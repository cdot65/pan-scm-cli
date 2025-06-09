# SCM CLI Commands Documentation

This directory contains the command modules for the Strata Cloud Manager CLI. Each module groups related commands following a consistent pattern.

## Command Modules

### objects.py

This module contains commands for managing various configuration objects in Strata Cloud Manager. All commands follow the pattern:

```bash
scm <action> objects <object-type> [options]
```

#### Supported Object Types and Commands

##### Address Objects

```bash
# Create/update an address object
scm set objects address --folder Shared --name web-server \
  --ip-netmask 192.168.1.100/32 --description "Web server"

# Show address objects
scm show objects address --folder Shared --list
scm show objects address --folder Shared --name web-server

# Delete an address object
scm delete objects address --folder Shared --name web-server

# Bulk load from YAML
scm load objects address --folder Shared --file addresses.yml

# Backup to YAML
scm backup objects address --folder Shared
```

##### Address Groups

```bash
# Create/update an address group
scm set objects address-group --folder Shared --name servers \
  --type static --members "web-server,db-server"

# Show address groups
scm show objects address-group --folder Shared --list
scm show objects address-group --folder Shared --name servers

# Delete an address group
scm delete objects address-group --folder Shared --name servers

# Bulk operations
scm load objects address-group --folder Shared --file address-groups.yml
scm backup objects address-group --folder Shared
```

##### Applications

```bash
# Create/update an application
scm set objects application --folder Shared --name custom-app \
  --category business-systems --subcategory database \
  --technology client-server --risk 3 --ports "tcp/8080"

# Show applications
scm show objects application --folder Shared --list
scm show objects application --folder Shared --name custom-app

# Delete an application
scm delete objects application --folder Shared --name custom-app

# Bulk operations
scm load objects application --folder Shared --file applications.yml
scm backup objects application --folder Shared
```

##### Application Groups

```bash
# Create/update an application group
scm set objects application-group --folder Shared --name business-apps \
  --members "salesforce,office365,custom-app"

# Show application groups
scm show objects application-group --folder Shared --list
scm show objects application-group --folder Shared --name business-apps

# Delete an application group
scm delete objects application-group --folder Shared --name business-apps

# Bulk operations
scm load objects application-group --folder Shared --file app-groups.yml
scm backup objects application-group --folder Shared
```

##### Application Filters

```bash
# Create/update an application filter
scm set objects application-filter --folder Shared --name high-risk \
  --category "file-sharing" --risk 4 --risk 5

# Show application filters
scm show objects application-filter --folder Shared --list
scm show objects application-filter --folder Shared --name high-risk

# Delete an application filter
scm delete objects application-filter --folder Shared --name high-risk

# Bulk operations
scm load objects application-filter --folder Shared --file app-filters.yml
scm backup objects application-filter --folder Shared
```

##### Dynamic User Groups

```bash
# Create/update a dynamic user group
scm set objects dynamic-user-group --folder Shared --name it-admins \
  --filter "'IT' and 'Admin'"

# Show dynamic user groups
scm show objects dynamic-user-group --folder Shared --list
scm show objects dynamic-user-group --folder Shared --name it-admins

# Delete a dynamic user group
scm delete objects dynamic-user-group --folder Shared --name it-admins

# Bulk operations
scm load objects dynamic-user-group --folder Shared --file user-groups.yml
scm backup objects dynamic-user-group --folder Shared
```

##### External Dynamic Lists

```bash
# Create/update an external dynamic list
scm set objects external-dynamic-list --folder Shared \
  --name threat-list --type ip \
  --url "https://example.com/threats.txt" --recurring hourly

# Show external dynamic lists
scm show objects external-dynamic-list --folder Shared --list
scm show objects external-dynamic-list --folder Shared --name threat-list

# Delete an external dynamic list
scm delete objects external-dynamic-list --folder Shared --name threat-list

# Bulk operations
scm load objects external-dynamic-list --folder Shared --file edls.yml
scm backup objects external-dynamic-list --folder Shared
```

##### HIP Objects

```bash
# Create/update a HIP object
scm set objects hip-object --folder Shared --name windows-compliance \
  --patch-management-vendor-name "Microsoft Corporation" \
  --patch-management-product-name "Windows" \
  --patch-management-criteria-is-installed yes

# Show HIP objects
scm show objects hip-object --folder Shared --list
scm show objects hip-object --folder Shared --name windows-compliance

# Delete a HIP object
scm delete objects hip-object --folder Shared --name windows-compliance

# Bulk operations
scm load objects hip-object --folder Shared --file hip-objects.yml
scm backup objects hip-object --folder Shared
```

##### HIP Profiles

```bash
# Create/update a HIP profile
scm set objects hip-profile --folder Shared --name secure-endpoints \
  --match '{"windows-compliance": {"is": true}}'

# Show HIP profiles
scm show objects hip-profile --folder Shared --list
scm show objects hip-profile --folder Shared --name secure-endpoints

# Delete a HIP profile
scm delete objects hip-profile --folder Shared --name secure-endpoints

# Bulk operations
scm load objects hip-profile --folder Shared --file hip-profiles.yml
scm backup objects hip-profile --folder Shared
```

##### HTTP Server Profiles

```bash
# Create/update an HTTP server profile
scm set objects http-server-profile --folder Shared --name syslog-http \
  --servers '[{"name": "server1", "address": "10.0.1.50", "protocol": "HTTPS", "port": 443, "http_method": "POST"}]'

# Show HTTP server profiles
scm show objects http-server-profile --folder Shared --list
scm show objects http-server-profile --folder Shared --name syslog-http

# Delete an HTTP server profile
scm delete objects http-server-profile --folder Shared --name syslog-http

# Bulk operations
scm load objects http-server-profile --folder Shared --file http-profiles.yml
scm backup objects http-server-profile --folder Shared
```

##### Log Forwarding Profiles

```bash
# Create/update a log forwarding profile
scm set objects log-forwarding-profile --folder Shared --name central-logging \
  --match-list '[{"name": "all-logs", "log_type": "traffic", "filter": "All Logs", "http_profiles": ["syslog-http"]}]'

# Show log forwarding profiles
scm show objects log-forwarding-profile --folder Shared --list
scm show objects log-forwarding-profile --folder Shared --name central-logging

# Delete a log forwarding profile
scm delete objects log-forwarding-profile --folder Shared --name central-logging

# Bulk operations
scm load objects log-forwarding-profile --folder Shared --file log-profiles.yml
scm backup objects log-forwarding-profile --folder Shared
```

##### Services

```bash
# Create/update a service
scm set objects service --folder Shared --name custom-tcp \
  --protocol tcp --port "8080,8443" --description "Custom service"

# Show services
scm show objects service --folder Shared --list
scm show objects service --folder Shared --name custom-tcp

# Delete a service
scm delete objects service --folder Shared --name custom-tcp

# Bulk operations
scm load objects service --folder Shared --file services.yml
scm backup objects service --folder Shared
```

##### Service Groups

```bash
# Create/update a service group
scm set objects service-group --folder Shared --name web-services \
  --members "http,https,ssl"

# Show service groups
scm show objects service-group --folder Shared --list
scm show objects service-group --folder Shared --name web-services

# Delete a service group
scm delete objects service-group --folder Shared --name web-services

# Bulk operations
scm load objects service-group --folder Shared --file service-groups.yml
scm backup objects service-group --folder Shared
```

##### Syslog Server Profiles

```bash
# Create/update a syslog server profile
scm set objects syslog-server-profile --folder Shared --name central-syslog \
  --servers '[{"name": "syslog1", "server": "10.0.1.50", "port": 514, "transport": "TCP", "format": "BSD", "facility": "LOG_USER"}]'

# Show syslog server profiles
scm show objects syslog-server-profile --folder Shared --list
scm show objects syslog-server-profile --folder Shared --name central-syslog

# Delete a syslog server profile
scm delete objects syslog-server-profile --folder Shared --name central-syslog

# Bulk operations
scm load objects syslog-server-profile --folder Shared --file syslog-profiles.yml
scm backup objects syslog-server-profile --folder Shared
```

##### Tags

```bash
# Create/update a tag
scm set objects tag --folder Shared --name production \
  --color "Red" --comments "Production resources"

# Show tags
scm show objects tag --folder Shared --list
scm show objects tag --folder Shared --name production

# Delete a tag
scm delete objects tag --folder Shared --name production

# Bulk operations
scm load objects tag --folder Shared --file tags.yml
scm backup objects tag --folder Shared
```

### network.py

Contains commands for network-related configurations:

```bash
# Security zones
scm set network security-zone --folder Shared --name DMZ --mode layer3
scm show network security-zone --folder Shared --list
scm delete network security-zone --folder Shared --name DMZ
scm load network security-zone --folder Shared --file zones.yml
scm backup network security-zone --folder Shared
```

### security.py

Contains commands for security policy configurations:

```bash
# Security rules
scm set security rule --folder Shared --name "Allow-Web" \
  --source-zones "Trust" --destination-zones "DMZ" \
  --applications "web-browsing,ssl" --action allow

scm show security rule --folder Shared --list --rulebase pre
scm delete security rule --folder Shared --name "Allow-Web" --rulebase pre
scm load security rule --folder Shared --file rules.yml
scm backup security rule --folder Shared --rulebase pre
```

### deployment.py

Contains commands for deployment-related configurations:

```bash
# Bandwidth allocations
scm set deployment bandwidth --folder Shared --name "Branch-100M" \
  --egress-guaranteed 50 --egress-burstable 100

scm show deployment bandwidth --folder Shared --list
scm delete deployment bandwidth --folder Shared --name "Branch-100M"
scm load deployment bandwidth --folder Shared --file bandwidth.yml
scm backup deployment bandwidth --folder Shared
```

## Common Options

All commands support these common options:

- `--folder`: Specify the folder (default: "Shared")
- `--snippet`: Use snippet context instead of folder
- `--device`: Use device context instead of folder
- `--mock`: Run in mock mode without making API calls
- `--list`: List all objects of the specified type
- `--dry-run`: Preview changes without applying them (for load commands)

## Bulk Operations

All object types support bulk operations via YAML files:

1. **Load**: Import multiple objects from a YAML file
2. **Backup**: Export existing objects to a YAML file

Example YAML format:

```yaml
addresses:
  - name: server1
    ip_netmask: 10.0.1.10/32
    description: "Web server 1"
  - name: server2
    ip_netmask: 10.0.1.11/32
    description: "Web server 2"
```

## Error Handling

The CLI provides clear error messages for common issues:

- Authentication failures
- Object not found
- Validation errors
- API errors
- Network connectivity issues

Use the `--mock` flag to test commands without making actual API calls.
