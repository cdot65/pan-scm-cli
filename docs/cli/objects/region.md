# Region

Regions define geographic locations with optional latitude, longitude, and address associations for use in security policies. The `scm` CLI provides commands to create, update, delete, show, load, and backup region objects.

## Overview

The `region` commands allow you to:

- Create regions with geographic coordinates
- Associate address ranges with regions
- Delete regions that are no longer needed
- Bulk import regions from YAML files
- Export regions for backup or migration

## Set Region

Create or update a region.

### Syntax

```bash
scm set object region NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the region (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--latitude FLOAT` | Latitude (-90 to 90) | No |
| `--longitude FLOAT` | Longitude (-180 to 180) | No |
| `--addresses TEXT` | Associated addresses | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Create a Region with Coordinates

```bash
$ scm set object region us-west \
    --folder Texas \
    --latitude 37.7749 \
    --longitude -122.4194
---> 100%
Created region: us-west in folder Texas
```

#### Create a Region with Addresses

```bash
$ scm set object region branch-offices \
    --folder Texas \
    --addresses 10.0.0.0/8 \
    --addresses 172.16.0.0/12
---> 100%
Created region: branch-offices in folder Texas
```

## Delete Region

Delete a region from SCM.

### Syntax

```bash
scm delete object region NAME [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `NAME` | Name of the region (positional) | Yes |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--force` | Skip confirmation prompt | No |

\* One of --folder, --snippet, or --device is required.

### Example

```bash
$ scm delete object region us-west --folder Texas --force
---> 100%
Deleted region: us-west from folder Texas
```

## Load Regions

Load multiple regions from a YAML file.

### Syntax

```bash
scm load object region [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing region definitions | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
regions:
  - name: us-west
    folder: Texas
    latitude: 37.7749
    longitude: -122.4194

  - name: branch-offices
    folder: Texas
    addresses:
      - 10.0.0.0/8
      - 172.16.0.0/12
```

### Examples

#### Load with Original Locations

```bash
$ scm load object region --file regions.yaml
---> 100%
✓ Loaded region: us-west
✓ Loaded region: branch-offices

Successfully loaded 2 out of 2 regions from 'regions.yaml'
```

#### Load with Folder Override

```bash
$ scm load object region --file regions.yaml --folder Austin
---> 100%
✓ Loaded region: us-west
✓ Loaded region: branch-offices

Successfully loaded 2 out of 2 regions from 'regions.yaml'
```

!!! note
    When using container override options (--folder, --snippet, --device), all regions
    will be loaded into the specified container, ignoring the container specified in the
    YAML file.

## Show Region

Display region objects.

### Syntax

```bash
scm show object region [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder location | No\* |
| `--snippet TEXT` | Snippet location | No\* |
| `--device TEXT` | Device location | No\* |
| `--name TEXT` | Name of specific region to show | No |

!!! note
    When no `--name` is specified, all items are listed by default.

\* One of --folder, --snippet, or --device is required.

### Examples

#### Show Specific Region

```bash
$ scm show object region --folder Texas --name us-west
---> 100%
Region: us-west
  Location: Folder 'Texas'
  Latitude: 37.7749
  Longitude: -122.4194
```

#### List All Regions (Default Behavior)

```bash
$ scm show object region --folder Texas
---> 100%
Regions in folder 'Texas':
------------------------------------------------------------
Name: us-west
  Latitude: 37.7749
  Longitude: -122.4194
------------------------------------------------------------
Name: branch-offices
  Addresses: 10.0.0.0/8, 172.16.0.0/12
------------------------------------------------------------
```

## Backup Regions

Backup all region objects from a specified location to a YAML file.

### Syntax

```bash
scm backup object region [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup regions from | No\* |
| `--snippet TEXT` | Snippet to backup regions from | No\* |
| `--device TEXT` | Device to backup regions from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup object region --folder Texas
---> 100%
Successfully backed up 5 regions to region_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object region --folder Texas --file texas-regions.yaml
---> 100%
Successfully backed up 5 regions to texas-regions.yaml
```

## Best Practices

1. **Use Descriptive Names**: Name regions after geographic locations or office names.
2. **Include Coordinates**: Add latitude and longitude for map-based visualization.
3. **Associate Addresses**: Link IP address ranges to regions for geographic policy enforcement.
4. **Use YAML for Bulk Operations**: For managing multiple regions, use YAML files.
5. **Organize by Folder**: Keep regions organized in logical folders.
