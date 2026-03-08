# BGP Address Family Profile

BGP address family profiles define address family configurations (IPv4 unicast/multicast) for BGP routing.

## Set BGP Address Family Profile

```bash
scm set network bgp-address-family-profile NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name (positional) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--ipv4-json TEXT` | IPv4 address family config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set network bgp-address-family-profile my-af-profile \
    --folder Texas \
    --ipv4-json '{"unicast": {"enable": true}}'
```

## Show / Delete / Load / Backup

```bash
scm show network bgp-address-family-profile --folder Texas
scm delete network bgp-address-family-profile my-af-profile --folder Texas
scm load network bgp-address-family-profile --file af-profiles.yaml --folder Texas
scm backup network bgp-address-family-profile --folder Texas
```
