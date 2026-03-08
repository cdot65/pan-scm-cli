# BGP Route Map

BGP route maps define match conditions and set actions for BGP route policy processing. The `scm` CLI provides commands to create, update, delete, and load BGP route maps.

## Overview

The `bgp-route-map` commands allow you to:

- Create BGP route maps with match and set actions
- Update existing route map configurations
- Delete route maps that are no longer needed
- Bulk import route maps from YAML files
- Export route maps for backup or migration

## Set BGP Route Map

Create or update a BGP route map.

### Syntax

```bash
scm set network bgp-route-map NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Route map name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--route-map-json TEXT` | Route map entries as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create a Route Map with Permit Action

```bash
$ scm set network bgp-route-map my-route-map \
    --folder Texas \
    --route-map-json '[{"name": "rule1", "action": "permit", "match": {"as_path": "my-as-path"}}]'
---> 100%
Created BGP route map: my-route-map in folder Texas
```

#### Create a Route Map with Deny Action

```bash
$ scm set network bgp-route-map deny-map \
    --folder Texas \
    --route-map-json '[{"name": "rule1", "action": "deny", "match": {"community": "no-export"}}]'
---> 100%
Created BGP route map: deny-map in folder Texas
```

## Delete BGP Route Map

Delete a BGP route map from SCM.

### Syntax

```bash
scm delete network bgp-route-map NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Route map name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete network bgp-route-map my-route-map --folder Texas
---> 100%
Deleted BGP route map: my-route-map from folder Texas
```

## Load BGP Route Map

Load multiple BGP route maps from a YAML file.

### Syntax

```bash
scm load network bgp-route-map [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--dry-run` | Preview changes without applying | No |

\* One of --folder, --snippet, or --device is required.

### YAML File Format

```yaml
---
bgp_route_maps:
  - name: permit-map
    folder: Texas
    route_map:
      - name: "rule1"
        action: permit
        match:
          as_path: "my-as-path"

  - name: deny-map
    folder: Texas
    route_map:
      - name: "rule1"
        action: deny
        match:
          community: "no-export"
```

### Examples

#### Load with Original Locations

```bash
$ scm load network bgp-route-map --file route-maps.yml
---> 100%
✓ Loaded BGP route map: permit-map
✓ Loaded BGP route map: deny-map

Successfully loaded 2 out of 2 BGP route maps from 'route-maps.yml'
```

#### Load with Folder Override

```bash
$ scm load network bgp-route-map --file route-maps.yml --folder Austin
---> 100%
✓ Loaded BGP route map: permit-map
✓ Loaded BGP route map: deny-map

Successfully loaded 2 out of 2 BGP route maps from 'route-maps.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all BGP route maps
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show BGP Route Map

Display BGP route map objects.

### Syntax

```bash
scm show network bgp-route-map [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Name of a specific route map | No |

\* One of --folder, --snippet, or --device is required.

!!! note
    When no `--name` is specified, all items are listed by default.

### Examples

#### Show Specific BGP Route Map

```bash
$ scm show network bgp-route-map --folder Texas --name my-route-map
---> 100%
BGP Route Map: my-route-map
  Location: Folder 'Texas'
  Rules:
    rule1: permit (match AS path: my-as-path)
```

#### List All BGP Route Maps (Default Behavior)

```bash
$ scm show network bgp-route-map --folder Texas
---> 100%
BGP route maps in folder 'Texas':
------------------------------------------------------------
Name: permit-map
  Rules: 1
------------------------------------------------------------
Name: deny-map
  Rules: 1
------------------------------------------------------------
```

## Backup BGP Route Maps

Backup all BGP route map objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network bgp-route-map [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--file TEXT` | Custom output filename | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup network bgp-route-map --folder Texas
---> 100%
Successfully backed up 6 BGP route maps to bgp_route_map_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network bgp-route-map --folder Texas --file texas-route-maps.yaml
---> 100%
Successfully backed up 6 BGP route maps to texas-route-maps.yaml
```

## Best Practices

1. **Order Rules Carefully**: Route map rules are evaluated in order; place more specific matches first.
2. **Use Explicit Deny**: End route maps with an explicit deny rule to make the policy intent clear.
3. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
4. **Backup Before Changes**: Always backup existing route maps before making bulk modifications.
5. **Document Match Criteria**: Use descriptive rule names that indicate what each match condition does.
