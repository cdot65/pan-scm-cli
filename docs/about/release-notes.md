# Release Notes

This page contains the release history of the Strata Cloud Manager CLI, with the most recent releases at the top.

## Version 0.4.1 (Unreleased)

**Released:** June 9, 2025

### Added

- **SASE Deployment Commands**: Comprehensive support for SASE (Secure Access Service Edge) deployment configuration
  - **Service Connections**: Full CRUD operations for Service Connection management
    - Create/update with BGP peering, QoS, and NAT configurations
    - Automatic folder enforcement ("Service Connections" folder only)
    - List, show, delete, load, and backup operations
  - **Remote Networks**: Complete management for Remote Network configurations
    - Support for ECMP load balancing and IPsec tunnel configurations
    - Automatic folder enforcement ("Remote Networks" folder only)
    - Full CRUD, list, show, load, and backup functionality
  - All SASE commands follow the pattern: `scm <action> sase <resource-type>`

- **Lazy Client Initialization**: SDK client is now initialized only when needed
  - Significantly faster CLI startup for commands that don't require API access (e.g., `--help`)
  - Improved resource efficiency for scripting and automation
  - Better error isolation - authentication errors only occur during actual API usage

- **Enhanced Authentication Error Handling**: Graceful handling of authentication failures
  - Specific detection for `InvalidClientError` from OAuth library
  - Clear, actionable error messages with context information
  - Shows current context, client ID, and TSG ID (with client secret masked)
  - Provides exact command to fix credential issues

### Changed

- **CLI Command Syntax**: Unified all object-related commands to use singular form
  - Changed from `scm <action> objects <type>` to `scm <action> object <type>`
  - Affects all object commands: address, address-group, application, service, tag, etc.
  - **Migration**: Update scripts to use `object` instead of `objects`
  - Example: `scm show objects address` → `scm show object address`

- **Deployment Module Renamed**: Changed from "deployment" to "sase" for clarity
  - All deployment commands now use `scm <action> sase <resource>`
  - Better reflects the SASE-specific nature of these resources
  - **Migration**: Update scripts using `deployment` to use `sase`

### Improved

- **Cleaner Output**: Suppressed verbose authentication logging from SDK and OAuth libraries
  - Removed noisy debug messages during authentication
  - Log levels set to CRITICAL for `scm.auth` and `oauthlib` loggers
  - Cleaner, more professional output for end users

- **Context Test Command**: Enhanced error handling and feedback
  - Better detection of invalid credentials
  - Clear success/failure indicators with emojis (✓/❌)
  - Actionable guidance for troubleshooting

### Technical Details

- Implemented `LazyClient` wrapper class that delays SDK initialization
- Enhanced `_handle_api_exception()` method with specific error detection
- Improved logging configuration for cleaner output
- Added hardcoded folder constraints for Service Connections and Remote Networks
- Updated all documentation to reflect new command syntax

### Examples

#### SASE Commands
```bash
# Service Connections
scm set sase service-connection --name datacenter-1 --auto_vpn_monitor_enabled
scm show sase service-connection --name datacenter-1
scm list sase service-connections
scm backup sase service-connections

# Remote Networks
scm set sase remote-network --name branch-1 --region us-east-1
scm show sase remote-network --name branch-1
scm list sase remote-networks
scm backup sase remote-networks
```

#### Object Commands (New Syntax)
```bash
# Old syntax (no longer supported)
scm show objects address --folder Texas

# New syntax
scm show object address --folder Texas
scm set object tag --folder Texas --name production --color Red
scm backup object service --folder Texas
```

#### Authentication Error
```
❌ Authentication failed: Invalid client credentials

Current context: production
Client ID: abc123...
TSG ID: 456789...
Client Secret: ****

Please check your credentials and try again.
You can update the context with:
  scm context create production --client-id <id> --client-secret <secret> --tsg-id <tsg>
```

## Version 0.4.0 (Unreleased)

**Released:** TBD

### Added

- **Multi-tenant Context Management**: Comprehensive authentication context system for managing multiple SCM tenants
  - New `scm context` command group with subcommands: create, list, use, delete, show, current, test
  - Context-based authentication takes precedence over environment variables
  - Secure credential storage in `~/.scm-cli/contexts/` directory
  - Seamless Docker integration with volume mounting support
  - Informational logging shows active context during operations
  - Test authentication without switching contexts

### Changed

- **Show Commands Default Behavior**: Updated all `show` commands to make listing the default behavior
  - Removed the `--list` flag from all show commands across objects, network, security, and deployment modules
  - When no `--name` parameter is provided, the command now lists all items by default
  - This change affects all 20+ show commands including addresses, address groups, applications, services, tags, security zones, rules, and more
  - **Migration**: If you have scripts using `--list`, simply remove the flag - the behavior remains the same

- **Authentication Precedence**: Fixed authentication order to prioritize contexts
  - Active context (set via `scm context use`) now takes precedence
  - Environment variables can still override for CI/CD scenarios
  - Removed support for legacy config files (`~/.scm-cli/config.yaml` and `.secrets.yaml`)
  - **Migration**: Create contexts for your existing configurations using `scm context create`

### Removed

- **test-auth Command**: Replaced with `scm context test` for enhanced functionality
- **Legacy Config Files**: No longer loads `~/.scm-cli/config.yaml` or `.secrets.yaml`

### Examples

#### Context Management
```bash
# Create a context for production
scm context create production \
  --client-id "prod@123456789.iam.panserviceaccount.com" \
  --client-secret "your-secret" \
  --tsg-id "123456789"

# Switch to production context
scm context use production

# Test authentication
scm context test

# Docker integration
docker run -d --name pan-scm \
  -v ~/.scm-cli:/home/scmuser/.scm-cli \
  ghcr.io/cdot65/pan-scm-cli:latest
```

#### Show Commands
```bash
# Old syntax (no longer supported)
scm show object address --folder Texas --list

# New syntax (lists all by default)
scm show object address --folder Texas

# Show specific item (unchanged)
scm show object address --folder Texas --name web-server
```

## Version 0.3.39

**Released:** March 29, 2025

### Fixed

- **Security Rule Move Operation**: Fixed UUID serialization issue in the `.move()` method of `SecurityRule` class
  - Previously, when a UUID object was passed as `destination_rule` parameter, JSON serialization would fail
  - Now properly converts UUID objects to strings before sending to the API
- **Example Scripts**: Added example script for testing security rule move operations
  - Demonstrates proper handling of UUID serialization
  - Includes improved error handling for edge cases

## Version 0.3.22

**Released:** March 18, 2025

### Added

- **Mobile Agent Features**:
  - **Agent Versions**: Support for managing GlobalProtect agent versions
  - **Authentication Settings**: Support for configuring GlobalProtect authentication settings

### Fixed

- **API Endpoint Path**: Fixed 404 error in agent_versions API endpoint path by adding missing '/config' prefix
- **Documentation**: Fixed inconsistencies between code and documentation regarding client service property names
  - Corrected references from `client.auth_settings` to `client.auth_setting`
  - Corrected references from `client.agent_versions` to `client.agent_version`
  - Updated code examples to use correct API client attribute names

## Version 0.3.21

**Released:** March 16, 2025

### Added

- **Prisma Access Features**:
  - **Bandwidth Allocations**: Support for managing bandwidth allocation across service provider networks (SPNs)
  - **BGP Routing**: Support for configuring and managing BGP routing
  - **Internal DNS Servers**: Support for configuring internal DNS servers
  - **Network Locations**: Support for managing network locations

## Version 0.3.20

**Released:** March 13, 2025

### Fixed

- **Security Zone**: Added temporary workaround for inconsistent API response format in the `fetch()` method
  - Now supports both direct object response format and list-style data array format
  - Ensures backward compatibility when API format is corrected
  - Comprehensive test coverage for both response formats

## Version 0.3.19

**Released:** March 12, 2025

### Added

- **NAT Rules**: Support for managing tags not named "Automation" and "Decryption". Oof.

## Version 0.3.18

**Released:** March 8, 2025

### Added

- **Service Connections**: Support for managing Service Connection objects
  - Create, retrieve, update, and delete service connections
  - Filter service connections by name and other attributes
  - Integration with the unified client interface
  - Automatic validation of input parameters
  - Full pagination support with configurable limits

### Improved

- **Code Quality**: Enhanced validation for API parameters
- **Documentation**: Added comprehensive Service Connection documentation and usage examples

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
- **Examples**: Added examples for each of the objects and network service files

### Fixed

- **Custom Token URL Support**: Fixed issue where `token_url` parameter defined in `AuthRequestModel` wasn't exposed through the `Scm` and `ScmClient` constructors. Users can now specify custom OAuth token endpoints when initializing the client.
- **Documentation Updates**: Added comprehensive documentation for the `token_url` parameter

## Version 0.3.15

**Released:** March 2, 2025

### Added

- **HTTP Server Profile**: Support for managing HTTP Server Profiles
- **Log Forwarding Profile**: Support for managing Log Forwarding Profiles
- **SYSLOG Server Profile**: Support for managing SYSLOG Server Profiles

## Version 0.3.14

**Released:** February 28, 2025

### Added

- **Unified Client Interface**: New attribute-based access pattern for services (e.g., `client.address.create()` instead of creating separate service instances)
- **ScmClient Class**: Added as an alias for the Scm class with identical functionality but more descriptive name
- **Comprehensive Tests**: Added test suite for the unified client functionality
- **Enhanced Documentation**: Updated documentation to showcase both traditional and unified client patterns

### Improved

- **Developer Experience**: Streamlined API usage with fewer imports and less code
- **Token Refresh Handling**: Unified token refresh across all service operations

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

- **Commit Enhancement**: Support for passing the string value of "all" to a commit to specify all admin users

## Version 0.3.10

**Released:** February 12, 2025

### Added

- **Security Rule Enhancement**: Support for new security rule types of SWG by allowing the `device` field to be either string or dictionary

## Version 0.3.9

**Released:** February 8, 2025

### Added

- **NAT Rules**: Support for managing NAT rules

## Version 0.3.8

**Released:** February 5, 2025

### Added

- **Remote Networks**: Support for managing remote networks
- **SASE API Integration**: First time leveraging SASE APIs until Remote Network endpoints for SCM API are working properly

## Version 0.3.7

**Released:** February 2, 2025

### Added

- **HIP Objects**: Support for managing HIP objects

## Version 0.3.6

**Released:** January 28, 2025

### Added

- **Pagination**: Auto-pagination when using the `list()` method
- **Request Control**: Support for controlling the maximum amount of objects returned in a request (default: 2500, max: 5000)

## Version 0.3.5

**Released:** January 25, 2025

### Added

- **Advanced Filtering**: Support for performing advanced filtering capabilities

## Version 0.3.4

**Released:** January 22, 2025

### Added

- **External Dynamic Lists**: Support for managing External Dynamic Lists
- **Auto Tag Actions**: Support for Auto Tag Actions (not yet supported by API)

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
- **Model Integration**: `fetch()` returns a Pydantic modeled object now
- **Model Update**: `update()` supports passing of Pydantic modeled objects

### Changed

- **Exceptions**: Refactored exception handling
- **Logging**: Refactored logging system

### Fixed

- **OAuth Client**: Fixed issue with refresh_token handling

## Version 0.2.1

**Released:** March 30, 2025

### Fixed

- **Typer Compatibility**: Upgraded Typer from 0.11.1 to 0.15.2
  - Fixed compatibility issues with Python 3.10+ type annotations (`|` union operator)
  - Resolved `RuntimeError: Type not yet supported: list[str] | None` error when running CLI commands
  - Improved overall CLI stability with modern Python type hints

## Version 0.2.0

**Released:** December 28, 2024

### Added

- **Fetch Method**: Added `fetch` method to various profile and object classes
- **Model Updates**: Introduced `AntiSpywareProfileUpdateModel`

### Changed

- **Update Methods**: Refactored update methods to use `data['id']` directly
- **Error Handling**: Improved error type extraction logic in client
- **Model Architecture**: Refactored Address models for separate base, create, update, and response logic

## Version 0.1.17

**Released:** December 25, 2024

### Added

- **Rule Movement**: Added `move` method to enable moving security rules within the rule base

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

### Improved

- **Documentation**: Updated the mkdocs site

## Version 0.1.4

**Released:** November 12, 2024

### Added

- **Services**: Support for Services

### Improved

- **Documentation**: Updated the mkdocs site

## Version 0.1.3

**Released:** November 8, 2024

### Added

- **Applications**: Support for Applications

### Improved

- **Documentation**: Revamped README and mkdocs site

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

For more detailed information on each release, visit the [GitHub repository](https://github.com/cdot65/pan-scm-sdk/releases) or check the [commit history](https://github.com/cdot65/pan-scm-sdk/commits/main).
