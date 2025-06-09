# Object Commands Examples

This document provides comprehensive examples for all load and backup commands in the `scm` CLI tool for object management.

## Table of Contents

1. [Address Commands](#address-commands)
2. [Address Group Commands](#address-group-commands)
3. [Application Commands](#application-commands)
4. [Application Group Commands](#application-group-commands)
5. [Application Filter Commands](#application-filter-commands)
6. [Dynamic User Group Commands](#dynamic-user-group-commands)
7. [External Dynamic List Commands](#external-dynamic-list-commands)
8. [HIP Object Commands](#hip-object-commands)
9. [HIP Profile Commands](#hip-profile-commands)
10. [HTTP Server Profile Commands](#http-server-profile-commands)
11. [Log Forwarding Profile Commands](#log-forwarding-profile-commands)
12. [Service Commands](#service-commands)
13. [Service Group Commands](#service-group-commands)
14. [Syslog Server Profile Commands](#syslog-server-profile-commands)
15. [Tag Commands](#tag-commands)

---

## Address Commands

### Backup Address Objects

```bash
# Backup all addresses from a folder (auto-generated filename)
scm backup object address --folder Texas
# Creates: address-texas.yaml

# Backup from a folder with custom output file
scm backup object address --folder "Production/US-East" --file backups/prod-addresses.yaml

# Backup from a snippet
scm backup object address --snippet "Shared Config" --file shared-addresses.yaml

# Backup from a device
scm backup object address --device "fw-datacenter-01" --file device-addresses.yaml
```

### Load Address Objects

```bash
# Load addresses from a file
scm load object address --file examples/addresses.yml

# Load with dry-run to preview changes
scm load object address --file examples/addresses.yml --dry-run

# Load with container override (all addresses go to specified folder)
scm load object address --file examples/addresses.yml --folder "Texas/Dallas"

# Load with snippet override
scm load object address --file examples/addresses.yml --snippet "Branch Template"

# Load with device override
scm load object address --file examples/addresses.yml --device "fw-branch-01"
```

---

## Address Group Commands

### Backup Address Group Objects

```bash
# Backup all address groups from a folder
scm backup object address-group --folder Texas
# Creates: address-group-texas.yaml

# Backup with custom output file
scm backup object address-group --folder Production --file backups/prod-addr-groups.yaml

# Backup from a snippet
scm backup object address-group --snippet "Security Best Practices"

# Backup from a device
scm backup object address-group --device "fw-hq-01" --file device-groups.yaml
```

### Load Address Group Objects

```bash
# Load address groups from a file
scm load object address-group --file examples/address-groups.yml

# Preview changes without applying
scm load object address-group --file examples/address-groups.yml --dry-run

# Load with folder override
scm load object address-group --file examples/address-groups.yml --folder Production

# Load with snippet override
scm load object address-group --file examples/address-groups.yml --snippet "DMZ Config"

# Load with device override
scm load object address-group --file examples/address-groups.yml --device "fw-dmz-01"
```

---

## Application Commands

### Backup Application Objects

```bash
# Backup all applications from a folder
scm backup object application --folder "Custom Apps"
# Creates: application-custom-apps.yaml

# Backup with custom filename
scm backup object application --folder Production --file backups/prod-apps.yaml

# Backup from a snippet
scm backup object application --snippet "App Definitions" --file snippet-apps.yaml

# Backup from a device
scm backup object application --device "fw-edge-01"
```

### Load Application Objects

```bash
# Load applications from a file
scm load object application --file examples/applications.yml

# Preview without applying
scm load object application --file examples/applications.yml --dry-run

# Load with folder override
scm load object application --file examples/applications.yml --folder "Custom Apps"

# Load with snippet override
scm load object application --file examples/applications.yml --snippet "Standard Apps"

# Load with device override
scm load object application --file examples/applications.yml --device "fw-branch-02"
```

---

## Application Group Commands

### Backup Application Group Objects

```bash
# Backup all application groups from a folder
scm backup object application-group --folder Production
# Creates: application-group-production.yaml

# Backup with custom file
scm backup object application-group --folder Texas --file texas-app-groups.yaml

# Backup from a snippet
scm backup object application-group --snippet "App Categories"

# Backup from a device
scm backup object application-group --device "fw-main-01" --file device-app-groups.yaml
```

### Load Application Group Objects

```bash
# Load application groups from a file
scm load object application-group --file examples/application-groups.yml

# Preview changes
scm load object application-group --file examples/application-groups.yml --dry-run

# Load with folder override
scm load object application-group --file examples/application-groups.yml --folder Production

# Load with snippet override
scm load object application-group --file examples/application-groups.yml --snippet "App Policies"

# Load with device override
scm load object application-group --file examples/application-groups.yml --device "fw-edge-02"
```

---

## Application Filter Commands

### Backup Application Filter Objects

```bash
# Backup all application filters from a folder
scm backup object application-filter --folder Security
# Creates: application-filter-security.yaml

# Backup with custom filename
scm backup object application-filter --folder Production --file prod-app-filters.yaml

# Backup from a snippet
scm backup object application-filter --snippet "Risk Filters"

# Backup from a device
scm backup object application-filter --device "fw-inspection-01"
```

### Load Application Filter Objects

```bash
# Load application filters from a file
scm load object application-filter --file examples/application-filters.yml

# Preview without applying
scm load object application-filter --file examples/application-filters.yml --dry-run

# Load with folder override
scm load object application-filter --file examples/application-filters.yml --folder Security

# Load with snippet override
scm load object application-filter --file examples/application-filters.yml --snippet "High Risk Apps"

# Load with device override
scm load object application-filter --file examples/application-filters.yml --device "fw-dmz-02"
```

---

## Dynamic User Group Commands

### Backup Dynamic User Group Objects

```bash
# Backup all dynamic user groups from a folder
scm backup object dynamic-user-group --folder "User Groups"
# Creates: dynamic-user-group-user-groups.yaml

# Backup with custom file
scm backup object dynamic-user-group --folder Production --file prod-user-groups.yaml

# Backup from a snippet
scm backup object dynamic-user-group --snippet "AD Integration"

# Backup from a device
scm backup object dynamic-user-group --device "fw-corp-01"
```

### Load Dynamic User Group Objects

```bash
# Load dynamic user groups from a file
scm load object dynamic-user-group --file examples/dynamic-user-groups.yml

# Preview changes
scm load object dynamic-user-group --file examples/dynamic-user-groups.yml --dry-run

# Load with folder override
scm load object dynamic-user-group --file examples/dynamic-user-groups.yml --folder "User Groups"

# Load with snippet override
scm load object dynamic-user-group --file examples/dynamic-user-groups.yml --snippet "LDAP Groups"

# Load with device override
scm load object dynamic-user-group --file examples/dynamic-user-groups.yml --device "fw-campus-01"
```

---

## External Dynamic List Commands

### Backup External Dynamic List Objects

```bash
# Backup all external dynamic lists from a folder
scm backup object external-dynamic-list --folder Security
# Creates: external-dynamic-list-security.yaml

# Backup with custom file
scm backup object external-dynamic-list --folder Production --file prod-edl.yaml

# Backup from a snippet
scm backup object external-dynamic-list --snippet "Threat Intel"

# Backup from a device
scm backup object external-dynamic-list --device "fw-perimeter-01"
```

### Load External Dynamic List Objects

```bash
# Load external dynamic lists from a file
scm load object external-dynamic-list --file examples/external-dynamic-lists.yml

# Preview without applying
scm load object external-dynamic-list --file examples/external-dynamic-lists.yml --dry-run

# Load with folder override
scm load object external-dynamic-list --file examples/external-dynamic-lists.yml --folder Security

# Load with snippet override
scm load object external-dynamic-list --file examples/external-dynamic-lists.yml --snippet "Block Lists"

# Load with device override
scm load object external-dynamic-list --file examples/external-dynamic-lists.yml --device "fw-edge-03"
```

---

## HIP Object Commands

### Backup HIP Object Objects

```bash
# Backup all HIP objects from a folder
scm backup object hip-object --folder Compliance
# Creates: hip-object-compliance.yaml

# Backup with custom file
scm backup object hip-object --folder Production --file prod-hip-objects.yaml

# Backup from a snippet
scm backup object hip-object --snippet "Endpoint Security"

# Backup from a device
scm backup object hip-object --device "fw-vpn-01"
```

### Load HIP Object Objects

```bash
# Load HIP objects from a file
scm load object hip-object --file examples/hip-objects.yml

# Preview changes
scm load object hip-object --file examples/hip-objects.yml --dry-run

# Load with folder override
scm load object hip-object --file examples/hip-objects.yml --folder Compliance

# Load with snippet override
scm load object hip-object --file examples/hip-objects.yml --snippet "HIP Policies"

# Load with device override
scm load object hip-object --file examples/hip-objects.yml --device "fw-remote-01"
```

---

## HIP Profile Commands

### Backup HIP Profile Objects

```bash
# Backup all HIP profiles from a folder
scm backup object hip-profile --folder Compliance
# Creates: hip-profile-compliance.yaml

# Backup with custom file
scm backup object hip-profile --folder Production --file prod-hip-profiles.yaml

# Backup from a snippet
scm backup object hip-profile --snippet "VPN Profiles"

# Backup from a device
scm backup object hip-profile --device "fw-gateway-01"
```

### Load HIP Profile Objects

```bash
# Load HIP profiles from a file
scm load object hip-profile --file examples/hip-profiles.yml

# Preview changes
scm load object hip-profile --file examples/hip-profiles.yml --dry-run

# Load with folder override
scm load object hip-profile --file examples/hip-profiles.yml --folder Compliance

# Load with snippet override
scm load object hip-profile --file examples/hip-profiles.yml --snippet "Remote Access"

# Load with device override
scm load object hip-profile --file examples/hip-profiles.yml --device "fw-vpn-02"
```

---

## HTTP Server Profile Commands

### Backup HTTP Server Profile Objects

```bash
# Backup all HTTP server profiles from a folder
scm backup object http-server-profile --folder Logging
# Creates: http-server-profile-logging.yaml

# Backup with custom file
scm backup object http-server-profile --folder Production --file prod-http-profiles.yaml

# Backup from a snippet
scm backup object http-server-profile --snippet "Log Collectors"

# Backup from a device
scm backup object http-server-profile --device "fw-log-01"
```

### Load HTTP Server Profile Objects

```bash
# Load HTTP server profiles from a file
scm load object http-server-profile --file examples/http-server-profiles.yml

# Preview changes
scm load object http-server-profile --file examples/http-server-profiles.yml --dry-run

# Load with folder override
scm load object http-server-profile --file examples/http-server-profiles.yml --folder Logging

# Load with snippet override
scm load object http-server-profile --file examples/http-server-profiles.yml --snippet "SIEM Integration"

# Load with device override
scm load object http-server-profile --file examples/http-server-profiles.yml --device "fw-collector-01"
```

---

## Log Forwarding Profile Commands

### Backup Log Forwarding Profile Objects

```bash
# Backup all log forwarding profiles from a folder
scm backup object log-forwarding-profile --folder Logging
# Creates: log-forwarding-profile-logging.yaml

# Backup with custom file
scm backup object log-forwarding-profile --folder Production --file prod-log-profiles.yaml

# Backup from a snippet
scm backup object log-forwarding-profile --snippet "SIEM Forward"

# Backup from a device
scm backup object log-forwarding-profile --device "fw-core-01"
```

### Load Log Forwarding Profile Objects

```bash
# Load log forwarding profiles from a file
scm load object log-forwarding-profile --file examples/log-forwarding-profiles.yml

# Preview changes
scm load object log-forwarding-profile --file examples/log-forwarding-profiles.yml --dry-run

# Load with folder override
scm load object log-forwarding-profile --file examples/log-forwarding-profiles.yml --folder Logging

# Load with snippet override
scm load object log-forwarding-profile --file examples/log-forwarding-profiles.yml --snippet "Compliance Logs"

# Load with device override
scm load object log-forwarding-profile --file examples/log-forwarding-profiles.yml --device "fw-audit-01"
```

---

## Service Commands

### Backup Service Objects

```bash
# Backup all services from a folder
scm backup object service --folder Applications
# Creates: service-applications.yaml

# Backup with custom file
scm backup object service --folder Production --file prod-services.yaml

# Backup from a snippet
scm backup object service --snippet "Custom Services"

# Backup from a device
scm backup object service --device "fw-app-01"
```

### Load Service Objects

```bash
# Load services from a file
scm load object service --file examples/services.yml

# Preview changes
scm load object service --file examples/services.yml --dry-run

# Load with folder override
scm load object service --file examples/services.yml --folder Applications

# Load with snippet override
scm load object service --file examples/services.yml --snippet "App Services"

# Load with device override
scm load object service --file examples/services.yml --device "fw-web-01"
```

---

## Service Group Commands

### Backup Service Group Objects

```bash
# Backup all service groups from a folder
scm backup object service-group --folder Applications
# Creates: service-group-applications.yaml

# Backup with custom file
scm backup object service-group --folder Production --file prod-service-groups.yaml

# Backup from a snippet
scm backup object service-group --snippet "Service Categories"

# Backup from a device
scm backup object service-group --device "fw-services-01"
```

### Load Service Group Objects

```bash
# Load service groups from a file
scm load object service-group --file examples/service-groups.yml

# Preview changes
scm load object service-group --file examples/service-groups.yml --dry-run

# Load with folder override
scm load object service-group --file examples/service-groups.yml --folder Applications

# Load with snippet override
scm load object service-group --file examples/service-groups.yml --snippet "Web Services"

# Load with device override
scm load object service-group --file examples/service-groups.yml --device "fw-lb-01"
```

---

## Syslog Server Profile Commands

### Backup Syslog Server Profile Objects

```bash
# Backup all syslog server profiles from a folder
scm backup object syslog-server-profile --folder Logging
# Creates: syslog-server-profile-logging.yaml

# Backup with custom file
scm backup object syslog-server-profile --folder Production --file prod-syslog.yaml

# Backup from a snippet
scm backup object syslog-server-profile --snippet "Log Servers"

# Backup from a device
scm backup object syslog-server-profile --device "fw-syslog-01"
```

### Load Syslog Server Profile Objects

```bash
# Load syslog server profiles from a file
scm load object syslog-server-profile --file examples/syslog-server-profiles.yml

# Preview changes
scm load object syslog-server-profile --file examples/syslog-server-profiles.yml --dry-run

# Load with folder override
scm load object syslog-server-profile --file examples/syslog-server-profiles.yml --folder Logging

# Load with snippet override
scm load object syslog-server-profile --file examples/syslog-server-profiles.yml --snippet "Central Logging"

# Load with device override
scm load object syslog-server-profile --file examples/syslog-server-profiles.yml --device "fw-central-01"
```

---

## Tag Commands

### Backup Tag Objects

```bash
# Backup all tags from a folder
scm backup object tag --folder Organization
# Creates: tag-organization.yaml

# Backup with custom file
scm backup object tag --folder Production --file prod-tags.yaml

# Backup from a snippet
scm backup object tag --snippet "Metadata Tags"

# Backup from a device
scm backup object tag --device "fw-master-01"
```

### Load Tag Objects

```bash
# Load tags from a file
scm load object tag --file examples/tags.yml

# Preview changes
scm load object tag --file examples/tags.yml --dry-run

# Load with folder override
scm load object tag --file examples/tags.yml --folder Organization

# Load with snippet override
scm load object tag --file examples/tags.yml --snippet "Classification"

# Load with device override
scm load object tag --file examples/tags.yml --device "fw-tag-01"
```

---

## Common Patterns and Tips

### Backup Patterns

1. **Auto-generated filenames**: When no `--file` is specified, filenames follow the pattern: `{object-type}-{location}.yaml`

   ```bash
   scm backup object address --folder Texas
   # Creates: address-texas.yaml
   ```

2. **Hierarchical folders**: Folder names with slashes are converted to hyphens

   ```bash
   scm backup object address --folder "Production/US-East"
   # Creates: address-production-us-east.yaml
   ```

3. **Custom output paths**: Use `--file` for specific locations

   ```bash
   scm backup object address --folder Production --file /backups/$(date +%Y%m%d)-prod-addresses.yaml
   ```

### Load Patterns

1. **Dry run first**: Always preview changes before applying

   ```bash
   scm load object address --file config.yml --dry-run
   ```

2. **Container overrides**: Override all object locations in one command

   ```bash
   # Move all objects to a different folder
   scm load object address --file config.yml --folder "New Location"
   ```

3. **Bulk operations**: Load multiple object types in sequence

   ```bash
   # Load in dependency order
   scm load object tag --file tags.yml
   scm load object address --file addresses.yml
   scm load object address-group --file address-groups.yml
   ```

### Best Practices

1. **Backup before changes**: Always backup existing configurations

   ```bash
   scm backup object address --folder Production --file backup-$(date +%Y%m%d).yaml
   ```

2. **Use version control**: Store YAML files in git

   ```bash
   git add configs/*.yaml
   git commit -m "Updated address configurations"
   ```

3. **Organize by environment**: Structure your files by environment

   ```bash
   configs/
   ├── production/
   │   ├── addresses.yaml
   │   └── address-groups.yaml
   ├── staging/
   │   ├── addresses.yaml
   │   └── address-groups.yaml
   └── development/
       ├── addresses.yaml
       └── address-groups.yaml
   ```
