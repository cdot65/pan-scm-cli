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
from pydantic import ValidationError

from ..utils import validate_location_params
from ..utils.config import load_from_yaml
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
FOLDER_OPTION = typer.Option(
    ...,
    "--folder",
    help="Folder path for the zone",
)
NAME_OPTION = typer.Option(
    ...,
    "--name",
    help="Name of the zone",
)
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
NAT_FOLDER_OPTION = typer.Option(
    ...,
    "--folder",
    help="Folder path for the NAT rule",
)
NAT_NAME_OPTION = typer.Option(
    ...,
    "--name",
    help="Name of the NAT rule",
)
NAT_DESCRIPTION_OPTION = typer.Option(
    None,
    "--description",
    help="Description of the NAT rule",
)
NAT_TAG_OPTION = typer.Option(
    None,
    "--tag",
    help="Tags for the NAT rule",
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
IPSEC_FOLDER_OPTION = typer.Option("Texas", "--folder", help="Folder path for the IPsec crypto profile")
IPSEC_NAME_OPTION = typer.Option(..., "--name", help="Name of the IPsec crypto profile")
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
        typer.echo(
            f"Error: QoS profiles only support folders: {', '.join(QOS_PROFILE_ALLOWED_FOLDERS)}. Got: '{folder}'",
            err=True,
        )
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
def backup_ike_crypto_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export IKE crypto profiles from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving IKE crypto profiles from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        profiles = scm_client.list_ike_crypto_profiles(**kwargs)
        if not profiles:
            typer.echo(f"No IKE crypto profiles found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"ike_crypto_profiles": profiles}
        filename = Path(file or get_default_backup_filename("ike-crypto-profile", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(profiles)} IKE crypto profiles to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up IKE crypto profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("ike-crypto-profile", help="Delete an IKE crypto profile.")
def delete_ike_crypto_profile(
    name: str = typer.Argument(..., help="Name of the IKE crypto profile to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete an IKE crypto profile."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        profile = scm_client.get_ike_crypto_profile(name=name, folder=folder, snippet=snippet, device=device)
        if not profile:
            typer.echo(f"IKE crypto profile '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete IKE crypto profile '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_ike_crypto_profile(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted IKE crypto profile: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting IKE crypto profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("ike-crypto-profile", help="Load IKE crypto profiles from a YAML file.")
def load_ike_crypto_profile(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
) -> None:
    """Load IKE crypto profiles from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "ike_crypto_profiles" not in data:
            typer.echo("No IKE crypto profiles found in file", err=True)
            raise typer.Exit(code=1)
        profiles = data["ike_crypto_profiles"]
        if not isinstance(profiles, list):
            profiles = [profiles]
        created_count = 0
        for profile_data in profiles:
            try:
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
                created_count += 1
                container = validated_profile.folder or validated_profile.snippet or validated_profile.device
                typer.echo(f"Created IKE crypto profile: {validated_profile.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing IKE crypto profile: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count} IKE crypto profiles")
    except Exception as e:
        typer.echo(f"Error loading IKE crypto profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("ike-crypto-profile", help="Create or update an IKE crypto profile.")
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
    try:
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
            typer.echo(f"Created IKE crypto profile: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated IKE crypto profile: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for IKE crypto profile: {name} in {location_value}")
    except Exception as e:
        typer.echo(f"Error creating/updating IKE crypto profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("ike-crypto-profile", help="Show IKE crypto profile details.")
def show_ike_crypto_profile(
    name: str = typer.Option(None, "--name", help="Name of specific IKE crypto profile to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show IKE crypto profile details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            profile = scm_client.get_ike_crypto_profile(name=name, folder=folder, snippet=snippet, device=device)
            if not profile:
                typer.echo(f"IKE crypto profile '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nIKE Crypto Profile: {profile['name']}")
            typer.echo("=" * 60)
            location = profile.get("folder") or profile.get("snippet") or profile.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if profile.get("hash"):
                typer.echo(f"Hash: {', '.join(profile['hash'])}")
            if profile.get("dh_group"):
                typer.echo(f"DH Group: {', '.join(profile['dh_group'])}")
            if profile.get("encryption"):
                typer.echo(f"Encryption: {', '.join(profile['encryption'])}")
            lifetime = profile.get("lifetime")
            if lifetime and isinstance(lifetime, dict):
                for unit, value in lifetime.items():
                    typer.echo(f"Lifetime: {value} {unit}")
            if profile.get("authentication_multiple") is not None:
                typer.echo(f"Authentication Multiple: {profile['authentication_multiple']}")
            if profile.get("id"):
                typer.echo(f"\nID: {profile['id']}")
            return profile
        else:
            profiles = scm_client.list_ike_crypto_profiles(folder=folder, snippet=snippet, device=device)
            if not profiles:
                typer.echo("No IKE crypto profiles found")
                return
            typer.echo("\nIKE Crypto Profiles:")
            typer.echo("-" * 80)
            for profile in profiles:
                location = profile.get("folder") or profile.get("snippet") or profile.get("device", "N/A")
                typer.echo(f"Name: {profile.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                typer.echo(f"  Hash: {', '.join(profile.get('hash', []))}")
                typer.echo(f"  DH Group: {', '.join(profile.get('dh_group', []))}")
                typer.echo(f"  Encryption: {', '.join(profile.get('encryption', []))}")
                lifetime = profile.get("lifetime")
                if lifetime and isinstance(lifetime, dict):
                    for unit, value in lifetime.items():
                        typer.echo(f"  Lifetime: {value} {unit}")
                if profile.get("authentication_multiple") is not None:
                    typer.echo(f"  Authentication Multiple: {profile['authentication_multiple']}")
                if profile.get("id"):
                    typer.echo(f"  ID: {profile['id']}")
                typer.echo("-" * 80)
            return profiles
    except Exception as e:
        typer.echo(f"Error showing IKE crypto profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# AGGREGATE INTERFACE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("aggregate-interface", help="Export aggregate interfaces to a YAML file.")
def backup_aggregate_interface(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export aggregate interfaces from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving aggregate interfaces from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        interfaces = scm_client.list_aggregate_interfaces(**kwargs)
        if not interfaces:
            typer.echo(f"No aggregate interfaces found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"aggregate_interfaces": interfaces}
        filename = Path(file or get_default_backup_filename("aggregate-interface", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(interfaces)} aggregate interfaces to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up aggregate interfaces: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("aggregate-interface", help="Delete an aggregate interface.")
def delete_aggregate_interface(
    name: str = typer.Argument(..., help="Name of the aggregate interface to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete an aggregate interface."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        iface = scm_client.get_aggregate_interface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            typer.echo(f"Aggregate interface '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete aggregate interface '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_aggregate_interface(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted aggregate interface: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting aggregate interface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("aggregate-interface", help="Load aggregate interfaces from a YAML file.")
def load_aggregate_interface(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load aggregate interfaces from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "aggregate_interfaces" not in data:
            typer.echo("No aggregate interfaces found in file", err=True)
            raise typer.Exit(code=1)
        interfaces = data["aggregate_interfaces"]
        if not isinstance(interfaces, list):
            interfaces = [interfaces]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(interfaces))
            return None

        created_count = 0
        updated_count = 0
        no_change_count = 0
        for iface_data in interfaces:
            try:
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
                action = result.pop("__action__", "created")
                container = validated_iface.folder or validated_iface.snippet or validated_iface.device
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created aggregate interface: {validated_iface.name} in {container}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated aggregate interface: {validated_iface.name} in {container}")
                else:
                    no_change_count += 1
                    typer.echo(f"No changes needed for aggregate interface: {validated_iface.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing aggregate interface: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count + updated_count + no_change_count} aggregate interfaces")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")
        if no_change_count > 0:
            typer.echo(f"  - No change: {no_change_count}")
    except Exception as e:
        typer.echo(f"Error loading aggregate interfaces: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("aggregate-interface", help="Create or update an aggregate interface.")
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
    try:
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
            typer.echo(f"Created aggregate interface: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated aggregate interface: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for aggregate interface: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating aggregate interface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("aggregate-interface", help="Show aggregate interface details.")
def show_aggregate_interface(
    name: str = typer.Option(None, "--name", help="Name of specific aggregate interface to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show aggregate interface details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            iface = scm_client.get_aggregate_interface(name=name, folder=folder, snippet=snippet, device=device)
            if not iface:
                typer.echo(f"Aggregate interface '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nAggregate Interface: {iface['name']}")
            typer.echo("=" * 60)
            location = iface.get("folder") or iface.get("snippet") or iface.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if iface.get("comment"):
                typer.echo(f"Comment: {iface['comment']}")
            # Interface mode
            if iface.get("layer3"):
                typer.echo("Mode: Layer3")
                l3 = iface["layer3"]
                if l3.get("mtu"):
                    typer.echo(f"  MTU: {l3['mtu']}")
                if l3.get("ip"):
                    for ip_entry in l3["ip"]:
                        typer.echo(f"  IP: {ip_entry.get('name', 'N/A')}")
                if l3.get("interface_management_profile"):
                    typer.echo(f"  Management Profile: {l3['interface_management_profile']}")
                if l3.get("dhcp_client"):
                    typer.echo("  DHCP Client: Enabled")
            elif iface.get("layer2"):
                typer.echo("Mode: Layer2")
                l2 = iface["layer2"]
                if l2.get("vlan_tag"):
                    typer.echo(f"  VLAN Tag: {l2['vlan_tag']}")
            if iface.get("id"):
                typer.echo(f"\nID: {iface['id']}")
            return iface
        else:
            interfaces = scm_client.list_aggregate_interfaces(folder=folder, snippet=snippet, device=device)
            if not interfaces:
                typer.echo("No aggregate interfaces found")
                return
            typer.echo("\nAggregate Interfaces:")
            typer.echo("-" * 80)
            for iface in interfaces:
                location = iface.get("folder") or iface.get("snippet") or iface.get("device", "N/A")
                typer.echo(f"Name: {iface.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if iface.get("comment"):
                    typer.echo(f"  Comment: {iface['comment']}")
                if iface.get("layer3"):
                    typer.echo("  Mode: Layer3")
                    if iface["layer3"].get("mtu"):
                        typer.echo(f"  MTU: {iface['layer3']['mtu']}")
                elif iface.get("layer2"):
                    typer.echo("  Mode: Layer2")
                    if iface["layer2"].get("vlan_tag"):
                        typer.echo(f"  VLAN Tag: {iface['layer2']['vlan_tag']}")
                if iface.get("id"):
                    typer.echo(f"  ID: {iface['id']}")
                typer.echo("-" * 80)
            return interfaces
    except Exception as e:
        typer.echo(f"Error showing aggregate interface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# IKE GATEWAY COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("ike-gateway", help="Export IKE gateways to a YAML file.")
def backup_ike_gateway(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export IKE gateways from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving IKE gateways from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        gateways = scm_client.list_ike_gateways(**kwargs)
        if not gateways:
            typer.echo(f"No IKE gateways found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"ike_gateways": gateways}
        filename = Path(file or get_default_backup_filename("ike-gateway", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(gateways)} IKE gateways to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up IKE gateways: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("ike-gateway", help="Delete an IKE gateway.")
def delete_ike_gateway(
    name: str = typer.Argument(..., help="Name of the IKE gateway to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete an IKE gateway."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        gateway = scm_client.get_ike_gateway(name=name, folder=folder, snippet=snippet, device=device)
        if not gateway:
            typer.echo(f"IKE gateway '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete IKE gateway '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_ike_gateway(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted IKE gateway: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting IKE gateway: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("ike-gateway", help="Load IKE gateways from a YAML file.")
def load_ike_gateway(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load IKE gateways from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "ike_gateways" not in data:
            typer.echo("No IKE gateways found in file", err=True)
            raise typer.Exit(code=1)
        gateways = data["ike_gateways"]
        if not isinstance(gateways, list):
            gateways = [gateways]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(gateways))
            return None

        created_count = 0
        updated_count = 0
        no_change_count = 0
        for gateway_data in gateways:
            try:
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
                action = result.pop("__action__", "created")
                container = validated_gw.folder or validated_gw.snippet or validated_gw.device
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created IKE gateway: {validated_gw.name} in {container}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated IKE gateway: {validated_gw.name} in {container}")
                else:
                    no_change_count += 1
                    typer.echo(f"No changes needed for IKE gateway: {validated_gw.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing IKE gateway: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count + updated_count + no_change_count} IKE gateways")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")
        if no_change_count > 0:
            typer.echo(f"  - No change: {no_change_count}")
    except Exception as e:
        typer.echo(f"Error loading IKE gateways: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("ike-gateway", help="Create or update an IKE gateway.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)

        # Build authentication
        if authentication_json:
            authentication = json.loads(authentication_json)
        elif pre_shared_key:
            authentication = {"pre_shared_key": {"key": pre_shared_key}}
        else:
            typer.echo("Error: --pre-shared-key or --authentication-json is required", err=True)
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
            typer.echo("Error: one of --peer-address-ip, --peer-address-fqdn, --peer-address-dynamic, or --peer-address-json is required", err=True)
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
            typer.echo(f"Created IKE gateway: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated IKE gateway: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for IKE gateway: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating IKE gateway: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("ike-gateway", help="Show IKE gateway details.")
def show_ike_gateway(
    name: str = typer.Option(None, "--name", help="Name of specific IKE gateway to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show IKE gateway details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            gateway = scm_client.get_ike_gateway(name=name, folder=folder, snippet=snippet, device=device)
            if not gateway:
                typer.echo(f"IKE gateway '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nIKE Gateway: {gateway['name']}")
            typer.echo("=" * 60)
            location = gateway.get("folder") or gateway.get("snippet") or gateway.get("device", "N/A")
            typer.echo(f"Location: {location}")
            # Authentication
            auth = gateway.get("authentication", {})
            if "pre_shared_key" in auth:
                typer.echo("Authentication: Pre-Shared Key")
            elif "certificate" in auth:
                typer.echo("Authentication: Certificate")
            # Peer address
            peer_addr = gateway.get("peer_address", {})
            if "ip" in peer_addr:
                typer.echo(f"Peer Address: {peer_addr['ip']}")
            elif "fqdn" in peer_addr:
                typer.echo(f"Peer Address (FQDN): {peer_addr['fqdn']}")
            elif "dynamic" in peer_addr:
                typer.echo("Peer Address: Dynamic")
            # Protocol
            proto = gateway.get("protocol", {})
            typer.echo(f"Protocol Version: {proto.get('version', 'N/A')}")
            if proto.get("ikev1") and proto["ikev1"].get("ike_crypto_profile"):
                typer.echo(f"IKEv1 Crypto Profile: {proto['ikev1']['ike_crypto_profile']}")
            if proto.get("ikev2") and proto["ikev2"].get("ike_crypto_profile"):
                typer.echo(f"IKEv2 Crypto Profile: {proto['ikev2']['ike_crypto_profile']}")
            # Peer/Local ID
            if gateway.get("peer_id"):
                typer.echo(f"Peer ID: {gateway['peer_id'].get('type', 'N/A')} = {gateway['peer_id'].get('id', 'N/A')}")
            if gateway.get("local_id"):
                typer.echo(f"Local ID: {gateway['local_id'].get('type', 'N/A')} = {gateway['local_id'].get('id', 'N/A')}")
            # Protocol common
            common = gateway.get("protocol_common", {})
            if common.get("nat_traversal"):
                typer.echo(f"NAT Traversal: {common['nat_traversal'].get('enable', False)}")
            if common.get("fragmentation"):
                typer.echo(f"Fragmentation: {common['fragmentation'].get('enable', False)}")
            if common.get("passive_mode") is not None:
                typer.echo(f"Passive Mode: {common['passive_mode']}")
            if gateway.get("id"):
                typer.echo(f"\nID: {gateway['id']}")
            return gateway
        else:
            gateways = scm_client.list_ike_gateways(folder=folder, snippet=snippet, device=device)
            if not gateways:
                typer.echo("No IKE gateways found")
                return
            typer.echo("\nIKE Gateways:")
            typer.echo("-" * 80)
            for gateway in gateways:
                location = gateway.get("folder") or gateway.get("snippet") or gateway.get("device", "N/A")
                typer.echo(f"Name: {gateway.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                auth = gateway.get("authentication", {})
                if "pre_shared_key" in auth:
                    typer.echo("  Authentication: Pre-Shared Key")
                elif "certificate" in auth:
                    typer.echo("  Authentication: Certificate")
                peer_addr = gateway.get("peer_address", {})
                if "ip" in peer_addr:
                    typer.echo(f"  Peer Address: {peer_addr['ip']}")
                elif "fqdn" in peer_addr:
                    typer.echo(f"  Peer Address (FQDN): {peer_addr['fqdn']}")
                elif "dynamic" in peer_addr:
                    typer.echo("  Peer Address: Dynamic")
                proto = gateway.get("protocol", {})
                typer.echo(f"  Protocol Version: {proto.get('version', 'N/A')}")
                if gateway.get("id"):
                    typer.echo(f"  ID: {gateway['id']}")
                typer.echo("-" * 80)
            return gateways
    except Exception as e:
        typer.echo(f"Error showing IKE gateway: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# SECURITY ZONE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("zone")
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

    try:
        # List all security zones with exact_match=True
        zones = scm_client.list_security_zones(folder=folder, snippet=snippet, device=device, exact_match=True)

        if not zones:
            typer.echo(f"No security zones found in {location_type} '{location_value}'")
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

        typer.echo(f"Successfully backed up {len(backup_data)} security zones to {file}")
        return file

    except NotImplementedError as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error backing up security zones: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("zone")
def delete_zone(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete a security zone.

    Example: scm delete network zone --folder Texas --name trust
    """
    try:
        # Call the SDK client to delete the zone
        result = scm_client.delete_zone(folder=folder, name=name)

        if result:
            typer.echo(f"Deleted zone: {name} from folder {folder}")
        else:
            typer.echo(f"Zone not found: {name} in folder {folder}", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting security zone: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("zone")
def load_security_zone(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load security zones from a YAML file.

    Example: scm load network zone --file security-zone-austin.yaml
    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(str(file), "security_zones")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["security_zones"]))
            return None

        # Apply each zone
        results = []
        for zone_data in config["security_zones"]:
            # Validate using the Pydantic model
            zone = Zone(**zone_data)

            # Convert to the SDK model and create the zone
            sdk_data = zone.to_sdk_model()
            result = scm_client.create_zone(
                folder=zone.folder,
                name=sdk_data["name"],
                mode=sdk_data["mode"],
                interfaces=sdk_data["interfaces"],
            )

            results.append(result)
            typer.echo(f"Applied zone: {result['name']} in folder {result['folder']}")

        return results
    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading security zones: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("zone")
def set_zone(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    mode: str = MODE_OPTION,
    interfaces: list[str] | None = INTERFACES_OPTION,
    enable_user_id: bool | None = ENABLE_USER_ID_OPTION,
):
    """Create or update a security zone.

    Example:
    -------
        scm set network zone --folder Texas --name trust --mode layer3 \
        --interfaces ["ethernet1/1"] --enable-user-id

    """
    try:
        # Validate mode parameter
        valid_modes = ["layer3", "layer2", "virtual-wire", "tap", "external", "tunnel"]
        if mode not in valid_modes:
            typer.echo(
                f"Error: Invalid mode '{mode}'. Must be one of: {', '.join(valid_modes)}",
                err=True,
            )
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
            # Add None defaults for optional fields
            snippet=None,
            device=None,
            enable_user_identification=enable_user_id,
            enable_device_identification=None,
        )

        # Call the SDK client
        # Convert to the SDK model
        sdk_model = zone.to_sdk_model()

        result = scm_client.create_zone(
            folder=zone.folder,
            name=zone.name,
            mode=sdk_model["mode"],
            interfaces=sdk_model["interfaces"],
            enable_user_identification=sdk_model.get("enable_user_identification"),
            enable_device_identification=sdk_model.get("enable_device_identification"),
        )

        action = result.get("__action__", "created")
        if action == "created":
            typer.echo(f"Created zone: {result['name']} in folder {result['folder']}")
        elif action == "updated":
            typer.echo(f"Updated zone: {result['name']} in folder {result['folder']}")
        elif action == "no_change":
            typer.echo(f"No changes needed for zone: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating security zone: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("zone")
def show_zone(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the security zone to show"),
):
    """Display security zones.

    Example:
    -------
        # List all security zones in a folder (default behavior)
        scm show network zone --folder Texas

        # Show a specific security zone by name
        scm show network zone --folder Texas --name trust

    """
    try:
        if name:
            # Get a specific security zone by name
            zone = scm_client.get_security_zone(folder=folder, name=name)

            typer.echo(f"\nSecurity Zone: {zone.get('name', 'N/A')}")
            typer.echo("=" * 80)

            # Display container location (folder, snippet, or device)
            if zone.get("folder"):
                typer.echo(f"Location: Folder '{zone['folder']}'")
            elif zone.get("snippet"):
                typer.echo(f"Location: Snippet '{zone['snippet']}'")
            elif zone.get("device"):
                typer.echo(f"Location: Device '{zone['device']}'")
            else:
                typer.echo("Location: N/A")

            # Display network configuration details
            network = zone.get("network", {})
            if network:
                # Determine and display the network type
                if network.get("layer3"):
                    typer.echo("Type: Layer 3")
                    typer.echo(f"Interfaces: {', '.join(network['layer3'])}")
                elif network.get("layer2"):
                    typer.echo("Type: Layer 2")
                    typer.echo(f"Interfaces: {', '.join(network['layer2'])}")
                elif network.get("virtual_wire"):
                    typer.echo("Type: Virtual Wire")
                    typer.echo(f"Interfaces: {', '.join(network['virtual_wire'])}")
                elif network.get("tap"):
                    typer.echo("Type: TAP")
                    typer.echo(f"Interfaces: {', '.join(network['tap'])}")
                elif network.get("external"):
                    typer.echo("Type: External")
                    typer.echo(f"Interfaces: {', '.join(network['external'])}")
                elif network.get("tunnel"):
                    typer.echo("Type: Tunnel")

                # Display zone protection profile if present
                if network.get("zone_protection_profile"):
                    typer.echo(f"Zone Protection Profile: {network['zone_protection_profile']}")

                # Display packet buffer protection if enabled
                if network.get("enable_packet_buffer_protection"):
                    typer.echo("Packet Buffer Protection: Enabled")

                # Display log setting if present
                if network.get("log_setting"):
                    typer.echo(f"Log Setting: {network['log_setting']}")

            # Display user/device identification settings
            if zone.get("enable_user_identification"):
                typer.echo("User Identification: Enabled")
            if zone.get("enable_device_identification"):
                typer.echo("Device Identification: Enabled")

            # Display DoS profile settings
            if zone.get("dos_profile"):
                typer.echo(f"DoS Profile: {zone['dos_profile']}")
            if zone.get("dos_log_setting"):
                typer.echo(f"DoS Log Setting: {zone['dos_log_setting']}")

            # Display user ACL if present
            user_acl = zone.get("user_acl", {})
            if user_acl:
                typer.echo("User Access Control List:")
                if user_acl.get("include_list"):
                    typer.echo(f"  Include: {', '.join(user_acl['include_list'])}")
                if user_acl.get("exclude_list"):
                    typer.echo(f"  Exclude: {', '.join(user_acl['exclude_list'])}")

            # Display device ACL if present
            device_acl = zone.get("device_acl", {})
            if device_acl:
                typer.echo("Device Access Control List:")
                if device_acl.get("include_list"):
                    typer.echo(f"  Include: {', '.join(device_acl['include_list'])}")
                if device_acl.get("exclude_list"):
                    typer.echo(f"  Exclude: {', '.join(device_acl['exclude_list'])}")

            # Display description if present
            if zone.get("description"):
                typer.echo(f"Description: {zone['description']}")

            # Display ID if present
            if zone.get("id"):
                typer.echo(f"ID: {zone['id']}")

            return zone

        else:
            # List all security zones in the specified folder (default behavior)
            zones = scm_client.list_security_zones(folder=folder)

            if not zones:
                typer.echo(f"No security zones found in folder '{folder}'")
                return None

            typer.echo(f"\nSecurity Zones in folder '{folder}':")
            typer.echo("=" * 80)

            for zone in zones:
                # Display zone information
                typer.echo(f"Name: {zone.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if zone.get("folder"):
                    typer.echo(f"  Location: Folder '{zone['folder']}'")
                elif zone.get("snippet"):
                    typer.echo(f"  Location: Snippet '{zone['snippet']}'")
                elif zone.get("device"):
                    typer.echo(f"  Location: Device '{zone['device']}'")
                else:
                    typer.echo("  Location: N/A")

                # Display network type and interfaces
                network = zone.get("network", {})
                if network:
                    # Check which type of network configuration is present
                    if network.get("layer3"):
                        typer.echo("  Type: Layer 3")
                        typer.echo(f"  Interfaces: {', '.join(network['layer3'])}")
                    elif network.get("layer2"):
                        typer.echo("  Type: Layer 2")
                        typer.echo(f"  Interfaces: {', '.join(network['layer2'])}")
                    elif network.get("virtual_wire"):
                        typer.echo("  Type: Virtual Wire")
                        typer.echo(f"  Interfaces: {', '.join(network['virtual_wire'])}")
                    elif network.get("tap"):
                        typer.echo("  Type: TAP")
                        typer.echo(f"  Interfaces: {', '.join(network['tap'])}")
                    elif network.get("external"):
                        typer.echo("  Type: External")
                        typer.echo(f"  Interfaces: {', '.join(network['external'])}")
                    elif network.get("tunnel"):
                        typer.echo("  Type: Tunnel")

                    # Display zone protection profile if present
                    if network.get("zone_protection_profile"):
                        typer.echo(f"  Zone Protection Profile: {network['zone_protection_profile']}")

                    # Display packet buffer protection if enabled
                    if network.get("enable_packet_buffer_protection"):
                        typer.echo("  Packet Buffer Protection: Enabled")

                    # Display log setting if present
                    if network.get("log_setting"):
                        typer.echo(f"  Log Setting: {network['log_setting']}")

                # Display user/device identification settings
                if zone.get("enable_user_identification"):
                    typer.echo("  User Identification: Enabled")
                if zone.get("enable_device_identification"):
                    typer.echo("  Device Identification: Enabled")

                # Display DoS profile settings
                if zone.get("dos_profile"):
                    typer.echo(f"  DoS Profile: {zone['dos_profile']}")
                if zone.get("dos_log_setting"):
                    typer.echo(f"  DoS Log Setting: {zone['dos_log_setting']}")

                # Display description if present
                if zone.get("description"):
                    typer.echo(f"  Description: {zone['description']}")

                # Display ID if present
                if zone.get("id"):
                    typer.echo(f"  ID: {zone['id']}")

                typer.echo("-" * 80)

            return zones

    except Exception as e:
        typer.echo(f"Error showing security zone: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# IPSEC CRYPTO PROFILE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("ipsec-crypto-profile")
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

    try:
        profiles = scm_client.list_ipsec_crypto_profiles(folder=folder, snippet=snippet, device=device, exact_match=True)

        if not profiles:
            typer.echo(f"No IPsec crypto profiles found in {location_type} '{location_value}'")
            return None

        backup_data = []
        for profile in profiles:
            profile_dict = profile.copy()
            profile_dict.pop("id", None)
            backup_data.append(profile_dict)

        yaml_data = {"ipsec_crypto_profiles": backup_data}

        with open(file, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} IPsec crypto profiles to {file}")
        return file

    except NotImplementedError as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error backing up IPsec crypto profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("ipsec-crypto-profile")
def delete_ipsec_crypto_profile(
    folder: str = IPSEC_FOLDER_OPTION,
    name: str = IPSEC_NAME_OPTION,
):
    """Delete an IPsec crypto profile.

    Example: scm delete network ipsec-crypto-profile --folder Texas --name my-profile
    """
    try:
        result = scm_client.delete_ipsec_crypto_profile(folder=folder, name=name)

        if result:
            typer.echo(f"Deleted IPsec crypto profile: {name} from folder {folder}")
        else:
            typer.echo(f"IPsec crypto profile not found: {name} in folder {folder}", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting IPsec crypto profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("ipsec-crypto-profile")
def load_ipsec_crypto_profile(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load IPsec crypto profiles from a YAML file.

    Example: scm load network ipsec-crypto-profile --file ipsec-profiles.yaml
    """
    try:
        config = load_from_yaml(str(file), "ipsec_crypto_profiles")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["ipsec_crypto_profiles"]))
            return None

        results = []
        for profile_data in config["ipsec_crypto_profiles"]:
            profile = IPSecCryptoProfile(**profile_data)
            sdk_data = profile.to_sdk_model()

            result = scm_client.create_ipsec_crypto_profile(
                folder=profile.folder or "Texas",
                name=sdk_data["name"],
                esp_encryption=sdk_data["esp"]["encryption"],
                esp_authentication=sdk_data["esp"]["authentication"],
                dh_group=sdk_data.get("dh_group", "group14"),
                lifetime=sdk_data.get("lifetime"),
                lifesize=sdk_data.get("lifesize"),
            )

            results.append(result)
            action = result.get("__action__", "applied")
            typer.echo(f"IPsec crypto profile '{result['name']}' {action} in folder {result.get('folder', 'N/A')}")

        return results
    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading IPsec crypto profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("ipsec-crypto-profile")
def set_ipsec_crypto_profile(
    folder: str = IPSEC_FOLDER_OPTION,
    name: str = IPSEC_NAME_OPTION,
    esp_encryption: list[str] = IPSEC_ESP_ENCRYPTION_OPTION,
    esp_authentication: list[str] = IPSEC_ESP_AUTHENTICATION_OPTION,
    dh_group: str = IPSEC_DH_GROUP_OPTION,
    lifetime_seconds: int | None = IPSEC_LIFETIME_SECONDS_OPTION,
    lifetime_hours: int | None = IPSEC_LIFETIME_HOURS_OPTION,
):
    """Create or update an IPsec crypto profile.

    Example:
    -------
        scm set network ipsec-crypto-profile --folder Texas --name my-profile \
        --esp-encryption aes-256-cbc --esp-authentication sha256 --dh-group group14

    """
    try:
        profile = IPSecCryptoProfile(
            folder=folder,
            snippet=None,
            device=None,
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
            name=name,
            esp_encryption=sdk_data["esp"]["encryption"],
            esp_authentication=sdk_data["esp"]["authentication"],
            dh_group=sdk_data.get("dh_group", "group14"),
            lifetime=sdk_data.get("lifetime"),
            lifesize=sdk_data.get("lifesize"),
        )

        action = result.get("__action__", "created")
        if action == "created":
            typer.echo(f"Created IPsec crypto profile: {result['name']} in folder {result.get('folder', folder)}")
        elif action == "updated":
            typer.echo(f"Updated IPsec crypto profile: {result['name']} in folder {result.get('folder', folder)}")
        elif action == "no_change":
            typer.echo(f"No changes needed for IPsec crypto profile: {result['name']} in folder {result.get('folder', folder)}")
        return result
    except Exception as e:
        typer.echo(f"Error creating IPsec crypto profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("ipsec-crypto-profile")
def show_ipsec_crypto_profile(
    folder: str = IPSEC_FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the IPsec crypto profile to show"),
):
    """Display IPsec crypto profiles.

    Example:
    -------
        # List all IPsec crypto profiles in a folder
        scm show network ipsec-crypto-profile --folder Texas

        # Show a specific IPsec crypto profile
        scm show network ipsec-crypto-profile --folder Texas --name my-profile

    """
    try:
        if name:
            profile = scm_client.get_ipsec_crypto_profile(folder=folder, name=name)

            typer.echo(f"\nIPsec Crypto Profile: {profile.get('name', 'N/A')}")
            typer.echo("=" * 80)

            if profile.get("folder"):
                typer.echo(f"Location: Folder '{profile['folder']}'")

            # Display ESP config
            esp = profile.get("esp", {})
            if esp:
                typer.echo(f"ESP Encryption: {', '.join(esp.get('encryption', []))}")
                typer.echo(f"ESP Authentication: {', '.join(esp.get('authentication', []))}")

            if profile.get("dh_group"):
                typer.echo(f"DH Group: {profile['dh_group']}")

            # Display lifetime
            lifetime = profile.get("lifetime", {})
            if lifetime:
                for unit, value in lifetime.items():
                    typer.echo(f"Lifetime: {value} {unit}")

            # Display lifesize
            lifesize = profile.get("lifesize", {})
            if lifesize:
                for unit, value in lifesize.items():
                    typer.echo(f"Lifesize: {value} {unit.upper()}")

            if profile.get("id"):
                typer.echo(f"ID: {profile['id']}")

            return profile

        else:
            profiles = scm_client.list_ipsec_crypto_profiles(folder=folder)

            if not profiles:
                typer.echo(f"No IPsec crypto profiles found in folder '{folder}'")
                return None

            typer.echo(f"\nIPsec Crypto Profiles in folder '{folder}':")
            typer.echo("=" * 80)

            for profile in profiles:
                typer.echo(f"Name: {profile.get('name', 'N/A')}")

                if profile.get("folder"):
                    typer.echo(f"  Location: Folder '{profile['folder']}'")

                esp = profile.get("esp", {})
                if esp:
                    typer.echo(f"  ESP Encryption: {', '.join(esp.get('encryption', []))}")
                    typer.echo(f"  ESP Authentication: {', '.join(esp.get('authentication', []))}")

                if profile.get("dh_group"):
                    typer.echo(f"  DH Group: {profile['dh_group']}")

                lifetime = profile.get("lifetime", {})
                if lifetime:
                    for unit, value in lifetime.items():
                        typer.echo(f"  Lifetime: {value} {unit}")

                lifesize = profile.get("lifesize", {})
                if lifesize:
                    for unit, value in lifesize.items():
                        typer.echo(f"  Lifesize: {value} {unit.upper()}")

                if profile.get("id"):
                    typer.echo(f"  ID: {profile['id']}")

                typer.echo("-" * 80)

            return profiles

    except Exception as e:
        typer.echo(f"Error showing IPsec crypto profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# NAT RULE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("nat-rule")
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

    try:
        nat_rules = scm_client.list_nat_rules(folder=folder, snippet=snippet, device=device, exact_match=True)

        if not nat_rules:
            typer.echo(f"No NAT rules found in {location_type} '{location_value}'")
            return None

        backup_data = []
        for rule in nat_rules:
            rule_dict = rule.copy()
            rule_dict.pop("id", None)
            backup_data.append(rule_dict)

        yaml_data = {"nat_rules": backup_data}

        with open(file, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} NAT rules to {file}")
        return file

    except NotImplementedError as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error backing up NAT rules: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("nat-rule")
def delete_nat_rule(
    folder: str = NAT_FOLDER_OPTION,
    name: str = NAT_NAME_OPTION,
):
    """Delete a NAT rule.

    Example: scm delete network nat-rule --folder Texas --name outbound-nat
    """
    try:
        result = scm_client.delete_nat_rule(folder=folder, name=name)

        if result:
            typer.echo(f"Deleted NAT rule: {name} from folder {folder}")
        else:
            typer.echo(f"NAT rule not found: {name} in folder {folder}", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting NAT rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("nat-rule")
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
    try:
        # Validate container override parameters
        if sum(1 for x in [folder, snippet, device] if x is not None) > 1:
            typer.echo(
                "Error: Only one of --folder, --snippet, or --device can be specified",
                err=True,
            )
            raise typer.Exit(code=1)

        if not file.exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)

        with open(file) as f:
            raw_data = yaml.safe_load(f)

        if not raw_data or "nat_rules" not in raw_data:
            typer.echo("No NAT rules found in file", err=True)
            raise typer.Exit(code=1)

        nat_rules = raw_data["nat_rules"]
        if not isinstance(nat_rules, list):
            nat_rules = [nat_rules]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(nat_rules))
            return None

        results: list[dict[str, Any]] = []
        created_count = 0
        updated_count = 0
        no_change_count = 0

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
                typer.echo(
                    f"Error processing NAT rule '{rule_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                continue

        typer.echo(f"Successfully processed {len(results)} NAT rule(s):")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")
        if no_change_count > 0:
            typer.echo(f"  - No change: {no_change_count}")

        return results

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading NAT rules: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("nat-rule")
def set_nat_rule(
    folder: str = NAT_FOLDER_OPTION,
    name: str = NAT_NAME_OPTION,
    description: str | None = NAT_DESCRIPTION_OPTION,
    tag: list[str] | None = NAT_TAG_OPTION,
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
        scm set network nat-rule --folder Texas --name outbound-nat \
        --from-zone trust --to-zone untrust --source any --destination any \
        --source-translation '{"dynamic_ip_and_port": {"type": "dynamic_ip_and_port", "translated_address": ["10.0.0.1"]}}'

    """
    try:
        # Parse JSON strings for translation configs
        src_translation = json.loads(source_translation) if source_translation else None
        dst_translation = json.loads(destination_translation) if destination_translation else None

        result = scm_client.create_nat_rule(
            folder=folder,
            name=name,
            description=description,
            tag=tag,
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
            typer.echo(f"Created NAT rule: {result['name']} in folder {folder}")
        elif action == "updated":
            typer.echo(f"Updated NAT rule: {result['name']} in folder {folder}")
        elif action == "no_change":
            typer.echo(f"No changes needed for NAT rule: {result['name']} in folder {folder}")

        return result
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating NAT rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("nat-rule")
def show_nat_rule(
    folder: str = NAT_FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the NAT rule to show"),
):
    """Display NAT rules.

    Example:
    -------
        # List all NAT rules in a folder
        scm show network nat-rule --folder Texas

        # Show a specific NAT rule by name
        scm show network nat-rule --folder Texas --name outbound-nat

    """
    try:
        if name:
            rule = scm_client.get_nat_rule(folder=folder, name=name)

            typer.echo(f"\nNAT Rule: {rule.get('name', 'N/A')}")
            typer.echo("=" * 80)

            if rule.get("folder"):
                typer.echo(f"Location: Folder '{rule['folder']}'")
            elif rule.get("snippet"):
                typer.echo(f"Location: Snippet '{rule['snippet']}'")
            elif rule.get("device"):
                typer.echo(f"Location: Device '{rule['device']}'")

            if rule.get("description"):
                typer.echo(f"Description: {rule['description']}")
            typer.echo(f"NAT Type: {rule.get('nat_type', 'ipv4')}")
            typer.echo(f"From: {', '.join(rule.get('from_', ['any']))}")
            typer.echo(f"To: {', '.join(rule.get('to_', ['any']))}")
            typer.echo(f"Source: {', '.join(rule.get('source', ['any']))}")
            typer.echo(f"Destination: {', '.join(rule.get('destination', ['any']))}")
            typer.echo(f"Service: {rule.get('service', 'any')}")

            if rule.get("source_translation"):
                typer.echo(f"Source Translation: {json.dumps(rule['source_translation'], indent=2)}")
            if rule.get("destination_translation"):
                typer.echo(f"Destination Translation: {json.dumps(rule['destination_translation'], indent=2)}")
            if rule.get("disabled"):
                typer.echo("Status: Disabled")
            if rule.get("tag"):
                typer.echo(f"Tags: {', '.join(rule['tag'])}")
            if rule.get("id"):
                typer.echo(f"ID: {rule['id']}")

            return rule

        else:
            rules = scm_client.list_nat_rules(folder=folder)

            if not rules:
                typer.echo(f"No NAT rules found in folder '{folder}'")
                return None

            typer.echo(f"\nNAT Rules in folder '{folder}':")
            typer.echo("=" * 80)

            for rule in rules:
                typer.echo(f"Name: {rule.get('name', 'N/A')}")

                if rule.get("folder"):
                    typer.echo(f"  Location: Folder '{rule['folder']}'")
                elif rule.get("snippet"):
                    typer.echo(f"  Location: Snippet '{rule['snippet']}'")
                elif rule.get("device"):
                    typer.echo(f"  Location: Device '{rule['device']}'")

                if rule.get("description"):
                    typer.echo(f"  Description: {rule['description']}")
                typer.echo(f"  NAT Type: {rule.get('nat_type', 'ipv4')}")
                typer.echo(f"  From: {', '.join(rule.get('from_', ['any']))}")
                typer.echo(f"  To: {', '.join(rule.get('to_', ['any']))}")
                typer.echo(f"  Source: {', '.join(rule.get('source', ['any']))}")
                typer.echo(f"  Destination: {', '.join(rule.get('destination', ['any']))}")
                typer.echo(f"  Service: {rule.get('service', 'any')}")

                if rule.get("source_translation"):
                    typer.echo(f"  Source Translation: {json.dumps(rule['source_translation'])}")
                if rule.get("destination_translation"):
                    typer.echo(f"  Destination Translation: {json.dumps(rule['destination_translation'])}")
                if rule.get("disabled"):
                    typer.echo("  Status: Disabled")
                if rule.get("tag"):
                    typer.echo(f"  Tags: {', '.join(rule['tag'])}")
                if rule.get("id"):
                    typer.echo(f"  ID: {rule['id']}")

                typer.echo("-" * 80)

            return rules

    except Exception as e:
        typer.echo(f"Error showing NAT rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# DHCP INTERFACE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("dhcp-interface", help="Export DHCP interfaces to a YAML file.")
def backup_dhcp_interface(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export DHCP interfaces from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving DHCP interfaces from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        interfaces = scm_client.list_dhcp_interfaces(**kwargs)
        if not interfaces:
            typer.echo(f"No DHCP interfaces found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"dhcp_interfaces": interfaces}
        filename = Path(file or get_default_backup_filename("dhcp-interface", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(interfaces)} DHCP interfaces to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up DHCP interfaces: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("dhcp-interface", help="Delete a DHCP interface.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        iface = scm_client.get_dhcp_interface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            typer.echo(f"DHCP interface '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete DHCP interface '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_dhcp_interface(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted DHCP interface: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting DHCP interface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("dhcp-interface", help="Load DHCP interfaces from a YAML file.")
def load_dhcp_interface(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load DHCP interfaces from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "dhcp_interfaces" not in data:
            typer.echo("No DHCP interfaces found in file", err=True)
            raise typer.Exit(code=1)
        interfaces = data["dhcp_interfaces"]
        if not isinstance(interfaces, list):
            interfaces = [interfaces]
        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(interfaces))
            return None
        created_count = 0
        updated_count = 0
        no_change_count = 0
        for iface_data in interfaces:
            try:
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
                action = result.pop("__action__", "created")
                container = validated_iface.folder or validated_iface.snippet or validated_iface.device
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created DHCP interface: {validated_iface.name} in {container}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated DHCP interface: {validated_iface.name} in {container}")
                else:
                    no_change_count += 1
                    typer.echo(f"No changes needed for DHCP interface: {validated_iface.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing DHCP interface: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count + updated_count + no_change_count} DHCP interfaces")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")
        if no_change_count > 0:
            typer.echo(f"  - No change: {no_change_count}")
    except Exception as e:
        typer.echo(f"Error loading DHCP interfaces: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("dhcp-interface", help="Create or update a DHCP interface.")
def set_dhcp_interface(
    name: str = typer.Argument(..., help="Name of the DHCP interface"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    server_json: str = typer.Option(None, "--server-json", help="DHCP server config as JSON"),
    relay_json: str = typer.Option(None, "--relay-json", help="DHCP relay config as JSON"),
) -> None:
    """Create or update a DHCP interface."""
    try:
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
            typer.echo(f"Created DHCP interface: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated DHCP interface: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for DHCP interface: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating DHCP interface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("dhcp-interface", help="Show DHCP interface details.")
def show_dhcp_interface(
    name: str = typer.Option(None, "--name", help="Name of specific DHCP interface to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show DHCP interface details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            iface = scm_client.get_dhcp_interface(name=name, folder=folder, snippet=snippet, device=device)
            if not iface:
                typer.echo(f"DHCP interface '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nDHCP Interface: {iface['name']}")
            typer.echo("=" * 60)
            location = iface.get("folder") or iface.get("snippet") or iface.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if iface.get("server"):
                typer.echo(f"Server: {json.dumps(iface['server'])}")
            if iface.get("relay"):
                typer.echo(f"Relay: {json.dumps(iface['relay'])}")
            if iface.get("id"):
                typer.echo(f"\nID: {iface['id']}")
            return iface
        else:
            interfaces = scm_client.list_dhcp_interfaces(folder=folder, snippet=snippet, device=device)
            if not interfaces:
                typer.echo("No DHCP interfaces found")
                return
            typer.echo("\nDHCP Interfaces:")
            typer.echo("-" * 80)
            for iface in interfaces:
                location = iface.get("folder") or iface.get("snippet") or iface.get("device", "N/A")
                typer.echo(f"Name: {iface.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if iface.get("server"):
                    typer.echo("  Type: Server")
                elif iface.get("relay"):
                    typer.echo("  Type: Relay")
                if iface.get("id"):
                    typer.echo(f"  ID: {iface['id']}")
                typer.echo("-" * 80)
            return interfaces
    except Exception as e:
        typer.echo(f"Error showing DHCP interface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# ETHERNET INTERFACE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("ethernet-interface", help="Export ethernet interfaces to a YAML file.")
def backup_ethernet_interface(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export ethernet interfaces from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving ethernet interfaces from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        interfaces = scm_client.list_ethernet_interfaces(**kwargs)
        if not interfaces:
            typer.echo(f"No ethernet interfaces found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"ethernet_interfaces": interfaces}
        filename = Path(file or get_default_backup_filename("ethernet-interface", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(interfaces)} ethernet interfaces to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up ethernet interfaces: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("ethernet-interface", help="Delete an ethernet interface.")
def delete_ethernet_interface(
    name: str = typer.Argument(..., help="Name of the ethernet interface to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete an ethernet interface."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        iface = scm_client.get_ethernet_interface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            typer.echo(f"Ethernet interface '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete ethernet interface '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_ethernet_interface(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted ethernet interface: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting ethernet interface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("ethernet-interface", help="Load ethernet interfaces from a YAML file.")
def load_ethernet_interface(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load ethernet interfaces from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "ethernet_interfaces" not in data:
            typer.echo("No ethernet interfaces found in file", err=True)
            raise typer.Exit(code=1)
        interfaces = data["ethernet_interfaces"]
        if not isinstance(interfaces, list):
            interfaces = [interfaces]
        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(interfaces))
            return None
        created_count = 0
        updated_count = 0
        no_change_count = 0
        for iface_data in interfaces:
            try:
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
                action = result.pop("__action__", "created")
                container = validated_iface.folder or validated_iface.snippet or validated_iface.device
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created ethernet interface: {validated_iface.name} in {container}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated ethernet interface: {validated_iface.name} in {container}")
                else:
                    no_change_count += 1
                    typer.echo(f"No changes needed for ethernet interface: {validated_iface.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing ethernet interface: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count + updated_count + no_change_count} ethernet interfaces")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")
        if no_change_count > 0:
            typer.echo(f"  - No change: {no_change_count}")
    except Exception as e:
        typer.echo(f"Error loading ethernet interfaces: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("ethernet-interface", help="Create or update an ethernet interface.")
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
    try:
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
            typer.echo(f"Created ethernet interface: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated ethernet interface: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for ethernet interface: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating ethernet interface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("ethernet-interface", help="Show ethernet interface details.")
def show_ethernet_interface(
    name: str = typer.Option(None, "--name", help="Name of specific ethernet interface to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show ethernet interface details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            iface = scm_client.get_ethernet_interface(name=name, folder=folder, snippet=snippet, device=device)
            if not iface:
                typer.echo(f"Ethernet interface '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nEthernet Interface: {iface['name']}")
            typer.echo("=" * 60)
            location = iface.get("folder") or iface.get("snippet") or iface.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if iface.get("comment"):
                typer.echo(f"Comment: {iface['comment']}")
            if iface.get("layer3"):
                typer.echo("Mode: Layer3")
                l3 = iface["layer3"]
                if l3.get("mtu"):
                    typer.echo(f"  MTU: {l3['mtu']}")
                if l3.get("ip"):
                    for ip_entry in l3["ip"]:
                        typer.echo(f"  IP: {ip_entry.get('name', 'N/A')}")
            elif iface.get("layer2"):
                typer.echo("Mode: Layer2")
                l2 = iface["layer2"]
                if l2.get("vlan_tag"):
                    typer.echo(f"  VLAN Tag: {l2['vlan_tag']}")
            elif iface.get("tap"):
                typer.echo("Mode: TAP")
            if iface.get("id"):
                typer.echo(f"\nID: {iface['id']}")
            return iface
        else:
            interfaces = scm_client.list_ethernet_interfaces(folder=folder, snippet=snippet, device=device)
            if not interfaces:
                typer.echo("No ethernet interfaces found")
                return
            typer.echo("\nEthernet Interfaces:")
            typer.echo("-" * 80)
            for iface in interfaces:
                location = iface.get("folder") or iface.get("snippet") or iface.get("device", "N/A")
                typer.echo(f"Name: {iface.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if iface.get("comment"):
                    typer.echo(f"  Comment: {iface['comment']}")
                if iface.get("layer3"):
                    typer.echo("  Mode: Layer3")
                elif iface.get("layer2"):
                    typer.echo("  Mode: Layer2")
                elif iface.get("tap"):
                    typer.echo("  Mode: TAP")
                if iface.get("id"):
                    typer.echo(f"  ID: {iface['id']}")
                typer.echo("-" * 80)
            return interfaces
    except Exception as e:
        typer.echo(f"Error showing ethernet interface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# LAYER2 SUBINTERFACE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("layer2-subinterface", help="Export layer2 subinterfaces to a YAML file.")
def backup_layer2_subinterface(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export layer2 subinterfaces from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving layer2 subinterfaces from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        interfaces = scm_client.list_layer2_subinterfaces(**kwargs)
        if not interfaces:
            typer.echo(f"No layer2 subinterfaces found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"layer2_subinterfaces": interfaces}
        filename = Path(file or get_default_backup_filename("layer2-subinterface", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(interfaces)} layer2 subinterfaces to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up layer2 subinterfaces: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("layer2-subinterface", help="Delete a layer2 subinterface.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        iface = scm_client.get_layer2_subinterface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            typer.echo(f"Layer2 subinterface '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete layer2 subinterface '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_layer2_subinterface(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted layer2 subinterface: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting layer2 subinterface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("layer2-subinterface", help="Load layer2 subinterfaces from a YAML file.")
def load_layer2_subinterface(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load layer2 subinterfaces from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "layer2_subinterfaces" not in data:
            typer.echo("No layer2 subinterfaces found in file", err=True)
            raise typer.Exit(code=1)
        interfaces = data["layer2_subinterfaces"]
        if not isinstance(interfaces, list):
            interfaces = [interfaces]
        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(interfaces))
            return None
        created_count = 0
        updated_count = 0
        no_change_count = 0
        for iface_data in interfaces:
            try:
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
                action = result.pop("__action__", "created")
                container = validated_iface.folder or validated_iface.snippet or validated_iface.device
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created layer2 subinterface: {validated_iface.name} in {container}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated layer2 subinterface: {validated_iface.name} in {container}")
                else:
                    no_change_count += 1
                    typer.echo(f"No changes needed for layer2 subinterface: {validated_iface.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing layer2 subinterface: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count + updated_count + no_change_count} layer2 subinterfaces")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")
        if no_change_count > 0:
            typer.echo(f"  - No change: {no_change_count}")
    except Exception as e:
        typer.echo(f"Error loading layer2 subinterfaces: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("layer2-subinterface", help="Create or update a layer2 subinterface.")
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
    try:
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
            typer.echo(f"Created layer2 subinterface: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated layer2 subinterface: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for layer2 subinterface: {name} in {location_value}")
    except Exception as e:
        typer.echo(f"Error creating/updating layer2 subinterface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("layer2-subinterface", help="Show layer2 subinterface details.")
def show_layer2_subinterface(
    name: str = typer.Option(None, "--name", help="Name of specific layer2 subinterface to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show layer2 subinterface details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            iface = scm_client.get_layer2_subinterface(name=name, folder=folder, snippet=snippet, device=device)
            if not iface:
                typer.echo(f"Layer2 subinterface '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nLayer2 Subinterface: {iface['name']}")
            typer.echo("=" * 60)
            location = iface.get("folder") or iface.get("snippet") or iface.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if iface.get("vlan_tag"):
                typer.echo(f"VLAN Tag: {iface['vlan_tag']}")
            if iface.get("parent_interface"):
                typer.echo(f"Parent Interface: {iface['parent_interface']}")
            if iface.get("comment"):
                typer.echo(f"Comment: {iface['comment']}")
            if iface.get("id"):
                typer.echo(f"\nID: {iface['id']}")
            return iface
        else:
            interfaces = scm_client.list_layer2_subinterfaces(folder=folder, snippet=snippet, device=device)
            if not interfaces:
                typer.echo("No layer2 subinterfaces found")
                return
            typer.echo("\nLayer2 Subinterfaces:")
            typer.echo("-" * 80)
            for iface in interfaces:
                location = iface.get("folder") or iface.get("snippet") or iface.get("device", "N/A")
                typer.echo(f"Name: {iface.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if iface.get("vlan_tag"):
                    typer.echo(f"  VLAN Tag: {iface['vlan_tag']}")
                if iface.get("parent_interface"):
                    typer.echo(f"  Parent: {iface['parent_interface']}")
                if iface.get("id"):
                    typer.echo(f"  ID: {iface['id']}")
                typer.echo("-" * 80)
            return interfaces
    except Exception as e:
        typer.echo(f"Error showing layer2 subinterface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# LAYER3 SUBINTERFACE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("layer3-subinterface", help="Export layer3 subinterfaces to a YAML file.")
def backup_layer3_subinterface(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export layer3 subinterfaces from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving layer3 subinterfaces from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        interfaces = scm_client.list_layer3_subinterfaces(**kwargs)
        if not interfaces:
            typer.echo(f"No layer3 subinterfaces found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"layer3_subinterfaces": interfaces}
        filename = Path(file or get_default_backup_filename("layer3-subinterface", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(interfaces)} layer3 subinterfaces to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up layer3 subinterfaces: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("layer3-subinterface", help="Delete a layer3 subinterface.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        iface = scm_client.get_layer3_subinterface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            typer.echo(f"Layer3 subinterface '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete layer3 subinterface '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_layer3_subinterface(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted layer3 subinterface: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting layer3 subinterface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("layer3-subinterface", help="Load layer3 subinterfaces from a YAML file.")
def load_layer3_subinterface(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load layer3 subinterfaces from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "layer3_subinterfaces" not in data:
            typer.echo("No layer3 subinterfaces found in file", err=True)
            raise typer.Exit(code=1)
        interfaces = data["layer3_subinterfaces"]
        if not isinstance(interfaces, list):
            interfaces = [interfaces]
        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(interfaces))
            return None
        created_count = 0
        updated_count = 0
        no_change_count = 0
        for iface_data in interfaces:
            try:
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
                action = result.pop("__action__", "created")
                container = validated_iface.folder or validated_iface.snippet or validated_iface.device
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created layer3 subinterface: {validated_iface.name} in {container}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated layer3 subinterface: {validated_iface.name} in {container}")
                else:
                    no_change_count += 1
                    typer.echo(f"No changes needed for layer3 subinterface: {validated_iface.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing layer3 subinterface: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count + updated_count + no_change_count} layer3 subinterfaces")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")
        if no_change_count > 0:
            typer.echo(f"  - No change: {no_change_count}")
    except Exception as e:
        typer.echo(f"Error loading layer3 subinterfaces: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("layer3-subinterface", help="Create or update a layer3 subinterface.")
def set_layer3_subinterface(
    name: str = typer.Argument(..., help="Name of the layer3 subinterface"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    tag: int = typer.Option(None, "--tag", help="VLAN tag (1-4096)"),
    parent_interface: str = typer.Option(None, "--parent-interface", help="Parent interface name"),
    comment: str = typer.Option(None, "--comment", help="Interface description/comment"),
    mtu: int = typer.Option(None, "--mtu", help="MTU (576-9216)"),
    ip_json: str = typer.Option(None, "--ip-json", help='Static IPs as JSON (e.g. \'[{"name": "10.0.0.1/24"}]\')'),
    dhcp_client_json: str = typer.Option(None, "--dhcp-client-json", help="DHCP client config as JSON"),
) -> None:
    """Create or update a layer3 subinterface."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        iface_data: dict[str, Any] = {"name": name, location_type: location_value}
        if tag is not None:
            iface_data["tag"] = tag
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
            typer.echo(f"Created layer3 subinterface: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated layer3 subinterface: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for layer3 subinterface: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating layer3 subinterface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("layer3-subinterface", help="Show layer3 subinterface details.")
def show_layer3_subinterface(
    name: str = typer.Option(None, "--name", help="Name of specific layer3 subinterface to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show layer3 subinterface details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            iface = scm_client.get_layer3_subinterface(name=name, folder=folder, snippet=snippet, device=device)
            if not iface:
                typer.echo(f"Layer3 subinterface '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nLayer3 Subinterface: {iface['name']}")
            typer.echo("=" * 60)
            location = iface.get("folder") or iface.get("snippet") or iface.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if iface.get("tag"):
                typer.echo(f"VLAN Tag: {iface['tag']}")
            if iface.get("mtu"):
                typer.echo(f"MTU: {iface['mtu']}")
            if iface.get("ip"):
                for ip_entry in iface["ip"]:
                    typer.echo(f"IP: {ip_entry.get('name', 'N/A')}")
            if iface.get("dhcp_client"):
                typer.echo("DHCP Client: Enabled")
            if iface.get("comment"):
                typer.echo(f"Comment: {iface['comment']}")
            if iface.get("id"):
                typer.echo(f"\nID: {iface['id']}")
            return iface
        else:
            interfaces = scm_client.list_layer3_subinterfaces(folder=folder, snippet=snippet, device=device)
            if not interfaces:
                typer.echo("No layer3 subinterfaces found")
                return
            typer.echo("\nLayer3 Subinterfaces:")
            typer.echo("-" * 80)
            for iface in interfaces:
                location = iface.get("folder") or iface.get("snippet") or iface.get("device", "N/A")
                typer.echo(f"Name: {iface.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if iface.get("tag"):
                    typer.echo(f"  VLAN Tag: {iface['tag']}")
                if iface.get("mtu"):
                    typer.echo(f"  MTU: {iface['mtu']}")
                if iface.get("id"):
                    typer.echo(f"  ID: {iface['id']}")
                typer.echo("-" * 80)
            return interfaces
    except Exception as e:
        typer.echo(f"Error showing layer3 subinterface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# LOOPBACK INTERFACE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("loopback-interface", help="Export loopback interfaces to a YAML file.")
def backup_loopback_interface(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export loopback interfaces from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving loopback interfaces from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        interfaces = scm_client.list_loopback_interfaces(**kwargs)
        if not interfaces:
            typer.echo(f"No loopback interfaces found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"loopback_interfaces": interfaces}
        filename = Path(file or get_default_backup_filename("loopback-interface", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(interfaces)} loopback interfaces to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up loopback interfaces: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("loopback-interface", help="Delete a loopback interface.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        iface = scm_client.get_loopback_interface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            typer.echo(f"Loopback interface '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete loopback interface '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_loopback_interface(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted loopback interface: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting loopback interface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("loopback-interface", help="Load loopback interfaces from a YAML file.")
def load_loopback_interface(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load loopback interfaces from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "loopback_interfaces" not in data:
            typer.echo("No loopback interfaces found in file", err=True)
            raise typer.Exit(code=1)
        interfaces = data["loopback_interfaces"]
        if not isinstance(interfaces, list):
            interfaces = [interfaces]
        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(interfaces))
            return None
        created_count = 0
        updated_count = 0
        no_change_count = 0
        for iface_data in interfaces:
            try:
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
                action = result.pop("__action__", "created")
                container = validated_iface.folder or validated_iface.snippet or validated_iface.device
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created loopback interface: {validated_iface.name} in {container}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated loopback interface: {validated_iface.name} in {container}")
                else:
                    no_change_count += 1
                    typer.echo(f"No changes needed for loopback interface: {validated_iface.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing loopback interface: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count + updated_count + no_change_count} loopback interfaces")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")
        if no_change_count > 0:
            typer.echo(f"  - No change: {no_change_count}")
    except Exception as e:
        typer.echo(f"Error loading loopback interfaces: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("loopback-interface", help="Create or update a loopback interface.")
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
    try:
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
            typer.echo(f"Created loopback interface: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated loopback interface: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for loopback interface: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating loopback interface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("loopback-interface", help="Show loopback interface details.")
def show_loopback_interface(
    name: str = typer.Option(None, "--name", help="Name of specific loopback interface to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show loopback interface details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            iface = scm_client.get_loopback_interface(name=name, folder=folder, snippet=snippet, device=device)
            if not iface:
                typer.echo(f"Loopback interface '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nLoopback Interface: {iface['name']}")
            typer.echo("=" * 60)
            location = iface.get("folder") or iface.get("snippet") or iface.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if iface.get("comment"):
                typer.echo(f"Comment: {iface['comment']}")
            if iface.get("mtu"):
                typer.echo(f"MTU: {iface['mtu']}")
            if iface.get("ip"):
                for ip_entry in iface["ip"]:
                    typer.echo(f"IP: {ip_entry.get('name', 'N/A')}")
            if iface.get("id"):
                typer.echo(f"\nID: {iface['id']}")
            return iface
        else:
            interfaces = scm_client.list_loopback_interfaces(folder=folder, snippet=snippet, device=device)
            if not interfaces:
                typer.echo("No loopback interfaces found")
                return
            typer.echo("\nLoopback Interfaces:")
            typer.echo("-" * 80)
            for iface in interfaces:
                location = iface.get("folder") or iface.get("snippet") or iface.get("device", "N/A")
                typer.echo(f"Name: {iface.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if iface.get("comment"):
                    typer.echo(f"  Comment: {iface['comment']}")
                if iface.get("ip"):
                    typer.echo(f"  IPs: {len(iface['ip'])}")
                if iface.get("id"):
                    typer.echo(f"  ID: {iface['id']}")
                typer.echo("-" * 80)
            return interfaces
    except Exception as e:
        typer.echo(f"Error showing loopback interface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# TUNNEL INTERFACE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("tunnel-interface", help="Export tunnel interfaces to a YAML file.")
def backup_tunnel_interface(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export tunnel interfaces from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving tunnel interfaces from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        interfaces = scm_client.list_tunnel_interfaces(**kwargs)
        if not interfaces:
            typer.echo(f"No tunnel interfaces found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"tunnel_interfaces": interfaces}
        filename = Path(file or get_default_backup_filename("tunnel-interface", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(interfaces)} tunnel interfaces to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up tunnel interfaces: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("tunnel-interface", help="Delete a tunnel interface.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        iface = scm_client.get_tunnel_interface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            typer.echo(f"Tunnel interface '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete tunnel interface '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_tunnel_interface(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted tunnel interface: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting tunnel interface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("tunnel-interface", help="Load tunnel interfaces from a YAML file.")
def load_tunnel_interface(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load tunnel interfaces from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "tunnel_interfaces" not in data:
            typer.echo("No tunnel interfaces found in file", err=True)
            raise typer.Exit(code=1)
        interfaces = data["tunnel_interfaces"]
        if not isinstance(interfaces, list):
            interfaces = [interfaces]
        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(interfaces))
            return None
        created_count = 0
        updated_count = 0
        no_change_count = 0
        for iface_data in interfaces:
            try:
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
                action = result.pop("__action__", "created")
                container = validated_iface.folder or validated_iface.snippet or validated_iface.device
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created tunnel interface: {validated_iface.name} in {container}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated tunnel interface: {validated_iface.name} in {container}")
                else:
                    no_change_count += 1
                    typer.echo(f"No changes needed for tunnel interface: {validated_iface.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing tunnel interface: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count + updated_count + no_change_count} tunnel interfaces")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")
        if no_change_count > 0:
            typer.echo(f"  - No change: {no_change_count}")
    except Exception as e:
        typer.echo(f"Error loading tunnel interfaces: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("tunnel-interface", help="Create or update a tunnel interface.")
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
    try:
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
            typer.echo(f"Created tunnel interface: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated tunnel interface: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for tunnel interface: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating tunnel interface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("tunnel-interface", help="Show tunnel interface details.")
def show_tunnel_interface(
    name: str = typer.Option(None, "--name", help="Name of specific tunnel interface to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show tunnel interface details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            iface = scm_client.get_tunnel_interface(name=name, folder=folder, snippet=snippet, device=device)
            if not iface:
                typer.echo(f"Tunnel interface '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nTunnel Interface: {iface['name']}")
            typer.echo("=" * 60)
            location = iface.get("folder") or iface.get("snippet") or iface.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if iface.get("comment"):
                typer.echo(f"Comment: {iface['comment']}")
            if iface.get("mtu"):
                typer.echo(f"MTU: {iface['mtu']}")
            if iface.get("ip"):
                for ip_entry in iface["ip"]:
                    typer.echo(f"IP: {ip_entry.get('name', 'N/A')}")
            if iface.get("id"):
                typer.echo(f"\nID: {iface['id']}")
            return iface
        else:
            interfaces = scm_client.list_tunnel_interfaces(folder=folder, snippet=snippet, device=device)
            if not interfaces:
                typer.echo("No tunnel interfaces found")
                return
            typer.echo("\nTunnel Interfaces:")
            typer.echo("-" * 80)
            for iface in interfaces:
                location = iface.get("folder") or iface.get("snippet") or iface.get("device", "N/A")
                typer.echo(f"Name: {iface.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if iface.get("comment"):
                    typer.echo(f"  Comment: {iface['comment']}")
                if iface.get("mtu"):
                    typer.echo(f"  MTU: {iface['mtu']}")
                if iface.get("id"):
                    typer.echo(f"  ID: {iface['id']}")
                typer.echo("-" * 80)
            return interfaces
    except Exception as e:
        typer.echo(f"Error showing tunnel interface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# VLAN INTERFACE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("vlan-interface", help="Export VLAN interfaces to a YAML file.")
def backup_vlan_interface(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export VLAN interfaces from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving VLAN interfaces from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        interfaces = scm_client.list_vlan_interfaces(**kwargs)
        if not interfaces:
            typer.echo(f"No VLAN interfaces found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"vlan_interfaces": interfaces}
        filename = Path(file or get_default_backup_filename("vlan-interface", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(interfaces)} VLAN interfaces to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up VLAN interfaces: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("vlan-interface", help="Delete a VLAN interface.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        iface = scm_client.get_vlan_interface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            typer.echo(f"VLAN interface '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete VLAN interface '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_vlan_interface(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted VLAN interface: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting VLAN interface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("vlan-interface", help="Load VLAN interfaces from a YAML file.")
def load_vlan_interface(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load VLAN interfaces from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "vlan_interfaces" not in data:
            typer.echo("No VLAN interfaces found in file", err=True)
            raise typer.Exit(code=1)
        interfaces = data["vlan_interfaces"]
        if not isinstance(interfaces, list):
            interfaces = [interfaces]
        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(interfaces))
            return None
        created_count = 0
        updated_count = 0
        no_change_count = 0
        for iface_data in interfaces:
            try:
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
                action = result.pop("__action__", "created")
                container = validated_iface.folder or validated_iface.snippet or validated_iface.device
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created VLAN interface: {validated_iface.name} in {container}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated VLAN interface: {validated_iface.name} in {container}")
                else:
                    no_change_count += 1
                    typer.echo(f"No changes needed for VLAN interface: {validated_iface.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing VLAN interface: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count + updated_count + no_change_count} VLAN interfaces")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")
        if no_change_count > 0:
            typer.echo(f"  - No change: {no_change_count}")
    except Exception as e:
        typer.echo(f"Error loading VLAN interfaces: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("vlan-interface", help="Create or update a VLAN interface.")
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
    try:
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
            typer.echo(f"Created VLAN interface: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated VLAN interface: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for VLAN interface: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating VLAN interface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("vlan-interface", help="Show VLAN interface details.")
def show_vlan_interface(
    name: str = typer.Option(None, "--name", help="Name of specific VLAN interface to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show VLAN interface details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            iface = scm_client.get_vlan_interface(name=name, folder=folder, snippet=snippet, device=device)
            if not iface:
                typer.echo(f"VLAN interface '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nVLAN Interface: {iface['name']}")
            typer.echo("=" * 60)
            location = iface.get("folder") or iface.get("snippet") or iface.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if iface.get("comment"):
                typer.echo(f"Comment: {iface['comment']}")
            if iface.get("vlan_tag"):
                typer.echo(f"VLAN Tag: {iface['vlan_tag']}")
            if iface.get("mtu"):
                typer.echo(f"MTU: {iface['mtu']}")
            if iface.get("ip"):
                for ip_entry in iface["ip"]:
                    typer.echo(f"IP: {ip_entry.get('name', 'N/A')}")
            if iface.get("dhcp_client"):
                typer.echo("DHCP Client: Enabled")
            if iface.get("id"):
                typer.echo(f"\nID: {iface['id']}")
            return iface
        else:
            interfaces = scm_client.list_vlan_interfaces(folder=folder, snippet=snippet, device=device)
            if not interfaces:
                typer.echo("No VLAN interfaces found")
                return
            typer.echo("\nVLAN Interfaces:")
            typer.echo("-" * 80)
            for iface in interfaces:
                location = iface.get("folder") or iface.get("snippet") or iface.get("device", "N/A")
                typer.echo(f"Name: {iface.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if iface.get("vlan_tag"):
                    typer.echo(f"  VLAN Tag: {iface['vlan_tag']}")
                if iface.get("comment"):
                    typer.echo(f"  Comment: {iface['comment']}")
                if iface.get("id"):
                    typer.echo(f"  ID: {iface['id']}")
                typer.echo("-" * 80)
            return interfaces
    except Exception as e:
        typer.echo(f"Error showing VLAN interface: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# BGP ADDRESS FAMILY PROFILE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("bgp-address-family-profile", help="Export BGP address family profiles to a YAML file.")
def backup_bgp_address_family_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export BGP address family profiles from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving BGP address family profiles from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        profiles = scm_client.list_bgp_address_family_profiles(**kwargs)
        if not profiles:
            typer.echo(f"No BGP address family profiles found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"bgp_address_family_profiles": profiles}
        filename = Path(file or get_default_backup_filename("bgp-address-family-profile", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(profiles)} BGP address family profiles to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up BGP address family profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("bgp-address-family-profile", help="Delete a BGP address family profile.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        profile = scm_client.get_bgp_address_family_profile(name=name, folder=folder, snippet=snippet, device=device)
        if not profile:
            typer.echo(f"BGP address family profile '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete BGP address family profile '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_bgp_address_family_profile(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted BGP address family profile: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting BGP address family profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("bgp-address-family-profile", help="Load BGP address family profiles from a YAML file.")
def load_bgp_address_family_profile(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load BGP address family profiles from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "bgp_address_family_profiles" not in data:
            typer.echo("No BGP address family profiles found in file", err=True)
            raise typer.Exit(code=1)
        profiles = data["bgp_address_family_profiles"]
        if not isinstance(profiles, list):
            profiles = [profiles]
        if dry_run:
            typer.echo("Dry run mode - no changes will be applied")
            for p in profiles:
                typer.echo(f"  Would process: {p.get('name', 'N/A')}")
            return
        created_count = 0
        updated_count = 0
        no_change_count = 0
        for profile_data in profiles:
            try:
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
                action = result.pop("__action__", "created")
                container = validated.folder or validated.snippet or validated.device
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created BGP address family profile: {validated.name} in {container}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated BGP address family profile: {validated.name} in {container}")
                else:
                    no_change_count += 1
                    typer.echo(f"No changes needed for BGP address family profile: {validated.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing BGP address family profile: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count + updated_count + no_change_count} BGP address family profiles")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")
        if no_change_count > 0:
            typer.echo(f"  - No change: {no_change_count}")
    except Exception as e:
        typer.echo(f"Error loading BGP address family profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("bgp-address-family-profile", help="Create or update a BGP address family profile.")
def set_bgp_address_family_profile(
    name: str = typer.Argument(..., help="Name of the BGP address family profile"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    ipv4_json: str = typer.Option(None, "--ipv4-json", help="IPv4 address family config as JSON"),
) -> None:
    """Create or update a BGP address family profile."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        profile_data: dict[str, Any] = {"name": name, location_type: location_value}
        if ipv4_json:
            profile_data["ipv4"] = json.loads(ipv4_json)
        validated = BgpAddressFamilyProfile(**profile_data)
        sdk_data = validated.to_sdk_model()
        result = scm_client.create_bgp_address_family_profile(sdk_data)
        action = result.pop("__action__", "created")
        if action == "created":
            typer.echo(f"Created BGP address family profile: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated BGP address family profile: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for BGP address family profile: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating BGP address family profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("bgp-address-family-profile", help="Show BGP address family profile details.")
def show_bgp_address_family_profile(
    name: str = typer.Option(None, "--name", help="Name of specific profile to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show BGP address family profile details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            profile = scm_client.get_bgp_address_family_profile(name=name, folder=folder, snippet=snippet, device=device)
            if not profile:
                typer.echo(f"BGP address family profile '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nBGP Address Family Profile: {profile['name']}")
            typer.echo("=" * 60)
            location = profile.get("folder") or profile.get("snippet") or profile.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if profile.get("ipv4"):
                typer.echo(f"IPv4: {json.dumps(profile['ipv4'], indent=2)}")
            if profile.get("id"):
                typer.echo(f"\nID: {profile['id']}")
            return profile
        else:
            profiles = scm_client.list_bgp_address_family_profiles(folder=folder, snippet=snippet, device=device)
            if not profiles:
                typer.echo("No BGP address family profiles found")
                return
            typer.echo("\nBGP Address Family Profiles:")
            typer.echo("-" * 80)
            for profile in profiles:
                location = profile.get("folder") or profile.get("snippet") or profile.get("device", "N/A")
                typer.echo(f"Name: {profile.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if profile.get("id"):
                    typer.echo(f"  ID: {profile['id']}")
                typer.echo("-" * 80)
            return profiles
    except Exception as e:
        typer.echo(f"Error showing BGP address family profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# BGP AUTH PROFILE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("bgp-auth-profile", help="Export BGP auth profiles to a YAML file.")
def backup_bgp_auth_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export BGP auth profiles from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving BGP auth profiles from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        profiles = scm_client.list_bgp_auth_profiles(**kwargs)
        if not profiles:
            typer.echo(f"No BGP auth profiles found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"bgp_auth_profiles": profiles}
        filename = Path(file or get_default_backup_filename("bgp-auth-profile", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(profiles)} BGP auth profiles to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up BGP auth profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("bgp-auth-profile", help="Delete a BGP auth profile.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        profile = scm_client.get_bgp_auth_profile(name=name, folder=folder, snippet=snippet, device=device)
        if not profile:
            typer.echo(f"BGP auth profile '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete BGP auth profile '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_bgp_auth_profile(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted BGP auth profile: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting BGP auth profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("bgp-auth-profile", help="Load BGP auth profiles from a YAML file.")
def load_bgp_auth_profile(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load BGP auth profiles from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "bgp_auth_profiles" not in data:
            typer.echo("No BGP auth profiles found in file", err=True)
            raise typer.Exit(code=1)
        profiles = data["bgp_auth_profiles"]
        if not isinstance(profiles, list):
            profiles = [profiles]
        if dry_run:
            typer.echo("Dry run mode - no changes will be applied")
            for p in profiles:
                typer.echo(f"  Would process: {p.get('name', 'N/A')}")
            return
        created_count = 0
        updated_count = 0
        no_change_count = 0
        for profile_data in profiles:
            try:
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
                action = result.pop("__action__", "created")
                container = validated.folder or validated.snippet or validated.device
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created BGP auth profile: {validated.name} in {container}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated BGP auth profile: {validated.name} in {container}")
                else:
                    no_change_count += 1
                    typer.echo(f"No changes needed for BGP auth profile: {validated.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing BGP auth profile: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count + updated_count + no_change_count} BGP auth profiles")
    except Exception as e:
        typer.echo(f"Error loading BGP auth profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("bgp-auth-profile", help="Create or update a BGP auth profile.")
def set_bgp_auth_profile(
    name: str = typer.Argument(..., help="Name of the BGP auth profile"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    secret: str = typer.Option(None, "--secret", help="BGP authentication key"),
) -> None:
    """Create or update a BGP auth profile."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        profile_data: dict[str, Any] = {"name": name, location_type: location_value}
        if secret is not None:
            profile_data["secret"] = secret
        validated = BgpAuthProfile(**profile_data)
        sdk_data = validated.to_sdk_model()
        result = scm_client.create_bgp_auth_profile(sdk_data)
        action = result.pop("__action__", "created")
        if action == "created":
            typer.echo(f"Created BGP auth profile: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated BGP auth profile: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for BGP auth profile: {name} in {location_value}")
    except Exception as e:
        typer.echo(f"Error creating/updating BGP auth profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("bgp-auth-profile", help="Show BGP auth profile details.")
def show_bgp_auth_profile(
    name: str = typer.Option(None, "--name", help="Name of specific profile to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show BGP auth profile details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            profile = scm_client.get_bgp_auth_profile(name=name, folder=folder, snippet=snippet, device=device)
            if not profile:
                typer.echo(f"BGP auth profile '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nBGP Auth Profile: {profile['name']}")
            typer.echo("=" * 60)
            location = profile.get("folder") or profile.get("snippet") or profile.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if profile.get("secret"):
                typer.echo("Secret: ********")
            if profile.get("id"):
                typer.echo(f"\nID: {profile['id']}")
            return profile
        else:
            profiles = scm_client.list_bgp_auth_profiles(folder=folder, snippet=snippet, device=device)
            if not profiles:
                typer.echo("No BGP auth profiles found")
                return
            typer.echo("\nBGP Auth Profiles:")
            typer.echo("-" * 80)
            for profile in profiles:
                location = profile.get("folder") or profile.get("snippet") or profile.get("device", "N/A")
                typer.echo(f"Name: {profile.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if profile.get("id"):
                    typer.echo(f"  ID: {profile['id']}")
                typer.echo("-" * 80)
            return profiles
    except Exception as e:
        typer.echo(f"Error showing BGP auth profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# OSPF AUTH PROFILE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("ospf-auth-profile", help="Export OSPF auth profiles to a YAML file.")
def backup_ospf_auth_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export OSPF auth profiles from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving OSPF auth profiles from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        profiles = scm_client.list_ospf_auth_profiles(**kwargs)
        if not profiles:
            typer.echo(f"No OSPF auth profiles found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"ospf_auth_profiles": profiles}
        filename = Path(file or get_default_backup_filename("ospf-auth-profile", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(profiles)} OSPF auth profiles to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up OSPF auth profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("ospf-auth-profile", help="Delete an OSPF auth profile.")
def delete_ospf_auth_profile(
    name: str = typer.Argument(..., help="Name of the OSPF auth profile to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete an OSPF auth profile."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        profile = scm_client.get_ospf_auth_profile(name=name, folder=folder, snippet=snippet, device=device)
        if not profile:
            typer.echo(f"OSPF auth profile '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete OSPF auth profile '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_ospf_auth_profile(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted OSPF auth profile: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting OSPF auth profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("ospf-auth-profile", help="Load OSPF auth profiles from a YAML file.")
def load_ospf_auth_profile(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load OSPF auth profiles from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "ospf_auth_profiles" not in data:
            typer.echo("No OSPF auth profiles found in file", err=True)
            raise typer.Exit(code=1)
        profiles = data["ospf_auth_profiles"]
        if not isinstance(profiles, list):
            profiles = [profiles]
        if dry_run:
            typer.echo("Dry run mode - no changes will be applied")
            for p in profiles:
                typer.echo(f"  Would process: {p.get('name', 'N/A')}")
            return
        created_count = 0
        updated_count = 0
        no_change_count = 0
        for profile_data in profiles:
            try:
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
                action = result.pop("__action__", "created")
                container = validated.folder or validated.snippet or validated.device
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created OSPF auth profile: {validated.name} in {container}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated OSPF auth profile: {validated.name} in {container}")
                else:
                    no_change_count += 1
                    typer.echo(f"No changes needed for OSPF auth profile: {validated.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing OSPF auth profile: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count + updated_count + no_change_count} OSPF auth profiles")
    except Exception as e:
        typer.echo(f"Error loading OSPF auth profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("ospf-auth-profile", help="Create or update an OSPF auth profile.")
def set_ospf_auth_profile(
    name: str = typer.Argument(..., help="Name of the OSPF auth profile"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    password: str = typer.Option(None, "--password", help="Simple password authentication"),
    md5_json: str = typer.Option(None, "--md5-json", help="MD5 authentication keys as JSON"),
) -> None:
    """Create or update an OSPF auth profile."""
    try:
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
            typer.echo(f"Created OSPF auth profile: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated OSPF auth profile: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for OSPF auth profile: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating OSPF auth profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("ospf-auth-profile", help="Show OSPF auth profile details.")
def show_ospf_auth_profile(
    name: str = typer.Option(None, "--name", help="Name of specific profile to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show OSPF auth profile details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            profile = scm_client.get_ospf_auth_profile(name=name, folder=folder, snippet=snippet, device=device)
            if not profile:
                typer.echo(f"OSPF auth profile '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nOSPF Auth Profile: {profile['name']}")
            typer.echo("=" * 60)
            location = profile.get("folder") or profile.get("snippet") or profile.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if profile.get("password"):
                typer.echo("Password: ********")
            if profile.get("md5"):
                typer.echo(f"MD5 Keys: {len(profile['md5'])} key(s)")
            if profile.get("id"):
                typer.echo(f"\nID: {profile['id']}")
            return profile
        else:
            profiles = scm_client.list_ospf_auth_profiles(folder=folder, snippet=snippet, device=device)
            if not profiles:
                typer.echo("No OSPF auth profiles found")
                return
            typer.echo("\nOSPF Auth Profiles:")
            typer.echo("-" * 80)
            for profile in profiles:
                location = profile.get("folder") or profile.get("snippet") or profile.get("device", "N/A")
                typer.echo(f"Name: {profile.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if profile.get("id"):
                    typer.echo(f"  ID: {profile['id']}")
                typer.echo("-" * 80)
            return profiles
    except Exception as e:
        typer.echo(f"Error showing OSPF auth profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# ROUTE ACCESS LIST COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("route-access-list", help="Export route access lists to a YAML file.")
def backup_route_access_list(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export route access lists from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving route access lists from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        items = scm_client.list_route_access_lists(**kwargs)
        if not items:
            typer.echo(f"No route access lists found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"route_access_lists": items}
        filename = Path(file or get_default_backup_filename("route-access-list", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(items)} route access lists to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up route access lists: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("route-access-list", help="Delete a route access list.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        item = scm_client.get_route_access_list(name=name, folder=folder, snippet=snippet, device=device)
        if not item:
            typer.echo(f"Route access list '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete route access list '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_route_access_list(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted route access list: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting route access list: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("route-access-list", help="Load route access lists from a YAML file.")
def load_route_access_list(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load route access lists from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "route_access_lists" not in data:
            typer.echo("No route access lists found in file", err=True)
            raise typer.Exit(code=1)
        items = data["route_access_lists"]
        if not isinstance(items, list):
            items = [items]
        if dry_run:
            typer.echo("Dry run mode - no changes will be applied")
            for item in items:
                typer.echo(f"  Would process: {item.get('name', 'N/A')}")
            return
        created_count = 0
        updated_count = 0
        no_change_count = 0
        for item_data in items:
            try:
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
                action = result.pop("__action__", "created")
                container = validated.folder or validated.snippet or validated.device
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created route access list: {validated.name} in {container}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated route access list: {validated.name} in {container}")
                else:
                    no_change_count += 1
                    typer.echo(f"No changes needed for route access list: {validated.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing route access list: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count + updated_count + no_change_count} route access lists")
    except Exception as e:
        typer.echo(f"Error loading route access lists: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("route-access-list", help="Create or update a route access list.")
def set_route_access_list(
    name: str = typer.Argument(..., help="Name of the route access list"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    description: str = typer.Option(None, "--description", help="Description"),
    type_json: str = typer.Option(None, "--type-json", help="Access list type config as JSON"),
) -> None:
    """Create or update a route access list."""
    try:
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
            typer.echo(f"Created route access list: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated route access list: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for route access list: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating route access list: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("route-access-list", help="Show route access list details.")
def show_route_access_list(
    name: str = typer.Option(None, "--name", help="Name of specific route access list to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show route access list details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            item = scm_client.get_route_access_list(name=name, folder=folder, snippet=snippet, device=device)
            if not item:
                typer.echo(f"Route access list '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nRoute Access List: {item['name']}")
            typer.echo("=" * 60)
            location = item.get("folder") or item.get("snippet") or item.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if item.get("description"):
                typer.echo(f"Description: {item['description']}")
            if item.get("type"):
                typer.echo(f"Type: {json.dumps(item['type'], indent=2)}")
            if item.get("id"):
                typer.echo(f"\nID: {item['id']}")
            return item
        else:
            items = scm_client.list_route_access_lists(folder=folder, snippet=snippet, device=device)
            if not items:
                typer.echo("No route access lists found")
                return
            typer.echo("\nRoute Access Lists:")
            typer.echo("-" * 80)
            for item in items:
                location = item.get("folder") or item.get("snippet") or item.get("device", "N/A")
                typer.echo(f"Name: {item.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if item.get("description"):
                    typer.echo(f"  Description: {item['description']}")
                if item.get("id"):
                    typer.echo(f"  ID: {item['id']}")
                typer.echo("-" * 80)
            return items
    except Exception as e:
        typer.echo(f"Error showing route access list: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# ROUTE PREFIX LIST COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("route-prefix-list", help="Export route prefix lists to a YAML file.")
def backup_route_prefix_list(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export route prefix lists from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving route prefix lists from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        items = scm_client.list_route_prefix_lists(**kwargs)
        if not items:
            typer.echo(f"No route prefix lists found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"route_prefix_lists": items}
        filename = Path(file or get_default_backup_filename("route-prefix-list", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(items)} route prefix lists to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up route prefix lists: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("route-prefix-list", help="Delete a route prefix list.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        item = scm_client.get_route_prefix_list(name=name, folder=folder, snippet=snippet, device=device)
        if not item:
            typer.echo(f"Route prefix list '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete route prefix list '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_route_prefix_list(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted route prefix list: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting route prefix list: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("route-prefix-list", help="Load route prefix lists from a YAML file.")
def load_route_prefix_list(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load route prefix lists from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "route_prefix_lists" not in data:
            typer.echo("No route prefix lists found in file", err=True)
            raise typer.Exit(code=1)
        items = data["route_prefix_lists"]
        if not isinstance(items, list):
            items = [items]
        if dry_run:
            typer.echo("Dry run mode - no changes will be applied")
            for item in items:
                typer.echo(f"  Would process: {item.get('name', 'N/A')}")
            return
        created_count = 0
        updated_count = 0
        no_change_count = 0
        for item_data in items:
            try:
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
                action = result.pop("__action__", "created")
                container = validated.folder or validated.snippet or validated.device
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created route prefix list: {validated.name} in {container}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated route prefix list: {validated.name} in {container}")
                else:
                    no_change_count += 1
                    typer.echo(f"No changes needed for route prefix list: {validated.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing route prefix list: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count + updated_count + no_change_count} route prefix lists")
    except Exception as e:
        typer.echo(f"Error loading route prefix lists: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("route-prefix-list", help="Create or update a route prefix list.")
def set_route_prefix_list(
    name: str = typer.Argument(..., help="Name of the route prefix list"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    description: str = typer.Option(None, "--description", help="Description"),
    ipv4_json: str = typer.Option(None, "--ipv4-json", help="IPv4 prefix list config as JSON"),
) -> None:
    """Create or update a route prefix list."""
    try:
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
            typer.echo(f"Created route prefix list: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated route prefix list: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for route prefix list: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating route prefix list: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("route-prefix-list", help="Show route prefix list details.")
def show_route_prefix_list(
    name: str = typer.Option(None, "--name", help="Name of specific route prefix list to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show route prefix list details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            item = scm_client.get_route_prefix_list(name=name, folder=folder, snippet=snippet, device=device)
            if not item:
                typer.echo(f"Route prefix list '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nRoute Prefix List: {item['name']}")
            typer.echo("=" * 60)
            location = item.get("folder") or item.get("snippet") or item.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if item.get("description"):
                typer.echo(f"Description: {item['description']}")
            if item.get("ipv4"):
                typer.echo(f"IPv4: {json.dumps(item['ipv4'], indent=2)}")
            if item.get("id"):
                typer.echo(f"\nID: {item['id']}")
            return item
        else:
            items = scm_client.list_route_prefix_lists(folder=folder, snippet=snippet, device=device)
            if not items:
                typer.echo("No route prefix lists found")
                return
            typer.echo("\nRoute Prefix Lists:")
            typer.echo("-" * 80)
            for item in items:
                location = item.get("folder") or item.get("snippet") or item.get("device", "N/A")
                typer.echo(f"Name: {item.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if item.get("description"):
                    typer.echo(f"  Description: {item['description']}")
                if item.get("id"):
                    typer.echo(f"  ID: {item['id']}")
                typer.echo("-" * 80)
            return items
    except Exception as e:
        typer.echo(f"Error showing route prefix list: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# BGP FILTERING PROFILE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("bgp-filtering-profile", help="Export BGP filtering profiles to a YAML file.")
def backup_bgp_filtering_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export BGP filtering profiles from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving BGP filtering profiles from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        profiles = scm_client.list_bgp_filtering_profiles(**kwargs)
        if not profiles:
            typer.echo(f"No BGP filtering profiles found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"bgp_filtering_profiles": profiles}
        filename = Path(file or get_default_backup_filename("bgp-filtering-profile", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(profiles)} BGP filtering profiles to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up BGP filtering profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("bgp-filtering-profile", help="Delete a BGP filtering profile.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        profile = scm_client.get_bgp_filtering_profile(name=name, folder=folder, snippet=snippet, device=device)
        if not profile:
            typer.echo(f"BGP filtering profile '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete BGP filtering profile '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_bgp_filtering_profile(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted BGP filtering profile: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting BGP filtering profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("bgp-filtering-profile", help="Load BGP filtering profiles from a YAML file.")
def load_bgp_filtering_profile(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load BGP filtering profiles from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "bgp_filtering_profiles" not in data:
            typer.echo("No BGP filtering profiles found in file", err=True)
            raise typer.Exit(code=1)
        profiles = data["bgp_filtering_profiles"]
        if not isinstance(profiles, list):
            profiles = [profiles]
        if dry_run:
            typer.echo("Dry run mode - no changes will be applied")
            for p in profiles:
                typer.echo(f"  Would process: {p.get('name', 'N/A')}")
            return
        created_count = 0
        for profile_data in profiles:
            try:
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
                action = result.pop("__action__", "created")
                container = validated.folder or validated.snippet or validated.device
                created_count += 1
                typer.echo(f"{action.capitalize()} BGP filtering profile: {validated.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing BGP filtering profile: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count} BGP filtering profiles")
    except Exception as e:
        typer.echo(f"Error loading BGP filtering profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("bgp-filtering-profile", help="Create or update a BGP filtering profile.")
def set_bgp_filtering_profile(
    name: str = typer.Argument(..., help="Name of the BGP filtering profile"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    ipv4_json: str = typer.Option(None, "--ipv4-json", help="IPv4 filtering config as JSON"),
) -> None:
    """Create or update a BGP filtering profile."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        profile_data: dict[str, Any] = {"name": name, location_type: location_value}
        if ipv4_json:
            profile_data["ipv4"] = json.loads(ipv4_json)
        validated = BgpFilteringProfile(**profile_data)
        sdk_data = validated.to_sdk_model()
        result = scm_client.create_bgp_filtering_profile(sdk_data)
        action = result.pop("__action__", "created")
        if action == "created":
            typer.echo(f"Created BGP filtering profile: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated BGP filtering profile: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for BGP filtering profile: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating BGP filtering profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("bgp-filtering-profile", help="Show BGP filtering profile details.")
def show_bgp_filtering_profile(
    name: str = typer.Option(None, "--name", help="Name of specific profile to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show BGP filtering profile details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            profile = scm_client.get_bgp_filtering_profile(name=name, folder=folder, snippet=snippet, device=device)
            if not profile:
                typer.echo(f"BGP filtering profile '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nBGP Filtering Profile: {profile['name']}")
            typer.echo("=" * 60)
            location = profile.get("folder") or profile.get("snippet") or profile.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if profile.get("ipv4"):
                typer.echo(f"IPv4: {json.dumps(profile['ipv4'], indent=2)}")
            if profile.get("id"):
                typer.echo(f"\nID: {profile['id']}")
            return profile
        else:
            profiles = scm_client.list_bgp_filtering_profiles(folder=folder, snippet=snippet, device=device)
            if not profiles:
                typer.echo("No BGP filtering profiles found")
                return
            typer.echo("\nBGP Filtering Profiles:")
            typer.echo("-" * 80)
            for profile in profiles:
                location = profile.get("folder") or profile.get("snippet") or profile.get("device", "N/A")
                typer.echo(f"Name: {profile.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if profile.get("id"):
                    typer.echo(f"  ID: {profile['id']}")
                typer.echo("-" * 80)
            return profiles
    except Exception as e:
        typer.echo(f"Error showing BGP filtering profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# BGP REDISTRIBUTION PROFILE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("bgp-redistribution-profile", help="Export BGP redistribution profiles to a YAML file.")
def backup_bgp_redistribution_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export BGP redistribution profiles from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving BGP redistribution profiles from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        profiles = scm_client.list_bgp_redistribution_profiles(**kwargs)
        if not profiles:
            typer.echo(f"No BGP redistribution profiles found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"bgp_redistribution_profiles": profiles}
        filename = Path(file or get_default_backup_filename("bgp-redistribution-profile", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(profiles)} BGP redistribution profiles to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up BGP redistribution profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("bgp-redistribution-profile", help="Delete a BGP redistribution profile.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        profile = scm_client.get_bgp_redistribution_profile(name=name, folder=folder, snippet=snippet, device=device)
        if not profile:
            typer.echo(f"BGP redistribution profile '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete BGP redistribution profile '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_bgp_redistribution_profile(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted BGP redistribution profile: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting BGP redistribution profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("bgp-redistribution-profile", help="Load BGP redistribution profiles from a YAML file.")
def load_bgp_redistribution_profile(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load BGP redistribution profiles from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "bgp_redistribution_profiles" not in data:
            typer.echo("No BGP redistribution profiles found in file", err=True)
            raise typer.Exit(code=1)
        profiles = data["bgp_redistribution_profiles"]
        if not isinstance(profiles, list):
            profiles = [profiles]
        if dry_run:
            typer.echo("Dry run mode - no changes will be applied")
            for p in profiles:
                typer.echo(f"  Would process: {p.get('name', 'N/A')}")
            return
        created_count = 0
        for profile_data in profiles:
            try:
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
                action = result.pop("__action__", "created")
                container = validated.folder or validated.snippet or validated.device
                created_count += 1
                typer.echo(f"{action.capitalize()} BGP redistribution profile: {validated.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing BGP redistribution profile: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count} BGP redistribution profiles")
    except Exception as e:
        typer.echo(f"Error loading BGP redistribution profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("bgp-redistribution-profile", help="Create or update a BGP redistribution profile.")
def set_bgp_redistribution_profile(
    name: str = typer.Argument(..., help="Name of the BGP redistribution profile"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    ipv4_json: str = typer.Option(None, "--ipv4-json", help="IPv4 redistribution config as JSON"),
) -> None:
    """Create or update a BGP redistribution profile."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        profile_data: dict[str, Any] = {"name": name, location_type: location_value}
        if ipv4_json:
            profile_data["ipv4"] = json.loads(ipv4_json)
        validated = BgpRedistributionProfile(**profile_data)
        sdk_data = validated.to_sdk_model()
        result = scm_client.create_bgp_redistribution_profile(sdk_data)
        action = result.pop("__action__", "created")
        if action == "created":
            typer.echo(f"Created BGP redistribution profile: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated BGP redistribution profile: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for BGP redistribution profile: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating BGP redistribution profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("bgp-redistribution-profile", help="Show BGP redistribution profile details.")
def show_bgp_redistribution_profile(
    name: str = typer.Option(None, "--name", help="Name of specific profile to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show BGP redistribution profile details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            profile = scm_client.get_bgp_redistribution_profile(name=name, folder=folder, snippet=snippet, device=device)
            if not profile:
                typer.echo(f"BGP redistribution profile '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nBGP Redistribution Profile: {profile['name']}")
            typer.echo("=" * 60)
            location = profile.get("folder") or profile.get("snippet") or profile.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if profile.get("ipv4"):
                typer.echo(f"IPv4: {json.dumps(profile['ipv4'], indent=2)}")
            if profile.get("id"):
                typer.echo(f"\nID: {profile['id']}")
            return profile
        else:
            profiles = scm_client.list_bgp_redistribution_profiles(folder=folder, snippet=snippet, device=device)
            if not profiles:
                typer.echo("No BGP redistribution profiles found")
                return
            typer.echo("\nBGP Redistribution Profiles:")
            typer.echo("-" * 80)
            for profile in profiles:
                location = profile.get("folder") or profile.get("snippet") or profile.get("device", "N/A")
                typer.echo(f"Name: {profile.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if profile.get("id"):
                    typer.echo(f"  ID: {profile['id']}")
                typer.echo("-" * 80)
            return profiles
    except Exception as e:
        typer.echo(f"Error showing BGP redistribution profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# BGP ROUTE MAP COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("bgp-route-map", help="Export BGP route maps to a YAML file.")
def backup_bgp_route_map(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export BGP route maps from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving BGP route maps from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        items = scm_client.list_bgp_route_maps(**kwargs)
        if not items:
            typer.echo(f"No BGP route maps found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"bgp_route_maps": items}
        filename = Path(file or get_default_backup_filename("bgp-route-map", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(items)} BGP route maps to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up BGP route maps: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("bgp-route-map", help="Delete a BGP route map.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        item = scm_client.get_bgp_route_map(name=name, folder=folder, snippet=snippet, device=device)
        if not item:
            typer.echo(f"BGP route map '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete BGP route map '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_bgp_route_map(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted BGP route map: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting BGP route map: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("bgp-route-map", help="Load BGP route maps from a YAML file.")
def load_bgp_route_map(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load BGP route maps from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "bgp_route_maps" not in data:
            typer.echo("No BGP route maps found in file", err=True)
            raise typer.Exit(code=1)
        items = data["bgp_route_maps"]
        if not isinstance(items, list):
            items = [items]
        if dry_run:
            typer.echo("Dry run mode - no changes will be applied")
            for item in items:
                typer.echo(f"  Would process: {item.get('name', 'N/A')}")
            return
        created_count = 0
        for item_data in items:
            try:
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
                action = result.pop("__action__", "created")
                container = validated.folder or validated.snippet or validated.device
                created_count += 1
                typer.echo(f"{action.capitalize()} BGP route map: {validated.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing BGP route map: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count} BGP route maps")
    except Exception as e:
        typer.echo(f"Error loading BGP route maps: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("bgp-route-map", help="Create or update a BGP route map.")
def set_bgp_route_map(
    name: str = typer.Argument(..., help="Name of the BGP route map"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    route_map_json: str = typer.Option(None, "--route-map-json", help="Route map entries as JSON"),
) -> None:
    """Create or update a BGP route map."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        item_data: dict[str, Any] = {"name": name, location_type: location_value}
        if route_map_json:
            item_data["route_map"] = json.loads(route_map_json)
        validated = BgpRouteMap(**item_data)
        sdk_data = validated.to_sdk_model()
        result = scm_client.create_bgp_route_map(sdk_data)
        action = result.pop("__action__", "created")
        if action == "created":
            typer.echo(f"Created BGP route map: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated BGP route map: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for BGP route map: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating BGP route map: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("bgp-route-map", help="Show BGP route map details.")
def show_bgp_route_map(
    name: str = typer.Option(None, "--name", help="Name of specific BGP route map to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show BGP route map details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            item = scm_client.get_bgp_route_map(name=name, folder=folder, snippet=snippet, device=device)
            if not item:
                typer.echo(f"BGP route map '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nBGP Route Map: {item['name']}")
            typer.echo("=" * 60)
            location = item.get("folder") or item.get("snippet") or item.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if item.get("route_map"):
                typer.echo(f"Entries: {len(item['route_map'])}")
                for entry in item["route_map"]:
                    typer.echo(f"  Seq {entry.get('name', 'N/A')}: {entry.get('action', 'N/A')}")
            if item.get("id"):
                typer.echo(f"\nID: {item['id']}")
            return item
        else:
            items = scm_client.list_bgp_route_maps(folder=folder, snippet=snippet, device=device)
            if not items:
                typer.echo("No BGP route maps found")
                return
            typer.echo("\nBGP Route Maps:")
            typer.echo("-" * 80)
            for item in items:
                location = item.get("folder") or item.get("snippet") or item.get("device", "N/A")
                typer.echo(f"Name: {item.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                entries = item.get("route_map", [])
                typer.echo(f"  Entries: {len(entries)}")
                if item.get("id"):
                    typer.echo(f"  ID: {item['id']}")
                typer.echo("-" * 80)
            return items
    except Exception as e:
        typer.echo(f"Error showing BGP route map: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# BGP ROUTE MAP REDISTRIBUTION COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("bgp-route-map-redistribution", help="Export BGP route map redistributions to a YAML file.")
def backup_bgp_route_map_redistribution(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export BGP route map redistributions from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving BGP route map redistributions from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        items = scm_client.list_bgp_route_map_redistributions(**kwargs)
        if not items:
            typer.echo(f"No BGP route map redistributions found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"bgp_route_map_redistributions": items}
        filename = Path(file or get_default_backup_filename("bgp-route-map-redistribution", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(items)} BGP route map redistributions to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up BGP route map redistributions: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("bgp-route-map-redistribution", help="Delete a BGP route map redistribution.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        item = scm_client.get_bgp_route_map_redistribution(name=name, folder=folder, snippet=snippet, device=device)
        if not item:
            typer.echo(f"BGP route map redistribution '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete BGP route map redistribution '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_bgp_route_map_redistribution(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted BGP route map redistribution: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting BGP route map redistribution: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("bgp-route-map-redistribution", help="Load BGP route map redistributions from a YAML file.")
def load_bgp_route_map_redistribution(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load BGP route map redistributions from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "bgp_route_map_redistributions" not in data:
            typer.echo("No BGP route map redistributions found in file", err=True)
            raise typer.Exit(code=1)
        items = data["bgp_route_map_redistributions"]
        if not isinstance(items, list):
            items = [items]
        if dry_run:
            typer.echo("Dry run mode - no changes will be applied")
            for item in items:
                typer.echo(f"  Would process: {item.get('name', 'N/A')}")
            return
        created_count = 0
        for item_data in items:
            try:
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
                action = result.pop("__action__", "created")
                container = validated.folder or validated.snippet or validated.device
                created_count += 1
                typer.echo(f"{action.capitalize()} BGP route map redistribution: {validated.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing BGP route map redistribution: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count} BGP route map redistributions")
    except Exception as e:
        typer.echo(f"Error loading BGP route map redistributions: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("bgp-route-map-redistribution", help="Create or update a BGP route map redistribution.")
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
    try:
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
            typer.echo(f"Created BGP route map redistribution: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated BGP route map redistribution: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for BGP route map redistribution: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating BGP route map redistribution: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("bgp-route-map-redistribution", help="Show BGP route map redistribution details.")
def show_bgp_route_map_redistribution(
    name: str = typer.Option(None, "--name", help="Name of specific BGP route map redistribution to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show BGP route map redistribution details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            item = scm_client.get_bgp_route_map_redistribution(name=name, folder=folder, snippet=snippet, device=device)
            if not item:
                typer.echo(f"BGP route map redistribution '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nBGP Route Map Redistribution: {item['name']}")
            typer.echo("=" * 60)
            location = item.get("folder") or item.get("snippet") or item.get("device", "N/A")
            typer.echo(f"Location: {location}")
            for proto in ["bgp", "ospf", "connected_static"]:
                if item.get(proto):
                    typer.echo(f"Source: {proto}")
                    typer.echo(f"  Config: {json.dumps(item[proto], indent=2)}")
            if item.get("id"):
                typer.echo(f"\nID: {item['id']}")
            return item
        else:
            items = scm_client.list_bgp_route_map_redistributions(folder=folder, snippet=snippet, device=device)
            if not items:
                typer.echo("No BGP route map redistributions found")
                return
            typer.echo("\nBGP Route Map Redistributions:")
            typer.echo("-" * 80)
            for item in items:
                location = item.get("folder") or item.get("snippet") or item.get("device", "N/A")
                typer.echo(f"Name: {item.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                for proto in ["bgp", "ospf", "connected_static"]:
                    if item.get(proto):
                        typer.echo(f"  Source: {proto}")
                if item.get("id"):
                    typer.echo(f"  ID: {item['id']}")
                typer.echo("-" * 80)
            return items
    except Exception as e:
        typer.echo(f"Error showing BGP route map redistribution: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# DNS PROXY COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("dns-proxy", help="Export DNS proxies to a YAML file.")
def backup_dns_proxy(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export DNS proxies from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving DNS proxies from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        proxies = scm_client.list_dns_proxies(**kwargs)
        if not proxies:
            typer.echo(f"No DNS proxies found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"dns_proxies": proxies}
        filename = Path(file or get_default_backup_filename("dns-proxy", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(proxies)} DNS proxies to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up DNS proxies: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("dns-proxy", help="Delete a DNS proxy.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        proxy = scm_client.get_dns_proxy(name=name, folder=folder, snippet=snippet, device=device)
        if not proxy:
            typer.echo(f"DNS proxy '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete DNS proxy '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_dns_proxy(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted DNS proxy: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting DNS proxy: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("dns-proxy", help="Load DNS proxies from a YAML file.")
def load_dns_proxy(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load DNS proxies from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "dns_proxies" not in data:
            typer.echo("No DNS proxies found in file", err=True)
            raise typer.Exit(code=1)
        proxies = data["dns_proxies"]
        if not isinstance(proxies, list):
            proxies = [proxies]
        if dry_run:
            typer.echo("Dry run mode - no changes will be applied")
            for p in proxies:
                typer.echo(f"  Would process: {p.get('name', 'N/A')}")
            return
        created_count = 0
        updated_count = 0
        no_change_count = 0
        for proxy_data in proxies:
            try:
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
                action = result.pop("__action__", "created")
                container = validated.folder or validated.snippet or validated.device
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created DNS proxy: {validated.name} in {container}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated DNS proxy: {validated.name} in {container}")
                else:
                    no_change_count += 1
                    typer.echo(f"No changes needed for DNS proxy: {validated.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing DNS proxy: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count + updated_count + no_change_count} DNS proxies")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")
        if no_change_count > 0:
            typer.echo(f"  - No change: {no_change_count}")
    except Exception as e:
        typer.echo(f"Error loading DNS proxies: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("dns-proxy", help="Create or update a DNS proxy.")
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
    try:
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
            typer.echo(f"Created DNS proxy: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated DNS proxy: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for DNS proxy: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating DNS proxy: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("dns-proxy", help="Show DNS proxy details.")
def show_dns_proxy(
    name: str = typer.Option(None, "--name", help="Name of specific DNS proxy to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show DNS proxy details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            proxy = scm_client.get_dns_proxy(name=name, folder=folder, snippet=snippet, device=device)
            if not proxy:
                typer.echo(f"DNS proxy '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nDNS Proxy: {proxy['name']}")
            typer.echo("=" * 60)
            location = proxy.get("folder") or proxy.get("snippet") or proxy.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if proxy.get("enabled") is not None:
                typer.echo(f"Enabled: {proxy['enabled']}")
            if proxy.get("default"):
                typer.echo(f"Default: {json.dumps(proxy['default'], indent=2)}")
            if proxy.get("id"):
                typer.echo(f"\nID: {proxy['id']}")
            return proxy
        else:
            proxies = scm_client.list_dns_proxies(folder=folder, snippet=snippet, device=device)
            if not proxies:
                typer.echo("No DNS proxies found")
                return
            typer.echo("\nDNS Proxies:")
            typer.echo("-" * 80)
            for proxy in proxies:
                location = proxy.get("folder") or proxy.get("snippet") or proxy.get("device", "N/A")
                typer.echo(f"Name: {proxy.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if proxy.get("enabled") is not None:
                    typer.echo(f"  Enabled: {proxy['enabled']}")
                if proxy.get("id"):
                    typer.echo(f"  ID: {proxy['id']}")
                typer.echo("-" * 80)
            return proxies
    except Exception as e:
        typer.echo(f"Error showing DNS proxy: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# PBF RULE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("pbf-rule", help="Export PBF rules to a YAML file.")
def backup_pbf_rule(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export PBF rules from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving PBF rules from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        rules = scm_client.list_pbf_rules(**kwargs)
        if not rules:
            typer.echo(f"No PBF rules found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"pbf_rules": rules}
        filename = Path(file or get_default_backup_filename("pbf-rule", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(rules)} PBF rules to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up PBF rules: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("pbf-rule", help="Delete a PBF rule.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        rule = scm_client.get_pbf_rule(name=name, folder=folder, snippet=snippet, device=device)
        if not rule:
            typer.echo(f"PBF rule '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete PBF rule '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_pbf_rule(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted PBF rule: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting PBF rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("pbf-rule", help="Load PBF rules from a YAML file.")
def load_pbf_rule(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load PBF rules from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "pbf_rules" not in data:
            typer.echo("No PBF rules found in file", err=True)
            raise typer.Exit(code=1)
        rules = data["pbf_rules"]
        if not isinstance(rules, list):
            rules = [rules]
        if dry_run:
            typer.echo("Dry run mode - no changes will be applied")
            for r in rules:
                typer.echo(f"  Would process: {r.get('name', 'N/A')}")
            return
        created_count = 0
        updated_count = 0
        no_change_count = 0
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
                    typer.echo(f"Created PBF rule: {validated.name} in {container}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated PBF rule: {validated.name} in {container}")
                else:
                    no_change_count += 1
                    typer.echo(f"No changes needed for PBF rule: {validated.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing PBF rule: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count + updated_count + no_change_count} PBF rules")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")
        if no_change_count > 0:
            typer.echo(f"  - No change: {no_change_count}")
    except Exception as e:
        typer.echo(f"Error loading PBF rules: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("pbf-rule", help="Create or update a PBF rule.")
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
    try:
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
            typer.echo(f"Created PBF rule: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated PBF rule: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for PBF rule: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating PBF rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("pbf-rule", help="Show PBF rule details.")
def show_pbf_rule(
    name: str = typer.Option(None, "--name", help="Name of specific PBF rule to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show PBF rule details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            rule = scm_client.get_pbf_rule(name=name, folder=folder, snippet=snippet, device=device)
            if not rule:
                typer.echo(f"PBF rule '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nPBF Rule: {rule['name']}")
            typer.echo("=" * 60)
            location = rule.get("folder") or rule.get("snippet") or rule.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if rule.get("description"):
                typer.echo(f"Description: {rule['description']}")
            if rule.get("action"):
                typer.echo(f"Action: {json.dumps(rule['action'], indent=2)}")
            if rule.get("id"):
                typer.echo(f"\nID: {rule['id']}")
            return rule
        else:
            rules = scm_client.list_pbf_rules(folder=folder, snippet=snippet, device=device)
            if not rules:
                typer.echo("No PBF rules found")
                return
            typer.echo("\nPBF Rules:")
            typer.echo("-" * 80)
            for rule in rules:
                location = rule.get("folder") or rule.get("snippet") or rule.get("device", "N/A")
                typer.echo(f"Name: {rule.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if rule.get("description"):
                    typer.echo(f"  Description: {rule['description']}")
                if rule.get("id"):
                    typer.echo(f"  ID: {rule['id']}")
                typer.echo("-" * 80)
            return rules
    except Exception as e:
        typer.echo(f"Error showing PBF rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# QOS PROFILE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("qos-profile", help="Export QoS profiles to a YAML file.")
def backup_qos_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export QoS profiles from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        validate_qos_profile_folder(folder)
        typer.echo(f"Retrieving QoS profiles from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        profiles = scm_client.list_qos_profiles(**kwargs)
        if not profiles:
            typer.echo(f"No QoS profiles found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"qos_profiles": profiles}
        filename = Path(file or get_default_backup_filename("qos-profile", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(profiles)} QoS profiles to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up QoS profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("qos-profile", help="Delete a QoS profile.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        validate_qos_profile_folder(folder)
        profile = scm_client.get_qos_profile(name=name, folder=folder, snippet=snippet, device=device)
        if not profile:
            typer.echo(f"QoS profile '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete QoS profile '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_qos_profile(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted QoS profile: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting QoS profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("qos-profile", help="Load QoS profiles from a YAML file.")
def load_qos_profile(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load QoS profiles from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "qos_profiles" not in data:
            typer.echo("No QoS profiles found in file", err=True)
            raise typer.Exit(code=1)
        profiles = data["qos_profiles"]
        if not isinstance(profiles, list):
            profiles = [profiles]
        if dry_run:
            typer.echo("Dry run mode - no changes will be applied")
            for p in profiles:
                typer.echo(f"  Would process: {p.get('name', 'N/A')}")
            return
        created_count = 0
        updated_count = 0
        no_change_count = 0
        for profile_data in profiles:
            try:
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
                action = result.pop("__action__", "created")
                container = validated.folder or validated.snippet or validated.device
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created QoS profile: {validated.name} in {container}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated QoS profile: {validated.name} in {container}")
                else:
                    no_change_count += 1
                    typer.echo(f"No changes needed for QoS profile: {validated.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing QoS profile: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count + updated_count + no_change_count} QoS profiles")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")
        if no_change_count > 0:
            typer.echo(f"  - No change: {no_change_count}")
    except Exception as e:
        typer.echo(f"Error loading QoS profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("qos-profile", help="Create or update a QoS profile.")
def set_qos_profile(
    name: str = typer.Argument(..., help="Name of the QoS profile"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    aggregate_bandwidth_json: str = typer.Option(None, "--aggregate-bandwidth-json", help="Aggregate bandwidth config as JSON"),
    class_bandwidth_type_json: str = typer.Option(None, "--class-bandwidth-type-json", help="Class bandwidth type config as JSON"),
) -> None:
    """Create or update a QoS profile."""
    try:
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
            typer.echo(f"Created QoS profile: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated QoS profile: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for QoS profile: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating QoS profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("qos-profile", help="Show QoS profile details.")
def show_qos_profile(
    name: str = typer.Option(None, "--name", help="Name of specific QoS profile to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show QoS profile details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        validate_qos_profile_folder(folder)
        if name:
            profile = scm_client.get_qos_profile(name=name, folder=folder, snippet=snippet, device=device)
            if not profile:
                typer.echo(f"QoS profile '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nQoS Profile: {profile['name']}")
            typer.echo("=" * 60)
            location = profile.get("folder") or profile.get("snippet") or profile.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if profile.get("aggregate_bandwidth"):
                typer.echo(f"Aggregate Bandwidth: {json.dumps(profile['aggregate_bandwidth'], indent=2)}")
            if profile.get("class_bandwidth_type"):
                typer.echo(f"Class Bandwidth Type: {json.dumps(profile['class_bandwidth_type'], indent=2)}")
            if profile.get("id"):
                typer.echo(f"\nID: {profile['id']}")
            return profile
        else:
            profiles = scm_client.list_qos_profiles(folder=folder, snippet=snippet, device=device)
            if not profiles:
                typer.echo("No QoS profiles found")
                return
            typer.echo("\nQoS Profiles:")
            typer.echo("-" * 80)
            for profile in profiles:
                location = profile.get("folder") or profile.get("snippet") or profile.get("device", "N/A")
                typer.echo(f"Name: {profile.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if profile.get("id"):
                    typer.echo(f"  ID: {profile['id']}")
                typer.echo("-" * 80)
            return profiles
    except Exception as e:
        typer.echo(f"Error showing QoS profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# QOS RULE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("qos-rule", help="Export QoS rules to a YAML file.")
def backup_qos_rule(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export QoS rules from a specified location to a YAML file."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        typer.echo(f"Retrieving QoS rules from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        rules = scm_client.list_qos_rules(**kwargs)
        if not rules:
            typer.echo(f"No QoS rules found in {location_type} '{location_value}'", err=True)
            return
        export_data = {"qos_rules": rules}
        filename = Path(file or get_default_backup_filename("qos-rule", location_type, location_value))
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)
        typer.echo(f"Successfully backed up {len(rules)} QoS rules to {filename}")
    except Exception as e:
        typer.echo(f"Error backing up QoS rules: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("qos-rule", help="Delete a QoS rule.")
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
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        rule = scm_client.get_qos_rule(name=name, folder=folder, snippet=snippet, device=device)
        if not rule:
            typer.echo(f"QoS rule '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            typer.confirm(f"Delete QoS rule '{name}' from {location_type} '{location_value}'?", abort=True)
        scm_client.delete_qos_rule(name=name, folder=folder, snippet=snippet, device=device)
        typer.echo(f"Deleted QoS rule: {name} from {location_value}")
    except Exception as e:
        typer.echo(f"Error deleting QoS rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("qos-rule", help="Load QoS rules from a YAML file.")
def load_qos_rule(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load QoS rules from a YAML file."""
    try:
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)
        with Path(file).open() as f:
            data = yaml.safe_load(f)
        if not data or "qos_rules" not in data:
            typer.echo("No QoS rules found in file", err=True)
            raise typer.Exit(code=1)
        rules = data["qos_rules"]
        if not isinstance(rules, list):
            rules = [rules]
        if dry_run:
            typer.echo("Dry run mode - no changes will be applied")
            for r in rules:
                typer.echo(f"  Would process: {r.get('name', 'N/A')}")
            return
        created_count = 0
        updated_count = 0
        no_change_count = 0
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
                    typer.echo(f"Created QoS rule: {validated.name} in {container}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated QoS rule: {validated.name} in {container}")
                else:
                    no_change_count += 1
                    typer.echo(f"No changes needed for QoS rule: {validated.name} in {container}")
            except Exception as e:
                typer.echo(f"Error processing QoS rule: {str(e)}", err=True)
                continue
        typer.echo(f"\nSummary: Processed {created_count + updated_count + no_change_count} QoS rules")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")
        if no_change_count > 0:
            typer.echo(f"  - No change: {no_change_count}")
    except Exception as e:
        typer.echo(f"Error loading QoS rules: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("qos-rule", help="Create or update a QoS rule.")
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
    try:
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
            typer.echo(f"Created QoS rule: {name} in {location_value}")
        elif action == "updated":
            typer.echo(f"Updated QoS rule: {name} in {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for QoS rule: {name} in {location_value}")
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating QoS rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("qos-rule", help="Show QoS rule details.")
def show_qos_rule(
    name: str = typer.Option(None, "--name", help="Name of specific QoS rule to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show QoS rule details."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if name:
            rule = scm_client.get_qos_rule(name=name, folder=folder, snippet=snippet, device=device)
            if not rule:
                typer.echo(f"QoS rule '{name}' not found", err=True)
                raise typer.Exit(code=1)
            typer.echo(f"\nQoS Rule: {rule['name']}")
            typer.echo("=" * 60)
            location = rule.get("folder") or rule.get("snippet") or rule.get("device", "N/A")
            typer.echo(f"Location: {location}")
            if rule.get("description"):
                typer.echo(f"Description: {rule['description']}")
            if rule.get("action"):
                typer.echo(f"Action: {json.dumps(rule['action'], indent=2)}")
            if rule.get("schedule"):
                typer.echo(f"Schedule: {rule['schedule']}")
            if rule.get("id"):
                typer.echo(f"\nID: {rule['id']}")
            return rule
        else:
            rules = scm_client.list_qos_rules(folder=folder, snippet=snippet, device=device)
            if not rules:
                typer.echo("No QoS rules found")
                return
            typer.echo("\nQoS Rules:")
            typer.echo("-" * 80)
            for rule in rules:
                location = rule.get("folder") or rule.get("snippet") or rule.get("device", "N/A")
                typer.echo(f"Name: {rule.get('name', 'N/A')}")
                typer.echo(f"  Location: {location}")
                if rule.get("description"):
                    typer.echo(f"  Description: {rule['description']}")
                if rule.get("id"):
                    typer.echo(f"  ID: {rule['id']}")
                typer.echo("-" * 80)
            return rules
    except Exception as e:
        typer.echo(f"Error showing QoS rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
