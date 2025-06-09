# CLI Reference

The `pan-scm-cli` command-line interface is organized into a logical structure that makes it easy to manage resources in Strata Cloud Manager.

## Command Structure

All commands follow this pattern:

```bash
scm <action> <resource-type> <resource> [options]
```

Where:

- `<action>`: The operation to perform (set, delete, load, show, backup)
- `<resource-type>`: Category of resource (objects, deployment, network, security)
- `<resource>`: Specific resource type (address, address-group, zone, etc.)
- `[options]`: Resource-specific parameters and global options

!!! note "Show Command Default Behavior"
All `show` commands default to listing all items when no `--name` parameter is provided. The `--list` flag has been removed entirely for a more intuitive experience.

## Available Commands

### Objects

Commands for managing configuration objects:

> **Note:** Bulk operations (`load`, `backup`) use YAML files. See individual object docs for file formats.

| Command                                                                                      | Description                                   |
| -------------------------------------------------------------------------------------------- | --------------------------------------------- |
| [`scm set object address`](objects/address.md)                                              | Create or update an address object            |
| [`scm delete object address`](objects/address.md#delete-address)                            | Delete an address object                      |
| [`scm load object address`](objects/address.md#load-addresses)                              | Bulk import address objects from YAML         |
| [`scm show object address`](objects/address.md#show-address)                                | Show/list address objects                     |
| [`scm backup object address`](objects/address.md#backup-addresses)                          | Backup address objects to YAML                |
| [`scm set object address-group`](objects/address-group.md)                                  | Create or update an address group             |
| [`scm delete object address-group`](objects/address-group.md#delete-address-group)          | Delete an address group                       |
| [`scm load object address-group`](objects/address-group.md#load-address-groups)             | Bulk import address groups from YAML          |
| [`scm show object address-group`](objects/address-group.md#show-address-groups)             | Show/list address groups                      |
| [`scm backup object address-group`](objects/address-group.md#backup-address-groups)         | Backup address groups to YAML                 |
| [`scm set object application`](objects/application.md)                                      | Create or update an application               |
| [`scm delete object application`](objects/application.md#delete-application)                | Delete an application                         |
| [`scm load object application`](objects/application.md#load-applications)                   | Bulk import applications from YAML            |
| [`scm show object application`](objects/application.md#show-application)                    | Show/list applications                        |
| [`scm backup object application`](objects/application.md#backup-applications)               | Backup applications to YAML                   |
| [`scm set object application-group`](objects/application-group.md)                          | Create or update an application group         |
| [`scm delete object application-group`](objects/application-group.md#delete-application-group) | Delete an application group                   |
| [`scm load object application-group`](objects/application-group.md#load-application-groups)    | Bulk import application groups from YAML      |
| [`scm show object application-group`](objects/application-group.md#show-application-group)     | Show/list application groups                  |
| [`scm backup object application-group`](objects/application-group.md#backup-application-groups) | Backup application groups to YAML             |
| [`scm set object application-filter`](objects/application-filter.md)                        | Create or update an application filter        |
| [`scm delete object application-filter`](objects/application-filter.md#delete-application-filter)   | Delete an application filter                  |
| [`scm load object application-filter`](objects/application-filter.md#load-application-filters)      | Bulk import application filters from YAML     |
| [`scm show object application-filter`](objects/application-filter.md#show-application-filter)       | Show/list application filters                 |
| [`scm backup object application-filter`](objects/application-filter.md#backup-application-filters)  | Backup application filters to YAML            |
| [`scm set object dynamic-user-group`](objects/dynamic-user-group.md)                        | Create or update a dynamic user group         |
| [`scm delete object dynamic-user-group`](objects/dynamic-user-group.md#delete-dynamic-user-group)          | Delete a dynamic user group                   |
| [`scm load object dynamic-user-group`](objects/dynamic-user-group.md#load-dynamic-user-groups)             | Bulk import dynamic user groups from YAML     |
| [`scm show object dynamic-user-group`](objects/dynamic-user-group.md#show-dynamic-user-group)              | Show/list dynamic user groups                 |
| [`scm backup object dynamic-user-group`](objects/dynamic-user-group.md#backup-dynamic-user-groups)         | Backup dynamic user groups to YAML            |
| [`scm set object external-dynamic-list`](objects/external-dynamic-list.md)                  | Create or update an external dynamic list     |
| [`scm delete object external-dynamic-list`](objects/external-dynamic-list.md#delete-external-dynamic-list)    | Delete an external dynamic list               |
| [`scm load object external-dynamic-list`](objects/external-dynamic-list.md#load-external-dynamic-lists)       | Bulk import external dynamic lists from YAML  |
| [`scm show object external-dynamic-list`](objects/external-dynamic-list.md#show-external-dynamic-list)        | Show/list external dynamic lists              |
| [`scm backup object external-dynamic-list`](objects/external-dynamic-list.md#backup-external-dynamic-lists)   | Backup external dynamic lists to YAML         |
| [`scm set object hip-object`](objects/hip-object.md)                                        | Create or update a HIP object                 |
| [`scm delete object hip-object`](objects/hip-object.md#delete-hip-object)                   | Delete a HIP object                           |
| [`scm load object hip-object`](objects/hip-object.md#load-hip-objects)                      | Bulk import HIP objects from YAML             |
| [`scm show object hip-object`](objects/hip-object.md#show-hip-object)                       | Show/list HIP objects                         |
| [`scm backup object hip-object`](objects/hip-object.md#backup-hip-objects)                  | Backup HIP objects to YAML                    |
| [`scm set object hip-profile`](objects/hip-profile.md)                                      | Create or update a HIP profile                |
| [`scm delete object hip-profile`](objects/hip-profile.md#delete-hip-profile)                | Delete a HIP profile                          |
| [`scm load object hip-profile`](objects/hip-profile.md#load-hip-profiles)                   | Bulk import HIP profiles from YAML            |
| [`scm show object hip-profile`](objects/hip-profile.md#show-hip-profile)                    | Show/list HIP profiles                        |
| [`scm backup object hip-profile`](objects/hip-profile.md#backup-hip-profiles)               | Backup HIP profiles to YAML                   |
| [`scm set object http-server-profile`](objects/http-server-profile.md)                      | Create or update an HTTP server profile       |
| [`scm delete object http-server-profile`](objects/http-server-profile.md#delete-http-server-profile)       | Delete an HTTP server profile                 |
| [`scm load object http-server-profile`](objects/http-server-profile.md#load-http-server-profiles)           | Bulk import HTTP server profiles from YAML    |
| [`scm show object http-server-profile`](objects/http-server-profile.md#show-http-server-profile)           | Show/list HTTP server profiles                |
| [`scm backup object http-server-profile`](objects/http-server-profile.md#backup-http-server-profiles)       | Backup HTTP server profiles to YAML           |
| [`scm set object log-forwarding-profile`](objects/log-forwarding-profile.md)                | Create or update a log forwarding profile     |
| [`scm delete object log-forwarding-profile`](objects/log-forwarding-profile.md#delete-log-forwarding-profile)  | Delete a log forwarding profile               |
| [`scm load object log-forwarding-profile`](objects/log-forwarding-profile.md#load-log-forwarding-profiles)      | Bulk import log forwarding profiles from YAML |
| [`scm show object log-forwarding-profile`](objects/log-forwarding-profile.md#show-log-forwarding-profile)      | Show/list log forwarding profiles             |
| [`scm backup object log-forwarding-profile`](objects/log-forwarding-profile.md#backup-log-forwarding-profiles)  | Backup log forwarding profiles to YAML        |
| [`scm set object service`](objects/service.md)                                              | Create or update a service                    |
| [`scm delete object service`](objects/service.md#deleting-services)                            | Delete a service                              |
| [`scm load object service`](objects/service.md#load-services)                               | Bulk import services from YAML                |
| [`scm show object service`](objects/service.md#showing-service-details)                                | Show/list services                            |
| [`scm backup object service`](objects/service.md#backup-services)                           | Backup services to YAML                       |
| [`scm set object service-group`](objects/service-group.md)                                  | Create or update a service group              |
| [`scm delete object service-group`](objects/service-group.md#deleting-service-groups)          | Delete a service group                        |
| [`scm load object service-group`](objects/service-group.md#load-service-groups)             | Bulk import service groups from YAML          |
| [`scm show object service-group`](objects/service-group.md#showing-service-group-details)              | Show/list service groups                      |
| [`scm backup object service-group`](objects/service-group.md#backup-service-groups)         | Backup service groups to YAML                 |
| [`scm set object syslog-server-profile`](objects/syslog-server-profile.md)                  | Create or update a syslog server profile      |
| [`scm delete object syslog-server-profile`](objects/syslog-server-profile.md#deleting-syslog-server-profiles) | Delete a syslog server profile                |
| [`scm load object syslog-server-profile`](objects/syslog-server-profile.md#load-syslog-server-profiles)     | Bulk import syslog server profiles from YAML  |
| [`scm show object syslog-server-profile`](objects/syslog-server-profile.md#showing-syslog-server-profile-details)     | Show/list syslog server profiles              |
| [`scm backup object syslog-server-profile`](objects/syslog-server-profile.md#backup-syslog-server-profiles) | Backup syslog server profiles to YAML         |
| [`scm set object tag`](objects/tag.md)                                                      | Create or update a tag                        |
| [`scm delete object tag`](objects/tag.md#deleting-tags)                                        | Delete a tag                                  |
| [`scm load object tag`](objects/tag.md#load-tags)                                           | Bulk import tags from YAML                    |
| [`scm show object tag`](objects/tag.md#showing-tag-details)                                            | Show/list tags                                |
| [`scm backup object tag`](objects/tag.md#backup-tags)                                       | Backup tags to YAML                           |

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
