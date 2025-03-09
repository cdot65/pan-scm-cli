# sdk_client.py - SCM SDK Client Module

## Overview

The `sdk_client.py` module provides a flexible abstraction layer between the CLI and the Palo Alto Networks SCM SDK. It's designed to handle the complexities of the underlying API, providing a consistent interface for the CLI regardless of SDK version or behavior changes.

Key responsibilities:
1. Initializing and maintaining the SDK connection
2. Providing CRUD operations for address objects
3. Handling API errors and exceptions
4. Abstracting SDK model differences and versions
5. Performance tracking

## Key Components

### SDKClient Class

The `SDKClient` class is the main interface to the SCM SDK, handling:

- Connection establishment with OAuth credentials
- API operation execution
- Error handling and standardization

```python
class SDKClient:
    def __init__(self, config: SCMConfig) -> None:
        self.config = config
        self.client = Scm(
            client_id=config.client_id,
            client_secret=config.client_secret,
            tsg_id=config.tsg_id,
            log_level="INFO",
        )
        self.addresses = Address(self.client)
```

Key methods include:
- `test_connection()`: Verify API connectivity
- CRUD operations for address objects:
  - `create_address_object()`
  - `get_address_object()`
  - `update_address_object()`
  - `delete_address_object()`
  - `list_address_objects()`
- Optimized direct operations:
  - `direct_fetch_address_object()`
  - `direct_create_address_object()`
  - `direct_update_address_object()`

### AddressObject Adapter Class

The `AddressObject` class serves as an adapter between the CLI layer and the SDK models:

```python
class AddressObject:
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
        # Initialize properties
```

It provides:
- Consistent representation of address objects
- Conversion between SDK and CLI data formats
- Type mapping between CLI types (like `ip-netmask`) and SDK types (like `ip`)
- Serialization and deserialization methods

### SDK Model Compatibility

The module handles different SDK versions with a flexible approach:

1. Attempts to import models from different possible locations:
   ```python
   try:
       from scm.models.objects import (
           AddressCreateModel, AddressUpdateModel, AddressResponseModel
       )
       HAS_NEW_MODELS = True
   except ImportError:
       # Try alternative imports
   ```

2. Provides compatibility methods that adapt to available models:
   ```python
   def to_sdk_model(self) -> Any:
       # Create appropriate model based on what's available
       if HAS_NEW_MODELS:
           # Use new model classes
       elif HAS_MODELS:
           # Use legacy model classes
       else:
           # Fall back to dictionary approach
   ```

### Performance Monitoring

The module implements the `@timeit` decorator to track API call performance:

```python
@timeit
def get_address_object(self, folder: str, name: str) -> AddressObject:
    # Method implementation with performance tracking
```

This provides:
- Detailed timing information for operations
- Warnings for slow operations
- Debugging insights for performance optimization

## Exception Handling

The module defines and uses standardized exceptions:

- `ValidationError`: For data validation failures
- `ResourceNotFoundError`: When requested resources don't exist
- `APIError`: For general API communication errors

These are used consistently throughout the module to provide clear error information.

## Optimization Strategies

The module implements several strategies to optimize API performance:

1. **Direct Fetch**: Using SDK-specific optimized methods when available
   ```python
   if hasattr(self.addresses, 'fetch') and callable(getattr(self.addresses, 'fetch')):
       obj = self.addresses.fetch(folder=folder, name=name)
   ```

2. **Fallback Methods**: Gracefully degrading to alternative approaches if preferred methods aren't available
   ```python
   # Try multiple methods with fallbacks
   try:
       # Try direct fetch first
   except (AttributeError, TypeError):
       # Try alternative method
   except Exception:
       # Fall back to list method
   ```

3. **Caching**: Reusing object IDs when possible to avoid repeated lookups

4. **Partial Updates**: Supporting updates of specific fields without retrieving or sending the entire object

## Debugging Support

The module includes extensive logging for debugging:

```python
logger.debug(f"API call to direct_fetch_address_object for '{args.name}' took {api_end_time - api_start_time:.3f} seconds")
```

This helps identify:
- Slow API calls
- Failed operations
- SDK compatibility issues
- Model serialization problems