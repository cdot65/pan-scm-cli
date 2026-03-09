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
scm set security authentication-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Rule name | Yes |
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
$ scm set security authentication-rule \
    --folder Texas \
    --name auth-web \
    --source-zones trust \
    --destination-zones untrust \
    --authentication-enforcement my-auth-profile
---> 100%
Created authentication rule: auth-web in folder Texas
```

#### Create Rule with Service and Category

```bash
$ scm set security authentication-rule \
    --folder Texas \
    --name auth-sensitive \
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
scm set security authentication-rule --move [OPTIONS]
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
$ scm set security authentication-rule --move \
    --folder Texas \
    --name auth-sensitive \
    --location top
---> 100%
Moved authentication rule: auth-sensitive to top in folder Texas
```

#### Move Rule Before Another Rule

```bash
$ scm set security authentication-rule --move \
    --folder Texas \
    --name auth-web \
    --location before \
    --reference auth-sensitive
---> 100%
Moved authentication rule: auth-web before auth-sensitive in folder Texas
```

## Delete Authentication Rule

Delete an authentication rule from SCM.

### Syntax

```bash
scm delete security authentication-rule [OPTIONS]
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
$ scm delete security authentication-rule \
    --folder Texas \
    --name auth-web \
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

!!! note
    When using container override options (--folder, --snippet, --device), all rules
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show Authentication Rule

Display authentication rule objects.

### Syntax

```bash
scm show security authentication-rule [OPTIONS]
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
$ scm show security authentication-rule \
    --folder Texas \
    --name auth-web
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
