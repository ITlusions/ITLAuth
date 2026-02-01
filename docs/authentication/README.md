# Authentication

ITL Token CLI authentication methods and realm management.

## 📚 Documentation

### Core Concepts

1. **[Interactive Login](INTERACTIVE_LOGIN.md)**
   - Azure CLI-style browser-based authentication
   - Token caching & auto-refresh
   - Multi-realm support

2. **[Token CLI Integration](TOKEN_CLI_INTEGRATION.md)**
   - Service account authentication (CI/CD)
   - Token inspection & validation
   - Integration examples

### Advanced Topics

3. **[Realm Discovery](REALM_DISCOVERY.md)**
   - Automatic realm detection
   - Multi-tenant setup
   - Realm switching

4. **[Realm Isolation](REALM_ISOLATION.md)**
   - Security boundaries
   - Cross-realm access
   - Best practices

## 🚀 Quick Start

### Interactive Login (Developers)
```bash
# Login with browser
itlc login

# Get token
TOKEN=$(itlc get-token --output=token)

# Use token
curl -H "Authorization: Bearer $TOKEN" https://api.example.com
```

### Service Account (CI/CD)
```bash
# Set credentials
export KEYCLOAK_CLIENT_ID=my-service
export KEYCLOAK_CLIENT_SECRET=secret

# Get token
TOKEN=$(itlc get-token --output=token)
```

### Multi-Realm
```bash
# List realms
itlc realm list

# Switch realm
itlc realm set production

# Get token for current realm
itlc get-token
```

## 🔑 Authentication Methods

| Method | Use Case | Example |
|--------|----------|---------|
| **Interactive** | Developer workstations | `itlc login` |
| **Service Account** | CI/CD pipelines | `KEYCLOAK_CLIENT_ID=...` |
| **Device Code** | Headless servers | `itlc login --device-code` |

## 📖 Related Documentation

- [Getting Started](../getting-started/INSTALLATION.md) - Initial setup
- [Kubernetes Integration](../kubernetes/) - K8s OIDC configuration
- [PIM](../pim/) - Privilege elevation workflows

## Command Reference

```bash
# Authentication
itlc login                    # Interactive browser login
itlc logout                   # Clear cached tokens
itlc whoami                   # Show current user

# Token Management
itlc get-token                # Get access token
itlc get-token --output=token # Token only (for scripts)
itlc inspect <token>          # Decode JWT
itlc introspect <token>       # Validate token

# Realm Management
itlc realm list               # List available realms
itlc realm set <name>         # Switch to realm
itlc realm show               # Show current realm

# Cache Management
itlc cache-list               # List cached tokens
itlc clear-cache --all        # Clear all cached tokens
```
