# Remote Network

Remote networks represent branch offices, data centers, or other physical locations that connect to Prisma SASE. The `scm` CLI provides commands to create, update, delete, list, and load remote network configurations.

## Overview

Remote networks are fundamental building blocks in Prisma SASE deployments, defining:

- Physical locations and their associated subnets
- IPsec tunnel assignments for secure connectivity
- BGP routing configurations for dynamic route exchange
- ECMP (Equal-Cost Multi-Path) settings for load balancing
- Licensing models for the remote location

## Set Remote Network

Create or update a remote network configuration.

### Syntax

```bash
scm set sase remote-network [OPTIONS]
```

### Options

| Option                          | Description                                     | Required |
| ------------------------------- | ----------------------------------------------- | -------- |
| `--name TEXT`                   | Name of the remote network                      | Yes      |
| `--region TEXT`                 | Region for the remote network                   | Yes      |
| `--license-type TEXT`           | License type (default: "FWAAS-AGGREGATE")       | No       |
| `--description TEXT`            | Description of the remote network               | No       |
| `--subnets LIST`                | List of subnets for the remote network          | No       |
| `--spn-name TEXT`               | SPN name (required for FWAAS-AGGREGATE license) | No       |
| `--ecmp-load-balancing TEXT`    | Enable or disable ECMP (default: "disable")     | No       |
| `--ipsec-tunnel TEXT`           | IPsec tunnel (required when ECMP is disabled)   | No       |
| `--secondary-ipsec-tunnel TEXT` | Secondary IPsec tunnel for redundancy           | No       |
| `--bgp-enable`                  | Enable BGP                                      | No       |
| `--bgp-peer-as TEXT`            | BGP peer AS number                              | No       |
| `--bgp-peer-ip TEXT`            | BGP peer IP address                             | No       |
| `--bgp-local-ip TEXT`           | BGP local IP address                            | No       |
| `--bgp-secret TEXT`             | BGP authentication secret                       | No       |

### Examples

#### Create a Basic Remote Network

```bash
$ scm set sase remote-network --name "branch-office-nyc" \
  --region "us-east-1" \
  --spn-name "us-east-spn" \
  --ipsec-tunnel "ipsec-tunnel-nyc" \
  --subnets "10.1.0.0/24,10.1.1.0/24" \
  --description "New York branch office"
Creating remote network 'branch-office-nyc'...
Remote network created successfully.
```

#### Create a Remote Network with BGP

```bash
$ scm set sase remote-network --name "datacenter-west" \
  --region "us-west-2" \
  --license-type "FWAAS-AGGREGATE" \
  --spn-name "us-west-spn" \
  --ipsec-tunnel "ipsec-tunnel-dc-west" \
  --subnets "172.16.0.0/16,172.17.0.0/16" \
  --bgp-enable \
  --bgp-peer-as "65001" \
  --bgp-peer-ip "192.168.1.1" \
  --bgp-local-ip "192.168.1.2" \
  --bgp-secret "bgp-secret-west"
Creating remote network 'datacenter-west'...
Remote network created successfully.
```

#### Create a Remote Network with ECMP Load Balancing

```bash
$ scm set sase remote-network --name "hq-campus" \
  --region "eu-central-1" \
  --spn-name "eu-central-spn" \
  --ecmp-load-balancing "enable" \
  --subnets "10.0.0.0/8" \
  --description "Headquarters campus network with ECMP"
Creating remote network 'hq-campus'...
Remote network created successfully.
```

#### Create a Remote Network with Redundant Tunnels

```bash
$ scm set sase remote-network --name "critical-site" \
  --region "ap-southeast-1" \
  --spn-name "ap-southeast-spn" \
  --ipsec-tunnel "ipsec-tunnel-primary" \
  --secondary-ipsec-tunnel "ipsec-tunnel-secondary" \
  --subnets "192.168.0.0/16" \
  --description "Critical site with tunnel redundancy"
Creating remote network 'critical-site'...
Remote network created successfully.
```

## Delete Remote Network

Delete a remote network configuration.

### Syntax

```bash
scm delete sase remote-network [OPTIONS]
```

### Options

| Option        | Description                          | Required |
| ------------- | ------------------------------------ | -------- |
| `--name TEXT` | Name of the remote network to delete | Yes      |

### Example

```bash
$ scm delete sase remote-network --name "branch-office-nyc"
Deleting remote network 'branch-office-nyc'...
Remote network deleted successfully.
```

## Load Remote Networks

Create or update multiple remote networks from a YAML file.

### Syntax

```bash
scm load sase remote-network [OPTIONS]
```

### Options

| Option        | Description                                             | Required |
| ------------- | ------------------------------------------------------- | -------- |
| `--file TEXT` | Path to YAML file containing remote network definitions | Yes      |
| `--dry-run`   | Simulate execution without applying changes             | No       |

### Example YAML File

```yaml
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
      - 10.1.2.0/24
    ecmp_load_balancing: disable
    ipsec_tunnel: ipsec-tunnel-east
    bgp_enable: true
    bgp_peer_as: "65001"
    bgp_peer_ip_address: 192.168.1.1
    bgp_local_ip_address: 192.168.1.2
    bgp_secret: bgp-secret-east

  - name: branch-office-west
    folder: Remote Networks
    region: us-west-2
    license_type: FWAAS-AGGREGATE
    description: "West coast branch office with redundancy"
    spn_name: us-west-spn
    subnets:
      - 10.2.0.0/24
      - 10.2.1.0/24
    ecmp_load_balancing: disable
    ipsec_tunnel: ipsec-tunnel-west-primary
    secondary_ipsec_tunnel: ipsec-tunnel-west-secondary
    bgp_enable: true
    bgp_peer_as: "65002"
    bgp_peer_ip_address: 192.168.2.1
    bgp_local_ip_address: 192.168.2.2
    bgp_originate_default_route: true

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

  - name: retail-store-001
    folder: Remote Networks
    region: eu-west-1
    license_type: FWAAS-AGGREGATE
    description: "Retail location 001"
    spn_name: eu-west-spn
    subnets:
      - 192.168.100.0/24
    ecmp_load_balancing: disable
    ipsec_tunnel: ipsec-tunnel-retail-001
```

### Example Command

```bash
$ scm load sase remote-network --file remote-networks.yaml
Loading remote networks from 'remote-networks.yaml'...
Applied remote network: branch-office-east
Applied remote network: branch-office-west
Applied remote network: datacenter-central
Applied remote network: retail-store-001
Loaded 4 remote network(s)
```

## Show Remote Networks

Display remote network configurations.

### Syntax

```bash
scm show sase remote-network [OPTIONS]
```

### Options

| Option        | Description                        | Required |
| ------------- | ---------------------------------- | -------- |
| `--name TEXT` | Name of the remote network to show | No       |

### Examples

#### List All Remote Networks

```bash
$ scm show sase remote-network
Remote Networks:
------------------------------------------------------------
Name: branch-office-east
  Folder: Remote Networks
  Region: us-east-1
  License Type: FWAAS-AGGREGATE
  Subnets: 10.1.0.0/24, 10.1.1.0/24, 10.1.2.0/24
  ECMP: disable
  BGP: Enabled (AS 65001)
  ID: 12345678-1234-1234-1234-123456789012
------------------------------------------------------------
Name: branch-office-west
  Folder: Remote Networks
  Region: us-west-2
  License Type: FWAAS-AGGREGATE
  Subnets: 10.2.0.0/24, 10.2.1.0/24
  ECMP: disable
  BGP: Enabled (AS 65002)
  ID: 23456789-2345-2345-2345-234567890123
------------------------------------------------------------
Name: datacenter-central
  Folder: Remote Networks
  Region: us-central-1
  License Type: FWAAS-AGGREGATE
  Subnets: 172.16.0.0/12, 192.168.0.0/16
  ECMP: enable
  ID: 34567890-3456-3456-3456-345678901234
------------------------------------------------------------
```

#### Show Specific Remote Network

```bash
$ scm show sase remote-network --name datacenter-central
Remote Network: datacenter-central
Folder: Remote Networks
Region: us-central-1
License Type: FWAAS-AGGREGATE
Description: Central datacenter with ECMP
Subnets: 172.16.0.0/12, 192.168.0.0/16
SPN Name: us-central-spn
ECMP Load Balancing: enable
ECMP Tunnels:
  Tunnel 1: ipsec-tunnel-dc-1
  Tunnel 2: ipsec-tunnel-dc-2
  Tunnel 3: ipsec-tunnel-dc-3
  Tunnel 4: ipsec-tunnel-dc-4
ID: 34567890-3456-3456-3456-345678901234
```

## Backup Remote Networks

Back up all remote networks to a YAML file.

### Syntax

```bash
scm backup sase remote-network
```

### Example

```bash
$ scm backup sase remote-network
Successfully backed up 4 remote networks to remote-networks.yaml
```

## Advanced Configuration Examples

### Remote Network with Full BGP Options

```yaml
remote_networks:
  - name: advanced-bgp-site
    folder: Remote Networks
    region: us-east-1
    license_type: FWAAS-AGGREGATE
    spn_name: us-east-spn
    subnets:
      - 10.100.0.0/16
      - 10.101.0.0/16
      - 10.102.0.0/16
    ecmp_load_balancing: disable
    ipsec_tunnel: ipsec-tunnel-bgp
    bgp_enable: true
    bgp_peer_as: "65500"
    bgp_peer_ip_address: 172.16.0.1
    bgp_local_ip_address: 172.16.0.2
    bgp_secret: strong-bgp-secret
    bgp_peering_type: external
    bgp_originate_default_route: true
    bgp_summarize_mobile_user_routes: true
    bgp_do_not_export_routes: false
```

### Remote Network with ECMP and Weighted Load Balancing

```yaml
remote_networks:
  - name: datacenter-ecmp
    folder: Remote Networks
    region: ap-southeast-1
    license_type: FWAAS-AGGREGATE
    description: "Datacenter with weighted ECMP load balancing"
    spn_name: ap-southeast-spn
    subnets:
      - 172.20.0.0/16
      - 172.21.0.0/16
      - 172.22.0.0/16
      - 172.23.0.0/16
    ecmp_load_balancing: enable
    ecmp_tunnels:
      - name: ipsec-tunnel-primary-1
        priority: 10
        weight: 50
      - name: ipsec-tunnel-primary-2
        priority: 10
        weight: 50
      - name: ipsec-tunnel-backup-1
        priority: 20
        weight: 30
      - name: ipsec-tunnel-backup-2
        priority: 20
        weight: 70
```

### Multiple Remote Networks for Global Deployment

```yaml
remote_networks:
  # North America
  - name: na-hq-campus
    folder: Remote Networks
    region: us-east-1
    license_type: FWAAS-AGGREGATE
    description: "North America headquarters"
    spn_name: na-east-spn
    subnets:
      - 10.0.0.0/16
      - 10.1.0.0/16
    ecmp_load_balancing: enable
    ecmp_tunnels:
      - name: na-hq-tunnel-1
      - name: na-hq-tunnel-2

  # Europe
  - name: eu-office-london
    folder: Remote Networks
    region: eu-west-2
    license_type: FWAAS-AGGREGATE
    description: "European office - London"
    spn_name: eu-west-spn
    subnets:
      - 10.20.0.0/16
    ipsec_tunnel: eu-london-tunnel
    bgp_enable: true
    bgp_peer_as: "65100"
    bgp_peer_ip_address: 192.168.100.1
    bgp_local_ip_address: 192.168.100.2

  # Asia Pacific
  - name: apac-office-singapore
    folder: Remote Networks
    region: ap-southeast-1
    license_type: FWAAS-AGGREGATE
    description: "APAC office - Singapore"
    spn_name: apac-spn
    subnets:
      - 10.30.0.0/16
    ipsec_tunnel: apac-singapore-tunnel
    secondary_ipsec_tunnel: apac-singapore-tunnel-backup
```

## Best Practices

1. **Naming Convention**: Use a consistent naming scheme that includes location and purpose (e.g., "region-city-type")

2. **Subnet Planning**:

   - Document all subnets to avoid overlaps
   - Use hierarchical addressing for easier summarization
   - Reserve address space for future growth

3. **ECMP Configuration**:

   - Use ECMP for locations requiring high bandwidth
   - Configure up to 4 tunnels for load balancing
   - Set appropriate priorities and weights

4. **BGP Best Practices**:

   - Use private AS numbers (64512-65535) for enterprise networks
   - Enable route summarization to reduce routing table size
   - Configure BGP authentication for security

5. **High Availability**:

   - Configure secondary tunnels for critical sites
   - Use different ISPs for primary and secondary tunnels
   - Test failover scenarios regularly

6. **Regional Selection**:
   - Choose the nearest region for optimal performance
   - Consider data sovereignty requirements
   - Plan for disaster recovery scenarios

## Troubleshooting

### Common Issues

1. **License Type Errors**

   - FWAAS-AGGREGATE requires spn_name to be specified
   - Verify license entitlements in your tenant

2. **ECMP Configuration Issues**

   - ECMP requires ecmp_tunnels when enabled
   - Maximum of 4 tunnels can be configured
   - Cannot use ipsec_tunnel when ECMP is enabled

3. **Tunnel Configuration Conflicts**

   - When ECMP is disabled, ipsec_tunnel is required
   - Ensure tunnel names exist before referencing them
   - Check for tunnel capacity limits

4. **BGP Connection Problems**
   - Verify AS numbers don't conflict
   - Ensure IP addresses are correctly configured
   - Check BGP secrets match on both ends
   - Confirm routing policies allow BGP

### Debug Commands

```bash
# Show detailed remote network information
scm show sase remote-network --name <network-name>

# Verify IPsec tunnel configuration
scm show network ipsec-tunnel --name <tunnel-name>

# Test configuration with dry-run
scm load sase remote-network --file config.yaml --dry-run

# Check BGP routing status (requires appropriate permissions)
scm show network bgp-routes --remote-network <network-name>
```

## Integration with Service Connections

Remote networks work in conjunction with service connections to establish complete site-to-site connectivity:

1. **Remote Network**: Defines the physical location and its properties
2. **Service Connection**: Establishes the logical connection using IPsec tunnels

Example workflow:

```bash
# 1. Create IPsec tunnel
scm set network ipsec-tunnel --name "site-tunnel" ...

# 2. Create remote network
scm set sase remote-network --name "branch-site" --ipsec-tunnel "site-tunnel" ...

# 3. Create service connection
scm set sase service-connection --name "branch-connection" --ipsec-tunnel "site-tunnel" ...
```
