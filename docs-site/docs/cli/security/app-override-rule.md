# App Override Rule

App override rules force the firewall to identify specific traffic as a particular application, bypassing the App-ID engine. The `scm` CLI provides commands to create, update, delete, move, and load app override rules.

## Overview

The `app-override-rule` commands allow you to:

- Create app override rules with protocol, port, and application mappings
- Update existing rule configurations
- Delete rules that are no longer needed
- Move rules to control processing order
- Bulk import rules from YAML files
- Export rules for backup or migration

## Set App Override Rule

Create or update an app override rule.

### Syntax

```bash
scm set security app-override-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Rule name | Yes |
| `--application TEXT` | Application to override | Yes |
| `--port TEXT` | Port(s) for the rule | Yes |
| `--protocol TEXT` | Protocol (tcp or udp) | Yes |
| `--rulebase TEXT` | Rulebase (pre, post, default) | No |
| `--description TEXT` | Description | No |
| `--source-zones TEXT` | Source zones | No |
| `--destination-zones TEXT` | Destination zones | No |
| `--disabled` | Disable the rule | No |
| `--tags TEXT` | Tags | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create Basic Override Rule

```bash
$ scm set security app-override-rule \
    --folder Texas \
    --name override-https \
    --application ssl \
    --port 8443 \
    --protocol tcp
---> 100%
Created app override rule: override-https in folder Texas
```

#### Create Override with Zones

```bash
$ scm set security app-override-rule \
    --folder Texas \
    --name custom-app-override \
    --application web-browsing \
    --port 9090 \
    --protocol tcp \
    --source-zones trust \
    --destination-zones untrust \
    --description "Override custom web app on port 9090"
---> 100%
Created app override rule: custom-app-override in folder Texas
```

## Move App Override Rule

Change the position of an app override rule. Rules are processed in order from top to bottom.

### Syntax

```bash
scm set security app-override-rule --move [OPTIONS]
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
$ scm set security app-override-rule --move \
    --folder Texas \
    --name override-https \
    --location top
---> 100%
Moved app override rule: override-https to top in folder Texas
```

#### Move Rule After Another Rule

```bash
$ scm set security app-override-rule --move \
    --folder Texas \
    --name custom-app-override \
    --location after \
    --reference override-https
---> 100%
Moved app override rule: custom-app-override after override-https in folder Texas
```

## Delete App Override Rule

Delete an app override rule from SCM.

### Syntax

```bash
scm delete security app-override-rule [OPTIONS]
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
$ scm delete security app-override-rule \
    --folder Texas \
    --name override-https \
    --force
---> 100%
Deleted app override rule: override-https from folder Texas
```

## Load App Override Rule

Load multiple app override rules from a YAML file.

### Syntax

```bash
scm load security app-override-rule [OPTIONS]
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
app_override_rules:
  - name: override-https
    folder: Texas
    application: ssl
    port: "8443"
    protocol: tcp

  - name: custom-app-override
    folder: Texas
    application: web-browsing
    port: "9090"
    protocol: tcp
    source_zones:
      - trust
    destination_zones:
      - untrust
    description: "Override custom web app on port 9090"
```

### Examples

#### Load with Original Locations

```bash
$ scm load security app-override-rule \
    --file app-overrides.yaml
---> 100%
✓ Loaded app override rule: override-https
✓ Loaded app override rule: custom-app-override

Successfully loaded 2 out of 2 app override rules from 'app-overrides.yaml'
```

#### Load with Folder Override

```bash
$ scm load security app-override-rule \
    --file app-overrides.yaml \
    --folder Austin
---> 100%
✓ Loaded app override rule: override-https
✓ Loaded app override rule: custom-app-override

Successfully loaded 2 out of 2 app override rules from 'app-overrides.yaml'
```

:::note
When using container override options (--folder, --snippet, --device), all rules
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show App Override Rule

Display app override rule objects.

### Syntax

```bash
scm show security app-override-rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Rule name to display | No |

\* One of --folder, --snippet, or --device is required.

:::note
When no `--name` is specified, all items are listed by default.
:::

### Examples

#### Show Specific Rule

```bash
$ scm show security app-override-rule \
    --folder Texas \
    --name override-https
---> 100%
App Override Rule: override-https
  Location: Folder 'Texas'
  Application: ssl
  Port: 8443
  Protocol: tcp
```

#### List All Rules (Default Behavior)

```bash
$ scm show security app-override-rule --folder Texas
---> 100%
App Override Rules in folder 'Texas':
------------------------------------------------------------
Name: override-https
  Application: ssl
  Port: 8443
  Protocol: tcp
------------------------------------------------------------
Name: custom-app-override
  Application: web-browsing
  Port: 9090
  Protocol: tcp
------------------------------------------------------------
```

## Backup App Override Rules

Backup all app override rule objects from a specified location to a YAML file.

### Syntax

```bash
scm backup security app-override-rule [OPTIONS]
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
$ scm backup security app-override-rule --folder Texas
---> 100%
Successfully backed up 8 app override rules to app_override_rule_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup security app-override-rule \
    --folder Texas \
    --file texas-app-overrides.yaml
---> 100%
Successfully backed up 8 app override rules to texas-app-overrides.yaml
```

## Best Practices

1. **Use Sparingly**: Only create app override rules when App-ID cannot correctly identify an application; prefer proper App-ID identification when possible.
2. **Be Specific with Ports**: Define exact ports rather than broad ranges to minimize the scope of the override.
3. **Specify Zones**: Include source and destination zones to limit the override to specific traffic paths.
4. **Order Rules Carefully**: Place more specific override rules above general ones since rules are processed top to bottom.
5. **Backup Before Changes**: Always backup existing rules before making bulk modifications via load commands.
