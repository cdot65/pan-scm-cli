# TACACS+ Server Profile

TACACS+ server profiles configure TACACS+ servers for authentication, authorization, and accounting in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, and bulk manage TACACS+ server profiles.

## Overview

The `tacacs-server-profile` commands allow you to:

- Create TACACS+ server profiles with server and protocol configurations
- Update existing profile settings including timeout and connection options
- Delete profiles that are no longer needed
- Bulk import profiles from YAML files
- Export profiles for backup or migration

## Set TACACS+ Server Profile

Create or update a TACACS+ server profile.

### Syntax

```bash
scm set identity tacacs-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Profile name | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--servers TEXT` | Server list as JSON | No |
| `--protocol TEXT` | Protocol type (CHAP, PAP) | No |
| `--timeout INT` | Timeout in seconds (1-30) | No |
| `--use-single-connection` | Use single connection | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create TACACS+ Server Profile

```bash
$ scm set identity tacacs-server-profile \
    --folder Texas \
    --name corp-tacacs \
    --servers '[{"name": "tac1", "address": "10.0.0.1", "port": 49, "secret": "s3cret"}]' \
    --protocol CHAP \
    --timeout 5
---> 100%
Created tacacs-server-profile: corp-tacacs in folder Texas
```

#### Create Profile with Multiple Servers and Single Connection

```bash
$ scm set identity tacacs-server-profile \
    --folder Texas \
    --name corp-tacacs-ha \
    --servers '[{"name": "tac1", "address": "10.0.0.1", "port": 49, "secret": "s3cret"}, {"name": "tac2", "address": "10.0.0.2", "port": 49, "secret": "s3cret"}]' \
    --protocol CHAP \
    --timeout 3 \
    --use-single-connection
---> 100%
Created tacacs-server-profile: corp-tacacs-ha in folder Texas
```

#### Create Profile with PAP Protocol

```bash
$ scm set identity tacacs-server-profile \
    --folder Texas \
    --name legacy-tacacs \
    --servers '[{"name": "tac-legacy", "address": "10.0.1.1", "port": 49, "secret": "legacy-s3cret"}]' \
    --protocol PAP \
    --timeout 10
---> 100%
Created tacacs-server-profile: legacy-tacacs in folder Texas
```

## Delete TACACS+ Server Profile

Delete a TACACS+ server profile from SCM.

### Syntax

```bash
scm delete identity tacacs-server-profile [OPTIONS]
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
$ scm delete identity tacacs-server-profile \
    --folder Texas \
    --name corp-tacacs \
    --force
---> 100%
Deleted tacacs-server-profile: corp-tacacs from folder Texas
```

## Load TACACS+ Server Profile

Load multiple TACACS+ server profiles from a YAML file.

### Syntax

```bash
scm load identity tacacs-server-profile [OPTIONS]
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
tacacs_server_profiles:
  - name: corp-tacacs
    folder: Texas
    servers:
      - name: tac1
        address: "10.0.0.1"
        port: 49
        secret: s3cret
    protocol: CHAP
    timeout: 5

  - name: legacy-tacacs
    folder: Texas
    servers:
      - name: tac-legacy
        address: "10.0.1.1"
        port: 49
        secret: legacy-s3cret
    protocol: PAP
    timeout: 10
```

### Examples

#### Load with Original Locations

```bash
$ scm load identity tacacs-server-profile --file tacacs.yml
---> 100%
✓ Loaded tacacs-server-profile: corp-tacacs
✓ Loaded tacacs-server-profile: legacy-tacacs

Successfully loaded 2 out of 2 tacacs-server-profiles from 'tacacs.yml'
```

#### Load with Folder Override

```bash
$ scm load identity tacacs-server-profile \
    --file tacacs.yml \
    --folder Austin
---> 100%
✓ Loaded tacacs-server-profile: corp-tacacs
✓ Loaded tacacs-server-profile: legacy-tacacs

Successfully loaded 2 out of 2 tacacs-server-profiles from 'tacacs.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all TACACS+ server
profiles will be loaded into the specified container, ignoring the container specified in
the YAML file.
:::

## Show TACACS+ Server Profile

Display TACACS+ server profile objects.

### Syntax

```bash
scm show identity tacacs-server-profile [OPTIONS]
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

#### Show Specific TACACS+ Server Profile

```bash
$ scm show identity tacacs-server-profile \
    --folder Texas \
    --name corp-tacacs
---> 100%
TACACS+ Server Profile: corp-tacacs
  Location: Folder 'Texas'
  Protocol: CHAP
  Timeout: 5s
  Single Connection: No
  Servers:
    - tac1 (10.0.0.1:49)
```

#### List All TACACS+ Server Profiles (Default Behavior)

```bash
$ scm show identity tacacs-server-profile --folder Texas
---> 100%
TACACS+ Server Profiles in folder 'Texas':
------------------------------------------------------------
Name: corp-tacacs
  Protocol: CHAP
  Servers: tac1 (10.0.0.1:49)
------------------------------------------------------------
Name: legacy-tacacs
  Protocol: PAP
  Servers: tac-legacy (10.0.1.1:49)
------------------------------------------------------------
```

## Backup TACACS+ Server Profiles

Backup all TACACS+ server profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup identity tacacs-server-profile [OPTIONS]
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
$ scm backup identity tacacs-server-profile --folder Texas
---> 100%
Successfully backed up 3 tacacs-server-profiles to tacacs_server_profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup identity tacacs-server-profile \
    --folder Texas \
    --file texas-tacacs.yaml
---> 100%
Successfully backed up 3 tacacs-server-profiles to texas-tacacs.yaml
```

## Best Practices

1. **Use Strong Shared Secrets**: Configure strong, unique shared secrets for each TACACS+ server to secure communication.
2. **Configure Multiple Servers**: Add redundant TACACS+ servers to ensure high availability for authentication services.
3. **Prefer CHAP over PAP**: Use CHAP for enhanced password security as PAP transmits passwords in cleartext.
4. **Enable Single Connection**: Use `--use-single-connection` to maintain a persistent TCP connection for improved performance when supported by your TACACS+ server.
5. **Tune Timeout Values**: Set appropriate timeout values (1-30 seconds) based on your network latency to balance responsiveness and reliability.
6. **Backup Before Changes**: Export existing profiles before making modifications to enable quick rollback if needed.
