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
    name: str = Field(..., min_length=1, max_length=63, pattern=r"^[ a-zA-Z\d.\-_]+$", description="Name of the external dynamic list")
    type: str = Field(..., description="Type of EDL (predefined_ip, predefined_url, ip, domain, url, imsi, imei)")

    # Type-specific configurations
    url: str = Field("", max_length=255, description="URL for the external list")
    description: str = Field("", max_length=255, description="Description of the external dynamic list")
    exception_list: list[str] = Field(default_factory=list, description="Exception list entries")

    # For custom EDLs (ip, domain, url, imsi, imei)
    recurring: str | None = Field(None, description="Update frequency (five_minute, hourly, daily, weekly, monthly)")
    hour: str | None = Field(None, pattern=r"([01][0-9]|[2][0-3])", description="Hour for daily/weekly/monthly updates (00-23)")
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
        valid_types = ["predefined_ip", "predefined_url", "ip", "domain", "url", "imsi", "imei"]
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
                type_config["auth"] = {"username": self.username, "password": self.password}

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
                type_config["recurring"] = {"monthly": {"day_of_month": int(self.day), "at": self.hour}}

            # Add domain-specific options
            if self.type == "domain" and self.expand_domain:
                type_config["expand_domain"] = self.expand_domain

            model_data["type"] = {self.type: type_config}

        return model_data


class HIPObject(BaseModel):
    """Model for HIP object configurations with folder path."""

    folder: str = Field(..., description="Folder path for the HIP object")
    name: str = Field(..., min_length=1, max_length=31, pattern=r"^[ a-zA-Z0-9.\-_]+$", description="Name of the HIP object")
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
        if any([self.host_info_domain, self.host_info_os, self.host_info_client_version,
                self.host_info_host_name, self.host_info_host_id, self.host_info_managed is not None,
                self.host_info_serial_number]):
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
                criteria["os"] = {"contains": {self.host_info_os: self.host_info_os_value}}

            # Managed state
            if self.host_info_managed is not None:
                criteria["managed"] = self.host_info_managed

            model_data["host_info"] = {"criteria": criteria}

        # Build network info
        if self.network_info_type and self.network_info_value:
            network_criteria = {}
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
        if any([self.mobile_device_jailbroken is not None, self.mobile_device_disk_encrypted is not None,
                self.mobile_device_passcode_set is not None, self.mobile_device_last_checkin_time,
                self.mobile_device_has_malware is not None, self.mobile_device_has_unmanaged_app is not None,
                self.mobile_device_applications]):
            mobile_criteria = {}
            
            if self.mobile_device_jailbroken is not None:
                mobile_criteria["jailbroken"] = self.mobile_device_jailbroken
            if self.mobile_device_disk_encrypted is not None:
                mobile_criteria["disk_encrypted"] = self.mobile_device_disk_encrypted
            if self.mobile_device_passcode_set is not None:
                mobile_criteria["passcode_set"] = self.mobile_device_passcode_set
                
            if self.mobile_device_last_checkin_time and self.mobile_device_last_checkin_value:
                mobile_criteria["last_checkin_time"] = {
                    self.mobile_device_last_checkin_time: self.mobile_device_last_checkin_value
                }
                
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
            except (TypeError, ValueError):
                raise ValueError(f"Server {idx}: port must be a valid integer")
            
            # HTTPS-specific validations
            if server["protocol"] == "HTTPS":
                if "tls_version" in server and server["tls_version"] not in ["1.0", "1.1", "1.2", "1.3"]:
                    raise ValueError(f"Server {idx}: tls_version must be one of: 1.0, 1.1, 1.2, 1.3")
            
            # Validate HTTP method if present
            if "http_method" in server and server["http_method"] not in ["GET", "POST", "PUT", "DELETE"]:
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
