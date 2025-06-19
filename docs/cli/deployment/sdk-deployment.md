# SDK Deployment Objects

This document lists all deployment-related configuration object classes provided by the Python SDK (`scm.config.deployment`) and the standard methods you can use to perform **C**reate, **R**ead, **U**pdate and **D**elete (CRUD) operations.

Like the configuration objects, every class exposes a _consistent_ interface, so once you understand one it is straightforward to use the others.

> **Tip** After any create / update / delete you generally finish with `commit()` and (optionally) monitor the returned job with `get_job_status()` or `list_jobs()`.

## Quick-reference table

| Object               | SDK Class                                    | Description                                 | Create     | Read                         | Update     | Delete     | Commit     |
| -------------------- | -------------------------------------------- | ------------------------------------------- | ---------- | ---------------------------- | ---------- | ---------- | ---------- |
| BGP Routing          | `scm.config.deployment.BGPRouting`           | Manage BGP settings for Service Connections | `create()` | `get()`                      | `update()` | `delete()` | `commit()` |
| Bandwidth Allocation | `scm.config.deployment.BandwidthAllocations` | Manage bandwidth allocation objects         | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Internal DNS Server  | `scm.config.deployment.InternalDnsServers`   | Manage internal DNS server objects          | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Network Location     | `scm.config.deployment.NetworkLocations`     | Manage network location objects             | —          | `fetch()`, `list()`          | —          | —          | —          |
| Remote Network       | `scm.config.deployment.RemoteNetworks`       | Manage remote network objects               | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Service Connection   | `scm.config.deployment.ServiceConnection`    | Manage service connection objects           | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |

---

## Usage pattern

All classes follow the same pattern:

```python
from scm.config.deployment import RemoteNetworks  # choose the class you need

# Create
resp = RemoteNetworks.create(name="HQ", subnets=["10.0.0.0/24"], region="us-east-1")
RemoteNetworks.commit()

# Read
obj = RemoteNetworks.get(resp.id)
items = RemoteNetworks.list(page_size=100)

# Update
RemoteNetworks.update(resp.id, description="Updated description")
RemoteNetworks.commit()

# Delete
RemoteNetworks.delete(resp.id)
RemoteNetworks.commit()
```

### Monitoring jobs

```python
status = RemoteNetworks.get_job_status(job_id)
jobs   = RemoteNetworks.list_jobs(limit=20)
```

---

## Object details

### BGP Routing (`BGPRouting`)

Configure and manage BGP routing parameters for Service Connections.

### Bandwidth Allocation (`BandwidthAllocations`)

Define and manage bandwidth allocation policies for tunnels.

### Internal DNS Server (`InternalDnsServers`)

Maintain lists of internal DNS servers to be applied to Remote Networks or Service Connections.

### Network Location (`NetworkLocations`)

Describe network locations for traffic steering and policy.

### Remote Network (`RemoteNetworks`)

Create and manage Remote Network connections.

### Service Connection (`ServiceConnection`)

Configure Service Connections (including routing, redundancy, etc.).

---

## Related Pydantic data-models

For each deployment-related class there are corresponding models in `scm.models.deployment.*` (e.g. `RemoteNetworkCreateModel`, `BGPRoutingModel`, …) which provide type-safe validation for input parameters and SDK responses.

---

_Last generated: 2025-06-11_
