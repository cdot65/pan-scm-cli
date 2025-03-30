# scm-cli

CLI for Palo Alto Networks Strata Cloud Manager

## Overview

The `scm-cli` tool provides a command-line interface for managing Palo Alto Networks Strata Cloud Manager (SCM) configurations. It is designed for network engineers who prefer a terminal-based workflow.

The CLI follows a consistent command structure:
```
scm-cli <action> <object-type> <object> [options]
```

Where:
- `<action>`: set, delete, or load
- `<object-type>`: objects, network, security, or deployment
- `<object>`: specific object type like address-group, zone, security-rule, or bandwidth-allocation

## Installation

Install from PyPI:

```bash
pip install pan-scm-cli
```

## Development Setup

### Prerequisites

- Python 3.10+ (recommended: 3.12.9)
- Poetry (for dependency management)

### Setting Up Python with pyenv

```bash
# Install pyenv if you don't have it
brew install pyenv

# Install Python 3.12.9
pyenv install 3.12.9

# Set local Python version
echo "3.12.9" > .python-version

# Verify Python version
python --version
```

### Setting Up the Development Environment

```bash
# Clone the repository
git clone https://github.com/your-username/pan-scm-cli.git
cd pan-scm-cli

# Install dependencies with Poetry
poetry install

# Activate the virtual environment
poetry shell
```

## SDK Integration

The `pan-scm-cli` tool is built on top of the `pan-scm-sdk` library, which provides a Python interface to the Palo Alto Networks Strata Cloud Manager API. Here's how the integration works:

### Client Initialization

The SDK client is initialized in `src/scm_cli/utils/sdk_client.py` and implements a singleton pattern to ensure only one client instance is used throughout the application. The client initialization process:

1. Attempts to load credentials from the environment variables or configuration file using dynaconf
2. Initializes the real SDK client with the credentials if they are available
3. Falls back to mock mode if credentials are missing or authentication fails

```python
# Example of how the client is initialized
self.client = Scm(
    client_id=self.client_id,
    client_secret=self.client_secret,
    tsg_id=self.tsg_id,
    log_level=settings.get("log_level", "INFO")
)
```

### Data Modeling and Validation

The CLI uses Pydantic models defined in `src/scm_cli/utils/validators.py` to validate and transform input data before passing it to the SDK:

- `BandwidthAllocation`: For bandwidth allocation configurations
- `AddressGroup`: For address group configurations
- `Zone`: For security zone configurations
- `SecurityRule`: For security rule configurations

Each model implements a `to_sdk_model()` method that transforms the validated data into the format expected by the SDK client.

### Error Handling

The SDK client wrapper implements robust error handling through the `_handle_api_exception` method, which:

1. Catches API exceptions from the SDK
2. Logs appropriate error messages
3. Formats errors for CLI output
4. Provides consistent error handling across all commands

### Mock Mode for Testing

The client implementation includes a mock mode that returns predefined response data instead of making real API calls. This is used:

- When real credentials aren't available
- During testing to avoid external dependencies
- To simulate API responses for development

For example, the mock response for creating a security rule might look like:

```python
return {
    "id": f"sr-{name}",
    "folder": folder,
    "name": name,
    "source_zones": source_zones,
    "destination_zones": destination_zones,
    "action": action,
    "enabled": enabled
}
```

### Command Integration

The CLI commands in `src/scm_cli/commands/` use the SDK client to perform operations:

1. Command parameters are parsed and validated using Typer
2. Data is transformed into the appropriate model using Pydantic validators
3. The SDK client is called with the validated data
4. Results are formatted and displayed to the user

Example command flow:
```
CLI Input → Typer Command → Pydantic Validation → SDK Client → API Call → Formatted Output
```

## Usage Examples

### Creating Objects

```bash
# Create an address group
scm-cli set objects address-group --folder Texas --name test123 --type static --members "['abc', 'xyz']" --description "Test group" --tags "['production', 'test']"

# Create a security zone
scm-cli set network zone --folder Texas --name trust --mode L3 --interfaces "['ethernet1/1']" --description "Trust zone" --tags "['internal']"

# Create a security rule
scm-cli set security security-rule --folder Texas --name allow-web --source-zones "['trust']" --destination-zones "['untrust']" --applications "['web-browsing']" --action allow
```

### Deleting Objects

```bash
# Delete an address group
scm-cli delete objects address-group --folder Texas --name test123

# Delete a security zone
scm-cli delete network zone --folder Texas --name trust

# Delete a security rule
scm-cli delete security security-rule --folder Texas --name allow-web
```

### Loading Objects from YAML Files

```bash
# Load address groups from YAML
scm-cli load objects address-group --file examples/address-groups.yml

# Load security zones from YAML
scm-cli load network zone --file examples/security-zones.yml

# Load security rules from YAML
scm-cli load security security-rule --file examples/security-rules.yml

# Load bandwidth allocations from YAML
scm-cli load deployment bandwidth-allocation --file examples/bandwidth-example.yml
```

You can use the `--dry-run` flag with any load command to preview changes without applying them:

```bash
scm-cli load security security-rule --file examples/security-rules.yml --dry-run
```

## Project Structure

```
pan-scm-cli/
├── src/
│   └── scm_cli/             # Core package
│       ├── __init__.py      # Package initialization
│       ├── main.py          # Entry point and command registration
│       ├── commands/        # Command implementations
│       │   ├── deployment.py
│       │   ├── network.py
│       │   ├── objects.py
│       │   └── security.py
│       └── utils/           # Utility modules
│           ├── config.py
│           ├── sdk_client.py
│           └── validators.py
├── examples/                # Example YAML configurations
├── pyproject.toml          # Project metadata and dependencies
├── poetry.toml             # Poetry configuration
└── .python-version         # Python version specification
```

## License

Copyright (c) 2023 Calvin Remsburg
