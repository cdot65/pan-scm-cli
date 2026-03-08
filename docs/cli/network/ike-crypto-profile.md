# IKE Crypto Profile

IKE crypto profiles define encryption, authentication, and key exchange parameters for IKE Phase 1 negotiations.

## Set IKE Crypto Profile

```bash
scm set network ike-crypto-profile NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name (positional) | Yes |
| `--hash TEXT` | Hash algorithms (sha256, sha384, sha512, sha1, md5) | Yes |
| `--dh-group TEXT` | DH groups (group1, group2, group5, group14, group19, group20) | Yes |
| `--encryption TEXT` | Encryption algorithms (aes-256-cbc, aes-128-cbc, etc.) | Yes |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--lifetime-seconds INT` | Lifetime in seconds (180-65535) | No |
| `--lifetime-minutes INT` | Lifetime in minutes (3-65535) | No |
| `--lifetime-hours INT` | Lifetime in hours (1-65535) | No |
| `--lifetime-days INT` | Lifetime in days (1-365) | No |
| `--authentication-multiple INT` | IKEv2 SA reauthentication interval (0-50) | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set network ike-crypto-profile my-ike-profile \
    --folder Texas \
    --hash sha256 \
    --dh-group group14 \
    --encryption aes-256-cbc \
    --lifetime-hours 8
```

## Show IKE Crypto Profile

```bash
scm show network ike-crypto-profile --folder Texas
scm show network ike-crypto-profile --folder Texas --name my-ike-profile
```

## Delete IKE Crypto Profile

```bash
scm delete network ike-crypto-profile my-ike-profile --folder Texas
```

## Load / Backup

```bash
scm load network ike-crypto-profile --file ike-profiles.yaml --folder Texas
scm backup network ike-crypto-profile --folder Texas
```
