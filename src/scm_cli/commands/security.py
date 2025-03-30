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

# Create app groups for each action type
set_app = typer.Typer(help="Create or update security configurations")
delete_app = typer.Typer(help="Remove security configurations")
load_app = typer.Typer(help="Load security configurations from YAML files")

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
        config = load_from_yaml(file, "security_rules")

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
