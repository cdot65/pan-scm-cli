# BGP Routing

BGP routing is a singleton configuration that controls backbone routing behavior for SASE deployments.

## Set BGP Routing

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

### Example

```bash
$ scm set sase bgp-routing \
    --backbone-routing no-asymmetric-routing \
    --routing-preference default \
    --accept-route-over-sc
```

## Show BGP Routing

```bash
scm show sase bgp-routing
```

## Delete BGP Routing

Resets BGP routing configuration to defaults.

```bash
scm delete sase bgp-routing
```
