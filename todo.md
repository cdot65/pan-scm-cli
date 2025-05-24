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

## Current Work (In Progress)
- [ ] Implement smart upsert logic for `create_bandwidth_allocation` method

## Phase 1: Show Command Implementation (Completed ✅)

### Address Objects (Completed ✅)
- [x] Implement `show objects address` command with `--list` and `--name` flags
- [x] Add SDK client methods: `list_addresses()` and `get_address()`
- [x] Add comprehensive tests for show address functionality
- [x] Update README with show address examples

### Address Groups (Completed ✅)
- [x] Implement `show objects address-group` command with `--list` and `--name` flags
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

### Bandwidth Allocations (Completed ✅)
- [x] Implement `show deployment bandwidth-allocation` command
- [x] Add SDK client methods for listing and fetching allocations
- [x] Add tests and documentation

## Phase 1.5: Backup Command Implementation (Completed ✅)

### All Resource Types (Completed ✅)
- [x] Implement `backup objects address` command
- [x] Implement `backup objects address-group` command  
- [x] Implement `backup network security-zone` command
- [x] Implement `backup security rule` command
- [x] Implement `backup deployment bandwidth` command
- [x] Update SDK client with `exact_match` parameter for list methods
- [x] Add field mapping from SDK to CLI format
- [x] Implement proper file naming conventions
- [x] Exclude system fields and None values from backups

## Phase 2: Update Command Implementation

### Address Objects
- [ ] Implement `update objects address` command
- [ ] Add SDK client method: `update_address()`
- [ ] Add tests and documentation

### Address Groups
- [ ] Implement `update objects address-group` command
- [ ] Add SDK client method: `update_address_group()`
- [ ] Add tests and documentation

### Security Zones
- [ ] Implement `update network security-zone` command
- [ ] Add SDK client method: `update_zone()`
- [ ] Add tests and documentation

### Security Rules
- [ ] Implement `update security rule` command
- [ ] Add SDK client method: `update_security_rule()`
- [ ] Add tests and documentation

## Phase 3: Advanced Features

### Filtering and Search
- [ ] Add filter options to list commands (by tag, description, etc.)
- [ ] Implement search functionality across object types
- [ ] Add pagination support for large result sets

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

## Notes
- All show commands should support both `--list` (all objects) and `--name` (specific object) flags
- Maintain consistent command structure across all object types
- Follow existing patterns for error handling and output formatting
- Update documentation immediately after implementing each feature