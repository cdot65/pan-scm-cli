# Tunnel Interface

Tunnel interfaces are virtual interfaces used for VPN tunnels and encapsulation.

## Set Tunnel Interface

```bash
scm set network tunnel-interface NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Interface name (positional) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--comment TEXT` | Interface description | No |
| `--default-value TEXT` | Default interface (e.g. tunnel.1) | No |
| `--mtu INT` | MTU (576-9216) | No |
| `--ip-json TEXT` | Static IPs as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set network tunnel-interface tunnel.1 \
    --folder Texas \
    --ip-json '[{"name": "10.0.0.1/30"}]' \
    --comment "VPN tunnel"
```

## Show / Delete / Load / Backup

```bash
scm show network tunnel-interface --folder Texas
scm delete network tunnel-interface tunnel.1 --folder Texas
scm load network tunnel-interface --file tunnels.yaml --folder Texas
scm backup network tunnel-interface --folder Texas
```
