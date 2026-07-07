# Decryption Profile

Decryption profiles configure SSL/TLS inspection settings for three proxy types: SSL Forward Proxy (outbound), SSL Inbound Proxy (inbound), and SSL No Proxy (bypass). The `scm` CLI provides commands to create, update, delete, and load decryption profiles.

## Overview

The `decryption-profile` commands allow you to:

- Create decryption profiles with SSL/TLS proxy configurations
- Update existing profile settings including protocol versions and cipher suites
- Delete profiles that are no longer needed
- Bulk import profiles from YAML files
- Export profiles for backup or migration

## Proxy Types

Decryption profiles support three proxy types:

| Proxy Type | Direction | Description |
| --- | --- | --- |
| SSL Forward Proxy | Outbound | Decrypt outbound SSL/TLS traffic for inspection |
| SSL Inbound Proxy | Inbound | Decrypt inbound SSL/TLS traffic to internal servers |
| SSL No Proxy | Bypass | Define certificate handling without decryption |

## Set Decryption Profile

Create or update a decryption profile.

### Syntax

```bash
scm set security decryption-profile NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--description TEXT` | Profile description | No |
| `--ssl-forward-proxy TEXT` | SSL forward proxy settings as JSON | No |
| `--ssl-inbound-proxy TEXT` | SSL inbound proxy settings as JSON | No |
| `--ssl-no-proxy TEXT` | SSL no proxy settings as JSON | No |
| `--ssl-protocol-settings TEXT` | SSL protocol settings as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create SSL Forward Proxy Profile

```bash
$ scm set security decryption-profile ssl-forward \
    --folder Texas \
    --ssl-forward-proxy '{"block_expired_certificate": true, "block_untrusted_issuer": true}'
---> 100%
Created decryption profile: ssl-forward in folder Texas
```

#### Create Profile with Protocol Settings

```bash
$ scm set security decryption-profile custom-decrypt \
    --folder Texas \
    --ssl-forward-proxy '{"block_expired_certificate": true}' \
    --ssl-protocol-settings '{"min_version": "tls1-2", "max_version": "tls1-3"}'
---> 100%
Created decryption profile: custom-decrypt in folder Texas
```

#### Create No-Decrypt Profile

```bash
$ scm set security decryption-profile no-decrypt \
    --folder Texas \
    --ssl-no-proxy '{"block_expired_certificate": false}'
---> 100%
Created decryption profile: no-decrypt in folder Texas
```

## Delete Decryption Profile

Delete a decryption profile from SCM.

### Syntax

```bash
scm delete security decryption-profile NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name to delete | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete security decryption-profile ssl-forward \
    --folder Texas \
    --force
---> 100%
Deleted decryption profile: ssl-forward from folder Texas
```

## Load Decryption Profile

Load multiple decryption profiles from a YAML file.

### Syntax

```bash
scm load security decryption-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing profile definitions | Yes |
| `--folder TEXT` | Override folder location for all profiles | No |
| `--snippet TEXT` | Override snippet location for all profiles | No |
| `--device TEXT` | Override device location for all profiles | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
decryption_profiles:
  - name: ssl-forward
    folder: Texas
    ssl_forward_proxy:
      block_expired_certificate: true
      block_untrusted_issuer: true

  - name: custom-decrypt
    folder: Texas
    ssl_forward_proxy:
      block_expired_certificate: true
    ssl_protocol_settings:
      min_version: "tls1-2"
      max_version: "tls1-3"
```

### Examples

#### Load with Original Locations

```bash
$ scm load security decryption-profile \
    --file decrypt-profiles.yaml
---> 100%
✓ Loaded decryption profile: ssl-forward
✓ Loaded decryption profile: custom-decrypt

Successfully loaded 2 out of 2 decryption profiles from 'decrypt-profiles.yaml'
```

#### Load with Folder Override

```bash
$ scm load security decryption-profile \
    --file decrypt-profiles.yaml \
    --folder Austin
---> 100%
✓ Loaded decryption profile: ssl-forward
✓ Loaded decryption profile: custom-decrypt

Successfully loaded 2 out of 2 decryption profiles from 'decrypt-profiles.yaml'
```

:::note
When using container override options (--folder, --snippet, --device), all profiles
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show Decryption Profile

Display decryption profile objects.

### Syntax

```bash
scm show security decryption-profile [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name to display; omit to list all | No |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--output, -o [table\|json\|yaml]` | Output format (default: table) | No |
| `--max-results INTEGER` | Maximum number of results to display | No |

\* One of --folder, --snippet, or --device is required.

:::note
When no `NAME` is specified, all items are listed by default.
:::

### Examples

#### Show Specific Profile

```bash
$ scm show security decryption-profile ssl-forward \
    --folder Texas
---> 100%
Decryption Profile: ssl-forward
  Location: Folder 'Texas'
  SSL Forward Proxy:
    Block Expired Certificate: true
    Block Untrusted Issuer: true
```

#### List All Profiles (Default Behavior)

```bash
$ scm show security decryption-profile --folder Texas
---> 100%
Decryption Profiles in folder 'Texas':
------------------------------------------------------------
Name: ssl-forward
  SSL Forward Proxy: configured
------------------------------------------------------------
Name: custom-decrypt
  SSL Forward Proxy: configured
  SSL Protocol Settings: TLS 1.2 - TLS 1.3
------------------------------------------------------------
```

## Backup Decryption Profiles

Backup all decryption profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup security decryption-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup profiles from | No\* |
| `--snippet TEXT` | Snippet to backup profiles from | No\* |
| `--device TEXT` | Device to backup profiles from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup security decryption-profile --folder Texas
---> 100%
Successfully backed up 3 decryption profiles to decryption_profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup security decryption-profile \
    --folder Texas \
    --file texas-decrypt-profiles.yaml
---> 100%
Successfully backed up 3 decryption profiles to texas-decrypt-profiles.yaml
```

## Best Practices

1. **Enforce TLS 1.2 Minimum**: Use `--ssl-protocol-settings` to set `min_version` to `tls1-2` to prevent downgrade attacks.
2. **Block Expired Certificates**: Enable `block_expired_certificate` in forward proxy settings to prevent connections to servers with invalid certificates.
3. **Separate Profiles by Use Case**: Create distinct profiles for forward proxy, inbound proxy, and no-proxy scenarios rather than combining settings.
4. **Use JSON Input Carefully**: Validate JSON strings before passing them to `--ssl-forward-proxy` and related options to avoid configuration errors.
5. **Backup Before Changes**: Always backup existing profiles before making bulk modifications via load commands.
