# URL Category

Custom URL categories define lists of URLs or URL category matches for use in security policies and URL filtering profiles. The `scm` CLI provides commands to create, update, delete, and load custom URL categories.

## Overview

The `url-category` commands allow you to:

- Create custom URL categories with URL lists or category matches
- Update existing category configurations
- Delete categories that are no longer needed
- Bulk import categories from YAML files
- Export categories for backup or migration

## Category Types

| Type | Description |
| --- | --- |
| URL List | Define explicit URLs or URL patterns to match |
| Category Match | Match against predefined URL category names |

## Set URL Category

Create or update a custom URL category.

### Syntax

```bash
scm set security url-category [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Category name | Yes |
| `--description TEXT` | Description | No |
| `--type TEXT` | Type: "URL List" or "Category Match" (default: URL List) | No |
| `--url TEXT` | URL entries (can specify multiple) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create URL List Category

```bash
$ scm set security url-category \
    --folder Texas \
    --name custom-block \
    --url malware.example.com \
    --url phishing.test.org
---> 100%
Created URL category: custom-block in folder Texas
```

#### Create Category Match Type

```bash
$ scm set security url-category \
    --folder Texas \
    --name match-category \
    --type "Category Match" \
    --url gambling \
    --url adult
---> 100%
Created URL category: match-category in folder Texas
```

## Delete URL Category

Delete a custom URL category from SCM.

### Syntax

```bash
scm delete security url-category [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Category name to delete | Yes |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete security url-category \
    --folder Texas \
    --name custom-block
---> 100%
Deleted URL category: custom-block from folder Texas
```

## Load URL Category

Load multiple custom URL categories from a YAML file.

### Syntax

```bash
scm load security url-category [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing category definitions | Yes |
| `--folder TEXT` | Override folder location for all categories | No |
| `--snippet TEXT` | Override snippet location for all categories | No |
| `--device TEXT` | Override device location for all categories | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
url_categories:
  - name: custom-block
    folder: Texas
    description: "Blocked URL list"
    type: "URL List"
    url:
      - malware.example.com
      - phishing.test.org

  - name: match-category
    folder: Texas
    description: "Category match filter"
    type: "Category Match"
    url:
      - gambling
      - adult
```

### Examples

#### Load with Original Locations

```bash
$ scm load security url-category \
    --file url-categories.yaml
---> 100%
✓ Loaded URL category: custom-block
✓ Loaded URL category: match-category

Successfully loaded 2 out of 2 URL categories from 'url-categories.yaml'
```

#### Load with Folder Override

```bash
$ scm load security url-category \
    --file url-categories.yaml \
    --folder Austin
---> 100%
✓ Loaded URL category: custom-block
✓ Loaded URL category: match-category

Successfully loaded 2 out of 2 URL categories from 'url-categories.yaml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all categories
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show URL Category

Display custom URL category objects.

### Syntax

```bash
scm show security url-category [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Category name to display | No |

\* One of --folder, --snippet, or --device is required.

!!! note
    When no `--name` is specified, all items are listed by default.

### Examples

#### Show Specific Category

```bash
$ scm show security url-category \
    --folder Texas \
    --name custom-block
---> 100%
URL Category: custom-block
  Location: Folder 'Texas'
  Type: URL List
  URLs: malware.example.com, phishing.test.org
```

#### List All Categories (Default Behavior)

```bash
$ scm show security url-category --folder Texas
---> 100%
URL Categories in folder 'Texas':
------------------------------------------------------------
Name: custom-block
  Type: URL List
  URLs: 2 entries
------------------------------------------------------------
Name: match-category
  Type: Category Match
  URLs: gambling, adult
------------------------------------------------------------
```

## Backup URL Categories

Backup all custom URL category objects from a specified location to a YAML file.

### Syntax

```bash
scm backup security url-category [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup categories from | No\* |
| `--snippet TEXT` | Snippet to backup categories from | No\* |
| `--device TEXT` | Device to backup categories from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup security url-category --folder Texas
---> 100%
Successfully backed up 6 URL categories to url_category_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup security url-category \
    --folder Texas \
    --file texas-url-categories.yaml
---> 100%
Successfully backed up 6 URL categories to texas-url-categories.yaml
```

## Best Practices

1. **Use URL Lists for Specific Sites**: Create URL List categories for explicit domain blocking or allowing of known sites.
2. **Use Category Match for Broad Filtering**: Use Category Match type to reference predefined categories in custom policies.
3. **Descriptive Names**: Name categories to clearly indicate their purpose (e.g., `blocked-malware-sites`, `allowed-business-apps`).
4. **Reference in URL Access Profiles**: Combine custom URL categories with URL access profiles for granular filtering control.
5. **Backup Before Changes**: Always backup existing categories before making bulk modifications via load commands.
