# HIP Object

Host Information Profile (HIP) objects define criteria for evaluating endpoint compliance and security posture in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load HIP objects.

## Overview

The `hip-object` commands allow you to:

- Define host information criteria (OS, domain, version)
- Configure patch management and disk encryption requirements
- Define mobile device compliance criteria
- Delete HIP objects that are no longer needed
- Bulk import HIP objects from YAML files
- Export HIP objects for backup or migration

## Set HIP Object

Create or update a HIP object.

### Syntax

```bash
scm set object hip-object [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder for the HIP object | No\* |
| `--snippet TEXT` | Snippet for the HIP object | No\* |
| `--device TEXT` | Device for the HIP object | No\* |
| `--name TEXT` | Name of the HIP object (max 31 characters) | Yes |
| `--description TEXT` | Description (max 255 characters) | No |
| `--host-info-os TEXT` | OS vendor (Microsoft, Apple, Google, Linux, Other) | No |
| `--host-info-os-value TEXT` | OS version or "All" | No |
| `--host-info-domain TEXT` | Domain criteria (is, is_not, contains) | No |
| `--host-info-domain-value TEXT` | Domain value to match | No |
| `--host-info-managed` | Managed state (true/false) | No |
| `--patch-management-enabled` | Enable patch management checks | No |
| `--patch-management-vendor-name TEXT` | Vendor name | No |
| `--patch-management-product-name TEXT` | Product name | No |
| `--patch-management-criteria-is-installed TEXT` | Installation criteria | No |
| `--patch-management-missing-patches TEXT` | Missing patches check | No |
| `--disk-encryption-enabled` | Enable disk encryption checks | No |
| `--disk-encryption-vendor-name TEXT` | Encryption vendor | No |
| `--disk-encryption-product-name TEXT` | Encryption product | No |
| `--disk-encryption-criteria-is-installed TEXT` | Installation criteria (is, is_not) | No |
| `--disk-encryption-state TEXT` | Encryption state (is, is_not) | No |
| `--mobile-device-jailbroken TEXT` | Jailbreak status | No |
| `--mobile-device-disk-encrypted TEXT` | Disk encryption status | No |
| `--mobile-device-passcode-set TEXT` | Passcode requirement | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create Basic Windows Patch Compliance

```bash
$ scm set object hip-object \
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
$ scm set object hip-object \
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

#### Create Domain Membership Check

```bash
$ scm set object hip-object \
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

## Delete HIP Object

Delete a HIP object from SCM.

### Syntax

```bash
scm delete object hip-object [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the HIP object | No\* |
| `--snippet TEXT` | Snippet containing the HIP object | No\* |
| `--device TEXT` | Device containing the HIP object | No\* |
| `--name TEXT` | Name of the HIP object to delete | Yes |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete object hip-object --folder Texas --name windows-patches --force
---> 100%
Deleted HIP object: windows-patches from folder Texas
```

## Load HIP Objects

Load multiple HIP objects from a YAML file.

### Syntax

```bash
scm load object hip-object [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing HIP object definitions | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
hip_objects:
  - name: windows-security
    folder: Texas
    description: "Windows security compliance"
    host_info_os: "Microsoft"
    host_info_os_value: "All"
    patch_management_enabled: true
    patch_management_missing_patches: "check-not-exist"
    patch_management_vendors:
      - name: "Microsoft Corporation"
        product:
          - "Windows"

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
$ scm load object hip-object --file hip-objects.yml
---> 100%
✓ Loaded HIP object: windows-security
✓ Loaded HIP object: disk-encryption-windows
✓ Loaded HIP object: corporate-domain

Successfully loaded 3 out of 3 HIP objects from 'hip-objects.yml'
```

#### Load with Folder Override

```bash
$ scm load object hip-object --file hip-objects.yml --folder Austin
---> 100%
✓ Loaded HIP object: windows-security
✓ Loaded HIP object: disk-encryption-windows
✓ Loaded HIP object: corporate-domain

Successfully loaded 3 out of 3 HIP objects from 'hip-objects.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all HIP objects
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show HIP Object

Display HIP objects.

### Syntax

```bash
scm show object hip-object [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the HIP object | No\* |
| `--snippet TEXT` | Snippet containing the HIP object | No\* |
| `--device TEXT` | Device containing the HIP object | No\* |
| `--name TEXT` | Name of the HIP object to show | No |

:::note
When no `--name` is specified, all items are listed by default.
:::

\* One of --folder, --snippet, or --device is required.

### Examples

#### Show Specific HIP Object

```bash
$ scm show object hip-object --folder Texas --name windows-patches
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
$ scm show object hip-object --folder Texas
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
scm backup object hip-object [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup HIP objects from | No\* |
| `--snippet TEXT` | Snippet to backup HIP objects from | No\* |
| `--device TEXT` | Device to backup HIP objects from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup object hip-object --folder Texas
---> 100%
Successfully backed up 12 HIP objects to hip-object_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object hip-object --folder Texas --file texas-hip-objects.yaml
---> 100%
Successfully backed up 12 HIP objects to texas-hip-objects.yaml
```

## Best Practices

1. **Modular Design**: Create focused HIP objects for specific checks (one for patches, one for encryption, one for domain).
2. **OS-Specific Objects**: Create separate objects for different operating systems.
3. **Naming Convention**: Use descriptive names indicating the check purpose.
4. **Documentation**: Always include descriptions explaining the compliance requirement.
5. **Testing**: Test HIP objects with sample endpoints before deployment.
6. **Use YAML for Bulk Operations**: For complex deployments, use YAML files.
7. **Organize by Container**: Keep HIP objects organized in appropriate folders, snippets, or devices.
