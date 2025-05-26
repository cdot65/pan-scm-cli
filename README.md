# Strata Cloud Manager CLI

![Banner Image](https://raw.githubusercontent.com/cdot65/pan-scm-cli/main/docs/images/logo.svg)
[![Build Status](https://github.com/cdot65/pan-scm-cli/actions/workflows/code-quality.yml/badge.svg)](https://github.com/cdot65/pan-scm-cli/actions/workflows/code-quality.yml)
[![PyPI version](https://badge.fury.io/py/pan-scm-cli.svg)](https://badge.fury.io/py/pan-scm-cli)
[![Python versions](https://img.shields.io/pypi/pyversions/pan-scm-cli.svg)](https://pypi.org/project/pan-scm-cli/)
[![License](https://img.shields.io/github/license/cdot65/pan-scm-cli.svg)](https://github.com/cdot65/pan-scm-cli/blob/main/LICENSE)

A powerful command-line interface for managing Palo Alto Networks Strata Cloud Manager configurations. Built on the [pan-scm-sdk](https://github.com/cdot65/pan-scm-sdk), this tool provides network engineers with a consistent, user-friendly CLI experience for automating and managing SCM resources.

> **NOTE**: Please refer to the [GitHub Pages documentation site](https://cdot65.github.io/pan-scm-cli/) for all
> examples

## Table of Contents

- [Strata Cloud Manager CLI](#strata-cloud-manager-cli)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Authentication](#authentication)
      - [Method 1: Environment Variables (Highest Priority)](#method-1-environment-variables-highest-priority)
      - [Method 2: Config File in Home Directory](#method-2-config-file-in-home-directory)
      - [Method 3: Local Project Configuration (Development)](#method-3-local-project-configuration-development)
      - [Verifying Authentication](#verifying-authentication)
    - [Command Structure](#command-structure)
    - [Example Commands](#example-commands)
      - [Managing Address Objects](#managing-address-objects)
      - [Managing Address Groups](#managing-address-groups)
      - [Managing Security Zones](#managing-security-zones)
      - [Managing Security Rules](#managing-security-rules)
      - [Managing Bandwidth Allocations](#managing-bandwidth-allocations)
      - [Bulk Operations](#bulk-operations)
  - [Development](#development)
    - [Setup](#setup)
    - [Code Quality](#code-quality)
    - [Pre-commit Hooks](#pre-commit-hooks)
  - [Contributing](#contributing)
  - [License](#license)
  - [Support](#support)
  - [Project Status](#project-status)

## Features

- **Consistent Command Structure**: Intuitive command pattern that follows standard CLI conventions.
- **Comprehensive Object Management**: Create, read, update, and delete configuration objects including:
  - Address objects (IP/netmask, FQDN, IP range, wildcard)
  - Address groups (static and dynamic)
  - Applications (custom application definitions with security attributes)
  - Application groups (logical grouping of applications)
  - Application filters (dynamic application selection based on criteria)
  - Dynamic user groups (tag-based user grouping)
  - External dynamic lists (EDLs for threat intelligence integration)
  - HIP objects (Host Information Profiles for endpoint compliance)
  - HIP profiles (HIP object combinations for policy enforcement)
  - HTTP server profiles (Log forwarding and integration configurations)
  - Security zones (layer3, layer2, virtual-wire, tap modes)
  - Security rules with full policy configuration
  - Bandwidth allocation profiles
- **Bulk Operations**: Load and manage objects in bulk using YAML files for efficient configuration management.
- **Backup and Restore**: Export existing configurations to YAML files and restore them later:
- **Mock Mode**: Test commands without making actual API calls, perfect for validation and development.
- **Flexible Authentication**: Multiple authentication methods with automatic fallback:
  - Environment variables (production-ready)
  - Home directory config (~/.scm-cli/config.yaml)
  - Local development config (.secrets.yaml)
- **Input Validation**: Built-in Pydantic validation ensures data integrity before API calls.
- **Comprehensive Error Handling**: Clear, actionable error messages with detailed logging options.
- **Extensive Documentation**: Full MkDocs-based documentation with interactive CLI examples.

## Installation

**Requirements**:

- Python 3.10 or higher

Install the package via pip:

```bash
pip install pan-scm-cli
```

## Usage

### Authentication

The SCM CLI uses dynaconf to manage authentication credentials. Configure authentication using one of the following methods (in order of precedence):

#### Method 1: Environment Variables (Highest Priority)

For production use or scripting, set environment variables:

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

These environment variables will be automatically detected and used with highest priority.

#### Method 2: Config File in Home Directory

For a more permanent configuration, create a config file in your home directory:

```bash
# Create the config directory if it doesn't exist
mkdir -p ~/.scm-cli

# Create and edit the config file
cat > ~/.scm-cli/config.yaml << EOL
client_id: "your_client_id"
client_secret: "your_client_secret"
tsg_id: "your_tenant_service_group_id"
EOL

# Secure the file with restrictive permissions
chmod 600 ~/.scm-cli/config.yaml
```

This method is used when environment variables are not set.

#### Method 3: Local Project Configuration (Development)

> **⚠️ SECURITY WARNING**
>
> Storage of credentials in project files poses security risks. Consider these best practices:
>
> - **NEVER commit credential files to version control**
> - **Use environment variables for production environments**
> - **Protect local credential files with appropriate file permissions**
> - **Regularly rotate your credentials**

For local development, follow these steps:

1. Copy the example configuration file to create a local secrets file:

   ```bash
   cp example-config.yaml .secrets.yaml
   ```

2. Edit the `.secrets.yaml` file with your actual credentials:

   ```yaml
   default:
     scm_client_id: "your_client_id"
     scm_client_secret: "your_client_secret"
     scm_tsg_id: "your_tenant_service_group_id"
   ```

3. Secure the file with restrictive permissions:

   ```bash
   # On Linux/macOS
   chmod 600 .secrets.yaml
   ```

> **Note**: The `.secrets.yaml` file is excluded from version control in `.gitignore` to prevent accidental exposure of credentials.

#### Verifying Authentication

To verify your authentication configuration:

```bash
# Test with actual credentials
scm-cli test-auth

# Test in mock mode (doesn't require real credentials)
scm-cli test-auth --mock
```

### Command Structure

The CLI follows a consistent command pattern:

```bash
scm-cli <action> <object-type> <object> [options]
```

Where:

- `<action>`: Operation to perform
  - `set`: Create or update an object
  - `delete`: Remove an object
  - `load`: Bulk import from YAML file
  - `show`: Display existing objects
  - `backup`: Export configurations to YAML file
  - `test-auth`: Verify authentication configuration
- `<object-type>`: Resource category
  - `objects`: Address objects and address groups
  - `network`: Security zones
  - `security`: Security rules
  - `deployment`: Bandwidth allocations
- `<object>`: Specific resource type (e.g., `address`, `address-group`, `security-zone`, `rule`, `bandwidth`)

Global options available for all commands:

- `--mock`: Run in mock mode without API calls
- `--folder`: Specify the folder location (default: "Shared")
- `--list`: List all objects of the specified type

### Example Commands

#### Managing Address Objects

```bash
# Create a new address object
scm-cli set objects address --folder Shared --name web-server --ip-netmask 192.168.1.100/32 --description "Web server in DMZ"

# List all address objects in a folder
scm-cli show objects address --folder Shared --list

# Show a specific address object
scm-cli show objects address --folder Shared --name web-server

# Delete an address object
scm-cli delete objects address --folder Shared --name web-server
```

#### Managing Address Groups

```bash
# Create a static address group
scm-cli set objects address-group --folder Shared --name web-servers --type static --members "web-server-1,web-server-2"

# Create a dynamic address group
scm-cli set objects address-group --folder Shared --name dynamic-endpoints --type dynamic --filter "'endpoint' and 'corporate'"

# List all address groups in a folder
scm-cli show objects address-group --folder Shared --list

# Show a specific address group
scm-cli show objects address-group --folder Shared --name web-servers

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

#### Managing Bandwidth Allocations

```bash
# Create a bandwidth allocation profile
scm-cli set deployment bandwidth --folder Shared --name "Branch-100Mbps" \
  --egress-guaranteed 50 --egress-burstable 100

# List all bandwidth profiles
scm-cli set deployment bandwidth --list --folder Shared
```

#### Managing Applications

```bash
# Create a custom application
scm-cli set objects application --folder Shared --name custom-app \
  --category business-systems --subcategory database \
  --technology client-server --risk 3 \
  --ports "tcp/8080,tcp/8443" --description "Custom business application"

# List all applications
scm-cli show objects application --folder Shared --list

# Show specific application details
scm-cli show objects application --folder Shared --name custom-app
```

#### Managing Application Groups

```bash
# Create an application group
scm-cli set objects application-group --folder Shared --name business-apps \
  --members "salesforce,ms-365,custom-app"

# List all application groups
scm-cli show objects application-group --folder Shared --list
```

#### Managing Application Filters

```bash
# Create an application filter for high-risk apps
scm-cli set objects application-filter --folder Shared --name high-risk-filter \
  --category "file-sharing,peer-to-peer" --risk 4 --risk 5 \
  --has-known-vulnerabilities --transfers-files

# List all application filters
scm-cli show objects application-filter --folder Shared --list
```

#### Managing Dynamic User Groups

```bash
# Create a dynamic user group based on tags
scm-cli set objects dynamic-user-group --folder Shared --name it-admins \
  --filter "'IT' and 'Admin'" --description "IT administrators group"

# List all dynamic user groups
scm-cli show objects dynamic-user-group --folder Shared --list
```

#### Managing External Dynamic Lists

```bash
# Create a predefined IP blocklist
scm-cli set objects external-dynamic-list --folder Shared \
  --name paloalto-bulletproof --type predefined_ip \
  --url "panw-bulletproof-ip-list"

# Create a custom IP blocklist with hourly updates
scm-cli set objects external-dynamic-list --folder Shared \
  --name custom-threats --type ip \
  --url "https://example.com/threats.txt" --recurring hourly

# List all external dynamic lists
scm-cli show objects external-dynamic-list --folder Shared --list
```

#### Managing HIP Objects

```bash
# Create a HIP object for Windows patch management
scm-cli set objects hip-object --folder Shared --name windows-security-compliance \
  --description "Windows security compliance check" \
  --patch-management-vendor-name "Microsoft Corporation" \
  --patch-management-product-name "Windows" \
  --patch-management-criteria-is-installed yes \
  --patch-management-missing-patches check-not-exist

# Create a HIP object for disk encryption
scm-cli set objects hip-object --folder Shared --name disk-encryption-check \
  --disk-encryption-vendor-name "BitLocker" \
  --disk-encryption-product-name "BitLocker Drive Encryption" \
  --disk-encryption-criteria-is-installed is \
  --disk-encryption-state is

# List all HIP objects
scm-cli show objects hip-object --folder Shared --list

# Show specific HIP object details
scm-cli show objects hip-object --folder Shared --name windows-security-compliance
```

#### Managing HIP Profiles

```bash
# Create a HIP profile with multiple match criteria
scm-cli set objects hip-profile --folder Shared --name secure-endpoints \
  --match '{"windows-security-compliance": {"is": true}, "disk-encryption-check": {"is": true}}' \
  --description "Profile for fully compliant Windows endpoints"

# List all HIP profiles
scm-cli show objects hip-profile --folder Shared --list

# Show specific HIP profile details
scm-cli show objects hip-profile --folder Shared --name secure-endpoints
```

#### Managing HTTP Server Profiles

```bash
# Create an HTTP server profile for syslog forwarding
scm-cli set objects http-server-profile --folder Shared --name syslog-collector \
  --servers '[{"name": "primary-syslog", "address": "syslog.example.com", "protocol": "HTTPS", "port": 443, "http_method": "POST"}]' \
  --description "Primary syslog collector"

# Create an HTTP server profile with authentication
scm-cli set objects http-server-profile --folder Shared --name splunk-hec \
  --servers '[{"name": "splunk-server", "address": "10.0.1.100", "protocol": "HTTPS", "port": 8088, "http_method": "POST", "username": "hec_user", "password": "secure_token"}]'

# List all HTTP server profiles
scm-cli show objects http-server-profile --folder Shared --list
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

  - name: db-server
    description: "Database server"
    fqdn: db.example.com
    tags:
      - database
      - production
```

Load the objects:

```bash
scm-cli load objects address --folder Shared --file addresses.yml

# Verify in mock mode first
scm-cli load objects address --folder Shared --file addresses.yml --mock
```

See the `examples/` directory for more bulk operation templates, including:

- Complete RFC 1918 private network setup (`rfc1918-addresses.yml` and `rfc1918-address-group.yml`)
- Multi-folder configuration examples across ngfw-shared, Texas, and Austin folders
- Security zone configurations for different network modes
- Pre and post rulebase security rule examples
- Application definitions with security attributes (`applications.yml`)
- Application group configurations (`application-groups.yml`)
- Application filter criteria (`application-filters.yml`)
- Dynamic user group filter expressions (`dynamic-user-groups.yml`)
- External dynamic list configurations for all EDL types (`external-dynamic-lists.yml`)
- HIP object configurations for endpoint compliance (`hip-objects.yml`)
- HIP profile configurations for policy enforcement (`hip-profiles.yml`)
- HTTP server profile configurations for log forwarding (`http-server-profiles.yml`)

#### Backup and Restore Operations

Export existing configurations to YAML files:

```bash
# Backup address objects from a specific folder
scm-cli backup objects address --folder Austin
# Creates: address-austin.yaml

# Backup address groups
scm-cli backup objects address-group --folder Texas
# Creates: address-group-texas.yaml

# Backup security zones
scm-cli backup network security-zone --folder ngfw-shared
# Creates: security-zone-ngfw-shared.yaml

# Backup security rules
scm-cli backup security rule --folder Austin --rulebase pre
# Creates: rule-austin-pre.yaml

# Backup bandwidth allocations
scm-cli backup deployment bandwidth-allocation
# Creates: bandwidth-allocations.yaml

# Backup applications
scm-cli backup objects application --folder Texas
# Creates: application-texas.yaml

# Backup application groups
scm-cli backup objects application-group --folder Texas
# Creates: application-group-texas.yaml

# Backup application filters
scm-cli backup objects application-filter --folder Texas
# Creates: application-filter-texas.yaml

# Backup dynamic user groups
scm-cli backup objects dynamic-user-group --folder Texas
# Creates: dynamic-user-group-texas.yaml

# Backup external dynamic lists
scm-cli backup objects external-dynamic-list --folder Texas
# Creates: external-dynamic-list-texas.yaml

# Backup HIP objects
scm-cli backup objects hip-object --folder Texas
# Creates: hip-object-texas.yaml

# Backup HIP profiles
scm-cli backup objects hip-profile --folder Texas
# Creates: hip-profile-texas.yaml

# Backup HTTP server profiles
scm-cli backup objects http-server-profile --folder Texas
# Creates: http-server-profile-texas.yaml
```

Restore configurations from backup files:

```bash
# Restore addresses (preview first with --dry-run)
scm-cli load objects address --file address-austin.yaml --dry-run
scm-cli load objects address --file address-austin.yaml

# Restore address groups
scm-cli load objects address-group --file address-group-texas.yaml

# Restore security zones
scm-cli load network security-zone --file security-zone-ngfw-shared.yaml

# Restore security rules
scm-cli load security rule --file rule-austin-pre.yaml

# Restore bandwidth allocations
scm-cli load deployment bandwidth-allocation --file bandwidth-allocations.yaml
```

The backup feature uses the `exact_match=True` parameter to only export objects that are directly defined in the specified folder, excluding inherited objects from parent folders.

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

This project uses [ruff](https://github.com/astral-sh/ruff) for linting and formatting, along with comprehensive quality checks:

```bash
# Run all quality checks (lint, format, type checking, tests)
make quality

# Individual checks
make lint               # Run flake8 and yamllint
make format             # Format code with ruff
make fix                # Auto-fix linting issues with ruff

# Testing
make tests              # Run the full test suite
pytest -v               # Run tests with verbose output
pytest -k "test_name"   # Run specific tests by pattern
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
3. Make your changes, ensuring all quality checks pass:

   ```bash
   make quality  # Run all checks
   ```

4. Add tests for new functionality in the `tests/` directory.
5. Update documentation if adding new features.
6. Commit your changes (`git commit -m 'Add new feature'`).
7. Push to your branch (`git push origin feature/your-feature`).
8. Open a Pull Request.

Ensure your code adheres to the project's coding standards and includes tests where appropriate. See [CONTRIBUTING.md](./docs/about/contributing.md) for detailed guidelines.

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](./LICENSE) file for details.

## Support

- **Documentation**: [GitHub Pages site](https://cdot65.github.io/pan-scm-cli/)
- **Issues**: [GitHub Issues](https://github.com/cdot65/pan-scm-cli/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cdot65/pan-scm-cli/discussions)
- **Examples**: See the `examples/` directory for configuration templates

## Project Status

This project is actively maintained and uses:

- Python 3.12+ with Poetry for dependency management
- pan-scm-sdk v0.3.39 for API interactions
- Dynaconf for flexible configuration management
- Pydantic for robust input validation
- Comprehensive test coverage with pytest

---

_Detailed documentation is available on our [GitHub Pages documentation site](https://cdot65.github.io/pan-scm-cli/)._
