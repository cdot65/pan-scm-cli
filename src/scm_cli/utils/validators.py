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


class BandwidthAllocation(BaseModel):
    """Model for bandwidth allocation configurations with folder path."""

    folder: str = Field(..., description="Folder path for the bandwidth allocation")
    name: str = Field(..., description="Name of the bandwidth allocation")
    bandwidth: int = Field(..., description="Bandwidth value in Mbps")
    description: str = Field("", description="Description of the bandwidth allocation")
    tags: list[str] = Field(default_factory=list, description="List of tags")

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        return {"name": self.name, "allocated_bandwidth": self.bandwidth, "description": self.description, "tags": self.tags}


# ========================================================================================================================================================================================
# OBJECTS CONFIGURATION MODELS
# ========================================================================================================================================================================================


class AddressGroup(BaseModel):
    """Model for address group configurations with folder path."""

    folder: str = Field(..., description="Folder path for the address group")
    name: str = Field(..., description="Name of the address group")
    type: str = Field(..., description="Type of address group (static or dynamic)")
    members: list[str] = Field(default_factory=list, description="List of addresses in the group")
    description: str = Field("", description="Description of the address group")
    tags: list[str] = Field(default_factory=list, description="List of tags")

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {"name": self.name, "description": self.description, "tags": self.tags}

        if self.type == "static":
            model_data["type"] = "static"
            model_data["members"] = self.members
        else:
            model_data["type"] = "dynamic"
            # Handle dynamic group fields if needed

        return model_data


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

    folder: str = Field(..., description="Folder containing the address object")
    name: str = Field(..., min_length=1, max_length=63, description="Name of the address object")
    description: str = Field("", description="Description of the address object")
    tags: list[str] = Field(default_factory=list, description="Tags associated with the address object")

    # Address type fields - exactly one must be provided
    ip_netmask: str | None = Field(None, description="IP address with CIDR notation")
    ip_range: str | None = Field(None, description="IP address range")
    ip_wildcard: str | None = Field(None, description="IP wildcard mask")
    fqdn: str | None = Field(None, description="Fully qualified domain name")

    @model_validator(mode="after")
    def validate_address_type(self) -> "Address":
        """Validate that exactly one address type is provided.

        Returns
        -------
            Address: The validated address object

        Raises
        ------
            ValueError: If zero or multiple address types are provided

        """
        address_fields = ["ip_netmask", "ip_range", "ip_wildcard", "fqdn"]
        provided = [field for field in address_fields if getattr(self, field) is not None]

        if len(provided) == 0:
            raise ValueError("Exactly one of 'ip_netmask', 'ip_range', 'ip_wildcard', or 'fqdn' must be provided.")
        elif len(provided) > 1:
            raise ValueError("Only one of 'ip_netmask', 'ip_range', 'ip_wildcard', or 'fqdn' can be provided.")

        return self


# ========================================================================================================================================================================================
# NETWORK CONFIGURATION MODELS
# ========================================================================================================================================================================================


class Zone(BaseModel):
    """Model for security zone configurations with folder path."""

    folder: str = Field(..., description="Folder path for the zone")
    name: str = Field(..., description="Name of the zone")
    network: dict[str, Any] = Field(default_factory=dict, description="Network configuration")
    description: str | None = Field(None, description="Description of the zone")
    snippet: str | None = Field(None, description="Snippet location")
    device: str | None = Field(None, description="Device location")
    enable_user_identification: bool | None = Field(None, description="Enable user identification")
    enable_device_identification: bool | None = Field(None, description="Enable device identification")
    tags: list[str] | None = Field(None, description="List of tags")

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        # Extract mode and interfaces from network config
        mode = "layer3"  # default
        interfaces = []

        if self.network:
            if "layer3" in self.network:
                mode = "layer3"
                interfaces = self.network.get("layer3", [])
            elif "layer2" in self.network:
                mode = "layer2"
                interfaces = self.network.get("layer2", [])
            elif "virtual_wire" in self.network:
                mode = "virtual-wire"
                interfaces = self.network.get("virtual_wire", [])
            elif "tap" in self.network:
                mode = "tap"
                interfaces = self.network.get("tap", [])
            elif "external" in self.network:
                mode = "external"
                interfaces = self.network.get("external", [])
            elif "tunnel" in self.network:
                mode = "tunnel"
                interfaces = self.network.get("tunnel", [])

        return {
            "name": self.name,
            "mode": mode,
            "interfaces": interfaces,
            "description": self.description or "",
            "tags": self.tags or [],
        }


# ========================================================================================================================================================================================
# SECURITY CONFIGURATION MODELS
# ========================================================================================================================================================================================


class SecurityRule(BaseModel):
    """Model for security rule configurations with folder path."""

    folder: str = Field(..., description="Folder path for the security rule")
    name: str = Field(..., description="Name of the security rule")
    rulebase: str = Field("pre", description="Rulebase (pre, post, or default)")
    source_zones: list[str] = Field(default_factory=lambda: ["any"], description="List of source zones")
    destination_zones: list[str] = Field(default_factory=lambda: ["any"], description="List of destination zones")
    source_addresses: list[str] = Field(default_factory=lambda: ["any"], description="List of source addresses")
    destination_addresses: list[str] = Field(default_factory=lambda: ["any"], description="List of destination addresses")
    applications: list[str] = Field(default_factory=lambda: ["any"], description="List of applications")
    service: list[str] = Field(default_factory=lambda: ["any"], description="List of services")
    action: str = Field("allow", description="Action to take")
    description: str | None = Field(None, description="Description of the security rule")
    tags: list[str] | None = Field(None, description="List of tags")
    enabled: bool = Field(True, description="Whether the rule is enabled")
    tag: list[str] | None = Field(None, description="Alternative tags field from API")
    source_user: list[str] | None = Field(None, description="Source users")
    source_hip: list[str] | None = Field(None, description="Source HIP profiles")
    destination_hip: list[str] | None = Field(None, description="Destination HIP profiles")
    category: list[str] | None = Field(None, description="URL categories")
    negate_source: bool | None = Field(None, description="Negate source")
    negate_destination: bool | None = Field(None, description="Negate destination")

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        # Use tag field if tags is not provided
        tags_list = self.tags if self.tags is not None else (self.tag or [])

        return {
            "folder": self.folder,
            "name": self.name,
            "source_zones": self.source_zones,
            "destination_zones": self.destination_zones,
            "source_addresses": self.source_addresses,
            "destination_addresses": self.destination_addresses,
            "applications": self.applications,
            "action": self.action,
            "description": self.description or "",
            "tags": tags_list,
            "enabled": self.enabled,
            "rulebase": self.rulebase,
        }


# ========================================================================================================================================================================================
# UTILITY FUNCTIONS
# ========================================================================================================================================================================================


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
