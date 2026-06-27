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
| `virtual-wire` | Transparent inline mode between two interfaces |
| `tap` | Passive monitoring mode for traffic analysis |

## Set Security Zone

Create or update a security zone.

### Syntax

```bash
scm set network zone [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the security zone | Yes |
| `--folder TEXT` | Folder location | Yes |
| `--mode TEXT` | Zone protection mode (layer3, layer2, virtual-wire, tap) | Yes |
| `--description TEXT` | Description for the security zone | No |
| `--tags LIST` | List of tags to apply | No |
| `--enable-user-id BOOLEAN` | Enable User-ID for this zone | No |
| `--exclude-local-pan BOOLEAN` | Exclude local Panorama from User-ID distribution | No |
| `--log-setting TEXT` | Log forwarding profile | No |

### Examples

#### Create a Layer3 Security Zone

```bash
$ scm set network zone \
    --folder Shared \
    --name Trust \
    --mode layer3 \
    --enable-user-id true \
    --description "Internal trusted network zone"
---> 100%
Created security zone: Trust in folder Shared
```

#### Create a Virtual-Wire Security Zone

```bash
$ scm set network zone \
    --folder Shared \
    --name DMZ \
    --mode virtual-wire \
    --description "DMZ between trusted and untrusted networks"
---> 100%
Created security zone: DMZ in folder Shared
```

## Delete Security Zone

Delete a security zone from SCM.

### Syntax

```bash
scm delete network zone [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the security zone to delete | Yes |
| `--folder TEXT` | Folder location | Yes |
| `--force` | Skip confirmation prompt | No |

### Example

```bash
$ scm delete network zone --folder Shared --name DMZ --force
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
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--dry-run` | Preview changes without applying | No |

\* One of --folder, --snippet, or --device is required.

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

#### Load with Original Locations

```bash
$ scm load network zone --file security-zones.yml
---> 100%
✓ Loaded security zone: Trust
✓ Loaded security zone: Untrust
✓ Loaded security zone: DMZ

Successfully loaded 3 out of 3 security zones from 'security-zones.yml'
```

#### Load with Folder Override

```bash
$ scm load network zone --file security-zones.yml --folder Austin
---> 100%
✓ Loaded security zone: Trust
✓ Loaded security zone: Untrust
✓ Loaded security zone: DMZ

Successfully loaded 3 out of 3 security zones from 'security-zones.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all security zones
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show Security Zone

Display security zone objects.

### Syntax

```bash
scm show network zone [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Name of a specific security zone | No |

\* One of --folder, --snippet, or --device is required.

:::note
When no `--name` is specified, all items are listed by default.
:::

### Examples

#### Show Specific Security Zone

```bash
$ scm show network zone --folder Shared --name Trust
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
