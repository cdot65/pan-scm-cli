"""Client module for Strata Cloud Manager API.

Provides client initialization for SCM API interaction.
"""

import logging
from typing import Any

import scm.client
from scm.exceptions import AuthenticationError

from .utils.config import get_auth_config

logger = logging.getLogger(__name__)


class MockSCMClient:
    """Mock client for testing without API calls."""

    def __init__(self):
        """Initialize the mock client."""
        self._auth_user_credentials = {"mock": True}

    def __getattr__(self, name: str) -> Any:
        """Mock any attribute access with a callable that returns success.

        Args:
        ----
            name: Attribute name being accessed

        Returns:
        -------
            A callable that returns a mock success response

        """

        def mock_callable(*args, **kwargs):
            logger.info(f"Mock SCM API call: {name}(*{args}, **{kwargs})")
            return {"status": "success", "message": f"Mock call to {name}"}

        return MockSCMClient() if name not in ["list", "create", "update", "delete"] else mock_callable


def get_scm_client(mock: bool = False) -> Any:
    """Initialize and return an SCM API client.

    Loads authentication parameters from config and initializes
    either a real or mock SCM client based on the mock parameter.

    Args:
    ----
        mock: If True, returns a mock client without making API calls

    Returns:
    -------
        An initialized SCM client (real or mock)

    Examples:
    --------
        client = get_scm_client()  # Real client
        mock_client = get_scm_client(mock=True)  # Mock client

    """
    if mock:
        logger.info("Creating mock SCM client")
        return MockSCMClient()

    logger.info("Initializing SCM client")
    auth_params = get_auth_config()
    try:
        # Use the Scm client from the pan-scm-sdk (imported as scm.client)
        client = scm.client.Scm(**auth_params)
        logger.info(f"Successfully initialized SDK client for TSG ID: {auth_params['tsg_id']}")
        return client
    except AuthenticationError as e:
        logger.error(f"Authentication error: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Error initializing SCM client: {str(e)}")
        raise e
