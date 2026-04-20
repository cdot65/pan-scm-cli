# Service Connection

Service connections define how branch offices and remote locations connect to Prisma SASE, enabling secure connectivity through IPsec tunnels with optional BGP routing and QoS configurations. The `scm` CLI provides commands to create, update, delete, bulk load, and back up service connection configurations.

## Overview

!!! important
    When creating a service connection, all referenced IKE gateways and IPsec tunnels **must exist in the `Service Connections` folder** (not in user-created custom folders). References to resources in other folders will result in `INVALID_REFERENCE` errors.

The `service-connection` commands allow you to:

- Create service connections with IPsec tunnels and subnet configurations
- Configure BGP routing for dynamic route exchange
- Enable QoS profiles for traffic prioritization and source NAT
- Bulk import service connection configurations from YAML files
- Export service connection configurations for backup or migration

## Set Service Connection

Create or update a service connection configuration.

### Syntax

```bash
scm set sase service-connection [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the service connection | Yes |
| `--ipsec-tunnel TEXT` | IPsec tunnel for the service connection | Yes |
| `--region TEXT` | Region for the service connection | Yes |
| `--onboarding-type TEXT` | Onboarding type (default: classic) | No |
| `--backup-sc TEXT` | Backup service connection name | No |
| `--nat-pool TEXT` | NAT pool for the service connection | No |
| `--source-nat` | Enable source NAT | No |
| `--subnets LIST` | Comma-separated list of subnets | No |
| `--bgp-enable` | Enable BGP | No |
| `--bgp-peer-as TEXT` | BGP peer AS number | No |
| `--bgp-peer-ip TEXT` | BGP peer IP address | No |
| `--bgp-local-ip TEXT` | BGP local IP address | No |
| `--bgp-secret TEXT` | BGP authentication secret | No |
| `--qos-enable` | Enable QoS | No |
| `--qos-profile TEXT` | QoS profile name | No |

### Examples

#### Create a Basic Service Connection

```bash
$ scm set sase service-connection \
    --name branch-office-1 \
    --ipsec-tunnel ipsec-tunnel-branch-1 \
    --region us-east-1 \
    --subnets "10.1.0.0/24,10.1.1.0/24"
---> 100%
Created service connection: branch-office-1
```

#### Create a Service Connection with BGP

```bash
$ scm set sase service-connection \
    --name hq-connection \
    --ipsec-tunnel ipsec-tunnel-hq \
    --region us-west-2 \
    --subnets "172.16.0.0/16" \
    --bgp-enable \
    --bgp-peer-as "65001" \
    --bgp-peer-ip "192.168.1.1" \
    --bgp-local-ip "192.168.1.2" \
    --bgp-secret "mysecret123"
---> 100%
Created service connection: hq-connection
```

#### Create a Service Connection with High Availability

```bash
$ scm set sase service-connection \
    --name critical-site \
    --ipsec-tunnel ipsec-tunnel-primary \
    --region eu-central-1 \
    --backup-sc backup-connection \
    --subnets "10.10.0.0/16" \
    --source-nat \
    --qos-enable \
    --qos-profile business-critical
---> 100%
Created service connection: critical-site
```

## Delete Service Connection

Delete a service connection configuration from SCM.

### Syntax

```bash
scm delete sase service-connection [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the service connection to delete | Yes |
| `--force` | Skip confirmation prompt | No |

### Example

```bash
$ scm delete sase service-connection --name branch-office-1 --force
---> 100%
Deleted service connection: branch-office-1
```

## Load Service Connections

Load multiple service connection configurations from a YAML file.

### Syntax

```bash
scm load sase service-connection [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing service connection definitions | Yes |
| `--dry-run` | Simulate execution without applying changes | No |

### YAML File Format

```yaml
---
service_connections:
  - name: branch-office-east
    ipsec_tunnel: ipsec-tunnel-east
    region: us-east-1
    onboarding_type: classic
    subnets:
      - 10.1.0.0/24
      - 10.1.1.0/24
    bgp_enable: true
    bgp_peer_as: "65001"
    bgp_peer_ip_address: 192.168.1.1
    bgp_local_ip_address: 192.168.1.2
    bgp_secret: bgp-secret-east

  - name: branch-office-west
    ipsec_tunnel: ipsec-tunnel-west
    region: us-west-2
    backup_SC: branch-office-west-backup
    subnets:
      - 10.2.0.0/24
      - 10.2.1.0/24
    source_nat: true
    nat_pool: nat-pool-west
    qos_enable: true
    qos_profile: standard-qos
```

### Examples

#### Load Service Connections

```bash
$ scm load sase service-connection --file service-connections.yml
---> 100%
✓ Loaded service connection: branch-office-east
✓ Loaded service connection: branch-office-west

Successfully loaded 2 out of 2 service connections from 'service-connections.yml'
```

#### Dry Run to Validate Configuration

```bash
$ scm load sase service-connection --file service-connections.yml --dry-run
---> 100%
[DRY RUN] Would load service connection: branch-office-east
[DRY RUN] Would load service connection: branch-office-west

Dry run complete. 2 service connections would be loaded.
```

## Show Service Connection

Display service connection configurations.

### Syntax

```bash
scm show sase service-connection [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the service connection to show | No |

!!! note
    When no `--name` is specified, all items are listed by default.

### Examples

#### Show Specific Service Connection

```bash
$ scm show sase service-connection --name branch-office-east
---> 100%
Service Connection: branch-office-east
  IPsec Tunnel: ipsec-tunnel-east
  Region: us-east-1
  Onboarding Type: classic
  Subnets: 10.1.0.0/24, 10.1.1.0/24
  BGP Settings:
    Enabled: true
    Peer AS: 65001
    Peer IP: 192.168.1.1
    Local IP: 192.168.1.2
```

#### List All Service Connections (Default Behavior)

```bash
$ scm show sase service-connection
---> 100%
Service Connections:
------------------------------------------------------------
Name: branch-office-east
  IPsec Tunnel: ipsec-tunnel-east
  Region: us-east-1
  Subnets: 10.1.0.0/24, 10.1.1.0/24
  BGP: Enabled (AS 65001)
------------------------------------------------------------
Name: branch-office-west
  IPsec Tunnel: ipsec-tunnel-west
  Region: us-west-2
  Subnets: 10.2.0.0/24, 10.2.1.0/24
  QoS: Enabled
------------------------------------------------------------
```

## Backup Service Connections

Backup all service connection configurations to a YAML file.

### Syntax

```bash
scm backup sase service-connection [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Custom output filename | No |

### Examples

#### Backup with Default Filename

```bash
$ scm backup sase service-connection
---> 100%
Successfully backed up 3 service connections to service_connection_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup sase service-connection --file sc-backup.yaml
---> 100%
Successfully backed up 3 service connections to sc-backup.yaml
```

## Best Practices

1. **Use Descriptive Names**: Name service connections to clearly identify the location or purpose (e.g., "branch-office-nyc", "retail-store-001").
2. **Folder Scope for Dependencies**: Always create IKE gateways and IPsec tunnels used for service connections in the `Service Connections` folder to avoid invalid reference errors.
3. **Configure Backup Connections**: Set up backup service connections for critical sites to ensure continuous connectivity during primary tunnel failures.
4. **Enable BGP for Complex Networks**: Use BGP dynamic routing when connecting sites with multiple subnets or complex routing requirements.
5. **Secure BGP Secrets**: Store BGP authentication secrets securely and rotate them regularly to maintain routing security.
6. **Apply QoS Profiles**: Assign appropriate QoS profiles to prioritize business-critical traffic over less important flows.
7. **Plan Subnets Carefully**: Document subnet allocations across all service connections to avoid overlaps and ensure proper routing.

## Related Topics

- [Remote Network](remote-network.md)
- [BGP Routing](bgp-routing.md)
