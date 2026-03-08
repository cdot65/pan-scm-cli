# IKE Gateway

IKE gateways define VPN tunnel endpoints with peer addressing, authentication, and protocol settings.

## Set IKE Gateway

```bash
scm set network ike-gateway NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Gateway name (positional) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--pre-shared-key TEXT` | Pre-shared key for authentication | No** |
| `--peer-address-ip TEXT` | Peer IP address | No*** |
| `--peer-address-fqdn TEXT` | Peer FQDN | No*** |
| `--peer-address-dynamic` | Use dynamic peer address | No*** |
| `--protocol-version TEXT` | IKE version (ikev1, ikev2, ikev2-preferred) | No |
| `--ike-crypto-profile TEXT` | IKE crypto profile name | No |
| `--peer-id-type TEXT` | Peer ID type (ipaddr, keyid, fqdn, ufqdn) | No |
| `--peer-id-value TEXT` | Peer ID value | No |
| `--local-id-type TEXT` | Local ID type | No |
| `--local-id-value TEXT` | Local ID value | No |
| `--nat-traversal` | Enable NAT traversal | No |
| `--fragmentation` | Enable IKE fragmentation | No |
| `--passive-mode` | Enable passive mode | No |
| `--dpd-enable` | Enable Dead Peer Detection | No |
| `--authentication-json TEXT` | Full authentication config as JSON | No** |
| `--peer-address-json TEXT` | Full peer address config as JSON | No*** |
| `--protocol-json TEXT` | Full protocol config as JSON | No |
| `--protocol-common-json TEXT` | Full protocol_common config as JSON | No |

\* One of --folder, --snippet, or --device is required.
\*\* Either --pre-shared-key or --authentication-json is required.
\*\*\* One of --peer-address-ip, --peer-address-fqdn, --peer-address-dynamic, or --peer-address-json is required.

### Example

```bash
$ scm set network ike-gateway my-gateway \
    --folder Texas \
    --pre-shared-key "mysecret" \
    --peer-address-ip 203.0.113.1 \
    --ike-crypto-profile my-ike-profile \
    --nat-traversal \
    --dpd-enable
```

## Show IKE Gateway

```bash
scm show network ike-gateway --folder Texas
scm show network ike-gateway --folder Texas --name my-gateway
```

## Delete IKE Gateway

```bash
scm delete network ike-gateway my-gateway --folder Texas
```

## Load / Backup

```bash
scm load network ike-gateway --file ike-gateways.yaml --folder Texas
scm backup network ike-gateway --folder Texas
```
