# Introduction

## Overview

The `pan-scm-cli` is a command-line interface tool designed to simplify interactions with Palo Alto Networks Strata Cloud Manager (SCM). It provides a consistent and intuitive way to manage SCM configurations directly from your terminal, allowing for efficient management of security objects and policies.

## Why Use pan-scm-cli?

Manually managing configurations in the SCM web interface can be time-consuming and prone to errors. The CLI provides a streamlined way to automate these tasks, ensuring consistency and efficiency. It's especially valuable for:

- Bulk operations that would be tedious to perform in the web interface
- Integrating SCM management into scripts and automation workflows
- Consistent application of configuration changes across multiple environments

## Key Features

- **Consistent Command Structure**: Standardized command patterns for easy learning and usage
- **Resource Management**: Create, update, delete, and list SCM objects using simple commands
- **Bulk Operations**: Apply configurations from YAML files for efficient batch processing
- **Validated Input**: Built-in validation ensures configurations are properly formatted
- **Error Handling**: Clear error messages to help identify and resolve issues
- **Dry Run Mode**: Preview changes before applying them to your environment

## Command Structure

Commands in `pan-scm-cli` follow a consistent structure:

```
scm-cli <action> <resource-type> <resource> [options]
```

Where:

- `<action>`: The operation to perform (set, delete, load)
- `<resource-type>`: The category of resource (objects, deployment, network, security)
- `<resource>`: The specific resource type (address, address-group, zone, etc.)
- `[options]`: Resource-specific parameters and global options

## Who Should Use This CLI?

- **Network Engineers** looking to automate configuration tasks
- **Security Professionals** managing SCM deployments
- **DevOps Teams** integrating SCM into deployment workflows
- **Automation Engineers** building scripts that interact with SCM

## Getting Help

- **Documentation**: Explore the [CLI Reference](../cli/index.md) for detailed command information
- **GitHub Repository**: Visit the [pan-scm-cli GitHub repository](https://github.com/cdot65/pan-scm-cli) for source code and issue tracking
- **Help Command**: Use `scm-cli --help` or `scm-cli <command> --help` for command-specific assistance

## Next Steps

Proceed to the [Getting Started Guide](getting-started.md) to set up `pan-scm-cli` and begin managing your SCM configurations.
