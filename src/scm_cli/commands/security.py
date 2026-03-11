"""Security module commands for scm.

This module implements set, delete, and load commands for security-related
configurations such as security rules, profiles, etc.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import typer
import yaml

from ..utils import parse_comma_separated_list
from ..utils.sdk_client import scm_client
from ..utils.validators import (
    AntiSpywareProfile,
    AppOverrideRule,
    AuthenticationRule,
    DecryptionProfile,
    DecryptionRule,
    DNSSecurityProfile,
    SecurityRule,
    URLAccessProfile,
    URLCategory,
    VulnerabilityProtectionProfile,
    WildfireAntivirusProfile,
)

# ========================================================================================================================================================================================
# TYPER APP CONFIGURATION
# ========================================================================================================================================================================================

# Create app groups for each action type
set_app = typer.Typer(help="Create or update security configurations")
delete_app = typer.Typer(help="Remove security configurations")
load_app = typer.Typer(help="Load security configurations from YAML files")
show_app = typer.Typer(help="Display security configurations")
backup_app = typer.Typer(help="Backup security configurations to YAML files")
move_app = typer.Typer(help="Move security rules to a new position")

# ========================================================================================================================================================================================
# COMMAND OPTIONS
# ========================================================================================================================================================================================

# Common options
FOLDER_OPTION = typer.Option(
    ...,
    "--folder",
    help="Folder path for the security rule",
)
SNIPPET_OPTION = typer.Option(
    None,
    "--snippet",
    help="Snippet path for the security rule",
)
DEVICE_OPTION = typer.Option(
    None,
    "--device",
    help="Device path for the security rule",
)
NAME_OPTION = typer.Option(
    ...,
    "--name",
    help="Name of the security rule",
)
FILE_OPTION = typer.Option(
    ...,
    "--file",
    help="Path to YAML file containing configurations",
)
DRY_RUN_OPTION = typer.Option(
    False,
    "--dry-run",
    help="Show what would be done without making changes",
)
RULEBASE_OPTION = typer.Option(
    "pre",
    "--rulebase",
    help="Rulebase to use (pre, post, or default)",
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

# Set command options
SOURCE_ZONES_OPTION = typer.Option(
    ...,
    "--source-zones",
    help="List of source zones",
)
DESTINATION_ZONES_OPTION = typer.Option(
    ...,
    "--destination-zones",
    help="List of destination zones",
)
SOURCE_ADDRESSES_OPTION = typer.Option(
    None,
    "--source-addresses",
    help="List of source addresses",
)
DESTINATION_ADDRESSES_OPTION = typer.Option(
    None,
    "--destination-addresses",
    help="List of destination addresses",
)
APPLICATIONS_OPTION = typer.Option(
    None,
    "--applications",
    help="List of applications",
)
SERVICES_OPTION = typer.Option(
    None,
    "--services",
    help="List of services",
)
ACTION_OPTION = typer.Option(
    "allow",
    "--action",
    help="Action (allow, deny, drop)",
)
DESCRIPTION_OPTION = typer.Option(
    None,
    "--description",
    help="Description of the security rule",
)
TAGS_OPTION = typer.Option(
    None,
    "--tags",
    help="List of tags",
)
ENABLED_OPTION = typer.Option(
    True,
    "--enabled/--disabled",
    help="Enable or disable the security rule",
)
LOG_START_OPTION = typer.Option(
    False,
    "--log-start",
    help="Log at session start",
)
LOG_END_OPTION = typer.Option(
    False,
    "--log-end",
    help="Log at session end",
)
LOG_SETTING_OPTION = typer.Option(
    None,
    "--log-setting",
    help="Log forwarding profile",
)

# Load command options (container overrides)
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

URL_CATEGORY_URLS_OPTION = typer.Option(None, "--url", help="URL entries for the category")
APP_OVERRIDE_SOURCE_ZONES_OPTION = typer.Option(None, "--source-zones", help="Source zones")
APP_OVERRIDE_DEST_ZONES_OPTION = typer.Option(None, "--destination-zones", help="Destination zones")
AUTH_RULE_SOURCE_ZONES_OPTION = typer.Option(None, "--source-zones", help="Source zones")
AUTH_RULE_DEST_ZONES_OPTION = typer.Option(None, "--destination-zones", help="Destination zones")
AUTH_RULE_SERVICE_OPTION = typer.Option(None, "--service", help="Services")
AUTH_RULE_CATEGORY_OPTION = typer.Option(None, "--category", help="URL categories")
DECRYPT_RULE_SOURCE_ZONES_OPTION = typer.Option(None, "--source-zones", help="Source zones")
DECRYPT_RULE_DEST_ZONES_OPTION = typer.Option(None, "--destination-zones", help="Destination zones")
URL_PROFILE_BLOCK_OPTION = typer.Option(None, "--block", help="URL categories to block")
URL_PROFILE_ALERT_OPTION = typer.Option(None, "--alert", help="URL categories to alert")
URL_PROFILE_ALLOW_OPTION = typer.Option(None, "--allow", help="URL categories to allow")

# ========================================================================================================================================================================================
# HELPER FUNCTIONS
# ========================================================================================================================================================================================


def validate_location_params(
    folder: str = None,
    snippet: str = None,
    device: str = None,
) -> tuple[str, str]:
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


def get_default_backup_filename(
    object_type: str,
    location_type: str,
    location_value: str,
    rulebase: str = None,
) -> str:
    """Generate default backup filename.

    Args:
        object_type: Type of object (e.g., "security-rules")
        location_type: Type of location (folder, snippet, device)
        location_value: Value of the location
        rulebase: Optional rulebase for security rules

    Returns:
        str: Default filename

    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_location = location_value.lower().replace(" ", "-").replace("/", "-")
    if rulebase:
        return f"{object_type}_{location_type}_{safe_location}_{rulebase}_{timestamp}.yaml"
    return f"{object_type}_{location_type}_{safe_location}_{timestamp}.yaml"


# ========================================================================================================================================================================================
# SECURITY RULE COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("rule")
def backup_security_rule(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: str = BACKUP_FILE_OPTION,
    rulebase: str = RULEBASE_OPTION,
):
    """Backup all security rules from a container and rulebase to a YAML file.

    Examples:
        # Backup from folder
        scm backup security rule --folder Austin --rulebase pre

        # Backup from snippet
        scm backup security rule --snippet DNS-Best-Practice --rulebase post

        # Backup from device
        scm backup security rule --device austin-01 --rulebase default

        # Backup to custom filename
        scm backup security rule --folder Austin --file my-rules.yaml

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Set default filename if not provided
    if not file:
        file = get_default_backup_filename("security-rules", location_type, location_value, rulebase)

    try:
        # List all security rules with exact_match=True using kwargs pattern
        kwargs = {location_type: location_value}
        rules = scm_client.list_security_rules(**kwargs, rulebase=rulebase, exact_match=True)

        if not rules:
            typer.echo(f"No security rules found in {location_type} '{location_value}' rulebase '{rulebase}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for rule in rules:
            # The list method already returns dicts with exclude_unset=True
            rule_dict = rule.copy()
            # Remove system fields that shouldn't be in backup
            rule_dict.pop("id", None)

            # Convert SDK format back to CLI format for consistency
            # Map SDK field names to CLI field names
            if "from_" in rule_dict:
                rule_dict["source_zones"] = rule_dict.pop("from_", [])
            if "to_" in rule_dict:
                rule_dict["destination_zones"] = rule_dict.pop("to_", [])
            if "source" in rule_dict:
                rule_dict["source_addresses"] = rule_dict.pop("source", [])
            if "destination" in rule_dict:
                rule_dict["destination_addresses"] = rule_dict.pop("destination", [])
            if "application" in rule_dict:
                rule_dict["applications"] = rule_dict.pop("application", [])

            # Convert disabled to enabled for CLI consistency
            if "disabled" in rule_dict:
                rule_dict["enabled"] = not rule_dict.pop("disabled", False)

            # Add rulebase info
            rule_dict["rulebase"] = rulebase

            backup_data.append(rule_dict)

        # Create the YAML structure
        yaml_data = {"security_rules": backup_data}

        # Write to YAML file
        with open(file, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} security rules to {file}")
        return file

    except NotImplementedError as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error backing up security rules: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("rule")
def delete_security_rule(
    folder: str = typer.Option(None, "--folder", help="Folder containing the security rule"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the security rule"),
    device: str = typer.Option(None, "--device", help="Device containing the security rule"),
    name: str = NAME_OPTION,
    rulebase: str = RULEBASE_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a security rule.

    Examples:
        # Delete from folder
        scm delete security rule --folder Texas --name test

        # Delete from snippet
        scm delete security rule --snippet DNS-Best-Practice --name block-dns

        # Delete from device
        scm delete security rule --device austin-01 --name local-rule

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    if not force:
        confirm = typer.confirm(f"Delete security rule '{name}' from {location_type} '{location_value}'?")
        if not confirm:
            raise typer.Abort()

    try:
        # For now, SDK only supports folder
        if location_type != "folder":
            typer.echo(
                f"Error: Deleting security rules from {location_type} is not yet supported by the SDK",
                err=True,
            )
            raise typer.Exit(code=1)

        result = scm_client.delete_security_rule(folder=location_value, name=name, rulebase=rulebase)
        if result:
            typer.echo(f"Deleted security rule: {name} from {location_type} {location_value} rulebase {rulebase}")
        else:
            typer.echo(
                f"Security rule not found: {name} in {location_type} {location_value}",
                err=True,
            )
            raise typer.Exit(code=1) from Exception
    except Exception as e:
        typer.echo(f"Error deleting security rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("rule", help="Load security rules from a YAML file.")
def load_security_rule(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load security rules from a YAML file.

    Examples:
        # Load from file with original locations
        scm load security rule --file config/security_rules.yml

        # Load with folder override
        scm load security rule --file config/security_rules.yml --folder Production

        # Load with snippet override
        scm load security rule --file config/security_rules.yml --snippet DNS-Rules

        # Dry run to preview changes
        scm load security rule --file config/security_rules.yml --dry-run

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

        if not raw_data or "security_rules" not in raw_data:
            typer.echo("No security rules found in file", err=True)
            raise typer.Exit(code=1)

        rules = raw_data["security_rules"]
        if not isinstance(rules, list):
            rules = [rules]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            # Show override information if applicable
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(rules))
            return []

        # Apply each security rule
        results = []
        created_count = 0
        updated_count = 0

        for rule_data in rules:
            try:
                # Apply container override if specified
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

                # Validate using the Pydantic model
                rule = SecurityRule(**rule_data)

                # For now, SDK only supports folder
                if hasattr(rule, "snippet") and rule.snippet:
                    typer.echo(
                        f"Warning: Creating security rules in snippets is not yet supported by the SDK. Skipping rule '{rule.name}'",
                        err=True,
                    )
                    continue
                elif hasattr(rule, "device") and rule.device:
                    typer.echo(
                        f"Warning: Creating security rules on devices is not yet supported by the SDK. Skipping rule '{rule.name}'",
                        err=True,
                    )
                    continue

                # Call the SDK client to create the security rule
                sdk_data = rule.to_sdk_model()
                result = scm_client.create_security_rule(
                    folder=sdk_data["folder"],
                    name=sdk_data["name"],
                    source_zones=sdk_data["source_zones"],
                    destination_zones=sdk_data["destination_zones"],
                    source_addresses=sdk_data["source_addresses"],
                    destination_addresses=sdk_data["destination_addresses"],
                    applications=sdk_data["applications"],
                    services=rule.service,  # Use the service field from the model
                    action=sdk_data["action"],
                    description=sdk_data["description"],
                    tags=sdk_data["tags"],
                    enabled=sdk_data["enabled"],
                    rulebase=sdk_data["rulebase"],
                    log_start=rule.log_start or False,
                    log_end=rule.log_end or False,
                    log_setting=rule.log_setting,
                )

                results.append(result)

                # Track if created or updated based on response
                if "created" in str(result).lower():
                    created_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                typer.echo(
                    f"Error processing security rule '{rule_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                # Continue processing other rules
                continue

        # Display summary with counts
        typer.echo(f"Successfully processed {len(results)} security rule(s):")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")

        return results

    except Exception as e:
        typer.echo(f"Error loading security rules: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("rule")
def set_security_rule(
    folder: str = typer.Option(None, "--folder", help="Folder path for the security rule"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet path for the security rule"),
    device: str = typer.Option(None, "--device", help="Device path for the security rule"),
    name: str = NAME_OPTION,
    source_zones: list[str] = SOURCE_ZONES_OPTION,
    destination_zones: list[str] = DESTINATION_ZONES_OPTION,
    source_addresses: list[str] | None = SOURCE_ADDRESSES_OPTION,
    destination_addresses: list[str] | None = DESTINATION_ADDRESSES_OPTION,
    applications: list[str] | None = APPLICATIONS_OPTION,
    services: list[str] | None = SERVICES_OPTION,
    action: str = ACTION_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    tags: list[str] | None = TAGS_OPTION,
    enabled: bool = ENABLED_OPTION,
    log_start: bool = LOG_START_OPTION,
    log_end: bool = LOG_END_OPTION,
    log_setting: str | None = LOG_SETTING_OPTION,
    rulebase: str = RULEBASE_OPTION,
):
    r"""Create or update a security rule.

    Examples:
        # Create basic rule
        scm set security rule --folder Texas --name test \\
            --source-zones trust --destination-zones untrust

        # Create rule with full options
        scm set security rule --folder Texas --name web-allow \\
            --source-zones trust --destination-zones untrust \\
            --source-addresses internal-net --destination-addresses any \\
            --applications web-browsing --applications ssl \\
            --services application-default \\
            --action allow --log-end \\
            --description "Allow web traffic" \\
            --tags web --tags production

        # Create rule in post rulebase
        scm set security rule --folder Texas --name cleanup \\
            --source-zones any --destination-zones any \\
            --action deny --log-start --log-end \\
            --rulebase post

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # For now, SDK only supports folder
    if location_type != "folder":
        typer.echo(
            f"Error: Creating security rules in {location_type} is not yet supported by the SDK",
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        # Parse comma-separated list options
        parsed_src_zones = parse_comma_separated_list(source_zones)
        parsed_dst_zones = parse_comma_separated_list(destination_zones)
        parsed_src_addrs = parse_comma_separated_list(source_addresses) if source_addresses else ["any"]
        parsed_dst_addrs = parse_comma_separated_list(destination_addresses) if destination_addresses else ["any"]
        parsed_apps = parse_comma_separated_list(applications) if applications else ["any"]
        parsed_svcs = parse_comma_separated_list(services) if services else ["any"]
        parsed_tags = parse_comma_separated_list(tags) if tags else []

        # Validate and create security rule
        rule = SecurityRule(
            folder=location_value,
            name=name,
            source_zones=parsed_src_zones,
            destination_zones=parsed_dst_zones,
            source_addresses=parsed_src_addrs,
            destination_addresses=parsed_dst_addrs,
            applications=parsed_apps,
            service=parsed_svcs,
            action=action,
            description=description or "",
            tags=parsed_tags,
            enabled=enabled,
            rulebase=rulebase,
            log_start=log_start,
            log_end=log_end,
            log_setting=log_setting,
            # Add optional fields with defaults
            tag=None,
            source_user=None,
            source_hip=None,
            destination_hip=None,
            category=None,
            negate_source=None,
            negate_destination=None,
        )

        # Call SDK client to create the rule
        result = scm_client.create_security_rule(
            folder=rule.folder,
            name=rule.name,
            source_zones=rule.source_zones,
            destination_zones=rule.destination_zones,
            source_addresses=rule.source_addresses,
            destination_addresses=rule.destination_addresses,
            applications=rule.applications,
            services=rule.service,
            action=rule.action,
            description=rule.description or "",
            tags=rule.tags,
            enabled=rule.enabled,
            rulebase=rule.rulebase,
            log_start=rule.log_start or False,
            log_end=rule.log_end or False,
            log_setting=rule.log_setting,
        )

        # Format and display output
        action = result.get("__action__", "created")
        if action == "created":
            typer.echo(f"Created security rule: {result['name']} in {location_type} {location_value}")
        elif action == "updated":
            typer.echo(f"Updated security rule: {result['name']} in {location_type} {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for security rule: {result['name']} in {location_type} {location_value}")

    except Exception as e:
        typer.echo(f"Error creating security rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("rule")
def show_security_rule(
    folder: str = typer.Option(None, "--folder", help="Folder containing the security rule"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the security rule"),
    device: str = typer.Option(None, "--device", help="Device containing the security rule"),
    rulebase: str = RULEBASE_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the security rule to show"),
    exclude_folder: list[str] | None = EXCLUDE_FOLDER_OPTION,
    exclude_snippet: list[str] | None = EXCLUDE_SNIPPET_OPTION,
    exclude_device: list[str] | None = EXCLUDE_DEVICE_OPTION,
):
    """Display security rules.

    Examples:
    --------
        # List all security rules in a folder and rulebase (default behavior)
        scm show security rule --folder Texas

        # List rules in post rulebase
        scm show security rule --folder Texas --rulebase post

        # Show a specific security rule by name
        scm show security rule --folder Texas --name "Allow Web Traffic"

        # List rules excluding specific folders
        scm show security rule --folder Texas --exclude-folder "All"

    Note:
    ----
        Security rules require both container and rulebase parameters.

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        if name:
            # For now, SDK only supports folder for get operations
            if location_type != "folder":
                typer.echo(
                    f"Error: Getting security rules from {location_type} is not yet supported by the SDK",
                    err=True,
                )
                raise typer.Exit(code=1)

            # Get a specific security rule by name
            rule = scm_client.get_security_rule(folder=location_value, name=name, rulebase=rulebase)

            typer.echo(f"\nSecurity Rule: {rule.get('name', 'N/A')}")
            typer.echo("=" * 80)

            # Display container location (folder, snippet, or device) and rulebase
            if rule.get("folder"):
                typer.echo(f"Location: Folder '{rule['folder']}' / Rulebase '{rulebase}'")
            elif rule.get("snippet"):
                typer.echo(f"Location: Snippet '{rule['snippet']}' / Rulebase '{rulebase}'")
            elif rule.get("device"):
                typer.echo(f"Location: Device '{rule['device']}' / Rulebase '{rulebase}'")
            else:
                typer.echo(f"Location: N/A / Rulebase '{rulebase}'")

            typer.echo(f"Action: {rule.get('action', 'N/A')}")

            # Display source zones
            source_zones = rule.get("from_", [])
            typer.echo(f"Source Zones: {', '.join(source_zones) if source_zones else 'any'}")

            # Display destination zones
            dest_zones = rule.get("to_", [])
            typer.echo(f"Destination Zones: {', '.join(dest_zones) if dest_zones else 'any'}")

            # Display source addresses
            source_addrs = rule.get("source", [])
            typer.echo(f"Source Addresses: {', '.join(source_addrs) if source_addrs else 'any'}")

            # Display destination addresses
            dest_addrs = rule.get("destination", [])
            typer.echo(f"Destination Addresses: {', '.join(dest_addrs) if dest_addrs else 'any'}")

            # Display applications
            apps = rule.get("application", [])
            typer.echo(f"Applications: {', '.join(apps) if apps else 'any'}")

            # Display services
            services = rule.get("service", [])
            typer.echo(f"Services: {', '.join(services) if services else 'any'}")

            # Display categories
            categories = rule.get("category", [])
            if categories:
                typer.echo(f"Categories: {', '.join(categories)}")

            # Display description if present
            if rule.get("description"):
                typer.echo(f"Description: {rule['description']}")

            # Display tags if present
            tags = rule.get("tag", [])
            if tags:
                typer.echo(f"Tags: {', '.join(tags)}")

            # Display enabled/disabled status
            disabled = rule.get("disabled", False)
            typer.echo(f"Status: {'Disabled' if disabled else 'Enabled'}")

            # Display logging settings
            if rule.get("log_start"):
                typer.echo("Log Start: Yes")
            if rule.get("log_end"):
                typer.echo("Log End: Yes")

            # Display log forwarding profile if present
            if rule.get("log_setting"):
                typer.echo(f"Log Forwarding Profile: {rule['log_setting']}")

            # Display security profiles if present
            profile_setting = rule.get("profile_setting")
            if profile_setting:
                typer.echo("Security Profiles:")
                if profile_setting.get("group"):
                    typer.echo(f"  Profile Group: {', '.join(profile_setting['group'])}")
                else:
                    # Individual profiles
                    for profile_type in [
                        "antivirus",
                        "anti_spyware",
                        "vulnerability",
                        "url_filtering",
                        "file_blocking",
                        "data_filtering",
                        "wildfire_analysis",
                    ]:
                        if profile_setting.get(profile_type):
                            profile_name = profile_type.replace("_", " ").title()
                            typer.echo(f"  {profile_name}: {profile_setting[profile_type]}")

            # Display ID if present
            if rule.get("id"):
                typer.echo(f"ID: {rule['id']}")

            return rule

        else:
            # Default behavior: list all
            # List all security rules in the specified container and rulebase (default behavior)
            kwargs = {location_type: location_value}
            rules = scm_client.list_security_rules(
                **kwargs,
                rulebase=rulebase,
                exclude_folders=exclude_folder or None,
                exclude_snippets=exclude_snippet or None,
                exclude_devices=exclude_device or None,
            )

            if not rules:
                typer.echo(f"No security rules found in {location_type} '{location_value}' rulebase '{rulebase}'")
                return

            typer.echo(f"\nSecurity Rules in {location_type} '{location_value}' rulebase '{rulebase}':")
            typer.echo("=" * 80)

            for rule in rules:
                # Display rule information
                typer.echo(f"Name: {rule.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device) and rulebase
                if rule.get("folder"):
                    typer.echo(f"  Location: Folder '{rule['folder']}' / Rulebase '{rulebase}'")
                elif rule.get("snippet"):
                    typer.echo(f"  Location: Snippet '{rule['snippet']}' / Rulebase '{rulebase}'")
                elif rule.get("device"):
                    typer.echo(f"  Location: Device '{rule['device']}' / Rulebase '{rulebase}'")
                else:
                    typer.echo(f"  Location: N/A / Rulebase '{rulebase}'")

                typer.echo(f"  Action: {rule.get('action', 'N/A')}")

                # Display source zones
                source_zones = rule.get("from_", [])
                typer.echo(f"  Source Zones: {', '.join(source_zones) if source_zones else 'any'}")

                # Display destination zones
                dest_zones = rule.get("to_", [])
                typer.echo(f"  Destination Zones: {', '.join(dest_zones) if dest_zones else 'any'}")

                # Display source addresses
                source_addrs = rule.get("source", [])
                typer.echo(f"  Source Addresses: {', '.join(source_addrs) if source_addrs else 'any'}")

                # Display destination addresses
                dest_addrs = rule.get("destination", [])
                typer.echo(f"  Destination Addresses: {', '.join(dest_addrs) if dest_addrs else 'any'}")

                # Display applications
                apps = rule.get("application", [])
                typer.echo(f"  Applications: {', '.join(apps) if apps else 'any'}")

                # Display services
                services = rule.get("service", [])
                typer.echo(f"  Services: {', '.join(services) if services else 'any'}")

                # Display description if present
                if rule.get("description"):
                    typer.echo(f"  Description: {rule['description']}")

                # Display tags if present
                tags = rule.get("tag", [])
                if tags:
                    typer.echo(f"  Tags: {', '.join(tags)}")

                # Display enabled/disabled status
                disabled = rule.get("disabled", False)
                typer.echo(f"  Status: {'Disabled' if disabled else 'Enabled'}")

                # Display ID if present
                if rule.get("id"):
                    typer.echo(f"  ID: {rule['id']}")

                typer.echo("-" * 80)

            return rules

    except Exception as e:
        typer.echo(f"Error showing security rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# ANTI-SPYWARE PROFILE COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("anti-spyware-profile")
def backup_anti_spyware_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: str = BACKUP_FILE_OPTION,
):
    """Backup all anti-spyware profiles from a container to a YAML file.

    Examples:
        # Backup from folder
        scm backup security anti-spyware-profile --folder Austin

        # Backup from snippet
        scm backup security anti-spyware-profile --snippet DNS-Best-Practice

        # Backup from device
        scm backup security anti-spyware-profile --device austin-01

        # Backup to custom filename
        scm backup security anti-spyware-profile --folder Austin --file my-profiles.yaml

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Set default filename if not provided
    if not file:
        file = get_default_backup_filename("anti-spyware-profiles", location_type, location_value)

    try:
        # List all anti-spyware profiles with exact_match=True using kwargs pattern
        kwargs = {location_type: location_value}
        profiles = scm_client.list_anti_spyware_profiles(**kwargs, exact_match=True)

        if not profiles:
            typer.echo(f"No anti-spyware profiles found in {location_type} '{location_value}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for profile in profiles:
            # The list method already returns dicts with exclude_unset=True
            profile_dict = profile.copy()
            # Remove system fields that shouldn't be in backup
            profile_dict.pop("id", None)

            backup_data.append(profile_dict)

        # Create the YAML structure
        yaml_data = {"anti_spyware_profiles": backup_data}

        # Write to YAML file
        with open(file, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} anti-spyware profiles to {file}")
        return file

    except Exception as e:
        typer.echo(f"Error backing up anti-spyware profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("anti-spyware-profile")
def delete_anti_spyware_profile(
    folder: str = typer.Option(None, "--folder", help="Folder containing the anti-spyware profile"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the anti-spyware profile"),
    device: str = typer.Option(None, "--device", help="Device containing the anti-spyware profile"),
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete an anti-spyware profile.

    Examples:
        # Delete from folder
        scm delete security anti-spyware-profile --folder Texas --name strict-security

        # Delete from snippet
        scm delete security anti-spyware-profile --snippet DNS-Best-Practice --name dns-protection

        # Delete from device
        scm delete security anti-spyware-profile --device austin-01 --name local-profile

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    if not force:
        confirm = typer.confirm(f"Delete anti-spyware profile '{name}' from {location_type} '{location_value}'?")
        if not confirm:
            raise typer.Abort()

    try:
        kwargs = {location_type: location_value}
        result = scm_client.delete_anti_spyware_profile(**kwargs, name=name)
        if result:
            typer.echo(f"Deleted anti-spyware profile: {name} from {location_type} {location_value}")
        else:
            typer.echo(
                f"Anti-spyware profile not found: {name} in {location_type} {location_value}",
                err=True,
            )
            raise typer.Exit(code=1) from Exception
    except Exception as e:
        typer.echo(f"Error deleting anti-spyware profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("anti-spyware-profile", help="Load anti-spyware profiles from a YAML file.")
def load_anti_spyware_profile(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load anti-spyware profiles from a YAML file.

    Examples:
        # Load from file with original locations
        scm load security anti-spyware-profile --file config/anti_spyware_profiles.yml

        # Load with folder override
        scm load security anti-spyware-profile --file config/anti_spyware_profiles.yml --folder Production

        # Load with snippet override
        scm load security anti-spyware-profile --file config/anti_spyware_profiles.yml --snippet Security-Best-Practice

        # Dry run to preview changes
        scm load security anti-spyware-profile --file config/anti_spyware_profiles.yml --dry-run

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

        if not raw_data or "anti_spyware_profiles" not in raw_data:
            typer.echo("No anti-spyware profiles found in file", err=True)
            raise typer.Exit(code=1)

        profiles = raw_data["anti_spyware_profiles"]
        if not isinstance(profiles, list):
            profiles = [profiles]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            # Show override information if applicable
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(profiles))
            return []

        # Apply each anti-spyware profile
        results = []
        created_count = 0
        updated_count = 0

        for profile_data in profiles:
            try:
                # Apply container override if specified
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

                # Validate using the Pydantic model
                profile = AntiSpywareProfile(**profile_data)

                # Call the SDK client to create the anti-spyware profile
                sdk_data = profile.to_sdk_model()

                # Extract container params
                container_kwargs = {}
                if sdk_data.get("folder"):
                    container_kwargs["folder"] = sdk_data.pop("folder")
                elif sdk_data.get("snippet"):
                    container_kwargs["snippet"] = sdk_data.pop("snippet")
                elif sdk_data.get("device"):
                    container_kwargs["device"] = sdk_data.pop("device")

                result = scm_client.create_anti_spyware_profile(**container_kwargs, **sdk_data)

                results.append(result)

                # Track if created or updated based on response
                if "created" in str(result).lower():
                    created_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                typer.echo(
                    f"Error processing anti-spyware profile '{profile_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                # Continue processing other profiles
                continue

        # Display summary with counts
        typer.echo(f"Successfully processed {len(results)} anti-spyware profile(s):")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")

        return results

    except Exception as e:
        typer.echo(f"Error loading anti-spyware profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("anti-spyware-profile")
def set_anti_spyware_profile(
    folder: str = typer.Option(None, "--folder", help="Folder path for the anti-spyware profile"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet path for the anti-spyware profile"),
    device: str = typer.Option(None, "--device", help="Device path for the anti-spyware profile"),
    name: str = NAME_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    cloud_inline_analysis: bool = typer.Option(
        False,
        "--cloud-inline-analysis/--no-cloud-inline-analysis",
        help="Enable cloud inline analysis",
    ),
    block_critical_high: bool = typer.Option(
        False,
        "--block-critical-high",
        help="Add default rule to block critical and high severity threats",
    ),
):
    r"""Create or update an anti-spyware profile.

    Examples:
        # Create basic profile in folder
        scm set security anti-spyware-profile --folder Texas --name strict-security \
            --description "Block critical threats"

        # Create profile with cloud inline analysis
        scm set security anti-spyware-profile --folder Texas --name cloud-protection \
            --cloud-inline-analysis

        # Create profile in snippet
        scm set security anti-spyware-profile --snippet Security-Best-Practice \
            --name standard-protection

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        # Validate and create anti-spyware profile
        profile_data: dict[str, Any] = {
            location_type: location_value,
            "name": name,
        }

        if description:
            profile_data["description"] = description
        if cloud_inline_analysis:
            profile_data["cloud_inline_analysis"] = cloud_inline_analysis

        # Add a default rule if requested or if no rules specified
        if block_critical_high:
            profile_data["rules"] = [
                {
                    "name": "Block Critical and High",
                    "severity": ["critical", "high"],
                    "category": "any",
                    "action": "block",
                    "packet_capture": "single-packet",
                }
            ]
        else:
            # Add a minimal default rule to satisfy SDK requirements
            profile_data["rules"] = [
                {
                    "name": "simple-critical",
                    "severity": ["critical"],
                    "category": "any",
                    "action": "block",
                }
            ]

        # AntiSpywareProfile expects specific field types
        # Ensure all fields have the correct types
        typed_profile_data = profile_data.copy()
        profile = AntiSpywareProfile(**typed_profile_data)

        # Call SDK client to create the profile
        sdk_data = profile.to_sdk_model()

        # Extract container params
        container_kwargs = {}
        if sdk_data.get("folder"):
            container_kwargs["folder"] = sdk_data.pop("folder")
        elif sdk_data.get("snippet"):
            container_kwargs["snippet"] = sdk_data.pop("snippet")
        elif sdk_data.get("device"):
            container_kwargs["device"] = sdk_data.pop("device")

        result = scm_client.create_anti_spyware_profile(**container_kwargs, **sdk_data)

        # Format and display output
        action = result.get("__action__", "created")
        if action == "created":
            typer.echo(f"Created anti-spyware profile: {result['name']} in {location_type} {location_value}")
        elif action == "updated":
            typer.echo(f"Updated anti-spyware profile: {result['name']} in {location_type} {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for anti-spyware profile: {result['name']} in {location_type} {location_value}")

    except Exception as e:
        typer.echo(f"Error creating anti-spyware profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("anti-spyware-profile")
def show_anti_spyware_profile(
    folder: str = typer.Option(None, "--folder", help="Folder containing the anti-spyware profile"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the anti-spyware profile"),
    device: str = typer.Option(None, "--device", help="Device containing the anti-spyware profile"),
    name: str | None = typer.Option(None, "--name", help="Name of the anti-spyware profile to show"),
):
    """Display anti-spyware profiles.

    Examples:
        # List all anti-spyware profiles in a folder (default behavior)
        scm show security anti-spyware-profile --folder Texas

        # Show a specific anti-spyware profile by name
        scm show security anti-spyware-profile --folder Texas --name strict-security

        # List profiles in snippet
        scm show security anti-spyware-profile --snippet Security-Best-Practice

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        if name:
            # Get a specific anti-spyware profile by name
            kwargs = {location_type: location_value}
            profile = scm_client.get_anti_spyware_profile(**kwargs, name=name)

            typer.echo(f"\nAnti-Spyware Profile: {profile.get('name', 'N/A')}")
            typer.echo("=" * 80)

            # Display container location (folder, snippet, or device)
            if profile.get("folder"):
                typer.echo(f"Location: Folder '{profile['folder']}'")
            elif profile.get("snippet"):
                typer.echo(f"Location: Snippet '{profile['snippet']}'")
            elif profile.get("device"):
                typer.echo(f"Location: Device '{profile['device']}'")

            # Display description if present
            if profile.get("description"):
                typer.echo(f"Description: {profile['description']}")

            # Display rules in detail
            if profile.get("rules"):
                typer.echo(f"\nRules ({len(profile['rules'])}):")
                for idx, rule in enumerate(profile["rules"], 1):
                    typer.echo(f"  Rule {idx}: {rule.get('name', 'Unnamed')}")
                    if rule.get("severity"):
                        severity = rule["severity"] if isinstance(rule["severity"], list) else [rule["severity"]]
                        typer.echo(f"    Severity: {', '.join(severity)}")
                    typer.echo(f"    Action: {rule.get('action', 'N/A')}")
                    if rule.get("category"):
                        typer.echo(f"    Category: {rule['category']}")
                    if rule.get("threat_name"):
                        typer.echo(f"    Threat Name: {rule['threat_name']}")
                    if rule.get("packet_capture"):
                        typer.echo(f"    Packet Capture: {rule['packet_capture']}")

            # Display cloud inline analysis setting
            if "cloud_inline_analysis" in profile:
                typer.echo(f"\nCloud Inline Analysis: {'Enabled' if profile['cloud_inline_analysis'] else 'Disabled'}")

            # Display threat exceptions in detail
            if profile.get("threat_exception"):
                typer.echo(f"\nThreat Exceptions ({len(profile['threat_exception'])}):")
                for idx, exception in enumerate(profile["threat_exception"], 1):
                    typer.echo(f"  Exception {idx}:")
                    if exception.get("name"):
                        typer.echo(f"    Name: {exception['name']}")
                    if exception.get("packet_capture"):
                        typer.echo(f"    Packet Capture: {exception['packet_capture']}")
                    if exception.get("action"):
                        typer.echo(f"    Action: {exception['action']}")
                    if exception.get("exempt_ip"):
                        typer.echo(f"    Exempt IPs: {', '.join(exception['exempt_ip'])}")

            # Display MICA engine settings if present
            if profile.get("mica_engine_spyware_enabled"):
                typer.echo("\nMICA Engine Settings:")
                for setting in profile["mica_engine_spyware_enabled"]:
                    if setting.get("name"):
                        typer.echo(f"  - {setting['name']}")
                        if setting.get("inline_policy_action"):
                            typer.echo(f"    Inline Policy Action: {setting['inline_policy_action']}")

            # Display ID if present
            if profile.get("id"):
                typer.echo(f"\nID: {profile['id']}")

            return profile

        else:
            # Default behavior: list all
            # List all anti-spyware profiles in the specified container (default behavior)
            kwargs = {location_type: location_value}
            profiles = scm_client.list_anti_spyware_profiles(**kwargs, exact_match=False)

            if not profiles:
                typer.echo(f"No anti-spyware profiles found in {location_type} '{location_value}'")
                return

            typer.echo(f"\nAnti-Spyware Profiles in {location_type} '{location_value}':")
            typer.echo("=" * 80)

            for profile in profiles:
                # Display profile information
                typer.echo(f"Name: {profile.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if profile.get("folder"):
                    typer.echo(f"  Location: Folder '{profile['folder']}'")
                elif profile.get("snippet"):
                    typer.echo(f"  Location: Snippet '{profile['snippet']}'")
                elif profile.get("device"):
                    typer.echo(f"  Location: Device '{profile['device']}'")

                # Display description if present
                if profile.get("description"):
                    typer.echo(f"  Description: {profile['description']}")

                # Display rules if present
                if profile.get("rules"):
                    typer.echo(f"  Rules: {len(profile['rules'])} configured")
                    for rule in profile["rules"]:
                        typer.echo(f"    - {rule.get('name', 'Unnamed')}: {rule.get('action', 'N/A')}")

                # Display cloud inline analysis setting
                if profile.get("cloud_inline_analysis"):
                    typer.echo("  Cloud Inline Analysis: Enabled")

                # Display threat exceptions if present
                if profile.get("threat_exception"):
                    typer.echo(f"  Threat Exceptions: {len(profile['threat_exception'])}")

                # Display MICA engine settings if present
                if profile.get("mica_engine_spyware_enabled"):
                    typer.echo("  MICA Engine: Configured")

                # Display ID if present
                if profile.get("id"):
                    typer.echo(f"  ID: {profile['id']}")

                typer.echo("-" * 80)

            return profiles

    except Exception as e:
        typer.echo(f"Error showing anti-spyware profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# DECRYPTION PROFILE COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("decryption-profile")
def backup_decryption_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: str = BACKUP_FILE_OPTION,
):
    """Backup all decryption profiles from a container to a YAML file.

    Examples:
        # Backup from folder
        scm backup security decryption-profile --folder Austin

        # Backup from snippet
        scm backup security decryption-profile --snippet DNS-Best-Practice

        # Backup from device
        scm backup security decryption-profile --device austin-01

        # Backup to custom filename
        scm backup security decryption-profile --folder Austin --file my-profiles.yaml

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Set default filename if not provided
    if not file:
        file = get_default_backup_filename("decryption-profiles", location_type, location_value)

    try:
        # List all decryption profiles with exact_match=True using kwargs pattern
        kwargs = {location_type: location_value}
        profiles = scm_client.list_decryption_profiles(**kwargs, exact_match=True)

        if not profiles:
            typer.echo(f"No decryption profiles found in {location_type} '{location_value}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for profile in profiles:
            # The list method already returns dicts with exclude_unset=True
            profile_dict = profile.copy()
            # Remove system fields that shouldn't be in backup
            profile_dict.pop("id", None)

            backup_data.append(profile_dict)

        # Create the YAML structure
        yaml_data = {"decryption_profiles": backup_data}

        # Write to YAML file
        with open(file, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} decryption profiles to {file}")
        return file

    except Exception as e:
        typer.echo(f"Error backing up decryption profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("decryption-profile")
def delete_decryption_profile(
    folder: str = typer.Option(None, "--folder", help="Folder containing the decryption profile"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the decryption profile"),
    device: str = typer.Option(None, "--device", help="Device containing the decryption profile"),
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a decryption profile.

    Examples:
        # Delete from folder
        scm delete security decryption-profile --folder Texas --name ssl-forward-proxy

        # Delete from snippet
        scm delete security decryption-profile --snippet DNS-Best-Practice --name ssl-inbound

        # Delete from device
        scm delete security decryption-profile --device austin-01 --name no-decrypt

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    if not force:
        confirm = typer.confirm(f"Delete decryption profile '{name}' from {location_type} '{location_value}'?")
        if not confirm:
            raise typer.Abort()

    try:
        kwargs = {location_type: location_value}
        result = scm_client.delete_decryption_profile(**kwargs, name=name)
        if result:
            typer.echo(f"Deleted decryption profile: {name} from {location_type} {location_value}")
        else:
            typer.echo(
                f"Decryption profile not found: {name} in {location_type} {location_value}",
                err=True,
            )
            raise typer.Exit(code=1) from Exception
    except Exception as e:
        typer.echo(f"Error deleting decryption profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("decryption-profile", help="Load decryption profiles from a YAML file.")
def load_decryption_profile(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load decryption profiles from a YAML file.

    Examples:
        # Load from file with original locations
        scm load security decryption-profile --file config/decryption_profiles.yml

        # Load with folder override
        scm load security decryption-profile --file config/decryption_profiles.yml --folder Production

        # Load with snippet override
        scm load security decryption-profile --file config/decryption_profiles.yml --snippet Security-Best-Practice

        # Dry run to preview changes
        scm load security decryption-profile --file config/decryption_profiles.yml --dry-run

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

        if not raw_data or "decryption_profiles" not in raw_data:
            typer.echo("No decryption profiles found in file", err=True)
            raise typer.Exit(code=1)

        profiles = raw_data["decryption_profiles"]
        if not isinstance(profiles, list):
            profiles = [profiles]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            # Show override information if applicable
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(profiles))
            return []

        # Apply each decryption profile
        results = []
        created_count = 0
        updated_count = 0

        for profile_data in profiles:
            try:
                # Apply container override if specified
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

                # Validate using the Pydantic model
                profile = DecryptionProfile(**profile_data)

                # Call the SDK client to create the decryption profile
                sdk_data = profile.to_sdk_model()

                # Extract container params
                container_kwargs = {}
                if sdk_data.get("folder"):
                    container_kwargs["folder"] = sdk_data.pop("folder")
                elif sdk_data.get("snippet"):
                    container_kwargs["snippet"] = sdk_data.pop("snippet")
                elif sdk_data.get("device"):
                    container_kwargs["device"] = sdk_data.pop("device")

                result = scm_client.create_decryption_profile(**container_kwargs, **sdk_data)

                results.append(result)

                # Track if created or updated based on response
                if "created" in str(result).lower():
                    created_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                typer.echo(
                    f"Error processing decryption profile '{profile_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                # Continue processing other profiles
                continue

        # Display summary with counts
        typer.echo(f"Successfully processed {len(results)} decryption profile(s):")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")

        return results

    except Exception as e:
        typer.echo(f"Error loading decryption profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("decryption-profile")
def set_decryption_profile(
    folder: str = typer.Option(None, "--folder", help="Folder path for the decryption profile"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet path for the decryption profile"),
    device: str = typer.Option(None, "--device", help="Device path for the decryption profile"),
    name: str = NAME_OPTION,
    description: str | None = typer.Option(
        None,
        "--description",
        help="Description of the decryption profile",
    ),
    ssl_forward_proxy: str | None = typer.Option(
        None,
        "--ssl-forward-proxy",
        help="SSL forward proxy settings as JSON string",
    ),
    ssl_inbound_proxy: str | None = typer.Option(
        None,
        "--ssl-inbound-proxy",
        help="SSL inbound proxy settings as JSON string",
    ),
    ssl_no_proxy: str | None = typer.Option(
        None,
        "--ssl-no-proxy",
        help="SSL no proxy settings as JSON string",
    ),
    ssl_protocol_settings: str | None = typer.Option(
        None,
        "--ssl-protocol-settings",
        help="SSL protocol settings as JSON string",
    ),
):
    r"""Create or update a decryption profile.

    Examples:
        # Create basic SSL forward proxy profile
        scm set security decryption-profile --folder Texas --name ssl-forward \
            --ssl-forward-proxy '{"block_expired_certificate": true, "block_untrusted_issuer": true}'

        # Create SSL inbound inspection profile
        scm set security decryption-profile --folder Texas --name ssl-inbound \
            --ssl-inbound-proxy '{"block_if_no_resource": true, "block_unsupported_cipher": true}'

        # Create no-decrypt profile
        scm set security decryption-profile --folder Texas --name no-decrypt \
            --ssl-no-proxy '{"block_expired_certificate": false, "block_untrusted_issuer": false}'

        # Create profile with protocol settings
        scm set security decryption-profile --folder Texas --name custom-decrypt \
            --ssl-forward-proxy '{"block_expired_certificate": true}' \
            --ssl-protocol-settings '{"min_version": "tls1-2", "max_version": "tls1-3"}'

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        # Build profile data
        profile_data: dict[str, Any] = {
            location_type: location_value,
            "name": name,
        }

        # Add optional description
        if description:
            profile_data["description"] = description

        # Parse JSON strings for proxy settings
        if ssl_forward_proxy:
            profile_data["ssl_forward_proxy"] = json.loads(ssl_forward_proxy)
        if ssl_inbound_proxy:
            profile_data["ssl_inbound_proxy"] = json.loads(ssl_inbound_proxy)
        if ssl_no_proxy:
            profile_data["ssl_no_proxy"] = json.loads(ssl_no_proxy)
        if ssl_protocol_settings:
            profile_data["ssl_protocol_settings"] = json.loads(ssl_protocol_settings)

        # Validate using the Pydantic model
        profile = DecryptionProfile(**profile_data)

        # Call SDK client to create the profile
        sdk_data = profile.to_sdk_model()

        # Extract container params
        container_kwargs = {}
        if sdk_data.get("folder"):
            container_kwargs["folder"] = sdk_data.pop("folder")
        elif sdk_data.get("snippet"):
            container_kwargs["snippet"] = sdk_data.pop("snippet")
        elif sdk_data.get("device"):
            container_kwargs["device"] = sdk_data.pop("device")

        result = scm_client.create_decryption_profile(**container_kwargs, **sdk_data)

        # Format and display output
        action = result.get("__action__", "created")
        if action == "created":
            typer.echo(f"Created decryption profile: {result['name']} in {location_type} {location_value}")
        elif action == "updated":
            typer.echo(f"Updated decryption profile: {result['name']} in {location_type} {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for decryption profile: {result['name']} in {location_type} {location_value}")

    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON settings: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating decryption profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("decryption-profile")
def show_decryption_profile(
    folder: str = typer.Option(None, "--folder", help="Folder containing the decryption profile"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the decryption profile"),
    device: str = typer.Option(None, "--device", help="Device containing the decryption profile"),
    name: str | None = typer.Option(None, "--name", help="Name of the decryption profile to show"),
):
    """Display decryption profiles.

    Examples:
        # List all decryption profiles in a folder (default behavior)
        scm show security decryption-profile --folder Texas

        # Show a specific decryption profile by name
        scm show security decryption-profile --folder Texas --name ssl-forward

        # List profiles in snippet
        scm show security decryption-profile --snippet Security-Best-Practice

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        if name:
            # Get a specific decryption profile by name
            kwargs = {location_type: location_value}
            profile = scm_client.get_decryption_profile(**kwargs, name=name)

            typer.echo(f"\nDecryption Profile: {profile.get('name', 'N/A')}")
            typer.echo("=" * 80)

            # Display container location (folder, snippet, or device)
            if profile.get("folder"):
                typer.echo(f"Location: Folder '{profile['folder']}'")
            elif profile.get("snippet"):
                typer.echo(f"Location: Snippet '{profile['snippet']}'")
            elif profile.get("device"):
                typer.echo(f"Location: Device '{profile['device']}'")

            # Display description if present
            if profile.get("description"):
                typer.echo(f"Description: {profile['description']}")

            # Display SSL Forward Proxy settings
            if profile.get("ssl_forward_proxy"):
                typer.echo("\nSSL Forward Proxy Settings:")
                proxy = profile["ssl_forward_proxy"]
                for key, value in proxy.items():
                    key_display = key.replace("_", " ").title()
                    typer.echo(f"  {key_display}: {value}")

            # Display SSL Inbound Proxy settings
            if profile.get("ssl_inbound_proxy"):
                typer.echo("\nSSL Inbound Proxy Settings:")
                proxy = profile["ssl_inbound_proxy"]
                for key, value in proxy.items():
                    key_display = key.replace("_", " ").title()
                    typer.echo(f"  {key_display}: {value}")

            # Display SSL No Proxy settings
            if profile.get("ssl_no_proxy"):
                typer.echo("\nSSL No Proxy Settings:")
                proxy = profile["ssl_no_proxy"]
                for key, value in proxy.items():
                    key_display = key.replace("_", " ").title()
                    typer.echo(f"  {key_display}: {value}")

            # Display SSL Protocol Settings
            if profile.get("ssl_protocol_settings"):
                typer.echo("\nSSL Protocol Settings:")
                settings = profile["ssl_protocol_settings"]
                for key, value in settings.items():
                    key_display = key.replace("_", " ").title()
                    typer.echo(f"  {key_display}: {value}")

            # Display ID if present
            if profile.get("id"):
                typer.echo(f"\nID: {profile['id']}")

            return profile

        else:
            # Default behavior: list all
            # List all decryption profiles in the specified container (default behavior)
            kwargs = {location_type: location_value}
            profiles = scm_client.list_decryption_profiles(**kwargs, exact_match=False)

            if not profiles:
                typer.echo(f"No decryption profiles found in {location_type} '{location_value}'")
                return

            typer.echo(f"\nDecryption Profiles in {location_type} '{location_value}':")
            typer.echo("=" * 80)

            for profile in profiles:
                # Display profile information
                typer.echo(f"Name: {profile.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if profile.get("folder"):
                    typer.echo(f"  Location: Folder '{profile['folder']}'")
                elif profile.get("snippet"):
                    typer.echo(f"  Location: Snippet '{profile['snippet']}'")
                elif profile.get("device"):
                    typer.echo(f"  Location: Device '{profile['device']}'")

                # Display description if present
                if profile.get("description"):
                    typer.echo(f"  Description: {profile['description']}")

                # Display proxy types configured
                proxy_types = []
                if profile.get("ssl_forward_proxy"):
                    proxy_types.append("SSL Forward Proxy")
                if profile.get("ssl_inbound_proxy"):
                    proxy_types.append("SSL Inbound Proxy")
                if profile.get("ssl_no_proxy"):
                    proxy_types.append("SSL No Proxy")

                if proxy_types:
                    typer.echo(f"  Proxy Types: {', '.join(proxy_types)}")

                # Display SSL protocol settings if present
                if profile.get("ssl_protocol_settings"):
                    settings = profile["ssl_protocol_settings"]
                    if "min_version" in settings or "max_version" in settings:
                        typer.echo(f"  SSL Versions: {settings.get('min_version', 'N/A')} - {settings.get('max_version', 'N/A')}")

                # Display ID if present
                if profile.get("id"):
                    typer.echo(f"  ID: {profile['id']}")

                typer.echo("-" * 80)

            return profiles

    except Exception as e:
        typer.echo(f"Error showing decryption profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# WILDFIRE ANTIVIRUS PROFILE COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("wildfire-antivirus-profile")
def backup_wildfire_antivirus_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: str = BACKUP_FILE_OPTION,
):
    """Backup all WildFire antivirus profiles from a container to a YAML file.

    Examples:
        # Backup from folder
        scm backup security wildfire-antivirus-profile --folder Austin

        # Backup from snippet
        scm backup security wildfire-antivirus-profile --snippet Security-Best-Practice

        # Backup from device
        scm backup security wildfire-antivirus-profile --device austin-01

        # Backup to custom filename
        scm backup security wildfire-antivirus-profile --folder Austin --file my-profiles.yaml

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Set default filename if not provided
    if not file:
        file = get_default_backup_filename("wildfire-antivirus-profiles", location_type, location_value)

    try:
        # List all WildFire antivirus profiles with exact_match=True using kwargs pattern
        kwargs = {location_type: location_value}
        profiles = scm_client.list_wildfire_antivirus_profiles(**kwargs, exact_match=True)

        if not profiles:
            typer.echo(f"No WildFire antivirus profiles found in {location_type} '{location_value}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for profile in profiles:
            # The list method already returns dicts with exclude_unset=True
            profile_dict = profile.copy()
            # Remove system fields that shouldn't be in backup
            profile_dict.pop("id", None)

            backup_data.append(profile_dict)

        # Create the YAML structure
        yaml_data = {"wildfire_antivirus_profiles": backup_data}

        # Write to YAML file
        with open(file, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} WildFire antivirus profiles to {file}")
        return file

    except Exception as e:
        typer.echo(f"Error backing up WildFire antivirus profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("wildfire-antivirus-profile")
def delete_wildfire_antivirus_profile(
    folder: str = typer.Option(None, "--folder", help="Folder containing the WildFire antivirus profile"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the WildFire antivirus profile"),
    device: str = typer.Option(None, "--device", help="Device containing the WildFire antivirus profile"),
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a WildFire antivirus profile.

    Examples:
        # Delete from folder
        scm delete security wildfire-antivirus-profile --folder Texas --name wf-strict

        # Delete from snippet
        scm delete security wildfire-antivirus-profile --snippet Security-Best-Practice --name wf-standard

        # Delete from device
        scm delete security wildfire-antivirus-profile --device austin-01 --name wf-local

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    if not force:
        confirm = typer.confirm(f"Delete WildFire antivirus profile '{name}' from {location_type} '{location_value}'?")
        if not confirm:
            raise typer.Abort()

    try:
        kwargs = {location_type: location_value}
        result = scm_client.delete_wildfire_antivirus_profile(**kwargs, name=name)
        if result:
            typer.echo(f"Deleted WildFire antivirus profile: {name} from {location_type} {location_value}")
        else:
            typer.echo(
                f"WildFire antivirus profile not found: {name} in {location_type} {location_value}",
                err=True,
            )
            raise typer.Exit(code=1) from Exception
    except Exception as e:
        typer.echo(f"Error deleting WildFire antivirus profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("wildfire-antivirus-profile", help="Load WildFire antivirus profiles from a YAML file.")
def load_wildfire_antivirus_profile(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load WildFire antivirus profiles from a YAML file.

    Examples:
        # Load from file with original locations
        scm load security wildfire-antivirus-profile --file config/wildfire_antivirus_profiles.yml

        # Load with folder override
        scm load security wildfire-antivirus-profile --file config/wildfire_antivirus_profiles.yml --folder Production

        # Load with snippet override
        scm load security wildfire-antivirus-profile --file config/wildfire_antivirus_profiles.yml --snippet Security-Best-Practice

        # Dry run to preview changes
        scm load security wildfire-antivirus-profile --file config/wildfire_antivirus_profiles.yml --dry-run

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

        if not raw_data or "wildfire_antivirus_profiles" not in raw_data:
            typer.echo("No WildFire antivirus profiles found in file", err=True)
            raise typer.Exit(code=1)

        profiles = raw_data["wildfire_antivirus_profiles"]
        if not isinstance(profiles, list):
            profiles = [profiles]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            # Show override information if applicable
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(profiles))
            return []

        # Apply each WildFire antivirus profile
        results = []
        created_count = 0
        updated_count = 0

        for profile_data in profiles:
            try:
                # Apply container override if specified
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

                # Validate using the Pydantic model
                profile = WildfireAntivirusProfile(**profile_data)

                # Call the SDK client to create the WildFire antivirus profile
                sdk_data = profile.to_sdk_model()

                # Extract container params
                container_kwargs = {}
                if sdk_data.get("folder"):
                    container_kwargs["folder"] = sdk_data.pop("folder")
                elif sdk_data.get("snippet"):
                    container_kwargs["snippet"] = sdk_data.pop("snippet")
                elif sdk_data.get("device"):
                    container_kwargs["device"] = sdk_data.pop("device")

                result = scm_client.create_wildfire_antivirus_profile(**container_kwargs, **sdk_data)

                results.append(result)

                # Track if created or updated based on response
                if "created" in str(result).lower():
                    created_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                typer.echo(
                    f"Error processing WildFire antivirus profile '{profile_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                # Continue processing other profiles
                continue

        # Display summary with counts
        typer.echo(f"Successfully processed {len(results)} WildFire antivirus profile(s):")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")

        return results

    except Exception as e:
        typer.echo(f"Error loading WildFire antivirus profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("wildfire-antivirus-profile")
def set_wildfire_antivirus_profile(
    folder: str = typer.Option(None, "--folder", help="Folder path for the WildFire antivirus profile"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet path for the WildFire antivirus profile"),
    device: str = typer.Option(None, "--device", help="Device path for the WildFire antivirus profile"),
    name: str = NAME_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    rules_json: str | None = typer.Option(
        None,
        "--rules",
        help="JSON string of rules configuration",
    ),
    packet_capture: bool = typer.Option(
        False,
        "--packet-capture/--no-packet-capture",
        help="Enable packet capture",
    ),
):
    r"""Create or update a WildFire antivirus profile.

    Examples:
        # Create basic profile in folder with default rule
        scm set security wildfire-antivirus-profile --folder Texas --name wf-basic \
            --description "Basic WildFire profile"

        # Create profile with custom rules (JSON)
        scm set security wildfire-antivirus-profile --folder Texas --name wf-custom \
            --rules '[{"name":"Forward All","direction":"both","analysis":"public-cloud","application":["any"],"file_type":["any"]}]'

        # Create profile with packet capture
        scm set security wildfire-antivirus-profile --folder Texas --name wf-capture \
            --packet-capture

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        # Validate and create WildFire antivirus profile
        profile_data: dict[str, Any] = {
            location_type: location_value,
            "name": name,
        }

        if description:
            profile_data["description"] = description
        if packet_capture:
            profile_data["packet_capture"] = packet_capture

        # Parse rules from JSON if provided
        if rules_json:
            try:
                profile_data["rules"] = json.loads(rules_json)
            except json.JSONDecodeError as e:
                typer.echo(f"Error parsing rules JSON: {str(e)}", err=True)
                raise typer.Exit(code=1) from e
        else:
            # Add a default rule
            profile_data["rules"] = [
                {
                    "name": "default-fwd",
                    "direction": "both",
                    "analysis": "public-cloud",
                    "application": ["any"],
                    "file_type": ["any"],
                }
            ]

        # Validate using the Pydantic model
        profile = WildfireAntivirusProfile(**profile_data)

        # Call SDK client to create the profile
        sdk_data = profile.to_sdk_model()

        # Extract container params
        container_kwargs = {}
        if sdk_data.get("folder"):
            container_kwargs["folder"] = sdk_data.pop("folder")
        elif sdk_data.get("snippet"):
            container_kwargs["snippet"] = sdk_data.pop("snippet")
        elif sdk_data.get("device"):
            container_kwargs["device"] = sdk_data.pop("device")

        result = scm_client.create_wildfire_antivirus_profile(**container_kwargs, **sdk_data)

        # Format and display output
        action = result.get("__action__", "created")
        if action == "created":
            typer.echo(f"Created WildFire antivirus profile: {result['name']} in {location_type} {location_value}")
        elif action == "updated":
            typer.echo(f"Updated WildFire antivirus profile: {result['name']} in {location_type} {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for WildFire antivirus profile: {result['name']} in {location_type} {location_value}")

    except Exception as e:
        typer.echo(f"Error creating WildFire antivirus profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("wildfire-antivirus-profile")
def show_wildfire_antivirus_profile(
    folder: str = typer.Option(None, "--folder", help="Folder containing the WildFire antivirus profile"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the WildFire antivirus profile"),
    device: str = typer.Option(None, "--device", help="Device containing the WildFire antivirus profile"),
    name: str | None = typer.Option(None, "--name", help="Name of the WildFire antivirus profile to show"),
):
    """Display WildFire antivirus profiles.

    Examples:
        # List all WildFire antivirus profiles in a folder (default behavior)
        scm show security wildfire-antivirus-profile --folder Texas

        # Show a specific profile by name
        scm show security wildfire-antivirus-profile --folder Texas --name wf-basic

        # List profiles in snippet
        scm show security wildfire-antivirus-profile --snippet Security-Best-Practice

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        if name:
            # Get a specific WildFire antivirus profile by name
            kwargs = {location_type: location_value}
            profile = scm_client.get_wildfire_antivirus_profile(**kwargs, name=name)

            typer.echo(f"\nWildFire Antivirus Profile: {profile.get('name', 'N/A')}")
            typer.echo("=" * 80)

            # Display container location (folder, snippet, or device)
            if profile.get("folder"):
                typer.echo(f"Location: Folder '{profile['folder']}'")
            elif profile.get("snippet"):
                typer.echo(f"Location: Snippet '{profile['snippet']}'")
            elif profile.get("device"):
                typer.echo(f"Location: Device '{profile['device']}'")

            # Display description if present
            if profile.get("description"):
                typer.echo(f"Description: {profile['description']}")

            # Display packet capture setting
            if "packet_capture" in profile:
                typer.echo(f"Packet Capture: {'Enabled' if profile['packet_capture'] else 'Disabled'}")

            # Display rules in detail
            if profile.get("rules"):
                typer.echo(f"\nRules ({len(profile['rules'])}):")
                for idx, rule in enumerate(profile["rules"], 1):
                    typer.echo(f"  Rule {idx}: {rule.get('name', 'Unnamed')}")
                    typer.echo(f"    Direction: {rule.get('direction', 'N/A')}")
                    if rule.get("analysis"):
                        typer.echo(f"    Analysis: {rule['analysis']}")
                    if rule.get("application"):
                        typer.echo(f"    Applications: {', '.join(rule['application'])}")
                    if rule.get("file_type"):
                        typer.echo(f"    File Types: {', '.join(rule['file_type'])}")

            # Display MLAV exceptions if present
            if profile.get("mlav_exception"):
                typer.echo(f"\nMLAV Exceptions ({len(profile['mlav_exception'])}):")
                for idx, exc in enumerate(profile["mlav_exception"], 1):
                    typer.echo(f"  Exception {idx}: {exc.get('name', 'Unnamed')}")
                    if exc.get("filename"):
                        typer.echo(f"    Filename: {exc['filename']}")
                    if exc.get("description"):
                        typer.echo(f"    Description: {exc['description']}")

            # Display threat exceptions if present
            if profile.get("threat_exception"):
                typer.echo(f"\nThreat Exceptions ({len(profile['threat_exception'])}):")
                for idx, exc in enumerate(profile["threat_exception"], 1):
                    typer.echo(f"  Exception {idx}: {exc.get('name', 'Unnamed')}")
                    if exc.get("notes"):
                        typer.echo(f"    Notes: {exc['notes']}")

            # Display ID if present
            if profile.get("id"):
                typer.echo(f"\nID: {profile['id']}")

            return profile

        else:
            # Default behavior: list all
            kwargs = {location_type: location_value}
            profiles = scm_client.list_wildfire_antivirus_profiles(**kwargs, exact_match=False)

            if not profiles:
                typer.echo(f"No WildFire antivirus profiles found in {location_type} '{location_value}'")
                return

            typer.echo(f"\nWildFire Antivirus Profiles in {location_type} '{location_value}':")
            typer.echo("=" * 80)

            for profile in profiles:
                # Display profile information
                typer.echo(f"Name: {profile.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if profile.get("folder"):
                    typer.echo(f"  Location: Folder '{profile['folder']}'")
                elif profile.get("snippet"):
                    typer.echo(f"  Location: Snippet '{profile['snippet']}'")
                elif profile.get("device"):
                    typer.echo(f"  Location: Device '{profile['device']}'")

                # Display description if present
                if profile.get("description"):
                    typer.echo(f"  Description: {profile['description']}")

                # Display rules if present
                if profile.get("rules"):
                    typer.echo(f"  Rules: {len(profile['rules'])} configured")
                    for rule in profile["rules"]:
                        typer.echo(f"    - {rule.get('name', 'Unnamed')}: {rule.get('direction', 'N/A')}")

                # Display packet capture setting
                if profile.get("packet_capture"):
                    typer.echo("  Packet Capture: Enabled")

                # Display threat exceptions if present
                if profile.get("threat_exception"):
                    typer.echo(f"  Threat Exceptions: {len(profile['threat_exception'])}")

                # Display MLAV exceptions if present
                if profile.get("mlav_exception"):
                    typer.echo(f"  MLAV Exceptions: {len(profile['mlav_exception'])}")

                # Display ID if present
                if profile.get("id"):
                    typer.echo(f"  ID: {profile['id']}")

                typer.echo("-" * 80)

            return profiles

    except Exception as e:
        typer.echo(f"Error showing WildFire antivirus profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# DNS SECURITY PROFILE COMMANDS
# ========================================================================================================================================================================================

# Module-level option constants for dns-security-profile list types (avoids B008 lint errors)
DNS_SEC_FOLDER_OPTION = typer.Option(None, "--folder", help="Folder containing the DNS security profile")
DNS_SEC_SNIPPET_OPTION = typer.Option(None, "--snippet", help="Snippet containing the DNS security profile")
DNS_SEC_DEVICE_OPTION = typer.Option(None, "--device", help="Device containing the DNS security profile")


@backup_app.command("dns-security-profile")
def backup_dns_security_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: str = BACKUP_FILE_OPTION,
):
    """Backup all DNS security profiles from a container to a YAML file.

    Examples:
        # Backup from folder
        scm backup security dns-security-profile --folder Austin

        # Backup from snippet
        scm backup security dns-security-profile --snippet DNS-Best-Practice

        # Backup to custom filename
        scm backup security dns-security-profile --folder Austin --file my-dns-profiles.yaml

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Set default filename if not provided
    if not file:
        file = get_default_backup_filename("dns-security-profiles", location_type, location_value)

    try:
        # List all DNS security profiles with exact_match=True using kwargs pattern
        kwargs = {location_type: location_value}
        profiles = scm_client.list_dns_security_profiles(**kwargs, exact_match=True)

        if not profiles:
            typer.echo(f"No DNS security profiles found in {location_type} '{location_value}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for profile in profiles:
            # The list method already returns dicts with exclude_unset=True
            profile_dict = profile.copy()
            # Remove system fields that shouldn't be in backup
            profile_dict.pop("id", None)

            backup_data.append(profile_dict)

        # Create the YAML structure
        yaml_data = {"dns_security_profiles": backup_data}

        # Write to YAML file
        with open(file, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} DNS security profiles to {file}")
        return file

    except Exception as e:
        typer.echo(f"Error backing up DNS security profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("dns-security-profile")
def delete_dns_security_profile(
    folder: str = DNS_SEC_FOLDER_OPTION,
    snippet: str = DNS_SEC_SNIPPET_OPTION,
    device: str = DNS_SEC_DEVICE_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a DNS security profile.

    Examples:
        # Delete from folder
        scm delete security dns-security-profile --folder Texas --name dns-sec-default

        # Delete from snippet
        scm delete security dns-security-profile --snippet DNS-Best-Practice --name dns-sec-strict

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    if not force:
        confirm = typer.confirm(f"Delete DNS security profile '{name}' from {location_type} '{location_value}'?")
        if not confirm:
            raise typer.Abort()

    try:
        kwargs = {location_type: location_value}
        result = scm_client.delete_dns_security_profile(**kwargs, name=name)
        if result:
            typer.echo(f"Deleted DNS security profile: {name} from {location_type} {location_value}")
        else:
            typer.echo(
                f"DNS security profile not found: {name} in {location_type} {location_value}",
                err=True,
            )
            raise typer.Exit(code=1) from Exception
    except Exception as e:
        typer.echo(f"Error deleting DNS security profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("dns-security-profile", help="Load DNS security profiles from a YAML file.")
def load_dns_security_profile(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load DNS security profiles from a YAML file.

    Examples:
        # Load from file with original locations
        scm load security dns-security-profile --file config/dns_security_profiles.yml

        # Load with folder override
        scm load security dns-security-profile --file config/dns_security_profiles.yml --folder Production

        # Dry run to preview changes
        scm load security dns-security-profile --file config/dns_security_profiles.yml --dry-run

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

        if not raw_data or "dns_security_profiles" not in raw_data:
            typer.echo("No DNS security profiles found in file", err=True)
            raise typer.Exit(code=1)

        profiles = raw_data["dns_security_profiles"]
        if not isinstance(profiles, list):
            profiles = [profiles]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            # Show override information if applicable
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(profiles))
            return []

        # Apply each DNS security profile
        results = []
        created_count = 0
        updated_count = 0

        for profile_data in profiles:
            try:
                # Apply container override if specified
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

                # Validate using the Pydantic model
                profile = DNSSecurityProfile(**profile_data)

                # Call the SDK client to create the DNS security profile
                sdk_data = profile.to_sdk_model()

                # Extract container params
                container_kwargs = {}
                if sdk_data.get("folder"):
                    container_kwargs["folder"] = sdk_data.pop("folder")
                elif sdk_data.get("snippet"):
                    container_kwargs["snippet"] = sdk_data.pop("snippet")
                elif sdk_data.get("device"):
                    container_kwargs["device"] = sdk_data.pop("device")

                result = scm_client.create_dns_security_profile(**container_kwargs, **sdk_data)

                results.append(result)

                # Track if created or updated based on __action__ field
                action = result.get("__action__", "")
                if action == "created":
                    created_count += 1
                elif action == "updated":
                    updated_count += 1

            except Exception as e:
                typer.echo(
                    f"Error processing DNS security profile '{profile_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                # Continue processing other profiles
                continue

        # Display summary with counts
        typer.echo(f"Successfully processed {len(results)} DNS security profile(s):")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")

        return results

    except Exception as e:
        typer.echo(f"Error loading DNS security profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("dns-security-profile")
def set_dns_security_profile(
    folder: str = typer.Option(None, "--folder", help="Folder path for the DNS security profile"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet path for the DNS security profile"),
    device: str = typer.Option(None, "--device", help="Device path for the DNS security profile"),
    name: str = NAME_OPTION,
    description: str | None = typer.Option(
        None,
        "--description",
        help="Description of the DNS security profile",
    ),
    botnet_domains: str | None = typer.Option(
        None,
        "--botnet-domains",
        help="Botnet domains settings as JSON string",
    ),
):
    r"""Create or update a DNS security profile.

    Examples:
        # Create basic DNS security profile with sinkhole
        scm set security dns-security-profile --folder Texas --name dns-sec-default \
            --botnet-domains '{"dns_security_categories": [{"name": "pan-dns-sec-malware", "action": "sinkhole"}]}'

        # Create profile with whitelist
        scm set security dns-security-profile --folder Texas --name dns-sec-custom \
            --botnet-domains '{"whitelist": [{"name": "example.com"}]}'

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        # Build profile data
        profile_data: dict[str, Any] = {
            location_type: location_value,
            "name": name,
        }

        # Add optional description
        if description:
            profile_data["description"] = description

        # Parse JSON string for botnet domains
        if botnet_domains:
            profile_data["botnet_domains"] = json.loads(botnet_domains)

        # Validate using the Pydantic model
        profile = DNSSecurityProfile(**profile_data)

        # Call SDK client to create the profile
        sdk_data = profile.to_sdk_model()

        # Extract container params
        container_kwargs = {}
        if sdk_data.get("folder"):
            container_kwargs["folder"] = sdk_data.pop("folder")
        elif sdk_data.get("snippet"):
            container_kwargs["snippet"] = sdk_data.pop("snippet")
        elif sdk_data.get("device"):
            container_kwargs["device"] = sdk_data.pop("device")

        result = scm_client.create_dns_security_profile(**container_kwargs, **sdk_data)

        # Format and display output based on action
        action = result.get("__action__", "created")
        if action == "updated":
            typer.echo(f"Updated DNS security profile: {result['name']} in {location_type} {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes to DNS security profile: {result['name']} in {location_type} {location_value}")
        else:
            typer.echo(f"Created DNS security profile: {result['name']} in {location_type} {location_value}")

    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON settings: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating DNS security profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("dns-security-profile")
def show_dns_security_profile(
    folder: str = DNS_SEC_FOLDER_OPTION,
    snippet: str = DNS_SEC_SNIPPET_OPTION,
    device: str = DNS_SEC_DEVICE_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the DNS security profile to show"),
):
    """Display DNS security profiles.

    Examples:
        # List all DNS security profiles in a folder (default behavior)
        scm show security dns-security-profile --folder Texas

        # Show a specific DNS security profile by name
        scm show security dns-security-profile --folder Texas --name dns-sec-default

        # List profiles in snippet
        scm show security dns-security-profile --snippet Security-Best-Practice

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        if name:
            # Get a specific DNS security profile by name
            kwargs = {location_type: location_value}
            profile = scm_client.get_dns_security_profile(**kwargs, name=name)

            typer.echo(f"\nDNS Security Profile: {profile.get('name', 'N/A')}")
            typer.echo("=" * 80)

            # Display container location (folder, snippet, or device)
            if profile.get("folder"):
                typer.echo(f"Location: Folder '{profile['folder']}'")
            elif profile.get("snippet"):
                typer.echo(f"Location: Snippet '{profile['snippet']}'")
            elif profile.get("device"):
                typer.echo(f"Location: Device '{profile['device']}'")

            # Display description if present
            if profile.get("description"):
                typer.echo(f"Description: {profile['description']}")

            # Display botnet domains settings
            botnet = profile.get("botnet_domains")
            if botnet:
                # Display DNS security categories
                categories = botnet.get("dns_security_categories")
                if categories:
                    typer.echo("\nDNS Security Categories:")
                    for cat in categories:
                        typer.echo(f"  Name: {cat.get('name', 'N/A')}")
                        typer.echo(f"    Action: {cat.get('action', 'N/A')}")
                        if cat.get("log_level"):
                            typer.echo(f"    Log Level: {cat['log_level']}")
                        if cat.get("packet_capture"):
                            typer.echo(f"    Packet Capture: {cat['packet_capture']}")

                # Display lists
                lists = botnet.get("lists")
                if lists:
                    typer.echo("\nDNS Lists:")
                    for lst in lists:
                        typer.echo(f"  Name: {lst.get('name', 'N/A')}")
                        if lst.get("action"):
                            typer.echo(f"    Action: {lst['action']}")
                        if lst.get("packet_capture"):
                            typer.echo(f"    Packet Capture: {lst['packet_capture']}")

                # Display sinkhole settings
                sinkhole = botnet.get("sinkhole")
                if sinkhole:
                    typer.echo("\nSinkhole Settings:")
                    typer.echo(f"  IPv4 Address: {sinkhole.get('ipv4_address', 'N/A')}")
                    typer.echo(f"  IPv6 Address: {sinkhole.get('ipv6_address', 'N/A')}")

                # Display whitelist
                whitelist = botnet.get("whitelist")
                if whitelist:
                    typer.echo("\nWhitelist:")
                    for entry in whitelist:
                        typer.echo(f"  Domain: {entry.get('name', 'N/A')}")
                        if entry.get("description"):
                            typer.echo(f"    Description: {entry['description']}")

            # Display ID if present
            if profile.get("id"):
                typer.echo(f"\nID: {profile['id']}")

            return profile

        else:
            # Default behavior: list all
            kwargs = {location_type: location_value}
            profiles = scm_client.list_dns_security_profiles(**kwargs, exact_match=False)

            if not profiles:
                typer.echo(f"No DNS security profiles found in {location_type} '{location_value}'")
                return

            typer.echo(f"\nDNS Security Profiles in {location_type} '{location_value}':")
            typer.echo("=" * 80)

            for profile in profiles:
                # Display profile information
                typer.echo(f"Name: {profile.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if profile.get("folder"):
                    typer.echo(f"  Location: Folder '{profile['folder']}'")
                elif profile.get("snippet"):
                    typer.echo(f"  Location: Snippet '{profile['snippet']}'")
                elif profile.get("device"):
                    typer.echo(f"  Location: Device '{profile['device']}'")

                # Display description if present
                if profile.get("description"):
                    typer.echo(f"  Description: {profile['description']}")

                # Display DNS security categories count
                botnet = profile.get("botnet_domains")
                if botnet:
                    categories = botnet.get("dns_security_categories")
                    if categories:
                        typer.echo(f"  DNS Security Categories: {len(categories)}")

                    # Show sinkhole config
                    if botnet.get("sinkhole"):
                        sinkhole = botnet["sinkhole"]
                        typer.echo(f"  Sinkhole: IPv4={sinkhole.get('ipv4_address', 'N/A')}, IPv6={sinkhole.get('ipv6_address', 'N/A')}")

                    # Show whitelist count
                    whitelist = botnet.get("whitelist")
                    if whitelist:
                        typer.echo(f"  Whitelist Entries: {len(whitelist)}")

                # Display ID if present
                if profile.get("id"):
                    typer.echo(f"  ID: {profile['id']}")

                typer.echo("-" * 80)

            return profiles

    except Exception as e:
        typer.echo(f"Error showing DNS security profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# VULNERABILITY PROTECTION PROFILE COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("vulnerability-protection-profile")
def backup_vulnerability_protection_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: str = BACKUP_FILE_OPTION,
):
    """Backup all vulnerability protection profiles from a container to a YAML file.

    Examples:
        # Backup from folder
        scm backup security vulnerability-protection-profile --folder Austin

        # Backup from snippet
        scm backup security vulnerability-protection-profile --snippet Security-Best-Practice

        # Backup from device
        scm backup security vulnerability-protection-profile --device austin-01

        # Backup to custom filename
        scm backup security vulnerability-protection-profile --folder Austin --file my-profiles.yaml

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Set default filename if not provided
    if not file:
        file = get_default_backup_filename("vulnerability-protection-profiles", location_type, location_value)

    try:
        # List all vulnerability protection profiles with exact_match=True using kwargs pattern
        kwargs = {location_type: location_value}
        profiles = scm_client.list_vulnerability_protection_profiles(**kwargs, exact_match=True)

        if not profiles:
            typer.echo(f"No vulnerability protection profiles found in {location_type} '{location_value}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for profile in profiles:
            # The list method already returns dicts with exclude_unset=True
            profile_dict = profile.copy()
            # Remove system fields that shouldn't be in backup
            profile_dict.pop("id", None)

            backup_data.append(profile_dict)

        # Create the YAML structure
        yaml_data = {"vulnerability_protection_profiles": backup_data}

        # Write to YAML file
        with open(file, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} vulnerability protection profiles to {file}")
        return file

    except Exception as e:
        typer.echo(f"Error backing up vulnerability protection profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("vulnerability-protection-profile")
def delete_vulnerability_protection_profile(
    folder: str = typer.Option(None, "--folder", help="Folder containing the vulnerability protection profile"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the vulnerability protection profile"),
    device: str = typer.Option(None, "--device", help="Device containing the vulnerability protection profile"),
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a vulnerability protection profile.

    Examples:
        # Delete from folder
        scm delete security vulnerability-protection-profile --folder Texas --name strict-vuln

        # Delete from snippet
        scm delete security vulnerability-protection-profile --snippet Security-Best-Practice --name vuln-protection

        # Delete from device
        scm delete security vulnerability-protection-profile --device austin-01 --name local-profile

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    if not force:
        confirm = typer.confirm(f"Delete vulnerability protection profile '{name}' from {location_type} '{location_value}'?")
        if not confirm:
            raise typer.Abort()

    try:
        kwargs = {location_type: location_value}
        result = scm_client.delete_vulnerability_protection_profile(**kwargs, name=name)
        if result:
            typer.echo(f"Deleted vulnerability protection profile: {name} from {location_type} {location_value}")
        else:
            typer.echo(
                f"Vulnerability protection profile not found: {name} in {location_type} {location_value}",
                err=True,
            )
            raise typer.Exit(code=1) from Exception
    except Exception as e:
        typer.echo(f"Error deleting vulnerability protection profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("vulnerability-protection-profile", help="Load vulnerability protection profiles from a YAML file.")
def load_vulnerability_protection_profile(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load vulnerability protection profiles from a YAML file.

    Examples:
        # Load from file with original locations
        scm load security vulnerability-protection-profile --file config/vuln_profiles.yml

        # Load with folder override
        scm load security vulnerability-protection-profile --file config/vuln_profiles.yml --folder Production

        # Load with snippet override
        scm load security vulnerability-protection-profile --file config/vuln_profiles.yml --snippet Security-Best-Practice

        # Dry run to preview changes
        scm load security vulnerability-protection-profile --file config/vuln_profiles.yml --dry-run

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

        if not raw_data or "vulnerability_protection_profiles" not in raw_data:
            typer.echo("No vulnerability protection profiles found in file", err=True)
            raise typer.Exit(code=1)

        profiles = raw_data["vulnerability_protection_profiles"]
        if not isinstance(profiles, list):
            profiles = [profiles]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            # Show override information if applicable
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(profiles))
            return []

        # Apply each vulnerability protection profile
        results = []
        created_count = 0
        updated_count = 0

        for profile_data in profiles:
            try:
                # Apply container override if specified
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

                # Validate using the Pydantic model
                profile = VulnerabilityProtectionProfile(**profile_data)

                # Call the SDK client to create the vulnerability protection profile
                sdk_data = profile.to_sdk_model()

                # Extract container params
                container_kwargs = {}
                if sdk_data.get("folder"):
                    container_kwargs["folder"] = sdk_data.pop("folder")
                elif sdk_data.get("snippet"):
                    container_kwargs["snippet"] = sdk_data.pop("snippet")
                elif sdk_data.get("device"):
                    container_kwargs["device"] = sdk_data.pop("device")

                result = scm_client.create_vulnerability_protection_profile(**container_kwargs, **sdk_data)

                results.append(result)

                # Track if created or updated based on response
                if "created" in str(result).lower():
                    created_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                typer.echo(
                    f"Error processing vulnerability protection profile '{profile_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                # Continue processing other profiles
                continue

        # Display summary with counts
        typer.echo(f"Successfully processed {len(results)} vulnerability protection profile(s):")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")

        return results

    except Exception as e:
        typer.echo(f"Error loading vulnerability protection profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("vulnerability-protection-profile")
def set_vulnerability_protection_profile(
    folder: str = typer.Option(None, "--folder", help="Folder path for the vulnerability protection profile"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet path for the vulnerability protection profile"),
    device: str = typer.Option(None, "--device", help="Device path for the vulnerability protection profile"),
    name: str = NAME_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    block_critical_high: bool = typer.Option(
        False,
        "--block-critical-high",
        help="Add default rule to block critical and high severity vulnerabilities",
    ),
):
    r"""Create or update a vulnerability protection profile.

    Examples:
        # Create basic profile in folder
        scm set security vulnerability-protection-profile --folder Texas --name strict-vuln \
            --description "Block critical vulnerabilities"

        # Create profile with block critical/high rule
        scm set security vulnerability-protection-profile --folder Texas --name vuln-protection \
            --block-critical-high

        # Create profile in snippet
        scm set security vulnerability-protection-profile --snippet Security-Best-Practice \
            --name standard-vuln

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        # Validate and create vulnerability protection profile
        profile_data: dict[str, Any] = {
            location_type: location_value,
            "name": name,
        }

        if description:
            profile_data["description"] = description

        # Add a default rule if requested or if no rules specified
        if block_critical_high:
            profile_data["rules"] = [
                {
                    "name": "Block Critical and High",
                    "severity": ["critical", "high"],
                    "category": "any",
                    "host": "any",
                    "cve": ["any"],
                    "vendor_id": ["any"],
                    "action": "alert",
                    "packet_capture": "single-packet",
                }
            ]
        else:
            # Add a minimal default rule to satisfy SDK requirements
            profile_data["rules"] = [
                {
                    "name": "simple-critical",
                    "severity": ["critical"],
                    "category": "any",
                    "host": "any",
                    "cve": ["any"],
                    "vendor_id": ["any"],
                    "action": "default",
                }
            ]

        # VulnerabilityProtectionProfile expects specific field types
        typed_profile_data = profile_data.copy()
        profile = VulnerabilityProtectionProfile(**typed_profile_data)

        # Call SDK client to create the profile
        sdk_data = profile.to_sdk_model()

        # Extract container params
        container_kwargs = {}
        if sdk_data.get("folder"):
            container_kwargs["folder"] = sdk_data.pop("folder")
        elif sdk_data.get("snippet"):
            container_kwargs["snippet"] = sdk_data.pop("snippet")
        elif sdk_data.get("device"):
            container_kwargs["device"] = sdk_data.pop("device")

        result = scm_client.create_vulnerability_protection_profile(**container_kwargs, **sdk_data)

        # Format and display output
        action = result.get("__action__", "created")
        if action == "created":
            typer.echo(f"Created vulnerability protection profile: {result['name']} in {location_type} {location_value}")
        elif action == "updated":
            typer.echo(f"Updated vulnerability protection profile: {result['name']} in {location_type} {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for vulnerability protection profile: {result['name']} in {location_type} {location_value}")

    except Exception as e:
        typer.echo(f"Error creating vulnerability protection profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("vulnerability-protection-profile")
def show_vulnerability_protection_profile(
    folder: str = typer.Option(None, "--folder", help="Folder containing the vulnerability protection profile"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the vulnerability protection profile"),
    device: str = typer.Option(None, "--device", help="Device containing the vulnerability protection profile"),
    name: str | None = typer.Option(None, "--name", help="Name of the vulnerability protection profile to show"),
):
    """Display vulnerability protection profiles.

    Examples:
        # List all vulnerability protection profiles in a folder (default behavior)
        scm show security vulnerability-protection-profile --folder Texas

        # Show a specific vulnerability protection profile by name
        scm show security vulnerability-protection-profile --folder Texas --name strict-vuln

        # List profiles in snippet
        scm show security vulnerability-protection-profile --snippet Security-Best-Practice

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        if name:
            # Get a specific vulnerability protection profile by name
            kwargs = {location_type: location_value}
            profile = scm_client.get_vulnerability_protection_profile(**kwargs, name=name)

            typer.echo(f"\nVulnerability Protection Profile: {profile.get('name', 'N/A')}")
            typer.echo("=" * 80)

            # Display container location (folder, snippet, or device)
            if profile.get("folder"):
                typer.echo(f"Location: Folder '{profile['folder']}'")
            elif profile.get("snippet"):
                typer.echo(f"Location: Snippet '{profile['snippet']}'")
            elif profile.get("device"):
                typer.echo(f"Location: Device '{profile['device']}'")

            # Display description if present
            if profile.get("description"):
                typer.echo(f"Description: {profile['description']}")

            # Display rules in detail
            if profile.get("rules"):
                typer.echo(f"\nRules ({len(profile['rules'])}):")
                for idx, rule in enumerate(profile["rules"], 1):
                    typer.echo(f"  Rule {idx}: {rule.get('name', 'Unnamed')}")
                    if rule.get("severity"):
                        severity = rule["severity"] if isinstance(rule["severity"], list) else [rule["severity"]]
                        typer.echo(f"    Severity: {', '.join(severity)}")
                    typer.echo(f"    Action: {rule.get('action', 'N/A')}")
                    if rule.get("category"):
                        typer.echo(f"    Category: {rule['category']}")
                    if rule.get("host"):
                        typer.echo(f"    Host: {rule['host']}")
                    if rule.get("threat_name"):
                        typer.echo(f"    Threat Name: {rule['threat_name']}")
                    if rule.get("packet_capture"):
                        typer.echo(f"    Packet Capture: {rule['packet_capture']}")
                    if rule.get("cve"):
                        typer.echo(f"    CVE: {', '.join(rule['cve'])}")
                    if rule.get("vendor_id") or rule.get("vendor-id"):
                        vendor_ids = rule.get("vendor_id") or rule.get("vendor-id")
                        typer.echo(f"    Vendor ID: {', '.join(vendor_ids)}")

            # Display threat exceptions in detail
            if profile.get("threat_exception"):
                typer.echo(f"\nThreat Exceptions ({len(profile['threat_exception'])}):")
                for idx, exception in enumerate(profile["threat_exception"], 1):
                    typer.echo(f"  Exception {idx}:")
                    if exception.get("name"):
                        typer.echo(f"    Name: {exception['name']}")
                    if exception.get("packet_capture"):
                        typer.echo(f"    Packet Capture: {exception['packet_capture']}")
                    if exception.get("action"):
                        typer.echo(f"    Action: {exception['action']}")
                    if exception.get("exempt_ip"):
                        ips = [ip.get("name", str(ip)) if isinstance(ip, dict) else str(ip) for ip in exception["exempt_ip"]]
                        typer.echo(f"    Exempt IPs: {', '.join(ips)}")
                    if exception.get("notes"):
                        typer.echo(f"    Notes: {exception['notes']}")
                    if exception.get("time_attribute"):
                        ta = exception["time_attribute"]
                        typer.echo(f"    Time Attribute: interval={ta.get('interval')}, threshold={ta.get('threshold')}, track_by={ta.get('track_by')}")

            # Display ID if present
            if profile.get("id"):
                typer.echo(f"\nID: {profile['id']}")

            return profile

        else:
            # Default behavior: list all
            kwargs = {location_type: location_value}
            profiles = scm_client.list_vulnerability_protection_profiles(**kwargs, exact_match=False)

            if not profiles:
                typer.echo(f"No vulnerability protection profiles found in {location_type} '{location_value}'")
                return

            typer.echo(f"\nVulnerability Protection Profiles in {location_type} '{location_value}':")
            typer.echo("=" * 80)

            for profile in profiles:
                # Display profile information
                typer.echo(f"Name: {profile.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if profile.get("folder"):
                    typer.echo(f"  Location: Folder '{profile['folder']}'")
                elif profile.get("snippet"):
                    typer.echo(f"  Location: Snippet '{profile['snippet']}'")
                elif profile.get("device"):
                    typer.echo(f"  Location: Device '{profile['device']}'")

                # Display description if present
                if profile.get("description"):
                    typer.echo(f"  Description: {profile['description']}")

                # Display rules if present
                if profile.get("rules"):
                    typer.echo(f"  Rules: {len(profile['rules'])} configured")
                    for rule in profile["rules"]:
                        typer.echo(f"    - {rule.get('name', 'Unnamed')}: {rule.get('action', 'N/A')}")

                # Display threat exceptions if present
                if profile.get("threat_exception"):
                    typer.echo(f"  Threat Exceptions: {len(profile['threat_exception'])}")

                # Display ID if present
                if profile.get("id"):
                    typer.echo(f"  ID: {profile['id']}")

                typer.echo("-" * 80)

            return profiles

    except Exception as e:
        typer.echo(f"Error showing vulnerability protection profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# URL CATEGORY COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("url-category")
def backup_url_category(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: str = BACKUP_FILE_OPTION,
):
    """Backup all URL categories from a container to a YAML file.

    Examples:
        # Backup from folder
        scm backup security url-category --folder Austin

        # Backup from snippet
        scm backup security url-category --snippet DNS-Best-Practice

        # Backup from device
        scm backup security url-category --device austin-01

        # Backup to custom filename
        scm backup security url-category --folder Austin --file my-url-categories.yaml

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Set default filename if not provided
    if not file:
        file = get_default_backup_filename("url-categories", location_type, location_value)

    try:
        # List all URL categories with exact_match=True using kwargs pattern
        kwargs = {location_type: location_value}
        categories = scm_client.list_url_categories(**kwargs, exact_match=True)

        if not categories:
            typer.echo(f"No URL categories found in {location_type} '{location_value}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for category in categories:
            category_dict = category.copy()
            # Remove system fields that shouldn't be in backup
            category_dict.pop("id", None)

            backup_data.append(category_dict)

        # Create the YAML structure
        yaml_data = {"url_categories": backup_data}

        # Write to YAML file
        with open(file, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} URL categories to {file}")
        return file

    except Exception as e:
        typer.echo(f"Error backing up URL categories: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("url-category")
def delete_url_category(
    folder: str = typer.Option(None, "--folder", help="Folder containing the URL category"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the URL category"),
    device: str = typer.Option(None, "--device", help="Device containing the URL category"),
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a URL category.

    Examples:
        # Delete from folder
        scm delete security url-category --folder Texas --name custom-block-list

        # Delete from snippet
        scm delete security url-category --snippet DNS-Best-Practice --name phishing-urls

        # Delete from device
        scm delete security url-category --device austin-01 --name local-blocklist

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    if not force:
        confirm = typer.confirm(f"Delete URL category '{name}' from {location_type} '{location_value}'?")
        if not confirm:
            raise typer.Abort()

    try:
        kwargs = {location_type: location_value}
        result = scm_client.delete_url_category(**kwargs, name=name)
        if result:
            typer.echo(f"Deleted URL category: {name} from {location_type} {location_value}")
        else:
            typer.echo(
                f"URL category not found: {name} in {location_type} {location_value}",
                err=True,
            )
            raise typer.Exit(code=1) from Exception
    except Exception as e:
        typer.echo(f"Error deleting URL category: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("url-category", help="Load URL categories from a YAML file.")
def load_url_category(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load URL categories from a YAML file.

    Examples:
        # Load from file with original locations
        scm load security url-category --file config/url_categories.yml

        # Load with folder override
        scm load security url-category --file config/url_categories.yml --folder Production

        # Load with snippet override
        scm load security url-category --file config/url_categories.yml --snippet Security-Best-Practice

        # Dry run to preview changes
        scm load security url-category --file config/url_categories.yml --dry-run

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

        if not raw_data or "url_categories" not in raw_data:
            typer.echo("No URL categories found in file", err=True)
            raise typer.Exit(code=1)

        categories = raw_data["url_categories"]
        if not isinstance(categories, list):
            categories = [categories]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            # Show override information if applicable
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(categories))
            return []

        # Apply each URL category
        results = []
        created_count = 0
        updated_count = 0

        for category_data in categories:
            try:
                # Apply container override if specified
                if folder:
                    category_data["folder"] = folder
                    category_data.pop("snippet", None)
                    category_data.pop("device", None)
                elif snippet:
                    category_data["snippet"] = snippet
                    category_data.pop("folder", None)
                    category_data.pop("device", None)
                elif device:
                    category_data["device"] = device
                    category_data.pop("folder", None)
                    category_data.pop("snippet", None)

                # Validate using the Pydantic model
                category = URLCategory(**category_data)

                # Call the SDK client to create the URL category
                sdk_data = category.to_sdk_model()

                # Extract container params
                container_kwargs = {}
                if sdk_data.get("folder"):
                    container_kwargs["folder"] = sdk_data.pop("folder")
                elif sdk_data.get("snippet"):
                    container_kwargs["snippet"] = sdk_data.pop("snippet")
                elif sdk_data.get("device"):
                    container_kwargs["device"] = sdk_data.pop("device")

                result = scm_client.create_url_category(**container_kwargs, **sdk_data)

                results.append(result)

                # Track if created or updated based on response
                if result.get("__action__") == "created":
                    created_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                typer.echo(
                    f"Error processing URL category '{category_data.get('name', 'unknown')}': {str(e)}",
                    err=True,
                )
                # Continue processing other categories
                continue

        # Display summary with counts
        typer.echo(f"Successfully processed {len(results)} URL category(ies):")
        if created_count > 0:
            typer.echo(f"  - Created: {created_count}")
        if updated_count > 0:
            typer.echo(f"  - Updated: {updated_count}")

        return results

    except Exception as e:
        typer.echo(f"Error loading URL categories: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("url-category")
def set_url_category(
    folder: str = typer.Option(None, "--folder", help="Folder path for the URL category"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet path for the URL category"),
    device: str = typer.Option(None, "--device", help="Device path for the URL category"),
    name: str = NAME_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    type: str = typer.Option("URL List", "--type", help="Type of URL category (URL List or Category Match)"),
    urls: list[str] | None = URL_CATEGORY_URLS_OPTION,
):
    r"""Create or update a URL category.

    Examples:
        # Create URL list category in folder
        scm set security url-category --folder Texas --name custom-block \
            --url malware.example.com --url phishing.test.org

        # Create category match type
        scm set security url-category --folder Texas --name match-category \
            --type "Category Match" --url gambling --url adult

        # Create in snippet
        scm set security url-category --snippet Security-Best-Practice \
            --name blocked-sites --url bad-site.com

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        # Build category data
        category_data: dict[str, Any] = {
            location_type: location_value,
            "name": name,
            "type": type,
        }

        if description:
            category_data["description"] = description
        if urls:
            category_data["list"] = urls

        # Validate using Pydantic model
        category = URLCategory(**category_data)

        # Call SDK client
        sdk_data = category.to_sdk_model()

        # Extract container params
        container_kwargs = {}
        if sdk_data.get("folder"):
            container_kwargs["folder"] = sdk_data.pop("folder")
        elif sdk_data.get("snippet"):
            container_kwargs["snippet"] = sdk_data.pop("snippet")
        elif sdk_data.get("device"):
            container_kwargs["device"] = sdk_data.pop("device")

        result = scm_client.create_url_category(**container_kwargs, **sdk_data)

        # Format and display output
        action = result.get("__action__", "created")
        if action == "created":
            typer.echo(f"Created URL category: {result['name']} in {location_type} {location_value}")
        elif action == "updated":
            typer.echo(f"Updated URL category: {result['name']} in {location_type} {location_value}")
        else:
            typer.echo(f"No changes to URL category: {result['name']} in {location_type} {location_value}")

    except Exception as e:
        typer.echo(f"Error creating URL category: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("url-category")
def show_url_category(
    folder: str = typer.Option(None, "--folder", help="Folder containing the URL category"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the URL category"),
    device: str = typer.Option(None, "--device", help="Device containing the URL category"),
    name: str | None = typer.Option(None, "--name", help="Name of the URL category to show"),
):
    """Display URL categories.

    Examples:
        # List all URL categories in a folder (default behavior)
        scm show security url-category --folder Texas

        # Show a specific URL category by name
        scm show security url-category --folder Texas --name custom-block

        # List URL categories in snippet
        scm show security url-category --snippet Security-Best-Practice

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        if name:
            # Get a specific URL category by name
            kwargs = {location_type: location_value}
            category = scm_client.get_url_category(**kwargs, name=name)

            typer.echo(f"\nURL Category: {category.get('name', 'N/A')}")
            typer.echo("=" * 80)

            # Display container location
            if category.get("folder"):
                typer.echo(f"Location: Folder '{category['folder']}'")
            elif category.get("snippet"):
                typer.echo(f"Location: Snippet '{category['snippet']}'")
            elif category.get("device"):
                typer.echo(f"Location: Device '{category['device']}'")

            # Display description if present
            if category.get("description"):
                typer.echo(f"Description: {category['description']}")

            # Display type
            if category.get("type"):
                typer.echo(f"Type: {category['type']}")

            # Display URL list
            if category.get("list"):
                typer.echo(f"\nURLs ({len(category['list'])}):")
                for url in category["list"]:
                    typer.echo(f"  - {url}")

            # Display ID if present
            if category.get("id"):
                typer.echo(f"\nID: {category['id']}")

            return category

        else:
            # Default behavior: list all
            kwargs = {location_type: location_value}
            categories = scm_client.list_url_categories(**kwargs, exact_match=False)

            if not categories:
                typer.echo(f"No URL categories found in {location_type} '{location_value}'")
                return

            typer.echo(f"\nURL Categories in {location_type} '{location_value}':")
            typer.echo("=" * 80)

            for category in categories:
                typer.echo(f"Name: {category.get('name', 'N/A')}")

                # Display container location
                if category.get("folder"):
                    typer.echo(f"  Location: Folder '{category['folder']}'")
                elif category.get("snippet"):
                    typer.echo(f"  Location: Snippet '{category['snippet']}'")
                elif category.get("device"):
                    typer.echo(f"  Location: Device '{category['device']}'")

                # Display description if present
                if category.get("description"):
                    typer.echo(f"  Description: {category['description']}")

                # Display type
                if category.get("type"):
                    typer.echo(f"  Type: {category['type']}")

                # Display URL count
                if category.get("list"):
                    typer.echo(f"  URLs: {len(category['list'])} entries")

                # Display ID if present
                if category.get("id"):
                    typer.echo(f"  ID: {category['id']}")

                typer.echo("-" * 80)

            return categories

    except Exception as e:
        typer.echo(f"Error showing URL category: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# APP OVERRIDE RULE COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("app-override-rule")
def backup_app_override_rule(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: str = BACKUP_FILE_OPTION,
    rulebase: str = RULEBASE_OPTION,
):
    """Backup all app override rules from a container to a YAML file.

    Examples:
        # Backup from folder
        scm backup security app-override-rule --folder Austin --rulebase pre

        # Backup to custom filename
        scm backup security app-override-rule --folder Austin --file my-rules.yaml

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    if not file:
        file = get_default_backup_filename("app-override-rules", location_type, location_value, rulebase)

    try:
        kwargs = {location_type: location_value}
        rules = scm_client.list_app_override_rules(**kwargs, rulebase=rulebase, exact_match=True)

        if not rules:
            typer.echo(f"No app override rules found in {location_type} '{location_value}' rulebase '{rulebase}'")
            return

        backup_data = []
        for rule in rules:
            rule_dict = rule.copy()
            rule_dict.pop("id", None)
            rule_dict["rulebase"] = rulebase
            backup_data.append(rule_dict)

        yaml_data = {"app_override_rules": backup_data}

        with open(file, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} app override rules to {file}")
        return file

    except Exception as e:
        typer.echo(f"Error backing up app override rules: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("app-override-rule")
def delete_app_override_rule(
    folder: str = typer.Option(None, "--folder", help="Folder containing the rule"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the rule"),
    device: str = typer.Option(None, "--device", help="Device containing the rule"),
    name: str = NAME_OPTION,
    rulebase: str = RULEBASE_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete an app override rule.

    Examples:
        scm delete security app-override-rule --folder Texas --name override-web --rulebase pre

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    if not force:
        confirm = typer.confirm(f"Delete app override rule '{name}' from {location_type} '{location_value}'?")
        if not confirm:
            raise typer.Abort()

    try:
        kwargs = {location_type: location_value}
        result = scm_client.delete_app_override_rule(**kwargs, name=name, rulebase=rulebase)
        if result:
            typer.echo(f"Deleted app override rule: {name} from {location_type} {location_value}")
        else:
            typer.echo(f"App override rule not found: {name} in {location_type} {location_value}", err=True)
            raise typer.Exit(code=1) from Exception
    except Exception as e:
        typer.echo(f"Error deleting app override rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("app-override-rule", help="Load app override rules from a YAML file.")
def load_app_override_rule(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load app override rules from a YAML file.

    Examples:
        scm load security app-override-rule --file config/app_override_rules.yml
        scm load security app-override-rule --file config/app_override_rules.yml --folder Production
        scm load security app-override-rule --file config/app_override_rules.yml --dry-run

    """
    try:
        if sum(1 for x in [folder, snippet, device] if x is not None) > 1:
            typer.echo("Error: Only one of --folder, --snippet, or --device can be specified", err=True)
            raise typer.Exit(code=1)

        if not file.exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)

        with open(file) as f:
            raw_data = yaml.safe_load(f)

        if not raw_data or "app_override_rules" not in raw_data:
            typer.echo("No app override rules found in file", err=True)
            raise typer.Exit(code=1)

        rules = raw_data["app_override_rules"]
        if not isinstance(rules, list):
            rules = [rules]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(rules))
            return []

        results = []
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

                rule = AppOverrideRule(**rule_data)
                sdk_data = rule.to_sdk_model()

                container_kwargs = {}
                if sdk_data.get("folder"):
                    container_kwargs["folder"] = sdk_data.pop("folder")
                elif sdk_data.get("snippet"):
                    container_kwargs["snippet"] = sdk_data.pop("snippet")
                elif sdk_data.get("device"):
                    container_kwargs["device"] = sdk_data.pop("device")

                result = scm_client.create_app_override_rule(**container_kwargs, **sdk_data)
                results.append(result)

            except Exception as e:
                typer.echo(f"Error processing app override rule '{rule_data.get('name', 'unknown')}': {str(e)}", err=True)
                continue

        typer.echo(f"Successfully processed {len(results)} app override rule(s)")
        return results

    except Exception as e:
        typer.echo(f"Error loading app override rules: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("app-override-rule")
def set_app_override_rule(
    folder: str = typer.Option(None, "--folder", help="Folder path"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet path"),
    device: str = typer.Option(None, "--device", help="Device path"),
    name: str = NAME_OPTION,
    application: str = typer.Option(..., "--application", help="Application to override"),
    port: str = typer.Option(..., "--port", help="Port(s) for the rule"),
    protocol: str = typer.Option(..., "--protocol", help="Protocol (tcp or udp)"),
    rulebase: str = RULEBASE_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    source_zones: list[str] | None = APP_OVERRIDE_SOURCE_ZONES_OPTION,
    destination_zones: list[str] | None = APP_OVERRIDE_DEST_ZONES_OPTION,
    disabled: bool = typer.Option(False, "--disabled", help="Disable the rule"),
    tags: list[str] | None = TAGS_OPTION,
):
    r"""Create or update an app override rule.

    Examples:
        scm set security app-override-rule --folder Texas --name override-https \
            --application ssl --port 8443 --protocol tcp

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        rule_data: dict[str, Any] = {
            location_type: location_value,
            "name": name,
            "application": application,
            "port": port,
            "protocol": protocol,
            "rulebase": rulebase,
        }

        if description:
            rule_data["description"] = description
        if source_zones:
            rule_data["from_zones"] = source_zones
        if destination_zones:
            rule_data["to_zones"] = destination_zones
        if disabled:
            rule_data["disabled"] = disabled
        if tags:
            rule_data["tag"] = tags

        rule = AppOverrideRule(**rule_data)
        sdk_data = rule.to_sdk_model()

        container_kwargs = {}
        if sdk_data.get("folder"):
            container_kwargs["folder"] = sdk_data.pop("folder")
        elif sdk_data.get("snippet"):
            container_kwargs["snippet"] = sdk_data.pop("snippet")
        elif sdk_data.get("device"):
            container_kwargs["device"] = sdk_data.pop("device")

        result = scm_client.create_app_override_rule(**container_kwargs, **sdk_data)
        action = result.get("__action__", "created")
        if action == "created":
            typer.echo(f"Created app override rule: {result['name']} in {location_type} {location_value}")
        elif action == "updated":
            typer.echo(f"Updated app override rule: {result['name']} in {location_type} {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for app override rule: {result['name']} in {location_type} {location_value}")

    except Exception as e:
        typer.echo(f"Error creating app override rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("app-override-rule")
def show_app_override_rule(
    folder: str = typer.Option(None, "--folder", help="Folder containing the rule"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the rule"),
    device: str = typer.Option(None, "--device", help="Device containing the rule"),
    name: str | None = typer.Option(None, "--name", help="Name of the rule to show"),
    rulebase: str = RULEBASE_OPTION,
):
    """Display app override rules.

    Examples:
        scm show security app-override-rule --folder Texas --rulebase pre
        scm show security app-override-rule --folder Texas --name override-https

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        if name:
            kwargs = {location_type: location_value}
            rule = scm_client.get_app_override_rule(**kwargs, name=name, rulebase=rulebase)

            typer.echo(f"\nApp Override Rule: {rule.get('name', 'N/A')}")
            typer.echo("=" * 80)
            if rule.get("folder"):
                typer.echo(f"Location: Folder '{rule['folder']}'")
            elif rule.get("snippet"):
                typer.echo(f"Location: Snippet '{rule['snippet']}'")
            elif rule.get("device"):
                typer.echo(f"Location: Device '{rule['device']}'")
            if rule.get("description"):
                typer.echo(f"Description: {rule['description']}")
            typer.echo(f"Application: {rule.get('application', 'N/A')}")
            typer.echo(f"Port: {rule.get('port', 'N/A')}")
            typer.echo(f"Protocol: {rule.get('protocol', 'N/A')}")
            typer.echo(f"From: {rule.get('from', ['any'])}")
            typer.echo(f"To: {rule.get('to', ['any'])}")
            typer.echo(f"Source: {rule.get('source', ['any'])}")
            typer.echo(f"Destination: {rule.get('destination', ['any'])}")
            if rule.get("disabled"):
                typer.echo("Status: Disabled")
            if rule.get("id"):
                typer.echo(f"ID: {rule['id']}")

        else:
            kwargs = {location_type: location_value}
            rules = scm_client.list_app_override_rules(**kwargs, rulebase=rulebase, exact_match=False)

            if not rules:
                typer.echo(f"No app override rules found in {location_type} '{location_value}'")
                return

            typer.echo(f"\nApp Override Rules in {location_type} '{location_value}':")
            typer.echo("=" * 80)

            for rule in rules:
                typer.echo(f"Name: {rule.get('name', 'N/A')}")
                typer.echo(f"  Application: {rule.get('application', 'N/A')}")
                typer.echo(f"  Port: {rule.get('port', 'N/A')}")
                typer.echo(f"  Protocol: {rule.get('protocol', 'N/A')}")
                if rule.get("id"):
                    typer.echo(f"  ID: {rule['id']}")
                typer.echo("-" * 80)

            return rules

    except Exception as e:
        typer.echo(f"Error showing app override rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# AUTHENTICATION RULE COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("authentication-rule")
def backup_authentication_rule(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: str = BACKUP_FILE_OPTION,
    rulebase: str = RULEBASE_OPTION,
):
    """Backup all authentication rules from a container to a YAML file.

    Examples:
        scm backup security authentication-rule --folder Austin --rulebase pre

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    if not file:
        file = get_default_backup_filename("authentication-rules", location_type, location_value, rulebase)

    try:
        kwargs = {location_type: location_value}
        rules = scm_client.list_authentication_rules(**kwargs, rulebase=rulebase, exact_match=True)

        if not rules:
            typer.echo(f"No authentication rules found in {location_type} '{location_value}' rulebase '{rulebase}'")
            return

        backup_data = []
        for rule in rules:
            rule_dict = rule.copy()
            rule_dict.pop("id", None)
            rule_dict["rulebase"] = rulebase
            backup_data.append(rule_dict)

        yaml_data = {"authentication_rules": backup_data}

        with open(file, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} authentication rules to {file}")
        return file

    except Exception as e:
        typer.echo(f"Error backing up authentication rules: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("authentication-rule")
def delete_authentication_rule(
    folder: str = typer.Option(None, "--folder", help="Folder containing the rule"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the rule"),
    device: str = typer.Option(None, "--device", help="Device containing the rule"),
    name: str = NAME_OPTION,
    rulebase: str = RULEBASE_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete an authentication rule.

    Examples:
        scm delete security authentication-rule --folder Texas --name auth-rule-1

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    if not force:
        confirm = typer.confirm(f"Delete authentication rule '{name}' from {location_type} '{location_value}'?")
        if not confirm:
            raise typer.Abort()

    try:
        kwargs = {location_type: location_value}
        result = scm_client.delete_authentication_rule(**kwargs, name=name, rulebase=rulebase)
        if result:
            typer.echo(f"Deleted authentication rule: {name} from {location_type} {location_value}")
        else:
            typer.echo(f"Authentication rule not found: {name} in {location_type} {location_value}", err=True)
            raise typer.Exit(code=1) from Exception
    except Exception as e:
        typer.echo(f"Error deleting authentication rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("authentication-rule", help="Load authentication rules from a YAML file.")
def load_authentication_rule(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load authentication rules from a YAML file.

    Examples:
        scm load security authentication-rule --file config/authentication_rules.yml
        scm load security authentication-rule --file config/authentication_rules.yml --folder Production

    """
    try:
        if sum(1 for x in [folder, snippet, device] if x is not None) > 1:
            typer.echo("Error: Only one of --folder, --snippet, or --device can be specified", err=True)
            raise typer.Exit(code=1)

        if not file.exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)

        with open(file) as f:
            raw_data = yaml.safe_load(f)

        if not raw_data or "authentication_rules" not in raw_data:
            typer.echo("No authentication rules found in file", err=True)
            raise typer.Exit(code=1)

        rules = raw_data["authentication_rules"]
        if not isinstance(rules, list):
            rules = [rules]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(rules))
            return []

        results = []
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

                rule = AuthenticationRule(**rule_data)
                sdk_data = rule.to_sdk_model()

                container_kwargs = {}
                if sdk_data.get("folder"):
                    container_kwargs["folder"] = sdk_data.pop("folder")
                elif sdk_data.get("snippet"):
                    container_kwargs["snippet"] = sdk_data.pop("snippet")
                elif sdk_data.get("device"):
                    container_kwargs["device"] = sdk_data.pop("device")

                result = scm_client.create_authentication_rule(**container_kwargs, **sdk_data)
                results.append(result)

            except Exception as e:
                typer.echo(f"Error processing authentication rule '{rule_data.get('name', 'unknown')}': {str(e)}", err=True)
                continue

        typer.echo(f"Successfully processed {len(results)} authentication rule(s)")
        return results

    except Exception as e:
        typer.echo(f"Error loading authentication rules: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("authentication-rule")
def set_authentication_rule(
    folder: str = typer.Option(None, "--folder", help="Folder path"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet path"),
    device: str = typer.Option(None, "--device", help="Device path"),
    name: str = NAME_OPTION,
    rulebase: str = RULEBASE_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    source_zones: list[str] | None = AUTH_RULE_SOURCE_ZONES_OPTION,
    destination_zones: list[str] | None = AUTH_RULE_DEST_ZONES_OPTION,
    service: list[str] | None = AUTH_RULE_SERVICE_OPTION,
    category: list[str] | None = AUTH_RULE_CATEGORY_OPTION,
    authentication_enforcement: str | None = typer.Option(None, "--authentication-enforcement", help="Authentication profile"),
    disabled: bool = typer.Option(False, "--disabled", help="Disable the rule"),
    tags: list[str] | None = TAGS_OPTION,
):
    r"""Create or update an authentication rule.

    Examples:
        scm set security authentication-rule --folder Texas --name auth-web \
            --source-zones trust --destination-zones untrust

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        rule_data: dict[str, Any] = {
            location_type: location_value,
            "name": name,
            "rulebase": rulebase,
        }

        if description:
            rule_data["description"] = description
        if source_zones:
            rule_data["from_zones"] = source_zones
        if destination_zones:
            rule_data["to_zones"] = destination_zones
        if service:
            rule_data["service"] = service
        if category:
            rule_data["category"] = category
        if authentication_enforcement:
            rule_data["authentication_enforcement"] = authentication_enforcement
        if disabled:
            rule_data["disabled"] = disabled
        if tags:
            rule_data["tag"] = tags

        rule = AuthenticationRule(**rule_data)
        sdk_data = rule.to_sdk_model()

        container_kwargs = {}
        if sdk_data.get("folder"):
            container_kwargs["folder"] = sdk_data.pop("folder")
        elif sdk_data.get("snippet"):
            container_kwargs["snippet"] = sdk_data.pop("snippet")
        elif sdk_data.get("device"):
            container_kwargs["device"] = sdk_data.pop("device")

        result = scm_client.create_authentication_rule(**container_kwargs, **sdk_data)
        action = result.get("__action__", "created")
        if action == "created":
            typer.echo(f"Created authentication rule: {result['name']} in {location_type} {location_value}")
        elif action == "updated":
            typer.echo(f"Updated authentication rule: {result['name']} in {location_type} {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for authentication rule: {result['name']} in {location_type} {location_value}")

    except Exception as e:
        typer.echo(f"Error creating authentication rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("authentication-rule")
def show_authentication_rule(
    folder: str = typer.Option(None, "--folder", help="Folder containing the rule"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the rule"),
    device: str = typer.Option(None, "--device", help="Device containing the rule"),
    name: str | None = typer.Option(None, "--name", help="Name of the rule to show"),
    rulebase: str = RULEBASE_OPTION,
):
    """Display authentication rules.

    Examples:
        scm show security authentication-rule --folder Texas --rulebase pre
        scm show security authentication-rule --folder Texas --name auth-web

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        if name:
            kwargs = {location_type: location_value}
            rule = scm_client.get_authentication_rule(**kwargs, name=name, rulebase=rulebase)

            typer.echo(f"\nAuthentication Rule: {rule.get('name', 'N/A')}")
            typer.echo("=" * 80)
            if rule.get("folder"):
                typer.echo(f"Location: Folder '{rule['folder']}'")
            elif rule.get("snippet"):
                typer.echo(f"Location: Snippet '{rule['snippet']}'")
            elif rule.get("device"):
                typer.echo(f"Location: Device '{rule['device']}'")
            if rule.get("description"):
                typer.echo(f"Description: {rule['description']}")
            typer.echo(f"From: {rule.get('from', ['any'])}")
            typer.echo(f"To: {rule.get('to', ['any'])}")
            typer.echo(f"Source: {rule.get('source', ['any'])}")
            typer.echo(f"Destination: {rule.get('destination', ['any'])}")
            typer.echo(f"Service: {rule.get('service', ['any'])}")
            typer.echo(f"Category: {rule.get('category', ['any'])}")
            if rule.get("authentication_enforcement"):
                typer.echo(f"Authentication Enforcement: {rule['authentication_enforcement']}")
            if rule.get("disabled"):
                typer.echo("Status: Disabled")
            if rule.get("id"):
                typer.echo(f"ID: {rule['id']}")

        else:
            kwargs = {location_type: location_value}
            rules = scm_client.list_authentication_rules(**kwargs, rulebase=rulebase, exact_match=False)

            if not rules:
                typer.echo(f"No authentication rules found in {location_type} '{location_value}'")
                return

            typer.echo(f"\nAuthentication Rules in {location_type} '{location_value}':")
            typer.echo("=" * 80)

            for rule in rules:
                typer.echo(f"Name: {rule.get('name', 'N/A')}")
                if rule.get("authentication_enforcement"):
                    typer.echo(f"  Auth Enforcement: {rule['authentication_enforcement']}")
                if rule.get("id"):
                    typer.echo(f"  ID: {rule['id']}")
                typer.echo("-" * 80)

            return rules

    except Exception as e:
        typer.echo(f"Error showing authentication rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# DECRYPTION RULE COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("decryption-rule")
def backup_decryption_rule(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: str = BACKUP_FILE_OPTION,
    rulebase: str = RULEBASE_OPTION,
):
    """Backup all decryption rules from a container to a YAML file.

    Examples:
        scm backup security decryption-rule --folder Austin --rulebase pre

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    if not file:
        file = get_default_backup_filename("decryption-rules", location_type, location_value, rulebase)

    try:
        kwargs = {location_type: location_value}
        rules = scm_client.list_decryption_rules(**kwargs, rulebase=rulebase, exact_match=True)

        if not rules:
            typer.echo(f"No decryption rules found in {location_type} '{location_value}' rulebase '{rulebase}'")
            return

        backup_data = []
        for rule in rules:
            rule_dict = rule.copy()
            rule_dict.pop("id", None)
            rule_dict["rulebase"] = rulebase
            backup_data.append(rule_dict)

        yaml_data = {"decryption_rules": backup_data}

        with open(file, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} decryption rules to {file}")
        return file

    except Exception as e:
        typer.echo(f"Error backing up decryption rules: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("decryption-rule")
def delete_decryption_rule(
    folder: str = typer.Option(None, "--folder", help="Folder containing the rule"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the rule"),
    device: str = typer.Option(None, "--device", help="Device containing the rule"),
    name: str = NAME_OPTION,
    rulebase: str = RULEBASE_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a decryption rule.

    Examples:
        scm delete security decryption-rule --folder Texas --name decrypt-web

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    if not force:
        confirm = typer.confirm(f"Delete decryption rule '{name}' from {location_type} '{location_value}'?")
        if not confirm:
            raise typer.Abort()

    try:
        kwargs = {location_type: location_value}
        result = scm_client.delete_decryption_rule(**kwargs, name=name, rulebase=rulebase)
        if result:
            typer.echo(f"Deleted decryption rule: {name} from {location_type} {location_value}")
        else:
            typer.echo(f"Decryption rule not found: {name} in {location_type} {location_value}", err=True)
            raise typer.Exit(code=1) from Exception
    except Exception as e:
        typer.echo(f"Error deleting decryption rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("decryption-rule", help="Load decryption rules from a YAML file.")
def load_decryption_rule(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load decryption rules from a YAML file.

    Examples:
        scm load security decryption-rule --file config/decryption_rules.yml
        scm load security decryption-rule --file config/decryption_rules.yml --folder Production

    """
    try:
        if sum(1 for x in [folder, snippet, device] if x is not None) > 1:
            typer.echo("Error: Only one of --folder, --snippet, or --device can be specified", err=True)
            raise typer.Exit(code=1)

        if not file.exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)

        with open(file) as f:
            raw_data = yaml.safe_load(f)

        if not raw_data or "decryption_rules" not in raw_data:
            typer.echo("No decryption rules found in file", err=True)
            raise typer.Exit(code=1)

        rules = raw_data["decryption_rules"]
        if not isinstance(rules, list):
            rules = [rules]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(rules))
            return []

        results = []
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

                rule = DecryptionRule(**rule_data)
                sdk_data = rule.to_sdk_model()

                container_kwargs = {}
                if sdk_data.get("folder"):
                    container_kwargs["folder"] = sdk_data.pop("folder")
                elif sdk_data.get("snippet"):
                    container_kwargs["snippet"] = sdk_data.pop("snippet")
                elif sdk_data.get("device"):
                    container_kwargs["device"] = sdk_data.pop("device")

                result = scm_client.create_decryption_rule(**container_kwargs, **sdk_data)
                results.append(result)

            except Exception as e:
                typer.echo(f"Error processing decryption rule '{rule_data.get('name', 'unknown')}': {str(e)}", err=True)
                continue

        typer.echo(f"Successfully processed {len(results)} decryption rule(s)")
        return results

    except Exception as e:
        typer.echo(f"Error loading decryption rules: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("decryption-rule")
def set_decryption_rule(
    folder: str = typer.Option(None, "--folder", help="Folder path"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet path"),
    device: str = typer.Option(None, "--device", help="Device path"),
    name: str = NAME_OPTION,
    action: str = typer.Option(..., "--action", help="Action (decrypt or no-decrypt)"),
    rulebase: str = RULEBASE_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    source_zones: list[str] | None = DECRYPT_RULE_SOURCE_ZONES_OPTION,
    destination_zones: list[str] | None = DECRYPT_RULE_DEST_ZONES_OPTION,
    profile: str | None = typer.Option(None, "--profile", help="Decryption profile"),
    type_json: str | None = typer.Option(None, "--type", help="Decryption type as JSON"),
    disabled: bool = typer.Option(False, "--disabled", help="Disable the rule"),
    tags: list[str] | None = TAGS_OPTION,
):
    r"""Create or update a decryption rule.

    Examples:
        scm set security decryption-rule --folder Texas --name no-decrypt-internal \
            --action no-decrypt --source-zones trust --destination-zones trust

        scm set security decryption-rule --folder Texas --name decrypt-outbound \
            --action decrypt --type '{"ssl_forward_proxy": {}}'

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        rule_data: dict[str, Any] = {
            location_type: location_value,
            "name": name,
            "action": action,
            "rulebase": rulebase,
        }

        if description:
            rule_data["description"] = description
        if source_zones:
            rule_data["from_zones"] = source_zones
        if destination_zones:
            rule_data["to_zones"] = destination_zones
        if profile:
            rule_data["profile"] = profile
        if type_json:
            rule_data["type"] = json.loads(type_json)
        if disabled:
            rule_data["disabled"] = disabled
        if tags:
            rule_data["tag"] = tags

        rule = DecryptionRule(**rule_data)
        sdk_data = rule.to_sdk_model()

        container_kwargs = {}
        if sdk_data.get("folder"):
            container_kwargs["folder"] = sdk_data.pop("folder")
        elif sdk_data.get("snippet"):
            container_kwargs["snippet"] = sdk_data.pop("snippet")
        elif sdk_data.get("device"):
            container_kwargs["device"] = sdk_data.pop("device")

        result = scm_client.create_decryption_rule(**container_kwargs, **sdk_data)
        action = result.get("__action__", "created")
        if action == "created":
            typer.echo(f"Created decryption rule: {result['name']} in {location_type} {location_value}")
        elif action == "updated":
            typer.echo(f"Updated decryption rule: {result['name']} in {location_type} {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for decryption rule: {result['name']} in {location_type} {location_value}")

    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating decryption rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("decryption-rule")
def show_decryption_rule(
    folder: str = typer.Option(None, "--folder", help="Folder containing the rule"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the rule"),
    device: str = typer.Option(None, "--device", help="Device containing the rule"),
    name: str | None = typer.Option(None, "--name", help="Name of the rule to show"),
    rulebase: str = RULEBASE_OPTION,
):
    """Display decryption rules.

    Examples:
        scm show security decryption-rule --folder Texas --rulebase pre
        scm show security decryption-rule --folder Texas --name decrypt-outbound

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        if name:
            kwargs = {location_type: location_value}
            rule = scm_client.get_decryption_rule(**kwargs, name=name, rulebase=rulebase)

            typer.echo(f"\nDecryption Rule: {rule.get('name', 'N/A')}")
            typer.echo("=" * 80)
            if rule.get("folder"):
                typer.echo(f"Location: Folder '{rule['folder']}'")
            elif rule.get("snippet"):
                typer.echo(f"Location: Snippet '{rule['snippet']}'")
            elif rule.get("device"):
                typer.echo(f"Location: Device '{rule['device']}'")
            if rule.get("description"):
                typer.echo(f"Description: {rule['description']}")
            typer.echo(f"Action: {rule.get('action', 'N/A')}")
            typer.echo(f"From: {rule.get('from', ['any'])}")
            typer.echo(f"To: {rule.get('to', ['any'])}")
            typer.echo(f"Source: {rule.get('source', ['any'])}")
            typer.echo(f"Destination: {rule.get('destination', ['any'])}")
            if rule.get("profile"):
                typer.echo(f"Profile: {rule['profile']}")
            if rule.get("type"):
                typer.echo(f"Type: {rule['type']}")
            if rule.get("disabled"):
                typer.echo("Status: Disabled")
            if rule.get("id"):
                typer.echo(f"ID: {rule['id']}")

        else:
            kwargs = {location_type: location_value}
            rules = scm_client.list_decryption_rules(**kwargs, rulebase=rulebase, exact_match=False)

            if not rules:
                typer.echo(f"No decryption rules found in {location_type} '{location_value}'")
                return

            typer.echo(f"\nDecryption Rules in {location_type} '{location_value}':")
            typer.echo("=" * 80)

            for rule in rules:
                typer.echo(f"Name: {rule.get('name', 'N/A')}")
                typer.echo(f"  Action: {rule.get('action', 'N/A')}")
                if rule.get("id"):
                    typer.echo(f"  ID: {rule['id']}")
                typer.echo("-" * 80)

            return rules

    except Exception as e:
        typer.echo(f"Error showing decryption rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# URL ACCESS PROFILE COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("url-access-profile")
def backup_url_access_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: str = BACKUP_FILE_OPTION,
):
    """Backup all URL access profiles from a container to a YAML file.

    Examples:
        scm backup security url-access-profile --folder Austin

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    if not file:
        file = get_default_backup_filename("url-access-profiles", location_type, location_value)

    try:
        kwargs = {location_type: location_value}
        profiles = scm_client.list_url_access_profiles(**kwargs, exact_match=True)

        if not profiles:
            typer.echo(f"No URL access profiles found in {location_type} '{location_value}'")
            return

        backup_data = []
        for profile in profiles:
            profile_dict = profile.copy()
            profile_dict.pop("id", None)
            backup_data.append(profile_dict)

        yaml_data = {"url_access_profiles": backup_data}

        with open(file, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} URL access profiles to {file}")
        return file

    except Exception as e:
        typer.echo(f"Error backing up URL access profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("url-access-profile")
def delete_url_access_profile(
    folder: str = typer.Option(None, "--folder", help="Folder containing the profile"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the profile"),
    device: str = typer.Option(None, "--device", help="Device containing the profile"),
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a URL access profile.

    Examples:
        scm delete security url-access-profile --folder Texas --name strict-url-profile

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    if not force:
        confirm = typer.confirm(f"Delete URL access profile '{name}' from {location_type} '{location_value}'?")
        if not confirm:
            raise typer.Abort()

    try:
        kwargs = {location_type: location_value}
        result = scm_client.delete_url_access_profile(**kwargs, name=name)
        if result:
            typer.echo(f"Deleted URL access profile: {name} from {location_type} {location_value}")
        else:
            typer.echo(f"URL access profile not found: {name} in {location_type} {location_value}", err=True)
            raise typer.Exit(code=1) from Exception
    except Exception as e:
        typer.echo(f"Error deleting URL access profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("url-access-profile", help="Load URL access profiles from a YAML file.")
def load_url_access_profile(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load URL access profiles from a YAML file.

    Examples:
        scm load security url-access-profile --file config/url_access_profiles.yml
        scm load security url-access-profile --file config/url_access_profiles.yml --folder Production

    """
    try:
        if sum(1 for x in [folder, snippet, device] if x is not None) > 1:
            typer.echo("Error: Only one of --folder, --snippet, or --device can be specified", err=True)
            raise typer.Exit(code=1)

        if not file.exists():
            typer.echo(f"File not found: {file}", err=True)
            raise typer.Exit(code=1)

        with open(file) as f:
            raw_data = yaml.safe_load(f)

        if not raw_data or "url_access_profiles" not in raw_data:
            typer.echo("No URL access profiles found in file", err=True)
            raise typer.Exit(code=1)

        profiles = raw_data["url_access_profiles"]
        if not isinstance(profiles, list):
            profiles = [profiles]

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            if folder or snippet or device:
                override_type = "folder" if folder else ("snippet" if snippet else "device")
                override_value = folder or snippet or device
                typer.echo(f"Container override: {override_type} = '{override_value}'")
            typer.echo(yaml.dump(profiles))
            return []

        results = []
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

                profile = URLAccessProfile(**profile_data)
                sdk_data = profile.to_sdk_model()

                container_kwargs = {}
                if sdk_data.get("folder"):
                    container_kwargs["folder"] = sdk_data.pop("folder")
                elif sdk_data.get("snippet"):
                    container_kwargs["snippet"] = sdk_data.pop("snippet")
                elif sdk_data.get("device"):
                    container_kwargs["device"] = sdk_data.pop("device")

                result = scm_client.create_url_access_profile(**container_kwargs, **sdk_data)
                results.append(result)

            except Exception as e:
                typer.echo(f"Error processing URL access profile '{profile_data.get('name', 'unknown')}': {str(e)}", err=True)
                continue

        typer.echo(f"Successfully processed {len(results)} URL access profile(s)")
        return results

    except Exception as e:
        typer.echo(f"Error loading URL access profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("url-access-profile")
def set_url_access_profile(
    folder: str = typer.Option(None, "--folder", help="Folder path"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet path"),
    device: str = typer.Option(None, "--device", help="Device path"),
    name: str = NAME_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    block: list[str] | None = URL_PROFILE_BLOCK_OPTION,
    alert: list[str] | None = URL_PROFILE_ALERT_OPTION,
    allow: list[str] | None = URL_PROFILE_ALLOW_OPTION,
    credential_enforcement_json: str | None = typer.Option(None, "--credential-enforcement", help="Credential enforcement as JSON"),
    cloud_inline_cat: bool = typer.Option(False, "--cloud-inline-cat/--no-cloud-inline-cat", help="Enable cloud inline categorization"),
    safe_search_enforcement: bool = typer.Option(False, "--safe-search/--no-safe-search", help="Enable safe search enforcement"),
):
    r"""Create or update a URL access profile.

    Examples:
        scm set security url-access-profile --folder Texas --name strict-url \
            --block adult --block malware --alert hacking

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        profile_data: dict[str, Any] = {
            location_type: location_value,
            "name": name,
        }

        if description:
            profile_data["description"] = description
        if block:
            profile_data["block"] = block
        if alert:
            profile_data["alert"] = alert
        if allow:
            profile_data["allow"] = allow
        if credential_enforcement_json:
            profile_data["credential_enforcement"] = json.loads(credential_enforcement_json)
        if cloud_inline_cat:
            profile_data["cloud_inline_cat"] = cloud_inline_cat
        if safe_search_enforcement:
            profile_data["safe_search_enforcement"] = safe_search_enforcement

        profile = URLAccessProfile(**profile_data)
        sdk_data = profile.to_sdk_model()

        container_kwargs = {}
        if sdk_data.get("folder"):
            container_kwargs["folder"] = sdk_data.pop("folder")
        elif sdk_data.get("snippet"):
            container_kwargs["snippet"] = sdk_data.pop("snippet")
        elif sdk_data.get("device"):
            container_kwargs["device"] = sdk_data.pop("device")

        result = scm_client.create_url_access_profile(**container_kwargs, **sdk_data)
        action = result.get("__action__", "created")
        if action == "created":
            typer.echo(f"Created URL access profile: {result['name']} in {location_type} {location_value}")
        elif action == "updated":
            typer.echo(f"Updated URL access profile: {result['name']} in {location_type} {location_value}")
        elif action == "no_change":
            typer.echo(f"No changes needed for URL access profile: {result['name']} in {location_type} {location_value}")

    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing JSON: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating URL access profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("url-access-profile")
def show_url_access_profile(
    folder: str = typer.Option(None, "--folder", help="Folder containing the profile"),
    snippet: str = typer.Option(None, "--snippet", help="Snippet containing the profile"),
    device: str = typer.Option(None, "--device", help="Device containing the profile"),
    name: str | None = typer.Option(None, "--name", help="Name of the profile to show"),
):
    """Display URL access profiles.

    Examples:
        scm show security url-access-profile --folder Texas
        scm show security url-access-profile --folder Texas --name strict-url

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
        if name:
            kwargs = {location_type: location_value}
            profile = scm_client.get_url_access_profile(**kwargs, name=name)

            typer.echo(f"\nURL Access Profile: {profile.get('name', 'N/A')}")
            typer.echo("=" * 80)
            if profile.get("folder"):
                typer.echo(f"Location: Folder '{profile['folder']}'")
            elif profile.get("snippet"):
                typer.echo(f"Location: Snippet '{profile['snippet']}'")
            elif profile.get("device"):
                typer.echo(f"Location: Device '{profile['device']}'")
            if profile.get("description"):
                typer.echo(f"Description: {profile['description']}")
            if profile.get("block"):
                typer.echo(f"Block: {profile['block']}")
            if profile.get("alert"):
                typer.echo(f"Alert: {profile['alert']}")
            if profile.get("allow"):
                typer.echo(f"Allow: {profile['allow']}")
            if profile.get("continue"):
                typer.echo(f"Continue: {profile['continue']}")
            if profile.get("redirect"):
                typer.echo(f"Redirect: {profile['redirect']}")
            if profile.get("credential_enforcement"):
                typer.echo(f"Credential Enforcement: {profile['credential_enforcement']}")
            if profile.get("cloud_inline_cat") is not None:
                typer.echo(f"Cloud Inline Cat: {'Enabled' if profile['cloud_inline_cat'] else 'Disabled'}")
            if profile.get("safe_search_enforcement") is not None:
                typer.echo(f"Safe Search: {'Enabled' if profile['safe_search_enforcement'] else 'Disabled'}")
            if profile.get("id"):
                typer.echo(f"ID: {profile['id']}")

        else:
            kwargs = {location_type: location_value}
            profiles = scm_client.list_url_access_profiles(**kwargs, exact_match=False)

            if not profiles:
                typer.echo(f"No URL access profiles found in {location_type} '{location_value}'")
                return

            typer.echo(f"\nURL Access Profiles in {location_type} '{location_value}':")
            typer.echo("=" * 80)

            for profile in profiles:
                typer.echo(f"Name: {profile.get('name', 'N/A')}")
                if profile.get("description"):
                    typer.echo(f"  Description: {profile['description']}")
                if profile.get("block"):
                    typer.echo(f"  Block: {len(profile['block'])} categories")
                if profile.get("alert"):
                    typer.echo(f"  Alert: {len(profile['alert'])} categories")
                if profile.get("id"):
                    typer.echo(f"  ID: {profile['id']}")
                typer.echo("-" * 80)

            return profiles

    except Exception as e:
        typer.echo(f"Error showing URL access profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# MOVE COMMANDS
# ========================================================================================================================================================================================

MOVE_FOLDER_OPTION = typer.Option(None, "--folder", help="Folder containing the rule")
MOVE_SNIPPET_OPTION = typer.Option(None, "--snippet", help="Snippet containing the rule")
MOVE_DEVICE_OPTION = typer.Option(None, "--device", help="Device containing the rule")
MOVE_NAME_OPTION = typer.Option(..., "--name", help="Name of the rule to move")
MOVE_DESTINATION_OPTION = typer.Option(..., "--destination", help="Where to move (top, bottom, before, after)")
MOVE_RULEBASE_OPTION = typer.Option("pre", "--rulebase", help="Rulebase (pre or post)")
MOVE_DESTINATION_RULE_OPTION = typer.Option(None, "--destination-rule", help="UUID of reference rule for before/after")


@move_app.command("rule")
def move_security_rule_cmd(
    folder: str = MOVE_FOLDER_OPTION,
    snippet: str = MOVE_SNIPPET_OPTION,
    device: str = MOVE_DEVICE_OPTION,
    name: str = MOVE_NAME_OPTION,
    destination: str = MOVE_DESTINATION_OPTION,
    rulebase: str = MOVE_RULEBASE_OPTION,
    destination_rule: str = MOVE_DESTINATION_RULE_OPTION,
):
    """Move a security rule to a new position.

    Examples:
        scm move security rule --folder Texas --name "Allow Web" --destination top --rulebase pre
        scm move security rule --folder Texas --name "Allow Web" --destination after --destination-rule <uuid>

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    if destination in ("before", "after") and not destination_rule:
        typer.echo("Error: --destination-rule is required when using before/after", err=True)
        raise typer.Exit(code=1)

    try:
        kwargs = {location_type: location_value}
        scm_client.move_security_rule(
            **kwargs,
            name=name,
            rulebase=rulebase,
            destination=destination,
            destination_rule=destination_rule,
        )
        typer.echo(f"Moved security rule '{name}' to {destination} in {location_type} '{location_value}' rulebase '{rulebase}'")

    except Exception as e:
        typer.echo(f"Error moving security rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@move_app.command("app-override-rule")
def move_app_override_rule_cmd(
    folder: str = MOVE_FOLDER_OPTION,
    snippet: str = MOVE_SNIPPET_OPTION,
    device: str = MOVE_DEVICE_OPTION,
    name: str = MOVE_NAME_OPTION,
    destination: str = MOVE_DESTINATION_OPTION,
    rulebase: str = MOVE_RULEBASE_OPTION,
    destination_rule: str = MOVE_DESTINATION_RULE_OPTION,
):
    """Move an app override rule to a new position.

    Examples:
        scm move security app-override-rule --folder Texas --name override-https --destination top
        scm move security app-override-rule --folder Texas --name override-https --destination before --destination-rule <uuid>

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    if destination in ("before", "after") and not destination_rule:
        typer.echo("Error: --destination-rule is required when using before/after", err=True)
        raise typer.Exit(code=1)

    try:
        kwargs = {location_type: location_value}
        scm_client.move_app_override_rule(
            **kwargs,
            name=name,
            rulebase=rulebase,
            destination=destination,
            destination_rule=destination_rule,
        )
        typer.echo(f"Moved app override rule '{name}' to {destination} in {location_type} '{location_value}' rulebase '{rulebase}'")

    except Exception as e:
        typer.echo(f"Error moving app override rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@move_app.command("authentication-rule")
def move_authentication_rule_cmd(
    folder: str = MOVE_FOLDER_OPTION,
    snippet: str = MOVE_SNIPPET_OPTION,
    device: str = MOVE_DEVICE_OPTION,
    name: str = MOVE_NAME_OPTION,
    destination: str = MOVE_DESTINATION_OPTION,
    rulebase: str = MOVE_RULEBASE_OPTION,
    destination_rule: str = MOVE_DESTINATION_RULE_OPTION,
):
    """Move an authentication rule to a new position.

    Examples:
        scm move security authentication-rule --folder Texas --name auth-rule --destination bottom

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    if destination in ("before", "after") and not destination_rule:
        typer.echo("Error: --destination-rule is required when using before/after", err=True)
        raise typer.Exit(code=1)

    try:
        kwargs = {location_type: location_value}
        scm_client.move_authentication_rule(
            **kwargs,
            name=name,
            rulebase=rulebase,
            destination=destination,
            destination_rule=destination_rule,
        )
        typer.echo(f"Moved authentication rule '{name}' to {destination} in {location_type} '{location_value}' rulebase '{rulebase}'")

    except Exception as e:
        typer.echo(f"Error moving authentication rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@move_app.command("decryption-rule")
def move_decryption_rule_cmd(
    folder: str = MOVE_FOLDER_OPTION,
    snippet: str = MOVE_SNIPPET_OPTION,
    device: str = MOVE_DEVICE_OPTION,
    name: str = MOVE_NAME_OPTION,
    destination: str = MOVE_DESTINATION_OPTION,
    rulebase: str = MOVE_RULEBASE_OPTION,
    destination_rule: str = MOVE_DESTINATION_RULE_OPTION,
):
    """Move a decryption rule to a new position.

    Examples:
        scm move security decryption-rule --folder Texas --name decrypt-rule --destination top

    """
    location_type, location_value = validate_location_params(folder, snippet, device)

    if destination in ("before", "after") and not destination_rule:
        typer.echo("Error: --destination-rule is required when using before/after", err=True)
        raise typer.Exit(code=1)

    try:
        kwargs = {location_type: location_value}
        scm_client.move_decryption_rule(
            **kwargs,
            name=name,
            rulebase=rulebase,
            destination=destination,
            destination_rule=destination_rule,
        )
        typer.echo(f"Moved decryption rule '{name}' to {destination} in {location_type} '{location_value}' rulebase '{rulebase}'")

    except Exception as e:
        typer.echo(f"Error moving decryption rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
