# Quarantined Device

Quarantined devices are endpoints isolated from the network due to security policy violations.

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
$ scm set object quarantined-device abc123 --serial-number SN12345
```

## Show Quarantined Devices

```bash
# List all quarantined devices
scm show object quarantined-device

# Filter by host ID
scm show object quarantined-device --host-id abc123

# Filter by serial number
scm show object quarantined-device --serial-number SN12345
```

## Delete Quarantined Device

```bash
scm delete object quarantined-device abc123
```

## Load Quarantined Devices

```bash
scm load object quarantined-device --file quarantined.yaml
```
