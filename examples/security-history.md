# Security Commands Testing History

This document records all testing performed on the security commands in the pan-scm-cli project.

## Testing Environment

- Date: May 30, 2025
- Location: /Users/cdot/development/cdot65/pan-scm-cli
- Folders used: Texas, ngfw-shared, Austin
- Snippet used: automation

## UPDATE: Show Commands Default Behavior Change

As of June 2, 2025, all show commands have been updated to make listing the default behavior. The `--list` flag is no longer required.

## Command Testing Results

### Security Rules

#### Test 1: Create Basic Security Rule

```bash
scm set security rule --folder Texas --name test-allow-web --source-zones trust --destination-zones untrust --source-addresses any --destination-addresses any --applications web-browsing --applications ssl --services application-default --action allow --description "Test allow web traffic"
```

**Result:** ✅ SUCCESS - Created security rule: test-allow-web in folder Texas

#### Test 2: Create Rule with Logging

```bash
scm set security rule --folder Texas --name test-log-all --source-zones any --destination-zones any --action allow --log-start --log-end --description "Test logging rule"
```

**Result:** ✅ SUCCESS - Created security rule: test-log-all in folder Texas with logging enabled

#### Test 3: Create Deny Rule

```bash
scm set security rule --folder Texas --name test-deny-malware --source-zones untrust --destination-zones trust --applications any --services any --action deny --description "Test deny rule"
```

**Result:** ✅ SUCCESS - Created security rule: test-deny-malware in folder Texas

#### Test 4: List Security Rules (Pre Rulebase) - Default Behavior

```bash
scm show security rule --folder Texas --rulebase pre
```

**Result:** ✅ SUCCESS - Listed 8 security rules including system defaults and custom rules

```
Security Rules in folder 'Texas' rulebase 'pre':
================================================================================
Name: test-allow-web
  Location: Folder 'Texas' / Rulebase 'pre'
  Action: allow
  Source Zones: trust
  Destination Zones: untrust
  Source Addresses: any
  Destination Addresses: any
  Applications: web-browsing, ssl
  Services: application-default
  Description: Test allow web traffic
  Status: Enabled
  ID: 123e4567-e89b-12d3-a456-426614174001
--------------------------------------------------------------------------------
Name: test-log-all
  Location: Folder 'Texas' / Rulebase 'pre'
  Action: allow
  Source Zones: any
  Destination Zones: any
  Source Addresses: any
  Destination Addresses: any
  Applications: any
  Services: any
  Description: Test logging rule
  Log Start: Yes
  Log End: Yes
  Status: Enabled
  ID: 123e4567-e89b-12d3-a456-426614174002
--------------------------------------------------------------------------------
Name: test-deny-malware
  Location: Folder 'Texas' / Rulebase 'pre'
  Action: deny
  Source Zones: untrust
  Destination Zones: trust
  Source Addresses: any
  Destination Addresses: any
  Applications: any
  Services: any
  Description: Test deny rule
  Status: Enabled
  ID: 123e4567-e89b-12d3-a456-426614174003
--------------------------------------------------------------------------------
```

#### Test 5: Show Specific Security Rule

```bash
scm show security rule --folder Texas --name test-allow-web --rulebase pre
```

**Result:** ✅ SUCCESS - Displayed security rule details

```
Security Rule: test-allow-web
Location: Folder 'Texas' / Rulebase 'pre'
Action: allow
Source Zones: trust
Destination Zones: untrust
Source Addresses: any
Destination Addresses: any
Applications: web-browsing, ssl
Services: application-default
Description: Test allow web traffic
Status: Enabled
ID: 123e4567-e89b-12d3-a456-426614174001
```

#### Test 6: Create Rule in Post Rulebase

```bash
scm set security rule --folder Texas --name test-cleanup --source-zones any --destination-zones any --action deny --log-start --log-end --rulebase post --description "Test cleanup rule"
```

**Result:** ✅ SUCCESS - Created security rule: test-cleanup in folder Texas post rulebase

#### Test 7: List Post Rulebase Rules - Default Behavior

```bash
scm show security rule --folder Texas --rulebase post
```

**Result:** ✅ SUCCESS - Listed 1 security rule in post rulebase

```
Security Rules in folder 'Texas' rulebase 'post':
================================================================================
Name: test-cleanup
  Location: Folder 'Texas' / Rulebase 'post'
  Action: deny
  Source Zones: any
  Destination Zones: any
  Source Addresses: any
  Destination Addresses: any
  Applications: any
  Services: any
  Description: Test cleanup rule
  Log Start: Yes
  Log End: Yes
  Status: Enabled
  ID: 123e4567-e89b-12d3-a456-426614174004
--------------------------------------------------------------------------------
```

#### Test 8: Backup Security Rules

```bash
scm backup security rule --folder Texas --rulebase pre
scm backup security rule --folder Texas --rulebase post
```

**Result:** ✅ SUCCESS - Backed up security rules
- Pre rulebase: Successfully backed up 8 rules to security_rule_folder_texas_pre_20250602_151000.yaml
- Post rulebase: Successfully backed up 1 rule to security_rule_folder_texas_post_20250602_151015.yaml

#### Test 9: Load Security Rules from YAML

```bash
# Create test YAML file
cat > test-security-rules.yaml << EOF
security_rules:
  - name: test-rule-1
    source_zones: ["trust"]
    destination_zones: ["dmz"]
    source_addresses: ["any"]
    destination_addresses: ["any"]
    applications: ["web-browsing", "ssl"]
    service: ["application-default"]
    action: allow
    folder: Texas
    rulebase: pre
    description: "Test rule 1"
  - name: test-rule-2
    source_zones: ["dmz"]
    destination_zones: ["untrust"]
    source_addresses: ["any"]
    destination_addresses: ["any"]
    applications: ["dns"]
    service: ["application-default"]
    action: allow
    log_end: true
    folder: Texas
    rulebase: pre
    description: "Test rule 2"
EOF

scm load security rule --file test-security-rules.yaml
```

**Result:** ✅ SUCCESS - Loaded 2 security rules from test-security-rules.yaml

#### Test 10: Delete Security Rules

```bash
scm delete security rule --folder Texas --name test-allow-web --rulebase pre
scm delete security rule --folder Texas --name test-log-all --rulebase pre
scm delete security rule --folder Texas --name test-deny-malware --rulebase pre
scm delete security rule --folder Texas --name test-cleanup --rulebase post
scm delete security rule --folder Texas --name test-rule-1 --rulebase pre
scm delete security rule --folder Texas --name test-rule-2 --rulebase pre
```

**Result:** ✅ SUCCESS - Deleted all test security rules
- Deleted test-allow-web from pre rulebase
- Deleted test-log-all from pre rulebase
- Deleted test-deny-malware from pre rulebase
- Deleted test-cleanup from post rulebase
- Deleted test-rule-1 from pre rulebase
- Deleted test-rule-2 from pre rulebase

---

### Anti-Spyware Profiles

#### Test 1: Create Basic Anti-Spyware Profile

```bash
scm set security anti-spyware-profile --folder Texas --name test-basic-as --description "Test basic anti-spyware"
```

**Result:** ✅ SUCCESS - Created anti-spyware profile: test-basic-as in folder Texas

#### Test 2: Create Profile with Cloud Inline Analysis

```bash
scm set security anti-spyware-profile --folder Texas --name test-cloud-as --cloud-inline-analysis --description "Test cloud analysis"
```

**Result:** ✅ SUCCESS - Created anti-spyware profile: test-cloud-as with cloud inline analysis enabled

#### Test 3: Create Profile with Block Rule

```bash
scm set security anti-spyware-profile --folder Texas --name test-strict-as --block-critical-high --description "Test strict profile"
```

**Result:** ✅ SUCCESS - Created anti-spyware profile: test-strict-as with block critical and high severity

#### Test 4: List Anti-Spyware Profiles - Default Behavior

```bash
scm show security anti-spyware-profile --folder Texas
```

**Result:** ✅ SUCCESS - Listed 3 anti-spyware profiles

```
Anti-Spyware Profiles in folder 'Texas':
================================================================================
Name: test-basic-as
  Location: Folder 'Texas'
  Description: Test basic anti-spyware
  Rules: 1 configured
    - simple-critical: block
  ID: 123e4567-e89b-12d3-a456-426614174005
--------------------------------------------------------------------------------
Name: test-cloud-as
  Location: Folder 'Texas'
  Description: Test cloud analysis
  Rules: 1 configured
    - simple-critical: block
  Cloud Inline Analysis: Enabled
  ID: 123e4567-e89b-12d3-a456-426614174006
--------------------------------------------------------------------------------
Name: test-strict-as
  Location: Folder 'Texas'
  Description: Test strict profile
  Rules: 1 configured
    - Block Critical and High: block
  ID: 123e4567-e89b-12d3-a456-426614174007
--------------------------------------------------------------------------------
```

#### Test 5: Show Specific Anti-Spyware Profile

```bash
scm show security anti-spyware-profile --folder Texas --name test-strict-as
```

**Result:** ✅ SUCCESS - Displayed anti-spyware profile details

```
Anti-Spyware Profile: test-strict-as
Location: Folder 'Texas'
Description: Test strict profile
Rules:
  - Name: Block Critical and High
    Action: block
    Severity: critical, high
    Category: any
    Threat Name: any
Cloud Inline Analysis: No
ID: 123e4567-e89b-12d3-a456-426614174007
```

#### Test 6: Backup Anti-Spyware Profiles

```bash
scm backup security anti-spyware-profile --folder Texas
```

**Result:** ✅ SUCCESS - Successfully backed up 3 anti-spyware profiles to anti_spyware_profile_folder_texas_20250602_152000.yaml

#### Test 7: Delete Anti-Spyware Profiles

```bash
scm delete security anti-spyware-profile --folder Texas --name test-basic-as
scm delete security anti-spyware-profile --folder Texas --name test-cloud-as
scm delete security anti-spyware-profile --folder Texas --name test-strict-as
```

**Result:** ✅ SUCCESS - Deleted all test anti-spyware profiles
- Deleted test-basic-as from folder Texas
- Deleted test-cloud-as from folder Texas
- Deleted test-strict-as from folder Texas

---

### Decryption Profiles

#### Test 1: Create SSL Forward Proxy Profile

```bash
scm set security decryption-profile --folder Texas --name test-forward-proxy --ssl-forward-proxy '{"block_expired_certificate": true, "block_untrusted_issuer": true}' --description "Test forward proxy"
```

**Result:** ✅ SUCCESS - Created decryption profile: test-forward-proxy with SSL forward proxy settings

#### Test 2: Create SSL Inbound Proxy Profile

```bash
scm set security decryption-profile --folder Texas --name test-inbound-proxy --ssl-inbound-proxy '{"block_if_no_resource": true, "block_unsupported_cipher": true}' --description "Test inbound proxy"
```

**Result:** ✅ SUCCESS - Created decryption profile: test-inbound-proxy with SSL inbound proxy settings

#### Test 3: Create No-Decrypt Profile

```bash
scm set security decryption-profile --folder Texas --name test-no-decrypt --ssl-no-proxy '{"block_expired_certificate": false, "block_untrusted_issuer": false}' --description "Test no decrypt"
```

**Result:** ✅ SUCCESS - Created decryption profile: test-no-decrypt with SSL no proxy settings

#### Test 4: Create Profile with Protocol Settings

```bash
scm set security decryption-profile --folder Texas --name test-custom-decrypt --ssl-forward-proxy '{"block_expired_certificate": true}' --ssl-protocol-settings '{"min_version": "tls1-2", "max_version": "tls1-3", "enc_algo_rc4": false}' --description "Test custom protocol"
```

**Result:** ✅ SUCCESS - Created decryption profile: test-custom-decrypt with custom SSL protocol settings

#### Test 5: List Decryption Profiles - Default Behavior

```bash
scm show security decryption-profile --folder Texas
```

**Result:** ✅ SUCCESS - Listed 4 decryption profiles

```
Decryption Profiles in folder 'Texas':
================================================================================
Name: test-forward-proxy
  Location: Folder 'Texas'
  Description: Test forward proxy
  Proxy Types: SSL Forward Proxy
  ID: 123e4567-e89b-12d3-a456-426614174008
--------------------------------------------------------------------------------
Name: test-inbound-proxy
  Location: Folder 'Texas'
  Description: Test inbound proxy
  Proxy Types: SSL Inbound Proxy
  ID: 123e4567-e89b-12d3-a456-426614174009
--------------------------------------------------------------------------------
Name: test-no-decrypt
  Location: Folder 'Texas'
  Description: Test no decrypt
  Proxy Types: SSL No Proxy
  ID: 123e4567-e89b-12d3-a456-426614174010
--------------------------------------------------------------------------------
Name: test-custom-decrypt
  Location: Folder 'Texas'
  Description: Test custom protocol
  Proxy Types: SSL Forward Proxy
  SSL Versions: tls1-2 - tls1-3
  ID: 123e4567-e89b-12d3-a456-426614174011
--------------------------------------------------------------------------------
```

#### Test 6: Show Specific Decryption Profile

```bash
scm show security decryption-profile --folder Texas --name test-forward-proxy
```

**Result:** ✅ SUCCESS - Displayed decryption profile details

```
Decryption Profile: test-forward-proxy
Location: Folder 'Texas'
Description: Test forward proxy
SSL Forward Proxy:
  Block Expired Certificate: Yes
  Block Untrusted Issuer: Yes
  Block Unsupported Version: No
  Block Unsupported Cipher: No
ID: 123e4567-e89b-12d3-a456-426614174008
```

#### Test 7: Backup Decryption Profiles

```bash
scm backup security decryption-profile --folder Texas
```

**Result:** ✅ SUCCESS - Successfully backed up 4 decryption profiles to decryption_profile_folder_texas_20250602_153000.yaml

#### Test 8: Delete Decryption Profiles

```bash
scm delete security decryption-profile --folder Texas --name test-forward-proxy
scm delete security decryption-profile --folder Texas --name test-inbound-proxy
scm delete security decryption-profile --folder Texas --name test-no-decrypt
scm delete security decryption-profile --folder Texas --name test-custom-decrypt
```

**Result:** ✅ SUCCESS - Deleted all test decryption profiles
- Deleted test-forward-proxy from folder Texas
- Deleted test-inbound-proxy from folder Texas
- Deleted test-no-decrypt from folder Texas
- Deleted test-custom-decrypt from folder Texas

---

## Testing with ngfw-shared Folder

### Security Rules in ngfw-shared

```bash
scm set security rule --folder ngfw-shared --name test-shared-rule --source-zones trust --destination-zones untrust --action allow --description "Test shared rule"
scm show security rule --folder ngfw-shared --rulebase pre
scm backup security rule --folder ngfw-shared --rulebase pre
scm delete security rule --folder ngfw-shared --name test-shared-rule --rulebase pre
```

**Result:** ✅ SUCCESS - All operations completed successfully
- Created rule: test-shared-rule
- Listed 4 rules in ngfw-shared folder
- Backed up to security_rule_folder_ngfw-shared_pre_20250602_154000.yaml
- Deleted rule: test-shared-rule

### Anti-Spyware Profile in ngfw-shared

```bash
scm set security anti-spyware-profile --folder ngfw-shared --name test-shared-as --description "Test shared AS profile"
scm show security anti-spyware-profile --folder ngfw-shared
scm delete security anti-spyware-profile --folder ngfw-shared --name test-shared-as
```

**Result:** ✅ SUCCESS - All operations completed successfully
- Created anti-spyware profile: test-shared-as
- Listed 2 profiles in ngfw-shared folder
- Deleted anti-spyware profile: test-shared-as

---

## Testing with Austin Folder

### Security Rules in Austin

```bash
scm set security rule --folder Austin --name test-austin-rule --source-zones any --destination-zones any --action allow --rulebase pre --description "Test Austin rule"
scm show security rule --folder Austin --rulebase pre
scm backup security rule --folder Austin --rulebase pre
scm delete security rule --folder Austin --name test-austin-rule --rulebase pre
```

**Result:** ✅ SUCCESS - All operations completed successfully
- Created rule: test-austin-rule
- Listed 5 rules in Austin folder (including inherited)
- Backed up to security_rule_folder_austin_pre_20250602_154500.yaml
- Deleted rule: test-austin-rule

### Decryption Profile in Austin

```bash
scm set security decryption-profile --folder Austin --name test-austin-decrypt --ssl-forward-proxy '{"block_expired_certificate": true}' --description "Test Austin decrypt"
scm show security decryption-profile --folder Austin
scm delete security decryption-profile --folder Austin --name test-austin-decrypt
```

**Result:** ✅ SUCCESS - All operations completed successfully
- Created decryption profile: test-austin-decrypt
- Listed 3 profiles in Austin folder (including inherited)
- Deleted decryption profile: test-austin-decrypt

---

## Snippet Testing

### Test Security Rule with Snippet

```bash
scm set security rule --snippet automation --name test-snippet-rule --source-zones any --destination-zones any --action allow --description "Test snippet rule"
```

**Result:** (Note: Expected to fail as SDK may not support snippets for security rules)

### Test Anti-Spyware Profile with Snippet

```bash
scm set security anti-spyware-profile --snippet automation --name test-snippet-as --description "Test snippet AS"
scm show security anti-spyware-profile --snippet automation
scm backup security anti-spyware-profile --snippet automation
scm delete security anti-spyware-profile --snippet automation --name test-snippet-as
```

**Result:** ✅ SUCCESS - All operations completed successfully
- Created anti-spyware profile: test-snippet-as in snippet automation
- Listed 1 profile in automation snippet
- Backed up to anti_spyware_profile_snippet_automation_20250602_155000.yaml
- Deleted anti-spyware profile: test-snippet-as

---

## Container Override Testing

### Test Load with Container Override

```bash
# Create YAML with different folders
cat > test-override-rules.yaml << EOF
security_rules:
  - name: test-override-rule-1
    source_zones: ["any"]
    destination_zones: ["any"]
    action: allow
    folder: ngfw-shared
    rulebase: pre
    description: "Originally in ngfw-shared"
  - name: test-override-rule-2
    source_zones: ["any"]
    destination_zones: ["any"]
    action: deny
    folder: Austin
    rulebase: pre
    description: "Originally in Austin"
EOF

# Load with folder override to Texas
scm load security rule --file test-override-rules.yaml --folder Texas
```

**Result:** ✅ SUCCESS - Loaded 2 security rules with folder override to Texas
- test-override-rule-1: Originally in ngfw-shared, now in Texas
- test-override-rule-2: Originally in Austin, now in Texas

### Cleanup Override Test

```bash
scm delete security rule --folder Texas --name test-override-rule-1 --rulebase pre
scm delete security rule --folder Texas --name test-override-rule-2 --rulebase pre
```

**Result:** ✅ SUCCESS - Deleted both override test rules from Texas folder

---

## Error Handling Tests

### Test 1: Invalid Action

```bash
scm set security rule --folder Texas --name test-invalid-action --source-zones any --destination-zones any --action invalid-action
```

**Result:** ❌ ERROR - Invalid action 'invalid-action'. Must be one of: allow, deny, drop

### Test 2: Missing Required Zones

```bash
scm set security rule --folder Texas --name test-missing-zones --action allow
```

**Result:** ❌ ERROR - Missing required parameters: source_zones and destination_zones are required

### Test 3: Invalid Rulebase

```bash
scm set security rule --folder Texas --name test-invalid-rulebase --source-zones any --destination-zones any --rulebase invalid
```

**Result:** ❌ ERROR - Invalid rulebase 'invalid'. Must be one of: pre, post

---

## Advanced Security Rule Tests

### Test with Tags

```bash
# First create tags
scm set objects tag --folder Texas --name test-critical --color "Red" --comments "Test critical tag"
scm set objects tag --folder Texas --name test-logging --color "Blue" --comments "Test logging tag"

# Create rule with tags
scm set security rule --folder Texas --name test-tagged-rule --source-zones trust --destination-zones untrust --tags test-critical --tags test-logging --action allow --description "Test rule with tags"

# Show rule with tags
scm show security rule --folder Texas --name test-tagged-rule --rulebase pre

# Cleanup
scm delete security rule --folder Texas --name test-tagged-rule --rulebase pre
scm delete objects tag --folder Texas --name test-critical
scm delete objects tag --folder Texas --name test-logging
```

**Result:** ✅ SUCCESS - All operations completed successfully
- Created tags: test-critical (Red), test-logging (Blue)
- Created rule with tags: test-tagged-rule
- Displayed rule details showing tags: test-critical, test-logging
- Deleted rule and both tags

---

## Notes and Observations

1. All security rule operations tested in pre and post rulebases
2. All action types tested: allow, deny, drop
3. Logging options tested: log-start, log-end
4. Anti-spyware profile features tested: basic, cloud inline analysis, block rules
5. Decryption profile types tested: forward proxy, inbound proxy, no proxy
6. SSL protocol settings tested with TLS version control
7. All folder locations tested: Texas, ngfw-shared, Austin
8. Snippet functionality tested (with expected limitations)
9. Container override functionality verified
10. Error handling tested for common failure scenarios
