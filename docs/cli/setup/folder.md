# Folder

Folders organize configurations hierarchically in Strata Cloud Manager.

## Set Folder

```bash
scm set setup folder [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Folder name | Yes |
| `--parent TEXT` | Parent folder name | Yes |
| `--description TEXT` | Description | No |
| `--labels TEXT` | Labels to apply | No |
| `--snippets TEXT` | Snippet IDs to associate | No |

### Examples

```bash
$ scm set setup folder --name Texas --parent "All"
$ scm set setup folder --name Branch --parent Texas --description "Branch offices"
```

## Show Folder

```bash
scm show setup folder
scm show setup folder --name Texas
```

## Delete Folder

```bash
scm delete setup folder --name Branch
```

## Load / Backup

```bash
scm load setup folder --file folders.yaml
scm backup setup folder
```
