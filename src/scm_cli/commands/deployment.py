"""Deployment module commands for scm-cli.

This module implements set, delete, and load commands for deployment-related
configurations such as bandwidth allocations.
"""

from pathlib import Path

import typer
import yaml

from ..utils.config import load_from_yaml
from ..utils.sdk_client import scm_client
from ..utils.validators import BandwidthAllocation

# Create app groups for each action type
set_app = typer.Typer(help="Create or update deployment configurations")
delete_app = typer.Typer(help="Remove deployment configurations")
load_app = typer.Typer(help="Load deployment configurations from YAML files")

# Define typer option constants
FOLDER_OPTION = typer.Option(..., "--folder", help="Folder path for the bandwidth allocation")
NAME_OPTION = typer.Option(..., "--name", help="Name of the bandwidth allocation")
BANDWIDTH_OPTION = typer.Option(..., "--bandwidth", help="Bandwidth value in Mbps")
DESCRIPTION_OPTION = typer.Option(None, "--description", help="Description of the bandwidth allocation")
TAGS_OPTION = typer.Option(None, "--tags", help="List of tags")
FILE_OPTION = typer.Option(..., "--file", help="YAML file to load configurations from")
DRY_RUN_OPTION = typer.Option(False, "--dry-run", help="Simulate execution without applying changes")


@set_app.command("bandwidth-allocation")
def set_bandwidth_allocation(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    bandwidth: int = BANDWIDTH_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    tags: list[str] | None = TAGS_OPTION,
):
    """Create or update a bandwidth allocation.

    Example:
    -------
    scm-cli set deployment bandwidth-allocation \
        --folder Texas \
        --name primary \
        --bandwidth 1000 \
        --description "Primary allocation" \
        --tags ["production"]

    """
    try:
        # Validate input using Pydantic model
        allocation = BandwidthAllocation(
            folder=folder,
            name=name,
            bandwidth=bandwidth,
            description=description or "",
            tags=tags or [],
        )

        # Call the SDK client to create the bandwidth allocation
        result = scm_client.create_bandwidth_allocation(
            folder=allocation.folder,
            name=allocation.name,
            bandwidth=allocation.bandwidth,
            description=allocation.description,
            tags=allocation.tags,
        )

        # Include bandwidth in the output message to match test expectations
        typer.echo(f"Created bandwidth allocation: {result['name']} ({result['bandwidth']} Mbps) in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating bandwidth allocation: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("bandwidth-allocation")
def delete_bandwidth_allocation(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete a bandwidth allocation.

    Example:
    -------
    scm-cli delete deployment bandwidth-allocation \
        --folder Texas \
        --name primary

    """
    try:
        result = scm_client.delete_bandwidth_allocation(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted bandwidth allocation: {name} from folder {folder}")
        else:
            typer.echo(f"Bandwidth allocation not found: {name} in folder {folder}", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting bandwidth allocation: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("bandwidth-allocation")
def load_bandwidth_allocation(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load bandwidth allocations from a YAML file.

    Example: scm-cli load deployment bandwidth-allocation --file config/bandwidth_allocations.yml
    """
    try:
        # Load and parse the YAML file - specifically catch ValueError
        try:
            config = load_from_yaml(file, "bandwidth_allocations")
        except ValueError as ve:
            # Directly capture and re-raise the ValueError with the original message
            typer.echo(f"Error loading bandwidth allocations: {str(ve)}", err=True)
            raise typer.Exit(code=1) from ve

        if dry_run:
            typer.echo("DRY RUN: Would apply the following configurations:")
            for allocation_data in config["bandwidth_allocations"]:
                # Output details about each allocation that would be created
                typer.echo(f"Would create bandwidth allocation: {allocation_data['name']} ({allocation_data['bandwidth']} Mbps) in folder {allocation_data['folder']}")
            typer.echo(yaml.dump(config["bandwidth_allocations"]))
            return

        # Apply each allocation
        results = []
        for allocation_data in config["bandwidth_allocations"]:
            # Validate using the Pydantic model
            allocation = BandwidthAllocation(**allocation_data)

            # Call the SDK client to create the bandwidth allocation
            result = scm_client.create_bandwidth_allocation(
                folder=allocation.folder,
                name=allocation.name,
                bandwidth=allocation.bandwidth,
                description=allocation.description,
                tags=allocation.tags,
            )

            results.append(result)
            # Output details about each allocation
            typer.echo(f"Applied bandwidth allocation: {result['name']} ({result['bandwidth']} Mbps) in folder {result['folder']}")

        # Add summary message that matches test expectations
        typer.echo(f"Loaded {len(results)} bandwidth allocation(s)")
        return results
    except Exception as e:
        # This will catch any other exceptions that might occur
        typer.echo(f"Error loading bandwidth allocations: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
