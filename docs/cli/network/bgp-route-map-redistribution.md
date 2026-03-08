# BGP Route Map Redistribution

BGP route map redistributions define how routes from different source protocols are redistributed using route maps. The `scm` CLI provides commands to create, update, delete, and load BGP route map redistributions.

## Overview

The `bgp-route-map-redistribution` commands allow you to:

- Create BGP route map redistributions for various source protocols
- Update existing route map redistribution configurations
- Delete route map redistributions that are no longer needed
- Bulk import route map redistributions from YAML files
- Export route map redistributions for backup or migration

## Set BGP Route Map Redistribution

Create or update a BGP route map redistribution.

### Syntax

```bash
scm set network bgp-route-map-redistribution NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--bgp-json TEXT` | BGP source protocol config as JSON | No |
| `--ospf-json TEXT` | OSPF source protocol config as JSON | No |
| `--connected-static-json TEXT` | Connected/Static source config as JSON | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Redistribute Connected Routes via Route Map

```bash
$ scm set network bgp-route-map-redistribution my-redist-map \
    --folder Texas \
    --connected-static-json '{"connected": {"route_map": "my-route-map"}}'
---> 100%
Created BGP route map redistribution: my-redist-map in folder Texas
```

#### Redistribute OSPF Routes via Route Map

```bash
$ scm set network bgp-route-map-redistribution ospf-redist \
    --folder Texas \
    --ospf-json '{"route_map": "ospf-to-bgp-map"}'
---> 100%
Created BGP route map redistribution: ospf-redist in folder Texas
```

## Delete BGP Route Map Redistribution

Delete a BGP route map redistribution from SCM.

### Syntax

```bash
scm delete network bgp-route-map-redistribution NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Name (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete network bgp-route-map-redistribution my-redist-map --folder Texas
---> 100%
Deleted BGP route map redistribution: my-redist-map from folder Texas
```

## Load BGP Route Map Redistribution

Load multiple BGP route map redistributions from a YAML file.

### Syntax

```bash
scm load network bgp-route-map-redistribution [OPTIONS]
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
bgp_route_map_redistributions:
  - name: connected-redist
    folder: Texas
    connected_static:
      connected:
        route_map: "my-route-map"

  - name: ospf-redist
    folder: Texas
    ospf:
      route_map: "ospf-to-bgp-map"
```

### Examples

#### Load with Original Locations

```bash
$ scm load network bgp-route-map-redistribution --file redist-maps.yml
---> 100%
✓ Loaded BGP route map redistribution: connected-redist
✓ Loaded BGP route map redistribution: ospf-redist

Successfully loaded 2 out of 2 BGP route map redistributions from 'redist-maps.yml'
```

#### Load with Folder Override

```bash
$ scm load network bgp-route-map-redistribution --file redist-maps.yml --folder Austin
---> 100%
✓ Loaded BGP route map redistribution: connected-redist
✓ Loaded BGP route map redistribution: ospf-redist

Successfully loaded 2 out of 2 BGP route map redistributions from 'redist-maps.yml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all BGP route map redistributions
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show BGP Route Map Redistribution

Display BGP route map redistribution objects.

### Syntax

```bash
scm show network bgp-route-map-redistribution [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Name of a specific redistribution | No |

\* One of --folder, --snippet, or --device is required.

!!! note
    When no `--name` is specified, all items are listed by default.

### Examples

#### Show Specific BGP Route Map Redistribution

```bash
$ scm show network bgp-route-map-redistribution --folder Texas --name my-redist-map
---> 100%
BGP Route Map Redistribution: my-redist-map
  Location: Folder 'Texas'
  Connected Route Map: my-route-map
```

#### List All BGP Route Map Redistributions (Default Behavior)

```bash
$ scm show network bgp-route-map-redistribution --folder Texas
---> 100%
BGP route map redistributions in folder 'Texas':
------------------------------------------------------------
Name: connected-redist
  Source: Connected
  Route Map: my-route-map
------------------------------------------------------------
Name: ospf-redist
  Source: OSPF
  Route Map: ospf-to-bgp-map
------------------------------------------------------------
```

## Backup BGP Route Map Redistributions

Backup all BGP route map redistribution objects from a specified location to a YAML file.

### Syntax

```bash
scm backup network bgp-route-map-redistribution [OPTIONS]
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
$ scm backup network bgp-route-map-redistribution --folder Texas
---> 100%
Successfully backed up 3 BGP route map redistributions to bgp_route_map_redistribution_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup network bgp-route-map-redistribution --folder Texas --file texas-redist-maps.yaml
---> 100%
Successfully backed up 3 BGP route map redistributions to texas-redist-maps.yaml
```

## Best Practices

1. **Reference Existing Route Maps**: Ensure route maps referenced in redistribution configs exist before applying.
2. **Redistribute Selectively**: Only redistribute protocols that need to be advertised via BGP.
3. **Test with Dry Run**: Use `--dry-run` when loading configurations to preview changes before applying.
4. **Backup Before Changes**: Always backup existing configurations before making bulk modifications.
5. **Coordinate with Route Maps**: Update route maps and redistribution configurations together to avoid routing inconsistencies.
