# NAT Rule

NAT rules define network address translation policies for traffic flowing between zones. The `scm` CLI provides commands to create, update, delete, and load NAT rules.

## Overview

The `nat-rule` commands allow you to:

- Create NAT rules with source and destination translation
- Update existing NAT rule configurations
- Delete NAT rules that are no longer needed
- Bulk import NAT rules from YAML files
- Export NAT rules for backup or migration

## Set NAT Rule

Create or update a NAT rule.

### Syntax

```bash
scm set network nat-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Rule name | Yes |
| `--folder TEXT` | Folder location | Yes |
| `--description TEXT` | Rule description | No |
| `--tag TEXT` | Tags | No |
| `--disabled` | Disable the rule | No |
| `--nat-type TEXT` | NAT type (ipv4, nat64, nptv6) | No |
| `--from-zone TEXT` | Source zones | No |
| `--to-zone TEXT` | Destination zones | No |
| `--to-interface TEXT` | Destination interface | No |
| `--source TEXT` | Source addresses | No |
| `--destination TEXT` | Destination addresses | No |
| `--service TEXT` | Service | No |
| `--source-translation TEXT` | Source translation config as JSON | No |
| `--destination-translation TEXT` | Destination translation config as JSON | No |

### Examples

#### Create an Outbound NAT Rule

```bash
$ scm set network nat-rule \
    --folder Texas \
    --name outbound-nat \
    --from-zone trust \
    --to-zone untrust \
    --source any \
    --destination any \
    --source-translation '{"dynamic_ip_and_port": {"type": "dynamic_ip_and_port", "translated_address": ["10.0.0.1"]}}'
---> 100%
Created NAT rule: outbound-nat in folder Texas
```

#### Create a Destination NAT Rule

```bash
$ scm set network nat-rule \
    --folder Texas \
    --name inbound-web \
    --from-zone untrust \
    --to-zone dmz \
    --destination 203.0.113.10 \
    --destination-translation '{"translated_address": "192.168.1.10", "translated_port": 443}'
---> 100%
Created NAT rule: inbound-web in folder Texas
```

## Delete NAT Rule

Delete a NAT rule from SCM.

### Syntax

```bash
scm delete network nat-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Rule name | Yes |
| `--folder TEXT` | Folder location | Yes |
| `--force` | Skip confirmation prompt | No |

### Example

```bash
$ scm delete network nat-rule --folder Texas --name outbound-nat --force
---> 100%
Deleted NAT rule: outbound-nat from folder Texas
```

## Load NAT Rule

Load multiple NAT rules from a YAML file.

### Syntax

```bash
scm load network nat-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--dry-run` | Preview changes without applying | No |

\* One of --folder, --snippet, or --device is required.

### YAML File Format

```yaml
---
nat_rules:
  - name: outbound-nat
    folder: Texas
    from_zone:
      - trust
    to_zone:
      - untrust
    source:
      - any
    destination:
      - any
    source_translation:
      dynamic_ip_and_port:
        type: dynamic_ip_and_port
        translated_address:
          - "10.0.0.1"

  - name: inbound-web
    folder: Texas
    from_zone:
      - untrust
    to_zone:
      - dmz
    destination:
      - "203.0.113.10"
    destination_translation:
      translated_address: "192.168.1.10"
      translated_port: 443
```

### Examples

#### Load with Original Locations

```bash
$ scm load network nat-rule --file nat-rules.yml
---> 100%
✓ Loaded NAT rule: outbound-nat
✓ Loaded NAT rule: inbound-web

Successfully loaded 2 out of 2 NAT rules from 'nat-rules.yml'
```

#### Load with Folder Override

```bash
$ scm load network nat-rule --file nat-rules.yml --folder Austin
---> 100%
✓ Loaded NAT rule: outbound-nat
✓ Loaded NAT rule: inbound-web

Successfully loaded 2 out of 2 NAT rules from 'nat-rules.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all NAT rules
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show NAT Rule

Display NAT rule objects.

### Syntax

```bash
scm show network nat-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Name of a specific rule | No |

\* One of --folder, --snippet, or --device is required.

!!! note
    When no `--name` is specified, all items are listed by default.

### Examples

#### Show Specific NAT Rule

```bash
$ scm show network nat-rule --folder Texas --name outbound-nat
---> 100%
NAT Rule: outbound-nat
  Location: Folder 'Texas'
  From Zone: trust
  To Zone: untrust
  Source: any
  Destination: any
  Source Translation: dynamic_ip_and_port (10.0.0.1)
```

#### List All NAT Rules (Default Behavior)

```bash
$ scm show network nat-rule --folder Texas
---> 100%
NAT rules in folder 'Texas':
------------------------------------------------------------
Name: outbound-nat
  From: trust -> To: untrust
  Type: Source Translation
------------------------------------------------------------
Name: inbound-web
  From: untrust -> To: dmz
  Type: Destination Translation
------------------------------------------------------------
```

## Backup NAT Rules

Backup all NAT rule objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network nat-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--file TEXT` | Custom output filename | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup network nat-rule --folder Texas
---> 100%
Successfully backed up 12 NAT rules to nat_rule_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network nat-rule --folder Texas --file texas-nat-rules.yaml
---> 100%
Successfully backed up 12 NAT rules to texas-nat-rules.yaml
```

## Best Practices

1. **Order Rules Carefully**: NAT rules are evaluated in order; place more specific rules before general ones.
2. **Use Descriptive Names**: Name NAT rules to clearly indicate the translation direction and purpose.
3. **Specify Zones Explicitly**: Always define source and destination zones to limit NAT rule scope.
4. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
5. **Backup Before Changes**: Always backup existing NAT rules before making bulk modifications.
6. **Avoid Overlapping Rules**: Ensure NAT rules do not conflict with each other to prevent unexpected translations.
