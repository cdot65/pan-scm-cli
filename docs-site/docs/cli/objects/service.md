# Service Objects

Service objects define network services by protocol and port combinations in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load service objects.

## Overview

The `service` commands allow you to:

- Create custom service definitions with TCP or UDP protocols
- Define port configurations (single, range, or comma-separated)
- Set timeout values for connection handling
- Delete services that are no longer needed
- Bulk import services from YAML files
- Export services for backup or migration

## Port Specification Formats

| Format | Example | Description |
| --- | --- | --- |
| Single port | `8080` | One specific port |
| Port range | `8000-8100` | All ports in the range |
| Multiple ports | `80,443,8080` | Specific listed ports |
| Mixed | `80,443,8000-8100` | Combination of formats |

## Set Service

Create or update a service object.

### Syntax

```bash
scm set object service [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder for the service object | No\* |
| `--snippet TEXT` | Snippet for the service object | No\* |
| `--device TEXT` | Device for the service object | No\* |
| `--name TEXT` | Name of the service | Yes |
| `--protocol TEXT` | Protocol type (tcp or udp) | Yes |
| `--port TEXT` | Port specification | Yes |
| `--description TEXT` | Description of the service | No |
| `--tag TEXT` | Tags for categorization (comma-separated) | No |
| `--timeout INT` | Session timeout in seconds (TCP only) | No |
| `--halfclose-timeout INT` | TCP half-close timeout | No |
| `--timewait-timeout INT` | TCP time-wait timeout | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create a Basic TCP Service

```bash
$ scm set object service \
    --folder Texas \
    --name custom-web \
    --protocol tcp \
    --port "8080,8443" \
    --description "Custom web service ports"
---> 100%
Created service: custom-web in folder Texas
```

#### Create a UDP Service with Port Range

```bash
$ scm set object service \
    --folder Texas \
    --name custom-voip \
    --protocol udp \
    --port "5060-5070" \
    --description "VoIP signaling ports"
---> 100%
Created service: custom-voip in folder Texas
```

#### Create a TCP Service with Timeout Overrides

```bash
$ scm set object service \
    --folder Texas \
    --name database-service \
    --protocol tcp \
    --port "3306" \
    --timeout 7200 \
    --halfclose-timeout 120 \
    --timewait-timeout 30 \
    --description "MySQL with extended timeouts"
---> 100%
Created service: database-service in folder Texas
```

## Delete Service

Delete a service object from SCM.

### Syntax

```bash
scm delete object service [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the service object | No\* |
| `--snippet TEXT` | Snippet containing the service object | No\* |
| `--device TEXT` | Device containing the service object | No\* |
| `--name TEXT` | Name of the service to delete | Yes |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete object service --folder Texas --name custom-web --force
---> 100%
Deleted service: custom-web from folder Texas
```

## Load Services

Load multiple service objects from a YAML file.

### Syntax

```bash
scm load object service [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing service definitions | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
services:
  - name: custom-web
    folder: Texas
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

### Examples

#### Load with Original Locations

```bash
$ scm load object service --file services.yml
---> 100%
✓ Loaded service: custom-web
✓ Loaded service: database-cluster
✓ Loaded service: custom-dns
✓ Loaded service: legacy-app

Successfully loaded 4 out of 4 services from 'services.yml'
```

#### Load with Folder Override

```bash
$ scm load object service --file services.yml --folder Austin
---> 100%
✓ Loaded service: custom-web
✓ Loaded service: database-cluster
✓ Loaded service: custom-dns
✓ Loaded service: legacy-app

Successfully loaded 4 out of 4 services from 'services.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all services
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show Service

Display service objects.

### Syntax

```bash
scm show object service [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the service object | No\* |
| `--snippet TEXT` | Snippet containing the service object | No\* |
| `--device TEXT` | Device containing the service object | No\* |
| `--name TEXT` | Name of the service to show | No |

:::note
When no `--name` is specified, all items are listed by default.
:::

\* One of --folder, --snippet, or --device is required.

### Examples

#### Show Specific Service

```bash
$ scm show object service --folder Texas --name custom-web
---> 100%
Service: custom-web
  Location: Folder 'Texas'
  Protocol: tcp
  Ports: 8080,8443
  Description: Custom web service ports
  Tags: None
```

#### List All Services (Default Behavior)

```bash
$ scm show object service --folder Texas
---> 100%
Services in folder 'Texas':
------------------------------------------------------------
Name: custom-web
  Protocol: tcp
  Ports: 8080,8443
  Description: Custom web service ports
------------------------------------------------------------
Name: custom-voip
  Protocol: udp
  Ports: 5060-5070
  Description: VoIP signaling ports
------------------------------------------------------------
Name: database-service
  Protocol: tcp
  Ports: 3306
  Timeout: 7200s
  Description: MySQL with extended timeouts
------------------------------------------------------------
```

## Backup Services

Backup all service objects from a specified location to a YAML file.

### Syntax

```bash
scm backup object service [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup services from | No\* |
| `--snippet TEXT` | Snippet to backup services from | No\* |
| `--device TEXT` | Device to backup services from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup object service --folder Texas
---> 100%
Successfully backed up 15 services to service_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object service --folder Texas --file texas-services.yaml
---> 100%
Successfully backed up 15 services to texas-services.yaml
```

## Best Practices

1. **Descriptive Names**: Use names that clearly identify the service purpose.
2. **Port Documentation**: Always include descriptions explaining port usage.
3. **Timeout Considerations**: Only override timeouts when necessary for application requirements.
4. **Tag Organization**: Use consistent tags for easier filtering and management.
5. **Port Range Efficiency**: Use ranges instead of listing sequential ports.
6. **Use YAML for Bulk Operations**: For large deployments, use YAML files.
