# Decryption Profile

Decryption profiles configure SSL/TLS inspection settings for three proxy types: SSL Forward Proxy (outbound), SSL Inbound Proxy (inbound), and SSL No Proxy (bypass).

## Set Decryption Profile

```bash
scm set security decryption-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--name TEXT` | Profile name | Yes |
| `--description TEXT` | Profile description | No |
| `--ssl-forward-proxy TEXT` | SSL forward proxy settings as JSON | No |
| `--ssl-inbound-proxy TEXT` | SSL inbound proxy settings as JSON | No |
| `--ssl-no-proxy TEXT` | SSL no proxy settings as JSON | No |
| `--ssl-protocol-settings TEXT` | SSL protocol settings as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Examples

```bash
# Create SSL forward proxy profile
$ scm set security decryption-profile --folder Texas --name ssl-forward \
    --ssl-forward-proxy '{"block_expired_certificate": true, "block_untrusted_issuer": true}'

# Create profile with protocol settings
$ scm set security decryption-profile --folder Texas --name custom-decrypt \
    --ssl-forward-proxy '{"block_expired_certificate": true}' \
    --ssl-protocol-settings '{"min_version": "tls1-2", "max_version": "tls1-3"}'

# Create no-decrypt profile
$ scm set security decryption-profile --folder Texas --name no-decrypt \
    --ssl-no-proxy '{"block_expired_certificate": false}'
```

## Show / Delete / Load / Backup

```bash
scm show security decryption-profile --folder Texas
scm delete security decryption-profile --folder Texas --name ssl-forward
scm load security decryption-profile --file decrypt-profiles.yaml --folder Texas
scm backup security decryption-profile --folder Texas
```
