# RADIUS Server Profile

RADIUS server profiles configure RADIUS servers for authentication, authorization, and accounting (AAA) in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, and bulk manage RADIUS server profiles.

## Overview

The `radius-server-profile` commands allow you to:

- Create RADIUS server profiles with server and protocol configurations
- Update existing profile settings including timeout and retry parameters
- Delete profiles that are no longer needed
- Bulk import profiles from YAML files
- Export profiles for backup or migration

## Set RADIUS Server Profile

Create or update a RADIUS server profile.

### Syntax

```bash
scm set identity radius-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Profile name | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--servers TEXT` | Server list as JSON | No |
| `--protocol TEXT` | Protocol configuration as JSON | No |
| `--timeout INT` | Timeout in seconds (1-120) | No |
| `--retries INT` | Number of retries (1-5) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create RADIUS Server Profile

```bash
$ scm set identity radius-server-profile \
    --folder Texas \
    --name corp-radius \
    --servers '[{"name": "rad1", "ip_address": "10.0.0.1", "port": 1812, "secret": "s3cret"}]' \
    --protocol '{"CHAP": {}}' \
    --timeout 5 \
    --retries 3
---> 100%
Created radius-server-profile: corp-radius in folder Texas
```

#### Create Profile with Multiple Servers

```bash
$ scm set identity radius-server-profile \
    --folder Texas \
    --name corp-radius-ha \
    --servers '[{"name": "rad1", "ip_address": "10.0.0.1", "port": 1812, "secret": "s3cret"}, {"name": "rad2", "ip_address": "10.0.0.2", "port": 1812, "secret": "s3cret"}]' \
    --timeout 3 \
    --retries 3
---> 100%
Created radius-server-profile: corp-radius-ha in folder Texas
```

#### Create Profile with PAP Protocol

```bash
$ scm set identity radius-server-profile \
    --folder Texas \
    --name vpn-radius \
    --servers '[{"name": "rad-vpn", "ip_address": "10.0.1.1", "port": 1812, "secret": "vpn-s3cret"}]' \
    --protocol '{"PAP": {}}' \
    --timeout 10
---> 100%
Created radius-server-profile: vpn-radius in folder Texas
```

## Delete RADIUS Server Profile

Delete a RADIUS server profile from SCM.

### Syntax

```bash
scm delete identity radius-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Profile name | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete identity radius-server-profile \
    --folder Texas \
    --name corp-radius \
    --force
---> 100%
Deleted radius-server-profile: corp-radius from folder Texas
```

## Load RADIUS Server Profile

Load multiple RADIUS server profiles from a YAML file.

### Syntax

```bash
scm load identity radius-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file | Yes |
| `--folder TEXT` | Folder location override | No |
| `--snippet TEXT` | Snippet location override | No |
| `--device TEXT` | Device location override | No |
| `--dry-run` | Preview changes without applying | No |

### YAML File Format

```yaml
---
radius_server_profiles:
  - name: corp-radius
    folder: Texas
    servers:
      - name: rad1
        ip_address: "10.0.0.1"
        port: 1812
        secret: s3cret
    protocol:
      CHAP: {}
    timeout: 5
    retries: 3

  - name: vpn-radius
    folder: Texas
    servers:
      - name: rad-vpn
        ip_address: "10.0.1.1"
        port: 1812
        secret: vpn-s3cret
    protocol:
      PAP: {}
    timeout: 10
```

### Examples

#### Load with Original Locations

```bash
$ scm load identity radius-server-profile --file radius.yml
---> 100%
✓ Loaded radius-server-profile: corp-radius
✓ Loaded radius-server-profile: vpn-radius

Successfully loaded 2 out of 2 radius-server-profiles from 'radius.yml'
```

#### Load with Folder Override

```bash
$ scm load identity radius-server-profile \
    --file radius.yml \
    --folder Austin
---> 100%
✓ Loaded radius-server-profile: corp-radius
✓ Loaded radius-server-profile: vpn-radius

Successfully loaded 2 out of 2 radius-server-profiles from 'radius.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all RADIUS server
profiles will be loaded into the specified container, ignoring the container specified in
the YAML file.
:::

## Show RADIUS Server Profile

Display RADIUS server profile objects.

### Syntax

```bash
scm show identity radius-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Profile name | No |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |

\* One of --folder, --snippet, or --device is required.

:::note
When no `--name` is specified, all items are listed by default.
:::

### Examples

#### Show Specific RADIUS Server Profile

```bash
$ scm show identity radius-server-profile \
    --folder Texas \
    --name corp-radius
---> 100%
RADIUS Server Profile: corp-radius
  Location: Folder 'Texas'
  Protocol: CHAP
  Timeout: 5s
  Retries: 3
  Servers:
    - rad1 (10.0.0.1:1812)
```

#### List All RADIUS Server Profiles (Default Behavior)

```bash
$ scm show identity radius-server-profile --folder Texas
---> 100%
RADIUS Server Profiles in folder 'Texas':
------------------------------------------------------------
Name: corp-radius
  Protocol: CHAP
  Servers: rad1 (10.0.0.1:1812)
------------------------------------------------------------
Name: vpn-radius
  Protocol: PAP
  Servers: rad-vpn (10.0.1.1:1812)
------------------------------------------------------------
```

## Backup RADIUS Server Profiles

Backup all RADIUS server profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup identity radius-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--file TEXT` | Custom output filename | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup identity radius-server-profile --folder Texas
---> 100%
Successfully backed up 3 radius-server-profiles to radius_server_profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup identity radius-server-profile \
    --folder Texas \
    --file texas-radius.yaml
---> 100%
Successfully backed up 3 radius-server-profiles to texas-radius.yaml
```

## Best Practices

1. **Use Strong Shared Secrets**: Configure strong, unique shared secrets for each RADIUS server to secure communication.
2. **Configure Multiple Servers**: Add redundant RADIUS servers to ensure high availability for authentication services.
3. **Tune Timeout and Retries**: Set appropriate timeout and retry values based on your network latency to avoid authentication delays.
4. **Choose the Right Protocol**: Use CHAP for enhanced password security or PAP when compatibility with legacy systems is required.
5. **Backup Before Changes**: Export existing profiles before making modifications to enable quick rollback if needed.
6. **Use YAML for Bulk Operations**: Manage multiple RADIUS server profiles through YAML files to ensure consistency across environments.
