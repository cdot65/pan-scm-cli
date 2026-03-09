# Layer3 Subinterface

Layer3 subinterfaces create VLAN-tagged subinterfaces operating in layer3 (routing) mode with IP addressing. The `scm` CLI provides commands to create, update, delete, and load layer3 subinterfaces.

## Overview

The `layer3-subinterface` commands allow you to:

- Create layer3 subinterfaces with VLAN tags and IP addressing
- Update existing layer3 subinterface configurations
- Delete layer3 subinterfaces that are no longer needed
- Bulk import layer3 subinterfaces from YAML files
- Export layer3 subinterfaces for backup or migration

## Set Layer3 Subinterface

Create or update a layer3 subinterface.

### Syntax

```bash
scm set network layer3-subinterface NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Subinterface name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--tag INT` | VLAN tag (1-4096) | No |
| `--parent-interface TEXT` | Parent interface name | No |
| `--comment TEXT` | Interface description | No |
| `--mtu INT` | MTU (576-9216) | No |
| `--ip-json TEXT` | Static IPs as JSON | No |
| `--dhcp-client-json TEXT` | DHCP client config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create a Layer3 Subinterface with Static IP

```bash
$ scm set network layer3-subinterface ethernet1/1.200 \
    --folder Texas \
    --tag 200 \
    --parent-interface ethernet1/1 \
    --mtu 1500 \
    --ip-json '[{"name": "10.0.2.1/24"}]'
---> 100%
Created layer3 subinterface: ethernet1/1.200 in folder Texas
```

#### Create a Layer3 Subinterface with DHCP

```bash
$ scm set network layer3-subinterface ethernet1/2.300 \
    --folder Texas \
    --tag 300 \
    --parent-interface ethernet1/2 \
    --dhcp-client-json '{"enable": true}' \
    --comment "DHCP-assigned VLAN"
---> 100%
Created layer3 subinterface: ethernet1/2.300 in folder Texas
```

## Delete Layer3 Subinterface

Delete a layer3 subinterface from SCM.

### Syntax

```bash
scm delete network layer3-subinterface NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Subinterface name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete network layer3-subinterface ethernet1/1.200 --folder Texas --force
---> 100%
Deleted layer3 subinterface: ethernet1/1.200 from folder Texas
```

## Load Layer3 Subinterface

Load multiple layer3 subinterfaces from a YAML file.

### Syntax

```bash
scm load network layer3-subinterface [OPTIONS]
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
layer3_subinterfaces:
  - name: ethernet1/1.200
    folder: Texas
    tag: 200
    parent_interface: ethernet1/1
    mtu: 1500
    ip:
      - name: "10.0.2.1/24"

  - name: ethernet1/1.300
    folder: Texas
    tag: 300
    parent_interface: ethernet1/1
    mtu: 1500
    ip:
      - name: "10.0.3.1/24"
```

### Examples

#### Load with Original Locations

```bash
$ scm load network layer3-subinterface --file subinterfaces.yml
---> 100%
✓ Loaded layer3 subinterface: ethernet1/1.200
✓ Loaded layer3 subinterface: ethernet1/1.300

Successfully loaded 2 out of 2 layer3 subinterfaces from 'subinterfaces.yml'
```

#### Load with Folder Override

```bash
$ scm load network layer3-subinterface --file subinterfaces.yml --folder Austin
---> 100%
✓ Loaded layer3 subinterface: ethernet1/1.200
✓ Loaded layer3 subinterface: ethernet1/1.300

Successfully loaded 2 out of 2 layer3 subinterfaces from 'subinterfaces.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all layer3 subinterfaces
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show Layer3 Subinterface

Display layer3 subinterface objects.

### Syntax

```bash
scm show network layer3-subinterface [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Name of a specific subinterface | No |

\* One of --folder, --snippet, or --device is required.

!!! note
    When no `--name` is specified, all items are listed by default.

### Examples

#### Show Specific Layer3 Subinterface

```bash
$ scm show network layer3-subinterface --folder Texas --name ethernet1/1.200
---> 100%
Layer3 Subinterface: ethernet1/1.200
  Location: Folder 'Texas'
  VLAN Tag: 200
  Parent Interface: ethernet1/1
  MTU: 1500
  IP: 10.0.2.1/24
```

#### List All Layer3 Subinterfaces (Default Behavior)

```bash
$ scm show network layer3-subinterface --folder Texas
---> 100%
Layer3 subinterfaces in folder 'Texas':
------------------------------------------------------------
Name: ethernet1/1.200
  VLAN Tag: 200
  IP: 10.0.2.1/24
------------------------------------------------------------
Name: ethernet1/1.300
  VLAN Tag: 300
  IP: 10.0.3.1/24
------------------------------------------------------------
```

## Backup Layer3 Subinterfaces

Backup all layer3 subinterface objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network layer3-subinterface [OPTIONS]
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
$ scm backup network layer3-subinterface --folder Texas
---> 100%
Successfully backed up 8 layer3 subinterfaces to layer3_subinterface_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network layer3-subinterface --folder Texas --file texas-l3-subinterfaces.yaml
---> 100%
Successfully backed up 8 layer3 subinterfaces to texas-l3-subinterfaces.yaml
```

## Best Practices

1. **Plan IP Addressing**: Assign subnet addresses consistently across layer3 subinterfaces to avoid overlap.
2. **Set Appropriate MTU**: Configure MTU to account for VLAN encapsulation overhead when needed.
3. **Use Consistent VLAN Tags**: Coordinate VLAN tag assignments with network switches and other devices.
4. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
5. **Backup Before Changes**: Always backup existing subinterface configurations before making bulk modifications.
