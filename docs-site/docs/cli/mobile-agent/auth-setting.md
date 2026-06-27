# Auth Setting

Auth settings configure authentication methods for GlobalProtect mobile agent connections in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, and load auth settings.

## Overview

The `auth-setting` commands allow you to:

- Create auth settings with SAML, client certificate, or LDAP authentication
- Update existing auth setting configurations
- Delete auth settings that are no longer needed
- Bulk import auth settings from YAML files
- Export auth settings for backup or migration

## Authentication Types

Auth settings support the following authentication methods:

| Type | Description |
| --- | --- |
| `saml` | SAML-based single sign-on via an identity provider |
| `client-certificate` | Certificate-based authentication |
| `ldap` | LDAP directory-based authentication |

## Set Auth Setting

Create or update an auth setting.

### Syntax

```bash
scm set mobile-agent auth-setting [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes |
| `--name TEXT` | Name of the auth setting | Yes |
| `--description TEXT` | Description | No |
| `--auth-type TEXT` | Authentication type (saml, client-certificate, ldap) | No |
| `--os TEXT` | Operating system (Any, Windows, macOS, Linux, iOS, Android, ChromeOS) | No |
| `--max-user INT` | Maximum number of concurrent users | No |
| `--saml-idp TEXT` | SAML identity provider profile name | No |
| `--certificate-profile TEXT` | Certificate profile name | No |
| `--ldap-profile TEXT` | LDAP server profile name | No |

### Examples

#### Create SAML Auth Setting

```bash
$ scm set mobile-agent auth-setting \
    --folder "Mobile Users" \
    --name "saml-auth" \
    --auth-type saml \
    --saml-idp "okta-idp" \
    --os Any
---> 100%
Created auth setting: saml-auth in folder Mobile Users
```

#### Create LDAP Auth Setting

```bash
$ scm set mobile-agent auth-setting \
    --folder "Mobile Users" \
    --name "ldap-auth" \
    --auth-type ldap \
    --ldap-profile "corp-ldap" \
    --os Windows \
    --max-user 500
---> 100%
Created auth setting: ldap-auth in folder Mobile Users
```

#### Create Certificate Auth Setting

```bash
$ scm set mobile-agent auth-setting \
    --folder "Mobile Users" \
    --name "cert-auth" \
    --auth-type client-certificate \
    --certificate-profile "gp-cert-profile" \
    --os macOS
---> 100%
Created auth setting: cert-auth in folder Mobile Users
```

## Delete Auth Setting

Delete an auth setting from SCM.

### Syntax

```bash
scm delete mobile-agent auth-setting [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes |
| `--name TEXT` | Name of the auth setting to delete | Yes |
| `--force` | Skip confirmation prompt | No |

### Example

```bash
$ scm delete mobile-agent auth-setting \
    --folder "Mobile Users" \
    --name "saml-auth" \
    --force
---> 100%
Deleted auth setting: saml-auth from folder Mobile Users
```

## Load Auth Setting

Load multiple auth settings from a YAML file.

### Syntax

```bash
scm load mobile-agent auth-setting [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to the YAML file | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Simulate execution without applying changes | No |

### YAML File Format

```yaml
---
auth_settings:
  - name: saml-auth
    folder: "Mobile Users"
    auth_type: saml
    saml_idp: "okta-idp"
    os: Any

  - name: ldap-auth
    folder: "Mobile Users"
    auth_type: ldap
    ldap_profile: "corp-ldap"
    os: Windows
    max_user: 500
```

### Examples

#### Load with Original Locations

```bash
$ scm load mobile-agent auth-setting --file auth_settings.yml
---> 100%
✓ Loaded auth setting: saml-auth
✓ Loaded auth setting: ldap-auth

Successfully loaded 2 out of 2 auth settings from 'auth_settings.yml'
```

#### Load with Folder Override

```bash
$ scm load mobile-agent auth-setting \
    --file auth_settings.yml \
    --folder "Mobile Users"
---> 100%
✓ Loaded auth setting: saml-auth
✓ Loaded auth setting: ldap-auth

Successfully loaded 2 out of 2 auth settings from 'auth_settings.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all auth settings
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show Auth Setting

Display auth setting objects.

### Syntax

```bash
scm show mobile-agent auth-setting [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes |
| `--name TEXT` | Name of a specific auth setting | No |

:::note
When no `--name` is specified, all items are listed by default.
:::

### Examples

#### Show Specific Auth Setting

```bash
$ scm show mobile-agent auth-setting \
    --folder "Mobile Users" \
    --name "saml-auth"
---> 100%
Auth Setting: saml-auth
  Location: Folder 'Mobile Users'
  Auth Type: saml
  OS: Any
  SAML IDP: okta-idp
```

#### List All Auth Settings (Default Behavior)

```bash
$ scm show mobile-agent auth-setting --folder "Mobile Users"
---> 100%
Auth Settings in folder 'Mobile Users':
------------------------------------------------------------
Name: saml-auth
  Auth Type: saml
  OS: Any
------------------------------------------------------------
Name: ldap-auth
  Auth Type: ldap
  OS: Windows
------------------------------------------------------------
```

## Backup Auth Settings

Backup all auth settings from a specified location to a YAML file.

### Syntax

```bash
scm backup mobile-agent auth-setting [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--file TEXT` | Output file path | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup mobile-agent auth-setting --folder "Mobile Users"
---> 100%
Successfully backed up 5 auth settings to auth-setting-mobile-users.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup mobile-agent auth-setting \
    --folder "Mobile Users" \
    --file mobile-auth-backup.yaml
---> 100%
Successfully backed up 5 auth settings to mobile-auth-backup.yaml
```

## Best Practices

1. **Use Descriptive Names**: Name auth settings to reflect their authentication method and purpose, such as `saml-okta-prod` or `ldap-corp-windows`.
2. **Limit by OS When Possible**: Restrict auth settings to specific operating systems to enforce platform-appropriate authentication methods.
3. **Set Max User Limits**: Configure `--max-user` to prevent resource exhaustion from excessive concurrent connections.
4. **Backup Before Changes**: Always backup existing auth settings before making bulk modifications via load commands.
5. **Use Dry Run for Validation**: Test YAML configurations with `--dry-run` before applying changes to production environments.

## Related Topics

- [Agent Version](agent-version.md)
