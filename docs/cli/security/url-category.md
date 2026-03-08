# URL Category

Custom URL categories define lists of URLs or URL category matches for use in security policies and URL filtering profiles.

## Set URL Category

```bash
scm set security url-category [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No* |
| `--snippet TEXT` | Snippet location | No* |
| `--device TEXT` | Device location | No* |
| `--name TEXT` | Category name | Yes |
| `--description TEXT` | Description | No |
| `--type TEXT` | Type: "URL List" or "Category Match" (default: URL List) | No |
| `--url TEXT` | URL entries (can specify multiple) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

```bash
# Create URL list category
$ scm set security url-category --folder Texas --name custom-block \
    --url malware.example.com --url phishing.test.org

# Create category match type
$ scm set security url-category --folder Texas --name match-category \
    --type "Category Match" --url gambling --url adult
```

## Show / Delete / Load / Backup

```bash
scm show security url-category --folder Texas
scm delete security url-category --folder Texas --name custom-block
scm load security url-category --file url-categories.yaml --folder Texas
scm backup security url-category --folder Texas
```
