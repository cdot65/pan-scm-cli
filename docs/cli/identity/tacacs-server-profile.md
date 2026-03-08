# TACACS+ Server Profile

TACACS+ server profiles configure TACACS+ servers for authentication, authorization, and accounting.

## Set TACACS+ Server Profile

```bash
scm set identity tacacs-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder scope | No* |
| `--snippet TEXT` | Snippet scope | No* |
| `--device TEXT` | Device scope | No* |
| `--name TEXT` | Profile name | Yes |
| `--servers TEXT` | Server list as JSON | No |
| `--protocol TEXT` | Protocol type (CHAP, PAP) | No |
| `--timeout INT` | Timeout in seconds (1-30) | No |
| `--use-single-connection` | Use single connection | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set identity tacacs-server-profile --folder Texas --name corp-tacacs \
    --servers '[{"name": "tac1", "address": "10.0.0.1", "port": 49, "secret": "s3cret"}]' \
    --protocol CHAP --timeout 5
```

## Show / Delete / Load / Backup

```bash
scm show identity tacacs-server-profile --folder Texas --list
scm show identity tacacs-server-profile --folder Texas --name corp-tacacs
scm delete identity tacacs-server-profile --folder Texas --name corp-tacacs
scm load identity tacacs-server-profile --file tacacs.yaml
scm backup identity tacacs-server-profile --folder Texas
```
