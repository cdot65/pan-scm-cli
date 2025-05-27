# Application Filter Management

This section covers the commands for managing application filter objects in Strata Cloud Manager.

## Overview

Application filters provide dynamic application selection based on specific criteria. The `application-filter` commands allow you to:

- Create filters based on application characteristics
- Filter by categories, subcategories, and technologies
- Filter by risk levels and security attributes
- Identify applications with specific behaviors
- Use filters in security policies for dynamic control

## Commands

### Creating/Updating Application Filters

Basic filter by category and risk:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects application-filter --folder Texas --name high-risk-apps \
  --category "file-sharing,peer-to-peer" --risk 4 --risk 5 \
  --description "High-risk file sharing applications"
<span style="color: green;">✓</span> Application filter 'high-risk-apps' created successfully
```

</div>

Filter with security characteristics:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects application-filter --folder Texas --name malware-apps \
  --category "file-sharing" --used-by-malware \
  --has-known-vulnerabilities --transfers-files \
  --description "Applications with security concerns"
<span style="color: green;">✓</span> Application filter 'malware-apps' created successfully
```

</div>

Comprehensive filter:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects application-filter --folder Texas --name problematic-apps \
  --category "file-sharing,gaming,social-networking" \
  --subcategory "peer-to-peer,online-gaming" \
  --technology "peer-to-peer,browser-based" \
  --risk 3 --risk 4 --risk 5 \
  --excessive-bandwidth-use --evasive \
  --description "Applications to monitor or block"
<span style="color: green;">✓</span> Application filter 'problematic-apps' created successfully
```

</div>

### Listing Application Filters

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects application-filter --folder Texas --list
Application filters in folder 'Texas':
- high-risk-apps
- malware-apps
- problematic-apps
- bandwidth-heavy
```

</div>

### Showing Application Filter Details

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects application-filter --folder Texas --name high-risk-apps
Application Filter: high-risk-apps
  Categories: file-sharing, peer-to-peer
  Risk Levels: 4, 5
  Description: High-risk file sharing applications
  Folder: Texas
```

</div>

### Deleting Application Filters

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli delete objects application-filter --folder Texas --name high-risk-apps
<span style="color: green;">✓</span> Application filter 'high-risk-apps' deleted successfully
```

</div>

### Bulk Operations

Load multiple application filters from a YAML file:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli load objects application-filter --folder Texas --file app-filters.yml
<span style="color: green;">✓</span> Loaded 5 application filters successfully
```

</div>

Backup existing application filters:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli backup objects application-filter --folder Texas
<span style="color: green;">✓</span> Backed up 5 application filters to application-filter-texas.yaml
```

</div>

## YAML Configuration Format

Application filters can be defined in YAML for bulk operations:

```yaml
application_filters:
  - name: high-risk-apps
    description: "High-risk applications requiring attention"
    category:
      - file-sharing
      - peer-to-peer
    risk:
      - 4
      - 5
    
  - name: vulnerable-apps
    description: "Applications with known security issues"
    category:
      - collaboration
      - file-sharing
    has_known_vulnerabilities: true
    transfers_files: true
    
  - name: bandwidth-heavy
    description: "Applications consuming excessive bandwidth"
    category:
      - media
      - file-sharing
      - peer-to-peer
    subcategory:
      - streaming-media
      - file-transfer
    excessive_bandwidth_use: true
    
  - name: evasive-apps
    description: "Applications using evasive techniques"
    technology:
      - peer-to-peer
      - encrypted-tunnel
    evasive: true
    tunnels_other_apps: true
    
  - name: business-critical
    description: "Critical business applications"
    category:
      - business-systems
      - collaboration
    subcategory:
      - enterprise-applications
      - web-conferencing
    risk:
      - 1
      - 2
```

## Configuration Options

### Required Parameters

- `--name`: Name of the application filter
- `--category`: List of application categories (at least one required)
- `--subcategory`: List of application subcategories (at least one required)
- `--technology`: List of technologies (at least one required)
- `--risk`: List of risk levels 1-5 (at least one required)

Note: At least one of the above filtering criteria must be specified.

### Optional Parameters

- `--description`: Detailed description
- `--evasive`: Filter for evasive applications
- `--pervasive`: Filter for pervasive applications
- `--excessive-bandwidth-use`: Filter for bandwidth-heavy applications
- `--used-by-malware`: Filter for applications used by malware
- `--transfers-files`: Filter for file transfer applications
- `--has-known-vulnerabilities`: Filter for vulnerable applications
- `--tunnels-other-apps`: Filter for tunneling applications
- `--prone-to-misuse`: Filter for applications prone to misuse
- `--no-certifications`: Filter for uncertified applications

### Context Parameters

Exactly one context parameter must be specified:

- `--folder`: Folder name (e.g., "Texas", "Shared")
- `--snippet`: Snippet name for Panorama
- `--device`: Device name for NGFW

## Examples

### Create a Security-Focused Filter

```bash
scm-cli set objects application-filter --folder Shared --name security-risk \
  --category "file-sharing,peer-to-peer,proxy" \
  --risk 4 --risk 5 \
  --has-known-vulnerabilities --used-by-malware \
  --description "Applications with significant security risks"
```

### Create a Bandwidth Management Filter

```bash
scm-cli set objects application-filter --folder Shared --name bandwidth-control \
  --category "media,file-sharing" \
  --subcategory "streaming-media,peer-to-peer" \
  --excessive-bandwidth-use \
  --description "Applications requiring bandwidth management"
```

### Create a Compliance Filter

```bash
scm-cli set objects application-filter --folder Shared --name non-compliant \
  --category "file-sharing,social-networking,gaming" \
  --risk 3 --risk 4 --risk 5 \
  --transfers-files --evasive \
  --description "Applications violating company policy"
```

### Create a Business Application Filter

```bash
scm-cli set objects application-filter --folder Shared --name approved-business \
  --category "business-systems,collaboration" \
  --subcategory "enterprise-applications,project-management" \
  --risk 1 --risk 2 \
  --description "Approved business applications"
```

## Integration with Security Policies

Application filters are commonly used in security rules for dynamic control:

```bash
# Block high-risk applications
scm-cli set security rule --folder Shared --name "Block-High-Risk" \
  --source-zones "Trust" --destination-zones "Internet" \
  --applications "@high-risk-apps" --action deny

# Monitor vulnerable applications
scm-cli set security rule --folder Shared --name "Monitor-Vulnerable" \
  --source-zones "any" --destination-zones "any" \
  --applications "@vulnerable-apps" --action allow \
  --log-start --log-end
```

## Best Practices

1. **Clear Naming**: Use descriptive names that indicate the filter's purpose

2. **Combine Criteria**: Use multiple criteria for more precise filtering

3. **Risk-Based Approach**: Group applications by risk level for policy enforcement

4. **Regular Updates**: Review filters periodically as new applications are identified

5. **Documentation**: Always include descriptions explaining the filter's purpose

## Filter Logic

### AND Logic Within Categories

When specifying multiple values for a single criterion, OR logic is used:
- `--risk 4 --risk 5` matches applications with risk level 4 OR 5
- `--category "file-sharing,gaming"` matches file-sharing OR gaming

### AND Logic Between Categories

Different criteria types use AND logic:
- Applications must match ALL specified criteria types
- Example: `--category "file-sharing" --risk 5` matches only file-sharing apps with risk level 5

## Common Use Cases

### Security Filtering
```bash
# High-risk applications
--risk 4 --risk 5 --has-known-vulnerabilities

# Malware vectors
--used-by-malware --transfers-files --evasive
```

### Performance Filtering
```bash
# Bandwidth management
--excessive-bandwidth-use --category "media,file-sharing"

# Resource-intensive apps
--pervasive --excessive-bandwidth-use
```

### Compliance Filtering
```bash
# Non-business applications
--category "gaming,social-networking" --risk 3 --risk 4 --risk 5

# Uncertified applications
--no-certifications --prone-to-misuse
```

## Notes

- Filter names must be unique within a folder
- At least one filtering criterion must be specified
- Filters are referenced in policies using the "@" prefix
- Risk levels range from 1 (lowest) to 5 (highest)
- Boolean criteria (e.g., evasive, transfers-files) are inherently true when specified
- Filters provide dynamic matching - as new applications are identified, they automatically match if criteria are met