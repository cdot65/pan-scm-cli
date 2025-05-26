# Product Requirements Document (PRD): `pan-scm-cli` Feature Enhancements

## 1. Overview

### 1.1 Product Name

`pan-scm-cli`

### 1.2 Version

0.4.0 (Major Feature Enhancements)

### 1.3 Description

This PRD covers multiple enhancements to the `pan-scm-cli` project:
1. **Authentication Enhancement**: Support for authentication via the `~/.scm-cli/config.yaml` file
2. **Show Commands**: Implementation of show commands for all resource types
3. **Smart Upsert Logic**: Intelligent create/update handling for all object types
4. **Backup Commands**: New backup functionality for exporting configurations to YAML files

### 1.4 Latest Enhancement: Backup Commands

The CLI now supports backing up configurations to YAML files with the following features:
- `backup` command for all configuration types (objects, network, security, deployment)
- Uses `exact_match=True` to only backup objects from the specified folder
- Generates YAML files with naming convention: `{configuration-item-type}-{location}.yaml`
- Excludes system fields and converts SDK format to CLI format for consistency
- Supports all object types: addresses, address groups, security zones, security rules, and bandwidth allocations

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

### 10.2 Test Scenarios
- Env vars only: Set variables, unset config file, run `test-auth`.
- Config file only: Unset variables, create `config.yaml`, run `test-auth`.
- Both: Set variables and create `config.yaml` with different values, confirm env vars win.

## 11. Smart Upsert Feature for Address Objects

### 11.1 Problem Statement

Previously, attempting to create an address that already exists would result in an error, requiring users to:
1. Check if the address exists
2. Delete it if it does
3. Create the new address

This was cumbersome and error-prone, especially in automation scenarios.

### 11.2 Solution: Intelligent Create/Update Logic

The `create_address` method in `sdk_client.py` now implements smart upsert logic:

#### 11.2.1 Basic Upsert Flow
```python
# Try to fetch existing address
existing_address = client.address.fetch(name=name, folder=folder)
if existing_address:
    # Update existing
    existing_address.description = new_description
    result = client.address.update(existing_address)
else:
    # Create new
    result = client.address.create(address_data)
```

#### 11.2.2 Address Type Change Handling

When changing address types (e.g., IP to FQDN), the method:
1. Detects the type change
2. Deletes the existing address
3. Creates a new address with the new type

This avoids SDK validation errors that occur when trying to change address types directly.

### 11.3 Technical Implementation Details

#### 11.3.1 Type Detection
- Uses `hasattr()` and value checks to determine current address type
- Maps user input to determine desired address type
- Compares types to decide on update vs. recreate strategy

#### 11.3.2 Field Management
- Only updates fields that are actually changing
- Avoids setting fields to `None` which causes SDK validation errors
- Preserves existing values when not explicitly changed

#### 11.3.3 Error Handling
- Gracefully handles `NotFoundError` when address doesn't exist
- Logs all operations clearly for debugging
- Maintains consistent error messages via `_handle_api_exception`

### 11.4 Benefits

1. **Idempotent Operations**: Running the same command multiple times produces the same result
2. **Simplified Automation**: No need for complex existence checks in scripts
3. **Better User Experience**: Clear logging shows whether objects are created or updated
4. **Type Flexibility**: Seamlessly handles address type changes without manual intervention

### 11.5 Future Considerations

This pattern should be extended to other object types:
- Address Groups ✅ (Completed)
- Security Zones (In Progress)
- Security Rules
- Bandwidth Allocations

Each will require similar logic adapted to their specific constraints and SDK requirements.

## 12. Smart Upsert Feature for Address Groups

### 12.1 Problem Statement

Similar to address objects, attempting to create an address group that already exists would result in an error, requiring manual intervention.

### 12.2 Solution: Intelligent Create/Update Logic

The `create_address_group` method now implements smart upsert logic similar to address objects:

#### 12.2.1 Basic Upsert Flow
```python
# Try to fetch existing address group
existing_group = client.address_group.fetch(name=name, folder=folder)
if existing_group:
    # Update existing
    existing_group.description = new_description
    existing_group.static = new_members  # or dynamic filter
    result = client.address_group.update(existing_group)
else:
    # Create new
    result = client.address_group.create(group_data)
```

#### 12.2.2 Group Type Change Handling

When changing group types (static ↔ dynamic), the method:
1. Detects the type change
2. Deletes the existing group
3. Creates a new group with the new type

This is necessary because the SDK doesn't allow direct type changes.

### 12.3 Technical Implementation Details

#### 12.3.1 Type Detection
- Checks for presence of `static` or `dynamic` attributes
- Compares current type with requested type
- Decides on update vs. recreate strategy

#### 12.3.2 Field Management
- Updates only fields that are changing
- Handles static member lists vs dynamic filter expressions
- Preserves existing values when not explicitly changed

### 12.4 Benefits

1. **Consistent Behavior**: Same upsert pattern as address objects
2. **Type Flexibility**: Seamlessly handles group type changes
3. **Simplified Workflows**: No need to manually check existence
4. **Clear Feedback**: Logging shows create vs update operations

## 13. Smart Upsert Feature for Security Zones

### 13.1 Implementation

The `create_zone` method now implements smart upsert logic with SDK-specific considerations:

- Automatically detects existing zones and updates them
- Handles description and tag updates seamlessly
- Provides warnings about SDK limitations for mode changes
- Simplified interface handling (full implementation would require proper network configuration)

### 13.2 SDK Limitations

The SDK doesn't support changing zone modes after creation. The implementation logs warnings about this limitation and focuses on updating other attributes.

## 14. Smart Upsert Feature for Security Rules

### 14.1 Problem Statement

Security rules require both folder and rulebase parameters, making the upsert logic more complex than other object types.

### 14.2 Solution: Rulebase-Aware Upsert

The `create_security_rule` method implements smart upsert with rulebase support:

#### 14.2.1 Enhanced Fetch Logic
```python
# Try to fetch existing rule with folder and rulebase
existing_rule = client.security_rule.fetch(
    name=name, 
    folder=folder, 
    rulebase=rulebase
)
```

#### 14.2.2 Field Name Mapping

The SDK uses different field names than our CLI interface:
- `source_zones` → `from_`
- `destination_zones` → `to_`
- `source_addresses` → `source`
- `destination_addresses` → `destination`
- `applications` → `application`
- `enabled` → `disabled` (inverted logic)
- `tags` → `tag`

### 14.3 Technical Implementation Details

#### 14.3.1 Rulebase Support
- Added `rulebase` parameter with default value "pre"
- Fetch operation includes rulebase for proper rule location
- Create operation passes rulebase to SDK

#### 14.3.2 Field Updates
- All rule attributes can be updated in place
- Service field defaults to ["any"]
- Proper handling of enabled/disabled inversion

### 14.4 Benefits

1. **Rulebase Awareness**: Properly handles pre/post/default rulebases
2. **Field Mapping**: Transparent translation between CLI and SDK field names
3. **Complete Updates**: All rule attributes can be modified
4. **Consistent Pattern**: Same upsert approach as other object types

## 15. Backup Commands Feature

### 15.1 Problem Statement

Users need a way to export their SCM configurations to YAML files for:
- Version control and change tracking
- Disaster recovery and backup purposes
- Migration between environments
- Documentation and auditing

### 15.2 Solution: Backup Commands

New `backup` command added to the CLI with the following capabilities:

#### 15.2.1 Command Structure
```bash
scm-cli backup <object-type> <object> --folder <folder-name>
```

#### 15.2.2 Supported Commands
- `scm-cli backup objects address --folder Austin`
- `scm-cli backup objects address-group --folder Austin`
- `scm-cli backup network security-zone --folder Austin`
- `scm-cli backup security rule --folder Austin --rulebase pre`
- `scm-cli backup deployment bandwidth` (no folder needed)

### 15.3 Technical Implementation Details

#### 15.3.1 SDK Client Updates
- Added `exact_match: bool = False` parameter to all list methods
- When `exact_match=True`, only objects defined exactly in the specified folder are returned
- Updated methods: `list_addresses()`, `list_address_groups()`, `list_security_zones()`, `list_security_rules()`

#### 15.3.2 Backup Implementation
- Uses `exact_match=True` to avoid backing up inherited objects
- Removes system fields like `id` that shouldn't be in backups
- Converts SDK field names back to CLI field names for consistency
- Excludes None/empty values using dictionary comprehension

#### 15.3.3 File Naming Convention
- `address-{folder}.yaml` for address objects
- `address-group-{folder}.yaml` for address groups
- `security-zone-{folder}.yaml` for security zones
- `rule-{folder}-{rulebase}.yaml` for security rules
- `bandwidth-allocations.yaml` for bandwidth allocations (global)

### 15.4 Data Transformation

The backup commands perform intelligent data transformation:

1. **Address Groups**: Converts SDK format (static/dynamic keys) to CLI format (type field with members/filter)
2. **Security Zones**: Extracts mode and interfaces from network configuration
3. **Security Rules**: Maps SDK fields (from_, to_, etc.) back to CLI fields (source_zones, destination_zones, etc.)
4. **Bandwidth Allocations**: Maps allocated_bandwidth to bandwidth

### 15.5 Benefits

1. **Version Control**: YAML files can be tracked in git
2. **Disaster Recovery**: Easy restoration from backups
3. **Migration**: Move configurations between environments
4. **Auditing**: Clear visibility into what's configured
5. **Automation**: Generated files can be used with `load` commands

## 16. Style Guide Updates

### 16.1 Section Separators

All code files now use consistent 191-character separators:
- Major sections: Double lines of equals signs (=)
- Subsections: Single lines of dashes (-) with centered titles

### 16.2 Alphabetical Ordering

The main.py file has been updated with alphabetical ordering:
- Action app groups: backup, delete, load, set, show
- Module registrations follow the same alphabetical pattern
- Improves code organization and readability

## 17. Application and Application Group Support

### 17.1 Problem Statement

The CLI needed to support custom application definitions and application group management to provide complete object configuration capabilities. Applications are critical for defining security policies and require complex attribute management.

### 17.2 Solution: Full Application Management

Implemented comprehensive support for both applications and application groups with all CRUD operations.

#### 17.2.1 Application Features
- **Create/Update**: Support for all application attributes including:
  - Basic properties: name, category, subcategory, technology, risk level
  - Port definitions: TCP/UDP port specifications
  - Security attributes: 9 boolean flags for security characteristics
- **Show**: List all or display specific applications with detailed attribute information
- **Load**: Bulk import from YAML files
- **Delete**: Remove applications by name
- **Backup**: Export applications to YAML with proper formatting

#### 17.2.2 Application Group Features
- **Create/Update**: Simple member list management
- **Show**: Display group membership
- **Load**: Bulk import groups from YAML
- **Delete**: Remove groups by name
- **Backup**: Export groups to YAML format

### 17.3 Technical Implementation Details

#### 17.3.1 SDK Client Methods
Added the following methods to `sdk_client.py`:
- `create_application()`: Smart upsert with full attribute support
- `delete_application()`: Remove by name and folder
- `get_application()`: Fetch specific application
- `list_applications()`: List with exact_match support
- `create_application_group()`: Smart upsert for groups
- `delete_application_group()`: Remove groups
- `get_application_group()`: Fetch specific group
- `list_application_groups()`: List with exact_match support

#### 17.3.2 Command Implementation
In `objects.py`, added full command sets for both types:
- Application commands: set, show, load, delete, backup
- Application group commands: set, show, load, delete, backup
- Proper option handling for all application attributes
- Consistent error handling and user feedback

#### 17.3.3 Validation Models
Extended `validators.py` with:
- `Application` model with all SDK fields
- `ApplicationGroup` model with member validation
- Proper `to_sdk_model()` methods for both

### 17.4 Benefits

1. **Complete Object Coverage**: CLI now supports all major object types
2. **Security Policy Support**: Applications are essential for rule definitions
3. **Bulk Operations**: YAML-based load/backup for migration scenarios
4. **Attribute Management**: Full control over all security characteristics
5. **Group Organization**: Logical grouping of related applications

### 17.5 Testing Results

All commands have been thoroughly tested with the Austin folder:
- ✅ Set command creates applications with all attributes
- ✅ Show command displays detailed application information
- ✅ Load command imports from YAML files
- ✅ Delete command removes applications cleanly
- ✅ Backup command exports to properly formatted YAML

Note: When using the CLI, application references must be valid existing applications in the SCM system.
