# Forwarding Profile Regional and Custom Proxy

Forwarding profile regional and custom proxies define how GlobalProtect forwarding profiles steer traffic to regional Prisma Access locations or custom explicit proxies in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load regional and custom proxies.

## Overview

The `forwarding-profile-regional-and-custom-proxy` commands allow you to:

- Create regional and custom proxy definitions for forwarding profiles
- Configure primary/secondary custom proxy servers, connectivity preferences, and fallback behavior
- Update existing proxy configurations
- Delete proxies that are no longer needed
- Bulk import proxies from YAML files
- Export proxies for backup or migration

!!! note
    Forwarding profile regional and custom proxies live exclusively in the `Mobile Users` folder. Snippet and device locations are not supported.

## Field Reference

| Field | Values | Description |
| --- | --- | --- |
| `type` | `gp-and-pac` (default), `ztna-agent` | Proxy type |
| `proxy_1` / `proxy_2` | `fqdn`, `port` (1-65535), `location` | Custom proxy servers |
| `connectivity_preference` | `tunnel`, `proxy`, `adns`, `masque` (each with `enabled`) | Connectivity preference entries |
| `fallback_option` | `fail-open`, `fail-safe` | Behavior when the proxy is unreachable |
| `location_preference` | `best-available-pa-location`, `specific-pa-location` | Prisma Access location selection |
| `prisma_access_locations` | `name` (`americas`, `europe`, `apac`) + `locations` list | Specific Prisma Access locations |

## Set Forwarding Profile Regional and Custom Proxy

Create or update a forwarding profile regional and custom proxy.

### Syntax

```bash
scm set mobile-agent forwarding-profile-regional-and-custom-proxy [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location (must be `Mobile Users`) | Yes |
| `--name TEXT` | Name of the regional and custom proxy | Yes |
| `--type TEXT` | Proxy type (`gp-and-pac`, `ztna-agent`) | No |
| `--proxy-1-fqdn TEXT` | Primary proxy server FQDN | No |
| `--proxy-1-port INT` | Primary proxy server port (1-65535) | No |
| `--proxy-1-location TEXT` | Primary proxy server location | No |
| `--proxy-2-fqdn TEXT` | Secondary proxy server FQDN | No |
| `--proxy-2-port INT` | Secondary proxy server port (1-65535) | No |
| `--proxy-2-location TEXT` | Secondary proxy server location | No |
| `--fallback-option TEXT` | Fallback option (`fail-open`, `fail-safe`) | No |
| `--location-preference TEXT` | Location preference | No |
| `--description TEXT` | Description | No |

!!! tip
    Nested `connectivity_preference` and `prisma_access_locations` entries are supported via the load command's YAML schema.

### Examples

```bash
$ scm set mobile-agent forwarding-profile-regional-and-custom-proxy \
    --folder "Mobile Users" \
    --name "emea-proxy" \
    --type gp-and-pac \
    --proxy-1-fqdn "proxy1.example.com" \
    --proxy-1-port 8080 \
    --fallback-option fail-open
Created forwarding profile regional and custom proxy: emea-proxy in folder Mobile Users
```

## Show Forwarding Profile Regional and Custom Proxy

Display forwarding profile regional and custom proxies.

### Syntax

```bash
scm show mobile-agent forwarding-profile-regional-and-custom-proxy [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location (must be `Mobile Users`) | Yes |
| `--name TEXT` | Name of the regional and custom proxy to show | No |

### Examples

```bash
# List all regional and custom proxies in the folder
$ scm show mobile-agent forwarding-profile-regional-and-custom-proxy --folder "Mobile Users"

# Show a specific regional and custom proxy by name
$ scm show mobile-agent forwarding-profile-regional-and-custom-proxy --folder "Mobile Users" --name "emea-proxy"
```

## Delete Forwarding Profile Regional and Custom Proxy

Remove a forwarding profile regional and custom proxy.

### Syntax

```bash
scm delete mobile-agent forwarding-profile-regional-and-custom-proxy [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location (must be `Mobile Users`) | Yes |
| `--name TEXT` | Name of the regional and custom proxy | Yes |
| `--force` | Skip confirmation prompt | No |

### Examples

```bash
$ scm delete mobile-agent forwarding-profile-regional-and-custom-proxy --folder "Mobile Users" --name "emea-proxy" --force
Deleted forwarding profile regional and custom proxy: emea-proxy from folder Mobile Users
```

## Backup Forwarding Profile Regional and Custom Proxy

Export all forwarding profile regional and custom proxies from a folder to a YAML file.

### Syntax

```bash
scm backup mobile-agent forwarding-profile-regional-and-custom-proxy [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup from (defaults to `Mobile Users`) | No |
| `--file PATH` | Output file path (defaults to `forwarding-profile-regional-and-custom-proxy-{location}.yaml`) | No |

### Examples

```bash
$ scm backup mobile-agent forwarding-profile-regional-and-custom-proxy --folder "Mobile Users"
Successfully backed up 2 forwarding profile regional and custom proxies to forwarding-profile-regional-and-custom-proxy-mobile-users.yaml
```

## Load Forwarding Profile Regional and Custom Proxy

Bulk import forwarding profile regional and custom proxies from a YAML file. All nested fields are supported.

### Syntax

```bash
scm load mobile-agent forwarding-profile-regional-and-custom-proxy [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file PATH` | YAML file to load from | Yes |
| `--dry-run` | Simulate execution without applying changes | No |
| `--folder TEXT` | Override folder location for all objects | No |

### YAML Schema

```yaml
forwarding_profile_regional_and_custom_proxies:
  - name: emea-proxy
    folder: "Mobile Users"
    type: gp-and-pac
    proxy_1:
      fqdn: proxy1.example.com
      port: 8080
    proxy_2:
      fqdn: proxy2.example.com
      port: 8080
    connectivity_preference:
      - name: tunnel
        enabled: true
      - name: proxy
        enabled: false
    fallback_option: fail-open
  - name: ztna-proxy
    folder: "Mobile Users"
    type: ztna-agent
    location_preference: specific-pa-location
    prisma_access_locations:
      - name: europe
        locations:
          - "Frankfurt"
```

### Examples

```bash
# Preview without applying
$ scm load mobile-agent forwarding-profile-regional-and-custom-proxy --file regional_proxies.yml --dry-run

# Apply the configurations
$ scm load mobile-agent forwarding-profile-regional-and-custom-proxy --file regional_proxies.yml
Created forwarding profile regional and custom proxy: emea-proxy
Created forwarding profile regional and custom proxy: ztna-proxy

Summary: 2 created, 0 updated, 0 unchanged
```
