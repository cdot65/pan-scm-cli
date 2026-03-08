# Security Rules

Security rules define policies that control traffic flow between zones. The `scm` CLI provides commands to create, update, delete, move, and load security rules.

## Overview

The `rule` commands allow you to:

- Create security rules with source/destination zones, addresses, and applications
- Update existing rule configurations and security profiles
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
| Profiles | Security profiles applied to allowed traffic |

## Set Security Rule

Create or update a security rule.

### Syntax

```bash
scm set security rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder for the security rule | Yes |
| `--name TEXT` | Name of the security rule | Yes |
| `--description TEXT` | Description for the rule | No |
| `--source-zones LIST` | Source security zones | Yes |
| `--destination-zones LIST` | Destination security zones | Yes |
| `--source-addresses LIST` | Source address or address groups | Yes |
| `--destination-addresses LIST` | Destination address or address groups | Yes |
| `--applications LIST` | Applications to match | Yes |
| `--services LIST` | Services to match | Yes |
| `--action TEXT` | Action to take (allow, deny, drop) | Yes |
| `--log-start BOOLEAN` | Log at session start | No |
| `--log-end BOOLEAN` | Log at session end | No |
| `--disabled BOOLEAN` | Whether rule is disabled | No |
| `--tags LIST` | List of tags to apply to the rule | No |
| `--profile-group TEXT` | Security profile group to apply | No |
| `--anti-virus TEXT` | Anti-virus profile to apply | No |
| `--anti-spyware TEXT` | Anti-spyware profile to apply | No |
| `--vulnerability TEXT` | Vulnerability protection profile to apply | No |
| `--url-filtering TEXT` | URL filtering profile to apply | No |
| `--file-blocking TEXT` | File blocking profile to apply | No |
| `--data-filtering TEXT` | Data filtering profile to apply | No |
| `--wildfire-analysis TEXT` | WildFire analysis profile to apply | No |

### Examples

#### Create an Allow Rule

```bash
$ scm set security rule \
    --folder Shared \
    --name "Allow-Internal-Web" \
    --source-zones Trust \
    --destination-zones DMZ \
    --source-addresses "any" \
    --destination-addresses "web-servers" \
    --applications web-browsing \
    --services application-default \
    --action allow \
    --log-end true
---> 100%
Created security rule: Allow-Internal-Web in folder Shared
```

#### Create a Block Rule with Security Profiles

```bash
$ scm set security rule \
    --folder Shared \
    --name "Block-Malicious-Web" \
    --source-zones Untrust \
    --destination-zones DMZ \
    --source-addresses "any" \
    --destination-addresses "any" \
    --applications any \
    --services application-default \
    --action deny \
    --log-start true \
    --log-end true \
    --anti-virus "default-av" \
    --anti-spyware "default-as" \
    --url-filtering "strict-url-filtering"
---> 100%
Created security rule: Block-Malicious-Web in folder Shared
```

## Move Security Rule

Change the position of a security rule. Security rules are processed in order from top to bottom.

### Syntax

```bash
scm set security rule --move [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the security rules | Yes |
| `--name TEXT` | Name of the security rule to move | Yes |
| `--location TEXT` | Where to move the rule (top, bottom, before, after) | Yes |
| `--reference TEXT` | Reference rule name (required with before/after) | No\*\* |

\*\* Required when `--location` is `before` or `after`.

### Examples

#### Move Rule to Top

```bash
$ scm set security rule --move \
    --folder Shared \
    --name "Block-Malicious-Web" \
    --location top
---> 100%
Moved security rule: Block-Malicious-Web to top in folder Shared
```

#### Move Rule After Another Rule

```bash
$ scm set security rule --move \
    --folder Shared \
    --name "Allow-Internal-Web" \
    --location after \
    --reference "Allow-Internal-DNS"
---> 100%
Moved security rule: Allow-Internal-Web after Allow-Internal-DNS in folder Shared
```

## Delete Security Rule

Delete a security rule from SCM.

### Syntax

```bash
scm delete security rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the security rule | Yes |
| `--name TEXT` | Name of the security rule to delete | Yes |

### Example

```bash
$ scm delete security rule \
    --folder Shared \
    --name "Allow-Internal-Web"
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
| `--file TEXT` | Path to YAML file containing security rule definitions | Yes |
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
    anti_virus: default-av
    anti_spyware: default-as
    url_filtering: strict-url-filtering
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

!!! note
    When using container override options (--folder, --snippet, --device), all rules
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show Security Rule

Display security rule objects.

### Syntax

```bash
scm show security rule [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes |
| `--name TEXT` | Rule name to display | No |

!!! note
    When no `--name` is specified, all items are listed by default.

### Examples

#### Show Specific Rule

```bash
$ scm show security rule \
    --folder Shared \
    --name "Allow-Internal-Web"
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
| `--folder TEXT` | Folder to backup rules from | Yes |
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
2. **Apply Security Profiles**: Attach anti-virus, anti-spyware, vulnerability protection, and URL filtering profiles to allow rules for defense in depth.
3. **Enable Logging**: Use `--log-end true` on all rules for visibility; add `--log-start true` for deny rules to capture blocked traffic.
4. **Use Descriptive Names**: Name rules to clearly indicate their purpose (e.g., `Allow-Internal-Web`, `Block-Malicious-Traffic`).
5. **Tag Rules for Organization**: Apply tags to group related rules by function, department, or compliance requirement.
6. **Backup Before Changes**: Always backup existing rules before making bulk modifications via load commands.
