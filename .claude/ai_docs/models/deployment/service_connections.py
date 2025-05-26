"""Service Connections models for Strata Cloud Manager SDK.

Contains Pydantic models for representing service connection objects and related data.
"""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OnboardingType(str, Enum):
    """Types of onboarding for service connections."""

    CLASSIC = "classic"


class NoExportCommunity(str, Enum):
    """No export community options for service connections."""

    DISABLED = "Disabled"
    ENABLED_IN = "Enabled-In"
    ENABLED_OUT = "Enabled-Out"
    ENABLED_BOTH = "Enabled-Both"


class BgpPeerModel(BaseModel):
    """BGP peer configuration for service connections."""

    local_ip_address: str | None = Field(None, description="Local IPv4 address for BGP peering")
    local_ipv6_address: str | None = Field(None, description="Local IPv6 address for BGP peering")
    peer_ip_address: str | None = Field(None, description="Peer IPv4 address for BGP peering")
    peer_ipv6_address: str | None = Field(None, description="Peer IPv6 address for BGP peering")
    secret: str | None = Field(None, description="BGP authentication secret")


class BgpProtocolModel(BaseModel):
    """BGP protocol configuration for service connections."""

    do_not_export_routes: bool | None = Field(None, description="Do not export routes option")
    enable: bool | None = Field(None, description="Enable BGP")
    fast_failover: bool | None = Field(None, description="Enable fast failover")
    local_ip_address: str | None = Field(None, description="Local IPv4 address for BGP peering")
    originate_default_route: bool | None = Field(None, description="Originate default route")
    peer_as: str | None = Field(None, description="BGP peer AS number")
    peer_ip_address: str | None = Field(None, description="Peer IPv4 address for BGP peering")
    secret: str | None = Field(None, description="BGP authentication secret")
    summarize_mobile_user_routes: bool | None = Field(None, description="Summarize mobile user routes")


class ProtocolModel(BaseModel):
    """Protocol configuration for service connections."""

    bgp: BgpProtocolModel | None = Field(None, description="BGP protocol configuration")


class QosModel(BaseModel):
    """QoS configuration for service connections."""

    enable: bool | None = Field(None, description="Enable QoS")
    qos_profile: str | None = Field(None, description="QoS profile name")


class ServiceConnectionBaseModel(BaseModel):
    """Base model for Service Connections containing fields common to all operations."""

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    name: str = Field(
        ...,
        description="The name of the service connection",
        pattern=r"^[0-9a-zA-Z._\- ]+$",  # Pattern includes whitespace
        max_length=63,
    )
    folder: str | None = Field(
        "Service Connections",
        description="The folder containing the service connection",
    )
    ipsec_tunnel: str = Field(..., description="IPsec tunnel for the service connection")
    onboarding_type: OnboardingType = Field(OnboardingType.CLASSIC, description="Onboarding type for the service connection")
    region: str = Field(..., description="Region for the service connection")
    backup_SC: str | None = Field(None, description="Backup service connection")
    bgp_peer: BgpPeerModel | None = Field(None, description="BGP peer configuration")
    nat_pool: str | None = Field(None, description="NAT pool for the service connection")
    no_export_community: NoExportCommunity | None = Field(None, description="No export community configuration")
    protocol: ProtocolModel | None = Field(None, description="Protocol configuration")
    qos: QosModel | None = Field(None, description="QoS configuration")
    secondary_ipsec_tunnel: str | None = Field(None, description="Secondary IPsec tunnel")
    source_nat: bool | None = Field(None, description="Enable source NAT")
    subnets: list[str] | None = Field(None, description="Subnets for the service connection")


class ServiceConnectionCreateModel(ServiceConnectionBaseModel):
    """Model for creating new Service Connections."""

    id: str | None = None


class ServiceConnectionUpdateModel(ServiceConnectionBaseModel):
    """Model for updating existing Service Connections."""

    id: UUID = Field(
        ...,
        description="The UUID of the service connection",
        examples=["123e4567-e89b-12d3-a456-426655440000"],
    )


class ServiceConnectionResponseModel(ServiceConnectionBaseModel):
    """Model for Service Connection responses."""

    id: UUID = Field(
        ...,
        description="The UUID of the service connection",
        examples=["123e4567-e89b-12d3-a456-426655440000"],
    )
