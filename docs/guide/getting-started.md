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

The SCM CLI uses contexts to manage authentication credentials for multiple SCM tenants.

### Option 1: Context-based Authentication (Recommended)

Context management is the recommended approach for working with SCM, especially when managing multiple tenants or environments:

```bash
# Create a context for production
$ scm context create production \
  --client-id "prod@123456789.iam.panserviceaccount.com" \
  --client-secret "your-secret-key" \
  --tsg-id "123456789"
✓ Context 'production' created successfully
✓ Context 'production' set as current

# Create a context for development with debug logging
$ scm context create development \
  --client-id "dev@987654321.iam.panserviceaccount.com" \
  --client-secret "your-dev-secret" \
  --tsg-id "987654321" \
  --log-level DEBUG
✓ Context 'development' created successfully

# View all contexts
$ scm context list
                       SCM Authentication Contexts                        
┏━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Context     ┃ Current ┃ Client ID                                       ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ production  │ ✓       │ prod@12345...@123456789.iam.panserviceaccount.com │
│ development │         │ dev@987654...@987654321.iam.panserviceaccount.com │
└─────────────┴─────────┴────────────────────────────────────────────────────┘

# Switch between contexts
$ scm context use development
✓ Switched to context 'development'

# Test authentication
$ scm context test
Testing authentication for context: development
✓ Authentication successful!
  Client ID: dev@987654321.iam.panserviceaccount.com
  TSG ID: 987654321
✓ API connectivity verified (found 42 address objects in Shared folder)
```

> **Note**: Contexts are stored in `~/.scm-cli/contexts/` with appropriate file permissions. Each context is isolated, making it safe to work with multiple tenants.

### Option 2: Environment Variables (For CI/CD)

For automated workflows and CI/CD pipelines, use environment variables:

```bash
# For Linux/macOS
export SCM_CLIENT_ID="your-client-id@123456789.iam.panserviceaccount.com"
export SCM_CLIENT_SECRET="your-client-secret"
export SCM_TSG_ID="123456789"

# For Windows PowerShell
$env:SCM_CLIENT_ID = "your-client-id@123456789.iam.panserviceaccount.com"
$env:SCM_CLIENT_SECRET = "your-client-secret"
$env:SCM_TSG_ID = "123456789"
```

> **Important**: Environment variables take precedence over contexts when both are set.

## Basic Usage Examples

Here are some examples to help you get started with common CLI operations:

### Listing Address Objects

```bash
# List all address objects in the Shared folder
scm set object address --list --folder Shared
```

### Creating an Address Object

```bash
# Create a new address object
scm set object address --folder Shared --name example-server --ip-netmask 192.168.1.100/32 --description "Example server"
```

### Updating an Address Object

```bash
# Update an existing address object
scm set object address --folder Shared --name example-server --ip-netmask 192.168.1.200/32 --description "Updated example server"
```

### Deleting an Address Object

```bash
# Delete an address object
scm delete object address --folder Shared --name example-server
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
scm load object address --folder Shared --file addresses.yaml
```

## Getting Help

The CLI includes comprehensive help information:

```bash
# Show general help
scm --help

# Show help for a specific command
scm set object address --help
```

## Next Steps

- Explore [Working with Configuration Objects](configuration-objects.md) to learn about different object types
- Read [Advanced CLI Topics](advanced-topics.md) for tips on automation and scripting
- Review [CLI Operations](operations.md) for information on managing deployments
- See the [CLI Reference](../cli/index.md) for detailed command documentation
