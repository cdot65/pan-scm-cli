"""Objects module commands for scm.

This module implements set, delete, and load commands for objects-related
configurations such as address-group, address, service-group, etc.
"""

from pathlib import Path
from typing import Any

import typer
import yaml

# Removed unused import: from the `..utils.config` import load_from_yaml
from ..utils import parse_comma_separated_list, validate_location_params
from ..utils.config import settings
from ..utils.context import get_current_context
from ..utils.decorators import handle_command_errors
from ..utils.output import OUTPUT_OPTION, OutputFormat, emit, error, info, redact, success, warning
from ..utils.sdk_client import scm_client
from ..utils.validators import (
    Address,
    AddressGroup,
    Application,
    ApplicationFilter,
    ApplicationGroup,
    AutoTagAction,
    DynamicUserGroup,
    ExternalDynamicList,
    HIPObject,
    HIPProfile,
    HTTPServerProfile,
    LogForwardingProfile,
    QuarantinedDevice,
    Region,
    Schedule,
    Service,
    ServiceGroup,
    SyslogServerProfile,
    Tag,
)

# =============================================================================================================================================================================================
# HELPER FUNCTIONS
# =============================================================================================================================================================================================


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


# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

# Create app groups for each action type
set_app = typer.Typer(help="Create or update object configurations")
delete_app = typer.Typer(help="Remove object configurations")
load_app = typer.Typer(help="Load object configurations from YAML files")
show_app = typer.Typer(help="Display object configurations")
backup_app = typer.Typer(help="Backup object configurations to YAML files")

# =============================================================================================================================================================================================
# COMMAND OPTIONS
# =============================================================================================================================================================================================

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
EXCLUDE_FOLDER_OPTION = typer.Option(
    None,
    "--exclude-folder",
    help="Folder(s) to exclude from results",
)
EXCLUDE_SNIPPET_OPTION = typer.Option(
    None,
    "--exclude-snippet",
    help="Snippet(s) to exclude from results",
)
EXCLUDE_DEVICE_OPTION = typer.Option(
    None,
    "--exclude-device",
    help="Device(s) to exclude from results",
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

REGION_ADDRESSES_OPTION = typer.Option(
    None,
    "--address",
    help="Address CIDRs for the region",
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

# Schedule-specific options
SCHEDULE_TIME_RANGE_OPTION = typer.Option(
    None,
    "--time-range",
    help="Time ranges (e.g., 09:00-17:00 for daily, YYYY/MM/DD@HH:MM-YYYY/MM/DD@HH:MM for non-recurring)",
)
SCHEDULE_MONDAY_OPTION = typer.Option(None, "--monday", help="Time ranges for Monday (weekly only)")
SCHEDULE_TUESDAY_OPTION = typer.Option(None, "--tuesday", help="Time ranges for Tuesday (weekly only)")
SCHEDULE_WEDNESDAY_OPTION = typer.Option(None, "--wednesday", help="Time ranges for Wednesday (weekly only)")
SCHEDULE_THURSDAY_OPTION = typer.Option(None, "--thursday", help="Time ranges for Thursday (weekly only)")
SCHEDULE_FRIDAY_OPTION = typer.Option(None, "--friday", help="Time ranges for Friday (weekly only)")
SCHEDULE_SATURDAY_OPTION = typer.Option(None, "--saturday", help="Time ranges for Saturday (weekly only)")
SCHEDULE_SUNDAY_OPTION = typer.Option(None, "--sunday", help="Time ranges for Sunday (weekly only)")

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

# =============================================================================================================================================================================================
# HELPER FUNCTIONS
# =============================================================================================================================================================================================


def get_default_backup_filename(object_type: str, location_type: str, location_value: str) -> str:
    """Generate default backup filename based on object type and location."""
    # Sanitize location value for filename
    safe_location = location_value.lower().replace("/", "-").replace(" ", "-")
    return f"{object_type}-{safe_location}.yaml"


# =============================================================================================================================================================================================
# ADDRESS GROUP COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("address-group")
@handle_command_errors("backing up address groups")
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
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # List all address groups in the location with exact_match=True
    kwargs = {location_type: location_value}
    groups = scm_client.list_address_groups(**kwargs, exact_match=True)

    if not groups:
        info(f"No address groups found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(backup_data)} address groups to {file}")
    return str(file)


@delete_app.command("address-group")
@handle_command_errors("deleting address group")
def delete_address_group(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete an address group.

    Examples
    --------
        scm delete object address-group --folder Texas --name test123

    """
    if not force:
        confirm = typer.confirm(f"Delete address group '{name}' from folder '{folder}'?")
        if not confirm:
            raise typer.Abort()
    result = scm_client.delete_address_group(folder=folder, name=name)
    if result:
        success(f"Deleted address group: {name} from folder {folder}")
    return result


@load_app.command("address-group", help="Load address groups from a YAML file.")
@handle_command_errors("loading address groups")
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
    # Validate file exists
    if not file.exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)

    # Additionally load raw data for potential manipulation
    with file.open() as f:
        raw_data = yaml.safe_load(f)

    if not raw_data or "address_groups" not in raw_data:
        error("No address groups found in file")
        raise typer.Exit(code=1)

    address_groups = raw_data["address_groups"]
    if not isinstance(address_groups, list):
        address_groups = [address_groups]

    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        # Show override information if applicable
        if folder or snippet or device:
            info(f"Container override: {folder or snippet or device}")
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
                warning(f"Warning: Address groups do not support snippets. Skipping group '{ag_data.get('name', 'unknown')}'")
                continue
            elif device:
                warning(f"Warning: Address groups do not support devices. Skipping group '{ag_data.get('name', 'unknown')}'")
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
            error(f"Error processing address group '{ag_data.get('name', 'unknown')}': {str(e)}")
            # Continue processing other objects
            continue

    # Display summary with counts
    success(f"Successfully processed {len(results)} address group(s):")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")


@set_app.command("address-group")
@handle_command_errors("creating address group")
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
    # Parse comma-separated list options
    parsed_members = parse_comma_separated_list(members) if members else []
    parsed_tags = parse_comma_separated_list(tags) if tags else []

    # Validate inputs using the Pydantic model
    address_group = AddressGroup(
        folder=folder,
        name=name,
        type=type,
        members=parsed_members,
        filter=filter,
        description=description or "",
        tags=parsed_tags,
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

    action = result.pop("__action__", "created")
    if action == "updated":
        success(f"Updated address group: {result['name']} in folder {result['folder']}")
    else:
        success(f"Created address group: {result['name']} in folder {result['folder']}")
    return result


@show_app.command("address-group")
@handle_command_errors("showing address group")
def show_address_group(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the address group to show"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display address group objects.

    Examples
    --------
        # List all address groups in a folder (default behavior)
        scm show object address-group --folder Texas

        # Show a specific address group by name
        scm show object address-group --folder Texas --name web-servers

    """
    if name:
        # Get a specific address group by name
        group = scm_client.get_address_group(folder=folder, name=name)
        emit(group, output, title=f"Address Group: {group.get('name', name)}")
        return group

    # Default behavior: list all address groups in the folder
    groups = scm_client.list_address_groups(folder=folder)
    emit(
        groups,
        output,
        columns=["name", "folder", "static", "dynamic", "description", "tag"],
        title=f"Address Groups in folder '{folder}'",
    )
    return groups or None


# =============================================================================================================================================================================================
# ADDRESS OBJECT COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("address")
@handle_command_errors("backing up addresses")
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
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # List all addresses in the location with exact_match=True
    kwargs = {location_type: location_value}
    addresses = scm_client.list_addresses(**kwargs, exact_match=True)

    if not addresses:
        info(f"No addresses found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(backup_data)} addresses to {file}")
    return str(file)


@delete_app.command("address")
@handle_command_errors("deleting address")
def delete_address(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete an address object.

    Examples
    --------
        scm delete object address --folder Texas --name webserver

    """
    if not force:
        confirm = typer.confirm(f"Delete address '{name}' from folder '{folder}'?")
        if not confirm:
            raise typer.Abort()
    result = scm_client.delete_address(folder=folder, name=name)
    if result:
        success(f"Deleted address: {name} from folder {folder}")
    return result


@load_app.command("address", help="Load addresses from a YAML file.")
@handle_command_errors("loading addresses")
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
    # Validate container override parameters
    if sum(1 for x in [folder, snippet, device] if x is not None) > 1:
        error("Error: Only one of --folder, --snippet, or --device can be specified")
        raise typer.Exit(code=1)

    # Validate file exists
    if not file.exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)

    # Load YAML data using the same pattern as other commands
    with open(file) as f:
        raw_data = yaml.safe_load(f)

    if not raw_data or "addresses" not in raw_data:
        error("No addresses found in file")
        raise typer.Exit(code=1)

    addresses = raw_data["addresses"]
    if not isinstance(addresses, list):
        addresses = [addresses]

    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        # Show override information if applicable
        if folder or snippet or device:
            override_type = "folder" if folder else ("snippet" if snippet else "device")
            override_value = folder or snippet or device
            info(f"Container override: {override_type} = '{override_value}'")
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
            error(f"Error processing address '{addr_data.get('name', 'unknown')}': {str(e)}")
            # Continue processing other addresses
            continue

    # Display summary with counts
    success(f"Successfully processed {len(results)} address(es):")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")


@set_app.command("address")
@handle_command_errors("creating address")
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
        success(f"Created address: {result['name']} in folder {result['folder']}")
    elif action == "updated":
        success(f"Updated address: {result['name']} in folder {result['folder']}")
    elif action == "no_change":
        info(f"No changes needed for address: {result['name']} in folder {result['folder']}")

    return result


@show_app.command("address")
@handle_command_errors("showing address")
def show_address(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the address to show"),
    exclude_folder: list[str] | None = EXCLUDE_FOLDER_OPTION,
    exclude_snippet: list[str] | None = EXCLUDE_SNIPPET_OPTION,
    exclude_device: list[str] | None = EXCLUDE_DEVICE_OPTION,
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display address objects.

    Example:
    -------
        # List all addresses in a folder (default behavior)
        scm show object address --folder Texas

        # Show a specific address by name
        scm show object address --folder Texas --name webserver

        # List addresses excluding specific folders
        scm show object address --folder Texas --exclude-folder "All"

    """
    # Show context info if log level is INFO
    show_context_info()

    if name:
        # Get a specific address by name
        address = scm_client.get_address(folder=folder, name=name)
        emit(address, output, title=f"Address: {address.get('name', name)}")
        return address

    # Default behavior: list all addresses in the folder
    addresses = scm_client.list_addresses(
        folder=folder,
        exclude_folders=exclude_folder or None,
        exclude_snippets=exclude_snippet or None,
        exclude_devices=exclude_device or None,
    )
    emit(
        addresses,
        output,
        columns=["name", "folder", "ip_netmask", "ip_range", "ip_wildcard", "fqdn", "description", "tag"],
        title=f"Addresses in folder '{folder}'",
    )
    return addresses or None


# =============================================================================================================================================================================================
# APPLICATION COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("application")
@handle_command_errors("backing up applications")
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
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # List all applications in the location with exact_match=True
    kwargs = {location_type: location_value}
    applications = scm_client.list_applications(**kwargs, exact_match=True)

    if not applications:
        info(f"No applications found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(backup_data)} applications to {file}")
    return str(file)


@delete_app.command("application")
@handle_command_errors("deleting application")
def delete_application(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete an application.

    Example:
    -------
    scm delete object application --folder Texas --name custom-app

    """
    if not force:
        confirm = typer.confirm(f"Delete application '{name}' from folder '{folder}'?")
        if not confirm:
            raise typer.Abort()
    result = scm_client.delete_application(folder=folder, name=name)
    if result:
        success(f"Deleted application: {name} from folder {folder}")
    return result


@load_app.command("application", help="Load applications from a YAML file.")
@handle_command_errors("loading applications")
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
    # Validate file exists
    if not file.exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)

    # Additionally load raw data for potential manipulation
    with file.open() as f:
        raw_data = yaml.safe_load(f)

    if not raw_data or "applications" not in raw_data:
        error("No applications found in file")
        raise typer.Exit(code=1)

    applications = raw_data["applications"]
    if not isinstance(applications, list):
        applications = [applications]

    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        # Show override information if applicable
        if folder or snippet or device:
            info(f"Container override: {folder or snippet or device}")
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
                warning(f"Warning: Applications do not support snippets. Skipping application '{app_data.get('name', 'unknown')}'")
                continue
            elif device:
                warning(f"Warning: Applications do not support devices. Skipping application '{app_data.get('name', 'unknown')}'")
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
            error(f"Error processing application '{app_data.get('name', 'unknown')}': {str(e)}")
            # Continue processing other objects
            continue

    # Display summary with counts
    success(f"Successfully processed {len(results)} application(s):")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")


@set_app.command("application")
@handle_command_errors("creating application")
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

    action = result.pop("__action__", "created")
    if action == "updated":
        success(f"Updated application: {result['name']} in folder {result['folder']}")
    else:
        success(f"Created application: {result['name']} in folder {result['folder']}")
    return result


@show_app.command("application")
@handle_command_errors("showing application")
def show_application(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the application to show"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display application objects.

    Examples
    --------
        # List all applications in a folder (default behavior)
        scm show object application --folder Texas

        # Show a specific application by name
        scm show object application --folder Texas --name custom-database

    """
    if name:
        # Get a specific application by name
        application = scm_client.get_application(folder=folder, name=name)
        emit(application, output, title=f"Application: {application.get('name', name)}")
        return application

    # List all applications in the folder (default behavior)
    applications = scm_client.list_applications(folder=folder)
    emit(
        applications,
        output,
        columns=["name", "folder", "category", "subcategory", "technology", "risk", "description"],
        title=f"Applications in folder '{folder}'",
    )
    return applications or None


# =============================================================================================================================================================================================
# APPLICATION GROUP COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("application-group")
@handle_command_errors("backing up application groups")
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
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # List all application groups in the location with exact_match=True
    kwargs = {location_type: location_value}
    groups = scm_client.list_application_groups(**kwargs, exact_match=True)

    if not groups:
        info(f"No application groups found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(backup_data)} application groups to {file}")
    return str(file)


@delete_app.command("application-group")
@handle_command_errors("deleting application group")
def delete_application_group(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete an application group.

    Example:
    -------
    scm delete object application-group --folder Texas --name web-apps

    """
    if not force:
        confirm = typer.confirm(f"Delete application group '{name}' from folder '{folder}'?")
        if not confirm:
            raise typer.Abort()
    result = scm_client.delete_application_group(folder=folder, name=name)
    if result:
        success(f"Deleted application group: {name} from folder {folder}")
    return result


@load_app.command("application-group", help="Load application groups from a YAML file.")
@handle_command_errors("loading application groups")
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
    # Validate container override parameters
    validate_location_params(folder, snippet, device)

    # Validate file exists
    if not file.exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)

    # Load YAML data
    with file.open() as f:
        data = yaml.safe_load(f)

    if not data or "application_groups" not in data:
        error("No application groups found in file")
        raise typer.Exit(code=1)

    application_groups = data["application_groups"]
    if not isinstance(application_groups, list):
        application_groups = [application_groups]

    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        if folder or snippet or device:
            info(f"Container override: {folder or snippet or device}")
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
            error(f"Error processing application group '{group_data.get('name', 'unknown')}': {str(e)}")
            continue

    # Display summary with counts
    success(f"Successfully processed {len(results)} application group(s)")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")


@set_app.command("application-group")
@handle_command_errors("creating application group")
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
    # Parse comma-separated members
    parsed_members = parse_comma_separated_list(members)

    # Validate inputs using the Pydantic model
    app_group = ApplicationGroup(
        folder=folder,
        name=name,
        members=parsed_members,
    )

    # Call the SDK client to create the application group
    result = scm_client.create_application_group(
        folder=app_group.folder,
        name=app_group.name,
        members=app_group.members,
    )

    action = result.pop("__action__", "created")
    if action == "updated":
        success(f"Updated application group: {result['name']} in folder {result['folder']}")
    else:
        success(f"Created application group: {result['name']} in folder {result['folder']}")
    return result


@show_app.command("application-group")
@handle_command_errors("showing application group")
def show_application_group(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the application group to show"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display application group objects.

    Examples
    --------
        # List all application groups in a folder (default behavior)
        scm show object application-group --folder Texas

        # Show a specific application group by name
        scm show object application-group --folder Texas --name web-apps

    """
    if name:
        # Get a specific application group by name
        group = scm_client.get_application_group(folder=folder, name=name)
        emit(group, output, title=f"Application Group: {group.get('name', name)}")
        return group

    # List all application groups in the folder (default behavior)
    groups = scm_client.list_application_groups(folder=folder)
    emit(
        groups,
        output,
        columns=["name", "folder", "members"],
        title=f"Application Groups in folder '{folder}'",
    )
    return groups or None


# =============================================================================================================================================================================================
# APPLICATION FILTER COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("application-filter")
@handle_command_errors("backing up application filters")
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
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # List all application filters in the location with exact_match=True
    kwargs = {location_type: location_value}
    filters = scm_client.list_application_filters(**kwargs, exact_match=True)

    if not filters:
        info(f"No application filters found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(backup_data)} application filters to {file}")
    return str(file)


@delete_app.command("application-filter")
@handle_command_errors("deleting application filter")
def delete_application_filter(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete an application filter.

    Example:
    -------
    scm delete object application-filter --folder Texas --name high-risk-apps

    """
    if not force:
        confirm = typer.confirm(f"Delete application filter '{name}' from folder '{folder}'?")
        if not confirm:
            raise typer.Abort()
    result = scm_client.delete_application_filter(folder=folder, name=name)
    if result:
        success(f"Deleted application filter: {name} from folder {folder}")
    return result


@load_app.command("application-filter", help="Load application filters from a YAML file.")
@handle_command_errors("loading application filters")
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
    # Validate container override parameters
    validate_location_params(folder, snippet, device)

    # Validate file exists
    if not file.exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)

    # Load YAML data
    with file.open() as f:
        data = yaml.safe_load(f)

    if not data or "application_filters" not in data:
        error("No application filters found in file")
        raise typer.Exit(code=1)

    application_filters = data["application_filters"]
    if not isinstance(application_filters, list):
        application_filters = [application_filters]

    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        if folder or snippet or device:
            info(f"Container override: {folder or snippet or device}")
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
            error(f"Error processing application filter '{filter_data.get('name', 'unknown')}': {str(e)}")
            continue

    # Display summary with counts
    success(f"Successfully processed {len(results)} application filter(s)")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")


@set_app.command("application-filter")
@handle_command_errors("creating application filter")
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

    # Get the action performed
    action = result.pop("__action__", "created")

    if action == "created":
        success(f"Created application filter: {result['name']} in folder {result['folder']}")
    elif action == "updated":
        success(f"Updated application filter: {result['name']} in folder {result['folder']}")
    elif action == "no_change":
        info(f"No changes needed for application filter: {result['name']} in folder {result['folder']}")

    return result


@show_app.command("application-filter")
@handle_command_errors("showing application filter")
def show_application_filter(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the application filter to show"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display application filter objects.

    Examples
    --------
        # List all application filters in a folder (default behavior)
        scm show object application-filter --folder Texas

        # Show a specific application filter by name
        scm show object application-filter --folder Texas --name high-risk-apps

    """
    if name:
        # Get a specific application filter by name
        filter_obj = scm_client.get_application_filter(folder=folder, name=name)
        emit(filter_obj, output, title=f"Application Filter: {filter_obj.get('name', name)}")
        return filter_obj

    # List all application filters in the folder (default behavior)
    filters = scm_client.list_application_filters(folder=folder)
    emit(
        filters,
        output,
        columns=["name", "folder", "category", "sub_category", "technology", "risk"],
        title=f"Application Filters in folder '{folder}'",
    )
    return filters or None


# =============================================================================================================================================================================================
# DYNAMIC USER GROUP COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("dynamic-user-group")
@handle_command_errors("backing up dynamic user groups")
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
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # List all dynamic user groups in the location with exact_match=True
    kwargs = {location_type: location_value}
    groups = scm_client.list_dynamic_user_groups(**kwargs, exact_match=True)

    if not groups:
        info(f"No dynamic user groups found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(backup_data)} dynamic user groups to {file}")
    return str(file)


@delete_app.command("dynamic-user-group")
@handle_command_errors("deleting dynamic user group")
def delete_dynamic_user_group(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a dynamic user group.

    Example:
    -------
    scm delete object dynamic-user-group --folder Texas --name it-admins

    """
    if not force:
        confirm = typer.confirm(f"Delete dynamic user group '{name}' from folder '{folder}'?")
        if not confirm:
            raise typer.Abort()
    result = scm_client.delete_dynamic_user_group(folder=folder, name=name)
    if result:
        success(f"Deleted dynamic user group: {name} from folder {folder}")
    return result


@load_app.command("dynamic-user-group", help="Load dynamic user groups from a YAML file.")
@handle_command_errors("loading dynamic user groups")
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
    # Validate container override parameters
    validate_location_params(folder, snippet, device)

    # Validate file exists
    if not file.exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)

    # Load YAML data
    with file.open() as f:
        data = yaml.safe_load(f)

    if not data or "dynamic_user_groups" not in data:
        error("No dynamic user groups found in file")
        raise typer.Exit(code=1)

    dynamic_user_groups = data["dynamic_user_groups"]
    if not isinstance(dynamic_user_groups, list):
        dynamic_user_groups = [dynamic_user_groups]

    if dry_run:
        info("Dry run mode: would apply the following configurations:")
        if folder or snippet or device:
            info(f"Container override: {folder or snippet or device}")
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
            error(f"Error processing dynamic user group '{group_data.get('name', 'unknown')}': {str(e)}")
            continue

    # Display summary with counts
    success(f"Successfully processed {len(results)} dynamic user group(s)")
    if created_count > 0:
        info(f"  - Created: {created_count}")
    if updated_count > 0:
        info(f"  - Updated: {updated_count}")


@set_app.command("dynamic-user-group")
@handle_command_errors("creating dynamic user group")
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

    action = result.pop("__action__", "created")
    if action == "updated":
        success(f"Updated dynamic user group: {result['name']} in folder {result['folder']}")
    else:
        success(f"Created dynamic user group: {result['name']} in folder {result['folder']}")
    return result


@show_app.command("dynamic-user-group")
@handle_command_errors("showing dynamic user group")
def show_dynamic_user_group(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the dynamic user group to show"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display dynamic user group objects.

    Examples
    --------
        # List all dynamic user groups in a folder (default behavior)
        scm show object dynamic-user-group --folder Texas

        # Show a specific dynamic user group by name
        scm show object dynamic-user-group --folder Texas --name it-admins

    """
    if name:
        # Get a specific dynamic user group by name
        group = scm_client.get_dynamic_user_group(folder=folder, name=name)
        emit(group, output, title=f"Dynamic User Group: {group.get('name', name)}")
        return group

    # List all dynamic user groups in the folder (default behavior)
    groups = scm_client.list_dynamic_user_groups(folder=folder)
    emit(
        groups,
        output,
        columns=["name", "folder", "filter", "description", "tag"],
        title=f"Dynamic User Groups in folder '{folder}'",
    )
    return groups or None


# =============================================================================================================================================================================================
# EXTERNAL DYNAMIC LIST COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("external-dynamic-list")
@handle_command_errors("backing up external dynamic lists")
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
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # List all external dynamic lists in the location with exact_match=True
    kwargs = {location_type: location_value}
    edls = scm_client.list_external_dynamic_lists(**kwargs, exact_match=True)

    if not edls:
        info(f"No external dynamic lists found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(backup_data)} external dynamic lists to {file}")
    return str(file)


@delete_app.command("external-dynamic-list")
@handle_command_errors("deleting external dynamic list")
def delete_external_dynamic_list(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete an external dynamic list.

    Example:
    -------
    scm delete object external-dynamic-list --folder Texas --name malicious-ips

    """
    if not force:
        confirm = typer.confirm(f"Delete external dynamic list '{name}' from folder '{folder}'?")
        if not confirm:
            raise typer.Abort()
    result = scm_client.delete_external_dynamic_list(folder=folder, name=name)
    if result:
        success(f"Deleted external dynamic list: {name} from folder {folder}")
    return result


@load_app.command("external-dynamic-list", help="Load external dynamic lists from a YAML file.")
@handle_command_errors("loading external dynamic lists")
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
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Validate the file exists
    if not file.exists():
        error(f"Error: File '{file}' does not exist")
        raise typer.Exit(code=1)

    # Load YAML content
    with file.open() as f:
        yaml_content = yaml.safe_load(f)

    if not yaml_content:
        error(f"Error: File '{file}' is empty or invalid")
        raise typer.Exit(code=1)

    # Extract external dynamic lists from YAML
    external_dynamic_lists = yaml_content.get("external_dynamic_lists", [])
    if not external_dynamic_lists:
        info("No external dynamic lists found in the YAML file.")
        return

    if dry_run:
        info("[DRY RUN] Would load the following external dynamic lists:")

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
                success(f"Loaded external dynamic list: {edl.name}")
                loaded_count += 1
                results.append(
                    {
                        "action": "created/updated",
                        "name": edl.name,
                        "result": result,
                    }
                )
        except Exception as e:
            error(f"Error with external dynamic list '{edl_config.get('name', 'unknown')}': {str(e)}")
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
        info(f"[DRY RUN] Would load {len(external_dynamic_lists)} external dynamic lists from '{file}'")
    else:
        success(f"Successfully loaded {loaded_count} out of {len(external_dynamic_lists)} external dynamic lists from '{file}'")


@set_app.command("external-dynamic-list")
@handle_command_errors("creating/updating external dynamic list")
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

    # Get the action performed
    action = result.pop("__action__", "created")

    if action == "created":
        success(f"Created external dynamic list: {result.get('name', name)} in folder {result.get('folder', folder)}")
    elif action == "updated":
        success(f"Updated external dynamic list: {result.get('name', name)} in folder {result.get('folder', folder)}")
    elif action == "no_change":
        info(f"No changes needed for external dynamic list: {result.get('name', name)} in folder {result.get('folder', folder)}")

    return result


@show_app.command("external-dynamic-list")
@handle_command_errors("showing external dynamic list")
def show_external_dynamic_list(
    folder: str = FOLDER_OPTION,
    name: str = typer.Option(None, help="Name of the external dynamic list to show"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Show external dynamic list details or list all external dynamic lists in a folder.

    Examples
    --------
        # List all external dynamic lists in a folder (default behavior)
        scm show object external-dynamic-list --folder Texas

        # Show a specific external dynamic list by name
        scm show object external-dynamic-list --folder Texas --name malicious-ips

    """
    if name:
        # Get a specific external dynamic list by name
        edl = scm_client.get_external_dynamic_list(folder=folder, name=name)
        emit(edl, output, title=f"External Dynamic List: {edl.get('name', name)}")
        return edl

    # List all external dynamic lists in the folder (default behavior)
    edls = scm_client.list_external_dynamic_lists(folder=folder)
    emit(
        edls,
        output,
        columns=["name", "folder", "type"],
        title=f"External Dynamic Lists in folder '{folder}'",
    )
    return edls or None


# =============================================================================================================================================================================================
# HIP OBJECT COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("hip-object")
@handle_command_errors("backing up HIP objects")
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
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # List all HIP objects in the location with exact_match=True
    kwargs = {location_type: location_value}
    hip_objects = scm_client.list_hip_objects(**kwargs, exact_match=True)

    if not hip_objects:
        info(f"No HIP objects found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(backup_data)} HIP objects to {file}")
    return str(file)


@delete_app.command("hip-object")
@handle_command_errors("deleting HIP object")
def delete_hip_object(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a HIP object.

    Example:
    -------
    scm delete object hip-object --folder Texas --name windows-compliance

    """
    if not force:
        confirm = typer.confirm(f"Delete HIP object '{name}' from folder '{folder}'?")
        if not confirm:
            raise typer.Abort()
    result = scm_client.delete_hip_object(folder=folder, name=name)
    if result:
        success(f"Deleted HIP object: {name} from folder {folder}")
    return result


@load_app.command("hip-object", help="Load HIP objects from a YAML file.")
@handle_command_errors("loading HIP objects")
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
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Validate the file exists
    if not file.exists():
        error(f"Error: File '{file}' does not exist")
        raise typer.Exit(code=1)

    # Load YAML content
    with file.open() as f:
        yaml_content = yaml.safe_load(f)

    if not yaml_content:
        error(f"Error: File '{file}' is empty or invalid")
        raise typer.Exit(code=1)

    # Extract HIP objects from YAML
    hip_objects = yaml_content.get("hip_objects", [])
    if not hip_objects:
        info("No HIP objects found in the YAML file.")
        return

    if dry_run:
        info("[DRY RUN] Would load the following HIP objects:")

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

                success(f"Loaded HIP object: {hip_obj.name}")
                loaded_count += 1
                results.append(
                    {
                        "action": "created/updated",
                        "name": hip_obj.name,
                        "result": result,
                    }
                )
        except Exception as e:
            error(f"Error with HIP object '{hip_data.get('name', 'unknown')}': {str(e)}")
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
        info(f"[DRY RUN] Would load {len(hip_objects)} HIP objects from '{file}'")
    else:
        success(f"Successfully loaded {loaded_count} out of {len(hip_objects)} HIP objects from '{file}'")


@set_app.command("hip-object")
@handle_command_errors("creating HIP object")
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

    # Get the action performed
    action = result.pop("__action__", "created")

    if action == "created":
        success(f"Created HIP object: {result['name']} in folder {result['folder']}")
    elif action == "updated":
        success(f"Updated HIP object: {result['name']} in folder {result['folder']}")
    elif action == "no_change":
        info(f"No changes needed for HIP object: {result['name']} in folder {result['folder']}")

    return result


@show_app.command("hip-object")
@handle_command_errors("showing HIP object")
def show_hip_object(
    folder: str = FOLDER_OPTION,
    name: str = typer.Option(None, help="Name of the HIP object to show"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display HIP object configurations.

    Examples
    --------
        # List all HIP objects in a folder (default behavior)
        scm show object hip-object --folder Texas

        # Show a specific HIP object by name
        scm show object hip-object --folder Texas --name windows-compliance

    """
    if name:
        # Get a specific HIP object by name
        hip_obj = scm_client.get_hip_object(folder=folder, name=name)
        emit(hip_obj, output, title=f"HIP Object: {hip_obj.get('name', name)}")
        return hip_obj

    # List all HIP objects in the folder (default behavior)
    hip_objects = scm_client.list_hip_objects(folder=folder)
    emit(
        hip_objects,
        output,
        columns=["name", "folder", "description"],
        title=f"HIP Objects in folder '{folder}'",
    )
    return hip_objects or None


# =============================================================================================================================================================================================
# HIP PROFILE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("hip-profile")
@handle_command_errors("backing up HIP profiles")
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
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Get all HIP profiles from the location
    info(f"Fetching HIP profiles from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    hip_profiles = scm_client.list_hip_profiles(**kwargs, exact_match=True)

    if not hip_profiles:
        info(f"No HIP profiles found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(hip_profiles)} HIP profiles to {filename}")


@delete_app.command("hip-profile")
@handle_command_errors("deleting HIP profile")
def delete_hip_profile(
    folder: str = typer.Option(..., "--folder", help="Folder containing the HIP profile"),
    name: str = typer.Option(..., "--name", help="Name of the HIP profile to delete"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a HIP profile.

    Examples
    --------
        scm delete object hip-profile --folder Texas --name my-hip-profile

    """
    if not force:
        confirm = typer.confirm(f"Delete HIP profile '{name}' from folder '{folder}'?")
        if not confirm:
            raise typer.Abort()
    # Delete the HIP profile
    info(f"Deleting HIP profile '{name}' from folder '{folder}'...")
    scm_client.delete_hip_profile(folder=folder, name=name)
    success(f"Deleted HIP profile: {name} from folder {folder}")


@load_app.command("hip-profile", help="Load HIP profiles from a YAML file.")
@handle_command_errors("loading HIP profiles")
def load_hip_profile(
    file: Path = HIP_PROFILE_FILE_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
    dry_run: bool = HIP_PROFILE_DRY_RUN_OPTION,
):
    """Load HIP profiles from a YAML file."""
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Validate the file exists
    if not file.exists():
        error(f"Error: File '{file}' does not exist")
        raise typer.Exit(code=1)

    # Load YAML content
    with file.open() as f:
        yaml_content = yaml.safe_load(f)

    if not yaml_content:
        error(f"Error: File '{file}' is empty or invalid")
        raise typer.Exit(code=1)

    # Extract HIP profiles from YAML
    hip_profiles = yaml_content.get("hip_profiles", [])
    if not hip_profiles:
        info("No HIP profiles found in the YAML file.")
        return

    if dry_run:
        info("[DRY RUN] Would load the following HIP profiles:")

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
                success(f"Loaded HIP profile: {profile.name}")
                loaded_count += 1
                results.append(
                    {
                        "action": "created/updated",
                        "name": profile.name,
                        "result": profile_sdk,
                    }
                )
        except Exception as e:
            error(f"Error with HIP profile '{profile_data.get('name', 'unknown')}': {str(e)}")
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
        info(f"[DRY RUN] Would load {len(hip_profiles)} HIP profiles from '{file}'")
    else:
        success(f"Successfully loaded {loaded_count} out of {len(hip_profiles)} HIP profiles from '{file}'")


@set_app.command("hip-profile")
@handle_command_errors("creating/updating HIP profile")
def set_hip_profile(
    folder: str = typer.Option(..., "--folder", help="Folder path for the HIP profile"),
    name: str = typer.Option(..., "--name", help="Name of the HIP profile"),
    match: str = typer.Option(..., "--match", help="Match criteria for the HIP profile"),
    description: str = typer.Option(None, "--description", help="Description of the HIP profile"),
):
    """Create or update a HIP profile."""
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

    # Get the action performed
    action = result.pop("__action__", "created")

    if action == "created":
        success(f"Created HIP profile: {result['name']} in folder {result['folder']}")
    elif action == "updated":
        success(f"Updated HIP profile: {result['name']} in folder {result['folder']}")
    elif action == "no_change":
        info(f"No changes needed for HIP profile: {result['name']} in folder {result['folder']}")

    return result


@show_app.command("hip-profile")
@handle_command_errors("showing HIP profile")
def show_hip_profile(
    folder: str = typer.Option(..., "--folder", help="Folder path for the HIP profile"),
    name: str = typer.Option(None, "--name", help="Name of specific HIP profile to show"),
    output: OutputFormat = OUTPUT_OPTION,
) -> dict[str, Any] | None:
    """Show HIP profile details or list all HIP profiles in a folder.

    Examples
    --------
        # List all HIP profiles in a folder (default behavior)
        scm show object hip-profile --folder Texas

        # Show a specific HIP profile by name
        scm show object hip-profile --folder Texas --name windows-compliance

    """
    if name:
        # Show specific HIP profile
        hip_profile = scm_client.get_hip_profile(folder=folder, name=name)
        emit(hip_profile, output, title=f"HIP Profile: {hip_profile.get('name', name)}")
        return hip_profile

    # Default behavior: list all HIP profiles in the folder
    hip_profiles = scm_client.list_hip_profiles(folder=folder)
    emit(
        hip_profiles,
        output,
        columns=["name", "folder", "match", "description"],
        title=f"HIP profiles in folder '{folder}'",
    )
    return None


# =============================================================================================================================================================================================
# HTTP SERVER PROFILE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("http-server-profile")
@handle_command_errors("backing up HTTP server profiles")
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
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Get all HTTP server profiles from the location
    info(f"Fetching HTTP server profiles from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    http_server_profiles = scm_client.list_http_server_profiles(**kwargs, exact_match=True)

    if not http_server_profiles:
        info(f"No HTTP server profiles found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(http_server_profiles)} HTTP server profiles to {filename}")


@delete_app.command("http-server-profile")
@handle_command_errors("deleting HTTP server profile")
def delete_http_server_profile(
    folder: str = typer.Option(..., "--folder", help="Folder containing the HTTP server profile"),
    name: str = typer.Option(..., "--name", help="Name of the HTTP server profile to delete"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete an HTTP server profile from a specific folder."""
    if not force:
        confirm = typer.confirm(f"Delete HTTP server profile '{name}' from folder '{folder}'?")
        if not confirm:
            raise typer.Abort()
    # Delete the HTTP server profile
    info(f"Deleting HTTP server profile '{name}' from folder '{folder}'...")
    scm_client.delete_http_server_profile(folder=folder, name=name)
    success(f"Deleted HTTP server profile: {name} from folder {folder}")


@load_app.command("http-server-profile", help="Load HTTP server profiles from a YAML file.")
@handle_command_errors("loading HTTP server profiles")
def load_http_server_profile(
    file: Path = HTTP_SERVER_PROFILE_FILE_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
    dry_run: bool = HTTP_SERVER_PROFILE_DRY_RUN_OPTION,
):
    """Load HTTP server profiles from a YAML file."""
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Validate the file exists
    if not file.exists():
        error(f"Error: File '{file}' does not exist")
        raise typer.Exit(code=1)

    # Load YAML content
    with file.open() as f:
        yaml_content = yaml.safe_load(f)

    if not yaml_content:
        error(f"Error: File '{file}' is empty or invalid")
        raise typer.Exit(code=1)

    # Extract HTTP server profiles from YAML
    http_server_profiles = yaml_content.get("http_server_profiles", [])
    if not http_server_profiles:
        info("No HTTP server profiles found in the YAML file.")
        return

    if dry_run:
        info("[DRY RUN] Would load the following HTTP server profiles:")

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
                    typer.echo(f"    Server {server_idx + 1}: {server.get('name', 'unnamed')} - {server.get('address', 'N/A')}:{server.get('port', 'N/A')} ({server.get('protocol', 'N/A')})")
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
                success(f"Loaded HTTP server profile: {profile.name}")
                loaded_count += 1
                results.append(
                    {
                        "action": "created/updated",
                        "name": profile.name,
                        "result": profile_sdk,
                    }
                )
        except Exception as e:
            error(f"Error with HTTP server profile '{profile_data.get('name', 'unknown')}': {str(e)}")
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
        info(f"[DRY RUN] Would load {len(http_server_profiles)} HTTP server profiles from '{file}'")
    else:
        success(f"Successfully loaded {loaded_count} out of {len(http_server_profiles)} HTTP server profiles from '{file}'")


@set_app.command("http-server-profile")
@handle_command_errors("creating/updating HTTP server profile")
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

    # Get the action performed
    action = result.pop("__action__", "created")

    if action == "created":
        success(f"Created HTTP server profile: {result['name']} in folder {result['folder']}")
    elif action == "updated":
        success(f"Updated HTTP server profile: {result['name']} in folder {result['folder']}")
    elif action == "no_change":
        info(f"No changes needed for HTTP server profile: {result['name']} in folder {result['folder']}")

    return result


@show_app.command("http-server-profile")
@handle_command_errors("showing HTTP server profile")
def show_http_server_profile(
    folder: str = typer.Option(..., "--folder", help="Folder path for the HTTP server profile"),
    name: str = typer.Option(None, "--name", help="Name of specific HTTP server profile to show"),
    list: bool = typer.Option(False, "--list", help="List all HTTP server profiles in the folder"),
    output: OutputFormat = OUTPUT_OPTION,
) -> dict[str, Any] | None:
    """Show HTTP server profile details or list all HTTP server profiles in a folder.

    Examples
    --------
        # List all HTTP server profiles in a folder (default behavior)
        scm show object http-server-profile --folder Texas

        # Show a specific HTTP server profile by name
        scm show object http-server-profile --folder Texas --name syslog-collector

    """
    if name:
        # Show specific HTTP server profile (server configs may carry passwords)
        http_server_profile = scm_client.get_http_server_profile(folder=folder, name=name)
        emit(redact(http_server_profile), output, title=f"HTTP Server Profile: {http_server_profile.get('name', name)}")
        return http_server_profile

    # List all HTTP server profiles in the folder (default behavior)
    http_server_profiles = scm_client.list_http_server_profiles(folder=folder)
    emit(
        redact(http_server_profiles),
        output,
        columns=["name", "folder", "tag_registration", "server", "description"],
        title=f"HTTP server profiles in folder '{folder}'",
    )
    return None


@backup_app.command("log-forwarding-profile")
@handle_command_errors("backing up log forwarding profiles")
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
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # List all log forwarding profiles in the location (exact match)
    kwargs = {location_type: location_value}
    log_forwarding_profiles = scm_client.list_log_forwarding_profiles(**kwargs, exact_match=True)

    if not log_forwarding_profiles:
        info(f"No log forwarding profiles found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(profiles_data)} log forwarding profiles to {filename}")


@delete_app.command("log-forwarding-profile")
@handle_command_errors("deleting log forwarding profile")
def delete_log_forwarding_profile(
    folder: str = typer.Option(..., "--folder", help="Folder path for the log forwarding profile"),
    name: str = typer.Option(..., "--name", help="Name of the log forwarding profile to delete"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a log forwarding profile.

    Examples
    --------
        scm delete object log-forwarding-profile --folder Texas --name my-lfp

    """
    if not force:
        confirm = typer.confirm(f"Delete log forwarding profile '{name}' from folder '{folder}'?")
        if not confirm:
            raise typer.Abort()
    # Delete the log forwarding profile
    deleted = scm_client.delete_log_forwarding_profile(folder=folder, name=name)

    if deleted:
        success(f"Deleted log forwarding profile: {name} from folder {folder}")
    else:
        error(f"Failed to delete log forwarding profile '{name}' from folder '{folder}'")
        raise typer.Exit(code=1)


@load_app.command("log-forwarding-profile", help="Load log forwarding profiles from a YAML file.")
@handle_command_errors("loading log forwarding profiles")
def load_log_forwarding_profile(
    file: Path = FILE_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load log forwarding profiles from a YAML file."""
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Validate the file exists
    if not file.exists():
        error(f"Error: File '{file}' does not exist")
        raise typer.Exit(code=1)

    # Load YAML content
    with file.open() as f:
        yaml_content = yaml.safe_load(f)

    if not yaml_content:
        error(f"Error: File '{file}' is empty or invalid")
        raise typer.Exit(code=1)

    # Extract log forwarding profiles from YAML
    log_forwarding_profiles = yaml_content.get("log_forwarding_profiles", [])
    if not log_forwarding_profiles:
        info("No log forwarding profiles found in the YAML file.")
        return

    if dry_run:
        info("[DRY RUN] Would load the following log forwarding profiles:")

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

                success(f"Loaded log forwarding profile: {profile.name}")
                loaded_count += 1
                results.append(
                    {
                        "action": "created/updated",
                        "name": profile.name,
                        "result": result,
                    }
                )
        except Exception as e:
            error(f"Error with log forwarding profile '{profile_data.get('name', 'unknown')}': {str(e)}")
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
        info(f"[DRY RUN] Would load {len(log_forwarding_profiles)} log forwarding profiles from '{file}'")
    else:
        success(f"Successfully loaded {loaded_count} out of {len(log_forwarding_profiles)} log forwarding profiles from '{file}'")


@set_app.command("log-forwarding-profile")
@handle_command_errors("creating/updating log forwarding profile")
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

    # Parse match list if provided
    match_list_data = None
    if match_list:
        try:
            match_list_data = json.loads(match_list)
            if not isinstance(match_list_data, list):
                error("Error: match_list must be a JSON array")
                raise typer.Exit(code=1)
        except json.JSONDecodeError as e:
            error(f"Error parsing match list JSON: {str(e)}")
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
        # Get the action performed
        action = result.pop("__action__", "created")

        if action == "created":
            success(f"Created log forwarding profile: {name} in folder {folder}")
        elif action == "updated":
            success(f"Updated log forwarding profile: {name} in folder {folder}")
        elif action == "no_change":
            info(f"No changes needed for log forwarding profile: {name} in folder {folder}")
    else:
        error(f"Failed to create/update log forwarding profile '{name}'")
        raise typer.Exit(code=1)


@show_app.command("log-forwarding-profile")
@handle_command_errors("showing log forwarding profile")
def show_log_forwarding_profile(
    folder: str = typer.Option(..., "--folder", help="Folder path for the log forwarding profile"),
    name: str = typer.Option(None, "--name", help="Name of specific log forwarding profile to show"),
    list: bool = typer.Option(False, "--list", help="List all log forwarding profiles in the folder"),
    output: OutputFormat = OUTPUT_OPTION,
) -> dict[str, Any] | None:
    """Show log forwarding profile details or list all log forwarding profiles in a folder.

    Examples
    --------
        # List all log forwarding profiles in a folder (default behavior)
        scm show object log-forwarding-profile --folder Texas

        # Show a specific log forwarding profile by name
        scm show object log-forwarding-profile --folder Texas --name security-logs

    """
    if name:
        # Show specific log forwarding profile
        log_forwarding_profile = scm_client.get_log_forwarding_profile(folder=folder, name=name)
        emit(log_forwarding_profile, output, title=f"Log Forwarding Profile: {log_forwarding_profile.get('name', name)}")
        return log_forwarding_profile

    # List all log forwarding profiles in the folder (default behavior)
    log_forwarding_profiles = scm_client.list_log_forwarding_profiles(folder=folder)
    emit(
        log_forwarding_profiles,
        output,
        columns=["name", "folder", "enhanced_application_logging", "match_list", "description"],
        title=f"Log forwarding profiles in folder '{folder}'",
    )
    return None


@backup_app.command("region", help="Export regions to a YAML file.")
@handle_command_errors("backing up regions")
def backup_region(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export regions from a specified location to a YAML file.

    Examples
    --------
        # Backup from a folder
        scm backup object region --folder Austin

        # Backup with custom output file
        scm backup object region --folder Austin --file regions.yaml

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # List all regions based on location type
    info(f"Retrieving regions from {location_type} '{location_value}'...")

    # Build kwargs based on location type
    kwargs = {location_type: location_value}
    regions = scm_client.list_regions(**kwargs)

    if not regions:
        info(f"No regions found in {location_type} '{location_value}'")
        return

    # Prepare data for export
    export_data = {"regions": regions}

    # Generate filename if not provided
    filename = Path(file or get_default_backup_filename("region", location_type, location_value))

    # Write to file
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(regions)} regions to {filename}")


@delete_app.command("region", help="Delete a region.")
@handle_command_errors("deleting region")
def delete_region(
    name: str = typer.Argument(..., help="Name of the region to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a region.

    Examples
    --------
        scm delete object region us-east --folder Texas

    """
    # Determine container location
    if not any([folder, snippet, device]):
        folder = "Texas"  # Default to Texas folder

    # Retrieve the region first to confirm it exists
    region = scm_client.get_region(
        name=name,
        folder=folder,
        snippet=snippet,
        device=device,
    )

    if not region:
        error(f"Region '{name}' not found")
        raise typer.Exit(code=1)

    # Confirm deletion
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete region '{name}'?")
        if not confirm:
            info("Deletion cancelled")
            raise typer.Exit(code=0)

    # Delete the region
    scm_client.delete_region(
        name=name,
        folder=folder,
        snippet=snippet,
        device=device,
    )

    container = folder or snippet or device
    success(f"Deleted region: {name} from {container}")


@load_app.command("region", help="Load regions from a YAML file.")
@handle_command_errors("loading regions")
def load_region(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
) -> None:
    """Load regions from a YAML file."""
    # Validate file exists
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)

    # Load YAML data
    with Path(file).open() as f:
        data = yaml.safe_load(f)

    if not data or "regions" not in data:
        error("No regions found in file")
        raise typer.Exit(code=1)

    regions = data["regions"]
    if not isinstance(regions, list):
        regions = [regions]

    # Process each region
    created_count = 0
    for region_data in regions:
        try:
            # Validate with Pydantic model
            validated_region = Region(**region_data)

            # Override container if specified
            if folder:
                validated_region.folder = folder
                validated_region.snippet = None
                validated_region.device = None
            elif snippet:
                validated_region.snippet = snippet
                validated_region.folder = None
                validated_region.device = None
            elif device:
                validated_region.device = device
                validated_region.folder = None
                validated_region.snippet = None

            # Convert to SDK format
            sdk_data = validated_region.to_sdk_model()

            # Create/update the region
            scm_client.create_region(sdk_data)

            created_count += 1

            container = validated_region.folder or validated_region.snippet or validated_region.device
            success(f"Created region: {validated_region.name} in {container}")

        except Exception as e:
            error(f"Error processing region: {str(e)}")
            continue

    success(f"Summary: Processed {created_count} regions")


@delete_app.command("quarantined-device", help="Delete a quarantined device.")
@handle_command_errors("deleting quarantined device")
def delete_quarantined_device(
    host_id: str = typer.Argument(..., help="Host ID of the quarantined device to delete"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a quarantined device by host ID.

    Examples
    --------
        scm delete object quarantined-device 01abcdef-2345-6789-abcd-ef0123456789

    """
    show_context_info()

    if not force:
        confirm = typer.confirm(f"Delete quarantined device '{host_id}'?")
        if not confirm:
            raise typer.Abort()

    scm_client.delete_quarantined_device(host_id=host_id)
    success(f"Deleted quarantined device: {host_id}")


@load_app.command("quarantined-device", help="Load quarantined devices from a YAML file.")
@handle_command_errors("loading quarantined devices")
def load_quarantined_device(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
) -> None:
    """Load quarantined devices from a YAML file."""
    # Validate file exists
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)

    # Load YAML data
    with Path(file).open() as f:
        data = yaml.safe_load(f)

    if not data or "quarantined_devices" not in data:
        error("No quarantined_devices found in file")
        raise typer.Exit(code=1)

    devices = data["quarantined_devices"]
    if not isinstance(devices, list):
        devices = [devices]

    # Process each device
    created_count = 0
    for device_data in devices:
        try:
            # Validate with Pydantic model
            validated_device = QuarantinedDevice(**device_data)

            # Convert to SDK format
            sdk_data = validated_device.to_sdk_model()

            # Create the quarantined device
            scm_client.create_quarantined_device(sdk_data)

            created_count += 1
            success(f"Created quarantined device: {validated_device.host_id}")

        except Exception as e:
            error(f"Error processing quarantined device: {str(e)}")
            continue

    success(f"Summary: Processed {created_count} quarantined devices")


@set_app.command("region", help="Create or update a region.")
@handle_command_errors("creating/updating region")
def set_region(
    name: str = typer.Argument(..., help="Name of the region"),
    latitude: float = typer.Option(None, "--latitude", help="Latitude of the region (-90 to 90)"),
    longitude: float = typer.Option(None, "--longitude", help="Longitude of the region (-180 to 180)"),
    addresses: list[str] | None = REGION_ADDRESSES_OPTION,
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Create or update a region."""
    # Determine container location
    if not any([folder, snippet, device]):
        folder = "Texas"  # Default to Texas folder

    # Build region data
    region_data: dict[str, Any] = {
        "name": name,
    }

    # Add container
    if folder:
        region_data["folder"] = folder
    elif snippet:
        region_data["snippet"] = snippet
    elif device:
        region_data["device"] = device

    # Add optional fields
    if latitude is not None:
        region_data["latitude"] = latitude
    if longitude is not None:
        region_data["longitude"] = longitude
    if addresses:
        region_data["addresses"] = addresses

    # Validate with Pydantic model
    validated_region = Region(**region_data)

    # Convert to SDK format
    sdk_data = validated_region.to_sdk_model()

    # Create/update the region
    result = scm_client.create_region(sdk_data)

    # Get the action performed
    action = result.pop("__action__", "created")

    container = folder or snippet or device
    if action == "created":
        success(f"Created region: {name} in {container}")
    elif action == "updated":
        success(f"Updated region: {name} in {container}")
    elif action == "no_change":
        info(f"No changes needed for region: {name} in {container}")


@show_app.command("region", help="Show region details.")
@handle_command_errors("showing region")
def show_region(
    name: str = typer.Option(None, "--name", help="Name of specific region to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
) -> list[dict[str, Any]] | dict[str, Any] | None:
    """Show region details.

    Examples
    --------
        # List all regions (default behavior)
        scm show object region

        # Show a specific region by name
        scm show object region --name US-South

    """
    # Determine container location
    if not any([folder, snippet, device]):
        folder = "Texas"  # Default to Texas folder

    if name:
        # Show specific region
        region = scm_client.get_region(
            name=name,
            folder=folder,
            snippet=snippet,
            device=device,
        )

        if not region:
            error(f"Region '{name}' not found")
            raise typer.Exit(code=1)

        emit(region, output, title=f"Region: {region.get('name', name)}")
        return region

    # Default behavior: list all regions
    regions = scm_client.list_regions(
        folder=folder,
        snippet=snippet,
        device=device,
    )
    emit(
        regions,
        output,
        columns=["name", "folder", "geo_location", "address"],
        title="Regions",
    )
    return regions or None


@set_app.command("quarantined-device", help="Create a quarantined device entry.")
@handle_command_errors("creating quarantined device")
def set_quarantined_device(
    host_id: str = typer.Argument(..., help="Host ID of the device to quarantine"),
    serial_number: str = typer.Option(None, "--serial-number", help="Serial number of the device"),
) -> None:
    """Create a quarantined device entry."""
    show_context_info()

    # Build device data
    device_data: dict[str, Any] = {
        "host_id": host_id,
    }

    if serial_number:
        device_data["serial_number"] = serial_number

    # Validate with Pydantic model
    validated_device = QuarantinedDevice(**device_data)

    # Convert to SDK format
    sdk_data = validated_device.to_sdk_model()

    # Create the quarantined device
    scm_client.create_quarantined_device(sdk_data)

    success(f"Created quarantined device: {host_id}")


@show_app.command("quarantined-device", help="Show quarantined devices.")
@handle_command_errors("showing quarantined devices")
def show_quarantined_device(
    host_id: str = typer.Option(None, "--host-id", help="Filter by host ID"),
    serial_number: str = typer.Option(None, "--serial-number", help="Filter by serial number"),
    output: OutputFormat = OUTPUT_OPTION,
) -> list[dict[str, Any]] | dict[str, Any] | None:
    """Show quarantined devices.

    Examples
    --------
        # List all quarantined devices
        scm show object quarantined-device

        # Filter by host ID
        scm show object quarantined-device --host-id abc123

    """
    show_context_info()

    devices = scm_client.list_quarantined_devices(
        host_id=host_id,
        serial_number=serial_number,
    )
    emit(
        devices,
        output,
        columns=["host_id", "serial_number"],
        title="Quarantined Devices",
    )
    return devices or None


@backup_app.command("service")
@handle_command_errors("backing up services")
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
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # List all services in the location (exact match)
    kwargs = {location_type: location_value}
    services = scm_client.list_services(**kwargs, exact_match=True)

    if not services:
        info(f"No services found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(services_data)} services to {filename}")


@delete_app.command("service")
@handle_command_errors("deleting service")
def delete_service(
    folder: str = typer.Option(..., "--folder", help="Folder path for the service"),
    name: str = typer.Option(..., "--name", help="Name of the service to delete"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a service.

    Examples
    --------
        scm delete object service --folder Texas --name web-service

    """
    if not force:
        confirm = typer.confirm(f"Delete service '{name}' from folder '{folder}'?")
        if not confirm:
            raise typer.Abort()
    # Delete the service
    deleted = scm_client.delete_service(folder=folder, name=name)

    if deleted:
        success(f"Deleted service: {name} from folder {folder}")
    else:
        error(f"Failed to delete service '{name}' from folder '{folder}'")
        raise typer.Exit(code=1)


@load_app.command("service", help="Load services from a YAML file.")
@handle_command_errors("loading services")
def load_service(
    file: Path = FILE_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load services from a YAML file."""
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Validate the file exists
    if not file.exists():
        error(f"Error: File '{file}' does not exist")
        raise typer.Exit(code=1)

    # Load YAML content
    with file.open() as f:
        yaml_content = yaml.safe_load(f)

    if not yaml_content:
        error(f"Error: File '{file}' is empty or invalid")
        raise typer.Exit(code=1)

    # Extract services from YAML
    services = yaml_content.get("services", [])
    if not services:
        info("No services found in the YAML file.")
        return

    if dry_run:
        info("[DRY RUN] Would load the following services:")

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

                success(f"Loaded service: {service.name}")
                loaded_count += 1
                results.append(
                    {
                        "action": "created/updated",
                        "name": service.name,
                        "result": result,
                    }
                )

        except Exception as e:
            error(f"Error with service '{service_data.get('name', 'unknown')}': {str(e)}")
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
        info(f"[DRY RUN] Would load {len(services)} services from '{file}'")
    else:
        success(f"Successfully loaded {loaded_count} out of {len(services)} services from '{file}'")


@set_app.command("service")
@handle_command_errors("creating/updating service")
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
        tag_list = parse_comma_separated_list([tag])

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
            success(f"Created service: {name} in folder {folder}")
        elif action == "updated":
            success(f"Updated service: {name} in folder {folder}")
        elif action == "no_change":
            info(f"No changes needed for service: {name} in folder {folder}")
    else:
        error(f"Failed to create/update service '{name}'")
        raise typer.Exit(code=1)


@show_app.command("service")
@handle_command_errors("showing service")
def show_service(
    folder: str = typer.Option(..., "--folder", help="Folder path for the service"),
    name: str = typer.Option(None, "--name", help="Name of specific service to show"),
    list: bool = typer.Option(False, "--list", help="List all services in the folder"),
    output: OutputFormat = OUTPUT_OPTION,
) -> dict[str, Any] | None:
    """Show service details or list all services in a folder.

    Examples
    --------
        # List all services in a folder (default behavior)
        scm show object service --folder Texas

        # Show a specific service by name
        scm show object service --folder Texas --name web-server

    """
    if name:
        # Show specific service
        service = scm_client.get_service(folder=folder, name=name)
        emit(service, output, title=f"Service: {service.get('name', name)}")
        return service

    # List all services in the folder (default behavior)
    services = scm_client.list_services(folder=folder)
    emit(
        services,
        output,
        columns=["name", "folder", "protocol", "description", "tag"],
        title=f"Services in folder '{folder}'",
    )
    return None


@backup_app.command("service-group")
@handle_command_errors("backing up service groups")
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
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # List all service groups in the location (exact match)
    kwargs = {location_type: location_value}
    service_groups = scm_client.list_service_groups(**kwargs, exact_match=True)

    if not service_groups:
        info(f"No service groups found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(groups_data)} service groups to {filename}")


@delete_app.command("service-group")
@handle_command_errors("deleting service group")
def delete_service_group(
    folder: str = typer.Option(..., "--folder", help="Folder path for the service group"),
    name: str = typer.Option(..., "--name", help="Name of the service group to delete"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a service group.

    Examples
    --------
        scm delete object service-group --folder Texas --name web-services

    """
    if not force:
        confirm = typer.confirm(f"Delete service group '{name}' from folder '{folder}'?")
        if not confirm:
            raise typer.Abort()
    # Delete the service group
    deleted = scm_client.delete_service_group(folder=folder, name=name)

    if deleted:
        success(f"Deleted service group: {name} from folder {folder}")
    else:
        error(f"Failed to delete service group '{name}' from folder '{folder}'")
        raise typer.Exit(code=1)


@load_app.command("service-group", help="Load service groups from a YAML file.")
@handle_command_errors("loading service groups")
def load_service_group(
    file: Path = FILE_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load service groups from a YAML file."""
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Validate the file exists
    if not file.exists():
        error(f"Error: File '{file}' does not exist")
        raise typer.Exit(code=1)

    # Load YAML content
    with file.open() as f:
        yaml_content = yaml.safe_load(f)

    if not yaml_content:
        error(f"Error: File '{file}' is empty or invalid")
        raise typer.Exit(code=1)

    # Extract service groups from YAML
    service_groups = yaml_content.get("service_groups", [])
    if not service_groups:
        info("No service groups found in the YAML file.")
        return

    if dry_run:
        info("[DRY RUN] Would load the following service groups:")

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

                success(f"Loaded service group: {service_group.name}")
                loaded_count += 1
                results.append(
                    {
                        "action": "created/updated",
                        "name": service_group.name,
                        "result": result,
                    }
                )

        except Exception as e:
            error(f"Error with service group '{group_data.get('name', 'unknown')}': {str(e)}")
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
        info(f"[DRY RUN] Would load {len(service_groups)} service groups from '{file}'")
    else:
        success(f"Successfully loaded {loaded_count} out of {len(service_groups)} service groups from '{file}'")


@set_app.command("service-group")
@handle_command_errors("creating/updating service group")
def set_service_group(
    folder: str = typer.Option(..., "--folder", help="Folder path for the service group"),
    name: str = typer.Option(..., "--name", help="Name of the service group"),
    members: str = typer.Option(..., "--members", help="Comma-separated list of service or service group names"),
    tag: str = typer.Option(None, "--tag", help="Comma-separated list of tags"),
) -> None:
    """Create or update a service group."""
    # Parse members
    member_list = parse_comma_separated_list([members])
    if not member_list:
        error("Error: At least one member must be provided")
        raise typer.Exit(code=1)

    # Parse tags if provided
    tag_list = None
    if tag:
        tag_list = parse_comma_separated_list([tag])

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
        # Get the action performed
        action = result.pop("__action__", "created")

        if action == "created":
            success(f"Created service group: {name} in folder {folder}")
        elif action == "updated":
            success(f"Updated service group: {name} in folder {folder}")
        elif action == "no_change":
            info(f"No changes needed for service group: {name} in folder {folder}")
    else:
        error(f"Failed to create/update service group '{name}'")
        raise typer.Exit(code=1)


@show_app.command("service-group")
@handle_command_errors("showing service group")
def show_service_group(
    folder: str = typer.Option(..., "--folder", help="Folder path for the service group"),
    name: str = typer.Option(None, "--name", help="Name of specific service group to show"),
    list: bool = typer.Option(False, "--list", help="List all service groups in the folder"),
    output: OutputFormat = OUTPUT_OPTION,
) -> dict[str, Any] | None:
    """Show service group details or list all service groups in a folder.

    Examples
    --------
        # List all service groups in a folder (default behavior)
        scm show object service-group --folder Texas

        # Show a specific service group by name
        scm show object service-group --folder Texas --name web-services

    """
    if name:
        # Show specific service group
        service_group = scm_client.get_service_group(folder=folder, name=name)
        emit(service_group, output, title=f"Service Group: {service_group.get('name', name)}")
        return service_group

    # List all service groups in the folder (default behavior)
    service_groups = scm_client.list_service_groups(folder=folder)
    emit(
        service_groups,
        output,
        columns=["name", "folder", "members", "tag"],
        title=f"Service groups in folder '{folder}'",
    )
    return None


# =============================================================================================================================================================================================
# SYSLOG SERVER PROFILE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("syslog-server-profile", help="Export syslog server profiles to a YAML file.")
@handle_command_errors("backing up syslog server profiles")
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
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # List all syslog server profiles based on location type
    info(f"Retrieving syslog server profiles from {location_type} '{location_value}'...")

    # Build kwargs based on location type
    kwargs = {location_type: location_value}
    profiles = scm_client.list_syslog_server_profiles(**kwargs)

    if not profiles:
        info(f"No syslog server profiles found in {location_type} '{location_value}'")
        return

    # Prepare data for export
    export_data = {"syslog_server_profiles": profiles}

    # Generate filename if not provided
    filename = Path(file or get_default_backup_filename("syslog-server-profile", location_type, location_value))

    # Write to file
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(profiles)} syslog server profiles to {filename}")


@delete_app.command("syslog-server-profile", help="Delete a syslog server profile.")
@handle_command_errors("deleting syslog server profile")
def delete_syslog_server_profile(
    name: str = typer.Argument(..., help="Name of the syslog server profile to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a syslog server profile.

    Examples
    --------
        scm delete object syslog-server-profile my-syslog --folder Texas

    """
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
        error(f"Syslog server profile '{name}' not found")
        raise typer.Exit(code=1)

    # Confirm deletion
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete syslog server profile '{name}'?")
        if not confirm:
            info("Deletion cancelled")
            raise typer.Exit(code=0)

    # Delete the profile
    scm_client.delete_syslog_server_profile(
        name=name,
        folder=folder,
        snippet=snippet,
        device=device,
    )

    container = folder or snippet or device
    success(f"Deleted syslog server profile: {name} from {container}")


@load_app.command("syslog-server-profile", help="Load syslog server profiles from a YAML file.")
@handle_command_errors("loading syslog server profiles")
def load_syslog_server_profile(
    file: Path = FILE_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load syslog server profiles from a YAML file."""
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Validate the file exists
    if not file.exists():
        error(f"Error: File '{file}' does not exist")
        raise typer.Exit(code=1)

    # Load YAML content
    with file.open() as f:
        yaml_content = yaml.safe_load(f)

    if not yaml_content:
        error(f"Error: File '{file}' is empty or invalid")
        raise typer.Exit(code=1)

    # Extract syslog server profiles from YAML
    syslog_server_profiles = yaml_content.get("syslog_server_profiles", [])
    if not syslog_server_profiles:
        info("No syslog server profiles found in the YAML file.")
        return

    if dry_run:
        info("[DRY RUN] Would load the following syslog server profiles:")

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

                success(f"Loaded syslog server profile: {profile.name}")
                loaded_count += 1
                results.append(
                    {
                        "action": "created/updated",
                        "name": profile.name,
                        "result": sdk_data,
                    }
                )

        except Exception as e:
            error(f"Error with syslog server profile '{profile_data.get('name', 'unknown')}': {str(e)}")
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
        info(f"[DRY RUN] Would load {len(syslog_server_profiles)} syslog server profiles from '{file}'")
    else:
        success(f"Successfully loaded {loaded_count} out of {len(syslog_server_profiles)} syslog server profiles from '{file}'")


@set_app.command("syslog-server-profile", help="Create or update a syslog server profile.")
@handle_command_errors("creating/updating syslog server profile")
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
    result = scm_client.create_syslog_server_profile(sdk_data)

    container = folder or snippet or device

    # Get the action performed
    action = result.pop("__action__", "created") if result else "created"

    if action == "created":
        success(f"Created syslog server profile: {name} in {container}")
    elif action == "updated":
        success(f"Updated syslog server profile: {name} in {container}")
    elif action == "no_change":
        info(f"No changes needed for syslog server profile: {name} in {container}")


@show_app.command("syslog-server-profile", help="Show syslog server profile details.")
@handle_command_errors("showing syslog server profile")
def show_syslog_server_profile(
    name: str = typer.Option(None, "--name", help="Name of specific syslog server profile to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
) -> list[dict[str, Any]] | dict[str, Any] | None:
    """Show syslog server profile details.

    Examples
    --------
        # List all syslog server profiles (default behavior)
        scm show object syslog-server-profile

        # Show a specific syslog server profile by name
        scm show object syslog-server-profile --name primary-syslog

    """
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
            error(f"Syslog server profile '{name}' not found")
            raise typer.Exit(code=1)

        emit(profile, output, title=f"Syslog Server Profile: {profile.get('name', name)}")
        return profile

    # Default behavior: list all syslog server profiles
    profiles = scm_client.list_syslog_server_profiles(
        folder=folder,
        snippet=snippet,
        device=device,
    )
    emit(
        profiles,
        output,
        columns=["name", "folder", "server", "description", "tag"],
        title="Syslog Server Profiles",
    )
    return profiles or None


# =============================================================================================================================================================================================
# SCHEDULE COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("schedule", help="Export schedules to a YAML file.")
@handle_command_errors("backing up schedules")
def backup_schedule(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
) -> None:
    """Export schedules from a specified location to a YAML file.

    Examples
    --------
        # Backup from a folder
        scm backup object schedule --folder Austin

        # Backup with custom output file
        scm backup object schedule --folder Austin --file schedules.yaml

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # List all schedules based on location type
    info(f"Retrieving schedules from {location_type} '{location_value}'...")

    # Build kwargs based on location type
    kwargs = {location_type: location_value}
    schedules = scm_client.list_schedules(**kwargs)

    if not schedules:
        info(f"No schedules found in {location_type} '{location_value}'")
        return

    # Prepare data for export
    export_data = {"schedules": schedules}

    # Generate filename if not provided
    filename = Path(file or get_default_backup_filename("schedule", location_type, location_value))

    # Write to file
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(schedules)} schedules to {filename}")


@delete_app.command("schedule", help="Delete a schedule.")
@handle_command_errors("deleting schedule")
def delete_schedule(
    name: str = typer.Argument(..., help="Name of the schedule to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a schedule.

    Examples
    --------
        scm delete object schedule business-hours --folder Texas

    """
    # Determine container location
    if not any([folder, snippet, device]):
        folder = "Texas"  # Default to Texas folder

    # Retrieve the schedule first to confirm it exists
    schedule = scm_client.get_schedule(
        name=name,
        folder=folder,
        snippet=snippet,
        device=device,
    )

    if not schedule:
        error(f"Schedule '{name}' not found")
        raise typer.Exit(code=1)

    # Confirm deletion
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete schedule '{name}'?")
        if not confirm:
            info("Deletion cancelled")
            raise typer.Exit(code=0)

    # Delete the schedule
    scm_client.delete_schedule(
        name=name,
        folder=folder,
        snippet=snippet,
        device=device,
    )

    container = folder or snippet or device
    success(f"Deleted schedule: {name} from {container}")


@load_app.command("schedule", help="Load schedules from a YAML file.")
@handle_command_errors("loading schedules")
def load_schedule(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
) -> None:
    """Load schedules from a YAML file."""
    # Validate file exists
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)

    # Load YAML data
    with Path(file).open() as f:
        data = yaml.safe_load(f)

    if not data or "schedules" not in data:
        error("No schedules found in file")
        raise typer.Exit(code=1)

    schedules = data["schedules"]
    if not isinstance(schedules, list):
        schedules = [schedules]

    # Process each schedule
    created_count = 0
    for schedule_data in schedules:
        try:
            # Create/update the schedule directly (YAML already has SDK format)
            scm_client.create_schedule(schedule_data)

            created_count += 1

            container = schedule_data.get("folder") or schedule_data.get("snippet") or schedule_data.get("device")
            success(f"Created schedule: {schedule_data['name']} in {container}")

        except Exception as e:
            error(f"Error processing schedule: {str(e)}")
            continue

    success(f"Summary: Processed {created_count} schedules")


@set_app.command("schedule", help="Create or update a schedule.")
@handle_command_errors("creating/updating schedule")
def set_schedule(
    name: str = typer.Argument(..., help="Name of the schedule"),
    schedule_type: str = typer.Option(..., "--schedule-type", help="Schedule type: recurring-daily, recurring-weekly, or non-recurring"),
    time_ranges: list[str] | None = SCHEDULE_TIME_RANGE_OPTION,
    days_monday: list[str] | None = SCHEDULE_MONDAY_OPTION,
    days_tuesday: list[str] | None = SCHEDULE_TUESDAY_OPTION,
    days_wednesday: list[str] | None = SCHEDULE_WEDNESDAY_OPTION,
    days_thursday: list[str] | None = SCHEDULE_THURSDAY_OPTION,
    days_friday: list[str] | None = SCHEDULE_FRIDAY_OPTION,
    days_saturday: list[str] | None = SCHEDULE_SATURDAY_OPTION,
    days_sunday: list[str] | None = SCHEDULE_SUNDAY_OPTION,
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Create or update a schedule."""
    # Determine container location
    if not any([folder, snippet, device]):
        folder = "Texas"  # Default to Texas folder

    # Build days mapping for weekly schedules
    days = None
    if schedule_type == "recurring-weekly":
        days = {}
        if days_monday:
            days["monday"] = days_monday
        if days_tuesday:
            days["tuesday"] = days_tuesday
        if days_wednesday:
            days["wednesday"] = days_wednesday
        if days_thursday:
            days["thursday"] = days_thursday
        if days_friday:
            days["friday"] = days_friday
        if days_saturday:
            days["saturday"] = days_saturday
        if days_sunday:
            days["sunday"] = days_sunday

    # Build schedule data
    schedule_data: dict[str, Any] = {
        "name": name,
        "schedule_type": schedule_type,
    }

    # Add container
    if folder:
        schedule_data["folder"] = folder
    elif snippet:
        schedule_data["snippet"] = snippet
    elif device:
        schedule_data["device"] = device

    # Add schedule-type-specific fields
    if time_ranges:
        schedule_data["time_ranges"] = time_ranges
    if days:
        schedule_data["days"] = days

    # Validate with Pydantic model
    validated_schedule = Schedule(**schedule_data)

    # Convert to SDK format
    sdk_data = validated_schedule.to_sdk_model()

    # Create/update the schedule
    result = scm_client.create_schedule(sdk_data)

    # Get the action performed
    action = result.pop("__action__", "created")

    container = folder or snippet or device
    if action == "created":
        success(f"Created schedule: {name} in {container}")
    elif action == "updated":
        success(f"Updated schedule: {name} in {container}")
    elif action == "no_change":
        info(f"No changes needed for schedule: {name} in {container}")


@show_app.command("schedule", help="Show schedule details.")
@handle_command_errors("showing schedule")
def show_schedule(
    name: str = typer.Option(None, "--name", help="Name of specific schedule to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
) -> list[dict[str, Any]] | dict[str, Any] | None:
    """Show schedule details.

    Examples
    --------
        # List all schedules (default behavior)
        scm show object schedule

        # Show a specific schedule by name
        scm show object schedule --name BusinessHours

    """
    # Determine container location
    if not any([folder, snippet, device]):
        folder = "Texas"  # Default to Texas folder

    if name:
        # Show specific schedule
        schedule = scm_client.get_schedule(
            name=name,
            folder=folder,
            snippet=snippet,
            device=device,
        )

        if not schedule:
            error(f"Schedule '{name}' not found")
            raise typer.Exit(code=1)

        emit(schedule, output, title=f"Schedule: {schedule.get('name', name)}")
        return schedule

    # Default behavior: list all schedules
    schedules = scm_client.list_schedules(
        folder=folder,
        snippet=snippet,
        device=device,
    )
    emit(
        schedules,
        output,
        columns=["name", "folder", "schedule_type"],
        title="Schedules",
    )
    return schedules or None


# =============================================================================================================================================================================================
# TAG COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("tag", help="Export tags to a YAML file.")
@handle_command_errors("backing up tags")
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
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # List all tags based on location type
    info(f"Retrieving tags from {location_type} '{location_value}'...")

    # Build kwargs based on location type
    kwargs = {location_type: location_value}
    tags = scm_client.list_tags(**kwargs)

    if not tags:
        info(f"No tags found in {location_type} '{location_value}'")
        return

    # Prepare data for export
    export_data = {"tags": tags}

    # Generate filename if not provided
    filename = Path(file or get_default_backup_filename("tag", location_type, location_value))

    # Write to file
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w") as f:
        yaml.dump(export_data, f, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(tags)} tags to {filename}")


@delete_app.command("tag", help="Delete a tag.")
@handle_command_errors("deleting tag")
def delete_tag(
    name: str = typer.Option(..., "--name", help="Name of the tag to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete a tag.

    Examples
    --------
        scm delete object tag --name production --folder Texas

    """
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
        error(f"Tag '{name}' not found")
        raise typer.Exit(code=1)

    # Confirm deletion
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete tag '{name}'?")
        if not confirm:
            info("Deletion cancelled")
            raise typer.Exit(code=0)

    # Delete the tag
    scm_client.delete_tag(
        name=name,
        folder=folder,
        snippet=snippet,
        device=device,
    )

    container = folder or snippet or device
    success(f"Deleted tag: {name} from {container}")


@load_app.command("tag", help="Load tags from a YAML file.")
@handle_command_errors("loading tags")
def load_tag(
    file: str = typer.Option(..., "--file", "-f", help="Input YAML file path"),
    folder: str = typer.Option(None, "--folder", help="Override folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Override snippet location"),
    device: str = typer.Option(None, "--device", help="Override device location"),
) -> None:
    """Load tags from a YAML file."""
    # Validate file exists
    if not Path(file).exists():
        error(f"File not found: {file}")
        raise typer.Exit(code=1)

    # Load YAML data
    with Path(file).open() as f:
        data = yaml.safe_load(f)

    if not data or "tags" not in data:
        error("No tags found in file")
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
            success(f"Created tag: {validated_tag.name} in {container}")

        except Exception as e:
            error(f"Error processing tag: {str(e)}")
            continue

    success(f"Summary: Processed {created_count} tags")


@set_app.command("tag", help="Create or update a tag.")
@handle_command_errors("creating/updating tag")
def set_tag(
    name: str = typer.Option(..., "--name", help="Name of the tag"),
    color: str = typer.Option(None, "--color", help="Color for the tag (e.g., Red, Blue, Green)"),
    comments: str = typer.Option(None, "--comments", help="Comments for the tag"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
) -> None:
    """Create or update a tag."""
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
        success(f"Created tag: {name} in {container}")
    elif action == "updated":
        success(f"Updated tag: {name} in {container}")
    elif action == "no_change":
        info(f"No changes needed for tag: {name} in {container}")


@show_app.command("tag", help="Show tag details.")
@handle_command_errors("showing tag")
def show_tag(
    name: str = typer.Option(None, "--name", help="Name of specific tag to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
) -> list[dict[str, Any]] | dict[str, Any] | None:
    """Show tag details.

    Examples
    --------
        # List all tags (default behavior)
        scm show object tag

        # Show a specific tag by name
        scm show object tag --name Production

    """
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
            error(f"Tag '{name}' not found")
            raise typer.Exit(code=1)

        emit(tag, output, title=f"Tag: {tag.get('name', name)}")
        return tag

    # Default behavior: list all tags
    tags = scm_client.list_tags(
        folder=folder,
        snippet=snippet,
        device=device,
    )
    emit(
        tags,
        output,
        columns=["name", "folder", "color", "comments"],
        title="Tags",
    )
    return tags or None


# =============================================================================================================================================================================================
# AUTO TAG ACTION COMMANDS
# =============================================================================================================================================================================================


@set_app.command("auto-tag-action", help="Create or update an auto tag action.")
@handle_command_errors("creating/updating auto tag action")
def set_auto_tag_action(
    name: str = typer.Argument(..., help="Name of the auto tag action"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    description: str = typer.Option(None, "--description", help="Description"),
    log_type: str = typer.Option(None, "--log-type", help="Log type (traffic, threat, etc.)"),
    filter_expr: str = typer.Option(None, "--filter", help="Filter expression"),
    tags: list[str] = TAGS_OPTION,
    send_to_panorama: bool = typer.Option(None, "--send-to-panorama", help="Send to Panorama"),
    quarantine: bool = typer.Option(None, "--quarantine", help="Enable quarantine"),
) -> None:
    """Create or update an auto tag action."""
    if not any([folder, snippet, device]):
        folder = "Texas"

    tag_data: dict[str, Any] = {"name": name}
    if folder:
        tag_data["folder"] = folder
    elif snippet:
        tag_data["snippet"] = snippet
    elif device:
        tag_data["device"] = device
    if description:
        tag_data["description"] = description
    if log_type:
        tag_data["log_type"] = log_type
    if filter_expr:
        tag_data["filter"] = filter_expr
    if tags:
        tag_data["tags"] = tags
    if send_to_panorama is not None:
        tag_data["send_to_panorama"] = send_to_panorama
    if quarantine is not None:
        tag_data["quarantine"] = quarantine

    validated = AutoTagAction(**tag_data)
    sdk_data = validated.to_sdk_model()

    result = scm_client.create_auto_tag_action(sdk_data)
    action = result.pop("__action__", "created")

    container = folder or snippet or device
    if action == "created":
        success(f"Created auto tag action: {name} in {container}")
    elif action == "updated":
        success(f"Updated auto tag action: {name} in {container}")
    elif action == "no_change":
        info(f"No changes needed for auto tag action: {name} in {container}")


@delete_app.command("auto-tag-action", help="Delete an auto tag action.")
@handle_command_errors("deleting auto tag action")
def delete_auto_tag_action(
    name: str = typer.Argument(..., help="Name of the auto tag action to delete"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
) -> None:
    """Delete an auto tag action."""
    if not any([folder, snippet, device]):
        folder = "Texas"

    location_type = "folder" if folder else ("snippet" if snippet else "device")
    location_value = folder or snippet or device

    if not force:
        confirm = typer.confirm(f"Delete auto tag action '{name}' from {location_type} '{location_value}'?")
        if not confirm:
            raise typer.Abort()

    scm_client.delete_auto_tag_action(
        name=name,
        folder=folder,
        snippet=snippet,
        device=device,
    )
    container = folder or snippet or device
    success(f"Deleted auto tag action: {name} from {container}")


@load_app.command("auto-tag-action", help="Load auto tag actions from a YAML file.")
@handle_command_errors("loading auto tag actions")
def load_auto_tag_action(
    file: str = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
) -> None:
    """Load auto tag actions from a YAML file."""
    if not file:
        error("Error: --file is required")
        raise typer.Exit(code=1)

    file_path = Path(file)
    if not file_path.exists():
        error(f"Error: File not found: {file}")
        raise typer.Exit(code=1)

    with open(file_path) as f:
        config = yaml.safe_load(f)

    if "auto_tag_actions" not in config:
        error("Error: Missing 'auto_tag_actions' section in YAML file")
        raise typer.Exit(code=1)

    created_count = 0
    for entry in config["auto_tag_actions"]:
        try:
            validated = AutoTagAction(**entry)
            sdk_data = validated.to_sdk_model()

            if dry_run:
                info(f"[DRY RUN] Would create auto tag action: {validated.name}")
                created_count += 1
                continue

            scm_client.create_auto_tag_action(sdk_data)
            created_count += 1
            container = entry.get("folder") or entry.get("snippet") or entry.get("device")
            success(f"Created auto tag action: {validated.name} in {container}")

        except Exception as e:
            error(f"Error processing auto tag action: {str(e)}")
            continue

    success(f"Summary: Processed {created_count} auto tag actions")


@show_app.command("auto-tag-action", help="Show auto tag action details.")
@handle_command_errors("showing auto tag action")
def show_auto_tag_action(
    name: str = typer.Option(None, "--name", help="Name of specific auto tag action to show"),
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    output: OutputFormat = OUTPUT_OPTION,
) -> list[dict[str, Any]] | dict[str, Any] | None:
    """Show auto tag action details.

    Examples
    --------
        scm show object auto-tag-action --folder Texas
        scm show object auto-tag-action --folder Texas --name my-action

    """
    if not any([folder, snippet, device]):
        folder = "Texas"

    if name:
        action = scm_client.get_auto_tag_action(
            name=name,
            folder=folder,
            snippet=snippet,
            device=device,
        )

        if not action:
            error(f"Auto tag action '{name}' not found")
            raise typer.Exit(code=1)

        emit(action, output, title=f"Auto Tag Action: {action.get('name', name)}")
        return action

    actions = scm_client.list_auto_tag_actions(
        folder=folder,
        snippet=snippet,
        device=device,
    )
    emit(
        actions,
        output,
        columns=["name", "folder", "log_type", "filter", "description"],
        title="Auto Tag Actions",
    )
    return actions or None


@backup_app.command("auto-tag-action", help="Backup auto tag actions to YAML.")
@handle_command_errors("backing up auto tag actions")
def backup_auto_tag_action(
    folder: str = typer.Option(None, "--folder", help="Folder location"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet location"),
    device: str = typer.Option(None, "--device", help="Device location"),
    file: str = typer.Option(None, "--file", help="Output file path"),
) -> None:
    """Backup auto tag actions to a YAML file."""
    if not any([folder, snippet, device]):
        folder = "Texas"

    actions = scm_client.list_auto_tag_actions(
        folder=folder,
        snippet=snippet,
        device=device,
        exact_match=True,
    )

    if not actions:
        container = folder or snippet or device
        info(f"No auto tag actions found in {container}")
        return

    backup_data = []
    for action in actions:
        action_dict = action.copy()
        action_dict.pop("id", None)
        backup_data.append(action_dict)

    yaml_data = {"auto_tag_actions": backup_data}

    if not file:
        from datetime import datetime

        container = folder or snippet or device
        safe_name = container.lower().replace(" ", "-").replace("/", "-")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file = f"auto-tag-actions_{safe_name}_{timestamp}.yaml"

    with open(file, "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    success(f"Backed up {len(backup_data)} auto tag actions to {file}")
