# Strata Cloud Manager CLI

![Banner Image](https://raw.githubusercontent.com/cdot65/pan-scm-cli/main/docs/images/logo.svg)
[![Build Status](https://github.com/cdot65/pan-scm-cli/actions/workflows/code-quality.yml/badge.svg)](https://github.com/cdot65/pan-scm-cli/actions/workflows/code-quality.yml)
[![PyPI version](https://badge.fury.io/py/pan-scm-cli.svg)](https://badge.fury.io/py/pan-scm-cli)
[![Python versions](https://img.shields.io/pypi/pyversions/pan-scm-cli.svg)](https://pypi.org/project/pan-scm-cli/)
[![License](https://img.shields.io/github/license/cdot65/pan-scm-cli.svg)](https://github.com/cdot65/pan-scm-cli/blob/main/LICENSE)

Command-line interface for Palo Alto Networks Strata Cloud Manager.

> **NOTE**: Please refer to the [GitHub Pages documentation site](https://cdot65.github.io/pan-scm-cli/) for all
> examples

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
    - [Authentication](#authentication)
    - [Command Structure](#command-structure)
    - [Example Commands](#example-commands)
- [Development](#development)
    - [Setup](#setup)
    - [Code Quality](#code-quality)
    - [Pre-commit Hooks](#pre-commit-hooks)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

## Features

- **Consistent Command Structure**: Intuitive command pattern that follows standard CLI conventions.
- **Comprehensive Object Management**: Create, read, update, and delete configuration objects like addresses, address groups, security zones, and security rules.
- **Bulk Operations**: Load and manage objects in bulk using YAML files.
- **Mock Mode**: Test commands without making actual API calls to validate configurations.
- **Authentication Management**: Multiple authentication methods including environment variables and configuration files.
- **Extensive Documentation**: Comprehensive examples for all supported operations.

## Installation

**Requirements**:

- Python 3.10 or higher

Install the package via pip:

```bash
pip install pan-scm-cli
```

## Usage

### Authentication

Configure authentication using one of the following methods:

#### Environment Variables

```bash
# Linux/macOS
export SCM_CLIENT_ID="your_client_id"
export SCM_CLIENT_SECRET="your_client_secret"
export SCM_TSG_ID="your_tenant_service_group_id"

# Windows PowerShell
$env:SCM_CLIENT_ID = "your_client_id"
$env:SCM_CLIENT_SECRET = "your_client_secret"
$env:SCM_TSG_ID = "your_tenant_service_group_id"
```

#### Configuration File

Create a config file at `~/.scm-cli/config.yaml`:

```yaml
client_id: "your_client_id"
client_secret: "your_client_secret"
tsg_id: "your_tenant_service_group_id"
```

### Command Structure

The CLI follows a consistent command pattern:

```
scm-cli <action> <object-type> <object> [options]
```

Where:
- `<action>`: `set`, `delete`, or `load`
- `<object-type>`: `objects`, `network`, `security`, or `deployment`
- `<object>`: Specific object type (e.g., `address`, `address-group`, `security-zone`)

### Example Commands

#### Managing Address Objects

```bash
# Create a new address object
scm-cli set objects address --folder Shared --name web-server --ip-netmask 192.168.1.100/32 --description "Web server in DMZ"

# List all address objects in a folder
scm-cli set objects address --list --folder Shared

# Delete an address object
scm-cli delete objects address --folder Shared --name web-server
```

#### Managing Address Groups

```bash
# Create a static address group
scm-cli set objects address-group --folder Shared --name web-servers --type static --members "web-server-1,web-server-2"

# Create a dynamic address group
scm-cli set objects address-group --folder Shared --name dynamic-endpoints --type dynamic --filter "'endpoint' and 'corporate'"

# Delete an address group
scm-cli delete objects address-group --folder Shared --name web-servers
```

#### Managing Security Zones

```bash
# Create a security zone
scm-cli set network security-zone --folder Shared --name DMZ --mode layer3 --enable-user-id true

# List all security zones
scm-cli set network security-zone --list --folder Shared
```

#### Managing Security Rules

```bash
# Create a security rule
scm-cli set security rule --folder Shared --name "Allow-Web" \
  --source-zones "Trust" --destination-zones "DMZ" \
  --source-addresses "any" --destination-addresses "web-servers" \
  --applications "web-browsing,ssl" --services "application-default" \
  --action allow --log-end true

# List all security rules
scm-cli set security rule --list --folder Shared
```

#### Bulk Operations

Create a YAML file with multiple objects:

```yaml
# addresses.yaml
addresses:
  - name: web-server-1
    description: "Web server 1"
    ip_netmask: 192.168.1.100/32
    tags:
      - web
      - production

  - name: web-server-2
    description: "Web server 2"
    ip_netmask: 192.168.1.101/32
    tags:
      - web
      - production
```

Load the objects:

```bash
scm-cli load objects address --folder Shared --file addresses.yaml
```

## Development

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/cdot65/pan-scm-cli.git
   cd pan-scm-cli
   ```

2. Install dependencies and pre-commit hooks:
   ```bash
   make setup
   ```

   Alternatively, you can install manually:
   ```bash
   poetry install
   poetry run pre-commit install
   ```

### Code Quality

This project uses [ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Run linting checks
make lint

# Format code
make format

# Auto-fix linting issues when possible
make fix
```

### Pre-commit Hooks

We use pre-commit hooks to ensure code quality before committing:

```bash
# Run pre-commit hooks on all files
make pre-commit-all
```

The following checks run automatically before each commit:
- ruff linting and formatting
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON syntax checking
- Large file detection
- Python syntax validation
- Merge conflict detection
- Private key detection

## Contributing

We welcome contributions! To contribute:

1. Fork the repository.
2. Create a new feature branch (`git checkout -b feature/your-feature`).
3. Make your changes, ensuring all linting and tests pass.
4. Commit your changes (`git commit -m 'Add new feature'`).
5. Push to your branch (`git push origin feature/your-feature`).
6. Open a Pull Request.

Ensure your code adheres to the project's coding standards and includes tests where appropriate.

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](./LICENSE) file for details.

## Support

For support and questions, please refer to the [SUPPORT.md](./SUPPORT.md) file in this repository.

---

*Detailed documentation is available on our [GitHub Pages documentation site](https://cdot65.github.io/pan-scm-cli/).*
