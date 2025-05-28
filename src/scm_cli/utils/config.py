"""Configuration utility module for scm-cli.

Handles YAML parsing and validation using Dynaconf and Pydantic models.
"""

import os
from typing import Any, TypeVar

import yaml
from dynaconf import Dynaconf
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

# Define config paths
HOME_CONFIG_PATH = os.path.expanduser("~/.scm-cli/config.yaml")

# Initialize Dynaconf settings with both environment variables and config file
settings = Dynaconf(
    envvar_prefix="SCM",
    settings_files=[
        # Local project settings (for development)
        "settings.yaml",
        ".secrets.yaml",
        # User config in home directory (as documented in README)
        HOME_CONFIG_PATH,
    ],
    load_dotenv=True,
    environments=False,  # Disable environments to ensure home config is loaded properly
    merge_enabled=True,
)


def load_from_yaml(file_path: str, submodule: str) -> dict[str, Any]:
    """Load and parse a YAML configuration file.

    Args:
    ----
        file_path: Path to the YAML file.
        submodule: Submodule key to extract from the YAML.

    Returns:
    -------
        Parsed YAML data.

    Raises:
    ------
        ValueError: If the submodule key is missing from the YAML.
        yaml.YAMLError: If the YAML file is invalid.

    """
    try:
        with open(file_path) as f:
            config = yaml.safe_load(f)

        if not config:
            raise ValueError(f"Empty or invalid YAML file: {file_path}")

        if submodule not in config:
            raise ValueError(f"Missing '{submodule}' section in YAML file: {file_path}")

        return config
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file {file_path}: {str(e)}") from e
    except FileNotFoundError as e:
        raise FileNotFoundError(f"YAML file not found: {file_path}") from e


def get_auth_config() -> dict[str, str]:
    """Get SCM API authentication configuration from dynaconf settings.

    Prioritizes environment variables over config file values.
    Checks for client_id, client_secret, and tsg_id from either source.

    Returns
    -------
        Dict containing client_id, client_secret, and tsg_id.

    Raises
    ------
        ValueError: If required authentication parameters are missing.

    Examples
    --------
        >>> auth = get_auth_config()
        >>> client = Scm(**auth)

    """
    # Check if home config file exists and manually load it if Dynaconf didn't pick it up
    home_config: dict[str, Any] = {}
    if os.path.exists(HOME_CONFIG_PATH) and not settings.get("client_id"):
        try:
            with open(HOME_CONFIG_PATH) as f:
                home_config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Error loading {HOME_CONFIG_PATH}: {e}")

    # First try environment variables (PREFIX_client_id)
    auth = {
        "client_id": settings.get("client_id"),
        "client_secret": settings.get("client_secret"),
        "tsg_id": settings.get("tsg_id"),
    }

    # For backward compatibility, also check the scm_ prefixed settings
    if not auth["client_id"]:
        auth["client_id"] = settings.get("scm_client_id")
    if not auth["client_secret"]:
        auth["client_secret"] = settings.get("scm_client_secret")
    if not auth["tsg_id"]:
        auth["tsg_id"] = settings.get("scm_tsg_id")

    # Try the manually loaded home config values as a last resort
    if not auth["client_id"] and "client_id" in home_config:
        auth["client_id"] = home_config.get("client_id")
    if not auth["client_secret"] and "client_secret" in home_config:
        auth["client_secret"] = home_config.get("client_secret")
    if not auth["tsg_id"] and "tsg_id" in home_config:
        auth["tsg_id"] = home_config.get("tsg_id")

    # Check for missing parameters
    missing = [k for k, v in auth.items() if not v]
    if missing:
        raise ValueError(f"Missing required authentication parameters: {', '.join(missing)}")

    return auth


def get_credentials() -> dict[str, str]:
    """Get SCM API credentials from dynaconf settings.

    This function is kept for backward compatibility.
    Use get_auth_config() for new code.

    Returns
    -------
        Dict containing client_id, client_secret, and tsg_id.

    Raises
    ------
        ValueError: If required credentials are missing.

    """
    return get_auth_config()
