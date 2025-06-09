"""Network module commands for scm.

This module implements set, delete, and load commands for network-related
configurations such as zones and interfaces.
"""

from datetime import datetime
from pathlib import Path

import typer
import yaml
from pydantic import ValidationError

from ..utils.config import load_from_yaml
from ..utils.sdk_client import scm_client
from ..utils.validators import Zone

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
