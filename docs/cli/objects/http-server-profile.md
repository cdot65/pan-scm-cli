# HTTP Server Profile Management

This section covers the commands for managing HTTP server profiles in Strata Cloud Manager.

## Overview

HTTP server profiles define HTTP/HTTPS servers for log forwarding and integration. The `http-server-profile` commands allow you to:

- Configure multiple HTTP/HTTPS servers
- Set authentication credentials
- Define TLS settings for secure connections
- Configure HTTP methods and ports
- Enable tag registration on match
- Customize log format settings

## Commands

### Creating/Updating HTTP Server Profiles

Basic HTTP server profile:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects http-server-profile --folder Texas --name syslog-http \
  --servers '[{"name": "primary", "address": "10.0.1.50", "protocol": "HTTP", "port": 8080, "http_method": "POST"}]' \
  --description "HTTP syslog forwarder"
<span style="color: green;">✓</span> HTTP server profile 'syslog-http' created successfully
```

</div>

HTTPS with authentication:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects http-server-profile --folder Texas --name splunk-hec \
  --servers '[{"name": "splunk", "address": "splunk.company.com", "protocol": "HTTPS", "port": 8088, "http_method": "POST", "username": "hec_user", "password": "hec_token", "tls_version": "1.2"}]' \
  --description "Splunk HTTP Event Collector"
<span style="color: green;">✓</span> HTTP server profile 'splunk-hec' created successfully
```

</div>

Multiple servers for redundancy:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects http-server-profile --folder Texas --name siem-collectors \
  --servers '[{"name": "primary", "address": "siem1.company.com", "protocol": "HTTPS", "port": 443, "http_method": "POST"}, {"name": "secondary", "address": "siem2.company.com", "protocol": "HTTPS", "port": 443, "http_method": "POST"}]' \
  --tag-registration \
  --description "SIEM collector endpoints"
<span style="color: green;">✓</span> HTTP server profile 'siem-collectors' created successfully
```

</div>

### Listing HTTP Server Profiles

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects http-server-profile --folder Texas --list
HTTP server profiles in folder 'Texas':
- syslog-http
- splunk-hec
- siem-collectors
- elastic-endpoint
```

</div>

### Showing HTTP Server Profile Details

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects http-server-profile --folder Texas --name splunk-hec
HTTP Server Profile: splunk-hec
  Servers:
    - Name: splunk
      Address: splunk.company.com
      Protocol: HTTPS
      Port: 8088
      HTTP Method: POST
      TLS Version: 1.2
  Description: Splunk HTTP Event Collector
  Tag Registration: False
  Folder: Texas
```

</div>

### Deleting HTTP Server Profiles

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli delete objects http-server-profile --folder Texas --name syslog-http
<span style="color: green;">✓</span> HTTP server profile 'syslog-http' deleted successfully
```

</div>

### Bulk Operations

Load multiple HTTP server profiles from a YAML file:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli load objects http-server-profile --folder Texas --file http-profiles.yml
<span style="color: green;">✓</span> Loaded 6 HTTP server profiles successfully
```

</div>

Backup existing HTTP server profiles:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli backup objects http-server-profile --folder Texas
<span style="color: green;">✓</span> Backed up 6 HTTP server profiles to http-server-profile-texas.yaml
```

</div>

## YAML Configuration Format

HTTP server profiles can be defined in YAML for bulk operations:

```yaml
http_server_profiles:
  - name: splunk-hec
    description: "Splunk HTTP Event Collector"
    servers:
      - name: splunk-primary
        address: splunk1.company.com
        protocol: HTTPS
        port: 8088
        http_method: POST
        username: hec_user
        password: secure_token
        tls_version: "1.2"
    
  - name: elastic-logs
    description: "Elasticsearch log ingestion"
    servers:
      - name: elastic-node1
        address: 10.0.2.10
        protocol: HTTPS
        port: 9200
        http_method: POST
        username: elastic
        password: changeme
        tls_version: "1.3"
      - name: elastic-node2
        address: 10.0.2.11
        protocol: HTTPS
        port: 9200
        http_method: POST
        username: elastic
        password: changeme
        tls_version: "1.3"
    
  - name: syslog-http
    description: "HTTP syslog receiver"
    servers:
      - name: syslog-receiver
        address: syslog.internal.com
        protocol: HTTP
        port: 514
        http_method: POST
    
  - name: webhook-endpoint
    description: "Webhook notification service"
    servers:
      - name: webhook
        address: hooks.company.com
        protocol: HTTPS
        port: 443
        http_method: POST
        certificate_profile: webhook-cert
    tag_registration: true
    
  - name: siem-integration
    description: "SIEM platform integration"
    servers:
      - name: siem-primary
        address: siem.company.com
        protocol: HTTPS
        port: 8443
        http_method: PUT
        username: api_user
        password: api_key
        tls_version: "1.2"
    format:
      traffic:
        payload: custom
      threat:
        payload: custom
```

## Configuration Options

### Required Parameters

- `--name`: Name of the HTTP server profile
- `--servers`: JSON array of server configurations

### Optional Parameters

- `--description`: Detailed description
- `--tag-registration`: Enable tag registration on match
- `--format-config`: Custom format settings for log types

### Server Configuration Fields

Each server in the servers array requires:

- `name`: Unique name for the server
- `address`: IP address or hostname
- `protocol`: HTTP or HTTPS
- `port`: Port number (1-65535)
- `http_method`: HTTP method (GET, POST, PUT, DELETE)

Optional server fields:

- `username`: Username for basic authentication
- `password`: Password for basic authentication
- `certificate_profile`: Certificate profile for mutual TLS
- `tls_version`: TLS version for HTTPS (1.0, 1.1, 1.2, 1.3)

### Context Parameters

Exactly one context parameter must be specified:

- `--folder`: Folder name (e.g., "Texas", "Shared")
- `--snippet`: Snippet name for Panorama
- `--device`: Device name for NGFW

## Examples

### Basic HTTP Server

```bash
scm-cli set objects http-server-profile --folder Shared --name simple-http \
  --servers '[{"name": "server1", "address": "192.168.1.100", "protocol": "HTTP", "port": 8080, "http_method": "POST"}]' \
  --description "Basic HTTP logging"
```

### Secure HTTPS with Authentication

```bash
scm-cli set objects http-server-profile --folder Shared --name secure-logging \
  --servers '[{
    "name": "secure-server",
    "address": "logs.company.com",
    "protocol": "HTTPS",
    "port": 443,
    "http_method": "POST",
    "username": "log_user",
    "password": "secure_pass",
    "tls_version": "1.3"
  }]' \
  --description "Secure HTTPS logging with auth"
```

### Multiple Servers for High Availability

```bash
scm-cli set objects http-server-profile --folder Shared --name ha-logging \
  --servers '[
    {"name": "primary", "address": "log1.company.com", "protocol": "HTTPS", "port": 443, "http_method": "POST"},
    {"name": "secondary", "address": "log2.company.com", "protocol": "HTTPS", "port": 443, "http_method": "POST"},
    {"name": "tertiary", "address": "log3.company.com", "protocol": "HTTPS", "port": 443, "http_method": "POST"}
  ]' \
  --description "High availability logging cluster"
```

### Splunk Integration

```bash
scm-cli set objects http-server-profile --folder Shared --name splunk-integration \
  --servers '[{
    "name": "splunk-hec",
    "address": "splunk-hec.company.com",
    "protocol": "HTTPS",
    "port": 8088,
    "http_method": "POST",
    "username": "x-splunk-token",
    "password": "your-hec-token-here",
    "tls_version": "1.2"
  }]' \
  --tag-registration \
  --description "Splunk HTTP Event Collector"
```

### Certificate-Based Authentication

```bash
scm-cli set objects http-server-profile --folder Shared --name cert-auth \
  --servers '[{
    "name": "mtls-server",
    "address": "secure-logs.company.com",
    "protocol": "HTTPS",
    "port": 8443,
    "http_method": "POST",
    "certificate_profile": "client-cert-profile",
    "tls_version": "1.3"
  }]' \
  --description "Mutual TLS authentication"
```

## Integration with Log Forwarding

HTTP server profiles are referenced in log forwarding profiles:

```bash
# Create log forwarding profile using HTTP servers
scm-cli set objects log-forwarding-profile --folder Shared --name forward-to-http \
  --match-list '[{
    "name": "all-logs",
    "log_type": "traffic",
    "filter": "All Logs",
    "http_profiles": ["splunk-hec", "siem-integration"]
  }]'
```

## Server Selection and Load Balancing

When multiple servers are configured:

1. **Primary/Secondary**: Servers are used in order of configuration
2. **Failover**: If primary fails, secondary is used
3. **Health Checks**: Automatic health monitoring
4. **Recovery**: Automatic return to primary when available

## Best Practices

1. **Use HTTPS**: Always use HTTPS for production environments
   ```bash
   "protocol": "HTTPS", "tls_version": "1.2"
   ```

2. **Authentication**: Implement proper authentication
   - Basic auth for simple setups
   - Certificate auth for high security

3. **Port Selection**: Use standard ports when possible
   - HTTP: 80, 8080
   - HTTPS: 443, 8443

4. **Redundancy**: Configure multiple servers for high availability

5. **TLS Versions**: Use TLS 1.2 or higher for security

## Common Integrations

### SIEM Platforms
- Splunk HTTP Event Collector
- Elasticsearch
- IBM QRadar
- ArcSight

### Log Management
- ELK Stack
- Graylog
- Sumo Logic
- Datadog

### Custom Applications
- Webhook endpoints
- Custom REST APIs
- Internal logging systems

## Troubleshooting

### Connection Issues

1. **Network Connectivity**: Verify firewall can reach HTTP servers
2. **Port Access**: Ensure ports are open and accessible
3. **DNS Resolution**: Verify hostnames resolve correctly
4. **TLS Compatibility**: Check TLS version compatibility

### Authentication Failures

1. **Credentials**: Verify username/password
2. **Certificate**: Check certificate validity and trust
3. **Token Format**: Ensure proper token formatting for services like Splunk

## Notes

- Profile names must be unique within a folder
- At least one server must be configured
- HTTP method is required for all servers
- HTTPS is recommended for production use
- Authentication credentials are encrypted in configuration
- Certificate profiles must exist before referencing
- Profiles are used by log forwarding profiles
- Maximum number of servers per profile may be limited by platform