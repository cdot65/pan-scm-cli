# Forwarding Profile Destination

Forwarding profile destinations define FQDN and IP address targets that GlobalProtect forwarding rules match against in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load destinations.

## Overview

The `forwarding-profile-destination` commands allow you to:

- Create destinations with FQDN entries (wildcards supported) and IP address entries (wildcards and CIDR supported)
- Update existing destination configurations
- Delete destinations by name or UUID
- Show a destination by name or UUID, or list all destinations
- Bulk import destinations from YAML files
- Export destinations for backup or migration

:::note
Destinations only support the `Mobile Users` folder. The API addresses individual destinations by UUID; the CLI resolves `--name` to the UUID for you, or you can pass `--id` directly.
:::

## Entry Formats

| Entry | Format | Examples |
| --- | --- | --- |
| FQDN | `host` or `host:port`; wildcards allowed | `app.internal`, `*.example.com:8080` |
| IP address | `ip`, `ip/prefix`, or `ip:port`; wildcards allowed | `10.0.0.0/8`, `192.168.1.1:443`, `10.*.*.*` |

Ports must be between 1 and 65535.

## Set Forwarding Profile Destination

Create or update a destination.

### Syntax

```bash
scm set mobile-agent forwarding-profile-destination [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location (must be `Mobile Users`) | Yes |
| `--name TEXT` | Name of the destination | Yes |
| `--description TEXT` | Description | No |
| `--fqdn TEXT` | FQDN entry as `host[:port]` (repeatable) | No |
| `--ip-address TEXT` | IP entry as `ip[/prefix][:port]` (repeatable) | No |

### Examples

```bash
$ scm set mobile-agent forwarding-profile-destination \
    --folder "Mobile Users" \
    --name "internal-apps" \
    --fqdn "*.example.com:8080" \
    --fqdn "app.internal" \
    --ip-address "10.0.0.0/8"
Created forwarding profile destination: internal-apps
```

## Show Forwarding Profile Destination

Display destinations.

### Syntax

```bash
scm show mobile-agent forwarding-profile-destination [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No (defaults to `Mobile Users`) |
| `--name TEXT` | Name of the destination to show | No |
| `--id TEXT` | UUID of the destination to show | No |

### Examples

```bash
# List all destinations
$ scm show mobile-agent forwarding-profile-destination --folder "Mobile Users"

# Show by name
$ scm show mobile-agent forwarding-profile-destination --folder "Mobile Users" --name "internal-apps"

# Show by UUID
$ scm show mobile-agent forwarding-profile-destination --id "123e4567-e89b-12d3-a456-426655440000"
```

## Delete Forwarding Profile Destination

Delete a destination by name or UUID.

### Syntax

```bash
scm delete mobile-agent forwarding-profile-destination [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No (defaults to `Mobile Users`) |
| `--name TEXT` | Name of the destination to delete | Yes (or `--id`) |
| `--id TEXT` | UUID of the destination to delete | No |
| `--force` | Skip confirmation prompt | No |

### Examples

```bash
$ scm delete mobile-agent forwarding-profile-destination --folder "Mobile Users" --name "internal-apps" --force
Deleted forwarding profile destination: internal-apps
```

## Load Forwarding Profile Destination

Bulk import destinations from a YAML file.

### Syntax

```bash
scm load mobile-agent forwarding-profile-destination --file FILE [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file PATH` | YAML file to load from | Yes |
| `--dry-run` | Preview without applying | No |
| `--folder TEXT` | Override folder for all objects | No |

### YAML Format

```yaml
forwarding_profile_destinations:
  - name: internal-apps
    folder: "Mobile Users"
    description: Internal applications
    fqdn:
      - name: app.internal
        port: 443
      - name: "*.example.com"
  - name: corp-ranges
    folder: "Mobile Users"
    ip_addresses:
      - name: 10.0.0.0/8
      - name: 192.168.1.1
        port: 443
```

## Backup Forwarding Profile Destination

Export all destinations in a folder to a YAML file (re-loadable via `scm load`).

### Syntax

```bash
scm backup mobile-agent forwarding-profile-destination [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup from | No (defaults to `Mobile Users`) |
| `--file PATH` | Output file (defaults to `forwarding-profile-destination-{folder}.yaml`) | No |

### Examples

```bash
$ scm backup mobile-agent forwarding-profile-destination --folder "Mobile Users"
Successfully backed up 2 forwarding profile destinations to forwarding-profile-destination-mobile-users.yaml
```

## Related

- [Forwarding Profile](forwarding-profile.md) — profiles whose forwarding rules reference these destinations
- [Auth Setting](auth-setting.md)
