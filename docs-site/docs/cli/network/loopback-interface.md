# Loopback Interface

Loopback interfaces are virtual interfaces used for management access, routing protocols, and NAT. The `scm` CLI provides commands to create, update, delete, and load loopback interfaces.

## Overview

The `loopback-interface` commands allow you to:

- Create loopback interfaces with IP addressing
- Update existing loopback interface configurations
- Delete loopback interfaces that are no longer needed
- Bulk import loopback interfaces from YAML files
- Export loopback interfaces for backup or migration

## Set Loopback Interface

Create or update a loopback interface.

### Syntax

```bash
scm set network loopback-interface NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the loopback interface | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes\* |
| `--snippet TEXT` | Snippet location | Yes\* |
| `--device TEXT` | Device location | Yes\* |
| `--comment TEXT` | Interface description | No |
| `--default-value TEXT` | Default interface (e.g. loopback.1) | No |
| `--mtu INTEGER` | MTU (576-9216) | No |
| `--ip-json TEXT` | Static IPs as JSON | No |
| `--ipv6-json TEXT` | IPv6 config as JSON | No |

\* Exactly one of `--folder`, `--snippet`, or `--device` is required.

### Examples

#### Create a Loopback Interface

```bash
$ scm set network loopback-interface loopback.1 \
    --folder Texas \
    --ip-json '[{"name": "10.0.0.1/32"}]' \
    --comment "Management loopback"
---> 100%
Created loopback interface: loopback.1 in folder Texas
```

#### Create a Loopback with IPv6

```bash
$ scm set network loopback-interface loopback.2 \
    --folder Texas \
    --ip-json '[{"name": "10.0.0.2/32"}]' \
    --ipv6-json '{"addresses": [{"name": "fd00::1/128"}]}' \
    --comment "Dual-stack loopback"
---> 100%
Created loopback interface: loopback.2 in folder Texas
```

## Delete Loopback Interface

Delete a loopback interface from SCM.

### Syntax

```bash
scm delete network loopback-interface NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the loopback interface to delete | Yes |

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
$ scm delete network loopback-interface loopback.1 --folder Texas --force
---> 100%
Deleted loopback interface: loopback.1 from folder Texas
```

## Load Loopback Interface

Load multiple loopback interfaces from a YAML file.

### Syntax

```bash
scm load network loopback-interface [OPTIONS]
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
loopback_interfaces:
  - name: loopback.1
    folder: Texas
    comment: "Management loopback"
    ip:
      - name: "10.0.0.1/32"

  - name: loopback.2
    folder: Texas
    comment: "Routing protocol loopback"
    ip:
      - name: "10.0.0.2/32"
```

### Examples

#### Load with Original Locations

```bash
$ scm load network loopback-interface --file loopbacks.yml
---> 100%
✓ Loaded loopback interface: loopback.1
✓ Loaded loopback interface: loopback.2

Successfully loaded 2 out of 2 loopback interfaces from 'loopbacks.yml'
```

#### Load with Folder Override

```bash
$ scm load network loopback-interface --file loopbacks.yml --folder Austin
---> 100%
✓ Loaded loopback interface: loopback.1
✓ Loaded loopback interface: loopback.2

Successfully loaded 2 out of 2 loopback interfaces from 'loopbacks.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all loopback interfaces
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show Loopback Interface

Display loopback interface objects.

### Syntax

```bash
scm show network loopback-interface [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the loopback interface to show; omit to list all | No |

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

#### Show Specific Loopback Interface

```bash
$ scm show network loopback-interface loopback.1 --folder Texas
---> 100%
Loopback Interface: loopback.1
  Location: Folder 'Texas'
  Comment: Management loopback
  IP: 10.0.0.1/32
```

#### List All Loopback Interfaces (Default Behavior)

```bash
$ scm show network loopback-interface --folder Texas
---> 100%
Loopback interfaces in folder 'Texas':
------------------------------------------------------------
Name: loopback.1
  Comment: Management loopback
  IP: 10.0.0.1/32
------------------------------------------------------------
Name: loopback.2
  Comment: Routing protocol loopback
  IP: 10.0.0.2/32
------------------------------------------------------------
```

## Backup Loopback Interfaces

Backup all loopback interface objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network loopback-interface [OPTIONS]
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
$ scm backup network loopback-interface --folder Texas
---> 100%
Successfully backed up 4 loopback interfaces to loopback_interface_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network loopback-interface --folder Texas --file texas-loopbacks.yaml
---> 100%
Successfully backed up 4 loopback interfaces to texas-loopbacks.yaml
```

## Best Practices

1. **Use /32 Addresses**: Assign /32 subnet masks to loopback interfaces as they represent a single host address.
2. **Dedicate for Routing**: Use dedicated loopback interfaces for routing protocol peering (BGP, OSPF).
3. **Add Descriptive Comments**: Document the purpose of each loopback interface for easier management.
4. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
5. **Backup Before Changes**: Always backup existing loopback configurations before making bulk modifications.
