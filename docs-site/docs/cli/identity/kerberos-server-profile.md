# Kerberos Server Profile

Kerberos server profiles configure KDC (Key Distribution Center) server connections for Kerberos authentication in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, and bulk manage Kerberos server profiles.

## Overview

The `kerberos-server-profile` commands allow you to:

- Create Kerberos server profiles with KDC server configurations
- Update existing profile server lists and settings
- Delete profiles that are no longer needed
- Bulk import profiles from YAML files
- Export profiles for backup or migration

## Set Kerberos Server Profile

Create or update a Kerberos server profile.

### Syntax

```bash
scm set identity kerberos-server-profile NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--servers TEXT` | Server list as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create Kerberos Server Profile

```bash
$ scm set identity kerberos-server-profile corp-kerberos \
    --folder Texas \
    --servers '[{"name": "kdc1", "host": "kdc1.example.com", "port": 88}]'
---> 100%
Created kerberos-server-profile: corp-kerberos in folder Texas
```

#### Create Profile with Multiple KDC Servers

```bash
$ scm set identity kerberos-server-profile corp-kerberos-ha \
    --folder Texas \
    --servers '[{"name": "kdc1", "host": "kdc1.example.com", "port": 88}, {"name": "kdc2", "host": "kdc2.example.com", "port": 88}]'
---> 100%
Created kerberos-server-profile: corp-kerberos-ha in folder Texas
```

## Delete Kerberos Server Profile

Delete a Kerberos server profile from SCM.

### Syntax

```bash
scm delete identity kerberos-server-profile NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete identity kerberos-server-profile corp-kerberos \
    --folder Texas \
    --force
---> 100%
Deleted kerberos-server-profile: corp-kerberos from folder Texas
```

## Load Kerberos Server Profile

Load multiple Kerberos server profiles from a YAML file.

### Syntax

```bash
scm load identity kerberos-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file | Yes |
| `--folder TEXT` | Folder location override | No |
| `--snippet TEXT` | Snippet location override | No |
| `--device TEXT` | Device location override | No |
| `--dry-run` | Preview changes without applying | No |

### YAML File Format

```yaml
---
kerberos_server_profiles:
  - name: corp-kerberos
    folder: Texas
    servers:
      - name: kdc1
        host: kdc1.example.com
        port: 88

  - name: branch-kerberos
    folder: Texas
    servers:
      - name: kdc-branch1
        host: kdc-branch1.example.com
        port: 88
      - name: kdc-branch2
        host: kdc-branch2.example.com
        port: 88
```

### Examples

#### Load with Original Locations

```bash
$ scm load identity kerberos-server-profile --file kerberos.yml
---> 100%
✓ Loaded kerberos-server-profile: corp-kerberos
✓ Loaded kerberos-server-profile: branch-kerberos

Successfully loaded 2 out of 2 kerberos-server-profiles from 'kerberos.yml'
```

#### Load with Folder Override

```bash
$ scm load identity kerberos-server-profile \
    --file kerberos.yml \
    --folder Austin
---> 100%
✓ Loaded kerberos-server-profile: corp-kerberos
✓ Loaded kerberos-server-profile: branch-kerberos

Successfully loaded 2 out of 2 kerberos-server-profiles from 'kerberos.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all Kerberos server
profiles will be loaded into the specified container, ignoring the container specified in
the YAML file.
:::

## Show Kerberos Server Profile

Display Kerberos server profile objects.

### Syntax

```bash
scm show identity kerberos-server-profile [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name; omit to list all | No |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--output, -o [table\|json\|yaml]` | Output format (default: table) | No |
| `--max-results INTEGER` | Maximum number of results to display | No |

\* One of --folder, --snippet, or --device is required.

:::note
When no `NAME` is specified, all items are listed by default.
:::

### Examples

#### Show Specific Kerberos Server Profile

```bash
$ scm show identity kerberos-server-profile corp-kerberos \
    --folder Texas
---> 100%
Kerberos Server Profile: corp-kerberos
  Location: Folder 'Texas'
  Servers:
    - kdc1 (kdc1.example.com:88)
```

#### List All Kerberos Server Profiles (Default Behavior)

```bash
$ scm show identity kerberos-server-profile --folder Texas
---> 100%
Kerberos Server Profiles in folder 'Texas':
------------------------------------------------------------
Name: corp-kerberos
  Servers: kdc1 (kdc1.example.com:88)
------------------------------------------------------------
Name: branch-kerberos
  Servers: kdc-branch1 (kdc-branch1.example.com:88), kdc-branch2 (kdc-branch2.example.com:88)
------------------------------------------------------------
```

## Backup Kerberos Server Profiles

Backup all Kerberos server profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup identity kerberos-server-profile [OPTIONS]
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
$ scm backup identity kerberos-server-profile --folder Texas
---> 100%
Successfully backed up 3 kerberos-server-profiles to kerberos_server_profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup identity kerberos-server-profile \
    --folder Texas \
    --file texas-kerberos.yaml
---> 100%
Successfully backed up 3 kerberos-server-profiles to texas-kerberos.yaml
```

## Best Practices

1. **Use Descriptive Profile Names**: Name profiles by environment or location (e.g., `corp-kerberos`, `branch-kerberos`) for easy identification.
2. **Configure Multiple KDC Servers**: Add redundant KDC servers to ensure high availability for Kerberos authentication.
3. **Use Standard Ports**: Use port 88 (the Kerberos default) unless your environment requires a non-standard configuration.
4. **Backup Before Changes**: Export existing profiles before making modifications to enable quick rollback if needed.
5. **Use YAML for Bulk Operations**: Manage multiple Kerberos server profiles through YAML files to ensure consistency across environments.
