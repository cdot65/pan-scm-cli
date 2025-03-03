"""Mock SDK module to simulate the actual pan-scm-sdk package."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union


class AddressObjectType(str, Enum):
    """Enum for address object types."""

    IP = "ip"
    RANGE = "range"
    WILDCARD = "wildcard"
    FQDN = "fqdn"


class AddressObject:
    """Mock AddressObject class."""

    def __init__(
        self,
        name: str,
        type: AddressObjectType,
        value: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        """Initialize an address object.

        Args:
            name: The name of the address object
            type: The type of address (IP, RANGE, WILDCARD, FQDN)
            value: The value of the address
            description: Optional description
            tags: Optional list of tags
        """
        self.name = name
        self.type = type
        self.value = value
        self.description = description
        self.tags = tags or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary.

        Returns:
            Dict representation of the object
        """
        return {
            "name": self.name,
            "type": self.type.value,
            "value": self.value,
            "description": self.description,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AddressObject":
        """Create an AddressObject from a dictionary.

        Args:
            data: Dictionary with address object data

        Returns:
            AddressObject instance
        """
        return cls(
            name=data["name"],
            type=AddressObjectType(data["type"]),
            value=data["value"],
            description=data.get("description"),
            tags=data.get("tags", []),
        )


class ResourceNotFoundError(Exception):
    """Exception raised when a resource is not found."""

    pass


class ValidationError(Exception):
    """Exception raised when validation fails."""

    pass


class AuthenticationError(Exception):
    """Exception raised when authentication fails."""

    pass


class APIError(Exception):
    """Exception raised for general API errors."""

    pass


class AddressObjectClient:
    """Mock client for address objects."""

    def __init__(self) -> None:
        """Initialize client with empty storage."""
        self.storage: Dict[str, Dict[str, AddressObject]] = {}

    def create(
        self, folder: str, address_object: AddressObject
    ) -> AddressObject:
        """Create a new address object.

        Args:
            folder: The folder to create the address object in
            address_object: The address object to create

        Returns:
            The created address object

        Raises:
            ValidationError: If the address object is invalid
        """
        if not folder or not isinstance(folder, str):
            raise ValidationError("Folder must be a non-empty string")

        if not address_object or not isinstance(address_object, AddressObject):
            raise ValidationError("Address object must be an AddressObject instance")

        # Initialize folder if it doesn't exist
        if folder not in self.storage:
            self.storage[folder] = {}

        # Check if address object with same name already exists
        if address_object.name in self.storage[folder]:
            raise ValidationError(f"Address object {address_object.name} already exists")

        # Store the address object
        self.storage[folder][address_object.name] = address_object
        return address_object

    def get(self, folder: str, name: str) -> AddressObject:
        """Get an address object by folder and name.

        Args:
            folder: The folder containing the address object
            name: The name of the address object

        Returns:
            The address object

        Raises:
            ResourceNotFoundError: If the address object doesn't exist
        """
        if folder not in self.storage or name not in self.storage[folder]:
            raise ResourceNotFoundError(
                f"Address object {name} not found in folder {folder}"
            )

        return self.storage[folder][name]

    def update(
        self, folder: str, address_object: AddressObject
    ) -> AddressObject:
        """Update an address object.

        Args:
            folder: The folder containing the address object
            address_object: The updated address object

        Returns:
            The updated address object

        Raises:
            ResourceNotFoundError: If the address object doesn't exist
            ValidationError: If the address object is invalid
        """
        if not folder or not isinstance(folder, str):
            raise ValidationError("Folder must be a non-empty string")

        if not address_object or not isinstance(address_object, AddressObject):
            raise ValidationError("Address object must be an AddressObject instance")

        if folder not in self.storage or address_object.name not in self.storage[folder]:
            raise ResourceNotFoundError(
                f"Address object {address_object.name} not found in folder {folder}"
            )

        # Update the address object
        self.storage[folder][address_object.name] = address_object
        return address_object

    def delete(self, folder: str, name: str) -> None:
        """Delete an address object.

        Args:
            folder: The folder containing the address object
            name: The name of the address object

        Raises:
            ResourceNotFoundError: If the address object doesn't exist
        """
        if folder not in self.storage or name not in self.storage[folder]:
            raise ResourceNotFoundError(
                f"Address object {name} not found in folder {folder}"
            )

        del self.storage[folder][name]

    def list(self, folder: str) -> List[AddressObject]:
        """List all address objects in a folder.

        Args:
            folder: The folder to list address objects from

        Returns:
            List of address objects in the folder
        """
        if folder not in self.storage:
            return []

        return list(self.storage[folder].values())


class Client:
    """Mock SCM client."""

    def __init__(
        self, client_id: str, client_secret: str, tsg_id: str, 
        base_url: str = "https://api.scm.paloaltonetworks.com", 
        verify: bool = True
    ) -> None:
        """Initialize the SCM client.

        Args:
            client_id: The client ID for OAuth2 authentication
            client_secret: The client secret for OAuth2 authentication
            tsg_id: The TSG ID for the tenant
            base_url: The base URL for the SCM API
            verify: Whether to verify SSL certificates
        """
        # Validate required parameters
        if not client_id or not client_secret or not tsg_id:
            raise AuthenticationError("client_id, client_secret, and tsg_id are required")
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.tsg_id = tsg_id
        self.base_url = base_url
        self.verify = verify
        
        # Initialize address object client
        self.address_objects = AddressObjectClient()
        
    def test_connection(self) -> bool:
        """Test the connection to the SCM API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        # In a real implementation, this would make an API call
        # For our mock, just check that we have valid credentials
        return bool(self.client_id and self.client_secret and self.tsg_id)