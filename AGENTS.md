# AI Agent Instructions for pan-scm-cli

> This document provides comprehensive instructions for AI agents (Claude Code, Gemini CLI, etc.) to operate the `scm` CLI for managing Palo Alto Networks Strata Cloud Manager configurations.

## Quick Reference

```
scm <action> <category> <object-type> [options]
```

**Actions:** `set`, `delete`, `show`, `load`, `backup`, `move`
**Categories:** `object`, `network`, `security`, `identity`, `mobile-agent`, `setup`, `sase`
**Standalone:** `scm commit`, `scm context`, `scm jobs`, `scm insights`

---

## Authentication

### Context Setup (required before any API calls)

```bash
# Create a context with OAuth2 credentials
scm context create <name> --client-id <id> --client-secret <secret> --tsg-id <tsg>

# Create a context with bearer token
scm context create <name> --access-token <token>

# Switch active context
scm context use <name>

# Verify auth works
scm context test

# List / show / delete contexts
scm context list
scm context show [name]
scm context delete <name> [--force]
scm context current
```

**Environment variable overrides:** `SCM_CLIENT_ID`, `SCM_CLIENT_SECRET`, `SCM_TSG_ID`

**Mock mode:** Append `--mock` to most commands to test without API credentials.

---

## Container Locations

Most commands require exactly ONE container location:

| Flag | Description |
|------|-------------|
| `--folder <name>` | Folder in the hierarchy (most common) |
| `--snippet <name>` | Shared configuration snippet |
| `--device <name>` | Device-level configuration |

---

## Object Management (`scm ... object ...`)

### Addresses

**Create:**
```bash
# IP netmask
scm set object address --folder Texas --name webserver --ip-netmask 10.1.1.10/32 --description "Web server" --tags web prod

# IP range
scm set object address --folder Texas --name dhcp-pool --ip-range 10.1.3.1-10.1.3.10

# FQDN
scm set object address --folder Texas --name google-dns --fqdn dns.google.com

# IP wildcard
scm set object address --folder Texas --name wildcard --ip-wildcard 10.20.0.0/0.0.255.255
```

**Show / Delete:**
```bash
scm show object address --folder Texas                    # list all
scm show object address --folder Texas --name webserver   # show one
scm delete object address --folder Texas --name webserver [--force]
```

**Constraints:** Name 1-63 chars. Exactly ONE address type required.

---

### Address Groups

```bash
# Static group
scm set object address-group --folder Texas --name web-servers --type static --members webserver1 webserver2

# Dynamic group
scm set object address-group --folder Texas --name tagged-web --type dynamic --filter "'web' and 'prod'"
```

**Constraints:** Static requires `--members` (min 1). Dynamic uses tag-based filter expressions.

---

### Applications

```bash
scm set object application --folder Texas --name custom-app \
  --category business-systems --subcategory erp --technology client-server --risk 3 \
  --ports tcp/8080 tcp/8443 --transfers-files --has-known-vulnerabilities
```

**Risk levels:** 1-5. Boolean flags: `--evasive`, `--pervasive`, `--excessive-bandwidth-use`, `--used-by-malware`, `--transfers-files`, `--has-known-vulnerabilities`, `--tunnels-other-apps`, `--prone-to-misuse`, `--no-certifications`.

---

### Application Groups

```bash
scm set object application-group --folder Texas --name web-apps --members web-browsing ssl http
```

---

### Application Filters

```bash
scm set object application-filter --folder Texas --name high-risk \
  --category business-systems --subcategory erp --technology client-server --risk 4 5
```

---

### Tags

```bash
scm set object tag --folder Texas --name production --color Red --comments "Production environment"
```

**42 valid colors:** Red, Green, Blue, Yellow, Copper, Orange, Purple, Gray, Light Green, Cyan, Light Gray, Blue Gray, Lime, Black, Gold, Brown, Olive, Maroon, Red-Orange, Yellow-Orange, Forest Green, Turquoise Blue, Azure Blue, Cerulean Blue, Midnight Blue, Medium Blue, Cobalt Blue, Violet Blue, Blue Violet, Medium Violet, Medium Rose, Lavender, Orchid, Thistle, Peach, Salmon, Magenta, Red Violet, Mahogany, Burnt Sienna, Chestnut.

---

### Services

```bash
scm set object service --folder Texas --name web-http --protocol tcp --port 80
scm set object service --folder Texas --name web-https --protocol tcp --port 443 --timeout 3600
scm set object service --folder Texas --name multi-port --protocol tcp --port 80,443,8080
scm set object service --folder Texas --name port-range --protocol tcp --port 8000-8999
```

**Constraints:** Protocol: `tcp` or `udp`. Port: single, range (80-443), or comma-separated (80,443,8080).

---

### Service Groups

```bash
scm set object service-group --folder Texas --name web-services --members web-http web-https
```

**Constraints:** Members must be unique, can reference services or other service groups.

---

### Dynamic User Groups

```bash
scm set object dynamic-user-group --folder Texas --name risky-users \
  --filter "'high-risk' and 'external'" --description "High risk external users"
```

**Constraints:** Filter max 2047 chars. Uses tag-based expressions with single quotes.

---

### External Dynamic Lists

```bash
# Predefined IP list
scm set object external-dynamic-list --folder Texas --name bulletproof-ips \
  --type predefined_ip --url panw-bulletproof-ip-list

# Custom IP list with daily updates
scm set object external-dynamic-list --folder Texas --name threat-ips \
  --type ip --url https://example.com/threats.txt --recurring daily --hour 03

# Domain list with auth
scm set object external-dynamic-list --folder Texas --name blocked-domains \
  --type domain --url https://example.com/domains.txt --recurring hourly \
  --username api_user --password secret --expand-domain
```

**Types:** `predefined_ip`, `predefined_url`, `ip`, `domain`, `url`, `imsi`, `imei`.
**Recurring:** `five_minute`, `hourly`, `daily`, `weekly`, `monthly`.

---

### HIP Objects

```bash
scm set object hip-object --folder Texas --name corporate-host \
  --host-info-os Microsoft --host-info-managed true \
  --disk-encryption-enabled true
```

HIP objects have many criteria types (host info, network info, patch management, disk encryption, mobile device, certificate). Refer to `examples/hip-objects.yml` for full field reference.

---

### HIP Profiles

```bash
scm set object hip-profile --folder Texas --name corp-compliance \
  --match "corporate-host is"
```

---

### HTTP Server Profiles

```bash
scm set object http-server-profile --folder Texas --name webhook-profile \
  --server-name srv1 --server-address 192.168.1.1 --server-protocol HTTP \
  --server-port 8080 --server-http-method POST
```

**Important:** `http_method` is required for all server configs.

---

### Log Forwarding Profiles

```bash
scm set object log-forwarding-profile --folder Texas --name forward-all \
  --enhanced-application-logging
```

**Important:** The `filter` field is required in match list entries despite SDK docs showing it as optional.

---

### Syslog Server Profiles

```bash
scm set object syslog-server-profile --folder Texas --name syslog-central \
  --server-name syslog1 --server-address 192.168.1.100 \
  --server-transport UDP --server-port 514 --server-format BSD --server-facility LOG_USER
```

**Transport:** UDP, TCP. **Format:** BSD, IETF. **Facilities:** LOG_USER, LOG_LOCAL0 through LOG_LOCAL7.

---

### Schedules

```bash
scm set object schedule --folder Texas --name maintenance-window \
  --saturday 02:00-06:00 --sunday 02:00-06:00
```

---

### Regions

```bash
scm set object region --folder Texas --name us-east --address 10.0.0.0/8 172.16.0.0/12
```

---

### Auto Tag Actions

```bash
scm set object auto-tag-action --folder Texas --name auto-tag-threats
```

---

## Network Management (`scm ... network ...`)

### Security Zones

```bash
scm set network zone --folder Texas --name trust --interfaces ethernet1/1 ethernet1/2
scm show network zone --folder Texas
scm delete network zone --folder Texas --name trust [--force]
```

### Other Network Objects

All follow the same `scm <action> network <type>` pattern:

| Object Type | Description |
|-------------|-------------|
| `aggregate-interface` | Aggregate (LAG) interfaces |
| `bgp-address-family-profile` | BGP address family profiles |
| `bgp-auth-profile` | BGP authentication profiles |
| `bgp-filtering-profile` | BGP filtering profiles |
| `bgp-redistribution-profile` | BGP redistribution profiles |
| `bgp-route-map` | BGP route maps |
| `bgp-route-map-redistribution` | BGP route map redistribution |
| `dhcp-interface` | DHCP interface configs |
| `dns-proxy` | DNS proxy configs |
| `ethernet-interface` | Ethernet interfaces |
| `ike-crypto-profile` | IKE crypto profiles |
| `ike-gateway` | IKE gateways |
| `ipsec-crypto-profile` | IPSec crypto profiles |
| `layer2-subinterface` | Layer 2 subinterfaces |
| `layer3-subinterface` | Layer 3 subinterfaces |
| `loopback-interface` | Loopback interfaces |
| `nat-rule` | NAT rules |
| `ospf-auth-profile` | OSPF auth profiles |
| `pbf-rule` | Policy-based forwarding rules |
| `qos-profile` | QoS profiles |
| `qos-rule` | QoS rules |
| `route-access-list` | Route access lists |
| `route-prefix-list` | Route prefix lists |
| `tunnel-interface` | Tunnel interfaces |
| `vlan-interface` | VLAN interfaces |
| `zone` | Security zones |

---

## Security Management (`scm ... security ...`)

### Security Rules

**Create:**
```bash
scm set security rule --folder Texas --name allow-web \
  --source-zones trust --destination-zones untrust \
  --source-addresses any --destination-addresses web-servers \
  --applications web-browsing ssl --services application-default \
  --action allow --log-end --description "Allow web traffic" \
  --rulebase pre
```

**Show / Delete:**
```bash
scm show security rule --folder Texas
scm show security rule --folder Texas --name allow-web
scm delete security rule --folder Texas --name allow-web [--force]
```

**Move (reorder):**
```bash
scm move security rule --folder Texas --name allow-web --insert before --reference deny-all --rulebase pre
scm move security rule --folder Texas --name allow-web --insert after --reference allow-dns --rulebase pre
```

**Options:**
- `--source-zones`, `--destination-zones`: Zone names or `any`
- `--source-addresses`, `--destination-addresses`: Address/group names or `any`
- `--applications`: Application names or `any`
- `--services`: Service names, `application-default`, or `any`
- `--action`: `allow`, `deny`, `drop`
- `--enabled` / `--disabled`
- `--log-start`, `--log-end`
- `--log-setting`: Log forwarding profile name
- `--rulebase`: `pre` (default), `post`, `default`
- `--tags`: Tag names

### Security Profiles

| Object Type | Description |
|-------------|-------------|
| `anti-spyware-profile` | Anti-spyware profiles (min 1 rule required) |
| `app-override-rule` | Application override rules |
| `authentication-rule` | Authentication rules |
| `decryption-profile` | SSL/TLS decryption profiles |
| `decryption-rule` | Decryption rules |
| `dns-security-profile` | DNS security profiles |
| `url-access-profile` | URL filtering profiles |
| `url-category` | Custom URL categories |
| `vulnerability-protection-profile` | Vulnerability protection profiles |
| `wildfire-antivirus-profile` | WildFire antivirus profiles |

---

## Identity Management (`scm ... identity ...`)

| Object Type | Description |
|-------------|-------------|
| `authentication-profile` | Authentication profiles |
| `kerberos-server-profile` | Kerberos server profiles |
| `ldap-server-profile` | LDAP server profiles |
| `radius-server-profile` | RADIUS server profiles |
| `saml-server-profile` | SAML server profiles |
| `tacacs-server-profile` | TACACS+ server profiles |

---

## Mobile Agent (`scm ... mobile-agent ...`)

| Object Type | Description |
|-------------|-------------|
| `agent-version` | Agent versions (show only, read-only) |
| `auth-setting` | GlobalProtect auth settings |

```bash
scm set mobile-agent auth-setting --folder Texas --name gp-auth \
  --authentication-profile corp-auth --os Any
```

---

## Setup (`scm ... setup ...`)

### Folders

```bash
scm set setup folder --name "Branch Office" --parent "All Firewalls" --description "Branch config"
scm show setup folder
scm delete setup folder --name "Branch Office" [--force]
```

### Labels

```bash
scm set setup label --name production --description "Production environment"
```

### Snippets

```bash
scm set setup snippet --name shared-config --description "Shared configuration"
```

### Variables

```bash
scm set setup variable --folder Texas --name '$dns-server' --type ip-netmask --value 8.8.8.8/32
```

**Variable types:** `percent`, `count`, `ip-netmask`, `zone`, `ip-range`, `ip-wildcard`, `fqdn`, `port`, `egress-max`, and more.

---

## SASE / Deployment (`scm ... sase ...`)

| Object Type | Description |
|-------------|-------------|
| `bandwidth-allocation` | Bandwidth allocations |
| `bgp-routing` | BGP routing configs |
| `internal-dns-server` | Internal DNS servers |
| `remote-network` | Remote network configs |
| `service-connection` | Service connections |

```bash
scm set sase bandwidth-allocation --folder Texas --name site-bw --bandwidth 1000
scm show sase bandwidth-allocation --folder Texas
```

---

## Bulk Operations via YAML (`load` / `backup`)

### Loading from YAML

```bash
scm load object address --file addresses.yml [--dry-run]
scm load object address --file addresses.yml --folder Override-Folder
scm load security rule --file rules.yml [--dry-run]
```

- `--file` (required): Path to YAML file
- `--dry-run`: Preview changes without applying
- `--folder` / `--snippet` / `--device`: Override container location in the YAML

### Backing Up to YAML

```bash
scm backup object address --folder Texas [--file custom-output.yaml]
scm backup security rule --folder Texas --file rules-backup.yaml
```

- Defaults output file to `{object-type}-{location}.yaml`

### YAML File Formats

**Addresses:**
```yaml
addresses:
  - name: webserver
    folder: Texas
    ip_netmask: 10.1.1.10/32
    description: Web server
    tags: [web, prod]
  - name: dns-server
    folder: Texas
    fqdn: dns.google.com
```

**Address Groups:**
```yaml
address_groups:
  - name: web-servers
    folder: Texas
    type: static
    members: [webserver1, webserver2]
    tags: [web]
  - name: tagged-servers
    folder: Texas
    type: dynamic
    filter: "'web' and 'prod'"
```

**Services:**
```yaml
services:
  - name: web-http
    folder: Texas
    protocol:
      tcp:
        port: "80"
    tag: [web]
```

**Security Rules:**
```yaml
security_rules:
  - name: allow-web
    folder: Texas
    rulebase: pre
    source_zones: [trust]
    destination_zones: [untrust]
    source_addresses: [any]
    destination_addresses: [web-servers]
    applications: [web-browsing, ssl]
    service: [application-default]
    action: allow
    enabled: true
    log_end: true
```

**Tags:**
```yaml
tags:
  - name: production
    folder: Texas
    color: Red
    comments: Production environment
```

**Security Zones:**
```yaml
security_zones:
  - name: trust
    folder: Texas
    network:
      layer3: [ethernet1/1, ethernet1/2]
```

**External Dynamic Lists:**
```yaml
external_dynamic_lists:
  - name: threat-ips
    folder: Texas
    type: ip
    url: https://example.com/threats.txt
    recurring: daily
    hour: "03"
```

**Syslog Server Profiles:**
```yaml
syslog_server_profiles:
  - name: central-syslog
    folder: Texas
    server:
      - name: syslog1
        server: 192.168.1.100
        transport: UDP
        port: 514
        format: BSD
        facility: LOG_USER
```

See `examples/` directory for complete YAML templates for all object types.

---

## Committing Changes

Changes made via `set`, `delete`, or `load` are staged and must be committed:

```bash
# Simple commit
scm commit --folder Texas --description "Updated address objects"

# Multi-folder commit
scm commit --folder Texas --folder California --description "Multi-site update"

# Synchronous commit (wait for completion)
scm commit --folder Texas --description "Update" --sync --timeout 600
```

---

## Job Management

```bash
scm jobs list [--max-results 50]
scm jobs status --id 12345
scm jobs wait --id 12345 [--timeout 600]
```

---

## Insights (Monitoring)

```bash
# Alerts
scm insights alerts --list [--severity Critical] [--max-results 20]
scm insights alerts --id <alert-id>
scm insights alerts --list --export json --output alerts.json

# Mobile users
scm insights mobile-users --list [--status connected] [--location "US West"]

# Locations
scm insights locations --list [--region "Americas"]

# Remote networks
scm insights remote-networks --list [--connectivity connected] [--metrics]

# Service connections
scm insights service-connections --list [--health healthy] [--metrics]

# Tunnels
scm insights tunnels --list [--status up] [--stats]
```

All insights commands support: `--export json|csv`, `--output <file>`, `--max-results <n>`, `--folder <name>`, `--mock`.

---

## Common Workflows for Agents

### 1. Create a complete security policy

```bash
# Step 1: Create tags
scm set object tag --folder Texas --name web-tier --color Blue
scm set object tag --folder Texas --name app-tier --color Green

# Step 2: Create address objects
scm set object address --folder Texas --name web-server-1 --ip-netmask 10.1.1.10/32 --tags web-tier
scm set object address --folder Texas --name app-server-1 --ip-netmask 10.1.2.10/32 --tags app-tier

# Step 3: Create address groups
scm set object address-group --folder Texas --name web-servers --type static --members web-server-1
scm set object address-group --folder Texas --name app-servers --type static --members app-server-1

# Step 4: Create security rule
scm set security rule --folder Texas --name allow-web-to-app \
  --source-zones web --destination-zones app \
  --source-addresses web-servers --destination-addresses app-servers \
  --applications web-browsing ssl --services application-default \
  --action allow --log-end --rulebase pre

# Step 5: Commit
scm commit --folder Texas --description "Add web-to-app security policy" --sync
```

### 2. Bulk import from YAML

```bash
# Preview first
scm load object address --file addresses.yml --dry-run

# Apply
scm load object address --file addresses.yml

# Commit
scm commit --folder Texas --description "Bulk address import"
```

### 3. Backup and restore

```bash
# Backup everything
scm backup object address --folder Texas --file addr-backup.yaml
scm backup object tag --folder Texas --file tag-backup.yaml
scm backup security rule --folder Texas --file rule-backup.yaml

# Restore
scm load object tag --file tag-backup.yaml
scm load object address --file addr-backup.yaml
scm load security rule --file rule-backup.yaml
scm commit --folder Texas --description "Restore from backup" --sync
```

### 4. Monitor and troubleshoot

```bash
# Check alerts
scm insights alerts --list --severity Critical --max-results 10

# Check tunnel status
scm insights tunnels --list --status down

# Check mobile user connectivity
scm insights mobile-users --list --status disconnected

# Export for analysis
scm insights alerts --list --export csv --output alerts.csv
```

---

## Important Notes for Agents

1. **Always commit after changes.** `set`, `delete`, and `load` stage changes but do not apply them until `scm commit` is run.
2. **One address type per address object.** Use exactly one of: `--ip-netmask`, `--ip-range`, `--ip-wildcard`, `--fqdn`.
3. **One container per command.** Specify exactly one of `--folder`, `--snippet`, or `--device`.
4. **Boolean fields:** Omit false booleans from YAML to avoid API validation errors.
5. **Tag references must exist.** Tags referenced by objects must be created first.
6. **Service names are singular in SDK.** e.g., `application_filter` not `application_filters`.
7. **Predefined EDLs use short names.** e.g., `panw-bulletproof-ip-list` not the full URL.
8. **HTTP server profiles require `http_method`.** Always include it.
9. **Log forwarding profile match lists require `filter`.** Despite SDK docs showing it as optional.
10. **`--force` skips confirmation prompts.** Use on `delete` commands when running non-interactively.
11. **`--mock` flag** is available on most commands for testing without API credentials.
12. **Security rule ordering matters.** Use `scm move security rule` to reorder rules after creation.
13. **Rulebase options:** `pre` (before default rules), `post` (after), `default` (the default rulebase).
14. **Color names are case-sensitive in API** but case-insensitive in the CLI validator.
15. **YAML key names** may differ from CLI flags (e.g., YAML uses `tag` while CLI uses `--tags`). Refer to the examples above.
