# Advanced Topics

The `scm` CLI supports advanced workflows including multi-folder operations, bulk loading, mock mode testing, verbose output, environment variable configuration, and script integration. This guide covers techniques for power users and automation scenarios.

## Overview

This guide covers advanced CLI capabilities:

- Work with objects across multiple configuration folders
- Perform bulk operations using YAML files
- Test commands safely with mock mode
- Enable verbose output for troubleshooting
- Configure the CLI with environment variables
- Integrate the CLI into scripts and automation pipelines

## Prerequisites

Before using these advanced features, ensure you have:

- The `scm` CLI installed and authenticated (see [Getting Started](getting-started.md))
- Familiarity with basic CLI operations (see [Configuration Objects](configuration-objects.md))
- For scripting: a POSIX-compatible shell (bash, zsh) or PowerShell

## Core Concepts

### Folder-Based Organization

All object-related commands require the `--folder` parameter to specify where objects should be created, updated, or retrieved from. SCM uses folders to organize configurations hierarchically.

### Mock Mode

The `--mock` flag allows you to run any command without making actual API calls. This is useful for validating syntax, testing YAML files, and developing scripts.

### Verbose Output

The `--verbose` flag provides detailed information about API requests, responses, timing, and errors. Use it when troubleshooting unexpected behavior.

## Examples

### Working with Multiple Folders

#### Specifying Folders

```bash
$ scm set object address \
    --folder Shared \
    --name web-server \
    --ip-netmask 10.1.1.10/32
---> 100%
Created address: web-server in folder Shared
```

#### Listing Objects Across Folders

```bash
$ scm show object address --folder Shared
---> 100%
Addresses in folder 'Shared':
------------------------------------------------------------
Name: web-server
  IP Netmask: 10.1.1.10/32
------------------------------------------------------------
```

```bash
$ scm show object address --folder Branch-Office-1
---> 100%
Addresses in folder 'Branch-Office-1':
------------------------------------------------------------
Name: branch-server
  IP Netmask: 10.2.1.10/32
------------------------------------------------------------
```

### Bulk Operations

#### Loading Multiple Objects

Load multiple objects of the same type from a YAML file:

```bash
$ scm load object address --folder Shared --file addresses.yaml
---> 100%
✓ Loaded address: web-server-1
✓ Loaded address: web-server-2

Successfully loaded 2 out of 2 addresses from 'addresses.yaml'
```

#### YAML Structure for Bulk Loading

Each resource type has a specific YAML structure:

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

:::tip
Use YAML files for complex or repeatable configurations. Store them in
version control to track changes over time.
:::

### Mock Mode

#### Testing Commands Safely

Add the `--mock` flag to any command to run it without API calls:

```bash
$ scm set object address \
    --mock \
    --folder Shared \
    --name test-server \
    --ip-netmask 10.1.1.10/32
---> 100%
Created address: test-server in folder Shared (mock mode)
```

Mock mode is useful for:

- Testing command syntax without making changes
- Validating YAML files before bulk loading
- Script development and testing

### Verbose Output

#### Troubleshooting with Verbose Mode

Add the `--verbose` flag to see detailed operation information:

```bash
$ scm set object address \
    --verbose \
    --folder Shared \
    --name test-server \
    --ip-netmask 10.1.1.10/32
```

Verbose output includes:

- API request details
- Response data
- Timing information
- Error details (when failures occur)

### Environment Variables

#### Available Environment Variables

| Variable | Description | Example |
| --- | --- | --- |
| `SCM_CLIENT_ID` | Client ID for authentication | `export SCM_CLIENT_ID=client-id-value` |
| `SCM_CLIENT_SECRET` | Client secret for authentication | `export SCM_CLIENT_SECRET=client-secret-value` |
| `SCM_TSG_ID` | Tenant Service Group ID | `export SCM_TSG_ID=tsg-id-value` |
| `SCM_LOG_LEVEL` | Logging level (DEBUG, INFO, etc.) | `export SCM_LOG_LEVEL=DEBUG` |

:::info
For full details on configuration sources and precedence, see
[Configuration Management](configuration.md).
:::

### Script Integration

#### Exit Codes

The CLI uses standard exit codes for scripting:

| Exit Code | Meaning |
| --- | --- |
| `0` | Success |
| `1` | Error (details printed to stderr) |

:::info
Success output (e.g., "Created address: test-server") goes to **stdout**.
Error output (e.g., "Error creating address: ...") goes to **stderr**.
This separation allows clean output parsing in scripts.
:::

#### Error Checking in Scripts

```bash
#!/bin/bash
# Create an address and check if successful
scm set object address \
    --folder Shared \
    --name test-server \
    --ip-netmask 10.1.1.10/32 2>error.log

if [ $? -eq 0 ]; then
    echo "Address created successfully"
else
    echo "Failed to create address:"
    cat error.log
    exit 1
fi
```

#### Parsing CLI Output

```bash
# Get a list of addresses and process with jq
ADDRESSES=$(scm show object address \
    --folder Shared \
    --output json | jq '.[] | select(.name | startswith("web-"))')
```

## Best Practices

1. **Use mock mode for development**: Always test new scripts and YAML files with `--mock` before running against production.
2. **Organize objects by folder**: Use SCM folders to logically separate configurations by environment or location.
3. **Store YAML files in version control**: Track configuration changes alongside your infrastructure code.
4. **Use verbose mode for debugging**: Enable `--verbose` when troubleshooting unexpected behavior.
5. **Handle exit codes in scripts**: Always check return codes when integrating the CLI into automation pipelines.
6. **Use environment variables for CI/CD**: Set credentials via environment variables in automated workflows rather than hardcoding them.

## Next Steps

- Explore the [CLI Reference](../cli/index.md) for detailed information on all available commands
- Review [Data Formats](data-models.md) for YAML file structures and validation rules
- Check the [GitHub repository](https://github.com/cdot65/pan-scm-cli) for examples and updates
