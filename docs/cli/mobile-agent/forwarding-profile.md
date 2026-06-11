# Forwarding Profile

Forwarding profiles control how GlobalProtect mobile agent traffic is forwarded (PAC file, GlobalProtect proxy, or ZTNA agent) in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load forwarding profiles.

## Overview

The `forwarding-profile` commands allow you to:

- Create forwarding profiles of type PAC file, GlobalProtect proxy, or ZTNA agent
- Update existing forwarding profile configurations
- Delete forwarding profiles by name or UUID
- Show a profile by name or UUID, or list all profiles
- Bulk import forwarding profiles (including forwarding rules and block rules) from YAML files
- Export forwarding profiles for backup or migration

!!! note
    Forwarding profiles only support the `Mobile Users` folder. The API addresses individual profiles by UUID; the CLI resolves `--name` to the UUID for you, or you can pass `--id` directly.

## Profile Types

| Type | `--profile-type` value | YAML `type` key | Description |
| --- | --- | --- | --- |
| PAC file | `pac-file` | `pac_file` | Forwarding driven by a PAC file |
| GlobalProtect proxy | `global-protect-proxy` | `global_protect_proxy` | Forwarding via GlobalProtect proxy |
| ZTNA agent | `ztna-agent` | `ztna_agent` | ZTNA agent forwarding with traffic-type rules |

## Set Forwarding Profile

Create or update a forwarding profile.

### Syntax

```bash
scm set mobile-agent forwarding-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location (must be `Mobile Users`) | Yes |
| `--name TEXT` | Name of the forwarding profile | Yes |
| `--description TEXT` | Description | No |
| `--definition-method TEXT` | How the profile is defined: `rules` or `pac-file` | No |
| `--profile-type TEXT` | Profile type: `pac-file`, `global-protect-proxy`, or `ztna-agent` | No |
| `--pac-upload / --no-pac-upload` | Whether the user uploads a PAC file | No |

Complex forwarding rules and block rules are not expressible as flags — use [Load Forwarding Profile](#load-forwarding-profile) with a YAML file for those.

### Examples

#### Create ZTNA Agent Profile

```bash
$ scm set mobile-agent forwarding-profile \
    --folder "Mobile Users" \
    --name "ztna-profile" \
    --profile-type ztna-agent
Created forwarding profile: ztna-profile
```

#### Create GlobalProtect Proxy Profile with PAC Upload

```bash
$ scm set mobile-agent forwarding-profile \
    --folder "Mobile Users" \
    --name "proxy-profile" \
    --profile-type global-protect-proxy \
    --pac-upload
Created forwarding profile: proxy-profile
```

## Show Forwarding Profile

Display forwarding profiles.

### Syntax

```bash
scm show mobile-agent forwarding-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No (defaults to `Mobile Users`) |
| `--name TEXT` | Name of the profile to show | No |
| `--id TEXT` | UUID of the profile to show | No |

### Examples

```bash
# List all forwarding profiles
$ scm show mobile-agent forwarding-profile --folder "Mobile Users"

# Show by name
$ scm show mobile-agent forwarding-profile --folder "Mobile Users" --name "ztna-profile"

# Show by UUID
$ scm show mobile-agent forwarding-profile --id "123e4567-e89b-12d3-a456-426655440000"
```

## Delete Forwarding Profile

Delete a forwarding profile by name or UUID.

### Syntax

```bash
scm delete mobile-agent forwarding-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No (defaults to `Mobile Users`) |
| `--name TEXT` | Name of the profile to delete | Yes (or `--id`) |
| `--id TEXT` | UUID of the profile to delete | No |
| `--force` | Skip confirmation prompt | No |

### Examples

```bash
$ scm delete mobile-agent forwarding-profile --folder "Mobile Users" --name "ztna-profile" --force
Deleted forwarding profile: ztna-profile
```

## Load Forwarding Profile

Bulk import forwarding profiles from a YAML file. This is the path for full configurations including forwarding rules and block rules.

### Syntax

```bash
scm load mobile-agent forwarding-profile --file FILE [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file PATH` | YAML file to load from | Yes |
| `--dry-run` | Preview without applying | No |
| `--folder TEXT` | Override folder for all objects | No |

### YAML Format

```yaml
forwarding_profiles:
  - name: ztna-profile
    folder: "Mobile Users"
    definition_method: rules
    type:
      ztna_agent:
        pac_upload: false
        forwarding_rules:
          - name: rule1
            traffic_type: dns            # dns | dns-and-network-traffic | network-traffic
            enabled: true
            user_locations: Any
            source_applications: Any
            destinations: Any
            connectivity: direct
        block_rule:
          block_all_other_unmatched_outbound_connections: true
          allow_icmp_for_troubleshooting: true
  - name: pac-profile
    folder: "Mobile Users"
    definition_method: pac-file
    type:
      pac_file:
        pac_upload: true
        forwarding_rules:
          - name: rule1
            enabled: true
            connectivity: direct
        block_rule:
          enable: true
          allow_tcp:
            enable_locations: true
            locations:
              - "US"
```

## Backup Forwarding Profile

Export all forwarding profiles in a folder to a YAML file (re-loadable via `scm load`).

### Syntax

```bash
scm backup mobile-agent forwarding-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup from | No (defaults to `Mobile Users`) |
| `--file PATH` | Output file (defaults to `forwarding-profile-{folder}.yaml`) | No |

### Examples

```bash
$ scm backup mobile-agent forwarding-profile --folder "Mobile Users"
Successfully backed up 2 forwarding profiles to forwarding-profile-mobile-users.yaml
```

## Related

- [Forwarding Profile Destination](forwarding-profile-destination.md) — destination objects referenced by forwarding rules
- [Auth Setting](auth-setting.md)
