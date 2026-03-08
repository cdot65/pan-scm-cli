# IKE Crypto Profile

IKE crypto profiles define encryption, authentication, and key exchange parameters for IKE Phase 1 negotiations. The `scm` CLI provides commands to create, update, delete, and load IKE crypto profiles.

## Overview

The `ike-crypto-profile` commands allow you to:

- Create IKE crypto profiles with encryption, hash, and DH group settings
- Update existing IKE crypto profile configurations
- Delete IKE crypto profiles that are no longer needed
- Bulk import IKE crypto profiles from YAML files
- Export IKE crypto profiles for backup or migration

## Set IKE Crypto Profile

Create or update an IKE crypto profile.

### Syntax

```bash
scm set network ike-crypto-profile NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name (positional) | Yes |
| `--hash TEXT` | Hash algorithms (sha256, sha384, sha512, sha1, md5) | Yes |
| `--dh-group TEXT` | DH groups (group1, group2, group5, group14, group19, group20) | Yes |
| `--encryption TEXT` | Encryption algorithms (aes-256-cbc, aes-128-cbc, etc.) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--lifetime-seconds INT` | Lifetime in seconds (180-65535) | No |
| `--lifetime-minutes INT` | Lifetime in minutes (3-65535) | No |
| `--lifetime-hours INT` | Lifetime in hours (1-65535) | No |
| `--lifetime-days INT` | Lifetime in days (1-365) | No |
| `--authentication-multiple INT` | IKEv2 SA reauthentication interval (0-50) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create an IKE Crypto Profile with Hours Lifetime

```bash
$ scm set network ike-crypto-profile my-ike-profile \
    --folder Texas \
    --hash sha256 \
    --dh-group group14 \
    --encryption aes-256-cbc \
    --lifetime-hours 8
---> 100%
Created IKE crypto profile: my-ike-profile in folder Texas
```

#### Create an IKE Crypto Profile with Seconds Lifetime

```bash
$ scm set network ike-crypto-profile quick-rekey \
    --folder Texas \
    --hash sha384 \
    --dh-group group19 \
    --encryption aes-256-cbc \
    --lifetime-seconds 28800
---> 100%
Created IKE crypto profile: quick-rekey in folder Texas
```

## Delete IKE Crypto Profile

Delete an IKE crypto profile from SCM.

### Syntax

```bash
scm delete network ike-crypto-profile NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete network ike-crypto-profile my-ike-profile --folder Texas
---> 100%
Deleted IKE crypto profile: my-ike-profile from folder Texas
```

## Load IKE Crypto Profile

Load multiple IKE crypto profiles from a YAML file.

### Syntax

```bash
scm load network ike-crypto-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--dry-run` | Preview changes without applying | No |

\* One of --folder, --snippet, or --device is required.

### YAML File Format

```yaml
---
ike_crypto_profiles:
  - name: standard-ike
    folder: Texas
    hash:
      - sha256
    dh_group:
      - group14
    encryption:
      - aes-256-cbc
    lifetime_hours: 8

  - name: high-security-ike
    folder: Texas
    hash:
      - sha384
    dh_group:
      - group19
    encryption:
      - aes-256-cbc
    lifetime_hours: 4
```

### Examples

#### Load with Original Locations

```bash
$ scm load network ike-crypto-profile --file ike-profiles.yml
---> 100%
✓ Loaded IKE crypto profile: standard-ike
✓ Loaded IKE crypto profile: high-security-ike

Successfully loaded 2 out of 2 IKE crypto profiles from 'ike-profiles.yml'
```

#### Load with Folder Override

```bash
$ scm load network ike-crypto-profile --file ike-profiles.yml --folder Austin
---> 100%
✓ Loaded IKE crypto profile: standard-ike
✓ Loaded IKE crypto profile: high-security-ike

Successfully loaded 2 out of 2 IKE crypto profiles from 'ike-profiles.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all IKE crypto profiles
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show IKE Crypto Profile

Display IKE crypto profile objects.

### Syntax

```bash
scm show network ike-crypto-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Name of a specific profile | No |

\* One of --folder, --snippet, or --device is required.

!!! note
    When no `--name` is specified, all items are listed by default.

### Examples

#### Show Specific IKE Crypto Profile

```bash
$ scm show network ike-crypto-profile --folder Texas --name my-ike-profile
---> 100%
IKE Crypto Profile: my-ike-profile
  Location: Folder 'Texas'
  Hash: sha256
  DH Group: group14
  Encryption: aes-256-cbc
  Lifetime: 8 hours
```

#### List All IKE Crypto Profiles (Default Behavior)

```bash
$ scm show network ike-crypto-profile --folder Texas
---> 100%
IKE crypto profiles in folder 'Texas':
------------------------------------------------------------
Name: standard-ike
  Hash: sha256
  Encryption: aes-256-cbc
------------------------------------------------------------
Name: high-security-ike
  Hash: sha384
  Encryption: aes-256-cbc
------------------------------------------------------------
```

## Backup IKE Crypto Profiles

Backup all IKE crypto profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network ike-crypto-profile [OPTIONS]
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
$ scm backup network ike-crypto-profile --folder Texas
---> 100%
Successfully backed up 5 IKE crypto profiles to ike_crypto_profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network ike-crypto-profile --folder Texas --file texas-ike-profiles.yaml
---> 100%
Successfully backed up 5 IKE crypto profiles to texas-ike-profiles.yaml
```

## Best Practices

1. **Use Strong Algorithms**: Prefer sha256 or higher for hash and aes-256-cbc for encryption in production environments.
2. **Select Appropriate DH Groups**: Use group14 or higher for adequate key exchange security.
3. **Set Reasonable Lifetimes**: Balance security (shorter lifetimes) with performance (fewer renegotiations).
4. **Standardize Profiles**: Create a small set of standard profiles and reuse them across IKE gateways.
5. **Backup Before Changes**: Always backup existing profiles before making bulk modifications.
