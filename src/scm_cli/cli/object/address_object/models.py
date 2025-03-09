"""Address object models and utilities for SCM CLI."""

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from scm.client import ScmClient
from scm.exceptions import NotFoundError
from scm.models.objects import (
    AddressCreateModel,
    AddressUpdateModel,
)

from src.scm_cli.utils.decorators import timeit, retry

# Use child logger from the root logger
logger = logging.getLogger("scm_cli.cli.object.address_object.models")

# Common type mappings
CLI_TO_SDK_TYPE = {"ip-netmask": "ip", "ip-range": "range", "fqdn": "fqdn"}
SDK_TO_CLI_TYPE = {"ip": "ip-netmask", "range": "ip-range", "fqdn": "fqdn"}


# CLI-specific models based on Pydantic
class AddressObjectCLI(BaseModel):
    """CLI representation of an address object."""

    name: str
    type: str
    value: str
    description: Optional[str] = None
    tag: Optional[List[str]] = None
    folder: str
    id: Optional[str] = None


# Exception classes
class ValidationError(Exception):
    """Exception raised for address object validation errors."""

    pass


class APIError(Exception):
    """Exception raised for API-related errors."""

    pass


class ResourceNotFoundError(Exception):
    """Exception raised when a resource is not found."""

    pass


def get_attribute_safely(obj: Any, attr_name: str, default=None) -> Any:
    """Safely get an attribute from an object.

    Args:
        obj: Object to get attribute from
        attr_name: Name of the attribute
        default: Default value if attribute doesn't exist

    Returns:
        Attribute value or default
    """
    if hasattr(obj, attr_name):
        value = getattr(obj, attr_name)
        # Handle enum values
        if hasattr(value, "value"):
            return value.value
        return value
    return default


class AddressObjectAPI:
    """API for address object operations."""

    def __init__(self, client: ScmClient):
        """Initialize the address object API.

        Args:
            client: Initialized SCM client
        """
        self.client = client
        self.address = client.address

    @timeit
    def list_objects(
        self, folder: str, filter_criteria: Optional[Dict[str, str]] = None
    ) -> List[Any]:
        """List address objects in a folder.

        Args:
            folder: Folder to list objects from
            filter_criteria: Optional filter criteria

        Returns:
            List of address objects as Pydantic models

        Raises:
            APIError: If API request fails
        """
        try:
            # Get all address objects in the folder
            addresses = self.address.list(folder=folder)

            # Apply filters if provided
            if filter_criteria:
                filtered_result = []
                for addr in addresses:
                    match = True

                    # Apply filters - work directly with attributes
                    for key, value in filter_criteria.items():
                        if key == "name":
                            name_attr = get_attribute_safely(addr, "name", "")
                            if value.lower() not in name_attr.lower():
                                match = False
                                break
                        elif key == "type":
                            # Get type from model
                            addr_type = get_attribute_safely(addr, "type", None)
                            if addr_type:
                                # Convert for comparison
                                cli_type = SDK_TO_CLI_TYPE.get(addr_type, addr_type)
                                if value.lower() != cli_type.lower():
                                    match = False
                                    break
                            else:
                                match = False
                                break
                        elif key == "value":
                            # Check in all possible value fields
                            value_fields = ["ip_netmask", "ip_range", "fqdn"]
                            value_match = False
                            for field in value_fields:
                                field_value = get_attribute_safely(addr, field, None)
                                if (
                                    field_value
                                    and value.lower() in str(field_value).lower()
                                ):
                                    value_match = True
                                    break
                            if not value_match:
                                match = False
                                break
                        elif key == "tag":
                            tags = get_attribute_safely(addr, "tag", []) or []
                            if not any(value.lower() in tag.lower() for tag in tags):
                                match = False
                                break

                    if match:
                        filtered_result.append(addr)

                return filtered_result

            return addresses

        except Exception as e:
            raise APIError(f"Failed to list address objects: {str(e)}")

    @timeit
    def get_object(self, folder: str, name: str) -> Optional[Any]:
        """Get an address object by name.

        Args:
            folder: Folder containing the object
            name: Name of the object

        Returns:
            Address object (Pydantic model) or None if not found

        Raises:
            APIError: If API request fails
        """
        try:
            # Use fetch if available
            if hasattr(self.address, "fetch") and callable(
                getattr(self.address, "fetch")
            ):
                try:
                    # Use the retry decorator for API operations that might fail intermittently
                    @retry(max_attempts=3, delay=0.5)
                    def fetch_with_retry():
                        return self.address.fetch(folder=folder, name=name)
                    
                    obj = fetch_with_retry()
                    return obj
                except NotFoundError:
                    return None
                except Exception as e:
                    logger.debug(f"Fetch method failed: {str(e)}, trying alternatives")

            # Use list and filter if fetch not available
            addresses = self.address.list(folder=folder)
            for addr in addresses:
                if get_attribute_safely(addr, "name", None) == name:
                    return addr

            return None

        except Exception as e:
            raise APIError(f"Failed to get address object: {str(e)}")

    @timeit
    def create_object(self, folder: str, data: Dict[str, Any]) -> Any:
        """Create a new address object.

        Args:
            folder: Folder to create object in
            data: Object data

        Returns:
            Created address object as Pydantic model

        Raises:
            ValidationError: If object data is invalid
            APIError: If API request fails
        """
        try:
            # Ensure folder is set
            data["folder"] = folder

            # Convert CLI type to SDK type if needed
            if "type" in data:
                data["type"] = CLI_TO_SDK_TYPE.get(data["type"], data["type"])

            # Handle value field
            if "value" in data:
                value = data.pop("value")

                # If type is specified, use it
                if "type" in data:
                    addr_type = data.pop("type")
                # If not, try to infer from value
                else:
                    # Determine type from value format
                    if "/" in value:  # Looks like a CIDR notation
                        addr_type = "ip"
                    elif "-" in value:  # Looks like a range
                        addr_type = "range"
                    elif any(
                        c.isalpha() for c in value
                    ):  # Contains letters, likely FQDN
                        addr_type = "fqdn"
                    else:  # Default to IP if we can't determine
                        addr_type = "ip"
                    logger.debug(
                        f"Inferred type '{addr_type}' from value format: {value}"
                    )

                # Set the appropriate field based on type
                if addr_type == "ip":
                    data["ip_netmask"] = value
                elif addr_type == "range":
                    data["ip_range"] = value
                elif addr_type == "fqdn":
                    data["fqdn"] = value
                else:
                    raise ValidationError(f"Invalid address type: {addr_type}")

            # Create the object - let the SDK handle the pydantic conversion
            try:
                # Define a retry-enabled creation function for API stability
                @retry(max_attempts=2, delay=1.0)
                def create_with_retry(data_dict):
                    try:
                        # First try direct dictionary approach
                        return self.address.create(data_dict)
                    except Exception as error_e:
                        # If direct creation fails, try using the model
                        logger.debug(f"Direct creation failed: {str(error_e)}, trying with model")
                        model = AddressCreateModel(**data_dict)
                        return self.address.create(model)
                
                # Call the retry-wrapped function
                obj = create_with_retry(data)
                return obj
            except Exception as e:
                # This will be reached if all retry attempts failed
                logger.error(f"All creation attempts failed: {str(e)}")
                raise

        except Exception as e:
            if "already exists" in str(e) or "not unique" in str(e):
                raise ValidationError(
                    f"Address object with name '{data.get('name')}' already exists"
                )
            raise APIError(f"Failed to create address object: {str(e)}")

    @timeit
    def update_object(self, folder: str, name: str, data: Dict[str, Any]) -> Any:
        """Update an existing address object.

        Args:
            folder: Folder containing the object
            name: Name of the object
            data: Updated object data

        Returns:
            Updated address object as Pydantic model

        Raises:
            ResourceNotFoundError: If object not found
            ValidationError: If object data is invalid
            APIError: If API request fails
        """
        try:
            # Get existing object (as Pydantic model)
            existing_obj = self.get_object(folder, name)
            if not existing_obj:
                raise ResourceNotFoundError(
                    f"Address object '{name}' not found in folder '{folder}'"
                )

            # Build update dictionary from existing object attributes
            update_data = {}
            # Extract key attributes from existing object
            for attr_name in [
                "name",
                "folder",
                "id",
                "type",
                "description",
                "tag",
                "ip_netmask",
                "ip_range",
                "fqdn",
            ]:
                value = get_attribute_safely(existing_obj, attr_name, None)
                if value is not None:
                    update_data[attr_name] = value

            # Update with new data
            update_data.update(data)

            # Ensure name and folder are set
            update_data["name"] = name
            update_data["folder"] = folder

            # Convert CLI type to SDK type if needed
            if "type" in update_data:
                update_data["type"] = CLI_TO_SDK_TYPE.get(
                    update_data["type"], update_data["type"]
                )

            # Handle value field if present in new data
            if "value" in data:
                value = data["value"]

                # Try to determine address type
                # First try using the provided type
                if "type" in update_data:
                    addr_type = update_data.pop("type")
                    addr_type = CLI_TO_SDK_TYPE.get(addr_type, addr_type)
                # Next try getting type from existing object
                else:
                    # Try to infer from existing value fields
                    if get_attribute_safely(existing_obj, "ip_netmask", None):
                        addr_type = "ip"
                    elif get_attribute_safely(existing_obj, "ip_range", None):
                        addr_type = "range"
                    elif get_attribute_safely(existing_obj, "fqdn", None):
                        addr_type = "fqdn"
                    # Try to infer from value format as last resort
                    else:
                        # Determine type from value format
                        if "/" in value:  # Looks like a CIDR notation
                            addr_type = "ip"
                        elif "-" in value:  # Looks like a range
                            addr_type = "range"
                        elif any(
                            c.isalpha() for c in value
                        ):  # Contains letters, likely FQDN
                            addr_type = "fqdn"
                        else:  # Default to IP if we can't determine
                            addr_type = "ip"
                        logger.debug(
                            f"Inferred type '{addr_type}' from value format: {value}"
                        )

                # Set the appropriate field based on type
                if addr_type == "ip":
                    update_data["ip_netmask"] = value
                    update_data.pop("ip_range", None)
                    update_data.pop("fqdn", None)
                elif addr_type == "range":
                    update_data["ip_range"] = value
                    update_data.pop("ip_netmask", None)
                    update_data.pop("fqdn", None)
                elif addr_type == "fqdn":
                    update_data["fqdn"] = value
                    update_data.pop("ip_netmask", None)
                    update_data.pop("ip_range", None)
                else:
                    raise ValidationError(f"Invalid address type: {addr_type}")

                # Log what we determined
                logger.debug(f"Using address type '{addr_type}' for value '{value}'")

                # Remove the value field as we've processed it
                update_data.pop("value", None)

            # Log what we're about to update with
            logger.debug(f"Updating address object with data: {update_data}")

            # Update the object - pass data directly to update method
            try:
                # Try direct update first
                obj = self.address.update(update_data)
                return obj
            except Exception as e:
                # If direct update fails, try using the model
                logger.debug(f"Direct update failed: {str(e)}, trying with model")
                model = AddressUpdateModel(**update_data)
                obj = self.address.update(model)
                return obj

        except NotFoundError:
            raise ResourceNotFoundError(
                f"Address object '{name}' not found in folder '{folder}'"
            )
        except Exception as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Address object '{name}' not found in folder '{folder}'"
                )
            raise APIError(f"Failed to update address object: {str(e)}")

    @timeit
    def delete_object(self, folder: str, name: str) -> None:
        """Delete an address object.

        Args:
            folder: Folder containing the object
            name: Name of the object

        Raises:
            ResourceNotFoundError: If object not found
            APIError: If API request fails
        """
        try:
            # Get existing object to get its ID
            existing_obj = self.get_object(folder, name)
            if not existing_obj:
                raise ResourceNotFoundError(
                    f"Address object '{name}' not found in folder '{folder}'"
                )

            # Get the ID from the object
            obj_id = get_attribute_safely(existing_obj, "id", None)

            if not obj_id:
                raise APIError(f"Address object '{name}' has no ID")

            # Delete the object
            self.address.delete(obj_id)

        except NotFoundError:
            raise ResourceNotFoundError(
                f"Address object '{name}' not found in folder '{folder}'"
            )
        except Exception as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError(
                    f"Address object '{name}' not found in folder '{folder}'"
                )
            raise APIError(f"Failed to delete address object: {str(e)}")
