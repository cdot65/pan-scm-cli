# Data Formats

The `scm` CLI handles data validation and formatting internally, but understanding the expected data formats is important when working with command parameters and bulk operations. This guide covers parameter types, YAML file structures, and validation rules.

## Overview

This guide explains the data formats used by the CLI:

- Understand parameter types for command-line input (strings, booleans, lists)
- Write correctly structured YAML files for bulk loading
- Validate input data before submitting to the API
- Troubleshoot common validation errors

## Prerequisites

Before working with data formats, ensure you have:

- The `scm` CLI installed (see [Getting Started](getting-started.md))
- Familiarity with YAML syntax for bulk operations
- An understanding of the object types you plan to manage (see [Configuration Objects](configuration-objects.md))

## Core Concepts

### Parameter Types

CLI commands accept parameters in several formats depending on the field type.

#### String Parameters

Most simple parameters are provided as strings:

```bash
$ scm set object address \
    --name "web-server" \
    --description "Web server in DMZ" \
    --folder "Shared"
---> 100%
Created address: web-server in folder Shared
```

#### Boolean Parameters

Boolean parameters accept `true` or `false`:

```bash
$ scm set security rule \
    --name "Allow-Web" \
    --folder "Shared" \
    --disabled false
---> 100%
Created security rule: Allow-Web in folder Shared
```

#### List Parameters

Lists are provided as comma-separated values:

```bash
$ scm set object address \
    --name "web-server" \
    --folder "Shared" \
    --tags "web,dmz,production"
---> 100%
Created address: web-server in folder Shared
```

#### Object Parameters

Complex parameters with nested structure typically require YAML file loading rather than command-line input.

### YAML Key Naming

YAML files use `snake_case` keys matching the SDK model field names, while CLI flags use `kebab-case`:

| YAML Key | CLI Flag |
| --- | --- |
| `ip_netmask` | `--ip-netmask` |
| `source_zones` | `--source-zones` |
| `enable_user_id` | `--enable-user-id` |

### Data Validation

The CLI performs validation at multiple stages:

1. **Command-line parameters**: Validated immediately when you run the command
2. **YAML files**: Validated when processed by `load` commands
3. **Object relationships**: Referenced objects must exist (e.g., address group members)

## Examples

### YAML File Formats

#### Address Objects

```yaml
---
addresses:
  - name: web-server-1
    description: "Web server 1"
    ip_netmask: 192.168.1.100/32
    tags:
      - web
      - production

  - name: web-server-2
    description: "Web server 2"
    ip_netmask: 192.168.1.101/32
    tags:
      - web
      - production
```

#### Address Groups

```yaml
---
address_groups:
  - name: web-servers
    description: "Group of web servers"
    type: static
    members:
      - web-server-1
      - web-server-2
    tags:
      - web
      - servers

  - name: dynamic-endpoints
    description: "Dynamic group for endpoints"
    type: dynamic
    filter: "'endpoint' and 'corporate'"
    tags:
      - endpoints
```

#### Security Zones

```yaml
---
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
```

#### Security Rules

```yaml
---
security_rules:
  - name: Allow-Internal-Web
    description: "Allow internal users to access web servers"
    source_zones:
      - Trust
    destination_zones:
      - DMZ
    source_addresses:
      - any
    destination_addresses:
      - web-servers
    applications:
      - web-browsing
      - ssl
    services:
      - application-default
    action: allow
    log_end: true
    tags:
      - internal-access
```

#### Bandwidth Allocation

```yaml
---
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
```

### Common Validation Rules

| Rule | Description |
| --- | --- |
| Unique names | Names must be unique within their scope |
| Valid IP formats | IP addresses must use valid CIDR or host notation |
| Valid references | References to other objects must point to existing objects |
| Required fields | All required fields must be provided |
| Exclusive fields | Mutually exclusive fields cannot both be specified |

!!! tip
    Use the `--mock` flag to validate YAML files and command parameters
    without making changes to your SCM environment.

## Best Practices

1. **Use YAML files for complex or bulk operations**: Structured files are easier to maintain and review than long command lines.
2. **Keep YAML files in version control**: Track configuration changes alongside your infrastructure code.
3. **Validate before applying**: Use `--mock` to validate YAML files and commands before making changes.
4. **Check command help for formats**: Use `--help` with any command to see required parameters and accepted formats.
5. **Use `snake_case` in YAML**: Match the SDK model field names exactly when writing YAML files.

## Next Steps

- Explore the [CLI Reference](../cli/index.md) for detailed command formats
- Learn about [Advanced CLI Topics](advanced-topics.md) for scripting and automation
- Review [Configuration Objects](configuration-objects.md) for understanding what objects you can manage
