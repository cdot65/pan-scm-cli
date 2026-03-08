# URL Access Profile

URL access profiles define URL filtering policies that control access to websites by category.

## Set URL Access Profile

```bash
scm set security url-access-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--name TEXT` | Profile name | Yes |
| `--description TEXT` | Description | No |
| `--block TEXT` | URL categories to block (can specify multiple) | No |
| `--alert TEXT` | URL categories to alert (can specify multiple) | No |
| `--allow TEXT` | URL categories to allow (can specify multiple) | No |
| `--credential-enforcement TEXT` | Credential enforcement as JSON | No |
| `--cloud-inline-cat / --no-cloud-inline-cat` | Enable cloud inline categorization | No |
| `--safe-search / --no-safe-search` | Enable safe search enforcement | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm set security url-access-profile --folder Texas --name strict-url \
    --block adult --block malware --alert hacking
```

## Show / Delete / Load / Backup

```bash
scm show security url-access-profile --folder Texas
scm delete security url-access-profile --folder Texas --name strict-url
scm load security url-access-profile --file url-profiles.yaml --folder Texas
scm backup security url-access-profile --folder Texas
```
