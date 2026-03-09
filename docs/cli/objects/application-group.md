# Application Group Objects

Application group objects logically group multiple applications together for use in security policies in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load application group objects.

## Overview

The `application-group` commands allow you to:

- Create and manage groups of applications
- Reference both built-in and custom applications
- Delete application groups that are no longer needed
- Bulk import application groups from YAML files
- Export application groups for backup or migration

## Set Application Group

Create or update an application group object.

### Syntax

```bash
scm set object application-group [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder for the application group object | No\* |
| `--snippet TEXT` | Snippet for the application group object | No\* |
| `--device TEXT` | Device for the application group object | No\* |
| `--name TEXT` | Name of the application group | Yes |
| `--members LIST` | Comma-separated list of application names | Yes |
| `--description TEXT` | Description of the group | No |
| `--tag LIST` | Tags for categorization | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create a Basic Application Group

```bash
$ scm set object application-group \
    --folder Texas \
    --name business-apps \
    --members "salesforce,office365,zoom,custom-crm" \
    --description "Business critical applications"
---> 100%
Created application group: business-apps in folder Texas
```

#### Create an Application Group with Tags

```bash
$ scm set object application-group \
    --folder Texas \
    --name collaboration-tools \
    --members "slack,ms-teams,zoom,webex" \
    --tag "collaboration,approved" \
    --description "Approved collaboration applications"
---> 100%
Created application group: collaboration-tools in folder Texas
```

## Delete Application Group

Delete an application group object from SCM.

### Syntax

```bash
scm delete object application-group [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the application group object | No\* |
| `--snippet TEXT` | Snippet containing the application group object | No\* |
| `--device TEXT` | Device containing the application group object | No\* |
| `--name TEXT` | Name of the application group object to delete | Yes |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete object application-group --folder Texas --name business-apps --force
---> 100%
Deleted application group: business-apps from folder Texas
```

## Load Application Groups

Load multiple application group objects from a YAML file.

### Syntax

```bash
scm load object application-group [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing application group definitions | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
application_groups:
  - name: business-apps
    folder: Texas
    description: "Business critical applications"
    members:
      - salesforce
      - office365
      - zoom
      - custom-crm

  - name: collaboration-tools
    folder: Texas
    description: "Approved collaboration applications"
    members:
      - slack
      - ms-teams
      - zoom
      - webex
    tag:
      - collaboration
      - approved
```

### Examples

#### Load with Original Locations

```bash
$ scm load object application-group --file app-groups.yml
---> 100%
✓ Loaded application group: business-apps
✓ Loaded application group: collaboration-tools

Successfully loaded 2 out of 2 application groups from 'app-groups.yml'
```

#### Load with Folder Override

```bash
$ scm load object application-group --file app-groups.yml --folder Austin
---> 100%
✓ Loaded application group: business-apps
✓ Loaded application group: collaboration-tools

Successfully loaded 2 out of 2 application groups from 'app-groups.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all application
    groups will be loaded into the specified container, ignoring the container specified
    in the YAML file.

## Show Application Group

Display application group objects.

### Syntax

```bash
scm show object application-group [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the application group object | No\* |
| `--snippet TEXT` | Snippet containing the application group object | No\* |
| `--device TEXT` | Device containing the application group object | No\* |
| `--name TEXT` | Name of the application group object to show | No |

!!! note
    When no `--name` is specified, all items are listed by default.

\* One of --folder, --snippet, or --device is required.

### Examples

#### Show Specific Application Group

```bash
$ scm show object application-group --folder Texas --name business-apps
---> 100%
Application Group: business-apps
  Location: Folder 'Texas'
  Members: salesforce, office365, zoom, custom-crm
  Description: Business critical applications
  Tags: None
  ID: 123e4567-e89b-12d3-a456-426614174000
```

#### List All Application Groups (Default Behavior)

```bash
$ scm show object application-group --folder Texas
---> 100%
Application Groups in folder 'Texas':
------------------------------------------------------------
Name: business-apps
  Location: Folder 'Texas'
  Members: salesforce, office365, zoom, custom-crm
  Description: Business critical applications
------------------------------------------------------------
Name: collaboration-tools
  Location: Folder 'Texas'
  Members: slack, ms-teams, zoom, webex
  Tags: collaboration, approved
  Description: Approved collaboration applications
------------------------------------------------------------
```

## Backup Application Groups

Backup all application group objects from a specified location to a YAML file.

### Syntax

```bash
scm backup object application-group [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup application groups from | No\* |
| `--snippet TEXT` | Snippet to backup application groups from | No\* |
| `--device TEXT` | Device to backup application groups from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup object application-group --folder Texas
---> 100%
Successfully backed up 10 application groups to application-group_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object application-group --folder Texas --file texas-app-groups.yaml
---> 100%
Successfully backed up 10 application groups to texas-app-groups.yaml
```

## Best Practices

1. **Logical Grouping**: Group applications that serve similar purposes or have similar security requirements.
2. **Naming Convention**: Use descriptive names that indicate the group's purpose.
3. **Documentation**: Always include descriptions to explain the group's purpose.
4. **Tag Usage**: Use tags to categorize groups for easier management.
5. **Regular Review**: Periodically review group membership to ensure accuracy.
6. **Use YAML for Bulk Operations**: For complex deployments, use YAML files.
7. **Organize by Container**: Keep groups organized in appropriate folders, snippets, or devices.
