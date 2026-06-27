# Quarantined Device

Quarantined devices are endpoints isolated from the network due to security policy violations. The `scm` CLI provides commands to create, show, delete, and load quarantined device entries.

## Overview

The `quarantined-device` commands allow you to:

- Create quarantined device entries by host ID
- View quarantined devices with optional filtering
- Delete quarantined device entries
- Bulk import quarantined devices from YAML files

## Set Quarantined Device

Create a quarantined device entry.

### Syntax

```bash
scm set object quarantined-device HOST_ID [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `HOST_ID` | Host ID of the device (positional) | Yes |
| `--serial-number TEXT` | Serial number of the device | No |

### Example

```bash
$ scm set object quarantined-device abc123 \
    --serial-number SN12345
---> 100%
Created quarantined device: abc123
```

## Delete Quarantined Device

Delete a quarantined device entry.

### Syntax

```bash
scm delete object quarantined-device HOST_ID
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `HOST_ID` | Host ID of the device (positional) | Yes |
| `--force` | Skip confirmation prompt | No |

### Example

```bash
$ scm delete object quarantined-device abc123 --force
---> 100%
Deleted quarantined device: abc123
```

## Load Quarantined Devices

Load multiple quarantined device entries from a YAML file.

### Syntax

```bash
scm load object quarantined-device [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing quarantined device definitions | Yes |

### YAML File Format

```yaml
---
quarantined_devices:
  - host_id: abc123
    serial_number: SN12345

  - host_id: def456
    serial_number: SN67890
```

### Example

```bash
$ scm load object quarantined-device --file quarantined.yaml
---> 100%
✓ Loaded quarantined device: abc123
✓ Loaded quarantined device: def456

Successfully loaded 2 out of 2 quarantined devices from 'quarantined.yaml'
```

## Show Quarantined Device

Display quarantined device entries.

### Syntax

```bash
scm show object quarantined-device [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--host-id TEXT` | Filter by host ID | No |
| `--serial-number TEXT` | Filter by serial number | No |

:::note
When no filters are specified, all quarantined devices are listed by default.
:::

### Examples

#### List All Quarantined Devices

```bash
$ scm show object quarantined-device
---> 100%
Quarantined Devices:
------------------------------------------------------------
Host ID: abc123
  Serial Number: SN12345
------------------------------------------------------------
Host ID: def456
  Serial Number: SN67890
------------------------------------------------------------
```

#### Filter by Host ID

```bash
$ scm show object quarantined-device --host-id abc123
---> 100%
Quarantined Device: abc123
  Serial Number: SN12345
```

## Best Practices

1. **Document Reasons**: Track why devices are quarantined outside of SCM.
2. **Regular Review**: Periodically review quarantined devices and release compliant ones.
3. **Use YAML for Bulk Operations**: For managing multiple quarantine entries, use YAML files.
4. **Serial Number Tracking**: Always include serial numbers for device identification.
