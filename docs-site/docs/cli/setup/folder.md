# Folder

Folders organize configurations hierarchically in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, list, bulk import, and back up folders.

## Overview

The `folder` commands allow you to:

- Create folders with a parent hierarchy and optional labels
- Update existing folder configurations
- Delete folders that are no longer needed
- Bulk import folders from YAML files
- Export folders for backup or migration

## Set Folder

Create or update a folder.

### Syntax

```bash
scm set setup folder NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Folder name | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--parent TEXT` | Parent folder name | Yes |
| `--description TEXT` | Description | No |
| `--labels TEXT` | Labels to apply | No |
| `--snippets TEXT` | Snippet IDs to associate | No |

### Examples

#### Create a Top-Level Folder

```bash
$ scm set setup folder Texas \
    --parent "All"
---> 100%
Created folder: Texas (parent: All)
```

#### Create a Child Folder with Description

```bash
$ scm set setup folder Branch \
    --parent Texas \
    --description "Branch offices"
---> 100%
Created folder: Branch (parent: Texas)
```

#### Create a Folder with Labels

```bash
$ scm set setup folder Austin \
    --parent Texas \
    --labels production \
    --labels west-region
---> 100%
Created folder: Austin (parent: Texas)
```

## Delete Folder

Delete a folder from SCM.

### Syntax

```bash
scm delete setup folder NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the folder to delete | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--force` | Skip confirmation prompt | No |

### Example

```bash
$ scm delete setup folder Branch --force
---> 100%
Deleted folder: Branch
```

## Load Folder

Load multiple folders from a YAML file.

### Syntax

```bash
scm load setup folder [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file PATH` | YAML file to load configurations from | Yes |
| `--dry-run` | Simulate execution without applying changes | No |

### YAML File Format

```yaml
---
folders:
  - name: Texas
    parent: "All"
    description: "Texas regional office"

  - name: Austin
    parent: Texas
    description: "Austin branch"
    labels:
      - production
```

### Examples

#### Load Folders from File

```bash
$ scm load setup folder --file folders.yaml
---> 100%
✓ Loaded folder: Texas
✓ Loaded folder: Austin

Processed 2 folders from folders.yaml
```

#### Dry Run

```bash
$ scm load setup folder --file folders.yaml --dry-run
---> 100%
Dry run mode: would apply the following configurations:
- name: Texas
  parent: All
  description: Texas regional office
- name: Austin
  parent: Texas
  description: Austin branch
```

## Show Folder

Display folder objects.

### Syntax

```bash
scm show setup folder [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the folder to show; omit to list all | No |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--output, -o [table\|json\|yaml]` | Output format (default: table) | No |
| `--max-results INTEGER` | Maximum number of results to display | No |

:::note
When no `NAME` is specified, all folders are listed by default.
:::

### Examples

#### Show Specific Folder

```bash
$ scm show setup folder Texas
---> 100%
Folder: Texas
================================================================================
Parent: All
Description: Texas regional office
Labels: production, west-region
```

#### List All Folders (Default Behavior)

```bash
$ scm show setup folder
---> 100%
Folders (3):
--------------------------------------------------------------------------------
Name: All
  Parent: N/A
--------------------------------------------------------------------------------
Name: Texas
  Parent: All
  Description: Texas regional office
--------------------------------------------------------------------------------
Name: Austin
  Parent: Texas
  Description: Austin branch
--------------------------------------------------------------------------------
```

## Backup Folders

Backup all folder objects to a YAML file.

### Syntax

```bash
scm backup setup folder [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Output filename for backup | No |

### Examples

#### Backup with Default Filename

```bash
$ scm backup setup folder
---> 100%
Successfully backed up 12 folders to folders_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup setup folder --file my-folders.yaml
---> 100%
Successfully backed up 12 folders to my-folders.yaml
```

## Best Practices

1. **Plan Your Hierarchy**: Design the folder structure before creating folders to avoid reorganization later.
2. **Use Descriptive Names**: Choose folder names that clearly indicate their purpose or geographic scope.
3. **Apply Labels Consistently**: Use labels to categorize folders for easier filtering and management.
4. **Back Up Before Changes**: Export your folder structure before making significant modifications.
5. **Use Dry Run for Bulk Imports**: Always preview bulk imports with `--dry-run` before applying changes.

## Related Topics

- [Label](label.md)
- [Snippet](snippet.md)
- [Variable](variable.md)
