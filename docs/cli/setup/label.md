# Label

Labels provide metadata tags for organizing folders and resources in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, list, bulk import, and back up labels.

## Overview

The `label` commands allow you to:

- Create labels with optional descriptions
- Update existing label configurations
- Delete labels that are no longer needed
- Bulk import labels from YAML files
- Export labels for backup or migration

## Set Label

Create or update a label.

### Syntax

```bash
scm set setup label [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Label name | Yes |
| `--description TEXT` | Description | No |

### Examples

#### Create a Simple Label

```bash
$ scm set setup label --name production
---> 100%
Created label: production
```

#### Create a Label with Description

```bash
$ scm set setup label \
    --name staging \
    --description "Staging environment"
---> 100%
Created label: staging
```

## Delete Label

Delete a label from SCM.

### Syntax

```bash
scm delete setup label [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the label to delete | Yes |
| `--force` | Skip confirmation prompt | No |

### Example

```bash
$ scm delete setup label --name staging --force
---> 100%
Deleted label: staging
```

## Load Label

Load multiple labels from a YAML file.

### Syntax

```bash
scm load setup label [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file PATH` | YAML file to load configurations from | Yes |
| `--dry-run` | Simulate execution without applying changes | No |

### YAML File Format

```yaml
---
labels:
  - name: production
    description: "Production environment"

  - name: staging
    description: "Staging environment"
```

### Examples

#### Load Labels from File

```bash
$ scm load setup label --file labels.yaml
---> 100%
✓ Loaded label: production
✓ Loaded label: staging

Processed 2 labels from labels.yaml
```

#### Dry Run

```bash
$ scm load setup label --file labels.yaml --dry-run
---> 100%
Dry run mode: would apply the following configurations:
- name: production
  description: Production environment
- name: staging
  description: Staging environment
```

## Show Label

Display label objects.

### Syntax

```bash
scm show setup label [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the label to show | No |

!!! note
    When no `--name` is specified, all labels are listed by default.

### Examples

#### Show Specific Label

```bash
$ scm show setup label --name production
---> 100%
Label: production
================================================================================
Description: Production environment
```

#### List All Labels (Default Behavior)

```bash
$ scm show setup label
---> 100%
Labels (3):
--------------------------------------------------------------------------------
Name: production
  Description: Production environment
--------------------------------------------------------------------------------
Name: staging
  Description: Staging environment
--------------------------------------------------------------------------------
Name: development
  Description: Development environment
--------------------------------------------------------------------------------
```

## Backup Labels

Backup all label objects to a YAML file.

### Syntax

```bash
scm backup setup label [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Output filename for backup | No |

### Examples

#### Backup with Default Filename

```bash
$ scm backup setup label
---> 100%
Successfully backed up 5 labels to labels_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup setup label --file my-labels.yaml
---> 100%
Successfully backed up 5 labels to my-labels.yaml
```

## Best Practices

1. **Use Consistent Naming**: Adopt a naming convention for labels (e.g., lowercase with hyphens) and apply it uniformly.
2. **Add Descriptions**: Include descriptions to clarify each label's purpose for team members.
3. **Back Up Regularly**: Export labels before making bulk changes to preserve your organization scheme.
4. **Use Dry Run for Bulk Imports**: Preview bulk imports with `--dry-run` before applying changes.

## Using labels on resources

Labels can be applied to folders, snippets, and devices. Create the labels first with `scm set setup label`, then attach them via each resource's `--labels` flag:

```bash
# Folder
scm set setup folder --name Austin --parent Texas --labels production

# Snippet
scm set setup snippet --name Web-Security --labels production

# Device (must already exist)
scm set setup device --name PA-VM-01 --labels production --labels west
```

See [folders](folder.md), [snippets](snippet.md), and [devices](device.md) for full details on each command.

## Related Topics

- [Device](device.md)
- [Folder](folder.md)
- [Snippet](snippet.md)
- [Variable](variable.md)
