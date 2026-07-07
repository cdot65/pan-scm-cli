"""Network module commands for scm.

This module implements set, delete, and load commands for network-related
configurations such as zones and interfaces.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import typer
import yaml

from ..utils import validate_location_params
from ..utils.bulk import run_bulk
from ..utils.config import load_from_yaml
from ..utils.decorators import handle_command_errors
from ..utils.output import OUTPUT_OPTION, OutputFormat, emit, error, info, success
from ..utils.sdk_client import scm_client
from ..utils.validators import (
    AggregateInterface,
    BgpAddressFamilyProfile,
    BgpAuthProfile,
    BgpFilteringProfile,
    BgpRedistributionProfile,
    BgpRouteMap,
    BgpRouteMapRedistribution,
    DhcpInterface,
    DnsProxy,
    EthernetInterface,
    IKECryptoProfile,
    IKEGateway,
    IPSecCryptoProfile,
    Layer2Subinterface,
    Layer3Subinterface,
    LoopbackInterface,
    NATRule,
    OspfAuthProfile,
    PbfRule,
    QosProfile,
    QosRule,
    RouteAccessList,
    RoutePrefixList,
    TunnelInterface,
    VlanInterface,
    Zone,
)

# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

# Create app groups for each action type
set_app = typer.Typer(help="Create or update network configurations")
delete_app = typer.Typer(help="Remove network configurations")
load_app = typer.Typer(help="Load network configurations from YAML files")
show_app = typer.Typer(help="Display network configurations")
backup_app = typer.Typer(help="Backup network configurations to YAML files")

# =============================================================================================================================================================================================
# COMMAND OPTIONS
# =============================================================================================================================================================================================

# Define typer option constants
MODE_OPTION = typer.Option(
    ...,
    "--mode",
    help="Zone mode (layer2, layer3, external, virtual-wire, tunnel, tap)",
)
INTERFACES_OPTION = typer.Option(
    None,
    "--interfaces",
    help="List of interfaces",
)
ENABLE_USER_ID_OPTION = typer.Option(
    None,
    "--enable-user-id",
    help="Enable user identification",
)
FILE_OPTION = typer.Option(
    ...,
    "--file",
    help="YAML file to load configurations from",
)
DRY_RUN_OPTION = typer.Option(
    False,
    "--dry-run",
    help="Simulate execution without applying changes",
)

# Backup command options
BACKUP_FOLDER_OPTION = typer.Option(
    None,
    "--folder",
    help="Folder path for backup",
)
BACKUP_SNIPPET_OPTION = typer.Option(
    None,
    "--snippet",
    help="Snippet path for backup",
)
BACKUP_DEVICE_OPTION = typer.Option(
    None,
    "--device",
    help="Device path for backup",
)
BACKUP_FILE_OPTION = typer.Option(
    None,
    "--file",
    help="Output filename for backup (defaults to {object-type}-{location}.yaml)",
)

# NAT rule option constants
NAT_DESCRIPTION_OPTION = typer.Option(
    None,
    "--description",
    help="Description of the NAT rule",
)
NAT_TAGS_OPTION = typer.Option(
    None,
    "--tags",
    help="Tags for the NAT rule (repeat for multiple)",
)
NAT_DISABLED_OPTION = typer.Option(
    False,
    "--disabled",
    help="Disable the NAT rule",
)
NAT_NAT_TYPE_OPTION = typer.Option(
    "ipv4",
    "--nat-type",
    help="NAT type (ipv4, nat64, nptv6)",
)
NAT_FROM_ZONES_OPTION = typer.Option(
    None,
    "--from-zone",
    help="Source zone(s)",
)
NAT_TO_ZONES_OPTION = typer.Option(
    None,
    "--to-zone",
    help="Destination zone(s)",
)
NAT_TO_INTERFACE_OPTION = typer.Option(
    None,
    "--to-interface",
    help="Destination interface",
)
NAT_SOURCE_OPTION = typer.Option(
    None,
    "--source",
    help="Source address(es)",
)
NAT_DESTINATION_OPTION = typer.Option(
    None,
    "--destination",
    help="Destination address(es)",
)
NAT_SERVICE_OPTION = typer.Option(
    "any",
    "--service",
    help="TCP/UDP service",
)
NAT_SOURCE_TRANSLATION_OPTION = typer.Option(
    None,
    "--source-translation",
    help="Source translation config as JSON string",
)
NAT_DESTINATION_TRANSLATION_OPTION = typer.Option(
    None,
    "--destination-translation",
    help="Destination translation config as JSON string",
)

# Container override options for load commands
LOAD_FOLDER_OPTION = typer.Option(
    None,
    "--folder",
    help="Override folder location for all objects",
)
LOAD_SNIPPET_OPTION = typer.Option(
    None,
    "--snippet",
    help="Override snippet location for all objects",
)
LOAD_DEVICE_OPTION = typer.Option(
    None,
    "--device",
    help="Override device location for all objects",
)

# IPsec crypto profile option constants (module-level to avoid B008)
IPSEC_ESP_ENCRYPTION_OPTION: list[str] = typer.Option(
    ["aes-256-cbc"],
    "--esp-encryption",
    help="ESP encryption algorithms (des, 3des, aes-128-cbc, aes-192-cbc, aes-256-cbc, aes-128-gcm, aes-256-gcm, null)",
)
IPSEC_ESP_AUTHENTICATION_OPTION: list[str] = typer.Option(
    ["sha256"],
    "--esp-authentication",
    help="ESP authentication algorithms (md5, sha1, sha256, sha384, sha512)",
)
IPSEC_DH_GROUP_OPTION = typer.Option(
    "group14",
    "--dh-group",
    help="DH group for PFS (no-pfs, group1, group2, group5, group14, group19, group20)",
)
IPSEC_LIFETIME_SECONDS_OPTION = typer.Option(None, "--lifetime-seconds", help="Lifetime in seconds (180-65535)")
IPSEC_LIFETIME_HOURS_OPTION = typer.Option(None, "--lifetime-hours", help="Lifetime in hours (1-65535)")

IKE_HASH_OPTION = typer.Option(..., "--hash", help="Hash algorithms (sha256, sha384, sha512, sha1, md5)")
IKE_DH_GROUP_OPTION = typer.Option(..., "--dh-group", help="DH groups (group1, group2, group5, group14, group19, group20)")
IKE_ENCRYPTION_OPTION = typer.Option(..., "--encryption", help="Encryption algorithms (aes-256-cbc, aes-128-cbc, etc.)")

# =============================================================================================================================================================================================
# HELPER FUNCTIONS
# =============================================================================================================================================================================================

QOS_PROFILE_ALLOWED_FOLDERS = ["Remote Networks", "Service Connections"]


def validate_qos_profile_folder(folder: str | None) -> None:
    """Validate that folder is allowed for QoS profiles."""
    if folder is not None and folder not in QOS_PROFILE_ALLOWED_FOLDERS:
        error(f"Error: QoS profiles only support folders: {', '.join(QOS_PROFILE_ALLOWED_FOLDERS)}. Got: '{folder}'")
        raise typer.Exit(code=1)


def get_default_backup_filename(object_type: str, location_type: str, location_value: str) -> str:
    """Generate the default backup filename.

    Args:
        object_type: Type of object (e.g., "security-zone")
        location_type: Type of location (folder, snippet, device)
        location_value: Value of the location

    Returns:
        str: Default filename

    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_location = location_value.lower().replace(" ", "-").replace("/", "-")
    return f"{object_type}_{location_type}_{safe_location}_{timestamp}.yaml"


# =============================================================================================================================================================================================
# IKE CRYPTO PROFILE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("ike-crypto-profile", help="Export IKE crypto profiles to a YAML file.")
@handle_command_errors("backing up IKE crypto profiles")
def backup_ike_crypto_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export IKE crypto profiles from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving IKE crypto profiles from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    profiles = scm_client.list_ike_crypto_profiles(**kwargs)
    if not profiles:
        info(f"No IKE crypto profiles found in {location_type} '{location_value}'")
        return
    export_data = {"ike_crypto_profiles": profiles}
    filename = Path(file or get_default_backup_filename("ike-crypto-profile", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(profiles)} IKE crypto profiles to {filename}")


@delete_app.command("ike-crypto-profile", help="Delete an IKE crypto profile.")
@handle_command_errors("deleting IKE crypto profile")
def delete_ike_crypto_profile(
    name: str = typer.Argument(..., help="Name of the IKE crypto profile to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete an IKE crypto profile."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    profile = scm_client.get_ike_crypto_profile(name=name, folder=folder, snippet=snippet, device=device)
    if not profile:
        error(f"IKE crypto profile '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete IKE crypto profile '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_ike_crypto_profile(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted IKE crypto profile: {name} from {location_value}")


@load_app.command("ike-crypto-profile", help="Load IKE crypto profiles from a YAML file.")
@handle_command_errors("loading IKE crypto profiles")
def load_ike_crypto_profile(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load IKE crypto profiles from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "ike_crypto_profiles" not in data:
        error("No IKE crypto profiles found in file")
        raise typer.Exit(code=1)
    profiles = data["ike_crypto_profiles"]
    if not isinstance(profiles, list):
        profiles = [profiles]

    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        if folder or snippet or device:
            override_type = "folder" if folder else ("snippet" if snippet else "device")
            override_value = folder or snippet or device
            info(f"Container override: {override_type} = '{override_value}'")
        typer.echo(yaml.dump(profiles))
        return None

    created_count = 0

    def _apply(profile_data: dict):
        validated_profile = IKECryptoProfile(**profile_data)
        if folder:
            validated_profile.folder = folder
            validated_profile.snippet = None
            validated_profile.device = None
        elif snippet:
            validated_profile.snippet = snippet
            validated_profile.folder = None
            validated_profile.device = None
        elif device:
            validated_profile.device = device
            validated_profile.folder = None
            validated_profile.snippet = None
        sdk_data = validated_profile.to_sdk_model()
        scm_client.create_ike_crypto_profile(sdk_data)
        return validated_profile

    for _item, validated_profile, exc in run_bulk(profiles, _apply):
        if exc is not None:
            error(f"Error processing IKE crypto profile: {str(exc)}")
            continue
        created_count += 1
        container = validated_profile.folder or validated_profile.snippet or validated_profile.device
        success(f"Created IKE crypto profile: {validated_profile.name} in {container}")
    info(f"\nSummary: Processed {created_count} IKE crypto profiles")


@set_app.command("ike-crypto-profile", help="Create or update an IKE crypto profile.")
@handle_command_errors("creating/updating IKE crypto profile")
def set_ike_crypto_profile(
    name: str = typer.Argument(..., help="Name of the IKE crypto profile"),
    hash: list[str] = IKE_HASH_OPTION,
    dh_group: list[str] = IKE_DH_GROUP_OPTION,
    encryption: list[str] = IKE_ENCRYPTION_OPTION,
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    lifetime_seconds: int = typer.Option(None, "--lifetime-seconds", help="Lifetime in seconds (180-65535)"),
    lifetime_minutes: int = typer.Option(None, "--lifetime-minutes", help="Lifetime in minutes (3-65535)"),
    lifetime_hours: int = typer.Option(None, "--lifetime-hours", help="Lifetime in hours (1-65535)"),
    lifetime_days: int = typer.Option(None, "--lifetime-days", help="Lifetime in days (1-365)"),
    authentication_multiple: int = typer.Option(None, "--authentication-multiple", help="IKEv2 SA reauthentication interval (0-50)"),
) -> None:
    """Create or update an IKE crypto profile."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    location_kwargs = {location_type: location_value}
    validated_profile = IKECryptoProfile(
        name=name,
        hash=hash,
        dh_group=dh_group,
        encryption=encryption,
        lifetime_seconds=lifetime_seconds,
        lifetime_minutes=lifetime_minutes,
        lifetime_hours=lifetime_hours,
        lifetime_days=lifetime_days,
        authentication_multiple=authentication_multiple,
        **location_kwargs,
    )
    sdk_data = validated_profile.to_sdk_model()
    result = scm_client.create_ike_crypto_profile(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created IKE crypto profile: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated IKE crypto profile: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for IKE crypto profile: {name} in {location_value}")


@show_app.command("ike-crypto-profile", help="Show IKE crypto profile details.")
@handle_command_errors("showing IKE crypto profile")
def show_ike_crypto_profile(
    name: str | None = typer.Argument(None, help="Name of the IKE crypto profile to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show IKE crypto profile details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        profile = scm_client.get_ike_crypto_profile(name=name, folder=folder, snippet=snippet, device=device)
        if not profile:
            error(f"IKE crypto profile '{name}' not found")
            raise typer.Exit(code=1)
        emit(profile, output, title=f"IKE Crypto Profile: {name}")
        return profile
    else:
        profiles = scm_client.list_ike_crypto_profiles(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            profiles = profiles[:max_results]
        emit(profiles, output, title=f"IKE Crypto Profiles in {location_type} '{location_value}'")
        return profiles


# =============================================================================================================================================================================================
# AGGREGATE INTERFACE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("aggregate-interface", help="Export aggregate interfaces to a YAML file.")
@handle_command_errors("backing up aggregate interfaces")
def backup_aggregate_interface(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export aggregate interfaces from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving aggregate interfaces from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    interfaces = scm_client.list_aggregate_interfaces(**kwargs)
    if not interfaces:
        info(f"No aggregate interfaces found in {location_type} '{location_value}'")
        return
    export_data = {"aggregate_interfaces": interfaces}
    filename = Path(file or get_default_backup_filename("aggregate-interface", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(interfaces)} aggregate interfaces to {filename}")


@delete_app.command("aggregate-interface", help="Delete an aggregate interface.")
@handle_command_errors("deleting aggregate interface")
def delete_aggregate_interface(
    name: str = typer.Argument(..., help="Name of the aggregate interface to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete an aggregate interface."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    iface = scm_client.get_aggregate_interface(name=name, folder=folder, snippet=snippet, device=device)
    if not iface:
        error(f"Aggregate interface '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete aggregate interface '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_aggregate_interface(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted aggregate interface: {name} from {location_value}")


@load_app.command("aggregate-interface", help="Load aggregate interfaces from a YAML file.")
@handle_command_errors("loading aggregate interfaces")
def load_aggregate_interface(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load aggregate interfaces from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "aggregate_interfaces" not in data:
        error("No aggregate interfaces found in file")
        raise typer.Exit(code=1)
    interfaces = data["aggregate_interfaces"]
    if not isinstance(interfaces, list):
        interfaces = [interfaces]

    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        if folder or snippet or device:
            override_type = "folder" if folder else ("snippet" if snippet else "device")
            override_value = folder or snippet or device
            info(f"Container override: {override_type} = '{override_value}'")
        typer.echo(yaml.dump(interfaces))
        return None

    created_count = 0
    updated_count = 0
    no_change_count = 0

    def _apply(iface_data: dict):
        if folder:
            iface_data["folder"] = folder
            iface_data.pop("snippet", None)
            iface_data.pop("device", None)
        elif snippet:
            iface_data["snippet"] = snippet
            iface_data.pop("folder", None)
            iface_data.pop("device", None)
        elif device:
            iface_data["device"] = device
            iface_data.pop("folder", None)
            iface_data.pop("snippet", None)
        validated_iface = AggregateInterface(**iface_data)
        sdk_data = validated_iface.to_sdk_model()
        result = scm_client.create_aggregate_interface(sdk_data)
        return validated_iface, result

    for _item, outcome, exc in run_bulk(interfaces, _apply):
        if exc is not None:
            error(f"Error processing aggregate interface: {str(exc)}")
            continue
        validated_iface, result = outcome
        action = result.pop("__action__", "created")
        container = validated_iface.folder or validated_iface.snippet or validated_iface.device
        if action == "created":
            created_count += 1
            success(f"Created aggregate interface: {validated_iface.name} in {container}")
        elif action == "updated":
            updated_count += 1
            success(f"Updated aggregate interface: {validated_iface.name} in {container}")
        else:
            no_change_count += 1
            info(f"No changes needed for aggregate interface: {validated_iface.name} in {container}")
    info(f"\nSummary: Processed {created_count + updated_count + no_change_count} aggregate interfaces")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")
    if no_change_count > 0:
        info(f"  - No change: {no_change_count}")


@set_app.command("aggregate-interface", help="Create or update an aggregate interface.")
@handle_command_errors("creating/updating aggregate interface")
def set_aggregate_interface(
    name: str = typer.Argument(..., help="Name of the aggregate interface"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    comment: str = typer.Option(None, "--comment", help="Interface description/comment"),
    layer2_json: str = typer.Option(None, "--layer2-json", help='Layer2 config as JSON (e.g. \'{"vlan_tag": "100"}\')'),
    layer3_json: str = typer.Option(None, "--layer3-json", help='Layer3 config as JSON (e.g. \'{"mtu": 1500, "ip": [{"name": "10.0.0.1/24"}]}\')'),
) -> None:
    """Create or update an aggregate interface."""
    location_type, location_value = validate_location_params(folder, snippet, device)

    iface_data: dict[str, Any] = {
        "name": name,
        location_type: location_value,
    }

    if comment:
        iface_data["comment"] = comment

    if layer2_json:
        iface_data["layer2"] = json.loads(layer2_json)
    if layer3_json:
        iface_data["layer3"] = json.loads(layer3_json)

    validated_iface = AggregateInterface(**iface_data)
    sdk_data = validated_iface.to_sdk_model()
    result = scm_client.create_aggregate_interface(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created aggregate interface: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated aggregate interface: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for aggregate interface: {name} in {location_value}")


@show_app.command("aggregate-interface", help="Show aggregate interface details.")
@handle_command_errors("showing aggregate interface")
def show_aggregate_interface(
    name: str | None = typer.Argument(None, help="Name of the aggregate interface to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show aggregate interface details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        iface = scm_client.get_aggregate_interface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            error(f"Aggregate interface '{name}' not found")
            raise typer.Exit(code=1)
        emit(iface, output, title=f"Aggregate Interface: {name}")
        return iface
    else:
        interfaces = scm_client.list_aggregate_interfaces(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            interfaces = interfaces[:max_results]
        emit(interfaces, output, title=f"Aggregate Interfaces in {location_type} '{location_value}'")
        return interfaces


# =============================================================================================================================================================================================
# IKE GATEWAY COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("ike-gateway", help="Export IKE gateways to a YAML file.")
@handle_command_errors("backing up IKE gateways")
def backup_ike_gateway(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export IKE gateways from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving IKE gateways from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    gateways = scm_client.list_ike_gateways(**kwargs)
    if not gateways:
        info(f"No IKE gateways found in {location_type} '{location_value}'")
        return
    export_data = {"ike_gateways": gateways}
    filename = Path(file or get_default_backup_filename("ike-gateway", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(gateways)} IKE gateways to {filename}")


@delete_app.command("ike-gateway", help="Delete an IKE gateway.")
@handle_command_errors("deleting IKE gateway")
def delete_ike_gateway(
    name: str = typer.Argument(..., help="Name of the IKE gateway to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete an IKE gateway."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    gateway = scm_client.get_ike_gateway(name=name, folder=folder, snippet=snippet, device=device)
    if not gateway:
        error(f"IKE gateway '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete IKE gateway '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_ike_gateway(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted IKE gateway: {name} from {location_value}")


@load_app.command("ike-gateway", help="Load IKE gateways from a YAML file.")
@handle_command_errors("loading IKE gateways")
def load_ike_gateway(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load IKE gateways from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "ike_gateways" not in data:
        error("No IKE gateways found in file")
        raise typer.Exit(code=1)
    gateways = data["ike_gateways"]
    if not isinstance(gateways, list):
        gateways = [gateways]

    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        if folder or snippet or device:
            override_type = "folder" if folder else ("snippet" if snippet else "device")
            override_value = folder or snippet or device
            info(f"Container override: {override_type} = '{override_value}'")
        typer.echo(yaml.dump(gateways))
        return None

    created_count = 0
    updated_count = 0
    no_change_count = 0

    def _apply(gateway_data: dict):
        if folder:
            gateway_data["folder"] = folder
            gateway_data.pop("snippet", None)
            gateway_data.pop("device", None)
        elif snippet:
            gateway_data["snippet"] = snippet
            gateway_data.pop("folder", None)
            gateway_data.pop("device", None)
        elif device:
            gateway_data["device"] = device
            gateway_data.pop("folder", None)
            gateway_data.pop("snippet", None)
        validated_gw = IKEGateway(**gateway_data)
        sdk_data = validated_gw.to_sdk_model()
        result = scm_client.create_ike_gateway(sdk_data)
        return validated_gw, result

    for _item, outcome, exc in run_bulk(gateways, _apply):
        if exc is not None:
            error(f"Error processing IKE gateway: {str(exc)}")
            continue
        validated_gw, result = outcome
        action = result.pop("__action__", "created")
        container = validated_gw.folder or validated_gw.snippet or validated_gw.device
        if action == "created":
            created_count += 1
            success(f"Created IKE gateway: {validated_gw.name} in {container}")
        elif action == "updated":
            updated_count += 1
            success(f"Updated IKE gateway: {validated_gw.name} in {container}")
        else:
            no_change_count += 1
            info(f"No changes needed for IKE gateway: {validated_gw.name} in {container}")
    info(f"\nSummary: Processed {created_count + updated_count + no_change_count} IKE gateways")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")
    if no_change_count > 0:
        info(f"  - No change: {no_change_count}")


@set_app.command("ike-gateway", help="Create or update an IKE gateway.")
@handle_command_errors("creating/updating IKE gateway")
def set_ike_gateway(
    name: str = typer.Argument(..., help="Name of the IKE gateway"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    pre_shared_key: str = typer.Option(None, "--pre-shared-key", help="Pre-shared key for authentication"),
    peer_address_ip: str = typer.Option(None, "--peer-address-ip", help="Peer IP address"),
    peer_address_fqdn: str = typer.Option(None, "--peer-address-fqdn", help="Peer FQDN"),
    peer_address_dynamic: bool = typer.Option(False, "--peer-address-dynamic", help="Use dynamic peer address"),
    protocol_version: str = typer.Option("ikev2-preferred", "--protocol-version", help="IKE version (ikev1, ikev2, ikev2-preferred)"),
    ike_crypto_profile: str = typer.Option(None, "--ike-crypto-profile", help="IKE crypto profile name"),
    peer_id_type: str = typer.Option(None, "--peer-id-type", help="Peer ID type (ipaddr, keyid, fqdn, ufqdn)"),
    peer_id_value: str = typer.Option(None, "--peer-id-value", help="Peer ID value"),
    local_id_type: str = typer.Option(None, "--local-id-type", help="Local ID type (ipaddr, keyid, fqdn, ufqdn)"),
    local_id_value: str = typer.Option(None, "--local-id-value", help="Local ID value"),
    nat_traversal: bool = typer.Option(None, "--nat-traversal", help="Enable NAT traversal"),
    fragmentation: bool = typer.Option(None, "--fragmentation", help="Enable IKE fragmentation"),
    passive_mode: bool = typer.Option(None, "--passive-mode", help="Enable passive mode"),
    dpd_enable: bool = typer.Option(None, "--dpd-enable", help="Enable Dead Peer Detection"),
    authentication_json: str = typer.Option(None, "--authentication-json", help="Full authentication config as JSON (overrides --pre-shared-key)"),
    peer_address_json: str = typer.Option(None, "--peer-address-json", help="Full peer address config as JSON"),
    protocol_json: str = typer.Option(None, "--protocol-json", help="Full protocol config as JSON"),
    protocol_common_json: str = typer.Option(None, "--protocol-common-json", help="Full protocol_common config as JSON"),
) -> None:
    """Create or update an IKE gateway."""
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Build authentication
    if authentication_json:
        authentication = json.loads(authentication_json)
    elif pre_shared_key:
        authentication = {"pre_shared_key": {"key": pre_shared_key}}
    else:
        error("Error: --pre-shared-key or --authentication-json is required")
        raise typer.Exit(code=1)

    # Build peer_address
    if peer_address_json:
        peer_address = json.loads(peer_address_json)
    elif peer_address_ip:
        peer_address = {"ip": peer_address_ip}
    elif peer_address_fqdn:
        peer_address = {"fqdn": peer_address_fqdn}
    elif peer_address_dynamic:
        peer_address = {"dynamic": {}}
    else:
        error("Error: one of --peer-address-ip, --peer-address-fqdn, --peer-address-dynamic, or --peer-address-json is required")
        raise typer.Exit(code=1)

    # Build protocol
    protocol: dict[str, Any]
    if protocol_json:
        protocol = json.loads(protocol_json)
    else:
        protocol = {"version": protocol_version}
        if protocol_version in ("ikev1", "ikev2-preferred"):
            ikev1_config: dict[str, Any] = {}
            if ike_crypto_profile:
                ikev1_config["ike_crypto_profile"] = ike_crypto_profile
            if dpd_enable is not None:
                ikev1_config["dpd"] = {"enable": dpd_enable}
            if ikev1_config:
                protocol["ikev1"] = ikev1_config
        if protocol_version in ("ikev2", "ikev2-preferred"):
            ikev2_config: dict[str, Any] = {}
            if ike_crypto_profile:
                ikev2_config["ike_crypto_profile"] = ike_crypto_profile
            if dpd_enable is not None:
                ikev2_config["dpd"] = {"enable": dpd_enable}
            if ikev2_config:
                protocol["ikev2"] = ikev2_config

    gateway_data: dict[str, Any] = {
        "name": name,
        location_type: location_value,
        "authentication": authentication,
        "peer_address": peer_address,
        "protocol": protocol,
    }

    # Build peer_id
    if peer_id_type and peer_id_value:
        gateway_data["peer_id"] = {"type": peer_id_type, "id": peer_id_value}

    # Build local_id
    if local_id_type and local_id_value:
        gateway_data["local_id"] = {"type": local_id_type, "id": local_id_value}

    # Build protocol_common
    if protocol_common_json:
        gateway_data["protocol_common"] = json.loads(protocol_common_json)
    else:
        protocol_common: dict[str, Any] = {}
        if nat_traversal is not None:
            protocol_common["nat_traversal"] = {"enable": nat_traversal}
        if fragmentation is not None:
            protocol_common["fragmentation"] = {"enable": fragmentation}
        if passive_mode is not None:
            protocol_common["passive_mode"] = passive_mode
        if protocol_common:
            gateway_data["protocol_common"] = protocol_common

    validated_gw = IKEGateway(**gateway_data)
    sdk_data = validated_gw.to_sdk_model()
    result = scm_client.create_ike_gateway(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created IKE gateway: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated IKE gateway: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for IKE gateway: {name} in {location_value}")


@show_app.command("ike-gateway", help="Show IKE gateway details.")
@handle_command_errors("showing IKE gateway")
def show_ike_gateway(
    name: str | None = typer.Argument(None, help="Name of the IKE gateway to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show IKE gateway details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        gateway = scm_client.get_ike_gateway(name=name, folder=folder, snippet=snippet, device=device)
        if not gateway:
            error(f"IKE gateway '{name}' not found")
            raise typer.Exit(code=1)
        emit(gateway, output, title=f"IKE Gateway: {name}")
        return gateway
    else:
        gateways = scm_client.list_ike_gateways(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            gateways = gateways[:max_results]
        emit(gateways, output, title=f"IKE Gateways in {location_type} '{location_value}'")
        return gateways


# =============================================================================================================================================================================================
# SECURITY ZONE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("zone")
@handle_command_errors("backing up security zones")
def backup_security_zone(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: str = BACKUP_FILE_OPTION,
):
    """Back up all security zones from a container to a YAML file.

    Examples
    --------
        # Backup from folder
        scm backup network zone --folder Austin

        # Backup from snippet
        scm backup network zone --snippet DNS-Best-Practice

        # Backup from device
        scm backup network zone --device austin-01

        # Backup to custom filename
        scm backup network zone --folder Austin --file my-zones.yaml

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Set the default filename if not provided
    if not file:
        file = get_default_backup_filename("security-zones", location_type, location_value)

    # List all security zones with exact_match=True
    zones = scm_client.list_security_zones(folder=folder, snippet=snippet, device=device, exact_match=True)

    if not zones:
        info(f"No security zones found in {location_type} '{location_value}'")
        return None

    # Convert SDK models to dictionaries, excluding unset values
    backup_data = []
    for zone in zones:
        # The list method already returns dicts with exclude_unset=True
        zone_dict = zone.copy()
        # Remove system fields that shouldn't be in the backup
        zone_dict.pop("id", None)

        backup_data.append(zone_dict)

    # Create the YAML structure
    yaml_data = {"security_zones": backup_data}

    # Write to YAML file
    with open(file, "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(backup_data)} security zones to {file}")
    return file


@delete_app.command("zone")
@handle_command_errors("deleting security zone")
def delete_zone(
    name: str = typer.Argument(..., help="Name of the security zone to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a security zone.

    Example: scm delete network zone trust --folder Texas
    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    if not force:
        typer.confirm(f"Delete zone '{name}' from {location_type} '{location_value}'?", abort=True)
    # Call the SDK client to delete the zone
    result = scm_client.delete_zone(folder=folder, snippet=snippet, device=device, name=name)

    if result:
        success(f"Deleted zone: {name} from {location_type} {location_value}")
    else:
        error(f"Zone not found: {name} in {location_type} {location_value}")
        raise typer.Exit(code=1)


@load_app.command("zone")
@handle_command_errors("loading security zones")
def load_security_zone(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load security zones from a YAML file.

    Example: scm load network zone --file security-zone-austin.yaml
    """
    # Load and parse the YAML file
    config = load_from_yaml(str(file), "security_zones")

    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        typer.echo(yaml.dump(config["security_zones"]))
        return None

    def _apply(zone_data: dict):
        # Validate using the Pydantic model
        zone = Zone(**zone_data)

        # Convert to the SDK model and create the zone
        sdk_data = zone.to_sdk_model()
        result = scm_client.create_zone(
            folder=zone.folder,
            snippet=zone.snippet,
            device=zone.device,
            name=sdk_data["name"],
            mode=sdk_data["mode"],
            interfaces=sdk_data["interfaces"],
        )
        return zone, result

    # Apply each zone
    results = []
    for _item, outcome, exc in run_bulk(config["security_zones"], _apply):
        if exc is not None:
            raise exc  # abort on first error, matching the previous sequential behavior

        zone, result = outcome
        results.append(result)
        container = zone.folder or zone.snippet or zone.device
        success(f"Applied zone: {result['name']} in {container}")

    return results


@set_app.command("zone")
@handle_command_errors("creating security zone")
def set_zone(
    name: str = typer.Argument(..., help="Name of the security zone"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    mode: str = MODE_OPTION,
    interfaces: list[str] | None = INTERFACES_OPTION,
    enable_user_id: bool | None = ENABLE_USER_ID_OPTION,
):
    """Create or update a security zone.

    Example:
    -------
        scm set network zone trust --folder Texas --mode layer3 \
        --interfaces ["ethernet1/1"] --enable-user-id

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    # Validate mode parameter
    valid_modes = ["layer3", "layer2", "virtual-wire", "tap", "external", "tunnel"]
    if mode not in valid_modes:
        error(f"Error: Invalid mode '{mode}'. Must be one of: {', '.join(valid_modes)}")
        raise typer.Exit(code=1)

    # Build network configuration based on mode
    network_config = {}
    if mode == "layer3":
        network_config["layer3"] = interfaces or []
    elif mode == "layer2":
        network_config["layer2"] = interfaces or []
    elif mode == "virtual-wire":
        network_config["virtual_wire"] = interfaces or []
    elif mode == "tap":
        network_config["tap"] = interfaces or []
    elif mode == "external":
        network_config["external"] = interfaces or []
    elif mode == "tunnel":
        network_config["tunnel"] = interfaces or []

    zone = Zone(
        name=name,
        folder=folder,
        network=network_config,
        description=None,
        tags=None,
        snippet=snippet,
        device=device,
        enable_user_identification=enable_user_id,
        enable_device_identification=None,
    )

    # Call the SDK client
    # Convert to the SDK model
    sdk_model = zone.to_sdk_model()

    result = scm_client.create_zone(
        folder=zone.folder,
        snippet=zone.snippet,
        device=zone.device,
        name=zone.name,
        mode=sdk_model["mode"],
        interfaces=sdk_model["interfaces"],
        enable_user_identification=sdk_model.get("enable_user_identification"),
        enable_device_identification=sdk_model.get("enable_device_identification"),
    )

    action = result.get("__action__", "created")
    if action == "created":
        success(f"Created zone: {result['name']} in {location_type} {location_value}")
    elif action == "updated":
        success(f"Updated zone: {result['name']} in {location_type} {location_value}")
    elif action == "no_change":
        info(f"No changes needed for zone: {result['name']} in {location_type} {location_value}")
    return result


@show_app.command("zone")
@handle_command_errors("showing security zone")
def show_zone(
    name: str | None = typer.Argument(None, help="Name of the security zone to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
):
    """Display security zones.

    Example:
    -------
        # List all security zones in a folder (default behavior)
        scm show network zone --folder Texas

        # Show a specific security zone by name
        scm show network zone trust --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        zone = scm_client.get_security_zone(folder=folder, snippet=snippet, device=device, name=name)
        emit(zone, output, title=f"Security Zone: {name}")
        return zone
    else:
        zones = scm_client.list_security_zones(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            zones = zones[:max_results]
        emit(zones, output, title=f"Security Zones in {location_type} '{location_value}'")
        return zones


# =============================================================================================================================================================================================
# IPSEC CRYPTO PROFILE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("ipsec-crypto-profile")
@handle_command_errors("backing up IPsec crypto profiles")
def backup_ipsec_crypto_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: str = BACKUP_FILE_OPTION,
):
    """Back up all IPsec crypto profiles from a container to a YAML file.

    Examples
    --------
        # Backup from folder
        scm backup network ipsec-crypto-profile --folder Texas

        # Backup to custom filename
        scm backup network ipsec-crypto-profile --folder Texas --file my-profiles.yaml

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    if not file:
        file = get_default_backup_filename("ipsec-crypto-profiles", location_type, location_value)

    profiles = scm_client.list_ipsec_crypto_profiles(folder=folder, snippet=snippet, device=device, exact_match=True)

    if not profiles:
        info(f"No IPsec crypto profiles found in {location_type} '{location_value}'")
        return None

    backup_data = []
    for profile in profiles:
        profile_dict = profile.copy()
        profile_dict.pop("id", None)
        backup_data.append(profile_dict)

    yaml_data = {"ipsec_crypto_profiles": backup_data}

    with open(file, "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(backup_data)} IPsec crypto profiles to {file}")
    return file


@delete_app.command("ipsec-crypto-profile")
@handle_command_errors("deleting IPsec crypto profile")
def delete_ipsec_crypto_profile(
    name: str = typer.Argument(..., help="Name of the IPsec crypto profile to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete an IPsec crypto profile.

    Example: scm delete network ipsec-crypto-profile my-profile --folder Texas
    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    if not force:
        typer.confirm(f"Delete IPsec crypto profile '{name}' from {location_type} '{location_value}'?", abort=True)
    result = scm_client.delete_ipsec_crypto_profile(folder=folder, snippet=snippet, device=device, name=name)

    if result:
        success(f"Deleted IPsec crypto profile: {name} from {location_type} {location_value}")
    else:
        error(f"IPsec crypto profile not found: {name} in {location_type} {location_value}")
        raise typer.Exit(code=1)


@load_app.command("ipsec-crypto-profile")
@handle_command_errors("loading IPsec crypto profiles")
def load_ipsec_crypto_profile(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load IPsec crypto profiles from a YAML file.

    Example: scm load network ipsec-crypto-profile --file ipsec-profiles.yaml
    """
    config = load_from_yaml(str(file), "ipsec_crypto_profiles")

    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        typer.echo(yaml.dump(config["ipsec_crypto_profiles"]))
        return None

    def _apply(profile_data: dict):
        profile = IPSecCryptoProfile(**profile_data)
        sdk_data = profile.to_sdk_model()

        return scm_client.create_ipsec_crypto_profile(
            folder=profile.folder,
            snippet=profile.snippet,
            device=profile.device,
            name=sdk_data["name"],
            esp_encryption=sdk_data["esp"]["encryption"],
            esp_authentication=sdk_data["esp"]["authentication"],
            dh_group=sdk_data.get("dh_group", "group14"),
            lifetime=sdk_data.get("lifetime"),
            lifesize=sdk_data.get("lifesize"),
        )

    results = []
    for _item, result, exc in run_bulk(config["ipsec_crypto_profiles"], _apply):
        if exc is not None:
            raise exc  # abort on first error, matching the previous sequential behavior

        results.append(result)
        action = result.get("__action__", "applied")
        success(f"IPsec crypto profile '{result['name']}' {action} in folder {result.get('folder', 'N/A')}")

    return results


@set_app.command("ipsec-crypto-profile")
@handle_command_errors("creating IPsec crypto profile")
def set_ipsec_crypto_profile(
    name: str = typer.Argument(..., help="Name of the IPsec crypto profile"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    esp_encryption: list[str] = IPSEC_ESP_ENCRYPTION_OPTION,
    esp_authentication: list[str] = IPSEC_ESP_AUTHENTICATION_OPTION,
    dh_group: str = IPSEC_DH_GROUP_OPTION,
    lifetime_seconds: int | None = IPSEC_LIFETIME_SECONDS_OPTION,
    lifetime_hours: int | None = IPSEC_LIFETIME_HOURS_OPTION,
):
    """Create or update an IPsec crypto profile.

    Example:
    -------
        scm set network ipsec-crypto-profile my-profile --folder Texas \
        --esp-encryption aes-256-cbc --esp-authentication sha256 --dh-group group14

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    profile = IPSecCryptoProfile(
        folder=folder,
        snippet=snippet,
        device=device,
        name=name,
        esp_encryption=esp_encryption,
        esp_authentication=esp_authentication,
        dh_group=dh_group,
        lifetime_seconds=lifetime_seconds,
        lifetime_minutes=None,
        lifetime_hours=lifetime_hours,
        lifetime_days=None,
        lifesize_kb=None,
        lifesize_mb=None,
        lifesize_gb=None,
        lifesize_tb=None,
    )

    sdk_data = profile.to_sdk_model()

    result = scm_client.create_ipsec_crypto_profile(
        folder=folder,
        snippet=snippet,
        device=device,
        name=name,
        esp_encryption=sdk_data["esp"]["encryption"],
        esp_authentication=sdk_data["esp"]["authentication"],
        dh_group=sdk_data.get("dh_group", "group14"),
        lifetime=sdk_data.get("lifetime"),
        lifesize=sdk_data.get("lifesize"),
    )

    action = result.get("__action__", "created")
    if action == "created":
        success(f"Created IPsec crypto profile: {result['name']} in {location_type} {location_value}")
    elif action == "updated":
        success(f"Updated IPsec crypto profile: {result['name']} in {location_type} {location_value}")
    elif action == "no_change":
        info(f"No changes needed for IPsec crypto profile: {result['name']} in {location_type} {location_value}")
    return result


@show_app.command("ipsec-crypto-profile")
@handle_command_errors("showing IPsec crypto profile")
def show_ipsec_crypto_profile(
    name: str | None = typer.Argument(None, help="Name of the IPsec crypto profile to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
):
    """Display IPsec crypto profiles.

    Example:
    -------
        # List all IPsec crypto profiles in a folder
        scm show network ipsec-crypto-profile --folder Texas

        # Show a specific IPsec crypto profile
        scm show network ipsec-crypto-profile my-profile --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        profile = scm_client.get_ipsec_crypto_profile(folder=folder, snippet=snippet, device=device, name=name)
        emit(profile, output, title=f"IPsec Crypto Profile: {name}")
        return profile
    else:
        profiles = scm_client.list_ipsec_crypto_profiles(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            profiles = profiles[:max_results]
        emit(profiles, output, title=f"IPsec Crypto Profiles in {location_type} '{location_value}'")
        return profiles


# =============================================================================================================================================================================================
# NAT RULE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("nat-rule")
@handle_command_errors("backing up NAT rules")
def backup_nat_rule(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: str = BACKUP_FILE_OPTION,
):
    """Back up all NAT rules from a container to a YAML file.

    Examples
    --------
        # Backup from folder
        scm backup network nat-rule --folder Texas

        # Backup to custom filename
        scm backup network nat-rule --folder Texas --file my-nat-rules.yaml

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    if not file:
        file = get_default_backup_filename("nat-rules", location_type, location_value)

    nat_rules = scm_client.list_nat_rules(folder=folder, snippet=snippet, device=device, exact_match=True)

    if not nat_rules:
        info(f"No NAT rules found in {location_type} '{location_value}'")
        return None

    backup_data = []
    for rule in nat_rules:
        rule_dict = rule.copy()
        rule_dict.pop("id", None)
        backup_data.append(rule_dict)

    yaml_data = {"nat_rules": backup_data}

    with open(file, "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(backup_data)} NAT rules to {file}")
    return file


@delete_app.command("nat-rule")
@handle_command_errors("deleting NAT rule")
def delete_nat_rule(
    name: str = typer.Argument(..., help="Name of the NAT rule to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a NAT rule.

    Example: scm delete network nat-rule outbound-nat --folder Texas
    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    if not force:
        typer.confirm(f"Delete NAT rule '{name}' from {location_type} '{location_value}'?", abort=True)
    result = scm_client.delete_nat_rule(folder=folder, snippet=snippet, device=device, name=name)

    if result:
        success(f"Deleted NAT rule: {name} from {location_type} {location_value}")
    else:
        error(f"NAT rule not found: {name} in {location_type} {location_value}")
        raise typer.Exit(code=1)


@load_app.command("nat-rule")
@handle_command_errors("loading NAT rules")
def load_nat_rule(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load NAT rules from a YAML file.

    Example: scm load network nat-rule --file nat-rules.yaml
    """
    # Validate container override parameters
    if sum(1 for x in [folder, snippet, device] if x is not None) > 1:
        error("Error: Only one of --folder, --snippet, or --device can be specified")
        raise typer.Exit(code=1)

    if not file.exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)

    with open(file) as f:
        raw_data = yaml.safe_load(f)

    if not raw_data or "nat_rules" not in raw_data:
        error("No NAT rules found in file")
        raise typer.Exit(code=1)

    nat_rules = raw_data["nat_rules"]
    if not isinstance(nat_rules, list):
        nat_rules = [nat_rules]

    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        if folder or snippet or device:
            override_type = "folder" if folder else ("snippet" if snippet else "device")
            override_value = folder or snippet or device
            info(f"Container override: {override_type} = '{override_value}'")
        typer.echo(yaml.dump(nat_rules))
        return None

    results: list[dict[str, Any]] = []
    created_count = 0
    updated_count = 0
    no_change_count = 0

    # sequential: rule order matters
    for rule_data in nat_rules:
        try:
            # Apply container override
            if folder:
                rule_data["folder"] = folder
                rule_data.pop("snippet", None)
                rule_data.pop("device", None)
            elif snippet:
                rule_data["snippet"] = snippet
                rule_data.pop("folder", None)
                rule_data.pop("device", None)
            elif device:
                rule_data["device"] = device
                rule_data.pop("folder", None)
                rule_data.pop("snippet", None)

            nat_rule = NATRule(**rule_data)
            sdk_data = nat_rule.to_sdk_model()

            result = scm_client.create_nat_rule(
                folder=nat_rule.folder,
                snippet=nat_rule.snippet,
                device=nat_rule.device,
                name=nat_rule.name,
                description=nat_rule.description,
                tag=nat_rule.tag,
                disabled=nat_rule.disabled,
                nat_type=nat_rule.nat_type,
                from_zones=sdk_data.get("from_"),
                to_zones=sdk_data.get("to_"),
                to_interface=nat_rule.to_interface,
                source=sdk_data.get("source"),
                destination=sdk_data.get("destination"),
                service=nat_rule.service,
                source_translation=nat_rule.source_translation,
                destination_translation=nat_rule.destination_translation,
                active_active_device_binding=nat_rule.active_active_device_binding,
            )

            action = result.pop("__action__", "created")
            results.append(result)

            if action == "created":
                created_count += 1
            elif action == "updated":
                updated_count += 1
            else:
                no_change_count += 1

        except Exception as e:
            error(f"Error processing NAT rule '{rule_data.get('name', 'unknown')}': {str(e)}")
            continue

    success(f"Successfully processed {len(results)} NAT rule(s):")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")
    if no_change_count > 0:
        info(f"  - No change: {no_change_count}")

    return results


@set_app.command("nat-rule")
@handle_command_errors("creating NAT rule")
def set_nat_rule(
    name: str = typer.Argument(..., help="Name of the NAT rule"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    description: str | None = NAT_DESCRIPTION_OPTION,
    tags: list[str] | None = NAT_TAGS_OPTION,
    disabled: bool = NAT_DISABLED_OPTION,
    nat_type: str = NAT_NAT_TYPE_OPTION,
    from_zone: list[str] | None = NAT_FROM_ZONES_OPTION,
    to_zone: list[str] | None = NAT_TO_ZONES_OPTION,
    to_interface: str | None = NAT_TO_INTERFACE_OPTION,
    source: list[str] | None = NAT_SOURCE_OPTION,
    destination: list[str] | None = NAT_DESTINATION_OPTION,
    service: str = NAT_SERVICE_OPTION,
    source_translation: str | None = NAT_SOURCE_TRANSLATION_OPTION,
    destination_translation: str | None = NAT_DESTINATION_TRANSLATION_OPTION,
):
    r"""Create or update a NAT rule.

    Example:
    -------
        scm set network nat-rule outbound-nat --folder Texas \
        --from-zone trust --to-zone untrust --source any --destination any \
        --source-translation '{"dynamic_ip_and_port": {"type": "dynamic_ip_and_port", "translated_address": ["10.0.0.1"]}}'

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    # Parse JSON strings for translation configs
    src_translation = json.loads(source_translation) if source_translation else None
    dst_translation = json.loads(destination_translation) if destination_translation else None

    result = scm_client.create_nat_rule(
        folder=folder,
        snippet=snippet,
        device=device,
        name=name,
        description=description,
        tag=tags,
        disabled=disabled,
        nat_type=nat_type,
        from_zones=from_zone or ["any"],
        to_zones=to_zone or ["any"],
        to_interface=to_interface,
        source=source or ["any"],
        destination=destination or ["any"],
        service=service,
        source_translation=src_translation,
        destination_translation=dst_translation,
    )

    action = result.pop("__action__", "created")

    if action == "created":
        success(f"Created NAT rule: {result['name']} in {location_type} {location_value}")
    elif action == "updated":
        success(f"Updated NAT rule: {result['name']} in {location_type} {location_value}")
    elif action == "no_change":
        info(f"No changes needed for NAT rule: {result['name']} in {location_type} {location_value}")

    return result


@show_app.command("nat-rule")
@handle_command_errors("showing NAT rule")
def show_nat_rule(
    name: str | None = typer.Argument(None, help="Name of the NAT rule to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
):
    """Display NAT rules.

    Example:
    -------
        # List all NAT rules in a folder
        scm show network nat-rule --folder Texas

        # Show a specific NAT rule by name
        scm show network nat-rule outbound-nat --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        rule = scm_client.get_nat_rule(folder=folder, snippet=snippet, device=device, name=name)
        emit(rule, output, title=f"NAT Rule: {name}")
        return rule
    else:
        rules = scm_client.list_nat_rules(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            rules = rules[:max_results]
        emit(rules, output, title=f"NAT Rules in {location_type} '{location_value}'")
        return rules


# =============================================================================================================================================================================================
# DHCP INTERFACE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("dhcp-interface", help="Export DHCP interfaces to a YAML file.")
@handle_command_errors("backing up DHCP interfaces")
def backup_dhcp_interface(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export DHCP interfaces from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving DHCP interfaces from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    interfaces = scm_client.list_dhcp_interfaces(**kwargs)
    if not interfaces:
        info(f"No DHCP interfaces found in {location_type} '{location_value}'")
        return
    export_data = {"dhcp_interfaces": interfaces}
    filename = Path(file or get_default_backup_filename("dhcp-interface", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(interfaces)} DHCP interfaces to {filename}")


@delete_app.command("dhcp-interface", help="Delete a DHCP interface.")
@handle_command_errors("deleting DHCP interface")
def delete_dhcp_interface(
    name: str = typer.Argument(..., help="Name of the DHCP interface to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a DHCP interface.

    Examples
    --------
        scm delete network dhcp-interface eth0 --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    iface = scm_client.get_dhcp_interface(name=name, folder=folder, snippet=snippet, device=device)
    if not iface:
        error(f"DHCP interface '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete DHCP interface '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_dhcp_interface(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted DHCP interface: {name} from {location_value}")


@load_app.command("dhcp-interface", help="Load DHCP interfaces from a YAML file.")
@handle_command_errors("loading DHCP interfaces")
def load_dhcp_interface(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load DHCP interfaces from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "dhcp_interfaces" not in data:
        error("No DHCP interfaces found in file")
        raise typer.Exit(code=1)
    interfaces = data["dhcp_interfaces"]
    if not isinstance(interfaces, list):
        interfaces = [interfaces]
    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        if folder or snippet or device:
            override_type = "folder" if folder else ("snippet" if snippet else "device")
            override_value = folder or snippet or device
            info(f"Container override: {override_type} = '{override_value}'")
        typer.echo(yaml.dump(interfaces))
        return None
    created_count = 0
    updated_count = 0
    no_change_count = 0

    def _apply(iface_data: dict):
        if folder:
            iface_data["folder"] = folder
            iface_data.pop("snippet", None)
            iface_data.pop("device", None)
        elif snippet:
            iface_data["snippet"] = snippet
            iface_data.pop("folder", None)
            iface_data.pop("device", None)
        elif device:
            iface_data["device"] = device
            iface_data.pop("folder", None)
            iface_data.pop("snippet", None)
        validated_iface = DhcpInterface(**iface_data)
        sdk_data = validated_iface.to_sdk_model()
        result = scm_client.create_dhcp_interface(sdk_data)
        return validated_iface, result

    for _item, outcome, exc in run_bulk(interfaces, _apply):
        if exc is not None:
            error(f"Error processing DHCP interface: {str(exc)}")
            continue
        validated_iface, result = outcome
        action = result.pop("__action__", "created")
        container = validated_iface.folder or validated_iface.snippet or validated_iface.device
        if action == "created":
            created_count += 1
            success(f"Created DHCP interface: {validated_iface.name} in {container}")
        elif action == "updated":
            updated_count += 1
            success(f"Updated DHCP interface: {validated_iface.name} in {container}")
        else:
            no_change_count += 1
            info(f"No changes needed for DHCP interface: {validated_iface.name} in {container}")
    info(f"\nSummary: Processed {created_count + updated_count + no_change_count} DHCP interfaces")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")
    if no_change_count > 0:
        info(f"  - No change: {no_change_count}")


@set_app.command("dhcp-interface", help="Create or update a DHCP interface.")
@handle_command_errors("creating/updating DHCP interface")
def set_dhcp_interface(
    name: str = typer.Argument(..., help="Name of the DHCP interface"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    server_json: str = typer.Option(None, "--server-json", help="DHCP server config as JSON"),
    relay_json: str = typer.Option(None, "--relay-json", help="DHCP relay config as JSON"),
) -> None:
    """Create or update a DHCP interface."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    iface_data: dict[str, Any] = {"name": name, location_type: location_value}
    if server_json:
        iface_data["server"] = json.loads(server_json)
    if relay_json:
        iface_data["relay"] = json.loads(relay_json)
    validated_iface = DhcpInterface(**iface_data)
    sdk_data = validated_iface.to_sdk_model()
    result = scm_client.create_dhcp_interface(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created DHCP interface: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated DHCP interface: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for DHCP interface: {name} in {location_value}")


@show_app.command("dhcp-interface", help="Show DHCP interface details.")
@handle_command_errors("showing DHCP interface")
def show_dhcp_interface(
    name: str | None = typer.Argument(None, help="Name of the DHCP interface to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show DHCP interface details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        iface = scm_client.get_dhcp_interface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            error(f"DHCP interface '{name}' not found")
            raise typer.Exit(code=1)
        emit(iface, output, title=f"DHCP Interface: {name}")
        return iface
    else:
        interfaces = scm_client.list_dhcp_interfaces(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            interfaces = interfaces[:max_results]
        emit(interfaces, output, title=f"DHCP Interfaces in {location_type} '{location_value}'")
        return interfaces


# =============================================================================================================================================================================================
# ETHERNET INTERFACE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("ethernet-interface", help="Export ethernet interfaces to a YAML file.")
@handle_command_errors("backing up ethernet interfaces")
def backup_ethernet_interface(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export ethernet interfaces from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving ethernet interfaces from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    interfaces = scm_client.list_ethernet_interfaces(**kwargs)
    if not interfaces:
        info(f"No ethernet interfaces found in {location_type} '{location_value}'")
        return
    export_data = {"ethernet_interfaces": interfaces}
    filename = Path(file or get_default_backup_filename("ethernet-interface", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(interfaces)} ethernet interfaces to {filename}")


@delete_app.command("ethernet-interface", help="Delete an ethernet interface.")
@handle_command_errors("deleting ethernet interface")
def delete_ethernet_interface(
    name: str = typer.Argument(..., help="Name of the ethernet interface to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete an ethernet interface."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    iface = scm_client.get_ethernet_interface(name=name, folder=folder, snippet=snippet, device=device)
    if not iface:
        error(f"Ethernet interface '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete ethernet interface '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_ethernet_interface(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted ethernet interface: {name} from {location_value}")


@load_app.command("ethernet-interface", help="Load ethernet interfaces from a YAML file.")
@handle_command_errors("loading ethernet interfaces")
def load_ethernet_interface(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load ethernet interfaces from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "ethernet_interfaces" not in data:
        error("No ethernet interfaces found in file")
        raise typer.Exit(code=1)
    interfaces = data["ethernet_interfaces"]
    if not isinstance(interfaces, list):
        interfaces = [interfaces]
    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        if folder or snippet or device:
            override_type = "folder" if folder else ("snippet" if snippet else "device")
            override_value = folder or snippet or device
            info(f"Container override: {override_type} = '{override_value}'")
        typer.echo(yaml.dump(interfaces))
        return None
    created_count = 0
    updated_count = 0
    no_change_count = 0

    def _apply(iface_data: dict):
        if folder:
            iface_data["folder"] = folder
            iface_data.pop("snippet", None)
            iface_data.pop("device", None)
        elif snippet:
            iface_data["snippet"] = snippet
            iface_data.pop("folder", None)
            iface_data.pop("device", None)
        elif device:
            iface_data["device"] = device
            iface_data.pop("folder", None)
            iface_data.pop("snippet", None)
        validated_iface = EthernetInterface(**iface_data)
        sdk_data = validated_iface.to_sdk_model()
        result = scm_client.create_ethernet_interface(sdk_data)
        return validated_iface, result

    for _item, outcome, exc in run_bulk(interfaces, _apply):
        if exc is not None:
            error(f"Error processing ethernet interface: {str(exc)}")
            continue
        validated_iface, result = outcome
        action = result.pop("__action__", "created")
        container = validated_iface.folder or validated_iface.snippet or validated_iface.device
        if action == "created":
            created_count += 1
            success(f"Created ethernet interface: {validated_iface.name} in {container}")
        elif action == "updated":
            updated_count += 1
            success(f"Updated ethernet interface: {validated_iface.name} in {container}")
        else:
            no_change_count += 1
            info(f"No changes needed for ethernet interface: {validated_iface.name} in {container}")
    info(f"\nSummary: Processed {created_count + updated_count + no_change_count} ethernet interfaces")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")
    if no_change_count > 0:
        info(f"  - No change: {no_change_count}")


@set_app.command("ethernet-interface", help="Create or update an ethernet interface.")
@handle_command_errors("creating/updating ethernet interface")
def set_ethernet_interface(
    name: str = typer.Argument(..., help="Name of the ethernet interface"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    comment: str = typer.Option(None, "--comment", help="Interface description/comment"),
    default_value: str = typer.Option(None, "--default-value", help="Physical interface (e.g. ethernet1/1)"),
    link_speed: str = typer.Option(None, "--link-speed", help="Link speed (auto, 10, 100, 1000, 10000)"),
    link_duplex: str = typer.Option(None, "--link-duplex", help="Link duplex (auto, half, full)"),
    link_state: str = typer.Option(None, "--link-state", help="Link state (auto, up, down)"),
    layer2_json: str = typer.Option(None, "--layer2-json", help="Layer2 config as JSON"),
    layer3_json: str = typer.Option(None, "--layer3-json", help="Layer3 config as JSON"),
    tap_json: str = typer.Option(None, "--tap-json", help="TAP config as JSON"),
) -> None:
    """Create or update an ethernet interface."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    iface_data: dict[str, Any] = {"name": name, location_type: location_value}
    if comment:
        iface_data["comment"] = comment
    if default_value:
        iface_data["default_value"] = default_value
    if link_speed:
        iface_data["link_speed"] = link_speed
    if link_duplex:
        iface_data["link_duplex"] = link_duplex
    if link_state:
        iface_data["link_state"] = link_state
    if layer2_json:
        iface_data["layer2"] = json.loads(layer2_json)
    if layer3_json:
        iface_data["layer3"] = json.loads(layer3_json)
    if tap_json:
        iface_data["tap"] = json.loads(tap_json)
    validated_iface = EthernetInterface(**iface_data)
    sdk_data = validated_iface.to_sdk_model()
    result = scm_client.create_ethernet_interface(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created ethernet interface: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated ethernet interface: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for ethernet interface: {name} in {location_value}")


@show_app.command("ethernet-interface", help="Show ethernet interface details.")
@handle_command_errors("showing ethernet interface")
def show_ethernet_interface(
    name: str | None = typer.Argument(None, help="Name of the ethernet interface to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show ethernet interface details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        iface = scm_client.get_ethernet_interface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            error(f"Ethernet interface '{name}' not found")
            raise typer.Exit(code=1)
        emit(iface, output, title=f"Ethernet Interface: {name}")
        return iface
    else:
        interfaces = scm_client.list_ethernet_interfaces(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            interfaces = interfaces[:max_results]
        emit(interfaces, output, title=f"Ethernet Interfaces in {location_type} '{location_value}'")
        return interfaces


# =============================================================================================================================================================================================
# LAYER2 SUBINTERFACE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("layer2-subinterface", help="Export layer2 subinterfaces to a YAML file.")
@handle_command_errors("backing up layer2 subinterfaces")
def backup_layer2_subinterface(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export layer2 subinterfaces from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving layer2 subinterfaces from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    interfaces = scm_client.list_layer2_subinterfaces(**kwargs)
    if not interfaces:
        info(f"No layer2 subinterfaces found in {location_type} '{location_value}'")
        return
    export_data = {"layer2_subinterfaces": interfaces}
    filename = Path(file or get_default_backup_filename("layer2-subinterface", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(interfaces)} layer2 subinterfaces to {filename}")


@delete_app.command("layer2-subinterface", help="Delete a layer2 subinterface.")
@handle_command_errors("deleting layer2 subinterface")
def delete_layer2_subinterface(
    name: str = typer.Argument(..., help="Name of the layer2 subinterface to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a layer2 subinterface.

    Examples
    --------
        scm delete network layer2-subinterface ethernet1/1.100 --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    iface = scm_client.get_layer2_subinterface(name=name, folder=folder, snippet=snippet, device=device)
    if not iface:
        error(f"Layer2 subinterface '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete layer2 subinterface '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_layer2_subinterface(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted layer2 subinterface: {name} from {location_value}")


@load_app.command("layer2-subinterface", help="Load layer2 subinterfaces from a YAML file.")
@handle_command_errors("loading layer2 subinterfaces")
def load_layer2_subinterface(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load layer2 subinterfaces from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "layer2_subinterfaces" not in data:
        error("No layer2 subinterfaces found in file")
        raise typer.Exit(code=1)
    interfaces = data["layer2_subinterfaces"]
    if not isinstance(interfaces, list):
        interfaces = [interfaces]
    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        if folder or snippet or device:
            override_type = "folder" if folder else ("snippet" if snippet else "device")
            override_value = folder or snippet or device
            info(f"Container override: {override_type} = '{override_value}'")
        typer.echo(yaml.dump(interfaces))
        return None
    created_count = 0
    updated_count = 0
    no_change_count = 0

    def _apply(iface_data: dict):
        if folder:
            iface_data["folder"] = folder
            iface_data.pop("snippet", None)
            iface_data.pop("device", None)
        elif snippet:
            iface_data["snippet"] = snippet
            iface_data.pop("folder", None)
            iface_data.pop("device", None)
        elif device:
            iface_data["device"] = device
            iface_data.pop("folder", None)
            iface_data.pop("snippet", None)
        validated_iface = Layer2Subinterface(**iface_data)
        sdk_data = validated_iface.to_sdk_model()
        result = scm_client.create_layer2_subinterface(sdk_data)
        return validated_iface, result

    for _item, outcome, exc in run_bulk(interfaces, _apply):
        if exc is not None:
            error(f"Error processing layer2 subinterface: {str(exc)}")
            continue
        validated_iface, result = outcome
        action = result.pop("__action__", "created")
        container = validated_iface.folder or validated_iface.snippet or validated_iface.device
        if action == "created":
            created_count += 1
            success(f"Created layer2 subinterface: {validated_iface.name} in {container}")
        elif action == "updated":
            updated_count += 1
            success(f"Updated layer2 subinterface: {validated_iface.name} in {container}")
        else:
            no_change_count += 1
            info(f"No changes needed for layer2 subinterface: {validated_iface.name} in {container}")
    info(f"\nSummary: Processed {created_count + updated_count + no_change_count} layer2 subinterfaces")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")
    if no_change_count > 0:
        info(f"  - No change: {no_change_count}")


@set_app.command("layer2-subinterface", help="Create or update a layer2 subinterface.")
@handle_command_errors("creating/updating layer2 subinterface")
def set_layer2_subinterface(
    name: str = typer.Argument(..., help="Name of the layer2 subinterface"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    vlan_tag: str = typer.Option(..., "--vlan-tag", help="VLAN tag (1-4096)"),
    parent_interface: str = typer.Option(None, "--parent-interface", help="Parent interface name"),
    comment: str = typer.Option(None, "--comment", help="Interface description/comment"),
) -> None:
    """Create or update a layer2 subinterface."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    iface_data: dict[str, Any] = {"name": name, "vlan_tag": vlan_tag, location_type: location_value}
    if parent_interface:
        iface_data["parent_interface"] = parent_interface
    if comment:
        iface_data["comment"] = comment
    validated_iface = Layer2Subinterface(**iface_data)
    sdk_data = validated_iface.to_sdk_model()
    result = scm_client.create_layer2_subinterface(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created layer2 subinterface: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated layer2 subinterface: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for layer2 subinterface: {name} in {location_value}")


@show_app.command("layer2-subinterface", help="Show layer2 subinterface details.")
@handle_command_errors("showing layer2 subinterface")
def show_layer2_subinterface(
    name: str | None = typer.Argument(None, help="Name of the layer2 subinterface to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show layer2 subinterface details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        iface = scm_client.get_layer2_subinterface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            error(f"Layer2 subinterface '{name}' not found")
            raise typer.Exit(code=1)
        emit(iface, output, title=f"Layer2 Subinterface: {name}")
        return iface
    else:
        interfaces = scm_client.list_layer2_subinterfaces(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            interfaces = interfaces[:max_results]
        emit(interfaces, output, title=f"Layer2 Subinterfaces in {location_type} '{location_value}'")
        return interfaces


# =============================================================================================================================================================================================
# LAYER3 SUBINTERFACE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("layer3-subinterface", help="Export layer3 subinterfaces to a YAML file.")
@handle_command_errors("backing up layer3 subinterfaces")
def backup_layer3_subinterface(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export layer3 subinterfaces from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving layer3 subinterfaces from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    interfaces = scm_client.list_layer3_subinterfaces(**kwargs)
    if not interfaces:
        info(f"No layer3 subinterfaces found in {location_type} '{location_value}'")
        return
    export_data = {"layer3_subinterfaces": interfaces}
    filename = Path(file or get_default_backup_filename("layer3-subinterface", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(interfaces)} layer3 subinterfaces to {filename}")


@delete_app.command("layer3-subinterface", help="Delete a layer3 subinterface.")
@handle_command_errors("deleting layer3 subinterface")
def delete_layer3_subinterface(
    name: str = typer.Argument(..., help="Name of the layer3 subinterface to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a layer3 subinterface.

    Examples
    --------
        scm delete network layer3-subinterface ethernet1/1.200 --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    iface = scm_client.get_layer3_subinterface(name=name, folder=folder, snippet=snippet, device=device)
    if not iface:
        error(f"Layer3 subinterface '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete layer3 subinterface '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_layer3_subinterface(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted layer3 subinterface: {name} from {location_value}")


@load_app.command("layer3-subinterface", help="Load layer3 subinterfaces from a YAML file.")
@handle_command_errors("loading layer3 subinterfaces")
def load_layer3_subinterface(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load layer3 subinterfaces from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "layer3_subinterfaces" not in data:
        error("No layer3 subinterfaces found in file")
        raise typer.Exit(code=1)
    interfaces = data["layer3_subinterfaces"]
    if not isinstance(interfaces, list):
        interfaces = [interfaces]
    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        if folder or snippet or device:
            override_type = "folder" if folder else ("snippet" if snippet else "device")
            override_value = folder or snippet or device
            info(f"Container override: {override_type} = '{override_value}'")
        typer.echo(yaml.dump(interfaces))
        return None
    created_count = 0
    updated_count = 0
    no_change_count = 0

    def _apply(iface_data: dict):
        if folder:
            iface_data["folder"] = folder
            iface_data.pop("snippet", None)
            iface_data.pop("device", None)
        elif snippet:
            iface_data["snippet"] = snippet
            iface_data.pop("folder", None)
            iface_data.pop("device", None)
        elif device:
            iface_data["device"] = device
            iface_data.pop("folder", None)
            iface_data.pop("snippet", None)
        validated_iface = Layer3Subinterface(**iface_data)
        sdk_data = validated_iface.to_sdk_model()
        result = scm_client.create_layer3_subinterface(sdk_data)
        return validated_iface, result

    for _item, outcome, exc in run_bulk(interfaces, _apply):
        if exc is not None:
            error(f"Error processing layer3 subinterface: {str(exc)}")
            continue
        validated_iface, result = outcome
        action = result.pop("__action__", "created")
        container = validated_iface.folder or validated_iface.snippet or validated_iface.device
        if action == "created":
            created_count += 1
            success(f"Created layer3 subinterface: {validated_iface.name} in {container}")
        elif action == "updated":
            updated_count += 1
            success(f"Updated layer3 subinterface: {validated_iface.name} in {container}")
        else:
            no_change_count += 1
            info(f"No changes needed for layer3 subinterface: {validated_iface.name} in {container}")
    info(f"\nSummary: Processed {created_count + updated_count + no_change_count} layer3 subinterfaces")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")
    if no_change_count > 0:
        info(f"  - No change: {no_change_count}")


@set_app.command("layer3-subinterface", help="Create or update a layer3 subinterface.")
@handle_command_errors("creating/updating layer3 subinterface")
def set_layer3_subinterface(
    name: str = typer.Argument(..., help="Name of the layer3 subinterface"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    vlan_tag: int = typer.Option(None, "--vlan-tag", help="VLAN tag (1-4096)"),
    parent_interface: str = typer.Option(None, "--parent-interface", help="Parent interface name"),
    comment: str = typer.Option(None, "--comment", help="Interface description/comment"),
    mtu: int = typer.Option(None, "--mtu", help="MTU (576-9216)"),
    ip_json: str = typer.Option(None, "--ip-json", help='Static IPs as JSON (e.g. \'[{"name": "10.0.0.1/24"}]\')'),
    dhcp_client_json: str = typer.Option(None, "--dhcp-client-json", help="DHCP client config as JSON"),
) -> None:
    """Create or update a layer3 subinterface."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    iface_data: dict[str, Any] = {"name": name, location_type: location_value}
    if vlan_tag is not None:
        iface_data["tag"] = vlan_tag
    if parent_interface:
        iface_data["parent_interface"] = parent_interface
    if comment:
        iface_data["comment"] = comment
    if mtu is not None:
        iface_data["mtu"] = mtu
    if ip_json:
        iface_data["ip"] = json.loads(ip_json)
    if dhcp_client_json:
        iface_data["dhcp_client"] = json.loads(dhcp_client_json)
    validated_iface = Layer3Subinterface(**iface_data)
    sdk_data = validated_iface.to_sdk_model()
    result = scm_client.create_layer3_subinterface(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created layer3 subinterface: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated layer3 subinterface: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for layer3 subinterface: {name} in {location_value}")


@show_app.command("layer3-subinterface", help="Show layer3 subinterface details.")
@handle_command_errors("showing layer3 subinterface")
def show_layer3_subinterface(
    name: str | None = typer.Argument(None, help="Name of the layer3 subinterface to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show layer3 subinterface details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        iface = scm_client.get_layer3_subinterface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            error(f"Layer3 subinterface '{name}' not found")
            raise typer.Exit(code=1)
        emit(iface, output, title=f"Layer3 Subinterface: {name}")
        return iface
    else:
        interfaces = scm_client.list_layer3_subinterfaces(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            interfaces = interfaces[:max_results]
        emit(interfaces, output, title=f"Layer3 Subinterfaces in {location_type} '{location_value}'")
        return interfaces


# =============================================================================================================================================================================================
# LOOPBACK INTERFACE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("loopback-interface", help="Export loopback interfaces to a YAML file.")
@handle_command_errors("backing up loopback interfaces")
def backup_loopback_interface(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export loopback interfaces from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving loopback interfaces from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    interfaces = scm_client.list_loopback_interfaces(**kwargs)
    if not interfaces:
        info(f"No loopback interfaces found in {location_type} '{location_value}'")
        return
    export_data = {"loopback_interfaces": interfaces}
    filename = Path(file or get_default_backup_filename("loopback-interface", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(interfaces)} loopback interfaces to {filename}")


@delete_app.command("loopback-interface", help="Delete a loopback interface.")
@handle_command_errors("deleting loopback interface")
def delete_loopback_interface(
    name: str = typer.Argument(..., help="Name of the loopback interface to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a loopback interface.

    Examples
    --------
        scm delete network loopback-interface loopback.1 --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    iface = scm_client.get_loopback_interface(name=name, folder=folder, snippet=snippet, device=device)
    if not iface:
        error(f"Loopback interface '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete loopback interface '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_loopback_interface(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted loopback interface: {name} from {location_value}")


@load_app.command("loopback-interface", help="Load loopback interfaces from a YAML file.")
@handle_command_errors("loading loopback interfaces")
def load_loopback_interface(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load loopback interfaces from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "loopback_interfaces" not in data:
        error("No loopback interfaces found in file")
        raise typer.Exit(code=1)
    interfaces = data["loopback_interfaces"]
    if not isinstance(interfaces, list):
        interfaces = [interfaces]
    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        if folder or snippet or device:
            override_type = "folder" if folder else ("snippet" if snippet else "device")
            override_value = folder or snippet or device
            info(f"Container override: {override_type} = '{override_value}'")
        typer.echo(yaml.dump(interfaces))
        return None
    created_count = 0
    updated_count = 0
    no_change_count = 0

    def _apply(iface_data: dict):
        if folder:
            iface_data["folder"] = folder
            iface_data.pop("snippet", None)
            iface_data.pop("device", None)
        elif snippet:
            iface_data["snippet"] = snippet
            iface_data.pop("folder", None)
            iface_data.pop("device", None)
        elif device:
            iface_data["device"] = device
            iface_data.pop("folder", None)
            iface_data.pop("snippet", None)
        validated_iface = LoopbackInterface(**iface_data)
        sdk_data = validated_iface.to_sdk_model()
        result = scm_client.create_loopback_interface(sdk_data)
        return validated_iface, result

    for _item, outcome, exc in run_bulk(interfaces, _apply):
        if exc is not None:
            error(f"Error processing loopback interface: {str(exc)}")
            continue
        validated_iface, result = outcome
        action = result.pop("__action__", "created")
        container = validated_iface.folder or validated_iface.snippet or validated_iface.device
        if action == "created":
            created_count += 1
            success(f"Created loopback interface: {validated_iface.name} in {container}")
        elif action == "updated":
            updated_count += 1
            success(f"Updated loopback interface: {validated_iface.name} in {container}")
        else:
            no_change_count += 1
            info(f"No changes needed for loopback interface: {validated_iface.name} in {container}")
    info(f"\nSummary: Processed {created_count + updated_count + no_change_count} loopback interfaces")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")
    if no_change_count > 0:
        info(f"  - No change: {no_change_count}")


@set_app.command("loopback-interface", help="Create or update a loopback interface.")
@handle_command_errors("creating/updating loopback interface")
def set_loopback_interface(
    name: str = typer.Argument(..., help="Name of the loopback interface"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    comment: str = typer.Option(None, "--comment", help="Interface description/comment"),
    default_value: str = typer.Option(None, "--default-value", help="Default interface (e.g. loopback.1)"),
    mtu: int = typer.Option(None, "--mtu", help="MTU (576-9216)"),
    ip_json: str = typer.Option(None, "--ip-json", help='Static IPs as JSON (e.g. \'[{"name": "10.0.0.1/32"}]\')'),
    ipv6_json: str = typer.Option(None, "--ipv6-json", help="IPv6 config as JSON"),
) -> None:
    """Create or update a loopback interface."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    iface_data: dict[str, Any] = {"name": name, location_type: location_value}
    if comment:
        iface_data["comment"] = comment
    if default_value:
        iface_data["default_value"] = default_value
    if mtu is not None:
        iface_data["mtu"] = mtu
    if ip_json:
        iface_data["ip"] = json.loads(ip_json)
    if ipv6_json:
        iface_data["ipv6"] = json.loads(ipv6_json)
    validated_iface = LoopbackInterface(**iface_data)
    sdk_data = validated_iface.to_sdk_model()
    result = scm_client.create_loopback_interface(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created loopback interface: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated loopback interface: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for loopback interface: {name} in {location_value}")


@show_app.command("loopback-interface", help="Show loopback interface details.")
@handle_command_errors("showing loopback interface")
def show_loopback_interface(
    name: str | None = typer.Argument(None, help="Name of the loopback interface to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show loopback interface details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        iface = scm_client.get_loopback_interface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            error(f"Loopback interface '{name}' not found")
            raise typer.Exit(code=1)
        emit(iface, output, title=f"Loopback Interface: {name}")
        return iface
    else:
        interfaces = scm_client.list_loopback_interfaces(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            interfaces = interfaces[:max_results]
        emit(interfaces, output, title=f"Loopback Interfaces in {location_type} '{location_value}'")
        return interfaces


# =============================================================================================================================================================================================
# TUNNEL INTERFACE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("tunnel-interface", help="Export tunnel interfaces to a YAML file.")
@handle_command_errors("backing up tunnel interfaces")
def backup_tunnel_interface(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export tunnel interfaces from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving tunnel interfaces from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    interfaces = scm_client.list_tunnel_interfaces(**kwargs)
    if not interfaces:
        info(f"No tunnel interfaces found in {location_type} '{location_value}'")
        return
    export_data = {"tunnel_interfaces": interfaces}
    filename = Path(file or get_default_backup_filename("tunnel-interface", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(interfaces)} tunnel interfaces to {filename}")


@delete_app.command("tunnel-interface", help="Delete a tunnel interface.")
@handle_command_errors("deleting tunnel interface")
def delete_tunnel_interface(
    name: str = typer.Argument(..., help="Name of the tunnel interface to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a tunnel interface.

    Examples
    --------
        scm delete network tunnel-interface tunnel.1 --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    iface = scm_client.get_tunnel_interface(name=name, folder=folder, snippet=snippet, device=device)
    if not iface:
        error(f"Tunnel interface '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete tunnel interface '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_tunnel_interface(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted tunnel interface: {name} from {location_value}")


@load_app.command("tunnel-interface", help="Load tunnel interfaces from a YAML file.")
@handle_command_errors("loading tunnel interfaces")
def load_tunnel_interface(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load tunnel interfaces from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "tunnel_interfaces" not in data:
        error("No tunnel interfaces found in file")
        raise typer.Exit(code=1)
    interfaces = data["tunnel_interfaces"]
    if not isinstance(interfaces, list):
        interfaces = [interfaces]
    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        if folder or snippet or device:
            override_type = "folder" if folder else ("snippet" if snippet else "device")
            override_value = folder or snippet or device
            info(f"Container override: {override_type} = '{override_value}'")
        typer.echo(yaml.dump(interfaces))
        return None
    created_count = 0
    updated_count = 0
    no_change_count = 0

    def _apply(iface_data: dict):
        if folder:
            iface_data["folder"] = folder
            iface_data.pop("snippet", None)
            iface_data.pop("device", None)
        elif snippet:
            iface_data["snippet"] = snippet
            iface_data.pop("folder", None)
            iface_data.pop("device", None)
        elif device:
            iface_data["device"] = device
            iface_data.pop("folder", None)
            iface_data.pop("snippet", None)
        validated_iface = TunnelInterface(**iface_data)
        sdk_data = validated_iface.to_sdk_model()
        result = scm_client.create_tunnel_interface(sdk_data)
        return validated_iface, result

    for _item, outcome, exc in run_bulk(interfaces, _apply):
        if exc is not None:
            error(f"Error processing tunnel interface: {str(exc)}")
            continue
        validated_iface, result = outcome
        action = result.pop("__action__", "created")
        container = validated_iface.folder or validated_iface.snippet or validated_iface.device
        if action == "created":
            created_count += 1
            success(f"Created tunnel interface: {validated_iface.name} in {container}")
        elif action == "updated":
            updated_count += 1
            success(f"Updated tunnel interface: {validated_iface.name} in {container}")
        else:
            no_change_count += 1
            info(f"No changes needed for tunnel interface: {validated_iface.name} in {container}")
    info(f"\nSummary: Processed {created_count + updated_count + no_change_count} tunnel interfaces")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")
    if no_change_count > 0:
        info(f"  - No change: {no_change_count}")


@set_app.command("tunnel-interface", help="Create or update a tunnel interface.")
@handle_command_errors("creating/updating tunnel interface")
def set_tunnel_interface(
    name: str = typer.Argument(..., help="Name of the tunnel interface"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    comment: str = typer.Option(None, "--comment", help="Interface description/comment"),
    default_value: str = typer.Option(None, "--default-value", help="Default interface (e.g. tunnel.1)"),
    mtu: int = typer.Option(None, "--mtu", help="MTU (576-9216)"),
    ip_json: str = typer.Option(None, "--ip-json", help='Static IPs as JSON (e.g. \'[{"name": "10.0.0.1/30"}]\')'),
) -> None:
    """Create or update a tunnel interface."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    iface_data: dict[str, Any] = {"name": name, location_type: location_value}
    if comment:
        iface_data["comment"] = comment
    if default_value:
        iface_data["default_value"] = default_value
    if mtu is not None:
        iface_data["mtu"] = mtu
    if ip_json:
        iface_data["ip"] = json.loads(ip_json)
    validated_iface = TunnelInterface(**iface_data)
    sdk_data = validated_iface.to_sdk_model()
    result = scm_client.create_tunnel_interface(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created tunnel interface: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated tunnel interface: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for tunnel interface: {name} in {location_value}")


@show_app.command("tunnel-interface", help="Show tunnel interface details.")
@handle_command_errors("showing tunnel interface")
def show_tunnel_interface(
    name: str | None = typer.Argument(None, help="Name of the tunnel interface to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show tunnel interface details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        iface = scm_client.get_tunnel_interface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            error(f"Tunnel interface '{name}' not found")
            raise typer.Exit(code=1)
        emit(iface, output, title=f"Tunnel Interface: {name}")
        return iface
    else:
        interfaces = scm_client.list_tunnel_interfaces(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            interfaces = interfaces[:max_results]
        emit(interfaces, output, title=f"Tunnel Interfaces in {location_type} '{location_value}'")
        return interfaces


# =============================================================================================================================================================================================
# VLAN INTERFACE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("vlan-interface", help="Export VLAN interfaces to a YAML file.")
@handle_command_errors("backing up VLAN interfaces")
def backup_vlan_interface(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export VLAN interfaces from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving VLAN interfaces from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    interfaces = scm_client.list_vlan_interfaces(**kwargs)
    if not interfaces:
        info(f"No VLAN interfaces found in {location_type} '{location_value}'")
        return
    export_data = {"vlan_interfaces": interfaces}
    filename = Path(file or get_default_backup_filename("vlan-interface", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(interfaces)} VLAN interfaces to {filename}")


@delete_app.command("vlan-interface", help="Delete a VLAN interface.")
@handle_command_errors("deleting VLAN interface")
def delete_vlan_interface(
    name: str = typer.Argument(..., help="Name of the VLAN interface to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a VLAN interface.

    Examples
    --------
        scm delete network vlan-interface vlan.100 --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    iface = scm_client.get_vlan_interface(name=name, folder=folder, snippet=snippet, device=device)
    if not iface:
        error(f"VLAN interface '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete VLAN interface '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_vlan_interface(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted VLAN interface: {name} from {location_value}")


@load_app.command("vlan-interface", help="Load VLAN interfaces from a YAML file.")
@handle_command_errors("loading VLAN interfaces")
def load_vlan_interface(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load VLAN interfaces from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "vlan_interfaces" not in data:
        error("No VLAN interfaces found in file")
        raise typer.Exit(code=1)
    interfaces = data["vlan_interfaces"]
    if not isinstance(interfaces, list):
        interfaces = [interfaces]
    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        if folder or snippet or device:
            override_type = "folder" if folder else ("snippet" if snippet else "device")
            override_value = folder or snippet or device
            info(f"Container override: {override_type} = '{override_value}'")
        typer.echo(yaml.dump(interfaces))
        return None
    created_count = 0
    updated_count = 0
    no_change_count = 0

    def _apply(iface_data: dict):
        if folder:
            iface_data["folder"] = folder
            iface_data.pop("snippet", None)
            iface_data.pop("device", None)
        elif snippet:
            iface_data["snippet"] = snippet
            iface_data.pop("folder", None)
            iface_data.pop("device", None)
        elif device:
            iface_data["device"] = device
            iface_data.pop("folder", None)
            iface_data.pop("snippet", None)
        validated_iface = VlanInterface(**iface_data)
        sdk_data = validated_iface.to_sdk_model()
        result = scm_client.create_vlan_interface(sdk_data)
        return validated_iface, result

    for _item, outcome, exc in run_bulk(interfaces, _apply):
        if exc is not None:
            error(f"Error processing VLAN interface: {str(exc)}")
            continue
        validated_iface, result = outcome
        action = result.pop("__action__", "created")
        container = validated_iface.folder or validated_iface.snippet or validated_iface.device
        if action == "created":
            created_count += 1
            success(f"Created VLAN interface: {validated_iface.name} in {container}")
        elif action == "updated":
            updated_count += 1
            success(f"Updated VLAN interface: {validated_iface.name} in {container}")
        else:
            no_change_count += 1
            info(f"No changes needed for VLAN interface: {validated_iface.name} in {container}")
    info(f"\nSummary: Processed {created_count + updated_count + no_change_count} VLAN interfaces")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")
    if no_change_count > 0:
        info(f"  - No change: {no_change_count}")


@set_app.command("vlan-interface", help="Create or update a VLAN interface.")
@handle_command_errors("creating/updating VLAN interface")
def set_vlan_interface(
    name: str = typer.Argument(..., help="Name of the VLAN interface"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    comment: str = typer.Option(None, "--comment", help="Interface description/comment"),
    default_value: str = typer.Option(None, "--default-value", help="Default interface (e.g. vlan.100)"),
    vlan_tag: str = typer.Option(None, "--vlan-tag", help="VLAN tag (1-4096)"),
    mtu: int = typer.Option(None, "--mtu", help="MTU (576-9216)"),
    ip_json: str = typer.Option(None, "--ip-json", help='Static IPs as JSON (e.g. \'[{"name": "10.0.0.1/24"}]\')'),
    dhcp_client_json: str = typer.Option(None, "--dhcp-client-json", help="DHCP client config as JSON"),
) -> None:
    """Create or update a VLAN interface."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    iface_data: dict[str, Any] = {"name": name, location_type: location_value}
    if comment:
        iface_data["comment"] = comment
    if default_value:
        iface_data["default_value"] = default_value
    if vlan_tag:
        iface_data["vlan_tag"] = vlan_tag
    if mtu is not None:
        iface_data["mtu"] = mtu
    if ip_json:
        iface_data["ip"] = json.loads(ip_json)
    if dhcp_client_json:
        iface_data["dhcp_client"] = json.loads(dhcp_client_json)
    validated_iface = VlanInterface(**iface_data)
    sdk_data = validated_iface.to_sdk_model()
    result = scm_client.create_vlan_interface(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created VLAN interface: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated VLAN interface: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for VLAN interface: {name} in {location_value}")


@show_app.command("vlan-interface", help="Show VLAN interface details.")
@handle_command_errors("showing VLAN interface")
def show_vlan_interface(
    name: str | None = typer.Argument(None, help="Name of the VLAN interface to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show VLAN interface details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        iface = scm_client.get_vlan_interface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            error(f"VLAN interface '{name}' not found")
            raise typer.Exit(code=1)
        emit(iface, output, title=f"VLAN Interface: {name}")
        return iface
    else:
        interfaces = scm_client.list_vlan_interfaces(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            interfaces = interfaces[:max_results]
        emit(interfaces, output, title=f"VLAN Interfaces in {location_type} '{location_value}'")
        return interfaces


# =============================================================================================================================================================================================
# BGP ADDRESS FAMILY PROFILE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("bgp-address-family-profile", help="Export BGP address family profiles to a YAML file.")
@handle_command_errors("backing up BGP address family profiles")
def backup_bgp_address_family_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export BGP address family profiles from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving BGP address family profiles from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    profiles = scm_client.list_bgp_address_family_profiles(**kwargs)
    if not profiles:
        info(f"No BGP address family profiles found in {location_type} '{location_value}'")
        return
    export_data = {"bgp_address_family_profiles": profiles}
    filename = Path(file or get_default_backup_filename("bgp-address-family-profile", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(profiles)} BGP address family profiles to {filename}")


@delete_app.command("bgp-address-family-profile", help="Delete a BGP address family profile.")
@handle_command_errors("deleting BGP address family profile")
def delete_bgp_address_family_profile(
    name: str = typer.Argument(..., help="Name of the BGP address family profile to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a BGP address family profile.

    Examples
    --------
        scm delete network bgp-address-family-profile my-af-profile --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    profile = scm_client.get_bgp_address_family_profile(name=name, folder=folder, snippet=snippet, device=device)
    if not profile:
        error(f"BGP address family profile '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete BGP address family profile '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_bgp_address_family_profile(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted BGP address family profile: {name} from {location_value}")


@load_app.command("bgp-address-family-profile", help="Load BGP address family profiles from a YAML file.")
@handle_command_errors("loading BGP address family profiles")
def load_bgp_address_family_profile(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load BGP address family profiles from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "bgp_address_family_profiles" not in data:
        error("No BGP address family profiles found in file")
        raise typer.Exit(code=1)
    profiles = data["bgp_address_family_profiles"]
    if not isinstance(profiles, list):
        profiles = [profiles]
    if dry_run:
        info("Dry run mode - no changes will be applied")
        for p in profiles:
            info(f"  Would process: {p.get('name', 'N/A')}")
        return
    created_count = 0
    updated_count = 0
    no_change_count = 0

    def _apply(profile_data: dict):
        if folder:
            profile_data["folder"] = folder
            profile_data.pop("snippet", None)
            profile_data.pop("device", None)
        elif snippet:
            profile_data["snippet"] = snippet
            profile_data.pop("folder", None)
            profile_data.pop("device", None)
        elif device:
            profile_data["device"] = device
            profile_data.pop("folder", None)
            profile_data.pop("snippet", None)
        validated = BgpAddressFamilyProfile(**profile_data)
        sdk_data = validated.to_sdk_model()
        result = scm_client.create_bgp_address_family_profile(sdk_data)
        return validated, result

    for _item, outcome, exc in run_bulk(profiles, _apply):
        if exc is not None:
            error(f"Error processing BGP address family profile: {str(exc)}")
            continue
        validated, result = outcome
        action = result.pop("__action__", "created")
        container = validated.folder or validated.snippet or validated.device
        if action == "created":
            created_count += 1
            success(f"Created BGP address family profile: {validated.name} in {container}")
        elif action == "updated":
            updated_count += 1
            success(f"Updated BGP address family profile: {validated.name} in {container}")
        else:
            no_change_count += 1
            info(f"No changes needed for BGP address family profile: {validated.name} in {container}")
    info(f"\nSummary: Processed {created_count + updated_count + no_change_count} BGP address family profiles")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")
    if no_change_count > 0:
        info(f"  - No change: {no_change_count}")


@set_app.command("bgp-address-family-profile", help="Create or update a BGP address family profile.")
@handle_command_errors("creating/updating BGP address family profile")
def set_bgp_address_family_profile(
    name: str = typer.Argument(..., help="Name of the BGP address family profile"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    ipv4_json: str = typer.Option(None, "--ipv4-json", help="IPv4 address family config as JSON"),
) -> None:
    """Create or update a BGP address family profile."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    profile_data: dict[str, Any] = {"name": name, location_type: location_value}
    if ipv4_json:
        profile_data["ipv4"] = json.loads(ipv4_json)
    validated = BgpAddressFamilyProfile(**profile_data)
    sdk_data = validated.to_sdk_model()
    result = scm_client.create_bgp_address_family_profile(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created BGP address family profile: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated BGP address family profile: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for BGP address family profile: {name} in {location_value}")


@show_app.command("bgp-address-family-profile", help="Show BGP address family profile details.")
@handle_command_errors("showing BGP address family profile")
def show_bgp_address_family_profile(
    name: str | None = typer.Argument(None, help="Name of the profile to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show BGP address family profile details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        profile = scm_client.get_bgp_address_family_profile(name=name, folder=folder, snippet=snippet, device=device)
        if not profile:
            error(f"BGP address family profile '{name}' not found")
            raise typer.Exit(code=1)
        emit(profile, output, title=f"BGP Address Family Profile: {name}")
        return profile
    else:
        profiles = scm_client.list_bgp_address_family_profiles(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            profiles = profiles[:max_results]
        emit(profiles, output, title=f"BGP Address Family Profiles in {location_type} '{location_value}'")
        return profiles


# =============================================================================================================================================================================================
# BGP AUTH PROFILE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("bgp-auth-profile", help="Export BGP auth profiles to a YAML file.")
@handle_command_errors("backing up BGP auth profiles")
def backup_bgp_auth_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export BGP auth profiles from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving BGP auth profiles from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    profiles = scm_client.list_bgp_auth_profiles(**kwargs)
    if not profiles:
        info(f"No BGP auth profiles found in {location_type} '{location_value}'")
        return
    export_data = {"bgp_auth_profiles": profiles}
    filename = Path(file or get_default_backup_filename("bgp-auth-profile", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(profiles)} BGP auth profiles to {filename}")


@delete_app.command("bgp-auth-profile", help="Delete a BGP auth profile.")
@handle_command_errors("deleting BGP auth profile")
def delete_bgp_auth_profile(
    name: str = typer.Argument(..., help="Name of the BGP auth profile to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a BGP auth profile.

    Examples
    --------
        scm delete network bgp-auth-profile my-auth-profile --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    profile = scm_client.get_bgp_auth_profile(name=name, folder=folder, snippet=snippet, device=device)
    if not profile:
        error(f"BGP auth profile '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete BGP auth profile '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_bgp_auth_profile(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted BGP auth profile: {name} from {location_value}")


@load_app.command("bgp-auth-profile", help="Load BGP auth profiles from a YAML file.")
@handle_command_errors("loading BGP auth profiles")
def load_bgp_auth_profile(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load BGP auth profiles from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "bgp_auth_profiles" not in data:
        error("No BGP auth profiles found in file")
        raise typer.Exit(code=1)
    profiles = data["bgp_auth_profiles"]
    if not isinstance(profiles, list):
        profiles = [profiles]
    if dry_run:
        info("Dry run mode - no changes will be applied")
        for p in profiles:
            info(f"  Would process: {p.get('name', 'N/A')}")
        return
    created_count = 0
    updated_count = 0
    no_change_count = 0

    def _apply(profile_data: dict):
        if folder:
            profile_data["folder"] = folder
            profile_data.pop("snippet", None)
            profile_data.pop("device", None)
        elif snippet:
            profile_data["snippet"] = snippet
            profile_data.pop("folder", None)
            profile_data.pop("device", None)
        elif device:
            profile_data["device"] = device
            profile_data.pop("folder", None)
            profile_data.pop("snippet", None)
        validated = BgpAuthProfile(**profile_data)
        sdk_data = validated.to_sdk_model()
        result = scm_client.create_bgp_auth_profile(sdk_data)
        return validated, result

    for _item, outcome, exc in run_bulk(profiles, _apply):
        if exc is not None:
            error(f"Error processing BGP auth profile: {str(exc)}")
            continue
        validated, result = outcome
        action = result.pop("__action__", "created")
        container = validated.folder or validated.snippet or validated.device
        if action == "created":
            created_count += 1
            success(f"Created BGP auth profile: {validated.name} in {container}")
        elif action == "updated":
            updated_count += 1
            success(f"Updated BGP auth profile: {validated.name} in {container}")
        else:
            no_change_count += 1
            info(f"No changes needed for BGP auth profile: {validated.name} in {container}")
    info(f"\nSummary: Processed {created_count + updated_count + no_change_count} BGP auth profiles")


@set_app.command("bgp-auth-profile", help="Create or update a BGP auth profile.")
@handle_command_errors("creating/updating BGP auth profile")
def set_bgp_auth_profile(
    name: str = typer.Argument(..., help="Name of the BGP auth profile"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    secret: str = typer.Option(None, "--secret", help="BGP authentication key"),
) -> None:
    """Create or update a BGP auth profile."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    profile_data: dict[str, Any] = {"name": name, location_type: location_value}
    if secret is not None:
        profile_data["secret"] = secret
    validated = BgpAuthProfile(**profile_data)
    sdk_data = validated.to_sdk_model()
    result = scm_client.create_bgp_auth_profile(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created BGP auth profile: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated BGP auth profile: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for BGP auth profile: {name} in {location_value}")


@show_app.command("bgp-auth-profile", help="Show BGP auth profile details.")
@handle_command_errors("showing BGP auth profile")
def show_bgp_auth_profile(
    name: str | None = typer.Argument(None, help="Name of the profile to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show BGP auth profile details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        profile = scm_client.get_bgp_auth_profile(name=name, folder=folder, snippet=snippet, device=device)
        if not profile:
            error(f"BGP auth profile '{name}' not found")
            raise typer.Exit(code=1)
        emit(profile, output, title=f"BGP Auth Profile: {name}")
        return profile
    else:
        profiles = scm_client.list_bgp_auth_profiles(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            profiles = profiles[:max_results]
        emit(profiles, output, title=f"BGP Auth Profiles in {location_type} '{location_value}'")
        return profiles


# =============================================================================================================================================================================================
# OSPF AUTH PROFILE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("ospf-auth-profile", help="Export OSPF auth profiles to a YAML file.")
@handle_command_errors("backing up OSPF auth profiles")
def backup_ospf_auth_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export OSPF auth profiles from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving OSPF auth profiles from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    profiles = scm_client.list_ospf_auth_profiles(**kwargs)
    if not profiles:
        info(f"No OSPF auth profiles found in {location_type} '{location_value}'")
        return
    export_data = {"ospf_auth_profiles": profiles}
    filename = Path(file or get_default_backup_filename("ospf-auth-profile", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(profiles)} OSPF auth profiles to {filename}")


@delete_app.command("ospf-auth-profile", help="Delete an OSPF auth profile.")
@handle_command_errors("deleting OSPF auth profile")
def delete_ospf_auth_profile(
    name: str = typer.Argument(..., help="Name of the OSPF auth profile to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete an OSPF auth profile."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    profile = scm_client.get_ospf_auth_profile(name=name, folder=folder, snippet=snippet, device=device)
    if not profile:
        error(f"OSPF auth profile '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete OSPF auth profile '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_ospf_auth_profile(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted OSPF auth profile: {name} from {location_value}")


@load_app.command("ospf-auth-profile", help="Load OSPF auth profiles from a YAML file.")
@handle_command_errors("loading OSPF auth profiles")
def load_ospf_auth_profile(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load OSPF auth profiles from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "ospf_auth_profiles" not in data:
        error("No OSPF auth profiles found in file")
        raise typer.Exit(code=1)
    profiles = data["ospf_auth_profiles"]
    if not isinstance(profiles, list):
        profiles = [profiles]
    if dry_run:
        info("Dry run mode - no changes will be applied")
        for p in profiles:
            info(f"  Would process: {p.get('name', 'N/A')}")
        return
    created_count = 0
    updated_count = 0
    no_change_count = 0

    def _apply(profile_data: dict):
        if folder:
            profile_data["folder"] = folder
            profile_data.pop("snippet", None)
            profile_data.pop("device", None)
        elif snippet:
            profile_data["snippet"] = snippet
            profile_data.pop("folder", None)
            profile_data.pop("device", None)
        elif device:
            profile_data["device"] = device
            profile_data.pop("folder", None)
            profile_data.pop("snippet", None)
        validated = OspfAuthProfile(**profile_data)
        sdk_data = validated.to_sdk_model()
        result = scm_client.create_ospf_auth_profile(sdk_data)
        return validated, result

    for _item, outcome, exc in run_bulk(profiles, _apply):
        if exc is not None:
            error(f"Error processing OSPF auth profile: {str(exc)}")
            continue
        validated, result = outcome
        action = result.pop("__action__", "created")
        container = validated.folder or validated.snippet or validated.device
        if action == "created":
            created_count += 1
            success(f"Created OSPF auth profile: {validated.name} in {container}")
        elif action == "updated":
            updated_count += 1
            success(f"Updated OSPF auth profile: {validated.name} in {container}")
        else:
            no_change_count += 1
            info(f"No changes needed for OSPF auth profile: {validated.name} in {container}")
    info(f"\nSummary: Processed {created_count + updated_count + no_change_count} OSPF auth profiles")


@set_app.command("ospf-auth-profile", help="Create or update an OSPF auth profile.")
@handle_command_errors("creating/updating OSPF auth profile")
def set_ospf_auth_profile(
    name: str = typer.Argument(..., help="Name of the OSPF auth profile"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    password: str = typer.Option(None, "--password", help="Simple password authentication"),
    md5_json: str = typer.Option(None, "--md5-json", help="MD5 authentication keys as JSON"),
) -> None:
    """Create or update an OSPF auth profile."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    profile_data: dict[str, Any] = {"name": name, location_type: location_value}
    if password is not None:
        profile_data["password"] = password
    if md5_json:
        profile_data["md5"] = json.loads(md5_json)
    validated = OspfAuthProfile(**profile_data)
    sdk_data = validated.to_sdk_model()
    result = scm_client.create_ospf_auth_profile(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created OSPF auth profile: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated OSPF auth profile: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for OSPF auth profile: {name} in {location_value}")


@show_app.command("ospf-auth-profile", help="Show OSPF auth profile details.")
@handle_command_errors("showing OSPF auth profile")
def show_ospf_auth_profile(
    name: str | None = typer.Argument(None, help="Name of the profile to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show OSPF auth profile details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        profile = scm_client.get_ospf_auth_profile(name=name, folder=folder, snippet=snippet, device=device)
        if not profile:
            error(f"OSPF auth profile '{name}' not found")
            raise typer.Exit(code=1)
        emit(profile, output, title=f"OSPF Auth Profile: {name}")
        return profile
    else:
        profiles = scm_client.list_ospf_auth_profiles(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            profiles = profiles[:max_results]
        emit(profiles, output, title=f"OSPF Auth Profiles in {location_type} '{location_value}'")
        return profiles


# =============================================================================================================================================================================================
# ROUTE ACCESS LIST COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("route-access-list", help="Export route access lists to a YAML file.")
@handle_command_errors("backing up route access lists")
def backup_route_access_list(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export route access lists from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving route access lists from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    items = scm_client.list_route_access_lists(**kwargs)
    if not items:
        info(f"No route access lists found in {location_type} '{location_value}'")
        return
    export_data = {"route_access_lists": items}
    filename = Path(file or get_default_backup_filename("route-access-list", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(items)} route access lists to {filename}")


@delete_app.command("route-access-list", help="Delete a route access list.")
@handle_command_errors("deleting route access list")
def delete_route_access_list(
    name: str = typer.Argument(..., help="Name of the route access list to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a route access list.

    Examples
    --------
        scm delete network route-access-list my-access-list --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    item = scm_client.get_route_access_list(name=name, folder=folder, snippet=snippet, device=device)
    if not item:
        error(f"Route access list '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete route access list '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_route_access_list(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted route access list: {name} from {location_value}")


@load_app.command("route-access-list", help="Load route access lists from a YAML file.")
@handle_command_errors("loading route access lists")
def load_route_access_list(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load route access lists from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "route_access_lists" not in data:
        error("No route access lists found in file")
        raise typer.Exit(code=1)
    items = data["route_access_lists"]
    if not isinstance(items, list):
        items = [items]
    if dry_run:
        info("Dry run mode - no changes will be applied")
        for item in items:
            info(f"  Would process: {item.get('name', 'N/A')}")
        return
    created_count = 0
    updated_count = 0
    no_change_count = 0

    def _apply(item_data: dict):
        if folder:
            item_data["folder"] = folder
            item_data.pop("snippet", None)
            item_data.pop("device", None)
        elif snippet:
            item_data["snippet"] = snippet
            item_data.pop("folder", None)
            item_data.pop("device", None)
        elif device:
            item_data["device"] = device
            item_data.pop("folder", None)
            item_data.pop("snippet", None)
        validated = RouteAccessList(**item_data)
        sdk_data = validated.to_sdk_model()
        result = scm_client.create_route_access_list(sdk_data)
        return validated, result

    for _item, outcome, exc in run_bulk(items, _apply):
        if exc is not None:
            error(f"Error processing route access list: {str(exc)}")
            continue
        validated, result = outcome
        action = result.pop("__action__", "created")
        container = validated.folder or validated.snippet or validated.device
        if action == "created":
            created_count += 1
            success(f"Created route access list: {validated.name} in {container}")
        elif action == "updated":
            updated_count += 1
            success(f"Updated route access list: {validated.name} in {container}")
        else:
            no_change_count += 1
            info(f"No changes needed for route access list: {validated.name} in {container}")
    info(f"\nSummary: Processed {created_count + updated_count + no_change_count} route access lists")


@set_app.command("route-access-list", help="Create or update a route access list.")
@handle_command_errors("creating/updating route access list")
def set_route_access_list(
    name: str = typer.Argument(..., help="Name of the route access list"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    description: str = typer.Option(None, "--description", help="Description"),
    type_json: str = typer.Option(None, "--type-json", help="Access list type config as JSON"),
) -> None:
    """Create or update a route access list."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    item_data: dict[str, Any] = {"name": name, location_type: location_value}
    if description is not None:
        item_data["description"] = description
    if type_json:
        item_data["type"] = json.loads(type_json)
    validated = RouteAccessList(**item_data)
    sdk_data = validated.to_sdk_model()
    result = scm_client.create_route_access_list(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created route access list: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated route access list: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for route access list: {name} in {location_value}")


@show_app.command("route-access-list", help="Show route access list details.")
@handle_command_errors("showing route access list")
def show_route_access_list(
    name: str | None = typer.Argument(None, help="Name of the route access list to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show route access list details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        item = scm_client.get_route_access_list(name=name, folder=folder, snippet=snippet, device=device)
        if not item:
            error(f"Route access list '{name}' not found")
            raise typer.Exit(code=1)
        emit(item, output, title=f"Route Access List: {name}")
        return item
    else:
        items = scm_client.list_route_access_lists(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            items = items[:max_results]
        emit(items, output, title=f"Route Access Lists in {location_type} '{location_value}'")
        return items


# =============================================================================================================================================================================================
# ROUTE PREFIX LIST COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("route-prefix-list", help="Export route prefix lists to a YAML file.")
@handle_command_errors("backing up route prefix lists")
def backup_route_prefix_list(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export route prefix lists from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving route prefix lists from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    items = scm_client.list_route_prefix_lists(**kwargs)
    if not items:
        info(f"No route prefix lists found in {location_type} '{location_value}'")
        return
    export_data = {"route_prefix_lists": items}
    filename = Path(file or get_default_backup_filename("route-prefix-list", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(items)} route prefix lists to {filename}")


@delete_app.command("route-prefix-list", help="Delete a route prefix list.")
@handle_command_errors("deleting route prefix list")
def delete_route_prefix_list(
    name: str = typer.Argument(..., help="Name of the route prefix list to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a route prefix list.

    Examples
    --------
        scm delete network route-prefix-list my-prefix-list --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    item = scm_client.get_route_prefix_list(name=name, folder=folder, snippet=snippet, device=device)
    if not item:
        error(f"Route prefix list '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete route prefix list '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_route_prefix_list(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted route prefix list: {name} from {location_value}")


@load_app.command("route-prefix-list", help="Load route prefix lists from a YAML file.")
@handle_command_errors("loading route prefix lists")
def load_route_prefix_list(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load route prefix lists from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "route_prefix_lists" not in data:
        error("No route prefix lists found in file")
        raise typer.Exit(code=1)
    items = data["route_prefix_lists"]
    if not isinstance(items, list):
        items = [items]
    if dry_run:
        info("Dry run mode - no changes will be applied")
        for item in items:
            info(f"  Would process: {item.get('name', 'N/A')}")
        return
    created_count = 0
    updated_count = 0
    no_change_count = 0

    def _apply(item_data: dict):
        if folder:
            item_data["folder"] = folder
            item_data.pop("snippet", None)
            item_data.pop("device", None)
        elif snippet:
            item_data["snippet"] = snippet
            item_data.pop("folder", None)
            item_data.pop("device", None)
        elif device:
            item_data["device"] = device
            item_data.pop("folder", None)
            item_data.pop("snippet", None)
        validated = RoutePrefixList(**item_data)
        sdk_data = validated.to_sdk_model()
        result = scm_client.create_route_prefix_list(sdk_data)
        return validated, result

    for _item, outcome, exc in run_bulk(items, _apply):
        if exc is not None:
            error(f"Error processing route prefix list: {str(exc)}")
            continue
        validated, result = outcome
        action = result.pop("__action__", "created")
        container = validated.folder or validated.snippet or validated.device
        if action == "created":
            created_count += 1
            success(f"Created route prefix list: {validated.name} in {container}")
        elif action == "updated":
            updated_count += 1
            success(f"Updated route prefix list: {validated.name} in {container}")
        else:
            no_change_count += 1
            info(f"No changes needed for route prefix list: {validated.name} in {container}")
    info(f"\nSummary: Processed {created_count + updated_count + no_change_count} route prefix lists")


@set_app.command("route-prefix-list", help="Create or update a route prefix list.")
@handle_command_errors("creating/updating route prefix list")
def set_route_prefix_list(
    name: str = typer.Argument(..., help="Name of the route prefix list"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    description: str = typer.Option(None, "--description", help="Description"),
    ipv4_json: str = typer.Option(None, "--ipv4-json", help="IPv4 prefix list config as JSON"),
) -> None:
    """Create or update a route prefix list."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    item_data: dict[str, Any] = {"name": name, location_type: location_value}
    if description is not None:
        item_data["description"] = description
    if ipv4_json:
        item_data["ipv4"] = json.loads(ipv4_json)
    validated = RoutePrefixList(**item_data)
    sdk_data = validated.to_sdk_model()
    result = scm_client.create_route_prefix_list(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created route prefix list: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated route prefix list: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for route prefix list: {name} in {location_value}")


@show_app.command("route-prefix-list", help="Show route prefix list details.")
@handle_command_errors("showing route prefix list")
def show_route_prefix_list(
    name: str | None = typer.Argument(None, help="Name of the route prefix list to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show route prefix list details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        item = scm_client.get_route_prefix_list(name=name, folder=folder, snippet=snippet, device=device)
        if not item:
            error(f"Route prefix list '{name}' not found")
            raise typer.Exit(code=1)
        emit(item, output, title=f"Route Prefix List: {name}")
        return item
    else:
        items = scm_client.list_route_prefix_lists(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            items = items[:max_results]
        emit(items, output, title=f"Route Prefix Lists in {location_type} '{location_value}'")
        return items


# =============================================================================================================================================================================================
# BGP FILTERING PROFILE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("bgp-filtering-profile", help="Export BGP filtering profiles to a YAML file.")
@handle_command_errors("backing up BGP filtering profiles")
def backup_bgp_filtering_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export BGP filtering profiles from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving BGP filtering profiles from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    profiles = scm_client.list_bgp_filtering_profiles(**kwargs)
    if not profiles:
        info(f"No BGP filtering profiles found in {location_type} '{location_value}'")
        return
    export_data = {"bgp_filtering_profiles": profiles}
    filename = Path(file or get_default_backup_filename("bgp-filtering-profile", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(profiles)} BGP filtering profiles to {filename}")


@delete_app.command("bgp-filtering-profile", help="Delete a BGP filtering profile.")
@handle_command_errors("deleting BGP filtering profile")
def delete_bgp_filtering_profile(
    name: str = typer.Argument(..., help="Name of the BGP filtering profile to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a BGP filtering profile.

    Examples
    --------
        scm delete network bgp-filtering-profile my-filter --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    profile = scm_client.get_bgp_filtering_profile(name=name, folder=folder, snippet=snippet, device=device)
    if not profile:
        error(f"BGP filtering profile '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete BGP filtering profile '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_bgp_filtering_profile(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted BGP filtering profile: {name} from {location_value}")


@load_app.command("bgp-filtering-profile", help="Load BGP filtering profiles from a YAML file.")
@handle_command_errors("loading BGP filtering profiles")
def load_bgp_filtering_profile(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load BGP filtering profiles from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "bgp_filtering_profiles" not in data:
        error("No BGP filtering profiles found in file")
        raise typer.Exit(code=1)
    profiles = data["bgp_filtering_profiles"]
    if not isinstance(profiles, list):
        profiles = [profiles]
    if dry_run:
        info("Dry run mode - no changes will be applied")
        for p in profiles:
            info(f"  Would process: {p.get('name', 'N/A')}")
        return
    created_count = 0

    def _apply(profile_data: dict):
        if folder:
            profile_data["folder"] = folder
            profile_data.pop("snippet", None)
            profile_data.pop("device", None)
        elif snippet:
            profile_data["snippet"] = snippet
            profile_data.pop("folder", None)
            profile_data.pop("device", None)
        elif device:
            profile_data["device"] = device
            profile_data.pop("folder", None)
            profile_data.pop("snippet", None)
        validated = BgpFilteringProfile(**profile_data)
        sdk_data = validated.to_sdk_model()
        result = scm_client.create_bgp_filtering_profile(sdk_data)
        return validated, result

    for _item, outcome, exc in run_bulk(profiles, _apply):
        if exc is not None:
            error(f"Error processing BGP filtering profile: {str(exc)}")
            continue
        validated, result = outcome
        action = result.pop("__action__", "created")
        container = validated.folder or validated.snippet or validated.device
        created_count += 1
        success(f"{action.capitalize()} BGP filtering profile: {validated.name} in {container}")
    info(f"\nSummary: Processed {created_count} BGP filtering profiles")


@set_app.command("bgp-filtering-profile", help="Create or update a BGP filtering profile.")
@handle_command_errors("creating/updating BGP filtering profile")
def set_bgp_filtering_profile(
    name: str = typer.Argument(..., help="Name of the BGP filtering profile"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    ipv4_json: str = typer.Option(None, "--ipv4-json", help="IPv4 filtering config as JSON"),
) -> None:
    """Create or update a BGP filtering profile."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    profile_data: dict[str, Any] = {"name": name, location_type: location_value}
    if ipv4_json:
        profile_data["ipv4"] = json.loads(ipv4_json)
    validated = BgpFilteringProfile(**profile_data)
    sdk_data = validated.to_sdk_model()
    result = scm_client.create_bgp_filtering_profile(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created BGP filtering profile: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated BGP filtering profile: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for BGP filtering profile: {name} in {location_value}")


@show_app.command("bgp-filtering-profile", help="Show BGP filtering profile details.")
@handle_command_errors("showing BGP filtering profile")
def show_bgp_filtering_profile(
    name: str | None = typer.Argument(None, help="Name of the profile to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show BGP filtering profile details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        profile = scm_client.get_bgp_filtering_profile(name=name, folder=folder, snippet=snippet, device=device)
        if not profile:
            error(f"BGP filtering profile '{name}' not found")
            raise typer.Exit(code=1)
        emit(profile, output, title=f"BGP Filtering Profile: {name}")
        return profile
    else:
        profiles = scm_client.list_bgp_filtering_profiles(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            profiles = profiles[:max_results]
        emit(profiles, output, title=f"BGP Filtering Profiles in {location_type} '{location_value}'")
        return profiles


# =============================================================================================================================================================================================
# BGP REDISTRIBUTION PROFILE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("bgp-redistribution-profile", help="Export BGP redistribution profiles to a YAML file.")
@handle_command_errors("backing up BGP redistribution profiles")
def backup_bgp_redistribution_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export BGP redistribution profiles from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving BGP redistribution profiles from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    profiles = scm_client.list_bgp_redistribution_profiles(**kwargs)
    if not profiles:
        info(f"No BGP redistribution profiles found in {location_type} '{location_value}'")
        return
    export_data = {"bgp_redistribution_profiles": profiles}
    filename = Path(file or get_default_backup_filename("bgp-redistribution-profile", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(profiles)} BGP redistribution profiles to {filename}")


@delete_app.command("bgp-redistribution-profile", help="Delete a BGP redistribution profile.")
@handle_command_errors("deleting BGP redistribution profile")
def delete_bgp_redistribution_profile(
    name: str = typer.Argument(..., help="Name of the BGP redistribution profile to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a BGP redistribution profile.

    Examples
    --------
        scm delete network bgp-redistribution-profile my-redist --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    profile = scm_client.get_bgp_redistribution_profile(name=name, folder=folder, snippet=snippet, device=device)
    if not profile:
        error(f"BGP redistribution profile '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete BGP redistribution profile '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_bgp_redistribution_profile(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted BGP redistribution profile: {name} from {location_value}")


@load_app.command("bgp-redistribution-profile", help="Load BGP redistribution profiles from a YAML file.")
@handle_command_errors("loading BGP redistribution profiles")
def load_bgp_redistribution_profile(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load BGP redistribution profiles from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "bgp_redistribution_profiles" not in data:
        error("No BGP redistribution profiles found in file")
        raise typer.Exit(code=1)
    profiles = data["bgp_redistribution_profiles"]
    if not isinstance(profiles, list):
        profiles = [profiles]
    if dry_run:
        info("Dry run mode - no changes will be applied")
        for p in profiles:
            info(f"  Would process: {p.get('name', 'N/A')}")
        return
    created_count = 0

    def _apply(profile_data: dict):
        if folder:
            profile_data["folder"] = folder
            profile_data.pop("snippet", None)
            profile_data.pop("device", None)
        elif snippet:
            profile_data["snippet"] = snippet
            profile_data.pop("folder", None)
            profile_data.pop("device", None)
        elif device:
            profile_data["device"] = device
            profile_data.pop("folder", None)
            profile_data.pop("snippet", None)
        validated = BgpRedistributionProfile(**profile_data)
        sdk_data = validated.to_sdk_model()
        result = scm_client.create_bgp_redistribution_profile(sdk_data)
        return validated, result

    for _item, outcome, exc in run_bulk(profiles, _apply):
        if exc is not None:
            error(f"Error processing BGP redistribution profile: {str(exc)}")
            continue
        validated, result = outcome
        action = result.pop("__action__", "created")
        container = validated.folder or validated.snippet or validated.device
        created_count += 1
        success(f"{action.capitalize()} BGP redistribution profile: {validated.name} in {container}")
    info(f"\nSummary: Processed {created_count} BGP redistribution profiles")


@set_app.command("bgp-redistribution-profile", help="Create or update a BGP redistribution profile.")
@handle_command_errors("creating/updating BGP redistribution profile")
def set_bgp_redistribution_profile(
    name: str = typer.Argument(..., help="Name of the BGP redistribution profile"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    ipv4_json: str = typer.Option(None, "--ipv4-json", help="IPv4 redistribution config as JSON"),
) -> None:
    """Create or update a BGP redistribution profile."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    profile_data: dict[str, Any] = {"name": name, location_type: location_value}
    if ipv4_json:
        profile_data["ipv4"] = json.loads(ipv4_json)
    validated = BgpRedistributionProfile(**profile_data)
    sdk_data = validated.to_sdk_model()
    result = scm_client.create_bgp_redistribution_profile(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created BGP redistribution profile: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated BGP redistribution profile: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for BGP redistribution profile: {name} in {location_value}")


@show_app.command("bgp-redistribution-profile", help="Show BGP redistribution profile details.")
@handle_command_errors("showing BGP redistribution profile")
def show_bgp_redistribution_profile(
    name: str | None = typer.Argument(None, help="Name of the profile to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show BGP redistribution profile details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        profile = scm_client.get_bgp_redistribution_profile(name=name, folder=folder, snippet=snippet, device=device)
        if not profile:
            error(f"BGP redistribution profile '{name}' not found")
            raise typer.Exit(code=1)
        emit(profile, output, title=f"BGP Redistribution Profile: {name}")
        return profile
    else:
        profiles = scm_client.list_bgp_redistribution_profiles(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            profiles = profiles[:max_results]
        emit(profiles, output, title=f"BGP Redistribution Profiles in {location_type} '{location_value}'")
        return profiles


# =============================================================================================================================================================================================
# BGP ROUTE MAP COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("bgp-route-map", help="Export BGP route maps to a YAML file.")
@handle_command_errors("backing up BGP route maps")
def backup_bgp_route_map(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export BGP route maps from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving BGP route maps from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    items = scm_client.list_bgp_route_maps(**kwargs)
    if not items:
        info(f"No BGP route maps found in {location_type} '{location_value}'")
        return
    export_data = {"bgp_route_maps": items}
    filename = Path(file or get_default_backup_filename("bgp-route-map", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(items)} BGP route maps to {filename}")


@delete_app.command("bgp-route-map", help="Delete a BGP route map.")
@handle_command_errors("deleting BGP route map")
def delete_bgp_route_map(
    name: str = typer.Argument(..., help="Name of the BGP route map to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a BGP route map.

    Examples
    --------
        scm delete network bgp-route-map my-route-map --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    item = scm_client.get_bgp_route_map(name=name, folder=folder, snippet=snippet, device=device)
    if not item:
        error(f"BGP route map '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete BGP route map '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_bgp_route_map(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted BGP route map: {name} from {location_value}")


@load_app.command("bgp-route-map", help="Load BGP route maps from a YAML file.")
@handle_command_errors("loading BGP route maps")
def load_bgp_route_map(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load BGP route maps from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "bgp_route_maps" not in data:
        error("No BGP route maps found in file")
        raise typer.Exit(code=1)
    items = data["bgp_route_maps"]
    if not isinstance(items, list):
        items = [items]
    if dry_run:
        info("Dry run mode - no changes will be applied")
        for item in items:
            info(f"  Would process: {item.get('name', 'N/A')}")
        return
    created_count = 0

    def _apply(item_data: dict):
        if folder:
            item_data["folder"] = folder
            item_data.pop("snippet", None)
            item_data.pop("device", None)
        elif snippet:
            item_data["snippet"] = snippet
            item_data.pop("folder", None)
            item_data.pop("device", None)
        elif device:
            item_data["device"] = device
            item_data.pop("folder", None)
            item_data.pop("snippet", None)
        validated = BgpRouteMap(**item_data)
        sdk_data = validated.to_sdk_model()
        result = scm_client.create_bgp_route_map(sdk_data)
        return validated, result

    for _item, outcome, exc in run_bulk(items, _apply):
        if exc is not None:
            error(f"Error processing BGP route map: {str(exc)}")
            continue
        validated, result = outcome
        action = result.pop("__action__", "created")
        container = validated.folder or validated.snippet or validated.device
        created_count += 1
        success(f"{action.capitalize()} BGP route map: {validated.name} in {container}")
    info(f"\nSummary: Processed {created_count} BGP route maps")


@set_app.command("bgp-route-map", help="Create or update a BGP route map.")
@handle_command_errors("creating/updating BGP route map")
def set_bgp_route_map(
    name: str = typer.Argument(..., help="Name of the BGP route map"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    route_map_json: str = typer.Option(None, "--route-map-json", help="Route map entries as JSON"),
) -> None:
    """Create or update a BGP route map."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    item_data: dict[str, Any] = {"name": name, location_type: location_value}
    if route_map_json:
        item_data["route_map"] = json.loads(route_map_json)
    validated = BgpRouteMap(**item_data)
    sdk_data = validated.to_sdk_model()
    result = scm_client.create_bgp_route_map(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created BGP route map: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated BGP route map: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for BGP route map: {name} in {location_value}")


@show_app.command("bgp-route-map", help="Show BGP route map details.")
@handle_command_errors("showing BGP route map")
def show_bgp_route_map(
    name: str | None = typer.Argument(None, help="Name of the BGP route map to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show BGP route map details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        item = scm_client.get_bgp_route_map(name=name, folder=folder, snippet=snippet, device=device)
        if not item:
            error(f"BGP route map '{name}' not found")
            raise typer.Exit(code=1)
        emit(item, output, title=f"BGP Route Map: {name}")
        return item
    else:
        items = scm_client.list_bgp_route_maps(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            items = items[:max_results]
        emit(items, output, title=f"BGP Route Maps in {location_type} '{location_value}'")
        return items


# =============================================================================================================================================================================================
# BGP ROUTE MAP REDISTRIBUTION COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("bgp-route-map-redistribution", help="Export BGP route map redistributions to a YAML file.")
@handle_command_errors("backing up BGP route map redistributions")
def backup_bgp_route_map_redistribution(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export BGP route map redistributions from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving BGP route map redistributions from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    items = scm_client.list_bgp_route_map_redistributions(**kwargs)
    if not items:
        info(f"No BGP route map redistributions found in {location_type} '{location_value}'")
        return
    export_data = {"bgp_route_map_redistributions": items}
    filename = Path(file or get_default_backup_filename("bgp-route-map-redistribution", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(items)} BGP route map redistributions to {filename}")


@delete_app.command("bgp-route-map-redistribution", help="Delete a BGP route map redistribution.")
@handle_command_errors("deleting BGP route map redistribution")
def delete_bgp_route_map_redistribution(
    name: str = typer.Argument(..., help="Name of the BGP route map redistribution to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a BGP route map redistribution.

    Examples
    --------
        scm delete network bgp-route-map-redistribution my-redist-map --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    item = scm_client.get_bgp_route_map_redistribution(name=name, folder=folder, snippet=snippet, device=device)
    if not item:
        error(f"BGP route map redistribution '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete BGP route map redistribution '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_bgp_route_map_redistribution(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted BGP route map redistribution: {name} from {location_value}")


@load_app.command("bgp-route-map-redistribution", help="Load BGP route map redistributions from a YAML file.")
@handle_command_errors("loading BGP route map redistributions")
def load_bgp_route_map_redistribution(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load BGP route map redistributions from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "bgp_route_map_redistributions" not in data:
        error("No BGP route map redistributions found in file")
        raise typer.Exit(code=1)
    items = data["bgp_route_map_redistributions"]
    if not isinstance(items, list):
        items = [items]
    if dry_run:
        info("Dry run mode - no changes will be applied")
        for item in items:
            info(f"  Would process: {item.get('name', 'N/A')}")
        return
    created_count = 0

    def _apply(item_data: dict):
        if folder:
            item_data["folder"] = folder
            item_data.pop("snippet", None)
            item_data.pop("device", None)
        elif snippet:
            item_data["snippet"] = snippet
            item_data.pop("folder", None)
            item_data.pop("device", None)
        elif device:
            item_data["device"] = device
            item_data.pop("folder", None)
            item_data.pop("snippet", None)
        validated = BgpRouteMapRedistribution(**item_data)
        sdk_data = validated.to_sdk_model()
        result = scm_client.create_bgp_route_map_redistribution(sdk_data)
        return validated, result

    for _item, outcome, exc in run_bulk(items, _apply):
        if exc is not None:
            error(f"Error processing BGP route map redistribution: {str(exc)}")
            continue
        validated, result = outcome
        action = result.pop("__action__", "created")
        container = validated.folder or validated.snippet or validated.device
        created_count += 1
        success(f"{action.capitalize()} BGP route map redistribution: {validated.name} in {container}")
    info(f"\nSummary: Processed {created_count} BGP route map redistributions")


@set_app.command("bgp-route-map-redistribution", help="Create or update a BGP route map redistribution.")
@handle_command_errors("creating/updating BGP route map redistribution")
def set_bgp_route_map_redistribution(
    name: str = typer.Argument(..., help="Name of the BGP route map redistribution"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    bgp_json: str = typer.Option(None, "--bgp-json", help="BGP source protocol config as JSON"),
    ospf_json: str = typer.Option(None, "--ospf-json", help="OSPF source protocol config as JSON"),
    connected_static_json: str = typer.Option(None, "--connected-static-json", help="Connected/Static source protocol config as JSON"),
) -> None:
    """Create or update a BGP route map redistribution."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    item_data: dict[str, Any] = {"name": name, location_type: location_value}
    if bgp_json:
        item_data["bgp"] = json.loads(bgp_json)
    if ospf_json:
        item_data["ospf"] = json.loads(ospf_json)
    if connected_static_json:
        item_data["connected_static"] = json.loads(connected_static_json)
    validated = BgpRouteMapRedistribution(**item_data)
    sdk_data = validated.to_sdk_model()
    result = scm_client.create_bgp_route_map_redistribution(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created BGP route map redistribution: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated BGP route map redistribution: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for BGP route map redistribution: {name} in {location_value}")


@show_app.command("bgp-route-map-redistribution", help="Show BGP route map redistribution details.")
@handle_command_errors("showing BGP route map redistribution")
def show_bgp_route_map_redistribution(
    name: str | None = typer.Argument(None, help="Name of the BGP route map redistribution to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show BGP route map redistribution details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        item = scm_client.get_bgp_route_map_redistribution(name=name, folder=folder, snippet=snippet, device=device)
        if not item:
            error(f"BGP route map redistribution '{name}' not found")
            raise typer.Exit(code=1)
        emit(item, output, title=f"BGP Route Map Redistribution: {name}")
        return item
    else:
        items = scm_client.list_bgp_route_map_redistributions(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            items = items[:max_results]
        emit(items, output, title=f"BGP Route Map Redistributions in {location_type} '{location_value}'")
        return items


# =============================================================================================================================================================================================
# DNS PROXY COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("dns-proxy", help="Export DNS proxies to a YAML file.")
@handle_command_errors("backing up DNS proxies")
def backup_dns_proxy(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export DNS proxies from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving DNS proxies from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    proxies = scm_client.list_dns_proxies(**kwargs)
    if not proxies:
        info(f"No DNS proxies found in {location_type} '{location_value}'")
        return
    export_data = {"dns_proxies": proxies}
    filename = Path(file or get_default_backup_filename("dns-proxy", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(proxies)} DNS proxies to {filename}")


@delete_app.command("dns-proxy", help="Delete a DNS proxy.")
@handle_command_errors("deleting DNS proxy")
def delete_dns_proxy(
    name: str = typer.Argument(..., help="Name of the DNS proxy to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a DNS proxy.

    Examples
    --------
        scm delete network dns-proxy my-dns-proxy --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    proxy = scm_client.get_dns_proxy(name=name, folder=folder, snippet=snippet, device=device)
    if not proxy:
        error(f"DNS proxy '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete DNS proxy '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_dns_proxy(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted DNS proxy: {name} from {location_value}")


@load_app.command("dns-proxy", help="Load DNS proxies from a YAML file.")
@handle_command_errors("loading DNS proxies")
def load_dns_proxy(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load DNS proxies from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "dns_proxies" not in data:
        error("No DNS proxies found in file")
        raise typer.Exit(code=1)
    proxies = data["dns_proxies"]
    if not isinstance(proxies, list):
        proxies = [proxies]
    if dry_run:
        info("Dry run mode - no changes will be applied")
        for p in proxies:
            info(f"  Would process: {p.get('name', 'N/A')}")
        return
    created_count = 0
    updated_count = 0
    no_change_count = 0

    def _apply(proxy_data: dict):
        if folder:
            proxy_data["folder"] = folder
            proxy_data.pop("snippet", None)
            proxy_data.pop("device", None)
        elif snippet:
            proxy_data["snippet"] = snippet
            proxy_data.pop("folder", None)
            proxy_data.pop("device", None)
        elif device:
            proxy_data["device"] = device
            proxy_data.pop("folder", None)
            proxy_data.pop("snippet", None)
        validated = DnsProxy(**proxy_data)
        sdk_data = validated.to_sdk_model()
        result = scm_client.create_dns_proxy(sdk_data)
        return validated, result

    for _item, outcome, exc in run_bulk(proxies, _apply):
        if exc is not None:
            error(f"Error processing DNS proxy: {str(exc)}")
            continue
        validated, result = outcome
        action = result.pop("__action__", "created")
        container = validated.folder or validated.snippet or validated.device
        if action == "created":
            created_count += 1
            success(f"Created DNS proxy: {validated.name} in {container}")
        elif action == "updated":
            updated_count += 1
            success(f"Updated DNS proxy: {validated.name} in {container}")
        else:
            no_change_count += 1
            info(f"No changes needed for DNS proxy: {validated.name} in {container}")
    info(f"\nSummary: Processed {created_count + updated_count + no_change_count} DNS proxies")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")
    if no_change_count > 0:
        info(f"  - No change: {no_change_count}")


@set_app.command("dns-proxy", help="Create or update a DNS proxy.")
@handle_command_errors("creating/updating DNS proxy")
def set_dns_proxy(
    name: str = typer.Argument(..., help="Name of the DNS proxy"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    enabled: bool = typer.Option(None, "--enabled", help="Enable DNS proxy"),
    default_json: str = typer.Option(None, "--default-json", help="Default DNS server config as JSON"),
    cache_json: str = typer.Option(None, "--cache-json", help="Cache configuration as JSON"),
) -> None:
    """Create or update a DNS proxy."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    proxy_data: dict[str, Any] = {"name": name, location_type: location_value}
    if enabled is not None:
        proxy_data["enabled"] = enabled
    if default_json:
        proxy_data["default"] = json.loads(default_json)
    if cache_json:
        proxy_data["cache"] = json.loads(cache_json)
    validated = DnsProxy(**proxy_data)
    sdk_data = validated.to_sdk_model()
    result = scm_client.create_dns_proxy(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created DNS proxy: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated DNS proxy: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for DNS proxy: {name} in {location_value}")


@show_app.command("dns-proxy", help="Show DNS proxy details.")
@handle_command_errors("showing DNS proxy")
def show_dns_proxy(
    name: str | None = typer.Argument(None, help="Name of the DNS proxy to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show DNS proxy details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        proxy = scm_client.get_dns_proxy(name=name, folder=folder, snippet=snippet, device=device)
        if not proxy:
            error(f"DNS proxy '{name}' not found")
            raise typer.Exit(code=1)
        emit(proxy, output, title=f"DNS Proxy: {name}")
        return proxy
    else:
        proxies = scm_client.list_dns_proxies(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            proxies = proxies[:max_results]
        emit(proxies, output, title=f"DNS Proxies in {location_type} '{location_value}'")
        return proxies


# =============================================================================================================================================================================================
# PBF RULE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("pbf-rule", help="Export PBF rules to a YAML file.")
@handle_command_errors("backing up PBF rules")
def backup_pbf_rule(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export PBF rules from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving PBF rules from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    rules = scm_client.list_pbf_rules(**kwargs)
    if not rules:
        info(f"No PBF rules found in {location_type} '{location_value}'")
        return
    export_data = {"pbf_rules": rules}
    filename = Path(file or get_default_backup_filename("pbf-rule", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(rules)} PBF rules to {filename}")


@delete_app.command("pbf-rule", help="Delete a PBF rule.")
@handle_command_errors("deleting PBF rule")
def delete_pbf_rule(
    name: str = typer.Argument(..., help="Name of the PBF rule to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a PBF rule.

    Examples
    --------
        scm delete network pbf-rule my-pbf-rule --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    rule = scm_client.get_pbf_rule(name=name, folder=folder, snippet=snippet, device=device)
    if not rule:
        error(f"PBF rule '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete PBF rule '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_pbf_rule(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted PBF rule: {name} from {location_value}")


@load_app.command("pbf-rule", help="Load PBF rules from a YAML file.")
@handle_command_errors("loading PBF rules")
def load_pbf_rule(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load PBF rules from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "pbf_rules" not in data:
        error("No PBF rules found in file")
        raise typer.Exit(code=1)
    rules = data["pbf_rules"]
    if not isinstance(rules, list):
        rules = [rules]
    if dry_run:
        info("Dry run mode - no changes will be applied")
        for r in rules:
            info(f"  Would process: {r.get('name', 'N/A')}")
        return
    created_count = 0
    updated_count = 0
    no_change_count = 0
    # sequential: rule order matters
    for rule_data in rules:
        try:
            if folder:
                rule_data["folder"] = folder
                rule_data.pop("snippet", None)
                rule_data.pop("device", None)
            elif snippet:
                rule_data["snippet"] = snippet
                rule_data.pop("folder", None)
                rule_data.pop("device", None)
            elif device:
                rule_data["device"] = device
                rule_data.pop("folder", None)
                rule_data.pop("snippet", None)
            validated = PbfRule(**rule_data)
            sdk_data = validated.to_sdk_model()
            result = scm_client.create_pbf_rule(sdk_data)
            action = result.pop("__action__", "created")
            container = validated.folder or validated.snippet or validated.device
            if action == "created":
                created_count += 1
                success(f"Created PBF rule: {validated.name} in {container}")
            elif action == "updated":
                updated_count += 1
                success(f"Updated PBF rule: {validated.name} in {container}")
            else:
                no_change_count += 1
                info(f"No changes needed for PBF rule: {validated.name} in {container}")
        except Exception as e:
            error(f"Error processing PBF rule: {str(e)}")
            continue
    info(f"\nSummary: Processed {created_count + updated_count + no_change_count} PBF rules")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")
    if no_change_count > 0:
        info(f"  - No change: {no_change_count}")


@set_app.command("pbf-rule", help="Create or update a PBF rule.")
@handle_command_errors("creating/updating PBF rule")
def set_pbf_rule(
    name: str = typer.Argument(..., help="Name of the PBF rule"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    description: str = typer.Option(None, "--description", help="Description"),
    action_json: str = typer.Option(None, "--action-json", help="Action config as JSON"),
    from_json: str = typer.Option(None, "--from-json", help="Source zone/interface config as JSON"),
) -> None:
    """Create or update a PBF rule."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    rule_data: dict[str, Any] = {"name": name, location_type: location_value}
    if description:
        rule_data["description"] = description
    if action_json:
        rule_data["action"] = json.loads(action_json)
    if from_json:
        rule_data["from"] = json.loads(from_json)
    validated = PbfRule(**rule_data)
    sdk_data = validated.to_sdk_model()
    result = scm_client.create_pbf_rule(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created PBF rule: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated PBF rule: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for PBF rule: {name} in {location_value}")


@show_app.command("pbf-rule", help="Show PBF rule details.")
@handle_command_errors("showing PBF rule")
def show_pbf_rule(
    name: str | None = typer.Argument(None, help="Name of the PBF rule to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show PBF rule details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        rule = scm_client.get_pbf_rule(name=name, folder=folder, snippet=snippet, device=device)
        if not rule:
            error(f"PBF rule '{name}' not found")
            raise typer.Exit(code=1)
        emit(rule, output, title=f"PBF Rule: {name}")
        return rule
    else:
        rules = scm_client.list_pbf_rules(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            rules = rules[:max_results]
        emit(rules, output, title=f"PBF Rules in {location_type} '{location_value}'")
        return rules


# =============================================================================================================================================================================================
# QOS PROFILE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("qos-profile", help="Export QoS profiles to a YAML file.")
@handle_command_errors("backing up QoS profiles")
def backup_qos_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export QoS profiles from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    validate_qos_profile_folder(folder)
    info(f"Retrieving QoS profiles from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    profiles = scm_client.list_qos_profiles(**kwargs)
    if not profiles:
        info(f"No QoS profiles found in {location_type} '{location_value}'")
        return
    export_data = {"qos_profiles": profiles}
    filename = Path(file or get_default_backup_filename("qos-profile", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(profiles)} QoS profiles to {filename}")


@delete_app.command("qos-profile", help="Delete a QoS profile.")
@handle_command_errors("deleting QoS profile")
def delete_qos_profile(
    name: str = typer.Argument(..., help="Name of the QoS profile to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a QoS profile.

    Examples
    --------
        scm delete network qos-profile my-qos-profile --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    validate_qos_profile_folder(folder)
    profile = scm_client.get_qos_profile(name=name, folder=folder, snippet=snippet, device=device)
    if not profile:
        error(f"QoS profile '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete QoS profile '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_qos_profile(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted QoS profile: {name} from {location_value}")


@load_app.command("qos-profile", help="Load QoS profiles from a YAML file.")
@handle_command_errors("loading QoS profiles")
def load_qos_profile(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load QoS profiles from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "qos_profiles" not in data:
        error("No QoS profiles found in file")
        raise typer.Exit(code=1)
    profiles = data["qos_profiles"]
    if not isinstance(profiles, list):
        profiles = [profiles]
    if dry_run:
        info("Dry run mode - no changes will be applied")
        for p in profiles:
            info(f"  Would process: {p.get('name', 'N/A')}")
        return
    created_count = 0
    updated_count = 0
    no_change_count = 0

    def _apply(profile_data: dict):
        if folder:
            profile_data["folder"] = folder
            profile_data.pop("snippet", None)
            profile_data.pop("device", None)
        elif snippet:
            profile_data["snippet"] = snippet
            profile_data.pop("folder", None)
            profile_data.pop("device", None)
        elif device:
            profile_data["device"] = device
            profile_data.pop("folder", None)
            profile_data.pop("snippet", None)
        validated = QosProfile(**profile_data)
        sdk_data = validated.to_sdk_model()
        result = scm_client.create_qos_profile(sdk_data)
        return validated, result

    for _item, outcome, exc in run_bulk(profiles, _apply):
        if exc is not None:
            error(f"Error processing QoS profile: {str(exc)}")
            continue
        validated, result = outcome
        action = result.pop("__action__", "created")
        container = validated.folder or validated.snippet or validated.device
        if action == "created":
            created_count += 1
            success(f"Created QoS profile: {validated.name} in {container}")
        elif action == "updated":
            updated_count += 1
            success(f"Updated QoS profile: {validated.name} in {container}")
        else:
            no_change_count += 1
            info(f"No changes needed for QoS profile: {validated.name} in {container}")
    info(f"\nSummary: Processed {created_count + updated_count + no_change_count} QoS profiles")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")
    if no_change_count > 0:
        info(f"  - No change: {no_change_count}")


@set_app.command("qos-profile", help="Create or update a QoS profile.")
@handle_command_errors("creating/updating QoS profile")
def set_qos_profile(
    name: str = typer.Argument(..., help="Name of the QoS profile"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    aggregate_bandwidth_json: str = typer.Option(None, "--aggregate-bandwidth-json", help="Aggregate bandwidth config as JSON"),
    class_bandwidth_type_json: str = typer.Option(None, "--class-bandwidth-type-json", help="Class bandwidth type config as JSON"),
) -> None:
    """Create or update a QoS profile."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    validate_qos_profile_folder(folder)
    profile_data: dict[str, Any] = {"name": name, location_type: location_value}
    if aggregate_bandwidth_json:
        profile_data["aggregate_bandwidth"] = json.loads(aggregate_bandwidth_json)
    if class_bandwidth_type_json:
        profile_data["class_bandwidth_type"] = json.loads(class_bandwidth_type_json)
    validated = QosProfile(**profile_data)
    sdk_data = validated.to_sdk_model()
    result = scm_client.create_qos_profile(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created QoS profile: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated QoS profile: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for QoS profile: {name} in {location_value}")


@show_app.command("qos-profile", help="Show QoS profile details.")
@handle_command_errors("showing QoS profile")
def show_qos_profile(
    name: str | None = typer.Argument(None, help="Name of the QoS profile to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show QoS profile details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    validate_qos_profile_folder(folder)
    if name:
        profile = scm_client.get_qos_profile(name=name, folder=folder, snippet=snippet, device=device)
        if not profile:
            error(f"QoS profile '{name}' not found")
            raise typer.Exit(code=1)
        emit(profile, output, title=f"QoS Profile: {name}")
        return profile
    else:
        profiles = scm_client.list_qos_profiles(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            profiles = profiles[:max_results]
        emit(profiles, output, title=f"QoS Profiles in {location_type} '{location_value}'")
        return profiles


# =============================================================================================================================================================================================
# QOS RULE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("qos-rule", help="Export QoS rules to a YAML file.")
@handle_command_errors("backing up QoS rules")
def backup_qos_rule(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export QoS rules from a specified location to a YAML file."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    info(f"Retrieving QoS rules from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    rules = scm_client.list_qos_rules(**kwargs)
    if not rules:
        info(f"No QoS rules found in {location_type} '{location_value}'")
        return
    export_data = {"qos_rules": rules}
    filename = Path(file or get_default_backup_filename("qos-rule", location_type, location_value))
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
    success(f"Successfully backed up {len(rules)} QoS rules to {filename}")


@delete_app.command("qos-rule", help="Delete a QoS rule.")
@handle_command_errors("deleting QoS rule")
def delete_qos_rule(
    name: str = typer.Argument(..., help="Name of the QoS rule to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a QoS rule.

    Examples
    --------
        scm delete network qos-rule my-qos-rule --folder Texas

    """
    location_type, location_value = validate_location_params(folder, snippet, device)
    rule = scm_client.get_qos_rule(name=name, folder=folder, snippet=snippet, device=device)
    if not rule:
        error(f"QoS rule '{name}' not found")
        raise typer.Exit(code=1)
    if not force:
        typer.confirm(f"Delete QoS rule '{name}' from {location_type} '{location_value}'?", abort=True)
    scm_client.delete_qos_rule(name=name, folder=folder, snippet=snippet, device=device)
    success(f"Deleted QoS rule: {name} from {location_value}")


@load_app.command("qos-rule", help="Load QoS rules from a YAML file.")
@handle_command_errors("loading QoS rules")
def load_qos_rule(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load QoS rules from a YAML file."""
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)
    with Path(file).open() as f:
        data = yaml.safe_load(f)
    if not data or "qos_rules" not in data:
        error("No QoS rules found in file")
        raise typer.Exit(code=1)
    rules = data["qos_rules"]
    if not isinstance(rules, list):
        rules = [rules]
    if dry_run:
        info("Dry run mode - no changes will be applied")
        for r in rules:
            info(f"  Would process: {r.get('name', 'N/A')}")
        return
    created_count = 0
    updated_count = 0
    no_change_count = 0
    # sequential: rule order matters
    for rule_data in rules:
        try:
            if folder:
                rule_data["folder"] = folder
                rule_data.pop("snippet", None)
                rule_data.pop("device", None)
            elif snippet:
                rule_data["snippet"] = snippet
                rule_data.pop("folder", None)
                rule_data.pop("device", None)
            elif device:
                rule_data["device"] = device
                rule_data.pop("folder", None)
                rule_data.pop("snippet", None)
            validated = QosRule(**rule_data)
            sdk_data = validated.to_sdk_model()
            result = scm_client.create_qos_rule(sdk_data)
            action = result.pop("__action__", "created")
            container = validated.folder or validated.snippet or validated.device
            if action == "created":
                created_count += 1
                success(f"Created QoS rule: {validated.name} in {container}")
            elif action == "updated":
                updated_count += 1
                success(f"Updated QoS rule: {validated.name} in {container}")
            else:
                no_change_count += 1
                info(f"No changes needed for QoS rule: {validated.name} in {container}")
        except Exception as e:
            error(f"Error processing QoS rule: {str(e)}")
            continue
    info(f"\nSummary: Processed {created_count + updated_count + no_change_count} QoS rules")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")
    if no_change_count > 0:
        info(f"  - No change: {no_change_count}")


@set_app.command("qos-rule", help="Create or update a QoS rule.")
@handle_command_errors("creating/updating QoS rule")
def set_qos_rule(
    name: str = typer.Argument(..., help="Name of the QoS rule"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    description: str = typer.Option(None, "--description", help="Description"),
    action_json: str = typer.Option(None, "--action-json", help="Action config as JSON"),
    schedule: str = typer.Option(None, "--schedule", help="Schedule"),
    dscp_tos_json: str = typer.Option(None, "--dscp-tos-json", help="DSCP/TOS config as JSON"),
) -> None:
    """Create or update a QoS rule."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    rule_data: dict[str, Any] = {"name": name, location_type: location_value}
    if description:
        rule_data["description"] = description
    if action_json:
        rule_data["action"] = json.loads(action_json)
    if schedule:
        rule_data["schedule"] = schedule
    if dscp_tos_json:
        rule_data["dscp_tos"] = json.loads(dscp_tos_json)
    validated = QosRule(**rule_data)
    sdk_data = validated.to_sdk_model()
    result = scm_client.create_qos_rule(sdk_data)
    action = result.pop("__action__", "created")
    if action == "created":
        success(f"Created QoS rule: {name} in {location_value}")
    elif action == "updated":
        success(f"Updated QoS rule: {name} in {location_value}")
    elif action == "no_change":
        info(f"No changes needed for QoS rule: {name} in {location_value}")


@show_app.command("qos-rule", help="Show QoS rule details.")
@handle_command_errors("showing QoS rule")
def show_qos_rule(
    name: str | None = typer.Argument(None, help="Name of the QoS rule to show; omit to list all"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
    max_results: int | None = typer.Option(None, "--max-results", help="Maximum number of results to display"),
) -> None:
    """Show QoS rule details."""
    location_type, location_value = validate_location_params(folder, snippet, device)
    if name:
        rule = scm_client.get_qos_rule(name=name, folder=folder, snippet=snippet, device=device)
        if not rule:
            error(f"QoS rule '{name}' not found")
            raise typer.Exit(code=1)
        emit(rule, output, title=f"QoS Rule: {name}")
        return rule
    else:
        rules = scm_client.list_qos_rules(folder=folder, snippet=snippet, device=device)
        if max_results is not None:
            rules = rules[:max_results]
        emit(rules, output, title=f"QoS Rules in {location_type} '{location_value}'")
        return rules
