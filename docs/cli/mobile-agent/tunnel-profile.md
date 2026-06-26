# Tunnel Profile

Tunnel profiles configure GlobalProtect tunnel settings (split tunneling, framed IP retrieval, local network access) for mobile users in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load tunnel profiles.

## Overview

The `tunnel-profile` commands allow you to:

- Create tunnel profiles with split tunneling routes and applications
- Update existing tunnel profile configurations
- Delete tunnel profiles that are no longer needed
- Bulk import tunnel profiles from YAML files (including nested settings)
- Export tunnel profiles for backup or migration

!!! note "Folder restriction"
    Tunnel profiles only exist in the `Mobile Users` folder. The `--folder` option defaults to `Mobile Users` and any other value is rejected. Snippet and device containers are not supported. Profile names are limited to 31 characters.

## Set Tunnel Profile

Create or update a tunnel profile.

### Syntax

```bash
scm set mobile-agent tunnel-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location (defaults to `Mobile Users`) | No |
| `--name TEXT` | Name of the tunnel profile (max 31 chars) | Yes |
| `--no-direct-access-to-local-network / --allow-direct-access-to-local-network` | Disable/allow direct access to the local network | No |
| `--retrieve-framed-ip-address / --no-retrieve-framed-ip-address` | Retrieve the framed IP address from the authentication server | No |
| `--os TEXT` | Operating system, repeatable (`Android`, `Chrome`, `IoT`, `Linux`, `Mac`, `Windows`, `WindowsUWP`, `iOS`) | No |
| `--source-user TEXT` | Source user, repeatable | No |
| `--access-route TEXT` | Route included in the tunnel, repeatable | No |
| `--exclude-access-route TEXT` | Route excluded from the tunnel, repeatable | No |
| `--include-application TEXT` | Application included in the tunnel, repeatable | No |
| `--exclude-application TEXT` | Application excluded from the tunnel, repeatable | No |

Nested settings (authentication override cookies, source address, split tunneling domains) are supported through `scm load mobile-agent tunnel-profile`.

### Examples

#### Create Tunnel Profile with Split Tunneling

```bash
$ scm set mobile-agent tunnel-profile \
    --folder "Mobile Users" \
    --name "corp-tunnel" \
    --access-route 10.0.0.0/8 \
    --exclude-access-route 192.168.1.0/24 \
    --no-direct-access-to-local-network
Created tunnel profile: corp-tunnel in folder Mobile Users
```

## Show Tunnel Profile

Display one or all tunnel profiles.

### Syntax

```bash
scm show mobile-agent tunnel-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location (defaults to `Mobile Users`) | No |
| `--name TEXT` | Name of the tunnel profile to show (lists all when omitted) | No |

### Examples

```bash
# List all tunnel profiles
$ scm show mobile-agent tunnel-profile

# Show a specific tunnel profile
$ scm show mobile-agent tunnel-profile --name "corp-tunnel"
```

## Delete Tunnel Profile

Remove a tunnel profile.

### Syntax

```bash
scm delete mobile-agent tunnel-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location (defaults to `Mobile Users`) | No |
| `--name TEXT` | Name of the tunnel profile to delete | Yes |
| `--force` | Skip the confirmation prompt | No |

### Examples

```bash
$ scm delete mobile-agent tunnel-profile --name "corp-tunnel" --force
Deleted tunnel profile: corp-tunnel from folder Mobile Users
```

## Backup Tunnel Profile

Export all tunnel profiles in a folder to a YAML file.

### Syntax

```bash
scm backup mobile-agent tunnel-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup from (defaults to `Mobile Users`) | No |
| `--file PATH` | Output file path (defaults to `tunnel-profile-mobile-users.yaml`) | No |

### Examples

```bash
$ scm backup mobile-agent tunnel-profile
Successfully backed up 2 tunnel profiles to tunnel-profile-mobile-users.yaml
```

## Load Tunnel Profile

Bulk create or update tunnel profiles from a YAML file. The YAML supports the full nested SDK structure.

### Syntax

```bash
scm load mobile-agent tunnel-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file PATH` | YAML file to load configurations from | Yes |
| `--dry-run` | Simulate execution without applying changes | No |
| `--folder TEXT` | Override folder location for all objects | No |

### YAML Schema

```yaml
tunnel_profiles:
  - name: corp-tunnel
    folder: "Mobile Users"
    no_direct_access_to_local_network: true
    retrieve_framed_ip_address: false
    os:
      - Windows
      - Mac
    access_route:            # convenience key, folded into split_tunneling
      - 10.0.0.0/8
    exclude_access_route:    # convenience key, folded into split_tunneling
      - 192.168.1.0/24
    authentication_override:
      accept_cookie:
        generate_cookie: true
        cookie_lifetime:
          lifetime_in_hours: 24
    source_address:
      region:
        - US
```

!!! tip "split_tunneling precedence"
    If a profile specifies `split_tunneling` directly, it takes precedence and the `access_route` / `exclude_access_route` / `include_applications` / `exclude_applications` convenience keys are ignored.

### Examples

```bash
# Validate without applying
$ scm load mobile-agent tunnel-profile --file tunnel_profiles.yml --dry-run

# Apply
$ scm load mobile-agent tunnel-profile --file tunnel_profiles.yml
Created tunnel profile: corp-tunnel

Summary: 1 created, 0 updated, 0 unchanged
```
