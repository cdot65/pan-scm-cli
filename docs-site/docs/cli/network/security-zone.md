# Security Zone

Security zones are logical divisions of the network that define boundaries for traffic control and enforce security policies. The `scm` CLI provides commands to create, update, delete, and load security zones.

## Overview

The `zone` commands allow you to:

- Create security zones with layer3, layer2, virtual-wire, or TAP mode
- Update existing security zone configurations
- Delete security zones that are no longer needed
- Bulk import security zones from YAML files
- Export security zones for backup or migration

## Zone Modes

| Mode | Description |
| --- | --- |
| `layer3` | Standard routed mode with IP addressing |
| `layer2` | Switched mode for bridging traffic |
| `external` | Zone for traffic between virtual systems |
| `virtual-wire` | Transparent inline mode between two interfaces |
| `tunnel` | Zone for tunnel interfaces |
| `tap` | Passive monitoring mode for traffic analysis |

## Set Security Zone

Create or update a security zone.

### Syntax

```bash
scm set network zone NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the security zone | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes\* |
| `--snippet TEXT` | Snippet location | Yes\* |
| `--device TEXT` | Device location | Yes\* |
| `--mode TEXT` | Zone mode (layer2, layer3, external, virtual-wire, tunnel, tap) | Yes |
| `--interfaces TEXT` | List of interfaces | No |
| `--enable-user-id` | Enable user identification | No |

\* Exactly one of `--folder`, `--snippet`, or `--device` is required.

### Examples

#### Create a Layer3 Security Zone

```bash
$ scm set network zone Trust \
    --folder Shared \
    --mode layer3 \
    --enable-user-id
---> 100%
Created security zone: Trust in folder Shared
```

#### Create a Virtual-Wire Security Zone

```bash
$ scm set network zone DMZ \
    --folder Shared \
    --mode virtual-wire
---> 100%
Created security zone: DMZ in folder Shared
```

## Delete Security Zone

Delete a security zone from SCM.

### Syntax

```bash
scm delete network zone NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the security zone to delete | Yes |

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
$ scm delete network zone DMZ --folder Shared --force
---> 100%
Deleted security zone: DMZ from folder Shared
```

## Load Security Zone

Load multiple security zones from a YAML file.

### Syntax

```bash
scm load network zone [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing security zone definitions | Yes |
| `--dry-run` | Preview changes without applying | No |

### YAML File Format

```yaml
---
security_zones:
  - name: Trust
    folder: Shared
    description: "Internal trusted network zone"
    mode: layer3
    enable_user_id: true
    tags:
      - internal
      - trusted

  - name: Untrust
    folder: Shared
    description: "External untrusted network zone"
    mode: layer3
    enable_user_id: false
    tags:
      - external
      - untrusted

  - name: DMZ
    folder: Shared
    description: "DMZ between trusted and untrusted networks"
    mode: virtual-wire
    enable_user_id: true
    tags:
      - dmz
```

### Examples

#### Load Security Zones

```bash
$ scm load network zone --file security-zones.yml
---> 100%
✓ Loaded security zone: Trust
✓ Loaded security zone: Untrust
✓ Loaded security zone: DMZ

Successfully loaded 3 out of 3 security zones from 'security-zones.yml'
```

:::note
Each security zone is loaded into the container (folder, snippet, or device) specified
in the YAML file.
:::

## Show Security Zone

Display security zone objects.

### Syntax

```bash
scm show network zone [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the security zone to show; omit to list all | No |

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

#### Show Specific Security Zone

```bash
$ scm show network zone Trust --folder Shared
---> 100%
Security Zone: Trust
  Location: Folder 'Shared'
  Mode: layer3
  Description: Internal trusted network zone
  User-ID: enabled
  Tags: internal, trusted
```

#### List All Security Zones (Default Behavior)

```bash
$ scm show network zone --folder Shared
---> 100%
Security zones in folder 'Shared':
------------------------------------------------------------
Name: Trust
  Mode: layer3
  User-ID: enabled
------------------------------------------------------------
Name: Untrust
  Mode: layer3
  User-ID: disabled
------------------------------------------------------------
Name: DMZ
  Mode: virtual-wire
  User-ID: enabled
------------------------------------------------------------
```

## Backup Security Zones

Backup all security zone objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network zone [OPTIONS]
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
$ scm backup network zone --folder Shared
---> 100%
Successfully backed up 5 security zones to security_zone_folder_shared_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network zone --folder Shared --file shared-zones.yaml
---> 100%
Successfully backed up 5 security zones to shared-zones.yaml
```

## Best Practices

1. **Use Descriptive Names**: Name zones clearly to indicate their security posture (Trust, Untrust, DMZ).
2. **Enable User-ID Selectively**: Only enable User-ID on zones where user identification is needed for policy enforcement.
3. **Choose Appropriate Mode**: Select the zone mode (layer3, layer2, virtual-wire, tap) that matches your network topology.
4. **Apply Tags for Organization**: Use tags to categorize and organize security zones for easier management.
5. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
6. **Backup Before Changes**: Always backup existing security zone configurations before making bulk modifications.
