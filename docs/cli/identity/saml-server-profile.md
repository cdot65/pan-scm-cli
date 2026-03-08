# SAML Server Profile

SAML server profiles configure SAML 2.0 Identity Provider connections for single sign-on authentication in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, and bulk manage SAML server profiles.

## Overview

The `saml-server-profile` commands allow you to:

- Create SAML server profiles with IdP connection settings
- Update existing profile configurations including SSO and SLO bindings
- Delete profiles that are no longer needed
- Bulk import profiles from YAML files
- Export profiles for backup or migration

## Set SAML Server Profile

Create or update a SAML server profile.

### Syntax

```bash
scm set identity saml-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Profile name | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--entity-id TEXT` | Entity ID of the IdP | Yes |
| `--certificate TEXT` | Certificate name for IdP verification | Yes |
| `--sso-url TEXT` | Single Sign-On URL | Yes |
| `--sso-bindings TEXT` | SSO binding type (post, redirect) | Yes |
| `--slo-bindings TEXT` | SLO binding type (post, redirect) | No |
| `--max-clock-skew INT` | Maximum clock skew in seconds (1-900) | No |
| `--validate-idp-certificate` | Validate IdP certificate | No |
| `--want-auth-requests-signed` | Require signed authentication requests | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create Basic SAML Server Profile

```bash
$ scm set identity saml-server-profile \
    --folder Texas \
    --name corp-saml \
    --entity-id "https://idp.example.com" \
    --certificate idp-cert \
    --sso-url "https://idp.example.com/sso" \
    --sso-bindings post
---> 100%
Created saml-server-profile: corp-saml in folder Texas
```

#### Create SAML Profile with SLO and Certificate Validation

```bash
$ scm set identity saml-server-profile \
    --folder Texas \
    --name secure-saml \
    --entity-id "https://idp.example.com" \
    --certificate idp-cert \
    --sso-url "https://idp.example.com/sso" \
    --sso-bindings post \
    --slo-bindings redirect \
    --validate-idp-certificate \
    --want-auth-requests-signed \
    --max-clock-skew 60
---> 100%
Created saml-server-profile: secure-saml in folder Texas
```

#### Create SAML Profile with Redirect Binding

```bash
$ scm set identity saml-server-profile \
    --folder Texas \
    --name redirect-saml \
    --entity-id "https://idp.example.com/redirect" \
    --certificate idp-redirect-cert \
    --sso-url "https://idp.example.com/sso/redirect" \
    --sso-bindings redirect
---> 100%
Created saml-server-profile: redirect-saml in folder Texas
```

## Delete SAML Server Profile

Delete a SAML server profile from SCM.

### Syntax

```bash
scm delete identity saml-server-profile [OPTIONS]
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
$ scm delete identity saml-server-profile \
    --folder Texas \
    --name corp-saml
---> 100%
Deleted saml-server-profile: corp-saml from folder Texas
```

## Load SAML Server Profile

Load multiple SAML server profiles from a YAML file.

### Syntax

```bash
scm load identity saml-server-profile [OPTIONS]
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
saml_server_profiles:
  - name: corp-saml
    folder: Texas
    entity_id: "https://idp.example.com"
    certificate: idp-cert
    sso_url: "https://idp.example.com/sso"
    sso_bindings: post

  - name: secure-saml
    folder: Texas
    entity_id: "https://idp.example.com"
    certificate: idp-cert
    sso_url: "https://idp.example.com/sso"
    sso_bindings: post
    slo_bindings: redirect
    validate_idp_certificate: true
    want_auth_requests_signed: true
    max_clock_skew: 60
```

### Examples

#### Load with Original Locations

```bash
$ scm load identity saml-server-profile --file saml.yml
---> 100%
✓ Loaded saml-server-profile: corp-saml
✓ Loaded saml-server-profile: secure-saml

Successfully loaded 2 out of 2 saml-server-profiles from 'saml.yml'
```

#### Load with Folder Override

```bash
$ scm load identity saml-server-profile \
    --file saml.yml \
    --folder Austin
---> 100%
✓ Loaded saml-server-profile: corp-saml
✓ Loaded saml-server-profile: secure-saml

Successfully loaded 2 out of 2 saml-server-profiles from 'saml.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all SAML server
    profiles will be loaded into the specified container, ignoring the container specified in
    the YAML file.

## Show SAML Server Profile

Display SAML server profile objects.

### Syntax

```bash
scm show identity saml-server-profile [OPTIONS]
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

#### Show Specific SAML Server Profile

```bash
$ scm show identity saml-server-profile \
    --folder Texas \
    --name corp-saml
---> 100%
SAML Server Profile: corp-saml
  Location: Folder 'Texas'
  Entity ID: https://idp.example.com
  SSO URL: https://idp.example.com/sso
  SSO Bindings: post
  Certificate: idp-cert
```

#### List All SAML Server Profiles (Default Behavior)

```bash
$ scm show identity saml-server-profile --folder Texas
---> 100%
SAML Server Profiles in folder 'Texas':
------------------------------------------------------------
Name: corp-saml
  Entity ID: https://idp.example.com
  SSO Bindings: post
------------------------------------------------------------
Name: secure-saml
  Entity ID: https://idp.example.com
  SSO Bindings: post
  SLO Bindings: redirect
  Validate IdP Certificate: Yes
------------------------------------------------------------
```

## Backup SAML Server Profiles

Backup all SAML server profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup identity saml-server-profile [OPTIONS]
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
$ scm backup identity saml-server-profile --folder Texas
---> 100%
Successfully backed up 3 saml-server-profiles to saml_server_profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup identity saml-server-profile \
    --folder Texas \
    --file texas-saml.yaml
---> 100%
Successfully backed up 3 saml-server-profiles to texas-saml.yaml
```

## Best Practices

1. **Validate IdP Certificates**: Enable certificate validation in production to prevent man-in-the-middle attacks on SAML assertions.
2. **Sign Authentication Requests**: Use the `--want-auth-requests-signed` flag for enhanced security in sensitive environments.
3. **Configure Clock Skew Tolerance**: Set an appropriate `--max-clock-skew` value to accommodate time differences between SP and IdP while minimizing replay attack windows.
4. **Use POST Bindings for Security**: Prefer POST bindings over redirect bindings as POST transmits SAML data in the request body rather than URL parameters.
5. **Backup Before Changes**: Export existing profiles before making modifications to enable quick rollback if needed.
6. **Configure SLO**: Set up Single Logout bindings to ensure users are properly logged out across all SAML-integrated services.
