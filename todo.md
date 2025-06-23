# To-Do List: `pan-scm-cli` CRUD Command Enhancements

## Current State

The project has successfully implemented:

- ✅ Authentication via environment variables and config file
- ✅ Basic CRUD operations: set, delete, load
- ✅ Show command for all resource types
- ✅ Backup command for all resource types
- ✅ Smart upsert logic for all object types (except bandwidth allocations)
- ✅ Comprehensive test coverage for existing commands
- ✅ Documentation with examples
- ✅ Consistent style guide with 191-character separators
- ✅ Alphabetical ordering in main.py
- ✅ Multi-tenant context management
- ✅ Docker multi-platform support
- ✅ Authentication error handling and lazy client initialization

## Recent Improvements (Completed ✅)

- [x] Enhanced `create_address` method to handle existing objects gracefully
  - Automatically detects if address exists and updates instead of failing
  - Handles address type changes by delete/recreate when necessary
  - Avoids SDK validation errors by not setting unused fields to None
- [x] Enhanced `create_address_group` method with smart upsert logic
  - Automatically detects existing groups and updates them
  - Handles group type changes (static ↔ dynamic) by delete/recreate
  - Maintains consistent behavior with address objects
- [x] Created comprehensive style guides for command modules, SDK client, and validators
- [x] Implemented show commands for bandwidth allocations, security rules, and security zones
- [x] Implemented backup commands for all resource types
  - Added `exact_match` parameter to SDK list methods
  - Creates YAML files with proper naming conventions
  - Converts SDK format to CLI format for consistency
  - Excludes system fields and None values
- [x] Updated main.py with 191-character separators and alphabetical ordering
- [x] Implemented full Application support (all CRUD operations)
  - Smart upsert logic for create/update operations
  - Full attribute support including 9 security flags
  - Show command with list and detailed views
  - Load/backup YAML support
  - Delete functionality
- [x] Implemented full Application Group support (all CRUD operations)
  - Smart upsert logic for groups
  - Member management
  - Show command with membership details
  - Load/backup YAML support
  - Delete functionality
- [x] Implemented full Application Filter support (all CRUD operations)
  - Smart upsert logic for filters
  - List-based attribute filtering (category, subcategory, technology, risk)
  - Boolean security attribute filtering
  - Show command with filter criteria display
  - Load/backup YAML support
  - Delete functionality
  - Fixed SDK service name (singular not plural)
  - Fixed boolean field handling (omit when false)
- [x] Implemented full Dynamic User Group support (all CRUD operations)
  - Smart upsert logic for dynamic groups
  - Tag-based filter expressions
  - Show command with filter display
  - Load/backup YAML support
  - Delete functionality
  - Created comprehensive example YAML file
- [x] Implemented full External Dynamic List support (all CRUD operations)
  - Smart upsert logic for EDLs
  - Support for all EDL types (predefined_ip, predefined_url, ip, domain, url, imsi, imei)
  - Complex configuration support (recurring schedules, authentication, certificates)
  - Show command with detailed configuration display
  - Load/backup YAML support with flattened structure
  - Delete functionality
  - Fixed SDK service name (external_dynamic_list not external_dynamic_lists)
  - Created comprehensive example YAML file
- [x] Implemented full HIP Object support (all CRUD operations)
  - Smart upsert logic for HIP objects
  - Support for all HIP criteria types (host info, network, patch mgmt, disk encryption, mobile, certificate)
  - Show command with detailed criteria display
  - Load/backup YAML support with flattened structure
  - Delete functionality
  - Created comprehensive example YAML file with 11 HIP policies
- [x] Implemented full Multi-tenant Context Management (all features completed)
  - Smart context switching for managing multiple SCM tenants
  - Context commands: create, list, use, delete, show, current, test
  - Fixed authentication precedence order (contexts now take priority)
  - Removed legacy config file support (~/.scm-cli/config.yaml and .secrets.yaml)
  - Added informational logging showing active context
  - Replaced test-auth command with context test
  - Full Docker container support with volume mounting
  - Comprehensive documentation updates with real command output
- [x] Enhanced Docker Build Script (completed)
  - Multi-platform build support (AMD64 and ARM64)
  - Local development builds without registry push
  - Platform-specific tags (:latest for AMD64, :apple for ARM64)
  - GitHub Container Registry integration (ghcr.io)
  - Added --no-cache flag for forced rebuilds
  - Added --local and --amd64 options for specific platform builds
  - Updated documentation with build instructions
- [x] Authentication Error Handling and Lazy Client Initialization (completed)
  - Implemented lazy client initialization for better performance
  - Added specific error detection for InvalidClientError and APIError
  - Enhanced error messages with context information and actionable steps
  - Suppressed verbose SDK authentication logging
  - Improved context test command with better error handling
  - Faster CLI startup for commands that don't need API access
  - Resource efficiency through on-demand client initialization

## Current Work (In Progress)

### Smart Upsert Pattern Enhancement

The project now implements an enhanced smart upsert pattern that:

1. Fetches existing resources before create/update
2. Compares fields to detect actual changes
3. Only calls update() if fields have changed
4. Logs appropriately (found existing, creating new, updating specific fields, no changes)
5. Handles type changes with delete/recreate when necessary

#### Completed Enhancements

- [x] Enhanced `create_tag` method with proper change detection
- [x] Enhanced `create_service` method with complex field comparison
- [x] Created developer documentation at `docs/developer/smart-upsert-pattern.md`

#### Remaining Work

- [ ] Enhance remaining create methods to follow the improved pattern:
  - [ ] `create_bandwidth_allocation` - Add change detection
  - [ ] `create_security_rule` - Add change detection
  - [ ] `create_zone` - Add change detection
  - [ ] Review and update other create methods that blindly update

## Phase 1: Show Command Implementation (Completed ✅)

### Address Objects (Completed ✅)

- [x] Implement `show object address` command with `--list` and `--name` flags
- [x] Add SDK client methods: `list_addresses()` and `get_address()`
- [x] Add comprehensive tests for show address functionality
- [x] Update README with show address examples

### Address Groups (Completed ✅)

- [x] Implement `show object address-group` command with `--list` and `--name` flags
- [x] Add SDK client methods: `list_address_groups()` and `get_address_group()`
- [x] Add comprehensive tests for show address-group functionality
- [x] Update README with show address-group examples

### Security Zones (Completed ✅)

- [x] Implement `show network security-zone` command
- [x] Add SDK client methods for listing and fetching zones
- [x] Add tests and documentation

### Security Rules (Completed ✅)

- [x] Implement `show security rule` command
- [x] Add SDK client methods for listing and fetching rules
- [x] Add tests and documentation

### Applications (Completed ✅)

- [x] Implement `show object application` command with `--list` and `--name` flags
- [x] Add SDK client methods: `list_applications()` and `get_application()`
- [x] Implement all CRUD operations: set, load, delete, backup
- [x] Add comprehensive attribute support (9 security flags)
- [x] Add tests and documentation

### Application Groups (Completed ✅)

- [x] Implement `show object application-group` command with `--list` and `--name` flags
- [x] Add SDK client methods: `list_application_groups()` and `get_application_group()`
- [x] Implement all CRUD operations: set, load, delete, backup
- [x] Add member management functionality
- [x] Add tests and documentation

### Application Filters (Completed ✅)

- [x] Implement `show object application-filter` command with `--list` and `--name` flags
- [x] Add SDK client methods: `list_application_filters()` and `get_application_filter()`
- [x] Implement all CRUD operations: set, load, delete, backup
- [x] Add complex filter criteria support (lists and booleans)
- [x] Fix SDK service naming (application_filter not application_filters)
- [x] Fix boolean field handling in API requests
- [x] Add tests and documentation

### Dynamic User Groups (Completed ✅)

- [x] Implement `show object dynamic-user-group` command with `--list` and `--name` flags
- [x] Add SDK client methods: `list_dynamic_user_groups()` and `get_dynamic_user_group()`
- [x] Implement all CRUD operations: set, load, delete, backup
- [x] Add tag-based filter expression support
- [x] Create comprehensive example YAML file
- [x] Add tests and documentation

### External Dynamic Lists (Completed ✅)

- [x] Implement `show object external-dynamic-list` command with `--list` and `--name` flags
- [x] Add SDK client methods: `list_external_dynamic_lists()` and `get_external_dynamic_list()`
- [x] Implement all CRUD operations: set, load, delete, backup
- [x] Add support for all EDL types with proper configuration
- [x] Create comprehensive example YAML file with all EDL types
- [x] Add tests and documentation

### HIP Objects (Completed ✅)

- [x] Implement `show object hip-object` command with `--list` and `--name` flags
- [x] Add SDK client methods: `list_hip_objects()` and `get_hip_object()`
- [x] Implement all CRUD operations: set, load, delete, backup
- [x] Add support for all HIP criteria types (host info, network, patch mgmt, disk encryption, mobile, certificate)
- [x] Create comprehensive example YAML file with 11 different HIP policies
- [x] Add tests and documentation

### HIP Profiles (Completed ✅)

- [x] Implement `show object hip-profile` command with `--list` and `--name` flags
- [x] Add SDK client methods: `list_hip_profiles()` and `get_hip_profile()`
- [x] Implement all CRUD operations: set, load, delete, backup
- [x] Add support for complex match criteria with boolean operators
- [x] Create example YAML file with various profile configurations
- [x] Add tests and documentation

### HTTP Server Profiles (Completed ✅)

- [x] Implement `show object http-server-profile` command with `--list` and `--name` flags
- [x] Add SDK client methods: `list_http_server_profiles()` and `get_http_server_profile()`
- [x] Implement all CRUD operations: set, load, delete, backup
- [x] Add support for complex server configurations with authentication and TLS
- [x] Discover and fix required field issue (http_method)
- [x] Create comprehensive example YAML file with 10 profile configurations
- [x] Add tests and documentation

### Log Forwarding Profiles (Completed ✅)

- [x] Implement `show object log-forwarding-profile` command with `--list` and `--name` flags
- [x] Add SDK client methods: `list_log_forwarding_profiles()` and `get_log_forwarding_profile()`
- [x] Implement all CRUD operations: set, load, delete, backup
- [x] Add support for match list configurations with multiple log types
- [x] Discover and fix required field issue (filter field in match list)
- [x] Create comprehensive example YAML file with 10 profile configurations
- [x] Add tests and documentation

### Services (Completed ✅)

- [x] Implement `show object service` command with `--list` and `--name` flags
- [x] Add SDK client methods: `list_services()` and `get_service()`
- [x] Implement all CRUD operations: set, load, delete, backup
- [x] Add support for TCP/UDP protocols with port configurations
- [x] Add support for timeout override settings
- [x] Create comprehensive example YAML file with 10 service configurations
- [x] Add tests and documentation

### Service Groups (Completed ✅)

- [x] Implement `show object service-group` command with `--list` and `--name` flags
- [x] Add SDK client methods: `list_service_groups()` and `get_service_group()`
- [x] Implement all CRUD operations: set, load, delete, backup
- [x] Add support for organizing services and service groups
- [x] Add tag support for categorization
- [x] Create comprehensive example YAML file with 10 service group configurations
- [x] Add tests and documentation

### Syslog Server Profiles (Completed ✅)

- [x] Implement `show object syslog-server-profile` command with `--list` and `--name` flags
- [x] Add SDK client methods: `list_syslog_server_profiles()` and `get_syslog_server_profile()`
- [x] Implement all CRUD operations: set, load, delete, backup
- [x] Add support for multiple syslog servers with transport configurations
- [x] Support UDP and TCP transports (SSL not supported by SDK)
- [x] Create comprehensive example YAML file with 10 profile configurations
- [x] Add tests and documentation

### Tags (Completed ✅)

- [x] Implement `show object tag` command with `--list` and `--name` flags
- [x] Add SDK client methods: `list_tags()` and `get_tag()`
- [x] Implement all CRUD operations: set, load, delete, backup
- [x] Add color validation with all supported Palo Alto colors
- [x] Support comments and tag categorization
- [x] Create comprehensive example YAML file with various tag configurations
- [x] Add tests and documentation

### Decryption Profiles (Completed ✅)

- [x] Implement `show security decryption-profile` command with `--list` and `--name` flags
- [x] Add SDK client methods: `list_decryption_profiles()` and `get_decryption_profile()`
- [x] Implement all CRUD operations: set, load, delete, backup
- [x] Add support for SSL forward proxy, inbound proxy, and no proxy configurations
- [x] Support SSL protocol settings with cipher suite control
- [x] Create comprehensive example YAML file with various profile configurations
- [x] Add tests and documentation

## Command Styling Guide (Completed ✅)

- [x] Review styling patterns for address, address-group, and application objects
- [x] Create command-styling.md guide in src/scm_cli/commands/ directory
- [x] Document module structure conventions (docstrings, imports, separators)
- [x] Document command organization patterns (app groups, option constants)
- [x] Document implementation patterns for each command type (backup, delete, load, set, show)
- [x] Document error handling and output formatting conventions
- [x] Document type hints and naming conventions
- [x] Update prd.md with style guide information
- [x] Update todo.md with completion status

## Phase 1.5: Backup Command Implementation (Completed ✅)

### All Resource Types (Completed ✅)

- [x] Implement `backup object address` command
- [x] Implement `backup object address-group` command
- [x] Implement `backup object application` command
- [x] Implement `backup object application-group` command
- [x] Implement `backup object application-filter` command
- [x] Implement `backup object dynamic-user-group` command
- [x] Implement `backup object external-dynamic-list` command
- [x] Implement `backup object hip-object` command
- [x] Implement `backup object hip-profile` command
- [x] Implement `backup object http-server-profile` command
- [x] Implement `backup object log-forwarding-profile` command
- [x] Implement `backup object service` command
- [x] Implement `backup object service-group` command
- [x] Implement `backup object syslog-server-profile` command
- [x] Implement `backup object tag` command
- [x] Implement `backup network security-zone` command
- [x] Implement `backup security rule` command
- [x] Implement `backup security anti-spyware-profile` command
- [x] Implement `backup security decryption-profile` command
- [x] Implement `backup sase bandwidth` command
- [x] Update SDK client with `exact_match` parameter for list methods
- [x] Add field mapping from SDK to CLI format
- [x] Implement proper file naming conventions
- [x] Exclude system fields and None values from backups
- [x] Standardize backup command parameters (folder/snippet/device/file) across all commands
- [x] Update all SDK client list methods to support folder/snippet/device parameters
- [x] Implement kwargs pattern for cleaner API calls in backup commands
- [x] Add location validation and default filename generation helpers

## Phase 1.6: Load Command Standardization (Completed ✅)

### All Load Commands (Completed ✅)

- [x] Standardize all load commands to use consistent pattern
- [x] Add help text in decorator for all load commands
- [x] Change file parameter from `str` to `Path` using FILE_OPTION
- [x] Add container override options (folder/snippet/device) to all load commands
- [x] Implement container parameter validation where needed
- [x] Update file validation to use `file.exists()`
- [x] Switch to direct YAML loading with `yaml.safe_load()`
- [x] Add container override logic in processing loops
- [x] Standardize output to count-based format
- [x] Add error handling with continue for resilience
- [x] Ensure all commands return results list
- [x] Update command-styling.md with load command pattern

### Commands Standardized (Completed ✅)

- [x] `load object address-group` - Standardized with all features
- [x] `load object application` - Standardized with all features
- [x] `load object application-group` - Standardized with all features
- [x] `load object application-filter` - Standardized with all features
- [x] `load object dynamic-user-group` - Standardized with all features
- [x] `load object external-dynamic-list` - Standardized with all features
- [x] `load object hip-object` - Standardized with all features
- [x] `load object hip-profile` - Standardized with all features
- [x] `load object http-server-profile` - Standardized with all features
- [x] `load object log-forwarding-profile` - Standardized with all features
- [x] `load object service` - Standardized with all features
- [x] `load object service-group` - Standardized with all features
- [x] `load object syslog-server-profile` - Standardized with all features
- [x] `load object tag` - Already had correct pattern
- [x] `set sase service-connection` - Implement full CRUD, list, load, and backup commands for service connections (Completed)
- [x] `set sase remote-network` - Implement full CRUD, list, load, and backup commands for remote networks (Completed)
- [ ] `set sase bandwidth-allocation` - Implement full CRUD, list, load, and backup commands for bandwidth allocations

## Phase 2: Smart Upsert Logic for Remaining Resources

### Note on Update Commands

The project uses a unified approach where `set` commands handle both create and update operations automatically. This eliminates the need for separate `update` commands. The smart upsert logic:

- Detects if a resource exists
- Updates it if found
- Creates it if not found
- Handles type changes by delete/recreate when necessary

This pattern has been successfully implemented for most object types and should be extended to the remaining resources.

### SASE Bandwidth Allocations (In Progress)

- [ ] Implement smart upsert logic for `create_sase_bandwidth_allocation` method
- [ ] Handle existing allocations gracefully (update instead of fail)
- [ ] Add proper error handling for allocation conflicts
- [ ] Implement CLI commands: set sase bandwidth-allocation, delete sase bandwidth-allocation, show sase bandwidth-allocation, list sase bandwidth-allocations, load sase bandwidth-allocations, backup sase bandwidth-allocations
- [ ] Add comprehensive tests and documentation for all sase bandwidth-allocation commands

### Security Zones

- [ ] Enhance `create_zone` method with smart upsert logic
- [ ] Handle zone type changes if applicable
- [ ] Add tests for update scenarios

### Security Rules

- [ ] Enhance `create_security_rule` method with smart upsert logic
- [ ] Handle rule modifications without errors
- [ ] Add tests for update scenarios

## Phase 3: Advanced Features

### Filtering and Search

- [ ] Add filter options to list commands (by tag, description, etc.)
- [ ] Implement search functionality across object types
- [ ] Add pagination support for large result sets

### Security Service CLI Coverage

- [ ] Implement CRUD/show/backup/load CLI commands for:
  - DNS Security Profile
  - URL Categories
  - Vulnerability Protection Profile
  - WildFire Antivirus Profile

### Output Formats

- [ ] Add JSON output format option
- [ ] Add CSV export option
- [ ] Add table format for better readability

### Batch Operations

- [ ] Implement batch update capabilities
- [ ] Add dry-run support for all modification commands
- [ ] Implement rollback functionality

## Phase 4: Documentation and Polish

### Documentation

- [ ] Create comprehensive API documentation
- [ ] Add more real-world examples
- [ ] Create video tutorials

### Performance

- [ ] Implement caching for frequently accessed objects
- [ ] Add progress bars for long-running operations
- [ ] Optimize bulk operations

### Testing

- [ ] Achieve 100% test coverage
- [ ] Add integration tests with mock SCM API
- [ ] Add performance benchmarks

## Phase 5: Insights Commands (New)

### Overview

Implement comprehensive insights commands for monitoring and analyzing SCM deployments. These commands will provide access to real-time and historical data about network resources, user activity, and infrastructure state.

### Insights Command Structure

```bash
scm insights <resource> [options]
```

### Resources to Implement

#### Alerts

- [ ] Research SDK support for alerts endpoint
- [ ] Implement `list_alerts()` method in sdk_client.py
- [ ] Implement `get_alert()` method in sdk_client.py
- [ ] Create Alert validator model in validators.py
- [ ] Implement `show insights alerts` command with --list and --id options
- [ ] Add severity filtering (--severity critical/high/medium/low)
- [ ] Add time range filtering (--start, --end)
- [ ] Add export functionality (--export json/csv)
- [ ] Add real-time monitoring option (--real-time)
- [ ] Add comprehensive tests
- [ ] Document command usage and examples

#### Mobile Users

- [ ] Research SDK support for mobile users endpoint
- [ ] Implement `list_mobile_users()` method in sdk_client.py
- [ ] Implement `get_mobile_user()` method in sdk_client.py
- [ ] Create MobileUser validator model in validators.py
- [ ] Implement `show insights mobile-users` command
- [ ] Add status filtering (--status connected/disconnected)
- [ ] Add location filtering (--location)
- [ ] Add export functionality (--export json/csv)
- [ ] Add comprehensive tests
- [ ] Document command usage and examples

#### Locations

- [ ] Research SDK support for locations endpoint
- [ ] Implement `list_locations()` method in sdk_client.py
- [ ] Implement `get_location()` method in sdk_client.py
- [ ] Create Location validator model in validators.py
- [ ] Implement `show insights locations` command
- [ ] Add geographic filtering options
- [ ] Add export functionality (--export json/csv)
- [ ] Add comprehensive tests
- [ ] Document command usage and examples

#### Remote Networks

- [ ] Research SDK support for remote networks insights endpoint
- [ ] Implement `list_remote_network_insights()` method in sdk_client.py
- [ ] Implement `get_remote_network_insights()` method in sdk_client.py
- [ ] Create RemoteNetworkInsights validator model in validators.py
- [ ] Implement `show insights remote-networks` command
- [ ] Add connectivity status filtering
- [ ] Add performance metrics display
- [ ] Add export functionality (--export json/csv)
- [ ] Add comprehensive tests
- [ ] Document command usage and examples

#### Service Connections

- [ ] Research SDK support for service connections insights endpoint
- [ ] Implement `list_service_connection_insights()` method in sdk_client.py
- [ ] Implement `get_service_connection_insights()` method in sdk_client.py
- [ ] Create ServiceConnectionInsights validator model in validators.py
- [ ] Implement `show insights service-connections` command
- [ ] Add health status filtering
- [ ] Add metrics display (latency, throughput, etc.)
- [ ] Add export functionality (--export json/csv)
- [ ] Add comprehensive tests
- [ ] Document command usage and examples

#### Tunnels

- [ ] Research SDK support for tunnels endpoint
- [ ] Implement `list_tunnels()` method in sdk_client.py
- [ ] Implement `get_tunnel()` method in sdk_client.py
- [ ] Create Tunnel validator model in validators.py
- [ ] Implement `show insights tunnels` command
- [ ] Add status filtering (--status up/down)
- [ ] Add performance statistics display
- [ ] Add time range filtering for historical data
- [ ] Add export functionality (--export json/csv)
- [ ] Add comprehensive tests
- [ ] Document command usage and examples

### Implementation Tasks

#### Module Setup

- [ ] Create src/scm_cli/commands/insights.py module
- [ ] Follow established command patterns from other modules
- [ ] Register insights app in main.py
- [ ] Add consistent section separators (191 characters)

#### Common Features

- [ ] Implement table output format using Rich library
- [ ] Implement JSON output format
- [ ] Implement CSV export functionality
- [ ] Add progress indicators for long-running operations
- [ ] Handle pagination for large result sets
- [ ] Add mock mode support for testing

#### Testing

- [ ] Create test_insights_commands.py
- [ ] Add unit tests for each insights resource
- [ ] Add integration tests with mock data
- [ ] Ensure 100% test coverage

#### Documentation

- [ ] Create docs/cli/insights/ directory
- [ ] Document each insights resource command
- [ ] Add examples for common use cases
- [ ] Update main README with insights commands

## Notes

- All show commands should support both `--list` (all objects) and `--name` (specific object) flags
- Maintain consistent command structure across all object types
- Follow existing patterns for error handling and output formatting
- Update documentation immediately after implementing each feature
- Insights commands may require different SDK endpoints than configuration commands
- Consider rate limiting and performance implications for real-time monitoring
- Ensure proper error handling for network connectivity issues
