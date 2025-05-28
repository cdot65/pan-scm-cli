# Service Management

This section covers the commands for managing service objects in Strata Cloud Manager.

## Overview

Service objects define network services by protocol and port combinations. The `service` commands allow you to:

- Create custom service definitions
- Define TCP and UDP port configurations
- Set timeout values for connection handling
- Manage service descriptions and tags
- Group services for policy use

## Commands

### Creating/Updating Services

Basic TCP service:

```bash
$ scm set objects service --folder Texas --name custom-web \
  --protocol tcp --port "8080,8443" \
  --description "Custom web service ports"
<span style="color: green;">✓</span> Service 'custom-web' created successfully
```

UDP service with port range:

```bash
$ scm set objects service --folder Texas --name custom-voip \
  --protocol udp --port "5060-5070" \
  --description "VoIP signaling ports"
<span style="color: green;">✓</span> Service 'custom-voip' created successfully
```

TCP service with timeout overrides:

```bash
$ scm set objects service --folder Texas --name database-service \
  --protocol tcp --port "3306" \
  --timeout 7200 --halfclose-timeout 120 --timewait-timeout 30 \
  --description "MySQL with extended timeouts"
<span style="color: green;">✓</span> Service 'database-service' created successfully
```

### Listing Services

```bash
$ scm show objects service --folder Texas --list
Services in folder 'Texas':
- custom-web
- custom-voip
- database-service
- legacy-app
```

### Showing Service Details

```bash
$ scm show objects service --folder Texas --name custom-web
Service: custom-web
  Protocol: tcp
  Ports: 8080,8443
  Description: Custom web service ports
  Tags: None
  Folder: Texas
```

### Deleting Services

```bash
$ scm delete objects service --folder Texas --name custom-web
<span style="color: green;">✓</span> Service 'custom-web' deleted successfully
```

### Load Services

Load multiple services from a YAML file.

#### Syntax

```bash
scm load objects service [OPTIONS]
```

#### Options

| Option           | Description                                      | Required |
| ---------------- | ------------------------------------------------ | -------- |
| `--file TEXT`    | Path to YAML file containing service definitions | Yes      |
| `--folder TEXT`  | Override folder location for all objects         | No       |
| `--snippet TEXT` | Override snippet location for all objects        | No       |
| `--device TEXT`  | Override device location for all objects         | No       |
| `--dry-run`      | Preview changes without applying them            | No       |

#### Examples

Load from file with original locations:

```bash
$ scm load objects service --file services.yml
<span style="color: green;">✓</span> Loaded service: custom-web
<span style="color: green;">✓</span> Loaded service: database-cluster
<span style="color: green;">✓</span> Loaded service: custom-dns
<span style="color: green;">✓</span> Loaded service: legacy-app

Successfully loaded 4 out of 4 services from 'services.yml'
```

Load with folder override:

```bash
$ scm load objects service --file services.yml --folder Austin
<span style="color: green;">✓</span> Loaded service: custom-web
<span style="color: green;">✓</span> Loaded service: database-cluster
<span style="color: green;">✓</span> Loaded service: custom-dns
<span style="color: green;">✓</span> Loaded service: legacy-app

Successfully loaded 4 out of 4 services from 'services.yml'
```

!!! note
When using container override options (--folder, --snippet, --device), all services will be loaded into the specified container, ignoring the container specified in the YAML file.

### Backup Services

Backup all service objects from a specified location to a YAML file.

#### Syntax

```bash
scm backup objects service [OPTIONS]
```

#### Options

| Option           | Description                                  | Required |
| ---------------- | -------------------------------------------- | -------- |
| `--folder TEXT`  | Folder to backup services from               | No\*     |
| `--snippet TEXT` | Snippet to backup services from              | No\*     |
| `--device TEXT`  | Device to backup services from               | No\*     |
| `--file TEXT`    | Output filename (defaults to auto-generated) | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

#### Examples

Backup from folder:

```bash
$ scm backup objects service --folder Texas
<span style="color: green;">✓</span> Successfully backed up 15 services to service_folder_texas_20240115_120530.yaml
```

Backup with custom filename:

```bash
$ scm backup objects service --folder Texas --file texas-services.yaml
<span style="color: green;">✓</span> Successfully backed up 15 services to texas-services.yaml
```

## YAML Configuration Format

Services can be defined in YAML for bulk operations:

```yaml
services:
  - name: custom-web
    folder: Texas # Container location (folder, snippet, or device)
    protocol: tcp
    port: "8080,8443"
    description: "Custom web service ports"

  - name: database-cluster
    folder: Texas
    protocol: tcp
    port: "3306-3310"
    description: "MySQL cluster ports"
    override:
      timeout: 7200
      halfclose_timeout: 120
      timewait_timeout: 30

  - name: custom-dns
    folder: Texas
    protocol: udp
    port: "5353"
    description: "mDNS/Bonjour service"
    tag:
      - network
      - discovery

  - name: legacy-app
    folder: Texas
    protocol: tcp
    port: "9000,9001,9002"
    description: "Legacy application ports"
    tag:
      - legacy
      - monitor
```

## Configuration Options

### Required Parameters

- `--name`: Name of the service
- `--protocol`: Protocol type (tcp or udp)
- `--port`: Port specification (single, range, or comma-separated)

### Optional Parameters

- `--description`: Detailed description
- `--tag`: Tags for categorization (comma-separated)

### TCP-Only Optional Parameters

- `--timeout`: Session timeout in seconds
- `--halfclose-timeout`: TCP half-close timeout
- `--timewait-timeout`: TCP time-wait timeout

### Context Parameters

Exactly one context parameter must be specified:

- `--folder`: Folder name (e.g., "Texas", "Shared")
- `--snippet`: Snippet name for Panorama
- `--device`: Device name for NGFW

## Port Specification Formats

### Single Port

```bash
--port "8080"
```

### Port Range

```bash
--port "8000-8100"
```

### Multiple Ports

```bash
--port "80,443,8080,8443"
```

### Mixed Format

```bash
--port "80,443,8000-8100"
```

## Examples

### Create a Basic TCP Service

```bash
scm set objects service --folder Shared --name web-app \
  --protocol tcp --port "8080"
```

### Create a UDP Service Range

```bash
scm set objects service --folder Shared --name voip-rtp \
  --protocol udp --port "10000-20000" \
  --description "RTP media ports for VoIP"
```

### Create a Service with Extended Timeouts

```bash
scm set objects service --folder Shared --name long-running-job \
  --protocol tcp --port "9999" \
  --timeout 14400 \
  --description "Service for long-running batch jobs (4 hour timeout)"
```

### Create a Tagged Service

```bash
scm set objects service --folder Shared --name critical-db \
  --protocol tcp --port "5432" \
  --tag "critical,database,postgresql" \
  --description "PostgreSQL database service"
```

## Best Practices

1. **Descriptive Names**: Use names that clearly identify the service purpose

2. **Port Documentation**: Always include descriptions explaining port usage

3. **Timeout Considerations**: Only override timeouts when necessary for application requirements

4. **Tag Organization**: Use consistent tags for easier filtering and management

5. **Port Range Efficiency**: Use ranges instead of listing sequential ports

## Integration with Security Policies

Services are used in security rules to control traffic:

```bash
# Allow custom web service
scm set security rule --folder Shared --name "Allow-Custom-Web" \
  --source-zones "Trust" --destination-zones "DMZ" \
  --services "custom-web" --action allow

# Use service in NAT rule
scm set security nat --folder Shared --name "Web-NAT" \
  --source-zones "Internet" --destination-zones "DMZ" \
  --services "custom-web" --translated-port 80
```

## Notes

- Service names must be unique within a folder
- Valid port ranges are 1-65535
- Timeout values are in seconds
- Timeout overrides only apply to TCP services
- Tags must exist before being referenced
- Services can be grouped using service groups
- Some built-in services cannot be modified
