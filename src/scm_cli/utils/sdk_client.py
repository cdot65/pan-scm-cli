"""Lightweight wrapper around the Palo Alto Networks SCM SDK."""

import logging

from scm.client import ScmClient
from .config import SCMConfig

# Use child logger from the root logger
logger = logging.getLogger("scm_cli.utils.sdk_client")


def create_client(config: SCMConfig) -> ScmClient:
    """Create a new ScmClient instance with the provided configuration.

    Args:
        config: SCM configuration with OAuth credentials

    Returns:
        Initialized ScmClient
    """
    logger.debug("Creating new ScmClient with provided configuration")

    client = ScmClient(
        client_id=config.client_id,
        client_secret=config.client_secret,
        tsg_id=config.tsg_id,
        log_level="INFO",
    )

    return client


def test_connection(client: ScmClient) -> bool:
    """Test connection to SCM API.

    Args:
        client: Initialized ScmClient

    Returns:
        True if connection is successful

    Raises:
        Exception: If connection test fails
    """
    logger.debug("Testing connection to SCM API")

    # A simple list operation to verify we have valid credentials
    # The Address manager requires a folder to list objects
    # So we'll try to list addresses in the "All" folder
    client.address.list(folder="All")

    return True
