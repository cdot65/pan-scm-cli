# Kerberos Server Profile

Kerberos server profiles configure KDC (Key Distribution Center) servers for Kerberos authentication.

## Set Kerberos Server Profile

```bash
scm set identity kerberos-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder scope | No* |
| `--snippet TEXT` | Snippet scope | No* |
| `--device TEXT` | Device scope | No* |
| `--name TEXT` | Profile name | Yes |
| `--servers TEXT` | Server list as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set identity kerberos-server-profile --folder Texas --name corp-kerberos \
    --servers '[{"name": "kdc1", "host": "kdc1.example.com", "port": 88}]'
```

## Show / Delete / Load / Backup

```bash
scm show identity kerberos-server-profile --folder Texas --list
scm show identity kerberos-server-profile --folder Texas --name corp-kerberos
scm delete identity kerberos-server-profile --folder Texas --name corp-kerberos
scm load identity kerberos-server-profile --file kerberos.yaml
scm backup identity kerberos-server-profile --folder Texas
```
