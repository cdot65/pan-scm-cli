# HIP Object

Host Information Profile (HIP) objects define criteria for evaluating endpoint compliance and security posture in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load HIP objects.

## Overview

HIP objects allow you to:

- Define host information criteria (OS, domain, version)
- Configure patch management requirements
- Set disk encryption requirements
- Define mobile device criteria
- Establish certificate requirements
- Create complex compliance checks

## Set HIP Object

Create or update a HIP object.

### Syntax

```bash
scm set objects hip-object [OPTIONS]
```

### Options

| Option                   | Description                                | Required |
| ------------------------ | ------------------------------------------ | -------- |
| `--folder TEXT`          | Folder for the HIP object                  | Yes\*    |
| `--snippet TEXT`         | Snippet for the HIP object                 | Yes\*    |
| `--device TEXT`          | Device for the HIP object                  | Yes\*    |
| `--name TEXT`            | Name of the HIP object (max 31 characters) | Yes      |
| `--description TEXT`     | Description (max 255 characters)           | No       |
| Host Information Options | See detailed list below                    | No       |
| Patch Management Options | See detailed list below                    | No       |
| Disk Encryption Options  | See detailed list below                    | No       |
| Mobile Device Options    | See detailed list below                    | No       |
| Certificate Options      | See detailed list below                    | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

### Examples

#### Create Basic Windows Patch Compliance

```bash
$ scm set objects hip-object \
    --folder Texas \
    --name windows-patches \
    --description "Windows security patch compliance" \
    --patch-management-vendor-name "Microsoft Corporation" \
    --patch-management-product-name "Windows" \
    --patch-management-criteria-is-installed yes \
    --patch-management-missing-patches check-not-exist
---> 100%
Created HIP object: windows-patches in folder Texas
```

#### Create Disk Encryption Check

```bash
$ scm set objects hip-object \
    --folder Texas \
    --name disk-encryption \
    --description "Disk encryption requirement" \
    --disk-encryption-vendor-name "BitLocker" \
    --disk-encryption-product-name "BitLocker Drive Encryption" \
    --disk-encryption-criteria-is-installed is \
    --disk-encryption-state is
---> 100%
Created HIP object: disk-encryption in folder Texas
```

## Delete HIP Object

Delete a HIP object from SCM.

### Syntax

```bash
scm delete objects hip-object [OPTIONS]
```

### Options

| Option           | Description                       | Required |
| ---------------- | --------------------------------- | -------- |
| `--folder TEXT`  | Folder containing the HIP object  | Yes\*    |
| `--snippet TEXT` | Snippet containing the HIP object | Yes\*    |
| `--device TEXT`  | Device containing the HIP object  | Yes\*    |
| `--name TEXT`    | Name of the HIP object to delete  | Yes      |

\* You must specify exactly one of --folder, --snippet, or --device.

### Example

```bash
$ scm delete objects hip-object --folder Texas --name windows-patches
---> 100%
Deleted HIP object: windows-patches from folder Texas
```

## Load HIP Objects

Load multiple HIP objects from a YAML file.

### Syntax

```bash
scm load objects hip-object [OPTIONS]
```

### Options

| Option           | Description                                         | Required |
| ---------------- | --------------------------------------------------- | -------- |
| `--file TEXT`    | Path to YAML file containing HIP object definitions | Yes      |
| `--folder TEXT`  | Override folder location for all objects            | No       |
| `--snippet TEXT` | Override snippet location for all objects           | No       |
| `--device TEXT`  | Override device location for all objects            | No       |
| `--dry-run`      | Preview changes without applying them               | No       |

### YAML File Format

```yaml
---
hip_objects:
  - name: windows-security
    folder: Texas # Container location (folder, snippet, or device)
    description: "Windows security compliance"
    host_info_os: "Microsoft"
    host_info_os_value: "All"
    patch_management_enabled: true
    patch_management_missing_patches: "check-not-exist"
    patch_management_vendors:
      - name: "Microsoft Corporation"
        product:
          - "Windows"

  - name: macos-security
    folder: Texas
    description: "macOS security compliance"
    host_info_os: "Apple"
    host_info_os_value: "All"
    patch_management_enabled: true
    patch_management_missing_patches: "check-not-exist"
    patch_management_vendors:
      - name: "Apple Inc."
        product:
          - "macOS"

  - name: disk-encryption-windows
    folder: Texas
    description: "Windows BitLocker requirement"
    disk_encryption_enabled: true
    disk_encryption_vendors:
      - name: "Microsoft"
        product:
          - "BitLocker Drive Encryption"

  - name: corporate-domain
    folder: Texas
    description: "Corporate domain membership"
    host_info_domain: "contains"
    host_info_domain_value: "corp.company.com"
    host_info_managed: true
```

### Examples

#### Load with Original Locations

```bash
$ scm load objects hip-object --file hip-objects.yml
---> 100%
✓ Loaded HIP object: windows-security
✓ Loaded HIP object: macos-security
✓ Loaded HIP object: disk-encryption-windows
✓ Loaded HIP object: corporate-domain

Successfully loaded 4 out of 4 HIP objects from 'hip-objects.yml'
```

#### Load with Folder Override

```bash
$ scm load objects hip-object --file hip-objects.yml --folder Austin
---> 100%
✓ Loaded HIP object: windows-security
✓ Loaded HIP object: macos-security
✓ Loaded HIP object: disk-encryption-windows
✓ Loaded HIP object: corporate-domain

Successfully loaded 4 out of 4 HIP objects from 'hip-objects.yml'
```

!!! note
When using container override options (--folder, --snippet, --device), all HIP objects will be loaded into the specified container, ignoring the container specified in the YAML file.

## Show HIP Object

Display HIP objects.

### Syntax

```bash
scm show objects hip-object [OPTIONS]
```

### Options

| Option           | Description                           | Required |
| ---------------- | ------------------------------------- | -------- |
| `--folder TEXT`  | Folder containing the HIP object      | Yes\*    |
| `--snippet TEXT` | Snippet containing the HIP object     | Yes\*    |
| `--device TEXT`  | Device containing the HIP object      | Yes\*    |
| `--name TEXT`    | Name of the HIP object to show        | No\*\*   |
| `--list`         | List all HIP objects in the container | No\*\*   |

\* You must specify exactly one of --folder, --snippet, or --device.
\*\* If --name is not specified, all items will be listed.

### Examples

#### Show Specific HIP Object

```bash
$ scm show objects hip-object --folder Texas --name windows-patches
---> 100%
HIP Object: windows-patches
Location: Folder 'Texas'
Description: Windows security patch compliance
Patch Management:
  Vendor: Microsoft Corporation
  Product: Windows
  Criteria: Is Installed
  Missing Patches: check-not-exist
ID: 123e4567-e89b-12d3-a456-426614174000
```

#### List All HIP Objects (Default Behavior)

```bash
$ scm show objects hip-object --folder Texas
---> 100%
HIP Objects in folder 'Texas':
------------------------------------------------------------
Name: windows-patches
  Location: Folder 'Texas'
  Description: Windows security patch compliance
  Patch Management: Microsoft Corporation - Windows
------------------------------------------------------------
Name: disk-encryption
  Location: Folder 'Texas'
  Description: Disk encryption requirement
  Disk Encryption: BitLocker - BitLocker Drive Encryption
------------------------------------------------------------
Name: corp-domain
  Location: Folder 'Texas'
  Description: Corporate domain membership
  Host Info: Domain contains corp.company.com, OS: Microsoft
------------------------------------------------------------
```

## Backup HIP Objects

Backup all HIP objects from a specified location to a YAML file.

### Syntax

```bash
scm backup objects hip-object [OPTIONS]
```

### Options

| Option           | Description                                  | Required |
| ---------------- | -------------------------------------------- | -------- |
| `--folder TEXT`  | Folder to backup HIP objects from            | No\*     |
| `--snippet TEXT` | Snippet to backup HIP objects from           | No\*     |
| `--device TEXT`  | Device to backup HIP objects from            | No\*     |
| `--file TEXT`    | Output filename (defaults to auto-generated) | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

### Examples

#### Backup from Folder

```bash
$ scm backup objects hip-object --folder Texas
---> 100%
Successfully backed up 12 HIP objects to hip-object_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup objects hip-object --folder Texas --file texas-hip-objects.yaml
---> 100%
Successfully backed up 12 HIP objects to texas-hip-objects.yaml
```

## Best Practices

1. **Modular Design**: Create focused HIP objects for specific checks

   - One for patches
   - One for encryption
   - One for domain membership

2. **OS-Specific Objects**: Create separate objects for different operating systems

3. **Naming Convention**: Use descriptive names indicating the check purpose

4. **Documentation**: Always include descriptions explaining the compliance requirement

5. **Testing**: Test HIP objects with sample endpoints before deployment

6. **Use YAML for Bulk Operations**: For complex deployments, use YAML files

7. **Organize by Container**: Keep HIP objects organized in appropriate folders, snippets, or devices

## Additional Examples

### Windows Compliance Checks

```bash
$ scm set objects hip-object \
    --folder Shared \
    --name windows-full \
    --description "Full Windows compliance check" \
    --host-info-os "Microsoft" \
    --host-info-os-value "All" \
    --patch-management-enabled \
    --patch-management-missing-patches "check-not-exist" \
    --patch-management-vendor-name "Microsoft Corporation" \
    --patch-management-product-name "Windows" \
    --disk-encryption-enabled \
    --disk-encryption-vendor-name "Microsoft" \
    --disk-encryption-product-name "BitLocker Drive Encryption" \
    --disk-encryption-criteria-is-installed is
---> 100%
Created HIP object: windows-full in folder Shared
```

### Domain and OS Check

```bash
$ scm set objects hip-object \
    --folder Texas \
    --name corp-domain \
    --description "Corporate domain membership" \
    --host-info-domain contains \
    --host-info-domain-value "corp.company.com" \
    --host-info-os "Microsoft" \
    --host-info-os-value "All"
---> 100%
Created HIP object: corp-domain in folder Texas
```

### Mobile Device Compliance

```bash
$ scm set objects hip-object \
    --folder Shared \
    --name mobile-secure \
    --description "Mobile device security" \
    --mobile-device-jailbroken false \
    --mobile-device-disk-encrypted true \
    --mobile-device-passcode-set true \
    --mobile-device-last-checkin-time days \
    --mobile-device-last-checkin-value 1
---> 100%
Created HIP object: mobile-secure in folder Shared
```

## Option Details

### Host Information Criteria

- `--host-info-domain`: Domain criteria (is, is_not, contains)
- `--host-info-domain-value`: Domain value to match
- `--host-info-os`: OS vendor (Microsoft, Apple, Google, Linux, Other)
- `--host-info-os-value`: OS version or "All"
- `--host-info-client-version`: GlobalProtect client version criteria
- `--host-info-client-version-value`: Version value
- `--host-info-host-name`: Host name criteria
- `--host-info-host-name-value`: Host name value
- `--host-info-host-id`: Host ID criteria
- `--host-info-host-id-value`: Host ID value
- `--host-info-managed`: Managed state (true/false)
- `--host-info-serial-number`: Serial number criteria
- `--host-info-serial-number-value`: Serial number value

### Network Information

- `--network-info-type`: Network type criteria (is, is_not)
- `--network-info-value`: Network value (wifi, mobile, ethernet, unknown)

### Patch Management

- `--patch-management-enabled`: Enable patch management checks
- `--patch-management-missing-patches`: Missing patches check (has-any, has-none, has-all, check-not-exist)
- `--patch-management-severity`: Severity level (0-100000)
- `--patch-management-patches`: Specific patches (comma-separated)
- `--patch-management-vendor-name`: Vendor name
- `--patch-management-product-name`: Product name

### Disk Encryption

- `--disk-encryption-enabled`: Enable disk encryption checks
- `--disk-encryption-vendor-name`: Encryption vendor
- `--disk-encryption-product-name`: Encryption product
- `--disk-encryption-criteria-is-installed`: Installation criteria (is, is_not)
- `--disk-encryption-state`: Encryption state (is, is_not)

### Mobile Device

- `--mobile-device-jailbroken`: Jailbreak status
- `--mobile-device-disk-encrypted`: Disk encryption status
- `--mobile-device-passcode-set`: Passcode requirement
- `--mobile-device-last-checkin-time`: Check-in time type (days, hours)
- `--mobile-device-last-checkin-value`: Check-in time value (1-65535)
- `--mobile-device-has-malware`: Malware presence
- `--mobile-device-has-unmanaged-app`: Unmanaged apps

### Certificate

- `--certificate-profile`: Certificate profile name

## Integration with HIP Profiles

HIP objects are used in HIP profiles for policy enforcement:

```bash
$ scm set objects hip-profile \
    --folder Shared \
    --name secure-endpoints \
    --match '{"windows-patches": {"is": true}, "disk-encryption": {"is": true}}'
---> 100%
Created HIP profile: secure-endpoints in folder Shared
```

## Notes

- HIP object names must be unique within a container
- Maximum name length is 31 characters
- Criteria pairs must be complete (e.g., domain + domain_value)
- HIP objects define individual checks
- HIP profiles combine multiple HIP objects
- Some criteria are platform-specific
- GlobalProtect collects HIP data from endpoints
- String matching criteria: is (exact match), is_not (not equal), contains (substring)
- Boolean criteria: true (must be true), false (must be false)
- Missing patches criteria: check-not-exist, has-any, has-none, has-all
