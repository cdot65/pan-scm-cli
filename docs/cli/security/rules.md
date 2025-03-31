# Security Rules

Security rules define policies that control traffic flow between zones. The `pan-scm-cli` provides commands to create, update, delete, and load security rules.

## Rule Components

Security rules consist of several components:

- **Source and Destination**: Define where traffic is coming from and going to
- **Applications and Services**: Specify what type of traffic is allowed
- **Actions**: Determine what happens to matching traffic
- **Profiles**: Apply security profiles to traffic

## Set Security Rule

Create or update a security rule.

### Syntax

```
scm-cli set security rule [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--folder TEXT` | Folder for the security rule | Yes |
| `--name TEXT` | Name of the security rule | Yes |
| `--description TEXT` | Description for the rule | No |
| `--source-zones LIST` | Source security zones | Yes |
| `--destination-zones LIST` | Destination security zones | Yes |
| `--source-addresses LIST` | Source address or address groups | Yes |
| `--destination-addresses LIST` | Destination address or address groups | Yes |
| `--applications LIST` | Applications to match | Yes |
| `--services LIST` | Services to match | Yes |
| `--action TEXT` | Action to take (allow, deny, drop) | Yes |
| `--log-start BOOLEAN` | Log at session start | No |
| `--log-end BOOLEAN` | Log at session end | No |
| `--disabled BOOLEAN` | Whether rule is disabled | No |
| `--tags LIST` | List of tags to apply to the rule | No |
| `--profile-group TEXT` | Security profile group to apply | No |
| `--anti-virus TEXT` | Anti-virus profile to apply | No |
| `--anti-spyware TEXT` | Anti-spyware profile to apply | No |
| `--vulnerability TEXT` | Vulnerability protection profile to apply | No |
| `--url-filtering TEXT` | URL filtering profile to apply | No |
| `--file-blocking TEXT` | File blocking profile to apply | No |
| `--data-filtering TEXT` | Data filtering profile to apply | No |
| `--wildfire-analysis TEXT` | WildFire analysis profile to apply | No |

### Examples

#### Create an Allow Rule

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set security rule --folder Shared --name "Allow-Internal-Web" \
  --source-zones Trust --destination-zones DMZ \
  --source-addresses "any" --destination-addresses "web-servers" \
  --applications web-browsing --services application-default \
  --action allow --log-end true
Creating security rule 'Allow-Internal-Web' in folder 'Shared'...
Security rule created successfully.
```

</div>

#### Create a Block Rule with Security Profiles

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set security rule --folder Shared --name "Block-Malicious-Web" \
  --source-zones Untrust --destination-zones DMZ \
  --source-addresses "any" --destination-addresses "any" \
  --applications any --services application-default \
  --action deny --log-start true --log-end true \
  --anti-virus "default-av" --anti-spyware "default-as" \
  --url-filtering "strict-url-filtering"
Creating security rule 'Block-Malicious-Web' in folder 'Shared'...
Security rule created successfully.
```

</div>

## Delete Security Rule

Delete a security rule.

### Syntax

```
scm-cli delete security rule [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--folder TEXT` | Folder containing the security rule | Yes |
| `--name TEXT` | Name of the security rule to delete | Yes |

### Example

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli delete security rule --folder Shared --name "Allow-Internal-Web"
Deleting security rule 'Allow-Internal-Web' from folder 'Shared'...
Security rule deleted successfully.
```

</div>

## Move Security Rule

Change the position of a security rule. Security rules are processed in order from top to bottom.

### Syntax

```
scm-cli set security rule --move [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--folder TEXT` | Folder containing the security rules | Yes |
| `--name TEXT` | Name of the security rule to move | Yes |
| `--location TEXT` | Where to move the rule (top, bottom, before, after) | Yes |
| `--reference TEXT` | Reference rule name (required with before/after) | For before/after |

### Examples

#### Move Rule to Top

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set security rule --move --folder Shared --name "Block-Malicious-Web" --location top
Moving security rule 'Block-Malicious-Web' to top in folder 'Shared'...
Security rule moved successfully.
```

</div>

#### Move Rule After Another Rule

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set security rule --move --folder Shared --name "Allow-Internal-Web" --location after --reference "Allow-Internal-DNS"
Moving security rule 'Allow-Internal-Web' after 'Allow-Internal-DNS' in folder 'Shared'...
Security rule moved successfully.
```

</div>

## Load Security Rules

Create or update multiple security rules from a YAML file.

### Syntax

```
scm-cli load security rule [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--folder TEXT` | Folder for the security rules | Yes |
| `--file TEXT` | Path to YAML file containing security rule definitions | Yes |

### Example YAML File

```yaml
security_rules:
  - name: Allow-Internal-Web
    description: "Allow internal users to access web servers"
    source_zones:
      - Trust
    destination_zones:
      - DMZ
    source_addresses:
      - any
    destination_addresses:
      - web-servers
    applications:
      - web-browsing
      - ssl
    services:
      - application-default
    action: allow
    log_end: true
    tags:
      - internal-access

  - name: Block-Malicious-Web
    description: "Block malicious web traffic"
    source_zones:
      - Untrust
    destination_zones:
      - DMZ
    source_addresses:
      - any
    destination_addresses:
      - any
    applications:
      - any
    services:
      - application-default
    action: deny
    log_start: true
    log_end: true
    anti_virus: default-av
    anti_spyware: default-as
    url_filtering: strict-url-filtering
    tags:
      - security
      - blocking
```

### Example Command

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli load security rule --folder Shared --file security-rules.yaml
Loading security rules from 'security-rules.yaml' into folder 'Shared'...
Created 2 security rules successfully.
```

</div>

## List Security Rules

List all security rules in a folder.

### Syntax

```
scm-cli set security rule --list [OPTIONS]
```

### Options

| Option | Description | Required |
|--------|-------------|----------|
| `--folder TEXT` | Folder to list security rules from | Yes |

### Example

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set security rule --list --folder Shared
Listing security rules in folder 'Shared'...

| Name | Source Zones | Dest Zones | Source | Destination | Apps | Services | Action | Profiles |
|------|-------------|------------|--------|-------------|------|----------|--------|----------|
| Allow-Internal-Web | Trust | DMZ | any | web-servers | web-browsing,ssl | app-default | allow | - |
| Block-Malicious-Web | Untrust | DMZ | any | any | any | app-default | deny | AV,AS,URL |
```

</div>
