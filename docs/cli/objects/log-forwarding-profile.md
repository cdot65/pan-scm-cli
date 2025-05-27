# Log Forwarding Profile Management

This section covers the commands for managing log forwarding profiles in Strata Cloud Manager.

## Overview

Log forwarding profiles define how logs are forwarded to external systems. The `log-forwarding-profile` commands allow you to:

- Configure log forwarding for different log types
- Set filters to control which logs are forwarded
- Forward to HTTP servers, syslog servers, or Panorama
- Enable enhanced application logging
- Configure quarantine actions for matched logs

## Commands

### Creating/Updating Log Forwarding Profiles

Basic traffic log forwarding:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects log-forwarding-profile --folder Texas --name traffic-logs \
  --match-list '[{"name": "all-traffic", "log_type": "traffic", "filter": "All Logs", "syslog_profiles": ["central-syslog"]}]' \
  --description "Forward all traffic logs"
<span style="color: green;">✓</span> Log forwarding profile 'traffic-logs' created successfully
```

</div>

Threat log forwarding with HTTP:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects log-forwarding-profile --folder Texas --name threat-logs \
  --match-list '[{"name": "threats", "log_type": "threat", "filter": "All Logs", "http_profiles": ["splunk-hec"], "syslog_profiles": ["security-syslog"]}]' \
  --enhanced-application-logging \
  --description "Forward threat logs to SIEM"
<span style="color: green;">✓</span> Log forwarding profile 'threat-logs' created successfully
```

</div>

Multiple log types:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects log-forwarding-profile --folder Texas --name comprehensive-logging \
  --match-list '[
    {"name": "traffic", "log_type": "traffic", "filter": "All Logs", "syslog_profiles": ["central-syslog"]},
    {"name": "threats", "log_type": "threat", "filter": "All Logs", "http_profiles": ["splunk-hec"]},
    {"name": "urls", "log_type": "url", "filter": "All Logs", "syslog_profiles": ["web-proxy-logs"]}
  ]' \
  --description "Comprehensive log forwarding"
<span style="color: green;">✓</span> Log forwarding profile 'comprehensive-logging' created successfully
```

</div>

### Listing Log Forwarding Profiles

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects log-forwarding-profile --folder Texas --list
Log forwarding profiles in folder 'Texas':
- traffic-logs
- threat-logs
- comprehensive-logging
- security-monitoring
```

</div>

### Showing Log Forwarding Profile Details

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects log-forwarding-profile --folder Texas --name threat-logs
Log Forwarding Profile: threat-logs
  Match List:
    - Name: threats
      Log Type: threat
      Filter: All Logs
      HTTP Profiles: splunk-hec
      Syslog Profiles: security-syslog
  Enhanced Application Logging: True
  Description: Forward threat logs to SIEM
  Folder: Texas
```

</div>

### Deleting Log Forwarding Profiles

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli delete objects log-forwarding-profile --folder Texas --name traffic-logs
<span style="color: green;">✓</span> Log forwarding profile 'traffic-logs' deleted successfully
```

</div>

### Bulk Operations

Load multiple log forwarding profiles from a YAML file:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli load objects log-forwarding-profile --folder Texas --file log-profiles.yml
<span style="color: green;">✓</span> Loaded 10 log forwarding profiles successfully
```

</div>

Backup existing log forwarding profiles:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli backup objects log-forwarding-profile --folder Texas
<span style="color: green;">✓</span> Backed up 10 log forwarding profiles to log-forwarding-profile-texas.yaml
```

</div>

## YAML Configuration Format

Log forwarding profiles can be defined in YAML for bulk operations:

```yaml
log_forwarding_profiles:
  - name: basic-forwarding
    description: "Basic log forwarding"
    match_list:
      - name: all-logs
        log_type: traffic
        filter: "All Logs"
        syslog_profiles:
          - central-syslog
    
  - name: security-monitoring
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
      - name: data-filtering
        log_type: data
        filter: "All Logs"
        syslog_profiles:
          - dlp-syslog
    
  - name: performance-monitoring
    description: "Performance and traffic analysis"
    match_list:
      - name: traffic-analysis
        log_type: traffic
        filter: "( bytes geq 1000000 )"
        http_profiles:
          - elastic-logs
      - name: tunnel-monitoring
        log_type: tunnel
        filter: "All Logs"
        syslog_profiles:
          - network-syslog
    
  - name: threat-intelligence
    description: "Threat intelligence integration"
    enhanced_application_logging: true
    match_list:
      - name: malware
        log_type: threat
        filter: "( subtype eq virus ) or ( subtype eq spyware )"
        http_profiles:
          - threat-intel-api
        quarantine: true
      - name: dns-threats
        log_type: dns-security
        filter: "All Logs"
        http_profiles:
          - threat-intel-api
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

| Log Type | Description |
|----------|-------------|
| traffic | Network traffic logs |
| threat | Threat prevention logs |
| wildfire | WildFire malware analysis logs |
| url | URL filtering logs |
| data | Data filtering logs |
| tunnel | Tunnel inspection logs |
| auth | Authentication logs |
| decryption | SSL/TLS decryption logs |
| dns-security | DNS security logs |

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
scm-cli set objects log-forwarding-profile --folder Shared --name all-traffic \
  --match-list '[{"name": "traffic", "log_type": "traffic", "filter": "All Logs", "syslog_profiles": ["central-syslog"]}]'
```

### Security Monitoring

```bash
# Forward threats and malware
scm-cli set objects log-forwarding-profile --folder Shared --name security \
  --match-list '[
    {"name": "threats", "log_type": "threat", "filter": "All Logs", "http_profiles": ["siem"]},
    {"name": "malware", "log_type": "wildfire", "filter": "All Logs", "http_profiles": ["siem"]}
  ]' \
  --enhanced-application-logging
```

### Filtered Forwarding

```bash
# Forward specific traffic
scm-cli set objects log-forwarding-profile --folder Shared --name filtered \
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
scm-cli set objects log-forwarding-profile --folder Shared --name multi-dest \
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
scm-cli set security rule --folder Shared --name "Internet-Access" \
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