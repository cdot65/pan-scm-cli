# Route Access List

Route access lists filter routes based on network prefixes for use with routing protocols.

## Set Route Access List

```bash
scm set network route-access-list NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Access list name (positional) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--description TEXT` | Description | No |
| `--type-json TEXT` | Access list type config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set network route-access-list my-acl \
    --folder Texas \
    --type-json '{"prefix": [{"name": 1, "network": "10.0.0.0/8", "action": "permit"}]}'
```

## Show / Delete / Load / Backup

```bash
scm show network route-access-list --folder Texas
scm delete network route-access-list my-acl --folder Texas
scm load network route-access-list --file access-lists.yaml --folder Texas
scm backup network route-access-list --folder Texas
```
