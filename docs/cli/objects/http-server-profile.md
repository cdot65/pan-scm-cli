# HTTP Server Profile Objects

HTTP server profile objects define HTTP/HTTPS servers for log forwarding and integration in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load HTTP server profile objects.

## Overview

The `http-server-profile` commands allow you to:

- Configure multiple HTTP/HTTPS servers for log forwarding
- Set authentication credentials and TLS settings
- Define HTTP methods and port configurations
- Delete HTTP server profiles that are no longer needed
- Bulk import HTTP server profiles from YAML files
- Export HTTP server profiles for backup or migration

## Server Configuration Fields

Each server in the servers JSON array supports these fields:

| Field | Description | Required |
| --- | --- | --- |
| `name` | Unique name for the server | Yes |
| `address` | IP address or hostname | Yes |
| `protocol` | HTTP or HTTPS | Yes |
| `port` | Port number (1-65535) | Yes |
| `http_method` | HTTP method (GET, POST, PUT, DELETE) | Yes |
| `username` | Username for basic authentication | No |
| `password` | Password for basic authentication | No |
| `certificate_profile` | Certificate profile for mutual TLS | No |
| `tls_version` | TLS version for HTTPS (1.0, 1.1, 1.2, 1.3) | No |

## Set HTTP Server Profile

Create or update an HTTP server profile object.

### Syntax

```bash
scm set object http-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder for the HTTP server profile object | No\* |
| `--snippet TEXT` | Snippet for the HTTP server profile object | No\* |
| `--device TEXT` | Device for the HTTP server profile object | No\* |
| `--name TEXT` | Name of the HTTP server profile | Yes |
| `--servers JSON` | JSON array of server configurations | Yes |
| `--description TEXT` | Description of the profile | No |
| `--tag-registration` | Enable tag registration on match | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create Basic HTTP Server Profile

```bash
$ scm set object http-server-profile \
    --folder Texas \
    --name syslog-http \
    --servers '[{"name": "primary", "address": "10.0.1.50", "protocol": "HTTP", "port": 8080, "http_method": "POST"}]' \
    --description "HTTP syslog forwarder"
---> 100%
Created HTTP server profile: syslog-http in folder Texas
```

#### Create HTTPS Profile with Authentication

```bash
$ scm set object http-server-profile \
    --folder Texas \
    --name splunk-hec \
    --servers '[{"name": "splunk", "address": "splunk.company.com", "protocol": "HTTPS", "port": 8088, "http_method": "POST", "username": "hec_user", "password": "hec_token", "tls_version": "1.2"}]' \
    --description "Splunk HTTP Event Collector"
---> 100%
Created HTTP server profile: splunk-hec in folder Texas
```

#### Create Multi-Server Profile for Redundancy

```bash
$ scm set object http-server-profile \
    --folder Texas \
    --name siem-collectors \
    --servers '[{"name": "primary", "address": "siem1.company.com", "protocol": "HTTPS", "port": 443, "http_method": "POST"}, {"name": "secondary", "address": "siem2.company.com", "protocol": "HTTPS", "port": 443, "http_method": "POST"}]' \
    --tag-registration \
    --description "SIEM collector endpoints"
---> 100%
Created HTTP server profile: siem-collectors in folder Texas
```

## Delete HTTP Server Profile

Delete an HTTP server profile object from SCM.

### Syntax

```bash
scm delete object http-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the HTTP server profile object | No\* |
| `--snippet TEXT` | Snippet containing the HTTP server profile object | No\* |
| `--device TEXT` | Device containing the HTTP server profile object | No\* |
| `--name TEXT` | Name of the HTTP server profile object to delete | Yes |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete object http-server-profile --folder Texas --name syslog-http
---> 100%
Deleted HTTP server profile: syslog-http from folder Texas
```

## Load HTTP Server Profiles

Load multiple HTTP server profile objects from a YAML file.

### Syntax

```bash
scm load object http-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing HTTP server profile definitions | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
http_server_profiles:
  - name: splunk-hec
    folder: Texas
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
$ scm load object http-server-profile --file http-profiles.yml
---> 100%
✓ Loaded HTTP server profile: splunk-hec
✓ Loaded HTTP server profile: elastic-logs
✓ Loaded HTTP server profile: syslog-http

Successfully loaded 3 out of 3 HTTP server profiles from 'http-profiles.yml'
```

#### Load with Folder Override

```bash
$ scm load object http-server-profile --file http-profiles.yml --folder Austin
---> 100%
✓ Loaded HTTP server profile: splunk-hec
✓ Loaded HTTP server profile: elastic-logs
✓ Loaded HTTP server profile: syslog-http

Successfully loaded 3 out of 3 HTTP server profiles from 'http-profiles.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all HTTP server
    profiles will be loaded into the specified container, ignoring the container specified
    in the YAML file.

## Show HTTP Server Profile

Display HTTP server profile objects.

### Syntax

```bash
scm show object http-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the HTTP server profile object | No\* |
| `--snippet TEXT` | Snippet containing the HTTP server profile object | No\* |
| `--device TEXT` | Device containing the HTTP server profile object | No\* |
| `--name TEXT` | Name of the HTTP server profile object to show | No |

!!! note
    When no `--name` is specified, all items are listed by default.

\* One of --folder, --snippet, or --device is required.

### Examples

#### Show Specific HTTP Server Profile

```bash
$ scm show object http-server-profile --folder Texas --name splunk-hec
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
$ scm show object http-server-profile --folder Texas
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
scm backup object http-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup HTTP server profiles from | No\* |
| `--snippet TEXT` | Snippet to backup HTTP server profiles from | No\* |
| `--device TEXT` | Device to backup HTTP server profiles from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup object http-server-profile --folder Texas
---> 100%
Successfully backed up 6 HTTP server profiles to http-server-profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object http-server-profile --folder Texas --file texas-http-profiles.yaml
---> 100%
Successfully backed up 6 HTTP server profiles to texas-http-profiles.yaml
```

## Best Practices

1. **Use HTTPS**: Always use HTTPS for production environments.
2. **Authentication**: Implement proper authentication for all server connections.
3. **Redundancy**: Configure multiple servers for high availability.
4. **TLS Versions**: Use TLS 1.2 or higher for security.
5. **Port Selection**: Use standard ports when possible (443 for HTTPS, 8080 for HTTP).
6. **Use YAML for Bulk Operations**: For complex deployments, use YAML files.
7. **Organize by Container**: Keep profiles organized in appropriate folders, snippets, or devices.
