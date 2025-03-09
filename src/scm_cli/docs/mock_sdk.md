# mock_sdk.py - Mock SDK Implementation for Testing

## Overview

The `mock_sdk.py` module provides a mock implementation of the Palo Alto Networks SCM SDK for testing purposes. It simulates the behavior of the actual SDK without requiring real API connections, allowing for:

1. Unit testing without external dependencies
2. Development without valid API credentials
3. Testing edge cases and error conditions
4. Consistent and controllable test environments

## Key Components

### AddressObjectType Enum

An enumeration representing the different types of address objects:

```python
class AddressObjectType(str, Enum):
    IP = "ip"
    RANGE = "range"
    WILDCARD = "wildcard"
    FQDN = "fqdn"
```

### AddressObject Class

A mock implementation of an address object:

```python
class AddressObject:
    def __init__(
        self,
        name: str,
        type: AddressObjectType,
        value: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> None:
        # Initialize properties
```

This class includes:
- Properties matching the real SDK's address object
- Methods to convert to/from dictionaries
- Typical address object fields like name, type, value, description, and tags

### Exception Classes

The module defines the same exception classes used by the real SDK:

- `ResourceNotFoundError`: When a requested resource doesn't exist
- `ValidationError`: When data validation fails
- `AuthenticationError`: When authentication fails
- `APIError`: For general API errors

These exceptions ensure that the mock SDK behaves consistently with the real SDK.

### AddressObjectClient Class

A mock client for managing address objects:

```python
class AddressObjectClient:
    def __init__(self) -> None:
        self.storage: Dict[str, Dict[str, AddressObject]] = {}
```

The client includes methods that mimic the real SDK:
- `create()`: Create a new address object
- `get()`: Get an address object by folder and name
- `update()`: Update an existing address object
- `delete()`: Delete an address object
- `list()`: List all address objects in a folder

### Client Class

The main mock client class that mimics the real SCM SDK client:

```python
class Client:
    def __init__(
        self, client_id: str, client_secret: str, tsg_id: str, 
        base_url: str = "https://api.scm.paloaltonetworks.com", 
        verify: bool = True
    ) -> None:
        # Initialize properties
        self.address_objects = AddressObjectClient()
```

The client:
- Accepts the same initialization parameters as the real SDK
- Provides access to the address object client
- Includes a `test_connection()` method to simulate connection testing

## In-Memory Storage

The mock SDK uses in-memory storage to maintain state during tests:

```python
self.storage: Dict[str, Dict[str, AddressObject]] = {}
```

This allows tests to create, update, and delete objects as they would with the real API, but without persistence beyond the test session.

## Validation and Error Handling

The mock SDK includes validation similar to the real SDK:

```python
if not folder or not isinstance(folder, str):
    raise ValidationError("Folder must be a non-empty string")

if address_object.name in self.storage[folder]:
    raise ValidationError(f"Address object {address_object.name} already exists")
```

This ensures that tests can properly handle error conditions and validate input.

## Usage in Tests

This module is designed to be used in tests by substituting it for the real SDK:

```python
# In test code
from unittest.mock import patch

@patch('scm_cli.sdk_client.Scm', MockClient)
def test_address_object_creation():
    # Test implementation
```

It allows tests to:
- Run without real API credentials
- Execute quickly without network delays
- Have consistent, predictable behavior
- Test error handling without causing real API errors

## Differences from Real SDK

While the mock SDK aims to behave similarly to the real SDK, there are some differences:

1. It's much simpler, implementing only the essential functionality
2. It uses in-memory storage rather than making API calls
3. It doesn't implement all the edge cases and complexities of the real API
4. It's focused on the address object functionality only