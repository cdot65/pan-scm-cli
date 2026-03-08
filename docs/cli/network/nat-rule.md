# NAT Rule

NAT rules define network address translation policies for traffic flowing between zones.

## Set NAT Rule

```bash
scm set network nat-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes |
| `--name TEXT` | Rule name | Yes |
| `--description TEXT` | Rule description | No |
| `--tag TEXT` | Tags | No |
| `--disabled` | Disable the rule | No |
| `--nat-type TEXT` | NAT type (ipv4, nat64, nptv6) | No |
| `--from-zone TEXT` | Source zones | No |
| `--to-zone TEXT` | Destination zones | No |
| `--to-interface TEXT` | Destination interface | No |
| `--source TEXT` | Source addresses | No |
| `--destination TEXT` | Destination addresses | No |
| `--service TEXT` | Service | No |
| `--source-translation TEXT` | Source translation config as JSON | No |
| `--destination-translation TEXT` | Destination translation config as JSON | No |

### Examples

```bash
# Create outbound NAT rule
$ scm set network nat-rule --folder Texas --name outbound-nat \
    --from-zone trust --to-zone untrust \
    --source any --destination any \
    --source-translation '{"dynamic_ip_and_port": {"type": "dynamic_ip_and_port", "translated_address": ["10.0.0.1"]}}'

# Create destination NAT rule
$ scm set network nat-rule --folder Texas --name inbound-web \
    --from-zone untrust --to-zone dmz \
    --destination 203.0.113.10 \
    --destination-translation '{"translated_address": "192.168.1.10", "translated_port": 443}'
```

## Show NAT Rule

```bash
scm show network nat-rule --folder Texas
scm show network nat-rule --folder Texas --name outbound-nat
```

## Delete NAT Rule

```bash
scm delete network nat-rule --folder Texas --name outbound-nat
```

## Load / Backup

```bash
scm load network nat-rule --file nat-rules.yaml --folder Texas
scm backup network nat-rule --folder Texas
```
