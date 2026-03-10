# Release Notes

This page contains the release history of the Strata Cloud Manager CLI, with the most recent releases at the top.

## Version 1.0.7

**Released:** March 10, 2026

### Fixed

- **Error Logging**: Fixed 23 `_handle_api_exception()` calls with swapped `folder` and `resource_name` arguments, correcting error messages for service connections, remote networks, HIP profiles, HTTP server profiles, log forwarding profiles, services, service groups, internal DNS servers, and network locations.
- **Deprecated API**: Replaced 3 deprecated Pydantic v1 `.dict()` calls with `.model_dump_json()` in address group, security zone, and security rule creation methods.

## Version 1.0.6

**Released:** March 9, 2026

### Added

- **QoS Profile Folder Validation**: CLI now validates that QoS profiles only accept `Remote Networks` or `Service Connections` as folder values, matching SCM API enforcement. Invalid folders produce a clear error message instead of an API 400 response.

## Version 1.0.5

**Released:** March 9, 2026

### Fixed

- **Type Safety**: Resolved all 13 mypy type errors in `network.py` — IKE crypto profile, IKE gateway, and IPsec crypto profile model construction now uses correct typed kwargs.
- **CI Enforcement**: mypy type checking now blocks PRs (removed `continue-on-error`).

## Version 1.0.4

**Released:** March 9, 2026

### Changed

- **SDK Dependency**: Bumped `pan-scm-sdk` from `^0.12.0` to `^0.12.2`, picking up AutoTagActions service implementation and DecryptionRule optional action field fix.
- **Version Tracking**: `__version__` now sourced from package metadata via `importlib.metadata` instead of a hardcoded string.

## Version 1.0.3

**Released:** March 9, 2026

### Added

- **Delete Confirmation Prompts**: All delete commands now prompt for confirmation before proceeding. Use `--force` to skip the prompt for scripting and automation.

### Fixed

- **Stale References**: Removed deprecated `scm test-auth` reference from CLI help text (now `scm context test`).
- **Config Mismatch**: Updated `mypy.ini` to target Python 3.12 (was incorrectly set to 3.10).
- **Documentation**: Fixed CLI syntax in address docs, corrected repository link in release notes.

## Version 0.5.1

**Released:** June 19, 2025

### Added

- **Bandwidth Allocation Smart-Upsert**: `set sase bandwidth-allocation` now performs create-or-update with field-level change detection and returns `__action__` (`created`, `updated`, `no_change`).

### Changed

- **Field Cleanup**: Bandwidth allocations no longer accept or display a `description` attribute. CLI options, validators, and SDK client have been updated accordingly.
- **CLI Error Handling**: Deleting bandwidth allocations now gracefully accepts both comma-separated strings and Python lists for `--spn-name-list`.

### Fixed

- Resolved `'list' object has no attribute 'split'` error when deleting bandwidth allocations with a single SPN.

## Version 0.5.0

**Released:** June 9, 2025

### Added

- **Smart Upsert Functionality**: Comprehensive intelligent object management across all resources
    - **Field-level Change Detection**: Only updates objects when actual changes are detected
        - Compares existing object configuration with proposed changes
        - Skips updates when objects are already up-to-date
        - Logs specific fields being updated for transparency
    - **Action Tracking**: Clear feedback on operations performed
        - Returns `"created"` for new objects
        - Returns `"updated"` for modified objects
        - Returns `"no_change"` for objects already up-to-date
    - **Unified Pattern**: Applied consistently across all object types including services, tags, addresses, security rules, and SASE resources

- **Enhanced SASE Integration**: Merged comprehensive SASE deployment features
    - **Service Connections**: Full CRUD operations with smart upsert support
        - Create/update with BGP peering, QoS, and NAT configurations
        - Automatic folder enforcement ("Service Connections" folder only)
        - List, show, delete, load, and backup operations
    - **Remote Networks**: Complete management with intelligent updates
        - Support for ECMP load balancing and IPsec tunnel configurations
        - Automatic folder enforcement ("Remote Networks" folder only)
        - Full CRUD, list, show, load, and backup functionality
    - All SASE commands follow the pattern: `scm <action> sase <resource-type>`

### Changed

- **Update Logic**: All object creation methods now use smart upsert pattern
    - `create_service()`, `create_tag()`, `create_address()` and others now check for existing objects
    - Only performs API updates when changes are detected
    - Provides clear feedback on actions taken

- **CLI Output**: Enhanced user feedback with action-specific messages
    - Shows "Created [object]: [name]" for new objects
    - Shows "Updated [object]: [name]" with field details for modifications
    - Shows "[Object] '[name]' already up to date" when no changes needed

### Improved

- **Performance**: Reduced unnecessary API calls through change detection
- **User Experience**: Clear visibility into what operations are being performed with detailed logging

### Examples

#### Smart Upsert in Action

```bash
# First run - creates new service connection
$ scm set sase service-connection \
    --name test-sc \
    --ipsec-tunnel tunnel-1 \
    --region us-east-1
---> 100%
Created service connection: test-sc

# Second run with same parameters - no changes needed
$ scm set sase service-connection \
    --name test-sc \
    --ipsec-tunnel tunnel-1 \
    --region us-east-1
---> 100%
Service connection 'test-sc' already up to date

# Third run with different parameter - updates only changed field
$ scm set sase service-connection \
    --name test-sc \
    --ipsec-tunnel tunnel-1 \
    --region us-east-1 \
    --bgp-enable
---> 100%
Updated service connection: test-sc
```

## Version 0.4.1

**Released:** June 9, 2025

### Added

- **Lazy Client Initialization**: SDK client is now initialized only when needed
    - Faster CLI startup for commands that don't require API access (e.g., `--help`)
    - Improved resource efficiency for scripting and automation

- **Enhanced Authentication Error Handling**: Graceful handling of authentication failures
    - Specific detection for `InvalidClientError` from OAuth library
    - Clear, actionable error messages with context information
    - Provides exact command to fix credential issues

### Changed

- **CLI Command Syntax**: Unified all object-related commands to use singular form
    - Changed from `scm <action> objects <type>` to `scm <action> object <type>`
    - **Migration**: Update scripts to use `object` instead of `objects`

- **Deployment Module Renamed**: Changed from "deployment" to "sase" for clarity
    - All deployment commands now use `scm <action> sase <resource>`
    - **Migration**: Update scripts using `deployment` to use `sase`

### Improved

- **Cleaner Output**: Suppressed verbose authentication logging from SDK and OAuth libraries
- **Context Test Command**: Enhanced error handling and feedback with clear success/failure indicators

### Fixed

- **Address Creation Without Description**: Fixed validation error when creating addresses without providing a description

### Examples

#### Object Commands (New Syntax)

```bash
# New syntax
$ scm show object address --folder Texas
$ scm set object tag --folder Texas --name production --color Red
$ scm backup object service --folder Texas
```

## Version 0.4.0

**Released:** TBD

### Added

- **Multi-tenant Context Management**: Comprehensive authentication context system
    - New `scm context` command group with subcommands: `create`, `list`, `use`, `delete`, `show`, `current`, `test`
    - Context-based authentication takes precedence over environment variables
    - Secure credential storage in `~/.scm-cli/contexts/` directory
    - Seamless Docker integration with volume mounting support

### Changed

- **Show Commands Default Behavior**: All `show` commands now list all items by default when no `--name` parameter is provided. The `--list` flag has been removed.
    - **Migration**: Remove `--list` from existing scripts

- **Authentication Precedence**: Active context now takes precedence; removed support for legacy config files

### Removed

- **test-auth Command**: Replaced with `scm context test`
- **Legacy Config Files**: No longer loads `~/.scm-cli/config.yaml` or `.secrets.yaml`

### Examples

#### Context Management

```bash
$ scm context create production \
    --client-id "prod@123456789.iam.panserviceaccount.com" \
    --client-secret "your-secret" \
    --tsg-id "123456789"
---> 100%
✓ Context 'production' created successfully

$ scm context use production
✓ Switched to context 'production'

$ scm context test
✓ Authentication successful!
```

## Version 0.3.39

**Released:** March 29, 2025

### Fixed

- **Security Rule Move Operation**: Fixed UUID serialization issue in the `.move()` method of `SecurityRule` class

## Version 0.3.22

**Released:** March 18, 2025

### Added

- **Mobile Agent Features**: Support for managing GlobalProtect agent versions and authentication settings

### Fixed

- **Documentation**: Fixed inconsistencies between code and documentation regarding client service property names

## Version 0.3.21

**Released:** March 16, 2025

### Added

- **Bandwidth Allocations**: Support for managing bandwidth allocation across service provider networks
- **BGP Routing**: Support for configuring and managing BGP routing
- **Internal DNS Servers**: Support for configuring internal DNS servers
- **Network Locations**: Support for managing network locations

## Version 0.3.20

**Released:** March 13, 2025

### Fixed

- **Security Zone**: Added workaround for inconsistent API response format in the `fetch()` method

## Version 0.3.19

**Released:** March 12, 2025

### Added

- **NAT Rules**: Support for managing NAT rules

## Version 0.3.18

**Released:** March 8, 2025

### Added

- **Service Connections**: Support for managing Service Connection objects with full CRUD, pagination, and validation

## Version 0.3.17

**Released:** March 7, 2025

### Added

- **IKE Crypto Profile**: Support for managing IKE Crypto Profiles
- **IKE Gateway**: Support for managing IKE Gateways
- **IPsec Crypto Profile**: Support for managing IPsec Crypto Profiles

## Version 0.3.16

**Released:** March 6, 2025

### Added

- **Security Zone**: Support for managing Security Zones

### Fixed

- **Custom Token URL Support**: Fixed issue where `token_url` parameter was not exposed through constructors

## Version 0.3.15

**Released:** March 2, 2025

### Added

- **HTTP Server Profile**: Support for managing HTTP Server Profiles
- **Log Forwarding Profile**: Support for managing Log Forwarding Profiles
- **SYSLOG Server Profile**: Support for managing SYSLOG Server Profiles

## Version 0.3.14

**Released:** February 28, 2025

### Added

- **Unified Client Interface**: New attribute-based access pattern for services
- **ScmClient Class**: Added as an alias for the Scm class

## Version 0.3.13

**Released:** February 22, 2025

### Added

- **HTTP Server Profiles**: Support for managing HTTP server profiles

## Version 0.3.12

**Released:** February 18, 2025

### Added

- **Dynamic User Groups**: Support for managing dynamic user groups
- **HIP Profiles**: Support for managing HIP profiles

## Version 0.3.11

**Released:** February 15, 2025

### Added

- **Commit Enhancement**: Support for passing "all" to a commit to specify all admin users

## Version 0.3.10

**Released:** February 12, 2025

### Added

- **Security Rule Enhancement**: Support for new security rule types of SWG

## Version 0.3.9

**Released:** February 8, 2025

### Added

- **NAT Rules**: Support for managing NAT rules

## Version 0.3.8

**Released:** February 5, 2025

### Added

- **Remote Networks**: Support for managing remote networks
- **SASE API Integration**: First time leveraging SASE APIs

## Version 0.3.7

**Released:** February 2, 2025

### Added

- **HIP Objects**: Support for managing HIP objects

## Version 0.3.6

**Released:** January 28, 2025

### Added

- **Pagination**: Auto-pagination when using the `list()` method
- **Request Control**: Support for controlling the maximum number of objects returned (default: 2500, max: 5000)

## Version 0.3.5

**Released:** January 25, 2025

### Added

- **Advanced Filtering**: Support for advanced filtering capabilities

## Version 0.3.4

**Released:** January 22, 2025

### Added

- **External Dynamic Lists**: Support for managing External Dynamic Lists
- **Auto Tag Actions**: Support for Auto Tag Actions

## Version 0.3.3

**Released:** January 18, 2025

### Added

- **URL Categories**: Support for managing URL Categories

## Version 0.3.2

**Released:** January 15, 2025

### Added

- **Commit Operations**: Support for performing commits
- **Job Status**: Support for pulling in job status

## Version 0.3.1

**Released:** January 12, 2025

### Added

- **Service Group Objects**: Support for managing Service Group objects

## Version 0.3.0

**Released:** January 8, 2025

### Added

- **Tag Objects**: Support for managing tag objects
- **Model Integration**: `fetch()` returns a Pydantic modeled object
- **Model Update**: `update()` supports passing Pydantic modeled objects

### Changed

- **Exceptions**: Refactored exception handling
- **Logging**: Refactored logging system

### Fixed

- **OAuth Client**: Fixed issue with refresh_token handling

## Version 0.2.1

**Released:** March 30, 2025

### Fixed

- **Typer Compatibility**: Upgraded Typer from 0.11.1 to 0.15.2, fixing compatibility issues with Python 3.10+ type annotations

## Version 0.2.0

**Released:** December 28, 2024

### Added

- **Fetch Method**: Added `fetch` method to various profile and object classes
- **Model Updates**: Introduced `AntiSpywareProfileUpdateModel`

### Changed

- **Update Methods**: Refactored update methods to use `data['id']` directly
- **Model Architecture**: Refactored Address models for separate base, create, update, and response logic

## Version 0.1.17

**Released:** December 25, 2024

### Added

- **Rule Movement**: Added `move` method for moving security rules within the rule base

## Version 0.1.16

**Released:** December 22, 2024

### Fixed

- **Create Method**: Updated `create` method to ensure missing dictionary keys are set with default values

## Version 0.1.15

**Released:** December 18, 2024

### Changed

- **Pattern Support**: Updated pattern to support periods (.) in security policy names

## Version 0.1.14

**Released:** December 15, 2024

### Added

- **Security Rules**: Support for Security Rules configuration

## Version 0.1.13

**Released:** December 12, 2024

### Added

- **Decryption Profiles**: Support for Decryption Profiles

## Version 0.1.12

**Released:** December 8, 2024

### Added

- **DNS Security Profiles**: Support for DNS Security Profiles

## Version 0.1.11

**Released:** December 5, 2024

### Added

- **Vulnerability Protection Profiles**: Support for Vulnerability Protection Profiles

## Version 0.1.10

**Released:** December 2, 2024

### Fixed

- **API Response Handling**: Support for empty API responses for PUT updates

## Version 0.1.9

**Released:** November 28, 2024

### Added

- **Wildfire Antivirus**: Support for managing Wildfire Anti-Virus Security Profiles

## Version 0.1.8

**Released:** November 25, 2024

### Added

- **Testing**: Added tests to support Anti Spyware Profiles

## Version 0.1.7

**Released:** November 22, 2024

### Added

- **Anti Spyware Profiles**: Support for Anti Spyware Profiles

## Version 0.1.6

**Released:** November 18, 2024

### Changed

- **Logging**: Changed default logging level to INFO

## Version 0.1.5

**Released:** November 15, 2024

### Added

- **Address Groups**: Support for Address Groups

## Version 0.1.4

**Released:** November 12, 2024

### Added

- **Services**: Support for Services

## Version 0.1.3

**Released:** November 8, 2024

### Added

- **Applications**: Support for Applications

## Version 0.1.2

**Released:** November 5, 2024

### Changed

- **Refactoring**: Simplified naming conventions across the project

## Version 0.1.1

**Released:** November 2, 2024

### Changed

- **Architecture**: Transitioned the project to an object-oriented structure

## Version 0.1.0

**Released:** October 30, 2024

### Added

- **Initial Release**: Developer version of `pan-scm-sdk`

---

For more detailed information on each release, visit the [GitHub repository](https://github.com/cdot65/pan-scm-cli/releases) or check the [commit history](https://github.com/cdot65/pan-scm-cli/commits/main).
