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

- **Product Owner**: Calvin Remsburg (mailto:dev@cdot.io)
- **Developers**: Open-source contributors (mailto:dev@cdot.io)
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

```bash
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

### 5.1 As a Network Engineer, I Want To

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
3. **Security Rules**: Maps SDK fields (from*, to*, etc.) back to CLI fields (source_zones, destination_zones, etc.)
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

## 18. Application Filter Support

### 18.1 Problem Statement

Application filters are essential for dynamic application selection in security policies. They allow administrators to create criteria-based selections rather than static lists, enabling more flexible and maintainable security configurations.

### 18.2 Solution: Full Application Filter Management

Implemented comprehensive support for application filters with all CRUD operations and complex filtering capabilities.

#### 18.2.1 Application Filter Features

- **Create/Update**: Support for all filter criteria including:
  - List-based attributes: category, subcategory, technology, risk levels
  - Boolean security flags: Same 9 attributes as applications
  - Smart upsert logic for seamless updates
- **Show**: List all or display specific filters with detailed criteria
- **Load**: Bulk import from YAML files with validation
- **Delete**: Remove filters by name and folder
- **Backup**: Export filters to YAML with proper formatting

#### 18.2.2 Key Implementation Fixes

- **SDK Service Name**: Fixed usage of `application_filter` (singular) instead of `application_filters` (plural)
- **Boolean Field Handling**: API rejects explicit `false` values; implementation now omits boolean fields when false
- **List Attribute Support**: Proper handling of multiple values for category, subcategory, technology, and risk

### 18.3 Technical Implementation Details

#### 18.3.1 SDK Client Methods

Added the following methods to `sdk_client.py`:

- `create_application_filter()`: Smart upsert with conditional boolean field inclusion
- `delete_application_filter()`: Remove by name and folder
- `get_application_filter()`: Fetch specific filter with all criteria
- `list_application_filters()`: List with exact_match support

#### 18.3.2 Command Implementation

In `objects.py`, added full command set:

- `set`: Create/update with list and boolean options
- `show`: Display with criteria formatting
- `load`: Import from YAML with validation
- `delete`: Remove filters
- `backup`: Export to YAML format

#### 18.3.3 Validation Model

Extended `validators.py` with:

- `ApplicationFilter` model with list and boolean fields
- Risk value validation (1-5 range)
- Proper `to_sdk_model()` with conditional field inclusion

### 18.4 Benefits

1. **Dynamic Policy Management**: Enable criteria-based application selection
2. **Reduced Maintenance**: Automatically include new applications matching criteria
3. **Complex Filtering**: Combine multiple criteria for precise selection
4. **API Compatibility**: Proper handling of SDK quirks and validation rules
5. **Bulk Operations**: YAML-based import/export for large-scale management

### 18.5 Example Usage

```bash
# Create a high-risk application filter
scm-cli set objects application-filter \
  --folder Texas \
  --name high-risk-apps \
  --category business-systems \
  --subcategory database \
  --technology client-server \
  --risk 4 --risk 5 \
  --has-known-vulnerabilities

# List all filters
scm-cli show objects application-filter --folder Texas --list

# Backup filters
scm-cli backup objects application-filter --folder Texas
```

### 18.6 Testing Results

All commands have been tested and verified:

- ✅ Set command creates filters with all criteria types
- ✅ Show command displays detailed filter information
- ✅ Load command imports from YAML files correctly
- ✅ Delete command removes filters cleanly
- ✅ Backup command exports to properly formatted YAML
- ✅ Boolean field handling works correctly (omits false values)
- ✅ SDK service name issue resolved

## 19. Dynamic User Group Support

### 19.1 Problem Statement

Dynamic user groups are essential for automatically grouping users based on tag attributes. They enable dynamic security policies that adapt as user attributes change, eliminating the need for manual group maintenance.

### 19.2 Solution: Full Dynamic User Group Management

Implemented comprehensive support for dynamic user groups with all CRUD operations and tag-based filter expressions.

#### 19.2.1 Dynamic User Group Features

- **Create/Update**: Support for tag-based filter expressions
  - Simple tag matching: "'Engineering' and 'Developer'"
  - Attribute-based filters: "tag.Department='IT' and tag.Role='Admin'"
  - Complex expressions with boolean logic
  - Smart upsert logic for seamless updates
- **Show**: List all or display specific groups with filter expressions
- **Load**: Bulk import from YAML files with validation
- **Delete**: Remove groups by name and folder
- **Backup**: Export groups to YAML with proper formatting

#### 19.2.2 Filter Expression Syntax

- Uses single quotes around tag values
- Supports boolean operators: and, or
- Allows attribute-based filtering with tag.attribute syntax
- Supports comparison operators for numeric values

### 19.3 Technical Implementation Details

#### 19.3.1 SDK Client Methods

Added the following methods to `sdk_client.py`:

- `create_dynamic_user_group()`: Smart upsert with filter expression support
- `delete_dynamic_user_group()`: Remove by name and folder
- `get_dynamic_user_group()`: Fetch specific group with filter
- `list_dynamic_user_groups()`: List with exact_match support

#### 19.3.2 Command Implementation

In `objects.py`, added full command set:

- `set`: Create/update with filter expression
- `show`: Display with filter formatting
- `load`: Import from YAML with validation
- `delete`: Remove groups
- `backup`: Export to YAML format with tag field mapping

#### 19.3.3 Validation Model

Extended `validators.py` with:

- `DynamicUserGroup` model with filter field
- Tag field mapping (tags → tag for SDK)
- Proper `to_sdk_model()` method

### 19.4 Benefits

1. **Automated User Management**: Groups update automatically as user tags change
2. **Flexible Filtering**: Complex tag-based expressions for precise grouping
3. **Scalability**: Handle large user populations without manual maintenance
4. **Policy Agility**: Security policies adapt dynamically to user changes
5. **Bulk Operations**: YAML-based import/export for migration

### 19.5 Example Usage

```bash
# Create a dynamic user group
scm-cli set objects dynamic-user-group \
  --folder Texas \
  --name it-admins \
  --filter "'IT' and 'Admin'" \
  --description "IT administrators"

# List all groups
scm-cli show objects dynamic-user-group --folder Texas --list

# Backup groups
scm-cli backup objects dynamic-user-group --folder Texas
```

### 19.6 Testing Results

All commands have been tested and verified:

- ✅ Set command creates groups with filter expressions
- ✅ Show command displays filter expressions correctly
- ✅ Load command imports from YAML files
- ✅ Delete command removes groups cleanly
- ✅ Backup command exports with proper tag field mapping
- ✅ Example YAML file created with comprehensive patterns

## 20. External Dynamic List Support

### 20.1 Problem Statement

External Dynamic Lists (EDLs) are crucial for integrating third-party threat intelligence feeds and maintaining dynamic blocklists/allowlists. They enable automatic updates from external sources without manual intervention, keeping security policies current with the latest threat intelligence.

### 20.2 Solution: Full External Dynamic List Management

Implemented comprehensive support for all EDL types with complete CRUD operations, complex configurations, and multiple update schedules.

#### 20.2.1 External Dynamic List Features

- **Create/Update**: Support for all EDL types with specific configurations
  - Predefined lists (IP and URL) from Palo Alto Networks
  - Custom IP, Domain, URL, IMSI, and IMEI lists
  - Recurring update schedules (5 minutes to monthly)
  - Authentication support (username/password, certificates)
  - Exception list management
  - Smart upsert logic for seamless updates
- **Show**: List all or display specific EDLs with configuration details
- **Load**: Bulk import from YAML files with validation
- **Delete**: Remove EDLs by name and folder
- **Backup**: Export EDLs to YAML with flattened structure

#### 20.2.2 Supported EDL Types

1. **Predefined IP** (`predefined_ip`): Palo Alto managed IP lists
2. **Predefined URL** (`predefined_url`): Palo Alto managed URL lists
3. **IP** (`ip`): Custom IP address lists
4. **Domain** (`domain`): Domain name lists with optional subdomain expansion
5. **URL** (`url`): Custom URL pattern lists
6. **IMSI** (`imsi`): Mobile subscriber identity lists
7. **IMEI** (`imei`): Mobile equipment identity lists

### 20.3 Technical Implementation Details

#### 20.3.1 SDK Client Methods

Added the following methods to `sdk_client.py`:

- `create_external_dynamic_list()`: Smart upsert with type-specific configuration
- `delete_external_dynamic_list()`: Remove by name and folder
- `get_external_dynamic_list()`: Fetch specific EDL with full configuration
- `list_external_dynamic_lists()`: List with exact_match support

#### 20.3.2 Validator Model

Created `ExternalDynamicList` model in `validators.py` with:

- Type validation ensuring proper EDL type selection
- Recurring schedule validation (daily/weekly/monthly require hour)
- Complex type configuration building
- Flattened YAML structure for easier editing

#### 20.3.3 CLI Commands

Implemented in `objects.py`:

- `backup_external_dynamic_list()`: Export with flattened structure
- `delete_external_dynamic_list()`: Remove by name and folder
- `load_external_dynamic_list()`: Import with full validation
- `set_external_dynamic_list()`: Create/update with all options
- `show_external_dynamic_list()`: Display with configuration details

### 20.4 Usage Examples

```bash
# Create a predefined IP list
scm-cli set objects external-dynamic-list \
  --folder Texas \
  --name paloalto-bulletproof \
  --type predefined_ip \
  --url "panw-bulletproof-ip-list"

# Create a custom IP list with hourly updates
scm-cli set objects external-dynamic-list \
  --folder Texas \
  --name custom-blocklist \
  --type ip \
  --url "https://example.com/blocklist.txt" \
  --recurring hourly

# Create a domain list with authentication
scm-cli set objects external-dynamic-list \
  --folder Texas \
  --name malicious-domains \
  --type domain \
  --url "https://secure.example.com/domains.txt" \
  --recurring daily \
  --hour 03 \
  --username api_user \
  --password secure_pass \
  --expand-domain

# List all EDLs
scm-cli show objects external-dynamic-list --folder Texas --list

# Backup EDLs
scm-cli backup objects external-dynamic-list --folder Texas
```

### 20.5 Testing Results

All commands have been tested and verified:

- ✅ Set command creates EDLs with all configuration types
- ✅ Show command displays detailed configuration including recurring schedules
- ✅ Load command imports from YAML files with proper validation
- ✅ Delete command removes EDLs cleanly
- ✅ Backup command exports with flattened structure for easy editing
- ✅ SDK service name corrected (external_dynamic_list not external_dynamic_lists)
- ✅ Comprehensive example YAML file created with all EDL types

## 21. HIP Object Support

### 21.1 Problem Statement

Host Information Profiles (HIP) are essential for enforcing endpoint compliance in security policies. They enable dynamic security based on device state, ensuring that only compliant endpoints can access sensitive resources. The CLI needed comprehensive HIP object management to complete its security configuration capabilities.

### 21.2 Solution: Full HIP Object Management

Implemented comprehensive support for HIP objects with all CRUD operations and multiple criteria types for endpoint validation.

#### 21.2.1 HIP Object Features

- **Create/Update**: Support for all HIP criteria types
  - Host information (domain, OS, client version, managed state, etc.)
  - Network information (WiFi, mobile, ethernet, unknown)
  - Patch management (installation status, missing patches, severity)
  - Disk encryption (installation status, encrypted locations, vendors)
  - Mobile device (jailbreak status, passcode, last check-in, applications)
  - Certificate (profile and attributes)
  - Smart upsert logic for seamless updates
- **Show**: List all or display specific HIP objects with detailed criteria
- **Load**: Bulk import from YAML files with validation
- **Delete**: Remove HIP objects by name and folder
- **Backup**: Export HIP objects to YAML with flattened structure

#### 21.2.2 Supported Criteria Types

1. **Host Information**: OS type, domain membership, managed state, client version
2. **Network Information**: Connection type restrictions (WiFi, ethernet, mobile)
3. **Patch Management**: Missing patches, severity thresholds, vendor-specific
4. **Disk Encryption**: Encryption status, specific locations, vendor support
5. **Mobile Device**: Jailbreak detection, passcode requirements, app control
6. **Certificate**: Profile validation, attribute matching

### 21.3 Technical Implementation Details

#### 21.3.1 SDK Client Methods

Added the following methods to `sdk_client.py`:

- `create_hip_object()`: Smart upsert with all criteria types
- `delete_hip_object()`: Remove by name and folder
- `get_hip_object()`: Fetch specific HIP object with full criteria
- `list_hip_objects()`: List with exact_match support

#### 21.3.2 Validator Model

Created `HIPObject` model in `validators.py` with:

- Flattened field structure for easier CLI usage
- Criteria pair validation (e.g., domain criteria requires domain value)
- Complex nested structure building for SDK compatibility
- Comprehensive `to_sdk_model()` method

#### 21.3.3 CLI Commands

Implemented in `objects.py`:

- `backup_hip_object()`: Export with flattened structure for easy editing
- `delete_hip_object()`: Remove by name and folder
- `load_hip_object()`: Import with full validation
- `set_hip_object()`: Create/update with simplified CLI options
- `show_hip_object()`: Display with formatted criteria sections

### 21.4 Usage Examples

```bash
# Create a Windows workstation compliance policy
scm-cli set objects hip-object \
  --folder Texas \
  --name windows-compliance \
  --description "Windows workstation compliance" \
  --host-info-os Microsoft \
  --host-info-os-value All \
  --host-info-managed \
  --disk-encryption-enabled \
  --patch-management-enabled

# Create a mobile device policy
scm-cli set objects hip-object \
  --folder Texas \
  --name mobile-secure \
  --description "Mobile device security" \
  --mobile-device-jailbroken false \
  --mobile-device-disk-encrypted \
  --mobile-device-passcode-set

# Create a network-based restriction
scm-cli set objects hip-object \
  --folder Texas \
  --name wifi-only \
  --description "WiFi network only" \
  --network-info-type is \
  --network-info-value wifi

# List all HIP objects
scm-cli show objects hip-object --folder Texas --list

# Backup HIP objects
scm-cli backup objects hip-object --folder Texas
```

### 21.5 Testing Results

All commands have been tested and verified:

- ✅ Set command creates HIP objects with all criteria types
- ✅ Show command displays formatted criteria sections
- ✅ Load command imports from YAML files with validation
- ✅ Delete command removes HIP objects cleanly
- ✅ Backup command exports with flattened structure for easy editing
- ✅ Comprehensive example YAML file created with 11 different HIP policies
- ✅ SDK service name correct (hip_object)

## 22. HIP Profile Support

### 22.1 Problem Statement

HIP profiles combine multiple HIP objects to create comprehensive endpoint compliance policies. They enable administrators to define complex compliance requirements by matching multiple HIP objects with boolean operators (is/is-not).

### 22.2 Solution: Full HIP Profile Management

Implemented comprehensive support for HIP profiles with all CRUD operations and complex match criteria handling.

#### 22.2.1 HIP Profile Features

- **Create/Update**: Support for complex match criteria
  - Match multiple HIP objects with boolean operators
  - JSON-based match configuration for CLI
  - Smart upsert logic for seamless updates
- **Show**: List all or display specific profiles with match criteria
- **Load**: Bulk import from YAML files with validation
- **Delete**: Remove profiles by name and folder
- **Backup**: Export profiles to YAML with proper formatting

#### 22.2.2 Match Criteria Format

- CLI uses JSON format: `{"hip-object-1": {"is": true}, "hip-object-2": {"is-not": true}}`
- YAML uses standard format for readability
- SDK requires nested structure with match field

### 22.3 Technical Implementation Details

#### 22.3.1 SDK Client Methods

Added the following methods to `sdk_client.py`:

- `create_hip_profile()`: Smart upsert with match criteria handling
- `delete_hip_profile()`: Remove by name and folder
- `get_hip_profile()`: Fetch specific profile with match criteria
- `list_hip_profiles()`: List with exact_match support

#### 22.3.2 Validator Model

Created `HIPProfile` model in `validators.py` with:

- Match field for HIP object criteria
- Proper `to_sdk_model()` method
- Support for both CLI JSON and YAML formats

#### 22.3.3 CLI Commands

Implemented in `objects.py`:

- `backup_hip_profile()`: Export to YAML format
- `delete_hip_profile()`: Remove by name and folder
- `load_hip_profile()`: Import with validation
- `set_hip_profile()`: Create/update with JSON match parameter
- `show_hip_profile()`: Display with formatted match criteria

### 22.4 Testing Results

All commands have been tested and verified:

- ✅ Set command creates profiles with complex match criteria
- ✅ Show command displays match criteria properly
- ✅ Load command imports from YAML files
- ✅ Delete command removes profiles cleanly
- ✅ Backup command exports to YAML format
- ✅ SDK service name correct (hip_profile)
- ✅ Example YAML file created with various profile configurations

## 23. HTTP Server Profile Support

### 23.1 Problem Statement

HTTP server profiles are essential for log forwarding and SIEM integration in modern security architectures. They enable sending logs to external systems via HTTP/HTTPS for centralized monitoring, analysis, and compliance requirements.

### 23.2 Solution: Full HTTP Server Profile Management

Implemented comprehensive support for HTTP server profiles with all CRUD operations and complex server configurations.

#### 23.2.1 HTTP Server Profile Features

- **Create/Update**: Support for complex server configurations
  - Multiple server configurations per profile
  - HTTP/HTTPS protocol support with port specification
  - Authentication (username/password)
  - TLS version and certificate profile options
  - Custom format configurations for different log types
  - Smart upsert logic for seamless updates
- **Show**: List all or display specific profiles with server details
- **Load**: Bulk import from YAML files with validation
- **Delete**: Remove profiles by name and folder
- **Backup**: Export profiles to YAML with proper field mapping

#### 23.2.2 Server Configuration Requirements

- **Required fields**: name, address, protocol, port, http_method
- **Optional fields**: tls_version, certificate_profile, username, password
- **Format config**: Custom headers and payload formats per log type

### 23.3 Technical Implementation Details

#### 23.3.1 SDK Client Methods

Added the following methods to `sdk_client.py`:

- `create_http_server_profile()`: Smart upsert with server configuration handling
- `delete_http_server_profile()`: Remove by name and folder
- `get_http_server_profile()`: Fetch specific profile with server details
- `list_http_server_profiles()`: List with exact_match support

#### 23.3.2 Validator Model

Created `HTTPServerProfile` model in `validators.py` with:

- Server list validation with required fields
- Format configuration support
- Proper `to_sdk_model()` method
- Field mapping (servers → server for SDK)

#### 23.3.3 CLI Commands

Implemented in `objects.py`:

- `backup_http_server_profile()`: Export with field mapping (server → servers)
- `delete_http_server_profile()`: Remove by name and folder
- `load_http_server_profile()`: Import with validation
- `set_http_server_profile()`: Create/update with JSON server configuration
- `show_http_server_profile()`: Display with formatted server details

### 23.4 Usage Examples

```bash
# Create an HTTP server profile for syslog forwarding
scm-cli set objects http-server-profile \
  --folder Texas \
  --name syslog-collector \
  --servers '[{"name": "primary-syslog", "address": "syslog.example.com", "protocol": "HTTPS", "port": 443, "http_method": "POST"}]' \
  --description "Primary syslog collector"

# Create a profile with authentication
scm-cli set objects http-server-profile \
  --folder Texas \
  --name splunk-hec \
  --servers '[{"name": "splunk-server", "address": "10.0.1.100", "protocol": "HTTPS", "port": 8088, "http_method": "POST", "username": "hec_user", "password": "secure_token"}]'

# List all profiles
scm-cli show objects http-server-profile --folder Texas --list

# Backup profiles
scm-cli backup objects http-server-profile --folder Texas
```

### 23.5 Testing Results

All commands have been tested and verified:

- ✅ Set command creates profiles with server configurations
- ✅ Show command displays server details properly
- ✅ Load command imports from YAML files
- ✅ Delete command removes profiles cleanly
- ✅ Backup command exports with field mapping (server → servers)
- ✅ SDK service name correct (http_server_profile)
- ✅ Example YAML file created with 10 different profile configurations
- ✅ Required field discovery: http_method is mandatory for all servers

## 24. Log Forwarding Profile Support

### 24.1 Problem Statement

Log forwarding profiles are critical for security operations, enabling organizations to send logs to multiple destinations for compliance, monitoring, and analysis. They provide granular control over which logs are forwarded and where they are sent.

### 24.2 Solution: Full Log Forwarding Profile Management

Implemented comprehensive support for log forwarding profiles with all CRUD operations and complex match list configurations.

#### 24.2.1 Log Forwarding Profile Features

- **Create/Update**: Support for complex match list configurations
  - Multiple match rules per profile with different log types
  - Actions: send to Panorama, syslog servers, HTTP servers, or quarantine
  - Filter expressions for granular log selection
  - Enhanced application logging support
  - Smart upsert logic for seamless updates
- **Show**: List all or display specific profiles with match list details
- **Load**: Bulk import from YAML files with validation
- **Delete**: Remove profiles by name and folder
- **Backup**: Export profiles to YAML with proper formatting

#### 24.2.2 Match List Configuration

- **Log Types**: traffic, threat, wildfire, url, data, tunnel, auth, decryption, dns-security
- **Actions**: send_to_panorama, send_syslog, send_http, quarantine
- **Filter**: Required field for match list entries (API requirement discovered during testing)

### 24.3 Technical Implementation Details

#### 24.3.1 SDK Client Methods

Added the following methods to `sdk_client.py`:

- `create_log_forwarding_profile()`: Smart upsert with automatic filter field addition
- `delete_log_forwarding_profile()`: Remove by name and folder
- `get_log_forwarding_profile()`: Fetch specific profile with match list
- `list_log_forwarding_profiles()`: List with exact_match support

#### 24.3.2 Validator Model

Created `LogForwardingProfile` model in `validators.py` with:

- Match list validation with required actions
- Log type validation against allowed values
- Proper `to_sdk_model()` method
- Support for enhanced application logging

#### 24.3.3 CLI Commands

Implemented in `objects.py`:

- `backup_log_forwarding_profile()`: Export to YAML format
- `delete_log_forwarding_profile()`: Remove by name and folder
- `load_log_forwarding_profile()`: Import with validation
- `set_log_forwarding_profile()`: Create/update with JSON match list
- `show_log_forwarding_profile()`: Display with formatted match rules

### 24.4 Usage Examples

```bash
# Create a log forwarding profile for all traffic logs
scm-cli set objects log-forwarding-profile \
  --folder Texas \
  --name all-traffic-logs \
  --match-list '[{"name": "traffic", "log_type": "traffic", "send_to_panorama": true}]' \
  --description "Forward all traffic logs to Panorama"

# Create a profile with multiple destinations
scm-cli set objects log-forwarding-profile \
  --folder Texas \
  --name security-logs \
  --match-list '[{"name": "threats", "log_type": "threat", "send_to_panorama": true, "send_syslog": ["syslog-server-1"], "filter": "severity eq high"}]' \
  --enhanced-application-logging

# List all profiles
scm-cli show objects log-forwarding-profile --folder Texas --list

# Backup profiles
scm-cli backup objects log-forwarding-profile --folder Texas
```

### 24.5 Testing Results

All commands have been tested and verified:

- ✅ Set command creates profiles with match list configurations
- ✅ Show command displays match rules with actions
- ✅ Load command imports from YAML files
- ✅ Delete command removes profiles cleanly
- ✅ Backup command exports to YAML format
- ✅ SDK service name correct (log_forwarding_profile)
- ✅ Example YAML file created with 10 different profile configurations
- ✅ Required field discovery: filter field is mandatory for match list entries

## 25. Service Object Support

### 25.1 Problem Statement

Services are fundamental building blocks for security policies, defining network protocols and ports. They enable administrators to create reusable service definitions that can be referenced in security rules, simplifying policy management and ensuring consistency.

### 25.2 Solution: Full Service Management

Implemented comprehensive support for services with all CRUD operations and protocol-specific configurations.

#### 25.2.1 Service Features

- **Create/Update**: Support for TCP and UDP protocols
  - Single ports, port ranges (e.g., 80-443), and comma-separated lists
  - Timeout overrides for TCP connections (timeout, halfclose, timewait)
  - Tag support for organization (must reference existing tag objects)
  - Smart upsert logic for seamless updates
- **Show**: List all or display specific services with protocol details
- **Load**: Bulk import from YAML files with validation
- **Delete**: Remove services by name and folder
- **Backup**: Export services to YAML with proper formatting

#### 25.2.2 Protocol Configuration

- **TCP**: Supports all port formats plus timeout overrides
- **UDP**: Supports all port formats
- **Port Formats**: Single (80), range (80-443), list (80,443,8080)

### 25.3 Technical Implementation Details

#### 25.3.1 SDK Client Methods

Added the following methods to `sdk_client.py`:

- `create_service()`: Smart upsert with protocol configuration
- `delete_service()`: Remove by name and folder
- `get_service()`: Fetch specific service with protocol details
- `list_services()`: List with exact_match support

#### 25.3.2 Validator Model

Created `Service` model in `validators.py` with:

- Protocol validation (exactly one of tcp/udp)
- Port format validation (single, range, list)
- Override settings validation for TCP
- Tag validation (1-127 characters)
- Proper `to_sdk_model()` method

#### 25.3.3 CLI Commands

Implemented in `objects.py`:

- `backup_service()`: Export to YAML format
- `delete_service()`: Remove by name and folder
- `load_service()`: Import with validation
- `set_service()`: Create/update with protocol and port options
- `show_service()`: Display with formatted protocol details

### 25.4 Usage Examples

```bash
# Create a basic TCP service
scm-cli set objects service \
  --folder Texas \
  --name custom-web \
  --protocol tcp \
  --port "8080,8443" \
  --description "Custom web service"

# Create a TCP service with timeout overrides
scm-cli set objects service \
  --folder Texas \
  --name database-service \
  --protocol tcp \
  --port "3306-3310" \
  --timeout 7200 \
  --halfclose-timeout 120 \
  --description "Database cluster with extended timeout"

# Create a UDP service
scm-cli set objects service \
  --folder Texas \
  --name custom-dns \
  --protocol udp \
  --port 5353 \
  --description "Custom DNS service"

# List all services
scm-cli show objects service --folder Texas --list

# Backup services
scm-cli backup objects service --folder Texas
```

### 25.5 Testing Results

All commands have been tested and verified:

- ✅ Set command creates services with protocol configurations
- ✅ Show command displays protocol details and overrides
- ✅ Load command imports from YAML files
- ✅ Delete command removes services cleanly
- ✅ Backup command exports to YAML format
- ✅ SDK service name correct (service)
- ✅ Example YAML file created with 10 different service configurations
- ✅ Tag validation: tags must reference existing tag objects in SCM
- ✅ Port format validation works for all supported formats

## 26. Service Group Support

### 26.1 Problem Statement

Service groups are essential for organizing related services into logical units for use in security policies. They simplify policy management by allowing administrators to reference a single group instead of multiple individual services, and support nested groups for hierarchical organization.

### 26.2 Solution: Full Service Group Management

Implemented comprehensive support for service groups with all CRUD operations and nested group support.

#### 26.2.1 Service Group Features

- **Create/Update**: Support for organizing services and service groups
  - Members can be services or other service groups (nested groups)
  - Member list must have unique values
  - Tag support for categorization (must reference existing tag objects)
  - Smart upsert logic for seamless updates
- **Show**: List all or display specific service groups with member details
- **Load**: Bulk import from YAML files with validation
- **Delete**: Remove service groups by name and folder
- **Backup**: Export service groups to YAML with proper formatting

#### 26.2.2 Member Configuration

- **Members**: List of service or service group names (minimum 1, maximum 1024)
- **Validation**: Members must be unique within the group
- **Nesting**: Service groups can contain other service groups

### 26.3 Technical Implementation Details

#### 26.3.1 SDK Client Methods

Added the following methods to `sdk_client.py`:

- `create_service_group()`: Smart upsert with member management
- `delete_service_group()`: Remove by name and folder
- `get_service_group()`: Fetch specific service group with members
- `list_service_groups()`: List with exact_match support

#### 26.3.2 Validator Model

Created `ServiceGroup` model in `validators.py` with:

- Member uniqueness validation
- Tag validation (1-127 characters)
- Name pattern validation
- Proper `to_sdk_model()` method

#### 26.3.3 CLI Commands

Implemented in `objects.py`:

- `backup_service_group()`: Export to YAML format
- `delete_service_group()`: Remove by name and folder
- `load_service_group()`: Import with validation
- `set_service_group()`: Create/update with member list
- `show_service_group()`: Display with member details

### 26.4 Usage Examples

```bash
# Create a service group
scm-cli set objects service-group \
  --folder Texas \
  --name web-services \
  --members "http,https,web-browsing,ssl"

# Create a nested service group
scm-cli set objects service-group \
  --folder Texas \
  --name all-critical-services \
  --members "database-services,infrastructure-mgmt,monitoring-services,dns,ntp" \
  --tag "critical,production"

# List all service groups
scm-cli show objects service-group --folder Texas --list

# Backup service groups
scm-cli backup objects service-group --folder Texas
```

### 26.5 Testing Results

All commands have been tested and verified:

- ✅ Set command creates service groups with member lists
- ✅ Show command displays members and tags properly
- ✅ Load command imports from YAML files with validation
- ✅ Delete command removes service groups cleanly
- ✅ Backup command exports to YAML format
- ✅ SDK service name correct (service_group)
- ✅ Example YAML file created with 10 different group configurations
- ✅ Nested service groups work correctly
- ✅ Member uniqueness validation functions properly

## 27. Syslog Server Profile Support

### 27.1 Problem Statement

Syslog server profiles are essential for centralized log collection and security monitoring. They enable organizations to send logs to external syslog servers for compliance, analysis, and long-term retention. The CLI needed comprehensive syslog server profile management to complete its logging configuration capabilities.

### 27.2 Solution: Full Syslog Server Profile Management

Implemented comprehensive support for syslog server profiles with all CRUD operations and multi-server configurations.

#### 27.2.1 Syslog Server Profile Features

- **Create/Update**: Support for multiple syslog server configurations
  - Server name, address, transport protocol, and port
  - Log format (BSD/IETF) and facility settings
  - Tag support for categorization
  - Smart upsert logic for seamless updates
- **Show**: List all or display specific profiles with server details
- **Load**: Bulk import from YAML files with validation
- **Delete**: Remove profiles by name and container
- **Backup**: Export profiles to YAML with proper formatting

#### 27.2.2 Server Configuration

- **Transport Protocols**: UDP and TCP (SSL not supported by SDK)
- **Formats**: BSD and IETF syslog formats
- **Facilities**: LOG_USER, LOG_LOCAL0-7
- **Multiple Servers**: Support for primary, secondary, and backup servers

### 27.3 Technical Implementation Details

#### 27.3.1 SDK Client Methods

Added the following methods to `sdk_client.py`:

- `create_syslog_server_profile()`: Smart upsert with server configuration handling
- `delete_syslog_server_profile()`: Remove by name and container
- `get_syslog_server_profile()`: Fetch specific profile with server details
- `list_syslog_server_profiles()`: List with exact_match support

#### 27.3.2 Validator Model

Created `SyslogServerProfile` model in `validators.py` with:

- Server list validation with required fields
- Transport protocol validation (UDP/TCP)
- Format and facility validation
- Container field validation (folder/snippet/device)
- Proper `to_sdk_model()` method

#### 27.3.3 CLI Commands

Implemented in `objects.py`:

- `backup_syslog_server_profile()`: Export to YAML format
- `delete_syslog_server_profile()`: Remove by name and container
- `load_syslog_server_profile()`: Import with validation
- `set_syslog_server_profile()`: Create/update with server configuration
- `show_syslog_server_profile()`: Display with formatted server details

### 27.4 Usage Examples

```bash
# Create a basic syslog server profile
scm-cli set objects syslog-server-profile test-syslog \
  --server-name test-server \
  --server-address 192.168.1.100 \
  --transport UDP \
  --port 514 \
  --format BSD \
  --facility LOG_USER \
  --description "Test syslog profile"

# List all profiles
scm-cli show objects syslog-server-profile --list

# Backup profiles
scm-cli backup objects syslog-server-profile --file /tmp/syslog-backup.yml
```

### 27.5 Testing Results

All commands have been tested and verified:

- ✅ Set command creates profiles with server configurations
- ✅ Show command displays server details properly
- ✅ Load command imports from YAML files
- ✅ Delete command removes profiles cleanly
- ✅ Backup command exports to YAML format
- ✅ SDK service name correct (syslog_server_profile)
- ✅ Example YAML file created with 10 different profile configurations
- ✅ SSL transport limitation discovered (SDK only supports UDP/TCP)

## 28. Tag Support

### 28.1 Problem Statement

Tags are fundamental for organizing and categorizing configuration objects across SCM. They enable administrators to apply consistent labeling, facilitate policy management, and improve visibility across large deployments. The CLI needed comprehensive tag management to support this critical organizational feature.

### 28.2 Solution: Full Tag Management

Implemented comprehensive support for tags with all CRUD operations and color categorization.

#### 28.2.1 Tag Features

- **Create/Update**: Support for tag creation with colors and comments
  - 42 predefined colors from Palo Alto Networks palette
  - Comments for detailed descriptions
  - Container support (folder/snippet/device)
  - Smart upsert logic for seamless updates
- **Show**: List all or display specific tags with color and comments
- **Load**: Bulk import from YAML files with validation
- **Delete**: Remove tags by name and container
- **Backup**: Export tags to YAML with proper formatting

#### 28.2.2 Color Support

The following colors are supported:
Azure Blue, Black, Blue, Blue Gray, Blue Violet, Brown, Burnt Sienna, Cerulean Blue, Chestnut, Cobalt Blue, Copper, Cyan, Forest Green, Gold, Gray, Green, Lavender, Light Gray, Light Green, Lime, Magenta, Mahogany, Maroon, Medium Blue, Medium Rose, Medium Violet, Midnight Blue, Olive, Orange, Orchid, Peach, Purple, Red, Red Violet, Red-Orange, Salmon, Thistle, Turquoise Blue, Violet Blue, Yellow, Yellow-Orange

### 28.3 Technical Implementation Details

#### 28.3.1 SDK Client Methods

Added the following methods to `sdk_client.py`:

- `create_tag()`: Smart upsert with color validation
- `delete_tag()`: Remove by name and container
- `get_tag()`: Fetch specific tag with details
- `list_tags()`: List with exact_match support

#### 28.3.2 Validator Model

Created `Tag` model in `validators.py` with:

- Name pattern validation
- Color validation against allowed list
- Comments field with length constraints
- Container field validation
- Proper `to_sdk_model()` method

#### 28.3.3 CLI Commands

Implemented in `objects.py`:

- `backup_tag()`: Export to YAML format
- `delete_tag()`: Remove by name and container
- `load_tag()`: Import with validation
- `set_tag()`: Create/update with color and comments
- `show_tag()`: Display with color and comment details

### 28.4 Usage Examples

```bash
# Create a tag with color
scm-cli set objects tag test-tag --color Blue --comments "Test tag for CLI"

# Create environment tags
scm-cli set objects tag Production --color Red --comments "Production environment"
scm-cli set objects tag Development --color Green --comments "Development environment"

# List all tags
scm-cli show objects tag --list

# Backup tags
scm-cli backup objects tag --file /tmp/tags-backup.yml
```

### 28.5 Testing Results

All commands have been tested and verified:

- ✅ Set command creates tags with colors and comments
- ✅ Show command displays tag details properly
- ✅ Load command imports from YAML files
- ✅ Delete command removes tags cleanly
- ✅ Backup command exports to YAML format
- ✅ SDK service name correct (tag)
- ✅ Example YAML file created with comprehensive tag configurations
- ✅ Color validation works for all 42 supported colors

## 29. Command Styling Guidelines

### 29.1 Overview

A comprehensive command styling guide has been created to ensure consistency across all CLI command modules. The guide is located at `src/scm_cli/commands/command-styling.md` and documents the patterns observed in the address, address-group, and application object implementations.

### 29.2 Key Styling Principles

#### 29.2.1 Module Structure

- Comprehensive module docstrings with command lists and examples
- Organized imports (standard library, third-party, local)
- Consistent 191-character section separators

#### 29.2.2 Command Organization

- Separate Typer apps for each action type (set, delete, load, show, backup)
- Consistent command order per object type
- Common options defined as constants for reusability

#### 29.2.3 Implementation Patterns

- Standardized patterns for each command type (backup, delete, load, set, show)
- Consistent error handling with user-friendly messages
- Proper type hints using Python 3.10+ syntax

#### 29.2.4 Output Formatting

- Consistent success message formats
- Structured list and detail output formats
- Clear error messages with exit codes

### 29.3 Benefits

1. **Consistency**: All commands follow the same patterns
2. **Maintainability**: Easy to add new object types following the guide
3. **Readability**: Developers can quickly understand any command module
4. **User Experience**: Consistent CLI behavior across all commands

## 30. Backup Command Standardization

### 30.1 Problem Statement

The initial backup command implementation only supported folder-based backups. With the growing need to support multiple container types (folder, snippet, device) across SCM, the backup commands needed to be standardized to provide consistent parameter handling and flexibility.

### 30.2 Solution: Standardized Backup Parameters

All backup commands have been updated to support a consistent set of parameters:

#### 30.2.1 Standard Parameters

- **--folder**: Backup from a specific folder location
- **--snippet**: Backup from a snippet (code template) location
- **--device**: Backup from a device-specific location
- **--file**: Custom output filename (optional, defaults to generated name)

#### 30.2.2 Parameter Validation

- Exactly one location parameter (folder, snippet, or device) must be specified
- Clear error messages guide users when parameters are missing or conflicting
- Validation logic is centralized in helper functions for consistency

### 30.3 Technical Implementation Details

#### 30.3.1 Helper Functions

```python
def validate_location_params(folder: str = None, snippet: str = None, device: str = None) -> tuple[str, str]:
    """Validate that exactly one location parameter is provided."""

def get_default_backup_filename(object_type: str, location_type: str, location_value: str) -> str:
    """Generate default backup filename with timestamp."""
```

#### 30.3.2 SDK Client Updates

All list methods in `sdk_client.py` now accept optional folder, snippet, and device parameters:

```python
def list_addresses(
    self,
    folder: str | None = None,
    snippet: str | None = None,
    device: str | None = None,
    exact_match: bool = False,
) -> list[dict[str, Any]]:
```

#### 30.3.3 Kwargs Pattern

Backup commands use the kwargs pattern for cleaner API calls:

```python
kwargs = {location_type: location_value}
items = scm_client.list_items(**kwargs, exact_match=True)
```

### 30.4 Benefits

1. **Flexibility**: Support for all SCM container types (folder, snippet, device)
2. **Consistency**: Same parameter pattern across all backup commands
3. **User-Friendly**: Clear validation messages and sensible defaults
4. **Future-Proof**: Easy to add new location types without changing command signatures
5. **Clean API**: Kwargs pattern only passes necessary parameters

### 30.5 Usage Examples

```bash
# Backup from different container types
scm-cli backup objects address --folder Austin
scm-cli backup objects tag --snippet DNS-Best-Practice
scm-cli backup objects service --device austin-01

# Custom output filename
scm-cli backup objects address-group --folder Texas --file my-groups.yaml

# Automatic filename generation
# Creates: address_folder_austin_20240115_143022.yaml
scm-cli backup objects address --folder Austin
```

## 31. Load Command Standardization

### 31.1 Problem Statement

Load commands across different object types had significant inconsistencies that made the CLI difficult to use and maintain:

- Different parameter types (Path vs str)
- Inconsistent container override support
- Varying file validation methods
- Different error handling approaches
- Inconsistent output formats

### 31.2 Solution: Standardized Load Command Pattern

All load commands have been standardized to follow a consistent pattern with these key features:

#### 31.2.1 Standard Parameters

```python
@load_app.command("object-type", help="Load {object_type}s from a YAML file.")
def load_object_type(
    file: Path = FILE_OPTION,
    dry_run: bool = DRY_RUN_OPTION,
    folder: str = LOAD_FOLDER_OPTION,
    snippet: str = LOAD_SNIPPET_OPTION,
    device: str = LOAD_DEVICE_OPTION,
):
```

#### 31.2.2 Container Override Support

All load commands now support overriding the container location for all objects in a file:

- `--folder`: Override folder location for all objects
- `--snippet`: Override snippet location for all objects
- `--device`: Override device location for all objects

#### 31.2.3 Standardized Implementation Pattern

1. Help text in decorator
2. Container parameter validation
3. File existence check using `file.exists()`
4. Direct YAML loading with `yaml.safe_load()`
5. Container override logic in loops
6. Count-based output format
7. Error handling with continue
8. Return list of results

### 31.3 Technical Implementation Details

#### 31.3.1 Container Override Options

```python
LOAD_FOLDER_OPTION = typer.Option(None, "--folder", help="Override folder location for all objects")
LOAD_SNIPPET_OPTION = typer.Option(None, "--snippet", help="Override snippet location for all objects")
LOAD_DEVICE_OPTION = typer.Option(None, "--device", help="Override device location for all objects")
```

#### 31.3.2 Container Override Logic

```python
# Apply container overrides if specified
if folder:
    obj_data["folder"] = folder
    obj_data.pop("snippet", None)
    obj_data.pop("device", None)
elif snippet:
    obj_data["snippet"] = snippet
    obj_data.pop("folder", None)
    obj_data.pop("device", None)
elif device:
    obj_data["device"] = device
    obj_data.pop("folder", None)
    obj_data.pop("snippet", None)
```

#### 31.3.3 Standardized Output Format

```python
# Display summary with counts
typer.echo(f"Successfully processed {len(results)} {object_type}(s)")
if created_count > 0:
    typer.echo(f"  - Created: {created_count}")
if updated_count > 0:
    typer.echo(f"  - Updated: {updated_count}")
```

### 31.4 Benefits

1. **Consistency**: All load commands work the same way across object types
2. **Flexibility**: Container overrides enable bulk migrations between locations
3. **User Experience**: Consistent parameters and output formats
4. **Error Resilience**: Continue processing on individual failures
5. **Dry Run Support**: Preview changes before applying them

### 31.5 Commands Updated

All 14 load commands have been standardized:

- ✅ address-group
- ✅ application
- ✅ application-group
- ✅ application-filter
- ✅ dynamic-user-group
- ✅ external-dynamic-list
- ✅ hip-object
- ✅ hip-profile
- ✅ http-server-profile
- ✅ log-forwarding-profile
- ✅ service
- ✅ service-group
- ✅ syslog-server-profile
- ✅ tag

### 31.6 Usage Examples

```bash
# Load with original locations from file
scm-cli load objects address --file addresses.yml

# Override all objects to a specific folder
scm-cli load objects address --file addresses.yml --folder Production

# Override to snippet location
scm-cli load objects service --file services.yml --snippet DNS-Best-Practice

# Dry run to preview changes
scm-cli load objects tag --file tags.yml --dry-run

# Container override with dry run
scm-cli load objects application --file apps.yml --folder Texas --dry-run
```

## 32. Decryption Profile Support

### 32.1 Problem Statement

Decryption profiles are critical for SSL/TLS inspection in modern security architectures. They enable organizations to inspect encrypted traffic for threats while maintaining control over which traffic to decrypt based on security and privacy requirements. The CLI needed comprehensive decryption profile management to support SSL forward proxy, SSL inbound proxy, and no-decrypt scenarios.

### 32.2 Solution: Full Decryption Profile Management

Implemented comprehensive support for decryption profiles with all CRUD operations and flexible SSL/TLS configuration options.

#### 32.2.1 Decryption Profile Features

- **Create/Update**: Support for multiple proxy types and SSL protocol settings
  - SSL Forward Proxy: Client-to-server traffic inspection
  - SSL Inbound Proxy: Server-to-client traffic inspection
  - SSL No Proxy: Bypass decryption for specific traffic
  - SSL Protocol Settings: Control supported protocols and cipher suites
  - Smart upsert logic for seamless updates
- **Show**: List all or display specific profiles with configuration details
- **Load**: Bulk import from YAML files with validation
- **Delete**: Remove profiles by name and container
- **Backup**: Export profiles to YAML with proper formatting

#### 32.2.2 Proxy Type Configurations

1. **SSL Forward Proxy**: Controls decryption of outbound SSL/TLS traffic

   - Certificate validation options (expired, untrusted, unknown)
   - Client certificate handling
   - TLS 1.3 downgrade behavior
   - ALPN stripping

2. **SSL Inbound Proxy**: Controls decryption of inbound SSL/TLS traffic

   - HSM availability handling
   - Resource availability checks
   - Cipher and version support

3. **SSL No Proxy**: Defines traffic that should not be decrypted

   - Certificate validation bypass options

4. **SSL Protocol Settings**: Fine-grained control over SSL/TLS parameters
   - Minimum and maximum TLS versions
   - Authentication algorithms (MD5, SHA1, SHA256, SHA384)
   - Encryption algorithms (3DES, AES variants, ChaCha20-Poly1305, RC4)
   - Key exchange algorithms (DHE, ECDHE, RSA)

### 32.3 Technical Implementation Details

#### 32.3.1 SDK Client Methods

Added the following methods to `sdk_client.py`:

- `create_decryption_profile()`: Smart upsert with proxy type configuration
- `delete_decryption_profile()`: Remove by name and container
- `get_decryption_profile()`: Fetch specific profile with all settings
- `list_decryption_profiles()`: List with exact_match support

#### 32.3.2 Validator Model

Created `DecryptionProfile` model in `validators.py` with:

- Container validation (folder/snippet/device)
- Proxy type validation (at least one required)
- SSL version ordering validation
- Proper `to_sdk_model()` method

#### 32.3.3 CLI Commands

Implemented in `security.py`:

- `backup_decryption_profile()`: Export to YAML format
- `delete_decryption_profile()`: Remove by name and container
- `load_decryption_profile()`: Import with validation
- `set_decryption_profile()`: Create/update with JSON configuration
- `show_decryption_profile()`: Display with formatted settings

### 32.4 Usage Examples

```bash
# Create SSL forward proxy profile
scm-cli set security decryption-profile --folder Texas --name ssl-forward \
  --ssl-forward-proxy '{"block_expired_certificate": true, "block_untrusted_issuer": true}'

# Create SSL inbound inspection profile
scm-cli set security decryption-profile --folder Texas --name ssl-inbound \
  --ssl-inbound-proxy '{"block_if_no_resource": true, "block_unsupported_cipher": true}'

# Create no-decrypt profile for sensitive traffic
scm-cli set security decryption-profile --folder Texas --name no-decrypt-medical \
  --ssl-no-proxy '{"block_expired_certificate": false, "block_untrusted_issuer": false}'

# Create profile with custom protocol settings
scm-cli set security decryption-profile --folder Texas --name secure-decrypt \
  --ssl-forward-proxy '{"block_expired_certificate": true}' \
  --ssl-protocol-settings '{"min_version": "tls1-2", "max_version": "tls1-3", "enc_algo_rc4": false}'

# List all profiles
scm-cli show security decryption-profile --folder Texas --list

# Show specific profile details
scm-cli show security decryption-profile --folder Texas --name ssl-forward

# Backup profiles
scm-cli backup security decryption-profile --folder Texas

# Load profiles from YAML
scm-cli load security decryption-profile --file decryption-profiles.yml
```

### 32.5 Testing Results

All commands have been tested and verified:

- ✅ Set command creates profiles with all proxy types
- ✅ Show command displays detailed configuration settings
- ✅ Load command imports from YAML files correctly
- ✅ Delete command removes profiles cleanly
- ✅ Backup command exports to YAML format
- ✅ Example YAML file created with various profile configurations
