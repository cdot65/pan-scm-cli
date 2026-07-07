"""Mobile agent module commands for scm.

This module implements commands for mobile agent configurations
including agent versions (read-only) and auth settings (full CRUD).
"""

from pathlib import Path
from typing import Any

import typer
import yaml
from pydantic import ValidationError

from ..utils import validate_location_params
from ..utils.bulk import run_bulk
from ..utils.config import load_from_yaml
from ..utils.decorators import handle_command_errors
from ..utils.output import OUTPUT_OPTION, OutputFormat, emit, error, info, success
from ..utils.sdk_client import scm_client
from ..utils.validators import (
    AgentProfile,
    AuthSetting,
    ForwardingProfile,
    ForwardingProfileDestination,
    ForwardingProfileRegionalAndCustomProxy,
    ForwardingProfileSourceApplication,
    ForwardingProfileUserLocation,
    GlobalSetting,
    InfrastructureSetting,
    TunnelProfile,
)

# =============================================================================================================================================================================================
# HELPER FUNCTIONS
# =============================================================================================================================================================================================


def get_default_backup_filename(object_type: str, location_type: str, location_value: str) -> str:
    """Generate default backup filename based on object type and location."""
    safe_location = location_value.lower().replace("/", "-").replace(" ", "-")
    return f"{object_type}-{safe_location}.yaml"


def _bulk_load_items(items: list[dict], apply_item, label: str) -> list[dict]:
    """Apply load items concurrently and report outcomes in input order.

    ``apply_item`` validates and creates a single item, returning the SDK
    result dict. Per-item failures are reported with the same wording as the
    previous sequential loop and skipped.
    """
    results = []
    created_count = 0
    updated_count = 0
    no_change_count = 0

    for item_data, result, exc in run_bulk(items, apply_item):
        if exc is not None:
            error(f"Error loading {label} '{item_data.get('name', 'unknown')}': {str(exc)}")
            continue

        action = result.pop("__action__", "created")
        if action == "created":
            created_count += 1
            success(f"Created {label}: {result.get('name', 'N/A')}")
        elif action == "updated":
            updated_count += 1
            success(f"Updated {label}: {result.get('name', 'N/A')}")
        elif action == "no_change":
            no_change_count += 1
            info(f"No changes needed for {label}: {result.get('name', 'N/A')}")

        results.append(result)

    # Summary
    info(f"Summary: {created_count} created, {updated_count} updated, {no_change_count} unchanged")

    return results


# =============================================================================================================================================================================================
# TYPER APP CONFIGURATION
# =============================================================================================================================================================================================

# Create app groups for each action type
set_app = typer.Typer(help="Create or update mobile agent configurations")
delete_app = typer.Typer(help="Remove mobile agent configurations")
load_app = typer.Typer(help="Load mobile agent configurations from YAML files")
show_app = typer.Typer(help="Display mobile agent configurations")
backup_app = typer.Typer(help="Backup mobile agent configurations to YAML files")

# =============================================================================================================================================================================================
# COMMAND OPTIONS
# =============================================================================================================================================================================================

# Common options
FOLDER_OPTION = typer.Option(
    None,
    "--folder",
    help="Folder path for the resource",
)
NAME_OPTION = typer.Option(
    None,
    "--name",
    help="Name of the resource",
)
DESCRIPTION_OPTION = typer.Option(
    None,
    "--description",
    help="Description of the resource",
)
FILE_OPTION = typer.Option(
    ...,
    "--file",
    help="YAML file to load configurations from",
)
DRY_RUN_OPTION = typer.Option(
    False,
    "--dry-run",
    help="Simulate execution without applying changes",
)

# Backup command options
BACKUP_FOLDER_OPTION = typer.Option(
    None,
    "--folder",
    help="Folder to backup configurations from",
)
BACKUP_SNIPPET_OPTION = typer.Option(
    None,
    "--snippet",
    help="Snippet to backup configurations from",
)
BACKUP_DEVICE_OPTION = typer.Option(
    None,
    "--device",
    help="Device to backup configurations from",
)
BACKUP_FILE_OPTION = typer.Option(
    None,
    "--file",
    help="Output file path (optional, defaults to {type}-{location}.yaml)",
)

# Container override options for load commands
LOAD_FOLDER_OPTION = typer.Option(
    None,
    "--folder",
    help="Override folder location for all objects",
)
LOAD_SNIPPET_OPTION = typer.Option(
    None,
    "--snippet",
    help="Override snippet location for all objects",
)
LOAD_DEVICE_OPTION = typer.Option(
    None,
    "--device",
    help="Override device location for all objects",
)

# Auth Setting specific options
AUTHENTICATION_PROFILE_OPTION = typer.Option(
    None,
    "--authentication-profile",
    help="Authentication profile name (required for create)",
)
OS_OPTION = typer.Option(
    None,
    "--os",
    help="Operating system (e.g., Any, Windows, macOS, Linux, iOS, Android, ChromeOS)",
)
USER_CREDENTIAL_OR_CLIENT_CERT_REQUIRED_OPTION = typer.Option(
    None,
    "--user-credential-or-client-cert-required",
    help="Whether user credential or client certificate is required",
)


# =============================================================================================================================================================================================
# AGENT VERSION COMMANDS (READ-ONLY)
# =============================================================================================================================================================================================


@show_app.command("agent-version")
@handle_command_errors("showing agent version")
def show_agent_version(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the agent version to show"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display agent versions.

    Examples
    --------
        # List all agent versions in a folder (default behavior)
        scm show mobile-agent agent-version --folder "Mobile Users"

        # Show a specific agent version by name
        scm show mobile-agent agent-version --folder "Mobile Users" --name "5.2.0"

    """
    if name:
        # Get a specific agent version by name
        version = scm_client.get_agent_version(folder=folder, name=name)
        emit(version, output, title=f"Agent Version: {version.get('name', 'N/A')}")
        return version

    # Default: list all agent versions
    versions = scm_client.list_agent_versions(folder=folder)
    emit(
        versions,
        output,
        columns=["name", "version", "platform", "release_date"],
        title=f"Agent Versions in folder '{folder}'",
    )
    return versions


# =============================================================================================================================================================================================
# AUTH SETTING COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("auth-setting")
@handle_command_errors("backing up auth settings")
def backup_auth_setting(
    folder: str = BACKUP_FOLDER_OPTION,
    snippet: str = BACKUP_SNIPPET_OPTION,
    device: str = BACKUP_DEVICE_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup all auth settings from a specified location to a YAML file.

    Examples
    --------
        # Backup from a folder
        scm backup mobile-agent auth-setting --folder "Mobile Users"

        # Backup with custom output file
        scm backup mobile-agent auth-setting --folder "Mobile Users" --file auth-settings-backup.yaml

    """
    # Validate location parameters
    location_type, location_value = validate_location_params(folder, snippet, device)

    # List all auth settings in the location with exact_match=True
    kwargs = {location_type: location_value}
    auth_settings = scm_client.list_auth_settings(**kwargs, exact_match=True)

    if not auth_settings:
        info(f"No auth settings found in {location_type} '{location_value}'")
        return

    # Convert SDK models to dictionaries, excluding unset values
    backup_data = []
    for setting in auth_settings:
        setting_dict = {k: v for k, v in setting.items() if v is not None}
        # Remove system fields that shouldn't be in backup
        setting_dict.pop("id", None)
        backup_data.append(setting_dict)

    # Create the YAML structure
    yaml_data = {"auth_settings": backup_data}

    # Generate filename
    if file is None:
        file = Path(get_default_backup_filename("auth-setting", location_type, location_value))

    # Write to YAML file
    with file.open("w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(backup_data)} auth settings to {file}")
    return str(file)


@delete_app.command("auth-setting")
@handle_command_errors("deleting auth setting")
def delete_auth_setting(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete an auth setting.

    Examples
    --------
        scm delete mobile-agent auth-setting --folder "Mobile Users" --name "saml-auth"

    """
    if not force:
        typer.confirm(f"Delete auth setting '{name}' from folder '{folder}'?", abort=True)
    result = scm_client.delete_auth_setting(folder=folder, name=name)
    if result:
        success(f"Deleted auth setting: {name} from folder {folder}")
    return result


@load_app.command("auth-setting")
@handle_command_errors("loading auth settings")
def load_auth_setting(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
    """Load auth settings from a YAML file.

    Examples
    --------
        # Load from file with original locations
        scm load mobile-agent auth-setting --file config/auth_settings.yml

        # Load with folder override
        scm load mobile-agent auth-setting --file config/auth_settings.yml --folder "Mobile Users"

    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(str(file), "auth_settings")

        if dry_run:
            info("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["auth_settings"]))
            return None

        def _apply(setting_data: dict):
            # Apply container override if specified
            if folder:
                setting_data["folder"] = folder
                setting_data.pop("snippet", None)
                setting_data.pop("device", None)
            elif snippet:
                setting_data["snippet"] = snippet
                setting_data.pop("folder", None)
                setting_data.pop("device", None)
            elif device:
                setting_data["device"] = device
                setting_data.pop("folder", None)
                setting_data.pop("snippet", None)
            # Validate using the Pydantic model
            item = AuthSetting(**setting_data)
            sdk_data = item.to_sdk_model()

            # Create via SDK client
            return scm_client.create_auth_setting(**sdk_data)

        return _bulk_load_items(config["auth_settings"], _apply, "auth setting")

    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e


@set_app.command("auth-setting")
@handle_command_errors("creating/updating auth setting")
def set_auth_setting(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    authentication_profile: str | None = AUTHENTICATION_PROFILE_OPTION,
    os: str | None = OS_OPTION,
    user_credential_or_client_cert_required: bool | None = USER_CREDENTIAL_OR_CLIENT_CERT_REQUIRED_OPTION,
):
    r"""Create or update an auth setting.

    Examples
    --------
        scm set mobile-agent auth-setting \
        --folder "Mobile Users" \
        --name "saml-auth" \
        --authentication-profile "best-practice" \
        --os Any

    """
    # Build auth setting data
    setting_data: dict[str, Any] = {
        "name": name,
    }

    if folder:
        setting_data["folder"] = folder
    if description is not None:
        setting_data["description"] = description
    if authentication_profile is not None:
        setting_data["authentication_profile"] = authentication_profile
    if os is not None:
        setting_data["os"] = os
    if user_credential_or_client_cert_required is not None:
        setting_data["user_credential_or_client_cert_required"] = user_credential_or_client_cert_required

    # Validate using the Pydantic model
    try:
        auth_setting = AuthSetting(**setting_data)
        sdk_data = auth_setting.to_sdk_model()
    except ValidationError as e:
        error(f"Validation error: {str(e)}")
        raise typer.Exit(code=1) from e

    # Call the SDK client
    result = scm_client.create_auth_setting(**sdk_data)

    # Get the action performed
    action = result.pop("__action__", "created")

    if action == "created":
        success(f"Created auth setting: {result.get('name', name)} in folder {result.get('folder', folder)}")
    elif action == "updated":
        success(f"Updated auth setting: {result.get('name', name)} in folder {result.get('folder', folder)}")
    elif action == "no_change":
        info(f"No changes needed for auth setting: {result.get('name', name)} in folder {result.get('folder', folder)}")

    return result


@show_app.command("auth-setting")
@handle_command_errors("showing auth setting")
def show_auth_setting(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the auth setting to show"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display auth settings.

    Examples
    --------
        # List all auth settings in a folder (default behavior)
        scm show mobile-agent auth-setting --folder "Mobile Users"

        # Show a specific auth setting by name
        scm show mobile-agent auth-setting --folder "Mobile Users" --name "saml-auth"

    """
    if name:
        # Get a specific auth setting by name
        setting = scm_client.get_auth_setting(folder=folder, name=name)
        emit(setting, output, title=f"Auth Setting: {setting.get('name', 'N/A')}")
        return setting

    # Default: list all auth settings
    settings_list = scm_client.list_auth_settings(folder=folder)
    emit(
        settings_list,
        output,
        columns=["name", "authentication_profile", "os", "description"],
        title=f"Auth Settings in folder '{folder}'",
    )
    return settings_list


# =============================================================================================================================================================================================
# FORWARDING PROFILE COMMANDS (GlobalProtect, SDK 0.15.0)
# =============================================================================================================================================================================================

# Forwarding profile specific options
PROFILE_TYPE_OPTION = typer.Option(
    None,
    "--profile-type",
    help="Profile type: pac-file, global-protect-proxy, or ztna-agent",
)
DEFINITION_METHOD_OPTION = typer.Option(
    None,
    "--definition-method",
    help="How the profile is defined: rules or pac-file",
)
PAC_UPLOAD_OPTION = typer.Option(
    None,
    "--pac-upload/--no-pac-upload",
    help="Whether the user uploads a PAC file",
)
PROFILE_ID_OPTION = typer.Option(
    None,
    "--id",
    help="UUID of the resource (alternative to --name)",
)

_PROFILE_TYPE_KEY_MAP = {
    "pac-file": "pac_file",
    "global-protect-proxy": "global_protect_proxy",
    "ztna-agent": "ztna_agent",
}


@backup_app.command("forwarding-profile")
@handle_command_errors("backing up forwarding profiles")
def backup_forwarding_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup all forwarding profiles from a folder to a YAML file.

    Examples
    --------
        scm backup mobile-agent forwarding-profile --folder "Mobile Users"

    """
    if not folder:
        folder = "Mobile Users"

    profiles = scm_client.list_forwarding_profiles(folder=folder)

    if not profiles:
        info(f"No forwarding profiles found in folder '{folder}'")
        return None

    backup_data = []
    for profile in profiles:
        profile_dict = {k: v for k, v in profile.items() if v is not None}
        profile_dict.pop("id", None)
        backup_data.append(profile_dict)

    yaml_data = {"forwarding_profiles": backup_data}

    if file is None:
        file = Path(get_default_backup_filename("forwarding-profile", "folder", folder))

    with file.open("w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(backup_data)} forwarding profiles to {file}")
    return str(file)


@delete_app.command("forwarding-profile")
@handle_command_errors("deleting forwarding profile")
def delete_forwarding_profile(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    profile_id: str | None = PROFILE_ID_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a forwarding profile by name or UUID.

    Examples
    --------
        scm delete mobile-agent forwarding-profile --folder "Mobile Users" --name "ztna-profile"

        scm delete mobile-agent forwarding-profile --id "123e4567-e89b-12d3-a456-426655440000"

    """
    identifier = profile_id or name
    if not force:
        typer.confirm(f"Delete forwarding profile '{identifier}'?", abort=True)
    result = scm_client.delete_forwarding_profile(folder=folder, name=name, profile_id=profile_id)
    if result:
        success(f"Deleted forwarding profile: {identifier}")
    return result


@load_app.command("forwarding-profile")
@handle_command_errors("loading forwarding profiles")
def load_forwarding_profile(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
):
    """Load forwarding profiles from a YAML file.

    Complex profile configurations (forwarding rules, block rules) are expressed in
    YAML under the `type` key: {pac_file | global_protect_proxy | ztna_agent: {...}}.

    Examples
    --------
        scm load mobile-agent forwarding-profile --file config/forwarding_profiles.yml

    """
    try:
        config = load_from_yaml(str(file), "forwarding_profiles")

        if dry_run:
            info("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["forwarding_profiles"]))
            return None

        def _apply(profile_data: dict):
            # Apply folder override if specified
            if folder:
                profile_data["folder"] = folder
            # Validate using the Pydantic model
            item = ForwardingProfile(**profile_data)
            sdk_data = item.to_sdk_model()

            # Create via SDK client
            return scm_client.create_forwarding_profile(**sdk_data)

        return _bulk_load_items(config["forwarding_profiles"], _apply, "forwarding profile")

    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e


@set_app.command("forwarding-profile")
@handle_command_errors("creating/updating forwarding profile")
def set_forwarding_profile(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    definition_method: str | None = DEFINITION_METHOD_OPTION,
    profile_type: str | None = PROFILE_TYPE_OPTION,
    pac_upload: bool | None = PAC_UPLOAD_OPTION,
):
    r"""Create or update a forwarding profile.

    The folder must be "Mobile Users" (the only folder supported by the API).
    Use --profile-type to select the profile flavor; full forwarding/block rules
    are supported via `scm load mobile-agent forwarding-profile --file ...`.

    Examples
    --------
        scm set mobile-agent forwarding-profile \
        --folder "Mobile Users" \
        --name "ztna-profile" \
        --profile-type ztna-agent

    """
    profile_data: dict[str, Any] = {
        "name": name,
    }

    if folder:
        profile_data["folder"] = folder
    if description is not None:
        profile_data["description"] = description
    if definition_method is not None:
        profile_data["definition_method"] = definition_method
    if profile_type is not None:
        type_key = _PROFILE_TYPE_KEY_MAP.get(profile_type)
        if type_key is None:
            error(f"Error: --profile-type must be one of: {', '.join(sorted(_PROFILE_TYPE_KEY_MAP))}")
            raise typer.Exit(code=1)
        type_config: dict[str, Any] = {}
        if pac_upload is not None:
            type_config["pac_upload"] = pac_upload
        profile_data["type"] = {type_key: type_config}

    try:
        profile = ForwardingProfile(**profile_data)
        sdk_data = profile.to_sdk_model()
    except ValidationError as e:
        error(f"Validation error: {str(e)}")
        raise typer.Exit(code=1) from e

    result = scm_client.create_forwarding_profile(**sdk_data)

    action = result.pop("__action__", "created")

    if action == "created":
        success(f"Created forwarding profile: {result.get('name', name)}")
    elif action == "updated":
        success(f"Updated forwarding profile: {result.get('name', name)}")
    elif action == "no_change":
        info(f"No changes needed for forwarding profile: {result.get('name', name)}")

    return result


@show_app.command("forwarding-profile")
@handle_command_errors("showing forwarding profile")
def show_forwarding_profile(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the forwarding profile to show"),
    profile_id: str | None = PROFILE_ID_OPTION,
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display forwarding profiles.

    Examples
    --------
        # List all forwarding profiles (default behavior)
        scm show mobile-agent forwarding-profile --folder "Mobile Users"

        # Show a specific forwarding profile by name
        scm show mobile-agent forwarding-profile --folder "Mobile Users" --name "ztna-profile"

        # Show a specific forwarding profile by UUID
        scm show mobile-agent forwarding-profile --id "123e4567-e89b-12d3-a456-426655440000"

    """
    if profile_id or name:
        profile = scm_client.get_forwarding_profile(folder=folder, name=name, profile_id=profile_id)
        emit(profile, output, title=f"Forwarding Profile: {profile.get('name', 'N/A')}")
        return profile

    profiles = scm_client.list_forwarding_profiles(folder=folder)
    emit(
        profiles,
        output,
        columns=["name", "definition_method", "type", "description", "id"],
        title=f"Forwarding Profiles in folder '{folder or 'Mobile Users'}'",
    )
    return profiles


# =============================================================================================================================================================================================
# FORWARDING PROFILE DESTINATION COMMANDS (GlobalProtect, SDK 0.15.0)
# =============================================================================================================================================================================================

# Forwarding profile destination specific options
FQDN_OPTION = typer.Option(
    None,
    "--fqdn",
    help="FQDN entry as 'host' or 'host:port' (repeatable)",
)
IP_ADDRESS_OPTION = typer.Option(
    None,
    "--ip-address",
    help="IP entry as 'ip', 'ip/prefix', or 'ip:port' (repeatable)",
)


@backup_app.command("forwarding-profile-destination")
@handle_command_errors("backing up forwarding profile destinations")
def backup_forwarding_profile_destination(
    folder: str = BACKUP_FOLDER_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup all forwarding profile destinations from a folder to a YAML file.

    Examples
    --------
        scm backup mobile-agent forwarding-profile-destination --folder "Mobile Users"

    """
    if not folder:
        folder = "Mobile Users"

    destinations = scm_client.list_forwarding_profile_destinations(folder=folder)

    if not destinations:
        info(f"No forwarding profile destinations found in folder '{folder}'")
        return None

    backup_data = []
    for destination in destinations:
        destination_dict = {k: v for k, v in destination.items() if v is not None}
        destination_dict.pop("id", None)
        backup_data.append(destination_dict)

    yaml_data = {"forwarding_profile_destinations": backup_data}

    if file is None:
        file = Path(get_default_backup_filename("forwarding-profile-destination", "folder", folder))

    with file.open("w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(backup_data)} forwarding profile destinations to {file}")
    return str(file)


@delete_app.command("forwarding-profile-destination")
@handle_command_errors("deleting forwarding profile destination")
def delete_forwarding_profile_destination(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    destination_id: str | None = PROFILE_ID_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a forwarding profile destination by name or UUID.

    Examples
    --------
        scm delete mobile-agent forwarding-profile-destination --folder "Mobile Users" --name "internal-apps"

    """
    identifier = destination_id or name
    if not force:
        typer.confirm(f"Delete forwarding profile destination '{identifier}'?", abort=True)
    result = scm_client.delete_forwarding_profile_destination(folder=folder, name=name, destination_id=destination_id)
    if result:
        success(f"Deleted forwarding profile destination: {identifier}")
    return result


@load_app.command("forwarding-profile-destination")
@handle_command_errors("loading forwarding profile destinations")
def load_forwarding_profile_destination(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
):
    """Load forwarding profile destinations from a YAML file.

    Examples
    --------
        scm load mobile-agent forwarding-profile-destination --file config/destinations.yml

    """
    try:
        config = load_from_yaml(str(file), "forwarding_profile_destinations")

        if dry_run:
            info("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["forwarding_profile_destinations"]))
            return None

        def _apply(destination_data: dict):
            # Apply folder override if specified
            if folder:
                destination_data["folder"] = folder
            # Validate using the Pydantic model
            item = ForwardingProfileDestination(**destination_data)
            sdk_data = item.to_sdk_model()

            # Create via SDK client
            return scm_client.create_forwarding_profile_destination(**sdk_data)

        return _bulk_load_items(config["forwarding_profile_destinations"], _apply, "forwarding profile destination")

    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e


@set_app.command("forwarding-profile-destination")
@handle_command_errors("creating/updating forwarding profile destination")
def set_forwarding_profile_destination(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    fqdn: list[str] | None = FQDN_OPTION,
    ip_address: list[str] | None = IP_ADDRESS_OPTION,
):
    r"""Create or update a forwarding profile destination.

    The folder must be "Mobile Users" (the only folder supported by the API).
    Entries accept an optional ':port' suffix.

    Examples
    --------
        scm set mobile-agent forwarding-profile-destination \
        --folder "Mobile Users" \
        --name "internal-apps" \
        --fqdn "*.example.com:8080" \
        --ip-address "10.0.0.0/8"

    """
    destination_data: dict[str, Any] = {
        "name": name,
    }

    if folder:
        destination_data["folder"] = folder
    if description is not None:
        destination_data["description"] = description
    if fqdn:
        destination_data["fqdn"] = fqdn
    if ip_address:
        destination_data["ip_addresses"] = ip_address

    try:
        destination = ForwardingProfileDestination(**destination_data)
        sdk_data = destination.to_sdk_model()
    except ValidationError as e:
        error(f"Validation error: {str(e)}")
        raise typer.Exit(code=1) from e

    result = scm_client.create_forwarding_profile_destination(**sdk_data)

    action = result.pop("__action__", "created")

    if action == "created":
        success(f"Created forwarding profile destination: {result.get('name', name)}")
    elif action == "updated":
        success(f"Updated forwarding profile destination: {result.get('name', name)}")
    elif action == "no_change":
        info(f"No changes needed for forwarding profile destination: {result.get('name', name)}")

    return result


@show_app.command("forwarding-profile-destination")
@handle_command_errors("showing forwarding profile destination")
def show_forwarding_profile_destination(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the forwarding profile destination to show"),
    destination_id: str | None = PROFILE_ID_OPTION,
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display forwarding profile destinations.

    Examples
    --------
        # List all forwarding profile destinations (default behavior)
        scm show mobile-agent forwarding-profile-destination --folder "Mobile Users"

        # Show a specific destination by name
        scm show mobile-agent forwarding-profile-destination --folder "Mobile Users" --name "internal-apps"

        # Show a specific destination by UUID
        scm show mobile-agent forwarding-profile-destination --id "123e4567-e89b-12d3-a456-426655440000"

    """
    if destination_id or name:
        destination = scm_client.get_forwarding_profile_destination(folder=folder, name=name, destination_id=destination_id)
        emit(destination, output, title=f"Forwarding Profile Destination: {destination.get('name', 'N/A')}")
        return destination

    destinations = scm_client.list_forwarding_profile_destinations(folder=folder)
    emit(
        destinations,
        output,
        columns=["name", "fqdn", "ip_addresses", "description", "id"],
        title=f"Forwarding Profile Destinations in folder '{folder or 'Mobile Users'}'",
    )
    return destinations


# =============================================================================================================================================================================================
# AGENT PROFILE COMMANDS (agent3)
# =============================================================================================================================================================================================

# Agent/tunnel profiles live only in the 'Mobile Users' folder (no snippet/device)
GP_FOLDER_OPTION = typer.Option(
    "Mobile Users",
    "--folder",
    help="Folder path (GlobalProtect profiles only support 'Mobile Users')",
)

# Module-level option constants for repeatable list options (avoids B008 lint errors)
GP_OS_OPTION: list[str] | None = typer.Option(
    None,
    "--os",
    help="Operating system (repeatable: Android, Chrome, IoT, Linux, Mac, Windows, WindowsUWP, iOS)",
)
GP_SOURCE_USER_OPTION: list[str] | None = typer.Option(
    None,
    "--source-user",
    help="Source user this profile applies to (repeatable)",
)
GP_THIRD_PARTY_VPN_CLIENT_OPTION: list[str] | None = typer.Option(
    None,
    "--third-party-vpn-client",
    help="Third party VPN client supported by this profile (repeatable)",
)
GP_ACCESS_ROUTE_OPTION: list[str] | None = typer.Option(
    None,
    "--access-route",
    help="Route included in the tunnel (repeatable)",
)
GP_EXCLUDE_ACCESS_ROUTE_OPTION: list[str] | None = typer.Option(
    None,
    "--exclude-access-route",
    help="Route excluded from the tunnel (repeatable)",
)
GP_INCLUDE_APPLICATION_OPTION: list[str] | None = typer.Option(
    None,
    "--include-application",
    help="Application included in the tunnel (repeatable)",
)
GP_EXCLUDE_APPLICATION_OPTION: list[str] | None = typer.Option(
    None,
    "--exclude-application",
    help="Application excluded from the tunnel (repeatable)",
)


@backup_app.command("agent-profile")
@handle_command_errors("backing up agent profiles")
def backup_agent_profile(
    folder: str = GP_FOLDER_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup all agent profiles from a folder to a YAML file.

    Examples
    --------
        # Backup from the Mobile Users folder
        scm backup mobile-agent agent-profile --folder "Mobile Users"

        # Backup with custom output file
        scm backup mobile-agent agent-profile --file agent-profiles-backup.yaml

    """
    profiles = scm_client.list_agent_profiles(folder=folder)

    if not profiles:
        info(f"No agent profiles found in folder '{folder}'")
        return

    backup_data = []
    for profile in profiles:
        profile_dict = {k: v for k, v in profile.items() if v is not None}
        profile_dict.pop("id", None)
        backup_data.append(profile_dict)

    yaml_data = {"agent_profiles": backup_data}

    if file is None:
        file = Path(get_default_backup_filename("agent-profile", "folder", folder))

    with file.open("w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(backup_data)} agent profiles to {file}")
    return str(file)


@delete_app.command("agent-profile")
@handle_command_errors("deleting agent profile")
def delete_agent_profile(
    folder: str = GP_FOLDER_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete an agent profile.

    Examples
    --------
        scm delete mobile-agent agent-profile --folder "Mobile Users" --name "corp-app-settings"

    """
    if not force:
        typer.confirm(f"Delete agent profile '{name}' from folder '{folder}'?", abort=True)
    result = scm_client.delete_agent_profile(folder=folder, name=name)
    if result:
        success(f"Deleted agent profile: {name} from folder {folder}")
    return result


@load_app.command("agent-profile")
@handle_command_errors("loading agent profiles")
def load_agent_profile(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
):
    """Load agent profiles from a YAML file.

    Examples
    --------
        # Load from file
        scm load mobile-agent agent-profile --file config/agent_profiles.yml

        # Load with folder override
        scm load mobile-agent agent-profile --file config/agent_profiles.yml --folder "Mobile Users"

    """
    try:
        config = load_from_yaml(str(file), "agent_profiles")

        if dry_run:
            info("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["agent_profiles"]))
            return None

        def _apply(profile_data: dict):
            # Apply folder override if specified
            if folder:
                profile_data["folder"] = folder
            # Validate using the Pydantic model
            item = AgentProfile(**profile_data)
            sdk_data = item.to_sdk_model()

            # Create via SDK client
            return scm_client.create_agent_profile(**sdk_data)

        return _bulk_load_items(config["agent_profiles"], _apply, "agent profile")

    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e


@set_app.command("agent-profile")
@handle_command_errors("creating/updating agent profile")
def set_agent_profile(
    folder: str = GP_FOLDER_OPTION,
    name: str = NAME_OPTION,
    os: list[str] | None = GP_OS_OPTION,
    connect_method: str | None = typer.Option(None, "--connect-method", help="Connect method (user-logon, pre-logon, on-demand, pre-logon-then-on-demand)"),
    tunnel_mtu: int | None = typer.Option(None, "--tunnel-mtu", help="GlobalProtect connection MTU in bytes (1000-1420)"),
    save_user_credentials: str | None = typer.Option(None, "--save-user-credentials", help="Save user credentials: 0=No, 1=Yes, 2=Save username only, 3=Only with user fingerprint"),
    source_user: list[str] | None = GP_SOURCE_USER_OPTION,
    third_party_vpn_clients: list[str] | None = GP_THIRD_PARTY_VPN_CLIENT_OPTION,
):
    r"""Create or update an agent profile (GlobalProtect app settings).

    Nested settings (agent UI, gateways, HIP collection, ...) are supported via
    `scm load mobile-agent agent-profile`.

    Examples
    --------
        scm set mobile-agent agent-profile \
        --folder "Mobile Users" \
        --name "corp-app-settings" \
        --connect-method user-logon \
        --tunnel-mtu 1400 \
        --os Windows --os Mac

    """
    profile_data: dict[str, Any] = {
        "name": name,
        "folder": folder,
    }

    if os:
        profile_data["os"] = os
    if connect_method is not None:
        profile_data["connect_method"] = connect_method
    if tunnel_mtu is not None:
        profile_data["tunnel_mtu"] = tunnel_mtu
    if save_user_credentials is not None:
        profile_data["save_user_credentials"] = save_user_credentials
    if source_user:
        profile_data["source_user"] = source_user
    if third_party_vpn_clients:
        profile_data["third_party_vpn_clients"] = third_party_vpn_clients

    try:
        agent_profile = AgentProfile(**profile_data)
        sdk_data = agent_profile.to_sdk_model()
    except ValidationError as e:
        error(f"Validation error: {str(e)}")
        raise typer.Exit(code=1) from e

    result = scm_client.create_agent_profile(**sdk_data)

    action = result.pop("__action__", "created")

    if action == "created":
        success(f"Created agent profile: {result.get('name', name)} in folder {result.get('folder', folder)}")
    elif action == "updated":
        success(f"Updated agent profile: {result.get('name', name)} in folder {result.get('folder', folder)}")
    elif action == "no_change":
        info(f"No changes needed for agent profile: {result.get('name', name)} in folder {result.get('folder', folder)}")

    return result


@show_app.command("agent-profile")
@handle_command_errors("showing agent profile")
def show_agent_profile(
    folder: str = GP_FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the agent profile to show"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display agent profiles (GlobalProtect app settings).

    Examples
    --------
        # List all agent profiles (default behavior)
        scm show mobile-agent agent-profile --folder "Mobile Users"

        # Show a specific agent profile by name
        scm show mobile-agent agent-profile --folder "Mobile Users" --name "corp-app-settings"

    """
    if name:
        profile = scm_client.get_agent_profile(folder=folder, name=name)
        emit(profile, output, title=f"Agent Profile: {profile.get('name', 'N/A')}")
        return profile

    profiles = scm_client.list_agent_profiles(folder=folder)
    emit(
        profiles,
        output,
        columns=["name", "os", "save_user_credentials"],
        title=f"Agent Profiles in folder '{folder}'",
    )
    return profiles


# =============================================================================================================================================================================================
# TUNNEL PROFILE COMMANDS (agent3)
# =============================================================================================================================================================================================


@backup_app.command("tunnel-profile")
@handle_command_errors("backing up tunnel profiles")
def backup_tunnel_profile(
    folder: str = GP_FOLDER_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup all tunnel profiles from a folder to a YAML file.

    Examples
    --------
        # Backup from the Mobile Users folder
        scm backup mobile-agent tunnel-profile --folder "Mobile Users"

        # Backup with custom output file
        scm backup mobile-agent tunnel-profile --file tunnel-profiles-backup.yaml

    """
    profiles = scm_client.list_tunnel_profiles(folder=folder)

    if not profiles:
        info(f"No tunnel profiles found in folder '{folder}'")
        return

    backup_data = []
    for profile in profiles:
        profile_dict = {k: v for k, v in profile.items() if v is not None}
        profile_dict.pop("id", None)
        backup_data.append(profile_dict)

    yaml_data = {"tunnel_profiles": backup_data}

    if file is None:
        file = Path(get_default_backup_filename("tunnel-profile", "folder", folder))

    with file.open("w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(backup_data)} tunnel profiles to {file}")
    return str(file)


@delete_app.command("tunnel-profile")
@handle_command_errors("deleting tunnel profile")
def delete_tunnel_profile(
    folder: str = GP_FOLDER_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a tunnel profile.

    Examples
    --------
        scm delete mobile-agent tunnel-profile --folder "Mobile Users" --name "corp-tunnel"

    """
    if not force:
        typer.confirm(f"Delete tunnel profile '{name}' from folder '{folder}'?", abort=True)
    result = scm_client.delete_tunnel_profile(folder=folder, name=name)
    if result:
        success(f"Deleted tunnel profile: {name} from folder {folder}")
    return result


@load_app.command("tunnel-profile")
@handle_command_errors("loading tunnel profiles")
def load_tunnel_profile(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
):
    """Load tunnel profiles from a YAML file.

    Examples
    --------
        # Load from file
        scm load mobile-agent tunnel-profile --file config/tunnel_profiles.yml

        # Load with folder override
        scm load mobile-agent tunnel-profile --file config/tunnel_profiles.yml --folder "Mobile Users"

    """
    try:
        config = load_from_yaml(str(file), "tunnel_profiles")

        if dry_run:
            info("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["tunnel_profiles"]))
            return None

        def _apply(profile_data: dict):
            # Apply folder override if specified
            if folder:
                profile_data["folder"] = folder
            # Validate using the Pydantic model
            item = TunnelProfile(**profile_data)
            sdk_data = item.to_sdk_model()

            # Create via SDK client
            return scm_client.create_tunnel_profile(**sdk_data)

        return _bulk_load_items(config["tunnel_profiles"], _apply, "tunnel profile")

    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e


@set_app.command("tunnel-profile")
@handle_command_errors("creating/updating tunnel profile")
def set_tunnel_profile(
    folder: str = GP_FOLDER_OPTION,
    name: str = NAME_OPTION,
    no_direct_access_to_local_network: bool | None = typer.Option(
        None,
        "--no-direct-access-to-local-network/--allow-direct-access-to-local-network",
        help="Disable direct access to the local network",
    ),
    retrieve_framed_ip_address: bool | None = typer.Option(
        None,
        "--retrieve-framed-ip-address/--no-retrieve-framed-ip-address",
        help="Retrieve the framed IP address from the authentication server",
    ),
    os: list[str] | None = GP_OS_OPTION,
    source_user: list[str] | None = GP_SOURCE_USER_OPTION,
    access_route: list[str] | None = GP_ACCESS_ROUTE_OPTION,
    exclude_access_route: list[str] | None = GP_EXCLUDE_ACCESS_ROUTE_OPTION,
    include_applications: list[str] | None = GP_INCLUDE_APPLICATION_OPTION,
    exclude_applications: list[str] | None = GP_EXCLUDE_APPLICATION_OPTION,
):
    r"""Create or update a tunnel profile (GlobalProtect tunnel settings).

    Nested settings (authentication override, source address, split tunneling
    domains) are supported via `scm load mobile-agent tunnel-profile`.

    Examples
    --------
        scm set mobile-agent tunnel-profile \
        --folder "Mobile Users" \
        --name "corp-tunnel" \
        --access-route 10.0.0.0/8 \
        --no-direct-access-to-local-network

    """
    profile_data: dict[str, Any] = {
        "name": name,
        "folder": folder,
    }

    if no_direct_access_to_local_network is not None:
        profile_data["no_direct_access_to_local_network"] = no_direct_access_to_local_network
    if retrieve_framed_ip_address is not None:
        profile_data["retrieve_framed_ip_address"] = retrieve_framed_ip_address
    if os:
        profile_data["os"] = os
    if source_user:
        profile_data["source_user"] = source_user
    if access_route:
        profile_data["access_route"] = access_route
    if exclude_access_route:
        profile_data["exclude_access_route"] = exclude_access_route
    if include_applications:
        profile_data["include_applications"] = include_applications
    if exclude_applications:
        profile_data["exclude_applications"] = exclude_applications

    try:
        tunnel_profile = TunnelProfile(**profile_data)
        sdk_data = tunnel_profile.to_sdk_model()
    except ValidationError as e:
        error(f"Validation error: {str(e)}")
        raise typer.Exit(code=1) from e

    result = scm_client.create_tunnel_profile(**sdk_data)

    action = result.pop("__action__", "created")

    if action == "created":
        success(f"Created tunnel profile: {result.get('name', name)} in folder {result.get('folder', folder)}")
    elif action == "updated":
        success(f"Updated tunnel profile: {result.get('name', name)} in folder {result.get('folder', folder)}")
    elif action == "no_change":
        info(f"No changes needed for tunnel profile: {result.get('name', name)} in folder {result.get('folder', folder)}")

    return result


@show_app.command("tunnel-profile")
@handle_command_errors("showing tunnel profile")
def show_tunnel_profile(
    folder: str = GP_FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the tunnel profile to show"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display tunnel profiles (GlobalProtect tunnel settings).

    Examples
    --------
        # List all tunnel profiles (default behavior)
        scm show mobile-agent tunnel-profile --folder "Mobile Users"

        # Show a specific tunnel profile by name
        scm show mobile-agent tunnel-profile --folder "Mobile Users" --name "corp-tunnel"

    """
    if name:
        profile = scm_client.get_tunnel_profile(folder=folder, name=name)
        emit(profile, output, title=f"Tunnel Profile: {profile.get('name', 'N/A')}")
        return profile

    profiles = scm_client.list_tunnel_profiles(folder=folder)
    emit(
        profiles,
        output,
        columns=["name", "os", "no_direct_access_to_local_network"],
        title=f"Tunnel Profiles in folder '{folder}'",
    )
    return profiles


# =============================================================================================================================================================================================
# INFRASTRUCTURE SETTING COMMANDS
# =============================================================================================================================================================================================

# Infrastructure settings live only in the 'Mobile Users' folder, and the SCM
# API addresses them by name everywhere (including list), so show/backup need --name.
INFRA_FOLDER_OPTION = typer.Option(
    "Mobile Users",
    "--folder",
    help="Folder path (must be 'Mobile Users')",
)
INFRA_NAME_OPTION = typer.Option(
    ...,
    "--name",
    help="Name of the infrastructure setting",
)


@set_app.command("infrastructure-setting")
@handle_command_errors("creating/updating infrastructure setting")
def set_infrastructure_setting(
    folder: str = INFRA_FOLDER_OPTION,
    name: str = INFRA_NAME_OPTION,
    dns_servers: str = typer.Option(..., "--dns-servers", help="DNS server entries as JSON list"),
    ip_pools: str = typer.Option(..., "--ip-pools", help="IP pools as JSON list"),
    portal_hostname: str = typer.Option(..., "--portal-hostname", help="Portal hostname configuration as JSON"),
    enable_wins: str | None = typer.Option(None, "--enable-wins", help="WINS configuration as JSON"),
    ipv6: bool | None = typer.Option(None, "--ipv6/--no-ipv6", help="Enable or disable IPv6"),
    udp_queries: str | None = typer.Option(None, "--udp-queries", help="UDP query retry configuration as JSON"),
    static_ip_pools: str | None = typer.Option(None, "--static-ip-pools", help="Static IP pools as JSON list"),
):
    r"""Create or update an infrastructure setting.

    Examples
    --------
        scm set mobile-agent infrastructure-setting \
        --name "gp-infra" \
        --dns-servers '[{"name": "dns-1", "dns_suffix": ["example.com"]}]' \
        --ip-pools '[{"name": "pool-1", "ip_pool": ["10.0.0.0/16"]}]' \
        --portal-hostname '{"default_domain": {"hostname": "acme"}}'

    """
    # Build setting data; the Pydantic model parses JSON strings into structures
    setting_data: dict[str, Any] = {
        "name": name,
        "folder": folder,
        "dns_servers": dns_servers,
        "ip_pools": ip_pools,
        "portal_hostname": portal_hostname,
    }
    if enable_wins is not None:
        setting_data["enable_wins"] = enable_wins
    if ipv6 is not None:
        setting_data["ipv6"] = ipv6
    if udp_queries is not None:
        setting_data["udp_queries"] = udp_queries
    if static_ip_pools is not None:
        setting_data["static_ip_pools"] = static_ip_pools

    # Validate using the Pydantic model
    try:
        infrastructure_setting = InfrastructureSetting(**setting_data)
        sdk_data = infrastructure_setting.to_sdk_model()
    except ValidationError as e:
        error(f"Validation error: {str(e)}")
        raise typer.Exit(code=1) from e

    # Call the SDK client
    result = scm_client.create_infrastructure_setting(**sdk_data)

    # Get the action performed
    action = result.pop("__action__", "created")

    if action == "created":
        success(f"Created infrastructure setting: {result.get('name', name)} in folder {folder}")
    elif action == "updated":
        success(f"Updated infrastructure setting: {result.get('name', name)} in folder {folder}")
    elif action == "no_change":
        info(f"No changes needed for infrastructure setting: {result.get('name', name)} in folder {folder}")

    return result


@show_app.command("infrastructure-setting")
@handle_command_errors("showing infrastructure setting")
def show_infrastructure_setting(
    folder: str = INFRA_FOLDER_OPTION,
    name: str = INFRA_NAME_OPTION,
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display an infrastructure setting.

    The SCM API requires a name for this endpoint; there is no list-all mode.

    Examples
    --------
        scm show mobile-agent infrastructure-setting --name "gp-infra"

    """
    setting = scm_client.get_infrastructure_setting(folder=folder, name=name)
    emit(setting, output, title=f"Infrastructure Setting: {setting.get('name', 'N/A')}")
    return setting


@delete_app.command("infrastructure-setting")
@handle_command_errors("deleting infrastructure setting")
def delete_infrastructure_setting(
    folder: str = INFRA_FOLDER_OPTION,
    name: str = INFRA_NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete an infrastructure setting.

    Examples
    --------
        scm delete mobile-agent infrastructure-setting --name "gp-infra"

    """
    if not force:
        typer.confirm(f"Delete infrastructure setting '{name}' from folder '{folder}'?", abort=True)
    result = scm_client.delete_infrastructure_setting(folder=folder, name=name)
    if result:
        success(f"Deleted infrastructure setting: {name} from folder {folder}")
    return result


@backup_app.command("infrastructure-setting")
@handle_command_errors("backing up infrastructure settings")
def backup_infrastructure_setting(
    folder: str = INFRA_FOLDER_OPTION,
    name: str = INFRA_NAME_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup an infrastructure setting to a YAML file.

    The SCM API requires a name for this endpoint, so backups cover the
    named setting rather than every setting in the folder.

    Examples
    --------
        scm backup mobile-agent infrastructure-setting --name "gp-infra"

    """
    settings_list = scm_client.list_infrastructure_settings(folder=folder, name=name)

    if not settings_list:
        info(f"No infrastructure settings named '{name}' found in folder '{folder}'")
        return

    # Convert to backup format, stripping system fields
    backup_data = []
    for setting in settings_list:
        setting_dict = {k: v for k, v in setting.items() if v is not None}
        setting_dict.pop("id", None)
        backup_data.append(setting_dict)

    yaml_data = {"infrastructure_settings": backup_data}

    if file is None:
        file = Path(get_default_backup_filename("infrastructure-setting", "folder", folder))

    with file.open("w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(backup_data)} infrastructure settings to {file}")
    return str(file)


@load_app.command("infrastructure-setting")
@handle_command_errors("loading infrastructure settings")
def load_infrastructure_setting(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
):
    """Load infrastructure settings from a YAML file.

    Examples
    --------
        scm load mobile-agent infrastructure-setting --file config/infrastructure_settings.yml

    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(str(file), "infrastructure_settings")

        if dry_run:
            info("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["infrastructure_settings"]))
            return None

        def _apply(setting_data: dict):
            # Apply folder override if specified
            if folder:
                setting_data["folder"] = folder
            # Validate using the Pydantic model
            item = InfrastructureSetting(**setting_data)
            sdk_data = item.to_sdk_model()

            # Create via SDK client
            return scm_client.create_infrastructure_setting(**sdk_data)

        return _bulk_load_items(config["infrastructure_settings"], _apply, "infrastructure setting")

    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# GLOBAL SETTING COMMANDS (SINGLETON — SHOW/SET ONLY)
# =============================================================================================================================================================================================


@show_app.command("global-setting")
@handle_command_errors("showing global settings")
def show_global_setting(
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display the GlobalProtect global settings.

    Global settings are a tenant-wide singleton; there is nothing to filter by.

    Examples
    --------
        scm show mobile-agent global-setting

    """
    setting = scm_client.get_global_settings()

    if not setting:
        info("No global settings configured")
    emit(setting, output, title="GlobalProtect Global Settings")
    return setting


@set_app.command("global-setting")
@handle_command_errors("updating global settings")
def set_global_setting(
    agent_version: str | None = typer.Option(None, "--agent-version", help="GlobalProtect agent version"),
    manual_gateway: str | None = typer.Option(None, "--manual-gateway", help="Manual gateway configuration as JSON"),
):
    r"""Update the GlobalProtect global settings.

    Global settings are a singleton: they always exist and are updated in
    place. There are no delete, backup, or load operations.

    Examples
    --------
        scm set mobile-agent global-setting --agent-version "6.2.0"

        scm set mobile-agent global-setting \
        --manual-gateway '{"region": [{"name": "americas", "locations": ["us-east-1"]}]}'

    """
    # Build setting data; the Pydantic model parses JSON strings into structures
    setting_data: dict[str, Any] = {}
    if agent_version is not None:
        setting_data["agent_version"] = agent_version
    if manual_gateway is not None:
        setting_data["manual_gateway"] = manual_gateway

    # Validate using the Pydantic model (requires at least one field)
    try:
        global_setting = GlobalSetting(**setting_data)
        sdk_data = global_setting.to_sdk_model()
    except ValidationError as e:
        error(f"Validation error: {str(e)}")
        raise typer.Exit(code=1) from e

    result = scm_client.update_global_settings(**sdk_data)
    result.pop("__action__", None)

    success("Updated GlobalProtect global settings")
    return result


# =============================================================================================================================================================================================
# FORWARDING PROFILE SOURCE APPLICATION COMMANDS
# =============================================================================================================================================================================================

APPLICATION_OPTION = typer.Option(
    None,
    "--application",
    help="Application name (repeatable)",
)


@backup_app.command("forwarding-profile-source-application")
@handle_command_errors("backing up forwarding profile source applications")
def backup_forwarding_profile_source_application(
    folder: str = BACKUP_FOLDER_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup all forwarding profile source applications from a folder to a YAML file.

    Examples
    --------
        # Backup from the Mobile Users folder
        scm backup mobile-agent forwarding-profile-source-application --folder "Mobile Users"

    """
    folder = folder or "Mobile Users"

    source_applications = scm_client.list_forwarding_profile_source_applications(folder=folder)

    if not source_applications:
        info(f"No forwarding profile source applications found in folder '{folder}'")
        return

    # Convert SDK models to dictionaries, excluding unset values
    backup_data = []
    for app in source_applications:
        app_dict = {k: v for k, v in app.items() if v is not None}
        # Remove system fields that shouldn't be in backup
        app_dict.pop("id", None)
        backup_data.append(app_dict)

    # Create the YAML structure
    yaml_data = {"forwarding_profile_source_applications": backup_data}

    # Generate filename
    if file is None:
        file = Path(get_default_backup_filename("forwarding-profile-source-application", "folder", folder))

    # Write to YAML file
    with file.open("w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(backup_data)} forwarding profile source applications to {file}")
    return str(file)


@delete_app.command("forwarding-profile-source-application")
@handle_command_errors("deleting forwarding profile source application")
def delete_forwarding_profile_source_application(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a forwarding profile source application.

    Examples
    --------
        scm delete mobile-agent forwarding-profile-source-application --folder "Mobile Users" --name "office-apps"

    """
    if not force:
        typer.confirm(f"Delete forwarding profile source application '{name}' from folder '{folder}'?", abort=True)
    result = scm_client.delete_forwarding_profile_source_application(folder=folder, name=name)
    if result:
        success(f"Deleted forwarding profile source application: {name} from folder {folder}")
    return result


@load_app.command("forwarding-profile-source-application")
@handle_command_errors("loading forwarding profile source applications")
def load_forwarding_profile_source_application(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
):
    """Load forwarding profile source applications from a YAML file.

    Examples
    --------
        # Load from file with original locations
        scm load mobile-agent forwarding-profile-source-application --file config/source_applications.yml

        # Load with folder override
        scm load mobile-agent forwarding-profile-source-application --file config/source_applications.yml --folder "Mobile Users"

    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(str(file), "forwarding_profile_source_applications")

        if dry_run:
            info("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["forwarding_profile_source_applications"]))
            return None

        def _apply(app_data: dict):
            # Apply folder override if specified
            if folder:
                app_data["folder"] = folder
            # Validate using the Pydantic model
            item = ForwardingProfileSourceApplication(**app_data)
            sdk_data = item.to_sdk_model()

            # Create via SDK client
            return scm_client.create_forwarding_profile_source_application(**sdk_data)

        return _bulk_load_items(config["forwarding_profile_source_applications"], _apply, "forwarding profile source application")

    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e


@set_app.command("forwarding-profile-source-application")
@handle_command_errors("creating/updating forwarding profile source application")
def set_forwarding_profile_source_application(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    application: list[str] | None = APPLICATION_OPTION,
):
    r"""Create or update a forwarding profile source application.

    Examples
    --------
        scm set mobile-agent forwarding-profile-source-application \
        --folder "Mobile Users" \
        --name "office-apps" \
        --application slack \
        --application zoom

    """
    # Build source application data
    app_data: dict[str, Any] = {
        "name": name,
    }

    if folder:
        app_data["folder"] = folder
    if description is not None:
        app_data["description"] = description
    if application:
        app_data["applications"] = application

    # Validate using the Pydantic model
    try:
        source_application = ForwardingProfileSourceApplication(**app_data)
        sdk_data = source_application.to_sdk_model()
    except ValidationError as e:
        error(f"Validation error: {str(e)}")
        raise typer.Exit(code=1) from e

    # Call the SDK client
    result = scm_client.create_forwarding_profile_source_application(**sdk_data)

    # Get the action performed
    action = result.pop("__action__", "created")

    if action == "created":
        success(f"Created forwarding profile source application: {result.get('name', name)} in folder {result.get('folder', folder)}")
    elif action == "updated":
        success(f"Updated forwarding profile source application: {result.get('name', name)} in folder {result.get('folder', folder)}")
    elif action == "no_change":
        info(f"No changes needed for forwarding profile source application: {result.get('name', name)} in folder {result.get('folder', folder)}")

    return result


@show_app.command("forwarding-profile-source-application")
@handle_command_errors("showing forwarding profile source application")
def show_forwarding_profile_source_application(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the source application to show"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display forwarding profile source applications.

    Examples
    --------
        # List all source applications in a folder (default behavior)
        scm show mobile-agent forwarding-profile-source-application --folder "Mobile Users"

        # Show a specific source application by name
        scm show mobile-agent forwarding-profile-source-application --folder "Mobile Users" --name "office-apps"

    """
    if name:
        # Get a specific source application by name
        app = scm_client.get_forwarding_profile_source_application(folder=folder, name=name)
        emit(app, output, title=f"Forwarding Profile Source Application: {app.get('name', 'N/A')}")
        return app

    # Default: list all source applications
    apps_list = scm_client.list_forwarding_profile_source_applications(folder=folder)
    emit(
        apps_list,
        output,
        columns=["name", "applications", "description"],
        title=f"Forwarding Profile Source Applications in folder '{folder}'",
    )
    return apps_list


# =============================================================================================================================================================================================
# FORWARDING PROFILE USER LOCATION COMMANDS
# =============================================================================================================================================================================================

INTERNAL_HOST_IP_OPTION = typer.Option(
    None,
    "--internal-host-ip",
    help="Internal host detection IP address",
)
INTERNAL_HOST_FQDN_OPTION = typer.Option(
    None,
    "--internal-host-fqdn",
    help="Internal host detection FQDN",
)
USER_LOCATION_IP_OPTION = typer.Option(
    None,
    "--ip-address",
    help="User location IP address (repeatable; supports wildcards or CIDR suffix)",
)


@backup_app.command("forwarding-profile-user-location")
@handle_command_errors("backing up forwarding profile user locations")
def backup_forwarding_profile_user_location(
    folder: str = BACKUP_FOLDER_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup all forwarding profile user locations from a folder to a YAML file.

    Examples
    --------
        # Backup from the Mobile Users folder
        scm backup mobile-agent forwarding-profile-user-location --folder "Mobile Users"

    """
    folder = folder or "Mobile Users"

    user_locations = scm_client.list_forwarding_profile_user_locations(folder=folder)

    if not user_locations:
        info(f"No forwarding profile user locations found in folder '{folder}'")
        return

    # Convert SDK models to dictionaries, excluding unset values
    backup_data = []
    for location in user_locations:
        location_dict = {k: v for k, v in location.items() if v is not None}
        # Remove system fields that shouldn't be in backup
        location_dict.pop("id", None)
        # Flatten choice into the CLI YAML schema
        choice = location_dict.pop("choice", None) or {}
        if choice.get("ip_addresses"):
            location_dict["ip_addresses"] = [entry["name"] for entry in choice["ip_addresses"] if entry.get("name")]
        internal_host = choice.get("internal_host_detection") or {}
        if internal_host.get("ip_address"):
            location_dict["internal_host_ip"] = internal_host["ip_address"]
        if internal_host.get("fqdn"):
            location_dict["internal_host_fqdn"] = internal_host["fqdn"]
        backup_data.append(location_dict)

    # Create the YAML structure
    yaml_data = {"forwarding_profile_user_locations": backup_data}

    # Generate filename
    if file is None:
        file = Path(get_default_backup_filename("forwarding-profile-user-location", "folder", folder))

    # Write to YAML file
    with file.open("w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(backup_data)} forwarding profile user locations to {file}")
    return str(file)


@delete_app.command("forwarding-profile-user-location")
@handle_command_errors("deleting forwarding profile user location")
def delete_forwarding_profile_user_location(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a forwarding profile user location.

    Examples
    --------
        scm delete mobile-agent forwarding-profile-user-location --folder "Mobile Users" --name "branch-network"

    """
    if not force:
        typer.confirm(f"Delete forwarding profile user location '{name}' from folder '{folder}'?", abort=True)
    result = scm_client.delete_forwarding_profile_user_location(folder=folder, name=name)
    if result:
        success(f"Deleted forwarding profile user location: {name} from folder {folder}")
    return result


@load_app.command("forwarding-profile-user-location")
@handle_command_errors("loading forwarding profile user locations")
def load_forwarding_profile_user_location(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
):
    """Load forwarding profile user locations from a YAML file.

    Examples
    --------
        # Load from file with original locations
        scm load mobile-agent forwarding-profile-user-location --file config/user_locations.yml

        # Load with folder override
        scm load mobile-agent forwarding-profile-user-location --file config/user_locations.yml --folder "Mobile Users"

    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(str(file), "forwarding_profile_user_locations")

        if dry_run:
            info("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["forwarding_profile_user_locations"]))
            return None

        def _apply(location_data: dict):
            # Apply folder override if specified
            if folder:
                location_data["folder"] = folder
            # Validate using the Pydantic model
            item = ForwardingProfileUserLocation(**location_data)
            sdk_data = item.to_sdk_model()

            # Create via SDK client
            return scm_client.create_forwarding_profile_user_location(**sdk_data)

        return _bulk_load_items(config["forwarding_profile_user_locations"], _apply, "forwarding profile user location")

    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e


@set_app.command("forwarding-profile-user-location")
@handle_command_errors("creating/updating forwarding profile user location")
def set_forwarding_profile_user_location(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    internal_host_ip: str | None = INTERNAL_HOST_IP_OPTION,
    internal_host_fqdn: str | None = INTERNAL_HOST_FQDN_OPTION,
    ip_address: list[str] | None = USER_LOCATION_IP_OPTION,
):
    r"""Create or update a forwarding profile user location.

    Provide either IP address entries (--ip-address, repeatable) or internal host
    detection settings (--internal-host-ip / --internal-host-fqdn), but not both.

    Examples
    --------
        # IP address based location
        scm set mobile-agent forwarding-profile-user-location \
        --folder "Mobile Users" \
        --name "branch-network" \
        --ip-address "10.1.0.0/16"

        # Internal host detection based location
        scm set mobile-agent forwarding-profile-user-location \
        --folder "Mobile Users" \
        --name "corp-office" \
        --internal-host-fqdn "intranet.example.com"

    """
    # Build user location data
    location_data: dict[str, Any] = {
        "name": name,
    }

    if folder:
        location_data["folder"] = folder
    if description is not None:
        location_data["description"] = description
    if internal_host_ip is not None:
        location_data["internal_host_ip"] = internal_host_ip
    if internal_host_fqdn is not None:
        location_data["internal_host_fqdn"] = internal_host_fqdn
    if ip_address:
        location_data["ip_addresses"] = ip_address

    # Validate using the Pydantic model
    try:
        user_location = ForwardingProfileUserLocation(**location_data)
        sdk_data = user_location.to_sdk_model()
    except ValidationError as e:
        error(f"Validation error: {str(e)}")
        raise typer.Exit(code=1) from e

    # Call the SDK client
    result = scm_client.create_forwarding_profile_user_location(**sdk_data)

    # Get the action performed
    action = result.pop("__action__", "created")

    if action == "created":
        success(f"Created forwarding profile user location: {result.get('name', name)} in folder {result.get('folder', folder)}")
    elif action == "updated":
        success(f"Updated forwarding profile user location: {result.get('name', name)} in folder {result.get('folder', folder)}")
    elif action == "no_change":
        info(f"No changes needed for forwarding profile user location: {result.get('name', name)} in folder {result.get('folder', folder)}")

    return result


@show_app.command("forwarding-profile-user-location")
@handle_command_errors("showing forwarding profile user location")
def show_forwarding_profile_user_location(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the user location to show"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display forwarding profile user locations.

    Examples
    --------
        # List all user locations in a folder (default behavior)
        scm show mobile-agent forwarding-profile-user-location --folder "Mobile Users"

        # Show a specific user location by name
        scm show mobile-agent forwarding-profile-user-location --folder "Mobile Users" --name "branch-network"

    """
    if name:
        # Get a specific user location by name
        location = scm_client.get_forwarding_profile_user_location(folder=folder, name=name)
        emit(location, output, title=f"Forwarding Profile User Location: {location.get('name', 'N/A')}")
        return location

    # Default: list all user locations
    locations_list = scm_client.list_forwarding_profile_user_locations(folder=folder)
    emit(
        locations_list,
        output,
        columns=["name", "choice", "description"],
        title=f"Forwarding Profile User Locations in folder '{folder}'",
    )
    return locations_list


# =============================================================================================================================================================================================
# FORWARDING PROFILE REGIONAL AND CUSTOM PROXY COMMANDS
# =============================================================================================================================================================================================

PROXY_TYPE_OPTION = typer.Option(
    None,
    "--type",
    help="Proxy type (gp-and-pac, ztna-agent)",
)
PROXY_1_FQDN_OPTION = typer.Option(
    None,
    "--proxy-1-fqdn",
    help="Primary proxy server FQDN",
)
PROXY_1_PORT_OPTION = typer.Option(
    None,
    "--proxy-1-port",
    help="Primary proxy server port (1-65535)",
)
PROXY_1_LOCATION_OPTION = typer.Option(
    None,
    "--proxy-1-location",
    help="Primary proxy server location",
)
PROXY_2_FQDN_OPTION = typer.Option(
    None,
    "--proxy-2-fqdn",
    help="Secondary proxy server FQDN",
)
PROXY_2_PORT_OPTION = typer.Option(
    None,
    "--proxy-2-port",
    help="Secondary proxy server port (1-65535)",
)
PROXY_2_LOCATION_OPTION = typer.Option(
    None,
    "--proxy-2-location",
    help="Secondary proxy server location",
)
FALLBACK_OPTION_OPTION = typer.Option(
    None,
    "--fallback-option",
    help="Fallback option (fail-open, fail-safe)",
)
LOCATION_PREFERENCE_OPTION = typer.Option(
    None,
    "--location-preference",
    help="Location preference (best-available-pa-location, specific-pa-location)",
)


@backup_app.command("forwarding-profile-regional-and-custom-proxy")
@handle_command_errors("backing up forwarding profile regional and custom proxies")
def backup_forwarding_profile_regional_and_custom_proxy(
    folder: str = BACKUP_FOLDER_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup all forwarding profile regional and custom proxies from a folder to a YAML file.

    Examples
    --------
        # Backup from the Mobile Users folder
        scm backup mobile-agent forwarding-profile-regional-and-custom-proxy --folder "Mobile Users"

    """
    folder = folder or "Mobile Users"

    proxies = scm_client.list_forwarding_profile_regional_and_custom_proxies(folder=folder)

    if not proxies:
        info(f"No forwarding profile regional and custom proxies found in folder '{folder}'")
        return

    # Convert SDK models to dictionaries, excluding unset values
    backup_data = []
    for proxy in proxies:
        proxy_dict = {k: v for k, v in proxy.items() if v is not None}
        # Remove system fields that shouldn't be in backup
        proxy_dict.pop("id", None)
        backup_data.append(proxy_dict)

    # Create the YAML structure
    yaml_data = {"forwarding_profile_regional_and_custom_proxies": backup_data}

    # Generate filename
    if file is None:
        file = Path(get_default_backup_filename("forwarding-profile-regional-and-custom-proxy", "folder", folder))

    # Write to YAML file
    with file.open("w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    success(f"Successfully backed up {len(backup_data)} forwarding profile regional and custom proxies to {file}")
    return str(file)


@delete_app.command("forwarding-profile-regional-and-custom-proxy")
@handle_command_errors("deleting forwarding profile regional and custom proxy")
def delete_forwarding_profile_regional_and_custom_proxy(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """Delete a forwarding profile regional and custom proxy.

    Examples
    --------
        scm delete mobile-agent forwarding-profile-regional-and-custom-proxy --folder "Mobile Users" --name "emea-proxy"

    """
    if not force:
        typer.confirm(f"Delete forwarding profile regional and custom proxy '{name}' from folder '{folder}'?", abort=True)
    result = scm_client.delete_forwarding_profile_regional_and_custom_proxy(folder=folder, name=name)
    if result:
        success(f"Deleted forwarding profile regional and custom proxy: {name} from folder {folder}")
    return result


@load_app.command("forwarding-profile-regional-and-custom-proxy")
@handle_command_errors("loading forwarding profile regional and custom proxies")
def load_forwarding_profile_regional_and_custom_proxy(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
):
    """Load forwarding profile regional and custom proxies from a YAML file.

    Nested fields (proxy_1, proxy_2, connectivity_preference, prisma_access_locations)
    are fully supported in the YAML schema.

    Examples
    --------
        # Load from file with original locations
        scm load mobile-agent forwarding-profile-regional-and-custom-proxy --file config/regional_proxies.yml

        # Load with folder override
        scm load mobile-agent forwarding-profile-regional-and-custom-proxy --file config/regional_proxies.yml --folder "Mobile Users"

    """
    try:
        # Load and parse the YAML file
        config = load_from_yaml(str(file), "forwarding_profile_regional_and_custom_proxies")

        if dry_run:
            info("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["forwarding_profile_regional_and_custom_proxies"]))
            return None

        def _apply(proxy_data: dict):
            # Apply folder override if specified
            if folder:
                proxy_data["folder"] = folder
            # Validate using the Pydantic model
            item = ForwardingProfileRegionalAndCustomProxy(**proxy_data)
            sdk_data = item.to_sdk_model()

            # Create via SDK client
            return scm_client.create_forwarding_profile_regional_and_custom_proxy(**sdk_data)

        return _bulk_load_items(config["forwarding_profile_regional_and_custom_proxies"], _apply, "forwarding profile regional and custom proxy")

    except ValidationError as e:
        error(f"Validation error: {e}")
        raise typer.Exit(code=1) from e


@set_app.command("forwarding-profile-regional-and-custom-proxy")
@handle_command_errors("creating/updating forwarding profile regional and custom proxy")
def set_forwarding_profile_regional_and_custom_proxy(
    folder: str = FOLDER_OPTION,
    name: str = NAME_OPTION,
    description: str | None = DESCRIPTION_OPTION,
    type: str | None = PROXY_TYPE_OPTION,
    proxy_1_fqdn: str | None = PROXY_1_FQDN_OPTION,
    proxy_1_port: int | None = PROXY_1_PORT_OPTION,
    proxy_1_location: str | None = PROXY_1_LOCATION_OPTION,
    proxy_2_fqdn: str | None = PROXY_2_FQDN_OPTION,
    proxy_2_port: int | None = PROXY_2_PORT_OPTION,
    proxy_2_location: str | None = PROXY_2_LOCATION_OPTION,
    fallback_option: str | None = FALLBACK_OPTION_OPTION,
    location_preference: str | None = LOCATION_PREFERENCE_OPTION,
):
    r"""Create or update a forwarding profile regional and custom proxy.

    Nested connectivity_preference and prisma_access_locations entries are
    supported via the load command's YAML schema.

    Examples
    --------
        scm set mobile-agent forwarding-profile-regional-and-custom-proxy \
        --folder "Mobile Users" \
        --name "emea-proxy" \
        --type gp-and-pac \
        --proxy-1-fqdn "proxy1.example.com" \
        --proxy-1-port 8080 \
        --fallback-option fail-open

    """
    # Build regional and custom proxy data
    proxy_data: dict[str, Any] = {
        "name": name,
    }

    if folder:
        proxy_data["folder"] = folder
    if description is not None:
        proxy_data["description"] = description
    if type is not None:
        proxy_data["type"] = type

    proxy_1: dict[str, Any] = {}
    if proxy_1_fqdn is not None:
        proxy_1["fqdn"] = proxy_1_fqdn
    if proxy_1_port is not None:
        proxy_1["port"] = proxy_1_port
    if proxy_1_location is not None:
        proxy_1["location"] = proxy_1_location
    if proxy_1:
        proxy_data["proxy_1"] = proxy_1

    proxy_2: dict[str, Any] = {}
    if proxy_2_fqdn is not None:
        proxy_2["fqdn"] = proxy_2_fqdn
    if proxy_2_port is not None:
        proxy_2["port"] = proxy_2_port
    if proxy_2_location is not None:
        proxy_2["location"] = proxy_2_location
    if proxy_2:
        proxy_data["proxy_2"] = proxy_2

    if fallback_option is not None:
        proxy_data["fallback_option"] = fallback_option
    if location_preference is not None:
        proxy_data["location_preference"] = location_preference

    # Validate using the Pydantic model
    try:
        regional_proxy = ForwardingProfileRegionalAndCustomProxy(**proxy_data)
        sdk_data = regional_proxy.to_sdk_model()
    except ValidationError as e:
        error(f"Validation error: {str(e)}")
        raise typer.Exit(code=1) from e

    # Call the SDK client
    result = scm_client.create_forwarding_profile_regional_and_custom_proxy(**sdk_data)

    # Get the action performed
    action = result.pop("__action__", "created")

    if action == "created":
        success(f"Created forwarding profile regional and custom proxy: {result.get('name', name)} in folder {result.get('folder', folder)}")
    elif action == "updated":
        success(f"Updated forwarding profile regional and custom proxy: {result.get('name', name)} in folder {result.get('folder', folder)}")
    elif action == "no_change":
        info(f"No changes needed for forwarding profile regional and custom proxy: {result.get('name', name)} in folder {result.get('folder', folder)}")

    return result


@show_app.command("forwarding-profile-regional-and-custom-proxy")
@handle_command_errors("showing forwarding profile regional and custom proxy")
def show_forwarding_profile_regional_and_custom_proxy(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the regional and custom proxy to show"),
    output: OutputFormat = OUTPUT_OPTION,
):
    """Display forwarding profile regional and custom proxies.

    Examples
    --------
        # List all regional and custom proxies in a folder (default behavior)
        scm show mobile-agent forwarding-profile-regional-and-custom-proxy --folder "Mobile Users"

        # Show a specific regional and custom proxy by name
        scm show mobile-agent forwarding-profile-regional-and-custom-proxy --folder "Mobile Users" --name "emea-proxy"

    """
    if name:
        # Get a specific regional and custom proxy by name
        proxy = scm_client.get_forwarding_profile_regional_and_custom_proxy(folder=folder, name=name)
        emit(proxy, output, title=f"Forwarding Profile Regional and Custom Proxy: {proxy.get('name', 'N/A')}")
        return proxy

    # Default: list all regional and custom proxies
    proxies_list = scm_client.list_forwarding_profile_regional_and_custom_proxies(folder=folder)
    emit(
        proxies_list,
        output,
        columns=["name", "type", "description"],
        title=f"Forwarding Profile Regional and Custom Proxies in folder '{folder}'",
    )
    return proxies_list
