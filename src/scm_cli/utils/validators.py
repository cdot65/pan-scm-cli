"""Model validators for scm-cli.

This module defines Pydantic models for validating input data structures before
sending them to the SCM API. These models enforce data integrity and ensure
that all required fields are present and correctly formatted.
"""

from typing import Any, TypeVar

from pydantic import BaseModel, Field

# Create a type variable bound to BaseModel
ModelT = TypeVar("ModelT", bound=BaseModel)


class BandwidthAllocation(BaseModel):
    """Model for bandwidth allocation configurations."""

    name: str = Field(..., description="Name of the bandwidth allocation")
    folder: str = Field(..., description="Folder path for the bandwidth allocation")
    bandwidth: int = Field(..., description="Bandwidth value in Mbps")
    description: str = Field("", description="Description of the bandwidth allocation")
    tags: list[str] = Field(default_factory=list, description="List of tags")


class AddressGroup(BaseModel):
    """Model for address group configurations."""

    name: str = Field(..., description="Name of the address group")
    folder: str = Field(..., description="Folder path for the address group")
    type: str = Field(..., description="Type of address group (static or dynamic)")
    members: list[str] = Field(default_factory=list, description="List of addresses in the group")
    description: str = Field("", description="Description of the address group")
    tags: list[str] = Field(default_factory=list, description="List of tags")


class Zone(BaseModel):
    """Model for security zone configurations."""

    name: str = Field(..., description="Name of the zone")
    folder: str = Field(..., description="Folder path for the zone")
    mode: str = Field(..., description="Zone mode (L2, L3, external, virtual-wire, tunnel)")
    interfaces: list[str] = Field(default_factory=list, description="List of interfaces")
    description: str = Field("", description="Description of the zone")
    tags: list[str] = Field(default_factory=list, description="List of tags")


class SecurityRule(BaseModel):
    """Model for security rule configurations."""

    name: str = Field(..., description="Name of the security rule")
    folder: str = Field(..., description="Folder path for the security rule")
    source_zones: list[str] = Field(..., description="List of source zones")
    destination_zones: list[str] = Field(..., description="List of destination zones")
    source_addresses: list[str] = Field(default_factory=lambda: ["any"], description="List of source addresses")
    destination_addresses: list[str] = Field(default_factory=lambda: ["any"], description="List of destination addresses")
    applications: list[str] = Field(default_factory=lambda: ["any"], description="List of applications")
    action: str = Field("allow", description="Action for the rule (allow, deny, drop)")
    description: str = Field("", description="Description of the security rule")
    tags: list[str] = Field(default_factory=list, description="List of tags")


def validate_yaml_file(data: dict[str, Any], model_class: type[ModelT], key: str) -> list[ModelT]:
    """Validate a YAML data structure against a Pydantic model.

    Args:
    ----
        data: The parsed YAML data
        model_class: The Pydantic model class to validate against
        key: The key in the YAML data that contains the items to validate

    Returns:
    -------
        A list of validated model instances

    Raises:
    ------
        ValueError: If the key is not found in the data or the data is empty
        ValidationError: If any item fails validation

    """
    if not data:
        raise ValueError("Empty data structure")

    if key not in data:
        raise ValueError(f"Missing '{key}' section in data")

    items = data[key]
    validated_items = []

    for item in items:
        validated_item = model_class(**item)
        validated_items.append(validated_item)

    return validated_items
