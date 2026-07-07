# Tunnel Interface

Tunnel interfaces are virtual interfaces used for VPN tunnels and encapsulation. The `scm` CLI provides commands to create, update, delete, and load tunnel interfaces.

## Overview

The `tunnel-interface` commands allow you to:

- Create tunnel interfaces with IP addressing
- Update existing tunnel interface configurations
- Delete tunnel interfaces that are no longer needed
- Bulk import tunnel interfaces from YAML files
- Export tunnel interfaces for backup or migration

## Set Tunnel Interface

Create or update a tunnel interface.

### Syntax

```bash
scm set network tunnel-interface NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the tunnel interface | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes\* |
| `--snippet TEXT` | Snippet location | Yes\* |
| `--device TEXT` | Device location | Yes\* |
| `--comment TEXT` | Interface description | No |
| `--default-value TEXT` | Default interface (e.g. tunnel.1) | No |
| `--mtu INTEGER` | MTU (576-9216) | No |
| `--ip-json TEXT` | Static IPs as JSON | No |

\* Exactly one of `--folder`, `--snippet`, or `--device` is required.

### Examples

#### Create a Tunnel Interface

```bash
$ scm set network tunnel-interface tunnel.1 \
    --folder Texas \
    --ip-json '[{"name": "10.0.0.1/30"}]' \
    --comment "VPN tunnel"
---> 100%
Created tunnel interface: tunnel.1 in folder Texas
```

#### Create a Tunnel Interface with Custom MTU

```bash
$ scm set network tunnel-interface tunnel.2 \
    --folder Texas \
    --ip-json '[{"name": "10.0.0.5/30"}]' \
    --mtu 1400 \
    --comment "Site-to-site VPN"
---> 100%
Created tunnel interface: tunnel.2 in folder Texas
```

## Delete Tunnel Interface

Delete a tunnel interface from SCM.

### Syntax

```bash
scm delete network tunnel-interface NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the tunnel interface to delete | Yes |

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
$ scm delete network tunnel-interface tunnel.1 --folder Texas --force
---> 100%
Deleted tunnel interface: tunnel.1 from folder Texas
```

## Load Tunnel Interface

Load multiple tunnel interfaces from a YAML file.

### Syntax

```bash
scm load network tunnel-interface [OPTIONS]
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
tunnel_interfaces:
  - name: tunnel.1
    folder: Texas
    comment: "VPN tunnel to site A"
    ip:
      - name: "10.0.0.1/30"

  - name: tunnel.2
    folder: Texas
    comment: "VPN tunnel to site B"
    mtu: 1400
    ip:
      - name: "10.0.0.5/30"
```

### Examples

#### Load with Original Locations

```bash
$ scm load network tunnel-interface --file tunnels.yml
---> 100%
✓ Loaded tunnel interface: tunnel.1
✓ Loaded tunnel interface: tunnel.2

Successfully loaded 2 out of 2 tunnel interfaces from 'tunnels.yml'
```

#### Load with Folder Override

```bash
$ scm load network tunnel-interface --file tunnels.yml --folder Austin
---> 100%
✓ Loaded tunnel interface: tunnel.1
✓ Loaded tunnel interface: tunnel.2

Successfully loaded 2 out of 2 tunnel interfaces from 'tunnels.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all tunnel interfaces
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show Tunnel Interface

Display tunnel interface objects.

### Syntax

```bash
scm show network tunnel-interface [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the tunnel interface to show; omit to list all | No |

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

#### Show Specific Tunnel Interface

```bash
$ scm show network tunnel-interface tunnel.1 --folder Texas
---> 100%
Tunnel Interface: tunnel.1
  Location: Folder 'Texas'
  Comment: VPN tunnel
  IP: 10.0.0.1/30
```

#### List All Tunnel Interfaces (Default Behavior)

```bash
$ scm show network tunnel-interface --folder Texas
---> 100%
Tunnel interfaces in folder 'Texas':
------------------------------------------------------------
Name: tunnel.1
  Comment: VPN tunnel
  IP: 10.0.0.1/30
------------------------------------------------------------
Name: tunnel.2
  Comment: Site-to-site VPN
  IP: 10.0.0.5/30
------------------------------------------------------------
```

## Backup Tunnel Interfaces

Backup all tunnel interface objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network tunnel-interface [OPTIONS]
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
$ scm backup network tunnel-interface --folder Texas
---> 100%
Successfully backed up 6 tunnel interfaces to tunnel_interface_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network tunnel-interface --folder Texas --file texas-tunnels.yaml
---> 100%
Successfully backed up 6 tunnel interfaces to texas-tunnels.yaml
```

## Best Practices

1. **Use /30 Subnets**: Assign /30 subnets for point-to-point tunnel interfaces to conserve IP addresses.
2. **Set Appropriate MTU**: Reduce MTU below the physical interface to account for tunnel encapsulation overhead.
3. **Add Descriptive Comments**: Document which VPN or site each tunnel interface connects to.
4. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
5. **Backup Before Changes**: Always backup existing tunnel configurations before making bulk modifications.
