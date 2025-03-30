"""SDK client integration for pan-scm-cli.

This module provides integration with the pan-scm-sdk client for interacting
with Palo Alto Networks Strata Cloud Manager. It uses the credentials from
dynaconf settings.
"""

import logging
from typing import Any

# Import the actual SDK client
from scm.client import Scm
from scm.exceptions import APIError, AuthenticationError, ClientError, NotFoundError

from .config import get_credentials, settings

# Configure logging
logging_level = getattr(logging, settings.get("log_level", "INFO"))
logging.basicConfig(level=logging_level)
logger = logging.getLogger(__name__)


class SCMClient:
    """Client for the SCM SDK."""

    def __init__(self):
        """Initialize the SCM client with logger and credentials."""
        self.logger = logger
        self.logger.info("Initializing SCM client")
        self.client = None

        try:
            # Get credentials from dynaconf settings
            credentials = get_credentials()
            self.client_id = credentials["client_id"]
            self.client_secret = credentials["client_secret"]
            self.tsg_id = credentials["tsg_id"]

            # Initialize the real SDK client with credentials
            self.client = Scm(
                client_id=self.client_id,
                client_secret=self.client_secret,
                tsg_id=self.tsg_id,
                log_level=settings.get("log_level", "INFO"),
            )
            self.logger.info(f"Successfully initialized SDK client for TSG ID: {self.tsg_id}")
        except (ValueError, AuthenticationError) as e:
            self.logger.warning(f"Failed to initialize SDK client: {str(e)}")
            self.logger.warning("Using mock mode with dummy credentials")
            self.client_id = "mock-client-id"
            self.client_secret = "mock-client-secret"
            self.tsg_id = "mock-tsg-id"
            # In mock mode, methods will return mock data instead of making API calls

    def _handle_api_exception(self, operation: str, folder: str, resource_name: str, exception: Exception) -> None:
        """Handle API exceptions with proper logging and error formatting.

        Args:
        ----
            operation: The operation being performed (create, update, delete, etc.)
            folder: The folder containing the resource
            resource_name: The name of the resource being operated on
            exception: The exception that was raised

        Raises:
        ------
            Exception: Re-raises the original exception after logging

        """
        if isinstance(exception, AuthenticationError):
            self.logger.error(f"Authentication error during {operation} of {resource_name}: {str(exception)}")
        elif isinstance(exception, NotFoundError):
            self.logger.error(f"Resource not found: {resource_name} in folder {folder}")
        elif isinstance(exception, ClientError):
            self.logger.error(f"Validation error during {operation} of {resource_name}: {str(exception)}")
        elif isinstance(exception, APIError):
            self.logger.error(f"API error during {operation} of {resource_name}: {str(exception)}")
        else:
            self.logger.error(f"Unexpected error during {operation} of {resource_name}: {str(exception)}")

        raise exception

    def create_bandwidth_allocation(
        self,
        folder: str,
        name: str,
        bandwidth: int,
        description: str = "",
        tags: list[str] = None,
    ) -> dict[str, Any]:
        """Create a bandwidth allocation.

        Args:
        ----
            folder: Folder to create the bandwidth allocation in
            name: Name of the bandwidth allocation
            bandwidth: Bandwidth in Mbps
            description: Optional description
            tags: Optional list of tags

        Returns:
        -------
            The created bandwidth allocation object

        """
        tags = tags or []
        self.logger.info(f"Creating bandwidth allocation: {name} with {bandwidth} Mbps in folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"ba-{name}",
                "folder": folder,
                "name": name,
                "bandwidth": bandwidth,
                "description": description,
                "tags": tags,
            }

        try:
            # Create using the SDK bandwidth_allocation service (singular, not plural)
            allocation_data = {
                "name": name,
                "folder": folder,  # Include folder in the data object
                "allocated_bandwidth": bandwidth,
                "description": description or "",
            }

            if tags:
                allocation_data["tags"] = tags

            # Updated to match SDK's expected method signature - pass data without folder as a separate param
            result = self.client.bandwidth_allocation.create(allocation_data)

            # Convert SDK response to dict for compatibility
            return result.dict()
        except Exception as e:
            self._handle_api_exception("creation", folder, name, e)

    def delete_bandwidth_allocation(self, folder: str, name: str) -> bool:
        """Delete a bandwidth allocation.

        Args:
        ----
            folder: Folder containing the bandwidth allocation
            name: Name of the bandwidth allocation to delete

        Returns:
        -------
            True if deletion was successful

        """
        self.logger.info(f"Deleting bandwidth allocation: {name} from folder {folder}")

        if not self.client:
            # Return mock result if no client is available
            return True

        try:
            # Delete using the SDK bandwidth_allocation service (singular, not plural)
            # Pass the folder and name as query parameters
            self.client.bandwidth_allocation.delete(folder=folder, name=name)
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder, name, e)

    def create_address_group(
        self,
        folder: str,
        name: str,
        type: str,
        members: list[str] = None,
        description: str = "",
        tags: list[str] = None,
    ) -> dict[str, Any]:
        """Create an address group.

        Args:
        ----
            folder: Folder to create the address group in
            name: Name of the address group
            type: Type of address group ("static" or "dynamic")
            members: List of member addresses for static groups
            description: Optional description
            tags: Optional list of tags

        Returns:
        -------
            The created address group object

        """
        members = members or []
        tags = tags or []
        self.logger.info(f"Creating address group: {name} of type {type} in folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"ag-{name}",
                "folder": folder,
                "name": name,
                "type": type,
                "members": members,
                "description": description,
                "tags": tags,
            }

        try:
            # Create using the SDK address_group service
            group_data = {
                "name": name,
                "folder": folder,  # Include folder in the data object
                "type": type,
                "description": description or "",
            }

            if type.lower() == "static" and members:
                group_data["members"] = members

            if tags:
                group_data["tags"] = tags

            # Updated to match SDK's expected method signature
            result = self.client.address_group.create(group_data)

            # Convert SDK response to dict for compatibility
            return result.dict()
        except Exception as e:
            self._handle_api_exception("creation", folder, name, e)

    def delete_address_group(self, folder: str, name: str) -> bool:
        """Delete an address group.

        Args:
        ----
            folder: Folder containing the address group
            name: Name of the address group to delete

        Returns:
        -------
            True if deletion was successful

        """
        self.logger.info(f"Deleting address group: {name} from folder {folder}")

        if not self.client:
            # Return mock result if no client is available
            return True

        try:
            # Delete using the SDK address_group service
            self.client.address_group.delete(folder=folder, name=name)
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder, name, e)

    def create_zone(
        self,
        folder: str,
        name: str,
        mode: str,
        interfaces: list[str] = None,
        description: str = "",
        tags: list[str] = None,
    ) -> dict[str, Any]:
        """Create a security zone.

        Args:
        ----
            folder: Folder to create the zone in
            name: Name of the zone
            mode: Zone mode (L2, L3, external, virtual-wire, tunnel)
            interfaces: List of interfaces
            description: Optional description
            tags: Optional list of tags

        Returns:
        -------
            The created zone object

        """
        interfaces = interfaces or []
        tags = tags or []
        self.logger.info(f"Creating zone: {name} with mode {mode} in folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"zone-{name}",
                "folder": folder,
                "name": name,
                "mode": mode,
                "interfaces": interfaces,
                "description": description,
                "tags": tags,
            }

        try:
            # Create using the SDK security_zone service
            zone_data = {
                "name": name,
                "folder": folder,  # Include folder in the data object
                "mode": mode,
                "description": description or "",
            }

            if interfaces:
                zone_data["interfaces"] = interfaces

            if tags:
                zone_data["tags"] = tags

            # Updated to match SDK's expected method signature
            result = self.client.security_zone.create(zone_data)

            # Convert SDK response to dict for compatibility
            return result.dict()
        except Exception as e:
            self._handle_api_exception("creation", folder, name, e)

    def delete_zone(self, folder: str, name: str) -> bool:
        """Delete a security zone.

        Args:
        ----
            folder: Folder containing the zone
            name: Name of the zone to delete

        Returns:
        -------
            True if deletion was successful

        """
        self.logger.info(f"Deleting zone: {name} from folder {folder}")

        if not self.client:
            # Return mock result if no client is available
            return True

        try:
            # Delete using the SDK security_zone service
            self.client.security_zone.delete(folder=folder, name=name)
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder, name, e)

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
        enabled: bool = True,
    ) -> dict[str, Any]:
        """Create a security rule.

        Args:
        ----
            folder: Folder to create the rule in
            name: Name of the rule
            source_zones: List of source zones
            destination_zones: List of destination zones
            source_addresses: List of source addresses
            destination_addresses: List of destination addresses
            applications: List of applications
            action: Action (allow, deny, drop)
            description: Optional description
            tags: Optional list of tags
            enabled: Whether the rule is enabled (default True)

        Returns:
        -------
            The created security rule object

        """
        source_addresses = source_addresses or ["any"]
        destination_addresses = destination_addresses or ["any"]
        applications = applications or ["any"]
        tags = tags or []
        self.logger.info(f"Creating security rule: {name} with action {action} in folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"sr-{name}",
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
                "enabled": enabled,
            }

        try:
            # Create using the SDK security_rule service
            rule_data = {
                "name": name,
                "folder": folder,  # Include folder in the data object
                "source_zones": source_zones,
                "destination_zones": destination_zones,
                "source_addresses": source_addresses,
                "destination_addresses": destination_addresses,
                "applications": applications,
                "action": action,
                "description": description or "",
            }

            if tags:
                rule_data["tags"] = tags

            # Updated to match SDK's expected method signature
            result = self.client.security_rule.create(rule_data)

            # Convert SDK response to dict for compatibility
            return result.dict()
        except Exception as e:
            self._handle_api_exception("creation", folder, name, e)

    def delete_security_rule(self, folder: str, name: str) -> bool:
        """Delete a security rule.

        Args:
        ----
            folder: Folder containing the security rule
            name: Name of the security rule to delete

        Returns:
        -------
            True if deletion was successful

        """
        self.logger.info(f"Deleting security rule: {name} from folder {folder}")

        if not self.client:
            # Return mock result if no client is available
            return True

        try:
            # Delete using the SDK security_rule service
            self.client.security_rule.delete(folder=folder, name=name)
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder, name, e)


# Create a singleton instance of the SCM client
scm_client = SCMClient()
