# Authentication Rule

Authentication rules enforce user authentication before allowing access to network resources.

## Set Authentication Rule

```bash
scm set security authentication-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--name TEXT` | Rule name | Yes |
| `--rulebase TEXT` | Rulebase (pre, post, default) | No |
| `--description TEXT` | Description | No |
| `--source-zones TEXT` | Source zones | No |
| `--destination-zones TEXT` | Destination zones | No |
| `--service TEXT` | Services | No |
| `--category TEXT` | URL categories | No |
| `--authentication-enforcement TEXT` | Authentication profile | No |
| `--disabled` | Disable the rule | No |
| `--tags TEXT` | Tags | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set security authentication-rule --folder Texas --name auth-web \
    --source-zones trust --destination-zones untrust \
    --authentication-enforcement my-auth-profile
```

## Show / Delete / Load / Backup

```bash
scm show security authentication-rule --folder Texas
scm delete security authentication-rule --folder Texas --name auth-web
scm load security authentication-rule --file auth-rules.yaml --folder Texas
scm backup security authentication-rule --folder Texas
```
