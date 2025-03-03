"""SDK client for SCM CLI."""

from typing import Dict, List, Optional

from .config import SCMConfig
from .mock_sdk import (  # Import from actual pan-scm-sdk when available
    APIError,
    AddressObject,
    AddressObjectType,
    AuthenticationError,
    Client,
    ResourceNotFoundError,
    ValidationError,
)


class SDKClient:
    """SDK client for SCM CLI."""

    def __init__(self, config: SCMConfig) -> None:
        """Initialize SDK client.

        Args:
            config: SCM configuration
        """
        self.config = config
        self.client = Client(
            client_id=config.client_id,
            client_secret=config.client_secret,
            tsg_id=config.tsg_id,
            base_url=config.base_url,
            verify=config.verify_ssl,
        )

    def test_connection(self) -> bool:
        """Test connection to SCM API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        return self.client.test_connection()

    def create_address_object(
        self,
        folder: str,
        name: str,
        type_val: str,
        value: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> AddressObject:
        """Create address object.

        Args:
            folder: Folder to create address object in
            name: Name of address object
            type_val: Type of address object (ip, range, wildcard, fqdn)
            value: Value of address object
            description: Description of address object
            tags: Tags for address object

        Returns:
            Created address object

        Raises:
            ValidationError: If validation fails
            APIError: If API request fails
        """
        try:
            addr_type = AddressObjectType(type_val)
            address = AddressObject(
                name=name,
                type=addr_type,
                value=value,
                description=description,
                tags=tags,
            )
            return self.client.address_objects.create(folder=folder, address_object=address)
        except (ValidationError, ValueError) as e:
            raise ValidationError(f"Invalid address object data: {str(e)}")
        except APIError as e:
            raise APIError(f"API error: {str(e)}")
        except Exception as e:
            raise APIError(f"Unknown error: {str(e)}")

    def get_address_object(self, folder: str, name: str) -> AddressObject:
        """Get address object.

        Args:
            folder: Folder containing address object
            name: Name of address object

        Returns:
            Address object

        Raises:
            ResourceNotFoundError: If address object not found
            APIError: If API request fails
        """
        try:
            return self.client.address_objects.get(folder=folder, name=name)
        except ResourceNotFoundError:
            raise ResourceNotFoundError(f"Address object {name} not found in folder {folder}")
        except APIError as e:
            raise APIError(f"API error: {str(e)}")
        except Exception as e:
            raise APIError(f"Unknown error: {str(e)}")

    def update_address_object(
        self,
        folder: str,
        name: str,
        type_val: str,
        value: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> AddressObject:
        """Update address object.

        Args:
            folder: Folder containing address object
            name: Name of address object
            type_val: Type of address object (ip, range, wildcard, fqdn)
            value: Value of address object
            description: Description of address object
            tags: Tags for address object

        Returns:
            Updated address object

        Raises:
            ResourceNotFoundError: If address object not found
            ValidationError: If validation fails
            APIError: If API request fails
        """
        try:
            # Get existing address object first
            existing = self.client.address_objects.get(folder=folder, name=name)
            
            # Update fields
            addr_type = AddressObjectType(type_val)
            address = AddressObject(
                name=name,
                type=addr_type,
                value=value,
                description=description if description is not None else existing.description,
                tags=tags if tags is not None else existing.tags,
            )
            
            return self.client.address_objects.update(folder=folder, address_object=address)
        except ResourceNotFoundError:
            raise ResourceNotFoundError(f"Address object {name} not found in folder {folder}")
        except (ValidationError, ValueError) as e:
            raise ValidationError(f"Invalid address object data: {str(e)}")
        except APIError as e:
            raise APIError(f"API error: {str(e)}")
        except Exception as e:
            raise APIError(f"Unknown error: {str(e)}")

    def delete_address_object(self, folder: str, name: str) -> None:
        """Delete address object.

        Args:
            folder: Folder containing address object
            name: Name of address object

        Raises:
            ResourceNotFoundError: If address object not found
            APIError: If API request fails
        """
        try:
            self.client.address_objects.delete(folder=folder, name=name)
        except ResourceNotFoundError:
            raise ResourceNotFoundError(f"Address object {name} not found in folder {folder}")
        except APIError as e:
            raise APIError(f"API error: {str(e)}")
        except Exception as e:
            raise APIError(f"Unknown error: {str(e)}")

    def list_address_objects(self, folder: str) -> List[AddressObject]:
        """List address objects.

        Args:
            folder: Folder to list address objects from

        Returns:
            List of address objects

        Raises:
            APIError: If API request fails
        """
        try:
            return self.client.address_objects.list(folder=folder)
        except APIError as e:
            raise APIError(f"API error: {str(e)}")
        except Exception as e:
            raise APIError(f"Unknown error: {str(e)}")