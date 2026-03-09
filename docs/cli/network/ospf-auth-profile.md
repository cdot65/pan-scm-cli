# OSPF Auth Profile

OSPF auth profiles define authentication settings for OSPF neighbor relationships, supporting simple password and MD5 authentication. The `scm` CLI provides commands to create, update, delete, and load OSPF auth profiles.

## Overview

The `ospf-auth-profile` commands allow you to:

- Create OSPF auth profiles with password or MD5 authentication
- Update existing OSPF auth profile configurations
- Delete OSPF auth profiles that are no longer needed
- Bulk import OSPF auth profiles from YAML files
- Export OSPF auth profiles for backup or migration

## Set OSPF Auth Profile

Create or update an OSPF auth profile.

### Syntax

```bash
scm set network ospf-auth-profile NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--password TEXT` | Simple password authentication | No |
| `--md5-json TEXT` | MD5 authentication keys as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create with Simple Password Authentication

```bash
$ scm set network ospf-auth-profile my-ospf-auth \
    --folder Texas \
    --password "ospf-secret"
---> 100%
Created OSPF auth profile: my-ospf-auth in folder Texas
```

#### Create with MD5 Authentication

```bash
$ scm set network ospf-auth-profile my-ospf-md5 \
    --folder Texas \
    --md5-json '[{"key_id": 1, "key": "md5-key"}]'
---> 100%
Created OSPF auth profile: my-ospf-md5 in folder Texas
```

## Delete OSPF Auth Profile

Delete an OSPF auth profile from SCM.

### Syntax

```bash
scm delete network ospf-auth-profile NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete network ospf-auth-profile my-ospf-auth --folder Texas --force
---> 100%
Deleted OSPF auth profile: my-ospf-auth from folder Texas
```

## Load OSPF Auth Profile

Load multiple OSPF auth profiles from a YAML file.

### Syntax

```bash
scm load network ospf-auth-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--dry-run` | Preview changes without applying | No |

\* One of --folder, --snippet, or --device is required.

### YAML File Format

```yaml
---
ospf_auth_profiles:
  - name: simple-auth
    folder: Texas
    password: "ospf-secret"

  - name: md5-auth
    folder: Texas
    md5:
      - key_id: 1
        key: "md5-key-1"
```

### Examples

#### Load with Original Locations

```bash
$ scm load network ospf-auth-profile --file ospf-auth.yml
---> 100%
✓ Loaded OSPF auth profile: simple-auth
✓ Loaded OSPF auth profile: md5-auth

Successfully loaded 2 out of 2 OSPF auth profiles from 'ospf-auth.yml'
```

#### Load with Folder Override

```bash
$ scm load network ospf-auth-profile --file ospf-auth.yml --folder Austin
---> 100%
✓ Loaded OSPF auth profile: simple-auth
✓ Loaded OSPF auth profile: md5-auth

Successfully loaded 2 out of 2 OSPF auth profiles from 'ospf-auth.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all OSPF auth profiles
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show OSPF Auth Profile

Display OSPF auth profile objects.

### Syntax

```bash
scm show network ospf-auth-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Name of a specific profile | No |

\* One of --folder, --snippet, or --device is required.

!!! note
    When no `--name` is specified, all items are listed by default.

### Examples

#### Show Specific OSPF Auth Profile

```bash
$ scm show network ospf-auth-profile --folder Texas --name my-ospf-auth
---> 100%
OSPF Auth Profile: my-ospf-auth
  Location: Folder 'Texas'
  Authentication: Simple Password
```

#### List All OSPF Auth Profiles (Default Behavior)

```bash
$ scm show network ospf-auth-profile --folder Texas
---> 100%
OSPF auth profiles in folder 'Texas':
------------------------------------------------------------
Name: simple-auth
  Authentication: Simple Password
------------------------------------------------------------
Name: md5-auth
  Authentication: MD5
------------------------------------------------------------
```

## Backup OSPF Auth Profiles

Backup all OSPF auth profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network ospf-auth-profile [OPTIONS]
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
$ scm backup network ospf-auth-profile --folder Texas
---> 100%
Successfully backed up 3 OSPF auth profiles to ospf_auth_profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network ospf-auth-profile --folder Texas --file texas-ospf-auth.yaml
---> 100%
Successfully backed up 3 OSPF auth profiles to texas-ospf-auth.yaml
```

## Best Practices

1. **Prefer MD5 Over Simple Password**: MD5 authentication provides stronger security than simple password authentication.
2. **Rotate Keys Regularly**: Update OSPF authentication keys periodically as part of security hygiene.
3. **Coordinate Key Changes**: Ensure all OSPF neighbors are updated simultaneously when rotating authentication keys.
4. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
5. **Backup Before Changes**: Always backup existing auth profiles before making bulk modifications.
