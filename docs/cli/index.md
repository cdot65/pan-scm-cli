# CLI Reference

The `pan-scm` command-line interface is organized into a logical structure that makes it easy to manage resources in Strata Cloud Manager.

## Command Structure

All commands follow this pattern:

```bash
scm <action> <resource-type> <resource> [options]
```

Where:

- `<action>`: The operation to perform (set, delete, load)
- `<resource-type>`: Category of resource (objects, deployment, network, security)
- `<resource>`: Specific resource type (address, address-group, zone, etc.)
- `[options]`: Resource-specific parameters and global options

## Available Commands

### Objects

Commands for managing configuration objects:

> **Note:** Bulk operations (`load`, `backup`) use YAML files. See individual object docs for file formats.

| Command                                                                                      | Description                                   |
| -------------------------------------------------------------------------------------------- | --------------------------------------------- |
| [`scm set objects address`](objects/address.md)                                              | Create or update an address object            |
| [`scm delete objects address`](objects/address.md#delete-address)                            | Delete an address object                      |
| [`scm load objects address`](objects/address.md#load-addresses)                              | Bulk import address objects from YAML         |
| [`scm show objects address`](objects/address.md#show-address)                                | Show/list address objects                     |
| [`scm backup objects address`](objects/address.md#backup-addresses)                          | Backup address objects to YAML                |
| [`scm set objects address-group`](objects/address-group.md)                                  | Create or update an address group             |
| [`scm delete objects address-group`](objects/address-group.md#delete-address-group)          | Delete an address group                       |
| [`scm load objects address-group`](objects/address-group.md#load-address-groups)             | Bulk import address groups from YAML          |
| [`scm show objects address-group`](objects/address-group.md#show-address-group)              | Show/list address groups                      |
| [`scm backup objects address-group`](objects/address-group.md#backup-address-groups)         | Backup address groups to YAML                 |
| [`scm set objects application`](objects/application.md)                                      | Create or update an application               |
| [`scm delete objects application`](objects/application.md#delete-application)                | Delete an application                         |
| [`scm load objects application`](objects/application.md#load-applications)                   | Bulk import applications from YAML            |
| [`scm show objects application`](objects/application.md#show-application)                    | Show/list applications                        |
| [`scm backup objects application`](objects/application.md#backup-applications)               | Backup applications to YAML                   |
| [`scm set objects application-group`](objects/application-group.md)                          | Create or update an application group         |
| [`scm delete objects application-group`](objects/application-group.md#delete-app-group)      | Delete an application group                   |
| [`scm load objects application-group`](objects/application-group.md#load-app-groups)         | Bulk import application groups from YAML      |
| [`scm show objects application-group`](objects/application-group.md#show-app-group)          | Show/list application groups                  |
| [`scm backup objects application-group`](objects/application-group.md#backup-app-groups)     | Backup application groups to YAML             |
| [`scm set objects application-filter`](objects/application-filter.md)                        | Create or update an application filter        |
| [`scm delete objects application-filter`](objects/application-filter.md#delete-app-filter)   | Delete an application filter                  |
| [`scm load objects application-filter`](objects/application-filter.md#load-app-filters)      | Bulk import application filters from YAML     |
| [`scm show objects application-filter`](objects/application-filter.md#show-app-filter)       | Show/list application filters                 |
| [`scm backup objects application-filter`](objects/application-filter.md#backup-app-filters)  | Backup application filters to YAML            |
| [`scm set objects dynamic-user-group`](objects/dynamic-user-group.md)                        | Create or update a dynamic user group         |
| [`scm delete objects dynamic-user-group`](objects/dynamic-user-group.md#delete-dug)          | Delete a dynamic user group                   |
| [`scm load objects dynamic-user-group`](objects/dynamic-user-group.md#load-dugs)             | Bulk import dynamic user groups from YAML     |
| [`scm show objects dynamic-user-group`](objects/dynamic-user-group.md#show-dug)              | Show/list dynamic user groups                 |
| [`scm backup objects dynamic-user-group`](objects/dynamic-user-group.md#backup-dugs)         | Backup dynamic user groups to YAML            |
| [`scm set objects external-dynamic-list`](objects/external-dynamic-list.md)                  | Create or update an external dynamic list     |
| [`scm delete objects external-dynamic-list`](objects/external-dynamic-list.md#delete-edl)    | Delete an external dynamic list               |
| [`scm load objects external-dynamic-list`](objects/external-dynamic-list.md#load-edls)       | Bulk import external dynamic lists from YAML  |
| [`scm show objects external-dynamic-list`](objects/external-dynamic-list.md#show-edl)        | Show/list external dynamic lists              |
| [`scm backup objects external-dynamic-list`](objects/external-dynamic-list.md#backup-edls)   | Backup external dynamic lists to YAML         |
| [`scm set objects hip-object`](objects/hip-object.md)                                        | Create or update a HIP object                 |
| [`scm delete objects hip-object`](objects/hip-object.md#delete-hip-object)                   | Delete a HIP object                           |
| [`scm load objects hip-object`](objects/hip-object.md#load-hip-objects)                      | Bulk import HIP objects from YAML             |
| [`scm show objects hip-object`](objects/hip-object.md#show-hip-object)                       | Show/list HIP objects                         |
| [`scm backup objects hip-object`](objects/hip-object.md#backup-hip-objects)                  | Backup HIP objects to YAML                    |
| [`scm set objects hip-profile`](objects/hip-profile.md)                                      | Create or update a HIP profile                |
| [`scm delete objects hip-profile`](objects/hip-profile.md#delete-hip-profile)                | Delete a HIP profile                          |
| [`scm load objects hip-profile`](objects/hip-profile.md#load-hip-profiles)                   | Bulk import HIP profiles from YAML            |
| [`scm show objects hip-profile`](objects/hip-profile.md#show-hip-profile)                    | Show/list HIP profiles                        |
| [`scm backup objects hip-profile`](objects/hip-profile.md#backup-hip-profiles)               | Backup HIP profiles to YAML                   |
| [`scm set objects http-server-profile`](objects/http-server-profile.md)                      | Create or update an HTTP server profile       |
| [`scm delete objects http-server-profile`](objects/http-server-profile.md#delete-http)       | Delete an HTTP server profile                 |
| [`scm load objects http-server-profile`](objects/http-server-profile.md#load-http)           | Bulk import HTTP server profiles from YAML    |
| [`scm show objects http-server-profile`](objects/http-server-profile.md#show-http)           | Show/list HTTP server profiles                |
| [`scm backup objects http-server-profile`](objects/http-server-profile.md#backup-http)       | Backup HTTP server profiles to YAML           |
| [`scm set objects log-forwarding-profile`](objects/log-forwarding-profile.md)                | Create or update a log forwarding profile     |
| [`scm delete objects log-forwarding-profile`](objects/log-forwarding-profile.md#delete-log)  | Delete a log forwarding profile               |
| [`scm load objects log-forwarding-profile`](objects/log-forwarding-profile.md#load-log)      | Bulk import log forwarding profiles from YAML |
| [`scm show objects log-forwarding-profile`](objects/log-forwarding-profile.md#show-log)      | Show/list log forwarding profiles             |
| [`scm backup objects log-forwarding-profile`](objects/log-forwarding-profile.md#backup-log)  | Backup log forwarding profiles to YAML        |
| [`scm set objects service`](objects/service.md)                                              | Create or update a service                    |
| [`scm delete objects service`](objects/service.md#delete-service)                            | Delete a service                              |
| [`scm load objects service`](objects/service.md#load-services)                               | Bulk import services from YAML                |
| [`scm show objects service`](objects/service.md#show-service)                                | Show/list services                            |
| [`scm backup objects service`](objects/service.md#backup-services)                           | Backup services to YAML                       |
| [`scm set objects service-group`](objects/service-group.md)                                  | Create or update a service group              |
| [`scm delete objects service-group`](objects/service-group.md#delete-service-group)          | Delete a service group                        |
| [`scm load objects service-group`](objects/service-group.md#load-service-groups)             | Bulk import service groups from YAML          |
| [`scm show objects service-group`](objects/service-group.md#show-service-group)              | Show/list service groups                      |
| [`scm backup objects service-group`](objects/service-group.md#backup-service-groups)         | Backup service groups to YAML                 |
| [`scm set objects syslog-server-profile`](objects/syslog-server-profile.md)                  | Create or update a syslog server profile      |
| [`scm delete objects syslog-server-profile`](objects/syslog-server-profile.md#delete-syslog) | Delete a syslog server profile                |
| [`scm load objects syslog-server-profile`](objects/syslog-server-profile.md#load-syslog)     | Bulk import syslog server profiles from YAML  |
| [`scm show objects syslog-server-profile`](objects/syslog-server-profile.md#show-syslog)     | Show/list syslog server profiles              |
| [`scm backup objects syslog-server-profile`](objects/syslog-server-profile.md#backup-syslog) | Backup syslog server profiles to YAML         |
| [`scm set objects tag`](objects/tag.md)                                                      | Create or update a tag                        |
| [`scm delete objects tag`](objects/tag.md#delete-tag)                                        | Delete a tag                                  |
| [`scm load objects tag`](objects/tag.md#load-tags)                                           | Bulk import tags from YAML                    |
| [`scm show objects tag`](objects/tag.md#show-tag)                                            | Show/list tags                                |
| [`scm backup objects tag`](objects/tag.md#backup-tags)                                       | Backup tags to YAML                           |

### Security

Commands for managing security policies:

| Command                                                                | Description                          |
| ---------------------------------------------------------------------- | ------------------------------------ |
| [`scm set security rule`](security/rules.md)                           | Create or update a security rule     |
| [`scm delete security rule`](security/rules.md#delete-security-rule)   | Delete a security rule               |
| [`scm load security rule`](security/rules.md#load-security-rules)      | Bulk import security rules from YAML |
| [`scm set security rule --move`](security/rules.md#move-security-rule) | Move a security rule position        |

### Network

Commands for managing network configurations:

| Command                                                                             | Description                          |
| ----------------------------------------------------------------------------------- | ------------------------------------ |
| [`scm set network security-zone`](network/security-zone.md)                         | Create or update a security zone     |
| [`scm delete network security-zone`](network/security-zone.md#delete-security-zone) | Delete a security zone               |
| [`scm load network security-zone`](network/security-zone.md#load-security-zones)    | Bulk import security zones from YAML |

### Deployment

Commands for managing deployment configurations:

| Command                                                                                        | Description                                 |
| ---------------------------------------------------------------------------------------------- | ------------------------------------------- |
| [`scm set deployment bandwidth`](deployment/bandwidth.md)                                      | Create or update bandwidth allocation       |
| [`scm delete deployment bandwidth`](deployment/bandwidth.md#delete-bandwidth-allocation)       | Delete a bandwidth allocation               |
| [`scm load deployment bandwidth`](deployment/bandwidth.md#load-bandwidth-allocations)          | Bulk import bandwidth allocations from YAML |
| [`scm set deployment bandwidth --assign`](deployment/bandwidth.md#assign-bandwidth-allocation) | Assign bandwidth allocation to SPNs         |

## Global Options

Options that apply to all commands:

| Option      | Description                                  |
| ----------- | -------------------------------------------- |
| `--help`    | Show help message for any command            |
| `--version` | Show the CLI version information             |
| `--verbose` | Enable verbose output for additional details |
| `--mock`    | Run in mock mode (no actual API connections) |

## Working with the CLI

For more detailed examples and use cases, refer to the specific command documentation linked above or see the [Getting Started](../about/getting-started.md) guide.
