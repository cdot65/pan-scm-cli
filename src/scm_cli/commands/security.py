"""Security module commands for scm-cli.

This module implements set, delete, and load commands for security-related
configurations such as security rules.
"""

from pathlib import Path

import typer
from pydantic import ValidationError

from ..utils.sdk_client import scm_client
from ..utils.validators import SecurityRule, validate_yaml_file

# Create apps for commands
set_app = typer.Typer(help="Set commands for security resources")
delete_app = typer.Typer(help="Delete commands for security resources")
load_app = typer.Typer(help="Load commands for security resources")

# Define typer option constants
FOLDER_OPTION = typer.Option(..., "--folder", help="Folder path for the security rule")
NAME_OPTION = typer.Option(..., "--name", help="Name of the security rule")
SOURCE_ZONES_OPTION = typer.Option(..., "--source-zones", help="Source zones for the rule")
DESTINATION_ZONES_OPTION = typer.Option(..., "--destination-zones", help="Destination zones for the rule")
SOURCE_ADDRESSES_OPTION = typer.Option(["any"], "--source-addresses", help="Source addresses for the rule")
DESTINATION_ADDRESSES_OPTION = typer.Option(["any"], "--destination-addresses", help="Destination addresses for the rule")
APPLICATIONS_OPTION = typer.Option(["any"], "--applications", help="Applications for the rule")
ACTION_OPTION = typer.Option("allow", "--action", help="Action for the rule (allow, deny, drop)")
DESCRIPTION_OPTION = typer.Option(None, "--description", help="Description of the security rule")
TAGS_OPTION = typer.Option(None, "--tags", help="List of tags")
ENABLED_OPTION = typer.Option(True, "--enabled/--disabled", help="Whether the rule is enabled")
FILE_OPTION = typer.Option(..., "--file", help="YAML file to load configurations from")
DRY_RUN_OPTION = typer.Option(False, "--dry-run", help="Simulate execution without applying changes")


@set_app.command("security-rule")
def set_security_rule(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    source_zones: list[str] = SOURCE_ZONES_OPTION,
    destination_zones: list[str] = DESTINATION_ZONES_OPTION,
    source_addresses: list[str] = SOURCE_ADDRESSES_OPTION,
    destination_addresses: list[str] = DESTINATION_ADDRESSES_OPTION,
    applications: list[str] = APPLICATIONS_OPTION,
    action: str = ACTION_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    tags: list[str] | None = TAGS_OPTION,
    enabled: bool = ENABLED_OPTION,
):
    """Create or update a security rule.

    Example:
    -------
        scm-cli set security security-rule --folder Texas --name allow-web \
        --source-zones ["trust"] --destination-zones ["untrust"] \
        --action allow --applications ["web-browsing"] \
        --description "Allow web traffic"

    """
    try:
        # Validate input
        rule = SecurityRule(
            name=name,
            folder=folder,
            source_zones=source_zones,
            destination_zones=destination_zones,
            source_addresses=source_addresses,
            destination_addresses=destination_addresses,
            applications=applications,
            action=action,
            description=description or "",
            tags=tags or [],
            enabled=enabled,
        )

        # Call the SDK client (mock for now)
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
            enabled=rule.enabled,
        )

        typer.echo(f"Created security rule: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating security rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("security-rule")
def delete_security_rule(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete a security rule.

    Example: scm-cli delete security security-rule --folder Texas --name test123
    """
    try:
        # Call the SDK client (mock for now)
        result = scm_client.delete_security_rule(folder=folder, name=name)

        if result:
            typer.echo(f"Deleted security rule: {name} from folder {folder}")
        else:
            error_msg = f"Security rule not found: {name} in folder {folder}"
            typer.echo(error_msg, err=True)
            raise typer.Exit(code=1) from None
    except Exception as e:
        typer.echo(f"Error deleting security rule: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("security-rule")
def load_security_rule(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load security rules from a YAML file.

    Example: scm-cli load security security-rule --file config/security_rules.yml
    """
    try:
        # Load and parse the YAML file
        config = validate_yaml_file(file, "security_rules")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(config["security_rules"])
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
                enabled=rule.enabled,
            )

            results.append(result)
            typer.echo(f"Applied security rule: {result['name']} in folder {result['folder']}")

        return results
    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading security rules: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
