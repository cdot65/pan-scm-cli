# Application Objects

Application objects define custom applications with detailed security attributes in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load application objects.

## Overview

Application objects allow you to:

- Create and update custom application definitions
- Define application category, subcategory, and technology
- Set risk levels and security characteristics
- Configure protocol and port mappings
- Manage application descriptions and metadata

## Set Application

Create or update an application object.

### Syntax

```bash
scm set object application [OPTIONS]
```

### Options

| Option                          | Description                          | Required |
| ------------------------------- | ------------------------------------ | -------- |
| `--folder TEXT`                 | Folder for the application object    | Yes\*    |
| `--snippet TEXT`                | Snippet for the application object   | Yes\*    |
| `--device TEXT`                 | Device for the application object    | Yes\*    |
| `--name TEXT`                   | Name of the application              | Yes      |
| `--category TEXT`               | Primary category                     | Yes      |
| `--subcategory TEXT`            | Subcategory within the main category | Yes      |
| `--technology TEXT`             | Technology type                      | Yes      |
| `--risk INT`                    | Risk level (1-5)                     | Yes      |
| `--ports LIST`                  | Protocol and port combinations       | Yes      |
| `--description TEXT`            | Description of the application       | No       |
| `--able-to-transfer-files`      | Can transfer files                   | No       |
| `--has-known-vulnerabilities`   | Has known security vulnerabilities   | No       |
| `--tunnels-other-applications`  | Can tunnel other applications        | No       |
| `--evasive`                     | Uses evasive techniques              | No       |
| `--pervasive`                   | Pervasive use                        | No       |
| `--excessive-bandwidth-use`     | Consumes excessive bandwidth         | No       |
| `--used-by-malware`             | Known to be used by malware          | No       |
| `--no-app-id-caching`           | Disable app-id caching               | No       |
| `--parent-app TEXT`             | Parent application name              | No       |
| `--timeout INT`                 | Session timeout in seconds           | No       |
| `--tcp-timeout INT`             | TCP session timeout                  | No       |
| `--udp-timeout INT`             | UDP session timeout                  | No       |
| `--tcp-half-closed-timeout INT` | TCP half-closed timeout              | No       |
| `--tcp-time-wait-timeout INT`   | TCP time-wait timeout                | No       |
| `--tag LIST`                    | Tags for categorization              | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

### Examples

#### Create a Basic Application

```bash
$ scm set object application \
    --folder Texas \
    --name custom-crm \
    --category business-systems \
    --subcategory database \
    --technology client-server \
    --risk 3 \
    --ports "tcp/8080,tcp/8443" \
    --description "Custom CRM application"
---> 100%
Created application: custom-crm in folder Texas
```

#### Create an Application with Security Attributes

```bash
$ scm set object application \
    --folder Texas \
    --name file-transfer-app \
    --category collaboration \
    --subcategory file-sharing \
    --technology peer-to-peer \
    --risk 4 \
    --ports "tcp/2121,udp/2121" \
    --able-to-transfer-files \
    --has-known-vulnerabilities \
    --description "P2P file transfer application"
---> 100%
Created application: file-transfer-app in folder Texas
```

## Delete Application

Delete an application object from SCM.

### Syntax

```bash
scm delete object application [OPTIONS]
```

### Options

| Option           | Description                               | Required |
| ---------------- | ----------------------------------------- | -------- |
| `--folder TEXT`  | Folder containing the application object  | Yes\*    |
| `--snippet TEXT` | Snippet containing the application object | Yes\*    |
| `--device TEXT`  | Device containing the application object  | Yes\*    |
| `--name TEXT`    | Name of the application object to delete  | Yes      |

\* You must specify exactly one of --folder, --snippet, or --device.

### Example

```bash
$ scm delete object application --folder Texas --name custom-crm
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

| Option           | Description                                          | Required |
| ---------------- | ---------------------------------------------------- | -------- |
| `--file TEXT`    | Path to YAML file containing application definitions | Yes      |
| `--folder TEXT`  | Override folder location for all objects             | No       |
| `--snippet TEXT` | Override snippet location for all objects            | No       |
| `--device TEXT`  | Override device location for all objects             | No       |
| `--dry-run`      | Preview changes without applying them                | No       |

### YAML File Format

```yaml
---
applications:
  - name: custom-crm
    folder: Texas # Container location (folder, snippet, or device)
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

  - name: mobile-sales
    folder: Texas
    category: business-systems
    subcategory: sales-force-automation
    technology: mobile-application
    risk: 2
    description: "Mobile sales application"
    ports:
      - tcp/443
    uses_encryption: true
    tunnel_applications: true
```

### Examples

#### Load with Original Locations

```bash
$ scm load object application --file applications.yml
---> 100%
✓ Loaded application: custom-crm
✓ Loaded application: file-transfer-app
✓ Loaded application: mobile-sales

Successfully loaded 3 out of 3 applications from 'applications.yml'
```

#### Load with Folder Override

```bash
$ scm load object application --file applications.yml --folder Austin
---> 100%
✓ Loaded application: custom-crm
✓ Loaded application: file-transfer-app
✓ Loaded application: mobile-sales

Successfully loaded 3 out of 3 applications from 'applications.yml'
```

!!! note
When using container override options (--folder, --snippet, --device), all applications will be loaded into the specified container, ignoring the container specified in the YAML file.

## Show Application

Display application objects.

### Syntax

```bash
scm show object application [OPTIONS]
```

### Options

| Option           | Description                               | Required |
| ---------------- | ----------------------------------------- | -------- |
| `--folder TEXT`  | Folder containing the application object  | Yes\*    |
| `--snippet TEXT` | Snippet containing the application object | Yes\*    |
| `--device TEXT`  | Device containing the application object  | Yes\*    |
| `--name TEXT`    | Name of the application object to show    | No\*\*   |
| `--list`         | List all applications in the container    | No\*\*   |

\* You must specify exactly one of --folder, --snippet, or --device.
\*\* If --name is not specified, all items will be listed.

### Examples

#### Show Specific Application

```bash
$ scm show object application --folder Texas --name custom-crm
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

| Option           | Description                                  | Required |
| ---------------- | -------------------------------------------- | -------- |
| `--folder TEXT`  | Folder to backup applications from           | No\*     |
| `--snippet TEXT` | Snippet to backup applications from          | No\*     |
| `--device TEXT`  | Device to backup applications from           | No\*     |
| `--file TEXT`    | Output filename (defaults to auto-generated) | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

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

1. **Use Descriptive Names**: Choose clear, descriptive names for applications
2. **Set Appropriate Risk Levels**: Risk levels (1-5) help in policy decisions
3. **Define All Security Attributes**: Include relevant security attributes like file transfer and vulnerability status
4. **Use YAML for Bulk Operations**: For large deployments, use YAML files to manage applications
5. **Validate First**: Use the `--dry-run` option to preview changes before applying them
6. **Port Specifications**: Support ranges (e.g., "tcp/8000-8100") and comma-separated lists
7. **Organize by Container**: Keep applications organized in appropriate folders, snippets, or devices

## Additional Examples

### Create a Web Application

```bash
$ scm set object application \
    --folder Shared \
    --name custom-portal \
    --category collaboration \
    --subcategory web-posting \
    --technology browser-based \
    --risk 2 \
    --ports "tcp/443" \
    --uses-encryption \
    --description "Internal web portal"
---> 100%
Created application: custom-portal in folder Shared
```

### Create a High-Risk Application

```bash
$ scm set object application \
    --folder Shared \
    --name risky-app \
    --category networking \
    --subcategory peer-to-peer \
    --technology peer-to-peer \
    --risk 5 \
    --ports "tcp/6881-6889,udp/6881-6889" \
    --able-to-transfer-files \
    --has-known-vulnerabilities \
    --used-by-malware \
    --excessive-bandwidth-use \
    --description "Known P2P application with security risks"
---> 100%
Created application: risky-app in folder Shared
```

### Create Application with Timeouts

```bash
$ scm set object application \
    --folder Shared \
    --name database-app \
    --category business-systems \
    --subcategory database \
    --technology client-server \
    --risk 1 \
    --ports "tcp/1433" \
    --timeout 7200 \
    --tcp-timeout 1800 \
    --description "SQL Server application with extended timeouts"
---> 100%
Created application: database-app in folder Shared
```

## Notes

- Application names must be unique within a container
- Port specifications support ranges (e.g., "tcp/8000-8100")
- Multiple ports can be comma-separated
- Risk levels help in policy decisions
- Security attributes affect how the firewall handles the application
- Tags must exist before being referenced
