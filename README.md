# Strata Cloud Manager CLI

[![PyPI version](https://badge.fury.io/py/pan-scm-cli.svg)](https://badge.fury.io/py/pan-scm-cli)
[![Python versions](https://img.shields.io/pypi/pyversions/pan-scm-cli.svg)](https://pypi.org/project/pan-scm-cli/)
[![License](https://img.shields.io/github/license/cdot65/pan-scm-cli.svg)](https://github.com/cdot65/pan-scm-cli/blob/main/LICENSE)

A command-line interface for managing Palo Alto Networks Strata Cloud Manager (SCM) configurations. This tool simplifies the management of security policies, objects, and configurations through an intuitive CLI.

## Quick Start

```bash
# Install
pip install pan-scm-cli

# Set credentials
export SCM_CLIENT_ID="your_client_id"
export SCM_CLIENT_SECRET="your_client_secret"
export SCM_TSG_ID="your_tsg_id"

# Create an address object
scm set object address --folder Texas --name web-server --ip-netmask 10.1.1.100/32 --description "Web server"

# List all addresses
scm show object address --folder Texas

# Create a security rule
scm set security rule --folder Texas --name allow-web \
  --source-zones trust --destination-zones dmz \
  --source-addresses any --destination-addresses web-server \
  --services any --action allow
```

## Table of Contents

- [Installation](#installation)
- [Getting Started](#getting-started)
- [Common Use Cases](#common-use-cases)
- [Command Reference](#command-reference)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Key Features

- **Comprehensive Object Management**: Create, update, and delete security configurations
- **Bulk Operations**: Import/export configurations using YAML files
- **Smart Updates**: Automatically handles existing objects without errors
- **Container Support**: Work with folders, snippets, and devices
- **Mock Mode**: Test commands without making API calls
- **Input Validation**: Prevents errors before they reach the API

## Installation

### Requirements

- Python 3.10 or higher
- An active Strata Cloud Manager account

### Install via pip

```bash
pip install pan-scm-cli
```

## Getting Started

### 1. Set Up Authentication

Choose one of these methods to configure your credentials:

#### Option A: Context-based Authentication (Recommended for Multiple Tenants)

```bash
# Create a context for each SCM tenant
$ scm context create production \
  --client-id "prod-app@123456789.iam.panserviceaccount.com" \
  --client-secret "your-secret-key" \
  --tsg-id "123456789"
✓ Context 'production' created successfully
✓ Context 'production' set as current

# Create another context (with custom log level)
$ scm context create development \
  --client-id "dev-app@987654321.iam.panserviceaccount.com" \
  --client-secret "your-dev-secret" \
  --tsg-id "987654321" \
  --log-level DEBUG
✓ Context 'development' created successfully

# View all available contexts
$ scm context list
                       SCM Authentication Contexts
┏━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Context     ┃ Current ┃ Client ID                                       ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ production  │ ✓       │ prod-app@1...@123456789.iam.panserviceaccount.com │
│ development │         │ dev-app@98...@987654321.iam.panserviceaccount.com │
└─────────────┴─────────┴────────────────────────────────────────────────────┘

# Show details of a specific context
$ scm context show production
Context: production

Configuration:
  Client ID: prod-app@123456789.iam.panserviceaccount.com
  TSG ID: 123456789
  Log Level: INFO
  Client Secret: ***** (configured)

# Switch between contexts
$ scm context use development
✓ Switched to context 'development'

Client ID: dev-app@987654321.iam.panserviceaccount.com
TSG ID: 987654321

# Check current context
$ scm context current
Current context: development

Client ID: dev-app@987654321.iam.panserviceaccount.com
TSG ID: 987654321
```

#### Option B: Environment Variables (For CI/CD and Automation)

```bash
export SCM_CLIENT_ID="your_client_id"
export SCM_CLIENT_SECRET="your_client_secret"
export SCM_TSG_ID="your_tenant_service_group_id"
```

**Note:** Environment variables take precedence over contexts when both are set.

### 2. Verify Your Setup

```bash
# Test current context authentication
$ scm context test
Testing authentication for context: development
✓ Authentication successful!
  Client ID: dev-app@987654321.iam.panserviceaccount.com
  TSG ID: 987654321
✓ API connectivity verified (found 42 address objects in Shared folder)

# Test a specific context without switching
$ scm context test production
Testing authentication for context: production
✓ Authentication successful!
  Client ID: prod-app@123456789.iam.panserviceaccount.com
  TSG ID: 123456789
✓ API connectivity verified (found 15 address objects in Shared folder)

# Test without API calls (mock mode)
$ scm context test --mock
Testing authentication for context: development
✓ Authentication simulation successful (mock mode)
  Client ID: dev-app@987654321.iam.panserviceaccount.com
  TSG ID: 987654321
```

### 3. Try Your First Commands

```bash
# Create a tag
scm set object tag --folder Texas --name production --color Red --comments "Production resources"

# Create an address
scm set object address --folder Texas --name web-server --ip-netmask 10.1.1.100/32

# List all addresses
scm show object address --folder Texas
```

## Common Use Cases

### Managing Network Objects

#### Create Address Objects

```bash
# Single IP address
scm set object address --folder Texas --name web-server-1 --ip-netmask 10.1.1.100/32 --description "Production web server"

# Subnet
scm set object address --folder Texas --name dmz-subnet --ip-netmask 10.0.0.0/24 --description "DMZ network"

# FQDN
scm set object address --folder Texas --name external-site --fqdn example.com --description "External website"
```

#### Create Address Groups

```bash
# Static group with multiple members
scm set object address-group --folder Texas --name web-servers --type static --members "web-server-1,web-server-2"

# Dynamic group based on tags
scm set object address-group --folder Texas --name dynamic-web-servers --type dynamic --filter "'web' and 'production'"
```

### Security Policy Management

#### Create Security Zones

```bash
# Layer 3 zone
scm set network zone --folder Texas --name dmz --mode layer3

# Zone with user ID enabled
scm set network zone --folder Texas --name trust --mode layer3 --enable-user-id
```

#### Create Security Rules

```bash
# Basic allow rule
scm set security rule --folder Texas --name allow-web-traffic \
  --source-zones trust \
  --destination-zones dmz \
  --source-addresses any \
  --destination-addresses web-servers \
  --services any \
  --action allow \
  --log-end

# Application-specific rule
scm set security rule --folder Texas --name allow-database \
  --source-zones app-zone \
  --destination-zones db-zone \
  --source-addresses app-servers \
  --destination-addresses database-servers \
  --applications "mysql,postgresql" \
  --action allow
```

### Service Management

#### Create Custom Services

```bash
# TCP service
scm set object service --folder Texas --name custom-web --protocol tcp --port "8080,8443" --description "Custom web ports"

# UDP service
scm set object service --folder Texas --name custom-dns --protocol udp --port 5353 --description "mDNS"

# Service with timeout override
scm set object service --folder Texas --name long-running-db --protocol tcp --port 3306 --timeout 7200
```

#### Service Groups

```bash
# Group related services
scm set object service-group --folder Texas --name web-services --members "http,https,custom-web"
```

### Tag Management

Tags help organize and categorize your objects:

```bash
# Environment tags
scm set object tag --folder Texas --name production --color Red --comments "Production environment"
scm set object tag --folder Texas --name development --color Green --comments "Development environment"
scm set object tag --folder Texas --name staging --color Blue --comments "Staging environment"

# Category tags
scm set object tag --folder Texas --name database --color Orange --comments "Database resources"
scm set object tag --folder Texas --name web --color Cyan --comments "Web resources"
```

### Bulk Operations

Work with multiple objects at once using YAML files:

#### Export Configuration

```bash
# Export all addresses from a folder
scm backup object address --folder Texas
# Creates: address_folder_texas_20250602_143000.yaml

# Export with custom filename
scm backup object address-group --folder Texas --file my-groups.yaml

# Export from different containers
scm backup object tag --snippet automation
scm backup object service --device austin-01
```

#### Import Configuration

Create a YAML file for bulk import:

```yaml
# addresses.yaml
addresses:
  - name: web-01
    description: "Production web server"
    ip_netmask: 10.1.1.10/32
    folder: Texas
    tags:
      - web
      - production

  - name: web-02
    description: "Production web server"
    ip_netmask: 10.1.1.11/32
    folder: Texas
    tags:
      - web
      - production

  - name: db-01
    description: "Database server"
    ip_netmask: 10.2.1.10/32
    folder: Texas
    tags:
      - database
      - production
```

Import the configuration:

```bash
# Preview changes
scm load object address --file addresses.yaml --dry-run

# Import to original locations
scm load object address --file addresses.yaml

# Override location for all objects
scm load object address --file addresses.yaml --folder Production
```

### Context Management Examples

#### Working with Multiple Tenants

```bash
# Create contexts for different environments
$ scm context create prod-us \
  --client-id "us-prod@111111111.iam.panserviceaccount.com" \
  --client-secret "prod-secret" \
  --tsg-id "111111111" \
  --log-level WARNING
✓ Context 'prod-us' created successfully

$ scm context create prod-eu \
  --client-id "eu-prod@222222222.iam.panserviceaccount.com" \
  --client-secret "prod-secret" \
  --tsg-id "222222222" \
  --log-level WARNING
✓ Context 'prod-eu' created successfully

# List all contexts
$ scm context list
                           SCM Authentication Contexts
┏━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Context     ┃ Current ┃ Client ID                                       ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ production  │         │ prod-app@1...@123456789.iam.panserviceaccount.com │
│ development │ ✓       │ dev-app@98...@987654321.iam.panserviceaccount.com │
│ prod-us     │         │ us-prod@11...@111111111.iam.panserviceaccount.com │
│ prod-eu     │         │ eu-prod@22...@222222222.iam.panserviceaccount.com │
└─────────────┴─────────┴────────────────────────────────────────────────────┘

# Work with US production
$ scm context use prod-us
✓ Switched to context 'prod-us'

$ scm show object address --folder Texas
[INFO] Using authentication context: prod-us
Addresses in folder 'Texas':
...

# Switch to EU production
$ scm context use prod-eu
✓ Switched to context 'prod-eu'

$ scm show object address --folder London
[INFO] Using authentication context: prod-eu
Addresses in folder 'London':
...

# Delete a context you no longer need
$ scm context delete old-dev
Are you sure you want to delete context 'old-dev'? [y/N]: y
✓ Context 'old-dev' deleted
```

### Docker Container Support

The SCM CLI is available as a Docker image, providing a consistent environment across different platforms. The Docker image integrates seamlessly with the context management system:

#### Running with Contexts

```bash
# Pull the official image
docker pull ghcr.io/cdot65/pan-scm-cli:latest

# Run with context volume mounting
docker run -d \
  --name pan-scm \
  -v ~/.scm-cli:/home/scmuser/.scm-cli \
  ghcr.io/cdot65/pan-scm-cli:latest

# Your contexts are now available in the container
docker exec pan-scm scm context list

# Switch contexts in the container
docker exec pan-scm scm context use production

# Run commands with the active context
docker exec pan-scm scm show object address --folder Texas
```

#### Benefits of Docker with Contexts

1. **Consistent Environment**: Same CLI version and dependencies across all systems
2. **Context Portability**: Your contexts work identically on host and in containers
3. **Security**: Credentials stay on the host, never baked into images
4. **Multi-tenant Isolation**: Run multiple containers with different contexts simultaneously
5. **CI/CD Ready**: Perfect for automated workflows with environment variable overrides

#### Multi-tenant Example

```bash
# Run containers for different environments
docker run -d --name scm-prod -v ~/.scm-cli:/home/scmuser/.scm-cli ghcr.io/cdot65/pan-scm-cli:latest
docker run -d --name scm-dev -v ~/.scm-cli:/home/scmuser/.scm-cli ghcr.io/cdot65/pan-scm-cli:latest

# Use different contexts in each container
docker exec scm-prod scm context use production
docker exec scm-dev scm context use development

# Now each container operates on different tenants
docker exec scm-prod scm show object address --folder Production
docker exec scm-dev scm show object address --folder Development
```

#### Building Docker Images

For developers who want to build their own images:

```bash
# Clone the repository
git clone https://github.com/cdot65/pan-scm-cli.git
cd pan-scm-cli

# Build for your local platform
./docker/docker-build.sh --local

# Build AMD64 image (for Intel/AMD systems)
./docker/docker-build.sh --amd64

# Force rebuild without cache
./docker/docker-build.sh --no-cache --local
```

Platform-specific images are available:

- **AMD64**: `ghcr.io/cdot65/pan-scm-cli:latest`
- **ARM64**: `ghcr.io/cdot65/pan-scm-cli:apple` (for Apple Silicon)

### SASE Deployment

#### Service Connections

Service connections establish secure tunnels between your branch locations and Prisma Access:

```bash
# Create a service connection
scm set sase service-connection \
  --name branch-primary \
  --ipsec-tunnel ipsec-tunnel-1 \
  --region us-east-1 \
  --subnets "10.1.0.0/24,10.1.1.0/24"

# Enable BGP for dynamic routing
scm set sase service-connection \
  --name datacenter-connection \
  --ipsec-tunnel dc-tunnel \
  --region us-west-2 \
  --bgp-enable \
  --bgp-peer-as 65000 \
  --bgp-peer-ip 192.168.1.1 \
  --bgp-local-ip 192.168.1.2

# List all service connections
scm show sase service-connection
```

#### Remote Networks

Remote networks define your branch office or data center locations:

```bash
# Create a remote network
scm set sase remote-network \
  --name branch-office-1 \
  --region us-east-1 \
  --license-type FWAAS-AGGREGATE \
  --spn-name us-east-spn \
  --ipsec-tunnel branch-tunnel-1 \
  --subnets "10.1.0.0/16"

# Remote network with BGP
scm set sase remote-network \
  --name datacenter-west \
  --region us-west-2 \
  --spn-name us-west-spn \
  --ipsec-tunnel dc-tunnel \
  --bgp-enable \
  --bgp-peer-as 65000 \
  --bgp-peer-ip 192.168.1.1

# List all remote networks
scm show sase remote-network
```

### Complete Workflow Example

Here's a complete example of setting up a web application security policy:

```bash
# Step 1: Create tags
scm set object tag --folder Texas --name web --color Cyan --comments "Web resources"
scm set object tag --folder Texas --name database --color Orange --comments "Database resources"
scm set object tag --folder Texas --name production --color Red --comments "Production environment"

# Step 2: Create addresses
scm set object address --folder Texas --name web-01 --ip-netmask 10.1.1.10/32 --tag web,production
scm set object address --folder Texas --name web-02 --ip-netmask 10.1.1.11/32 --tag web,production
scm set object address --folder Texas --name db-01 --ip-netmask 10.2.1.10/32 --tag database,production

# Step 3: Create address groups
scm set object address-group --folder Texas --name web-servers-group --type static --members "web-01,web-02"
scm set object address-group --folder Texas --name database-servers --type static --members "db-01"

# Step 4: Create custom services
scm set object service --folder Texas --name custom-web --protocol tcp --port 443
scm set object service --folder Texas --name custom-db --protocol tcp --port 3306

# Step 5: Create service group
scm set object service-group --folder Texas --name app-services --members "custom-web,custom-db"

# Step 6: Create security zones
scm set network zone --folder Texas --name trust --mode layer3
scm set network zone --folder Texas --name dmz --mode layer3
scm set network zone --folder Texas --name database --mode layer3

# Step 7: Create security rule
scm set security rule --folder Texas --name allow-web-to-db \
  --source-zones dmz \
  --destination-zones database \
  --source-addresses web-servers-group \
  --destination-addresses database-servers \
  --services custom-db \
  --action allow \
  --log-end \
  --description "Allow web servers to access database"

# Step 8: Verify configuration
scm show security rule --folder Texas --name allow-web-to-db
```

## Command Reference

### Basic Command Structure

```
scm <action> <object-type> <object> [options]
```

### Actions

- **set**: Create or update an object
- **show**: Display objects (lists all by default, use --name for specific object)
- **delete**: Remove an object
- **load**: Import from YAML file
- **backup**: Export to YAML file
- **context**: Manage authentication contexts

### Object Types

- **objects**: Address, service, tag, application configurations
- **network**: Security zones
- **security**: Security rules and profiles
- **sase**: Service connections, remote networks, bandwidth allocations

### Common Options

- `--folder`: Specify folder location (default: "Shared")
- `--snippet`: Use snippet instead of folder
- `--device`: Use device instead of folder
- `--mock`: Run without API calls
- `--help`: Show command help

## Advanced Features

### External Dynamic Lists (EDLs)

Integrate threat intelligence feeds:

```bash
# Palo Alto Networks predefined lists
scm set object external-dynamic-list --folder Texas \
  --name bulletproof-ips --type predefined_ip \
  --url "panw-bulletproof-ip-list"

# Custom threat feed with hourly updates
scm set object external-dynamic-list --folder Texas \
  --name threat-feed --type ip \
  --url "https://example.com/threats.txt" \
  --recurring hourly

# Domain blocklist with authentication
scm set object external-dynamic-list --folder Texas \
  --name malicious-domains --type domain \
  --url "https://secure.example.com/domains.txt" \
  --username api_user --password secure_pass \
  --recurring daily --hour 3
```

### Application Management

Define custom applications:

```bash
# Create custom application
scm set object application --folder Texas --name internal-portal \
  --category business-systems --subcategory general-business \
  --technology browser-based --risk 2 \
  --ports "tcp/443" --description "Internal employee portal"

# High-risk application filter
scm set object application-filter --folder Texas --name high-risk-apps \
  --category "file-sharing,peer-to-peer" --risk 4 --risk 5 \
  --has-known-vulnerabilities
```

### HIP (Host Information Profile) Compliance

Enforce endpoint compliance:

```bash
# Windows compliance check
scm set object hip-object --folder Texas --name windows-compliance \
  --description "Windows security requirements" \
  --host-info-os Microsoft --host-info-os-value All \
  --host-info-managed \
  --disk-encryption-enabled \
  --patch-management-enabled

# Create HIP profile
scm set object hip-profile --folder Texas --name secure-endpoints \
  --match '{"windows-compliance": {"is": true}}' \
  --description "Require compliant Windows endpoints"
```

### Log Forwarding

Configure log collection:

```bash
# Syslog server profile
scm set object syslog-server-profile --folder Texas --name central-syslog \
  --servers '[{"name": "primary", "server": "10.0.1.50", "port": 514, "transport": "TCP", "format": "BSD", "facility": "LOG_USER"}]'

# HTTP server profile for SIEM
scm set object http-server-profile --folder Texas --name splunk-hec \
  --servers '[{"name": "splunk", "address": "10.0.1.100", "protocol": "HTTPS", "port": 8088, "http_method": "POST"}]'

# Log forwarding profile
scm set object log-forwarding-profile --folder Texas --name security-logs \
  --match-list '[{"name": "threats", "log_type": "threat", "send_to_panorama": true}]'
```

## Troubleshooting

### Common Issues

#### Authentication Errors

```bash
# Check current authentication
scm context test

# If fails, verify credentials
echo $SCM_CLIENT_ID
echo $SCM_CLIENT_SECRET
echo $SCM_TSG_ID
```

#### Object Already Exists

The CLI handles existing objects gracefully:

```bash
# This will update if exists, create if not
scm set object address --folder Texas --name server --ip-netmask 10.1.1.1/32
```

#### Rate Limiting

If you encounter rate limits:

```bash
# Use mock mode for testing
scm set object address --folder Texas --name test --ip-netmask 10.1.1.1/32 --mock

# Or add delays in scripts
sleep 1
```

### Debug Mode

For detailed logging:

```bash
# Set log level
export SCM_LOG_LEVEL=DEBUG

# Run command
scm show object address --folder Texas
```

## Examples Directory

The `examples/` directory contains ready-to-use templates:

- `addresses.yml` - Common address objects
- `rfc1918-addresses.yml` - Private IP ranges
- `security-rules.yml` - Security policy examples
- `tags.yml` - Tag organization system
- `services.yml` - Custom service definitions
- `hip-objects.yml` - HIP compliance configurations
- `SASE_COMMANDS_EXAMPLES.md` - Service connection and remote network examples

## Contributing

We welcome contributions! Please see our [Contributing Guide](./docs/about/contributing.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/cdot65/pan-scm-cli.git
cd pan-scm-cli

# Install dependencies
make setup

# Run tests
make tests

# Check code quality
make quality
```

## License

Apache 2.0 - see [LICENSE](./LICENSE) for details.

## Resources

- [Documentation](https://cdot65.github.io/pan-scm-cli/)
- [GitHub Issues](https://github.com/cdot65/pan-scm-cli/issues)
- [Examples](./examples/)
- [Release Notes](https://github.com/cdot65/pan-scm-cli/releases)
