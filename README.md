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
