# Snippet

Snippets are reusable configuration templates that can be shared across multiple folders in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, list, bulk import, and back up snippets.

## Overview

The `snippet` commands allow you to:

- Create snippets with optional labels and prefix settings
- Update existing snippet configurations
- Delete snippets that are no longer needed
- Bulk import snippets from YAML files
- Export snippets for backup or migration

## Set Snippet

Create or update a snippet.

### Syntax

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

#### Create a Simple Snippet

```bash
$ scm set setup snippet --name "DNS-Best-Practice"
---> 100%
Created snippet: DNS-Best-Practice
```

#### Create a Snippet with Description and Labels

```bash
$ scm set setup snippet \
    --name "Web-Security" \
    --description "Web security config" \
    --labels prod
---> 100%
Created snippet: Web-Security
```

#### Create a Snippet with Prefix Enabled

```bash
$ scm set setup snippet \
    --name "Branch-Template" \
    --description "Standard branch config" \
    --enable-prefix
---> 100%
Created snippet: Branch-Template
```

## Delete Snippet

Delete a snippet from SCM.

### Syntax

```bash
scm delete setup snippet [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the snippet to delete | Yes |
| `--force` | Skip confirmation prompt | No |

### Example

```bash
$ scm delete setup snippet --name "DNS-Best-Practice" --force
---> 100%
Deleted snippet: DNS-Best-Practice
```

## Load Snippet

Load multiple snippets from a YAML file.

### Syntax

```bash
scm load setup snippet [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file PATH` | YAML file to load configurations from | Yes |
| `--dry-run` | Simulate execution without applying changes | No |

### YAML File Format

```yaml
---
snippets:
  - name: DNS-Best-Practice
    description: "DNS security best practices"

  - name: Web-Security
    description: "Web security config"
    labels:
      - prod
    enable_prefix: true
```

### Examples

#### Load Snippets from File

```bash
$ scm load setup snippet --file snippets.yaml
---> 100%
✓ Loaded snippet: DNS-Best-Practice
✓ Loaded snippet: Web-Security

Processed 2 snippets from snippets.yaml
```

#### Dry Run

```bash
$ scm load setup snippet --file snippets.yaml --dry-run
---> 100%
Dry run mode: would apply the following configurations:
- name: DNS-Best-Practice
  description: DNS security best practices
- name: Web-Security
  description: Web security config
  labels:
    - prod
  enable_prefix: true
```

## Show Snippet

Display snippet objects.

### Syntax

```bash
scm show setup snippet [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the snippet to show | No |

!!! note
    When no `--name` is specified, all snippets are listed by default.

### Examples

#### Show Specific Snippet

```bash
$ scm show setup snippet --name "DNS-Best-Practice"
---> 100%
Snippet: DNS-Best-Practice
================================================================================
Description: DNS security best practices
Type: predefined
Labels: prod
Enable Prefix: true
```

#### List All Snippets (Default Behavior)

```bash
$ scm show setup snippet
---> 100%
Snippets (3):
--------------------------------------------------------------------------------
Name: DNS-Best-Practice
  Description: DNS security best practices
  Type: predefined
--------------------------------------------------------------------------------
Name: Web-Security
  Description: Web security config
  Type: custom
--------------------------------------------------------------------------------
Name: Branch-Template
  Description: Standard branch config
  Type: custom
--------------------------------------------------------------------------------
```

## Backup Snippets

Backup all snippet objects to a YAML file.

### Syntax

```bash
scm backup setup snippet [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Output filename for backup | No |

### Examples

#### Backup with Default Filename

```bash
$ scm backup setup snippet
---> 100%
Successfully backed up 8 snippets to snippets_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup setup snippet --file my-snippets.yaml
---> 100%
Successfully backed up 8 snippets to my-snippets.yaml
```

## Best Practices

1. **Use Descriptive Names**: Choose snippet names that clearly indicate the configuration purpose.
2. **Apply Labels for Organization**: Use labels to categorize snippets by function or environment.
3. **Enable Prefix When Sharing**: Use `--enable-prefix` when snippets are shared across folders to avoid naming conflicts.
4. **Back Up Before Changes**: Export your snippets before making significant modifications.
5. **Use Dry Run for Bulk Imports**: Preview bulk imports with `--dry-run` before applying changes.

## Related Topics

- [Folder](folder.md)
- [Label](label.md)
- [Variable](variable.md)
