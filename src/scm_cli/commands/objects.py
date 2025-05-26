"""Objects module commands for scm-cli.

This module implements set, delete, and load commands for objects-related
configurations such as address-group, address, service-group, etc.
"""

from pathlib import Path

import typer
import yaml

from ..utils.config import load_from_yaml
from ..utils.sdk_client import scm_client
from ..utils.validators import Address, AddressGroup, Application

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
