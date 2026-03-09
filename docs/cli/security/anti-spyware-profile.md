# Anti-Spyware Profile

Anti-spyware profiles define threat detection and prevention rules for spyware, command-and-control traffic, and other malicious activity. The `scm` CLI provides commands to create, update, delete, and load anti-spyware profiles.

## Overview

The `anti-spyware-profile` commands allow you to:

- Create anti-spyware profiles with threat blocking rules
- Update existing profile configurations
- Delete profiles that are no longer needed
- Bulk import profiles from YAML files
- Export profiles for backup or migration

## Set Anti-Spyware Profile

Create or update an anti-spyware profile.

### Syntax

```bash
scm set security anti-spyware-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Profile name | Yes |
| `--description TEXT` | Profile description | No |
| `--cloud-inline-analysis / --no-cloud-inline-analysis` | Enable cloud inline analysis | No |
| `--block-critical-high` | Add default rule to block critical and high severity threats | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create Basic Profile

```bash
$ scm set security anti-spyware-profile \
    --folder Texas \
    --name strict-security \
    --description "Block critical threats"
---> 100%
Created anti-spyware profile: strict-security in folder Texas
```

#### Create Profile Blocking Critical and High Severity

```bash
$ scm set security anti-spyware-profile \
    --folder Texas \
    --name block-threats \
    --block-critical-high \
    --cloud-inline-analysis
---> 100%
Created anti-spyware profile: block-threats in folder Texas
```

#### Create Profile in Snippet

```bash
$ scm set security anti-spyware-profile \
    --snippet Security-Best-Practice \
    --name standard-protection
---> 100%
Created anti-spyware profile: standard-protection in snippet Security-Best-Practice
```

## Delete Anti-Spyware Profile

Delete an anti-spyware profile from SCM.

### Syntax

```bash
scm delete security anti-spyware-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Profile name to delete | Yes |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete security anti-spyware-profile \
    --folder Texas \
    --name strict-security \
    --force
---> 100%
Deleted anti-spyware profile: strict-security from folder Texas
```

## Load Anti-Spyware Profile

Load multiple anti-spyware profiles from a YAML file.

### Syntax

```bash
scm load security anti-spyware-profile [OPTIONS]
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
anti_spyware_profiles:
  - name: strict-security
    folder: Texas
    description: "Block critical threats"
    cloud_inline_analysis: true

  - name: standard-protection
    folder: Texas
    description: "Standard spyware protection"
```

### Examples

#### Load with Original Locations

```bash
$ scm load security anti-spyware-profile \
    --file anti-spyware.yaml
---> 100%
✓ Loaded anti-spyware profile: strict-security
✓ Loaded anti-spyware profile: standard-protection

Successfully loaded 2 out of 2 anti-spyware profiles from 'anti-spyware.yaml'
```

#### Load with Folder Override

```bash
$ scm load security anti-spyware-profile \
    --file anti-spyware.yaml \
    --folder Austin
---> 100%
✓ Loaded anti-spyware profile: strict-security
✓ Loaded anti-spyware profile: standard-protection

Successfully loaded 2 out of 2 anti-spyware profiles from 'anti-spyware.yaml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all profiles
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show Anti-Spyware Profile

Display anti-spyware profile objects.

### Syntax

```bash
scm show security anti-spyware-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Profile name to display | No |

\* One of --folder, --snippet, or --device is required.

!!! note
    When no `--name` is specified, all items are listed by default.

### Examples

#### Show Specific Profile

```bash
$ scm show security anti-spyware-profile \
    --folder Texas \
    --name strict-security
---> 100%
Anti-Spyware Profile: strict-security
  Location: Folder 'Texas'
  Description: Block critical threats
  Cloud Inline Analysis: true
```

#### List All Profiles (Default Behavior)

```bash
$ scm show security anti-spyware-profile --folder Texas
---> 100%
Anti-Spyware Profiles in folder 'Texas':
------------------------------------------------------------
Name: strict-security
  Description: Block critical threats
  Cloud Inline Analysis: true
------------------------------------------------------------
Name: standard-protection
  Description: Standard spyware protection
------------------------------------------------------------
```

## Backup Anti-Spyware Profiles

Backup all anti-spyware profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup security anti-spyware-profile [OPTIONS]
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
$ scm backup security anti-spyware-profile --folder Texas
---> 100%
Successfully backed up 5 anti-spyware profiles to anti_spyware_profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup security anti-spyware-profile \
    --folder Texas \
    --file texas-anti-spyware.yaml
---> 100%
Successfully backed up 5 anti-spyware profiles to texas-anti-spyware.yaml
```

## Best Practices

1. **Block Critical and High Severity**: Use `--block-critical-high` to create profiles that automatically block the most dangerous threats.
2. **Enable Cloud Analysis**: Turn on `--cloud-inline-analysis` for real-time cloud-based threat detection on critical traffic paths.
3. **Use Descriptive Names**: Name profiles to reflect their purpose and severity level (e.g., `strict-security`, `standard-protection`).
4. **Backup Before Changes**: Always backup existing profiles before making bulk modifications via load commands.
5. **Test in Non-Production**: Create and validate profiles in a test folder before applying to production environments.
