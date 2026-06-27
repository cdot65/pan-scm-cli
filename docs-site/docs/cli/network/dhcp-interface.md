# DHCP Interface

DHCP interfaces configure DHCP server or relay functionality on network interfaces. The `scm` CLI provides commands to create, update, delete, and load DHCP interfaces.

## Overview

The `dhcp-interface` commands allow you to:

- Create DHCP interfaces with server or relay configurations
- Update existing DHCP interface settings
- Delete DHCP interfaces that are no longer needed
- Bulk import DHCP interfaces from YAML files
- Export DHCP interfaces for backup or migration

## Set DHCP Interface

Create or update a DHCP interface.

### Syntax

```bash
scm set network dhcp-interface NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Interface name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--server-json TEXT` | DHCP server config as JSON | No |
| `--relay-json TEXT` | DHCP relay config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create a DHCP Server Interface

```bash
$ scm set network dhcp-interface ethernet1/1 \
    --folder Texas \
    --server-json '{"ip_pool": [{"name": "pool1", "start_ip": "10.0.0.100", "end_ip": "10.0.0.200"}]}'
---> 100%
Created DHCP interface: ethernet1/1 in folder Texas
```

#### Create a DHCP Relay Interface

```bash
$ scm set network dhcp-interface ethernet1/2 \
    --folder Texas \
    --relay-json '{"server_addresses": ["10.0.1.1", "10.0.1.2"]}'
---> 100%
Created DHCP interface: ethernet1/2 in folder Texas
```

## Delete DHCP Interface

Delete a DHCP interface from SCM.

### Syntax

```bash
scm delete network dhcp-interface NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Interface name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete network dhcp-interface ethernet1/1 --folder Texas --force
---> 100%
Deleted DHCP interface: ethernet1/1 from folder Texas
```

## Load DHCP Interface

Load multiple DHCP interfaces from a YAML file.

### Syntax

```bash
scm load network dhcp-interface [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--dry-run` | Preview changes without applying | No |

\* One of --folder, --snippet, or --device is required.

### YAML File Format

```yaml
---
dhcp_interfaces:
  - name: ethernet1/1
    folder: Texas
    server:
      ip_pool:
        - name: "pool1"
          start_ip: "10.0.0.100"
          end_ip: "10.0.0.200"

  - name: ethernet1/2
    folder: Texas
    relay:
      server_addresses:
        - "10.0.1.1"
        - "10.0.1.2"
```

### Examples

#### Load with Original Locations

```bash
$ scm load network dhcp-interface --file dhcp.yml
---> 100%
✓ Loaded DHCP interface: ethernet1/1
✓ Loaded DHCP interface: ethernet1/2

Successfully loaded 2 out of 2 DHCP interfaces from 'dhcp.yml'
```

#### Load with Folder Override

```bash
$ scm load network dhcp-interface --file dhcp.yml --folder Austin
---> 100%
✓ Loaded DHCP interface: ethernet1/1
✓ Loaded DHCP interface: ethernet1/2

Successfully loaded 2 out of 2 DHCP interfaces from 'dhcp.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all DHCP interfaces
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show DHCP Interface

Display DHCP interface objects.

### Syntax

```bash
scm show network dhcp-interface [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Name of a specific interface | No |

\* One of --folder, --snippet, or --device is required.

:::note
When no `--name` is specified, all items are listed by default.
:::

### Examples

#### Show Specific DHCP Interface

```bash
$ scm show network dhcp-interface --folder Texas --name ethernet1/1
---> 100%
DHCP Interface: ethernet1/1
  Location: Folder 'Texas'
  Mode: Server
  IP Pool: 10.0.0.100 - 10.0.0.200
```

#### List All DHCP Interfaces (Default Behavior)

```bash
$ scm show network dhcp-interface --folder Texas
---> 100%
DHCP interfaces in folder 'Texas':
------------------------------------------------------------
Name: ethernet1/1
  Mode: Server
------------------------------------------------------------
Name: ethernet1/2
  Mode: Relay
------------------------------------------------------------
```

## Backup DHCP Interfaces

Backup all DHCP interface objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network dhcp-interface [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--file TEXT` | Custom output filename | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup network dhcp-interface --folder Texas
---> 100%
Successfully backed up 5 DHCP interfaces to dhcp_interface_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network dhcp-interface --folder Texas --file texas-dhcp.yaml
---> 100%
Successfully backed up 5 DHCP interfaces to texas-dhcp.yaml
```

## Best Practices

1. **Avoid IP Pool Overlap**: Ensure DHCP server IP pools do not overlap with static IP assignments on the network.
2. **Configure Redundant Relays**: When using DHCP relay, specify multiple server addresses for high availability.
3. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
4. **Backup Before Changes**: Always backup existing DHCP configurations before making bulk modifications.
5. **Document Pool Assignments**: Maintain records of which interfaces serve which DHCP pools for troubleshooting.
