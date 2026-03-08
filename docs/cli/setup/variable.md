# Variable

Variables define reusable values scoped to folders, snippets, or devices in Strata Cloud Manager. Variable names must start with `$`. The `scm` CLI provides commands to create, update, delete, list, bulk import, and back up variables.

## Overview

The `variable` commands allow you to:

- Create variables with typed values scoped to a container
- Update existing variable configurations
- Delete variables that are no longer needed
- Bulk import variables from YAML files
- Export variables for backup or migration

## Variable Types

| Type | Description | Example Value |
| --- | --- | --- |
| `percent` | Percentage value | `80` |
| `count` | Numeric count | `100` |
| `ip-netmask` | IP address with netmask | `192.168.1.0/24` |
| `zone` | Security zone name | `trust` |
| `ip-range` | IP address range | `192.168.1.1-192.168.1.254` |
| `ip-wildcard` | Wildcard IP pattern | `10.0.0.0/0.0.255.255` |
| `fqdn` | Fully qualified domain name | `dns.example.com` |
| `port` | Port number | `8080` |
| `egress-max` | Maximum egress bandwidth | `1000` |

## Set Variable

Create or update a variable.

### Syntax

```bash
scm set setup variable [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Variable name (must start with $) | Yes |
| `--type TEXT` | Variable type | Yes |
| `--value TEXT` | Variable value | Yes |
| `--folder TEXT` | Folder scope | No\* |
| `--snippet TEXT` | Snippet scope | No\* |
| `--device TEXT` | Device scope | No\* |
| `--description TEXT` | Description | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create an Egress Max Variable

```bash
$ scm set setup variable \
    --name "\$egress-max" \
    --type egress-max \
    --value 1000 \
    --folder Texas
---> 100%
Created variable: $egress-max in folder Texas
```

#### Create an FQDN Variable in a Snippet

```bash
$ scm set setup variable \
    --name "\$dns-server" \
    --type fqdn \
    --value dns.example.com \
    --snippet "DNS-Config"
---> 100%
Created variable: $dns-server in snippet DNS-Config
```

#### Create a Variable with Description

```bash
$ scm set setup variable \
    --name "\$web-port" \
    --type port \
    --value 8080 \
    --folder Texas \
    --description "Primary web server port"
---> 100%
Created variable: $web-port in folder Texas
```

## Delete Variable

Delete a variable from SCM.

### Syntax

```bash
scm delete setup variable [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the variable to delete | Yes |
| `--folder TEXT` | Folder scope | No\* |
| `--snippet TEXT` | Snippet scope | No\* |
| `--device TEXT` | Device scope | No\* |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete setup variable --name "\$egress-max" --folder Texas
---> 100%
Deleted variable: $egress-max from folder Texas
```

## Load Variable

Load multiple variables from a YAML file.

### Syntax

```bash
scm load setup variable [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file PATH` | YAML file to load configurations from | Yes |
| `--dry-run` | Simulate execution without applying changes | No |

### YAML File Format

```yaml
---
variables:
  - name: "$egress-max"
    type: egress-max
    value: "1000"
    folder: Texas
    description: "Maximum egress bandwidth"

  - name: "$dns-server"
    type: fqdn
    value: "dns.example.com"
    snippet: "DNS-Config"
```

### Examples

#### Load Variables from File

```bash
$ scm load setup variable --file variables.yaml
---> 100%
✓ Loaded variable: $egress-max
✓ Loaded variable: $dns-server

Processed 2 variables from variables.yaml
```

#### Dry Run

```bash
$ scm load setup variable --file variables.yaml --dry-run
---> 100%
Dry run mode: would apply the following configurations:
- name: $egress-max
  type: egress-max
  value: '1000'
  folder: Texas
  description: Maximum egress bandwidth
- name: $dns-server
  type: fqdn
  value: dns.example.com
  snippet: DNS-Config
```

## Show Variable

Display variable objects.

### Syntax

```bash
scm show setup variable [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the variable to show | No |
| `--folder TEXT` | Folder scope | No\* |
| `--snippet TEXT` | Snippet scope | No\* |
| `--device TEXT` | Device scope | No\* |

\* One of --folder, --snippet, or --device is required when listing variables.

!!! note
    When no `--name` is specified, all variables in the specified container are listed
    by default.

### Examples

#### Show Specific Variable

```bash
$ scm show setup variable --folder Texas --name "\$egress-max"
---> 100%
Variable: $egress-max
================================================================================
Type: egress-max
Value: 1000
Folder: Texas
```

#### List All Variables in a Folder (Default Behavior)

```bash
$ scm show setup variable --folder Texas
---> 100%
Variables (3):
--------------------------------------------------------------------------------
Name: $egress-max
  Type: egress-max
  Value: 1000
--------------------------------------------------------------------------------
Name: $web-port
  Type: port
  Value: 8080
  Description: Primary web server port
--------------------------------------------------------------------------------
Name: $dns-server
  Type: fqdn
  Value: dns.example.com
--------------------------------------------------------------------------------
```

## Backup Variables

Backup variable objects from a specified location to a YAML file.

### Syntax

```bash
scm backup setup variable [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder scope | No\* |
| `--snippet TEXT` | Snippet scope | No\* |
| `--device TEXT` | Device scope | No\* |
| `--file TEXT` | Output filename for backup | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup setup variable --folder Texas
---> 100%
Successfully backed up 5 variables to variables_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup setup variable --folder Texas --file texas-variables.yaml
---> 100%
Successfully backed up 5 variables to texas-variables.yaml
```

#### Backup from Snippet

```bash
$ scm backup setup variable --snippet "DNS-Config"
---> 100%
Successfully backed up 2 variables to variables_20240115_120545.yaml
```

## Best Practices

1. **Use the `$` Prefix**: Always prefix variable names with `$` as required by SCM convention.
2. **Choose Correct Types**: Select the variable type that matches the intended use to ensure proper validation.
3. **Scope Appropriately**: Assign variables to the most specific container (folder, snippet, or device) needed.
4. **Add Descriptions**: Include descriptions to document each variable's purpose for team members.
5. **Back Up Before Changes**: Export your variables before making significant modifications.
6. **Use Dry Run for Bulk Imports**: Preview bulk imports with `--dry-run` before applying changes.

## Related Topics

- [Folder](folder.md)
- [Label](label.md)
- [Snippet](snippet.md)
