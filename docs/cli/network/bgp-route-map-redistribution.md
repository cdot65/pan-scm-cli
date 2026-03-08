# BGP Route Map Redistribution

BGP route map redistributions define how routes from different source protocols are redistributed using route maps.

## Set BGP Route Map Redistribution

```bash
scm set network bgp-route-map-redistribution NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Name (positional) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--bgp-json TEXT` | BGP source protocol config as JSON | No |
| `--ospf-json TEXT` | OSPF source protocol config as JSON | No |
| `--connected-static-json TEXT` | Connected/Static source config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set network bgp-route-map-redistribution my-redist-map \
    --folder Texas \
    --connected-static-json '{"connected": {"route_map": "my-route-map"}}'
```

## Show / Delete / Load / Backup

```bash
scm show network bgp-route-map-redistribution --folder Texas
scm delete network bgp-route-map-redistribution my-redist-map --folder Texas
scm load network bgp-route-map-redistribution --file redist-maps.yaml --folder Texas
scm backup network bgp-route-map-redistribution --folder Texas
```
