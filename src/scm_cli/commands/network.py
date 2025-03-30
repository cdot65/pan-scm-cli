"""Network module commands for scm-cli.

This module implements set, delete, and load commands for network-related
configurations such as zones and interfaces.
"""

from pathlib import Path

import typer
import yaml
from pydantic import ValidationError

from ..utils.config import load_from_yaml
from ..utils.sdk_client import scm_client
from ..utils.validators import Zone

# Create app groups for each action type
set_app = typer.Typer(help="Create or update network configurations")
delete_app = typer.Typer(help="Remove network configurations")
load_app = typer.Typer(help="Load network configurations from YAML files")

# Define typer option constants
FOLDER_OPTION = typer.Option(..., "--folder", help="Folder path for the zone")
NAME_OPTION = typer.Option(..., "--name", help="Name of the zone")
MODE_OPTION = typer.Option(..., "--mode", help="Zone mode (L2, L3, external, virtual-wire, tunnel)")
INTERFACES_OPTION = typer.Option(None, "--interfaces", help="List of interfaces")
DESCRIPTION_OPTION = typer.Option(None, "--description", help="Description of the zone")
TAGS_OPTION = typer.Option(None, "--tags", help="List of tags")
FILE_OPTION = typer.Option(..., "--file", help="YAML file to load configurations from")
DRY_RUN_OPTION = typer.Option(False, "--dry-run", help="Simulate execution without applying changes")


@set_app.command("zone")
def set_zone(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    mode: str = MODE_OPTION,
    interfaces: list[str] | None = INTERFACES_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    tags: list[str] | None = TAGS_OPTION,
):
    """Create or update a security zone.

    Example:
    -------
        scm-cli set network zone --folder Texas --name trust --mode L3 \
        --interfaces ["ethernet1/1"] --description "Trust zone" --tags ["internal"]

    """
    try:
        # Validate input using the Pydantic model
        zone = Zone(
            name=name,
            folder=folder,
            mode=mode,
            interfaces=interfaces or [],
            description=description or "",
            tags=tags or [],
        )

        # Call the SDK client
        result = scm_client.create_zone(
            folder=zone.folder,
            name=zone.name,
            mode=zone.mode,
            interfaces=zone.interfaces,
            description=zone.description,
            tags=zone.tags,
        )

        typer.echo(f"Created zone: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating security zone: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("zone")
def delete_zone(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete a security zone.

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
        typer.echo(f"Error deleting security zone: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("zone")
def load_zone(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load security zones from a YAML file.

    Example: scm-cli load network zone --file config/security_zones.yml
    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(file, "zones")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
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
                tags=zone.tags,
            )

            results.append(result)
            typer.echo(f"Applied zone: {result['name']} in folder {result['folder']}")

        return results
    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading security zones: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
