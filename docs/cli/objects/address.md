# Address Objects

Address objects are used to identify network addresses in security policies, NAT rules, and other configurations. The `pan-scm-cli` provides commands to create, update, delete, and load address objects.

## Address Types

The CLI supports four types of address objects:

| Type | Format | Example |
|------|--------|---------|
| IP Netmask | IP address with CIDR notation | `192.168.1.0/24` |
| IP Range | Range of IP addresses | `192.168.1.1-192.168.1.10` |
| IP Wildcard | IP with wildcard mask | `10.20.1.0/0.0.248.255` |
| FQDN | Fully qualified domain name | `example.com` |

!!! note
    You can only specify one address type per address object.

## Set Address

Create or update an address object.

### Syntax

```
scm-cli set objects address [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--folder TEXT` | Folder for the address object | Yes |
| `--name TEXT` | Name of the address object | Yes |
| `--description TEXT` | Description for the address | No |
| `--tags LIST` | List of tags to apply to the address | No |
| `--ip-netmask TEXT` | Address in CIDR notation | No* |
| `--ip-range TEXT` | Address range | No* |
| `--ip-wildcard TEXT` | Address with wildcard mask | No* |
| `--fqdn TEXT` | Fully qualified domain name | No* |

\* You must specify exactly one of the address type options.

### Examples

#### Create an IP Netmask Address

<div class="termy">

<!-- termynal -->

```console
$ scm-cli set objects address \
    --folder Texas \
    --name webserver \
    --ip-netmask 192.168.1.100/32 \
    --description "Web server" \
    --tags ["server", "web"]
---> 100%
Created address: webserver in folder Texas
```

</div>

#### Create an FQDN Address

<div class="termy">

<!-- termynal -->

```console
$ scm-cli set objects address \
    --folder Texas \
    --name company-website \
    --fqdn example.com \
    --description "Company website"
---> 100%
Created address: company-website in folder Texas
```

</div>

#### Create an IP Range Address

<div class="termy">

<!-- termynal -->

```console
$ scm-cli set objects address \
    --folder Texas \
    --name dhcp-pool \
    --ip-range 192.168.1.100-192.168.1.200 \
    --description "DHCP address pool"
---> 100%
Created address: dhcp-pool in folder Texas
```

</div>

## Delete Address

Delete an address object from SCM.

### Syntax

```
scm-cli delete objects address [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--folder TEXT` | Folder containing the address object | Yes |
| `--name TEXT` | Name of the address object to delete | Yes |

### Example

<div class="termy">

<!-- termynal -->

```console
$ scm-cli delete objects address --folder Texas --name webserver
---> 100%
Deleted address: webserver from folder Texas
```

</div>

## Load Addresses

Load multiple address objects from a YAML file.

### Syntax

```
scm-cli load objects address [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--file TEXT` | Path to YAML file containing address definitions | Yes |
| `--dry-run` | Preview changes without applying them | No |

### YAML File Format

```yaml
---
folder: Texas  # Target folder for all addresses
addresses:
  - name: web-server-1
    description: "Web Server 1"
    ip_netmask: 192.168.1.10/32
    tags:
      - web
      - production

  - name: web-server-2
    description: "Web Server 2"
    ip_netmask: 192.168.1.11/32
    tags:
      - web
      - production

  - name: database-server
    description: "Database Server"
    ip_netmask: 192.168.2.10/32
    tags:
      - database
      - production

  - name: company-website
    description: "Company Website"
    fqdn: example.com
    tags:
      - web
      - external
```

### Example

<div class="termy">

<!-- termynal -->

```console
$ scm-cli load objects address --file addresses.yml
---> 100%
Loading addresses from addresses.yml
Applied address: web-server-1 in folder Texas
Applied address: web-server-2 in folder Texas
Applied address: database-server in folder Texas
Applied address: company-website in folder Texas
Successfully applied 4 address objects
```

</div>

## Get Address

Retrieve a specific address object.

### Syntax

```
scm-cli get objects address [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--folder TEXT` | Folder containing the address object | Yes |
| `--name TEXT` | Name of the address object to retrieve | Yes |
| `--output` | Output format (text, json, table) | No |

### Example

<div class="termy">

<!-- termynal -->

```console
$ scm-cli get objects address --folder Texas --name webserver --output json
---> 100%
{
  "name": "webserver",
  "folder": "Texas",
  "ip_netmask": "192.168.1.100/32",
  "description": "Web server",
  "tags": ["server", "web"]
}
```

</div>

## List Addresses

List all address objects in a folder.

### Syntax

```
scm-cli list objects address [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--folder TEXT` | Folder to list addresses from | Yes |
| `--output` | Output format (text, json, table) | No |

### Example

<div class="termy">

<!-- termynal -->

```console
$ scm-cli list objects address --folder Texas
---> 100%
+----------------+---------------+------------------+
| Name           | Type          | Value            |
+----------------+---------------+------------------+
| webserver      | ip-netmask    | 192.168.1.100/32 |
| company-website| fqdn          | example.com      |
| dhcp-pool      | ip-range      | 192.168.1.100-200|
| database       | ip-netmask    | 192.168.2.50/32  |
+----------------+---------------+------------------+
```

</div>

## Best Practices

1. **Use Descriptive Names**: Choose clear, descriptive names for address objects
2. **Add Descriptions**: Always include a description to document the purpose of each address
3. **Apply Tags**: Use tags to categorize addresses for easier management and policy creation
4. **Use YAML for Bulk Operations**: For large deployments, use YAML files to manage address objects
5. **Validate First**: Use the `--dry-run` option to preview changes before applying them
6. **Organize by Folder**: Keep address objects organized in logical folders
