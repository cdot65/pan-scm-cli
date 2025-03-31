# Address Groups

Address groups are collections of address objects that can be referenced in security policies, NAT rules, and other configurations. The `pan-scm-cli` provides commands to create, update, delete, and load address groups.

## Address Group Types

The CLI supports two types of address groups:

| Type | Description | Example Use Case |
|------|-------------|------------------|
| Static | Fixed list of address objects | Group of web servers |
| Dynamic | Members determined by filter criteria (tags) | Endpoints matching security criteria |

## Set Address Group

Create or update an address group.

### Syntax

```
scm-cli set objects address-group [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--folder TEXT` | Folder for the address group | Yes |
| `--name TEXT` | Name of the address group | Yes |
| `--description TEXT` | Description for the address group | No |
| `--tags LIST` | List of tags to apply to the address group | No |
| `--static` | Create a static address group | No* |
| `--dynamic` | Create a dynamic address group | No* |
| `--members LIST` | List of address objects for static groups | Only with `--static` |
| `--filter TEXT` | Tag-based filter expression for dynamic groups | Only with `--dynamic` |

\* You must specify exactly one of `--static` or `--dynamic`.

### Examples

#### Create a Static Address Group

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects address-group --folder Shared --name web-servers --static --members "web-server-1,web-server-2"
Creating address group 'web-servers' in folder 'Shared'...
Address group created successfully.
```

</div>

#### Create a Dynamic Address Group

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects address-group --folder Shared --name trusted-endpoints --dynamic --filter "'trusted-endpoint' and 'corporate-asset'"
Creating address group 'trusted-endpoints' in folder 'Shared'...
Address group created successfully.
```

</div>

## Delete Address Group

Delete an address group.

### Syntax

```
scm-cli delete objects address-group [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--folder TEXT` | Folder containing the address group | Yes |
| `--name TEXT` | Name of the address group to delete | Yes |

### Example

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli delete objects address-group --folder Shared --name web-servers
Deleting address group 'web-servers' from folder 'Shared'...
Address group deleted successfully.
```

</div>

## Load Address Groups

Create or update multiple address groups from a YAML file.

### Syntax

```
scm-cli load objects address-group [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--folder TEXT` | Folder for the address groups | Yes |
| `--file TEXT` | Path to YAML file containing address group definitions | Yes |

### Example YAML File

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

  - name: trusted-endpoints
    description: "Dynamic group for trusted corporate endpoints"
    type: dynamic
    filter: "'trusted-endpoint' and 'corporate-asset'"
    tags:
      - endpoints
      - trusted
```

### Example Command

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli load objects address-group --folder Shared --file address-groups.yaml
Loading address groups from 'address-groups.yaml' into folder 'Shared'...
Created 2 address groups successfully.
```

</div>

## List Address Groups

List all address groups in a folder.

### Syntax

```
scm-cli set objects address-group --list [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--folder TEXT` | Folder to list address groups from | Yes |

### Example

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects address-group --list --folder Shared
Listing address groups in folder 'Shared'...

| Name            | Type    | Description                        | Members/Filter                            |
|-----------------|---------|------------------------------------|--------------------------------------------|
| web-servers     | Static  | Group of web servers               | web-server-1, web-server-2                |
| trusted-endpoints | Dynamic | Dynamic group for trusted endpoints | 'trusted-endpoint' and 'corporate-asset' |
```

</div>
