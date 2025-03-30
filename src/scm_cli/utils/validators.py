"""
Model validators for scm-cli.

This module defines Pydantic models for validating input data structures before
sending them to the SCM API. These models enforce data integrity and ensure
that all required fields are present and correctly formatted.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class BandwidthAllocation(BaseModel):
    """Model for bandwidth allocation configurations."""
    
    name: str = Field(..., description="Name of the bandwidth allocation")
    folder: str = Field(..., description="Folder path for the bandwidth allocation")
    bandwidth: int = Field(..., description="Bandwidth value in Mbps")
    description: str = Field("", description="Description of the bandwidth allocation")
    tags: List[str] = Field(default_factory=list, description="List of tags")


class AddressGroup(BaseModel):
    """Model for address group configurations."""
    
    name: str = Field(..., description="Name of the address group")
    folder: str = Field(..., description="Folder path for the address group")
    type: str = Field(..., description="Type of address group (static or dynamic)")
    members: List[str] = Field(default_factory=list, description="List of addresses in the group")
    description: str = Field("", description="Description of the address group")
    tags: List[str] = Field(default_factory=list, description="List of tags")


class Zone(BaseModel):
    """Model for security zone configurations."""
    
    name: str = Field(..., description="Name of the zone")
    folder: str = Field(..., description="Folder path for the zone")
    mode: str = Field(..., description="Zone mode (L2, L3, external, virtual-wire, tunnel)")
    interfaces: List[str] = Field(default_factory=list, description="List of interfaces")
    description: str = Field("", description="Description of the zone")
    tags: List[str] = Field(default_factory=list, description="List of tags")


class SecurityRule(BaseModel):
    """Model for security rule configurations."""
    
    name: str = Field(..., description="Name of the security rule")
    folder: str = Field(..., description="Folder path for the security rule")
    source_zones: List[str] = Field(..., description="List of source zones")
    destination_zones: List[str] = Field(..., description="List of destination zones")
    source_addresses: List[str] = Field(default_factory=lambda: ["any"], description="List of source addresses")
    destination_addresses: List[str] = Field(default_factory=lambda: ["any"], description="List of destination addresses")
    applications: List[str] = Field(default_factory=lambda: ["any"], description="List of applications")
    action: str = Field("allow", description="Action to take (allow, deny)")
    description: str = Field("", description="Description of the security rule")
    tags: List[str] = Field(default_factory=list, description="List of tags")
