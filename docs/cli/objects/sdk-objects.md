# SDK Configuration Objects

This document lists all configuration object classes provided by the Python SDK (`scm.config.objects`) and the standard methods you can use to perform **C**reate, **R**ead, **U**pdate and **D**elete (CRUD) operations.  
All object classes expose a _consistent_ interface, so once you understand how to work with one class you can work with any other.

> **Tip** After creating, updating or deleting objects you usually call `commit()` to push the pending configuration to Strata Cloud Manager and optionally track progress with `get_job_status()` / `list_jobs()`.

## Quick-reference table

| Object                 | SDK Class                                 | Description                            | Create     | Read                         | Update     | Delete     | Commit     |
| ---------------------- | ----------------------------------------- | -------------------------------------- | ---------- | ---------------------------- | ---------- | ---------- | ---------- |
| Address                | `scm.config.objects.Address`              | Manages Address objects                | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Address Group          | `scm.config.objects.AddressGroup`         | Manages Address Group objects          | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Application            | `scm.config.objects.Application`          | Manages Application objects            | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Application Filter     | `scm.config.objects.ApplicationFilters`   | Manages Application Filters            | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Application Group      | `scm.config.objects.ApplicationGroup`     | Manages Application Group objects      | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Dynamic User Group     | `scm.config.objects.DynamicUserGroup`     | Manages Dynamic User Group objects     | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| External Dynamic List  | `scm.config.objects.ExternalDynamicLists` | Manages EDL objects                    | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| HIP Object             | `scm.config.objects.HIPObject`            | Manages HIP objects                    | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| HIP Profile            | `scm.config.objects.HIPProfile`           | Manages HIP profiles                   | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| HTTP Server Profile    | `scm.config.objects.HTTPServerProfile`    | Manages HTTP Server Profile objects    | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Log Forwarding Profile | `scm.config.objects.LogForwardingProfile` | Manages Log Forwarding Profile objects | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Quarantined Devices    | `scm.config.objects.QuarantinedDevices`   | Manages Quarantined Device entries     | `create()` | `get()` , `list()`           | `update()` | `delete()` | `commit()` |
| Region                 | `scm.config.objects.Region`               | Manages Region objects                 | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Schedule               | `scm.config.objects.Schedule`             | Manages Schedule objects               | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Service                | `scm.config.objects.Service`              | Manages Service objects                | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Service Group          | `scm.config.objects.ServiceGroup`         | Manages Service Group objects          | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Syslog Server Profile  | `scm.config.objects.SyslogServerProfile`  | Manages Syslog Server Profile objects  | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Tag                    | `scm.config.objects.Tag`                  | Manages Tag objects                    | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |

---

## Usage patterns

Each class follows the same pattern:

```python
from scm.config.objects import Address  # replace with the class you need

# 1) Create
resp = Address.create(name="webserver", folder="Shared", ip_netmask="192.168.1.100/32")
print("Job ID", resp.job_id)
Address.commit()

# 2) Read
obj = Address.get(resp.id)               # or Address.fetch(name="webserver", folder="Shared")
items = Address.list(folder="Shared")   # list many

# 3) Update
Address.update(resp.id, description="Updated description")
Address.commit()

# 4) Delete
Address.delete(resp.id)
Address.commit()
```

### Monitoring jobs

Most write operations (`create`, `update`, `delete`, `commit`) return a **job ID**.  
You can track progress:

```python
status = Address.get_job_status(job_id)
all_jobs = Address.list_jobs(page_size=20)
```

---

## Object details

Below you will find a concise description of each object class and the key methods it implements.

### Address

Manages Address objects (single IP, range, wildcard or FQDN). Typical workflow:

- `create()` → new address object
- `fetch()/get()/list()` → read existing
- `update()` → modify
- `delete()` → remove
- `commit()` → push pending changes

### Address Group

Handles static / dynamic groups of address objects.

### Application

Represents a custom application signature.

### Application Filter

Filters built-in App-ID signatures by criteria (category, risk, etc.).

### Application Group

Groups Applications and/or Filters together.

### Dynamic User Group

Groups users dynamically based on log queries.

### External Dynamic List (EDL)

References external lists of IPs, domains or URLs.

### HIP Object & HIP Profile

Host Information Profile components for GlobalProtect.

### HTTP Server Profile

Server profile used by log-forwarding or other features.

### Log Forwarding Profile

Defines rules to forward logs to destinations.

### Quarantined Devices

List of devices quarantined via IoT Security or other sources.

### Region

Geographical regions (standard or custom) for policy matching.

### Schedule

Time-based schedules for policies.

### Service & Service Group

L4 service definitions (TCP/UDP/other) and their groupings.

### Syslog Server Profile

Syslog destinations (address / port / format).

### Tag

Simple label objects that can be applied to other resources.

---

## Related Pydantic data-models

For every class above you will find corresponding **create / update / list / detail** models in `scm.models.objects.*` (e.g. `AddressCreateModel`, `AddressModel`, …).  
These models provide type-safe validation when you supply parameters to the SDK methods and when results are returned.

---

_Last generated: 2025-06-11_
