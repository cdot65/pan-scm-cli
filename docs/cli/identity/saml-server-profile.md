# SAML Server Profile

SAML server profiles configure SAML 2.0 Identity Provider connections for single sign-on authentication.

## Set SAML Server Profile

```bash
scm set identity saml-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder scope | No* |
| `--snippet TEXT` | Snippet scope | No* |
| `--device TEXT` | Device scope | No* |
| `--name TEXT` | Profile name | Yes |
| `--entity-id TEXT` | Entity ID | Yes |
| `--certificate TEXT` | Certificate name | Yes |
| `--sso-url TEXT` | Single Sign-On URL | Yes |
| `--sso-bindings TEXT` | SSO binding type (post, redirect) | Yes |
| `--slo-bindings TEXT` | SLO binding type (post, redirect) | No |
| `--max-clock-skew INT` | Maximum clock skew in seconds (1-900) | No |
| `--validate-idp-certificate` | Validate IDP certificate | No |
| `--want-auth-requests-signed` | Want auth requests signed | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set identity saml-server-profile --folder Texas --name corp-saml \
    --entity-id "https://idp.example.com" --certificate idp-cert \
    --sso-url "https://idp.example.com/sso" --sso-bindings post
```

## Show / Delete / Load / Backup

```bash
scm show identity saml-server-profile --folder Texas --list
scm show identity saml-server-profile --folder Texas --name corp-saml
scm delete identity saml-server-profile --folder Texas --name corp-saml
scm load identity saml-server-profile --file saml.yaml
scm backup identity saml-server-profile --folder Texas
```
