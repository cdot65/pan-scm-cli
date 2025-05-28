# Bandwidth Allocation

Bandwidth allocation allows you to control and optimize bandwidth usage across your network. The `scm` CLI provides commands to create, update, delete, and load bandwidth allocation configurations.

## Set Bandwidth Allocation

Create or update a bandwidth allocation.

### Syntax

```bash
scm set deployment bandwidth [OPTIONS]
```

### Options

| Option                         | Description                                       | Required |
| ------------------------------ | ------------------------------------------------- | -------- |
| `--folder TEXT`                | Folder for the bandwidth allocation               | Yes      |
| `--name TEXT`                  | Name of the bandwidth allocation                  | Yes      |
| `--description TEXT`           | Description for the bandwidth allocation          | No       |
| `--tags LIST`                  | List of tags to apply to the bandwidth allocation | No       |
| `--egress-guaranteed INTEGER`  | Guaranteed egress bandwidth in Mbps               | Yes      |
| `--egress-max INTEGER`         | Maximum egress bandwidth in Mbps                  | Yes      |
| `--ingress-guaranteed INTEGER` | Guaranteed ingress bandwidth in Mbps              | Yes      |
| `--ingress-max INTEGER`        | Maximum ingress bandwidth in Mbps                 | Yes      |
| `--spn-name-list LIST`         | List of SPN names to apply this allocation to     | No       |

### Examples

#### Create a Bandwidth Allocation

```bash
$ scm set deployment bandwidth --folder Shared --name "Standard-Branch" \
  --egress-guaranteed 50 --egress-max 100 \
  --ingress-guaranteed 75 --ingress-max 150 \
  --description "Standard bandwidth allocation for branch offices"
Creating bandwidth allocation 'Standard-Branch' in folder 'Shared'...
Bandwidth allocation created successfully.
```

#### Create a Bandwidth Allocation with SPN Association

```bash
$ scm set deployment bandwidth --folder Shared --name "HQ-Bandwidth" \
  --egress-guaranteed 500 --egress-max 1000 \
  --ingress-guaranteed 750 --ingress-max 1500 \
  --spn-name-list "HQ-SPN-1,HQ-SPN-2" \
  --description "High bandwidth allocation for headquarters"
Creating bandwidth allocation 'HQ-Bandwidth' in folder 'Shared'...
Bandwidth allocation created successfully.
```

## Delete Bandwidth Allocation

Delete a bandwidth allocation.

### Syntax

```bash
scm delete deployment bandwidth [OPTIONS]
```

### Options

| Option          | Description                                | Required |
| --------------- | ------------------------------------------ | -------- |
| `--folder TEXT` | Folder containing the bandwidth allocation | Yes      |
| `--name TEXT`   | Name of the bandwidth allocation to delete | Yes      |

### Example

```bash
$ scm delete deployment bandwidth --folder Shared --name "Standard-Branch"
Deleting bandwidth allocation 'Standard-Branch' from folder 'Shared'...
Bandwidth allocation deleted successfully.
```

## Load Bandwidth Allocations

Create or update multiple bandwidth allocations from a YAML file.

### Syntax

```bash
scm load deployment bandwidth [OPTIONS]
```

### Options

| Option          | Description                                                   | Required |
| --------------- | ------------------------------------------------------------- | -------- |
| `--folder TEXT` | Folder for the bandwidth allocations                          | Yes      |
| `--file TEXT`   | Path to YAML file containing bandwidth allocation definitions | Yes      |

### Example YAML File

```yaml
bandwidth_allocations:
  - name: Standard-Branch
    description: "Standard bandwidth allocation for branch offices"
    egress_guaranteed: 50
    egress_max: 100
    ingress_guaranteed: 75
    ingress_max: 150
    tags:
      - branch
      - standard

  - name: HQ-Bandwidth
    description: "High bandwidth allocation for headquarters"
    egress_guaranteed: 500
    egress_max: 1000
    ingress_guaranteed: 750
    ingress_max: 1500
    spn_name_list:
      - HQ-SPN-1
      - HQ-SPN-2
    tags:
      - hq
      - high-bandwidth

  - name: Retail-Store
    description: "Limited bandwidth for retail locations"
    egress_guaranteed: 25
    egress_max: 50
    ingress_guaranteed: 35
    ingress_max: 70
    tags:
      - retail
      - limited
```

### Example Command

```bash
$ scm load deployment bandwidth --folder Shared --file bandwidth-allocations.yaml
Loading bandwidth allocations from 'bandwidth-allocations.yaml' into folder 'Shared'...
Created 3 bandwidth allocations successfully.
```

## List Bandwidth Allocations

List all bandwidth allocations in a folder.

### Syntax

```bash
scm set deployment bandwidth --list [OPTIONS]
```

### Options

| Option          | Description                               | Required |
| --------------- | ----------------------------------------- | -------- |
| `--folder TEXT` | Folder to list bandwidth allocations from | Yes      |

### Example

```bash
$ scm set deployment bandwidth --list --folder Shared
Listing bandwidth allocations in folder 'Shared'...

| Name | Egress (Guaranteed/Max) | Ingress (Guaranteed/Max) | SPNs | Description |
|------|-------------------------|--------------------------|------|-------------|
| Standard-Branch | 50/100 Mbps | 75/150 Mbps | - | Standard bandwidth allocation for branch offices |
| HQ-Bandwidth | 500/1000 Mbps | 750/1500 Mbps | HQ-SPN-1, HQ-SPN-2 | High bandwidth allocation for headquarters |
| Retail-Store | 25/50 Mbps | 35/70 Mbps | - | Limited bandwidth for retail locations |
```

## Assign Bandwidth Allocation

Assign a bandwidth allocation to specific Service Provider Networks (SPNs).

### Syntax

```bash
scm set deployment bandwidth --assign [OPTIONS]
```

### Options

| Option                 | Description                                  | Required |
| ---------------------- | -------------------------------------------- | -------- |
| `--folder TEXT`        | Folder containing the bandwidth allocation   | Yes      |
| `--name TEXT`          | Name of the bandwidth allocation             | Yes      |
| `--spn-name-list LIST` | List of SPN names to apply the allocation to | Yes      |

### Example

```bash
$ scm set deployment bandwidth --assign --folder Shared --name "Retail-Store" --spn-name-list "retail-spn-east,retail-spn-west"
Assigning bandwidth allocation 'Retail-Store' to SPNs 'retail-spn-east,retail-spn-west'...
Bandwidth allocation assigned successfully.
```
