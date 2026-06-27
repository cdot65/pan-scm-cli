# Log Forwarding Profile Objects

Log forwarding profile objects define how logs are forwarded to external systems in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load log forwarding profile objects.

## Overview

The `log-forwarding-profile` commands allow you to:

- Configure log forwarding for different log types
- Set filters to control which logs are forwarded
- Forward to HTTP servers, syslog servers, or Panorama
- Delete log forwarding profiles that are no longer needed
- Bulk import log forwarding profiles from YAML files
- Export log forwarding profiles for backup or migration

## Supported Log Types

| Log Type | Description |
| --- | --- |
| traffic | Network traffic logs |
| threat | Threat prevention logs |
| wildfire | WildFire malware analysis logs |
| url | URL filtering logs |
| data | Data filtering logs |
| tunnel | Tunnel inspection logs |
| auth | Authentication logs |
| decryption | SSL/TLS decryption logs |
| dns-security | DNS security logs |

## Set Log Forwarding Profile

Create or update a log forwarding profile object.

### Syntax

```bash
scm set object log-forwarding-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder for the log forwarding profile object | No\* |
| `--snippet TEXT` | Snippet for the log forwarding profile object | No\* |
| `--device TEXT` | Device for the log forwarding profile object | No\* |
| `--name TEXT` | Name of the log forwarding profile | Yes |
| `--match-list JSON` | JSON array of match list configurations | Yes |
| `--description TEXT` | Description of the profile | No |
| `--enhanced-application-logging` | Enable enhanced application logging | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create Basic Traffic Log Forwarding

```bash
$ scm set object log-forwarding-profile \
    --folder Texas \
    --name traffic-logs \
    --match-list '[{"name": "all-traffic", "log_type": "traffic", "filter": "All Logs", "syslog_profiles": ["central-syslog"]}]' \
    --description "Forward all traffic logs"
---> 100%
Created log forwarding profile: traffic-logs in folder Texas
```

#### Create Threat Log Forwarding with HTTP

```bash
$ scm set object log-forwarding-profile \
    --folder Texas \
    --name threat-logs \
    --match-list '[{"name": "threats", "log_type": "threat", "filter": "All Logs", "http_profiles": ["splunk-hec"], "syslog_profiles": ["security-syslog"]}]' \
    --enhanced-application-logging \
    --description "Forward threat logs to SIEM"
---> 100%
Created log forwarding profile: threat-logs in folder Texas
```

#### Create Multi-Destination Forwarding

```bash
$ scm set object log-forwarding-profile \
    --folder Texas \
    --name comprehensive-logging \
    --match-list '[{"name": "traffic", "log_type": "traffic", "filter": "All Logs", "syslog_profiles": ["central-syslog"]}, {"name": "threats", "log_type": "threat", "filter": "All Logs", "http_profiles": ["splunk-hec"]}, {"name": "urls", "log_type": "url", "filter": "All Logs", "http_profiles": ["splunk-hec"]}]' \
    --description "Comprehensive log forwarding"
---> 100%
Created log forwarding profile: comprehensive-logging in folder Texas
```

## Delete Log Forwarding Profile

Delete a log forwarding profile object from SCM.

### Syntax

```bash
scm delete object log-forwarding-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the log forwarding profile object | No\* |
| `--snippet TEXT` | Snippet containing the log forwarding profile object | No\* |
| `--device TEXT` | Device containing the log forwarding profile object | No\* |
| `--name TEXT` | Name of the log forwarding profile object to delete | Yes |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete object log-forwarding-profile --folder Texas --name traffic-logs --force
---> 100%
Deleted log forwarding profile: traffic-logs from folder Texas
```

## Load Log Forwarding Profiles

Load multiple log forwarding profile objects from a YAML file.

### Syntax

```bash
scm load object log-forwarding-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing log forwarding profile definitions | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
log_forwarding_profiles:
  - name: basic-forwarding
    folder: Texas
    description: "Basic log forwarding"
    match_list:
      - name: all-logs
        log_type: traffic
        filter: "All Logs"
        syslog_profiles:
          - central-syslog

  - name: security-monitoring
    folder: Texas
    description: "Security event monitoring"
    enhanced_application_logging: true
    match_list:
      - name: threats
        log_type: threat
        filter: "All Logs"
        http_profiles:
          - splunk-hec
        syslog_profiles:
          - security-syslog
      - name: wildfire
        log_type: wildfire
        filter: "All Logs"
        http_profiles:
          - splunk-hec

  - name: compliance-logging
    folder: Texas
    description: "Compliance and audit logging"
    match_list:
      - name: traffic-audit
        log_type: traffic
        filter: "( zone.src eq Trust ) and ( zone.dst eq Untrust )"
        syslog_profiles:
          - compliance-syslog
      - name: auth-events
        log_type: auth
        filter: "All Logs"
        syslog_profiles:
          - compliance-syslog
```

### Examples

#### Load with Original Locations

```bash
$ scm load object log-forwarding-profile --file log-profiles.yml
---> 100%
✓ Loaded log forwarding profile: basic-forwarding
✓ Loaded log forwarding profile: security-monitoring
✓ Loaded log forwarding profile: compliance-logging

Successfully loaded 3 out of 3 log forwarding profiles from 'log-profiles.yml'
```

#### Load with Folder Override

```bash
$ scm load object log-forwarding-profile --file log-profiles.yml --folder Austin
---> 100%
✓ Loaded log forwarding profile: basic-forwarding
✓ Loaded log forwarding profile: security-monitoring
✓ Loaded log forwarding profile: compliance-logging

Successfully loaded 3 out of 3 log forwarding profiles from 'log-profiles.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all log
forwarding profiles will be loaded into the specified container, ignoring the
container specified in the YAML file.
:::

## Show Log Forwarding Profile

Display log forwarding profile objects.

### Syntax

```bash
scm show object log-forwarding-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the log forwarding profile object | No\* |
| `--snippet TEXT` | Snippet containing the log forwarding profile object | No\* |
| `--device TEXT` | Device containing the log forwarding profile object | No\* |
| `--name TEXT` | Name of the log forwarding profile object to show | No |

:::note
When no `--name` is specified, all items are listed by default.
:::

\* One of --folder, --snippet, or --device is required.

### Examples

#### Show Specific Log Forwarding Profile

```bash
$ scm show object log-forwarding-profile --folder Texas --name threat-logs
---> 100%
Log Forwarding Profile: threat-logs
  Location: Folder 'Texas'
  Match List:
    - Name: threats
      Log Type: threat
      Filter: All Logs
      HTTP Profiles: splunk-hec
      Syslog Profiles: security-syslog
  Enhanced Application Logging: True
  Description: Forward threat logs to SIEM
  ID: 123e4567-e89b-12d3-a456-426614174000
```

#### List All Log Forwarding Profiles (Default Behavior)

```bash
$ scm show object log-forwarding-profile --folder Texas
---> 100%
Log Forwarding Profiles in folder 'Texas':
------------------------------------------------------------
Name: traffic-logs
  Location: Folder 'Texas'
  Match List: all-traffic (traffic)
  Description: Forward all traffic logs
------------------------------------------------------------
Name: threat-logs
  Location: Folder 'Texas'
  Match List: threats (threat)
  Enhanced Application Logging: Yes
  Description: Forward threat logs to SIEM
------------------------------------------------------------
Name: comprehensive-logging
  Location: Folder 'Texas'
  Match List: traffic (traffic), threats (threat), urls (url)
  Description: Comprehensive log forwarding
------------------------------------------------------------
```

## Backup Log Forwarding Profiles

Backup all log forwarding profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup object log-forwarding-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup log forwarding profiles from | No\* |
| `--snippet TEXT` | Snippet to backup log forwarding profiles from | No\* |
| `--device TEXT` | Device to backup log forwarding profiles from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup object log-forwarding-profile --folder Texas
---> 100%
Successfully backed up 10 log forwarding profiles to log-forwarding-profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object log-forwarding-profile --folder Texas --file texas-log-profiles.yaml
---> 100%
Successfully backed up 10 log forwarding profiles to texas-log-profiles.yaml
```

## Best Practices

1. **Log Type Separation**: Create separate match entries for different log types.
2. **Filter Efficiency**: Use specific filters to reduce log volume and improve performance.
3. **Destination Planning**: Use syslog for traditional log management, HTTP for modern SIEM integration.
4. **Enhanced Logging**: Enable enhanced application logging for detailed application information.
5. **Redundancy**: Configure multiple destinations for critical logs.
6. **Use YAML for Bulk Operations**: For complex deployments, use YAML files.
