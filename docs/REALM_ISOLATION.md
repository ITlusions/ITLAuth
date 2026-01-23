# ITLC Realm Isolation & Security

## Overview

ITLC CLI implements **realm isolation** - users can only see and interact with realms they've successfully authenticated to. This ensures proper security boundaries between different Keycloak realms.

## How Realm Isolation Works

### Basic Principle

```
User A logs into Realm X → Can only see Realm X
User B logs into Realm Y → Can only see Realm Y
User A cannot see or access Realm Y (and vice versa)
```

### Authentication Flow

```
┌──────────────┐
│   User       │
└──────┬───────┘
       │
       │ 1. itlc login --realm production
       ▼
┌──────────────────────┐
│  Keycloak Realm:     │
│  "production"        │
└──────┬───────────────┘
       │
       │ 2. Authentication succeeds
       │ 3. Context saved to ~/.itl/context.json
       ▼
┌──────────────────────┐
│  User can now:       │
│  - See "production"  │
│  - Get tokens        │
│  - Use whoami        │
│                      │
│  User CANNOT:        │
│  - See "staging"     │
│  - See "development" │
│  - Access other      │
│    realms            │
└──────────────────────┘
```

## Commands Respecting Realm Isolation

### `itlc realm discover`

**NEW**: Discover all available realms on the Keycloak server without authentication:

```bash
$ itlc realm discover

[*] Discovering realms on https://sts.itlusions.com...

Discovered Realms on https://sts.itlusions.com:

  master
* itlusions (authenticated)
  itldev

ℹ Found 3 realm(s)
```

**Use cases:**
- Find available realms before first login
- Verify realm names before authenticating
- Check if a specific realm exists on the server

**Security note:** This queries public Keycloak endpoints. It shows realms that exist on the server, but users still need valid credentials to authenticate to each realm.

### `itlc realm list`

Shows **only** realms you're authenticated to:

```bash
# User authenticated to 'production'
$ itlc realm list

Authenticated Realms:

* production

ℹ You can only see realms you've authenticated to (realm isolation)
```

```bash
# User not authenticated
$ itlc realm list

ℹ Not authenticated to any realm. Run 'itlc login' first.
```

### `itlc whoami`

Shows information for the **current authenticated realm only**:

```bash
$ itlc whoami

User Information:

Username: user@company.com
Email: user@company.com
Name: John Doe
Realm: production        # ← Current realm
Keycloak URL: https://sts.yourcompany.com
```

### `itlc get-token`

Returns tokens **only for the authenticated realm**:

```bash
# Authenticated to 'production'
$ itlc get-token
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...  # Production token

# Cannot get tokens for 'staging' without authenticating
```

## Multi-Realm Workflow

If you need to work with multiple realms, authenticate to each separately:

### Discovering Available Realms

**NEW: Use `itlc realm discover` to find available realms:**

```bash
# Discover all realms on the server
itlc realm discover

# Discover realms on a custom server
itlc realm discover --server https://sts.yourcompany.com
```

### Switching Between Realms

```bash
# Login to production
itlc realm set production
itlc login
# Now working in production

# Switch to staging
itlc realm set staging
itlc login
# Now working in staging

# List current realm
itlc realm show
```

### Current Limitation

**One realm at a time**: ITLC currently stores context for **one realm** at a time. Switching realms requires:
1. Logout from current realm (optional but recommended)
2. Set new realm
3. Login to new realm

```bash
# Clean switch
itlc logout              # Clear production context
itlc realm set staging
itlc login               # Authenticate to staging
```

## Security Implications

### ✅ What Realm Isolation Prevents

1. **Cross-realm token leakage**: Tokens from Realm A cannot be used in Realm B
2. **Unauthorized realm discovery**: Users cannot enumerate realms they don't have access to
3. **Cross-realm user enumeration**: Users in Realm A cannot see users in Realm B
4. **Privilege escalation**: Cannot escalate privileges by switching realms without authentication

### ✅ Authentication Required Per Realm

Each realm requires separate authentication:

```bash
# User has credentials for both 'production' and 'staging'

# Must authenticate to each separately:
itlc realm set production
itlc login  # Authenticate with production credentials

itlc realm set staging
itlc login  # Must authenticate again with staging credentials
```

### ✅ Token Scope Limitations

Tokens are scoped to their realm:

```bash
# Production token
TOKEN_PROD=$(itlc get-token --realm production)

# This token CANNOT be used for staging APIs
curl -H "Authorization: Bearer $TOKEN_PROD" \
  https://api-staging.company.com/resource
# ❌ 401 Unauthorized
```

## Implementation Details

### Context Storage

User context is stored in `~/.itl/context.json`:

```json
{
  "realm": "production",
  "keycloak_url": "https://sts.yourcompany.com",
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "Bearer",
  "expires_in": 300,
  "refresh_expires_in": 1800,
  "scope": "openid email profile"
}
```

**Security Note**: This file contains sensitive tokens and is:
- Readable only by the file owner (Unix: 0600)
- Located in user's home directory
- Never transmitted over network
- Cleared on `itlc logout`

### Realm List Query

When you run `itlc realm list`, ITLC:

1. ✅ Reads `~/.itl/context.json`
2. ✅ Returns `realm` from context (only the authenticated realm)
3. ❌ Does NOT query Keycloak admin API
4. ❌ Does NOT attempt to discover other realms
5. ❌ Does NOT return realms from environment variables

This ensures users only see realms they've explicitly authenticated to.

## Advanced: Multi-Realm Management

### Option 1: Multiple Context Files (Manual)

Store contexts for different realms:

```bash
# Production context
itlc login --realm production
cp ~/.itl/context.json ~/.itl/context-production.json

# Staging context  
itlc login --realm staging
cp ~/.itl/context.json ~/.itl/context-staging.json

# Switch between realms
cp ~/.itl/context-production.json ~/.itl/context.json  # Use production
cp ~/.itl/context-staging.json ~/.itl/context.json     # Use staging
```

### Option 2: Environment-Based Separation

Use environment variables for different shells/terminals:

**Terminal 1 (Production):**
```bash
export KEYCLOAK_REALM=production
itlc login
# All commands in this terminal use production
```

**Terminal 2 (Staging):**
```bash
export KEYCLOAK_REALM=staging
itlc login
# All commands in this terminal use staging
```

### Option 3: Profile-Based (Future Enhancement)

Future versions may support named profiles:

```bash
# Not yet implemented - future concept
itlc login --profile production
itlc login --profile staging

itlc realm list --all-profiles
# Output:
# production (active)
# staging

itlc --profile staging get-token
```

## Troubleshooting Realm Access

### Issue: "Not authenticated to any realm"

```bash
$ itlc realm list
ℹ Not authenticated to any realm. Run 'itlc login' first.
```

**Solution:**
```bash
itlc login
```

### Issue: "Cannot access realm X"

```bash
$ itlc realm set development
$ itlc login
[✗] Authentication failed: Unauthorized
```

**Possible causes:**
1. User doesn't have account in 'development' realm
2. Keycloak client 'itl-cli' doesn't exist in 'development' realm
3. User's credentials are not valid for 'development' realm

**Solution:**
- Verify you have an account in the target realm
- Confirm the `itl-cli` client exists in that realm
- Use correct credentials for that realm

### Issue: "Seeing wrong realm after switching"

```bash
$ itlc realm set staging
$ itlc whoami
Realm: production  # ← Still shows production!
```

**Cause**: Old context still cached

**Solution:**
```bash
itlc logout          # Clear old context
itlc realm set staging
itlc login           # Fresh authentication
itlc whoami          # Now shows staging
```

## Security Best Practices

### 1. Logout After Sensitive Operations

```bash
itlc login
# ... do work in production ...
itlc logout  # Clear tokens and context
```

### 2. Use Separate Clients Per Realm

Create dedicated Keycloak clients:
- `itl-cli-production` in production realm
- `itl-cli-staging` in staging realm
- `itl-cli-development` in development realm

### 3. Avoid Storing Contexts in Version Control

```bash
# .gitignore
.itl/
context.json
token-cache/
```

### 4. Use Short-Lived Tokens

Configure in Keycloak:
- **Access Token Lifespan**: 5-15 minutes
- **Refresh Token Lifespan**: 30 minutes
- **SSO Session Idle**: 30 minutes

### 5. Monitor Authentication Events

Enable Keycloak audit logs:
- Track `itlc login` events
- Alert on failed authentication attempts
- Monitor realm switching patterns

## FAQ

**Q: Can I be authenticated to multiple realms simultaneously?**  
A: Currently no. ITLC stores one context at a time. You must logout and login to switch realms.

**Q: Why can't I see all realms in my Keycloak server?**  
A: Security by design. Users should only see realms they're actively using. This prevents information disclosure.

**Q: How do I grant access to a user for multiple realms?**  
A: Create user accounts in each realm separately. Keycloak realms are isolated by design.

**Q: Can admin users see all realms?**  
A: No. Even Keycloak admins must authenticate to each realm separately when using ITLC. Admin access via web console is separate from CLI access.

**Q: What if I need to automate multi-realm operations?**  
A: Use service accounts with scripting:
```bash
#!/bin/bash
for realm in production staging development; do
  export KEYCLOAK_REALM=$realm
  itlc login --non-interactive
  itlc get-token | save-to-vault $realm
  itlc logout
done
```

**Q: Is the realm list cached?**  
A: No. `itlc realm list` reads directly from `~/.itl/context.json` each time.

## Related Documentation

- [Interactive Login Guide](INTERACTIVE_LOGIN.md)
- [Custom STS Setup](CUSTOM_STS_SETUP.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Security Best Practices](../SECURITY.md)

## Version History

- **v1.0.0**: Initial realm isolation implementation
  - Single realm context support
  - Explicit authentication required per realm
  - No cross-realm visibility
