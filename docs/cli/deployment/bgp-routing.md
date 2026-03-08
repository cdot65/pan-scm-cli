# BGP Routing

BGP routing is a singleton configuration that controls backbone routing behavior for SASE deployments. The `scm` CLI provides commands to configure, view, and reset BGP routing settings.

## Overview

The `bgp-routing` commands allow you to:

- Configure backbone routing mode (symmetric or asymmetric)
- Set routing preferences and outbound route policies
- Enable route acceptance over service connections
- Reset BGP routing configuration to defaults

## Set BGP Routing

Create or update the BGP routing configuration.

### Syntax

```bash
scm set sase bgp-routing [OPTIONS]
```

### Options

| Option | Description | Required |
| --- | --- | --- |
| `--backbone-routing TEXT` | Backbone routing mode (no-asymmetric-routing, asymmetric-routing) | Yes |
| `--routing-preference TEXT` | Routing preference (default, hot_potato_routing) | No |
| `--accept-route-over-sc` | Accept routes over service connections | No |
| `--outbound-routes TEXT` | Comma-separated outbound routes for services | No |
| `--add-host-route-to-ike-peer` | Add host route to IKE peer | No |
| `--withdraw-static-route` | Withdraw static routes | No |

### Examples

#### Configure Basic BGP Routing

```bash
$ scm set sase bgp-routing \
    --backbone-routing no-asymmetric-routing \
    --routing-preference default
---> 100%
Updated BGP routing configuration
```

#### Configure BGP Routing with Service Connection Routes

```bash
$ scm set sase bgp-routing \
    --backbone-routing no-asymmetric-routing \
    --routing-preference default \
    --accept-route-over-sc \
    --add-host-route-to-ike-peer
---> 100%
Updated BGP routing configuration
```

#### Configure Asymmetric Routing with Outbound Routes

```bash
$ scm set sase bgp-routing \
    --backbone-routing asymmetric-routing \
    --outbound-routes "10.0.0.0/8,172.16.0.0/12" \
    --withdraw-static-route
---> 100%
Updated BGP routing configuration
```

## Delete BGP Routing

Reset BGP routing configuration to defaults.

### Syntax

```bash
scm delete sase bgp-routing
```

### Example

```bash
$ scm delete sase bgp-routing
---> 100%
Reset BGP routing configuration to defaults
```

## Show BGP Routing

Display the current BGP routing configuration.

### Syntax

```bash
scm show sase bgp-routing
```

### Example

```bash
$ scm show sase bgp-routing
---> 100%
BGP Routing Configuration:
  Backbone Routing: no-asymmetric-routing
  Routing Preference: default
  Accept Route Over SC: true
  Add Host Route to IKE Peer: true
  Withdraw Static Route: false
```

## Best Practices

1. **Use Symmetric Routing by Default**: Start with `no-asymmetric-routing` to ensure predictable traffic paths and simplify troubleshooting.
2. **Enable Service Connection Routes Carefully**: Only enable `--accept-route-over-sc` when you need dynamic route exchange over service connections.
3. **Plan Outbound Routes**: Document all outbound routes before configuring them to avoid unintended traffic flows through the SASE backbone.
4. **Test Before Production**: Use `scm show sase bgp-routing` to verify configuration changes before committing them to production.
