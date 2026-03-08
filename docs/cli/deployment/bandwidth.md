# Bandwidth Allocation

Bandwidth allocations control and optimize bandwidth usage across your SASE network by defining guaranteed and maximum bandwidth limits. The `scm` CLI provides commands to create, update, delete, and bulk load bandwidth allocation configurations.

## Overview

The `bandwidth` commands allow you to:

- Create bandwidth allocations with guaranteed and maximum bandwidth limits
- Assign allocations to specific Service Provider Networks (SPNs)
- Delete bandwidth allocations that are no longer needed
- Bulk import bandwidth allocations from YAML files
- List all bandwidth allocations in a folder

## Set Bandwidth Allocation

Create or update a bandwidth allocation.

### Syntax

```bash
scm set sase bandwidth [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder for the bandwidth allocation | Yes |
| `--name TEXT` | Name of the bandwidth allocation | Yes |
| `--egress-guaranteed INT` | Guaranteed egress bandwidth in Mbps | Yes |
| `--egress-max INT` | Maximum egress bandwidth in Mbps | Yes |
| `--ingress-guaranteed INT` | Guaranteed ingress bandwidth in Mbps | Yes |
| `--ingress-max INT` | Maximum ingress bandwidth in Mbps | Yes |
| `--description TEXT` | Description for the bandwidth allocation | No |
| `--tags LIST` | List of tags to apply | No |
| `--spn-name-list LIST` | Comma-separated list of SPN names | No |

### Examples

#### Create a Basic Bandwidth Allocation

```bash
$ scm set sase bandwidth \
    --folder Shared \
    --name Standard-Branch \
    --egress-guaranteed 50 \
    --egress-max 100 \
    --ingress-guaranteed 75 \
    --ingress-max 150 \
    --description "Standard bandwidth for branch offices"
---> 100%
Created bandwidth allocation: Standard-Branch in folder Shared
```

#### Create a Bandwidth Allocation with SPN Association

```bash
$ scm set sase bandwidth \
    --folder Shared \
    --name HQ-Bandwidth \
    --egress-guaranteed 500 \
    --egress-max 1000 \
    --ingress-guaranteed 750 \
    --ingress-max 1500 \
    --spn-name-list "HQ-SPN-1,HQ-SPN-2" \
    --description "High bandwidth for headquarters"
---> 100%
Created bandwidth allocation: HQ-Bandwidth in folder Shared
```

#### Assign Bandwidth Allocation to SPNs

```bash
$ scm set sase bandwidth \
    --folder Shared \
    --name Retail-Store \
    --egress-guaranteed 25 \
    --egress-max 50 \
    --ingress-guaranteed 35 \
    --ingress-max 70 \
    --spn-name-list "retail-spn-east,retail-spn-west"
---> 100%
Updated bandwidth allocation: Retail-Store in folder Shared
```

## Delete Bandwidth Allocation

Delete a bandwidth allocation from SCM.

### Syntax

```bash
scm delete sase bandwidth [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the bandwidth allocation | Yes |
| `--name TEXT` | Name of the bandwidth allocation to delete | Yes |

### Example

```bash
$ scm delete sase bandwidth --folder Shared --name Standard-Branch
---> 100%
Deleted bandwidth allocation: Standard-Branch from folder Shared
```

## Load Bandwidth Allocations

Load multiple bandwidth allocations from a YAML file.

### Syntax

```bash
scm load sase bandwidth [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing bandwidth allocation definitions | Yes |
| `--folder TEXT` | Folder override for all bandwidth allocations | No |

### YAML File Format

```yaml
---
bandwidth_allocations:
  - name: Standard-Branch
    folder: Shared
    description: "Standard bandwidth for branch offices"
    egress_guaranteed: 50
    egress_max: 100
    ingress_guaranteed: 75
    ingress_max: 150
    tags:
      - branch
      - standard

  - name: HQ-Bandwidth
    folder: Shared
    description: "High bandwidth for headquarters"
    egress_guaranteed: 500
    egress_max: 1000
    ingress_guaranteed: 750
    ingress_max: 1500
    spn_name_list:
      - HQ-SPN-1
      - HQ-SPN-2

  - name: Retail-Store
    folder: Shared
    description: "Limited bandwidth for retail locations"
    egress_guaranteed: 25
    egress_max: 50
    ingress_guaranteed: 35
    ingress_max: 70
```

### Examples

#### Load with Original Locations

```bash
$ scm load sase bandwidth --file bandwidth-allocations.yml
---> 100%
✓ Loaded bandwidth allocation: Standard-Branch
✓ Loaded bandwidth allocation: HQ-Bandwidth
✓ Loaded bandwidth allocation: Retail-Store

Successfully loaded 3 out of 3 bandwidth allocations from 'bandwidth-allocations.yml'
```

#### Load with Folder Override

```bash
$ scm load sase bandwidth --file bandwidth-allocations.yml --folder Shared
---> 100%
✓ Loaded bandwidth allocation: Standard-Branch
✓ Loaded bandwidth allocation: HQ-Bandwidth
✓ Loaded bandwidth allocation: Retail-Store

Successfully loaded 3 out of 3 bandwidth allocations from 'bandwidth-allocations.yml'
```

!!! note
    When using the `--folder` override option, all bandwidth allocations will be loaded
    into the specified folder, ignoring the folder specified in the YAML file.

## Show Bandwidth Allocation

Display bandwidth allocation objects.

### Syntax

```bash
scm show sase bandwidth [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to list bandwidth allocations from | Yes |
| `--name TEXT` | Name of the bandwidth allocation to show | No |

!!! note
    When no `--name` is specified, all items are listed by default.

### Examples

#### Show Specific Bandwidth Allocation

```bash
$ scm show sase bandwidth --folder Shared --name HQ-Bandwidth
---> 100%
Bandwidth Allocation: HQ-Bandwidth
  Location: Folder 'Shared'
  Egress: 500/1000 Mbps (guaranteed/max)
  Ingress: 750/1500 Mbps (guaranteed/max)
  SPNs: HQ-SPN-1, HQ-SPN-2
  Description: High bandwidth for headquarters
```

#### List All Bandwidth Allocations (Default Behavior)

```bash
$ scm show sase bandwidth --folder Shared
---> 100%
Bandwidth Allocations in folder 'Shared':
------------------------------------------------------------
Name: Standard-Branch
  Egress: 50/100 Mbps (guaranteed/max)
  Ingress: 75/150 Mbps (guaranteed/max)
  SPNs: -
  Description: Standard bandwidth for branch offices
------------------------------------------------------------
Name: HQ-Bandwidth
  Egress: 500/1000 Mbps (guaranteed/max)
  Ingress: 750/1500 Mbps (guaranteed/max)
  SPNs: HQ-SPN-1, HQ-SPN-2
  Description: High bandwidth for headquarters
------------------------------------------------------------
Name: Retail-Store
  Egress: 25/50 Mbps (guaranteed/max)
  Ingress: 35/70 Mbps (guaranteed/max)
  SPNs: -
  Description: Limited bandwidth for retail locations
------------------------------------------------------------
```

## Best Practices

1. **Plan Bandwidth Tiers**: Define standard bandwidth tiers (e.g., branch, headquarters, retail) to simplify allocation management across your organization.
2. **Set Realistic Guarantees**: Ensure guaranteed bandwidth values reflect actual minimum requirements, as over-commitment can degrade performance for all sites.
3. **Associate SPNs Early**: Assign bandwidth allocations to SPNs during creation to ensure traffic shaping takes effect immediately.
4. **Use Tags for Organization**: Apply consistent tags to bandwidth allocations for easier filtering and reporting across large deployments.
5. **Monitor Utilization**: Regularly review bandwidth utilization against allocated limits and adjust configurations as traffic patterns change.
