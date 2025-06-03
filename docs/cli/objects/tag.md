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

```bash
$ scm set objects tag --folder Texas --name production \
  --color "Red" --comments "Production environment resources"
<span style="color: green;">✓</span> Tag 'production' created successfully
```

Multiple tags for categorization:

```bash
$ scm set objects tag --folder Texas --name critical --color "Orange"
$ scm set objects tag --folder Texas --name database --color "Blue"
$ scm set objects tag --folder Texas --name web-tier --color "Green"
<span style="color: green;">✓</span> Tag 'critical' created successfully
<span style="color: green;">✓</span> Tag 'database' created successfully
<span style="color: green;">✓</span> Tag 'web-tier' created successfully
```

### Listing Tags (Default Behavior)

```bash
$ scm show objects tag --folder Texas
Tags in folder 'Texas':
- production (Red)
- development (Yellow)
- critical (Orange)
- database (Blue)
- web-tier (Green)
```

!!! note
When no --name is specified, all tags are listed by default.

### Showing Tag Details

```bash
$ scm show objects tag --folder Texas --name production
Tag: production
  Color: Red
  Comments: Production environment resources
  Folder: Texas
```

### Deleting Tags

```bash
$ scm delete objects tag --folder Texas --name production
<span style="color: green;">✓</span> Tag 'production' deleted successfully
```

### Load Tags

Load multiple tags from a YAML file.

#### Syntax

```bash
scm load objects tag [OPTIONS]
```

#### Options

| Option           | Description                                  | Required |
| ---------------- | -------------------------------------------- | -------- |
| `--file TEXT`    | Path to YAML file containing tag definitions | Yes      |
| `--folder TEXT`  | Override folder location for all objects     | No       |
| `--snippet TEXT` | Override snippet location for all objects    | No       |
| `--device TEXT`  | Override device location for all objects     | No       |
| `--dry-run`      | Preview changes without applying them        | No       |

#### Examples

Load from file with original locations:

```bash
$ scm load objects tag --file tags.yml
<span style="color: green;">✓</span> Created tag: production in Texas
<span style="color: green;">✓</span> Created tag: staging in Texas
<span style="color: green;">✓</span> Created tag: development in Texas
<span style="color: green;">✓</span> Created tag: finance in Texas

<span style="color: green;">✓</span> Summary: Processed 42 tags
```

Load with folder override:

```bash
$ scm load objects tag --file tags.yml --folder Austin
<span style="color: green;">✓</span> Created tag: production in Austin
<span style="color: green;">✓</span> Created tag: staging in Austin
<span style="color: green;">✓</span> Created tag: development in Austin
<span style="color: green;">✓</span> Created tag: finance in Austin

<span style="color: green;">✓</span> Summary: Processed 42 tags
```

!!! note
When using container override options (--folder, --snippet, --device), all tags will be loaded into the specified container, ignoring the container specified in the YAML file.

### Backup Tags

Backup all tag objects from a specified location to a YAML file.

#### Syntax

```bash
scm backup objects tag [OPTIONS]
```

#### Options

| Option           | Description                                  | Required |
| ---------------- | -------------------------------------------- | -------- |
| `--folder TEXT`  | Folder to backup tags from                   | No\*     |
| `--snippet TEXT` | Snippet to backup tags from                  | No\*     |
| `--device TEXT`  | Device to backup tags from                   | No\*     |
| `--file TEXT`    | Output filename (defaults to auto-generated) | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

#### Examples

Backup from folder:

```bash
$ scm backup objects tag --folder Texas
<span style="color: green;">✓</span> Successfully backed up 42 tags to tag_folder_texas_20240115_120530.yaml
```

Backup with custom filename:

```bash
$ scm backup objects tag --folder Texas --file texas-tags.yaml
<span style="color: green;">✓</span> Successfully backed up 42 tags to texas-tags.yaml
```

## YAML Configuration Format

Tags can be defined in YAML for bulk operations:

```yaml
tags:
  # Environment tags
  - name: production
    folder: Texas # Container location (folder, snippet, or device)
    color: "Red"
    comments: "Production environment resources"

  - name: staging
    folder: Texas
    color: "Orange"
    comments: "Staging environment resources"

  - name: development
    folder: Texas
    color: "Yellow"
    comments: "Development environment resources"

  # Department tags
  - name: finance
    folder: Texas
    color: "Gold"
    comments: "Finance department resources"

  - name: hr
    folder: Texas
    color: "Purple"
    comments: "Human resources department"

  - name: it
    folder: Texas
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

| Color Name     | Color Name    | Color Name    |
| -------------- | ------------- | ------------- |
| Red            | Green         | Blue          |
| Yellow         | Copper        | Orange        |
| Purple         | Gray          | Light Green   |
| Cyan           | Light Gray    | Blue Gray     |
| Lime           | Black         | Gold          |
| Brown          | Olive         | Maroon        |
| Red-Orange     | Yellow-Orange | Forest Green  |
| Turquoise Blue | Azure Blue    | Cerulean Blue |
| Midnight Blue  | Medium Blue   | Cobalt Blue   |
| Violet Blue    | Blue Violet   | Medium Violet |
| Medium Rose    | Lavender      | Orchid        |
| Thistle        | Peach         | Salmon        |
| Magenta        | Red Violet    | Mahogany      |
| Burnt Sienna   | Chestnut      |               |

## Examples

### Create Environment Tags

```bash
# Production environment
scm set objects tag --folder Shared --name prod \
  --color "Red" --comments "Production resources - handle with care"

# Development environment
scm set objects tag --folder Shared --name dev \
  --color "Green" --comments "Development resources - safe to modify"

# Test environment
scm set objects tag --folder Shared --name test \
  --color "Yellow" --comments "Test resources - automated testing"
```

### Create Department Tags

```bash
# Create department tags with consistent color scheme
scm set objects tag --folder Shared --name dept-finance \
  --color "Gold" --comments "Finance department"

scm set objects tag --folder Shared --name dept-hr \
  --color "Purple" --comments "Human Resources"

scm set objects tag --folder Shared --name dept-it \
  --color "Blue" --comments "Information Technology"
```

### Create Security Classification Tags

```bash
# Security classification tags
scm set objects tag --folder Shared --name confidential \
  --color "Red" --comments "Confidential data - restricted access"

scm set objects tag --folder Shared --name internal \
  --color "Orange" --comments "Internal use only"

scm set objects tag --folder Shared --name public \
  --color "Green" --comments "Public information"
```

## Using Tags

Tags can be applied to various objects:

### Apply Tags to Addresses

```bash
scm set objects address --folder Shared --name web-server \
  --ip-netmask 10.0.1.10/32 --tag "production,web-tier,critical"
```

### Apply Tags to Services

```bash
scm set objects service --folder Shared --name custom-app \
  --protocol tcp --port 8080 --tag "production,tier1"
```

### Use Tags in Dynamic Groups

```bash
scm set objects dynamic-user-group --folder Shared --name prod-admins \
  --filter "'production' and 'admin'"
```

### Use Tags in Dynamic Address Groups

```bash
scm set objects address-group --folder Shared --name prod-servers \
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
