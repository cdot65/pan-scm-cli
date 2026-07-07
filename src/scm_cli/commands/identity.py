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

from ..utils import validate_location_params
from ..utils.decorators import handle_command_errors
from ..utils.output import OUTPUT_OPTION, OutputFormat, emit, error, info, success
from ..utils.sdk_client import scm_client
from ..utils.validators import (
    AuthenticationProfile,
    KerberosServerProfile,
    LdapServerProfile,
    RadiusServerProfile,
    SamlServerProfile,
    TacacsServerProfile,
)

# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

set_app = typer.Typer(help="Create or update identity configurations")
delete_app = typer.Typer(help="Remove identity configurations")
load_app = typer.Typer(help="Load identity configurations from YAML files")
show_app = typer.Typer(help="Display identity configurations")
backup_app = typer.Typer(help="Backup identity configurations to YAML files")

# =============================================================================================================================================================================================
# COMMAND OPTIONS
# =============================================================================================================================================================================================

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

# =============================================================================================================================================================================================
# HELPER FUNCTIONS
# =============================================================================================================================================================================================


def get_default_backup_filename(object_type: str, location_type: str, location_value: str) -> str:
    """Generate default backup filename based on object type and location."""
    safe_location = location_value.lower().replace("/", "-").replace(" ", "-")
    return f"{object_type}-{safe_location}.yaml"


# =============================================================================================================================================================================================
# AUTHENTICATION PROFILE COMMANDS
# =============================================================================================================================================================================================


@set_app.command("authentication-profile")
@handle_command_errors("creating authentication profile")
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
    location_type, location_value = validate_location_params(folder, snippet, device)

    # Parse JSON fields
    method_dict = json_lib.loads(method) if method else None
    lockout_dict = json_lib.loads(lockout) if lockout else None
    mfa_dict = json_lib.loads(multi_factor_auth) if multi_factor_auth else None
    sso_dict = json_lib.loads(single_sign_on) if single_sign_on else None

    try:
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
    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e

    sdk_data = profile.to_sdk_model()
    result = scm_client.create_authentication_profile(**sdk_data)

    action = result.get("__action__", "created")
    if action == "no_change":
        info(f"No changes detected for authentication profile: {name}")
    elif action == "updated":
        success(f"Updated authentication profile: {name} in {location_type} {location_value}")
    else:
        success(f"Created authentication profile: {name} in {location_type} {location_value}")
    return result


@show_app.command("authentication-profile")
@handle_command_errors("showing authentication profiles")
def show_authentication_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the authentication profile to show"),
    list_items: bool = typer.Option(False, "--list", "-l", help="List all authentication profiles"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display authentication profiles.

    Examples
    --------
        scm show identity authentication-profile --folder Texas --list
        scm show identity authentication-profile --folder Texas --name my-auth

    """
    if name:
        location_type, location_value = validate_location_params(folder, snippet, device)
        profile = scm_client.get_authentication_profile(name=name, **{location_type: location_value})
        emit(profile, output, title=f"Authentication Profile: {name}")
        return

    profiles = scm_client.list_authentication_profiles(folder=folder, snippet=snippet, device=device)
    location = folder or snippet or device
    title = f"Authentication Profiles in {location}" if location else "Authentication Profiles"
    emit(profiles, output, columns=["name", "user_domain", "method", "allow_list"], title=title)


@delete_app.command("authentication-profile")
@handle_command_errors("deleting authentication profile")
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
    location_type, location_value = validate_location_params(folder, snippet, device)
    if not force:
        typer.confirm(f"Delete authentication profile '{name}' from {location_type} '{location_value}'?", abort=True)
    result = scm_client.delete_authentication_profile(name=name, **{location_type: location_value})

    if result:
        success(f"Deleted authentication profile: {name} from {location_type} {location_value}")
    else:
        error(f"Authentication profile not found: {name}")
        raise typer.Exit(code=1)


@load_app.command("authentication-profile")
@handle_command_errors("loading authentication profiles")
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
    if not file.exists():
        error(f"Error: File '{file}' does not exist")
        raise typer.Exit(code=1)

    with file.open() as f:
        yaml_content = yaml.safe_load(f)

    if not yaml_content:
        error(f"Error: File '{file}' is empty or invalid")
        raise typer.Exit(code=1)

    profiles = yaml_content.get("authentication_profiles", [])
    if not profiles:
        info("No authentication profiles found in the YAML file.")
        return

    if dry_run:
        info("[DRY RUN] Would load the following authentication profiles:")
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
                info(f"No changes for authentication profile: {profile.name}")
            elif action == "updated":
                success(f"Updated authentication profile: {profile.name}")
            else:
                success(f"Created authentication profile: {profile.name}")
            loaded_count += 1

        except Exception as e:
            error(f"Error loading authentication profile: {str(e)}")

    success(f"Processed {loaded_count} authentication profiles from {file}")


@backup_app.command("authentication-profile")
@handle_command_errors("backing up authentication profiles")
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
    location_type, location_value = validate_location_params(folder, snippet, device)

    info(f"Fetching authentication profiles from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    profiles = scm_client.list_authentication_profiles(**kwargs, exact_match=True)

    if not profiles:
        info(f"No authentication profiles found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(backup_data['authentication_profiles'])} authentication profiles to {filename}")


# =============================================================================================================================================================================================
# KERBEROS SERVER PROFILE COMMANDS
# =============================================================================================================================================================================================


@set_app.command("kerberos-server-profile")
@handle_command_errors("creating Kerberos server profile")
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
    location_type, location_value = validate_location_params(folder, snippet, device)

    servers_list = json_lib.loads(servers) if servers else None

    try:
        profile = KerberosServerProfile(
            name=name,
            folder=folder,
            snippet=snippet,
            device=device,
            servers=servers_list,
        )
    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e

    sdk_data = profile.to_sdk_model()
    result = scm_client.create_kerberos_server_profile(**sdk_data)

    action = result.get("__action__", "created")
    if action == "no_change":
        info(f"No changes detected for Kerberos server profile: {name}")
    elif action == "updated":
        success(f"Updated Kerberos server profile: {name} in {location_type} {location_value}")
    else:
        success(f"Created Kerberos server profile: {name} in {location_type} {location_value}")
    return result


@show_app.command("kerberos-server-profile")
@handle_command_errors("showing Kerberos server profiles")
def show_kerberos_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the Kerberos server profile to show"),
    list_items: bool = typer.Option(False, "--list", "-l", help="List all Kerberos server profiles"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display Kerberos server profiles.

    Examples
    --------
        scm show identity kerberos-server-profile --folder Texas --list
        scm show identity kerberos-server-profile --folder Texas --name corp-kerberos

    """
    if name:
        location_type, location_value = validate_location_params(folder, snippet, device)
        profile = scm_client.get_kerberos_server_profile(name=name, **{location_type: location_value})
        emit(profile, output, title=f"Kerberos Server Profile: {name}")
        return

    profiles = scm_client.list_kerberos_server_profiles(folder=folder, snippet=snippet, device=device)
    location = folder or snippet or device
    title = f"Kerberos Server Profiles in {location}" if location else "Kerberos Server Profiles"
    emit(profiles, output, columns=["name", "server"], title=title)


@delete_app.command("kerberos-server-profile")
@handle_command_errors("deleting Kerberos server profile")
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
    location_type, location_value = validate_location_params(folder, snippet, device)
    if not force:
        typer.confirm(f"Delete Kerberos server profile '{name}' from {location_type} '{location_value}'?", abort=True)
    result = scm_client.delete_kerberos_server_profile(name=name, **{location_type: location_value})

    if result:
        success(f"Deleted Kerberos server profile: {name} from {location_type} {location_value}")
    else:
        error(f"Kerberos server profile not found: {name}")
        raise typer.Exit(code=1)


@load_app.command("kerberos-server-profile")
@handle_command_errors("loading Kerberos server profiles")
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
    if not file.exists():
        error(f"Error: File '{file}' does not exist")
        raise typer.Exit(code=1)

    with file.open() as f:
        yaml_content = yaml.safe_load(f)

    if not yaml_content:
        error(f"Error: File '{file}' is empty or invalid")
        raise typer.Exit(code=1)

    profiles = yaml_content.get("kerberos_server_profiles", [])
    if not profiles:
        info("No Kerberos server profiles found in the YAML file.")
        return

    if dry_run:
        info("[DRY RUN] Would load the following Kerberos server profiles:")
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
                info(f"No changes for Kerberos server profile: {profile.name}")
            elif action == "updated":
                success(f"Updated Kerberos server profile: {profile.name}")
            else:
                success(f"Created Kerberos server profile: {profile.name}")
            loaded_count += 1

        except Exception as e:
            error(f"Error loading Kerberos server profile: {str(e)}")

    success(f"Processed {loaded_count} Kerberos server profiles from {file}")


@backup_app.command("kerberos-server-profile")
@handle_command_errors("backing up Kerberos server profiles")
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
    location_type, location_value = validate_location_params(folder, snippet, device)

    info(f"Fetching Kerberos server profiles from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    profiles = scm_client.list_kerberos_server_profiles(**kwargs, exact_match=True)

    if not profiles:
        info(f"No Kerberos server profiles found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(backup_data['kerberos_server_profiles'])} Kerberos server profiles to {filename}")


# =============================================================================================================================================================================================
# LDAP SERVER PROFILE COMMANDS
# =============================================================================================================================================================================================


@set_app.command("ldap-server-profile")
@handle_command_errors("creating LDAP server profile")
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
    location_type, location_value = validate_location_params(folder, snippet, device)

    servers_list = json_lib.loads(servers) if servers else None

    try:
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
    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e

    sdk_data = profile.to_sdk_model()
    result = scm_client.create_ldap_server_profile(**sdk_data)

    action = result.get("__action__", "created")
    if action == "no_change":
        info(f"No changes detected for LDAP server profile: {name}")
    elif action == "updated":
        success(f"Updated LDAP server profile: {name} in {location_type} {location_value}")
    else:
        success(f"Created LDAP server profile: {name} in {location_type} {location_value}")
    return result


@show_app.command("ldap-server-profile")
@handle_command_errors("showing LDAP server profiles")
def show_ldap_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the LDAP server profile to show"),
    list_items: bool = typer.Option(False, "--list", "-l", help="List all LDAP server profiles"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display LDAP server profiles.

    Examples
    --------
        scm show identity ldap-server-profile --folder Texas --list
        scm show identity ldap-server-profile --folder Texas --name corp-ldap

    """
    if name:
        location_type, location_value = validate_location_params(folder, snippet, device)
        profile = scm_client.get_ldap_server_profile(name=name, **{location_type: location_value})
        emit(profile, output, title=f"LDAP Server Profile: {name}")
        return

    profiles = scm_client.list_ldap_server_profiles(folder=folder, snippet=snippet, device=device)
    location = folder or snippet or device
    title = f"LDAP Server Profiles in {location}" if location else "LDAP Server Profiles"
    emit(profiles, output, columns=["name", "ldap_type", "base", "server"], title=title)


@delete_app.command("ldap-server-profile")
@handle_command_errors("deleting LDAP server profile")
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
    location_type, location_value = validate_location_params(folder, snippet, device)
    if not force:
        typer.confirm(f"Delete LDAP server profile '{name}' from {location_type} '{location_value}'?", abort=True)
    result = scm_client.delete_ldap_server_profile(name=name, **{location_type: location_value})

    if result:
        success(f"Deleted LDAP server profile: {name} from {location_type} {location_value}")
    else:
        error(f"LDAP server profile not found: {name}")
        raise typer.Exit(code=1)


@load_app.command("ldap-server-profile")
@handle_command_errors("loading LDAP server profiles")
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
    if not file.exists():
        error(f"Error: File '{file}' does not exist")
        raise typer.Exit(code=1)

    with file.open() as f:
        yaml_content = yaml.safe_load(f)

    if not yaml_content:
        error(f"Error: File '{file}' is empty or invalid")
        raise typer.Exit(code=1)

    profiles = yaml_content.get("ldap_server_profiles", [])
    if not profiles:
        info("No LDAP server profiles found in the YAML file.")
        return

    if dry_run:
        info("[DRY RUN] Would load the following LDAP server profiles:")
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
                info(f"No changes for LDAP server profile: {profile.name}")
            elif action == "updated":
                success(f"Updated LDAP server profile: {profile.name}")
            else:
                success(f"Created LDAP server profile: {profile.name}")
            loaded_count += 1

        except Exception as e:
            error(f"Error loading LDAP server profile: {str(e)}")

    success(f"Processed {loaded_count} LDAP server profiles from {file}")


@backup_app.command("ldap-server-profile")
@handle_command_errors("backing up LDAP server profiles")
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
    location_type, location_value = validate_location_params(folder, snippet, device)

    info(f"Fetching LDAP server profiles from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    profiles = scm_client.list_ldap_server_profiles(**kwargs, exact_match=True)

    if not profiles:
        info(f"No LDAP server profiles found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(backup_data['ldap_server_profiles'])} LDAP server profiles to {filename}")


# =============================================================================================================================================================================================
# RADIUS SERVER PROFILE COMMANDS
# =============================================================================================================================================================================================


@set_app.command("radius-server-profile")
@handle_command_errors("creating RADIUS server profile")
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
    location_type, location_value = validate_location_params(folder, snippet, device)

    servers_list = json_lib.loads(servers) if servers else None
    protocol_dict = json_lib.loads(protocol) if protocol else None

    try:
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
    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e

    sdk_data = profile.to_sdk_model()
    result = scm_client.create_radius_server_profile(**sdk_data)

    action = result.get("__action__", "created")
    if action == "no_change":
        info(f"No changes detected for RADIUS server profile: {name}")
    elif action == "updated":
        success(f"Updated RADIUS server profile: {name} in {location_type} {location_value}")
    else:
        success(f"Created RADIUS server profile: {name} in {location_type} {location_value}")
    return result


@show_app.command("radius-server-profile")
@handle_command_errors("showing RADIUS server profiles")
def show_radius_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the RADIUS server profile to show"),
    list_items: bool = typer.Option(False, "--list", "-l", help="List all RADIUS server profiles"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display RADIUS server profiles.

    Examples
    --------
        scm show identity radius-server-profile --folder Texas --list
        scm show identity radius-server-profile --folder Texas --name corp-radius

    """
    if name:
        location_type, location_value = validate_location_params(folder, snippet, device)
        profile = scm_client.get_radius_server_profile(name=name, **{location_type: location_value})
        emit(profile, output, title=f"RADIUS Server Profile: {name}")
        return

    profiles = scm_client.list_radius_server_profiles(folder=folder, snippet=snippet, device=device)
    location = folder or snippet or device
    title = f"RADIUS Server Profiles in {location}" if location else "RADIUS Server Profiles"
    emit(profiles, output, columns=["name", "server", "timeout", "retries"], title=title)


@delete_app.command("radius-server-profile")
@handle_command_errors("deleting RADIUS server profile")
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
    location_type, location_value = validate_location_params(folder, snippet, device)
    if not force:
        typer.confirm(f"Delete RADIUS server profile '{name}' from {location_type} '{location_value}'?", abort=True)
    result = scm_client.delete_radius_server_profile(name=name, **{location_type: location_value})

    if result:
        success(f"Deleted RADIUS server profile: {name} from {location_type} {location_value}")
    else:
        error(f"RADIUS server profile not found: {name}")
        raise typer.Exit(code=1)


@load_app.command("radius-server-profile")
@handle_command_errors("loading RADIUS server profiles")
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
    if not file.exists():
        error(f"Error: File '{file}' does not exist")
        raise typer.Exit(code=1)

    with file.open() as f:
        yaml_content = yaml.safe_load(f)

    if not yaml_content:
        error(f"Error: File '{file}' is empty or invalid")
        raise typer.Exit(code=1)

    profiles = yaml_content.get("radius_server_profiles", [])
    if not profiles:
        info("No RADIUS server profiles found in the YAML file.")
        return

    if dry_run:
        info("[DRY RUN] Would load the following RADIUS server profiles:")
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
                info(f"No changes for RADIUS server profile: {profile.name}")
            elif action == "updated":
                success(f"Updated RADIUS server profile: {profile.name}")
            else:
                success(f"Created RADIUS server profile: {profile.name}")
            loaded_count += 1

        except Exception as e:
            error(f"Error loading RADIUS server profile: {str(e)}")

    success(f"Processed {loaded_count} RADIUS server profiles from {file}")


@backup_app.command("radius-server-profile")
@handle_command_errors("backing up RADIUS server profiles")
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
    location_type, location_value = validate_location_params(folder, snippet, device)

    info(f"Fetching RADIUS server profiles from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    profiles = scm_client.list_radius_server_profiles(**kwargs, exact_match=True)

    if not profiles:
        info(f"No RADIUS server profiles found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(backup_data['radius_server_profiles'])} RADIUS server profiles to {filename}")


# =============================================================================================================================================================================================
# SAML SERVER PROFILE COMMANDS
# =============================================================================================================================================================================================


@set_app.command("saml-server-profile")
@handle_command_errors("creating SAML server profile")
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
    location_type, location_value = validate_location_params(folder, snippet, device)

    try:
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
    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e

    sdk_data = profile.to_sdk_model()
    result = scm_client.create_saml_server_profile(**sdk_data)

    action = result.get("__action__", "created")
    if action == "no_change":
        info(f"No changes detected for SAML server profile: {name}")
    elif action == "updated":
        success(f"Updated SAML server profile: {name} in {location_type} {location_value}")
    else:
        success(f"Created SAML server profile: {name} in {location_type} {location_value}")
    return result


@show_app.command("saml-server-profile")
@handle_command_errors("showing SAML server profiles")
def show_saml_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the SAML server profile to show"),
    list_items: bool = typer.Option(False, "--list", "-l", help="List all SAML server profiles"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display SAML server profiles.

    Examples
    --------
        scm show identity saml-server-profile --folder Texas --list
        scm show identity saml-server-profile --folder Texas --name corp-saml

    """
    if name:
        location_type, location_value = validate_location_params(folder, snippet, device)
        profile = scm_client.get_saml_server_profile(name=name, **{location_type: location_value})
        emit(profile, output, title=f"SAML Server Profile: {name}")
        return

    profiles = scm_client.list_saml_server_profiles(folder=folder, snippet=snippet, device=device)
    location = folder or snippet or device
    title = f"SAML Server Profiles in {location}" if location else "SAML Server Profiles"
    emit(profiles, output, columns=["name", "entity_id", "sso_url", "sso_bindings"], title=title)


@delete_app.command("saml-server-profile")
@handle_command_errors("deleting SAML server profile")
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
    location_type, location_value = validate_location_params(folder, snippet, device)
    if not force:
        typer.confirm(f"Delete SAML server profile '{name}' from {location_type} '{location_value}'?", abort=True)
    result = scm_client.delete_saml_server_profile(name=name, **{location_type: location_value})

    if result:
        success(f"Deleted SAML server profile: {name} from {location_type} {location_value}")
    else:
        error(f"SAML server profile not found: {name}")
        raise typer.Exit(code=1)


@load_app.command("saml-server-profile")
@handle_command_errors("loading SAML server profiles")
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
    if not file.exists():
        error(f"Error: File '{file}' does not exist")
        raise typer.Exit(code=1)

    with file.open() as f:
        yaml_content = yaml.safe_load(f)

    if not yaml_content:
        error(f"Error: File '{file}' is empty or invalid")
        raise typer.Exit(code=1)

    profiles = yaml_content.get("saml_server_profiles", [])
    if not profiles:
        info("No SAML server profiles found in the YAML file.")
        return

    if dry_run:
        info("[DRY RUN] Would load the following SAML server profiles:")
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
                info(f"No changes for SAML server profile: {profile.name}")
            elif action == "updated":
                success(f"Updated SAML server profile: {profile.name}")
            else:
                success(f"Created SAML server profile: {profile.name}")
            loaded_count += 1

        except Exception as e:
            error(f"Error loading SAML server profile: {str(e)}")

    success(f"Processed {loaded_count} SAML server profiles from {file}")


@backup_app.command("saml-server-profile")
@handle_command_errors("backing up SAML server profiles")
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
    location_type, location_value = validate_location_params(folder, snippet, device)

    info(f"Fetching SAML server profiles from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    profiles = scm_client.list_saml_server_profiles(**kwargs, exact_match=True)

    if not profiles:
        info(f"No SAML server profiles found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(backup_data['saml_server_profiles'])} SAML server profiles to {filename}")


# =============================================================================================================================================================================================
# TACACS+ SERVER PROFILE COMMANDS
# =============================================================================================================================================================================================


@set_app.command("tacacs-server-profile")
@handle_command_errors("creating TACACS+ server profile")
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
    location_type, location_value = validate_location_params(folder, snippet, device)

    servers_list = json_lib.loads(servers) if servers else None

    try:
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
    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e

    sdk_data = profile.to_sdk_model()
    result = scm_client.create_tacacs_server_profile(**sdk_data)

    action = result.get("__action__", "created")
    if action == "no_change":
        info(f"No changes detected for TACACS+ server profile: {name}")
    elif action == "updated":
        success(f"Updated TACACS+ server profile: {name} in {location_type} {location_value}")
    else:
        success(f"Created TACACS+ server profile: {name} in {location_type} {location_value}")
    return result


@show_app.command("tacacs-server-profile")
@handle_command_errors("showing TACACS+ server profiles")
def show_tacacs_server_profile(
    folder: str | None = FOLDER_OPTION,
    snippet: str | None = SNIPPET_OPTION,
    device: str | None = DEVICE_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the TACACS+ server profile to show"),
    list_items: bool = typer.Option(False, "--list", "-l", help="List all TACACS+ server profiles"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display TACACS+ server profiles.

    Examples
    --------
        scm show identity tacacs-server-profile --folder Texas --list
        scm show identity tacacs-server-profile --folder Texas --name corp-tacacs

    """
    if name:
        location_type, location_value = validate_location_params(folder, snippet, device)
        profile = scm_client.get_tacacs_server_profile(name=name, **{location_type: location_value})
        emit(profile, output, title=f"TACACS+ Server Profile: {name}")
        return

    profiles = scm_client.list_tacacs_server_profiles(folder=folder, snippet=snippet, device=device)
    location = folder or snippet or device
    title = f"TACACS+ Server Profiles in {location}" if location else "TACACS+ Server Profiles"
    emit(profiles, output, columns=["name", "protocol", "server", "timeout"], title=title)


@delete_app.command("tacacs-server-profile")
@handle_command_errors("deleting TACACS+ server profile")
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
    location_type, location_value = validate_location_params(folder, snippet, device)
    if not force:
        typer.confirm(f"Delete TACACS+ server profile '{name}' from {location_type} '{location_value}'?", abort=True)
    result = scm_client.delete_tacacs_server_profile(name=name, **{location_type: location_value})

    if result:
        success(f"Deleted TACACS+ server profile: {name} from {location_type} {location_value}")
    else:
        error(f"TACACS+ server profile not found: {name}")
        raise typer.Exit(code=1)


@load_app.command("tacacs-server-profile")
@handle_command_errors("loading TACACS+ server profiles")
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
    if not file.exists():
        error(f"Error: File '{file}' does not exist")
        raise typer.Exit(code=1)

    with file.open() as f:
        yaml_content = yaml.safe_load(f)

    if not yaml_content:
        error(f"Error: File '{file}' is empty or invalid")
        raise typer.Exit(code=1)

    profiles = yaml_content.get("tacacs_server_profiles", [])
    if not profiles:
        info("No TACACS+ server profiles found in the YAML file.")
        return

    if dry_run:
        info("[DRY RUN] Would load the following TACACS+ server profiles:")
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
                info(f"No changes for TACACS+ server profile: {profile.name}")
            elif action == "updated":
                success(f"Updated TACACS+ server profile: {profile.name}")
            else:
                success(f"Created TACACS+ server profile: {profile.name}")
            loaded_count += 1

        except Exception as e:
            error(f"Error loading TACACS+ server profile: {str(e)}")

    success(f"Processed {loaded_count} TACACS+ server profiles from {file}")


@backup_app.command("tacacs-server-profile")
@handle_command_errors("backing up TACACS+ server profiles")
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
    location_type, location_value = validate_location_params(folder, snippet, device)

    info(f"Fetching TACACS+ server profiles from {location_type} '{location_value}'...")
    kwargs = {location_type: location_value}
    profiles = scm_client.list_tacacs_server_profiles(**kwargs, exact_match=True)

    if not profiles:
        info(f"No TACACS+ server profiles found in {location_type} '{location_value}'")
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

    success(f"Successfully backed up {len(backup_data['tacacs_server_profiles'])} TACACS+ server profiles to {filename}")
