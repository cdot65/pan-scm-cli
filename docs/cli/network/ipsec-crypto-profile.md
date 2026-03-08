# IPsec Crypto Profile

IPsec crypto profiles define encryption and authentication parameters for IPsec Phase 2 (ESP) negotiations.

## Set IPsec Crypto Profile

```bash
scm set network ipsec-crypto-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes |
| `--name TEXT` | Profile name | Yes |
| `--esp-encryption TEXT` | ESP encryption algorithms (aes-256-cbc, aes-128-cbc, etc.) | Yes |
| `--esp-authentication TEXT` | ESP authentication algorithms (sha256, sha384, sha512, sha1, md5) | Yes |
| `--dh-group TEXT` | DH group for PFS (group14, group19, group20, no-pfs) | Yes |
| `--lifetime-seconds INT` | Lifetime in seconds | No |
| `--lifetime-hours INT` | Lifetime in hours | No |

### Example

```bash
$ scm set network ipsec-crypto-profile \
    --folder Texas \
    --name my-ipsec-profile \
    --esp-encryption aes-256-cbc \
    --esp-authentication sha256 \
    --dh-group group14
```

## Show IPsec Crypto Profile

```bash
scm show network ipsec-crypto-profile --folder Texas
scm show network ipsec-crypto-profile --folder Texas --name my-ipsec-profile
```

## Delete IPsec Crypto Profile

```bash
scm delete network ipsec-crypto-profile --folder Texas --name my-ipsec-profile
```

## Load / Backup

```bash
scm load network ipsec-crypto-profile --file ipsec-profiles.yaml --folder Texas
scm backup network ipsec-crypto-profile --folder Texas
```
