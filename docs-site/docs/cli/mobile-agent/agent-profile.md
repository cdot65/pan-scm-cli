# Agent Profile

Agent profiles (called "App Settings" / "Application Settings" in the SCM UI) configure GlobalProtect app behavior for mobile users in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load agent profiles.

## Overview

The `agent-profile` commands allow you to:

- Create agent profiles with connect method, tunnel MTU, and OS targeting
- Update existing agent profile configurations
- Delete agent profiles that are no longer needed
- Bulk import agent profiles from YAML files (including nested settings)
- Export agent profiles for backup or migration

:::note[Folder restriction]
Agent profiles only exist in the `Mobile Users` folder. The `--folder` option defaults to `Mobile Users` and any other value is rejected. Snippet and device containers are not supported.
:::

## Set Agent Profile

Create or update an agent profile.

### Syntax

```bash
scm set mobile-agent agent-profile NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the agent profile | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location (defaults to `Mobile Users`) | No |
| `--connect-method TEXT` | Connect method (`user-logon`, `pre-logon`, `on-demand`, `pre-logon-then-on-demand`) | No |
| `--tunnel-mtu INT` | GlobalProtect connection MTU in bytes (1000-1420) | No |
| `--os TEXT` | Operating system, repeatable (`Android`, `Chrome`, `IoT`, `Linux`, `Mac`, `Windows`, `WindowsUWP`, `iOS`) | No |
| `--save-user-credentials TEXT` | `0`=No, `1`=Yes, `2`=Save username only, `3`=Only with user fingerprint | No |
| `--source-user TEXT` | Source user, repeatable | No |
| `--third-party-vpn-client TEXT` | Third party VPN client, repeatable | No |

Nested settings (agent UI, gateways, HIP collection, authentication override, certificates, custom checks, internal host detection) are supported through `scm load mobile-agent agent-profile`.

### Examples

#### Create Agent Profile

```bash
$ scm set mobile-agent agent-profile "corp-app-settings" \
    --folder "Mobile Users" \
    --connect-method user-logon \
    --tunnel-mtu 1400 \
    --os Windows --os Mac
Created agent profile: corp-app-settings in folder Mobile Users
```

#### Update Save Credentials Behavior

```bash
$ scm set mobile-agent agent-profile "corp-app-settings" \
    --save-user-credentials 3
Updated agent profile: corp-app-settings in folder Mobile Users
```

## Show Agent Profile

Display one or all agent profiles.

### Syntax

```bash
scm show mobile-agent agent-profile [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the agent profile to show (lists all when omitted); omit to list all | No |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location (defaults to `Mobile Users`) | No |
| `--output, -o [table\|json\|yaml]` | Output format (default: table) | No |
| `--max-results INTEGER` | Maximum number of results to display | No |

### Examples

```bash
# List all agent profiles
$ scm show mobile-agent agent-profile

# Show a specific agent profile
$ scm show mobile-agent agent-profile "corp-app-settings"
```

## Delete Agent Profile

Remove an agent profile.

### Syntax

```bash
scm delete mobile-agent agent-profile NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the agent profile to delete | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location (defaults to `Mobile Users`) | No |
| `--force` | Skip the confirmation prompt | No |

### Examples

```bash
$ scm delete mobile-agent agent-profile "corp-app-settings" --force
Deleted agent profile: corp-app-settings from folder Mobile Users
```

## Backup Agent Profile

Export all agent profiles in a folder to a YAML file.

### Syntax

```bash
scm backup mobile-agent agent-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup from (defaults to `Mobile Users`) | No |
| `--file PATH` | Output file path (defaults to `agent-profile-mobile-users.yaml`) | No |

### Examples

```bash
$ scm backup mobile-agent agent-profile
Successfully backed up 2 agent profiles to agent-profile-mobile-users.yaml
```

## Load Agent Profile

Bulk create or update agent profiles from a YAML file. The YAML supports the full nested SDK structure.

### Syntax

```bash
scm load mobile-agent agent-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file PATH` | YAML file to load configurations from | Yes |
| `--dry-run` | Simulate execution without applying changes | No |
| `--folder TEXT` | Override folder location for all objects | No |

### YAML Schema

```yaml
agent_profiles:
  - name: corp-app-settings
    folder: "Mobile Users"
    connect_method: user-logon   # convenience key, folded into gp_app_config
    tunnel_mtu: 1400             # convenience key, folded into gp_app_config
    os:
      - Windows
      - Mac
    save_user_credentials: "0"
    agent_ui:
      max_agent_user_overrides: 5
      agent_user_override_timeout: 60
    gateways:
      external:
        list:
          - name: gw-us-east
            choice:
              fqdn: gw-us-east.example.com
            priority_rule:
              - name: default
                priority: "1"
    hip_collection:
      collect_hip_data: true
      max_wait_time: 20
```

:::tip[gp_app_config precedence]
If a profile specifies `gp_app_config` directly, it takes precedence and the `connect_method` / `tunnel_mtu` convenience keys are ignored.
:::

### Examples

```bash
# Validate without applying
$ scm load mobile-agent agent-profile --file agent_profiles.yml --dry-run

# Apply
$ scm load mobile-agent agent-profile --file agent_profiles.yml
Created agent profile: corp-app-settings

Summary: 1 created, 0 updated, 0 unchanged
```
