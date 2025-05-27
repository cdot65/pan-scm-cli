# HIP Profile Management

This section covers the commands for managing Host Information Profile (HIP) profiles in Strata Cloud Manager.

## Overview

HIP profiles combine multiple HIP objects to create comprehensive endpoint compliance policies. The `hip-profile` commands allow you to:

- Create profiles that reference multiple HIP objects
- Define match criteria with boolean logic
- Enforce multi-factor compliance requirements
- Use profiles in security policies
- Manage profile descriptions and organization

## Commands

### Creating/Updating HIP Profiles

Basic HIP profile with single object:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects hip-profile --folder Texas --name basic-compliance \
  --match '{"windows-patches": {"is": true}}' \
  --description "Basic Windows patch compliance"
<span style="color: green;">✓</span> HIP profile 'basic-compliance' created successfully
```

</div>

Multi-object compliance profile:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects hip-profile --folder Texas --name secure-endpoints \
  --match '{"windows-patches": {"is": true}, "disk-encryption": {"is": true}, "antivirus": {"is": true}}' \
  --description "Comprehensive endpoint security"
<span style="color: green;">✓</span> HIP profile 'secure-endpoints' created successfully
```

</div>

Platform-specific profile:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects hip-profile --folder Texas --name windows-corporate \
  --match '{"corp-domain": {"is": true}, "windows-security": {"is": true}}' \
  --description "Corporate Windows requirements"
<span style="color: green;">✓</span> HIP profile 'windows-corporate' created successfully
```

</div>

### Listing HIP Profiles

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects hip-profile --folder Texas --list
HIP profiles in folder 'Texas':
- basic-compliance
- secure-endpoints
- windows-corporate
- mobile-compliance
```

</div>

### Showing HIP Profile Details

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects hip-profile --folder Texas --name secure-endpoints
HIP Profile: secure-endpoints
  Match: {"windows-patches": {"is": true}, "disk-encryption": {"is": true}, "antivirus": {"is": true}}
  Description: Comprehensive endpoint security
  Folder: Texas
```

</div>

### Deleting HIP Profiles

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli delete objects hip-profile --folder Texas --name secure-endpoints
<span style="color: green;">✓</span> HIP profile 'secure-endpoints' deleted successfully
```

</div>

### Bulk Operations

Load multiple HIP profiles from a YAML file:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli load objects hip-profile --folder Texas --file hip-profiles.yml
<span style="color: green;">✓</span> Loaded 8 HIP profiles successfully
```

</div>

Backup existing HIP profiles:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli backup objects hip-profile --folder Texas
<span style="color: green;">✓</span> Backed up 8 HIP profiles to hip-profile-texas.yaml
```

</div>

## YAML Configuration Format

HIP profiles can be defined in YAML for bulk operations:

```yaml
hip_profiles:
  - name: basic-windows
    description: "Basic Windows compliance"
    match: '{"windows-patches": {"is": true}}'
    
  - name: secure-windows
    description: "Secure Windows endpoints"
    match: '{"windows-patches": {"is": true}, "disk-encryption": {"is": true}, "antivirus": {"is": true}}'
    
  - name: corporate-windows
    description: "Corporate Windows requirements"
    match: '{"corp-domain": {"is": true}, "windows-security": {"is": true}, "disk-encryption": {"is": true}}'
    
  - name: secure-mac
    description: "Secure macOS endpoints"
    match: '{"macos-patches": {"is": true}, "filevault": {"is": true}}'
    
  - name: mobile-secure
    description: "Secure mobile devices"
    match: '{"mobile-compliance": {"is": true}}'
    
  - name: domain-only
    description: "Domain membership required"
    match: '{"corp-domain": {"is": true}}'
    
  - name: certificate-auth
    description: "Certificate-based authentication"
    match: '{"client-certificate": {"is": true}}'
    
  - name: ultra-secure
    description: "Maximum security requirements"
    match: '{"windows-patches": {"is": true}, "disk-encryption": {"is": true}, "antivirus": {"is": true}, "corp-domain": {"is": true}, "client-certificate": {"is": true}}'
```

## Configuration Options

### Required Parameters

- `--name`: Name of the HIP profile (max 31 characters)
- `--match`: Match criteria in JSON format (max 2048 characters)

### Optional Parameters

- `--description`: Detailed description (max 255 characters)

### Context Parameters

Exactly one context parameter must be specified:

- `--folder`: Folder name (e.g., "Texas", "Shared")
- `--snippet`: Snippet name for Panorama
- `--device`: Device name for NGFW

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

## Examples

### Basic Compliance Profiles

```bash
# Patch compliance only
scm-cli set objects hip-profile --folder Shared --name patch-compliance \
  --match '{"os-patches": {"is": true}}'

# Encryption only
scm-cli set objects hip-profile --folder Shared --name encryption-required \
  --match '{"disk-encryption": {"is": true}}'
```

### Platform-Specific Profiles

```bash
# Windows corporate
scm-cli set objects hip-profile --folder Shared --name windows-corp \
  --match '{"windows-domain": {"is": true}, "windows-security": {"is": true}}' \
  --description "Corporate Windows endpoints"

# macOS corporate
scm-cli set objects hip-profile --folder Shared --name macos-corp \
  --match '{"macos-managed": {"is": true}, "filevault": {"is": true}}' \
  --description "Corporate macOS endpoints"
```

### Security Level Profiles

```bash
# Basic security
scm-cli set objects hip-profile --folder Shared --name basic-security \
  --match '{"antivirus": {"is": true}}' \
  --description "Basic security requirements"

# Standard security
scm-cli set objects hip-profile --folder Shared --name standard-security \
  --match '{"antivirus": {"is": true}, "os-patches": {"is": true}}' \
  --description "Standard security requirements"

# High security
scm-cli set objects hip-profile --folder Shared --name high-security \
  --match '{"antivirus": {"is": true}, "os-patches": {"is": true}, "disk-encryption": {"is": true}, "corp-domain": {"is": true}}' \
  --description "High security requirements"
```

### Special Purpose Profiles

```bash
# Mobile devices
scm-cli set objects hip-profile --folder Shared --name mobile-policy \
  --match '{"mobile-secure": {"is": true}, "mobile-managed": {"is": true}}'

# Guest access
scm-cli set objects hip-profile --folder Shared --name guest-requirements \
  --match '{"antivirus": {"is": true}, "no-malware": {"is": true}}'
```

## Integration with Security Policies

HIP profiles are used in security rules for endpoint-based access control:

```bash
# Allow only compliant endpoints
scm-cli set security rule --folder Shared --name "Compliant-Access" \
  --source-hip "@secure-endpoints" --destination-zones "Corporate" \
  --applications "any" --action allow

# Restrict non-compliant devices
scm-cli set security rule --folder Shared --name "Block-Non-Compliant" \
  --source-hip "!@basic-compliance" --destination-zones "Corporate" \
  --action deny
```

## Best Practices

1. **Layered Profiles**: Create profiles for different security levels
   - Basic: Minimum requirements
   - Standard: Typical corporate requirements
   - High: Sensitive resource access

2. **Platform Separation**: Create separate profiles for different platforms
   - Windows profiles
   - macOS profiles
   - Mobile profiles

3. **Clear Naming**: Use descriptive names indicating security level or purpose

4. **Documentation**: Always include descriptions explaining profile requirements

5. **Testing**: Test profiles with sample endpoints before deployment

## Profile Design Patterns

### Incremental Security

```bash
# Level 1: Basic
'{"antivirus": {"is": true}}'

# Level 2: Standard
'{"antivirus": {"is": true}, "patches": {"is": true}}'

# Level 3: High
'{"antivirus": {"is": true}, "patches": {"is": true}, "encryption": {"is": true}}'

# Level 4: Maximum
'{"antivirus": {"is": true}, "patches": {"is": true}, "encryption": {"is": true}, "domain": {"is": true}}'
```

### Role-Based Profiles

```bash
# Standard users
'{"basic-compliance": {"is": true}}'

# Privileged users
'{"full-compliance": {"is": true}, "mfa-device": {"is": true}}'

# Administrators
'{"full-compliance": {"is": true}, "mfa-device": {"is": true}, "managed-device": {"is": true}}'
```

## Troubleshooting

### Common Issues

1. **JSON Syntax**: Ensure proper JSON formatting in match criteria
2. **HIP Object Names**: Verify exact HIP object names (case-sensitive)
3. **Object Existence**: HIP objects must exist before referencing in profiles
4. **Match Logic**: Remember all conditions use AND logic

### Testing Match Criteria

```bash
# Test with simple match first
--match '{"single-object": {"is": true}}'

# Then add complexity
--match '{"object1": {"is": true}, "object2": {"is": true}}'
```

## Notes

- Profile names must be unique within a folder
- Maximum name length is 31 characters
- Match criteria use JSON format
- All HIP objects in match criteria must exist
- Profiles use AND logic (all conditions must match)
- Use "is": false for negative matching
- Profiles are referenced in policies using the "@" prefix
- GlobalProtect enforces HIP profiles on endpoints