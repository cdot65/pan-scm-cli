# Log Forwarding Profile Objects

Log forwarding profile objects define how logs are forwarded to external systems in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load log forwarding profile objects.

## Overview

Log forwarding profiles allow you to:

- Configure log forwarding for different log types
- Set filters to control which logs are forwarded
- Forward to HTTP servers, syslog servers, or Panorama
- Enable enhanced application logging
- Configure quarantine actions for matched logs

## Set Log Forwarding Profile

Create or update a log forwarding profile object.

### Syntax

```bash
scm set objects log-forwarding-profile [OPTIONS]
```

### Options

| Option                           | Description                                   | Required |
| -------------------------------- | --------------------------------------------- | -------- |
| `--folder TEXT`                  | Folder for the log forwarding profile object  | Yes\*    |
| `--snippet TEXT`                 | Snippet for the log forwarding profile object | Yes\*    |
| `--device TEXT`                  | Device for the log forwarding profile object  | Yes\*    |
| `--name TEXT`                    | Name of the log forwarding profile            | Yes      |
| `--match-list JSON`              | JSON array of match list configurations       | Yes      |
| `--description TEXT`             | Description of the profile                    | No       |
| `--enhanced-application-logging` | Enable enhanced application logging           | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

### Examples

#### Create Basic Traffic Log Forwarding

```bash
$ scm set objects log-forwarding-profile \
    --folder Texas \
    --name traffic-logs \
    --match-list '[{"name": "all-traffic", "log_type": "traffic", "filter": "All Logs", "syslog_profiles": ["central-syslog"]}]' \
    --description "Forward all traffic logs"
---> 100%
Created log forwarding profile: traffic-logs in folder Texas
```

#### Create Threat Log Forwarding with HTTP

```bash
$ scm set objects log-forwarding-profile \
    --folder Texas \
    --name threat-logs \
    --match-list '[{"name": "threats", "log_type": "threat", "filter": "All Logs", "http_profiles": ["splunk-hec"], "syslog_profiles": ["security-syslog"]}]' \
    --enhanced-application-logging \
    --description "Forward threat logs to SIEM"
---> 100%
Created log forwarding profile: threat-logs in folder Texas
```

## Delete Log Forwarding Profile

Delete a log forwarding profile object from SCM.

### Syntax

```bash
scm delete objects log-forwarding-profile [OPTIONS]
```

### Options

| Option           | Description                                          | Required |
| ---------------- | ---------------------------------------------------- | -------- |
| `--folder TEXT`  | Folder containing the log forwarding profile object  | Yes\*    |
| `--snippet TEXT` | Snippet containing the log forwarding profile object | Yes\*    |
| `--device TEXT`  | Device containing the log forwarding profile object  | Yes\*    |
| `--name TEXT`    | Name of the log forwarding profile object to delete  | Yes      |

\* You must specify exactly one of --folder, --snippet, or --device.

### Example

```bash
$ scm delete objects log-forwarding-profile --folder Texas --name traffic-logs
---> 100%
Deleted log forwarding profile: traffic-logs from folder Texas
```

## Load Log Forwarding Profiles

Load multiple log forwarding profile objects from a YAML file.

### Syntax

```bash
scm load objects log-forwarding-profile [OPTIONS]
```

### Options

| Option           | Description                                                     | Required |
| ---------------- | --------------------------------------------------------------- | -------- |
| `--file TEXT`    | Path to YAML file containing log forwarding profile definitions | Yes      |
| `--folder TEXT`  | Override folder location for all objects                        | No       |
| `--snippet TEXT` | Override snippet location for all objects                       | No       |
| `--device TEXT`  | Override device location for all objects                        | No       |
| `--dry-run`      | Preview changes without applying them                           | No       |

### YAML File Format

```yaml
---
log_forwarding_profiles:
  - name: basic-forwarding
    folder: Texas # Container location (folder, snippet, or device)
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
$ scm load objects log-forwarding-profile --file log-profiles.yml
---> 100%
✓ Loaded log forwarding profile: basic-forwarding
✓ Loaded log forwarding profile: security-monitoring
✓ Loaded log forwarding profile: compliance-logging

Successfully loaded 3 out of 3 log forwarding profiles from 'log-profiles.yml'
```

#### Load with Folder Override

```bash
$ scm load objects log-forwarding-profile --file log-profiles.yml --folder Austin
---> 100%
✓ Loaded log forwarding profile: basic-forwarding
✓ Loaded log forwarding profile: security-monitoring
✓ Loaded log forwarding profile: compliance-logging

Successfully loaded 3 out of 3 log forwarding profiles from 'log-profiles.yml'
```

!!! note
When using container override options (--folder, --snippet, --device), all log forwarding profiles will be loaded into the specified container, ignoring the container specified in the YAML file.

## Show Log Forwarding Profile

Display log forwarding profile objects.

### Syntax

```bash
scm show objects log-forwarding-profile [OPTIONS]
```

### Options

| Option           | Description                                          | Required |
| ---------------- | ---------------------------------------------------- | -------- |
| `--folder TEXT`  | Folder containing the log forwarding profile object  | Yes\*    |
| `--snippet TEXT` | Snippet containing the log forwarding profile object | Yes\*    |
| `--device TEXT`  | Device containing the log forwarding profile object  | Yes\*    |
| `--name TEXT`    | Name of the log forwarding profile object to show    | No\*\*   |
| `--list`         | List all log forwarding profiles in the container    | No\*\*   |

\* You must specify exactly one of --folder, --snippet, or --device.
\*\* If --name is not specified, all items will be listed.

### Examples

#### Show Specific Log Forwarding Profile

```bash
$ scm show objects log-forwarding-profile --folder Texas --name threat-logs
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
$ scm show objects log-forwarding-profile --folder Texas
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
scm backup objects log-forwarding-profile [OPTIONS]
```

### Options

| Option           | Description                                    | Required |
| ---------------- | ---------------------------------------------- | -------- |
| `--folder TEXT`  | Folder to backup log forwarding profiles from  | No\*     |
| `--snippet TEXT` | Snippet to backup log forwarding profiles from | No\*     |
| `--device TEXT`  | Device to backup log forwarding profiles from  | No\*     |
| `--file TEXT`    | Output filename (defaults to auto-generated)   | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

### Examples

#### Backup from Folder

```bash
$ scm backup objects log-forwarding-profile --folder Texas
---> 100%
Successfully backed up 10 log forwarding profiles to log-forwarding-profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup objects log-forwarding-profile --folder Texas --file texas-log-profiles.yaml
---> 100%
Successfully backed up 10 log forwarding profiles to texas-log-profiles.yaml
```

## Configuration Options

### Required Parameters

- `--name`: Name of the log forwarding profile

### Optional Parameters

- `--description`: Detailed description (max 255 characters)
- `--enhanced-application-logging`: Enable enhanced application logging
- `--match-list`: JSON array of match list configurations

### Match List Configuration

Each match list entry requires:

- `name`: Unique name for the match entry
- `log_type`: Type of log to match (see supported types below)
- `filter`: Filter expression or "All Logs"

Optional match list fields:

- `http_profiles`: List of HTTP server profiles to forward to
- `syslog_profiles`: List of syslog server profiles to forward to
- `send_to_panorama`: Forward to Panorama (true/false)
- `quarantine`: Quarantine matched logs (true/false)

### Context Parameters

Exactly one context parameter must be specified:

- `--folder`: Folder name (e.g., "Texas", "Shared")
- `--snippet`: Snippet name for Panorama
- `--device`: Device name for NGFW

## Supported Log Types

| Log Type     | Description                    |
| ------------ | ------------------------------ |
| traffic      | Network traffic logs           |
| threat       | Threat prevention logs         |
| wildfire     | WildFire malware analysis logs |
| url          | URL filtering logs             |
| data         | Data filtering logs            |
| tunnel       | Tunnel inspection logs         |
| auth         | Authentication logs            |
| decryption   | SSL/TLS decryption logs        |
| dns-security | DNS security logs              |

## Filter Expressions

### Basic Syntax

- `"All Logs"`: Forward all logs of the specified type
- Custom filters use attribute comparisons

### Common Filter Attributes

**Traffic Logs:**

- `zone.src`: Source zone
- `zone.dst`: Destination zone
- `addr.src`: Source address
- `addr.dst`: Destination address
- `app`: Application
- `bytes`: Session bytes

**Threat Logs:**

- `subtype`: Threat subtype (virus, spyware, vulnerability)
- `severity`: Threat severity
- `action`: Action taken

### Filter Operators

- `eq`: Equals
- `neq`: Not equals
- `geq`: Greater than or equal
- `leq`: Less than or equal
- `and`: Logical AND
- `or`: Logical OR

### Filter Examples

```bash
# Source zone filter
"( zone.src eq Trust )"

# Multiple conditions
"( zone.src eq Trust ) and ( zone.dst eq Untrust )"

# Byte threshold
"( bytes geq 1000000 )"

# Threat severity
"( severity geq high )"

# Complex filter
"( zone.src eq Trust ) and ( app eq ssl ) and ( bytes geq 1000000 )"
```

## Examples

### Basic Log Forwarding

```bash
# Forward all traffic logs
scm set objects log-forwarding-profile --folder Shared --name all-traffic \
  --match-list '[{"name": "traffic", "log_type": "traffic", "filter": "All Logs", "syslog_profiles": ["central-syslog"]}]'
```

### Security Monitoring

```bash
# Forward threats and malware
scm set objects log-forwarding-profile --folder Shared --name security \
  --match-list '[
    {"name": "threats", "log_type": "threat", "filter": "All Logs", "http_profiles": ["siem"]},
    {"name": "malware", "log_type": "wildfire", "filter": "All Logs", "http_profiles": ["siem"]}
  ]' \
  --enhanced-application-logging
```

### Filtered Forwarding

```bash
# Forward specific traffic
scm set objects log-forwarding-profile --folder Shared --name filtered \
  --match-list '[{
    "name": "internet-traffic",
    "log_type": "traffic",
    "filter": "( zone.dst eq Internet ) and ( bytes geq 10000 )",
    "syslog_profiles": ["traffic-analysis"]
  }]'
```

### Multi-Destination Forwarding

```bash
# Forward to multiple destinations
scm set objects log-forwarding-profile --folder Shared --name multi-dest \
  --match-list '[{
    "name": "all-threats",
    "log_type": "threat",
    "filter": "All Logs",
    "http_profiles": ["splunk", "elastic"],
    "syslog_profiles": ["syslog1", "syslog2"],
    "send_to_panorama": true
  }]'
```

## Best Practices

1. **Log Type Separation**: Create separate match entries for different log types

2. **Filter Efficiency**: Use specific filters to reduce log volume

3. **Destination Planning**:

   - Use syslog for traditional log management
   - Use HTTP for modern SIEM integration
   - Send to Panorama for centralized management

4. **Enhanced Logging**: Enable for detailed application information

5. **Redundancy**: Configure multiple destinations for critical logs

## Integration with Security Policies

Log forwarding profiles are applied to security rules:

```bash
# Apply log forwarding to security rule
scm set security rule --folder Shared --name "Internet-Access" \
  --log-forwarding-profile "comprehensive-logging" \
  --log-start --log-end
```

## Performance Considerations

1. **Filter Complexity**: Complex filters impact performance
2. **Destination Count**: More destinations increase resource usage
3. **Log Volume**: High-volume log types (traffic) need careful planning
4. **Enhanced Logging**: Increases log size and processing

## Troubleshooting

### Common Issues

1. **Missing Profiles**: Ensure HTTP/syslog profiles exist before referencing
2. **Filter Syntax**: Validate filter expressions
3. **Destination Connectivity**: Verify log destinations are reachable
4. **Log Volume**: Monitor for excessive log generation

### Testing Filters

```bash
# Start with "All Logs"
"All Logs"

# Add simple filter
"( zone.src eq Trust )"

# Build complex filter incrementally
"( zone.src eq Trust ) and ( zone.dst eq Internet )"
```

## Notes

- Profile names must be unique within a folder
- At least one match entry is recommended
- Each match entry needs at least one forwarding action
- Filter field is required (use "All Logs" for no filtering)
- Referenced HTTP/syslog profiles must exist
- Profiles are applied to security rules
- Enhanced logging increases log detail but also size
- Some log types may not be available on all platforms
