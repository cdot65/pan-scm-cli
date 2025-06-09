# Address Groups

Address groups are collections of address objects that can be referenced in security policies, NAT rules, and other configurations. The `scm` CLI provides commands to create, update, delete, and load address groups.

## Address Group Types

The CLI supports two types of address groups:

| Type    | Description                                  | Example Use Case                     |
| ------- | -------------------------------------------- | ------------------------------------ |
| Static  | Fixed list of address objects                | Group of web servers                 |
| Dynamic | Members determined by filter criteria (tags) | Endpoints matching security criteria |

## Set Address Group

Create or update an address group.

### Syntax

```bash
scm set object address-group [OPTIONS]
```

### Options

| Option               | Description                                    | Required              |
| -------------------- | ---------------------------------------------- | --------------------- |
| `--folder TEXT`      | Folder for the address group                   | Yes                   |
| `--name TEXT`        | Name of the address group                      | Yes                   |
| `--description TEXT` | Description for the address group              | No                    |
| `--tags LIST`        | List of tags to apply to the address group     | No                    |
| `--static`           | Create a static address group                  | No\*                  |
| `--dynamic`          | Create a dynamic address group                 | No\*                  |
| `--members LIST`     | List of address objects for static groups      | Only with `--static`  |
| `--filter TEXT`      | Tag-based filter expression for dynamic groups | Only with `--dynamic` |

\* You must specify exactly one of `--static` or `--dynamic`.

### Examples

#### Create a Static Address Group

```bash
$ scm set object address-group --folder Shared --name web-servers --static --members "web-server-1,web-server-2"
Creating address group 'web-servers' in folder 'Shared'...
Address group created successfully.
```

#### Create a Dynamic Address Group

```bash
$ scm set object address-group --folder Shared --name trusted-endpoints --dynamic --filter "'trusted-endpoint' and 'corporate-asset'"
Creating address group 'trusted-endpoints' in folder 'Shared'...
Address group created successfully.
```

## Delete Address Group

Delete an address group.

### Syntax

```bash
scm delete object address-group [OPTIONS]
```

### Options

| Option          | Description                         | Required |
| --------------- | ----------------------------------- | -------- |
| `--folder TEXT` | Folder containing the address group | Yes      |
| `--name TEXT`   | Name of the address group to delete | Yes      |

### Example

```bash
$ scm delete object address-group --folder Shared --name web-servers
Deleting address group 'web-servers' from folder 'Shared'...
Address group deleted successfully.
```

## Load Address Groups

Create or update multiple address groups from a YAML file.

### Syntax

```bash
scm load object address-group [OPTIONS]
```

### Options

| Option          | Description                                            | Required |
| --------------- | ------------------------------------------------------ | -------- |
| `--folder TEXT` | Folder for the address groups                          | Yes      |
| `--file TEXT`   | Path to YAML file containing address group definitions | Yes      |

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

```bash
$ scm load object address-group --folder Shared --file address-groups.yaml
Loading address groups from 'address-groups.yaml' into folder 'Shared'...
Created 2 address groups successfully.
```

## Show Address Groups

Display address group objects.

### Syntax

```bash
scm show object address-group [OPTIONS]
```

### Options

| Option          | Description                         | Required |
| --------------- | ----------------------------------- | -------- |
| `--folder TEXT` | Folder containing the address group | Yes      |
| `--name TEXT`   | Name of the address group to show   | No       |

\* If --name is not specified, all items will be listed.

### Examples

#### Show Specific Address Group

```bash
$ scm show object address-group --folder Texas --name web-servers
Address Group: web-servers
Location: Folder 'Texas'
Type: static
Description: Group of web servers
Members (2):
  - web-server-1
  - web-server-2
Tags: web, servers
ID: 123e4567-e89b-12d3-a456-426614174001
```

#### List All Address Groups (Default Behavior)

```bash
$ scm show object address-group --folder Texas
Address Groups in folder 'Texas':
------------------------------------------------------------
Name: web-servers
  Location: Folder 'Texas'
  Type: static
  Members: web-server-1, web-server-2
  Description: Group of web servers
  Tags: web, servers
------------------------------------------------------------
Name: trusted-endpoints
  Location: Folder 'Texas'
  Type: dynamic
  Filter: 'trusted-endpoint' and 'corporate-asset'
  Description: Dynamic group for trusted corporate endpoints
  Tags: endpoints, trusted
------------------------------------------------------------
```

## Backup Address Groups

Backup all address groups from a specified location to a YAML file.

### Syntax

```bash
scm backup object address-group [OPTIONS]
```

### Options

| Option           | Description                                  | Required |
| ---------------- | -------------------------------------------- | -------- |
| `--folder TEXT`  | Folder to backup address groups from         | No\*     |
| `--snippet TEXT` | Snippet to backup address groups from        | No\*     |
| `--device TEXT`  | Device to backup address groups from         | No\*     |
| `--file TEXT`    | Output filename (defaults to auto-generated) | No       |

\* You must specify exactly one of --folder, --snippet, or --device.

### Examples

#### Backup from Folder

```bash
$ scm backup object address-group --folder Texas
Successfully backed up 12 address groups to address-group_folder_texas_20240115_120530.yaml
```

#### Backup with Custom Filename

```bash
$ scm backup object address-group --folder Texas --file texas-groups.yaml
Successfully backed up 12 address groups to texas-groups.yaml
```
