# Decryption Rule

Decryption rules define which traffic should be decrypted for inspection or bypassed.

## Set Decryption Rule

```bash
scm set security decryption-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--name TEXT` | Rule name | Yes |
| `--action TEXT` | Action (decrypt or no-decrypt) | Yes |
| `--rulebase TEXT` | Rulebase (pre, post, default) | No |
| `--description TEXT` | Description | No |
| `--source-zones TEXT` | Source zones | No |
| `--destination-zones TEXT` | Destination zones | No |
| `--profile TEXT` | Decryption profile | No |
| `--type TEXT` | Decryption type as JSON | No |
| `--disabled` | Disable the rule | No |
| `--tags TEXT` | Tags | No |

\* One of --folder, --snippet, or --device is required.

### Examples

```bash
# Create no-decrypt rule
$ scm set security decryption-rule --folder Texas --name no-decrypt-internal \
    --action no-decrypt --source-zones trust --destination-zones trust

# Create decrypt rule with SSL forward proxy
$ scm set security decryption-rule --folder Texas --name decrypt-outbound \
    --action decrypt --type '{"ssl_forward_proxy": {}}'
```

## Show / Delete / Load / Backup

```bash
scm show security decryption-rule --folder Texas
scm delete security decryption-rule --folder Texas --name no-decrypt-internal
scm load security decryption-rule --file decrypt-rules.yaml --folder Texas
scm backup security decryption-rule --folder Texas
```
