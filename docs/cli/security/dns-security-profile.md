# DNS Security Profile

DNS security profiles protect against DNS-based threats including malware domains, command-and-control traffic, and DNS tunneling. The `scm` CLI provides commands to create, update, delete, and load DNS security profiles.

## Overview

The `dns-security-profile` commands allow you to:

- Create DNS security profiles with botnet domain protections
- Update existing profile configurations including sinkhole settings
- Delete profiles that are no longer needed
- Bulk import profiles from YAML files
- Export profiles for backup or migration

## Set DNS Security Profile

Create or update a DNS security profile.

### Syntax

```bash
scm set security dns-security-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Profile name | Yes |
| `--description TEXT` | Profile description | No |
| `--botnet-domains TEXT` | Botnet domains settings as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create Profile with Sinkhole

```bash
$ scm set security dns-security-profile \
    --folder Texas \
    --name dns-sec-default \
    --botnet-domains '{"dns_security_categories": [{"name": "pan-dns-sec-malware", "action": "sinkhole"}]}'
---> 100%
Created DNS security profile: dns-sec-default in folder Texas
```

#### Create Profile with Whitelist

```bash
$ scm set security dns-security-profile \
    --folder Texas \
    --name dns-sec-custom \
    --botnet-domains '{"whitelist": [{"name": "example.com"}]}'
---> 100%
Created DNS security profile: dns-sec-custom in folder Texas
```

## Delete DNS Security Profile

Delete a DNS security profile from SCM.

### Syntax

```bash
scm delete security dns-security-profile [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Profile name to delete | Yes |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete security dns-security-profile \
    --folder Texas \
    --name dns-sec-default
---> 100%
Deleted DNS security profile: dns-sec-default from folder Texas
```

## Load DNS Security Profile

Load multiple DNS security profiles from a YAML file.

### Syntax

```bash
scm load security dns-security-profile [OPTIONS]
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
dns_security_profiles:
  - name: dns-sec-default
    folder: Texas
    description: "Default DNS security profile"
    botnet_domains:
      dns_security_categories:
        - name: pan-dns-sec-malware
          action: sinkhole

  - name: dns-sec-custom
    folder: Texas
    description: "Custom DNS security with whitelist"
    botnet_domains:
      whitelist:
        - name: example.com
```

### Examples

#### Load with Original Locations

```bash
$ scm load security dns-security-profile \
    --file dns-security.yaml
---> 100%
✓ Loaded DNS security profile: dns-sec-default
✓ Loaded DNS security profile: dns-sec-custom

Successfully loaded 2 out of 2 DNS security profiles from 'dns-security.yaml'
```

#### Load with Folder Override

```bash
$ scm load security dns-security-profile \
    --file dns-security.yaml \
    --folder Austin
---> 100%
✓ Loaded DNS security profile: dns-sec-default
✓ Loaded DNS security profile: dns-sec-custom

Successfully loaded 2 out of 2 DNS security profiles from 'dns-security.yaml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all profiles
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show DNS Security Profile

Display DNS security profile objects.

### Syntax

```bash
scm show security dns-security-profile [OPTIONS]
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
$ scm show security dns-security-profile \
    --folder Texas \
    --name dns-sec-default
---> 100%
DNS Security Profile: dns-sec-default
  Location: Folder 'Texas'
  Description: Default DNS security profile
  Botnet Domains: configured
```

#### List All Profiles (Default Behavior)

```bash
$ scm show security dns-security-profile --folder Texas
---> 100%
DNS Security Profiles in folder 'Texas':
------------------------------------------------------------
Name: dns-sec-default
  Description: Default DNS security profile
------------------------------------------------------------
Name: dns-sec-custom
  Description: Custom DNS security with whitelist
------------------------------------------------------------
```

## Backup DNS Security Profiles

Backup all DNS security profile objects from a specified location to a YAML file.

### Syntax

```bash
scm backup security dns-security-profile [OPTIONS]
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
$ scm backup security dns-security-profile --folder Texas
---> 100%
Successfully backed up 4 DNS security profiles to dns_security_profile_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup security dns-security-profile \
    --folder Texas \
    --file texas-dns-security.yaml
---> 100%
Successfully backed up 4 DNS security profiles to texas-dns-security.yaml
```

## Best Practices

1. **Sinkhole Malware Domains**: Configure `dns_security_categories` with sinkhole actions to redirect malware DNS queries to a safe IP.
2. **Whitelist Trusted Domains**: Add legitimate domains to the whitelist to prevent false positives for business-critical services.
3. **Use Descriptive Names**: Name profiles to reflect their protection scope (e.g., `dns-sec-strict`, `dns-sec-custom`).
4. **Backup Before Changes**: Always backup existing profiles before making bulk modifications via load commands.
5. **Layer with Other Profiles**: Combine DNS security profiles with anti-spyware and URL filtering for comprehensive threat protection.
