# SDK Mobile-Agent Objects

This document lists GlobalProtect **Mobile-Agent** configuration classes provided by the Python SDK (`scm.config.mobile_agent`) and the CRUD-style methods you can use.

> **Tip** After creating, updating or deleting objects, call `commit()` and track the resulting job via `get_job_status()` or `list_jobs()`.

## Quick-reference table

| Object         | SDK Class                               | Description                                       | Create     | Read                         | Update               | Delete     | Commit     |
| -------------- | --------------------------------------- | ------------------------------------------------- | ---------- | ---------------------------- | -------------------- | ---------- | ---------- |
| Agent Versions | `scm.config.mobile_agent.AgentVersions` | Manage allowed GlobalProtect agent versions       | —          | `fetch()`, `list()`          | —                    | —          | —          |
| Auth Settings  | `scm.config.mobile_agent.AuthSettings`  | Manage authentication settings (SAML/OAuth, etc.) | `create()` | `get()`, `fetch()`, `list()` | `update()`, `move()` | `delete()` | `commit()` |

---

## Usage pattern

```python
from scm.config.mobile_agent import AgentVersions

# Read
a_version = AgentVersions.fetch()
versions  = AgentVersions.list()

# Update
# Not supported

# Delete
# Not supported

# Create
# Not supported
```

### Monitoring jobs

```python
status = AgentVersions.get_job_status(job_id)
all_jobs = AgentVersions.list_jobs(limit=20)
```

---

## Object details

### Agent Versions (`AgentVersions`)

Define which GlobalProtect agent versions are allowed, disallowed, or force-upgraded for users.

### Auth Settings (`AuthSettings`)

Configure GlobalProtect portal and gateway authentication methods such as SAML, OAuth, or certificates.

---

## Related Pydantic data-models

Each class has corresponding models in `scm.models.mobile_agent.*` (e.g. `AgentVersionCreateModel`, `AuthSettingsModel`) that validate inputs and SDK responses.

---

_Last generated: 2025-06-11_
