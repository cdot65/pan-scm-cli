# Label

Labels provide metadata tags for organizing folders and resources in SCM.

## Set Label

```bash
scm set setup label [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Label name | Yes |
| `--description TEXT` | Description | No |

### Examples

```bash
$ scm set setup label --name production
$ scm set setup label --name staging --description "Staging environment"
```

## Show Label

```bash
scm show setup label
scm show setup label --name production
```

## Delete Label

```bash
scm delete setup label --name staging
```

## Load / Backup

```bash
scm load setup label --file labels.yaml
scm backup setup label
```
