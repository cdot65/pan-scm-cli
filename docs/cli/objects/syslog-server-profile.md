# Syslog Server Profile Management

This section covers the commands for managing syslog server profile objects in Strata Cloud Manager.

## Overview

Syslog server profiles define external syslog servers for log forwarding. The `syslog-server-profile` commands allow you to:

- Configure multiple syslog servers in a profile
- Set transport protocols (TCP/UDP)
- Define syslog formats (BSD/IETF)
- Configure syslog facilities
- Manage server-specific settings

## Commands

### Creating/Updating Syslog Server Profiles

Basic syslog profile with TCP:

```bash
$ scm set object syslog-server-profile --folder Texas --name central-syslog \
  --servers '[{"name": "primary", "server": "10.0.1.50", "port": 514, "transport": "TCP", "format": "BSD", "facility": "LOG_USER"}]' \
  --description "Central syslog collection"
<span style="color: green;">✓</span> Syslog server profile 'central-syslog' created successfully
```

Profile with multiple servers:

```bash
$ scm set object syslog-server-profile --folder Texas --name redundant-syslog \
  --servers '[{"name": "primary", "server": "syslog1.company.com", "port": 514, "transport": "UDP", "format": "BSD", "facility": "LOG_USER"}, {"name": "secondary", "server": "syslog2.company.com", "port": 514, "transport": "UDP", "format": "BSD", "facility": "LOG_USER"}]' \
  --description "Redundant syslog servers"
<span style="color: green;">✓</span> Syslog server profile 'redundant-syslog' created successfully
```

### Listing Syslog Server Profiles (Default Behavior)

```bash
$ scm show object syslog-server-profile --folder Texas
Syslog server profiles in folder 'Texas':
- central-syslog
- redundant-syslog
- compliance-syslog
- security-syslog
```

!!! note
When no --name is specified, all syslog server profiles are listed by default.

### Showing Syslog Server Profile Details

```bash
$ scm show object syslog-server-profile --folder Texas --name central-syslog
Syslog Server Profile: central-syslog
  Servers:
    - Name: primary
      Server: 10.0.1.50
      Port: 514
      Transport: TCP
      Format: BSD
      Facility: LOG_USER
  Description: Central syslog collection
  Folder: Texas
```

### Deleting Syslog Server Profiles

```bash
$ scm delete object syslog-server-profile --folder Texas --name central-syslog
<span style="color: green;">✓</span> Syslog server profile 'central-syslog' deleted successfully
```

### Load Syslog Server Profiles

Load multiple syslog server profiles from a YAML file.

#### Syntax

```bash
scm load object syslog-server-profile [OPTIONS]
```

#### Options

| Option           | Description                                                    | Required |
| ---------------- | -------------------------------------------------------------- | -------- |
| `--file TEXT`    | Path to YAML file containing syslog server profile definitions | Yes      |
| `--folder TEXT`  | Override folder location for all objects                       | No       |
| `--snippet TEXT` | Override snippet location for all objects                      | No       |
| `--device TEXT`  | Override device location for all objects                       | No       |
| `--dry-run`      | Preview changes without applying them                          | No       |

#### Examples

Load from file with original locations:

```bash
$ scm load object syslog-server-profile --file syslog-profiles.yml
<span style="color: green;">✓</span> Loaded syslog server profile: central-syslog
<span style="color: green;">✓</span> Loaded syslog server profile: redundant-syslog
<span style="color: green;">✓</span> Loaded syslog server profile: compliance-syslog
<span style="color: green;">✓</span> Loaded syslog server profile: security-syslog

Successfully loaded 4 out of 4 syslog server profiles from 'syslog-profiles.yml'
```

Load with folder override:

```bash
$ scm load object syslog-server-profile --file syslog-profiles.yml --folder Austin
<span style="color: green;">✓</span> Loaded syslog server profile: central-syslog
<span style="color: green;">✓</span> Loaded syslog server profile: redundant-syslog
<span style="color: green;">✓</span> Loaded syslog server profile: compliance-syslog
<span style="color: green;">✓</span> Loaded syslog server profile: security-syslog

Successfully loaded 4 out of 4 syslog server profiles from 'syslog-profiles.yml'
```

!!! note
When using container override options (--folder, --snippet, --device), all syslog server profiles will be loaded into the specified container, ignoring the container specified in the YAML file.

### Backup Syslog Server Profiles

Backup all syslog server profile objects from a specified location to a YAML file.

#### Syntax

```bash
scm backup object syslog-server-profile [OPTIONS]
```

#### Options

| Option           | Description                                   | Required |
| ---------------- | --------------------------------------------- | -------- |
| `--folder TEXT`  | Folder to backup syslog server profiles from  | No\*     |
| `--snippet TEXT` | Snippet to backup syslog server profiles from | No\*     |
| `--device TEXT`  | Device to backup syslog server profiles from  | No\*     |
| `--file TEXT`    | Output filename (defaults to auto-generated)  | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

#### Examples

Backup from folder:

```bash
$ scm backup object syslog-server-profile --folder Texas
<span style="color: green;">✓</span> Successfully backed up 10 syslog server profiles to syslog-server-profile_folder_texas_20240115_120530.yaml
```

Backup with custom filename:

```bash
$ scm backup object syslog-server-profile --folder Texas --file texas-syslog-profiles.yaml
<span style="color: green;">✓</span> Successfully backed up 10 syslog server profiles to texas-syslog-profiles.yaml
```

## YAML Configuration Format

Syslog server profiles can be defined in YAML for bulk operations:

```yaml
syslog_server_profiles:
  - name: central-syslog
    folder: Texas # Container location (folder, snippet, or device)
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
    description: "Compliance logging with IETF format"
    servers:
      - name: compliance-server
        server: compliance.company.local
        port: 6514
        transport: TCP
        format: IETF
        facility: LOG_LOCAL7

  - name: security-syslog
    description: "Security event logging"
    servers:
      - name: siem-collector
        server: siem.security.local
        port: 1514
        transport: TCP
        format: BSD
        facility: LOG_AUTH
```

## Configuration Options

### Required Parameters

- `--name`: Name of the syslog server profile
- `--servers`: JSON array of server configurations

### Optional Parameters

- `--description`: Detailed description of the profile
- `--tag`: Tags for categorization (comma-separated)

### Server Configuration Fields

Each server in the servers array must include:

- `name`: Unique name for the server within the profile
- `server`: IP address or hostname of the syslog server
- `port`: Port number (typically 514 for standard syslog)
- `transport`: Transport protocol (TCP or UDP)
- `format`: Syslog message format (BSD or IETF)
- `facility`: Syslog facility (e.g., LOG_USER, LOG_LOCAL0-7)

### Context Parameters

Exactly one context parameter must be specified:

- `--folder`: Folder name (e.g., "Texas", "Shared")
- `--snippet`: Snippet name for Panorama
- `--device`: Device name for NGFW

## Supported Facilities

The following syslog facilities are supported:

- LOG_USER (default)
- LOG_LOCAL0
- LOG_LOCAL1
- LOG_LOCAL2
- LOG_LOCAL3
- LOG_LOCAL4
- LOG_LOCAL5
- LOG_LOCAL6
- LOG_LOCAL7
- LOG_AUTH
- LOG_AUTHPRIV
- LOG_DAEMON
- LOG_KERN
- LOG_MAIL
- LOG_NEWS
- LOG_SYSLOG
- LOG_UUCP

## Examples

### Create a Basic Syslog Profile

```bash
scm set object syslog-server-profile --folder Shared --name simple-syslog \
  --servers '[{"name": "main", "server": "192.168.1.100", "port": 514, "transport": "UDP", "format": "BSD", "facility": "LOG_USER"}]'
```

### Create a High-Availability Syslog Profile

```bash
scm set object syslog-server-profile --folder Shared --name ha-syslog \
  --servers '[
    {"name": "primary", "server": "syslog-primary.local", "port": 514, "transport": "TCP", "format": "BSD", "facility": "LOG_LOCAL0"},
    {"name": "secondary", "server": "syslog-secondary.local", "port": 514, "transport": "TCP", "format": "BSD", "facility": "LOG_LOCAL0"}
  ]' \
  --description "High availability syslog configuration"
```

### Create a Compliance Syslog Profile

```bash
scm set object syslog-server-profile --folder Shared --name compliance \
  --servers '[{"name": "compliance-srv", "server": "10.10.10.50", "port": 6514, "transport": "TCP", "format": "IETF", "facility": "LOG_LOCAL7"}]' \
  --tag "compliance,audit" \
  --description "Compliance logging with IETF format"
```

## Integration with Log Forwarding

Syslog server profiles are referenced in log forwarding profiles:

```bash
# Create log forwarding profile using syslog servers
scm set object log-forwarding-profile --folder Shared --name forward-to-syslog \
  --match-list '[{
    "name": "traffic-logs",
    "log_type": "traffic",
    "filter": "All Logs",
    "syslog_profiles": ["central-syslog", "security-syslog"]
  }]'
```

## Best Practices

1. **Redundancy**: Configure multiple servers for high availability

2. **Transport Selection**:

   - Use TCP for reliable delivery
   - Use UDP for better performance with acceptable message loss

3. **Port Configuration**: Use non-standard ports for security isolation

4. **Format Selection**:

   - BSD format for traditional syslog systems
   - IETF format for newer RFC5424-compliant systems

5. **Facility Usage**: Use LOG_LOCAL facilities to separate log streams

## Troubleshooting

### Common Issues

1. **Connection Failures**: Verify network connectivity and firewall rules
2. **Format Mismatches**: Ensure syslog server expects the configured format
3. **Port Conflicts**: Check for port availability on syslog servers
4. **DNS Resolution**: Use IP addresses if DNS is unreliable

### Testing Configuration

```bash
# Test in mock mode first
scm set object syslog-server-profile --folder Shared --name test-syslog \
  --servers '[{"name": "test", "server": "10.0.0.1", "port": 514, "transport": "UDP", "format": "BSD", "facility": "LOG_USER"}]' \
  --mock
```

## Notes

- Profile names must be unique within a folder
- SSL/TLS transport is not currently supported by the SDK
- Server names must be unique within a profile
- Maximum number of servers per profile may be limited
- Tags must exist before being referenced
- Profiles are referenced by log forwarding profiles
- Changes to profiles affect all referencing log forwarding configurations
