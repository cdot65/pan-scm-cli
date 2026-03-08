# Snippet

Snippets are reusable configuration templates that can be shared across multiple folders.

## Set Snippet

```bash
scm set setup snippet [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Snippet name | Yes |
| `--description TEXT` | Description | No |
| `--labels TEXT` | Labels to apply | No |
| `--enable-prefix` | Enable prefix for the snippet | No |

### Examples

```bash
$ scm set setup snippet --name "DNS-Best-Practice"
$ scm set setup snippet --name "Web-Security" --description "Web security config" --labels prod
```

## Show Snippet

```bash
scm show setup snippet
scm show setup snippet --name "DNS-Best-Practice"
```

## Delete Snippet

```bash
scm delete setup snippet --name "DNS-Best-Practice"
```

## Load / Backup

```bash
scm load setup snippet --file snippets.yaml
scm backup setup snippet
```
