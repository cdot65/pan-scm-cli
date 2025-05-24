# Product Requirements Document (PRD): `pan-scm-cli` Authentication Enhancement

## 1. Overview

### 1.1 Product Name

`pan-scm-cli`

### 1.2 Version

0.2.1 (Feature Enhancement)

### 1.3 Description

This PRD addresses a critical gap in the `pan-scm-cli` project: the lack of support for authentication via the `~/.scm-cli/config.yaml` file, despite its inclusion in the README as a supported method. The CLI currently relies on environment variables (`SCM_CLIENT_ID`, `SCM_CLIENT_SECRET`, `SCM_TSG_ID`), but the promised config file functionality is missing. This enhancement will integrate Dynaconf to enable seamless authentication from both sources, ensuring consistency with documented features.

### 1.4 Purpose

Enable `pan-scm-cli` to fully support authentication via:

- Environment variables (`SCM_CLIENT_ID`, `SCM_CLIENT_SECRET`, `SCM_TSG_ID`).
- A configuration file at `~/.scm-cli/config.yaml`.
  This ensures flexibility for users and aligns the implementation with the README’s stated capabilities.

### 1.5 Target Audience

- Network engineers using `pan-scm-cli` to manage Strata Cloud Manager (SCM) configurations.
- DevOps teams automating SCM workflows.

### 1.6 Stakeholders

- **Product Owner**: Calvin Remsburg (dev@cdot.io)
- **Developers**: Open-source contributors (https://github.com/cdot65/pan-scm-cli)
- **Users**: Network engineering community

## 2. Goals and Objectives

### 2.1 Goals

- Close the authentication functionality gap by implementing config file support.
- Provide a seamless and prioritized authentication mechanism (environment variables over config file).
- Enhance user experience with a verification command to test authentication setup.

### 2.2 Success Metrics

- CLI successfully authenticates using `config.yaml` when environment variables are absent.
- CLI prioritizes environment variables over `config.yaml` when both are present.
- 100% of test cases pass for authentication scenarios (env vars only, config file only, both).
- Updated README is accurate and validated by at least 5 users within 1 month of release.

## 3. Features and Requirements

### 3.1 Functional Requirements

#### 3.1.1 Authentication Sources

- **Environment Variables**:
  - `SCM_CLIENT_ID`: Client ID for SCM API.
  - `SCM_CLIENT_SECRET`: Client secret for SCM API.
  - `SCM_TSG_ID`: Tenant Service Group ID for SCM.
- **Configuration File**:

  - Location: `~/.scm-cli/config.yaml`.
  - Structure:

    ```yaml
    client_id: "your_client_id"
    client_secret: "your_client_secret"
    tsg_id: "your_tenant_service_group_id"
    ```

  - File must be optional; CLI falls back to it if environment variables are unset.

#### 3.1.2 Priority Logic

- Environment variables take precedence over `config.yaml` values.
- If neither source provides all required credentials, raise a clear error message (e.g., "Missing required authentication parameters: client_id, tsg_id").

#### 3.1.3 SCM Client Integration

- Use credentials from either source to initialize the `pan-scm-sdk` `StrataCloudManager` client.
- Support `--mock` mode with a mock client that doesn’t require real credentials.

#### 3.1.4 Verification Command

- Add a `test-auth` command to verify authentication setup:
  - `scm-cli test-auth`: Confirms client initialization with real credentials.
  - `scm-cli test-auth --mock`: Simulates authentication without API calls.

### 3.2 Non-Functional Requirements

- **Reliability**: Gracefully handle missing or invalid credentials with user-friendly errors.
- **Security**: Recommend file permissions (e.g., `chmod 600`) for `config.yaml` in documentation.
- **Maintainability**: Use Dynaconf for configuration management to leverage its built-in features.
- **Documentation**: Update README to reflect prioritization and verification command.

## 4. Technical Specifications

### 4.1 Tech Stack

- **Existing Dependencies**:
  - `python>=3.10,<3.14`
  - `dynaconf>=3.2.10` (for config management)
  - `pan-scm-sdk==0.3.39` (SCM API client)
  - `typer==0.15.2` (CLI framework)
- **No New Dependencies Required**

### 4.2 Project Structure Updates

```
pan-scm-cli/
├── src/
│   └── scm_cli/
│       ├── __init__.py
│       ├── main.py           # Updated with test-auth command
│       ├── config.py        # New: Dynaconf configuration
│       ├── client.py        # New: SCM client initialization
│       └── commands/
│           ├── objects/     # Updated to use client.py
│           └── ...          # Other modules similarly updated
├── tests/
│   ├── test_config.py       # New: Test authentication logic
│   └── ...                  # Existing tests
├── README.md                # Updated authentication section
└── pyproject.toml           # Unchanged
```

### 4.3 Key Components

#### 4.3.1 Configuration (`config.py`)

- Use Dynaconf to load credentials from environment variables or `config.yaml`.
- Example:

```python
from dynaconf import Dynaconf
from pathlib import Path

settings = Dynaconf(
    envvar_prefix="SCM",
    settings_files=[Path.home() / ".scm-cli" / "config.yaml"],
)

def get_auth_config():
    auth = {
        "client_id": settings.get("client_id"),
        "client_secret": settings.get("client_secret"),
        "tsg_id": settings.get("tsg_id"),
    }
    missing = [k for k, v in auth.items() if not v]
    if missing:
        raise ValueError(f"Missing required authentication parameters: {', '.join(missing)}")
    return auth
```

#### 4.3.2 SCM Client (`client.py`)

- Initialize `StrataCloudManager` with loaded credentials.
- Example:

```python
from pan_scm_sdk import StrataCloudManager
from .config import get_auth_config

def get_scm_client(mock=False):
    if mock:
        return MockSCMClient()
    auth = get_auth_config()
    return StrataCloudManager(**auth)

class MockSCMClient:
    def __getattr__(self, name):
        def mock_method(*args, **kwargs):
            return {"status": "success", "message": f"Mock {name} call"}
        return mock_method
```

#### 4.3.3 Main CLI (`main.py`)

- Add `test-auth` command and integrate client.
- Example:

```python
import typer
from .client import get_scm_client

app = typer.Typer(name="scm-cli", help="CLI for Palo Alto Networks Strata Cloud Manager")

@app.command()
def test_auth(mock: bool = typer.Option(False, "--mock")):
    client = get_scm_client(mock=mock)
    typer.echo("Authentication successful" if mock else f"Client initialized: {client}")
```

#### 4.3.4 Command Updates

- Update commands (e.g., `objects/set.py`) to use `get_scm_client`.

### 4.4 Dependencies

- No changes to `pyproject.toml`; Dynaconf is already included.

## 5. User Stories

### 5.1 As a Network Engineer, I Want To:

- Authenticate using `~/.scm-cli/config.yaml` when environment variables aren’t set, so I can avoid repetitive shell configuration.
- Verify my authentication setup with `scm-cli test-auth`, so I can troubleshoot issues easily.
- Use environment variables when available, overriding `config.yaml`, for scripting flexibility.

## 6. Milestones and Timeline

### 6.1 Milestone 1: Implementation (1 week)

- Add `config.py` and `client.py`.
- Update `main.py` with `test-auth`.
- Modify existing commands to use `get_scm_client`.

### 6.2 Milestone 2: Testing and Documentation (1 week)

- Write unit tests for `config.py` and integration tests for authentication.
- Update README with new authentication details.

### 6.3 Total Timeline

- 2 weeks from start to completion.

## 7. Risks and Mitigations

### 7.1 Risk: Dynaconf Misconfiguration

- **Mitigation**: Thoroughly test all authentication scenarios; document edge cases in README.

### 7.2 Risk: File Permission Issues

- **Mitigation**: Include security guidance in README (e.g., `chmod 600`).

### 7.3 Risk: User Confusion on Priority

- **Mitigation**: Clearly document prioritization in README and error messages.

## 8. Acceptance Criteria

- CLI authenticates successfully with `config.yaml` when environment variables are unset.
- CLI prioritizes environment variables over `config.yaml` when both are present.
- `scm-cli test-auth` confirms authentication setup (real and mock modes).
- All tests pass with 100% coverage for new code.
- Updated README accurately reflects behavior and is validated by sample usage.

## 9. Support and Maintenance

- **Support**: GitHub Issues (update `SUPPORT.md` if needed).
- **Maintenance**: Monitor Dynaconf and `pan-scm-sdk` updates monthly.

## 10. Appendix

### 10.1 Updated README Authentication Section

````markdown
### Authentication

Configure authentication using one of the following methods. The CLI prioritizes environment variables over the configuration file if both are present.

#### Environment Variables

```bash
# Linux/macOS
export SCM_CLIENT_ID="your_client_id"
export SCM_CLIENT_SECRET="your_client_secret"
export SCM_TSG_ID="your_tenant_service_group_id"
```
````

#### Configuration File

Create `~/.scm-cli/config.yaml`:

```yaml
client_id: "your_client_id"
client_secret: "your_client_secret"
tsg_id: "your_tenant_service_group_id"
```

Ensure file permissions are secure (e.g., `chmod 600 ~/.scm-cli/config.yaml`).

#### Verification

Test your setup with:

```bash
scm-cli test-auth
```

Use `--mock` for simulation:

```bash
scm-cli test-auth --mock
```

```

### 10.2 Test Scenarios
- Env vars only: Set variables, unset config file, run `test-auth`.
- Config file only: Unset variables, create `config.yaml`, run `test-auth`.
- Both: Set variables and create `config.yaml` with different values, confirm env vars win.
```
