# HIP Profile Objects

Host Information Profile (HIP) profile objects combine multiple HIP objects to create comprehensive endpoint compliance policies in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load HIP profile objects.

## Overview

HIP profiles allow you to:

- Create profiles that reference multiple HIP objects
- Define match criteria with boolean logic
- Enforce multi-factor compliance requirements
- Use profiles in security policies
- Manage profile descriptions and organization

## Set HIP Profile

Create or update a HIP profile object.

### Syntax

```bash
scm set objects hip-profile [OPTIONS]
```

### Options

| Option               | Description                                         | Required |
| -------------------- | --------------------------------------------------- | -------- |
| `--folder TEXT`      | Folder for the HIP profile object                   | Yes\*    |
| `--snippet TEXT`     | Snippet for the HIP profile object                  | Yes\*    |
| `--device TEXT`      | Device for the HIP profile object                   | Yes\*    |
| `--name TEXT`        | Name of the HIP profile (max 31 characters)         | Yes      |
| `--match TEXT`       | Match criteria in JSON format (max 2048 characters) | Yes      |
| `--description TEXT` | Description (max 255 characters)                    | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

### Examples

#### Create Basic HIP Profile

```bash
$ scm set objects hip-profile \
    --folder Texas \
    --name basic-compliance \
    --match '{"windows-patches": {"is": true}}' \
    --description "Basic Windows patch compliance"
---> 100%
Created HIP profile: basic-compliance in folder Texas
```

#### Create Multi-Object Compliance Profile

```bash
$ scm set objects hip-profile \
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
scm delete objects hip-profile [OPTIONS]
```

### Options

| Option           | Description                               | Required |
| ---------------- | ----------------------------------------- | -------- |
| `--folder TEXT`  | Folder containing the HIP profile object  | Yes\*    |
| `--snippet TEXT` | Snippet containing the HIP profile object | Yes\*    |
| `--device TEXT`  | Device containing the HIP profile object  | Yes\*    |
| `--name TEXT`    | Name of the HIP profile object to delete  | Yes      |

\* You must specify exactly one of --folder, --snippet, or --device.

### Example

```bash
$ scm delete objects hip-profile --folder Texas --name secure-endpoints
---> 100%
Deleted HIP profile: secure-endpoints from folder Texas
```

## Load HIP Profiles

Load multiple HIP profile objects from a YAML file.

### Syntax

```bash
scm load objects hip-profile [OPTIONS]
```

### Options

| Option           | Description                                          | Required |
| ---------------- | ---------------------------------------------------- | -------- |
| `--file TEXT`    | Path to YAML file containing HIP profile definitions | Yes      |
| `--folder TEXT`  | Override folder location for all objects             | No       |
| `--snippet TEXT` | Override snippet location for all objects            | No       |
| `--device TEXT`  | Override device location for all objects             | No       |
| `--dry-run`      | Preview changes without applying them                | No       |

### YAML File Format

```yaml
---
hip_profiles:
  - name: basic-windows
    folder: Texas # Container location (folder, snippet, or device)
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

  - name: mobile-secure
    folder: Texas
    description: "Secure mobile devices"
    match: '{"mobile-compliance": {"is": true}}'
```

### Examples

#### Load with Original Locations

```bash
$ scm load objects hip-profile --file hip-profiles.yml
---> 100%
✓ Loaded HIP profile: basic-windows
✓ Loaded HIP profile: secure-windows
✓ Loaded HIP profile: corporate-windows
✓ Loaded HIP profile: secure-mac
✓ Loaded HIP profile: mobile-secure

Successfully loaded 5 out of 5 HIP profiles from 'hip-profiles.yml'
```

#### Load with Folder Override

```bash
$ scm load objects hip-profile --file hip-profiles.yml --folder Austin
---> 100%
✓ Loaded HIP profile: basic-windows
✓ Loaded HIP profile: secure-windows
✓ Loaded HIP profile: corporate-windows
✓ Loaded HIP profile: secure-mac
✓ Loaded HIP profile: mobile-secure

Successfully loaded 5 out of 5 HIP profiles from 'hip-profiles.yml'
```

!!! note
When using container override options (--folder, --snippet, --device), all HIP profiles will be loaded into the specified container, ignoring the container specified in the YAML file.

## Show HIP Profile

Display HIP profile objects.

### Syntax

```bash
scm show objects hip-profile [OPTIONS]
```

### Options

| Option           | Description                               | Required |
| ---------------- | ----------------------------------------- | -------- |
| `--folder TEXT`  | Folder containing the HIP profile object  | Yes\*    |
| `--snippet TEXT` | Snippet containing the HIP profile object | Yes\*    |
| `--device TEXT`  | Device containing the HIP profile object  | Yes\*    |
| `--name TEXT`    | Name of the HIP profile object to show    | No\*\*   |
| `--list`         | List all HIP profiles in the container    | No\*\*   |

\* You must specify exactly one of --folder, --snippet, or --device.
\*\* You must specify either --name or --list.

### Examples

#### Show Specific HIP Profile

```bash
$ scm show objects hip-profile --folder Texas --name secure-endpoints
---> 100%
HIP Profile: secure-endpoints
Location: Folder 'Texas'
Match: {"windows-patches": {"is": true}, "disk-encryption": {"is": true}, "antivirus": {"is": true}}
Description: Comprehensive endpoint security
ID: 123e4567-e89b-12d3-a456-426614174000
```

#### List All HIP Profiles

```bash
$ scm show objects hip-profile --folder Texas --list
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
scm backup objects hip-profile [OPTIONS]
```

### Options

| Option           | Description                                  | Required |
| ---------------- | -------------------------------------------- | -------- |
| `--folder TEXT`  | Folder to backup HIP profiles from           | No\*     |
| `--snippet TEXT` | Snippet to backup HIP profiles from          | No\*     |
| `--device TEXT`  | Device to backup HIP profiles from           | No\*     |
| `--file TEXT`    | Output filename (defaults to auto-generated) | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

### Examples

#### Backup from Folder

```bash
$ scm backup objects hip-profile --folder Texas
---> 100%
Successfully backed up 8 HIP profiles to hip-profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup objects hip-profile --folder Texas --file texas-hip-profiles.yaml
---> 100%
Successfully backed up 8 HIP profiles to texas-hip-profiles.yaml
```

## Best Practices

1. **Modular HIP Objects**: Create focused HIP objects that can be combined in profiles

2. **Progressive Requirements**: Start with basic requirements and add more for higher security

3. **Platform-Specific Profiles**: Create separate profiles for different operating systems

4. **Clear Naming**: Use descriptive names that indicate the compliance level

5. **Documentation**: Always include descriptions explaining the profile's purpose

6. **Use YAML for Bulk Operations**: For complex deployments, use YAML files

7. **Organize by Container**: Keep profiles organized in appropriate folders, snippets, or devices

## Match Criteria Format

### Basic Format

Match criteria use JSON format with HIP object references:

```json
{
  "hip-object-name": {
    "is": true
  }
}
```

### Multiple Objects (AND Logic)

All specified objects must match:

```json
{
  "windows-patches": {
    "is": true
  },
  "disk-encryption": {
    "is": true
  }
}
```

### Negative Matching

Check that a HIP object does NOT match:

```json
{
  "jailbroken-device": {
    "is": false
  }
}
```

### Complex Example

Multiple requirements with mixed logic:

```json
{
  "corp-domain": {
    "is": true
  },
  "windows-patches": {
    "is": true
  },
  "disk-encryption": {
    "is": true
  },
  "compromised-device": {
    "is": false
  }
}
```

## Additional Examples

### Basic Compliance Profiles

```bash
$ scm set objects hip-profile \
    --folder Shared \
    --name patch-compliance \
    --match '{"os-patches": {"is": true}}' \
    --description "Patch compliance only"
---> 100%
Created HIP profile: patch-compliance in folder Shared
```

### Platform-Specific Profile

```bash
$ scm set objects hip-profile \
    --folder Texas \
    --name windows-corporate \
    --match '{"corp-domain": {"is": true}, "windows-security": {"is": true}}' \
    --description "Corporate Windows requirements"
---> 100%
Created HIP profile: windows-corporate in folder Texas
```

### High Security Profile

```bash
$ scm set objects hip-profile \
    --folder Shared \
    --name high-security \
    --match '{"antivirus": {"is": true}, "os-patches": {"is": true}, "disk-encryption": {"is": true}, "corp-domain": {"is": true}}' \
    --description "High security requirements"
---> 100%
Created HIP profile: high-security in folder Shared
```

## Integration with Security Policies

HIP profiles are used in security rules for endpoint-based access control:

```bash
$ scm set security rule \
    --folder Shared \
    --name "Compliant-Access" \
    --source-hip "@secure-endpoints" \
    --destination-zones "Corporate" \
    --applications "any" \
    --action allow
---> 100%
Created security rule: Compliant-Access in folder Shared
```

## Notes

- Profile names must be unique within a container
- Maximum name length is 31 characters
- Match criteria use JSON format
- All HIP objects in match criteria must exist
- Profiles use AND logic (all conditions must match)
- Use "is": false for negative matching
- Profiles are referenced in policies using the "@" prefix
- GlobalProtect enforces HIP profiles on endpoints
