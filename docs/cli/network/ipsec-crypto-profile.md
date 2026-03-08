# IPsec Crypto Profile

IPsec crypto profiles define encryption and authentication parameters for IPsec Phase 2 (ESP) negotiations. The `scm` CLI provides commands to create, update, delete, and load IPsec crypto profiles.

## Overview

The `ipsec-crypto-profile` commands allow you to:

- Create IPsec crypto profiles with ESP encryption and authentication settings
- Update existing IPsec crypto profile configurations
- Delete IPsec crypto profiles that are no longer needed
- Bulk import IPsec crypto profiles from YAML files
- Export IPsec crypto profiles for backup or migration

## Set IPsec Crypto Profile

Create or update an IPsec crypto profile.

### Syntax

```bash
scm set network ipsec-crypto-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Profile name | Yes |
| `--folder TEXT` | Folder location | Yes |
| `--esp-encryption TEXT` | ESP encryption algorithms (aes-256-cbc, aes-128-cbc, etc.) | Yes |
| `--esp-authentication TEXT` | ESP authentication algorithms (sha256, sha384, sha512, sha1, md5) | Yes |
| `--dh-group TEXT` | DH group for PFS (group14, group19, group20, no-pfs) | Yes |
| `--lifetime-seconds INT` | Lifetime in seconds | No |
| `--lifetime-hours INT` | Lifetime in hours | No |

### Examples

#### Create an IPsec Crypto Profile

```bash
$ scm set network ipsec-crypto-profile \
    --folder Texas \
    --name my-ipsec-profile \
    --esp-encryption aes-256-cbc \
    --esp-authentication sha256 \
    --dh-group group14
---> 100%
Created IPsec crypto profile: my-ipsec-profile in folder Texas
```

#### Create a Profile with Custom Lifetime

```bash
$ scm set network ipsec-crypto-profile \
    --folder Texas \
    --name short-lived-profile \
    --esp-encryption aes-256-cbc \
    --esp-authentication sha384 \
    --dh-group group19 \
    --lifetime-hours 1
---> 100%
Created IPsec crypto profile: short-lived-profile in folder Texas
```

## Delete IPsec Crypto Profile

Delete an IPsec crypto profile from SCM.

### Syntax

```bash
scm delete network ipsec-crypto-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Profile name | Yes |
| `--folder TEXT` | Folder location | Yes |

### Example

```bash
$ scm delete network ipsec-crypto-profile --folder Texas --name my-ipsec-profile
---> 100%
Deleted IPsec crypto profile: my-ipsec-profile from folder Texas
```

## Load IPsec Crypto Profile

Load multiple IPsec crypto profiles from a YAML file.

### Syntax

```bash
scm load network ipsec-crypto-profile [OPTIONS]
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
ipsec_crypto_profiles:
  - name: standard-ipsec
    folder: Texas
    esp:
      encryption:
        - aes-256-cbc
      authentication:
        - sha256
    dh_group: group14
    lifetime_hours: 8

  - name: high-security-ipsec
    folder: Texas
    esp:
      encryption:
        - aes-256-cbc
      authentication:
        - sha384
    dh_group: group19
    lifetime_hours: 4
```

### Examples

#### Load with Original Locations

```bash
$ scm load network ipsec-crypto-profile --file ipsec-profiles.yml
---> 100%
✓ Loaded IPsec crypto profile: standard-ipsec
✓ Loaded IPsec crypto profile: high-security-ipsec

Successfully loaded 2 out of 2 IPsec crypto profiles from 'ipsec-profiles.yml'
```

#### Load with Folder Override

```bash
$ scm load network ipsec-crypto-profile --file ipsec-profiles.yml --folder Austin
---> 100%
✓ Loaded IPsec crypto profile: standard-ipsec
✓ Loaded IPsec crypto profile: high-security-ipsec

Successfully loaded 2 out of 2 IPsec crypto profiles from 'ipsec-profiles.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all IPsec crypto profiles
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show IPsec Crypto Profile

Display IPsec crypto profile objects.

### Syntax

```bash
scm show network ipsec-crypto-profile [OPTIONS]
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

#### Show Specific IPsec Crypto Profile

```bash
$ scm show network ipsec-crypto-profile --folder Texas --name my-ipsec-profile
---> 100%
IPsec Crypto Profile: my-ipsec-profile
  Location: Folder 'Texas'
  ESP Encryption: aes-256-cbc
  ESP Authentication: sha256
  DH Group: group14
```

#### List All IPsec Crypto Profiles (Default Behavior)

```bash
$ scm show network ipsec-crypto-profile --folder Texas
---> 100%
IPsec crypto profiles in folder 'Texas':
------------------------------------------------------------
Name: standard-ipsec
  ESP Encryption: aes-256-cbc
  DH Group: group14
------------------------------------------------------------
Name: high-security-ipsec
  ESP Encryption: aes-256-cbc
  DH Group: group19
------------------------------------------------------------
```

## Backup IPsec Crypto Profiles

Backup all IPsec crypto profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network ipsec-crypto-profile [OPTIONS]
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
$ scm backup network ipsec-crypto-profile --folder Texas
---> 100%
Successfully backed up 5 IPsec crypto profiles to ipsec_crypto_profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network ipsec-crypto-profile --folder Texas --file texas-ipsec-profiles.yaml
---> 100%
Successfully backed up 5 IPsec crypto profiles to texas-ipsec-profiles.yaml
```

## Best Practices

1. **Enable PFS**: Use a DH group (group14 or higher) for Perfect Forward Secrecy rather than no-pfs.
2. **Use Strong Encryption**: Prefer aes-256-cbc with sha256 or higher authentication for production tunnels.
3. **Match IKE and IPsec Profiles**: Ensure IPsec profile security level is consistent with the paired IKE crypto profile.
4. **Set Appropriate Lifetimes**: Shorter lifetimes increase security but may impact performance during rekeying.
5. **Backup Before Changes**: Always backup existing profiles before making bulk modifications.
