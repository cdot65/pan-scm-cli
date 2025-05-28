"""Security module commands for scm-cli.

This module implements set, delete, and load commands for security-related
configurations such as security rules, profiles, etc.
"""

from datetime import datetime
from pathlib import Path

import typer
import yaml

from ..utils.config import load_from_yaml
from ..utils.sdk_client import scm_client
from ..utils.validators import SecurityRule

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

# Define typer option constants
FOLDER_OPTION = typer.Option(..., "--folder", help="Folder path for the security rule")
NAME_OPTION = typer.Option(..., "--name", help="Name of the security rule")
SOURCE_ZONES_OPTION = typer.Option(..., "--source-zones", help="List of source zones")
DESTINATION_ZONES_OPTION = typer.Option(..., "--destination-zones", help="List of destination zones")
SOURCE_ADDRESSES_OPTION = typer.Option(None, "--source-addresses", help="List of source addresses")
DESTINATION_ADDRESSES_OPTION = typer.Option(None, "--destination-addresses", help="List of destination addresses")
APPLICATIONS_OPTION = typer.Option(None, "--applications", help="List of applications")
ACTION_OPTION = typer.Option("allow", "--action", help="Action (allow, deny, drop)")
DESCRIPTION_OPTION = typer.Option(None, "--description", help="Description of the security rule")
TAGS_OPTION = typer.Option(None, "--tags", help="List of tags")
ENABLED_OPTION = typer.Option(True, "--enabled/--disabled", help="Enable or disable the security rule")
FILE_OPTION = typer.Option(..., "--file", help="YAML file to load configurations from")
DRY_RUN_OPTION = typer.Option(False, "--dry-run", help="Simulate execution without applying changes")
RULEBASE_OPTION = typer.Option("pre", "--rulebase", help="Rulebase to use (pre, post, or default)")

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
        typer.echo("Error: Only one of --folder, --snippet, or --device can be specified", err=True)
        raise typer.Exit(code=1)

    if folder:
        return "folder", folder
    elif snippet:
        return "snippet", snippet
    else:
        return "device", device


def get_default_backup_filename(object_type: str, location_type: str, location_value: str, rulebase: str = None) -> str:
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
    --------
        # Backup from folder
        scm-cli backup security rule --folder Austin --rulebase pre

        # Backup from snippet
        scm-cli backup security rule --snippet DNS-Best-Practice --rulebase post

        # Backup from device
        scm-cli backup security rule --device austin-01 --rulebase default

        # Backup to custom filename
        scm-cli backup security rule --folder Austin --file my-rules.yaml

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Set default filename if not provided
    if not file:
        file = get_default_backup_filename("security-rules", location_type, location_value, rulebase)

    try:
        # List all security rules with exact_match=True
        rules = scm_client.list_security_rules(folder=folder, snippet=snippet, device=device, rulebase=rulebase, exact_match=True)

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
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete a security rule.

    Example:
    -------
        scm-cli delete security rule --folder Texas --name test

    """
    try:
        result = scm_client.delete_security_rule(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted security rule: {name} from folder {folder}")
        else:
            typer.echo(f"Security rule not found: {name} in folder {folder}", err=True)
            raise typer.Exit(code=1) from Exception
    except Exception as e:
        typer.echo(f"Error deleting security rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("rule")
def load_security_rule(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load security rules from a YAML file.

    Example:
    -------
        scm-cli load security rule --file config/security_rules.yml

    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(str(file), "security_rules")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["security_rules"]))
            return

        # Apply each security rule
        results = []
        for rule_data in config["security_rules"]:
            # Validate using the Pydantic model
            rule = SecurityRule(**rule_data)

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
                action=sdk_data["action"],
                description=sdk_data["description"],
                tags=sdk_data["tags"],
                enabled=sdk_data["enabled"],
                rulebase=sdk_data["rulebase"],
            )

            results.append(result)
            typer.echo(f"Applied security rule: {result['name']} in folder {result['folder']}")

        return results
    except Exception as e:
        typer.echo(f"Error loading security rules: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("rule")
def set_security_rule(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    source_zones: list[str] = SOURCE_ZONES_OPTION,
    destination_zones: list[str] = DESTINATION_ZONES_OPTION,
    source_addresses: list[str] | None = SOURCE_ADDRESSES_OPTION,
    destination_addresses: list[str] | None = DESTINATION_ADDRESSES_OPTION,
    applications: list[str] | None = APPLICATIONS_OPTION,
    action: str = ACTION_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    tags: list[str] | None = TAGS_OPTION,
    enabled: bool = ENABLED_OPTION,
):
    """Create or update a security rule.

    Example:
    -------
        scm-cli set security rule --folder Texas --name test --source-zones trust --destination-zones untrust

    """
    try:
        # Validate and create security rule
        rule = SecurityRule(
            folder=folder,
            name=name,
            source_zones=source_zones,
            destination_zones=destination_zones,
            source_addresses=source_addresses or ["any"],
            destination_addresses=destination_addresses or ["any"],
            applications=applications or ["any"],
            action=action,
            description=description or "",
            tags=tags or [],
            enabled=enabled,
        )

        # Call SDK client to create the rule
        result = scm_client.create_security_rule(**rule.to_sdk_model())

        # Format and display output
        typer.echo(f"Created security rule: {result['name']} in folder {result['folder']}")

    except Exception as e:
        typer.echo(f"Error creating security rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("rule")
def show_security_rule(
    folder: str = FOLDER_OPTION,
    rulebase: str = RULEBASE_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the security rule to show"),
    list_rules: bool = typer.Option(False, "--list", help="List all security rules"),
):
    """Display security rules.

    Examples:
    --------
        # List all security rules in a folder and rulebase
        scm-cli show security rule --folder Texas --list

        # List rules in post rulebase
        scm-cli show security rule --folder Texas --rulebase post --list

        # Show a specific security rule by name
        scm-cli show security rule --folder Texas --name "Allow Web Traffic"

    Note:
    ----
        Security rules require both folder and rulebase parameters.

    """
    try:
        if list_rules:
            # List all security rules in the specified folder and rulebase
            rules = scm_client.list_security_rules(folder=folder, rulebase=rulebase)

            if not rules:
                typer.echo(f"No security rules found in folder '{folder}' rulebase '{rulebase}'")
                return

            typer.echo(f"\nSecurity Rules in folder '{folder}' rulebase '{rulebase}':")
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

        elif name:
            # Get a specific security rule by name
            rule = scm_client.get_security_rule(folder=folder, name=name, rulebase=rulebase)

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
                    for profile_type in ["antivirus", "anti_spyware", "vulnerability", "url_filtering", "file_blocking", "data_filtering", "wildfire_analysis"]:
                        if profile_setting.get(profile_type):
                            profile_name = profile_type.replace("_", " ").title()
                            typer.echo(f"  {profile_name}: {profile_setting[profile_type]}")

            # Display ID if present
            if rule.get("id"):
                typer.echo(f"ID: {rule['id']}")

            return rule

        else:
            # Neither --list nor --name was provided
            typer.echo("Error: Either --list or --name must be specified", err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"Error showing security rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
