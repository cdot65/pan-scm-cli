# LDAP Server Profile

LDAP server profiles configure directory server connections for user authentication and group lookups.

## Set LDAP Server Profile

```bash
scm set identity ldap-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder scope | No* |
| `--snippet TEXT` | Snippet scope | No* |
| `--device TEXT` | Device scope | No* |
| `--name TEXT` | Profile name | Yes |
| `--servers TEXT` | Server list as JSON | No |
| `--base TEXT` | Base distinguished name | No |
| `--bind-dn TEXT` | Bind distinguished name | No |
| `--bind-password TEXT` | Bind password | No |
| `--ldap-type TEXT` | LDAP type (active-directory, e-directory, sun, other) | No |
| `--ssl` | Enable SSL | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set identity ldap-server-profile --folder Texas --name corp-ldap \
    --servers '[{"name": "ldap1", "address": "ldap.example.com", "port": 389}]' \
    --base "dc=example,dc=com" --ldap-type active-directory
```

## Show / Delete / Load / Backup

```bash
scm show identity ldap-server-profile --folder Texas --list
scm show identity ldap-server-profile --folder Texas --name corp-ldap
scm delete identity ldap-server-profile --folder Texas --name corp-ldap
scm load identity ldap-server-profile --file ldap.yaml
scm backup identity ldap-server-profile --folder Texas
```
