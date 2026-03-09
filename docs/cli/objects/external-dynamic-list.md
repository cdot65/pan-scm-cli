# External Dynamic List Objects

External Dynamic List (EDL) objects enable dynamic import of IP addresses, domains, URLs, and mobile identifiers from external sources in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load external dynamic list objects.

## Overview

The `external-dynamic-list` commands allow you to:

- Configure predefined threat intelligence feeds
- Create custom EDLs with scheduled updates
- Import IP addresses, domains, URLs, IMSI, and IMEI lists
- Configure authentication for secure sources
- Export EDLs for backup or migration

## EDL Types

### Predefined Lists

Palo Alto Networks managed threat feeds:

| Type | Common URLs |
| --- | --- |
| predefined_ip | panw-bulletproof-ip-list |
| predefined_ip | panw-highrisk-ip-list |
| predefined_ip | panw-known-ip-list |
| predefined_ip | panw-torexit-ip-list |
| predefined_url | panw-malware-url-list |
| predefined_url | panw-phishing-url-list |

### Custom Lists

User-defined lists with flexible update schedules:

| Type | Content | Format |
| --- | --- | --- |
| ip | IP addresses | One per line, CIDR notation supported |
| domain | Domain names | One per line, wildcards supported |
| url | URLs | Full URLs, one per line |
| imsi | Mobile subscriber IDs | Numeric identifiers |
| imei | Mobile equipment IDs | Device identifiers |

## Set External Dynamic List

Create or update an external dynamic list object.

### Syntax

```bash
scm set object external-dynamic-list [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder for the external dynamic list object | No\* |
| `--snippet TEXT` | Snippet for the external dynamic list object | No\* |
| `--device TEXT` | Device for the external dynamic list object | No\* |
| `--name TEXT` | Name of the external dynamic list | Yes |
| `--type TEXT` | EDL type (predefined_ip, predefined_url, ip, domain, url, imsi, imei) | Yes |
| `--url TEXT` | Source URL for the list | Yes |
| `--description TEXT` | Description of the EDL | No |
| `--exception-list LIST` | Items to exclude from the list | No |
| `--username TEXT` | Username for basic authentication | No |
| `--password TEXT` | Password for basic authentication | No |
| `--certificate-profile TEXT` | Certificate profile for mutual TLS | No |
| `--recurring TEXT` | Update frequency (five_minute, hourly, daily, weekly, monthly) | No\*\* |
| `--hour TEXT` | Hour for updates (00-23) | No\*\*\* |
| `--day TEXT` | Day for updates | No\*\*\* |
| `--expand-domain` | Expand to include subdomains (domain type only) | No |

\* One of --folder, --snippet, or --device is required.

\*\* Required for custom EDL types (ip, domain, url, imsi, imei).

\*\*\* Required based on recurring frequency.

### Examples

#### Create Predefined IP Blocklist

```bash
$ scm set object external-dynamic-list \
    --folder Texas \
    --name paloalto-bulletproof \
    --type predefined_ip \
    --url "panw-bulletproof-ip-list" \
    --description "Palo Alto Networks Bulletproof IP list"
---> 100%
Created external dynamic list: paloalto-bulletproof in folder Texas
```

#### Create Custom IP List with Hourly Updates

```bash
$ scm set object external-dynamic-list \
    --folder Texas \
    --name custom-threats \
    --type ip \
    --url "https://threats.example.com/ips.txt" \
    --recurring hourly \
    --description "Custom threat IP list"
---> 100%
Created external dynamic list: custom-threats in folder Texas
```

#### Create Domain List with Authentication

```bash
$ scm set object external-dynamic-list \
    --folder Texas \
    --name malware-domains \
    --type domain \
    --url "https://secure.example.com/domains.txt" \
    --username "api_user" \
    --password "secure_token" \
    --recurring daily \
    --hour 02 \
    --expand-domain \
    --description "Malware domain blocklist"
---> 100%
Created external dynamic list: malware-domains in folder Texas
```

## Delete External Dynamic List

Delete an external dynamic list object from SCM.

### Syntax

```bash
scm delete object external-dynamic-list [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the external dynamic list object | No\* |
| `--snippet TEXT` | Snippet containing the external dynamic list object | No\* |
| `--device TEXT` | Device containing the external dynamic list object | No\* |
| `--name TEXT` | Name of the external dynamic list object to delete | Yes |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete object external-dynamic-list --folder Texas --name custom-threats --force
---> 100%
Deleted external dynamic list: custom-threats from folder Texas
```

## Load External Dynamic Lists

Load multiple external dynamic list objects from a YAML file.

### Syntax

```bash
scm load object external-dynamic-list [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing external dynamic list definitions | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
external_dynamic_lists:
  - name: paloalto-bulletproof
    folder: Texas
    type: predefined_ip
    url: "panw-bulletproof-ip-list"
    description: "Palo Alto Networks Bulletproof IP list"

  - name: office-ips
    folder: Texas
    type: ip
    url: "https://internal.company.com/office-ips.txt"
    description: "Office IP addresses"
    recurring: daily
    hour: "06"
    exception_list:
      - "10.0.0.0/8"
      - "172.16.0.0/12"

  - name: malware-domains
    folder: Texas
    type: domain
    url: "https://threat-intel.example.com/domains"
    description: "Known malware domains"
    username: "api_user"
    password: "secure_token"
    recurring: hourly
    expand_domain: true
```

### Examples

#### Load with Original Locations

```bash
$ scm load object external-dynamic-list --file edls.yml
---> 100%
✓ Loaded external dynamic list: paloalto-bulletproof
✓ Loaded external dynamic list: office-ips
✓ Loaded external dynamic list: malware-domains

Successfully loaded 3 out of 3 external dynamic lists from 'edls.yml'
```

#### Load with Folder Override

```bash
$ scm load object external-dynamic-list --file edls.yml --folder Austin
---> 100%
✓ Loaded external dynamic list: paloalto-bulletproof
✓ Loaded external dynamic list: office-ips
✓ Loaded external dynamic list: malware-domains

Successfully loaded 3 out of 3 external dynamic lists from 'edls.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all external
    dynamic lists will be loaded into the specified container, ignoring the container
    specified in the YAML file.

## Show External Dynamic List

Display external dynamic list objects.

### Syntax

```bash
scm show object external-dynamic-list [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the external dynamic list object | No\* |
| `--snippet TEXT` | Snippet containing the external dynamic list object | No\* |
| `--device TEXT` | Device containing the external dynamic list object | No\* |
| `--name TEXT` | Name of the external dynamic list object to show | No |

!!! note
    When no `--name` is specified, all items are listed by default.

\* One of --folder, --snippet, or --device is required.

### Examples

#### Show Specific External Dynamic List

```bash
$ scm show object external-dynamic-list --folder Texas --name custom-threats
---> 100%
External Dynamic List: custom-threats
  Location: Folder 'Texas'
  Type: ip
  URL: https://threats.example.com/ips.txt
  Recurring: hourly
  Description: Custom threat IP list
  ID: 123e4567-e89b-12d3-a456-426614174000
```

#### List All External Dynamic Lists (Default Behavior)

```bash
$ scm show object external-dynamic-list --folder Texas
---> 100%
External Dynamic Lists in folder 'Texas':
------------------------------------------------------------
Name: paloalto-bulletproof
  Location: Folder 'Texas'
  Type: predefined_ip
  URL: panw-bulletproof-ip-list
  Description: Palo Alto Networks Bulletproof IP list
------------------------------------------------------------
Name: custom-threats
  Location: Folder 'Texas'
  Type: ip
  URL: https://threats.example.com/ips.txt
  Recurring: hourly
  Description: Custom threat IP list
------------------------------------------------------------
Name: malware-domains
  Location: Folder 'Texas'
  Type: domain
  URL: https://secure.example.com/domains.txt
  Recurring: daily at 02:00
  Authentication: Basic (api_user)
  Expand Domain: Yes
  Description: Malware domain blocklist
------------------------------------------------------------
```

## Backup External Dynamic Lists

Backup all external dynamic list objects from a specified location to a YAML file.

### Syntax

```bash
scm backup object external-dynamic-list [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup external dynamic lists from | No\* |
| `--snippet TEXT` | Snippet to backup external dynamic lists from | No\* |
| `--device TEXT` | Device to backup external dynamic lists from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup object external-dynamic-list --folder Texas
---> 100%
Successfully backed up 8 external dynamic lists to external-dynamic-list_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object external-dynamic-list --folder Texas --file texas-edls.yaml
---> 100%
Successfully backed up 8 external dynamic lists to texas-edls.yaml
```

## Best Practices

1. **Update Frequency**: Balance freshness and resource usage -- critical lists every 5 minutes, standard lists daily.
2. **List Validation**: Ensure source URLs are reliable and properly formatted.
3. **Exception Lists**: Use exception lists for false positives or internal resources.
4. **Authentication**: Use HTTPS and authentication for sensitive lists.
5. **Monitoring**: Monitor EDL update status and failures regularly.
6. **Use YAML for Bulk Operations**: For complex deployments, use YAML files.
7. **Organize by Container**: Keep EDLs organized in appropriate folders, snippets, or devices.
