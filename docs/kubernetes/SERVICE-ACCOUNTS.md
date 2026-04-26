# Service Accounts Management

## Overview

This guide covers managing service accounts for the ITLAuth authentication system. We provide both Kubernetes-native service accounts and Keycloak-based centralized service account management.

## Kubernetes Service Accounts

### Creating Traditional Service Accounts

For applications running inside the cluster that need to access the Kubernetes API:

```bash
# Create a service account
kubectl create serviceaccount my-app-sa -n my-namespace

# Create a role with specific permissions
kubectl create role my-app-role \
    --verb=get,list,watch \
    --resource=pods,services \
    -n my-namespace

# Bind the role to the service account
kubectl create rolebinding my-app-binding \
    --role=my-app-role \
    --serviceaccount=my-namespace:my-app-sa \
    -n my-namespace
```

### Service Account Tokens

Since Kubernetes 1.24, service account tokens are no longer automatically created. Create them manually:

```bash
# Create a secret for the service account token
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: my-app-sa-token
  namespace: my-namespace
  annotations:
    kubernetes.io/service-account.name: my-app-sa
type: kubernetes.io/service-account-token
EOF

# Get the token
kubectl get secret my-app-sa-token -n my-namespace -o jsonpath='{.data.token}' | base64 -d
```

## Keycloak-Based Service Accounts

### Overview

For centralized authentication and better integration with OIDC, you can create service accounts in Keycloak that can authenticate to Kubernetes.

### Creating Keycloak Service Accounts

#### Using Keycloak Admin Console

1. **Login to Keycloak Admin Console:**
   - Navigate to https://sts.itlusions.com/admin
   - Login with admin credentials

2. **Create Client for Service Account:**
   - Go to Clients → Create client
   - Client type: `OpenID Connect`
   - Client ID: `service-account-name`
   - Client authentication: `On`
   - Authorization: `Off`
   - Authentication flow: Uncheck all except "Service accounts roles"

3. **Configure Client:**
   - Go to Settings tab
   - Access Type: `confidential`
   - Service Accounts Enabled: `On`
   - Standard Flow Enabled: `Off`
   - Direct Access Grants Enabled: `Off`

4. **Get Client Credentials:**
   - Go to Credentials tab
   - Copy Client Secret

#### Using Keycloak Admin CLI

```bash
# Download and setup Keycloak admin CLI
curl -LO https://github.com/keycloak/keycloak/releases/download/22.0.1/keycloak-admin-cli-22.0.1.tar.gz
tar -xzf keycloak-admin-cli-22.0.1.tar.gz

# Login to Keycloak
./kcadm.sh config credentials \
    --server https://sts.itlusions.com \
    --realm master \
    --user admin

# Create service account client
./kcadm.sh create clients -r itlusions -s clientId=my-service-account -s serviceAccountsEnabled=true -s standardFlowEnabled=false -s directAccessGrantsEnabled=false

# Get client secret
./kcadm.sh get clients/my-service-account/client-secret -r itlusions
```

#### Using PowerShell Script

```powershell
# ITLAuth Service Account Creation Script
param(
    [Parameter(Mandatory=$true)]
    [string]$ServiceAccountName,
    
    [Parameter(Mandatory=$true)]
    [string]$Description,
    
    [string]$KeycloakServer = "https://sts.itlusions.com",
    [string]$Realm = "itlusions",
    [string]$AdminUser = "admin"
)

# Function to create Keycloak service account
function New-KeycloakServiceAccount {
    param($Name, $Description, $Server, $Realm, $AdminUser)
    
    Write-Host "Creating Keycloak service account: $Name" -ForegroundColor Green
    
    # Get admin token
    $adminToken = Get-KeycloakAdminToken -Server $Server -User $AdminUser
    
    # Create client configuration
    $clientConfig = @{
        clientId = $Name
        name = $Description
        description = $Description
        serviceAccountsEnabled = $true
        standardFlowEnabled = $false
        directAccessGrantsEnabled = $false
        implicitFlowEnabled = $false
        publicClient = $false
        protocol = "openid-connect"
    } | ConvertTo-Json
    
    # Create client
    $createUrl = "$Server/admin/realms/$Realm/clients"
    $headers = @{
        "Authorization" = "Bearer $adminToken"
        "Content-Type" = "application/json"
    }
    
    try {
        $response = Invoke-RestMethod -Uri $createUrl -Method POST -Body $clientConfig -Headers $headers
        Write-Host "Service account created successfully" -ForegroundColor Green
        
        # Get client details
        $clientsUrl = "$Server/admin/realms/$Realm/clients?clientId=$Name"
        $client = Invoke-RestMethod -Uri $clientsUrl -Method GET -Headers $headers
        $clientUuid = $client[0].id
        
        # Get client secret
        $secretUrl = "$Server/admin/realms/$Realm/clients/$clientUuid/client-secret"
        $secret = Invoke-RestMethod -Uri $secretUrl -Method GET -Headers $headers
        
        return @{
            ClientId = $Name
            ClientSecret = $secret.value
            ClientUuid = $clientUuid
        }
    }
    catch {
        Write-Error "Failed to create service account: $($_.Exception.Message)"
        return $null
    }
}

# Create the service account
$serviceAccount = New-KeycloakServiceAccount -Name $ServiceAccountName -Description $Description -Server $KeycloakServer -Realm $Realm -AdminUser $AdminUser

if ($serviceAccount) {
    Write-Host "`nService Account Created:" -ForegroundColor Green
    Write-Host "Client ID: $($serviceAccount.ClientId)"
    Write-Host "Client Secret: $($serviceAccount.ClientSecret)"
    Write-Host "`nSave these credentials securely!"
}
```

### Assigning Permissions to Keycloak Service Accounts

#### Map to Kubernetes Groups

1. **Create Kubernetes group mapping in Keycloak:**
   - Go to Clients → your-service-account → Service account roles
   - Assign realm roles or client roles as needed

2. **Create client mapper for groups:**
   - Go to Clients → your-service-account → Client scopes → your-service-account-dedicated → Mappers
   - Create mapper:
     - Name: `groups`
     - Mapper Type: `Group Membership`
     - Token Claim Name: `groups`
     - Full group path: `Off`

#### Create Kubernetes RBAC

```bash
# Create ClusterRoleBinding for service account
kubectl create clusterrolebinding my-service-account-binding \
    --clusterrole=view \
    --group=service-accounts

# Or create custom role
kubectl apply -f - <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: service-account-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: service-account-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: service-account-role
subjects:
- apiGroup: rbac.authorization.k8s.io
  kind: Group
  name: service-accounts
EOF
```

### Using Service Accounts

#### Authentication with Client Credentials

```bash
# Get token using client credentials flow
curl -X POST https://sts.itlusions.com/realms/itlusions/protocol/openid-connect/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=client_credentials" \
    -d "client_id=my-service-account" \
    -d "client_secret=your-client-secret"
```

#### Using with kubectl

```bash
# Configure kubectl to use the service account token
kubectl config set-credentials my-service-account \
    --auth-provider=oidc \
    --auth-provider-arg=idp-issuer-url=https://sts.itlusions.com/realms/itlusions \
    --auth-provider-arg=client-id=my-service-account \
    --auth-provider-arg=client-secret=your-client-secret \
    --auth-provider-arg=refresh-token=your-refresh-token

# Or use kubelogin with service account
kubectl config set-credentials my-service-account \
    --exec-api-version=client.authentication.k8s.io/v1beta1 \
    --exec-command=kubelogin \
    --exec-arg=get-token \
    --exec-arg=--oidc-issuer-url=https://sts.itlusions.com/realms/itlusions \
    --exec-arg=--oidc-client-id=my-service-account \
    --exec-arg=--oidc-client-secret=your-client-secret \
    --exec-arg=--grant-type=client_credentials
```

#### In Applications

**Go Example:**
```go
package main

import (
    "context"
    "fmt"
    "golang.org/x/oauth2/clientcredentials"
    "k8s.io/client-go/kubernetes"
    "k8s.io/client-go/rest"
)

func main() {
    // Configure OAuth2 client credentials
    config := clientcredentials.Config{
        ClientID:     "my-service-account",
        ClientSecret: "your-client-secret",
        TokenURL:     "https://sts.itlusions.com/realms/itlusions/protocol/openid-connect/token",
    }
    
    // Get token
    token, err := config.Token(context.Background())
    if err != nil {
        panic(err)
    }
    
    // Create Kubernetes client
    kubeConfig := &rest.Config{
        Host:        "https://your-k8s-api-server:6443",
        BearerToken: token.AccessToken,
    }
    
    clientset, err := kubernetes.NewForConfig(kubeConfig)
    if err != nil {
        panic(err)
    }
    
    // Use the client
    pods, err := clientset.CoreV1().Pods("default").List(context.TODO(), metav1.ListOptions{})
    if err != nil {
        panic(err)
    }
    
    fmt.Printf("Found %d pods\n", len(pods.Items))
}
```

**Python Example:**
```python
import requests
import kubernetes
from kubernetes import client, config

def get_service_account_token(client_id, client_secret):
    """Get token using client credentials flow"""
    token_url = "https://sts.itlusions.com/realms/itlusions/protocol/openid-connect/token"
    
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    response = requests.post(token_url, data=data)
    response.raise_for_status()
    
    return response.json()["access_token"]

# Get token
token = get_service_account_token("my-service-account", "your-client-secret")

# Configure Kubernetes client
configuration = client.Configuration()
configuration.host = "https://your-k8s-api-server:6443"
configuration.api_key = {"authorization": f"Bearer {token}"}
configuration.api_key_prefix = {"authorization": "Bearer"}

# Create API client
api_client = client.ApiClient(configuration)
v1 = client.CoreV1Api(api_client)

# List pods
pods = v1.list_pod_for_all_namespaces()
print(f"Found {len(pods.items)} pods")
```

## Automation Scripts

### Batch Service Account Creation

Create multiple service accounts with different permissions:

```bash
#!/bin/bash
# create-service-accounts.sh

KEYCLOAK_SERVER="https://sts.itlusions.com"
REALM="itlusions"

# Service accounts configuration
declare -A SERVICE_ACCOUNTS=(
    ["monitoring-sa"]="Monitoring and metrics collection"
    ["backup-sa"]="Backup and restore operations"
    ["ci-cd-sa"]="CI/CD pipeline automation"
    ["logging-sa"]="Log collection and processing"
)

# Function to create service account
create_service_account() {
    local name=$1
    local description=$2
    
    echo "Creating service account: $name"
    
    # Create Keycloak client (simplified - add actual implementation)
    # ... Keycloak API calls ...
    
    # Create Kubernetes RBAC
    kubectl apply -f - <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: ${name}-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: view  # Adjust as needed
subjects:
- apiGroup: rbac.authorization.k8s.io
  kind: Group
  name: ${name}-group
EOF
}

# Create all service accounts
for sa_name in "${!SERVICE_ACCOUNTS[@]}"; do
    create_service_account "$sa_name" "${SERVICE_ACCOUNTS[$sa_name]}"
done
```

### Service Account Token Refresh

Automate token refresh for long-running services:

```python
#!/usr/bin/env python3
# token-refresher.py

import time
import requests
import yaml
import os
from datetime import datetime, timedelta

class ServiceAccountTokenManager:
    def __init__(self, config_file):
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.tokens = {}
    
    def get_token(self, service_account):
        """Get or refresh token for service account"""
        config = self.config['service_accounts'][service_account]
        
        # Check if token exists and is valid
        if service_account in self.tokens:
            token_info = self.tokens[service_account]
            if datetime.now() < token_info['expires_at']:
                return token_info['access_token']
        
        # Get new token
        token_url = f"{self.config['keycloak']['server']}/realms/{self.config['keycloak']['realm']}/protocol/openid-connect/token"
        
        data = {
            "grant_type": "client_credentials",
            "client_id": config['client_id'],
            "client_secret": config['client_secret']
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        
        # Store token with expiration
        expires_in = token_data.get('expires_in', 3600)
        self.tokens[service_account] = {
            'access_token': token_data['access_token'],
            'expires_at': datetime.now() + timedelta(seconds=expires_in - 60)  # Refresh 1 minute early
        }
        
        return token_data['access_token']
    
    def refresh_all_tokens(self):
        """Refresh all service account tokens"""
        for sa_name in self.config['service_accounts']:
            try:
                token = self.get_token(sa_name)
                print(f"Refreshed token for {sa_name}")
            except Exception as e:
                print(f"Failed to refresh token for {sa_name}: {e}")

if __name__ == "__main__":
    manager = ServiceAccountTokenManager("service-accounts.yaml")
    
    while True:
        manager.refresh_all_tokens()
        time.sleep(300)  # Check every 5 minutes
```

## Security Best Practices

### Service Account Security

1. **Minimal Permissions:**
   - Grant only necessary permissions
   - Use namespace-specific roles when possible
   - Avoid cluster-admin unless absolutely required

2. **Secret Management:**
   - Store client secrets securely (Vault, Azure Key Vault, etc.)
   - Rotate secrets regularly
   - Never log or expose secrets

3. **Token Lifecycle:**
   - Use short-lived tokens
   - Implement automatic refresh
   - Monitor token usage

4. **Audit and Monitoring:**
   - Log all service account activities
   - Monitor for unusual access patterns
   - Set up alerts for failed authentications

### Example Security Configuration

```yaml
# service-account-security.yaml
apiVersion: v1
kind: Secret
metadata:
  name: monitoring-sa-secret
  namespace: monitoring
type: Opaque
data:
  client-id: bW9uaXRvcmluZy1zYQ==  # base64 encoded
  client-secret: <base64-encoded-secret>
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: monitoring
  name: monitoring-reader
rules:
- apiGroups: [""]
  resources: ["pods", "services", "endpoints"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: monitoring-sa-binding
  namespace: monitoring
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: monitoring-reader
subjects:
- apiGroup: rbac.authorization.k8s.io
  kind: Group
  name: monitoring-group
```

## Troubleshooting Service Accounts

### Common Issues

1. **Authentication Failures:**
   - Verify client credentials
   - Check token expiration
   - Validate OIDC configuration

2. **Permission Denied:**
   - Check RBAC bindings
   - Verify group mappings
   - Review service account roles

3. **Token Not Accepted:**
   - Verify audience claim
   - Check issuer URL
   - Validate token signature

### Debugging Commands

```bash
# Test service account authentication
curl -X POST https://sts.itlusions.com/realms/itlusions/protocol/openid-connect/token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=client_credentials" \
    -d "client_id=my-service-account" \
    -d "client_secret=your-client-secret" | jq .

# Decode JWT token
echo "your-jwt-token" | cut -d. -f2 | base64 -d | jq .

# Check Kubernetes permissions
kubectl auth can-i --list --as=system:serviceaccount:namespace:serviceaccount-name
```

## Migration from Kubernetes Service Accounts

If you're migrating from traditional Kubernetes service accounts to Keycloak-based ones:

1. **Audit existing service accounts:**
   ```bash
   kubectl get serviceaccounts --all-namespaces
   ```

2. **Document current permissions:**
   ```bash
   kubectl describe rolebinding,clusterrolebinding | grep -A5 -B5 serviceaccount
   ```

3. **Create equivalent Keycloak service accounts**
4. **Update applications gradually**
5. **Clean up old service accounts after migration**

This approach provides centralized management while maintaining security and functionality.