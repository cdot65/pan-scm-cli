# Getting Started with the CLI

This guide provides a quick introduction to using the Strata Cloud Manager CLI.

## Installation

Install the CLI using pip:

```bash
pip install pan-scm-cli
```

Or with poetry:

```bash
poetry add pan-scm-cli
```

## Authentication

To use the CLI, you need to authenticate with Strata Cloud Manager. You have two options:

### Option 1: Environment Variables (Recommended)

Set the following environment variables:

```bash
# For Linux/macOS
export SCM_CLIENT_ID="your-client-id"
export SCM_CLIENT_SECRET="your-client-secret"
export SCM_TSG_ID="your-tenant-service-group-id"

# For Windows PowerShell
$env:SCM_CLIENT_ID = "your-client-id"
$env:SCM_CLIENT_SECRET = "your-client-secret"
$env:SCM_TSG_ID = "your-tenant-service-group-id"
```

### Option 2: Configuration File

Create a configuration file at `~/.scm-cli/config.yaml`:

```yaml
client_id: "your-client-id"
client_secret: "your-client-secret"
tsg_id: "your-tenant-service-group-id"
```

## Basic Usage Examples

Here are some examples to help you get started with common CLI operations:

### Listing Address Objects

```bash
# List all address objects in the Shared folder
scm-cli set objects address --list --folder Shared
```

### Creating an Address Object

```bash
# Create a new address object
scm-cli set objects address --folder Shared --name example-server --ip-netmask 192.168.1.100/32 --description "Example server"
```

### Updating an Address Object

```bash
# Update an existing address object
scm-cli set objects address --folder Shared --name example-server --ip-netmask 192.168.1.200/32 --description "Updated example server"
```

### Deleting an Address Object

```bash
# Delete an address object
scm-cli delete objects address --folder Shared --name example-server
```

### Bulk Operations with YAML

Create a file named `addresses.yaml`:

```yaml
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
scm-cli load objects address --folder Shared --file addresses.yaml
```

## Getting Help

The CLI includes comprehensive help information:

```bash
# Show general help
scm-cli --help

# Show help for a specific command
scm-cli set objects address --help
```

## Next Steps

- Explore [Working with Configuration Objects](configuration-objects.md) to learn about different object types
- Read [Advanced CLI Topics](advanced-topics.md) for tips on automation and scripting
- Review [CLI Operations](operations.md) for information on managing deployments
- See the [CLI Reference](../cli/index.md) for detailed command documentation
