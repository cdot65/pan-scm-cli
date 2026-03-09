# BGP Filtering Profile

BGP filtering profiles define route filtering rules applied to BGP peer sessions for controlling route advertisements. The `scm` CLI provides commands to create, update, delete, and load BGP filtering profiles.

## Overview

The `bgp-filtering-profile` commands allow you to:

- Create BGP filtering profiles with IPv4 filtering configurations
- Update existing filtering profile settings
- Delete filtering profiles that are no longer needed
- Bulk import filtering profiles from YAML files
- Export filtering profiles for backup or migration

## Set BGP Filtering Profile

Create or update a BGP filtering profile.

### Syntax

```bash
scm set network bgp-filtering-profile NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--ipv4-json TEXT` | IPv4 filtering config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create a Filtering Profile with Inbound Filter

```bash
$ scm set network bgp-filtering-profile my-filter \
    --folder Texas \
    --ipv4-json '{"unicast": {"filter_in": "my-prefix-list"}}'
---> 100%
Created BGP filtering profile: my-filter in folder Texas
```

#### Create a Filtering Profile with Outbound Filter

```bash
$ scm set network bgp-filtering-profile outbound-filter \
    --folder Texas \
    --ipv4-json '{"unicast": {"filter_out": "export-prefix-list"}}'
---> 100%
Created BGP filtering profile: outbound-filter in folder Texas
```

## Delete BGP Filtering Profile

Delete a BGP filtering profile from SCM.

### Syntax

```bash
scm delete network bgp-filtering-profile NAME [OPTIONS]
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
$ scm delete network bgp-filtering-profile my-filter --folder Texas --force
---> 100%
Deleted BGP filtering profile: my-filter from folder Texas
```

## Load BGP Filtering Profile

Load multiple BGP filtering profiles from a YAML file.

### Syntax

```bash
scm load network bgp-filtering-profile [OPTIONS]
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
bgp_filtering_profiles:
  - name: inbound-filter
    folder: Texas
    ipv4:
      unicast:
        filter_in: "my-prefix-list"

  - name: outbound-filter
    folder: Texas
    ipv4:
      unicast:
        filter_out: "export-prefix-list"
```

### Examples

#### Load with Original Locations

```bash
$ scm load network bgp-filtering-profile --file bgp-filters.yml
---> 100%
✓ Loaded BGP filtering profile: inbound-filter
✓ Loaded BGP filtering profile: outbound-filter

Successfully loaded 2 out of 2 BGP filtering profiles from 'bgp-filters.yml'
```

#### Load with Folder Override

```bash
$ scm load network bgp-filtering-profile --file bgp-filters.yml --folder Austin
---> 100%
✓ Loaded BGP filtering profile: inbound-filter
✓ Loaded BGP filtering profile: outbound-filter

Successfully loaded 2 out of 2 BGP filtering profiles from 'bgp-filters.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all BGP filtering profiles
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show BGP Filtering Profile

Display BGP filtering profile objects.

### Syntax

```bash
scm show network bgp-filtering-profile [OPTIONS]
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

#### Show Specific BGP Filtering Profile

```bash
$ scm show network bgp-filtering-profile --folder Texas --name my-filter
---> 100%
BGP Filtering Profile: my-filter
  Location: Folder 'Texas'
  IPv4 Unicast Filter In: my-prefix-list
```

#### List All BGP Filtering Profiles (Default Behavior)

```bash
$ scm show network bgp-filtering-profile --folder Texas
---> 100%
BGP filtering profiles in folder 'Texas':
------------------------------------------------------------
Name: inbound-filter
  IPv4 Unicast Filter In: my-prefix-list
------------------------------------------------------------
Name: outbound-filter
  IPv4 Unicast Filter Out: export-prefix-list
------------------------------------------------------------
```

## Backup BGP Filtering Profiles

Backup all BGP filtering profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network bgp-filtering-profile [OPTIONS]
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
$ scm backup network bgp-filtering-profile --folder Texas
---> 100%
Successfully backed up 5 BGP filtering profiles to bgp_filtering_profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network bgp-filtering-profile --folder Texas --file texas-bgp-filters.yaml
---> 100%
Successfully backed up 5 BGP filtering profiles to texas-bgp-filters.yaml
```

## Best Practices

1. **Filter Inbound and Outbound**: Apply both inbound and outbound filters to control route exchange precisely.
2. **Reference Prefix Lists**: Use prefix lists for filtering rather than inline definitions for better reusability.
3. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
4. **Backup Before Changes**: Always backup existing profiles before making bulk modifications.
5. **Use Descriptive Names**: Name profiles to indicate their filtering direction and purpose.
