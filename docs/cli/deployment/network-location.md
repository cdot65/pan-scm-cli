# Network Location

Network locations are read-only resources representing available SASE deployment regions with geographic information.

## Show Network Location

```bash
scm show sase network-location [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--value TEXT` | System value of the location (e.g., us-west-1) | No |

### Examples

```bash
# List all network locations
$ scm show sase network-location

# Show a specific location
$ scm show sase network-location --value us-west-1
```

!!! note
    Network locations are read-only. They cannot be created, updated, or deleted.
