# Aggregate Interface

Aggregate interfaces combine multiple physical interfaces into a single logical interface for link aggregation (LACP).

## Set Aggregate Interface

```bash
scm set network aggregate-interface NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Interface name (positional) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--comment TEXT` | Interface description | No |
| `--layer2-json TEXT` | Layer2 config as JSON | No |
| `--layer3-json TEXT` | Layer3 config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set network aggregate-interface ae1 \
    --folder Texas \
    --layer3-json '{"mtu": 1500, "ip": [{"name": "10.0.0.1/24"}]}' \
    --comment "Aggregated uplink"
```

## Show / Delete / Load / Backup

```bash
scm show network aggregate-interface --folder Texas
scm delete network aggregate-interface ae1 --folder Texas
scm load network aggregate-interface --file interfaces.yaml --folder Texas
scm backup network aggregate-interface --folder Texas
```
