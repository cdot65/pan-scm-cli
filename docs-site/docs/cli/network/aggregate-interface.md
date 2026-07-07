# Aggregate Interface

Aggregate interfaces combine multiple physical interfaces into a single logical interface for link aggregation (LACP). The `scm` CLI provides commands to create, update, delete, and load aggregate interfaces.

## Overview

The `aggregate-interface` commands allow you to:

- Create aggregate interfaces with layer2 or layer3 configurations
- Update existing aggregate interface settings
- Delete aggregate interfaces that are no longer needed
- Bulk import aggregate interfaces from YAML files
- Export aggregate interfaces for backup or migration

## Set Aggregate Interface

Create or update an aggregate interface.

### Syntax

```bash
scm set network aggregate-interface NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the aggregate interface | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes\* |
| `--snippet TEXT` | Snippet location | Yes\* |
| `--device TEXT` | Device location | Yes\* |
| `--comment TEXT` | Interface description | No |
| `--layer2-json TEXT` | Layer2 config as JSON | No |
| `--layer3-json TEXT` | Layer3 config as JSON | No |

\* Exactly one of `--folder`, `--snippet`, or `--device` is required.

### Examples

#### Create a Layer3 Aggregate Interface

```bash
$ scm set network aggregate-interface ae1 \
    --folder Texas \
    --layer3-json '{"mtu": 1500, "ip": [{"name": "10.0.0.1/24"}]}' \
    --comment "Aggregated uplink"
---> 100%
Created aggregate interface: ae1 in folder Texas
```

#### Create a Layer2 Aggregate Interface

```bash
$ scm set network aggregate-interface ae2 \
    --folder Texas \
    --layer2-json '{"lldp": {"enable": true}}' \
    --comment "Layer2 trunk"
---> 100%
Created aggregate interface: ae2 in folder Texas
```

## Delete Aggregate Interface

Delete an aggregate interface from SCM.

### Syntax

```bash
scm delete network aggregate-interface NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the aggregate interface to delete | Yes |

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
$ scm delete network aggregate-interface ae1 --folder Texas --force
---> 100%
Deleted aggregate interface: ae1 from folder Texas
```

## Load Aggregate Interface

Load multiple aggregate interfaces from a YAML file.

### Syntax

```bash
scm load network aggregate-interface [OPTIONS]
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
aggregate_interfaces:
  - name: ae1
    folder: Texas
    comment: "Aggregated uplink"
    layer3:
      mtu: 1500
      ip:
        - name: "10.0.0.1/24"

  - name: ae2
    folder: Texas
    comment: "Layer2 trunk"
    layer2:
      lldp:
        enable: true
```

### Examples

#### Load with Original Locations

```bash
$ scm load network aggregate-interface --file interfaces.yml
---> 100%
✓ Loaded aggregate interface: ae1
✓ Loaded aggregate interface: ae2

Successfully loaded 2 out of 2 aggregate interfaces from 'interfaces.yml'
```

#### Load with Folder Override

```bash
$ scm load network aggregate-interface --file interfaces.yml --folder Austin
---> 100%
✓ Loaded aggregate interface: ae1
✓ Loaded aggregate interface: ae2

Successfully loaded 2 out of 2 aggregate interfaces from 'interfaces.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all aggregate interfaces
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show Aggregate Interface

Display aggregate interface objects.

### Syntax

```bash
scm show network aggregate-interface [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the aggregate interface to show; omit to list all | No |

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

#### Show Specific Aggregate Interface

```bash
$ scm show network aggregate-interface ae1 --folder Texas
---> 100%
Aggregate Interface: ae1
  Location: Folder 'Texas'
  Comment: Aggregated uplink
  Layer3 MTU: 1500
```

#### List All Aggregate Interfaces (Default Behavior)

```bash
$ scm show network aggregate-interface --folder Texas
---> 100%
Aggregate interfaces in folder 'Texas':
------------------------------------------------------------
Name: ae1
  Comment: Aggregated uplink
  Mode: Layer3
------------------------------------------------------------
Name: ae2
  Comment: Layer2 trunk
  Mode: Layer2
------------------------------------------------------------
```

## Backup Aggregate Interfaces

Backup all aggregate interface objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network aggregate-interface [OPTIONS]
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
$ scm backup network aggregate-interface --folder Texas
---> 100%
Successfully backed up 4 aggregate interfaces to aggregate_interface_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network aggregate-interface --folder Texas --file texas-ae-interfaces.yaml
---> 100%
Successfully backed up 4 aggregate interfaces to texas-ae-interfaces.yaml
```

## Best Practices

1. **Use Descriptive Comments**: Add comments to each aggregate interface describing its purpose and member links.
2. **Plan IP Addressing**: Ensure layer3 aggregate interfaces have proper IP addressing before assigning to security zones.
3. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
4. **Backup Before Changes**: Always backup existing aggregate interface configurations before making bulk modifications.
5. **Use Consistent Naming**: Follow a naming convention like `ae1`, `ae2` for aggregate interface names.
