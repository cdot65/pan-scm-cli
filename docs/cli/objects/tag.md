# Tag Objects

Tags provide a flexible way to categorize and organize objects across Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load tag objects.

## Overview

The `tag` commands allow you to:

- Create tags with specific colors for visual identification
- Add descriptive comments to tags
- Delete tags that are no longer needed
- Bulk import tags from YAML files
- Export tags for backup or migration

## Supported Colors

The following 42 colors are supported:

| Color Name | Color Name | Color Name |
| --- | --- | --- |
| Red | Green | Blue |
| Yellow | Copper | Orange |
| Purple | Gray | Light Green |
| Cyan | Light Gray | Blue Gray |
| Lime | Black | Gold |
| Brown | Olive | Maroon |
| Red-Orange | Yellow-Orange | Forest Green |
| Turquoise Blue | Azure Blue | Cerulean Blue |
| Midnight Blue | Medium Blue | Cobalt Blue |
| Violet Blue | Blue Violet | Medium Violet |
| Medium Rose | Lavender | Orchid |
| Thistle | Peach | Salmon |
| Magenta | Red Violet | Mahogany |
| Burnt Sienna | Chestnut | |

## Set Tag

Create or update a tag object.

### Syntax

```bash
scm set object tag [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder for the tag object | No\* |
| `--snippet TEXT` | Snippet for the tag object | No\* |
| `--device TEXT` | Device for the tag object | No\* |
| `--name TEXT` | Name of the tag | Yes |
| `--color TEXT` | Color for visual identification | No |
| `--comments TEXT` | Descriptive comments about the tag | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create a Tag with Color

```bash
$ scm set object tag \
    --folder Texas \
    --name production \
    --color "Red" \
    --comments "Production environment resources"
---> 100%
Created tag: production in folder Texas
```

#### Create Multiple Environment Tags

```bash
$ scm set object tag \
    --folder Texas \
    --name critical \
    --color "Orange"
---> 100%
Created tag: critical in folder Texas
```

```bash
$ scm set object tag \
    --folder Texas \
    --name database \
    --color "Blue"
---> 100%
Created tag: database in folder Texas
```

## Delete Tag

Delete a tag object from SCM.

### Syntax

```bash
scm delete object tag [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the tag object | No\* |
| `--snippet TEXT` | Snippet containing the tag object | No\* |
| `--device TEXT` | Device containing the tag object | No\* |
| `--name TEXT` | Name of the tag to delete | Yes |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete object tag --folder Texas --name production --force
---> 100%
Deleted tag: production from folder Texas
```

## Load Tags

Load multiple tag objects from a YAML file.

### Syntax

```bash
scm load object tag [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing tag definitions | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
tags:
  - name: production
    folder: Texas
    color: "Red"
    comments: "Production environment resources"

  - name: staging
    folder: Texas
    color: "Orange"
    comments: "Staging environment resources"

  - name: development
    folder: Texas
    color: "Yellow"
    comments: "Development environment resources"

  - name: finance
    folder: Texas
    color: "Gold"
    comments: "Finance department resources"

  - name: it
    folder: Texas
    color: "Blue"
    comments: "IT department resources"

  - name: restricted
    folder: Texas
    color: "Magenta"
    comments: "Restricted access resources"
```

### Examples

#### Load with Original Locations

```bash
$ scm load object tag --file tags.yml
---> 100%
✓ Loaded tag: production
✓ Loaded tag: staging
✓ Loaded tag: development
✓ Loaded tag: finance
✓ Loaded tag: it
✓ Loaded tag: restricted

Successfully loaded 6 out of 6 tags from 'tags.yml'
```

#### Load with Folder Override

```bash
$ scm load object tag --file tags.yml --folder Austin
---> 100%
✓ Loaded tag: production
✓ Loaded tag: staging
✓ Loaded tag: development
✓ Loaded tag: finance
✓ Loaded tag: it
✓ Loaded tag: restricted

Successfully loaded 6 out of 6 tags from 'tags.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all tags
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show Tag

Display tag objects.

### Syntax

```bash
scm show object tag [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the tag object | No\* |
| `--snippet TEXT` | Snippet containing the tag object | No\* |
| `--device TEXT` | Device containing the tag object | No\* |
| `--name TEXT` | Name of the tag to show | No |

!!! note
    When no `--name` is specified, all items are listed by default.

\* One of --folder, --snippet, or --device is required.

### Examples

#### Show Specific Tag

```bash
$ scm show object tag --folder Texas --name production
---> 100%
Tag: production
  Location: Folder 'Texas'
  Color: Red
  Comments: Production environment resources
```

#### List All Tags (Default Behavior)

```bash
$ scm show object tag --folder Texas
---> 100%
Tags in folder 'Texas':
------------------------------------------------------------
Name: production
  Color: Red
  Comments: Production environment resources
------------------------------------------------------------
Name: staging
  Color: Orange
  Comments: Staging environment resources
------------------------------------------------------------
Name: development
  Color: Yellow
  Comments: Development environment resources
------------------------------------------------------------
Name: critical
  Color: Orange
------------------------------------------------------------
Name: database
  Color: Blue
------------------------------------------------------------
```

## Backup Tags

Backup all tag objects from a specified location to a YAML file.

### Syntax

```bash
scm backup object tag [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup tags from | No\* |
| `--snippet TEXT` | Snippet to backup tags from | No\* |
| `--device TEXT` | Device to backup tags from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup object tag --folder Texas
---> 100%
Successfully backed up 42 tags to tag_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object tag --folder Texas --file texas-tags.yaml
---> 100%
Successfully backed up 42 tags to texas-tags.yaml
```

## Best Practices

1. **Consistent Naming**: Use a consistent naming convention (e.g., env-prod, dept-finance).
2. **Color Coding**: Establish a color scheme (e.g., Red for production, Green for development).
3. **Documentation**: Always add comments to explain the tag's purpose.
4. **Hierarchical Tagging**: Use prefixes to create logical hierarchies.
5. **Regular Cleanup**: Remove unused tags to maintain organization.
6. **Create Tags First**: Tags must exist before being referenced by other objects.
