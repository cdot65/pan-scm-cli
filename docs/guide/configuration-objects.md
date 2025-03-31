# Working with Configuration Objects in the CLI

The `pan-scm-cli` provides a consistent interface for managing various configuration objects in Strata Cloud Manager.

## Object Categories and Commands

The CLI organizes configuration management commands into logical categories:

### Objects

Commands for managing network objects:

```bash
# Address Objects
scm-cli set objects address --folder Shared --name web-server --ip-netmask 10.1.1.10/32
scm-cli delete objects address --folder Shared --name web-server
scm-cli load objects address --folder Shared --file addresses.yaml

# Address Groups
scm-cli set objects address-group --folder Shared --name web-servers --static --members "web-server-1,web-server-2"
scm-cli delete objects address-group --folder Shared --name web-servers
scm-cli load objects address-group --folder Shared --file address-groups.yaml
```

### Network

Commands for managing network configurations:

```bash
# Security Zones
scm-cli set network security-zone --folder Shared --name Trust --mode layer3
scm-cli delete network security-zone --folder Shared --name Trust
scm-cli load network security-zone --folder Shared --file security-zones.yaml
```

### Security

Commands for managing security policies:

```bash
# Security Rules
scm-cli set security rule --folder Shared --name "Allow-Web" --source-zones Trust --destination-zones Untrust
scm-cli delete security rule --folder Shared --name "Allow-Web"
scm-cli load security rule --folder Shared --file security-rules.yaml
```

### Deployment

Commands for managing deployment settings:

```bash
# Bandwidth Allocation
scm-cli set deployment bandwidth --folder Shared --name "Standard-Branch" --egress-guaranteed 50 --egress-max 100
scm-cli delete deployment bandwidth --folder Shared --name "Standard-Branch"
scm-cli load deployment bandwidth --folder Shared --file bandwidth-allocations.yaml
```

## Common Operations

### Creating Objects

Every object type has a specific `set` command with required and optional parameters:

```bash
scm-cli set objects address --folder Shared --name web-server --ip-netmask 10.1.1.10/32 --description "Web server" --tags "web,production"
```

### Updating Objects

Updating uses the same `set` command as creating. The CLI will update the object if it exists:

```bash
# Update an existing address object
scm-cli set objects address --folder Shared --name web-server --ip-netmask 10.1.1.20/32 --description "Updated web server"
```

### Deleting Objects

Delete objects using the `delete` command:

```bash
scm-cli delete objects address --folder Shared --name web-server
```

### Listing Objects

List objects using the `--list` option with the `set` command:

```bash
scm-cli set objects address --list --folder Shared
```

### Bulk Operations

Load multiple objects from YAML files:

```bash
scm-cli load objects address --folder Shared --file addresses.yaml
```

## Understanding Object Relationships

Configuration objects often have relationships. For example:

- Address Groups reference Address objects
- Security Rules reference Zones, Address objects, and Address Groups

When creating objects, ensure that any referenced objects already exist:

```bash
# First create the address objects
scm-cli set objects address --folder Shared --name web-server-1 --ip-netmask 10.1.1.10/32
scm-cli set objects address --folder Shared --name web-server-2 --ip-netmask 10.1.1.11/32

# Then create an address group that references them
scm-cli set objects address-group --folder Shared --name web-servers --static --members "web-server-1,web-server-2"
```

## Next Steps

For detailed information on specific object types, see the CLI reference documentation:

- [Address Objects](../cli/objects/address.md)
- [Address Groups](../cli/objects/address-group.md)
- [Security Zones](../cli/network/security-zone.md)
- [Security Rules](../cli/security/rules.md)
- [Bandwidth Allocation](../cli/deployment/bandwidth.md)
