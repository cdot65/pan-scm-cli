# Security Zones

Security zones are logical divisions of the network that define boundaries for traffic control and enforce security policies. The `pan-scm-cli` provides commands to create, update, delete, and load security zones.

## Set Security Zone

Create or update a security zone.

### Syntax

```
scm-cli set network security-zone [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--folder TEXT` | Folder for the security zone | Yes |
| `--name TEXT` | Name of the security zone | Yes |
| `--description TEXT` | Description for the security zone | No |
| `--tags LIST` | List of tags to apply to the security zone | No |
| `--mode TEXT` | Zone protection mode (layer3, layer2, virtual-wire, tap) | Yes |
| `--enable-user-id BOOLEAN` | Enable User-ID for this zone | No |
| `--exclude-local-pan BOOLEAN` | Exclude local Panorama from User-ID distribution | No |
| `--log-setting TEXT` | Log forwarding profile | No |

### Examples

#### Create a Layer 3 Security Zone

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set network security-zone --folder Shared --name Trust --mode layer3 --enable-user-id true --description "Internal trusted network zone"
Creating security zone 'Trust' in folder 'Shared'...
Security zone created successfully.
```

</div>

#### Create a Virtual-Wire Security Zone

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set network security-zone --folder Shared --name DMZ --mode virtual-wire --description "DMZ between trusted and untrusted networks"
Creating security zone 'DMZ' in folder 'Shared'...
Security zone created successfully.
```

</div>

## Delete Security Zone

Delete a security zone.

### Syntax

```
scm-cli delete network security-zone [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--folder TEXT` | Folder containing the security zone | Yes |
| `--name TEXT` | Name of the security zone to delete | Yes |

### Example

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli delete network security-zone --folder Shared --name DMZ
Deleting security zone 'DMZ' from folder 'Shared'...
Security zone deleted successfully.
```

</div>

## Load Security Zones

Create or update multiple security zones from a YAML file.

### Syntax

```
scm-cli load network security-zone [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--folder TEXT` | Folder for the security zones | Yes |
| `--file TEXT` | Path to YAML file containing security zone definitions | Yes |

### Example YAML File

```yaml
security_zones:
  - name: Trust
    description: "Internal trusted network zone"
    mode: layer3
    enable_user_id: true
    tags:
      - internal
      - trusted

  - name: Untrust
    description: "External untrusted network zone"
    mode: layer3
    enable_user_id: false
    tags:
      - external
      - untrusted

  - name: DMZ
    description: "DMZ between trusted and untrusted networks"
    mode: virtual-wire
    enable_user_id: true
    tags:
      - dmz
```

### Example Command

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli load network security-zone --folder Shared --file security-zones.yaml
Loading security zones from 'security-zones.yaml' into folder 'Shared'...
Created 3 security zones successfully.
```

</div>

## List Security Zones

List all security zones in a folder.

### Syntax

```
scm-cli set network security-zone --list [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--folder TEXT` | Folder to list security zones from | Yes |

### Example

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set network security-zone --list --folder Shared
Listing security zones in folder 'Shared'...

| Name    | Mode       | Description                        | User-ID | Tags                |
|---------|------------|------------------------------------|---------|--------------------|
| Trust   | layer3     | Internal trusted network zone      | Enabled | internal, trusted  |
| Untrust | layer3     | External untrusted network zone    | Disabled| external, untrusted|
| DMZ     | virtual-wire | DMZ between networks              | Enabled | dmz                |
```

</div>
