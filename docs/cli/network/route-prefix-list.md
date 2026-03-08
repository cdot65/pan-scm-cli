# Route Prefix List

Route prefix lists filter routes based on IP prefixes with optional length matching, used with BGP and OSPF route maps.

## Set Route Prefix List

```bash
scm set network route-prefix-list NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Prefix list name (positional) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--description TEXT` | Description | No |
| `--ipv4-json TEXT` | IPv4 prefix list config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set network route-prefix-list my-prefix-list \
    --folder Texas \
    --ipv4-json '[{"name": "rule1", "prefix": "10.0.0.0/8", "action": "permit", "ge": 16, "le": 24}]'
```

## Show / Delete / Load / Backup

```bash
scm show network route-prefix-list --folder Texas
scm delete network route-prefix-list my-prefix-list --folder Texas
scm load network route-prefix-list --file prefix-lists.yaml --folder Texas
scm backup network route-prefix-list --folder Texas
```
