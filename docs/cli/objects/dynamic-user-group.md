# Dynamic User Group Objects

Dynamic user group objects automatically include users based on tag-based filter expressions in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load dynamic user group objects.

## Overview

Dynamic user groups allow you to:

- Create user groups with dynamic membership
- Define tag-based filter expressions
- Use boolean logic for complex grouping
- Integrate with User-ID for dynamic policy enforcement
- Apply tags and descriptions for organization

## Set Dynamic User Group

Create or update a dynamic user group object.

### Syntax

```bash
scm set object dynamic-user-group [OPTIONS]
```

### Options

| Option               | Description                                       | Required |
| -------------------- | ------------------------------------------------- | -------- |
| `--folder TEXT`      | Folder for the dynamic user group object          | Yes\*    |
| `--snippet TEXT`     | Snippet for the dynamic user group object         | Yes\*    |
| `--device TEXT`      | Device for the dynamic user group object          | Yes\*    |
| `--name TEXT`        | Name of the dynamic user group                    | Yes      |
| `--filter TEXT`      | Tag-based filter expression (max 2047 characters) | Yes      |
| `--description TEXT` | Description (max 1023 characters)                 | No       |
| `--tag LIST`         | Tags for categorization                           | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

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

| Option           | Description                                      | Required |
| ---------------- | ------------------------------------------------ | -------- |
| `--folder TEXT`  | Folder containing the dynamic user group object  | Yes\*    |
| `--snippet TEXT` | Snippet containing the dynamic user group object | Yes\*    |
| `--device TEXT`  | Device containing the dynamic user group object  | Yes\*    |
| `--name TEXT`    | Name of the dynamic user group object to delete  | Yes      |

\* You must specify exactly one of --folder, --snippet, or --device.

### Example

```bash
$ scm delete object dynamic-user-group --folder Texas --name it-admins
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

| Option           | Description                                                 | Required |
| ---------------- | ----------------------------------------------------------- | -------- |
| `--file TEXT`    | Path to YAML file containing dynamic user group definitions | Yes      |
| `--folder TEXT`  | Override folder location for all objects                    | No       |
| `--snippet TEXT` | Override snippet location for all objects                   | No       |
| `--device TEXT`  | Override device location for all objects                    | No       |
| `--dry-run`      | Preview changes without applying them                       | No       |

### YAML File Format

```yaml
---
dynamic_user_groups:
  - name: it-admins
    folder: Texas # Container location (folder, snippet, or device)
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

  - name: vpn-users
    folder: Texas
    filter: "'VPN-Access' and not 'Disabled'"
    description: "Users with VPN access"
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
✓ Loaded dynamic user group: vpn-users

Successfully loaded 5 out of 5 dynamic user groups from 'user-groups.yml'
```

#### Load with Folder Override

```bash
$ scm load object dynamic-user-group --file user-groups.yml --folder Austin
---> 100%
✓ Loaded dynamic user group: it-admins
✓ Loaded dynamic user group: remote-employees
✓ Loaded dynamic user group: privileged-users
✓ Loaded dynamic user group: contractors
✓ Loaded dynamic user group: vpn-users

Successfully loaded 5 out of 5 dynamic user groups from 'user-groups.yml'
```

!!! note
When using container override options (--folder, --snippet, --device), all dynamic user groups will be loaded into the specified container, ignoring the container specified in the YAML file.

## Show Dynamic User Group

Display dynamic user group objects.

### Syntax

```bash
scm show object dynamic-user-group [OPTIONS]
```

### Options

| Option           | Description                                      | Required |
| ---------------- | ------------------------------------------------ | -------- |
| `--folder TEXT`  | Folder containing the dynamic user group object  | Yes\*    |
| `--snippet TEXT` | Snippet containing the dynamic user group object | Yes\*    |
| `--device TEXT`  | Device containing the dynamic user group object  | Yes\*    |
| `--name TEXT`    | Name of the dynamic user group object to show    | No\*\*   |
| `--list`         | List all dynamic user groups in the container    | No\*\*   |

\* You must specify exactly one of --folder, --snippet, or --device.
\*\* If --name is not specified, all items will be listed.

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

| Option           | Description                                  | Required |
| ---------------- | -------------------------------------------- | -------- |
| `--folder TEXT`  | Folder to backup dynamic user groups from    | No\*     |
| `--snippet TEXT` | Snippet to backup dynamic user groups from   | No\*     |
| `--device TEXT`  | Device to backup dynamic user groups from    | No\*     |
| `--file TEXT`    | Output filename (defaults to auto-generated) | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

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

1. **Tag Strategy**: Establish a consistent tagging strategy for users

   - Department tags: Engineering, Sales, Finance
   - Role tags: Admin, Manager, Developer
   - Status tags: Active, Contractor, Remote

2. **Filter Simplicity**: Keep filter expressions as simple as possible while meeting requirements

3. **Naming Convention**: Use descriptive names that indicate group membership criteria

4. **Documentation**: Always include descriptions explaining the group's purpose

5. **Testing**: Test filter expressions with sample users before deployment

6. **Use YAML for Bulk Operations**: For complex deployments, use YAML files

7. **Organize by Container**: Keep groups organized in appropriate folders, snippets, or devices

## Filter Expression Syntax

### Basic Syntax

Filter expressions use tag names enclosed in single quotes:

- Single tag: `'TagName'`
- Multiple tags with AND: `'Tag1' and 'Tag2'`
- Multiple tags with OR: `'Tag1' or 'Tag2'`

### Boolean Operators

- **and**: Both conditions must be true
- **or**: At least one condition must be true
- **not**: Negates the condition

### Parentheses for Grouping

Use parentheses to control evaluation order:

```
'Department' and ('Role1' or 'Role2' or 'Role3')
```

### Complex Expressions

Examples of complex filter expressions:

```bash
# Users in IT who are either admins or managers
"'IT' and ('Admin' or 'Manager')"

# Remote users not in engineering
"'Remote' and not 'Engineering'"

# Executives or admins, but not contractors
"('Executive' or 'Admin') and not 'Contractor'"

# Users in multiple departments with specific roles
"('Sales' or 'Marketing') and ('Manager' or 'Director')"
```

## Additional Examples

### Create Department-Based Groups

```bash
$ scm set object dynamic-user-group \
    --folder Shared \
    --name engineering \
    --filter "'Engineering' and 'Active'" \
    --description "Active engineering team members"
---> 100%
Created dynamic user group: engineering in folder Shared
```

### Create Access-Based Groups

```bash
$ scm set object dynamic-user-group \
    --folder Shared \
    --name remote-access \
    --filter "'VPN-Access' or 'Remote-Desktop'" \
    --tag "remote,monitor" \
    --description "VPN and remote access users"
---> 100%
Created dynamic user group: remote-access in folder Shared
```

### Create Groups with Complex Filters

```bash
$ scm set object dynamic-user-group \
    --folder Texas \
    --name privileged-users \
    --filter "'Executive' or 'Admin' or 'Finance-Manager'" \
    --tag "high-privilege,monitor" \
    --description "Users with elevated privileges"
---> 100%
Created dynamic user group: privileged-users in folder Texas
```

## Integration with Security Policies

Dynamic user groups are used in security rules for user-based access control:

```bash
$ scm set security rule \
    --folder Shared \
    --name "IT-Admin-Access" \
    --source-users "@it-admins" \
    --destination-zones "Servers" \
    --applications "ssh,rdp" \
    --action allow
---> 100%
Created security rule: IT-Admin-Access in folder Shared
```

## User-ID Integration

Dynamic user groups require User-ID to function properly:

1. **User Tagging**: Users must be tagged in the User-ID system
2. **Tag Propagation**: Tags are distributed to firewalls via User-ID
3. **Dynamic Updates**: Group membership updates automatically as tags change
4. **Real-time Enforcement**: Policy enforcement reflects current group membership

## Troubleshooting

### Common Issues

1. **Empty Groups**: Ensure users have the required tags in User-ID
2. **Filter Syntax**: Check for proper quoting and parentheses
3. **Tag Names**: Verify exact tag names (case-sensitive)
4. **Boolean Logic**: Test complex expressions with simple cases first

### Filter Validation

Test filter logic:

```bash
# Simple test
"'TestTag'"

# Incremental complexity
"'TestTag1' and 'TestTag2'"
"'TestTag1' and ('TestTag2' or 'TestTag3')"
```

## Notes

- Group names must be unique within a container
- Filter expressions are case-sensitive
- Maximum filter length is 2047 characters
- Tags must exist in the User-ID system
- Groups are referenced in policies using the "@" prefix
- Membership is dynamic and updates in real-time
- Use single quotes around tag names in filter expressions
- Boolean operators (and, or, not) must be lowercase
