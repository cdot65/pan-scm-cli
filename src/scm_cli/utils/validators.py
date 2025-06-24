"""Model validators for scm-cli.

This module defines integrations with SDK Pydantic models for validating input data structures before
sending them to the SCM API. These models enforce data integrity and ensure
that all required fields are present and correctly formatted.
"""

from typing import Any, TypeVar

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

# ========================================================================================================================================================================================
# TYPE DEFINITIONS
# ========================================================================================================================================================================================

# Create a type variable bound to BaseModel
ModelT = TypeVar("ModelT", bound=BaseModel)

# ========================================================================================================================================================================================
# SASE DEPLOYMENT CONFIGURATION MODELS
# ========================================================================================================================================================================================


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
            "folder": self.folder,
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
            "folder": self.folder,
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


# ========================================================================================================================================================================================
# OBJECTS CONFIGURATION MODELS
# ========================================================================================================================================================================================


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
                if isinstance(action, dict) and "alert" in action:
                    # It's an alert with packet capture
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


# ========================================================================================================================================================================================
# INSIGHTS AND MONITORING MODELS
# ========================================================================================================================================================================================


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
