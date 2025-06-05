"""Configuration utility module for scm-cli.

Handles YAML parsing and validation using Dynaconf and Pydantic models.
"""

import os
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

from .context import get_context_aware_settings

T = TypeVar("T", bound=BaseModel)

# Define config paths
HOME_CONFIG_PATH = os.path.expanduser("~/.scm-cli/config.yaml")

# Initialize Dynaconf settings with context awareness
settings = get_context_aware_settings()


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
        Yaml.YAMLError: If the YAML file is invalid.

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

    Uses the following precedence order:
    1. Current context (set via 'scm context use')
    2. Environment variables (SCM_CLIENT_ID, etc.)
    3. Default settings

    Note: Legacy config file (~/.scm-cli/config.yaml) is no longer supported.
    Use contexts for multi-tenant support.

    Returns
    -------
        Dict containing client_id, client_secret, and tsg_id.

    Raises
    ------
        ValueError: If required authentication parameters are missing.

    Examples
    --------
        >>> auth = get_auth_config()
        >>> client = Scm(**auth) #noqa

    """
    # Get authentication from settings (which already includes context awareness)
    auth = {
        "client_id": settings.get("client_id", ""),
        "client_secret": settings.get("client_secret", ""),
        "tsg_id": settings.get("tsg_id", ""),
    }

    # For backward compatibility, also check the scm_ prefixed settings
    # but only if the non-prefixed values are empty
    if not auth["client_id"]:
        auth["client_id"] = settings.get("scm_client_id", "")
    if not auth["client_secret"]:
        auth["client_secret"] = settings.get("scm_client_secret", "")
    if not auth["tsg_id"]:
        auth["tsg_id"] = settings.get("scm_tsg_id", "")

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
