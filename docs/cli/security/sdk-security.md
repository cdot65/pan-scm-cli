# SDK Security Objects

This document lists all security-related configuration object classes provided by the Python SDK (`scm.config.security`) and the standard methods you can use to perform **C**reate, **R**ead, **U**pdate and **D**elete (CRUD) operations.

All classes share a consistent interface; once you’ve used one, you can use the rest.

> **Tip** Remember to call `commit()` after create / update / delete, and use `get_job_status()` / `list_jobs()` to monitor the resulting job.

## Quick-reference table

| Object                           | SDK Class                                            | Description                              | Create     | Read                         | Update               | Delete     | Commit     |
| -------------------------------- | ---------------------------------------------------- | ---------------------------------------- | ---------- | ---------------------------- | -------------------- | ---------- | ---------- |
| Anti-Spyware Profile             | `scm.config.security.AntiSpywareProfile`             | Manage Anti-Spyware profiles             | `create()` | `get()`, `fetch()`, `list()` | `update()`           | `delete()` | `commit()` |
| DNS Security Profile             | `scm.config.security.DNSSecurityProfile`             | Manage DNS Security profiles             | `create()` | `get()`, `fetch()`, `list()` | `update()`           | `delete()` | `commit()` |
| Decryption Profile               | `scm.config.security.DecryptionProfile`              | Manage Decryption profiles               | `create()` | `get()`, `fetch()`, `list()` | `update()`           | `delete()` | `commit()` |
| Security Rule                    | `scm.config.security.SecurityRule`                   | Manage Security policy rules             | `create()` | `get()`, `fetch()`, `list()` | `update()`, `move()` | `delete()` | `commit()` |
| URL Categories                   | `scm.config.security.URLCategories`                  | Manage custom URL categories             | `create()` | `get()`, `fetch()`, `list()` | `update()`           | `delete()` | `commit()` |
| Vulnerability Protection Profile | `scm.config.security.VulnerabilityProtectionProfile` | Manage Vulnerability Protection profiles | `create()` | `get()`, `fetch()`, `list()` | `update()`           | `delete()` | `commit()` |
| WildFire Antivirus Profile       | `scm.config.security.WildfireAntivirusProfile`       | Manage WildFire Antivirus profiles       | `create()` | `get()`, `fetch()`, `list()` | `update()`           | `delete()` | `commit()` |

---

## Usage pattern

```python
from scm.config.security import SecurityRule  # choose the class you need

# Create a rule
resp = SecurityRule.create(name="allow-web", source_zones=["Trust"], destination_zones=["Untrust"], applications=["web-browsing"], action="allow")
SecurityRule.commit()

# Read
rule = SecurityRule.get(resp.id)
rules = SecurityRule.list(limit=100)

# Update
SecurityRule.update(resp.id, description="Allow outbound web traffic")
SecurityRule.commit()

# Delete
SecurityRule.delete(resp.id)
SecurityRule.commit()
```

### Monitoring jobs

```python
status = SecurityRule.get_job_status(job_id)
all_jobs = SecurityRule.list_jobs(limit=10)
```

---

## Object details

### Anti-Spyware Profile (`AntiSpywareProfile`)

Detects and blocks spyware / malicious traffic patterns.

### DNS Security Profile (`DNSSecurityProfile`)

Adds domain intelligence to DNS queries to block malicious domains.

### Decryption Profile (`DecryptionProfile`)

Defines certificate checks and security settings for SSL/TLS decryption.

### Security Rule (`SecurityRule`)

Layer-3/4/7 policy rules controlling traffic.

### URL Categories (`URLCategories`)

Custom URL category lists used in policy.

### Vulnerability Protection Profile (`VulnerabilityProtectionProfile`)

Protects against exploits and protocol deviations.

### WildFire Antivirus Profile (`WildfireAntivirusProfile`)

Cloud-based malware detection with WildFire signatures.

---

## Related Pydantic data-models

For every class above you will find corresponding models in `scm.models.security.*` (e.g. `SecurityRuleCreateModel`, `AntiSpywareProfileModel`, …) which provide type-safe validation for inputs and SDK responses.

---

_Last generated: 2025-06-11_
