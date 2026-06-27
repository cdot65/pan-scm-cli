# Getting Started

The `scm` CLI provides a command-line interface for managing Palo Alto Networks Strata Cloud Manager configurations. This guide walks you through installation, authentication, and your first commands.

## Overview

This guide covers the essentials for getting up and running with the CLI:

- Install the CLI using pip or Poetry
- Configure authentication via contexts or environment variables
- Run basic commands to create, list, update, and delete objects
- Perform bulk operations with YAML files
- Access built-in help for any command

## Prerequisites

Before you begin, ensure you have:

- Python 3.12 or later installed
- Access to a Strata Cloud Manager tenant
- Service account credentials (client ID, client secret, TSG ID)

## Core Concepts

### Command Structure

The CLI follows a consistent pattern:

```bash
scm <action> <category> <object> [OPTIONS]
```

| Component | Description | Examples |
| --- | --- | --- |
| `action` | Operation to perform | `set`, `show`, `delete`, `load`, `backup` |
| `category` | Resource category | `object`, `network`, `security`, `deployment` |
| `object` | Resource type | `address`, `address-group`, `security-zone`, `rule` |

### Smart Upsert

The `set` command uses a smart upsert pattern: if an object with the given name exists, it updates only changed fields. If it does not exist, it creates it.

### Installation

Install the CLI using pip:

```bash
pip install pan-scm-cli
```

Or with Poetry:

```bash
poetry add pan-scm-cli
```

### Authentication

The SCM CLI uses contexts to manage authentication credentials for multiple SCM tenants.

#### Context-Based Authentication (Recommended)

Context management is the recommended approach, especially when managing multiple tenants or environments:

```bash
$ scm context create production \
    --client-id "prod@123456789.iam.panserviceaccount.com" \
    --client-secret "your-secret-key" \
    --tsg-id "123456789"
---> 100%
✓ Context 'production' created successfully
✓ Context 'production' set as current
```

```bash
$ scm context create development \
    --client-id "dev@987654321.iam.panserviceaccount.com" \
    --client-secret "your-dev-secret" \
    --tsg-id "987654321" \
    --log-level DEBUG
---> 100%
✓ Context 'development' created successfully
```

View all contexts:

```bash
$ scm context list
                       SCM Authentication Contexts
┏━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Context     ┃ Current ┃ Client ID                                       ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ production  │ ✓       │ prod@12345...@123456789.iam.panserviceaccount.com │
│ development │         │ dev@987654...@987654321.iam.panserviceaccount.com │
└─────────────┴─────────┴────────────────────────────────────────────────────┘
```

Switch between contexts and test authentication:

```bash
$ scm context use development
---> 100%
✓ Switched to context 'development'

$ scm context test
Testing authentication for context: development
✓ Authentication successful!
  Client ID: dev@987654321.iam.panserviceaccount.com
  TSG ID: 987654321
✓ API connectivity verified (found 42 address objects in Shared folder)
```

:::info
Contexts are stored in `~/.scm-cli/contexts/` with appropriate file permissions.
Each context is isolated, making it safe to work with multiple tenants.
:::

#### Environment Variables (For CI/CD)

For automated workflows and CI/CD pipelines, use environment variables:

```bash
# For Linux/macOS
export SCM_CLIENT_ID="your-client-id@123456789.iam.panserviceaccount.com"
export SCM_CLIENT_SECRET="your-client-secret"
export SCM_TSG_ID="123456789"
```

```bash
# For Windows PowerShell
$env:SCM_CLIENT_ID = "your-client-id@123456789.iam.panserviceaccount.com"
$env:SCM_CLIENT_SECRET = "your-client-secret"
$env:SCM_TSG_ID = "123456789"
```

:::warning
Environment variables take precedence over contexts when both are set.
Avoid committing credentials to version control.
:::

## Examples

### Creating an Address Object

```bash
$ scm set object address \
    --folder Shared \
    --name web-server \
    --ip-netmask 192.168.1.100/32 \
    --description "Web server"
---> 100%
Created address: web-server in folder Shared
```

### Listing Address Objects

```bash
$ scm show object address --folder Shared
---> 100%
Addresses in folder 'Shared':
------------------------------------------------------------
Name: web-server
  IP Netmask: 192.168.1.100/32
  Description: Web server
------------------------------------------------------------
```

### Updating an Address Object

```bash
$ scm set object address \
    --folder Shared \
    --name web-server \
    --ip-netmask 192.168.1.200/32 \
    --description "Updated web server"
---> 100%
Updated address: web-server in folder Shared
```

### Deleting an Address Object

```bash
$ scm delete object address --folder Shared --name web-server
---> 100%
Deleted address: web-server from folder Shared
```

### Bulk Operations with YAML

Create a file named `addresses.yaml`:

```yaml
---
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

Then load these address objects:

```bash
$ scm load object address --folder Shared --file addresses.yaml
---> 100%
✓ Loaded address: web-server-1
✓ Loaded address: web-server-2

Successfully loaded 2 out of 2 addresses from 'addresses.yaml'
```

### Getting Help

The CLI includes comprehensive help information:

```bash
scm --help
```

```bash
scm set object address --help
```

## Best Practices

1. **Use contexts for authentication**: Contexts provide safe, isolated credential storage for multiple tenants.
2. **Start with mock mode**: Use the `--mock` flag to test commands without making API changes.
3. **Use YAML for bulk operations**: Loading objects from YAML files is more maintainable than individual commands.
4. **Test authentication first**: Run `scm context test` to verify credentials before running commands.
5. **Check help for options**: Every command supports `--help` to show available parameters.

## Next Steps

- Explore [Working with Configuration Objects](configuration-objects.md) to learn about different object types
- Read [Configuration Management](configuration.md) for details on multi-tenant setup and settings
- Review [Advanced CLI Topics](advanced-topics.md) for tips on automation and scripting
- See the [CLI Reference](../cli/index.md) for detailed command documentation
