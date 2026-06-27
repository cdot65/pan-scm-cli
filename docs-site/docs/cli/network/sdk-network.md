# SDK Network Objects

This document lists all network-related configuration object classes provided by the Python SDK (`scm.config.network`) and the standard methods you can use to perform **C**reate, **R**ead, **U**pdate and **D**elete (CRUD) operations.

As with deployment and object classes, every class exposes a _consistent_ interface.

> **Tip** After making changes use `commit()` and track the resulting job with `get_job_status()` / `list_jobs()`.

## Quick-reference table

| Object               | SDK Class                               | Description                         | Create     | Read                         | Update     | Delete     | Commit     |
| -------------------- | --------------------------------------- | ----------------------------------- | ---------- | ---------------------------- | ---------- | ---------- | ---------- |
| IKE Crypto Profile   | `scm.config.network.IKECryptoProfile`   | Manage IKE Crypto Profile objects   | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| IKE Gateway          | `scm.config.network.IKEGateway`         | Manage IKE Gateway objects          | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| IPsec Crypto Profile | `scm.config.network.IPsecCryptoProfile` | Manage IPsec Crypto Profile objects | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| NAT Rule             | `scm.config.network.NatRule`            | Manage NAT Rule objects             | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Security Zone        | `scm.config.network.SecurityZone`       | Manage Security Zone objects        | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |

---

## Usage pattern

```python
from scm.config.network import SecurityZone  # choose the class you need

# Create
resp = SecurityZone.create(name="Trust", type="layer3", subnets=["10.0.0.0/24"])
SecurityZone.commit()

# Read
zone = SecurityZone.get(resp.id)
zones = SecurityZone.list(page_size=50)

# Update
SecurityZone.update(resp.id, description="Updated description")
SecurityZone.commit()

# Delete
SecurityZone.delete(resp.id)
SecurityZone.commit()
```

### Monitoring jobs

```python
status = SecurityZone.get_job_status(job_id)
all_jobs = SecurityZone.list_jobs(limit=10)
```

---

## Object details

### IKE Crypto Profile (`IKECryptoProfile`)

Define phase-1 encryption / hashing parameters.

### IKE Gateway (`IKEGateway`)

Configure IKE gateway peers and authentication.

### IPsec Crypto Profile (`IPsecCryptoProfile`)

Define phase-2 (IPsec) encryption / hashing parameters.

### NAT Rule (`NatRule`)

Layer-3 NAT rules for traffic translation.

### Security Zone (`SecurityZone`)

Logical zones used in security policy.

---

## Related Pydantic data-models

For each class there are corresponding models in `scm.models.network.*` (e.g. `SecurityZoneCreateModel`, `IKEGatewayModel`, …) that validate inputs and SDK responses.

---

_Last generated: 2025-06-11_
