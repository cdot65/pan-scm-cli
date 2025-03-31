"""Objects module commands for scm-cli.

This module implements set, delete, and load commands for objects-related
configurations such as address-group, address, service-group, etc.
"""

from pathlib import Path

import typer
import yaml

from ..utils.config import load_from_yaml
from ..utils.sdk_client import scm_client
from ..utils.validators import Address, AddressGroup

# Create app groups for each action type
set_app = typer.Typer(help="Create or update objects configurations")
delete_app = typer.Typer(help="Remove objects configurations")
load_app = typer.Typer(help="Load objects configurations from YAML files")

# Define typer option constants
FOLDER_OPTION = typer.Option(..., "--folder", help="Folder path for the address group")
NAME_OPTION = typer.Option(..., "--name", help="Name of the address group")
TYPE_OPTION = typer.Option(..., "--type", help="Type of address group (static or dynamic)")
MEMBERS_OPTION = typer.Option(None, "--members", help="List of addresses in the group")
DESCRIPTION_OPTION = typer.Option(None, "--description", help="Description of the address group")
TAGS_OPTION = typer.Option(None, "--tags", help="List of tags")
FILE_OPTION = typer.Option(..., "--file", help="YAML file to load configurations from")
DRY_RUN_OPTION = typer.Option(False, "--dry-run", help="Simulate execution without applying changes")

# Address-specific options
IP_NETMASK_OPTION = typer.Option(None, "--ip-netmask", help="IP address with CIDR notation (e.g. 192.168.1.0/24)")
IP_RANGE_OPTION = typer.Option(None, "--ip-range", help="IP address range (e.g. 192.168.1.1-192.168.1.10)")
IP_WILDCARD_OPTION = typer.Option(None, "--ip-wildcard", help="IP wildcard mask (e.g. 10.20.1.0/0.0.248.255)")
FQDN_OPTION = typer.Option(None, "--fqdn", help="Fully qualified domain name (e.g. example.com)")


@set_app.command("address-group")
def set_address_group(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    type: str = TYPE_OPTION,
    members: list[str] | None = MEMBERS_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    tags: list[str] | None = TAGS_OPTION,
):
    """Create or update an address group.

    Example:
    -------
        scm-cli set objects address-group \
        --folder Texas \
        --name test123 \
        --type static \
        --members ["abc", "xyz"] \
        --description "test" \
        --tags ["abc", "automation"]

    """
    try:
        # Validate inputs using the Pydantic model
        address_group = AddressGroup(
            folder=folder,
            name=name,
            type=type,
            members=members or [],
            description=description or "",
            tags=tags or [],
        )

        # Call the SDK client to create the address group
        result = scm_client.create_address_group(
            folder=address_group.folder,
            name=address_group.name,
            type=address_group.type,
            members=address_group.members,
            description=address_group.description,
            tags=address_group.tags,
        )

        typer.echo(f"Created address group: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating address group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("address-group")
def delete_address_group(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete an address group.

    Example: scm-cli delete objects address-group --folder Texas --name test123
    """
    try:
        result = scm_client.delete_address_group(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted address group: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting address group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("address-group")
def load_address_group(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load address groups from a YAML file.

    Example: scm-cli load objects address-group --file config/address_groups.yml
    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(file, "address_groups")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["address_groups"]))
            return

        # Apply each address group
        results = []
        for ag_data in config["address_groups"]:
            # Validate using the Pydantic model
            address_group = AddressGroup(**ag_data)

            # Call the SDK client to create the address group
            result = scm_client.create_address_group(
                folder=address_group.folder,
                name=address_group.name,
                type=address_group.type,
                members=address_group.members,
                description=address_group.description,
                tags=address_group.tags,
            )

            results.append(result)
            typer.echo(f"Applied address group: {result['name']} in folder {result['folder']}")

        return results
    except Exception as e:
        typer.echo(f"Error loading address groups: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("address")
def set_address(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    tags: list[str] | None = TAGS_OPTION,
    ip_netmask: str | None = IP_NETMASK_OPTION,
    ip_range: str | None = IP_RANGE_OPTION,
    ip_wildcard: str | None = IP_WILDCARD_OPTION,
    fqdn: str | None = FQDN_OPTION,
):
    """Create or update an address object.

    Example:
    -------
        scm-cli set objects address \
        --folder Texas \
        --name webserver \
        --ip-netmask 192.168.1.100/32 \
        --description "Web server" \
        --tags ["server", "web"]

    Note: Exactly one of ip-netmask, ip-range, ip-wildcard, or fqdn must be provided.

    """
    try:
        # Validate inputs using the Pydantic model
        address = Address(
            folder=folder,
            name=name,
            description=description or "",
            tags=tags or [],
            ip_netmask=ip_netmask,
            ip_range=ip_range,
            ip_wildcard=ip_wildcard,
            fqdn=fqdn,
        )

        # Call the SDK client to create the address
        result = scm_client.create_address(
            folder=address.folder,
            name=address.name,
            description=address.description,
            tags=address.tags,
            ip_netmask=address.ip_netmask,
            ip_range=address.ip_range,
            ip_wildcard=address.ip_wildcard,
            fqdn=address.fqdn,
        )

        typer.echo(f"Created address: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating address: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("address")
def delete_address(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete an address object.

    Example:
    -------
    scm-cli delete objects address --folder Texas --name webserver

    """
    try:
        result = scm_client.delete_address(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted address: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting address: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("address")
def load_address(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load address objects from a YAML file.

    Example:
    -------
    scm-cli load objects address --file config/addresses.yml

    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(file, "addresses")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["addresses"]))
            return

        # Apply each address
        results = []
        for addr_data in config["addresses"]:
            # Validate using the Pydantic model
            address = Address(**addr_data)

            # Call the SDK client to create the address
            result = scm_client.create_address(
                folder=address.folder,
                name=address.name,
                description=address.description,
                tags=address.tags,
                ip_netmask=address.ip_netmask,
                ip_range=address.ip_range,
                ip_wildcard=address.ip_wildcard,
                fqdn=address.fqdn,
            )

            results.append(result)
            typer.echo(f"Applied address: {result['name']} in folder {result['folder']}")

        return results
    except Exception as e:
        typer.echo(f"Error loading addresses: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
