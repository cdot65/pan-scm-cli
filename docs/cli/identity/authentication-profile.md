# Authentication Profile

Authentication profiles define how users authenticate to Palo Alto Networks Strata Cloud Manager, supporting LDAP, RADIUS, Kerberos, SAML, and other methods. The `scm` CLI provides commands to create, update, delete, and bulk manage authentication profiles.

## Overview

The `authentication-profile` commands allow you to:

- Create authentication profiles with various authentication methods
- Update existing profile configurations including lockout and MFA settings
- Delete profiles that are no longer needed
- Bulk import profiles from YAML files
- Export profiles for backup or migration

## Set Authentication Profile

Create or update an authentication profile.

### Syntax

```bash
scm set identity authentication-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Profile name | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--method TEXT` | Authentication method as JSON | No |
| `--user-domain TEXT` | User domain | No |
| `--username-modifier TEXT` | Username modifier pattern | No |
| `--lockout TEXT` | Lockout configuration as JSON | No |
| `--allow-list TEXT` | Allow list entries | No |
| `--multi-factor-auth TEXT` | Multi-factor auth configuration as JSON | No |
| `--single-sign-on TEXT` | SSO configuration as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create LDAP Authentication Profile

```bash
$ scm set identity authentication-profile \
    --folder Texas \
    --name corp-ldap-auth \
    --method '{"ldap": {"server_profile": "corp-ldap", "login_attribute": "sAMAccountName"}}' \
    --user-domain "example.com"
---> 100%
Created authentication-profile: corp-ldap-auth in folder Texas
```

#### Create RADIUS Authentication Profile with Lockout

```bash
$ scm set identity authentication-profile \
    --folder Texas \
    --name corp-radius-auth \
    --method '{"radius": {"server_profile": "corp-radius"}}' \
    --lockout '{"failed_attempts": 5, "lockout_time": 30}'
---> 100%
Created authentication-profile: corp-radius-auth in folder Texas
```

#### Create SAML Profile with MFA

```bash
$ scm set identity authentication-profile \
    --folder Texas \
    --name corp-saml-mfa \
    --method '{"saml_idp": {"server_profile": "corp-saml"}}' \
    --multi-factor-auth '{"mfa_enable": true, "factors": ["okta-otp"]}' \
    --single-sign-on '{"realm": "example.com"}'
---> 100%
Created authentication-profile: corp-saml-mfa in folder Texas
```

## Delete Authentication Profile

Delete an authentication profile from SCM.

### Syntax

```bash
scm delete identity authentication-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Profile name | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete identity authentication-profile \
    --folder Texas \
    --name corp-ldap-auth
---> 100%
Deleted authentication-profile: corp-ldap-auth from folder Texas
```

## Load Authentication Profile

Load multiple authentication profiles from a YAML file.

### Syntax

```bash
scm load identity authentication-profile [OPTIONS]
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
authentication_profiles:
  - name: corp-ldap-auth
    folder: Texas
    method:
      ldap:
        server_profile: corp-ldap
        login_attribute: sAMAccountName
    user_domain: example.com

  - name: corp-radius-auth
    folder: Texas
    method:
      radius:
        server_profile: corp-radius
    lockout:
      failed_attempts: 5
      lockout_time: 30
```

### Examples

#### Load with Original Locations

```bash
$ scm load identity authentication-profile --file auth-profiles.yml
---> 100%
✓ Loaded authentication-profile: corp-ldap-auth
✓ Loaded authentication-profile: corp-radius-auth

Successfully loaded 2 out of 2 authentication-profiles from 'auth-profiles.yml'
```

#### Load with Folder Override

```bash
$ scm load identity authentication-profile \
    --file auth-profiles.yml \
    --folder Austin
---> 100%
✓ Loaded authentication-profile: corp-ldap-auth
✓ Loaded authentication-profile: corp-radius-auth

Successfully loaded 2 out of 2 authentication-profiles from 'auth-profiles.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all authentication
    profiles will be loaded into the specified container, ignoring the container specified in
    the YAML file.

## Show Authentication Profile

Display authentication profile objects.

### Syntax

```bash
scm show identity authentication-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Profile name | No |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |

\* One of --folder, --snippet, or --device is required.

!!! note
    When no `--name` is specified, all items are listed by default.

### Examples

#### Show Specific Authentication Profile

```bash
$ scm show identity authentication-profile \
    --folder Texas \
    --name corp-ldap-auth
---> 100%
Authentication Profile: corp-ldap-auth
  Location: Folder 'Texas'
  Method: LDAP
  Server Profile: corp-ldap
  User Domain: example.com
```

#### List All Authentication Profiles (Default Behavior)

```bash
$ scm show identity authentication-profile --folder Texas
---> 100%
Authentication Profiles in folder 'Texas':
------------------------------------------------------------
Name: corp-ldap-auth
  Method: LDAP
  Server Profile: corp-ldap
------------------------------------------------------------
Name: corp-radius-auth
  Method: RADIUS
  Server Profile: corp-radius
------------------------------------------------------------
```

## Backup Authentication Profiles

Backup all authentication profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup identity authentication-profile [OPTIONS]
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
$ scm backup identity authentication-profile --folder Texas
---> 100%
Successfully backed up 5 authentication-profiles to authentication_profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup identity authentication-profile \
    --folder Texas \
    --file texas-auth-profiles.yaml
---> 100%
Successfully backed up 5 authentication-profiles to texas-auth-profiles.yaml
```

## Best Practices

1. **Use Descriptive Names**: Name profiles by their authentication method and purpose (e.g., `corp-ldap-auth`, `vpn-radius-auth`) for easy identification.
2. **Configure Lockout Policies**: Set failed attempt thresholds and lockout durations to protect against brute-force attacks.
3. **Enable Multi-Factor Authentication**: Add MFA factors to critical authentication profiles for enhanced security.
4. **Backup Before Changes**: Export existing profiles before making modifications to enable quick rollback if needed.
5. **Use YAML for Bulk Operations**: Manage multiple authentication profiles through YAML files to ensure consistency and repeatability.
