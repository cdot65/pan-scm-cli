# Application Management

This section covers the commands for managing application objects in Strata Cloud Manager.

## Overview

Application objects define custom applications with detailed security attributes. The `application` commands allow you to:

- Create and update custom application definitions
- Define application category, subcategory, and technology
- Set risk levels and security characteristics
- Configure protocol and port mappings
- Manage application descriptions and metadata

## Commands

### Creating/Updating Applications

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects application --folder Texas --name custom-crm \
  --category business-systems --subcategory database \
  --technology client-server --risk 3 \
  --ports "tcp/8080,tcp/8443" \
  --description "Custom CRM application"
<span style="color: green;">✓</span> Application 'custom-crm' created successfully
```

</div>

With additional security attributes:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli set objects application --folder Texas --name file-transfer-app \
  --category collaboration --subcategory file-sharing \
  --technology peer-to-peer --risk 4 \
  --ports "tcp/2121,udp/2121" \
  --able-to-transfer-files --has-known-vulnerabilities \
  --description "P2P file transfer application"
<span style="color: green;">✓</span> Application 'file-transfer-app' created successfully
```

</div>

### Listing Applications

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects application --folder Texas --list
Applications in folder 'Texas':
- custom-crm
- file-transfer-app
- legacy-erp
- mobile-app
```

</div>

### Showing Application Details

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli show objects application --folder Texas --name custom-crm
Application: custom-crm
  Category: business-systems
  Subcategory: database
  Technology: client-server
  Risk: 3
  Ports: tcp/8080,tcp/8443
  Description: Custom CRM application
  Folder: Texas
```

</div>

### Deleting Applications

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli delete objects application --folder Texas --name custom-crm
<span style="color: green;">✓</span> Application 'custom-crm' deleted successfully
```

</div>

### Bulk Operations

Load multiple applications from a YAML file:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli load objects application --folder Texas --file applications.yml
<span style="color: green;">✓</span> Loaded 10 applications successfully
```

</div>

Backup existing applications:

<div class="termy">

<!-- termynal -->
```bash
$ scm-cli backup objects application --folder Texas
<span style="color: green;">✓</span> Backed up 10 applications to application-texas.yaml
```

</div>

## YAML Configuration Format

Applications can be defined in YAML for bulk operations:

```yaml
applications:
  - name: custom-crm
    category: business-systems
    subcategory: database
    technology: client-server
    risk: 3
    description: "Custom CRM application"
    ports:
      - tcp/8080
      - tcp/8443
    
  - name: file-transfer-app
    category: collaboration
    subcategory: file-sharing
    technology: peer-to-peer
    risk: 4
    description: "P2P file transfer application"
    ports:
      - tcp/2121
      - udp/2121
    able_to_transfer_files: true
    has_known_vulnerabilities: true
    
  - name: mobile-sales
    category: business-systems
    subcategory: sales-force-automation
    technology: mobile-application
    risk: 2
    description: "Mobile sales application"
    ports:
      - tcp/443
    uses_encryption: true
    tunnel_applications: true
```

## Configuration Options

### Required Parameters

- `--name`: Name of the application
- `--category`: Primary category (e.g., business-systems, collaboration)
- `--subcategory`: Subcategory within the main category
- `--technology`: Technology type (e.g., client-server, browser-based)
- `--risk`: Risk level (1-5, with 5 being highest risk)
- `--ports`: Protocol and port combinations

### Optional Parameters

- `--description`: Detailed description
- `--able-to-transfer-files`: Can transfer files
- `--has-known-vulnerabilities`: Has known security vulnerabilities
- `--tunnels-other-applications`: Can tunnel other applications
- `--evasive`: Uses evasive techniques
- `--pervasive`: Pervasive use
- `--excessive-bandwidth-use`: Consumes excessive bandwidth
- `--used-by-malware`: Known to be used by malware
- `--no-app-id-caching`: Disable app-id caching
- `--parent-app`: Parent application name
- `--timeout`: Session timeout in seconds
- `--tcp-timeout`: TCP session timeout
- `--udp-timeout`: UDP session timeout
- `--tcp-half-closed-timeout`: TCP half-closed timeout
- `--tcp-time-wait-timeout`: TCP time-wait timeout
- `--tag`: Tags for categorization

### Context Parameters

Exactly one context parameter must be specified:

- `--folder`: Folder name (e.g., "Texas", "Shared")
- `--snippet`: Snippet name for Panorama
- `--device`: Device name for NGFW

## Examples

### Create a Web Application

```bash
scm-cli set objects application --folder Shared --name custom-portal \
  --category collaboration --subcategory web-posting \
  --technology browser-based --risk 2 \
  --ports "tcp/443" --uses-encryption \
  --description "Internal web portal"
```

### Create a High-Risk Application

```bash
scm-cli set objects application --folder Shared --name risky-app \
  --category networking --subcategory peer-to-peer \
  --technology peer-to-peer --risk 5 \
  --ports "tcp/6881-6889,udp/6881-6889" \
  --able-to-transfer-files --has-known-vulnerabilities \
  --used-by-malware --excessive-bandwidth-use \
  --description "Known P2P application with security risks"
```

### Create Application with Timeouts

```bash
scm-cli set objects application --folder Shared --name database-app \
  --category business-systems --subcategory database \
  --technology client-server --risk 1 \
  --ports "tcp/1433" \
  --timeout 7200 --tcp-timeout 1800 \
  --description "SQL Server application with extended timeouts"
```

## Notes

- Application names must be unique within a folder
- Port specifications support ranges (e.g., "tcp/8000-8100")
- Multiple ports can be comma-separated
- Risk levels help in policy decisions
- Security attributes affect how the firewall handles the application
- Tags must exist before being referenced