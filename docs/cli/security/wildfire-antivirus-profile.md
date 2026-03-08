# WildFire Antivirus Profile

WildFire antivirus profiles configure file forwarding to WildFire for cloud-based malware analysis and prevention.

## Set WildFire Antivirus Profile

```bash
scm set security wildfire-antivirus-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--name TEXT` | Profile name | Yes |
| `--description TEXT` | Profile description | No |
| `--rules TEXT` | Rules configuration as JSON | No |
| `--packet-capture / --no-packet-capture` | Enable packet capture | No |

\* One of --folder, --snippet, or --device is required.

### Examples

```bash
# Create basic profile with default rule
$ scm set security wildfire-antivirus-profile --folder Texas --name wf-basic \
    --description "Basic WildFire profile"

# Create profile with custom rules
$ scm set security wildfire-antivirus-profile --folder Texas --name wf-custom \
    --rules '[{"name":"Forward All","direction":"both","analysis":"public-cloud","application":["any"],"file_type":["any"]}]'

# Create profile with packet capture
$ scm set security wildfire-antivirus-profile --folder Texas --name wf-capture \
    --packet-capture
```

## Show / Delete / Load / Backup

```bash
scm show security wildfire-antivirus-profile --folder Texas
scm delete security wildfire-antivirus-profile --folder Texas --name wf-basic
scm load security wildfire-antivirus-profile --file wildfire.yaml --folder Texas
scm backup security wildfire-antivirus-profile --folder Texas
```
