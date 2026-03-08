# Ethernet Interface

Ethernet interfaces configure physical network ports with layer2, layer3, or TAP mode settings.

## Set Ethernet Interface

```bash
scm set network ethernet-interface NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Interface name (positional) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--comment TEXT` | Interface description | No |
| `--default-value TEXT` | Physical interface (e.g. ethernet1/1) | No |
| `--link-speed TEXT` | Link speed (auto, 10, 100, 1000, 10000) | No |
| `--link-duplex TEXT` | Link duplex (auto, half, full) | No |
| `--link-state TEXT` | Link state (auto, up, down) | No |
| `--layer2-json TEXT` | Layer2 config as JSON | No |
| `--layer3-json TEXT` | Layer3 config as JSON | No |
| `--tap-json TEXT` | TAP config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set network ethernet-interface ethernet1/1 \
    --folder Texas \
    --layer3-json '{"mtu": 1500, "ip": [{"name": "10.0.0.1/24"}]}' \
    --link-speed auto \
    --comment "WAN uplink"
```

## Show / Delete / Load / Backup

```bash
scm show network ethernet-interface --folder Texas
scm delete network ethernet-interface ethernet1/1 --folder Texas
scm load network ethernet-interface --file interfaces.yaml --folder Texas
scm backup network ethernet-interface --folder Texas
```
