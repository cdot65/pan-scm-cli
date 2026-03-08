# Insights Commands

The `scm insights` commands provide access to monitoring and telemetry data from Strata Cloud Manager, including alerts, mobile users, locations, remote networks, service connections, and tunnels.

## Overview

The insights commands allow you to:

- View security and system alerts with severity filtering
- Monitor mobile user connections and activity
- Track location-based metrics and capacity
- Analyze remote network connectivity and performance
- Check service connection health status
- Monitor tunnel status and statistics

## Prerequisites

1. Install pan-scm-cli (see [Installation](../about/installation.md))
2. Configure authentication (see [Configuration](../guide/configuration.md))
3. Ensure your user has appropriate permissions for monitoring data

## Commands

### Alerts

View and export security and system alerts from your Prisma Access environment.

| Option | Description | Required |
| --- | --- | --- |
| `--list` | List all alerts | No\* |
| `--id TEXT` | Get a specific alert by ID | No\* |
| `--real-time` | Monitor alerts in real-time (continuous polling) | No\* |
| `--severity TEXT` | Filter alerts by severity (Critical, High, Medium, Low) | No |
| `--start DATETIME` | Filter alerts starting from this time (ISO format) | No |
| `--end DATETIME` | Filter alerts up to this time (ISO format) | No |
| `--folder TEXT` | Filter alerts by folder | No |
| `--max-results INT` | Maximum number of results to return (default: 10) | No |
| `--export TEXT` | Export format (json, csv) | No |
| `--output TEXT` | Output file path for export | No |
| `--mock` | Run in mock mode | No |

\* One of --list, --id, or --real-time is required.

#### List All Alerts

```bash
$ scm insights alerts --list
---> 100%
- id: alert-001
  name: Critical CPU Usage
  severity: critical
  status: active
  timestamp: '2026-03-08T10:30:00Z'
```

#### Filter Alerts by Severity

```bash
$ scm insights alerts --list --severity critical
---> 100%
- id: alert-001
  name: Critical CPU Usage
  severity: critical
  status: active
```

#### Filter Alerts by Time Range

```bash
$ scm insights alerts --list \
    --start "2026-03-01T00:00:00" \
    --end "2026-03-08T23:59:59"
---> 100%
- id: alert-001
  name: Critical CPU Usage
  severity: critical
```

#### Get a Specific Alert

```bash
$ scm insights alerts --id alert-001
---> 100%
id: alert-001
name: Critical CPU Usage
severity: critical
status: active
timestamp: '2026-03-08T10:30:00Z'
description: CPU usage exceeded 95% threshold
impacted_resources:
  - fw-01
  - fw-02
```

#### Export Alerts to JSON

```bash
$ scm insights alerts --list \
    --export json \
    --output alerts.json
---> 100%
Data exported to alerts.json
```

#### Export Alerts to CSV

```bash
$ scm insights alerts --list \
    --export csv \
    --output alerts.csv
---> 100%
Data exported to alerts.csv
```

### Mobile Users

Monitor mobile user connections and activity.

| Option | Description | Required |
| --- | --- | --- |
| `--list` | List all mobile users | No\* |
| `--id TEXT` | Get a specific mobile user by ID | No\* |
| `--status TEXT` | Filter by status (connected, disconnected) | No |
| `--location TEXT` | Filter by location | No |
| `--folder TEXT` | Filter by folder | No |
| `--max-results INT` | Maximum number of results to return (default: 100) | No |
| `--export TEXT` | Export format (json, csv) | No |
| `--output TEXT` | Output file path for export | No |
| `--mock` | Run in mock mode | No |

\* One of --list or --id is required.

#### List All Mobile Users

```bash
$ scm insights mobile-users --list
---> 100%
- id: user-001
  username: jsmith@example.com
  status: connected
  location: New York
```

#### Filter by Connection Status

```bash
$ scm insights mobile-users --list --status connected
---> 100%
- id: user-001
  username: jsmith@example.com
  status: connected
  location: New York
```

#### Filter by Location

```bash
$ scm insights mobile-users --list --location "New York"
---> 100%
- id: user-001
  username: jsmith@example.com
  status: connected
  location: New York
```

#### Get a Specific User

```bash
$ scm insights mobile-users --id user-001
---> 100%
id: user-001
username: jsmith@example.com
status: connected
location: New York
```

### Locations

View location-based metrics and capacity information.

| Option | Description | Required |
| --- | --- | --- |
| `--list` | List all locations | No\* |
| `--id TEXT` | Get a specific location by ID | No\* |
| `--region TEXT` | Filter by geographic region | No |
| `--folder TEXT` | Filter by folder | No |
| `--max-results INT` | Maximum number of results to return (default: 100) | No |
| `--export TEXT` | Export format (json, csv) | No |
| `--output TEXT` | Output file path for export | No |
| `--mock` | Run in mock mode | No |

\* One of --list or --id is required.

#### List All Locations

```bash
$ scm insights locations --list
---> 100%
- id: loc-001
  name: US East
  region: us-east
  status: active
```

#### Filter by Region

```bash
$ scm insights locations --list --region us-east
---> 100%
- id: loc-001
  name: US East
  region: us-east
  status: active
```

#### Get Location Details

```bash
$ scm insights locations --id loc-001
---> 100%
id: loc-001
name: US East
region: us-east
status: active
capacity: 85%
```

### Remote Networks

Monitor remote network connectivity and performance.

| Option | Description | Required |
| --- | --- | --- |
| `--list` | List all remote networks | No\* |
| `--id TEXT` | Get a specific remote network by ID | No\* |
| `--connectivity TEXT` | Filter by connectivity status (connected, disconnected, degraded) | No |
| `--metrics` | Include performance metrics | No |
| `--folder TEXT` | Filter by folder | No |
| `--max-results INT` | Maximum number of results to return (default: 100) | No |
| `--export TEXT` | Export format (json, csv) | No |
| `--output TEXT` | Output file path for export | No |
| `--mock` | Run in mock mode | No |

\* One of --list or --id is required.

#### List All Remote Networks

```bash
$ scm insights remote-networks --list
---> 100%
- id: rn-001
  name: Branch-Office-1
  connectivity: connected
  site: Dallas
```

#### Filter by Connectivity Status

```bash
$ scm insights remote-networks --list --connectivity degraded
---> 100%
- id: rn-003
  name: Branch-Office-3
  connectivity: degraded
  site: Austin
```

#### Include Performance Metrics

```bash
$ scm insights remote-networks --list --metrics
---> 100%
- id: rn-001
  name: Branch-Office-1
  connectivity: connected
  latency_ms: 12
  throughput_mbps: 450
```

#### Get Specific Network Details

```bash
$ scm insights remote-networks --id rn-001 --metrics
---> 100%
id: rn-001
name: Branch-Office-1
connectivity: connected
latency_ms: 12
throughput_mbps: 450
packet_loss: 0.01%
```

### Service Connections

Monitor cloud service connections and their health status.

| Option | Description | Required |
| --- | --- | --- |
| `--list` | List all service connections | No\* |
| `--id TEXT` | Get a specific service connection by ID | No\* |
| `--health TEXT` | Filter by health status (healthy, unhealthy, degraded) | No |
| `--metrics` | Include performance metrics (latency, throughput) | No |
| `--folder TEXT` | Filter by folder | No |
| `--max-results INT` | Maximum number of results to return (default: 100) | No |
| `--export TEXT` | Export format (json, csv) | No |
| `--output TEXT` | Output file path for export | No |
| `--mock` | Run in mock mode | No |

\* One of --list or --id is required.

#### List All Service Connections

```bash
$ scm insights service-connections --list
---> 100%
- id: sc-001
  name: AWS-US-East
  health: healthy
  type: aws
```

#### Filter by Health Status

```bash
$ scm insights service-connections --list --health unhealthy
---> 100%
- id: sc-003
  name: Azure-EU-West
  health: unhealthy
  type: azure
```

#### Include Performance Metrics

```bash
$ scm insights service-connections --list --metrics
---> 100%
- id: sc-001
  name: AWS-US-East
  health: healthy
  latency_ms: 8
  throughput_mbps: 920
```

### Tunnels

Monitor IPSec and SSL tunnel status and performance.

| Option | Description | Required |
| --- | --- | --- |
| `--list` | List all tunnels | No\* |
| `--id TEXT` | Get a specific tunnel by ID | No\* |
| `--status TEXT` | Filter by tunnel status (up, down) | No |
| `--stats` | Include performance statistics | No |
| `--start DATETIME` | Filter historical data from this time (ISO format) | No |
| `--end DATETIME` | Filter historical data up to this time (ISO format) | No |
| `--folder TEXT` | Filter by folder | No |
| `--max-results INT` | Maximum number of results to return (default: 100) | No |
| `--export TEXT` | Export format (json, csv) | No |
| `--output TEXT` | Output file path for export | No |
| `--mock` | Run in mock mode | No |

\* One of --list or --id is required.

#### List All Tunnels

```bash
$ scm insights tunnels --list
---> 100%
- id: tunnel-001
  name: HQ-to-Branch1
  status: up
  type: ipsec
```

#### Filter by Status

```bash
$ scm insights tunnels --list --status down
---> 100%
- id: tunnel-003
  name: HQ-to-Branch3
  status: down
  type: ipsec
```

#### Include Statistics

```bash
$ scm insights tunnels --list --stats
---> 100%
- id: tunnel-001
  name: HQ-to-Branch1
  status: up
  bytes_in: 1234567890
  bytes_out: 987654321
```

#### Get Historical Data

```bash
$ scm insights tunnels --list \
    --start "2026-03-01T00:00:00" \
    --end "2026-03-08T23:59:59"
---> 100%
- id: tunnel-001
  name: HQ-to-Branch1
  status: up
```

## Common Options

All insights commands support these common options:

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Filter by folder | No |
| `--max-results INT` | Limit the number of results (default varies by command) | No |
| `--export TEXT` | Export format (json or csv) | No |
| `--output TEXT` | Output file path for exports | No |
| `--mock` | Run in mock mode for testing | No |

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
    "timestamp": "2026-03-08T10:30:00Z",
    "description": "CPU usage exceeded 95% threshold",
    "impacted_resources": ["fw-01", "fw-02"]
  }
]
```

### CSV Export

Exports data in CSV format with flattened fields:

```csv
id,name,severity,status,timestamp,description
alert-001,Critical CPU Usage,critical,active,2026-03-08T10:30:00Z,CPU usage exceeded 95% threshold
```

## Notes

- The insights APIs require appropriate permissions in your Strata Cloud Manager tenant
- Some metrics and statistics may have a delay of several minutes
- Export operations respect the `--max-results` limit
- Time filters accept ISO timestamps (e.g., `2026-03-01T00:00:00`)
- Alerts default to the last 7 days when no `--start` time is specified
- All commands support `--mock` for testing without API credentials
