# ITL Core Resources Management

The ITLC CLI provides comprehensive CRUD operations for Core Provider resources via the API Gateway.

## Overview

The Core Provider (`ITL.Core`) manages foundational infrastructure resources:
- **Tenants** - Multi-tenant organization boundaries
- **Subscriptions** - Billing and resource containers
- **Resource Groups** - Logical grouping of resources
- **Management Groups** - Hierarchical organization structure for subscriptions
- **Locations** - Azure-compatible datacenter regions

All commands communicate with the API Gateway, which routes requests to the Core Provider following ARM-style URL patterns.

## Prerequisites

1. **API Gateway Running**: Ensure the ITL Control Plane API Gateway is accessible
2. **Authentication**: Obtain a valid authentication token (via `itlc login` or service account)
3. **Environment Variables**:
   ```bash
   export CONTROLPLANE_API_URL="http://localhost:8080"  # or production URL
   export CONTROLPLANE_TOKEN="your-jwt-token"
   ```

## Tenant Management

Tenants represent the highest level of organization hierarchy.

### Create Tenant
```bash
# Basic tenant
itlc tenant create my-tenant

# With domain and tags
itlc tenant create acme-corp \
    --display-name "ACME Corporation" \
    --domain acme.com \
    --location westeurope \
    --tag environment=production \
    --tag owner=platform-team

# Output as JSON
itlc tenant create my-tenant --output json

# Get tenant ID only
itlc tenant create my-tenant --output id
```

### List Tenants
```bash
# Table format (default)
itlc tenant list

# JSON format
itlc tenant list --output json
```

### Get Tenant Details
```bash
# JSON output (default)
itlc tenant get tenant-001

# Table output
itlc tenant get tenant-001 --output table
```

### Delete Tenant
```bash
# With confirmation prompt
itlc tenant delete tenant-001

# Skip confirmation
itlc tenant delete tenant-001 --yes
```

## Subscription Management

Subscriptions are billing and resource containers within a tenant.

### Create Subscription
```bash
# Basic subscription
itlc subscription create my-subscription

# With tenant parent
itlc subscription create prod-subscription \
    --display-name "Production Subscription" \
    --tenant-id tenant-001 \
    --state Enabled \
    --location westeurope \
    --tag costcenter=engineering

# States: Enabled, Disabled, Deleted
itlc subscription create test-sub --state Disabled
```

### List Subscriptions
```bash
# All subscriptions
itlc subscription list

# Filter by tenant
itlc subscription list --tenant-id tenant-001

# JSON output
itlc subscription list --output json
```

### Get Subscription Details
```bash
itlc subscription get sub-001
itlc subscription get sub-001 --output table
```

### Delete Subscription
```bash
itlc subscription delete sub-001
itlc subscription delete sub-001 --yes
```

## Resource Group Management

Resource groups provide logical grouping of resources within a subscription.

### Create Resource Group
```bash
# Basic resource group
itlc resourcegroup create my-rg sub-001 --location westeurope

# With managed-by and tags
itlc resourcegroup create app-rg sub-prod-001 \
    --location westeurope \
    --managed-by /subscriptions/sub-001/providers/ITL.Solutions/applications/myapp \
    --tag app=webserver \
    --tag tier=frontend

# Output ID for scripting
RG_ID=$(itlc resourcegroup create my-rg sub-001 --location westeurope --output id)
echo "Created: $RG_ID"
```

### List Resource Groups
```bash
# All resource groups
itlc resourcegroup list

# Filter by subscription
itlc resourcegroup list --subscription-id sub-001

# JSON output
itlc resourcegroup list --subscription-id sub-001 --output json
```

### Get Resource Group Details
```bash
itlc resourcegroup get sub-001 my-rg
itlc resourcegroup get sub-001 my-rg --output table
```

### Delete Resource Group
```bash
itlc resourcegroup delete sub-001 my-rg
itlc resourcegroup delete sub-001 my-rg --yes
```

## Location Management

Locations represent Azure-compatible datacenter regions.

### Create Location
```bash
# Basic location
itlc location create my-datacenter

# With region and coordinates
itlc location create itl-amsterdam \
    --display-name "ITL Amsterdam" \
    --region "Netherlands" \
    --location-type Region \
    --latitude 52.3676 \
    --longitude 4.9041

# Location types: Region, EdgeZone, DataCenter
itlc location create edge-site-01 \
    --display-name "Edge Site 01" \
    --location-type EdgeZone
```

### List Locations
```bash
# Table format
itlc location list

# JSON format
itlc location list --output json
```

### Get Location Details
```bash
itlc location get westeurope
itlc location get eastus --output table
```

### Delete Location
```bash
# With confirmation prompt
itlc location delete my-datacenter

# Skip confirmation
itlc location delete my-datacenter --yes
```

## Management Group Management

Management groups provide hierarchical organization for subscriptions.

### Create Management Group
```bash
# Basic management group
itlc managementgroup create platform-mg

# With display name and parent
itlc managementgroup create production-mg \
    --display-name "Production" \
    --parent-id platform-mg \
    --tenant-id tenant-001

# Nested hierarchy
itlc managementgroup create root-mg --display-name "Root"
itlc managementgroup create platform-mg --display-name "Platform" --parent-id root-mg
itlc managementgroup create workloads-mg --display-name "Workloads" --parent-id root-mg
```

### List Management Groups
```bash
# Table format
itlc managementgroup list

# JSON format
itlc managementgroup list --output json
```

### Get Management Group Details
```bash
# JSON output (default)
itlc managementgroup get platform-mg

# Table output
itlc managementgroup get platform-mg --output table
```

### Delete Management Group
```bash
# With confirmation prompt
itlc managementgroup delete platform-mg

# Skip confirmation
itlc managementgroup delete platform-mg --yes
```

## Authentication

### Using Interactive Login
```bash
# Login interactively
itlc login

# Commands automatically use cached token
itlc tenant list
```

### Using Service Account Token
```bash
# Get service account token
TOKEN=$(itlc get-token --client-id my-app --client-secret secret --output token)

# Use token for commands
export CONTROLPLANE_TOKEN=$TOKEN
itlc tenant list
```

### Using Environment Variables
```bash
# Set once
export CONTROLPLANE_API_URL="https://api.itlusions.com"
export CONTROLPLANE_TOKEN="eyJhbGc..."

# Run commands without flags
itlc tenant create my-tenant
itlc subscription list
```

## Complete Workflow Example

```bash
# 1. Setup environment
export CONTROLPLANE_API_URL="http://localhost:8080"
export CONTROLPLANE_TOKEN=$(itlc get-token --client-id admin --client-secret secret --output token)

# 2. Create tenant
TENANT_ID=$(itlc tenant create acme-corp \
    --display-name "ACME Corporation" \
    --domain acme.com \
    --output id)
echo "Created tenant: $TENANT_ID"

# 3. Create subscription
SUB_ID=$(itlc subscription create prod-sub \
    --display-name "Production Subscription" \
    --tenant-id $TENANT_ID \
    --state Enabled \
    --output id)
echo "Created subscription: $SUB_ID"

# 4. Create resource group
RG_ID=$(itlc resourcegroup create app-rg $SUB_ID \
    --location westeurope \
    --tag environment=production \
    --output id)
echo "Created resource group: $RG_ID"

# 5. Create management group hierarchy
MG_ROOT=$(itlc managementgroup create root-mg \
    --display-name "Organization Root" \
    --output id)
echo "Created root management group: $MG_ROOT"

MG_PLATFORM=$(itlc managementgroup create platform-mg \
    --display-name "Platform" \
    --parent-id root-mg \
    --output id)
echo "Created platform management group: $MG_PLATFORM"

# 6. List all resources
echo "=== Tenants ==="
itlc tenant list

echo "=== Subscriptions ==="
itlc subscription list --tenant-id $TENANT_ID

echo "=== Resource Groups ==="
itlc resourcegroup list --subscription-id $SUB_ID

echo "=== Management Groups ==="
itlc managementgroup list

echo "=== Available Locations ==="
itlc location list
```

## API Gateway Endpoints

The CLI uses ARM-style endpoints via the API Gateway:

```
# Tenants (global scope)
PUT    /providers/ITL.Core/tenants/{name}
GET    /providers/ITL.Core/tenants
GET    /providers/ITL.Core/tenants/{name}
DELETE /providers/ITL.Core/tenants/{name}

# Subscriptions (tenant scope)
PUT    /providers/ITL.Core/subscriptions/{name}
GET    /providers/ITL.Core/subscriptions?tenantId={id}
GET    /providers/ITL.Core/subscriptions/{name}
DELETE /providers/ITL.Core/subscriptions/{name}

# Resource Groups (subscription scope)
PUT    /subscriptions/{id}/resourceGroups/{name}
GET    /subscriptions/{id}/resourceGroups
GET    /subscriptions/{id}/resourceGroups/{name}
DELETE /subscriptions/{id}/resourceGroups/{name}

# Management Groups (global scope)
PUT    /providers/ITL.Core/managementGroups/{name}
GET    /providers/ITL.Core/managementGroups
GET    /providers/ITL.Core/managementGroups/{name}
DELETE /providers/ITL.Core/managementGroups/{name}

# Locations (global scope)
PUT    /providers/ITL.Core/locations/{name}
GET    /providers/ITL.Core/locations
GET    /providers/ITL.Core/locations/{name}
DELETE /providers/ITL.Core/locations/{name}
```

## Error Handling

The CLI provides clear error messages:

```bash
# Resource not found
$ itlc tenant get nonexistent
✗ Tenant 'nonexistent' not found

# Missing authentication
$ itlc tenant list
✗ Failed to list tenants
  - Check CONTROLPLANE_TOKEN is set
  - Verify API Gateway URL is correct

# Network error
$ itlc --api-url http://invalid tenant list
✗ Failed to list tenants
  - Verify API Gateway is running
  - Check firewall/network connectivity
```

## Output Formats

### JSON Output
```bash
itlc tenant list --output json
```
```json
{
  "value": [
    {
      "id": "/providers/ITL.Core/tenants/acme-corp",
      "name": "acme-corp",
      "type": "ITL.Core/tenants",
      "location": "westeurope",
      "properties": {
        "displayName": "ACME Corporation",
        "domain": "acme.com",
        "provisioningState": "Succeeded"
      },
      "tags": {
        "environment": "production"
      }
    }
  ]
}
```

### Table Output
```bash
itlc tenant list --output table
```
```
Found 2 tenant(s):

  • acme-corp (/providers/ITL.Core/tenants/acme-corp)
    Domain: acme.com
  • itl-corp (/providers/ITL.Core/tenants/itl-corp)
    Domain: itlusions.com
```

### ID Output (for scripting)
```bash
TENANT_ID=$(itlc tenant create my-tenant --output id)
echo $TENANT_ID
# /providers/ITL.Core/tenants/my-tenant
```

## Troubleshooting

### API Gateway Not Responding
```bash
# Check health
curl http://localhost:8080/health

# Verify API Gateway is running
docker ps | grep api-gateway

# Check logs
docker logs itl-api-gateway
```

### Authentication Failures
```bash
# Verify token is valid
itlc whoami

# Get fresh token
itlc login

# Test with explicit token
TOKEN=$(itlc get-token --client-id admin --client-secret secret --output token)
itlc tenant list --token $TOKEN
```

### Resource Already Exists
```bash
# Check if resource exists
itlc tenant get my-tenant

# Use different name or delete first
itlc tenant delete my-tenant --yes
itlc tenant create my-tenant
```

## Integration with Other Tools

### Bash Scripts
```bash
#!/bin/bash
set -e

# Setup
export CONTROLPLANE_API_URL="http://localhost:8080"
TOKEN=$(itlc get-token --client-id admin --client-secret $SECRET --output token)
export CONTROLPLANE_TOKEN=$TOKEN

# Create resources
TENANT=$(itlc tenant create demo-tenant --output id)
SUB=$(itlc subscription create demo-sub --tenant-id $TENANT --output id)
RG=$(itlc resourcegroup create demo-rg $SUB --location westeurope --output id)

echo "Created: $TENANT -> $SUB -> $RG"
```

### PowerShell Scripts
```powershell
# Setup
$env:CONTROLPLANE_API_URL = "http://localhost:8080"
$token = itlc get-token --client-id admin --client-secret $secret --output token
$env:CONTROLPLANE_TOKEN = $token

# Create resources
$tenant = itlc tenant create demo-tenant --output id
$sub = itlc subscription create demo-sub --tenant-id $tenant --output id
$rg = itlc resourcegroup create demo-rg $sub --location westeurope --output id

Write-Host "Created: $tenant -> $sub -> $rg"
```

### Python Integration
```python
import subprocess
import json
import os

# Setup
os.environ['CONTROLPLANE_API_URL'] = 'http://localhost:8080'
token = subprocess.check_output(['itlc', 'get-token', '--client-id', 'admin', 
                                '--client-secret', secret, '--output', 'token']).decode().strip()
os.environ['CONTROLPLANE_TOKEN'] = token

# Create tenant
result = subprocess.check_output(['itlc', 'tenant', 'create', 'my-tenant', '--output', 'json'])
tenant = json.loads(result)
print(f"Created tenant: {tenant['id']}")
```

## See Also

- [OIDC Setup Guide](OIDC_SETUP.md) - Authentication configuration
- [API Gateway Documentation](../../ITL.ControlPlane.Api/docs/) - API Gateway details
- [Core Provider Documentation](../../ITL.ControlPlane.ResourceProvider.Core/docs/) - Core Provider internals
