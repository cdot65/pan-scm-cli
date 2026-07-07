# Authentication Rule

Authentication rules enforce user authentication before allowing access to network resources. The `scm` CLI provides commands to create, update, delete, move, and load authentication rules.

## Overview

The `authentication-rule` commands allow you to:

- Create authentication rules with zone, service, and category matching
- Update existing rule configurations and authentication enforcement profiles
- Delete rules that are no longer needed
- Move rules to control processing order
- Bulk import rules from YAML files
- Export rules for backup or migration

## Set Authentication Rule

Create or update an authentication rule.

### Syntax

```bash
scm set security authentication-rule NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Rule name | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--rulebase TEXT` | Rulebase (pre, post, default) | No |
| `--description TEXT` | Description | No |
| `--source-zones TEXT` | Source zones | No |
| `--destination-zones TEXT` | Destination zones | No |
| `--service TEXT` | Services | No |
| `--category TEXT` | URL categories | No |
| `--authentication-enforcement TEXT` | Authentication profile | No |
| `--disabled` | Disable the rule | No |
| `--tags TEXT` | Tags | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create Basic Authentication Rule

```bash
$ scm set security authentication-rule auth-web \
    --folder Texas \
    --source-zones trust \
    --destination-zones untrust \
    --authentication-enforcement my-auth-profile
---> 100%
Created authentication rule: auth-web in folder Texas
```

#### Create Rule with Service and Category

```bash
$ scm set security authentication-rule auth-sensitive \
    --folder Texas \
    --source-zones trust \
    --destination-zones dmz \
    --service "service-https" \
    --category "financial-services" \
    --authentication-enforcement strict-auth \
    --description "Authenticate before accessing sensitive resources"
---> 100%
Created authentication rule: auth-sensitive in folder Texas
```

## Move Authentication Rule

Change the position of an authentication rule. Rules are processed in order from top to bottom.

### Syntax

```bash
scm move security authentication-rule NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the rule to move | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the rule | No\* |
| `--snippet TEXT` | Snippet containing the rule | No\* |
| `--device TEXT` | Device containing the rule | No\* |
| `--destination TEXT` | Where to move (top, bottom, before, after) | Yes |
| `--destination-rule TEXT` | UUID of the reference rule (required with before/after) | No\*\* |
| `--rulebase TEXT` | Rulebase (pre or post; default: pre) | No |

\* One of --folder, --snippet, or --device is required.

\*\* Required when `--destination` is `before` or `after`.

### Examples

#### Move Rule to Top

```bash
$ scm move security authentication-rule auth-sensitive \
    --folder Texas \
    --destination top
---> 100%
Moved authentication rule: auth-sensitive to top in folder Texas
```

#### Move Rule Before Another Rule

```bash
$ scm move security authentication-rule auth-web \
    --folder Texas \
    --destination before \
    --destination-rule 123e4567-e89b-12d3-a456-426614174000
---> 100%
Moved authentication rule: auth-web before rule 123e4567-e89b-12d3-a456-426614174000 in folder Texas
```

## Delete Authentication Rule

Delete an authentication rule from SCM.

### Syntax

```bash
scm delete security authentication-rule NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Rule name to delete | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--rulebase TEXT` | Rulebase to use (pre, post, or default; default: pre) | No |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete security authentication-rule auth-web \
    --folder Texas \
    --force
---> 100%
Deleted authentication rule: auth-web from folder Texas
```

## Load Authentication Rule

Load multiple authentication rules from a YAML file.

### Syntax

```bash
scm load security authentication-rule [OPTIONS]
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
authentication_rules:
  - name: auth-web
    folder: Texas
    description: "Authenticate web traffic"
    source_zones:
      - trust
    destination_zones:
      - untrust
    authentication_enforcement: my-auth-profile

  - name: auth-sensitive
    folder: Texas
    description: "Authenticate before accessing sensitive resources"
    source_zones:
      - trust
    destination_zones:
      - dmz
    service:
      - service-https
    category:
      - financial-services
    authentication_enforcement: strict-auth
```

### Examples

#### Load with Original Locations

```bash
$ scm load security authentication-rule \
    --file auth-rules.yaml
---> 100%
✓ Loaded authentication rule: auth-web
✓ Loaded authentication rule: auth-sensitive

Successfully loaded 2 out of 2 authentication rules from 'auth-rules.yaml'
```

#### Load with Folder Override

```bash
$ scm load security authentication-rule \
    --file auth-rules.yaml \
    --folder Austin
---> 100%
✓ Loaded authentication rule: auth-web
✓ Loaded authentication rule: auth-sensitive

Successfully loaded 2 out of 2 authentication rules from 'auth-rules.yaml'
```

:::note
When using container override options (--folder, --snippet, --device), all rules
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show Authentication Rule

Display authentication rule objects.

### Syntax

```bash
scm show security authentication-rule [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Rule name to display; omit to list all | No |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--rulebase TEXT` | Rulebase to use (pre, post, or default; default: pre) | No |
| `--output, -o [table\|json\|yaml]` | Output format (default: table) | No |
| `--max-results INTEGER` | Maximum number of results to display | No |

\* One of --folder, --snippet, or --device is required.

:::note
When no `NAME` is specified, all items are listed by default.
:::

### Examples

#### Show Specific Rule

```bash
$ scm show security authentication-rule auth-web \
    --folder Texas
---> 100%
Authentication Rule: auth-web
  Location: Folder 'Texas'
  Source Zones: trust
  Destination Zones: untrust
  Authentication Enforcement: my-auth-profile
```

#### List All Rules (Default Behavior)

```bash
$ scm show security authentication-rule --folder Texas
---> 100%
Authentication Rules in folder 'Texas':
------------------------------------------------------------
Name: auth-web
  Source Zones: trust
  Destination Zones: untrust
  Authentication Enforcement: my-auth-profile
------------------------------------------------------------
Name: auth-sensitive
  Source Zones: trust
  Destination Zones: dmz
  Authentication Enforcement: strict-auth
------------------------------------------------------------
```

## Backup Authentication Rules

Backup all authentication rule objects from a specified location to a YAML file.

### Syntax

```bash
scm backup security authentication-rule [OPTIONS]
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
$ scm backup security authentication-rule --folder Texas
---> 100%
Successfully backed up 6 authentication rules to authentication_rule_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup security authentication-rule \
    --folder Texas \
    --file texas-auth-rules.yaml
---> 100%
Successfully backed up 6 authentication rules to texas-auth-rules.yaml
```

## Best Practices

1. **Match Specific Traffic**: Define source zones, destination zones, and services to target authentication requirements to specific traffic flows.
2. **Order Rules Carefully**: Place more specific authentication rules above general ones since rules are processed top to bottom.
3. **Use Authentication Enforcement Profiles**: Reference pre-configured authentication profiles to ensure consistent authentication behavior.
4. **Use Category Matching**: Combine URL categories with authentication rules for context-aware authentication requirements.
5. **Backup Before Changes**: Always backup existing rules before making bulk modifications via load commands.
