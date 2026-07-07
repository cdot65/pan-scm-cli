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
scm set object hip-object NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the HIP object (max 31 characters) | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes\* |
| `--snippet TEXT` | Snippet location | Yes\* |
| `--device TEXT` | Device location | Yes\* |
| `--description TEXT` | Description (max 255 characters) | No |
| `--host-info-os TEXT` | OS vendor (Microsoft, Apple, Google, Linux, Other) | No |
| `--host-info-os-value TEXT` | OS version or "All" | No |
| `--host-info-domain TEXT` | Domain criteria (is, is_not, contains) | No |
| `--host-info-domain-value TEXT` | Domain value to match | No |
| `--host-info-managed / --no-host-info-managed` | Managed state criteria | No |
| `--network-info-type TEXT` | Network type (is, is_not) | No |
| `--network-info-value TEXT` | Network value (wifi, mobile, ethernet, unknown) | No |
| `--patch-management-enabled / --no-patch-management-enabled` | Whether patch management is enabled | No |
| `--patch-management-missing-patches TEXT` | Missing patches check (has-any, has-none, has-all) | No |
| `--patch-management-severity INTEGER` | Patch severity level | No |
| `--disk-encryption-enabled / --no-disk-encryption-enabled` | Whether disk encryption is enabled | No |
| `--mobile-device-jailbroken / --no-mobile-device-jailbroken` | Jailbroken status | No |
| `--mobile-device-disk-encrypted / --no-mobile-device-disk-encrypted` | Disk encryption status | No |
| `--mobile-device-passcode-set / --no-mobile-device-passcode-set` | Passcode status | No |
| `--certificate-profile TEXT` | Certificate profile name | No |

\* Exactly one of `--folder`, `--snippet`, or `--device` is required.

### Examples

#### Create a Windows Workstation Compliance Policy

```bash
$ scm set object hip-object windows-compliance \
    --folder Texas \
    --description "Windows workstation compliance" \
    --host-info-os Microsoft \
    --host-info-os-value All \
    --host-info-managed \
    --disk-encryption-enabled \
    --patch-management-enabled
---> 100%
Created HIP object: windows-compliance in folder Texas
```

#### Create a Mobile Device Policy

```bash
$ scm set object hip-object mobile-policy \
    --folder Texas \
    --description "Mobile device compliance" \
    --no-mobile-device-jailbroken \
    --mobile-device-disk-encrypted \
    --mobile-device-passcode-set
---> 100%
Created HIP object: mobile-policy in folder Texas
```

#### Create Domain Membership Check

```bash
$ scm set object hip-object corp-domain \
    --folder Texas \
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
scm delete object hip-object NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the HIP object to delete | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes\* |
| `--snippet TEXT` | Snippet location | Yes\* |
| `--device TEXT` | Device location | Yes\* |
| `--force` | Skip confirmation prompt | No |

\* Exactly one of `--folder`, `--snippet`, or `--device` is required.

### Example

```bash
$ scm delete object hip-object windows-patches --folder Texas --force
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
scm show object hip-object [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the HIP object to show; omit to list all | No |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes\* |
| `--snippet TEXT` | Snippet location | Yes\* |
| `--device TEXT` | Device location | Yes\* |
| `--max-results INTEGER` | Maximum number of results to display | No |
| `--output [table\|json\|yaml]` | Output format (default: `table`) | No |

\* Exactly one of `--folder`, `--snippet`, or `--device` is required.

:::note
When no `NAME` argument is provided, all items are listed by default.
:::

### Examples

#### Show Specific HIP Object

```bash
$ scm show object hip-object windows-patches --folder Texas
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
