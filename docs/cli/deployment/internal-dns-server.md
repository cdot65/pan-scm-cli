# Internal DNS Server

Internal DNS servers configure DNS resolution for internal domains through SASE infrastructure.

## Set Internal DNS Server

```bash
scm set sase internal-dns-server [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Server name | Yes |
| `--domain-name TEXT` | Domain name(s), comma-separated | Yes |
| `--primary TEXT` | Primary DNS server IP | Yes |
| `--secondary TEXT` | Secondary DNS server IP | No |

### Example

```bash
$ scm set sase internal-dns-server \
    --name corp-dns \
    --domain-name corp.example.com \
    --primary 10.0.0.1 \
    --secondary 10.0.0.2
```

## Show Internal DNS Server

```bash
scm show sase internal-dns-server
scm show sase internal-dns-server --name corp-dns
```

## Delete Internal DNS Server

```bash
scm delete sase internal-dns-server --name corp-dns
```

## Load / Backup

```bash
scm load sase internal-dns-server --file dns-servers.yaml
scm backup sase internal-dns-server
```
