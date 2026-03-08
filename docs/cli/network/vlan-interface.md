# VLAN Interface

VLAN interfaces are virtual interfaces associated with VLAN tags for inter-VLAN routing.

## Set VLAN Interface

```bash
scm set network vlan-interface NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Interface name (positional) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--comment TEXT` | Interface description | No |
| `--default-value TEXT` | Default interface (e.g. vlan.100) | No |
| `--vlan-tag TEXT` | VLAN tag (1-4096) | No |
| `--mtu INT` | MTU (576-9216) | No |
| `--ip-json TEXT` | Static IPs as JSON | No |
| `--dhcp-client-json TEXT` | DHCP client config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set network vlan-interface vlan.100 \
    --folder Texas \
    --vlan-tag 100 \
    --ip-json '[{"name": "10.0.100.1/24"}]' \
    --comment "VLAN 100 gateway"
```

## Show / Delete / Load / Backup

```bash
scm show network vlan-interface --folder Texas
scm delete network vlan-interface vlan.100 --folder Texas
scm load network vlan-interface --file vlans.yaml --folder Texas
scm backup network vlan-interface --folder Texas
```
