"""
Mock SDK client for scm-cli.

This module provides a mock implementation of the pan-scm-sdk client for testing
and development purposes. In a production environment, this would be replaced with
actual calls to the pan-scm-sdk.
"""

import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SCMClient:
    """Mock client for the SCM SDK."""

    def __init__(self):
        self.logger = logger
        self.logger.info("Initializing SCM mock client")

    def create_bandwidth_allocation(
        self, folder: str, name: str, bandwidth: int, description: str = "", tags: List[str] = None
    ) -> Dict[str, Any]:
        """Mock for creating a bandwidth allocation."""
        tags = tags or []
        self.logger.info(f"Creating bandwidth allocation: {name} with {bandwidth} Mbps in folder {folder}")
        return {
            "id": f"ba-{name}",
            "folder": folder,
            "name": name,
            "bandwidth": bandwidth,
            "description": description,
            "tags": tags
        }

    def delete_bandwidth_allocation(self, folder: str, name: str) -> bool:
        """Mock for deleting a bandwidth allocation."""
        self.logger.info(f"Deleting bandwidth allocation: {name} from folder {folder}")
        return True

    def create_address_group(
        self, folder: str, name: str, type: str, members: List[str] = None, description: str = "", tags: List[str] = None
    ) -> Dict[str, Any]:
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
            "tags": tags
        }

    def delete_address_group(self, folder: str, name: str) -> bool:
        """Mock for deleting an address group."""
        self.logger.info(f"Deleting address group: {name} from folder {folder}")
        return True

    def create_zone(
        self, folder: str, name: str, mode: str, interfaces: List[str] = None, description: str = "", tags: List[str] = None
    ) -> Dict[str, Any]:
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
            "tags": tags
        }

    def delete_zone(self, folder: str, name: str) -> bool:
        """Mock for deleting a zone."""
        self.logger.info(f"Deleting zone: {name} from folder {folder}")
        return True

    def create_security_rule(
        self, folder: str, name: str, source_zones: List[str], destination_zones: List[str],
        source_addresses: List[str] = None, destination_addresses: List[str] = None,
        applications: List[str] = None, action: str = "allow", description: str = "", tags: List[str] = None
    ) -> Dict[str, Any]:
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
            "tags": tags
        }

    def delete_security_rule(self, folder: str, name: str) -> bool:
        """Mock for deleting a security rule."""
        self.logger.info(f"Deleting security rule: {name} from folder {folder}")
        return True


# Create a singleton instance of the SCM client
scm_client = SCMClient()
