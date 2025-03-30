"""
Security module commands for scm-cli.

This module implements set, delete, and load commands for security-related
configurations such as security rules.
"""

import typer
import yaml
from typing import Optional, List, Dict, Any
from pathlib import Path

from ..utils.sdk_client import scm_client
from ..utils.config import load_from_yaml
from ..utils.validators import SecurityRule

# Create app groups for each action type
set_app = typer.Typer(help="Create or update security configurations")
delete_app = typer.Typer(help="Remove security configurations")
load_app = typer.Typer(help="Load security configurations from YAML files")


@set_app.command("security-rule")
def set_security_rule(
    folder: str = typer.Option(..., "--folder", help="Folder path for the security rule"),
    name: str = typer.Option(..., "--name", help="Name of the security rule"),
    source_zones: List[str] = typer.Option(..., "--source-zones", help="Source zones for the rule"),
    destination_zones: List[str] = typer.Option(..., "--destination-zones", help="Destination zones for the rule"),
    source_addresses: List[str] = typer.Option(["any"], "--source-addresses", help="Source addresses for the rule"),
    destination_addresses: List[str] = typer.Option(["any"], "--destination-addresses", help="Destination addresses for the rule"),
    applications: List[str] = typer.Option(["any"], "--applications", help="Applications for the rule"),
    action: str = typer.Option("allow", "--action", help="Action for the rule (allow, deny, drop)"),
    description: Optional[str] = typer.Option(None, "--description", help="Description of the security rule"),
    tags: Optional[List[str]] = typer.Option(None, "--tags", help="List of tags"),
    enabled: bool = typer.Option(True, "--enabled/--disabled", help="Whether the rule is enabled"),
):
    """
    Create or update a security rule.

    Example: scm-cli set security security-rule --folder Texas --name allow-web --source-zones ["trust"] --destination-zones ["untrust"] --action allow --applications ["web-browsing"] --description "Allow web traffic"
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
            enabled=enabled
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
            enabled=rule.enabled
        )
        
        typer.echo(f"Created security rule: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating security rule: {str(e)}", err=True)
        raise typer.Exit(code=1)


@delete_app.command("security-rule")
def delete_security_rule(
    folder: str = typer.Option(..., "--folder", help="Folder path for the security rule"),
    name: str = typer.Option(..., "--name", help="Name of the security rule to delete"),
):
    """
    Delete a security rule.

    Example: scm-cli delete security security-rule --folder Texas --name test123
    """
    try:
        # Call the SDK client (mock for now)
        result = scm_client.delete_security_rule(folder=folder, name=name)
        
        if result:
            typer.echo(f"Deleted security rule: {name} from folder {folder}")
        else:
            typer.echo(f"Security rule not found: {name} in folder {folder}", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting security rule: {str(e)}", err=True)
        raise typer.Exit(code=1)


@load_app.command("security-rule")
def load_security_rule(
    file: Path = typer.Option(..., "--file", help="YAML file to load configurations from"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate execution without applying changes"),
):
    """
    Load security rules from a YAML file.

    Example: scm-cli load security security-rule --file config/security_rules.yml
    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(file, "security_rules")
        
        if dry_run:
            typer.echo(f"Dry run mode: would apply the following configurations:")
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
                enabled=rule.enabled
            )
            
            results.append(result)
            typer.echo(f"Applied security rule: {result['name']} in folder {result['folder']}")
        
        return results
    except Exception as e:
        typer.echo(f"Error loading security rules: {str(e)}", err=True)
        raise typer.Exit(code=1)
