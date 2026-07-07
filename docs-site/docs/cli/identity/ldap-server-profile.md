# LDAP Server Profile

LDAP server profiles configure directory server connections for user authentication and group lookups in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, and bulk manage LDAP server profiles.

## Overview

The `ldap-server-profile` commands allow you to:

- Create LDAP server profiles with directory server configurations
- Update existing profile settings including bind credentials and SSL options
- Delete profiles that are no longer needed
- Bulk import profiles from YAML files
- Export profiles for backup or migration

## LDAP Types

| Type | Description |
| --- | --- |
| `active-directory` | Microsoft Active Directory |
| `e-directory` | Novell eDirectory |
| `sun` | Sun/Oracle Directory Server |
| `other` | Other LDAP-compliant directory |

## Set LDAP Server Profile

Create or update an LDAP server profile.

### Syntax

```bash
scm set identity ldap-server-profile NAME [OPTIONS]
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
| `--servers TEXT` | Server list as JSON | No |
| `--base TEXT` | Base distinguished name | No |
| `--bind-dn TEXT` | Bind distinguished name | No |
| `--bind-password TEXT` | Bind password | No |
| `--ldap-type TEXT` | LDAP type (active-directory, e-directory, sun, other) | No |
| `--ssl` | Enable SSL | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create Active Directory Profile

```bash
$ scm set identity ldap-server-profile corp-ldap \
    --folder Texas \
    --servers '[{"name": "ldap1", "address": "ldap.example.com", "port": 389}]' \
    --base "dc=example,dc=com" \
    --ldap-type active-directory
---> 100%
Created ldap-server-profile: corp-ldap in folder Texas
```

#### Create LDAP Profile with SSL and Bind Credentials

```bash
$ scm set identity ldap-server-profile secure-ldap \
    --folder Texas \
    --servers '[{"name": "ldaps1", "address": "ldaps.example.com", "port": 636}]' \
    --base "dc=example,dc=com" \
    --bind-dn "cn=admin,dc=example,dc=com" \
    --bind-password "s3cret" \
    --ldap-type active-directory \
    --ssl
---> 100%
Created ldap-server-profile: secure-ldap in folder Texas
```

#### Create Profile with Multiple Servers

```bash
$ scm set identity ldap-server-profile corp-ldap-ha \
    --folder Texas \
    --servers '[{"name": "ldap1", "address": "ldap1.example.com", "port": 389}, {"name": "ldap2", "address": "ldap2.example.com", "port": 389}]' \
    --base "dc=example,dc=com" \
    --ldap-type active-directory
---> 100%
Created ldap-server-profile: corp-ldap-ha in folder Texas
```

## Delete LDAP Server Profile

Delete an LDAP server profile from SCM.

### Syntax

```bash
scm delete identity ldap-server-profile NAME [OPTIONS]
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
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete identity ldap-server-profile corp-ldap \
    --folder Texas \
    --force
---> 100%
Deleted ldap-server-profile: corp-ldap from folder Texas
```

## Load LDAP Server Profile

Load multiple LDAP server profiles from a YAML file.

### Syntax

```bash
scm load identity ldap-server-profile [OPTIONS]
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
ldap_server_profiles:
  - name: corp-ldap
    folder: Texas
    servers:
      - name: ldap1
        address: ldap.example.com
        port: 389
    base: "dc=example,dc=com"
    ldap_type: active-directory

  - name: secure-ldap
    folder: Texas
    servers:
      - name: ldaps1
        address: ldaps.example.com
        port: 636
    base: "dc=example,dc=com"
    bind_dn: "cn=admin,dc=example,dc=com"
    bind_password: "s3cret"
    ldap_type: active-directory
    ssl: true
```

### Examples

#### Load with Original Locations

```bash
$ scm load identity ldap-server-profile --file ldap.yml
---> 100%
✓ Loaded ldap-server-profile: corp-ldap
✓ Loaded ldap-server-profile: secure-ldap

Successfully loaded 2 out of 2 ldap-server-profiles from 'ldap.yml'
```

#### Load with Folder Override

```bash
$ scm load identity ldap-server-profile \
    --file ldap.yml \
    --folder Austin
---> 100%
✓ Loaded ldap-server-profile: corp-ldap
✓ Loaded ldap-server-profile: secure-ldap

Successfully loaded 2 out of 2 ldap-server-profiles from 'ldap.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all LDAP server
profiles will be loaded into the specified container, ignoring the container specified in
the YAML file.
:::

## Show LDAP Server Profile

Display LDAP server profile objects.

### Syntax

```bash
scm show identity ldap-server-profile [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name; omit to list all | No |

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

#### Show Specific LDAP Server Profile

```bash
$ scm show identity ldap-server-profile corp-ldap \
    --folder Texas
---> 100%
LDAP Server Profile: corp-ldap
  Location: Folder 'Texas'
  LDAP Type: active-directory
  Base DN: dc=example,dc=com
  SSL: No
  Servers:
    - ldap1 (ldap.example.com:389)
```

#### List All LDAP Server Profiles (Default Behavior)

```bash
$ scm show identity ldap-server-profile --folder Texas
---> 100%
LDAP Server Profiles in folder 'Texas':
------------------------------------------------------------
Name: corp-ldap
  LDAP Type: active-directory
  Servers: ldap1 (ldap.example.com:389)
------------------------------------------------------------
Name: secure-ldap
  LDAP Type: active-directory
  SSL: Yes
  Servers: ldaps1 (ldaps.example.com:636)
------------------------------------------------------------
```

## Backup LDAP Server Profiles

Backup all LDAP server profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup identity ldap-server-profile [OPTIONS]
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
$ scm backup identity ldap-server-profile --folder Texas
---> 100%
Successfully backed up 4 ldap-server-profiles to ldap_server_profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup identity ldap-server-profile \
    --folder Texas \
    --file texas-ldap.yaml
---> 100%
Successfully backed up 4 ldap-server-profiles to texas-ldap.yaml
```

## Best Practices

1. **Use SSL for Production**: Always enable SSL (port 636) for LDAP connections in production environments to protect credentials in transit.
2. **Configure Multiple Servers**: Add redundant LDAP servers to ensure high availability for authentication services.
3. **Use Service Accounts for Bind**: Create dedicated service accounts with minimal privileges for LDAP bind operations rather than using admin credentials.
4. **Choose the Correct LDAP Type**: Select the appropriate directory type (active-directory, e-directory, sun, other) to ensure proper attribute mapping.
5. **Backup Before Changes**: Export existing profiles before making modifications to enable quick rollback if needed.
6. **Protect Bind Credentials**: Store bind passwords securely and rotate them regularly according to your organization's security policy.
