# CLI Reference

The `pan-scm-cli` command-line interface provides a structured set of commands for managing resources in Palo Alto Networks Strata Cloud Manager.

## Command Structure

All commands follow this pattern:

```bash
scm <action> <category> <resource> [options]
```

| Component | Description | Examples |
| --- | --- | --- |
| `<action>` | Operation to perform | `set`, `delete`, `load`, `show`, `backup` |
| `<category>` | Category of resource | `object`, `network`, `security`, `sase` |
| `<resource>` | Specific resource type | `address`, `security-zone`, `rule` |
| `[options]` | Resource-specific parameters | `--folder`, `--name`, `--file` |

:::note
All `show` commands default to listing all items when no `--name` parameter
is provided.
:::

## Objects

Commands for managing configuration objects.

| Resource | Page | Operations |
| --- | --- | --- |
| Address | [address](objects/address.md) | set, delete, load, show, backup |
| Address Group | [address-group](objects/address-group.md) | set, delete, load, show, backup |
| Application | [application](objects/application.md) | set, delete, load, show, backup |
| Application Filter | [application-filter](objects/application-filter.md) | set, delete, load, show, backup |
| Application Group | [application-group](objects/application-group.md) | set, delete, load, show, backup |
| Dynamic User Group | [dynamic-user-group](objects/dynamic-user-group.md) | set, delete, load, show, backup |
| External Dynamic List | [external-dynamic-list](objects/external-dynamic-list.md) | set, delete, load, show, backup |
| HIP Object | [hip-object](objects/hip-object.md) | set, delete, load, show, backup |
| HIP Profile | [hip-profile](objects/hip-profile.md) | set, delete, load, show, backup |
| HTTP Server Profile | [http-server-profile](objects/http-server-profile.md) | set, delete, load, show, backup |
| Log Forwarding Profile | [log-forwarding-profile](objects/log-forwarding-profile.md) | set, delete, load, show, backup |
| Quarantined Device | [quarantined-device](objects/quarantined-device.md) | show |
| Region | [region](objects/region.md) | show |
| Schedule | [schedule](objects/schedule.md) | show |
| Service | [service](objects/service.md) | set, delete, load, show, backup |
| Service Group | [service-group](objects/service-group.md) | set, delete, load, show, backup |
| Syslog Server Profile | [syslog-server-profile](objects/syslog-server-profile.md) | set, delete, load, show, backup |
| Tag | [tag](objects/tag.md) | set, delete, load, show, backup |

:::tip
Bulk operations (`load`, `backup`) use YAML files. See individual resource
pages for file format details.
:::

## Security

Commands for managing security policies and profiles.

| Resource | Page | Operations |
| --- | --- | --- |
| Security Rule | [rule](security/rules.md) | set, delete, load, show |
| Anti-Spyware Profile | [anti-spyware-profile](security/anti-spyware-profile.md) | set, delete, load, show, backup |
| App Override Rule | [app-override-rule](security/app-override-rule.md) | show |
| Authentication Rule | [authentication-rule](security/authentication-rule.md) | show |
| Decryption Profile | [decryption-profile](security/decryption-profile.md) | set, delete, load, show, backup |
| Decryption Rule | [decryption-rule](security/decryption-rule.md) | show |
| DNS Security Profile | [dns-security-profile](security/dns-security-profile.md) | show |
| URL Access Profile | [url-access-profile](security/url-access-profile.md) | show |
| URL Category | [url-category](security/url-category.md) | show |
| Vulnerability Protection Profile | [vulnerability-protection-profile](security/vulnerability-protection-profile.md) | show |
| Wildfire Antivirus Profile | [wildfire-antivirus-profile](security/wildfire-antivirus-profile.md) | show |

## Network

Commands for managing network configurations.

| Resource | Page | Operations |
| --- | --- | --- |
| Security Zone | [security-zone](network/security-zone.md) | set, delete, load, show, backup |
| Aggregate Interface | [aggregate-interface](network/aggregate-interface.md) | show |
| BGP Address Family Profile | [bgp-address-family-profile](network/bgp-address-family-profile.md) | show |
| BGP Auth Profile | [bgp-auth-profile](network/bgp-auth-profile.md) | show |
| BGP Filtering Profile | [bgp-filtering-profile](network/bgp-filtering-profile.md) | show |
| BGP Redistribution Profile | [bgp-redistribution-profile](network/bgp-redistribution-profile.md) | show |
| BGP Route Map | [bgp-route-map](network/bgp-route-map.md) | show |
| BGP Route Map Redistribution | [bgp-route-map-redistribution](network/bgp-route-map-redistribution.md) | show |
| DHCP Interface | [dhcp-interface](network/dhcp-interface.md) | show |
| Ethernet Interface | [ethernet-interface](network/ethernet-interface.md) | show |
| IKE Crypto Profile | [ike-crypto-profile](network/ike-crypto-profile.md) | show |
| IKE Gateway | [ike-gateway](network/ike-gateway.md) | show |
| IPsec Crypto Profile | [ipsec-crypto-profile](network/ipsec-crypto-profile.md) | show |
| Layer2 Subinterface | [layer2-subinterface](network/layer2-subinterface.md) | show |
| Layer3 Subinterface | [layer3-subinterface](network/layer3-subinterface.md) | show |
| Loopback Interface | [loopback-interface](network/loopback-interface.md) | show |
| NAT Rule | [nat-rule](network/nat-rule.md) | show |
| OSPF Auth Profile | [ospf-auth-profile](network/ospf-auth-profile.md) | show |
| Route Access List | [route-access-list](network/route-access-list.md) | show |
| Route Prefix List | [route-prefix-list](network/route-prefix-list.md) | show |
| Tunnel Interface | [tunnel-interface](network/tunnel-interface.md) | show |
| VLAN Interface | [vlan-interface](network/vlan-interface.md) | show |

## SASE / Deployment

Commands for managing SASE deployment configurations.

| Resource | Page | Operations |
| --- | --- | --- |
| Bandwidth Allocation | [bandwidth](deployment/bandwidth.md) | set, delete, load, show |
| BGP Routing | [bgp-routing](deployment/bgp-routing.md) | show |
| Internal DNS Server | [internal-dns-server](deployment/internal-dns-server.md) | show |
| Network Location | [network-location](deployment/network-location.md) | show |
| Remote Network | [remote-network](deployment/remote-network.md) | set, delete, load, show, backup |
| Service Connection | [service-connection](deployment/service-connection.md) | set, delete, load, show, backup |

## Identity

Commands for managing identity and authentication configurations.

| Resource | Page | Operations |
| --- | --- | --- |
| Authentication Profile | [authentication-profile](identity/authentication-profile.md) | show |
| Kerberos Server Profile | [kerberos-server-profile](identity/kerberos-server-profile.md) | show |
| LDAP Server Profile | [ldap-server-profile](identity/ldap-server-profile.md) | show |
| RADIUS Server Profile | [radius-server-profile](identity/radius-server-profile.md) | show |
| SAML Server Profile | [saml-server-profile](identity/saml-server-profile.md) | show |
| TACACS Server Profile | [tacacs-server-profile](identity/tacacs-server-profile.md) | show |

## Mobile Agent

Commands for managing GlobalProtect mobile agent configurations.

| Resource | Page | Operations |
| --- | --- | --- |
| Agent Version | [agent-version](mobile-agent/agent-version.md) | show |
| Auth Setting | [auth-setting](mobile-agent/auth-setting.md) | show |

## Setup

Commands for managing setup and organizational configurations.

| Resource | Page | Operations |
| --- | --- | --- |
| Device | [device](setup/device.md) | show |
| Folder | [folder](setup/folder.md) | show |
| Label | [label](setup/label.md) | show |
| Snippet | [snippet](setup/snippet.md) | show |
| Variable | [variable](setup/variable.md) | show |

## Operational Commands

| Command | Page | Description |
| --- | --- | --- |
| Commit | [commit](commit.md) | Push candidate configurations to running |
| Jobs | [jobs](jobs.md) | Monitor and manage configuration jobs |
| Insights | [insights](insights.md) | Query SASE health and connectivity data |
| Context | [context](../about/getting-started.md#option-1-contexts-recommended) | Manage authentication contexts |

## Global Options

Options that apply to all commands:

| Option | Description |
| --- | --- |
| `--help` | Show help message for any command |
| `--version` | Show the CLI version information |
| `--verbose` | Enable verbose output for additional details |
| `--mock` | Run in mock mode without API connections |

## Related Topics

- [Getting Started](../about/getting-started.md) for initial setup and basic usage
- [Installation](../about/installation.md) for setup instructions
- [Troubleshooting](../about/troubleshooting.md) for common issues and solutions
