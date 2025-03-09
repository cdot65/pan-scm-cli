"""Lightweight wrapper around the Palo Alto Networks SCM SDK."""

import logging

from scm.client import ScmClient
from .config import SCMConfig

# Configure logging
logger = logging.getLogger("scm_cli.utils.sdk_client")
logger.setLevel(logging.DEBUG)

# Set up console handler if not already configured
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


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
