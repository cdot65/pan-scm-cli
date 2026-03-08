# Variable

Variables define reusable values scoped to folders, snippets, or devices. Variable names must start with `$`.

## Set Variable

```bash
scm set setup variable [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Variable name (e.g., $egress-max) | Yes |
| `--type TEXT` | Variable type (percent, count, ip-netmask, zone, ip-range, ip-wildcard, fqdn, port, egress-max) | Yes |
| `--value TEXT` | Variable value | Yes |
| `--folder TEXT` | Folder scope | No* |
| `--snippet TEXT` | Snippet scope | No* |
| `--device TEXT` | Device scope | No* |
| `--description TEXT` | Description | No |

\* One of --folder, --snippet, or --device is required.

### Examples

```bash
$ scm set setup variable --name "\$egress-max" --type egress-max --value 1000 --folder Texas
$ scm set setup variable --name "\$dns-server" --type fqdn --value dns.example.com --snippet "DNS-Config"
```

## Show Variable

```bash
scm show setup variable --folder Texas
scm show setup variable --folder Texas --name "\$egress-max"
```

## Delete Variable

```bash
scm delete setup variable --name "\$egress-max" --folder Texas
```

## Load / Backup

```bash
scm load setup variable --file variables.yaml
scm backup setup variable --folder Texas
```
