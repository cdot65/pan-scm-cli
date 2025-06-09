# SASE Commands Examples

This document provides practical examples of Service Connection and Remote Network commands for Prisma SASE deployments. These examples demonstrate real-world scenarios and best practices for connecting branch offices, data centers, and remote locations to Prisma SASE.

## Table of Contents

1. [Basic Branch Office Setup](#basic-branch-office-setup)
2. [Data Center with BGP](#data-center-with-bgp)
3. [High Availability Configuration](#high-availability-configuration)
4. [ECMP Load Balancing](#ecmp-load-balancing)
5. [Global Deployment](#global-deployment)
6. [Retail Chain Deployment](#retail-chain-deployment)
7. [Migration Scenarios](#migration-scenarios)
8. [Troubleshooting Examples](#troubleshooting-examples)

## Basic Branch Office Setup

### Scenario
Connect a small branch office with basic requirements:
- Single subnet (10.1.0.0/24)
- Primary IPsec tunnel
- No BGP required

### Commands

```bash
# Step 1: Create the remote network
scm set deployment remote-network \
  --name "branch-office-dallas" \
  --region "us-south-1" \
  --spn-name "us-south-spn" \
  --ipsec-tunnel "ipsec-tunnel-dallas" \
  --subnets "10.1.0.0/24" \
  --description "Dallas branch office - 50 users"

# Step 2: Create the service connection
scm set deployment service-connection \
  --name "dallas-connection" \
  --ipsec-tunnel "ipsec-tunnel-dallas" \
  --region "us-south-1" \
  --subnets "10.1.0.0/24"

# Step 3: Verify the configuration
scm show deployment remote-network --name "branch-office-dallas"
scm show deployment service-connection --name "dallas-connection"
```

### YAML Configuration

```yaml
# remote-networks-basic.yaml
remote_networks:
  - name: branch-office-dallas
    folder: Remote Networks
    region: us-south-1
    license_type: FWAAS-AGGREGATE
    description: "Dallas branch office - 50 users"
    spn_name: us-south-spn
    subnets:
      - 10.1.0.0/24
    ecmp_load_balancing: disable
    ipsec_tunnel: ipsec-tunnel-dallas

# service-connections-basic.yaml
service_connections:
  - name: dallas-connection
    ipsec_tunnel: ipsec-tunnel-dallas
    region: us-south-1
    subnets:
      - 10.1.0.0/24
```

## Data Center with BGP

### Scenario
Connect a data center with multiple subnets and dynamic routing:
- Multiple subnets
- BGP for dynamic route advertisement
- QoS for traffic prioritization

### Commands

```bash
# Step 1: Create the remote network with BGP
scm set deployment remote-network \
  --name "datacenter-east" \
  --region "us-east-1" \
  --spn-name "us-east-spn" \
  --ipsec-tunnel "ipsec-tunnel-dc-east" \
  --subnets "172.16.0.0/16,172.17.0.0/16,172.18.0.0/16" \
  --description "Primary data center - East Coast" \
  --bgp-enable \
  --bgp-peer-as "65001" \
  --bgp-peer-ip "192.168.1.1" \
  --bgp-local-ip "192.168.1.2" \
  --bgp-secret "Bgp$ecret123"

# Step 2: Create the service connection with BGP and QoS
scm set deployment service-connection \
  --name "dc-east-connection" \
  --ipsec-tunnel "ipsec-tunnel-dc-east" \
  --region "us-east-1" \
  --subnets "172.16.0.0/16,172.17.0.0/16,172.18.0.0/16" \
  --bgp-enable \
  --bgp-peer-as "65001" \
  --bgp-peer-ip "192.168.1.1" \
  --bgp-local-ip "192.168.1.2" \
  --bgp-secret "Bgp$ecret123" \
  --qos-enable \
  --qos-profile "datacenter-qos"
```

### YAML Configuration

```yaml
# remote-networks-datacenter.yaml
remote_networks:
  - name: datacenter-east
    folder: Remote Networks
    region: us-east-1
    license_type: FWAAS-AGGREGATE
    description: "Primary data center - East Coast"
    spn_name: us-east-spn
    subnets:
      - 172.16.0.0/16
      - 172.17.0.0/16
      - 172.18.0.0/16
    ecmp_load_balancing: disable
    ipsec_tunnel: ipsec-tunnel-dc-east
    bgp_enable: true
    bgp_peer_as: "65001"
    bgp_peer_ip_address: 192.168.1.1
    bgp_local_ip_address: 192.168.1.2
    bgp_secret: "Bgp$ecret123"
    bgp_originate_default_route: false
    bgp_summarize_mobile_user_routes: true

# service-connections-datacenter.yaml
service_connections:
  - name: dc-east-connection
    ipsec_tunnel: ipsec-tunnel-dc-east
    region: us-east-1
    subnets:
      - 172.16.0.0/16
      - 172.17.0.0/16
      - 172.18.0.0/16
    bgp_enable: true
    bgp_peer_as: "65001"
    bgp_peer_ip_address: 192.168.1.1
    bgp_local_ip_address: 192.168.1.2
    bgp_secret: "Bgp$ecret123"
    bgp_fast_failover: true
    bgp_originate_default_route: false
    bgp_summarize_mobile_user_routes: true
    qos_enable: true
    qos_profile: datacenter-qos
```

## High Availability Configuration

### Scenario
Configure a critical site with redundant connections:
- Primary and secondary IPsec tunnels
- Backup service connection
- BGP with fast failover

### Commands

```bash
# Step 1: Create the remote network with redundant tunnels
scm set deployment remote-network \
  --name "hq-campus" \
  --region "us-west-2" \
  --spn-name "us-west-spn" \
  --ipsec-tunnel "ipsec-tunnel-hq-primary" \
  --secondary-ipsec-tunnel "ipsec-tunnel-hq-secondary" \
  --subnets "10.0.0.0/8" \
  --description "Corporate headquarters with HA" \
  --bgp-enable \
  --bgp-peer-as "65000" \
  --bgp-peer-ip "192.168.10.1" \
  --bgp-local-ip "192.168.10.2"

# Step 2: Create primary service connection
scm set deployment service-connection \
  --name "hq-primary-connection" \
  --ipsec-tunnel "ipsec-tunnel-hq-primary" \
  --region "us-west-2" \
  --subnets "10.0.0.0/8" \
  --backup-sc "hq-backup-connection" \
  --bgp-enable \
  --bgp-peer-as "65000" \
  --bgp-peer-ip "192.168.10.1" \
  --bgp-local-ip "192.168.10.2"

# Step 3: Create backup service connection
scm set deployment service-connection \
  --name "hq-backup-connection" \
  --ipsec-tunnel "ipsec-tunnel-hq-secondary" \
  --region "us-west-2" \
  --subnets "10.0.0.0/8" \
  --bgp-enable \
  --bgp-peer-as "65000" \
  --bgp-peer-ip "192.168.11.1" \
  --bgp-local-ip "192.168.11.2"
```

### YAML Configuration

```yaml
# high-availability-setup.yaml
remote_networks:
  - name: hq-campus
    folder: Remote Networks
    region: us-west-2
    license_type: FWAAS-AGGREGATE
    description: "Corporate headquarters with HA"
    spn_name: us-west-spn
    subnets:
      - 10.0.0.0/8
    ecmp_load_balancing: disable
    ipsec_tunnel: ipsec-tunnel-hq-primary
    secondary_ipsec_tunnel: ipsec-tunnel-hq-secondary
    bgp_enable: true
    bgp_peer_as: "65000"
    bgp_peer_ip_address: 192.168.10.1
    bgp_local_ip_address: 192.168.10.2
    bgp_secret: "ha-bgp-secret"

service_connections:
  - name: hq-primary-connection
    ipsec_tunnel: ipsec-tunnel-hq-primary
    region: us-west-2
    backup_SC: hq-backup-connection
    subnets:
      - 10.0.0.0/8
    bgp_enable: true
    bgp_peer_as: "65000"
    bgp_peer_ip_address: 192.168.10.1
    bgp_local_ip_address: 192.168.10.2
    bgp_secret: "ha-bgp-secret"
    bgp_fast_failover: true
    qos_enable: true
    qos_profile: business-critical

  - name: hq-backup-connection
    ipsec_tunnel: ipsec-tunnel-hq-secondary
    region: us-west-2
    subnets:
      - 10.0.0.0/8
    bgp_enable: true
    bgp_peer_as: "65000"
    bgp_peer_ip_address: 192.168.11.1
    bgp_local_ip_address: 192.168.11.2
    bgp_secret: "ha-bgp-secret"
    bgp_fast_failover: true
```

## ECMP Load Balancing

### Scenario
Configure a high-bandwidth location with ECMP load balancing:
- Multiple IPsec tunnels for load distribution
- Weighted load balancing
- Large subnet space

### Commands

```bash
# Create the remote network with ECMP (requires YAML for ecmp_tunnels)
scm load deployment remote-network --file ecmp-config.yaml
```

### YAML Configuration

```yaml
# ecmp-config.yaml
remote_networks:
  - name: datacenter-central
    folder: Remote Networks
    region: us-central-1
    license_type: FWAAS-AGGREGATE
    description: "Central datacenter with 4x10G ECMP"
    spn_name: us-central-spn
    subnets:
      - 172.20.0.0/12
      - 192.168.0.0/16
      - 10.100.0.0/16
    ecmp_load_balancing: enable
    ecmp_tunnels:
      - name: ipsec-tunnel-dc-isp1-primary
        priority: 10
        weight: 30
      - name: ipsec-tunnel-dc-isp1-secondary
        priority: 10
        weight: 30
      - name: ipsec-tunnel-dc-isp2-primary
        priority: 10
        weight: 20
      - name: ipsec-tunnel-dc-isp2-secondary
        priority: 10
        weight: 20
    bgp_enable: true
    bgp_peer_as: "65100"
    bgp_peer_ip_address: 172.31.1.1
    bgp_local_ip_address: 172.31.1.2
    bgp_secret: "ecmp-bgp-secret"

# Note: Service connections are created separately for each tunnel in ECMP scenarios
service_connections:
  - name: dc-central-isp1-primary
    ipsec_tunnel: ipsec-tunnel-dc-isp1-primary
    region: us-central-1
    subnets:
      - 172.20.0.0/12
      - 192.168.0.0/16
      - 10.100.0.0/16
    bgp_enable: true
    bgp_peer_as: "65100"
    bgp_peer_ip_address: 172.31.1.1
    bgp_local_ip_address: 172.31.1.2
    bgp_secret: "ecmp-bgp-secret"

  - name: dc-central-isp1-secondary
    ipsec_tunnel: ipsec-tunnel-dc-isp1-secondary
    region: us-central-1
    subnets:
      - 172.20.0.0/12
      - 192.168.0.0/16
      - 10.100.0.0/16
    bgp_enable: true
    bgp_peer_as: "65100"
    bgp_peer_ip_address: 172.31.2.1
    bgp_local_ip_address: 172.31.2.2
    bgp_secret: "ecmp-bgp-secret"
```

## Global Deployment

### Scenario
Deploy SASE connectivity for a global organization with offices worldwide.

### YAML Configuration

```yaml
# global-deployment.yaml
remote_networks:
  # Americas
  - name: na-hq-newyork
    folder: Remote Networks
    region: us-east-1
    license_type: FWAAS-AGGREGATE
    description: "North America HQ - New York"
    spn_name: na-east-spn
    subnets:
      - 10.1.0.0/16
      - 10.2.0.0/16
    ecmp_load_balancing: enable
    ecmp_tunnels:
      - name: na-ny-tunnel-1
      - name: na-ny-tunnel-2
    bgp_enable: true
    bgp_peer_as: "65001"
    bgp_peer_ip_address: 192.168.1.1
    bgp_local_ip_address: 192.168.1.2

  - name: na-branch-toronto
    folder: Remote Networks
    region: canada-central-1
    license_type: FWAAS-AGGREGATE
    description: "Canada branch - Toronto"
    spn_name: ca-central-spn
    subnets:
      - 10.10.0.0/16
    ipsec_tunnel: na-toronto-tunnel
    bgp_enable: true
    bgp_peer_as: "65010"
    bgp_peer_ip_address: 192.168.10.1
    bgp_local_ip_address: 192.168.10.2

  # Europe
  - name: eu-hq-london
    folder: Remote Networks
    region: eu-west-2
    license_type: FWAAS-AGGREGATE
    description: "European HQ - London"
    spn_name: eu-west-spn
    subnets:
      - 10.20.0.0/16
      - 10.21.0.0/16
    ipsec_tunnel: eu-london-tunnel-primary
    secondary_ipsec_tunnel: eu-london-tunnel-secondary
    bgp_enable: true
    bgp_peer_as: "65020"
    bgp_peer_ip_address: 192.168.20.1
    bgp_local_ip_address: 192.168.20.2

  - name: eu-branch-frankfurt
    folder: Remote Networks
    region: eu-central-1
    license_type: FWAAS-AGGREGATE
    description: "Germany branch - Frankfurt"
    spn_name: eu-central-spn
    subnets:
      - 10.30.0.0/16
    ipsec_tunnel: eu-frankfurt-tunnel

  # Asia Pacific
  - name: apac-hq-singapore
    folder: Remote Networks
    region: ap-southeast-1
    license_type: FWAAS-AGGREGATE
    description: "APAC HQ - Singapore"
    spn_name: apac-spn
    subnets:
      - 10.40.0.0/16
      - 10.41.0.0/16
    ecmp_load_balancing: enable
    ecmp_tunnels:
      - name: apac-sg-tunnel-1
      - name: apac-sg-tunnel-2
    bgp_enable: true
    bgp_peer_as: "65040"
    bgp_peer_ip_address: 192.168.40.1
    bgp_local_ip_address: 192.168.40.2

  - name: apac-branch-sydney
    folder: Remote Networks
    region: ap-southeast-2
    license_type: FWAAS-AGGREGATE
    description: "Australia branch - Sydney"
    spn_name: apac-au-spn
    subnets:
      - 10.50.0.0/16
    ipsec_tunnel: apac-sydney-tunnel

service_connections:
  # Americas connections
  - name: na-hq-connection-1
    ipsec_tunnel: na-ny-tunnel-1
    region: us-east-1
    subnets:
      - 10.1.0.0/16
      - 10.2.0.0/16
    bgp_enable: true
    bgp_peer_as: "65001"
    bgp_peer_ip_address: 192.168.1.1
    bgp_local_ip_address: 192.168.1.2
    qos_enable: true
    qos_profile: global-hq

  - name: na-toronto-connection
    ipsec_tunnel: na-toronto-tunnel
    region: canada-central-1
    subnets:
      - 10.10.0.0/16
    bgp_enable: true
    bgp_peer_as: "65010"
    bgp_peer_ip_address: 192.168.10.1
    bgp_local_ip_address: 192.168.10.2

  # Europe connections
  - name: eu-london-primary
    ipsec_tunnel: eu-london-tunnel-primary
    region: eu-west-2
    backup_SC: eu-london-backup
    subnets:
      - 10.20.0.0/16
      - 10.21.0.0/16
    bgp_enable: true
    bgp_peer_as: "65020"
    bgp_peer_ip_address: 192.168.20.1
    bgp_local_ip_address: 192.168.20.2
    qos_enable: true
    qos_profile: global-hq

  - name: eu-frankfurt-connection
    ipsec_tunnel: eu-frankfurt-tunnel
    region: eu-central-1
    subnets:
      - 10.30.0.0/16

  # APAC connections
  - name: apac-singapore-connection-1
    ipsec_tunnel: apac-sg-tunnel-1
    region: ap-southeast-1
    subnets:
      - 10.40.0.0/16
      - 10.41.0.0/16
    bgp_enable: true
    bgp_peer_as: "65040"
    bgp_peer_ip_address: 192.168.40.1
    bgp_local_ip_address: 192.168.40.2
    qos_enable: true
    qos_profile: global-hq
```

## Retail Chain Deployment

### Scenario
Deploy SASE for a retail chain with hundreds of small locations.

### Template Configuration

```yaml
# retail-template.yaml
remote_networks:
  - name: retail-store-001
    folder: Remote Networks
    region: us-east-1
    license_type: FWAAS-AGGREGATE
    description: "Retail Store #001 - New York, NY"
    spn_name: retail-east-spn
    subnets:
      - 192.168.1.0/24
    ipsec_tunnel: retail-001-tunnel

  - name: retail-store-002
    folder: Remote Networks
    region: us-east-1
    license_type: FWAAS-AGGREGATE
    description: "Retail Store #002 - Boston, MA"
    spn_name: retail-east-spn
    subnets:
      - 192.168.2.0/24
    ipsec_tunnel: retail-002-tunnel

  - name: retail-store-003
    folder: Remote Networks
    region: us-west-2
    license_type: FWAAS-AGGREGATE
    description: "Retail Store #003 - Seattle, WA"
    spn_name: retail-west-spn
    subnets:
      - 192.168.3.0/24
    ipsec_tunnel: retail-003-tunnel

service_connections:
  - name: retail-001-connection
    ipsec_tunnel: retail-001-tunnel
    region: us-east-1
    subnets:
      - 192.168.1.0/24
    source_nat: true
    nat_pool: retail-nat-pool

  - name: retail-002-connection
    ipsec_tunnel: retail-002-tunnel
    region: us-east-1
    subnets:
      - 192.168.2.0/24
    source_nat: true
    nat_pool: retail-nat-pool

  - name: retail-003-connection
    ipsec_tunnel: retail-003-tunnel
    region: us-west-2
    subnets:
      - 192.168.3.0/24
    source_nat: true
    nat_pool: retail-nat-pool
```

### Bulk Generation Script

```bash
#!/bin/bash
# generate-retail-configs.sh

# Generate configurations for 100 retail stores
for i in {1..100}; do
  store_num=$(printf "%03d" $i)
  subnet_third_octet=$i
  
  # Determine region based on store number
  if [ $i -le 33 ]; then
    region="us-east-1"
    spn="retail-east-spn"
  elif [ $i -le 66 ]; then
    region="us-west-2"
    spn="retail-west-spn"
  else
    region="eu-west-1"
    spn="retail-eu-spn"
  fi
  
  # Create individual YAML files
  cat > "retail-store-${store_num}.yaml" << EOF
remote_networks:
  - name: retail-store-${store_num}
    folder: Remote Networks
    region: ${region}
    license_type: FWAAS-AGGREGATE
    description: "Retail Store #${store_num}"
    spn_name: ${spn}
    subnets:
      - 192.168.${subnet_third_octet}.0/24
    ipsec_tunnel: retail-${store_num}-tunnel

service_connections:
  - name: retail-${store_num}-connection
    ipsec_tunnel: retail-${store_num}-tunnel
    region: ${region}
    subnets:
      - 192.168.${subnet_third_octet}.0/24
    source_nat: true
    nat_pool: retail-nat-pool
EOF
done

# Load all configurations
for file in retail-store-*.yaml; do
  echo "Loading $file..."
  scm load deployment remote-network --file "$file"
  scm load deployment service-connection --file "$file"
done
```

## Migration Scenarios

### Scenario 1: Migrating from Legacy VPN to Prisma SASE

```bash
# Step 1: Create remote network with same subnets as legacy VPN
scm set deployment remote-network \
  --name "legacy-dc-migration" \
  --region "us-east-1" \
  --spn-name "us-east-spn" \
  --ipsec-tunnel "prisma-sase-tunnel" \
  --subnets "10.0.0.0/8,172.16.0.0/12,192.168.0.0/16" \
  --description "Data center migration from legacy VPN" \
  --bgp-enable \
  --bgp-peer-as "65001" \
  --bgp-peer-ip "10.255.255.1" \
  --bgp-local-ip "10.255.255.2"

# Step 2: Create service connection with higher BGP local preference
scm set deployment service-connection \
  --name "dc-migration-connection" \
  --ipsec-tunnel "prisma-sase-tunnel" \
  --region "us-east-1" \
  --subnets "10.0.0.0/8,172.16.0.0/12,192.168.0.0/16" \
  --bgp-enable \
  --bgp-peer-as "65001" \
  --bgp-peer-ip "10.255.255.1" \
  --bgp-local-ip "10.255.255.2"

# Step 3: Monitor traffic and gradually shift from legacy to Prisma SASE
# Step 4: Decommission legacy VPN once migration is complete
```

### Scenario 2: Phased Branch Migration

```yaml
# phase1-branches.yaml - Pilot branches
remote_networks:
  - name: pilot-branch-01
    folder: Remote Networks
    region: us-east-1
    license_type: FWAAS-AGGREGATE
    description: "Pilot branch for SASE migration"
    spn_name: us-east-spn
    subnets:
      - 10.101.0.0/24
    ipsec_tunnel: pilot-01-tunnel

# phase2-branches.yaml - Production rollout
remote_networks:
  - name: prod-branch-01
    folder: Remote Networks
    region: us-east-1
    license_type: FWAAS-AGGREGATE
    description: "Production branch - Wave 1"
    spn_name: us-east-spn
    subnets:
      - 10.201.0.0/24
    ipsec_tunnel: prod-01-tunnel
    secondary_ipsec_tunnel: prod-01-tunnel-backup
```

## Troubleshooting Examples

### Check Connectivity Status

```bash
# List all remote networks and their status
scm show deployment remote-network

# Check specific remote network details
scm show deployment remote-network --name "branch-office-dallas"

# List all service connections
scm show deployment service-connection

# Check specific service connection
scm show deployment service-connection --name "dallas-connection"
```

### Verify BGP Configuration

```bash
# Check BGP settings for a remote network
scm show deployment remote-network --name "datacenter-east" | grep -A5 "BGP"

# Verify BGP peer configuration
scm show deployment service-connection --name "dc-east-connection" | grep -A5 "BGP"
```

### Test Configuration Before Applying

```bash
# Dry run to validate configuration
scm load deployment remote-network --file test-config.yaml --dry-run
scm load deployment service-connection --file test-config.yaml --dry-run
```

### Backup and Restore

```bash
# Backup current configurations
scm backup deployment remote-network
scm backup deployment service-connection

# This creates:
# - remote-networks.yaml
# - service-connections.yaml

# Restore from backup
scm load deployment remote-network --file remote-networks.yaml
scm load deployment service-connection --file service-connections.yaml
```

### Common Error Resolution

```bash
# Error: "ipsec_tunnel is required when ecmp_load_balancing is disable"
# Solution: Specify an IPsec tunnel when not using ECMP
scm set deployment remote-network \
  --name "branch-office" \
  --region "us-east-1" \
  --ipsec-tunnel "branch-tunnel"  # Add this

# Error: "spn_name is required when license_type is FWAAS-AGGREGATE"
# Solution: Add the SPN name
scm set deployment remote-network \
  --name "branch-office" \
  --region "us-east-1" \
  --spn-name "us-east-spn"  # Add this

# Error: "BGP peer configuration mismatch"
# Solution: Ensure BGP settings match between remote network and service connection
# Check both configurations have matching:
# - bgp_peer_as
# - bgp_peer_ip_address
# - bgp_local_ip_address
# - bgp_secret
```

## Best Practices Summary

1. **Always create remote networks before service connections**
   - Remote networks define the location
   - Service connections establish the logical connection

2. **Use consistent naming conventions**
   - Include location identifiers
   - Add purpose or type (e.g., "hq", "branch", "dc")
   - Use sequential numbering for similar sites

3. **Plan IP addressing carefully**
   - Document all subnets
   - Avoid overlaps with Prisma SASE infrastructure
   - Reserve space for growth

4. **Implement high availability for critical sites**
   - Use primary and secondary tunnels
   - Configure backup service connections
   - Enable BGP fast failover

5. **Use YAML files for bulk operations**
   - Easier to manage multiple sites
   - Version control friendly
   - Supports dry-run testing

6. **Regular backups**
   - Backup configurations before major changes
   - Store backups in version control
   - Test restore procedures

7. **Monitor and optimize**
   - Review bandwidth utilization
   - Adjust ECMP weights as needed
   - Update QoS profiles based on traffic patterns