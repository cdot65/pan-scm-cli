# Route Access List

Route access lists filter routes based on network prefixes for use with routing protocols. The `scm` CLI provides commands to create, update, delete, and load route access lists.

## Overview

The `route-access-list` commands allow you to:

- Create route access lists with prefix-based filtering rules
- Update existing route access list configurations
- Delete route access lists that are no longer needed
- Bulk import route access lists from YAML files
- Export route access lists for backup or migration

## Set Route Access List

Create or update a route access list.

### Syntax

```bash
scm set network route-access-list NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Access list name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--description TEXT` | Description | No |
| `--type-json TEXT` | Access list type config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create a Route Access List with Permit

```bash
$ scm set network route-access-list my-acl \
    --folder Texas \
    --type-json '{"prefix": [{"name": 1, "network": "10.0.0.0/8", "action": "permit"}]}'
---> 100%
Created route access list: my-acl in folder Texas
```

#### Create a Route Access List with Multiple Entries

```bash
$ scm set network route-access-list multi-acl \
    --folder Texas \
    --type-json '{"prefix": [{"name": 1, "network": "10.0.0.0/8", "action": "permit"}, {"name": 2, "network": "172.16.0.0/12", "action": "deny"}]}'
---> 100%
Created route access list: multi-acl in folder Texas
```

## Delete Route Access List

Delete a route access list from SCM.

### Syntax

```bash
scm delete network route-access-list NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Access list name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete network route-access-list my-acl --folder Texas
---> 100%
Deleted route access list: my-acl from folder Texas
```

## Load Route Access List

Load multiple route access lists from a YAML file.

### Syntax

```bash
scm load network route-access-list [OPTIONS]
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
route_access_lists:
  - name: internal-acl
    folder: Texas
    type:
      prefix:
        - name: 1
          network: "10.0.0.0/8"
          action: permit

  - name: rfc1918-acl
    folder: Texas
    type:
      prefix:
        - name: 1
          network: "10.0.0.0/8"
          action: permit
        - name: 2
          network: "172.16.0.0/12"
          action: permit
        - name: 3
          network: "192.168.0.0/16"
          action: permit
```

### Examples

#### Load with Original Locations

```bash
$ scm load network route-access-list --file access-lists.yml
---> 100%
✓ Loaded route access list: internal-acl
✓ Loaded route access list: rfc1918-acl

Successfully loaded 2 out of 2 route access lists from 'access-lists.yml'
```

#### Load with Folder Override

```bash
$ scm load network route-access-list --file access-lists.yml --folder Austin
---> 100%
✓ Loaded route access list: internal-acl
✓ Loaded route access list: rfc1918-acl

Successfully loaded 2 out of 2 route access lists from 'access-lists.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all route access lists
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show Route Access List

Display route access list objects.

### Syntax

```bash
scm show network route-access-list [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Name of a specific access list | No |

\* One of --folder, --snippet, or --device is required.

!!! note
    When no `--name` is specified, all items are listed by default.

### Examples

#### Show Specific Route Access List

```bash
$ scm show network route-access-list --folder Texas --name my-acl
---> 100%
Route Access List: my-acl
  Location: Folder 'Texas'
  Entries:
    1: 10.0.0.0/8 (permit)
```

#### List All Route Access Lists (Default Behavior)

```bash
$ scm show network route-access-list --folder Texas
---> 100%
Route access lists in folder 'Texas':
------------------------------------------------------------
Name: internal-acl
  Entries: 1
------------------------------------------------------------
Name: rfc1918-acl
  Entries: 3
------------------------------------------------------------
```

## Backup Route Access Lists

Backup all route access list objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network route-access-list [OPTIONS]
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
$ scm backup network route-access-list --folder Texas
---> 100%
Successfully backed up 5 route access lists to route_access_list_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network route-access-list --folder Texas --file texas-access-lists.yaml
---> 100%
Successfully backed up 5 route access lists to texas-access-lists.yaml
```

## Best Practices

1. **Order Entries Logically**: Number entries sequentially and place more specific prefixes before broader ones.
2. **Use Implicit Deny**: Remember that access lists have an implicit deny at the end; only permitted prefixes pass.
3. **Document Purpose**: Use descriptive names that indicate what the access list filters.
4. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
5. **Backup Before Changes**: Always backup existing access lists before making bulk modifications.
