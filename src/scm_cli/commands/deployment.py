"""Deployment module commands for scm.

This module implements set, delete, and load commands for deployment-related
configurations such as bandwidth allocations.
"""

from pathlib import Path
from typing import Any

import typer
import yaml

from ..utils.config import load_from_yaml
from ..utils.decorators import handle_command_errors
from ..utils.output import OUTPUT_OPTION, OutputFormat, emit, error, info, success
from ..utils.sdk_client import scm_client
from ..utils.validators import BandwidthAllocation, BGPRouting, InternalDNSServer, RemoteNetwork, ServiceConnection

# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

# Create app groups for each action type
set_app = typer.Typer(help="Create or update SASE configurations")
delete_app = typer.Typer(help="Remove SASE configurations")
load_app = typer.Typer(help="Load SASE configurations from YAML files")
show_app = typer.Typer(help="Display SASE configurations")
backup_app = typer.Typer(help="Backup SASE configurations to YAML files")

# =============================================================================================================================================================================================
# COMMAND OPTIONS
# =============================================================================================================================================================================================

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

# =============================================================================================================================================================================================
# BANDWIDTH ALLOCATION COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("bandwidth-allocation")
@handle_command_errors("backing up bandwidth allocations")
def backup_bandwidth_allocation():
    """Back up all bandwidth allocations to a YAML file.

    The backup file will be named 'bandwidth-allocations.yaml' in the current directory.

    Example:
    -------
    scm backup sase bandwidth

    Note: Bandwidth allocations are global and do not have a folder parameter.

    """
    # List all bandwidth allocations
    allocations = scm_client.list_bandwidth_allocations()

    if not allocations:
        info("No bandwidth allocations found")
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

    success(f"Successfully backed up {len(backup_data)} bandwidth allocations to {filename}")
    return filename


@delete_app.command("bandwidth-allocation")
@handle_command_errors("deleting bandwidth allocation")
def delete_bandwidth_allocation(
    name: str = NAME_OPTION,
    spn_name_list: str = typer.Option(..., "--spn-name-list", help="SPN names (comma-separated if multiple)"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a bandwidth allocation.

    Example:
    -------
    scm delete sase bandwidth-allocation \
        --name primary \
        --spn-name-list ["spn1", "spn2"]

    Note: Bandwidth allocations are global resources and do not require a folder parameter.

    """
    # Defensive check: Only accept comma-separated string, not list
    if isinstance(spn_name_list, list):
        error("Error: --spn-name-list must be a comma-separated string (e.g., --spn-name-list foo,bar)")
        raise typer.Exit(code=1)

    if not force:
        typer.confirm(f"Delete bandwidth allocation '{name}'?", abort=True)

    # Convert comma-separated string to list
    spn_list = ([spn.strip() for spn in spn_name_list.split(",")] if "," in spn_name_list else [spn_name_list.strip()]) if isinstance(spn_name_list, str) else spn_name_list

    result = scm_client.delete_bandwidth_allocation(name=name, spn_name_list=spn_list)
    if result:
        success(f"Deleted bandwidth allocation: {name}")
    else:
        error(f"Bandwidth allocation not found: {name}")
        raise typer.Exit(code=1)


@load_app.command("bandwidth-allocation")
@handle_command_errors("loading bandwidth allocations")
def load_bandwidth_allocation(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load bandwidth allocations from a YAML file.

    Example: scm load sase bandwidth-allocation --file config/bandwidth_allocations.yml
    """
    # Load and parse the YAML file
    config = load_from_yaml(str(file), "bandwidth_allocations")

    if dry_run:
        info("DRY RUN: Would apply the following configurations:")
        for allocation_data in config["bandwidth_allocations"]:
            # Output details about each allocation that would be created
            spn_names = allocation_data.get("spn_name_list", [])
            info(f"Would create bandwidth allocation: {allocation_data['name']} ({allocation_data['bandwidth']} Mbps) with SPNs: {spn_names}")
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
        success(f"Applied bandwidth allocation: {result['name']} ({bandwidth_value} Mbps)")

    # Add a summary message that matches test expectations
    success(f"Loaded {len(results)} bandwidth allocation(s)")
    return results


@set_app.command("bandwidth-allocation")
@handle_command_errors("creating bandwidth allocation")
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
    action = result.get("__action__", "created")
    bw = result.get("allocated_bandwidth", result.get("bandwidth", "N/A"))
    if action == "created":
        success(f"Created bandwidth allocation: {result['name']} ({bw} Mbps)")
    elif action == "updated":
        success(f"Updated bandwidth allocation: {result['name']} ({bw} Mbps)")
    elif action == "no_change":
        info(f"No changes needed for bandwidth allocation: {result['name']} ({bw} Mbps)")
    return result


@show_app.command("bandwidth-allocation")
@handle_command_errors("showing bandwidth allocation")
def show_bandwidth_allocation(
    name: str | None = typer.Option(None, "--name", help="Name of the bandwidth allocation to show"),
    output: OutputFormat = OUTPUT_OPTION,
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
    if name:
        # Get a specific bandwidth allocation by name
        allocation = scm_client.get_bandwidth_allocation(name=name)
        emit(allocation, output, title=f"Bandwidth Allocation: {name}")
        return allocation

    # List all bandwidth allocations (default behavior)
    allocations = scm_client.list_bandwidth_allocations()

    if not allocations:
        emit([], output)
        return None

    emit(
        allocations,
        output,
        columns=["name", "allocated_bandwidth", "spn_name_list", "description", "id"],
        title="Bandwidth Allocations",
    )
    return allocations


# =============================================================================================================================================================================================
# SERVICE CONNECTION COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("service-connection")
@handle_command_errors("backing up service connections")
def backup_service_connection():
    """Back up all service connections to a YAML file.

    The backup file will be named 'service-connections.yaml' in the current directory.

    Example:
    -------
    scm backup sase service-connection

    """
    # List all service connections
    connections = scm_client.list_service_connections()

    if not connections:
        info("No service connections found")
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

    success(f"Successfully backed up {len(backup_data)} service connections to {filename}")
    return filename


@delete_app.command("service-connection")
@handle_command_errors("deleting service connection")
def delete_service_connection(
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a service connection.

    Example:
    -------
    scm delete sase service-connection --name primary-connection

    """
    if not force:
        typer.confirm(f"Delete service connection '{name}'?", abort=True)
    result = scm_client.delete_service_connection(name=name)
    if result:
        success(f"Deleted service connection: {name}")
    else:
        error(f"Service connection not found: {name}")
        raise typer.Exit(code=1)


@load_app.command("service-connection")
@handle_command_errors("loading service connections")
def load_service_connection(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load service connections from a YAML file.

    Example: scm load sase service-connection --file config/service_connections.yml
    """
    # Load and parse the YAML file
    config = load_from_yaml(str(file), "service_connections")

    if dry_run:
        info("DRY RUN: Would apply the following configurations:")
        for connection_data in config["service_connections"]:
            info(f"Would create service connection: {connection_data['name']}")
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
            success(f"Created service connection: {result['name']}")
        elif action == "updated":
            success(f"Updated service connection: {result['name']}")
        else:  # no_change
            info(f"Service connection '{result['name']}' already up to date")

    success(f"Loaded {len(results)} service connection(s)")
    return results


@set_app.command("service-connection")
@handle_command_errors("creating service connection")
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
        success(f"Created service connection: {result['name']}")
    elif action == "updated":
        success(f"Updated service connection: {result['name']}")
    else:  # no_change
        info(f"Service connection '{result['name']}' already up to date")
    return result


@show_app.command("service-connection")
@handle_command_errors("showing service connection")
def show_service_connection(
    name: str | None = typer.Option(None, "--name", help="Name of the service connection to show"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display service connections.

    Example:
    -------
        # List all service connections
        scm show sase service-connection

        # Show a specific service connection by name
        scm show sase service-connection --name primary-connection

    """
    if name:
        # Get a specific service connection by name
        connection = scm_client.get_service_connection(name=name)
        emit(connection, output, title=f"Service Connection: {name}")
        return connection

    # List all service connections in the folder
    connections = scm_client.list_service_connections()

    if not connections:
        emit([], output)
        return None

    emit(
        connections,
        output,
        columns=["name", "ipsec_tunnel", "region", "onboarding_type", "subnets", "id"],
        title="Service Connections",
    )
    return connections


# =============================================================================================================================================================================================
# REMOTE NETWORK COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("remote-network")
@handle_command_errors("backing up remote networks")
def backup_remote_network():
    """Back up all remote networks to a YAML file.

    The backup file will be named 'remote-networks.yaml' in the current directory.

    Example:
    -------
    scm backup sase remote-network

    """
    # List all remote networks
    networks = scm_client.list_remote_networks()

    if not networks:
        info("No remote networks found")
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

    success(f"Successfully backed up {len(backup_data)} remote networks to {filename}")
    return filename


@delete_app.command("remote-network")
@handle_command_errors("deleting remote network")
def delete_remote_network(
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a remote network.

    Example:
    -------
    scm delete sase remote-network --name branch-network

    """
    if not force:
        typer.confirm(f"Delete remote network '{name}'?", abort=True)
    result = scm_client.delete_remote_network(
        name=name,
    )
    if result:
        success(f"Deleted remote network: {name}")
    else:
        error(f"Remote network not found: {name}")
        raise typer.Exit(code=1)


@load_app.command("remote-network")
@handle_command_errors("loading remote networks")
def load_remote_network(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load remote networks from a YAML file.

    Example: scm load sase remote-network --file config/remote_networks.yml
    """
    # Load and parse the YAML file
    config = load_from_yaml(str(file), "remote_networks")

    if dry_run:
        info("DRY RUN: Would apply the following configurations:")
        for network_data in config["remote_networks"]:
            info(f"Would create remote network: {network_data['name']}")
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
            success(f"Created remote network: {result['name']}")
        elif action == "updated":
            success(f"Updated remote network: {result['name']}")
        else:  # no_change
            info(f"Remote network '{result['name']}' already up to date")

    success(f"Loaded {len(results)} remote network(s)")
    return results


@set_app.command("remote-network")
@handle_command_errors("creating remote network")
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
        success(f"Created remote network: {result['name']}")
    elif action == "updated":
        success(f"Updated remote network: {result['name']}")
    else:  # no_change
        info(f"Remote network '{result['name']}' already up to date")
    return result


@show_app.command("remote-network")
@handle_command_errors("showing remote network")
def show_remote_network(
    name: str | None = typer.Option(None, "--name", help="Name of the remote network to show"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display remote networks.

    Example:
    -------
        # List all remote networks
        scm show sase remote-network

        # Show a specific remote network by name
        scm show sase remote-network --name branch-network

    """
    if name:
        # Get a specific remote network by name
        network = scm_client.get_remote_network(
            name=name,
        )
        emit(network, output, title=f"Remote Network: {name}")
        return network

    # List all remote networks
    networks = scm_client.list_remote_networks()

    if not networks:
        emit([], output)
        return None

    emit(
        networks,
        output,
        columns=["name", "region", "license_type", "subnets", "ecmp_load_balancing", "id"],
        title="Remote Networks",
    )
    return networks


# =============================================================================================================================================================================================
# BGP ROUTING COMMANDS
# =============================================================================================================================================================================================

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
@handle_command_errors("resetting BGP routing")
def delete_bgp_routing(
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Reset BGP routing configuration to defaults.

    Example:
    -------
    scm delete sase bgp-routing

    Note: BGP routing is a singleton; delete resets to defaults.

    """
    if not force:
        typer.confirm("Reset BGP routing configuration to defaults?", abort=True)
    result = scm_client.delete_bgp_routing()
    if result:
        success("Reset BGP routing configuration to defaults")
    else:
        error("Error resetting BGP routing configuration")
        raise typer.Exit(code=1)


@set_app.command("bgp-routing")
@handle_command_errors("creating BGP routing")
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
        success(f"Created BGP routing configuration (backbone: {result.get('backbone_routing', 'N/A')})")
    elif action == "updated":
        success(f"Updated BGP routing configuration (backbone: {result.get('backbone_routing', 'N/A')})")
    else:
        info("BGP routing configuration already up to date")
    return result


@show_app.command("bgp-routing")
@handle_command_errors("showing BGP routing")
def show_bgp_routing(
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display BGP routing configuration.

    Example:
    -------
    scm show sase bgp-routing

    Note: BGP routing is a singleton; always shows the current configuration.

    """
    config = scm_client.get_bgp_routing()
    emit(config, output, title="BGP Routing Configuration")
    return config


# =============================================================================================================================================================================================
# INTERNAL DNS SERVER COMMANDS
# =============================================================================================================================================================================================

# Internal DNS Server option constants
DNS_NAME_OPTION = typer.Option(..., "--name", help="Name of the internal DNS server")
DNS_DOMAIN_OPTION = typer.Option(..., "--domain-name", help="DNS domain name(s) (comma-separated if multiple)")
DNS_PRIMARY_OPTION = typer.Option(..., "--primary", help="Primary DNS server IP address")
DNS_SECONDARY_OPTION = typer.Option(None, "--secondary", help="Secondary DNS server IP address")
DNS_FILE_OPTION = typer.Option(..., "--file", help="YAML file to load configurations from")
DNS_DRY_RUN_OPTION = typer.Option(False, "--dry-run", help="Simulate execution without applying changes")


@backup_app.command("internal-dns-server")
@handle_command_errors("backing up internal DNS servers")
def backup_internal_dns_server():
    """Back up all internal DNS servers to a YAML file.

    The backup file will be named 'internal-dns-servers.yaml' in the current directory.

    Example:
    -------
    scm backup sase internal-dns-server

    """
    servers = scm_client.list_internal_dns_servers()

    if not servers:
        info("No internal DNS servers found")
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

    success(f"Successfully backed up {len(backup_data)} internal DNS servers to {filename}")
    return filename


@delete_app.command("internal-dns-server")
@handle_command_errors("deleting internal DNS server")
def delete_internal_dns_server(
    name: str = DNS_NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete an internal DNS server.

    Example:
    -------
    scm delete sase internal-dns-server --name my-dns-server

    """
    if not force:
        typer.confirm(f"Delete internal DNS server '{name}'?", abort=True)
    result = scm_client.delete_internal_dns_server(name=name)
    if result:
        success(f"Deleted internal DNS server: {name}")
    else:
        error(f"Internal DNS server not found: {name}")
        raise typer.Exit(code=1)


@load_app.command("internal-dns-server")
@handle_command_errors("loading internal DNS servers")
def load_internal_dns_server(
    file: Path = DNS_FILE_OPTION,
    dry_run: bool = DNS_DRY_RUN_OPTION,
):
    """Load internal DNS servers from a YAML file.

    Example: scm load sase internal-dns-server --file config/internal_dns_servers.yml
    """
    config = load_from_yaml(str(file), "internal_dns_servers")

    if dry_run:
        info("DRY RUN: Would apply the following configurations:")
        for server_data in config["internal_dns_servers"]:
            info(f"Would create internal DNS server: {server_data['name']}")
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
            success(f"Created internal DNS server: {result['name']}")
        elif action == "updated":
            success(f"Updated internal DNS server: {result['name']}")
        else:
            info(f"Internal DNS server '{result['name']}' already up to date")

    success(f"Loaded {len(results)} internal DNS server(s)")
    return results


@set_app.command("internal-dns-server")
@handle_command_errors("creating internal DNS server")
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
        success(f"Created internal DNS server: {result['name']}")
    elif action == "updated":
        success(f"Updated internal DNS server: {result['name']}")
    else:
        info(f"Internal DNS server '{result['name']}' already up to date")
    return result


@show_app.command("internal-dns-server")
@handle_command_errors("showing internal DNS server")
def show_internal_dns_server(
    name: str | None = typer.Option(None, "--name", help="Name of the internal DNS server to show"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display internal DNS servers.

    Example:
    -------
        # List all internal DNS servers
        scm show sase internal-dns-server

        # Show a specific internal DNS server by name
        scm show sase internal-dns-server --name corp-dns

    """
    if name:
        server = scm_client.get_internal_dns_server(name=name)
        emit(server, output, title=f"Internal DNS Server: {name}")
        return server

    servers = scm_client.list_internal_dns_servers()

    if not servers:
        emit([], output)
        return None

    emit(
        servers,
        output,
        columns=["name", "domain_name", "primary", "secondary", "id"],
        title="Internal DNS Servers",
    )
    return servers


# =============================================================================================================================================================================================
# NETWORK LOCATION COMMANDS
# =============================================================================================================================================================================================


@show_app.command("network-location")
@handle_command_errors("showing network location")
def show_network_location(
    value: str | None = typer.Option(None, "--value", help="System value of the network location (e.g., us-west-1)"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display network locations (read-only).

    Example:
    -------
        # List all network locations
        scm show sase network-location

        # Show a specific network location by value
        scm show sase network-location --value us-west-1

    """
    if value:
        location = scm_client.get_network_location(value=value)
        emit(location, output, title=f"Network Location: {value}")
        return location

    locations = scm_client.list_network_locations()

    if not locations:
        emit([], output)
        return None

    emit(
        locations,
        output,
        columns=["value", "display", "continent", "region"],
        title="Network Locations",
    )
    return locations
