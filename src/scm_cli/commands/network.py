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

from ..utils.config import load_from_yaml
from ..utils.sdk_client import scm_client
from ..utils.validators import (
    AggregateInterface,
    DhcpInterface,
    EthernetInterface,
    IKECryptoProfile,
    IKEGateway,
    IPSecCryptoProfile,
    Layer2Subinterface,
    Layer3Subinterface,
    LoopbackInterface,
    NATRule,
    TunnelInterface,
    VlanInterface,
    Zone,
)

# ========================================================================================================================================================================================
# TYPER APP CONFIGURATION
# ========================================================================================================================================================================================

# Create app groups for each action type
set_app = typer.Typer(help="Create or update network configurations")
delete_app = typer.Typer(help="Remove network configurations")
load_app = typer.Typer(help="Load network configurations from YAML files")
show_app = typer.Typer(help="Display network configurations")
backup_app = typer.Typer(help="Backup network configurations to YAML files")

# ========================================================================================================================================================================================
# COMMAND OPTIONS
# ========================================================================================================================================================================================

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

# ========================================================================================================================================================================================
# HELPER FUNCTIONS
# ========================================================================================================================================================================================


def validate_location_params(folder: str = None, snippet: str = None, device: str = None) -> tuple[str, str]:
    """Validate that exactly one location parameter is provided.

    Returns:
        tuple: (location_type, location_value)

    """
    location_count = sum(1 for loc in [folder, snippet, device] if loc is not None)

    if location_count == 0:
        typer.echo("Error: One of --folder, --snippet, or --device must be specified", err=True)
        raise typer.Exit(code=1)
    elif location_count > 1:
        typer.echo(
            "Error: Only one of --folder, --snippet, or --device can be specified",
            err=True,
        )
        raise typer.Exit(code=1)

    if folder:
        return "folder", folder
    elif snippet:
        return "snippet", snippet
    else:
        return "device", device


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


# ========================================================================================================================================================================================
# IKE CRYPTO PROFILE COMMANDS
# ========================================================================================================================================================================================


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
            confirm = typer.confirm(f"Are you sure you want to delete IKE crypto profile '{name}'?")
            if not confirm:
                typer.echo("Deletion cancelled")
                raise typer.Exit(code=0)
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
    hash: list[str] = typer.Option(..., "--hash", help="Hash algorithms (sha256, sha384, sha512, sha1, md5)"),
    dh_group: list[str] = typer.Option(..., "--dh-group", help="DH groups (group1, group2, group5, group14, group19, group20)"),
    encryption: list[str] = typer.Option(..., "--encryption", help="Encryption algorithms (aes-256-cbc, aes-128-cbc, etc.)"),
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
        profile_data = {"name": name, "hash": hash, "dh_group": dh_group, "encryption": encryption, location_type: location_value}
        if lifetime_seconds is not None:
            profile_data["lifetime_seconds"] = lifetime_seconds
        if lifetime_minutes is not None:
            profile_data["lifetime_minutes"] = lifetime_minutes
        if lifetime_hours is not None:
            profile_data["lifetime_hours"] = lifetime_hours
        if lifetime_days is not None:
            profile_data["lifetime_days"] = lifetime_days
        if authentication_multiple is not None:
            profile_data["authentication_multiple"] = authentication_multiple
        validated_profile = IKECryptoProfile(**profile_data)
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


# ========================================================================================================================================================================================
# AGGREGATE INTERFACE COMMANDS
# ========================================================================================================================================================================================


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
            confirm = typer.confirm(f"Are you sure you want to delete aggregate interface '{name}'?")
            if not confirm:
                typer.echo("Deletion cancelled")
                raise typer.Exit(code=0)
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


# ========================================================================================================================================================================================
# IKE GATEWAY COMMANDS
# ========================================================================================================================================================================================


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
            confirm = typer.confirm(f"Are you sure you want to delete IKE gateway '{name}'?")
            if not confirm:
                typer.echo("Deletion cancelled")
                raise typer.Exit(code=0)
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
        if protocol_json:
            protocol = json.loads(protocol_json)
        else:
            protocol: dict[str, Any] = {"version": protocol_version}
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


# ========================================================================================================================================================================================
# SECURITY ZONE COMMANDS
# ========================================================================================================================================================================================


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

        typer.echo(f"Created zone: {result['name']} in folder {result['folder']}")
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


# ========================================================================================================================================================================================
# IPSEC CRYPTO PROFILE COMMANDS
# ========================================================================================================================================================================================


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
            name=name,
            esp_encryption=esp_encryption,
            esp_authentication=esp_authentication,
            dh_group=dh_group,
            lifetime_seconds=lifetime_seconds,
            lifetime_hours=lifetime_hours,
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
        typer.echo(f"IPsec crypto profile '{result['name']}' {action} in folder {result.get('folder', folder)}")
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


# ========================================================================================================================================================================================
# NAT RULE COMMANDS
# ========================================================================================================================================================================================


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


# ========================================================================================================================================================================================
# DHCP INTERFACE COMMANDS
# ========================================================================================================================================================================================


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
    """Delete a DHCP interface."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        iface = scm_client.get_dhcp_interface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            typer.echo(f"DHCP interface '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            confirm = typer.confirm(f"Are you sure you want to delete DHCP interface '{name}'?")
            if not confirm:
                typer.echo("Deletion cancelled")
                raise typer.Exit(code=0)
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


# ========================================================================================================================================================================================
# ETHERNET INTERFACE COMMANDS
# ========================================================================================================================================================================================


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
            confirm = typer.confirm(f"Are you sure you want to delete ethernet interface '{name}'?")
            if not confirm:
                typer.echo("Deletion cancelled")
                raise typer.Exit(code=0)
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


# ========================================================================================================================================================================================
# LAYER2 SUBINTERFACE COMMANDS
# ========================================================================================================================================================================================


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
    """Delete a layer2 subinterface."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        iface = scm_client.get_layer2_subinterface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            typer.echo(f"Layer2 subinterface '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            confirm = typer.confirm(f"Are you sure you want to delete layer2 subinterface '{name}'?")
            if not confirm:
                typer.echo("Deletion cancelled")
                raise typer.Exit(code=0)
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


# ========================================================================================================================================================================================
# LAYER3 SUBINTERFACE COMMANDS
# ========================================================================================================================================================================================


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
    """Delete a layer3 subinterface."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        iface = scm_client.get_layer3_subinterface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            typer.echo(f"Layer3 subinterface '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            confirm = typer.confirm(f"Are you sure you want to delete layer3 subinterface '{name}'?")
            if not confirm:
                typer.echo("Deletion cancelled")
                raise typer.Exit(code=0)
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


# ========================================================================================================================================================================================
# LOOPBACK INTERFACE COMMANDS
# ========================================================================================================================================================================================


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
    """Delete a loopback interface."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        iface = scm_client.get_loopback_interface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            typer.echo(f"Loopback interface '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            confirm = typer.confirm(f"Are you sure you want to delete loopback interface '{name}'?")
            if not confirm:
                typer.echo("Deletion cancelled")
                raise typer.Exit(code=0)
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


# ========================================================================================================================================================================================
# TUNNEL INTERFACE COMMANDS
# ========================================================================================================================================================================================


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
    """Delete a tunnel interface."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        iface = scm_client.get_tunnel_interface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            typer.echo(f"Tunnel interface '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            confirm = typer.confirm(f"Are you sure you want to delete tunnel interface '{name}'?")
            if not confirm:
                typer.echo("Deletion cancelled")
                raise typer.Exit(code=0)
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


# ========================================================================================================================================================================================
# VLAN INTERFACE COMMANDS
# ========================================================================================================================================================================================


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
    """Delete a VLAN interface."""
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        iface = scm_client.get_vlan_interface(name=name, folder=folder, snippet=snippet, device=device)
        if not iface:
            typer.echo(f"VLAN interface '{name}' not found", err=True)
            raise typer.Exit(code=1)
        if not force:
            confirm = typer.confirm(f"Are you sure you want to delete VLAN interface '{name}'?")
            if not confirm:
                typer.echo("Deletion cancelled")
                raise typer.Exit(code=0)
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
