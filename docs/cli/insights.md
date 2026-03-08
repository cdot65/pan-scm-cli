# Insights Commands

The `scm insights` commands provide access to monitoring and telemetry data from Strata Cloud Manager, including alerts, mobile users, locations, remote networks, service connections, and tunnels.

## Overview

The insights commands allow you to:
- View security and system alerts
- Monitor mobile user connections and activity
- Track location-based metrics
- Analyze remote network performance
- Check service connection health
- Monitor tunnel status and statistics

## Prerequisites

1. Install pan-scm-cli (see [Installation](../about/installation.md))
2. Configure authentication (see [Configuration](../guide/configuration.md))
3. Ensure your user has appropriate permissions for monitoring data

## Commands

### Alerts

View and export security and system alerts from your Prisma Access environment.

#### List all alerts
```bash
scm insights alerts --list
```

#### Filter alerts by severity
```bash
scm insights alerts --list --severity critical
scm insights alerts --list --severity high,medium
```

#### Filter alerts by time range
```bash
# Last 7 days
scm insights alerts --list --start 7

# Specific date range
scm insights alerts --list --start 2024-01-01T00:00:00 --end 2024-01-31T23:59:59
```

#### Get a specific alert
```bash
scm insights alerts --id alert-001
```

#### Export alerts
```bash
# Export to JSON
scm insights alerts --list --export json --output alerts.json

# Export to CSV
scm insights alerts --list --export csv --output alerts.csv
```

### Mobile Users

Monitor mobile user connections and activity.

#### List all mobile users
```bash
scm insights mobile-users --list
```

#### Filter by connection status
```bash
scm insights mobile-users --list --status connected
scm insights mobile-users --list --status disconnected
```

#### Filter by location
```bash
scm insights mobile-users --list --location "New York"
```

#### Get a specific user
```bash
scm insights mobile-users --id user-001
```

### Locations

View location-based metrics and capacity information.

#### List all locations
```bash
scm insights locations --list
```

#### Filter by region
```bash
scm insights locations --list --region us-east
```

#### Get location details
```bash
scm insights locations --id loc-001
```

### Remote Networks

Monitor remote network connectivity and performance.

#### List all remote networks
```bash
scm insights remote-networks --list
```

#### Filter by connectivity status
```bash
scm insights remote-networks --list --connectivity degraded
```

#### Include performance metrics
```bash
scm insights remote-networks --list --metrics
```

#### Get specific network details
```bash
scm insights remote-networks --id rn-001 --metrics
```

### Service Connections

Monitor cloud service connections and their health status.

#### List all service connections
```bash
scm insights service-connections --list
```

#### Filter by health status
```bash
scm insights service-connections --list --health unhealthy
```

#### Include performance metrics
```bash
scm insights service-connections --list --metrics
```

### Tunnels

Monitor IPSec and SSL tunnel status and performance.

#### List all tunnels
```bash
scm insights tunnels --list
```

#### Filter by status
```bash
scm insights tunnels --list --status down
```

#### Include statistics
```bash
scm insights tunnels --list --stats
```

#### Get historical data
```bash
scm insights tunnels --list --start 2024-01-01T00:00:00 --end 2024-01-31T23:59:59
```

## Common Options

All insights commands support these common options:

- `--folder`: Filter by folder
- `--max-results`: Limit the number of results (default: 100)
- `--export`: Export format (json or csv)
- `--output`: Output file path for exports
- `--mock`: Run in mock mode for testing

## Export Formats

### JSON Export
Exports data in JSON format with full field details:
```json
[
  {
    "id": "alert-001",
    "name": "Critical CPU Usage",
    "severity": "critical",
    "status": "active",
    "timestamp": "2024-01-20T10:30:00Z",
    "description": "CPU usage exceeded 95% threshold",
    "impacted_resources": ["fw-01", "fw-02"]
  }
]
```

### CSV Export
Exports data in CSV format with flattened fields:
```csv
id,name,severity,status,timestamp,description
alert-001,Critical CPU Usage,critical,active,2024-01-20T10:30:00Z,CPU usage exceeded 95% threshold
```

## Mock Mode

All insights commands support mock mode for testing and development:

```bash
# Force mock mode by clearing credentials
SCM_CLIENT_ID="" SCM_CLIENT_SECRET="" SCM_TSG_ID="" scm insights alerts --list
```

This returns realistic sample data without making actual API calls.

## Notes

- The insights APIs require appropriate permissions in your Strata Cloud Manager tenant
- Some metrics and statistics may have a delay of several minutes
- Export operations respect the --max-results limit
- Time filters accept both relative days (e.g., 7 for last 7 days) and ISO timestamps
- The insights functionality requires the pan-scm-sdk to have the insights services implemented