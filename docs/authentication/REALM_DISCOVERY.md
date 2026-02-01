# Realm Discovery & Switching - Quick Reference

## Complete Workflow

### 1. Discover Available Realms

```bash
# Discover realms on default server (https://sts.itlusions.com)
itlc realm discover

# Output:
# [*] Discovering realms on https://sts.itlusions.com...
# 
# Discovered Realms on https://sts.itlusions.com:
# 
#   master
#   itlusions
#   itldev
# 
# ℹ Found 3 realm(s)
```

### 2. Set Target Realm

```bash
itlc realm set itldev
# ✓ Default realm set to: itldev
```

### 3. Authenticate

```bash
itlc login
# [*] Starting interactive login for realm: itldev
# [*] Opening browser for authentication...
# ... browser opens, user authenticates ...
# ✓ Authentication successful!
```

### 4. Verify

```bash
itlc whoami
# User Information:
# Username: user@company.com
# Realm: itldev

itlc realm show
# Current Realm:
# Realm: itldev
# Keycloak URL: https://sts.itlusions.com
```

## Commands Summary

| Command | Description | Requires Auth |
|---------|-------------|---------------|
| `itlc realm discover` | Find all realms on server | ❌ No |
| `itlc realm discover --server <url>` | Find realms on custom server | ❌ No |
| `itlc realm list` | List authenticated realms | ✅ Yes |
| `itlc realm set <name>` | Switch to realm | ❌ No (but login required after) |
| `itlc realm show` | Show current realm | ❌ No |
| `itlc login` | Authenticate to current realm | ❌ No (initiates auth) |
| `itlc whoami` | Show user in current realm | ✅ Yes |

## Examples

### Example 1: New User Workflow

```bash
# User has no context yet, wants to find available realms
itlc realm discover
# Shows: master, itlusions, itldev

# User picks 'itlusions'
itlc realm set itlusions
itlc login
# Authenticates via browser

# Check authentication
itlc whoami
# Shows user details for itlusions realm
```

### Example 2: Switch Between Realms

```bash
# Currently in 'production'
itlc realm show
# Realm: production

# Discover other realms
itlc realm discover
# Shows: master, production, staging, development

# Switch to staging
itlc realm set staging
itlc login
# Authenticates to staging

# Work in staging
itlc get-token
# Returns staging token

# Switch back to production
itlc realm set production
itlc login
# Re-authenticates to production
```

### Example 3: Custom Keycloak Server

```bash
# Discover realms on company STS
itlc realm discover --server https://sts.company.com
# [*] Discovering realms on https://sts.company.com...
# Shows discovered realms

# Set environment for custom server
export KEYCLOAK_URL=https://sts.company.com
export KEYCLOAK_REALM=production

# Login
itlc login
```

### Example 4: Check Before Switching

```bash
# Want to check if 'test' realm exists before switching
itlc realm discover | grep test
# If found: proceed with switch
# If not found: realm doesn't exist

# If found, switch
itlc realm set test
itlc login
```

## Tips & Best Practices

### 🔍 Always Discover First

Before switching realms, discover available realms to avoid typos:

```bash
# Good: Discover first
itlc realm discover
itlc realm set staging  # You saw 'staging' in the list

# Bad: Typo in realm name
itlc realm set stagign  # Typo! Will fail on login
```

### 🔐 Re-authenticate After Switching

**Important:** Switching realms changes the target, but you must login to get tokens:

```bash
itlc realm set development
# ✓ Default realm set to: development

itlc get-token
# ❌ Error: Not authenticated

itlc login  # REQUIRED
# ✓ Authentication successful!

itlc get-token
# ✓ Returns token
```

### 📋 List Shows Only Authenticated

`itlc realm list` only shows realms you're logged into (usually just one):

```bash
itlc realm discover  # Shows all realms on server
itlc realm list      # Shows only authenticated realms
```

### 🌐 Use Environment Variables for Automation

```bash
# Script to work across multiple realms
#!/bin/bash
for realm in production staging development; do
  export KEYCLOAK_REALM=$realm
  itlc login --non-interactive
  TOKEN=$(itlc get-token)
  echo "Token for $realm: $TOKEN"
  itlc logout
done
```

### 🚫 One Realm at a Time

ITLC maintains **one active context**. Switching realms replaces the context:

```bash
# Authenticated to 'production'
itlc whoami
# Realm: production

# Switch to 'staging' (login required)
itlc realm set staging
itlc login

# Now authenticated to 'staging', production context is lost
itlc whoami
# Realm: staging
```

## Troubleshooting

### "No realms discovered"

**Problem:**
```bash
itlc realm discover
# ℹ No realms discovered on https://sts.itlusions.com
```

**Causes:**
1. Server URL is incorrect
2. Server is not accessible (network/firewall)
3. Keycloak server has non-standard realm names

**Solution:**
```bash
# Check server accessibility
curl https://sts.itlusions.com/realms/master/.well-known/openid-configuration

# Try custom server
itlc realm discover --server https://your-keycloak.com

# If you know the realm name, set it directly
itlc realm set your-realm-name
itlc login
```

### "Authentication failed" after switching

**Problem:**
```bash
itlc realm set staging
itlc login
# [✗] Authentication failed: Unauthorized
```

**Causes:**
1. Your user doesn't exist in the target realm
2. Keycloak client 'itl-cli' doesn't exist in target realm
3. Wrong credentials for target realm

**Solution:**
```bash
# Verify realm exists
itlc realm discover | grep staging

# Check if you have account in staging (ask admin)
# Verify itl-cli client exists in staging realm
# Ensure you're using correct credentials
```

### Discovery shows realm but login fails

**Problem:**
```bash
itlc realm discover
# Shows: itldev

itlc realm set itldev
itlc login
# [✗] Client not found
```

**Cause:** Realm exists but doesn't have the 'itl-cli' client configured

**Solution:**
Create the client in that realm (see [CUSTOM_STS_SETUP.md](CUSTOM_STS_SETUP.md))

## Related Documentation

- [Realm Isolation](REALM_ISOLATION.md) - Security boundaries between realms
- [Custom STS Setup](guides/CUSTOM_STS_SETUP.md) - Configure ITLC for your Keycloak
- [Interactive Login](INTERACTIVE_LOGIN.md) - Authentication flow details
