# HIP Profile Objects

Host Information Profile (HIP) profile objects combine multiple HIP objects to create comprehensive endpoint compliance policies in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load HIP profile objects.

## Overview

The `hip-profile` commands allow you to:

- Create profiles that reference multiple HIP objects
- Define match criteria with boolean logic in JSON format
- Delete HIP profiles that are no longer needed
- Bulk import HIP profiles from YAML files
- Export HIP profiles for backup or migration

## Match Criteria Format

Match criteria use JSON format with HIP object references:

```json
{
  "hip-object-name": {
    "is": true
  }
}
```

Multiple objects use AND logic (all conditions must match). Use `"is": false` for negative matching.

## Set HIP Profile

Create or update a HIP profile object.

### Syntax

```bash
scm set object hip-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder for the HIP profile object | No\* |
| `--snippet TEXT` | Snippet for the HIP profile object | No\* |
| `--device TEXT` | Device for the HIP profile object | No\* |
| `--name TEXT` | Name of the HIP profile (max 31 characters) | Yes |
| `--match TEXT` | Match criteria in JSON format (max 2048 characters) | Yes |
| `--description TEXT` | Description (max 255 characters) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create Basic HIP Profile

```bash
$ scm set object hip-profile \
    --folder Texas \
    --name basic-compliance \
    --match '{"windows-patches": {"is": true}}' \
    --description "Basic Windows patch compliance"
---> 100%
Created HIP profile: basic-compliance in folder Texas
```

#### Create Multi-Object Compliance Profile

```bash
$ scm set object hip-profile \
    --folder Texas \
    --name secure-endpoints \
    --match '{"windows-patches": {"is": true}, "disk-encryption": {"is": true}, "antivirus": {"is": true}}' \
    --description "Comprehensive endpoint security"
---> 100%
Created HIP profile: secure-endpoints in folder Texas
```

## Delete HIP Profile

Delete a HIP profile object from SCM.

### Syntax

```bash
scm delete object hip-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the HIP profile object | No\* |
| `--snippet TEXT` | Snippet containing the HIP profile object | No\* |
| `--device TEXT` | Device containing the HIP profile object | No\* |
| `--name TEXT` | Name of the HIP profile object to delete | Yes |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete object hip-profile --folder Texas --name secure-endpoints --force
---> 100%
Deleted HIP profile: secure-endpoints from folder Texas
```

## Load HIP Profiles

Load multiple HIP profile objects from a YAML file.

### Syntax

```bash
scm load object hip-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing HIP profile definitions | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
hip_profiles:
  - name: basic-windows
    folder: Texas
    description: "Basic Windows compliance"
    match: '{"windows-patches": {"is": true}}'

  - name: secure-windows
    folder: Texas
    description: "Secure Windows endpoints"
    match: '{"windows-patches": {"is": true}, "disk-encryption": {"is": true}, "antivirus": {"is": true}}'

  - name: corporate-windows
    folder: Texas
    description: "Corporate Windows requirements"
    match: '{"corp-domain": {"is": true}, "windows-security": {"is": true}, "disk-encryption": {"is": true}}'

  - name: secure-mac
    folder: Texas
    description: "Secure macOS endpoints"
    match: '{"macos-patches": {"is": true}, "filevault": {"is": true}}'
```

### Examples

#### Load with Original Locations

```bash
$ scm load object hip-profile --file hip-profiles.yml
---> 100%
✓ Loaded HIP profile: basic-windows
✓ Loaded HIP profile: secure-windows
✓ Loaded HIP profile: corporate-windows
✓ Loaded HIP profile: secure-mac

Successfully loaded 4 out of 4 HIP profiles from 'hip-profiles.yml'
```

#### Load with Folder Override

```bash
$ scm load object hip-profile --file hip-profiles.yml --folder Austin
---> 100%
✓ Loaded HIP profile: basic-windows
✓ Loaded HIP profile: secure-windows
✓ Loaded HIP profile: corporate-windows
✓ Loaded HIP profile: secure-mac

Successfully loaded 4 out of 4 HIP profiles from 'hip-profiles.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all HIP profiles
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show HIP Profile

Display HIP profile objects.

### Syntax

```bash
scm show object hip-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the HIP profile object | No\* |
| `--snippet TEXT` | Snippet containing the HIP profile object | No\* |
| `--device TEXT` | Device containing the HIP profile object | No\* |
| `--name TEXT` | Name of the HIP profile object to show | No |

:::note
When no `--name` is specified, all items are listed by default.
:::

\* One of --folder, --snippet, or --device is required.

### Examples

#### Show Specific HIP Profile

```bash
$ scm show object hip-profile --folder Texas --name secure-endpoints
---> 100%
HIP Profile: secure-endpoints
  Location: Folder 'Texas'
  Match: {"windows-patches": {"is": true}, "disk-encryption": {"is": true}, "antivirus": {"is": true}}
  Description: Comprehensive endpoint security
  ID: 123e4567-e89b-12d3-a456-426614174000
```

#### List All HIP Profiles (Default Behavior)

```bash
$ scm show object hip-profile --folder Texas
---> 100%
HIP Profiles in folder 'Texas':
------------------------------------------------------------
Name: basic-compliance
  Location: Folder 'Texas'
  Match: {"windows-patches": {"is": true}}
  Description: Basic Windows patch compliance
------------------------------------------------------------
Name: secure-endpoints
  Location: Folder 'Texas'
  Match: {"windows-patches": {"is": true}, "disk-encryption": {"is": true}, "antivirus": {"is": true}}
  Description: Comprehensive endpoint security
------------------------------------------------------------
Name: windows-corporate
  Location: Folder 'Texas'
  Match: {"corp-domain": {"is": true}, "windows-security": {"is": true}}
  Description: Corporate Windows requirements
------------------------------------------------------------
```

## Backup HIP Profiles

Backup all HIP profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup object hip-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup HIP profiles from | No\* |
| `--snippet TEXT` | Snippet to backup HIP profiles from | No\* |
| `--device TEXT` | Device to backup HIP profiles from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup object hip-profile --folder Texas
---> 100%
Successfully backed up 8 HIP profiles to hip-profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object hip-profile --folder Texas --file texas-hip-profiles.yaml
---> 100%
Successfully backed up 8 HIP profiles to texas-hip-profiles.yaml
```

## Best Practices

1. **Modular HIP Objects**: Create focused HIP objects that can be combined in profiles.
2. **Progressive Requirements**: Start with basic requirements and add more for higher security tiers.
3. **Platform-Specific Profiles**: Create separate profiles for different operating systems.
4. **Clear Naming**: Use descriptive names that indicate the compliance level.
5. **Documentation**: Always include descriptions explaining the profile's purpose.
6. **Use YAML for Bulk Operations**: For complex deployments, use YAML files.
7. **Organize by Container**: Keep profiles organized in appropriate folders, snippets, or devices.
