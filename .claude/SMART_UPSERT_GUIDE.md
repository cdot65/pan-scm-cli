# Smart Upsert Pattern Guide

This guide documents the smart upsert pattern used in the pan-scm-cli project for handling both create and update operations through a single `set` command.

## Overview

The smart upsert pattern eliminates the need for separate `update` commands by making `set` commands intelligent enough to:
1. Check if a resource exists using `fetch()`
2. Compare the existing resource with the requested changes
3. Only update fields that have changed
4. Handle special cases like type changes that require delete/recreate
5. Return an action indicator for proper user feedback

## Action Tracking

The smart upsert pattern returns an `__action__` field in the response to indicate what operation was performed:
- `"created"` - A new resource was created
- `"updated"` - An existing resource was updated  
- `"no_change"` - Resource exists but no changes were needed

This allows commands to provide accurate feedback to users about what actually happened.

## Implementation Pattern

### SDK Client Method Pattern

```python
def create_resource(self, folder: str, name: str, **kwargs) -> dict[str, Any]:
    """Create or update a resource using smart upsert logic."""
    try:
        # Step 1: Try to fetch the existing resource
        existing_resource = None
        try:
            existing_resource = self.client.resource.fetch(name=name, folder=folder)
            self.logger.info(f"Found existing resource '{name}' in folder '{folder}'")
        except NotFoundError:
            self.logger.info(f"Resource '{name}' not found in folder '{folder}', will create new")
        
        if existing_resource:
            # Step 2: Check what needs updating
            needs_update = False
            update_fields = []
            
            # Compare each field
            if kwargs.get("field") is not None and existing_resource.field != kwargs["field"]:
                existing_resource.field = kwargs["field"]
                update_fields.append("field")
                needs_update = True
            
            # Step 3: Only update if changes detected
            if needs_update:
                self.logger.info(f"Updating resource fields: {', '.join(update_fields)}")
                result = self.client.resource.update(existing_resource)
                self.logger.info(f"Successfully updated resource '{name}' in folder '{folder}'")
                response = json.loads(result.model_dump_json(exclude_unset=True))
                response["__action__"] = "updated"
                return response
            else:
                self.logger.info(f"No changes detected for resource '{name}', skipping update")
                response = json.loads(existing_resource.model_dump_json(exclude_unset=True))
                response["__action__"] = "no_change"
                return response
        else:
            # Step 4: Create new resource
            result = self.client.resource.create(resource_data)
            self.logger.info(f"Successfully created resource '{name}' in folder '{folder}'")
            response = json.loads(result.model_dump_json(exclude_unset=True))
            response["__action__"] = "created"
            return response
            
    except Exception as e:
        self._handle_api_exception("create/update", folder, name, e)
```

### Command Pattern

```python
@set_app.command("resource")
def set_resource(
    folder: str = typer.Option(..., "--folder", help="Folder path"),
    name: str = typer.Option(..., "--name", help="Resource name"),
    # ... other options
) -> None:
    """Create or update a resource."""
    try:
        # ... prepare data ...
        
        # Create/update the resource
        result = scm_client.create_resource(
            folder=folder,
            name=name,
            # ... other parameters
        )
        
        # Get the action performed
        action = result.pop("__action__", "created")
        
        # Provide appropriate user feedback
        if action == "created":
            typer.echo(f"✅ Created resource: {name} in folder {folder}")
        elif action == "updated":
            typer.echo(f"✅ Updated resource: {name} in folder {folder}")
        elif action == "no_change":
            typer.echo(f"ℹ️  No changes needed for resource: {name} in folder {folder}")
            
    except Exception as e:
        typer.echo(f"❌ Error creating/updating resource: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
```

## Field Comparison Patterns

### Simple Fields

```python
# String comparison
if description is not None:
    current_desc = getattr(existing_resource, "description", "")
    if current_desc != description:
        existing_resource.description = description
        update_fields.append("description")
        needs_update = True
```

### List Fields (Order Doesn't Matter)

```python
# Compare as sets to ignore order
if tags is not None:
    current_tags = getattr(existing_resource, "tags", []) or []
    if set(current_tags) != set(tags):
        existing_resource.tags = tags
        update_fields.append("tags")
        needs_update = True
```

### Complex/Nested Fields

```python
# Protocol comparison for services
if protocol and hasattr(existing_resource, "protocol"):
    existing_protocol = existing_resource.protocol.model_dump(exclude_unset=True)
    if existing_protocol != protocol:
        existing_resource.protocol = protocol
        update_fields.append("protocol")
        needs_update = True
```

### Case-Insensitive Fields

```python
# Color comparison for tags (API uses Title case)
if "color" in data and data["color"]:
    new_color = data["color"].title()
    if hasattr(existing_resource, "color") and existing_resource.color != new_color:
        existing_resource.color = new_color
        update_fields.append("color")
        needs_update = True
```

## Type Change Handling

For resources with mutually exclusive types (like addresses):

```python
# Determine current and new types
current_type = self._get_address_type(existing_address)
new_type = self._get_address_type_from_kwargs(**kwargs)

# If type is changing, delete and recreate
if current_type and new_type and current_type != new_type:
    self.logger.info(f"Address type changing from {current_type} to {new_type}, recreating...")
    self.client.address.delete(object_id=str(existing_address.id))
    result = self.client.address.create(address_data)
    response = json.loads(result.model_dump_json(exclude_unset=True))
    response["__action__"] = "recreated"
    return response
```

## Logging Standards

The pattern uses specific log messages for each scenario:

1. **Fetch Stage**:
   - `"Found existing resource 'name' in folder 'folder'"`
   - `"Resource 'name' not found in folder 'folder', will create new"`

2. **Update Stage**:
   - `"Updating resource fields: field1, field2"` (when changes detected)
   - `"No changes detected for resource 'name', skipping update"` (no changes)

3. **Result Stage**:
   - `"Successfully created resource 'name' in folder 'folder'"`
   - `"Successfully updated resource 'name' in folder 'folder'"`

## Best Practices

1. **Always compare before updating**: Don't call update() if nothing changed
2. **Use appropriate comparison methods**: Sets for unordered lists, case normalization for strings
3. **Include all relevant fields**: Don't skip optional fields in comparisons
4. **Handle None vs empty**: Be explicit about None vs empty string/list
5. **Return consistent format**: Always include the `__action__` field
6. **Log appropriately**: Use consistent log messages across all methods

## Common Pitfalls

1. **Updating unchanged resources**: This triggers unnecessary API calls and audit logs
2. **Wrong field comparisons**: Not handling lists, case sensitivity, or nested objects properly
3. **Missing action indicators**: Forgetting to add `__action__` to the response
4. **Inconsistent logging**: Using different log message formats

## Testing Checklist

When implementing smart upsert logic, test:

1. ✅ Creating a new resource (should show "Created")
2. ✅ Updating an existing resource with changes (should show "Updated")
3. ✅ Re-running same command (should show "No changes needed")
4. ✅ Changing resource type (should handle delete/recreate)
5. ✅ Error scenarios (invalid data, API errors)