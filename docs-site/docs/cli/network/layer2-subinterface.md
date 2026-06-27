# Layer2 Subinterface

Layer2 subinterfaces create VLAN-tagged subinterfaces operating in layer2 (switching) mode. The `scm` CLI provides commands to create, update, delete, and load layer2 subinterfaces.

## Overview

The `layer2-subinterface` commands allow you to:

- Create layer2 subinterfaces with VLAN tag configurations
- Update existing layer2 subinterface settings
- Delete layer2 subinterfaces that are no longer needed
- Bulk import layer2 subinterfaces from YAML files
- Export layer2 subinterfaces for backup or migration

## Set Layer2 Subinterface

Create or update a layer2 subinterface.

### Syntax

```bash
scm set network layer2-subinterface NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Subinterface name (positional) | Yes |
| `--vlan-tag TEXT` | VLAN tag (1-4096) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--parent-interface TEXT` | Parent interface name | No |
| `--comment TEXT` | Interface description | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create a Layer2 Subinterface

```bash
$ scm set network layer2-subinterface ethernet1/1.100 \
    --folder Texas \
    --vlan-tag 100 \
    --parent-interface ethernet1/1
---> 100%
Created layer2 subinterface: ethernet1/1.100 in folder Texas
```

#### Create with Description

```bash
$ scm set network layer2-subinterface ethernet1/2.200 \
    --folder Texas \
    --vlan-tag 200 \
    --parent-interface ethernet1/2 \
    --comment "Guest VLAN"
---> 100%
Created layer2 subinterface: ethernet1/2.200 in folder Texas
```

## Delete Layer2 Subinterface

Delete a layer2 subinterface from SCM.

### Syntax

```bash
scm delete network layer2-subinterface NAME [OPTIONS]
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
$ scm delete network layer2-subinterface ethernet1/1.100 --folder Texas --force
---> 100%
Deleted layer2 subinterface: ethernet1/1.100 from folder Texas
```

## Load Layer2 Subinterface

Load multiple layer2 subinterfaces from a YAML file.

### Syntax

```bash
scm load network layer2-subinterface [OPTIONS]
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
layer2_subinterfaces:
  - name: ethernet1/1.100
    folder: Texas
    vlan_tag: 100
    parent_interface: ethernet1/1

  - name: ethernet1/1.200
    folder: Texas
    vlan_tag: 200
    parent_interface: ethernet1/1
    comment: "Guest VLAN"
```

### Examples

#### Load with Original Locations

```bash
$ scm load network layer2-subinterface --file subinterfaces.yml
---> 100%
✓ Loaded layer2 subinterface: ethernet1/1.100
✓ Loaded layer2 subinterface: ethernet1/1.200

Successfully loaded 2 out of 2 layer2 subinterfaces from 'subinterfaces.yml'
```

#### Load with Folder Override

```bash
$ scm load network layer2-subinterface --file subinterfaces.yml --folder Austin
---> 100%
✓ Loaded layer2 subinterface: ethernet1/1.100
✓ Loaded layer2 subinterface: ethernet1/1.200

Successfully loaded 2 out of 2 layer2 subinterfaces from 'subinterfaces.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all layer2 subinterfaces
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show Layer2 Subinterface

Display layer2 subinterface objects.

### Syntax

```bash
scm show network layer2-subinterface [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Name of a specific subinterface | No |

\* One of --folder, --snippet, or --device is required.

:::note
When no `--name` is specified, all items are listed by default.
:::

### Examples

#### Show Specific Layer2 Subinterface

```bash
$ scm show network layer2-subinterface --folder Texas --name ethernet1/1.100
---> 100%
Layer2 Subinterface: ethernet1/1.100
  Location: Folder 'Texas'
  VLAN Tag: 100
  Parent Interface: ethernet1/1
```

#### List All Layer2 Subinterfaces (Default Behavior)

```bash
$ scm show network layer2-subinterface --folder Texas
---> 100%
Layer2 subinterfaces in folder 'Texas':
------------------------------------------------------------
Name: ethernet1/1.100
  VLAN Tag: 100
  Parent: ethernet1/1
------------------------------------------------------------
Name: ethernet1/1.200
  VLAN Tag: 200
  Parent: ethernet1/1
------------------------------------------------------------
```

## Backup Layer2 Subinterfaces

Backup all layer2 subinterface objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network layer2-subinterface [OPTIONS]
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
$ scm backup network layer2-subinterface --folder Texas
---> 100%
Successfully backed up 6 layer2 subinterfaces to layer2_subinterface_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network layer2-subinterface --folder Texas --file texas-l2-subinterfaces.yaml
---> 100%
Successfully backed up 6 layer2 subinterfaces to texas-l2-subinterfaces.yaml
```

## Best Practices

1. **Use Consistent VLAN Tags**: Coordinate VLAN tag assignments across all subinterfaces to avoid conflicts.
2. **Specify Parent Interface**: Always specify the parent interface for clarity and proper association.
3. **Add Descriptive Comments**: Document the purpose of each VLAN subinterface for easier management.
4. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
5. **Backup Before Changes**: Always backup existing subinterface configurations before making bulk modifications.
