# Internal DNS Server

Internal DNS servers configure DNS resolution for internal domains through SASE infrastructure. The `scm` CLI provides commands to create, update, delete, bulk load, and back up internal DNS server configurations.

## Overview

The `internal-dns-server` commands allow you to:

- Create DNS server entries for internal domain resolution
- Configure primary and secondary DNS servers for redundancy
- Delete DNS server entries that are no longer needed
- Bulk import DNS server configurations from YAML files
- Export DNS server configurations for backup or migration

## Set Internal DNS Server

Create or update an internal DNS server configuration.

### Syntax

```bash
scm set sase internal-dns-server [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the DNS server entry | Yes |
| `--domain-name TEXT` | Domain name(s), comma-separated | Yes |
| `--primary TEXT` | Primary DNS server IP address | Yes |
| `--secondary TEXT` | Secondary DNS server IP address | No |

### Examples

#### Create a DNS Server with Primary and Secondary

```bash
$ scm set sase internal-dns-server \
    --name corp-dns \
    --domain-name corp.example.com \
    --primary 10.0.0.1 \
    --secondary 10.0.0.2
---> 100%
Created internal DNS server: corp-dns
```

#### Create a DNS Server for Multiple Domains

```bash
$ scm set sase internal-dns-server \
    --name multi-domain-dns \
    --domain-name "internal.example.com,dev.example.com" \
    --primary 10.0.1.1
---> 100%
Created internal DNS server: multi-domain-dns
```

## Delete Internal DNS Server

Delete an internal DNS server configuration from SCM.

### Syntax

```bash
scm delete sase internal-dns-server [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the DNS server entry to delete | Yes |
| `--force` | Skip confirmation prompt | No |

### Example

```bash
$ scm delete sase internal-dns-server --name corp-dns --force
---> 100%
Deleted internal DNS server: corp-dns
```

## Load Internal DNS Servers

Load multiple internal DNS server configurations from a YAML file.

### Syntax

```bash
scm load sase internal-dns-server [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing DNS server definitions | Yes |

### YAML File Format

```yaml
---
internal_dns_servers:
  - name: corp-dns
    domain_name:
      - corp.example.com
    primary: 10.0.0.1
    secondary: 10.0.0.2

  - name: dev-dns
    domain_name:
      - dev.example.com
      - staging.example.com
    primary: 10.0.1.1
    secondary: 10.0.1.2
```

### Examples

#### Load DNS Server Configurations

```bash
$ scm load sase internal-dns-server --file dns-servers.yml
---> 100%
✓ Loaded internal DNS server: corp-dns
✓ Loaded internal DNS server: dev-dns

Successfully loaded 2 out of 2 internal DNS servers from 'dns-servers.yml'
```

## Show Internal DNS Server

Display internal DNS server configurations.

### Syntax

```bash
scm show sase internal-dns-server [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the DNS server entry to show | No |

:::note
When no `--name` is specified, all items are listed by default.
:::

### Examples

#### Show Specific Internal DNS Server

```bash
$ scm show sase internal-dns-server --name corp-dns
---> 100%
Internal DNS Server: corp-dns
  Domain: corp.example.com
  Primary: 10.0.0.1
  Secondary: 10.0.0.2
```

#### List All Internal DNS Servers (Default Behavior)

```bash
$ scm show sase internal-dns-server
---> 100%
Internal DNS Servers:
------------------------------------------------------------
Name: corp-dns
  Domain: corp.example.com
  Primary: 10.0.0.1
  Secondary: 10.0.0.2
------------------------------------------------------------
Name: dev-dns
  Domain: dev.example.com, staging.example.com
  Primary: 10.0.1.1
  Secondary: 10.0.1.2
------------------------------------------------------------
```

## Backup Internal DNS Servers

Backup all internal DNS server configurations to a YAML file.

### Syntax

```bash
scm backup sase internal-dns-server [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Custom output filename | No |

### Examples

#### Backup with Default Filename

```bash
$ scm backup sase internal-dns-server
---> 100%
Successfully backed up 2 internal DNS servers to internal_dns_server_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup sase internal-dns-server --file dns-backup.yaml
---> 100%
Successfully backed up 2 internal DNS servers to dns-backup.yaml
```

## Best Practices

1. **Configure Secondary Servers**: Always specify a secondary DNS server for redundancy in case the primary becomes unreachable.
2. **Use Descriptive Names**: Name DNS server entries to clearly indicate the domains they serve (e.g., "corp-dns", "dev-dns").
3. **Minimize Domain Overlap**: Avoid configuring multiple DNS server entries for the same domain to prevent resolution conflicts.
4. **Backup Before Changes**: Export existing configurations with the backup command before making bulk changes via load.
5. **Validate DNS Reachability**: Ensure the specified DNS server IP addresses are reachable from your SASE infrastructure before configuring them.
