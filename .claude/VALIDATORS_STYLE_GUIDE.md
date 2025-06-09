# Validators Style Guide

This guide defines the specific patterns and standards for the validators module (`src/scm_cli/utils/validators.py`).

## Table of Contents

1. [Module Structure](#module-structure)
2. [Model Design Patterns](#model-design-patterns)
3. [Field Definitions](#field-definitions)
4. [Validation Patterns](#validation-patterns)
5. [Type Annotations](#type-annotations)
6. [SDK Model Conversion](#sdk-model-conversion)
7. [Utility Functions](#utility-functions)
8. [Documentation Standards](#documentation-standards)

## Module Structure

### Standard Module Layout

```python
"""Model validators for scm-cli.

This module defines integrations with SDK Pydantic models for validating input data structures before
sending them to the SCM API. These models enforce data integrity and ensure
that all required fields are present and correctly formatted.
"""

from typing import Any, TypeVar

from pydantic import BaseModel, Field, model_validator

# ========================================================================================================================================================================================
# TYPE DEFINITIONS
# ========================================================================================================================================================================================

# Create a type variable bound to BaseModel
ModelT = TypeVar("ModelT", bound=BaseModel)

# ========================================================================================================================================================================================
# DEPLOYMENT CONFIGURATION MODELS
# ========================================================================================================================================================================================

# Models organized by configuration type...
```

### Section Organization

Use 191-character separators to organize models by configuration type:

1. TYPE DEFINITIONS
2. DEPLOYMENT CONFIGURATION MODELS
3. OBJECTS CONFIGURATION MODELS
4. NETWORK CONFIGURATION MODELS
5. SECURITY CONFIGURATION MODELS
6. UTILITY FUNCTIONS

## Model Design Patterns

### Basic Model Structure

```python
class ResourceModel(BaseModel):
    """Model for resource configurations with folder path."""

    # Container/location field (always required)
    folder: str = Field(..., description="Folder path for the resource")

    # Identity field (always required)
    name: str = Field(..., description="Name of the resource")

    # Type-specific required fields
    required_field: type = Field(..., description="Description of required field")

    # Optional fields with defaults
    description: str = Field("", description="Description of the resource")
    tags: list[str] = Field(default_factory=list, description="List of tags")

    # Type-specific optional fields
    optional_field: type | None = Field(None, description="Description of optional field")
```

### Model Naming Convention

- Use PascalCase for model class names
- Match the resource type name (e.g., `AddressGroup`, `SecurityRule`)
- Don't include "Model" suffix in the name
- Be consistent with SDK naming where applicable

## Field Definitions

### Field Declaration Patterns

```python
# Required fields - use ellipsis
folder: str = Field(..., description="Folder path for the resource")
name: str = Field(..., min_length=1, max_length=63, description="Name of the resource")

# Optional fields with empty defaults
description: str = Field("", description="Description of the resource")

# Optional fields with None default
ip_netmask: str | None = None

# List fields with factory
tags: list[str] = Field(default_factory=list, description="List of tags")

# List fields with specific defaults
source_addresses: list[str] = Field(default_factory=lambda: ["any"], description="List of source addresses")

services: list[str] = Field(default_factory=list, description="List of services")

# Boolean fields with defaults
enabled: bool = Field(True, description="Whether the rule is enabled")

# Numeric fields
bandwidth: int = Field(..., description="Bandwidth value in Mbps")
```

**Guidance:**

- Always use `default_factory=list` for all list fields, even if not required, for consistency and type safety.
- For fields with a default value other than empty, use a lambda (e.g., `default_factory=lambda: ["any"]`).

### Field Constraints

```python
# String length constraints
name: str = Field(..., min_length=1, max_length=63)

# Numeric constraints
port: int = Field(..., ge=1, le=65535)
bandwidth: int = Field(..., gt=0)

# Pattern constraints
ip_address: str = Field(..., pattern=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")

# Enum constraints (using literal strings)
mode: str = Field(..., description="Zone mode (L2, L3, external, virtual-wire, tunnel)")
action: str = Field("allow", description="Action to take")

# Container/context validation (exactly one of folder, snippet, device)
@model_validator(mode="after")
def validate_container(self) -> "ModelName":
    """Validate that exactly one container context is provided (folder, snippet, or device).

    Returns:
        ModelName: The validated model instance
    Raises:
        ValueError: If zero or more than one container context is provided
    """
    locations = [self.folder, self.snippet, self.device]
    if sum(x is not None for x in locations) != 1:
        raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be specified.")
    return self
```

**Guidance:**

- Always validate container context for all models representing containerized resources.
- Use clear, actionable error messages for all field and context validations.

### Field Descriptions

- Always include a description for every field
- Be concise but clear
- Include valid values for constrained fields
- Use consistent terminology

## Validation Patterns

### Model Validators

```python
@model_validator(mode="after")
def validate_resource(self) -> "ResourceModel":
    """Validate resource constraints.

    Returns:
        ResourceModel: The validated resource model
    Raises:
        ValueError: If validation fails
    """
    # Validation logic
    if some_condition:
        raise ValueError("Clear error message")
    return self
```

### Common Validation Patterns

#### Mutually Exclusive Fields

```python
@model_validator(mode="after")
def validate_address_type(self) -> "Address":
    """Validate that exactly one address type is provided.

    Returns:
        Address: The validated address object
    Raises:
        ValueError: If zero or multiple address types are provided
    """
    address_fields = ["ip_netmask", "ip_range", "ip_wildcard", "fqdn"]
    provided = [field for field in address_fields if getattr(self, field) is not None]
    if len(provided) == 0:
        raise ValueError("Exactly one of 'ip_netmask', 'ip_range', 'ip_wildcard', or 'fqdn' must be provided.")
    elif len(provided) > 1:
        raise ValueError("Only one of 'ip_netmask', 'ip_range', 'ip_wildcard', or 'fqdn' can be provided.")
    return self
```

**Guidance:**

- Use `@model_validator(mode="after")` for all complex field or context validations.
- Always return `self` from validators.
- Write clear, actionable error messages for all validation failures.

#### Conditional Requirements

```python
@model_validator(mode="after")
def validate_group_type(self) -> "AddressGroup":
    """Validate group type specific requirements."""
    if self.type == "dynamic" and not self.filter:
        raise ValueError("Dynamic groups require a filter expression")

    if self.type == "static" and not self.members:
        raise ValueError("Static groups require at least one member")

    return self
```

## Type Annotations

### Import Requirements

```python
from typing import Any, TypeVar
```

### Type Patterns

```python
# Basic types
field: str
field: int
field: bool

# Optional types (use union syntax)
field: str | None
field: list[str] | None

# Lists
tags: list[str]
members: list[str]

# Complex types
data: dict[str, Any]

# Type variables
ModelT = TypeVar("ModelT", bound=BaseModel)
```

### Generic Model Type

```python
# Define at module level
ModelT = TypeVar("ModelT", bound=BaseModel)

# Use in utility functions
def validate_yaml_file(data: dict[str, Any], model_class: type[ModelT], key: str) -> list[ModelT]:
```

## SDK Model Conversion

### Conversion Method Pattern

```python
def to_sdk_model(self) -> dict[str, Any]:
    """Convert CLI model to SDK model format."""
    # Basic field mapping
    model_data = {
        "name": self.name,
        "description": self.description,
    }

    # Handle optional fields
    if self.tags:
        model_data["tags"] = self.tags

    # Handle type-specific logic
    if self.type == "static":
        model_data["type"] = "static"
        model_data["members"] = self.members
    else:
        model_data["type"] = "dynamic"
        # Handle dynamic fields

    return model_data
```

### Field Mapping Patterns

```python
# Direct mapping
"name": self.name

# Field name changes
"allocated_bandwidth": self.bandwidth  # CLI uses 'bandwidth', SDK uses 'allocated_bandwidth'

# Conditional inclusion
if self.description:
    model_data["description"] = self.description

# Default values
"description": self.description or ""

# Nested structures
if self.type == "dynamic":
    model_data["dynamic"] = {"filter": self.filter}
```

## Utility Functions

### YAML Validation Function

```python
def validate_yaml_file(data: dict[str, Any], model_class: type[ModelT], key: str) -> list[ModelT]:
    """Validate a YAML data structure against a Pydantic model.

    Args:
        data: The parsed YAML data
        model_class: The Pydantic model class to validate against
        key: The key in the YAML data that contains the items to validate

    Returns:
        list[ModelT]: A list of validated model instances
    Raises:
        ValueError: If the key is not found in the data or the data is empty
        ValidationError: If any item fails validation
    """
    if not data:
        raise ValueError("YAML data is empty or could not be parsed")
    if key not in data:
        raise ValueError(f"Key '{key}' not found in YAML data")
    items = data[key]
    if not items or not isinstance(items, list):
        raise ValueError(f"'{key}' should be a non-empty list")
    validated_items = []
    for idx, item in enumerate(items):
        try:
            model = model_class(**item)
            validated_items.append(model)
        except Exception as e:
            raise ValueError(f"Validation error in item {idx}: {str(e)}") from e
    return validated_items
```

**Guidance:**

- Always validate YAML file structure and provide actionable error messages.
- Use the same pattern for all bulk load commands.

## Documentation Standards

### Model Class Docstrings

```python
class ResourceModel(BaseModel):
    """Model for resource configurations with folder path."""
```

Or for more complex models:

```python
class Address(BaseModel):
    """Model for address objects with container information.

    Attributes
    ----------
        folder (str): The folder where the address object is located
        name (str): The name of the address object
        description (str): Description of the address object
        tags (List[str]): Tags associated with the address object
        ip_netmask (Optional[str]): IP address with CIDR notation (e.g. "192.168.1.0/24")
        ip_range (Optional[str]): IP address range (e.g. "192.168.1.1-192.168.1.10")
        ip_wildcard (Optional[str]): IP wildcard mask (e.g. "10.20.1.0/0.0.248.255")
        fqdn (Optional[str]): Fully qualified domain name (e.g. "example.com")

    """
```

### Method Docstrings (Google Format)

```python
def to_sdk_model(self) -> dict[str, Any]:
    """Convert CLI model to SDK model format.

    Returns:
        dict[str, Any]: Model data formatted for SDK consumption

    """
```

### Validation Method Docstrings

```python
@model_validator(mode="after")
def validate_constraints(self) -> "ModelName":
    """Validate model-specific constraints.

    Returns:
        ModelName: The validated model instance

    Raises:
        ValueError: If validation constraints are not met

    """
```

## Model Organization Guidelines

### Grouping Related Models

Keep models organized by their configuration type:

- Deployment models together
- Object models together
- Network models together
- Security models together

### Model Dependencies

If models reference each other:

```python
# Forward references if needed
from __future__ import annotations

# Or use string references
related: list["OtherModel"]
```

## Common Patterns by Resource Type

### Address Objects

- Mutually exclusive type fields (ip_netmask, ip_range, ip_wildcard, fqdn)
- Exactly one type must be provided
- Name constraints (min/max length)

### Address Groups

- Type field determines structure (static vs dynamic)
- Static groups have members list
- Dynamic groups have filter expression

### Security Rules

- Lists with defaults (source_addresses default to ["any"])
- Boolean flags (enabled)
- Action constraints

### Zones

- Mode determines valid configurations
- Interface lists

## Code Review Checklist

- [ ] Models organized by configuration type with section separators
- [ ] All fields have descriptions
- [ ] Required fields use `...` in Field()
- [ ] Optional fields have appropriate defaults
- [ ] Field constraints are properly defined
- [ ] Model validators handle edge cases
- [ ] Clear error messages in validators
- [ ] Type annotations use modern syntax (|)
- [ ] to_sdk_model() handles field mapping correctly
- [ ] Docstrings follow Google format
- [ ] Utility functions have comprehensive error handling
- [ ] 191-character separators used for sections
