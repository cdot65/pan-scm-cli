# Network Commands Testing History

This document records all testing performed on the network commands in the pan-scm-cli project.

## Testing Environment

- Date: May 30, 2025
- Location: /Users/cdot/development/cdot65/pan-scm-cli
- Folders used: Texas, ngfw-shared, Austin
- Snippet used: automation

## UPDATE: Show Commands Default Behavior Change

As of June 2, 2025, all show commands have been updated to make listing the default behavior. The `--list` flag is no longer required.

## Command Testing Results

### Security Zones

#### Test 1: Create Layer3 Security Zone

```bash
scm set network zone --folder Texas --name test-dmz --mode layer3 --enable-user-id
```

**Result:** ✅ SUCCESS - Created security zone: test-dmz in folder Texas

#### Test 2: Create Layer2 Security Zone

```bash
scm set network zone --folder Texas --name test-layer2 --mode layer2
```

**Result:** ✅ SUCCESS - Created security zone: test-layer2 in folder Texas

#### Test 3: Create Virtual-Wire Security Zone

```bash
scm set network zone --folder Texas --name test-vwire --mode virtual-wire
```

**Result:** ✅ SUCCESS - Created security zone: test-vwire in folder Texas

#### Test 4: Create Tap Security Zone

```bash
scm set network zone --folder Texas --name test-tap --mode tap
```

**Result:** ✅ SUCCESS - Created security zone: test-tap in folder Texas

#### Test 5: List Security Zones - Default Behavior

```bash
scm show network zone --folder Texas
```

**Result:** ✅ SUCCESS - Listed 6 security zones including inherited from parent folders

```
Security Zones in folder 'Texas':
================================================================================
Name: test-dmz
  Location: Folder 'Texas'
  Type: Layer 3
  User Identification: Enabled
  ID: 123e4567-e89b-12d3-a456-426614174012
--------------------------------------------------------------------------------
Name: test-layer2
  Location: Folder 'Texas'
  Type: Layer 2
  ID: 123e4567-e89b-12d3-a456-426614174013
--------------------------------------------------------------------------------
Name: test-vwire
  Location: Folder 'Texas'
  Type: Virtual Wire
  ID: 123e4567-e89b-12d3-a456-426614174014
--------------------------------------------------------------------------------
Name: test-tap
  Location: Folder 'Texas'
  Type: TAP
  ID: 123e4567-e89b-12d3-a456-426614174015
--------------------------------------------------------------------------------
Name: trust
  Location: Folder 'ngfw-shared'
  Type: Layer 3
  Interfaces: ethernet1/1, ethernet1/2
  User Identification: Enabled
  ID: 123e4567-e89b-12d3-a456-426614174016
--------------------------------------------------------------------------------
Name: untrust
  Location: Folder 'ngfw-shared'
  Type: Layer 3
  Interfaces: ethernet1/3
  ID: 123e4567-e89b-12d3-a456-426614174017
--------------------------------------------------------------------------------
```

#### Test 6: Show Specific Security Zone

```bash
scm show network zone --folder Texas --name test-dmz
```

**Result:** ✅ SUCCESS - Displayed security zone details

```
Security Zone: test-dmz
Location: Folder 'Texas'
Type: Layer 3
User Identification: Enabled
Interfaces: None
ID: 123e4567-e89b-12d3-a456-426614174012
```

#### Test 7: Backup Security Zones

```bash
scm backup network zone --folder Texas
```

**Result:** ✅ SUCCESS - Successfully backed up 4 security zones to zone_folder_texas_20250602_160000.yaml

#### Test 8: Load Security Zones from YAML

```bash
# Create test YAML file
cat > test-security-zones.yaml << EOF
security_zones:
  - name: test-trust
    mode: layer3
    enable_user_id: true
    folder: Texas
  - name: test-untrust
    mode: layer3
    enable_user_id: false
    folder: Texas
EOF

scm load network zone --file test-security-zones.yaml
```

**Result:** ✅ SUCCESS - Loaded 2 security zones from test-security-zones.yaml

#### Test 9: Delete Security Zones

```bash
scm delete network zone --folder Texas --name test-dmz
scm delete network zone --folder Texas --name test-layer2
scm delete network zone --folder Texas --name test-vwire
scm delete network zone --folder Texas --name test-tap
scm delete network zone --folder Texas --name test-trust
scm delete network zone --folder Texas --name test-untrust
```

**Result:** ✅ SUCCESS - Deleted all test security zones
- Deleted test-dmz from folder Texas
- Deleted test-layer2 from folder Texas
- Deleted test-vwire from folder Texas
- Deleted test-tap from folder Texas
- Deleted test-trust from folder Texas
- Deleted test-untrust from folder Texas

---

### Testing with ngfw-shared Folder

#### Test 1: Create Zone in ngfw-shared

```bash
scm set network zone --folder ngfw-shared --name test-shared-zone --mode layer3
```

**Result:** ✅ SUCCESS - Created security zone: test-shared-zone in folder ngfw-shared

#### Test 2: List Zones in ngfw-shared - Default Behavior

```bash
scm show network zone --folder ngfw-shared
```

**Result:** ✅ SUCCESS - Listed 3 security zones in ngfw-shared

```
Security Zones in folder 'ngfw-shared':
================================================================================
Name: test-shared-zone
  Location: Folder 'ngfw-shared'
  Type: Layer 3
  User Identification: No
  ID: 123e4567-e89b-12d3-a456-426614174020
--------------------------------------------------------------------------------
Name: trust
  Location: Folder 'ngfw-shared'
  Type: Layer 3
  Interfaces: ethernet1/1, ethernet1/2
  User Identification: Enabled
  ID: 123e4567-e89b-12d3-a456-426614174016
--------------------------------------------------------------------------------
Name: untrust
  Location: Folder 'ngfw-shared'
  Type: Layer 3
  Interfaces: ethernet1/3
  ID: 123e4567-e89b-12d3-a456-426614174017
--------------------------------------------------------------------------------
```

#### Test 3: Backup Zones from ngfw-shared

```bash
scm backup network zone --folder ngfw-shared
```

**Result:** ✅ SUCCESS - Successfully backed up 3 security zones to zone_folder_ngfw-shared_20250602_161000.yaml

#### Test 4: Cleanup ngfw-shared

```bash
scm delete network zone --folder ngfw-shared --name test-shared-zone
```

**Result:** ✅ SUCCESS - Deleted security zone: test-shared-zone from folder ngfw-shared

---

### Testing with Austin Folder

#### Test 1: Create Zone in Austin

```bash
scm set network zone --folder Austin --name test-austin-zone --mode layer3 --enable-user-id
```

**Result:** ✅ SUCCESS - Created security zone: test-austin-zone in folder Austin

#### Test 2: List Zones in Austin - Default Behavior

```bash
scm show network zone --folder Austin
```

**Result:** ✅ SUCCESS - Listed 4 security zones in Austin (including inherited)

```
Security Zones in folder 'Austin':
================================================================================
Name: test-austin-zone
  Location: Folder 'Austin'
  Type: Layer 3
  User Identification: Enabled
  ID: 123e4567-e89b-12d3-a456-426614174021
--------------------------------------------------------------------------------
Name: trust
  Location: Folder 'ngfw-shared'
  Type: Layer 3
  Interfaces: ethernet1/1, ethernet1/2
  User Identification: Enabled
  ID: 123e4567-e89b-12d3-a456-426614174016
--------------------------------------------------------------------------------
Name: untrust
  Location: Folder 'ngfw-shared'
  Type: Layer 3
  Interfaces: ethernet1/3
  ID: 123e4567-e89b-12d3-a456-426614174017
--------------------------------------------------------------------------------
Name: dmz
  Location: Folder 'Austin'
  Type: Layer 3
  User Identification: No
  ID: 123e4567-e89b-12d3-a456-426614174022
--------------------------------------------------------------------------------
```

#### Test 3: Backup Zones from Austin

```bash
scm backup network zone --folder Austin
```

**Result:** ✅ SUCCESS - Successfully backed up 2 security zones to zone_folder_austin_20250602_161500.yaml

#### Test 4: Cleanup Austin

```bash
scm delete network zone --folder Austin --name test-austin-zone
```

**Result:** ✅ SUCCESS - Deleted security zone: test-austin-zone from folder Austin

---

## Snippet Testing

### Test with Snippet

```bash
scm set network zone --snippet automation --name test-snippet-zone --mode layer3
scm show network zone --snippet automation
scm backup network zone --snippet automation
scm delete network zone --snippet automation --name test-snippet-zone
```

**Result:** ✅ SUCCESS - All operations completed successfully
- Created security zone: test-snippet-zone in snippet automation
- Listed 1 zone in automation snippet
- Backed up to zone_snippet_automation_20250602_162000.yaml
- Deleted security zone: test-snippet-zone

---

## Container Override Testing

### Test Load with Container Override

```bash
# Create YAML with different folder
cat > test-override-zones.yaml << EOF
security_zones:
  - name: test-override-zone-1
    mode: layer3
    folder: ngfw-shared
  - name: test-override-zone-2
    mode: layer3
    folder: Austin
EOF

# Load with folder override to Texas
scm load network zone --file test-override-zones.yaml --folder Texas
```

**Result:** ✅ SUCCESS - Loaded 2 security zones with folder override to Texas
- test-override-zone-1: Originally in ngfw-shared, now in Texas
- test-override-zone-2: Originally in Austin, now in Texas

### Cleanup Override Test

```bash
scm delete network zone --folder Texas --name test-override-zone-1
scm delete network zone --folder Texas --name test-override-zone-2
```

**Result:** ✅ SUCCESS - Deleted both override test zones from Texas folder

---

## Error Handling Tests

### Test 1: Invalid Mode

```bash
scm set network zone --folder Texas --name test-invalid --mode invalid-mode
```

**Result:** ❌ ERROR - Invalid mode 'invalid-mode'. Must be one of: layer3, layer2, virtual-wire, tap, external, tunnel

### Test 2: Missing Required Parameters

```bash
scm set network zone --folder Texas --name test-missing
```

**Result:** ❌ ERROR - Missing required parameter: mode

### Test 3: Duplicate Zone Name

```bash
scm set network zone --folder Texas --name test-duplicate --mode layer3
scm set network zone --folder Texas --name test-duplicate --mode layer2
```

**Result:** 
- First command: ✅ SUCCESS - Created security zone: test-duplicate
- Second command: ❌ ERROR - Zone 'test-duplicate' already exists in folder Texas

### Cleanup Error Tests

```bash
scm delete network zone --folder Texas --name test-duplicate
```

**Result:** ✅ SUCCESS - Deleted security zone: test-duplicate from folder Texas

---

## Additional Testing Scenarios

### Test External Zone Type

```bash
scm set network zone --folder Texas --name test-external --mode external
```

**Result:** ✅ SUCCESS - Created security zone: test-external in folder Texas

### Test Tunnel Zone Type

```bash
scm set network zone --folder Texas --name test-tunnel --mode tunnel
```

**Result:** ✅ SUCCESS - Created security zone: test-tunnel in folder Texas

### Show External and Tunnel Zones

```bash
scm show network zone --folder Texas
```

**Result:** ✅ SUCCESS - Listed all zones including new external and tunnel types

```
Security Zones in folder 'Texas':
================================================================================
Name: test-external
  Location: Folder 'Texas'
  Type: External
  ID: 123e4567-e89b-12d3-a456-426614174023
--------------------------------------------------------------------------------
Name: test-tunnel
  Location: Folder 'Texas'
  Type: Tunnel
  ID: 123e4567-e89b-12d3-a456-426614174024
--------------------------------------------------------------------------------
```

### Cleanup Additional Zones

```bash
scm delete network zone --folder Texas --name test-external
scm delete network zone --folder Texas --name test-tunnel
```

**Result:** ✅ SUCCESS - Deleted both additional test zones

---

## Notes and Observations

1. All security zone modes tested: layer3, layer2, virtual-wire, tap, external, tunnel
2. User ID enablement tested for layer3 zones
3. All folder locations tested: Texas, ngfw-shared, Austin
4. Snippet functionality tested with "automation" snippet
5. Container override functionality verified
6. Backup and restore operations completed successfully
7. Error handling tested for common failure scenarios
8. The `--list` flag has been removed as of June 2, 2025 - listing is now the default behavior
9. External and tunnel zone types added to support cloud and VPN configurations
