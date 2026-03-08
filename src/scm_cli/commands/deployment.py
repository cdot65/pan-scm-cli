"""Deployment module commands for scm.

This module implements set, delete, and load commands for deployment-related
configurations such as bandwidth allocations.
"""

from pathlib import Path
from typing import Any

import typer
import yaml

from ..utils.config import load_from_yaml
from ..utils.sdk_client import scm_client
from ..utils.validators import BandwidthAllocation, BGPRouting, InternalDNSServer, RemoteNetwork, ServiceConnection

# ========================================================================================================================================================================================
# TYPER APP CONFIGURATION
# ========================================================================================================================================================================================

# Create app groups for each action type
set_app = typer.Typer(help="Create or update SASE configurations")
delete_app = typer.Typer(help="Remove SASE configurations")
load_app = typer.Typer(help="Load SASE configurations from YAML files")
show_app = typer.Typer(help="Display SASE configurations")
backup_app = typer.Typer(help="Backup SASE configurations to YAML files")

# ========================================================================================================================================================================================
# COMMAND OPTIONS
# ========================================================================================================================================================================================

# Define typer option constants
NAME_OPTION = typer.Option(..., "--name", help="Name of the bandwidth allocation")
BANDWIDTH_OPTION = typer.Option(..., "--bandwidth", help="Bandwidth value in Mbps")
DESCRIPTION_OPTION = typer.Option(None, "--description", help="Description of the bandwidth allocation")
FILE_OPTION = typer.Option(..., "--file", help="YAML file to load configurations from")
DRY_RUN_OPTION = typer.Option(False, "--dry-run", help="Simulate execution without applying changes")

# List options for multiline definitions
SUBNETS_SC_OPTION = typer.Option(
    None,
    "--subnets",
    help="Subnets for the service connection",
)
SUBNETS_RN_OPTION = typer.Option(
    None,
    "--subnets",
    help="Subnets for the remote network",
)

# ========================================================================================================================================================================================
# BANDWIDTH ALLOCATION COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("bandwidth-allocation")
def backup_bandwidth_allocation():
    """Back up all bandwidth allocations to a YAML file.

    The backup file will be named 'bandwidth-allocations.yaml' in the current directory.

    Example:
    -------
    scm backup sase bandwidth

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
    name: str = NAME_OPTION,
    spn_name_list: str = typer.Option(..., "--spn-name-list", help="SPN names (comma-separated if multiple)"),
):
    """Delete a bandwidth allocation.

    Example:
    -------
    scm delete sase bandwidth-allocation \
        --name primary \
        --spn-name-list ["spn1", "spn2"]

    Note: Bandwidth allocations are global resources and do not require a folder parameter.

    """
    try:
        # Defensive check: Only accept comma-separated string, not list
        if isinstance(spn_name_list, list):
            typer.echo("Error: --spn-name-list must be a comma-separated string (e.g., --spn-name-list foo,bar)", err=True)
            raise typer.Exit(code=1)

        # Convert comma-separated string to list
        spn_list = ([spn.strip() for spn in spn_name_list.split(",")] if "," in spn_name_list else [spn_name_list.strip()]) if isinstance(spn_name_list, str) else spn_name_list

        result = scm_client.delete_bandwidth_allocation(name=name, spn_name_list=spn_list)
        if result:
            typer.echo(f"Deleted bandwidth allocation: {name}")
        else:
            typer.echo(f"Bandwidth allocation not found: {name}", err=True)
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

    Example: scm load sase bandwidth-allocation --file config/bandwidth_allocations.yml
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
                spn_names = allocation_data.get("spn_name_list", [])
                typer.echo(f"Would create bandwidth allocation: {allocation_data['name']} ({allocation_data['bandwidth']} Mbps) with SPNs: {spn_names}")
            typer.echo(yaml.dump(config["bandwidth_allocations"]))
            return None

        # Apply each allocation
        results = []
        for allocation_data in config["bandwidth_allocations"]:
            # Extract description before validation since it's not in the model
            description = allocation_data.pop("description", "")

            # Validate using the Pydantic model
            allocation = BandwidthAllocation(**allocation_data)

            # Call the SDK client to create the bandwidth allocation
            result = scm_client.create_bandwidth_allocation(
                name=allocation.name,
                bandwidth=allocation.bandwidth,
                spn_name_list=allocation.spn_name_list,
                description=description,
                tags=allocation.tags,
            )

            results.append(result)
            # Output details about each allocation
            bandwidth_value = result.get("allocated_bandwidth", result.get("bandwidth", "N/A"))
            typer.echo(f"Applied bandwidth allocation: {result['name']} ({bandwidth_value} Mbps)")

        # Add a summary message that matches test expectations
        typer.echo(f"Loaded {len(results)} bandwidth allocation(s)")
        return results
    except Exception as e:
        # This will catch any other exceptions that might occur
        typer.echo(f"Error loading bandwidth allocations: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("bandwidth-allocation")
def set_bandwidth_allocation(
    name: str = NAME_OPTION,
    bandwidth: int = BANDWIDTH_OPTION,
    spn_name_list: str = typer.Option(..., "--spn-name-list", help="SPN names (comma-separated if multiple)"),
    description: str | None = DESCRIPTION_OPTION,
    tags: str | None = typer.Option(None, "--tags", help="Tags (comma-separated if multiple)"),
):
    """Create or update a bandwidth allocation.

    Example:
    -------
    scm set sase bandwidth-allocation \
        --name primary \
        --bandwidth 1000 \
        --spn-name-list ["spn1", "spn2"] \
        --description "Primary allocation" \
        --tags ["production"]

    Note: Bandwidth allocations are global resources and do not require a folder parameter.

    """
    try:
        # Convert comma-separated strings to lists
        spn_list = ([spn.strip() for spn in spn_name_list.split(",")] if "," in spn_name_list else [spn_name_list.strip()]) if isinstance(spn_name_list, str) else spn_name_list

        tag_list = ([tag.strip() for tag in tags.split(",")] if tags and "," in tags else [tags.strip()] if tags else []) if isinstance(tags, str) else tags or []

        # Validate input using Pydantic model
        allocation = BandwidthAllocation(
            name=name,
            bandwidth=bandwidth,
            spn_name_list=spn_list,
            tags=tag_list,
        )

        # Call the SDK client to create the bandwidth allocation
        result = scm_client.create_bandwidth_allocation(
            name=allocation.name,
            bandwidth=allocation.bandwidth,
            spn_name_list=allocation.spn_name_list,
            description=description or "",
            tags=allocation.tags,
        )

        # Include bandwidth in the output message to match test expectations
        typer.echo(f"Created bandwidth allocation: {result['name']} ({result.get('allocated_bandwidth', result.get('bandwidth', 'N/A'))} Mbps)")
        return result
    except Exception as e:
        typer.echo(f"Error creating bandwidth allocation: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("bandwidth-allocation")
def show_bandwidth_allocation(
    name: str | None = typer.Option(None, "--name", help="Name of the bandwidth allocation to show"),
):
    """Display bandwidth allocations.

    Example:
    -------
        # List all bandwidth allocations (default behavior)
        scm show sase bandwidth-allocation

        # Show a specific bandwidth allocation by name
        scm show sase bandwidth-allocation --name primary

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


# ========================================================================================================================================================================================
# SERVICE CONNECTION COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("service-connection")
def backup_service_connection():
    """Back up all service connections to a YAML file.

    The backup file will be named 'service-connections.yaml' in the current directory.

    Example:
    -------
    scm backup sase service-connection

    """
    try:
        # List all service connections
        connections = scm_client.list_service_connections()

        if not connections:
            typer.echo("No service connections found")
            return None

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for connection in connections:
            # The list method returns dict objects already
            connection_dict = {k: v for k, v in connection.items() if v is not None}
            # Remove system fields that shouldn't be in the backup
            connection_dict.pop("id", None)

            # Flatten nested BGP peer configuration for CLI consistency
            if "bgp_peer" in connection_dict:
                bgp_peer = connection_dict.pop("bgp_peer")
                if bgp_peer:
                    for key, value in bgp_peer.items():
                        connection_dict[f"bgp_peer_{key}"] = value

            # Flatten BGP protocol configuration
            if "protocol" in connection_dict and "bgp" in connection_dict["protocol"]:
                bgp = connection_dict["protocol"]["bgp"]
                connection_dict.pop("protocol")
                for key, value in bgp.items():
                    if key != "enable" or value is True:
                        connection_dict[f"bgp_{key}"] = value

            # Flatten QoS configuration
            if "qos" in connection_dict:
                qos = connection_dict.pop("qos")
                if qos:
                    for key, value in qos.items():
                        if key != "enable" or value is True:
                            connection_dict[f"qos_{key}"] = value

            backup_data.append(connection_dict)

        # Create the YAML structure
        yaml_data = {"service_connections": backup_data}

        # Generate filename
        filename = "service-connections.yaml"

        # Write to YAML file
        with open(filename, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} service connections to {filename}")
        return filename

    except Exception as e:
        typer.echo(f"Error backing up service connections: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("service-connection")
def delete_service_connection(
    name: str = NAME_OPTION,
):
    """Delete a service connection.

    Example:
    -------
    scm delete sase service-connection --name primary-connection

    """
    try:
        result = scm_client.delete_service_connection(name=name)
        if result:
            typer.echo(f"Deleted service connection: {name}")
        else:
            typer.echo(f"Service connection not found: {name}", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting service connection: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("service-connection")
def load_service_connection(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load service connections from a YAML file.

    Example: scm load sase service-connection --file config/service_connections.yml
    """
    try:
        # Load and parse the YAML file
        try:
            config = load_from_yaml(str(file), "service_connections")
        except ValueError as ve:
            typer.echo(f"Error loading service connections: {str(ve)}", err=True)
            raise typer.Exit(code=1) from ve

        if dry_run:
            typer.echo("DRY RUN: Would apply the following configurations:")
            for connection_data in config["service_connections"]:
                typer.echo(f"Would create service connection: {connection_data['name']}")
            typer.echo(yaml.dump(config["service_connections"]))
            return None

        # Apply each connection
        results = []
        for connection_data in config["service_connections"]:
            # Validate using the Pydantic model
            connection = ServiceConnection(**connection_data)

            # Convert to SDK model format
            sdk_data = connection.to_sdk_model()

            # Call the SDK client to create the service connection
            result = scm_client.create_service_connection(**sdk_data)

            results.append(result)
            # Show appropriate message based on action taken
            action = result.get("__action__", "created")
            if action == "created":
                typer.echo(f"Created service connection: {result['name']}")
            elif action == "updated":
                typer.echo(f"Updated service connection: {result['name']}")
            else:  # no_change
                typer.echo(f"Service connection '{result['name']}' already up to date")

        typer.echo(f"Loaded {len(results)} service connection(s)")
        return results
    except Exception as e:
        typer.echo(f"Error loading service connections: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("service-connection")
def set_service_connection(
    name: str = NAME_OPTION,
    ipsec_tunnel: str = typer.Option(..., "--ipsec-tunnel", help="IPsec tunnel for the service connection"),
    region: str = typer.Option(..., "--region", help="Region for the service connection"),
    onboarding_type: str = typer.Option("classic", "--onboarding-type", help="Onboarding type"),
    backup_sc: str | None = typer.Option(None, "--backup-sc", help="Backup service connection"),
    nat_pool: str | None = typer.Option(None, "--nat-pool", help="NAT pool"),
    source_nat: bool | None = typer.Option(None, "--source-nat", help="Enable source NAT"),
    subnets: list[str] | None = SUBNETS_SC_OPTION,
    bgp_enable: bool | None = typer.Option(None, "--bgp-enable", help="Enable BGP"),
    bgp_peer_as: str | None = typer.Option(None, "--bgp-peer-as", help="BGP peer AS number"),
    bgp_peer_ip_address: str | None = typer.Option(None, "--bgp-peer-ip", help="BGP peer IP address"),
    bgp_local_ip_address: str | None = typer.Option(None, "--bgp-local-ip", help="BGP local IP address"),
    bgp_secret: str | None = typer.Option(None, "--bgp-secret", help="BGP authentication secret"),
    qos_enable: bool | None = typer.Option(None, "--qos-enable", help="Enable QoS"),
    qos_profile: str | None = typer.Option(None, "--qos-profile", help="QoS profile name"),
):
    """Create or update a service connection.

    Example:
    -------
    scm set sase service-connection \
        --name primary-connection \
        --ipsec-tunnel ipsec-tunnel-1 \
        --region us-east-1 \
        --subnets ["10.0.0.0/24", "10.0.1.0/24"] \
        --bgp-enable \
        --bgp-peer-as 65000 \
        --bgp-peer-ip 192.168.1.1 \
        --bgp-local-ip 192.168.1.2

    """
    try:
        # Build connection data
        connection_data: dict[str, Any] = {
            "name": name,
            "folder": "Service Connections",
            "ipsec_tunnel": ipsec_tunnel,
            "region": region,
            "onboarding_type": onboarding_type,
        }

        # Add optional fields
        if backup_sc:
            connection_data["backup_SC"] = backup_sc
        if nat_pool:
            connection_data["nat_pool"] = nat_pool
        if source_nat is not None:
            connection_data["source_nat"] = source_nat
        if subnets:
            connection_data["subnets"] = subnets

        # Add BGP configuration
        if bgp_enable is not None:
            connection_data["bgp_enable"] = bgp_enable
        if bgp_peer_as:
            connection_data["bgp_peer_as"] = bgp_peer_as
        if bgp_peer_ip_address:
            connection_data["bgp_peer_ip_address"] = bgp_peer_ip_address
        if bgp_local_ip_address:
            connection_data["bgp_local_ip_address"] = bgp_local_ip_address
        if bgp_secret:
            connection_data["bgp_secret"] = bgp_secret

        # Add QoS configuration
        if qos_enable is not None:
            connection_data["qos_enable"] = qos_enable
        if qos_profile:
            connection_data["qos_profile"] = qos_profile

        # Validate using Pydantic model
        connection = ServiceConnection(**connection_data)

        # Convert to SDK model format
        sdk_data = connection.to_sdk_model()

        # Call the SDK client to create the service connection
        result = scm_client.create_service_connection(**sdk_data)

        # Show appropriate message based on action taken
        action = result.get("__action__", "created")
        if action == "created":
            typer.echo(f"Created service connection: {result['name']}")
        elif action == "updated":
            typer.echo(f"Updated service connection: {result['name']}")
        else:  # no_change
            typer.echo(f"Service connection '{result['name']}' already up to date")
        return result
    except Exception as e:
        typer.echo(f"Error creating service connection: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("service-connection")
def show_service_connection(
    name: str | None = typer.Option(None, "--name", help="Name of the service connection to show"),
):
    """Display service connections.

    Example:
    -------
        # List all service connections
        scm show sase service-connection

        # Show a specific service connection by name
        scm show sase service-connection --name primary-connection

    """
    try:
        if name:
            # Get a specific service connection by name
            connection = scm_client.get_service_connection(name=name)

            typer.echo(f"Service Connection: {connection.get('name', 'N/A')}")
            typer.echo(f"IPsec Tunnel: {connection.get('ipsec_tunnel', 'N/A')}")
            typer.echo(f"Region: {connection.get('region', 'N/A')}")
            typer.echo(f"Onboarding Type: {connection.get('onboarding_type', 'N/A')}")

            # Display optional fields if present
            if connection.get("backup_SC"):
                typer.echo(f"Backup SC: {connection['backup_SC']}")
            if connection.get("nat_pool"):
                typer.echo(f"NAT Pool: {connection['nat_pool']}")
            if connection.get("source_nat") is not None:
                typer.echo(f"Source NAT: {connection['source_nat']}")
            if connection.get("subnets"):
                typer.echo(f"Subnets: {', '.join(connection['subnets'])}")

            # Display BGP settings if present
            if connection.get("protocol") and connection["protocol"].get("bgp"):
                bgp = connection["protocol"]["bgp"]
                typer.echo("BGP Settings:")
                typer.echo(f"  Enabled: {bgp.get('enable', False)}")
                if bgp.get("peer_as"):
                    typer.echo(f"  Peer AS: {bgp['peer_as']}")
                if bgp.get("peer_ip_address"):
                    typer.echo(f"  Peer IP: {bgp['peer_ip_address']}")
                if bgp.get("local_ip_address"):
                    typer.echo(f"  Local IP: {bgp['local_ip_address']}")

            # Display QoS settings if present
            if connection.get("qos"):
                qos = connection["qos"]
                typer.echo("QoS Settings:")
                typer.echo(f"  Enabled: {qos.get('enable', False)}")
                if qos.get("qos_profile"):
                    typer.echo(f"  Profile: {qos['qos_profile']}")

            # Display ID if present
            if connection.get("id"):
                typer.echo(f"ID: {connection['id']}")

            return connection

        else:
            # List all service connections in the folder
            connections = scm_client.list_service_connections()

            if not connections:
                typer.echo("No service connections found")
                return None

            typer.echo("Service Connections:")
            typer.echo("-" * 60)

            for connection in connections:
                typer.echo(f"Name: {connection.get('name', 'N/A')}")
                typer.echo(f"  IPsec Tunnel: {connection.get('ipsec_tunnel', 'N/A')}")
                typer.echo(f"  Region: {connection.get('region', 'N/A')}")
                typer.echo(f"  Onboarding Type: {connection.get('onboarding_type', 'N/A')}")

                # Show BGP status if configured
                if connection.get("protocol") and connection["protocol"].get("bgp"):
                    bgp = connection["protocol"]["bgp"]
                    if bgp.get("enable"):
                        typer.echo(f"  BGP: Enabled (AS {bgp.get('peer_as', 'N/A')})")

                # Show QoS status if configured
                if connection.get("qos") and connection["qos"].get("enable"):
                    typer.echo("  QoS: Enabled")

                # Display ID if present
                if connection.get("id"):
                    typer.echo(f"  ID: {connection['id']}")

                typer.echo("-" * 60)

            return connections

    except Exception as e:
        typer.echo(f"Error showing service connection: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# REMOTE NETWORK COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("remote-network")
def backup_remote_network():
    """Back up all remote networks to a YAML file.

    The backup file will be named 'remote-networks.yaml' in the current directory.

    Example:
    -------
    scm backup sase remote-network

    """
    try:
        # List all remote networks
        networks = scm_client.list_remote_networks()

        if not networks:
            typer.echo("No remote networks found")
            return None

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for network in networks:
            # The list method returns dict objects already
            network_dict = {k: v for k, v in network.items() if v is not None}
            # Remove system fields that shouldn't be in the backup
            network_dict.pop("id", None)

            # Flatten BGP protocol configuration for CLI consistency
            if "protocol" in network_dict and "bgp" in network_dict["protocol"]:
                bgp = network_dict["protocol"]["bgp"]
                network_dict.pop("protocol")
                for key, value in bgp.items():
                    if key != "enable" or value is True:
                        network_dict[f"bgp_{key}"] = value

            backup_data.append(network_dict)

        # Create the YAML structure
        yaml_data = {"remote_networks": backup_data}

        # Generate filename
        filename = "remote-networks.yaml"

        # Write to YAML file
        with open(filename, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} remote networks to {filename}")
        return filename

    except Exception as e:
        typer.echo(f"Error backing up remote networks: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("remote-network")
def delete_remote_network(
    name: str = NAME_OPTION,
):
    """Delete a remote network.

    Example:
    -------
    scm delete sase remote-network --name branch-network

    """
    try:
        result = scm_client.delete_remote_network(
            name=name,
        )
        if result:
            typer.echo(f"Deleted remote network: {name}")
        else:
            typer.echo(f"Remote network not found: {name}", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting remote network: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("remote-network")
def load_remote_network(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load remote networks from a YAML file.

    Example: scm load sase remote-network --file config/remote_networks.yml
    """
    try:
        # Load and parse the YAML file
        try:
            config = load_from_yaml(str(file), "remote_networks")
        except ValueError as ve:
            typer.echo(f"Error loading remote networks: {str(ve)}", err=True)
            raise typer.Exit(code=1) from ve

        if dry_run:
            typer.echo("DRY RUN: Would apply the following configurations:")
            for network_data in config["remote_networks"]:
                typer.echo(f"Would create remote network: {network_data['name']}")
            typer.echo(yaml.dump(config["remote_networks"]))
            return None

        # Apply each network
        results = []
        for network_data in config["remote_networks"]:
            # Validate using the Pydantic model
            network = RemoteNetwork(**network_data)

            # Convert to SDK model format
            sdk_data = network.to_sdk_model()

            # Call the SDK client to create the remote network
            result = scm_client.create_remote_network(**sdk_data)

            results.append(result)
            # Show appropriate message based on action taken
            action = result.get("__action__", "created")
            if action == "created":
                typer.echo(f"Created remote network: {result['name']}")
            elif action == "updated":
                typer.echo(f"Updated remote network: {result['name']}")
            else:  # no_change
                typer.echo(f"Remote network '{result['name']}' already up to date")

        typer.echo(f"Loaded {len(results)} remote network(s)")
        return results
    except Exception as e:
        typer.echo(f"Error loading remote networks: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("remote-network")
def set_remote_network(
    name: str = NAME_OPTION,
    region: str = typer.Option(..., "--region", help="Region for the remote network"),
    license_type: str = typer.Option("FWAAS-AGGREGATE", "--license-type", help="License type"),
    description: str | None = DESCRIPTION_OPTION,
    subnets: list[str] | None = SUBNETS_RN_OPTION,
    spn_name: str | None = typer.Option(None, "--spn-name", help="SPN name (required for FWAAS-AGGREGATE)"),
    ecmp_load_balancing: str = typer.Option("disable", "--ecmp-load-balancing", help="Enable or disable ECMP"),
    ipsec_tunnel: str | None = typer.Option(None, "--ipsec-tunnel", help="IPsec tunnel (required when ECMP disabled)"),
    secondary_ipsec_tunnel: str | None = typer.Option(None, "--secondary-ipsec-tunnel", help="Secondary IPsec tunnel"),
    bgp_enable: bool | None = typer.Option(None, "--bgp-enable", help="Enable BGP"),
    bgp_peer_as: str | None = typer.Option(None, "--bgp-peer-as", help="BGP peer AS number"),
    bgp_peer_ip_address: str | None = typer.Option(None, "--bgp-peer-ip", help="BGP peer IP address"),
    bgp_local_ip_address: str | None = typer.Option(None, "--bgp-local-ip", help="BGP local IP address"),
    bgp_secret: str | None = typer.Option(None, "--bgp-secret", help="BGP authentication secret"),
):
    """Create or update a remote network.

    Example:
    -------
    scm set sase remote-network \
        --name branch-network \
        --region us-west-1 \
        --license-type FWAAS-AGGREGATE \
        --spn-name spn-west \
        --subnets ["10.1.0.0/24", "10.1.1.0/24"] \
        --ipsec-tunnel ipsec-tunnel-1 \
        --bgp-enable \
        --bgp-peer-as 65001 \
        --bgp-peer-ip 192.168.2.1 \
        --bgp-local-ip 192.168.2.2

    """
    try:
        # Build network data
        network_data: dict[str, Any] = {
            "name": name,
            "folder": "Remote Networks",
            "region": region,
            "license_type": license_type,
            "ecmp_load_balancing": ecmp_load_balancing,
        }

        # Add optional fields
        if description:
            network_data["description"] = description
        if subnets:
            network_data["subnets"] = subnets
        if spn_name:
            network_data["spn_name"] = spn_name
        if ipsec_tunnel:
            network_data["ipsec_tunnel"] = ipsec_tunnel
        if secondary_ipsec_tunnel:
            network_data["secondary_ipsec_tunnel"] = secondary_ipsec_tunnel

        # Add BGP configuration
        if bgp_enable is not None:
            network_data["bgp_enable"] = bgp_enable
        if bgp_peer_as:
            network_data["bgp_peer_as"] = bgp_peer_as
        if bgp_peer_ip_address:
            network_data["bgp_peer_ip_address"] = bgp_peer_ip_address
        if bgp_local_ip_address:
            network_data["bgp_local_ip_address"] = bgp_local_ip_address
        if bgp_secret:
            network_data["bgp_secret"] = bgp_secret

        # Validate using Pydantic model
        network = RemoteNetwork(**network_data)

        # Convert to SDK model format
        sdk_data = network.to_sdk_model()

        # Call the SDK client to create the remote network
        result = scm_client.create_remote_network(**sdk_data)

        # Show appropriate message based on action taken
        action = result.get("__action__", "created")
        if action == "created":
            typer.echo(f"Created remote network: {result['name']}")
        elif action == "updated":
            typer.echo(f"Updated remote network: {result['name']}")
        else:  # no_change
            typer.echo(f"Remote network '{result['name']}' already up to date")
        return result
    except Exception as e:
        typer.echo(f"Error creating remote network: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("remote-network")
def show_remote_network(
    name: str | None = typer.Option(None, "--name", help="Name of the remote network to show"),
):
    """Display remote networks.

    Example:
    -------
        # List all remote networks
        scm show sase remote-network

        # Show a specific remote network by name
        scm show sase remote-network --name branch-network

    """
    try:
        if name:
            # Get a specific remote network by name
            network = scm_client.get_remote_network(
                name=name,
            )

            typer.echo(f"Remote Network: {network.get('name', 'N/A')}")
            typer.echo(f"Region: {network.get('region', 'N/A')}")
            typer.echo(f"License Type: {network.get('license_type', 'N/A')}")

            # Display optional fields if present
            if network.get("description"):
                typer.echo(f"Description: {network['description']}")
            if network.get("subnets"):
                typer.echo(f"Subnets: {', '.join(network['subnets'])}")
            if network.get("spn_name"):
                typer.echo(f"SPN Name: {network['spn_name']}")

            # Display ECMP and tunnel configuration
            typer.echo(f"ECMP Load Balancing: {network.get('ecmp_load_balancing', 'N/A')}")
            if network.get("ipsec_tunnel"):
                typer.echo(f"IPsec Tunnel: {network['ipsec_tunnel']}")
            if network.get("secondary_ipsec_tunnel"):
                typer.echo(f"Secondary IPsec Tunnel: {network['secondary_ipsec_tunnel']}")
            if network.get("ecmp_tunnels"):
                typer.echo("ECMP Tunnels:")
                for idx, tunnel in enumerate(network["ecmp_tunnels"], 1):
                    typer.echo(f"  Tunnel {idx}: {tunnel}")

            # Display BGP settings if present
            if network.get("protocol") and network["protocol"].get("bgp"):
                bgp = network["protocol"]["bgp"]
                typer.echo("BGP Settings:")
                typer.echo(f"  Enabled: {bgp.get('enable', False)}")
                if bgp.get("peer_as"):
                    typer.echo(f"  Peer AS: {bgp['peer_as']}")
                if bgp.get("peer_ip_address"):
                    typer.echo(f"  Peer IP: {bgp['peer_ip_address']}")
                if bgp.get("local_ip_address"):
                    typer.echo(f"  Local IP: {bgp['local_ip_address']}")
                if bgp.get("peering_type"):
                    typer.echo(f"  Peering Type: {bgp['peering_type']}")

            # Display ID if present
            if network.get("id"):
                typer.echo(f"ID: {network['id']}")

            return network

        else:
            # List all remote networks
            networks = scm_client.list_remote_networks()

            if not networks:
                typer.echo("No remote networks found")
                return None

            typer.echo("Remote Networks:")
            typer.echo("-" * 60)

            for network in networks:
                typer.echo(f"Name: {network.get('name', 'N/A')}")
                typer.echo(f"  Region: {network.get('region', 'N/A')}")
                typer.echo(f"  License Type: {network.get('license_type', 'N/A')}")

                # Show subnets if configured
                if network.get("subnets"):
                    typer.echo(f"  Subnets: {', '.join(network['subnets'][:3])}{'...' if len(network['subnets']) > 3 else ''}")

                # Show ECMP status
                typer.echo(f"  ECMP: {network.get('ecmp_load_balancing', 'N/A')}")

                # Show BGP status if configured
                if network.get("protocol") and network["protocol"].get("bgp"):
                    bgp = network["protocol"]["bgp"]
                    if bgp.get("enable"):
                        typer.echo(f"  BGP: Enabled (AS {bgp.get('peer_as', 'N/A')})")

                # Display ID if present
                if network.get("id"):
                    typer.echo(f"  ID: {network['id']}")

                typer.echo("-" * 60)

            return networks

    except Exception as e:
        typer.echo(f"Error showing remote network: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# BGP ROUTING COMMANDS
# ========================================================================================================================================================================================

# BGP Routing option constants
BGP_BACKBONE_OPTION = typer.Option(
    ...,
    "--backbone-routing",
    help="Backbone routing mode (no-asymmetric-routing, asymmetric-routing-only, asymmetric-routing-with-load-share)",
)
BGP_ROUTING_PREF_OPTION = typer.Option(None, "--routing-preference", help="Routing preference (default, hot_potato_routing)")
BGP_ACCEPT_SC_OPTION = typer.Option(False, "--accept-route-over-sc", help="Accept routes over service connections")
BGP_OUTBOUND_ROUTES_OPTION = typer.Option(None, "--outbound-routes", help="Outbound routes for services (comma-separated CIDR)")
BGP_HOST_ROUTE_OPTION = typer.Option(False, "--add-host-route-to-ike-peer", help="Add host route to IKE peer")
BGP_WITHDRAW_STATIC_OPTION = typer.Option(False, "--withdraw-static-route", help="Withdraw static routes")


@delete_app.command("bgp-routing")
def delete_bgp_routing():
    """Reset BGP routing configuration to defaults.

    Example:
    -------
    scm delete sase bgp-routing

    Note: BGP routing is a singleton; delete resets to defaults.

    """
    try:
        result = scm_client.delete_bgp_routing()
        if result:
            typer.echo("Reset BGP routing configuration to defaults")
        else:
            typer.echo("Error resetting BGP routing configuration", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error resetting BGP routing: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("bgp-routing")
def set_bgp_routing(
    backbone_routing: str = BGP_BACKBONE_OPTION,
    routing_preference: str | None = BGP_ROUTING_PREF_OPTION,
    accept_route_over_sc: bool = BGP_ACCEPT_SC_OPTION,
    outbound_routes: str | None = BGP_OUTBOUND_ROUTES_OPTION,
    add_host_route_to_ike_peer: bool = BGP_HOST_ROUTE_OPTION,
    withdraw_static_route: bool = BGP_WITHDRAW_STATIC_OPTION,
):
    r"""Create or update BGP routing configuration.

    Example:
    -------
    scm set sase bgp-routing \
        --backbone-routing no-asymmetric-routing \
        --routing-preference default \
        --accept-route-over-sc

    Note: BGP routing is a singleton configuration object.

    """
    try:
        # Parse outbound routes
        outbound_list = [r.strip() for r in outbound_routes.split(",")] if outbound_routes else []

        # Validate using Pydantic model
        bgp = BGPRouting(
            backbone_routing=backbone_routing,
            routing_preference=routing_preference,
            accept_route_over_sc=accept_route_over_sc,
            outbound_routes_for_services=outbound_list,
            add_host_route_to_ike_peer=add_host_route_to_ike_peer,
            withdraw_static_route=withdraw_static_route,
        )

        # Convert to SDK model format
        sdk_data = bgp.to_sdk_model()

        # Call the SDK client
        result = scm_client.create_bgp_routing(**sdk_data)

        # Show appropriate message based on action taken
        action = result.get("__action__", "created")
        if action == "created":
            typer.echo(f"Created BGP routing configuration (backbone: {result.get('backbone_routing', 'N/A')})")
        elif action == "updated":
            typer.echo(f"Updated BGP routing configuration (backbone: {result.get('backbone_routing', 'N/A')})")
        else:
            typer.echo("BGP routing configuration already up to date")
        return result
    except Exception as e:
        typer.echo(f"Error creating BGP routing: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("bgp-routing")
def show_bgp_routing():
    """Display BGP routing configuration.

    Example:
    -------
    scm show sase bgp-routing

    Note: BGP routing is a singleton; always shows the current configuration.

    """
    try:
        config = scm_client.get_bgp_routing()

        typer.echo("BGP Routing Configuration:")
        typer.echo("-" * 60)
        typer.echo(f"Backbone Routing: {config.get('backbone_routing', 'N/A')}")

        # Display routing preference
        routing_pref = config.get("routing_preference")
        if routing_pref:
            if isinstance(routing_pref, dict):
                pref_type = "default" if "default" in routing_pref else "hot_potato_routing" if "hot_potato_routing" in routing_pref else str(routing_pref)
            else:
                pref_type = str(routing_pref)
            typer.echo(f"Routing Preference: {pref_type}")

        typer.echo(f"Accept Route Over SC: {config.get('accept_route_over_SC', False)}")

        outbound = config.get("outbound_routes_for_services", [])
        if outbound:
            typer.echo(f"Outbound Routes: {', '.join(outbound)}")
        else:
            typer.echo("Outbound Routes: None")

        typer.echo(f"Add Host Route to IKE Peer: {config.get('add_host_route_to_ike_peer', False)}")
        typer.echo(f"Withdraw Static Route: {config.get('withdraw_static_route', False)}")

        return config

    except Exception as e:
        typer.echo(f"Error showing BGP routing: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# INTERNAL DNS SERVER COMMANDS
# ========================================================================================================================================================================================

# Internal DNS Server option constants
DNS_NAME_OPTION = typer.Option(..., "--name", help="Name of the internal DNS server")
DNS_DOMAIN_OPTION = typer.Option(..., "--domain-name", help="DNS domain name(s) (comma-separated if multiple)")
DNS_PRIMARY_OPTION = typer.Option(..., "--primary", help="Primary DNS server IP address")
DNS_SECONDARY_OPTION = typer.Option(None, "--secondary", help="Secondary DNS server IP address")
DNS_FILE_OPTION = typer.Option(..., "--file", help="YAML file to load configurations from")
DNS_DRY_RUN_OPTION = typer.Option(False, "--dry-run", help="Simulate execution without applying changes")


@backup_app.command("internal-dns-server")
def backup_internal_dns_server():
    """Back up all internal DNS servers to a YAML file.

    The backup file will be named 'internal-dns-servers.yaml' in the current directory.

    Example:
    -------
    scm backup sase internal-dns-server

    """
    try:
        servers = scm_client.list_internal_dns_servers()

        if not servers:
            typer.echo("No internal DNS servers found")
            return None

        backup_data = []
        for server in servers:
            server_dict = {k: v for k, v in server.items() if v is not None}
            server_dict.pop("id", None)
            backup_data.append(server_dict)

        yaml_data = {"internal_dns_servers": backup_data}
        filename = "internal-dns-servers.yaml"

        with open(filename, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} internal DNS servers to {filename}")
        return filename

    except Exception as e:
        typer.echo(f"Error backing up internal DNS servers: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("internal-dns-server")
def delete_internal_dns_server(
    name: str = DNS_NAME_OPTION,
):
    """Delete an internal DNS server.

    Example:
    -------
    scm delete sase internal-dns-server --name my-dns-server

    """
    try:
        result = scm_client.delete_internal_dns_server(name=name)
        if result:
            typer.echo(f"Deleted internal DNS server: {name}")
        else:
            typer.echo(f"Internal DNS server not found: {name}", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting internal DNS server: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("internal-dns-server")
def load_internal_dns_server(
    file: Path = DNS_FILE_OPTION,
    dry_run: bool = DNS_DRY_RUN_OPTION,
):
    """Load internal DNS servers from a YAML file.

    Example: scm load sase internal-dns-server --file config/internal_dns_servers.yml
    """
    try:
        try:
            config = load_from_yaml(str(file), "internal_dns_servers")
        except ValueError as ve:
            typer.echo(f"Error loading internal DNS servers: {str(ve)}", err=True)
            raise typer.Exit(code=1) from ve

        if dry_run:
            typer.echo("DRY RUN: Would apply the following configurations:")
            for server_data in config["internal_dns_servers"]:
                typer.echo(f"Would create internal DNS server: {server_data['name']}")
            typer.echo(yaml.dump(config["internal_dns_servers"]))
            return None

        results = []
        for server_data in config["internal_dns_servers"]:
            server = InternalDNSServer(**server_data)
            sdk_data = server.to_sdk_model()
            result = scm_client.create_internal_dns_server(**sdk_data)

            results.append(result)
            action = result.get("__action__", "created")
            if action == "created":
                typer.echo(f"Created internal DNS server: {result['name']}")
            elif action == "updated":
                typer.echo(f"Updated internal DNS server: {result['name']}")
            else:
                typer.echo(f"Internal DNS server '{result['name']}' already up to date")

        typer.echo(f"Loaded {len(results)} internal DNS server(s)")
        return results
    except Exception as e:
        typer.echo(f"Error loading internal DNS servers: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("internal-dns-server")
def set_internal_dns_server(
    name: str = DNS_NAME_OPTION,
    domain_name: str = DNS_DOMAIN_OPTION,
    primary: str = DNS_PRIMARY_OPTION,
    secondary: str | None = DNS_SECONDARY_OPTION,
):
    r"""Create or update an internal DNS server.

    Example:
    -------
    scm set sase internal-dns-server \
        --name corp-dns \
        --domain-name corp.example.com \
        --primary 10.0.0.1 \
        --secondary 10.0.0.2

    """
    try:
        # Parse comma-separated domain names
        domain_list = [d.strip() for d in domain_name.split(",")]

        # Validate using Pydantic model
        server = InternalDNSServer(
            name=name,
            domain_name=domain_list,
            primary=primary,
            secondary=secondary,
        )

        # Convert to SDK model format
        sdk_data = server.to_sdk_model()

        # Call the SDK client
        result = scm_client.create_internal_dns_server(**sdk_data)

        # Show appropriate message based on action taken
        action = result.get("__action__", "created")
        if action == "created":
            typer.echo(f"Created internal DNS server: {result['name']}")
        elif action == "updated":
            typer.echo(f"Updated internal DNS server: {result['name']}")
        else:
            typer.echo(f"Internal DNS server '{result['name']}' already up to date")
        return result
    except Exception as e:
        typer.echo(f"Error creating internal DNS server: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("internal-dns-server")
def show_internal_dns_server(
    name: str | None = typer.Option(None, "--name", help="Name of the internal DNS server to show"),
):
    """Display internal DNS servers.

    Example:
    -------
        # List all internal DNS servers
        scm show sase internal-dns-server

        # Show a specific internal DNS server by name
        scm show sase internal-dns-server --name corp-dns

    """
    try:
        if name:
            server = scm_client.get_internal_dns_server(name=name)

            typer.echo(f"Internal DNS Server: {server.get('name', 'N/A')}")
            typer.echo(f"Domain Names: {', '.join(server.get('domain_name', []))}")
            typer.echo(f"Primary: {server.get('primary', 'N/A')}")

            if server.get("secondary"):
                typer.echo(f"Secondary: {server['secondary']}")

            if server.get("id"):
                typer.echo(f"ID: {server['id']}")

            return server

        else:
            servers = scm_client.list_internal_dns_servers()

            if not servers:
                typer.echo("No internal DNS servers found")
                return None

            typer.echo("Internal DNS Servers:")
            typer.echo("-" * 60)

            for server in servers:
                typer.echo(f"Name: {server.get('name', 'N/A')}")
                typer.echo(f"  Domain Names: {', '.join(server.get('domain_name', []))}")
                typer.echo(f"  Primary: {server.get('primary', 'N/A')}")

                if server.get("secondary"):
                    typer.echo(f"  Secondary: {server['secondary']}")

                if server.get("id"):
                    typer.echo(f"  ID: {server['id']}")

                typer.echo("-" * 60)

            return servers

    except Exception as e:
        typer.echo(f"Error showing internal DNS server: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# NETWORK LOCATION COMMANDS
# ========================================================================================================================================================================================


@show_app.command("network-location")
def show_network_location(
    value: str | None = typer.Option(None, "--value", help="System value of the network location (e.g., us-west-1)"),
):
    """Display network locations (read-only).

    Example:
    -------
        # List all network locations
        scm show sase network-location

        # Show a specific network location by value
        scm show sase network-location --value us-west-1

    """
    try:
        if value:
            location = scm_client.get_network_location(value=value)

            typer.echo(f"Network Location: {location.get('display', 'N/A')}")
            typer.echo(f"Value: {location.get('value', 'N/A')}")
            typer.echo(f"Continent: {location.get('continent', 'N/A')}")
            typer.echo(f"Region: {location.get('region', 'N/A')}")
            typer.echo(f"Aggregate Region: {location.get('aggregate_region', 'N/A')}")

            if location.get("latitude") is not None:
                typer.echo(f"Latitude: {location['latitude']}")
            if location.get("longitude") is not None:
                typer.echo(f"Longitude: {location['longitude']}")

            return location

        else:
            locations = scm_client.list_network_locations()

            if not locations:
                typer.echo("No network locations found")
                return None

            typer.echo("Network Locations:")
            typer.echo("-" * 60)

            for location in locations:
                typer.echo(f"Value: {location.get('value', 'N/A')}")
                typer.echo(f"  Display: {location.get('display', 'N/A')}")
                typer.echo(f"  Continent: {location.get('continent', 'N/A')}")
                typer.echo(f"  Region: {location.get('region', 'N/A')}")
                typer.echo("-" * 60)

            return locations

    except Exception as e:
        typer.echo(f"Error showing network location: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
