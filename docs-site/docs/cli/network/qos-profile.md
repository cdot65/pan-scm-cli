# QoS Profile

QoS profiles define bandwidth allocation and traffic class settings for network connections. The `scm` CLI provides commands to create, update, delete, and manage QoS profiles.

## Overview

The `qos-profile` commands allow you to:

- Create QoS profiles with aggregate bandwidth and class bandwidth type settings
- Update existing QoS profile configurations
- Delete QoS profiles that are no longer needed
- Bulk import QoS profiles from YAML files
- Export QoS profiles for backup or migration

:::warning[Folder Restriction]
QoS profiles only support **"Remote Networks"** and **"Service Connections"** folders. Using any other folder will result in an error.
:::

## Set QoS Profile

Create or update a QoS profile.

### Syntax

```bash
scm set network qos-profile [OPTIONS] NAME
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the QoS profile | Yes |
| `--folder TEXT` | Folder location (must be "Remote Networks" or "Service Connections") | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--aggregate-bandwidth-json TEXT` | Aggregate bandwidth config as JSON | No |
| `--class-bandwidth-type-json TEXT` | Class bandwidth type config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create a QoS Profile

```bash
$ scm set network qos-profile my-qos \
    --folder "Remote Networks" \
    --aggregate-bandwidth-json '{"egress_max": 100, "egress_guaranteed": 50}'
---> 100%
Created QoS profile: my-qos in Remote Networks
```

#### Create in Service Connections

```bash
$ scm set network qos-profile sc-qos \
    --folder "Service Connections" \
    --aggregate-bandwidth-json '{"egress_max": 200}'
---> 100%
Created QoS profile: sc-qos in Service Connections
```

## Delete QoS Profile

Delete a QoS profile from SCM.

### Syntax

```bash
scm delete network qos-profile [OPTIONS] NAME
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the QoS profile to delete | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete network qos-profile my-qos --folder "Remote Networks" --force
---> 100%
Deleted QoS profile: my-qos from Remote Networks
```

## Load QoS Profile

Load multiple QoS profiles from a YAML file.

### Syntax

```bash
scm load network qos-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing QoS profile definitions | Yes |
| `--folder TEXT` | Override folder location | No |
| `--snippet TEXT` | Override snippet location | No |
| `--device TEXT` | Override device location | No |
| `--dry-run` | Preview changes without applying | No |

### YAML File Format

```yaml
---
qos_profiles:
  - name: remote-qos
    folder: "Remote Networks"
    aggregate_bandwidth:
      egress_max: 100
      egress_guaranteed: 50
    class_bandwidth_type:
      mbps:
        class1:
          egress_max: 30
          egress_guaranteed: 20

  - name: sc-qos
    folder: "Service Connections"
    aggregate_bandwidth:
      egress_max: 200
```

### Examples

#### Load from File

```bash
$ scm load network qos-profile --file qos-profiles.yml
---> 100%
Created QoS profile: remote-qos in Remote Networks
Created QoS profile: sc-qos in Service Connections

Summary: Processed 2 QoS profiles
  - Created: 2
```

#### Dry Run

```bash
$ scm load network qos-profile --file qos-profiles.yml --dry-run
Dry run mode - no changes will be applied
  Would process: remote-qos
  Would process: sc-qos
```

## Show QoS Profile

Display QoS profile details.

### Syntax

```bash
scm show network qos-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Name of a specific QoS profile | No |

\* One of --folder, --snippet, or --device is required.

:::note
When no `--name` is specified, all items are listed by default.
:::

### Examples

#### Show Specific QoS Profile

```bash
$ scm show network qos-profile --folder "Remote Networks" --name my-qos
---> 100%
QoS Profile: my-qos
============================================================
Location: Remote Networks
Aggregate Bandwidth: {"egress_max": 100, "egress_guaranteed": 50}

ID: 12345678-abcd-1234-efgh-123456789012
```

#### List All QoS Profiles

```bash
$ scm show network qos-profile --folder "Remote Networks"
---> 100%
QoS Profiles:
--------------------------------------------------------------------------------
Name: my-qos
  Location: Remote Networks
  ID: 12345678-abcd-1234-efgh-123456789012
--------------------------------------------------------------------------------
Name: other-qos
  Location: Remote Networks
  ID: 87654321-dcba-4321-hgfe-210987654321
--------------------------------------------------------------------------------
```

## Backup QoS Profiles

Export all QoS profiles from a specified location to a YAML file.

### Syntax

```bash
scm backup network qos-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--file TEXT` | Custom output filename | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm backup network qos-profile --folder "Remote Networks"
---> 100%
Successfully backed up 2 QoS profiles to qos-profile_Remote Networks.yml
```
