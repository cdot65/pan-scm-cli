# HIP Object Management

This section covers the commands for managing Host Information Profile (HIP) objects in Strata Cloud Manager.

## Overview

HIP objects define criteria for evaluating endpoint compliance and security posture. The `hip-object` commands allow you to:

- Define host information criteria (OS, domain, version)
- Configure patch management requirements
- Set disk encryption requirements
- Define mobile device criteria
- Establish certificate requirements
- Create complex compliance checks

## Commands

### Creating/Updating HIP Objects

Basic Windows patch compliance:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects hip-object --folder Texas --name windows-patches \
  --description "Windows security patch compliance" \
  --patch-management-vendor-name "Microsoft Corporation" \
  --patch-management-product-name "Windows" \
  --patch-management-criteria-is-installed yes \
  --patch-management-missing-patches check-not-exist
<span style="color: green;">✓</span> HIP object 'windows-patches' created successfully
```

</div>

Disk encryption check:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects hip-object --folder Texas --name disk-encryption \
  --description "Disk encryption requirement" \
  --disk-encryption-vendor-name "BitLocker" \
  --disk-encryption-product-name "BitLocker Drive Encryption" \
  --disk-encryption-criteria-is-installed is \
  --disk-encryption-state is
<span style="color: green;">✓</span> HIP object 'disk-encryption' created successfully
```

</div>

Domain and OS check:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects hip-object --folder Texas --name corp-domain \
  --description "Corporate domain membership" \
  --host-info-domain contains --host-info-domain-value "corp.company.com" \
  --host-info-os "Microsoft" --host-info-os-value "All"
<span style="color: green;">✓</span> HIP object 'corp-domain' created successfully
```

</div>

### Listing HIP Objects

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects hip-object --folder Texas --list
HIP objects in folder 'Texas':
- windows-patches
- disk-encryption
- corp-domain
- antivirus-check
```

</div>

### Showing HIP Object Details

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects hip-object --folder Texas --name windows-patches
HIP Object: windows-patches
  Description: Windows security patch compliance
  Patch Management:
    Vendor: Microsoft Corporation
    Product: Windows
    Criteria: Is Installed
    Missing Patches: check-not-exist
  Folder: Texas
```

</div>

### Deleting HIP Objects

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli delete objects hip-object --folder Texas --name windows-patches
<span style="color: green;">✓</span> HIP object 'windows-patches' deleted successfully
```

</div>

### Bulk Operations

Load multiple HIP objects from a YAML file:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli load objects hip-object --folder Texas --file hip-objects.yml
<span style="color: green;">✓</span> Loaded 12 HIP objects successfully
```

</div>

Backup existing HIP objects:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli backup objects hip-object --folder Texas
<span style="color: green;">✓</span> Backed up 12 HIP objects to hip-object-texas.yaml
```

</div>

## YAML Configuration Format

HIP objects can be defined in YAML for bulk operations:

```yaml
hip_objects:
  - name: windows-security
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
    description: "Windows BitLocker requirement"
    disk_encryption_enabled: true
    disk_encryption_vendors:
      - name: "Microsoft"
        product:
          - "BitLocker Drive Encryption"
    
  - name: disk-encryption-mac
    description: "macOS FileVault requirement"
    disk_encryption_enabled: true
    disk_encryption_vendors:
      - name: "Apple"
        product:
          - "FileVault"
    
  - name: corporate-domain
    description: "Corporate domain membership"
    host_info_domain: "contains"
    host_info_domain_value: "corp.company.com"
    host_info_managed: true
    
  - name: antivirus-windows
    description: "Windows antivirus check"
    antimalware_enabled: true
    antimalware_vendors:
      - name: "Microsoft"
        product:
          - "Windows Defender"
      - name: "CrowdStrike"
        product:
          - "Falcon"
    
  - name: mobile-compliance
    description: "Mobile device compliance"
    mobile_device_jailbroken: false
    mobile_device_disk_encrypted: true
    mobile_device_passcode_set: true
    mobile_device_last_checkin_time: "days"
    mobile_device_last_checkin_value: 7
    
  - name: certificate-check
    description: "Client certificate validation"
    certificate_profile: "Client-Cert-Profile"
    certificate_attributes:
      - name: "issuer"
        value: "CN=Company CA"
```

## Configuration Options

### Required Parameters

- `--name`: Name of the HIP object (max 31 characters)

### Optional Parameters

- `--description`: Detailed description (max 255 characters)

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
- `--patch-management-missing-patches`: Missing patches check (has-any, has-none, has-all)
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

### Context Parameters

Exactly one context parameter must be specified:

- `--folder`: Folder name (e.g., "Texas", "Shared")
- `--snippet`: Snippet name for Panorama
- `--device`: Device name for NGFW

## Examples

### Windows Compliance Checks

```bash
# Comprehensive Windows security
scm-cli set objects hip-object --folder Shared --name windows-full \
  --description "Full Windows compliance check" \
  --host-info-os "Microsoft" --host-info-os-value "All" \
  --patch-management-enabled \
  --patch-management-missing-patches "check-not-exist" \
  --patch-management-vendor-name "Microsoft Corporation" \
  --patch-management-product-name "Windows" \
  --disk-encryption-enabled \
  --disk-encryption-vendor-name "Microsoft" \
  --disk-encryption-product-name "BitLocker Drive Encryption" \
  --disk-encryption-criteria-is-installed is
```

### macOS Compliance Checks

```bash
# macOS with FileVault
scm-cli set objects hip-object --folder Shared --name macos-security \
  --description "macOS security requirements" \
  --host-info-os "Apple" --host-info-os-value "All" \
  --disk-encryption-enabled \
  --disk-encryption-vendor-name "Apple" \
  --disk-encryption-product-name "FileVault" \
  --disk-encryption-criteria-is-installed is
```

### Domain Membership

```bash
# Corporate domain check
scm-cli set objects hip-object --folder Shared --name domain-member \
  --description "Must be domain member" \
  --host-info-domain contains --host-info-domain-value "corp.company.com" \
  --host-info-managed true
```

### Mobile Device Compliance

```bash
# Secure mobile device
scm-cli set objects hip-object --folder Shared --name mobile-secure \
  --description "Mobile device security" \
  --mobile-device-jailbroken false \
  --mobile-device-disk-encrypted true \
  --mobile-device-passcode-set true \
  --mobile-device-last-checkin-time days \
  --mobile-device-last-checkin-value 1
```

### Network-Based Checks

```bash
# WiFi network check
scm-cli set objects hip-object --folder Shared --name wifi-only \
  --description "WiFi connections only" \
  --network-info-type is --network-info-value wifi

# Not on mobile network
scm-cli set objects hip-object --folder Shared --name no-mobile \
  --description "Prohibit mobile networks" \
  --network-info-type is_not --network-info-value mobile
```

## Integration with HIP Profiles

HIP objects are used in HIP profiles for policy enforcement:

```bash
# Create HIP profile using HIP objects
scm-cli set objects hip-profile --folder Shared --name secure-endpoints \
  --match '{"windows-patches": {"is": true}, "disk-encryption": {"is": true}}'
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

## Criteria Logic

### String Matching Criteria

For domain, host name, client version, etc.:
- `is`: Exact match
- `is_not`: Not equal to
- `contains`: Substring match

### Boolean Criteria

For managed state, encryption, etc.:
- `true`: Condition must be true
- `false`: Condition must be false

### Missing Patches Criteria

- `check-not-exist`: No critical patches missing
- `has-any`: Has at least one specified patch
- `has-none`: Has none of the specified patches
- `has-all`: Has all specified patches

## Notes

- HIP object names must be unique within a folder
- Maximum name length is 31 characters
- Criteria pairs must be complete (e.g., domain + domain_value)
- HIP objects define individual checks
- HIP profiles combine multiple HIP objects
- Some criteria are platform-specific
- GlobalProtect collects HIP data from endpoints