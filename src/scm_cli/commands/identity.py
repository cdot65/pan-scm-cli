"""Identity module commands for scm.

This module implements set, show, delete, load, and backup commands for identity-related
configurations such as authentication profiles, Kerberos server profiles, LDAP server profiles,
RADIUS server profiles, SAML server profiles, and TACACS+ server profiles.
"""

import json as json_lib
from pathlib import Path
from typing import Any

import typer
import yaml
from pydantic import ValidationError

from ..utils.sdk_client import scm_client
from ..utils.validators import (
    AuthenticationProfile,
    KerberosServerProfile,
    LdapServerProfile,
    RadiusServerProfile,
    SamlServerProfile,
    TacacsServerProfile,
)

# ==============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# ==============================================================================================================================================================================================

set_app = typer.Typer(help="Create or update identity configurations")
delete_app = typer.Typer(help="Remove identity configurations")
load_app = typer.Typer(help="Load identity configurations from YAML files")
show_app = typer.Typer(help="Display identity configurations")
backup_app = typer.Typer(help="Backup identity configurations to YAML files")

# ==============================================================================================================================================================================================
# COMMAND OPTIONS
# ==============================================================================================================================================================================================

NAME_OPTION = typer.Option(..., "--name", help="Name of the resource")
DESCRIPTION_OPTION = typer.Option(None, "--description", help="Description of the resource")
FOLDER_OPTION = typer.Option(None, "--folder", help="Folder to scope the resource to")
SNIPPET_OPTION = typer.Option(None, "--snippet", help="Snippet to scope the resource to")
DEVICE_OPTION = typer.Option(None, "--device", help="Device to scope the resource to")
FILE_OPTION = typer.Option(..., "--file", help="YAML file to load configurations from")
DRY_RUN_OPTION = typer.Option(False, "--dry-run", help="Simulate execution without applying changes")

# Backup options
BACKUP_FOLDER_OPTION = typer.Option(None, "--folder", help="Folder to backup configurations from")
BACKUP_SNIPPET_OPTION = typer.Option(None, "--snippet", help="Snippet to backup configurations from")
BACKUP_DEVICE_OPTION = typer.Option(None, "--device", help="Device to backup configurations from")
BACKUP_FILE_OPTION = typer.Option(None, "--file", help="Output file path (optional, defaults to {type}-{location}.yaml)")

# Load container override options
LOAD_FOLDER_OPTION = typer.Option(None, "--folder", help="Override folder location for all objects")
LOAD_SNIPPET_OPTION = typer.Option(None, "--snippet", help="Override snippet location for all objects")
LOAD_DEVICE_OPTION = typer.Option(None, "--device", help="Override device location for all objects")
ALLOW_LIST_OPTION = typer.Option(None, "--allow-list", help="Allow list entries")

# ==============================================================================================================================================================================================
# HELPER FUNCTIONS
# ==============================================================================================================================================================================================


def validate_location_params(folder: str | None = None, snippet: str | None = None, device: str | None = None) -> tuple[str, str]:
    """Validate that exactly one location parameter is provided.

    Returns:
        tuple: (location_type, location_value)

    """
    location_count = sum(1 for loc in [folder, snippet, device] if loc is not None)

    if location_count == 0:
        typer.echo("Error: One of --folder, --snippet, or --device must be specified", err=True)
        raise typer.Exit(code=1)
    elif location_count > 1:
        typer.echo("Error: Only one of --folder, --snippet, or --device can be specified", err=True)
        raise typer.Exit(code=1)

    if folder:
        return "folder", folder
    elif snippet:
        return "snippet", snippet
    else:
        assert device is not None
        return "device", device


def get_default_backup_filename(object_type: str, location_type: str, location_value: str) -> str:
    """Generate default backup filename based on object type and location."""
    safe_location = location_value.lower().replace("/", "-").replace(" ", "-")
    return f"{object_type}-{safe_location}.yaml"


# ==============================================================================================================================================================================================
# AUTHENTICATION PROFILE COMMANDS
# ==============================================================================================================================================================================================


@set_app.command("authentication-profile")
def set_authentication_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str = NAME_OPTION,
    method: str | None = typer.Option(None, "--method", help="Authentication method as JSON string"),
    user_domain: str | None = typer.Option(None, "--user-domain", help="User domain"),
    username_modifier: str | None = typer.Option(None, "--username-modifier", help="Username modifier pattern"),
    lockout: str | None = typer.Option(None, "--lockout", help="Lockout configuration as JSON string"),
    allow_list: list[str] | None = ALLOW_LIST_OPTION,
    multi_factor_auth: str | None = typer.Option(None, "--multi-factor-auth", help="Multi-factor auth config as JSON"),
    single_sign_on: str | None = typer.Option(None, "--single-sign-on", help="SSO config as JSON"),
):
    r"""Create or update an authentication profile.

    Examples
    --------
        scm set identity authentication-profile --folder Texas --name my-auth \\
            --method '{"ldap": {"server_profile": "corp-ldap", "login_attribute": "sAMAccountName"}}'

    """
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)

        # Parse JSON fields
        method_dict = json_lib.loads(method) if method else None
        lockout_dict = json_lib.loads(lockout) if lockout else None
        mfa_dict = json_lib.loads(multi_factor_auth) if multi_factor_auth else None
        sso_dict = json_lib.loads(single_sign_on) if single_sign_on else None

        profile = AuthenticationProfile(
            name=name,
            folder=folder,
            snippet=snippet,
            device=device,
            method=method_dict,
            user_domain=user_domain,
            username_modifier=username_modifier,
            lockout=lockout_dict,
            allow_list=allow_list or ["all"],
            multi_factor_auth=mfa_dict,
            single_sign_on=sso_dict,
        )

        sdk_data = profile.to_sdk_model()
        result = scm_client.create_authentication_profile(**sdk_data)

        action = result.get("__action__", "created")
        if action == "no_change":
            typer.echo(f"No changes detected for authentication profile: {name}")
        elif action == "updated":
            typer.echo(f"Updated authentication profile: {name} in {location_type} {location_value}")
        else:
            typer.echo(f"Created authentication profile: {name} in {location_type} {location_value}")
        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating authentication profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("authentication-profile")
def show_authentication_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the authentication profile to show"),
    list_items: bool = typer.Option(False, "--list", "-l", help="List all authentication profiles"),
):
    """Display authentication profiles.

    Examples
    --------
        scm show identity authentication-profile --folder Texas --list
        scm show identity authentication-profile --folder Texas --name my-auth

    """
    try:
        if name:
            location_type, location_value = validate_location_params(folder, snippet, device)
            profile = scm_client.get_authentication_profile(name=name, **{location_type: location_value})

            typer.echo(f"\nAuthentication Profile: {profile.get('name', 'N/A')}")
            typer.echo("=" * 80)
            if profile.get("user_domain"):
                typer.echo(f"User Domain: {profile['user_domain']}")
            if profile.get("method"):
                typer.echo(f"Method: {json_lib.dumps(profile['method'], indent=2)}")
            if profile.get("allow_list"):
                typer.echo(f"Allow List: {profile['allow_list']}")
            if profile.get("id"):
                typer.echo(f"ID: {profile['id']}")
        else:
            # List all authentication profiles (default behavior)
            profiles = scm_client.list_authentication_profiles(folder=folder, snippet=snippet, device=device)
            if not profiles:
                typer.echo("No authentication profiles found")
                return

            typer.echo(f"\nAuthentication Profiles ({len(profiles)}):")
            typer.echo("-" * 80)
            for p in profiles:
                typer.echo(f"Name: {p.get('name', 'N/A')}")
                if p.get("user_domain"):
                    typer.echo(f"  User Domain: {p['user_domain']}")
                if p.get("method"):
                    typer.echo(f"  Method: {list(p['method'].keys())}")
                typer.echo("-" * 80)

    except Exception as e:
        typer.echo(f"Error showing authentication profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("authentication-profile")
def delete_authentication_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete an authentication profile.

    Example: scm delete identity authentication-profile --folder Texas --name my-auth

    """
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if not force:
            typer.confirm(f"Delete authentication profile '{name}' from {location_type} '{location_value}'?", abort=True)
        result = scm_client.delete_authentication_profile(name=name, **{location_type: location_value})

        if result:
            typer.echo(f"Deleted authentication profile: {name} from {location_type} {location_value}")
        else:
            typer.echo(f"Authentication profile not found: {name}", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting authentication profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("authentication-profile")
def load_authentication_profile(
    file: Path = FILE_OPTION,
    folder: str | None = LOAD_FOLDER_OPTION,
    snippet: str | None = LOAD_SNIPPET_OPTION,
    device: str | None = LOAD_DEVICE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load authentication profiles from a YAML file.

    Example: scm load identity authentication-profile --file auth-profiles.yaml --folder Texas

    """
    try:
        if not file.exists():
            typer.echo(f"Error: File '{file}' does not exist", err=True)
            raise typer.Exit(code=1)

        with file.open() as f:
            yaml_content = yaml.safe_load(f)

        if not yaml_content:
            typer.echo(f"Error: File '{file}' is empty or invalid", err=True)
            raise typer.Exit(code=1)

        profiles = yaml_content.get("authentication_profiles", [])
        if not profiles:
            typer.echo("No authentication profiles found in the YAML file.")
            return

        if dry_run:
            typer.echo("[DRY RUN] Would load the following authentication profiles:")
            typer.echo(yaml.dump(profiles, default_flow_style=False))
            return

        loaded_count = 0
        for profile_data in profiles:
            try:
                if folder:
                    profile_data["folder"] = folder
                elif snippet:
                    profile_data["snippet"] = snippet
                elif device:
                    profile_data["device"] = device

                profile = AuthenticationProfile(**profile_data)
                sdk_data = profile.to_sdk_model()
                result = scm_client.create_authentication_profile(**sdk_data)

                action = result.get("__action__", "created")
                if action == "no_change":
                    typer.echo(f"No changes for authentication profile: {profile.name}")
                elif action == "updated":
                    typer.echo(f"Updated authentication profile: {profile.name}")
                else:
                    typer.echo(f"Created authentication profile: {profile.name}")
                loaded_count += 1

            except Exception as e:
                typer.echo(f"Error loading authentication profile: {str(e)}", err=True)

        typer.echo(f"\nProcessed {loaded_count} authentication profiles from {file}")

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading authentication profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@backup_app.command("authentication-profile")
def backup_authentication_profile(
    folder: str | None = BACKUP_FOLDER_OPTION,
    snippet: str | None = BACKUP_SNIPPET_OPTION,
    device: str | None = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup authentication profiles to a YAML file.

    Examples
    --------
        scm backup identity authentication-profile --folder Texas
        scm backup identity authentication-profile --folder Texas --file auth-profiles.yaml

    """
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)

        typer.echo(f"Fetching authentication profiles from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        profiles = scm_client.list_authentication_profiles(**kwargs, exact_match=True)

        if not profiles:
            typer.echo(f"No authentication profiles found in {location_type} '{location_value}'")
            return

        backup_data: dict[str, list[dict[str, Any]]] = {"authentication_profiles": []}
        for p in profiles:
            p_dict = p.copy()
            p_dict.pop("id", None)
            backup_data["authentication_profiles"].append(p_dict)

        backup_data["authentication_profiles"].sort(key=lambda x: x["name"])
        filename = file or Path(get_default_backup_filename("authentication-profile", location_type, location_value))

        with open(filename, "w") as fh:
            yaml.dump(backup_data, fh, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data['authentication_profiles'])} authentication profiles to {filename}")

    except Exception as e:
        typer.echo(f"Error backing up authentication profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ==============================================================================================================================================================================================
# KERBEROS SERVER PROFILE COMMANDS
# ==============================================================================================================================================================================================


@set_app.command("kerberos-server-profile")
def set_kerberos_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str = NAME_OPTION,
    servers: str | None = typer.Option(None, "--servers", help="Server list as JSON string"),
):
    r"""Create or update a Kerberos server profile.

    Examples
    --------
        scm set identity kerberos-server-profile --folder Texas --name corp-kerberos \\
            --servers '[{"name": "kdc1", "host": "kdc1.example.com", "port": 88}]'

    """
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)

        servers_list = json_lib.loads(servers) if servers else None

        profile = KerberosServerProfile(
            name=name,
            folder=folder,
            snippet=snippet,
            device=device,
            servers=servers_list,
        )

        sdk_data = profile.to_sdk_model()
        result = scm_client.create_kerberos_server_profile(**sdk_data)

        action = result.get("__action__", "created")
        if action == "no_change":
            typer.echo(f"No changes detected for Kerberos server profile: {name}")
        elif action == "updated":
            typer.echo(f"Updated Kerberos server profile: {name} in {location_type} {location_value}")
        else:
            typer.echo(f"Created Kerberos server profile: {name} in {location_type} {location_value}")
        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating Kerberos server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("kerberos-server-profile")
def show_kerberos_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the Kerberos server profile to show"),
    list_items: bool = typer.Option(False, "--list", "-l", help="List all Kerberos server profiles"),
):
    """Display Kerberos server profiles.

    Examples
    --------
        scm show identity kerberos-server-profile --folder Texas --list
        scm show identity kerberos-server-profile --folder Texas --name corp-kerberos

    """
    try:
        if name:
            location_type, location_value = validate_location_params(folder, snippet, device)
            profile = scm_client.get_kerberos_server_profile(name=name, **{location_type: location_value})

            typer.echo(f"\nKerberos Server Profile: {profile.get('name', 'N/A')}")
            typer.echo("=" * 80)
            if profile.get("server"):
                typer.echo(f"Servers ({len(profile['server'])}):")
                for idx, srv in enumerate(profile["server"]):
                    typer.echo(f"  Server {idx + 1}: {srv.get('name', 'N/A')} - {srv.get('host', 'N/A')}:{srv.get('port', 'N/A')}")
            if profile.get("id"):
                typer.echo(f"ID: {profile['id']}")
        else:
            # List all Kerberos server profiles (default behavior)
            profiles = scm_client.list_kerberos_server_profiles(folder=folder, snippet=snippet, device=device)
            if not profiles:
                typer.echo("No Kerberos server profiles found")
                return

            typer.echo(f"\nKerberos Server Profiles ({len(profiles)}):")
            typer.echo("-" * 80)
            for p in profiles:
                typer.echo(f"Name: {p.get('name', 'N/A')}")
                if p.get("server"):
                    typer.echo(f"  Servers: {len(p['server'])}")
                typer.echo("-" * 80)

    except Exception as e:
        typer.echo(f"Error showing Kerberos server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("kerberos-server-profile")
def delete_kerberos_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a Kerberos server profile.

    Example: scm delete identity kerberos-server-profile --folder Texas --name corp-kerberos

    """
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if not force:
            typer.confirm(f"Delete Kerberos server profile '{name}' from {location_type} '{location_value}'?", abort=True)
        result = scm_client.delete_kerberos_server_profile(name=name, **{location_type: location_value})

        if result:
            typer.echo(f"Deleted Kerberos server profile: {name} from {location_type} {location_value}")
        else:
            typer.echo(f"Kerberos server profile not found: {name}", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting Kerberos server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("kerberos-server-profile")
def load_kerberos_server_profile(
    file: Path = FILE_OPTION,
    folder: str | None = LOAD_FOLDER_OPTION,
    snippet: str | None = LOAD_SNIPPET_OPTION,
    device: str | None = LOAD_DEVICE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load Kerberos server profiles from a YAML file.

    Example: scm load identity kerberos-server-profile --file kerberos.yaml --folder Texas

    """
    try:
        if not file.exists():
            typer.echo(f"Error: File '{file}' does not exist", err=True)
            raise typer.Exit(code=1)

        with file.open() as f:
            yaml_content = yaml.safe_load(f)

        if not yaml_content:
            typer.echo(f"Error: File '{file}' is empty or invalid", err=True)
            raise typer.Exit(code=1)

        profiles = yaml_content.get("kerberos_server_profiles", [])
        if not profiles:
            typer.echo("No Kerberos server profiles found in the YAML file.")
            return

        if dry_run:
            typer.echo("[DRY RUN] Would load the following Kerberos server profiles:")
            typer.echo(yaml.dump(profiles, default_flow_style=False))
            return

        loaded_count = 0
        for profile_data in profiles:
            try:
                if folder:
                    profile_data["folder"] = folder
                elif snippet:
                    profile_data["snippet"] = snippet
                elif device:
                    profile_data["device"] = device

                profile = KerberosServerProfile(**profile_data)
                sdk_data = profile.to_sdk_model()
                result = scm_client.create_kerberos_server_profile(**sdk_data)

                action = result.get("__action__", "created")
                if action == "no_change":
                    typer.echo(f"No changes for Kerberos server profile: {profile.name}")
                elif action == "updated":
                    typer.echo(f"Updated Kerberos server profile: {profile.name}")
                else:
                    typer.echo(f"Created Kerberos server profile: {profile.name}")
                loaded_count += 1

            except Exception as e:
                typer.echo(f"Error loading Kerberos server profile: {str(e)}", err=True)

        typer.echo(f"\nProcessed {loaded_count} Kerberos server profiles from {file}")

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading Kerberos server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@backup_app.command("kerberos-server-profile")
def backup_kerberos_server_profile(
    folder: str | None = BACKUP_FOLDER_OPTION,
    snippet: str | None = BACKUP_SNIPPET_OPTION,
    device: str | None = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup Kerberos server profiles to a YAML file.

    Examples
    --------
        scm backup identity kerberos-server-profile --folder Texas
        scm backup identity kerberos-server-profile --folder Texas --file kerberos.yaml

    """
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)

        typer.echo(f"Fetching Kerberos server profiles from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        profiles = scm_client.list_kerberos_server_profiles(**kwargs, exact_match=True)

        if not profiles:
            typer.echo(f"No Kerberos server profiles found in {location_type} '{location_value}'")
            return

        backup_data: dict[str, list[dict[str, Any]]] = {"kerberos_server_profiles": []}
        for p in profiles:
            p_dict = p.copy()
            p_dict.pop("id", None)
            backup_data["kerberos_server_profiles"].append(p_dict)

        backup_data["kerberos_server_profiles"].sort(key=lambda x: x["name"])
        filename = file or Path(get_default_backup_filename("kerberos-server-profile", location_type, location_value))

        with open(filename, "w") as fh:
            yaml.dump(backup_data, fh, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data['kerberos_server_profiles'])} Kerberos server profiles to {filename}")

    except Exception as e:
        typer.echo(f"Error backing up Kerberos server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ==============================================================================================================================================================================================
# LDAP SERVER PROFILE COMMANDS
# ==============================================================================================================================================================================================


@set_app.command("ldap-server-profile")
def set_ldap_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str = NAME_OPTION,
    servers: str | None = typer.Option(None, "--servers", help="Server list as JSON string"),
    base: str | None = typer.Option(None, "--base", help="Base distinguished name"),
    bind_dn: str | None = typer.Option(None, "--bind-dn", help="Bind distinguished name"),
    bind_password: str | None = typer.Option(None, "--bind-password", help="Bind password"),
    ldap_type: str | None = typer.Option(None, "--ldap-type", help="LDAP type (active-directory, e-directory, sun, other)"),
    ssl: bool | None = typer.Option(None, "--ssl", help="Enable SSL"),
):
    r"""Create or update an LDAP server profile.

    Examples
    --------
        scm set identity ldap-server-profile --folder Texas --name corp-ldap \\
            --servers '[{"name": "ldap1", "address": "ldap.example.com", "port": 389}]' \\
            --base "dc=example,dc=com" --ldap-type active-directory

    """
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)

        servers_list = json_lib.loads(servers) if servers else None

        profile = LdapServerProfile(
            name=name,
            folder=folder,
            snippet=snippet,
            device=device,
            servers=servers_list,
            base=base,
            bind_dn=bind_dn,
            bind_password=bind_password,
            ldap_type=ldap_type,
            ssl=ssl,
        )

        sdk_data = profile.to_sdk_model()
        result = scm_client.create_ldap_server_profile(**sdk_data)

        action = result.get("__action__", "created")
        if action == "no_change":
            typer.echo(f"No changes detected for LDAP server profile: {name}")
        elif action == "updated":
            typer.echo(f"Updated LDAP server profile: {name} in {location_type} {location_value}")
        else:
            typer.echo(f"Created LDAP server profile: {name} in {location_type} {location_value}")
        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating LDAP server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("ldap-server-profile")
def show_ldap_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the LDAP server profile to show"),
    list_items: bool = typer.Option(False, "--list", "-l", help="List all LDAP server profiles"),
):
    """Display LDAP server profiles.

    Examples
    --------
        scm show identity ldap-server-profile --folder Texas --list
        scm show identity ldap-server-profile --folder Texas --name corp-ldap

    """
    try:
        if name:
            location_type, location_value = validate_location_params(folder, snippet, device)
            profile = scm_client.get_ldap_server_profile(name=name, **{location_type: location_value})

            typer.echo(f"\nLDAP Server Profile: {profile.get('name', 'N/A')}")
            typer.echo("=" * 80)
            if profile.get("ldap_type"):
                typer.echo(f"Type: {profile['ldap_type']}")
            if profile.get("base"):
                typer.echo(f"Base DN: {profile['base']}")
            if profile.get("bind_dn"):
                typer.echo(f"Bind DN: {profile['bind_dn']}")
            if profile.get("ssl") is not None:
                typer.echo(f"SSL: {profile['ssl']}")
            if profile.get("server"):
                typer.echo(f"Servers ({len(profile['server'])}):")
                for idx, srv in enumerate(profile["server"]):
                    typer.echo(f"  Server {idx + 1}: {srv.get('name', 'N/A')} - {srv.get('address', 'N/A')}:{srv.get('port', 'N/A')}")
            if profile.get("id"):
                typer.echo(f"ID: {profile['id']}")
        else:
            # List all LDAP server profiles (default behavior)
            profiles = scm_client.list_ldap_server_profiles(folder=folder, snippet=snippet, device=device)
            if not profiles:
                typer.echo("No LDAP server profiles found")
                return

            typer.echo(f"\nLDAP Server Profiles ({len(profiles)}):")
            typer.echo("-" * 80)
            for p in profiles:
                typer.echo(f"Name: {p.get('name', 'N/A')}")
                if p.get("ldap_type"):
                    typer.echo(f"  Type: {p['ldap_type']}")
                if p.get("server"):
                    typer.echo(f"  Servers: {len(p['server'])}")
                typer.echo("-" * 80)

    except Exception as e:
        typer.echo(f"Error showing LDAP server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("ldap-server-profile")
def delete_ldap_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete an LDAP server profile.

    Example: scm delete identity ldap-server-profile --folder Texas --name corp-ldap

    """
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if not force:
            typer.confirm(f"Delete LDAP server profile '{name}' from {location_type} '{location_value}'?", abort=True)
        result = scm_client.delete_ldap_server_profile(name=name, **{location_type: location_value})

        if result:
            typer.echo(f"Deleted LDAP server profile: {name} from {location_type} {location_value}")
        else:
            typer.echo(f"LDAP server profile not found: {name}", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting LDAP server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("ldap-server-profile")
def load_ldap_server_profile(
    file: Path = FILE_OPTION,
    folder: str | None = LOAD_FOLDER_OPTION,
    snippet: str | None = LOAD_SNIPPET_OPTION,
    device: str | None = LOAD_DEVICE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load LDAP server profiles from a YAML file.

    Example: scm load identity ldap-server-profile --file ldap.yaml --folder Texas

    """
    try:
        if not file.exists():
            typer.echo(f"Error: File '{file}' does not exist", err=True)
            raise typer.Exit(code=1)

        with file.open() as f:
            yaml_content = yaml.safe_load(f)

        if not yaml_content:
            typer.echo(f"Error: File '{file}' is empty or invalid", err=True)
            raise typer.Exit(code=1)

        profiles = yaml_content.get("ldap_server_profiles", [])
        if not profiles:
            typer.echo("No LDAP server profiles found in the YAML file.")
            return

        if dry_run:
            typer.echo("[DRY RUN] Would load the following LDAP server profiles:")
            typer.echo(yaml.dump(profiles, default_flow_style=False))
            return

        loaded_count = 0
        for profile_data in profiles:
            try:
                if folder:
                    profile_data["folder"] = folder
                elif snippet:
                    profile_data["snippet"] = snippet
                elif device:
                    profile_data["device"] = device

                profile = LdapServerProfile(**profile_data)
                sdk_data = profile.to_sdk_model()
                result = scm_client.create_ldap_server_profile(**sdk_data)

                action = result.get("__action__", "created")
                if action == "no_change":
                    typer.echo(f"No changes for LDAP server profile: {profile.name}")
                elif action == "updated":
                    typer.echo(f"Updated LDAP server profile: {profile.name}")
                else:
                    typer.echo(f"Created LDAP server profile: {profile.name}")
                loaded_count += 1

            except Exception as e:
                typer.echo(f"Error loading LDAP server profile: {str(e)}", err=True)

        typer.echo(f"\nProcessed {loaded_count} LDAP server profiles from {file}")

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading LDAP server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@backup_app.command("ldap-server-profile")
def backup_ldap_server_profile(
    folder: str | None = BACKUP_FOLDER_OPTION,
    snippet: str | None = BACKUP_SNIPPET_OPTION,
    device: str | None = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup LDAP server profiles to a YAML file.

    Examples
    --------
        scm backup identity ldap-server-profile --folder Texas
        scm backup identity ldap-server-profile --folder Texas --file ldap.yaml

    """
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)

        typer.echo(f"Fetching LDAP server profiles from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        profiles = scm_client.list_ldap_server_profiles(**kwargs, exact_match=True)

        if not profiles:
            typer.echo(f"No LDAP server profiles found in {location_type} '{location_value}'")
            return

        backup_data: dict[str, list[dict[str, Any]]] = {"ldap_server_profiles": []}
        for p in profiles:
            p_dict = p.copy()
            p_dict.pop("id", None)
            backup_data["ldap_server_profiles"].append(p_dict)

        backup_data["ldap_server_profiles"].sort(key=lambda x: x["name"])
        filename = file or Path(get_default_backup_filename("ldap-server-profile", location_type, location_value))

        with open(filename, "w") as fh:
            yaml.dump(backup_data, fh, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data['ldap_server_profiles'])} LDAP server profiles to {filename}")

    except Exception as e:
        typer.echo(f"Error backing up LDAP server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ==============================================================================================================================================================================================
# RADIUS SERVER PROFILE COMMANDS
# ==============================================================================================================================================================================================


@set_app.command("radius-server-profile")
def set_radius_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str = NAME_OPTION,
    servers: str | None = typer.Option(None, "--servers", help="Server list as JSON string"),
    protocol: str | None = typer.Option(None, "--protocol", help="Protocol config as JSON string"),
    timeout: int | None = typer.Option(None, "--timeout", help="Timeout in seconds (1-120)"),
    retries: int | None = typer.Option(None, "--retries", help="Number of retries (1-5)"),
):
    r"""Create or update a RADIUS server profile.

    Examples
    --------
        scm set identity radius-server-profile --folder Texas --name corp-radius \\
            --servers '[{"name": "rad1", "ip_address": "10.0.0.1", "port": 1812, "secret": "s3cret"}]' \\
            --protocol '{"CHAP": {}}' --timeout 5 --retries 3

    """
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)

        servers_list = json_lib.loads(servers) if servers else None
        protocol_dict = json_lib.loads(protocol) if protocol else None

        profile = RadiusServerProfile(
            name=name,
            folder=folder,
            snippet=snippet,
            device=device,
            servers=servers_list,
            protocol=protocol_dict,
            timeout=timeout,
            retries=retries,
        )

        sdk_data = profile.to_sdk_model()
        result = scm_client.create_radius_server_profile(**sdk_data)

        action = result.get("__action__", "created")
        if action == "no_change":
            typer.echo(f"No changes detected for RADIUS server profile: {name}")
        elif action == "updated":
            typer.echo(f"Updated RADIUS server profile: {name} in {location_type} {location_value}")
        else:
            typer.echo(f"Created RADIUS server profile: {name} in {location_type} {location_value}")
        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating RADIUS server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("radius-server-profile")
def show_radius_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the RADIUS server profile to show"),
    list_items: bool = typer.Option(False, "--list", "-l", help="List all RADIUS server profiles"),
):
    """Display RADIUS server profiles.

    Examples
    --------
        scm show identity radius-server-profile --folder Texas --list
        scm show identity radius-server-profile --folder Texas --name corp-radius

    """
    try:
        if name:
            location_type, location_value = validate_location_params(folder, snippet, device)
            profile = scm_client.get_radius_server_profile(name=name, **{location_type: location_value})

            typer.echo(f"\nRADIUS Server Profile: {profile.get('name', 'N/A')}")
            typer.echo("=" * 80)
            if profile.get("protocol"):
                typer.echo(f"Protocol: {json_lib.dumps(profile['protocol'])}")
            if profile.get("timeout"):
                typer.echo(f"Timeout: {profile['timeout']}s")
            if profile.get("retries"):
                typer.echo(f"Retries: {profile['retries']}")
            if profile.get("server"):
                typer.echo(f"Servers ({len(profile['server'])}):")
                for idx, srv in enumerate(profile["server"]):
                    typer.echo(f"  Server {idx + 1}: {srv.get('name', 'N/A')} - {srv.get('ip_address', 'N/A')}:{srv.get('port', 'N/A')}")
            if profile.get("id"):
                typer.echo(f"ID: {profile['id']}")
        else:
            # List all RADIUS server profiles (default behavior)
            profiles = scm_client.list_radius_server_profiles(folder=folder, snippet=snippet, device=device)
            if not profiles:
                typer.echo("No RADIUS server profiles found")
                return

            typer.echo(f"\nRADIUS Server Profiles ({len(profiles)}):")
            typer.echo("-" * 80)
            for p in profiles:
                typer.echo(f"Name: {p.get('name', 'N/A')}")
                if p.get("server"):
                    typer.echo(f"  Servers: {len(p['server'])}")
                if p.get("timeout"):
                    typer.echo(f"  Timeout: {p['timeout']}s")
                typer.echo("-" * 80)

    except Exception as e:
        typer.echo(f"Error showing RADIUS server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("radius-server-profile")
def delete_radius_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a RADIUS server profile.

    Example: scm delete identity radius-server-profile --folder Texas --name corp-radius

    """
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if not force:
            typer.confirm(f"Delete RADIUS server profile '{name}' from {location_type} '{location_value}'?", abort=True)
        result = scm_client.delete_radius_server_profile(name=name, **{location_type: location_value})

        if result:
            typer.echo(f"Deleted RADIUS server profile: {name} from {location_type} {location_value}")
        else:
            typer.echo(f"RADIUS server profile not found: {name}", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting RADIUS server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("radius-server-profile")
def load_radius_server_profile(
    file: Path = FILE_OPTION,
    folder: str | None = LOAD_FOLDER_OPTION,
    snippet: str | None = LOAD_SNIPPET_OPTION,
    device: str | None = LOAD_DEVICE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load RADIUS server profiles from a YAML file.

    Example: scm load identity radius-server-profile --file radius.yaml --folder Texas

    """
    try:
        if not file.exists():
            typer.echo(f"Error: File '{file}' does not exist", err=True)
            raise typer.Exit(code=1)

        with file.open() as f:
            yaml_content = yaml.safe_load(f)

        if not yaml_content:
            typer.echo(f"Error: File '{file}' is empty or invalid", err=True)
            raise typer.Exit(code=1)

        profiles = yaml_content.get("radius_server_profiles", [])
        if not profiles:
            typer.echo("No RADIUS server profiles found in the YAML file.")
            return

        if dry_run:
            typer.echo("[DRY RUN] Would load the following RADIUS server profiles:")
            typer.echo(yaml.dump(profiles, default_flow_style=False))
            return

        loaded_count = 0
        for profile_data in profiles:
            try:
                if folder:
                    profile_data["folder"] = folder
                elif snippet:
                    profile_data["snippet"] = snippet
                elif device:
                    profile_data["device"] = device

                profile = RadiusServerProfile(**profile_data)
                sdk_data = profile.to_sdk_model()
                result = scm_client.create_radius_server_profile(**sdk_data)

                action = result.get("__action__", "created")
                if action == "no_change":
                    typer.echo(f"No changes for RADIUS server profile: {profile.name}")
                elif action == "updated":
                    typer.echo(f"Updated RADIUS server profile: {profile.name}")
                else:
                    typer.echo(f"Created RADIUS server profile: {profile.name}")
                loaded_count += 1

            except Exception as e:
                typer.echo(f"Error loading RADIUS server profile: {str(e)}", err=True)

        typer.echo(f"\nProcessed {loaded_count} RADIUS server profiles from {file}")

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading RADIUS server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@backup_app.command("radius-server-profile")
def backup_radius_server_profile(
    folder: str | None = BACKUP_FOLDER_OPTION,
    snippet: str | None = BACKUP_SNIPPET_OPTION,
    device: str | None = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup RADIUS server profiles to a YAML file.

    Examples
    --------
        scm backup identity radius-server-profile --folder Texas
        scm backup identity radius-server-profile --folder Texas --file radius.yaml

    """
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)

        typer.echo(f"Fetching RADIUS server profiles from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        profiles = scm_client.list_radius_server_profiles(**kwargs, exact_match=True)

        if not profiles:
            typer.echo(f"No RADIUS server profiles found in {location_type} '{location_value}'")
            return

        backup_data: dict[str, list[dict[str, Any]]] = {"radius_server_profiles": []}
        for p in profiles:
            p_dict = p.copy()
            p_dict.pop("id", None)
            backup_data["radius_server_profiles"].append(p_dict)

        backup_data["radius_server_profiles"].sort(key=lambda x: x["name"])
        filename = file or Path(get_default_backup_filename("radius-server-profile", location_type, location_value))

        with open(filename, "w") as fh:
            yaml.dump(backup_data, fh, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data['radius_server_profiles'])} RADIUS server profiles to {filename}")

    except Exception as e:
        typer.echo(f"Error backing up RADIUS server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ==============================================================================================================================================================================================
# SAML SERVER PROFILE COMMANDS
# ==============================================================================================================================================================================================


@set_app.command("saml-server-profile")
def set_saml_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str = NAME_OPTION,
    entity_id: str = typer.Option(..., "--entity-id", help="Entity ID"),
    certificate: str = typer.Option(..., "--certificate", help="Certificate name"),
    sso_url: str = typer.Option(..., "--sso-url", help="Single Sign-On URL"),
    sso_bindings: str = typer.Option(..., "--sso-bindings", help="SSO binding type (post, redirect)"),
    slo_bindings: str | None = typer.Option(None, "--slo-bindings", help="SLO binding type (post, redirect)"),
    max_clock_skew: int | None = typer.Option(None, "--max-clock-skew", help="Maximum clock skew in seconds (1-900)"),
    validate_idp_certificate: bool | None = typer.Option(None, "--validate-idp-certificate", help="Validate IDP certificate"),
    want_auth_requests_signed: bool | None = typer.Option(None, "--want-auth-requests-signed", help="Want auth requests signed"),
):
    r"""Create or update a SAML server profile.

    Examples
    --------
        scm set identity saml-server-profile --folder Texas --name corp-saml \\
            --entity-id "https://idp.example.com" --certificate idp-cert \\
            --sso-url "https://idp.example.com/sso" --sso-bindings post

    """
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)

        profile = SamlServerProfile(
            name=name,
            folder=folder,
            snippet=snippet,
            device=device,
            entity_id=entity_id,
            certificate=certificate,
            sso_url=sso_url,
            sso_bindings=sso_bindings,
            slo_bindings=slo_bindings,
            max_clock_skew=max_clock_skew,
            validate_idp_certificate=validate_idp_certificate,
            want_auth_requests_signed=want_auth_requests_signed,
        )

        sdk_data = profile.to_sdk_model()
        result = scm_client.create_saml_server_profile(**sdk_data)

        action = result.get("__action__", "created")
        if action == "no_change":
            typer.echo(f"No changes detected for SAML server profile: {name}")
        elif action == "updated":
            typer.echo(f"Updated SAML server profile: {name} in {location_type} {location_value}")
        else:
            typer.echo(f"Created SAML server profile: {name} in {location_type} {location_value}")
        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating SAML server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("saml-server-profile")
def show_saml_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the SAML server profile to show"),
    list_items: bool = typer.Option(False, "--list", "-l", help="List all SAML server profiles"),
):
    """Display SAML server profiles.

    Examples
    --------
        scm show identity saml-server-profile --folder Texas --list
        scm show identity saml-server-profile --folder Texas --name corp-saml

    """
    try:
        if name:
            location_type, location_value = validate_location_params(folder, snippet, device)
            profile = scm_client.get_saml_server_profile(name=name, **{location_type: location_value})

            typer.echo(f"\nSAML Server Profile: {profile.get('name', 'N/A')}")
            typer.echo("=" * 80)
            if profile.get("entity_id"):
                typer.echo(f"Entity ID: {profile['entity_id']}")
            if profile.get("certificate"):
                typer.echo(f"Certificate: {profile['certificate']}")
            if profile.get("sso_url"):
                typer.echo(f"SSO URL: {profile['sso_url']}")
            if profile.get("sso_bindings"):
                typer.echo(f"SSO Bindings: {profile['sso_bindings']}")
            if profile.get("slo_bindings"):
                typer.echo(f"SLO Bindings: {profile['slo_bindings']}")
            if profile.get("max_clock_skew"):
                typer.echo(f"Max Clock Skew: {profile['max_clock_skew']}s")
            if profile.get("id"):
                typer.echo(f"ID: {profile['id']}")
        else:
            # List all SAML server profiles (default behavior)
            profiles = scm_client.list_saml_server_profiles(folder=folder, snippet=snippet, device=device)
            if not profiles:
                typer.echo("No SAML server profiles found")
                return

            typer.echo(f"\nSAML Server Profiles ({len(profiles)}):")
            typer.echo("-" * 80)
            for p in profiles:
                typer.echo(f"Name: {p.get('name', 'N/A')}")
                if p.get("entity_id"):
                    typer.echo(f"  Entity ID: {p['entity_id']}")
                if p.get("sso_url"):
                    typer.echo(f"  SSO URL: {p['sso_url']}")
                typer.echo("-" * 80)

    except Exception as e:
        typer.echo(f"Error showing SAML server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("saml-server-profile")
def delete_saml_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a SAML server profile.

    Example: scm delete identity saml-server-profile --folder Texas --name corp-saml

    """
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if not force:
            typer.confirm(f"Delete SAML server profile '{name}' from {location_type} '{location_value}'?", abort=True)
        result = scm_client.delete_saml_server_profile(name=name, **{location_type: location_value})

        if result:
            typer.echo(f"Deleted SAML server profile: {name} from {location_type} {location_value}")
        else:
            typer.echo(f"SAML server profile not found: {name}", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting SAML server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("saml-server-profile")
def load_saml_server_profile(
    file: Path = FILE_OPTION,
    folder: str | None = LOAD_FOLDER_OPTION,
    snippet: str | None = LOAD_SNIPPET_OPTION,
    device: str | None = LOAD_DEVICE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load SAML server profiles from a YAML file.

    Example: scm load identity saml-server-profile --file saml.yaml --folder Texas

    """
    try:
        if not file.exists():
            typer.echo(f"Error: File '{file}' does not exist", err=True)
            raise typer.Exit(code=1)

        with file.open() as f:
            yaml_content = yaml.safe_load(f)

        if not yaml_content:
            typer.echo(f"Error: File '{file}' is empty or invalid", err=True)
            raise typer.Exit(code=1)

        profiles = yaml_content.get("saml_server_profiles", [])
        if not profiles:
            typer.echo("No SAML server profiles found in the YAML file.")
            return

        if dry_run:
            typer.echo("[DRY RUN] Would load the following SAML server profiles:")
            typer.echo(yaml.dump(profiles, default_flow_style=False))
            return

        loaded_count = 0
        for profile_data in profiles:
            try:
                if folder:
                    profile_data["folder"] = folder
                elif snippet:
                    profile_data["snippet"] = snippet
                elif device:
                    profile_data["device"] = device

                profile = SamlServerProfile(**profile_data)
                sdk_data = profile.to_sdk_model()
                result = scm_client.create_saml_server_profile(**sdk_data)

                action = result.get("__action__", "created")
                if action == "no_change":
                    typer.echo(f"No changes for SAML server profile: {profile.name}")
                elif action == "updated":
                    typer.echo(f"Updated SAML server profile: {profile.name}")
                else:
                    typer.echo(f"Created SAML server profile: {profile.name}")
                loaded_count += 1

            except Exception as e:
                typer.echo(f"Error loading SAML server profile: {str(e)}", err=True)

        typer.echo(f"\nProcessed {loaded_count} SAML server profiles from {file}")

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading SAML server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@backup_app.command("saml-server-profile")
def backup_saml_server_profile(
    folder: str | None = BACKUP_FOLDER_OPTION,
    snippet: str | None = BACKUP_SNIPPET_OPTION,
    device: str | None = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup SAML server profiles to a YAML file.

    Examples
    --------
        scm backup identity saml-server-profile --folder Texas
        scm backup identity saml-server-profile --folder Texas --file saml.yaml

    """
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)

        typer.echo(f"Fetching SAML server profiles from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        profiles = scm_client.list_saml_server_profiles(**kwargs, exact_match=True)

        if not profiles:
            typer.echo(f"No SAML server profiles found in {location_type} '{location_value}'")
            return

        backup_data: dict[str, list[dict[str, Any]]] = {"saml_server_profiles": []}
        for p in profiles:
            p_dict = p.copy()
            p_dict.pop("id", None)
            backup_data["saml_server_profiles"].append(p_dict)

        backup_data["saml_server_profiles"].sort(key=lambda x: x["name"])
        filename = file or Path(get_default_backup_filename("saml-server-profile", location_type, location_value))

        with open(filename, "w") as fh:
            yaml.dump(backup_data, fh, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data['saml_server_profiles'])} SAML server profiles to {filename}")

    except Exception as e:
        typer.echo(f"Error backing up SAML server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# ==============================================================================================================================================================================================
# TACACS+ SERVER PROFILE COMMANDS
# ==============================================================================================================================================================================================


@set_app.command("tacacs-server-profile")
def set_tacacs_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str = NAME_OPTION,
    servers: str | None = typer.Option(None, "--servers", help="Server list as JSON string"),
    protocol: str | None = typer.Option(None, "--protocol", help="Protocol type (CHAP, PAP)"),
    timeout: int | None = typer.Option(None, "--timeout", help="Timeout in seconds (1-30)"),
    use_single_connection: bool | None = typer.Option(None, "--use-single-connection", help="Use single connection"),
):
    r"""Create or update a TACACS+ server profile.

    Examples
    --------
        scm set identity tacacs-server-profile --folder Texas --name corp-tacacs \\
            --servers '[{"name": "tac1", "address": "10.0.0.1", "port": 49, "secret": "s3cret"}]' \\
            --protocol CHAP --timeout 5

    """
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)

        servers_list = json_lib.loads(servers) if servers else None

        profile = TacacsServerProfile(
            name=name,
            folder=folder,
            snippet=snippet,
            device=device,
            servers=servers_list,
            protocol=protocol,
            timeout=timeout,
            use_single_connection=use_single_connection,
        )

        sdk_data = profile.to_sdk_model()
        result = scm_client.create_tacacs_server_profile(**sdk_data)

        action = result.get("__action__", "created")
        if action == "no_change":
            typer.echo(f"No changes detected for TACACS+ server profile: {name}")
        elif action == "updated":
            typer.echo(f"Updated TACACS+ server profile: {name} in {location_type} {location_value}")
        else:
            typer.echo(f"Created TACACS+ server profile: {name} in {location_type} {location_value}")
        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating TACACS+ server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("tacacs-server-profile")
def show_tacacs_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the TACACS+ server profile to show"),
    list_items: bool = typer.Option(False, "--list", "-l", help="List all TACACS+ server profiles"),
):
    """Display TACACS+ server profiles.

    Examples
    --------
        scm show identity tacacs-server-profile --folder Texas --list
        scm show identity tacacs-server-profile --folder Texas --name corp-tacacs

    """
    try:
        if name:
            location_type, location_value = validate_location_params(folder, snippet, device)
            profile = scm_client.get_tacacs_server_profile(name=name, **{location_type: location_value})

            typer.echo(f"\nTACACS+ Server Profile: {profile.get('name', 'N/A')}")
            typer.echo("=" * 80)
            if profile.get("protocol"):
                typer.echo(f"Protocol: {profile['protocol']}")
            if profile.get("timeout"):
                typer.echo(f"Timeout: {profile['timeout']}s")
            if profile.get("use_single_connection") is not None:
                typer.echo(f"Use Single Connection: {profile['use_single_connection']}")
            if profile.get("server"):
                typer.echo(f"Servers ({len(profile['server'])}):")
                for idx, srv in enumerate(profile["server"]):
                    typer.echo(f"  Server {idx + 1}: {srv.get('name', 'N/A')} - {srv.get('address', 'N/A')}:{srv.get('port', 'N/A')}")
            if profile.get("id"):
                typer.echo(f"ID: {profile['id']}")
        else:
            # List all TACACS+ server profiles (default behavior)
            profiles = scm_client.list_tacacs_server_profiles(folder=folder, snippet=snippet, device=device)
            if not profiles:
                typer.echo("No TACACS+ server profiles found")
                return

            typer.echo(f"\nTACACS+ Server Profiles ({len(profiles)}):")
            typer.echo("-" * 80)
            for p in profiles:
                typer.echo(f"Name: {p.get('name', 'N/A')}")
                if p.get("protocol"):
                    typer.echo(f"  Protocol: {p['protocol']}")
                if p.get("server"):
                    typer.echo(f"  Servers: {len(p['server'])}")
                typer.echo("-" * 80)

    except Exception as e:
        typer.echo(f"Error showing TACACS+ server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("tacacs-server-profile")
def delete_tacacs_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a TACACS+ server profile.

    Example: scm delete identity tacacs-server-profile --folder Texas --name corp-tacacs

    """
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)
        if not force:
            typer.confirm(f"Delete TACACS+ server profile '{name}' from {location_type} '{location_value}'?", abort=True)
        result = scm_client.delete_tacacs_server_profile(name=name, **{location_type: location_value})

        if result:
            typer.echo(f"Deleted TACACS+ server profile: {name} from {location_type} {location_value}")
        else:
            typer.echo(f"TACACS+ server profile not found: {name}", err=True)
            raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error deleting TACACS+ server profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("tacacs-server-profile")
def load_tacacs_server_profile(
    file: Path = FILE_OPTION,
    folder: str | None = LOAD_FOLDER_OPTION,
    snippet: str | None = LOAD_SNIPPET_OPTION,
    device: str | None = LOAD_DEVICE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
):
    """Load TACACS+ server profiles from a YAML file.

    Example: scm load identity tacacs-server-profile --file tacacs.yaml --folder Texas

    """
    try:
        if not file.exists():
            typer.echo(f"Error: File '{file}' does not exist", err=True)
            raise typer.Exit(code=1)

        with file.open() as f:
            yaml_content = yaml.safe_load(f)

        if not yaml_content:
            typer.echo(f"Error: File '{file}' is empty or invalid", err=True)
            raise typer.Exit(code=1)

        profiles = yaml_content.get("tacacs_server_profiles", [])
        if not profiles:
            typer.echo("No TACACS+ server profiles found in the YAML file.")
            return

        if dry_run:
            typer.echo("[DRY RUN] Would load the following TACACS+ server profiles:")
            typer.echo(yaml.dump(profiles, default_flow_style=False))
            return

        loaded_count = 0
        for profile_data in profiles:
            try:
                if folder:
                    profile_data["folder"] = folder
                elif snippet:
                    profile_data["snippet"] = snippet
                elif device:
                    profile_data["device"] = device

                profile = TacacsServerProfile(**profile_data)
                sdk_data = profile.to_sdk_model()
                result = scm_client.create_tacacs_server_profile(**sdk_data)

                action = result.get("__action__", "created")
                if action == "no_change":
                    typer.echo(f"No changes for TACACS+ server profile: {profile.name}")
                elif action == "updated":
                    typer.echo(f"Updated TACACS+ server profile: {profile.name}")
                else:
                    typer.echo(f"Created TACACS+ server profile: {profile.name}")
                loaded_count += 1

            except Exception as e:
                typer.echo(f"Error loading TACACS+ server profile: {str(e)}", err=True)

        typer.echo(f"\nProcessed {loaded_count} TACACS+ server profiles from {file}")

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading TACACS+ server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@backup_app.command("tacacs-server-profile")
def backup_tacacs_server_profile(
    folder: str | None = BACKUP_FOLDER_OPTION,
    snippet: str | None = BACKUP_SNIPPET_OPTION,
    device: str | None = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup TACACS+ server profiles to a YAML file.

    Examples
    --------
        scm backup identity tacacs-server-profile --folder Texas
        scm backup identity tacacs-server-profile --folder Texas --file tacacs.yaml

    """
    try:
        location_type, location_value = validate_location_params(folder, snippet, device)

        typer.echo(f"Fetching TACACS+ server profiles from {location_type} '{location_value}'...")
        kwargs = {location_type: location_value}
        profiles = scm_client.list_tacacs_server_profiles(**kwargs, exact_match=True)

        if not profiles:
            typer.echo(f"No TACACS+ server profiles found in {location_type} '{location_value}'")
            return

        backup_data: dict[str, list[dict[str, Any]]] = {"tacacs_server_profiles": []}
        for p in profiles:
            p_dict = p.copy()
            p_dict.pop("id", None)
            backup_data["tacacs_server_profiles"].append(p_dict)

        backup_data["tacacs_server_profiles"].sort(key=lambda x: x["name"])
        filename = file or Path(get_default_backup_filename("tacacs-server-profile", location_type, location_value))

        with open(filename, "w") as fh:
            yaml.dump(backup_data, fh, default_flow_style=False, sort_keys=False)

        typer.echo(f"Successfully backed up {len(backup_data['tacacs_server_profiles'])} TACACS+ server profiles to {filename}")

    except Exception as e:
        typer.echo(f"Error backing up TACACS+ server profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
