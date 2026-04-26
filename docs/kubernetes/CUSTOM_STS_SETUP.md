# Custom STS Setup Guide

This guide explains how to configure ITLC CLI to work with your own Keycloak or OpenID Connect (OIDC) provider.

## Overview

ITLC CLI is designed to work with any Keycloak or OIDC-compliant authentication server. While it's pre-configured for ITLusions STS (`https://sts.itlusions.com`), you can easily adapt it for your own environment.

## Prerequisites

- Access to a Keycloak server (version 20+) or OIDC-compliant provider
- Admin credentials for client configuration
- Python 3.8+ installed
- Network access to your STS from the machine running ITLC

## Architecture

```
┌─────────────────┐
│   ITLC CLI      │
│   (localhost)   │
└────────┬────────┘
         │
         │ 1. Opens browser with auth URL
         │
    ┌────▼─────────────────────────┐
    │  Your Keycloak/STS Server    │
    │  (e.g., sts.yourcompany.com) │
    └────┬─────────────────────────┘
         │
         │ 2. User authenticates
         │
    ┌────▼──────────────┐
    │  Callback Server  │
    │  localhost:8765   │
    └───────────────────┘
```

## Step 1: Create Keycloak Client

### Option A: Using Keycloak Admin UI

1. **Login to Keycloak Admin Console**
   ```
   https://your-keycloak-server.com/admin
   ```

2. **Select Your Realm**
   - Navigate to the realm where you want to create the client
   - Example: `production`, `master`, or custom realm name

3. **Create New Client**
   - Go to **Clients** → **Create client**
   - Fill in the following:

   | Field | Value |
   |-------|-------|
   | **Client ID** | `itl-cli` (or your preferred name) |
   | **Name** | `ITL CLI Token Manager` |
   | **Description** | `CLI tool for interactive authentication` |
   | **Client Protocol** | `openid-connect` |
   | **Client Type** | `Public` |

4. **Configure Client Settings**

   **Capability config:**
   - ✅ **Client authentication**: OFF (public client)
   - ✅ **Authorization**: OFF
   - ✅ **Standard flow**: ON
   - ❌ **Direct access grants**: OFF
   - ❌ **Implicit flow**: OFF
   - ❌ **Service accounts roles**: OFF

   **Login settings:**
   - **Root URL**: Leave empty
   - **Home URL**: Leave empty
   - **Valid redirect URIs**: `http://localhost:8765/callback`
   - **Valid post logout redirect URIs**: `+`
   - **Web origins**: `http://localhost:8765`

   **Advanced settings:**
   - **Proof Key for Code Exchange (PKCE)**: 
     - PKCE Code Challenge Method: `S256` (required)
   - **OAuth 2.0 Device Authorization Grant**: OFF

5. **Save the Client**

### Option B: Using Keycloak Admin CLI (kcadm.sh)

Create a JSON file `itl-cli-client.json`:

```json
{
  "clientId": "itl-cli",
  "name": "ITL CLI Token Manager",
  "description": "CLI tool for interactive authentication",
  "rootUrl": "",
  "adminUrl": "",
  "baseUrl": "",
  "surrogateAuthRequired": false,
  "enabled": true,
  "alwaysDisplayInConsole": false,
  "clientAuthenticatorType": "client-secret",
  "redirectUris": [
    "http://localhost:8765/callback"
  ],
  "webOrigins": [
    "http://localhost:8765"
  ],
  "notBefore": 0,
  "bearerOnly": false,
  "consentRequired": false,
  "standardFlowEnabled": true,
  "implicitFlowEnabled": false,
  "directAccessGrantsEnabled": false,
  "serviceAccountsEnabled": false,
  "publicClient": true,
  "frontchannelLogout": false,
  "protocol": "openid-connect",
  "attributes": {
    "pkce.code.challenge.method": "S256",
    "post.logout.redirect.uris": "+",
    "oauth2.device.authorization.grant.enabled": "false"
  },
  "authenticationFlowBindingOverrides": {},
  "fullScopeAllowed": true,
  "nodeReRegistrationTimeout": -1,
  "protocolMappers": [],
  "defaultClientScopes": [
    "web-origins",
    "acr",
    "profile",
    "roles",
    "email"
  ],
  "optionalClientScopes": [
    "address",
    "phone",
    "offline_access",
    "microprofile-jwt"
  ]
}
```

Create the client:

```bash
# Login to Keycloak admin
kcadm.sh config credentials \
  --server https://your-keycloak-server.com \
  --realm master \
  --user admin

# Create the client in your target realm
kcadm.sh create clients -r your-realm-name -f itl-cli-client.json
```

### Option C: Using kubectl (Kubernetes Deployment)

If Keycloak is running in Kubernetes:

```bash
# Find Keycloak pod
kubectl get pods -n keycloak-namespace

# Copy client JSON to pod
kubectl cp itl-cli-client.json keycloak-namespace/keycloak-pod:/tmp/

# Login to kcadm
kubectl exec -n keycloak-namespace keycloak-pod -- \
  /opt/keycloak/bin/kcadm.sh config credentials \
  --server https://your-keycloak-server.com \
  --realm master \
  --user admin

# Create client
kubectl exec -n keycloak-namespace keycloak-pod -- \
  /opt/keycloak/bin/kcadm.sh create clients \
  -r your-realm-name \
  -f /tmp/itl-cli-client.json
```

## Step 2: Configure ITLC CLI

### Method 1: Environment Variables

Create a configuration file or set environment variables:

```bash
# Windows PowerShell
$env:KEYCLOAK_SERVER = "https://sts.yourcompany.com"
$env:KEYCLOAK_REALM = "production"
$env:KEYCLOAK_CLIENT_ID = "itl-cli"

# Linux/macOS
export KEYCLOAK_SERVER="https://sts.yourcompany.com"
export KEYCLOAK_REALM="production"
export KEYCLOAK_CLIENT_ID="itl-cli"
```

Make these permanent:

**Windows:**
```powershell
[System.Environment]::SetEnvironmentVariable('KEYCLOAK_SERVER', 'https://sts.yourcompany.com', 'User')
[System.Environment]::SetEnvironmentVariable('KEYCLOAK_REALM', 'production', 'User')
[System.Environment]::SetEnvironmentVariable('KEYCLOAK_CLIENT_ID', 'itl-cli', 'User')
```

**Linux/macOS (add to ~/.bashrc or ~/.zshrc):**
```bash
export KEYCLOAK_SERVER="https://sts.yourcompany.com"
export KEYCLOAK_REALM="production"
export KEYCLOAK_CLIENT_ID="itl-cli"
```

### Method 2: Configuration File

Create `~/.itl/config.yaml`:

```yaml
keycloak:
  server: https://sts.yourcompany.com
  realm: production
  client_id: itl-cli

# Optional: Override callback port (default: 8765)
callback:
  port: 8765
  host: localhost

# Optional: Token cache settings
cache:
  enabled: true
  directory: ~/.itl/token-cache
  
# Optional: Context storage
context:
  file: ~/.itl/context.json
```

### Method 3: Command-Line Parameters

Use command-line flags to override defaults:

```bash
itlc login \
  --server https://sts.yourcompany.com \
  --realm production \
  --client-id itl-cli
```

## Step 3: Customize ITLC Code (Advanced)

If you want to hardcode your STS configuration, modify the source:

**Edit `src/itlc/interactive_auth.py`:**

```python
class InteractiveAuth:
    def __init__(
        self,
        keycloak_url: str = "https://sts.yourcompany.com",  # Change this
        realm: str = "production",  # Change this
        client_id: str = "itl-cli",  # Change this
        redirect_uri: str = "http://localhost:8765/callback",
        context_file: Optional[Path] = None
    ):
```

**Rebuild and install:**

```bash
cd ITLAuth
pip install -e .
```

## Step 4: Test Authentication

1. **Check Available Realms:**
   ```bash
   itlc realm list
   ```
   
   Expected output:
   ```
   Available realms:
   - production
   - development
   - staging
   ```

2. **Set Your Target Realm:**
   ```bash
   itlc realm set production
   ```

3. **Test Interactive Login:**
   ```bash
   itlc login
   ```
   
   Expected flow:
   ```
   [*] Starting interactive login for realm: production
   [*] Opening browser for authentication...
   [*] Listening on http://localhost:8765
   ```
   
   - Browser opens to your Keycloak login page
   - Authenticate with your credentials
   - Success page displays
   - Terminal shows: `[✓] Login successful!`

4. **Verify Authentication:**
   ```bash
   itlc whoami
   ```
   
   Expected output:
   ```
   User Information:
   ┌──────────────────┬─────────────────────────────┐
   │ Field            │ Value                       │
   ├──────────────────┼─────────────────────────────┤
   │ Subject (sub)    │ a1b2c3d4-5678-90ab-cdef     │
   │ Email            │ user@yourcompany.com        │
   │ Email Verified   │ True                        │
   │ Name             │ John Doe                    │
   │ Preferred Username│ john.doe                   │
   │ Realm            │ production                  │
   │ Client ID        │ itl-cli                     │
   └──────────────────┴─────────────────────────────┘
   ```

## Step 5: Configure Callback Page Branding (Optional)

Customize the OAuth callback page to match your company branding:

**Edit `src/itlc/callback_success.html`:**

```html
<!-- Change gradient colors -->
<style>
    body {
        background: linear-gradient(135deg, #YOUR_COLOR_1 0%, #YOUR_COLOR_2 100%);
    }
    .icon {
        background: linear-gradient(135deg, #YOUR_COLOR_1 0%, #YOUR_COLOR_2 100%);
    }
</style>

<!-- Change branding text -->
<div class="brand">Your Company Token Manager</div>
```

**Edit `src/itlc/callback_error.html`** similarly.

**Rebuild:**
```bash
pip install -e .
```

## Multi-Realm Configuration

If your organization has multiple Keycloak realms (dev, staging, prod):

### Create Realm Profiles

**~/.itl/realms.yaml:**

```yaml
realms:
  development:
    server: https://sts-dev.yourcompany.com
    realm: dev
    client_id: itl-cli-dev
  
  staging:
    server: https://sts-staging.yourcompany.com
    realm: staging
    client_id: itl-cli-staging
  
  production:
    server: https://sts.yourcompany.com
    realm: production
    client_id: itl-cli
```

### Switch Between Realms

```bash
# List available realms
itlc realm list

# Switch to development
itlc realm set development
itlc login

# Switch to production
itlc realm set production
itlc login
```

## Troubleshooting

### Issue: Browser doesn't open

**Solution 1: Manual URL**
```bash
# Copy the URL from terminal output and paste in browser
itlc login
# [*] Opening browser for authentication...
# [*] URL: https://sts.yourcompany.com/realms/...
```

**Solution 2: Check firewall**
```bash
# Ensure localhost:8765 is not blocked
netstat -an | findstr 8765  # Windows
netstat -an | grep 8765     # Linux/macOS
```

### Issue: Redirect URI mismatch

**Error:**
```
Invalid parameter: redirect_uri
```

**Solution:**
1. Verify callback URL in Keycloak client matches exactly: `http://localhost:8765/callback`
2. Check for trailing slashes (should NOT have trailing slash)
3. Ensure protocol is `http` (not `https`) for localhost

### Issue: PKCE not enabled

**Error:**
```
Client requires PKCE but challenge was not provided
```

**Solution:**
1. In Keycloak client settings, set:
   - **Proof Key for Code Exchange (PKCE)**: S256
2. Ensure client is **Public** type (not Confidential)

### Issue: Invalid client

**Error:**
```
Client not found or client authentication failed
```

**Solution:**
1. Verify client exists in correct realm
   ```bash
   # Using kcadm
   kcadm.sh get clients -r your-realm --fields clientId,enabled
   ```
2. Check client is enabled
3. Verify client ID matches exactly (case-sensitive)

### Issue: Token expired immediately

**Symptom:**
```bash
itlc get-token
# Error: Token expired
```

**Solution:**
Adjust token lifespans in Keycloak:
1. Realm Settings → Tokens
2. **Access Token Lifespan**: 5 minutes (minimum)
3. **SSO Session Idle**: 30 minutes
4. **SSO Session Max**: 10 hours

### Issue: Network connection failed

**Error:**
```
Failed to connect to Keycloak server
```

**Solution:**
1. Verify server URL is correct
   ```bash
   curl https://sts.yourcompany.com/realms/production/.well-known/openid-configuration
   ```
2. Check DNS resolution
   ```bash
   nslookup sts.yourcompany.com
   ```
3. Test TLS certificate
   ```bash
   openssl s_client -connect sts.yourcompany.com:443
   ```
4. Check corporate proxy settings
   ```bash
   # Windows
   netsh winhttp show proxy
   
   # Linux/macOS
   echo $HTTP_PROXY
   echo $HTTPS_PROXY
   ```

## Advanced Configuration

### Custom Callback Port

If port 8765 is already in use:

**Edit `src/itlc/interactive_auth.py`:**

```python
def _start_callback_server(self) -> HTTPServer:
    server = HTTPServer(('localhost', 9876), CallbackHandler)  # Change port
    return server
```

**Update Keycloak client redirect URI:**
```
http://localhost:9876/callback
```

### Corporate Proxy Support

**Set proxy environment variables:**

```bash
# Windows PowerShell
$env:HTTP_PROXY = "http://proxy.company.com:8080"
$env:HTTPS_PROXY = "http://proxy.company.com:8080"
$env:NO_PROXY = "localhost,127.0.0.1"

# Linux/macOS
export HTTP_PROXY="http://proxy.company.com:8080"
export HTTPS_PROXY="http://proxy.company.com:8080"
export NO_PROXY="localhost,127.0.0.1"
```

ITLC will automatically use these proxies for Keycloak API calls.

### Custom Scopes

Request additional OIDC scopes:

**Edit `src/itlc/interactive_auth.py`:**

```python
params = {
    'client_id': self.client_id,
    'redirect_uri': self.redirect_uri,
    'response_type': 'code',
    'scope': 'openid email profile groups roles',  # Add custom scopes
    'code_challenge': code_challenge,
    'code_challenge_method': 'S256',
    'state': state
}
```

## Security Best Practices

1. **Always use HTTPS** for production Keycloak servers
2. **Enable PKCE S256** for public clients (ITLC default)
3. **Use short-lived access tokens** (5-15 minutes)
4. **Enable refresh token rotation** in Keycloak
5. **Restrict redirect URIs** to localhost only
6. **Audit token usage** via Keycloak admin events
7. **Revoke tokens on logout**:
   ```bash
   itlc logout  # Clears local context and cached tokens
   ```
8. **Rotate client secrets** regularly (if using confidential clients)

## Integration Examples

### Use with API Calls

```bash
# Get token and use with curl
TOKEN=$(itlc get-token)
curl -H "Authorization: Bearer $TOKEN" https://api.yourcompany.com/resource
```

### Use with Python Requests

```python
import subprocess
import requests

# Get token from ITLC
token = subprocess.check_output(['itlc', 'get-token']).decode().strip()

# Use in API call
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('https://api.yourcompany.com/resource', headers=headers)
```

### Use with Kubernetes kubectl

```bash
# Get token
TOKEN=$(itlc get-token)

# Use with kubectl
kubectl --token="$TOKEN" get pods
```

## Support

For issues specific to ITLC CLI:
- GitHub: https://github.com/itlusions/ITLAuth
- Documentation: https://docs.itlusions.com/itlauth

For Keycloak configuration issues:
- Keycloak Documentation: https://www.keycloak.org/documentation
- Community: https://keycloak.discourse.group/

## Next Steps

- [Interactive Login Guide](INTERACTIVE_LOGIN.md)
- [Service Accounts Setup](SERVICE-ACCOUNTS.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [API Integration Examples](../examples/)
