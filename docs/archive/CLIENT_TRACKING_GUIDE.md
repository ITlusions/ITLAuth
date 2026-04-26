# Client & Identity Tracking Guide

## Overview

The ITL Control Plane CLI now includes comprehensive client and identity tracking capabilities. Every resource created through the CLI can be associated with:

- **Keycloak Client ID** - The OAuth2 client that created the resource
- **User ID** - The user (email/identifier) who performed the action
- **Tenant ID** - The Keycloak realm/tenant where the action originated
- **Timestamps** - When the resource was created
- **Metadata** - Additional context about the resource

This enables complete audit trails for multi-tenant, multi-client environments.

## Architecture

### Data Flow

```
User/App
    ↓
Keycloak (extracts client_id, user_id, tenant_id from JWT)
    ↓
CLI Client (includes identity headers)
    ↓
Control Plane API
    ↓
Audit Trail (stores creator metadata)
```

### Storage

Audit information is stored in `resource_audit_trail.json`:

```json
{
  "timestamp": "2026-02-01T12:34:56Z",
  "resource": {
    "id": "/subscriptions/sub-prod",
    "name": "sub-prod",
    "type": "subscription",
    "subscription_id": null
  },
  "creator": {
    "client_id": "api-gateway",
    "user_id": "bob@acme.com",
    "tenant_id": "acme"
  },
  "metadata": {
    "display_name": "Production Subscription",
    "resource_guid": "550e8400-e29b-41d4-a716-446655440001"
  }
}
```

## Bulk Data Ingestion

The `bulk_ingest_with_client_tracking.py` script provides automated multi-client data ingestion with full audit tracking.

### Installation

```powershell
# From ITLAuth directory
python bulk_ingest_with_client_tracking.py --help
```

### Usage Scenarios

#### 1. Simple Ingestion (1 client, 2 subscriptions)

```powershell
python bulk_ingest_with_client_tracking.py --scenario simple
```

Output:
```
============================================================
BULK DATA INGESTION WITH CLIENT TRACKING
============================================================

Scenario: Simple ingestion (1 client, 2 subscriptions, 2 RGs each)

Client: frontend-app (tenant: acme)
  Creating subscription: frontend-prod (client: frontend-app)
    ✓ Created: /subscriptions/frontend-prod
  Creating subscription: frontend-dev (client: frontend-app)
    ✓ Created: /subscriptions/frontend-dev
  Creating resource group: compute (client: frontend-app)
    ✓ Created: /subscriptions/frontend-prod/resourceGroups/compute
  ...
```

#### 2. Multi-Tenant Ingestion (3 clients, 2 tenants)

```powershell
python bulk_ingest_with_client_tracking.py --scenario multi-tenant
```

Creates:
- **ACME Tenant**
  - `api-gateway` client (Bob) - 2 subscriptions, 4 resource groups
  - `db-manager` client (Charlie) - 1 subscription, 2 resource groups

- **Global Systems Tenant**
  - `platform-admin` client (Diana) - 1 subscription, 2 resource groups

#### 3. Load Test (10 clients, 50 subscriptions total)

```powershell
python bulk_ingest_with_client_tracking.py --scenario load-test
```

Creates 10 simulated clients each with 5 subscriptions and 3 resource groups.

### Options

```powershell
# Use custom API URL
python bulk_ingest_with_client_tracking.py --api-url https://api.itlusions.com --scenario simple

# Use authentication token
python bulk_ingest_with_client_tracking.py --token "eyJhbGc..." --scenario multi-tenant

# Dry run (preview without creating)
python bulk_ingest_with_client_tracking.py --scenario multi-tenant --dry-run

# Custom audit trail file
# (Edit script to change ClientTrackingAuditLog(log_file="custom_path.json"))
```

## CLI Audit Commands

### View Complete Audit Trail

```powershell
# Table format (default)
itlc audit trail

# JSON format
itlc audit trail --format json

# YAML format
itlc audit trail --format yaml

# Custom audit file
itlc audit trail --file /path/to/audit.json
```

Output (table format):
```
============================================================
Complete Audit Trail (25 entries)
============================================================

1. [2026-02-01T12:34:56Z]
   Resource: subscription - frontend-prod
   Creator: client_id=frontend-app, user_id=alice@acme.com, tenant=acme

2. [2026-02-01T12:34:57Z]
   Resource: resourcegroup - compute
   Creator: client_id=frontend-app, user_id=alice@acme.com, tenant=acme

...
```

### Filter by Client

**View all resources created by a specific Keycloak client:**

```powershell
itlc audit by-client api-gateway

itlc audit by-client db-manager --format json

itlc audit by-client frontend-app --format yaml
```

Output:
```
============================================================
Resources created by client: api-gateway
Total: 6 resource(s)

SUBSCRIPTION (2)
  - api-prod                                   [2026-02-01T12:34:56Z]
  - api-staging                                [2026-02-01T12:34:57Z]

RESOURCEGROUP (4)
  - gateway                                    [2026-02-01T12:34:58Z]
  - integration                                [2026-02-01T12:34:59Z]
  ...
```

### Filter by Tenant

**View all resources created in a specific Keycloak realm/tenant:**

```powershell
itlc audit by-tenant acme

itlc audit by-tenant global-systems --format json
```

Output:
```
============================================================
Resources in tenant: acme
Total: 8 resource(s)

Client: api-gateway (3 resources)
  - subscription api-prod                      (user: bob@acme.com)
  - subscription api-staging                   (user: bob@acme.com)
  - resourcegroup gateway                      (user: bob@acme.com)

Client: db-manager (5 resources)
  - subscription db-prod                       (user: charlie@acme.com)
  - resourcegroup primary                      (user: charlie@acme.com)
  ...
```

### Filter by User

**View all resources created by a specific user:**

```powershell
itlc audit by-user alice@acme.com

itlc audit by-user bob@acme.com --format json

itlc audit by-user charlie@acme.com --format yaml
```

Output:
```
============================================================
Resources created by user: alice@acme.com
Tenant: acme
Total: 8 resource(s)

  - subscription frontend-prod                [client: frontend-app] (2026-02-01T12:34:56Z)
  - subscription frontend-dev                 [client: frontend-app] (2026-02-01T12:34:57Z)
  - resourcegroup compute                     [client: frontend-app] (2026-02-01T12:34:58Z)
  ...
```

### View Summary Statistics

**Get overview of all resources by type, client, and tenant:**

```powershell
itlc audit summary
```

Output:
```
============================================================
Audit Trail Summary
============================================================

Total Resources: 25
Resource Types: 3

Distribution by Type:
  - subscription             8 resources
  - resourcegroup           15 resources
  - deployment               2 resources

Clients: 3
  - api-gateway                                5 resources
  - db-manager                                 8 resources
  - frontend-app                               12 resources

Tenants: 2
  - acme                                       18 resources
  - global-systems                             7 resources
```

## Workflow Examples

### Scenario 1: Audit a Specific Client's Activity

You want to see what `api-gateway` client has created:

```powershell
# 1. View all resources created by api-gateway
itlc audit by-client api-gateway

# 2. Get JSON for further processing
itlc audit by-client api-gateway --format json | ConvertFrom-Json | ...

# 3. Export to file for analysis
itlc audit by-client api-gateway --format json > api-gateway-resources.json
```

### Scenario 2: Compliance Audit - User Activity

Verify what user `bob@acme.com` created:

```powershell
# View all resources created by bob
itlc audit by-user bob@acme.com

# Export for compliance report
itlc audit by-user bob@acme.com --format yaml > compliance-report-bob.yaml
```

### Scenario 3: Multi-Tenant Isolation Check

Verify clients in different tenants don't interfere:

```powershell
# Check ACME tenant resources
itlc audit by-tenant acme

# Check Global Systems tenant resources
itlc audit by-tenant global-systems

# Compare counts
$acme = itlc audit by-tenant acme --format json | ConvertFrom-Json
$global = itlc audit by-tenant global-systems --format json | ConvertFrom-Json
Write-Host "ACME: $($acme.Count) resources, Global Systems: $($global.Count) resources"
```

### Scenario 4: Timeline Analysis

View complete chronological audit trail:

```powershell
# Get chronologically ordered audit trail
itlc audit trail --format json | ConvertFrom-Json | `
  Sort-Object { [datetime]$_.timestamp } | `
  ForEach-Object {
    "$($_.timestamp): $($_.creator.client_id) created $($_.resource.type)/$($_.resource.name)"
  }
```

Output:
```
2026-02-01T12:34:56Z: frontend-app created subscription/frontend-prod
2026-02-01T12:34:57Z: frontend-app created subscription/frontend-dev
2026-02-01T12:34:58Z: frontend-app created resourcegroup/compute
2026-02-01T12:34:59Z: frontend-app created resourcegroup/storage
2026-02-01T12:35:00Z: api-gateway created subscription/api-prod
...
```

## Integration with Keycloak

### Extracting Identity from JWT Token

When using the CLI with Keycloak authentication:

1. **Client ID** - Extracted from JWT `client_id` claim
2. **User ID** - Extracted from JWT `preferred_username` or `sub` claim
3. **Tenant ID** - Extracted from JWT `iss` (issuer) or `realm` claim

### Configuring ControlPlaneClient for Identity

The `ControlPlaneClient` can be enhanced to automatically extract and include identity information:

```python
from itlc.controlplane_client import ControlPlaneClient
import jwt

# Decode token to get identity info
token = "your_keycloak_token"
decoded = jwt.decode(token, options={"verify_signature": False})

client_id = decoded.get("client_id")
user_id = decoded.get("preferred_username")
tenant_id = decoded.get("iss", "").split("/")[-1]  # Extract realm from issuer

# Pass to client
cp_client = ControlPlaneClient(token=token)
# Identity info is stored in audit logs during resource creation
```

## Best Practices

### 1. Regular Audit Trail Reviews

```powershell
# Weekly audit summary
Invoke-Expression "itlc audit summary"

# Monthly report by tenant
$tenants = "acme", "global-systems"
foreach ($tenant in $tenants) {
    "=== Tenant: $tenant ===" | Out-File -Append monthly-report.txt
    itlc audit by-tenant $tenant >> monthly-report.txt
}
```

### 2. Detecting Unauthorized Access

```powershell
# Find resources created by unexpected clients
$expected_clients = @("api-gateway", "db-manager")
$all = itlc audit summary --format json | ConvertFrom-Json
$unexpected = $all | Where-Object { $_.creator.client_id -notin $expected_clients }

if ($unexpected.Count -gt 0) {
    Write-Warning "Found unauthorized client access:"
    $unexpected | Format-Table
}
```

### 3. Clean Audit Trail for Testing

```powershell
# Backup current audit trail
Copy-Item resource_audit_trail.json resource_audit_trail.backup.json

# Clear for fresh test
Remove-Item resource_audit_trail.json

# Run test scenario
python bulk_ingest_with_client_tracking.py --scenario simple

# Restore if needed
Copy-Item resource_audit_trail.backup.json resource_audit_trail.json
```

### 4. Export for External Analysis

```powershell
# Export to CSV for Excel analysis
$audit = itlc audit trail --format json | ConvertFrom-Json
$audit | ForEach-Object {
    [PSCustomObject]@{
        Timestamp = $_.timestamp
        ResourceType = $_.resource.type
        ResourceName = $_.resource.name
        ClientID = $_.creator.client_id
        UserID = $_.creator.user_id
        TenantID = $_.creator.tenant_id
    }
} | Export-Csv audit_export.csv -NoTypeInformation
```

## Troubleshooting

### Audit Trail File Not Found

```powershell
# Check current directory
Get-ChildItem -Name *audit*.json

# Specify correct path
itlc audit trail --file ./resource_audit_trail.json
```

### Empty Audit Trail After Ingestion

Verify ingestion completed successfully:

```powershell
# Run with verbose output
python bulk_ingest_with_client_tracking.py --scenario simple | Tee-Object -Variable output

# Check file was created
Test-Path resource_audit_trail.json

# View file contents
Get-Content resource_audit_trail.json | ConvertFrom-Json | Select-Object -First 1
```

### Missing User or Tenant Information

The audit trail may have `null` values if not provided during ingestion:

```powershell
# Update the bulk ingestion script to include user_id and tenant_id:
ingestion.ingest_subscriptions(
    client_id="api-gateway",
    tenant_id="acme",           # Add this
    user_id="bob@acme.com",     # Add this
    ...
)
```

## API Integration

For programmatic access to audit data:

```python
import json
from pathlib import Path

# Load audit trail
with open("resource_audit_trail.json") as f:
    audit_entries = json.load(f)

# Filter by client
api_gateway_resources = [
    e for e in audit_entries 
    if e["creator"]["client_id"] == "api-gateway"
]

# Analyze
print(f"API Gateway created {len(api_gateway_resources)} resources")
for entry in api_gateway_resources:
    print(f"  - {entry['resource']['type']}: {entry['resource']['name']}")
```

## Next Steps

1. **Run bulk ingestion** - `python bulk_ingest_with_client_tracking.py --scenario multi-tenant`
2. **View audit trail** - `itlc audit summary`
3. **Filter by client** - `itlc audit by-client api-gateway`
4. **Export for analysis** - `itlc audit trail --format json > report.json`
5. **Set up scheduled audits** - Use PowerShell scheduled tasks or cron jobs
