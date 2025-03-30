"""Configuration utility module for scm-cli.

Handles YAML parsing and validation using Dynaconf and Pydantic models.
"""

from typing import Any, TypeVar

import yaml
from dynaconf import Dynaconf
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

# Initialize Dynaconf settings
settings = Dynaconf(
    envvar_prefix="SCM",
    settings_files=["settings.yaml", ".secrets.yaml"],
    environments=True,
    merge_enabled=True,
)


def load_from_yaml(file_path: str, submodule: str) -> dict[str, Any]:
    """Load and parse a YAML configuration file.

    Args:
    ----
        file_path: Path to the YAML file
        submodule: The submodule key to extract from the YAML

    Returns:
    -------
        Dict containing the parsed YAML data

    Raises:
    ------
        ValueError: If the submodule key is missing from the YAML
        yaml.YAMLError: If the YAML file is invalid

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


def get_credentials() -> dict[str, str]:
    """Get SCM API credentials from dynaconf settings.

    Returns
    -------
        Dict containing client_id, client_secret, and tsg_id

    Raises
    ------
        ValueError: If required credentials are missing

    """
    client_id = settings.get("scm_client_id")
    client_secret = settings.get("scm_client_secret")
    tsg_id = settings.get("scm_tsg_id")

    if not client_id or not client_secret or not tsg_id:
        raise ValueError("Missing required SCM API credentials. Check your .secrets.yaml file.")

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "tsg_id": tsg_id,
    }
