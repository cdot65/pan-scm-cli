# BGP Redistribution Profile

BGP redistribution profiles control how routes from other protocols (OSPF, static, connected) are redistributed into BGP. The `scm` CLI provides commands to create, update, delete, and load BGP redistribution profiles.

## Overview

The `bgp-redistribution-profile` commands allow you to:

- Create BGP redistribution profiles with protocol redistribution settings
- Update existing redistribution profile configurations
- Delete redistribution profiles that are no longer needed
- Bulk import redistribution profiles from YAML files
- Export redistribution profiles for backup or migration

## Set BGP Redistribution Profile

Create or update a BGP redistribution profile.

### Syntax

```bash
scm set network bgp-redistribution-profile NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--ipv4-json TEXT` | IPv4 redistribution config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Redistribute Connected Routes

```bash
$ scm set network bgp-redistribution-profile my-redist \
    --folder Texas \
    --ipv4-json '{"unicast": {"connected": {"enable": true}}}'
---> 100%
Created BGP redistribution profile: my-redist in folder Texas
```

#### Redistribute Static Routes

```bash
$ scm set network bgp-redistribution-profile static-redist \
    --folder Texas \
    --ipv4-json '{"unicast": {"static": {"enable": true}}}'
---> 100%
Created BGP redistribution profile: static-redist in folder Texas
```

## Delete BGP Redistribution Profile

Delete a BGP redistribution profile from SCM.

### Syntax

```bash
scm delete network bgp-redistribution-profile NAME [OPTIONS]
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
$ scm delete network bgp-redistribution-profile my-redist --folder Texas --force
---> 100%
Deleted BGP redistribution profile: my-redist from folder Texas
```

## Load BGP Redistribution Profile

Load multiple BGP redistribution profiles from a YAML file.

### Syntax

```bash
scm load network bgp-redistribution-profile [OPTIONS]
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
bgp_redistribution_profiles:
  - name: connected-redist
    folder: Texas
    ipv4:
      unicast:
        connected:
          enable: true

  - name: static-redist
    folder: Texas
    ipv4:
      unicast:
        static:
          enable: true
```

### Examples

#### Load with Original Locations

```bash
$ scm load network bgp-redistribution-profile --file bgp-redist.yml
---> 100%
✓ Loaded BGP redistribution profile: connected-redist
✓ Loaded BGP redistribution profile: static-redist

Successfully loaded 2 out of 2 BGP redistribution profiles from 'bgp-redist.yml'
```

#### Load with Folder Override

```bash
$ scm load network bgp-redistribution-profile --file bgp-redist.yml --folder Austin
---> 100%
✓ Loaded BGP redistribution profile: connected-redist
✓ Loaded BGP redistribution profile: static-redist

Successfully loaded 2 out of 2 BGP redistribution profiles from 'bgp-redist.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all BGP redistribution profiles
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show BGP Redistribution Profile

Display BGP redistribution profile objects.

### Syntax

```bash
scm show network bgp-redistribution-profile [OPTIONS]
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

#### Show Specific BGP Redistribution Profile

```bash
$ scm show network bgp-redistribution-profile --folder Texas --name my-redist
---> 100%
BGP Redistribution Profile: my-redist
  Location: Folder 'Texas'
  IPv4 Unicast Connected: enabled
```

#### List All BGP Redistribution Profiles (Default Behavior)

```bash
$ scm show network bgp-redistribution-profile --folder Texas
---> 100%
BGP redistribution profiles in folder 'Texas':
------------------------------------------------------------
Name: connected-redist
  IPv4 Unicast Connected: enabled
------------------------------------------------------------
Name: static-redist
  IPv4 Unicast Static: enabled
------------------------------------------------------------
```

## Backup BGP Redistribution Profiles

Backup all BGP redistribution profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network bgp-redistribution-profile [OPTIONS]
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
$ scm backup network bgp-redistribution-profile --folder Texas
---> 100%
Successfully backed up 4 BGP redistribution profiles to bgp_redistribution_profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network bgp-redistribution-profile --folder Texas --file texas-bgp-redist.yaml
---> 100%
Successfully backed up 4 BGP redistribution profiles to texas-bgp-redist.yaml
```

## Best Practices

1. **Redistribute Selectively**: Only redistribute route types that are necessary to avoid routing table bloat.
2. **Use Route Maps**: Combine redistribution profiles with route maps for granular control over redistributed routes.
3. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
4. **Backup Before Changes**: Always backup existing profiles before making bulk modifications.
5. **Document Redistribution Policies**: Clearly document which protocols are redistributed and why.
