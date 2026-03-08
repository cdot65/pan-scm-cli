# Introduction

The `pan-scm-cli` is a command-line interface for managing Palo Alto Networks Strata Cloud Manager (SCM) configurations directly from your terminal.

## Overview

The CLI provides a consistent and intuitive way to:

- Create, update, and delete SCM configuration objects with simple commands
- Bulk import configurations from YAML files for efficient batch processing
- Back up existing configurations for migration or disaster recovery
- Validate input before applying changes to your environment
- Preview changes with dry run mode before committing

## Why Use pan-scm-cli?

Manually managing configurations in the SCM web interface can be time-consuming and error-prone. The CLI streamlines these tasks, ensuring consistency and efficiency. It is especially valuable for:

- **Bulk Operations**: Apply hundreds of configuration changes that would be tedious in the web interface
- **Automation Workflows**: Integrate SCM management into CI/CD pipelines and scripts
- **Multi-Environment Consistency**: Apply the same configurations across multiple tenants using contexts
- **Auditability**: Track configuration changes through version-controlled YAML files

## Key Features

- **Consistent Command Structure**: Standardized `scm <action> <category> <resource>` pattern for easy learning
- **Resource Management**: Create, update, delete, and list SCM objects using simple commands
- **Bulk Operations**: Apply configurations from YAML files for efficient batch processing
- **Validated Input**: Built-in Pydantic validation ensures configurations are properly formatted
- **Error Handling**: Clear error messages to help identify and resolve issues
- **Dry Run Mode**: Preview changes before applying them to your environment
- **Mock Mode**: Test commands without connecting to the SCM API

## Command Structure

Commands in `pan-scm-cli` follow a consistent structure:

```bash
scm <action> <category> <resource> [options]
```

Where:

- `<action>`: The operation to perform (`set`, `delete`, `load`, `show`, `backup`)
- `<category>`: The category of resource (`object`, `network`, `security`, `sase`)
- `<resource>`: The specific resource type (`address`, `address-group`, `security-zone`, etc.)
- `[options]`: Resource-specific parameters and global options

## Who Should Use This CLI?

- **Network Engineers** looking to automate configuration tasks
- **Security Professionals** managing SCM deployments
- **DevOps Teams** integrating SCM into deployment workflows
- **Automation Engineers** building scripts that interact with SCM

## Getting Help

- **Documentation**: Explore the [CLI Reference](../cli/index.md) for detailed command information
- **GitHub Repository**: Visit the [pan-scm-cli GitHub repository](https://github.com/cdot65/pan-scm-cli) for source code and issue tracking
- **Help Command**: Use `scm --help` or `scm <command> --help` for command-specific assistance

## Next Steps

Proceed to the [Installation Guide](installation.md) to install `pan-scm-cli`, then follow the [Getting Started Guide](getting-started.md) to begin managing your SCM configurations.
