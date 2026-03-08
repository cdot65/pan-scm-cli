# Loopback Interface

Loopback interfaces are virtual interfaces used for management access, routing protocols, and NAT.

## Set Loopback Interface

```bash
scm set network loopback-interface NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Interface name (positional) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--comment TEXT` | Interface description | No |
| `--default-value TEXT` | Default interface (e.g. loopback.1) | No |
| `--mtu INT` | MTU (576-9216) | No |
| `--ip-json TEXT` | Static IPs as JSON | No |
| `--ipv6-json TEXT` | IPv6 config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set network loopback-interface loopback.1 \
    --folder Texas \
    --ip-json '[{"name": "10.0.0.1/32"}]' \
    --comment "Management loopback"
```

## Show / Delete / Load / Backup

```bash
scm show network loopback-interface --folder Texas
scm delete network loopback-interface loopback.1 --folder Texas
scm load network loopback-interface --file loopbacks.yaml --folder Texas
scm backup network loopback-interface --folder Texas
```
