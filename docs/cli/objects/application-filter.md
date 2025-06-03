# Application Filter Objects

Application filter objects provide dynamic application selection based on specific criteria in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load application filter objects.

## Overview

Application filters allow you to:

- Create filters based on application characteristics
- Filter by categories, subcategories, and technologies
- Filter by risk levels and security attributes
- Identify applications with specific behaviors
- Use filters in security policies for dynamic control

## Set Application Filter

Create or update an application filter object.

### Syntax

```bash
scm set objects application-filter [OPTIONS]
```

### Options

| Option                        | Description                               | Required |
| ----------------------------- | ----------------------------------------- | -------- |
| `--folder TEXT`               | Folder for the application filter object  | Yes\*    |
| `--snippet TEXT`              | Snippet for the application filter object | Yes\*    |
| `--device TEXT`               | Device for the application filter object  | Yes\*    |
| `--name TEXT`                 | Name of the application filter            | Yes      |
| `--category LIST`             | List of application categories            | No\*\*   |
| `--subcategory LIST`          | List of application subcategories         | No\*\*   |
| `--technology LIST`           | List of technologies                      | No\*\*   |
| `--risk LIST`                 | List of risk levels (1-5)                 | No\*\*   |
| `--description TEXT`          | Description of the filter                 | No       |
| `--evasive`                   | Filter for evasive applications           | No       |
| `--pervasive`                 | Filter for pervasive applications         | No       |
| `--excessive-bandwidth-use`   | Filter for bandwidth-heavy applications   | No       |
| `--used-by-malware`           | Filter for applications used by malware   | No       |
| `--transfers-files`           | Filter for file transfer applications     | No       |
| `--has-known-vulnerabilities` | Filter for vulnerable applications        | No       |
| `--tunnels-other-apps`        | Filter for tunneling applications         | No       |
| `--prone-to-misuse`           | Filter for applications prone to misuse   | No       |
| `--no-certifications`         | Filter for uncertified applications       | No       |

\* You must specify exactly one of --folder, --snippet, or --device.
\*\* At least one filtering criterion must be specified.

### Examples

#### Create Basic Filter by Category and Risk

```bash
$ scm set objects application-filter \
    --folder Texas \
    --name high-risk-apps \
    --category "file-sharing,peer-to-peer" \
    --risk 4 --risk 5 \
    --description "High-risk file sharing applications"
---> 100%
Created application filter: high-risk-apps in folder Texas
```

#### Create Filter with Security Characteristics

```bash
$ scm set objects application-filter \
    --folder Texas \
    --name malware-apps \
    --category "file-sharing" \
    --used-by-malware \
    --has-known-vulnerabilities \
    --transfers-files \
    --description "Applications with security concerns"
---> 100%
Created application filter: malware-apps in folder Texas
```

## Delete Application Filter

Delete an application filter object from SCM.

### Syntax

```bash
scm delete objects application-filter [OPTIONS]
```

### Options

| Option           | Description                                      | Required |
| ---------------- | ------------------------------------------------ | -------- |
| `--folder TEXT`  | Folder containing the application filter object  | Yes\*    |
| `--snippet TEXT` | Snippet containing the application filter object | Yes\*    |
| `--device TEXT`  | Device containing the application filter object  | Yes\*    |
| `--name TEXT`    | Name of the application filter object to delete  | Yes      |

\* You must specify exactly one of --folder, --snippet, or --device.

### Example

```bash
$ scm delete objects application-filter --folder Texas --name high-risk-apps
---> 100%
Deleted application filter: high-risk-apps from folder Texas
```

## Load Application Filters

Load multiple application filter objects from a YAML file.

### Syntax

```bash
scm load objects application-filter [OPTIONS]
```

### Options

| Option           | Description                                                 | Required |
| ---------------- | ----------------------------------------------------------- | -------- |
| `--file TEXT`    | Path to YAML file containing application filter definitions | Yes      |
| `--folder TEXT`  | Override folder location for all objects                    | No       |
| `--snippet TEXT` | Override snippet location for all objects                   | No       |
| `--device TEXT`  | Override device location for all objects                    | No       |
| `--dry-run`      | Preview changes without applying them                       | No       |

### YAML File Format

```yaml
---
application_filters:
  - name: high-risk-apps
    folder: Texas # Container location (folder, snippet, or device)
    description: "High-risk applications requiring attention"
    category:
      - file-sharing
      - peer-to-peer
    risk:
      - 4
      - 5

  - name: vulnerable-apps
    folder: Texas
    description: "Applications with known security issues"
    category:
      - collaboration
      - file-sharing
    has_known_vulnerabilities: true
    transfers_files: true

  - name: bandwidth-heavy
    folder: Texas
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
    folder: Texas
    description: "Applications using evasive techniques"
    technology:
      - peer-to-peer
      - encrypted-tunnel
    evasive: true
    tunnels_other_apps: true

  - name: business-critical
    folder: Texas
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

### Examples

#### Load with Original Locations

```bash
$ scm load objects application-filter --file app-filters.yml
---> 100%
✓ Loaded application filter: high-risk-apps
✓ Loaded application filter: vulnerable-apps
✓ Loaded application filter: bandwidth-heavy
✓ Loaded application filter: evasive-apps
✓ Loaded application filter: business-critical

Successfully loaded 5 out of 5 application filters from 'app-filters.yml'
```

#### Load with Folder Override

```bash
$ scm load objects application-filter --file app-filters.yml --folder Austin
---> 100%
✓ Loaded application filter: high-risk-apps
✓ Loaded application filter: vulnerable-apps
✓ Loaded application filter: bandwidth-heavy
✓ Loaded application filter: evasive-apps
✓ Loaded application filter: business-critical

Successfully loaded 5 out of 5 application filters from 'app-filters.yml'
```

!!! note
When using container override options (--folder, --snippet, --device), all application filters will be loaded into the specified container, ignoring the container specified in the YAML file.

## Show Application Filter

Display application filter objects.

### Syntax

```bash
scm show objects application-filter [OPTIONS]
```

### Options

| Option           | Description                                      | Required |
| ---------------- | ------------------------------------------------ | -------- |
| `--folder TEXT`  | Folder containing the application filter object  | Yes\*    |
| `--snippet TEXT` | Snippet containing the application filter object | Yes\*    |
| `--device TEXT`  | Device containing the application filter object  | Yes\*    |
| `--name TEXT`    | Name of the application filter object to show    | No\*\*   |
| `--list`         | List all application filters in the container    | No\*\*   |

\* You must specify exactly one of --folder, --snippet, or --device.
\*\* If --name is not specified, all items will be listed.

### Examples

#### Show Specific Application Filter

```bash
$ scm show objects application-filter --folder Texas --name high-risk-apps
---> 100%
Application Filter: high-risk-apps
Location: Folder 'Texas'
Categories: file-sharing, peer-to-peer
Risk Levels: 4, 5
Description: High-risk file sharing applications
ID: 123e4567-e89b-12d3-a456-426614174000
```

#### List All Application Filters (Default Behavior)

```bash
$ scm show objects application-filter --folder Texas
---> 100%
Application Filters in folder 'Texas':
------------------------------------------------------------
Name: high-risk-apps
  Location: Folder 'Texas'
  Categories: file-sharing, peer-to-peer
  Risk Levels: 4, 5
  Description: High-risk file sharing applications
------------------------------------------------------------
Name: malware-apps
  Location: Folder 'Texas'
  Categories: file-sharing
  Security Attributes: used-by-malware, has-known-vulnerabilities, transfers-files
  Description: Applications with security concerns
------------------------------------------------------------
Name: bandwidth-heavy
  Location: Folder 'Texas'
  Categories: media, file-sharing, peer-to-peer
  Subcategories: streaming-media, file-transfer
  Security Attributes: excessive-bandwidth-use
  Description: Applications consuming excessive bandwidth
------------------------------------------------------------
```

## Backup Application Filters

Backup all application filter objects from a specified location to a YAML file.

### Syntax

```bash
scm backup objects application-filter [OPTIONS]
```

### Options

| Option           | Description                                  | Required |
| ---------------- | -------------------------------------------- | -------- |
| `--folder TEXT`  | Folder to backup application filters from    | No\*     |
| `--snippet TEXT` | Snippet to backup application filters from   | No\*     |
| `--device TEXT`  | Device to backup application filters from    | No\*     |
| `--file TEXT`    | Output filename (defaults to auto-generated) | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

### Examples

#### Backup from Folder

```bash
$ scm backup objects application-filter --folder Texas
---> 100%
Successfully backed up 5 application filters to application-filter_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup objects application-filter --folder Texas --file texas-app-filters.yaml
---> 100%
Successfully backed up 5 application filters to texas-app-filters.yaml
```

## Best Practices

1. **Clear Naming**: Use descriptive names that indicate the filter's purpose
2. **Combine Criteria**: Use multiple criteria for more precise filtering
3. **Risk-Based Approach**: Group applications by risk level for policy enforcement
4. **Regular Updates**: Review filters periodically as new applications are identified
5. **Documentation**: Always include descriptions explaining the filter's purpose
6. **Use YAML for Bulk Operations**: For complex deployments, use YAML files
7. **Organize by Container**: Keep filters organized in appropriate folders, snippets, or devices

## Additional Examples

### Create a Security-Focused Filter

```bash
$ scm set objects application-filter \
    --folder Shared \
    --name security-risk \
    --category "file-sharing,peer-to-peer,proxy" \
    --risk 4 --risk 5 \
    --has-known-vulnerabilities \
    --used-by-malware \
    --description "Applications with significant security risks"
---> 100%
Created application filter: security-risk in folder Shared
```

### Create a Bandwidth Management Filter

```bash
$ scm set objects application-filter \
    --folder Shared \
    --name bandwidth-control \
    --category "media,file-sharing" \
    --subcategory "streaming-media,peer-to-peer" \
    --excessive-bandwidth-use \
    --description "Applications requiring bandwidth management"
---> 100%
Created application filter: bandwidth-control in folder Shared
```

### Create a Comprehensive Filter

```bash
$ scm set objects application-filter \
    --folder Texas \
    --name problematic-apps \
    --category "file-sharing,gaming,social-networking" \
    --subcategory "peer-to-peer,online-gaming" \
    --technology "peer-to-peer,browser-based" \
    --risk 3 --risk 4 --risk 5 \
    --excessive-bandwidth-use \
    --evasive \
    --description "Applications to monitor or block"
---> 100%
Created application filter: problematic-apps in folder Texas
```

## Integration with Security Policies

Application filters are commonly used in security rules for dynamic control:

```bash
$ scm set security rule \
    --folder Shared \
    --name "Block-High-Risk" \
    --source-zones "Trust" \
    --destination-zones "Internet" \
    --applications "@high-risk-apps" \
    --action deny
---> 100%
Created security rule: Block-High-Risk in folder Shared
```

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

- Filter names must be unique within a container
- At least one filtering criterion must be specified
- Filters are referenced in policies using the "@" prefix
- Risk levels range from 1 (lowest) to 5 (highest)
- Boolean criteria (e.g., evasive, transfers-files) are inherently true when specified
- Filters provide dynamic matching - as new applications are identified, they automatically match if criteria are met
- When specifying multiple values for a single criterion, OR logic is used
- Different criteria types use AND logic between them
