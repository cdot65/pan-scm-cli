"""SDK client for SCM CLI."""

from typing import Dict, List, Optional, Any
import uuid
import time
import logging

# Configure logging
logger = logging.getLogger("scm_cli.sdk_client")
# Set debug level for detailed timing information
logger.setLevel(logging.DEBUG)

# Set up console handler if not already configured
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

from .config import SCMConfig

# Import from pan-scm-sdk
from scm.client import Scm
from scm.config.objects import Address

# Import SDK models - try multiple paths to handle different SDK versions
# First try to import the models mentioned in the task
try:
    # Try to import from models/objects path as mentioned in the task
    from scm.models.objects import (
        AddressCreateModel,
        AddressUpdateModel, 
        AddressResponseModel
    )
    logger.debug("Successfully imported models from scm.models.objects")
    HAS_MODELS = True
    HAS_NEW_MODELS = True
except ImportError:
    logger.debug("Could not import models from scm.models.objects, trying alternative locations")
    HAS_NEW_MODELS = False
    try:
        # Try to import from standard location
        from scm.models.address import AddressRequestSchema
        logger.debug("Successfully imported AddressRequestSchema from scm.models.address")
        HAS_MODELS = True
    except ImportError:
        try:
            # Try alternate location
            from scm.config.models import AddressModel
            AddressRequestSchema = AddressModel  # Alias for consistency
            logger.debug("Successfully imported AddressModel from scm.config.models")
            HAS_MODELS = True
        except ImportError:
            # No models available
            logger.debug("No models available in SDK")
            HAS_MODELS = False
from scm.exceptions import (
    InvalidObjectError as ValidationError,
    NotFoundError as ResourceNotFoundError,
    AuthenticationError,
    NameNotUniqueError,
)

# Define a custom APIError class to match our internal error handling
class APIError(Exception):
    """Exception raised for general API errors."""
    pass

# Performance measurement decorator
def timeit(method):
    """Decorator to measure the execution time of methods."""
    def timed(*args, **kwargs):
        start_time = time.time()
        result = method(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        # Extract method name and class name (if method is part of a class)
        if hasattr(method, '__qualname__'):
            name = method.__qualname__
        else:
            name = method.__name__
        logger.debug(f"API call timing: {name} took {duration:.3f} seconds")
        # If duration is longer than 1 second, log as warning
        if duration > 1.0:
            logger.warning(f"API call {name} took {duration:.3f} seconds - performance optimization may be needed")
        return result
    return timed

# Adapter/helper class to maintain compatibility and provide utility functions 
# for working with SDK models
class AddressObject:
    """Address object adapter for SCM SDK."""
    
    def __init__(
        self,
        name: str,
        type_val: str,
        value: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        folder: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        """Initialize an address object.

        Args:
            name: The name of the address object
            type_val: The type of address (ip, range, wildcard, fqdn)
            value: The value of the address
            description: Optional description
            tags: Optional list of tags
            folder: Optional folder
            id: Optional UUID for existing objects
        """
        self.name = name
        self.type = type_val
        self.value = value
        self.description = description
        self.tags = tags or []
        self.folder = folder
        self.id = id
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert object to dictionary.

        Returns:
            Dict representation of the object
        """
        result = {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "tag": self.tags,
        }
        
        # Add the appropriate value field based on type
        if self.type == "ip":
            result["ip_netmask"] = self.value
        elif self.type == "range":
            result["ip_range"] = self.value
        elif self.type == "fqdn":
            result["fqdn"] = self.value
        
        if self.folder:
            result["folder"] = self.folder
            
        if self.id:
            result["id"] = self.id
            
        return result
    
    def to_sdk_model(self) -> Any:
        """Convert to an SDK model object.
        
        Returns:
            An SDK model instance based on the available models
            
        Raises:
            ValueError: If no appropriate model can be created
        """
        # Create a dict with all the required fields
        model_dict = {
            "name": self.name,
            "folder": self.folder or "Shared"  # Default to Shared if no folder specified
        }
        
        # Add the appropriate value field based on type
        if self.type == "ip":
            model_dict["ip_netmask"] = self.value
        elif self.type == "range":
            model_dict["ip_range"] = self.value
        elif self.type == "fqdn":
            model_dict["fqdn"] = self.value
            
        # The API seems to require a description even though schema says optional
        # Always include description (empty string if not provided)
        model_dict["description"] = self.description if self.description else ""
        
        # Add other optional fields if they exist
        if self.tags:
            model_dict["tag"] = self.tags
        if self.id:
            model_dict["id"] = self.id
            
        # Create appropriate model based on what's available
        if HAS_NEW_MODELS:
            logger.debug("Using new SDK models (AddressCreateModel/AddressUpdateModel)")
            if self.id:
                # If we have an ID, it's an update
                return AddressUpdateModel(**model_dict)
            else:
                # Otherwise it's a create
                return AddressCreateModel(**model_dict)
        elif HAS_MODELS:
            logger.debug("Using legacy SDK model (AddressRequestSchema)")
            return AddressRequestSchema(**model_dict)
        else:
            logger.debug("No SDK models available, returning dictionary")
            return model_dict
    
    @classmethod
    def from_sdk_object(cls, sdk_obj: Any) -> "AddressObject":
        """Create an AddressObject from a SDK response object.
        
        Args:
            sdk_obj: Response object from the SDK
            
        Returns:
            AddressObject instance
        """
        # If the SDK object has a model_dump method (Pydantic model), use it
        if hasattr(sdk_obj, 'model_dump') and callable(getattr(sdk_obj, 'model_dump')):
            try:
                # Try using the Pydantic model_dump method with exclude options
                logger.debug("Using model_dump method to convert SDK object")
                # This will exclude unset and None values for cleaner output
                obj_dict = sdk_obj.model_dump(exclude_unset=True, exclude_none=True)
                logger.debug(f"Model dump successful: {list(obj_dict.keys())}")
            except Exception as e:
                logger.debug(f"Error using model_dump: {str(e)}, falling back to attribute access")
                obj_dict = {}
                # Fallback to manual attribute access
                for attr in dir(sdk_obj):
                    if not attr.startswith('_') and attr != 'model_dump':
                        try:
                            value = getattr(sdk_obj, attr)
                            if value is not None:
                                obj_dict[attr] = value
                        except Exception:
                            pass
        else:
            # If it's not a Pydantic model, try to access attributes directly
            logger.debug("SDK object doesn't have model_dump, using attribute access")
            obj_dict = {}
            for attr in dir(sdk_obj):
                if not attr.startswith('_'):
                    try:
                        value = getattr(sdk_obj, attr)
                        if value is not None and not callable(value):
                            obj_dict[attr] = value
                    except Exception:
                        pass
        
        # Determine the type and value based on which field is present
        if "ip_netmask" in obj_dict and obj_dict["ip_netmask"]:
            type_val = "ip"
            value = obj_dict["ip_netmask"]
        elif "ip_range" in obj_dict and obj_dict["ip_range"]:
            type_val = "range"
            value = obj_dict["ip_range"]
        elif "fqdn" in obj_dict and obj_dict["fqdn"]:
            type_val = "fqdn"
            value = obj_dict["fqdn"]
        else:
            # Try attribute access if dictionary lookup fails
            if hasattr(sdk_obj, "ip_netmask") and getattr(sdk_obj, "ip_netmask", None):
                type_val = "ip"
                value = getattr(sdk_obj, "ip_netmask")
            elif hasattr(sdk_obj, "ip_range") and getattr(sdk_obj, "ip_range", None):
                type_val = "range"
                value = getattr(sdk_obj, "ip_range")
            elif hasattr(sdk_obj, "fqdn") and getattr(sdk_obj, "fqdn", None):
                type_val = "fqdn"
                value = getattr(sdk_obj, "fqdn")
            else:
                type_val = "unknown"
                value = ""
            
        # Extract name with fallback
        if "name" in obj_dict:
            name = obj_dict["name"]
        else:
            name = getattr(sdk_obj, "name", "unknown")
            
        # Extract description with fallback
        if "description" in obj_dict:
            description = obj_dict["description"]
        else:
            description = getattr(sdk_obj, "description", None)
            
        # Extract tags with fallback - the SDK might use 'tag' instead of 'tags'
        if "tag" in obj_dict and obj_dict["tag"]:
            tags = obj_dict["tag"]
        elif "tags" in obj_dict and obj_dict["tags"]:
            tags = obj_dict["tags"]
        elif hasattr(sdk_obj, "tag") and getattr(sdk_obj, "tag", None):
            tags = getattr(sdk_obj, "tag")
        elif hasattr(sdk_obj, "tags") and getattr(sdk_obj, "tags", None):
            tags = getattr(sdk_obj, "tags")
        else:
            tags = []
            
        # Get folder with fallback
        if "folder" in obj_dict:
            folder = obj_dict["folder"]
        else:
            folder = getattr(sdk_obj, "folder", None)
            
        # Get ID with fallback
        if "id" in obj_dict:
            id_val = str(obj_dict["id"])
        else:
            id_val = str(getattr(sdk_obj, "id", None)) if getattr(sdk_obj, "id", None) is not None else None
            
        return cls(
            name=name,
            type_val=type_val,
            value=value,
            description=description,
            tags=tags,
            folder=folder,
            id=id_val,
        )
    
    @staticmethod
    def cli_to_sdk_type(cli_type: str) -> str:
        """Convert CLI type to SDK type.
        
        Args:
            cli_type: CLI type (ip-netmask, ip-range, fqdn)
            
        Returns:
            SDK type (ip, range, fqdn)
        """
        type_map = {
            "ip-netmask": "ip",
            "ip-range": "range",
            "fqdn": "fqdn"
        }
        return type_map.get(cli_type, cli_type)
    
    @staticmethod
    def sdk_to_cli_type(sdk_type: str) -> str:
        """Convert SDK type to CLI type.
        
        Args:
            sdk_type: SDK type (ip, range, fqdn)
            
        Returns:
            CLI type (ip-netmask, ip-range, fqdn)
        """
        type_map = {
            "ip": "ip-netmask",
            "range": "ip-range",
            "fqdn": "fqdn"
        }
        return type_map.get(sdk_type, sdk_type)


class SDKClient:
    """SDK client for SCM CLI."""

    def __init__(self, config: SCMConfig) -> None:
        """Initialize SDK client.

        Args:
            config: SCM configuration
        """
        self.config = config
        self.client = Scm(
            client_id=config.client_id,
            client_secret=config.client_secret,
            tsg_id=config.tsg_id,
            log_level="INFO",
        )
        # Initialize the address manager
        self.addresses = Address(self.client)

    @timeit
    def test_connection(self) -> bool:
        """Test connection to SCM API.
        
        Returns:
            True if connection is successful
            
        Raises:
            AuthenticationError: If authentication fails
            APIError: If API request fails
        """
        # Try to list folders to test the connection
        try:
            # A simple list operation to verify we have valid credentials
            # The Address manager requires a folder to list objects
            # So we'll try to list addresses in the "All" folder
            self.addresses.list(folder="All")
            return True
        except Exception as e:
            # Re-raise the exception with a more descriptive message
            raise APIError(f"Failed to connect to SCM API: {str(e)}")

    @timeit
    def direct_update_address_object(self, folder: str, name: str, type_val: str, value: str,
                                    description: Optional[str] = None, tags: Optional[List[str]] = None,
                                    object_id: Optional[str] = None) -> AddressObject:
        """Update an address object using direct SDK calls, handling object lookup internally.
        
        This method tries to update an address object in the most efficient way possible,
        based on the capabilities of the underlying SDK. Supports partial updates where
        only provided fields will be updated.
        
        Args:
            folder: Folder containing the address object
            name: Name of the address object
            type_val: Type of the address object (ip, range, fqdn)
            value: Value for the address object
            description: Optional description (if None, won't be updated)
            tags: Optional tags (if None, won't be updated)
            object_id: Optional object ID to avoid lookup
            
        Returns:
            AddressObject: The updated address object
            
        Raises:
            ResourceNotFoundError: If the object doesn't exist
            ValidationError: If update fails
            APIError: If API request fails
        """
        try:
            # Create config dictionary with required fields
            config = {
                "name": name,
                "folder": folder,
            }
            
            # Only include description if explicitly provided
            if description is not None:
                config["description"] = description
                
            # Only include tags if explicitly provided  
            if tags is not None:
                config["tag"] = tags
            
            # Add the appropriate field based on address type
            if type_val == "ip":
                config["ip_netmask"] = value
            elif type_val == "range":
                config["ip_range"] = value
            elif type_val == "fqdn":
                config["fqdn"] = value
            else:
                raise ValidationError(f"Invalid address type: {type_val}")
            
            # If object ID is provided, use it directly (most efficient)
            if object_id:
                logger.debug(f"Using provided object ID: {object_id}")
                # Add the ID to the config
                config["id"] = object_id
                
                # Using a super simple approach that will work with any SDK version
                start_time = time.time()
                
                # Log what we're attempting to do
                logger.debug(f"Using extremely simplified update for ID: {object_id}")
                
                # Skip all the clever strategies and use the most direct approach
                # This avoids any model_dump issues
                
                # Fetch the existing object to preserve values we're not changing
                existing_object = self.fetch_address_object_by_id(object_id)
                if existing_object is None:
                    raise ResourceNotFoundError(f"Could not find address object with ID: {object_id}")
                
                # Create a new dict that exactly matches the structure of the response
                update_dict = existing_object.to_dict()
                
                # Now update the fields we want to change
                update_dict["name"] = name
                update_dict["folder"] = folder
                
                # Update type-specific value field
                if type_val == "ip":
                    # Ensure we remove any existing type-specific fields first
                    if "fqdn" in update_dict:
                        del update_dict["fqdn"]
                    if "ip_range" in update_dict:
                        del update_dict["ip_range"]
                    update_dict["ip_netmask"] = value
                elif type_val == "range":
                    if "fqdn" in update_dict:
                        del update_dict["fqdn"]
                    if "ip_netmask" in update_dict:
                        del update_dict["ip_netmask"]
                    update_dict["ip_range"] = value
                elif type_val == "fqdn":
                    if "ip_netmask" in update_dict:
                        del update_dict["ip_netmask"]
                    if "ip_range" in update_dict:
                        del update_dict["ip_range"]
                    update_dict["fqdn"] = value
                
                # Only update description and tags if provided
                if description is not None:
                    update_dict["description"] = description
                if tags is not None:
                    update_dict["tag"] = tags
                
                # Now submit the update via the most direct REST API call
                logger.debug(f"Performing direct PUT to /config/objects/addresses/{object_id}")
                
                try:
                    # For partial updates, we need to approach this differently
                    # First try direct API call which is most reliable for patches
                    if hasattr(self.client, 'put') and callable(getattr(self.client, 'put')):
                        logger.debug("Using direct REST API call for partial update")
                        url = f"/config/objects/addresses/{object_id}"
                        updated_obj = self.client.put(url, json=update_dict)
                    elif HAS_NEW_MODELS:
                        # Convert to model and then use the address manager's update method
                        logger.debug("Creating AddressUpdateModel for update")
                        try:
                            model = AddressUpdateModel(**update_dict)
                            # Try to get model_dump but handle case where it might not be available
                            if hasattr(model, 'model_dump') and callable(getattr(model, 'model_dump')):
                                update_clean_dict = model.model_dump(exclude_unset=True, exclude_none=True)
                                updated_obj = self.addresses.update(update_clean_dict)
                            else:
                                # If no model_dump method, use the model directly
                                updated_obj = self.addresses.update(model)
                        except Exception as model_error:
                            logger.debug(f"Model-based update failed: {str(model_error)}")
                            # If model fails, use dictionary directly
                            updated_obj = self.addresses.update(update_dict)
                    elif HAS_MODELS:
                        # Convert to model and then use the address manager's update method
                        logger.debug("Creating AddressRequestSchema for update")
                        try:
                            model = AddressRequestSchema(**update_dict)
                            updated_obj = self.addresses.update(model)
                        except Exception as model_error:
                            logger.debug(f"Model-based update failed: {str(model_error)}")
                            # If model fails, use dictionary directly
                            updated_obj = self.addresses.update(update_dict)
                    else:
                        # Try direct update with dict - might not work on all SDK versions
                        updated_obj = self.addresses.update(update_dict)
                except Exception as e:
                    logger.debug(f"All standard update methods failed: {str(e)}")
                    
                    # Last resort - try a different URL or approach
                    if hasattr(self.client, 'put') and callable(getattr(self.client, 'put')):
                        logger.debug("Trying alternative REST API path")
                        try:
                            # Try different API path
                            url = f"/config/object/addresses/{object_id}"
                            updated_obj = self.client.put(url, json=update_dict)
                        except Exception as e2:
                            logger.debug(f"Alternative API path failed: {str(e2)}")
                            url = f"/resources/objects/addresses/{object_id}"
                            updated_obj = self.client.put(url, json=update_dict)
                    else:
                        # If all else fails, use the official method but with a clean dict
                        clean_dict = {
                            "id": object_id,
                            "name": name,
                            "folder": folder,
                        }
                        
                        # Add the value based on type
                        if type_val == "ip":
                            clean_dict["ip_netmask"] = value
                        elif type_val == "range":
                            clean_dict["ip_range"] = value
                        elif type_val == "fqdn":
                            clean_dict["fqdn"] = value
                            
                        # Add optional fields
                        if description is not None:
                            clean_dict["description"] = description
                        if tags is not None:
                            clean_dict["tag"] = tags
                            
                        updated_obj = self.addresses.update(clean_dict)
                        
                update_time = time.time()
                logger.debug(f"Update with provided ID took {update_time - start_time:.3f} seconds")
                
                return AddressObject.from_sdk_object(updated_obj)
                
            # Otherwise, need to fetch the object first to get its ID
            # Use fetch method - this is the most efficient way to get an object by name
            start_time = time.time()
            try:
                # Try the most efficient method first - fetch by name
                if hasattr(self.addresses, 'fetch') and callable(getattr(self.addresses, 'fetch')):
                    logger.debug(f"Using direct fetch method for '{name}'")
                    existing = self.addresses.fetch(folder=folder, name=name)
                    fetch_time = time.time()
                    logger.debug(f"Direct fetch took {fetch_time - start_time:.3f} seconds")
                    
                    # Add the ID to the config
                    config["id"] = existing.id
                    
                    # Update using the ID with error handling
                    try:
                        updated_obj = self.addresses.update(config)
                    except AttributeError as e:
                        # If we get model_dump error, the SDK might be expecting a model instead of dict
                        if "model_dump" in str(e):
                            logger.debug("SDK expects a model, not a dict. Trying workarounds...")
                            # Try to create a model if possible
                            if hasattr(self.addresses, 'create_model'):
                                model = self.addresses.create_model(config)
                                updated_obj = self.addresses.update(model)
                            else:
                                # Try direct API call
                                if hasattr(self.client, 'put'):
                                    api_path = f"/config/object/addresses/{existing.id}"
                                    logger.debug(f"Using direct API call to {api_path}")
                                    updated_obj = self.client.put(api_path, json=config)
                                else:
                                    raise
                        else:
                            raise
                            
                    update_time = time.time()
                    logger.debug(f"Update with ID took {update_time - fetch_time:.3f} seconds")
                    
                    return AddressObject.from_sdk_object(updated_obj)
                    
                # Try alternative methods if fetch isn't available
                elif hasattr(self.addresses, 'get_by_name') and callable(getattr(self.addresses, 'get_by_name')):
                    logger.debug(f"Using get_by_name method for '{name}'")
                    existing = self.addresses.get_by_name(folder=folder, name=name)
                    lookup_time = time.time()
                    logger.debug(f"Direct lookup by name took {lookup_time - start_time:.3f} seconds")
                    
                    # Add the ID to the config
                    config["id"] = existing.id
                    
                    # Update using the ID with error handling
                    try:
                        updated_obj = self.addresses.update(config)
                    except AttributeError as e:
                        # If we get model_dump error, the SDK might be expecting a model instead of dict
                        if "model_dump" in str(e):
                            logger.debug("SDK expects a model, not a dict. Trying workarounds...")
                            # Try to create a model if possible
                            if hasattr(self.addresses, 'create_model'):
                                model = self.addresses.create_model(config)
                                updated_obj = self.addresses.update(model)
                            else:
                                # Try direct API call
                                if hasattr(self.client, 'put'):
                                    api_path = f"/config/object/addresses/{existing.id}"
                                    logger.debug(f"Using direct API call to {api_path}")
                                    updated_obj = self.client.put(api_path, json=config)
                                else:
                                    raise
                        else:
                            raise
                            
                    update_time = time.time()
                    logger.debug(f"Update with ID took {update_time - lookup_time:.3f} seconds")
                    
                    return AddressObject.from_sdk_object(updated_obj)
            except Exception as e:
                logger.debug(f"Direct lookup methods failed: {str(e)}, trying fallback list method")
            
            # Last resort - use list with filter as a fallback
            logger.warning(f"Falling back to inefficient list method for '{name}'")
            start_time = time.time()
            
            # Get first 10 objects and check if one matches - very limited for performance
            addresses = self.addresses.list(folder=folder, limit=10)
            list_time = time.time()
            logger.debug(f"Listing objects (limit=10) took {list_time - start_time:.3f} seconds")
            
            matching_addresses = [addr for addr in addresses if addr.name == name]
            filter_time = time.time()
            logger.debug(f"Filtering for matching object took {filter_time - list_time:.3f} seconds")
            
            if not matching_addresses:
                raise ResourceNotFoundError(f"Address object {name} not found in folder {folder}")
                
            # Get the first matching address (should be only one with this name)
            existing = matching_addresses[0]
            
            # Add the ID to the config
            config["id"] = existing.id
            
            # Update the object
            updated_obj = self.addresses.update(config)
            update_time = time.time()
            logger.debug(f"Update with ID took {update_time - filter_time:.3f} seconds")
            
            return AddressObject.from_sdk_object(updated_obj)
            
        except ResourceNotFoundError:
            raise ResourceNotFoundError(f"Address object {name} not found in folder {folder}")
        except Exception as e:
            raise APIError(f"Error updating address object: {str(e)}")
    
    @timeit
    def fetch_address_object_by_id(self, object_id: str) -> Optional[AddressObject]:
        """Fetch an address object by its ID.
        
        This is a helper method specifically for updates.
        
        Args:
            object_id: The ID of the object to fetch
            
        Returns:
            AddressObject if found, None if not found
            
        Raises:
            APIError: If an API error occurs
        """
        try:
            logger.debug(f"Fetching address object by ID: {object_id}")
            
            # Try using get direct API call first
            if hasattr(self.client, 'get') and callable(getattr(self.client, 'get')):
                try:
                    api_path = f"/config/objects/addresses/{object_id}"
                    # This will return either a model or a dict depending on SDK version
                    obj = self.client.get(api_path)
                    # Convert to our internal format
                    return AddressObject.from_sdk_object(obj)
                except Exception as e:
                    logger.debug(f"Failed to get object by ID using direct API call: {str(e)}")
            
            # Fall back to get_by_id on the Address manager if available
            if hasattr(self.addresses, 'get_by_id') and callable(getattr(self.addresses, 'get_by_id')):
                try:
                    obj = self.addresses.get_by_id(object_id)
                    return AddressObject.from_sdk_object(obj)
                except Exception as e:
                    logger.debug(f"Failed to get object using get_by_id: {str(e)}")
            
            # Last resort - use list and find by ID
            all_objects = []
            try:
                # Try to get all objects and filter by ID
                for folder in ["All", "Shared", "Texas"]:  # Try common folders
                    try:
                        folder_objects = self.addresses.list(folder=folder)
                        all_objects.extend(folder_objects)
                    except Exception:
                        pass
                        
                # Find by ID
                for obj in all_objects:
                    if str(obj.id) == object_id:
                        return AddressObject.from_sdk_object(obj)
            except Exception as e:
                logger.debug(f"Failed to find object by ID in list: {str(e)}")
                
            # If we get here, we couldn't find the object
            return None
                
        except Exception as e:
            # Re-raise as APIError
            raise APIError(f"Error fetching address object by ID: {str(e)}")
    
    @timeit
    def direct_fetch_address_object(self, folder: str, name: str) -> Optional[AddressObject]:
        """Fetch an address object directly using the SDK's fetch method.
        
        This is the most efficient way to get a single object by name.
        
        Args:
            folder: Folder containing the object
            name: Name of the object
            
        Returns:
            AddressObject if found, None if not found
            
        Raises:
            APIError: If an API error occurs
        """
        try:
            # Check if fetch method is available
            if hasattr(self.addresses, 'fetch') and callable(getattr(self.addresses, 'fetch')):
                # Time the operation
                start_time = time.time()
                
                try:
                    # This will raise ResourceNotFoundError if not found
                    obj = self.addresses.fetch(folder=folder, name=name)
                    
                    # Convert to our internal format
                    result = AddressObject.from_sdk_object(obj)
                    
                    end_time = time.time()
                    logger.debug(f"Direct fetch took {end_time - start_time:.3f} seconds")
                    
                    return result
                except ResourceNotFoundError:
                    # Object doesn't exist
                    logger.debug(f"Object '{name}' not found in folder '{folder}'")
                    return None
            else:
                # Fetch not supported, try get_address_object
                logger.debug(f"fetch method not available, trying alternatives")
                try:
                    return self.get_address_object(folder, name)
                except ResourceNotFoundError:
                    return None
                
        except Exception as e:
            # Re-raise as APIError
            raise APIError(f"Error during direct fetch: {str(e)}")
            
    @timeit
    def direct_create_address_object(self, folder: str, name: str, type_val: str, value: str, 
                                   description: Optional[str] = None, tags: Optional[List[str]] = None) -> AddressObject:
        """Create an address object using direct SDK calls, avoiding our wrapper methods.
        
        This method directly uses the underlying SDK to create an address object,
        bypassing our potentially slower wrapper methods.
        
        Args:
            folder: Folder to create object in
            name: Name of the address object
            type_val: Type of the address object (ip, range, fqdn)
            value: Value for the address object
            description: Optional description
            tags: Optional tags
            
        Returns:
            AddressObject: The created address object
            
        Raises:
            ValidationError: If creation fails
            APIError: If API request fails
        """
        try:
            # Create an AddressObject instance that will help us with model creation
            address_obj = AddressObject(
                name=name,
                type_val=type_val,
                value=value,
                description=description,
                tags=tags,
                folder=folder
            )
            
            # Get the model dictionary directly
            model_dict = {
                "name": name,
                "folder": folder,
                "description": description if description else "Created by SCM CLI",  # Default description if None
                "tag": tags or [],  # Empty list if None
            }
            
            # Add the appropriate field based on address type
            if type_val == "ip":
                model_dict["ip_netmask"] = value
            elif type_val == "range":
                model_dict["ip_range"] = value
            elif type_val == "fqdn":
                model_dict["fqdn"] = value
            
            # Directly call the underlying SDK create method
            logger.debug(f"Direct creating address object: {name} in folder {folder}")
            
            # Time the SDK call
            start_time = time.time()
            
            # Try to use model-based creation first
            try:
                # Log the model contents for debugging
                logger.debug(f"Attempting to create with model: {model_dict}")
                
                # For creating objects, we always use the dictionary approach
                # as per requirements, not the Pydantic model directly
                if HAS_NEW_MODELS:
                    logger.debug("Using AddressCreateModel for creation (as dictionary)")
                    # Create the model first to validate
                    model_obj = AddressCreateModel(**model_dict)
                    # Then use model_dump to get a clean dictionary
                    create_dict = model_obj.model_dump(exclude_unset=True, exclude_none=True)
                    created_obj = self.addresses.create(create_dict)
                elif HAS_MODELS:
                    logger.debug("Using AddressRequestSchema for creation (as dictionary)")
                    # Create the model first to validate
                    model_obj = AddressRequestSchema(**model_dict)
                    # Then use model_dump to get a clean dictionary
                    if hasattr(model_obj, 'model_dump') and callable(getattr(model_obj, 'model_dump')):
                        create_dict = model_obj.model_dump(exclude_unset=True, exclude_none=True)
                    else:
                        # Fall back if no model_dump method
                        create_dict = model_dict
                    created_obj = self.addresses.create(create_dict)
                else:
                    logger.debug("Using dictionary for creation")
                    created_obj = self.addresses.create(model_dict)
            except Exception as e:
                logger.debug(f"Model-based creation failed: {str(e)}, falling back to dictionary")
                # Fall back to dictionary-based creation if model approach fails
                created_obj = self.addresses.create(model_dict)
                
            end_time = time.time()
            logger.debug(f"Direct SDK create call took {end_time - start_time:.3f} seconds")
            
            # If the created object has model_dump, use that for consistent output
            if hasattr(created_obj, 'model_dump') and callable(getattr(created_obj, 'model_dump')):
                logger.debug("Response object has model_dump method, using for output")
                try:
                    # This will be the cleaned output that can be presented to the user
                    dumped = created_obj.model_dump(exclude_unset=True, exclude_none=True)
                    logger.debug(f"model_dump successful: {list(dumped.keys())}")
                except Exception as e:
                    logger.debug(f"model_dump failed: {str(e)}")
            
            # Convert to our internal format for compatibility
            return AddressObject.from_sdk_object(created_obj)
            
        except Exception as e:
            if "already exists" in str(e) or "not unique" in str(e) or "conflict" in str(e):
                raise ValidationError(f"Address object with name '{name}' already exists in folder '{folder}'")
            raise APIError(f"Error creating address object: {str(e)}")
            
    @timeit
    def check_address_object_exists(self, folder: str, name: str) -> bool:
        """Check if an address object exists without retrieving all details.
        
        Args:
            folder: Folder to check in
            name: Name of address object to check
            
        Returns:
            True if the object exists, False otherwise
        """
        try:
            # First try using fetch - the most efficient way to get a single object by name
            try:
                if hasattr(self.addresses, 'fetch') and callable(getattr(self.addresses, 'fetch')):
                    # This will throw ResourceNotFoundError if not found
                    logger.debug(f"Using fetch method to check if '{name}' exists")
                    self.addresses.fetch(folder=folder, name=name)
                    logger.debug(f"Object '{name}' exists according to fetch method")
                    return True
            except ResourceNotFoundError:
                logger.debug(f"Object '{name}' not found using fetch method")
                return False
            except (AttributeError, TypeError):
                # SDK doesn't support fetch, try get_by_name next
                logger.debug("fetch not supported by SDK, trying get_by_name")
            except Exception as e:
                logger.debug(f"fetch existence check failed: {str(e)}, trying alternatives")
                
            # Try get_by_name if fetch isn't available
            try:
                if hasattr(self.addresses, 'get_by_name') and callable(getattr(self.addresses, 'get_by_name')):
                    # This will throw ResourceNotFoundError if not found
                    logger.debug(f"Using get_by_name method to check if '{name}' exists")
                    self.addresses.get_by_name(folder=folder, name=name)
                    logger.debug(f"Object '{name}' exists according to get_by_name method")
                    return True
            except ResourceNotFoundError:
                logger.debug(f"Object '{name}' not found using get_by_name method")
                return False
            except (AttributeError, TypeError):
                # SDK doesn't support direct fetch, try alternative
                logger.debug("get_by_name not supported by SDK, trying alternative")
            except Exception as e:
                logger.debug(f"get_by_name existence check failed: {str(e)}, trying alternatives")
            
            # Alternative approach - use a list with small limit and filter
            logger.warning(f"Using inefficient list method to check if '{name}' exists")
            try:
                # Try to use filtered listing - very small limit to minimize data transfer
                addresses = self.addresses.list(folder=folder, limit=5)
                exists = any(addr.name == name for addr in addresses)
                logger.debug(f"Object '{name}' {'exists' if exists else 'does not exist'} according to list method")
                return exists
            except Exception as e:
                logger.debug(f"Filtered list existence check failed: {str(e)}")
                
            # We've tried all methods and failed
            logger.warning(f"All methods to check existence of '{name}' failed")
            return False
            
        except ResourceNotFoundError:
            return False
        except Exception as e:
            logger.warning(f"Error checking if address object exists: {str(e)}")
            # Default to False to let create attempt to proceed
            return False

    @timeit
    def create_address_object(
        self,
        folder: str,
        name: str,
        type_val: str,
        value: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        skip_existence_check: bool = False,
    ) -> AddressObject:
        """Create address object.

        Args:
            folder: Folder to create address object in
            name: Name of address object
            type_val: Type of address object (ip, range, wildcard, fqdn)
            value: Value of address object
            description: Description of address object
            tags: Tags for address object
            skip_existence_check: If True, skip checking if object exists before creating

        Returns:
            Created address object

        Raises:
            ValidationError: If validation fails
            APIError: If API request fails
        """
        try:
            # Check if object exists, but only if not skipping this check
            if not skip_existence_check:
                logger.debug(f"Checking if object '{name}' exists before creating")
                if self.check_address_object_exists(folder, name):
                    raise ValidationError(f"Address object with name '{name}' already exists in folder '{folder}'")
            
            # Create address configuration dictionary
            config = {
                "name": name,
                "folder": folder,
                "description": description,
                "tag": tags or [],
            }
            
            # Add the appropriate field based on address type
            if type_val == "ip":
                config["ip_netmask"] = value
            elif type_val == "range":
                config["ip_range"] = value
            elif type_val == "fqdn":
                config["fqdn"] = value
            else:
                raise ValidationError(f"Invalid address type: {type_val}")
                
            # Create the address object
            created_obj = self.addresses.create(config)
            
            # Convert to our internal AddressObject format
            return AddressObject.from_sdk_object(created_obj)
            
        except ValidationError as e:
            raise ValidationError(f"Invalid address object data: {str(e)}")
        except NameNotUniqueError as e:
            raise ValidationError(f"Address name conflict: {str(e)}")
        except Exception as e:
            raise APIError(f"API error: {str(e)}")

    @timeit
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
            start_time = time.time()
            logger.debug(f"Fetching address object '{name}' from folder '{folder}'")
            
            # Try the most efficient method first - fetch
            try:
                if hasattr(self.addresses, 'fetch') and callable(getattr(self.addresses, 'fetch')):
                    # Use the dedicated fetch method - most efficient
                    logger.debug(f"Using fetch method for '{name}'")
                    address = self.addresses.fetch(folder=folder, name=name)
                    fetch_time = time.time()
                    logger.debug(f"Fetch took {fetch_time - start_time:.3f} seconds")
                    
                    # Convert to our internal AddressObject format
                    result = AddressObject.from_sdk_object(address)
                    convert_time = time.time()
                    logger.debug(f"Converting object took {convert_time - fetch_time:.3f} seconds")
                    
                    return result
                
                # Fall back to get_by_name if fetch not available
                elif hasattr(self.addresses, 'get_by_name') and callable(getattr(self.addresses, 'get_by_name')):
                    # Use direct fetch if available
                    logger.debug(f"Using get_by_name for '{name}'")
                    address = self.addresses.get_by_name(folder=folder, name=name)
                    fetch_time = time.time()
                    logger.debug(f"get_by_name took {fetch_time - start_time:.3f} seconds")
                    
                    # Convert to our internal AddressObject format
                    result = AddressObject.from_sdk_object(address)
                    convert_time = time.time()
                    logger.debug(f"Converting object took {convert_time - fetch_time:.3f} seconds")
                    
                    return result
            except (AttributeError, TypeError):
                # SDK doesn't support these methods, continue with list method
                logger.debug("Direct fetch methods not supported by SDK, falling back to list method")
            except ResourceNotFoundError:
                # Re-raise if not found
                raise ResourceNotFoundError(f"Address object {name} not found in folder {folder}")
            except Exception as e:
                # If we get any other exception during direct fetch, log and continue with list
                logger.debug(f"Direct fetch failed: {str(e)}, falling back to list method")
            
            # Last resort - fallback to list method with a limited number of objects
            logger.warning(f"PERFORMANCE WARNING: Using inefficient list method to find object '{name}'")
            
            # Only request a small number of objects - we only need one that matches
            addresses = self.addresses.list(folder=folder, limit=10)
            list_time = time.time()
            logger.debug(f"Listing objects (limit=10) took {list_time - start_time:.3f} seconds, got {len(addresses)} objects")
            
            # Filter to find the exact match by name
            matching_addresses = [addr for addr in addresses if addr.name == name]
            filter_time = time.time()
            logger.debug(f"Filtering for object '{name}' took {filter_time - list_time:.3f} seconds")
            
            if not matching_addresses:
                raise ResourceNotFoundError(f"Address object {name} not found in folder {folder}")
                
            # Get the first matching address (should be only one with this name)
            address = matching_addresses[0]
            
            # Convert to our internal AddressObject format
            result = AddressObject.from_sdk_object(address)
            convert_time = time.time()
            logger.debug(f"Converting object took {convert_time - filter_time:.3f} seconds")
            
            return result
            
        except ResourceNotFoundError:
            raise ResourceNotFoundError(f"Address object {name} not found in folder {folder}")
        except Exception as e:
            raise APIError(f"API error: {str(e)}")

    @timeit
    def update_address_object(
        self,
        folder: str,
        name: str,
        type_val: str,
        value: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        object_id: Optional[str] = None,
    ) -> AddressObject:
        """Update address object.

        Args:
            folder: Folder containing address object
            name: Name of address object
            type_val: Type of address object (ip, range, wildcard, fqdn)
            value: Value of address object
            description: Description of address object
            tags: Tags for address object
            object_id: Optional object ID - if provided, avoids lookup

        Returns:
            Updated address object

        Raises:
            ResourceNotFoundError: If address object not found
            ValidationError: If validation fails
            APIError: If API request fails
        """
        try:
            start_time = time.time()
            
            # Check if the SDK has update_by_name capability
            update_by_name_supported = hasattr(self.addresses, 'update_by_name') and callable(getattr(self.addresses, 'update_by_name'))
            
            # If we can update by name directly, use that approach
            if update_by_name_supported:
                logger.debug(f"Using direct update_by_name for '{name}'")
                # This is the most efficient path - create config without ID
                config = {
                    "name": name,
                    "folder": folder,
                    "description": description,
                    "tag": tags or [],
                }
                
                # Add the appropriate field based on address type
                if type_val == "ip":
                    config["ip_netmask"] = value
                elif type_val == "range":
                    config["ip_range"] = value
                elif type_val == "fqdn":
                    config["fqdn"] = value
                else:
                    raise ValidationError(f"Invalid address type: {type_val}")
                    
                updated_obj = self.addresses.update_by_name(folder=folder, name=name, config=config)
                update_time = time.time()
                logger.debug(f"Direct update_by_name took {update_time - start_time:.3f} seconds")
                
                return AddressObject.from_sdk_object(updated_obj)
            
            # If we already have the object ID, use that directly without lookup
            if object_id:
                logger.debug(f"Using provided object ID for update: {object_id}")
                config = {
                    "id": object_id,
                    "name": name,
                    "folder": folder,
                    "description": description,
                    "tag": tags or [],
                }
                
                # Add the appropriate field based on address type
                if type_val == "ip":
                    config["ip_netmask"] = value
                elif type_val == "range":
                    config["ip_range"] = value
                elif type_val == "fqdn":
                    config["fqdn"] = value
                else:
                    raise ValidationError(f"Invalid address type: {type_val}")
                    
                updated_obj = self.addresses.update(config)
                update_time = time.time()
                logger.debug(f"Update with provided ID took {update_time - start_time:.3f} seconds")
                
                return AddressObject.from_sdk_object(updated_obj)
            
            # We need to lookup the object first to get its ID
            logger.debug(f"Need to look up object ID first - less efficient path")
            
            # If we have a faster method to get just the ID, use that
            # First try direct REST API call if supported
            try:
                if hasattr(self.addresses, 'get_id_by_name') and callable(getattr(self.addresses, 'get_id_by_name')):
                    object_id = self.addresses.get_id_by_name(folder=folder, name=name)
                    logger.debug(f"Got object ID using direct method: {object_id}")
                else:
                    # Need to get the full object
                    existing = self.get_address_object(folder, name)
                    object_id = existing.id
                    logger.debug(f"Got object ID from full object: {object_id}")
            except Exception as e:
                logger.warning(f"Error getting object ID: {str(e)}, falling back to full object lookup")
                # Fall back to full object lookup if any errors
                existing = self.get_address_object(folder, name)
                object_id = existing.id
                
                if not object_id:
                    raise ResourceNotFoundError(f"Address object {name} has no ID")
                
            get_time = time.time()
            logger.debug(f"Getting object ID took {get_time - start_time:.3f} seconds")
            
            # Create address configuration dictionary
            config = {
                "id": object_id,
                "name": name,
                "folder": folder,
            }
            
            # Only add description if provided
            if description is not None:
                config["description"] = description
            
            # Only add tags if provided
            if tags is not None:
                config["tag"] = tags
            
            # Add the appropriate field based on address type
            if type_val == "ip":
                config["ip_netmask"] = value
            elif type_val == "range":
                config["ip_range"] = value
            elif type_val == "fqdn":
                config["fqdn"] = value
            else:
                raise ValidationError(f"Invalid address type: {type_val}")
                
            # Update the address object
            prep_time = time.time()
            logger.debug(f"Preparing update data took {prep_time - get_time:.3f} seconds")
            
            # Perform the update with error handling
            try:
                updated_obj = self.addresses.update(config)
            except AttributeError as e:
                # If we get model_dump error, the SDK might be expecting a model instead of dict
                if "model_dump" in str(e):
                    logger.debug("SDK expects a model, not a dict. Trying workarounds...")
                    # Try to create a model if possible
                    if hasattr(self.addresses, 'create_model'):
                        model = self.addresses.create_model(config)
                        updated_obj = self.addresses.update(model)
                    else:
                        # Try direct API call
                        if hasattr(self.client, 'put'):
                            api_path = f"/config/object/addresses/{config['id']}"
                            logger.debug(f"Using direct API call to {api_path}")
                            updated_obj = self.client.put(api_path, json=config)
                        else:
                            raise
                else:
                    raise
                    
            update_time = time.time()
            logger.debug(f"API update call took {update_time - prep_time:.3f} seconds")
            
            # Convert to our internal AddressObject format
            result = AddressObject.from_sdk_object(updated_obj)
            convert_time = time.time()
            logger.debug(f"Converting result took {convert_time - update_time:.3f} seconds")
            
            return result
            
        except ResourceNotFoundError:
            raise ResourceNotFoundError(f"Address object {name} not found in folder {folder}")
        except ValidationError as e:
            raise ValidationError(f"Invalid address object data: {str(e)}")
        except Exception as e:
            raise APIError(f"API error: {str(e)}")

    @timeit
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
            # First get the object to get its ID
            address = self.get_address_object(folder, name)
            
            if not address.id:
                raise ResourceNotFoundError(f"Address object {name} has no ID")
                
            # Delete the address object by ID
            self.addresses.delete(address.id)
            
        except ResourceNotFoundError:
            raise ResourceNotFoundError(f"Address object {name} not found in folder {folder}")
        except Exception as e:
            raise APIError(f"API error: {str(e)}")

    @timeit
    def list_address_objects(
        self, 
        folder: str, 
        filter_criteria: Optional[Dict[str, str]] = None
    ) -> List[AddressObject]:
        """List address objects.

        Args:
            folder: Folder to list address objects from
            filter_criteria: Optional filter criteria dictionary
                Examples: 
                    {"name": "web"} - Objects with name containing "web"
                    {"type": "fqdn"} - Objects of type FQDN
                    {"value": "192.168.1"} - Objects with value containing "192.168.1"
                    {"tag": "prod"} - Objects with tag containing "prod"

        Returns:
            List of address objects

        Raises:
            APIError: If API request fails
        """
        try:
            # Start detailed timing for API call
            start_api = time.time()
            
            # Get all address objects in the folder
            logger.debug(f"Fetching address objects from folder '{folder}'")
            addresses = self.addresses.list(folder=folder)
            
            api_end = time.time()
            logger.debug(f"API call to get addresses took {api_end - start_api:.3f} seconds, got {len(addresses)} objects")
            
            # Start timing conversion
            start_convert = time.time()
            
            # Convert SDK objects to our internal format - this could be slow for many objects
            address_objects = [AddressObject.from_sdk_object(addr) for addr in addresses]
            
            convert_end = time.time()
            logger.debug(f"Converting {len(addresses)} address objects took {convert_end - start_convert:.3f} seconds")
            
            # If no filter criteria, return all addresses
            if not filter_criteria:
                return address_objects
                
            # Start timing the filtering process
            start_filter = time.time()
            
            # Apply filters
            filtered_addresses = []
            for address in address_objects:
                match = True
                
                for key, value in filter_criteria.items():
                    if key == "name" and value.lower() not in address.name.lower():
                        match = False
                        break
                    elif key == "type" and value.lower() != address.type.lower():
                        match = False
                        break
                    elif key == "value" and value.lower() not in address.value.lower():
                        match = False
                        break
                    elif key == "tag" and not any(value.lower() in tag.lower() for tag in address.tags):
                        match = False
                        break
                        
                if match:
                    filtered_addresses.append(address)
            
            filter_end = time.time()
            logger.debug(f"Filtering took {filter_end - start_filter:.3f} seconds, reduced from {len(address_objects)} to {len(filtered_addresses)} objects")
                    
            return filtered_addresses
            
        except Exception as e:
            raise APIError(f"API error: {str(e)}")