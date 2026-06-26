# Infrastructure Setting

Infrastructure settings configure the GlobalProtect mobile users environment in Strata Cloud Manager — DNS servers, IP pools, the portal hostname, WINS, IPv6, and UDP query behavior. The `scm` CLI provides commands to create, update, delete, show, back up, and load infrastructure settings.

## Overview

The `infrastructure-setting` commands allow you to:

- Create or update infrastructure settings with DNS servers, IP pools, and a portal hostname
- Show a named infrastructure setting
- Delete infrastructure settings
- Back up a named infrastructure setting to YAML
- Bulk import infrastructure settings from YAML files

!!! note "Folder constraint"
    Infrastructure settings live only in the `Mobile Users` folder. The `--folder` option defaults to `Mobile Users` and any other value is rejected.

!!! note "Name required for show and backup"
    The SCM API addresses this resource by name everywhere, including list. There is no list-all mode, so `show` and `backup` require `--name`.

## Set Infrastructure Setting

Create or update an infrastructure setting.

### Syntax

```bash
scm set mobile-agent infrastructure-setting [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the infrastructure setting | Yes |
| `--folder TEXT` | Folder location (must be `Mobile Users`, the default) | No |
| `--dns-servers JSON` | DNS server entries as a JSON list | Yes |
| `--ip-pools JSON` | IP pools as a JSON list | Yes |
| `--portal-hostname JSON` | Portal hostname configuration as JSON | Yes |
| `--enable-wins JSON` | WINS configuration as JSON | No |
| `--ipv6 / --no-ipv6` | Enable or disable IPv6 | No |
| `--udp-queries JSON` | UDP query retry configuration as JSON | No |
| `--static-ip-pools JSON` | Static IP pools as a JSON list | No |

### Examples

```bash
$ scm set mobile-agent infrastructure-setting \
    --name "gp-infra" \
    --dns-servers '[{"name": "dns-1", "dns_suffix": ["example.com"], "primary_public_dns": {"dns_server": "8.8.8.8"}}]' \
    --ip-pools '[{"name": "pool-1", "ip_pool": ["10.0.0.0/16"]}]' \
    --portal-hostname '{"default_domain": {"hostname": "acme"}}'
Created infrastructure setting: gp-infra in folder Mobile Users
```

```bash
$ scm set mobile-agent infrastructure-setting \
    --name "gp-infra" \
    --dns-servers '[{"name": "dns-1", "dns_suffix": ["example.com"]}]' \
    --ip-pools '[{"name": "pool-1", "ip_pool": ["10.0.0.0/16"]}]' \
    --portal-hostname '{"custom_domain": {"hostname": "vpn.acme.com", "cname": "acme.gpcloudservice.com", "ssl_tls_service_profile": "acme-profile"}}' \
    --ipv6 \
    --udp-queries '{"retries": {"attempts": 5, "interval": 2}}'
Updated infrastructure setting: gp-infra in folder Mobile Users
```

## Show Infrastructure Setting

Display a named infrastructure setting.

### Syntax

```bash
scm show mobile-agent infrastructure-setting --name NAME
```

### Examples

```bash
$ scm show mobile-agent infrastructure-setting --name "gp-infra"

Infrastructure Setting: gp-infra
================================================================================
Location: Folder 'Mobile Users'
Portal Hostname: {default_domain: {hostname: acme}}
DNS Servers: [{name: dns-1, dns_suffix: [example.com]}]
IP Pools: [{name: pool-1, ip_pool: [10.0.0.0/16]}]
```

## Delete Infrastructure Setting

Delete an infrastructure setting.

### Syntax

```bash
scm delete mobile-agent infrastructure-setting --name NAME [--force]
```

### Examples

```bash
$ scm delete mobile-agent infrastructure-setting --name "gp-infra" --force
Deleted infrastructure setting: gp-infra from folder Mobile Users
```

## Backup Infrastructure Setting

Back up a named infrastructure setting to a YAML file.

### Syntax

```bash
scm backup mobile-agent infrastructure-setting --name NAME [--file FILE]
```

### Examples

```bash
$ scm backup mobile-agent infrastructure-setting --name "gp-infra"
Successfully backed up 1 infrastructure settings to infrastructure-setting-mobile-users.yaml
```

## Load Infrastructure Setting

Load infrastructure settings from a YAML file.

### Syntax

```bash
scm load mobile-agent infrastructure-setting --file FILE [--dry-run] [--folder FOLDER]
```

### YAML Format

```yaml
infrastructure_settings:
  - name: gp-infra
    folder: "Mobile Users"
    dns_servers:
      - name: dns-1
        dns_suffix:
          - example.com
        primary_public_dns:
          dns_server: 8.8.8.8
    ip_pools:
      - name: pool-1
        ip_pool:
          - 10.0.0.0/16
    portal_hostname:
      default_domain:
        hostname: acme
    ipv6: false
```

### Examples

```bash
$ scm load mobile-agent infrastructure-setting --file infrastructure_settings.yml
Created infrastructure setting: gp-infra

Summary: 1 created, 0 updated, 0 unchanged
```

```bash
$ scm load mobile-agent infrastructure-setting --file infrastructure_settings.yml --dry-run
Dry run mode: would apply the following configurations:
...
```
