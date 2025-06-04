# External Dynamic List Objects

External Dynamic List (EDL) objects enable dynamic import of IP addresses, domains, URLs, and mobile identifiers from external sources in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load external dynamic list objects.

## Overview

External Dynamic Lists allow you to:

- Configure predefined threat intelligence feeds
- Create custom EDLs with scheduled updates
- Import IP addresses, domains, URLs, IMSI, and IMEI lists
- Configure authentication for secure sources
- Set update frequencies and exception lists

## Set External Dynamic List

Create or update an external dynamic list object.

### Syntax

```bash
scm set objects external-dynamic-list [OPTIONS]
```

### Options

| Option                       | Description                                                           | Required |
| ---------------------------- | --------------------------------------------------------------------- | -------- |
| `--folder TEXT`              | Folder for the external dynamic list object                           | Yes\*    |
| `--snippet TEXT`             | Snippet for the external dynamic list object                          | Yes\*    |
| `--device TEXT`              | Device for the external dynamic list object                           | Yes\*    |
| `--name TEXT`                | Name of the external dynamic list                                     | Yes      |
| `--type TEXT`                | EDL type (predefined_ip, predefined_url, ip, domain, url, imsi, imei) | Yes      |
| `--url TEXT`                 | Source URL for the list                                               | Yes      |
| `--description TEXT`         | Description of the EDL                                                | No       |
| `--exception-list LIST`      | Items to exclude from the list                                        | No       |
| `--username TEXT`            | Username for basic authentication                                     | No       |
| `--password TEXT`            | Password for basic authentication                                     | No       |
| `--certificate-profile TEXT` | Certificate profile for mutual TLS                                    | No       |
| `--recurring TEXT`           | Update frequency (five_minute, hourly, daily, weekly, monthly)        | No\*\*   |
| `--hour TEXT`                | Hour for updates (00-23)                                              | No\*\*\* |
| `--day TEXT`                 | Day for updates                                                       | No\*\*\* |
| `--expand-domain`            | Expand to include subdomains (domain type only)                       | No       |

\* You must specify exactly one of --folder, --snippet, or --device.
\*\* Required for custom EDL types (ip, domain, url, imsi, imei).
\*\*\* Required based on recurring frequency.

### Examples

#### Create Predefined IP Blocklist

```bash
$ scm set objects external-dynamic-list \
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
$ scm set objects external-dynamic-list \
    --folder Texas \
    --name custom-threats \
    --type ip \
    --url "https://threats.example.com/ips.txt" \
    --recurring hourly \
    --description "Custom threat IP list"
---> 100%
Created external dynamic list: custom-threats in folder Texas
```

## Delete External Dynamic List

Delete an external dynamic list object from SCM.

### Syntax

```bash
scm delete objects external-dynamic-list [OPTIONS]
```

### Options

| Option           | Description                                         | Required |
| ---------------- | --------------------------------------------------- | -------- |
| `--folder TEXT`  | Folder containing the external dynamic list object  | Yes\*    |
| `--snippet TEXT` | Snippet containing the external dynamic list object | Yes\*    |
| `--device TEXT`  | Device containing the external dynamic list object  | Yes\*    |
| `--name TEXT`    | Name of the external dynamic list object to delete  | Yes      |

\* You must specify exactly one of --folder, --snippet, or --device.

### Example

```bash
$ scm delete objects external-dynamic-list --folder Texas --name custom-threats
---> 100%
Deleted external dynamic list: custom-threats from folder Texas
```

## Load External Dynamic Lists

Load multiple external dynamic list objects from a YAML file.

### Syntax

```bash
scm load objects external-dynamic-list [OPTIONS]
```

### Options

| Option           | Description                                                    | Required |
| ---------------- | -------------------------------------------------------------- | -------- |
| `--file TEXT`    | Path to YAML file containing external dynamic list definitions | Yes      |
| `--folder TEXT`  | Override folder location for all objects                       | No       |
| `--snippet TEXT` | Override snippet location for all objects                      | No       |
| `--device TEXT`  | Override device location for all objects                       | No       |
| `--dry-run`      | Preview changes without applying them                          | No       |

### YAML File Format

```yaml
---
external_dynamic_lists:
  # Predefined lists
  - name: paloalto-bulletproof
    folder: Texas # Container location (folder, snippet, or device)
    type: predefined_ip
    url: "panw-bulletproof-ip-list"
    description: "Palo Alto Networks Bulletproof IP list"

  - name: paloalto-highrisk
    folder: Texas
    type: predefined_ip
    url: "panw-highrisk-ip-list"
    description: "High risk IP addresses"

  # Custom IP list with exceptions
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

  # Domain list with authentication
  - name: malware-domains
    folder: Texas
    type: domain
    url: "https://threat-intel.example.com/domains"
    description: "Known malware domains"
    username: "api_user"
    password: "secure_token"
    recurring: hourly
    expand_domain: true

  # URL list with certificate authentication
  - name: phishing-urls
    folder: Texas
    type: url
    url: "https://secure-feed.example.com/urls.txt"
    description: "Phishing URL list"
    certificate_profile: "EDL-Client-Cert"
    recurring: five_minute
```

### Examples

#### Load with Original Locations

```bash
$ scm load objects external-dynamic-list --file edls.yml
---> 100%
✓ Loaded external dynamic list: paloalto-bulletproof
✓ Loaded external dynamic list: paloalto-highrisk
✓ Loaded external dynamic list: office-ips
✓ Loaded external dynamic list: malware-domains
✓ Loaded external dynamic list: phishing-urls

Successfully loaded 5 out of 5 external dynamic lists from 'edls.yml'
```

#### Load with Folder Override

```bash
$ scm load objects external-dynamic-list --file edls.yml --folder Austin
---> 100%
✓ Loaded external dynamic list: paloalto-bulletproof
✓ Loaded external dynamic list: paloalto-highrisk
✓ Loaded external dynamic list: office-ips
✓ Loaded external dynamic list: malware-domains
✓ Loaded external dynamic list: phishing-urls

Successfully loaded 5 out of 5 external dynamic lists from 'edls.yml'
```

!!! note
When using container override options (--folder, --snippet, --device), all external dynamic lists will be loaded into the specified container, ignoring the container specified in the YAML file.

## Show External Dynamic List

Display external dynamic list objects.

### Syntax

```bash
scm show objects external-dynamic-list [OPTIONS]
```

### Options

| Option           | Description                                         | Required |
| ---------------- | --------------------------------------------------- | -------- |
| `--folder TEXT`  | Folder containing the external dynamic list object  | Yes\*    |
| `--snippet TEXT` | Snippet containing the external dynamic list object | Yes\*    |
| `--device TEXT`  | Device containing the external dynamic list object  | Yes\*    |
| `--name TEXT`    | Name of the external dynamic list object to show    | No\*\*   |
| `--list`         | List all external dynamic lists in the container    | No\*\*   |

\* You must specify exactly one of --folder, --snippet, or --device.
\*\* If --name is not specified, all items will be listed.

### Examples

#### Show Specific External Dynamic List

```bash
$ scm show objects external-dynamic-list --folder Texas --name custom-threats
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
$ scm show objects external-dynamic-list --folder Texas
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
scm backup objects external-dynamic-list [OPTIONS]
```

### Options

| Option           | Description                                   | Required |
| ---------------- | --------------------------------------------- | -------- |
| `--folder TEXT`  | Folder to backup external dynamic lists from  | No\*     |
| `--snippet TEXT` | Snippet to backup external dynamic lists from | No\*     |
| `--device TEXT`  | Device to backup external dynamic lists from  | No\*     |
| `--file TEXT`    | Output filename (defaults to auto-generated)  | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

### Examples

#### Backup from Folder

```bash
$ scm backup objects external-dynamic-list --folder Texas
---> 100%
Successfully backed up 8 external dynamic lists to external-dynamic-list_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup objects external-dynamic-list --folder Texas --file texas-edls.yaml
---> 100%
Successfully backed up 8 external dynamic lists to texas-edls.yaml
```

## Best Practices

1. **Update Frequency**: Balance between freshness and resource usage

   - Critical lists: 5 minutes to hourly
   - Standard lists: Daily
   - Reference lists: Weekly or monthly

2. **List Validation**: Ensure source URLs are reliable and properly formatted

3. **Exception Lists**: Use for false positives or internal resources

4. **Authentication**: Use HTTPS and authentication for sensitive lists

5. **Monitoring**: Monitor EDL update status and failures

6. **Use YAML for Bulk Operations**: For complex deployments, use YAML files

7. **Organize by Container**: Keep EDLs organized in appropriate folders, snippets, or devices

## EDL Types

### Predefined Lists

Palo Alto Networks managed threat feeds:

| Type           | Common URLs              |
| -------------- | ------------------------ |
| predefined_ip  | panw-bulletproof-ip-list |
| predefined_ip  | panw-highrisk-ip-list    |
| predefined_ip  | panw-known-ip-list       |
| predefined_ip  | panw-torexit-ip-list     |
| predefined_url | panw-malware-url-list    |
| predefined_url | panw-phishing-url-list   |

### Custom Lists

User-defined lists with flexible update schedules:

| Type   | Content               | Format                                |
| ------ | --------------------- | ------------------------------------- |
| ip     | IP addresses          | One per line, CIDR notation supported |
| domain | Domain names          | One per line, wildcards supported     |
| url    | URLs                  | Full URLs, one per line               |
| imsi   | Mobile subscriber IDs | Numeric identifiers                   |
| imei   | Mobile equipment IDs  | Device identifiers                    |

## Additional Examples

### Create Predefined Threat Lists

```bash
$ scm set objects external-dynamic-list \
    --folder Shared \
    --name bulletproof-ips \
    --type predefined_ip \
    --url "panw-bulletproof-ip-list" \
    --description "Bulletproof hosting IPs"
---> 100%
Created external dynamic list: bulletproof-ips in folder Shared
```

### Create Custom IP Lists

```bash
$ scm set objects external-dynamic-list \
    --folder Shared \
    --name office-whitelist \
    --type ip \
    --url "https://internal.company.com/offices.txt" \
    --recurring daily \
    --hour 06 \
    --exception-list "10.0.0.0/8,172.16.0.0/12" \
    --description "Daily office IPs with exceptions"
---> 100%
Created external dynamic list: office-whitelist in folder Shared
```

### Create Domain Lists with Authentication

```bash
$ scm set objects external-dynamic-list \
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

## EDL Types

### Predefined Lists

Palo Alto Networks managed threat feeds:

| Type           | Common URLs              |
| -------------- | ------------------------ |
| predefined_ip  | panw-bulletproof-ip-list |
| predefined_ip  | panw-highrisk-ip-list    |
| predefined_ip  | panw-known-ip-list       |
| predefined_ip  | panw-torexit-ip-list     |
| predefined_url | panw-malware-url-list    |
| predefined_url | panw-phishing-url-list   |

### Custom Lists

User-defined lists with flexible update schedules:

| Type   | Content               | Format                                |
| ------ | --------------------- | ------------------------------------- |
| ip     | IP addresses          | One per line, CIDR notation supported |
| domain | Domain names          | One per line, wildcards supported     |
| url    | URLs                  | Full URLs, one per line               |
| imsi   | Mobile subscriber IDs | Numeric identifiers                   |
| imei   | Mobile equipment IDs  | Device identifiers                    |

## Update Schedules

### Five Minute Updates

```bash
--recurring five_minute
```

Best for critical, rapidly changing lists.

### Hourly Updates

```bash
--recurring hourly
```

Good balance for most threat feeds.

### Daily Updates

```bash
--recurring daily --hour 02
```

Sufficient for stable lists, specify hour (00-23).

### Weekly Updates

```bash
--recurring weekly --day sunday --hour 03
```

For lists that change weekly, specify day and hour.

### Monthly Updates

```bash
--recurring monthly --day 1 --hour 00
```

For stable reference lists, specify day (1-31) and hour.

## Integration with Security Policies

EDLs are used in security rules for dynamic blocking:

```bash
$ scm set security rule \
    --folder Shared \
    --name "Block-Threat-IPs" \
    --source-addresses "@threat-ips" \
    --destination-zones "Internet" \
    --action deny
---> 100%
Created security rule: Block-Threat-IPs in folder Shared
```

## Notes

- EDL names must be unique within a container
- Predefined EDLs use short names, not full URLs
- Custom EDLs require recurring configuration
- Maximum entries vary by platform and license
- Lists are referenced in policies using the "@" prefix
- Empty lists are allowed but may affect policy enforcement
- URL sources should return plain text with one entry per line
- Comments in source files typically start with # or //
