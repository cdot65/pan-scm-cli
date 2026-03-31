"""Model validators for scm-cli.

This module defines integrations with SDK Pydantic models for validating input data structures before
sending them to the SCM API. These models enforce data integrity and ensure
that all required fields are present and correctly formatted.
"""

from typing import Any, ClassVar, TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

# =============================================================================================================================================================================================
# TYPE DEFINITIONS
# =============================================================================================================================================================================================

# Create a type variable bound to BaseModel
ModelT = TypeVar("ModelT", bound=BaseModel)

# =============================================================================================================================================================================================
# SASE DEPLOYMENT CONFIGURATION MODELS
# =============================================================================================================================================================================================


class BandwidthAllocation(BaseModel):
    """Model for bandwidth allocation configurations (global resource, no folder)."""

    name: str = Field(..., description="Name of the bandwidth allocation")
    bandwidth: int = Field(..., description="Bandwidth value in Mbps")
    spn_name_list: list[str] = Field(..., min_length=1, description="List of SPN names to associate with allocation")
    tags: list[str] = Field(default_factory=list, description="List of tags")

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        return {
            "name": self.name,
            "allocated_bandwidth": self.bandwidth,
            "spn_name_list": self.spn_name_list,
            "tags": self.tags,
        }


class ServiceConnection(BaseModel):
    """Model for service connection configurations."""

    name: str = Field(..., max_length=63, pattern=r"^[0-9a-zA-Z._\- ]+$", description="Name of the service connection")
    folder: str = Field("Service Connections", description="The folder containing the service connection")
    ipsec_tunnel: str = Field(..., description="IPsec tunnel for the service connection")
    region: str = Field(..., description="Region for the service connection")
    onboarding_type: str = Field("classic", description="Onboarding type for the service connection")
    backup_sc: str | None = Field(None, alias="backup_SC", description="Backup service connection")
    nat_pool: str | None = Field(None, description="NAT pool for the service connection")
    no_export_community: str | None = Field(None, description="No export community configuration")
    source_nat: bool | None = Field(None, description="Enable source NAT")
    subnets: list[str] | None = Field(None, description="Subnets for the service connection")
    secondary_ipsec_tunnel: str | None = Field(None, description="Secondary IPsec tunnel")

    # BGP peer configuration
    bgp_peer_local_ip_address: str | None = Field(None, description="Local IPv4 address for BGP peering")
    bgp_peer_local_ipv6_address: str | None = Field(None, description="Local IPv6 address for BGP peering")
    bgp_peer_peer_ip_address: str | None = Field(None, description="Peer IPv4 address for BGP peering")
    bgp_peer_peer_ipv6_address: str | None = Field(None, description="Peer IPv6 address for BGP peering")
    bgp_peer_secret: str | None = Field(None, description="BGP authentication secret")

    # BGP protocol configuration
    bgp_enable: bool | None = Field(None, description="Enable BGP")
    bgp_do_not_export_routes: bool | None = Field(None, description="Do not export routes option")
    bgp_fast_failover: bool | None = Field(None, description="Enable fast failover")
    bgp_local_ip_address: str | None = Field(None, description="Local IPv4 address for BGP peering")
    bgp_originate_default_route: bool | None = Field(None, description="Originate default route")
    bgp_peer_as: str | None = Field(None, description="BGP peer AS number")
    bgp_peer_ip_address: str | None = Field(None, description="Peer IPv4 address for BGP peering")
    bgp_secret: str | None = Field(None, description="BGP authentication secret")
    bgp_summarize_mobile_user_routes: bool | None = Field(None, description="Summarize mobile user routes")

    # QoS configuration
    qos_enable: bool | None = Field(None, description="Enable QoS")
    qos_profile: str | None = Field(None, description="QoS profile name")

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
            "ipsec_tunnel": self.ipsec_tunnel,
            "region": self.region,
            "onboarding_type": self.onboarding_type,
        }

        # Add optional fields if present
        if self.backup_sc:
            model_data["backup_SC"] = self.backup_sc
        if self.nat_pool:
            model_data["nat_pool"] = self.nat_pool
        if self.no_export_community:
            model_data["no_export_community"] = self.no_export_community
        if self.source_nat is not None:
            model_data["source_nat"] = self.source_nat
        if self.subnets:
            model_data["subnets"] = self.subnets
        if self.secondary_ipsec_tunnel:
            model_data["secondary_ipsec_tunnel"] = self.secondary_ipsec_tunnel

        # Build BGP peer configuration if any field is set
        if any([self.bgp_peer_local_ip_address, self.bgp_peer_local_ipv6_address, self.bgp_peer_peer_ip_address, self.bgp_peer_peer_ipv6_address, self.bgp_peer_secret]):
            bgp_peer = {}
            if self.bgp_peer_local_ip_address:
                bgp_peer["local_ip_address"] = self.bgp_peer_local_ip_address
            if self.bgp_peer_local_ipv6_address:
                bgp_peer["local_ipv6_address"] = self.bgp_peer_local_ipv6_address
            if self.bgp_peer_peer_ip_address:
                bgp_peer["peer_ip_address"] = self.bgp_peer_peer_ip_address
            if self.bgp_peer_peer_ipv6_address:
                bgp_peer["peer_ipv6_address"] = self.bgp_peer_peer_ipv6_address
            if self.bgp_peer_secret:
                bgp_peer["secret"] = self.bgp_peer_secret
            model_data["bgp_peer"] = bgp_peer

        # Build BGP protocol configuration if any field is set
        if any(
            [
                self.bgp_enable is not None,
                self.bgp_do_not_export_routes is not None,
                self.bgp_fast_failover is not None,
                self.bgp_local_ip_address,
                self.bgp_originate_default_route is not None,
                self.bgp_peer_as,
                self.bgp_peer_ip_address,
                self.bgp_secret,
                self.bgp_summarize_mobile_user_routes is not None,
            ]
        ):
            bgp = {}
            if self.bgp_enable is not None:
                bgp["enable"] = self.bgp_enable
            if self.bgp_do_not_export_routes is not None:
                bgp["do_not_export_routes"] = self.bgp_do_not_export_routes
            if self.bgp_fast_failover is not None:
                bgp["fast_failover"] = self.bgp_fast_failover
            if self.bgp_local_ip_address:
                bgp["local_ip_address"] = self.bgp_local_ip_address
            if self.bgp_originate_default_route is not None:
                bgp["originate_default_route"] = self.bgp_originate_default_route
            if self.bgp_peer_as:
                bgp["peer_as"] = self.bgp_peer_as
            if self.bgp_peer_ip_address:
                bgp["peer_ip_address"] = self.bgp_peer_ip_address
            if self.bgp_secret:
                bgp["secret"] = self.bgp_secret
            if self.bgp_summarize_mobile_user_routes is not None:
                bgp["summarize_mobile_user_routes"] = self.bgp_summarize_mobile_user_routes
            model_data["protocol"] = {"bgp": bgp}

        # Build QoS configuration if any field is set
        if self.qos_enable is not None or self.qos_profile:
            qos = {}
            if self.qos_enable is not None:
                qos["enable"] = self.qos_enable
            if self.qos_profile:
                qos["qos_profile"] = self.qos_profile
            model_data["qos"] = qos

        return model_data


class RemoteNetwork(BaseModel):
    """Model for remote network configurations."""

    name: str = Field(..., max_length=63, pattern=r"^[A-Za-z][0-9A-Za-z._-]*$", description="Name of the remote network")
    folder: str = Field(..., description="Folder containing the remote network")
    region: str = Field(..., description="Region for the remote network")
    license_type: str = Field("FWAAS-AGGREGATE", description="License type")
    description: str | None = Field(None, max_length=1023, description="Description of the remote network")
    subnets: list[str] | None = Field(None, description="Subnets for the remote network")
    spn_name: str | None = Field(None, description="SPN name (needed when license_type is FWAAS-AGGREGATE)")
    ecmp_load_balancing: str = Field("disable", description="Enable or disable ECMP load balancing")
    ecmp_tunnels: list[dict[str, Any]] | None = Field(None, max_length=4, description="ECMP tunnel configurations")
    ipsec_tunnel: str | None = Field(None, description="IPsec tunnel (required when ecmp_load_balancing is disable)")
    secondary_ipsec_tunnel: str | None = Field(None, description="Secondary IPsec tunnel")

    # BGP configuration
    bgp_enable: bool | None = Field(None, description="Enable BGP")
    bgp_do_not_export_routes: bool | None = Field(None, description="Do not export routes")
    bgp_local_ip_address: str | None = Field(None, description="Local IP address for BGP")
    bgp_originate_default_route: bool | None = Field(None, description="Originate default route")
    bgp_peer_as: str | None = Field(None, description="BGP peer AS number")
    bgp_peer_ip_address: str | None = Field(None, description="Peer IP address for BGP")
    bgp_peering_type: str | None = Field(None, description="BGP peering type")
    bgp_secret: str | None = Field(None, description="BGP secret")
    bgp_summarize_mobile_user_routes: bool | None = Field(None, description="Summarize mobile user routes")

    @model_validator(mode="after")
    def validate_ecmp_settings(self) -> "RemoteNetwork":
        """Validate ECMP and tunnel settings."""
        if self.ecmp_load_balancing == "enable":
            if not self.ecmp_tunnels:
                raise ValueError("ecmp_tunnels is required when ecmp_load_balancing is enable")
        else:
            if not self.ipsec_tunnel:
                raise ValueError("ipsec_tunnel is required when ecmp_load_balancing is disable")

        if self.license_type == "FWAAS-AGGREGATE" and not self.spn_name:
            raise ValueError("spn_name is required when license_type is FWAAS-AGGREGATE")

        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
            "region": self.region,
            "license_type": self.license_type,
            "ecmp_load_balancing": self.ecmp_load_balancing,
        }

        # Add optional fields if present
        if self.description:
            model_data["description"] = self.description
        if self.subnets:
            model_data["subnets"] = self.subnets
        if self.spn_name:
            model_data["spn_name"] = self.spn_name
        if self.ecmp_tunnels:
            model_data["ecmp_tunnels"] = self.ecmp_tunnels
        if self.ipsec_tunnel:
            model_data["ipsec_tunnel"] = self.ipsec_tunnel
        if self.secondary_ipsec_tunnel:
            model_data["secondary_ipsec_tunnel"] = self.secondary_ipsec_tunnel

        # Build BGP protocol configuration if any field is set
        if any(
            [
                self.bgp_enable is not None,
                self.bgp_do_not_export_routes is not None,
                self.bgp_local_ip_address,
                self.bgp_originate_default_route is not None,
                self.bgp_peer_as,
                self.bgp_peer_ip_address,
                self.bgp_peering_type,
                self.bgp_secret,
                self.bgp_summarize_mobile_user_routes is not None,
            ]
        ):
            bgp = {}
            if self.bgp_enable is not None:
                bgp["enable"] = self.bgp_enable
            if self.bgp_do_not_export_routes is not None:
                bgp["do_not_export_routes"] = self.bgp_do_not_export_routes
            if self.bgp_local_ip_address:
                bgp["local_ip_address"] = self.bgp_local_ip_address
            if self.bgp_originate_default_route is not None:
                bgp["originate_default_route"] = self.bgp_originate_default_route
            if self.bgp_peer_as:
                bgp["peer_as"] = self.bgp_peer_as
            if self.bgp_peer_ip_address:
                bgp["peer_ip_address"] = self.bgp_peer_ip_address
            if self.bgp_peering_type:
                bgp["peering_type"] = self.bgp_peering_type
            if self.bgp_secret:
                bgp["secret"] = self.bgp_secret
            if self.bgp_summarize_mobile_user_routes is not None:
                bgp["summarize_mobile_user_routes"] = self.bgp_summarize_mobile_user_routes
            model_data["protocol"] = {"bgp": bgp}

        return model_data


# =============================================================================================================================================================================================
# OBJECTS CONFIGURATION MODELS
# =============================================================================================================================================================================================


class AddressGroup(BaseModel):
    """Model for address group configurations with folder path."""

    folder: str = Field(..., description="Folder path for the address group")
    name: str = Field(..., description="Name of the address group")
    type: str = Field(..., description="Type of address group (static or dynamic)")
    members: list[str] = Field(default_factory=list, description="List of addresses in the group (for static groups)")
    filter: str | None = Field(None, description="Filter expression for dynamic address groups")
    description: str = Field("", description="Description of the address group")
    tags: list[str] = Field(default_factory=list, description="List of tags")

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
        }

        if self.type == "static":
            model_data["type"] = "static"
            model_data["members"] = self.members
        else:
            model_data["type"] = "dynamic"
            if self.filter:
                model_data["filter"] = self.filter

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


class AutoTagAction(BaseModel):
    """Model for auto tag action configurations."""

    name: str = Field(..., max_length=127, description="Name of the auto tag action")
    folder: str | None = Field(None, description="Folder location")
    snippet: str | None = Field(None, description="Snippet location")
    device: str | None = Field(None, description="Device location")
    description: str | None = Field(None, max_length=1023, description="Description")
    actions: list[dict[str, Any]] = Field(default_factory=list, description="List of tag actions")
    filter: str | None = Field(None, description="Filter expression for matching")
    log_type: str | None = Field(None, description="Log type to match (e.g., traffic, threat)")
    send_to_panorama: bool | None = Field(None, description="Send to Panorama")
    quarantine: bool | None = Field(None, description="Enable quarantine action")
    tags: list[str] = Field(default_factory=list, description="Tags to apply")

    @model_validator(mode="after")
    def check_container_set(self) -> "AutoTagAction":
        """Ensure at least one container field is set when needed."""
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        data: dict[str, Any] = {
            "name": self.name,
        }
        if self.folder:
            data["folder"] = self.folder
        if self.snippet:
            data["snippet"] = self.snippet
        if self.device:
            data["device"] = self.device
        if self.description:
            data["description"] = self.description
        if self.actions:
            data["actions"] = self.actions
        if self.filter:
            data["filter"] = self.filter
        if self.log_type:
            data["log_type"] = self.log_type
        if self.send_to_panorama is not None:
            data["send_to_panorama"] = self.send_to_panorama
        if self.quarantine is not None:
            data["quarantine"] = self.quarantine
        if self.tags:
            data["tags"] = self.tags
        return data


class Application(BaseModel):
    """Model for application configurations with folder path."""

    folder: str = Field(..., description="Folder path for the application")
    name: str = Field(..., min_length=1, max_length=63, description="Name of the application")
    category: str = Field(..., max_length=50, description="High-level category")
    subcategory: str = Field(..., max_length=50, description="Specific sub-category")
    technology: str = Field(..., max_length=50, description="Underlying technology")
    risk: int = Field(..., ge=1, le=5, description="Risk level (1-5)")
    description: str = Field("", max_length=1023, description="Description of the application")
    ports: list[str] = Field(default_factory=list, description="Associated TCP/UDP ports")
    evasive: bool = Field(False, description="Uses evasive techniques")
    pervasive: bool = Field(False, description="Widely used")
    excessive_bandwidth_use: bool = Field(False, description="Uses excessive bandwidth")
    used_by_malware: bool = Field(False, description="Used by malware")
    transfers_files: bool = Field(False, description="Transfers files")
    has_known_vulnerabilities: bool = Field(False, description="Has known vulnerabilities")
    tunnels_other_apps: bool = Field(False, description="Tunnels other applications")
    prone_to_misuse: bool = Field(False, description="Prone to misuse")
    no_certifications: bool = Field(False, description="Lacks certifications")

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
            "category": self.category,
            "subcategory": self.subcategory,
            "technology": self.technology,
            "risk": self.risk,
            "description": self.description,
        }

        # Add optional fields only if they are not default values
        if self.ports:
            model_data["ports"] = self.ports
        if self.evasive:
            model_data["evasive"] = self.evasive
        if self.pervasive:
            model_data["pervasive"] = self.pervasive
        if self.excessive_bandwidth_use:
            model_data["excessive_bandwidth_use"] = self.excessive_bandwidth_use
        if self.used_by_malware:
            model_data["used_by_malware"] = self.used_by_malware
        if self.transfers_files:
            model_data["transfers_files"] = self.transfers_files
        if self.has_known_vulnerabilities:
            model_data["has_known_vulnerabilities"] = self.has_known_vulnerabilities
        if self.tunnels_other_apps:
            model_data["tunnels_other_apps"] = self.tunnels_other_apps
        if self.prone_to_misuse:
            model_data["prone_to_misuse"] = self.prone_to_misuse
        if self.no_certifications:
            model_data["no_certifications"] = self.no_certifications

        return model_data


class ApplicationGroup(BaseModel):
    """Model for application group configurations with folder path."""

    folder: str = Field(..., description="Folder path for the application group")
    name: str = Field(..., min_length=1, max_length=63, description="Name of the application group")
    members: list[str] = Field(..., min_length=1, description="List of application names")

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        return {
            "name": self.name,
            "members": self.members,
        }


class ApplicationFilter(BaseModel):
    """Model for application filter configurations with folder path."""

    folder: str = Field(..., description="Folder path for the application filter")
    name: str = Field(..., min_length=1, max_length=63, description="Name of the application filter")
    category: list[str] = Field(..., min_length=1, description="List of category strings")
    subcategory: list[str] = Field(..., min_length=1, description="List of subcategory strings")
    technology: list[str] = Field(..., min_length=1, description="List of technology strings")
    risk: list[int] = Field(..., min_length=1, description="List of risk levels (1-5)")
    evasive: bool = Field(False, description="Filter for apps that use evasive techniques")
    pervasive: bool = Field(False, description="Filter for apps that are widely used")
    excessive_bandwidth_use: bool = Field(False, description="Filter for apps that use excessive bandwidth")
    used_by_malware: bool = Field(False, description="Filter for apps used by malware")
    transfers_files: bool = Field(False, description="Filter for apps that transfer files")
    has_known_vulnerabilities: bool = Field(False, description="Filter for apps with known vulnerabilities")
    tunnels_other_apps: bool = Field(False, description="Filter for apps that tunnel other applications")
    prone_to_misuse: bool = Field(False, description="Filter for apps prone to misuse")
    no_certifications: bool = Field(False, description="Filter for apps lacking certifications")

    @model_validator(mode="after")
    def validate_risk_values(self) -> "ApplicationFilter":
        """Validate that all risk values are between 1 and 5.

        Returns:
            ApplicationFilter: The validated application filter object

        Raises:
            ValueError: If any risk value is out of range

        """
        for risk_value in self.risk:
            if risk_value < 1 or risk_value > 5:
                raise ValueError(f"Risk value {risk_value} is out of range. Must be between 1 and 5.")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
            "category": self.category,
            "sub_category": self.subcategory,
            "technology": self.technology,
            "risk": self.risk,
        }

        # Add boolean fields only if they are True
        if self.evasive:
            model_data["evasive"] = self.evasive
        if self.pervasive:
            model_data["pervasive"] = self.pervasive
        if self.excessive_bandwidth_use:
            model_data["excessive_bandwidth_use"] = self.excessive_bandwidth_use
        if self.used_by_malware:
            model_data["used_by_malware"] = self.used_by_malware
        if self.transfers_files:
            model_data["transfers_files"] = self.transfers_files
        if self.has_known_vulnerabilities:
            model_data["has_known_vulnerabilities"] = self.has_known_vulnerabilities
        if self.tunnels_other_apps:
            model_data["tunnels_other_apps"] = self.tunnels_other_apps
        if self.prone_to_misuse:
            model_data["prone_to_misuse"] = self.prone_to_misuse
        if self.no_certifications:
            model_data["no_certifications"] = self.no_certifications

        return model_data


class DynamicUserGroup(BaseModel):
    """Model for dynamic user group configurations with folder path."""

    folder: str = Field(..., description="Folder path for the dynamic user group")
    name: str = Field(..., min_length=1, max_length=63, description="Name of the dynamic user group")
    filter: str = Field(..., max_length=2047, description="Tag-based filter expression")
    description: str = Field("", max_length=1023, description="Description of the dynamic user group")
    tags: list[str] = Field(default_factory=list, description="Tags associated with the dynamic user group")

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
            "filter": self.filter,
            "description": self.description,
        }

        if self.tags:
            model_data["tag"] = self.tags  # SDK expects 'tag', not 'tags'

        return model_data


class ExternalDynamicList(BaseModel):
    """Model for external dynamic list configurations with folder path."""

    folder: str = Field(..., description="Folder path for the external dynamic list")
    name: str = Field(
        ...,
        min_length=1,
        max_length=63,
        pattern=r"^[ a-zA-Z\d.\-_]+$",
        description="Name of the external dynamic list",
    )
    type: str = Field(
        ...,
        description="Type of EDL (predefined_ip, predefined_url, ip, domain, url, imsi, imei)",
    )

    # Type-specific configurations
    url: str = Field("", max_length=255, description="URL for the external list")
    description: str = Field("", max_length=255, description="Description of the external dynamic list")
    exception_list: list[str] = Field(default_factory=list, description="Exception list entries")

    # For custom EDLs (ip, domain, url, imsi, imei)
    recurring: str | None = Field(
        None,
        description="Update frequency (five_minute, hourly, daily, weekly, monthly)",
    )
    hour: str | None = Field(
        None,
        pattern=r"([01][0-9]|[2][0-3])",
        description="Hour for daily/weekly/monthly updates (00-23)",
    )
    day: str | None = Field(None, description="Day for weekly (sunday-saturday) or monthly (1-31) updates")

    # Authentication
    username: str | None = Field(None, max_length=255, description="Authentication username")
    password: str | None = Field(None, max_length=255, description="Authentication password")
    certificate_profile: str | None = Field(None, description="Certificate profile for authentication")

    # Domain-specific
    expand_domain: bool = Field(False, description="Enable/Disable expand domain (for domain type)")

    @model_validator(mode="after")
    def validate_edl_type(self) -> "ExternalDynamicList":
        """Validate EDL type and required fields."""
        valid_types = [
            "predefined_ip",
            "predefined_url",
            "ip",
            "domain",
            "url",
            "imsi",
            "imei",
        ]
        if self.type not in valid_types:
            raise ValueError(f"Invalid EDL type '{self.type}'. Must be one of: {', '.join(valid_types)}")

        # Custom EDLs require recurring configuration
        if self.type in ["ip", "domain", "url", "imsi", "imei"] and not self.recurring:
            raise ValueError(f"EDL type '{self.type}' requires 'recurring' configuration")

        # Validate recurring settings
        if self.recurring:
            if self.recurring in ["daily", "weekly", "monthly"] and not self.hour:
                raise ValueError(f"Recurring '{self.recurring}' requires 'hour' to be set")
            if self.recurring == "weekly" and not self.day:
                raise ValueError("Recurring 'weekly' requires 'day' to be set (sunday-saturday)")
            if self.recurring == "monthly" and not self.day:
                raise ValueError("Recurring 'monthly' requires 'day' to be set (1-31)")

        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {"name": self.name}

        # Build the type configuration
        type_config = {}

        if self.type in ["predefined_ip", "predefined_url"]:
            # Predefined types are simpler
            type_config["url"] = self.url
            if self.description:
                type_config["description"] = self.description
            if self.exception_list:
                type_config["exception_list"] = self.exception_list

            model_data["type"] = {self.type: type_config}
        else:
            # Custom types require more configuration
            type_config["url"] = self.url
            if self.description:
                type_config["description"] = self.description
            if self.exception_list:
                type_config["exception_list"] = self.exception_list

            # Add authentication if provided
            if self.username and self.password:
                type_config["auth"] = {
                    "username": self.username,
                    "password": self.password,
                }

            if self.certificate_profile:
                type_config["certificate_profile"] = self.certificate_profile

            # Add recurring configuration
            if self.recurring == "five_minute":
                type_config["recurring"] = {"five_minute": {}}
            elif self.recurring == "hourly":
                type_config["recurring"] = {"hourly": {}}
            elif self.recurring == "daily":
                type_config["recurring"] = {"daily": {"at": self.hour}}
            elif self.recurring == "weekly":
                type_config["recurring"] = {"weekly": {"day_of_week": self.day, "at": self.hour}}
            elif self.recurring == "monthly":
                type_config["recurring"] = {
                    "monthly": {
                        "day_of_month": int(self.day) if self.day else 1,
                        "at": self.hour,
                    }
                }

            # Add domain-specific options
            if self.type == "domain" and self.expand_domain:
                type_config["expand_domain"] = self.expand_domain

            model_data["type"] = {self.type: type_config}

        return model_data


class HIPObject(BaseModel):
    """Model for HIP object configurations with folder path."""

    folder: str = Field(..., description="Folder path for the HIP object")
    name: str = Field(
        ...,
        min_length=1,
        max_length=31,
        pattern=r"^[ a-zA-Z0-9.\-_]+$",
        description="Name of the HIP object",
    )
    description: str = Field("", max_length=255, description="Description of the HIP object")

    # Host information criteria
    host_info_domain: str | None = Field(None, description="Domain criteria (is, is_not, contains)")
    host_info_domain_value: str | None = Field(None, max_length=255, description="Domain value to match")
    host_info_os: str | None = Field(None, description="OS vendor (Microsoft, Apple, Google, Linux, Other)")
    host_info_os_value: str | None = Field(None, max_length=255, description="OS value (All or specific version)")
    host_info_client_version: str | None = Field(None, description="Client version criteria (is, is_not, contains)")
    host_info_client_version_value: str | None = Field(None, max_length=255, description="Client version value")
    host_info_host_name: str | None = Field(None, description="Host name criteria (is, is_not, contains)")
    host_info_host_name_value: str | None = Field(None, max_length=255, description="Host name value")
    host_info_host_id: str | None = Field(None, description="Host ID criteria (is, is_not, contains)")
    host_info_host_id_value: str | None = Field(None, max_length=255, description="Host ID value")
    host_info_managed: bool | None = Field(None, description="Managed state criteria")
    host_info_serial_number: str | None = Field(None, description="Serial number criteria (is, is_not, contains)")
    host_info_serial_number_value: str | None = Field(None, max_length=255, description="Serial number value")

    # Network information
    network_info_type: str | None = Field(None, description="Network type (is, is_not)")
    network_info_value: str | None = Field(None, description="Network value (wifi, mobile, ethernet, unknown)")

    # Patch management
    patch_management_enabled: bool | None = Field(None, description="Whether patch management is enabled")
    patch_management_missing_patches: str | None = Field(None, description="Missing patches check (has-any, has-none, has-all)")
    patch_management_severity: int | None = Field(None, ge=0, le=100000, description="Patch severity level")
    patch_management_patches: list[str] | None = Field(None, description="List of specific patches")
    patch_management_vendors: list[dict[str, Any]] | None = Field(None, description="Vendor specifications")

    # Disk encryption
    disk_encryption_enabled: bool | None = Field(None, description="Whether disk encryption is enabled")
    disk_encryption_locations: list[dict[str, Any]] | None = Field(None, description="Encryption location specifications")
    disk_encryption_vendors: list[dict[str, Any]] | None = Field(None, description="Vendor specifications")

    # Mobile device
    mobile_device_jailbroken: bool | None = Field(None, description="Jailbroken status")
    mobile_device_disk_encrypted: bool | None = Field(None, description="Disk encryption status")
    mobile_device_passcode_set: bool | None = Field(None, description="Passcode status")
    mobile_device_last_checkin_time: str | None = Field(None, description="Last check-in time type (days, hours)")
    mobile_device_last_checkin_value: int | None = Field(None, ge=1, le=65535, description="Last check-in time value")
    mobile_device_has_malware: bool | None = Field(None, description="Malware presence")
    mobile_device_has_unmanaged_app: bool | None = Field(None, description="Unmanaged apps presence")
    mobile_device_applications: list[dict[str, Any]] | None = Field(None, description="Application specifications")

    # Certificate
    certificate_profile: str | None = Field(None, description="Certificate profile name")
    certificate_attributes: list[dict[str, Any]] | None = Field(None, description="Certificate attribute specifications")

    @model_validator(mode="after")
    def validate_criteria_pairs(self) -> "HIPObject":
        """Validate that criteria and value pairs are properly matched."""
        # Host info validations
        if self.host_info_domain and not self.host_info_domain_value:
            raise ValueError("host_info_domain requires host_info_domain_value")
        if self.host_info_domain_value and not self.host_info_domain:
            raise ValueError("host_info_domain_value requires host_info_domain")

        if self.host_info_os and not self.host_info_os_value:
            raise ValueError("host_info_os requires host_info_os_value")
        if self.host_info_os_value and not self.host_info_os:
            raise ValueError("host_info_os_value requires host_info_os")

        # Network info validation
        if self.network_info_type and not self.network_info_value:
            raise ValueError("network_info_type requires network_info_value")
        if self.network_info_value and not self.network_info_type:
            raise ValueError("network_info_value requires network_info_type")

        # Mobile device time validation
        if self.mobile_device_last_checkin_time and not self.mobile_device_last_checkin_value:
            raise ValueError("mobile_device_last_checkin_time requires mobile_device_last_checkin_value")
        if self.mobile_device_last_checkin_value and not self.mobile_device_last_checkin_time:
            raise ValueError("mobile_device_last_checkin_value requires mobile_device_last_checkin_time")

        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
        }

        if self.description:
            model_data["description"] = self.description

        # Build host info criteria
        if any(
            [
                self.host_info_domain,
                self.host_info_os,
                self.host_info_client_version,
                self.host_info_host_name,
                self.host_info_host_id,
                self.host_info_managed is not None,
                self.host_info_serial_number,
            ]
        ):
            criteria = {}

            # String comparisons
            if self.host_info_domain and self.host_info_domain_value:
                if self.host_info_domain == "is":
                    criteria["domain"] = {"is": self.host_info_domain_value}
                elif self.host_info_domain == "is_not":
                    criteria["domain"] = {"is_not": self.host_info_domain_value}
                elif self.host_info_domain == "contains":
                    criteria["domain"] = {"contains": self.host_info_domain_value}

            if self.host_info_client_version and self.host_info_client_version_value:
                if self.host_info_client_version == "is":
                    criteria["client_version"] = {"is": self.host_info_client_version_value}
                elif self.host_info_client_version == "is_not":
                    criteria["client_version"] = {"is_not": self.host_info_client_version_value}
                elif self.host_info_client_version == "contains":
                    criteria["client_version"] = {"contains": self.host_info_client_version_value}

            if self.host_info_host_name and self.host_info_host_name_value:
                if self.host_info_host_name == "is":
                    criteria["host_name"] = {"is": self.host_info_host_name_value}
                elif self.host_info_host_name == "is_not":
                    criteria["host_name"] = {"is_not": self.host_info_host_name_value}
                elif self.host_info_host_name == "contains":
                    criteria["host_name"] = {"contains": self.host_info_host_name_value}

            if self.host_info_host_id and self.host_info_host_id_value:
                if self.host_info_host_id == "is":
                    criteria["host_id"] = {"is": self.host_info_host_id_value}
                elif self.host_info_host_id == "is_not":
                    criteria["host_id"] = {"is_not": self.host_info_host_id_value}
                elif self.host_info_host_id == "contains":
                    criteria["host_id"] = {"contains": self.host_info_host_id_value}

            if self.host_info_serial_number and self.host_info_serial_number_value:
                if self.host_info_serial_number == "is":
                    criteria["serial_number"] = {"is": self.host_info_serial_number_value}
                elif self.host_info_serial_number == "is_not":
                    criteria["serial_number"] = {"is_not": self.host_info_serial_number_value}
                elif self.host_info_serial_number == "contains":
                    criteria["serial_number"] = {"contains": self.host_info_serial_number_value}

            # OS criteria
            if self.host_info_os and self.host_info_os_value:
                criteria["os"] = {"contains": {self.host_info_os: self.host_info_os_value}}  # type: ignore[dict-item]

            # Managed state
            if self.host_info_managed is not None:
                criteria["managed"] = self.host_info_managed

            model_data["host_info"] = {"criteria": criteria}

        # Build network info
        if self.network_info_type and self.network_info_value:
            network_criteria: dict[str, Any] = {}
            if self.network_info_type == "is":
                network_criteria["network"] = {"is": {self.network_info_value: {}}}
            elif self.network_info_type == "is_not":
                network_criteria["network"] = {"is_not": {self.network_info_value: {}}}
            model_data["network_info"] = {"criteria": network_criteria}

        # Build patch management
        if self.patch_management_enabled is not None:
            patch_criteria = {"is_installed": self.patch_management_enabled}

            if self.patch_management_missing_patches:
                missing_patches = {"check": self.patch_management_missing_patches}
                if self.patch_management_severity is not None:
                    missing_patches["severity"] = self.patch_management_severity
                if self.patch_management_patches:
                    missing_patches["patches"] = self.patch_management_patches
                patch_criteria["missing_patches"] = missing_patches

            patch_mgmt = {"criteria": patch_criteria}
            if self.patch_management_vendors:
                patch_mgmt["vendor"] = self.patch_management_vendors

            model_data["patch_management"] = patch_mgmt

        # Build disk encryption
        if self.disk_encryption_enabled is not None:
            disk_criteria = {"is_installed": self.disk_encryption_enabled}

            if self.disk_encryption_locations:
                disk_criteria["encrypted_locations"] = self.disk_encryption_locations

            disk_enc = {"criteria": disk_criteria}
            if self.disk_encryption_vendors:
                disk_enc["vendor"] = self.disk_encryption_vendors

            model_data["disk_encryption"] = disk_enc

        # Build mobile device
        if any(
            [
                self.mobile_device_jailbroken is not None,
                self.mobile_device_disk_encrypted is not None,
                self.mobile_device_passcode_set is not None,
                self.mobile_device_last_checkin_time,
                self.mobile_device_has_malware is not None,
                self.mobile_device_has_unmanaged_app is not None,
                self.mobile_device_applications,
            ]
        ):
            mobile_criteria = {}

            if self.mobile_device_jailbroken is not None:
                mobile_criteria["jailbroken"] = self.mobile_device_jailbroken
            if self.mobile_device_disk_encrypted is not None:
                mobile_criteria["disk_encrypted"] = self.mobile_device_disk_encrypted
            if self.mobile_device_passcode_set is not None:
                mobile_criteria["passcode_set"] = self.mobile_device_passcode_set

            if self.mobile_device_last_checkin_time and self.mobile_device_last_checkin_value:
                mobile_criteria["last_checkin_time"] = {self.mobile_device_last_checkin_time: self.mobile_device_last_checkin_value}

            if self.mobile_device_has_malware is not None or self.mobile_device_has_unmanaged_app is not None or self.mobile_device_applications:
                applications = {}
                if self.mobile_device_has_malware is not None:
                    applications["has_malware"] = self.mobile_device_has_malware
                if self.mobile_device_has_unmanaged_app is not None:
                    applications["has_unmanaged_app"] = self.mobile_device_has_unmanaged_app
                if self.mobile_device_applications:
                    applications["includes"] = self.mobile_device_applications
                mobile_criteria["applications"] = applications

            model_data["mobile_device"] = {"criteria": mobile_criteria}

        # Build certificate
        if self.certificate_profile or self.certificate_attributes:
            cert_criteria = {}
            if self.certificate_profile:
                cert_criteria["certificate_profile"] = self.certificate_profile
            if self.certificate_attributes:
                cert_criteria["certificate_attributes"] = self.certificate_attributes
            model_data["certificate"] = {"criteria": cert_criteria}

        return model_data


class HIPProfile(BaseModel):
    """Model for HIP profile configurations with folder path."""

    folder: str = Field(..., description="Folder path for the HIP profile")
    name: str = Field(
        ...,
        min_length=1,
        max_length=31,
        pattern=r"^[a-zA-Z\d\-_. ]+$",
        description="Name of the HIP profile",
    )
    description: str | None = Field(None, max_length=255, description="Description of the HIP profile")
    match: str = Field(..., max_length=2048, description="Match criteria for the HIP profile")

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "folder": self.folder,
            "name": self.name,
            "match": self.match,
        }

        if self.description:
            model_data["description"] = self.description

        return model_data


class HTTPServerProfile(BaseModel):
    """Model for HTTP server profile configurations with folder path."""

    folder: str = Field(..., description="Folder path for the HTTP server profile")
    name: str = Field(
        ...,
        min_length=1,
        max_length=63,
        description="Name of the HTTP server profile",
    )
    description: str | None = Field(None, description="Description of the HTTP server profile")
    tag_registration: bool = Field(False, description="Register tags on match")

    # Server configurations - at least one required
    servers: list[dict[str, Any]] = Field(
        ...,
        min_length=1,
        description="List of HTTP server configurations",
    )

    # Format configurations for different log types
    format_config: dict[str, dict[str, Any]] | None = Field(
        None,
        description="Format settings for different log types",
    )

    @model_validator(mode="after")
    def validate_servers(self) -> "HTTPServerProfile":
        """Validate server configurations."""
        for idx, server in enumerate(self.servers):
            # Required fields
            if "name" not in server:
                raise ValueError(f"Server {idx}: 'name' is required")
            if "address" not in server:
                raise ValueError(f"Server {idx}: 'address' is required")
            if "protocol" not in server:
                raise ValueError(f"Server {idx}: 'protocol' is required")
            if "port" not in server:
                raise ValueError(f"Server {idx}: 'port' is required")

            # Validate protocol
            if server["protocol"] not in ["HTTP", "HTTPS"]:
                raise ValueError(f"Server {idx}: protocol must be 'HTTP' or 'HTTPS'")

            # Validate port
            try:
                port = int(server["port"])
                if port < 1 or port > 65535:
                    raise ValueError(f"Server {idx}: port must be between 1 and 65535")
            except (TypeError, ValueError) as err:
                raise ValueError(f"Server {idx}: port must be a valid integer") from err

            # HTTPS-specific validations
            if server["protocol"] == "HTTPS" and "tls_version" in server and server["tls_version"] not in ["1.0", "1.1", "1.2", "1.3"]:
                raise ValueError(f"Server {idx}: tls_version must be one of: 1.0, 1.1, 1.2, 1.3")

            # Validate HTTP method if present
            if "http_method" in server and server["http_method"] not in [
                "GET",
                "POST",
                "PUT",
                "DELETE",
            ]:
                raise ValueError(f"Server {idx}: http_method must be one of: GET, POST, PUT, DELETE")

        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "folder": self.folder,
            "name": self.name,
            "server": self.servers,
        }

        if self.description:
            model_data["description"] = self.description

        if self.tag_registration:
            model_data["tag_registration"] = self.tag_registration

        if self.format_config:
            model_data["format"] = self.format_config

        return model_data


class LogForwardingProfile(BaseModel):
    """Model for log forwarding profile configurations with folder path."""

    folder: str = Field(..., description="Folder path for the log forwarding profile")
    name: str = Field(
        ...,
        min_length=1,
        max_length=63,
        description="Name of the log forwarding profile",
    )
    description: str | None = Field(None, max_length=255, description="Description of the log forwarding profile")
    enhanced_application_logging: bool = Field(False, description="Enable enhanced application logging")

    # Match list configurations - at least one can be defined
    match_list: list[dict[str, Any]] | None = Field(
        None,
        description="List of match profile configurations",
    )

    @model_validator(mode="after")
    def validate_match_list(self) -> "LogForwardingProfile":
        """Validate match list configurations."""
        if self.match_list:
            for idx, match in enumerate(self.match_list):
                # Required fields
                if "name" not in match:
                    raise ValueError(f"Match list {idx}: 'name' is required")
                if "log_type" not in match:
                    raise ValueError(f"Match list {idx}: 'log_type' is required")

                # Validate log type
                valid_log_types = [
                    "traffic",
                    "threat",
                    "wildfire",
                    "url",
                    "data",
                    "tunnel",
                    "auth",
                    "decryption",
                    "dns-security",
                ]
                if match["log_type"] not in valid_log_types:
                    raise ValueError(f"Match list {idx}: log_type must be one of: {', '.join(valid_log_types)}")

                # At least one action is required
                actions = ["send_http", "send_syslog", "send_to_panorama", "quarantine"]
                if not any(match.get(action) for action in actions):
                    raise ValueError(f"Match list {idx}: At least one action must be specified (send_http, send_syslog, send_to_panorama, or quarantine)")

        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "folder": self.folder,
            "name": self.name,
        }

        if self.description:
            model_data["description"] = self.description

        if self.enhanced_application_logging:
            model_data["enhanced_application_logging"] = self.enhanced_application_logging

        if self.match_list:
            model_data["match_list"] = self.match_list

        return model_data


class Region(BaseModel):
    """Model for region configurations with folder path."""

    folder: str = Field(..., description="Folder path for the region")
    name: str = Field(
        ...,
        description="Name of the region",
        max_length=64,
    )
    latitude: float | None = Field(None, description="Latitude of the region (-90 to 90)", ge=-90, le=90)
    longitude: float | None = Field(None, description="Longitude of the region (-180 to 180)", ge=-180, le=180)
    addresses: list[str] | None = Field(None, description="List of address CIDRs")
    snippet: str | None = Field(None, description="Snippet location")
    device: str | None = Field(None, description="Device location")

    @field_validator("folder", "snippet", "device")
    def validate_container(
        cls,
        v: str | None,
        info: ValidationInfo,
    ) -> str | None:
        """Validate that exactly one container field is set."""
        if v is not None:
            values = info.data
            containers = ["folder", "snippet", "device"]
            field_name = info.field_name
            other_containers = [c for c in containers if c != field_name]

            for container in other_containers:
                if values.get(container) is not None:
                    raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")

        return v

    @model_validator(mode="after")
    def check_container_set(self) -> "Region":
        """Ensure exactly one container field is set."""
        containers_set = sum(1 for field in ["folder", "snippet", "device"] if getattr(self, field) is not None)

        if containers_set != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")

        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {
            "name": self.name,
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Add geo_location if latitude/longitude provided
        if self.latitude is not None and self.longitude is not None:
            model_data["geo_location"] = {
                "latitude": self.latitude,
                "longitude": self.longitude,
            }

        # Add addresses
        if self.addresses:
            model_data["address"] = self.addresses

        return model_data


class QuarantinedDevice(BaseModel):
    """Model for quarantined device configurations."""

    host_id: str = Field(..., description="Device host ID")
    serial_number: str | None = Field(None, description="Device serial number")

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {
            "host_id": self.host_id,
        }

        if self.serial_number:
            model_data["serial_number"] = self.serial_number

        return model_data


class Service(BaseModel):
    """Model for service configurations with folder path."""

    folder: str = Field(..., description="Folder path for the service")
    name: str = Field(
        ...,
        min_length=1,
        max_length=63,
        pattern=r"^[a-zA-Z0-9_\-. ]+$",
        description="Name of the service",
    )
    description: str | None = Field(None, max_length=1023, description="Description of the service")
    tag: list[str] | None = Field(None, description="Tags for filtering and grouping")
    protocol: dict[str, Any] = Field(..., description="Protocol configuration (TCP or UDP)")

    @model_validator(mode="after")
    def validate_service(self) -> "Service":
        """Validate service configuration."""
        # Check protocol structure
        if not self.protocol:
            raise ValueError("Protocol configuration is required")

        # Must have exactly one protocol type
        protocol_types = ["tcp", "udp"]
        specified = [p for p in protocol_types if p in self.protocol]

        if len(specified) != 1:
            raise ValueError("Exactly one protocol type (tcp or udp) must be specified")

        protocol_type = specified[0]
        protocol_config = self.protocol[protocol_type]

        # Validate port configuration
        if "port" not in protocol_config:
            raise ValueError(f"Port configuration is required for {protocol_type.upper()}")

        port = protocol_config["port"]

        # Port can be a string with ranges/lists or an integer
        if isinstance(port, str):
            # Validate port string format
            if "-" in port:
                # Port range
                parts = port.split("-")
                if len(parts) != 2:
                    raise ValueError("Invalid port range format. Use 'start-end'")
                try:
                    start, end = int(parts[0]), int(parts[1])
                    if not (1 <= start <= 65535 and 1 <= end <= 65535):
                        raise ValueError("Port numbers must be between 1 and 65535")
                    if start > end:
                        raise ValueError("Invalid port range: start must be <= end")
                except ValueError as e:
                    if "invalid literal" in str(e):
                        raise ValueError("Port range must contain valid integers") from e
                    raise
            elif "," in port:
                # Comma-separated ports
                ports = [p.strip() for p in port.split(",")]
                for p in ports:
                    try:
                        port_num = int(p)
                        if not (1 <= port_num <= 65535):
                            raise ValueError(f"Port {port_num} must be between 1 and 65535")
                    except ValueError as e:
                        raise ValueError(f"Invalid port number: {p}") from e
            else:
                # Single port
                try:
                    port_num = int(port)
                    if not (1 <= port_num <= 65535):
                        raise ValueError("Port number must be between 1 and 65535")
                except ValueError as e:
                    raise ValueError(f"Invalid port number: {port}") from e
        elif isinstance(port, int):
            if not (1 <= port <= 65535):
                raise ValueError("Port number must be between 1 and 65535")
        else:
            raise ValueError("Port must be a string or integer")

        # Validate override settings if present
        if "override" in protocol_config:
            override = protocol_config["override"]
            if "timeout" in override:
                timeout = override["timeout"]
                if not isinstance(timeout, int) or timeout < 0:
                    raise ValueError("Override timeout must be a non-negative integer")
            if "halfclose_timeout" in override:
                halfclose = override["halfclose_timeout"]
                if not isinstance(halfclose, int) or halfclose < 0:
                    raise ValueError("Override halfclose_timeout must be a non-negative integer")
            if "timewait_timeout" in override:
                timewait = override["timewait_timeout"]
                if not isinstance(timewait, int) or timewait < 0:
                    raise ValueError("Override timewait_timeout must be a non-negative integer")

        # Validate tags
        if self.tag:
            for tag_value in self.tag:
                if not tag_value or len(tag_value) > 127:
                    raise ValueError("Each tag must be between 1 and 127 characters")

        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "folder": self.folder,
            "name": self.name,
            "protocol": self.protocol,
        }

        if self.description:
            model_data["description"] = self.description

        if self.tag:
            model_data["tag"] = self.tag

        return model_data


class ServiceGroup(BaseModel):
    """Model for service group configurations with folder path."""

    folder: str = Field(..., description="Folder path for the service group")
    name: str = Field(
        ...,
        min_length=1,
        max_length=63,
        pattern=r"^[a-zA-Z0-9_ \.-]+$",
        description="Name of the service group",
    )
    members: list[str] = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="List of service or service group names",
    )
    tag: list[str] | None = Field(None, description="Tags for filtering and grouping")

    @model_validator(mode="after")
    def validate_service_group(self) -> "ServiceGroup":
        """Validate service group configuration."""
        # Validate member list has unique values
        if self.members and len(self.members) != len(set(self.members)):
            raise ValueError("Service group members must be unique")

        # Validate tags
        if self.tag:
            for tag_value in self.tag:
                if not tag_value or len(tag_value) > 127:
                    raise ValueError("Each tag must be between 1 and 127 characters")

        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert to SDK model format."""
        model_data = {
            "folder": self.folder,
            "name": self.name,
            "members": self.members,
        }

        if self.tag:
            model_data["tag"] = self.tag

        return model_data


class SyslogServerProfile(BaseModel):
    """Model for syslog server profile configurations with folder path."""

    folder: str = Field(..., description="Folder path for the syslog server profile")
    name: str = Field(..., description="Name of the syslog server profile")
    description: str | None = Field(None, description="Description of the profile")
    server: list[dict[str, Any]] = Field(..., description="List of syslog servers")
    format: dict[str, Any] | None = Field(None, description="Log format settings")
    tag: list[str] | None = Field(None, description="List of tags")
    snippet: str | None = Field(None, description="Snippet location")
    device: str | None = Field(None, description="Device location")

    @field_validator("folder", "snippet", "device")
    def validate_container(cls, v: str | None, info: ValidationInfo) -> str | None:  # noqa: N805
        """Validate that exactly one container field is set."""
        if v is not None:
            # Check other container fields
            values = info.data
            containers = ["folder", "snippet", "device"]
            field_name = info.field_name
            other_containers = [c for c in containers if c != field_name]

            for container in other_containers:
                if values.get(container) is not None:
                    raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")

        return v

    @model_validator(mode="after")
    def check_container_set(self) -> "SyslogServerProfile":
        """Ensure exactly one container field is set."""
        containers_set = sum(1 for field in ["folder", "snippet", "device"] if getattr(self, field) is not None)

        if containers_set != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")

        return self

    @field_validator("server")
    def validate_servers(
        cls,
        v: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:  # noqa: N805
        """Validate server configurations."""
        if not v:
            raise ValueError("At least one server must be specified")

        for server in v:
            # Validate required fields
            if "name" not in server:
                raise ValueError("Server name is required")
            if "server" not in server:
                raise ValueError("Server address is required")
            if "transport" not in server:
                raise ValueError("Server transport is required")
            if "port" not in server:
                raise ValueError("Server port is required")
            if "format" not in server:
                raise ValueError("Server format is required")
            if "facility" not in server:
                raise ValueError("Server facility is required")

            # Validate transport
            if server["transport"] not in ["UDP", "TCP", "SSL"]:
                raise ValueError("Transport must be one of: UDP, TCP, SSL")

            # Validate port
            port = server["port"]
            if not isinstance(port, int) or port < 1 or port > 65535:
                raise ValueError("Port must be between 1 and 65535")

            # Validate format
            if server["format"] not in ["BSD", "IETF"]:
                raise ValueError("Format must be one of: BSD, IETF")

            # Validate facility
            valid_facilities = [
                "LOG_USER",
                "LOG_LOCAL0",
                "LOG_LOCAL1",
                "LOG_LOCAL2",
                "LOG_LOCAL3",
                "LOG_LOCAL4",
                "LOG_LOCAL5",
                "LOG_LOCAL6",
                "LOG_LOCAL7",
            ]
            if server["facility"] not in valid_facilities:
                raise ValueError(f"Facility must be one of: {', '.join(valid_facilities)}")

        return v

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
            "server": self.server,
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Add optional fields
        if self.description:
            model_data["description"] = self.description
        if self.format:
            model_data["format"] = self.format
        if self.tag:
            model_data["tag"] = self.tag

        return model_data


class Schedule(BaseModel):
    """Model for schedule configurations with folder path.

    Supports three schedule types:
    - recurring-daily: Same time ranges every day
    - recurring-weekly: Different time ranges per day of week
    - non-recurring: One-time date/time ranges
    """

    folder: str = Field(..., description="Folder path for the schedule")
    name: str = Field(
        ...,
        description="Name of the schedule",
        pattern=r"^[ a-zA-Z\d._-]+$",
        max_length=31,
    )
    schedule_type: str = Field(
        ...,
        description="Schedule type: recurring-daily, recurring-weekly, or non-recurring",
    )
    time_ranges: list[str] | None = Field(
        None,
        description="List of time ranges (HH:MM-HH:MM for recurring, YYYY/MM/DD@HH:MM-YYYY/MM/DD@HH:MM for non-recurring)",
    )
    days: dict[str, list[str]] | None = Field(
        None,
        description="Day-to-time-range mapping for weekly schedules (e.g., {'monday': ['09:00-17:00']})",
    )
    snippet: str | None = Field(None, description="Snippet location")
    device: str | None = Field(None, description="Device location")

    @field_validator("folder", "snippet", "device")
    def validate_container(
        cls,
        v: str | None,
        info: ValidationInfo,
    ) -> str | None:
        """Validate that exactly one container field is set."""
        if v is not None:
            # Check other container fields
            values = info.data
            containers = ["folder", "snippet", "device"]
            field_name = info.field_name
            other_containers = [c for c in containers if c != field_name]

            for container in other_containers:
                if values.get(container) is not None:
                    raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")

        return v

    @model_validator(mode="after")
    def check_container_set(self) -> "Schedule":
        """Ensure exactly one container field is set."""
        containers_set = sum(1 for field in ["folder", "snippet", "device"] if getattr(self, field) is not None)

        if containers_set != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")

        return self

    @field_validator("schedule_type")
    def validate_schedule_type(cls, v: str) -> str:
        """Validate schedule type is from allowed set."""
        valid_types = ["recurring-daily", "recurring-weekly", "non-recurring"]
        if v not in valid_types:
            raise ValueError(f"Schedule type must be one of: {', '.join(valid_types)}")
        return v

    @model_validator(mode="after")
    def validate_schedule_data(self) -> "Schedule":
        """Validate that required data is provided for the schedule type."""
        if self.schedule_type == "recurring-daily":
            if not self.time_ranges:
                raise ValueError("time_ranges is required for recurring-daily schedules")
        elif self.schedule_type == "recurring-weekly":
            if not self.days:
                raise ValueError("days is required for recurring-weekly schedules")
        elif self.schedule_type == "non-recurring" and not self.time_ranges:
            raise ValueError("time_ranges is required for non-recurring schedules")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {
            "name": self.name,
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Build schedule_type structure
        if self.schedule_type == "recurring-daily":
            model_data["schedule_type"] = {
                "recurring": {
                    "daily": self.time_ranges,
                },
            }
        elif self.schedule_type == "recurring-weekly":
            model_data["schedule_type"] = {
                "recurring": {
                    "weekly": self.days,
                },
            }
        elif self.schedule_type == "non-recurring":
            model_data["schedule_type"] = {
                "non_recurring": self.time_ranges,
            }

        return model_data


class Tag(BaseModel):
    """Model for tag configurations with folder path."""

    folder: str = Field(..., description="Folder path for the tag")
    name: str = Field(
        ...,
        description="Name of the tag",
        pattern=r"^[a-zA-Z0-9_ \.-\[\]\-\&\(\)]+$",
        max_length=127,
    )
    color: str | None = Field(None, description="Color associated with tag")
    comments: str | None = Field(None, description="Comments for the tag", max_length=1023)
    snippet: str | None = Field(None, description="Snippet location")
    device: str | None = Field(None, description="Device location")

    @field_validator("folder", "snippet", "device")
    def validate_container(
        cls,
        v: str | None,
        info: ValidationInfo,
    ) -> str | None:
        """Validate that exactly one container field is set."""
        if v is not None:
            # Check other container fields
            values = info.data
            containers = ["folder", "snippet", "device"]
            field_name = info.field_name
            other_containers = [c for c in containers if c != field_name]

            for container in other_containers:
                if values.get(container) is not None:
                    raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")

        return v

    @model_validator(mode="after")
    def check_container_set(self) -> "Tag":
        """Ensure exactly one container field is set."""
        containers_set = sum(1 for field in ["folder", "snippet", "device"] if getattr(self, field) is not None)

        if containers_set != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")

        return self

    @field_validator("color")
    def validate_color(cls, v: str | None) -> str | None:
        """Validate color is from allowed set."""
        if v is None:
            return v

        # Valid colors from the SDK
        valid_colors = [
            "Azure Blue",
            "Black",
            "Blue",
            "Blue Gray",
            "Blue Violet",
            "Brown",
            "Burnt Sienna",
            "Cerulean Blue",
            "Chestnut",
            "Cobalt Blue",
            "Copper",
            "Cyan",
            "Forest Green",
            "Gold",
            "Gray",
            "Green",
            "Lavender",
            "Light Gray",
            "Light Green",
            "Lime",
            "Magenta",
            "Mahogany",
            "Maroon",
            "Medium Blue",
            "Medium Rose",
            "Medium Violet",
            "Midnight Blue",
            "Olive",
            "Orange",
            "Orchid",
            "Peach",
            "Purple",
            "Red",
            "Red Violet",
            "Red-Orange",
            "Salmon",
            "Thistle",
            "Turquoise Blue",
            "Violet Blue",
            "Yellow",
            "Yellow-Orange",
        ]

        if v not in valid_colors:
            raise ValueError(f"Color must be one of: {', '.join(valid_colors)}")

        return v

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Add optional fields
        if self.color:
            model_data["color"] = self.color
        if self.comments:
            model_data["comments"] = self.comments

        return model_data


# =============================================================================================================================================================================================
# IDENTITY CONFIGURATION MODELS
# =============================================================================================================================================================================================


class AuthenticationProfile(BaseModel):
    """Model for authentication profile configurations."""

    folder: str | None = Field(None, description="Folder path for the authentication profile")
    snippet: str | None = Field(None, description="Snippet path for the authentication profile")
    device: str | None = Field(None, description="Device path for the authentication profile")
    name: str = Field(..., description="Name of the authentication profile")
    method: dict[str, Any] | None = Field(None, description="Authentication method configuration as dict")
    user_domain: str | None = Field(None, description="User domain")
    username_modifier: str | None = Field(None, description="Username modifier pattern")
    lockout: dict[str, Any] | None = Field(None, description="Account lockout configuration")
    allow_list: list[str] | None = Field(None, description="Allow list entries")
    multi_factor_auth: dict[str, Any] | None = Field(None, description="Multi-factor auth configuration")
    single_sign_on: dict[str, Any] | None = Field(None, description="Single sign-on configuration")

    @model_validator(mode="after")
    def validate_container(self) -> "AuthenticationProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}

        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        if self.method:
            model_data["method"] = self.method
        if self.user_domain:
            model_data["user_domain"] = self.user_domain
        if self.username_modifier:
            model_data["username_modifier"] = self.username_modifier
        if self.lockout:
            model_data["lockout"] = self.lockout
        if self.allow_list:
            model_data["allow_list"] = self.allow_list
        if self.multi_factor_auth:
            model_data["multi_factor_auth"] = self.multi_factor_auth
        if self.single_sign_on:
            model_data["single_sign_on"] = self.single_sign_on

        return model_data


class KerberosServerProfile(BaseModel):
    """Model for Kerberos server profile configurations."""

    folder: str | None = Field(None, description="Folder path for the Kerberos server profile")
    snippet: str | None = Field(None, description="Snippet path for the Kerberos server profile")
    device: str | None = Field(None, description="Device path for the Kerberos server profile")
    name: str = Field(..., description="Name of the Kerberos server profile")
    servers: list[dict[str, Any]] | None = Field(None, description="List of Kerberos server configurations")

    @model_validator(mode="after")
    def validate_container(self) -> "KerberosServerProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}

        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        if self.servers:
            model_data["server"] = self.servers

        return model_data


class LdapServerProfile(BaseModel):
    """Model for LDAP server profile configurations."""

    folder: str | None = Field(None, description="Folder path for the LDAP server profile")
    snippet: str | None = Field(None, description="Snippet path for the LDAP server profile")
    device: str | None = Field(None, description="Device path for the LDAP server profile")
    name: str = Field(..., description="Name of the LDAP server profile")
    servers: list[dict[str, Any]] | None = Field(None, description="List of LDAP server configurations")
    base: str | None = Field(None, description="Base distinguished name", max_length=255)
    bind_dn: str | None = Field(None, description="Bind distinguished name", max_length=255)
    bind_password: str | None = Field(None, description="Bind password", max_length=121)
    ldap_type: str | None = Field(None, description="LDAP type (active-directory, e-directory, sun, other)")
    ssl: bool | None = Field(None, description="Enable SSL")

    @model_validator(mode="after")
    def validate_container(self) -> "LdapServerProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @model_validator(mode="after")
    def validate_ldap_type(self) -> "LdapServerProfile":
        """Validate ldap_type if provided."""
        if self.ldap_type and self.ldap_type not in ["active-directory", "e-directory", "sun", "other"]:
            raise ValueError("ldap_type must be one of: active-directory, e-directory, sun, other")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}

        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        if self.servers:
            model_data["server"] = self.servers
        if self.base:
            model_data["base"] = self.base
        if self.bind_dn:
            model_data["bind_dn"] = self.bind_dn
        if self.bind_password:
            model_data["bind_password"] = self.bind_password
        if self.ldap_type:
            model_data["ldap_type"] = self.ldap_type
        if self.ssl is not None:
            model_data["ssl"] = self.ssl

        return model_data


class RadiusServerProfile(BaseModel):
    """Model for RADIUS server profile configurations."""

    folder: str | None = Field(None, description="Folder path for the RADIUS server profile")
    snippet: str | None = Field(None, description="Snippet path for the RADIUS server profile")
    device: str | None = Field(None, description="Device path for the RADIUS server profile")
    name: str = Field(..., description="Name of the RADIUS server profile")
    servers: list[dict[str, Any]] | None = Field(None, description="List of RADIUS server configurations")
    protocol: dict[str, Any] | None = Field(None, description="Protocol configuration (e.g. {'CHAP': {}})")
    timeout: int | None = Field(None, description="Timeout in seconds", ge=1, le=120)
    retries: int | None = Field(None, description="Number of retries", ge=1, le=5)

    @model_validator(mode="after")
    def validate_container(self) -> "RadiusServerProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}

        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        if self.servers:
            model_data["server"] = self.servers
        if self.protocol:
            model_data["protocol"] = self.protocol
        if self.timeout is not None:
            model_data["timeout"] = self.timeout
        if self.retries is not None:
            model_data["retries"] = self.retries

        return model_data


class SamlServerProfile(BaseModel):
    """Model for SAML server profile configurations."""

    folder: str | None = Field(None, description="Folder path for the SAML server profile")
    snippet: str | None = Field(None, description="Snippet path for the SAML server profile")
    device: str | None = Field(None, description="Device path for the SAML server profile")
    name: str = Field(..., description="Name of the SAML server profile")
    entity_id: str = Field(..., description="Entity ID", max_length=1024)
    certificate: str = Field(..., description="Certificate name", max_length=63)
    sso_url: str = Field(..., description="Single Sign-On URL", max_length=255)
    sso_bindings: str = Field(..., description="SSO binding type (post, redirect)")
    slo_bindings: str | None = Field(None, description="SLO binding type (post, redirect)")
    max_clock_skew: int | None = Field(None, description="Maximum clock skew in seconds", ge=1, le=900)
    validate_idp_certificate: bool | None = Field(None, description="Validate IDP certificate")
    want_auth_requests_signed: bool | None = Field(None, description="Want auth requests signed")

    @model_validator(mode="after")
    def validate_container(self) -> "SamlServerProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @model_validator(mode="after")
    def validate_bindings(self) -> "SamlServerProfile":
        """Validate binding types."""
        valid_bindings = ["post", "redirect"]
        if self.sso_bindings not in valid_bindings:
            raise ValueError(f"sso_bindings must be one of: {valid_bindings}")
        if self.slo_bindings and self.slo_bindings not in valid_bindings:
            raise ValueError(f"slo_bindings must be one of: {valid_bindings}")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {
            "name": self.name,
            "entity_id": self.entity_id,
            "certificate": self.certificate,
            "sso_url": self.sso_url,
            "sso_bindings": self.sso_bindings,
        }

        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        if self.slo_bindings:
            model_data["slo_bindings"] = self.slo_bindings
        if self.max_clock_skew is not None:
            model_data["max_clock_skew"] = self.max_clock_skew
        if self.validate_idp_certificate is not None:
            model_data["validate_idp_certificate"] = self.validate_idp_certificate
        if self.want_auth_requests_signed is not None:
            model_data["want_auth_requests_signed"] = self.want_auth_requests_signed

        return model_data


class TacacsServerProfile(BaseModel):
    """Model for TACACS+ server profile configurations."""

    folder: str | None = Field(None, description="Folder path for the TACACS+ server profile")
    snippet: str | None = Field(None, description="Snippet path for the TACACS+ server profile")
    device: str | None = Field(None, description="Device path for the TACACS+ server profile")
    name: str = Field(..., description="Name of the TACACS+ server profile")
    servers: list[dict[str, Any]] | None = Field(None, description="List of TACACS+ server configurations")
    protocol: str | None = Field(None, description="Protocol type (CHAP, PAP)")
    timeout: int | None = Field(None, description="Timeout in seconds", ge=1, le=30)
    use_single_connection: bool | None = Field(None, description="Use single connection")

    @model_validator(mode="after")
    def validate_container(self) -> "TacacsServerProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @model_validator(mode="after")
    def validate_protocol(self) -> "TacacsServerProfile":
        """Validate protocol if provided."""
        if self.protocol and self.protocol not in ["CHAP", "PAP"]:
            raise ValueError("protocol must be one of: CHAP, PAP")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}

        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        if self.servers:
            model_data["server"] = self.servers
        if self.protocol:
            model_data["protocol"] = self.protocol
        if self.timeout is not None:
            model_data["timeout"] = self.timeout
        if self.use_single_connection is not None:
            model_data["use_single_connection"] = self.use_single_connection

        return model_data


# =============================================================================================================================================================================================
# NETWORK CONFIGURATION MODELS
# =============================================================================================================================================================================================


class AggregateInterface(BaseModel):
    """Model for aggregate interface configurations."""

    folder: str | None = Field(None, description="Folder path for the aggregate interface")
    snippet: str | None = Field(None, description="Snippet path for the aggregate interface")
    device: str | None = Field(None, description="Device path for the aggregate interface")
    name: str = Field(
        ...,
        description="Aggregate interface name (e.g. ae1)",
    )
    comment: str | None = Field(None, description="Interface description/comment")
    default_value: str | None = Field(None, description="Default interface assignment")
    layer2: dict[str, Any] | None = Field(None, description="Layer2 configuration (vlan_tag, lacp)")
    layer3: dict[str, Any] | None = Field(None, description="Layer3 configuration (ip, dhcp_client, mtu, arp, lacp)")

    @model_validator(mode="after")
    def validate_container(self) -> "AggregateInterface":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @model_validator(mode="after")
    def validate_interface_mode(self) -> "AggregateInterface":
        """Validate that at most one interface mode is specified."""
        modes = [self.layer2, self.layer3]
        configured = [m for m in modes if m is not None]
        if len(configured) > 1:
            raise ValueError("Only one interface mode allowed: layer2 or layer3")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {
            "name": self.name,
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Add optional fields
        if self.comment:
            model_data["comment"] = self.comment
        if self.default_value:
            model_data["default_value"] = self.default_value
        if self.layer2 is not None:
            model_data["layer2"] = self.layer2
        if self.layer3 is not None:
            model_data["layer3"] = self.layer3

        return model_data


class DhcpInterface(BaseModel):
    """Model for DHCP interface configurations."""

    folder: str | None = Field(None, description="Folder path for the DHCP interface")
    snippet: str | None = Field(None, description="Snippet path for the DHCP interface")
    device: str | None = Field(None, description="Device path for the DHCP interface")
    name: str = Field(..., description="Interface name (e.g. ethernet1/1)")
    server: dict[str, Any] | None = Field(None, description="DHCP server configuration (mode, ip_pool, option, reserved)")
    relay: dict[str, Any] | None = Field(None, description="DHCP relay configuration (ip: {enabled, server})")

    @model_validator(mode="after")
    def validate_container(self) -> "DhcpInterface":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @model_validator(mode="after")
    def validate_server_relay(self) -> "DhcpInterface":
        """Validate that server and relay are mutually exclusive."""
        if self.server is not None and self.relay is not None:
            raise ValueError("Only one of 'server' or 'relay' can be specified")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device
        if self.server is not None:
            model_data["server"] = self.server
        if self.relay is not None:
            model_data["relay"] = self.relay
        return model_data


class EthernetInterface(BaseModel):
    """Model for ethernet interface configurations."""

    folder: str | None = Field(None, description="Folder path for the ethernet interface")
    snippet: str | None = Field(None, description="Snippet path for the ethernet interface")
    device: str | None = Field(None, description="Device path for the ethernet interface")
    name: str = Field(..., description="Ethernet interface variable name (must start with $)")
    comment: str | None = Field(None, description="Interface description/comment")
    default_value: str | None = Field(None, description="Physical interface assignment (e.g. ethernet1/1)")
    link_speed: str | None = Field(None, description="Link speed (auto, 10, 100, 1000, 10000)")
    link_duplex: str | None = Field(None, description="Link duplex (auto, half, full)")
    link_state: str | None = Field(None, description="Link state (auto, up, down)")
    layer2: dict[str, Any] | None = Field(None, description="Layer2 configuration (vlan_tag, lldp)")
    layer3: dict[str, Any] | None = Field(None, description="Layer3 configuration (ip, dhcp_client, mtu, arp)")
    tap: dict[str, Any] | None = Field(None, description="TAP mode configuration")

    @model_validator(mode="after")
    def validate_container(self) -> "EthernetInterface":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @model_validator(mode="after")
    def validate_interface_mode(self) -> "EthernetInterface":
        """Validate that at most one interface mode is specified."""
        modes = [self.layer2, self.layer3, self.tap]
        configured = [m for m in modes if m is not None]
        if len(configured) > 1:
            raise ValueError("Only one interface mode allowed: layer2, layer3, or tap")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device
        if self.comment:
            model_data["comment"] = self.comment
        if self.default_value:
            model_data["default_value"] = self.default_value
        if self.link_speed:
            model_data["link_speed"] = self.link_speed
        if self.link_duplex:
            model_data["link_duplex"] = self.link_duplex
        if self.link_state:
            model_data["link_state"] = self.link_state
        if self.layer2 is not None:
            model_data["layer2"] = self.layer2
        if self.layer3 is not None:
            model_data["layer3"] = self.layer3
        if self.tap is not None:
            model_data["tap"] = self.tap
        return model_data


class Layer2Subinterface(BaseModel):
    """Model for layer2 subinterface configurations."""

    folder: str | None = Field(None, description="Folder path for the layer2 subinterface")
    snippet: str | None = Field(None, description="Snippet path for the layer2 subinterface")
    device: str | None = Field(None, description="Device path for the layer2 subinterface")
    name: str = Field(..., description="Subinterface name (e.g. ethernet1/1.100)")
    vlan_tag: str = Field(..., description="VLAN tag (1-4096)")
    parent_interface: str | None = Field(None, description="Parent interface name")
    comment: str | None = Field(None, description="Interface description/comment")

    @model_validator(mode="after")
    def validate_container(self) -> "Layer2Subinterface":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name, "vlan_tag": self.vlan_tag}
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device
        if self.parent_interface:
            model_data["parent_interface"] = self.parent_interface
        if self.comment:
            model_data["comment"] = self.comment
        return model_data


class Layer3Subinterface(BaseModel):
    """Model for layer3 subinterface configurations."""

    folder: str | None = Field(None, description="Folder path for the layer3 subinterface")
    snippet: str | None = Field(None, description="Snippet path for the layer3 subinterface")
    device: str | None = Field(None, description="Device path for the layer3 subinterface")
    name: str = Field(..., description="Subinterface name (e.g. ethernet1/1.100)")
    tag: int | None = Field(None, description="VLAN tag (1-4096)")
    parent_interface: str | None = Field(None, description="Parent interface name")
    comment: str | None = Field(None, description="Interface description/comment")
    mtu: int | None = Field(None, description="Maximum transmission unit (576-9216)")
    interface_management_profile: str | None = Field(None, description="Interface management profile name")
    ip: list[dict[str, Any]] | None = Field(None, description="Static IP addresses [{name: ip/mask}]")
    dhcp_client: dict[str, Any] | None = Field(None, description="DHCP client configuration")

    @model_validator(mode="after")
    def validate_container(self) -> "Layer3Subinterface":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @model_validator(mode="after")
    def validate_ip_mode(self) -> "Layer3Subinterface":
        """Validate that only one IP addressing mode is configured."""
        if self.ip and self.dhcp_client:
            raise ValueError("Only one IP addressing mode allowed: static IP or DHCP")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device
        if self.tag is not None:
            model_data["tag"] = self.tag
        if self.parent_interface:
            model_data["parent_interface"] = self.parent_interface
        if self.comment:
            model_data["comment"] = self.comment
        if self.mtu is not None:
            model_data["mtu"] = self.mtu
        if self.interface_management_profile:
            model_data["interface_management_profile"] = self.interface_management_profile
        if self.ip is not None:
            model_data["ip"] = self.ip
        if self.dhcp_client is not None:
            model_data["dhcp_client"] = self.dhcp_client
        return model_data


class LoopbackInterface(BaseModel):
    """Model for loopback interface configurations."""

    folder: str | None = Field(None, description="Folder path for the loopback interface")
    snippet: str | None = Field(None, description="Snippet path for the loopback interface")
    device: str | None = Field(None, description="Device path for the loopback interface")
    name: str = Field(..., description="Loopback interface name (variable format, starts with $)")
    comment: str | None = Field(None, description="Interface description/comment")
    default_value: str | None = Field(None, description="Default interface assignment (e.g. loopback.1)")
    mtu: int | None = Field(None, description="Maximum transmission unit (576-9216)")
    interface_management_profile: str | None = Field(None, description="Interface management profile name")
    ip: list[dict[str, Any]] | None = Field(None, description="Static IP addresses [{name: ip/mask}]")
    ipv6: dict[str, Any] | None = Field(None, description="IPv6 configuration")

    @model_validator(mode="after")
    def validate_container(self) -> "LoopbackInterface":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device
        if self.comment:
            model_data["comment"] = self.comment
        if self.default_value:
            model_data["default_value"] = self.default_value
        if self.mtu is not None:
            model_data["mtu"] = self.mtu
        if self.interface_management_profile:
            model_data["interface_management_profile"] = self.interface_management_profile
        if self.ip is not None:
            model_data["ip"] = self.ip
        if self.ipv6 is not None:
            model_data["ipv6"] = self.ipv6
        return model_data


class TunnelInterface(BaseModel):
    """Model for tunnel interface configurations."""

    folder: str | None = Field(None, description="Folder path for the tunnel interface")
    snippet: str | None = Field(None, description="Snippet path for the tunnel interface")
    device: str | None = Field(None, description="Device path for the tunnel interface")
    name: str = Field(..., description="Tunnel interface name")
    comment: str | None = Field(None, description="Interface description/comment")
    default_value: str | None = Field(None, description="Default interface assignment (e.g. tunnel.1)")
    mtu: int | None = Field(None, description="Maximum transmission unit (576-9216)")
    interface_management_profile: str | None = Field(None, description="Interface management profile name")
    ip: list[dict[str, Any]] | None = Field(None, description="Static IP addresses [{name: ip/mask}]")

    @model_validator(mode="after")
    def validate_container(self) -> "TunnelInterface":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device
        if self.comment:
            model_data["comment"] = self.comment
        if self.default_value:
            model_data["default_value"] = self.default_value
        if self.mtu is not None:
            model_data["mtu"] = self.mtu
        if self.interface_management_profile:
            model_data["interface_management_profile"] = self.interface_management_profile
        if self.ip is not None:
            model_data["ip"] = self.ip
        return model_data


class VlanInterface(BaseModel):
    """Model for VLAN interface configurations."""

    folder: str | None = Field(None, description="Folder path for the VLAN interface")
    snippet: str | None = Field(None, description="Snippet path for the VLAN interface")
    device: str | None = Field(None, description="Device path for the VLAN interface")
    name: str = Field(..., description="VLAN interface name")
    comment: str | None = Field(None, description="Interface description/comment")
    default_value: str | None = Field(None, description="Default interface assignment (e.g. vlan.100)")
    vlan_tag: str | None = Field(None, description="VLAN tag (1-4096)")
    mtu: int | None = Field(None, description="Maximum transmission unit (576-9216)")
    interface_management_profile: str | None = Field(None, description="Interface management profile name")
    ip: list[dict[str, Any]] | None = Field(None, description="Static IP addresses [{name: ip/mask}]")
    dhcp_client: dict[str, Any] | None = Field(None, description="DHCP client configuration")

    @model_validator(mode="after")
    def validate_container(self) -> "VlanInterface":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @model_validator(mode="after")
    def validate_ip_mode(self) -> "VlanInterface":
        """Validate that only one IP addressing mode is configured."""
        if self.ip and self.dhcp_client:
            raise ValueError("Only one IP addressing mode allowed: static IP or DHCP")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device
        if self.comment:
            model_data["comment"] = self.comment
        if self.default_value:
            model_data["default_value"] = self.default_value
        if self.vlan_tag:
            model_data["vlan_tag"] = self.vlan_tag
        if self.mtu is not None:
            model_data["mtu"] = self.mtu
        if self.interface_management_profile:
            model_data["interface_management_profile"] = self.interface_management_profile
        if self.ip is not None:
            model_data["ip"] = self.ip
        if self.dhcp_client is not None:
            model_data["dhcp_client"] = self.dhcp_client
        return model_data


class NATRule(BaseModel):
    """Model for NAT rule configurations."""

    folder: str | None = Field(None, description="Folder path for the NAT rule")
    snippet: str | None = Field(None, description="Snippet path for the NAT rule")
    device: str | None = Field(None, description="Device path for the NAT rule")
    name: str = Field(..., description="Name of the NAT rule")
    description: str | None = Field(None, description="Description of the NAT rule")
    tag: list[str] | None = Field(None, description="Tags associated with the NAT rule")
    disabled: bool = Field(False, description="Whether the NAT rule is disabled")
    nat_type: str = Field("ipv4", description="NAT type (ipv4, nat64, nptv6)")
    from_zone: list[str] = Field(default_factory=lambda: ["any"], alias="from", description="Source zone(s)")
    to_zone: list[str] = Field(default_factory=lambda: ["any"], alias="to", description="Destination zone(s)")
    to_interface: str | None = Field(None, description="Destination interface")
    source: list[str] = Field(default_factory=lambda: ["any"], description="Source address(es)")
    destination: list[str] = Field(default_factory=lambda: ["any"], description="Destination address(es)")
    service: str = Field("any", description="TCP/UDP service")
    source_translation: dict[str, Any] | None = Field(None, description="Source translation configuration")
    destination_translation: dict[str, Any] | None = Field(None, description="Destination translation configuration")
    active_active_device_binding: str | None = Field(None, description="Active/Active device binding")

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_container(self) -> "NATRule":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {
            "name": self.name,
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Add optional fields
        if self.description:
            model_data["description"] = self.description
        if self.tag:
            model_data["tag"] = self.tag
        if self.disabled:
            model_data["disabled"] = self.disabled
        if self.nat_type != "ipv4":
            model_data["nat_type"] = self.nat_type

        # Zone fields use 'from' and 'to' aliases in the SDK
        model_data["from_"] = self.from_zone
        model_data["to_"] = self.to_zone
        model_data["source"] = self.source
        model_data["destination"] = self.destination
        model_data["service"] = self.service

        if self.to_interface:
            model_data["to_interface"] = self.to_interface
        if self.source_translation:
            model_data["source_translation"] = self.source_translation
        if self.destination_translation:
            model_data["destination_translation"] = self.destination_translation
        if self.active_active_device_binding:
            model_data["active_active_device_binding"] = self.active_active_device_binding

        return model_data


class IKECryptoProfile(BaseModel):
    """Model for IKE crypto profile configurations."""

    folder: str | None = Field(None, description="Folder path for the IKE crypto profile")
    snippet: str | None = Field(None, description="Snippet path for the IKE crypto profile")
    device: str | None = Field(None, description="Device path for the IKE crypto profile")
    name: str = Field(
        ...,
        description="Name of the IKE crypto profile",
        pattern=r"^[0-9a-zA-Z._-]+$",
        max_length=31,
    )
    hash: list[str] = Field(..., description="Hashing algorithms (md5, sha1, sha256, sha384, sha512)")
    dh_group: list[str] = Field(..., description="Phase-1 DH group (group1, group2, group5, group14, group19, group20)")
    encryption: list[str] = Field(..., description="Encryption algorithms (des, 3des, aes-128-cbc, aes-192-cbc, aes-256-cbc, aes-128-gcm, aes-256-gcm)")
    lifetime_seconds: int | None = Field(None, description="Lifetime in seconds (180-65535)", ge=180, le=65535)
    lifetime_minutes: int | None = Field(None, description="Lifetime in minutes (3-65535)", ge=3, le=65535)
    lifetime_hours: int | None = Field(None, description="Lifetime in hours (1-65535)", ge=1, le=65535)
    lifetime_days: int | None = Field(None, description="Lifetime in days (1-365)", ge=1, le=365)
    authentication_multiple: int | None = Field(None, description="IKEv2 SA reauthentication interval (0-50)", ge=0, le=50)

    @model_validator(mode="after")
    def validate_container(self) -> "IKECryptoProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @model_validator(mode="after")
    def validate_lifetime(self) -> "IKECryptoProfile":
        """Validate that at most one lifetime field is specified."""
        lifetime_fields = [self.lifetime_seconds, self.lifetime_minutes, self.lifetime_hours, self.lifetime_days]
        if sum(1 for f in lifetime_fields if f is not None) > 1:
            raise ValueError("At most one of 'lifetime_seconds', 'lifetime_minutes', 'lifetime_hours', or 'lifetime_days' may be set")
        return self

    @field_validator("hash")
    def validate_hash(cls, v: list[str]) -> list[str]:  # noqa: N805
        """Validate hash algorithms."""
        valid = {"md5", "sha1", "sha256", "sha384", "sha512"}
        for h in v:
            if h not in valid:
                raise ValueError(f"Invalid hash algorithm '{h}'. Must be one of: {', '.join(sorted(valid))}")
        return v

    @field_validator("dh_group")
    def validate_dh_group(cls, v: list[str]) -> list[str]:  # noqa: N805
        """Validate DH group values."""
        valid = {"group1", "group2", "group5", "group14", "group19", "group20"}
        for g in v:
            if g not in valid:
                raise ValueError(f"Invalid DH group '{g}'. Must be one of: {', '.join(sorted(valid))}")
        return v

    @field_validator("encryption")
    def validate_encryption(cls, v: list[str]) -> list[str]:  # noqa: N805
        """Validate encryption algorithms."""
        valid = {"des", "3des", "aes-128-cbc", "aes-192-cbc", "aes-256-cbc", "aes-128-gcm", "aes-256-gcm"}
        for e in v:
            if e not in valid:
                raise ValueError(f"Invalid encryption algorithm '{e}'. Must be one of: {', '.join(sorted(valid))}")
        return v

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {
            "name": self.name,
            "hash": self.hash,
            "dh_group": self.dh_group,
            "encryption": self.encryption,
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Add lifetime if specified
        if self.lifetime_seconds is not None:
            model_data["lifetime"] = {"seconds": self.lifetime_seconds}
        elif self.lifetime_minutes is not None:
            model_data["lifetime"] = {"minutes": self.lifetime_minutes}
        elif self.lifetime_hours is not None:
            model_data["lifetime"] = {"hours": self.lifetime_hours}
        elif self.lifetime_days is not None:
            model_data["lifetime"] = {"days": self.lifetime_days}

        # Add authentication_multiple if specified
        if self.authentication_multiple is not None:
            model_data["authentication_multiple"] = self.authentication_multiple

        return model_data


class IKEGateway(BaseModel):
    """Model for IKE gateway configurations."""

    folder: str | None = Field(None, description="Folder path for the IKE gateway")
    snippet: str | None = Field(None, description="Snippet path for the IKE gateway")
    device: str | None = Field(None, description="Device path for the IKE gateway")
    name: str = Field(
        ...,
        description="Name of the IKE gateway",
        pattern=r"^[0-9a-zA-Z._\-]+$",
        max_length=63,
    )

    # Authentication
    authentication: dict[str, Any] = Field(..., description="Authentication configuration (pre_shared_key or certificate)")

    # Peer address
    peer_address: dict[str, Any] = Field(..., description="Peer address configuration (ip, fqdn, or dynamic)")

    # Protocol
    protocol: dict[str, Any] = Field(..., description="IKE protocol configuration (ikev1, ikev2, version)")

    # Optional fields
    peer_id: dict[str, Any] | None = Field(None, description="Peer identification (type and id)")
    local_id: dict[str, Any] | None = Field(None, description="Local identification (type and id)")
    protocol_common: dict[str, Any] | None = Field(None, description="Common protocol settings (nat_traversal, passive_mode, fragmentation)")

    @model_validator(mode="after")
    def validate_container(self) -> "IKEGateway":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @model_validator(mode="after")
    def validate_authentication(self) -> "IKEGateway":
        """Validate authentication configuration."""
        auth = self.authentication
        if "pre_shared_key" not in auth and "certificate" not in auth:
            raise ValueError("Authentication must include 'pre_shared_key' or 'certificate'")
        if "pre_shared_key" in auth and "certificate" in auth:
            raise ValueError("Only one of 'pre_shared_key' or 'certificate' can be specified")
        if "pre_shared_key" in auth:
            psk = auth["pre_shared_key"]
            if not isinstance(psk, dict) or "key" not in psk:
                raise ValueError("pre_shared_key must be a dict with 'key' field")
        return self

    @model_validator(mode="after")
    def validate_peer_address(self) -> "IKEGateway":
        """Validate peer address configuration."""
        addr = self.peer_address
        addr_types = [k for k in ["ip", "fqdn", "dynamic"] if k in addr]
        if len(addr_types) != 1:
            raise ValueError("Exactly one of 'ip', 'fqdn', or 'dynamic' must be specified in peer_address")
        return self

    @model_validator(mode="after")
    def validate_protocol(self) -> "IKEGateway":
        """Validate protocol configuration."""
        proto = self.protocol
        version = proto.get("version", "ikev2-preferred")
        valid_versions = ["ikev1", "ikev2", "ikev2-preferred"]
        if version not in valid_versions:
            raise ValueError(f"Invalid protocol version '{version}'. Must be one of: {', '.join(valid_versions)}")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {
            "name": self.name,
            "authentication": self.authentication,
            "peer_address": self.peer_address,
            "protocol": self.protocol,
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Add optional fields
        if self.peer_id:
            model_data["peer_id"] = self.peer_id
        if self.local_id:
            model_data["local_id"] = self.local_id
        if self.protocol_common:
            model_data["protocol_common"] = self.protocol_common

        return model_data


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

        model_data = {
            "name": self.name,
            "mode": mode,
            "interfaces": interfaces,
            "description": self.description or "",
            "tags": self.tags or [],
        }

        # Add user/device identification settings if specified
        if self.enable_user_identification is not None:
            model_data["enable_user_identification"] = self.enable_user_identification
        if self.enable_device_identification is not None:
            model_data["enable_device_identification"] = self.enable_device_identification

        return model_data


class IPSecCryptoProfile(BaseModel):
    """Model for IPsec crypto profile configurations."""

    folder: str | None = Field(None, description="Folder path for the IPsec crypto profile")
    snippet: str | None = Field(None, description="Snippet path for the IPsec crypto profile")
    device: str | None = Field(None, description="Device path for the IPsec crypto profile")
    name: str = Field(..., description="Name of the IPsec crypto profile")
    esp_encryption: list[str] = Field(default_factory=lambda: ["aes-256-cbc"], description="ESP encryption algorithms")
    esp_authentication: list[str] = Field(default_factory=lambda: ["sha256"], description="ESP authentication algorithms")
    dh_group: str = Field("group14", description="DH group for PFS")
    lifetime_seconds: int | None = Field(None, description="Lifetime in seconds (180-65535)")
    lifetime_minutes: int | None = Field(None, description="Lifetime in minutes (3-65535)")
    lifetime_hours: int | None = Field(None, description="Lifetime in hours (1-65535)")
    lifetime_days: int | None = Field(None, description="Lifetime in days (1-365)")
    lifesize_kb: int | None = Field(None, description="Lifesize in KB (1-65535)")
    lifesize_mb: int | None = Field(None, description="Lifesize in MB (1-65535)")
    lifesize_gb: int | None = Field(None, description="Lifesize in GB (1-65535)")
    lifesize_tb: int | None = Field(None, description="Lifesize in TB (1-65535)")

    @model_validator(mode="after")
    def validate_container(self) -> "IPSecCryptoProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @field_validator("esp_encryption")
    def validate_esp_encryption(cls, v: list[str]) -> list[str]:  # noqa: N805
        """Validate ESP encryption algorithms."""
        valid = ["des", "3des", "aes-128-cbc", "aes-192-cbc", "aes-256-cbc", "aes-128-gcm", "aes-256-gcm", "null"]
        for alg in v:
            if alg not in valid:
                raise ValueError(f"Invalid ESP encryption algorithm '{alg}'. Valid: {', '.join(valid)}")
        return v

    @field_validator("esp_authentication")
    def validate_esp_authentication(cls, v: list[str]) -> list[str]:  # noqa: N805
        """Validate ESP authentication algorithms."""
        valid = ["md5", "sha1", "sha256", "sha384", "sha512"]
        for alg in v:
            if alg not in valid:
                raise ValueError(f"Invalid ESP authentication algorithm '{alg}'. Valid: {', '.join(valid)}")
        return v

    @field_validator("dh_group")
    def validate_dh_group(cls, v: str) -> str:  # noqa: N805
        """Validate DH group."""
        valid = ["no-pfs", "group1", "group2", "group5", "group14", "group19", "group20"]
        if v not in valid:
            raise ValueError(f"Invalid DH group '{v}'. Valid: {', '.join(valid)}")
        return v

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {
            "name": self.name,
            "dh_group": self.dh_group,
            "esp": {
                "encryption": self.esp_encryption,
                "authentication": self.esp_authentication,
            },
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Build lifetime - default to 1 hour if none specified
        if self.lifetime_seconds:
            model_data["lifetime"] = {"seconds": self.lifetime_seconds}
        elif self.lifetime_minutes:
            model_data["lifetime"] = {"minutes": self.lifetime_minutes}
        elif self.lifetime_hours:
            model_data["lifetime"] = {"hours": self.lifetime_hours}
        elif self.lifetime_days:
            model_data["lifetime"] = {"days": self.lifetime_days}
        else:
            model_data["lifetime"] = {"hours": 1}

        # Build lifesize if specified
        if self.lifesize_kb:
            model_data["lifesize"] = {"kb": self.lifesize_kb}
        elif self.lifesize_mb:
            model_data["lifesize"] = {"mb": self.lifesize_mb}
        elif self.lifesize_gb:
            model_data["lifesize"] = {"gb": self.lifesize_gb}
        elif self.lifesize_tb:
            model_data["lifesize"] = {"tb": self.lifesize_tb}

        return model_data


class BgpAddressFamilyProfile(BaseModel):
    """Model for BGP address family profile configurations."""

    folder: str | None = Field(None, description="Folder path")
    snippet: str | None = Field(None, description="Snippet path")
    device: str | None = Field(None, description="Device path")
    name: str = Field(..., description="Profile name")
    ipv4: dict[str, Any] | None = Field(None, description="IPv4 address family configuration (unicast/multicast)")

    @model_validator(mode="after")
    def validate_container(self) -> "BgpAddressFamilyProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device
        if self.ipv4 is not None:
            model_data["ipv4"] = self.ipv4
        return model_data


class BgpAuthProfile(BaseModel):
    """Model for BGP authentication profile configurations."""

    folder: str | None = Field(None, description="Folder path")
    snippet: str | None = Field(None, description="Snippet path")
    device: str | None = Field(None, description="Device path")
    name: str = Field(..., description="Profile name")
    secret: str | None = Field(None, description="BGP authentication key")

    @model_validator(mode="after")
    def validate_container(self) -> "BgpAuthProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device
        if self.secret is not None:
            model_data["secret"] = self.secret
        return model_data


class OspfAuthProfile(BaseModel):
    """Model for OSPF authentication profile configurations."""

    folder: str | None = Field(None, description="Folder path")
    snippet: str | None = Field(None, description="Snippet path")
    device: str | None = Field(None, description="Device path")
    name: str = Field(..., description="Profile name")
    password: str | None = Field(None, description="Simple password authentication")
    md5: list[dict[str, Any]] | None = Field(None, description="MD5 authentication keys")

    @model_validator(mode="after")
    def validate_container(self) -> "OspfAuthProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @model_validator(mode="after")
    def validate_auth_type(self) -> "OspfAuthProfile":
        """Validate that password and md5 are mutually exclusive."""
        if self.password is not None and self.md5 is not None:
            raise ValueError("'password' and 'md5' are mutually exclusive")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device
        if self.password is not None:
            model_data["password"] = self.password
        if self.md5 is not None:
            model_data["md5"] = self.md5
        return model_data


class RouteAccessList(BaseModel):
    """Model for route access list configurations."""

    folder: str | None = Field(None, description="Folder path")
    snippet: str | None = Field(None, description="Snippet path")
    device: str | None = Field(None, description="Device path")
    name: str = Field(..., description="Route access list name")
    description: str | None = Field(None, description="Description")
    type: dict[str, Any] | None = Field(None, description="Access list type configuration (ipv4)")

    @model_validator(mode="after")
    def validate_container(self) -> "RouteAccessList":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device
        if self.description is not None:
            model_data["description"] = self.description
        if self.type is not None:
            model_data["type"] = self.type
        return model_data


class RoutePrefixList(BaseModel):
    """Model for route prefix list configurations."""

    folder: str | None = Field(None, description="Folder path")
    snippet: str | None = Field(None, description="Snippet path")
    device: str | None = Field(None, description="Device path")
    name: str = Field(..., description="Filter prefix list name")
    description: str | None = Field(None, description="Description")
    ipv4: dict[str, Any] | None = Field(None, description="IPv4 prefix list configuration")

    @model_validator(mode="after")
    def validate_container(self) -> "RoutePrefixList":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device
        if self.description is not None:
            model_data["description"] = self.description
        if self.ipv4 is not None:
            model_data["ipv4"] = self.ipv4
        return model_data


class BgpFilteringProfile(BaseModel):
    """Model for BGP filtering profile configurations."""

    folder: str | None = Field(None, description="Folder path")
    snippet: str | None = Field(None, description="Snippet path")
    device: str | None = Field(None, description="Device path")
    name: str = Field(..., description="Profile name")
    ipv4: dict[str, Any] | None = Field(None, description="IPv4 filtering configuration (unicast/multicast)")

    @model_validator(mode="after")
    def validate_container(self) -> "BgpFilteringProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device
        if self.ipv4 is not None:
            model_data["ipv4"] = self.ipv4
        return model_data


class BgpRedistributionProfile(BaseModel):
    """Model for BGP redistribution profile configurations."""

    folder: str | None = Field(None, description="Folder path")
    snippet: str | None = Field(None, description="Snippet path")
    device: str | None = Field(None, description="Device path")
    name: str = Field(..., description="Profile name")
    ipv4: dict[str, Any] | None = Field(None, description="IPv4 redistribution configuration")

    @model_validator(mode="after")
    def validate_container(self) -> "BgpRedistributionProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device
        if self.ipv4 is not None:
            model_data["ipv4"] = self.ipv4
        return model_data


class BgpRouteMap(BaseModel):
    """Model for BGP route map configurations."""

    folder: str | None = Field(None, description="Folder path")
    snippet: str | None = Field(None, description="Snippet path")
    device: str | None = Field(None, description="Device path")
    name: str = Field(..., description="Route map name")
    route_map: list[dict[str, Any]] | None = Field(None, description="List of route map entries")

    @model_validator(mode="after")
    def validate_container(self) -> "BgpRouteMap":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device
        if self.route_map is not None:
            model_data["route_map"] = self.route_map
        return model_data


class BgpRouteMapRedistribution(BaseModel):
    """Model for BGP route map redistribution configurations."""

    folder: str | None = Field(None, description="Folder path")
    snippet: str | None = Field(None, description="Snippet path")
    device: str | None = Field(None, description="Device path")
    name: str = Field(..., description="Redistribution name")
    bgp: dict[str, Any] | None = Field(None, description="BGP as source protocol")
    ospf: dict[str, Any] | None = Field(None, description="OSPF as source protocol")
    connected_static: dict[str, Any] | None = Field(None, description="Connected/Static as source protocol")

    @model_validator(mode="after")
    def validate_container(self) -> "BgpRouteMapRedistribution":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @model_validator(mode="after")
    def validate_source_protocol(self) -> "BgpRouteMapRedistribution":
        """Validate that at most one source protocol is specified."""
        sources = [self.bgp, self.ospf, self.connected_static]
        if sum(1 for s in sources if s is not None) > 1:
            raise ValueError("At most one of 'bgp', 'ospf', or 'connected_static' can be set")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device
        if self.bgp is not None:
            model_data["bgp"] = self.bgp
        if self.ospf is not None:
            model_data["ospf"] = self.ospf
        if self.connected_static is not None:
            model_data["connected_static"] = self.connected_static
        return model_data


class DnsProxy(BaseModel):
    """Validator for DNS proxy configuration."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., description="DNS proxy name")
    folder: str | None = Field(None, description="Folder container")
    snippet: str | None = Field(None, description="Snippet container")
    device: str | None = Field(None, description="Device container")
    enabled: bool | None = Field(None, description="Enable DNS proxy")
    default: dict[str, Any] | None = Field(None, description="Default DNS server configuration")
    interface: list[str] | None = Field(None, description="Interfaces to bind to")
    domain_servers: list[dict[str, Any]] | None = Field(None, description="Domain-specific DNS servers")
    static_entries: list[dict[str, Any]] | None = Field(None, description="Static DNS entries")
    tcp_queries: dict[str, Any] | None = Field(None, description="TCP query settings")
    udp_queries: dict[str, Any] | None = Field(None, description="UDP query settings")
    cache: dict[str, Any] | None = Field(None, description="DNS cache settings")

    @model_validator(mode="after")
    def validate_container(self) -> "DnsProxy":
        """Ensure exactly one container is provided."""
        containers = [self.folder, self.snippet, self.device]
        provided = sum(1 for c in containers if c is not None)
        if provided != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be provided.")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert to SDK-compatible dict."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder is not None:
            model_data["folder"] = self.folder
        if self.snippet is not None:
            model_data["snippet"] = self.snippet
        if self.device is not None:
            model_data["device"] = self.device
        if self.enabled is not None:
            model_data["enabled"] = self.enabled
        if self.default is not None:
            model_data["default"] = self.default
        if self.interface is not None:
            model_data["interface"] = self.interface
        if self.domain_servers is not None:
            model_data["domain_servers"] = self.domain_servers
        if self.static_entries is not None:
            model_data["static_entries"] = self.static_entries
        if self.tcp_queries is not None:
            model_data["tcp_queries"] = self.tcp_queries
        if self.udp_queries is not None:
            model_data["udp_queries"] = self.udp_queries
        if self.cache is not None:
            model_data["cache"] = self.cache
        return model_data


class PbfRule(BaseModel):
    """Validator for PBF rule configuration."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., description="PBF rule name")
    folder: str | None = Field(None, description="Folder container")
    snippet: str | None = Field(None, description="Snippet container")
    device: str | None = Field(None, description="Device container")
    description: str | None = Field(None, description="Description")
    tag: list[str] | None = Field(None, description="Tags")
    schedule: str | None = Field(None, description="Schedule")
    disabled: bool | None = Field(None, description="Disabled state")
    from_: dict[str, Any] | None = Field(None, alias="from", description="Source zone or interface")
    source: list[str] | None = Field(None, description="Source addresses")
    source_user: list[str] | None = Field(None, description="Source users")
    destination: list[str] | None = Field(None, description="Destination addresses")
    destination_application: dict[str, Any] | None = Field(None, description="Destination application")
    service: list[str] | None = Field(None, description="Services")
    application: list[str] | None = Field(None, description="Applications")
    action: dict[str, Any] | None = Field(None, description="Action (forward, discard, no_pbf)")
    enforce_symmetric_return: dict[str, Any] | None = Field(None, description="Symmetric return config")

    @model_validator(mode="after")
    def validate_container(self) -> "PbfRule":
        """Ensure exactly one container is provided."""
        containers = [self.folder, self.snippet, self.device]
        provided = sum(1 for c in containers if c is not None)
        if provided != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be provided.")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert to SDK-compatible dict."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder is not None:
            model_data["folder"] = self.folder
        if self.snippet is not None:
            model_data["snippet"] = self.snippet
        if self.device is not None:
            model_data["device"] = self.device
        if self.description is not None:
            model_data["description"] = self.description
        if self.tag is not None:
            model_data["tag"] = self.tag
        if self.schedule is not None:
            model_data["schedule"] = self.schedule
        if self.disabled is not None:
            model_data["disabled"] = self.disabled
        if self.from_ is not None:
            model_data["from"] = self.from_
        if self.source is not None:
            model_data["source"] = self.source
        if self.source_user is not None:
            model_data["source_user"] = self.source_user
        if self.destination is not None:
            model_data["destination"] = self.destination
        if self.destination_application is not None:
            model_data["destination_application"] = self.destination_application
        if self.service is not None:
            model_data["service"] = self.service
        if self.application is not None:
            model_data["application"] = self.application
        if self.action is not None:
            model_data["action"] = self.action
        if self.enforce_symmetric_return is not None:
            model_data["enforce_symmetric_return"] = self.enforce_symmetric_return
        return model_data


class QosProfile(BaseModel):
    """Validator for QoS profile configuration."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., max_length=31, description="QoS profile name")
    folder: str | None = Field(None, description="Folder container")
    snippet: str | None = Field(None, description="Snippet container")
    device: str | None = Field(None, description="Device container")
    aggregate_bandwidth: dict[str, Any] | None = Field(None, description="Aggregate bandwidth settings")
    class_bandwidth_type: dict[str, Any] | None = Field(None, description="Class bandwidth type config")

    ALLOWED_FOLDERS: ClassVar[list[str]] = ["Remote Networks", "Service Connections"]

    @model_validator(mode="after")
    def validate_container(self) -> "QosProfile":
        """Ensure exactly one container is provided and folder is allowed."""
        containers = [self.folder, self.snippet, self.device]
        provided = sum(1 for c in containers if c is not None)
        if provided != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be provided.")
        if self.folder is not None and self.folder not in self.ALLOWED_FOLDERS:
            raise ValueError(f"QoS profiles only support folders: {', '.join(self.ALLOWED_FOLDERS)}. Got: '{self.folder}'")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert to SDK-compatible dict."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder is not None:
            model_data["folder"] = self.folder
        if self.snippet is not None:
            model_data["snippet"] = self.snippet
        if self.device is not None:
            model_data["device"] = self.device
        if self.aggregate_bandwidth is not None:
            model_data["aggregate_bandwidth"] = self.aggregate_bandwidth
        if self.class_bandwidth_type is not None:
            model_data["class_bandwidth_type"] = self.class_bandwidth_type
        return model_data


class QosRule(BaseModel):
    """Validator for QoS rule configuration."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., description="QoS rule name")
    folder: str | None = Field(None, description="Folder container")
    snippet: str | None = Field(None, description="Snippet container")
    device: str | None = Field(None, description="Device container")
    description: str | None = Field(None, description="Description")
    action: dict[str, Any] | None = Field(None, description="QoS action config")
    schedule: str | None = Field(None, description="Schedule")
    dscp_tos: dict[str, Any] | None = Field(None, description="DSCP/TOS settings")

    @model_validator(mode="after")
    def validate_container(self) -> "QosRule":
        """Ensure exactly one container is provided."""
        containers = [self.folder, self.snippet, self.device]
        provided = sum(1 for c in containers if c is not None)
        if provided != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be provided.")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert to SDK-compatible dict."""
        model_data: dict[str, Any] = {"name": self.name}
        if self.folder is not None:
            model_data["folder"] = self.folder
        if self.snippet is not None:
            model_data["snippet"] = self.snippet
        if self.device is not None:
            model_data["device"] = self.device
        if self.description is not None:
            model_data["description"] = self.description
        if self.action is not None:
            model_data["action"] = self.action
        if self.schedule is not None:
            model_data["schedule"] = self.schedule
        if self.dscp_tos is not None:
            model_data["dscp_tos"] = self.dscp_tos
        return model_data


# =============================================================================================================================================================================================
# SECURITY CONFIGURATION MODELS
# =============================================================================================================================================================================================


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
    log_start: bool | None = Field(None, description="Log at session start")
    log_end: bool | None = Field(None, description="Log at session end")
    log_setting: str | None = Field(None, description="Log forwarding profile")

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


class AntiSpywareProfile(BaseModel):
    """Model for anti-spyware profile configurations."""

    folder: str | None = Field(None, description="Folder path for the anti-spyware profile")
    snippet: str | None = Field(None, description="Snippet path for the anti-spyware profile")
    device: str | None = Field(None, description="Device path for the anti-spyware profile")
    name: str = Field(..., description="Name of the anti-spyware profile")
    description: str | None = Field(None, description="Description of the anti-spyware profile")

    # Threat exceptions
    threat_exceptions: list[dict[str, Any]] | None = Field(None, description="List of threat exceptions")

    # Rules configuration
    rules: list[dict[str, Any]] | None = Field(None, description="List of anti-spyware rules")

    # MICA engine settings
    mica_engine_spyware_enabled: list[dict[str, Any]] | None = Field(None, description="MICA engine spyware detection settings")

    # Cloud inline analysis
    cloud_inline_analysis: bool | None = Field(None, description="Enable cloud inline analysis")

    @model_validator(mode="after")
    def validate_container(self) -> "AntiSpywareProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @field_validator("rules")
    def validate_rules(cls, v: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:  # noqa: N805
        """Validate rules configuration."""
        if v is None:
            return v

        for idx, rule in enumerate(v):
            # Required fields
            if "name" not in rule:
                raise ValueError(f"Rule {idx}: 'name' is required")
            if "severity" not in rule:
                raise ValueError(f"Rule {idx}: 'severity' is required")
            # Note: action might not be returned by SDK in some cases
            # if "action" not in rule:
            #     raise ValueError(f"Rule {idx}: 'action' is required")

            # Validate severity
            valid_severities = [
                "critical",
                "high",
                "medium",
                "low",
                "informational",
                "any",
            ]
            if isinstance(rule["severity"], list):
                for sev in rule["severity"]:
                    if sev not in valid_severities:
                        raise ValueError(f"Rule {idx}: Invalid severity '{sev}'")
            elif rule["severity"] not in valid_severities:
                raise ValueError(f"Rule {idx}: Invalid severity '{rule['severity']}'")

            # Validate action if present
            if "action" in rule:
                valid_actions = [
                    "alert",
                    "allow",
                    "block",
                    "drop",
                    "reset-both",
                    "reset-client",
                    "reset-server",
                ]
                action = rule["action"]
                if isinstance(action, dict):
                    # Dict format actions are accepted (e.g., from API responses)
                    pass
                elif action not in valid_actions:
                    raise ValueError(f"Rule {idx}: Invalid action '{action}'")

        return v

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Add optional fields
        if self.description:
            model_data["description"] = self.description
        if self.threat_exceptions:
            model_data["threat_exception"] = self.threat_exceptions
        if self.rules:
            model_data["rules"] = self.rules
        if self.mica_engine_spyware_enabled:
            model_data["mica_engine_spyware_enabled"] = self.mica_engine_spyware_enabled
        if self.cloud_inline_analysis is not None:
            model_data["cloud_inline_analysis"] = self.cloud_inline_analysis

        return model_data


class DecryptionProfile(BaseModel):
    """Model for decryption profile configurations."""

    folder: str | None = Field(None, description="Folder path for the decryption profile")
    snippet: str | None = Field(None, description="Snippet path for the decryption profile")
    device: str | None = Field(None, description="Device path for the decryption profile")
    name: str = Field(..., description="Name of the decryption profile")
    description: str | None = Field(None, description="Description of the decryption profile")

    # SSL Forward Proxy settings
    ssl_forward_proxy: dict[str, Any] | None = Field(None, description="SSL Forward Proxy settings")

    # SSL Inbound Proxy settings
    ssl_inbound_proxy: dict[str, Any] | None = Field(None, description="SSL Inbound Proxy settings")

    # SSL No Proxy settings
    ssl_no_proxy: dict[str, Any] | None = Field(None, description="SSL No Proxy settings")

    # SSL Protocol Settings
    ssl_protocol_settings: dict[str, Any] | None = Field(None, description="SSL Protocol settings")

    @model_validator(mode="after")
    def validate_container(self) -> "DecryptionProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @model_validator(mode="after")
    def validate_proxy_settings(self) -> "DecryptionProfile":
        """Validate that at least one proxy type is configured."""
        proxy_types = [
            self.ssl_forward_proxy,
            self.ssl_inbound_proxy,
            self.ssl_no_proxy,
        ]
        if not any(proxy_types):
            raise ValueError("At least one proxy type (ssl_forward_proxy, ssl_inbound_proxy, or ssl_no_proxy) must be configured")
        return self

    @field_validator("ssl_protocol_settings")
    def validate_ssl_protocol_settings(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:  # noqa: N805
        """Validate SSL protocol settings."""
        if v is None:
            return v

        # Validate SSL versions if present
        if "min_version" in v and "max_version" in v:
            ssl_versions = ["sslv3", "tls1-0", "tls1-1", "tls1-2", "tls1-3", "max"]
            min_idx = ssl_versions.index(v["min_version"]) if v["min_version"] in ssl_versions else -1
            max_idx = ssl_versions.index(v["max_version"]) if v["max_version"] in ssl_versions else -1

            if min_idx == -1 or max_idx == -1:
                raise ValueError("Invalid SSL version specified")
            if min_idx > max_idx:
                raise ValueError("min_version cannot be greater than max_version")

        return v

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Add optional fields
        if self.description:
            model_data["description"] = self.description

        # Add proxy settings if present
        if self.ssl_forward_proxy:
            model_data["ssl_forward_proxy"] = self.ssl_forward_proxy
        if self.ssl_inbound_proxy:
            model_data["ssl_inbound_proxy"] = self.ssl_inbound_proxy
        if self.ssl_no_proxy:
            model_data["ssl_no_proxy"] = self.ssl_no_proxy
        if self.ssl_protocol_settings:
            model_data["ssl_protocol_settings"] = self.ssl_protocol_settings

        return model_data


class WildfireAntivirusProfile(BaseModel):
    """Model for WildFire antivirus profile configurations."""

    folder: str | None = Field(None, description="Folder path for the WildFire antivirus profile")
    snippet: str | None = Field(None, description="Snippet path for the WildFire antivirus profile")
    device: str | None = Field(None, description="Device path for the WildFire antivirus profile")
    name: str = Field(..., description="Name of the WildFire antivirus profile")
    description: str | None = Field(None, description="Description of the WildFire antivirus profile")

    # Packet capture
    packet_capture: bool | None = Field(None, description="Enable packet capture")

    # Rules configuration
    rules: list[dict[str, Any]] | None = Field(None, description="List of WildFire antivirus rules")

    # MLAV exceptions
    mlav_exception: list[dict[str, Any]] | None = Field(None, description="List of MLAV exceptions")

    # Threat exceptions
    threat_exception: list[dict[str, Any]] | None = Field(None, description="List of threat exceptions")

    @model_validator(mode="after")
    def validate_container(self) -> "WildfireAntivirusProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @field_validator("rules")
    def validate_rules(cls, v: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:  # noqa: N805
        """Validate rules configuration."""
        if v is None:
            return v

        valid_directions = ["download", "upload", "both"]
        valid_analyses = ["public-cloud", "private-cloud"]

        for idx, rule in enumerate(v):
            if "name" not in rule:
                raise ValueError(f"Rule {idx}: 'name' is required")
            if "direction" not in rule:
                raise ValueError(f"Rule {idx}: 'direction' is required")
            if rule["direction"] not in valid_directions:
                raise ValueError(f"Rule {idx}: Invalid direction '{rule['direction']}'")
            if "analysis" in rule and rule["analysis"] is not None and rule["analysis"] not in valid_analyses:
                raise ValueError(f"Rule {idx}: Invalid analysis '{rule['analysis']}'")

        return v

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Add optional fields
        if self.description:
            model_data["description"] = self.description
        if self.packet_capture is not None:
            model_data["packet_capture"] = self.packet_capture
        if self.rules:
            model_data["rules"] = self.rules
        if self.mlav_exception:
            model_data["mlav_exception"] = self.mlav_exception
        if self.threat_exception:
            model_data["threat_exception"] = self.threat_exception

        return model_data


class DNSSecurityProfile(BaseModel):
    """Model for DNS security profile configurations."""

    folder: str | None = Field(None, description="Folder path for the DNS security profile")
    snippet: str | None = Field(None, description="Snippet path for the DNS security profile")
    device: str | None = Field(None, description="Device path for the DNS security profile")
    name: str = Field(..., description="Name of the DNS security profile")
    description: str | None = Field(None, description="Description of the DNS security profile")

    # Botnet domains configuration (passed as JSON)
    botnet_domains: dict[str, Any] | None = Field(None, description="Botnet domains settings as dict")

    @model_validator(mode="after")
    def validate_container(self) -> "DNSSecurityProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Add optional fields
        if self.description:
            model_data["description"] = self.description
        if self.botnet_domains:
            model_data["botnet_domains"] = self.botnet_domains

        return model_data


class URLCategory(BaseModel):
    """Model for URL category configurations."""

    model_config = {"populate_by_name": True}

    folder: str | None = Field(None, description="Folder path for the URL category")
    snippet: str | None = Field(None, description="Snippet path for the URL category")
    device: str | None = Field(None, description="Device path for the URL category")
    name: str = Field(..., description="Name of the URL category")
    description: str | None = Field(None, description="Description of the URL category")

    # URL category type
    type: str | None = Field("URL List", description="Type of the URL category (URL List or Category Match)")

    # List of URLs or categories - use alias to match SDK field name "list"
    url_list: list[str] = Field(default_factory=list, alias="list", description="List of URLs or category matches")

    @model_validator(mode="after")
    def validate_container(self) -> "URLCategory":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @field_validator("type")
    def validate_type(cls, v: str | None) -> str | None:  # noqa: N805
        """Validate URL category type."""
        if v is None:
            return v
        valid_types = ["URL List", "Category Match"]
        if v not in valid_types:
            raise ValueError(f"Invalid type '{v}'. Must be one of: {', '.join(valid_types)}")
        return v

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Add optional fields
        if self.description:
            model_data["description"] = self.description
        if self.type:
            model_data["type"] = self.type
        if self.url_list:
            model_data["list"] = self.url_list

        return model_data


class AppOverrideRule(BaseModel):
    """Model for app override rule configurations."""

    folder: str | None = Field(None, description="Folder path for the app override rule")
    snippet: str | None = Field(None, description="Snippet path for the app override rule")
    device: str | None = Field(None, description="Device path for the app override rule")
    name: str = Field(..., description="Name of the app override rule")
    description: str | None = Field(None, description="Description of the app override rule")
    application: str = Field(..., description="Application to override")
    port: str = Field(..., description="Port(s) for the rule")
    protocol: str = Field(..., description="Protocol (tcp or udp)")
    rulebase: str = Field("pre", description="Rulebase (pre or post)")

    # Zone and address fields
    from_zones: list[str] = Field(default_factory=lambda: ["any"], description="Source security zones")
    to_zones: list[str] = Field(default_factory=lambda: ["any"], description="Destination security zones")
    source: list[str] = Field(default_factory=lambda: ["any"], description="Source addresses")
    destination: list[str] = Field(default_factory=lambda: ["any"], description="Destination addresses")

    # Optional fields
    disabled: bool = Field(False, description="Whether the rule is disabled")
    negate_source: bool = Field(False, description="Negate source addresses")
    negate_destination: bool = Field(False, description="Negate destination addresses")
    tag: list[str] | None = Field(None, description="Tags for the rule")
    group_tag: str | None = Field(None, description="Group tag for the rule")

    @model_validator(mode="after")
    def validate_container(self) -> "AppOverrideRule":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @field_validator("protocol")
    @classmethod
    def validate_protocol(cls, v: str) -> str:
        """Validate protocol value."""
        if v.lower() not in ("tcp", "udp"):
            raise ValueError("Protocol must be 'tcp' or 'udp'")
        return v.lower()

    @field_validator("rulebase")
    @classmethod
    def validate_rulebase(cls, v: str) -> str:
        """Validate rulebase value."""
        if v.lower() not in ("pre", "post"):
            raise ValueError("Rulebase must be 'pre' or 'post'")
        return v.lower()

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {
            "name": self.name,
            "application": self.application,
            "port": self.port,
            "protocol": self.protocol,
            "rulebase": self.rulebase,
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Add zone/address fields
        model_data["from"] = self.from_zones
        model_data["to"] = self.to_zones
        model_data["source"] = self.source
        model_data["destination"] = self.destination

        # Add optional fields
        if self.description:
            model_data["description"] = self.description
        if self.disabled:
            model_data["disabled"] = self.disabled
        if self.negate_source:
            model_data["negate_source"] = self.negate_source
        if self.negate_destination:
            model_data["negate_destination"] = self.negate_destination
        if self.tag:
            model_data["tag"] = self.tag
        if self.group_tag:
            model_data["group_tag"] = self.group_tag

        return model_data


class AuthenticationRule(BaseModel):
    """Model for authentication rule configurations."""

    folder: str | None = Field(None, description="Folder path for the authentication rule")
    snippet: str | None = Field(None, description="Snippet path for the authentication rule")
    device: str | None = Field(None, description="Device path for the authentication rule")
    name: str = Field(..., description="Name of the authentication rule")
    description: str | None = Field(None, description="Description of the authentication rule")
    rulebase: str = Field("pre", description="Rulebase (pre or post)")

    # Zone and address fields
    from_zones: list[str] = Field(default_factory=lambda: ["any"], description="Source security zones")
    to_zones: list[str] = Field(default_factory=lambda: ["any"], description="Destination security zones")
    source: list[str] = Field(default_factory=lambda: ["any"], description="Source addresses")
    destination: list[str] = Field(default_factory=lambda: ["any"], description="Destination addresses")
    source_user: list[str] = Field(default_factory=lambda: ["any"], description="Source users")
    source_hip: list[str] = Field(default_factory=lambda: ["any"], description="Source HIP profiles")
    destination_hip: list[str] = Field(default_factory=lambda: ["any"], description="Destination HIP profiles")
    service: list[str] = Field(default_factory=lambda: ["any"], description="Services")
    category: list[str] = Field(default_factory=lambda: ["any"], description="URL categories")

    # Optional fields
    disabled: bool = Field(False, description="Whether the rule is disabled")
    negate_source: bool = Field(False, description="Negate source addresses")
    negate_destination: bool = Field(False, description="Negate destination addresses")
    tag: list[str] | None = Field(None, description="Tags for the rule")
    group_tag: str | None = Field(None, description="Group tag for the rule")
    authentication_enforcement: str | None = Field(None, description="Authentication profile name")
    timeout: int | None = Field(None, description="Auth session timeout in minutes")
    log_setting: str | None = Field(None, description="Log forwarding profile")
    log_authentication_timeout: bool = Field(False, description="Log authentication timeouts")
    hip_profiles: list[str] | None = Field(None, description="HIP profiles")

    @model_validator(mode="after")
    def validate_container(self) -> "AuthenticationRule":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @field_validator("rulebase")
    @classmethod
    def validate_rulebase(cls, v: str) -> str:
        """Validate rulebase value."""
        if v.lower() not in ("pre", "post"):
            raise ValueError("Rulebase must be 'pre' or 'post'")
        return v.lower()

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {
            "name": self.name,
            "rulebase": self.rulebase,
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Add zone/address fields
        model_data["from"] = self.from_zones
        model_data["to"] = self.to_zones
        model_data["source"] = self.source
        model_data["destination"] = self.destination
        model_data["source_user"] = self.source_user
        model_data["source_hip"] = self.source_hip
        model_data["destination_hip"] = self.destination_hip
        model_data["service"] = self.service
        model_data["category"] = self.category

        # Add optional fields
        if self.description:
            model_data["description"] = self.description
        if self.disabled:
            model_data["disabled"] = self.disabled
        if self.negate_source:
            model_data["negate_source"] = self.negate_source
        if self.negate_destination:
            model_data["negate_destination"] = self.negate_destination
        if self.tag:
            model_data["tag"] = self.tag
        if self.group_tag:
            model_data["group_tag"] = self.group_tag
        if self.authentication_enforcement:
            model_data["authentication_enforcement"] = self.authentication_enforcement
        if self.timeout is not None:
            model_data["timeout"] = self.timeout
        if self.log_setting:
            model_data["log_setting"] = self.log_setting
        if self.log_authentication_timeout:
            model_data["log_authentication_timeout"] = self.log_authentication_timeout
        if self.hip_profiles:
            model_data["hip_profiles"] = self.hip_profiles

        return model_data


class DecryptionRule(BaseModel):
    """Model for decryption rule configurations."""

    folder: str | None = Field(None, description="Folder path for the decryption rule")
    snippet: str | None = Field(None, description="Snippet path for the decryption rule")
    device: str | None = Field(None, description="Device path for the decryption rule")
    name: str = Field(..., description="Name of the decryption rule")
    description: str | None = Field(None, description="Description of the decryption rule")
    action: str = Field(..., description="Action (decrypt or no-decrypt)")
    rulebase: str = Field("pre", description="Rulebase (pre or post)")

    # Zone and address fields
    from_zones: list[str] = Field(default_factory=lambda: ["any"], description="Source security zones")
    to_zones: list[str] = Field(default_factory=lambda: ["any"], description="Destination security zones")
    source: list[str] = Field(default_factory=lambda: ["any"], description="Source addresses")
    destination: list[str] = Field(default_factory=lambda: ["any"], description="Destination addresses")
    source_user: list[str] = Field(default_factory=lambda: ["any"], description="Source users")
    source_hip: list[str] = Field(default_factory=lambda: ["any"], description="Source HIP profiles")
    destination_hip: list[str] = Field(default_factory=lambda: ["any"], description="Destination HIP profiles")
    service: list[str] = Field(default_factory=lambda: ["any"], description="Services")
    category: list[str] = Field(default_factory=lambda: ["any"], description="URL categories")

    # Optional fields
    disabled: bool = Field(False, description="Whether the rule is disabled")
    negate_source: bool = Field(False, description="Negate source addresses")
    negate_destination: bool = Field(False, description="Negate destination addresses")
    tag: list[str] | None = Field(None, description="Tags for the rule")
    profile: str | None = Field(None, description="Decryption profile")
    type: dict[str, Any] | None = Field(None, description="Decryption type (ssl_forward_proxy or ssl_inbound_inspection)")
    log_setting: str | None = Field(None, description="Log forwarding profile")
    log_fail: bool | None = Field(None, description="Log failed decryption events")
    log_success: bool | None = Field(None, description="Log successful decryption events")

    @model_validator(mode="after")
    def validate_container(self) -> "DecryptionRule":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        """Validate action value."""
        if v.lower() not in ("decrypt", "no-decrypt"):
            raise ValueError("Action must be 'decrypt' or 'no-decrypt'")
        return v.lower()

    @field_validator("rulebase")
    @classmethod
    def validate_rulebase(cls, v: str) -> str:
        """Validate rulebase value."""
        if v.lower() not in ("pre", "post"):
            raise ValueError("Rulebase must be 'pre' or 'post'")
        return v.lower()

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {
            "name": self.name,
            "action": self.action,
            "rulebase": self.rulebase,
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Add zone/address fields
        model_data["from"] = self.from_zones
        model_data["to"] = self.to_zones
        model_data["source"] = self.source
        model_data["destination"] = self.destination
        model_data["source_user"] = self.source_user
        model_data["source_hip"] = self.source_hip
        model_data["destination_hip"] = self.destination_hip
        model_data["service"] = self.service
        model_data["category"] = self.category

        # Add optional fields
        if self.description:
            model_data["description"] = self.description
        if self.disabled:
            model_data["disabled"] = self.disabled
        if self.negate_source:
            model_data["negate_source"] = self.negate_source
        if self.negate_destination:
            model_data["negate_destination"] = self.negate_destination
        if self.tag:
            model_data["tag"] = self.tag
        if self.profile:
            model_data["profile"] = self.profile
        if self.type:
            model_data["type"] = self.type
        if self.log_setting:
            model_data["log_setting"] = self.log_setting
        if self.log_fail is not None:
            model_data["log_fail"] = self.log_fail
        if self.log_success is not None:
            model_data["log_success"] = self.log_success

        return model_data


class URLAccessProfile(BaseModel):
    """Model for URL access profile configurations."""

    folder: str | None = Field(None, description="Folder path for the URL access profile")
    snippet: str | None = Field(None, description="Snippet path for the URL access profile")
    device: str | None = Field(None, description="Device path for the URL access profile")
    name: str = Field(..., description="Name of the URL access profile")
    description: str | None = Field(None, description="Description of the URL access profile")

    # URL category action lists
    alert: list[str] | None = Field(None, description="URL categories for alert action")
    allow: list[str] | None = Field(None, description="URL categories for allow action")
    block: list[str] | None = Field(None, description="URL categories for block action")
    continue_categories: list[str] | None = Field(None, description="URL categories for continue action")
    redirect: list[str] | None = Field(None, description="URL categories for redirect action")

    # Inline categorization
    cloud_inline_cat: bool | None = Field(None, description="Enable cloud inline categorization")
    local_inline_cat: bool | None = Field(None, description="Enable local inline categorization")

    # Credential enforcement (as JSON dict)
    credential_enforcement: dict[str, Any] | None = Field(None, description="Credential enforcement settings")

    # Logging options
    log_container_page_only: bool | None = Field(None, description="Log container page only")
    log_http_hdr_referer: bool | None = Field(None, description="Log HTTP header referer")
    log_http_hdr_user_agent: bool | None = Field(None, description="Log HTTP header user agent")
    log_http_hdr_xff: bool | None = Field(None, description="Log HTTP header X-Forwarded-For")

    # Other options
    safe_search_enforcement: bool | None = Field(None, description="Enable safe search enforcement")
    mlav_category_exception: list[str] | None = Field(None, description="MLAV category exceptions")

    @model_validator(mode="after")
    def validate_container(self) -> "URLAccessProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data: dict[str, Any] = {
            "name": self.name,
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Add optional fields
        if self.description:
            model_data["description"] = self.description
        if self.alert:
            model_data["alert"] = self.alert
        if self.allow:
            model_data["allow"] = self.allow
        if self.block:
            model_data["block"] = self.block
        if self.continue_categories:
            model_data["continue"] = self.continue_categories
        if self.redirect:
            model_data["redirect"] = self.redirect
        if self.cloud_inline_cat is not None:
            model_data["cloud_inline_cat"] = self.cloud_inline_cat
        if self.local_inline_cat is not None:
            model_data["local_inline_cat"] = self.local_inline_cat
        if self.credential_enforcement:
            model_data["credential_enforcement"] = self.credential_enforcement
        if self.log_container_page_only is not None:
            model_data["log_container_page_only"] = self.log_container_page_only
        if self.log_http_hdr_referer is not None:
            model_data["log_http_hdr_referer"] = self.log_http_hdr_referer
        if self.log_http_hdr_user_agent is not None:
            model_data["log_http_hdr_user_agent"] = self.log_http_hdr_user_agent
        if self.log_http_hdr_xff is not None:
            model_data["log_http_hdr_xff"] = self.log_http_hdr_xff
        if self.safe_search_enforcement is not None:
            model_data["safe_search_enforcement"] = self.safe_search_enforcement
        if self.mlav_category_exception:
            model_data["mlav_category_exception"] = self.mlav_category_exception

        return model_data


# =============================================================================================================================================================================================
# SETUP CONFIGURATION MODELS
# =============================================================================================================================================================================================


class Folder(BaseModel):
    """Model for folder configurations."""

    name: str = Field(..., description="Name of the folder")
    parent: str = Field(..., description="Parent folder name (empty string for root folders)")
    description: str | None = Field(None, description="Description of the folder")
    labels: list[str] | None = Field(None, description="Labels to apply to the folder")
    snippets: list[str] | None = Field(None, description="Snippet IDs associated with the folder")

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
            "parent": self.parent,
        }

        if self.description:
            model_data["description"] = self.description
        if self.labels:
            model_data["labels"] = self.labels
        if self.snippets:
            model_data["snippets"] = self.snippets

        return model_data


class Label(BaseModel):
    """Model for label configurations."""

    name: str = Field(..., max_length=63, description="Name of the label")
    description: str | None = Field(None, description="Description of the label")

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
        }

        if self.description:
            model_data["description"] = self.description

        return model_data


class Snippet(BaseModel):
    """Model for snippet configurations."""

    name: str = Field(..., description="Name of the snippet")
    description: str | None = Field(None, description="Description of the snippet")
    labels: list[str] | None = Field(None, description="Labels to apply to the snippet")
    enable_prefix: bool | None = Field(None, description="Whether to enable prefix for this snippet")

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
        }

        if self.description:
            model_data["description"] = self.description
        if self.labels:
            model_data["labels"] = self.labels
        if self.enable_prefix is not None:
            model_data["enable_prefix"] = self.enable_prefix

        return model_data


class Variable(BaseModel):
    """Model for variable configurations."""

    name: str = Field(..., max_length=63, description="Name of the variable")
    type: str = Field(..., description="Variable type")
    value: str = Field(..., description="Variable value")
    description: str | None = Field(None, description="Description of the variable")
    folder: str | None = Field(None, description="Folder to scope the variable to")
    snippet: str | None = Field(None, description="Snippet to scope the variable to")
    device: str | None = Field(None, description="Device to scope the variable to")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate that the type is one of the allowed values."""
        allowed = [
            "percent",
            "count",
            "ip-netmask",
            "zone",
            "ip-range",
            "ip-wildcard",
            "device-priority",
            "device-id",
            "egress-max",
            "as-number",
            "fqdn",
            "port",
            "link-tag",
            "group-id",
            "rate",
            "router-id",
            "qos-profile",
            "timer",
        ]
        if v not in allowed:
            raise ValueError(f"type must be one of {allowed}, got {v}")
        return v

    @model_validator(mode="after")
    def validate_container(self) -> "Variable":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
            "type": self.type,
            "value": self.value,
        }

        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        if self.description:
            model_data["description"] = self.description

        return model_data


# =============================================================================================================================================================================================
# UTILITY FUNCTIONS
# =============================================================================================================================================================================================


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


class VulnerabilityProtectionProfile(BaseModel):
    """Model for vulnerability protection profile configurations."""

    folder: str | None = Field(None, description="Folder path for the vulnerability protection profile")
    snippet: str | None = Field(None, description="Snippet path for the vulnerability protection profile")
    device: str | None = Field(None, description="Device path for the vulnerability protection profile")
    name: str = Field(..., description="Name of the vulnerability protection profile")
    description: str | None = Field(None, description="Description of the vulnerability protection profile")

    # Threat exceptions
    threat_exceptions: list[dict[str, Any]] | None = Field(None, description="List of threat exceptions")

    # Rules configuration
    rules: list[dict[str, Any]] | None = Field(None, description="List of vulnerability protection rules")

    @model_validator(mode="after")
    def validate_container(self) -> "VulnerabilityProtectionProfile":
        """Validate that exactly one container is specified."""
        containers = [self.folder, self.snippet, self.device]
        if sum(1 for c in containers if c is not None) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be set")
        return self

    @field_validator("rules")
    def validate_rules(cls, v: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:  # noqa: N805
        """Validate rules configuration."""
        if v is None:
            return v

        for idx, rule in enumerate(v):
            # Required fields
            if "name" not in rule:
                raise ValueError(f"Rule {idx}: 'name' is required")
            if "severity" not in rule:
                raise ValueError(f"Rule {idx}: 'severity' is required")
            if "host" not in rule:
                raise ValueError(f"Rule {idx}: 'host' is required")

            # Validate severity
            valid_severities = [
                "critical",
                "high",
                "medium",
                "low",
                "informational",
                "any",
            ]
            if isinstance(rule["severity"], list):
                for sev in rule["severity"]:
                    if sev not in valid_severities:
                        raise ValueError(f"Rule {idx}: Invalid severity '{sev}'")
            elif rule["severity"] not in valid_severities:
                raise ValueError(f"Rule {idx}: Invalid severity '{rule['severity']}'")

            # Validate host if present
            valid_hosts = ["any", "client", "server"]
            if rule["host"] not in valid_hosts:
                raise ValueError(f"Rule {idx}: Invalid host '{rule['host']}'")

            # Validate action if present
            if "action" in rule:
                valid_actions = [
                    "allow",
                    "alert",
                    "drop",
                    "reset-client",
                    "reset-server",
                    "reset-both",
                    "block-ip",
                    "default",
                ]
                action = rule["action"]
                if isinstance(action, dict):
                    # Action is a dict like {"block_ip": {"track_by": "source", "duration": 300}}
                    pass
                elif action not in valid_actions:
                    raise ValueError(f"Rule {idx}: Invalid action '{action}'")

            # Validate packet_capture if present
            if "packet_capture" in rule:
                valid_captures = ["disable", "single-packet", "extended-capture"]
                if rule["packet_capture"] not in valid_captures:
                    raise ValueError(f"Rule {idx}: Invalid packet_capture '{rule['packet_capture']}'")

            # Validate category if present
            if "category" in rule:
                valid_categories = [
                    "any",
                    "brute-force",
                    "code-execution",
                    "code-obfuscation",
                    "command-execution",
                    "dos",
                    "exploit-kit",
                    "info-leak",
                    "insecure-credentials",
                    "overflow",
                    "phishing",
                    "protocol-anomaly",
                    "scan",
                    "sql-injection",
                ]
                if rule["category"] not in valid_categories:
                    raise ValueError(f"Rule {idx}: Invalid category '{rule['category']}'")

        return v

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        model_data = {
            "name": self.name,
        }

        # Add container field
        if self.folder:
            model_data["folder"] = self.folder
        elif self.snippet:
            model_data["snippet"] = self.snippet
        elif self.device:
            model_data["device"] = self.device

        # Add optional fields
        if self.description:
            model_data["description"] = self.description
        if self.threat_exceptions:
            model_data["threat_exception"] = self.threat_exceptions
        if self.rules:
            # Add default cve field if not specified
            converted_rules = []
            for rule in self.rules:
                rule_copy = dict(rule)
                if "cve" not in rule_copy:
                    rule_copy["cve"] = ["any"]
                converted_rules.append(rule_copy)
            model_data["rules"] = converted_rules

        return model_data


# =============================================================================================================================================================================================
# MOBILE AGENT CONFIGURATION MODELS
# =============================================================================================================================================================================================


class AuthSetting(BaseModel):
    """Model for mobile agent auth setting configurations."""

    name: str = Field(..., description="Name of the auth setting")
    folder: str | None = Field(None, description="Folder path for the auth setting")
    snippet: str | None = Field(None, description="Snippet location")
    device: str | None = Field(None, description="Device location")
    description: str | None = Field(None, description="Description of the auth setting")
    authentication_profile: str | None = Field(None, description="Authentication profile name")
    os: str | None = Field(None, description="Operating system (Any, Windows, macOS, Linux, iOS, Android, ChromeOS)")
    user_credential_or_client_cert_required: bool | None = Field(None, description="Whether user credential or client certificate is required")

    @model_validator(mode="after")
    def validate_container(self) -> "AuthSetting":
        """Validate that at least one container is provided.

        Returns:
            The validated auth setting model

        Raises:
            ValueError: If no container is provided

        """
        if not self.folder and not self.snippet and not self.device:
            raise ValueError("At least one of folder, snippet, or device must be provided")
        return self

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format.

        Returns:
            dict[str, Any]: SDK-compatible dictionary

        """
        model_data: dict[str, Any] = {
            "name": self.name,
        }

        # Add container
        if self.folder:
            model_data["folder"] = self.folder
        if self.snippet:
            model_data["snippet"] = self.snippet
        if self.device:
            model_data["device"] = self.device

        # Add optional fields
        if self.description is not None:
            model_data["description"] = self.description
        if self.authentication_profile is not None:
            model_data["authentication_profile"] = self.authentication_profile
        if self.os is not None:
            model_data["os"] = self.os
        if self.user_credential_or_client_cert_required is not None:
            model_data["user_credential_or_client_cert_required"] = self.user_credential_or_client_cert_required

        return model_data


# =============================================================================================================================================================================================
# INSIGHTS AND MONITORING MODELS
# =============================================================================================================================================================================================


class Alert(BaseModel):
    """Model for alert data from insights API."""

    id: str = Field(..., description="Alert ID")
    name: str = Field(..., description="Alert name")
    severity: str = Field(..., description="Alert severity level (critical, high, medium, low)")
    status: str = Field(..., description="Alert status")
    timestamp: str = Field(..., description="Alert timestamp")
    description: str | None = Field(None, description="Alert description")
    folder: str | None = Field(None, description="Folder containing the alert")
    source: str | None = Field(None, description="Alert source")
    category: str | None = Field(None, description="Alert category")
    impacted_resources: list[str] = Field(default_factory=list, description="List of impacted resources")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional alert metadata")


class MobileUser(BaseModel):
    """Model for mobile user insights data."""

    id: str = Field(..., description="Mobile user ID")
    username: str = Field(..., description="Username")
    device_id: str | None = Field(None, description="Device ID")
    status: str = Field(..., description="Connection status (connected, disconnected)")
    location: str | None = Field(None, description="Current location")
    last_seen: str | None = Field(None, description="Last seen timestamp")
    ip_address: str | None = Field(None, description="IP address")
    folder: str | None = Field(None, description="Folder")
    gateway: str | None = Field(None, description="Connected gateway")
    bandwidth_used: int | None = Field(None, description="Bandwidth used in Mbps")
    session_duration: int | None = Field(None, description="Session duration in seconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional user metadata")


class Location(BaseModel):
    """Model for location insights data."""

    id: str = Field(..., description="Location ID")
    name: str = Field(..., description="Location name")
    region: str | None = Field(None, description="Geographic region")
    country: str | None = Field(None, description="Country")
    state: str | None = Field(None, description="State or province")
    city: str | None = Field(None, description="City")
    latitude: float | None = Field(None, description="Latitude coordinate")
    longitude: float | None = Field(None, description="Longitude coordinate")
    folder: str | None = Field(None, description="Folder")
    total_users: int | None = Field(None, description="Total users at location")
    active_users: int | None = Field(None, description="Active users at location")
    bandwidth_capacity: int | None = Field(None, description="Bandwidth capacity in Mbps")
    bandwidth_used: int | None = Field(None, description="Bandwidth used in Mbps")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional location metadata")


class RemoteNetworkInsights(BaseModel):
    """Model for remote network insights data."""

    id: str = Field(..., description="Remote network ID")
    name: str = Field(..., description="Remote network name")
    connectivity_status: str = Field(..., description="Connectivity status (connected, disconnected, degraded)")
    folder: str | None = Field(None, description="Folder")
    site_id: str | None = Field(None, description="Site ID")
    region: str | None = Field(None, description="Region")
    bandwidth_allocated: int | None = Field(None, description="Allocated bandwidth in Mbps")
    bandwidth_used: int | None = Field(None, description="Used bandwidth in Mbps")
    latency: float | None = Field(None, description="Latency in milliseconds")
    packet_loss: float | None = Field(None, description="Packet loss percentage")
    jitter: float | None = Field(None, description="Jitter in milliseconds")
    tunnel_count: int | None = Field(None, description="Number of tunnels")
    active_tunnels: int | None = Field(None, description="Number of active tunnels")
    last_status_change: str | None = Field(None, description="Last status change timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional network metadata")


class ServiceConnectionInsights(BaseModel):
    """Model for service connection insights data."""

    id: str = Field(..., description="Service connection ID")
    name: str = Field(..., description="Service connection name")
    health_status: str = Field(..., description="Health status (healthy, unhealthy, degraded)")
    folder: str | None = Field(None, description="Folder")
    region: str | None = Field(None, description="Region")
    service_type: str | None = Field(None, description="Service type")
    latency: float | None = Field(None, description="Latency in milliseconds")
    throughput: float | None = Field(None, description="Throughput in Mbps")
    availability: float | None = Field(None, description="Availability percentage")
    uptime: int | None = Field(None, description="Uptime in seconds")
    last_health_check: str | None = Field(None, description="Last health check timestamp")
    error_count: int | None = Field(None, description="Error count")
    warning_count: int | None = Field(None, description="Warning count")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional connection metadata")


class Tunnel(BaseModel):
    """Model for tunnel insights data."""

    id: str = Field(..., description="Tunnel ID")
    name: str = Field(..., description="Tunnel name")
    status: str = Field(..., description="Tunnel status (up, down)")
    tunnel_type: str | None = Field(None, description="Tunnel type (IPSec, SSL, etc)")
    folder: str | None = Field(None, description="Folder")
    source_zone: str | None = Field(None, description="Source zone")
    destination_zone: str | None = Field(None, description="Destination zone")
    local_address: str | None = Field(None, description="Local endpoint address")
    remote_address: str | None = Field(None, description="Remote endpoint address")
    bytes_sent: int | None = Field(None, description="Bytes sent")
    bytes_received: int | None = Field(None, description="Bytes received")
    packets_sent: int | None = Field(None, description="Packets sent")
    packets_received: int | None = Field(None, description="Packets received")
    latency: float | None = Field(None, description="Latency in milliseconds")
    jitter: float | None = Field(None, description="Jitter in milliseconds")
    packet_loss: float | None = Field(None, description="Packet loss percentage")
    uptime: int | None = Field(None, description="Uptime in seconds")
    last_state_change: str | None = Field(None, description="Last state change timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional tunnel metadata")


# =============================================================================================================================================================================================
# BGP ROUTING CONFIGURATION MODELS
# =============================================================================================================================================================================================


class BGPRouting(BaseModel):
    """Model for BGP routing configurations (singleton, no folder)."""

    backbone_routing: str = Field(
        ...,
        description="Backbone routing mode (no-asymmetric-routing, asymmetric-routing-only, asymmetric-routing-with-load-share)",
    )
    routing_preference: str | None = Field(
        None,
        description="Routing preference (default, hot_potato_routing)",
    )
    accept_route_over_sc: bool = Field(False, description="Accept routes over service connections")
    outbound_routes_for_services: list[str] = Field(default_factory=list, description="Outbound routes for services in CIDR notation")
    add_host_route_to_ike_peer: bool = Field(False, description="Add host route to IKE peer")
    withdraw_static_route: bool = Field(False, description="Withdraw static routes")

    @field_validator("backbone_routing")
    @classmethod
    def validate_backbone_routing(cls, v: str) -> str:
        """Validate backbone_routing value."""
        valid_values = {"no-asymmetric-routing", "asymmetric-routing-only", "asymmetric-routing-with-load-share"}
        if v not in valid_values:
            raise ValueError(f"backbone_routing must be one of: {', '.join(sorted(valid_values))}")
        return v

    @field_validator("routing_preference")
    @classmethod
    def validate_routing_preference(cls, v: str | None) -> str | None:
        """Validate routing_preference value."""
        if v is not None:
            valid_values = {"default", "hot_potato_routing"}
            if v not in valid_values:
                raise ValueError(f"routing_preference must be one of: {', '.join(sorted(valid_values))}")
        return v

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        data: dict[str, Any] = {
            "backbone_routing": self.backbone_routing,
            "accept_route_over_SC": self.accept_route_over_sc,
            "outbound_routes_for_services": self.outbound_routes_for_services,
            "add_host_route_to_ike_peer": self.add_host_route_to_ike_peer,
            "withdraw_static_route": self.withdraw_static_route,
        }
        if self.routing_preference:
            if self.routing_preference == "default":
                data["routing_preference"] = {"default": {}}
            elif self.routing_preference == "hot_potato_routing":
                data["routing_preference"] = {"hot_potato_routing": {}}
        return data


# =============================================================================================================================================================================================
# INTERNAL DNS SERVER CONFIGURATION MODELS
# =============================================================================================================================================================================================


class InternalDNSServer(BaseModel):
    """Model for internal DNS server configurations."""

    name: str = Field(..., max_length=63, pattern=r"^[0-9a-zA-Z._\- ]+$", description="Name of the internal DNS server")
    domain_name: list[str] = Field(..., min_length=1, description="DNS domain name(s)")
    primary: str = Field(..., description="Primary DNS server IP address")
    secondary: str | None = Field(None, description="Secondary DNS server IP address")

    @field_validator("domain_name", mode="before")
    @classmethod
    def validate_domain_name(cls, v: Any) -> list[str]:
        """Ensure domain_name is a list."""
        if isinstance(v, str):
            return [v]
        return v

    def to_sdk_model(self) -> dict[str, Any]:
        """Convert CLI model to SDK model format."""
        data: dict[str, Any] = {
            "name": self.name,
            "domain_name": self.domain_name,
            "primary": self.primary,
        }
        if self.secondary:
            data["secondary"] = self.secondary
        return data


# =============================================================================================================================================================================================
# POSTURE / BPA VALIDATORS
# =============================================================================================================================================================================================


class PostureExport(BaseModel):
    """Validator for posture export command parameters.

    Attributes:
        host: PAN-OS firewall hostname or IP address.
        user: Admin username for XML API authentication.
        password: Admin password (optional, can come from env).
        output: Output file path for exported config.
        category: Config category to export (running or candidate).

    """

    host: str = Field(..., min_length=1, description="Firewall hostname or IP")
    user: str = Field(..., min_length=1, description="Admin username")
    password: str | None = Field(None, description="Admin password")
    output: str = Field("config.xml", description="Output file path")
    category: str = Field("running", description="Config category")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate category is running or candidate."""
        allowed = {"running", "candidate"}
        if v not in allowed:
            raise ValueError(f"category must be one of {allowed}, got '{v}'")
        return v


class BpaAssessRequest(BaseModel):
    """Validator for BPA assess command parameters.

    Attributes:
        config: Path to the config file to assess.
        delete_after_processing: Delete config from cloud after assessment.
        output: Output file path for BPA report JSON.
        timeout: Maximum seconds to wait for BPA processing.

    """

    config: str = Field(..., min_length=1, description="Config file path")
    delete_after_processing: bool = Field(True, description="Delete config after processing")
    output: str = Field("report.json", description="Output file path for report")
    timeout: int = Field(300, ge=30, le=600, description="Max wait seconds")


class BpaStatusResponse(BaseModel):
    """Validator for BPA processing status API response.

    Attributes:
        status: Processing status (QUEUED, IN_PROGRESS, COMPLETED, FAILED).
        message: Optional status message.
        result: Result object populated when status is COMPLETED.

    """

    status: str = Field(..., description="Processing status")
    message: str | None = Field(None, description="Status message")
    result: dict | None = Field(None, description="Result when completed")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is a known BPA status."""
        allowed = {"QUEUED", "UPLOAD_COMPLETE", "IN_PROGRESS", "COMPLETED", "FAILED"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}, got '{v}'")
        return v
