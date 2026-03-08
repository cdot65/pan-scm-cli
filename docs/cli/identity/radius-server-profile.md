# RADIUS Server Profile

RADIUS server profiles configure RADIUS servers for authentication, authorization, and accounting (AAA).

## Set RADIUS Server Profile

```bash
scm set identity radius-server-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder scope | No* |
| `--snippet TEXT` | Snippet scope | No* |
| `--device TEXT` | Device scope | No* |
| `--name TEXT` | Profile name | Yes |
| `--servers TEXT` | Server list as JSON | No |
| `--protocol TEXT` | Protocol config as JSON | No |
| `--timeout INT` | Timeout in seconds (1-120) | No |
| `--retries INT` | Number of retries (1-5) | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set identity radius-server-profile --folder Texas --name corp-radius \
    --servers '[{"name": "rad1", "ip_address": "10.0.0.1", "port": 1812, "secret": "s3cret"}]' \
    --protocol '{"CHAP": {}}' --timeout 5 --retries 3
```

## Show / Delete / Load / Backup

```bash
scm show identity radius-server-profile --folder Texas --list
scm show identity radius-server-profile --folder Texas --name corp-radius
scm delete identity radius-server-profile --folder Texas --name corp-radius
scm load identity radius-server-profile --file radius.yaml
scm backup identity radius-server-profile --folder Texas
```
