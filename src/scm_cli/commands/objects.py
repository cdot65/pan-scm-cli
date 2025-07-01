"""Objects module commands for scm.

This module implements set, delete, and load commands for objects-related
configurations such as address-group, address, service-group, etc.
"""

from pathlib import Path
from typing import Any

import typer
import yaml

# Removed unused import: from the `..utils.config` import load_from_yaml
from ..utils.config import settings
from ..utils.context import get_current_context
from ..utils.sdk_client import scm_client
from ..utils.validators import (
    Address,
    AddressGroup,
    Application,
    ApplicationFilter,
    ApplicationGroup,
    DynamicUserGroup,
    ExternalDynamicList,
    HIPObject,
    HIPProfile,
    HTTPServerProfile,
    LogForwardingProfile,
    Service,
    ServiceGroup,
    SyslogServerProfile,
    Tag,
)

# ========================================================================================================================================================================================
# HELPER FUNCTIONS
# ========================================================================================================================================================================================


def show_context_info() -> None:
    """Display current context information if log level is INFO."""
    log_level = settings.get("log_level", "INFO").upper()
    if log_level == "INFO":
        current_context = get_current_context()
        if current_context:
            typer.echo(f"[INFO] Using authentication context: {current_context}", err=True)
        else:
            typer.echo(
                "[INFO] No context set, using environment variables or default settings",
                err=True,
            )


# ========================================================================================================================================================================================
# TYPER APP CONFIGURATION
# ========================================================================================================================================================================================

# Create app groups for each action type
set_app = typer.Typer(help="Create or update object configurations")
delete_app = typer.Typer(help="Remove object configurations")
load_app = typer.Typer(help="Load object configurations from YAML files")
show_app = typer.Typer(help="Display object configurations")
backup_app = typer.Typer(help="Backup object configurations to YAML files")

# ========================================================================================================================================================================================
# COMMAND OPTIONS
# ========================================================================================================================================================================================

# Define typer option constants
FOLDER_OPTION = typer.Option(
    None,
    "--folder",
    help="Folder path for the address group",
)
NAME_OPTION = typer.Option(
    None,
    "--name",
    help="Name of the address group",
)
TYPE_OPTION = typer.Option(
    None,
    "--type",
    help="Type of address group (static or dynamic)",
)
MEMBERS_OPTION = typer.Option(
    None,
    "--members",
    help="List of addresses in the group (for static groups)",
)
FILTER_OPTION = typer.Option(
    None,
    "--filter",
    help="Filter expression for dynamic address groups (e.g., \"'tag1' and 'tag2'\")",
)
DESCRIPTION_OPTION = typer.Option(
    None,
    "--description",
    help="Description of the address group",
)
TAGS_OPTION = typer.Option(
    None,
    "--tags",
    help="List of tags",
)
FILE_OPTION = typer.Option(
    None,
    "--file",
    help="YAML file to load configurations from",
)
DRY_RUN_OPTION = typer.Option(
    False,
    "--dry-run",
    help="Simulate execution without applying changes",
)

# Address-specific options
IP_NETMASK_OPTION = typer.Option(
    None,
    "--ip-netmask",
    help="IP address with CIDR notation (e.g. 192.168.1.0/24)",
)
IP_RANGE_OPTION = typer.Option(
    None,
    "--ip-range",
    help="IP address range (e.g. 192.168.1.1-192.168.1.10)",
)
IP_WILDCARD_OPTION = typer.Option(
    None,
    "--ip-wildcard",
    help="IP wildcard mask (e.g. 10.20.1.0/0.0.248.255)",
)
FQDN_OPTION = typer.Option(
    None,
    "--fqdn",
    help="Fully qualified domain name (e.g. example.com)",
)

# HIP Profile load options
HIP_PROFILE_FILE_OPTION = typer.Option(
    ...,
    "--file",
    help="YAML file containing HIP profiles",
)
HIP_PROFILE_FOLDER_OPTION = typer.Option(
    None,
    "--folder",
    help="Override folder path for all HIP profiles",
)
HIP_PROFILE_DRY_RUN_OPTION = typer.Option(
    False,
    "--dry-run",
    help="Preview changes without applying them",
)

# HTTP Server Profile load options
HTTP_SERVER_PROFILE_FILE_OPTION = typer.Option(
    ...,
    "--file",
    help="YAML file containing HTTP server profiles",
)
HTTP_SERVER_PROFILE_FOLDER_OPTION = typer.Option(
    None,
    "--folder",
    help="Override folder path for all HTTP server profiles",
)
HTTP_SERVER_PROFILE_DRY_RUN_OPTION = typer.Option(
    False,
    "--dry-run",
    help="Preview changes without applying them",
)

# Misc profile options for syslog, etc.
SNIPPET_OPTION = typer.Option(
    None,
    "--snippet",
    help="Snippet location",
)
DEVICE_OPTION = typer.Option(
    None,
    "--device",
    help="Device location",
)
TAG_OPTION = typer.Option(
    None,
    "--tag",
    help="Tags to apply",
)

# External Dynamic List options
EXCEPTION_LIST_OPTION = typer.Option(
    default_factory=list,
    help="Exception list entries",
)
RECURRING_OPTION = typer.Option(
    None,
    help="Update frequency (five_minute, hourly, daily, weekly, monthly)",
)
HOUR_OPTION = typer.Option(
    None,
    help="Hour for daily/weekly/monthly updates (00-23)",
)
DAY_OPTION = typer.Option(
    None,
    help="Day for weekly (sunday-saturday) or monthly (1-31) updates",
)
USERNAME_OPTION = typer.Option(
    None,
    help="Authentication username",
)
PASSWORD_OPTION = typer.Option(
    None,
    help="Authentication password",
)
CERTIFICATE_PROFILE_OPTION = typer.Option(
    None,
    help="Certificate profile for authentication",
)
EXPAND_DOMAIN_OPTION = typer.Option(
    False,
    help="Enable/Disable expand domain (for domain type)",
)

# Application-specific options
CATEGORY_OPTION = typer.Option(
    ...,
    "--category",
    help="High-level category (max 50 chars)",
)
SUBCATEGORY_OPTION = typer.Option(
    ...,
    "--subcategory",
    help="Specific sub-category (max 50 chars)",
)
TECHNOLOGY_OPTION = typer.Option(
    ...,
    "--technology",
    help="Underlying technology (max 50 chars)",
)
RISK_OPTION = typer.Option(
    ...,
    "--risk",
    min=1,
    max=5,
    help="Risk level (1-5)",
)
PORTS_OPTION = typer.Option(
    None,
    "--ports",
    help="List of TCP/UDP ports (e.g. tcp/80, udp/53)",
)
EVASIVE_OPTION = typer.Option(
    False,
    "--evasive",
    help="Uses evasive techniques",
)
PERVASIVE_OPTION = typer.Option(
    False,
    "--pervasive",
    help="Widely used",
)
EXCESSIVE_BANDWIDTH_OPTION = typer.Option(
    False,
    "--excessive-bandwidth-use",
    help="Uses excessive bandwidth",
)
USED_BY_MALWARE_OPTION = typer.Option(
    False,
    "--used-by-malware",
    help="Used by malware",
)
TRANSFERS_FILES_OPTION = typer.Option(
    False,
    "--transfers-files",
    help="Transfers files",
)
HAS_KNOWN_VULNERABILITIES_OPTION = typer.Option(
    False,
    "--has-known-vulnerabilities",
    help="Has known vulnerabilities",
)
TUNNELS_OTHER_APPS_OPTION = typer.Option(
    False,
    "--tunnels-other-apps",
    help="Tunnels other applications",
)
PRONE_TO_MISUSE_OPTION = typer.Option(
    False,
    "--prone-to-misuse",
    help="Prone to misuse",
)
NO_CERTIFICATIONS_OPTION = typer.Option(
    False,
    "--no-certifications",
    help="Lacks certifications",
)

# Application group-specific options
APP_GROUP_MEMBERS_OPTION = typer.Option(
    ...,
    "--members",
    help="List of application names in the group",
)

# Application filter-specific options
FILTER_CATEGORY_OPTION = typer.Option(
    ...,
    "--category",
    help="List of category strings to filter by",
)
FILTER_SUBCATEGORY_OPTION = typer.Option(
    ...,
    "--subcategory",
    help="List of subcategory strings to filter by",
)
FILTER_TECHNOLOGY_OPTION = typer.Option(
    ...,
    "--technology",
    help="List of technology strings to filter by",
)
FILTER_RISK_OPTION = typer.Option(
    ...,
    "--risk",
    help="List of risk levels (1-5) to filter by",
)

# Dynamic user group-specific options
FILTER_EXPRESSION_OPTION = typer.Option(
    ...,
    "--filter",
    help="Tag-based filter expression (e.g., \"tag.Department='IT' and tag.Role='Admin'\")",
)

# Standardized backup command options
BACKUP_FOLDER_OPTION = typer.Option(
    None,
    "--folder",
    help="Folder to backup configurations from",
)
BACKUP_SNIPPET_OPTION = typer.Option(
    None,
    "--snippet",
    help="Snippet to backup configurations from",
)
BACKUP_DEVICE_OPTION = typer.Option(
    None,
    "--device",
    help="Device to backup configurations from",
)
BACKUP_FILE_OPTION = typer.Option(
    None,
    "--file",
    help="Output file path (optional, defaults to {type}-{location}.yaml)",
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

# ========================================================================================================================================================================================
# HELPER FUNCTIONS
# ========================================================================================================================================================================================


def validate_location_params(folder: str = None, snippet: str = None, device: str = None) -> tuple[str, str]:
    """Validate that exactly one location parameter is provided.

    Returnas:
        tuple: (location_type, location_value)

    Raise:
        typer.Exit: If validation fails
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
    """Generate default backup filename based on object type and location."""
    # Sanitize location value for filename
    safe_location = location_value.lower().replace("/", "-").replace(" ", "-")
    return f"{object_type}-{safe_location}.yaml"


# ========================================================================================================================================================================================
# ADDRESS GROUP COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("address-group")
def backup_address_group(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup all address groups from a specified location to a YAML file.

    Examples
    --------
        # Backup from a folder
        scm backup object address-group --folder Austin

        # Backup from a folder with custom output file
        scm backup object address-group --folder Austin --file my-backups/austin-groups.yaml

        # Backup from a snippet (when supported by SDK)
        scm backup object address-group --snippet "Shared Objects"

        # Backup from a device (when supported by SDK)
        scm backup object address-group --device "FW-NYC-01"

    """
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # List all address groups in the location with exact_match=True
        kwargs = {location_type: location_value}
        groups = scm_client.list_address_groups(**kwargs, exact_match=True)

        if not groups:
            typer.echo(f"No address groups found in {location_type} '{location_value}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for group in groups:
            # The list method returns dict objects already, but let's ensure we exclude any None values
            group_dict = {k: v for k, v in group.items() if v is not None}
            # Remove system fields that shouldn't be in backup
            group_dict.pop("id", None)

            # Convert SDK format back to CLI format for consistency
            if "static" in group_dict:
                group_dict["type"] = "static"
                group_dict["members"] = group_dict.pop("static", [])
            elif "dynamic" in group_dict:
                group_dict["type"] = "dynamic"
                dynamic_info = group_dict.pop("dynamic", {})
                if dynamic_info.get("filter"):
                    group_dict["filter"] = dynamic_info["filter"]

            backup_data.append(group_dict)

        # Create the YAML structure
        yaml_data = {"address_groups": backup_data}

        # Generate filename
        if file is None:
            file = Path(get_default_backup_filename("address-group", location_type, location_value))

        # Write to YAML file
        with file.open("w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} address groups to {file}")
        return str(file)

    except Exception as e:
        typer.echo(f"Error backing up address groups: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("address-group")
def delete_address_group(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete an address group.

    Examples
    --------
        scm delete object address-group --folder Texas --name test123

    """
    try:
        result = scm_client.delete_address_group(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted address group: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting address group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("address-group", help="Load address groups from a YAML file.")
def load_address_group(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load address groups from a YAML file.

    Examples
    --------
        # Load from file with original locations
        scm load object address-group --file config/address_groups.yml

        # Load with folder override
        scm load object address-group --file config/address_groups.yml --folder Texas

        # Load with snippet override
        scm load object address-group --file config/address_groups.yml --snippet DNS-Best-Practice

        # Dry run to preview changes
        scm load object address-group --file config/address_groups.yml --dry-run

    """
    try:
        # Validate file exists
        if not file.exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)

        # Additionally load raw data for potential manipulation
        with file.open() as f:
            raw_data = yaml.safe_load(f)

        if not raw_data or "address_groups" not in raw_data:
            typer.echo("No address groups found in file", err=True)
            raise typer.Exit(code=1)

        address_groups = raw_data["address_groups"]
        if not isinstance(address_groups, list):
            address_groups = [address_groups]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            # Show override information if applicable
            if folder or snippet or device:
                typer.echo(f"Container override: {folder or snippet or device}")
            typer.echo(yaml.dump(address_groups))
            return

        # Apply each address group
        results: list[dict[str, Any]] = []
        created_count = 0
        updated_count = 0

        for ag_data in address_groups:
            try:
                # Apply container override if specified
                if folder:
                    ag_data["folder"] = folder
                    ag_data.pop("snippet", None)
                    ag_data.pop("device", None)
                elif snippet:
                    typer.echo(
                        f"Warning: Address groups do not support snippets. Skipping group '{ag_data.get('name', 'unknown')}'",
                        err=True,
                    )
                    continue
                elif device:
                    typer.echo(
                        f"Warning: Address groups do not support devices. Skipping group '{ag_data.get('name', 'unknown')}'",
                        err=True,
                    )
                    continue

                # Validate using the Pydantic model
                address_group = AddressGroup(**ag_data)

                # Call the SDK client to create the address group
                result = scm_client.create_address_group(
                    folder=address_group.folder,
                    name=address_group.name,
                    type=address_group.type,
                    members=address_group.members,
                    description=address_group.description,
                    tags=address_group.tags,
                )

                results.append(result)

                # Track if created or updated based on response
                if "created" in str(result).lower():
                    created_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                typer.echo(
                    f"Error processing address group '{ag_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                # Continue processing other objects
                continue

        # Display summary with counts
        typer.echo(f"Successfully processed {len(results)} address group(s):")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")

    except Exception as e:
        typer.echo(f"Error loading address groups: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("address-group")
def set_address_group(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    type: str = TYPE_OPTION,
    members: list[str] | None = MEMBERS_OPTION,
    filter: str | None = FILTER_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    tags: list[str] | None = TAGS_OPTION,
):
    r"""Create or update an address group.

    Example:
    -------
        # Static address group
        scm set object address-group \
        --folder Texas \
        --name test-static \
        --type static \
        --members ["addr1", "addr2"] \
        --description "test static group"

        # Dynamic address group
        scm set object address-group \
        --folder Texas \
        --name test-dynamic \
        --type dynamic \
        --filter "'web' and 'production'" \
        --description "test dynamic group"

    """
    try:
        # Validate inputs using the Pydantic model
        address_group = AddressGroup(
            folder=folder,
            name=name,
            type=type,
            members=members or [],
            filter=filter,
            description=description or "",
            tags=tags or [],
        )

        # Call the SDK client to create the address group
        result = scm_client.create_address_group(
            folder=address_group.folder,
            name=address_group.name,
            type=address_group.type,
            members=address_group.members,
            filter=address_group.filter,
            description=address_group.description,
            tags=address_group.tags,
        )

        typer.echo(f"Created address group: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating address group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("address-group")
def show_address_group(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the address group to show"),
):
    """Display address group objects.

    Examples
    --------
        # List all address groups in a folder (default behavior)
        scm show object address-group --folder Texas

        # Show a specific address group by name
        scm show object address-group --folder Texas --name web-servers

    """
    try:
        if name:
            # Get a specific address group by name
            group = scm_client.get_address_group(folder=folder, name=name)

            typer.echo(f"Address Group: {group.get('name', 'N/A')}")

            # Display container location (folder, snippet, or device)
            if group.get("folder"):
                typer.echo(f"Location: Folder '{group['folder']}'")
            elif group.get("snippet"):
                typer.echo(f"Location: Snippet '{group['snippet']}'")
            elif group.get("device"):
                typer.echo(f"Location: Device '{group['device']}'")
            else:
                typer.echo("Location: N/A")

            # Determine type based on presence of 'static' or 'dynamic' key
            if group.get("static") is not None:
                typer.echo("Type: static")
                typer.echo(f"Description: {group.get('description', 'N/A')}")
                members = group.get("static", [])
                if members:
                    typer.echo(f"Members ({len(members)}):")
                    for member in members:
                        typer.echo(f"  - {member}")
                else:
                    typer.echo("Members: None")
            elif group.get("dynamic") is not None:
                typer.echo("Type: dynamic")
                typer.echo(f"Description: {group.get('description', 'N/A')}")
                dynamic_info = group.get("dynamic", {})
                if dynamic_info.get("filter"):
                    typer.echo(f"Filter: {dynamic_info['filter']}")
                else:
                    typer.echo("Filter: None")
            else:
                typer.echo("Type: unknown")
                typer.echo(f"Description: {group.get('description', 'N/A')}")

            # Display tags if present
            if group.get("tag"):
                typer.echo(f"Tags: {', '.join(group['tag'])}")

            # Display ID if present
            if group.get("id"):
                typer.echo(f"ID: {group['id']}")

            return group

        else:
            # Default behavior: list all address groups in the folder
            groups = scm_client.list_address_groups(folder=folder)

            if not groups:
                typer.echo(f"No address groups found in folder '{folder}'")
                return

            typer.echo(f"Address Groups in folder '{folder}':")
            typer.echo("-" * 60)

            for group in groups:
                # Display address group information
                typer.echo(f"Name: {group.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if group.get("folder"):
                    typer.echo(f"  Location: Folder '{group['folder']}'")
                elif group.get("snippet"):
                    typer.echo(f"  Location: Snippet '{group['snippet']}'")
                elif group.get("device"):
                    typer.echo(f"  Location: Device '{group['device']}'")
                else:
                    typer.echo("  Location: N/A")

                # Determine type based on presence of 'static' or 'dynamic' key
                if group.get("static") is not None:
                    typer.echo("  Type: static")
                    typer.echo(f"  Members: {', '.join(group.get('static', []))}")
                elif group.get("dynamic") is not None:
                    typer.echo("  Type: dynamic")
                    dynamic_info = group.get("dynamic", {})
                    if dynamic_info.get("filter"):
                        typer.echo(f"  Filter: {dynamic_info['filter']}")

                typer.echo(f"  Description: {group.get('description', 'N/A')}")

                # Display tags if present
                if group.get("tag"):
                    typer.echo(f"  Tags: {', '.join(group['tag'])}")

                typer.echo("-" * 60)

            return groups

    except Exception as e:
        typer.echo(f"Error showing address group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# ADDRESS OBJECT COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("address")
def backup_address(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup all address object from a specified location to a YAML file.

    Examples
    --------
        # Backup from a folder
        scm backup object address --folder Austin

        # Backup with custom output file
        scm backup object address --folder Austin --file addresses-backup.yaml

        # Backup from a snippet (when supported by SDK)
        scm backup object address --snippet "Shared Objects"

    """
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # List all addresses in the location with exact_match=True
        kwargs = {location_type: location_value}
        addresses = scm_client.list_addresses(**kwargs, exact_match=True)

        if not addresses:
            typer.echo(f"No addresses found in {location_type} '{location_value}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for addr in addresses:
            # The list method returns dict objects already, but let's ensure we exclude any None values
            addr_dict = {k: v for k, v in addr.items() if v is not None}
            # Remove system fields that shouldn't be in backup
            addr_dict.pop("id", None)
            backup_data.append(addr_dict)

        # Create the YAML structure
        yaml_data = {"addresses": backup_data}

        # Generate filename
        if file is None:
            file = Path(get_default_backup_filename("address", location_type, location_value))

        # Write to YAML file
        with file.open("w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} addresses to {file}")
        return str(file)

    except Exception as e:
        typer.echo(f"Error backing up addresses: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("address")
def delete_address(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete an address object.

    Examples
    --------
        scm delete object address --folder Texas --name webserver

    """
    try:
        result = scm_client.delete_address(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted address: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting address: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("address", help="Load addresses from a YAML file.")
def load_address(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load address object from a YAML file.

    Examples:
        # Load from file with original locations
        scm load object address --file config/addresses.yml

        # Load with folder override
        scm load object address --file config/addresses.yml --folder Production

        # Load with snippet override
        scm load object address --file config/addresses.yml --snippet DNS-Best-Practice

        # Dry run to preview changes
        scm load object address --file config/addresses.yml --dry-run

    """
    try:
        # Validate container override parameters
        if sum(1 for x in [folder, snippet, device] if x is not None) > 1:
            typer.echo(
                "Error: Only one of --folder, --snippet, or --device can be specified",
                err=True,
            )
            raise typer.Exit(code=1)

        # Validate file exists
        if not file.exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)

        # Load YAML data using the same pattern as other commands
        with open(file) as f:
            raw_data = yaml.safe_load(f)

        if not raw_data or "addresses" not in raw_data:
            typer.echo("No addresses found in file", err=True)
            raise typer.Exit(code=1)

        addresses = raw_data["addresses"]
        if not isinstance(addresses, list):
            addresses = [addresses]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            # Show override information if applicable
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(addresses))
            return

        # Apply each address
        results: list[dict[str, Any]] = []
        created_count = 0
        updated_count = 0

        for addr_data in addresses:
            try:
                # Apply container override if specified
                if folder:
                    addr_data["folder"] = folder
                    addr_data.pop("snippet", None)
                    addr_data.pop("device", None)
                elif snippet:
                    addr_data["snippet"] = snippet
                    addr_data.pop("folder", None)
                    addr_data.pop("device", None)
                elif device:
                    addr_data["device"] = device
                    addr_data.pop("folder", None)
                    addr_data.pop("snippet", None)

                # Validate using the Pydantic model
                address = Address(**addr_data)

                # Call the SDK client to create the address
                result = scm_client.create_address(
                    folder=address.folder,
                    name=address.name,
                    description=address.description,
                    tags=address.tags,
                    ip_netmask=address.ip_netmask,
                    ip_range=address.ip_range,
                    ip_wildcard=address.ip_wildcard,
                    fqdn=address.fqdn,
                )

                results.append(result)

                # Track if created or updated based on response
                if "created" in str(result).lower():
                    created_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                typer.echo(
                    f"Error processing address '{addr_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                # Continue processing other addresses
                continue

        # Display summary with counts
        typer.echo(f"Successfully processed {len(results)} address(es):")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")

    except Exception as e:
        typer.echo(f"Error loading addresses: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("address")
def set_address(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    tags: list[str] | None = TAGS_OPTION,
    ip_netmask: str | None = IP_NETMASK_OPTION,
    ip_range: str | None = IP_RANGE_OPTION,
    ip_wildcard: str | None = IP_WILDCARD_OPTION,
    fqdn: str | None = FQDN_OPTION,
):
    r"""Create or update an address object.

    Example:
    -------
        scm set object address \
        --folder Texas \
        --name webserver \
        --ip-netmask 192.168.1.100/32 \
        --description "Web server" \
        --tags ["server", "web"]

    Note: Exactly one of ip-netmask, ip-range, ip-wildcard, or fqdn must be provided.

    """
    try:
        # Validate inputs using the Pydantic model
        address_data: dict[str, Any] = {
            "folder": folder,
            "name": name,
            "tags": tags or [],
            "ip_netmask": ip_netmask,
            "ip_range": ip_range,
            "ip_wildcard": ip_wildcard,
            "fqdn": fqdn,
        }

        # Only include description if provided
        if description is not None:
            address_data["description"] = description

        address = Address(**address_data)

        # Call the SDK client to create the address
        result = scm_client.create_address(
            folder=address.folder,
            name=address.name,
            description=description,  # Pass None if not provided, not empty string
            tags=address.tags,
            ip_netmask=address.ip_netmask,
            ip_range=address.ip_range,
            ip_wildcard=address.ip_wildcard,
            fqdn=address.fqdn,
        )

        # Get the action performed
        action = result.pop("__action__", "created")

        if action == "created":
            typer.echo(f"✅ Created address: {result['name']} in folder {result['folder']}")
        elif action == "updated":
            typer.echo(f"✅ Updated address: {result['name']} in folder {result['folder']}")
        elif action == "no_change":
            typer.echo(f"ℹ️  No changes needed for address: {result['name']} in folder {result['folder']}")

        return result
    except Exception as e:
        typer.echo(f"Error creating address: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("address")
def show_address(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the address to show"),
):
    """Display address objects.

    Example:
    -------
        # List all addresses in a folder (default behavior)
        scm show object address --folder Texas

        # Show a specific address by name
        scm show object address --folder Texas --name webserver

    """
    try:
        # Show context info if log level is INFO
        show_context_info()

        if name:
            # Get a specific address by name
            address = scm_client.get_address(folder=folder, name=name)

            typer.echo(f"Address: {address.get('name', 'N/A')}")

            # Display container location (folder, snippet, or device)
            if address.get("folder"):
                typer.echo(f"Location: Folder '{address['folder']}'")
            elif address.get("snippet"):
                typer.echo(f"Location: Snippet '{address['snippet']}'")
            elif address.get("device"):
                typer.echo(f"Location: Device '{address['device']}'")
            else:
                typer.echo("Location: N/A")

            typer.echo(f"Description: {address.get('description', 'N/A')}")

            # Display the address type and value
            if address.get("ip_netmask"):
                typer.echo("Type: IP/Netmask")
                typer.echo(f"Value: {address['ip_netmask']}")
            elif address.get("ip_range"):
                typer.echo("Type: IP Range")
                typer.echo(f"Value: {address['ip_range']}")
            elif address.get("ip_wildcard"):
                typer.echo("Type: IP Wildcard")
                typer.echo(f"Value: {address['ip_wildcard']}")
            elif address.get("fqdn"):
                typer.echo("Type: FQDN")
                typer.echo(f"Value: {address['fqdn']}")

            # Display tags if present
            if address.get("tag"):
                typer.echo(f"Tags: {', '.join(address['tag'])}")

            # Display ID if present
            if address.get("id"):
                typer.echo(f"ID: {address['id']}")

            return address

        else:
            # Default behavior: list all addresses in the folder
            addresses = scm_client.list_addresses(folder=folder)

            if not addresses:
                typer.echo(f"No addresses found in folder '{folder}'")
                return

            typer.echo(f"Addresses in folder '{folder}':")
            typer.echo("-" * 60)

            for addr in addresses:
                # Display address information
                typer.echo(f"Name: {addr.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if addr.get("folder"):
                    typer.echo(f"  Location: Folder '{addr['folder']}'")
                elif addr.get("snippet"):
                    typer.echo(f"  Location: Snippet '{addr['snippet']}'")
                elif addr.get("device"):
                    typer.echo(f"  Location: Device '{addr['device']}'")
                else:
                    typer.echo("  Location: N/A")

                typer.echo(f"  Description: {addr.get('description', 'N/A')}")

                # Display the address type and value
                if addr.get("ip_netmask"):
                    typer.echo("  Type: IP/Netmask")
                    typer.echo(f"  Value: {addr['ip_netmask']}")
                elif addr.get("ip_range"):
                    typer.echo("  Type: IP Range")
                    typer.echo(f"  Value: {addr['ip_range']}")
                elif addr.get("ip_wildcard"):
                    typer.echo("  Type: IP Wildcard")
                    typer.echo(f"  Value: {addr['ip_wildcard']}")
                elif addr.get("fqdn"):
                    typer.echo("  Type: FQDN")
                    typer.echo(f"  Value: {addr['fqdn']}")

                # Display tags if present
                if addr.get("tag"):
                    typer.echo(f"  Tags: {', '.join(addr['tag'])}")

                typer.echo("-" * 60)

            return addresses

    except Exception as e:
        typer.echo(f"Error showing address: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# APPLICATION COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("application")
def backup_application(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup all applications from a specified location to a YAML file.

    Examples
    --------
        # Backup from a folder
        scm backup object application --folder Austin

        # Backup with custom output file
        scm backup object application --folder Austin --file apps-backup.yaml

    """
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # List all applications in the location with exact_match=True
        kwargs = {location_type: location_value}
        applications = scm_client.list_applications(**kwargs, exact_match=True)

        if not applications:
            typer.echo(f"No applications found in {location_type} '{location_value}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for app in applications:
            # The list method returns dict objects already, but let's ensure we exclude any None values
            app_dict = {k: v for k, v in app.items() if v is not None}
            # Remove system fields that shouldn't be in backup
            app_dict.pop("id", None)
            backup_data.append(app_dict)

        # Create the YAML structure
        yaml_data = {"applications": backup_data}

        # Generate filename
        if file is None:
            file = Path(get_default_backup_filename("application", location_type, location_value))

        # Write to YAML file
        with file.open("w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} applications to {file}")
        return str(file)

    except Exception as e:
        typer.echo(f"Error backing up applications: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("application")
def delete_application(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete an application.

    Example:
    -------
    scm delete object application --folder Texas --name custom-app

    """
    try:
        result = scm_client.delete_application(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted application: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting application: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("application", help="Load applications from a YAML file.")
def load_application(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load applications from a YAML file.

    Examples
    --------
        # Load from file with original locations
        scm load object application --file config/applications.yml

        # Load with folder override
        scm load object application --file config/applications.yml --folder Texas

        # Load with snippet override
        scm load object application --file config/applications.yml --snippet DNS-Best-Practice

        # Dry run to preview changes
        scm load object application --file config/applications.yml --dry-run

    """
    try:
        # Validate file exists
        if not file.exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)

        # Additionally load raw data for potential manipulation
        with file.open() as f:
            raw_data = yaml.safe_load(f)

        if not raw_data or "applications" not in raw_data:
            typer.echo("No applications found in file", err=True)
            raise typer.Exit(code=1)

        applications = raw_data["applications"]
        if not isinstance(applications, list):
            applications = [applications]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            # Show override information if applicable
            if folder or snippet or device:
                typer.echo(f"Container override: {folder or snippet or device}")
            typer.echo(yaml.dump(applications))
            return

        # Apply each application
        results: list[dict[str, Any]] = []
        created_count = 0
        updated_count = 0

        for app_data in applications:
            try:
                # Apply container override if specified
                if folder:
                    app_data["folder"] = folder
                    app_data.pop("snippet", None)
                    app_data.pop("device", None)
                elif snippet:
                    typer.echo(
                        f"Warning: Applications do not support snippets. Skipping application '{app_data.get('name', 'unknown')}'",
                        err=True,
                    )
                    continue
                elif device:
                    typer.echo(
                        f"Warning: Applications do not support devices. Skipping application '{app_data.get('name', 'unknown')}'",
                        err=True,
                    )
                    continue

                # Validate using the Pydantic model
                application = Application(**app_data)

                # Call the SDK client to create the application
                result = scm_client.create_application(
                    folder=application.folder,
                    name=application.name,
                    category=application.category,
                    subcategory=application.subcategory,
                    technology=application.technology,
                    risk=application.risk,
                    description=application.description,
                    ports=application.ports,
                    evasive=application.evasive,
                    pervasive=application.pervasive,
                    excessive_bandwidth_use=application.excessive_bandwidth_use,
                    used_by_malware=application.used_by_malware,
                    transfers_files=application.transfers_files,
                    has_known_vulnerabilities=application.has_known_vulnerabilities,
                    tunnels_other_apps=application.tunnels_other_apps,
                    prone_to_misuse=application.prone_to_misuse,
                    no_certifications=application.no_certifications,
                )

                results.append(result)

                # Track if created or updated based on response
                if "created" in str(result).lower():
                    created_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                typer.echo(
                    f"Error processing application '{app_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                # Continue processing other objects
                continue

        # Display summary with counts
        typer.echo(f"Successfully processed {len(results)} application(s):")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")

    except Exception as e:
        typer.echo(f"Error loading applications: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("application")
def set_application(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    category: str = CATEGORY_OPTION,
    subcategory: str = SUBCATEGORY_OPTION,
    technology: str = TECHNOLOGY_OPTION,
    risk: int = RISK_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    ports: list[str] | None = PORTS_OPTION,
    tags: list[str] | None = TAGS_OPTION,
    evasive: bool = EVASIVE_OPTION,
    pervasive: bool = PERVASIVE_OPTION,
    excessive_bandwidth_use: bool = EXCESSIVE_BANDWIDTH_OPTION,
    used_by_malware: bool = USED_BY_MALWARE_OPTION,
    transfers_files: bool = TRANSFERS_FILES_OPTION,
    has_known_vulnerabilities: bool = HAS_KNOWN_VULNERABILITIES_OPTION,
    tunnels_other_apps: bool = TUNNELS_OTHER_APPS_OPTION,
    prone_to_misuse: bool = PRONE_TO_MISUSE_OPTION,
    no_certifications: bool = NO_CERTIFICATIONS_OPTION,
):
    r"""Create or update an application.

    Example:
    -------
        scm set object application \
        --folder Texas \
        --name custom-database \
        --category business-systems \
        --subcategory database \
        --technology client-server \
        --risk 3 \
        --description "Custom database application" \
        --ports ["tcp/1521", "tcp/1522"] \
        --transfers-files

    """
    try:
        # Validate inputs using the Pydantic model
        application = Application(
            folder=folder,
            name=name,
            category=category,
            subcategory=subcategory,
            technology=technology,
            risk=risk,
            description=description or "",
            ports=ports or [],
            evasive=evasive,
            pervasive=pervasive,
            excessive_bandwidth_use=excessive_bandwidth_use,
            used_by_malware=used_by_malware,
            transfers_files=transfers_files,
            has_known_vulnerabilities=has_known_vulnerabilities,
            tunnels_other_apps=tunnels_other_apps,
            prone_to_misuse=prone_to_misuse,
            no_certifications=no_certifications,
        )

        # Call the SDK client to create the application
        result = scm_client.create_application(
            folder=application.folder,
            name=application.name,
            category=application.category,
            subcategory=application.subcategory,
            technology=application.technology,
            risk=application.risk,
            description=application.description,
            ports=application.ports,
            evasive=application.evasive,
            pervasive=application.pervasive,
            excessive_bandwidth_use=application.excessive_bandwidth_use,
            used_by_malware=application.used_by_malware,
            transfers_files=application.transfers_files,
            has_known_vulnerabilities=application.has_known_vulnerabilities,
            tunnels_other_apps=application.tunnels_other_apps,
            prone_to_misuse=application.prone_to_misuse,
            no_certifications=application.no_certifications,
        )

        typer.echo(f"Created application: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating application: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("application")
def show_application(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the application to show"),
):
    """Display application objects.

    Examples
    --------
        # List all applications in a folder (default behavior)
        scm show object application --folder Texas

        # Show a specific application by name
        scm show object application --folder Texas --name custom-database

    """
    try:
        if name:
            # Get a specific application by name
            application = scm_client.get_application(folder=folder, name=name)

            typer.echo(f"Application: {application.get('name', 'N/A')}")

            # Display container location (folder, snippet, or device)
            if application.get("folder"):
                typer.echo(f"Location: Folder '{application['folder']}'")
            elif application.get("snippet"):
                typer.echo(f"Location: Snippet '{application['snippet']}'")
            elif application.get("device"):
                typer.echo(f"Location: Device '{application['device']}'")
            else:
                typer.echo("Location: N/A")

            typer.echo(f"Category: {application.get('category', 'N/A')}")
            typer.echo(f"Subcategory: {application.get('subcategory', 'N/A')}")
            typer.echo(f"Technology: {application.get('technology', 'N/A')}")
            typer.echo(f"Risk: {application.get('risk', 'N/A')}")
            typer.echo(f"Description: {application.get('description', 'N/A')}")

            # Display ports if present
            if application.get("ports"):
                typer.echo(f"Ports: {', '.join(application['ports'])}")

            # Display security attributes
            typer.echo("Security Attributes:")
            typer.echo(f"  Evasive: {application.get('evasive', False)}")
            typer.echo(f"  Pervasive: {application.get('pervasive', False)}")
            typer.echo(f"  Excessive Bandwidth Use: {application.get('excessive_bandwidth_use', False)}")
            typer.echo(f"  Used by Malware: {application.get('used_by_malware', False)}")
            typer.echo(f"  Transfers Files: {application.get('transfers_files', False)}")
            typer.echo(f"  Has Known Vulnerabilities: {application.get('has_known_vulnerabilities', False)}")
            typer.echo(f"  Tunnels Other Apps: {application.get('tunnels_other_apps', False)}")
            typer.echo(f"  Prone to Misuse: {application.get('prone_to_misuse', False)}")
            typer.echo(f"  No Certifications: {application.get('no_certifications', False)}")

            # Display ID if present
            if application.get("id"):
                typer.echo(f"ID: {application['id']}")

            return application

        else:
            # List all applications in the folder (default behavior)
            applications = scm_client.list_applications(folder=folder)

            if not applications:
                typer.echo(f"No applications found in folder '{folder}'")
                return

            typer.echo(f"Applications in folder '{folder}':")
            typer.echo("-" * 60)

            for app in applications:
                # Display application information
                typer.echo(f"Name: {app.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if app.get("folder"):
                    typer.echo(f"  Location: Folder '{app['folder']}'")
                elif app.get("snippet"):
                    typer.echo(f"  Location: Snippet '{app['snippet']}'")
                elif app.get("device"):
                    typer.echo(f"  Location: Device '{app['device']}'")
                else:
                    typer.echo("  Location: N/A")

                typer.echo(f"  Category: {app.get('category', 'N/A')}")
                typer.echo(f"  Subcategory: {app.get('subcategory', 'N/A')}")
                typer.echo(f"  Technology: {app.get('technology', 'N/A')}")
                typer.echo(f"  Risk: {app.get('risk', 'N/A')}")
                typer.echo(f"  Description: {app.get('description', 'N/A')}")

                # Display ports if present
                if app.get("ports"):
                    typer.echo(f"  Ports: {', '.join(app['ports'])}")

                # Display security attributes if any are true
                attrs = []
                if app.get("evasive"):
                    attrs.append("Evasive")
                if app.get("pervasive"):
                    attrs.append("Pervasive")
                if app.get("excessive_bandwidth_use"):
                    attrs.append("Excessive Bandwidth")
                if app.get("used_by_malware"):
                    attrs.append("Used by Malware")
                if app.get("transfers_files"):
                    attrs.append("Transfers Files")
                if app.get("has_known_vulnerabilities"):
                    attrs.append("Has Vulnerabilities")
                if app.get("tunnels_other_apps"):
                    attrs.append("Tunnels Apps")
                if app.get("prone_to_misuse"):
                    attrs.append("Prone to Misuse")
                if app.get("no_certifications"):
                    attrs.append("No Certifications")

                if attrs:
                    typer.echo(f"  Attributes: {', '.join(attrs)}")

                typer.echo("-" * 60)

            return applications

    except Exception as e:
        typer.echo(f"Error showing application: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# APPLICATION GROUP COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("application-group")
def backup_application_group(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup all application groups from a specified location to a YAML file.

    Examples
    --------
        # Backup from a folder
        scm backup object application-group --folder Austin

        # Backup with custom output file
        scm backup object application-group --folder Austin --file app-groups.yaml

    """
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # List all application groups in the location with exact_match=True
        kwargs = {location_type: location_value}
        groups = scm_client.list_application_groups(**kwargs, exact_match=True)

        if not groups:
            typer.echo(f"No application groups found in {location_type} '{location_value}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for group in groups:
            # The list method returns dict object already, but let's ensure we exclude any None values
            group_dict = {k: v for k, v in group.items() if v is not None}
            # Remove system fields that shouldn't be in backup
            group_dict.pop("id", None)
            backup_data.append(group_dict)

        # Create the YAML structure
        yaml_data = {"application_groups": backup_data}

        # Generate filename
        if file is None:
            file = Path(get_default_backup_filename("application-group", location_type, location_value))

        # Write to YAML file
        with file.open("w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} application groups to {file}")
        return str(file)

    except Exception as e:
        typer.echo(f"Error backing up application groups: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("application-group")
def delete_application_group(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete an application group.

    Example:
    -------
    scm delete object application-group --folder Texas --name web-apps

    """
    try:
        result = scm_client.delete_application_group(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted application group: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting application group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("application-group", help="Load application groups from a YAML file.")
def load_application_group(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load application groups from a YAML file.

    Example:
    -------
    scm load object application-group --file config/application_groups.yml

    """
    try:
        # Validate container override parameters
        validate_location_params(folder, snippet, device)

        # Validate file exists
        if not file.exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)

        # Load YAML data
        with file.open() as f:
            data = yaml.safe_load(f)

        if not data or "application_groups" not in data:
            typer.echo("No application groups found in file", err=True)
            raise typer.Exit(code=1)

        application_groups = data["application_groups"]
        if not isinstance(application_groups, list):
            application_groups = [application_groups]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            if folder or snippet or device:
                typer.echo(f"Container override: {folder or snippet or device}")
            typer.echo(yaml.dump(application_groups))
            return

        # Apply each application group
        results: list[dict[str, Any]] = []
        created_count = 0
        updated_count = 0

        for group_data in application_groups:
            try:
                # Apply container overrides if specified
                if folder:
                    group_data["folder"] = folder
                    group_data.pop("snippet", None)
                    group_data.pop("device", None)
                elif snippet:
                    group_data["snippet"] = snippet
                    group_data.pop("folder", None)
                    group_data.pop("device", None)
                elif device:
                    group_data["device"] = device
                    group_data.pop("folder", None)
                    group_data.pop("snippet", None)

                # Validate using the Pydantic model
                app_group = ApplicationGroup(**group_data)

                # Call the SDK client to create the application group
                result = scm_client.create_application_group(
                    folder=app_group.folder,
                    name=app_group.name,
                    members=app_group.members,
                )

                results.append(result)
                created_count += 1

            except Exception as e:
                typer.echo(
                    f"Error processing application group '{group_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                continue

        # Display summary with counts
        typer.echo(f"Successfully processed {len(results)} application group(s)")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")

    except Exception as e:
        typer.echo(f"Error loading application groups: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("application-group")
def set_application_group(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    members: list[str] = APP_GROUP_MEMBERS_OPTION,
):
    r"""Create or update an application group.

    Example:
    -------
        scm set object application-group \
        --folder Texas \
        --name web-apps \
        --members ["ssl", "web-browsing", "http", "https"]

    """
    try:
        # Validate inputs using the Pydantic model
        app_group = ApplicationGroup(
            folder=folder,
            name=name,
            members=members,
        )

        # Call the SDK client to create the application group
        result = scm_client.create_application_group(
            folder=app_group.folder,
            name=app_group.name,
            members=app_group.members,
        )

        typer.echo(f"Created application group: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating application group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("application-group")
def show_application_group(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the application group to show"),
):
    """Display application group objects.

    Examples
    --------
        # List all application groups in a folder (default behavior)
        scm show object application-group --folder Texas

        # Show a specific application group by name
        scm show object application-group --folder Texas --name web-apps

    """
    try:
        if name:
            # Get a specific application group by name
            group = scm_client.get_application_group(folder=folder, name=name)

            typer.echo(f"Application Group: {group.get('name', 'N/A')}")

            # Display container location (folder, snippet, or device)
            if group.get("folder"):
                typer.echo(f"Location: Folder '{group['folder']}'")
            elif group.get("snippet"):
                typer.echo(f"Location: Snippet '{group['snippet']}'")
            elif group.get("device"):
                typer.echo(f"Location: Device '{group['device']}'")
            else:
                typer.echo("Location: N/A")

            # Display members
            members = group.get("members", [])
            if members:
                typer.echo(f"Members ({len(members)}):")
                for member in members:
                    typer.echo(f"  - {member}")
            else:
                typer.echo("Members: None")

            # Display ID if present
            if group.get("id"):
                typer.echo(f"ID: {group['id']}")

            return group

        else:
            # List all application groups in the folder (default behavior)
            groups = scm_client.list_application_groups(folder=folder)

            if not groups:
                typer.echo(f"No application groups found in folder '{folder}'")
                return

            typer.echo(f"Application Groups in folder '{folder}':")
            typer.echo("-" * 60)

            for group in groups:
                # Display application group information
                typer.echo(f"Name: {group.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if group.get("folder"):
                    typer.echo(f"  Location: Folder '{group['folder']}'")
                elif group.get("snippet"):
                    typer.echo(f"  Location: Snippet '{group['snippet']}'")
                elif group.get("device"):
                    typer.echo(f"  Location: Device '{group['device']}'")
                else:
                    typer.echo("  Location: N/A")

                # Display members
                members = group.get("members", [])
                if members:
                    typer.echo(f"  Members ({len(members)}): {', '.join(members)}")
                else:
                    typer.echo("  Members: None")

                typer.echo("-" * 60)

            return groups

    except Exception as e:
        typer.echo(f"Error showing application group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# APPLICATION FILTER COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("application-filter")
def backup_application_filter(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup all application filters from a specified location to a YAML file.

    Examples
    --------
        # Backup from a folder
        scm backup object application-filter --folder Austin

        # Backup with custom output file
        scm backup object application-filter --folder Austin --file app-filters.yaml

    """
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # List all application filters in the location with exact_match=True
        kwargs = {location_type: location_value}
        filters = scm_client.list_application_filters(**kwargs, exact_match=True)

        if not filters:
            typer.echo(f"No application filters found in {location_type} '{location_value}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for filter_obj in filters:
            # The list method returns dict object already, but let's ensure we exclude any None values
            filter_dict = {k: v for k, v in filter_obj.items() if v is not None}
            # Remove system fields that shouldn't be in backup
            filter_dict.pop("id", None)
            backup_data.append(filter_dict)

        # Create the YAML structure
        yaml_data = {"application_filters": backup_data}

        # Generate filename
        if file is None:
            file = Path(get_default_backup_filename("application-filter", location_type, location_value))

        # Write to YAML file
        with file.open("w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} application filters to {file}")
        return str(file)

    except Exception as e:
        typer.echo(f"Error backing up application filters: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("application-filter")
def delete_application_filter(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete an application filter.

    Example:
    -------
    scm delete object application-filter --folder Texas --name high-risk-apps

    """
    try:
        result = scm_client.delete_application_filter(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted application filter: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting application filter: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("application-filter", help="Load application filters from a YAML file.")
def load_application_filter(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load application filters from a YAML file.

    Example:
    -------
    scm load object application-filter --file config/application_filters.yml

    """
    try:
        # Validate container override parameters
        validate_location_params(folder, snippet, device)

        # Validate file exists
        if not file.exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)

        # Load YAML data
        with file.open() as f:
            data = yaml.safe_load(f)

        if not data or "application_filters" not in data:
            typer.echo("No application filters found in file", err=True)
            raise typer.Exit(code=1)

        application_filters = data["application_filters"]
        if not isinstance(application_filters, list):
            application_filters = [application_filters]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            if folder or snippet or device:
                typer.echo(f"Container override: {folder or snippet or device}")
            typer.echo(yaml.dump(application_filters))
            return

        # Apply each application filter
        results: list[dict[str, Any]] = []
        created_count = 0
        updated_count = 0

        for filter_data in application_filters:
            try:
                # Apply container overrides if specified
                if folder:
                    filter_data["folder"] = folder
                    filter_data.pop("snippet", None)
                    filter_data.pop("device", None)
                elif snippet:
                    filter_data["snippet"] = snippet
                    filter_data.pop("folder", None)
                    filter_data.pop("device", None)
                elif device:
                    filter_data["device"] = device
                    filter_data.pop("folder", None)
                    filter_data.pop("snippet", None)

                # Validate using the Pydantic model
                app_filter = ApplicationFilter(**filter_data)

                # Call the SDK client to create the application filter
                result = scm_client.create_application_filter(
                    folder=app_filter.folder,
                    name=app_filter.name,
                    category=app_filter.category,
                    subcategory=app_filter.subcategory,
                    technology=app_filter.technology,
                    risk=app_filter.risk,
                    evasive=app_filter.evasive,
                    pervasive=app_filter.pervasive,
                    excessive_bandwidth_use=app_filter.excessive_bandwidth_use,
                    used_by_malware=app_filter.used_by_malware,
                    transfers_files=app_filter.transfers_files,
                    has_known_vulnerabilities=app_filter.has_known_vulnerabilities,
                    tunnels_other_apps=app_filter.tunnels_other_apps,
                    prone_to_misuse=app_filter.prone_to_misuse,
                    no_certifications=app_filter.no_certifications,
                )

                results.append(result)
                created_count += 1

            except Exception as e:
                typer.echo(
                    f"Error processing application filter '{filter_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                continue

        # Display summary with counts
        typer.echo(f"Successfully processed {len(results)} application filter(s)")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")

    except Exception as e:
        typer.echo(f"Error loading application filters: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("application-filter")
def set_application_filter(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    category: list[str] = FILTER_CATEGORY_OPTION,
    subcategory: list[str] = FILTER_SUBCATEGORY_OPTION,
    technology: list[str] = FILTER_TECHNOLOGY_OPTION,
    risk: list[int] = FILTER_RISK_OPTION,
    evasive: bool = EVASIVE_OPTION,
    pervasive: bool = PERVASIVE_OPTION,
    excessive_bandwidth_use: bool = EXCESSIVE_BANDWIDTH_OPTION,
    used_by_malware: bool = USED_BY_MALWARE_OPTION,
    transfers_files: bool = TRANSFERS_FILES_OPTION,
    has_known_vulnerabilities: bool = HAS_KNOWN_VULNERABILITIES_OPTION,
    tunnels_other_apps: bool = TUNNELS_OTHER_APPS_OPTION,
    prone_to_misuse: bool = PRONE_TO_MISUSE_OPTION,
    no_certifications: bool = NO_CERTIFICATIONS_OPTION,
):
    r"""Create or update an application filter.

    Example:
    -------
        scm set object application-filter \
        --folder Texas \
        --name high-risk-apps \
        --category ["business-systems"] \
        --subcategory ["database"] \
        --technology ["client-server"] \
        --risk [4, 5] \
        --has-known-vulnerabilities \
        --used-by-malware

    """
    try:
        # Validate inputs using the Pydantic model
        app_filter = ApplicationFilter(
            folder=folder,
            name=name,
            category=category,
            subcategory=subcategory,
            technology=technology,
            risk=risk,
            evasive=evasive,
            pervasive=pervasive,
            excessive_bandwidth_use=excessive_bandwidth_use,
            used_by_malware=used_by_malware,
            transfers_files=transfers_files,
            has_known_vulnerabilities=has_known_vulnerabilities,
            tunnels_other_apps=tunnels_other_apps,
            prone_to_misuse=prone_to_misuse,
            no_certifications=no_certifications,
        )

        # Call the SDK client to create the application filter
        result = scm_client.create_application_filter(
            folder=app_filter.folder,
            name=app_filter.name,
            category=app_filter.category,
            subcategory=app_filter.subcategory,
            technology=app_filter.technology,
            risk=app_filter.risk,
            evasive=app_filter.evasive,
            pervasive=app_filter.pervasive,
            excessive_bandwidth_use=app_filter.excessive_bandwidth_use,
            used_by_malware=app_filter.used_by_malware,
            transfers_files=app_filter.transfers_files,
            has_known_vulnerabilities=app_filter.has_known_vulnerabilities,
            tunnels_other_apps=app_filter.tunnels_other_apps,
            prone_to_misuse=app_filter.prone_to_misuse,
            no_certifications=app_filter.no_certifications,
        )

        typer.echo(f"Created application filter: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating application filter: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("application-filter")
def show_application_filter(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the application filter to show"),
):
    """Display application filter objects.

    Examples
    --------
        # List all application filters in a folder (default behavior)
        scm show object application-filter --folder Texas

        # Show a specific application filter by name
        scm show object application-filter --folder Texas --name high-risk-apps

    """
    try:
        if name:
            # Get a specific application filter by name
            filter_obj = scm_client.get_application_filter(folder=folder, name=name)

            typer.echo(f"Application Filter: {filter_obj.get('name', 'N/A')}")

            # Display container location (folder, snippet, or device)
            if filter_obj.get("folder"):
                typer.echo(f"Location: Folder '{filter_obj['folder']}'")
            elif filter_obj.get("snippet"):
                typer.echo(f"Location: Snippet '{filter_obj['snippet']}'")
            elif filter_obj.get("device"):
                typer.echo(f"Location: Device '{filter_obj['device']}'")
            else:
                typer.echo("Location: N/A")

            # Display filter criteria
            typer.echo("\nFilter Criteria:")
            if filter_obj.get("category"):
                typer.echo(f"  Categories: {', '.join(filter_obj['category'])}")
            if filter_obj.get("sub_category"):
                typer.echo(f"  Subcategories: {', '.join(filter_obj['sub_category'])}")
            if filter_obj.get("technology"):
                typer.echo(f"  Technologies: {', '.join(filter_obj['technology'])}")
            if filter_obj.get("risk"):
                typer.echo(f"  Risk Levels: {', '.join(map(str, filter_obj['risk']))}")

            # Display boolean attributes
            typer.echo("\nFilter Attributes:")
            typer.echo(f"  Evasive: {filter_obj.get('evasive', False)}")
            typer.echo(f"  Pervasive: {filter_obj.get('pervasive', False)}")
            typer.echo(f"  Excessive Bandwidth Use: {filter_obj.get('excessive_bandwidth_use', False)}")
            typer.echo(f"  Used by Malware: {filter_obj.get('used_by_malware', False)}")
            typer.echo(f"  Transfers Files: {filter_obj.get('transfers_files', False)}")
            typer.echo(f"  Has Known Vulnerabilities: {filter_obj.get('has_known_vulnerabilities', False)}")
            typer.echo(f"  Tunnels Other Apps: {filter_obj.get('tunnels_other_apps', False)}")
            typer.echo(f"  Prone to Misuse: {filter_obj.get('prone_to_misuse', False)}")
            typer.echo(f"  No Certifications: {filter_obj.get('no_certifications', False)}")

            # Display ID if present
            if filter_obj.get("id"):
                typer.echo(f"\nID: {filter_obj['id']}")

            return filter_obj

        else:
            # List all application filters in the folder (default behavior)
            filters = scm_client.list_application_filters(folder=folder)

            if not filters:
                typer.echo(f"No application filters found in folder '{folder}'")
                return

            typer.echo(f"Application Filters in folder '{folder}':")
            typer.echo("-" * 60)

            for filter_obj in filters:
                # Display application filter information
                typer.echo(f"Name: {filter_obj.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if filter_obj.get("folder"):
                    typer.echo(f"  Location: Folder '{filter_obj['folder']}'")
                elif filter_obj.get("snippet"):
                    typer.echo(f"  Location: Snippet '{filter_obj['snippet']}'")
                elif filter_obj.get("device"):
                    typer.echo(f"  Location: Device '{filter_obj['device']}'")
                else:
                    typer.echo("  Location: N/A")

                # Display filter criteria
                if filter_obj.get("category"):
                    typer.echo(f"  Categories: {', '.join(filter_obj['category'])}")
                if filter_obj.get("sub_category"):
                    typer.echo(f"  Subcategories: {', '.join(filter_obj['sub_category'])}")
                if filter_obj.get("technology"):
                    typer.echo(f"  Technologies: {', '.join(filter_obj['technology'])}")
                if filter_obj.get("risk"):
                    typer.echo(f"  Risk Levels: {', '.join(map(str, filter_obj['risk']))}")

                # Display boolean criteria if any are true
                attrs = []
                if filter_obj.get("evasive"):
                    attrs.append("Evasive")
                if filter_obj.get("pervasive"):
                    attrs.append("Pervasive")
                if filter_obj.get("excessive_bandwidth_use"):
                    attrs.append("Excessive Bandwidth")
                if filter_obj.get("used_by_malware"):
                    attrs.append("Used by Malware")
                if filter_obj.get("transfers_files"):
                    attrs.append("Transfers Files")
                if filter_obj.get("has_known_vulnerabilities"):
                    attrs.append("Has Vulnerabilities")
                if filter_obj.get("tunnels_other_apps"):
                    attrs.append("Tunnels Apps")
                if filter_obj.get("prone_to_misuse"):
                    attrs.append("Prone to Misuse")
                if filter_obj.get("no_certifications"):
                    attrs.append("No Certifications")

                if attrs:
                    typer.echo(f"  Filter Attributes: {', '.join(attrs)}")

                typer.echo("-" * 60)

            return filters

    except Exception as e:
        typer.echo(f"Error showing application filter: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# DYNAMIC USER GROUP COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("dynamic-user-group")
def backup_dynamic_user_group(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup all dynamic user groups from a specified location to a YAML file.

    Examples
    --------
        # Backup from a folder
        scm backup object dynamic-user-group --folder Austin

        # Backup with custom output file
        scm backup object dynamic-user-group --folder Austin --file dug-backup.yaml

    """
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # List all dynamic user groups in the location with exact_match=True
        kwargs = {location_type: location_value}
        groups = scm_client.list_dynamic_user_groups(**kwargs, exact_match=True)

        if not groups:
            typer.echo(f"No dynamic user groups found in {location_type} '{location_value}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for group in groups:
            # The list method returns dict objects already, but let's ensure we exclude any None values
            group_dict = {k: v for k, v in group.items() if v is not None}
            # Remove system fields that shouldn't be in backup
            group_dict.pop("id", None)

            # Convert 'tag' back to 'tags' for CLI consistency
            if "tag" in group_dict:
                group_dict["tags"] = group_dict.pop("tag")

            backup_data.append(group_dict)

        # Create the YAML structure
        yaml_data = {"dynamic_user_groups": backup_data}

        # Generate filename
        if file is None:
            file = Path(get_default_backup_filename("dynamic-user-group", location_type, location_value))

        # Write to YAML file
        with file.open("w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} dynamic user groups to {file}")
        return str(file)

    except Exception as e:
        typer.echo(f"Error backing up dynamic user groups: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("dynamic-user-group")
def delete_dynamic_user_group(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete a dynamic user group.

    Example:
    -------
    scm delete object dynamic-user-group --folder Texas --name it-admins

    """
    try:
        result = scm_client.delete_dynamic_user_group(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted dynamic user group: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting dynamic user group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("dynamic-user-group", help="Load dynamic user groups from a YAML file.")
def load_dynamic_user_group(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load dynamic user groups from a YAML file.

    Example:
    -------
    scm load object dynamic-user-group --file config/dynamic_user_groups.yml

    """
    try:
        # Validate container override parameters
        validate_location_params(folder, snippet, device)

        # Validate file exists
        if not file.exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)

        # Load YAML data
        with file.open() as f:
            data = yaml.safe_load(f)

        if not data or "dynamic_user_groups" not in data:
            typer.echo("No dynamic user groups found in file", err=True)
            raise typer.Exit(code=1)

        dynamic_user_groups = data["dynamic_user_groups"]
        if not isinstance(dynamic_user_groups, list):
            dynamic_user_groups = [dynamic_user_groups]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            if folder or snippet or device:
                typer.echo(f"Container override: {folder or snippet or device}")
            typer.echo(yaml.dump(dynamic_user_groups))
            return

        # Apply each dynamic user group
        results: list[dict[str, Any]] = []
        created_count = 0
        updated_count = 0

        for group_data in dynamic_user_groups:
            try:
                # Apply container overrides if specified
                if folder:
                    group_data["folder"] = folder
                    group_data.pop("snippet", None)
                    group_data.pop("device", None)
                elif snippet:
                    group_data["snippet"] = snippet
                    group_data.pop("folder", None)
                    group_data.pop("device", None)
                elif device:
                    group_data["device"] = device
                    group_data.pop("folder", None)
                    group_data.pop("snippet", None)

                # Validate using the Pydantic model
                dug = DynamicUserGroup(**group_data)

                # Call the SDK client to create the dynamic user group
                result = scm_client.create_dynamic_user_group(
                    folder=dug.folder,
                    name=dug.name,
                    filter=dug.filter,
                    description=dug.description,
                    tags=dug.tags,
                )

                results.append(result)
                created_count += 1

            except Exception as e:
                typer.echo(
                    f"Error processing dynamic user group '{group_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                continue

        # Display summary with counts
        typer.echo(f"Successfully processed {len(results)} dynamic user group(s)")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")

    except Exception as e:
        typer.echo(f"Error loading dynamic user groups: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("dynamic-user-group")
def set_dynamic_user_group(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    filter: str = FILTER_EXPRESSION_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    tags: list[str] | None = TAGS_OPTION,
):
    r"""Create or update a dynamic user group.

    Example:
    -------
        scm set object dynamic-user-group \\
        --folder Texas \\
        --name it-admins \\
        --filter "tag.Department='IT' and tag.Role='Admin'" \\
        --description "IT administrators" \\
        --tags ["automation", "admin"]

    """
    try:
        # Validate inputs using the Pydantic model
        dug = DynamicUserGroup(
            folder=folder,
            name=name,
            filter=filter,
            description=description or "",
            tags=tags or [],
        )

        # Call the SDK client to create the dynamic user group
        result = scm_client.create_dynamic_user_group(
            folder=dug.folder,
            name=dug.name,
            filter=dug.filter,
            description=dug.description,
            tags=dug.tags,
        )

        typer.echo(f"Created dynamic user group: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating dynamic user group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("dynamic-user-group")
def show_dynamic_user_group(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the dynamic user group to show"),
):
    """Display dynamic user group objects.

    Examples
    --------
        # List all dynamic user groups in a folder (default behavior)
        scm show object dynamic-user-group --folder Texas

        # Show a specific dynamic user group by name
        scm show object dynamic-user-group --folder Texas --name it-admins

    """
    try:
        if name:
            # Get a specific dynamic user group by name
            group = scm_client.get_dynamic_user_group(folder=folder, name=name)

            typer.echo(f"Dynamic User Group: {group.get('name', 'N/A')}")

            # Display container location (folder, snippet, or device)
            if group.get("folder"):
                typer.echo(f"Location: Folder '{group['folder']}'")
            elif group.get("snippet"):
                typer.echo(f"Location: Snippet '{group['snippet']}'")
            elif group.get("device"):
                typer.echo(f"Location: Device '{group['device']}'")
            else:
                typer.echo("Location: N/A")

            typer.echo(f"Filter: {group.get('filter', 'N/A')}")
            typer.echo(f"Description: {group.get('description', 'N/A')}")

            # Display tags if present
            if group.get("tag"):
                typer.echo(f"Tags: {', '.join(group['tag'])}")

            # Display ID if present
            if group.get("id"):
                typer.echo(f"ID: {group['id']}")

            return group

        else:
            # List all dynamic user groups in the folder (default behavior)
            groups = scm_client.list_dynamic_user_groups(folder=folder)

            if not groups:
                typer.echo(f"No dynamic user groups found in folder '{folder}'")
                return

            typer.echo(f"Dynamic User Groups in folder '{folder}':")
            typer.echo("-" * 60)

            for group in groups:
                # Display dynamic user group information
                typer.echo(f"Name: {group.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if group.get("folder"):
                    typer.echo(f"  Location: Folder '{group['folder']}'")
                elif group.get("snippet"):
                    typer.echo(f"  Location: Snippet '{group['snippet']}'")
                elif group.get("device"):
                    typer.echo(f"  Location: Device '{group['device']}'")
                else:
                    typer.echo("  Location: N/A")

                typer.echo(f"  Filter: {group.get('filter', 'N/A')}")
                typer.echo(f"  Description: {group.get('description', 'N/A')}")

                # Display tags if present
                if group.get("tag"):
                    typer.echo(f"  Tags: {', '.join(group['tag'])}")

                typer.echo("-" * 60)

            return groups

    except Exception as e:
        typer.echo(f"Error showing dynamic user group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# EXTERNAL DYNAMIC LIST COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("external-dynamic-list")
def backup_external_dynamic_list(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup all external dynamic lists from a specified location to a YAML file.

    Examples
    --------
        # Backup from a folder
        scm backup object external-dynamic-list --folder Austin

        # Backup with custom output file
        scm backup object external-dynamic-list --folder Austin --file edl-backup.yaml

    """
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # List all external dynamic lists in the location with exact_match=True
        kwargs = {location_type: location_value}
        edls = scm_client.list_external_dynamic_lists(**kwargs, exact_match=True)

        if not edls:
            typer.echo(f"No external dynamic lists found in {location_type} '{location_value}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for edl in edls:
            # The list method returns dict objects already, but let's ensure we exclude any None values
            edl_dict = {k: v for k, v in edl.items() if v is not None}
            # Remove system fields that shouldn't be in backup
            edl_dict.pop("id", None)

            # Convert nested type structure to flat structure for easier YAML editing
            if "type" in edl_dict and isinstance(edl_dict["type"], dict):
                type_data = edl_dict["type"]
                # Extract the type key (predefined_ip, ip, domain, etc.)
                type_key = list(type_data.keys())[0]
                edl_dict["type"] = type_key

                # Flatten the type-specific configuration
                type_config = type_data[type_key]
                for key, value in type_config.items():
                    if key == "recurring" and isinstance(value, dict):
                        # Handle recurring configuration
                        recur_type = list(value.keys())[0]
                        edl_dict["recurring"] = recur_type
                        if recur_type in ["daily", "weekly", "monthly"]:
                            recur_config = value[recur_type]
                            if "at" in recur_config:
                                edl_dict["hour"] = recur_config["at"]
                            if "day_of_week" in recur_config:
                                edl_dict["day"] = recur_config["day_of_week"]
                            elif "day_of_month" in recur_config:
                                edl_dict["day"] = str(recur_config["day_of_month"])
                    elif key == "auth" and isinstance(value, dict):
                        # Handle authentication
                        edl_dict["username"] = value.get("username")
                        edl_dict["password"] = value.get("password")
                    else:
                        edl_dict[key] = value

            backup_data.append(edl_dict)

        # Create the YAML structure
        yaml_data = {"external_dynamic_lists": backup_data}

        # Generate filename
        if file is None:
            file = Path(get_default_backup_filename("external-dynamic-list", location_type, location_value))

        # Write to YAML file
        with file.open("w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} external dynamic lists to {file}")
        return str(file)

    except Exception as e:
        typer.echo(f"Error backing up external dynamic lists: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("external-dynamic-list")
def delete_external_dynamic_list(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete an external dynamic list.

    Example:
    -------
    scm delete object external-dynamic-list --folder Texas --name malicious-ips

    """
    try:
        result = scm_client.delete_external_dynamic_list(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted external dynamic list: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting external dynamic list: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("external-dynamic-list", help="Load external dynamic lists from a YAML file.")
def load_external_dynamic_list(
    file: Path = FILE_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load external dynamic lists from a YAML file.

    Example:
    -------
    scm load object external-dynamic-list --file config/external_dynamic_lists.yml

    """
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # Validate the file exists
        if not file.exists():
            typer.echo(f"Error: File '{file}' does not exist", err=True)
            raise typer.Exit(code=1)

        # Load YAML content
        with file.open() as f:
            yaml_content = yaml.safe_load(f)

        if not yaml_content:
            typer.echo(f"Error: File '{file}' is empty or invalid", err=True)
            raise typer.Exit(code=1)

        # Extract external dynamic lists from YAML
        external_dynamic_lists = yaml_content.get("external_dynamic_lists", [])
        if not external_dynamic_lists:
            typer.echo("No external dynamic lists found in the YAML file.")
            return

        if dry_run:
            typer.echo("[DRY RUN] Would load the following external dynamic lists:")

        results: list[dict[str, Any]] = []
        loaded_count = 0

        for idx, edl_config in enumerate(external_dynamic_lists, 1):
            try:
                # Override container if specified in command line
                if location_value:
                    edl_config[location_type] = location_value
                    # Remove other container fields
                    for container in ["folder", "snippet", "device"]:
                        if container != location_type and container in edl_config:
                            del edl_config[container]

                # Validate the configuration
                edl = ExternalDynamicList(**edl_config)

                if dry_run:
                    typer.echo(f"\n[{idx}] External Dynamic List: {edl.name}")
                    typer.echo(f"  Container: {getattr(edl, location_type or 'folder')}")
                    typer.echo(f"  Type: {edl.type}")
                    typer.echo(f"  URL: {edl.url}")
                    if edl.description:
                        typer.echo(f"  Description: {edl.description}")
                    if edl.recurring:
                        typer.echo(f"  Update Frequency: {edl.recurring}")
                    results.append({"action": "would create/update", "name": edl.name})
                else:
                    # Convert to SDK model format
                    sdk_data = edl.to_sdk_model()

                    # Extract container params
                    container_params = {}
                    if "folder" in edl_config:
                        container_params["folder"] = edl_config["folder"]
                    elif "snippet" in edl_config:
                        container_params["snippet"] = edl_config["snippet"]
                    elif "device" in edl_config:
                        container_params["device"] = edl_config["device"]
                    # Create the EDL using the SDK data
                    result = scm_client.create_external_dynamic_list(
                        **container_params,
                        **sdk_data,
                    )
                    typer.echo(f"✓ Loaded external dynamic list: {edl.name}")
                    loaded_count += 1
                    results.append(
                        {
                            "action": "created/updated",
                            "name": edl.name,
                            "result": result,
                        }
                    )
            except Exception as e:
                typer.echo(
                    f"✗ Error with external dynamic list '{edl_config.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                results.append(
                    {
                        "action": "error",
                        "name": edl_config.get("name", "unknown"),
                        "error": str(e),
                    }
                )
                continue

        # Summary
        if dry_run:
            typer.echo(f"\n[DRY RUN] Would load {len(external_dynamic_lists)} external dynamic lists from '{file}'")
        else:
            typer.echo(f"\nSuccessfully loaded {loaded_count} out of {len(external_dynamic_lists)} external dynamic lists from '{file}'")

    except Exception as e:
        typer.echo(f"Error loading external dynamic lists: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("external-dynamic-list")
def set_external_dynamic_list(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    type: str = typer.Option(
        ...,
        help="Type of EDL (predefined_ip, predefined_url, ip, domain, url, imsi, imei)",
    ),
    url: str = typer.Option(..., help="URL for the external list"),
    description: str = typer.Option("", help="Description of the external dynamic list"),
    exception_list: list[str] = EXCEPTION_LIST_OPTION,
    recurring: str = RECURRING_OPTION,
    hour: str = HOUR_OPTION,
    day: str = DAY_OPTION,
    username: str = USERNAME_OPTION,
    password: str = PASSWORD_OPTION,
    certificate_profile: str = CERTIFICATE_PROFILE_OPTION,
    expand_domain: bool = EXPAND_DOMAIN_OPTION,
):
    r"""Create or update an external dynamic list.

    Example:
    -------
        # Create a predefined IP list
        scm set object external-dynamic-list --folder Texas --name paloalto-bulletproof \\
            --type predefined_ip --url "https://saasedl.paloaltonetworks.com/feeds/BulletproofIPList"

        # Create a custom IP blocklist with hourly updates
        scm set object external-dynamic-list --folder Texas --name custom-blocklist \\
            --type ip --url "https://example.com/blocklist.txt" --recurring hourly

        # Create a domain list with daily updates at 3 AM
        scm set object external-dynamic-list --folder Texas --name malicious-domains \\
            --type domain --url "https://example.com/domains.txt" --recurring daily --hour 03 \\
            --expand-domain

    """
    try:
        # Validate the configuration

        edl_config: dict[str, Any] = {
            "folder": folder,
            "name": name,
            "type": type,
            "url": url,
            "description": description or "",
            "exception_list": exception_list or [],
            "recurring": recurring,
            "hour": hour,
            "day": day,
            "username": username,
            "password": password,
            "certificate_profile": certificate_profile,
            "expand_domain": expand_domain,
        }

        # Remove None values except for fields with defaults
        edl_config = {k: v for k, v in edl_config.items() if v is not None or k in ["description", "exception_list"]}

        # Validate using Pydantic model
        edl = ExternalDynamicList(**edl_config)

        # Convert to SDK model format
        edl_data = edl.to_sdk_model()

        # Create/update the external dynamic list
        result = scm_client.create_external_dynamic_list(
            folder=folder,
            name=name,
            type_config=edl_data["type"],
        )

        typer.echo(f"Created external dynamic list: {name} in folder {folder}")
        return result

    except Exception as e:
        typer.echo(f"Error creating/updating external dynamic list: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("external-dynamic-list")
def show_external_dynamic_list(
    folder: str = FOLDER_OPTION,
    name: str = typer.Option(None, help="Name of the external dynamic list to show"),
):
    """Show external dynamic list details or list all external dynamic lists in a folder.

    Examples
    --------
        # List all external dynamic lists in a folder (default behavior)
        scm show object external-dynamic-list --folder Texas

        # Show a specific external dynamic list by name
        scm show object external-dynamic-list --folder Texas --name malicious-ips

    """
    try:
        if name:
            # Get a specific external dynamic list by name
            edl = scm_client.get_external_dynamic_list(folder=folder, name=name)

            typer.echo(f"External Dynamic List: {edl.get('name', 'N/A')}")

            # Display container location (folder, snippet, or device)
            if edl.get("folder"):
                typer.echo(f"Location: Folder '{edl['folder']}'")
            elif edl.get("snippet"):
                typer.echo(f"Location: Snippet '{edl['snippet']}'")
            elif edl.get("device"):
                typer.echo(f"Location: Device '{edl['device']}'")
            else:
                typer.echo("Location: N/A")

            # Display type information
            if edl.get("type") and isinstance(edl["type"], dict):
                type_key = list(edl["type"].keys())[0]
                type_config = edl["type"][type_key]
                typer.echo(f"Type: {type_key}")
                typer.echo(f"URL: {type_config.get('url', 'N/A')}")
                if type_config.get("description"):
                    typer.echo(f"Description: {type_config['description']}")
                if type_config.get("recurring"):
                    recur_type = list(type_config["recurring"].keys())[0]
                    typer.echo(f"Update Frequency: {recur_type}")
                    recur_config = type_config["recurring"][recur_type]
                    if recur_config and isinstance(recur_config, dict):
                        if "at" in recur_config:
                            typer.echo(f"  Update Hour: {recur_config['at']}")
                        if "day_of_week" in recur_config:
                            typer.echo(f"  Update Day: {recur_config['day_of_week']}")
                        elif "day_of_month" in recur_config:
                            typer.echo(f"  Update Day: {recur_config['day_of_month']}")
                if type_config.get("exception_list"):
                    typer.echo(f"Exception List: {', '.join(type_config['exception_list'])}")
                if type_config.get("auth"):
                    typer.echo(f"Authentication: Username '{type_config['auth']['username']}'")
                if type_config.get("certificate_profile"):
                    typer.echo(f"Certificate Profile: {type_config['certificate_profile']}")
                if type_config.get("expand_domain"):
                    typer.echo(f"Expand Domain: {type_config['expand_domain']}")

            # Display ID if present
            if edl.get("id"):
                typer.echo(f"ID: {edl['id']}")

            return edl

        else:
            # List all external dynamic lists in the folder (default behavior)
            edls = scm_client.list_external_dynamic_lists(folder=folder)

            if not edls:
                typer.echo(f"No external dynamic lists found in folder '{folder}'")
                return

            typer.echo(f"External Dynamic Lists in folder '{folder}':")
            typer.echo("-" * 60)

            for edl in edls:
                # Display external dynamic list information
                typer.echo(f"Name: {edl.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if edl.get("folder"):
                    typer.echo(f"  Location: Folder '{edl['folder']}'")
                elif edl.get("snippet"):
                    typer.echo(f"  Location: Snippet '{edl['snippet']}'")
                elif edl.get("device"):
                    typer.echo(f"  Location: Device '{edl['device']}'")
                else:
                    typer.echo("  Location: N/A")

                # Display type information
                if edl.get("type") and isinstance(edl["type"], dict):
                    type_key = list(edl["type"].keys())[0]
                    type_config = edl["type"][type_key]
                    typer.echo(f"  Type: {type_key}")
                    typer.echo(f"  URL: {type_config.get('url', 'N/A')}")
                    if type_config.get("description"):
                        typer.echo(f"  Description: {type_config['description']}")
                    if type_config.get("recurring"):
                        recur_type = list(type_config["recurring"].keys())[0]
                        typer.echo(f"  Update Frequency: {recur_type}")
                    if type_config.get("exception_list"):
                        typer.echo(f"  Exception List: {', '.join(type_config['exception_list'])}")

                typer.echo("-" * 60)

            return edls

    except Exception as e:
        typer.echo(f"Error showing external dynamic list: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# HIP OBJECT COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("hip-object")
def backup_hip_object(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup all HIP objects from a specified location to a YAML file.

    Examples
    --------
        # Backup from a folder
        scm backup object hip-object --folder Austin

        # Backup with custom output file
        scm backup object hip-object --folder Austin --file hip-objects.yaml

    """
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # List all HIP objects in the location with exact_match=True
        kwargs = {location_type: location_value}
        hip_objects = scm_client.list_hip_objects(**kwargs, exact_match=True)

        if not hip_objects:
            typer.echo(f"No HIP objects found in {location_type} '{location_value}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for hip_obj in hip_objects:
            # The list method returns dict objects already, but let's ensure we exclude any None values
            hip_dict = {k: v for k, v in hip_obj.items() if v is not None}
            # Remove system fields that shouldn't be in backup
            hip_dict.pop("id", None)

            # Flatten the structure for easier YAML editing
            flat_dict = {"folder": hip_dict.get("folder"), "name": hip_dict.get("name")}

            if hip_dict.get("description"):
                flat_dict["description"] = hip_dict["description"]

            # Flatten host info
            if hip_dict.get("host_info") and hip_dict["host_info"].get("criteria"):
                criteria = hip_dict["host_info"]["criteria"]

                # Handle string comparisons
                if criteria.get("domain"):
                    domain_val = criteria["domain"]
                    if "is" in domain_val:
                        flat_dict["host_info_domain"] = "is"
                        flat_dict["host_info_domain_value"] = domain_val["is"]
                    elif "is_not" in domain_val:
                        flat_dict["host_info_domain"] = "is_not"
                        flat_dict["host_info_domain_value"] = domain_val["is_not"]
                    elif "contains" in domain_val:
                        flat_dict["host_info_domain"] = "contains"
                        flat_dict["host_info_domain_value"] = domain_val["contains"]

                # Handle OS
                if criteria.get("os") and criteria["os"].get("contains"):
                    os_data = criteria["os"]["contains"]
                    for vendor, value in os_data.items():
                        flat_dict["host_info_os"] = vendor
                        flat_dict["host_info_os_value"] = value

                # Handle other string comparisons
                for field in [
                    "client_version",
                    "host_name",
                    "host_id",
                    "serial_number",
                ]:
                    if criteria.get(field):
                        field_val = criteria[field]
                        if "is" in field_val:
                            flat_dict[f"host_info_{field}"] = "is"
                            flat_dict[f"host_info_{field}_value"] = field_val["is"]
                        elif "is_not" in field_val:
                            flat_dict[f"host_info_{field}"] = "is_not"
                            flat_dict[f"host_info_{field}_value"] = field_val["is_not"]
                        elif "contains" in field_val:
                            flat_dict[f"host_info_{field}"] = "contains"
                            flat_dict[f"host_info_{field}_value"] = field_val["contains"]

                # Handle managed state
                if "managed" in criteria:
                    flat_dict["host_info_managed"] = criteria["managed"]

            # Flatten network info
            if hip_dict.get("network_info") and hip_dict["network_info"].get("criteria"):
                criteria = hip_dict["network_info"]["criteria"]
                if criteria.get("network"):
                    network_val = criteria["network"]
                    if "is" in network_val:
                        flat_dict["network_info_type"] = "is"
                        flat_dict["network_info_value"] = list(network_val["is"].keys())[0]
                    elif "is_not" in network_val:
                        flat_dict["network_info_type"] = "is_not"
                        flat_dict["network_info_value"] = list(network_val["is_not"].keys())[0]

            # Handle patch management
            if hip_dict.get("patch_management"):
                pm_data = hip_dict["patch_management"]
                if pm_data.get("criteria"):
                    criteria = pm_data["criteria"]
                    if "is_installed" in criteria:
                        flat_dict["patch_management_enabled"] = criteria["is_installed"]
                    if criteria.get("missing_patches"):
                        mp = criteria["missing_patches"]
                        if "check" in mp:
                            flat_dict["patch_management_missing_patches"] = mp["check"]
                        if "severity" in mp:
                            flat_dict["patch_management_severity"] = mp["severity"]
                        if "patches" in mp:
                            flat_dict["patch_management_patches"] = mp["patches"]
                if pm_data.get("vendor"):
                    flat_dict["patch_management_vendors"] = pm_data["vendor"]

            # Handle disk encryption
            if hip_dict.get("disk_encryption"):
                de_data = hip_dict["disk_encryption"]
                if de_data.get("criteria"):
                    criteria = de_data["criteria"]
                    if "is_installed" in criteria:
                        flat_dict["disk_encryption_enabled"] = criteria["is_installed"]
                    if "encrypted_locations" in criteria:
                        flat_dict["disk_encryption_locations"] = criteria["encrypted_locations"]
                if de_data.get("vendor"):
                    flat_dict["disk_encryption_vendors"] = de_data["vendor"]

            # Handle mobile device
            if hip_dict.get("mobile_device") and hip_dict["mobile_device"].get("criteria"):
                criteria = hip_dict["mobile_device"]["criteria"]
                if "jailbroken" in criteria:
                    flat_dict["mobile_device_jailbroken"] = criteria["jailbroken"]
                if "disk_encrypted" in criteria:
                    flat_dict["mobile_device_disk_encrypted"] = criteria["disk_encrypted"]
                if "passcode_set" in criteria:
                    flat_dict["mobile_device_passcode_set"] = criteria["passcode_set"]
                if criteria.get("last_checkin_time"):
                    lct = criteria["last_checkin_time"]
                    if "days" in lct:
                        flat_dict["mobile_device_last_checkin_time"] = "days"
                        flat_dict["mobile_device_last_checkin_value"] = lct["days"]
                    elif "hours" in lct:
                        flat_dict["mobile_device_last_checkin_time"] = "hours"
                        flat_dict["mobile_device_last_checkin_value"] = lct["hours"]
                if criteria.get("applications"):
                    apps = criteria["applications"]
                    if "has_malware" in apps:
                        flat_dict["mobile_device_has_malware"] = apps["has_malware"]
                    if "has_unmanaged_app" in apps:
                        flat_dict["mobile_device_has_unmanaged_app"] = apps["has_unmanaged_app"]
                    if "includes" in apps:
                        flat_dict["mobile_device_applications"] = apps["includes"]

            # Handle certificate
            if hip_dict.get("certificate") and hip_dict["certificate"].get("criteria"):
                criteria = hip_dict["certificate"]["criteria"]
                if "certificate_profile" in criteria:
                    flat_dict["certificate_profile"] = criteria["certificate_profile"]
                if "certificate_attributes" in criteria:
                    flat_dict["certificate_attributes"] = criteria["certificate_attributes"]

            backup_data.append(flat_dict)

        # Create the YAML structure
        yaml_data = {"hip_objects": backup_data}

        # Generate filename
        if file is None:
            file = Path(get_default_backup_filename("hip-object", location_type, location_value))

        # Write to YAML file
        with file.open("w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} HIP objects to {file}")
        return str(file)

    except Exception as e:
        typer.echo(f"Error backing up HIP objects: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("hip-object")
def delete_hip_object(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete a HIP object.

    Example:
    -------
    scm delete object hip-object --folder Texas --name windows-compliance

    """
    try:
        result = scm_client.delete_hip_object(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted HIP object: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting HIP object: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("hip-object", help="Load HIP objects from a YAML file.")
def load_hip_object(
    file: Path = FILE_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load HIP objects from a YAML file.

    Example:
    -------
    scm load object hip-object --file config/hip_objects.yml

    """
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # Validate the file exists
        if not file.exists():
            typer.echo(f"Error: File '{file}' does not exist", err=True)
            raise typer.Exit(code=1)

        # Load YAML content
        with file.open() as f:
            yaml_content = yaml.safe_load(f)

        if not yaml_content:
            typer.echo(f"Error: File '{file}' is empty or invalid", err=True)
            raise typer.Exit(code=1)

        # Extract HIP objects from YAML
        hip_objects = yaml_content.get("hip_objects", [])
        if not hip_objects:
            typer.echo("No HIP objects found in the YAML file.")
            return

        if dry_run:
            typer.echo("[DRY RUN] Would load the following HIP objects:")

        results: list[dict[str, Any]] = []
        loaded_count = 0

        for idx, hip_data in enumerate(hip_objects, 1):
            try:
                # Override container if specified in command line
                if location_value:
                    hip_data[location_type] = location_value
                    # Remove other container fields
                    for container in ["folder", "snippet", "device"]:
                        if container != location_type and container in hip_data:
                            del hip_data[container]

                # Validate using the Pydantic model
                hip_obj = HIPObject(**hip_data)

                if dry_run:
                    typer.echo(f"\n[{idx}] HIP Object: {hip_obj.name}")
                    typer.echo(f"  Container: {getattr(hip_obj, location_type or 'folder')}")
                    if hip_obj.description:
                        typer.echo(f"  Description: {hip_obj.description}")
                    results.append({"action": "would create/update", "name": hip_obj.name})
                else:
                    # Convert to SDK model format
                    sdk_data = hip_obj.to_sdk_model()

                    # Call the SDK client to create the HIP object
                    container_params = {location_type or "folder": getattr(hip_obj, location_type or "folder")}
                    result = scm_client.create_hip_object(
                        **container_params,
                        **sdk_data,
                    )

                    typer.echo(f"✓ Loaded HIP object: {hip_obj.name}")
                    loaded_count += 1
                    results.append(
                        {
                            "action": "created/updated",
                            "name": hip_obj.name,
                            "result": result,
                        }
                    )
            except Exception as e:
                typer.echo(
                    f"✗ Error with HIP object '{hip_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                results.append(
                    {
                        "action": "error",
                        "name": hip_data.get("name", "unknown"),
                        "error": str(e),
                    }
                )
                continue

        # Summary
        if dry_run:
            typer.echo(f"\n[DRY RUN] Would load {len(hip_objects)} HIP objects from '{file}'")
        else:
            typer.echo(f"\nSuccessfully loaded {loaded_count} out of {len(hip_objects)} HIP objects from '{file}'")

    except Exception as e:
        typer.echo(f"Error loading HIP objects: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("hip-object")
def set_hip_object(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    description: str = typer.Option("", help="Description of the HIP object"),
    # Host info options
    host_info_domain: str = typer.Option(None, help="Domain criteria (is, is_not, contains)"),
    host_info_domain_value: str = typer.Option(None, help="Domain value to match"),
    host_info_os: str = typer.Option(None, help="OS vendor (Microsoft, Apple, Google, Linux, Other)"),
    host_info_os_value: str = typer.Option(None, help="OS value (All or specific version)"),
    host_info_managed: bool = typer.Option(None, help="Managed state criteria"),
    # Network info options
    network_info_type: str = typer.Option(None, help="Network type (is, is_not)"),
    network_info_value: str = typer.Option(None, help="Network value (wifi, mobile, ethernet, unknown)"),
    # Patch management options
    patch_management_enabled: bool = typer.Option(None, help="Whether patch management is enabled"),
    patch_management_missing_patches: str = typer.Option(None, help="Missing patches check (has-any, has-none, has-all)"),
    patch_management_severity: int = typer.Option(None, help="Patch severity level"),
    # Disk encryption options
    disk_encryption_enabled: bool = typer.Option(None, help="Whether disk encryption is enabled"),
    # Mobile device options
    mobile_device_jailbroken: bool = typer.Option(None, help="Jailbroken status"),
    mobile_device_disk_encrypted: bool = typer.Option(None, help="Disk encryption status"),
    mobile_device_passcode_set: bool = typer.Option(None, help="Passcode status"),
    # Certificate options
    certificate_profile: str = typer.Option(None, help="Certificate profile name"),
):
    r"""Create or update a HIP object.

    Example:
    -------
        # Create a Windows workstation compliance policy
        scm set object hip-object \\
        --folder Texas \\
        --name windows-compliance \\
        --description "Windows workstation compliance" \\
        --host-info-os Microsoft \\
        --host-info-os-value All \\
        --host-info-managed \\
        --disk-encryption-enabled \\
        --patch-management-enabled

        # Create a mobile device policy
        scm set object hip-object \\
        --folder Texas \\
        --name mobile-policy \\
        --description "Mobile device compliance" \\
        --mobile-device-jailbroken false \\
        --mobile-device-disk-encrypted \\
        --mobile-device-passcode-set

        # Create a network-based policy
        scm set object hip-object \\
        --folder Texas \\
        --name wifi-only \\
        --description "WiFi network only" \\
        --network-info-type is \\
        --network-info-value wifi

    """
    try:
        # Build the HIP object data from options
        hip_data: dict[str, Any] = {
            "folder": folder,
            "name": name,
            "description": description,
        }

        # Add host info options if provided
        if host_info_domain:
            hip_data["host_info_domain"] = host_info_domain
            hip_data["host_info_domain_value"] = host_info_domain_value
        if host_info_os:
            hip_data["host_info_os"] = host_info_os
            hip_data["host_info_os_value"] = host_info_os_value
        if host_info_managed is not None:
            hip_data["host_info_managed"] = host_info_managed

        # Add network info options if provided
        if network_info_type:
            hip_data["network_info_type"] = network_info_type
            hip_data["network_info_value"] = network_info_value

        # Add patch management options if provided
        if patch_management_enabled is not None:
            hip_data["patch_management_enabled"] = patch_management_enabled
        if patch_management_missing_patches:
            hip_data["patch_management_missing_patches"] = patch_management_missing_patches
        if patch_management_severity is not None:
            hip_data["patch_management_severity"] = patch_management_severity

        # Add disk encryption options if provided
        if disk_encryption_enabled is not None:
            hip_data["disk_encryption_enabled"] = disk_encryption_enabled

        # Add mobile device options if provided
        if mobile_device_jailbroken is not None:
            hip_data["mobile_device_jailbroken"] = mobile_device_jailbroken
        if mobile_device_disk_encrypted is not None:
            hip_data["mobile_device_disk_encrypted"] = mobile_device_disk_encrypted
        if mobile_device_passcode_set is not None:
            hip_data["mobile_device_passcode_set"] = mobile_device_passcode_set

        # Add certificate options if provided
        if certificate_profile:
            hip_data["certificate_profile"] = certificate_profile

        # Validate using the Pydantic model
        # Ensure proper typing for fields
        typed_hip_data = hip_data.copy()
        hip_obj = HIPObject(**typed_hip_data)

        # Convert to SDK model format
        sdk_data = hip_obj.to_sdk_model()

        # Call the SDK client to create the HIP object
        result = scm_client.create_hip_object(
            folder=hip_obj.folder,
            name=hip_obj.name,
            description=sdk_data.get("description"),
            host_info=sdk_data.get("host_info"),
            network_info=sdk_data.get("network_info"),
            patch_management=sdk_data.get("patch_management"),
            disk_encryption=sdk_data.get("disk_encryption"),
            mobile_device=sdk_data.get("mobile_device"),
            certificate=sdk_data.get("certificate"),
        )

        typer.echo(f"Created HIP object: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating HIP object: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("hip-object")
def show_hip_object(
    folder: str = FOLDER_OPTION,
    name: str = typer.Option(None, help="Name of the HIP object to show"),
):
    """Display HIP object configurations.

    Examples
    --------
        # List all HIP objects in a folder (default behavior)
        scm show object hip-object --folder Texas

        # Show a specific HIP object by name
        scm show object hip-object --folder Texas --name windows-compliance

    """
    try:
        if name:
            # Get a specific HIP object by name
            hip_obj = scm_client.get_hip_object(folder=folder, name=name)

            typer.echo(f"HIP Object: {hip_obj.get('name', 'N/A')}")

            # Display container location (folder, snippet, or device)
            if hip_obj.get("folder"):
                typer.echo(f"Location: Folder '{hip_obj['folder']}'")
            elif hip_obj.get("snippet"):
                typer.echo(f"Location: Snippet '{hip_obj['snippet']}'")
            elif hip_obj.get("device"):
                typer.echo(f"Location: Device '{hip_obj['device']}'")
            else:
                typer.echo("Location: N/A")

            typer.echo(f"Description: {hip_obj.get('description', 'N/A')}")

            # Display host info criteria
            if hip_obj.get("host_info") and hip_obj["host_info"].get("criteria"):
                typer.echo("\nHost Information Criteria:")
                criteria = hip_obj["host_info"]["criteria"]

                if criteria.get("domain"):
                    domain_val = criteria["domain"]
                    for key, value in domain_val.items():
                        typer.echo(f"  Domain {key}: {value}")

                if criteria.get("os") and criteria["os"].get("contains"):
                    os_data = criteria["os"]["contains"]
                    for vendor, value in os_data.items():
                        typer.echo(f"  OS: {vendor} - {value}")

                if "managed" in criteria:
                    typer.echo(f"  Managed: {criteria['managed']}")

                for field in [
                    "client_version",
                    "host_name",
                    "host_id",
                    "serial_number",
                ]:
                    if criteria.get(field):
                        field_val = criteria[field]
                        for key, value in field_val.items():
                            typer.echo(f"  {field.replace('_', ' ').title()} {key}: {value}")

            # Display network info criteria
            if hip_obj.get("network_info") and hip_obj["network_info"].get("criteria"):
                typer.echo("\nNetwork Information Criteria:")
                criteria = hip_obj["network_info"]["criteria"]
                if criteria.get("network"):
                    network_val = criteria["network"]
                    for op, value in network_val.items():
                        network_type = list(value.keys())[0]
                        typer.echo(f"  Network {op}: {network_type}")

            # Display patch management criteria
            if hip_obj.get("patch_management"):
                typer.echo("\nPatch Management Criteria:")
                pm_data = hip_obj["patch_management"]
                if pm_data.get("criteria"):
                    criteria = pm_data["criteria"]
                    if "is_installed" in criteria:
                        typer.echo(f"  Is Installed: {criteria['is_installed']}")
                    if criteria.get("missing_patches"):
                        mp = criteria["missing_patches"]
                        typer.echo(f"  Missing Patches Check: {mp.get('check', 'N/A')}")
                        if "severity" in mp:
                            typer.echo(f"  Severity Threshold: {mp['severity']}")
                        if "patches" in mp:
                            typer.echo(f"  Specific Patches: {', '.join(mp['patches'])}")
                if pm_data.get("vendor"):
                    typer.echo("  Vendors:")
                    for vendor in pm_data["vendor"]:
                        typer.echo(f"    - {vendor.get('name', 'N/A')}: {', '.join(vendor.get('product', []))}")

            # Display disk encryption criteria
            if hip_obj.get("disk_encryption"):
                typer.echo("\nDisk Encryption Criteria:")
                de_data = hip_obj["disk_encryption"]
                if de_data.get("criteria"):
                    criteria = de_data["criteria"]
                    if "is_installed" in criteria:
                        typer.echo(f"  Is Installed: {criteria['is_installed']}")
                    if criteria.get("encrypted_locations"):
                        typer.echo("  Encrypted Locations:")
                        for loc in criteria["encrypted_locations"]:
                            state = loc.get("encryption_state", {})
                            state_str = "N/A"
                            if "is" in state:
                                state_str = f"is {state['is']}"
                            elif "is_not" in state:
                                state_str = f"is not {state['is_not']}"
                            typer.echo(f"    - {loc.get('name', 'N/A')}: {state_str}")
                if de_data.get("vendor"):
                    typer.echo("  Vendors:")
                    for vendor in de_data["vendor"]:
                        typer.echo(f"    - {vendor.get('name', 'N/A')}: {', '.join(vendor.get('product', []))}")

            # Display mobile device criteria
            if hip_obj.get("mobile_device") and hip_obj["mobile_device"].get("criteria"):
                typer.echo("\nMobile Device Criteria:")
                criteria = hip_obj["mobile_device"]["criteria"]

                if "jailbroken" in criteria:
                    typer.echo(f"  Jailbroken: {criteria['jailbroken']}")
                if "disk_encrypted" in criteria:
                    typer.echo(f"  Disk Encrypted: {criteria['disk_encrypted']}")
                if "passcode_set" in criteria:
                    typer.echo(f"  Passcode Set: {criteria['passcode_set']}")

                if criteria.get("last_checkin_time"):
                    lct = criteria["last_checkin_time"]
                    for unit, value in lct.items():
                        typer.echo(f"  Last Check-in Time: {value} {unit}")

                if criteria.get("applications"):
                    apps = criteria["applications"]
                    if "has_malware" in apps:
                        typer.echo(f"  Has Malware: {apps['has_malware']}")
                    if "has_unmanaged_app" in apps:
                        typer.echo(f"  Has Unmanaged App: {apps['has_unmanaged_app']}")
                    if apps.get("includes"):
                        typer.echo("  Required Applications:")
                        for app in apps["includes"]:
                            typer.echo(f"    - {app.get('name', 'N/A')}")
                            if app.get("package"):
                                typer.echo(f"      Package: {app['package']}")
                            if app.get("hash"):
                                typer.echo(f"      Hash: {app['hash']}")

            # Display certificate criteria
            if hip_obj.get("certificate") and hip_obj["certificate"].get("criteria"):
                typer.echo("\nCertificate Criteria:")
                criteria = hip_obj["certificate"]["criteria"]

                if criteria.get("certificate_profile"):
                    typer.echo(f"  Certificate Profile: {criteria['certificate_profile']}")

                if criteria.get("certificate_attributes"):
                    typer.echo("  Certificate Attributes:")
                    for attr in criteria["certificate_attributes"]:
                        typer.echo(f"    - {attr.get('name', 'N/A')}: {attr.get('value', 'N/A')}")

            # Display ID if present
            if hip_obj.get("id"):
                typer.echo(f"\nID: {hip_obj['id']}")

            return hip_obj

        else:
            # List all HIP objects in the folder (default behavior)
            hip_objects = scm_client.list_hip_objects(folder=folder)

            if not hip_objects:
                typer.echo(f"No HIP objects found in folder '{folder}'")
                return

            typer.echo(f"HIP Objects in folder '{folder}':")
            typer.echo("-" * 60)

            for hip_obj in hip_objects:
                # Display HIP object information
                typer.echo(f"Name: {hip_obj.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if hip_obj.get("folder"):
                    typer.echo(f"  Location: Folder '{hip_obj['folder']}'")
                elif hip_obj.get("snippet"):
                    typer.echo(f"  Location: Snippet '{hip_obj['snippet']}'")
                elif hip_obj.get("device"):
                    typer.echo(f"  Location: Device '{hip_obj['device']}'")
                else:
                    typer.echo("  Location: N/A")

                typer.echo(f"  Description: {hip_obj.get('description', 'N/A')}")

                # Display criteria types
                criteria_types = []
                if hip_obj.get("host_info"):
                    criteria_types.append("Host Info")
                if hip_obj.get("network_info"):
                    criteria_types.append("Network Info")
                if hip_obj.get("patch_management"):
                    criteria_types.append("Patch Management")
                if hip_obj.get("disk_encryption"):
                    criteria_types.append("Disk Encryption")
                if hip_obj.get("mobile_device"):
                    criteria_types.append("Mobile Device")
                if hip_obj.get("certificate"):
                    criteria_types.append("Certificate")

                if criteria_types:
                    typer.echo(f"  Criteria Types: {', '.join(criteria_types)}")

                typer.echo("-" * 60)

            return hip_objects

    except Exception as e:
        typer.echo(f"Error showing HIP object: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# HIP PROFILE COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("hip-profile")
def backup_hip_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Backup HIP profiles from a specified location to a YAML file.

    Examples
    --------
        # Backup from a folder
        scm backup object hip-profile --folder Austin

        # Backup with custom output file
        scm backup object hip-profile --folder Austin --file hip-profiles.yaml

    """
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # Get all HIP profiles from the location
        typer.echo(f"Fetching HIP profiles from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        hip_profiles = scm_client.list_hip_profiles(**kwargs, exact_match=True)

        if not hip_profiles:
            typer.echo(f"No HIP profiles found in {location_type} '{location_value}'")
            return

        # Prepare the data for YAML export
        backup_data: dict[str, list[dict[str, Any]]] = {"hip_profiles": []}

        for profile in hip_profiles:
            # Create a clean dict with only the fields we want to export
            profile_data = {
                "name": profile["name"],
                "folder": profile["folder"],
                "match": profile["match"],
            }

            # Add optional fields if present
            if profile.get("description"):
                profile_data["description"] = profile["description"]

            backup_data["hip_profiles"].append(profile_data)

        # Sort HIP profiles by name for consistent output
        backup_data["hip_profiles"].sort(key=lambda x: x["name"])

        # Determine output file name
        filename = file or get_default_backup_filename("hip-profile", location_type, location_value)

        # Write to YAML file
        with open(filename, "w") as f:
            yaml.dump(backup_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(hip_profiles)} HIP profiles to {filename}")

    except Exception as e:
        typer.echo(f"Error backing up HIP profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("hip-profile")
def delete_hip_profile(
    folder: str = typer.Option(..., "--folder", help="Folder containing the HIP profile"),
    name: str = typer.Option(..., "--name", help="Name of the HIP profile to delete"),
) -> None:
    """Delete a HIP profile from a specific folder."""
    try:
        # Delete the HIP profile
        typer.echo(f"Deleting HIP profile '{name}' from folder '{folder}'...")
        scm_client.delete_hip_profile(folder=folder, name=name)
        typer.echo(f"Deleted HIP profile: {name} from folder {folder}")

    except Exception as e:
        typer.echo(f"Error deleting HIP profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("hip-profile", help="Load HIP profiles from a YAML file.")
def load_hip_profile(
    file: Path = HIP_PROFILE_FILE_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
    dry_run: bool = HIP_PROFILE_DRY_RUN_OPTION,
):
    """Load HIP profiles from a YAML file."""
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # Validate the file exists
        if not file.exists():
            typer.echo(f"Error: File '{file}' does not exist", err=True)
            raise typer.Exit(code=1)

        # Load YAML content
        with file.open() as f:
            yaml_content = yaml.safe_load(f)

        if not yaml_content:
            typer.echo(f"Error: File '{file}' is empty or invalid", err=True)
            raise typer.Exit(code=1)

        # Extract HIP profiles from YAML
        hip_profiles = yaml_content.get("hip_profiles", [])
        if not hip_profiles:
            typer.echo("No HIP profiles found in the YAML file.")
            return

        if dry_run:
            typer.echo("[DRY RUN] Would load the following HIP profiles:")

        results: list[dict[str, Any]] = []
        loaded_count = 0

        for idx, profile_data in enumerate(hip_profiles, 1):
            try:
                # Override container if specified in command line
                if location_value:
                    profile_data[location_type] = location_value
                    # Remove other container fields
                    for container in ["folder", "snippet", "device"]:
                        if container != location_type and container in profile_data:
                            del profile_data[container]

                # Validate the configuration
                profile = HIPProfile(**profile_data)

                if dry_run:
                    typer.echo(f"\n[{idx}] HIP Profile: {profile.name}")
                    typer.echo(f"  Container: {getattr(profile, location_type or 'folder')}")
                    typer.echo(f"  Match: {profile.match}")
                    if profile.description:
                        typer.echo(f"  Description: {profile.description}")
                    results.append({"action": "would create/update", "name": profile.name})
                else:
                    # Convert to SDK model format
                    profile_sdk = profile.to_sdk_model()

                    # Call the SDK client to create the HIP profile
                    container_params = {location_type or "folder": getattr(profile, location_type or "folder")}
                    scm_client.create_hip_profile(
                        **container_params,
                        name=profile_sdk["name"],
                        match=profile_sdk["match"],
                        description=profile_sdk.get("description"),
                    )
                    typer.echo(f"✓ Loaded HIP profile: {profile.name}")
                    loaded_count += 1
                    results.append(
                        {
                            "action": "created/updated",
                            "name": profile.name,
                            "result": profile_sdk,
                        }
                    )
            except Exception as e:
                typer.echo(
                    f"✗ Error with HIP profile '{profile_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                results.append(
                    {
                        "action": "error",
                        "name": profile_data.get("name", "unknown"),
                        "error": str(e),
                    }
                )
                continue

        # Summary
        if dry_run:
            typer.echo(f"\n[DRY RUN] Would load {len(hip_profiles)} HIP profiles from '{file}'")
        else:
            typer.echo(f"\nSuccessfully loaded {loaded_count} out of {len(hip_profiles)} HIP profiles from '{file}'")

    except Exception as e:
        typer.echo(f"Error loading HIP profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("hip-profile")
def set_hip_profile(
    folder: str = typer.Option(..., "--folder", help="Folder path for the HIP profile"),
    name: str = typer.Option(..., "--name", help="Name of the HIP profile"),
    match: str = typer.Option(..., "--match", help="Match criteria for the HIP profile"),
    description: str = typer.Option(None, "--description", help="Description of the HIP profile"),
):
    """Create or update a HIP profile."""
    try:
        # Create the HIP profile object
        hip_profile = HIPProfile(
            folder=folder,
            name=name,
            match=match,
            description=description,
        )

        # Convert to SDK model format
        profile_data = hip_profile.to_sdk_model()

        # Create or update the HIP profile
        result = scm_client.create_hip_profile(
            folder=profile_data["folder"],
            name=profile_data["name"],
            match=profile_data["match"],
            description=profile_data.get("description"),
        )

        # Display result
        typer.echo(f"Created HIP profile: {result['name']} in folder {result['folder']}")
        return result

    except Exception as e:
        typer.echo(f"Error creating/updating HIP profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("hip-profile")
def show_hip_profile(
    folder: str = typer.Option(..., "--folder", help="Folder path for the HIP profile"),
    name: str = typer.Option(None, "--name", help="Name of specific HIP profile to show"),
) -> dict[str, Any] | None:
    """Show HIP profile details or list all HIP profiles in a folder.

    Examples
    --------
        # List all HIP profiles in a folder (default behavior)
        scm show object hip-profile --folder Texas

        # Show a specific HIP profile by name
        scm show object hip-profile --folder Texas --name windows-compliance

    """
    try:
        if name:
            # Show specific HIP profile
            hip_profile = scm_client.get_hip_profile(folder=folder, name=name)

            typer.echo(f"HIP Profile: {hip_profile['name']}")
            typer.echo("-" * 80)
            typer.echo(f"Folder: {hip_profile['folder']}")
            typer.echo(f"Match: {hip_profile['match']}")

            if hip_profile.get("description"):
                typer.echo(f"Description: {hip_profile['description']}")

            # Display ID if present
            if hip_profile.get("id"):
                typer.echo(f"\nID: {hip_profile['id']}")

            return hip_profile

        else:
            # Default behavior: list all HIP profiles in the folder
            hip_profiles = scm_client.list_hip_profiles(folder=folder)
            if not hip_profiles:
                typer.echo(f"No HIP profiles found in folder '{folder}'")
                return None

            typer.echo(f"HIP profiles in folder '{folder}':")
            typer.echo("-" * 80)

            # Display in table format
            for profile in hip_profiles:
                typer.echo(f"Name: {profile['name']}")
                typer.echo(f"  Match: {profile['match']}")
                if profile.get("description"):
                    typer.echo(f"  Description: {profile['description']}")
                typer.echo("")

            typer.echo(f"Total: {len(hip_profiles)} HIP profiles")
            return None

    except Exception as e:
        typer.echo(f"Error showing HIP profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# HTTP SERVER PROFILE COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("http-server-profile")
def backup_http_server_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Backup HTTP server profiles from a specified location to a YAML file.

    Examples
    --------
        # Backup from a folder
        scm backup object http-server-profile --folder Austin

        # Backup with custom output file
        scm backup object http-server-profile --folder Austin --file http-profiles.yaml

    """
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # Get all HTTP server profiles from the location
        typer.echo(f"Fetching HTTP server profiles from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        http_server_profiles = scm_client.list_http_server_profiles(**kwargs, exact_match=True)

        if not http_server_profiles:
            typer.echo(f"No HTTP server profiles found in {location_type} '{location_value}'")
            return

        # Prepare the data for YAML export
        backup_data: dict[str, list[dict[str, Any]]] = {"http_server_profiles": []}

        for profile in http_server_profiles:
            # Create a clean dict with only the fields we want to export
            profile_data = {
                "name": profile["name"],
                "folder": profile["folder"],
                "servers": profile["server"],  # Note: API uses 'server' but we'll use 'servers' in YAML
            }

            # Add optional fields if present
            if profile.get("description"):
                profile_data["description"] = profile["description"]

            if profile.get("tag_registration"):
                profile_data["tag_registration"] = profile["tag_registration"]

            if profile.get("format"):
                profile_data["format_config"] = profile["format"]

            backup_data["http_server_profiles"].append(profile_data)

        # Sort HTTP server profiles by name for consistent output
        backup_data["http_server_profiles"].sort(key=lambda x: x["name"])

        # Determine output file name
        filename = file or get_default_backup_filename("http-server-profile", location_type, location_value)

        # Write to YAML file
        with open(filename, "w") as f:
            yaml.dump(backup_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(http_server_profiles)} HTTP server profiles to {filename}")

    except Exception as e:
        typer.echo(f"Error backing up HTTP server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("http-server-profile")
def delete_http_server_profile(
    folder: str = typer.Option(..., "--folder", help="Folder containing the HTTP server profile"),
    name: str = typer.Option(..., "--name", help="Name of the HTTP server profile to delete"),
) -> None:
    """Delete an HTTP server profile from a specific folder."""
    try:
        # Delete the HTTP server profile
        typer.echo(f"Deleting HTTP server profile '{name}' from folder '{folder}'...")
        scm_client.delete_http_server_profile(folder=folder, name=name)
        typer.echo(f"Deleted HTTP server profile: {name} from folder {folder}")

    except Exception as e:
        typer.echo(f"Error deleting HTTP server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("http-server-profile", help="Load HTTP server profiles from a YAML file.")
def load_http_server_profile(
    file: Path = HTTP_SERVER_PROFILE_FILE_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
    dry_run: bool = HTTP_SERVER_PROFILE_DRY_RUN_OPTION,
):
    """Load HTTP server profiles from a YAML file."""
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # Validate the file exists
        if not file.exists():
            typer.echo(f"Error: File '{file}' does not exist", err=True)
            raise typer.Exit(code=1)

        # Load YAML content
        with file.open() as f:
            yaml_content = yaml.safe_load(f)

        if not yaml_content:
            typer.echo(f"Error: File '{file}' is empty or invalid", err=True)
            raise typer.Exit(code=1)

        # Extract HTTP server profiles from YAML
        http_server_profiles = yaml_content.get("http_server_profiles", [])
        if not http_server_profiles:
            typer.echo("No HTTP server profiles found in the YAML file.")
            return

        if dry_run:
            typer.echo("[DRY RUN] Would load the following HTTP server profiles:")

        results: list[dict[str, Any]] = []
        loaded_count = 0

        for idx, profile_data in enumerate(http_server_profiles, 1):
            try:
                # Override container if specified in command line
                if location_value:
                    profile_data[location_type] = location_value
                    # Remove other container fields
                    for container in ["folder", "snippet", "device"]:
                        if container != location_type and container in profile_data:
                            del profile_data[container]

                # Validate using the Pydantic model
                profile = HTTPServerProfile(**profile_data)

                if dry_run:
                    typer.echo(f"\n[{idx}] HTTP Server Profile: {profile.name}")
                    typer.echo(f"  Container: {getattr(profile, location_type or 'folder')}")
                    typer.echo(f"  Servers: {len(profile.servers)}")
                    for server_idx, server in enumerate(profile.servers):
                        typer.echo(
                            f"    Server {server_idx + 1}: {server.get('name', 'unnamed')} - {server.get('address', 'N/A')}:{server.get('port', 'N/A')} ({server.get('protocol', 'N/A')})"
                        )
                    if profile.description:
                        typer.echo(f"  Description: {profile.description}")
                    if profile.tag_registration:
                        typer.echo(f"  Tag Registration: {profile.tag_registration}")
                    results.append({"action": "would create/update", "name": profile.name})
                else:
                    # Convert to SDK model format
                    profile_sdk = profile.to_sdk_model()

                    # Call the SDK client to create the HTTP server profile
                    container_params = {location_type or "folder": getattr(profile, location_type or "folder")}
                    scm_client.create_http_server_profile(
                        **container_params,
                        **profile_sdk,
                    )
                    typer.echo(f"✓ Loaded HTTP server profile: {profile.name}")
                    loaded_count += 1
                    results.append(
                        {
                            "action": "created/updated",
                            "name": profile.name,
                            "result": profile_sdk,
                        }
                    )
            except Exception as e:
                typer.echo(
                    f"✗ Error with HTTP server profile '{profile_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                results.append(
                    {
                        "action": "error",
                        "name": profile_data.get("name", "unknown"),
                        "error": str(e),
                    }
                )
                continue

        # Summary
        if dry_run:
            typer.echo(f"\n[DRY RUN] Would load {len(http_server_profiles)} HTTP server profiles from '{file}'")
        else:
            typer.echo(f"\nSuccessfully loaded {loaded_count} out of {len(http_server_profiles)} HTTP server profiles from '{file}'")

    except Exception as e:
        typer.echo(f"Error loading HTTP server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("http-server-profile")
def set_http_server_profile(
    folder: str = typer.Option(..., "--folder", help="Folder path for the HTTP server profile"),
    name: str = typer.Option(..., "--name", help="Name of the HTTP server profile"),
    servers: str = typer.Option(..., "--servers", help="JSON string of server configurations"),
    description: str = typer.Option(None, "--description", help="Description of the HTTP server profile"),
    tag_registration: bool = typer.Option(False, "--tag-registration", help="Register tags on match"),
):
    """Create or update an HTTP server profile.

    Server configuration must be provided as a JSON string, e.g.:
    --servers '[{"name": "server1", "address": "192.168.1.100", "protocol": "HTTPS", "port": 443}]'
    """
    try:
        # Parse servers JSON
        import json as json_lib

        try:
            servers_list = json_lib.loads(servers)
            if not isinstance(servers_list, list):
                raise ValueError("Servers must be a JSON array")
        except json_lib.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON for servers: {e}") from e

        # Create the HTTP server profile object
        http_server_profile = HTTPServerProfile(
            folder=folder,
            name=name,
            servers=servers_list,
            description=description,
            tag_registration=tag_registration,
            format_config=None,
        )

        # Convert to SDK model format
        profile_data = http_server_profile.to_sdk_model()

        # Create or update the HTTP server profile
        result = scm_client.create_http_server_profile(
            folder=profile_data["folder"],
            name=profile_data["name"],
            servers=profile_data["server"],
            description=profile_data.get("description"),
            tag_registration=profile_data.get("tag_registration", False),
            format_config=profile_data.get("format"),
        )

        # Display result
        typer.echo(f"Created HTTP server profile: {result['name']} in folder {result['folder']}")
        return result

    except ValueError as e:
        typer.echo(f"Validation error: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating HTTP server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("http-server-profile")
def show_http_server_profile(
    folder: str = typer.Option(..., "--folder", help="Folder path for the HTTP server profile"),
    name: str = typer.Option(None, "--name", help="Name of specific HTTP server profile to show"),
    list: bool = typer.Option(False, "--list", help="List all HTTP server profiles in the folder"),
) -> dict[str, Any] | None:
    """Show HTTP server profile details or list all HTTP server profiles in a folder.

    Examples
    --------
        # List all HTTP server profiles in a folder (default behavior)
        scm show object http-server-profile --folder Texas

        # Show a specific HTTP server profile by name
        scm show object http-server-profile --folder Texas --name syslog-collector

    """
    try:
        if list:
            # List all HTTP server profiles in the folder (default behavior)
            http_server_profiles = scm_client.list_http_server_profiles(folder=folder)
            if not http_server_profiles:
                typer.echo(f"No HTTP server profiles found in folder '{folder}'")
                return None

            typer.echo(f"HTTP server profiles in folder '{folder}':")
            typer.echo("-" * 80)

            # Display in table format
            for profile in http_server_profiles:
                typer.echo(f"Name: {profile['name']}")
                if profile.get("description"):
                    typer.echo(f"  Description: {profile['description']}")
                typer.echo(f"  Tag Registration: {profile.get('tag_registration', False)}")
                typer.echo(f"  Servers: {len(profile.get('server', []))}")
                for idx, server in enumerate(profile.get("server", [])):
                    typer.echo(f"    Server {idx + 1}: {server.get('name', 'unnamed')} - {server.get('address', 'N/A')}:{server.get('port', 'N/A')} ({server.get('protocol', 'N/A')})")
                typer.echo("")

            typer.echo(f"Total: {len(http_server_profiles)} HTTP server profiles")
            return None

        elif name:
            # Show specific HTTP server profile
            http_server_profile = scm_client.get_http_server_profile(folder=folder, name=name)

            typer.echo(f"HTTP Server Profile: {http_server_profile['name']}")
            typer.echo("-" * 80)
            typer.echo(f"Folder: {http_server_profile['folder']}")

            if http_server_profile.get("description"):
                typer.echo(f"Description: {http_server_profile['description']}")

            typer.echo(f"Tag Registration: {http_server_profile.get('tag_registration', False)}")

            # Display servers
            typer.echo(f"\nServers ({len(http_server_profile.get('server', []))}):")
            for idx, server in enumerate(http_server_profile.get("server", [])):
                typer.echo(f"  Server {idx + 1}: {server.get('name', 'unnamed')}")
                typer.echo(f"    Address: {server.get('address', 'N/A')}")
                typer.echo(f"    Protocol: {server.get('protocol', 'N/A')}")
                typer.echo(f"    Port: {server.get('port', 'N/A')}")
                if server.get("protocol") == "HTTPS" and server.get("tls_version"):
                    typer.echo(f"    TLS Version: {server.get('tls_version')}")
                if server.get("certificate_profile"):
                    typer.echo(f"    Certificate Profile: {server.get('certificate_profile')}")
                if server.get("http_method"):
                    typer.echo(f"    HTTP Method: {server.get('http_method')}")
                if server.get("username"):
                    typer.echo(f"    Username: {server.get('username')}")
                    typer.echo(f"    Password: {'*' * 8}")  # Hide password

            # Display format configuration if present
            if http_server_profile.get("format"):
                typer.echo("\nFormat Configuration:")
                for log_type, format_config in http_server_profile["format"].items():
                    typer.echo(f"  {log_type}:")
                    if isinstance(format_config, dict):
                        if format_config.get("name"):
                            typer.echo(f"    Name: {format_config['name']}")
                        if format_config.get("url_format"):
                            typer.echo(f"    URL Format: {format_config['url_format']}")
                        if format_config.get("headers"):
                            typer.echo(f"    Headers: {len(format_config['headers'])} configured")
                        if format_config.get("params"):
                            typer.echo(f"    Parameters: {len(format_config['params'])} configured")

            # Display ID if present
            if http_server_profile.get("id"):
                typer.echo(f"\nID: {http_server_profile['id']}")

            return http_server_profile

        else:
            # Neither --list nor --name was provided
            typer.echo("Error: Either --list or --name must be specified", err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"Error showing HTTP server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# LOG FORWARDING PROFILE COMMANDS
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@backup_app.command("log-forwarding-profile")
def backup_log_forwarding_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Backup log forwarding profiles from a specified location to a YAML file.

    Examples
    --------
        # Backup from a folder
        scm backup object log-forwarding-profile --folder Austin

        # Backup with custom output file
        scm backup object log-forwarding-profile --folder Austin --file log-profiles.yaml

        # Exclude default profiles
        scm backup object log-forwarding-profile --folder Austin --exclude-default

    """
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # List all log forwarding profiles in the location (exact match)
        kwargs = {location_type: location_value}
        log_forwarding_profiles = scm_client.list_log_forwarding_profiles(**kwargs, exact_match=True)

        if not log_forwarding_profiles:
            typer.echo(f"No log forwarding profiles found in {location_type} '{location_value}'")
            return

        # Convert profiles to backup format
        profiles_data = []
        for profile in log_forwarding_profiles:
            # Remove system fields
            profile_data = {
                "name": profile["name"],
                "folder": profile["folder"],
            }

            # Add optional fields if present
            if profile.get("description"):
                profile_data["description"] = profile["description"]

            if profile.get("enhanced_application_logging"):
                profile_data["enhanced_application_logging"] = profile["enhanced_application_logging"]

            if profile.get("match_list"):
                profile_data["match_list"] = profile["match_list"]

            profiles_data.append(profile_data)

        # Prepare YAML data
        yaml_data = {"log_forwarding_profiles": profiles_data}

        # Generate output filename if not provided
        filename = file or get_default_backup_filename("log-forwarding-profile", location_type, location_value)

        # Write to file
        with open(filename, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(profiles_data)} log forwarding profiles to {filename}")

    except Exception as e:
        typer.echo(f"Error backing up log forwarding profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("log-forwarding-profile")
def delete_log_forwarding_profile(
    folder: str = typer.Option(..., "--folder", help="Folder path for the log forwarding profile"),
    name: str = typer.Option(..., "--name", help="Name of the log forwarding profile to delete"),
) -> None:
    """Delete a log forwarding profile."""
    try:
        # Delete the log forwarding profile
        success = scm_client.delete_log_forwarding_profile(folder=folder, name=name)

        if success:
            typer.echo(f"Deleted log forwarding profile: {name} from folder {folder}")
        else:
            typer.echo(
                f"Failed to delete log forwarding profile '{name}' from folder '{folder}'",
                err=True,
            )
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting log forwarding profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("log-forwarding-profile", help="Load log forwarding profiles from a YAML file.")
def load_log_forwarding_profile(
    file: Path = FILE_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load log forwarding profiles from a YAML file."""
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # Validate the file exists
        if not file.exists():
            typer.echo(f"Error: File '{file}' does not exist", err=True)
            raise typer.Exit(code=1)

        # Load YAML content
        with file.open() as f:
            yaml_content = yaml.safe_load(f)

        if not yaml_content:
            typer.echo(f"Error: File '{file}' is empty or invalid", err=True)
            raise typer.Exit(code=1)

        # Extract log forwarding profiles from YAML
        log_forwarding_profiles = yaml_content.get("log_forwarding_profiles", [])
        if not log_forwarding_profiles:
            typer.echo("No log forwarding profiles found in the YAML file.")
            return

        if dry_run:
            typer.echo("[DRY RUN] Would load the following log forwarding profiles:")

        results: list[dict[str, Any]] = []
        loaded_count = 0

        for idx, profile_data in enumerate(log_forwarding_profiles, 1):
            try:
                # Override container if specified in command line
                if location_value:
                    profile_data[location_type] = location_value
                    # Remove other container fields
                    for container in ["folder", "snippet", "device"]:
                        if container != location_type and container in profile_data:
                            del profile_data[container]

                # Validate using Pydantic model
                profile = LogForwardingProfile(**profile_data)

                if dry_run:
                    typer.echo(f"\n[{idx}] Log Forwarding Profile: {profile.name}")
                    typer.echo(f"  Container: {getattr(profile, location_type or 'folder')}")
                    if profile.description:
                        typer.echo(f"  Description: {profile.description}")
                    if profile.enhanced_application_logging:
                        typer.echo(f"  Enhanced Application Logging: {profile.enhanced_application_logging}")
                    if profile.match_list:
                        typer.echo(f"  Match List: {len(profile.match_list)} entries")
                        for match_idx, match in enumerate(profile.match_list):
                            typer.echo(f"    Match {match_idx + 1}: {match.get('name', 'unnamed')} - {match.get('log_type', 'N/A')}")
                    results.append({"action": "would create/update", "name": profile.name})
                else:
                    # Create the log forwarding profile
                    container_params = {location_type or "folder": getattr(profile, location_type or "folder")}
                    result = scm_client.create_log_forwarding_profile(
                        **container_params,
                        name=profile.name,
                        description=profile.description,
                        enhanced_application_logging=profile.enhanced_application_logging or False,
                        match_list=profile.match_list,
                    )

                    typer.echo(f"✓ Loaded log forwarding profile: {profile.name}")
                    loaded_count += 1
                    results.append(
                        {
                            "action": "created/updated",
                            "name": profile.name,
                            "result": result,
                        }
                    )
            except Exception as e:
                typer.echo(
                    f"✗ Error with log forwarding profile '{profile_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                results.append(
                    {
                        "action": "error",
                        "name": profile_data.get("name", "unknown"),
                        "error": str(e),
                    }
                )
                continue

        # Summary
        if dry_run:
            typer.echo(f"\n[DRY RUN] Would load {len(log_forwarding_profiles)} log forwarding profiles from '{file}'")
        else:
            typer.echo(f"\nSuccessfully loaded {loaded_count} out of {len(log_forwarding_profiles)} log forwarding profiles from '{file}'")

    except Exception as e:
        typer.echo(f"Error loading log forwarding profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("log-forwarding-profile")
def set_log_forwarding_profile(
    folder: str = typer.Option(..., "--folder", help="Folder path for the log forwarding profile"),
    name: str = typer.Option(..., "--name", help="Name of the log forwarding profile"),
    match_list: str = typer.Option(None, "--match-list", help="Match list configuration as JSON string"),
    description: str = typer.Option(None, "--description", help="Description of the log forwarding profile"),
    enhanced_application_logging: bool = typer.Option(
        False,
        "--enhanced-application-logging",
        help="Enable enhanced application logging",
    ),
) -> None:
    """Create or update a log forwarding profile."""
    import json

    try:
        # Parse match list if provided
        match_list_data = None
        if match_list:
            try:
                match_list_data = json.loads(match_list)
                if not isinstance(match_list_data, list):
                    typer.echo("Error: match_list must be a JSON array", err=True)
                    raise typer.Exit(code=1)
            except json.JSONDecodeError as e:
                typer.echo(f"Error parsing match list JSON: {str(e)}", err=True)
                raise typer.Exit(code=1) from e

        # Validate using Pydantic model
        profile_data: dict[str, Any] = {
            "folder": folder,
            "name": name,
        }

        if description:
            profile_data["description"] = description
        if enhanced_application_logging:
            profile_data["enhanced_application_logging"] = enhanced_application_logging
        if match_list_data:
            profile_data["match_list"] = match_list_data

        profile = LogForwardingProfile(**profile_data)

        # Create the log forwarding profile using SDK
        result = scm_client.create_log_forwarding_profile(
            folder=profile.folder,
            name=profile.name,
            description=profile.description,
            enhanced_application_logging=profile.enhanced_application_logging,
            match_list=profile.match_list,
        )

        if result:
            typer.echo(f"Created log forwarding profile: {name} in folder {folder}")
        else:
            typer.echo(f"Failed to create/update log forwarding profile '{name}'", err=True)
            raise typer.Exit(code=1)

    except ValueError as e:
        typer.echo(f"Validation error: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating log forwarding profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("log-forwarding-profile")
def show_log_forwarding_profile(
    folder: str = typer.Option(..., "--folder", help="Folder path for the log forwarding profile"),
    name: str = typer.Option(None, "--name", help="Name of specific log forwarding profile to show"),
    list: bool = typer.Option(False, "--list", help="List all log forwarding profiles in the folder"),
) -> dict[str, Any] | None:
    """Show log forwarding profile details or list all log forwarding profiles in a folder.

    Examples
    --------
        # List all log forwarding profiles in a folder (default behavior)
        scm show object log-forwarding-profile --folder Texas

        # Show a specific log forwarding profile by name
        scm show object log-forwarding-profile --folder Texas --name security-logs

    """
    try:
        if list:
            # List all log forwarding profiles in the folder (default behavior)
            log_forwarding_profiles = scm_client.list_log_forwarding_profiles(folder=folder)
            if not log_forwarding_profiles:
                typer.echo(f"No log forwarding profiles found in folder '{folder}'")
                return None

            typer.echo(f"Log forwarding profiles in folder '{folder}':")
            typer.echo("-" * 80)

            # Display in table format
            for profile in log_forwarding_profiles:
                typer.echo(f"Name: {profile['name']}")
                if profile.get("description"):
                    typer.echo(f"  Description: {profile['description']}")
                typer.echo(f"  Enhanced Application Logging: {profile.get('enhanced_application_logging', False)}")
                match_list = profile.get("match_list", [])
                typer.echo(f"  Match Rules: {len(match_list)}")
                for idx, match in enumerate(match_list):
                    typer.echo(f"    Rule {idx + 1}: {match.get('name', 'unnamed')} ({match.get('log_type', 'N/A')})")
                    actions = []
                    if match.get("send_to_panorama"):
                        actions.append("Panorama")
                    if match.get("send_syslog"):
                        actions.append(f"Syslog: {', '.join(match['send_syslog'])}")
                    if match.get("send_http"):
                        actions.append(f"HTTP: {', '.join(match['send_http'])}")
                    if match.get("quarantine"):
                        actions.append("Quarantine")
                    if actions:
                        typer.echo(f"      Actions: {', '.join(actions)}")
                typer.echo("")

            typer.echo(f"Total: {len(log_forwarding_profiles)} log forwarding profiles")
            return None

        elif name:
            # Show specific log forwarding profile
            log_forwarding_profile = scm_client.get_log_forwarding_profile(folder=folder, name=name)

            typer.echo(f"Log Forwarding Profile: {log_forwarding_profile['name']}")
            typer.echo("-" * 80)
            typer.echo(f"Folder: {log_forwarding_profile['folder']}")

            if log_forwarding_profile.get("description"):
                typer.echo(f"Description: {log_forwarding_profile['description']}")

            typer.echo(f"Enhanced Application Logging: {log_forwarding_profile.get('enhanced_application_logging', False)}")

            # Display match list
            match_list = log_forwarding_profile.get("match_list", [])
            typer.echo(f"\nMatch Rules ({len(match_list)}):")
            for idx, match in enumerate(match_list):
                typer.echo(f"  Rule {idx + 1}: {match.get('name', 'unnamed')}")
                typer.echo(f"    Log Type: {match.get('log_type', 'N/A')}")
                if match.get("action_desc"):
                    typer.echo(f"    Description: {match['action_desc']}")
                if match.get("filter"):
                    typer.echo(f"    Filter: {match['filter']}")

                # Display actions
                typer.echo("    Actions:")
                if match.get("send_to_panorama"):
                    typer.echo("      - Send to Panorama")
                if match.get("send_syslog"):
                    typer.echo(f"      - Send to Syslog: {', '.join(match['send_syslog'])}")
                if match.get("send_http"):
                    typer.echo(f"      - Send to HTTP: {', '.join(match['send_http'])}")
                if match.get("quarantine"):
                    typer.echo("      - Quarantine")

            # Display ID if present
            if log_forwarding_profile.get("id"):
                typer.echo(f"\nID: {log_forwarding_profile['id']}")

            return log_forwarding_profile

        else:
            # Neither --list nor --name was provided
            typer.echo("Error: Either --list or --name must be specified", err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"Error showing log forwarding profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# SERVICE COMMANDS
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@backup_app.command("service")
def backup_service(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Backup services from a specified location to a YAML file.

    Examples
    --------
        # Backup from a folder
        scm backup object service --folder Austin

        # Backup with custom output file
        scm backup object service --folder Austin --file services.yaml

    """
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # List all services in the location (exact match)
        kwargs = {location_type: location_value}
        services = scm_client.list_services(**kwargs, exact_match=True)

        if not services:
            typer.echo(f"No services found in {location_type} '{location_value}'")
            return

        # Convert services to backup format
        services_data = []
        for service in services:
            # Remove system fields
            service_data = {
                "name": service["name"],
                "folder": service["folder"],
                "protocol": service["protocol"],
            }

            # Add optional fields if present
            if service.get("description"):
                service_data["description"] = service["description"]

            if service.get("tag"):
                service_data["tag"] = service["tag"]

            services_data.append(service_data)

        # Prepare YAML data
        yaml_data = {"services": services_data}

        # Generate output filename if not provided
        filename = Path(file or get_default_backup_filename("service", location_type, location_value))

        # Write to file
        with filename.open("w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(services_data)} services to {filename}")

    except Exception as e:
        typer.echo(f"Error backing up services: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("service")
def delete_service(
    folder: str = typer.Option(..., "--folder", help="Folder path for the service"),
    name: str = typer.Option(..., "--name", help="Name of the service to delete"),
) -> None:
    """Delete a service."""
    try:
        # Delete the service
        success = scm_client.delete_service(folder=folder, name=name)

        if success:
            typer.echo(f"Deleted service: {name} from folder {folder}")
        else:
            typer.echo(f"Failed to delete service '{name}' from folder '{folder}'", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting service: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("service", help="Load services from a YAML file.")
def load_service(
    file: Path = FILE_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load services from a YAML file."""
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # Validate the file exists
        if not file.exists():
            typer.echo(f"Error: File '{file}' does not exist", err=True)
            raise typer.Exit(code=1)

        # Load YAML content
        with file.open() as f:
            yaml_content = yaml.safe_load(f)

        if not yaml_content:
            typer.echo(f"Error: File '{file}' is empty or invalid", err=True)
            raise typer.Exit(code=1)

        # Extract services from YAML
        services = yaml_content.get("services", [])
        if not services:
            typer.echo("No services found in the YAML file.")
            return

        if dry_run:
            typer.echo("[DRY RUN] Would load the following services:")

        results: list[dict[str, Any]] = []
        loaded_count = 0

        for idx, service_data in enumerate(services, 1):
            try:
                # Override container if specified in command line
                if location_value:
                    service_data[location_type] = location_value
                    # Remove other container fields
                    for container in ["folder", "snippet", "device"]:
                        if container != location_type and container in service_data:
                            del service_data[container]

                # Validate using Pydantic model
                service = Service(**service_data)

                if dry_run:
                    typer.echo(f"\n[{idx}] Service: {service.name}")
                    typer.echo(f"  Container: {getattr(service, location_type or 'folder')}")
                    if service.description:
                        typer.echo(f"  Description: {service.description}")

                    # Display protocol info
                    protocol = service_data.get("protocol", {})
                    if "tcp" in protocol:
                        typer.echo("  Protocol: TCP")
                        typer.echo(f"    Port: {protocol['tcp']['port']}")
                        if "override" in protocol["tcp"]:
                            typer.echo(f"    Override settings: {protocol['tcp']['override']}")
                    elif "udp" in protocol:
                        typer.echo("  Protocol: UDP")
                        typer.echo(f"    Port: {protocol['udp']['port']}")
                        if "override" in protocol["udp"]:
                            typer.echo(f"    Override settings: {protocol['udp']['override']}")

                    if service.tag:
                        typer.echo(f"  Tags: {', '.join(service.tag)}")
                    results.append({"action": "would create/update", "name": service.name})
                else:
                    # Create the service
                    container_params = {location_type or "folder": getattr(service, location_type or "folder")}
                    result = scm_client.create_service(
                        **container_params,
                        name=service.name,
                        protocol=service.protocol,
                        description=service.description,
                        tag=service.tag,
                    )

                    typer.echo(f"✓ Loaded service: {service.name}")
                    loaded_count += 1
                    results.append(
                        {
                            "action": "created/updated",
                            "name": service.name,
                            "result": result,
                        }
                    )

            except Exception as e:
                typer.echo(
                    f"✗ Error with service '{service_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                results.append(
                    {
                        "action": "error",
                        "name": service_data.get("name", "unknown"),
                        "error": str(e),
                    }
                )
                continue

        # Summary
        if dry_run:
            typer.echo(f"\n[DRY RUN] Would load {len(services)} services from '{file}'")
        else:
            typer.echo(f"\nSuccessfully loaded {loaded_count} out of {len(services)} services from '{file}'")

    except Exception as e:
        typer.echo(f"Error loading services: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("service")
def set_service(
    folder: str = typer.Option(..., "--folder", help="Folder path for the service"),
    name: str = typer.Option(..., "--name", help="Name of the service"),
    protocol: str = typer.Option(..., "--protocol", help="Protocol type (tcp or udp)"),
    port: str = typer.Option(
        ...,
        "--port",
        help="Port number, range (e.g., 80-443), or comma-separated list (e.g., 80,443,8080)",
    ),
    description: str = typer.Option(None, "--description", help="Description of the service"),
    tag: str = typer.Option(None, "--tag", help="Comma-separated list of tags"),
    timeout: int = typer.Option(None, "--timeout", help="Timeout override in seconds (TCP only)"),
    halfclose_timeout: int = typer.Option(
        None,
        "--halfclose-timeout",
        help="Half-close timeout override in seconds (TCP only)",
    ),
    timewait_timeout: int = typer.Option(
        None,
        "--timewait-timeout",
        help="Time-wait timeout override in seconds (TCP only)",
    ),
) -> None:
    """Create or update a service."""
    try:
        # Build protocol configuration
        protocol_config = {protocol.lower(): {"port": port}}

        # Add override settings if provided (TCP only)
        if protocol.lower() == "tcp" and any([timeout, halfclose_timeout, timewait_timeout]):
            override = {}
            if timeout is not None:
                override["timeout"] = timeout
            if halfclose_timeout is not None:
                override["halfclose_timeout"] = halfclose_timeout
            if timewait_timeout is not None:
                override["timewait_timeout"] = timewait_timeout
            protocol_config["tcp"]["override"] = override

        # Parse tags if provided
        tag_list = None
        if tag:
            tag_list = [t.strip() for t in tag.split(",") if t.strip()]

        # Validate using Pydantic model
        service_data: dict[str, Any] = {
            "folder": folder,
            "name": name,
            "protocol": protocol_config,
        }

        if description:
            service_data["description"] = description
        if tag_list:
            service_data["tag"] = tag_list

        service = Service(**service_data)

        # Create the service using SDK
        result = scm_client.create_service(
            folder=service.folder,
            name=service.name,
            protocol=service.protocol,
            description=service.description,
            tag=service.tag,
        )

        if result:
            # Get the action performed
            action = result.pop("__action__", "created")

            if action == "created":
                typer.echo(f"✅ Created service: {name} in folder {folder}")
            elif action == "updated":
                typer.echo(f"✅ Updated service: {name} in folder {folder}")
            elif action == "no_change":
                typer.echo(f"ℹ️  No changes needed for service: {name} in folder {folder}")
        else:
            typer.echo(f"Failed to create/update service '{name}'", err=True)
            raise typer.Exit(code=1)

    except ValueError as e:
        typer.echo(f"Validation error: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating service: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("service")
def show_service(
    folder: str = typer.Option(..., "--folder", help="Folder path for the service"),
    name: str = typer.Option(None, "--name", help="Name of specific service to show"),
    list: bool = typer.Option(False, "--list", help="List all services in the folder"),
) -> dict[str, Any] | None:
    """Show service details or list all services in a folder.

    Examples
    --------
        # List all services in a folder (default behavior)
        scm show object service --folder Texas

        # Show a specific service by name
        scm show object service --folder Texas --name web-server

    """
    try:
        if list:
            # List all services in the folder (default behavior)
            services = scm_client.list_services(folder=folder)
            if not services:
                typer.echo(f"No services found in folder '{folder}'")
                return None

            typer.echo(f"Services in folder '{folder}':")
            typer.echo("-" * 80)

            # Display in table format
            for service in services:
                typer.echo(f"Name: {service['name']}")
                if service.get("description"):
                    typer.echo(f"  Description: {service['description']}")

                # Display protocol info
                protocol = service.get("protocol", {})
                if "tcp" in protocol:
                    typer.echo("  Protocol: TCP")
                    typer.echo(f"    Port: {protocol['tcp']['port']}")
                    if "override" in protocol["tcp"]:
                        override = protocol["tcp"]["override"]
                        override_parts = []
                        if "timeout" in override:
                            override_parts.append(f"timeout={override['timeout']}s")
                        if "halfclose_timeout" in override:
                            override_parts.append(f"halfclose={override['halfclose_timeout']}s")
                        if "timewait_timeout" in override:
                            override_parts.append(f"timewait={override['timewait_timeout']}s")
                        if override_parts:
                            typer.echo(f"    Overrides: {', '.join(override_parts)}")
                elif "udp" in protocol:
                    typer.echo("  Protocol: UDP")
                    typer.echo(f"    Port: {protocol['udp']['port']}")
                    if "override" in protocol["udp"]:
                        override = protocol["udp"]["override"]
                        if "timeout" in override:
                            typer.echo(f"    Override: timeout={override['timeout']}s")

                if service.get("tag"):
                    typer.echo(f"  Tags: {', '.join(service['tag'])}")
                typer.echo("")

            typer.echo(f"Total: {len(services)} services")
            return None

        elif name:
            # Show specific service
            service = scm_client.get_service(folder=folder, name=name)

            typer.echo(f"Service: {service['name']}")
            typer.echo("-" * 80)
            typer.echo(f"Folder: {service['folder']}")

            if service.get("description"):
                typer.echo(f"Description: {service['description']}")

            # Display protocol details
            protocol = service.get("protocol", {})
            if "tcp" in protocol:
                typer.echo("\nProtocol: TCP")
                typer.echo(f"  Port: {protocol['tcp']['port']}")
                if "override" in protocol["tcp"]:
                    typer.echo("  Override Settings:")
                    override = protocol["tcp"]["override"]
                    if "timeout" in override:
                        typer.echo(f"    Timeout: {override['timeout']} seconds")
                    if "halfclose_timeout" in override:
                        typer.echo(f"    Half-close Timeout: {override['halfclose_timeout']} seconds")
                    if "timewait_timeout" in override:
                        typer.echo(f"    Time-wait Timeout: {override['timewait_timeout']} seconds")
            elif "udp" in protocol:
                typer.echo("\nProtocol: UDP")
                typer.echo(f"  Port: {protocol['udp']['port']}")
                if "override" in protocol["udp"]:
                    override = protocol["udp"]["override"]
                    if "timeout" in override:
                        typer.echo(f"  Timeout Override: {override['timeout']} seconds")

            if service.get("tag"):
                typer.echo(f"\nTags: {', '.join(service['tag'])}")

            # Display ID if present
            if service.get("id"):
                typer.echo(f"\nID: {service['id']}")

            return service

        else:
            # Neither --list nor --name was provided
            typer.echo("Error: Either --list or --name must be specified", err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"Error showing service: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# SERVICE GROUP COMMANDS
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@backup_app.command("service-group")
def backup_service_group(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Backup service groups from a specified location to a YAML file.

    Examples
    --------
        # Backup from a folder
        scm backup object service-group --folder Austin

        # Backup with custom output file
        scm backup object service-group --folder Austin --file service-groups.yaml

    """
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # List all service groups in the location (exact match)
        kwargs = {location_type: location_value}
        service_groups = scm_client.list_service_groups(**kwargs, exact_match=True)

        if not service_groups:
            typer.echo(f"No service groups found in {location_type} '{location_value}'")
            return

        # Convert service groups to backup format
        groups_data = []
        for group in service_groups:
            # Remove system fields
            group_data = {
                "name": group["name"],
                "folder": group["folder"],
                "members": group["members"],
            }

            # Add optional fields if present
            if group.get("tag"):
                group_data["tag"] = group["tag"]

            groups_data.append(group_data)

        # Prepare YAML data
        yaml_data = {"service_groups": groups_data}

        # Generate output filename if not provided
        filename = file or get_default_backup_filename("service-group", location_type, location_value)

        # Write to file
        with open(filename, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(groups_data)} service groups to {filename}")

    except Exception as e:
        typer.echo(f"Error backing up service groups: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("service-group")
def delete_service_group(
    folder: str = typer.Option(..., "--folder", help="Folder path for the service group"),
    name: str = typer.Option(..., "--name", help="Name of the service group to delete"),
) -> None:
    """Delete a service group."""
    try:
        # Delete the service group
        success = scm_client.delete_service_group(folder=folder, name=name)

        if success:
            typer.echo(f"Deleted service group: {name} from folder {folder}")
        else:
            typer.echo(
                f"Failed to delete service group '{name}' from folder '{folder}'",
                err=True,
            )
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting service group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("service-group", help="Load service groups from a YAML file.")
def load_service_group(
    file: Path = FILE_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load service groups from a YAML file."""
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # Validate the file exists
        if not file.exists():
            typer.echo(f"Error: File '{file}' does not exist", err=True)
            raise typer.Exit(code=1)

        # Load YAML content
        with file.open() as f:
            yaml_content = yaml.safe_load(f)

        if not yaml_content:
            typer.echo(f"Error: File '{file}' is empty or invalid", err=True)
            raise typer.Exit(code=1)

        # Extract service groups from YAML
        service_groups = yaml_content.get("service_groups", [])
        if not service_groups:
            typer.echo("No service groups found in the YAML file.")
            return

        if dry_run:
            typer.echo("[DRY RUN] Would load the following service groups:")

        results: list[dict[str, Any]] = []
        loaded_count = 0

        for idx, group_data in enumerate(service_groups, 1):
            try:
                # Override container if specified in command line
                if location_value:
                    group_data[location_type] = location_value
                    # Remove other container fields
                    for container in ["folder", "snippet", "device"]:
                        if container != location_type and container in group_data:
                            del group_data[container]

                # Validate using Pydantic model
                service_group = ServiceGroup(**group_data)

                if dry_run:
                    typer.echo(f"\n[{idx}] Service Group: {service_group.name}")
                    typer.echo(f"  Container: {getattr(service_group, location_type or 'folder')}")
                    typer.echo(f"  Members ({len(service_group.members)}): {', '.join(service_group.members)}")
                    if service_group.tag:
                        typer.echo(f"  Tags: {', '.join(service_group.tag)}")
                    results.append({"action": "would create/update", "name": service_group.name})
                else:
                    # Create the service group
                    container_params = {location_type or "folder": getattr(service_group, location_type or "folder")}
                    result = scm_client.create_service_group(
                        **container_params,
                        name=service_group.name,
                        members=service_group.members,
                        tag=service_group.tag,
                    )

                    typer.echo(f"✓ Loaded service group: {service_group.name}")
                    loaded_count += 1
                    results.append(
                        {
                            "action": "created/updated",
                            "name": service_group.name,
                            "result": result,
                        }
                    )

            except Exception as e:
                typer.echo(
                    f"✗ Error with service group '{group_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                results.append(
                    {
                        "action": "error",
                        "name": group_data.get("name", "unknown"),
                        "error": str(e),
                    }
                )
                continue

        # Summary
        if dry_run:
            typer.echo(f"\n[DRY RUN] Would load {len(service_groups)} service groups from '{file}'")
        else:
            typer.echo(f"\nSuccessfully loaded {loaded_count} out of {len(service_groups)} service groups from '{file}'")

    except Exception as e:
        typer.echo(f"Error loading service groups: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("service-group")
def set_service_group(
    folder: str = typer.Option(..., "--folder", help="Folder path for the service group"),
    name: str = typer.Option(..., "--name", help="Name of the service group"),
    members: str = typer.Option(..., "--members", help="Comma-separated list of service or service group names"),
    tag: str = typer.Option(None, "--tag", help="Comma-separated list of tags"),
) -> None:
    """Create or update a service group."""
    try:
        # Parse members
        member_list = [m.strip() for m in members.split(",") if m.strip()]
        if not member_list:
            typer.echo("Error: At least one member must be provided", err=True)
            raise typer.Exit(code=1)

        # Parse tags if provided
        tag_list = None
        if tag:
            tag_list = [t.strip() for t in tag.split(",") if t.strip()]

        # Validate using Pydantic model
        service_group_data: dict[str, Any] = {
            "folder": folder,
            "name": name,
            "members": member_list,
        }

        if tag_list:
            service_group_data["tag"] = tag_list

        service_group = ServiceGroup(**service_group_data)

        # Create the service group using SDK
        result = scm_client.create_service_group(
            folder=service_group.folder,
            name=service_group.name,
            members=service_group.members,
            tag=service_group.tag,
        )

        if result:
            typer.echo(f"Created service group: {name} in folder {folder}")
        else:
            typer.echo(f"Failed to create/update service group '{name}'", err=True)
            raise typer.Exit(code=1)

    except ValueError as e:
        typer.echo(f"Validation error: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating service group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("service-group")
def show_service_group(
    folder: str = typer.Option(..., "--folder", help="Folder path for the service group"),
    name: str = typer.Option(None, "--name", help="Name of specific service group to show"),
    list: bool = typer.Option(False, "--list", help="List all service groups in the folder"),
) -> dict[str, Any] | None:
    """Show service group details or list all service groups in a folder.

    Examples
    --------
        # List all service groups in a folder (default behavior)
        scm show object service-group --folder Texas

        # Show a specific service group by name
        scm show object service-group --folder Texas --name web-services

    """
    try:
        if list:
            # List all service groups in the folder (default behavior)
            service_groups = scm_client.list_service_groups(folder=folder)
            if not service_groups:
                typer.echo(f"No service groups found in folder '{folder}'")
                return None

            typer.echo(f"Service groups in folder '{folder}':")
            typer.echo("-" * 80)

            # Display in table format
            for group in service_groups:
                typer.echo(f"Name: {group['name']}")
                typer.echo(f"  Members ({len(group.get('members', []))}): {', '.join(group.get('members', []))}")
                if group.get("tag"):
                    typer.echo(f"  Tags: {', '.join(group['tag'])}")
                typer.echo("")

            typer.echo(f"Total: {len(service_groups)} service groups")
            return None

        elif name:
            # Show specific service group
            service_group = scm_client.get_service_group(folder=folder, name=name)

            typer.echo(f"Service Group: {service_group['name']}")
            typer.echo("-" * 80)
            typer.echo(f"Folder: {service_group['folder']}")

            # Display members
            members = service_group.get("members", [])
            typer.echo(f"\nMembers ({len(members)}):")
            for member in members:
                typer.echo(f"  - {member}")

            if service_group.get("tag"):
                typer.echo(f"\nTags: {', '.join(service_group['tag'])}")

            # Display ID if present
            if service_group.get("id"):
                typer.echo(f"\nID: {service_group['id']}")

            return service_group

        else:
            # Neither --list nor --name was provided
            typer.echo("Error: Either --list or --name must be specified", err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"Error showing service group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# SYSLOG SERVER PROFILE COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("syslog-server-profile", help="Export syslog server profiles to a YAML file.")
def backup_syslog_server_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export syslog server profiles from a specified location to a YAML file.

    Examples
    --------
        # Backup from a folder
        scm backup object syslog-server-profile --folder Austin

        # Backup with custom output file
        scm backup object syslog-server-profile --folder Austin --file syslog-profiles.yaml

    """
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # List all syslog server profiles based on location type
        typer.echo(f"Retrieving syslog server profiles from {location_type} '{location_value}'...")

        # Build kwargs based on location type
        kwargs = {location_type: location_value}
        profiles = scm_client.list_syslog_server_profiles(**kwargs)

        if not profiles:
            typer.echo(
                f"No syslog server profiles found in {location_type} '{location_value}'",
                err=True,
            )
            return

        # Prepare data for export
        export_data = {"syslog_server_profiles": profiles}

        # Generate filename if not provided
        filename = Path(file or get_default_backup_filename("syslog-server-profile", location_type, location_value))

        # Write to file
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(profiles)} syslog server profiles to {filename}")

    except Exception as e:
        typer.echo(f"Error backing up syslog server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("syslog-server-profile", help="Delete a syslog server profile.")
def delete_syslog_server_profile(
    name: str = typer.Argument(..., help="Name of the syslog server profile to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a syslog server profile."""
    try:
        # Use the imported scm_client

        # Determine container location
        if not any([folder, snippet, device]):
            folder = "Texas"  # Default to Texas folder

        # Retrieve the profile first to confirm it exists
        profile = scm_client.get_syslog_server_profile(
            name=name,
            folder=folder,
            snippet=snippet,
            device=device,
        )

        if not profile:
            typer.echo(f"Syslog server profile '{name}' not found", err=True)
            raise typer.Exit(code=1)

        # Confirm deletion
        if not force:
            confirm = typer.confirm(f"Are you sure you want to delete syslog server profile '{name}'?")
            if not confirm:
                typer.echo("Deletion cancelled")
                raise typer.Exit(code=0)

        # Delete the profile
        scm_client.delete_syslog_server_profile(
            name=name,
            folder=folder,
            snippet=snippet,
            device=device,
        )

        container = folder or snippet or device
        typer.echo(f"Deleted syslog server profile: {name} from {container}")

    except Exception as e:
        typer.echo(f"❌ Error deleting syslog server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("syslog-server-profile", help="Load syslog server profiles from a YAML file.")
def load_syslog_server_profile(
    file: Path = FILE_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load syslog server profiles from a YAML file."""
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # Validate the file exists
        if not file.exists():
            typer.echo(f"Error: File '{file}' does not exist", err=True)
            raise typer.Exit(code=1)

        # Load YAML content
        with file.open() as f:
            yaml_content = yaml.safe_load(f)

        if not yaml_content:
            typer.echo(f"Error: File '{file}' is empty or invalid", err=True)
            raise typer.Exit(code=1)

        # Extract syslog server profiles from YAML
        syslog_server_profiles = yaml_content.get("syslog_server_profiles", [])
        if not syslog_server_profiles:
            typer.echo("No syslog server profiles found in the YAML file.")
            return

        if dry_run:
            typer.echo("[DRY RUN] Would load the following syslog server profiles:")

        results: list[dict[str, Any]] = []
        loaded_count = 0

        for idx, profile_data in enumerate(syslog_server_profiles, 1):
            try:
                # Override container if specified in command line
                if location_value:
                    profile_data[location_type] = location_value
                    # Remove other container fields
                    for container in ["folder", "snippet", "device"]:
                        if container != location_type and container in profile_data:
                            del profile_data[container]

                # Validate with Pydantic model
                profile = SyslogServerProfile(**profile_data)

                if dry_run:
                    typer.echo(f"\n[{idx}] Syslog Server Profile: {profile.name}")
                    typer.echo(f"  Container: {getattr(profile, location_type or 'folder')}")
                    if profile.description:
                        typer.echo(f"  Description: {profile.description}")
                    if profile.server:
                        typer.echo(f"  Servers: {len(profile.server)}")
                        for server_idx, server in enumerate(profile.server):
                            typer.echo(
                                f"    Server {server_idx + 1}: {server.get('name', 'unnamed')} - {server.get('server', 'N/A')}:{server.get('port', 'N/A')} ({server.get('transport', 'N/A')})"
                            )
                    if profile.tag:
                        typer.echo(f"  Tags: {', '.join(profile.tag)}")
                    results.append({"action": "would create/update", "name": profile.name})
                else:
                    # Convert to SDK format
                    sdk_data = profile.to_sdk_model()

                    # Create/update the profile
                    scm_client.create_syslog_server_profile(sdk_data)

                    typer.echo(f"✓ Loaded syslog server profile: {profile.name}")
                    loaded_count += 1
                    results.append(
                        {
                            "action": "created/updated",
                            "name": profile.name,
                            "result": sdk_data,
                        }
                    )

            except Exception as e:
                typer.echo(
                    f"✗ Error with syslog server profile '{profile_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                results.append(
                    {
                        "action": "error",
                        "name": profile_data.get("name", "unknown"),
                        "error": str(e),
                    }
                )
                continue

        # Summary
        if dry_run:
            typer.echo(f"\n[DRY RUN] Would load {len(syslog_server_profiles)} syslog server profiles from '{file}'")
        else:
            typer.echo(f"\nSuccessfully loaded {loaded_count} out of {len(syslog_server_profiles)} syslog server profiles from '{file}'")

    except Exception as e:
        typer.echo(f"Error loading syslog server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("syslog-server-profile", help="Create or update a syslog server profile.")
def set_syslog_server_profile(
    name: str = typer.Argument(..., help="Name of the syslog server profile"),
    server_name: str = typer.Option(..., "--server-name", help="Name of the syslog server"),
    server_address: str = typer.Option(..., "--server-address", help="IP address or hostname of syslog server"),
    transport: str = typer.Option(..., "--transport", help="Transport protocol (UDP, TCP, SSL)"),
    port: int = typer.Option(..., "--port", help="Port number (1-65535)"),
    format: str = typer.Option(..., "--format", help="Log format (BSD, IETF)"),
    facility: str = typer.Option(..., "--facility", help="Syslog facility (LOG_USER, LOG_LOCAL0-7)"),
    description: str = DESCRIPTION_OPTION,
    folder: str = FOLDER_OPTION,
    snippet: str = SNIPPET_OPTION,
    device: str = DEVICE_OPTION,
    tag: list[str] = TAG_OPTION,
) -> None:
    """Create or update a syslog server profile."""
    try:
        # Use the imported scm_client

        # Determine container location
        if not any([folder, snippet, device]):
            folder = "Texas"  # Default to Texas folder

        # Build syslog server profile data
        profile_data: dict[str, Any] = {
            "name": name,
            "server": [
                {
                    "name": server_name,
                    "server": server_address,
                    "transport": transport,
                    "port": port,
                    "format": format,
                    "facility": facility,
                }
            ],
        }

        # Add container
        if folder:
            profile_data["folder"] = folder
        elif snippet:
            profile_data["snippet"] = snippet
        elif device:
            profile_data["device"] = device

        # Add optional fields
        if description:
            profile_data["description"] = description
        if tag:
            profile_data["tag"] = tag

        # Validate with Pydantic model
        validated_profile = SyslogServerProfile(**profile_data)

        # Convert to SDK format
        sdk_data = validated_profile.to_sdk_model()

        # Create/update the profile
        scm_client.create_syslog_server_profile(sdk_data)

        container = folder or snippet or device
        typer.echo(f"Created syslog server profile: {name} in {container}")

    except Exception as e:
        typer.echo(f"❌ Error creating/updating syslog server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("syslog-server-profile", help="Show syslog server profile details.")
def show_syslog_server_profile(
    name: str = typer.Option(None, "--name", help="Name of specific syslog server profile to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show syslog server profile details.

    Examples
    --------
        # List all syslog server profiles (default behavior)
        scm show object syslog-server-profile

        # Show a specific syslog server profile by name
        scm show object syslog-server-profile --name primary-syslog

    """
    try:
        # Use the imported scm_client

        # Determine container location
        if not any([folder, snippet, device]):
            folder = "Texas"  # Default to Texas folder

        if name:
            # Show specific syslog server profile
            profile = scm_client.get_syslog_server_profile(
                name=name,
                folder=folder,
                snippet=snippet,
                device=device,
            )

            if not profile:
                typer.echo(f"Syslog server profile '{name}' not found", err=True)
                raise typer.Exit(code=1)

            # Display detailed information
            typer.echo(f"\nSyslog Server Profile: {profile['name']}")
            typer.echo("=" * 50)

            location = profile.get("folder") or profile.get("snippet") or profile.get("device", "N/A")
            typer.echo(f"Location: {location}")

            if profile.get("description"):
                typer.echo(f"Description: {profile['description']}")

            # Display servers
            servers = profile.get("server", [])
            typer.echo(f"\nServers ({len(servers)}):")
            for server in servers:
                typer.echo(f"\n  Server: {server['name']}")
                typer.echo(f"    Address: {server['server']}")
                typer.echo(f"    Transport: {server['transport']}")
                typer.echo(f"    Port: {server['port']}")
                typer.echo(f"    Format: {server['format']}")
                typer.echo(f"    Facility: {server['facility']}")

            # Display format settings if present
            if profile.get("format"):
                typer.echo("\nFormat Settings:")
                for key, value in profile["format"].items():
                    typer.echo(f"  {key}: {value}")

            if profile.get("tag"):
                typer.echo(f"\nTags: {', '.join(profile['tag'])}")

            # Display ID if present
            if profile.get("id"):
                typer.echo(f"\nID: {profile['id']}")

            return profile

        else:
            # Default behavior: list all syslog server profiles
            profiles = scm_client.list_syslog_server_profiles(
                folder=folder,
                snippet=snippet,
                device=device,
            )

            if not profiles:
                typer.echo("No syslog server profiles found")
                return

            # Display in table format
            typer.echo("\nSyslog Server Profiles:")
            typer.echo("-" * 100)

            for profile in profiles:
                location = profile.get("folder") or profile.get("snippet") or profile.get("device", "N/A")
                servers = profile.get("server", [])
                server_count = len(servers)

                typer.echo(f"\nName: {profile['name']}")
                typer.echo(f"Location: {location}")
                if profile.get("description"):
                    typer.echo(f"Description: {profile['description']}")
                typer.echo(f"Servers: {server_count}")

                # Show server details
                for server in servers:
                    typer.echo(f"  - {server['name']}: {server['server']}:{server['port']} ({server['transport']}) - {server['format']}/{server['facility']}")

                if profile.get("tag"):
                    typer.echo(f"Tags: {', '.join(profile['tag'])}")

            typer.echo(f"\nTotal: {len(profiles)} syslog server profiles")

    except Exception as e:
        typer.echo(f"Error showing syslog server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# TAG COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("tag", help="Export tags to a YAML file.")
def backup_tag(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export tags from a specified location to a YAML file.

    Examples
    --------
        # Backup from a folder
        scm backup object tag --folder Austin

        # Backup with custom output file
        scm backup object tag --folder Austin --file tags.yaml

    """
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # List all tags based on location type
        typer.echo(f"Retrieving tags from {location_type} '{location_value}'...")

        # Build kwargs based on location type
        kwargs = {location_type: location_value}
        tags = scm_client.list_tags(**kwargs)

        if not tags:
            typer.echo(f"No tags found in {location_type} '{location_value}'", err=True)
            return

        # Prepare data for export
        export_data = {"tags": tags}

        # Generate filename if not provided
        filename = Path(file or get_default_backup_filename("tag", location_type, location_value))

        # Write to file
        filename.parent.mkdir(parents=True, exist_ok=True)
        with filename.open("w") as f:
            yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(tags)} tags to {filename}")

    except Exception as e:
        typer.echo(f"Error backing up tags: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("tag", help="Delete a tag.")
def delete_tag(
    name: str = typer.Argument(..., help="Name of the tag to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a tag."""
    try:
        # Determine container location
        if not any([folder, snippet, device]):
            folder = "Texas"  # Default to Texas folder

        # Retrieve the tag first to confirm it exists
        tag = scm_client.get_tag(
            name=name,
            folder=folder,
            snippet=snippet,
            device=device,
        )

        if not tag:
            typer.echo(f"Tag '{name}' not found", err=True)
            raise typer.Exit(code=1)

        # Confirm deletion
        if not force:
            confirm = typer.confirm(f"Are you sure you want to delete tag '{name}'?")
            if not confirm:
                typer.echo("Deletion cancelled")
                raise typer.Exit(code=0)

        # Delete the tag
        scm_client.delete_tag(
            name=name,
            folder=folder,
            snippet=snippet,
            device=device,
        )

        container = folder or snippet or device
        typer.echo(f"Deleted tag: {name} from {container}")

    except Exception as e:
        typer.echo(f"❌ Error deleting tag: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("tag", help="Load tags from a YAML file.")
def load_tag(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
) -> None:
    """Load tags from a YAML file."""
    try:
        # Validate file exists
        if not Path(file).exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)

        # Load YAML data
        with Path(file).open() as f:
            data = yaml.safe_load(f)

        if not data or "tags" not in data:
            typer.echo("No tags found in file", err=True)
            raise typer.Exit(code=1)

        tags = data["tags"]
        if not isinstance(tags, list):
            tags = [tags]

        # Process each tag
        created_count = 0
        for tag_data in tags:
            try:
                # Validate with Pydantic model
                validated_tag = Tag(**tag_data)

                # Override container if specified
                if folder:
                    validated_tag.folder = folder
                    validated_tag.snippet = None
                    validated_tag.device = None
                elif snippet:
                    validated_tag.snippet = snippet
                    validated_tag.folder = None
                    validated_tag.device = None
                elif device:
                    validated_tag.device = device
                    validated_tag.folder = None
                    validated_tag.snippet = None

                # Convert to SDK format
                sdk_data = validated_tag.to_sdk_model()

                # Create/update the tag
                scm_client.create_tag(sdk_data)

                created_count += 1

                container = validated_tag.folder or validated_tag.snippet or validated_tag.device
                typer.echo(f"Created tag: {validated_tag.name} in {container}")

            except Exception as e:
                typer.echo(f"❌ Error processing tag: {str(e)}", err=True)
                continue

        typer.echo(f"\n✅ Summary: Processed {created_count} tags")

    except Exception as e:
        typer.echo(f"❌ Error loading tags: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("tag", help="Create or update a tag.")
def set_tag(
    name: str = typer.Argument(..., help="Name of the tag"),
    color: str = typer.Option(None, "--color", help="Color for the tag (e.g., Red, Blue, Green)"),
    comments: str = typer.Option(None, "--comments", help="Comments for the tag"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Create or update a tag."""
    try:
        # Determine container location
        if not any([folder, snippet, device]):
            folder = "Texas"  # Default to Texas folder

        # Build tag data
        tag_data = {
            "name": name,
        }

        # Add container
        if folder:
            tag_data["folder"] = folder
        elif snippet:
            tag_data["snippet"] = snippet
        elif device:
            tag_data["device"] = device

        # Add optional fields
        if color:
            tag_data["color"] = color
        if comments:
            tag_data["comments"] = comments

        # Validate with Pydantic model
        validated_tag = Tag(**tag_data)

        # Convert to SDK format
        sdk_data = validated_tag.to_sdk_model()

        # Create/update the tag
        result = scm_client.create_tag(sdk_data)

        # Get the action performed
        action = result.pop("__action__", "created")

        container = folder or snippet or device
        if action == "created":
            typer.echo(f"✅ Created tag: {name} in {container}")
        elif action == "updated":
            typer.echo(f"✅ Updated tag: {name} in {container}")
        elif action == "no_change":
            typer.echo(f"ℹ️  No changes needed for tag: {name} in {container}")

    except Exception as e:
        typer.echo(f"❌ Error creating/updating tag: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("tag", help="Show tag details.")
def show_tag(
    name: str = typer.Option(None, "--name", help="Name of specific tag to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Show tag details.

    Examples
    --------
        # List all tags (default behavior)
        scm show object tag

        # Show a specific tag by name
        scm show object tag --name Production

    """
    try:
        # Determine container location
        if not any([folder, snippet, device]):
            folder = "Texas"  # Default to Texas folder

        if name:
            # Show specific tag
            tag = scm_client.get_tag(
                name=name,
                folder=folder,
                snippet=snippet,
                device=device,
            )

            if not tag:
                typer.echo(f"Tag '{name}' not found", err=True)
                raise typer.Exit(code=1)

            # Display detailed information
            typer.echo(f"\nTag: {tag['name']}")
            typer.echo("=" * 40)

            location = tag.get("folder") or tag.get("snippet") or tag.get("device", "N/A")
            typer.echo(f"Location: {location}")

            if tag.get("color"):
                typer.echo(f"Color: {tag['color']}")

            if tag.get("comments"):
                typer.echo(f"Comments: {tag['comments']}")

            # Display ID if present
            if tag.get("id"):
                typer.echo(f"\nID: {tag['id']}")

            return tag

        else:
            # Default behavior: list all tags
            tags = scm_client.list_tags(
                folder=folder,
                snippet=snippet,
                device=device,
            )

            if not tags:
                typer.echo("No tags found")
                return

            # Display in table format
            typer.echo("\nTags:")
            typer.echo("-" * 80)

            for tag in tags:
                location = tag.get("folder") or tag.get("snippet") or tag.get("device", "N/A")
                color = tag.get("color", "No color")

                typer.echo(f"\nName: {tag['name']}")
                typer.echo(f"Location: {location}")
                typer.echo(f"Color: {color}")
                if tag.get("comments"):
                    typer.echo(f"Comments: {tag['comments']}")

            typer.echo(f"\nTotal: {len(tags)} tags")

    except Exception as e:
        typer.echo(f"Error showing tag: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
