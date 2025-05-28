# Strata Cloud Manager CLI

![Banner Image](https://raw.githubusercontent.com/cdot65/pan-scm/main/docs/images/logo.svg)
[![Build Status](https://github.com/cdot65/pan-scm/actions/workflows/code-quality.yml/badge.svg)](https://github.com/cdot65/pan-scm/actions/workflows/code-quality.yml)
[![PyPI version](https://badge.fury.io/py/pan-scm.svg)](https://badge.fury.io/py/pan-scm)
[![Python versions](https://img.shields.io/pypi/pyversions/pan-scm.svg)](https://pypi.org/project/pan-scm/)
[![License](https://img.shields.io/github/license/cdot65/pan-scm.svg)](https://github.com/cdot65/pan-scm/blob/main/LICENSE)

A powerful command-line interface for managing Palo Alto Networks Strata Cloud Manager configurations. Built on the [pan-scm-sdk](https://github.com/cdot65/pan-scm-sdk), this tool provides network engineers with a consistent, user-friendly CLI experience for automating and managing SCM resources.

> **NOTE**: Please refer to the [GitHub Pages documentation site](https://cdot65.github.io/pan-scm/) for all
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
  - Services (Network service definitions with protocol and port configurations)
  - Service groups (Logical grouping of services for policy management)
  - Syslog server profiles (External syslog server configurations for log forwarding)
  - Tags (Organizational labels with color categorization)
  - Security zones (layer3, layer2, virtual-wire, tap modes)
  - Security rules with full policy configuration
  - Bandwidth allocation profiles
- **Bulk Operations**: Load and manage objects in bulk using YAML files for efficient configuration management:
  - Container override support for all load commands (folder/snippet/device)
  - Migrate objects between locations during import
  - Dry run mode to preview changes before applying
- **Backup and Restore**: Export existing configurations to YAML files and restore them later:
  - Support for all container types (folder, snippet, device)
  - Automatic filename generation with timestamps
  - Exact match filtering to backup only direct objects
- **Mock Mode**: Test commands without making actual API calls, perfect for validation and development.
- **Flexible Authentication**: Multiple authentication methods with automatic fallback:
  - Environment variables (production-ready)
  - Home directory config (~/.scm/config.yaml)
  - Local development config (.secrets.yaml)
- **Input Validation**: Built-in Pydantic validation ensures data integrity before API calls.
- **Comprehensive Error Handling**: Clear, actionable error messages with detailed logging options.
- **Extensive Documentation**: Full MkDocs-based documentation with interactive CLI examples.

## Installation

**Requirements**:

- Python 3.10 or higher

Install the package via pip:

```bash
pip install pan-scm
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
mkdir -p ~/.scm

# Create and edit the config file
cat > ~/.scm/config.yaml << EOL
client_id: "your_client_id"
client_secret: "your_client_secret"
tsg_id: "your_tenant_service_group_id"
EOL

# Secure the file with restrictive permissions
chmod 600 ~/.scm/config.yaml
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
scm test-auth

# Test in mock mode (doesn't require real credentials)
scm test-auth --mock
```

### Command Structure

The CLI follows a consistent command pattern:

```bash
scm <action> <object-type> <object> [options]
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
scm set objects address --folder Shared --name web-server --ip-netmask 192.168.1.100/32 --description "Web server in DMZ"

# List all address objects in a folder
scm show objects address --folder Shared --list

# Show a specific address object
scm show objects address --folder Shared --name web-server

# Delete an address object
scm delete objects address --folder Shared --name web-server
```

#### Managing Address Groups

```bash
# Create a static address group
scm set objects address-group --folder Shared --name web-servers --type static --members "web-server-1,web-server-2"

# Create a dynamic address group
scm set objects address-group --folder Shared --name dynamic-endpoints --type dynamic --filter "'endpoint' and 'corporate'"

# List all address groups in a folder
scm show objects address-group --folder Shared --list

# Show a specific address group
scm show objects address-group --folder Shared --name web-servers

# Delete an address group
scm delete objects address-group --folder Shared --name web-servers
```

#### Managing Security Zones

```bash
# Create a security zone
scm set network security-zone --folder Shared --name DMZ --mode layer3 --enable-user-id true

# List all security zones
scm set network security-zone --list --folder Shared
```

#### Managing Security Rules

```bash
# Create a security rule
scm set security rule --folder Shared --name "Allow-Web" \
  --source-zones "Trust" --destination-zones "DMZ" \
  --source-addresses "any" --destination-addresses "web-servers" \
  --applications "web-browsing,ssl" --services "application-default" \
  --action allow --log-end true

# List all security rules
scm set security rule --list --folder Shared
```

#### Managing Bandwidth Allocations

```bash
# Create a bandwidth allocation profile
scm set deployment bandwidth --folder Shared --name "Branch-100Mbps" \
  --egress-guaranteed 50 --egress-burstable 100

# List all bandwidth profiles
scm set deployment bandwidth --list --folder Shared
```

#### Managing Applications

```bash
# Create a custom application
scm set objects application --folder Shared --name custom-app \
  --category business-systems --subcategory database \
  --technology client-server --risk 3 \
  --ports "tcp/8080,tcp/8443" --description "Custom business application"

# List all applications
scm show objects application --folder Shared --list

# Show specific application details
scm show objects application --folder Shared --name custom-app
```

#### Managing Application Groups

```bash
# Create an application group
scm set objects application-group --folder Shared --name business-apps \
  --members "salesforce,ms-365,custom-app"

# List all application groups
scm show objects application-group --folder Shared --list
```

#### Managing Application Filters

```bash
# Create an application filter for high-risk apps
scm set objects application-filter --folder Shared --name high-risk-filter \
  --category "file-sharing,peer-to-peer" --risk 4 --risk 5 \
  --has-known-vulnerabilities --transfers-files

# List all application filters
scm show objects application-filter --folder Shared --list
```

#### Managing Dynamic User Groups

```bash
# Create a dynamic user group based on tags
scm set objects dynamic-user-group --folder Shared --name it-admins \
  --filter "'IT' and 'Admin'" --description "IT administrators group"

# List all dynamic user groups
scm show objects dynamic-user-group --folder Shared --list
```

#### Managing External Dynamic Lists

```bash
# Create a predefined IP blocklist
scm set objects external-dynamic-list --folder Shared \
  --name paloalto-bulletproof --type predefined_ip \
  --url "panw-bulletproof-ip-list"

# Create a custom IP blocklist with hourly updates
scm set objects external-dynamic-list --folder Shared \
  --name custom-threats --type ip \
  --url "https://example.com/threats.txt" --recurring hourly

# List all external dynamic lists
scm show objects external-dynamic-list --folder Shared --list
```

#### Managing HIP Objects

```bash
# Create a HIP object for Windows patch management
scm set objects hip-object --folder Shared --name windows-security-compliance \
  --description "Windows security compliance check" \
  --patch-management-vendor-name "Microsoft Corporation" \
  --patch-management-product-name "Windows" \
  --patch-management-criteria-is-installed yes \
  --patch-management-missing-patches check-not-exist

# Create a HIP object for disk encryption
scm set objects hip-object --folder Shared --name disk-encryption-check \
  --disk-encryption-vendor-name "BitLocker" \
  --disk-encryption-product-name "BitLocker Drive Encryption" \
  --disk-encryption-criteria-is-installed is \
  --disk-encryption-state is

# List all HIP objects
scm show objects hip-object --folder Shared --list

# Show specific HIP object details
scm show objects hip-object --folder Shared --name windows-security-compliance
```

#### Managing HIP Profiles

```bash
# Create a HIP profile with multiple match criteria
scm set objects hip-profile --folder Shared --name secure-endpoints \
  --match '{"windows-security-compliance": {"is": true}, "disk-encryption-check": {"is": true}}' \
  --description "Profile for fully compliant Windows endpoints"

# List all HIP profiles
scm show objects hip-profile --folder Shared --list

# Show specific HIP profile details
scm show objects hip-profile --folder Shared --name secure-endpoints
```

#### Managing HTTP Server Profiles

```bash
# Create an HTTP server profile for syslog forwarding
scm set objects http-server-profile --folder Shared --name syslog-collector \
  --servers '[{"name": "primary-syslog", "address": "syslog.example.com", "protocol": "HTTPS", "port": 443, "http_method": "POST"}]' \
  --description "Primary syslog collector"

# Create an HTTP server profile with authentication
scm set objects http-server-profile --folder Shared --name splunk-hec \
  --servers '[{"name": "splunk-server", "address": "10.0.1.100", "protocol": "HTTPS", "port": 8088, "http_method": "POST", "username": "hec_user", "password": "secure_token"}]'

# List all HTTP server profiles
scm show objects http-server-profile --folder Shared --list
```

#### Managing Services

```bash
# Create a basic TCP service
scm set objects service --folder Shared --name custom-web \
  --protocol tcp --port "8080,8443" --description "Custom web service"

# Create a UDP service
scm set objects service --folder Shared --name custom-dns \
  --protocol udp --port 5353 --description "Custom DNS service"

# Create a TCP service with timeout overrides
scm set objects service --folder Shared --name database-service \
  --protocol tcp --port "3306-3310" --timeout 7200 --halfclose-timeout 120 \
  --description "Database cluster ports with extended timeout"

# List all services
scm show objects service --folder Shared --list

# Show specific service details
scm show objects service --folder Shared --name custom-web
```

#### Managing Service Groups

```bash
# Create a service group
scm set objects service-group --folder Shared --name web-services \
  --members "http,https,web-browsing,ssl"

# Create a service group with tags
scm set objects service-group --folder Shared --name database-services \
  --members "mysql,mssql,oracle,postgresql" --tag "database,backend"

# List all service groups
scm show objects service-group --folder Shared --list

# Show specific service group details
scm show objects service-group --folder Shared --name web-services
```

#### Managing Syslog Server Profiles

```bash
# Create a syslog server profile with TCP
scm set objects syslog-server-profile --folder Shared --name central-syslog \
  --servers '[{"name": "syslog-primary", "server": "10.0.1.50", "port": 514, "transport": "TCP", "format": "BSD", "facility": "LOG_USER"}]' \
  --description "Central syslog collection"

# Create a syslog profile with UDP and custom format
scm set objects syslog-server-profile --folder Shared --name compliance-syslog \
  --servers '[{"name": "compliance-server", "server": "syslog.compliance.local", "port": 6514, "transport": "UDP", "format": "IETF", "facility": "LOG_LOCAL7"}]'

# List all syslog server profiles
scm show objects syslog-server-profile --folder Shared --list

# Show specific syslog profile details
scm show objects syslog-server-profile --folder Shared --name central-syslog
```

#### Managing Tags

```bash
# Create a tag with color
scm set objects tag --folder Shared --name production \
  --color "Red" --comments "Production environment resources"

# Create multiple tags for categorization
scm set objects tag --folder Shared --name database --color "Blue"
scm set objects tag --folder Shared --name frontend --color "Green"
scm set objects tag --folder Shared --name critical --color "Orange"

# List all tags
scm show objects tag --folder Shared --list

# Show specific tag details
scm show objects tag --folder Shared --name production
```

#### Bulk Operations

Create a YAML file with multiple objects:

```yaml
# addresses.yaml
addresses:
  - name: web-server-1
    description: "Web server 1"
    ip_netmask: 192.168.1.100/32
    folder: Development
    tags:
      - web
      - production

  - name: web-server-2
    description: "Web server 2"
    ip_netmask: 192.168.1.101/32
    folder: Development
    tags:
      - web
      - production

  - name: db-server
    description: "Database server"
    fqdn: db.example.com
    folder: Production
    tags:
      - database
      - production
```

Load the objects:

```bash
# Load objects with their original locations from the file
scm load objects address --file addresses.yml

# Override all objects to load into a specific folder
scm load objects address --file addresses.yml --folder Shared

# Override to a snippet location
scm load objects address --file addresses.yml --snippet DNS-Best-Practice

# Override to a device location
scm load objects address --file addresses.yml --device fw-austin-01

# Verify in mock mode first
scm load objects address --file addresses.yml --folder Shared --mock

# Dry run to preview changes
scm load objects address --file addresses.yml --dry-run
```

All load commands support container overrides, allowing you to:

- Migrate objects between folders/snippets/devices
- Test configurations in different locations
- Standardize object locations during bulk imports

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
- Service configurations with protocol and port definitions (`services.yml`)
- Service group configurations for logical service organization (`service-groups.yml`)
- Syslog server profile configurations for external logging (`syslog-server-profiles.yml`)
- Tag configurations for resource categorization (`tags.yml`)

#### Backup and Restore Operations

Export existing configurations to YAML files. All backup commands support multiple container types (folder, snippet, device) with automatic filename generation:

```bash
# Backup from different container types
scm backup objects address --folder Austin
# Creates: address_folder_austin_20240115_143022.yaml

scm backup objects tag --snippet DNS-Best-Practice
# Creates: tag_snippet_dns-best-practice_20240115_143022.yaml

scm backup objects service --device austin-01
# Creates: service_device_austin-01_20240115_143022.yaml

# Custom output filename
scm backup objects address-group --folder Texas --file my-groups.yaml
# Creates: my-groups.yaml

# All object types support folder/snippet/device parameters
scm backup objects address --folder Austin
scm backup objects address-group --folder Texas
scm backup objects application --folder Texas
scm backup objects application-group --folder Texas
scm backup objects application-filter --folder Texas
scm backup objects dynamic-user-group --folder Texas
scm backup objects external-dynamic-list --folder Texas
scm backup objects hip-object --folder Texas
scm backup objects hip-profile --folder Texas
scm backup objects http-server-profile --folder Texas
scm backup objects service --folder Texas
scm backup objects service-group --folder Texas
scm backup objects syslog-server-profile --folder Texas
scm backup objects tag --folder Texas

# Network and security backups also support all container types
scm backup network security-zone --folder ngfw-shared
scm backup network security-zone --snippet DNS-Best-Practice
scm backup network security-zone --device austin-01

scm backup security rule --folder Austin --rulebase pre
scm backup security rule --snippet DNS-Best-Practice --rulebase post

# Bandwidth allocations are global (no container parameter needed)
scm backup deployment bandwidth-allocation
# Creates: bandwidth-allocations.yaml
```

Note: Not all container types are supported by the SDK for all object types. When using snippet or device parameters, the CLI will show an appropriate error message if the SDK doesn't support that container type yet.

Restore configurations from backup files:

```bash
# Restore addresses (preview first with --dry-run)
scm load objects address --file address-austin.yaml --dry-run
scm load objects address --file address-austin.yaml

# Restore address groups
scm load objects address-group --file address-group-texas.yaml

# Restore security zones
scm load network security-zone --file security-zone-ngfw-shared.yaml

# Restore security rules
scm load security rule --file rule-austin-pre.yaml

# Restore bandwidth allocations
scm load deployment bandwidth-allocation --file bandwidth-allocations.yaml
```

The backup feature uses the `exact_match=True` parameter to only export objects that are directly defined in the specified folder, excluding inherited objects from parent folders.

## Development

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/cdot65/pan-scm.git
   cd pan-scm
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

- **Documentation**: [GitHub Pages site](https://cdot65.github.io/pan-scm/)
- **Issues**: [GitHub Issues](https://github.com/cdot65/pan-scm/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cdot65/pan-scm/discussions)
- **Examples**: See the `examples/` directory for configuration templates

## Project Status

This project is actively maintained and uses:

- Python 3.12+ with Poetry for dependency management
- pan-scm-sdk v0.3.39 for API interactions
- Dynaconf for flexible configuration management
- Pydantic for robust input validation
- Comprehensive test coverage with pytest

---

_Detailed documentation is available on our [GitHub Pages documentation site](https://cdot65.github.io/pan-scm/)._
