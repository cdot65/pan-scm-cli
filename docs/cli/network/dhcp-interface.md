# DHCP Interface

DHCP interfaces configure DHCP server or relay functionality on network interfaces.

## Set DHCP Interface

```bash
scm set network dhcp-interface NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Interface name (positional) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--server-json TEXT` | DHCP server config as JSON | No |
| `--relay-json TEXT` | DHCP relay config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set network dhcp-interface ethernet1/1 \
    --folder Texas \
    --server-json '{"ip_pool": [{"name": "pool1", "start_ip": "10.0.0.100", "end_ip": "10.0.0.200"}]}'
```

## Show / Delete / Load / Backup

```bash
scm show network dhcp-interface --folder Texas
scm delete network dhcp-interface ethernet1/1 --folder Texas
scm load network dhcp-interface --file dhcp.yaml --folder Texas
scm backup network dhcp-interface --folder Texas
```
