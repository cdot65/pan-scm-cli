# SDK Client Style Guide

This guide defines the specific patterns and standards for the SDK client integration module (`src/scm_cli/utils/sdk_client.py`).

## Table of Contents

1. [Module Structure](#module-structure)
2. [Class Design](#class-design)
3. [Method Organization](#method-organization)
4. [Method Patterns](#method-patterns)
5. [Error Handling](#error-handling)
6. [Mock Mode Support](#mock-mode-support)
7. [Logging Standards](#logging-standards)
8. [Type Annotations](#type-annotations)
9. [Documentation](#documentation)

## Module Structure

### Standard Module Layout

```python
"""SDK client integration for pan-scm-cli.

This module provides integration with the pan-scm-sdk client for interacting
with Palo Alto Networks Strata Cloud Manager. It uses the credentials from
dynaconf settings.
"""

import logging
from typing import Any, NoReturn

# Import the actual SDK client
from scm.client import Scm
from scm.exceptions import APIError, AuthenticationError, ClientError, NotFoundError

from .config import get_credentials, settings

# Configure logging
logging_level = getattr(logging, settings.get("log_level", "INFO"))
logging.basicConfig(level=logging_level)
logger = logging.getLogger(__name__)
```

### Section Organization

Use 191-character separators:

```python
# =======================================================================================================================================================================================
# API METHODS - Quick Navigation:
# - Deployment Configuration: Bandwidth Allocation
# - Objects Configuration: Address Groups, Address Objects
# - Network Configuration: Security Zones
# - Security Configuration: Security Rules
# =======================================================================================================================================================================================

# =======================================================================================================================================================================================
# DEPLOYMENT CONFIGURATION METHODS
# =======================================================================================================================================================================================
# region Deployment Configuration

# ----------------------------------------------------------------------------------- Bandwidth Allocation -----------------------------------------------------------------------------------
```

## Class Design

### SCMClient Class Structure

```python
class SCMClient:
    """Client for the SCM SDK.

    This client provides methods for interacting with Palo Alto Networks
    Strata Cloud Manager API, organized by configuration type:

    Deployment Configuration:
        - Bandwidth Allocation: create, delete

    Objects Configuration:
        - Address Groups: create, get, list, delete
        - Address Objects: create, get, list, delete

    Network Configuration:
        - Security Zones: create, delete

    Security Configuration:
        - Security Rules: create, delete
    """

    def __init__(self):
        """Initialize the SCM client with logger and credentials."""
        self.logger = logger
        self.logger.info("Initializing SCM client")
        self.client = None

        try:
            # Credential initialization
            credentials = get_credentials()
            self.client_id = credentials["client_id"]
            self.client_secret = credentials["client_secret"]
            self.tsg_id = credentials["tsg_id"]

            # SDK client initialization
            self.client = Scm(
                client_id=self.client_id,
                client_secret=self.client_secret,
                tsg_id=self.tsg_id,
                log_level=settings.get("log_level", "INFO"),
            )
            self.logger.info(f"Successfully initialized SDK client for TSG ID: {self.tsg_id}")
        except (ValueError, AuthenticationError) as e:
            self.logger.warning(f"Failed to initialize SDK client: {str(e)}")
            self.logger.warning("Using mock mode with dummy credentials")
            self.client_id = "mock-client-id"
            self.client_secret = "mock-client-secret"
            self.tsg_id = "mock-tsg-id"
            # In mock mode, methods will return mock data instead of making API calls

        except (APIError, InvalidClientError) as e:
            # Handle authentication failures gracefully
            error_msg = str(e)
            if "invalid_client" in error_msg or "Client authentication failed" in error_msg:
                import sys
                print("\n❌ Authentication failed: Invalid client credentials", file=sys.stderr)
                print(f"\nCurrent context: {current_context or 'None set'}", file=sys.stderr)
                print(f"Client ID: {credentials.get('client_id', 'Not set')}", file=sys.stderr)
                print(f"TSG ID: {credentials.get('tsg_id', 'Not set')}", file=sys.stderr)
                print("\nTo fix this issue:", file=sys.stderr)
                print("  1. Update context: scm context create <name> --client-id <id> --client-secret <secret> --tsg-id <tsg>", file=sys.stderr)
                print("  2. Switch context: scm context use <name>", file=sys.stderr)
                print("  3. Use environment variables: SCM_CLIENT_ID, SCM_CLIENT_SECRET, SCM_TSG_ID", file=sys.stderr)
                raise SystemExit(1) from e
            else:
                import sys
                print(f"\n❌ Failed to initialize SDK client: {error_msg}", file=sys.stderr)
                raise SystemExit(1) from e
```

## Method Organization

### Grouping by Configuration Type

Methods should be organized into clear sections using 191-character separators, matching the CLI and SDK structure:

1. **Deployment Configuration Methods**
   - Bandwidth Allocation operations
2. **Objects Configuration Methods**
   - Address Groups
   - Address Objects
   - Application, Application Group, Application Filter
3. **Network Configuration Methods**
   - Security Zones
   - Other network resource types
4. **Security Configuration Methods**
   - Security Rules
   - Anti-Spyware Profile
   - Decryption Profile
   - [Add new security services as implemented]

**Guidance:**

- Use clear region comments and separators for navigation.
- Keep CRUD patterns consistent for all resource types.
- Document new resource types as they are added.

### Method Naming Convention

Use consistent CRUD naming patterns:

- `create_<resource>()` - Create a new resource
- `get_<resource>()` - Retrieve a single resource
- `list_<resource>s()` - List multiple resources (note plural)
- `update_<resource>()` - Update an existing resource
- `delete_<resource>()` - Delete a resource

## Method Patterns

### Create Method Pattern

```python
def create_resource(
    self,
    folder: str,
    name: str,
    required_param: type,
    optional_param: str = "",
    tags: list[str] = [],
) -> dict[str, Any]:
    """Create a resource.

    Args:
        folder: Folder to create the resource in
        name: Name of the resource
        required_param: Description of required parameter
        optional_param: Description of optional parameter
        tags: Optional list of tags

    Returns:
        dict[str, Any]: The created resource object
    """
    self.logger.info(f"Creating resource: {name} in folder {folder}")

    if not self.client:
        # Return mock data if no client is available
        return {
            "id": f"resource-{name}",
            "folder": folder,
            "name": name,
            "required_param": required_param,
            "optional_param": optional_param,
            "tags": tags,
        }

    try:
        # Create using the SDK service
        resource_data = {
            "name": name,
            "folder": folder,
            "required_param": required_param,
        }

        if optional_param:
            resource_data["optional_param"] = optional_param

        if tags:
            resource_data["tag"] = tags  # or "tags" depending on SDK

        result = self.client.resource_service.create(resource_data)

        # Convert SDK response to dict for compatibility
        return result.model_dump()  # or result.dict() for older SDK
    except Exception as e:
        self._handle_api_exception("creation", folder, name, e)
```

### Get Method Pattern

```python
def get_resource(
    self,
    folder: str,
    name: str,
) -> dict[str, Any]:
    """Get a resource by name and folder.

    Args:
        folder: Folder containing the resource
        name: Name of the resource to get

    Returns:
        dict[str, Any]: The resource object

    """
    self.logger.info(f"Getting resource: {name} from folder {folder}")

    if not self.client:
        # Return mock data if no client is available
        return {
            "id": f"resource-{name}",
            "folder": folder,
            "name": name,
            "description": "Mock resource",
            "tags": ["mock"],
            # Include type-specific fields
        }

    try:
        # Fetch the resource using the SDK
        result = self.client.resource_service.fetch(name=name, folder=folder)

        # Convert SDK response to dict for compatibility
        return result.model_dump()
    except Exception as e:
        self._handle_api_exception("retrieval", folder, name, e)
```

### List Method Pattern

```python
def list_resources(
    self,
    folder: str,
) -> list[dict[str, Any]]:
    """List resources in a folder.

    Args:
        folder: Folder to list resources from

    Returns:
        list[dict[str, Any]]: List of resource objects

    """
    self.logger.info(f"Listing resources in folder: {folder}")

    if not self.client:
        # Return mock data if no client is available
        return [
            {
                "id": "resource-mock1",
                "folder": folder,
                "name": "mock-resource-1",
                "description": "Mock resource 1",
                "tags": ["mock"],
            },
            {
                "id": "resource-mock2",
                "folder": folder,
                "name": "mock-resource-2",
                "description": "Mock resource 2",
                "tags": ["mock"],
            },
        ]

    try:
        # List resources using the SDK
        results = self.client.resource_service.list(folder=folder)

        # Convert SDK response to list of dicts for compatibility
        return [result.model_dump() for result in results]
    except Exception as e:
        self._handle_api_exception("listing", folder, "resources", e)
```

### Delete Method Pattern

```python
def delete_resource(
    self,
    folder: str,
    name: str,
) -> bool:
    """Delete a resource.

    Args:
        folder: Folder containing the resource
        name: Name of the resource to delete

    Returns:
        bool: True if deletion was successful

    """
    self.logger.info(f"Deleting resource: {name} from folder {folder}")

    if not self.client:
        # Return mock result if no client is available
        return True

    try:
        # Delete using the SDK service
        self.client.resource_service.delete(folder=folder, name=name)
        return True
    except Exception as e:
        self._handle_api_exception("deletion", folder, name, e)
```

## Error Handling

### Central Error Handler

```python
def _handle_api_exception(self, operation: str, folder: str, resource_name: str, exception: Exception) -> NoReturn:
    """Handle API exceptions with proper logging and error formatting.

    Args:
        operation: The operation being performed (create, update, delete, etc.)
        folder: The folder containing the resource
        resource_name: The name of the resource being operated on
        exception: The exception that was raised

    Raises:
        Exception: Re-raises the original exception after logging

    """
    if isinstance(exception, AuthenticationError):
        self.logger.error(f"Authentication error during {operation} of {resource_name}: {str(exception)}")
        self.logger.error("Please check your credentials and try again.")
    elif isinstance(exception, NotFoundError):
        self.logger.error(f"Resource not found: {resource_name} in folder {folder}")
    elif isinstance(exception, ClientError):
        self.logger.error(f"Validation error during {operation} of {resource_name}: {str(exception)}")
    elif isinstance(exception, APIError):
        self.logger.error(f"API error during {operation} of {resource_name}: {str(exception)}")
    else:
        self.logger.error(f"Unexpected error during {operation} of {resource_name}: {str(exception)}")

    raise exception
```

## Mock Mode Support

### Mock Data Guidelines

- Always check `if not self.client:` before any SDK operation.
- Return realistic mock data matching the expected structure for each resource type.
- Use consistent ID format: `f"{resource-type}-{name}"`.
- Include all required fields and typical optional fields in mock responses.
- Make mock data identifiable with "mock" in descriptions/tags.
- Log a warning when falling back to mock mode.

### Mock Data Examples

```python
# Single resource mock
return {
    "id": f"addr-{name}",
    "folder": folder,
    "name": name,
    "description": "Mock address object",
    "tags": ["mock"],
    "ip_netmask": "192.168.1.0/24",  # Type-specific field
}

# List mock
return [
    {
        "id": "zone-mock1",
        "folder": folder,
        "name": "mock-zone-1",
        "description": "Mock security zone 1",
        "mode": "L3",
        "interfaces": ["ethernet1/1", "ethernet1/2"],
        "tags": ["mock"],
    },
    {
        "id": "zone-mock2",
        "folder": folder,
        "name": "mock-zone-2",
        "description": "Mock security zone 2",
        "mode": "L2",
        "interfaces": [],
        "tags": ["mock", "L2"],
    },
]
```

**Guidance:**

- Always provide mock data for new resource types as they are added.
- Document mock mode behavior in CLI help and developer docs.

## Logging Standards

### Log Levels

- `INFO`: Normal operations (creating, deleting, listing)
- `WARNING`: Non-fatal issues (falling back to mock mode, context fallback)
- `ERROR`: Operation failures (caught exceptions, authentication failures)

### Log Message Format

```python
# Operation start
self.logger.info(f"Creating {resource_type}: {name} in folder {folder}")

# Operation with details
self.logger.info(f"Creating bandwidth allocation: {name} with {bandwidth} Mbps in folder {folder}")

# Success (when needed)
self.logger.info(f"Successfully created {resource_type}: {name}")

# Warnings
self.logger.warning(f"Failed to initialize SDK client: {str(e)}")
self.logger.warning("Using mock mode with dummy credentials")
self.logger.warning("Falling back to context-based authentication")

# Errors (in exception handler)
self.logger.error(f"Authentication error during {operation} of {resource_name}: {str(exception)}")
self.logger.error(f"Resource not found: {resource_name} in folder {folder}")
```

**Guidance:**

- Use clear, actionable log messages for all major operations and errors.
- Always log the context (resource name, folder, etc.) for traceability.

## Type Annotations

### Import Requirements

```python
from typing import Any, NoReturn
```

### Method Signatures

```python
# Parameters with defaults
def method(
    self,
    required: str,
    optional: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:

# Return types
-> dict[str, Any]           # Single resource
-> list[dict[str, Any]]     # Multiple resources
-> bool                     # Success/failure operations
-> NoReturn                 # Exception handlers
```

### Parameter Types

- Use `str` for required strings
- Use `str | None` for optional strings with None default
- Use `list[str] | None` for optional lists
- Convert `None` to empty list/string in method body
- Use specific types where applicable (int for bandwidth, etc.)

## Documentation

### Module Docstring

Must describe the module's purpose and integration details.

### Class Docstring

Must include:

- Brief description
- Overview of provided functionality organized by category
- List of available operations per resource type

### Method Docstrings (Google Format)

```python
"""Brief description of the method.

Longer description if needed, explaining specifics
of the operation or any important details.

Args:
    folder: Folder to create the resource in
    name: Name of the resource
    param: Description of parameter
    tags: Optional list of tags

Returns:
    dict[str, Any]: The created resource object
    OR
    list[dict[str, Any]]: List of resource objects
    OR
    bool: True if operation was successful

Raises:
    AuthenticationError: If authentication fails
    NotFoundError: If resource is not found
    APIError: If API returns an error

Note:
    Additional information if needed

"""
```

## SDK Integration Patterns

### Data Transformation

```python
# CLI to SDK field mapping
resource_data = {
    "name": name,
    "folder": folder,
    # Map CLI field names to SDK field names
    "allocated_bandwidth": bandwidth,  # CLI uses 'bandwidth', SDK uses 'allocated_bandwidth'
}

# SDK response to dict
return result.model_dump()  # Preferred for newer pydantic
return result.dict()        # For older versions
```

### Service Access Pattern

```python
# Access SDK services through client
self.client.address           # Address service
self.client.address_group     # Address group service
self.client.bandwidth_allocation  # Note: singular, not plural
self.client.security_zone     # Security zone service
self.client.security_rule     # Security rule service
```

### Parameter Handling

```python
# Handle optional parameters
if description:
    resource_data["description"] = description

# Handle empty lists
if tags:
    resource_data["tag"] = tags  # Some SDK endpoints use 'tag', others use 'tags'

# Handle type-specific logic
if type.lower() == "static":
    group_data["static"] = members or []
elif type.lower() == "dynamic":
    if members and len(members) > 0:
        group_data["dynamic"] = {"filter": members[0]}
    else:
        raise ValueError("Dynamic groups require a filter expression")
```

## Testing Considerations

When writing SDK client methods, ensure they:

- Support mock mode without requiring credentials
- Return consistent data structures (always dicts/lists of dicts)
- Handle all expected SDK exceptions
- Log operations appropriately
- Validate parameters before SDK calls
- Convert SDK models to dicts for compatibility

## Code Review Checklist

- [ ] Methods organized by configuration type with proper sections
- [ ] Consistent CRUD naming (create*, get*, list*, delete*)
- [ ] Mock mode support with realistic data
- [ ] Proper error handling with `_handle_api_exception`
- [ ] Appropriate logging at correct levels
- [ ] Type annotations on all parameters and returns
- [ ] Google format docstrings with complete information
- [ ] SDK field mapping handled correctly
- [ ] Optional parameters handled with proper defaults
- [ ] Returns dict/list of dicts for consistency
- [ ] 191-character section separators used correctly
- [ ] List methods support `exact_match` parameter where applicable
