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

from ..utils.sdk_client import scm_client
from ..utils.validators import AntiSpywareProfile, DecryptionProfile, SecurityRule

# ========================================================================================================================================================================================
# TYPER APP CONFIGURATION
# ========================================================================================================================================================================================

# Create app groups for each action type
set_app = typer.Typer(help="Create or update security configurations")
delete_app = typer.Typer(help="Remove security configurations")
load_app = typer.Typer(help="Load security configurations from YAML files")
show_app = typer.Typer(help="Display security configurations")
backup_app = typer.Typer(help="Backup security configurations to YAML files")

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
        # Validate and create security rule
        rule = SecurityRule(
            folder=location_value,
            name=name,
            source_zones=source_zones,
            destination_zones=destination_zones,
            source_addresses=source_addresses or ["any"],
            destination_addresses=destination_addresses or ["any"],
            applications=applications or ["any"],
            service=services or ["any"],
            action=action,
            description=description or "",
            tags=tags or [],
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
        typer.echo(f"Created security rule: {result['name']} in {location_type} {location_value}")

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
            rules = scm_client.list_security_rules(**kwargs, rulebase=rulebase)

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
        typer.echo(f"Created anti-spyware profile: {result['name']} in {location_type} {location_value}")

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
        typer.echo(f"Created decryption profile: {result['name']} in {location_type} {location_value}")

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
