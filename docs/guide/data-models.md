# Working with Data Formats

The Strata Cloud Manager CLI handles data validation and formatting internally, but it's important to understand the expected data formats for various commands, especially when working with bulk operations.

## Command Parameters

Each CLI command accepts specific parameters in appropriate formats:

### String Parameters

Most simple parameters are provided as strings:

```bash
# Name, description, and folder are string parameters
scm-cli set objects address --name "web-server" --description "Web server in DMZ" --folder "Shared"
```

### Boolean Parameters

Boolean parameters can be specified as `true` or `false`:

```bash
# Disabled is a boolean parameter
scm-cli set security rule --name "Allow-Web" --folder "Shared" --disabled false
```

### List Parameters

Lists can be provided as comma-separated values:

```bash
# Tags is a list parameter
scm-cli set objects address --name "web-server" --folder "Shared" --tags "web,dmz,production"
```

### Object Parameters

Some complex parameters might require structured input. In these cases, you'll typically use the YAML file loading feature.

## YAML File Formats

The CLI's `load` commands allow you to provide data in YAML files for bulk operations. Each resource type has an expected YAML structure.

### Address Objects

```yaml
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

### Address Groups

```yaml
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

### Security Zones

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
```

### Security Rules

```yaml
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

### Bandwidth Allocation

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
```

## Data Validation

The CLI performs validation on input data:

1. **Command-line parameters** are validated immediately when you run the command
2. **YAML files** are validated when processed by `load` commands
3. **Relationships** between objects are checked (e.g., referenced objects must exist)

If validation fails, the CLI will display an error message explaining the issue.

### Common Validation Rules

- **Names** must be unique within their scope
- **IP addresses** must be in valid formats
- **References** to other objects must point to existing objects
- **Required fields** must be provided
- **Exclusive fields** (where only one can be specified) are enforced

## Best Practices

1. **Use YAML files for complex or bulk operations** - This provides better structure and maintainability
2. **Keep YAML files in version control** - Track changes to your configurations
3. **Validate YAML** - Use the `--mock` flag to validate without making changes
4. **Check command help** - Use `--help` with any command to see required parameters and formats

## Next Steps

- Explore the [CLI Reference](../cli/index.md) for detailed command formats
- Learn about [Advanced CLI Topics](advanced-topics.md) for scripting and automation
- Review [Configuration Objects](configuration-objects.md) for understanding what objects you can manage
