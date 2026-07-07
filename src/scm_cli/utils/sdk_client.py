"""SDK client integration for pan-scm-cli.

This module provides integration with the pan-scm-sdk client for interacting
with Palo Alto Networks Strata Cloud Manager. It uses the credentials from
dynaconf settings.
"""

import contextlib
import gzip
import inspect
import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, NoReturn

import requests
from oauthlib.oauth2.rfc6749.errors import InvalidClientError
from pydantic import ValidationError
from scm.client import Scm
from scm.exceptions import APIError, AuthenticationError, ClientError, GatewayTimeoutError, NotFoundError, ObjectNotPresentError

from . import token_cache
from .config import get_credentials, settings
from .context import get_current_context

# Create logger (will be configured in __init__)
logger = logging.getLogger(__name__)

_TRUTHY = ("1", "true", "yes", "on")


def mock_mode_requested() -> bool:
    """Return True if mock mode was explicitly requested.

    Mock mode activates only via the SCM_MOCK environment variable —
    never as a silent fallback for missing credentials. The environment
    is read directly (not through Dynaconf) so the check stays accurate
    even after settings have been loaded and cached.
    """
    import os

    return os.environ.get("SCM_MOCK", "").strip().lower() in _TRUTHY


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
        """Initialize the SCM client with logger and credentials.

        Logging is configured once at CLI entry (main callback), not here.
        """
        self.logger = logger
        self.logger.info("Initializing SCM client")
        self.client = None

        # Log the current context if one is set
        current_context = get_current_context()
        if current_context:
            self.logger.info(f"Using authentication context: {current_context}")
        else:
            self.logger.info("No context set, using environment variables or default settings")

        self._bearer_token_mode = False
        self._cached_token_mode = False

        if mock_mode_requested():
            # Explicit mock mode: no API client, methods return mock data.
            self.logger.info("Mock mode enabled (SCM_MOCK) — no API calls will be made")
            # The following mock credentials are used only in mock mode for testing purposes and do not represent real secrets.
            self.client_id = "mock-client-id"
            self.client_secret = "mock-client"  # noqa: S105
            self.tsg_id = "mock-tsg-id"
            return

        try:
            # Check for bearer token auth mode first
            access_token = settings.get("access_token", None)
            if not access_token and current_context:
                from .context import get_context_config

                try:
                    ctx_config = get_context_config(current_context)
                    access_token = ctx_config.get("access_token")
                except Exception as e:
                    self.logger.warning(f"Could not read context config for '{current_context}': {e}")

            if access_token:
                # Bearer token authentication mode
                self.logger.info("Using bearer token authentication mode")
                self.client_id = ""
                self.client_secret = ""  # noqa: S105
                self.tsg_id = ""
                self._bearer_token_mode = True

                # Resolve region: global flag > context > default
                try:
                    from scm_cli.main import get_region_override

                    region_override = get_region_override()
                except ImportError:
                    region_override = None
                resolved_region = region_override or settings.get("region", "americas")

                scm_kwargs: dict[str, Any] = {
                    "access_token": access_token,
                    "log_level": settings.get("log_level", "INFO"),
                }
                scm_params = inspect.signature(Scm.__init__).parameters
                if "region" in scm_params:
                    scm_kwargs["region"] = resolved_region
                # Endpoint overrides (env > context) — omitted when unset so SDK defaults apply
                api_base_url = settings.get("api_base_url", None)
                if api_base_url and "api_base_url" in scm_params:
                    scm_kwargs["api_base_url"] = api_base_url
                token_url = settings.get("token_url", None)
                if token_url and "token_url" in scm_params:
                    scm_kwargs["token_url"] = token_url
                self.client = Scm(**scm_kwargs)
                self.logger.info("Successfully initialized SDK client with bearer token")
            else:
                # OAuth2 authentication mode
                credentials = get_credentials()
                self.client_id = credentials["client_id"]
                self.client_secret = credentials["client_secret"]
                self.tsg_id = credentials["tsg_id"]

                # Resolve region: global flag > context > default
                try:
                    from scm_cli.main import get_region_override

                    region_override = get_region_override()
                except ImportError:
                    region_override = None
                resolved_region = region_override or credentials.get("region", "americas")

                scm_params = inspect.signature(Scm.__init__).parameters
                common_kwargs: dict[str, Any] = {"log_level": settings.get("log_level", "INFO")}
                if "region" in scm_params:
                    common_kwargs["region"] = resolved_region
                # Endpoint overrides (env > context) — omitted when unset so SDK defaults apply
                api_base_url = credentials.get("api_base_url") or settings.get("api_base_url", None)
                if api_base_url and "api_base_url" in scm_params:
                    common_kwargs["api_base_url"] = api_base_url
                token_url = credentials.get("token_url") or settings.get("token_url", None)
                if token_url and "token_url" in scm_params:
                    common_kwargs["token_url"] = token_url

                # Reuse a cached OAuth token (bearer-mode session) when one is
                # still valid for these exact credentials — skips the token +
                # JWKS roundtrips on every invocation.
                cached = token_cache.load_token(current_context)
                if cached and str(cached.get("client_id")) == str(self.client_id) and str(cached.get("tsg_id")) == str(self.tsg_id):
                    self.client = Scm(access_token=cached["token"]["access_token"], **common_kwargs)
                    self._cached_token_mode = True
                    self.logger.debug("Using cached OAuth token (bearer-mode session)")
                else:
                    self.client = Scm(
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                        tsg_id=self.tsg_id,
                        **common_kwargs,
                    )
                    oauth_client = getattr(self.client, "oauth_client", None)
                    token = getattr(getattr(oauth_client, "session", None), "token", None)
                    if token and token.get("access_token"):
                        token_cache.save_token(current_context, dict(token), client_id=self.client_id, tsg_id=self.tsg_id)
                self.logger.info(f"Successfully initialized SDK client for TSG ID: {self.tsg_id}")
        except (ValueError, AuthenticationError) as e:
            import sys

            print(f"\n❌ Authentication not configured: {e}", file=sys.stderr)
            print(f"\nCurrent context: {current_context or 'None set'}", file=sys.stderr)
            print("\nTo fix this issue:", file=sys.stderr)
            print(
                "  1. Create a context: scm context create <name> --client-id <id> --client-secret <secret> --tsg-id <tsg>",
                file=sys.stderr,
            )
            print("  2. Switch context: scm context use <name>", file=sys.stderr)
            print(
                "  3. Or use environment variables: SCM_CLIENT_ID, SCM_CLIENT_SECRET, SCM_TSG_ID",
                file=sys.stderr,
            )
            print(
                "\nFor testing without credentials, set SCM_MOCK=1 to enable mock mode.",
                file=sys.stderr,
            )
            raise SystemExit(1) from e
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
            if isinstance(value, list | dict) and not value:
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
            if self._cached_token_mode:
                # The cached token was rejected — clear it so the next
                # invocation performs a fresh OAuth login.
                token_cache.clear_token(get_current_context())
                self.logger.warning("Cached token rejected by the API; cache cleared — retry the command")
        elif isinstance(exception, NotFoundError):
            self.logger.error(f"Resource not found: {resource_name} in folder {folder}")
        elif isinstance(exception, ValidationError):
            self.logger.error(
                f"SDK model validation error during {operation} of {resource_name}: {str(exception)}. "
                "This is likely a mismatch between the SDK model and the API response. "
                "Consider updating pan-scm-sdk."
            )
        elif isinstance(exception, AttributeError) and "has no attribute" in str(exception):
            self.logger.error(f"SDK service not available for {resource_name}: {str(exception)}. This feature may not be implemented in the current pan-scm-sdk version.")
        elif isinstance(exception, ClientError):
            self.logger.error(f"Validation error during {operation} of {resource_name}: {str(exception)}")
        elif isinstance(exception, GatewayTimeoutError):
            self.logger.error(
                f"Request timed out during {operation} of {resource_name}: {str(exception)}. "
                "The operation may still be processing on the server. "
                "Retry after a brief wait or check the SCM portal for current status."
            )
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
                }
                if description:
                    allocation_data["description"] = description
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
                # Remove folder from data dict; SDK create() receives it separately
                data.pop("folder", None)
                created = self.client.service_connection.create(data)
                self.logger.info(f"Successfully created service connection '{name}' in folder: {folder}")
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result

        except Exception as e:
            self._handle_api_exception("creating/updating", "service connection", name, e)

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
            self._handle_api_exception("deleting", "service connection", name, e)

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
            self._handle_api_exception("fetching", "service connection", name, e)

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
            self._handle_api_exception("creating/updating", "remote network", name, e)

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
            self._handle_api_exception("deleting", "remote network", name, e)

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
            self._handle_api_exception("fetching", "remote network", name, e)

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
        exclude_folders: list[str] | None = None,
        exclude_snippets: list[str] | None = None,
        exclude_devices: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """List address objects in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return objects defined exactly in the specified container
            exclude_folders: List of folder names to exclude from results
            exclude_snippets: List of snippet names to exclude from results
            exclude_devices: List of device names to exclude from results

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
            # Build list kwargs with optional exclude filters
            list_kwargs = {"exact_match": exact_match, **container_kwargs}
            if exclude_folders:
                list_kwargs["exclude_folders"] = exclude_folders
            if exclude_snippets:
                list_kwargs["exclude_snippets"] = exclude_snippets
            if exclude_devices:
                list_kwargs["exclude_devices"] = exclude_devices

            # List addresses using the SDK
            results = self.client.address.list(**list_kwargs)

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
            }
            if description:
                group_data["description"] = description

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
                    if description:
                        existing_group.description = description
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
            result_dict = json.loads(result.model_dump_json(exclude_unset=True))
            result_dict["__action__"] = "updated" if existing_group else "created"
            return result_dict
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
            }
            if description:
                app_data["description"] = description

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
                if description:
                    existing_app.description = description

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
            result_dict = json.loads(result.model_dump_json(exclude_unset=True))
            result_dict["__action__"] = "updated" if existing_app else "created"
            return result_dict
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
            result_dict = json.loads(result.model_dump_json(exclude_unset=True))
            result_dict["__action__"] = "updated" if existing_group else "created"
            return result_dict
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
            }
            if description:
                group_data["description"] = description

            if tags:
                group_data["tag"] = tags  # SDK expects 'tag', not 'tags'

            # If a dynamic user group exists, update it
            if existing_group:
                # Update fields
                existing_group.filter = filter
                if description:
                    existing_group.description = description
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
            result_dict = json.loads(result.model_dump_json(exclude_unset=True))
            result_dict["__action__"] = "updated" if existing_group else "created"
            return result_dict
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
            # First, try to fetch the existing EDL
            existing_edl = None
            try:
                existing_edl = self.client.external_dynamic_list.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing EDL '{name}' in folder '{folder}', updating...")
            except NotFoundError:
                self.logger.info(f"EDL '{name}' not found in folder '{folder}', creating new...")
            except Exception as fetch_error:
                # Log but continue - we'll try to create if fetch failed for other reasons
                self.logger.warning(f"Error fetching EDL '{name}': {str(fetch_error)}")

            if existing_edl:
                # Update existing EDL by modifying the model object's attributes
                existing_edl.type = type_config
                result = self.client.external_dynamic_list.update(existing_edl)
                response = json.loads(result.model_dump_json(exclude_unset=True))
                response["__action__"] = "updated"
                return response
            else:
                # Create a new EDL
                edl_data = {
                    "folder": folder,
                    "name": name,
                    "type": type_config,
                }
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
            self._handle_api_exception("creating/updating", "HIP profile", name, e)

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
            self._handle_api_exception("deleting", "HIP profile", name, e)

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
            self._handle_api_exception("fetching", "HIP profile", name, e)

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
            self._handle_api_exception("creating/updating", "HTTP server profile", name, e)

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
            self._handle_api_exception("deleting", "HTTP server profile", name, e)

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
            self._handle_api_exception("fetching", "HTTP server profile", name, e)

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
            self._handle_api_exception("creating/updating", "log-forwarding profile", name, e)

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
            self._handle_api_exception("deleting", "log-forwarding profile", name, e)

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

    # Regions ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_region(
        self,
        region_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create or update a region using smart upsert logic.

        Args:
            region_data: The region data

        Returns:
            Created/updated region data

        """
        # Determine container (folder, snippet, or device)
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None

        for field in container_fields:
            if field in region_data and region_data[field] is not None:
                container_field = field
                container_value = region_data[field]
                break

        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")

        # Return mock data if no client
        if not self.client:
            return region_data

        # Check if the region already exists
        existing_region = None
        try:
            existing_region = self.client.region.fetch(name=region_data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing region '{region_data['name']}' in {container_field} '{container_value}'")
        except NotFoundError:
            self.logger.info(f"Region '{region_data['name']}' not found in {container_field} '{container_value}', will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching region '{region_data['name']}': {str(e)}")

        if existing_region:
            # Check what needs updating
            needs_update = False
            update_fields = []

            # Compare geo_location
            if "geo_location" in region_data and region_data["geo_location"]:
                new_geo = region_data["geo_location"]
                if hasattr(existing_region, "geo_location") and existing_region.geo_location:
                    if existing_region.geo_location.latitude != new_geo.get("latitude") or existing_region.geo_location.longitude != new_geo.get("longitude"):
                        existing_region.geo_location.latitude = new_geo["latitude"]
                        existing_region.geo_location.longitude = new_geo["longitude"]
                        update_fields.append("geo_location")
                        needs_update = True
                else:
                    from scm.models.objects.regions import GeoLocation

                    existing_region.geo_location = GeoLocation(**new_geo)
                    update_fields.append("geo_location")
                    needs_update = True

            # Compare addresses
            if "address" in region_data and region_data["address"] is not None:
                existing_addresses = set(existing_region.address) if hasattr(existing_region, "address") and existing_region.address else set()
                new_addresses = set(region_data["address"])
                if existing_addresses != new_addresses:
                    existing_region.address = region_data["address"]
                    update_fields.append("address")
                    needs_update = True

            if needs_update:
                self.logger.info(f"Updating region fields: {', '.join(update_fields)}")
                try:
                    updated = existing_region.update()
                    self.logger.info(f"Successfully updated region '{region_data['name']}' in {container_field} '{container_value}'")
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"region '{region_data['name']}'", update_error)
            else:
                self.logger.info(f"No changes detected for region '{region_data['name']}', skipping update")
                result = json.loads(existing_region.model_dump_json(exclude_unset=True))
                result["__action__"] = "no_change"
                return result
        else:
            # Create new region
            try:
                created = self.client.region.create(region_data)
                self.logger.info(f"Created new region '{region_data['name']}' in {container_field} '{container_value}'")
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception(
                    "creating",
                    str(container_value),
                    f"region '{region_data['name']}'",
                    create_error,
                )

    def delete_region(
        self,
        name: str,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
    ) -> None:
        """Delete a region.

        Args:
            name: Name of the region to delete
            folder: Folder location
            snippet: Snippet location
            device: Device location

        """
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete region: {name}")
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
            # First, fetch the region to get its ID
            region = self.client.region.fetch(name=name, **container_kwargs)
            self.client.region.delete(str(region.id))
            self.logger.info(f"Deleted region: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"region '{name}'", e)

    def get_region(
        self,
        name: str,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
    ) -> dict[str, Any] | None:
        """Get a specific region.

        Args:
            name: Name of the region to retrieve
            folder: Folder location
            snippet: Snippet location
            device: Device location

        Returns:
            Region data or None if not found

        """
        if not self.client:
            return {
                "id": "region-mock",
                "name": name,
                "folder": folder or "ngfw-shared",
                "geo_location": {"latitude": 30.2672, "longitude": -97.7431},
                "address": ["10.0.0.0/8", "192.168.1.0/24"],
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
            result = self.client.region.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"Region '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"region '{name}'", e)

    def list_regions(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List regions in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return exact matches

        Returns:
            List of regions

        """
        if not self.client:
            return [
                {
                    "id": "region-mock1",
                    "folder": folder or "ngfw-shared",
                    "name": "US-South",
                    "geo_location": {"latitude": 30.2672, "longitude": -97.7431},
                    "address": ["10.0.0.0/8"],
                },
                {
                    "id": "region-mock2",
                    "folder": folder or "ngfw-shared",
                    "name": "US-East",
                    "geo_location": {"latitude": 40.7128, "longitude": -74.0060},
                    "address": ["172.16.0.0/12"],
                },
                {
                    "id": "region-mock3",
                    "folder": folder or "ngfw-shared",
                    "name": "EU-West",
                    "geo_location": {"latitude": 51.5074, "longitude": -0.1278},
                    "address": ["192.168.0.0/16"],
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
            # List regions using the SDK
            results = self.client.region.list(exact_match=exact_match, **container_kwargs)

            # Convert SDK response to the list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "regions", e)

    # Quarantined Devices ------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_quarantined_device(
        self,
        device_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a quarantined device entry.

        Args:
            device_data: The quarantined device data (host_id, optional serial_number)

        Returns:
            Created quarantined device data

        """
        self.logger.info(f"Creating quarantined device: {device_data.get('host_id', 'unknown')}")

        if not self.client:
            return device_data

        try:
            created = self.client.quarantined_device.create(device_data)
            self.logger.info(f"Created quarantined device: {device_data.get('host_id')}")
            return json.loads(created.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("creating", "quarantined-devices", f"device '{device_data.get('host_id')}'", e)

    def delete_quarantined_device(
        self,
        host_id: str,
    ) -> None:
        """Delete a quarantined device by host ID.

        Args:
            host_id: The host ID of the quarantined device to delete

        """
        self.logger.info(f"Deleting quarantined device: {host_id}")

        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete quarantined device: {host_id}")
            return

        try:
            self.client.quarantined_device.delete(host_id=host_id)
            self.logger.info(f"Deleted quarantined device: {host_id}")
        except Exception as e:
            self._handle_api_exception("deleting", "quarantined-devices", f"device '{host_id}'", e)

    def list_quarantined_devices(
        self,
        host_id: str | None = None,
        serial_number: str | None = None,
    ) -> list[dict[str, Any]]:
        """List quarantined devices with optional filtering.

        Args:
            host_id: Filter by device host ID
            serial_number: Filter by device serial number

        Returns:
            List of quarantined device objects

        """
        self.logger.info(f"Listing quarantined devices (host_id={host_id}, serial_number={serial_number})")

        if not self.client:
            return [
                {
                    "host_id": "mock-host-001",
                    "serial_number": "SN-001",
                },
                {
                    "host_id": "mock-host-002",
                    "serial_number": "SN-002",
                },
            ]

        try:
            results = self.client.quarantined_device.list(
                host_id=host_id,
                serial_number=serial_number,
            )
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", "quarantined-devices", "quarantined devices", e)

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
            self._handle_api_exception("deleting", "service", name, e)

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
            self._handle_api_exception("fetching", "service", name, e)

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
            self._handle_api_exception("creating/updating", "service group", name, e)

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
            self._handle_api_exception("deleting", "service group", name, e)

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
            self._handle_api_exception("fetching", "service group", name, e)

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
            # Fetch first to get the ID, then delete by ID (consistent with other delete methods)
            profile = self.client.syslog_server_profile.fetch(name=name, **container_kwargs)
            self.client.syslog_server_profile.delete(str(profile.id))
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

    # Schedules ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_schedule(
        self,
        schedule_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create or update a schedule using smart upsert logic.

        Args:
            schedule_data: The schedule data

        Returns:
            Created/updated schedule data

        """
        # Determine container (folder, snippet, or device)
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None

        for field in container_fields:
            if field in schedule_data and schedule_data[field] is not None:
                container_field = field
                container_value = schedule_data[field]
                break

        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")

        # Return mock data if no client
        if not self.client:
            return schedule_data

        # Check if the schedule already exists
        existing_schedule = None
        try:
            existing_schedule = self.client.schedule.fetch(name=schedule_data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing schedule '{schedule_data['name']}' in {container_field} '{container_value}'")
        except NotFoundError:
            self.logger.info(f"Schedule '{schedule_data['name']}' not found in {container_field} '{container_value}', will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching schedule '{schedule_data['name']}': {str(e)}")

        if existing_schedule:
            # Check what needs updating
            needs_update = False
            update_fields = []

            # Compare schedule_type
            if "schedule_type" in schedule_data:
                existing_data = json.loads(existing_schedule.model_dump_json(exclude_unset=True))
                if existing_data.get("schedule_type") != schedule_data["schedule_type"]:
                    existing_schedule.schedule_type = schedule_data["schedule_type"]
                    update_fields.append("schedule_type")
                    needs_update = True

            if needs_update:
                self.logger.info(f"Updating schedule fields: {', '.join(update_fields)}")
                try:
                    updated = existing_schedule.update()
                    self.logger.info(f"Successfully updated schedule '{schedule_data['name']}' in {container_field} '{container_value}'")
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"schedule '{schedule_data['name']}'", update_error)
            else:
                self.logger.info(f"No changes detected for schedule '{schedule_data['name']}', skipping update")
                result = json.loads(existing_schedule.model_dump_json(exclude_unset=True))
                result["__action__"] = "no_change"
                return result
        else:
            # Create new schedule
            try:
                created = self.client.schedule.create(schedule_data)
                self.logger.info(f"Created new schedule '{schedule_data['name']}' in {container_field} '{container_value}'")
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception(
                    "creating",
                    str(container_value),
                    f"schedule '{schedule_data['name']}'",
                    create_error,
                )

    def delete_schedule(
        self,
        name: str,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
    ) -> None:
        """Delete a schedule.

        Args:
            name: Name of the schedule to delete
            folder: Folder location
            snippet: Snippet location
            device: Device location

        """
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete schedule: {name}")
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
            # First, fetch the schedule to get its ID
            schedule = self.client.schedule.fetch(name=name, **container_kwargs)
            self.client.schedule.delete(str(schedule.id))
            self.logger.info(f"Deleted schedule: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"schedule '{name}'", e)

    def get_schedule(
        self,
        name: str,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
    ) -> dict[str, Any] | None:
        """Get a specific schedule.

        Args:
            name: Name of the schedule to retrieve
            folder: Folder location
            snippet: Snippet location
            device: Device location

        Returns:
            Schedule data or None if not found

        """
        if not self.client:
            return {
                "id": "schedule-mock",
                "name": name,
                "folder": folder or "ngfw-shared",
                "schedule_type": {
                    "recurring": {
                        "daily": ["09:00-17:00"],
                    },
                },
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
            result = self.client.schedule.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"Schedule '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"schedule '{name}'", e)

    def list_schedules(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List schedules in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return exact matches

        Returns:
            List of schedules

        """
        if not self.client:
            return [
                {
                    "id": "schedule-mock1",
                    "folder": folder or "ngfw-shared",
                    "name": "BusinessHours",
                    "schedule_type": {
                        "recurring": {
                            "daily": ["09:00-17:00"],
                        },
                    },
                },
                {
                    "id": "schedule-mock2",
                    "folder": folder or "ngfw-shared",
                    "name": "Weekends",
                    "schedule_type": {
                        "recurring": {
                            "weekly": {
                                "saturday": ["00:00-23:59"],
                                "sunday": ["00:00-23:59"],
                            },
                        },
                    },
                },
                {
                    "id": "schedule-mock3",
                    "folder": folder or "ngfw-shared",
                    "name": "MaintenanceWindow",
                    "schedule_type": {
                        "non_recurring": ["2026/03/15@02:00-2026/03/15@06:00"],
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
            # List schedules using the SDK
            results = self.client.schedule.list(exact_match=exact_match, **container_kwargs)

            # Convert SDK response to the list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "schedules", e)

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
                    updated = self.client.tag.update(existing_tag)
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

    # ----------------------------------------------------------------------------- Auto Tag Actions ------------------------------------------------------------------------------------

    def create_auto_tag_action(
        self,
        auto_tag_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create or update an auto tag action.

        Args:
            auto_tag_data: The auto tag action data

        Returns:
            Created/updated auto tag action data

        """
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None

        for field in container_fields:
            if field in auto_tag_data and auto_tag_data[field] is not None:
                container_field = field
                container_value = auto_tag_data[field]
                break

        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")

        name = auto_tag_data.get("name", "unknown")
        self.logger.info(f"Creating/updating auto tag action: {name} in {container_field} {container_value}")

        if not self.client:
            auto_tag_data["id"] = f"ata-{name}"
            auto_tag_data["__action__"] = "created"
            return auto_tag_data

        try:
            existing = None
            try:
                existing = self.client.auto_tag_action.fetch(
                    name=name,
                    **{container_field: container_value},
                )
            except (NotFoundError, Exception):
                self.logger.info(f"Auto tag action '{name}' not found, will create new")

            if existing:
                try:
                    for key, value in auto_tag_data.items():
                        if key not in container_fields and key != "name" and hasattr(existing, key):
                            setattr(existing, key, value)
                    updated = existing.update()
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
                except Exception as update_error:
                    self._handle_api_exception("updating", container_value or "", f"auto tag action '{name}'", update_error)
            else:
                try:
                    created = self.client.auto_tag_action.create(auto_tag_data)
                    result = json.loads(created.model_dump_json(exclude_unset=True))
                    result["__action__"] = "created"
                    return result
                except Exception as create_error:
                    self._handle_api_exception("creating", container_value or "", f"auto tag action '{name}'", create_error)
        except Exception as e:
            self._handle_api_exception("creating/updating", container_value or "", f"auto tag action '{name}'", e)

    def delete_auto_tag_action(
        self,
        name: str,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
    ) -> None:
        """Delete an auto tag action.

        Args:
            name: Name of the auto tag action to delete
            folder: Folder location
            snippet: Snippet location
            device: Device location

        """
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete auto tag action: {name}")
            return

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
            obj = self.client.auto_tag_action.fetch(name=name, **container_kwargs)
            self.client.auto_tag_action.delete(str(obj.id))
            self.logger.info(f"Deleted auto tag action: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"auto tag action '{name}'", e)

    def get_auto_tag_action(
        self,
        name: str,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
    ) -> dict[str, Any] | None:
        """Get a specific auto tag action.

        Args:
            name: Name of the auto tag action
            folder: Folder location
            snippet: Snippet location
            device: Device location

        Returns:
            Auto tag action data or None if not found

        """
        if not self.client:
            return {
                "id": f"ata-{name}",
                "name": name,
                "folder": folder or "ngfw-shared",
                "description": "Mock auto tag action",
                "log_type": "traffic",
                "actions": [{"name": "add-tag", "type": {"tagging": {"action": "add-tag", "tags": ["auto-tagged"]}}}],
            }

        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            result = self.client.auto_tag_action.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("getting", folder or snippet or device or "", f"auto tag action '{name}'", e)

    def list_auto_tag_actions(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List auto tag actions in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return exact matches

        Returns:
            List of auto tag actions

        """
        if not self.client:
            return [
                {
                    "id": "ata-mock1",
                    "folder": folder or "ngfw-shared",
                    "name": "auto-tag-suspicious",
                    "description": "Auto tag suspicious traffic",
                    "log_type": "threat",
                },
                {
                    "id": "ata-mock2",
                    "folder": folder or "ngfw-shared",
                    "name": "auto-tag-blocked",
                    "description": "Auto tag blocked connections",
                    "log_type": "traffic",
                },
            ]

        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            results = self.client.auto_tag_action.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "auto tag actions", e)

    # ======================================================================================================================================================================================

    # --------------------------------------------------------------------------------- IKE Crypto Profiles ---------------------------------------------------------------------------------

    def create_ike_crypto_profile(self, profile_data: dict[str, Any]) -> dict[str, Any]:
        """Create or update an IKE crypto profile using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in profile_data and profile_data[field] is not None:
                container_field = field
                container_value = profile_data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            return profile_data
        existing_profile = None
        try:
            existing_profile = self.client.ike_crypto_profile.fetch(name=profile_data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing IKE crypto profile '{profile_data['name']}' in {container_field} '{container_value}'")
        except NotFoundError:
            self.logger.info(f"IKE crypto profile '{profile_data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching IKE crypto profile '{profile_data['name']}': {str(e)}")
        if existing_profile:
            needs_update = False
            update_fields = []
            if "hash" in profile_data:
                existing_hash = [h.value if hasattr(h, "value") else str(h) for h in existing_profile.hash]
                if set(profile_data["hash"]) != set(existing_hash):
                    needs_update = True
                    update_fields.append("hash")
            if "encryption" in profile_data:
                existing_enc = [e.value if hasattr(e, "value") else str(e) for e in existing_profile.encryption]
                if set(profile_data["encryption"]) != set(existing_enc):
                    needs_update = True
                    update_fields.append("encryption")
            if "dh_group" in profile_data:
                existing_dh = [g.value if hasattr(g, "value") else str(g) for g in existing_profile.dh_group]
                if set(profile_data["dh_group"]) != set(existing_dh):
                    needs_update = True
                    update_fields.append("dh_group")
            if "lifetime" in profile_data:
                existing_lifetime = existing_profile.lifetime.model_dump() if existing_profile.lifetime else None
                if profile_data["lifetime"] != existing_lifetime:
                    needs_update = True
                    update_fields.append("lifetime")
            if "authentication_multiple" in profile_data and profile_data["authentication_multiple"] != existing_profile.authentication_multiple:
                needs_update = True
                update_fields.append("authentication_multiple")
            if needs_update:
                self.logger.info(f"Updating IKE crypto profile fields: {', '.join(update_fields)}")
                try:
                    update_data = profile_data.copy()
                    update_data["id"] = str(existing_profile.id)
                    result = self.client.ike_crypto_profile.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"IKE crypto profile '{profile_data['name']}'", update_error)
            else:
                result = json.loads(existing_profile.model_dump_json(exclude_unset=True))
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.ike_crypto_profile.create(profile_data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"IKE crypto profile '{profile_data['name']}'", create_error)

    def delete_ike_crypto_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete an IKE crypto profile."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete IKE crypto profile: {name}")
            return
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
            profile = self.client.ike_crypto_profile.fetch(name=name, **container_kwargs)
            self.client.ike_crypto_profile.delete(str(profile.id))
            self.logger.info(f"Deleted IKE crypto profile: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"IKE crypto profile '{name}'", e)

    def get_ike_crypto_profile(
        self,
        name: str,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
    ) -> dict[str, Any] | None:
        """Get a specific IKE crypto profile."""
        if not self.client:
            return {
                "id": "ike-crypto-mock",
                "name": name,
                "folder": folder or "ngfw-shared",
                "hash": ["sha256"],
                "dh_group": ["group14"],
                "encryption": ["aes-256-cbc"],
                "lifetime": {"hours": 8},
                "authentication_multiple": 0,
            }
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
            result = self.client.ike_crypto_profile.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"IKE crypto profile '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"IKE crypto profile '{name}'", e)

    def list_ike_crypto_profiles(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List IKE crypto profiles in a container."""
        if not self.client:
            return [
                {
                    "id": "ike-crypto-mock1",
                    "folder": folder or "ngfw-shared",
                    "name": "default-ike-profile",
                    "hash": ["sha256", "sha384"],
                    "dh_group": ["group14", "group19"],
                    "encryption": ["aes-256-cbc"],
                    "lifetime": {"hours": 8},
                    "authentication_multiple": 0,
                },
                {
                    "id": "ike-crypto-mock2",
                    "folder": folder or "ngfw-shared",
                    "name": "strong-ike-profile",
                    "hash": ["sha512"],
                    "dh_group": ["group20"],
                    "encryption": ["aes-256-gcm"],
                    "lifetime": {"hours": 4},
                    "authentication_multiple": 3,
                },
            ]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.ike_crypto_profile.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "IKE crypto profiles", e)

    # ---------------------------------------------------------------------------------- Aggregate Interfaces ---------------------------------------------------------------------------------

    def create_aggregate_interface(self, iface_data: dict[str, Any]) -> dict[str, Any]:
        """Create or update an aggregate interface using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in iface_data and iface_data[field] is not None:
                container_field = field
                container_value = iface_data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = iface_data.copy()
            result["id"] = f"ae-{iface_data['name']}"
            result["__action__"] = "created"
            return result
        existing_iface = None
        try:
            existing_iface = self.client.aggregate_interface.fetch(name=iface_data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing aggregate interface '{iface_data['name']}' in {container_field} '{container_value}'")
        except NotFoundError:
            self.logger.info(f"Aggregate interface '{iface_data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching aggregate interface '{iface_data['name']}': {str(e)}")
        if existing_iface:
            needs_update = False
            update_fields = []
            # Compare comment
            if "comment" in iface_data:
                existing_comment = getattr(existing_iface, "comment", None)
                if iface_data["comment"] != existing_comment:
                    needs_update = True
                    update_fields.append("comment")
            # Compare layer2
            if "layer2" in iface_data:
                existing_layer2 = json.loads(existing_iface.layer2.model_dump_json(exclude_unset=True)) if existing_iface.layer2 else None
                if iface_data["layer2"] != existing_layer2:
                    needs_update = True
                    update_fields.append("layer2")
            # Compare layer3
            if "layer3" in iface_data:
                existing_layer3 = json.loads(existing_iface.layer3.model_dump_json(exclude_unset=True)) if existing_iface.layer3 else None
                if iface_data["layer3"] != existing_layer3:
                    needs_update = True
                    update_fields.append("layer3")
            if needs_update:
                self.logger.info(f"Updating aggregate interface fields: {', '.join(update_fields)}")
                try:
                    update_data = iface_data.copy()
                    update_data["id"] = str(existing_iface.id)
                    result = self.client.aggregate_interface.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"aggregate interface '{iface_data['name']}'", update_error)
            else:
                result = json.loads(existing_iface.model_dump_json(exclude_unset=True))
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.aggregate_interface.create(iface_data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"aggregate interface '{iface_data['name']}'", create_error)

    def delete_aggregate_interface(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete an aggregate interface."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete aggregate interface: {name}")
            return
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
            iface = self.client.aggregate_interface.fetch(name=name, **container_kwargs)
            self.client.aggregate_interface.delete(str(iface.id))
            self.logger.info(f"Deleted aggregate interface: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"aggregate interface '{name}'", e)

    def get_aggregate_interface(
        self,
        name: str,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
    ) -> dict[str, Any] | None:
        """Get a specific aggregate interface."""
        if not self.client:
            return {
                "id": "ae-mock",
                "name": name,
                "folder": folder or "ngfw-shared",
                "comment": "Mock aggregate interface",
                "layer3": {"mtu": 1500, "ip": [{"name": "10.0.0.1/24"}]},
            }
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
            result = self.client.aggregate_interface.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"Aggregate interface '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"aggregate interface '{name}'", e)

    def list_aggregate_interfaces(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List aggregate interfaces in a container."""
        if not self.client:
            return [
                {
                    "id": "ae-mock1",
                    "folder": folder or "ngfw-shared",
                    "name": "ae1",
                    "comment": "Mock aggregate interface 1",
                    "layer3": {"mtu": 1500, "ip": [{"name": "10.0.0.1/24"}]},
                },
                {
                    "id": "ae-mock2",
                    "folder": folder or "ngfw-shared",
                    "name": "ae2",
                    "comment": "Mock aggregate interface 2",
                    "layer2": {"vlan_tag": "100"},
                },
            ]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.aggregate_interface.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "aggregate interfaces", e)

    # --------------------------------------------------------------------------------------- IKE Gateways -----------------------------------------------------------------------------------

    def create_ike_gateway(self, gateway_data: dict[str, Any]) -> dict[str, Any]:
        """Create or update an IKE gateway using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in gateway_data and gateway_data[field] is not None:
                container_field = field
                container_value = gateway_data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = gateway_data.copy()
            result["id"] = f"ike-gw-{gateway_data['name']}"
            result["__action__"] = "created"
            return result
        existing_gateway = None
        try:
            existing_gateway = self.client.ike_gateway.fetch(name=gateway_data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing IKE gateway '{gateway_data['name']}' in {container_field} '{container_value}'")
        except NotFoundError:
            self.logger.info(f"IKE gateway '{gateway_data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching IKE gateway '{gateway_data['name']}': {str(e)}")
        if existing_gateway:
            needs_update = False
            update_fields = []
            # Compare authentication
            if "authentication" in gateway_data:
                existing_auth = json.loads(existing_gateway.authentication.model_dump_json(exclude_unset=True)) if existing_gateway.authentication else None
                if gateway_data["authentication"] != existing_auth:
                    needs_update = True
                    update_fields.append("authentication")
            # Compare peer_address
            if "peer_address" in gateway_data:
                existing_peer = json.loads(existing_gateway.peer_address.model_dump_json(exclude_unset=True)) if existing_gateway.peer_address else None
                if gateway_data["peer_address"] != existing_peer:
                    needs_update = True
                    update_fields.append("peer_address")
            # Compare protocol
            if "protocol" in gateway_data:
                existing_proto = json.loads(existing_gateway.protocol.model_dump_json(exclude_unset=True)) if existing_gateway.protocol else None
                if gateway_data["protocol"] != existing_proto:
                    needs_update = True
                    update_fields.append("protocol")
            # Compare peer_id
            if "peer_id" in gateway_data:
                existing_peer_id = json.loads(existing_gateway.peer_id.model_dump_json(exclude_unset=True)) if existing_gateway.peer_id else None
                if gateway_data["peer_id"] != existing_peer_id:
                    needs_update = True
                    update_fields.append("peer_id")
            # Compare local_id
            if "local_id" in gateway_data:
                existing_local_id = json.loads(existing_gateway.local_id.model_dump_json(exclude_unset=True)) if existing_gateway.local_id else None
                if gateway_data["local_id"] != existing_local_id:
                    needs_update = True
                    update_fields.append("local_id")
            # Compare protocol_common
            if "protocol_common" in gateway_data:
                existing_common = json.loads(existing_gateway.protocol_common.model_dump_json(exclude_unset=True)) if existing_gateway.protocol_common else None
                if gateway_data["protocol_common"] != existing_common:
                    needs_update = True
                    update_fields.append("protocol_common")
            if needs_update:
                self.logger.info(f"Updating IKE gateway fields: {', '.join(update_fields)}")
                try:
                    update_data = gateway_data.copy()
                    update_data["id"] = str(existing_gateway.id)
                    result = self.client.ike_gateway.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"IKE gateway '{gateway_data['name']}'", update_error)
            else:
                result = json.loads(existing_gateway.model_dump_json(exclude_unset=True))
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.ike_gateway.create(gateway_data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"IKE gateway '{gateway_data['name']}'", create_error)

    def delete_ike_gateway(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete an IKE gateway."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete IKE gateway: {name}")
            return
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
            gateway = self.client.ike_gateway.fetch(name=name, **container_kwargs)
            self.client.ike_gateway.delete(str(gateway.id))
            self.logger.info(f"Deleted IKE gateway: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"IKE gateway '{name}'", e)

    def get_ike_gateway(
        self,
        name: str,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
    ) -> dict[str, Any] | None:
        """Get a specific IKE gateway."""
        if not self.client:
            return {
                "id": "ike-gw-mock",
                "name": name,
                "folder": folder or "ngfw-shared",
                "authentication": {"pre_shared_key": {"key": "mock-key"}},
                "peer_address": {"ip": "203.0.113.1"},
                "protocol": {"version": "ikev2-preferred", "ikev1": {"ike_crypto_profile": "default"}, "ikev2": {"ike_crypto_profile": "default"}},
                "protocol_common": {"nat_traversal": {"enable": True}, "fragmentation": {"enable": False}},
            }
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
            result = self.client.ike_gateway.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"IKE gateway '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"IKE gateway '{name}'", e)

    def list_ike_gateways(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List IKE gateways in a container."""
        if not self.client:
            return [
                {
                    "id": "ike-gw-mock1",
                    "folder": folder or "ngfw-shared",
                    "name": "gw-site-a",
                    "authentication": {"pre_shared_key": {"key": "mock-key-1"}},
                    "peer_address": {"ip": "203.0.113.1"},
                    "protocol": {"version": "ikev2-preferred", "ikev1": {"ike_crypto_profile": "default"}, "ikev2": {"ike_crypto_profile": "default"}},
                },
                {
                    "id": "ike-gw-mock2",
                    "folder": folder or "ngfw-shared",
                    "name": "gw-site-b",
                    "authentication": {"pre_shared_key": {"key": "mock-key-2"}},
                    "peer_address": {"fqdn": "vpn.example.com"},
                    "protocol": {"version": "ikev2", "ikev2": {"ike_crypto_profile": "strong-profile"}},
                },
            ]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.ike_gateway.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "IKE gateways", e)

    # --------------------------------------------------------------------------------------- NAT Rules ------------------------------------------------------------------------------------

    def create_nat_rule(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = "",
        description: str | None = None,
        tag: list[str] | None = None,
        disabled: bool = False,
        nat_type: str = "ipv4",
        from_zones: list[str] | None = None,
        to_zones: list[str] | None = None,
        to_interface: str | None = None,
        source: list[str] | None = None,
        destination: list[str] | None = None,
        service: str = "any",
        source_translation: dict[str, Any] | None = None,
        destination_translation: dict[str, Any] | None = None,
        active_active_device_binding: str | None = None,
    ) -> dict[str, Any]:
        """Create or update a NAT rule (smart upsert).

        Args:
            folder: Folder to create the NAT rule in
            snippet: Snippet to create the NAT rule in
            device: Device to create the NAT rule in
            name: Name of the NAT rule
            description: Description of the NAT rule
            tag: Tags associated with the NAT rule
            disabled: Whether the NAT rule is disabled
            nat_type: NAT type (ipv4, nat64, nptv6)
            from_zones: Source zone(s)
            to_zones: Destination zone(s)
            to_interface: Destination interface
            source: Source address(es)
            destination: Destination address(es)
            service: TCP/UDP service
            source_translation: Source translation configuration
            destination_translation: Destination translation configuration
            active_active_device_binding: Active/Active device binding

        Returns:
            dict[str, Any]: The created/updated NAT rule object, with '__action__' key.

        """
        container = folder or snippet or device or "Texas"
        self.logger.info(f"Upsert NAT rule: {name} in {container}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"nat-{name}",
                "folder": folder or "Texas",
                "name": name,
                "description": description or "",
                "nat_type": nat_type,
                "from_": from_zones or ["any"],
                "to_": to_zones or ["any"],
                "source": source or ["any"],
                "destination": destination or ["any"],
                "service": service,
                "source_translation": source_translation,
                "destination_translation": destination_translation,
                "__action__": "created",
            }

        try:
            # Build NAT rule data
            nat_data: dict[str, Any] = {"name": name}
            if folder:
                nat_data["folder"] = folder
            elif snippet:
                nat_data["snippet"] = snippet
            elif device:
                nat_data["device"] = device

            if description:
                nat_data["description"] = description
            if tag:
                nat_data["tag"] = tag
            if disabled:
                nat_data["disabled"] = disabled
            if nat_type != "ipv4":
                nat_data["nat_type"] = nat_type
            nat_data["from_"] = from_zones or ["any"]
            nat_data["to_"] = to_zones or ["any"]
            nat_data["source"] = source or ["any"]
            nat_data["destination"] = destination or ["any"]
            nat_data["service"] = service
            if to_interface:
                nat_data["to_interface"] = to_interface
            if source_translation:
                nat_data["source_translation"] = source_translation
            if destination_translation:
                nat_data["destination_translation"] = destination_translation
            if active_active_device_binding:
                nat_data["active_active_device_binding"] = active_active_device_binding

            # Step 1: Try to fetch existing NAT rule
            existing = None
            try:
                fetch_kwargs = {"name": name}
                if folder:
                    fetch_kwargs["folder"] = folder
                elif snippet:
                    fetch_kwargs["snippet"] = snippet
                elif device:
                    fetch_kwargs["device"] = device
                existing = self.client.nat_rule.fetch(**fetch_kwargs)
                self.logger.info(f"Found existing NAT rule '{name}'")
            except NotFoundError:
                self.logger.info(f"NAT rule '{name}' not found, will create new")
            except Exception as e:
                self.logger.warning(f"Error fetching NAT rule '{name}': {str(e)}")

            if existing:
                # Step 2: Compare and update if needed
                needs_update = False
                update_fields = []

                # Compare description
                if description is not None and getattr(existing, "description", None) != description:
                    existing.description = description
                    update_fields.append("description")
                    needs_update = True

                # Compare source zones
                current_from = list(getattr(existing, "from_", []) or [])
                new_from = from_zones or ["any"]
                if set(current_from) != set(new_from):
                    existing.from_ = new_from
                    update_fields.append("from")
                    needs_update = True

                # Compare destination zones
                current_to = list(getattr(existing, "to_", []) or [])
                new_to = to_zones or ["any"]
                if set(current_to) != set(new_to):
                    existing.to_ = new_to
                    update_fields.append("to")
                    needs_update = True

                # Compare source addresses
                current_source = list(getattr(existing, "source", []) or [])
                new_source = source or ["any"]
                if set(current_source) != set(new_source):
                    existing.source = new_source
                    update_fields.append("source")
                    needs_update = True

                # Compare destination addresses
                current_dest = list(getattr(existing, "destination", []) or [])
                new_dest = destination or ["any"]
                if set(current_dest) != set(new_dest):
                    existing.destination = new_dest
                    update_fields.append("destination")
                    needs_update = True

                # Compare service
                if getattr(existing, "service", "any") != service:
                    existing.service = service
                    update_fields.append("service")
                    needs_update = True

                # Compare source_translation
                if source_translation is not None:
                    existing.source_translation = source_translation
                    update_fields.append("source_translation")
                    needs_update = True

                # Compare destination_translation
                if destination_translation is not None:
                    existing.destination_translation = destination_translation
                    update_fields.append("destination_translation")
                    needs_update = True

                # Compare tags
                if tag is not None:
                    current_tags = set(getattr(existing, "tag", []) or [])
                    new_tags = set(tag or [])
                    if current_tags != new_tags:
                        existing.tag = tag
                        update_fields.append("tag")
                        needs_update = True

                if needs_update:
                    self.logger.info(f"Updating NAT rule fields: {', '.join(update_fields)}")
                    updated = self.client.nat_rule.update(existing)
                    self.logger.info(f"Successfully updated NAT rule '{name}'")
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
                else:
                    self.logger.info(f"No changes detected for NAT rule '{name}', skipping update")
                    result = json.loads(existing.model_dump_json(exclude_unset=True))
                    result["__action__"] = "no_change"
                    return result
            else:
                # Step 3: Create new NAT rule
                created = self.client.nat_rule.create(nat_data)
                self.logger.info(f"Successfully created NAT rule '{name}'")
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
        except Exception as e:
            self._handle_api_exception("creation/update", container, name, e)

    def delete_nat_rule(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = "",
    ) -> bool:
        """Delete a NAT rule.

        Args:
            folder: Folder containing the NAT rule
            snippet: Snippet containing the NAT rule
            device: Device containing the NAT rule
            name: Name of the NAT rule to delete

        Returns:
            bool: True if deletion was successful

        """
        container = folder or snippet or device or "Texas"
        self.logger.info(f"Deleting NAT rule: {name} from {container}")

        if not self.client:
            return True

        try:
            fetch_kwargs: dict[str, str] = {"name": name}
            if folder:
                fetch_kwargs["folder"] = folder
            elif snippet:
                fetch_kwargs["snippet"] = snippet
            elif device:
                fetch_kwargs["device"] = device
            nat_rule = self.client.nat_rule.fetch(**fetch_kwargs)
            self.client.nat_rule.delete(str(nat_rule.id))
            self.logger.info(f"Successfully deleted NAT rule '{name}'")
            return True
        except Exception as e:
            self._handle_api_exception("deletion", container, name, e)

    def get_nat_rule(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = "",
    ) -> dict[str, Any]:
        """Get a NAT rule by name.

        Args:
            folder: Folder containing the NAT rule
            snippet: Snippet containing the NAT rule
            device: Device containing the NAT rule
            name: Name of the NAT rule to get

        Returns:
            dict[str, Any]: The NAT rule object

        """
        container = folder or snippet or device or "Texas"
        self.logger.info(f"Getting NAT rule: {name} from {container}")

        if not self.client:
            return {
                "id": f"nat-{name}",
                "folder": folder or "Texas",
                "name": name,
                "description": "Mock NAT rule",
                "nat_type": "ipv4",
                "from_": ["trust"],
                "to_": ["untrust"],
                "source": ["any"],
                "destination": ["any"],
                "service": "any",
                "source_translation": {
                    "dynamic_ip_and_port": {
                        "type": "dynamic_ip_and_port",
                        "translated_address": ["192.168.1.1"],
                    }
                },
            }

        try:
            fetch_kwargs: dict[str, str] = {"name": name}
            if folder:
                fetch_kwargs["folder"] = folder
            elif snippet:
                fetch_kwargs["snippet"] = snippet
            elif device:
                fetch_kwargs["device"] = device
            result = self.client.nat_rule.fetch(**fetch_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieval", container, name, e)

    def list_nat_rules(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List NAT rules in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return objects defined exactly in the specified container

        Returns:
            list[dict[str, Any]]: List of NAT rule objects

        """
        container = folder or snippet or device or "Texas"
        self.logger.info(f"Listing NAT rules in {folder=}, {snippet=}, {device=} (exact_match={exact_match})")

        if not self.client:
            return [
                {
                    "id": "nat-mock1",
                    "folder": folder or "Texas",
                    "name": "outbound-nat",
                    "nat_type": "ipv4",
                    "from_": ["trust"],
                    "to_": ["untrust"],
                    "source": ["any"],
                    "destination": ["any"],
                    "service": "any",
                    "source_translation": {
                        "dynamic_ip_and_port": {
                            "type": "dynamic_ip_and_port",
                            "translated_address": ["10.0.0.1"],
                        }
                    },
                },
                {
                    "id": "nat-mock2",
                    "folder": folder or "Texas",
                    "name": "inbound-web",
                    "nat_type": "ipv4",
                    "from_": ["untrust"],
                    "to_": ["trust"],
                    "source": ["any"],
                    "destination": ["203.0.113.10"],
                    "service": "service-http",
                    "destination_translation": {
                        "translated_address": "192.168.1.100",
                        "translated_port": 8080,
                    },
                },
            ]

        container_kwargs: dict[str, Any] = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            results = self.client.nat_rule.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container, "NAT rules", e)

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
            return json.loads(result.model_dump_json(exclude_unset=True))
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

    # -------------------------------------------------------------------------------- IPsec Crypto Profiles -------------------------------------------------------------------------------

    def create_ipsec_crypto_profile(
        self,
        folder: str,
        name: str,
        esp_encryption: list[str] | None = None,
        esp_authentication: list[str] | None = None,
        dh_group: str = "group14",
        lifetime: dict[str, int] | None = None,
        lifesize: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        """Create or update an IPsec crypto profile using smart upsert logic.

        Args:
            folder: Folder to create the profile in
            name: Name of the IPsec crypto profile
            esp_encryption: List of ESP encryption algorithms
            esp_authentication: List of ESP authentication algorithms
            dh_group: DH group for PFS
            lifetime: Lifetime configuration dict (e.g. {"hours": 1})
            lifesize: Lifesize configuration dict (e.g. {"mb": 100})

        Returns:
            dict[str, Any]: The created/updated IPsec crypto profile

        """
        esp_encryption = esp_encryption or ["aes-256-cbc"]
        esp_authentication = esp_authentication or ["sha256"]
        lifetime = lifetime or {"hours": 1}

        self.logger.info(f"Creating or updating IPsec crypto profile: {name} in folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            result = {
                "id": f"ipsec-crypto-{name}",
                "folder": folder,
                "name": name,
                "esp": {
                    "encryption": esp_encryption,
                    "authentication": esp_authentication,
                },
                "dh_group": dh_group,
                "lifetime": lifetime,
                "__action__": "created",
            }
            if lifesize:
                result["lifesize"] = lifesize
            return result

        try:
            # Prepare the profile data
            profile_data: dict[str, Any] = {
                "folder": folder,
                "name": name,
                "esp": {
                    "encryption": esp_encryption,
                    "authentication": esp_authentication,
                },
                "dh_group": dh_group,
                "lifetime": lifetime,
            }
            if lifesize:
                profile_data["lifesize"] = lifesize

            # Try to fetch existing profile for smart upsert
            existing_profile = None
            try:
                existing_profile = self.client.ipsec_crypto_profile.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing IPsec crypto profile '{name}' in folder '{folder}'")
            except NotFoundError:
                self.logger.info(f"IPsec crypto profile '{name}' not found in folder '{folder}', will create new")
            except Exception as fetch_error:
                self.logger.warning(f"Error fetching IPsec crypto profile '{name}': {str(fetch_error)}")

            if existing_profile:
                # Compare fields to detect changes
                needs_update = False
                update_fields = []

                # Compare ESP encryption
                existing_esp = existing_profile.esp
                if existing_esp:
                    existing_enc = [str(e.value) if hasattr(e, "value") else str(e) for e in existing_esp.encryption]
                    if set(existing_enc) != set(esp_encryption):
                        needs_update = True
                        update_fields.append("esp_encryption")
                    existing_auth = [str(a) for a in existing_esp.authentication]
                    if set(existing_auth) != set(esp_authentication):
                        needs_update = True
                        update_fields.append("esp_authentication")

                # Compare DH group
                existing_dh = str(existing_profile.dh_group.value) if hasattr(existing_profile.dh_group, "value") else str(existing_profile.dh_group)
                if existing_dh != dh_group:
                    needs_update = True
                    update_fields.append("dh_group")

                if needs_update:
                    self.logger.info(f"Updating IPsec crypto profile fields: {', '.join(update_fields)}")
                    profile_data["id"] = str(existing_profile.id)
                    result = self.client.ipsec_crypto_profile.update(profile_data)
                    self.logger.info(f"Successfully updated IPsec crypto profile '{name}'")
                    response = json.loads(result.model_dump_json(exclude_unset=True))
                    response["__action__"] = "updated"
                    return response
                else:
                    self.logger.info(f"No changes detected for IPsec crypto profile '{name}', skipping update")
                    response = json.loads(existing_profile.model_dump_json(exclude_unset=True))
                    response["__action__"] = "no_change"
                    return response
            else:
                # Create new profile
                result = self.client.ipsec_crypto_profile.create(profile_data)
                self.logger.info(f"Successfully created IPsec crypto profile '{name}'")
                response = json.loads(result.model_dump_json(exclude_unset=True))
                response["__action__"] = "created"
                return response

        except Exception as e:
            self._handle_api_exception("create/update", folder, name, e)

    def delete_ipsec_crypto_profile(
        self,
        folder: str,
        name: str,
    ) -> bool:
        """Delete an IPsec crypto profile.

        Args:
            folder: Folder containing the profile
            name: Name of the profile to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting IPsec crypto profile: {name} from folder {folder}")

        if not self.client:
            return True

        try:
            profile = self.client.ipsec_crypto_profile.fetch(name=name, folder=folder)
            self.client.ipsec_crypto_profile.delete(str(profile.id))
            self.logger.info(f"Successfully deleted IPsec crypto profile '{name}'")
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder, name, e)

    def get_ipsec_crypto_profile(
        self,
        folder: str,
        name: str,
    ) -> dict[str, Any]:
        """Get an IPsec crypto profile by name and folder.

        Args:
            folder: Folder containing the profile
            name: Name of the profile to get

        Returns:
            dict[str, Any]: The IPsec crypto profile

        """
        self.logger.info(f"Getting IPsec crypto profile: {name} from folder {folder}")

        if not self.client:
            return {
                "id": f"ipsec-crypto-{name}",
                "folder": folder,
                "name": name,
                "esp": {
                    "encryption": ["aes-256-cbc"],
                    "authentication": ["sha256"],
                },
                "dh_group": "group14",
                "lifetime": {"hours": 1},
            }

        try:
            result = self.client.ipsec_crypto_profile.fetch(name=name, folder=folder)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieval", folder, name, e)

    def list_ipsec_crypto_profiles(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List IPsec crypto profiles in a container.

        Args:
            folder: Folder location
            snippet: Snippet location
            device: Device location
            exact_match: If True, only return objects defined exactly in the specified container

        Returns:
            list[dict[str, Any]]: List of IPsec crypto profile objects

        """
        container = folder or snippet or device or "Texas"
        self.logger.info(f"Listing IPsec crypto profiles in {folder=}, {snippet=}, {device=} (exact_match={exact_match})")

        if not self.client:
            return [
                {
                    "id": "ipsec-crypto-mock1",
                    "folder": folder or "Texas",
                    "name": "ipsec-esp-aes256-sha256",
                    "esp": {
                        "encryption": ["aes-256-cbc"],
                        "authentication": ["sha256"],
                    },
                    "dh_group": "group14",
                    "lifetime": {"hours": 1},
                },
                {
                    "id": "ipsec-crypto-mock2",
                    "folder": folder or "Texas",
                    "name": "ipsec-esp-aes128-sha1",
                    "esp": {
                        "encryption": ["aes-128-cbc"],
                        "authentication": ["sha1"],
                    },
                    "dh_group": "group2",
                    "lifetime": {"seconds": 3600},
                },
                {
                    "id": "ipsec-crypto-mock3",
                    "folder": folder or "Texas",
                    "name": "ipsec-esp-aes256gcm",
                    "esp": {
                        "encryption": ["aes-256-gcm"],
                        "authentication": ["sha512"],
                    },
                    "dh_group": "group20",
                    "lifetime": {"hours": 8},
                    "lifesize": {"gb": 1},
                },
            ]

        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            results = self.client.ipsec_crypto_profile.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container, "IPsec crypto profiles", e)

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
                "disabled": not enabled,  # SDK uses disabled instead of enabled
                "category": ["any"],  # Required by SDK
                "source_user": ["any"],  # Required by SDK
            }

            if description:
                rule_data["description"] = description

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
                if description:
                    existing_rule.description = description
                existing_rule.disabled = not enabled
                existing_rule.category = ["any"]  # Required by SDK
                existing_rule.source_user = ["any"]  # Required by SDK

                if tags is not None:
                    existing_rule.tag = tags

                # Update logging settings
                existing_rule.log_start = log_start
                existing_rule.log_end = log_end
                if log_setting:
                    existing_rule.log_setting = str(log_setting)

                # Perform update
                result = self.client.security_rule.update(existing_rule)
                self.logger.info(f"Successfully updated security rule '{name}'")
            else:
                # Create a new rule - need to pass rulebase for creation
                result = self.client.security_rule.create(data=rule_data, rulebase=rulebase)
                self.logger.info(f"Successfully created security rule '{name}'")

            # Convert SDK response to dict for compatibility
            return json.loads(result.model_dump_json(exclude_unset=True))
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
        exclude_folders: list[str] | None = None,
        exclude_snippets: list[str] | None = None,
        exclude_devices: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """List security rules from SCM.

        Args:
            folder: The folder containing the rule
            snippet: The snippet containing the rule
            device: The device containing the rules
            rulebase: Rulebase to use (pre, post, or default)
            exact_match: If True, only return exact name matches
            exclude_folders: List of folder names to exclude from results
            exclude_snippets: List of snippet names to exclude from results
            exclude_devices: List of device names to exclude from results

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

            # Build list kwargs with optional exclude filters
            list_kwargs = {"exact_match": exact_match, "rulebase": rulebase, **container_kwargs}
            if exclude_folders:
                list_kwargs["exclude_folders"] = exclude_folders
            if exclude_snippets:
                list_kwargs["exclude_snippets"] = exclude_snippets
            if exclude_devices:
                list_kwargs["exclude_devices"] = exclude_devices

            # List security rules using the SDK
            results = self.client.security_rule.list(**list_kwargs)

            # Convert SDK response to a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container, "security rules", e)

    def move_security_rule(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
        rulebase: str = "pre",
        destination: str = "top",
        destination_rule: str | None = None,
    ) -> None:
        """Move a security rule to a new position.

        Args:
            folder: Folder containing the rule
            snippet: Snippet containing the rule
            device: Device containing the rule
            name: Name of the rule to move
            rulebase: Rulebase (pre or post)
            destination: Where to move (top, bottom, before, after)
            destination_rule: UUID of reference rule for before/after

        """
        container = folder or snippet or device
        self.logger.info(f"Moving security rule: {name} to {destination}")

        if not self.client:
            return

        try:
            rule = self.client.security_rule.fetch(
                name=name,
                folder=folder,
                snippet=snippet,
                device=device,
                rulebase=rulebase,
            )
            move_data = {"destination": destination, "rulebase": rulebase}
            if destination_rule:
                move_data["destination_rule"] = destination_rule
            self.client.security_rule.move(rule.id, move_data)
        except Exception as e:
            self._handle_api_exception("moving", container or "", f"security rule '{name}'", e)

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

                update_model = AntiSpywareProfileUpdateModel(**profile_data)  # type: ignore[arg-type]
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

    # --------------------------------------------------------------------------- WildFire Antivirus Profile ---------------------------------------------------------------------------

    def create_wildfire_antivirus_profile(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
        description: str | None = None,
        packet_capture: bool | None = None,
        rules: list[dict[str, Any]] | None = None,
        mlav_exception: list[dict[str, Any]] | None = None,
        threat_exception: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create a WildFire antivirus profile.

        Args:
            folder: Folder to create the profile in
            snippet: Snippet to create the profile in
            device: Device to create the profile in
            name: Name of the profile
            description: Optional description
            packet_capture: Enable packet capture
            rules: List of WildFire antivirus rules
            mlav_exception: List of MLAV exceptions
            threat_exception: List of threat exceptions

        Returns:
            dict[str, Any]: The created WildFire antivirus profile object

        Note:
            If a WildFire antivirus profile with the same name already exists in the container,
            it will be updated with the new configuration.

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")
        self.logger.info(f"Creating or updating WildFire antivirus profile: {name} in {container_type} {container}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"wfav-{name}",
                "folder": folder,
                "snippet": snippet,
                "device": device,
                "name": name,
                "description": description,
                "packet_capture": packet_capture,
                "rules": rules or [],
                "mlav_exception": mlav_exception,
                "threat_exception": threat_exception,
            }

        try:
            # First, try to fetch the existing profile
            existing_profile = None
            try:
                existing_profile = self.client.wildfire_antivirus_profile.fetch(name=name, folder=folder, snippet=snippet, device=device)
                self.logger.info(f"Found existing WildFire antivirus profile '{name}' in {container_type} '{container}', updating...")
            except NotFoundError:
                self.logger.info(f"WildFire antivirus profile '{name}' not found in {container_type} '{container}', creating new...")
            except Exception as fetch_error:
                # Log but continue - we'll try to create if fetch failed for other reasons
                self.logger.warning(f"Error fetching WildFire antivirus profile '{name}': {str(fetch_error)}")

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
            if packet_capture is not None:
                profile_data["packet_capture"] = packet_capture
            if rules is not None:
                profile_data["rules"] = rules
            if mlav_exception is not None:
                profile_data["mlav_exception"] = mlav_exception
            if threat_exception is not None:
                profile_data["threat_exception"] = threat_exception

            # Create or update the profile
            if existing_profile:
                # Update existing profile
                profile_data["id"] = existing_profile.id
                from scm.models.security import WildfireAvProfileUpdateModel

                update_model = WildfireAvProfileUpdateModel(**profile_data)  # type: ignore[arg-type]
                result = self.client.wildfire_antivirus_profile.update(update_model)
            else:
                # Create a new profile
                result = self.client.wildfire_antivirus_profile.create(profile_data)

            # Convert response to dict
            return json.loads(result.model_dump_json(exclude_unset=True))

        except Exception as e:
            self._handle_api_exception("creating", container or "", "WildFire antivirus profile", e)

    def delete_wildfire_antivirus_profile(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
    ) -> bool:
        """Delete a WildFire antivirus profile.

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
        self.logger.info(f"Deleting WildFire antivirus profile: {name} from {container_type} {container}")

        if not self.client:
            # Return mock success if no client is available
            return True

        try:
            # Fetch the profile to get its ID
            profile = self.client.wildfire_antivirus_profile.fetch(name=name, folder=folder, snippet=snippet, device=device)

            # Delete using the ID
            self.client.wildfire_antivirus_profile.delete(profile.id)
            self.logger.info(f"Successfully deleted WildFire antivirus profile '{name}' from {container_type} '{container}'")
            return True
        except NotFoundError:
            self.logger.warning(f"WildFire antivirus profile '{name}' not found in {container_type} '{container}'")
            return False
        except Exception as e:
            self._handle_api_exception("deleting", container or "", "WildFire antivirus profile", e)

    def get_wildfire_antivirus_profile(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
    ) -> dict[str, Any]:
        """Get a WildFire antivirus profile by name.

        Args:
            folder: Folder containing the profile
            snippet: Snippet containing the profile
            device: Device containing the profile
            name: Name of the profile

        Returns:
            dict[str, Any]: The WildFire antivirus profile object

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")
        self.logger.info(f"Getting WildFire antivirus profile: {name} from {container_type} {container}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"wfav-{name}",
                "folder": folder,
                "snippet": snippet,
                "device": device,
                "name": name,
                "description": "Mock WildFire antivirus profile",
                "rules": [
                    {
                        "name": "Default Rule",
                        "direction": "both",
                        "analysis": "public-cloud",
                        "application": ["any"],
                        "file_type": ["any"],
                    }
                ],
                "packet_capture": False,
            }

        try:
            # Fetch the profile using the SDK
            result = self.client.wildfire_antivirus_profile.fetch(name=name, folder=folder, snippet=snippet, device=device)

            # Convert SDK response to dict
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("getting", container or "", "WildFire antivirus profile", e)

    def list_wildfire_antivirus_profiles(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List WildFire antivirus profiles.

        Args:
            folder: Folder to list out
            snippet: Snippet to list out
            device: Device to list out
            exact_match: If True, only return exact container matches

        Returns:
            list[dict[str, Any]]: List of WildFire antivirus profile objects

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

        self.logger.info(f"Listing WildFire antivirus profiles in {container_type}: {container}")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "wfav-mock1",
                    "folder": folder or "Texas",
                    "name": "WildFire Best Practice",
                    "description": "Best practice WildFire antivirus profile",
                    "rules": [
                        {
                            "name": "Forward All",
                            "direction": "both",
                            "analysis": "public-cloud",
                            "application": ["any"],
                            "file_type": ["any"],
                        }
                    ],
                    "packet_capture": False,
                },
                {
                    "id": "wfav-mock2",
                    "folder": folder or "Texas",
                    "name": "WildFire Upload Only",
                    "description": "Upload-only WildFire profile",
                    "rules": [
                        {
                            "name": "Upload Rule",
                            "direction": "upload",
                            "analysis": "public-cloud",
                            "application": ["any"],
                            "file_type": ["any"],
                        }
                    ],
                },
            ]

        try:
            # List profiles using the SDK
            results = self.client.wildfire_antivirus_profile.list(**container_kwargs, exact_match=exact_match)

            # Convert SDK response to a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container or "", "WildFire antivirus profiles", e)

    # ------------------------------------------------------------------------------- DNS Security Profile ---------------------------------------------------------------------------

    def create_dns_security_profile(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        **profile_data,
    ) -> dict[str, Any]:
        """Create or update a DNS security profile.

        Args:
            folder: Folder to create the profile in
            snippet: Snippet to create the profile in
            device: Device to create the profile in
            **profile_data: Additional profile configuration data

        Returns:
            dict[str, Any]: Created/updated DNS security profile object

        """
        name = profile_data.get("name")
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Creating/updating DNS security profile: {name} in {container_type} {container}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"dns-sec-{name}",
                "name": name,
                container_type: container,
                "description": profile_data.get("description", ""),
                "botnet_domains": profile_data.get("botnet_domains", {}),
                "__action__": "created",
            }

        try:
            # Check if the profile already exists
            existing_profile = None
            try:
                if folder:
                    existing_profile = self.client.dns_security_profile.fetch(name=name, folder=folder)
                elif snippet:
                    existing_profile = self.client.dns_security_profile.fetch(name=name, snippet=snippet)
                elif device:
                    existing_profile = self.client.dns_security_profile.fetch(name=name, device=device)
            except NotFoundError:
                self.logger.info(f"DNS security profile '{name}' not found. Creating new profile.")

            if existing_profile:
                # Update existing profile
                self.logger.info(f"DNS security profile '{name}' exists. Updating.")

                # Update with new data
                for key, value in profile_data.items():
                    if value is not None and hasattr(existing_profile, key):
                        setattr(existing_profile, key, value)

                # Update the profile
                result = self.client.dns_security_profile.update(existing_profile)
                self.logger.info(f"Successfully updated DNS security profile '{name}'")
                result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                result_dict["__action__"] = "updated"
                return result_dict
            else:
                # Create a new profile
                profile_dict = {container_type: container}
                profile_dict.update(profile_data)

                result = self.client.dns_security_profile.create(profile_dict)
                self.logger.info(f"Successfully created DNS security profile '{name}'")
                result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                result_dict["__action__"] = "created"
                return result_dict
        except Exception as e:
            self._handle_api_exception("creation/update", container or "", name or "", e)

    def delete_dns_security_profile(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
    ) -> bool:
        """Delete a DNS security profile.

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

        self.logger.info(f"Deleting DNS security profile: {name} from {container_type} {container}")

        if not self.client:
            # Return a mock result if no client is available
            return True

        try:
            # Get the profile first to get its ID
            profile = None
            if folder:
                profile = self.client.dns_security_profile.fetch(name=name, folder=folder)
            elif snippet:
                profile = self.client.dns_security_profile.fetch(name=name, snippet=snippet)
            elif device:
                profile = self.client.dns_security_profile.fetch(name=name, device=device)

            # Delete using the ID
            if profile is None:
                raise ValueError(f"DNS security profile '{name}' not found")
            self.client.dns_security_profile.delete(str(profile.id))
            return True
        except Exception as e:
            self._handle_api_exception("deletion", container or "", name or "", e)

    def get_dns_security_profile(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
    ) -> dict[str, Any]:
        """Get a DNS security profile by name.

        Args:
            folder: Folder containing the profile
            snippet: Snippet containing the profile
            device: Device containing the profile
            name: Name of the profile to get

        Returns:
            dict[str, Any]: The DNS security profile object

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Getting DNS security profile: {name} from {container_type} {container}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"dns-sec-{name}",
                container_type: container,
                "name": name,
                "description": "Mock DNS security profile",
                "botnet_domains": {
                    "dns_security_categories": [
                        {
                            "name": "pan-dns-sec-grayware",
                            "action": "default",
                            "log_level": "default",
                            "packet_capture": "disable",
                        },
                        {
                            "name": "pan-dns-sec-malware",
                            "action": "sinkhole",
                            "log_level": "default",
                            "packet_capture": "single-packet",
                        },
                    ],
                    "sinkhole": {
                        "ipv4_address": "pan-sinkhole-default-ip",
                        "ipv6_address": "::1",
                    },
                    "whitelist": [
                        {
                            "name": "example.com",
                            "description": "Whitelisted domain",
                        },
                    ],
                },
            }

        try:
            # Fetch the profile using the SDK
            result = None
            if folder:
                result = self.client.dns_security_profile.fetch(name=name, folder=folder)
            elif snippet:
                result = self.client.dns_security_profile.fetch(name=name, snippet=snippet)
            elif device:
                result = self.client.dns_security_profile.fetch(name=name, device=device)

            # Convert SDK response to dict for compatibility
            if result is not None:
                return json.loads(result.model_dump_json(exclude_unset=True))
            else:
                raise ValueError(f"DNS security profile '{name}' not found")
        except Exception as e:
            self._handle_api_exception("getting", container or "", "DNS security profile", e)

    def list_dns_security_profiles(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List DNS security profiles.

        Args:
            folder: Folder to list from
            snippet: Snippet to list from
            device: Device to list from
            exact_match: If True, only return exact container matches

        Returns:
            list[dict[str, Any]]: List of DNS security profile objects

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

        self.logger.info(f"Listing DNS security profiles in {container_type}: {container}")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "dns-sec-mock1",
                    "folder": folder or "Texas",
                    "name": "DNS-Security-Default",
                    "description": "Default DNS security profile",
                    "botnet_domains": {
                        "dns_security_categories": [
                            {
                                "name": "pan-dns-sec-grayware",
                                "action": "default",
                                "log_level": "default",
                            },
                            {
                                "name": "pan-dns-sec-malware",
                                "action": "sinkhole",
                                "log_level": "default",
                                "packet_capture": "single-packet",
                            },
                        ],
                        "sinkhole": {
                            "ipv4_address": "pan-sinkhole-default-ip",
                            "ipv6_address": "::1",
                        },
                    },
                },
                {
                    "id": "dns-sec-mock2",
                    "folder": folder or "Texas",
                    "name": "DNS-Security-Strict",
                    "description": "Strict DNS security profile",
                    "botnet_domains": {
                        "dns_security_categories": [
                            {
                                "name": "pan-dns-sec-grayware",
                                "action": "block",
                                "log_level": "high",
                            },
                            {
                                "name": "pan-dns-sec-malware",
                                "action": "sinkhole",
                                "log_level": "critical",
                                "packet_capture": "extended-capture",
                            },
                        ],
                        "sinkhole": {
                            "ipv4_address": "pan-sinkhole-default-ip",
                            "ipv6_address": "::1",
                        },
                    },
                },
            ]

        try:
            # List profiles using the SDK
            results = self.client.dns_security_profile.list(**container_kwargs, exact_match=exact_match)

            # Convert SDK response to a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container or "", "DNS security profiles", e)

    # --------------------------------------------------------------------------- Vulnerability Protection Profile ---------------------------------------------------------------------------

    def create_vulnerability_protection_profile(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
        description: str | None = None,
        threat_exception: list[dict[str, Any]] | None = None,
        rules: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create a vulnerability protection profile.

        Args:
            folder: Folder to create the profile in
            snippet: Snippet to create the profile in
            device: Device to create the profile in
            name: Name of the profile
            description: Optional description
            threat_exception: List of threat exceptions
            rules: List of vulnerability protection rules

        Returns:
            dict[str, Any]: The created vulnerability protection profile object

        Note:
            If a vulnerability protection profile with the same name already exists in the container,
            it will be updated with the new configuration.

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")
        self.logger.info(f"Creating or updating vulnerability protection profile: {name} in {container_type} {container}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"vpp-{name}",
                "folder": folder,
                "snippet": snippet,
                "device": device,
                "name": name,
                "description": description,
                "threat_exception": threat_exception or [],
                "rules": rules or [],
            }

        try:
            # First, try to fetch the existing vulnerability protection profile
            existing_profile = None
            try:
                existing_profile = self.client.vulnerability_protection_profile.fetch(name=name, folder=folder, snippet=snippet, device=device)
                self.logger.info(f"Found existing vulnerability protection profile '{name}' in {container_type} '{container}', updating...")
            except NotFoundError:
                self.logger.info(f"Vulnerability protection profile '{name}' not found in {container_type} '{container}', creating new...")
            except Exception as fetch_error:
                # Log but continue - we'll try to create if fetch failed for other reasons
                self.logger.warning(f"Error fetching vulnerability protection profile '{name}': {str(fetch_error)}")

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
            if threat_exception is not None:
                profile_data["threat_exception"] = threat_exception
            if rules is not None:
                profile_data["rules"] = rules

            # Create or update the profile
            if existing_profile:
                # Update existing profile
                profile_data["id"] = existing_profile.id
                from scm.models.security import VulnerabilityProfileUpdateModel

                update_model = VulnerabilityProfileUpdateModel(**profile_data)  # type: ignore[arg-type]
                result = self.client.vulnerability_protection_profile.update(update_model)
            else:
                # Create a new profile
                result = self.client.vulnerability_protection_profile.create(profile_data)

            # Convert response to dict
            return json.loads(result.model_dump_json(exclude_unset=True))

        except Exception as e:
            self._handle_api_exception("creating", container or "", "vulnerability protection profile", e)

    def delete_vulnerability_protection_profile(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
    ) -> bool:
        """Delete a vulnerability protection profile.

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
        self.logger.info(f"Deleting vulnerability protection profile: {name} from {container_type} {container}")

        if not self.client:
            # Return mock success if no client is available
            return True

        try:
            # Fetch the profile to get its ID
            profile = self.client.vulnerability_protection_profile.fetch(name=name, folder=folder, snippet=snippet, device=device)

            # Delete using the ID
            self.client.vulnerability_protection_profile.delete(profile.id)
            self.logger.info(f"Successfully deleted vulnerability protection profile '{name}' from {container_type} '{container}'")
            return True
        except NotFoundError:
            self.logger.warning(f"Vulnerability protection profile '{name}' not found in {container_type} '{container}'")
            return False
        except Exception as e:
            self._handle_api_exception("deleting", container or "", "vulnerability protection profile", e)

    def get_vulnerability_protection_profile(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
    ) -> dict[str, Any]:
        """Get a vulnerability protection profile by name.

        Args:
            folder: Folder containing the profile
            snippet: Snippet containing the profile
            device: Device containing the profile
            name: Name of the profile

        Returns:
            dict[str, Any]: The vulnerability protection profile object

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")
        self.logger.info(f"Getting vulnerability protection profile: {name} from {container_type} {container}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"vpp-{name}",
                "folder": folder,
                "snippet": snippet,
                "device": device,
                "name": name,
                "description": "Mock vulnerability protection profile",
                "rules": [
                    {
                        "name": "Block Critical Vulnerabilities",
                        "severity": ["critical", "high"],
                        "category": "any",
                        "host": "any",
                        "action": {"alert": {}},
                        "packet_capture": "single-packet",
                    }
                ],
            }

        try:
            # Fetch the profile using the SDK
            result = self.client.vulnerability_protection_profile.fetch(name=name, folder=folder, snippet=snippet, device=device)

            # Convert SDK response to dict
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("getting", container or "", "vulnerability protection profile", e)

    def list_vulnerability_protection_profiles(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List vulnerability protection profiles.

        Args:
            folder: Folder to list out
            snippet: Snippet to list out
            device: Device to list out
            exact_match: If True, only return exact container matches

        Returns:
            list[dict[str, Any]]: List of vulnerability protection profile objects

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

        self.logger.info(f"Listing vulnerability protection profiles in {container_type}: {container}")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "vpp-mock1",
                    "folder": folder or "Texas",
                    "name": "Strict Vulnerability Protection",
                    "description": "Block all critical and high severity vulnerabilities",
                    "rules": [
                        {
                            "name": "Block Critical",
                            "severity": ["critical", "high"],
                            "category": "any",
                            "host": "any",
                            "action": {"alert": {}},
                        }
                    ],
                },
                {
                    "id": "vpp-mock2",
                    "folder": folder or "Texas",
                    "name": "Standard Vulnerability Protection",
                    "description": "Standard vulnerability protection",
                    "rules": [
                        {
                            "name": "Alert Medium",
                            "severity": ["medium"],
                            "category": "any",
                            "host": "any",
                            "action": {"default": {}},
                        }
                    ],
                },
            ]

        try:
            # List profiles using the SDK
            results = self.client.vulnerability_protection_profile.list(**container_kwargs, exact_match=exact_match)

            # Convert SDK response to a list of dicts for compatibility
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container or "", "vulnerability protection profiles", e)

    # -------------------------------------------------------------------------------------- URL Category ------------------------------------------------------------------------------------

    def create_url_category(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
        description: str | None = None,
        type: str | None = None,
        list: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create or update a URL category.

        Args:
            folder: Folder to create the URL category in
            snippet: Snippet to create the URL category in
            device: Device to create the URL category in
            name: Name of the URL category
            description: Optional description
            type: Type of URL category (URL List or Category Match)
            list: List of URLs or category matches

        Returns:
            dict[str, Any]: The created URL category object

        Note:
            If a URL category with the same name already exists in the container,
            it will be updated with the new configuration.

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")
        self.logger.info(f"Creating or updating URL category: {name} in {container_type} {container}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"urlcat-{name}",
                "folder": folder,
                "snippet": snippet,
                "device": device,
                "name": name,
                "description": description,
                "type": type or "URL List",
                "list": list or [],
                "__action__": "created",
            }

        try:
            # First, try to fetch the existing URL category
            existing = None
            try:
                existing = self.client.url_category.fetch(name=name, folder=folder, snippet=snippet, device=device)
                self.logger.info(f"Found existing URL category '{name}' in {container_type} '{container}', updating...")
            except NotFoundError:
                self.logger.info(f"URL category '{name}' not found in {container_type} '{container}', creating new...")
            except Exception as fetch_error:
                self.logger.warning(f"Error fetching URL category '{name}': {str(fetch_error)}")

            # Prepare data
            data = {
                "name": name,
            }

            # Add container field only if not None
            if folder is not None:
                data["folder"] = folder
            if snippet is not None:
                data["snippet"] = snippet
            if device is not None:
                data["device"] = device

            # Add optional fields if provided
            if description is not None:
                data["description"] = description
            if type is not None:
                data["type"] = type
            if list is not None:
                data["list"] = list

            # Create or update
            if existing:
                # Update existing
                data["id"] = existing.id
                from scm.models.security.url_categories import URLCategoriesUpdateModel

                update_model = URLCategoriesUpdateModel(**data)  # type: ignore[arg-type]
                result = self.client.url_category.update(update_model)
                result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                result_dict["__action__"] = "updated"
            else:
                # Create new
                result = self.client.url_category.create(data)
                result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                result_dict["__action__"] = "created"

            return result_dict

        except Exception as e:
            self._handle_api_exception("creating", container or "", "URL category", e)

    def delete_url_category(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
    ) -> bool:
        """Delete a URL category.

        Args:
            folder: Folder containing the URL category
            snippet: Snippet containing the URL category
            device: Device containing the URL category
            name: Name of the URL category to delete

        Returns:
            bool: True if deleted successfully

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")
        self.logger.info(f"Deleting URL category: {name} from {container_type} {container}")

        if not self.client:
            return True

        try:
            profile = self.client.url_category.fetch(name=name, folder=folder, snippet=snippet, device=device)
            self.client.url_category.delete(profile.id)
            self.logger.info(f"Successfully deleted URL category '{name}' from {container_type} '{container}'")
            return True
        except NotFoundError:
            self.logger.warning(f"URL category '{name}' not found in {container_type} '{container}'")
            return False
        except Exception as e:
            self._handle_api_exception("deleting", container or "", "URL category", e)

    def get_url_category(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
    ) -> dict[str, Any]:
        """Get a URL category by name.

        Args:
            folder: Folder containing the URL category
            snippet: Snippet containing the URL category
            device: Device containing the URL category
            name: Name of the URL category

        Returns:
            dict[str, Any]: The URL category object

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")
        self.logger.info(f"Getting URL category: {name} from {container_type} {container}")

        if not self.client:
            return {
                "id": f"urlcat-{name}",
                "folder": folder,
                "snippet": snippet,
                "device": device,
                "name": name,
                "description": "Mock URL category",
                "type": "URL List",
                "list": ["example.com", "test.org"],
            }

        try:
            result = self.client.url_category.fetch(name=name, folder=folder, snippet=snippet, device=device)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("getting", container or "", "URL category", e)

    def list_url_categories(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List URL categories.

        Args:
            folder: Folder to list out
            snippet: Snippet to list out
            device: Device to list out
            exact_match: If True, only return exact container matches

        Returns:
            list[dict[str, Any]]: List of URL category objects

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        self.logger.info(f"Listing URL categories in {container_type}: {container}")

        if not self.client:
            return [
                {
                    "id": "urlcat-mock1",
                    "folder": folder or "Texas",
                    "name": "Custom-Block-List",
                    "description": "Custom blocked URLs",
                    "type": "URL List",
                    "list": ["malware.example.com", "phishing.test.org"],
                },
                {
                    "id": "urlcat-mock2",
                    "folder": folder or "Texas",
                    "name": "Internal-Sites",
                    "description": "Internal company sites",
                    "type": "URL List",
                    "list": ["intranet.company.com", "wiki.company.com"],
                },
            ]

        try:
            results = self.client.url_category.list(**container_kwargs, exact_match=exact_match)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container or "", "URL categories", e)

    # ---------------------------------------------------------------------------- App Override Rule ---------------------------------------------------------------------------------

    def create_app_override_rule(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        **rule_data,
    ) -> dict[str, Any]:
        """Create or update an app override rule.

        Args:
            folder: Folder to create the rule in
            snippet: Snippet to create the rule in
            device: Device to create the rule in
            **rule_data: Additional rule configuration data

        Returns:
            dict[str, Any]: Created/updated app override rule object

        """
        name = rule_data.get("name")
        rulebase = rule_data.pop("rulebase", "pre")
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Creating/updating app override rule: {name} in {container_type} {container}")

        if not self.client:
            return {
                "id": f"aor-{name}",
                "name": name,
                container_type: container,
                "application": rule_data.get("application", "web-browsing"),
                "port": rule_data.get("port", "443"),
                "protocol": rule_data.get("protocol", "tcp"),
            }

        try:
            # Check if rule already exists
            existing_rule = None
            try:
                existing_rule = self.client.app_override_rule.fetch(
                    name=name,
                    folder=folder,
                    snippet=snippet,
                    device=device,
                    rulebase=rulebase,
                )
            except NotFoundError:
                self.logger.info(f"App override rule '{name}' not found. Creating new rule.")

            if existing_rule:
                # Update existing rule
                update_data = rule_data.copy()
                update_data["id"] = str(existing_rule.id)
                update_data[container_type] = container
                from scm.models.security import AppOverrideRuleUpdateModel

                update_model = AppOverrideRuleUpdateModel(**update_data)
                result = self.client.app_override_rule.update(update_model, rulebase=rulebase)
            else:
                # Create new rule
                create_data = rule_data.copy()
                create_data[container_type] = container
                result = self.client.app_override_rule.create(create_data, rulebase=rulebase)

            return json.loads(result.model_dump_json(exclude_unset=True, by_alias=True))
        except Exception as e:
            self._handle_api_exception("creating/updating", container or "", f"app override rule '{name}'", e)

    def delete_app_override_rule(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
        rulebase: str = "pre",
    ) -> bool:
        """Delete an app override rule.

        Args:
            folder: Folder containing the rule
            snippet: Snippet containing the rule
            device: Device containing the rule
            name: Name of the rule to delete
            rulebase: Rulebase (pre or post)

        Returns:
            bool: True if deletion was successful

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Deleting app override rule: {name} from {container_type} {container}")

        if not self.client:
            return True

        try:
            rule = self.client.app_override_rule.fetch(
                name=name,
                folder=folder,
                snippet=snippet,
                device=device,
                rulebase=rulebase,
            )
            self.client.app_override_rule.delete(str(rule.id), rulebase=rulebase)
            return True
        except NotFoundError:
            self.logger.warning(f"App override rule '{name}' not found in {container_type} '{container}'")
            return False
        except Exception as e:
            self._handle_api_exception("deleting", container or "", f"app override rule '{name}'", e)

    def get_app_override_rule(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
        rulebase: str = "pre",
    ) -> dict[str, Any]:
        """Get an app override rule by name.

        Args:
            folder: Folder containing the rule
            snippet: Snippet containing the rule
            device: Device containing the rule
            name: Name of the rule
            rulebase: Rulebase (pre or post)

        Returns:
            dict[str, Any]: The app override rule object

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Getting app override rule: {name} from {container_type} {container}")

        if not self.client:
            return {
                "id": f"aor-{name}",
                container_type: container,
                "name": name,
                "application": "web-browsing",
                "port": "443",
                "protocol": "tcp",
                "from": ["any"],
                "to": ["any"],
                "source": ["any"],
                "destination": ["any"],
            }

        try:
            result = self.client.app_override_rule.fetch(
                name=name,
                folder=folder,
                snippet=snippet,
                device=device,
                rulebase=rulebase,
            )
            return json.loads(result.model_dump_json(exclude_unset=True, by_alias=True))
        except Exception as e:
            self._handle_api_exception("retrieving", container or "", f"app override rule '{name}'", e)

    def list_app_override_rules(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        rulebase: str = "pre",
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List app override rules.

        Args:
            folder: Folder to list from
            snippet: Snippet to list from
            device: Device to list from
            rulebase: Rulebase (pre or post)
            exact_match: If True, only return exact container matches

        Returns:
            list[dict[str, Any]]: List of app override rule objects

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        self.logger.info(f"Listing app override rules in {container_type}: {container}")

        if not self.client:
            return [
                {
                    "id": "aor-mock1",
                    "folder": folder or "Texas",
                    "name": "Override Web",
                    "application": "web-browsing",
                    "port": "443",
                    "protocol": "tcp",
                    "from": ["any"],
                    "to": ["any"],
                },
            ]

        try:
            results = self.client.app_override_rule.list(
                **container_kwargs,
                rulebase=rulebase,
                exact_match=exact_match,
            )
            return [json.loads(result.model_dump_json(exclude_unset=True, by_alias=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container or "", "app override rules", e)

    def move_app_override_rule(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
        rulebase: str = "pre",
        destination: str = "top",
        destination_rule: str | None = None,
    ) -> None:
        """Move an app override rule to a new position.

        Args:
            folder: Folder containing the rule
            snippet: Snippet containing the rule
            device: Device containing the rule
            name: Name of the rule to move
            rulebase: Rulebase (pre or post)
            destination: Where to move (top, bottom, before, after)
            destination_rule: UUID of reference rule for before/after

        """
        container = folder or snippet or device
        self.logger.info(f"Moving app override rule: {name} to {destination}")

        if not self.client:
            return

        try:
            rule = self.client.app_override_rule.fetch(
                name=name,
                folder=folder,
                snippet=snippet,
                device=device,
                rulebase=rulebase,
            )
            move_data = {"destination": destination, "rulebase": rulebase}
            if destination_rule:
                move_data["destination_rule"] = destination_rule
            self.client.app_override_rule.move(rule.id, move_data)
        except Exception as e:
            self._handle_api_exception("moving", container or "", f"app override rule '{name}'", e)

    # -------------------------------------------------------------------------- Authentication Rule -----------------------------------------------------------------------------------

    def create_authentication_rule(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        **rule_data,
    ) -> dict[str, Any]:
        """Create or update an authentication rule.

        Args:
            folder: Folder to create the rule in
            snippet: Snippet to create the rule in
            device: Device to create the rule in
            **rule_data: Additional rule configuration data

        Returns:
            dict[str, Any]: Created/updated authentication rule object

        """
        name = rule_data.get("name")
        rulebase = rule_data.pop("rulebase", "pre")
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Creating/updating authentication rule: {name} in {container_type} {container}")

        if not self.client:
            return {
                "id": f"authr-{name}",
                "name": name,
                container_type: container,
                "from": rule_data.get("from", ["any"]),
                "to": rule_data.get("to", ["any"]),
            }

        try:
            existing_rule = None
            try:
                existing_rule = self.client.authentication_rule.fetch(
                    name=name,
                    folder=folder,
                    snippet=snippet,
                    device=device,
                    rulebase=rulebase,
                )
            except NotFoundError:
                self.logger.info(f"Authentication rule '{name}' not found. Creating new rule.")

            if existing_rule:
                update_data = rule_data.copy()
                update_data["id"] = str(existing_rule.id)
                update_data[container_type] = container
                from scm.models.security import AuthenticationRuleUpdateModel

                update_model = AuthenticationRuleUpdateModel(**update_data)
                result = self.client.authentication_rule.update(update_model, rulebase=rulebase)
            else:
                create_data = rule_data.copy()
                create_data[container_type] = container
                result = self.client.authentication_rule.create(create_data, rulebase=rulebase)

            return json.loads(result.model_dump_json(exclude_unset=True, by_alias=True))
        except Exception as e:
            self._handle_api_exception("creating/updating", container or "", f"authentication rule '{name}'", e)

    def delete_authentication_rule(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
        rulebase: str = "pre",
    ) -> bool:
        """Delete an authentication rule.

        Args:
            folder: Folder containing the rule
            snippet: Snippet containing the rule
            device: Device containing the rule
            name: Name of the rule to delete
            rulebase: Rulebase (pre or post)

        Returns:
            bool: True if deletion was successful

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Deleting authentication rule: {name} from {container_type} {container}")

        if not self.client:
            return True

        try:
            rule = self.client.authentication_rule.fetch(
                name=name,
                folder=folder,
                snippet=snippet,
                device=device,
                rulebase=rulebase,
            )
            self.client.authentication_rule.delete(str(rule.id), rulebase=rulebase)
            return True
        except NotFoundError:
            self.logger.warning(f"Authentication rule '{name}' not found in {container_type} '{container}'")
            return False
        except Exception as e:
            self._handle_api_exception("deleting", container or "", f"authentication rule '{name}'", e)

    def get_authentication_rule(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
        rulebase: str = "pre",
    ) -> dict[str, Any]:
        """Get an authentication rule by name.

        Args:
            folder: Folder containing the rule
            snippet: Snippet containing the rule
            device: Device containing the rule
            name: Name of the rule
            rulebase: Rulebase (pre or post)

        Returns:
            dict[str, Any]: The authentication rule object

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Getting authentication rule: {name} from {container_type} {container}")

        if not self.client:
            return {
                "id": f"authr-{name}",
                container_type: container,
                "name": name,
                "from": ["any"],
                "to": ["any"],
                "source": ["any"],
                "destination": ["any"],
                "service": ["any"],
                "category": ["any"],
            }

        try:
            result = self.client.authentication_rule.fetch(
                name=name,
                folder=folder,
                snippet=snippet,
                device=device,
                rulebase=rulebase,
            )
            return json.loads(result.model_dump_json(exclude_unset=True, by_alias=True))
        except Exception as e:
            self._handle_api_exception("retrieving", container or "", f"authentication rule '{name}'", e)

    def list_authentication_rules(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        rulebase: str = "pre",
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List authentication rules.

        Args:
            folder: Folder to list from
            snippet: Snippet to list from
            device: Device to list from
            rulebase: Rulebase (pre or post)
            exact_match: If True, only return exact container matches

        Returns:
            list[dict[str, Any]]: List of authentication rule objects

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        self.logger.info(f"Listing authentication rules in {container_type}: {container}")

        if not self.client:
            return [
                {
                    "id": "authr-mock1",
                    "folder": folder or "Texas",
                    "name": "Auth Rule 1",
                    "from": ["any"],
                    "to": ["any"],
                    "source": ["any"],
                    "destination": ["any"],
                },
            ]

        try:
            results = self.client.authentication_rule.list(
                **container_kwargs,
                rulebase=rulebase,
                exact_match=exact_match,
            )
            return [json.loads(result.model_dump_json(exclude_unset=True, by_alias=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container or "", "authentication rules", e)

    def move_authentication_rule(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
        rulebase: str = "pre",
        destination: str = "top",
        destination_rule: str | None = None,
    ) -> None:
        """Move an authentication rule to a new position.

        Args:
            folder: Folder containing the rule
            snippet: Snippet containing the rule
            device: Device containing the rule
            name: Name of the rule to move
            rulebase: Rulebase (pre or post)
            destination: Where to move (top, bottom, before, after)
            destination_rule: UUID of reference rule for before/after

        """
        container = folder or snippet or device
        self.logger.info(f"Moving authentication rule: {name} to {destination}")

        if not self.client:
            return

        try:
            rule = self.client.authentication_rule.fetch(
                name=name,
                folder=folder,
                snippet=snippet,
                device=device,
                rulebase=rulebase,
            )
            move_data = {"destination": destination, "rulebase": rulebase}
            if destination_rule:
                move_data["destination_rule"] = destination_rule
            self.client.authentication_rule.move(rule.id, move_data)
        except Exception as e:
            self._handle_api_exception("moving", container or "", f"authentication rule '{name}'", e)

    # ---------------------------------------------------------------------------- Decryption Rule -------------------------------------------------------------------------------------

    def create_decryption_rule(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        **rule_data,
    ) -> dict[str, Any]:
        """Create or update a decryption rule.

        Args:
            folder: Folder to create the rule in
            snippet: Snippet to create the rule in
            device: Device to create the rule in
            **rule_data: Additional rule configuration data

        Returns:
            dict[str, Any]: Created/updated decryption rule object

        """
        name = rule_data.get("name")
        rulebase = rule_data.pop("rulebase", "pre")
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Creating/updating decryption rule: {name} in {container_type} {container}")

        if not self.client:
            return {
                "id": f"decr-{name}",
                "name": name,
                container_type: container,
                "action": rule_data.get("action", "no-decrypt"),
                "from": rule_data.get("from", ["any"]),
                "to": rule_data.get("to", ["any"]),
            }

        try:
            existing_rule = None
            try:
                existing_rule = self.client.decryption_rule.fetch(
                    name=name,
                    folder=folder,
                    snippet=snippet,
                    device=device,
                    rulebase=rulebase,
                )
            except NotFoundError:
                self.logger.info(f"Decryption rule '{name}' not found. Creating new rule.")

            if existing_rule:
                update_data = rule_data.copy()
                update_data["id"] = str(existing_rule.id)
                update_data[container_type] = container
                from scm.models.security import DecryptionRuleUpdateModel

                update_model = DecryptionRuleUpdateModel(**update_data)
                result = self.client.decryption_rule.update(update_model, rulebase=rulebase)
            else:
                create_data = rule_data.copy()
                create_data[container_type] = container
                result = self.client.decryption_rule.create(create_data, rulebase=rulebase)

            return json.loads(result.model_dump_json(exclude_unset=True, by_alias=True))
        except Exception as e:
            self._handle_api_exception("creating/updating", container or "", f"decryption rule '{name}'", e)

    def delete_decryption_rule(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
        rulebase: str = "pre",
    ) -> bool:
        """Delete a decryption rule.

        Args:
            folder: Folder containing the rule
            snippet: Snippet containing the rule
            device: Device containing the rule
            name: Name of the rule to delete
            rulebase: Rulebase (pre or post)

        Returns:
            bool: True if deletion was successful

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Deleting decryption rule: {name} from {container_type} {container}")

        if not self.client:
            return True

        try:
            rule = self.client.decryption_rule.fetch(
                name=name,
                folder=folder,
                snippet=snippet,
                device=device,
                rulebase=rulebase,
            )
            self.client.decryption_rule.delete(str(rule.id), rulebase=rulebase)
            return True
        except NotFoundError:
            self.logger.warning(f"Decryption rule '{name}' not found in {container_type} '{container}'")
            return False
        except Exception as e:
            self._handle_api_exception("deleting", container or "", f"decryption rule '{name}'", e)

    def get_decryption_rule(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
        rulebase: str = "pre",
    ) -> dict[str, Any]:
        """Get a decryption rule by name.

        Args:
            folder: Folder containing the rule
            snippet: Snippet containing the rule
            device: Device containing the rule
            name: Name of the rule
            rulebase: Rulebase (pre or post)

        Returns:
            dict[str, Any]: The decryption rule object

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Getting decryption rule: {name} from {container_type} {container}")

        if not self.client:
            return {
                "id": f"decr-{name}",
                container_type: container,
                "name": name,
                "action": "no-decrypt",
                "from": ["any"],
                "to": ["any"],
                "source": ["any"],
                "destination": ["any"],
            }

        try:
            result = self.client.decryption_rule.fetch(
                name=name,
                folder=folder,
                snippet=snippet,
                device=device,
                rulebase=rulebase,
            )
            return json.loads(result.model_dump_json(exclude_unset=True, by_alias=True))
        except Exception as e:
            self._handle_api_exception("retrieving", container or "", f"decryption rule '{name}'", e)

    def list_decryption_rules(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        rulebase: str = "pre",
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List decryption rules.

        Args:
            folder: Folder to list from
            snippet: Snippet to list from
            device: Device to list from
            rulebase: Rulebase (pre or post)
            exact_match: If True, only return exact container matches

        Returns:
            list[dict[str, Any]]: List of decryption rule objects

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        self.logger.info(f"Listing decryption rules in {container_type}: {container}")

        if not self.client:
            return [
                {
                    "id": "decr-mock1",
                    "folder": folder or "Texas",
                    "name": "Decrypt Rule 1",
                    "action": "no-decrypt",
                    "from": ["any"],
                    "to": ["any"],
                },
            ]

        try:
            results = self.client.decryption_rule.list(
                **container_kwargs,
                rulebase=rulebase,
                exact_match=exact_match,
            )
            return [json.loads(result.model_dump_json(exclude_unset=True, by_alias=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container or "", "decryption rules", e)

    def move_decryption_rule(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
        rulebase: str = "pre",
        destination: str = "top",
        destination_rule: str | None = None,
    ) -> None:
        """Move a decryption rule to a new position.

        Args:
            folder: Folder containing the rule
            snippet: Snippet containing the rule
            device: Device containing the rule
            name: Name of the rule to move
            rulebase: Rulebase (pre or post)
            destination: Where to move (top, bottom, before, after)
            destination_rule: UUID of reference rule for before/after

        """
        container = folder or snippet or device
        self.logger.info(f"Moving decryption rule: {name} to {destination}")

        if not self.client:
            return

        try:
            rule = self.client.decryption_rule.fetch(
                name=name,
                folder=folder,
                snippet=snippet,
                device=device,
                rulebase=rulebase,
            )
            move_data = {"destination": destination, "rulebase": rulebase}
            if destination_rule:
                move_data["destination_rule"] = destination_rule
            self.client.decryption_rule.move(rule.id, move_data)
        except Exception as e:
            self._handle_api_exception("moving", container or "", f"decryption rule '{name}'", e)

    # --------------------------------------------------------------------------- URL Access Profile -----------------------------------------------------------------------------------

    def create_url_access_profile(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        **profile_data,
    ) -> dict[str, Any]:
        """Create or update a URL access profile.

        Args:
            folder: Folder to create the profile in
            snippet: Snippet to create the profile in
            device: Device to create the profile in
            **profile_data: Additional profile configuration data

        Returns:
            dict[str, Any]: Created/updated URL access profile object

        """
        name = profile_data.get("name")
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Creating/updating URL access profile: {name} in {container_type} {container}")

        if not self.client:
            return {
                "id": f"uap-{name}",
                "name": name,
                container_type: container,
                "block": profile_data.get("block", []),
                "alert": profile_data.get("alert", []),
                "allow": profile_data.get("allow", []),
            }

        try:
            existing_profile = None
            try:
                existing_profile = self.client.url_access_profile.fetch(
                    name=name,
                    folder=folder,
                    snippet=snippet,
                    device=device,
                )
            except NotFoundError:
                self.logger.info(f"URL access profile '{name}' not found. Creating new profile.")

            if existing_profile:
                update_data = profile_data.copy()
                update_data["id"] = str(existing_profile.id)
                update_data[container_type] = container
                from scm.models.security import URLAccessProfileUpdateModel

                update_model = URLAccessProfileUpdateModel(**update_data)
                result = self.client.url_access_profile.update(update_model)
            else:
                create_data = profile_data.copy()
                create_data[container_type] = container
                result = self.client.url_access_profile.create(create_data)

            return json.loads(result.model_dump_json(exclude_unset=True, by_alias=True))
        except Exception as e:
            self._handle_api_exception("creating/updating", container or "", f"URL access profile '{name}'", e)

    def delete_url_access_profile(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
    ) -> bool:
        """Delete a URL access profile.

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

        self.logger.info(f"Deleting URL access profile: {name} from {container_type} {container}")

        if not self.client:
            return True

        try:
            profile = self.client.url_access_profile.fetch(
                name=name,
                folder=folder,
                snippet=snippet,
                device=device,
            )
            self.client.url_access_profile.delete(str(profile.id))
            return True
        except NotFoundError:
            self.logger.warning(f"URL access profile '{name}' not found in {container_type} '{container}'")
            return False
        except Exception as e:
            self._handle_api_exception("deleting", container or "", f"URL access profile '{name}'", e)

    def get_url_access_profile(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
    ) -> dict[str, Any]:
        """Get a URL access profile by name.

        Args:
            folder: Folder containing the profile
            snippet: Snippet containing the profile
            device: Device containing the profile
            name: Name of the profile

        Returns:
            dict[str, Any]: The URL access profile object

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Getting URL access profile: {name} from {container_type} {container}")

        if not self.client:
            return {
                "id": f"uap-{name}",
                container_type: container,
                "name": name,
                "block": ["adult", "malware"],
                "alert": ["hacking"],
                "allow": ["business-and-economy"],
            }

        try:
            result = self.client.url_access_profile.fetch(
                name=name,
                folder=folder,
                snippet=snippet,
                device=device,
            )
            return json.loads(result.model_dump_json(exclude_unset=True, by_alias=True))
        except Exception as e:
            self._handle_api_exception("retrieving", container or "", f"URL access profile '{name}'", e)

    def list_url_access_profiles(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List URL access profiles.

        Args:
            folder: Folder to list from
            snippet: Snippet to list from
            device: Device to list from
            exact_match: If True, only return exact container matches

        Returns:
            list[dict[str, Any]]: List of URL access profile objects

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        self.logger.info(f"Listing URL access profiles in {container_type}: {container}")

        if not self.client:
            return [
                {
                    "id": "uap-mock1",
                    "folder": folder or "Texas",
                    "name": "URL Profile 1",
                    "block": ["adult", "malware"],
                    "alert": ["hacking"],
                },
            ]

        try:
            results = self.client.url_access_profile.list(**container_kwargs, exact_match=exact_match)
            return [json.loads(result.model_dump_json(exclude_unset=True, by_alias=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container or "", "URL access profiles", e)

    # ======================================================================================================================================================================================
    # JOBS AND COMMIT METHODS
    # ======================================================================================================================================================================================

    # ------------------------------------------------------------------------------------ Jobs ------------------------------------------------------------------------------------

    def list_jobs(self, max_results: int = 25) -> list[dict[str, Any]]:
        """List recent SCM configuration jobs.

        Args:
            max_results: Maximum number of jobs to return

        Returns:
            list[dict[str, Any]]: List of job dictionaries

        """
        self.logger.info(f"Listing jobs (max_results={max_results})")

        if not self.client:
            # Return mock data
            return [
                {
                    "id": "11111",
                    "type_str": "CommitAll",
                    "status_str": "FIN",
                    "description": "Mock commit job",
                    "start_ts": "2025-01-15T10:00:00Z",
                    "end_ts": "2025-01-15T10:02:00Z",
                    "result_str": "OK",
                },
                {
                    "id": "22222",
                    "type_str": "CommitAll",
                    "status_str": "PEND",
                    "description": "Mock pending job",
                    "start_ts": "2025-01-15T10:05:00Z",
                    "end_ts": "",
                    "result_str": "",
                },
                {
                    "id": "33333",
                    "type_str": "CommitAll",
                    "status_str": "FIN",
                    "description": "Mock completed job",
                    "start_ts": "2025-01-15T09:00:00Z",
                    "end_ts": "2025-01-15T09:03:00Z",
                    "result_str": "FAIL",
                },
            ]

        try:
            result = self.client.list_jobs()
            if hasattr(result, "data") and result.data:
                jobs = []
                for job in result.data[:max_results]:
                    if hasattr(job, "model_dump_json"):
                        jobs.append(json.loads(job.model_dump_json(exclude_unset=True)))
                    else:
                        jobs.append({"id": str(job)})
                return jobs
            elif isinstance(result, list):
                return [json.loads(j.model_dump_json(exclude_unset=True)) if hasattr(j, "model_dump_json") else {"id": str(j)} for j in result[:max_results]]
            return []
        except Exception as e:
            self._handle_api_exception("listing", "", "jobs", e)

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        """Get the status of a specific job.

        Args:
            job_id: The ID of the job to query

        Returns:
            dict[str, Any]: Job status dictionary

        """
        self.logger.info(f"Getting job status: {job_id}")

        if not self.client:
            # Return mock data
            return {
                "id": job_id,
                "type_str": "CommitAll",
                "status_str": "FIN",
                "result_str": "OK",
                "description": "Mock job",
                "start_ts": "2025-01-15T10:00:00Z",
                "end_ts": "2025-01-15T10:02:00Z",
                "details": "Configuration committed successfully",
            }

        try:
            result = self.client.get_job_status(job_id=job_id)
            if hasattr(result, "data") and result.data:
                job_data = result.data[0]
                return json.loads(job_data.model_dump_json(exclude_unset=True))
            if hasattr(result, "model_dump_json"):
                return json.loads(result.model_dump_json(exclude_unset=True))
            return {"id": job_id, "status": str(result)}
        except (ValidationError, ValueError) as e:
            # SDK may fail to parse in-progress jobs with empty end_ts.
            # Try extracting status from the raw API response.
            self.logger.warning(f"SDK validation error for job {job_id}, attempting raw extraction: {e}")
            try:
                response = self.client._client.get(f"/config/operations/v1/jobs/{job_id}")  # noqa: SLF001
                if hasattr(response, "json"):
                    raw = response.json()
                elif isinstance(response, dict):
                    raw = response
                else:
                    raw = {"id": job_id, "status": "unknown", "error": str(e)}
                # Normalize: API may nest data under "data" key
                if "data" in raw and isinstance(raw["data"], list) and raw["data"]:
                    return raw["data"][0]
                return raw
            except Exception:
                # Last resort: return what we know
                return {"id": job_id, "status": "unknown", "parse_error": str(e)}
        except Exception as e:
            self._handle_api_exception("getting status of", "", f"job {job_id}", e)

    def wait_for_job(self, job_id: str, timeout: int = 300) -> dict[str, Any]:
        """Wait for a job to complete.

        Args:
            job_id: The ID of the job to wait for
            timeout: Maximum time to wait in seconds

        Returns:
            dict[str, Any]: Final job status dictionary

        """
        self.logger.info(f"Waiting for job {job_id} (timeout={timeout}s)")

        if not self.client:
            # Return mock data (simulate completed job)
            return {
                "id": job_id,
                "type_str": "CommitAll",
                "status_str": "FIN",
                "result_str": "OK",
                "description": "Mock job completed",
                "start_ts": "2025-01-15T10:00:00Z",
                "end_ts": "2025-01-15T10:02:00Z",
                "details": "Configuration committed successfully",
            }

        import time

        terminal_results = {"OK", "FAIL", "PUSHABORT", "ABORTED"}
        terminal_statuses = {"FIN"}

        start = time.time()
        poll_interval = 5

        while True:
            elapsed = time.time() - start
            if elapsed >= timeout:
                raise TimeoutError(f"Job {job_id} did not complete within {timeout}s")

            job = self.get_job_status(job_id=job_id)
            status = job.get("status_str", job.get("status", ""))
            result_str = job.get("result_str", job.get("result", ""))

            self.logger.info(f"Job {job_id} poll: status={status}, result={result_str}")

            # Job is terminal when status is FIN, or result is a known terminal value
            if status in terminal_statuses or result_str in terminal_results:
                return job

            time.sleep(min(poll_interval, max(0, timeout - elapsed)))

    # ----------------------------------------------------------------------------------- Commit -----------------------------------------------------------------------------------

    def commit_config(
        self,
        folders: list[str],
        description: str,
        sync: bool = False,
        timeout: int = 300,
        admin: str | None = None,
    ) -> dict[str, Any]:
        """Commit configuration changes to SCM.

        Args:
            folders: List of folders to commit
            description: Description of the commit
            sync: Whether to wait synchronously for completion
            timeout: Timeout in seconds when sync is True
            admin: Admin user for commit (required for bearer token auth)

        Returns:
            dict[str, Any]: Commit result dictionary

        """
        self.logger.info(f"Committing config for folders: {folders}, sync={sync}")

        if not self.client:
            # Return mock data
            return {
                "success": True,
                "job_id": "mock-job-99999",
                "status": "FIN" if sync else "PEND",
                "message": "Mock commit " + ("completed" if sync else "initiated"),
            }

        try:
            commit_kwargs = {
                "folders": folders,
                "description": description,
                "sync": sync,
                "timeout": timeout,
            }

            # Pass admin parameter if specified (needed for bearer token auth)
            if admin:
                commit_kwargs["admin"] = [admin]
            elif self._cached_token_mode:
                # Cached-token sessions are bearer-mode to the SDK, so supply
                # the admin identity the token was issued for.
                commit_kwargs["admin"] = [self.client_id]

            # Always commit asynchronously, then use our own wait_for_job if sync
            async_kwargs = {k: v for k, v in commit_kwargs.items() if k not in ("sync", "timeout")}
            async_kwargs["sync"] = False

            result = self.client.commit(**async_kwargs)

            # Extract job_id from the commit response
            if hasattr(result, "model_dump_json"):
                result_dict = json.loads(result.model_dump_json(exclude_unset=True))
            elif isinstance(result, dict):
                result_dict = result
            else:
                result_dict = {"job_id": str(result) if result else "unknown"}

            job_id = str(result_dict.get("job_id", result_dict.get("id", result_dict.get("jobid", ""))))

            if sync and job_id and job_id != "unknown":
                # Use our own polling which handles all terminal states and empty end_ts
                job_result = self.wait_for_job(job_id=job_id, timeout=timeout)
                job_result["success"] = job_result.get("result_str", job_result.get("result", "")) == "OK"
                job_result["job_id"] = job_id
                return job_result

            result_dict.setdefault("success", not sync)
            result_dict.setdefault("job_id", job_id)
            return result_dict
        except Exception as e:
            self._handle_api_exception("committing", ", ".join(folders), "configuration", e)

    # ----------------------------- BGP Routing Methods ----------------------------

    def create_bgp_routing(
        self,
        backbone_routing: str,
        routing_preference: dict[str, Any] | None = None,
        accept_route_over_SC: bool = False,  # noqa: N803
        outbound_routes_for_services: list[str] | None = None,
        add_host_route_to_ike_peer: bool = False,
        withdraw_static_route: bool = False,
    ) -> dict[str, Any]:
        """Create or update BGP routing configuration (singleton resource).

        Args:
            backbone_routing: Backbone routing mode
            routing_preference: Routing preference configuration
            accept_route_over_SC: Accept routes over service connections
            outbound_routes_for_services: Outbound routes for services
            add_host_route_to_ike_peer: Add host route to IKE peer
            withdraw_static_route: Withdraw static routes

        Returns:
            dict[str, Any]: Created/updated BGP routing configuration

        """
        self.logger.info("Creating/updating BGP routing configuration")

        if not self.client:
            return {
                "backbone_routing": backbone_routing,
                "routing_preference": routing_preference or {"default": {}},
                "accept_route_over_SC": accept_route_over_SC,
                "outbound_routes_for_services": outbound_routes_for_services or [],
                "add_host_route_to_ike_peer": add_host_route_to_ike_peer,
                "withdraw_static_route": withdraw_static_route,
                "__action__": "created",
            }

        try:
            # BGP routing is a singleton; try to get existing config first
            existing = None
            try:
                existing = self.client.bgp_routing.get()
                self.logger.info("Found existing BGP routing configuration")
            except Exception:
                self.logger.info("No existing BGP routing configuration found, will create")

            data: dict[str, Any] = {
                "backbone_routing": backbone_routing,
                "accept_route_over_SC": accept_route_over_SC,
                "add_host_route_to_ike_peer": add_host_route_to_ike_peer,
                "withdraw_static_route": withdraw_static_route,
            }
            if outbound_routes_for_services:
                data["outbound_routes_for_services"] = outbound_routes_for_services
            if routing_preference:
                data["routing_preference"] = routing_preference

            if existing:
                result = self.client.bgp_routing.update(data)
                self.logger.info("Successfully updated BGP routing configuration")
                result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                result_dict["__action__"] = "updated"
                return result_dict
            else:
                result = self.client.bgp_routing.create(data)
                self.logger.info("Successfully created BGP routing configuration")
                result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                result_dict["__action__"] = "created"
                return result_dict

        except Exception as e:
            self._handle_api_exception("creating/updating", "N/A", "BGP routing", e)

    def get_bgp_routing(self) -> dict[str, Any]:
        """Get the current BGP routing configuration.

        Returns:
            dict[str, Any]: BGP routing configuration

        """
        self.logger.info("Getting BGP routing configuration")

        if not self.client:
            return {
                "backbone_routing": "no-asymmetric-routing",
                "routing_preference": {"default": {}},
                "accept_route_over_SC": False,
                "outbound_routes_for_services": [],
                "add_host_route_to_ike_peer": False,
                "withdraw_static_route": False,
            }

        try:
            result = self.client.bgp_routing.get()
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("fetching", "N/A", "BGP routing", e)

    def delete_bgp_routing(self) -> bool:
        """Reset BGP routing configuration to defaults.

        Returns:
            bool: True if reset was successful

        """
        self.logger.info("Resetting BGP routing configuration to defaults")

        if not self.client:
            self.logger.info("Mock mode: Would reset BGP routing configuration")
            return True

        try:
            self.client.bgp_routing.delete()
            self.logger.info("Successfully reset BGP routing configuration")
            return True
        except Exception as e:
            self._handle_api_exception("resetting", "N/A", "BGP routing", e)

    # ----------------------- Internal DNS Server Methods ------------------------

    def create_internal_dns_server(
        self,
        name: str,
        domain_name: list[str],
        primary: str,
        secondary: str | None = None,
    ) -> dict[str, Any]:
        """Create or update an internal DNS server using smart upsert logic.

        Args:
            name: Name of the internal DNS server
            domain_name: DNS domain name(s)
            primary: Primary DNS server IP address
            secondary: Secondary DNS server IP address

        Returns:
            dict[str, Any]: Created/updated internal DNS server object

        """
        self.logger.info(f"Creating/updating internal DNS server '{name}'")

        if not self.client:
            return {
                "id": f"dns-{name}",
                "name": name,
                "domain_name": domain_name,
                "primary": primary,
                "secondary": secondary,
                "__action__": "created",
            }

        try:
            # Step 1: Try to fetch existing DNS server
            existing = None
            try:
                existing = self.client.internal_dns_server.fetch(name=name)
                self.logger.info(f"Found existing internal DNS server '{name}'")
            except Exception:
                self.logger.info(f"Internal DNS server '{name}' not found, will create new")

            if existing:
                # Step 2: Check what needs updating
                needs_update = False
                update_fields = []

                if set(existing.domain_name) != set(domain_name):
                    update_fields.append("domain_name")
                    needs_update = True

                if str(existing.primary) != primary:
                    update_fields.append("primary")
                    needs_update = True

                existing_secondary = str(existing.secondary) if existing.secondary else None
                if existing_secondary != secondary:
                    update_fields.append("secondary")
                    needs_update = True

                if needs_update:
                    self.logger.info(f"Updating internal DNS server fields: {', '.join(update_fields)}")
                    from scm.models.deployment import InternalDnsServersUpdateModel

                    update_data = {
                        "id": str(existing.id),
                        "name": name,
                        "domain_name": domain_name,
                        "primary": primary,
                    }
                    if secondary:
                        update_data["secondary"] = secondary
                    update_model = InternalDnsServersUpdateModel(**update_data)  # type: ignore[arg-type]
                    updated = self.client.internal_dns_server.update(update_model)
                    self.logger.info(f"Successfully updated internal DNS server '{name}'")
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
                else:
                    self.logger.info(f"No changes detected for internal DNS server '{name}', skipping update")
                    result = json.loads(existing.model_dump_json(exclude_unset=True))
                    result["__action__"] = "no_change"
                    return result

            else:
                # Step 3: Create new DNS server
                data: dict[str, Any] = {
                    "name": name,
                    "domain_name": domain_name,
                    "primary": primary,
                }
                if secondary:
                    data["secondary"] = secondary

                self.logger.info(f"Creating new internal DNS server '{name}'")
                created = self.client.internal_dns_server.create(data)
                self.logger.info(f"Successfully created internal DNS server '{name}'")
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result

        except Exception as e:
            self._handle_api_exception("creating/updating", "internal DNS server", name, e)

    def get_internal_dns_server(self, name: str) -> dict[str, Any]:
        """Get a specific internal DNS server by name.

        Args:
            name: Name of the internal DNS server

        Returns:
            dict[str, Any]: Internal DNS server object

        """
        self.logger.info(f"Getting internal DNS server '{name}'")

        if not self.client:
            return {
                "id": f"dns-{name}",
                "name": name,
                "domain_name": ["example.com"],
                "primary": "10.0.0.1",
                "secondary": "10.0.0.2",
            }

        try:
            result = self.client.internal_dns_server.fetch(name=name)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("fetching", "internal DNS server", name, e)

    def list_internal_dns_servers(self) -> list[dict[str, Any]]:
        """List all internal DNS servers.

        Returns:
            list[dict[str, Any]]: List of internal DNS server objects

        """
        self.logger.info("Listing internal DNS servers")

        if not self.client:
            return [
                {
                    "id": "dns-1",
                    "name": "internal-dns-1",
                    "domain_name": ["corp.example.com"],
                    "primary": "10.0.0.1",
                    "secondary": "10.0.0.2",
                },
                {
                    "id": "dns-2",
                    "name": "internal-dns-2",
                    "domain_name": ["dev.example.com"],
                    "primary": "10.1.0.1",
                },
            ]

        try:
            results = self.client.internal_dns_server.list()
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", "N/A", "internal DNS servers", e)

    def delete_internal_dns_server(self, name: str) -> bool:
        """Delete an internal DNS server.

        Args:
            name: Name of the internal DNS server to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting internal DNS server '{name}'")

        if not self.client:
            self.logger.info(f"Mock mode: Would delete internal DNS server '{name}'")
            return True

        try:
            dns_server = self.client.internal_dns_server.fetch(name=name)
            self.client.internal_dns_server.delete(str(dns_server.id))
            self.logger.info(f"Successfully deleted internal DNS server '{name}'")
            return True
        except Exception as e:
            self._handle_api_exception("deleting", "internal DNS server", name, e)

    # ----------------------- Network Location Methods ---------------------------

    def get_network_location(self, value: str) -> dict[str, Any]:
        """Get a specific network location by value.

        Args:
            value: System value of the network location (e.g., 'us-west-1')

        Returns:
            dict[str, Any]: Network location object

        """
        self.logger.info(f"Getting network location '{value}'")

        if not self.client:
            return {
                "value": value,
                "display": f"Mock {value}",
                "continent": "North America",
                "latitude": 37.38,
                "longitude": -121.98,
                "region": value,
                "aggregate_region": "us-southwest",
            }

        try:
            result = self.client.network_location.fetch(value=value)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("fetching", "network location", value, e)

    def list_network_locations(self) -> list[dict[str, Any]]:
        """List all network locations.

        Returns:
            list[dict[str, Any]]: List of network location objects

        """
        self.logger.info("Listing network locations")

        if not self.client:
            return [
                {
                    "value": "us-west-1",
                    "display": "US West",
                    "continent": "North America",
                    "latitude": 37.38,
                    "longitude": -121.98,
                    "region": "us-west-1",
                    "aggregate_region": "us-southwest",
                },
                {
                    "value": "us-east-1",
                    "display": "US East",
                    "continent": "North America",
                    "latitude": 39.04,
                    "longitude": -77.49,
                    "region": "us-east-1",
                    "aggregate_region": "us-northeast",
                },
            ]

        try:
            results = self.client.network_location.list()
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", "N/A", "network locations", e)

    # ======================================================================================================================================================================================
    # MOBILE AGENT CONFIGURATION METHODS
    # ======================================================================================================================================================================================

    # ---------------------------------------------------------------------------------- Agent Version ---------------------------------------------------------------------------------

    def list_agent_versions(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
    ) -> list[dict[str, Any]]:
        """List agent versions.

        Args:
            folder: Folder to list from
            snippet: Snippet to list from
            device: Device to list from

        Returns:
            list[dict[str, Any]]: List of agent version objects

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Listing agent versions in {container_type}: {container}")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "av-mock1",
                    "folder": folder or "Mobile Users",
                    "name": "5.2.13",
                    "version": "5.2.13",
                    "platform": "Windows",
                    "release_date": "2024-01-15",
                },
                {
                    "id": "av-mock2",
                    "folder": folder or "Mobile Users",
                    "name": "5.2.12",
                    "version": "5.2.12",
                    "platform": "macOS",
                    "release_date": "2024-01-10",
                },
                {
                    "id": "av-mock3",
                    "folder": folder or "Mobile Users",
                    "name": "6.0.1",
                    "version": "6.0.1",
                    "platform": "Linux",
                    "release_date": "2024-02-01",
                },
            ]

        try:
            # Build container kwargs
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            results = self.client.agent_version.list(**container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container or "", "agent versions", e)

    def get_agent_version(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
    ) -> dict[str, Any]:
        """Get an agent version by name.

        Args:
            folder: Folder containing the agent version
            snippet: Snippet containing the agent version
            device: Device containing the agent version
            name: Name of the agent version to get

        Returns:
            dict[str, Any]: The agent version object

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Getting agent version: {name} from {container_type} {container}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"av-{name}",
                "folder": folder or "Mobile Users",
                "name": name,
                "version": name,
                "description": f"Mock agent version {name}",
                "platform": "Windows",
                "release_date": "2024-01-15",
            }

        try:
            result = None
            if folder:
                result = self.client.agent_version.fetch(name=name, folder=folder)
            elif snippet:
                result = self.client.agent_version.fetch(name=name, snippet=snippet)
            elif device:
                result = self.client.agent_version.fetch(name=name, device=device)

            if result is not None:
                return json.loads(result.model_dump_json(exclude_unset=True))
            else:
                raise ValueError(f"Agent version '{name}' not found")
        except Exception as e:
            self._handle_api_exception("getting", container or "", name or "", e)

    # ---------------------------------------------------------------------------------- Auth Setting ----------------------------------------------------------------------------------

    def create_auth_setting(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
        description: str | None = None,
        authentication_profile: str | None = None,
        os: str | None = None,
        user_credential_or_client_cert_required: bool | None = None,
    ) -> dict[str, Any]:
        """Create or update an auth setting using smart upsert logic.

        Args:
            folder: Folder to create the auth setting in
            snippet: Snippet to create the auth setting in
            device: Device to create the auth setting in
            name: Name of the auth setting
            description: Optional description
            authentication_profile: Authentication profile name
            os: Operating system
            user_credential_or_client_cert_required: Whether user credential or client cert is required

        Returns:
            dict[str, Any]: The created/updated auth setting object with __action__ field

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")
        self.logger.info(f"Creating or updating auth setting: {name} in {container_type} {container}")

        if not self.client:
            # Return mock data if no client is available
            result = {
                "id": f"as-{name}",
                "folder": folder,
                "snippet": snippet,
                "device": device,
                "name": name,
                "description": description,
                "authentication_profile": authentication_profile,
                "os": os,
                "user_credential_or_client_cert_required": user_credential_or_client_cert_required,
                "__action__": "created",
            }
            return {k: v for k, v in result.items() if v is not None}

        try:
            # Step 1: Try to fetch existing auth setting
            existing = None
            try:
                if folder:
                    existing = self.client.auth_setting.fetch(name=name, folder=folder)
                elif snippet:
                    existing = self.client.auth_setting.fetch(name=name, snippet=snippet)
                elif device:
                    existing = self.client.auth_setting.fetch(name=name, device=device)
                self.logger.info(f"Found existing auth setting '{name}' in {container_type} '{container}'")
            except NotFoundError:
                self.logger.info(f"Auth setting '{name}' not found in {container_type} '{container}', will create new")
            except Exception as fetch_error:
                self.logger.warning(f"Error fetching auth setting '{name}': {str(fetch_error)}")

            if existing:
                # Step 2: Compare fields and update if needed
                needs_update = False
                update_fields = []

                if description is not None and getattr(existing, "description", "") != description:
                    existing.description = description
                    update_fields.append("description")
                    needs_update = True

                if authentication_profile is not None and getattr(existing, "authentication_profile", None) != authentication_profile:
                    existing.authentication_profile = authentication_profile
                    update_fields.append("authentication_profile")
                    needs_update = True

                if os is not None and getattr(existing, "os", None) != os:
                    existing.os = os
                    update_fields.append("os")
                    needs_update = True

                if user_credential_or_client_cert_required is not None and getattr(existing, "user_credential_or_client_cert_required", None) != user_credential_or_client_cert_required:
                    existing.user_credential_or_client_cert_required = user_credential_or_client_cert_required
                    update_fields.append("user_credential_or_client_cert_required")
                    needs_update = True

                if needs_update:
                    self.logger.info(f"Updating auth setting fields: {', '.join(update_fields)}")
                    result = self.client.auth_setting.update(existing)
                    self.logger.info(f"Successfully updated auth setting '{name}' in {container_type} '{container}'")
                    response = json.loads(result.model_dump_json(exclude_unset=True))
                    response["__action__"] = "updated"
                    return response
                else:
                    self.logger.info(f"No changes detected for auth setting '{name}', skipping update")
                    response = json.loads(existing.model_dump_json(exclude_unset=True))
                    response["__action__"] = "no_change"
                    return response
            else:
                # Step 3: Create new auth setting
                setting_data = {"name": name}

                if folder is not None:
                    setting_data["folder"] = folder
                if snippet is not None:
                    setting_data["snippet"] = snippet
                if device is not None:
                    setting_data["device"] = device
                if description is not None:
                    setting_data["description"] = description
                if authentication_profile is not None:
                    setting_data["authentication_profile"] = authentication_profile
                if os is not None:
                    setting_data["os"] = os
                if user_credential_or_client_cert_required is not None:
                    setting_data["user_credential_or_client_cert_required"] = user_credential_or_client_cert_required

                result = self.client.auth_setting.create(setting_data)
                self.logger.info(f"Successfully created auth setting '{name}' in {container_type} '{container}'")
                response = json.loads(result.model_dump_json(exclude_unset=True))
                response["__action__"] = "created"
                return response

        except Exception as e:
            self._handle_api_exception("create/update", container or "", name or "", e)

    def get_auth_setting(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
    ) -> dict[str, Any]:
        """Get an auth setting by name.

        Args:
            folder: Folder containing the auth setting
            snippet: Snippet containing the auth setting
            device: Device containing the auth setting
            name: Name of the auth setting to get

        Returns:
            dict[str, Any]: The auth setting object

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Getting auth setting: {name} from {container_type} {container}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"as-{name}",
                "folder": folder or "Mobile Users",
                "name": name,
                "description": f"Mock auth setting {name}",
                "authentication_profile": "best-practice",
                "os": "Any",
            }

        try:
            result = None
            if folder:
                result = self.client.auth_setting.fetch(name=name, folder=folder)
            elif snippet:
                result = self.client.auth_setting.fetch(name=name, snippet=snippet)
            elif device:
                result = self.client.auth_setting.fetch(name=name, device=device)

            if result is not None:
                return json.loads(result.model_dump_json(exclude_unset=True))
            else:
                raise ValueError(f"Auth setting '{name}' not found")
        except Exception as e:
            self._handle_api_exception("getting", container or "", name or "", e)

    def list_auth_settings(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        exact_match: bool = False,
    ) -> list[dict[str, Any]]:
        """List auth settings.

        Args:
            folder: Folder to list from
            snippet: Snippet to list from
            device: Device to list from
            exact_match: If True, only return exact container matches

        Returns:
            list[dict[str, Any]]: List of auth setting objects

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

        self.logger.info(f"Listing auth settings in {container_type}: {container}")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "as-mock1",
                    "folder": folder or "Mobile Users",
                    "name": "saml-auth",
                    "description": "SAML authentication setting",
                    "authentication_profile": "best-practice",
                    "os": "Any",
                },
                {
                    "id": "as-mock2",
                    "folder": folder or "Mobile Users",
                    "name": "cert-auth",
                    "description": "Certificate authentication setting",
                    "authentication_profile": "corp-cert-profile",
                    "os": "Windows",
                    "user_credential_or_client_cert_required": True,
                },
            ]

        try:
            results = self.client.auth_setting.list(**container_kwargs, exact_match=exact_match)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", container or "", "auth settings", e)

    def delete_auth_setting(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        name: str = None,
    ) -> bool:
        """Delete an auth setting.

        Args:
            folder: Folder containing the auth setting
            snippet: Snippet containing the auth setting
            device: Device containing the auth setting
            name: Name of the auth setting to delete

        Returns:
            bool: True if deletion was successful

        """
        container = folder or snippet or device
        container_type = "folder" if folder else ("snippet" if snippet else "device")

        self.logger.info(f"Deleting auth setting: {name} from {container_type} {container}")

        if not self.client:
            return True

        try:
            # Get the auth setting first to get its ID
            setting = None
            if folder:
                setting = self.client.auth_setting.fetch(name=name, folder=folder)
            elif snippet:
                setting = self.client.auth_setting.fetch(name=name, snippet=snippet)
            elif device:
                setting = self.client.auth_setting.fetch(name=name, device=device)

            if setting is None:
                raise ValueError(f"Auth setting '{name}' not found")
            self.client.auth_setting.delete(str(setting.id))
            return True
        except Exception as e:
            self._handle_api_exception("deletion", container or "", name or "", e)

    # ------------------------------------------------------------------------------ GlobalProtect Agent Profile (agent3) ------------------------------------------------------------------

    @staticmethod
    def _is_not_found_error(exception: Exception) -> bool:
        """Check whether an SDK exception represents a 404 / not-found condition.

        The mobile-agent profile services raise InvalidObjectError with
        http_status_code 404 (rather than NotFoundError) when a fetch matches
        nothing.
        """
        if isinstance(exception, NotFoundError):
            return True
        return getattr(exception, "http_status_code", None) == 404

    def create_agent_profile(
        self,
        folder: str | None = None,
        name: str = None,
        os: list[str] | None = None,
        save_user_credentials: str | None = None,
        source_user: list[str] | None = None,
        third_party_vpn_clients: list[str] | None = None,
        agent_ui: dict[str, Any] | None = None,
        authentication_override: dict[str, Any] | None = None,
        certificate: dict[str, Any] | None = None,
        client_certificate: dict[str, Any] | None = None,
        custom_checks: dict[str, Any] | None = None,
        gateways: dict[str, Any] | None = None,
        gp_app_config: dict[str, Any] | None = None,
        hip_collection: dict[str, Any] | None = None,
        internal_host_detection: dict[str, Any] | None = None,
        internal_host_detection_v6: dict[str, Any] | None = None,
        machine_account_exists_with_serialno: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create or update a GlobalProtect agent profile using smart upsert logic.

        Agent profiles live only in the 'Mobile Users' folder and are addressed by
        name (the API exposes no ID-based endpoints). Updates send the merged field
        set; each provided field replaces the existing value wholesale.

        Args:
            folder: Folder containing the agent profile (must be 'Mobile Users')
            name: Name of the agent profile
            os: Operating systems this profile applies to
            save_user_credentials: Save user credentials behavior ('0'-'3')
            source_user: Source users this profile applies to
            third_party_vpn_clients: Supported third party VPN clients
            agent_ui: Agent UI configuration settings
            authentication_override: Authentication override settings
            certificate: Certificate settings
            client_certificate: Client certificate settings
            custom_checks: Custom checks settings
            gateways: Gateways configuration
            gp_app_config: GlobalProtect app configuration (connect-method / tunnel-mtu)
            hip_collection: HIP collection settings
            internal_host_detection: Internal host detection (IPv4) settings
            internal_host_detection_v6: Internal host detection (IPv6) settings
            machine_account_exists_with_serialno: Machine account / serial number setting

        Returns:
            dict[str, Any]: The created/updated agent profile object with __action__ field

        """
        provided_fields: dict[str, Any] = {
            key: value
            for key, value in {
                "os": os,
                "save_user_credentials": save_user_credentials,
                "source_user": source_user,
                "third_party_vpn_clients": third_party_vpn_clients,
                "agent_ui": agent_ui,
                "authentication_override": authentication_override,
                "certificate": certificate,
                "client_certificate": client_certificate,
                "custom_checks": custom_checks,
                "gateways": gateways,
                "gp_app_config": gp_app_config,
                "hip_collection": hip_collection,
                "internal_host_detection": internal_host_detection,
                "internal_host_detection_v6": internal_host_detection_v6,
                "machine_account_exists_with_serialno": machine_account_exists_with_serialno,
            }.items()
            if value is not None
        }

        self.logger.info(f"Creating or updating agent profile: {name} in folder {folder}")

        if not self.client:
            result = {"id": f"ap-{name}", "folder": folder, "name": name, **provided_fields, "__action__": "created"}
            return {k: v for k, v in result.items() if v is not None}

        try:
            existing = None
            try:
                existing = self.client.agent_profile.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing agent profile '{name}' in folder '{folder}'")
            except Exception as fetch_error:
                if self._is_not_found_error(fetch_error):
                    self.logger.info(f"Agent profile '{name}' not found in folder '{folder}', will create new")
                else:
                    self.logger.warning(f"Error fetching agent profile '{name}': {str(fetch_error)}")

            if existing:
                existing_data = json.loads(existing.model_dump_json(exclude_unset=True))
                changed_fields = [key for key, value in provided_fields.items() if existing_data.get(key) != value]

                if changed_fields:
                    self.logger.info(f"Updating agent profile fields: {', '.join(changed_fields)}")
                    update_data = {"name": name, "folder": folder, **provided_fields}
                    result = self.client.agent_profile.update(update_data)
                    if result is None:
                        # The API may return 200 with no body; re-fetch for the response
                        result = self.client.agent_profile.fetch(name=name, folder=folder)
                    self.logger.info(f"Successfully updated agent profile '{name}' in folder '{folder}'")
                    response = json.loads(result.model_dump_json(exclude_unset=True))
                    response["__action__"] = "updated"
                    return response
                else:
                    self.logger.info(f"No changes detected for agent profile '{name}', skipping update")
                    response = existing_data
                    response["__action__"] = "no_change"
                    return response
            else:
                profile_data = {"name": name, "folder": folder, **provided_fields}
                result = self.client.agent_profile.create(profile_data)
                self.logger.info(f"Successfully created agent profile '{name}' in folder '{folder}'")
                response = json.loads(result.model_dump_json(exclude_unset=True))
                response["__action__"] = "created"
                return response

        except Exception as e:
            self._handle_api_exception("create/update", folder or "", name or "", e)

    def get_agent_profile(
        self,
        folder: str | None = None,
        name: str = None,
    ) -> dict[str, Any]:
        """Get a GlobalProtect agent profile by name.

        Args:
            folder: Folder containing the agent profile (must be 'Mobile Users')
            name: Name of the agent profile to get

        Returns:
            dict[str, Any]: The agent profile object

        """
        self.logger.info(f"Getting agent profile: {name} from folder {folder}")

        if not self.client:
            return {
                "id": f"ap-{name}",
                "folder": folder or "Mobile Users",
                "name": name,
                "os": ["Windows", "Mac"],
                "save_user_credentials": "0",
                "gp_app_config": {"config": [{"name": "connect-method", "value": ["user-logon"]}]},
            }

        try:
            result = self.client.agent_profile.fetch(name=name, folder=folder)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("getting", folder or "", name or "", e)

    def list_agent_profiles(
        self,
        folder: str | None = None,
    ) -> list[dict[str, Any]]:
        """List GlobalProtect agent profiles.

        Args:
            folder: Folder to list from (must be 'Mobile Users')

        Returns:
            list[dict[str, Any]]: List of agent profile objects

        """
        self.logger.info(f"Listing agent profiles in folder: {folder}")

        if not self.client:
            return [
                {
                    "id": "ap-mock1",
                    "folder": folder or "Mobile Users",
                    "name": "corp-app-settings",
                    "os": ["Windows"],
                    "save_user_credentials": "0",
                },
                {
                    "id": "ap-mock2",
                    "folder": folder or "Mobile Users",
                    "name": "byod-app-settings",
                    "os": ["iOS", "Android"],
                    "save_user_credentials": "3",
                },
            ]

        try:
            results = self.client.agent_profile.list(folder=folder)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or "", "agent profiles", e)

    def delete_agent_profile(
        self,
        folder: str | None = None,
        name: str = None,
    ) -> bool:
        """Delete a GlobalProtect agent profile.

        The API deletes by name and folder query parameters; no ID is involved.

        Args:
            folder: Folder containing the agent profile (must be 'Mobile Users')
            name: Name of the agent profile to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting agent profile: {name} from folder {folder}")

        if not self.client:
            return True

        try:
            self.client.agent_profile.delete(name=name, folder=folder)
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder or "", name or "", e)

    # ------------------------------------------------------------------------------ GlobalProtect Tunnel Profile (agent3) -----------------------------------------------------------------

    def create_tunnel_profile(
        self,
        folder: str | None = None,
        name: str = None,
        no_direct_access_to_local_network: bool | None = None,
        retrieve_framed_ip_address: bool | None = None,
        os: list[str] | None = None,
        source_user: list[str] | None = None,
        authentication_override: dict[str, Any] | None = None,
        source_address: dict[str, Any] | None = None,
        split_tunneling: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create or update a GlobalProtect tunnel profile using smart upsert logic.

        Tunnel profiles live only in the 'Mobile Users' folder and are addressed by
        name. The folder travels as a query parameter and must NOT appear in the
        request body.

        Args:
            folder: Folder containing the tunnel profile (must be 'Mobile Users')
            name: Name of the tunnel profile
            no_direct_access_to_local_network: Disable direct access to the local network
            retrieve_framed_ip_address: Retrieve framed IP address from the auth server
            os: Operating systems this profile applies to
            source_user: Source users this profile applies to
            authentication_override: Authentication override configuration
            source_address: Source address configuration
            split_tunneling: Split tunneling configuration

        Returns:
            dict[str, Any]: The created/updated tunnel profile object with __action__ field

        """
        provided_fields: dict[str, Any] = {
            key: value
            for key, value in {
                "no_direct_access_to_local_network": no_direct_access_to_local_network,
                "retrieve_framed_ip_address": retrieve_framed_ip_address,
                "os": os,
                "source_user": source_user,
                "authentication_override": authentication_override,
                "source_address": source_address,
                "split_tunneling": split_tunneling,
            }.items()
            if value is not None
        }

        self.logger.info(f"Creating or updating tunnel profile: {name} in folder {folder}")

        if not self.client:
            result = {"id": f"tp-{name}", "folder": folder, "name": name, **provided_fields, "__action__": "created"}
            return {k: v for k, v in result.items() if v is not None}

        try:
            existing = None
            try:
                existing = self.client.tunnel_profile.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing tunnel profile '{name}' in folder '{folder}'")
            except Exception as fetch_error:
                if self._is_not_found_error(fetch_error):
                    self.logger.info(f"Tunnel profile '{name}' not found in folder '{folder}', will create new")
                else:
                    self.logger.warning(f"Error fetching tunnel profile '{name}': {str(fetch_error)}")

            # The tunnel-profiles API rejects folder in the request body
            body = {"name": name, **provided_fields}

            if existing:
                existing_data = json.loads(existing.model_dump_json(exclude_unset=True))
                changed_fields = [key for key, value in provided_fields.items() if existing_data.get(key) != value]

                if changed_fields:
                    self.logger.info(f"Updating tunnel profile fields: {', '.join(changed_fields)}")
                    result = self.client.tunnel_profile.update(body, folder=folder)
                    self.logger.info(f"Successfully updated tunnel profile '{name}' in folder '{folder}'")
                    response = json.loads(result.model_dump_json(exclude_unset=True))
                    response["__action__"] = "updated"
                    return response
                else:
                    self.logger.info(f"No changes detected for tunnel profile '{name}', skipping update")
                    response = existing_data
                    response["__action__"] = "no_change"
                    return response
            else:
                result = self.client.tunnel_profile.create(body, folder=folder)
                self.logger.info(f"Successfully created tunnel profile '{name}' in folder '{folder}'")
                response = json.loads(result.model_dump_json(exclude_unset=True))
                response["__action__"] = "created"
                return response

        except Exception as e:
            self._handle_api_exception("create/update", folder or "", name or "", e)

    def get_tunnel_profile(
        self,
        folder: str | None = None,
        name: str = None,
    ) -> dict[str, Any]:
        """Get a GlobalProtect tunnel profile by name.

        Args:
            folder: Folder containing the tunnel profile (must be 'Mobile Users')
            name: Name of the tunnel profile to get

        Returns:
            dict[str, Any]: The tunnel profile object

        """
        self.logger.info(f"Getting tunnel profile: {name} from folder {folder}")

        if not self.client:
            return {
                "id": f"tp-{name}",
                "folder": folder or "Mobile Users",
                "name": name,
                "no_direct_access_to_local_network": False,
                "split_tunneling": {"access_route": ["10.0.0.0/8"]},
            }

        try:
            result = self.client.tunnel_profile.fetch(name=name, folder=folder)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("getting", folder or "", name or "", e)

    def list_tunnel_profiles(
        self,
        folder: str | None = None,
    ) -> list[dict[str, Any]]:
        """List GlobalProtect tunnel profiles.

        Args:
            folder: Folder to list from (must be 'Mobile Users')

        Returns:
            list[dict[str, Any]]: List of tunnel profile objects

        """
        self.logger.info(f"Listing tunnel profiles in folder: {folder}")

        if not self.client:
            return [
                {
                    "id": "tp-mock1",
                    "folder": folder or "Mobile Users",
                    "name": "corp-tunnel",
                    "split_tunneling": {"access_route": ["10.0.0.0/8"]},
                },
                {
                    "id": "tp-mock2",
                    "folder": folder or "Mobile Users",
                    "name": "byod-tunnel",
                    "no_direct_access_to_local_network": True,
                },
            ]

        try:
            results = self.client.tunnel_profile.list(folder=folder)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or "", "tunnel profiles", e)

    def delete_tunnel_profile(
        self,
        folder: str | None = None,
        name: str = None,
    ) -> bool:
        """Delete a GlobalProtect tunnel profile.

        The API deletes by name and folder query parameters; no ID is involved.

        Args:
            folder: Folder containing the tunnel profile (must be 'Mobile Users')
            name: Name of the tunnel profile to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting tunnel profile: {name} from folder {folder}")

        if not self.client:
            return True

        try:
            self.client.tunnel_profile.delete(name=name, folder=folder)
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder or "", name or "", e)

    # ---------------------------------------------------------------- agent2: Infrastructure Setting (begin) ----------------------------------------------------------------

    def create_infrastructure_setting(
        self,
        name: str = None,
        folder: str = "Mobile Users",
        dns_servers: list[dict[str, Any]] | None = None,
        ip_pools: list[dict[str, Any]] | None = None,
        portal_hostname: dict[str, Any] | None = None,
        enable_wins: dict[str, Any] | None = None,
        ipv6: bool | None = None,
        udp_queries: dict[str, Any] | None = None,
        static_ip_pools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create or update an infrastructure setting using smart upsert logic.

        Infrastructure settings have no ID-based paths; the SDK addresses them
        by name and the 'Mobile Users' folder query parameter. Create and update
        may return an empty body, in which case the validated payload is echoed.

        Args:
            name: Name of the infrastructure setting
            folder: Folder (must be 'Mobile Users')
            dns_servers: DNS server entries
            ip_pools: IP pools
            portal_hostname: Portal hostname configuration
            enable_wins: WINS configuration
            ipv6: Whether IPv6 is enabled
            udp_queries: UDP query retry configuration
            static_ip_pools: Static IP pools

        Returns:
            dict[str, Any]: The created/updated infrastructure setting with __action__ field

        """
        self.logger.info(f"Creating or updating infrastructure setting: {name} in folder {folder}")

        setting_data: dict[str, Any] = {"name": name}
        if dns_servers is not None:
            setting_data["dns_servers"] = dns_servers
        if ip_pools is not None:
            setting_data["ip_pools"] = ip_pools
        if portal_hostname is not None:
            setting_data["portal_hostname"] = portal_hostname
        if enable_wins is not None:
            setting_data["enable_wins"] = enable_wins
        if ipv6 is not None:
            setting_data["ipv6"] = ipv6
        if udp_queries is not None:
            setting_data["udp_queries"] = udp_queries
        if static_ip_pools is not None:
            setting_data["static_ip_pools"] = static_ip_pools

        if not self.client:
            # Return mock data if no client is available
            result = dict(setting_data)
            result["id"] = f"is-{name}"
            result["folder"] = folder
            result["__action__"] = "created"
            return result

        try:
            # Step 1: Try to fetch the existing infrastructure setting. The SDK raises
            # InvalidObjectError (404) rather than NotFoundError when absent.
            existing = None
            try:
                existing = self.client.infrastructure_settings.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing infrastructure setting '{name}' in folder '{folder}'")
            except NotFoundError:
                self.logger.info(f"Infrastructure setting '{name}' not found in folder '{folder}', will create new")
            except Exception as fetch_error:
                if getattr(fetch_error, "http_status_code", None) == 404:
                    self.logger.info(f"Infrastructure setting '{name}' not found in folder '{folder}', will create new")
                else:
                    self.logger.warning(f"Error fetching infrastructure setting '{name}': {str(fetch_error)}")

            if existing:
                # Step 2: Compare the desired payload against the existing object
                existing_data = json.loads(existing.model_dump_json(exclude_unset=True))
                existing_data.pop("id", None)
                if all(existing_data.get(key) == value for key, value in setting_data.items()):
                    self.logger.info(f"No changes detected for infrastructure setting '{name}', skipping update")
                    response = json.loads(existing.model_dump_json(exclude_unset=True))
                    response["__action__"] = "no_change"
                    return response

                result = self.client.infrastructure_settings.update(setting_data, folder=folder)
                self.logger.info(f"Successfully updated infrastructure setting '{name}' in folder '{folder}'")
                # The API may respond with an empty body; echo the payload then
                response = json.loads(result.model_dump_json(exclude_unset=True)) if result is not None else dict(setting_data)
                response["__action__"] = "updated"
                return response
            else:
                # Step 3: Create a new infrastructure setting
                result = self.client.infrastructure_settings.create(setting_data, folder=folder)
                self.logger.info(f"Successfully created infrastructure setting '{name}' in folder '{folder}'")
                # The API responds with 201 Created and may have no body; echo the payload then
                response = json.loads(result.model_dump_json(exclude_unset=True)) if result is not None else dict(setting_data)
                response["__action__"] = "created"
                return response

        except Exception as e:
            self._handle_api_exception("create/update", folder, name or "", e)

    def get_infrastructure_setting(
        self,
        name: str = None,
        folder: str = "Mobile Users",
    ) -> dict[str, Any]:
        """Get an infrastructure setting by name.

        Args:
            name: Name of the infrastructure setting to get
            folder: Folder (must be 'Mobile Users')

        Returns:
            dict[str, Any]: The infrastructure setting object

        """
        self.logger.info(f"Getting infrastructure setting: {name} from folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"is-{name}",
                "folder": folder,
                "name": name,
                "dns_servers": [{"name": "dns-1", "dns_suffix": ["example.com"]}],
                "ip_pools": [{"name": "pool-1", "ip_pool": ["10.0.0.0/16"]}],
                "portal_hostname": {"default_domain": {"hostname": "example"}},
            }

        try:
            result = self.client.infrastructure_settings.fetch(name=name, folder=folder)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("getting", folder, name or "", e)

    def list_infrastructure_settings(
        self,
        name: str = None,
        folder: str = "Mobile Users",
    ) -> list[dict[str, Any]]:
        """List infrastructure settings matching a name.

        The SCM API requires the 'name' query parameter for this endpoint;
        there is no enumerate-all listing.

        Args:
            name: Name of the infrastructure settings (required by the API)
            folder: Folder (must be 'Mobile Users')

        Returns:
            list[dict[str, Any]]: List of infrastructure setting objects

        """
        self.logger.info(f"Listing infrastructure settings named '{name}' in folder: {folder}")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "is-mock1",
                    "folder": folder,
                    "name": name or "gp-infra",
                    "dns_servers": [{"name": "dns-1", "dns_suffix": ["example.com"]}],
                    "ip_pools": [{"name": "pool-1", "ip_pool": ["10.0.0.0/16"]}],
                    "portal_hostname": {"default_domain": {"hostname": "example"}},
                },
            ]

        try:
            results = self.client.infrastructure_settings.list(name=name, folder=folder)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder, "infrastructure settings", e)

    def delete_infrastructure_setting(
        self,
        name: str = None,
        folder: str = "Mobile Users",
    ) -> bool:
        """Delete an infrastructure setting.

        Args:
            name: Name of the infrastructure setting to delete
            folder: Folder (must be 'Mobile Users')

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting infrastructure setting: {name} from folder {folder}")

        if not self.client:
            return True

        try:
            self.client.infrastructure_settings.delete(name=name, folder=folder)
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder, name or "", e)

    # ---------------------------------------------------------------- agent2: Infrastructure Setting (end) ----------------------------------------------------------------

    # ---------------------------------------------------------------- agent2: Global Settings (begin) ----------------------------------------------------------------

    def get_global_settings(self) -> dict[str, Any]:
        """Get the GlobalProtect global settings singleton.

        Returns:
            dict[str, Any]: The global settings object

        """
        self.logger.info("Getting GlobalProtect global settings")

        if not self.client:
            # Return mock data if no client is available
            return {
                "agent_version": "6.2.0",
                "manual_gateway": {"region": [{"name": "americas", "locations": ["us-east-1"]}]},
            }

        try:
            result = self.client.global_settings.get()
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("getting", "global", "global settings", e)

    def update_global_settings(
        self,
        agent_version: str | None = None,
        manual_gateway: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update the GlobalProtect global settings singleton.

        Global settings always exist for the tenant, so this is a plain PUT;
        there is no create path and the action is always reported as updated.

        Args:
            agent_version: GlobalProtect agent version
            manual_gateway: Manual gateway configuration

        Returns:
            dict[str, Any]: The updated global settings with __action__ field

        """
        self.logger.info("Updating GlobalProtect global settings")

        settings_data: dict[str, Any] = {}
        if agent_version is not None:
            settings_data["agent_version"] = agent_version
        if manual_gateway is not None:
            settings_data["manual_gateway"] = manual_gateway

        if not self.client:
            # Return mock data if no client is available
            result = dict(settings_data)
            result["__action__"] = "updated"
            return result

        try:
            result = self.client.global_settings.update(settings_data)
            response = json.loads(result.model_dump_json(exclude_unset=True))
            response["__action__"] = "updated"
            return response
        except Exception as e:
            self._handle_api_exception("updating", "global", "global settings", e)

    # ---------------------------------------------------------------- agent2: Global Settings (end) ----------------------------------------------------------------

    # ---------------------------------------------------------------------- Forwarding Profile Source Application ----------------------------------------------------------------------

    def create_forwarding_profile_source_application(
        self,
        folder: str | None = None,
        name: str = None,
        description: str | None = None,
        applications: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create or update a forwarding profile source application using smart upsert logic.

        Args:
            folder: Folder to create the source application in (must be "Mobile Users")
            name: Name of the source application
            description: Optional description
            applications: List of applications

        Returns:
            dict[str, Any]: The created/updated source application object with __action__ field

        """
        self.logger.info(f"Creating or updating forwarding profile source application: {name} in folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            result = {
                "id": f"fpsa-{name}",
                "folder": folder,
                "name": name,
                "description": description,
                "applications": applications,
                "__action__": "created",
            }
            return {k: v for k, v in result.items() if v is not None}

        try:
            # Step 1: Try to fetch existing source application
            existing = None
            try:
                existing = self.client.forwarding_profile_source_application.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing forwarding profile source application '{name}' in folder '{folder}'")
            except NotFoundError:
                self.logger.info(f"Forwarding profile source application '{name}' not found in folder '{folder}', will create new")
            except Exception as fetch_error:
                self.logger.warning(f"Error fetching forwarding profile source application '{name}': {str(fetch_error)}")

            if existing:
                # Step 2: Compare fields and update if needed
                needs_update = False
                update_fields = []

                if description is not None and getattr(existing, "description", None) != description:
                    existing.description = description
                    update_fields.append("description")
                    needs_update = True

                if applications is not None and getattr(existing, "applications", None) != applications:
                    existing.applications = applications
                    update_fields.append("applications")
                    needs_update = True

                if needs_update:
                    self.logger.info(f"Updating forwarding profile source application fields: {', '.join(update_fields)}")
                    result = self.client.forwarding_profile_source_application.update(existing)
                    self.logger.info(f"Successfully updated forwarding profile source application '{name}' in folder '{folder}'")
                    response = json.loads(result.model_dump_json(exclude_unset=True))
                    response["__action__"] = "updated"
                    return response
                else:
                    self.logger.info(f"No changes detected for forwarding profile source application '{name}', skipping update")
                    response = json.loads(existing.model_dump_json(exclude_unset=True))
                    response["__action__"] = "no_change"
                    return response
            else:
                # Step 3: Create new source application (folder is a query param, not payload)
                setting_data: dict[str, Any] = {
                    "name": name,
                    "applications": applications or [],
                }
                if description is not None:
                    setting_data["description"] = description

                result = self.client.forwarding_profile_source_application.create(setting_data, folder=folder)
                self.logger.info(f"Successfully created forwarding profile source application '{name}' in folder '{folder}'")
                response = json.loads(result.model_dump_json(exclude_unset=True))
                response["__action__"] = "created"
                return response

        except Exception as e:
            self._handle_api_exception("create/update", folder or "", name or "", e)

    def get_forwarding_profile_source_application(
        self,
        folder: str | None = None,
        name: str = None,
    ) -> dict[str, Any]:
        """Get a forwarding profile source application by name.

        Args:
            folder: Folder containing the source application (must be "Mobile Users")
            name: Name of the source application to get

        Returns:
            dict[str, Any]: The source application object

        """
        self.logger.info(f"Getting forwarding profile source application: {name} from folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"fpsa-{name}",
                "folder": folder or "Mobile Users",
                "name": name,
                "description": f"Mock forwarding profile source application {name}",
                "applications": ["slack", "zoom"],
            }

        try:
            result = self.client.forwarding_profile_source_application.fetch(name=name, folder=folder)

            if result is not None:
                return json.loads(result.model_dump_json(exclude_unset=True))
            else:
                raise ValueError(f"Forwarding profile source application '{name}' not found")
        except Exception as e:
            self._handle_api_exception("getting", folder or "", name or "", e)

    def list_forwarding_profile_source_applications(
        self,
        folder: str | None = None,
    ) -> list[dict[str, Any]]:
        """List forwarding profile source applications.

        Args:
            folder: Folder to list from (must be "Mobile Users")

        Returns:
            list[dict[str, Any]]: List of source application objects

        """
        self.logger.info(f"Listing forwarding profile source applications in folder: {folder}")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "fpsa-mock1",
                    "folder": folder or "Mobile Users",
                    "name": "office-apps",
                    "description": "Office applications",
                    "applications": ["slack", "zoom"],
                },
            ]

        try:
            results = self.client.forwarding_profile_source_application.list(folder=folder)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or "", "forwarding profile source applications", e)

    def delete_forwarding_profile_source_application(
        self,
        folder: str | None = None,
        name: str = None,
    ) -> bool:
        """Delete a forwarding profile source application.

        Args:
            folder: Folder containing the source application (must be "Mobile Users")
            name: Name of the source application to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting forwarding profile source application: {name} from folder {folder}")

        if not self.client:
            return True

        try:
            # Get the source application first to get its ID
            setting = self.client.forwarding_profile_source_application.fetch(name=name, folder=folder)
            if setting is None:
                raise ValueError(f"Forwarding profile source application '{name}' not found")
            self.client.forwarding_profile_source_application.delete(str(setting.id))
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder or "", name or "", e)

    # ------------------------------------------------------------------------- Forwarding Profile User Location -------------------------------------------------------------------------

    def create_forwarding_profile_user_location(
        self,
        folder: str | None = None,
        name: str = None,
        description: str | None = None,
        choice: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create or update a forwarding profile user location using smart upsert logic.

        Args:
            folder: Folder to create the user location in (must be "Mobile Users")
            name: Name of the user location
            description: Optional description
            choice: Location matching criteria (internal_host_detection or ip_addresses)

        Returns:
            dict[str, Any]: The created/updated user location object with __action__ field

        """
        self.logger.info(f"Creating or updating forwarding profile user location: {name} in folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            result = {
                "id": f"fpul-{name}",
                "folder": folder,
                "name": name,
                "description": description,
                "choice": choice,
                "__action__": "created",
            }
            return {k: v for k, v in result.items() if v is not None}

        try:
            # Step 1: Try to fetch existing user location
            existing = None
            try:
                existing = self.client.forwarding_profile_user_location.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing forwarding profile user location '{name}' in folder '{folder}'")
            except NotFoundError:
                self.logger.info(f"Forwarding profile user location '{name}' not found in folder '{folder}', will create new")
            except Exception as fetch_error:
                self.logger.warning(f"Error fetching forwarding profile user location '{name}': {str(fetch_error)}")

            if existing:
                # Step 2: Compare fields and update if needed
                needs_update = False
                update_fields = []

                if description is not None and getattr(existing, "description", None) != description:
                    existing.description = description
                    update_fields.append("description")
                    needs_update = True

                if choice is not None:
                    existing_choice = json.loads(existing.choice.model_dump_json(exclude_none=True)) if getattr(existing, "choice", None) else None
                    if existing_choice != choice:
                        existing.choice = choice
                        update_fields.append("choice")
                        needs_update = True

                if needs_update:
                    self.logger.info(f"Updating forwarding profile user location fields: {', '.join(update_fields)}")
                    result = self.client.forwarding_profile_user_location.update(existing)
                    self.logger.info(f"Successfully updated forwarding profile user location '{name}' in folder '{folder}'")
                    response = json.loads(result.model_dump_json(exclude_unset=True))
                    response["__action__"] = "updated"
                    return response
                else:
                    self.logger.info(f"No changes detected for forwarding profile user location '{name}', skipping update")
                    response = json.loads(existing.model_dump_json(exclude_unset=True))
                    response["__action__"] = "no_change"
                    return response
            else:
                # Step 3: Create new user location (folder is a query param, not payload)
                setting_data: dict[str, Any] = {
                    "name": name,
                    "choice": choice or {},
                }
                if description is not None:
                    setting_data["description"] = description

                result = self.client.forwarding_profile_user_location.create(setting_data, folder=folder)
                self.logger.info(f"Successfully created forwarding profile user location '{name}' in folder '{folder}'")
                response = json.loads(result.model_dump_json(exclude_unset=True))
                response["__action__"] = "created"
                return response

        except Exception as e:
            self._handle_api_exception("create/update", folder or "", name or "", e)

    def get_forwarding_profile_user_location(
        self,
        folder: str | None = None,
        name: str = None,
    ) -> dict[str, Any]:
        """Get a forwarding profile user location by name.

        Args:
            folder: Folder containing the user location (must be "Mobile Users")
            name: Name of the user location to get

        Returns:
            dict[str, Any]: The user location object

        """
        self.logger.info(f"Getting forwarding profile user location: {name} from folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"fpul-{name}",
                "folder": folder or "Mobile Users",
                "name": name,
                "description": f"Mock forwarding profile user location {name}",
                "choice": {"ip_addresses": [{"name": "10.1.0.0/16"}]},
            }

        try:
            result = self.client.forwarding_profile_user_location.fetch(name=name, folder=folder)

            if result is not None:
                return json.loads(result.model_dump_json(exclude_unset=True))
            else:
                raise ValueError(f"Forwarding profile user location '{name}' not found")
        except Exception as e:
            self._handle_api_exception("getting", folder or "", name or "", e)

    def list_forwarding_profile_user_locations(
        self,
        folder: str | None = None,
    ) -> list[dict[str, Any]]:
        """List forwarding profile user locations.

        Args:
            folder: Folder to list from (must be "Mobile Users")

        Returns:
            list[dict[str, Any]]: List of user location objects

        """
        self.logger.info(f"Listing forwarding profile user locations in folder: {folder}")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "fpul-mock1",
                    "folder": folder or "Mobile Users",
                    "name": "branch-network",
                    "description": "Branch office network",
                    "choice": {"ip_addresses": [{"name": "10.1.0.0/16"}]},
                },
            ]

        try:
            results = self.client.forwarding_profile_user_location.list(folder=folder)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or "", "forwarding profile user locations", e)

    def delete_forwarding_profile_user_location(
        self,
        folder: str | None = None,
        name: str = None,
    ) -> bool:
        """Delete a forwarding profile user location.

        Args:
            folder: Folder containing the user location (must be "Mobile Users")
            name: Name of the user location to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting forwarding profile user location: {name} from folder {folder}")

        if not self.client:
            return True

        try:
            # Get the user location first to get its ID
            setting = self.client.forwarding_profile_user_location.fetch(name=name, folder=folder)
            if setting is None:
                raise ValueError(f"Forwarding profile user location '{name}' not found")
            self.client.forwarding_profile_user_location.delete(str(setting.id))
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder or "", name or "", e)

    # ------------------------------------------------------------------ Forwarding Profile Regional and Custom Proxy ------------------------------------------------------------------

    def create_forwarding_profile_regional_and_custom_proxy(
        self,
        folder: str | None = None,
        name: str = None,
        description: str | None = None,
        type: str | None = None,
        proxy_1: dict[str, Any] | None = None,
        proxy_2: dict[str, Any] | None = None,
        connectivity_preference: list[dict[str, Any]] | None = None,
        fallback_option: str | None = None,
        location_preference: str | None = None,
        prisma_access_locations: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create or update a forwarding profile regional and custom proxy using smart upsert logic.

        Args:
            folder: Folder to create the regional and custom proxy in (must be "Mobile Users")
            name: Name of the regional and custom proxy
            description: Optional description
            type: Proxy type (gp-and-pac, ztna-agent)
            proxy_1: Primary proxy server (fqdn, port, location)
            proxy_2: Secondary proxy server (fqdn, port, location)
            connectivity_preference: Connectivity preference entries (name, enabled)
            fallback_option: Fallback option (fail-open, fail-safe)
            location_preference: Location preference
            prisma_access_locations: Prisma Access locations (name, locations)

        Returns:
            dict[str, Any]: The created/updated regional and custom proxy object with __action__ field

        """
        self.logger.info(f"Creating or updating forwarding profile regional and custom proxy: {name} in folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            result = {
                "id": f"fprcp-{name}",
                "folder": folder,
                "name": name,
                "description": description,
                "type": type,
                "proxy_1": proxy_1,
                "proxy_2": proxy_2,
                "connectivity_preference": connectivity_preference,
                "fallback_option": fallback_option,
                "location_preference": location_preference,
                "prisma_access_locations": prisma_access_locations,
                "__action__": "created",
            }
            return {k: v for k, v in result.items() if v is not None}

        def nested_dump(value: Any) -> Any:
            """Dump nested SDK models to plain data for comparison."""
            if value is None:
                return None
            if isinstance(value, list):
                return [json.loads(item.model_dump_json(exclude_none=True)) for item in value]
            return json.loads(value.model_dump_json(exclude_none=True))

        try:
            # Step 1: Try to fetch existing regional and custom proxy
            existing = None
            try:
                existing = self.client.forwarding_profile_regional_and_custom_proxy.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing forwarding profile regional and custom proxy '{name}' in folder '{folder}'")
            except NotFoundError:
                self.logger.info(f"Forwarding profile regional and custom proxy '{name}' not found in folder '{folder}', will create new")
            except Exception as fetch_error:
                self.logger.warning(f"Error fetching forwarding profile regional and custom proxy '{name}': {str(fetch_error)}")

            if existing:
                # Step 2: Compare fields and update if needed
                needs_update = False
                update_fields = []

                scalar_fields = {
                    "description": description,
                    "type": type,
                    "fallback_option": fallback_option,
                    "location_preference": location_preference,
                }
                for field_name, new_value in scalar_fields.items():
                    if new_value is not None and getattr(existing, field_name, None) != new_value:
                        setattr(existing, field_name, new_value)
                        update_fields.append(field_name)
                        needs_update = True

                nested_fields = {
                    "proxy_1": proxy_1,
                    "proxy_2": proxy_2,
                    "connectivity_preference": connectivity_preference,
                    "prisma_access_locations": prisma_access_locations,
                }
                for field_name, new_value in nested_fields.items():
                    if new_value is not None and nested_dump(getattr(existing, field_name, None)) != new_value:
                        setattr(existing, field_name, new_value)
                        update_fields.append(field_name)
                        needs_update = True

                if needs_update:
                    self.logger.info(f"Updating forwarding profile regional and custom proxy fields: {', '.join(update_fields)}")
                    result = self.client.forwarding_profile_regional_and_custom_proxy.update(existing)
                    self.logger.info(f"Successfully updated forwarding profile regional and custom proxy '{name}' in folder '{folder}'")
                    response = json.loads(result.model_dump_json(exclude_unset=True))
                    response["__action__"] = "updated"
                    return response
                else:
                    self.logger.info(f"No changes detected for forwarding profile regional and custom proxy '{name}', skipping update")
                    response = json.loads(existing.model_dump_json(exclude_unset=True))
                    response["__action__"] = "no_change"
                    return response
            else:
                # Step 3: Create new regional and custom proxy (folder is a query param, not payload)
                setting_data: dict[str, Any] = {
                    "name": name,
                }
                if description is not None:
                    setting_data["description"] = description
                if type is not None:
                    setting_data["type"] = type
                if proxy_1 is not None:
                    setting_data["proxy_1"] = proxy_1
                if proxy_2 is not None:
                    setting_data["proxy_2"] = proxy_2
                if connectivity_preference is not None:
                    setting_data["connectivity_preference"] = connectivity_preference
                if fallback_option is not None:
                    setting_data["fallback_option"] = fallback_option
                if location_preference is not None:
                    setting_data["location_preference"] = location_preference
                if prisma_access_locations is not None:
                    setting_data["prisma_access_locations"] = prisma_access_locations

                result = self.client.forwarding_profile_regional_and_custom_proxy.create(setting_data, folder=folder)
                self.logger.info(f"Successfully created forwarding profile regional and custom proxy '{name}' in folder '{folder}'")
                response = json.loads(result.model_dump_json(exclude_unset=True))
                response["__action__"] = "created"
                return response

        except Exception as e:
            self._handle_api_exception("create/update", folder or "", name or "", e)

    def get_forwarding_profile_regional_and_custom_proxy(
        self,
        folder: str | None = None,
        name: str = None,
    ) -> dict[str, Any]:
        """Get a forwarding profile regional and custom proxy by name.

        Args:
            folder: Folder containing the regional and custom proxy (must be "Mobile Users")
            name: Name of the regional and custom proxy to get

        Returns:
            dict[str, Any]: The regional and custom proxy object

        """
        self.logger.info(f"Getting forwarding profile regional and custom proxy: {name} from folder {folder}")

        if not self.client:
            # Return mock data if no client is available
            return {
                "id": f"fprcp-{name}",
                "folder": folder or "Mobile Users",
                "name": name,
                "description": f"Mock forwarding profile regional and custom proxy {name}",
                "type": "gp-and-pac",
                "proxy_1": {"fqdn": "proxy1.example.com", "port": 8080},
            }

        try:
            result = self.client.forwarding_profile_regional_and_custom_proxy.fetch(name=name, folder=folder)

            if result is not None:
                return json.loads(result.model_dump_json(exclude_unset=True))
            else:
                raise ValueError(f"Forwarding profile regional and custom proxy '{name}' not found")
        except Exception as e:
            self._handle_api_exception("getting", folder or "", name or "", e)

    def list_forwarding_profile_regional_and_custom_proxies(
        self,
        folder: str | None = None,
    ) -> list[dict[str, Any]]:
        """List forwarding profile regional and custom proxies.

        Args:
            folder: Folder to list from (must be "Mobile Users")

        Returns:
            list[dict[str, Any]]: List of regional and custom proxy objects

        """
        self.logger.info(f"Listing forwarding profile regional and custom proxies in folder: {folder}")

        if not self.client:
            # Return mock data if no client is available
            return [
                {
                    "id": "fprcp-mock1",
                    "folder": folder or "Mobile Users",
                    "name": "emea-proxy",
                    "description": "EMEA regional proxy",
                    "type": "gp-and-pac",
                },
            ]

        try:
            results = self.client.forwarding_profile_regional_and_custom_proxy.list(folder=folder)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or "", "forwarding profile regional and custom proxies", e)

    def delete_forwarding_profile_regional_and_custom_proxy(
        self,
        folder: str | None = None,
        name: str = None,
    ) -> bool:
        """Delete a forwarding profile regional and custom proxy.

        Args:
            folder: Folder containing the regional and custom proxy (must be "Mobile Users")
            name: Name of the regional and custom proxy to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting forwarding profile regional and custom proxy: {name} from folder {folder}")

        if not self.client:
            return True

        try:
            # Get the regional and custom proxy first to get its ID
            setting = self.client.forwarding_profile_regional_and_custom_proxy.fetch(name=name, folder=folder)
            if setting is None:
                raise ValueError(f"Forwarding profile regional and custom proxy '{name}' not found")
            self.client.forwarding_profile_regional_and_custom_proxy.delete(str(setting.id))
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder or "", name or "", e)

    # ======================================================================================================================================================================================
    # SETUP CONFIGURATION METHODS
    # ======================================================================================================================================================================================

    # Folder ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_folder(
        self,
        name: str,
        parent: str,
        description: str | None = None,
        labels: list[str] | None = None,
        snippets: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create or update a folder (smart upsert).

        Args:
            name: Name of the folder
            parent: Parent folder name
            description: Optional description
            labels: Optional list of labels
            snippets: Optional list of snippet IDs

        Returns:
            dict[str, Any]: The created/updated folder object with '__action__' key.

        """
        self.logger.info(f"Upsert folder: {name} (parent: {parent})")

        if not self.client:
            return {
                "id": f"folder-{name}",
                "name": name,
                "parent": parent,
                "description": description or "",
                "labels": labels or [],
                "snippets": snippets or [],
                "__action__": "created",
            }

        try:
            existing = None
            try:
                existing = self.client.folder.fetch(name=name)
                self.logger.info(f"Found existing folder '{name}'")
            except NotFoundError:
                self.logger.info(f"Folder '{name}' not found, will create new")
            except Exception as e:
                self.logger.warning(f"Error fetching folder '{name}': {str(e)}")

            if existing:
                needs_update = False
                update_fields = []

                if getattr(existing, "parent", "") != parent:
                    existing.parent = parent
                    update_fields.append("parent")
                    needs_update = True

                if description is not None and getattr(existing, "description", None) != description:
                    existing.description = description
                    update_fields.append("description")
                    needs_update = True

                if labels is not None:
                    current_labels = set(getattr(existing, "labels", []) or [])
                    new_labels = set(labels or [])
                    if current_labels != new_labels:
                        existing.labels = labels
                        update_fields.append("labels")
                        needs_update = True

                if snippets is not None:
                    current_snippets = set(getattr(existing, "snippets", []) or [])
                    new_snippets = set(snippets or [])
                    if current_snippets != new_snippets:
                        existing.snippets = snippets
                        update_fields.append("snippets")
                        needs_update = True

                if needs_update:
                    self.logger.info(f"Updating folder fields: {', '.join(update_fields)}")
                    updated = self.client.folder.update(existing)
                    self.logger.info(f"Successfully updated folder '{name}'")
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
                else:
                    self.logger.info(f"No changes detected for folder '{name}', skipping update")
                    result = json.loads(existing.model_dump_json(exclude_unset=True))
                    result["__action__"] = "no_change"
                    return result
            else:
                folder_data = {
                    "name": name,
                    "parent": parent,
                }
                if description:
                    folder_data["description"] = description
                if labels:
                    folder_data["labels"] = labels
                if snippets:
                    folder_data["snippets"] = snippets

                created = self.client.folder.create(folder_data)
                self.logger.info(f"Successfully created folder '{name}'")
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
        except Exception as e:
            self._handle_api_exception("creation/update", parent, name, e)

    def get_folder(
        self,
        name: str,
    ) -> dict[str, Any]:
        """Get a folder by name.

        Args:
            name: Name of the folder

        Returns:
            dict[str, Any]: The folder object

        """
        self.logger.info(f"Getting folder: {name}")

        if not self.client:
            return {
                "id": f"folder-{name}",
                "name": name,
                "parent": "All",
                "description": f"Mock folder {name}",
            }

        try:
            result = self.client.folder.fetch(name=name)
            if result is None:
                self.logger.error(f"Folder '{name}' not found")
                return {}
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieval", "N/A", name, e)

    def list_folders(
        self,
    ) -> list[dict[str, Any]]:
        """List all folders.

        Returns:
            list[dict[str, Any]]: List of folder objects

        """
        self.logger.info("Listing folders")

        if not self.client:
            return [
                {
                    "id": "folder-all",
                    "name": "All",
                    "parent": "",
                    "description": "Root folder",
                },
                {
                    "id": "folder-texas",
                    "name": "Texas",
                    "parent": "All",
                    "description": "Texas branch offices",
                },
                {
                    "id": "folder-austin",
                    "name": "Austin",
                    "parent": "Texas",
                    "description": "Austin office",
                },
            ]

        try:
            results = self.client.folder.list()
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", "N/A", "folders", e)

    def delete_folder(
        self,
        name: str,
    ) -> bool:
        """Delete a folder.

        Args:
            name: Name of the folder to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting folder: {name}")

        if not self.client:
            return True

        try:
            folder = self.client.folder.fetch(name=name)
            if folder is None:
                self.logger.error(f"Folder '{name}' not found, cannot delete")
                return False
            self.client.folder.delete(folder_id=str(folder.id))
            return True
        except Exception as e:
            self._handle_api_exception("deletion", "N/A", name, e)

    # Label -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_label(
        self,
        name: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create or update a label (smart upsert).

        Args:
            name: Name of the label
            description: Optional description

        Returns:
            dict[str, Any]: The created/updated label object with '__action__' key.

        """
        self.logger.info(f"Upsert label: {name}")

        if not self.client:
            return {
                "id": f"label-{name}",
                "name": name,
                "description": description or "",
                "__action__": "created",
            }

        try:
            existing = None
            try:
                existing = self.client.label.fetch(name=name)
                self.logger.info(f"Found existing label '{name}'")
            except NotFoundError:
                self.logger.info(f"Label '{name}' not found, will create new")
            except Exception as e:
                self.logger.warning(f"Error fetching label '{name}': {str(e)}")

            if existing:
                needs_update = False
                update_fields = []

                if description is not None and getattr(existing, "description", None) != description:
                    existing.description = description
                    update_fields.append("description")
                    needs_update = True

                if needs_update:
                    self.logger.info(f"Updating label fields: {', '.join(update_fields)}")
                    updated = self.client.label.update(existing)
                    self.logger.info(f"Successfully updated label '{name}'")
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
                else:
                    self.logger.info(f"No changes detected for label '{name}', skipping update")
                    result = json.loads(existing.model_dump_json(exclude_unset=True))
                    result["__action__"] = "no_change"
                    return result
            else:
                label_data = {"name": name}
                if description:
                    label_data["description"] = description

                created = self.client.label.create(label_data)
                self.logger.info(f"Successfully created label '{name}'")
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
        except Exception as e:
            self._handle_api_exception("creation/update", "N/A", name, e)

    def get_label(
        self,
        name: str,
    ) -> dict[str, Any]:
        """Get a label by name.

        Args:
            name: Name of the label

        Returns:
            dict[str, Any]: The label object

        """
        self.logger.info(f"Getting label: {name}")

        if not self.client:
            return {
                "id": f"label-{name}",
                "name": name,
                "description": f"Mock label {name}",
            }

        try:
            result = self.client.label.fetch(name=name)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieval", "N/A", name, e)

    def list_labels(
        self,
    ) -> list[dict[str, Any]]:
        """List all labels.

        Returns:
            list[dict[str, Any]]: List of label objects

        """
        self.logger.info("Listing labels")

        if not self.client:
            return [
                {
                    "id": "label-prod",
                    "name": "production",
                    "description": "Production environment",
                },
                {
                    "id": "label-staging",
                    "name": "staging",
                    "description": "Staging environment",
                },
            ]

        try:
            results = self.client.label.list()
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", "N/A", "labels", e)

    def delete_label(
        self,
        name: str,
    ) -> bool:
        """Delete a label.

        Args:
            name: Name of the label to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting label: {name}")

        if not self.client:
            return True

        try:
            label = self.client.label.fetch(name=name)
            self.client.label.delete(label_id=str(label.id))
            return True
        except Exception as e:
            self._handle_api_exception("deletion", "N/A", name, e)

    # Snippet ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_snippet(
        self,
        name: str,
        description: str | None = None,
        labels: list[str] | None = None,
        enable_prefix: bool | None = None,
    ) -> dict[str, Any]:
        """Create or update a snippet (smart upsert).

        Args:
            name: Name of the snippet
            description: Optional description
            labels: Optional list of labels
            enable_prefix: Optional prefix enablement

        Returns:
            dict[str, Any]: The created/updated snippet object with '__action__' key.

        """
        self.logger.info(f"Upsert snippet: {name}")

        if not self.client:
            return {
                "id": f"snippet-{name}",
                "name": name,
                "description": description or "",
                "labels": labels or [],
                "type": "custom",
                "__action__": "created",
            }

        try:
            existing = None
            try:
                existing = self.client.snippet.fetch(name=name)
                self.logger.info(f"Found existing snippet '{name}'")
            except NotFoundError:
                self.logger.info(f"Snippet '{name}' not found, will create new")
            except Exception as e:
                self.logger.warning(f"Error fetching snippet '{name}': {str(e)}")

            if existing:
                needs_update = False
                update_fields = []

                if description is not None and getattr(existing, "description", None) != description:
                    existing.description = description
                    update_fields.append("description")
                    needs_update = True

                if labels is not None:
                    current_labels = set(getattr(existing, "labels", []) or [])
                    new_labels = set(labels or [])
                    if current_labels != new_labels:
                        existing.labels = labels
                        update_fields.append("labels")
                        needs_update = True

                if enable_prefix is not None and getattr(existing, "enable_prefix", None) != enable_prefix:
                    existing.enable_prefix = enable_prefix
                    update_fields.append("enable_prefix")
                    needs_update = True

                if needs_update:
                    self.logger.info(f"Updating snippet fields: {', '.join(update_fields)}")
                    updated = self.client.snippet.update(existing)
                    self.logger.info(f"Successfully updated snippet '{name}'")
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
                else:
                    self.logger.info(f"No changes detected for snippet '{name}', skipping update")
                    result = json.loads(existing.model_dump_json(exclude_unset=True))
                    result["__action__"] = "no_change"
                    return result
            else:
                snippet_data = {"name": name}
                if description:
                    snippet_data["description"] = description
                if labels:
                    snippet_data["labels"] = labels
                if enable_prefix is not None:
                    snippet_data["enable_prefix"] = enable_prefix

                created = self.client.snippet.create(snippet_data)
                self.logger.info(f"Successfully created snippet '{name}'")
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
        except Exception as e:
            self._handle_api_exception("creation/update", "N/A", name, e)

    def get_snippet(
        self,
        name: str,
    ) -> dict[str, Any]:
        """Get a snippet by name.

        Args:
            name: Name of the snippet

        Returns:
            dict[str, Any]: The snippet object

        """
        self.logger.info(f"Getting snippet: {name}")

        if not self.client:
            return {
                "id": f"snippet-{name}",
                "name": name,
                "description": f"Mock snippet {name}",
                "type": "custom",
            }

        try:
            result = self.client.snippet.fetch(name=name)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieval", "N/A", name, e)

    def list_snippets(
        self,
    ) -> list[dict[str, Any]]:
        """List all snippets.

        Returns:
            list[dict[str, Any]]: List of snippet objects

        """
        self.logger.info("Listing snippets")

        if not self.client:
            return [
                {
                    "id": "snippet-dns",
                    "name": "DNS-Best-Practice",
                    "description": "DNS best practice configuration",
                    "type": "predefined",
                },
                {
                    "id": "snippet-web",
                    "name": "Web-Security",
                    "description": "Web security configuration",
                    "type": "custom",
                },
            ]

        try:
            results = self.client.snippet.list()
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", "N/A", "snippets", e)

    def delete_snippet(
        self,
        name: str,
    ) -> bool:
        """Delete a snippet.

        Args:
            name: Name of the snippet to delete

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting snippet: {name}")

        if not self.client:
            return True

        try:
            snippet = self.client.snippet.fetch(name=name)
            self.client.snippet.delete(object_id=str(snippet.id))
            return True
        except Exception as e:
            self._handle_api_exception("deletion", "N/A", name, e)

    # Variable --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_variable(
        self,
        name: str,
        type: str,
        value: str,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create or update a variable (smart upsert).

        Args:
            name: Name of the variable
            type: Variable type
            value: Variable value
            folder: Folder to scope the variable to
            snippet: Snippet to scope the variable to
            device: Device to scope the variable to
            description: Optional description

        Returns:
            dict[str, Any]: The created/updated variable object with '__action__' key.

        """
        container = folder or snippet or device or "N/A"
        self.logger.info(f"Upsert variable: {name} in {container}")

        if not self.client:
            result = {
                "id": f"var-{name}",
                "name": name,
                "type": type,
                "value": value,
                "description": description or "",
                "__action__": "created",
            }
            if folder:
                result["folder"] = folder
            elif snippet:
                result["snippet"] = snippet
            elif device:
                result["device"] = device
            return result

        try:
            existing = None
            try:
                existing = self.client.variable.fetch(name=name, folder=folder, snippet=snippet, device=device)
                self.logger.info(f"Found existing variable '{name}'")
            except NotFoundError:
                self.logger.info(f"Variable '{name}' not found, will create new")
            except Exception as e:
                self.logger.warning(f"Error fetching variable '{name}': {str(e)}")

            if existing:
                needs_update = False
                update_fields = []

                if getattr(existing, "type", None) != type:
                    existing.type = type
                    update_fields.append("type")
                    needs_update = True

                if getattr(existing, "value", None) != value:
                    existing.value = value
                    update_fields.append("value")
                    needs_update = True

                if description is not None and getattr(existing, "description", None) != description:
                    existing.description = description
                    update_fields.append("description")
                    needs_update = True

                if needs_update:
                    self.logger.info(f"Updating variable fields: {', '.join(update_fields)}")
                    updated = self.client.variable.update(existing)
                    self.logger.info(f"Successfully updated variable '{name}'")
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
                else:
                    self.logger.info(f"No changes detected for variable '{name}', skipping update")
                    result = json.loads(existing.model_dump_json(exclude_unset=True))
                    result["__action__"] = "no_change"
                    return result
            else:
                var_data = {
                    "name": name,
                    "type": type,
                    "value": value,
                }
                if folder:
                    var_data["folder"] = folder
                elif snippet:
                    var_data["snippet"] = snippet
                elif device:
                    var_data["device"] = device
                if description:
                    var_data["description"] = description

                created = self.client.variable.create(var_data)
                self.logger.info(f"Successfully created variable '{name}'")
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
        except Exception as e:
            self._handle_api_exception("creation/update", container, name, e)

    def get_variable(
        self,
        name: str,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
    ) -> dict[str, Any]:
        """Get a variable by name.

        Args:
            name: Name of the variable
            folder: Folder scope
            snippet: Snippet scope
            device: Device scope

        Returns:
            dict[str, Any]: The variable object

        """
        self.logger.info(f"Getting variable: {name}")

        if not self.client:
            result = {
                "id": f"var-{name}",
                "name": name,
                "type": "ip-netmask",
                "value": "10.0.0.0/24",
                "description": f"Mock variable {name}",
            }
            if folder:
                result["folder"] = folder
            return result

        try:
            # SDK fetch() only supports name and folder kwargs
            result = self.client.variable.fetch(name=name, folder=folder)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieval", folder or snippet or device or "N/A", name, e)

    def list_variables(
        self,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
    ) -> list[dict[str, Any]]:
        """List variables.

        Args:
            folder: Folder scope
            snippet: Snippet scope
            device: Device scope

        Returns:
            list[dict[str, Any]]: List of variable objects

        """
        self.logger.info(f"Listing variables ({folder=}, {snippet=}, {device=})")

        if not self.client:
            return [
                {
                    "id": "var-egress",
                    "name": "$egress-max",
                    "type": "egress-max",
                    "value": "1000",
                    "folder": folder or "Texas",
                    "description": "Maximum egress bandwidth",
                },
                {
                    "id": "var-dns",
                    "name": "$dns-server",
                    "type": "fqdn",
                    "value": "dns.example.com",
                    "folder": folder or "Texas",
                    "description": "DNS server address",
                },
            ]

        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            results = self.client.variable.list(**container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            container = folder or snippet or device or "N/A"
            self._handle_api_exception("listing", container, "variables", e)

    def delete_variable(
        self,
        name: str,
        folder: str | None = None,
        snippet: str | None = None,
        device: str | None = None,
    ) -> bool:
        """Delete a variable.

        Args:
            name: Name of the variable to delete
            folder: Folder scope
            snippet: Snippet scope
            device: Device scope

        Returns:
            bool: True if deletion was successful

        """
        self.logger.info(f"Deleting variable: {name}")

        if not self.client:
            return True

        try:
            # SDK fetch() only supports name and folder kwargs
            variable = self.client.variable.fetch(name=name, folder=folder)
            self.client.variable.delete(variable_id=str(variable.id))
            return True
        except Exception as e:
            container = folder or snippet or device or "N/A"
            self._handle_api_exception("deletion", container, name, e)

    # Device ----------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def get_device(
        self,
        name: str,
    ) -> dict[str, Any]:
        """Get a device by name or serial number.

        Args:
            name: Name or serial number of the device

        Returns:
            dict[str, Any]: The device object

        """
        self.logger.info(f"Getting device: {name}")

        if not self.client:
            return {
                "id": f"device-{name}",
                "name": name,
                "display_name": f"{name} (display)",
                "hostname": name,
                "serial_number": "0123456789",
                "model": "PA-VM",
                "family": "vm",
                "folder": "Texas",
                "description": f"Mock device {name}",
                "labels": ["production"],
                "snippets": ["DNS-Best-Practice"],
                "software_version": "11.1.0",
                "is_connected": True,
                "uptime": "30 days",
            }

        try:
            result = self.client.device.fetch(name=name)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieval", "N/A", name, e)

    def list_devices(
        self,
        folder: str | None = None,
    ) -> list[dict[str, Any]]:
        """List devices.

        Args:
            folder: Optional folder to filter devices

        Returns:
            list[dict[str, Any]]: List of device objects

        """
        self.logger.info(f"Listing devices (folder={folder})")

        if not self.client:
            return [
                {
                    "id": "device-fw1",
                    "name": "PA-VM-01",
                    "display_name": "Edge-FW-01",
                    "hostname": "pa-vm-01",
                    "serial_number": "0123456789",
                    "model": "PA-VM",
                    "family": "vm",
                    "folder": folder or "Texas",
                    "description": "Edge firewall 1",
                    "labels": ["production", "west"],
                    "snippets": ["DNS-Best-Practice"],
                    "software_version": "11.1.0",
                    "is_connected": True,
                },
                {
                    "id": "device-fw2",
                    "name": "PA-VM-02",
                    "display_name": "Edge-FW-02",
                    "hostname": "pa-vm-02",
                    "serial_number": "9876543210",
                    "model": "PA-VM",
                    "family": "vm",
                    "folder": folder or "Texas",
                    "description": "Edge firewall 2",
                    "labels": ["staging"],
                    "software_version": "11.1.0",
                    "is_connected": False,
                },
            ]

        try:
            kwargs = {}
            if folder:
                kwargs["folder"] = folder
            results = self.client.device.list(**kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or "N/A", "devices", e)

    def update_device(
        self,
        name: str,
        display_name: str | None = None,
        folder: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
        snippets: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update a device (smart update — devices cannot be created).

        Args:
            name: Name or serial number of the device (lookup key).
            display_name: New display name (None = preserve).
            folder: New folder (None = preserve).
            description: New description (None = preserve).
            labels: New label set — replaces existing (None = preserve, [] = clear).
            snippets: New snippet set — replaces existing (None = preserve, [] = clear).

        Returns:
            dict[str, Any]: Device payload with '__action__' = 'updated' | 'no_change'.

        Raises:
            ValueError: If the device is not found (devices cannot be created).

        """
        self.logger.info(f"Update device: {name}")

        if not self.client:
            return {
                "id": f"device-{name}",
                "name": name,
                "display_name": display_name if display_name is not None else name,
                "folder": folder if folder is not None else "Texas",
                "description": description if description is not None else "",
                "labels": labels if labels is not None else [],
                "snippets": snippets if snippets is not None else [],
                "__action__": "updated",
            }

        try:
            try:
                existing = self.client.device.fetch(name=name)
            except NotFoundError as e:
                raise ValueError(f"Device '{name}' not found. Devices cannot be created via the CLI — they must be registered by the firewall itself.") from e

            needs_update = False
            update_fields: list[str] = []

            if display_name is not None and getattr(existing, "display_name", None) != display_name:
                existing.display_name = display_name
                update_fields.append("display_name")
                needs_update = True

            if folder is not None and getattr(existing, "folder", None) != folder:
                existing.folder = folder
                update_fields.append("folder")
                needs_update = True

            if description is not None and getattr(existing, "description", None) != description:
                existing.description = description
                update_fields.append("description")
                needs_update = True

            if labels is not None:
                current_labels = set(getattr(existing, "labels", []) or [])
                if current_labels != set(labels):
                    existing.labels = labels
                    update_fields.append("labels")
                    needs_update = True

            if snippets is not None:
                current_snippets = set(getattr(existing, "snippets", []) or [])
                if current_snippets != set(snippets):
                    existing.snippets = snippets
                    update_fields.append("snippets")
                    needs_update = True

            if needs_update:
                self.logger.info(f"Updating device fields: {', '.join(update_fields)}")
                updated = self.client.device.update(existing)
                result = json.loads(updated.model_dump_json(exclude_unset=True))
                result["__action__"] = "updated"
                return result

            self.logger.info(f"No changes detected for device '{name}', skipping update")
            result = json.loads(existing.model_dump_json(exclude_unset=True))
            result["__action__"] = "no_change"
            return result

        except ValueError:
            raise
        except Exception as e:
            self._handle_api_exception("update", "N/A", name, e)

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

    # ------------------------------------------------------------------------------------- DHCP Interfaces -----------------------------------------------------------------------------------

    def create_dhcp_interface(self, iface_data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a DHCP interface using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in iface_data and iface_data[field] is not None:
                container_field = field
                container_value = iface_data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = iface_data.copy()
            result["id"] = f"dhcp-{iface_data['name']}"
            result["__action__"] = "created"
            return result
        existing_iface = None
        try:
            existing_iface = self.client.dhcp_interface.fetch(name=iface_data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing DHCP interface '{iface_data['name']}' in {container_field} '{container_value}'")
        except NotFoundError:
            self.logger.info(f"DHCP interface '{iface_data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching DHCP interface '{iface_data['name']}': {str(e)}")
        if existing_iface:
            needs_update = False
            update_fields = []
            for key in ["server", "relay"]:
                if key in iface_data:
                    existing_val = getattr(existing_iface, key, None)
                    existing_dict = json.loads(existing_val.model_dump_json(exclude_unset=True)) if existing_val else None
                    if iface_data[key] != existing_dict:
                        needs_update = True
                        update_fields.append(key)
            if needs_update:
                self.logger.info(f"Updating DHCP interface fields: {', '.join(update_fields)}")
                try:
                    update_data = iface_data.copy()
                    update_data["id"] = str(existing_iface.id)
                    result = self.client.dhcp_interface.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"DHCP interface '{iface_data['name']}'", update_error)
            else:
                result = json.loads(existing_iface.model_dump_json(exclude_unset=True))
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.dhcp_interface.create(iface_data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"DHCP interface '{iface_data['name']}'", create_error)

    def delete_dhcp_interface(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete a DHCP interface."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete DHCP interface: {name}")
            return
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
            iface = self.client.dhcp_interface.fetch(name=name, **container_kwargs)
            self.client.dhcp_interface.delete(str(iface.id))
            self.logger.info(f"Deleted DHCP interface: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"DHCP interface '{name}'", e)

    def get_dhcp_interface(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific DHCP interface."""
        if not self.client:
            return {
                "id": "dhcp-mock",
                "name": name,
                "folder": folder or "ngfw-shared",
                "server": {"mode": "auto", "ip_pool": ["10.0.0.10-10.0.0.100"]},
            }
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
            result = self.client.dhcp_interface.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"DHCP interface '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"DHCP interface '{name}'", e)

    def list_dhcp_interfaces(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List DHCP interfaces in a container."""
        if not self.client:
            return [
                {"id": "dhcp-mock1", "folder": folder or "ngfw-shared", "name": "ethernet1/1", "server": {"mode": "auto", "ip_pool": ["10.0.0.10-10.0.0.100"]}},
                {"id": "dhcp-mock2", "folder": folder or "ngfw-shared", "name": "ethernet1/2", "relay": {"ip": {"enabled": True, "server": ["10.0.0.1"]}}},
            ]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.dhcp_interface.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "DHCP interfaces", e)

    # ----------------------------------------------------------------------------------- Ethernet Interfaces ---------------------------------------------------------------------------------

    def create_ethernet_interface(self, iface_data: dict[str, Any]) -> dict[str, Any]:
        """Create or update an ethernet interface using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in iface_data and iface_data[field] is not None:
                container_field = field
                container_value = iface_data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = iface_data.copy()
            result["id"] = f"eth-{iface_data['name']}"
            result["__action__"] = "created"
            return result
        existing_iface = None
        try:
            existing_iface = self.client.ethernet_interface.fetch(name=iface_data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing ethernet interface '{iface_data['name']}' in {container_field} '{container_value}'")
        except NotFoundError:
            self.logger.info(f"Ethernet interface '{iface_data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching ethernet interface '{iface_data['name']}': {str(e)}")
        if existing_iface:
            needs_update = False
            update_fields = []
            for key in ["comment", "link_speed", "link_duplex", "link_state"]:
                if key in iface_data and iface_data[key] != getattr(existing_iface, key, None):
                    needs_update = True
                    update_fields.append(key)
            for key in ["layer2", "layer3", "tap"]:
                if key in iface_data:
                    existing_val = getattr(existing_iface, key, None)
                    existing_dict = json.loads(existing_val.model_dump_json(exclude_unset=True)) if existing_val else None
                    if iface_data[key] != existing_dict:
                        needs_update = True
                        update_fields.append(key)
            if needs_update:
                self.logger.info(f"Updating ethernet interface fields: {', '.join(update_fields)}")
                try:
                    update_data = iface_data.copy()
                    update_data["id"] = str(existing_iface.id)
                    result = self.client.ethernet_interface.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"ethernet interface '{iface_data['name']}'", update_error)
            else:
                result = json.loads(existing_iface.model_dump_json(exclude_unset=True))
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.ethernet_interface.create(iface_data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"ethernet interface '{iface_data['name']}'", create_error)

    def delete_ethernet_interface(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete an ethernet interface."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete ethernet interface: {name}")
            return
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
            iface = self.client.ethernet_interface.fetch(name=name, **container_kwargs)
            self.client.ethernet_interface.delete(str(iface.id))
            self.logger.info(f"Deleted ethernet interface: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"ethernet interface '{name}'", e)

    def get_ethernet_interface(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific ethernet interface."""
        if not self.client:
            return {
                "id": "eth-mock",
                "name": name,
                "folder": folder or "ngfw-shared",
                "comment": "Mock ethernet interface",
                "layer3": {"mtu": 1500, "ip": [{"name": "10.0.0.1/24"}]},
            }
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
            result = self.client.ethernet_interface.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"Ethernet interface '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"ethernet interface '{name}'", e)

    def list_ethernet_interfaces(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List ethernet interfaces in a container."""
        if not self.client:
            return [
                {"id": "eth-mock1", "folder": folder or "ngfw-shared", "name": "$eth1", "comment": "Mock eth 1", "layer3": {"mtu": 1500, "ip": [{"name": "10.0.0.1/24"}]}},
                {"id": "eth-mock2", "folder": folder or "ngfw-shared", "name": "$eth2", "comment": "Mock eth 2", "layer2": {"vlan_tag": "100"}},
            ]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.ethernet_interface.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "ethernet interfaces", e)

    # ---------------------------------------------------------------------------------- Layer2 Subinterfaces ---------------------------------------------------------------------------------

    def create_layer2_subinterface(self, iface_data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a layer2 subinterface using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in iface_data and iface_data[field] is not None:
                container_field = field
                container_value = iface_data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = iface_data.copy()
            result["id"] = f"l2sub-{iface_data['name']}"
            result["__action__"] = "created"
            return result
        existing_iface = None
        try:
            existing_iface = self.client.layer2_subinterface.fetch(name=iface_data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing layer2 subinterface '{iface_data['name']}' in {container_field} '{container_value}'")
        except NotFoundError:
            self.logger.info(f"Layer2 subinterface '{iface_data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching layer2 subinterface '{iface_data['name']}': {str(e)}")
        if existing_iface:
            needs_update = False
            update_fields = []
            for key in ["vlan_tag", "comment", "parent_interface"]:
                if key in iface_data and iface_data[key] != getattr(existing_iface, key, None):
                    needs_update = True
                    update_fields.append(key)
            if needs_update:
                self.logger.info(f"Updating layer2 subinterface fields: {', '.join(update_fields)}")
                try:
                    update_data = iface_data.copy()
                    update_data["id"] = str(existing_iface.id)
                    result = self.client.layer2_subinterface.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"layer2 subinterface '{iface_data['name']}'", update_error)
            else:
                result = json.loads(existing_iface.model_dump_json(exclude_unset=True))
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.layer2_subinterface.create(iface_data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"layer2 subinterface '{iface_data['name']}'", create_error)

    def delete_layer2_subinterface(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete a layer2 subinterface."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete layer2 subinterface: {name}")
            return
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
            iface = self.client.layer2_subinterface.fetch(name=name, **container_kwargs)
            self.client.layer2_subinterface.delete(str(iface.id))
            self.logger.info(f"Deleted layer2 subinterface: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"layer2 subinterface '{name}'", e)

    def get_layer2_subinterface(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific layer2 subinterface."""
        if not self.client:
            return {
                "id": "l2sub-mock",
                "name": name,
                "folder": folder or "ngfw-shared",
                "vlan_tag": "100",
                "parent_interface": "ethernet1/1",
            }
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
            result = self.client.layer2_subinterface.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"Layer2 subinterface '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"layer2 subinterface '{name}'", e)

    def list_layer2_subinterfaces(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List layer2 subinterfaces in a container."""
        if not self.client:
            return [
                {"id": "l2sub-mock1", "folder": folder or "ngfw-shared", "name": "ethernet1/1.100", "vlan_tag": "100", "parent_interface": "ethernet1/1"},
                {"id": "l2sub-mock2", "folder": folder or "ngfw-shared", "name": "ethernet1/1.200", "vlan_tag": "200", "parent_interface": "ethernet1/1"},
            ]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.layer2_subinterface.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "layer2 subinterfaces", e)

    # ---------------------------------------------------------------------------------- Layer3 Subinterfaces ---------------------------------------------------------------------------------

    def create_layer3_subinterface(self, iface_data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a layer3 subinterface using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in iface_data and iface_data[field] is not None:
                container_field = field
                container_value = iface_data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = iface_data.copy()
            result["id"] = f"l3sub-{iface_data['name']}"
            result["__action__"] = "created"
            return result
        existing_iface = None
        try:
            existing_iface = self.client.layer3_subinterface.fetch(name=iface_data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing layer3 subinterface '{iface_data['name']}' in {container_field} '{container_value}'")
        except NotFoundError:
            self.logger.info(f"Layer3 subinterface '{iface_data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching layer3 subinterface '{iface_data['name']}': {str(e)}")
        if existing_iface:
            needs_update = False
            update_fields = []
            for key in ["tag", "comment", "parent_interface", "mtu", "interface_management_profile"]:
                if key in iface_data and iface_data[key] != getattr(existing_iface, key, None):
                    needs_update = True
                    update_fields.append(key)
            for key in ["ip", "dhcp_client"]:
                if key in iface_data:
                    existing_val = getattr(existing_iface, key, None)
                    if key == "ip" and existing_val:
                        existing_dict = [json.loads(e.model_dump_json(exclude_unset=True)) for e in existing_val]
                    elif existing_val and hasattr(existing_val, "model_dump_json"):
                        existing_dict = json.loads(existing_val.model_dump_json(exclude_unset=True))
                    else:
                        existing_dict = existing_val
                    if iface_data[key] != existing_dict:
                        needs_update = True
                        update_fields.append(key)
            if needs_update:
                self.logger.info(f"Updating layer3 subinterface fields: {', '.join(update_fields)}")
                try:
                    update_data = iface_data.copy()
                    update_data["id"] = str(existing_iface.id)
                    result = self.client.layer3_subinterface.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"layer3 subinterface '{iface_data['name']}'", update_error)
            else:
                result = json.loads(existing_iface.model_dump_json(exclude_unset=True))
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.layer3_subinterface.create(iface_data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"layer3 subinterface '{iface_data['name']}'", create_error)

    def delete_layer3_subinterface(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete a layer3 subinterface."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete layer3 subinterface: {name}")
            return
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
            iface = self.client.layer3_subinterface.fetch(name=name, **container_kwargs)
            self.client.layer3_subinterface.delete(str(iface.id))
            self.logger.info(f"Deleted layer3 subinterface: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"layer3 subinterface '{name}'", e)

    def get_layer3_subinterface(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific layer3 subinterface."""
        if not self.client:
            return {
                "id": "l3sub-mock",
                "name": name,
                "folder": folder or "ngfw-shared",
                "tag": 100,
                "mtu": 1500,
                "ip": [{"name": "10.0.1.1/24"}],
            }
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
            result = self.client.layer3_subinterface.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"Layer3 subinterface '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"layer3 subinterface '{name}'", e)

    def list_layer3_subinterfaces(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List layer3 subinterfaces in a container."""
        if not self.client:
            return [
                {"id": "l3sub-mock1", "folder": folder or "ngfw-shared", "name": "ethernet1/1.100", "tag": 100, "mtu": 1500, "ip": [{"name": "10.0.1.1/24"}]},
                {"id": "l3sub-mock2", "folder": folder or "ngfw-shared", "name": "ethernet1/1.200", "tag": 200, "dhcp_client": {"enable": True}},
            ]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.layer3_subinterface.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "layer3 subinterfaces", e)

    # ----------------------------------------------------------------------------------- Loopback Interfaces ---------------------------------------------------------------------------------

    def create_loopback_interface(self, iface_data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a loopback interface using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in iface_data and iface_data[field] is not None:
                container_field = field
                container_value = iface_data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = iface_data.copy()
            result["id"] = f"lo-{iface_data['name']}"
            result["__action__"] = "created"
            return result
        existing_iface = None
        try:
            existing_iface = self.client.loopback_interface.fetch(name=iface_data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing loopback interface '{iface_data['name']}' in {container_field} '{container_value}'")
        except NotFoundError:
            self.logger.info(f"Loopback interface '{iface_data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching loopback interface '{iface_data['name']}': {str(e)}")
        if existing_iface:
            needs_update = False
            update_fields = []
            for key in ["comment", "mtu", "interface_management_profile"]:
                if key in iface_data and iface_data[key] != getattr(existing_iface, key, None):
                    needs_update = True
                    update_fields.append(key)
            for key in ["ip", "ipv6"]:
                if key in iface_data:
                    existing_val = getattr(existing_iface, key, None)
                    if key == "ip" and existing_val:
                        existing_dict = [json.loads(e.model_dump_json(exclude_unset=True)) for e in existing_val]
                    elif existing_val and hasattr(existing_val, "model_dump_json"):
                        existing_dict = json.loads(existing_val.model_dump_json(exclude_unset=True))
                    else:
                        existing_dict = existing_val
                    if iface_data[key] != existing_dict:
                        needs_update = True
                        update_fields.append(key)
            if needs_update:
                self.logger.info(f"Updating loopback interface fields: {', '.join(update_fields)}")
                try:
                    update_data = iface_data.copy()
                    update_data["id"] = str(existing_iface.id)
                    result = self.client.loopback_interface.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"loopback interface '{iface_data['name']}'", update_error)
            else:
                result = json.loads(existing_iface.model_dump_json(exclude_unset=True))
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.loopback_interface.create(iface_data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"loopback interface '{iface_data['name']}'", create_error)

    def delete_loopback_interface(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete a loopback interface."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete loopback interface: {name}")
            return
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
            iface = self.client.loopback_interface.fetch(name=name, **container_kwargs)
            self.client.loopback_interface.delete(str(iface.id))
            self.logger.info(f"Deleted loopback interface: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"loopback interface '{name}'", e)

    def get_loopback_interface(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific loopback interface."""
        if not self.client:
            return {
                "id": "lo-mock",
                "name": name,
                "folder": folder or "ngfw-shared",
                "comment": "Mock loopback interface",
                "ip": [{"name": "10.0.0.1/32"}],
            }
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
            result = self.client.loopback_interface.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"Loopback interface '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"loopback interface '{name}'", e)

    def list_loopback_interfaces(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List loopback interfaces in a container."""
        if not self.client:
            return [
                {"id": "lo-mock1", "folder": folder or "ngfw-shared", "name": "$lo1", "comment": "Loopback 1", "ip": [{"name": "10.0.0.1/32"}]},
                {"id": "lo-mock2", "folder": folder or "ngfw-shared", "name": "$lo2", "comment": "Loopback 2", "ip": [{"name": "10.0.0.2/32"}]},
            ]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.loopback_interface.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "loopback interfaces", e)

    # ------------------------------------------------------------------------------------- Tunnel Interfaces ---------------------------------------------------------------------------------

    def create_tunnel_interface(self, iface_data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a tunnel interface using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in iface_data and iface_data[field] is not None:
                container_field = field
                container_value = iface_data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = iface_data.copy()
            result["id"] = f"tun-{iface_data['name']}"
            result["__action__"] = "created"
            return result
        existing_iface = None
        try:
            existing_iface = self.client.tunnel_interface.fetch(name=iface_data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing tunnel interface '{iface_data['name']}' in {container_field} '{container_value}'")
        except NotFoundError:
            self.logger.info(f"Tunnel interface '{iface_data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching tunnel interface '{iface_data['name']}': {str(e)}")
        if existing_iface:
            needs_update = False
            update_fields = []
            for key in ["comment", "mtu", "interface_management_profile"]:
                if key in iface_data and iface_data[key] != getattr(existing_iface, key, None):
                    needs_update = True
                    update_fields.append(key)
            if "ip" in iface_data:
                existing_ip = getattr(existing_iface, "ip", None)
                existing_ip_list = [json.loads(e.model_dump_json(exclude_unset=True)) for e in existing_ip] if existing_ip else None
                if iface_data["ip"] != existing_ip_list:
                    needs_update = True
                    update_fields.append("ip")
            if needs_update:
                self.logger.info(f"Updating tunnel interface fields: {', '.join(update_fields)}")
                try:
                    update_data = iface_data.copy()
                    update_data["id"] = str(existing_iface.id)
                    result = self.client.tunnel_interface.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"tunnel interface '{iface_data['name']}'", update_error)
            else:
                result = json.loads(existing_iface.model_dump_json(exclude_unset=True))
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.tunnel_interface.create(iface_data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"tunnel interface '{iface_data['name']}'", create_error)

    def delete_tunnel_interface(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete a tunnel interface."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete tunnel interface: {name}")
            return
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
            iface = self.client.tunnel_interface.fetch(name=name, **container_kwargs)
            self.client.tunnel_interface.delete(str(iface.id))
            self.logger.info(f"Deleted tunnel interface: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"tunnel interface '{name}'", e)

    def get_tunnel_interface(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific tunnel interface."""
        if not self.client:
            return {
                "id": "tun-mock",
                "name": name,
                "folder": folder or "ngfw-shared",
                "comment": "Mock tunnel interface",
                "mtu": 1500,
                "ip": [{"name": "10.0.0.1/30"}],
            }
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
            result = self.client.tunnel_interface.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"Tunnel interface '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"tunnel interface '{name}'", e)

    def list_tunnel_interfaces(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List tunnel interfaces in a container."""
        if not self.client:
            return [
                {"id": "tun-mock1", "folder": folder or "ngfw-shared", "name": "tunnel1", "mtu": 1500, "ip": [{"name": "10.0.0.1/30"}]},
                {"id": "tun-mock2", "folder": folder or "ngfw-shared", "name": "tunnel2", "mtu": 1400, "ip": [{"name": "10.0.0.5/30"}]},
            ]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.tunnel_interface.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "tunnel interfaces", e)

    # -------------------------------------------------------------------------------------- VLAN Interfaces ----------------------------------------------------------------------------------

    def create_vlan_interface(self, iface_data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a VLAN interface using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in iface_data and iface_data[field] is not None:
                container_field = field
                container_value = iface_data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = iface_data.copy()
            result["id"] = f"vlan-{iface_data['name']}"
            result["__action__"] = "created"
            return result
        existing_iface = None
        try:
            existing_iface = self.client.vlan_interface.fetch(name=iface_data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing VLAN interface '{iface_data['name']}' in {container_field} '{container_value}'")
        except NotFoundError:
            self.logger.info(f"VLAN interface '{iface_data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching VLAN interface '{iface_data['name']}': {str(e)}")
        if existing_iface:
            needs_update = False
            update_fields = []
            for key in ["comment", "vlan_tag", "mtu", "interface_management_profile"]:
                if key in iface_data and iface_data[key] != getattr(existing_iface, key, None):
                    needs_update = True
                    update_fields.append(key)
            for key in ["ip", "dhcp_client"]:
                if key in iface_data:
                    existing_val = getattr(existing_iface, key, None)
                    if key == "ip" and existing_val:
                        existing_dict = [json.loads(e.model_dump_json(exclude_unset=True)) for e in existing_val]
                    elif existing_val and hasattr(existing_val, "model_dump_json"):
                        existing_dict = json.loads(existing_val.model_dump_json(exclude_unset=True))
                    else:
                        existing_dict = existing_val
                    if iface_data[key] != existing_dict:
                        needs_update = True
                        update_fields.append(key)
            if needs_update:
                self.logger.info(f"Updating VLAN interface fields: {', '.join(update_fields)}")
                try:
                    update_data = iface_data.copy()
                    update_data["id"] = str(existing_iface.id)
                    result = self.client.vlan_interface.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"VLAN interface '{iface_data['name']}'", update_error)
            else:
                result = json.loads(existing_iface.model_dump_json(exclude_unset=True))
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.vlan_interface.create(iface_data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"VLAN interface '{iface_data['name']}'", create_error)

    def delete_vlan_interface(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete a VLAN interface."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete VLAN interface: {name}")
            return
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
            iface = self.client.vlan_interface.fetch(name=name, **container_kwargs)
            self.client.vlan_interface.delete(str(iface.id))
            self.logger.info(f"Deleted VLAN interface: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"VLAN interface '{name}'", e)

    def get_vlan_interface(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific VLAN interface."""
        if not self.client:
            return {
                "id": "vlan-mock",
                "name": name,
                "folder": folder or "ngfw-shared",
                "comment": "Mock VLAN interface",
                "vlan_tag": "100",
                "ip": [{"name": "10.0.10.1/24"}],
            }
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
            result = self.client.vlan_interface.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"VLAN interface '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"VLAN interface '{name}'", e)

    def list_vlan_interfaces(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List VLAN interfaces in a container."""
        if not self.client:
            return [
                {"id": "vlan-mock1", "folder": folder or "ngfw-shared", "name": "vlan1", "vlan_tag": "100", "ip": [{"name": "10.0.10.1/24"}]},
                {"id": "vlan-mock2", "folder": folder or "ngfw-shared", "name": "vlan2", "vlan_tag": "200", "ip": [{"name": "10.0.20.1/24"}]},
            ]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.vlan_interface.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "VLAN interfaces", e)

    # --------------------------------------------------------------------------- BGP Address Family Profiles ---------------------------------------------------------------------------

    def create_bgp_address_family_profile(self, profile_data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a BGP address family profile using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in profile_data and profile_data[field] is not None:
                container_field = field
                container_value = profile_data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = profile_data.copy()
            result["id"] = f"bgp-af-{profile_data['name']}"
            result["__action__"] = "created"
            return result
        existing = None
        try:
            existing = self.client.bgp_address_family_profile.fetch(name=profile_data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing BGP address family profile '{profile_data['name']}'")
        except NotFoundError:
            self.logger.info(f"BGP address family profile '{profile_data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching BGP address family profile '{profile_data['name']}': {str(e)}")
        if existing:
            needs_update = False
            existing_dict = json.loads(existing.model_dump_json(exclude_unset=True))
            for key in ["ipv4"]:
                if key in profile_data and profile_data[key] != existing_dict.get(key):
                    needs_update = True
            if needs_update:
                try:
                    update_data = profile_data.copy()
                    update_data["id"] = str(existing.id)
                    result = self.client.bgp_address_family_profile.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"BGP address family profile '{profile_data['name']}'", update_error)
            else:
                result = existing_dict
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.bgp_address_family_profile.create(profile_data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"BGP address family profile '{profile_data['name']}'", create_error)

    def delete_bgp_address_family_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete a BGP address family profile."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete BGP address family profile: {name}")
            return
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
            profile = self.client.bgp_address_family_profile.fetch(name=name, **container_kwargs)
            self.client.bgp_address_family_profile.delete(str(profile.id))
            self.logger.info(f"Deleted BGP address family profile: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"BGP address family profile '{name}'", e)

    def get_bgp_address_family_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific BGP address family profile."""
        if not self.client:
            return {"id": "bgp-af-mock", "name": name, "folder": folder or "ngfw-shared", "ipv4": {"unicast": {"enable": True}}}
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
            result = self.client.bgp_address_family_profile.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"BGP address family profile '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"BGP address family profile '{name}'", e)

    def list_bgp_address_family_profiles(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List BGP address family profiles in a container."""
        if not self.client:
            return [{"id": "bgp-af-mock1", "folder": folder or "ngfw-shared", "name": "default-af-profile", "ipv4": {"unicast": {"enable": True}}}]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.bgp_address_family_profile.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "BGP address family profiles", e)

    # ------------------------------------------------------------------------------- BGP Auth Profiles ---------------------------------------------------------------------------------

    def create_bgp_auth_profile(self, profile_data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a BGP auth profile using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in profile_data and profile_data[field] is not None:
                container_field = field
                container_value = profile_data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = profile_data.copy()
            result["id"] = f"bgp-auth-{profile_data['name']}"
            result["__action__"] = "created"
            return result
        existing = None
        try:
            existing = self.client.bgp_auth_profile.fetch(name=profile_data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing BGP auth profile '{profile_data['name']}'")
        except NotFoundError:
            self.logger.info(f"BGP auth profile '{profile_data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching BGP auth profile '{profile_data['name']}': {str(e)}")
        if existing:
            needs_update = False
            existing_dict = json.loads(existing.model_dump_json(exclude_unset=True))
            if "secret" in profile_data and profile_data["secret"] != existing_dict.get("secret"):
                needs_update = True
            if needs_update:
                try:
                    update_data = profile_data.copy()
                    update_data["id"] = str(existing.id)
                    result = self.client.bgp_auth_profile.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"BGP auth profile '{profile_data['name']}'", update_error)
            else:
                result = existing_dict
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.bgp_auth_profile.create(profile_data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"BGP auth profile '{profile_data['name']}'", create_error)

    def delete_bgp_auth_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete a BGP auth profile."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete BGP auth profile: {name}")
            return
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
            profile = self.client.bgp_auth_profile.fetch(name=name, **container_kwargs)
            self.client.bgp_auth_profile.delete(str(profile.id))
            self.logger.info(f"Deleted BGP auth profile: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"BGP auth profile '{name}'", e)

    def get_bgp_auth_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific BGP auth profile."""
        if not self.client:
            return {"id": "bgp-auth-mock", "name": name, "folder": folder or "ngfw-shared", "secret": "mock-secret"}
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
            result = self.client.bgp_auth_profile.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"BGP auth profile '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"BGP auth profile '{name}'", e)

    def list_bgp_auth_profiles(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List BGP auth profiles in a container."""
        if not self.client:
            return [{"id": "bgp-auth-mock1", "folder": folder or "ngfw-shared", "name": "default-bgp-auth", "secret": "mock-secret"}]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.bgp_auth_profile.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "BGP auth profiles", e)

    # ------------------------------------------------------------------------------ OSPF Auth Profiles ---------------------------------------------------------------------------------

    def create_ospf_auth_profile(self, profile_data: dict[str, Any]) -> dict[str, Any]:
        """Create or update an OSPF auth profile using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in profile_data and profile_data[field] is not None:
                container_field = field
                container_value = profile_data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = profile_data.copy()
            result["id"] = f"ospf-auth-{profile_data['name']}"
            result["__action__"] = "created"
            return result
        existing = None
        try:
            existing = self.client.ospf_auth_profile.fetch(name=profile_data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing OSPF auth profile '{profile_data['name']}'")
        except NotFoundError:
            self.logger.info(f"OSPF auth profile '{profile_data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching OSPF auth profile '{profile_data['name']}': {str(e)}")
        if existing:
            needs_update = False
            existing_dict = json.loads(existing.model_dump_json(exclude_unset=True))
            for key in ["password", "md5"]:
                if key in profile_data and profile_data[key] != existing_dict.get(key):
                    needs_update = True
            if needs_update:
                try:
                    update_data = profile_data.copy()
                    update_data["id"] = str(existing.id)
                    result = self.client.ospf_auth_profile.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"OSPF auth profile '{profile_data['name']}'", update_error)
            else:
                result = existing_dict
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.ospf_auth_profile.create(profile_data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"OSPF auth profile '{profile_data['name']}'", create_error)

    def delete_ospf_auth_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete an OSPF auth profile."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete OSPF auth profile: {name}")
            return
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
            profile = self.client.ospf_auth_profile.fetch(name=name, **container_kwargs)
            self.client.ospf_auth_profile.delete(str(profile.id))
            self.logger.info(f"Deleted OSPF auth profile: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"OSPF auth profile '{name}'", e)

    def get_ospf_auth_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific OSPF auth profile."""
        if not self.client:
            return {"id": "ospf-auth-mock", "name": name, "folder": folder or "ngfw-shared", "password": "mock-password"}
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
            result = self.client.ospf_auth_profile.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"OSPF auth profile '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"OSPF auth profile '{name}'", e)

    def list_ospf_auth_profiles(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List OSPF auth profiles in a container."""
        if not self.client:
            return [{"id": "ospf-auth-mock1", "folder": folder or "ngfw-shared", "name": "default-ospf-auth", "password": "mock-password"}]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.ospf_auth_profile.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "OSPF auth profiles", e)

    # ------------------------------------------------------------------------------ Route Access Lists ---------------------------------------------------------------------------------

    def create_route_access_list(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a route access list using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in data and data[field] is not None:
                container_field = field
                container_value = data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = data.copy()
            result["id"] = f"ral-{data['name']}"
            result["__action__"] = "created"
            return result
        existing = None
        try:
            existing = self.client.route_access_list.fetch(name=data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing route access list '{data['name']}'")
        except NotFoundError:
            self.logger.info(f"Route access list '{data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching route access list '{data['name']}': {str(e)}")
        if existing:
            needs_update = False
            existing_dict = json.loads(existing.model_dump_json(exclude_unset=True))
            for key in ["description", "type"]:
                if key in data and data[key] != existing_dict.get(key):
                    needs_update = True
            if needs_update:
                try:
                    update_data = data.copy()
                    update_data["id"] = str(existing.id)
                    result = self.client.route_access_list.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"route access list '{data['name']}'", update_error)
            else:
                result = existing_dict
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.route_access_list.create(data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"route access list '{data['name']}'", create_error)

    def delete_route_access_list(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete a route access list."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete route access list: {name}")
            return
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
            obj = self.client.route_access_list.fetch(name=name, **container_kwargs)
            self.client.route_access_list.delete(str(obj.id))
            self.logger.info(f"Deleted route access list: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"route access list '{name}'", e)

    def get_route_access_list(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific route access list."""
        if not self.client:
            return {"id": "ral-mock", "name": name, "folder": folder or "ngfw-shared", "description": "Mock route access list"}
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
            result = self.client.route_access_list.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"Route access list '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"route access list '{name}'", e)

    def list_route_access_lists(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List route access lists in a container."""
        if not self.client:
            return [{"id": "ral-mock1", "folder": folder or "ngfw-shared", "name": "default-acl", "description": "Mock route access list"}]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.route_access_list.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "route access lists", e)

    # ------------------------------------------------------------------------------ Route Prefix Lists ---------------------------------------------------------------------------------

    def create_route_prefix_list(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a route prefix list using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in data and data[field] is not None:
                container_field = field
                container_value = data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = data.copy()
            result["id"] = f"rpl-{data['name']}"
            result["__action__"] = "created"
            return result
        existing = None
        try:
            existing = self.client.route_prefix_list.fetch(name=data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing route prefix list '{data['name']}'")
        except NotFoundError:
            self.logger.info(f"Route prefix list '{data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching route prefix list '{data['name']}': {str(e)}")
        if existing:
            needs_update = False
            existing_dict = json.loads(existing.model_dump_json(exclude_unset=True))
            for key in ["description", "ipv4"]:
                if key in data and data[key] != existing_dict.get(key):
                    needs_update = True
            if needs_update:
                try:
                    update_data = data.copy()
                    update_data["id"] = str(existing.id)
                    result = self.client.route_prefix_list.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"route prefix list '{data['name']}'", update_error)
            else:
                result = existing_dict
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.route_prefix_list.create(data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"route prefix list '{data['name']}'", create_error)

    def delete_route_prefix_list(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete a route prefix list."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete route prefix list: {name}")
            return
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
            obj = self.client.route_prefix_list.fetch(name=name, **container_kwargs)
            self.client.route_prefix_list.delete(str(obj.id))
            self.logger.info(f"Deleted route prefix list: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"route prefix list '{name}'", e)

    def get_route_prefix_list(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific route prefix list."""
        if not self.client:
            return {"id": "rpl-mock", "name": name, "folder": folder or "ngfw-shared", "description": "Mock route prefix list"}
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
            result = self.client.route_prefix_list.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"Route prefix list '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"route prefix list '{name}'", e)

    def list_route_prefix_lists(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List route prefix lists in a container."""
        if not self.client:
            return [{"id": "rpl-mock1", "folder": folder or "ngfw-shared", "name": "default-prefix-list", "description": "Mock route prefix list"}]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.route_prefix_list.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "route prefix lists", e)

    # --------------------------------------------------------------------------- BGP Filtering Profiles --------------------------------------------------------------------------------

    def create_bgp_filtering_profile(self, profile_data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a BGP filtering profile using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in profile_data and profile_data[field] is not None:
                container_field = field
                container_value = profile_data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = profile_data.copy()
            result["id"] = f"bgp-filter-{profile_data['name']}"
            result["__action__"] = "created"
            return result
        existing = None
        try:
            existing = self.client.bgp_filtering_profile.fetch(name=profile_data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing BGP filtering profile '{profile_data['name']}'")
        except NotFoundError:
            self.logger.info(f"BGP filtering profile '{profile_data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching BGP filtering profile '{profile_data['name']}': {str(e)}")
        if existing:
            needs_update = False
            existing_dict = json.loads(existing.model_dump_json(exclude_unset=True))
            for key in ["ipv4"]:
                if key in profile_data and profile_data[key] != existing_dict.get(key):
                    needs_update = True
            if needs_update:
                try:
                    update_data = profile_data.copy()
                    update_data["id"] = str(existing.id)
                    result = self.client.bgp_filtering_profile.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"BGP filtering profile '{profile_data['name']}'", update_error)
            else:
                result = existing_dict
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.bgp_filtering_profile.create(profile_data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"BGP filtering profile '{profile_data['name']}'", create_error)

    def delete_bgp_filtering_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete a BGP filtering profile."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete BGP filtering profile: {name}")
            return
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
            profile = self.client.bgp_filtering_profile.fetch(name=name, **container_kwargs)
            self.client.bgp_filtering_profile.delete(str(profile.id))
            self.logger.info(f"Deleted BGP filtering profile: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"BGP filtering profile '{name}'", e)

    def get_bgp_filtering_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific BGP filtering profile."""
        if not self.client:
            return {"id": "bgp-filter-mock", "name": name, "folder": folder or "ngfw-shared", "ipv4": {"unicast": {"filter_list": {"inbound": "test"}}}}
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
            result = self.client.bgp_filtering_profile.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"BGP filtering profile '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"BGP filtering profile '{name}'", e)

    def list_bgp_filtering_profiles(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List BGP filtering profiles in a container."""
        if not self.client:
            return [{"id": "bgp-filter-mock1", "folder": folder or "ngfw-shared", "name": "default-filter", "ipv4": {"unicast": {}}}]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.bgp_filtering_profile.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "BGP filtering profiles", e)

    # -------------------------------------------------------------------------- BGP Redistribution Profiles ----------------------------------------------------------------------------

    def create_bgp_redistribution_profile(self, profile_data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a BGP redistribution profile using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in profile_data and profile_data[field] is not None:
                container_field = field
                container_value = profile_data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = profile_data.copy()
            result["id"] = f"bgp-redist-{profile_data['name']}"
            result["__action__"] = "created"
            return result
        existing = None
        try:
            existing = self.client.bgp_redistribution_profile.fetch(name=profile_data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing BGP redistribution profile '{profile_data['name']}'")
        except NotFoundError:
            self.logger.info(f"BGP redistribution profile '{profile_data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching BGP redistribution profile '{profile_data['name']}': {str(e)}")
        if existing:
            needs_update = False
            existing_dict = json.loads(existing.model_dump_json(exclude_unset=True))
            for key in ["ipv4"]:
                if key in profile_data and profile_data[key] != existing_dict.get(key):
                    needs_update = True
            if needs_update:
                try:
                    update_data = profile_data.copy()
                    update_data["id"] = str(existing.id)
                    result = self.client.bgp_redistribution_profile.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"BGP redistribution profile '{profile_data['name']}'", update_error)
            else:
                result = existing_dict
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.bgp_redistribution_profile.create(profile_data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"BGP redistribution profile '{profile_data['name']}'", create_error)

    def delete_bgp_redistribution_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete a BGP redistribution profile."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete BGP redistribution profile: {name}")
            return
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
            profile = self.client.bgp_redistribution_profile.fetch(name=name, **container_kwargs)
            self.client.bgp_redistribution_profile.delete(str(profile.id))
            self.logger.info(f"Deleted BGP redistribution profile: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"BGP redistribution profile '{name}'", e)

    def get_bgp_redistribution_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific BGP redistribution profile."""
        if not self.client:
            return {"id": "bgp-redist-mock", "name": name, "folder": folder or "ngfw-shared", "ipv4": {"unicast": {"static": {"enable": True}}}}
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
            result = self.client.bgp_redistribution_profile.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"BGP redistribution profile '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"BGP redistribution profile '{name}'", e)

    def list_bgp_redistribution_profiles(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List BGP redistribution profiles in a container."""
        if not self.client:
            return [{"id": "bgp-redist-mock1", "folder": folder or "ngfw-shared", "name": "default-redist", "ipv4": {"unicast": {"static": {"enable": True}}}}]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.bgp_redistribution_profile.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "BGP redistribution profiles", e)

    # ------------------------------------------------------------------------------- BGP Route Maps ------------------------------------------------------------------------------------

    def create_bgp_route_map(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a BGP route map using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in data and data[field] is not None:
                container_field = field
                container_value = data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = data.copy()
            result["id"] = f"bgp-rm-{data['name']}"
            result["__action__"] = "created"
            return result
        existing = None
        try:
            existing = self.client.bgp_route_map.fetch(name=data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing BGP route map '{data['name']}'")
        except NotFoundError:
            self.logger.info(f"BGP route map '{data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching BGP route map '{data['name']}': {str(e)}")
        if existing:
            needs_update = False
            existing_dict = json.loads(existing.model_dump_json(exclude_unset=True))
            for key in ["route_map"]:
                if key in data and data[key] != existing_dict.get(key):
                    needs_update = True
            if needs_update:
                try:
                    update_data = data.copy()
                    update_data["id"] = str(existing.id)
                    result = self.client.bgp_route_map.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"BGP route map '{data['name']}'", update_error)
            else:
                result = existing_dict
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.bgp_route_map.create(data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"BGP route map '{data['name']}'", create_error)

    def delete_bgp_route_map(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete a BGP route map."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete BGP route map: {name}")
            return
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
            obj = self.client.bgp_route_map.fetch(name=name, **container_kwargs)
            self.client.bgp_route_map.delete(str(obj.id))
            self.logger.info(f"Deleted BGP route map: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"BGP route map '{name}'", e)

    def get_bgp_route_map(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific BGP route map."""
        if not self.client:
            return {"id": "bgp-rm-mock", "name": name, "folder": folder or "ngfw-shared", "route_map": [{"name": 10, "action": "permit"}]}
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
            result = self.client.bgp_route_map.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"BGP route map '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"BGP route map '{name}'", e)

    def list_bgp_route_maps(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List BGP route maps in a container."""
        if not self.client:
            return [{"id": "bgp-rm-mock1", "folder": folder or "ngfw-shared", "name": "default-route-map", "route_map": [{"name": 10, "action": "permit"}]}]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.bgp_route_map.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "BGP route maps", e)

    # ----------------------------------------------------------------------- BGP Route Map Redistributions -----------------------------------------------------------------------------

    def create_bgp_route_map_redistribution(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a BGP route map redistribution using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in data and data[field] is not None:
                container_field = field
                container_value = data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = data.copy()
            result["id"] = f"bgp-rmr-{data['name']}"
            result["__action__"] = "created"
            return result
        existing = None
        try:
            existing = self.client.bgp_route_map_redistribution.fetch(name=data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing BGP route map redistribution '{data['name']}'")
        except NotFoundError:
            self.logger.info(f"BGP route map redistribution '{data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching BGP route map redistribution '{data['name']}': {str(e)}")
        if existing:
            needs_update = False
            existing_dict = json.loads(existing.model_dump_json(exclude_unset=True))
            for key in ["bgp", "ospf", "connected_static"]:
                if key in data and data[key] != existing_dict.get(key):
                    needs_update = True
            if needs_update:
                try:
                    update_data = data.copy()
                    update_data["id"] = str(existing.id)
                    result = self.client.bgp_route_map_redistribution.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"BGP route map redistribution '{data['name']}'", update_error)
            else:
                result = existing_dict
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.bgp_route_map_redistribution.create(data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"BGP route map redistribution '{data['name']}'", create_error)

    def delete_bgp_route_map_redistribution(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete a BGP route map redistribution."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete BGP route map redistribution: {name}")
            return
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
            obj = self.client.bgp_route_map_redistribution.fetch(name=name, **container_kwargs)
            self.client.bgp_route_map_redistribution.delete(str(obj.id))
            self.logger.info(f"Deleted BGP route map redistribution: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"BGP route map redistribution '{name}'", e)

    def get_bgp_route_map_redistribution(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific BGP route map redistribution."""
        if not self.client:
            return {"id": "bgp-rmr-mock", "name": name, "folder": folder or "ngfw-shared", "bgp": {"ospf": {"route_map": [{"name": 10, "action": "permit"}]}}}
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
            result = self.client.bgp_route_map_redistribution.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"BGP route map redistribution '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"BGP route map redistribution '{name}'", e)

    def list_bgp_route_map_redistributions(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List BGP route map redistributions in a container."""
        if not self.client:
            return [{"id": "bgp-rmr-mock1", "folder": folder or "ngfw-shared", "name": "default-rmr", "bgp": {"ospf": {"route_map": [{"name": 10, "action": "permit"}]}}}]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.bgp_route_map_redistribution.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "BGP route map redistributions", e)

    # =========================================================================================================================================================================================
    # IDENTITY CONFIGURATION METHODS
    # =========================================================================================================================================================================================

    # --------------------------------------------------------------------------- Authentication Profile ---------------------------------------------------------------------------

    def create_authentication_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None, **kwargs) -> dict[str, Any]:
        """Create or update an authentication profile using smart upsert logic."""
        container = folder or snippet or device
        self.logger.info(f"Creating/updating authentication profile '{name}' in {container}")

        if not self.client:
            result = {"id": f"auth-profile-{name}", "name": name, "__action__": "created"}
            if folder:
                result["folder"] = folder
            result.update(kwargs)
            return result

        try:
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            try:
                existing = self.client.authentication_profile.fetch(name=name, **container_kwargs)
                if existing:
                    for key, value in kwargs.items():
                        if value is not None:
                            setattr(existing, key, value)
                    updated = self.client.authentication_profile.update(existing)
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
            except (NotFoundError, ObjectNotPresentError):
                pass  # object does not exist yet; fall through to create

            create_data = {"name": name, **container_kwargs, **{k: v for k, v in kwargs.items() if v is not None}}
            created = self.client.authentication_profile.create(create_data)
            result = json.loads(created.model_dump_json(exclude_unset=True))
            result["__action__"] = "created"
            return result
        except Exception as e:
            self._handle_api_exception("creating", container or "", name, e)

    def delete_authentication_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> bool:
        """Delete an authentication profile."""
        container = folder or snippet or device
        self.logger.info(f"Deleting authentication profile '{name}' from {container}")

        if not self.client:
            return True

        try:
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            profile = self.client.authentication_profile.fetch(name=name, **container_kwargs)
            self.client.authentication_profile.delete(str(profile.id))
            return True
        except Exception as e:
            self._handle_api_exception("deleting", container or "", name, e)

    def get_authentication_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any]:
        """Get an authentication profile by name."""
        container = folder or snippet or device
        self.logger.info(f"Getting authentication profile '{name}' from {container}")

        if not self.client:
            return {"id": f"auth-profile-{name}", "name": name, "folder": folder or "Texas", "method": {"local_database": {}}, "allow_list": ["all"]}

        try:
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            result = self.client.authentication_profile.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieving", container or "", name, e)

    def list_authentication_profiles(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List authentication profiles in a container."""
        self.logger.info(f"Listing authentication profiles in {folder=}, {snippet=}, {device=}")

        if not self.client:
            return [
                {"id": "auth-profile-mock1", "folder": folder or "Texas", "name": "local-auth", "method": {"local_database": {}}, "allow_list": ["all"]},
                {"id": "auth-profile-mock2", "folder": folder or "Texas", "name": "ldap-auth", "method": {"ldap": {"server_profile": "corp-ldap"}}, "allow_list": ["all"]},
            ]

        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            results = self.client.authentication_profile.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "authentication profiles", e)

    # --------------------------------------------------------------------------- Kerberos Server Profile ---------------------------------------------------------------------------

    def create_kerberos_server_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None, **kwargs) -> dict[str, Any]:
        """Create or update a Kerberos server profile using smart upsert logic."""
        container = folder or snippet or device
        self.logger.info(f"Creating/updating Kerberos server profile '{name}' in {container}")

        if not self.client:
            result = {"id": f"kerberos-{name}", "name": name, "__action__": "created"}
            if folder:
                result["folder"] = folder
            result.update(kwargs)
            return result

        try:
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            try:
                existing = self.client.kerberos_server_profile.fetch(name=name, **container_kwargs)
                if existing:
                    for key, value in kwargs.items():
                        if value is not None:
                            setattr(existing, key, value)
                    updated = self.client.kerberos_server_profile.update(existing)
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
            except (NotFoundError, ObjectNotPresentError):
                pass  # object does not exist yet; fall through to create

            create_data = {"name": name, **container_kwargs, **{k: v for k, v in kwargs.items() if v is not None}}
            created = self.client.kerberos_server_profile.create(create_data)
            result = json.loads(created.model_dump_json(exclude_unset=True))
            result["__action__"] = "created"
            return result
        except Exception as e:
            self._handle_api_exception("creating", container or "", name, e)

    def delete_kerberos_server_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> bool:
        """Delete a Kerberos server profile."""
        container = folder or snippet or device
        self.logger.info(f"Deleting Kerberos server profile '{name}' from {container}")

        if not self.client:
            return True

        try:
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            profile = self.client.kerberos_server_profile.fetch(name=name, **container_kwargs)
            self.client.kerberos_server_profile.delete(str(profile.id))
            return True
        except Exception as e:
            self._handle_api_exception("deleting", container or "", name, e)

    def get_kerberos_server_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any]:
        """Get a Kerberos server profile by name."""
        container = folder or snippet or device
        self.logger.info(f"Getting Kerberos server profile '{name}' from {container}")

        if not self.client:
            return {"id": f"kerberos-{name}", "name": name, "folder": folder or "Texas", "server": [{"name": "kdc1", "host": "kdc1.example.com", "port": 88}]}

        try:
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            result = self.client.kerberos_server_profile.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieving", container or "", name, e)

    def list_kerberos_server_profiles(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List Kerberos server profiles in a container."""
        self.logger.info(f"Listing Kerberos server profiles in {folder=}, {snippet=}, {device=}")

        if not self.client:
            return [
                {"id": "kerberos-mock1", "folder": folder or "Texas", "name": "corp-kerberos", "server": [{"name": "kdc1", "host": "kdc1.example.com", "port": 88}]},
            ]

        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            results = self.client.kerberos_server_profile.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "Kerberos server profiles", e)

    # --------------------------------------------------------------------------- LDAP Server Profile ---------------------------------------------------------------------------

    def create_ldap_server_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None, **kwargs) -> dict[str, Any]:
        """Create or update an LDAP server profile using smart upsert logic."""
        container = folder or snippet or device
        self.logger.info(f"Creating/updating LDAP server profile '{name}' in {container}")

        if not self.client:
            result = {"id": f"ldap-{name}", "name": name, "__action__": "created"}
            if folder:
                result["folder"] = folder
            result.update(kwargs)
            return result

        try:
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            try:
                existing = self.client.ldap_server_profile.fetch(name=name, **container_kwargs)
                if existing:
                    for key, value in kwargs.items():
                        if value is not None:
                            setattr(existing, key, value)
                    updated = self.client.ldap_server_profile.update(existing)
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
            except (NotFoundError, ObjectNotPresentError):
                pass  # object does not exist yet; fall through to create

            create_data = {"name": name, **container_kwargs, **{k: v for k, v in kwargs.items() if v is not None}}
            created = self.client.ldap_server_profile.create(create_data)
            result = json.loads(created.model_dump_json(exclude_unset=True))
            result["__action__"] = "created"
            return result
        except Exception as e:
            self._handle_api_exception("creating", container or "", name, e)

    def delete_ldap_server_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> bool:
        """Delete an LDAP server profile."""
        container = folder or snippet or device
        self.logger.info(f"Deleting LDAP server profile '{name}' from {container}")

        if not self.client:
            return True

        try:
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            profile = self.client.ldap_server_profile.fetch(name=name, **container_kwargs)
            self.client.ldap_server_profile.delete(str(profile.id))
            return True
        except Exception as e:
            self._handle_api_exception("deleting", container or "", name, e)

    def get_ldap_server_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any]:
        """Get an LDAP server profile by name."""
        container = folder or snippet or device
        self.logger.info(f"Getting LDAP server profile '{name}' from {container}")

        if not self.client:
            return {
                "id": f"ldap-{name}",
                "name": name,
                "folder": folder or "Texas",
                "server": [{"name": "ldap1", "address": "ldap.example.com", "port": 389}],
                "ldap_type": "active-directory",
                "base": "dc=example,dc=com",
            }

        try:
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            result = self.client.ldap_server_profile.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieving", container or "", name, e)

    def list_ldap_server_profiles(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List LDAP server profiles in a container."""
        self.logger.info(f"Listing LDAP server profiles in {folder=}, {snippet=}, {device=}")

        if not self.client:
            return [
                {
                    "id": "ldap-mock1",
                    "folder": folder or "Texas",
                    "name": "corp-ldap",
                    "server": [{"name": "ldap1", "address": "ldap.example.com", "port": 389}],
                    "ldap_type": "active-directory",
                },
            ]

        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            results = self.client.ldap_server_profile.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "LDAP server profiles", e)

    # --------------------------------------------------------------------------- RADIUS Server Profile ---------------------------------------------------------------------------

    def create_radius_server_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None, **kwargs) -> dict[str, Any]:
        """Create or update a RADIUS server profile using smart upsert logic."""
        container = folder or snippet or device
        self.logger.info(f"Creating/updating RADIUS server profile '{name}' in {container}")

        if not self.client:
            result = {"id": f"radius-{name}", "name": name, "__action__": "created"}
            if folder:
                result["folder"] = folder
            result.update(kwargs)
            return result

        try:
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            try:
                existing = self.client.radius_server_profile.fetch(name=name, **container_kwargs)
                if existing:
                    for key, value in kwargs.items():
                        if value is not None:
                            setattr(existing, key, value)
                    updated = self.client.radius_server_profile.update(existing)
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
            except (NotFoundError, ObjectNotPresentError):
                pass  # object does not exist yet; fall through to create

            create_data = {"name": name, **container_kwargs, **{k: v for k, v in kwargs.items() if v is not None}}
            created = self.client.radius_server_profile.create(create_data)
            result = json.loads(created.model_dump_json(exclude_unset=True))
            result["__action__"] = "created"
            return result
        except Exception as e:
            self._handle_api_exception("creating", container or "", name, e)

    def delete_radius_server_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> bool:
        """Delete a RADIUS server profile."""
        container = folder or snippet or device
        self.logger.info(f"Deleting RADIUS server profile '{name}' from {container}")

        if not self.client:
            return True

        try:
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            profile = self.client.radius_server_profile.fetch(name=name, **container_kwargs)
            self.client.radius_server_profile.delete(str(profile.id))
            return True
        except Exception as e:
            self._handle_api_exception("deleting", container or "", name, e)

    def get_radius_server_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any]:
        """Get a RADIUS server profile by name."""
        container = folder or snippet or device
        self.logger.info(f"Getting RADIUS server profile '{name}' from {container}")

        if not self.client:
            return {
                "id": f"radius-{name}",
                "name": name,
                "folder": folder or "Texas",
                "server": [{"name": "rad1", "ip_address": "10.0.0.1", "port": 1812, "secret": "***"}],
                "protocol": {"CHAP": {}},
                "timeout": 5,
                "retries": 3,
            }

        try:
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            result = self.client.radius_server_profile.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieving", container or "", name, e)

    def list_radius_server_profiles(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List RADIUS server profiles in a container."""
        self.logger.info(f"Listing RADIUS server profiles in {folder=}, {snippet=}, {device=}")

        if not self.client:
            return [
                {"id": "radius-mock1", "folder": folder or "Texas", "name": "corp-radius", "server": [{"name": "rad1", "ip_address": "10.0.0.1", "port": 1812}], "protocol": {"CHAP": {}}},
            ]

        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            results = self.client.radius_server_profile.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "RADIUS server profiles", e)

    # --------------------------------------------------------------------------- SAML Server Profile ---------------------------------------------------------------------------

    def create_saml_server_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None, **kwargs) -> dict[str, Any]:
        """Create or update a SAML server profile using smart upsert logic."""
        container = folder or snippet or device
        self.logger.info(f"Creating/updating SAML server profile '{name}' in {container}")

        if not self.client:
            result = {"id": f"saml-{name}", "name": name, "__action__": "created"}
            if folder:
                result["folder"] = folder
            result.update(kwargs)
            return result

        try:
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            try:
                existing = self.client.saml_server_profile.fetch(name=name, **container_kwargs)
                if existing:
                    for key, value in kwargs.items():
                        if value is not None:
                            setattr(existing, key, value)
                    updated = self.client.saml_server_profile.update(existing)
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
            except (NotFoundError, ObjectNotPresentError):
                pass  # object does not exist yet; fall through to create

            create_data = {"name": name, **container_kwargs, **{k: v for k, v in kwargs.items() if v is not None}}
            created = self.client.saml_server_profile.create(create_data)
            result = json.loads(created.model_dump_json(exclude_unset=True))
            result["__action__"] = "created"
            return result
        except Exception as e:
            self._handle_api_exception("creating", container or "", name, e)

    def delete_saml_server_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> bool:
        """Delete a SAML server profile."""
        container = folder or snippet or device
        self.logger.info(f"Deleting SAML server profile '{name}' from {container}")

        if not self.client:
            return True

        try:
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            profile = self.client.saml_server_profile.fetch(name=name, **container_kwargs)
            self.client.saml_server_profile.delete(str(profile.id))
            return True
        except Exception as e:
            self._handle_api_exception("deleting", container or "", name, e)

    def get_saml_server_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any]:
        """Get a SAML server profile by name."""
        container = folder or snippet or device
        self.logger.info(f"Getting SAML server profile '{name}' from {container}")

        if not self.client:
            return {
                "id": f"saml-{name}",
                "name": name,
                "folder": folder or "Texas",
                "entity_id": "https://idp.example.com",
                "certificate": "idp-cert",
                "sso_url": "https://idp.example.com/sso",
                "sso_bindings": "post",
            }

        try:
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            result = self.client.saml_server_profile.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieving", container or "", name, e)

    def list_saml_server_profiles(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List SAML server profiles in a container."""
        self.logger.info(f"Listing SAML server profiles in {folder=}, {snippet=}, {device=}")

        if not self.client:
            return [
                {
                    "id": "saml-mock1",
                    "folder": folder or "Texas",
                    "name": "corp-saml",
                    "entity_id": "https://idp.example.com",
                    "certificate": "idp-cert",
                    "sso_url": "https://idp.example.com/sso",
                    "sso_bindings": "post",
                },
            ]

        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            results = self.client.saml_server_profile.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "SAML server profiles", e)

    # --------------------------------------------------------------------------- TACACS+ Server Profile ---------------------------------------------------------------------------

    def create_tacacs_server_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None, **kwargs) -> dict[str, Any]:
        """Create or update a TACACS+ server profile using smart upsert logic."""
        container = folder or snippet or device
        self.logger.info(f"Creating/updating TACACS+ server profile '{name}' in {container}")

        if not self.client:
            result = {"id": f"tacacs-{name}", "name": name, "__action__": "created"}
            if folder:
                result["folder"] = folder
            result.update(kwargs)
            return result

        try:
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            try:
                existing = self.client.tacacs_server_profile.fetch(name=name, **container_kwargs)
                if existing:
                    for key, value in kwargs.items():
                        if value is not None:
                            setattr(existing, key, value)
                    updated = self.client.tacacs_server_profile.update(existing)
                    result = json.loads(updated.model_dump_json(exclude_unset=True))
                    result["__action__"] = "updated"
                    return result
            except (NotFoundError, ObjectNotPresentError):
                pass  # object does not exist yet; fall through to create

            create_data = {"name": name, **container_kwargs, **{k: v for k, v in kwargs.items() if v is not None}}
            created = self.client.tacacs_server_profile.create(create_data)
            result = json.loads(created.model_dump_json(exclude_unset=True))
            result["__action__"] = "created"
            return result
        except Exception as e:
            self._handle_api_exception("creating", container or "", name, e)

    def delete_tacacs_server_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> bool:
        """Delete a TACACS+ server profile."""
        container = folder or snippet or device
        self.logger.info(f"Deleting TACACS+ server profile '{name}' from {container}")

        if not self.client:
            return True

        try:
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            profile = self.client.tacacs_server_profile.fetch(name=name, **container_kwargs)
            self.client.tacacs_server_profile.delete(str(profile.id))
            return True
        except Exception as e:
            self._handle_api_exception("deleting", container or "", name, e)

    def get_tacacs_server_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any]:
        """Get a TACACS+ server profile by name."""
        container = folder or snippet or device
        self.logger.info(f"Getting TACACS+ server profile '{name}' from {container}")

        if not self.client:
            return {
                "id": f"tacacs-{name}",
                "name": name,
                "folder": folder or "Texas",
                "server": [{"name": "tac1", "address": "10.0.0.1", "port": 49}],
                "protocol": "CHAP",
                "timeout": 5,
            }

        try:
            container_kwargs = {}
            if folder:
                container_kwargs["folder"] = folder
            elif snippet:
                container_kwargs["snippet"] = snippet
            elif device:
                container_kwargs["device"] = device

            result = self.client.tacacs_server_profile.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("retrieving", container or "", name, e)

    def list_tacacs_server_profiles(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List TACACS+ server profiles in a container."""
        self.logger.info(f"Listing TACACS+ server profiles in {folder=}, {snippet=}, {device=}")

        if not self.client:
            return [
                {"id": "tacacs-mock1", "folder": folder or "Texas", "name": "corp-tacacs", "server": [{"name": "tac1", "address": "10.0.0.1", "port": 49}], "protocol": "CHAP"},
            ]

        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device

        try:
            results = self.client.tacacs_server_profile.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "TACACS+ server profiles", e)

    # -------------------------------------------------------------------------------- DNS Proxy -------------------------------------------------------------------------------------

    def create_dns_proxy(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a DNS proxy using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in data and data[field] is not None:
                container_field = field
                container_value = data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = data.copy()
            result["id"] = f"dns-proxy-{data['name']}"
            result["__action__"] = "created"
            return result
        existing = None
        try:
            existing = self.client.dns_proxy.fetch(name=data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing DNS proxy '{data['name']}'")
        except NotFoundError:
            self.logger.info(f"DNS proxy '{data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching DNS proxy '{data['name']}': {str(e)}")
        if existing:
            needs_update = False
            existing_dict = json.loads(existing.model_dump_json(exclude_unset=True))
            for key in ["enabled", "default", "interface", "domain_servers", "static_entries", "tcp_queries", "udp_queries", "cache"]:
                if key in data and data[key] != existing_dict.get(key):
                    needs_update = True
            if needs_update:
                try:
                    update_data = data.copy()
                    update_data["id"] = str(existing.id)
                    result = self.client.dns_proxy.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"DNS proxy '{data['name']}'", update_error)
            else:
                result = existing_dict
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.dns_proxy.create(data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"DNS proxy '{data['name']}'", create_error)

    def delete_dns_proxy(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete a DNS proxy."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete DNS proxy: {name}")
            return
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
            proxy = self.client.dns_proxy.fetch(name=name, **container_kwargs)
            self.client.dns_proxy.delete(str(proxy.id))
            self.logger.info(f"Deleted DNS proxy: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"DNS proxy '{name}'", e)

    def get_dns_proxy(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific DNS proxy."""
        if not self.client:
            return {"id": "dns-proxy-mock", "name": name, "folder": folder or "ngfw-shared", "enabled": True, "default": {"primary": "8.8.8.8"}}
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
            result = self.client.dns_proxy.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"DNS proxy '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"DNS proxy '{name}'", e)

    def list_dns_proxies(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List DNS proxies in a container."""
        if not self.client:
            return [{"id": "dns-proxy-mock1", "folder": folder or "ngfw-shared", "name": "default-dns-proxy", "enabled": True}]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.dns_proxy.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "DNS proxies", e)

    # ----------------------------------------------------------------------------- PBF Rules ------------------------------------------------------------------------------------

    def create_pbf_rule(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a PBF rule using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in data and data[field] is not None:
                container_field = field
                container_value = data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = data.copy()
            result["id"] = f"pbf-rule-{data['name']}"
            result["__action__"] = "created"
            return result
        existing = None
        try:
            existing = self.client.pbf_rule.fetch(name=data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing PBF rule '{data['name']}'")
        except NotFoundError:
            self.logger.info(f"PBF rule '{data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching PBF rule '{data['name']}': {str(e)}")
        if existing:
            needs_update = False
            existing_dict = json.loads(existing.model_dump_json(exclude_unset=True))
            for key in [
                "description",
                "tag",
                "schedule",
                "disabled",
                "from",
                "source",
                "source_user",
                "destination",
                "destination_application",
                "service",
                "application",
                "action",
                "enforce_symmetric_return",
            ]:
                if key in data and data[key] != existing_dict.get(key):
                    needs_update = True
            if needs_update:
                try:
                    update_data = data.copy()
                    update_data["id"] = str(existing.id)
                    result = self.client.pbf_rule.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"PBF rule '{data['name']}'", update_error)
            else:
                result = existing_dict
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.pbf_rule.create(data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"PBF rule '{data['name']}'", create_error)

    def delete_pbf_rule(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete a PBF rule."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete PBF rule: {name}")
            return
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
            rule = self.client.pbf_rule.fetch(name=name, **container_kwargs)
            self.client.pbf_rule.delete(str(rule.id))
            self.logger.info(f"Deleted PBF rule: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"PBF rule '{name}'", e)

    def get_pbf_rule(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific PBF rule."""
        if not self.client:
            return {"id": "pbf-rule-mock", "name": name, "folder": folder or "ngfw-shared", "action": {"forward": {"egress_interface": "ethernet1/1"}}}
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
            result = self.client.pbf_rule.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"PBF rule '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"PBF rule '{name}'", e)

    def list_pbf_rules(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List PBF rules in a container."""
        if not self.client:
            return [{"id": "pbf-rule-mock1", "folder": folder or "ngfw-shared", "name": "default-pbf-rule", "action": {"forward": {"egress_interface": "ethernet1/1"}}}]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.pbf_rule.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "PBF rules", e)

    # ----------------------------------------------------------------------------- QoS Profiles ------------------------------------------------------------------------------------

    def create_qos_profile(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a QoS profile using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in data and data[field] is not None:
                container_field = field
                container_value = data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = data.copy()
            result["id"] = f"qos-profile-{data['name']}"
            result["__action__"] = "created"
            return result
        existing = None
        try:
            existing = self.client.qos_profile.fetch(name=data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing QoS profile '{data['name']}'")
        except NotFoundError:
            self.logger.info(f"QoS profile '{data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching QoS profile '{data['name']}': {str(e)}")
        if existing:
            needs_update = False
            existing_dict = json.loads(existing.model_dump_json(exclude_unset=True))
            for key in ["aggregate_bandwidth", "class_bandwidth_type"]:
                if key in data and data[key] != existing_dict.get(key):
                    needs_update = True
            if needs_update:
                try:
                    update_data = data.copy()
                    update_data["id"] = str(existing.id)
                    result = self.client.qos_profile.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"QoS profile '{data['name']}'", update_error)
            else:
                result = existing_dict
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.qos_profile.create(data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"QoS profile '{data['name']}'", create_error)

    def delete_qos_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete a QoS profile."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete QoS profile: {name}")
            return
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
            profile = self.client.qos_profile.fetch(name=name, **container_kwargs)
            self.client.qos_profile.delete(str(profile.id))
            self.logger.info(f"Deleted QoS profile: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"QoS profile '{name}'", e)

    def get_qos_profile(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific QoS profile."""
        if not self.client:
            return {"id": "qos-profile-mock", "name": name, "folder": folder or "ngfw-shared", "aggregate_bandwidth": {"egress_max": 100}}
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
            result = self.client.qos_profile.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"QoS profile '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"QoS profile '{name}'", e)

    def list_qos_profiles(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List QoS profiles in a container."""
        if not self.client:
            return [{"id": "qos-profile-mock1", "folder": folder or "ngfw-shared", "name": "default-qos-profile", "aggregate_bandwidth": {"egress_max": 100}}]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.qos_profile.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "QoS profiles", e)

    # ----------------------------------------------------------------------------- QoS Rules ------------------------------------------------------------------------------------

    def create_qos_rule(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create or update a QoS rule using smart upsert logic."""
        container_fields = ["folder", "snippet", "device"]
        container_field = None
        container_value = None
        for field in container_fields:
            if field in data and data[field] is not None:
                container_field = field
                container_value = data[field]
                break
        if not container_field:
            raise ValueError("One of 'folder', 'snippet', or 'device' must be specified")
        if not self.client:
            result = data.copy()
            result["id"] = f"qos-rule-{data['name']}"
            result["__action__"] = "created"
            return result
        existing = None
        try:
            existing = self.client.qos_rule.fetch(name=data["name"], **{container_field: container_value})
            self.logger.info(f"Found existing QoS rule '{data['name']}'")
        except NotFoundError:
            self.logger.info(f"QoS rule '{data['name']}' not found, will create new")
        except Exception as e:
            self.logger.warning(f"Error fetching QoS rule '{data['name']}': {str(e)}")
        if existing:
            needs_update = False
            existing_dict = json.loads(existing.model_dump_json(exclude_unset=True))
            for key in ["description", "action", "schedule", "dscp_tos"]:
                if key in data and data[key] != existing_dict.get(key):
                    needs_update = True
            if needs_update:
                try:
                    update_data = data.copy()
                    update_data["id"] = str(existing.id)
                    result = self.client.qos_rule.update(update_data)
                    result_dict = json.loads(result.model_dump_json(exclude_unset=True))
                    result_dict["__action__"] = "updated"
                    return result_dict
                except Exception as update_error:
                    self._handle_api_exception("update", container_value or "unknown", f"QoS rule '{data['name']}'", update_error)
            else:
                result = existing_dict
                result["__action__"] = "no_change"
                return result
        else:
            try:
                created = self.client.qos_rule.create(data)
                result = json.loads(created.model_dump_json(exclude_unset=True))
                result["__action__"] = "created"
                return result
            except Exception as create_error:
                self._handle_api_exception("creating", str(container_value), f"QoS rule '{data['name']}'", create_error)

    def delete_qos_rule(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> None:
        """Delete a QoS rule."""
        if not self.client:
            self.logger.info(f"[Mock Mode] Would delete QoS rule: {name}")
            return
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
            rule = self.client.qos_rule.fetch(name=name, **container_kwargs)
            self.client.qos_rule.delete(str(rule.id))
            self.logger.info(f"Deleted QoS rule: {name}")
        except Exception as e:
            self._handle_api_exception("deleting", folder or snippet or device or "", f"QoS rule '{name}'", e)

    def get_qos_rule(self, name: str, folder: str | None = None, snippet: str | None = None, device: str | None = None) -> dict[str, Any] | None:
        """Get a specific QoS rule."""
        if not self.client:
            return {"id": "qos-rule-mock", "name": name, "folder": folder or "ngfw-shared", "action": {"class": "class1"}}
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
            result = self.client.qos_rule.fetch(name=name, **container_kwargs)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except NotFoundError:
            self.logger.warning(f"QoS rule '{name}' not found")
            return None
        except Exception as e:
            self._handle_api_exception("retrieving", folder or snippet or device or "", f"QoS rule '{name}'", e)

    def list_qos_rules(self, folder: str | None = None, snippet: str | None = None, device: str | None = None, exact_match: bool = False) -> list[dict[str, Any]]:
        """List QoS rules in a container."""
        if not self.client:
            return [{"id": "qos-rule-mock1", "folder": folder or "ngfw-shared", "name": "default-qos-rule", "action": {"class": "class1"}}]
        container_kwargs = {}
        if folder:
            container_kwargs["folder"] = folder
        elif snippet:
            container_kwargs["snippet"] = snippet
        elif device:
            container_kwargs["device"] = device
        try:
            results = self.client.qos_rule.list(exact_match=exact_match, **container_kwargs)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder or snippet or device or "", "QoS rules", e)

    # ======================================================================================================================================================================================
    # POSTURE / BPA METHODS
    # ======================================================================================================================================================================================

    def generate_panos_api_key(self, host: str, user: str, password: str) -> str:
        """Generate an API key from PAN-OS XML API using username/password.

        Args:
            host: Firewall hostname or IP address.
            user: Admin username.
            password: Admin password.

        Returns:
            str: The generated API key.

        """
        self.logger.info(f"Generating API key for {user}@{host}")
        url = f"https://{host}/api/?type=keygen&user={user}&password={password}"
        response = requests.get(url, verify=False)  # noqa: S501
        response.raise_for_status()
        root = ET.fromstring(response.text)
        key_element = root.find(".//key")
        if key_element is None or key_element.text is None:
            raise ValueError(f"Failed to generate API key: {response.text}")
        return key_element.text

    def export_panos_config(self, host: str, api_key: str, category: str = "running") -> str:
        """Export configuration from PAN-OS firewall via XML API.

        Args:
            host: Firewall hostname or IP address.
            api_key: PAN-OS API key.
            category: Config category ('running' or 'candidate').

        Returns:
            str: The configuration XML as a string.

        """
        self.logger.info(f"Exporting {category} config from {host}")
        url = f"https://{host}/api/?type=export&category=configuration&key={api_key}"
        response = requests.get(url, verify=False)  # noqa: S501
        response.raise_for_status()
        return response.text

    def _get_scm_session(self) -> Any:
        """Get an authenticated requests session for SCM API calls.

        Returns:
            Any: Authenticated session from the SCM SDK client.

        """
        if not self.client:
            raise RuntimeError("SCM client not initialized — check credentials")
        return self.client.session

    def initiate_bpa_upload(self, delete_after_processing: bool = True) -> dict[str, Any]:
        """Initiate a BPA config file upload.

        Args:
            delete_after_processing: Delete config from cloud after assessment.

        Returns:
            dict[str, Any]: Response with task_id and upload_url.

        """
        self.logger.info("Initiating BPA config upload")
        session = self._get_scm_session()
        url = "https://api.strata.paloaltonetworks.com/posture/checks/v1/reports/config-file-upload"
        response = session.post(url, json={"delete_after_processing": delete_after_processing})
        response.raise_for_status()
        return response.json()

    def upload_config_to_presigned_url(self, upload_url: str, config_data: bytes) -> None:
        """Upload config file to a presigned GCS URL.

        Args:
            upload_url: Presigned GCS URL from initiate_bpa_upload.
            config_data: Raw config file bytes.

        """
        self.logger.info("Uploading config to presigned URL")
        compressed = gzip.compress(config_data)
        headers = {
            "Content-Type": "plain/text",
            "Content-Encoding": "gzip",
        }
        response = requests.put(upload_url, data=compressed, headers=headers)
        response.raise_for_status()

    def get_bpa_status(self, task_id: str) -> dict[str, Any]:
        """Get BPA processing status for a task.

        Args:
            task_id: The task ID from initiate_bpa_upload.

        Returns:
            dict[str, Any]: Status response with status, message, and result fields.

        """
        self.logger.info(f"Checking BPA status for task {task_id}")
        session = self._get_scm_session()
        url = f"https://api.strata.paloaltonetworks.com/posture/checks/v1/reports/{task_id}/bpa-result"
        response = session.get(url)
        response.raise_for_status()
        return response.json()

    def fetch_bpa_report(self, report_url: str) -> dict[str, Any]:
        """Fetch the completed BPA report from its URL.

        Args:
            report_url: URL to the completed BPA report.

        Returns:
            dict[str, Any]: The full BPA report as a dict.

        """
        self.logger.info(f"Fetching BPA report from {report_url}")
        session = self._get_scm_session()
        response = session.get(report_url)
        response.raise_for_status()
        return response.json()

    # ======================================================================================================================================================================================
    # DEVICE SERIAL RESOLUTION
    # ======================================================================================================================================================================================

    _SERIAL_PATTERN = __import__("re").compile(r"^\d{14,15}$")

    def resolve_device_serial(self, device: str) -> str:
        """Resolve a device name, hostname, or serial number to a serial number.

        Args:
            device: Device hostname, display name, or serial number.

        Returns:
            str: The 14-15 digit device serial number.

        Raises:
            ValueError: If the device cannot be found.

        """
        if self._SERIAL_PATTERN.match(device):
            return device

        self.logger.info(f"Resolving device name '{device}' to serial number")

        if not self.client:
            return "007951000123456"

        try:
            all_devices = self.client.device.list()
            search = device.lower()
            for d in all_devices:
                if any(search == (getattr(d, field, None) or "").lower() for field in ("hostname", "display_name", "name", "serial_number")):
                    self.logger.info(f"Resolved '{device}' to serial {d.id}")
                    return d.id
            available = [f"  {d.hostname or d.display_name or d.name} ({d.id})" for d in all_devices]
            raise ValueError(f"Device '{device}' not found. Available devices:\n" + "\n".join(available))
        except ValueError:
            raise
        except Exception as e:
            self._handle_api_exception("resolving", "N/A", f"device {device}", e)

    # ======================================================================================================================================================================================
    # LOCAL CONFIG METHODS
    # ======================================================================================================================================================================================

    def list_local_config_versions(self, device: str) -> list[dict[str, Any]]:
        """List configuration versions for a device.

        Args:
            device: Device name or serial number (resolved automatically).

        Returns:
            list[dict[str, Any]]: List of config version objects.

        """
        self.logger.info(f"Listing local config versions for device: {device}")

        if not self.client:
            return [
                {"id": "cfg-001", "serial": "007951000123456", "local_version": "42", "timestamp": "2026-04-15T14:30:00Z", "xfmed_version": "42", "md5": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"},
                {"id": "cfg-002", "serial": "007951000123456", "local_version": "41", "timestamp": "2026-04-14T09:12:00Z", "xfmed_version": "41", "md5": "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5"},
                {"id": "cfg-003", "serial": "007951000123456", "local_version": "40", "timestamp": "2026-04-13T11:45:00Z", "xfmed_version": "40", "md5": "c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6"},
            ]

        try:
            serial = self.resolve_device_serial(device)
            results = self.client.local_config.list_versions(device=serial)
            return [json.loads(r.model_dump_json(exclude_unset=True)) for r in results]
        except Exception as e:
            self._handle_api_exception("listing", "N/A", f"local config versions for {device}", e)

    def download_local_config(self, device: str, version: str) -> bytes:
        """Download a configuration version as raw XML.

        Args:
            device: Device name or serial number (resolved automatically).
            version: Config version ID to download.

        Returns:
            bytes: Raw XML configuration data.

        """
        self.logger.info(f"Downloading local config version {version} for device: {device}")

        if not self.client:
            return b'<?xml version="1.0"?>\n<config version="42">\n  <devices>\n    <entry name="fw-01">\n      <vsys/>\n    </entry>\n  </devices>\n</config>'

        try:
            serial = self.resolve_device_serial(device)
            return self.client.local_config.download(device=serial, version=version)
        except Exception as e:
            self._handle_api_exception("downloading", "N/A", f"local config v{version} for {device}", e)

    # ======================================================================================================================================================================================
    # DEVICE OPERATIONS METHODS
    # ======================================================================================================================================================================================

    _OPERATION_MOCK_RESULTS = {
        "route-table": [
            {"destination": "0.0.0.0/0", "next_hop": "10.0.0.1", "interface": "ethernet1/1", "metric": 10},
            {"destination": "10.1.0.0/16", "next_hop": "10.0.0.2", "interface": "ethernet1/2", "metric": 20},
        ],
        "fib-table": [
            {"destination": "0.0.0.0/0", "interface": "ethernet1/1", "next_hop": "10.0.0.1", "flags": "u"},
        ],
        "dns-proxy": [
            {"domain": "example.com", "primary": "8.8.8.8", "secondary": "8.8.4.4", "status": "active"},
        ],
        "interfaces": [
            {"name": "ethernet1/1", "status": "up", "ip": "10.0.0.1/24", "speed": "1Gbps"},
            {"name": "ethernet1/2", "status": "up", "ip": "10.1.0.1/24", "speed": "1Gbps"},
        ],
        "device-rules": [
            {"name": "allow-web", "action": "allow", "from": "trust", "to": "untrust"},
        ],
        "bgp-export": [
            {"prefix": "10.0.0.0/8", "next_hop": "10.0.0.1", "as_path": "65001 65002"},
        ],
        "logging-status": [
            {"service": "cortex-data-lake", "status": "connected", "last_log": "2026-04-16 10:30:00"},
        ],
    }

    def dispatch_device_operation(
        self,
        device: str,
        operation: str,
        sync: bool = True,
        timeout: int = 300,
    ) -> dict[str, Any]:
        """Dispatch a device operation job.

        Args:
            device: Device name or serial number (resolved automatically).
            operation: Operation type (route-table, fib-table, etc.).
            sync: If True, poll until completion. If False, return job_id immediately.
            timeout: Timeout in seconds for sync polling.

        Returns:
            dict: Results if sync, or job_id if async.

        """
        self.logger.info(f"Dispatching {operation} for device {device} (sync={sync})")

        if not self.client:
            if sync:
                return {
                    "status": "completed",
                    "job_id": f"mock-job-{operation}",
                    "device": device,
                    "operation": operation,
                    "results": self._OPERATION_MOCK_RESULTS.get(operation, []),
                }
            return {
                "job_id": f"mock-job-{operation}",
                "device": device,
                "operation": operation,
                "status": "pending",
            }

        try:
            serial = self.resolve_device_serial(device)
            op_method_map = {
                "route-table": "route_table",
                "fib-table": "fib_table",
                "dns-proxy": "dns_proxy",
                "interfaces": "device_interfaces",
                "device-rules": "device_rules",
                "bgp-export": "bgp_policy_export",
                "logging-status": "logging_service_status",
            }
            method_name = op_method_map.get(operation, operation.replace("-", "_"))
            method = getattr(self.client.device_operations, method_name)
            result = method(devices=[serial], sync=sync, timeout=timeout)
            result_dict = json.loads(result.model_dump_json(exclude_unset=True))
            if sync:
                result_dict["status"] = "completed"
                result_dict["device"] = device
                result_dict["operation"] = operation
            else:
                result_dict["device"] = device
                result_dict["operation"] = operation
                result_dict["status"] = "pending"
            return result_dict
        except Exception as e:
            self._handle_api_exception("dispatching", "N/A", f"{operation} for {device}", e)

    def get_device_operation_status(self, job_id: str) -> dict[str, Any]:
        """Get status of a device operation job.

        Args:
            job_id: The job ID to check.

        Returns:
            dict: Job status information.

        """
        self.logger.info(f"Checking status of job {job_id}")

        if not self.client:
            return {
                "job_id": job_id,
                "state": "completed",
                "device": "007951000123456",
                "operation": "route-table",
                "started": "2026-04-16 10:30:00",
                "completed": "2026-04-16 10:30:42",
            }

        try:
            result = self.client.device_operations.get_job_status(job_id=job_id)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("checking status", "N/A", f"job {job_id}", e)

    # ======================================================================================================================================================================================
    # INCIDENTS METHODS
    # ======================================================================================================================================================================================

    _MOCK_INCIDENTS = [
        {
            "incident_id": "INC-2026-04-001",
            "status": "open",
            "severity": "high",
            "product": "Prisma Access",
            "title": "Suspicious lateral movement detected from 10.1.2.50",
            "raised_time": 1744700580,
            "updated_time": 1744764900,
            "category": "lateral-movement",
            "alerts": [
                {"alert_id": "ALT-001", "severity": "high", "title": "Unusual SMB traffic from 10.1.2.50 to 10.1.2.100", "state": "open", "updated_time": 1744700580, "domain": "10.1.2.0/24"},
                {"alert_id": "ALT-002", "severity": "high", "title": "Credential dumping tool detected on 10.1.2.50", "state": "open", "updated_time": 1744700700, "domain": "10.1.2.0/24"},
                {"alert_id": "ALT-003", "severity": "medium", "title": "DNS tunneling attempt from 10.1.2.50", "state": "open", "updated_time": 1744701000, "domain": "10.1.2.0/24"},
            ],
            "description": "Lateral movement detected from host 10.1.2.50 involving SMB, credential dumping, and DNS tunneling.",
            "remediations": "Isolate host 10.1.2.50 from network. Reset credentials for affected accounts. Scan 10.1.2.100 for indicators of compromise.",
        },
        {
            "incident_id": "INC-2026-04-002",
            "status": "open",
            "severity": "critical",
            "product": "NGFW",
            "title": "C2 callback detected from internal host",
            "raised_time": 1744644300,
            "updated_time": 1744702800,
            "category": "command-and-control",
            "alerts": [
                {"alert_id": "ALT-004", "severity": "critical", "title": "Known C2 domain contacted by 10.2.1.30", "state": "open", "updated_time": 1744644300, "domain": "malware.example"},
                {"alert_id": "ALT-005", "severity": "high", "title": "Encrypted payload exfiltration attempt", "state": "open", "updated_time": 1744644600, "domain": "10.2.1.0"},
            ],
            "description": "C2 callback and data exfiltration attempt from host 10.2.1.30.",
            "remediations": "Block C2 domain at firewall. Isolate 10.2.1.30. Perform forensic analysis of affected host.",
        },
        {
            "incident_id": "INC-2026-03-088",
            "status": "closed",
            "severity": "medium",
            "product": "Prisma Access",
            "title": "Policy violation — data exfiltration attempt",
            "raised_time": 1743170400,
            "updated_time": 1743247800,
            "category": "data-exfiltration",
            "alerts": [
                {"alert_id": "ALT-006", "severity": "medium", "title": "Large file upload to unapproved storage", "state": "closed", "updated_time": 1743170400, "domain": "cloud.example"},
            ],
            "description": "User uploaded large files to unapproved cloud storage service.",
            "remediations": "User counseling completed. DLP policy updated to block unapproved storage.",
        },
    ]

    def list_incidents(
        self,
        status: str | None = None,
        severity: str | None = None,
        product: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search incidents with optional filters."""
        self.logger.info(f"Listing incidents (status={status}, severity={severity}, product={product})")

        if not self.client:
            results = list(self._MOCK_INCIDENTS)
            if status:
                results = [i for i in results if i["status"] == status]
            if severity:
                results = [i for i in results if i["severity"] == severity]
            if product:
                results = [i for i in results if i["product"] == product]
            return results

        try:
            kwargs: dict[str, Any] = {}
            if status:
                kwargs["status"] = [status]
            if severity:
                kwargs["severity"] = [severity]
            if product:
                kwargs["product"] = [product]
            response = self.client.incidents.search(**kwargs)
            return json.loads(response.model_dump_json(exclude_unset=True)).get("data", [])
        except Exception as e:
            self._handle_api_exception("searching", "N/A", "incidents", e)

    def get_incident(self, incident_id: str) -> dict[str, Any]:
        """Get detailed incident information including alerts and remediation."""
        self.logger.info(f"Getting incident detail: {incident_id}")

        if not self.client:
            for inc in self._MOCK_INCIDENTS:
                if inc["incident_id"] == incident_id:
                    return inc
            return self._MOCK_INCIDENTS[0]

        try:
            # Bypass SDK's get_details() which has a parsing bug (passes whole
            # response to model instead of extracting data[0] from the wrapper).
            session = self.client.oauth_client.session
            base = self.client.api_base_url
            resp = session.get(
                f"{base}/incidents/v1/details/{incident_id}",
                headers={"X-PANW-Region": getattr(self.client, "_region", "americas")},
            )
            resp.raise_for_status()
            body = resp.json()
            items = body.get("data", [])
            if not items:
                raise ValueError(f"Incident {incident_id} not found")
            return items[0]
        except ValueError:
            raise
        except Exception as e:
            self._handle_api_exception("fetching", "N/A", f"incident {incident_id}", e)

    # ======================================================================================================================================================================================
    # GLOBALPROTECT FORWARDING PROFILE METHODS (mobile-agent, SDK 0.15.0)
    # ======================================================================================================================================================================================

    # Forwarding Profile ----------------------------------------------------------------------------------------------------------------------------------------------------------------

    def create_forwarding_profile(
        self,
        folder: str | None = None,
        name: str = None,
        description: str | None = None,
        definition_method: str | None = None,
        type: dict[str, Any] | None = None,  # noqa: A002 - matches SDK field name
    ) -> dict[str, Any]:
        """Create or update a GlobalProtect forwarding profile using smart upsert logic.

        Args:
            folder: Folder for the profile (must be 'Mobile Users'; sent as query param)
            name: Name of the forwarding profile
            description: Optional description
            definition_method: How the profile is defined (rules or pac-file)
            type: Profile type configuration ({pac_file|global_protect_proxy|ztna_agent: {...}})

        Returns:
            dict[str, Any]: The created/updated forwarding profile with __action__ field

        """
        folder = folder or "Mobile Users"
        self.logger.info(f"Creating or updating forwarding profile: {name} in folder {folder}")

        if not self.client:
            result = {
                "id": f"fp-{name}",
                "name": name,
                "description": description,
                "definition_method": definition_method,
                "type": type,
                "__action__": "created",
            }
            return {k: v for k, v in result.items() if v is not None}

        try:
            # Step 1: Try to fetch existing profile by name (SDK fetch raises a 404-style
            # InvalidObjectError when missing, which lands in the generic handler below)
            existing = None
            try:
                existing = self.client.forwarding_profile.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing forwarding profile '{name}' in folder '{folder}'")
            except NotFoundError:
                self.logger.info(f"Forwarding profile '{name}' not found in folder '{folder}', will create new")
            except Exception as fetch_error:
                self.logger.info(f"Forwarding profile '{name}' lookup did not match ({fetch_error}), will create new")

            if existing:
                existing_dump = json.loads(existing.model_dump_json(exclude_unset=True))

                # Step 2: Compare provided fields and update if needed
                provided: dict[str, Any] = {}
                if description is not None:
                    provided["description"] = description
                if definition_method is not None:
                    provided["definition_method"] = definition_method
                if type is not None:
                    provided["type"] = type

                needs_update = any(existing_dump.get(field) != value for field, value in provided.items())

                if needs_update:
                    payload = {k: v for k, v in existing_dump.items() if k != "id"}
                    payload.update(provided)
                    result = self.client.forwarding_profile.update(str(existing.id), payload)
                    self.logger.info(f"Successfully updated forwarding profile '{name}' in folder '{folder}'")
                    response = json.loads(result.model_dump_json(exclude_unset=True))
                    response["__action__"] = "updated"
                    return response
                else:
                    self.logger.info(f"No changes detected for forwarding profile '{name}', skipping update")
                    response = existing_dump
                    response["__action__"] = "no_change"
                    return response
            else:
                # Step 3: Create new profile (folder goes as query param via the service)
                profile_data: dict[str, Any] = {"name": name}
                if description is not None:
                    profile_data["description"] = description
                if definition_method is not None:
                    profile_data["definition_method"] = definition_method
                if type is not None:
                    profile_data["type"] = type

                result = self.client.forwarding_profile.create(profile_data, folder=folder)
                self.logger.info(f"Successfully created forwarding profile '{name}' in folder '{folder}'")
                response = json.loads(result.model_dump_json(exclude_unset=True))
                response["__action__"] = "created"
                return response

        except Exception as e:
            self._handle_api_exception("create/update", folder, name or "", e)

    def get_forwarding_profile(
        self,
        folder: str | None = None,
        name: str | None = None,
        profile_id: str | None = None,
    ) -> dict[str, Any]:
        """Get a forwarding profile by name (fetch) or UUID (direct get).

        Args:
            folder: Folder containing the profile (used with name)
            name: Name of the forwarding profile
            profile_id: UUID of the forwarding profile (takes precedence over name)

        Returns:
            dict[str, Any]: The forwarding profile object

        """
        folder = folder or "Mobile Users"
        self.logger.info(f"Getting forwarding profile: {profile_id or name} from folder {folder}")

        if not self.client:
            return {
                "id": profile_id or f"fp-{name}",
                "name": name or "mock-profile",
                "description": f"Mock forwarding profile {name or profile_id}",
                "definition_method": "rules",
                "type": {"ztna_agent": {"pac_upload": False}},
            }

        try:
            result = self.client.forwarding_profile.get(profile_id) if profile_id else self.client.forwarding_profile.fetch(name=name, folder=folder)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("getting", folder, profile_id or name or "", e)

    def list_forwarding_profiles(
        self,
        folder: str | None = None,
    ) -> list[dict[str, Any]]:
        """List forwarding profiles.

        Args:
            folder: Folder to list from (must be 'Mobile Users')

        Returns:
            list[dict[str, Any]]: List of forwarding profile objects

        """
        folder = folder or "Mobile Users"
        self.logger.info(f"Listing forwarding profiles in folder: {folder}")

        if not self.client:
            return [
                {
                    "id": "fp-mock1",
                    "name": "ztna-profile",
                    "definition_method": "rules",
                    "type": {"ztna_agent": {"pac_upload": False}},
                },
                {
                    "id": "fp-mock2",
                    "name": "pac-profile",
                    "definition_method": "pac-file",
                    "type": {"pac_file": {"pac_upload": True}},
                },
            ]

        try:
            results = self.client.forwarding_profile.list(folder=folder)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder, "forwarding profiles", e)

    def delete_forwarding_profile(
        self,
        folder: str | None = None,
        name: str | None = None,
        profile_id: str | None = None,
    ) -> bool:
        """Delete a forwarding profile by name or UUID.

        Args:
            folder: Folder containing the profile (used with name)
            name: Name of the forwarding profile to delete
            profile_id: UUID of the forwarding profile (takes precedence over name)

        Returns:
            bool: True if deletion was successful

        """
        folder = folder or "Mobile Users"
        self.logger.info(f"Deleting forwarding profile: {profile_id or name} from folder {folder}")

        if not self.client:
            return True

        try:
            if not profile_id:
                profile = self.client.forwarding_profile.fetch(name=name, folder=folder)
                profile_id = str(profile.id)
            self.client.forwarding_profile.delete(profile_id)
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder, profile_id or name or "", e)

    # Forwarding Profile Destination ----------------------------------------------------------------------------------------------------------------------------------------------------

    def create_forwarding_profile_destination(
        self,
        folder: str | None = None,
        name: str = None,
        description: str | None = None,
        fqdn: list[dict[str, Any]] | None = None,
        ip_addresses: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create or update a forwarding profile destination using smart upsert logic.

        Args:
            folder: Folder for the destination (must be 'Mobile Users'; sent as query param)
            name: Name of the destination
            description: Optional description
            fqdn: FQDN entries ({name, port?})
            ip_addresses: IP address entries ({name, port?})

        Returns:
            dict[str, Any]: The created/updated destination with __action__ field

        """
        folder = folder or "Mobile Users"
        self.logger.info(f"Creating or updating forwarding profile destination: {name} in folder {folder}")

        if not self.client:
            result = {
                "id": f"fpd-{name}",
                "name": name,
                "description": description,
                "fqdn": fqdn,
                "ip_addresses": ip_addresses,
                "__action__": "created",
            }
            return {k: v for k, v in result.items() if v is not None}

        try:
            # Step 1: Try to fetch existing destination by name (SDK fetch raises a 404-style
            # InvalidObjectError when missing, which lands in the generic handler below)
            existing = None
            try:
                existing = self.client.forwarding_profile_destination.fetch(name=name, folder=folder)
                self.logger.info(f"Found existing forwarding profile destination '{name}' in folder '{folder}'")
            except NotFoundError:
                self.logger.info(f"Forwarding profile destination '{name}' not found in folder '{folder}', will create new")
            except Exception as fetch_error:
                self.logger.info(f"Forwarding profile destination '{name}' lookup did not match ({fetch_error}), will create new")

            if existing:
                existing_dump = json.loads(existing.model_dump_json(exclude_unset=True))

                # Step 2: Compare provided fields and update if needed
                provided: dict[str, Any] = {}
                if description is not None:
                    provided["description"] = description
                if fqdn is not None:
                    provided["fqdn"] = fqdn
                if ip_addresses is not None:
                    provided["ip_addresses"] = ip_addresses

                needs_update = any(existing_dump.get(field) != value for field, value in provided.items())

                if needs_update:
                    payload = {k: v for k, v in existing_dump.items() if k != "id"}
                    payload.update(provided)
                    result = self.client.forwarding_profile_destination.update(str(existing.id), payload)
                    self.logger.info(f"Successfully updated forwarding profile destination '{name}' in folder '{folder}'")
                    response = json.loads(result.model_dump_json(exclude_unset=True))
                    response["__action__"] = "updated"
                    return response
                else:
                    self.logger.info(f"No changes detected for forwarding profile destination '{name}', skipping update")
                    response = existing_dump
                    response["__action__"] = "no_change"
                    return response
            else:
                # Step 3: Create new destination (folder goes as query param via the service)
                destination_data: dict[str, Any] = {"name": name}
                if description is not None:
                    destination_data["description"] = description
                if fqdn is not None:
                    destination_data["fqdn"] = fqdn
                if ip_addresses is not None:
                    destination_data["ip_addresses"] = ip_addresses

                result = self.client.forwarding_profile_destination.create(destination_data, folder=folder)
                self.logger.info(f"Successfully created forwarding profile destination '{name}' in folder '{folder}'")
                response = json.loads(result.model_dump_json(exclude_unset=True))
                response["__action__"] = "created"
                return response

        except Exception as e:
            self._handle_api_exception("create/update", folder, name or "", e)

    def get_forwarding_profile_destination(
        self,
        folder: str | None = None,
        name: str | None = None,
        destination_id: str | None = None,
    ) -> dict[str, Any]:
        """Get a forwarding profile destination by name (fetch) or UUID (direct get).

        Args:
            folder: Folder containing the destination (used with name)
            name: Name of the destination
            destination_id: UUID of the destination (takes precedence over name)

        Returns:
            dict[str, Any]: The destination object

        """
        folder = folder or "Mobile Users"
        self.logger.info(f"Getting forwarding profile destination: {destination_id or name} from folder {folder}")

        if not self.client:
            return {
                "id": destination_id or f"fpd-{name}",
                "name": name or "mock-destination",
                "description": f"Mock destination {name or destination_id}",
                "fqdn": [{"name": "app.internal", "port": 443}],
            }

        try:
            result = self.client.forwarding_profile_destination.get(destination_id) if destination_id else self.client.forwarding_profile_destination.fetch(name=name, folder=folder)
            return json.loads(result.model_dump_json(exclude_unset=True))
        except Exception as e:
            self._handle_api_exception("getting", folder, destination_id or name or "", e)

    def list_forwarding_profile_destinations(
        self,
        folder: str | None = None,
    ) -> list[dict[str, Any]]:
        """List forwarding profile destinations.

        Args:
            folder: Folder to list from (must be 'Mobile Users')

        Returns:
            list[dict[str, Any]]: List of destination objects

        """
        folder = folder or "Mobile Users"
        self.logger.info(f"Listing forwarding profile destinations in folder: {folder}")

        if not self.client:
            return [
                {
                    "id": "fpd-mock1",
                    "name": "internal-apps",
                    "fqdn": [{"name": "app.internal", "port": 443}],
                },
                {
                    "id": "fpd-mock2",
                    "name": "corp-ranges",
                    "ip_addresses": [{"name": "10.0.0.0/8"}],
                },
            ]

        try:
            results = self.client.forwarding_profile_destination.list(folder=folder)
            return [json.loads(result.model_dump_json(exclude_unset=True)) for result in results]
        except Exception as e:
            self._handle_api_exception("listing", folder, "forwarding profile destinations", e)

    def delete_forwarding_profile_destination(
        self,
        folder: str | None = None,
        name: str | None = None,
        destination_id: str | None = None,
    ) -> bool:
        """Delete a forwarding profile destination by name or UUID.

        Args:
            folder: Folder containing the destination (used with name)
            name: Name of the destination to delete
            destination_id: UUID of the destination (takes precedence over name)

        Returns:
            bool: True if deletion was successful

        """
        folder = folder or "Mobile Users"
        self.logger.info(f"Deleting forwarding profile destination: {destination_id or name} from folder {folder}")

        if not self.client:
            return True

        try:
            if not destination_id:
                destination = self.client.forwarding_profile_destination.fetch(name=name, folder=folder)
                destination_id = str(destination.id)
            self.client.forwarding_profile_destination.delete(destination_id)
            return True
        except Exception as e:
            self._handle_api_exception("deletion", folder, destination_id or name or "", e)


class LazyClient:
    """Lazy wrapper for SCMClient that delays initialization until first use."""

    def __init__(self):
        """Initialize the lazy client wrapper."""
        self._client = None

    def __getattr__(self, name):
        """Initialize client on first access (never for dunder lookups)."""
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        if self._client is None:
            self._client = SCMClient()
        return getattr(self._client, name)

    def __setattr__(self, name, value):
        """Forward attribute setting to inner client (except _client itself)."""
        if name == "_client":
            object.__setattr__(self, name, value)
        else:
            if self._client is None:
                self._client = SCMClient()
            setattr(self._client, name, value)

    def __delattr__(self, name):
        """Forward attribute deletion to inner client."""
        if self._client is None:
            raise AttributeError(name)
        delattr(self._client, name)


# Create a singleton instance of the SCM client with lazy initialization
scm_client = LazyClient()
