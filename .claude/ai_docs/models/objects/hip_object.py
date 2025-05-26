"""HIP Object models for Strata Cloud Manager SDK.

Contains Pydantic models for representing HIP object resources and related data.
"""

# scm/models/objects/hip_object.py

from typing import Literal, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BaseHIPModel(BaseModel):
    """Base model with common configuration for all HIP object models."""

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True,
        populate_by_name=True,
    )


class NameProductModel(BaseHIPModel):
    """Model for name-product pairs used in vendor specifications."""

    name: str = Field(
        ...,
        max_length=103,
        description="Name identifier",
    )
    product: list[str] | None = Field(
        None,
        max_length=1023,
        description="List of associated products",
    )


class SecurityVendorModel(BaseHIPModel):
    """Model for security vendor specifications."""

    name: str = Field(
        ...,
        max_length=103,
        description="Vendor name",
    )
    product: list[str] | None = Field(
        None,
        max_length=1023,
        description="List of vendor products",
    )


class CertificateAttributeModel(BaseHIPModel):
    """Model for certificate attributes."""

    name: str = Field(
        ...,
        description="Attribute name",
    )
    value: str = Field(
        ...,
        max_length=1024,
        pattern=r"^[a-zA-Z0-9\-_. ]+$",
        description="Attribute value",
    )


# String Comparison Models
class StrContainsModel(BaseHIPModel):
    """Model for string contains comparison."""

    contains: str = Field(
        ...,
        max_length=255,
        description="String to check for containment",
    )


class StrIsModel(BaseHIPModel):
    """Model for string equality comparison."""

    is_: str = Field(
        ...,
        alias="is",
        max_length=255,
        description="String to check for equality",
    )


class StrIsNotModel(BaseHIPModel):
    """Model for string inequality comparison."""

    is_not: str = Field(
        ...,
        max_length=255,
        description="String to check for inequality",
    )


StrComparison = Union[
    StrContainsModel,
    StrIsModel,
    StrIsNotModel,
]


# OS Models
class MicrosoftOSModel(BaseHIPModel):
    """Model for Microsoft OS specification."""

    Microsoft: str = Field(
        "All",
        max_length=255,
        description="Microsoft OS specification",
    )


class AppleOSModel(BaseHIPModel):
    """Model for Apple OS specification."""

    Apple: str = Field(
        "All",
        max_length=255,
        description="Apple OS specification",
    )


class GoogleOSModel(BaseHIPModel):
    """Model for Google OS specification."""

    Google: str = Field(
        "All",
        max_length=255,
        description="Google OS specification",
    )


class LinuxOSModel(BaseHIPModel):
    """Model for Linux OS specification."""

    Linux: str = Field(
        "All",
        max_length=255,
        description="Linux OS specification",
    )


class OtherOSModel(BaseHIPModel):
    """Model for other OS specification."""

    Other: str = Field(
        ...,
        max_length=255,
        description="Other OS specification",
    )


OSVendorModel = Union[
    MicrosoftOSModel,
    AppleOSModel,
    GoogleOSModel,
    LinuxOSModel,
    OtherOSModel,
]


class OSContainsModel(BaseHIPModel):
    """Model for OS contains specification."""

    contains: OSVendorModel = Field(
        ...,
        description="OS vendor specification",
    )


# Host Info Models
class HostInfoCriteriaModel(BaseHIPModel):
    """Model for host information criteria."""

    domain: StrComparison | None = Field(
        None,
        description="Domain criteria",
    )
    os: OSContainsModel | None = Field(
        None,
        description="Operating system criteria",
    )
    client_version: StrComparison | None = Field(
        None,
        description="Client version criteria",
    )
    host_name: StrComparison | None = Field(
        None,
        description="Host name criteria",
    )
    host_id: StrComparison | None = Field(
        None,
        description="Host ID criteria",
    )
    managed: bool | None = Field(
        None,
        description="Managed state criteria",
    )
    serial_number: StrComparison | None = Field(
        None,
        description="Serial number criteria",
    )


class HostInfoModel(BaseHIPModel):
    """Model for host information section."""

    criteria: HostInfoCriteriaModel = Field(
        ...,
        description="Host information criteria",
    )


# Network Models
class NetworkTypeModel(BaseHIPModel):
    """Base model for network type specification."""

    pass


class WifiModel(NetworkTypeModel):
    """Model for Wi-Fi network specification."""

    wifi: dict | None = Field(
        None,
        description="WiFi network configuration",
    )


class MobileModel(NetworkTypeModel):
    """Model for mobile network specification."""

    mobile: dict | None = Field(
        None,
        description="Mobile network configuration",
    )


class EthernetModel(NetworkTypeModel):
    """Model for ethernet network specification."""

    ethernet: dict | None = Field(
        None,
        description="Ethernet network configuration",
    )


class UnknownModel(NetworkTypeModel):
    """Model for unknown network specification."""

    unknown: dict | None = Field(
        None,
        description="Unknown network configuration",
    )


NetworkIsOneOf = Union[
    WifiModel,
    MobileModel,
    UnknownModel,
]
NetworkIsNotOneOf = Union[
    WifiModel,
    MobileModel,
    EthernetModel,
    UnknownModel,
]


class NetworkIsModel(BaseHIPModel):
    """Model for network type positive specification."""

    is_: NetworkIsOneOf = Field(
        ...,
        alias="is",
        description="Network type specification",
    )


class NetworkIsNotModel(BaseHIPModel):
    """Model for network type negative specification."""

    is_not: NetworkIsNotOneOf = Field(
        ...,
        description="Network type negative specification",
    )


NetworkOneOf = Union[
    NetworkIsModel,
    NetworkIsNotModel,
]


class NetworkCriteriaModel(BaseHIPModel):
    """Model for network criteria."""

    network: NetworkOneOf | None = Field(
        None,
        description="Network criteria specification",
    )


class NetworkInfoModel(BaseHIPModel):
    """Model for network information section."""

    criteria: NetworkCriteriaModel = Field(
        ...,
        description="Network information criteria",
    )


# Time and Update Models
class DaysModel(BaseHIPModel):
    """Model for days specification."""

    days: int = Field(
        ...,
        ge=1,
        le=65535,
        description="Number of days",
    )


class HoursModel(BaseHIPModel):
    """Model for hours specification."""

    hours: int = Field(
        ...,
        ge=1,
        le=65535,
        description="Number of hours",
    )


class VersionsModel(BaseHIPModel):
    """Model for versions specification."""

    versions: int = Field(
        ...,
        ge=1,
        le=65535,
        description="Number of versions",
    )


TimeSpecification = Union[
    DaysModel,
    HoursModel,
]
UpdateSpecification = Union[
    DaysModel,
    VersionsModel,
]


# Security Product Models
class SecurityProductCriteriaModel(BaseHIPModel):
    """Base model for security product criteria."""

    is_installed: bool | None = Field(
        True,
        description="Installation status",
    )
    is_enabled: Literal["no", "yes", "not-available"] | None = Field(
        None,
        description="Enabled status",
    )


class SecurityProductModel(BaseHIPModel):
    """Base model for security products."""

    criteria: SecurityProductCriteriaModel = Field(
        ...,
        description="Security product criteria",
    )
    vendor: list[SecurityVendorModel] | None = Field(
        None,
        description="Vendor information",
    )
    exclude_vendor: bool | None = Field(
        False,
        description="Exclude vendor flag",
    )


# Patch Management Models
class MissingPatchesModel(BaseHIPModel):
    """Model for missing patches specification."""

    severity: int | None = Field(
        None,
        ge=0,
        le=100000,
        description="Patch severity level",
    )
    patches: list[str] | None = Field(
        None,
        description="List of patches",
    )
    check: Literal["has-any", "has-none", "has-all"] = Field(
        "has-any",
        description="Check type",
    )


class PatchManagementCriteriaModel(SecurityProductCriteriaModel):
    """Model for patch management criteria."""

    missing_patches: MissingPatchesModel | None = Field(
        None,
        description="Missing patches specification",
    )


class PatchManagementModel(SecurityProductModel):
    """Model for patch management section."""

    criteria: PatchManagementCriteriaModel = Field(
        ...,
        description="Patch management criteria",
    )


# Disk Encryption Models
class EncryptionLocationModel(BaseHIPModel):
    """Model for encryption location."""

    name: str = Field(
        ...,
        max_length=1023,
        description="Location name",
    )
    encryption_state: dict = Field(  # Simply use dict to allow the nested structure
        ...,
        description="Encryption state specification",
    )


class DiskEncryptionCriteriaModel(SecurityProductCriteriaModel):
    """Model for disk encryption criteria."""

    encrypted_locations: list[EncryptionLocationModel] | None = Field(
        None,
        description="Encrypted locations",
    )


class DiskEncryptionModel(SecurityProductModel):
    """Model for disk encryption section."""

    criteria: DiskEncryptionCriteriaModel = Field(
        ...,
        description="Disk encryption criteria",
    )


class EncryptionStateIs(BaseModel):
    """Model for encryption state 'is' condition."""

    is_: Literal["encrypted", "unencrypted", "partial", "unknown"] = Field(
        ...,
        alias="is",
        description="Encryption state value",
    )


class EncryptionStateIsNot(BaseModel):
    """Model for encryption state 'is_not' condition."""

    is_not: Literal["encrypted", "unencrypted", "partial", "unknown"] = Field(
        ...,
        description="Encryption state value to exclude",
    )


# Mobile Device Models
class MobileApplicationModel(BaseHIPModel):
    """Model for mobile application."""

    name: str = Field(
        ...,
        max_length=31,
        description="Application name",
    )
    package: str | None = Field(
        None,
        max_length=1024,
        pattern=r"^[a-zA-Z0-9\-_. ]+$",
        description="Package name",
    )
    hash: str | None = Field(
        None,
        max_length=1024,
        pattern=r"^[a-fA-F0-9]+$",
        description="Application hash",
    )


class MobileApplicationsModel(BaseHIPModel):
    """Model for mobile applications section."""

    has_malware: bool | None = Field(
        None,
        description="Malware presence flag",
    )
    has_unmanaged_app: bool | None = Field(
        None,
        description="Unmanaged apps presence flag",
    )
    includes: list[MobileApplicationModel] | None = Field(
        None,
        description="Included applications",
    )


class MobileDeviceCriteriaModel(BaseHIPModel):
    """Model for mobile device criteria."""

    jailbroken: bool | None = Field(
        None,
        description="Jailbroken status",
    )
    disk_encrypted: bool | None = Field(
        None,
        description="Disk encryption status",
    )
    passcode_set: bool | None = Field(
        None,
        description="Passcode status",
    )
    last_checkin_time: DaysModel | HoursModel | None = Field(
        None,
        description="Last check-in time",
    )
    applications: MobileApplicationsModel | None = Field(
        None,
        description="Applications criteria",
    )


class MobileDeviceModel(BaseHIPModel):
    """Model for mobile device section."""

    criteria: MobileDeviceCriteriaModel = Field(
        ...,
        description="Mobile device criteria",
    )


# Certificate Models
class CertificateCriteriaModel(BaseHIPModel):
    """Model for certificate criteria."""

    certificate_profile: str | None = Field(
        None,
        description="Certificate profile name",
    )
    certificate_attributes: list[CertificateAttributeModel] | None = Field(
        None,
        description="Certificate attributes",
    )


class CertificateModel(BaseHIPModel):
    """Model for certificate section."""

    criteria: CertificateCriteriaModel = Field(
        ...,
        description="Certificate criteria",
    )


class HIPObjectBaseModel(BaseHIPModel):
    """Base model for HIP objects."""

    name: str = Field(
        ...,
        max_length=31,
        pattern=r"^[ a-zA-Z0-9.\-_]+$",
        description="The name of the HIP object",
        examples=["windows-workstation-policy"],
    )
    description: str | None = Field(
        None,
        max_length=255,
        description="Description of the HIP object",
    )
    host_info: HostInfoModel | None = Field(
        None,
        description="Host information criteria",
    )
    network_info: NetworkInfoModel | None = Field(
        None,
        description="Network information criteria",
    )
    patch_management: PatchManagementModel | None = Field(
        None,
        description="Patch management criteria",
    )
    disk_encryption: DiskEncryptionModel | None = Field(
        None,
        description="Disk encryption criteria",
    )
    mobile_device: MobileDeviceModel | None = Field(
        None,
        description="Mobile device criteria",
    )
    certificate: CertificateModel | None = Field(
        None,
        description="Certificate criteria",
    )
    folder: str | None = Field(
        None,
        pattern=r"^[a-zA-Z0-9\-_. ]+$",
        max_length=64,
        description="The folder in which the resource is defined",
        examples=["Prisma Access"],
    )
    snippet: str | None = Field(
        None,
        pattern=r"^[a-zA-Z0-9\-_. ]+$",
        max_length=64,
        description="The snippet in which the resource is defined",
        examples=["My Snippet"],
    )
    device: str | None = Field(
        None,
        pattern=r"^[a-zA-Z0-9\-_. ]+$",
        max_length=64,
        description="The device in which the resource is defined",
        examples=["My Device"],
    )


class HIPObjectCreateModel(HIPObjectBaseModel):
    """Model for creating a new HIP object."""

    @model_validator(mode="after")
    def validate_container_type(self) -> "HIPObjectCreateModel":
        """Validate that exactly one container type is provided."""
        container_fields = [
            "folder",
            "snippet",
            "device",
        ]
        provided = [field for field in container_fields if getattr(self, field) is not None]
        if len(provided) != 1:
            raise ValueError("Exactly one of 'folder', 'snippet', or 'device' must be provided.")
        return self


class HIPObjectUpdateModel(HIPObjectBaseModel):
    """Model for updating an existing HIP object."""

    id: UUID | None = Field(
        None,
        description="The UUID of the HIP object",
        examples=["123e4567-e89b-12d3-a456-426655440000"],
    )


class HIPObjectResponseModel(HIPObjectBaseModel):
    """Model for HIP object responses."""

    id: UUID = Field(
        ...,
        description="The UUID of the HIP object",
        examples=["123e4567-e89b-12d3-a456-426655440000"],
    )
