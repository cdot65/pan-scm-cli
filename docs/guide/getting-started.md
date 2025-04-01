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

The SCM CLI uses dynaconf to manage authentication credentials. You have the following options for authentication:

### Option 1: Using Local .secrets.yaml (Recommended for Development)

> **⚠️ SECURITY WARNING**
>
> Storage of credentials in files poses security risks. Consider these best practices:
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

4. Run the CLI from the same directory where `.secrets.yaml` is located. Dynaconf will automatically load credentials from this file.

> **Note**: The `.secrets.yaml` file is excluded from version control in `.gitignore` to prevent accidental exposure of credentials. For team environments, each developer should maintain their own local configuration and credentials.

### Option 2: Environment Variables

For production use or scripting, set environment variables:

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

These environment variables will be automatically detected by dynaconf and used for authentication.

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
