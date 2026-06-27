# Address Objects

Address objects identify network addresses in security policies, NAT rules, and other configurations. The `scm` CLI provides commands to create, update, delete, and load address objects.

## Overview

The `address` commands allow you to:

- Create and update address objects with various address types
- Delete address objects that are no longer needed
- Bulk import address objects from YAML files
- Export address objects for backup or migration

## Address Types

The CLI supports four types of address objects:

| Type | Format | Example |
| --- | --- | --- |
| IP Netmask | IP address with CIDR notation | `192.168.1.0/24` |
| IP Range | Range of IP addresses | `192.168.1.1-192.168.1.10` |
| IP Wildcard | IP with wildcard mask | `10.20.1.0/0.0.248.255` |
| FQDN | Fully qualified domain name | `example.com` |

:::note
You can only specify one address type per address object.
:::

## Set Address

Create or update an address object.

### Syntax

```bash
scm set object address [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder for the address object | Yes |
| `--name TEXT` | Name of the address object | Yes |
| `--description TEXT` | Description for the address | No |
| `--tags LIST` | List of tags to apply to the address | No |
| `--ip-netmask TEXT` | Address in CIDR notation | No\* |
| `--ip-range TEXT` | Address range | No\* |
| `--ip-wildcard TEXT` | Address with wildcard mask | No\* |
| `--fqdn TEXT` | Fully qualified domain name | No\* |

\* You must specify exactly one of the address type options.

### Examples

#### Create an IP Netmask Address

```bash
$ scm set object address \
    --folder Texas \
    --name webserver \
    --ip-netmask 192.168.1.100/32 \
    --description "Web server" \
    --tags server --tags web
---> 100%
Created address: webserver in folder Texas
```

#### Create an FQDN Address

```bash
$ scm set object address \
    --folder Texas \
    --name company-website \
    --fqdn example.com \
    --description "Company website"
---> 100%
Created address: company-website in folder Texas
```

#### Create an IP Range Address

```bash
$ scm set object address \
    --folder Texas \
    --name dhcp-pool \
    --ip-range 192.168.1.100-192.168.1.200 \
    --description "DHCP address pool"
---> 100%
Created address: dhcp-pool in folder Texas
```

## Delete Address

Delete an address object from SCM.

### Syntax

```bash
scm delete object address [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the address object | Yes |
| `--name TEXT` | Name of the address object to delete | Yes |
| `--force` | Skip confirmation prompt | No |

### Example

```bash
$ scm delete object address --folder Texas --name webserver --force
---> 100%
Deleted address: webserver from folder Texas
```

## Load Addresses

Load multiple address objects from a YAML file.

### Syntax

```bash
scm load object address [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--file TEXT` | Path to YAML file containing address definitions | Yes |
| `--folder TEXT` | Override folder location for all objects | No |
| `--snippet TEXT` | Override snippet location for all objects | No |
| `--device TEXT` | Override device location for all objects | No |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
addresses:
  - name: web-server-1
    folder: Texas
    description: "Web Server 1"
    ip_netmask: 192.168.1.10/32
    tags:
      - web
      - production

  - name: web-server-2
    folder: Texas
    description: "Web Server 2"
    ip_netmask: 192.168.1.11/32
    tags:
      - web
      - production

  - name: company-website
    folder: Texas
    description: "Company Website"
    fqdn: example.com
    tags:
      - web
      - external
```

### Examples

#### Load with Original Locations

```bash
$ scm load object address --file addresses.yml
---> 100%
✓ Loaded address: web-server-1
✓ Loaded address: web-server-2
✓ Loaded address: company-website

Successfully loaded 3 out of 3 addresses from 'addresses.yml'
```

#### Load with Folder Override

```bash
$ scm load object address --file addresses.yml --folder Austin
---> 100%
✓ Loaded address: web-server-1
✓ Loaded address: web-server-2
✓ Loaded address: company-website

Successfully loaded 3 out of 3 addresses from 'addresses.yml'
```

:::note
When using container override options (--folder, --snippet, --device), all addresses
will be loaded into the specified container, ignoring the container specified in the
YAML file.
:::

## Show Address

Display address objects.

### Syntax

```bash
scm show object address [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder containing the address object | Yes |
| `--name TEXT` | Name of the address object to show | No |

:::note
When no `--name` is specified, all items are listed by default.
:::

### Examples

#### Show Specific Address

```bash
$ scm show object address --folder Texas --name webserver
---> 100%
Address: webserver
  Location: Folder 'Texas'
  Description: Web server
  Type: IP/Netmask
  Value: 192.168.1.100/32
  Tags: server, web
  ID: 123e4567-e89b-12d3-a456-426614174000
```

#### List All Addresses (Default Behavior)

```bash
$ scm show object address --folder Texas
---> 100%
Addresses in folder 'Texas':
------------------------------------------------------------
Name: webserver
  Location: Folder 'Texas'
  Description: Web server
  Type: IP/Netmask
  Value: 192.168.1.100/32
  Tags: server, web
------------------------------------------------------------
Name: company-website
  Location: Folder 'Texas'
  Description: Company website
  Type: FQDN
  Value: example.com
  Tags: web, external
------------------------------------------------------------
Name: dhcp-pool
  Location: Folder 'Texas'
  Description: DHCP address pool
  Type: IP Range
  Value: 192.168.1.100-192.168.1.200
------------------------------------------------------------
```

## Backup Addresses

Backup all address objects from a specified location to a YAML file.

### Syntax

```bash
scm backup object address [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--folder TEXT` | Folder to backup addresses from | No\* |
| `--snippet TEXT` | Snippet to backup addresses from | No\* |
| `--device TEXT` | Device to backup addresses from | No\* |
| `--file TEXT` | Output filename (defaults to auto-generated) | No |

\* One of --folder, --snippet, or --device is required.

### Examples

#### Backup from Folder

```bash
$ scm backup object address --folder Texas
---> 100%
Successfully backed up 15 addresses to address_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object address --folder Texas --file texas-addresses.yaml
---> 100%
Successfully backed up 15 addresses to texas-addresses.yaml
```

## Best Practices

1. **Use Descriptive Names**: Choose clear, descriptive names for address objects that indicate their purpose.
2. **Add Descriptions**: Always include a description to document the purpose of each address.
3. **Apply Tags**: Use tags to categorize addresses for easier management and policy creation.
4. **Use YAML for Bulk Operations**: For large deployments, use YAML files to manage address objects.
5. **Validate First**: Use the `--dry-run` option to preview changes before applying them.
6. **Organize by Folder**: Keep address objects organized in logical folders.
