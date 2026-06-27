# Auto Tag Action

Auto tag actions automatically apply tags to IP addresses based on log events, enabling dynamic security policy enforcement. The `scm` CLI provides commands to create, update, delete, show, backup, and load auto tag action configurations.

## Overview

The `auto-tag-action` commands allow you to:

- Create auto tag actions that apply tags based on log events
- Configure log type filters (traffic, threat, etc.)
- Delete auto tag actions that are no longer needed
- Bulk import auto tag actions from YAML files
- Export auto tag actions for backup or migration

## Set Auto Tag Action

Create or update an auto tag action.

### Syntax

```bash
scm set object auto-tag-action NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the auto tag action (positional argument) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--description TEXT` | Description of the auto tag action | No |
| `--log-type TEXT` | Log type (traffic, threat, etc.) | No |
| `--filter TEXT` | Filter expression | No |
| `--tags LIST` | Tags to apply | No |
| `--send-to-panorama` | Send to Panorama | No |
| `--quarantine` | Enable quarantine | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create an Auto Tag Action for Threat Logs

```bash
$ scm set object auto-tag-action threat-block \
    --folder Texas \
    --log-type threat \
    --filter "action eq block" \
    --tags blocked \
    --description "Tag IPs blocked by threat prevention"
---> 100%
Created auto tag action: threat-block in Texas
```

#### Update an Existing Auto Tag Action

```bash
$ scm set object auto-tag-action threat-block \
    --folder Texas \
    --log-type threat \
    --filter "action eq block" \
    --tags blocked --tags quarantined \
    --description "Tag and quarantine blocked IPs"
---> 100%
Updated auto tag action: threat-block in Texas
```

## Delete Auto Tag Action

Delete an auto tag action from SCM.

### Syntax

```bash
scm delete object auto-tag-action NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the auto tag action to delete (positional argument) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete object auto-tag-action threat-block --folder Texas --force
---> 100%
Deleted auto tag action: threat-block from Texas
```

## Load Auto Tag Actions

Load multiple auto tag actions from a YAML file.

### Syntax

```bash
scm load object auto-tag-action [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing auto tag action definitions | Yes |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
auto_tag_actions:
  - name: threat-block
    folder: Texas
    description: "Tag IPs blocked by threat prevention"
    log_type: threat
    filter: "action eq block"
    tags:
      - blocked
      - quarantined

  - name: traffic-deny
    folder: Texas
    description: "Tag IPs with denied traffic"
    log_type: traffic
    filter: "action eq deny"
    tags:
      - denied
```

### Examples

#### Load Auto Tag Actions

```bash
$ scm load object auto-tag-action --file auto-tag-actions.yml
---> 100%
Created auto tag action: threat-block in Texas
Created auto tag action: traffic-deny in Texas

Summary: Processed 2 auto tag actions
```

#### Dry Run Preview

```bash
$ scm load object auto-tag-action --file auto-tag-actions.yml --dry-run
---> 100%
[DRY RUN] Would create auto tag action: threat-block
[DRY RUN] Would create auto tag action: traffic-deny

Summary: Processed 2 auto tag actions
```

## Show Auto Tag Action

Display auto tag action objects.

### Syntax

```bash
scm show object auto-tag-action [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Name of a specific auto tag action | No |

\* One of --folder, --snippet, or --device is required.

:::note
When no `--name` is specified, all items are listed by default.
:::

### Examples

#### Show Specific Auto Tag Action

```bash
$ scm show object auto-tag-action --folder Texas --name threat-block
---> 100%
Auto Tag Action: threat-block
============================================================
Location: Texas
Description: Tag IPs blocked by threat prevention
Log Type: threat
Filter: action eq block
Tags: blocked, quarantined
```

#### List All Auto Tag Actions

```bash
$ scm show object auto-tag-action --folder Texas
---> 100%
Auto Tag Actions:
--------------------------------------------------------------------------------

Name: threat-block
Location: Texas
Description: Tag IPs blocked by threat prevention
Log Type: threat

Name: traffic-deny
Location: Texas
Description: Tag IPs with denied traffic
Log Type: traffic

Total: 2 auto tag actions
```

## Backup Auto Tag Actions

Backup all auto tag action objects from a specified location to a YAML file.

### Syntax

```bash
scm backup object auto-tag-action [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup from | No\* |
| `--snippet TEXT` | Snippet to backup from | No\* |
| `--device TEXT` | Device to backup from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup object auto-tag-action --folder Texas
---> 100%
Backed up 3 auto tag actions to auto-tag-actions_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object auto-tag-action --folder Texas --file texas-auto-tags.yaml
---> 100%
Backed up 3 auto tag actions to texas-auto-tags.yaml
```

## Best Practices

1. **Specific Filters**: Use precise filter expressions to avoid over-tagging.
2. **Descriptive Names**: Name actions clearly to indicate their purpose and trigger conditions.
3. **Tag Organization**: Create the referenced tags before creating auto tag actions.
4. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
5. **Backup Before Changes**: Always backup existing configurations before making bulk modifications.
