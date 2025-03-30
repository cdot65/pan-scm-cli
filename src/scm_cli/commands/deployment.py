"""
Deployment module commands for scm-cli.

This module implements set, delete, and load commands for deployment-related
configurations such as bandwidth-allocations.
"""

import typer
import yaml
from typing import Optional, List
from pathlib import Path

from ..utils.sdk_client import scm_client
from ..utils.config import load_from_yaml
from ..utils.validators import BandwidthAllocation

# Create app groups for each action type
set_app = typer.Typer(help="Create or update deployment configurations")
delete_app = typer.Typer(help="Remove deployment configurations")
load_app = typer.Typer(help="Load deployment configurations from YAML files")


@set_app.command("bandwidth-allocation")
def set_bandwidth_allocation(
    folder: str = typer.Option(..., "--folder", help="Folder path for the bandwidth allocation"),
    name: str = typer.Option(..., "--name", help="Name of the bandwidth allocation"),
    bandwidth: int = typer.Option(..., "--bandwidth", help="Bandwidth value in Mbps"),
    description: Optional[str] = typer.Option(None, "--description", help="Description of the bandwidth allocation"),
    tags: Optional[List[str]] = typer.Option(None, "--tags", help="List of tags"),
):
    """
    Create or update a bandwidth allocation.

    Example: scm-cli set deployment bandwidth-allocation --folder Texas --name primary --bandwidth 1000 --description "Primary allocation" --tags ["production"]
    """
    try:
        # Validate input using Pydantic model
        allocation = BandwidthAllocation(
            name=name,
            folder=folder,
            bandwidth=bandwidth,
            description=description or "",
            tags=tags or []
        )
        
        # Call the SDK client
        result = scm_client.create_bandwidth_allocation(
            folder=allocation.folder,
            name=allocation.name,
            bandwidth=allocation.bandwidth,
            description=allocation.description,
            tags=allocation.tags
        )
        
        typer.echo(f"Created bandwidth allocation: {result['name']}, {result['bandwidth']} Mbps in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating bandwidth allocation: {str(e)}", err=True)
        raise typer.Exit(code=1)


@delete_app.command("bandwidth-allocation")
def delete_bandwidth_allocation(
    folder: str = typer.Option(..., "--folder", help="Folder path for the bandwidth allocation"),
    name: str = typer.Option(..., "--name", help="Name of the bandwidth allocation to delete"),
):
    """
    Delete a bandwidth allocation.

    Example: scm-cli delete deployment bandwidth-allocation --folder Texas --name primary
    """
    try:
        # Call the SDK client to delete the bandwidth allocation
        result = scm_client.delete_bandwidth_allocation(folder=folder, name=name)
        
        if result:
            typer.echo(f"Deleted bandwidth allocation: {name} from folder {folder}")
        else:
            typer.echo(f"Bandwidth allocation not found: {name} in folder {folder}", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting bandwidth allocation: {str(e)}", err=True)
        raise typer.Exit(code=1)


@load_app.command("bandwidth-allocation")
def load_bandwidth_allocation(
    file: Path = typer.Option(..., "--file", help="YAML file to load configurations from"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate execution without applying changes"),
):
    """
    Load bandwidth allocations from a YAML file.

    Example: scm-cli load deployment bandwidth-allocation --file config/bandwidth_allocations.yml
    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(file, "bandwidth_allocations")
        
        if dry_run:
            typer.echo(f"Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["bandwidth_allocations"]))
            return
        
        # Apply each bandwidth allocation
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
                tags=allocation.tags
            )
            
            results.append(result)
            typer.echo(f"Applied bandwidth allocation: {result['name']}, {result['bandwidth']} Mbps in folder {result['folder']}")
        
        return results
    except Exception as e:
        typer.echo(f"Error loading bandwidth allocations: {str(e)}", err=True)
        raise typer.Exit(code=1)
