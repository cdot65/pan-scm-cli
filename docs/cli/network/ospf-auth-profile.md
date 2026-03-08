# OSPF Auth Profile

OSPF auth profiles define authentication settings for OSPF neighbor relationships, supporting simple password and MD5 authentication.

## Set OSPF Auth Profile

```bash
scm set network ospf-auth-profile NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name (positional) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--password TEXT` | Simple password authentication | No |
| `--md5-json TEXT` | MD5 authentication keys as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set network ospf-auth-profile my-ospf-auth \
    --folder Texas \
    --password "ospf-secret"

$ scm set network ospf-auth-profile my-ospf-md5 \
    --folder Texas \
    --md5-json '[{"key_id": 1, "key": "md5-key"}]'
```

## Show / Delete / Load / Backup

```bash
scm show network ospf-auth-profile --folder Texas
scm delete network ospf-auth-profile my-ospf-auth --folder Texas
scm load network ospf-auth-profile --file ospf-auth.yaml --folder Texas
scm backup network ospf-auth-profile --folder Texas
```
