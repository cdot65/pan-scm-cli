# IKE Gateway

IKE gateways define VPN tunnel endpoints with peer addressing, authentication, and protocol settings. The `scm` CLI provides commands to create, update, delete, and load IKE gateways.

## Overview

The `ike-gateway` commands allow you to:

- Create IKE gateways with pre-shared key or certificate authentication
- Update existing IKE gateway configurations
- Delete IKE gateways that are no longer needed
- Bulk import IKE gateways from YAML files
- Export IKE gateways for backup or migration

## Set IKE Gateway

Create or update an IKE gateway.

### Syntax

```bash
scm set network ike-gateway NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Gateway name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--pre-shared-key TEXT` | Pre-shared key for authentication | No\*\* |
| `--peer-address-ip TEXT` | Peer IP address | No\*\*\* |
| `--peer-address-fqdn TEXT` | Peer FQDN | No\*\*\* |
| `--peer-address-dynamic` | Use dynamic peer address | No\*\*\* |
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
| `--authentication-json TEXT` | Full authentication config as JSON | No\*\* |
| `--peer-address-json TEXT` | Full peer address config as JSON | No\*\*\* |
| `--protocol-json TEXT` | Full protocol config as JSON | No |
| `--protocol-common-json TEXT` | Full protocol_common config as JSON | No |

\* One of --folder, --snippet, or --device is required.
\*\* Either --pre-shared-key or --authentication-json is required.
\*\*\* One of --peer-address-ip, --peer-address-fqdn, --peer-address-dynamic, or --peer-address-json is required.

### Examples

#### Create an IKE Gateway with Pre-Shared Key

```bash
$ scm set network ike-gateway my-gateway \
    --folder Texas \
    --pre-shared-key "mysecret" \
    --peer-address-ip 203.0.113.1 \
    --ike-crypto-profile my-ike-profile \
    --nat-traversal \
    --dpd-enable
---> 100%
Created IKE gateway: my-gateway in folder Texas
```

#### Create an IKE Gateway with FQDN Peer

```bash
$ scm set network ike-gateway branch-gw \
    --folder Texas \
    --pre-shared-key "branch-secret" \
    --peer-address-fqdn vpn.example.com \
    --protocol-version ikev2 \
    --ike-crypto-profile high-security-ike
---> 100%
Created IKE gateway: branch-gw in folder Texas
```

## Delete IKE Gateway

Delete an IKE gateway from SCM.

### Syntax

```bash
scm delete network ike-gateway NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Gateway name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete network ike-gateway my-gateway --folder Texas
---> 100%
Deleted IKE gateway: my-gateway from folder Texas
```

## Load IKE Gateway

Load multiple IKE gateways from a YAML file.

### Syntax

```bash
scm load network ike-gateway [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--dry-run` | Preview changes without applying | No |

\* One of --folder, --snippet, or --device is required.

### YAML File Format

```yaml
---
ike_gateways:
  - name: site-a-gw
    folder: Texas
    authentication:
      pre_shared_key:
        key: "site-a-secret"
    peer_address:
      ip: "203.0.113.1"
    protocol:
      ikev2:
        ike_crypto_profile: "standard-ike"
    protocol_common:
      nat_traversal:
        enable: true

  - name: site-b-gw
    folder: Texas
    authentication:
      pre_shared_key:
        key: "site-b-secret"
    peer_address:
      fqdn: "vpn-b.example.com"
    protocol:
      ikev2:
        ike_crypto_profile: "standard-ike"
```

### Examples

#### Load with Original Locations

```bash
$ scm load network ike-gateway --file ike-gateways.yml
---> 100%
✓ Loaded IKE gateway: site-a-gw
✓ Loaded IKE gateway: site-b-gw

Successfully loaded 2 out of 2 IKE gateways from 'ike-gateways.yml'
```

#### Load with Folder Override

```bash
$ scm load network ike-gateway --file ike-gateways.yml --folder Austin
---> 100%
✓ Loaded IKE gateway: site-a-gw
✓ Loaded IKE gateway: site-b-gw

Successfully loaded 2 out of 2 IKE gateways from 'ike-gateways.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all IKE gateways
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show IKE Gateway

Display IKE gateway objects.

### Syntax

```bash
scm show network ike-gateway [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Name of a specific gateway | No |

\* One of --folder, --snippet, or --device is required.

!!! note
    When no `--name` is specified, all items are listed by default.

### Examples

#### Show Specific IKE Gateway

```bash
$ scm show network ike-gateway --folder Texas --name my-gateway
---> 100%
IKE Gateway: my-gateway
  Location: Folder 'Texas'
  Peer Address: 203.0.113.1
  IKE Crypto Profile: my-ike-profile
  NAT Traversal: enabled
  DPD: enabled
```

#### List All IKE Gateways (Default Behavior)

```bash
$ scm show network ike-gateway --folder Texas
---> 100%
IKE gateways in folder 'Texas':
------------------------------------------------------------
Name: site-a-gw
  Peer: 203.0.113.1
  Profile: standard-ike
------------------------------------------------------------
Name: site-b-gw
  Peer: vpn-b.example.com
  Profile: standard-ike
------------------------------------------------------------
```

## Backup IKE Gateways

Backup all IKE gateway objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network ike-gateway [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--file TEXT` | Custom output filename | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup network ike-gateway --folder Texas
---> 100%
Successfully backed up 10 IKE gateways to ike_gateway_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network ike-gateway --folder Texas --file texas-ike-gateways.yaml
---> 100%
Successfully backed up 10 IKE gateways to texas-ike-gateways.yaml
```

## Best Practices

1. **Enable DPD**: Always enable Dead Peer Detection to detect and recover from failed tunnels.
2. **Use NAT Traversal**: Enable NAT traversal when peers may be behind NAT devices.
3. **Prefer IKEv2**: Use ikev2 or ikev2-preferred for improved security and performance over IKEv1.
4. **Use Strong Pre-Shared Keys**: Generate long, random pre-shared keys for authentication.
5. **Backup Before Changes**: Always backup existing gateway configurations before making bulk modifications.
6. **Reference Crypto Profiles**: Ensure IKE crypto profiles exist before referencing them in gateway configurations.
