"""Configuration utility module for scm-cli.

Handles YAML parsing and validation using Pydantic models.
"""

from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


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
