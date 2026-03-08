# App Override Rule

App override rules force the firewall to identify specific traffic as a particular application, bypassing the App-ID engine.

## Set App Override Rule

```bash
scm set security app-override-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--name TEXT` | Rule name | Yes |
| `--application TEXT` | Application to override | Yes |
| `--port TEXT` | Port(s) for the rule | Yes |
| `--protocol TEXT` | Protocol (tcp or udp) | Yes |
| `--rulebase TEXT` | Rulebase (pre, post, default) | No |
| `--description TEXT` | Description | No |
| `--source-zones TEXT` | Source zones | No |
| `--destination-zones TEXT` | Destination zones | No |
| `--disabled` | Disable the rule | No |
| `--tags TEXT` | Tags | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set security app-override-rule --folder Texas --name override-https \
    --application ssl --port 8443 --protocol tcp
```

## Show / Delete / Load / Backup

```bash
scm show security app-override-rule --folder Texas
scm delete security app-override-rule --folder Texas --name override-https
scm load security app-override-rule --file app-overrides.yaml --folder Texas
scm backup security app-override-rule --folder Texas
```
