# SCM-CLI Style Guide

This guide defines the coding standards and patterns for the pan-scm-cli project. All code contributions should follow these guidelines to maintain consistency throughout the codebase.

## Table of Contents

1. [Module Structure](#module-structure)
2. [Section Organization](#section-organization)
3. [Command Architecture](#command-architecture)
4. [Function Patterns](#function-patterns)
5. [Documentation Standards](#documentation-standards)
6. [Error Handling](#error-handling)
7. [Type Annotations](#type-annotations)
8. [Naming Conventions](#naming-conventions)
9. [Output Formatting](#output-formatting)
10. [SDK Client Patterns](#sdk-client-patterns)
11. [Validator Patterns](#validator-patterns)
12. [Command Module Style Guide](#command-module-style-guide)

## Module Structure

### Import Organization

Imports should be organized in the following order:

1. Standard library imports
2. Third-party imports
3. Local imports (with relative imports for package modules)

```python
from pathlib import Path
from typing import Any, NoReturn

import typer
import yaml
from pydantic import ValidationError

from ..utils.config import load_from_yaml
from ..utils.sdk_client import scm_client
from ..utils.validators import ValidatorModel
```

### Module Docstring

Every module must start with a concise docstring:

```python
"""Module-level commands for Strata Cloud Manager.

This module provides CLI commands for managing resources through
the SCM API, organized by action types.
"""
```

## Section Organization

Use 191-character width section separators to organize code:

### Major Sections (Double Lines)

```python
# =======================================================================================================================================================================================
# SECTION NAME
# =======================================================================================================================================================================================
```

### Subsections (Single Line with Centered Title)

```python
# ----------------------------------------------------------------------------------- Subsection Name -----------------------------------------------------------------------------------
```

### Standard Section Order for Command Modules

1. Module docstring and imports
2. TYPER APP CONFIGURATION
3. COMMAND OPTIONS
4. [RESOURCE] COMMANDS (e.g., ADDRESS COMMANDS, ZONE COMMANDS)
5. BACKUP COMMANDS (if applicable)

### Standard Section Order for SDK Client

1. Module docstring and imports
2. Class definition
3. API METHODS (with navigation guide)
4. DEPLOYMENT CONFIGURATION METHODS
5. OBJECTS CONFIGURATION METHODS
6. NETWORK CONFIGURATION METHODS
7. SECURITY CONFIGURATION METHODS

### Standard Section Order for Validators

1. Module docstring and imports
2. TYPE DEFINITIONS
3. DEPLOYMENT CONFIGURATION MODELS
4. OBJECTS CONFIGURATION MODELS
5. NETWORK CONFIGURATION MODELS
6. SECURITY CONFIGURATION MODELS
7. UTILITY FUNCTIONS

### Alphabetical Ordering in main.py

All entries should be alphabetically ordered for consistency:

1. **Action App Groups**: backup, delete, load, set, show
2. **Action App Registration**: Same alphabetical order
3. **Module Commands**: Group by action type first, then alphabetically by module (deployment, network, objects, security)

## Command Architecture

### Typer App Structure

Create separate Typer apps for each action type:

```python
# ========================================================================================================================================================================================
# TYPER APP CONFIGURATION
# ========================================================================================================================================================================================

# Main module app
deployment_app = typer.Typer(help="Deployment configuration commands")

# Action apps
set_app = typer.Typer(help="Create or update deployment configurations")
delete_app = typer.Typer(help="Remove deployment configurations")
load_app = typer.Typer(help="Load deployment configurations from a file")
show_app = typer.Typer(help="Display deployment configurations")  # If applicable

# Register action apps with main app
deployment_app.add_typer(set_app, name="set")
deployment_app.add_typer(delete_app, name="delete")
deployment_app.add_typer(load_app, name="load")
```

### Command Options Pattern

Define all Typer options as constants with descriptive names and advanced defaults:

```python
# ========================================================================================================================================================================================
# COMMAND OPTIONS
# ========================================================================================================================================================================================

# Required options
FOLDER_OPTION = typer.Option(..., "--folder", help="Folder to place the resource in")
NAME_OPTION = typer.Option(..., "--name", help="Name of the resource")
FILE_OPTION = typer.Option(..., "--file", help="Path to YAML file")

# Optional options with defaults
DESCRIPTION_OPTION = typer.Option(None, "--description", help="Description of the resource")
TAGS_OPTION = typer.Option(default_factory=list, help="List of tags to add to the resource")
DRY_RUN_OPTION = typer.Option(False, "--dry-run", help="Show what would be loaded without making changes")

# Type-specific options
BANDWIDTH_OPTION = typer.Option(..., "--bandwidth", help="Bandwidth in Mbps")
MODE_OPTION = typer.Option(..., "--mode", help="Zone mode (L2, L3, external, virtual-wire, tunnel)")

# Container/context options (always include all three for containerized resources)
SNIPPET_OPTION = typer.Option(None, "--snippet", help="Snippet path for the resource")
DEVICE_OPTION = typer.Option(None, "--device", help="Device path for the resource")

# List options should use default_factory=list for correct type inference
PORTS_OPTION = typer.Option(default_factory=list, help="List of TCP/UDP ports (e.g. tcp/80, udp/53)")
```

**Guidance:**

- Use `default_factory=list` for all list-type options to ensure correct defaulting and avoid mutable default arguments.
- Always provide clear, actionable help text for each option.
- For containerized resources, always provide `--folder`, `--snippet`, and `--device` options and validate that exactly one is provided (see validators).
- Use consistent naming conventions for options across all modules (e.g., `--tags`, `--description`, `--file`).
- For security and objects modules, follow the same option patterns for all CRUD/backup/load/show commands.

## Function Patterns

### Command Function Structure

```python
@set_app.command("resource-name")
@handle_command_errors("creating resource")
def set_resource_name(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    specific_param: type = SPECIFIC_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    tags: list[str] = TAGS_OPTION,
):
    """Create or update a resource.

    Examples:
    --------
    scm-cli set module resource-name --folder Texas --name example --param value
    scm-cli set module resource-name --folder Texas --name example --param value --tags tag1 --tags tag2

    """
    # Input validation (if using Pydantic)
    model = ValidatorModel(
        folder=folder,
        name=name,
        specific_param=specific_param,
        description=description or "",
        tags=tags or [],
    )

    # SDK client call
    result = scm_client.create_resource(
        folder=folder,
        name=name,
        specific_param=specific_param,
        description=description,
        tags=tags,
    )

    # Outcome message (stderr, ✓ prefix)
    success(f"Created resource: {result['name']} in folder {result['folder']}")
    return result
```

Unexpected exceptions are converted to `Error creating resource: <message>` (stderr, exit 1)
by the decorator — no `try/except` in the command body.

### Load Command Pattern

```python
@load_app.command("resource-name")
@handle_command_errors("loading resources")
def load_resource_name(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load resources from a YAML file.

    Example:
    -------
    scm-cli load module resource-name --file resources.yml
    scm-cli load module resource-name --file resources.yml --dry-run

    """
    # Load and validate YAML
    data = load_from_yaml(file)

    if dry_run:
        info("Dry run mode - no changes will be made")
        typer.echo(yaml.dump(data, default_flow_style=False))
        return

    # Validate data structure
    items = validate_yaml_file(data, ValidatorModel, "resources")

    # Process each item; per-item failures are reported but do not stop the batch
    created_count = 0
    for item in items:
        try:
            result = scm_client.create_resource(**item.model_dump())
            success(f"Created resource: {result['name']} in folder {result['folder']}")
            created_count += 1
        except Exception as e:
            error(f"Error creating {item.name}: {str(e)}")

    # Summary
    success(f"Successfully created {created_count} resources from {file}")
```

### Show Command Pattern (for objects that support listing)

```python
@show_app.command("resource-name")
@handle_command_errors("showing resource")
def show_resource_name(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", "-n", help="Show specific resource by name"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Show resource details.

    Examples:
    --------
    scm-cli show module resource-name --folder Texas
    scm-cli show module resource-name --folder Texas --name example
    scm-cli show module resource-name --folder Texas --output json

    """
    if name:
        item = scm_client.get_resource(folder=folder, name=name)
        emit(item, output, title=f"Resource: {name}")
        return item

    items = scm_client.list_resources(folder=folder)
    emit(items, output, title=f"Resources in folder {folder}", columns=["name", "folder", "description"])
    return items
```

Listing is the default when `--name` is omitted; `emit` handles empty results,
table rendering, and the `--output json|yaml` machine formats.

## Documentation Standards

### Command Docstrings

Every command must have a docstring using **Google-style** as the preferred format, with:

1. Brief description (one line)
2. Blank line
3. Examples section ("Examples:", separator line, one or more CLI invocations)
4. (Optional) Note/extra info section

```python
"""Create or update a security rule.

Examples:
--------
scm-cli set security rule --folder Texas --name web-allow --source-zones trust --destination-zones untrust
scm-cli set security rule --folder Texas --name cleanup --source-zones any --destination-zones any --action deny --log-start --log-end --rulebase post

Note:
----
Security rules require both container and rulebase parameters.
"""
```

**Guidance:**

- Use "Examples:" (plural) and a separator line (`--------`) before listing CLI examples.
- Prefer Google-style docstrings for all functions and commands for consistency.
- Clearly indicate required and optional parameters in the docstring or help text.
- For complex commands, add a "Note:" section for caveats or special behaviors.

### Function/Method Docstrings (Google Format)

```python
def function_name(param1: type, param2: type | None = None) -> ReturnType:
    """Brief description of function.

    Args:
        param1: Description of param1
        param2: Description of param2 (optional)

    Returns:
        Description of return value

    Raises:
        ExceptionType: When this exception is raised
    """
```

**Guidance:**

- All public functions and methods should use Google-style docstrings as above.
- For CLI commands, include an "Examples:" section as shown above.
- For Pydantic model validators, include "Returns" and "Raises" for clarity.

## Error Handling

### Standard Error Pattern

Every command is wrapped with the shared decorator from `scm_cli.utils.decorators`:

```python
@set_app.command("resource-name")
@handle_command_errors("creating resource")
def set_resource_name(...):
    ...
```

The decorator catches unexpected exceptions, prints `Error creating resource: <message>`
to stderr, and exits with code 1; `typer.Exit`, `typer.Abort`, and `SystemExit` pass
through untouched. Do not wrap command bodies in blanket `try/except Exception` — only
catch narrower exceptions when the command can genuinely handle or enrich them (e.g.
per-item failures in a `load` loop, reported via `error(...)` without stopping the batch).

Expected failures (not-found, invalid combination of flags) are reported explicitly:

```python
error(f"Resource not found: {name} in folder {folder}")
raise typer.Exit(code=1)
```

**Mock Mode and Authentication Handling:**

- Mock mode is explicit-only: `SCM_MOCK=1` (env) or `--mock` where offered. Missing
  credentials must fail with exit code 1 and remediation steps — never silently fall
  back to mock data (see `sdk_client.py`).
- Use `typer.Exit(code=1)` for all fatal CLI errors to ensure consistent exit codes.

### SDK Client Error Handling

```python
def _handle_api_exception(self, operation: str, folder: str, resource_name: str, exception: Exception) -> NoReturn:
    """Handle API exceptions with proper logging and error formatting.

    Args:
        operation: The operation being performed
        folder: The folder containing the resource
        resource_name: The name of the resource
        exception: The exception that was raised

    Raises:
        Exception: Re-raises the original exception after logging

    """
    if isinstance(exception, AuthenticationError):
        self.logger.error(f"Authentication error during {operation} of {resource_name}: {str(exception)}")
    elif isinstance(exception, NotFoundError):
        self.logger.error(f"Resource not found: {resource_name} in folder {folder}")
    # ... other exception types

    raise exception
```

## Type Annotations

### Modern Python Type Hints

Use Python 3.10+ union syntax **exclusively**:

```python
# Preferred
param: str | None = None
items: list[str] = []

# Not preferred (old style)
param: Optional[str] = None
items: Optional[List[str]] = None
```

**Guidance:**

- Always use `str | None` instead of `Optional[str]`.
- For list options, use `list[str] = []` or `default_factory=list` for Pydantic/typer.
- Use explicit type hints for all function parameters and return types.

### Common Type Patterns

```python
# Required string
name: str = NAME_OPTION

# Optional string with None default
description: str | None = DESCRIPTION_OPTION

# Optional list with None default (converts to empty list in function)
tags: list[str] | None = TAGS_OPTION

# Path type for files
file: Path = FILE_OPTION

# Boolean with default
dry_run: bool = DRY_RUN_OPTION

# Return types
def function() -> dict[str, Any]:
def function() -> list[dict[str, Any]]:
def function() -> bool:
def function() -> NoReturn:  # For functions that always raise
```

## Naming Conventions

### Commands

- Use kebab-case for command names
- Be descriptive but concise
- For security services, follow the pattern: `set security <service>`, `delete security <service>`, etc.
- For objects, use: `set objects <type>`, `delete objects <type>`, etc.

```python
@set_app.command("bandwidth-allocation")  # Good
@set_app.command("anti-spyware-profile")  # Good
@set_app.command("ba")  # Too short
@set_app.command("create_bandwidth_allocation")  # Wrong style
```

**Guidance:**

- Always use descriptive, kebab-case command names matching the CLI structure in README and actual code.
- Avoid abbreviations unless they are industry standard and unambiguous.

### Functions

- Use snake_case
- Prefix with action verb

```python
def set_address_group():  # Good
def delete_security_rule():  # Good
def load_bandwidth_allocations():  # Good
def address_group():  # Missing action verb
```

### Constants

- Use UPPER_SNAKE_CASE
- Suffix with `_OPTION` for Typer options

```python
FOLDER_OPTION = typer.Option(...)  # Good
NAME_OPTION = typer.Option(...)  # Good
folder_option = typer.Option(...)  # Wrong case
FOLDER = typer.Option(...)  # Missing suffix
```

### Variables

- Use snake_case
- Be descriptive

```python
created_count = 0  # Good
address_groups = []  # Good
c = 0  # Too short
createdCount = 0  # Wrong style
```

## Output Formatting

All user-facing output flows through the shared output layer, `scm_cli.utils.output`.
Never hand-roll display code with `typer.echo` field dumps, `"-" * N` separators,
ad-hoc `rich.Console` instances, or `json.dumps`/`yaml.dump` spliced into prose.

Two rules define the layer:

1. **Data goes to stdout** — tables, detail views, JSON, YAML (via `emit`).
2. **Messages go to stderr** — success, error, warning, info (via the helpers).

This keeps stdout pipe-safe: `scm show ... --output json | jq` always receives pure data.

### Messages (stderr)

```python
from ..utils.output import error, info, success, warning

success(f"Created {resource_type}: {name} in folder {folder}")   # ✓ prefix
success(f"Deleted {resource_type}: {name} from folder {folder}")
info(f"No changes needed for {resource_type}: {name}")           # dim
warning("Something non-fatal")                                    # ⚠ prefix
error(f"{Resource} not found: {name} in folder {folder}")         # ✗ prefix, then raise typer.Exit(code=1)
```

Unexpected exceptions are handled by `@handle_command_errors("<verb-ing> <resource>")`
(see Error Handling) — do not wrap command bodies in blanket `try/except`.

### Data (stdout)

Every `show` command takes `output: OutputFormat = OUTPUT_OPTION` (`--output/-o table|json|yaml`)
and renders through `emit`:

```python
from ..utils.output import OUTPUT_OPTION, OutputFormat, emit

# List path: rich table (table format) or machine-readable document (json/yaml)
emit(items, output, title=f"Addresses in folder {folder}", columns=["name", "folder", "ip_netmask", "description"])

# Single-object path: field-per-line detail view (table format)
emit(item, output, title=f"Address: {name}")

# Empty list: emit([]) prints a stderr notice for tables and a valid empty document for json/yaml
```

## SDK Client Patterns

### Method Organization

Group methods by configuration type:

1. Deployment Configuration (bandwidth allocations)
2. Objects Configuration (addresses, address groups)
3. Network Configuration (zones)
4. Security Configuration (rules)

### Method Naming

Use consistent CRUD naming:

```python
def create_resource():  # Create new
def get_resource():     # Get single item
def list_resources():   # Get multiple items
def update_resource():  # Update existing
def delete_resource():  # Delete existing
```

### Mock Mode Support

Always check for client availability:

```python
if not self.client:
    # Return mock data
    return {
        "id": f"mock-{name}",
        "folder": folder,
        "name": name,
        # ... other fields
    }

# Real client operations
try:
    result = self.client.service.method()
    return result.model_dump()  # or result.dict() for older SDK
except Exception as e:
    self._handle_api_exception("operation", folder, name, e)
```

### Return Types

- Always return dictionaries for consistency
- Convert SDK model objects using `model_dump()` or `dict()`
- Return bool for delete operations

## Validator Patterns

### Model Structure

```python
class ResourceModel(BaseModel):
    """Model for resource configurations with folder path."""

    # Required fields
    folder: str = Field(..., description="Folder path for the resource")
    name: str = Field(..., description="Name of the resource")

    # Optional fields with defaults
    description: str = Field("", description="Description of the resource")
    tags: list[str] = Field(default_factory=list, description="List of tags")

    # Type-specific fields
    specific_field: str = Field(..., description="Resource-specific field")
```

### Validation Methods

```python
@model_validator(mode="after")
def validate_resource(self) -> "ResourceModel":
    """Validate resource constraints.

    Returns:
        The validated resource model

    Raises:
        ValueError: If validation fails

    """
    # Validation logic
    return self
```

### SDK Model Conversion

```python
def to_sdk_model(self) -> dict[str, Any]:
    """Convert CLI model to SDK model format."""
    return {
        "name": self.name,
        "description": self.description,
        # Map fields as needed for SDK
    }
```

### Utility Functions

```python
def validate_yaml_file(data: dict[str, Any], model_class: type[ModelT], key: str) -> list[ModelT]:
    """Validate a YAML data structure against a Pydantic model.

    Args:
        data: The parsed YAML data
        model_class: The Pydantic model class to validate against
        key: The key in the YAML data that contains the items

    Returns:
        A list of validated model instances

    Raises:
        ValueError: If validation fails

    """
```

## Command Module Style Guide

A comprehensive command styling guide has been created specifically for command modules. See `src/scm_cli/commands/command-styling.md` for detailed patterns and conventions specific to implementing CLI commands.

### Key Areas Covered

1. **Module Structure**: Docstrings, imports, section separators
2. **Typer App Organization**: Action groups, command registration
3. **Command Implementation Patterns**: Standardized patterns for backup, delete, load, set, and show commands
4. **Error Handling**: Consistent error messages and exit codes
5. **Output Formatting**: Success messages, list displays, detail views
6. **Type Hints**: Modern Python 3.10+ syntax
7. **Naming Conventions**: Commands, functions, variables

The command styling guide complements this general style guide with specific patterns observed in the address, address-group, and application object implementations.

## Code Review Checklist

Before submitting code, ensure:

- [ ] Follows section organization with 191-character separators
- [ ] Uses consistent naming conventions
- [ ] Includes proper docstrings for all functions/commands
- [ ] Has appropriate type annotations
- [ ] Implements standard error handling patterns
- [ ] Provides clear output messages
- [ ] Supports mock mode in SDK client methods
- [ ] Validates input with Pydantic models where appropriate
- [ ] Includes command examples in docstrings
- [ ] Groups related functionality appropriately
- [ ] Maintains consistent import organization
- [ ] Uses modern Python syntax (3.10+)
- [ ] Follows command-specific patterns from command-styling.md (for command modules)
