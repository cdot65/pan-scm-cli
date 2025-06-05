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

# ========================================================================================================================================================================================
# TYPER APP CONFIGURATION
# ========================================================================================================================================================================================

# Create app groups for each action type
set_app = typer.Typer(help="Create or update deployment configurations")
delete_app = typer.Typer(help="Remove deployment configurations")
load_app = typer.Typer(help="Load deployment configurations from YAML files")
show_app = typer.Typer(help="Display deployment configurations")
backup_app = typer.Typer(help="Backup deployment configurations to YAML files")

# ========================================================================================================================================================================================
# COMMAND OPTIONS
# ========================================================================================================================================================================================

# Define typer option constants
FOLDER_OPTION = typer.Option(..., "--folder", help="Folder path for the bandwidth allocation")
NAME_OPTION = typer.Option(..., "--name", help="Name of the bandwidth allocation")
BANDWIDTH_OPTION = typer.Option(..., "--bandwidth", help="Bandwidth value in Mbps")
DESCRIPTION_OPTION = typer.Option(None, "--description", help="Description of the bandwidth allocation")
TAGS_OPTION = typer.Option(None, "--tags", help="List of tags")
FILE_OPTION = typer.Option(..., "--file", help="YAML file to load configurations from")
DRY_RUN_OPTION = typer.Option(False, "--dry-run", help="Simulate execution without applying changes")

# ========================================================================================================================================================================================
# BANDWIDTH ALLOCATION COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("bandwidth")
def backup_bandwidth_allocation():
    """Back up all bandwidth allocations to a YAML file.

    The backup file will be named 'bandwidth-allocations.yaml' in the current directory.

    Example:
    -------
    scm-cli backup deployment bandwidth

    Note: Bandwidth allocations are global and do not have a folder parameter.

    """
    try:
        # List all bandwidth allocations
        allocations = scm_client.list_bandwidth_allocations()

        if not allocations:
            typer.echo("No bandwidth allocations found")
            return None

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for allocation in allocations:
            # The list method returns dict objects already, but let's ensure we exclude any None values
            allocation_dict = {k: v for k, v in allocation.items() if v is not None}
            # Remove system fields that shouldn't be in the backup
            allocation_dict.pop("id", None)

            # Map SDK fields to CLI fields for consistency
            if "allocated_bandwidth" in allocation_dict:
                allocation_dict["bandwidth"] = allocation_dict.pop("allocated_bandwidth")

            backup_data.append(allocation_dict)

        # Create the YAML structure
        yaml_data = {"bandwidth_allocations": backup_data}

        # Generate filename (no folder parameter for bandwidth allocations)
        filename = "bandwidth-allocations.yaml"

        # Write to YAML file
        with open(filename, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} bandwidth allocations to {filename}")
        return filename

    except Exception as e:
        typer.echo(f"Error backing up bandwidth allocations: {str(e)}", err=True)
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
            config = load_from_yaml(str(file), "bandwidth_allocations")
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
            return None

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

        # Add a summary message that matches test expectations
        typer.echo(f"Loaded {len(results)} bandwidth allocation(s)")
        return results
    except Exception as e:
        # This will catch any other exceptions that might occur
        typer.echo(f"Error loading bandwidth allocations: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


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


@show_app.command("bandwidth-allocation")
def show_bandwidth_allocation(name: str | None = typer.Option(None, "--name", help="Name of the bandwidth allocation to show")):
    """Display bandwidth allocations.

    Example:
    -------
        # List all bandwidth allocations (default behavior)
        scm-cli show deployment bandwidth-allocation

        # Show a specific bandwidth allocation by name
        scm-cli show deployment bandwidth-allocation --name primary

    Note: Bandwidth allocations do not have a folder parameter.

    """
    try:
        if name:
            # Get a specific bandwidth allocation by name
            allocation = scm_client.get_bandwidth_allocation(name=name)

            typer.echo(f"Bandwidth Allocation: {allocation.get('name', 'N/A')}")
            typer.echo(f"Allocated Bandwidth: {allocation.get('allocated_bandwidth', 'N/A')} Mbps")

            # Display SPN names if present
            spn_names = allocation.get("spn_name_list", [])
            if spn_names:
                typer.echo(f"SPN Names: {', '.join(spn_names)}")
            else:
                typer.echo("SPN Names: None")

            typer.echo(f"Description: {allocation.get('description', 'N/A')}")

            # Display QoS settings if present
            if allocation.get("qos_enabled"):
                typer.echo("QoS Settings:")
                typer.echo("  Enabled: True")
                if allocation.get("qos_guaranteed_ratio") is not None:
                    typer.echo(f"  Guaranteed Ratio: {allocation.get('qos_guaranteed_ratio')}%")

            # Display ID if present
            if allocation.get("id"):
                typer.echo(f"ID: {allocation['id']}")

            return allocation

        else:
            # List all bandwidth allocations (default behavior)
            allocations = scm_client.list_bandwidth_allocations()

            if not allocations:
                typer.echo("No bandwidth allocations found")
                return None

            typer.echo("Bandwidth Allocations:")
            typer.echo("-" * 60)

            for allocation in allocations:
                # Display bandwidth allocation information
                typer.echo(f"Name: {allocation.get('name', 'N/A')}")
                typer.echo(f"  Allocated Bandwidth: {allocation.get('allocated_bandwidth', 'N/A')} Mbps")

                # Display SPN names if present
                spn_names = allocation.get("spn_name_list", [])
                if spn_names:
                    typer.echo(f"  SPN Names: {', '.join(spn_names)}")
                else:
                    typer.echo("  SPN Names: None")

                typer.echo(f"  Description: {allocation.get('description', 'N/A')}")

                # Display QoS settings if enabled
                if allocation.get("qos_enabled"):
                    typer.echo("  QoS Settings:")
                    typer.echo("    Enabled: True")
                    if allocation.get("qos_guaranteed_ratio") is not None:
                        typer.echo(f"    Guaranteed Ratio: {allocation.get('qos_guaranteed_ratio')}%")

                # Display ID if present
                if allocation.get("id"):
                    typer.echo(f"  ID: {allocation['id']}")

                typer.echo("-" * 60)

            return allocations

    except Exception as e:
        typer.echo(f"Error showing bandwidth allocation: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
