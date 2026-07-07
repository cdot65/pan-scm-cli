# Getting Started

This guide walks you through initial setup and basic usage of the `pan-scm-cli` tool for managing Palo Alto Networks Strata Cloud Manager.

## Installation

Install the package via pip (Python 3.10+ required):

```bash
$ pip install pan-scm-cli
---> 100%
Successfully installed pan-scm-cli
```

:::tip
See the [Installation Guide](installation.md) for detailed setup instructions
including virtual environments and Docker.
:::

## Authentication Setup

The SCM CLI uses a context-based authentication system. You can configure credentials through contexts or environment variables.

### Option 1: Contexts (Recommended)

Create a named context with your SCM credentials:

```bash
$ scm context create production \
    --client-id "your-app@123456789.iam.panserviceaccount.com" \
    --client-secret "your-secret-key" \
    --tsg-id "123456789"
---> 100%
✓ Context 'production' created successfully
✓ Context 'production' set as current
```

Test the connection:

```bash
$ scm context test
Testing authentication for context: production
✓ Authentication successful!
  Client ID: your-app@123456789.iam.panserviceaccount.com
  TSG ID: 123456789
✓ API connectivity verified (found 15 address objects in Shared folder)
```

Switch between multiple tenants:

```bash
$ scm context list
$ scm context use staging
```

### Option 2: Environment Variables

For CI/CD pipelines or scripting, set environment variables:

```bash
export SCM_CLIENT_ID="your_client_id"
export SCM_CLIENT_SECRET="your_client_secret"
export SCM_TSG_ID="your_tsg_id"
```

:::info
Environment variables override context credentials when both are present.
This is useful for CI/CD environments where credentials are injected at runtime.
:::

### Credential Precedence

The CLI loads credentials in the following order (highest to lowest priority):

| Priority | Source | Use Case |
| --- | --- | --- |
| 1 | Environment variables (`SCM_CLIENT_ID`, `SCM_CLIENT_SECRET`, `SCM_TSG_ID`) | CI/CD pipelines |
| 2 | Active context (set via `scm context use`) | Interactive use |
| 3 | Mock mode | Testing without credentials |

:::warning
Never commit credentials to version control. Use contexts or environment
variables for secure credential management. Regularly rotate your credentials.
:::

## Command Structure

All commands follow this pattern:

```bash
scm <action> <category> <resource> [name] [options]
```

| Component | Description | Examples |
| --- | --- | --- |
| `<action>` | Operation to perform | `set`, `delete`, `load`, `show`, `backup`, `move` |
| `<category>` | Category of resource | `object`, `network`, `security`, `sase` |
| `<resource>` | Specific resource type | `address`, `address-group`, `zone` |
| `[name]` | Positional resource name (required for `set`/`delete`/`move`; optional for `show`) | `webserver` |
| `[options]` | Resource-specific parameters | `--folder`, `--ip-netmask` |

## Basic Usage Examples

### Getting Help

Use the `--help` flag for any command:

```bash
$ scm --help
Usage: scm [OPTIONS] COMMAND [ARGS]...

  Command-line interface for Palo Alto Networks Strata Cloud Manager.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  backup      Backup configurations to YAML files
  commit      Commit staged configuration changes
  context     Manage authentication contexts
  delete      Remove configurations
  incidents   Search and view security incidents
  insights    Query monitoring insights
  jobs        Manage SCM jobs
  load        Load configurations from YAML files
  local       Retrieve local device configurations
  move        Move rules to a new position
  operations  Run device operations
  posture     Firewall posture / BPA assessment
  set         Create or update configurations
  show        Display configurations
```

Command-specific help:

```bash
$ scm set object address --help
Usage: scm set object address [OPTIONS] NAME

  Create or update an address object.

Arguments:
  NAME                     Name of the address  [required]

Options:
  --folder TEXT            Folder location
  --snippet TEXT           Snippet location
  --device TEXT            Device location
  --description TEXT       Description of the address
  --tags TEXT              Tags (repeat for multiple)
  --ip-netmask TEXT        IP address with CIDR notation (e.g. 192.168.1.0/24)
  --ip-range TEXT          IP address range (e.g. 192.168.1.1-192.168.1.10)
  --ip-wildcard TEXT       IP wildcard mask (e.g. 10.20.1.0/0.0.248.255)
  --fqdn TEXT              Fully qualified domain name (e.g. example.com)
  --help                   Show this message and exit.
```

### Creating an Address Object

```bash
$ scm set object address webserver \
    --folder Texas \
    --ip-netmask 192.168.1.100/32 \
    --description "Web server"
---> 100%
Created address: webserver in folder Texas
```

### Creating an Address with FQDN

```bash
$ scm set object address company-website \
    --folder Texas \
    --fqdn example.com \
    --description "Company website"
---> 100%
Created address: company-website in folder Texas
```

### Listing Address Objects

```bash
$ scm show object address --folder Texas
---> 100%
Addresses in folder 'Texas':
------------------------------------------------------------
Name: webserver
  Type: ip-netmask
  Value: 192.168.1.100/32
------------------------------------------------------------
Name: company-website
  Type: fqdn
  Value: example.com
------------------------------------------------------------
```

### Deleting an Address Object

```bash
$ scm delete object address webserver --folder Texas
---> 100%
Deleted address: webserver from folder Texas
```

## Bulk Operations

### Loading from YAML

Create a YAML file with multiple definitions:

```yaml
---
addresses:
  - name: web-server-1
    folder: Texas
    description: "Web Server 1"
    ip_netmask: 192.168.1.10/32
    tags:
      - web
      - production

  - name: web-server-2
    folder: Texas
    description: "Web Server 2"
    ip_netmask: 192.168.1.11/32
    tags:
      - web
      - production

  - name: database-server
    folder: Texas
    description: "Database Server"
    ip_netmask: 192.168.2.10/32
    tags:
      - database
      - production
```

Load the addresses from the file:

```bash
$ scm load object address --file addresses.yml
---> 100%
✓ Loaded address: web-server-1
✓ Loaded address: web-server-2
✓ Loaded address: database-server

Successfully loaded 3 out of 3 addresses from 'addresses.yml'
```

## Dry Run and Mock Modes

### Dry Run Mode

Preview bulk changes without applying them (available on every `load` command):

```bash
$ scm load object address --file addresses.yml --dry-run
---> 100%
Dry run mode: would apply the following configurations:
- name: web-server-1
  folder: Texas
  ip_netmask: 192.168.1.10/32
```

### Mock Mode

Set `SCM_MOCK=1` to run commands without connecting to the SCM API:

```bash
$ SCM_MOCK=1 scm set object address webserver \
    --folder Texas \
    --ip-netmask 192.168.1.100/32
---> 100%
Created address: webserver in folder Texas
```

:::tip
Mock mode is useful for testing scripts and workflows without consuming
API calls or requiring valid credentials.
:::

## Next Steps

1. Explore the [CLI Reference](../cli/index.md) for a complete list of commands and options
2. Learn about [Troubleshooting](troubleshooting.md) common issues
3. Read about [Contributing](contributing.md) to the project
