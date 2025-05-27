# Application Group Management

This section covers the commands for managing application group objects in Strata Cloud Manager.

## Overview

Application groups provide a way to logically group multiple applications together for use in security policies. The `application-group` commands allow you to:

- Create and manage groups of applications
- Reference both built-in and custom applications
- Use application groups in security rules
- Apply tags for organization

## Commands

### Creating/Updating Application Groups

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects application-group --folder Texas --name business-apps \
  --members "salesforce,office365,zoom,custom-crm" \
  --description "Business critical applications"
<span style="color: green;">✓</span> Application group 'business-apps' created successfully
```

</div>

With tags:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects application-group --folder Texas --name collaboration-tools \
  --members "slack,ms-teams,zoom,webex" \
  --tag "collaboration,approved" \
  --description "Approved collaboration applications"
<span style="color: green;">✓</span> Application group 'collaboration-tools' created successfully
```

</div>

### Listing Application Groups

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects application-group --folder Texas --list
Application groups in folder 'Texas':
- business-apps
- collaboration-tools
- file-sharing-apps
- social-media
```

</div>

### Showing Application Group Details

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects application-group --folder Texas --name business-apps
Application Group: business-apps
  Members: salesforce, office365, zoom, custom-crm
  Description: Business critical applications
  Tags: None
  Folder: Texas
```

</div>

### Deleting Application Groups

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli delete objects application-group --folder Texas --name business-apps
<span style="color: green;">✓</span> Application group 'business-apps' deleted successfully
```

</div>

### Bulk Operations

Load multiple application groups from a YAML file:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli load objects application-group --folder Texas --file app-groups.yml
<span style="color: green;">✓</span> Loaded 10 application groups successfully
```

</div>

Backup existing application groups:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli backup objects application-group --folder Texas
<span style="color: green;">✓</span> Backed up 10 application groups to application-group-texas.yaml
```

</div>

## YAML Configuration Format

Application groups can be defined in YAML for bulk operations:

```yaml
application_groups:
  - name: business-apps
    description: "Business critical applications"
    members:
      - salesforce
      - office365
      - zoom
      - custom-crm
    
  - name: collaboration-tools
    description: "Approved collaboration applications"
    members:
      - slack
      - ms-teams
      - zoom
      - webex
    tag:
      - collaboration
      - approved
    
  - name: file-sharing-apps
    description: "File sharing and transfer applications"
    members:
      - dropbox
      - google-drive
      - onedrive
      - box
    tag:
      - file-sharing
    
  - name: social-media
    description: "Social media applications"
    members:
      - facebook
      - twitter
      - linkedin
      - instagram
    tag:
      - social
      - monitor
```

## Configuration Options

### Required Parameters

- `--name`: Name of the application group
- `--members`: Comma-separated list of application names

### Optional Parameters

- `--description`: Detailed description of the group
- `--tag`: Tags for categorization (comma-separated)

### Context Parameters

Exactly one context parameter must be specified:

- `--folder`: Folder name (e.g., "Texas", "Shared")
- `--snippet`: Snippet name for Panorama
- `--device`: Device name for NGFW

## Examples

### Create a Basic Application Group

```bash
scm-cli set objects application-group --folder Shared --name web-apps \
  --members "web-browsing,ssl,http,https"
```

### Create a Comprehensive Business Group

```bash
scm-cli set objects application-group --folder Shared --name critical-business \
  --members "salesforce,sap,oracle,custom-erp,custom-crm" \
  --tag "critical,business,monitor" \
  --description "Critical business applications requiring monitoring"
```

### Create a Security-Focused Group

```bash
scm-cli set objects application-group --folder Shared --name high-risk-apps \
  --members "bittorrent,tor,psiphon,ultrasurf" \
  --tag "block,high-risk" \
  --description "High-risk applications to block"
```

## Best Practices

1. **Logical Grouping**: Group applications that serve similar purposes or have similar security requirements

2. **Naming Convention**: Use descriptive names that indicate the group's purpose

3. **Documentation**: Always include descriptions to explain the group's purpose

4. **Tag Usage**: Use tags to categorize groups for easier management

5. **Regular Review**: Periodically review group membership to ensure accuracy

## Integration with Security Policies

Application groups are commonly used in security rules:

```bash
# Allow business applications
scm-cli set security rule --folder Shared --name "Allow-Business-Apps" \
  --source-zones "Trust" --destination-zones "Internet" \
  --applications "@business-apps" --action allow

# Block high-risk applications
scm-cli set security rule --folder Shared --name "Block-High-Risk" \
  --source-zones "any" --destination-zones "any" \
  --applications "@high-risk-apps" --action deny
```

## Notes

- Application group names must be unique within a folder
- Members must be existing applications (built-in or custom)
- Groups can contain both built-in and custom applications
- Tags must exist before being referenced
- Groups are referenced in policies using the "@" prefix
- Empty groups are allowed but not recommended