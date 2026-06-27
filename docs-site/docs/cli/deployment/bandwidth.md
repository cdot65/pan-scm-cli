# Bandwidth Allocation

Bandwidth allocations control and optimize bandwidth usage across your SASE network by defining guaranteed and maximum bandwidth limits. The `scm` CLI provides commands to create, update, delete, and bulk load bandwidth allocation configurations.

## Overview

The `bandwidth-allocation` commands allow you to:

- Create bandwidth allocations with guaranteed and maximum bandwidth limits
- Assign allocations to specific Service Provider Networks (SPNs)
- Delete bandwidth allocations that are no longer needed
- Bulk import bandwidth allocations from YAML files
- List all bandwidth allocations

## Set Bandwidth Allocation

Create or update a bandwidth allocation.

### Syntax

```bash
scm set sase bandwidth-allocation [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the bandwidth allocation | Yes |
| `--bandwidth INT` | Bandwidth value in Mbps | Yes |
| `--spn-name-list TEXT` | SPN names (comma-separated if multiple) | Yes |
| `--description TEXT` | Description for the bandwidth allocation | No |
| `--tags TEXT` | Tags (comma-separated if multiple) | No |

:::note
Bandwidth allocations are global resources and do not require a `--folder` parameter.
:::

### Examples

#### Create a Basic Bandwidth Allocation

```bash
$ scm set sase bandwidth-allocation \
    --name Standard-Branch \
    --bandwidth 100 \
    --spn-name-list "branch-spn-1" \
    --description "Standard bandwidth for branch offices"
---> 100%
Created bandwidth allocation: Standard-Branch (100 Mbps)
```

#### Create a Bandwidth Allocation with Multiple SPNs

```bash
$ scm set sase bandwidth-allocation \
    --name HQ-Bandwidth \
    --bandwidth 1000 \
    --spn-name-list "HQ-SPN-1,HQ-SPN-2" \
    --description "High bandwidth for headquarters"
---> 100%
Created bandwidth allocation: HQ-Bandwidth (1000 Mbps)
```

## Delete Bandwidth Allocation

Delete a bandwidth allocation from SCM.

### Syntax

```bash
scm delete sase bandwidth-allocation [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the bandwidth allocation to delete | Yes |
| `--spn-name-list TEXT` | SPN names (comma-separated if multiple) | Yes |
| `--force` | Skip confirmation prompt | No |

### Example

```bash
$ scm delete sase bandwidth-allocation --name Standard-Branch --spn-name-list "branch-spn-1" --force
---> 100%
Deleted bandwidth allocation: Standard-Branch
```

## Load Bandwidth Allocations

Load multiple bandwidth allocations from a YAML file.

### Syntax

```bash
scm load sase bandwidth-allocation [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing bandwidth allocation definitions | Yes |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
bandwidth_allocations:
  - name: Standard-Branch
    bandwidth: 100
    description: "Standard bandwidth for branch offices"
    spn_name_list:
      - branch-spn-1
    tags:
      - branch
      - standard

  - name: HQ-Bandwidth
    bandwidth: 1000
    description: "High bandwidth for headquarters"
    spn_name_list:
      - HQ-SPN-1
      - HQ-SPN-2
```

### Examples

#### Load with Original Locations

```bash
$ scm load sase bandwidth-allocation --file bandwidth-allocations.yml
---> 100%
✓ Loaded bandwidth allocation: Standard-Branch
✓ Loaded bandwidth allocation: HQ-Bandwidth
✓ Loaded bandwidth allocation: Retail-Store

Successfully loaded 3 out of 3 bandwidth allocations from 'bandwidth-allocations.yml'
```

## Show Bandwidth Allocation

Display bandwidth allocation objects.

### Syntax

```bash
scm show sase bandwidth-allocation [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--name TEXT` | Name of the bandwidth allocation to show | No |

:::note
When no `--name` is specified, all items are listed by default.
:::

### Examples

#### Show Specific Bandwidth Allocation

```bash
$ scm show sase bandwidth-allocation --name HQ-Bandwidth
---> 100%
Bandwidth Allocation: HQ-Bandwidth
  Allocated Bandwidth: 1000 Mbps
  SPNs: HQ-SPN-1, HQ-SPN-2
```

#### List All Bandwidth Allocations (Default Behavior)

```bash
$ scm show sase bandwidth-allocation
---> 100%
Bandwidth Allocations:
------------------------------------------------------------
Name: Standard-Branch
  Bandwidth: 100 Mbps
  SPNs: branch-spn-1
------------------------------------------------------------
Name: HQ-Bandwidth
  Bandwidth: 1000 Mbps
  SPNs: HQ-SPN-1, HQ-SPN-2
------------------------------------------------------------
```

## Best Practices

1. **Plan Bandwidth Tiers**: Define standard bandwidth tiers (e.g., branch, headquarters, retail) to simplify allocation management across your organization.
2. **Set Realistic Guarantees**: Ensure guaranteed bandwidth values reflect actual minimum requirements, as over-commitment can degrade performance for all sites.
3. **Associate SPNs Early**: Assign bandwidth allocations to SPNs during creation to ensure traffic shaping takes effect immediately.
4. **Use Tags for Organization**: Apply consistent tags to bandwidth allocations for easier filtering and reporting across large deployments.
5. **Monitor Utilization**: Regularly review bandwidth utilization against allocated limits and adjust configurations as traffic patterns change.
