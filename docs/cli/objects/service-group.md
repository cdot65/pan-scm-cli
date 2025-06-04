# Service Group Management

This section covers the commands for managing service group objects in Strata Cloud Manager.

## Overview

Service groups provide a way to logically group multiple services together for use in security policies. The `service-group` commands allow you to:

- Create groups of related services
- Reference both custom and built-in services
- Create nested service groups
- Use service groups in policies
- Apply tags for organization

## Commands

### Creating/Updating Service Groups

Basic service group:

```bash
$ scm set objects service-group --folder Texas --name web-services \
  --members "http,https,ssl,web-browsing" \
  --description "Standard web services"
<span style="color: green;">✓</span> Service group 'web-services' created successfully
```

Service group with custom services:

```bash
$ scm set objects service-group --folder Texas --name database-services \
  --members "mysql,ms-sql,oracle,postgresql,custom-db" \
  --tag "database,backend" \
  --description "Database service ports"
<span style="color: green;">✓</span> Service group 'database-services' created successfully
```

Nested service group:

```bash
$ scm set objects service-group --folder Texas --name all-services \
  --members "web-services,database-services,mail-services" \
  --description "All allowed services (nested groups)"
<span style="color: green;">✓</span> Service group 'all-services' created successfully
```

### Listing Service Groups (Default Behavior)

```bash
$ scm show objects service-group --folder Texas
Service groups in folder 'Texas':
- web-services
- database-services
- mail-services
- all-services
```

!!! note
When no --name is specified, all service groups are listed by default.

### Showing Service Group Details

```bash
$ scm show objects service-group --folder Texas --name web-services
Service Group: web-services
  Members: http, https, ssl, web-browsing
  Description: Standard web services
  Tags: None
  Folder: Texas
```

### Deleting Service Groups

```bash
$ scm delete objects service-group --folder Texas --name web-services
<span style="color: green;">✓</span> Service group 'web-services' deleted successfully
```

### Load Service Groups

Load multiple service groups from a YAML file.

#### Syntax

```bash
scm load objects service-group [OPTIONS]
```

#### Options

| Option           | Description                                            | Required |
| ---------------- | ------------------------------------------------------ | -------- |
| `--file TEXT`    | Path to YAML file containing service group definitions | Yes      |
| `--folder TEXT`  | Override folder location for all objects               | No       |
| `--snippet TEXT` | Override snippet location for all objects              | No       |
| `--device TEXT`  | Override device location for all objects               | No       |
| `--dry-run`      | Preview changes without applying them                  | No       |

#### Examples

Load from file with original locations:

```bash
$ scm load objects service-group --file service-groups.yml
<span style="color: green;">✓</span> Loaded service group: web-services
<span style="color: green;">✓</span> Loaded service group: database-services
<span style="color: green;">✓</span> Loaded service group: mail-services
<span style="color: green;">✓</span> Loaded service group: all-services

Successfully loaded 4 out of 4 service groups from 'service-groups.yml'
```

Load with folder override:

```bash
$ scm load objects service-group --file service-groups.yml --folder Austin
<span style="color: green;">✓</span> Loaded service group: web-services
<span style="color: green;">✓</span> Loaded service group: database-services
<span style="color: green;">✓</span> Loaded service group: mail-services
<span style="color: green;">✓</span> Loaded service group: all-services

Successfully loaded 4 out of 4 service groups from 'service-groups.yml'
```

!!! note
When using container override options (--folder, --snippet, --device), all service groups will be loaded into the specified container, ignoring the container specified in the YAML file.

### Backup Service Groups

Backup all service group objects from a specified location to a YAML file.

#### Syntax

```bash
scm backup objects service-group [OPTIONS]
```

#### Options

| Option           | Description                                  | Required |
| ---------------- | -------------------------------------------- | -------- |
| `--folder TEXT`  | Folder to backup service groups from         | No\*     |
| `--snippet TEXT` | Snippet to backup service groups from        | No\*     |
| `--device TEXT`  | Device to backup service groups from         | No\*     |
| `--file TEXT`    | Output filename (defaults to auto-generated) | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

#### Examples

Backup from folder:

```bash
$ scm backup objects service-group --folder Texas
<span style="color: green;">✓</span> Successfully backed up 8 service groups to service-group_folder_texas_20240115_120530.yaml
```

Backup with custom filename:

```bash
$ scm backup objects service-group --folder Texas --file texas-service-groups.yaml
<span style="color: green;">✓</span> Successfully backed up 8 service groups to texas-service-groups.yaml
```

## YAML Configuration Format

Service groups can be defined in YAML for bulk operations:

```yaml
service_groups:
  - name: web-services
    folder: Texas # Container location (folder, snippet, or device)
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

  - name: file-transfer
    folder: Texas
    description: "File transfer services"
    members:
      - ftp
      - ftps
      - sftp
      - tftp
      - custom-file-transfer

  - name: all-services
    folder: Texas
    description: "All allowed services (nested groups)"
    members:
      - web-services
      - database-services
      - mail-services
      - file-transfer
```

## Configuration Options

### Required Parameters

- `--name`: Name of the service group
- `--members`: Comma-separated list of service or service group names

### Optional Parameters

- `--description`: Detailed description of the group
- `--tag`: Tags for categorization (comma-separated)

### Context Parameters

Exactly one context parameter must be specified:

- `--folder`: Folder name (e.g., "Texas", "Shared")
- `--snippet`: Snippet name for Panorama
- `--device`: Device name for NGFW

## Examples

### Create a Basic Service Group

```bash
scm set objects service-group --folder Shared --name web-apps \
  --members "http,https,ssl"
```

### Create a Comprehensive Service Group

```bash
scm set objects service-group --folder Shared --name enterprise-apps \
  --members "ldap,ldaps,kerberos,radius,tacacs,custom-auth" \
  --tag "authentication,enterprise" \
  --description "Enterprise authentication services"
```

### Create a Nested Service Group

```bash
scm set objects service-group --folder Shared --name dmz-services \
  --members "web-services,mail-services,dns,ntp" \
  --tag "dmz,public" \
  --description "Services allowed in DMZ"
```

## Best Practices

1. **Logical Grouping**: Group services that are used together in policies

2. **Naming Convention**: Use descriptive names that indicate the group's purpose

3. **Avoid Over-Nesting**: While nesting is supported, avoid deep nesting for clarity

4. **Documentation**: Always include descriptions to explain the group's purpose

5. **Regular Review**: Periodically review group membership to ensure accuracy

## Integration with Security Policies

Service groups are commonly used in security rules:

```bash
# Allow web services
scm set security rule --folder Shared --name "Allow-Web-Traffic" \
  --source-zones "Trust" --destination-zones "DMZ" \
  --services "@web-services" --action allow

# Block database access from untrusted zones
scm set security rule --folder Shared --name "Protect-Databases" \
  --source-zones "Untrust" --destination-zones "Database" \
  --services "@database-services" --action deny
```

## Advanced Features

### Nested Groups

Service groups can contain other service groups, allowing for hierarchical organization:

```bash
# Create base groups
scm set objects service-group --folder Shared --name tcp-services \
  --members "http,https,ssh,telnet"

scm set objects service-group --folder Shared --name udp-services \
  --members "dns,ntp,snmp,syslog"

# Create parent group
scm set objects service-group --folder Shared --name all-protocols \
  --members "tcp-services,udp-services"
```

### Dynamic Membership

While service group membership is static, you can use tags and scripts to manage groups dynamically:

```bash
# Tag services
scm set objects service --folder Shared --name custom-app1 \
  --protocol tcp --port 9001 --tag "dynamic-group"

# Use external tools to update groups based on tags
```

## Notes

- Service group names must be unique within a folder
- Members must be existing services or service groups
- Circular references are not allowed
- Groups can mix built-in and custom services
- Groups can contain other groups (nested)
- Tags must exist before being referenced
- Groups are referenced in policies using the "@" prefix
- Member names must be unique (no duplicates)
