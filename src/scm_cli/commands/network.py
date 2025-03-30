"""
Network module commands for scm-cli.

This module implements set, delete, and load commands for network-related
configurations such as zones, interfaces, etc.
"""

import typer
import yaml
from typing import Optional, List
from pathlib import Path

from ..utils.sdk_client import scm_client
from ..utils.config import load_from_yaml
from ..utils.validators import Zone

# Create app groups for each action type
set_app = typer.Typer(help="Create or update network configurations")
delete_app = typer.Typer(help="Remove network configurations")
load_app = typer.Typer(help="Load network configurations from YAML files")


@set_app.command("zone")
def set_zone(
    folder: str = typer.Option(..., "--folder", help="Folder path for the zone"),
    name: str = typer.Option(..., "--name", help="Name of the zone"),
    mode: str = typer.Option(..., "--mode", help="Zone mode (L2, L3, external, virtual-wire, tunnel)"),
    interfaces: Optional[List[str]] = typer.Option(None, "--interfaces", help="List of interfaces"),
    description: Optional[str] = typer.Option(None, "--description", help="Description of the zone"),
    tags: Optional[List[str]] = typer.Option(None, "--tags", help="List of tags"),
):
    """
    Create or update a security zone.

    Example: scm-cli set network zone --folder Texas --name trust --mode L3 --interfaces ["ethernet1/1"] --description "Trust zone" --tags ["internal"]
    """
    try:
        # Validate input using the Pydantic model
        zone = Zone(
            name=name,
            folder=folder,
            mode=mode,
            interfaces=interfaces or [],
            description=description or "",
            tags=tags or []
        )
        
        # Call the SDK client
        result = scm_client.create_zone(
            folder=zone.folder,
            name=zone.name,
            mode=zone.mode,
            interfaces=zone.interfaces,
            description=zone.description,
            tags=zone.tags
        )
        
        typer.echo(f"Created zone: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating zone: {str(e)}", err=True)
        raise typer.Exit(code=1)


@delete_app.command("zone")
def delete_zone(
    folder: str = typer.Option(..., "--folder", help="Folder path for the zone"),
    name: str = typer.Option(..., "--name", help="Name of the zone to delete"),
):
    """
    Delete a security zone.

    Example: scm-cli delete network zone --folder Texas --name trust
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
        typer.echo(f"Error deleting zone: {str(e)}", err=True)
        raise typer.Exit(code=1)


@load_app.command("zone")
def load_zone(
    file: Path = typer.Option(..., "--file", help="YAML file to load configurations from"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate execution without applying changes"),
):
    """
    Load security zones from a YAML file.

    Example: scm-cli load network zone --file config/security_zones.yml
    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(file, "zones")
        
        if dry_run:
            typer.echo(f"Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["zones"]))
            return
        
        # Apply each zone
        results = []
        for zone_data in config["zones"]:
            # Validate using the Pydantic model
            zone = Zone(**zone_data)
            
            # Call the SDK client to create the zone
            result = scm_client.create_zone(
                folder=zone.folder,
                name=zone.name,
                mode=zone.mode,
                interfaces=zone.interfaces,
                description=zone.description,
                tags=zone.tags
            )
            
            results.append(result)
            typer.echo(f"Applied zone: {result['name']} in folder {result['folder']}")
        
        return results
    except Exception as e:
        typer.echo(f"Error loading zones: {str(e)}", err=True)
        raise typer.Exit(code=1)
