"""Context management for multi-tenant SCM CLI authentication.

This module provides functionality to manage multiple SCM tenant contexts,
allowing users to switch between different authentication profiles.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from dynaconf import Dynaconf

# Context configuration paths
CONTEXT_DIR = os.path.expanduser("~/.scm-cli/contexts")
CURRENT_CONTEXT_FILE = os.path.expanduser("~/.scm-cli/current-context")


def ensure_context_dir() -> None:
    """Ensure the context directory exists."""
    Path(CONTEXT_DIR).mkdir(parents=True, exist_ok=True)
    Path(CURRENT_CONTEXT_FILE).parent.mkdir(parents=True, exist_ok=True)


def list_contexts() -> list[str]:
    """List all available contexts.

    Returns
    -------
        List of context names.

    """
    ensure_context_dir()
    contexts = []

    if os.path.exists(CONTEXT_DIR):
        for file in os.listdir(CONTEXT_DIR):
            if file.endswith(".yaml") or file.endswith(".yml"):
                context_name = file.rsplit(".", 1)[0]
                contexts.append(context_name)

    return sorted(contexts)


def get_current_context() -> str | None:
    """Get the name of the current context.

    Returns
    -------
        Current context name or None if not set.

    """
    if os.path.exists(CURRENT_CONTEXT_FILE):
        try:
            with open(CURRENT_CONTEXT_FILE) as f:
                return f.read().strip()
        except Exception as e:
            print(f"Error reading current context: {e}")
            return None
    return None


def set_current_context(context_name: str) -> None:
    """Set the current context.

    Args:
    ----
        context_name: Name of the context to set as current.

    Raises:
    ------
        ValueError: If the context doesn't exist.

    """
    ensure_context_dir()

    # Verify context exists
    context_file = os.path.join(CONTEXT_DIR, f"{context_name}.yaml")
    if not os.path.exists(context_file):
        # Try with .yml extension
        context_file = os.path.join(CONTEXT_DIR, f"{context_name}.yml")
        if not os.path.exists(context_file):
            raise ValueError(f"Context '{context_name}' not found")

    # Write current context
    with open(CURRENT_CONTEXT_FILE, "w") as f:
        f.write(context_name)


def create_context(
    context_name: str,
    client_id: str,
    client_secret: str,
    tsg_id: str,
    log_level: str = "INFO",
) -> None:
    """Create or update a context configuration.

    Args:
    ----
        context_name: Name of the context.
        client_id: SCM client ID.
        client_secret: SCM client secret.
        tsg_id: Tenant Service Group ID.
        log_level: Logging level (default: INFO).

    """
    ensure_context_dir()

    context_file = os.path.join(CONTEXT_DIR, f"{context_name}.yaml")

    config = {
        "client_id": client_id,
        "client_secret": client_secret,
        "tsg_id": tsg_id,
        "log_level": log_level,
    }

    with open(context_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def delete_context(context_name: str) -> None:
    """Delete a context configuration.

    Args:
    ----
        context_name: Name of the context to delete.

    Raises:
    ------
        ValueError: If the context doesn't exist.

    """
    ensure_context_dir()

    # Try both extensions
    context_file = os.path.join(CONTEXT_DIR, f"{context_name}.yaml")
    if not os.path.exists(context_file):
        context_file = os.path.join(CONTEXT_DIR, f"{context_name}.yml")

    if not os.path.exists(context_file):
        raise ValueError(f"Context '{context_name}' not found")

    # If this is the current context, clear it
    if get_current_context() == context_name and os.path.exists(CURRENT_CONTEXT_FILE):
        os.remove(CURRENT_CONTEXT_FILE)

    os.remove(context_file)


def get_context_config(context_name: str | None = None) -> dict[str, Any]:
    """Get configuration for a specific context.

    Args:
    ----
        context_name: Name of the context. If None, uses current context.

    Returns:
    -------
        Context configuration dictionary.

    Raises:
    ------
        ValueError: If the context is not found or no current context is set.

    """
    if context_name is None:
        context_name = get_current_context()
        if not context_name:
            raise ValueError("No current context set. Use 'scm context use <name>' to set one.")

    # Try both extensions
    context_file = os.path.join(CONTEXT_DIR, f"{context_name}.yaml")
    if not os.path.exists(context_file):
        context_file = os.path.join(CONTEXT_DIR, f"{context_name}.yml")

    if not os.path.exists(context_file):
        raise ValueError(f"Context '{context_name}' not found")

    with open(context_file) as f:
        config = yaml.safe_load(f)

    return config or {}


def get_context_aware_settings() -> Dynaconf:
    """Get Dynaconf settings with context awareness.

    Returns settings that prioritize:
    1. Current context configuration (if set via 'scm context use')
    2. Environment variables (for CI/CD automation)
    3. Default settings.yaml

    Note: Legacy config files (~/.scm-cli/config.yaml and .secrets.yaml) are
    no longer supported. Use contexts instead of multi-tenant support.

    Returns
    -------
        Configured Dynaconf instance.

    """
    # Start with only the base settings file
    settings_files = ["settings.yaml"]

    # Add the current context file FIRST so it has the highest priority for file-based config
    current_context = get_current_context()
    if current_context:
        context_file = os.path.join(CONTEXT_DIR, f"{current_context}.yaml")
        if os.path.exists(context_file):
            # Insert at the beginning so context has priority over settings.yaml
            settings_files.insert(0, context_file)
        else:
            # Try .yml extension
            context_file = os.path.join(CONTEXT_DIR, f"{current_context}.yml")
            if os.path.exists(context_file):
                settings_files.insert(0, context_file)

    # Note: We removed .secrets.yaml and ~/.scm-cli/config.yaml
    # Users should migrate to contexts for better multi-tenant support

    return Dynaconf(
        envvar_prefix="SCM",
        settings_files=settings_files,
        load_dotenv=True,
        environments=False,
        merge_enabled=True,
    )
