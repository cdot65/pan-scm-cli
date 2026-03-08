# Layer3 Subinterface

Layer3 subinterfaces create VLAN-tagged subinterfaces operating in layer3 (routing) mode with IP addressing.

## Set Layer3 Subinterface

```bash
scm set network layer3-subinterface NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Subinterface name (positional) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--tag INT` | VLAN tag (1-4096) | No |
| `--parent-interface TEXT` | Parent interface name | No |
| `--comment TEXT` | Interface description | No |
| `--mtu INT` | MTU (576-9216) | No |
| `--ip-json TEXT` | Static IPs as JSON | No |
| `--dhcp-client-json TEXT` | DHCP client config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set network layer3-subinterface ethernet1/1.200 \
    --folder Texas \
    --tag 200 \
    --parent-interface ethernet1/1 \
    --mtu 1500 \
    --ip-json '[{"name": "10.0.2.1/24"}]'
```

## Show / Delete / Load / Backup

```bash
scm show network layer3-subinterface --folder Texas
scm delete network layer3-subinterface ethernet1/1.200 --folder Texas
scm load network layer3-subinterface --file subinterfaces.yaml --folder Texas
scm backup network layer3-subinterface --folder Texas
```
