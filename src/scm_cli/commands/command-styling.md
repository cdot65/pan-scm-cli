# Command Styling Guide

This guide documents the styling patterns and conventions used in the SCM CLI command modules, specifically for object management commands (address, address-group, application, etc.).

## Module Structure

### 1. Module Docstring
Every command module should start with a comprehensive docstring that includes:
- Brief description of the module's purpose
- List of all commands with their descriptions
- Example usage for key commands

```python
"""SCM Objects management commands.

This module provides commands for managing various objects in Strata Cloud Manager:
- Address objects (IP addresses, FQDNs, etc.)
- Address groups (static and dynamic groups)
- Applications (custom and predefined)
- Application groups
- Application filters
- Dynamic user groups
- External dynamic lists
- HIP objects and profiles
- Log forwarding profiles (HTTP, syslog, email)
- Quarantine groups
- Regions
- Schedules
- Services and service groups
- Syslog server profiles
- Tags

Example:
-------
scm-cli set objects address --folder Texas --name test --ip-netmask 192.168.1.1/32
scm-cli set objects address-group --folder Texas --name test --type static --members ["abc", "xyz"]
scm-cli load objects application --file config/applications.yml
"""
```

### 2. Imports Organization
Imports should be organized in the following order:
1. Standard library imports
2. Third-party imports
3. Local imports

```python
# Standard library imports
from pathlib import Path

# Third-party imports
import typer
import yaml

# Local imports
from scm_cli.client import get_scm_client
from scm_cli.utils.validators import (
    Address,
    AddressGroup,
    Application,
    # ... other validators
)
```

### 3. Section Separators
Use consistent 191-character separators to delineate major sections:

```python
# ========================================================================================================================================================================================
# SECTION NAME
# ========================================================================================================================================================================================
```

## Typer App Organization

### 1. App Group Creation
Create separate Typer apps for each action type:

```python
# Create app groups for each action type
set_app = typer.Typer(help="Create or update objects configurations")
delete_app = typer.Typer(help="Remove objects configurations")
load_app = typer.Typer(help="Load objects configurations from YAML files")
show_app = typer.Typer(help="Display objects configurations")
backup_app = typer.Typer(help="Backup objects configurations to YAML files")

# Register all app groups
app = typer.Typer()
app.add_typer(set_app, name="set")
app.add_typer(delete_app, name="delete")
app.add_typer(load_app, name="load")
app.add_typer(show_app, name="show")
app.add_typer(backup_app, name="backup")
```

### 2. Common Options
Define common options as constants for consistency:

```python
# Common options shared across commands
FOLDER_OPTION = typer.Option(..., "--folder", help="Folder location", prompt=True)
NAME_OPTION = typer.Option(..., "--name", help="Object name", prompt=True)
FILE_OPTION = typer.Option(..., "--file", help="Path to YAML file containing configurations")
DRY_RUN_OPTION = typer.Option(False, "--dry-run", help="Show what would be done without making changes")
DESCRIPTION_OPTION = typer.Option(None, "--description", help="Object description")
TAGS_OPTION = typer.Option(None, "--tags", help="List of tags")
```

## Command Implementation Patterns

### 1. Command Order per Object Type
For each object type, implement commands in this specific order:
1. `backup` - Export objects to YAML
2. `delete` - Remove an object
3. `load` - Import objects from YAML
4. `set` - Create or update an object
5. `show` - Display object(s)

### 2. Backup Command Pattern

```python
@backup_app.command("object-type")
def backup_object_type(
    folder: str = FOLDER_OPTION,
):
    """Backup all {object_type}s from a folder to a YAML file.
    
    The backup file will be named '{object-type}-{folder}.yaml' in the current directory.
    
    Example:
    -------
    scm-cli backup objects {object-type} --folder Austin
    
    """
    try:
        # List all objects with exact_match=True
        objects = scm_client.list_objects(folder=folder, exact_match=True)
        
        if not objects:
            typer.echo(f"No {object_type}s found in folder '{folder}'")
            return
        
        # Convert to dictionaries, excluding None values
        backup_data = []
        for obj in objects:
            obj_dict = {k: v for k, v in obj.items() if v is not None}
            # Remove system fields
            obj_dict.pop("id", None)
            backup_data.append(obj_dict)
        
        # Create YAML structure
        yaml_data = {"{object_type}s": backup_data}
        
        # Generate filename
        filename = f"{object-type}-{folder.lower()}.yaml"
        
        # Write to file
        with open(filename, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)
        
        typer.echo(f"Successfully backed up {len(backup_data)} {object_type}s to {filename}")
        return filename
        
    except Exception as e:
        typer.echo(f"Error backing up {object_type}s: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
```

### 3. Delete Command Pattern

```python
@delete_app.command("object-type")
def delete_object_type(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete a {object_type}.
    
    Example:
    -------
    scm-cli delete objects {object-type} --folder Texas --name example
    
    """
    try:
        result = scm_client.delete_object(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted {object_type}: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting {object_type}: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
```

### 4. Load Command Pattern

```python
@load_app.command("object-type")
def load_object_type(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load {object_type}s from a YAML file.
    
    Example:
    -------
    scm-cli load objects {object-type} --file config/{object_type}s.yml
    
    """
    try:
        # Load and parse YAML
        config = load_from_yaml(str(file), "{object_type}s")
        
        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["{object_type}s"]))
            return
        
        # Apply each object
        results = []
        for obj_data in config["{object_type}s"]:
            # Validate using Pydantic model
            obj = ObjectValidator(**obj_data)
            
            # Call SDK client
            result = scm_client.create_object(
                folder=obj.folder,
                name=obj.name,
                # ... other fields
            )
            
            results.append(result)
            typer.echo(f"Applied {object_type}: {result['name']} in folder {result['folder']}")
        
        return results
    except Exception as e:
        typer.echo(f"Error loading {object_type}s: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
```

### 5. Set Command Pattern

```python
@set_app.command("object-type")
def set_object_type(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    # ... object-specific options
):
    """Create or update a {object_type}.
    
    Example:
    -------
        scm-cli set objects {object-type} \
        --folder Texas \
        --name example \
        --field value
    
    """
    try:
        # Validate inputs using Pydantic model
        obj = ObjectValidator(
            folder=folder,
            name=name,
            # ... map options to model fields
        )
        
        # Call SDK client
        result = scm_client.create_object(
            folder=obj.folder,
            name=obj.name,
            # ... pass all fields
        )
        
        typer.echo(f"Created {object_type}: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating {object_type}: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
```

### 6. Show Command Pattern

```python
@show_app.command("object-type")
def show_object_type(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the {object_type} to show"),
    list_objects: bool = typer.Option(False, "--list", help="List all {object_type}s in the folder"),
):
    """Display {object_type} objects.
    
    Examples
    --------
        # List all {object_type}s in a folder
        scm-cli show objects {object-type} --folder Texas --list
        
        # Show a specific {object_type} by name
        scm-cli show objects {object-type} --folder Texas --name example
    
    """
    try:
        if list_objects:
            # List all objects
            objects = scm_client.list_objects(folder=folder)
            
            if not objects:
                typer.echo(f"No {object_type}s found in folder '{folder}'")
                return
            
            typer.echo(f"{Object_type}s in folder '{folder}':")
            typer.echo("-" * 60)
            
            for obj in objects:
                # Display object information
                typer.echo(f"Name: {obj.get('name', 'N/A')}")
                
                # Display location
                if obj.get("folder"):
                    typer.echo(f"  Location: Folder '{obj['folder']}'")
                elif obj.get("snippet"):
                    typer.echo(f"  Location: Snippet '{obj['snippet']}'")
                elif obj.get("device"):
                    typer.echo(f"  Location: Device '{obj['device']}'")
                else:
                    typer.echo("  Location: N/A")
                
                # Display object-specific fields
                # ...
                
                typer.echo("-" * 60)
            
            return objects
            
        elif name:
            # Get specific object
            obj = scm_client.get_object(folder=folder, name=name)
            
            typer.echo(f"{Object_type}: {obj.get('name', 'N/A')}")
            
            # Display detailed information
            # ...
            
            return obj
            
        else:
            # Neither option provided
            typer.echo("Error: Either --list or --name must be specified", err=True)
            raise typer.Exit(code=1)
            
    except Exception as e:
        typer.echo(f"Error showing {object_type}: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
```

## Error Handling Conventions

### 1. Consistent Error Messages
- Always catch exceptions and provide user-friendly error messages
- Use `typer.echo(message, err=True)` for error output
- Exit with code 1 on errors: `raise typer.Exit(code=1) from e`

### 2. Error Message Format
```python
typer.echo(f"Error {action} {object_type}: {str(e)}", err=True)
```

## Documentation Standards

### 1. Docstrings
- Use Google-style docstrings
- Include brief description
- Add "Example:" or "Examples" section with command-line examples
- Use proper indentation for multi-line examples

### 2. Example Format
```python
"""Brief description of what the command does.

Example:
-------
scm-cli command subcommand --option value

Examples
--------
    # Example 1 description
    scm-cli command subcommand --option1 value1
    
    # Example 2 description  
    scm-cli command subcommand --option2 value2

"""
```

## Output Formatting

### 1. Success Messages
- Use consistent format: `"{Action} {object_type}: {name} in folder {folder}"`
- Examples:
  - "Created address: webserver in folder Texas"
  - "Deleted application: custom-app from folder Austin"
  - "Applied address group: servers in folder Production"

### 2. List Output Format
```
{Object_type}s in folder '{folder}':
------------------------------------------------------------
Name: {name}
  Location: Folder '{folder}'
  Field1: {value1}
  Field2: {value2}
  Tags: {tag1}, {tag2}
------------------------------------------------------------
```

### 3. Detail Output Format
```
{Object_type}: {name}
Location: Folder '{folder}'
Field1: {value1}
Field2: {value2}
Tags: {tag1}, {tag2}
ID: {id}
```

## Type Hints and Annotations

### 1. Use Python 3.10+ Union Types
```python
# Preferred
name: str | None = typer.Option(None, "--name")

# Not preferred
from typing import Optional
name: Optional[str] = typer.Option(None, "--name")
```

### 2. List Type Hints
```python
# For options that accept lists
members: list[str] | None = MEMBERS_OPTION
tags: list[str] | None = TAGS_OPTION
```

## Naming Conventions

### 1. Command Names
- Use kebab-case for multi-word commands: `address-group`, `application-group`
- Keep names concise but descriptive

### 2. Function Names
- Use snake_case: `backup_address_group`, `delete_application`
- Follow pattern: `{action}_{object_type}`

### 3. Variable Names
- Use descriptive names: `addresses`, `applications`, not `objs` or `items`
- Use singular for individual items: `address`, `application`
- Use plural for collections: `addresses`, `applications`

## Special Considerations

### 1. Boolean Fields
- Omit boolean fields from API calls when they're False
- Use default False for boolean options

### 2. Conditional Field Display
- Only show fields that have values
- Group related fields (e.g., security attributes for applications)

### 3. Field Validation
- Always validate input using Pydantic models before API calls
- Let Pydantic handle type conversion and validation

### 4. Exact Match for Backups
- Always use `exact_match=True` when listing objects for backup
- This ensures only objects from the specified folder are included

## Example Implementation Reference

See the implementations of `address`, `address-group`, and `application` commands in `objects.py` as reference examples that follow all these conventions.