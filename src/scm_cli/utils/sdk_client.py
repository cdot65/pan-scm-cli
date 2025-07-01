"""SDK client integration for pan-scm-cli.

This module provides integration with the pan-scm-sdk client for interacting
with Palo Alto Networks Strata Cloud Manager. It uses the credentials from
dynaconf settings.
"""

import contextlib
import json
import logging
from datetime import datetime
from typing import Any, NoReturn

from oauthlib.oauth2.rfc6749.errors import InvalidClientError
from scm.client import Scm
from scm.exceptions import APIError, AuthenticationError, ClientError, NotFoundError

from .config import get_credentials, settings
from .context import get_current_context

# Create logger (will be configured in __init__)
logger = logging.getLogger(__name__)


class SCMClient:
    """Client for the SCM SDK.

    This client provides methods for interacting with Palo Alto Networks
    Strata Cloud Manager API, organized by configuration type:

    SASE Deployment Configuration:
        - Bandwidth Allocation: create, get, list, delete
        - Remote Network: create, get, list, delete
        - Service Connection: create, get, list, delete

    Objects Configuration:
        - Address Groups: create, get, list, delete
        - Address Objects: create, get, list, delete
        - Application Filters: create, get, list, delete
        - Applications: create, get, list, delete
        - Application Groups: create, get, list, delete
        - Dynamic User Groups: create, get, list, delete
        - External Dynamic Lists: create, get, list, delete
        - HIP Objects: create, get, list, delete

    Network Configuration:
        - Security Zones: create, delete

    Security Configuration:
        - Security Rules: create, get, list, delete
        - Anti-Spyware Profiles: create, get, list, delete
    """

    def __init__(self):
        """Initialize the SCM client with logger and credentials."""
        # Configure logging based on settings
        logging_level = getattr(logging, settings.get("log_level", "INFO"))
        logging.basicConfig(level=logging_level, force=True)

        # Suppress SDK auth logging for cleaner output
        logging.getLogger("scm.auth").setLevel(logging.CRITICAL)
        logging.getLogger("oauthlib").setLevel(logging.CRITICAL)

        self.logger = logger
        self.logger.info("Initializing SCM client")
        self.client = None

        # Log the current context if one is set
        current_context = get_current_context()
        if current_context:
            self.logger.info(f"Using authentication context: {current_context}")
        else:
            self.logger.info("No context set, using environment variables or default settings")

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
            # The following mock credentials are used only in mock mode for testing purposes and do not represent real secrets.
            self.client_id = "mock-client-id"
            self.client_secret = "mock-client"  # noqa: S105
            self.tsg_id = "mock-tsg-id"
            # In mock mode, methods will return mock data instead of making API calls
        except (APIError, InvalidClientError) as e:
            # Handle authentication failures gracefully
            error_msg = str(e)
            if "invalid_client" in error_msg or "Client authentication failed" in error_msg:
                import sys

                print(
                    "\n❌ Authentication failed: Invalid client credentials",
                    file=sys.stderr,
                )
                print(
                    f"\nCurrent context: {current_context or 'None set'}",
                    file=sys.stderr,
                )
                print(
                    f"Client ID: {credentials.get('client_id', 'Not set')}",
                    file=sys.stderr,
                )
                print(f"TSG ID: {credentials.get('tsg_id', 'Not set')}", file=sys.stderr)
                print("\nTo fix this issue:", file=sys.stderr)
                print(
                    "  1. Update context: scm context create <name> --client-id <id> --client-secret <secret> --tsg-id <tsg>",
                    file=sys.stderr,
                )
                print("  2. Switch context: scm context use <name>", file=sys.stderr)
                print(
                    "  3. Use environment variables: SCM_CLIENT_ID, SCM_CLIENT_SECRET, SCM_TSG_ID",
                    file=sys.stderr,
                )
                raise SystemExit(1) from e
            else:
                import sys

                print(
                    f"\n❌ Failed to initialize SDK client: {error_msg}",
                    file=sys.stderr,
                )
                raise SystemExit(1) from e

    @property
    def mock(self) -> bool:
        """Check if the client is in mock mode."""
        return self.client is None

    def _extract_impacted_resources(self, impacted_objects: Any) -> list[str]:
        """Extract impacted resources from various formats.

        Args:
            impacted_objects: Can be a list, dict, or string

        Returns:
            List of resource identifiers

        """
        if not impacted_objects:
            return []

        if isinstance(impacted_objects, list):
            return [str(obj) for obj in impacted_objects]

        if isinstance(impacted_objects, dict):
            # Extract meaningful identifiers from the dict
            resources = []
            if "entity" in impacted_objects and impacted_objects["entity"]:
                resources.append(str(impacted_objects["entity"]))
            if "tenant_id" in impacted_objects:
                resources.append(f"tenant:{impacted_objects['tenant_id']}")
            return resources if resources else [str(impacted_objects)]

        return [str(impacted_objects)]

    def _remove_empty_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        """Remove fields with empty values from a dictionary.

        Args:
            data: Dictionary to clean

        Returns:
            Dictionary with empty fields removed

        """
        cleaned = {}
        for key, value in data.items():
            # Skip empty lists, empty dicts, empty strings, and None values
            if value is None:
                continue
            if isinstance(value, (list, dict)) and not value:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            # Recursively clean nested dictionaries
            if isinstance(value, dict):
                cleaned_value = self._remove_empty_fields(value)
                if cleaned_value:  # Only add if the cleaned dict is not empty
                    cleaned[key] = cleaned_value
            else:
                cleaned[key] = value
        return cleaned

    def _handle_api_exception(self, operation: str, folder: str, resource_name: str, exception: Exception) -> NoReturn:
        """Handle API exceptions with proper logging and error formatting.

        Args:
            operation: The operation being performed (create, update, delete, etc.)
            folder: The folder containing the resource
            resource_name: The name of the resource being operated on
            exception: The exception that was raised

        Raises:
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

    # ======================================================================================================================================================================================
    # API METHODS - Quick Navigation:
    # - Objects Configuration: Address Groups, Address Objects
    # - Network Configuration: Security Zones
    # - SASE Deployment Configuration: Bandwidth Allocation
    # - Security Configuration: Security Rules, Anti-Spyware Profiles
    # ======================================================================================================================================================================================

    # ======================================================================================================================================================================================
    # SASE DEPLOYMENT CONFIGURATION METHODS
    # ======================================================================================================================================================================================

    # Bandwidth Allocation -----------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_bandwidth_allocation(
        self,
        name: str,
        bandwidth: int,
        spn_name_list: list[str],
        description: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create or update a bandwidth allocation (smart upsert).

        This method will:
        - Create a new bandwidth allocation if it does not exist
        - Update the allocation if it exists and any field differs
        - Skip update if no changes are detected

        Args:
            name: Name of the bandwidth allocation
            bandwidth: Bandwidth in Mbps
            spn_name_list: List of SPN names to associate with allocation
            description: Optional description
            tags: Optional list of tags

        Returns:
            dict[str, Any]: The created/updated bandwidth allocation object, with '__action__' key: 'created', 'updated', or 'no_change'.

        """
        tags = tags or []
        self.logger.info(f"Upsert bandwidth allocation: {name} ({bandwidth} Mbps) for SPNs: {spn_name_list}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"ba-{name}",
                "name": name,
                "allocated_bandwidth": bandwidth,
                "spn_name_list": spn_name_list,
                "description": description,
                "tags": tags,
                "__action__": "created",
            }

        try:
            # Step 1: Try to fetch the existing bandwidth allocation
            existing = None
            try:
                existing = self.client.bandwidth_allocation.fetch(name=name)
                self.logger.info(f"Found existing bandwidth allocation '{name}'")
            except NotFoundError:
                self.logger.info(f"Bandwidth allocation '{name}' not found, will create new")
            except Exception as e:
                self.logger.warning(f"Error fetching bandwidth allocation '{name}': {str(e)}")

            if existing:
                # Step 2: Compare fields and update if needed
                needs_update = False
                update_fields = []

                # Compare required fields
                if getattr(existing, "allocated_bandwidth", None) != bandwidth:
                    existing.allocated_bandwidth = bandwidth
                    update_fields.append("allocated_bandwidth")
                    needs_update = True

                # Compare SPN name list (order-insensitive)
                current_spns = set(getattr(existing, "spn_name_list", []) or [])
                new_spns = set(spn_name_list or [])
                if current_spns != new_spns:
                    existing.spn_name_list = spn_name_list
                    update_fields.append("spn_name_list")
                    needs_update = True

                # Compare description
                if description is not None and getattr(existing, "description", "") != description:
                    existing.description = description
                    update_fields.append("description")
                    needs_update = True

                # Compare tags (order-insensitive)
                if tags is not None:
                    current_tags = set(getattr(existing, "tags", []) or [])
                    new_tags = set(tags or [])
                    if current_tags != new_tags:
                        existing.tags = tags
                        update_fields.append("tags")
                        needs_update = True

                # Only update if changes detected
                if needs_update:
                    self.logger.info(f"Updating bandwidth allocation fields: {', '.join(update_fields)}")
                    updated = self.client.bandwidth_allocation.update(existing)
                    self.logger.info(f"Successfully updated bandwidth allocation '{name}'")
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
                else:
                    self.logger.info(f"No changes detected for bandwidth allocation '{name}', skipping update")
                    result = json.loads(existing.model_dump_json(exclude_unset=True))
                    result["__action__"] = "no_change"
                    return result
            else:
                # Step 3: Create new bandwidth allocation
                allocation_data = {
                    "name": name,
                    "allocated_bandwidth": bandwidth,
                    "spn_name_list": spn_name_list,
                    "description": description or "",
                }
                if tags:
                    allocation_data["tags"] = tags
                created = self.client.bandwidth_allocation.create(allocation_data)
                self.logger.info(f"Successfully created bandwidth allocation '{name}'")
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
        except Exception as e:
            self._handle_api_exception("creation/update", "N/A", name, e)

    def delete_bandwidth_allocation(
        self,
        name: str,
        spn_name_list: list[str],
    ) -> bool:
        """Delete a bandwidth allocation.

        Args:
            name: Name of the bandwidth allocation to delete
            spn_name_list: List of SPN names associated with the allocation

        Returns:
            bool: True if deletion was successful

        Note:
            Bandwidth allocations are global resources and do not have folder parameters.

        """
        self.logger.info(f"Deleting bandwidth allocation: {name} with SPNs: {spn_name_list}")

        if not self.client:
            # Return a mock result if no client is available
            return True

        try:
            # SDK expects comma-separated string for spn_name_list
            spn_arg = ",".join(spn_name_list) if isinstance(spn_name_list, list) else spn_name_list
            # Delete using the SDK bandwidth_allocation service (singular, not plural)
            self.client.bandwidth_allocation.delete(name=name, spn_name_list=spn_arg)
            return True
        except Exception as e:
            self._handle_api_exception("deletion", "N/A", name, e)

    def get_bandwidth_allocation(
        self,
        name: str,
    ) -> dict[str, Any]:
        """Get a bandwidth allocation by name.

        Args:
            name: Name of the bandwidth allocation to get

        Returns:
            dict[str, Any]: The bandwidth allocation object

        Note:
            Bandwidth allocations do not have a folder parameter

        """
        self.logger.info(f"Getting bandwidth allocation: {name}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"ba-{name}",
                "name": name,
                "allocated_bandwidth": 1000,
                "spn_name_list": ["spn1", "spn2"],
                "description": "Mock bandwidth allocation",
            }

        try:
            # Fetch the bandwidth allocation using the SDK
            result = self.client.bandwidth_allocation.fetch(name=name)

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieval", "N/A", name, e)

    def list_bandwidth_allocations(
        self,
    ) -> list[dict[str, Any]]:
        """List all bandwidth allocations.

        Returns:
            list[dict[str, Any]]: List of bandwidth allocation objects

        Note:
            Bandwidth allocations do not have a folder parameter

        """
        self.logger.info("Listing bandwidth allocations")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "ba-mock1",
                    "name": "mock-allocation-1",
                    "allocated_bandwidth": 1000,
                    "spn_name_list": ["spn1", "spn2"],
                    "description": "Mock bandwidth allocation 1",
                },
                {
                    "id": "ba-mock2",
                    "name": "mock-allocation-2",
                    "allocated_bandwidth": 2000,
                    "spn_name_list": ["spn3"],
                    "description": "Mock bandwidth allocation 2",
                    "qos_enabled": True,
                    "qos_guaranteed_ratio": 50,
                },
            ]

        try:
            # List bandwidth allocations using the SDK
            results = self.client.bandwidth_allocation.list()

            # Convert SDK response to a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", "N/A", "bandwidth allocations", e)

    # ------------------------- Service Connection Methods ------------------------

    def create_service_connection(
        self,
        name: str,
        ipsec_tunnel: str,
        region: str,
        onboarding_type: str = "classic",
        backup_sc: str | None = None,
        nat_pool: str | None = None,
        no_export_community: str | None = None,
        source_nat: bool | None = None,
        subnets: list[str] | None = None,
        secondary_ipsec_tunnel: str | None = None,
        bgp_peer: dict[str, Any] | None = None,
        protocol: dict[str, Any] | None = None,
        qos: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create or update a service connection using smart upsert logic (folder is always 'Service Connections').

        Args:
            name: Name of the service connection
            ipsec_tunnel: IPsec tunnel for the service connection
            region: Region for the service connection
            onboarding_type: Onboarding type (default: "classic")
            backup_sc: Backup service connection
            nat_pool: NAT pool for the service connection
            no_export_community: No export community configuration
            source_nat: Enable source NAT
            subnets: Subnets for the service connection
            secondary_ipsec_tunnel: Secondary IPsec tunnel
            bgp_peer: BGP peer configuration
            protocol: Protocol configuration (BGP)
            qos: QoS configuration

        Returns:
            dict[str, Any]: Created/updated service connection object

        """
        folder = "Service Connections"
        self.logger.info(f"Creating/updating service connection '{name}' in folder: {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"sc-{name}",
                "name": name,
                "folder": folder,
                "ipsec_tunnel": ipsec_tunnel,
                "region": region,
                "onboarding_type": onboarding_type,
                "subnets": subnets or ["10.0.0.0/24"],
                "__action__": "created",
            }

        try:
            # Step 1: Try to fetch the existing service connection
            existing_connection = None
            try:
                existing_connection = self.client.service_connection.fetch(name=name)
                self.logger.info(f"Found existing service connection '{name}'")
            except NotFoundError:
                self.logger.info(f"Service connection '{name}' not found, will create new")
            except Exception as e:
                self.logger.warning(f"Error fetching service connection '{name}': {str(e)}")

            if existing_connection:
                # Step 2: Check what needs updating with field-level change detection
                needs_update = False
                update_fields = []

                # Check required fields
                if existing_connection.ipsec_tunnel != ipsec_tunnel:
                    existing_connection.ipsec_tunnel = ipsec_tunnel
                    update_fields.append("ipsec_tunnel")
                    needs_update = True

                if existing_connection.region != region:
                    existing_connection.region = region
                    update_fields.append("region")
                    needs_update = True

                if existing_connection.onboarding_type != onboarding_type:
                    existing_connection.onboarding_type = onboarding_type
                    update_fields.append("onboarding_type")
                    needs_update = True

                # Check optional fields
                if backup_sc is not None and getattr(existing_connection, "backup_SC", None) != backup_sc:
                    existing_connection.backup_SC = backup_sc
                    update_fields.append("backup_SC")
                    needs_update = True

                if nat_pool is not None and getattr(existing_connection, "nat_pool", None) != nat_pool:
                    existing_connection.nat_pool = nat_pool
                    update_fields.append("nat_pool")
                    needs_update = True

                if no_export_community is not None and getattr(existing_connection, "no_export_community", None) != no_export_community:
                    existing_connection.no_export_community = no_export_community
                    update_fields.append("no_export_community")
                    needs_update = True

                if source_nat is not None and getattr(existing_connection, "source_nat", None) != source_nat:
                    existing_connection.source_nat = source_nat
                    update_fields.append("source_nat")
                    needs_update = True

                if subnets is not None:
                    current_subnets = getattr(existing_connection, "subnets", []) or []
                    if set(current_subnets) != set(subnets):
                        existing_connection.subnets = subnets
                        update_fields.append("subnets")
                        needs_update = True

                if secondary_ipsec_tunnel is not None and getattr(existing_connection, "secondary_ipsec_tunnel", None) != secondary_ipsec_tunnel:
                    existing_connection.secondary_ipsec_tunnel = secondary_ipsec_tunnel
                    update_fields.append("secondary_ipsec_tunnel")
                    needs_update = True

                # Check complex fields (BGP peer, protocol, QoS)
                if bgp_peer is not None:
                    existing_bgp_peer = getattr(existing_connection, "bgp_peer", None)
                    if existing_bgp_peer != bgp_peer:
                        existing_connection.bgp_peer = bgp_peer
                        update_fields.append("bgp_peer")
                        needs_update = True

                if protocol is not None:
                    existing_protocol = getattr(existing_connection, "protocol", None)
                    if existing_protocol != protocol:
                        existing_connection.protocol = protocol
                        update_fields.append("protocol")
                        needs_update = True

                if qos is not None:
                    existing_qos = getattr(existing_connection, "qos", None)
                    if existing_qos != qos:
                        existing_connection.qos = qos
                        update_fields.append("qos")
                        needs_update = True

                # Step 3: Only update if changes detected
                if needs_update:
                    self.logger.info(f"Updating service connection fields: {', '.join(update_fields)}")
                    updated = self.client.service_connection.update(existing_connection)
                    self.logger.info(f"Successfully updated service connection '{name}'")
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
                else:
                    self.logger.info(f"No changes detected for service connection '{name}', skipping update")
                    result = json.loads(existing_connection.model_dump_json(exclude_unset=True))
                    result["__action__"] = "no_change"
                    return result

            else:
                # Step 4: Create new service connection
                data = {
                    "name": name,
                    "folder": folder,
                    "ipsec_tunnel": ipsec_tunnel,
                    "region": region,
                    "onboarding_type": onboarding_type,
                }

                # Add optional fields
                if backup_sc:
                    data["backup_SC"] = backup_sc
                if nat_pool:
                    data["nat_pool"] = nat_pool
                if no_export_community:
                    data["no_export_community"] = no_export_community
                if source_nat is not None:
                    data["source_nat"] = source_nat
                if subnets:
                    data["subnets"] = subnets
                if secondary_ipsec_tunnel:
                    data["secondary_ipsec_tunnel"] = secondary_ipsec_tunnel
                if bgp_peer:
                    data["bgp_peer"] = bgp_peer
                if protocol:
                    data["protocol"] = protocol
                if qos:
                    data["qos"] = qos

                self.logger.info(f"Creating new service connection '{name}' in folder: {folder}")
                created = self.client.service_connection.create(data)
                self.logger.info(f"Successfully created service connection '{name}' in folder: {folder}")
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result

        except Exception as e:
            self._handle_api_exception("creating/updating", name, "service connection", e)

    def delete_service_connection(self, name: str) -> bool:
        """Delete a service connection.

        Args:
            name: Name of the service connection to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting service connection '{name}'")

        if not self.client:
            self.logger.info(f"Mock mode: Would delete service connection '{name}'")
            return True

        try:
            # First, fetch the service connection to get its ID
            service_connection = self.client.service_connection.fetch(name=name)
            self.client.service_connection.delete(str(service_connection.id))
            self.logger.info(f"Successfully deleted service connection '{name}'")
            return True
        except Exception as e:
            self._handle_api_exception("deleting", name, "service connection", e)

    def get_service_connection(self, name: str) -> dict[str, Any]:
        """Get a specific service connection by name.

        Args:
            name: Name of the service connection

        Returns:
            dict[str, Any]: Service connection object

        """
        self.logger.info(f"Getting service connection '{name}'")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"sc-{name}",
                "name": name,
                "folder": "Service Connections",
                "ipsec_tunnel": "ipsec-tunnel-1",
                "region": "us-east-1",
                "onboarding_type": "classic",
                "subnets": ["10.0.0.0/24"],
            }

        try:
            # Fetch the service connection by name
            result = self.client.service_connection.fetch(name=name)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("fetching", name, "service connection", e)

    def list_service_connections(self) -> list[dict[str, Any]]:
        """List all service connections.

        Returns:
            list[dict[str, Any]]: List of service connections

        """
        self.logger.info("Listing service connections")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "sc-1",
                    "name": "Primary Service Connection",
                    "folder": "Service Connections",
                    "ipsec_tunnel": "ipsec-tunnel-1",
                    "region": "us-east-1",
                    "onboarding_type": "classic",
                    "subnets": ["10.0.0.0/24"],
                },
                {
                    "id": "sc-2",
                    "name": "Backup Service Connection",
                    "folder": "Service Connections",
                    "ipsec_tunnel": "ipsec-tunnel-2",
                    "region": "us-west-2",
                    "onboarding_type": "classic",
                    "subnets": ["10.1.0.0/24"],
                },
            ]

        try:
            # List service connections using the SDK
            results = self.client.service_connection.list()
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", "", "service connections", e)

    # ------------------------- Remote Network Methods -------------------------

    def create_remote_network(
        self,
        name: str,
        region: str,
        license_type: str = "FWAAS-AGGREGATE",
        description: str | None = None,
        subnets: list[str] | None = None,
        spn_name: str | None = None,
        ecmp_load_balancing: str = "disable",
        ecmp_tunnels: list[dict[str, Any]] | None = None,
        ipsec_tunnel: str | None = None,
        secondary_ipsec_tunnel: str | None = None,
        protocol: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create or update a remote network using smart upsert logic (folder is always 'Remote Networks').

        Args:
            name: Name of the remote network
            region: Region for the remote network
            license_type: License type (default: "FWAAS-AGGREGATE")
            description: Description of the remote network
            subnets: Subnets for the remote network
            spn_name: SPN name (needed when license_type is FWAAS-AGGREGATE)
            ecmp_load_balancing: Enable or disable ECMP load balancing
            ecmp_tunnels: ECMP tunnel configurations
            ipsec_tunnel: IPsec tunnel (required when ecmp_load_balancing is disable)
            secondary_ipsec_tunnel: Secondary IPsec tunnel
            protocol: Protocol configuration (BGP)

        Returns:
            dict[str, Any]: Created/updated remote network object

        """
        folder = "Remote Networks"
        self.logger.info(f"Creating/updating remote network '{name}' in folder: {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"rn-{name}",
                "name": name,
                "folder": folder,
                "region": region,
                "license_type": license_type,
                "spn_name": spn_name or "default-spn",
                "ecmp_load_balancing": ecmp_load_balancing,
                "ipsec_tunnel": ipsec_tunnel or "ipsec-tunnel-1",
                "subnets": subnets or ["192.168.0.0/24"],
                "__action__": "created",
            }

        try:
            # Step 1: Try to fetch the existing remote network
            existing_network = None
            try:
                existing_network = self.client.remote_network.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing remote network '{name}' in folder '{folder}'")
            except NotFoundError:
                self.logger.info(f"Remote network '{name}' not found in folder '{folder}', will create new")
            except Exception as e:
                self.logger.warning(f"Error fetching remote network '{name}': {str(e)}")

            if existing_network:
                # Step 2: Check what needs updating with field-level change detection
                needs_update = False
                update_fields = []

                # Check required fields
                if existing_network.region != region:
                    existing_network.region = region
                    update_fields.append("region")
                    needs_update = True

                if existing_network.license_type != license_type:
                    existing_network.license_type = license_type
                    update_fields.append("license_type")
                    needs_update = True

                if existing_network.ecmp_load_balancing != ecmp_load_balancing:
                    existing_network.ecmp_load_balancing = ecmp_load_balancing
                    update_fields.append("ecmp_load_balancing")
                    needs_update = True

                # Check optional fields
                if description is not None:
                    current_desc = getattr(existing_network, "description", "")
                    if current_desc != description:
                        existing_network.description = description
                        update_fields.append("description")
                        needs_update = True

                if subnets is not None:
                    current_subnets = getattr(existing_network, "subnets", []) or []
                    if set(current_subnets) != set(subnets):
                        existing_network.subnets = subnets
                        update_fields.append("subnets")
                        needs_update = True

                if spn_name is not None and getattr(existing_network, "spn_name", None) != spn_name:
                    existing_network.spn_name = spn_name
                    update_fields.append("spn_name")
                    needs_update = True

                if ecmp_tunnels is not None:
                    current_ecmp_tunnels = getattr(existing_network, "ecmp_tunnels", []) or []
                    if current_ecmp_tunnels != ecmp_tunnels:
                        existing_network.ecmp_tunnels = ecmp_tunnels
                        update_fields.append("ecmp_tunnels")
                        needs_update = True

                if ipsec_tunnel is not None and getattr(existing_network, "ipsec_tunnel", None) != ipsec_tunnel:
                    existing_network.ipsec_tunnel = ipsec_tunnel
                    update_fields.append("ipsec_tunnel")
                    needs_update = True

                if secondary_ipsec_tunnel is not None and getattr(existing_network, "secondary_ipsec_tunnel", None) != secondary_ipsec_tunnel:
                    existing_network.secondary_ipsec_tunnel = secondary_ipsec_tunnel
                    update_fields.append("secondary_ipsec_tunnel")
                    needs_update = True

                # Check protocol configuration
                if protocol is not None:
                    existing_protocol = getattr(existing_network, "protocol", None)
                    if existing_protocol != protocol:
                        existing_network.protocol = protocol
                        update_fields.append("protocol")
                        needs_update = True

                # Step 3: Only update if changes detected
                if needs_update:
                    self.logger.info(f"Updating remote network fields: {', '.join(update_fields)}")
                    updated = self.client.remote_network.update(existing_network)
                    self.logger.info(f"Successfully updated remote network '{name}' in folder '{folder}'")
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
                else:
                    self.logger.info(f"No changes detected for remote network '{name}', skipping update")
                    result = json.loads(existing_network.model_dump_json(exclude_unset=True))
                    result["__action__"] = "no_change"
                    return result

            else:
                # Step 4: Create new remote network
                data = {
                    "name": name,
                    "folder": folder,
                    "region": region,
                    "license_type": license_type,
                    "ecmp_load_balancing": ecmp_load_balancing,
                }

                # Add optional fields
                if description:
                    data["description"] = description
                if subnets:
                    data["subnets"] = subnets
                if spn_name:
                    data["spn_name"] = spn_name
                if ecmp_tunnels:
                    data["ecmp_tunnels"] = ecmp_tunnels
                if ipsec_tunnel:
                    data["ipsec_tunnel"] = ipsec_tunnel
                if secondary_ipsec_tunnel:
                    data["secondary_ipsec_tunnel"] = secondary_ipsec_tunnel
                if protocol:
                    data["protocol"] = protocol

                self.logger.info(f"Creating new remote network '{name}' in folder '{folder}'")
                created = self.client.remote_network.create(data)
                self.logger.info(f"Successfully created remote network '{name}' in folder '{folder}'")
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result

        except Exception as e:
            self._handle_api_exception("creating/updating", name, "remote network", e)

    def delete_remote_network(self, folder: str, name: str) -> bool:
        """Delete a remote network.

        Args:
            folder: Folder containing the remote network
            name: Name of the remote network to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting remote network '{name}' from folder: {folder}")

        if not self.client:
            self.logger.info(f"Mock mode: Would delete remote network '{name}'")
            return True

        try:
            # First, fetch the remote network to get its ID
            remote_network = self.client.remote_network.fetch(name=name, folder=folder)
            self.client.remote_network.delete(str(remote_network.id))
            self.logger.info(f"Successfully deleted remote network '{name}'")
            return True
        except Exception as e:
            self._handle_api_exception("deleting", name, "remote network", e)

    def get_remote_network(self, name: str) -> dict[str, Any]:
        """Get a specific remote network by name (folder is always 'Remote Networks').

        Args:
            name: Name of the remote network

        Returns:
            dict[str, Any]: Remote network object

        """
        folder = "Remote Networks"
        self.logger.info(f"Getting remote network '{name}' from folder: {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"rn-{name}",
                "name": name,
                "folder": folder,
                "region": "us-east-1",
                "license_type": "FWAAS-AGGREGATE",
                "spn_name": "default-spn",
                "ecmp_load_balancing": "disable",
                "ipsec_tunnel": "ipsec-tunnel-1",
                "subnets": ["192.168.0.0/24"],
            }

        try:
            # Fetch the remote network by name and folder
            result = self.client.remote_network.fetch(name=name, folder=folder)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("fetching", name, "remote network", e)

    def list_remote_networks(self) -> list[dict[str, Any]]:
        """List all remote networks (folder is always 'Remote Networks').

        Returns:
            list[dict[str, Any]]: List of remote networks

        """
        folder = "Remote Networks"
        self.logger.info(f"Listing remote networks in folder: {folder}")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "rn-1",
                    "name": "Branch Office 1",
                    "folder": folder,
                    "region": "us-east-1",
                    "license_type": "FWAAS-AGGREGATE",
                    "spn_name": "default-spn",
                    "ecmp_load_balancing": "disable",
                    "ipsec_tunnel": "ipsec-tunnel-1",
                    "subnets": ["192.168.0.0/24"],
                },
                {
                    "id": "rn-2",
                    "name": "Branch Office 2",
                    "folder": folder,
                    "region": "us-west-2",
                    "license_type": "FWAAS-AGGREGATE",
                    "spn_name": "default-spn",
                    "ecmp_load_balancing": "disable",
                    "ipsec_tunnel": "ipsec-tunnel-2",
                    "subnets": ["192.168.1.0/24"],
                },
            ]

        try:
            # List remote networks using the SDK
            results = self.client.remote_network.list(folder=folder)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder, "remote networks", e)

    # ======================================================================================================================================================================================
    # OBJECTS CONFIGURATION METHODS
    # ======================================================================================================================================================================================

    # Address Objects ----------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_address(
        self,
        folder: str,
        name: str,
        description: str = "",
        tags: list[str] | None = None,
        ip_netmask: str | None = None,
        ip_range: str | None = None,
        ip_wildcard: str | None = None,
        fqdn: str | None = None,
    ) -> dict[str, Any]:
        """Create an address object.

        Args:
            folder: Folder to create the address in
            name: Name of the address
            description: Optional description
            tags: Optional list of tags
            ip_netmask: IP address with CIDR notation (e.g. "192.168.1.0/24")
            ip_range: IP address range (e.g. "192.168.1.1-192.168.1.10")
            ip_wildcard: IP wildcard mask (e.g. "10.20.1.0/0.0.248.255")
            fqdn: Fully qualified domain name (e.g. "example.com")

        Returns:
            dict[str, Any]: The created address object

        Note:
            Exactly one of ip_netmask, ip_range, ip_wildcard, or fqdn must be provided.
            If an address with the same name already exists in the folder, it will be updated.

        """
        tags = tags or []
        self.logger.info(f"Creating or updating address: {name} in folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"addr-{name}",
                "folder": folder,
                "name": name,
                "description": description,
                "tags": tags,
                "ip_netmask": ip_netmask,
                "ip_range": ip_range,
                "ip_wildcard": ip_wildcard,
                "fqdn": fqdn,
            }

        try:
            # First, try to fetch the existing address
            existing_address = None
            try:
                existing_address = self.client.address.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing address '{name}' in folder '{folder}', updating...")
            except NotFoundError:
                self.logger.info(f"Address '{name}' not found in folder '{folder}', creating new...")
            except Exception as fetch_error:
                # Log but continue - we'll try to create if fetch failed for other reasons
                self.logger.warning(f"Error fetching address '{name}': {str(fetch_error)}")

            # Prepare address data
            address_data = {
                "name": name,
                "folder": folder,
            }

            # Only include description if it's provided and not empty
            if description:
                address_data["description"] = description

            # Add exactly one address type
            if ip_netmask:
                address_data["ip_netmask"] = ip_netmask
            elif ip_range:
                address_data["ip_range"] = ip_range
            elif ip_wildcard:
                address_data["ip_wildcard"] = ip_wildcard
            elif fqdn:
                address_data["fqdn"] = fqdn

            if tags:
                address_data["tag"] = tags  # SDK expects 'tag', not 'tags'

            # If an address exists, update it
            if existing_address:
                # Check if an address type is changing
                current_type = None
                new_type = None

                # Determine the current address type
                if hasattr(existing_address, "ip_netmask") and existing_address.ip_netmask:
                    current_type = "ip_netmask"
                elif hasattr(existing_address, "ip_range") and existing_address.ip_range:
                    current_type = "ip_range"
                elif hasattr(existing_address, "ip_wildcard") and existing_address.ip_wildcard:
                    current_type = "ip_wildcard"
                elif hasattr(existing_address, "fqdn") and existing_address.fqdn:
                    current_type = "fqdn"

                # Determine a new address type
                if ip_netmask:
                    new_type = "ip_netmask"
                elif ip_range:
                    new_type = "ip_range"
                elif ip_wildcard:
                    new_type = "ip_wildcard"
                elif fqdn:
                    new_type = "fqdn"

                # If the address type is changing, update the object in place
                if current_type and new_type and current_type != new_type:
                    self.logger.info(f"Address type changing from {current_type} to {new_type}, updating in place...")
                    # Clear old type-specific fields
                    if current_type == "ip_netmask":
                        existing_address.ip_netmask = None
                    elif current_type == "ip_range":
                        existing_address.ip_range = None
                    elif current_type == "ip_wildcard":
                        existing_address.ip_wildcard = None
                    elif current_type == "fqdn":
                        existing_address.fqdn = None

                    # Set new type-specific field
                    if new_type == "ip_netmask":
                        existing_address.ip_netmask = ip_netmask
                    elif new_type == "ip_range":
                        existing_address.ip_range = ip_range
                    elif new_type == "ip_wildcard":
                        existing_address.ip_wildcard = ip_wildcard
                    elif new_type == "fqdn":
                        existing_address.fqdn = fqdn

                    # Update description if provided
                    if description is not None:
                        existing_address.description = description
                    # Update tags if provided
                    if tags is not None:
                        existing_address.tag = tags

                    self.logger.info(f"Updating address '{name}' to new type '{new_type}' and values")
                    result = self.client.address.update(existing_address)
                    self.logger.info(f"Successfully updated address '{name}' with new type")
                    response = json.loads(result.model_dump_json(exclude_unset=True))
                    response["__action__"] = "updated"
                    return response
                else:
                    # Check what needs updating
                    needs_update = False
                    update_fields = []

                    # Compare description
                    current_desc = getattr(existing_address, "description", "")
                    if description is not None and current_desc != description:
                        existing_address.description = description
                        update_fields.append("description")
                        needs_update = True

                    # Compare tags
                    if tags is not None:
                        current_tags = getattr(existing_address, "tag", []) or []
                        if set(current_tags) != set(tags):
                            existing_address.tag = tags
                            update_fields.append("tags")
                            needs_update = True

                    # Compare address value if provided and same type
                    if ip_netmask and current_type == "ip_netmask":
                        if existing_address.ip_netmask != ip_netmask:
                            existing_address.ip_netmask = ip_netmask
                            update_fields.append("ip_netmask")
                            needs_update = True
                    elif ip_range and current_type == "ip_range":
                        if existing_address.ip_range != ip_range:
                            existing_address.ip_range = ip_range
                            update_fields.append("ip_range")
                            needs_update = True
                    elif ip_wildcard and current_type == "ip_wildcard":
                        if existing_address.ip_wildcard != ip_wildcard:
                            existing_address.ip_wildcard = ip_wildcard
                            update_fields.append("ip_wildcard")
                            needs_update = True
                    elif fqdn and current_type == "fqdn" and existing_address.fqdn != fqdn:
                        existing_address.fqdn = fqdn
                        update_fields.append("fqdn")
                        needs_update = True

                    # Only update if changes detected
                    if needs_update:
                        self.logger.info(f"Updating address fields: {', '.join(update_fields)}")
                        result = self.client.address.update(existing_address)
                        self.logger.info(f"Successfully updated address '{name}'")
                        response = json.loads(result.model_dump_json(exclude_unset=True))
                        response["__action__"] = "updated"
                        return response
                    else:
                        self.logger.info(f"No changes detected for address '{name}', skipping update")
                        response = json.loads(existing_address.model_dump_json(exclude_unset=True))
                        response["__action__"] = "no_change"
                        return response
            else:
                # Create a new address
                result = self.client.address.create(address_data)
                self.logger.info(f"Successfully created address '{name}'")
                response = json.loads(result.model_dump_json(exclude_unset=True))
                response["__action__"] = "created"
                return response
        except Exception as e:
            self._handle_api_exception("creation/update", folder, name, e)

    def delete_address(
        self,
        folder: str,
        name: str,
    ) -> bool:
        """Delete an address object.

        Args:
            folder: Folder containing the address
            name: Name of the address to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting address: {name} from folder {folder}")

        if not self.client:
            # Return a mock result if no client is available
            return True

        try:
            # Get the address first to retrieve its ID
            address = self.client.address.fetch(name=name, folder=folder)

            # Delete using the address's ID
            self.client.address.delete(object_id=str(address.id))
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder, name, e)

    def get_address(
        self,
        folder: str,
        name: str,
    ) -> dict[str, Any]:
        """Get an address object by name and folder.

        Args:
            folder: Folder containing the address
            name: Name of the address to get

        Returns:
            dict[str, Any]: The address object

        """
        self.logger.info(f"Getting address: {name} from folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"addr-{name}",
                "folder": folder,
                "name": name,
                "description": "Mock address object",
                "tags": [],
                "ip_netmask": "192.168.1.0/24",
            }

        try:
            # Fetch the address using the SDK
            result = self.client.address.fetch(name=name, folder=folder)

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieval", folder, name, e)

    def list_addresses(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List address objects in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return objects defined exactly in the specified container

        Returns:
            list[dict[str, Any]]: List of address objects

        """
        container = folder or snippet or device or "ngfw-shared"
        self.logger.info(f"Listing addresses in {folder=}, {snippet=}, {device=} (exact_match={exact_match})")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "addr-mock1",
                    "folder": folder or "ngfw-shared",
                    "name": "mock-address-1",
                    "description": "Mock address 1",
                    "tags": ["mock"],
                    "ip_netmask": "192.168.1.0/24",
                },
                {
                    "id": "addr-mock2",
                    "folder": folder or "ngfw-shared",
                    "name": "mock-address-2",
                    "description": "Mock address 2",
                    "tags": ["mock"],
                    "fqdn": "example.com",
                },
            ]

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            # List addresses using the SDK
            results = self.client.address.list(exact_match=exact_match, **container_kwargs)

            # Convert SDK response to a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container, "addresses", e)

    # Address Groups -----------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_address_group(
        self,
        folder: str,
        name: str,
        type: str,
        members: list[str] | None = None,
        filter: str | None = None,
        description: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create an address group.

        Args:
            folder: Folder to create the address group in
            name: Name of the address group
            type: Type of address group ("static" or "dynamic")
            members: List of member addresses (for static groups)
            filter: Filter expression (for dynamic groups)
            description: Optional description
            tags: Optional list of tags

        Returns:
            dict[str, Any]: The created address group object

        Note:
            If an address group with the same name already exists in the folder, it will be updated.
            For dynamic groups, the first member is treated as the filter expression.

        """
        members = members or []
        tags = tags or []
        self.logger.info(f"Creating or updating address group: {name} of type {type} in folder {folder}")

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
            # First, try to fetch the existing address group
            existing_group = None
            try:
                existing_group = self.client.address_group.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing address group '{name}' in folder '{folder}', updating...")
            except NotFoundError:
                self.logger.info(f"Address group '{name}' not found in folder '{folder}', creating new...")
            except Exception as fetch_error:
                # Log but continue - we'll try to create if fetch failed for other reasons
                self.logger.warning(f"Error fetching address group '{name}': {str(fetch_error)}")

            # Prepare address group data
            group_data = {
                "name": name,
                "folder": folder,
                "description": description or "",
            }

            # SDK expects either 'static' or 'dynamic' key, not 'type'
            if type.lower() == "static":
                group_data["static"] = members or []
            elif type.lower() == "dynamic":
                # For dynamic groups, use the filter parameter
                if filter:
                    group_data["dynamic"] = {"filter": filter}
                elif members and len(members) > 0:
                    # Backward compatibility: treat first member as filter
                    group_data["dynamic"] = {"filter": members[0]}
                else:
                    raise ValueError("Dynamic address groups require a filter expression")

            if tags:
                group_data["tag"] = tags  # SDK expects 'tag', not 'tags'

            # If an address group exists, update it
            if existing_group:
                # Check if a group type is changing
                current_type = None
                new_type = type.lower()

                # Determine the current group type
                if hasattr(existing_group, "static") and existing_group.static is not None:
                    current_type = "static"
                elif hasattr(existing_group, "dynamic") and existing_group.dynamic is not None:
                    current_type = "dynamic"

                # If the group type is changing, we need to delete and recreate
                if current_type and new_type and current_type != new_type:
                    self.logger.info(f"Address group type changing from {current_type} to {new_type}, deleting and recreating...")
                    # Delete the existing group
                    self.client.address_group.delete(object_id=str(existing_group.id))
                    # Create a new group with a new type
                    result = self.client.address_group.create(group_data)
                    self.logger.info(f"Successfully recreated address group '{name}' with new type")
                else:
                    # Update only the fields that are changing
                    existing_group.description = description or ""
                    if tags is not None:  # Only update tags if explicitly provided
                        existing_group.tag = tags

                    # Update the members/filter if provided and same type
                    if new_type == "static" and current_type == "static":
                        existing_group.static = members or []
                    elif new_type == "dynamic" and current_type == "dynamic":
                        if filter:
                            existing_group.dynamic = {"filter": filter}
                        elif members and len(members) > 0:
                            # Backward compatibility: treat first member as filter
                            existing_group.dynamic = {"filter": members[0]}

                    # Perform update
                    result = self.client.address_group.update(existing_group)
                    self.logger.info(f"Successfully updated address group '{name}'")
            else:
                # Create a new address group
                result = self.client.address_group.create(group_data)
                self.logger.info(f"Successfully created address group '{name}'")

            # Convert SDK response to dict for compatibility
            return result.dict()
        except Exception as e:
            self._handle_api_exception("creation/update", folder, name, e)

    def delete_address_group(
        self,
        folder: str,
        name: str,
    ) -> bool:
        """Delete an address group.

        Args:
            folder: Folder containing the address group
            name: Name of the address group to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting address group: {name} from folder {folder}")

        if not self.client:
            # Return a mock result if no client is available
            return True

        try:
            # Get the address group first to retrieve its ID
            address_group = self.client.address_group.fetch(name=name, folder=folder)

            # Delete using the address group's ID
            self.client.address_group.delete(object_id=str(address_group.id))
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder, name, e)

    def get_address_group(
        self,
        folder: str,
        name: str,
    ) -> dict[str, Any]:
        """Get an address group by name and folder.

        Args:
            folder: Folder containing the address group
            name: Name of the address group to get

        Returns:
            dict[str, Any]: The address group object

        """
        self.logger.info(f"Getting address group: {name} from folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"ag-{name}",
                "folder": folder,
                "name": name,
                "description": "Mock address group",
                "type": "static",
                "members": ["192.168.1.0/24", "10.0.0.0/8"],
                "tags": ["mock"],
            }

        try:
            # Fetch the address group using the SDK
            result = self.client.address_group.fetch(name=name, folder=folder)

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieval", folder, name, e)

    def list_address_groups(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List address groups in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return objects defined exactly in the specified container

        Returns:
            list[dict[str, Any]]: List of address group objects

        """
        container = folder or snippet or device or "ngfw-shared"
        self.logger.info(f"Listing address groups in {folder=}, {snippet=}, {device=} (exact_match={exact_match})")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "ag-mock1",
                    "folder": folder or "ngfw-shared",
                    "name": "mock-group-1",
                    "description": "Mock address group 1",
                    "type": "static",
                    "members": ["192.168.1.0/24", "10.0.0.0/8"],
                    "tags": ["mock"],
                },
                {
                    "id": "ag-mock2",
                    "folder": folder or "ngfw-shared",
                    "name": "mock-group-2",
                    "description": "Mock address group 2",
                    "type": "dynamic",
                    "filter": "'tag1' and 'tag2'",
                    "tags": ["mock", "dynamic"],
                },
            ]

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            # List address groups using the SDK
            results = self.client.address_group.list(exact_match=exact_match, **container_kwargs)

            # Convert SDK response to a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container, "address groups", e)

    # Applications -------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_application(
        self,
        folder: str,
        name: str,
        category: str,
        subcategory: str,
        technology: str,
        risk: int,
        description: str = "",
        ports: list[str] | None = None,
        evasive: bool = False,
        pervasive: bool = False,
        excessive_bandwidth_use: bool = False,
        used_by_malware: bool = False,
        transfers_files: bool = False,
        has_known_vulnerabilities: bool = False,
        tunnels_other_apps: bool = False,
        prone_to_misuse: bool = False,
        no_certifications: bool = False,
    ) -> dict[str, Any]:
        """Create an application.

        Args:
            folder: Folder to create the application in
            name: Name of the application
            category: High-level category
            subcategory: Specific subcategory
            technology: Underlying technology
            risk: Risk level (1-5)
            description: Optional description
            ports: Optional list of TCP/UDP ports
            evasive: Uses evasive techniques
            pervasive: Widely used
            excessive_bandwidth_use: Uses excessive bandwidth
            used_by_malware: Used by malware
            transfers_files: Transfers files
            has_known_vulnerabilities: Has known vulnerabilities
            tunnels_other_apps: Tunnels other applications
            prone_to_misuse: Prone to misuse
            no_certifications: Lacks certifications

        Returns:
            dict[str, Any]: The created application object

        Note:
            If an application with the same name already exists in the folder, it will be updated.

        """
        ports = ports or []
        self.logger.info(f"Creating or updating application: {name} in folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"app-{name}",
                "folder": folder,
                "name": name,
                "category": category,
                "subcategory": subcategory,
                "technology": technology,
                "risk": risk,
                "description": description,
                "ports": ports,
            }

        try:
            # First, try to fetch the existing application
            existing_app = None
            try:
                existing_app = self.client.application.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing application '{name}' in folder '{folder}', updating...")
            except NotFoundError:
                self.logger.info(f"Application '{name}' not found in folder '{folder}', creating new...")
            except Exception as fetch_error:
                # Log but continue - we'll try to create if fetch failed for other reasons
                self.logger.warning(f"Error fetching application '{name}': {str(fetch_error)}")

            # Prepare application data
            app_data = {
                "name": name,
                "folder": folder,
                "category": category,
                "subcategory": subcategory,
                "technology": technology,
                "risk": risk,
                "description": description or "",
            }

            # Add optional fields only if they have non-default values
            if ports:
                app_data["ports"] = ports
            if evasive:
                app_data["evasive"] = evasive
            if pervasive:
                app_data["pervasive"] = pervasive
            if excessive_bandwidth_use:
                app_data["excessive_bandwidth_use"] = excessive_bandwidth_use
            if used_by_malware:
                app_data["used_by_malware"] = used_by_malware
            if transfers_files:
                app_data["transfers_files"] = transfers_files
            if has_known_vulnerabilities:
                app_data["has_known_vulnerabilities"] = has_known_vulnerabilities
            if tunnels_other_apps:
                app_data["tunnels_other_apps"] = tunnels_other_apps
            if prone_to_misuse:
                app_data["prone_to_misuse"] = prone_to_misuse
            if no_certifications:
                app_data["no_certifications"] = no_certifications

            # If an existing application exists, update it
            if existing_app:
                # Update all fields
                existing_app.category = category
                existing_app.subcategory = subcategory
                existing_app.technology = technology
                existing_app.risk = risk
                existing_app.description = description or ""

                # Update optional fields
                if ports is not None:
                    existing_app.ports = ports
                existing_app.evasive = evasive
                existing_app.pervasive = pervasive
                existing_app.excessive_bandwidth_use = excessive_bandwidth_use
                existing_app.used_by_malware = used_by_malware
                existing_app.transfers_files = transfers_files
                existing_app.has_known_vulnerabilities = has_known_vulnerabilities
                existing_app.tunnels_other_apps = tunnels_other_apps
                existing_app.prone_to_misuse = prone_to_misuse
                existing_app.no_certifications = no_certifications

                # Perform update
                result = self.client.application.update(existing_app)
                self.logger.info(f"Successfully updated application '{name}'")
            else:
                # Create a new application
                result = self.client.application.create(app_data)
                self.logger.info(f"Successfully created application '{name}'")

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("creation/update", folder, name, e)

    def delete_application(
        self,
        folder: str,
        name: str,
    ) -> bool:
        """Delete an application.

        Args:
            folder: Folder containing the application
            name: Name of the application to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting application: {name} from folder {folder}")

        if not self.client:
            # Return a mock result if no client is available
            return True

        try:
            # Get the application first to retrieve its ID
            app = self.client.application.fetch(name=name, folder=folder)

            # Delete using the application's ID
            self.client.application.delete(object_id=str(app.id))
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder, name, e)

    def get_application(
        self,
        folder: str,
        name: str,
    ) -> dict[str, Any]:
        """Get an application by name and folder.

        Args:
            folder: Folder containing the application
            name: Name of the application to get

        Returns:
            dict[str, Any]: The application object

        """
        self.logger.info(f"Getting application: {name} from folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"app-{name}",
                "folder": folder,
                "name": name,
                "category": "business-systems",
                "subcategory": "database",
                "technology": "client-server",
                "risk": 3,
                "description": "Mock application",
                "ports": ["tcp/1521"],
            }

        try:
            # Fetch the application using the SDK
            result = self.client.application.fetch(name=name, folder=folder)

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieval", folder, name, e)

    def list_applications(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List applications in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return objects defined exactly in the specified container

        Returns:
            list[dict[str, Any]]: List of application objects

        """
        container = folder or snippet or device or "ngfw-shared"
        self.logger.info(f"Listing applications in {folder=}, {snippet=}, {device=} (exact_match={exact_match})")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "app-mock1",
                    "folder": folder or "ngfw-shared",
                    "name": "mock-app-1",
                    "category": "business-systems",
                    "subcategory": "database",
                    "technology": "client-server",
                    "risk": 3,
                    "description": "Mock application 1",
                    "ports": ["tcp/1521"],
                },
                {
                    "id": "app-mock2",
                    "folder": folder or "ngfw-shared",
                    "name": "mock-app-2",
                    "category": "collaboration",
                    "subcategory": "instant-messaging",
                    "technology": "browser-based",
                    "risk": 2,
                    "description": "Mock application 2",
                    "ports": ["tcp/443"],
                },
            ]

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            # List applications using the SDK
            results = self.client.application.list(exact_match=exact_match, **container_kwargs)

            # Convert SDK response to a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container, "applications", e)

    # Application Groups -------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_application_group(
        self,
        folder: str,
        name: str,
        members: list[str],
    ) -> dict[str, Any]:
        """Create an application group.

        Args:
            folder: Folder to create the application group in
            name: Name of the application group
            members: List of application names

        Returns:
            dict[str, Any]: The created application group object

        Note:
            If an application group with the same name already exists in the folder, it will be updated.

        """
        self.logger.info(f"Creating or updating application group: {name} in folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"app-group-{name}",
                "folder": folder,
                "name": name,
                "members": members,
            }

        try:
            # First, try to fetch the existing application group
            existing_group = None
            try:
                existing_group = self.client.application_group.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing application group '{name}' in folder '{folder}', updating...")
            except NotFoundError:
                self.logger.info(f"Application group '{name}' not found in folder '{folder}', creating new...")
            except Exception as fetch_error:
                # Log but continue - we'll try to create if fetch failed for other reasons
                self.logger.warning(f"Error fetching application group '{name}': {str(fetch_error)}")

            # Prepare application group data
            group_data = {
                "name": name,
                "folder": folder,
                "members": members,
            }

            # If an existing application group exists, update it
            if existing_group:
                # Update members
                existing_group.members = members

                # Perform update
                result = self.client.application_group.update(existing_group)
                self.logger.info(f"Successfully updated application group '{name}'")
            else:
                # Create a new application group
                result = self.client.application_group.create(group_data)
                self.logger.info(f"Successfully created application group '{name}'")

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("creation/update", folder, name, e)

    def delete_application_group(
        self,
        folder: str,
        name: str,
    ) -> bool:
        """Delete an application group.

        Args:
            folder: Folder containing the application group
            name: Name of the application group to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting application group: {name} from folder {folder}")

        if not self.client:
            # Return a mock result if no client is available
            return True

        try:
            # Get the application group first to retrieve its ID
            group = self.client.application_group.fetch(name=name, folder=folder)

            # Delete using the application group's ID
            self.client.application_group.delete(object_id=str(group.id))
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder, name, e)

    def get_application_group(
        self,
        folder: str,
        name: str,
    ) -> dict[str, Any]:
        """Get an application group by name and folder.

        Args:
            folder: Folder containing the application group
            name: Name of the application group to get

        Returns:
            dict[str, Any]: The application group object

        """
        self.logger.info(f"Getting application group: {name} from folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"app-group-{name}",
                "folder": folder,
                "name": name,
                "members": ["ssl", "web-browsing"],
            }

        try:
            # Fetch the application group using the SDK
            result = self.client.application_group.fetch(name=name, folder=folder)

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieval", folder, name, e)

    def list_application_groups(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List application groups in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return objects defined exactly in the specified container

        Returns:
            list[dict[str, Any]]: List of application group objects

        """
        container = folder or snippet or device or "ngfw-shared"
        self.logger.info(f"Listing application groups in {folder=}, {snippet=}, {device=} (exact_match={exact_match})")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "app-group-mock1",
                    "folder": folder or "ngfw-shared",
                    "name": "web-apps",
                    "members": ["ssl", "web-browsing"],
                },
                {
                    "id": "app-group-mock2",
                    "folder": folder or "ngfw-shared",
                    "name": "database-apps",
                    "members": ["ms-sql", "mysql", "oracle-database"],
                },
            ]

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            # List application groups using the SDK
            results = self.client.application_group.list(exact_match=exact_match, **container_kwargs)

            # Convert SDK response to a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container, "application groups", e)

    # Application Filters ------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_application_filter(
        self,
        folder: str,
        name: str,
        category: list[str],
        subcategory: list[str],
        technology: list[str],
        risk: list[int],
        evasive: bool = False,
        pervasive: bool = False,
        excessive_bandwidth_use: bool = False,
        used_by_malware: bool = False,
        transfers_files: bool = False,
        has_known_vulnerabilities: bool = False,
        tunnels_other_apps: bool = False,
        prone_to_misuse: bool = False,
        no_certifications: bool = False,
    ) -> dict[str, Any]:
        """Create an application filter.

        Args:
            folder: Folder to create the application filter in
            name: Name of the application filter
            category: List of category strings
            subcategory: List of subcategory strings
            technology: List of technology strings
            risk: List of risk levels (1-5)
            evasive: Uses evasive techniques
            pervasive: Widely used
            excessive_bandwidth_use: Uses excessive bandwidth
            used_by_malware: Used by malware
            transfers_files: Transfers files
            has_known_vulnerabilities: Has known vulnerabilities
            tunnels_other_apps: Tunnels other applications
            prone_to_misuse: Prone to misuse
            no_certifications: Lacks certifications

        Returns:
            dict[str, Any]: The created application filter object

        Note:
            If an application filter with the same name already exists in the folder, it will be updated.

        """
        self.logger.info(f"Creating or updating application filter: {name} in folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"app-filter-{name}",
                "folder": folder,
                "name": name,
                "category": category,
                "sub_category": subcategory,
                "technology": technology,
                "risk": risk,
                "evasive": evasive,
                "pervasive": pervasive,
                "excessive_bandwidth_use": excessive_bandwidth_use,
                "used_by_malware": used_by_malware,
                "transfers_files": transfers_files,
                "has_known_vulnerabilities": has_known_vulnerabilities,
                "tunnels_other_apps": tunnels_other_apps,
                "prone_to_misuse": prone_to_misuse,
                "no_certifications": no_certifications,
            }

        try:
            # First, try to fetch the existing application filter
            existing_filter = None
            try:
                existing_filter = self.client.application_filter.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing application filter '{name}' in folder '{folder}', updating...")
            except NotFoundError:
                self.logger.info(f"Application filter '{name}' not found in folder '{folder}', creating new...")
            except Exception as fetch_error:
                # Log but continue - we'll try to create if fetch failed for other reasons
                self.logger.warning(f"Error fetching application filter '{name}': {str(fetch_error)}")

            # Prepare application filter data
            filter_data = {
                "name": name,
                "folder": folder,
                "category": category,
                "sub_category": subcategory,
                "technology": technology,
                "risk": risk,
            }

            # Only add boolean fields if they're True
            if evasive:
                filter_data["evasive"] = evasive
            if pervasive:
                filter_data["pervasive"] = pervasive
            if excessive_bandwidth_use:
                filter_data["excessive_bandwidth_use"] = excessive_bandwidth_use
            if used_by_malware:
                filter_data["used_by_malware"] = used_by_malware
            if transfers_files:
                filter_data["transfers_files"] = transfers_files
            if has_known_vulnerabilities:
                filter_data["has_known_vulnerabilities"] = has_known_vulnerabilities
            if tunnels_other_apps:
                filter_data["tunnels_other_apps"] = tunnels_other_apps
            if prone_to_misuse:
                filter_data["prone_to_misuse"] = prone_to_misuse
            if no_certifications:
                filter_data["no_certifications"] = no_certifications

            # If an application filter exists, update it
            if existing_filter:
                # Update all fields
                existing_filter.category = category
                existing_filter.sub_category = subcategory
                existing_filter.technology = technology
                existing_filter.risk = risk
                existing_filter.evasive = evasive
                existing_filter.pervasive = pervasive
                existing_filter.excessive_bandwidth_use = excessive_bandwidth_use
                existing_filter.used_by_malware = used_by_malware
                existing_filter.transfers_files = transfers_files
                existing_filter.has_known_vulnerabilities = has_known_vulnerabilities
                existing_filter.tunnels_other_apps = tunnels_other_apps
                existing_filter.prone_to_misuse = prone_to_misuse
                existing_filter.no_certifications = no_certifications

                # Perform update
                result = self.client.application_filter.update(existing_filter)
                self.logger.info(f"Successfully updated application filter '{name}'")
            else:
                # Create a new application filter
                result = self.client.application_filter.create(filter_data)
                self.logger.info(f"Successfully created application filter '{name}'")

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("creation/update", folder, name, e)

    def delete_application_filter(
        self,
        folder: str,
        name: str,
    ) -> bool:
        """Delete an application filter.

        Args:
            folder: Folder containing the application filter
            name: Name of the application filter to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting application filter: {name} from folder {folder}")

        if not self.client:
            # Return a mock result if no client is available
            return True

        try:
            # Get the application filter first to retrieve its ID
            filter_obj = self.client.application_filter.fetch(name=name, folder=folder)

            # Delete using the application filter's ID
            self.client.application_filter.delete(object_id=str(filter_obj.id))
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder, name, e)

    def get_application_filter(
        self,
        folder: str,
        name: str,
    ) -> dict[str, Any]:
        """Get an application filter by name and folder.

        Args:
            folder: Folder containing the application filter
            name: Name of the application filter to get

        Returns:
            dict[str, Any]: The application filter object

        """
        self.logger.info(f"Getting application filter: {name} from folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"app-filter-{name}",
                "folder": folder,
                "name": name,
                "category": ["business-systems", "networking"],
                "sub_category": ["database", "routing"],
                "technology": ["client-server", "network-protocol"],
                "risk": [1, 2, 3],
                "evasive": False,
                "pervasive": True,
                "excessive_bandwidth_use": False,
                "used_by_malware": False,
                "transfers_files": True,
                "has_known_vulnerabilities": False,
                "tunnels_other_apps": False,
                "prone_to_misuse": False,
                "no_certifications": False,
            }

        try:
            # Fetch the application filter using the SDK
            result = self.client.application_filter.fetch(name=name, folder=folder)

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieval", folder, name, e)

    def list_application_filters(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List application filters in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return objects defined exactly in the specified container

        Returns:
            list[dict[str, Any]]: List of application filter objects

        """
        container = folder or snippet or device or "ngfw-shared"
        self.logger.info(f"Listing application filters in {folder=}, {snippet=}, {device=} (exact_match={exact_match})")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "app-filter-mock1",
                    "folder": folder or "ngfw-shared",
                    "name": "high-risk-apps",
                    "category": ["business-systems"],
                    "sub_category": ["database"],
                    "technology": ["client-server"],
                    "risk": [4, 5],
                    "evasive": True,
                    "pervasive": False,
                    "excessive_bandwidth_use": False,
                    "used_by_malware": True,
                    "transfers_files": False,
                    "has_known_vulnerabilities": True,
                    "tunnels_other_apps": False,
                    "prone_to_misuse": True,
                    "no_certifications": False,
                },
                {
                    "id": "app-filter-mock2",
                    "folder": folder or "ngfw-shared",
                    "name": "file-transfer-apps",
                    "category": ["collaboration"],
                    "sub_category": ["file-sharing"],
                    "technology": ["peer-to-peer", "client-server"],
                    "risk": [2, 3],
                    "evasive": False,
                    "pervasive": True,
                    "excessive_bandwidth_use": True,
                    "used_by_malware": False,
                    "transfers_files": True,
                    "has_known_vulnerabilities": False,
                    "tunnels_other_apps": False,
                    "prone_to_misuse": False,
                    "no_certifications": False,
                },
            ]

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            # List application filters using the SDK
            results = self.client.application_filter.list(exact_match=exact_match, **container_kwargs)

            # Convert SDK response to a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container, "application filters", e)

    # Dynamic User Groups ------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_dynamic_user_group(
        self,
        folder: str,
        name: str,
        filter: str,
        description: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a dynamic user group.

        Args:
            folder: Folder to create the dynamic user group in
            name: Name of the dynamic user group
            filter: Tag-based filter expression
            description: Optional description
            tags: Optional list of tags

        Returns:
            dict[str, Any]: The created dynamic user group object

        Note:
            If a dynamic user group with the same name already exists in the folder, it will be updated.

        """
        tags = tags or []
        self.logger.info(f"Creating or updating dynamic user group: {name} in folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"dug-{name}",
                "folder": folder,
                "name": name,
                "filter": filter,
                "description": description,
                "tag": tags,
            }

        try:
            # First, try to fetch the existing dynamic user group
            existing_group = None
            try:
                existing_group = self.client.dynamic_user_group.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing dynamic user group '{name}' in folder '{folder}', updating...")
            except NotFoundError:
                self.logger.info(f"Dynamic user group '{name}' not found in folder '{folder}', creating new...")
            except Exception as fetch_error:
                # Log but continue - we'll try to create if fetch failed for other reasons
                self.logger.warning(f"Error fetching dynamic user group '{name}': {str(fetch_error)}")

            # Prepare dynamic user group data
            group_data = {
                "name": name,
                "folder": folder,
                "filter": filter,
                "description": description or "",
            }

            if tags:
                group_data["tag"] = tags  # SDK expects 'tag', not 'tags'

            # If a dynamic user group exists, update it
            if existing_group:
                # Update fields
                existing_group.filter = filter
                existing_group.description = description or ""
                if tags is not None:  # Only update tags if explicitly provided
                    existing_group.tag = tags

                # Perform update
                result = self.client.dynamic_user_group.update(existing_group)
                self.logger.info(f"Successfully updated dynamic user group '{name}'")
            else:
                # Create a new dynamic user group
                result = self.client.dynamic_user_group.create(group_data)
                self.logger.info(f"Successfully created dynamic user group '{name}'")

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("creation/update", folder, name, e)

    def delete_dynamic_user_group(
        self,
        folder: str,
        name: str,
    ) -> bool:
        """Delete a dynamic user group.

        Args:
            folder: Folder containing the dynamic user group
            name: Name of the dynamic user group to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting dynamic user group: {name} from folder {folder}")

        if not self.client:
            # Return a mock result if no client is available
            return True

        try:
            # Get the dynamic user group first to retrieve its ID
            group = self.client.dynamic_user_group.fetch(name=name, folder=folder)

            # Delete using the dynamic user group's ID
            self.client.dynamic_user_group.delete(object_id=str(group.id))
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder, name, e)

    def get_dynamic_user_group(
        self,
        folder: str,
        name: str,
    ) -> dict[str, Any]:
        """Get a dynamic user group by name and folder.

        Args:
            folder: Folder containing the dynamic user group
            name: Name of the dynamic user group to get

        Returns:
            dict[str, Any]: The dynamic user group object

        """
        self.logger.info(f"Getting dynamic user group: {name} from folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"dug-{name}",
                "folder": folder,
                "name": name,
                "filter": "tag.Department='IT' and tag.Environment='Production'",
                "description": "Mock dynamic user group",
                "tag": ["mock", "test"],
            }

        try:
            # Fetch the dynamic user group using the SDK
            result = self.client.dynamic_user_group.fetch(name=name, folder=folder)

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieval", folder, name, e)

    def list_dynamic_user_groups(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List dynamic user groups in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return objects defined exactly in the specified container

        Returns:
            list[dict[str, Any]]: List of dynamic user group objects

        """
        container = folder or snippet or device or "ngfw-shared"
        self.logger.info(f"Listing dynamic user groups in {folder=}, {snippet=}, {device=} (exact_match={exact_match})")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "dug-mock1",
                    "folder": folder or "ngfw-shared",
                    "name": "it-admins",
                    "filter": "tag.Department='IT' and tag.Role='Admin'",
                    "description": "IT administrators group",
                    "tag": ["mock", "admin"],
                },
                {
                    "id": "dug-mock2",
                    "folder": folder or "ngfw-shared",
                    "name": "remote-workers",
                    "filter": "tag.Location='Remote' and tag.Status='Active'",
                    "description": "Remote workers group",
                    "tag": ["mock", "remote"],
                },
            ]

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            # List dynamic user groups using the SDK
            results = self.client.dynamic_user_group.list(exact_match=exact_match, **container_kwargs)

            # Convert SDK response to a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container, "dynamic user groups", e)

    # ======================================================================================================================================================================================
    # NETWORK CONFIGURATION METHODS
    # ======================================================================================================================================================================================

    # External Dynamic Lists ---------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_external_dynamic_list(
        self,
        folder: str,
        name: str,
        type_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Create an external dynamic list.

        Args:
            folder: Folder to create the EDL in
            name: Name of the EDL
            type_config: Type configuration with EDL type and settings

        Returns:
            dict[str, Any]: The created EDL object

        Note:
            This uses smart upsert logic - if an EDL with the same name already exists, it will be updated.

        """
        self.logger.info(f"Creating or updating external dynamic list: {name} in folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"edl-{name}",
                "folder": folder,
                "name": name,
                "type": type_config,
            }

        try:
            # Prepare the EDL data
            edl_data = {
                "folder": folder,
                "name": name,
                "type": type_config,
            }

            # First, try to fetch the existing EDL
            try:
                existing_edl = self.client.external_dynamic_list.fetch(name=name, folder=folder)
                # Update existing EDL
                edl_data["id"] = str(existing_edl.id)
                result = self.client.external_dynamic_list.update(edl_data)
            except Exception as e:
                # If the HIP object doesn't exist, create a new one
                self.logger.debug(f"EDL {name} not found, creating a new one", exc_info=e)
                # EDL doesn't exist, create a new one
                result = self.client.external_dynamic_list.create(edl_data)

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("creation/update", folder, name, e)

    def delete_external_dynamic_list(
        self,
        folder: str,
        name: str,
    ) -> bool:
        """Delete an external dynamic list.

        Args:
            folder: Folder containing the EDL
            name: Name of the EDL to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting external dynamic list: {name} from folder {folder}")

        if not self.client:
            # Return a mock result if no client is available
            return True

        try:
            # Get the EDL first to retrieve its ID
            edl = self.client.external_dynamic_list.fetch(name=name, folder=folder)

            # Delete using the EDL's ID
            self.client.external_dynamic_list.delete(edl_id=str(edl.id))
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder, name, e)

    def get_external_dynamic_list(
        self,
        folder: str,
        name: str,
    ) -> dict[str, Any]:
        """Get an external dynamic list by name and folder.

        Args:
            folder: Folder containing the EDL
            name: Name of the EDL to get

        Returns:
            dict[str, Any]: The EDL object

        """
        self.logger.info(f"Getting external dynamic list: {name} from folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"edl-{name}",
                "folder": folder,
                "name": name,
                "type": {
                    "predefined_ip": {
                        "url": "https://example.com/blocklist.txt",
                        "description": "Mock external IP blocklist",
                        "exception_list": ["192.168.1.0/24", "10.0.0.0/8"],
                    }
                },
            }

        try:
            # Fetch the EDL using the SDK
            result = self.client.external_dynamic_list.fetch(name=name, folder=folder)

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieval", folder, name, e)

    def list_external_dynamic_lists(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List external dynamic lists in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return objects defined exactly in the specified container

        Returns:
            list[dict[str, Any]]: List of EDL objects

        """
        container = folder or snippet or device or "Texas"
        self.logger.info(f"Listing external dynamic lists in {folder=}, {snippet=}, {device=} (exact_match={exact_match})")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "edl-mock1",
                    "folder": folder or "Texas",
                    "name": "paloalto-bulletproof-ip-list",
                    "type": {
                        "predefined_ip": {
                            "url": "https://saasedl.paloaltonetworks.com/feeds/BulletproofIPList",
                            "description": "Palo Alto Networks Bulletproof IP addresses",
                        }
                    },
                },
                {
                    "id": "edl-mock2",
                    "folder": folder or "Texas",
                    "name": "custom-blocklist",
                    "type": {
                        "ip": {
                            "url": "https://example.com/custom-blocklist.txt",
                            "description": "Custom IP blocklist",
                            "recurring": {"hourly": {}},
                            "exception_list": ["192.168.0.0/16"],
                        }
                    },
                },
                {
                    "id": "edl-mock3",
                    "folder": folder or "Texas",
                    "name": "malicious-domains",
                    "type": {
                        "domain": {
                            "url": "https://example.com/malicious-domains.txt",
                            "description": "Known malicious domains",
                            "recurring": {"daily": {"at": "03"}},
                            "expand_domain": True,
                        }
                    },
                },
            ]

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            # List EDLs using the SDK
            results = self.client.external_dynamic_list.list(exact_match=exact_match, **container_kwargs)

            # Convert SDK response to a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container, "external dynamic lists", e)

    # HIP Objects --------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_hip_object(
        self,
        folder: str,
        name: str,
        description: str | None = None,
        host_info: dict[str, Any] | None = None,
        network_info: dict[str, Any] | None = None,
        patch_management: dict[str, Any] | None = None,
        disk_encryption: dict[str, Any] | None = None,
        mobile_device: dict[str, Any] | None = None,
        certificate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a HIP object.

        Args:
            folder: Folder to create the HIP object in
            name: Name of the HIP object
            description: Description of the HIP object
            host_info: Host information criteria
            network_info: Network information criteria
            patch_management: Patch management criteria
            disk_encryption: Disk encryption criteria
            mobile_device: Mobile device criteria
            certificate: Certificate criteria

        Returns:
            dict[str, Any]: The created HIP object

        Note:
            This uses smart upsert logic - if a HIP object with the same name already exists, it will be updated.

        """
        self.logger.info(f"Creating or updating HIP object: {name} in folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"hip-{name}",
                "folder": folder,
                "name": name,
                "description": description or "Mock HIP object",
                "host_info": host_info,
                "network_info": network_info,
                "patch_management": patch_management,
                "disk_encryption": disk_encryption,
                "mobile_device": mobile_device,
                "certificate": certificate,
            }

        try:
            # Prepare the HIP object data
            hip_data = {
                "folder": folder,
                "name": name,
            }

            # Add optional fields if provided
            if description:
                hip_data["description"] = description
            if host_info:
                hip_data["host_info"] = host_info
            if network_info:
                hip_data["network_info"] = network_info
            if patch_management:
                hip_data["patch_management"] = patch_management
            if disk_encryption:
                hip_data["disk_encryption"] = disk_encryption
            if mobile_device:
                hip_data["mobile_device"] = mobile_device
            if certificate:
                hip_data["certificate"] = certificate

            # First, try to fetch the existing HIP object
            try:
                existing_hip = self.client.hip_object.fetch(name=name, folder=folder)
                # Update and return an existing HIP object
                hip_data["id"] = str(existing_hip.id)
                result = self.client.hip_object.update(hip_data)
            except Exception as e:
                # If the HIP object doesn't exist, create a new one
                self.logger.debug(f"HIP object {name} not found, creating a new one", exc_info=e)
                # HIP object doesn't exist, create a new one
                result = self.client.hip_object.create(hip_data)

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("creation/update", folder, name, e)

    def delete_hip_object(
        self,
        folder: str,
        name: str,
    ) -> bool:
        """Delete a HIP object.

        Args:
            folder: Folder containing the HIP object
            name: Name of the HIP object to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting HIP object: {name} from folder {folder}")

        if not self.client:
            # Return a mock result if no client is available
            return True

        try:
            # Get the HIP object first to retrieve its ID
            hip_obj = self.client.hip_object.fetch(name=name, folder=folder)

            # Delete using the HIP object's ID
            self.client.hip_object.delete(object_id=str(hip_obj.id))
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder, name, e)

    def get_hip_object(
        self,
        folder: str,
        name: str,
    ) -> dict[str, Any]:
        """Get a HIP object by name and folder.

        Args:
            folder: Folder containing the HIP object
            name: Name of the HIP object to get

        Returns:
            dict[str, Any]: The HIP object

        """
        self.logger.info(f"Getting HIP object: {name} from folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"hip-{name}",
                "folder": folder,
                "name": name,
                "description": "Mock Windows workstation policy",
                "host_info": {
                    "criteria": {
                        "os": {"contains": {"Microsoft": "All"}},
                        "managed": True,
                    }
                },
                "disk_encryption": {
                    "criteria": {
                        "is_installed": True,
                        "encrypted_locations": [
                            {
                                "name": "C:",
                                "encryption_state": {"is": "encrypted"},
                            }
                        ],
                    },
                    "vendor": [{"name": "BitLocker", "product": []}],
                },
            }

        try:
            # Fetch the HIP object using the SDK
            result = self.client.hip_object.fetch(name=name, folder=folder)

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieval", folder, name, e)

    def list_hip_objects(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List HIP objects in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return objects defined exactly in the specified container

        Returns:
            list[dict[str, Any]]: List of HIP objects

        """
        container = folder or snippet or device or "Texas"
        self.logger.info(f"Listing HIP objects in {folder=}, {snippet=}, {device=} (exact_match={exact_match})")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "hip-mock1",
                    "folder": folder or "Texas",
                    "name": "windows-workstation",
                    "description": "Windows workstation compliance policy",
                    "host_info": {
                        "criteria": {
                            "os": {"contains": {"Microsoft": "All"}},
                            "managed": True,
                        }
                    },
                    "disk_encryption": {
                        "criteria": {"is_installed": True},
                        "vendor": [{"name": "BitLocker", "product": []}],
                    },
                },
                {
                    "id": "hip-mock2",
                    "folder": folder or "Texas",
                    "name": "mobile-device-policy",
                    "description": "Mobile device compliance policy",
                    "mobile_device": {
                        "criteria": {
                            "jailbroken": False,
                            "disk_encrypted": True,
                            "passcode_set": True,
                            "last_checkin_time": {"days": 7},
                        }
                    },
                },
                {
                    "id": "hip-mock3",
                    "folder": folder or "Texas",
                    "name": "patch-compliance",
                    "description": "Patch management compliance",
                    "patch_management": {
                        "criteria": {
                            "is_installed": True,
                            "missing_patches": {
                                "check": "has-none",
                                "severity": 50,
                            },
                        },
                        "vendor": [{"name": "Microsoft", "product": ["Windows"]}],
                    },
                },
            ]

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            # List HIP objects using the SDK
            results = self.client.hip_object.list(exact_match=exact_match, **container_kwargs)

            # Convert SDK response to a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container, "HIP objects", e)

    # HIP Profiles -------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_hip_profile(
        self,
        folder: str,
        name: str,
        match: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create or update a HIP profile.

        Args:
            folder: Folder where the HIP profile will be created
            name: Name of the HIP profile
            match: Match criteria for the HIP profile
            description: Optional description of the HIP profile

        Returns:
            dict[str, Any]: Created HIP profile object

        """
        self.logger.info(f"Creating/updating HIP profile '{name}' in folder: {folder}")

        if not self.client:
            # Return a mock response if no client is available
            return {
                "id": f"hip-profile-{name}",
                "folder": folder,
                "name": name,
                "match": match,
                "description": description or f"Mock HIP profile for {name}",
            }

        try:
            # Check if a HIP profile already exists
            try:
                existing = self.client.hip_profile.fetch(name=name, folder=folder)
                if existing:
                    # Update existing HIP profile
                    self.logger.info(f"HIP profile '{name}' already exists, updating...")
                    existing.description = description if description is not None else existing.description
                    existing.match = match
                    updated = self.client.hip_profile.update(existing)
                    return json.loads(updated.model_dump_json(exclude_unset=True))
            except Exception as fetch_error:
                # HIP profile doesn't exist, create a new one
                self.logger.debug(f"HIP profile '{name}' not found, creating new: {fetch_error}")

            # Prepare the profile data
            profile_data = {
                "folder": folder,
                "name": name,
                "match": match,
            }

            if description:
                profile_data["description"] = description

            # Create the HIP profile
            result = self.client.hip_profile.create(profile_data)
            return json.loads(result.model_dump_json(exclude_unset=True))

        except Exception as e:
            self._handle_api_exception("creating/updating", name, "HIP profile", e)

    def delete_hip_profile(self, folder: str, name: str) -> bool:
        """Delete a HIP profile.

        Args:
            folder: Folder containing the HIP profile
            name: Name of the HIP profile to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting HIP profile '{name}' from folder: {folder}")

        if not self.client:
            self.logger.info(f"Mock mode: Would delete HIP profile '{name}'")
            return True

        try:
            # First, fetch the HIP profile to get its ID
            hip_profile = self.client.hip_profile.fetch(name=name, folder=folder)
            self.client.hip_profile.delete(str(hip_profile.id))
            self.logger.info(f"Successfully deleted HIP profile '{name}'")
            return True
        except Exception as e:
            self._handle_api_exception("deleting", name, "HIP profile", e)

    def get_hip_profile(self, folder: str, name: str) -> dict[str, Any]:
        """Get a specific HIP profile by name.

        Args:
            folder: Folder containing the HIP profile
            name: Name of the HIP profile

        Returns:
            dict[str, Any]: HIP profile object

        """
        self.logger.info(f"Getting HIP profile '{name}' from folder: {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"hip-profile-{name}",
                "folder": folder,
                "name": name,
                "match": "'custom-check' and 'endpoint-management'",
                "description": f"Mock HIP profile for {name}",
            }

        try:
            # Fetch the HIP profile by name and folder
            result = self.client.hip_profile.fetch(name=name, folder=folder)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("fetching", name, "HIP profile", e)

    def list_hip_profiles(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List HIP profiles in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return objects defined exactly in the specified container

        Returns:
            list[dict[str, Any]]: List of HIP profiles

        """
        container = folder or snippet or device or "Texas"
        self.logger.info(f"Listing HIP profiles in {folder=}, {snippet=}, {device=} (exact_match={exact_match})")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "hip-profile-mock1",
                    "folder": folder or "Texas",
                    "name": "endpoint-compliance",
                    "match": "'endpoint-management' and 'patch-management'",
                    "description": "Endpoint compliance profile",
                },
                {
                    "id": "hip-profile-mock2",
                    "folder": folder or "Texas",
                    "name": "mobile-device-policy",
                    "match": "'mobile-device' and 'disk-encryption'",
                    "description": "Mobile device security policy",
                },
            ]

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            # List HIP profiles using the SDK
            results = self.client.hip_profile.list(exact_match=exact_match, **container_kwargs)

            # Convert SDK response to a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container, "HIP profiles", e)

    # HTTP Server Profiles -----------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_http_server_profile(
        self,
        folder: str,
        name: str,
        servers: list[dict[str, Any]],
        description: str | None = None,
        tag_registration: bool = False,
        format_config: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create or update an HTTP server profile.

        Args:
            folder: Folder where the HTTP server profile will be created
            name: Name of the HTTP server profile
            servers: List of server configurations
            description: Optional description of the HTTP server profile
            tag_registration: Whether to register tags on match
            format_config: Optional format configuration for different log types

        Returns:
            dict[str, Any]: Created an HTTP server profile object

        """
        self.logger.info(f"Creating/updating HTTP server profile '{name}' in folder: {folder}")

        if not self.client:
            # Return a mock response if no client is available
            return {
                "id": f"http-server-profile-{name}",
                "folder": folder,
                "name": name,
                "server": servers,
                "description": description or f"Mock HTTP server profile for {name}",
                "tag_registration": tag_registration,
            }

        try:
            # Check if an HTTP server profile already exists
            try:
                existing = self.client.http_server_profile.fetch(name=name, folder=folder)
                if existing:
                    # Update an existing HTTP server profile
                    self.logger.info(f"HTTP server profile '{name}' already exists, updating...")
                    existing.description = description if description is not None else existing.description
                    existing.server = servers
                    existing.tag_registration = tag_registration
                    if format_config:
                        existing.format = format_config
                    updated = self.client.http_server_profile.update(existing)
                    return json.loads(updated.model_dump_json(exclude_unset=True))
            except Exception as fetch_error:
                # HTTP server profile doesn't exist, create a new one
                self.logger.debug(f"HTTP server profile '{name}' not found, creating new: {fetch_error}")

            # Prepare the profile data
            profile_data = {
                "folder": folder,
                "name": name,
                "server": servers,
            }

            if description:
                profile_data["description"] = description

            if tag_registration:
                profile_data["tag_registration"] = tag_registration

            if format_config:
                profile_data["format"] = format_config

            # Create the HTTP server profile
            result = self.client.http_server_profile.create(profile_data)
            return json.loads(result.model_dump_json(exclude_unset=True))

        except Exception as e:
            self._handle_api_exception("creating/updating", name, "HTTP server profile", e)

    def delete_http_server_profile(self, folder: str, name: str) -> bool:
        """Delete an HTTP server profile.

        Args:
            folder: Folder containing the HTTP server profile
            name: Name of the HTTP server profile to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting HTTP server profile '{name}' from folder: {folder}")

        if not self.client:
            self.logger.info(f"Mock mode: Would delete HTTP server profile '{name}'")
            return True

        try:
            # First, fetch the HTTP server profile to get its ID
            http_server_profile = self.client.http_server_profile.fetch(name=name, folder=folder)
            self.client.http_server_profile.delete(str(http_server_profile.id))
            self.logger.info(f"Successfully deleted HTTP server profile '{name}'")
            return True
        except Exception as e:
            self._handle_api_exception("deleting", name, "HTTP server profile", e)

    def get_http_server_profile(self, folder: str, name: str) -> dict[str, Any]:
        """Get a specific HTTP server profile by name.

        Args:
            folder: Folder containing the HTTP server profile
            name: Name of the HTTP server profile

        Returns:
            dict[str, Any]: HTTP server profile object

        """
        self.logger.info(f"Getting HTTP server profile '{name}' from folder: {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"http-server-profile-{name}",
                "folder": folder,
                "name": name,
                "server": [
                    {
                        "name": "mock-server",
                        "address": "192.168.1.100",
                        "protocol": "HTTPS",
                        "port": 443,
                        "tls_version": "1.2",
                    }
                ],
                "description": f"Mock HTTP server profile for {name}",
                "tag_registration": False,
            }

        try:
            # Fetch the HTTP server profile by name and folder
            result = self.client.http_server_profile.fetch(name=name, folder=folder)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("fetching", name, "HTTP server profile", e)

    def list_http_server_profiles(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List HTTP server profiles in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return objects defined exactly in the specified container

        Returns:
            list[dict[str, Any]]: List of HTTP server profiles

        """
        container = folder or snippet or device or "Texas"
        self.logger.info(f"Listing HTTP server profiles in {folder=}, {snippet=}, {device=} (exact_match={exact_match})")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "http-server-profile-mock1",
                    "folder": folder or "Texas",
                    "name": "syslog-http-profile",
                    "server": [
                        {
                            "name": "syslog-server-1",
                            "address": "syslog.example.com",
                            "protocol": "HTTPS",
                            "port": 443,
                            "tls_version": "1.2",
                        }
                    ],
                    "description": "Syslog HTTP forwarding profile",
                    "tag_registration": True,
                },
                {
                    "id": "http-server-profile-mock2",
                    "folder": folder or "Texas",
                    "name": "siem-http-profile",
                    "server": [
                        {
                            "name": "siem-server",
                            "address": "siem.example.com",
                            "protocol": "HTTP",
                            "port": 8080,
                            "http_method": "POST",
                        }
                    ],
                    "description": "SIEM integration profile",
                    "tag_registration": False,
                },
            ]

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            # List HTTP server profiles using the SDK
            results = self.client.http_server_profile.list(exact_match=exact_match, **container_kwargs)

            # Convert SDK response to a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container, "HTTP server profiles", e)

    # log-forwarding Profiles --------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_log_forwarding_profile(
        self,
        folder: str,
        name: str,
        match_list: list[dict[str, Any]] | None = None,
        description: str | None = None,
        enhanced_application_logging: bool = False,
    ) -> dict[str, Any]:
        """Create or update a log-forwarding profile.

        Args:
            folder: Folder where the log-forwarding profile will be created
            name: Name of the log-forwarding profile
            match_list: List of match profile configurations
            description: Optional description of the log-forwarding profile
            enhanced_application_logging: Whether to enable enhanced application logging

        Returns:
            dict[str, Any]: Created a log-forwarding profile object

        """
        self.logger.info(f"Creating/updating log-forwarding profile '{name}' in folder: {folder}")

        if not self.client:
            # Return a mock response if no client is available
            return {
                "id": f"log-forwarding-profile-{name}",
                "folder": folder,
                "name": name,
                "match_list": match_list
                or [
                    {
                        "name": "default-match",
                        "log_type": "traffic",
                        "send_to_panorama": True,
                    }
                ],
                "description": description or f"Mock log-forwarding profile for {name}",
                "enhanced_application_logging": enhanced_application_logging,
            }

        try:
            # Check if a log-forwarding profile already exists
            try:
                existing = self.client.log_forwarding_profile.fetch(name=name, folder=folder)
                if existing:
                    # Update the existing log-forwarding profile
                    self.logger.info(f"log-forwarding profile '{name}' already exists, updating...")
                    existing.description = description if description is not None else existing.description
                    existing.enhanced_application_logging = enhanced_application_logging
                    if match_list:
                        existing.match_list = match_list
                    updated = self.client.log_forwarding_profile.update(existing)
                    return json.loads(updated.model_dump_json(exclude_unset=True))
            except Exception as fetch_error:
                # log-forwarding profile doesn't exist, create a new one
                self.logger.debug(f"log-forwarding profile '{name}' not found, creating new: {fetch_error}")

            # Prepare the profile data
            profile_data = {
                "folder": folder,
                "name": name,
            }

            if description:
                profile_data["description"] = description

            if enhanced_application_logging:
                profile_data["enhanced_application_logging"] = enhanced_application_logging

            if match_list:
                # Ensure each match has a filter field (API seems to require it despite SDK showing optional)
                for match in match_list:
                    if "filter" not in match or match["filter"] is None:
                        match["filter"] = "All Logs"
                profile_data["match_list"] = match_list

            # Create the log-forwarding profile
            result = self.client.log_forwarding_profile.create(profile_data)
            return json.loads(result.model_dump_json(exclude_unset=True))

        except Exception as e:
            self._handle_api_exception("creating/updating", name, "log-forwarding profile", e)

    def delete_log_forwarding_profile(self, folder: str, name: str) -> bool:
        """Delete a log-forwarding profile.

        Args:
            folder: Folder containing the log-forwarding profile
            name: Name of the log-forwarding profile to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting log-forwarding profile '{name}' from folder: {folder}")

        if not self.client:
            # Mock deletion
            self.logger.info(f"Mock mode: Would delete log-forwarding profile '{name}' from folder '{folder}'")
            return True

        try:
            # First, fetch the log-forwarding profile to get its ID
            profile = self.client.log_forwarding_profile.fetch(name=name, folder=folder)
            if profile:
                # Delete using the ID
                self.client.log_forwarding_profile.delete(str(profile.id))
                self.logger.info(f"Successfully deleted log-forwarding profile '{name}'")
                return True
            else:
                self.logger.warning(f"log-forwarding profile '{name}' not found in folder '{folder}'")
                return False
        except Exception as e:
            self._handle_api_exception("deleting", name, "log-forwarding profile", e)

    def get_log_forwarding_profile(self, folder: str, name: str) -> dict[str, Any] | None:
        """Get a specific log-forwarding profile by name.

        Args:
            folder: Folder containing the log-forwarding profile
            name: Name of the log-forwarding profile

        Returns:
            dict[str, Any] | None: Log a forwarding profile object if found, None otherwise

        """
        self.logger.info(f"Getting log-forwarding profile '{name}' from folder: {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"log-forwarding-profile-{name}",
                "folder": folder,
                "name": name,
                "match_list": [
                    {
                        "name": "traffic-logs",
                        "log_type": "traffic",
                        "send_to_panorama": True,
                        "send_syslog": ["syslog-server-1"],
                    }
                ],
                "description": f"Mock log-forwarding profile for {name}",
                "enhanced_application_logging": True,
            }

        try:
            # Fetch the log-forwarding profile
            profile = self.client.log_forwarding_profile.fetch(name=name, folder=folder)
            return json.loads(profile.model_dump_json(exclude_unset=True)) if profile else None
        except Exception as e:
            self.logger.error(f"Failed to get log-forwarding profile '{name}': {str(e)}")
            return None

    def list_log_forwarding_profiles(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List all log-forwarding profiles in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return profiles directly in the specified container

        Returns:
            list[dict[str, Any]]: List of log-forwarding profile objects

        """
        container = folder or snippet or device or "Texas"
        self.logger.info(f"Listing log-forwarding profiles in {folder=}, {snippet=}, {device=} (exact_match={exact_match})")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "log-forwarding-profile-mock1",
                    "folder": folder or "Texas",
                    "name": "default-log-forwarding",
                    "match_list": [
                        {
                            "name": "all-traffic",
                            "log_type": "traffic",
                            "send_to_panorama": True,
                        },
                        {
                            "name": "threat-logs",
                            "log_type": "threat",
                            "send_to_panorama": True,
                            "send_syslog": ["syslog-server-1"],
                        },
                    ],
                    "description": "Default log-forwarding profile",
                    "enhanced_application_logging": False,
                },
                {
                    "id": "log-forwarding-profile-mock2",
                    "folder": folder or "Texas",
                    "name": "security-log-forwarding",
                    "match_list": [
                        {
                            "name": "security-traffic",
                            "log_type": "traffic",
                            "filter": "severity eq high",
                            "send_to_panorama": True,
                            "send_http": ["http-server-1"],
                        }
                    ],
                    "description": "Security log-forwarding profile",
                    "enhanced_application_logging": True,
                },
            ]

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            # List log-forwarding profiles using the SDK
            results = self.client.log_forwarding_profile.list(exact_match=exact_match, **container_kwargs)

            # Convert SDK response to the list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container, "log-forwarding profiles", e)

    # Services -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_service(
        self,
        folder: str,
        name: str,
        protocol: dict[str, Any],
        description: str | None = None,
        tag: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create or update a service using smart upsert logic.

        Args:
            folder: Folder where the service will be created
            name: Name of the service
            protocol: Protocol configuration (tcp or udp with port)
            description: Optional description
            tag: Optional list of tags

        Returns:
            dict[str, Any]: Created/updated service object

        """
        if not self.client:
            # Return a mock response if no client is available
            return {
                "id": f"service-{name}",
                "folder": folder,
                "name": name,
                "protocol": protocol,
                "description": description or f"Mock service for {name}",
                "tag": tag or [],
            }

        try:
            # Step 1: Try to fetch the existing service
            existing_service = None
            try:
                existing_service = self.client.service.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing service '{name}' in folder '{folder}'")
            except NotFoundError:
                self.logger.info(f"Service '{name}' not found in folder '{folder}', will create new")
            except Exception as e:
                self.logger.warning(f"Error fetching service '{name}': {str(e)}")

            if existing_service:
                # Step 2: Check what needs updating
                needs_update = False
                update_fields = []

                # Compare protocol - this is complex as it's a nested dict
                if protocol and hasattr(existing_service, "protocol"):
                    # Convert both to comparable format
                    existing_protocol = existing_service.protocol.model_dump(exclude_unset=True) if hasattr(existing_service.protocol, "model_dump") else existing_service.protocol
                    if existing_protocol != protocol:
                        existing_service.protocol = protocol
                        update_fields.append("protocol")
                        needs_update = True

                # Compare description
                if description is not None:
                    current_desc = getattr(existing_service, "description", "")
                    if current_desc != description:
                        existing_service.description = description
                        update_fields.append("description")
                        needs_update = True

                # Compare tags (as sets to ignore order)
                if tag is not None:
                    current_tags = getattr(existing_service, "tag", []) or []
                    if set(current_tags) != set(tag):
                        existing_service.tag = tag
                        update_fields.append("tags")
                        needs_update = True

                # Step 3: Only update if changes detected
                if needs_update:
                    self.logger.info(f"Updating service fields: {', '.join(update_fields)}")
                    updated = self.client.service.update(existing_service)
                    self.logger.info(f"Successfully updated service '{name}' in folder '{folder}'")
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
                else:
                    self.logger.info(f"No changes detected for service '{name}', skipping update")
                    result = json.loads(existing_service.model_dump_json(exclude_unset=True))
                    result["__action__"] = "no_change"
                    return result
            else:
                # Step 4: Create new service
                service_data = {
                    "folder": folder,
                    "name": name,
                    "protocol": protocol,
                }

                if description:
                    service_data["description"] = description

                if tag:
                    service_data["tag"] = tag

                result = self.client.service.create(service_data)
                self.logger.info(f"Successfully created service '{name}' in folder '{folder}'")
                response = json.loads(result.model_dump_json(exclude_unset=True))
                response["__action__"] = "created"
                return response

        except Exception as e:
            self._handle_api_exception("create/update", folder, name, e)

    def delete_service(self, folder: str, name: str) -> bool:
        """Delete a service.

        Args:
            folder: Folder containing the service
            name: Name of the service to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting service '{name}' from folder: {folder}")

        if not self.client:
            self.logger.info(f"Mock mode: Would delete service '{name}'")
            return True

        try:
            # First, fetch the service to get its ID
            service = self.client.service.fetch(name=name, folder=folder)
            self.client.service.delete(str(service.id))
            self.logger.info(f"Successfully deleted service '{name}'")
            return True
        except Exception as e:
            self._handle_api_exception("deleting", name, "service", e)

    def get_service(self, folder: str, name: str) -> dict[str, Any]:
        """Get a specific service by name.

        Args:
            folder: Folder containing the service
            name: Name of the service

        Returns:
            dict[str, Any]: Service object

        """
        self.logger.info(f"Getting service '{name}' from folder: {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"service-{name}",
                "folder": folder,
                "name": name,
                "protocol": {
                    "tcp": {
                        "port": "80,443",
                        "override": {
                            "timeout": 3600,
                            "halfclose_timeout": 120,
                            "timewait_timeout": 15,
                        },
                    }
                },
                "description": f"Mock service for {name}",
                "tag": ["web", "production"],
            }

        try:
            # Fetch the service by name and folder
            result = self.client.service.fetch(name=name, folder=folder)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("fetching", name, "service", e)

    def list_services(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List services in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return objects defined exactly in the specified container

        Returns:
            list[dict[str, Any]]: List of services

        """
        container = folder or snippet or device or "Texas"
        self.logger.info(f"Listing services in {folder=}, {snippet=}, {device=} (exact_match={exact_match})")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "service-mock1",
                    "folder": folder or "Texas",
                    "name": "web-browsing",
                    "protocol": {
                        "tcp": {
                            "port": "80,443",
                        }
                    },
                    "description": "Web browsing ports",
                    "tag": ["web", "standard"],
                },
                {
                    "id": "service-mock2",
                    "folder": folder or "Texas",
                    "name": "dns",
                    "protocol": {
                        "udp": {
                            "port": "53",
                        }
                    },
                    "description": "DNS service",
                    "tag": ["infrastructure"],
                },
                {
                    "id": "service-mock3",
                    "folder": folder or "Texas",
                    "name": "ssh-custom",
                    "protocol": {
                        "tcp": {
                            "port": "2222",
                            "override": {
                                "timeout": 7200,
                            },
                        }
                    },
                    "description": "Custom SSH port",
                    "tag": ["management", "secure"],
                },
            ]

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            # List services using the SDK
            results = self.client.service.list(exact_match=exact_match, **container_kwargs)

            # Convert SDK response to show the list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container, "services", e)

    # Service Groups -----------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_service_group(
        self,
        folder: str,
        name: str,
        members: list[str],
        tag: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create or update a service group.

        Args:
            folder: Folder where the service group will be created
            name: Name of the service group
            members: List of service or service group names
            tag: Optional list of tags

        Returns:
            dict[str, Any]: The created service group object

        """
        self.logger.info(f"Creating/updating service group '{name}' in folder: {folder}")

        if not self.client:
            # Return a mock response if no client is available
            return {
                "id": f"service-group-{name}",
                "folder": folder,
                "name": name,
                "members": members,
                "tag": tag or [],
            }

        try:
            # Check if the service group already exists
            try:
                existing = self.client.service_group.fetch(name=name, folder=folder)
                if existing:
                    # Update the existing service group
                    self.logger.info(f"Service group '{name}' already exists, updating...")
                    existing.members = members
                    if tag is not None:
                        existing.tag = tag
                    updated = self.client.service_group.update(existing)
                    return json.loads(updated.model_dump_json(exclude_unset=True))
            except Exception as fetch_error:
                # Service group doesn't exist, create a new one
                self.logger.debug(f"Service group '{name}' not found, creating new: {fetch_error}")

            # Prepare the service group data
            service_group_data = {
                "folder": folder,
                "name": name,
                "members": members,
            }

            if tag:
                service_group_data["tag"] = tag

            # Create the service group
            result = self.client.service_group.create(service_group_data)
            return json.loads(result.model_dump_json(exclude_unset=True))

        except Exception as e:
            self._handle_api_exception("creating/updating", name, "service group", e)

    def delete_service_group(self, folder: str, name: str) -> bool:
        """Delete a service group.

        Args:
            folder: Folder containing the service group
            name: Name of the service group to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting service group '{name}' from folder: {folder}")

        if not self.client:
            self.logger.info(f"Mock mode: Would delete service group '{name}'")
            return True

        try:
            # First, fetch the service group to get its ID
            service_group = self.client.service_group.fetch(name=name, folder=folder)
            self.client.service_group.delete(str(service_group.id))
            self.logger.info(f"Successfully deleted service group '{name}'")
            return True
        except Exception as e:
            self._handle_api_exception("deleting", name, "service group", e)

    def get_service_group(self, folder: str, name: str) -> dict[str, Any]:
        """Get a specific service group by name.

        Args:
            folder: Folder containing the service group
            name: Name of the service group

        Returns:
            dict[str, Any]: Service group object

        """
        self.logger.info(f"Getting service group '{name}' from folder: {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"service-group-{name}",
                "folder": folder,
                "name": name,
                "members": ["web-browsing", "ssl", "custom-web"],
                "tag": ["production", "web"],
            }

        try:
            # Fetch the service group by name and folder
            result = self.client.service_group.fetch(name=name, folder=folder)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("fetching", name, "service group", e)

    def list_service_groups(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List service groups in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return objects defined exactly in the specified container

        Returns:
            list[dict[str, Any]]: List of service groups

        """
        container = folder or snippet or device or "Texas"
        self.logger.info(f"Listing service groups in {folder=}, {snippet=}, {device=} (exact_match={exact_match})")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "service-group-mock1",
                    "folder": folder or "Texas",
                    "name": "web-services",
                    "members": ["web-browsing", "ssl", "custom-web"],
                    "tag": ["web", "standard"],
                },
                {
                    "id": "service-group-mock2",
                    "folder": folder or "Texas",
                    "name": "database-services",
                    "members": ["mysql-cluster", "mssql", "oracle"],
                    "tag": ["database", "backend"],
                },
                {
                    "id": "service-group-mock3",
                    "folder": folder or "Texas",
                    "name": "infrastructure-services",
                    "members": ["dns", "ntp", "snmp", "syslog"],
                    "tag": ["infrastructure", "management"],
                },
            ]

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            # List service groups using the SDK
            results = self.client.service_group.list(exact_match=exact_match, **container_kwargs)

            # Convert SDK response to show the list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container, "service groups", e)

    # Syslog Server Profiles ---------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_syslog_server_profile(
        self,
        syslog_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create or update a syslog server profile using smart upsert logic.

        Args:
            syslog_data: The syslog server profile data

        Returns:
            Created/updated syslog server profile data

        """
        # Determine container (folder, snippet, or device)
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None

        for field in container_fields:
            if field in syslog_data and syslog_data[field] is not None:
                container_field = field
                container_value = syslog_data[field]
                break

        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")

        # Return mock data if no client
        if not self.client:
            return syslog_data

        # Check if syslog server profile already exists
        try:
            existing = self.client.syslog_server_profile.fetch(name=syslog_data["name"], **{container_field: container_value})
            # Update existing syslog server profile
            for key, value in syslog_data.items():
                if key not in container_fields and value is not None:
                    setattr(existing, key, value)
            updated = existing.update()
            self.logger.info(f"Updated existing syslog server profile '{syslog_data['name']}' in {container_field} '{container_value}'")
            return json.loads(updated.model_dump_json(exclude_unset=True))
        except Exception as e:
            # If a profile doesn't exist, create a new one
            self.logger.debug(f"Syslog server profile '{syslog_data['name']}' not found, creating new: {e}")
            # Create a new syslog server profile
            try:
                created = self.client.syslog_server_profile.create(syslog_data)
                self.logger.info(f"Created new syslog server profile '{syslog_data['name']}' in {container_field} '{container_value}'")
                return json.loads(created.model_dump_json(exclude_unset=True))
            except Exception as create_error:
                self._handle_api_exception(
                    "creating",
                    container_value or "",
                    f"syslog server profile '{syslog_data['name']}'",
                    create_error,
                )

    def delete_syslog_server_profile(
        self,
        name: str,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
    ) -> None:
        """Delete a syslog server profile.

        Args:
            name: Name of the syslog server profile to delete
            folder: Folder location
            snippet: Snippet location
            device: Device location

        """
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete syslog server profile: {name}")
            return

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            self.client.syslog_server_profile.delete(name, **container_kwargs)
            self.logger.info(f"Deleted syslog server profile: {name}")
        except Exception as e:
            location_value = folder or snippet or device or "unknown"
            self._handle_api_exception(
                "deleting",
                location_value,
                f"syslog server profile '{name}'",
                e,
            )

    def get_syslog_server_profile(
        self,
        name: str,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
    ) -> dict[str, Any] | None:
        """Get a specific syslog server profile.

        Args:
            name: Name of the syslog server profile to retrieve
            folder: Folder location
            snippet: Snippet location
            device: Device location

        Returns:
            Syslog server profile data or None if not found

        """
        if not self.client:
            return {
                "id": "syslog-mock",
                "name": name,
                "folder": folder or "ngfw-shared",
                "server": [
                    {
                        "name": "primary-syslog",
                        "server": "192.168.1.100",
                        "transport": "UDP",
                        "port": 514,
                        "format": "BSD",
                        "facility": "LOG_USER",
                    }
                ],
            }

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        else:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")

        try:
            result = self.client.syslog_server_profile.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"Syslog server profile '{name}' not found")
            return None
        except Exception as e:
            location_value = folder or snippet or device or "unknown"
            self._handle_api_exception(
                "retrieving",
                location_value,
                f"syslog server profile '{name}'",
                e,
            )

    def list_syslog_server_profiles(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List syslog server profiles in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return exact matches

        Returns:
            List of syslog server profiles

        """
        if not self.client:
            return [
                {
                    "id": "syslog-mock1",
                    "folder": folder or "ngfw-shared",
                    "name": "primary-syslog-profile",
                    "server": [
                        {
                            "name": "syslog-server-1",
                            "server": "192.168.1.100",
                            "transport": "UDP",
                            "port": 514,
                            "format": "BSD",
                            "facility": "LOG_USER",
                        }
                    ],
                },
                {
                    "id": "syslog-mock2",
                    "folder": folder or "ngfw-shared",
                    "name": "backup-syslog-profile",
                    "server": [
                        {
                            "name": "syslog-server-2",
                            "server": "192.168.1.101",
                            "transport": "TCP",
                            "port": 514,
                            "format": "IETF",
                            "facility": "LOG_LOCAL0",
                        }
                    ],
                },
                {
                    "id": "syslog-mock3",
                    "folder": folder or "ngfw-shared",
                    "name": "secure-syslog-profile",
                    "server": [
                        {
                            "name": "secure-syslog",
                            "server": "syslog.example.com",
                            "transport": "SSL",
                            "port": 6514,
                            "format": "BSD",
                            "facility": "LOG_LOCAL1",
                        }
                    ],
                },
            ]

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            # List syslog server profiles using the SDK
            results = self.client.syslog_server_profile.list(exact_match=exact_match, **container_kwargs)

            # Convert SDK response to show the list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception(
                "listing",
                folder or snippet or device or "",
                "syslog server profiles",
                e,
            )

    # Tags ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_tag(
        self,
        tag_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create or update a tag using smart upsert logic.

        Args:
            tag_data: The tag data

        Returns:
            Created/updated tag data

        """
        # Determine container (folder, snippet, or device)
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None

        for field in container_fields:
            if field in tag_data and tag_data[field] is not None:
                container_field = field
                container_value = tag_data[field]
                break

        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")

        # Return mock data if no client
        if not self.client:
            return tag_data

        # Check if the tag already exists
        existing_tag = None
        try:
            existing_tag = self.client.tag.fetch(name=tag_data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing tag '{tag_data['name']}' in {container_field} '{container_value}'")
        except NotFoundError:
            self.logger.info(f"Tag '{tag_data['name']}' not found in {container_field} '{container_value}', will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching tag '{tag_data['name']}': {str(e)}")

        if existing_tag:
            # Check what needs updating
            needs_update = False
            update_fields = []

            # Compare color (handle case differences)
            if "color" in tag_data and tag_data["color"]:
                # Normalize color for comparison (API uses Title case)
                new_color = tag_data["color"].title()
                if hasattr(existing_tag, "color") and existing_tag.color != new_color:
                    existing_tag.color = new_color
                    update_fields.append("color")
                    needs_update = True

            # Compare comments
            if "comments" in tag_data and tag_data["comments"] is not None and hasattr(existing_tag, "comments") and existing_tag.comments != tag_data["comments"]:
                existing_tag.comments = tag_data["comments"]
                update_fields.append("comments")
                needs_update = True

            if needs_update:
                self.logger.info(f"Updating tag fields: {', '.join(update_fields)}")
                try:
                    updated = existing_tag.update()
                    self.logger.info(f"Successfully updated tag '{tag_data['name']}' in {container_field} '{container_value}'")
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"tag '{tag_data['name']}'", update_error)
            else:
                self.logger.info(f"No changes detected for tag '{tag_data['name']}', skipping update")
                result = json.loads(existing_tag.model_dump_json(exclude_unset=True))
                result["__action__"] = "no_change"
                return result
        else:
            # Create new tag
            try:
                created = self.client.tag.create(tag_data)
                self.logger.info(f"Created new tag '{tag_data['name']}' in {container_field} '{container_value}'")
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception(
                    "creating",
                    str(container_value),
                    f"tag '{tag_data['name']}'",
                    create_error,
                )

    def delete_tag(
        self,
        name: str,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
    ) -> None:
        """Delete a tag.

        Args:
            name: Name of the tag to delete
            folder: Folder location
            snippet: Snippet location
            device: Device location

        """
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete tag: {name}")
            return

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        else:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")

        try:
            # First, fetch the tag to get its ID
            tag = self.client.tag.fetch(name=name, **container_kwargs)
            self.client.tag.delete(str(tag.id))
            self.logger.info(f"Deleted tag: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"tag '{name}'", e)

    def get_tag(
        self,
        name: str,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
    ) -> dict[str, Any] | None:
        """Get a specific tag.

        Args:
            name: Name of the tag to retrieve
            folder: Folder location
            snippet: Snippet location
            device: Device location

        Returns:
            Tag data or None if not found

        """
        if not self.client:
            return {
                "id": "tag-mock",
                "name": name,
                "folder": folder or "ngfw-shared",
                "color": "Blue",
                "comments": "Mock tag for testing",
            }

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        else:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")

        try:
            result = self.client.tag.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"Tag '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"tag '{name}'", e)

    def list_tags(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List tags in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return exact matches

        Returns:
            List of tags

        """
        if not self.client:
            return [
                {
                    "id": "tag-mock1",
                    "folder": folder or "ngfw-shared",
                    "name": "Production",
                    "color": "Red",
                    "comments": "Production environment resources",
                },
                {
                    "id": "tag-mock2",
                    "folder": folder or "ngfw-shared",
                    "name": "Development",
                    "color": "Green",
                    "comments": "Development environment resources",
                },
                {
                    "id": "tag-mock3",
                    "folder": folder or "ngfw-shared",
                    "name": "Critical",
                    "color": "Orange",
                    "comments": "Critical infrastructure",
                },
            ]

        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            # List tags using the SDK
            results = self.client.tag.list(exact_match=exact_match, **container_kwargs)

            # Convert SDK response to the list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "tags", e)

    # ======================================================================================================================================================================================

    # ------------------------------------------------------------------------------------ Security Zones ----------------------------------------------------------------------------------

    def create_zone(
        self,
        folder: str,
        name: str,
        mode: str,
        interfaces: list[str] | None = None,
        enable_user_identification: bool | None = None,
        enable_device_identification: bool | None = None,
    ) -> dict[str, Any]:
        """Create a security zone.

        Args:
            folder: Folder to create the zone in
            name: Name of the zone
            mode: Zone mode (L2, L3, external, virtual-wire, tunnel)
            interfaces: List of interfaces
            enable_user_identification: Enable user identification
            enable_device_identification: Enable device identification

        Returns:
            dict[str, Any]: The created zone object

        Note:
            If a security zone with the same name already exists in the folder, it will be updated.
            Note that the SDK doesn't support changing zone mode after creation, so if the mode
            differs, the zone will be deleted and recreated.

        """
        interfaces = interfaces or []
        self.logger.info(f"Creating or updating zone: {name} with mode {mode} in folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"zone-{name}",
                "folder": folder,
                "name": name,
                "mode": mode,
                "interfaces": interfaces,
            }

        try:
            # First, try to fetch the existing zone
            existing_zone = None
            try:
                existing_zone = self.client.security_zone.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing security zone '{name}' in folder '{folder}', updating...")
            except NotFoundError:
                self.logger.info(f"Security zone '{name}' not found in folder '{folder}', creating new...")
            except Exception as fetch_error:
                # Log but continue - we'll try to create if fetch failed for other reasons
                self.logger.warning(f"Error fetching security zone '{name}': {str(fetch_error)}")

            # Prepare zone data
            zone_data = {
                "name": name,
                "folder": folder,
            }

            # Note: The zone mode is typically stored within the network configuration
            # For this method, we'll treat mode as a way to initialize the zone,
            # but we can't change it after creation according to SDK constraints

            if interfaces:
                zone_data["interfaces"] = interfaces

            # Add identification settings if specified
            if enable_user_identification is not None:
                zone_data["enable_user_identification"] = enable_user_identification
            if enable_device_identification is not None:
                zone_data["enable_device_identification"] = enable_device_identification

            # If zone exists, update it
            if existing_zone:
                # Check if we need to recreate due to mode change
                # Since the SDK model doesn't directly expose mode, we'll update other fields
                # and log a warning if the mode might have changed

                # Update only the fields that are changing
                # Note: description field not supported by an SDK security zone model

                # Update interfaces if provided
                if interfaces is not None:
                    # Note: interfaces might be part of network configuration
                    # This is a simplified approach - actual implementation may vary
                    if hasattr(existing_zone, "network") and existing_zone.network:
                        # Update based on the network configuration type
                        pass  # Complex network configuration update would go here
                    else:
                        # If no network config exists, we might need to create one
                        self.logger.warning(f"Zone '{name}' exists but interface update may require network configuration")

                # Perform update
                result = self.client.security_zone.update(existing_zone)
                self.logger.info(f"Successfully updated security zone '{name}'")
            else:
                # Create the new zone - for new zones we need to include the mode in the network config
                # The actual structure depends on the mode type
                if mode:
                    # Initialize network configuration based on mode
                    # This is simplified - actual implementation would need proper network config
                    zone_data["network"] = {mode.lower().replace("-", "_"): interfaces or []}

                result = self.client.security_zone.create(zone_data)
                self.logger.info(f"Successfully created security zone '{name}'")

            # Convert SDK response to dict for compatibility
            return result.dict()
        except Exception as e:
            self._handle_api_exception("creation/update", folder, name, e)

    def delete_zone(
        self,
        folder: str,
        name: str,
    ) -> bool:
        """Delete a security zone.

        Args:
            folder: Folder containing the zone
            name: Name of the zone to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting zone: {name} from folder {folder}")

        if not self.client:
            # Return a mock result if no client is available
            return True

        try:
            # First, fetch the security zone to get its ID
            zone = self.client.security_zone.fetch(name=name, folder=folder)
            self.client.security_zone.delete(str(zone.id))
            self.logger.info(f"Successfully deleted security zone '{name}'")
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder, name, e)

    def get_security_zone(
        self,
        folder: str,
        name: str,
    ) -> dict[str, Any]:
        """Get a security zone by name and folder.

        Args:
            folder: Folder containing the security zone
            name: Name of the security zone to get

        Returns:
            dict[str, Any]: The security zone object

        """
        self.logger.info(f"Getting security zone: {name} from folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"zone-{name}",
                "folder": folder,
                "name": name,
                "network": {
                    "layer3": ["ethernet1/1", "ethernet1/2"],
                    "zone_protection_profile": "default",
                    "enable_packet_buffer_protection": True,
                },
                "enable_user_identification": True,
                "enable_device_identification": False,
                "description": "Mock security zone",
            }

        try:
            # Fetch the security zone using the SDK
            result = self.client.security_zone.fetch(name=name, folder=folder)

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieval", folder, name, e)

    def list_security_zones(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List security zones from SCM.

        Args:
            folder: The folder containing the zone
            snippet: The snippet containing the zone
            device: The device containing the zone
            exact_match: If True, only return exact name matches

        Returns:
            List of security zone dictionaries

        Raises:
            APIException: On API errors

        """
        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
            container = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
            container = snippet
        elif device:
            container_kwargs["device"] = device
            container = device
        else:
            container = "Unknown"

        self.logger.info(f"Listing security zones in container: {container} (exact_match={exact_match})")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "zone-mock1",
                    "folder": folder or "Texas",
                    "name": "trust",
                    "network": {
                        "layer3": ["ethernet1/1", "ethernet1/2"],
                        "zone_protection_profile": "default",
                    },
                    "enable_user_identification": True,
                    "description": "Trust zone for internal network",
                },
                {
                    "id": "zone-mock2",
                    "folder": folder or "Texas",
                    "name": "untrust",
                    "network": {
                        "layer3": ["ethernet1/3"],
                        "zone_protection_profile": "strict",
                    },
                    "enable_user_identification": False,
                    "description": "Untrust zone for external network",
                },
                {
                    "id": "zone-mock3",
                    "folder": folder or "Texas",
                    "name": "dmz",
                    "network": {
                        "layer3": ["ethernet1/4", "ethernet1/5"],
                        "enable_packet_buffer_protection": True,
                    },
                    "enable_device_identification": True,
                    "description": "DMZ zone for public services",
                },
            ]

        try:
            # Check if the snippet or device is supported
            if snippet or device:
                raise NotImplementedError(f"Listing security zones by {'snippet' if snippet else 'device'} is not yet supported by the SDK")

            # List security zones using the SDK
            results = self.client.security_zone.list(**container_kwargs, exact_match=exact_match)

            # Convert SDK response to show a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container, "security zones", e)

    # ======================================================================================================================================================================================
    # SECURITY CONFIGURATION METHODS
    # ======================================================================================================================================================================================

    # ------------------------------------------------------------------------------------ Security Rules ----------------------------------------------------------------------------------

    def create_security_rule(
        self,
        folder: str,
        name: str,
        source_zones: list[str],
        destination_zones: list[str],
        source_addresses: list[str] | None = None,
        destination_addresses: list[str] | None = None,
        applications: list[str] | None = None,
        services: list[str] | None = None,
        action: str = "allow",
        description: str = "",
        tags: list[str] | None = None,
        enabled: bool = True,
        rulebase: str = "pre",
        log_start: bool = False,
        log_end: bool = False,
        log_setting: str | None = None,
    ) -> dict[str, Any]:
        """Create a security rule.

        Args:
            folder: Folder to create the rule in
            name: Name of the rule
            source_zones: List of source zones
            destination_zones: List of destination zones
            source_addresses: List of source addresses
            destination_addresses: List of destination addresses
            applications: List of applications
            services: List of services
            action: Action (allow, deny, drop)
            description: Optional description
            tags: Optional list of tags
            enabled: Whether the rule is enabled (default True)
            rulebase: Rulebase to use (pre, post, or default)
            log_start: Log at session start
            log_end: Log at session end
            log_setting: log-forwarding profile name

        Returns:
            dict[str, Any]: The created security rule object

        Note:
            If a security rule with the same name already exists in the folder and rulebase,
            it will be updated with the new configuration.

        """
        source_addresses = source_addresses or ["any"]
        destination_addresses = destination_addresses or ["any"]
        applications = applications or ["any"]
        services = services or ["any"]
        tags = tags or []
        self.logger.info(f"Creating or updating security rule: {name} with action {action} in folder {folder}, rulebase {rulebase}")

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
                "services": services,
                "action": action,
                "description": description,
                "tags": tags,
                "enabled": enabled,
                "rulebase": rulebase,
                "log_start": log_start,
                "log_end": log_end,
                "log_setting": log_setting,
            }

        try:
            # First, try to fetch the existing security rule
            existing_rule = None
            try:
                existing_rule = self.client.security_rule.fetch(name=name, folder=folder, rulebase=rulebase)
                self.logger.info(f"Found existing security rule '{name}' in folder '{folder}', rulebase '{rulebase}', updating...")
            except NotFoundError:
                self.logger.info(f"Security rule '{name}' not found in folder '{folder}', rulebase '{rulebase}', creating new...")
            except Exception as fetch_error:
                # Log but continue - we'll try to create if fetch failed for other reasons
                self.logger.warning(f"Error fetching security rule '{name}': {str(fetch_error)}")

            # Prepare rule data - SDK uses different field names (from_, to_, etc.)
            rule_data = {
                "name": name,
                "folder": folder,
                "from_": source_zones,  # SDK uses from_ instead of source_zones
                "to_": destination_zones,  # SDK uses to_ instead of destination_zones
                "source": source_addresses,  # SDK uses `source` for the source instead of source_addresses
                "destination": destination_addresses,  # SDK uses destination instead of destination_addresses
                "application": applications,  # SDK uses application instead of applications
                "service": services,  # Use provided services or default to any
                "action": action,
                "description": description or "",
                "disabled": not enabled,  # SDK uses disabled instead of enabled
                "category": ["any"],  # Required by SDK
                "source_user": ["any"],  # Required by SDK
            }

            if tags:
                rule_data["tag"] = tags  # SDK expects 'tag', not 'tags'

            # Add logging settings if specified
            if log_start:
                rule_data["log_start"] = True
            if log_end:
                rule_data["log_end"] = True
            if log_setting:
                rule_data["log_setting"] = log_setting

            # If the rule exists, update it
            if existing_rule:
                # Update only the fields that are changing
                existing_rule.from_ = source_zones
                existing_rule.to_ = destination_zones
                existing_rule.source = source_addresses
                existing_rule.destination = destination_addresses
                existing_rule.application = applications
                existing_rule.service = services
                existing_rule.action = action
                existing_rule.description = description or ""
                existing_rule.disabled = not enabled
                existing_rule.category = ["any"]  # Required by SDK
                existing_rule.source_user = ["any"]  # Required by SDK

                if tags is not None:
                    existing_rule.tag = tags

                # Update logging settings
                existing_rule.log_start = log_start
                existing_rule.log_end = log_end
                if log_setting:
                    existing_rule.log_setting = log_setting
                else:
                    # Clear log_setting if not specified
                    existing_rule.log_setting = None

                # Perform update
                result = self.client.security_rule.update(existing_rule)
                self.logger.info(f"Successfully updated security rule '{name}'")
            else:
                # Create a new rule - need to pass rulebase for creation
                result = self.client.security_rule.create(data=rule_data, rulebase=rulebase)
                self.logger.info(f"Successfully created security rule '{name}'")

            # Convert SDK response to dict for compatibility
            return result.dict()
        except Exception as e:
            self._handle_api_exception("creation/update", folder, name, e)

    def delete_security_rule(
        self,
        folder: str,
        name: str,
        rulebase: str = "pre",
    ) -> bool:
        """Delete a security rule.

        Args:
            folder: Folder containing the security rule
            name: Name of the security rule to delete
            rulebase: Rulebase containing the rule (pre, post, or default)

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting security rule: {name} from folder {folder}, rulebase {rulebase}")

        if not self.client:
            # Return a mock result if no client is available
            return True

        try:
            # First, fetch the rule to get its ID
            rule = self.client.security_rule.fetch(name=name, folder=folder, rulebase=rulebase)

            # Delete using the rule's ID
            self.client.security_rule.delete(str(rule.id))
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder, name, e)

    def get_security_rule(
        self,
        folder: str,
        name: str,
        rulebase: str = "pre",
    ) -> dict[str, Any]:
        """Get a security rule by name and folder.

        Args:
            folder: Folder containing the security rule
            name: Name of the security rule to get
            rulebase: Rulebase to use (pre, post, or default)

        Returns:
            dict[str, Any]: The security rule object

        """
        self.logger.info(f"Getting security rule: {name} from folder {folder} in rulebase {rulebase}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"sr-{name}",
                "folder": folder,
                "name": name,
                "from_": ["trust"],
                "to_": ["untrust"],
                "source": ["any"],
                "destination": ["any"],
                "application": ["web-browsing", "ssl"],
                "service": ["application-default"],
                "action": "allow",
                "description": "Mock security rule",
                "tag": ["mock"],
                "disabled": False,
                "log_end": True,
            }

        try:
            # Fetch the security rule using the SDK
            result = self.client.security_rule.fetch(name=name, folder=folder, rulebase=rulebase)

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieval", folder, name, e)

    def list_security_rules(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        rulebase: str = "pre",
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List security rules from SCM.

        Args:
            folder: The folder containing the rule
            snippet: The snippet containing the rule
            device: The device containing the rules
            rulebase: Rulebase to use (pre, post, or default)
            exact_match: If True, only return exact name matches

        Returns:
            List of security rule dictionaries

        Raises:
            APIException: On API errors

        """
        # Determine container
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
            container = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
            container = snippet
        elif device:
            container_kwargs["device"] = device
            container = device
        else:
            container = "Unknown"

        self.logger.info(f"Listing security rules in container: {container}, rulebase: {rulebase} (exact_match={exact_match})")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "sr-mock1",
                    "folder": folder or "Texas",
                    "name": "Allow Web Traffic",
                    "from_": ["trust"],
                    "to_": ["untrust"],
                    "source": ["internal-net"],
                    "destination": ["any"],
                    "application": ["web-browsing", "ssl"],
                    "service": ["application-default"],
                    "action": "allow",
                    "description": "Allow web browsing from internal network",
                    "tag": ["mock", "web"],
                    "disabled": False,
                    "log_end": True,
                },
                {
                    "id": "sr-mock2",
                    "folder": folder or "Texas",
                    "name": "Block Malicious IPs",
                    "from_": ["any"],
                    "to_": ["any"],
                    "source": ["malicious-ip-list"],
                    "destination": ["any"],
                    "application": ["any"],
                    "service": ["any"],
                    "action": "deny",
                    "description": "Block known malicious IP addresses",
                    "tag": ["mock", "security"],
                    "disabled": False,
                    "log_start": True,
                    "log_end": True,
                },
            ]

        try:
            # Check if a snippet or device is supported
            if snippet or device:
                raise NotImplementedError(f"Listing security rules by {'snippet' if snippet else 'device'} is not yet supported by the SDK")

            # List security rules using the SDK
            results = self.client.security_rule.list(**container_kwargs, rulebase=rulebase, exact_match=exact_match)

            # Convert SDK response to a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container, "security rules", e)

    # ---------------------------------------------------------------------------------- Anti-Spyware Profiles ---------------------------------------------------------------------------------

    def create_anti_spyware_profile(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
        description: str | None = None,
        threat_exceptions: list[dict[str, Any]] | None = None,
        rules: list[dict[str, Any]] | None = None,
        mica_engine_spyware_enabled: list[dict[str, Any]] | None = None,
        cloud_inline_analysis: bool | None = None,
    ) -> dict[str, Any]:
        """Create an anti-spyware profile.

        Args:
            folder: Folder to create the profile in
            snippet: Snippet to create the profile in
            device: Device to create the profile in
            name: Name of the profile
            description: Optional description
            threat_exceptions: List of threat exceptions
            rules: List of anti-spyware rules
            mica_engine_spyware_enabled: MICA engine settings
            cloud_inline_analysis: Enable cloud inline analysis

        Returns:
            dict[str, Any]: The created anti-spyware profile object

        Note:
            If an anti-spyware profile with the same name already exists in the container,
            it will be updated with the new configuration.

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")
        self.logger.info(f"Creating or updating anti-spyware profile: {name} in {container_type} {container}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"asp-{name}",
                "folder": folder,
                "snippet": snippet,
                "device": device,
                "name": name,
                "description": description,
                "threat_exception": threat_exceptions or [],
                "rules": rules or [],
                "mica_engine_spyware_enabled": mica_engine_spyware_enabled,
                "cloud_inline_analysis": cloud_inline_analysis,
            }

        try:
            # First, try to fetch the existing anti-spyware profile
            existing_profile = None
            try:
                existing_profile = self.client.anti_spyware_profile.fetch(name=name, folder=folder, snippet=snippet, device=device)
                self.logger.info(f"Found existing anti-spyware profile '{name}' in {container_type} '{container}', updating...")
            except NotFoundError:
                self.logger.info(f"Anti-spyware profile '{name}' not found in {container_type} '{container}', creating new...")
            except Exception as fetch_error:
                # Log but continue - we'll try to create if fetch failed for other reasons
                self.logger.warning(f"Error fetching anti-spyware profile '{name}': {str(fetch_error)}")

            # Prepare profile data
            profile_data = {
                "name": name,
            }

            # Add container field only if not None
            if folder is not None:
                profile_data["folder"] = folder
            if snippet is not None:
                profile_data["snippet"] = snippet
            if device is not None:
                profile_data["device"] = device

            # Add optional fields if provided
            if description is not None:
                profile_data["description"] = description
            if threat_exceptions is not None:
                profile_data["threat_exception"] = threat_exceptions
            if rules is not None:
                profile_data["rules"] = rules
            if mica_engine_spyware_enabled is not None:
                profile_data["mica_engine_spyware_enabled"] = mica_engine_spyware_enabled
            if cloud_inline_analysis is not None:
                profile_data["cloud_inline_analysis"] = cloud_inline_analysis

            # Create or update the profile
            if existing_profile:
                # Update existing profile
                profile_data["id"] = existing_profile.id
                from scm.models.security import AntiSpywareProfileUpdateModel

                update_model = AntiSpywareProfileUpdateModel(**profile_data)
                result = self.client.anti_spyware_profile.update(update_model)
            else:
                # Create a new profile
                result = self.client.anti_spyware_profile.create(profile_data)

            # Convert response to dict
            return json.loads(result.model_dump_json(exclude_unset=True))

        except Exception as e:
            self._handle_api_exception("creating", container or "", "anti-spyware profile", e)

    def delete_anti_spyware_profile(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
    ) -> bool:
        """Delete an anti-spyware profile.

        Args:
            folder: Folder containing the profile
            snippet: Snippet containing the profile
            device: Device containing the profile
            name: Name of the profile to delete

        Returns:
            bool: True if deleted successfully

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")
        self.logger.info(f"Deleting anti-spyware profile: {name} from {container_type} {container}")

        if not self.client:
            # Return mock success if no client is available
            return True

        try:
            # Fetch the profile to get its ID
            profile = self.client.anti_spyware_profile.fetch(name=name, folder=folder, snippet=snippet, device=device)

            # Delete using the ID
            self.client.anti_spyware_profile.delete(profile.id)
            self.logger.info(f"Successfully deleted anti-spyware profile '{name}' from {container_type} '{container}'")
            return True
        except NotFoundError:
            self.logger.warning(f"Anti-spyware profile '{name}' not found in {container_type} '{container}'")
            return False
        except Exception as e:
            self._handle_api_exception("deleting", container or "", "anti-spyware profile", e)

    def get_anti_spyware_profile(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
    ) -> dict[str, Any]:
        """Get an anti-spyware profile by name.

        Args:
            folder: Folder containing the profile
            snippet: Snippet containing the profile
            device: Device containing the profile
            name: Name of the profile

        Returns:
            dict[str, Any]: The anti-spyware profile object

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")
        self.logger.info(f"Getting anti-spyware profile: {name} from {container_type} {container}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"asp-{name}",
                "folder": folder,
                "snippet": snippet,
                "device": device,
                "name": name,
                "description": "Mock anti-spyware profile",
                "rules": [
                    {
                        "name": "Block Critical Threats",
                        "severity": ["critical", "high"],
                        "action": "block",
                        "packet_capture": "single-packet",
                    }
                ],
                "cloud_inline_analysis": True,
            }

        try:
            # Fetch the profile using the SDK
            result = self.client.anti_spyware_profile.fetch(name=name, folder=folder, snippet=snippet, device=device)

            # Convert SDK response to dict
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("getting", container or "", "anti-spyware profile", e)

    def list_anti_spyware_profiles(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List anti-spyware profiles.

        Args:
            folder: Folder to list out
            snippet: Snippet to list out
            device: Device to list out
            exact_match: If True, only return exact container matches

        Returns:
            list[dict[str, Any]]: List of anti-spyware profile objects

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        # Build container kwargs
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        self.logger.info(f"Listing anti-spyware profiles in {container_type}: {container}")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "asp-mock1",
                    "folder": folder or "Texas",
                    "name": "Strict Security",
                    "description": "Block all critical and high severity threats",
                    "rules": [
                        {
                            "name": "Block Critical",
                            "severity": ["critical", "high"],
                            "action": "block",
                        }
                    ],
                    "cloud_inline_analysis": True,
                },
                {
                    "id": "asp-mock2",
                    "folder": folder or "Texas",
                    "name": "Standard Protection",
                    "description": "Standard anti-spyware protection",
                    "rules": [
                        {
                            "name": "Alert Medium",
                            "severity": ["medium"],
                            "action": "alert",
                        }
                    ],
                },
            ]

        try:
            # List profiles using the SDK
            results = self.client.anti_spyware_profile.list(**container_kwargs, exact_match=exact_match)

            # Convert SDK response to a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container or "", "anti-spyware profiles", e)

    # ------------------------------------------------------------------------------------ Decryption Profile ----------------------------------------------------------------------------------

    def create_decryption_profile(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        **profile_data,
    ) -> dict[str, Any]:
        """Create or update a decryption profile.

        Args:
            folder: Folder to create the profile in
            snippet: Snippet to create the profile in
            device: Device to create the profile in
            **profile_data: Additional profile configuration data

        Returns:
            dict[str, Any]: Created/updated a decryption profile object

        """
        name = profile_data.get("name")
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Creating/updating decryption profile: {name} in {container_type} {container}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"dec-{name}",
                "name": name,
                container_type: container,
                "ssl_forward_proxy": profile_data.get("ssl_forward_proxy", {}),
                "ssl_inbound_proxy": profile_data.get("ssl_inbound_proxy", {}),
                "ssl_no_proxy": profile_data.get("ssl_no_proxy", {}),
                "ssl_protocol_settings": profile_data.get("ssl_protocol_settings", {}),
            }

        try:
            # Check if the profile already exists
            existing_profile = None
            try:
                if folder:
                    existing_profile = self.client.decryption_profile.fetch(name=name, folder=folder)
                elif snippet:
                    existing_profile = self.client.decryption_profile.fetch(name=name, snippet=snippet)
                elif device:
                    existing_profile = self.client.decryption_profile.fetch(name=name, device=device)
            except NotFoundError:
                self.logger.info(f"Decryption profile '{name}' not found. Creating new profile.")

            if existing_profile:
                # Update existing profile
                self.logger.info(f"Decryption profile '{name}' exists. Updating.")

                # Update with new data
                for key, value in profile_data.items():
                    if value is not None and hasattr(existing_profile, key):
                        setattr(existing_profile, key, value)

                # Update the profile
                result = self.client.decryption_profile.update(existing_profile)
                self.logger.info(f"Successfully updated decryption profile '{name}'")
            else:
                # Create a new profile
                profile_dict = {container_type: container}
                profile_dict.update(profile_data)

                result = self.client.decryption_profile.create(profile_dict)
                self.logger.info(f"Successfully created decryption profile '{name}'")

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("creation/update", container or "", name or "", e)

    def delete_decryption_profile(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
    ) -> bool:
        """Delete a decryption profile.

        Args:
            folder: Folder containing the profile
            snippet: Snippet containing the profile
            device: Device containing the profile
            name: Name of the profile to delete

        Returns:
            bool: True if deletion was successful

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Deleting decryption profile: {name} from {container_type} {container}")

        if not self.client:
            # Return a mock result if no client is available
            return True

        try:
            # Get the profile first to get its ID
            profile = None
            if folder:
                profile = self.client.decryption_profile.fetch(name=name, folder=folder)
            elif snippet:
                profile = self.client.decryption_profile.fetch(name=name, snippet=snippet)
            elif device:
                profile = self.client.decryption_profile.fetch(name=name, device=device)

            # Delete using the ID
            if profile is None:
                raise ValueError(f"Decryption profile '{name}' not found")
            self.client.decryption_profile.delete(str(profile.id))
            return True
        except Exception as e:
            self._handle_api_exception("deletion", container or "", name or "", e)

    def get_decryption_profile(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
    ) -> dict[str, Any]:
        """Get a decryption profile by name.

        Args:
            folder: Folder containing the profile
            snippet: Snippet containing the profile
            device: Device containing the profile
            name: Name of the profile to get

        Returns:
            dict[str, Any]: The decryption profile object

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Getting decryption profile: {name} from {container_type} {container}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"dec-{name}",
                container_type: container,
                "name": name,
                "ssl_forward_proxy": {
                    "auto_include_altname": False,
                    "block_client_cert": False,
                    "block_expired_certificate": True,
                    "block_unknown_cert": True,
                    "block_untrusted_issuer": True,
                },
                "ssl_protocol_settings": {
                    "min_version": "tls1-0",
                    "max_version": "tls1-3",
                },
            }

        try:
            # Fetch the profile using the SDK
            result = None
            if folder:
                result = self.client.decryption_profile.fetch(name=name, folder=folder)
            elif snippet:
                result = self.client.decryption_profile.fetch(name=name, snippet=snippet)
            elif device:
                result = self.client.decryption_profile.fetch(name=name, device=device)

            # Convert SDK response to dict for compatibility
            if result is not None:
                return json.loads(result.model_dump_json(exclude_unset=True))
            else:
                raise ValueError(f"Decryption profile '{name}' not found")
        except Exception as e:
            self._handle_api_exception("getting", container or "", "decryption profile", e)

    def list_decryption_profiles(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List decryption profiles.

        Args:
            folder: Folder to a list from
            snippet: Snippet to a list from
            device: Device to a list from
            exact_match: If True, only return exact container matches

        Returns:
            list[dict[str, Any]]: List of decryption profile objects

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        # Build container kwargs
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        self.logger.info(f"Listing decryption profiles in {container_type}: {container}")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "dec-mock1",
                    "folder": folder or "Texas",
                    "name": "SSL Forward Proxy",
                    "ssl_forward_proxy": {
                        "auto_include_altname": True,
                        "block_expired_certificate": True,
                        "block_untrusted_issuer": True,
                    },
                    "ssl_protocol_settings": {
                        "min_version": "tls1-0",
                        "max_version": "tls1-3",
                    },
                },
                {
                    "id": "dec-mock2",
                    "folder": folder or "Texas",
                    "name": "SSL Inbound Inspection",
                    "ssl_inbound_proxy": {
                        "block_if_no_resource": True,
                        "block_unsupported_cipher": True,
                        "block_unsupported_version": True,
                    },
                },
            ]

        try:
            # List profiles using the SDK
            results = self.client.decryption_profile.list(**container_kwargs, exact_match=exact_match)

            # Convert SDK response to a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container or "", "decryption profiles", e)

    # ======================================================================================================================================================================================
    # INSIGHTS AND MONITORING METHODS
    # ======================================================================================================================================================================================

    # ------------------------------------------------------------------------------------ Alerts ----------------------------------------------------------------------------------

    def list_alerts(self, folder: str = None, max_results: int = 100, **filters) -> list[dict[str, Any]]:
        """List alerts from insights API.

        Args:
            folder: Folder to filter alerts (optional)
            max_results: Maximum number of results to return after sorting
            **filters: Additional filters (severity, start_time, end_time, etc.)

        Returns:
            List of alert dictionaries sorted by timestamp (newest first)

        """
        logger.info(f"Listing alerts (will return up to {max_results} after sorting)")
        
        # Always fetch more alerts than requested to ensure we get the most recent ones
        # The API might return alerts in arbitrary order, so we need to fetch enough
        # to ensure we capture recent alerts before sorting
        api_fetch_limit = max(200, max_results * 5)  # Fetch at least 200 or 5x requested

        if self.mock:
            # Return mock data for alerts
            return [
                {
                    "id": "alert-001",
                    "name": "Critical CPU Usage",
                    "severity": "critical",
                    "status": "active",
                    "timestamp": "2024-01-20T10:30:00Z",
                    "description": "CPU usage exceeded 95% threshold",
                    "folder": folder or "Texas",
                    "source": "system-monitor",
                    "category": "performance",
                    "impacted_resources": ["fw-01", "fw-02"],
                    "metadata": {"cpu_percent": 97.5},
                },
                {
                    "id": "alert-002",
                    "name": "Tunnel Down",
                    "severity": "high",
                    "status": "active",
                    "timestamp": "2024-01-20T09:15:00Z",
                    "description": "IPSec tunnel to remote site is down",
                    "folder": folder or "Texas",
                    "source": "tunnel-monitor",
                    "category": "connectivity",
                    "impacted_resources": ["tunnel-remote-01"],
                    "metadata": {"site": "Branch Office 1"},
                },
            ]

        try:
            # Check if the SDK has the alerts service
            if not hasattr(self.client, "alerts"):
                raise NotImplementedError("Alerts service not yet available in current pan-scm-sdk version")

            # Try using the SDK's list method with proper parameters
            try:
                # Convert string severity to list if needed
                severity_list = None
                if filters.get("severity"):
                    severity_list = filters["severity"].split(",") if isinstance(filters["severity"], str) else filters["severity"]

                status_list = None
                if filters.get("status"):
                    status_list = filters["status"].split(",") if isinstance(filters["status"], str) else filters["status"]

                # Convert ISO timestamp to Unix timestamp if provided
                start_timestamp = None
                if filters.get("start_time"):
                    try:
                        # If it's already a digit string, use it as-is
                        if filters["start_time"].isdigit():
                            start_timestamp = int(filters["start_time"])
                        else:
                            # Parse ISO format and convert to Unix timestamp
                            from datetime import datetime

                            dt = datetime.fromisoformat(filters["start_time"].replace("Z", "+00:00"))
                            start_timestamp = int(dt.timestamp())
                            self.logger.debug(f"Converted start_time {filters['start_time']} to timestamp {start_timestamp}")
                    except Exception as e:
                        self.logger.warning(f"Failed to parse start_time {filters['start_time']}: {e}")
                        pass

                # Try using list method - fetch more than requested for proper sorting
                result = self.client.alerts.list(
                    severity=severity_list,
                    status=status_list,
                    start_time=start_timestamp,
                    category=filters.get("category"),
                    max_results=api_fetch_limit,
                )

                # Process each alert
                alerts = []
                for alert_obj in result:
                    # Convert to dict - handle both dict and object responses
                    alert_data = alert_obj.model_dump() if hasattr(alert_obj, "model_dump") else alert_obj if isinstance(alert_obj, dict) else vars(alert_obj)

                    # Map fields to our expected format
                    alert = {
                        "id": alert_data.get("id") or alert_data.get("alert_id"),
                        "name": alert_data.get("name") or alert_data.get("message"),
                        "severity": alert_data.get("severity"),
                        "status": alert_data.get("status") or alert_data.get("state"),
                        "timestamp": alert_data.get("timestamp") or alert_data.get("raised_time"),
                        "description": alert_data.get("description"),
                        "folder": alert_data.get("folder"),
                        "source": alert_data.get("source"),
                        "category": alert_data.get("category"),
                        "impacted_resources": alert_data.get("impacted_resources") or alert_data.get("primary_impacted_objects", []),
                        "metadata": alert_data.get("metadata") or alert_data.get("resource_context"),
                    }
                    
                    # Remove empty fields for cleaner output
                    alert = self._remove_empty_fields(alert)

                    # Client-side time filtering if API doesn't support it
                    if filters.get("start_time") and alert.get("timestamp"):
                        try:
                            # Parse alert timestamp
                            alert_time = datetime.fromisoformat(alert["timestamp"].replace("Z", "+00:00"))
                            start_time = datetime.fromisoformat(filters["start_time"].replace("Z", "+00:00"))

                            # Skip alerts older than start_time
                            if alert_time < start_time:
                                self.logger.debug(f"Filtering out alert from {alert['timestamp']} (before {filters['start_time']})")
                                continue
                        except Exception as e:
                            self.logger.debug(f"Failed to filter by time: {e}")
                            pass

                    alerts.append(alert)

                # Sort alerts by timestamp (newest first)
                alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                
                # Limit to the requested number of results
                return alerts[:max_results]

            except Exception as list_error:
                # If list method fails, fall back to query method
                self.logger.debug(f"List method failed: {list_error}, trying query method")

                # Build properties for query
                properties = [
                    {"property": "alert_id"},
                    {"property": "severity"},
                    {"property": "message"},
                    {"property": "raised_time"},
                    {"property": "updated_time"},
                    {"property": "state"},
                    {"property": "category"},
                ]

                # Build filter for recent alerts (last 30 days by default)
                filter_rules = []

                # Add time filter
                days_back = 30  # default
                if filters.get("start_time") and filters["start_time"].isdigit():
                    days_back = int(filters["start_time"])
                filter_rules.append({"property": "updated_time", "operator": "last_n_days", "values": [days_back]})

                # Add severity filter if provided
                if filters.get("severity"):
                    severity_list = filters["severity"].split(",") if isinstance(filters["severity"], str) else filters["severity"]
                    filter_rules.append({"property": "severity", "operator": "in", "values": severity_list})

                # Add status filter if provided
                if filters.get("status"):
                    status_list = filters["status"].split(",") if isinstance(filters["status"], str) else filters["status"]
                    filter_rules.append({"property": "state", "operator": "in", "values": status_list})

                # Simple query with basic filters - fetch more for proper sorting
                response = self.client.alerts.query(properties=properties, filter={"rules": filter_rules}, count=api_fetch_limit)

                # Process raw response - response.data is a list of dicts
                alerts = []
                if hasattr(response, "data") and response.data:
                    for item in response.data:
                        # Handle timestamp conversion
                        timestamp = item.get("raised_time")
                        if isinstance(timestamp, int):
                            # Convert milliseconds to ISO format
                            timestamp = datetime.fromtimestamp(timestamp / 1000).isoformat() + "Z"

                        alert = {
                            "id": item.get("alert_id", ""),
                            "name": item.get("message", ""),
                            "severity": item.get("severity", ""),
                            "status": item.get("state", ""),
                            "timestamp": timestamp,
                            "category": item.get("category", ""),
                            "impacted_resources": [],
                            "metadata": {},
                        }
                        # Remove empty fields for cleaner output
                        alert = self._remove_empty_fields(alert)
                        alerts.append(alert)

                # Sort alerts by timestamp (newest first) and limit results
                alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                return alerts[:max_results]
        except NotImplementedError:
            raise
        except Exception as e:
            self._handle_api_exception("listing", folder or "insights", "alerts", e)

    def get_alert(self, alert_id: str, folder: str = None) -> dict[str, Any]:
        """Get a specific alert by ID.

        Args:
            alert_id: Alert ID
            folder: Folder containing the alert (optional)

        Returns:
            Alert dictionary

        """
        logger.info(f"Getting alert {alert_id}")

        if self.mock:
            return {
                "id": alert_id,
                "name": "Critical CPU Usage",
                "severity": "critical",
                "status": "active",
                "timestamp": "2024-01-20T10:30:00Z",
                "description": "CPU usage exceeded 95% threshold",
                "folder": folder or "Texas",
                "source": "system-monitor",
                "category": "performance",
                "impacted_resources": ["fw-01", "fw-02"],
                "metadata": {"cpu_percent": 97.5},
            }

        try:
            # Check if the SDK has the alerts service
            if not hasattr(self.client, "alerts"):
                raise NotImplementedError("Alerts service not yet available in current pan-scm-sdk version")

            # Use query method to get specific alert
            properties = [
                {"property": "alert_id"},
                {"property": "severity"},
                {"property": "message"},
                {"property": "raised_time"},
                {"property": "updated_time"},
                {"property": "state"},
                {"property": "category"},
                {"property": "code"},
                {"property": "primary_impacted_objects", "function": "to_json_string"},
                {"property": "resource_context", "function": "to_json_string"},
            ]

            response = self.client.alerts.query(properties=properties, filter={"rules": [{"property": "alert_id", "operator": "equals", "values": [alert_id]}]}, count=1)

            # Check if we got a result
            if not hasattr(response, "data") or not response.data:
                raise ValueError(f"Alert with ID '{alert_id}' not found")

            # Process the first (and only) result
            item = response.data[0]

            # Handle timestamp conversion
            timestamp = item.get("raised_time")
            if isinstance(timestamp, int):
                timestamp = datetime.fromtimestamp(timestamp / 1000).isoformat() + "Z"

            # Parse JSON string fields
            primary_impacted = item.get("primary_impacted_objects")
            if isinstance(primary_impacted, str):
                with contextlib.suppress(json.JSONDecodeError, TypeError):
                    primary_impacted = json.loads(primary_impacted)

            resource_context = item.get("resource_context")
            if isinstance(resource_context, str):
                with contextlib.suppress(json.JSONDecodeError, TypeError):
                    resource_context = json.loads(resource_context)

            # Return formatted alert
            return {
                "id": item.get("alert_id", ""),
                "name": item.get("message", ""),
                "severity": item.get("severity", ""),
                "status": item.get("state", ""),
                "timestamp": timestamp,
                "category": item.get("category", ""),
                "code": item.get("code", ""),
                "impacted_resources": self._extract_impacted_resources(primary_impacted),
                "metadata": resource_context,
            }
        except NotImplementedError:
            raise
        except Exception as e:
            self._handle_api_exception("retrieval", folder or "insights", f"alert {alert_id}", e)

    # ------------------------------------------------------------------------------------ Mobile Users ----------------------------------------------------------------------------------

    def list_mobile_users(self, folder: str = None, max_results: int = 100, **filters) -> list[dict[str, Any]]:
        """List mobile users from insights API.

        Args:
            folder: Folder to filter users (optional)
            max_results: Maximum number of results to return
            **filters: Additional filters (status, location, etc.)

        Returns:
            List of mobile user dictionaries

        """
        logger.info("Listing mobile users")

        if self.mock:
            return [
                {
                    "id": "user-001",
                    "username": "jsmith@company.com",
                    "device_id": "device-abc123",
                    "status": "connected",
                    "location": "New York, NY",
                    "last_seen": "2024-01-20T11:00:00Z",
                    "ip_address": "10.0.1.45",
                    "folder": folder or "Mobile Users",
                    "gateway": "gw-nyc-01",
                    "bandwidth_used": 25,
                    "session_duration": 3600,
                    "metadata": {"os": "Windows 11", "client_version": "6.2.1"},
                },
                {
                    "id": "user-002",
                    "username": "mjones@company.com",
                    "device_id": "device-xyz789",
                    "status": "disconnected",
                    "location": "San Francisco, CA",
                    "last_seen": "2024-01-20T09:30:00Z",
                    "ip_address": "10.0.2.67",
                    "folder": folder or "Mobile Users",
                    "gateway": "gw-sfo-01",
                    "bandwidth_used": 0,
                    "session_duration": 0,
                    "metadata": {"os": "macOS 14", "client_version": "6.2.0"},
                },
            ]

        # TODO: Implement actual API call when insights API is available
        raise NotImplementedError("Insights API not yet available in pan-scm-sdk")

    def get_mobile_user(self, user_id: str, folder: str = None) -> dict[str, Any]:
        """Get a specific mobile user by ID.

        Args:
            user_id: User ID
            folder: Folder containing the user (optional)

        Returns:
            Mobile user dictionary

        """
        logger.info(f"Getting mobile user {user_id}")

        if self.mock:
            return {
                "id": user_id,
                "username": "jsmith@company.com",
                "device_id": "device-abc123",
                "status": "connected",
                "location": "New York, NY",
                "last_seen": "2024-01-20T11:00:00Z",
                "ip_address": "10.0.1.45",
                "folder": folder or "Mobile Users",
                "gateway": "gw-nyc-01",
                "bandwidth_used": 25,
                "session_duration": 3600,
                "metadata": {"os": "Windows 11", "client_version": "6.2.1"},
            }

        # TODO: Implement actual API call when insights API is available
        raise NotImplementedError("Insights API not yet available in pan-scm-sdk")

    # ------------------------------------------------------------------------------------ Locations ----------------------------------------------------------------------------------

    def list_locations(self, folder: str = None, max_results: int = 100, **filters) -> list[dict[str, Any]]:
        """List locations from insights API.

        Args:
            folder: Folder to filter locations (optional)
            max_results: Maximum number of results to return
            **filters: Additional filters (region, etc.)

        Returns:
            List of location dictionaries

        """
        logger.info("Listing locations")

        if self.mock:
            return [
                {
                    "id": "loc-001",
                    "name": "New York Office",
                    "region": "us-east",
                    "country": "United States",
                    "state": "New York",
                    "city": "New York",
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "folder": folder or "Locations",
                    "total_users": 150,
                    "active_users": 87,
                    "bandwidth_capacity": 1000,
                    "bandwidth_used": 450,
                    "metadata": {"site_code": "NYC01", "timezone": "America/New_York"},
                },
                {
                    "id": "loc-002",
                    "name": "San Francisco Office",
                    "region": "us-west",
                    "country": "United States",
                    "state": "California",
                    "city": "San Francisco",
                    "latitude": 37.7749,
                    "longitude": -122.4194,
                    "folder": folder or "Locations",
                    "total_users": 200,
                    "active_users": 145,
                    "bandwidth_capacity": 2000,
                    "bandwidth_used": 1200,
                    "metadata": {"site_code": "SFO01", "timezone": "America/Los_Angeles"},
                },
            ]

        # TODO: Implement actual API call when insights API is available
        raise NotImplementedError("Insights API not yet available in pan-scm-sdk")

    def get_location(self, location_id: str, folder: str = None) -> dict[str, Any]:
        """Get a specific location by ID.

        Args:
            location_id: Location ID
            folder: Folder containing the location (optional)

        Returns:
            Location dictionary

        """
        logger.info(f"Getting location {location_id}")

        if self.mock:
            return {
                "id": location_id,
                "name": "New York Office",
                "region": "us-east",
                "country": "United States",
                "state": "New York",
                "city": "New York",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "folder": folder or "Locations",
                "total_users": 150,
                "active_users": 87,
                "bandwidth_capacity": 1000,
                "bandwidth_used": 450,
                "metadata": {"site_code": "NYC01", "timezone": "America/New_York"},
            }

        # TODO: Implement actual API call when insights API is available
        raise NotImplementedError("Insights API not yet available in pan-scm-sdk")

    # ------------------------------------------------------------------------------------ Remote Networks ----------------------------------------------------------------------------------

    def list_remote_network_insights(self, folder: str = None, max_results: int = 100, include_metrics: bool = False, **filters) -> list[dict[str, Any]]:
        """List remote network insights from API.

        Args:
            folder: Folder to filter networks (optional)
            max_results: Maximum number of results to return
            include_metrics: Include performance metrics
            **filters: Additional filters (connectivity, etc.)

        Returns:
            List of remote network insights dictionaries

        """
        logger.info("Listing remote network insights")

        if self.mock:
            return [
                {
                    "id": "rn-001",
                    "name": "Branch Office 1",
                    "connectivity_status": "connected",
                    "folder": folder or "Remote Networks",
                    "site_id": "site-001",
                    "region": "us-east",
                    "bandwidth_allocated": 100,
                    "bandwidth_used": 45,
                    "latency": 25.5 if include_metrics else None,
                    "packet_loss": 0.1 if include_metrics else None,
                    "jitter": 2.3 if include_metrics else None,
                    "tunnel_count": 2,
                    "active_tunnels": 2,
                    "last_status_change": "2024-01-19T14:30:00Z",
                    "metadata": {"branch_code": "BR001"},
                },
                {
                    "id": "rn-002",
                    "name": "Branch Office 2",
                    "connectivity_status": "degraded",
                    "folder": folder or "Remote Networks",
                    "site_id": "site-002",
                    "region": "us-west",
                    "bandwidth_allocated": 50,
                    "bandwidth_used": 48,
                    "latency": 150.2 if include_metrics else None,
                    "packet_loss": 2.5 if include_metrics else None,
                    "jitter": 15.7 if include_metrics else None,
                    "tunnel_count": 2,
                    "active_tunnels": 1,
                    "last_status_change": "2024-01-20T10:15:00Z",
                    "metadata": {"branch_code": "BR002"},
                },
            ]

        # TODO: Implement actual API call when insights API is available
        raise NotImplementedError("Insights API not yet available in pan-scm-sdk")

    def get_remote_network_insights(self, network_id: str, folder: str = None, include_metrics: bool = False) -> dict[str, Any]:
        """Get specific remote network insights by ID.

        Args:
            network_id: Network ID
            folder: Folder containing the network (optional)
            include_metrics: Include performance metrics

        Returns:
            Remote network insights dictionary

        """
        logger.info(f"Getting remote network insights for {network_id}")

        if self.mock:
            return {
                "id": network_id,
                "name": "Branch Office 1",
                "connectivity_status": "connected",
                "folder": folder or "Remote Networks",
                "site_id": "site-001",
                "region": "us-east",
                "bandwidth_allocated": 100,
                "bandwidth_used": 45,
                "latency": 25.5 if include_metrics else None,
                "packet_loss": 0.1 if include_metrics else None,
                "jitter": 2.3 if include_metrics else None,
                "tunnel_count": 2,
                "active_tunnels": 2,
                "last_status_change": "2024-01-19T14:30:00Z",
                "metadata": {"branch_code": "BR001"},
            }

        # TODO: Implement actual API call when insights API is available
        raise NotImplementedError("Insights API not yet available in pan-scm-sdk")

    # -------------------------------------------------------------------------------------- Service Connections -----------------------------------------------------------------------------

    def list_service_connection_insights(self, folder: str = None, max_results: int = 100, include_metrics: bool = False, **filters) -> list[dict[str, Any]]:
        """List service connection insights from API.

        Args:
            folder: Folder to filter connections (optional)
            max_results: Maximum number of results to return
            include_metrics: Include performance metrics
            **filters: Additional filters (health_status, etc.)

        Returns:
            List of service connection insights dictionaries

        """
        logger.info("Listing service connection insights")

        if self.mock:
            return [
                {
                    "id": "sc-001",
                    "name": "AWS Direct Connect",
                    "health_status": "healthy",
                    "folder": folder or "Service Connections",
                    "region": "us-east-1",
                    "service_type": "aws",
                    "latency": 5.2 if include_metrics else None,
                    "throughput": 850.5 if include_metrics else None,
                    "availability": 99.95 if include_metrics else None,
                    "uptime": 2592000,
                    "last_health_check": "2024-01-20T11:00:00Z",
                    "error_count": 0,
                    "warning_count": 2,
                    "metadata": {"connection_id": "dxcon-abc123"},
                },
                {
                    "id": "sc-002",
                    "name": "Azure ExpressRoute",
                    "health_status": "degraded",
                    "folder": folder or "Service Connections",
                    "region": "westus2",
                    "service_type": "azure",
                    "latency": 45.8 if include_metrics else None,
                    "throughput": 450.2 if include_metrics else None,
                    "availability": 98.5 if include_metrics else None,
                    "uptime": 1728000,
                    "last_health_check": "2024-01-20T10:55:00Z",
                    "error_count": 5,
                    "warning_count": 15,
                    "metadata": {"circuit_id": "expr-xyz789"},
                },
            ]

        # TODO: Implement actual API call when insights API is available
        raise NotImplementedError("Insights API not yet available in pan-scm-sdk")

    def get_service_connection_insights(self, connection_id: str, folder: str = None, include_metrics: bool = False) -> dict[str, Any]:
        """Get specific service connection insights by ID.

        Args:
            connection_id: Connection ID
            folder: Folder containing the connection (optional)
            include_metrics: Include performance metrics

        Returns:
            Service connection insights dictionary

        """
        logger.info(f"Getting service connection insights for {connection_id}")

        if self.mock:
            return {
                "id": connection_id,
                "name": "AWS Direct Connect",
                "health_status": "healthy",
                "folder": folder or "Service Connections",
                "region": "us-east-1",
                "service_type": "aws",
                "latency": 5.2 if include_metrics else None,
                "throughput": 850.5 if include_metrics else None,
                "availability": 99.95 if include_metrics else None,
                "uptime": 2592000,
                "last_health_check": "2024-01-20T11:00:00Z",
                "error_count": 0,
                "warning_count": 2,
                "metadata": {"connection_id": "dxcon-abc123"},
            }

        # TODO: Implement actual API call when insights API is available
        raise NotImplementedError("Insights API not yet available in pan-scm-sdk")

    # ------------------------------------------------------------------------------------ Tunnels ----------------------------------------------------------------------------------

    def list_tunnels(self, folder: str = None, max_results: int = 100, include_stats: bool = False, **filters) -> list[dict[str, Any]]:
        """List tunnels from insights API.

        Args:
            folder: Folder to filter tunnels (optional)
            max_results: Maximum number of results to return
            include_stats: Include performance statistics
            **filters: Additional filters (status, start_time, end_time, etc.)

        Returns:
            List of tunnel dictionaries

        """
        logger.info("Listing tunnels")

        if self.mock:
            return [
                {
                    "id": "tunnel-001",
                    "name": "IPSec-Branch-01",
                    "status": "up",
                    "tunnel_type": "IPSec",
                    "folder": folder or "Tunnels",
                    "source_zone": "trust",
                    "destination_zone": "untrust",
                    "local_address": "203.0.113.1",
                    "remote_address": "198.51.100.1",
                    "bytes_sent": 1073741824 if include_stats else None,
                    "bytes_received": 2147483648 if include_stats else None,
                    "packets_sent": 1000000 if include_stats else None,
                    "packets_received": 2000000 if include_stats else None,
                    "latency": 25.5 if include_stats else None,
                    "jitter": 2.3 if include_stats else None,
                    "packet_loss": 0.1 if include_stats else None,
                    "uptime": 2592000,
                    "last_state_change": "2024-01-01T00:00:00Z",
                    "metadata": {"peer_id": "branch-01"},
                },
                {
                    "id": "tunnel-002",
                    "name": "SSL-VPN-Users",
                    "status": "down",
                    "tunnel_type": "SSL",
                    "folder": folder or "Tunnels",
                    "source_zone": "vpn",
                    "destination_zone": "trust",
                    "local_address": "203.0.113.2",
                    "remote_address": "0.0.0.0",
                    "bytes_sent": 0 if include_stats else None,
                    "bytes_received": 0 if include_stats else None,
                    "packets_sent": 0 if include_stats else None,
                    "packets_received": 0 if include_stats else None,
                    "latency": None,
                    "jitter": None,
                    "packet_loss": None,
                    "uptime": 0,
                    "last_state_change": "2024-01-20T10:00:00Z",
                    "metadata": {"pool": "vpn-pool-1"},
                },
            ]

        # TODO: Implement actual API call when insights API is available
        raise NotImplementedError("Insights API not yet available in pan-scm-sdk")

    def get_tunnel(self, tunnel_id: str, folder: str = None, include_stats: bool = False, start_time: str = None, end_time: str = None) -> dict[str, Any]:
        """Get a specific tunnel by ID.

        Args:
            tunnel_id: Tunnel ID
            folder: Folder containing the tunnel (optional)
            include_stats: Include performance statistics
            start_time: Start time for historical data (ISO format)
            end_time: End time for historical data (ISO format)

        Returns:
            Tunnel dictionary

        """
        logger.info(f"Getting tunnel {tunnel_id}")

        if self.mock:
            return {
                "id": tunnel_id,
                "name": "IPSec-Branch-01",
                "status": "up",
                "tunnel_type": "IPSec",
                "folder": folder or "Tunnels",
                "source_zone": "trust",
                "destination_zone": "untrust",
                "local_address": "203.0.113.1",
                "remote_address": "198.51.100.1",
                "bytes_sent": 1073741824 if include_stats else None,
                "bytes_received": 2147483648 if include_stats else None,
                "packets_sent": 1000000 if include_stats else None,
                "packets_received": 2000000 if include_stats else None,
                "latency": 25.5 if include_stats else None,
                "jitter": 2.3 if include_stats else None,
                "packet_loss": 0.1 if include_stats else None,
                "uptime": 2592000,
                "last_state_change": "2024-01-01T00:00:00Z",
                "metadata": {"peer_id": "branch-01"},
            }

        # TODO: Implement actual API call when insights API is available
        raise NotImplementedError("Insights API not yet available in pan-scm-sdk")


class LazyClient:
    """Lazy wrapper for SCMClient that delays initialization until first use."""

    def __init__(self):
        """Initialize the lazy client wrapper."""
        self._client = None

    def __getattr__(self, name):
        """Initialize client on first access."""
        if self._client is None:
            self._client = SCMClient()
        return getattr(self._client, name)


# Create a singleton instance of the SCM client with lazy initialization
scm_client = LazyClient()
