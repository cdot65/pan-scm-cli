# Advanced CLI Topics

This guide covers advanced features and techniques for working with the Strata Cloud Manager CLI.

## Working with Multiple Folders

The CLI supports working with objects in different configuration folders.

### Specifying Folders

All object-related commands require the `--folder` parameter to specify where objects should be created, updated, or retrieved from:

```bash
# Create an address in the Shared folder
scm set objects address --folder Shared --name web-server --ip-netmask 10.1.1.10/32
```

### Common Folder Operations

Working across multiple folders:

```bash
# List all address objects in the Shared folder
scm set objects address --list --folder Shared

# List all address objects in a different folder
scm set objects address --list --folder Branch-Office-1
```

## Bulk Operations

The CLI provides powerful bulk operations through the `load` commands.

### Loading Multiple Objects

Load multiple objects of the same type from a YAML file:

```bash
# Create multiple addresses defined in a YAML file
scm load objects address --folder Shared --file addresses.yaml
```

### YAML Structure for Bulk Loading

Each resource type has a specific YAML structure. Here's an example for address objects:

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

## Mock Mode

The CLI offers a mock mode for testing commands without making actual API calls.

### Enabling Mock Mode

Add the `--mock` flag to any command to run it in mock mode:

```bash
# Test creating an address without actually calling the API
scm set objects address --mock --folder Shared --name test-server --ip-netmask 10.1.1.10/32
```

This is useful for:

- Testing command syntax without making changes
- Validating YAML files before bulk loading
- Script development and testing

## Verbose Output

For troubleshooting, use verbose mode to see more details.

### Enabling Verbose Mode

Add the `--verbose` flag to see detailed operation information:

```bash
# Get verbose output when creating an address
scm set objects address --verbose --folder Shared --name test-server --ip-netmask 10.1.1.10/32
```

Verbose output includes:

- API request details
- Response data
- Timing information
- Error details (when failures occur)

## Using Environment Variables

The CLI can be configured using environment variables for authentication and other settings.

### Available Environment Variables

| Variable            | Purpose                           | Example                                        |
| ------------------- | --------------------------------- | ---------------------------------------------- |
| `SCM_CLIENT_ID`     | Client ID for authentication      | `export SCM_CLIENT_ID=client-id-value`         |
| `SCM_CLIENT_SECRET` | Client secret for authentication  | `export SCM_CLIENT_SECRET=client-secret-value` |
| `SCM_TSG_ID`        | Tenant Service Group ID           | `export SCM_TSG_ID=tsg-id-value`               |
| `SCM_CLI_LOG_LEVEL` | Logging level (DEBUG, INFO, etc.) | `export SCM_CLI_LOG_LEVEL=DEBUG`               |

## Script Integration

The CLI is designed to work well in scripts and automation.

### Exit Codes

The CLI uses standard exit codes:

- `0`: Success
- Non-zero: Failure

This allows for scripting with error checking:

```bash
#!/bin/bash
# Create an address and check if successful
scm set objects address --folder Shared --name test-server --ip-netmask 10.1.1.10/32
if [ $? -eq 0 ]; then
  echo "Address created successfully"
else
  echo "Failed to create address"
  exit 1
fi
```

### Parsing Output

For programmatic use, consider parsing the CLI output:

```bash
# Get a list of addresses in JSON format and process with jq
ADDRESSES=$(scm set objects address --list --folder Shared --output json | jq '.[] | select(.name | startswith("web-"))')
```

## Next Steps

- Explore the [CLI Reference](../cli/index.md) for detailed information on all available commands
- Check the [GitHub repository](https://github.com/cdot65/pan-scm-cli) for examples and updates
