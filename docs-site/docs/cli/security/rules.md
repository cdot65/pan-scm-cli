# Security Rules

Security rules define policies that control traffic flow between zones. The `scm` CLI provides commands to create, update, delete, move, and load security rules.

## Overview

The `rule` commands allow you to:

- Create security rules with source/destination zones, addresses, and applications
- Update existing rule configurations
- Delete rules that are no longer needed
- Move rules to control processing order
- Bulk import rules from YAML files
- Export rules for backup or migration

## Rule Components

Security rules consist of several components:

| Component | Description |
| --- | --- |
| Source/Destination | Zones, addresses, and users that define traffic endpoints |
| Applications | Applications to match (e.g., web-browsing, ssl) |
| Services | Services to match (e.g., application-default) |
| Action | What happens to matching traffic (allow, deny, drop) |
| Rulebase | Where the rule lives (pre, post, or default) |

## Set Security Rule

Create or update a security rule.

### Syntax

```bash
scm set security rule NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the security rule | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder path for the security rule | One of folder/snippet/device |
| `--snippet TEXT` | Snippet path for the security rule | One of folder/snippet/device |
| `--device TEXT` | Device path for the security rule | One of folder/snippet/device |
| `--source-zones TEXT` | Source security zones (repeat for multiple) | Yes |
| `--destination-zones TEXT` | Destination security zones (repeat for multiple) | Yes |
| `--source-addresses TEXT` | Source addresses or address groups (repeat for multiple) | No |
| `--destination-addresses TEXT` | Destination addresses or address groups (repeat for multiple) | No |
| `--applications TEXT` | Applications to match (repeat for multiple) | No |
| `--services TEXT` | Services to match (repeat for multiple) | No |
| `--action TEXT` | Action to take (allow, deny, drop; default: allow) | No |
| `--description TEXT` | Description of the security rule | No |
| `--tags TEXT` | Tags (repeat for multiple) | No |
| `--enabled / --disabled` | Enable or disable the rule (default: enabled) | No |
| `--log-start` | Log at session start | No |
| `--log-end` | Log at session end | No |
| `--log-setting TEXT` | Log forwarding profile | No |
| `--rulebase TEXT` | Rulebase to use (pre, post, or default; default: pre) | No |

### Examples

#### Create an Allow Rule

```bash
$ scm set security rule Allow-Internal-Web \
    --folder Shared \
    --source-zones Trust \
    --destination-zones DMZ \
    --source-addresses any \
    --destination-addresses web-servers \
    --applications web-browsing \
    --services application-default \
    --action allow \
    --log-end
---> 100%
Created security rule: Allow-Internal-Web in folder Shared
```

#### Create a Block Rule in the Post Rulebase

```bash
$ scm set security rule Block-Malicious-Web \
    --folder Shared \
    --source-zones Untrust \
    --destination-zones DMZ \
    --source-addresses any \
    --destination-addresses any \
    --applications any \
    --services application-default \
    --action deny \
    --log-start \
    --log-end \
    --rulebase post
---> 100%
Created security rule: Block-Malicious-Web in folder Shared
```

## Move Security Rule

Change the position of a security rule. Security rules are processed in order from top to bottom.

### Syntax

```bash
scm move security rule NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the security rule to move | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the rule | One of folder/snippet/device |
| `--snippet TEXT` | Snippet containing the rule | One of folder/snippet/device |
| `--device TEXT` | Device containing the rule | One of folder/snippet/device |
| `--destination TEXT` | Where to move (top, bottom, before, after) | Yes |
| `--destination-rule TEXT` | UUID of the reference rule (required with before/after) | No\*\* |
| `--rulebase TEXT` | Rulebase (pre or post; default: pre) | No |

\*\* Required when `--destination` is `before` or `after`.

### Examples

#### Move Rule to Top

```bash
$ scm move security rule Block-Malicious-Web \
    --folder Shared \
    --destination top
---> 100%
Moved security rule: Block-Malicious-Web to top in folder Shared
```

#### Move Rule After Another Rule

```bash
$ scm move security rule Allow-Internal-Web \
    --folder Shared \
    --destination after \
    --destination-rule 123e4567-e89b-12d3-a456-426614174000
---> 100%
Moved security rule: Allow-Internal-Web after rule 123e4567-e89b-12d3-a456-426614174000 in folder Shared
```

## Delete Security Rule

Delete a security rule from SCM.

### Syntax

```bash
scm delete security rule NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the security rule to delete | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the security rule | One of folder/snippet/device |
| `--snippet TEXT` | Snippet containing the security rule | One of folder/snippet/device |
| `--device TEXT` | Device containing the security rule | One of folder/snippet/device |
| `--rulebase TEXT` | Rulebase to use (pre, post, or default; default: pre) | No |
| `--force` | Skip confirmation prompt | No |

### Example

```bash
$ scm delete security rule Allow-Internal-Web \
    --folder Shared \
    --force
---> 100%
Deleted security rule: Allow-Internal-Web from folder Shared
```

## Load Security Rules

Load multiple security rules from a YAML file.

### Syntax

```bash
scm load security rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file PATH` | Path to YAML file containing security rule definitions | Yes |
| `--folder TEXT` | Override folder location for all rules | No |
| `--snippet TEXT` | Override snippet location for all rules | No |
| `--device TEXT` | Override device location for all rules | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
security_rules:
  - name: Allow-Internal-Web
    folder: Shared
    description: "Allow internal users to access web servers"
    source_zones:
      - Trust
    destination_zones:
      - DMZ
    source_addresses:
      - any
    destination_addresses:
      - web-servers
    applications:
      - web-browsing
      - ssl
    services:
      - application-default
    action: allow
    log_end: true
    tags:
      - internal-access

  - name: Block-Malicious-Web
    folder: Shared
    description: "Block malicious web traffic"
    source_zones:
      - Untrust
    destination_zones:
      - DMZ
    source_addresses:
      - any
    destination_addresses:
      - any
    applications:
      - any
    services:
      - application-default
    action: deny
    log_start: true
    log_end: true
    tags:
      - security
      - blocking
```

### Examples

#### Load with Original Locations

```bash
$ scm load security rule --file security-rules.yaml
---> 100%
✓ Loaded security rule: Allow-Internal-Web
✓ Loaded security rule: Block-Malicious-Web

Successfully loaded 2 out of 2 security rules from 'security-rules.yaml'
```

#### Load with Folder Override

```bash
$ scm load security rule \
    --file security-rules.yaml \
    --folder Austin
---> 100%
✓ Loaded security rule: Allow-Internal-Web
✓ Loaded security rule: Block-Malicious-Web

Successfully loaded 2 out of 2 security rules from 'security-rules.yaml'
```

:::note
When using container override options (--folder, --snippet, --device), all rules
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show Security Rule

Display security rule objects.

### Syntax

```bash
scm show security rule [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the security rule to show; omit to list all | No |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the security rule | One of folder/snippet/device |
| `--snippet TEXT` | Snippet containing the security rule | One of folder/snippet/device |
| `--device TEXT` | Device containing the security rule | One of folder/snippet/device |
| `--rulebase TEXT` | Rulebase to use (pre, post, or default; default: pre) | No |
| `--output, -o [table\|json\|yaml]` | Output format (default: table) | No |
| `--max-results INTEGER` | Maximum number of results to display | No |

:::note
When no `NAME` is specified, all items are listed by default.
:::

### Examples

#### Show Specific Rule

```bash
$ scm show security rule Allow-Internal-Web --folder Shared
---> 100%
Security Rule: Allow-Internal-Web
  Location: Folder 'Shared'
  Source Zones: Trust
  Destination Zones: DMZ
  Source Addresses: any
  Destination Addresses: web-servers
  Applications: web-browsing
  Services: application-default
  Action: allow
  Log End: true
```

#### List All Rules (Default Behavior)

```bash
$ scm show security rule --folder Shared
---> 100%
Security Rules in folder 'Shared':
------------------------------------------------------------
Name: Allow-Internal-Web
  Source Zones: Trust
  Destination Zones: DMZ
  Action: allow
------------------------------------------------------------
Name: Block-Malicious-Web
  Source Zones: Untrust
  Destination Zones: DMZ
  Action: deny
------------------------------------------------------------
```

## Backup Security Rules

Backup all security rule objects from a specified location to a YAML file.

### Syntax

```bash
scm backup security rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup rules from | One of folder/snippet/device |
| `--snippet TEXT` | Snippet to backup rules from | One of folder/snippet/device |
| `--device TEXT` | Device to backup rules from | One of folder/snippet/device |
| `--rulebase TEXT` | Rulebase to use (pre, post, or default; default: pre) | No |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

### Examples

#### Backup from Folder

```bash
$ scm backup security rule --folder Shared
---> 100%
Successfully backed up 15 security rules to security_rule_folder_shared_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup security rule \
    --folder Shared \
    --file shared-security-rules.yaml
---> 100%
Successfully backed up 15 security rules to shared-security-rules.yaml
```

## Best Practices

1. **Order Rules Carefully**: Place more specific rules above general rules since rules are processed top to bottom; use the Move command to control order.
2. **Mind the Rulebase**: Use the `pre` rulebase for rules evaluated before local rules and `post` for cleanup rules evaluated after.
3. **Enable Logging**: Use `--log-end` on all rules for visibility; add `--log-start` for deny rules to capture blocked traffic.
4. **Use Descriptive Names**: Name rules to clearly indicate their purpose (e.g., `Allow-Internal-Web`, `Block-Malicious-Traffic`).
5. **Tag Rules for Organization**: Apply tags to group related rules by function, department, or compliance requirement.
6. **Backup Before Changes**: Always backup existing rules before making bulk modifications via load commands.
