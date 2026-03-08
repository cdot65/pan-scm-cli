# BGP Auth Profile

BGP auth profiles define authentication keys for BGP peer sessions.

## Set BGP Auth Profile

```bash
scm set network bgp-auth-profile NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name (positional) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--secret TEXT` | BGP authentication key | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set network bgp-auth-profile my-bgp-auth \
    --folder Texas \
    --secret "bgp-secret-key"
```

## Show / Delete / Load / Backup

```bash
scm show network bgp-auth-profile --folder Texas
scm delete network bgp-auth-profile my-bgp-auth --folder Texas
scm load network bgp-auth-profile --file bgp-auth.yaml --folder Texas
scm backup network bgp-auth-profile --folder Texas
```
