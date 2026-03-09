# Dynamic User Group Objects

Dynamic user group objects automatically include users based on tag-based filter expressions in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load dynamic user group objects.

## Overview

The `dynamic-user-group` commands allow you to:

- Create user groups with dynamic membership based on tags
- Define tag-based filter expressions with boolean logic
- Delete dynamic user groups that are no longer needed
- Bulk import dynamic user groups from YAML files
- Export dynamic user groups for backup or migration

## Filter Expression Syntax

Filter expressions use tag names enclosed in single quotes with boolean operators:

| Operator | Description | Example |
| --- | --- | --- |
| `and` | Both conditions must be true | `'Tag1' and 'Tag2'` |
| `or` | At least one condition must be true | `'Tag1' or 'Tag2'` |
| `not` | Negates the condition | `not 'Tag1'` |
| `()` | Groups for evaluation order | `'Dept' and ('Role1' or 'Role2')` |

## Set Dynamic User Group

Create or update a dynamic user group object.

### Syntax

```bash
scm set object dynamic-user-group [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder for the dynamic user group object | No\* |
| `--snippet TEXT` | Snippet for the dynamic user group object | No\* |
| `--device TEXT` | Device for the dynamic user group object | No\* |
| `--name TEXT` | Name of the dynamic user group | Yes |
| `--filter TEXT` | Tag-based filter expression (max 2047 characters) | Yes |
| `--description TEXT` | Description (max 1023 characters) | No |
| `--tag LIST` | Tags for categorization | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create Basic Dynamic User Group

```bash
$ scm set object dynamic-user-group \
    --folder Texas \
    --name it-admins \
    --filter "'IT' and 'Admin'" \
    --description "IT department administrators"
---> 100%
Created dynamic user group: it-admins in folder Texas
```

#### Create with Complex Filter Expression

```bash
$ scm set object dynamic-user-group \
    --folder Texas \
    --name remote-employees \
    --filter "'Remote' and ('Engineering' or 'Sales' or 'Support')" \
    --description "Remote workers in technical departments"
---> 100%
Created dynamic user group: remote-employees in folder Texas
```

## Delete Dynamic User Group

Delete a dynamic user group object from SCM.

### Syntax

```bash
scm delete object dynamic-user-group [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the dynamic user group object | No\* |
| `--snippet TEXT` | Snippet containing the dynamic user group object | No\* |
| `--device TEXT` | Device containing the dynamic user group object | No\* |
| `--name TEXT` | Name of the dynamic user group object to delete | Yes |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete object dynamic-user-group --folder Texas --name it-admins --force
---> 100%
Deleted dynamic user group: it-admins from folder Texas
```

## Load Dynamic User Groups

Load multiple dynamic user group objects from a YAML file.

### Syntax

```bash
scm load object dynamic-user-group [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing dynamic user group definitions | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
dynamic_user_groups:
  - name: it-admins
    folder: Texas
    filter: "'IT' and 'Admin'"
    description: "IT department administrators"

  - name: remote-employees
    folder: Texas
    filter: "'Remote' and ('Engineering' or 'Sales' or 'Support')"
    description: "Remote workers in technical departments"

  - name: privileged-users
    folder: Texas
    filter: "'Executive' or 'Admin' or 'Finance-Manager'"
    description: "Users with elevated privileges"
    tags:
      - high-privilege
      - monitor

  - name: contractors
    folder: Texas
    filter: "'Contractor' and not 'Permanent'"
    description: "External contractors"
    tags:
      - external
      - temporary
```

### Examples

#### Load with Original Locations

```bash
$ scm load object dynamic-user-group --file user-groups.yml
---> 100%
✓ Loaded dynamic user group: it-admins
✓ Loaded dynamic user group: remote-employees
✓ Loaded dynamic user group: privileged-users
✓ Loaded dynamic user group: contractors

Successfully loaded 4 out of 4 dynamic user groups from 'user-groups.yml'
```

#### Load with Folder Override

```bash
$ scm load object dynamic-user-group --file user-groups.yml --folder Austin
---> 100%
✓ Loaded dynamic user group: it-admins
✓ Loaded dynamic user group: remote-employees
✓ Loaded dynamic user group: privileged-users
✓ Loaded dynamic user group: contractors

Successfully loaded 4 out of 4 dynamic user groups from 'user-groups.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all dynamic
    user groups will be loaded into the specified container, ignoring the container
    specified in the YAML file.

## Show Dynamic User Group

Display dynamic user group objects.

### Syntax

```bash
scm show object dynamic-user-group [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the dynamic user group object | No\* |
| `--snippet TEXT` | Snippet containing the dynamic user group object | No\* |
| `--device TEXT` | Device containing the dynamic user group object | No\* |
| `--name TEXT` | Name of the dynamic user group object to show | No |

!!! note
    When no `--name` is specified, all items are listed by default.

\* One of --folder, --snippet, or --device is required.

### Examples

#### Show Specific Dynamic User Group

```bash
$ scm show object dynamic-user-group --folder Texas --name it-admins
---> 100%
Dynamic User Group: it-admins
  Location: Folder 'Texas'
  Filter: 'IT' and 'Admin'
  Description: IT department administrators
  Tags: None
  ID: 123e4567-e89b-12d3-a456-426614174000
```

#### List All Dynamic User Groups (Default Behavior)

```bash
$ scm show object dynamic-user-group --folder Texas
---> 100%
Dynamic User Groups in folder 'Texas':
------------------------------------------------------------
Name: it-admins
  Location: Folder 'Texas'
  Filter: 'IT' and 'Admin'
  Description: IT department administrators
------------------------------------------------------------
Name: remote-employees
  Location: Folder 'Texas'
  Filter: 'Remote' and ('Engineering' or 'Sales' or 'Support')
  Description: Remote workers in technical departments
------------------------------------------------------------
Name: privileged-users
  Location: Folder 'Texas'
  Filter: 'Executive' or 'Admin' or 'Finance-Manager'
  Tags: high-privilege, monitor
  Description: Users with elevated privileges
------------------------------------------------------------
```

## Backup Dynamic User Groups

Backup all dynamic user group objects from a specified location to a YAML file.

### Syntax

```bash
scm backup object dynamic-user-group [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup dynamic user groups from | No\* |
| `--snippet TEXT` | Snippet to backup dynamic user groups from | No\* |
| `--device TEXT` | Device to backup dynamic user groups from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup object dynamic-user-group --folder Texas
---> 100%
Successfully backed up 10 dynamic user groups to dynamic-user-group_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object dynamic-user-group --folder Texas --file texas-user-groups.yaml
---> 100%
Successfully backed up 10 dynamic user groups to texas-user-groups.yaml
```

## Best Practices

1. **Tag Strategy**: Establish a consistent tagging strategy with department, role, and status tags.
2. **Filter Simplicity**: Keep filter expressions as simple as possible while meeting requirements.
3. **Naming Convention**: Use descriptive names that indicate group membership criteria.
4. **Documentation**: Always include descriptions explaining the group's purpose and filter logic.
5. **Testing**: Test filter expressions with sample users before deployment.
6. **Use YAML for Bulk Operations**: For complex deployments, use YAML files.
7. **Organize by Container**: Keep groups organized in appropriate folders, snippets, or devices.
