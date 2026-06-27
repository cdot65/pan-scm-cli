# Route Prefix List

Route prefix lists filter routes based on IP prefixes with optional length matching, used with BGP and OSPF route maps. The `scm` CLI provides commands to create, update, delete, and load route prefix lists.

## Overview

The `route-prefix-list` commands allow you to:

- Create route prefix lists with prefix matching and length constraints
- Update existing route prefix list configurations
- Delete route prefix lists that are no longer needed
- Bulk import route prefix lists from YAML files
- Export route prefix lists for backup or migration

## Set Route Prefix List

Create or update a route prefix list.

### Syntax

```bash
scm set network route-prefix-list NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Prefix list name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--description TEXT` | Description | No |
| `--ipv4-json TEXT` | IPv4 prefix list config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create a Prefix List with Length Matching

```bash
$ scm set network route-prefix-list my-prefix-list \
    --folder Texas \
    --ipv4-json '[{"name": "rule1", "prefix": "10.0.0.0/8", "action": "permit", "ge": 16, "le": 24}]'
---> 100%
Created route prefix list: my-prefix-list in folder Texas
```

#### Create a Simple Prefix List

```bash
$ scm set network route-prefix-list default-only \
    --folder Texas \
    --ipv4-json '[{"name": "rule1", "prefix": "0.0.0.0/0", "action": "permit"}]'
---> 100%
Created route prefix list: default-only in folder Texas
```

## Delete Route Prefix List

Delete a route prefix list from SCM.

### Syntax

```bash
scm delete network route-prefix-list NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Prefix list name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete network route-prefix-list my-prefix-list --folder Texas --force
---> 100%
Deleted route prefix list: my-prefix-list from folder Texas
```

## Load Route Prefix List

Load multiple route prefix lists from a YAML file.

### Syntax

```bash
scm load network route-prefix-list [OPTIONS]
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
route_prefix_lists:
  - name: internal-prefixes
    folder: Texas
    ipv4:
      - name: "rule1"
        prefix: "10.0.0.0/8"
        action: permit
        ge: 16
        le: 24

  - name: default-route
    folder: Texas
    ipv4:
      - name: "rule1"
        prefix: "0.0.0.0/0"
        action: permit
```

### Examples

#### Load with Original Locations

```bash
$ scm load network route-prefix-list --file prefix-lists.yml
---> 100%
✓ Loaded route prefix list: internal-prefixes
✓ Loaded route prefix list: default-route

Successfully loaded 2 out of 2 route prefix lists from 'prefix-lists.yml'
```

#### Load with Folder Override

```bash
$ scm load network route-prefix-list --file prefix-lists.yml --folder Austin
---> 100%
✓ Loaded route prefix list: internal-prefixes
✓ Loaded route prefix list: default-route

Successfully loaded 2 out of 2 route prefix lists from 'prefix-lists.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all route prefix lists
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show Route Prefix List

Display route prefix list objects.

### Syntax

```bash
scm show network route-prefix-list [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Name of a specific prefix list | No |

\* One of --folder, --snippet, or --device is required.

:::note
When no `--name` is specified, all items are listed by default.
:::

### Examples

#### Show Specific Route Prefix List

```bash
$ scm show network route-prefix-list --folder Texas --name my-prefix-list
---> 100%
Route Prefix List: my-prefix-list
  Location: Folder 'Texas'
  Entries:
    rule1: 10.0.0.0/8 (permit, ge: 16, le: 24)
```

#### List All Route Prefix Lists (Default Behavior)

```bash
$ scm show network route-prefix-list --folder Texas
---> 100%
Route prefix lists in folder 'Texas':
------------------------------------------------------------
Name: internal-prefixes
  Entries: 1
------------------------------------------------------------
Name: default-route
  Entries: 1
------------------------------------------------------------
```

## Backup Route Prefix Lists

Backup all route prefix list objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network route-prefix-list [OPTIONS]
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
$ scm backup network route-prefix-list --folder Texas
---> 100%
Successfully backed up 4 route prefix lists to route_prefix_list_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network route-prefix-list --folder Texas --file texas-prefix-lists.yaml
---> 100%
Successfully backed up 4 route prefix lists to texas-prefix-lists.yaml
```

## Best Practices

1. **Use ge/le for Flexibility**: Use greater-than-or-equal (ge) and less-than-or-equal (le) modifiers to match a range of prefix lengths.
2. **Order Rules Carefully**: Prefix list entries are evaluated in order; place more specific matches first.
3. **Document Prefix Purposes**: Use descriptive names that indicate what prefixes the list matches.
4. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
5. **Backup Before Changes**: Always backup existing prefix lists before making bulk modifications.
