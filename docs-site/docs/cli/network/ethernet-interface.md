# Ethernet Interface

Ethernet interfaces configure physical network ports with layer2, layer3, or TAP mode settings. The `scm` CLI provides commands to create, update, delete, and load ethernet interfaces.

## Overview

The `ethernet-interface` commands allow you to:

- Create ethernet interfaces with layer2, layer3, or TAP configurations
- Update existing ethernet interface settings including link speed and duplex
- Delete ethernet interfaces that are no longer needed
- Bulk import ethernet interfaces from YAML files
- Export ethernet interfaces for backup or migration

## Set Ethernet Interface

Create or update an ethernet interface.

### Syntax

```bash
scm set network ethernet-interface NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Interface name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--comment TEXT` | Interface description | No |
| `--default-value TEXT` | Physical interface (e.g. ethernet1/1) | No |
| `--link-speed TEXT` | Link speed (auto, 10, 100, 1000, 10000) | No |
| `--link-duplex TEXT` | Link duplex (auto, half, full) | No |
| `--link-state TEXT` | Link state (auto, up, down) | No |
| `--layer2-json TEXT` | Layer2 config as JSON | No |
| `--layer3-json TEXT` | Layer3 config as JSON | No |
| `--tap-json TEXT` | TAP config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create a Layer3 Ethernet Interface

```bash
$ scm set network ethernet-interface ethernet1/1 \
    --folder Texas \
    --layer3-json '{"mtu": 1500, "ip": [{"name": "10.0.0.1/24"}]}' \
    --link-speed auto \
    --comment "WAN uplink"
---> 100%
Created ethernet interface: ethernet1/1 in folder Texas
```

#### Create a TAP Mode Interface

```bash
$ scm set network ethernet-interface ethernet1/3 \
    --folder Texas \
    --tap-json '{}' \
    --comment "Traffic monitoring"
---> 100%
Created ethernet interface: ethernet1/3 in folder Texas
```

## Delete Ethernet Interface

Delete an ethernet interface from SCM.

### Syntax

```bash
scm delete network ethernet-interface NAME [OPTIONS]
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
$ scm delete network ethernet-interface ethernet1/1 --folder Texas --force
---> 100%
Deleted ethernet interface: ethernet1/1 from folder Texas
```

## Load Ethernet Interface

Load multiple ethernet interfaces from a YAML file.

### Syntax

```bash
scm load network ethernet-interface [OPTIONS]
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
ethernet_interfaces:
  - name: ethernet1/1
    folder: Texas
    comment: "WAN uplink"
    link_speed: auto
    layer3:
      mtu: 1500
      ip:
        - name: "10.0.0.1/24"

  - name: ethernet1/2
    folder: Texas
    comment: "LAN interface"
    layer3:
      mtu: 1500
      ip:
        - name: "192.168.1.1/24"
```

### Examples

#### Load with Original Locations

```bash
$ scm load network ethernet-interface --file interfaces.yml
---> 100%
✓ Loaded ethernet interface: ethernet1/1
✓ Loaded ethernet interface: ethernet1/2

Successfully loaded 2 out of 2 ethernet interfaces from 'interfaces.yml'
```

#### Load with Folder Override

```bash
$ scm load network ethernet-interface --file interfaces.yml --folder Austin
---> 100%
✓ Loaded ethernet interface: ethernet1/1
✓ Loaded ethernet interface: ethernet1/2

Successfully loaded 2 out of 2 ethernet interfaces from 'interfaces.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all ethernet interfaces
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show Ethernet Interface

Display ethernet interface objects.

### Syntax

```bash
scm show network ethernet-interface [OPTIONS]
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

#### Show Specific Ethernet Interface

```bash
$ scm show network ethernet-interface --folder Texas --name ethernet1/1
---> 100%
Ethernet Interface: ethernet1/1
  Location: Folder 'Texas'
  Comment: WAN uplink
  Link Speed: auto
  Mode: Layer3
  MTU: 1500
```

#### List All Ethernet Interfaces (Default Behavior)

```bash
$ scm show network ethernet-interface --folder Texas
---> 100%
Ethernet interfaces in folder 'Texas':
------------------------------------------------------------
Name: ethernet1/1
  Comment: WAN uplink
  Mode: Layer3
------------------------------------------------------------
Name: ethernet1/2
  Comment: LAN interface
  Mode: Layer3
------------------------------------------------------------
```

## Backup Ethernet Interfaces

Backup all ethernet interface objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network ethernet-interface [OPTIONS]
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
$ scm backup network ethernet-interface --folder Texas
---> 100%
Successfully backed up 8 ethernet interfaces to ethernet_interface_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network ethernet-interface --folder Texas --file texas-interfaces.yaml
---> 100%
Successfully backed up 8 ethernet interfaces to texas-interfaces.yaml
```

## Best Practices

1. **Set Link Speed Explicitly**: While auto-negotiation works in most cases, set link speed explicitly for critical uplinks.
2. **Use Descriptive Comments**: Add comments describing the purpose and connected device for each interface.
3. **Plan IP Addressing**: Assign IP addresses following a consistent addressing scheme across all interfaces.
4. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
5. **Backup Before Changes**: Always backup existing interface configurations before making bulk modifications.
