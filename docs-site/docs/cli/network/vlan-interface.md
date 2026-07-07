# VLAN Interface

VLAN interfaces are virtual interfaces associated with VLAN tags for inter-VLAN routing. The `scm` CLI provides commands to create, update, delete, and load VLAN interfaces.

## Overview

The `vlan-interface` commands allow you to:

- Create VLAN interfaces with IP addressing and VLAN tags
- Update existing VLAN interface configurations
- Delete VLAN interfaces that are no longer needed
- Bulk import VLAN interfaces from YAML files
- Export VLAN interfaces for backup or migration

## Set VLAN Interface

Create or update a VLAN interface.

### Syntax

```bash
scm set network vlan-interface NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the VLAN interface | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes\* |
| `--snippet TEXT` | Snippet location | Yes\* |
| `--device TEXT` | Device location | Yes\* |
| `--comment TEXT` | Interface description | No |
| `--default-value TEXT` | Default interface (e.g. vlan.100) | No |
| `--vlan-tag TEXT` | VLAN tag (1-4096) | No |
| `--mtu INTEGER` | MTU (576-9216) | No |
| `--ip-json TEXT` | Static IPs as JSON | No |
| `--dhcp-client-json TEXT` | DHCP client config as JSON | No |

\* Exactly one of `--folder`, `--snippet`, or `--device` is required.

### Examples

#### Create a VLAN Interface with Static IP

```bash
$ scm set network vlan-interface vlan.100 \
    --folder Texas \
    --vlan-tag 100 \
    --ip-json '[{"name": "10.0.100.1/24"}]' \
    --comment "VLAN 100 gateway"
---> 100%
Created VLAN interface: vlan.100 in folder Texas
```

#### Create a VLAN Interface with DHCP

```bash
$ scm set network vlan-interface vlan.200 \
    --folder Texas \
    --vlan-tag 200 \
    --dhcp-client-json '{"enable": true}' \
    --comment "DHCP-assigned VLAN"
---> 100%
Created VLAN interface: vlan.200 in folder Texas
```

## Delete VLAN Interface

Delete a VLAN interface from SCM.

### Syntax

```bash
scm delete network vlan-interface NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the VLAN interface to delete | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes\* |
| `--snippet TEXT` | Snippet location | Yes\* |
| `--device TEXT` | Device location | Yes\* |
| `--force` | Skip confirmation prompt | No |

\* Exactly one of `--folder`, `--snippet`, or `--device` is required.

### Example

```bash
$ scm delete network vlan-interface vlan.100 --folder Texas --force
---> 100%
Deleted VLAN interface: vlan.100 from folder Texas
```

## Load VLAN Interface

Load multiple VLAN interfaces from a YAML file.

### Syntax

```bash
scm load network vlan-interface [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying | No |

### YAML File Format

```yaml
---
vlan_interfaces:
  - name: vlan.100
    folder: Texas
    vlan_tag: 100
    comment: "VLAN 100 gateway"
    ip:
      - name: "10.0.100.1/24"

  - name: vlan.200
    folder: Texas
    vlan_tag: 200
    comment: "VLAN 200 gateway"
    ip:
      - name: "10.0.200.1/24"
```

### Examples

#### Load with Original Locations

```bash
$ scm load network vlan-interface --file vlans.yml
---> 100%
✓ Loaded VLAN interface: vlan.100
✓ Loaded VLAN interface: vlan.200

Successfully loaded 2 out of 2 VLAN interfaces from 'vlans.yml'
```

#### Load with Folder Override

```bash
$ scm load network vlan-interface --file vlans.yml --folder Austin
---> 100%
✓ Loaded VLAN interface: vlan.100
✓ Loaded VLAN interface: vlan.200

Successfully loaded 2 out of 2 VLAN interfaces from 'vlans.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all VLAN interfaces
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show VLAN Interface

Display VLAN interface objects.

### Syntax

```bash
scm show network vlan-interface [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the VLAN interface to show; omit to list all | No |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes\* |
| `--snippet TEXT` | Snippet location | Yes\* |
| `--device TEXT` | Device location | Yes\* |
| `--max-results INTEGER` | Maximum number of results to display | No |
| `--output [table\|json\|yaml]` | Output format (default: `table`) | No |

\* Exactly one of `--folder`, `--snippet`, or `--device` is required.

:::note
When no `NAME` argument is provided, all items are listed by default.
:::

### Examples

#### Show Specific VLAN Interface

```bash
$ scm show network vlan-interface vlan.100 --folder Texas
---> 100%
VLAN Interface: vlan.100
  Location: Folder 'Texas'
  VLAN Tag: 100
  Comment: VLAN 100 gateway
  IP: 10.0.100.1/24
```

#### List All VLAN Interfaces (Default Behavior)

```bash
$ scm show network vlan-interface --folder Texas
---> 100%
VLAN interfaces in folder 'Texas':
------------------------------------------------------------
Name: vlan.100
  VLAN Tag: 100
  IP: 10.0.100.1/24
------------------------------------------------------------
Name: vlan.200
  VLAN Tag: 200
  IP: 10.0.200.1/24
------------------------------------------------------------
```

## Backup VLAN Interfaces

Backup all VLAN interface objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network vlan-interface [OPTIONS]
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
$ scm backup network vlan-interface --folder Texas
---> 100%
Successfully backed up 8 VLAN interfaces to vlan_interface_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network vlan-interface --folder Texas --file texas-vlans.yaml
---> 100%
Successfully backed up 8 VLAN interfaces to texas-vlans.yaml
```

## Best Practices

1. **Match VLAN Tags to Network Design**: Ensure VLAN tags align with your switch and network infrastructure configuration.
2. **Use Consistent IP Schemes**: Assign IP addresses following a pattern (e.g., x.x.VLAN_ID.1/24) for easier management.
3. **Add Descriptive Comments**: Document the purpose of each VLAN interface for easier troubleshooting.
4. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
5. **Backup Before Changes**: Always backup existing VLAN configurations before making bulk modifications.
