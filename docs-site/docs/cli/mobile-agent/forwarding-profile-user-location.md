# Forwarding Profile User Location

Forwarding profile user locations define where a GlobalProtect user is located — by IP address ranges or by internal host detection — for use as match criteria in forwarding profiles in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load user locations.

## Overview

The `forwarding-profile-user-location` commands allow you to:

- Create user locations based on IP address entries or internal host detection
- Update existing user location configurations
- Delete user locations that are no longer needed
- Bulk import user locations from YAML files
- Export user locations for backup or migration

:::note
Forwarding profile user locations live exclusively in the `Mobile Users` folder. Snippet and device locations are not supported.
:::

## Location Matching Criteria

Each user location uses exactly **one** of the following:

| Criteria | Options | Description |
| --- | --- | --- |
| IP addresses | `--ip-address` (repeatable) | IPv4 entries, with optional wildcards (`10.2.*.*`) or CIDR suffix (`10.1.0.0/16`) |
| Internal host detection | `--internal-host-ip`, `--internal-host-fqdn` | Detect the user's network by resolving a known internal host |

Providing both (or neither) is a validation error.

## Set Forwarding Profile User Location

Create or update a forwarding profile user location.

### Syntax

```bash
scm set mobile-agent forwarding-profile-user-location NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the user location | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location (must be `Mobile Users`) | Yes |
| `--ip-address TEXT` | User location IP address (repeatable) | One criteria |
| `--internal-host-ip TEXT` | Internal host detection IP address | One criteria |
| `--internal-host-fqdn TEXT` | Internal host detection FQDN | One criteria |
| `--description TEXT` | Description | No |

### Examples

```bash
# IP address based location
$ scm set mobile-agent forwarding-profile-user-location "branch-network" \
    --folder "Mobile Users" \
    --ip-address "10.1.0.0/16" \
    --ip-address "10.2.*.*"
Created forwarding profile user location: branch-network in folder Mobile Users

# Internal host detection based location
$ scm set mobile-agent forwarding-profile-user-location "corp-office" \
    --folder "Mobile Users" \
    --internal-host-ip "192.168.1.1" \
    --internal-host-fqdn "intranet.example.com"
Created forwarding profile user location: corp-office in folder Mobile Users
```

## Show Forwarding Profile User Location

Display forwarding profile user locations.

### Syntax

```bash
scm show mobile-agent forwarding-profile-user-location [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the user location to show; omit to list all | No |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location (must be `Mobile Users`) | Yes |
| `--output, -o [table\|json\|yaml]` | Output format (default: table) | No |
| `--max-results INTEGER` | Maximum number of results to display | No |

### Examples

```bash
# List all user locations in the folder
$ scm show mobile-agent forwarding-profile-user-location --folder "Mobile Users"

# Show a specific user location by name
$ scm show mobile-agent forwarding-profile-user-location "branch-network" --folder "Mobile Users"
```

## Delete Forwarding Profile User Location

Remove a forwarding profile user location.

### Syntax

```bash
scm delete mobile-agent forwarding-profile-user-location NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the user location | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location (must be `Mobile Users`) | Yes |
| `--force` | Skip confirmation prompt | No |

### Examples

```bash
$ scm delete mobile-agent forwarding-profile-user-location "branch-network" --folder "Mobile Users" --force
Deleted forwarding profile user location: branch-network from folder Mobile Users
```

## Backup Forwarding Profile User Location

Export all forwarding profile user locations from a folder to a YAML file. The exported YAML uses the same flat schema accepted by the load command.

### Syntax

```bash
scm backup mobile-agent forwarding-profile-user-location [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup from (defaults to `Mobile Users`) | No |
| `--file PATH` | Output file path (defaults to `forwarding-profile-user-location-{location}.yaml`) | No |

### Examples

```bash
$ scm backup mobile-agent forwarding-profile-user-location --folder "Mobile Users"
Successfully backed up 2 forwarding profile user locations to forwarding-profile-user-location-mobile-users.yaml
```

## Load Forwarding Profile User Location

Bulk import forwarding profile user locations from a YAML file.

### Syntax

```bash
scm load mobile-agent forwarding-profile-user-location [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file PATH` | YAML file to load from | Yes |
| `--dry-run` | Simulate execution without applying changes | No |
| `--folder TEXT` | Override folder location for all objects | No |

### YAML Schema

Each entry uses either `ip_addresses` or the internal host detection fields (`internal_host_ip` / `internal_host_fqdn`):

```yaml
forwarding_profile_user_locations:
  - name: branch-network
    folder: "Mobile Users"
    ip_addresses:
      - 10.1.0.0/16
      - 10.2.*.*
  - name: corp-office
    folder: "Mobile Users"
    internal_host_ip: 192.168.1.1
    internal_host_fqdn: intranet.example.com
```

### Examples

```bash
# Preview without applying
$ scm load mobile-agent forwarding-profile-user-location --file user_locations.yml --dry-run

# Apply the configurations
$ scm load mobile-agent forwarding-profile-user-location --file user_locations.yml
Created forwarding profile user location: branch-network
Created forwarding profile user location: corp-office

Summary: 2 created, 0 updated, 0 unchanged
```
