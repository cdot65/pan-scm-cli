# SDK Setup Objects

This document covers **tenant-setup** objects provided by the Python SDK (`scm.config.setup`) and shows the common CRUD operations available for each class.

Use these objects to create and organise the foundational hierarchy in Strata Cloud Manager—folders, snippets, variables, etc.—before adding security or network configurations.

> **Tip** After making changes call `commit()` and track the background job via `get_job_status()` or `list_jobs()`.

## Quick-reference table

| Object   | SDK Class                   | Description                       | Create     | Read                         | Update     | Delete     | Commit     |
| -------- | --------------------------- | --------------------------------- | ---------- | ---------------------------- | ---------- | ---------- | ---------- |
| Device   | `scm.config.setup.Device`   | Manage onboarded devices          | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Folder   | `scm.config.setup.Folder`   | Manage configuration folders      | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Label    | `scm.config.setup.Label`    | Manage labels used for grouping   | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Snippet  | `scm.config.setup.Snippet`  | Manage snippets (partial configs) | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |
| Variable | `scm.config.setup.Variable` | Manage template variables         | `create()` | `get()`, `fetch()`, `list()` | `update()` | `delete()` | `commit()` |

---

## Usage pattern

```python
from scm.config.setup import Folder

# Create a folder
resp = Folder.create(name="Production", parent="Shared")
Folder.commit()

# Read folders
folder = Folder.get(resp.id)
all_folders = Folder.list(limit=200)

# Update
Folder.update(resp.id, description="Production configs")
Folder.commit()

# Delete
Folder.delete(resp.id)
Folder.commit()
```

### Monitoring jobs

```python
status = Folder.get_job_status(job_id)
jobs   = Folder.list_jobs(limit=20)
```

---

## Object details

### Device (`Device`)

Represents a managed firewall or cloud device onboarded to SCM.

### Folder (`Folder`)

Container for organising configuration objects (analogous to device groups or folders).

### Label (`Label`)

Key-value labels applied to objects for classification.

### Snippet (`Snippet`)

Reusable partial configurations you can insert into policies or objects.

### Variable (`Variable`)

Template variables for dynamic values in snippets or policies.

---

## Related Pydantic data-models

Each class has matching Pydantic models in `scm.models.setup.*` (e.g. `FolderCreateModel`, `VariableModel`) that validate parameters and SDK responses.

---

_Last generated: 2025-06-11_
