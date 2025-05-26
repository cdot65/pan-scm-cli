"""Objects module commands for scm-cli.

This module implements set, delete, and load commands for objects-related
configurations such as address-group, address, service-group, etc.
"""

from pathlib import Path
from typing import Any

import typer
import yaml

from ..utils.config import load_from_yaml
from ..utils.sdk_client import scm_client
from ..utils.validators import Address, AddressGroup, Application, ApplicationFilter, ApplicationGroup, DynamicUserGroup, ExternalDynamicList, HIPObject, HIPProfile, HTTPServerProfile

# ========================================================================================================================================================================================
# TYPER APP CONFIGURATION
# ========================================================================================================================================================================================

# Create app groups for each action type
set_app = typer.Typer(help="Create or update objects configurations")
delete_app = typer.Typer(help="Remove objects configurations")
load_app = typer.Typer(help="Load objects configurations from YAML files")
show_app = typer.Typer(help="Display objects configurations")
backup_app = typer.Typer(help="Backup objects configurations to YAML files")

# ========================================================================================================================================================================================
# COMMAND OPTIONS
# ========================================================================================================================================================================================

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

# Application-specific options
CATEGORY_OPTION = typer.Option(..., "--category", help="High-level category (max 50 chars)")
SUBCATEGORY_OPTION = typer.Option(..., "--subcategory", help="Specific sub-category (max 50 chars)")
TECHNOLOGY_OPTION = typer.Option(..., "--technology", help="Underlying technology (max 50 chars)")
RISK_OPTION = typer.Option(..., "--risk", min=1, max=5, help="Risk level (1-5)")
PORTS_OPTION = typer.Option(None, "--ports", help="List of TCP/UDP ports (e.g. tcp/80, udp/53)")
EVASIVE_OPTION = typer.Option(False, "--evasive", help="Uses evasive techniques")
PERVASIVE_OPTION = typer.Option(False, "--pervasive", help="Widely used")
EXCESSIVE_BANDWIDTH_OPTION = typer.Option(False, "--excessive-bandwidth-use", help="Uses excessive bandwidth")
USED_BY_MALWARE_OPTION = typer.Option(False, "--used-by-malware", help="Used by malware")
TRANSFERS_FILES_OPTION = typer.Option(False, "--transfers-files", help="Transfers files")
HAS_KNOWN_VULNERABILITIES_OPTION = typer.Option(False, "--has-known-vulnerabilities", help="Has known vulnerabilities")
TUNNELS_OTHER_APPS_OPTION = typer.Option(False, "--tunnels-other-apps", help="Tunnels other applications")
PRONE_TO_MISUSE_OPTION = typer.Option(False, "--prone-to-misuse", help="Prone to misuse")
NO_CERTIFICATIONS_OPTION = typer.Option(False, "--no-certifications", help="Lacks certifications")

# Application group-specific options
APP_GROUP_MEMBERS_OPTION = typer.Option(..., "--members", help="List of application names in the group")

# Application filter-specific options
FILTER_CATEGORY_OPTION = typer.Option(..., "--category", help="List of category strings to filter by")
FILTER_SUBCATEGORY_OPTION = typer.Option(..., "--subcategory", help="List of subcategory strings to filter by")
FILTER_TECHNOLOGY_OPTION = typer.Option(..., "--technology", help="List of technology strings to filter by")
FILTER_RISK_OPTION = typer.Option(..., "--risk", help="List of risk levels (1-5) to filter by")

# Dynamic user group-specific options
FILTER_EXPRESSION_OPTION = typer.Option(..., "--filter", help="Tag-based filter expression (e.g., \"tag.Department='IT' and tag.Role='Admin'\")")

# ========================================================================================================================================================================================
# ADDRESS GROUP COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("address-group")
def backup_address_group(
    folder: str = FOLDER_OPTION,
):
    """Backup all address groups from a folder to a YAML file.

    The backup file will be named 'address-group-{folder}.yaml' in the current directory.

    Example:
    -------
    scm-cli backup objects address-group --folder Austin

    """
    try:
        # List all address groups in the folder with exact_match=True
        groups = scm_client.list_address_groups(folder=folder, exact_match=True)

        if not groups:
            typer.echo(f"No address groups found in folder '{folder}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for group in groups:
            # The list method returns dict objects already, but let's ensure we exclude any None values
            group_dict = {k: v for k, v in group.items() if v is not None}
            # Remove system fields that shouldn't be in backup
            group_dict.pop("id", None)

            # Convert SDK format back to CLI format for consistency
            if "static" in group_dict:
                group_dict["type"] = "static"
                group_dict["members"] = group_dict.pop("static", [])
            elif "dynamic" in group_dict:
                group_dict["type"] = "dynamic"
                dynamic_info = group_dict.pop("dynamic", {})
                if dynamic_info.get("filter"):
                    group_dict["filter"] = dynamic_info["filter"]

            backup_data.append(group_dict)

        # Create the YAML structure
        yaml_data = {"address_groups": backup_data}

        # Generate filename
        filename = f"address-group-{folder.lower()}.yaml"

        # Write to YAML file
        with open(filename, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} address groups to {filename}")
        return filename

    except Exception as e:
        typer.echo(f"Error backing up address groups: {str(e)}", err=True)
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
        config = load_from_yaml(str(file), "address_groups")

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


@show_app.command("address-group")
def show_address_group(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the address group to show"),
    list_groups: bool = typer.Option(False, "--list", help="List all address groups in the folder"),
):
    """Display address group objects.

    Examples
    --------
        # List all address groups in a folder
        scm-cli show objects address-group --folder Texas --list

        # Show a specific address group by name
        scm-cli show objects address-group --folder Texas --name web-servers

    """
    try:
        if list_groups:
            # List all address groups in the folder
            groups = scm_client.list_address_groups(folder=folder)

            if not groups:
                typer.echo(f"No address groups found in folder '{folder}'")
                return

            typer.echo(f"Address Groups in folder '{folder}':")
            typer.echo("-" * 60)

            for group in groups:
                # Display address group information
                typer.echo(f"Name: {group.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if group.get("folder"):
                    typer.echo(f"  Location: Folder '{group['folder']}'")
                elif group.get("snippet"):
                    typer.echo(f"  Location: Snippet '{group['snippet']}'")
                elif group.get("device"):
                    typer.echo(f"  Location: Device '{group['device']}'")
                else:
                    typer.echo("  Location: N/A")

                # Determine type based on presence of 'static' or 'dynamic' key
                if group.get("static") is not None:
                    typer.echo("  Type: static")
                    typer.echo(f"  Members: {', '.join(group.get('static', []))}")
                elif group.get("dynamic") is not None:
                    typer.echo("  Type: dynamic")
                    dynamic_info = group.get("dynamic", {})
                    if dynamic_info.get("filter"):
                        typer.echo(f"  Filter: {dynamic_info['filter']}")

                typer.echo(f"  Description: {group.get('description', 'N/A')}")

                # Display tags if present
                if group.get("tag"):
                    typer.echo(f"  Tags: {', '.join(group['tag'])}")

                typer.echo("-" * 60)

            return groups

        elif name:
            # Get a specific address group by name
            group = scm_client.get_address_group(folder=folder, name=name)

            typer.echo(f"Address Group: {group.get('name', 'N/A')}")

            # Display container location (folder, snippet, or device)
            if group.get("folder"):
                typer.echo(f"Location: Folder '{group['folder']}'")
            elif group.get("snippet"):
                typer.echo(f"Location: Snippet '{group['snippet']}'")
            elif group.get("device"):
                typer.echo(f"Location: Device '{group['device']}'")
            else:
                typer.echo("Location: N/A")

            # Determine type based on presence of 'static' or 'dynamic' key
            if group.get("static") is not None:
                typer.echo("Type: static")
                typer.echo(f"Description: {group.get('description', 'N/A')}")
                members = group.get("static", [])
                if members:
                    typer.echo(f"Members ({len(members)}):")
                    for member in members:
                        typer.echo(f"  - {member}")
                else:
                    typer.echo("Members: None")
            elif group.get("dynamic") is not None:
                typer.echo("Type: dynamic")
                typer.echo(f"Description: {group.get('description', 'N/A')}")
                dynamic_info = group.get("dynamic", {})
                if dynamic_info.get("filter"):
                    typer.echo(f"Filter: {dynamic_info['filter']}")
                else:
                    typer.echo("Filter: None")
            else:
                typer.echo("Type: unknown")
                typer.echo(f"Description: {group.get('description', 'N/A')}")

            # Display tags if present
            if group.get("tag"):
                typer.echo(f"Tags: {', '.join(group['tag'])}")

            # Display ID if present
            if group.get("id"):
                typer.echo(f"ID: {group['id']}")

            return group

        else:
            # Neither --list nor --name was provided
            typer.echo("Error: Either --list or --name must be specified", err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"Error showing address group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# ADDRESS OBJECT COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("address")
def backup_address(
    folder: str = FOLDER_OPTION,
):
    """Backup all address objects from a folder to a YAML file.

    The backup file will be named 'address-{folder}.yaml' in the current directory.

    Example:
    -------
    scm-cli backup objects address --folder Austin

    """
    try:
        # List all addresses in the folder with exact_match=True
        addresses = scm_client.list_addresses(folder=folder, exact_match=True)

        if not addresses:
            typer.echo(f"No addresses found in folder '{folder}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for addr in addresses:
            # The list method returns dict objects already, but let's ensure we exclude any None values
            addr_dict = {k: v for k, v in addr.items() if v is not None}
            # Remove system fields that shouldn't be in backup
            addr_dict.pop("id", None)
            backup_data.append(addr_dict)

        # Create the YAML structure
        yaml_data = {"addresses": backup_data}

        # Generate filename
        filename = f"address-{folder.lower()}.yaml"

        # Write to YAML file
        with open(filename, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} addresses to {filename}")
        return filename

    except Exception as e:
        typer.echo(f"Error backing up addresses: {str(e)}", err=True)
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
        config = load_from_yaml(str(file), "addresses")

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


@show_app.command("address")
def show_address(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the address to show"),
    list_addresses: bool = typer.Option(False, "--list", help="List all addresses in the folder"),
):
    """Display address objects.

    Example:
    -------
        # List all addresses in a folder
        scm-cli show objects address --folder Texas --list

        # Show a specific address by name
        scm-cli show objects address --folder Texas --name webserver

    """
    try:
        if list_addresses:
            # List all addresses in the folder
            addresses = scm_client.list_addresses(folder=folder)

            if not addresses:
                typer.echo(f"No addresses found in folder '{folder}'")
                return

            typer.echo(f"Addresses in folder '{folder}':")
            typer.echo("-" * 60)

            for addr in addresses:
                # Display address information
                typer.echo(f"Name: {addr.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if addr.get("folder"):
                    typer.echo(f"  Location: Folder '{addr['folder']}'")
                elif addr.get("snippet"):
                    typer.echo(f"  Location: Snippet '{addr['snippet']}'")
                elif addr.get("device"):
                    typer.echo(f"  Location: Device '{addr['device']}'")
                else:
                    typer.echo("  Location: N/A")

                typer.echo(f"  Description: {addr.get('description', 'N/A')}")

                # Display the address type and value
                if addr.get("ip_netmask"):
                    typer.echo("  Type: IP/Netmask")
                    typer.echo(f"  Value: {addr['ip_netmask']}")
                elif addr.get("ip_range"):
                    typer.echo("  Type: IP Range")
                    typer.echo(f"  Value: {addr['ip_range']}")
                elif addr.get("ip_wildcard"):
                    typer.echo("  Type: IP Wildcard")
                    typer.echo(f"  Value: {addr['ip_wildcard']}")
                elif addr.get("fqdn"):
                    typer.echo("  Type: FQDN")
                    typer.echo(f"  Value: {addr['fqdn']}")

                # Display tags if present
                if addr.get("tag"):
                    typer.echo(f"  Tags: {', '.join(addr['tag'])}")

                typer.echo("-" * 60)

            return addresses

        elif name:
            # Get a specific address by name
            address = scm_client.get_address(folder=folder, name=name)

            typer.echo(f"Address: {address.get('name', 'N/A')}")

            # Display container location (folder, snippet, or device)
            if address.get("folder"):
                typer.echo(f"Location: Folder '{address['folder']}'")
            elif address.get("snippet"):
                typer.echo(f"Location: Snippet '{address['snippet']}'")
            elif address.get("device"):
                typer.echo(f"Location: Device '{address['device']}'")
            else:
                typer.echo("Location: N/A")

            typer.echo(f"Description: {address.get('description', 'N/A')}")

            # Display the address type and value
            if address.get("ip_netmask"):
                typer.echo("Type: IP/Netmask")
                typer.echo(f"Value: {address['ip_netmask']}")
            elif address.get("ip_range"):
                typer.echo("Type: IP Range")
                typer.echo(f"Value: {address['ip_range']}")
            elif address.get("ip_wildcard"):
                typer.echo("Type: IP Wildcard")
                typer.echo(f"Value: {address['ip_wildcard']}")
            elif address.get("fqdn"):
                typer.echo("Type: FQDN")
                typer.echo(f"Value: {address['fqdn']}")

            # Display tags if present
            if address.get("tag"):
                typer.echo(f"Tags: {', '.join(address['tag'])}")

            # Display ID if present
            if address.get("id"):
                typer.echo(f"ID: {address['id']}")

            return address

        else:
            # Neither --list nor --name was provided
            typer.echo("Error: Either --list or --name must be specified", err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"Error showing address: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# APPLICATION COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("application")
def backup_application(
    folder: str = FOLDER_OPTION,
):
    """Backup all applications from a folder to a YAML file.

    The backup file will be named 'application-{folder}.yaml' in the current directory.

    Example:
    -------
    scm-cli backup objects application --folder Austin

    """
    try:
        # List all applications in the folder with exact_match=True
        applications = scm_client.list_applications(folder=folder, exact_match=True)

        if not applications:
            typer.echo(f"No applications found in folder '{folder}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for app in applications:
            # The list method returns dict objects already, but let's ensure we exclude any None values
            app_dict = {k: v for k, v in app.items() if v is not None}
            # Remove system fields that shouldn't be in backup
            app_dict.pop("id", None)
            backup_data.append(app_dict)

        # Create the YAML structure
        yaml_data = {"applications": backup_data}

        # Generate filename
        filename = f"application-{folder.lower()}.yaml"

        # Write to YAML file
        with open(filename, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} applications to {filename}")
        return filename

    except Exception as e:
        typer.echo(f"Error backing up applications: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("application")
def delete_application(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete an application.

    Example:
    -------
    scm-cli delete objects application --folder Texas --name custom-app

    """
    try:
        result = scm_client.delete_application(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted application: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting application: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("application")
def load_application(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load applications from a YAML file.

    Example:
    -------
    scm-cli load objects application --file config/applications.yml

    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(str(file), "applications")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["applications"]))
            return

        # Apply each application
        results = []
        for app_data in config["applications"]:
            # Validate using the Pydantic model
            application = Application(**app_data)

            # Call the SDK client to create the application
            result = scm_client.create_application(
                folder=application.folder,
                name=application.name,
                category=application.category,
                subcategory=application.subcategory,
                technology=application.technology,
                risk=application.risk,
                description=application.description,
                ports=application.ports,
                evasive=application.evasive,
                pervasive=application.pervasive,
                excessive_bandwidth_use=application.excessive_bandwidth_use,
                used_by_malware=application.used_by_malware,
                transfers_files=application.transfers_files,
                has_known_vulnerabilities=application.has_known_vulnerabilities,
                tunnels_other_apps=application.tunnels_other_apps,
                prone_to_misuse=application.prone_to_misuse,
                no_certifications=application.no_certifications,
            )

            results.append(result)
            typer.echo(f"Applied application: {result['name']} in folder {result['folder']}")

        return results
    except Exception as e:
        typer.echo(f"Error loading applications: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("application")
def set_application(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    category: str = CATEGORY_OPTION,
    subcategory: str = SUBCATEGORY_OPTION,
    technology: str = TECHNOLOGY_OPTION,
    risk: int = RISK_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    ports: list[str] | None = PORTS_OPTION,
    tags: list[str] | None = TAGS_OPTION,
    evasive: bool = EVASIVE_OPTION,
    pervasive: bool = PERVASIVE_OPTION,
    excessive_bandwidth_use: bool = EXCESSIVE_BANDWIDTH_OPTION,
    used_by_malware: bool = USED_BY_MALWARE_OPTION,
    transfers_files: bool = TRANSFERS_FILES_OPTION,
    has_known_vulnerabilities: bool = HAS_KNOWN_VULNERABILITIES_OPTION,
    tunnels_other_apps: bool = TUNNELS_OTHER_APPS_OPTION,
    prone_to_misuse: bool = PRONE_TO_MISUSE_OPTION,
    no_certifications: bool = NO_CERTIFICATIONS_OPTION,
):
    """Create or update an application.

    Example:
    -------
        scm-cli set objects application \
        --folder Texas \
        --name custom-database \
        --category business-systems \
        --subcategory database \
        --technology client-server \
        --risk 3 \
        --description "Custom database application" \
        --ports ["tcp/1521", "tcp/1522"] \
        --transfers-files

    """
    try:
        # Validate inputs using the Pydantic model
        application = Application(
            folder=folder,
            name=name,
            category=category,
            subcategory=subcategory,
            technology=technology,
            risk=risk,
            description=description or "",
            ports=ports or [],
            evasive=evasive,
            pervasive=pervasive,
            excessive_bandwidth_use=excessive_bandwidth_use,
            used_by_malware=used_by_malware,
            transfers_files=transfers_files,
            has_known_vulnerabilities=has_known_vulnerabilities,
            tunnels_other_apps=tunnels_other_apps,
            prone_to_misuse=prone_to_misuse,
            no_certifications=no_certifications,
        )

        # Call the SDK client to create the application
        result = scm_client.create_application(
            folder=application.folder,
            name=application.name,
            category=application.category,
            subcategory=application.subcategory,
            technology=application.technology,
            risk=application.risk,
            description=application.description,
            ports=application.ports,
            evasive=application.evasive,
            pervasive=application.pervasive,
            excessive_bandwidth_use=application.excessive_bandwidth_use,
            used_by_malware=application.used_by_malware,
            transfers_files=application.transfers_files,
            has_known_vulnerabilities=application.has_known_vulnerabilities,
            tunnels_other_apps=application.tunnels_other_apps,
            prone_to_misuse=application.prone_to_misuse,
            no_certifications=application.no_certifications,
        )

        typer.echo(f"Created application: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating application: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("application")
def show_application(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the application to show"),
    list_applications: bool = typer.Option(False, "--list", help="List all applications in the folder"),
):
    """Display application objects.

    Example:
    -------
        # List all applications in a folder
        scm-cli show objects application --folder Texas --list

        # Show a specific application by name
        scm-cli show objects application --folder Texas --name custom-database

    """
    try:
        if list_applications:
            # List all applications in the folder
            applications = scm_client.list_applications(folder=folder)

            if not applications:
                typer.echo(f"No applications found in folder '{folder}'")
                return

            typer.echo(f"Applications in folder '{folder}':")
            typer.echo("-" * 60)

            for app in applications:
                # Display application information
                typer.echo(f"Name: {app.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if app.get("folder"):
                    typer.echo(f"  Location: Folder '{app['folder']}'")
                elif app.get("snippet"):
                    typer.echo(f"  Location: Snippet '{app['snippet']}'")
                elif app.get("device"):
                    typer.echo(f"  Location: Device '{app['device']}'")
                else:
                    typer.echo("  Location: N/A")

                typer.echo(f"  Category: {app.get('category', 'N/A')}")
                typer.echo(f"  Subcategory: {app.get('subcategory', 'N/A')}")
                typer.echo(f"  Technology: {app.get('technology', 'N/A')}")
                typer.echo(f"  Risk: {app.get('risk', 'N/A')}")
                typer.echo(f"  Description: {app.get('description', 'N/A')}")

                # Display ports if present
                if app.get("ports"):
                    typer.echo(f"  Ports: {', '.join(app['ports'])}")

                # Display security attributes if any are true
                attrs = []
                if app.get("evasive"):
                    attrs.append("Evasive")
                if app.get("pervasive"):
                    attrs.append("Pervasive")
                if app.get("excessive_bandwidth_use"):
                    attrs.append("Excessive Bandwidth")
                if app.get("used_by_malware"):
                    attrs.append("Used by Malware")
                if app.get("transfers_files"):
                    attrs.append("Transfers Files")
                if app.get("has_known_vulnerabilities"):
                    attrs.append("Has Vulnerabilities")
                if app.get("tunnels_other_apps"):
                    attrs.append("Tunnels Apps")
                if app.get("prone_to_misuse"):
                    attrs.append("Prone to Misuse")
                if app.get("no_certifications"):
                    attrs.append("No Certifications")

                if attrs:
                    typer.echo(f"  Attributes: {', '.join(attrs)}")

                typer.echo("-" * 60)

            return applications

        elif name:
            # Get a specific application by name
            application = scm_client.get_application(folder=folder, name=name)

            typer.echo(f"Application: {application.get('name', 'N/A')}")

            # Display container location (folder, snippet, or device)
            if application.get("folder"):
                typer.echo(f"Location: Folder '{application['folder']}'")
            elif application.get("snippet"):
                typer.echo(f"Location: Snippet '{application['snippet']}'")
            elif application.get("device"):
                typer.echo(f"Location: Device '{application['device']}'")
            else:
                typer.echo("Location: N/A")

            typer.echo(f"Category: {application.get('category', 'N/A')}")
            typer.echo(f"Subcategory: {application.get('subcategory', 'N/A')}")
            typer.echo(f"Technology: {application.get('technology', 'N/A')}")
            typer.echo(f"Risk: {application.get('risk', 'N/A')}")
            typer.echo(f"Description: {application.get('description', 'N/A')}")

            # Display ports if present
            if application.get("ports"):
                typer.echo(f"Ports: {', '.join(application['ports'])}")

            # Display security attributes
            typer.echo("Security Attributes:")
            typer.echo(f"  Evasive: {application.get('evasive', False)}")
            typer.echo(f"  Pervasive: {application.get('pervasive', False)}")
            typer.echo(f"  Excessive Bandwidth Use: {application.get('excessive_bandwidth_use', False)}")
            typer.echo(f"  Used by Malware: {application.get('used_by_malware', False)}")
            typer.echo(f"  Transfers Files: {application.get('transfers_files', False)}")
            typer.echo(f"  Has Known Vulnerabilities: {application.get('has_known_vulnerabilities', False)}")
            typer.echo(f"  Tunnels Other Apps: {application.get('tunnels_other_apps', False)}")
            typer.echo(f"  Prone to Misuse: {application.get('prone_to_misuse', False)}")
            typer.echo(f"  No Certifications: {application.get('no_certifications', False)}")

            # Display ID if present
            if application.get("id"):
                typer.echo(f"ID: {application['id']}")

            return application

        else:
            # Neither --list nor --name was provided
            typer.echo("Error: Either --list or --name must be specified", err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"Error showing application: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# APPLICATION GROUP COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("application-group")
def backup_application_group(
    folder: str = FOLDER_OPTION,
):
    """Backup all application groups from a folder to a YAML file.

    The backup file will be named 'application-group-{folder}.yaml' in the current directory.

    Example:
    -------
    scm-cli backup objects application-group --folder Austin

    """
    try:
        # List all application groups in the folder with exact_match=True
        groups = scm_client.list_application_groups(folder=folder, exact_match=True)

        if not groups:
            typer.echo(f"No application groups found in folder '{folder}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for group in groups:
            # The list method returns dict objects already, but let's ensure we exclude any None values
            group_dict = {k: v for k, v in group.items() if v is not None}
            # Remove system fields that shouldn't be in backup
            group_dict.pop("id", None)
            backup_data.append(group_dict)

        # Create the YAML structure
        yaml_data = {"application_groups": backup_data}

        # Generate filename
        filename = f"application-group-{folder.lower()}.yaml"

        # Write to YAML file
        with open(filename, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} application groups to {filename}")
        return filename

    except Exception as e:
        typer.echo(f"Error backing up application groups: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("application-group")
def delete_application_group(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete an application group.

    Example:
    -------
    scm-cli delete objects application-group --folder Texas --name web-apps

    """
    try:
        result = scm_client.delete_application_group(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted application group: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting application group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("application-group")
def load_application_group(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load application groups from a YAML file.

    Example:
    -------
    scm-cli load objects application-group --file config/application_groups.yml

    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(str(file), "application_groups")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["application_groups"]))
            return

        # Apply each application group
        results = []
        for group_data in config["application_groups"]:
            # Validate using the Pydantic model
            app_group = ApplicationGroup(**group_data)

            # Call the SDK client to create the application group
            result = scm_client.create_application_group(
                folder=app_group.folder,
                name=app_group.name,
                members=app_group.members,
            )

            results.append(result)
            typer.echo(f"Applied application group: {result['name']} in folder {result['folder']}")

        return results
    except Exception as e:
        typer.echo(f"Error loading application groups: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("application-group")
def set_application_group(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    members: list[str] = APP_GROUP_MEMBERS_OPTION,
):
    """Create or update an application group.

    Example:
    -------
        scm-cli set objects application-group \
        --folder Texas \
        --name web-apps \
        --members ["ssl", "web-browsing", "http", "https"]

    """
    try:
        # Validate inputs using the Pydantic model
        app_group = ApplicationGroup(
            folder=folder,
            name=name,
            members=members,
        )

        # Call the SDK client to create the application group
        result = scm_client.create_application_group(
            folder=app_group.folder,
            name=app_group.name,
            members=app_group.members,
        )

        typer.echo(f"Created application group: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating application group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("application-group")
def show_application_group(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the application group to show"),
    list_groups: bool = typer.Option(False, "--list", help="List all application groups in the folder"),
):
    """Display application group objects.

    Example:
    -------
        # List all application groups in a folder
        scm-cli show objects application-group --folder Texas --list

        # Show a specific application group by name
        scm-cli show objects application-group --folder Texas --name web-apps

    """
    try:
        if list_groups:
            # List all application groups in the folder
            groups = scm_client.list_application_groups(folder=folder)

            if not groups:
                typer.echo(f"No application groups found in folder '{folder}'")
                return

            typer.echo(f"Application Groups in folder '{folder}':")
            typer.echo("-" * 60)

            for group in groups:
                # Display application group information
                typer.echo(f"Name: {group.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if group.get("folder"):
                    typer.echo(f"  Location: Folder '{group['folder']}'")
                elif group.get("snippet"):
                    typer.echo(f"  Location: Snippet '{group['snippet']}'")
                elif group.get("device"):
                    typer.echo(f"  Location: Device '{group['device']}'")
                else:
                    typer.echo("  Location: N/A")

                # Display members
                members = group.get("members", [])
                if members:
                    typer.echo(f"  Members ({len(members)}): {', '.join(members)}")
                else:
                    typer.echo("  Members: None")

                typer.echo("-" * 60)

            return groups

        elif name:
            # Get a specific application group by name
            group = scm_client.get_application_group(folder=folder, name=name)

            typer.echo(f"Application Group: {group.get('name', 'N/A')}")

            # Display container location (folder, snippet, or device)
            if group.get("folder"):
                typer.echo(f"Location: Folder '{group['folder']}'")
            elif group.get("snippet"):
                typer.echo(f"Location: Snippet '{group['snippet']}'")
            elif group.get("device"):
                typer.echo(f"Location: Device '{group['device']}'")
            else:
                typer.echo("Location: N/A")

            # Display members
            members = group.get("members", [])
            if members:
                typer.echo(f"Members ({len(members)}):")
                for member in members:
                    typer.echo(f"  - {member}")
            else:
                typer.echo("Members: None")

            # Display ID if present
            if group.get("id"):
                typer.echo(f"ID: {group['id']}")

            return group

        else:
            # Neither --list nor --name was provided
            typer.echo("Error: Either --list or --name must be specified", err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"Error showing application group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# APPLICATION FILTER COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("application-filter")
def backup_application_filter(
    folder: str = FOLDER_OPTION,
):
    """Backup all application filters from a folder to a YAML file.

    The backup file will be named 'application-filter-{folder}.yaml' in the current directory.

    Example:
    -------
    scm-cli backup objects application-filter --folder Austin

    """
    try:
        # List all application filters in the folder with exact_match=True
        filters = scm_client.list_application_filters(folder=folder, exact_match=True)

        if not filters:
            typer.echo(f"No application filters found in folder '{folder}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for filter_obj in filters:
            # The list method returns dict objects already, but let's ensure we exclude any None values
            filter_dict = {k: v for k, v in filter_obj.items() if v is not None}
            # Remove system fields that shouldn't be in backup
            filter_dict.pop("id", None)
            backup_data.append(filter_dict)

        # Create the YAML structure
        yaml_data = {"application_filters": backup_data}

        # Generate filename
        filename = f"application-filter-{folder.lower()}.yaml"

        # Write to YAML file
        with open(filename, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} application filters to {filename}")
        return filename

    except Exception as e:
        typer.echo(f"Error backing up application filters: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("application-filter")
def delete_application_filter(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete an application filter.

    Example:
    -------
    scm-cli delete objects application-filter --folder Texas --name high-risk-apps

    """
    try:
        result = scm_client.delete_application_filter(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted application filter: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting application filter: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("application-filter")
def load_application_filter(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load application filters from a YAML file.

    Example:
    -------
    scm-cli load objects application-filter --file config/application_filters.yml

    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(str(file), "application_filters")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["application_filters"]))
            return

        # Apply each application filter
        results = []
        for filter_data in config["application_filters"]:
            # Validate using the Pydantic model
            app_filter = ApplicationFilter(**filter_data)

            # Call the SDK client to create the application filter
            result = scm_client.create_application_filter(
                folder=app_filter.folder,
                name=app_filter.name,
                category=app_filter.category,
                subcategory=app_filter.subcategory,
                technology=app_filter.technology,
                risk=app_filter.risk,
                evasive=app_filter.evasive,
                pervasive=app_filter.pervasive,
                excessive_bandwidth_use=app_filter.excessive_bandwidth_use,
                used_by_malware=app_filter.used_by_malware,
                transfers_files=app_filter.transfers_files,
                has_known_vulnerabilities=app_filter.has_known_vulnerabilities,
                tunnels_other_apps=app_filter.tunnels_other_apps,
                prone_to_misuse=app_filter.prone_to_misuse,
                no_certifications=app_filter.no_certifications,
            )

            results.append(result)
            typer.echo(f"Applied application filter: {result['name']} in folder {result['folder']}")

        return results
    except Exception as e:
        typer.echo(f"Error loading application filters: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("application-filter")
def set_application_filter(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    category: list[str] = FILTER_CATEGORY_OPTION,
    subcategory: list[str] = FILTER_SUBCATEGORY_OPTION,
    technology: list[str] = FILTER_TECHNOLOGY_OPTION,
    risk: list[int] = FILTER_RISK_OPTION,
    evasive: bool = EVASIVE_OPTION,
    pervasive: bool = PERVASIVE_OPTION,
    excessive_bandwidth_use: bool = EXCESSIVE_BANDWIDTH_OPTION,
    used_by_malware: bool = USED_BY_MALWARE_OPTION,
    transfers_files: bool = TRANSFERS_FILES_OPTION,
    has_known_vulnerabilities: bool = HAS_KNOWN_VULNERABILITIES_OPTION,
    tunnels_other_apps: bool = TUNNELS_OTHER_APPS_OPTION,
    prone_to_misuse: bool = PRONE_TO_MISUSE_OPTION,
    no_certifications: bool = NO_CERTIFICATIONS_OPTION,
):
    """Create or update an application filter.

    Example:
    -------
        scm-cli set objects application-filter \
        --folder Texas \
        --name high-risk-apps \
        --category ["business-systems"] \
        --subcategory ["database"] \
        --technology ["client-server"] \
        --risk [4, 5] \
        --has-known-vulnerabilities \
        --used-by-malware

    """
    try:
        # Validate inputs using the Pydantic model
        app_filter = ApplicationFilter(
            folder=folder,
            name=name,
            category=category,
            subcategory=subcategory,
            technology=technology,
            risk=risk,
            evasive=evasive,
            pervasive=pervasive,
            excessive_bandwidth_use=excessive_bandwidth_use,
            used_by_malware=used_by_malware,
            transfers_files=transfers_files,
            has_known_vulnerabilities=has_known_vulnerabilities,
            tunnels_other_apps=tunnels_other_apps,
            prone_to_misuse=prone_to_misuse,
            no_certifications=no_certifications,
        )

        # Call the SDK client to create the application filter
        result = scm_client.create_application_filter(
            folder=app_filter.folder,
            name=app_filter.name,
            category=app_filter.category,
            subcategory=app_filter.subcategory,
            technology=app_filter.technology,
            risk=app_filter.risk,
            evasive=app_filter.evasive,
            pervasive=app_filter.pervasive,
            excessive_bandwidth_use=app_filter.excessive_bandwidth_use,
            used_by_malware=app_filter.used_by_malware,
            transfers_files=app_filter.transfers_files,
            has_known_vulnerabilities=app_filter.has_known_vulnerabilities,
            tunnels_other_apps=app_filter.tunnels_other_apps,
            prone_to_misuse=app_filter.prone_to_misuse,
            no_certifications=app_filter.no_certifications,
        )

        typer.echo(f"Created application filter: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating application filter: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("application-filter")
def show_application_filter(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the application filter to show"),
    list_filters: bool = typer.Option(False, "--list", help="List all application filters in the folder"),
):
    """Display application filter objects.

    Example:
    -------
        # List all application filters in a folder
        scm-cli show objects application-filter --folder Texas --list

        # Show a specific application filter by name
        scm-cli show objects application-filter --folder Texas --name high-risk-apps

    """
    try:
        if list_filters:
            # List all application filters in the folder
            filters = scm_client.list_application_filters(folder=folder)

            if not filters:
                typer.echo(f"No application filters found in folder '{folder}'")
                return

            typer.echo(f"Application Filters in folder '{folder}':")
            typer.echo("-" * 60)

            for filter_obj in filters:
                # Display application filter information
                typer.echo(f"Name: {filter_obj.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if filter_obj.get("folder"):
                    typer.echo(f"  Location: Folder '{filter_obj['folder']}'")
                elif filter_obj.get("snippet"):
                    typer.echo(f"  Location: Snippet '{filter_obj['snippet']}'")
                elif filter_obj.get("device"):
                    typer.echo(f"  Location: Device '{filter_obj['device']}'")
                else:
                    typer.echo("  Location: N/A")

                # Display filter criteria
                if filter_obj.get("category"):
                    typer.echo(f"  Categories: {', '.join(filter_obj['category'])}")
                if filter_obj.get("sub_category"):
                    typer.echo(f"  Subcategories: {', '.join(filter_obj['sub_category'])}")
                if filter_obj.get("technology"):
                    typer.echo(f"  Technologies: {', '.join(filter_obj['technology'])}")
                if filter_obj.get("risk"):
                    typer.echo(f"  Risk Levels: {', '.join(map(str, filter_obj['risk']))}")

                # Display boolean criteria if any are true
                attrs = []
                if filter_obj.get("evasive"):
                    attrs.append("Evasive")
                if filter_obj.get("pervasive"):
                    attrs.append("Pervasive")
                if filter_obj.get("excessive_bandwidth_use"):
                    attrs.append("Excessive Bandwidth")
                if filter_obj.get("used_by_malware"):
                    attrs.append("Used by Malware")
                if filter_obj.get("transfers_files"):
                    attrs.append("Transfers Files")
                if filter_obj.get("has_known_vulnerabilities"):
                    attrs.append("Has Vulnerabilities")
                if filter_obj.get("tunnels_other_apps"):
                    attrs.append("Tunnels Apps")
                if filter_obj.get("prone_to_misuse"):
                    attrs.append("Prone to Misuse")
                if filter_obj.get("no_certifications"):
                    attrs.append("No Certifications")

                if attrs:
                    typer.echo(f"  Filter Attributes: {', '.join(attrs)}")

                typer.echo("-" * 60)

            return filters

        elif name:
            # Get a specific application filter by name
            filter_obj = scm_client.get_application_filter(folder=folder, name=name)

            typer.echo(f"Application Filter: {filter_obj.get('name', 'N/A')}")

            # Display container location (folder, snippet, or device)
            if filter_obj.get("folder"):
                typer.echo(f"Location: Folder '{filter_obj['folder']}'")
            elif filter_obj.get("snippet"):
                typer.echo(f"Location: Snippet '{filter_obj['snippet']}'")
            elif filter_obj.get("device"):
                typer.echo(f"Location: Device '{filter_obj['device']}'")
            else:
                typer.echo("Location: N/A")

            # Display filter criteria
            typer.echo("\nFilter Criteria:")
            if filter_obj.get("category"):
                typer.echo(f"  Categories: {', '.join(filter_obj['category'])}")
            if filter_obj.get("sub_category"):
                typer.echo(f"  Subcategories: {', '.join(filter_obj['sub_category'])}")
            if filter_obj.get("technology"):
                typer.echo(f"  Technologies: {', '.join(filter_obj['technology'])}")
            if filter_obj.get("risk"):
                typer.echo(f"  Risk Levels: {', '.join(map(str, filter_obj['risk']))}")

            # Display boolean attributes
            typer.echo("\nFilter Attributes:")
            typer.echo(f"  Evasive: {filter_obj.get('evasive', False)}")
            typer.echo(f"  Pervasive: {filter_obj.get('pervasive', False)}")
            typer.echo(f"  Excessive Bandwidth Use: {filter_obj.get('excessive_bandwidth_use', False)}")
            typer.echo(f"  Used by Malware: {filter_obj.get('used_by_malware', False)}")
            typer.echo(f"  Transfers Files: {filter_obj.get('transfers_files', False)}")
            typer.echo(f"  Has Known Vulnerabilities: {filter_obj.get('has_known_vulnerabilities', False)}")
            typer.echo(f"  Tunnels Other Apps: {filter_obj.get('tunnels_other_apps', False)}")
            typer.echo(f"  Prone to Misuse: {filter_obj.get('prone_to_misuse', False)}")
            typer.echo(f"  No Certifications: {filter_obj.get('no_certifications', False)}")

            # Display ID if present
            if filter_obj.get("id"):
                typer.echo(f"\nID: {filter_obj['id']}")

            return filter_obj

        else:
            # Neither --list nor --name was provided
            typer.echo("Error: Either --list or --name must be specified", err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"Error showing application filter: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# DYNAMIC USER GROUP COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("dynamic-user-group")
def backup_dynamic_user_group(
    folder: str = FOLDER_OPTION,
):
    """Backup all dynamic user groups from a folder to a YAML file.

    The backup file will be named 'dynamic-user-group-{folder}.yaml' in the current directory.

    Example:
    -------
    scm-cli backup objects dynamic-user-group --folder Austin

    """
    try:
        # List all dynamic user groups in the folder with exact_match=True
        groups = scm_client.list_dynamic_user_groups(folder=folder, exact_match=True)

        if not groups:
            typer.echo(f"No dynamic user groups found in folder '{folder}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for group in groups:
            # The list method returns dict objects already, but let's ensure we exclude any None values
            group_dict = {k: v for k, v in group.items() if v is not None}
            # Remove system fields that shouldn't be in backup
            group_dict.pop("id", None)

            # Convert 'tag' back to 'tags' for CLI consistency
            if "tag" in group_dict:
                group_dict["tags"] = group_dict.pop("tag")

            backup_data.append(group_dict)

        # Create the YAML structure
        yaml_data = {"dynamic_user_groups": backup_data}

        # Generate filename
        filename = f"dynamic-user-group-{folder.lower()}.yaml"

        # Write to YAML file
        with open(filename, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} dynamic user groups to {filename}")
        return filename

    except Exception as e:
        typer.echo(f"Error backing up dynamic user groups: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("dynamic-user-group")
def delete_dynamic_user_group(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete a dynamic user group.

    Example:
    -------
    scm-cli delete objects dynamic-user-group --folder Texas --name it-admins

    """
    try:
        result = scm_client.delete_dynamic_user_group(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted dynamic user group: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting dynamic user group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("dynamic-user-group")
def load_dynamic_user_group(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load dynamic user groups from a YAML file.

    Example:
    -------
    scm-cli load objects dynamic-user-group --file config/dynamic_user_groups.yml

    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(str(file), "dynamic_user_groups")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["dynamic_user_groups"]))
            return

        # Apply each dynamic user group
        results = []
        for group_data in config["dynamic_user_groups"]:
            # Validate using the Pydantic model
            dug = DynamicUserGroup(**group_data)

            # Call the SDK client to create the dynamic user group
            result = scm_client.create_dynamic_user_group(
                folder=dug.folder,
                name=dug.name,
                filter=dug.filter,
                description=dug.description,
                tags=dug.tags,
            )

            results.append(result)
            typer.echo(f"Applied dynamic user group: {result['name']} in folder {result['folder']}")

        return results
    except Exception as e:
        typer.echo(f"Error loading dynamic user groups: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("dynamic-user-group")
def set_dynamic_user_group(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    filter: str = FILTER_EXPRESSION_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    tags: list[str] | None = TAGS_OPTION,
):
    """Create or update a dynamic user group.

    Example:
    -------
        scm-cli set objects dynamic-user-group \\
        --folder Texas \\
        --name it-admins \\
        --filter "tag.Department='IT' and tag.Role='Admin'" \\
        --description "IT administrators" \\
        --tags ["automation", "admin"]

    """
    try:
        # Validate inputs using the Pydantic model
        dug = DynamicUserGroup(
            folder=folder,
            name=name,
            filter=filter,
            description=description or "",
            tags=tags or [],
        )

        # Call the SDK client to create the dynamic user group
        result = scm_client.create_dynamic_user_group(
            folder=dug.folder,
            name=dug.name,
            filter=dug.filter,
            description=dug.description,
            tags=dug.tags,
        )

        typer.echo(f"Created dynamic user group: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating dynamic user group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("dynamic-user-group")
def show_dynamic_user_group(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the dynamic user group to show"),
    list_groups: bool = typer.Option(False, "--list", help="List all dynamic user groups in the folder"),
):
    """Display dynamic user group objects.

    Example:
    -------
        # List all dynamic user groups in a folder
        scm-cli show objects dynamic-user-group --folder Texas --list

        # Show a specific dynamic user group by name
        scm-cli show objects dynamic-user-group --folder Texas --name it-admins

    """
    try:
        if list_groups:
            # List all dynamic user groups in the folder
            groups = scm_client.list_dynamic_user_groups(folder=folder)

            if not groups:
                typer.echo(f"No dynamic user groups found in folder '{folder}'")
                return

            typer.echo(f"Dynamic User Groups in folder '{folder}':")
            typer.echo("-" * 60)

            for group in groups:
                # Display dynamic user group information
                typer.echo(f"Name: {group.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if group.get("folder"):
                    typer.echo(f"  Location: Folder '{group['folder']}'")
                elif group.get("snippet"):
                    typer.echo(f"  Location: Snippet '{group['snippet']}'")
                elif group.get("device"):
                    typer.echo(f"  Location: Device '{group['device']}'")
                else:
                    typer.echo("  Location: N/A")

                typer.echo(f"  Filter: {group.get('filter', 'N/A')}")
                typer.echo(f"  Description: {group.get('description', 'N/A')}")

                # Display tags if present
                if group.get("tag"):
                    typer.echo(f"  Tags: {', '.join(group['tag'])}")

                typer.echo("-" * 60)

            return groups

        elif name:
            # Get a specific dynamic user group by name
            group = scm_client.get_dynamic_user_group(folder=folder, name=name)

            typer.echo(f"Dynamic User Group: {group.get('name', 'N/A')}")

            # Display container location (folder, snippet, or device)
            if group.get("folder"):
                typer.echo(f"Location: Folder '{group['folder']}'")
            elif group.get("snippet"):
                typer.echo(f"Location: Snippet '{group['snippet']}'")
            elif group.get("device"):
                typer.echo(f"Location: Device '{group['device']}'")
            else:
                typer.echo("Location: N/A")

            typer.echo(f"Filter: {group.get('filter', 'N/A')}")
            typer.echo(f"Description: {group.get('description', 'N/A')}")

            # Display tags if present
            if group.get("tag"):
                typer.echo(f"Tags: {', '.join(group['tag'])}")

            # Display ID if present
            if group.get("id"):
                typer.echo(f"ID: {group['id']}")

            return group

        else:
            # Neither --list nor --name was provided
            typer.echo("Error: Either --list or --name must be specified", err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"Error showing dynamic user group: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# EXTERNAL DYNAMIC LIST COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("external-dynamic-list")
def backup_external_dynamic_list(
    folder: str = FOLDER_OPTION,
):
    """Backup all external dynamic lists from a folder to a YAML file.

    The backup file will be named 'external-dynamic-list-{folder}.yaml' in the current directory.

    Example:
    -------
    scm-cli backup objects external-dynamic-list --folder Austin

    """
    try:
        # List all external dynamic lists in the folder with exact_match=True
        edls = scm_client.list_external_dynamic_lists(folder=folder, exact_match=True)

        if not edls:
            typer.echo(f"No external dynamic lists found in folder '{folder}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for edl in edls:
            # The list method returns dict objects already, but let's ensure we exclude any None values
            edl_dict = {k: v for k, v in edl.items() if v is not None}
            # Remove system fields that shouldn't be in backup
            edl_dict.pop("id", None)

            # Convert nested type structure to flat structure for easier YAML editing
            if "type" in edl_dict and isinstance(edl_dict["type"], dict):
                type_data = edl_dict["type"]
                # Extract the type key (predefined_ip, ip, domain, etc.)
                type_key = list(type_data.keys())[0]
                edl_dict["type"] = type_key

                # Flatten the type-specific configuration
                type_config = type_data[type_key]
                for key, value in type_config.items():
                    if key == "recurring" and isinstance(value, dict):
                        # Handle recurring configuration
                        recur_type = list(value.keys())[0]
                        edl_dict["recurring"] = recur_type
                        if recur_type in ["daily", "weekly", "monthly"]:
                            recur_config = value[recur_type]
                            if "at" in recur_config:
                                edl_dict["hour"] = recur_config["at"]
                            if "day_of_week" in recur_config:
                                edl_dict["day"] = recur_config["day_of_week"]
                            elif "day_of_month" in recur_config:
                                edl_dict["day"] = str(recur_config["day_of_month"])
                    elif key == "auth" and isinstance(value, dict):
                        # Handle authentication
                        edl_dict["username"] = value.get("username")
                        edl_dict["password"] = value.get("password")
                    else:
                        edl_dict[key] = value

            backup_data.append(edl_dict)

        # Create the YAML structure
        yaml_data = {"external_dynamic_lists": backup_data}

        # Generate filename
        filename = f"external-dynamic-list-{folder.lower()}.yaml"

        # Write to YAML file
        with open(filename, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} external dynamic lists to {filename}")
        return filename

    except Exception as e:
        typer.echo(f"Error backing up external dynamic lists: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("external-dynamic-list")
def delete_external_dynamic_list(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete an external dynamic list.

    Example:
    -------
    scm-cli delete objects external-dynamic-list --folder Texas --name malicious-ips

    """
    try:
        result = scm_client.delete_external_dynamic_list(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted external dynamic list: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting external dynamic list: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("external-dynamic-list")
def load_external_dynamic_list(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load external dynamic lists from a YAML file.

    Example:
    -------
    scm-cli load objects external-dynamic-list --file config/external_dynamic_lists.yml

    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(str(file), "external_dynamic_lists")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")

        # Validate the configuration
        from scm_cli.utils.validators import ExternalDynamicList, validate_yaml_file

        external_dynamic_lists = validate_yaml_file(config, ExternalDynamicList, "external_dynamic_lists")

        results = []
        for idx, edl in enumerate(external_dynamic_lists):
            if dry_run:
                typer.echo(f"\n[{idx + 1}] External Dynamic List: {edl.name}")
                typer.echo(f"  Folder: {edl.folder}")
                typer.echo(f"  Type: {edl.type}")
                typer.echo(f"  URL: {edl.url}")
                if edl.description:
                    typer.echo(f"  Description: {edl.description}")
                if edl.recurring:
                    typer.echo(f"  Update Frequency: {edl.recurring}")
                results.append({"action": "would create/update", "name": edl.name})
            else:
                try:
                    # Convert to SDK model format
                    edl_data = edl.to_sdk_model()
                    result = scm_client.create_external_dynamic_list(
                        folder=edl.folder,
                        name=edl.name,
                        type_config=edl_data["type"],
                    )
                    typer.echo(f"✓ Created/Updated external dynamic list: {edl.name}")
                    results.append({"action": "created/updated", "name": edl.name, "result": result})
                except Exception as e:
                    typer.echo(f"✗ Error with external dynamic list '{edl.name}': {str(e)}", err=True)
                    results.append({"action": "error", "name": edl.name, "error": str(e)})

        # Summary
        total = len(external_dynamic_lists)
        if dry_run:
            typer.echo(f"\nDry run complete. Would create/update {total} external dynamic lists.")
        else:
            successful = sum(1 for r in results if r["action"] == "created/updated")
            failed = sum(1 for r in results if r["action"] == "error")
            typer.echo(f"\nOperation complete: {successful} successful, {failed} failed out of {total} total.")

        return results

    except Exception as e:
        typer.echo(f"Error loading external dynamic lists: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("external-dynamic-list")
def set_external_dynamic_list(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    type: str = typer.Option(..., help="Type of EDL (predefined_ip, predefined_url, ip, domain, url, imsi, imei)"),
    url: str = typer.Option(..., help="URL for the external list"),
    description: str = typer.Option("", help="Description of the external dynamic list"),
    exception_list: list[str] = typer.Option(default_factory=list, help="Exception list entries"),
    recurring: str = typer.Option(None, help="Update frequency (five_minute, hourly, daily, weekly, monthly)"),
    hour: str = typer.Option(None, help="Hour for daily/weekly/monthly updates (00-23)"),
    day: str = typer.Option(None, help="Day for weekly (sunday-saturday) or monthly (1-31) updates"),
    username: str = typer.Option(None, help="Authentication username"),
    password: str = typer.Option(None, help="Authentication password"),
    certificate_profile: str = typer.Option(None, help="Certificate profile for authentication"),
    expand_domain: bool = typer.Option(False, help="Enable/Disable expand domain (for domain type)"),
):
    """Create or update an external dynamic list.

    Example:
    -------
        # Create a predefined IP list
        scm-cli set objects external-dynamic-list --folder Texas --name paloalto-bulletproof \\
            --type predefined_ip --url "https://saasedl.paloaltonetworks.com/feeds/BulletproofIPList"

        # Create a custom IP blocklist with hourly updates
        scm-cli set objects external-dynamic-list --folder Texas --name custom-blocklist \\
            --type ip --url "https://example.com/blocklist.txt" --recurring hourly

        # Create a domain list with daily updates at 3 AM
        scm-cli set objects external-dynamic-list --folder Texas --name malicious-domains \\
            --type domain --url "https://example.com/domains.txt" --recurring daily --hour 03 \\
            --expand-domain

    """
    try:
        # Validate the configuration
        from scm_cli.utils.validators import ExternalDynamicList

        edl_config = {
            "folder": folder,
            "name": name,
            "type": type,
            "url": url,
            "description": description,
            "exception_list": exception_list,
            "recurring": recurring,
            "hour": hour,
            "day": day,
            "username": username,
            "password": password,
            "certificate_profile": certificate_profile,
            "expand_domain": expand_domain,
        }

        # Remove None values
        edl_config = {k: v for k, v in edl_config.items() if v is not None}

        # Validate using Pydantic model
        edl = ExternalDynamicList(**edl_config)

        # Convert to SDK model format
        edl_data = edl.to_sdk_model()

        # Create/update the external dynamic list
        result = scm_client.create_external_dynamic_list(
            folder=folder,
            name=name,
            type_config=edl_data["type"],
        )

        typer.echo(f"Successfully created/updated external dynamic list: {name}")
        return result

    except Exception as e:
        typer.echo(f"Error creating/updating external dynamic list: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("external-dynamic-list")
def show_external_dynamic_list(
    folder: str = FOLDER_OPTION,
    name: str = typer.Option(None, help="Name of the external dynamic list to show"),
    list_edls: bool = typer.Option(False, "--list", help="List all external dynamic lists in the folder"),
):
    """Show external dynamic list details or list all external dynamic lists in a folder.

    Example:
    -------
        # List all external dynamic lists in a folder
        scm-cli show objects external-dynamic-list --folder Texas --list

        # Show a specific external dynamic list by name
        scm-cli show objects external-dynamic-list --folder Texas --name malicious-ips

    """
    try:
        if list_edls:
            # List all external dynamic lists in the folder
            edls = scm_client.list_external_dynamic_lists(folder=folder)

            if not edls:
                typer.echo(f"No external dynamic lists found in folder '{folder}'")
                return

            typer.echo(f"External Dynamic Lists in folder '{folder}':")
            typer.echo("-" * 60)

            for edl in edls:
                # Display external dynamic list information
                typer.echo(f"Name: {edl.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if edl.get("folder"):
                    typer.echo(f"  Location: Folder '{edl['folder']}'")
                elif edl.get("snippet"):
                    typer.echo(f"  Location: Snippet '{edl['snippet']}'")
                elif edl.get("device"):
                    typer.echo(f"  Location: Device '{edl['device']}'")
                else:
                    typer.echo("  Location: N/A")

                # Display type information
                if edl.get("type") and isinstance(edl["type"], dict):
                    type_key = list(edl["type"].keys())[0]
                    type_config = edl["type"][type_key]
                    typer.echo(f"  Type: {type_key}")
                    typer.echo(f"  URL: {type_config.get('url', 'N/A')}")
                    if type_config.get("description"):
                        typer.echo(f"  Description: {type_config['description']}")
                    if type_config.get("recurring"):
                        recur_type = list(type_config["recurring"].keys())[0]
                        typer.echo(f"  Update Frequency: {recur_type}")
                    if type_config.get("exception_list"):
                        typer.echo(f"  Exception List: {', '.join(type_config['exception_list'])}")

                typer.echo("-" * 60)

            return edls

        elif name:
            # Get a specific external dynamic list by name
            edl = scm_client.get_external_dynamic_list(folder=folder, name=name)

            typer.echo(f"External Dynamic List: {edl.get('name', 'N/A')}")

            # Display container location (folder, snippet, or device)
            if edl.get("folder"):
                typer.echo(f"Location: Folder '{edl['folder']}'")
            elif edl.get("snippet"):
                typer.echo(f"Location: Snippet '{edl['snippet']}'")
            elif edl.get("device"):
                typer.echo(f"Location: Device '{edl['device']}'")
            else:
                typer.echo("Location: N/A")

            # Display type information
            if edl.get("type") and isinstance(edl["type"], dict):
                type_key = list(edl["type"].keys())[0]
                type_config = edl["type"][type_key]
                typer.echo(f"Type: {type_key}")
                typer.echo(f"URL: {type_config.get('url', 'N/A')}")
                if type_config.get("description"):
                    typer.echo(f"Description: {type_config['description']}")
                if type_config.get("recurring"):
                    recur_type = list(type_config["recurring"].keys())[0]
                    typer.echo(f"Update Frequency: {recur_type}")
                    recur_config = type_config["recurring"][recur_type]
                    if recur_config and isinstance(recur_config, dict):
                        if "at" in recur_config:
                            typer.echo(f"  Update Hour: {recur_config['at']}")
                        if "day_of_week" in recur_config:
                            typer.echo(f"  Update Day: {recur_config['day_of_week']}")
                        elif "day_of_month" in recur_config:
                            typer.echo(f"  Update Day: {recur_config['day_of_month']}")
                if type_config.get("exception_list"):
                    typer.echo(f"Exception List: {', '.join(type_config['exception_list'])}")
                if type_config.get("auth"):
                    typer.echo(f"Authentication: Username '{type_config['auth']['username']}'")
                if type_config.get("certificate_profile"):
                    typer.echo(f"Certificate Profile: {type_config['certificate_profile']}")
                if type_config.get("expand_domain"):
                    typer.echo(f"Expand Domain: {type_config['expand_domain']}")

            # Display ID if present
            if edl.get("id"):
                typer.echo(f"ID: {edl['id']}")

            return edl

        else:
            # Neither --list nor --name was provided
            typer.echo("Error: Either --list or --name must be specified", err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"Error showing external dynamic list: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# HIP OBJECT COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("hip-object")
def backup_hip_object(
    folder: str = FOLDER_OPTION,
):
    """Backup all HIP objects from a folder to a YAML file.

    The backup file will be named 'hip-object-{folder}.yaml' in the current directory.

    Example:
    -------
    scm-cli backup objects hip-object --folder Austin

    """
    try:
        # List all HIP objects in the folder with exact_match=True
        hip_objects = scm_client.list_hip_objects(folder=folder, exact_match=True)

        if not hip_objects:
            typer.echo(f"No HIP objects found in folder '{folder}'")
            return

        # Convert SDK models to dictionaries, excluding unset values
        backup_data = []
        for hip_obj in hip_objects:
            # The list method returns dict objects already, but let's ensure we exclude any None values
            hip_dict = {k: v for k, v in hip_obj.items() if v is not None}
            # Remove system fields that shouldn't be in backup
            hip_dict.pop("id", None)

            # Flatten the structure for easier YAML editing
            flat_dict = {"folder": hip_dict.get("folder"), "name": hip_dict.get("name")}
            
            if hip_dict.get("description"):
                flat_dict["description"] = hip_dict["description"]

            # Flatten host info
            if hip_dict.get("host_info") and hip_dict["host_info"].get("criteria"):
                criteria = hip_dict["host_info"]["criteria"]
                
                # Handle string comparisons
                if criteria.get("domain"):
                    domain_val = criteria["domain"]
                    if "is" in domain_val:
                        flat_dict["host_info_domain"] = "is"
                        flat_dict["host_info_domain_value"] = domain_val["is"]
                    elif "is_not" in domain_val:
                        flat_dict["host_info_domain"] = "is_not"
                        flat_dict["host_info_domain_value"] = domain_val["is_not"]
                    elif "contains" in domain_val:
                        flat_dict["host_info_domain"] = "contains"
                        flat_dict["host_info_domain_value"] = domain_val["contains"]
                
                # Handle OS
                if criteria.get("os") and criteria["os"].get("contains"):
                    os_data = criteria["os"]["contains"]
                    for vendor, value in os_data.items():
                        flat_dict["host_info_os"] = vendor
                        flat_dict["host_info_os_value"] = value
                
                # Handle other string comparisons
                for field in ["client_version", "host_name", "host_id", "serial_number"]:
                    if criteria.get(field):
                        field_val = criteria[field]
                        if "is" in field_val:
                            flat_dict[f"host_info_{field}"] = "is"
                            flat_dict[f"host_info_{field}_value"] = field_val["is"]
                        elif "is_not" in field_val:
                            flat_dict[f"host_info_{field}"] = "is_not"
                            flat_dict[f"host_info_{field}_value"] = field_val["is_not"]
                        elif "contains" in field_val:
                            flat_dict[f"host_info_{field}"] = "contains"
                            flat_dict[f"host_info_{field}_value"] = field_val["contains"]
                
                # Handle managed state
                if "managed" in criteria:
                    flat_dict["host_info_managed"] = criteria["managed"]

            # Flatten network info
            if hip_dict.get("network_info") and hip_dict["network_info"].get("criteria"):
                criteria = hip_dict["network_info"]["criteria"]
                if criteria.get("network"):
                    network_val = criteria["network"]
                    if "is" in network_val:
                        flat_dict["network_info_type"] = "is"
                        flat_dict["network_info_value"] = list(network_val["is"].keys())[0]
                    elif "is_not" in network_val:
                        flat_dict["network_info_type"] = "is_not"
                        flat_dict["network_info_value"] = list(network_val["is_not"].keys())[0]

            # Handle patch management
            if hip_dict.get("patch_management"):
                pm_data = hip_dict["patch_management"]
                if pm_data.get("criteria"):
                    criteria = pm_data["criteria"]
                    if "is_installed" in criteria:
                        flat_dict["patch_management_enabled"] = criteria["is_installed"]
                    if criteria.get("missing_patches"):
                        mp = criteria["missing_patches"]
                        if "check" in mp:
                            flat_dict["patch_management_missing_patches"] = mp["check"]
                        if "severity" in mp:
                            flat_dict["patch_management_severity"] = mp["severity"]
                        if "patches" in mp:
                            flat_dict["patch_management_patches"] = mp["patches"]
                if pm_data.get("vendor"):
                    flat_dict["patch_management_vendors"] = pm_data["vendor"]

            # Handle disk encryption
            if hip_dict.get("disk_encryption"):
                de_data = hip_dict["disk_encryption"]
                if de_data.get("criteria"):
                    criteria = de_data["criteria"]
                    if "is_installed" in criteria:
                        flat_dict["disk_encryption_enabled"] = criteria["is_installed"]
                    if "encrypted_locations" in criteria:
                        flat_dict["disk_encryption_locations"] = criteria["encrypted_locations"]
                if de_data.get("vendor"):
                    flat_dict["disk_encryption_vendors"] = de_data["vendor"]

            # Handle mobile device
            if hip_dict.get("mobile_device") and hip_dict["mobile_device"].get("criteria"):
                criteria = hip_dict["mobile_device"]["criteria"]
                if "jailbroken" in criteria:
                    flat_dict["mobile_device_jailbroken"] = criteria["jailbroken"]
                if "disk_encrypted" in criteria:
                    flat_dict["mobile_device_disk_encrypted"] = criteria["disk_encrypted"]
                if "passcode_set" in criteria:
                    flat_dict["mobile_device_passcode_set"] = criteria["passcode_set"]
                if criteria.get("last_checkin_time"):
                    lct = criteria["last_checkin_time"]
                    if "days" in lct:
                        flat_dict["mobile_device_last_checkin_time"] = "days"
                        flat_dict["mobile_device_last_checkin_value"] = lct["days"]
                    elif "hours" in lct:
                        flat_dict["mobile_device_last_checkin_time"] = "hours"
                        flat_dict["mobile_device_last_checkin_value"] = lct["hours"]
                if criteria.get("applications"):
                    apps = criteria["applications"]
                    if "has_malware" in apps:
                        flat_dict["mobile_device_has_malware"] = apps["has_malware"]
                    if "has_unmanaged_app" in apps:
                        flat_dict["mobile_device_has_unmanaged_app"] = apps["has_unmanaged_app"]
                    if "includes" in apps:
                        flat_dict["mobile_device_applications"] = apps["includes"]

            # Handle certificate
            if hip_dict.get("certificate") and hip_dict["certificate"].get("criteria"):
                criteria = hip_dict["certificate"]["criteria"]
                if "certificate_profile" in criteria:
                    flat_dict["certificate_profile"] = criteria["certificate_profile"]
                if "certificate_attributes" in criteria:
                    flat_dict["certificate_attributes"] = criteria["certificate_attributes"]

            backup_data.append(flat_dict)

        # Create the YAML structure
        yaml_data = {"hip_objects": backup_data}

        # Generate filename
        filename = f"hip-object-{folder.lower()}.yaml"

        # Write to YAML file
        with open(filename, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data)} HIP objects to {filename}")
        return filename

    except Exception as e:
        typer.echo(f"Error backing up HIP objects: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("hip-object")
def delete_hip_object(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
):
    """Delete a HIP object.

    Example:
    -------
    scm-cli delete objects hip-object --folder Texas --name windows-compliance

    """
    try:
        result = scm_client.delete_hip_object(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted HIP object: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting HIP object: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("hip-object")
def load_hip_object(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load HIP objects from a YAML file.

    Example:
    -------
    scm-cli load objects hip-object --file config/hip_objects.yml

    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(str(file), "hip_objects")

        if dry_run:
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["hip_objects"]))
            return

        # Apply each HIP object
        results = []
        for hip_data in config["hip_objects"]:
            # Validate using the Pydantic model
            hip_obj = HIPObject(**hip_data)

            # Convert to SDK model format
            sdk_data = hip_obj.to_sdk_model()

            # Call the SDK client to create the HIP object
            result = scm_client.create_hip_object(
                folder=hip_obj.folder,
                name=hip_obj.name,
                description=sdk_data.get("description"),
                host_info=sdk_data.get("host_info"),
                network_info=sdk_data.get("network_info"),
                patch_management=sdk_data.get("patch_management"),
                disk_encryption=sdk_data.get("disk_encryption"),
                mobile_device=sdk_data.get("mobile_device"),
                certificate=sdk_data.get("certificate"),
            )

            results.append(result)
            typer.echo(f"Applied HIP object: {result['name']} in folder {result['folder']}")

        return results
    except Exception as e:
        typer.echo(f"Error loading HIP objects: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("hip-object")
def set_hip_object(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    description: str = typer.Option("", help="Description of the HIP object"),
    # Host info options
    host_info_domain: str = typer.Option(None, help="Domain criteria (is, is_not, contains)"),
    host_info_domain_value: str = typer.Option(None, help="Domain value to match"),
    host_info_os: str = typer.Option(None, help="OS vendor (Microsoft, Apple, Google, Linux, Other)"),
    host_info_os_value: str = typer.Option(None, help="OS value (All or specific version)"),
    host_info_managed: bool = typer.Option(None, help="Managed state criteria"),
    # Network info options
    network_info_type: str = typer.Option(None, help="Network type (is, is_not)"),
    network_info_value: str = typer.Option(None, help="Network value (wifi, mobile, ethernet, unknown)"),
    # Patch management options
    patch_management_enabled: bool = typer.Option(None, help="Whether patch management is enabled"),
    patch_management_missing_patches: str = typer.Option(None, help="Missing patches check (has-any, has-none, has-all)"),
    patch_management_severity: int = typer.Option(None, help="Patch severity level"),
    # Disk encryption options
    disk_encryption_enabled: bool = typer.Option(None, help="Whether disk encryption is enabled"),
    # Mobile device options
    mobile_device_jailbroken: bool = typer.Option(None, help="Jailbroken status"),
    mobile_device_disk_encrypted: bool = typer.Option(None, help="Disk encryption status"),
    mobile_device_passcode_set: bool = typer.Option(None, help="Passcode status"),
    # Certificate options
    certificate_profile: str = typer.Option(None, help="Certificate profile name"),
):
    """Create or update a HIP object.

    Example:
    -------
        # Create a Windows workstation compliance policy
        scm-cli set objects hip-object \\
        --folder Texas \\
        --name windows-compliance \\
        --description "Windows workstation compliance" \\
        --host-info-os Microsoft \\
        --host-info-os-value All \\
        --host-info-managed \\
        --disk-encryption-enabled \\
        --patch-management-enabled

        # Create a mobile device policy
        scm-cli set objects hip-object \\
        --folder Texas \\
        --name mobile-policy \\
        --description "Mobile device compliance" \\
        --mobile-device-jailbroken false \\
        --mobile-device-disk-encrypted \\
        --mobile-device-passcode-set

        # Create a network-based policy
        scm-cli set objects hip-object \\
        --folder Texas \\
        --name wifi-only \\
        --description "WiFi network only" \\
        --network-info-type is \\
        --network-info-value wifi

    """
    try:
        # Build the HIP object data from options
        hip_data = {
            "folder": folder,
            "name": name,
            "description": description,
        }

        # Add host info options if provided
        if host_info_domain:
            hip_data["host_info_domain"] = host_info_domain
            hip_data["host_info_domain_value"] = host_info_domain_value
        if host_info_os:
            hip_data["host_info_os"] = host_info_os
            hip_data["host_info_os_value"] = host_info_os_value
        if host_info_managed is not None:
            hip_data["host_info_managed"] = host_info_managed

        # Add network info options if provided
        if network_info_type:
            hip_data["network_info_type"] = network_info_type
            hip_data["network_info_value"] = network_info_value

        # Add patch management options if provided
        if patch_management_enabled is not None:
            hip_data["patch_management_enabled"] = patch_management_enabled
        if patch_management_missing_patches:
            hip_data["patch_management_missing_patches"] = patch_management_missing_patches
        if patch_management_severity is not None:
            hip_data["patch_management_severity"] = patch_management_severity

        # Add disk encryption options if provided
        if disk_encryption_enabled is not None:
            hip_data["disk_encryption_enabled"] = disk_encryption_enabled

        # Add mobile device options if provided
        if mobile_device_jailbroken is not None:
            hip_data["mobile_device_jailbroken"] = mobile_device_jailbroken
        if mobile_device_disk_encrypted is not None:
            hip_data["mobile_device_disk_encrypted"] = mobile_device_disk_encrypted
        if mobile_device_passcode_set is not None:
            hip_data["mobile_device_passcode_set"] = mobile_device_passcode_set

        # Add certificate options if provided
        if certificate_profile:
            hip_data["certificate_profile"] = certificate_profile

        # Validate using the Pydantic model
        hip_obj = HIPObject(**hip_data)

        # Convert to SDK model format
        sdk_data = hip_obj.to_sdk_model()

        # Call the SDK client to create the HIP object
        result = scm_client.create_hip_object(
            folder=hip_obj.folder,
            name=hip_obj.name,
            description=sdk_data.get("description"),
            host_info=sdk_data.get("host_info"),
            network_info=sdk_data.get("network_info"),
            patch_management=sdk_data.get("patch_management"),
            disk_encryption=sdk_data.get("disk_encryption"),
            mobile_device=sdk_data.get("mobile_device"),
            certificate=sdk_data.get("certificate"),
        )

        typer.echo(f"Created HIP object: {result['name']} in folder {result['folder']}")
        return result
    except Exception as e:
        typer.echo(f"Error creating HIP object: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("hip-object")
def show_hip_object(
    folder: str = FOLDER_OPTION,
    name: str = typer.Option(None, help="Name of the HIP object to show"),
    list_objects: bool = typer.Option(False, "--list", help="List all HIP objects in the folder"),
):
    """Display HIP object configurations.

    Example:
    -------
        # List all HIP objects in a folder
        scm-cli show objects hip-object --folder Texas --list

        # Show a specific HIP object by name
        scm-cli show objects hip-object --folder Texas --name windows-compliance

    """
    try:
        if list_objects:
            # List all HIP objects in the folder
            hip_objects = scm_client.list_hip_objects(folder=folder)

            if not hip_objects:
                typer.echo(f"No HIP objects found in folder '{folder}'")
                return

            typer.echo(f"HIP Objects in folder '{folder}':")
            typer.echo("-" * 60)

            for hip_obj in hip_objects:
                # Display HIP object information
                typer.echo(f"Name: {hip_obj.get('name', 'N/A')}")

                # Display container location (folder, snippet, or device)
                if hip_obj.get("folder"):
                    typer.echo(f"  Location: Folder '{hip_obj['folder']}'")
                elif hip_obj.get("snippet"):
                    typer.echo(f"  Location: Snippet '{hip_obj['snippet']}'")
                elif hip_obj.get("device"):
                    typer.echo(f"  Location: Device '{hip_obj['device']}'")
                else:
                    typer.echo("  Location: N/A")

                typer.echo(f"  Description: {hip_obj.get('description', 'N/A')}")

                # Display criteria types
                criteria_types = []
                if hip_obj.get("host_info"):
                    criteria_types.append("Host Info")
                if hip_obj.get("network_info"):
                    criteria_types.append("Network Info")
                if hip_obj.get("patch_management"):
                    criteria_types.append("Patch Management")
                if hip_obj.get("disk_encryption"):
                    criteria_types.append("Disk Encryption")
                if hip_obj.get("mobile_device"):
                    criteria_types.append("Mobile Device")
                if hip_obj.get("certificate"):
                    criteria_types.append("Certificate")

                if criteria_types:
                    typer.echo(f"  Criteria Types: {', '.join(criteria_types)}")

                typer.echo("-" * 60)

            return hip_objects

        elif name:
            # Get a specific HIP object by name
            hip_obj = scm_client.get_hip_object(folder=folder, name=name)

            typer.echo(f"HIP Object: {hip_obj.get('name', 'N/A')}")

            # Display container location (folder, snippet, or device)
            if hip_obj.get("folder"):
                typer.echo(f"Location: Folder '{hip_obj['folder']}'")
            elif hip_obj.get("snippet"):
                typer.echo(f"Location: Snippet '{hip_obj['snippet']}'")
            elif hip_obj.get("device"):
                typer.echo(f"Location: Device '{hip_obj['device']}'")
            else:
                typer.echo("Location: N/A")

            typer.echo(f"Description: {hip_obj.get('description', 'N/A')}")

            # Display host info criteria
            if hip_obj.get("host_info") and hip_obj["host_info"].get("criteria"):
                typer.echo("\nHost Information Criteria:")
                criteria = hip_obj["host_info"]["criteria"]
                
                if criteria.get("domain"):
                    domain_val = criteria["domain"]
                    for key, value in domain_val.items():
                        typer.echo(f"  Domain {key}: {value}")
                
                if criteria.get("os") and criteria["os"].get("contains"):
                    os_data = criteria["os"]["contains"]
                    for vendor, value in os_data.items():
                        typer.echo(f"  OS: {vendor} - {value}")
                
                if "managed" in criteria:
                    typer.echo(f"  Managed: {criteria['managed']}")
                
                for field in ["client_version", "host_name", "host_id", "serial_number"]:
                    if criteria.get(field):
                        field_val = criteria[field]
                        for key, value in field_val.items():
                            typer.echo(f"  {field.replace('_', ' ').title()} {key}: {value}")

            # Display network info criteria
            if hip_obj.get("network_info") and hip_obj["network_info"].get("criteria"):
                typer.echo("\nNetwork Information Criteria:")
                criteria = hip_obj["network_info"]["criteria"]
                if criteria.get("network"):
                    network_val = criteria["network"]
                    for op, value in network_val.items():
                        network_type = list(value.keys())[0]
                        typer.echo(f"  Network {op}: {network_type}")

            # Display patch management criteria
            if hip_obj.get("patch_management"):
                typer.echo("\nPatch Management Criteria:")
                pm_data = hip_obj["patch_management"]
                if pm_data.get("criteria"):
                    criteria = pm_data["criteria"]
                    if "is_installed" in criteria:
                        typer.echo(f"  Is Installed: {criteria['is_installed']}")
                    if criteria.get("missing_patches"):
                        mp = criteria["missing_patches"]
                        typer.echo(f"  Missing Patches Check: {mp.get('check', 'N/A')}")
                        if "severity" in mp:
                            typer.echo(f"  Severity Threshold: {mp['severity']}")
                        if "patches" in mp:
                            typer.echo(f"  Specific Patches: {', '.join(mp['patches'])}")
                if pm_data.get("vendor"):
                    typer.echo("  Vendors:")
                    for vendor in pm_data["vendor"]:
                        typer.echo(f"    - {vendor.get('name', 'N/A')}: {', '.join(vendor.get('product', []))}")

            # Display disk encryption criteria
            if hip_obj.get("disk_encryption"):
                typer.echo("\nDisk Encryption Criteria:")
                de_data = hip_obj["disk_encryption"]
                if de_data.get("criteria"):
                    criteria = de_data["criteria"]
                    if "is_installed" in criteria:
                        typer.echo(f"  Is Installed: {criteria['is_installed']}")
                    if criteria.get("encrypted_locations"):
                        typer.echo("  Encrypted Locations:")
                        for loc in criteria["encrypted_locations"]:
                            state = loc.get("encryption_state", {})
                            state_str = "N/A"
                            if "is" in state:
                                state_str = f"is {state['is']}"
                            elif "is_not" in state:
                                state_str = f"is not {state['is_not']}"
                            typer.echo(f"    - {loc.get('name', 'N/A')}: {state_str}")
                if de_data.get("vendor"):
                    typer.echo("  Vendors:")
                    for vendor in de_data["vendor"]:
                        typer.echo(f"    - {vendor.get('name', 'N/A')}: {', '.join(vendor.get('product', []))}")

            # Display mobile device criteria
            if hip_obj.get("mobile_device") and hip_obj["mobile_device"].get("criteria"):
                typer.echo("\nMobile Device Criteria:")
                criteria = hip_obj["mobile_device"]["criteria"]
                
                if "jailbroken" in criteria:
                    typer.echo(f"  Jailbroken: {criteria['jailbroken']}")
                if "disk_encrypted" in criteria:
                    typer.echo(f"  Disk Encrypted: {criteria['disk_encrypted']}")
                if "passcode_set" in criteria:
                    typer.echo(f"  Passcode Set: {criteria['passcode_set']}")
                
                if criteria.get("last_checkin_time"):
                    lct = criteria["last_checkin_time"]
                    for unit, value in lct.items():
                        typer.echo(f"  Last Check-in Time: {value} {unit}")
                
                if criteria.get("applications"):
                    apps = criteria["applications"]
                    if "has_malware" in apps:
                        typer.echo(f"  Has Malware: {apps['has_malware']}")
                    if "has_unmanaged_app" in apps:
                        typer.echo(f"  Has Unmanaged App: {apps['has_unmanaged_app']}")
                    if apps.get("includes"):
                        typer.echo("  Required Applications:")
                        for app in apps["includes"]:
                            typer.echo(f"    - {app.get('name', 'N/A')}")
                            if app.get("package"):
                                typer.echo(f"      Package: {app['package']}")
                            if app.get("hash"):
                                typer.echo(f"      Hash: {app['hash']}")

            # Display certificate criteria
            if hip_obj.get("certificate") and hip_obj["certificate"].get("criteria"):
                typer.echo("\nCertificate Criteria:")
                criteria = hip_obj["certificate"]["criteria"]
                
                if criteria.get("certificate_profile"):
                    typer.echo(f"  Certificate Profile: {criteria['certificate_profile']}")
                
                if criteria.get("certificate_attributes"):
                    typer.echo("  Certificate Attributes:")
                    for attr in criteria["certificate_attributes"]:
                        typer.echo(f"    - {attr.get('name', 'N/A')}: {attr.get('value', 'N/A')}")

            # Display ID if present
            if hip_obj.get("id"):
                typer.echo(f"\nID: {hip_obj['id']}")

            return hip_obj

        else:
            # Neither --list nor --name was provided
            typer.echo("Error: Either --list or --name must be specified", err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"Error showing HIP object: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# HIP PROFILE COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("hip-profile")
def backup_hip_profile(
    folder: str = typer.Option(..., "--folder", help="Folder to backup HIP profiles from"),
    output_file: str = typer.Option(None, "--output", help="Output file name (defaults to hip-profile-{folder}.yaml)"),
) -> None:
    """Backup HIP profiles from a specific folder to a YAML file."""
    try:
        # Get all HIP profiles from the folder
        typer.echo(f"Fetching HIP profiles from folder '{folder}'...")
        hip_profiles = scm_client.list_hip_profiles(folder=folder, exact_match=True)

        if not hip_profiles:
            typer.echo(f"No HIP profiles found in folder '{folder}'")
            return

        # Prepare the data for YAML export
        backup_data = {"hip_profiles": []}

        for profile in hip_profiles:
            # Create a clean dict with only the fields we want to export
            profile_data = {
                "name": profile["name"],
                "folder": profile["folder"],
                "match": profile["match"],
            }

            # Add optional fields if present
            if profile.get("description"):
                profile_data["description"] = profile["description"]

            backup_data["hip_profiles"].append(profile_data)

        # Sort HIP profiles by name for consistent output
        backup_data["hip_profiles"].sort(key=lambda x: x["name"])

        # Determine output file name
        if not output_file:
            output_file = f"hip-profile-{folder.lower().replace('/', '-').replace(' ', '-')}.yaml"

        # Write to YAML file
        with open(output_file, "w") as f:
            yaml.dump(backup_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(hip_profiles)} HIP profiles to {output_file}")

    except Exception as e:
        typer.echo(f"Error backing up HIP profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("hip-profile")
def delete_hip_profile(
    folder: str = typer.Option(..., "--folder", help="Folder containing the HIP profile"),
    name: str = typer.Option(..., "--name", help="Name of the HIP profile to delete"),
) -> None:
    """Delete a HIP profile from a specific folder."""
    try:
        # Delete the HIP profile
        typer.echo(f"Deleting HIP profile '{name}' from folder '{folder}'...")
        scm_client.delete_hip_profile(folder=folder, name=name)
        typer.echo(f"Successfully deleted HIP profile '{name}'")

    except Exception as e:
        typer.echo(f"Error deleting HIP profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("hip-profile")
def load_hip_profile(
    file: Path = typer.Option(..., "--file", help="YAML file containing HIP profiles"),
    folder: str = typer.Option(None, "--folder", help="Override folder path for all HIP profiles"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without applying them"),
) -> None:
    """Load HIP profiles from a YAML file."""
    try:
        # Load and validate YAML
        data = load_from_yaml(str(file), "hip_profiles")
        
        # Validate the data
        from ..utils.validators import validate_yaml_file
        profiles = validate_yaml_file(data, HIPProfile, "hip_profiles")

        # Process each HIP profile
        created_count = 0
        updated_count = 0

        for profile in profiles:
            # Override folder if specified
            if folder:
                profile.folder = folder

            # Convert to SDK model format
            profile_data = profile.to_sdk_model()

            if dry_run:
                typer.echo(f"[DRY RUN] Would create/update HIP profile: {profile.name}")
                typer.echo(f"  Folder: {profile.folder}")
                typer.echo(f"  Match: {profile.match}")
                if profile.description:
                    typer.echo(f"  Description: {profile.description}")
            else:
                # Check if profile exists
                try:
                    existing = scm_client.get_hip_profile(folder=profile.folder, name=profile.name)
                    # Update existing
                    result = scm_client.create_hip_profile(
                        folder=profile_data["folder"],
                        name=profile_data["name"],
                        match=profile_data["match"],
                        description=profile_data.get("description"),
                    )
                    updated_count += 1
                    typer.echo(f"Updated HIP profile: {profile.name}")
                except Exception:
                    # Create new
                    result = scm_client.create_hip_profile(
                        folder=profile_data["folder"],
                        name=profile_data["name"],
                        match=profile_data["match"],
                        description=profile_data.get("description"),
                    )
                    created_count += 1
                    typer.echo(f"Created HIP profile: {profile.name}")

        # Summary
        typer.echo(f"\nSummary: Created {created_count}, Updated {updated_count} HIP profiles")

    except ValueError as e:
        typer.echo(f"Validation error: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading HIP profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("hip-profile")
def set_hip_profile(
    folder: str = typer.Option(..., "--folder", help="Folder path for the HIP profile"),
    name: str = typer.Option(..., "--name", help="Name of the HIP profile"),
    match: str = typer.Option(..., "--match", help="Match criteria for the HIP profile"),
    description: str = typer.Option(None, "--description", help="Description of the HIP profile"),
) -> None:
    """Create or update a HIP profile."""
    try:
        # Create the HIP profile object
        hip_profile = HIPProfile(
            folder=folder,
            name=name,
            match=match,
            description=description,
        )

        # Convert to SDK model format
        profile_data = hip_profile.to_sdk_model()

        # Create or update the HIP profile
        result = scm_client.create_hip_profile(
            folder=profile_data["folder"],
            name=profile_data["name"],
            match=profile_data["match"],
            description=profile_data.get("description"),
        )

        # Display result
        typer.echo(f"Successfully created/updated HIP profile: {result['name']}")
        typer.echo(f"ID: {result['id']}")
        typer.echo(f"Folder: {result['folder']}")
        typer.echo(f"Match: {result['match']}")
        if result.get("description"):
            typer.echo(f"Description: {result['description']}")

    except Exception as e:
        typer.echo(f"Error creating/updating HIP profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("hip-profile")
def show_hip_profile(
    folder: str = typer.Option(..., "--folder", help="Folder path for the HIP profile"),
    name: str = typer.Option(None, "--name", help="Name of specific HIP profile to show"),
    list: bool = typer.Option(False, "--list", help="List all HIP profiles in the folder"),
) -> dict[str, Any] | None:
    """Show HIP profile details or list all HIP profiles in a folder."""
    try:
        if list:
            # List all HIP profiles in the folder
            hip_profiles = scm_client.list_hip_profiles(folder=folder)
            if not hip_profiles:
                typer.echo(f"No HIP profiles found in folder '{folder}'")
                return None

            typer.echo(f"HIP profiles in folder '{folder}':")
            typer.echo("-" * 80)

            # Display in table format
            for profile in hip_profiles:
                typer.echo(f"Name: {profile['name']}")
                typer.echo(f"  Match: {profile['match']}")
                if profile.get("description"):
                    typer.echo(f"  Description: {profile['description']}")
                typer.echo("")

            typer.echo(f"Total: {len(hip_profiles)} HIP profiles")
            return None

        elif name:
            # Show specific HIP profile
            hip_profile = scm_client.get_hip_profile(folder=folder, name=name)

            typer.echo(f"HIP Profile: {hip_profile['name']}")
            typer.echo("-" * 80)
            typer.echo(f"Folder: {hip_profile['folder']}")
            typer.echo(f"Match: {hip_profile['match']}")

            if hip_profile.get("description"):
                typer.echo(f"Description: {hip_profile['description']}")

            # Display ID if present
            if hip_profile.get("id"):
                typer.echo(f"\nID: {hip_profile['id']}")

            return hip_profile

        else:
            # Neither --list nor --name was provided
            typer.echo("Error: Either --list or --name must be specified", err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"Error showing HIP profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ========================================================================================================================================================================================
# HTTP SERVER PROFILE COMMANDS
# ========================================================================================================================================================================================


@backup_app.command("http-server-profile")
def backup_http_server_profile(
    folder: str = typer.Option(..., "--folder", help="Folder to backup HTTP server profiles from"),
    output_file: str = typer.Option(None, "--output", help="Output file name (defaults to http-server-profile-{folder}.yaml)"),
) -> None:
    """Backup HTTP server profiles from a specific folder to a YAML file."""
    try:
        # Get all HTTP server profiles from the folder
        typer.echo(f"Fetching HTTP server profiles from folder '{folder}'...")
        http_server_profiles = scm_client.list_http_server_profiles(folder=folder, exact_match=True)

        if not http_server_profiles:
            typer.echo(f"No HTTP server profiles found in folder '{folder}'")
            return

        # Prepare the data for YAML export
        backup_data = {"http_server_profiles": []}

        for profile in http_server_profiles:
            # Create a clean dict with only the fields we want to export
            profile_data = {
                "name": profile["name"],
                "folder": profile["folder"],
                "servers": profile["server"],  # Note: API uses 'server' but we'll use 'servers' in YAML
            }

            # Add optional fields if present
            if profile.get("description"):
                profile_data["description"] = profile["description"]
            
            if profile.get("tag_registration"):
                profile_data["tag_registration"] = profile["tag_registration"]
                
            if profile.get("format"):
                profile_data["format_config"] = profile["format"]

            backup_data["http_server_profiles"].append(profile_data)

        # Sort HTTP server profiles by name for consistent output
        backup_data["http_server_profiles"].sort(key=lambda x: x["name"])

        # Determine output file name
        if not output_file:
            output_file = f"http-server-profile-{folder.lower().replace('/', '-').replace(' ', '-')}.yaml"

        # Write to YAML file
        with open(output_file, "w") as f:
            yaml.dump(backup_data, f, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(http_server_profiles)} HTTP server profiles to {output_file}")

    except Exception as e:
        typer.echo(f"Error backing up HTTP server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("http-server-profile")
def delete_http_server_profile(
    folder: str = typer.Option(..., "--folder", help="Folder containing the HTTP server profile"),
    name: str = typer.Option(..., "--name", help="Name of the HTTP server profile to delete"),
) -> None:
    """Delete an HTTP server profile from a specific folder."""
    try:
        # Delete the HTTP server profile
        typer.echo(f"Deleting HTTP server profile '{name}' from folder '{folder}'...")
        scm_client.delete_http_server_profile(folder=folder, name=name)
        typer.echo(f"Successfully deleted HTTP server profile '{name}'")

    except Exception as e:
        typer.echo(f"Error deleting HTTP server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("http-server-profile")
def load_http_server_profile(
    file: Path = typer.Option(..., "--file", help="YAML file containing HTTP server profiles"),
    folder: str = typer.Option(None, "--folder", help="Override folder path for all HTTP server profiles"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without applying them"),
) -> None:
    """Load HTTP server profiles from a YAML file."""
    try:
        # Load and validate YAML
        data = load_from_yaml(str(file), "http_server_profiles")
        
        # Validate the data
        from ..utils.validators import validate_yaml_file
        profiles = validate_yaml_file(data, HTTPServerProfile, "http_server_profiles")

        # Process each HTTP server profile
        created_count = 0
        updated_count = 0

        for profile in profiles:
            # Override folder if specified
            if folder:
                profile.folder = folder

            # Convert to SDK model format
            profile_data = profile.to_sdk_model()

            if dry_run:
                typer.echo(f"[DRY RUN] Would create/update HTTP server profile: {profile.name}")
                typer.echo(f"  Folder: {profile.folder}")
                typer.echo(f"  Servers: {len(profile.servers)}")
                for idx, server in enumerate(profile.servers):
                    typer.echo(f"    Server {idx + 1}: {server.get('name', 'unnamed')} - {server.get('address', 'N/A')}:{server.get('port', 'N/A')} ({server.get('protocol', 'N/A')})")
                if profile.description:
                    typer.echo(f"  Description: {profile.description}")
                if profile.tag_registration:
                    typer.echo(f"  Tag Registration: {profile.tag_registration}")
            else:
                # Check if profile exists
                try:
                    existing = scm_client.get_http_server_profile(folder=profile.folder, name=profile.name)
                    # Update existing
                    result = scm_client.create_http_server_profile(
                        folder=profile_data["folder"],
                        name=profile_data["name"],
                        servers=profile_data["server"],
                        description=profile_data.get("description"),
                        tag_registration=profile_data.get("tag_registration", False),
                        format_config=profile_data.get("format"),
                    )
                    updated_count += 1
                    typer.echo(f"Updated HTTP server profile: {profile.name}")
                except Exception:
                    # Create new
                    result = scm_client.create_http_server_profile(
                        folder=profile_data["folder"],
                        name=profile_data["name"],
                        servers=profile_data["server"],
                        description=profile_data.get("description"),
                        tag_registration=profile_data.get("tag_registration", False),
                        format_config=profile_data.get("format"),
                    )
                    created_count += 1
                    typer.echo(f"Created HTTP server profile: {profile.name}")

        # Summary
        typer.echo(f"\nSummary: Created {created_count}, Updated {updated_count} HTTP server profiles")

    except ValueError as e:
        typer.echo(f"Validation error: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading HTTP server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("http-server-profile")
def set_http_server_profile(
    folder: str = typer.Option(..., "--folder", help="Folder path for the HTTP server profile"),
    name: str = typer.Option(..., "--name", help="Name of the HTTP server profile"),
    servers: str = typer.Option(..., "--servers", help="JSON string of server configurations"),
    description: str = typer.Option(None, "--description", help="Description of the HTTP server profile"),
    tag_registration: bool = typer.Option(False, "--tag-registration", help="Register tags on match"),
) -> None:
    """Create or update an HTTP server profile.
    
    Server configuration must be provided as a JSON string, e.g.:
    --servers '[{"name": "server1", "address": "192.168.1.100", "protocol": "HTTPS", "port": 443}]'
    """
    try:
        # Parse servers JSON
        import json as json_lib
        try:
            servers_list = json_lib.loads(servers)
            if not isinstance(servers_list, list):
                raise ValueError("Servers must be a JSON array")
        except json_lib.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON for servers: {e}")

        # Create the HTTP server profile object
        http_server_profile = HTTPServerProfile(
            folder=folder,
            name=name,
            servers=servers_list,
            description=description,
            tag_registration=tag_registration,
        )

        # Convert to SDK model format
        profile_data = http_server_profile.to_sdk_model()

        # Create or update the HTTP server profile
        result = scm_client.create_http_server_profile(
            folder=profile_data["folder"],
            name=profile_data["name"],
            servers=profile_data["server"],
            description=profile_data.get("description"),
            tag_registration=profile_data.get("tag_registration", False),
            format_config=profile_data.get("format"),
        )

        # Display result
        typer.echo(f"Successfully created/updated HTTP server profile: {result['name']}")
        typer.echo(f"ID: {result['id']}")
        typer.echo(f"Folder: {result['folder']}")
        typer.echo(f"Servers: {len(result['server'])}")
        for idx, server in enumerate(result['server']):
            typer.echo(f"  Server {idx + 1}: {server.get('name', 'unnamed')} - {server.get('address', 'N/A')}:{server.get('port', 'N/A')} ({server.get('protocol', 'N/A')})")
        if result.get("description"):
            typer.echo(f"Description: {result['description']}")
        if result.get("tag_registration"):
            typer.echo(f"Tag Registration: {result['tag_registration']}")

    except ValueError as e:
        typer.echo(f"Validation error: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating HTTP server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("http-server-profile")
def show_http_server_profile(
    folder: str = typer.Option(..., "--folder", help="Folder path for the HTTP server profile"),
    name: str = typer.Option(None, "--name", help="Name of specific HTTP server profile to show"),
    list: bool = typer.Option(False, "--list", help="List all HTTP server profiles in the folder"),
) -> dict[str, Any] | None:
    """Show HTTP server profile details or list all HTTP server profiles in a folder."""
    try:
        if list:
            # List all HTTP server profiles in the folder
            http_server_profiles = scm_client.list_http_server_profiles(folder=folder)
            if not http_server_profiles:
                typer.echo(f"No HTTP server profiles found in folder '{folder}'")
                return None

            typer.echo(f"HTTP server profiles in folder '{folder}':")
            typer.echo("-" * 80)

            # Display in table format
            for profile in http_server_profiles:
                typer.echo(f"Name: {profile['name']}")
                if profile.get("description"):
                    typer.echo(f"  Description: {profile['description']}")
                typer.echo(f"  Tag Registration: {profile.get('tag_registration', False)}")
                typer.echo(f"  Servers: {len(profile.get('server', []))}")
                for idx, server in enumerate(profile.get('server', [])):
                    typer.echo(f"    Server {idx + 1}: {server.get('name', 'unnamed')} - {server.get('address', 'N/A')}:{server.get('port', 'N/A')} ({server.get('protocol', 'N/A')})")
                typer.echo("")

            typer.echo(f"Total: {len(http_server_profiles)} HTTP server profiles")
            return None

        elif name:
            # Show specific HTTP server profile
            http_server_profile = scm_client.get_http_server_profile(folder=folder, name=name)

            typer.echo(f"HTTP Server Profile: {http_server_profile['name']}")
            typer.echo("-" * 80)
            typer.echo(f"Folder: {http_server_profile['folder']}")
            
            if http_server_profile.get("description"):
                typer.echo(f"Description: {http_server_profile['description']}")
                
            typer.echo(f"Tag Registration: {http_server_profile.get('tag_registration', False)}")
            
            # Display servers
            typer.echo(f"\nServers ({len(http_server_profile.get('server', []))}):")
            for idx, server in enumerate(http_server_profile.get('server', [])):
                typer.echo(f"  Server {idx + 1}: {server.get('name', 'unnamed')}")
                typer.echo(f"    Address: {server.get('address', 'N/A')}")
                typer.echo(f"    Protocol: {server.get('protocol', 'N/A')}")
                typer.echo(f"    Port: {server.get('port', 'N/A')}")
                if server.get('protocol') == 'HTTPS' and server.get('tls_version'):
                    typer.echo(f"    TLS Version: {server.get('tls_version')}")
                if server.get('certificate_profile'):
                    typer.echo(f"    Certificate Profile: {server.get('certificate_profile')}")
                if server.get('http_method'):
                    typer.echo(f"    HTTP Method: {server.get('http_method')}")
                if server.get('username'):
                    typer.echo(f"    Username: {server.get('username')}")
                    typer.echo(f"    Password: {'*' * 8}")  # Hide password
            
            # Display format configuration if present
            if http_server_profile.get('format'):
                typer.echo(f"\nFormat Configuration:")
                for log_type, format_config in http_server_profile['format'].items():
                    typer.echo(f"  {log_type}:")
                    if isinstance(format_config, dict):
                        if format_config.get('name'):
                            typer.echo(f"    Name: {format_config['name']}")
                        if format_config.get('url_format'):
                            typer.echo(f"    URL Format: {format_config['url_format']}")
                        if format_config.get('headers'):
                            typer.echo(f"    Headers: {len(format_config['headers'])} configured")
                        if format_config.get('params'):
                            typer.echo(f"    Parameters: {len(format_config['params'])} configured")

            # Display ID if present
            if http_server_profile.get("id"):
                typer.echo(f"\nID: {http_server_profile['id']}")

            return http_server_profile

        else:
            # Neither --list nor --name was provided
            typer.echo("Error: Either --list or --name must be specified", err=True)
            raise typer.Exit(code=1)

    except Exception as e:
        typer.echo(f"Error showing HTTP server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
