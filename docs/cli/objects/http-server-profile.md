# HTTP Server Profile Objects

HTTP server profile objects define HTTP/HTTPS servers for log forwarding and integration in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load HTTP server profile objects.

## Overview

HTTP server profiles allow you to:

- Configure multiple HTTP/HTTPS servers
- Set authentication credentials
- Define TLS settings for secure connections
- Configure HTTP methods and ports
- Enable tag registration on match
- Customize log format settings

## Set HTTP Server Profile

Create or update an HTTP server profile object.

### Syntax

```bash
scm set objects http-server-profile [OPTIONS]
```

### Options

| Option               | Description                                | Required |
| -------------------- | ------------------------------------------ | -------- |
| `--folder TEXT`      | Folder for the HTTP server profile object  | Yes\*    |
| `--snippet TEXT`     | Snippet for the HTTP server profile object | Yes\*    |
| `--device TEXT`      | Device for the HTTP server profile object  | Yes\*    |
| `--name TEXT`        | Name of the HTTP server profile            | Yes      |
| `--servers JSON`     | JSON array of server configurations        | Yes      |
| `--description TEXT` | Description of the profile                 | No       |
| `--tag-registration` | Enable tag registration on match           | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

### Examples

#### Create Basic HTTP Server Profile

```bash
$ scm set objects http-server-profile \
    --folder Texas \
    --name syslog-http \
    --servers '[{"name": "primary", "address": "10.0.1.50", "protocol": "HTTP", "port": 8080, "http_method": "POST"}]' \
    --description "HTTP syslog forwarder"
---> 100%
Created HTTP server profile: syslog-http in folder Texas
```

#### Create HTTPS Profile with Authentication

```bash
$ scm set objects http-server-profile \
    --folder Texas \
    --name splunk-hec \
    --servers '[{"name": "splunk", "address": "splunk.company.com", "protocol": "HTTPS", "port": 8088, "http_method": "POST", "username": "hec_user", "password": "hec_token", "tls_version": "1.2"}]' \
    --description "Splunk HTTP Event Collector"
---> 100%
Created HTTP server profile: splunk-hec in folder Texas
```

## Delete HTTP Server Profile

Delete an HTTP server profile object from SCM.

### Syntax

```bash
scm delete objects http-server-profile [OPTIONS]
```

### Options

| Option           | Description                                       | Required |
| ---------------- | ------------------------------------------------- | -------- |
| `--folder TEXT`  | Folder containing the HTTP server profile object  | Yes\*    |
| `--snippet TEXT` | Snippet containing the HTTP server profile object | Yes\*    |
| `--device TEXT`  | Device containing the HTTP server profile object  | Yes\*    |
| `--name TEXT`    | Name of the HTTP server profile object to delete  | Yes      |

\* You must specify exactly one of --folder, --snippet, or --device.

### Example

```bash
$ scm delete objects http-server-profile --folder Texas --name syslog-http
---> 100%
Deleted HTTP server profile: syslog-http from folder Texas
```

## Load HTTP Server Profiles

Load multiple HTTP server profile objects from a YAML file.

### Syntax

```bash
scm load objects http-server-profile [OPTIONS]
```

### Options

| Option           | Description                                                  | Required |
| ---------------- | ------------------------------------------------------------ | -------- |
| `--file TEXT`    | Path to YAML file containing HTTP server profile definitions | Yes      |
| `--folder TEXT`  | Override folder location for all objects                     | No       |
| `--snippet TEXT` | Override snippet location for all objects                    | No       |
| `--device TEXT`  | Override device location for all objects                     | No       |
| `--dry-run`      | Preview changes without applying them                        | No       |

### YAML File Format

```yaml
---
http_server_profiles:
  - name: splunk-hec
    folder: Texas # Container location (folder, snippet, or device)
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
    folder: Texas
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
    folder: Texas
    description: "HTTP syslog receiver"
    servers:
      - name: syslog-receiver
        address: syslog.internal.com
        protocol: HTTP
        port: 514
        http_method: POST
```

### Examples

#### Load with Original Locations

```bash
$ scm load objects http-server-profile --file http-profiles.yml
---> 100%
✓ Loaded HTTP server profile: splunk-hec
✓ Loaded HTTP server profile: elastic-logs
✓ Loaded HTTP server profile: syslog-http

Successfully loaded 3 out of 3 HTTP server profiles from 'http-profiles.yml'
```

#### Load with Folder Override

```bash
$ scm load objects http-server-profile --file http-profiles.yml --folder Austin
---> 100%
✓ Loaded HTTP server profile: splunk-hec
✓ Loaded HTTP server profile: elastic-logs
✓ Loaded HTTP server profile: syslog-http

Successfully loaded 3 out of 3 HTTP server profiles from 'http-profiles.yml'
```

!!! note
When using container override options (--folder, --snippet, --device), all HTTP server profiles will be loaded into the specified container, ignoring the container specified in the YAML file.

## Show HTTP Server Profile

Display HTTP server profile objects.

### Syntax

```bash
scm show objects http-server-profile [OPTIONS]
```

### Options

| Option           | Description                                       | Required |
| ---------------- | ------------------------------------------------- | -------- |
| `--folder TEXT`  | Folder containing the HTTP server profile object  | Yes\*    |
| `--snippet TEXT` | Snippet containing the HTTP server profile object | Yes\*    |
| `--device TEXT`  | Device containing the HTTP server profile object  | Yes\*    |
| `--name TEXT`    | Name of the HTTP server profile object to show    | No\*\*   |
| `--list`         | List all HTTP server profiles in the container    | No\*\*   |

\* You must specify exactly one of --folder, --snippet, or --device.
\*\* If --name is not specified, all items will be listed.

### Examples

#### Show Specific HTTP Server Profile

```bash
$ scm show objects http-server-profile --folder Texas --name splunk-hec
---> 100%
HTTP Server Profile: splunk-hec
Location: Folder 'Texas'
Servers:
  - Name: splunk
    Address: splunk.company.com
    Protocol: HTTPS
    Port: 8088
    HTTP Method: POST
    TLS Version: 1.2
Description: Splunk HTTP Event Collector
Tag Registration: False
ID: 123e4567-e89b-12d3-a456-426614174000
```

#### List All HTTP Server Profiles (Default Behavior)

```bash
$ scm show objects http-server-profile --folder Texas
---> 100%
HTTP Server Profiles in folder 'Texas':
------------------------------------------------------------
Name: syslog-http
  Location: Folder 'Texas'
  Server: primary (10.0.1.50:8080 HTTP)
  Description: HTTP syslog forwarder
------------------------------------------------------------
Name: splunk-hec
  Location: Folder 'Texas'
  Server: splunk (splunk.company.com:8088 HTTPS)
  Description: Splunk HTTP Event Collector
------------------------------------------------------------
Name: siem-collectors
  Location: Folder 'Texas'
  Servers: primary (siem1.company.com:443 HTTPS), secondary (siem2.company.com:443 HTTPS)
  Tag Registration: Yes
  Description: SIEM collector endpoints
------------------------------------------------------------
```

## Backup HTTP Server Profiles

Backup all HTTP server profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup objects http-server-profile [OPTIONS]
```

### Options

| Option           | Description                                  | Required |
| ---------------- | -------------------------------------------- | -------- |
| `--folder TEXT`  | Folder to backup HTTP server profiles from   | No\*     |
| `--snippet TEXT` | Snippet to backup HTTP server profiles from  | No\*     |
| `--device TEXT`  | Device to backup HTTP server profiles from   | No\*     |
| `--file TEXT`    | Output filename (defaults to auto-generated) | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

### Examples

#### Backup from Folder

```bash
$ scm backup objects http-server-profile --folder Texas
---> 100%
Successfully backed up 6 HTTP server profiles to http-server-profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup objects http-server-profile --folder Texas --file texas-http-profiles.yaml
---> 100%
Successfully backed up 6 HTTP server profiles to texas-http-profiles.yaml
```

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

````

## Configuration Options

### Required Parameters

- `--name`: Name of the HTTP server profile
- `--servers`: JSON array of server configurations

### Optional Parameters

- `--description`: Detailed description
- `--tag-registration`: Enable tag registration on match

## Best Practices

1. **Use HTTPS**: Always use HTTPS for production environments

2. **Authentication**: Implement proper authentication

   - Basic auth for simple setups
   - Certificate auth for high security

3. **Port Selection**: Use standard ports when possible

   - HTTP: 80, 8080
   - HTTPS: 443, 8443

4. **Redundancy**: Configure multiple servers for high availability

5. **TLS Versions**: Use TLS 1.2 or higher for security

6. **Use YAML for Bulk Operations**: For complex deployments, use YAML files

7. **Organize by Container**: Keep profiles organized in appropriate folders, snippets, or devices

## Additional Examples

### Multiple Servers for Redundancy

```bash
$ scm set objects http-server-profile \
    --folder Texas \
    --name siem-collectors \
    --servers '[{"name": "primary", "address": "siem1.company.com", "protocol": "HTTPS", "port": 443, "http_method": "POST"}, {"name": "secondary", "address": "siem2.company.com", "protocol": "HTTPS", "port": 443, "http_method": "POST"}]' \
    --tag-registration \
    --description "SIEM collector endpoints"
---> 100%
Created HTTP server profile: siem-collectors in folder Texas
````

### Splunk Integration

```bash
$ scm set objects http-server-profile \
    --folder Shared \
    --name splunk-integration \
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
---> 100%
Created HTTP server profile: splunk-integration in folder Shared
```

### Certificate-Based Authentication

```bash
$ scm set objects http-server-profile \
    --folder Shared \
    --name cert-auth \
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
---> 100%
Created HTTP server profile: cert-auth in folder Shared
```

## Integration with Log Forwarding

HTTP server profiles are referenced in log forwarding profiles:

```bash
$ scm set objects log-forwarding-profile \
    --folder Shared \
    --name forward-to-http \
    --match-list '[{
      "name": "all-logs",
      "log_type": "traffic",
      "filter": "All Logs",
      "http_profiles": ["splunk-hec", "siem-integration"]
    }]'
---> 100%
Created log forwarding profile: forward-to-http in folder Shared
```

## Server Configuration Fields

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

## Notes

- Profile names must be unique within a container
- At least one server must be configured
- HTTP method is required for all servers
- HTTPS is recommended for production use
- Authentication credentials are encrypted in configuration
- Certificate profiles must exist before referencing
- Profiles are used by log forwarding profiles
- Maximum number of servers per profile may be limited by platform
- When multiple servers are configured, they are used in order with automatic failover
