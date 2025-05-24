# SCM CLI Examples

This directory contains example YAML configuration files for use with the SCM CLI tool.

## Available Examples

### Basic Configuration Examples

- `addresses.yml` - Example address objects across different folders
- `address-groups.yml` - Static and dynamic address group examples
- `security-zones.yml` - Various security zone configurations
- `security-rules.yml` - Pre and post rulebase security rules
- `bandwidth-allocations.yml` - Bandwidth allocation examples

### Special Use Cases

#### RFC 1918 Private Networks

Create all RFC 1918 private network address objects and groups:

```bash
# Step 1: Create the RFC 1918 address objects
scm-cli load objects address --file examples/rfc1918-addresses.yml

# Step 2: Create the address groups containing these objects
scm-cli load objects address-group --file examples/rfc1918-address-group.yml

# Or use the complete file to create just the addresses
scm-cli load objects address --file examples/rfc1918-complete.yml
```

The RFC 1918 examples create:

- `rfc1918-10-0-0-0-8` - Class A private network (10.0.0.0/8)
- `rfc1918-172-16-0-0-12` - Class B private network (172.16.0.0/12)
- `rfc1918-192-168-0-0-16` - Class C private network (192.168.0.0/16)
- `rfc1918-all-private-networks` - Address group containing all three ranges

## Usage Tips

1. **Always use --dry-run first** to preview changes:

   ```bash
   scm-cli load objects address --file examples/addresses.yml --dry-run
   ```

2. **Check dependencies** - Some configurations depend on others:

   - Address groups require their member addresses to exist first
   - Security rules may reference address objects, groups, and zones

3. **Folder structure** - Examples use three folders:

   - `ngfw-shared` - Shared/global configurations
   - `Texas` - Texas region configurations
   - `Austin` - Austin office configurations

4. **Backup before changes** - Export existing configurations:

   ```bash
   scm-cli backup objects address --folder ngfw-shared
   ```

## Customization

Feel free to modify these examples for your environment:

1. Change folder names to match your hierarchy
2. Update IP ranges and names to fit your network
3. Adjust tags for your organizational standards
4. Modify descriptions for clarity

## Loading Order

When setting up a new environment, load configurations in this order:

1. Addresses
2. Address Groups
3. Security Zones
4. Security Rules
5. Bandwidth Allocations

Example workflow:

```bash
# Load all address objects
scm-cli load objects address --file examples/addresses.yml

# Load address groups (which reference the addresses)
scm-cli load objects address-group --file examples/address-groups.yml

# Load security zones
scm-cli load network security-zone --file examples/security-zones.yml

# Load security rules (which reference zones and addresses)
scm-cli load security rule --file examples/security-rules.yml

# Load bandwidth allocations
scm-cli load deployment bandwidth-allocation --file examples/bandwidth-allocations.yml
```
