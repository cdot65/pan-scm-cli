# Application Objects

Application objects define custom applications with detailed security attributes in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load application objects.

## Overview

The `application` commands allow you to:

- Create and update custom application definitions
- Define application category, subcategory, and technology
- Set risk levels and security characteristics
- Configure protocol and port mappings
- Export applications for backup or migration

## Set Application

Create or update an application object.

### Syntax

```bash
scm set object application NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the application | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes\* |
| `--snippet TEXT` | Snippet location | Yes\* |
| `--device TEXT` | Device location | Yes\* |
| `--category TEXT` | Primary category | Yes |
| `--subcategory TEXT` | Subcategory within the main category | Yes |
| `--technology TEXT` | Technology type | Yes |
| `--risk INTEGER` | Risk level (1-5) | Yes |
| `--ports TEXT` | Protocol/port combination, e.g. `tcp/8080` (repeat for multiple) | No |
| `--description TEXT` | Description of the application | No |
| `--tags TEXT` | Tag to apply (repeat for multiple) | No |
| `--evasive` | Uses evasive techniques | No |
| `--pervasive` | Widely used | No |
| `--excessive-bandwidth-use` | Consumes excessive bandwidth | No |
| `--used-by-malware` | Known to be used by malware | No |
| `--transfers-files` | Can transfer files | No |
| `--has-known-vulnerabilities` | Has known security vulnerabilities | No |
| `--tunnels-other-apps` | Can tunnel other applications | No |
| `--prone-to-misuse` | Prone to misuse | No |
| `--no-certifications` | Lacks certifications | No |

\* Exactly one of `--folder`, `--snippet`, or `--device` is required.

### Examples

#### Create a Basic Application

```bash
$ scm set object application custom-crm \
    --folder Texas \
    --category business-systems \
    --subcategory database \
    --technology client-server \
    --risk 3 \
    --ports tcp/8080 --ports tcp/8443 \
    --description "Custom CRM application"
---> 100%
Created application: custom-crm in folder Texas
```

#### Create an Application with Security Attributes

```bash
$ scm set object application file-transfer-app \
    --folder Texas \
    --category collaboration \
    --subcategory file-sharing \
    --technology peer-to-peer \
    --risk 4 \
    --ports tcp/2121 --ports udp/2121 \
    --transfers-files \
    --has-known-vulnerabilities \
    --description "P2P file transfer application"
---> 100%
Created application: file-transfer-app in folder Texas
```

#### Create an Application with Tags

```bash
$ scm set object application database-app \
    --folder Shared \
    --category business-systems \
    --subcategory database \
    --technology client-server \
    --risk 1 \
    --ports tcp/1433 \
    --tags database --tags internal \
    --description "SQL Server application"
---> 100%
Created application: database-app in folder Shared
```

## Delete Application

Delete an application object from SCM.

### Syntax

```bash
scm delete object application NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the application object to delete | Yes |

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
$ scm delete object application custom-crm --folder Texas --force
---> 100%
Deleted application: custom-crm from folder Texas
```

## Load Applications

Load multiple application objects from a YAML file.

### Syntax

```bash
scm load object application [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing application definitions | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
applications:
  - name: custom-crm
    folder: Texas
    category: business-systems
    subcategory: database
    technology: client-server
    risk: 3
    description: "Custom CRM application"
    ports:
      - tcp/8080
      - tcp/8443

  - name: file-transfer-app
    folder: Texas
    category: collaboration
    subcategory: file-sharing
    technology: peer-to-peer
    risk: 4
    description: "P2P file transfer application"
    ports:
      - tcp/2121
      - udp/2121
    able_to_transfer_files: true
    has_known_vulnerabilities: true
```

### Examples

#### Load with Original Locations

```bash
$ scm load object application --file applications.yml
---> 100%
✓ Loaded application: custom-crm
✓ Loaded application: file-transfer-app

Successfully loaded 2 out of 2 applications from 'applications.yml'
```

#### Load with Folder Override

```bash
$ scm load object application --file applications.yml --folder Austin
---> 100%
✓ Loaded application: custom-crm
✓ Loaded application: file-transfer-app

Successfully loaded 2 out of 2 applications from 'applications.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all applications
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show Application

Display application objects.

### Syntax

```bash
scm show object application [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the application object to show; omit to list all | No |

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

#### Show Specific Application

```bash
$ scm show object application custom-crm --folder Texas
---> 100%
Application: custom-crm
  Location: Folder 'Texas'
  Category: business-systems
  Subcategory: database
  Technology: client-server
  Risk: 3
  Ports: tcp/8080, tcp/8443
  Description: Custom CRM application
  ID: 123e4567-e89b-12d3-a456-426614174000
```

#### List All Applications (Default Behavior)

```bash
$ scm show object application --folder Texas
---> 100%
Applications in folder 'Texas':
------------------------------------------------------------
Name: custom-crm
  Location: Folder 'Texas'
  Category: business-systems
  Subcategory: database
  Technology: client-server
  Risk: 3
  Ports: tcp/8080, tcp/8443
  Description: Custom CRM application
------------------------------------------------------------
Name: file-transfer-app
  Location: Folder 'Texas'
  Category: collaboration
  Subcategory: file-sharing
  Technology: peer-to-peer
  Risk: 4
  Ports: tcp/2121, udp/2121
  Security Attributes: able-to-transfer-files, has-known-vulnerabilities
  Description: P2P file transfer application
------------------------------------------------------------
```

## Backup Applications

Backup all application objects from a specified location to a YAML file.

### Syntax

```bash
scm backup object application [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup applications from | No\* |
| `--snippet TEXT` | Snippet to backup applications from | No\* |
| `--device TEXT` | Device to backup applications from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup object application --folder Texas
---> 100%
Successfully backed up 10 applications to application_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object application --folder Texas --file texas-applications.yaml
---> 100%
Successfully backed up 10 applications to texas-applications.yaml
```

## Best Practices

1. **Use Descriptive Names**: Choose clear, descriptive names for applications that indicate their purpose.
2. **Set Appropriate Risk Levels**: Risk levels (1-5) help in policy decisions and should reflect actual risk.
3. **Define Security Attributes**: Include relevant attributes like file transfer capability and vulnerability status.
4. **Use YAML for Bulk Operations**: For large deployments, use YAML files to manage applications.
5. **Validate First**: Use the `--dry-run` option to preview changes before applying them.
6. **Port Specifications**: Support ranges (e.g., "tcp/8000-8100") and comma-separated lists.
7. **Organize by Container**: Keep applications organized in appropriate folders, snippets, or devices.
