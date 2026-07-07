# Application Filter Objects

Application filter objects provide dynamic application selection based on specific criteria in Strata Cloud Manager. The `scm` CLI provides commands to create, update, delete, show, backup, and load application filter objects.

## Overview

The `application-filter` commands allow you to:

- Create filters based on application characteristics
- Filter by categories, subcategories, and technologies
- Filter by risk levels and security attributes
- Use filters in security policies for dynamic control
- Export filters for backup or migration

## Set Application Filter

Create or update an application filter object.

### Syntax

```bash
scm set object application-filter NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the application filter | Yes |

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | Yes\* |
| `--snippet TEXT` | Snippet location | Yes\* |
| `--device TEXT` | Device location | Yes\* |
| `--category TEXT` | Application category to filter by (repeat for multiple) | Yes |
| `--subcategory TEXT` | Application subcategory to filter by (repeat for multiple) | Yes |
| `--technology TEXT` | Technology to filter by (repeat for multiple) | Yes |
| `--risk INTEGER` | Risk level (1-5) to filter by (repeat for multiple) | Yes |
| `--evasive` | Filter for evasive applications | No |
| `--pervasive` | Filter for pervasive applications | No |
| `--excessive-bandwidth-use` | Filter for bandwidth-heavy applications | No |
| `--used-by-malware` | Filter for applications used by malware | No |
| `--transfers-files` | Filter for file transfer applications | No |
| `--has-known-vulnerabilities` | Filter for vulnerable applications | No |
| `--tunnels-other-apps` | Filter for tunneling applications | No |
| `--prone-to-misuse` | Filter for applications prone to misuse | No |
| `--no-certifications` | Filter for uncertified applications | No |

\* Exactly one of `--folder`, `--snippet`, or `--device` is required.

### Examples

#### Create Basic Filter by Category and Risk

```bash
$ scm set object application-filter high-risk-apps \
    --folder Texas \
    --category file-sharing --category peer-to-peer \
    --subcategory file-transfer \
    --technology peer-to-peer \
    --risk 4 --risk 5
---> 100%
Created application filter: high-risk-apps in folder Texas
```

#### Create Filter with Security Characteristics

```bash
$ scm set object application-filter malware-apps \
    --folder Texas \
    --category file-sharing \
    --subcategory file-transfer \
    --technology peer-to-peer \
    --risk 5 \
    --used-by-malware \
    --has-known-vulnerabilities \
    --transfers-files
---> 100%
Created application filter: malware-apps in folder Texas
```

## Delete Application Filter

Delete an application filter object from SCM.

### Syntax

```bash
scm delete object application-filter NAME [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the application filter object to delete | Yes |

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
$ scm delete object application-filter high-risk-apps --folder Texas --force
---> 100%
Deleted application filter: high-risk-apps from folder Texas
```

## Load Application Filters

Load multiple application filter objects from a YAML file.

### Syntax

```bash
scm load object application-filter [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing application filter definitions | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
application_filters:
  - name: high-risk-apps
    folder: Texas
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
```

### Examples

#### Load with Original Locations

```bash
$ scm load object application-filter --file app-filters.yml
---> 100%
✓ Loaded application filter: high-risk-apps
✓ Loaded application filter: vulnerable-apps
✓ Loaded application filter: bandwidth-heavy

Successfully loaded 3 out of 3 application filters from 'app-filters.yml'
```

#### Load with Folder Override

```bash
$ scm load object application-filter --file app-filters.yml --folder Austin
---> 100%
✓ Loaded application filter: high-risk-apps
✓ Loaded application filter: vulnerable-apps
✓ Loaded application filter: bandwidth-heavy

Successfully loaded 3 out of 3 application filters from 'app-filters.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all application
filters will be loaded into the specified container, ignoring the container specified
in the YAML file.
:::

## Show Application Filter

Display application filter objects.

### Syntax

```bash
scm show object application-filter [NAME] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the application filter object to show; omit to list all | No |

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

#### Show Specific Application Filter

```bash
$ scm show object application-filter high-risk-apps --folder Texas
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
$ scm show object application-filter --folder Texas
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
scm backup object application-filter [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup application filters from | No\* |
| `--snippet TEXT` | Snippet to backup application filters from | No\* |
| `--device TEXT` | Device to backup application filters from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup object application-filter --folder Texas
---> 100%
Successfully backed up 5 application filters to application-filter_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object application-filter --folder Texas --file texas-app-filters.yaml
---> 100%
Successfully backed up 5 application filters to texas-app-filters.yaml
```

## Best Practices

1. **Clear Naming**: Use descriptive names that indicate the filter's purpose and criteria.
2. **Combine Criteria**: Use multiple criteria for more precise application matching.
3. **Risk-Based Approach**: Group applications by risk level for tiered policy enforcement.
4. **Regular Updates**: Review filters periodically as new applications are identified.
5. **Documentation**: Always include descriptions explaining the filter's purpose.
6. **Use YAML for Bulk Operations**: For complex deployments, use YAML files.
7. **Organize by Container**: Keep filters organized in appropriate folders, snippets, or devices.
