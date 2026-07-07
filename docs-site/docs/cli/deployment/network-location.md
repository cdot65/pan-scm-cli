# Network Location

Network locations are read-only resources representing available SASE deployment regions with geographic information. Network location management is read-only through the CLI.

## Show Network Location

Display available SASE network locations.

### Syntax

```bash
scm show sase network-location [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--value TEXT` | System value of the location (e.g., us-west-1) | No |
| `--output, -o [table\|json\|yaml]` | Output format (default: table) | No |
| `--max-results INTEGER` | Maximum number of results to display | No |

### Examples

#### List All Network Locations

```bash
$ scm show sase network-location
---> 100%
Network Locations:
------------------------------------------------------------
Value: us-east-1
  Display: US East
  Continent: North America
------------------------------------------------------------
Value: us-west-1
  Display: US West
  Continent: North America
------------------------------------------------------------
Value: eu-west-1
  Display: EU West
  Continent: Europe
------------------------------------------------------------
```

#### Show a Specific Network Location

```bash
$ scm show sase network-location --value us-west-1
---> 100%
Network Location: us-west-1
  Display: US West
  Continent: North America
```

:::note
Network locations are read-only. They cannot be created, updated, or deleted
through the CLI.
:::
