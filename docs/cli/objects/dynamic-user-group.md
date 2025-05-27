# Dynamic User Group Management

This section covers the commands for managing dynamic user group objects in Strata Cloud Manager.

## Overview

Dynamic user groups automatically include users based on tag-based filter expressions. The `dynamic-user-group` commands allow you to:

- Create user groups with dynamic membership
- Define tag-based filter expressions
- Use boolean logic for complex grouping
- Integrate with User-ID for dynamic policy enforcement
- Apply tags and descriptions for organization

## Commands

### Creating/Updating Dynamic User Groups

Basic dynamic user group:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects dynamic-user-group --folder Texas --name it-admins \
  --filter "'IT' and 'Admin'" \
  --description "IT department administrators"
<span style="color: green;">✓</span> Dynamic user group 'it-admins' created successfully
```

</div>

Complex filter expression:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects dynamic-user-group --folder Texas --name remote-employees \
  --filter "'Remote' and ('Engineering' or 'Sales' or 'Support')" \
  --description "Remote workers in technical departments"
<span style="color: green;">✓</span> Dynamic user group 'remote-employees' created successfully
```

</div>

With tags:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects dynamic-user-group --folder Texas --name privileged-users \
  --filter "'Executive' or 'Admin' or 'Finance-Manager'" \
  --tag "high-privilege,monitor" \
  --description "Users with elevated privileges"
<span style="color: green;">✓</span> Dynamic user group 'privileged-users' created successfully
```

</div>

### Listing Dynamic User Groups

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects dynamic-user-group --folder Texas --list
Dynamic user groups in folder 'Texas':
- it-admins
- remote-employees
- privileged-users
- contractors
```

</div>

### Showing Dynamic User Group Details

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects dynamic-user-group --folder Texas --name it-admins
Dynamic User Group: it-admins
  Filter: 'IT' and 'Admin'
  Description: IT department administrators
  Tags: None
  Folder: Texas
```

</div>

### Deleting Dynamic User Groups

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli delete objects dynamic-user-group --folder Texas --name it-admins
<span style="color: green;">✓</span> Dynamic user group 'it-admins' deleted successfully
```

</div>

### Bulk Operations

Load multiple dynamic user groups from a YAML file:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli load objects dynamic-user-group --folder Texas --file user-groups.yml
<span style="color: green;">✓</span> Loaded 10 dynamic user groups successfully
```

</div>

Backup existing dynamic user groups:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli backup objects dynamic-user-group --folder Texas
<span style="color: green;">✓</span> Backed up 10 dynamic user groups to dynamic-user-group-texas.yaml
```

</div>

## YAML Configuration Format

Dynamic user groups can be defined in YAML for bulk operations:

```yaml
dynamic_user_groups:
  - name: it-admins
    filter: "'IT' and 'Admin'"
    description: "IT department administrators"
    
  - name: remote-employees
    filter: "'Remote' and ('Engineering' or 'Sales' or 'Support')"
    description: "Remote workers in technical departments"
    
  - name: privileged-users
    filter: "'Executive' or 'Admin' or 'Finance-Manager'"
    description: "Users with elevated privileges"
    tags:
      - high-privilege
      - monitor
    
  - name: contractors
    filter: "'Contractor' and not 'Permanent'"
    description: "External contractors"
    tags:
      - external
      - temporary
    
  - name: vpn-users
    filter: "'VPN-Access' and not 'Disabled'"
    description: "Users with VPN access"
    
  - name: developers
    filter: "'Engineering' and ('Developer' or 'DevOps')"
    description: "Software development team"
    
  - name: finance-team
    filter: "'Finance' and not 'Intern'"
    description: "Finance department employees"
    tags:
      - sensitive-access
    
  - name: interns
    filter: "'Intern' and 'Active'"
    description: "Active interns across all departments"
    tags:
      - limited-access
      - temporary
```

## Configuration Options

### Required Parameters

- `--name`: Name of the dynamic user group
- `--filter`: Tag-based filter expression (max 2047 characters)

### Optional Parameters

- `--description`: Detailed description (max 1023 characters)
- `--tag`: Tags for categorization (comma-separated)

### Context Parameters

Exactly one context parameter must be specified:

- `--folder`: Folder name (e.g., "Texas", "Shared")
- `--snippet`: Snippet name for Panorama
- `--device`: Device name for NGFW

## Filter Expression Syntax

### Basic Syntax

Filter expressions use tag names enclosed in single quotes:
- Single tag: `'TagName'`
- Multiple tags with AND: `'Tag1' and 'Tag2'`
- Multiple tags with OR: `'Tag1' or 'Tag2'`

### Boolean Operators

- **and**: Both conditions must be true
- **or**: At least one condition must be true
- **not**: Negates the condition

### Parentheses for Grouping

Use parentheses to control evaluation order:
```
'Department' and ('Role1' or 'Role2' or 'Role3')
```

### Complex Expressions

Examples of complex filter expressions:

```bash
# Users in IT who are either admins or managers
"'IT' and ('Admin' or 'Manager')"

# Remote users not in engineering
"'Remote' and not 'Engineering'"

# Executives or admins, but not contractors
"('Executive' or 'Admin') and not 'Contractor'"

# Users in multiple departments with specific roles
"('Sales' or 'Marketing') and ('Manager' or 'Director')"
```

## Examples

### Create Department-Based Groups

```bash
# Engineering team
scm-cli set objects dynamic-user-group --folder Shared --name engineering \
  --filter "'Engineering' and 'Active'" \
  --description "Active engineering team members"

# Management across departments
scm-cli set objects dynamic-user-group --folder Shared --name management \
  --filter "'Manager' or 'Director' or 'VP' or 'Executive'" \
  --description "Management personnel"
```

### Create Access-Based Groups

```bash
# VPN and remote access users
scm-cli set objects dynamic-user-group --folder Shared --name remote-access \
  --filter "'VPN-Access' or 'Remote-Desktop'" \
  --tag "remote,monitor"

# Privileged access users
scm-cli set objects dynamic-user-group --folder Shared --name privileged \
  --filter "'Admin' or 'Root' or 'Sudo'" \
  --tag "high-risk,audit"
```

### Create Exclusion Groups

```bash
# Employees excluding contractors
scm-cli set objects dynamic-user-group --folder Shared --name employees-only \
  --filter "'Employee' and not 'Contractor'"

# Active users excluding disabled accounts
scm-cli set objects dynamic-user-group --folder Shared --name active-users \
  --filter "'Active' and not ('Disabled' or 'Suspended')"
```

## Integration with Security Policies

Dynamic user groups are used in security rules for user-based access control:

```bash
# Allow IT admins to access servers
scm-cli set security rule --folder Shared --name "IT-Admin-Access" \
  --source-users "@it-admins" --destination-zones "Servers" \
  --applications "ssh,rdp" --action allow

# Restrict contractor access
scm-cli set security rule --folder Shared --name "Contractor-Restrictions" \
  --source-users "@contractors" --destination-zones "Internal" \
  --action deny
```

## Best Practices

1. **Tag Strategy**: Establish a consistent tagging strategy for users
   - Department tags: Engineering, Sales, Finance
   - Role tags: Admin, Manager, Developer
   - Status tags: Active, Contractor, Remote

2. **Filter Simplicity**: Keep filter expressions as simple as possible while meeting requirements

3. **Naming Convention**: Use descriptive names that indicate group membership criteria

4. **Documentation**: Always include descriptions explaining the group's purpose

5. **Testing**: Test filter expressions with sample users before deployment

## User-ID Integration

Dynamic user groups require User-ID to function properly:

1. **User Tagging**: Users must be tagged in the User-ID system
2. **Tag Propagation**: Tags are distributed to firewalls via User-ID
3. **Dynamic Updates**: Group membership updates automatically as tags change
4. **Real-time Enforcement**: Policy enforcement reflects current group membership

## Troubleshooting

### Common Issues

1. **Empty Groups**: Ensure users have the required tags in User-ID
2. **Filter Syntax**: Check for proper quoting and parentheses
3. **Tag Names**: Verify exact tag names (case-sensitive)
4. **Boolean Logic**: Test complex expressions with simple cases first

### Filter Validation

Test filter logic:
```bash
# Simple test
"'TestTag'"

# Incremental complexity
"'TestTag1' and 'TestTag2'"
"'TestTag1' and ('TestTag2' or 'TestTag3')"
```

## Notes

- Group names must be unique within a folder
- Filter expressions are case-sensitive
- Maximum filter length is 2047 characters
- Tags must exist in the User-ID system
- Groups are referenced in policies using the "@" prefix
- Membership is dynamic and updates in real-time
- Use single quotes around tag names in filter expressions
- Boolean operators (and, or, not) must be lowercase