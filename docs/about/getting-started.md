# Getting Started with pan-scm-cli

Welcome to the `pan-scm-cli`! This guide will walk you through the initial setup and basic usage of the CLI tool to interact with Palo Alto Networks Strata Cloud Manager.

## Installation

**Requirements**:

- Python 3.10 or higher

Install the package via pip:

```bash
$ pip install pan-scm-cli
---> 100%
Successfully installed pan-scm-cli
```

## Authentication Setup

The SCM CLI uses dynaconf to manage authentication credentials. You have the following options for authentication:

---

### Credential Precedence: How SCM CLI Loads Credentials

The SCM CLI loads authentication credentials in the following order (highest to lowest priority):

1. **Environment Variables** (`SCM_CLIENT_ID`, `SCM_CLIENT_SECRET`, `SCM_TSG_ID`)
2. **Local Config Files** in the current working directory (`settings.yaml`, `.secrets.yaml`)
3. **User Config File** at `~/.scm-cli/config.yaml`

> **Note:**
>
> - If a credential is set in multiple places, the one with the highest priority is used.
> - Environment variables always override config file values.
> - If a value is missing from higher-priority sources, the CLI will look for it in the next source.

**Example:**

- If you set `SCM_CLIENT_ID` as an environment variable, it will be used even if your `.secrets.yaml` or `~/.scm-cli/config.yaml` files have different values.
- If `.secrets.yaml` is present in your current directory, it will override `~/.scm-cli/config.yaml` for any values it contains.

---

### Option 1: Using Local .secrets.yaml (Recommended for Development)

> **⚠️ SECURITY WARNING**
>
> Storage of credentials in files poses security risks. Consider these best practices:
>
> - **NEVER commit credential files to version control**
> - **Use environment variables for production environments**
> - **Protect local credential files with appropriate file permissions**
> - **Regularly rotate your credentials**

For local development, follow these steps:

```bash
# Step 1: Copy the example configuration file
$ cp example-config.yaml .secrets.yaml

# Step 2: Edit the .secrets.yaml file with your credentials
$ nano .secrets.yaml

# Step 3: Secure the file with restrictive permissions
$ chmod 600 .secrets.yaml
```

> **Note**: The `.secrets.yaml` file is excluded from version control in `.gitignore` to prevent accidental exposure of credentials. For team environments, each developer should maintain their own local configuration and credentials.

Your `.secrets.yaml` file should look like this:

```yaml
default:
  scm_client_id: "your_client_id"
  scm_client_secret: "your_client_secret"
  scm_tsg_id: "your_tenant_service_group_id"
```

Run the CLI from the same directory where `.secrets.yaml` is located. Dynaconf will automatically load credentials from this file.

> **Note**: The `.secrets.yaml` file is excluded from version control in `.gitignore` to prevent accidental exposure of credentials. For team environments, each developer should maintain their own local configuration and credentials.

### Option 2: Environment Variables

For production use or scripting, set environment variables:

```bash
export SCM_CLIENT_ID="your_client_id"
export SCM_CLIENT_SECRET="your_client_secret"
export SCM_TSG_ID="your_tsg_id"
```

> **Note**: Environment variables are not included in version control. Each developer should set their own environment variables.

These environment variables will be automatically detected by dynaconf and used for authentication.

## Command Structure

All commands in `pan-scm-cli` follow this basic structure:

```bash
scm <action> <resource-type> <resource> [options]
```

Where:

- `<action>`: The operation to perform (set, delete, load)
- `<resource-type>`: The category of resource (objects, deployment, network, security)
- `<resource>`: The specific resource type (address, address-group, zone, etc.)
- `[options]`: Resource-specific parameters and global options

## Basic Usage Examples

### Getting Help

You can get help for any command by using the `--help` flag:

```bash
$ scm --help
Usage: scm [OPTIONS] COMMAND [ARGS]...

  Command-line interface for Palo Alto Networks Strata Cloud Manager.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  delete  Delete resources from SCM
  load    Load resources from files
  set     Set/configure resources in SCM
```

Command-specific help:

```bash
$ scm set objects address --help
Usage: scm set objects address [OPTIONS]

  Create or update an address object in SCM.

Options:
  --folder TEXT            Folder for the address object  [required]
  --name TEXT              Name of the address object  [required]
  --description TEXT       Description for the address
  --tags LIST              List of tags to apply to the address
  --ip-netmask TEXT        Address in CIDR notation (e.g., 192.168.1.0/24)
  --ip-range TEXT          Address range (e.g., 192.168.1.1-192.168.1.10)
  --ip-wildcard TEXT       Address with wildcard mask (e.g., 10.20.1.0/0.0.248.255)
  --fqdn TEXT              Fully qualified domain name (e.g., example.com)
  --help                   Show this message and exit.
```

### Working with Address Objects

### Creating an Address Object

```bash
$ scm set objects address \
    --folder Texas \
    --name webserver \
    --ip-netmask 192.168.1.100/32 \
    --description "Web server" \
    --tags ["server", "web"]
---> 100%
Created address: webserver in folder Texas
```

### Creating an Address with FQDN

```bash
$ scm set objects address \
    --folder Texas \
    --name company-website \
    --fqdn example.com \
    --description "Company website"
---> 100%
Created address: company-website in folder Texas
```

### Listing Address Objects

```bash
$ scm list objects address --folder Texas
---> 100%
+----------------+---------------+------------------+
| Name           | Type          | Value            |
+----------------+---------------+------------------+
| webserver      | ip-netmask    | 192.168.1.100/32 |
| company-website| fqdn          | example.com      |
| database       | ip-netmask    | 192.168.2.50/32  |
+----------------+---------------+------------------+
```

### Deleting an Address Object

```bash
$ scm delete objects address --folder Texas --name webserver
---> 100%
Deleted address: webserver from folder Texas
```

### Bulk Operations with YAML Files

### Loading Multiple Address Objects

Create a YAML file with multiple address definitions:

```bash
$ cat > addresses.yml << EOF
---
folder: Texas
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
EOF
```

Then load the addresses from the file:

```bash
$ scm load objects address --file addresses.yml
---> 100%
Loading addresses from addresses.yml
Applied address: web-server-1 in folder Texas
Applied address: web-server-2 in folder Texas
Applied address: database-server in folder Texas
Successfully applied 3 address objects
```

### Advanced Usage

### Using Dry Run Mode

Test changes without applying them:

```bash
$ scm set objects address \
    --folder Texas \
    --name webserver \
    --ip-netmask 192.168.1.100/32 \
    --dry-run
---> 100%
[DRY RUN] Would create address: webserver in folder Texas
```

### Using Mock Mode for Testing

Run commands without connecting to the SCM API:

```bash
$ export SCM_MOCK_MODE=true
$ scm set objects address \
    --folder Texas \
    --name webserver \
    --ip-netmask 192.168.1.100/32
---> 100%
[MOCK] Created address: webserver in folder Texas
```

## Next Steps

Now that you're familiar with the basics of using `pan-scm-cli`, you can:

1. Check out the CLI Reference for a complete list of commands and options
2. Learn about Address Objects and their implementation
3. Explore Security Rules for managing security policies
