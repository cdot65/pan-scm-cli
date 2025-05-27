# External Dynamic List Management

This section covers the commands for managing external dynamic list (EDL) objects in Strata Cloud Manager.

## Overview

External Dynamic Lists enable dynamic import of IP addresses, domains, URLs, and mobile identifiers from external sources. The `external-dynamic-list` commands allow you to:

- Configure predefined threat intelligence feeds
- Create custom EDLs with scheduled updates
- Import IP addresses, domains, URLs, IMSI, and IMEI lists
- Configure authentication for secure sources
- Set update frequencies and exception lists

## Commands

### Creating/Updating External Dynamic Lists

Predefined IP blocklist:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects external-dynamic-list --folder Texas \
  --name paloalto-bulletproof --type predefined_ip \
  --url "panw-bulletproof-ip-list" \
  --description "Palo Alto Networks Bulletproof IP list"
<span style="color: green;">✓</span> External dynamic list 'paloalto-bulletproof' created successfully
```

</div>

Custom IP list with hourly updates:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects external-dynamic-list --folder Texas \
  --name custom-threats --type ip \
  --url "https://threats.example.com/ips.txt" \
  --recurring hourly \
  --description "Custom threat IP list"
<span style="color: green;">✓</span> External dynamic list 'custom-threats' created successfully
```

</div>

Domain list with authentication:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects external-dynamic-list --folder Texas \
  --name malware-domains --type domain \
  --url "https://secure.example.com/domains.txt" \
  --username "api_user" --password "secure_token" \
  --recurring daily --hour 02 \
  --expand-domain \
  --description "Malware domain blocklist"
<span style="color: green;">✓</span> External dynamic list 'malware-domains' created successfully
```

</div>

### Listing External Dynamic Lists

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects external-dynamic-list --folder Texas --list
External dynamic lists in folder 'Texas':
- paloalto-bulletproof (predefined_ip)
- custom-threats (ip)
- malware-domains (domain)
- suspicious-urls (url)
```

</div>

### Showing External Dynamic List Details

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects external-dynamic-list --folder Texas --name custom-threats
External Dynamic List: custom-threats
  Type: ip
  URL: https://threats.example.com/ips.txt
  Recurring: hourly
  Description: Custom threat IP list
  Folder: Texas
```

</div>

### Deleting External Dynamic Lists

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli delete objects external-dynamic-list --folder Texas --name custom-threats
<span style="color: green;">✓</span> External dynamic list 'custom-threats' deleted successfully
```

</div>

### Bulk Operations

Load multiple EDLs from a YAML file:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli load objects external-dynamic-list --folder Texas --file edls.yml
<span style="color: green;">✓</span> Loaded 8 external dynamic lists successfully
```

</div>

Backup existing EDLs:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli backup objects external-dynamic-list --folder Texas
<span style="color: green;">✓</span> Backed up 8 external dynamic lists to external-dynamic-list-texas.yaml
```

</div>

## YAML Configuration Format

External dynamic lists can be defined in YAML for bulk operations:

```yaml
external_dynamic_lists:
  # Predefined lists
  - name: paloalto-bulletproof
    type: predefined_ip
    url: "panw-bulletproof-ip-list"
    description: "Palo Alto Networks Bulletproof IP list"
    
  - name: paloalto-highrisk
    type: predefined_ip
    url: "panw-highrisk-ip-list"
    description: "High risk IP addresses"
    
  # Custom IP list with exceptions
  - name: office-ips
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
    type: domain
    url: "https://threat-intel.example.com/domains"
    description: "Known malware domains"
    username: "api_user"
    password: "secure_token"
    recurring: hourly
    expand_domain: true
    
  # URL list with certificate authentication
  - name: phishing-urls
    type: url
    url: "https://secure-feed.example.com/urls.txt"
    description: "Phishing URL list"
    certificate_profile: "EDL-Client-Cert"
    recurring: five_minute
    
  # Weekly update on specific day
  - name: blocked-sites
    type: url
    url: "https://blocklist.example.com/weekly.txt"
    description: "Weekly blocklist update"
    recurring: weekly
    day: "sunday"
    hour: "03"
    
  # Monthly update
  - name: suspicious-ips
    type: ip
    url: "https://monthly-feed.example.com/ips.csv"
    description: "Monthly suspicious IP update"
    recurring: monthly
    day: "1"
    hour: "00"
    
  # Mobile identifiers
  - name: stolen-devices
    type: imei
    url: "https://security.example.com/stolen-imei.txt"
    description: "Stolen device IMEI numbers"
    recurring: daily
    hour: "12"
```

## Configuration Options

### Required Parameters

- `--name`: Name of the external dynamic list
- `--type`: EDL type (predefined_ip, predefined_url, ip, domain, url, imsi, imei)
- `--url`: Source URL for the list

### Optional Parameters

- `--description`: Detailed description
- `--exception-list`: Items to exclude from the list (comma-separated)

### Authentication Parameters

- `--username`: Username for basic authentication
- `--password`: Password for basic authentication
- `--certificate-profile`: Certificate profile for mutual TLS

### Recurring Update Parameters

Required for custom EDL types (ip, domain, url, imsi, imei):

- `--recurring`: Update frequency (five_minute, hourly, daily, weekly, monthly)
- `--hour`: Hour for updates (00-23) - required for daily, weekly, monthly
- `--day`: Day for updates
  - For weekly: sunday, monday, tuesday, wednesday, thursday, friday, saturday
  - For monthly: 1-31

### Domain-Specific Parameters

- `--expand-domain`: Expand to include subdomains (domain type only)

### Context Parameters

Exactly one context parameter must be specified:

- `--folder`: Folder name (e.g., "Texas", "Shared")
- `--snippet`: Snippet name for Panorama
- `--device`: Device name for NGFW

## EDL Types

### Predefined Lists

Palo Alto Networks managed threat feeds:

| Type | Common URLs |
|------|-------------|
| predefined_ip | panw-bulletproof-ip-list |
| predefined_ip | panw-highrisk-ip-list |
| predefined_ip | panw-known-ip-list |
| predefined_ip | panw-torexit-ip-list |
| predefined_url | panw-malware-url-list |
| predefined_url | panw-phishing-url-list |

### Custom Lists

User-defined lists with flexible update schedules:

| Type | Content | Format |
|------|---------|--------|
| ip | IP addresses | One per line, CIDR notation supported |
| domain | Domain names | One per line, wildcards supported |
| url | URLs | Full URLs, one per line |
| imsi | Mobile subscriber IDs | Numeric identifiers |
| imei | Mobile equipment IDs | Device identifiers |

## Examples

### Create Predefined Threat Lists

```bash
# Bulletproof hosting IPs
scm-cli set objects external-dynamic-list --folder Shared \
  --name bulletproof-ips --type predefined_ip \
  --url "panw-bulletproof-ip-list"

# Known malware URLs
scm-cli set objects external-dynamic-list --folder Shared \
  --name malware-urls --type predefined_url \
  --url "panw-malware-url-list"
```

### Create Custom IP Lists

```bash
# Hourly updated threat list
scm-cli set objects external-dynamic-list --folder Shared \
  --name threat-ips --type ip \
  --url "https://threats.company.com/ips.txt" \
  --recurring hourly

# Daily office IPs with exceptions
scm-cli set objects external-dynamic-list --folder Shared \
  --name office-whitelist --type ip \
  --url "https://internal.company.com/offices.txt" \
  --recurring daily --hour 06 \
  --exception-list "10.0.0.0/8,172.16.0.0/12"
```

### Create Domain Lists

```bash
# Malware domains with expansion
scm-cli set objects external-dynamic-list --folder Shared \
  --name malware-domains --type domain \
  --url "https://intel.company.com/domains.txt" \
  --recurring daily --hour 02 \
  --expand-domain
```

### Create Authenticated Lists

```bash
# Basic authentication
scm-cli set objects external-dynamic-list --folder Shared \
  --name partner-list --type ip \
  --url "https://partner.example.com/api/blocklist" \
  --username "api_user" --password "secure_key" \
  --recurring hourly

# Certificate authentication
scm-cli set objects external-dynamic-list --folder Shared \
  --name secure-intel --type url \
  --url "https://intel-feed.example.com/urls" \
  --certificate-profile "Intel-Feed-Cert" \
  --recurring five_minute
```

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
# Block traffic to/from threat IPs
scm-cli set security rule --folder Shared --name "Block-Threat-IPs" \
  --source-addresses "@threat-ips" --destination-zones "Internet" \
  --action deny

# Block access to malware domains
scm-cli set security rule --folder Shared --name "Block-Malware-Domains" \
  --destination-addresses "@malware-domains" \
  --action deny
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

## Notes

- EDL names must be unique within a folder
- Predefined EDLs use short names, not full URLs
- Custom EDLs require recurring configuration
- Maximum entries vary by platform and license
- Lists are referenced in policies using the "@" prefix
- Empty lists are allowed but may affect policy enforcement
- URL sources should return plain text with one entry per line
- Comments in source files typically start with # or //