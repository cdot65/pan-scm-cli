# Layer2 Subinterface

Layer2 subinterfaces create VLAN-tagged subinterfaces operating in layer2 (switching) mode.

## Set Layer2 Subinterface

```bash
scm set network layer2-subinterface NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Subinterface name (positional) | Yes |
| `--vlan-tag TEXT` | VLAN tag (1-4096) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--parent-interface TEXT` | Parent interface name | No |
| `--comment TEXT` | Interface description | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set network layer2-subinterface ethernet1/1.100 \
    --folder Texas \
    --vlan-tag 100 \
    --parent-interface ethernet1/1
```

## Show / Delete / Load / Backup

```bash
scm show network layer2-subinterface --folder Texas
scm delete network layer2-subinterface ethernet1/1.100 --folder Texas
scm load network layer2-subinterface --file subinterfaces.yaml --folder Texas
scm backup network layer2-subinterface --folder Texas
```
