# ITL Token Manager CLI (itlc)

Azure CLI-inspired token manager for Keycloak authentication.

## Quick Start

```bash
# Install
pip install itlauth

# Login interactively
itlc login

# Check current user
itlc whoami

# Get access token
itlc get-token
```

## Installation

```bash
cd d:\repos\ITLAuth
pip install -e .
```

Or install from PyPI (when published):
```bash
pip install itlc-manager
```

## Usage

### Set Environment Variables

```powershell
# Keycloak configuration
$env:KEYCLOAK_URL = "https://sts.itlusions.com"
$env:KEYCLOAK_REALM = "itlusions"

# Service account credentials
$env:KEYCLOAK_CLIENT_ID = "my-service-account"
$env:KEYCLOAK_CLIENT_SECRET = "my-secret"
```

### Commands

```bash
```bash
# Interactive authentication
itlc login
itlc whoami
itlc logout

# Realm management
itlc realm list
itlc realm set production
itlc realm show

# Token operations (service accounts)
itlc get-token
itlc get-token --client-id=my-app --client-secret=secret
itlc get-token --output=json

# Token inspection
itlc inspect <token>
itlc inspect <token> --decode

# Token validation
itlc introspect <token>

# Configuration
itlc config

# Cache management
itlc cache-list
itlc clear-cache --all
```

## Features

- ✅ **Interactive Login**: Browser-based OAuth 2.0 with PKCE
- ✅ **Multi-Realm Support**: Switch between Keycloak realms
- ✅ **Token Acquisition**: Get tokens via client credentials or user context
- ✅ **Token Caching**: Automatic caching in `~/.itl/token-cache/`
- ✅ **Auto Token Refresh**: Seamless background renewal
- ✅ **Environment Variables**: Azure-style credential discovery
- ✅ **JWT Inspection**: Decode and inspect JWT tokens
- ✅ **Token Introspection**: Validate tokens with Keycloak
- ✅ **Multiple Output Formats**: json, token, table

## Configuration

### For ITLusions STS (Default)

No configuration needed - works out of the box with `https://sts.itlusions.com`.

### For Your Own Keycloak/STS

See [Custom STS Setup Guide](../../docs/guides/CUSTOM_STS_SETUP.md) for complete instructions.

**Quick configuration:**

```bash
# Set environment variables
export KEYCLOAK_SERVER="https://sts.yourcompany.com"
export KEYCLOAK_REALM="production"
export KEYCLOAK_CLIENT_ID="itl-cli"

# Or use command-line flags
itlc login --server https://sts.yourcompany.com --realm production
```

## Environment Variable Priority

### For Interactive Login
1. Command-line parameters (`--server`, `--realm`, `--client-id`)
2. Configuration file (`~/.itl/config.yaml`)
3. Environment variables (`KEYCLOAK_SERVER`, `KEYCLOAK_REALM`, `KEYCLOAK_CLIENT_ID`)
4. Defaults (ITLusions STS)

### For Service Account Tokens
1. Command-line parameters (`--client-id`, `--client-secret`)
2. `KEYCLOAK_CLIENT_ID` + `KEYCLOAK_CLIENT_SECRET`
3. `ITL_CLIENT_ID` + `ITL_CLIENT_SECRET`
4. Mounted secrets at `/etc/secrets/keycloak/`

## Storage Locations

**Context file** (interactive login):
- Windows: `C:\Users\<username>\.itl\context.json`
- Linux/Mac: `~/.itl/context.json`

**Token cache** (service accounts):
- Windows: `C:\Users\<username>\.itl\token-cache\`
- Linux/Mac: `~/.itl/token-cache/`

## Comparison with Azure CLI

| Feature | Azure kubelogin | ITL Token CLI |
|---------|----------------|---------------|
| Get token | ✅ | ✅ |
| Token cache | ✅ | ✅ |
| Env variables | ✅ | ✅ |
| JWT inspection | ❌ | ✅ |
| Token introspection | ❌ | ✅ |
| Cache management | ❌ | ✅ |

## Integration with ITL Auth

This tool is part of the ITL Auth suite:
- `itl-kubectl-oidc-setup`: Configure kubectl OIDC authentication
- `itlc`: Manage Keycloak API tokens (this tool)

Use together for complete authentication workflows.
