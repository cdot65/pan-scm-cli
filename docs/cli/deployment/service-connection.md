# Service Connection

Service connections define how your branch offices and remote locations connect to Prisma SASE, enabling secure connectivity through IPsec tunnels with optional BGP routing and QoS configurations. The `scm` CLI provides commands to create, update, delete, list, and load service connection configurations.

## Overview

Service connections are essential for establishing secure site-to-site connectivity in Prisma SASE deployments. They support:

- Primary and backup IPsec tunnels for high availability
- BGP routing for dynamic route exchange
- QoS profiles for traffic prioritization
- Source NAT for address translation
- Multiple subnet support for complex networks

## Set Service Connection

Create or update a service connection configuration.

### Syntax

```bash
scm set sase service-connection [OPTIONS]
```

### Options

| Option                   | Description                                | Required |
| ------------------------ | ------------------------------------------ | -------- |
| `--name TEXT`            | Name of the service connection             | Yes      |
| `--ipsec-tunnel TEXT`    | IPsec tunnel for the service connection    | Yes      |
| `--region TEXT`          | Region for the service connection          | Yes      |
| `--onboarding-type TEXT` | Onboarding type (default: "classic")       | No       |
| `--backup-sc TEXT`       | Backup service connection name             | No       |
| `--nat-pool TEXT`        | NAT pool for the service connection        | No       |
| `--source-nat`           | Enable source NAT                          | No       |
| `--subnets LIST`         | List of subnets for the service connection | No       |
| `--bgp-enable`           | Enable BGP                                 | No       |
| `--bgp-peer-as TEXT`     | BGP peer AS number                         | No       |
| `--bgp-peer-ip TEXT`     | BGP peer IP address                        | No       |
| `--bgp-local-ip TEXT`    | BGP local IP address                       | No       |
| `--bgp-secret TEXT`      | BGP authentication secret                  | No       |
| `--qos-enable`           | Enable QoS                                 | No       |
| `--qos-profile TEXT`     | QoS profile name                           | No       |

### Examples

#### Create a Basic Service Connection

```bash
$ scm set sase service-connection --name "branch-office-1" \
  --ipsec-tunnel "ipsec-tunnel-branch-1" \
  --region "us-east-1" \
  --subnets "10.1.0.0/24,10.1.1.0/24"
Creating service connection 'branch-office-1'...
Service connection created successfully.
```

#### Create a Service Connection with BGP

```bash
$ scm set sase service-connection --name "hq-connection" \
  --ipsec-tunnel "ipsec-tunnel-hq" \
  --region "us-west-2" \
  --subnets "172.16.0.0/16" \
  --bgp-enable \
  --bgp-peer-as "65001" \
  --bgp-peer-ip "192.168.1.1" \
  --bgp-local-ip "192.168.1.2" \
  --bgp-secret "mysecret123"
Creating service connection 'hq-connection'...
Service connection created successfully.
```

#### Create a Service Connection with High Availability

```bash
$ scm set sase service-connection --name "critical-site" \
  --ipsec-tunnel "ipsec-tunnel-primary" \
  --region "eu-central-1" \
  --backup-sc "backup-connection" \
  --subnets "10.10.0.0/16" \
  --source-nat \
  --qos-enable \
  --qos-profile "business-critical"
Creating service connection 'critical-site'...
Service connection created successfully.
```

## Delete Service Connection

Delete a service connection configuration.

### Syntax

```bash
scm delete sase service-connection [OPTIONS]
```

### Options

| Option        | Description                              | Required |
| ------------- | ---------------------------------------- | -------- |
| `--name TEXT` | Name of the service connection to delete | Yes      |

### Example

```bash
$ scm delete sase service-connection --name "branch-office-1"
Deleting service connection 'branch-office-1'...
Service connection deleted successfully.
```

## Load Service Connections

Create or update multiple service connections from a YAML file.

### Syntax

```bash
scm load sase service-connection [OPTIONS]
```

### Options

| Option        | Description                                                 | Required |
| ------------- | ----------------------------------------------------------- | -------- |
| `--file TEXT` | Path to YAML file containing service connection definitions | Yes      |
| `--dry-run`   | Simulate execution without applying changes                 | No       |

### Example YAML File

```yaml
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

  - name: retail-store-001
    ipsec_tunnel: ipsec-tunnel-retail-001
    region: eu-west-1
    subnets:
      - 192.168.1.0/24
    bgp_enable: true
    bgp_peer_as: "65100"
    bgp_peer_ip_address: 10.0.0.1
    bgp_local_ip_address: 10.0.0.2
    bgp_originate_default_route: true
    bgp_summarize_mobile_user_routes: true
```

### Example Command

```bash
$ scm load sase service-connection --file service-connections.yaml
Loading service connections from 'service-connections.yaml'...
Applied service connection: branch-office-east
Applied service connection: branch-office-west
Applied service connection: retail-store-001
Loaded 3 service connection(s)
```

## Show Service Connections

Display service connection configurations.

### Syntax

```bash
scm show sase service-connection [OPTIONS]
```

### Options

| Option        | Description                            | Required |
| ------------- | -------------------------------------- | -------- |
| `--name TEXT` | Name of the service connection to show | No       |

### Examples

#### List All Service Connections

```bash
$ scm show sase service-connection
Service Connections:
------------------------------------------------------------
Name: branch-office-east
  IPsec Tunnel: ipsec-tunnel-east
  Region: us-east-1
  Onboarding Type: classic
  Subnets: 10.1.0.0/24, 10.1.1.0/24
  BGP: Enabled (AS 65001)
  ID: 12345678-1234-1234-1234-123456789012
------------------------------------------------------------
Name: branch-office-west
  IPsec Tunnel: ipsec-tunnel-west
  Region: us-west-2
  Onboarding Type: classic
  Subnets: 10.2.0.0/24, 10.2.1.0/24
  QoS: Enabled
  ID: 23456789-2345-2345-2345-234567890123
------------------------------------------------------------
Name: retail-store-001
  IPsec Tunnel: ipsec-tunnel-retail-001
  Region: eu-west-1
  Onboarding Type: classic
  Subnets: 192.168.1.0/24
  BGP: Enabled (AS 65100)
  ID: 34567890-3456-3456-3456-345678901234
------------------------------------------------------------
```

#### Show Specific Service Connection

```bash
$ scm show sase service-connection --name branch-office-east
Service Connection: branch-office-east
Folder: Service Connections
IPsec Tunnel: ipsec-tunnel-east
Region: us-east-1
Onboarding Type: classic
Subnets: 10.1.0.0/24, 10.1.1.0/24
BGP Settings:
  Enabled: True
  Peer AS: 65001
  Peer IP: 192.168.1.1
  Local IP: 192.168.1.2
ID: 12345678-1234-1234-1234-123456789012
```

## Backup Service Connections

Back up all service connections to a YAML file.

### Syntax

```bash
scm backup sase service-connection
```

### Example

```bash
$ scm backup sase service-connection
Successfully backed up 3 service connections to service-connections.yaml
```

## Advanced Configuration Examples

### Service Connection with Full BGP Options

```yaml
service_connections:
  - name: advanced-bgp-connection
    ipsec_tunnel: ipsec-tunnel-bgp
    region: us-central-1
    subnets:
      - 10.100.0.0/16
      - 10.101.0.0/16
    bgp_enable: true
    bgp_peer_as: "65500"
    bgp_peer_ip_address: 172.16.0.1
    bgp_local_ip_address: 172.16.0.2
    bgp_secret: strong-bgp-secret
    bgp_originate_default_route: true
    bgp_summarize_mobile_user_routes: true
    bgp_do_not_export_routes: false
    bgp_fast_failover: true
```

### Service Connection with NAT and QoS

```yaml
service_connections:
  - name: nat-qos-connection
    ipsec_tunnel: ipsec-tunnel-nat
    region: ap-southeast-1
    subnets:
      - 10.20.0.0/24
      - 10.20.1.0/24
      - 10.20.2.0/24
    source_nat: true
    nat_pool: branch-nat-pool
    qos_enable: true
    qos_profile: premium-bandwidth
    backup_SC: nat-qos-backup
```

### Service Connection with IPv6 Support

```yaml
service_connections:
  - name: dual-stack-connection
    ipsec_tunnel: ipsec-tunnel-v6
    region: eu-west-2
    subnets:
      - 10.30.0.0/24
      - 2001:db8:1::/64
    bgp_enable: true
    bgp_peer_as: "65600"
    bgp_peer_ip_address: 192.168.10.1
    bgp_local_ip_address: 192.168.10.2
    bgp_peer_ipv6_address: "2001:db8::1"
    bgp_local_ipv6_address: "2001:db8::2"
```

## Best Practices

1. **Naming Convention**: Use descriptive names that identify the location or purpose (e.g., "branch-office-nyc", "retail-store-001")

2. **High Availability**: Configure backup service connections for critical sites to ensure continuous connectivity

3. **BGP Configuration**: Use BGP for dynamic routing when connecting sites with multiple subnets or complex routing requirements

4. **Security**: Store BGP secrets securely and rotate them regularly

5. **QoS Profiles**: Apply appropriate QoS profiles to prioritize business-critical traffic

6. **Subnet Planning**: Carefully plan and document subnet allocations to avoid overlaps

7. **Regional Placement**: Choose regions closest to your physical locations for optimal performance

## Troubleshooting

### Common Issues

1. **IPsec Tunnel Not Found**

   - Ensure the referenced IPsec tunnel exists before creating the service connection
   - Verify the tunnel name is spelled correctly

2. **BGP Configuration Errors**

   - Verify peer AS numbers match your network configuration
   - Ensure IP addresses are correctly configured on both ends
   - Check that BGP secrets match on both peers

3. **Subnet Conflicts**

   - Check for overlapping subnets with other service connections
   - Ensure subnets don't conflict with Prisma SASE infrastructure ranges

4. **Regional Availability**
   - Verify the selected region is available for your tenant
   - Check service connection capacity limits for the region

### Debug Commands

```bash
# Show detailed service connection information
scm show sase service-connection --name <connection-name>

# Test configuration with dry-run
scm load sase service-connection --file config.yaml --dry-run

# Check IPsec tunnel status (requires appropriate permissions)
scm show network ipsec-tunnel --name <tunnel-name>
```
