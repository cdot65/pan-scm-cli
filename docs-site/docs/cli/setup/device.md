# Device

Devices represent firewalls registered to Strata Cloud Manager. The CLI supports **read and update** operations on devices; it does **not** support create or delete. Devices enroll themselves through firewall-side registration — the CLI cannot add or remove them.

:::note[Update-only surface]
`scm set setup device` updates existing devices. It errors if the named device does not exist. There is no `scm delete setup device`.
:::

## Overview

The `device` commands allow you to:

- Update device properties (display name, description, folder assignment)
- Apply labels and snippets to devices
- View device details and connectivity status
- Bulk import device updates from YAML files
- Export devices for backup or migration

## Writable Fields

| Field | Flag | Description |
| --- | --- | --- |
| `name` | `NAME` argument | Lookup key (name or serial number). Required. |
| `display_name` | `--display-name` | Human-friendly display name. |
| `folder` | `--folder` | Folder to move the device into. |
| `description` | `--description` | Free-text description. |
| `labels` | `--labels` | Labels to apply. Repeatable; replaces current set. |
| `snippets` | `--snippets` | Snippet IDs to associate. Repeatable; replaces current set. |

Omitting a flag preserves the current value on the device. To clear a list field, use YAML load with an empty list.

## Set Device

Update an existing device.

### Syntax

```bash
scm set setup device NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Device name or serial number | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--display-name TEXT` | Human-friendly display name | No |
| `--folder TEXT` | Folder to move device into | No |
| `--description TEXT` | Free-text description | No |
| `--labels TEXT` | Labels to apply (repeatable) | No |
| `--snippets TEXT` | Snippet IDs to associate (repeatable) | No |

### Examples

#### Attach Labels to a Device

```bash
$ scm set setup device PA-VM-01 --labels production --labels west
---> 100%
Updated device: PA-VM-01
```

#### Move Device into a Folder

```bash
$ scm set setup device 0123456789 --folder Austin
---> 100%
Updated device: 0123456789
```

#### Set Multiple Fields at Once

```bash
$ scm set setup device PA-VM-01 \
    --display-name "Edge-FW" \
    --description "Edge firewall" \
    --labels production
---> 100%
Updated device: PA-VM-01
```

If the named device does not exist, the command errors with a message explaining that devices cannot be created via the CLI.

## Show Device

Display device objects.

### Syntax

```bash
scm show setup device [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name or serial number of the device to show; omit to list all | No |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Filter devices by folder | No |
| `--output, -o [table\|json\|yaml]` | Output format (default: table) | No |
| `--max-results INTEGER` | Maximum number of results to display | No |

:::note
When no options are specified, all devices are listed by default.
:::

### Examples

#### List All Devices (Default Behavior)

```bash
$ scm show setup device
---> 100%
Devices (2):
--------------------------------------------------------------------------------
Name: PA-VM-01
  Serial: 0123456789
  Model: PA-VM
  Folder: Texas
  Labels: production, west
  Connected: True
--------------------------------------------------------------------------------
Name: PA-VM-02
  Serial: 9876543210
  Model: PA-VM
  Folder: Texas
  Labels: staging
  Connected: False
--------------------------------------------------------------------------------
```

#### Show a Single Device

```bash
$ scm show setup device PA-VM-01
---> 100%
Device: PA-VM-01
================================================================================
Serial Number: 0123456789
Model: PA-VM
Family: vm
Hostname: PA-VM-01
Display Name: PA-VM-01 (display)
Description: Mock device PA-VM-01
Labels: production
Snippets: DNS-Best-Practice
Folder: Texas
Software Version: 11.1.0
Connected: True
Uptime: 30 days
ID: device-PA-VM-01
```

#### Show Device by Serial Number

```bash
$ scm show setup device 0123456789
---> 100%
Device: 0123456789
================================================================================
Serial Number: 0123456789
Model: PA-VM
Family: vm
Hostname: 0123456789
Display Name: 0123456789 (display)
Description: Mock device 0123456789
Labels: production
Snippets: DNS-Best-Practice
Folder: Texas
Software Version: 11.1.0
Connected: True
Uptime: 30 days
ID: device-0123456789
```

#### Filter Devices by Folder

```bash
$ scm show setup device --folder Texas
---> 100%
Devices (2):
--------------------------------------------------------------------------------
Name: PA-VM-01
  Serial: 0123456789
  Model: PA-VM
  Folder: Texas
  Labels: production, west
  Connected: True
--------------------------------------------------------------------------------
Name: PA-VM-02
  Serial: 9876543210
  Model: PA-VM
  Folder: Texas
  Labels: staging
  Connected: False
--------------------------------------------------------------------------------
```

The detail view prints the writable fields (`display_name`, `folder`, `description`, `labels`, `snippets`) alongside read-only info (`serial_number`, `model`, `hostname`, `software_version`, `is_connected`, `uptime`).

## Load Device

Load multiple device updates from a YAML file.

### Syntax

```bash
scm load setup device [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file PATH` | YAML file to load configurations from | Yes |
| `--dry-run` | Simulate execution without applying changes | No |

### YAML File Format

```yaml
---
devices:
  - name: PA-VM-01
    display_name: Edge-FW-01
    folder: Austin
    description: Edge firewall
    labels:
      - production
      - west
    snippets:
      - DNS-Best-Practice
  - name: PA-VM-02
    labels:
      - staging
```

Read-only fields present in the YAML (e.g. `serial_number`, `model`, `is_connected`) are ignored — they are safe to leave in backups you edit and reload.

### Examples

#### Load Device Updates from File

```bash
$ scm load setup device --file tests/data/devices.yaml
---> 100%
Updated device: PA-VM-01
Updated device: PA-VM-02

Processed 2 devices from tests/data/devices.yaml
```

#### Dry Run

```bash
$ scm load setup device --file devices.yaml --dry-run
---> 100%
Dry run mode: would apply the following configurations:
- description: Edge firewall 1
  display_name: Edge-FW-01
  folder: Austin
  labels:
  - production
  - west
  name: PA-VM-01
  snippets:
  - DNS-Best-Practice
- is_connected: false
  labels:
  - staging
  model: PA-VM
  name: PA-VM-02
  serial_number: '9876543210'
```

## Backup Device

Backup all device objects to a YAML file.

### Syntax

```bash
scm backup setup device [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Output filename for backup | No |

### Examples

#### Backup with Default Filename

```bash
$ scm backup setup device
---> 100%
Successfully backed up 5 devices to devices_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup setup device --file my-devices.yaml
---> 100%
Successfully backed up 5 devices to my-devices.yaml
```

Backup dumps all devices (read-only and writable fields) except the SCM identifier (`id`). The output is consumable by `scm load setup device`.

## Best Practices

1. **Use Display Names**: Set clear display names for devices to make them easily identifiable in the UI.
2. **Organize with Folders**: Move devices into appropriate folders to match your organizational structure.
3. **Apply Labels Consistently**: Use labels to categorize devices for easier filtering and management.
4. **Add Descriptions**: Include descriptions to document device purpose or configuration notes.
5. **Back Up Before Changes**: Export devices before making bulk updates to preserve your configuration.
6. **Use Dry Run for Bulk Imports**: Always preview bulk imports with `--dry-run` before applying changes.

## Related Topics

- [Label](label.md)
- [Folder](folder.md)
- [Snippet](snippet.md)
