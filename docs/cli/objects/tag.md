# Tag Management

This section covers the commands for managing tag objects in Strata Cloud Manager.

## Overview

Tags provide a flexible way to categorize and organize objects across Strata Cloud Manager. The `tag` commands allow you to:

- Create tags with specific colors for visual identification
- Add descriptive comments to tags
- Apply tags to various objects (addresses, services, rules, etc.)
- Use tags in dynamic groups and policies
- Organize resources by department, environment, or purpose

## Commands

### Creating/Updating Tags

Basic tag with color:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects tag --folder Texas --name production \
  --color "Red" --comments "Production environment resources"
<span style="color: green;">✓</span> Tag 'production' created successfully
```

</div>

Multiple tags for categorization:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects tag --folder Texas --name critical --color "Orange"
$ scm-cli set objects tag --folder Texas --name database --color "Blue"
$ scm-cli set objects tag --folder Texas --name web-tier --color "Green"
<span style="color: green;">✓</span> Tag 'critical' created successfully
<span style="color: green;">✓</span> Tag 'database' created successfully
<span style="color: green;">✓</span> Tag 'web-tier' created successfully
```

</div>

### Listing Tags

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects tag --folder Texas --list
Tags in folder 'Texas':
- production (Red)
- development (Yellow)
- critical (Orange)
- database (Blue)
- web-tier (Green)
```

</div>

### Showing Tag Details

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects tag --folder Texas --name production
Tag: production
  Color: Red
  Comments: Production environment resources
  Folder: Texas
```

</div>

### Deleting Tags

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli delete objects tag --folder Texas --name production
<span style="color: green;">✓</span> Tag 'production' deleted successfully
```

</div>

### Bulk Operations

Load multiple tags from a YAML file:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli load objects tag --folder Texas --file tags.yml
<span style="color: green;">✓</span> Loaded 42 tags successfully
```

</div>

Backup existing tags:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli backup objects tag --folder Texas
<span style="color: green;">✓</span> Backed up 42 tags to tag-texas.yaml
```

</div>

## YAML Configuration Format

Tags can be defined in YAML for bulk operations:

```yaml
tags:
  # Environment tags
  - name: production
    color: "Red"
    comments: "Production environment resources"
    
  - name: staging
    color: "Orange"
    comments: "Staging environment resources"
    
  - name: development
    color: "Yellow"
    comments: "Development environment resources"
    
  # Department tags
  - name: finance
    color: "Gold"
    comments: "Finance department resources"
    
  - name: hr
    color: "Purple"
    comments: "Human resources department"
    
  - name: it
    color: "Blue"
    comments: "IT department resources"
    
  # Security classification
  - name: public
    color: "Green"
    comments: "Public-facing resources"
    
  - name: internal
    color: "Cyan"
    comments: "Internal resources only"
    
  - name: restricted
    color: "Magenta"
    comments: "Restricted access resources"
    
  # Service tiers
  - name: tier1
    color: "Cobalt Blue"
    comments: "Tier 1 - Critical services"
    
  - name: tier2
    color: "Medium Blue"
    comments: "Tier 2 - Important services"
    
  - name: tier3
    color: "Light Gray"
    comments: "Tier 3 - Standard services"
```

## Configuration Options

### Required Parameters

- `--name`: Name of the tag

### Optional Parameters

- `--color`: Color for visual identification (see supported colors below)
- `--comments`: Descriptive comments about the tag

### Context Parameters

Exactly one context parameter must be specified:

- `--folder`: Folder name (e.g., "Texas", "Shared")
- `--snippet`: Snippet name for Panorama
- `--device`: Device name for NGFW

## Supported Colors

The following 42 colors are supported:

| Color Name | Color Name | Color Name |
|------------|------------|------------|
| Red | Green | Blue |
| Yellow | Copper | Orange |
| Purple | Gray | Light Green |
| Cyan | Light Gray | Blue Gray |
| Lime | Black | Gold |
| Brown | Olive | Maroon |
| Red-Orange | Yellow-Orange | Forest Green |
| Turquoise Blue | Azure Blue | Cerulean Blue |
| Midnight Blue | Medium Blue | Cobalt Blue |
| Violet Blue | Blue Violet | Medium Violet |
| Medium Rose | Lavender | Orchid |
| Thistle | Peach | Salmon |
| Magenta | Red Violet | Mahogany |
| Burnt Sienna | Chestnut | |

## Examples

### Create Environment Tags

```bash
# Production environment
scm-cli set objects tag --folder Shared --name prod \
  --color "Red" --comments "Production resources - handle with care"

# Development environment
scm-cli set objects tag --folder Shared --name dev \
  --color "Green" --comments "Development resources - safe to modify"

# Test environment
scm-cli set objects tag --folder Shared --name test \
  --color "Yellow" --comments "Test resources - automated testing"
```

### Create Department Tags

```bash
# Create department tags with consistent color scheme
scm-cli set objects tag --folder Shared --name dept-finance \
  --color "Gold" --comments "Finance department"

scm-cli set objects tag --folder Shared --name dept-hr \
  --color "Purple" --comments "Human Resources"

scm-cli set objects tag --folder Shared --name dept-it \
  --color "Blue" --comments "Information Technology"
```

### Create Security Classification Tags

```bash
# Security classification tags
scm-cli set objects tag --folder Shared --name confidential \
  --color "Red" --comments "Confidential data - restricted access"

scm-cli set objects tag --folder Shared --name internal \
  --color "Orange" --comments "Internal use only"

scm-cli set objects tag --folder Shared --name public \
  --color "Green" --comments "Public information"
```

## Using Tags

Tags can be applied to various objects:

### Apply Tags to Addresses
```bash
scm-cli set objects address --folder Shared --name web-server \
  --ip-netmask 10.0.1.10/32 --tag "production,web-tier,critical"
```

### Apply Tags to Services
```bash
scm-cli set objects service --folder Shared --name custom-app \
  --protocol tcp --port 8080 --tag "production,tier1"
```

### Use Tags in Dynamic Groups
```bash
scm-cli set objects dynamic-user-group --folder Shared --name prod-admins \
  --filter "'production' and 'admin'"
```

### Use Tags in Dynamic Address Groups
```bash
scm-cli set objects address-group --folder Shared --name prod-servers \
  --type dynamic --filter "'production' and 'server'"
```

## Best Practices

1. **Consistent Naming**: Use a consistent naming convention (e.g., env-prod, dept-finance)

2. **Color Coding**: Establish a color scheme (e.g., Red for production, Green for development)

3. **Documentation**: Always add comments to explain the tag's purpose

4. **Hierarchical Tagging**: Use prefixes to create logical hierarchies

5. **Regular Cleanup**: Remove unused tags to maintain organization

## Notes

- Tag names must be unique within a folder
- Colors are case-sensitive (use exact names from the table)
- Tags must exist before being referenced by other objects
- Tags are used extensively in dynamic groups and filtering
- Comments help document the purpose and usage of tags
- Tags can be applied to most object types in SCM
- Deleting a tag doesn't automatically remove it from tagged objects