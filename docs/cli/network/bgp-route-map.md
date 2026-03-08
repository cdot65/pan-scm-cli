# BGP Route Map

BGP route maps define match conditions and set actions for BGP route policy processing.

## Set BGP Route Map

```bash
scm set network bgp-route-map NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Route map name (positional) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--route-map-json TEXT` | Route map entries as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set network bgp-route-map my-route-map \
    --folder Texas \
    --route-map-json '[{"name": "rule1", "action": "permit", "match": {"as_path": "my-as-path"}}]'
```

## Show / Delete / Load / Backup

```bash
scm show network bgp-route-map --folder Texas
scm delete network bgp-route-map my-route-map --folder Texas
scm load network bgp-route-map --file route-maps.yaml --folder Texas
scm backup network bgp-route-map --folder Texas
```
