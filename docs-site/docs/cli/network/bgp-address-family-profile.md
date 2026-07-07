# BGP Address Family Profile

BGP address family profiles define address family configurations (IPv4 unicast/multicast) for BGP routing. The `scm` CLI provides commands to create, update, delete, and load BGP address family profiles.

## Overview

The `bgp-address-family-profile` commands allow you to:

- Create BGP address family profiles with IPv4 unicast or multicast settings
- Update existing address family profile configurations
- Delete address family profiles that are no longer needed
- Bulk import address family profiles from YAML files
- Export address family profiles for backup or migration

## Set BGP Address Family Profile

Create or update a BGP address family profile.

### Syntax

```bash
scm set network bgp-address-family-profile NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the BGP address family profile | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes\* |
| `--snippet TEXT` | Snippet location | Yes\* |
| `--device TEXT` | Device location | Yes\* |
| `--ipv4-json TEXT` | IPv4 address family config as JSON | No |

\* Exactly one of `--folder`, `--snippet`, or `--device` is required.

### Examples

#### Create an IPv4 Unicast Profile

```bash
$ scm set network bgp-address-family-profile my-af-profile \
    --folder Texas \
    --ipv4-json '{"unicast": {"enable": true}}'
---> 100%
Created BGP address family profile: my-af-profile in folder Texas
```

#### Create an IPv4 Multicast Profile

```bash
$ scm set network bgp-address-family-profile multicast-af \
    --folder Texas \
    --ipv4-json '{"multicast": {"enable": true}}'
---> 100%
Created BGP address family profile: multicast-af in folder Texas
```

## Delete BGP Address Family Profile

Delete a BGP address family profile from SCM.

### Syntax

```bash
scm delete network bgp-address-family-profile NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the BGP address family profile to delete | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes\* |
| `--snippet TEXT` | Snippet location | Yes\* |
| `--device TEXT` | Device location | Yes\* |
| `--force` | Skip confirmation prompt | No |

\* Exactly one of `--folder`, `--snippet`, or `--device` is required.

### Example

```bash
$ scm delete network bgp-address-family-profile my-af-profile --folder Texas --force
---> 100%
Deleted BGP address family profile: my-af-profile from folder Texas
```

## Load BGP Address Family Profile

Load multiple BGP address family profiles from a YAML file.

### Syntax

```bash
scm load network bgp-address-family-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying | No |

### YAML File Format

```yaml
---
bgp_address_family_profiles:
  - name: unicast-af
    folder: Texas
    ipv4:
      unicast:
        enable: true

  - name: multicast-af
    folder: Texas
    ipv4:
      multicast:
        enable: true
```

### Examples

#### Load with Original Locations

```bash
$ scm load network bgp-address-family-profile --file af-profiles.yml
---> 100%
✓ Loaded BGP address family profile: unicast-af
✓ Loaded BGP address family profile: multicast-af

Successfully loaded 2 out of 2 BGP address family profiles from 'af-profiles.yml'
```

#### Load with Folder Override

```bash
$ scm load network bgp-address-family-profile --file af-profiles.yml --folder Austin
---> 100%
✓ Loaded BGP address family profile: unicast-af
✓ Loaded BGP address family profile: multicast-af

Successfully loaded 2 out of 2 BGP address family profiles from 'af-profiles.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all BGP address family profiles
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show BGP Address Family Profile

Display BGP address family profile objects.

### Syntax

```bash
scm show network bgp-address-family-profile [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the BGP address family profile to show; omit to list all | No |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes\* |
| `--snippet TEXT` | Snippet location | Yes\* |
| `--device TEXT` | Device location | Yes\* |
| `--max-results INTEGER` | Maximum number of results to display | No |
| `--output [table\|json\|yaml]` | Output format (default: `table`) | No |

\* Exactly one of `--folder`, `--snippet`, or `--device` is required.

:::note
When no `NAME` argument is provided, all items are listed by default.
:::

### Examples

#### Show Specific BGP Address Family Profile

```bash
$ scm show network bgp-address-family-profile my-af-profile --folder Texas
---> 100%
BGP Address Family Profile: my-af-profile
  Location: Folder 'Texas'
  IPv4 Unicast: enabled
```

#### List All BGP Address Family Profiles (Default Behavior)

```bash
$ scm show network bgp-address-family-profile --folder Texas
---> 100%
BGP address family profiles in folder 'Texas':
------------------------------------------------------------
Name: unicast-af
  IPv4 Unicast: enabled
------------------------------------------------------------
Name: multicast-af
  IPv4 Multicast: enabled
------------------------------------------------------------
```

## Backup BGP Address Family Profiles

Backup all BGP address family profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network bgp-address-family-profile [OPTIONS]
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
$ scm backup network bgp-address-family-profile --folder Texas
---> 100%
Successfully backed up 3 BGP address family profiles to bgp_address_family_profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network bgp-address-family-profile --folder Texas --file texas-af-profiles.yaml
---> 100%
Successfully backed up 3 BGP address family profiles to texas-af-profiles.yaml
```

## Best Practices

1. **Enable Only Required Families**: Only enable the address families (unicast/multicast) that your network requires.
2. **Use Consistent Naming**: Name profiles descriptively to indicate which address families are configured.
3. **Backup Before Changes**: Always backup existing profiles before making bulk modifications.
4. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
5. **Document Profile Purpose**: Keep track of which BGP peers reference each address family profile.
