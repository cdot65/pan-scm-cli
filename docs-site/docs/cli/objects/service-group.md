# Service Group Objects

Service groups logically group multiple services together for use in security policies in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load service group objects.

## Overview

The `service-group` commands allow you to:

- Create groups of related services
- Reference both custom and built-in services
- Create nested service groups (groups containing groups)
- Delete service groups that are no longer needed
- Bulk import service groups from YAML files
- Export service groups for backup or migration

## Set Service Group

Create or update a service group object.

### Syntax

```bash
scm set object service-group [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder for the service group object | No\* |
| `--snippet TEXT` | Snippet for the service group object | No\* |
| `--device TEXT` | Device for the service group object | No\* |
| `--name TEXT` | Name of the service group | Yes |
| `--members TEXT` | Comma-separated list of service or service group names | Yes |
| `--description TEXT` | Description of the group | No |
| `--tag TEXT` | Tags for categorization (comma-separated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create a Basic Service Group

```bash
$ scm set object service-group \
    --folder Texas \
    --name web-services \
    --members "http,https,ssl,web-browsing" \
    --description "Standard web services"
---> 100%
Created service group: web-services in folder Texas
```

#### Create a Service Group with Tags

```bash
$ scm set object service-group \
    --folder Texas \
    --name database-services \
    --members "mysql,ms-sql,oracle,postgresql,custom-db" \
    --tag "database,backend" \
    --description "Database service ports"
---> 100%
Created service group: database-services in folder Texas
```

#### Create a Nested Service Group

```bash
$ scm set object service-group \
    --folder Texas \
    --name all-services \
    --members "web-services,database-services,mail-services" \
    --description "All allowed services (nested groups)"
---> 100%
Created service group: all-services in folder Texas
```

## Delete Service Group

Delete a service group object from SCM.

### Syntax

```bash
scm delete object service-group [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the service group object | No\* |
| `--snippet TEXT` | Snippet containing the service group object | No\* |
| `--device TEXT` | Device containing the service group object | No\* |
| `--name TEXT` | Name of the service group to delete | Yes |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete object service-group --folder Texas --name web-services --force
---> 100%
Deleted service group: web-services from folder Texas
```

## Load Service Groups

Load multiple service group objects from a YAML file.

### Syntax

```bash
scm load object service-group [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing service group definitions | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
service_groups:
  - name: web-services
    folder: Texas
    description: "Standard web services"
    members:
      - http
      - https
      - ssl
      - web-browsing

  - name: database-services
    folder: Texas
    description: "Database service ports"
    members:
      - mysql
      - ms-sql
      - oracle
      - postgresql
      - custom-db
    tag:
      - database
      - backend

  - name: mail-services
    folder: Texas
    description: "Email services"
    members:
      - smtp
      - smtps
      - pop3
      - pop3s
      - imap
      - imaps
    tag:
      - email

  - name: all-services
    folder: Texas
    description: "All allowed services (nested groups)"
    members:
      - web-services
      - database-services
      - mail-services
```

### Examples

#### Load with Original Locations

```bash
$ scm load object service-group --file service-groups.yml
---> 100%
✓ Loaded service group: web-services
✓ Loaded service group: database-services
✓ Loaded service group: mail-services
✓ Loaded service group: all-services

Successfully loaded 4 out of 4 service groups from 'service-groups.yml'
```

#### Load with Folder Override

```bash
$ scm load object service-group --file service-groups.yml --folder Austin
---> 100%
✓ Loaded service group: web-services
✓ Loaded service group: database-services
✓ Loaded service group: mail-services
✓ Loaded service group: all-services

Successfully loaded 4 out of 4 service groups from 'service-groups.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all service
groups will be loaded into the specified container, ignoring the container specified
in the YAML file.
:::

## Show Service Group

Display service group objects.

### Syntax

```bash
scm show object service-group [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the service group object | No\* |
| `--snippet TEXT` | Snippet containing the service group object | No\* |
| `--device TEXT` | Device containing the service group object | No\* |
| `--name TEXT` | Name of the service group to show | No |

:::note
When no `--name` is specified, all items are listed by default.
:::

\* One of --folder, --snippet, or --device is required.

### Examples

#### Show Specific Service Group

```bash
$ scm show object service-group --folder Texas --name web-services
---> 100%
Service Group: web-services
  Location: Folder 'Texas'
  Members: http, https, ssl, web-browsing
  Description: Standard web services
  Tags: None
```

#### List All Service Groups (Default Behavior)

```bash
$ scm show object service-group --folder Texas
---> 100%
Service Groups in folder 'Texas':
------------------------------------------------------------
Name: web-services
  Members: http, https, ssl, web-browsing
  Description: Standard web services
------------------------------------------------------------
Name: database-services
  Members: mysql, ms-sql, oracle, postgresql, custom-db
  Tags: database, backend
  Description: Database service ports
------------------------------------------------------------
Name: all-services
  Members: web-services, database-services, mail-services
  Description: All allowed services (nested groups)
------------------------------------------------------------
```

## Backup Service Groups

Backup all service group objects from a specified location to a YAML file.

### Syntax

```bash
scm backup object service-group [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup service groups from | No\* |
| `--snippet TEXT` | Snippet to backup service groups from | No\* |
| `--device TEXT` | Device to backup service groups from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup object service-group --folder Texas
---> 100%
Successfully backed up 8 service groups to service-group_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object service-group --folder Texas --file texas-service-groups.yaml
---> 100%
Successfully backed up 8 service groups to texas-service-groups.yaml
```

## Best Practices

1. **Logical Grouping**: Group services that are used together in policies.
2. **Naming Convention**: Use descriptive names that indicate the group's purpose.
3. **Avoid Over-Nesting**: While nesting is supported, avoid deep nesting for clarity.
4. **Documentation**: Always include descriptions to explain the group's purpose.
5. **Regular Review**: Periodically review group membership to ensure accuracy.
6. **Use YAML for Bulk Operations**: For complex deployments, use YAML files.
