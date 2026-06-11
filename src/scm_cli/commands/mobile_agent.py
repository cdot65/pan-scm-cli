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
from ..utils.config import load_from_yaml, settings
from ..utils.context import get_current_context
from ..utils.sdk_client import scm_client
from ..utils.validators import AgentProfile, AuthSetting, ForwardingProfile, ForwardingProfileDestination, GlobalSetting, InfrastructureSetting, TunnelProfile

# =============================================================================================================================================================================================
# HELPER FUNCTIONS
# =============================================================================================================================================================================================


def show_context_info() -> None:
    """Display current context information if log level is INFO."""
    log_level = settings.get("log_level", "INFO").upper()
    if log_level == "INFO":
        current_context = get_current_context()
        if current_context:
            typer.echo(f"[INFO] Using authentication context: {current_context}", err=True)
        else:
            typer.echo(
                "[INFO] No context set, using environment variables or default settings",
                err=True,
            )


def get_default_backup_filename(object_type: str, location_type: str, location_value: str) -> str:
    """Generate default backup filename based on object type and location."""
    safe_location = location_value.lower().replace("/", "-").replace(" ", "-")
    return f"{object_type}-{safe_location}.yaml"


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
def show_agent_version(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the agent version to show"),
):
    """Display agent versions.

    Examples
    --------
        # List all agent versions in a folder (default behavior)
        scm show mobile-agent agent-version --folder "Mobile Users"

        # Show a specific agent version by name
        scm show mobile-agent agent-version --folder "Mobile Users" --name "5.2.0"

    """
    try:
        show_context_info()

        if name:
            # Get a specific agent version by name
            version = scm_client.get_agent_version(folder=folder, name=name)

            typer.echo(f"\nAgent Version: {version.get('name', 'N/A')}")
            typer.echo("=" * 80)

            # Display container location
            if version.get("folder"):
                typer.echo(f"Location: Folder '{version['folder']}'")
            elif version.get("snippet"):
                typer.echo(f"Location: Snippet '{version['snippet']}'")
            elif version.get("device"):
                typer.echo(f"Location: Device '{version['device']}'")
            else:
                typer.echo("Location: N/A")

            # Display version details
            if version.get("version"):
                typer.echo(f"Version: {version['version']}")
            if version.get("description"):
                typer.echo(f"Description: {version['description']}")
            if version.get("release_date"):
                typer.echo(f"Release Date: {version['release_date']}")
            if version.get("end_of_life_date"):
                typer.echo(f"End of Life: {version['end_of_life_date']}")
            if version.get("platform"):
                typer.echo(f"Platform: {version['platform']}")
            if version.get("id"):
                typer.echo(f"ID: {version['id']}")

            return version

        else:
            # Default: list all agent versions
            versions = scm_client.list_agent_versions(folder=folder)

            if not versions:
                typer.echo(f"No agent versions found in folder '{folder}'")
                return

            typer.echo(f"\nAgent Versions in folder '{folder}':")
            typer.echo("-" * 60)

            for ver in versions:
                typer.echo(f"Name: {ver.get('name', 'N/A')}")
                if ver.get("version"):
                    typer.echo(f"  Version: {ver['version']}")
                if ver.get("platform"):
                    typer.echo(f"  Platform: {ver['platform']}")
                if ver.get("release_date"):
                    typer.echo(f"  Release Date: {ver['release_date']}")
                typer.echo("-" * 60)

            return versions

    except Exception as e:
        typer.echo(f"Error showing agent version: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# AUTH SETTING COMMANDS
# =============================================================================================================================================================================================


@backup_app.command("auth-setting")
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
    try:
        # Validate location parameters
        location_type, location_value = validate_location_params(folder, snippet, device)

        # List all auth settings in the location with exact_match=True
        kwargs = {location_type: location_value}
        auth_settings = scm_client.list_auth_settings(**kwargs, exact_match=True)

        if not auth_settings:
            typer.echo(f"No auth settings found in {location_type} '{location_value}'")
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

        typer.echo(f"Successfully backed up {len(backup_data)} auth settings to {file}")
        return str(file)

    except Exception as e:
        typer.echo(f"Error backing up auth settings: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("auth-setting")
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
    try:
        if not force:
            typer.confirm(f"Delete auth setting '{name}' from folder '{folder}'?", abort=True)
        result = scm_client.delete_auth_setting(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted auth setting: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting auth setting: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("auth-setting")
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
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["auth_settings"]))
            return None

        # Apply each auth setting
        results = []
        created_count = 0
        updated_count = 0
        no_change_count = 0

        for setting_data in config["auth_settings"]:
            try:
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
                auth_setting = AuthSetting(**setting_data)
                sdk_data = auth_setting.to_sdk_model()

                # Create the auth setting via SDK client
                result = scm_client.create_auth_setting(**sdk_data)

                # Track action
                action = result.pop("__action__", "created")
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created auth setting: {result.get('name', 'N/A')}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated auth setting: {result.get('name', 'N/A')}")
                elif action == "no_change":
                    no_change_count += 1
                    typer.echo(f"No changes needed for auth setting: {result.get('name', 'N/A')}")

                results.append(result)

            except Exception as e:
                typer.echo(f"Error loading auth setting '{setting_data.get('name', 'unknown')}': {str(e)}", err=True)

        # Summary
        typer.echo(f"\nSummary: {created_count} created, {updated_count} updated, {no_change_count} unchanged")

        return results

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading auth settings: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("auth-setting")
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
    try:
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
        auth_setting = AuthSetting(**setting_data)
        sdk_data = auth_setting.to_sdk_model()

        # Call the SDK client
        result = scm_client.create_auth_setting(**sdk_data)

        # Get the action performed
        action = result.pop("__action__", "created")

        if action == "created":
            typer.echo(f"Created auth setting: {result.get('name', name)} in folder {result.get('folder', folder)}")
        elif action == "updated":
            typer.echo(f"Updated auth setting: {result.get('name', name)} in folder {result.get('folder', folder)}")
        elif action == "no_change":
            typer.echo(f"No changes needed for auth setting: {result.get('name', name)} in folder {result.get('folder', folder)}")

        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating auth setting: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("auth-setting")
def show_auth_setting(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the auth setting to show"),
):
    """Display auth settings.

    Examples
    --------
        # List all auth settings in a folder (default behavior)
        scm show mobile-agent auth-setting --folder "Mobile Users"

        # Show a specific auth setting by name
        scm show mobile-agent auth-setting --folder "Mobile Users" --name "saml-auth"

    """
    try:
        show_context_info()

        if name:
            # Get a specific auth setting by name
            setting = scm_client.get_auth_setting(folder=folder, name=name)

            typer.echo(f"\nAuth Setting: {setting.get('name', 'N/A')}")
            typer.echo("=" * 80)

            # Display container location
            if setting.get("folder"):
                typer.echo(f"Location: Folder '{setting['folder']}'")
            elif setting.get("snippet"):
                typer.echo(f"Location: Snippet '{setting['snippet']}'")
            elif setting.get("device"):
                typer.echo(f"Location: Device '{setting['device']}'")
            else:
                typer.echo("Location: N/A")

            # Display auth setting details
            if setting.get("description"):
                typer.echo(f"Description: {setting['description']}")
            if setting.get("authentication_profile"):
                typer.echo(f"Authentication Profile: {setting['authentication_profile']}")
            if setting.get("os"):
                typer.echo(f"OS: {setting['os']}")
            if setting.get("user_credential_or_client_cert_required") is not None:
                typer.echo(f"User Credential or Client Cert Required: {setting['user_credential_or_client_cert_required']}")
            if setting.get("id"):
                typer.echo(f"ID: {setting['id']}")

            return setting

        else:
            # Default: list all auth settings
            settings_list = scm_client.list_auth_settings(folder=folder)

            if not settings_list:
                typer.echo(f"No auth settings found in folder '{folder}'")
                return

            typer.echo(f"\nAuth Settings in folder '{folder}':")
            typer.echo("-" * 60)

            for setting in settings_list:
                typer.echo(f"Name: {setting.get('name', 'N/A')}")
                if setting.get("authentication_profile"):
                    typer.echo(f"  Authentication Profile: {setting['authentication_profile']}")
                if setting.get("os"):
                    typer.echo(f"  OS: {setting['os']}")
                if setting.get("description"):
                    typer.echo(f"  Description: {setting['description']}")
                typer.echo("-" * 60)

            return settings_list

    except Exception as e:
        typer.echo(f"Error showing auth setting: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


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
def backup_forwarding_profile(
    folder: str = BACKUP_FOLDER_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup all forwarding profiles from a folder to a YAML file.

    Examples
    --------
        scm backup mobile-agent forwarding-profile --folder "Mobile Users"

    """
    try:
        if not folder:
            folder = "Mobile Users"

        profiles = scm_client.list_forwarding_profiles(folder=folder)

        if not profiles:
            typer.echo(f"No forwarding profiles found in folder '{folder}'")
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

        typer.echo(f"Successfully backed up {len(backup_data)} forwarding profiles to {file}")
        return str(file)

    except Exception as e:
        typer.echo(f"Error backing up forwarding profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("forwarding-profile")
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
    try:
        identifier = profile_id or name
        if not force:
            typer.confirm(f"Delete forwarding profile '{identifier}'?", abort=True)
        result = scm_client.delete_forwarding_profile(folder=folder, name=name, profile_id=profile_id)
        if result:
            typer.echo(f"Deleted forwarding profile: {identifier}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting forwarding profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("forwarding-profile")
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
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["forwarding_profiles"]))
            return None

        results = []
        created_count = 0
        updated_count = 0
        no_change_count = 0

        for profile_data in config["forwarding_profiles"]:
            try:
                if folder:
                    profile_data["folder"] = folder

                profile = ForwardingProfile(**profile_data)
                sdk_data = profile.to_sdk_model()

                result = scm_client.create_forwarding_profile(**sdk_data)

                action = result.pop("__action__", "created")
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created forwarding profile: {result.get('name', 'N/A')}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated forwarding profile: {result.get('name', 'N/A')}")
                elif action == "no_change":
                    no_change_count += 1
                    typer.echo(f"No changes needed for forwarding profile: {result.get('name', 'N/A')}")

                results.append(result)

            except Exception as e:
                typer.echo(f"Error loading forwarding profile '{profile_data.get('name', 'unknown')}': {str(e)}", err=True)

        typer.echo(f"\nSummary: {created_count} created, {updated_count} updated, {no_change_count} unchanged")

        return results

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading forwarding profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("forwarding-profile")
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
    try:
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
                typer.echo(
                    f"Error: --profile-type must be one of: {', '.join(sorted(_PROFILE_TYPE_KEY_MAP))}",
                    err=True,
                )
                raise typer.Exit(code=1)
            type_config: dict[str, Any] = {}
            if pac_upload is not None:
                type_config["pac_upload"] = pac_upload
            profile_data["type"] = {type_key: type_config}

        profile = ForwardingProfile(**profile_data)
        sdk_data = profile.to_sdk_model()

        result = scm_client.create_forwarding_profile(**sdk_data)

        action = result.pop("__action__", "created")

        if action == "created":
            typer.echo(f"Created forwarding profile: {result.get('name', name)}")
        elif action == "updated":
            typer.echo(f"Updated forwarding profile: {result.get('name', name)}")
        elif action == "no_change":
            typer.echo(f"No changes needed for forwarding profile: {result.get('name', name)}")

        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error creating/updating forwarding profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("forwarding-profile")
def show_forwarding_profile(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the forwarding profile to show"),
    profile_id: str | None = PROFILE_ID_OPTION,
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
    try:
        show_context_info()

        if profile_id or name:
            profile = scm_client.get_forwarding_profile(folder=folder, name=name, profile_id=profile_id)

            typer.echo(f"\nForwarding Profile: {profile.get('name', 'N/A')}")
            typer.echo("=" * 80)

            if profile.get("description"):
                typer.echo(f"Description: {profile['description']}")
            if profile.get("definition_method"):
                typer.echo(f"Definition Method: {profile['definition_method']}")
            if profile.get("type"):
                typer.echo("Type:")
                typer.echo(yaml.dump(profile["type"], default_flow_style=False, sort_keys=False).rstrip())
            if profile.get("id"):
                typer.echo(f"ID: {profile['id']}")

            return profile

        else:
            profiles = scm_client.list_forwarding_profiles(folder=folder)

            if not profiles:
                typer.echo(f"No forwarding profiles found in folder '{folder or 'Mobile Users'}'")
                return None

            typer.echo(f"\nForwarding Profiles in folder '{folder or 'Mobile Users'}':")
            typer.echo("-" * 60)

            for profile in profiles:
                typer.echo(f"Name: {profile.get('name', 'N/A')}")
                if profile.get("definition_method"):
                    typer.echo(f"  Definition Method: {profile['definition_method']}")
                if profile.get("type"):
                    typer.echo(f"  Profile Type: {', '.join(profile['type'].keys())}")
                if profile.get("description"):
                    typer.echo(f"  Description: {profile['description']}")
                if profile.get("id"):
                    typer.echo(f"  ID: {profile['id']}")
                typer.echo("-" * 60)

            return profiles

    except Exception as e:
        typer.echo(f"Error showing forwarding profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


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
def backup_forwarding_profile_destination(
    folder: str = BACKUP_FOLDER_OPTION,
    file: Path | None = BACKUP_FILE_OPTION,
):
    """Backup all forwarding profile destinations from a folder to a YAML file.

    Examples
    --------
        scm backup mobile-agent forwarding-profile-destination --folder "Mobile Users"

    """
    try:
        if not folder:
            folder = "Mobile Users"

        destinations = scm_client.list_forwarding_profile_destinations(folder=folder)

        if not destinations:
            typer.echo(f"No forwarding profile destinations found in folder '{folder}'")
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

        typer.echo(f"Successfully backed up {len(backup_data)} forwarding profile destinations to {file}")
        return str(file)

    except Exception as e:
        typer.echo(f"Error backing up forwarding profile destinations: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("forwarding-profile-destination")
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
    try:
        identifier = destination_id or name
        if not force:
            typer.confirm(f"Delete forwarding profile destination '{identifier}'?", abort=True)
        result = scm_client.delete_forwarding_profile_destination(folder=folder, name=name, destination_id=destination_id)
        if result:
            typer.echo(f"Deleted forwarding profile destination: {identifier}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting forwarding profile destination: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("forwarding-profile-destination")
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
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["forwarding_profile_destinations"]))
            return None

        results = []
        created_count = 0
        updated_count = 0
        no_change_count = 0

        for destination_data in config["forwarding_profile_destinations"]:
            try:
                if folder:
                    destination_data["folder"] = folder

                destination = ForwardingProfileDestination(**destination_data)
                sdk_data = destination.to_sdk_model()

                result = scm_client.create_forwarding_profile_destination(**sdk_data)

                action = result.pop("__action__", "created")
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created forwarding profile destination: {result.get('name', 'N/A')}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated forwarding profile destination: {result.get('name', 'N/A')}")
                elif action == "no_change":
                    no_change_count += 1
                    typer.echo(f"No changes needed for forwarding profile destination: {result.get('name', 'N/A')}")

                results.append(result)

            except Exception as e:
                typer.echo(f"Error loading forwarding profile destination '{destination_data.get('name', 'unknown')}': {str(e)}", err=True)

        typer.echo(f"\nSummary: {created_count} created, {updated_count} updated, {no_change_count} unchanged")

        return results

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading forwarding profile destinations: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("forwarding-profile-destination")
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
    try:
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

        destination = ForwardingProfileDestination(**destination_data)
        sdk_data = destination.to_sdk_model()

        result = scm_client.create_forwarding_profile_destination(**sdk_data)

        action = result.pop("__action__", "created")

        if action == "created":
            typer.echo(f"Created forwarding profile destination: {result.get('name', name)}")
        elif action == "updated":
            typer.echo(f"Updated forwarding profile destination: {result.get('name', name)}")
        elif action == "no_change":
            typer.echo(f"No changes needed for forwarding profile destination: {result.get('name', name)}")

        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating forwarding profile destination: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("forwarding-profile-destination")
def show_forwarding_profile_destination(
    folder: str = FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the forwarding profile destination to show"),
    destination_id: str | None = PROFILE_ID_OPTION,
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
    try:
        show_context_info()

        if destination_id or name:
            destination = scm_client.get_forwarding_profile_destination(folder=folder, name=name, destination_id=destination_id)

            typer.echo(f"\nForwarding Profile Destination: {destination.get('name', 'N/A')}")
            typer.echo("=" * 80)

            if destination.get("description"):
                typer.echo(f"Description: {destination['description']}")
            if destination.get("fqdn"):
                typer.echo("FQDN Entries:")
                for entry in destination["fqdn"]:
                    port_suffix = f":{entry['port']}" if entry.get("port") else ""
                    typer.echo(f"  - {entry.get('name', 'N/A')}{port_suffix}")
            if destination.get("ip_addresses"):
                typer.echo("IP Address Entries:")
                for entry in destination["ip_addresses"]:
                    port_suffix = f":{entry['port']}" if entry.get("port") else ""
                    typer.echo(f"  - {entry.get('name', 'N/A')}{port_suffix}")
            if destination.get("id"):
                typer.echo(f"ID: {destination['id']}")

            return destination

        else:
            destinations = scm_client.list_forwarding_profile_destinations(folder=folder)

            if not destinations:
                typer.echo(f"No forwarding profile destinations found in folder '{folder or 'Mobile Users'}'")
                return None

            typer.echo(f"\nForwarding Profile Destinations in folder '{folder or 'Mobile Users'}':")
            typer.echo("-" * 60)

            for destination in destinations:
                typer.echo(f"Name: {destination.get('name', 'N/A')}")
                if destination.get("fqdn"):
                    typer.echo(f"  FQDN Entries: {len(destination['fqdn'])}")
                if destination.get("ip_addresses"):
                    typer.echo(f"  IP Address Entries: {len(destination['ip_addresses'])}")
                if destination.get("description"):
                    typer.echo(f"  Description: {destination['description']}")
                if destination.get("id"):
                    typer.echo(f"  ID: {destination['id']}")
                typer.echo("-" * 60)

            return destinations

    except Exception as e:
        typer.echo(f"Error showing forwarding profile destination: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


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


def _echo_nested(profile: dict[str, Any], keys: tuple[str, ...]) -> None:
    """Echo nested dict fields of a profile as indented YAML blocks."""
    for key in keys:
        if profile.get(key):
            typer.echo(f"{key.replace('_', ' ').title()}:")
            block = yaml.dump(profile[key], default_flow_style=False, sort_keys=False)
            typer.echo("\n".join(f"  {line}" for line in block.splitlines()))


@backup_app.command("agent-profile")
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
    try:
        profiles = scm_client.list_agent_profiles(folder=folder)

        if not profiles:
            typer.echo(f"No agent profiles found in folder '{folder}'")
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

        typer.echo(f"Successfully backed up {len(backup_data)} agent profiles to {file}")
        return str(file)

    except Exception as e:
        typer.echo(f"Error backing up agent profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("agent-profile")
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
    try:
        if not force:
            typer.confirm(f"Delete agent profile '{name}' from folder '{folder}'?", abort=True)
        result = scm_client.delete_agent_profile(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted agent profile: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting agent profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("agent-profile")
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
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["agent_profiles"]))
            return None

        results = []
        created_count = 0
        updated_count = 0
        no_change_count = 0

        for profile_data in config["agent_profiles"]:
            try:
                if folder:
                    profile_data["folder"] = folder

                agent_profile = AgentProfile(**profile_data)
                sdk_data = agent_profile.to_sdk_model()

                result = scm_client.create_agent_profile(**sdk_data)

                action = result.pop("__action__", "created")
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created agent profile: {result.get('name', 'N/A')}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated agent profile: {result.get('name', 'N/A')}")
                elif action == "no_change":
                    no_change_count += 1
                    typer.echo(f"No changes needed for agent profile: {result.get('name', 'N/A')}")

                results.append(result)

            except Exception as e:
                typer.echo(f"Error loading agent profile '{profile_data.get('name', 'unknown')}': {str(e)}", err=True)

        typer.echo(f"\nSummary: {created_count} created, {updated_count} updated, {no_change_count} unchanged")

        return results

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading agent profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("agent-profile")
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
    try:
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

        agent_profile = AgentProfile(**profile_data)
        sdk_data = agent_profile.to_sdk_model()

        result = scm_client.create_agent_profile(**sdk_data)

        action = result.pop("__action__", "created")

        if action == "created":
            typer.echo(f"Created agent profile: {result.get('name', name)} in folder {result.get('folder', folder)}")
        elif action == "updated":
            typer.echo(f"Updated agent profile: {result.get('name', name)} in folder {result.get('folder', folder)}")
        elif action == "no_change":
            typer.echo(f"No changes needed for agent profile: {result.get('name', name)} in folder {result.get('folder', folder)}")

        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating agent profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("agent-profile")
def show_agent_profile(
    folder: str = GP_FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the agent profile to show"),
):
    """Display agent profiles (GlobalProtect app settings).

    Examples
    --------
        # List all agent profiles (default behavior)
        scm show mobile-agent agent-profile --folder "Mobile Users"

        # Show a specific agent profile by name
        scm show mobile-agent agent-profile --folder "Mobile Users" --name "corp-app-settings"

    """
    try:
        show_context_info()

        if name:
            profile = scm_client.get_agent_profile(folder=folder, name=name)

            typer.echo(f"\nAgent Profile: {profile.get('name', 'N/A')}")
            typer.echo("=" * 80)
            typer.echo(f"Location: Folder '{profile.get('folder', folder)}'")

            if profile.get("os"):
                typer.echo(f"OS: {', '.join(profile['os'])}")
            if profile.get("save_user_credentials") is not None:
                typer.echo(f"Save User Credentials: {profile['save_user_credentials']}")
            if profile.get("source_user"):
                typer.echo(f"Source Users: {', '.join(profile['source_user'])}")
            if profile.get("third_party_vpn_clients"):
                typer.echo(f"Third Party VPN Clients: {', '.join(profile['third_party_vpn_clients'])}")
            _echo_nested(
                profile,
                (
                    "gp_app_config",
                    "agent_ui",
                    "authentication_override",
                    "certificate",
                    "client_certificate",
                    "custom_checks",
                    "gateways",
                    "hip_collection",
                    "internal_host_detection",
                    "internal_host_detection_v6",
                    "machine_account_exists_with_serialno",
                ),
            )
            if profile.get("id"):
                typer.echo(f"ID: {profile['id']}")

            return profile

        else:
            profiles = scm_client.list_agent_profiles(folder=folder)

            if not profiles:
                typer.echo(f"No agent profiles found in folder '{folder}'")
                return

            typer.echo(f"\nAgent Profiles in folder '{folder}':")
            typer.echo("-" * 60)

            for profile in profiles:
                typer.echo(f"Name: {profile.get('name', 'N/A')}")
                if profile.get("os"):
                    typer.echo(f"  OS: {', '.join(profile['os'])}")
                if profile.get("save_user_credentials") is not None:
                    typer.echo(f"  Save User Credentials: {profile['save_user_credentials']}")
                typer.echo("-" * 60)

            return profiles

    except Exception as e:
        typer.echo(f"Error showing agent profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# TUNNEL PROFILE COMMANDS (agent3)
# =============================================================================================================================================================================================


@backup_app.command("tunnel-profile")
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
    try:
        profiles = scm_client.list_tunnel_profiles(folder=folder)

        if not profiles:
            typer.echo(f"No tunnel profiles found in folder '{folder}'")
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

        typer.echo(f"Successfully backed up {len(backup_data)} tunnel profiles to {file}")
        return str(file)

    except Exception as e:
        typer.echo(f"Error backing up tunnel profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("tunnel-profile")
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
    try:
        if not force:
            typer.confirm(f"Delete tunnel profile '{name}' from folder '{folder}'?", abort=True)
        result = scm_client.delete_tunnel_profile(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted tunnel profile: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting tunnel profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("tunnel-profile")
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
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["tunnel_profiles"]))
            return None

        results = []
        created_count = 0
        updated_count = 0
        no_change_count = 0

        for profile_data in config["tunnel_profiles"]:
            try:
                if folder:
                    profile_data["folder"] = folder

                tunnel_profile = TunnelProfile(**profile_data)
                sdk_data = tunnel_profile.to_sdk_model()

                result = scm_client.create_tunnel_profile(**sdk_data)

                action = result.pop("__action__", "created")
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created tunnel profile: {result.get('name', 'N/A')}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated tunnel profile: {result.get('name', 'N/A')}")
                elif action == "no_change":
                    no_change_count += 1
                    typer.echo(f"No changes needed for tunnel profile: {result.get('name', 'N/A')}")

                results.append(result)

            except Exception as e:
                typer.echo(f"Error loading tunnel profile '{profile_data.get('name', 'unknown')}': {str(e)}", err=True)

        typer.echo(f"\nSummary: {created_count} created, {updated_count} updated, {no_change_count} unchanged")

        return results

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading tunnel profiles: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("tunnel-profile")
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
    try:
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

        tunnel_profile = TunnelProfile(**profile_data)
        sdk_data = tunnel_profile.to_sdk_model()

        result = scm_client.create_tunnel_profile(**sdk_data)

        action = result.pop("__action__", "created")

        if action == "created":
            typer.echo(f"Created tunnel profile: {result.get('name', name)} in folder {result.get('folder', folder)}")
        elif action == "updated":
            typer.echo(f"Updated tunnel profile: {result.get('name', name)} in folder {result.get('folder', folder)}")
        elif action == "no_change":
            typer.echo(f"No changes needed for tunnel profile: {result.get('name', name)} in folder {result.get('folder', folder)}")

        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating tunnel profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("tunnel-profile")
def show_tunnel_profile(
    folder: str = GP_FOLDER_OPTION,
    name: str | None = typer.Option(None, "--name", help="Name of the tunnel profile to show"),
):
    """Display tunnel profiles (GlobalProtect tunnel settings).

    Examples
    --------
        # List all tunnel profiles (default behavior)
        scm show mobile-agent tunnel-profile --folder "Mobile Users"

        # Show a specific tunnel profile by name
        scm show mobile-agent tunnel-profile --folder "Mobile Users" --name "corp-tunnel"

    """
    try:
        show_context_info()

        if name:
            profile = scm_client.get_tunnel_profile(folder=folder, name=name)

            typer.echo(f"\nTunnel Profile: {profile.get('name', 'N/A')}")
            typer.echo("=" * 80)
            typer.echo(f"Location: Folder '{profile.get('folder', folder)}'")

            if profile.get("no_direct_access_to_local_network") is not None:
                typer.echo(f"No Direct Access To Local Network: {profile['no_direct_access_to_local_network']}")
            if profile.get("retrieve_framed_ip_address") is not None:
                typer.echo(f"Retrieve Framed IP Address: {profile['retrieve_framed_ip_address']}")
            if profile.get("os"):
                typer.echo(f"OS: {', '.join(profile['os'])}")
            if profile.get("source_user"):
                typer.echo(f"Source Users: {', '.join(profile['source_user'])}")
            _echo_nested(profile, ("split_tunneling", "source_address", "authentication_override"))
            if profile.get("id"):
                typer.echo(f"ID: {profile['id']}")

            return profile

        else:
            profiles = scm_client.list_tunnel_profiles(folder=folder)

            if not profiles:
                typer.echo(f"No tunnel profiles found in folder '{folder}'")
                return

            typer.echo(f"\nTunnel Profiles in folder '{folder}':")
            typer.echo("-" * 60)

            for profile in profiles:
                typer.echo(f"Name: {profile.get('name', 'N/A')}")
                if profile.get("os"):
                    typer.echo(f"  OS: {', '.join(profile['os'])}")
                if profile.get("no_direct_access_to_local_network") is not None:
                    typer.echo(f"  No Direct Access To Local Network: {profile['no_direct_access_to_local_network']}")
                typer.echo("-" * 60)

            return profiles

    except Exception as e:
        typer.echo(f"Error showing tunnel profile: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


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
    try:
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
        infrastructure_setting = InfrastructureSetting(**setting_data)
        sdk_data = infrastructure_setting.to_sdk_model()

        # Call the SDK client
        result = scm_client.create_infrastructure_setting(**sdk_data)

        # Get the action performed
        action = result.pop("__action__", "created")

        if action == "created":
            typer.echo(f"Created infrastructure setting: {result.get('name', name)} in folder {folder}")
        elif action == "updated":
            typer.echo(f"Updated infrastructure setting: {result.get('name', name)} in folder {folder}")
        elif action == "no_change":
            typer.echo(f"No changes needed for infrastructure setting: {result.get('name', name)} in folder {folder}")

        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error creating/updating infrastructure setting: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@show_app.command("infrastructure-setting")
def show_infrastructure_setting(
    folder: str = INFRA_FOLDER_OPTION,
    name: str = INFRA_NAME_OPTION,
):
    """Display an infrastructure setting.

    The SCM API requires a name for this endpoint; there is no list-all mode.

    Examples
    --------
        scm show mobile-agent infrastructure-setting --name "gp-infra"

    """
    try:
        show_context_info()

        setting = scm_client.get_infrastructure_setting(folder=folder, name=name)

        typer.echo(f"\nInfrastructure Setting: {setting.get('name', 'N/A')}")
        typer.echo("=" * 80)
        typer.echo(f"Location: Folder '{folder}'")

        if setting.get("portal_hostname"):
            typer.echo(f"Portal Hostname: {yaml.dump(setting['portal_hostname'], default_flow_style=True).strip()}")
        if setting.get("dns_servers"):
            typer.echo(f"DNS Servers: {yaml.dump(setting['dns_servers'], default_flow_style=True).strip()}")
        if setting.get("ip_pools"):
            typer.echo(f"IP Pools: {yaml.dump(setting['ip_pools'], default_flow_style=True).strip()}")
        if setting.get("enable_wins"):
            typer.echo(f"WINS: {yaml.dump(setting['enable_wins'], default_flow_style=True).strip()}")
        if setting.get("ipv6") is not None:
            typer.echo(f"IPv6: {setting['ipv6']}")
        if setting.get("udp_queries"):
            typer.echo(f"UDP Queries: {yaml.dump(setting['udp_queries'], default_flow_style=True).strip()}")
        if setting.get("static_ip_pools"):
            typer.echo(f"Static IP Pools: {yaml.dump(setting['static_ip_pools'], default_flow_style=True).strip()}")
        if setting.get("id"):
            typer.echo(f"ID: {setting['id']}")

        return setting

    except Exception as e:
        typer.echo(f"Error showing infrastructure setting: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@delete_app.command("infrastructure-setting")
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
    try:
        if not force:
            typer.confirm(f"Delete infrastructure setting '{name}' from folder '{folder}'?", abort=True)
        result = scm_client.delete_infrastructure_setting(folder=folder, name=name)
        if result:
            typer.echo(f"Deleted infrastructure setting: {name} from folder {folder}")
        return result
    except Exception as e:
        typer.echo(f"Error deleting infrastructure setting: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@backup_app.command("infrastructure-setting")
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
    try:
        settings_list = scm_client.list_infrastructure_settings(folder=folder, name=name)

        if not settings_list:
            typer.echo(f"No infrastructure settings named '{name}' found in folder '{folder}'")
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

        typer.echo(f"Successfully backed up {len(backup_data)} infrastructure settings to {file}")
        return str(file)

    except Exception as e:
        typer.echo(f"Error backing up infrastructure settings: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@load_app.command("infrastructure-setting")
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
            typer.echo("Dry run mode: would apply the following configurations:")
            typer.echo(yaml.dump(config["infrastructure_settings"]))
            return None

        results = []
        created_count = 0
        updated_count = 0
        no_change_count = 0

        for setting_data in config["infrastructure_settings"]:
            try:
                # Apply folder override if specified (only valid value is 'Mobile Users')
                if folder:
                    setting_data["folder"] = folder

                # Validate using the Pydantic model
                infrastructure_setting = InfrastructureSetting(**setting_data)
                sdk_data = infrastructure_setting.to_sdk_model()

                result = scm_client.create_infrastructure_setting(**sdk_data)

                action = result.pop("__action__", "created")
                if action == "created":
                    created_count += 1
                    typer.echo(f"Created infrastructure setting: {result.get('name', 'N/A')}")
                elif action == "updated":
                    updated_count += 1
                    typer.echo(f"Updated infrastructure setting: {result.get('name', 'N/A')}")
                elif action == "no_change":
                    no_change_count += 1
                    typer.echo(f"No changes needed for infrastructure setting: {result.get('name', 'N/A')}")

                results.append(result)

            except Exception as e:
                typer.echo(f"Error loading infrastructure setting '{setting_data.get('name', 'unknown')}': {str(e)}", err=True)

        typer.echo(f"\nSummary: {created_count} created, {updated_count} updated, {no_change_count} unchanged")

        return results

    except ValidationError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error loading infrastructure settings: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


# =============================================================================================================================================================================================
# GLOBAL SETTING COMMANDS (SINGLETON — SHOW/SET ONLY)
# =============================================================================================================================================================================================


@show_app.command("global-setting")
def show_global_setting():
    """Display the GlobalProtect global settings.

    Global settings are a tenant-wide singleton; there is nothing to filter by.

    Examples
    --------
        scm show mobile-agent global-setting

    """
    try:
        show_context_info()

        setting = scm_client.get_global_settings()

        typer.echo("\nGlobalProtect Global Settings")
        typer.echo("=" * 80)

        if setting.get("agent_version"):
            typer.echo(f"Agent Version: {setting['agent_version']}")
        if setting.get("manual_gateway"):
            typer.echo(f"Manual Gateway: {yaml.dump(setting['manual_gateway'], default_flow_style=True).strip()}")
        if not setting:
            typer.echo("No global settings configured")

        return setting

    except Exception as e:
        typer.echo(f"Error showing global settings: {str(e)}", err=True)
        raise typer.Exit(code=1) from e


@set_app.command("global-setting")
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
    try:
        # Build setting data; the Pydantic model parses JSON strings into structures
        setting_data: dict[str, Any] = {}
        if agent_version is not None:
            setting_data["agent_version"] = agent_version
        if manual_gateway is not None:
            setting_data["manual_gateway"] = manual_gateway

        # Validate using the Pydantic model (requires at least one field)
        global_setting = GlobalSetting(**setting_data)
        sdk_data = global_setting.to_sdk_model()

        result = scm_client.update_global_settings(**sdk_data)
        result.pop("__action__", None)

        typer.echo("Updated GlobalProtect global settings")
        return result

    except ValidationError as e:
        typer.echo(f"Validation error: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"Error updating global settings: {str(e)}", err=True)
        raise typer.Exit(code=1) from e
