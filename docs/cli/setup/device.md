# Device

Devices represent managed firewall appliances. Device management is read-only through the CLI.

## Show Device

```bash
scm show setup device [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name or serial number of the device | No |
| `--folder TEXT` | Filter devices by folder | No |

### Examples

```bash
# List all devices
$ scm show setup device

# Show a specific device
$ scm show setup device --name "PA-VM-01"

# Filter by folder
$ scm show setup device --folder Texas
```

!!! note
    Device management is read-only. Devices cannot be created, updated, or deleted through the CLI.
