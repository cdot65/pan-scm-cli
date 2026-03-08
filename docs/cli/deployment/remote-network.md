# Remote Network

Remote networks represent branch offices, data centers, or other physical locations that connect to Prisma SASE. The `scm` CLI provides commands to create, update, delete, bulk load, and back up remote network configurations.

## Overview

The `remote-network` commands allow you to:

- Create remote networks with IPsec tunnel and subnet configurations
- Configure BGP routing for dynamic route exchange
- Enable ECMP load balancing across multiple tunnels
- Bulk import remote network configurations from YAML files
- Export remote network configurations for backup or migration

## Remote Network Components

| Component | Description |
| --- | --- |
| **Region** | SASE deployment region for the remote network |
| **SPN** | Service Provider Network association (required for FWAAS-AGGREGATE) |
| **IPsec Tunnel** | Primary tunnel for secure connectivity (required when ECMP disabled) |
| **ECMP** | Equal-Cost Multi-Path load balancing across up to 4 tunnels |
| **BGP** | Dynamic routing with peer AS, IP addressing, and authentication |
| **License Type** | Licensing model (default: FWAAS-AGGREGATE) |

## Set Remote Network

Create or update a remote network configuration.

### Syntax

```bash
scm set sase remote-network [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the remote network | Yes |
| `--region TEXT` | Region for the remote network | Yes |
| `--license-type TEXT` | License type (default: FWAAS-AGGREGATE) | No |
| `--description TEXT` | Description of the remote network | No |
| `--subnets LIST` | Comma-separated list of subnets | No |
| `--spn-name TEXT` | SPN name (required for FWAAS-AGGREGATE license) | No |
| `--ecmp-load-balancing TEXT` | Enable or disable ECMP (default: disable) | No |
| `--ipsec-tunnel TEXT` | IPsec tunnel (required when ECMP is disabled) | No |
| `--secondary-ipsec-tunnel TEXT` | Secondary IPsec tunnel for redundancy | No |
| `--bgp-enable` | Enable BGP | No |
| `--bgp-peer-as TEXT` | BGP peer AS number | No |
| `--bgp-peer-ip TEXT` | BGP peer IP address | No |
| `--bgp-local-ip TEXT` | BGP local IP address | No |
| `--bgp-secret TEXT` | BGP authentication secret | No |

### Examples

#### Create a Basic Remote Network

```bash
$ scm set sase remote-network \
    --name branch-office-nyc \
    --region us-east-1 \
    --spn-name us-east-spn \
    --ipsec-tunnel ipsec-tunnel-nyc \
    --subnets "10.1.0.0/24,10.1.1.0/24" \
    --description "New York branch office"
---> 100%
Created remote network: branch-office-nyc
```

#### Create a Remote Network with BGP

```bash
$ scm set sase remote-network \
    --name datacenter-west \
    --region us-west-2 \
    --spn-name us-west-spn \
    --ipsec-tunnel ipsec-tunnel-dc-west \
    --subnets "172.16.0.0/16,172.17.0.0/16" \
    --bgp-enable \
    --bgp-peer-as "65001" \
    --bgp-peer-ip "192.168.1.1" \
    --bgp-local-ip "192.168.1.2" \
    --bgp-secret "bgp-secret-west"
---> 100%
Created remote network: datacenter-west
```

#### Create a Remote Network with ECMP Load Balancing

```bash
$ scm set sase remote-network \
    --name hq-campus \
    --region eu-central-1 \
    --spn-name eu-central-spn \
    --ecmp-load-balancing enable \
    --subnets "10.0.0.0/8" \
    --description "Headquarters campus with ECMP"
---> 100%
Created remote network: hq-campus
```

#### Create a Remote Network with Redundant Tunnels

```bash
$ scm set sase remote-network \
    --name critical-site \
    --region ap-southeast-1 \
    --spn-name ap-southeast-spn \
    --ipsec-tunnel ipsec-tunnel-primary \
    --secondary-ipsec-tunnel ipsec-tunnel-secondary \
    --subnets "192.168.0.0/16" \
    --description "Critical site with tunnel redundancy"
---> 100%
Created remote network: critical-site
```

## Delete Remote Network

Delete a remote network configuration from SCM.

### Syntax

```bash
scm delete sase remote-network [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the remote network to delete | Yes |

### Example

```bash
$ scm delete sase remote-network --name branch-office-nyc
---> 100%
Deleted remote network: branch-office-nyc
```

## Load Remote Networks

Load multiple remote network configurations from a YAML file.

### Syntax

```bash
scm load sase remote-network [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing remote network definitions | Yes |
| `--dry-run` | Simulate execution without applying changes | No |

### YAML File Format

```yaml
---
remote_networks:
  - name: branch-office-east
    folder: Remote Networks
    region: us-east-1
    license_type: FWAAS-AGGREGATE
    description: "East coast branch office"
    spn_name: us-east-spn
    subnets:
      - 10.1.0.0/24
      - 10.1.1.0/24
    ecmp_load_balancing: disable
    ipsec_tunnel: ipsec-tunnel-east
    bgp_enable: true
    bgp_peer_as: "65001"
    bgp_peer_ip_address: 192.168.1.1
    bgp_local_ip_address: 192.168.1.2
    bgp_secret: bgp-secret-east

  - name: datacenter-central
    folder: Remote Networks
    region: us-central-1
    license_type: FWAAS-AGGREGATE
    description: "Central datacenter with ECMP"
    spn_name: us-central-spn
    subnets:
      - 172.16.0.0/12
      - 192.168.0.0/16
    ecmp_load_balancing: enable
    ecmp_tunnels:
      - name: ipsec-tunnel-dc-1
        priority: 10
      - name: ipsec-tunnel-dc-2
        priority: 10
      - name: ipsec-tunnel-dc-3
        priority: 20
      - name: ipsec-tunnel-dc-4
        priority: 20
```

### Examples

#### Load Remote Networks

```bash
$ scm load sase remote-network --file remote-networks.yml
---> 100%
✓ Loaded remote network: branch-office-east
✓ Loaded remote network: datacenter-central

Successfully loaded 2 out of 2 remote networks from 'remote-networks.yml'
```

#### Dry Run to Validate Configuration

```bash
$ scm load sase remote-network --file remote-networks.yml --dry-run
---> 100%
[DRY RUN] Would load remote network: branch-office-east
[DRY RUN] Would load remote network: datacenter-central

Dry run complete. 2 remote networks would be loaded.
```

## Show Remote Network

Display remote network configurations.

### Syntax

```bash
scm show sase remote-network [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the remote network to show | No |

!!! note
    When no `--name` is specified, all items are listed by default.

### Examples

#### Show Specific Remote Network

```bash
$ scm show sase remote-network --name datacenter-central
---> 100%
Remote Network: datacenter-central
  Folder: Remote Networks
  Region: us-central-1
  License Type: FWAAS-AGGREGATE
  Description: Central datacenter with ECMP
  Subnets: 172.16.0.0/12, 192.168.0.0/16
  SPN Name: us-central-spn
  ECMP Load Balancing: enable
  ECMP Tunnels:
    ipsec-tunnel-dc-1 (priority: 10)
    ipsec-tunnel-dc-2 (priority: 10)
    ipsec-tunnel-dc-3 (priority: 20)
    ipsec-tunnel-dc-4 (priority: 20)
```

#### List All Remote Networks (Default Behavior)

```bash
$ scm show sase remote-network
---> 100%
Remote Networks:
------------------------------------------------------------
Name: branch-office-east
  Region: us-east-1
  Subnets: 10.1.0.0/24, 10.1.1.0/24
  ECMP: disable
  BGP: Enabled (AS 65001)
------------------------------------------------------------
Name: datacenter-central
  Region: us-central-1
  Subnets: 172.16.0.0/12, 192.168.0.0/16
  ECMP: enable
------------------------------------------------------------
```

## Backup Remote Networks

Backup all remote network configurations to a YAML file.

### Syntax

```bash
scm backup sase remote-network [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Custom output filename | No |

### Examples

#### Backup with Default Filename

```bash
$ scm backup sase remote-network
---> 100%
Successfully backed up 4 remote networks to remote_network_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup sase remote-network --file remote-networks-backup.yaml
---> 100%
Successfully backed up 4 remote networks to remote-networks-backup.yaml
```

## Best Practices

1. **Use Consistent Naming**: Adopt a naming scheme that includes location and purpose (e.g., "region-city-type") for easy identification across large deployments.
2. **Plan Subnets Carefully**: Document all subnets to avoid overlaps and reserve address space for future growth using hierarchical addressing.
3. **Configure ECMP for Critical Sites**: Use ECMP load balancing with up to 4 tunnels for locations requiring high bandwidth and resilience.
4. **Enable BGP with Authentication**: Use private AS numbers (64512-65535) and configure BGP authentication secrets for secure dynamic routing.
5. **Deploy Redundant Tunnels**: Configure secondary IPsec tunnels for critical sites, ideally using different ISPs for primary and secondary paths.
6. **Select Nearest Region**: Choose the closest SASE region for optimal performance, while considering data sovereignty and disaster recovery requirements.
