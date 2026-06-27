# Configuration Objects

The `scm` CLI provides a consistent interface for managing configuration objects in Strata Cloud Manager. This guide explains the object categories, common operations, and how objects relate to each other.

## Overview

Configuration objects are the building blocks of your SCM environment. The CLI allows you to:

- Create and update objects across multiple categories (objects, network, security, deployment)
- Delete objects that are no longer needed
- List and inspect existing objects
- Bulk import objects from YAML files
- Back up objects for migration or disaster recovery

## Prerequisites

Before working with configuration objects, ensure you have:

- The `scm` CLI installed and authenticated (see [Getting Started](getting-started.md))
- Appropriate permissions for the target SCM folders
- An understanding of which object types your workflow requires

## Core Concepts

### Object Categories

The CLI organizes configuration management commands into logical categories:

| Category | Description | Example Resources |
| --- | --- | --- |
| `object` | Network objects | Address, address group, application, service, tag |
| `network` | Network configurations | Security zone |
| `security` | Security policies | Security rule, anti-spyware profile, decryption profile |
| `deployment` | Deployment settings | Bandwidth allocation |

### Command Pattern

All object commands follow a consistent pattern:

```bash
scm <action> <category> <object> [OPTIONS]
```

### Object Relationships

Configuration objects often have dependencies. For example:

- Address groups reference address objects
- Security rules reference zones, address objects, and address groups
- Service groups reference service objects

:::warning
When creating objects, ensure that any referenced objects already exist.
Creating an address group that references a nonexistent address will fail.
:::

## Examples

### Objects Category

#### Address Objects

```bash
$ scm set object address \
    --folder Shared \
    --name web-server \
    --ip-netmask 10.1.1.10/32
---> 100%
Created address: web-server in folder Shared
```

```bash
$ scm delete object address --folder Shared --name web-server
---> 100%
Deleted address: web-server from folder Shared
```

```bash
$ scm load object address --folder Shared --file addresses.yaml
---> 100%
✓ Loaded address: web-server-1
✓ Loaded address: web-server-2

Successfully loaded 2 out of 2 addresses from 'addresses.yaml'
```

#### Address Groups

```bash
$ scm set object address-group \
    --folder Shared \
    --name web-servers \
    --static \
    --members "web-server-1,web-server-2"
---> 100%
Created address-group: web-servers in folder Shared
```

```bash
$ scm delete object address-group --folder Shared --name web-servers
---> 100%
Deleted address-group: web-servers from folder Shared
```

```bash
$ scm load object address-group --folder Shared --file address-groups.yaml
---> 100%
✓ Loaded address-group: web-servers
✓ Loaded address-group: db-servers

Successfully loaded 2 out of 2 address-groups from 'address-groups.yaml'
```

### Network Category

#### Security Zones

```bash
$ scm set network security-zone \
    --folder Shared \
    --name Trust \
    --mode layer3
---> 100%
Created security-zone: Trust in folder Shared
```

```bash
$ scm delete network security-zone --folder Shared --name Trust
---> 100%
Deleted security-zone: Trust from folder Shared
```

```bash
$ scm load network security-zone --folder Shared --file security-zones.yaml
---> 100%
✓ Loaded security-zone: Trust
✓ Loaded security-zone: Untrust

Successfully loaded 2 out of 2 security-zones from 'security-zones.yaml'
```

### Security Category

#### Security Rules

```bash
$ scm set security rule \
    --folder Shared \
    --name "Allow-Web" \
    --source-zones Trust \
    --destination-zones Untrust
---> 100%
Created security rule: Allow-Web in folder Shared
```

```bash
$ scm delete security rule --folder Shared --name "Allow-Web"
---> 100%
Deleted security rule: Allow-Web from folder Shared
```

```bash
$ scm load security rule --folder Shared --file security-rules.yaml
---> 100%
✓ Loaded security rule: Allow-Web
✓ Loaded security rule: Block-Malware

Successfully loaded 2 out of 2 security rules from 'security-rules.yaml'
```

### Deployment Category

#### Bandwidth Allocation

```bash
$ scm set deployment bandwidth \
    --folder Shared \
    --name "Standard-Branch" \
    --egress-guaranteed 50 \
    --egress-max 100
---> 100%
Created bandwidth: Standard-Branch in folder Shared
```

```bash
$ scm delete deployment bandwidth --folder Shared --name "Standard-Branch"
---> 100%
Deleted bandwidth: Standard-Branch from folder Shared
```

```bash
$ scm load deployment bandwidth --folder Shared --file bandwidth-allocations.yaml
---> 100%
✓ Loaded bandwidth: Standard-Branch
✓ Loaded bandwidth: Premium-Branch

Successfully loaded 2 out of 2 bandwidth allocations from 'bandwidth-allocations.yaml'
```

### Common Operations

#### Creating Objects

Every object type has a `set` command with required and optional parameters:

```bash
$ scm set object address \
    --folder Shared \
    --name web-server \
    --ip-netmask 10.1.1.10/32 \
    --description "Web server" \
    --tags "web,production"
---> 100%
Created address: web-server in folder Shared
```

#### Updating Objects

Updating uses the same `set` command. The CLI updates the object if it already exists:

```bash
$ scm set object address \
    --folder Shared \
    --name web-server \
    --ip-netmask 10.1.1.20/32 \
    --description "Updated web server"
---> 100%
Updated address: web-server in folder Shared
```

#### Listing Objects

List objects using the `show` command:

```bash
$ scm show object address --folder Shared
---> 100%
Addresses in folder 'Shared':
------------------------------------------------------------
Name: web-server-1
  IP Netmask: 10.1.1.10/32
------------------------------------------------------------
Name: web-server-2
  IP Netmask: 10.1.1.11/32
------------------------------------------------------------
```

#### Bulk Operations

Load multiple objects from YAML files:

```bash
$ scm load object address --folder Shared --file addresses.yaml
---> 100%
✓ Loaded address: web-server-1
✓ Loaded address: web-server-2

Successfully loaded 2 out of 2 addresses from 'addresses.yaml'
```

### Building Object Dependencies

Create objects in the correct order to satisfy dependencies:

```bash
# First create the address objects
$ scm set object address \
    --folder Shared \
    --name web-server-1 \
    --ip-netmask 10.1.1.10/32
---> 100%
Created address: web-server-1 in folder Shared

$ scm set object address \
    --folder Shared \
    --name web-server-2 \
    --ip-netmask 10.1.1.11/32
---> 100%
Created address: web-server-2 in folder Shared

# Then create an address group that references them
$ scm set object address-group \
    --folder Shared \
    --name web-servers \
    --static \
    --members "web-server-1,web-server-2"
---> 100%
Created address-group: web-servers in folder Shared
```

## Best Practices

1. **Create dependencies first**: Always create referenced objects before the objects that reference them (e.g., addresses before address groups).
2. **Use YAML for complex setups**: Bulk loading from YAML files ensures consistency and is easier to maintain in version control.
3. **Validate with mock mode**: Use `--mock` to test commands before making changes to production.
4. **Use descriptive names**: Choose clear, meaningful names for objects to make policies easier to understand.
5. **Organize by folder**: Use SCM folders to logically separate objects by environment or location.

## Next Steps

- See the [CLI Reference](../cli/index.md) for detailed command documentation on each object type:
    - [Address Objects](../cli/objects/address.md)
    - [Address Groups](../cli/objects/address-group.md)
    - [Security Zones](../cli/network/security-zone.md)
    - [Security Rules](../cli/security/rules.md)
    - [Bandwidth Allocation](../cli/deployment/bandwidth.md)
- Learn about [Data Formats](data-models.md) for YAML file structures
- Review [Advanced CLI Topics](advanced-topics.md) for automation workflows
