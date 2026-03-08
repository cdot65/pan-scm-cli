# Region

Regions define geographic locations with optional latitude, longitude, and address associations for use in security policies.

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
| `--folder TEXT` | Folder location | No |
| `--snippet TEXT` | Snippet location | No |
| `--device TEXT` | Device location | No |
| `--latitude FLOAT` | Latitude (-90 to 90) | No |
| `--longitude FLOAT` | Longitude (-180 to 180) | No |
| `--addresses TEXT` | Associated addresses | No |

### Examples

```bash
# Create a region with coordinates
$ scm set object region us-west \
    --folder Texas \
    --latitude 37.7749 \
    --longitude -122.4194

# Create a region with addresses
$ scm set object region branch-offices \
    --folder Texas \
    --addresses 10.0.0.0/8 --addresses 172.16.0.0/12
```

## Show Region

```bash
scm show object region --folder Texas
scm show object region --folder Texas --name us-west
```

## Delete Region

```bash
scm delete object region us-west --folder Texas
```

## Load Regions

```bash
scm load object region --file regions.yaml
```

## Backup Regions

```bash
scm backup object region --folder Texas
```
