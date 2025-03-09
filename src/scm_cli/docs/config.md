# config.py - Configuration Module

## Overview

The `config.py` module handles loading and managing configuration for the SCM CLI, focusing primarily on OAuth authentication credentials. It provides:

1. A standardized configuration data structure
2. Environment variable loading from `.env` files
3. Validation and error reporting for missing or invalid credentials
4. Consistent interface for other modules to access configuration

## Key Components

### SCMConfig Dataclass

The `SCMConfig` dataclass represents the CLI's configuration data:

```python
@dataclass
class SCMConfig:
    client_id: str
    client_secret: str
    tsg_id: str
    base_url: str = "https://api.strata.paloaltonetworks.com"
    verify_ssl: bool = True
```

It includes:
- Required OAuth credentials for SCM API authentication
- Optional configuration parameters like base URL and SSL verification

### load_oauth_credentials Function

The `load_oauth_credentials()` function is the main entry point for loading configuration:

```python
def load_oauth_credentials() -> Tuple[bool, Optional[SCMConfig]]:
    # Implementation
```

It performs the following steps:
1. Checks for the existence of a `.env` file
2. Loads variables using python-dotenv
3. Validates required credentials (client_id, client_secret, tsg_id)
4. Reports clear error messages if anything is missing
5. Creates and returns the `SCMConfig` object

## Error Handling

The module uses the Rich console for user-friendly error messages:

```python
console = Console(stderr=True)
# Later in the code:
console.print("[bold red]Error:[/bold red] .env file not found in current directory", style="red")
```

This ensures:
- Errors are clearly displayed to the user
- Missing or invalid configuration is reported with guidance on fixing it
- The application gracefully exits when configuration is invalid

## Return Values

The `load_oauth_credentials()` function returns a tuple with:
1. A boolean success flag
2. The SCMConfig object (if successful) or None (if failed)

This approach allows the caller to easily check if configuration was successful without needing to handle exceptions.

## Usage in Other Modules

This module is primarily used by the `cli.py` module during initialization:

```python
success, config = load_oauth_credentials()
if not success:
    # Error messages already printed by load_oauth_credentials
    sys.exit(1)
```

The SDKClient is then initialized with this configuration.

## Security Considerations

The module follows security best practices by:
- Not hardcoding any credentials
- Loading credentials from a local `.env` file
- Supporting HTTPS and SSL verification
- Not logging sensitive information