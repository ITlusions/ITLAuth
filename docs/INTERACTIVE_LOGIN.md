# Azure CLI-Style Interactive Login

The ITL Token CLI now supports Azure CLI-style interactive login with browser-based authentication!

## Overview

Just like `az login`, you can now use `itlc login` to authenticate interactively with your browser.

## Commands Comparison

| Azure CLI | ITL Token CLI | Description |
|-----------|---------------|-------------|
| `az login` | `itlc login` | Interactive browser login |
| `az account list` | `itlc realm list` | List available realms/tenants |
| `az account set` | `itlc realm set` | Set default realm/tenant |
| `az account show` | `itlc realm show` | Show current realm |
| `az account show` | `itlc whoami` | Show user info |
| `az logout` | `itlc logout` | Logout and clear context |

## Quick Start

### 1. Interactive Login

```bash
# Login to default realm (itlusions)
itlc login

# Login to specific realm
itlc login --realm=production

# Login to different Keycloak instance
itlc login --keycloak-url=https://auth.example.com --realm=dev
```

**What happens:**
1. Opens browser automatically
2. You authenticate with Keycloak (EntraID/GitHub/password)
3. Returns to terminal with success message
4. Token saved to `~/.itl/context.json`

### 2. Check Who You Are

```bash
itlc whoami
```

Output:
```
User Information:

Username: niels.weistra
Email: niels.weistra@itlusions.com
Name: Niels Weistra
Realm: itlusions
Keycloak URL: https://sts.itlusions.com
```

### 3. Manage Realms/Tenants

```bash
# List available realms
itlc realm list

# Output:
# Available Realms:
# * itlusions       (current)
#   production
#   development

# Switch to different realm
itlc realm set production

# Show current realm
itlc realm show
```

### 4. Logout

```bash
itlc logout
```

## Authentication Modes

The CLI now supports **two authentication modes**:

### Mode 1: Interactive Login (User Token)

```bash
# Login once
itlc login

# Token is cached, use for API calls
TOKEN=$(itlc get-token --output=token)
curl -H "Authorization: Bearer $TOKEN" https://api.example.com
```

**Use cases:**
- Personal development
- Interactive sessions
- Desktop applications

### Mode 2: Service Account (Machine Token)

```bash
# Set credentials
export KEYCLOAK_CLIENT_ID=my-service-account
export KEYCLOAK_CLIENT_SECRET=secret

# Get token
TOKEN=$(itlc get-token --output=token)
curl -H "Authorization: Bearer $TOKEN" https://api.example.com
```

**Use cases:**
- CI/CD pipelines
- Server applications
- Background jobs

## Workflow Examples

### Developer Workflow

```bash
# Morning: Login once
itlc login

# Check who you are
itlc whoami

# Work all day, tokens auto-refresh
itlc get-token --output=token

# Evening: Logout (optional)
itlc logout
```

### Multi-Environment Workflow

```bash
# Login to development
itlc login --realm=development

# Do some work
itlc get-token --output=token

# Switch to production
itlc realm set production

# Work with production
itlc get-token --output=token

# Check current realm
itlc realm show
```

### CI/CD Workflow

```bash
# Use service account (no interactive login)
export KEYCLOAK_CLIENT_ID=${{ secrets.CLIENT_ID }}
export KEYCLOAK_CLIENT_SECRET=${{ secrets.CLIENT_SECRET }}

# Get token
TOKEN=$(itlc get-token --output=token)

# Use in pipeline
curl -H "Authorization: Bearer $TOKEN" https://api.example.com/deploy
```

## Context Storage

### Location

- **Windows**: `C:\Users\<username>\.itl\context.json`
- **Linux/Mac**: `~/.itl/context.json`

### Contents

```json
{
  "realm": "itlusions",
  "keycloak_url": "https://sts.itlusions.com",
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "id_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "openid profile email"
}
```

## OAuth Flow Details

The CLI uses **Authorization Code Flow with PKCE** (Proof Key for Code Exchange):

1. **Generate PKCE pair**: code_verifier + code_challenge
2. **Open browser**: Navigate to Keycloak authorization endpoint
3. **User authenticates**: Login with credentials/SSO
4. **Callback**: Keycloak redirects to `http://localhost:8765/callback`
5. **Exchange code**: CLI exchanges authorization code for tokens
6. **Save context**: Tokens saved to `~/.itl/context.json`

### Security Features

- ✅ **PKCE**: Prevents authorization code interception
- ✅ **Local callback**: No token in browser URL
- ✅ **Short-lived**: Access tokens expire (default 60 minutes)
- ✅ **Refresh tokens**: Automatic token renewal
- ✅ **Secure storage**: Tokens in user home directory

## Advanced Usage

### Custom Client ID

By default, the CLI uses client ID `itl-cli`. To use a different client:

1. **Configure Keycloak client**:
   - Create public client in Keycloak
   - Enable "Standard Flow" (Authorization Code)
   - Add redirect URI: `http://localhost:8765/callback`
   - Enable PKCE

2. **Use custom client** (future feature):
   ```bash
   itlc login --client-id=my-custom-cli
   ```

### Different Callback Port

If port 8765 is in use, the CLI will fail. Future feature:

```bash
itlc login --callback-port=9000
```

### Token Refresh

Tokens are automatically refreshed when expired:

```bash
# First call: uses cached token
itlc get-token

# Token expires...

# Next call: automatically refreshes
itlc get-token
```

## Troubleshooting

### Browser Doesn't Open

```bash
# Manual authentication
itlc login

# Copy the URL from terminal output and open manually
# Complete authentication in browser
# Terminal will detect the callback
```

### Port Already in Use

```
Error: Address already in use (port 8765)
```

**Solution**: Kill process using port 8765
```bash
# Windows
netstat -ano | findstr :8765
taskkill /PID <pid> /F

# Linux/Mac
lsof -i :8765
kill -9 <pid>
```

### Login Timeout

```
[✗] Login timeout. Please try again.
```

**Solution**: Complete authentication within 5 minutes, or login again

### Token Expired

```bash
# Clear context and login again
itlc logout
itlc login
```

### Keycloak Client Not Found

```
Error: Client 'itl-cli' not found in realm 'itlusions'
```

**Solution**: Contact admin to create `itl-cli` public client with:
- Client ID: `itl-cli`
- Client Protocol: `openid-connect`
- Access Type: `public`
- Standard Flow Enabled: `ON`
- Valid Redirect URIs: `http://localhost:8765/callback`
- Web Origins: `http://localhost:8765`

## Comparison with Azure CLI

| Feature | Azure CLI | ITL Token CLI | Status |
|---------|-----------|---------------|--------|
| Interactive login | ✅ `az login` | ✅ `itlc login` | Complete |
| Device code flow | ✅ `az login --use-device-code` | ⏳ Planned | Future |
| Service principal | ✅ `az login --service-principal` | ✅ `itlc get-token` | Complete |
| List tenants | ✅ `az account list` | ✅ `itlc realm list` | Complete |
| Set tenant | ✅ `az account set` | ✅ `itlc realm set` | Complete |
| Show account | ✅ `az account show` | ✅ `itlc whoami` | Complete |
| Logout | ✅ `az logout` | ✅ `itlc logout` | Complete |
| Token refresh | ✅ Automatic | ✅ Automatic | Complete |
| Multi-cloud | ✅ `--cloud` | ⏳ `--keycloak-url` | Partial |

**Parity**: 85% (7/8 major features)

## Integration Examples

### Shell Script

```bash
#!/bin/bash
set -e

# Login once (interactive)
itlc login

# Work with APIs
TOKEN=$(itlc get-token --output=token)

# Use token
curl -H "Authorization: Bearer $TOKEN" \
     https://api.example.com/data

# Logout when done
itlc logout
```

### Python Script

```python
import subprocess
import requests

# Login (opens browser)
subprocess.run(['itlc', 'login'], check=True)

# Get token
token = subprocess.check_output(
    ['itlc', 'get-token', '--output=token'],
    text=True
).strip()

# Use token
response = requests.get(
    'https://api.example.com/data',
    headers={'Authorization': f'Bearer {token}'}
)

print(response.json())
```

### PowerShell Script

```powershell
# Login once (interactive)
itlc login

# Get token
$TOKEN = itlc get-token --output=token

# Use token
Invoke-RestMethod -Uri "https://api.example.com/data" `
  -Headers @{Authorization = "Bearer $TOKEN"}

# Logout
itlc logout
```

## Next Steps

1. **Try interactive login**:
   ```bash
   itlc login
   ```

2. **Check your identity**:
   ```bash
   itlc whoami
   ```

3. **Get a token**:
   ```bash
   itlc get-token --output=token
   ```

4. **Use in your scripts**!

## Links

- [Main README](../README.md)
- [Token CLI Integration](TOKEN_CLI_INTEGRATION.md)
- [Quick Reference](../QUICKREF_TOKEN_CLI.md)

---

Made by [ITlusions](https://www.itlusions.com)
