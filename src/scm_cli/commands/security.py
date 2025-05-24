"""Security module commands for scm-cli.

This module implements set, delete, and load commands for security-related
configurations such as security rules, profiles, etc.
"""

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

# ========================================================================================================================================================================================
# SECURITY RULE COMMANDS
# ========================================================================================================================================================================================


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
            result = scm_client.create_security_rule(
                folder=rule.folder,
                name=rule.name,
                source_zones=rule.source_zones,
                destination_zones=rule.destination_zones,
                source_addresses=rule.source_addresses,
                destination_addresses=rule.destination_addresses,
                applications=rule.applications,
                action=rule.action,
                description=rule.description,
                tags=rule.tags,
            )

            results.append(result)
            typer.echo(f"Applied security rule: {result['name']} in folder {result['folder']}")

        return results
    except Exception as e:
        typer.echo(f"Error loading security rules: {str(e)}", err=True)
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
            typer.echo(f"Action: {rule.get('action', 'N/A')}")
            typer.echo(f"Folder: {rule.get('folder', folder)}")
            typer.echo(f"Rulebase: {rulebase}")

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
