# CLI Reference

The `pan-scm` command-line interface is organized into a logical structure that makes it easy to manage resources in Strata Cloud Manager.

## Command Structure

All commands follow this pattern:

```bash
scm <action> <resource-type> <resource> [options]
```

Where:

- `<action>`: The operation to perform (set, delete, load)
- `<resource-type>`: Category of resource (objects, deployment, network, security)
- `<resource>`: Specific resource type (address, address-group, zone, etc.)
- `[options]`: Resource-specific parameters and global options

## Available Commands

### Objects

Commands for managing configuration objects:

| Command                                                                             | Description                           |
| ----------------------------------------------------------------------------------- | ------------------------------------- |
| [`scm set objects address`](objects/address.md)                                     | Create or update an address object    |
| [`scm delete objects address`](objects/address.md#delete-address)                   | Delete an address object              |
| [`scm load objects address`](objects/address.md#load-addresses)                     | Bulk import address objects from YAML |
| [`scm set objects address-group`](objects/address-group.md)                         | Create or update an address group     |
| [`scm delete objects address-group`](objects/address-group.md#delete-address-group) | Delete an address group               |
| [`scm load objects address-group`](objects/address-group.md#load-address-groups)    | Bulk import address groups from YAML  |

### Security

Commands for managing security policies:

| Command                                                                | Description                          |
| ---------------------------------------------------------------------- | ------------------------------------ |
| [`scm set security rule`](security/rules.md)                           | Create or update a security rule     |
| [`scm delete security rule`](security/rules.md#delete-security-rule)   | Delete a security rule               |
| [`scm load security rule`](security/rules.md#load-security-rules)      | Bulk import security rules from YAML |
| [`scm set security rule --move`](security/rules.md#move-security-rule) | Move a security rule position        |

### Network

Commands for managing network configurations:

| Command                                                                             | Description                          |
| ----------------------------------------------------------------------------------- | ------------------------------------ |
| [`scm set network security-zone`](network/security-zone.md)                         | Create or update a security zone     |
| [`scm delete network security-zone`](network/security-zone.md#delete-security-zone) | Delete a security zone               |
| [`scm load network security-zone`](network/security-zone.md#load-security-zones)    | Bulk import security zones from YAML |

### Deployment

Commands for managing deployment configurations:

| Command                                                                                        | Description                                 |
| ---------------------------------------------------------------------------------------------- | ------------------------------------------- |
| [`scm set deployment bandwidth`](deployment/bandwidth.md)                                      | Create or update bandwidth allocation       |
| [`scm delete deployment bandwidth`](deployment/bandwidth.md#delete-bandwidth-allocation)       | Delete a bandwidth allocation               |
| [`scm load deployment bandwidth`](deployment/bandwidth.md#load-bandwidth-allocations)          | Bulk import bandwidth allocations from YAML |
| [`scm set deployment bandwidth --assign`](deployment/bandwidth.md#assign-bandwidth-allocation) | Assign bandwidth allocation to SPNs         |

## Global Options

Options that apply to all commands:

| Option      | Description                                  |
| ----------- | -------------------------------------------- |
| `--help`    | Show help message for any command            |
| `--version` | Show the CLI version information             |
| `--verbose` | Enable verbose output for additional details |
| `--mock`    | Run in mock mode (no actual API connections) |

## Working with the CLI

For more detailed examples and use cases, refer to the specific command documentation linked above or see the [Getting Started](../about/getting-started.md) guide.
