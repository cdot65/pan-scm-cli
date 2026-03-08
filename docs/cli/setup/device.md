# Device

Devices represent managed firewall appliances in Strata Cloud Manager. Device management is read-only through the CLI.

## Show Device

Display devices.

### Syntax

```bash
scm show setup device [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name or serial number of the device | No |
| `--folder TEXT` | Filter devices by folder | No |

### Examples

#### List All Devices

```bash
$ scm show setup device
---> 100%
Devices (3):
--------------------------------------------------------------------------------
Name: PA-VM-01
  Serial: 012345678901
  Model: PA-VM
  Folder: Texas
  Connected: True
--------------------------------------------------------------------------------
Name: PA-3260-01
  Serial: 098765432109
  Model: PA-3260
  Folder: Austin
  Connected: True
--------------------------------------------------------------------------------
```

#### Show a Specific Device

```bash
$ scm show setup device --name "PA-VM-01"
---> 100%
Device: PA-VM-01
================================================================================
Serial Number: 012345678901
Model: PA-VM
Family: vm
Hostname: PA-VM-01
IP Address: 10.0.1.100
Folder: Texas
Software Version: 11.1.0
Connected: True
```

#### Filter by Folder

```bash
$ scm show setup device --folder Texas
---> 100%
Devices (2):
--------------------------------------------------------------------------------
Name: PA-VM-01
  Serial: 012345678901
  Model: PA-VM
  Folder: Texas
  Connected: True
--------------------------------------------------------------------------------
Name: PA-VM-02
  Serial: 012345678902
  Model: PA-VM
  Folder: Texas
  Connected: False
--------------------------------------------------------------------------------
```

!!! note
    Device management is read-only. Devices cannot be created, updated, or deleted
    through the CLI.
