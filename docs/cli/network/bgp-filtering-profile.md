# BGP Filtering Profile

BGP filtering profiles define route filtering rules applied to BGP peer sessions for controlling route advertisements.

## Set BGP Filtering Profile

```bash
scm set network bgp-filtering-profile NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name (positional) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--ipv4-json TEXT` | IPv4 filtering config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set network bgp-filtering-profile my-filter \
    --folder Texas \
    --ipv4-json '{"unicast": {"filter_in": "my-prefix-list"}}'
```

## Show / Delete / Load / Backup

```bash
scm show network bgp-filtering-profile --folder Texas
scm delete network bgp-filtering-profile my-filter --folder Texas
scm load network bgp-filtering-profile --file bgp-filters.yaml --folder Texas
scm backup network bgp-filtering-profile --folder Texas
```
