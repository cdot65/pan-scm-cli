"""Mock SDK client for scm-cli.

This module provides a mock implementation of the pan-scm-sdk client for testing
and development purposes. In a production environment, this would be replaced with
actual calls to the pan-scm-sdk.
"""

import logging
from typing import Any

from .config import get_credentials, settings

# Configure logging
logging_level = getattr(logging, settings.get("log_level", "INFO"))
logging.basicConfig(level=logging_level)
logger = logging.getLogger(__name__)


class SCMClient:
    """Mock client for the SCM SDK."""

    def __init__(self):
        """Initialize the SCM mock client with logger and credentials."""
        self.logger = logger
        self.logger.info("Initializing SCM mock client")

        try:
            # Get credentials from dynaconf settings
            credentials = get_credentials()
            self.client_id = credentials["client_id"]
            self.client_secret = credentials["client_secret"]
            self.tsg_id = credentials["tsg_id"]

            # In a real implementation, these credentials would be used to authenticate
            self.logger.info(f"Successfully loaded credentials for TSG ID: {self.tsg_id}")
        except ValueError as e:
            self.logger.warning(f"Failed to load credentials: {str(e)}")
            self.logger.warning("Using mock mode with dummy credentials")
            self.client_id = "mock-client-id"
            self.client_secret = "mock-client-secret"
            self.tsg_id = "mock-tsg-id"

    def create_bandwidth_allocation(
        self,
        folder: str,
        name: str,
        bandwidth: int,
        description: str = "",
        tags: list[str] = None,
    ) -> dict[str, Any]:
        """Mock for creating a bandwidth allocation."""
        tags = tags or []
        self.logger.info(f"Creating bandwidth allocation: {name} with {bandwidth} Mbps in folder {folder}")
        return {
            "id": f"ba-{name}",
            "folder": folder,
            "name": name,
            "bandwidth": bandwidth,
            "description": description,
            "tags": tags,
        }

    def delete_bandwidth_allocation(self, folder: str, name: str) -> bool:
        """Mock for deleting a bandwidth allocation."""
        self.logger.info(f"Deleting bandwidth allocation: {name} from folder {folder}")
        return True

    def create_address_group(
        self,
        folder: str,
        name: str,
        type: str,
        members: list[str] = None,
        description: str = "",
        tags: list[str] = None,
    ) -> dict[str, Any]:
        """Mock for creating an address group."""
        members = members or []
        tags = tags or []
        self.logger.info(f"Creating address group: {name} of type {type} in folder {folder}")
        return {
            "id": f"ag-{name}",
            "folder": folder,
            "name": name,
            "type": type,
            "members": members,
            "description": description,
            "tags": tags,
        }

    def delete_address_group(self, folder: str, name: str) -> bool:
        """Mock for deleting an address group."""
        self.logger.info(f"Deleting address group: {name} from folder {folder}")
        return True

    def create_zone(
        self,
        folder: str,
        name: str,
        mode: str,
        interfaces: list[str] = None,
        description: str = "",
        tags: list[str] = None,
    ) -> dict[str, Any]:
        """Mock for creating a security zone."""
        interfaces = interfaces or []
        tags = tags or []
        self.logger.info(f"Creating zone: {name} with mode {mode} in folder {folder}")
        return {
            "id": f"zone-{name}",
            "folder": folder,
            "name": name,
            "mode": mode,
            "interfaces": interfaces,
            "description": description,
            "tags": tags,
        }

    def delete_zone(self, folder: str, name: str) -> bool:
        """Mock for deleting a zone."""
        self.logger.info(f"Deleting zone: {name} from folder {folder}")
        return True

    def create_security_rule(
        self,
        folder: str,
        name: str,
        source_zones: list[str],
        destination_zones: list[str],
        source_addresses: list[str] = None,
        destination_addresses: list[str] = None,
        applications: list[str] = None,
        action: str = "allow",
        description: str = "",
        tags: list[str] = None,
    ) -> dict[str, Any]:
        """Mock for creating a security rule."""
        source_addresses = source_addresses or ["any"]
        destination_addresses = destination_addresses or ["any"]
        applications = applications or ["any"]
        tags = tags or []
        self.logger.info(f"Creating security rule: {name} with action {action} in folder {folder}")
        return {
            "id": f"rule-{name}",
            "folder": folder,
            "name": name,
            "source_zones": source_zones,
            "destination_zones": destination_zones,
            "source_addresses": source_addresses,
            "destination_addresses": destination_addresses,
            "applications": applications,
            "action": action,
            "description": description,
            "tags": tags,
        }

    def delete_security_rule(self, folder: str, name: str) -> bool:
        """Mock for deleting a security rule."""
        self.logger.info(f"Deleting security rule: {name} from folder {folder}")
        return True


# Create a singleton instance of the SCM client
scm_client = SCMClient()
