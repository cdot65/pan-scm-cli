# WildFire Antivirus Profile

WildFire antivirus profiles configure file forwarding to WildFire for cloud-based malware analysis and prevention. The `scm` CLI provides commands to create, update, delete, and load WildFire antivirus profiles.

## Overview

The `wildfire-antivirus-profile` commands allow you to:

- Create WildFire antivirus profiles with file forwarding rules
- Update existing profile configurations including packet capture settings
- Delete profiles that are no longer needed
- Bulk import profiles from YAML files
- Export profiles for backup or migration

## Set WildFire Antivirus Profile

Create or update a WildFire antivirus profile.

### Syntax

```bash
scm set security wildfire-antivirus-profile NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--description TEXT` | Profile description | No |
| `--rules TEXT` | Rules configuration as JSON | No |
| `--packet-capture / --no-packet-capture` | Enable packet capture | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create Basic Profile

```bash
$ scm set security wildfire-antivirus-profile wf-basic \
    --folder Texas \
    --description "Basic WildFire profile"
---> 100%
Created WildFire antivirus profile: wf-basic in folder Texas
```

#### Create Profile with Custom Rules

```bash
$ scm set security wildfire-antivirus-profile wf-custom \
    --folder Texas \
    --rules '[{"name":"Forward All","direction":"both","analysis":"public-cloud","application":["any"],"file_type":["any"]}]'
---> 100%
Created WildFire antivirus profile: wf-custom in folder Texas
```

#### Create Profile with Packet Capture

```bash
$ scm set security wildfire-antivirus-profile wf-capture \
    --folder Texas \
    --packet-capture
---> 100%
Created WildFire antivirus profile: wf-capture in folder Texas
```

## Delete WildFire Antivirus Profile

Delete a WildFire antivirus profile from SCM.

### Syntax

```bash
scm delete security wildfire-antivirus-profile NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name to delete | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete security wildfire-antivirus-profile wf-basic \
    --folder Texas \
    --force
---> 100%
Deleted WildFire antivirus profile: wf-basic from folder Texas
```

## Load WildFire Antivirus Profile

Load multiple WildFire antivirus profiles from a YAML file.

### Syntax

```bash
scm load security wildfire-antivirus-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing profile definitions | Yes |
| `--folder TEXT` | Override folder location for all profiles | No |
| `--snippet TEXT` | Override snippet location for all profiles | No |
| `--device TEXT` | Override device location for all profiles | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
wildfire_antivirus_profiles:
  - name: wf-basic
    folder: Texas
    description: "Basic WildFire profile"

  - name: wf-custom
    folder: Texas
    description: "Custom WildFire rules"
    rules:
      - name: Forward All
        direction: both
        analysis: public-cloud
        application:
          - any
        file_type:
          - any
```

### Examples

#### Load with Original Locations

```bash
$ scm load security wildfire-antivirus-profile \
    --file wildfire.yaml
---> 100%
✓ Loaded WildFire antivirus profile: wf-basic
✓ Loaded WildFire antivirus profile: wf-custom

Successfully loaded 2 out of 2 WildFire antivirus profiles from 'wildfire.yaml'
```

#### Load with Folder Override

```bash
$ scm load security wildfire-antivirus-profile \
    --file wildfire.yaml \
    --folder Austin
---> 100%
✓ Loaded WildFire antivirus profile: wf-basic
✓ Loaded WildFire antivirus profile: wf-custom

Successfully loaded 2 out of 2 WildFire antivirus profiles from 'wildfire.yaml'
```

:::note
When using container override options (--folder, --snippet, --device), all profiles
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show WildFire Antivirus Profile

Display WildFire antivirus profile objects.

### Syntax

```bash
scm show security wildfire-antivirus-profile [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Profile name to display; omit to list all | No |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--output, -o [table\|json\|yaml]` | Output format (default: table) | No |
| `--max-results INTEGER` | Maximum number of results to display | No |

\* One of --folder, --snippet, or --device is required.

:::note
When no `NAME` is specified, all items are listed by default.
:::

### Examples

#### Show Specific Profile

```bash
$ scm show security wildfire-antivirus-profile wf-basic \
    --folder Texas
---> 100%
WildFire Antivirus Profile: wf-basic
  Location: Folder 'Texas'
  Description: Basic WildFire profile
```

#### List All Profiles (Default Behavior)

```bash
$ scm show security wildfire-antivirus-profile --folder Texas
---> 100%
WildFire Antivirus Profiles in folder 'Texas':
------------------------------------------------------------
Name: wf-basic
  Description: Basic WildFire profile
------------------------------------------------------------
Name: wf-custom
  Description: Custom WildFire rules
------------------------------------------------------------
```

## Backup WildFire Antivirus Profiles

Backup all WildFire antivirus profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup security wildfire-antivirus-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup profiles from | No\* |
| `--snippet TEXT` | Snippet to backup profiles from | No\* |
| `--device TEXT` | Device to backup profiles from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup security wildfire-antivirus-profile --folder Texas
---> 100%
Successfully backed up 3 WildFire antivirus profiles to wildfire_antivirus_profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup security wildfire-antivirus-profile \
    --folder Texas \
    --file texas-wildfire.yaml
---> 100%
Successfully backed up 3 WildFire antivirus profiles to texas-wildfire.yaml
```

## Best Practices

1. **Forward All File Types**: Use rules with `file_type: ["any"]` and `application: ["any"]` to ensure comprehensive malware analysis coverage.
2. **Enable Packet Capture**: Use `--packet-capture` for forensic analysis when investigating potential malware incidents.
3. **Use Public Cloud Analysis**: Set `analysis` to `public-cloud` for the broadest threat intelligence coverage from WildFire.
4. **Backup Before Changes**: Always backup existing profiles before making bulk modifications via load commands.
5. **Combine with Anti-Spyware**: Layer WildFire profiles with anti-spyware and vulnerability protection for defense in depth.
