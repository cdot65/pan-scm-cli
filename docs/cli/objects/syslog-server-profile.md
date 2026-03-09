# Syslog Server Profile Objects

Syslog server profile objects define external syslog servers for log forwarding in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load syslog server profile objects.

## Overview

The `syslog-server-profile` commands allow you to:

- Configure multiple syslog servers in a profile
- Set transport protocols (TCP/UDP) and message formats (BSD/IETF)
- Configure syslog facilities for log categorization
- Delete syslog server profiles that are no longer needed
- Bulk import syslog server profiles from YAML files
- Export syslog server profiles for backup or migration

## Supported Facilities

| Facility | Facility | Facility |
| --- | --- | --- |
| LOG_USER (default) | LOG_LOCAL0 | LOG_LOCAL1 |
| LOG_LOCAL2 | LOG_LOCAL3 | LOG_LOCAL4 |
| LOG_LOCAL5 | LOG_LOCAL6 | LOG_LOCAL7 |
| LOG_AUTH | LOG_AUTHPRIV | LOG_DAEMON |
| LOG_KERN | LOG_MAIL | LOG_NEWS |
| LOG_SYSLOG | LOG_UUCP | |

## Set Syslog Server Profile

Create or update a syslog server profile object.

### Syntax

```bash
scm set object syslog-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder for the syslog server profile object | No\* |
| `--snippet TEXT` | Snippet for the syslog server profile object | No\* |
| `--device TEXT` | Device for the syslog server profile object | No\* |
| `--name TEXT` | Name of the syslog server profile | Yes |
| `--servers JSON` | JSON array of server configurations | Yes |
| `--description TEXT` | Description of the profile | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create Basic Syslog Profile with TCP

```bash
$ scm set object syslog-server-profile \
    --folder Texas \
    --name central-syslog \
    --servers '[{"name": "primary", "server": "10.0.1.50", "port": 514, "transport": "TCP", "format": "BSD", "facility": "LOG_USER"}]' \
    --description "Central syslog collection"
---> 100%
Created syslog server profile: central-syslog in folder Texas
```

#### Create Profile with Multiple Servers

```bash
$ scm set object syslog-server-profile \
    --folder Texas \
    --name redundant-syslog \
    --servers '[{"name": "primary", "server": "syslog1.company.com", "port": 514, "transport": "UDP", "format": "BSD", "facility": "LOG_USER"}, {"name": "secondary", "server": "syslog2.company.com", "port": 514, "transport": "UDP", "format": "BSD", "facility": "LOG_USER"}]' \
    --description "Redundant syslog servers"
---> 100%
Created syslog server profile: redundant-syslog in folder Texas
```

#### Create Compliance Syslog Profile with IETF Format

```bash
$ scm set object syslog-server-profile \
    --folder Shared \
    --name compliance \
    --servers '[{"name": "compliance-srv", "server": "10.10.10.50", "port": 6514, "transport": "TCP", "format": "IETF", "facility": "LOG_LOCAL7"}]' \
    --description "Compliance logging with IETF format"
---> 100%
Created syslog server profile: compliance in folder Shared
```

## Delete Syslog Server Profile

Delete a syslog server profile object from SCM.

### Syntax

```bash
scm delete object syslog-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the syslog server profile object | No\* |
| `--snippet TEXT` | Snippet containing the syslog server profile object | No\* |
| `--device TEXT` | Device containing the syslog server profile object | No\* |
| `--name TEXT` | Name of the syslog server profile to delete | Yes |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete object syslog-server-profile --folder Texas --name central-syslog --force
---> 100%
Deleted syslog server profile: central-syslog from folder Texas
```

## Load Syslog Server Profiles

Load multiple syslog server profile objects from a YAML file.

### Syntax

```bash
scm load object syslog-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing syslog server profile definitions | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
syslog_server_profiles:
  - name: central-syslog
    folder: Texas
    description: "Central syslog collection"
    servers:
      - name: primary
        server: 10.0.1.50
        port: 514
        transport: TCP
        format: BSD
        facility: LOG_USER

  - name: redundant-syslog
    folder: Texas
    description: "Redundant syslog servers for high availability"
    servers:
      - name: primary
        server: syslog1.company.com
        port: 514
        transport: UDP
        format: BSD
        facility: LOG_USER
      - name: secondary
        server: syslog2.company.com
        port: 514
        transport: UDP
        format: BSD
        facility: LOG_USER

  - name: compliance-syslog
    folder: Texas
    description: "Compliance logging with IETF format"
    servers:
      - name: compliance-server
        server: compliance.company.local
        port: 6514
        transport: TCP
        format: IETF
        facility: LOG_LOCAL7

  - name: security-syslog
    folder: Texas
    description: "Security event logging"
    servers:
      - name: siem-collector
        server: siem.security.local
        port: 1514
        transport: TCP
        format: BSD
        facility: LOG_AUTH
```

### Examples

#### Load with Original Locations

```bash
$ scm load object syslog-server-profile --file syslog-profiles.yml
---> 100%
✓ Loaded syslog server profile: central-syslog
✓ Loaded syslog server profile: redundant-syslog
✓ Loaded syslog server profile: compliance-syslog
✓ Loaded syslog server profile: security-syslog

Successfully loaded 4 out of 4 syslog server profiles from 'syslog-profiles.yml'
```

#### Load with Folder Override

```bash
$ scm load object syslog-server-profile --file syslog-profiles.yml --folder Austin
---> 100%
✓ Loaded syslog server profile: central-syslog
✓ Loaded syslog server profile: redundant-syslog
✓ Loaded syslog server profile: compliance-syslog
✓ Loaded syslog server profile: security-syslog

Successfully loaded 4 out of 4 syslog server profiles from 'syslog-profiles.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all syslog
    server profiles will be loaded into the specified container, ignoring the container
    specified in the YAML file.

## Show Syslog Server Profile

Display syslog server profile objects.

### Syntax

```bash
scm show object syslog-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the syslog server profile object | No\* |
| `--snippet TEXT` | Snippet containing the syslog server profile object | No\* |
| `--device TEXT` | Device containing the syslog server profile object | No\* |
| `--name TEXT` | Name of the syslog server profile to show | No |

!!! note
    When no `--name` is specified, all items are listed by default.

\* One of --folder, --snippet, or --device is required.

### Examples

#### Show Specific Syslog Server Profile

```bash
$ scm show object syslog-server-profile --folder Texas --name central-syslog
---> 100%
Syslog Server Profile: central-syslog
  Location: Folder 'Texas'
  Servers:
    - Name: primary
      Server: 10.0.1.50
      Port: 514
      Transport: TCP
      Format: BSD
      Facility: LOG_USER
  Description: Central syslog collection
```

#### List All Syslog Server Profiles (Default Behavior)

```bash
$ scm show object syslog-server-profile --folder Texas
---> 100%
Syslog Server Profiles in folder 'Texas':
------------------------------------------------------------
Name: central-syslog
  Server: primary (10.0.1.50:514 TCP)
  Description: Central syslog collection
------------------------------------------------------------
Name: redundant-syslog
  Servers: primary (syslog1.company.com:514 UDP), secondary (syslog2.company.com:514 UDP)
  Description: Redundant syslog servers for high availability
------------------------------------------------------------
Name: compliance-syslog
  Server: compliance-server (compliance.company.local:6514 TCP IETF)
  Description: Compliance logging with IETF format
------------------------------------------------------------
```

## Backup Syslog Server Profiles

Backup all syslog server profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup object syslog-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup syslog server profiles from | No\* |
| `--snippet TEXT` | Snippet to backup syslog server profiles from | No\* |
| `--device TEXT` | Device to backup syslog server profiles from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup object syslog-server-profile --folder Texas
---> 100%
Successfully backed up 10 syslog server profiles to syslog-server-profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object syslog-server-profile --folder Texas --file texas-syslog-profiles.yaml
---> 100%
Successfully backed up 10 syslog server profiles to texas-syslog-profiles.yaml
```

## Best Practices

1. **Redundancy**: Configure multiple servers for high availability.
2. **Transport Selection**: Use TCP for reliable delivery, UDP for better performance with acceptable message loss.
3. **Format Selection**: Use BSD format for traditional syslog, IETF format for newer RFC5424-compliant systems.
4. **Facility Usage**: Use LOG_LOCAL facilities to separate log streams on the syslog server.
5. **Port Configuration**: Use non-standard ports for security isolation when appropriate.
6. **Use YAML for Bulk Operations**: For complex deployments, use YAML files.
