---
hide:
  - navigation
---

<style>
.md-content .md-typeset h1 { display: none; }
</style>

<p align="center">
    <a href="https://paloaltonetworks.com"><img src="images/logo.svg" alt="PaloAltoNetworks"></a>
</p>
<p align="center">
    <em><code>pan-scm-cli</code>: Command-line interface for managing Palo Alto Networks Strata Cloud Manager configurations</em>
</p>
<p align="center">
<a href="https://github.com/cdot65/pan-scm-cli/graphs/contributors" target="_blank">
    <img src="https://img.shields.io/github/contributors/cdot65/pan-scm-cli.svg?style=for-the-badge" alt="Contributors">
</a>
<a href="https://github.com/cdot65/pan-scm-cli/network/members" target="_blank">
    <img src="https://img.shields.io/github/forks/cdot65/pan-scm-cli.svg?style=for-the-badge" alt="Forks">
</a>
<a href="https://github.com/cdot65/pan-scm-cli/stargazers" target="_blank">
    <img src="https://img.shields.io/github/stars/cdot65/pan-scm-cli.svg?style=for-the-badge" alt="Stars">
</a>
<a href="https://github.com/cdot65/pan-scm-cli/issues" target="_blank">
    <img src="https://img.shields.io/github/issues/cdot65/pan-scm-cli.svg?style=for-the-badge" alt="Issues">
</a>
<a href="https://github.com/cdot65/pan-scm-cli/blob/main/LICENSE" target="_blank">
    <img src="https://img.shields.io/github/license/cdot65/pan-scm-cli.svg?style=for-the-badge" alt="License">
</a>
</p>

---

**Documentation**: <a href="https://cdot65.github.io/pan-scm-cli/" target="_blank">https://cdot65.github.io/pan-scm-cli/</a>

**Source Code**: <a href="https://github.com/cdot65/pan-scm-cli" target="_blank">https://github.com/cdot65/pan-scm-cli</a>

---

`pan-scm-cli` is a command-line interface tool for managing Palo Alto Networks Strata Cloud Manager configurations.

## Installation

**Requirements**:

- Python 3.10 or higher

```bash
$ pip install pan-scm-cli
---> 100%
Successfully installed pan-scm-cli
```

## Key Features

- **Intuitive CLI Structure**: Standardized command structure for easy learning and usage
- **Resource Management**: Create, update, and delete SCM objects using simple commands
- **Bulk Operations**: Apply configurations from YAML files for efficient batch processing
- **Validated Input**: Built-in validation ensures configurations are properly formatted
- **Consistent Output**: Standardized output format for all operations
- **Error Handling**: Clear error messages to help identify and resolve issues
- **Dry Run Mode**: Preview changes before applying them to your environment

## Quick Start

### Setting up authentication:

```bash
# Create a context for your SCM tenant
$ scm context create my-tenant \
  --client-id "app@123456789.iam.panserviceaccount.com" \
  --client-secret "your-secret-key" \
  --tsg-id "123456789"
✓ Context 'my-tenant' created successfully
✓ Context 'my-tenant' set as current

# Test the connection
$ scm context test
Testing authentication for context: my-tenant
✓ Authentication successful!
  Client ID: app@123456789.iam.panserviceaccount.com
  TSG ID: 123456789
✓ API connectivity verified (found 25 address objects in Shared folder)
```

### Example: Creating an Address Object

```bash
$ scm set object address \
    --folder Texas \
    --name webserver \
    --ip-netmask 192.168.1.100/32 \
    --description "Web server" \
    --tags ["server", "web"]
[INFO] Using authentication context: my-tenant
Created address: webserver in folder Texas
```

### Example: Deleting an Address Object

```bash
$ scm delete object address --folder Texas --name webserver
---> 100%
Deleted address: webserver from folder Texas
```

### Example: Loading Multiple Objects from YAML

```bash
$ scm load object address --file config/addresses.yml
---> 100%
Loading addresses from config/addresses.yml
Applied address: webserver in folder Texas
Applied address: database in folder Texas
Applied address: loadbalancer in folder Texas
Successfully applied 3 address objects
```

## Command Structure

Commands in pan-scm-cli follow a consistent structure:

```bash
scm <action> <resource-type> <resource> [options]
```

Where:

- `<action>`: The operation to perform (set, delete, load)
- `<resource-type>`: The category of resource (objects, deployment, network, security)
- `<resource>`: The specific resource type (address, address-group, zone, etc.)
- `[options]`: Resource-specific parameters and global options

## Getting Started

To begin using pan-scm-cli, check out the [Getting Started Guide](about/getting-started.md) which covers installation, configuration, and basic usage examples.

For detailed information about each command, refer to the [CLI Reference](cli/index.md) section.

## Contributing

Contributions are welcome and greatly appreciated. Visit the [Contributing](about/contributing.md) page for guidelines
on how to contribute.

## License

This project is licensed under the Apache 2.0 License - see the [License](about/license.md) page for details.
