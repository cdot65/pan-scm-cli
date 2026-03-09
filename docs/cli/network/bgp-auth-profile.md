# BGP Auth Profile

BGP auth profiles define authentication keys for BGP peer sessions. The `scm` CLI provides commands to create, update, delete, and load BGP auth profiles.

## Overview

The `bgp-auth-profile` commands allow you to:

- Create BGP auth profiles with authentication secrets
- Update existing BGP auth profile configurations
- Delete BGP auth profiles that are no longer needed
- Bulk import BGP auth profiles from YAML files
- Export BGP auth profiles for backup or migration

## Set BGP Auth Profile

Create or update a BGP auth profile.

### Syntax

```bash
scm set network bgp-auth-profile NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--secret TEXT` | BGP authentication key | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create a BGP Auth Profile

```bash
$ scm set network bgp-auth-profile my-bgp-auth \
    --folder Texas \
    --secret "bgp-secret-key"
---> 100%
Created BGP auth profile: my-bgp-auth in folder Texas
```

#### Update an Existing Auth Profile

```bash
$ scm set network bgp-auth-profile my-bgp-auth \
    --folder Texas \
    --secret "new-bgp-secret"
---> 100%
Updated BGP auth profile: my-bgp-auth in folder Texas
```

## Delete BGP Auth Profile

Delete a BGP auth profile from SCM.

### Syntax

```bash
scm delete network bgp-auth-profile NAME [OPTIONS]
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
$ scm delete network bgp-auth-profile my-bgp-auth --folder Texas --force
---> 100%
Deleted BGP auth profile: my-bgp-auth from folder Texas
```

## Load BGP Auth Profile

Load multiple BGP auth profiles from a YAML file.

### Syntax

```bash
scm load network bgp-auth-profile [OPTIONS]
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
bgp_auth_profiles:
  - name: peer-auth-1
    folder: Texas
    secret: "bgp-key-1"

  - name: peer-auth-2
    folder: Texas
    secret: "bgp-key-2"
```

### Examples

#### Load with Original Locations

```bash
$ scm load network bgp-auth-profile --file bgp-auth.yml
---> 100%
✓ Loaded BGP auth profile: peer-auth-1
✓ Loaded BGP auth profile: peer-auth-2

Successfully loaded 2 out of 2 BGP auth profiles from 'bgp-auth.yml'
```

#### Load with Folder Override

```bash
$ scm load network bgp-auth-profile --file bgp-auth.yml --folder Austin
---> 100%
✓ Loaded BGP auth profile: peer-auth-1
✓ Loaded BGP auth profile: peer-auth-2

Successfully loaded 2 out of 2 BGP auth profiles from 'bgp-auth.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all BGP auth profiles
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show BGP Auth Profile

Display BGP auth profile objects.

### Syntax

```bash
scm show network bgp-auth-profile [OPTIONS]
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

#### Show Specific BGP Auth Profile

```bash
$ scm show network bgp-auth-profile --folder Texas --name my-bgp-auth
---> 100%
BGP Auth Profile: my-bgp-auth
  Location: Folder 'Texas'
  Secret: ********
```

#### List All BGP Auth Profiles (Default Behavior)

```bash
$ scm show network bgp-auth-profile --folder Texas
---> 100%
BGP auth profiles in folder 'Texas':
------------------------------------------------------------
Name: peer-auth-1
  Secret: ********
------------------------------------------------------------
Name: peer-auth-2
  Secret: ********
------------------------------------------------------------
```

## Backup BGP Auth Profiles

Backup all BGP auth profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network bgp-auth-profile [OPTIONS]
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
$ scm backup network bgp-auth-profile --folder Texas
---> 100%
Successfully backed up 3 BGP auth profiles to bgp_auth_profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network bgp-auth-profile --folder Texas --file texas-bgp-auth.yaml
---> 100%
Successfully backed up 3 BGP auth profiles to texas-bgp-auth.yaml
```

## Best Practices

1. **Use Strong Secrets**: Choose complex authentication keys that are difficult to guess or brute-force.
2. **Rotate Keys Regularly**: Update BGP authentication secrets periodically as part of security hygiene.
3. **Coordinate Key Changes**: Ensure both BGP peers are updated simultaneously when rotating authentication keys.
4. **Backup Before Changes**: Always backup existing auth profiles before making bulk modifications.
5. **Use Consistent Naming**: Name profiles to clearly identify which BGP peer relationship they authenticate.
