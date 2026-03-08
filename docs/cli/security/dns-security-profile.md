# DNS Security Profile

DNS security profiles protect against DNS-based threats including malware domains, command-and-control, and DNS tunneling.

## Set DNS Security Profile

```bash
scm set security dns-security-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--name TEXT` | Profile name | Yes |
| `--description TEXT` | Profile description | No |
| `--botnet-domains TEXT` | Botnet domains settings as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Examples

```bash
# Create DNS security profile with sinkhole
$ scm set security dns-security-profile --folder Texas --name dns-sec-default \
    --botnet-domains '{"dns_security_categories": [{"name": "pan-dns-sec-malware", "action": "sinkhole"}]}'

# Create profile with whitelist
$ scm set security dns-security-profile --folder Texas --name dns-sec-custom \
    --botnet-domains '{"whitelist": [{"name": "example.com"}]}'
```

## Show / Delete / Load / Backup

```bash
scm show security dns-security-profile --folder Texas
scm delete security dns-security-profile --folder Texas --name dns-sec-default
scm load security dns-security-profile --file dns-security.yaml --folder Texas
scm backup security dns-security-profile --folder Texas
```
