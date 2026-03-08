# Authentication Profile

Authentication profiles define how users authenticate, supporting LDAP, RADIUS, Kerberos, SAML, and other methods.

## Set Authentication Profile

```bash
scm set identity authentication-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder scope | No* |
| `--snippet TEXT` | Snippet scope | No* |
| `--device TEXT` | Device scope | No* |
| `--name TEXT` | Profile name | Yes |
| `--method TEXT` | Authentication method as JSON | No |
| `--user-domain TEXT` | User domain | No |
| `--username-modifier TEXT` | Username modifier pattern | No |
| `--lockout TEXT` | Lockout configuration as JSON | No |
| `--allow-list TEXT` | Allow list entries | No |
| `--multi-factor-auth TEXT` | Multi-factor auth config as JSON | No |
| `--single-sign-on TEXT` | SSO config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set identity authentication-profile --folder Texas --name my-auth \
    --method '{"ldap": {"server_profile": "corp-ldap", "login_attribute": "sAMAccountName"}}'
```

## Show / Delete / Load / Backup

```bash
scm show identity authentication-profile --folder Texas
scm delete identity authentication-profile --folder Texas --name my-auth
scm load identity authentication-profile --file auth-profiles.yaml
scm backup identity authentication-profile --folder Texas
```
