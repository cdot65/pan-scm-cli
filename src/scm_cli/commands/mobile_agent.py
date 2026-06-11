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
from ..utils.validators import AuthSetting, ForwardingProfile, ForwardingProfileDestination

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
