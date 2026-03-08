# BGP Redistribution Profile

BGP redistribution profiles control how routes from other protocols (OSPF, static, connected) are redistributed into BGP.

## Set BGP Redistribution Profile

```bash
scm set network bgp-redistribution-profile NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name (positional) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--ipv4-json TEXT` | IPv4 redistribution config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set network bgp-redistribution-profile my-redist \
    --folder Texas \
    --ipv4-json '{"unicast": {"connected": {"enable": true}}}'
```

## Show / Delete / Load / Backup

```bash
scm show network bgp-redistribution-profile --folder Texas
scm delete network bgp-redistribution-profile my-redist --folder Texas
scm load network bgp-redistribution-profile --file bgp-redist.yaml --folder Texas
scm backup network bgp-redistribution-profile --folder Texas
```
