# ITL Control Plane CLI - Resource Management

## Overview

The ITLAuth CLI has been extended with resource management capabilities to interact with the ITL Control Plane API. Users can create and manage subscriptions, resource groups, locations, and deployments directly from the command line.

## Architecture

### Communication Modes

The CLI supports two communication modes:

1. **Direct Provider Communication** (default)
   - Connects directly to the ITL Control Plane API
   - Default URL: `http://localhost:8000`
   - Use for local development and testing
   - Set via: `CONTROLPLANE_URL` environment variable

2. **API Gateway Communication**
   - Routes requests through an API Gateway
   - Default URL: `https://api.itlusions.com`
   - Use for production environments
   - Set via: `CONTROLPLANE_GATEWAY_URL` environment variable
   - Enable with: `--gateway` flag in commands

### Control Plane Client

The `ControlPlaneClient` class (`controlplane_client.py`) provides:

- Health checks
- OpenAPI specification retrieval
- Subscription management (create, list, get, delete)
- Location listing
- Resource group management
- Deployment management
- Automatic subscription ID generation on the server side

## Features

### Subscription Management

Subscriptions are created with auto-generated IDs. The server generates a unique subscription_id if not provided by the client.

#### Create Subscription

```bash
itlc resource subscription create \
  --name my-subscription \
  --display-name "My Subscription" \
  --location westeurope \
  --state Enabled
```

Options:
- `--name` (required): Subscription resource name
- `--resource-group` (default: `default`): Resource group
- `--location` (default: `westeurope`): Azure location
- `--display-name`: User-friendly display name
- `--state` (default: `Enabled`): Subscription state
- `--api-url`: Custom API URL (overrides default)
- `--gateway`: Use API Gateway instead of direct connection
- `--output` (`-o`): Output format (json, table, yaml)

#### List Subscriptions

```bash
itlc resource subscription list
itlc resource subscription list --output json
itlc resource subscription list --gateway
```

#### Get Subscription

```bash
itlc resource subscription get my-subscription
itlc resource subscription get my-subscription --output json
```

#### Delete Subscription

```bash
itlc resource subscription delete my-subscription
itlc resource subscription delete my-subscription --force
```

### Location Management

#### List Available Locations

```bash
itlc resource location list
itlc resource location list --output json
```

Shows all 24+ available locations:
- US regions (East US, West US, Central US)
- European regions (West Europe, North Europe, etc.)
- City-specific locations
- CDN edge zones

### Resource Group Management

Resource groups organize resources within a subscription.

#### Create Resource Group

```bash
itlc resource resource-group create \
  --subscription-id my-subscription \
  --name my-rg \
  --location westeurope
```

Options:
- `--subscription-id` (required): Subscription ID
- `--name` (required): Resource group name
- `--location` (default: `westeurope`): Location
- `--display-name`: User-friendly display name
- `--api-url`: Custom API URL
- `--gateway`: Use API Gateway
- `--output` (`-o`): Output format

#### List Resource Groups

```bash
itlc resource resource-group list
itlc resource resource-group list --subscription-id my-subscription
```

## Environment Variables

```bash
# Keycloak Configuration
export KEYCLOAK_URL=https://sts.itlusions.com
export KEYCLOAK_REALM=itlusions

# Control Plane Configuration
export CONTROLPLANE_URL=http://localhost:8000          # Direct provider
export CONTROLPLANE_GATEWAY_URL=https://api.itlusions.com  # Gateway
```

## Output Formats

All commands support multiple output formats:

### Table (default)

```bash
itlc resource subscription list
```

```
cli-test-sub-01
  ID: /subscriptions/cli-test-sub-01
  Type: ITL.Core/subscriptions
  Display Name: CLI Test Subscription
  State: Enabled
```

### JSON

```bash
itlc resource subscription list --output json
```

```json
[
  {
    "id": "/subscriptions/cli-test-sub-01",
    "name": "cli-test-sub-01",
    "type": "ITL.Core/subscriptions",
    "location": "global",
    "properties": {
      "display_name": "CLI Test Subscription",
      "state": "Enabled"
    },
    "resource_guid": "c1361277-55b0-4e3f-91d6-47520fc4d1db"
  }
]
```

### YAML

```bash
itlc resource subscription list --output yaml
```

```yaml
- id: /subscriptions/cli-test-sub-01
  name: cli-test-sub-01
  type: ITL.Core/subscriptions
  location: global
  properties:
    display_name: CLI Test Subscription
    state: Enabled
  resource_guid: c1361277-55b0-4e3f-91d6-47520fc4d1db
```

## Workflow Examples

### Example 1: Create a Complete Infrastructure

```bash
# 1. Create subscription (server auto-generates ID)
itlc resource subscription create \
  --name prod-sub \
  --display-name "Production Subscription" \
  --location westeurope

# 2. Create resource group
itlc resource resource-group create \
  --subscription-id prod-sub \
  --name prod-rg \
  --display-name "Production RG" \
  --location westeurope

# 3. List all resources
itlc resource subscription list
itlc resource resource-group list --subscription-id prod-sub
```

### Example 2: Using API Gateway for Production

```bash
# Set environment variables for gateway
export CONTROLPLANE_GATEWAY_URL=https://api.itlusions.com

# Create subscription through gateway
itlc resource subscription create \
  --name prod-sub \
  --display-name "Production Subscription" \
  --gateway

# Or pass URL directly
itlc resource subscription list \
  --api-url https://api.itlusions.com \
  --gateway
```

### Example 3: JSON Output for Automation

```bash
# Get subscription as JSON for scripting
sub=$(itlc resource subscription create \
  --name automated-sub \
  --output json)

# Extract subscription ID
sub_id=$(echo $sub | jq -r '.name')
echo "Created subscription: $sub_id"

# Use in next command
itlc resource resource-group create \
  --subscription-id "$sub_id" \
  --name auto-rg
```

## Authentication

The CLI uses the Keycloak authentication configured via:

```bash
itlc login
```

After login, the authentication token is used for all Control Plane API calls.

### Authentication-less Testing

For local testing without full Keycloak setup, the test script uses the ControlPlaneClient directly:

```python
from itlc.controlplane_client import ControlPlaneClient

client = ControlPlaneClient(base_url='http://localhost:8000')
result = client.create_subscription(
    resource_name='test-sub',
    resource_group='test-rg',
    location='westeurope',
    display_name='Test Subscription'
)
```

## Error Handling

The CLI provides clear error messages:

```bash
# Connection error
$ itlc resource subscription list --api-url http://invalid-host:9999
✗ Cannot connect to Control Plane API at http://invalid-host:9999

# Authentication required
$ itlc resource subscription list
✗ Not authenticated. Run 'itlc login' first.

# Resource not found
$ itlc resource subscription get non-existent
✗ Subscription 'non-existent' not found
```

## Testing

### Run Integration Tests

```bash
cd ITLAuth
python test_cli_integration.py
```

This will:
1. Check API health
2. List 24+ available locations
3. Create a subscription (with auto-generated ID)
4. List subscriptions
5. Get subscription details
6. Create a resource group
7. List resource groups
8. Clean up (delete resource group and subscription)

### Test Results

```
============================================================
ITL Control Plane CLI - Integration Test
============================================================

[1] Checking API health...
✓ API is healthy

[2] Listing available locations...
✓ Found 24 locations

[3] Creating subscription...
✓ Subscription created successfully
  Name: cli-test-sub-01
  GUID: c1361277-55b0-4e3f-91d6-47520fc4d1db

[4] Listing subscriptions...
✓ Found 1 subscription(s)

[5] Getting subscription...
✓ Subscription retrieved

[6] Creating resource group...
✓ Resource group created successfully

[7] Listing resource groups...
✓ Found 1 resource group(s)

[8] Cleaning up...
✓ Cleanup successful

============================================================
✓ All tests passed!
============================================================
```

## Implementation Details

### Files Modified/Created

1. **`controlplane_client.py`** (NEW)
   - Complete Control Plane API client
   - 500+ lines of code
   - Supports direct and gateway communication
   - Handles all resource types

2. **`__main__.py`** (MODIFIED)
   - Added `resource` command group
   - Added subscription subcommands
   - Added location subcommands
   - Added resource-group subcommands
   - Added helper function for output formatting
   - 300+ new lines of code

3. **`__init__.py`** (MODIFIED)
   - Exported ControlPlaneClient

4. **`test_cli_integration.py`** (NEW)
   - Comprehensive integration test
   - Tests all major workflows
   - 200+ lines of code

### Subscription ID Auto-Generation

The API server automatically generates a unique UUID for each subscription if the `subscription_id` field is not provided in the request:

```python
# In Control Plane API (subscriptions.py)
subscription_id = request.subscription_id or str(uuid.uuid4())
```

The CLI leverages this by not requiring subscription_id:

```python
# CLI does not require subscription_id
result = client.create_subscription(
    resource_name=resource_name,
    resource_group=resource_group,
    location=location,
    display_name=display_name,
    state=state
    # subscription_id is auto-generated by server
)
```

## Future Enhancements

Potential future additions:

1. **Deployment management** - Create and manage deployments
2. **Resource parameters** - Support template parameters in deployments
3. **Policy management** - Create and assign policies
4. **Batch operations** - Bulk resource creation from files
5. **Export/Import** - Export resources as JSON/YAML
6. **Monitoring** - Integration with monitoring and logging
7. **RBAC** - Role-based access control
8. **Caching** - Cache frequently accessed resources

## Support

For issues or questions:

1. Check the help: `itlc resource --help`
2. Check subcommand help: `itlc resource subscription --help`
3. Review the integration test: `test_cli_integration.py`
4. Check API logs: `docker logs core-provider`

## API Reference

Full OpenAPI documentation available at:

```bash
itlc resource subscription list --api-url http://localhost:8000
# Then visit: http://localhost:8000/docs
```

Or retrieve the spec:

```bash
python -c "
from itlc.controlplane_client import ControlPlaneClient
client = ControlPlaneClient()
spec = client.get_openapi_spec()
print(json.dumps(spec, indent=2))
"
```
