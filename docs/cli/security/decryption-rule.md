# Decryption Rule

Decryption rules define which traffic should be decrypted for inspection or bypassed. The `scm` CLI provides commands to create, update, delete, move, and load decryption rules.

## Overview

The `decryption-rule` commands allow you to:

- Create decryption rules with decrypt or no-decrypt actions
- Update existing rule configurations including SSL proxy type settings
- Delete rules that are no longer needed
- Move rules to control processing order
- Bulk import rules from YAML files
- Export rules for backup or migration

## Set Decryption Rule

Create or update a decryption rule.

### Syntax

```bash
scm set security decryption-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Rule name | Yes |
| `--action TEXT` | Action (decrypt or no-decrypt) | Yes |
| `--rulebase TEXT` | Rulebase (pre, post, default) | No |
| `--description TEXT` | Description | No |
| `--source-zones TEXT` | Source zones | No |
| `--destination-zones TEXT` | Destination zones | No |
| `--profile TEXT` | Decryption profile | No |
| `--type TEXT` | Decryption type as JSON | No |
| `--disabled` | Disable the rule | No |
| `--tags TEXT` | Tags | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create No-Decrypt Rule

```bash
$ scm set security decryption-rule \
    --folder Texas \
    --name no-decrypt-internal \
    --action no-decrypt \
    --source-zones trust \
    --destination-zones trust
---> 100%
Created decryption rule: no-decrypt-internal in folder Texas
```

#### Create Decrypt Rule with SSL Forward Proxy

```bash
$ scm set security decryption-rule \
    --folder Texas \
    --name decrypt-outbound \
    --action decrypt \
    --type '{"ssl_forward_proxy": {}}' \
    --profile ssl-forward-profile \
    --source-zones trust \
    --destination-zones untrust
---> 100%
Created decryption rule: decrypt-outbound in folder Texas
```

## Move Decryption Rule

Change the position of a decryption rule. Rules are processed in order from top to bottom.

### Syntax

```bash
scm set security decryption-rule --move [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the rules | No\* |
| `--snippet TEXT` | Snippet containing the rules | No\* |
| `--device TEXT` | Device containing the rules | No\* |
| `--name TEXT` | Name of the rule to move | Yes |
| `--location TEXT` | Where to move the rule (top, bottom, before, after) | Yes |
| `--reference TEXT` | Reference rule name (required with before/after) | No\*\* |

\* One of --folder, --snippet, or --device is required.

\*\* Required when `--location` is `before` or `after`.

### Examples

#### Move Rule to Top

```bash
$ scm set security decryption-rule --move \
    --folder Texas \
    --name no-decrypt-internal \
    --location top
---> 100%
Moved decryption rule: no-decrypt-internal to top in folder Texas
```

#### Move Rule After Another Rule

```bash
$ scm set security decryption-rule --move \
    --folder Texas \
    --name decrypt-outbound \
    --location after \
    --reference no-decrypt-internal
---> 100%
Moved decryption rule: decrypt-outbound after no-decrypt-internal in folder Texas
```

## Delete Decryption Rule

Delete a decryption rule from SCM.

### Syntax

```bash
scm delete security decryption-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Rule name to delete | Yes |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete security decryption-rule \
    --folder Texas \
    --name no-decrypt-internal \
    --force
---> 100%
Deleted decryption rule: no-decrypt-internal from folder Texas
```

## Load Decryption Rule

Load multiple decryption rules from a YAML file.

### Syntax

```bash
scm load security decryption-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing rule definitions | Yes |
| `--folder TEXT` | Override folder location for all rules | No |
| `--snippet TEXT` | Override snippet location for all rules | No |
| `--device TEXT` | Override device location for all rules | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
decryption_rules:
  - name: no-decrypt-internal
    folder: Texas
    description: "Skip decryption for internal traffic"
    action: no-decrypt
    source_zones:
      - trust
    destination_zones:
      - trust

  - name: decrypt-outbound
    folder: Texas
    description: "Decrypt outbound traffic"
    action: decrypt
    type:
      ssl_forward_proxy: {}
    profile: ssl-forward-profile
    source_zones:
      - trust
    destination_zones:
      - untrust
```

### Examples

#### Load with Original Locations

```bash
$ scm load security decryption-rule \
    --file decrypt-rules.yaml
---> 100%
✓ Loaded decryption rule: no-decrypt-internal
✓ Loaded decryption rule: decrypt-outbound

Successfully loaded 2 out of 2 decryption rules from 'decrypt-rules.yaml'
```

#### Load with Folder Override

```bash
$ scm load security decryption-rule \
    --file decrypt-rules.yaml \
    --folder Austin
---> 100%
✓ Loaded decryption rule: no-decrypt-internal
✓ Loaded decryption rule: decrypt-outbound

Successfully loaded 2 out of 2 decryption rules from 'decrypt-rules.yaml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all rules
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show Decryption Rule

Display decryption rule objects.

### Syntax

```bash
scm show security decryption-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Rule name to display | No |

\* One of --folder, --snippet, or --device is required.

!!! note
    When no `--name` is specified, all items are listed by default.

### Examples

#### Show Specific Rule

```bash
$ scm show security decryption-rule \
    --folder Texas \
    --name decrypt-outbound
---> 100%
Decryption Rule: decrypt-outbound
  Location: Folder 'Texas'
  Action: decrypt
  Type: SSL Forward Proxy
  Profile: ssl-forward-profile
  Source Zones: trust
  Destination Zones: untrust
```

#### List All Rules (Default Behavior)

```bash
$ scm show security decryption-rule --folder Texas
---> 100%
Decryption Rules in folder 'Texas':
------------------------------------------------------------
Name: no-decrypt-internal
  Action: no-decrypt
  Source Zones: trust
  Destination Zones: trust
------------------------------------------------------------
Name: decrypt-outbound
  Action: decrypt
  Type: SSL Forward Proxy
------------------------------------------------------------
```

## Backup Decryption Rules

Backup all decryption rule objects from a specified location to a YAML file.

### Syntax

```bash
scm backup security decryption-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup rules from | No\* |
| `--snippet TEXT` | Snippet to backup rules from | No\* |
| `--device TEXT` | Device to backup rules from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup security decryption-rule --folder Texas
---> 100%
Successfully backed up 5 decryption rules to decryption_rule_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup security decryption-rule \
    --folder Texas \
    --file texas-decrypt-rules.yaml
---> 100%
Successfully backed up 5 decryption rules to texas-decrypt-rules.yaml
```

## Best Practices

1. **Exclude Internal Traffic**: Create no-decrypt rules for internal zone-to-zone traffic to reduce unnecessary processing overhead.
2. **Order No-Decrypt First**: Place no-decrypt bypass rules above decrypt rules so trusted traffic is excluded before decryption processing begins.
3. **Attach Decryption Profiles**: Always associate a decryption profile with decrypt rules to control SSL/TLS protocol settings and certificate handling.
4. **Use SSL Forward Proxy for Outbound**: Configure `ssl_forward_proxy` type for outbound traffic decryption to internal users browsing external sites.
5. **Backup Before Changes**: Always backup existing rules before making bulk modifications via load commands.
