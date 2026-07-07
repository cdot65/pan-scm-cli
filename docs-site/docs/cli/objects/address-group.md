# Address Groups

Address groups are collections of address objects that can be referenced in security policies, NAT rules, and other configurations. The `scm` CLI provides commands to create, update, delete, and load address groups.

## Overview

The `address-group` commands allow you to:

- Create static address groups with fixed member lists
- Create dynamic address groups with tag-based filter expressions
- Delete address groups that are no longer needed
- Bulk import address groups from YAML files
- Export address groups for backup or migration

## Address Group Types

The CLI supports two types of address groups:

| Type | Description | Example Use Case |
| --- | --- | --- |
| Static | Fixed list of address objects | Group of web servers |
| Dynamic | Members determined by filter criteria (tags) | Endpoints matching security criteria |

## Set Address Group

Create or update an address group.

### Syntax

```bash
scm set object address-group NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the address group | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes\* |
| `--snippet TEXT` | Snippet location | Yes\* |
| `--device TEXT` | Device location | Yes\* |
| `--description TEXT` | Description for the address group | No |
| `--tags TEXT` | Tag to apply (repeat for multiple) | No |
| `--type TEXT` | Type of address group (`static` or `dynamic`) | Yes |
| `--members TEXT` | Address object for static groups (repeat for multiple) | Only with `--type static` |
| `--filter TEXT` | Tag-based filter expression for dynamic groups | Only with `--type dynamic` |

\* Exactly one of `--folder`, `--snippet`, or `--device` is required.

### Examples

#### Create a Static Address Group

```bash
$ scm set object address-group web-servers \
    --folder Shared \
    --type static \
    --members web-server-1 --members web-server-2
---> 100%
Created address group: web-servers in folder Shared
```

#### Create a Dynamic Address Group

```bash
$ scm set object address-group trusted-endpoints \
    --folder Shared \
    --type dynamic \
    --filter "'trusted-endpoint' and 'corporate-asset'"
---> 100%
Created address group: trusted-endpoints in folder Shared
```

## Delete Address Group

Delete an address group from SCM.

### Syntax

```bash
scm delete object address-group NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the address group to delete | Yes |

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
$ scm delete object address-group web-servers --folder Shared --force
---> 100%
Deleted address group: web-servers from folder Shared
```

## Load Address Groups

Load multiple address groups from a YAML file.

### Syntax

```bash
scm load object address-group [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing address group definitions | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
address_groups:
  - name: web-servers
    folder: Texas
    description: "Group of web servers"
    type: static
    members:
      - web-server-1
      - web-server-2
    tags:
      - web
      - servers

  - name: trusted-endpoints
    folder: Texas
    description: "Dynamic group for trusted corporate endpoints"
    type: dynamic
    filter: "'trusted-endpoint' and 'corporate-asset'"
    tags:
      - endpoints
      - trusted
```

### Examples

#### Load with Original Locations

```bash
$ scm load object address-group --file address-groups.yml
---> 100%
✓ Loaded address group: web-servers
✓ Loaded address group: trusted-endpoints

Successfully loaded 2 out of 2 address groups from 'address-groups.yml'
```

#### Load with Folder Override

```bash
$ scm load object address-group --file address-groups.yml --folder Austin
---> 100%
✓ Loaded address group: web-servers
✓ Loaded address group: trusted-endpoints

Successfully loaded 2 out of 2 address groups from 'address-groups.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all address
groups will be loaded into the specified container, ignoring the container specified
in the YAML file.
:::

## Show Address Group

Display address group objects.

### Syntax

```bash
scm show object address-group [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the address group to show; omit to list all | No |

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

#### Show Specific Address Group

```bash
$ scm show object address-group web-servers --folder Texas
---> 100%
Address Group: web-servers
  Location: Folder 'Texas'
  Type: static
  Description: Group of web servers
  Members (2):
    - web-server-1
    - web-server-2
  Tags: web, servers
  ID: 123e4567-e89b-12d3-a456-426614174001
```

#### List All Address Groups (Default Behavior)

```bash
$ scm show object address-group --folder Texas
---> 100%
Address Groups in folder 'Texas':
------------------------------------------------------------
Name: web-servers
  Location: Folder 'Texas'
  Type: static
  Members: web-server-1, web-server-2
  Description: Group of web servers
  Tags: web, servers
------------------------------------------------------------
Name: trusted-endpoints
  Location: Folder 'Texas'
  Type: dynamic
  Filter: 'trusted-endpoint' and 'corporate-asset'
  Description: Dynamic group for trusted corporate endpoints
  Tags: endpoints, trusted
------------------------------------------------------------
```

## Backup Address Groups

Backup all address group objects from a specified location to a YAML file.

### Syntax

```bash
scm backup object address-group [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup address groups from | No\* |
| `--snippet TEXT` | Snippet to backup address groups from | No\* |
| `--device TEXT` | Device to backup address groups from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup object address-group --folder Texas
---> 100%
Successfully backed up 12 address groups to address-group_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object address-group --folder Texas --file texas-groups.yaml
---> 100%
Successfully backed up 12 address groups to texas-groups.yaml
```

## Best Practices

1. **Use Descriptive Names**: Choose names that clearly indicate the group's purpose and membership criteria.
2. **Prefer Dynamic Groups**: Use dynamic groups with tags for environments where membership changes frequently.
3. **Document Filter Expressions**: Always include descriptions explaining dynamic group filter logic.
4. **Apply Tags**: Use tags to categorize groups for easier management.
5. **Use YAML for Bulk Operations**: For large deployments, use YAML files to manage address groups.
6. **Organize by Folder**: Keep address groups organized in logical folders alongside their member addresses.
