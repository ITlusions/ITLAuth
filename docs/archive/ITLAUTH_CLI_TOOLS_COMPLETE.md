# ITLAuth CLI Tools Reference

**Complete guide to the `itlc` token manager and authentication CLI**

---

## Overview

ITLAuth provides a comprehensive command-line interface (`itlc`) for managing Kubernetes authentication with Keycloak OIDC. It combines interactive login, service account management, and privileged access elevation in a single, unified CLI.

```bash
$ itlc --help

  _____ _______ _       ______ _      _____ 
 |_   _|__   __| |     / ____/| |    |_   _|
   | |    | |  | |    | |     | |      | |  
   | |    | |  | |    | |     | |      | |  
  _| |_   | |  | |____| |____ | |____ _| |_ 
 |_____|  |_|  |______|\_____/|______|_____|

    ITLusions Token Manager v1.0.0
    Keycloak Authentication CLI

Usage: itlc [OPTIONS] COMMAND [ARGS]...

Options:
  --version             Show version
  --debug               Enable debug logging
  --help                Show this message
```

---

## Installation

### From PyPI
```bash
pip install itl-kubectl-oidc-setup
itlc --version
```

### From Source
```bash
git clone https://github.com/ITlusions/ITLAuth.git
cd ITLAuth
pip install .
itlc --version
```

### Verify Installation
```bash
which itlc              # Should show: /usr/local/bin/itlc (or similar)
itlc --version          # Should show: ITLAuth v1.0.0+
```

---

## Core Commands

### Authentication (`auth`)

#### Interactive Browser Login
```bash
itlc auth login

# With specific realm
itlc auth login --realm production

# With specific cluster
itlc auth login --cluster prod-us-east

# Full options
itlc auth login \
  --realm production \
  --client-id kubectl \
  --port 18000
```

**What it does:**
1. Opens browser to Keycloak login
2. User authenticates
3. Token returned to CLI
4. kubeconfig updated automatically
5. kubectl ready to use

**Exit codes:**
- `0` - Success
- `1` - Login failed
- `2` - Network error

---

#### Logout
```bash
itlc auth logout

# Logout and revoke token
itlc auth logout --revoke

# Logout from specific realm
itlc auth logout --realm production
```

---

### Token Management (`token`)

#### Get Current Token
```bash
itlc get-token

# Get token as JSON
itlc get-token --json

# Get token with metadata
itlc get-token --verbose

# Save to file
itlc get-token > token.txt
```

**Output:**
```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IjEifQ...
```

---

#### Show Token Information
```bash
itlc token-info

# Show as JSON
itlc token-info --json

# Include claims
itlc token-info --verbose
```

**Output:**
```
Token Information
─────────────────
Subject:      user-123
Issued At:    2026-01-31T10:00:00Z
Expires:      2026-01-31T11:00:00Z
Remaining:    45 minutes
Realm:        production
Scopes:       openid profile email
```

---

#### Refresh Token
```bash
itlc token refresh

# Force refresh even if not expired
itlc token refresh --force

# Refresh for specific realm
itlc token refresh --realm production
```

**Output:**
```
✓ Token refreshed successfully
  New expiry: 2026-01-31T11:00:00Z
  Remaining: 1 hour
```

---

#### Revoke Token
```bash
itlc token revoke

# Revoke and logout
itlc token revoke --logout

# Revoke specific token
itlc token revoke --token eyJhbGciOi...
```

---

#### List Token Cache
```bash
itlc token cache list

# Show cached tokens with details
itlc token cache list --verbose

# Show cache location
itlc token cache location
```

**Output:**
```
Cached Tokens
─────────────
1. production   | expires in 45 min | ~user-123
2. staging      | expires in 2h 30m | ~user-456
3. dev          | expired           | (refresh needed)
```

---

#### Clear Token Cache
```bash
itlc token cache clear

# Clear specific realm
itlc token cache clear --realm staging

# Clear all without confirmation
itlc token cache clear --force
```

---

### Realm Management (`realm`)

#### List Available Realms
```bash
itlc realm list

# Show detailed realm info
itlc realm list --verbose

# List as JSON
itlc realm list --json
```

**Output:**
```
Available Realms
────────────────
* production    (active)  → https://keycloak.example.com/realms/production
  staging       (ready)   → https://keycloak.example.com/realms/staging
  dev           (ready)   → https://keycloak.example.com/realms/dev
  experimental  (ready)   → https://keycloak.example.com/realms/experimental

Current: production
```

---

#### Switch Realm
```bash
itlc realm switch staging

# Switch and login if needed
itlc realm switch production --login

# Show which realm will be active
itlc realm current
```

---

#### Show Realm Information
```bash
itlc realm info

# Info for specific realm
itlc realm info --realm staging

# Show as JSON
itlc realm info --json
```

**Output:**
```
Realm Information
─────────────────
Name:        production
URL:         https://keycloak.example.com/realms/production
Issuer:      https://keycloak.example.com/realms/production
Auth Endpoint: https://keycloak.example.com/realms/production/protocol/openid-connect/auth
Token Endpoint: https://keycloak.example.com/realms/production/protocol/openid-connect/token

Users:       1,234
Clients:     42
Roles:       18
Status:      ✓ Healthy
```

---

#### Add Realm
```bash
itlc realm add production \
  --keycloak-url https://keycloak.example.com

# Add with custom client
itlc realm add staging \
  --keycloak-url https://keycloak.example.com \
  --client-id custom-kubectl
```

---

#### Remove Realm
```bash
itlc realm remove dev

# Remove and clear cache
itlc realm remove staging --clear-cache

# No confirmation
itlc realm remove experimental --force
```

---

### Service Account Management (`service-account`)

#### Create Service Account
```bash
itlc service-account create --name my-bot

# With roles
itlc service-account create \
  --name ci-bot \
  --roles admin,developer \
  --description "GitHub Actions bot"

# With token expiry
itlc service-account create \
  --name github-actions \
  --expiry 90d

# With custom audience
itlc service-account create \
  --name api-client \
  --audience https://api.example.com
```

**Output:**
```
✓ Service account created: my-bot
  Client ID:     service-account-my-bot
  Created:       2026-01-31T10:00:00Z
  Status:        Active
  Roles:         admin, developer
  Token expires: 2026-04-30T10:00:00Z
```

---

#### List Service Accounts
```bash
itlc service-account list

# Show detailed info
itlc service-account list --verbose

# Filter by realm
itlc service-account list --realm production
```

**Output:**
```
Service Accounts (production)
───────────────────────────────
Name                  | Roles           | Created       | Status
──────────────────────┼─────────────────┼───────────────┼────────
github-actions-bot    | developer       | 2 days ago    | Active
my-app-service        | admin, viewer   | 1 week ago    | Active
ci-deployment         | developer       | 3 weeks ago   | Active
legacy-app            | admin           | 2 months ago  | Inactive
```

---

#### Get Service Account Token
```bash
itlc service-account token --name my-bot

# Save to environment variable
export SA_TOKEN=$(itlc service-account token --name my-bot)

# Get as JSON
itlc service-account token --name my-bot --json

# Include token metadata
itlc service-account token --name my-bot --verbose
```

**Output:**
```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImtleS0xIn0...
```

---

#### Update Service Account
```bash
itlc service-account update --name my-bot \
  --add-roles viewer

# Remove roles
itlc service-account update --name my-bot \
  --remove-roles developer

# Update description
itlc service-account update --name my-bot \
  --description "Updated description"

# Extend token expiry
itlc service-account update --name my-bot \
  --extend-expiry 30d
```

---

#### Rotate Service Account Credentials
```bash
itlc service-account rotate --name my-bot

# Rotate and replace current token
itlc service-account rotate --name my-bot --apply
```

---

#### Delete Service Account
```bash
itlc service-account delete --name my-bot

# No confirmation
itlc service-account delete --name legacy-app --force

# Revoke tokens first
itlc service-account delete --name my-bot --revoke-tokens
```

---

#### Service Account Status
```bash
itlc service-account status --name my-bot

# Show in verbose/JSON
itlc service-account status --name my-bot --json
```

**Output:**
```
Service Account: my-bot
────────────────────────
Client ID:         service-account-my-bot
Created:           2026-01-31T10:00:00Z
Last Token:        2026-01-31T10:30:00Z
Token Expiry:      2026-04-30T10:00:00Z
Status:            Active
Roles:             admin, developer
Enabled:           Yes
```

---

### Privileged Identity Management (PIM) (`pim`)

#### Request Elevated Access
```bash
itlc pim request admin

# With custom duration
itlc pim request admin --duration 1h

# With justification
itlc pim request admin --reason "Emergency maintenance" --duration 2h

# Request specific role
itlc pim request cluster-admin --duration 30m
```

**Output:**
```
✓ Elevation request approved
  Role:          admin
  Duration:      1 hour
  Requested:     2026-01-31T10:00:00Z
  Expires:       2026-01-31T11:00:00Z
  Elevation ID:  elev-abc123def456
  Status:        Active
```

---

#### List Active Elevations
```bash
itlc pim list

# Show detailed info
itlc pim list --verbose

# Show expired elevations
itlc pim list --include-expired
```

**Output:**
```
Active Privilege Elevations
──────────────────────────────
ID              | Role          | Expires In | Status
────────────────┼───────────────┼────────────┼────────
elev-abc123     | admin         | 45 min     | Active
elev-def456     | cluster-admin | 2 days     | Active
elev-ghi789     | viewer        | Expired    | Revoked
```

---

#### Revoke Elevation
```bash
itlc pim revoke elev-abc123def456

# Revoke all active elevations
itlc pim revoke --all

# No confirmation
itlc pim revoke elev-abc123 --force
```

---

#### Check Elevation Status
```bash
itlc pim status elev-abc123def456

# Show as JSON
itlc pim status elev-abc123 --json
```

---

### Kubernetes Setup (`setup`)

#### Configure Kubernetes for OIDC
```bash
itlc setup kubernetes \
  --cluster-name prod-us-east \
  --api-server-host kubernetes.example.com

# Full options
itlc setup kubernetes \
  --cluster-name prod \
  --api-server-host k8s-api.example.com \
  --api-server-port 6443 \
  --api-server-ca /path/to/ca.crt
```

---

#### Generate kubeconfig
```bash
itlc setup kubeconfig \
  --cluster-name production \
  --api-server-host kubernetes.example.com \
  --output kubeconfig.yaml

# Merge with existing kubeconfig
itlc setup kubeconfig \
  --cluster-name staging \
  --api-server-host k8s-staging.example.com \
  --merge
```

---

#### Configure API Server
```bash
itlc setup apiserver \
  --api-server-url https://kubernetes.example.com:6443 \
  --output apiserver-config.yaml
```

---

### Configuration Management (`config`)

#### Set Configuration
```bash
itlc config set keycloak-url https://keycloak.example.com
itlc config set realm production
itlc config set token-cache-dir ~/.itlc/cache
itlc config set token-refresh-threshold 5m
itlc config set debug true
```

---

#### Get Configuration
```bash
itlc config get keycloak-url

# Show all configuration
itlc config show

# Show as JSON
itlc config show --json
```

---

#### Show Configuration File Location
```bash
itlc config location
```

**Output:**
```
Configuration File: ~/.config/itlc/config.yaml
Token Cache:       ~/.cache/itlc/tokens
Logs:              ~/.local/share/itlc/logs
```

---

#### Reset Configuration
```bash
itlc config reset

# Reset to defaults with confirmation
itlc config reset --confirm

# Force reset without confirmation
itlc config reset --force
```

---

### General Commands

#### Version
```bash
itlc --version
itlc version
```

**Output:**
```
ITLAuth v1.0.0
Python 3.10.5
Keycloak client v0.30.0
```

---

#### Status
```bash
itlc status

# Verbose status
itlc status --verbose
```

**Output:**
```
ITLAuth Status
──────────────
Version:         1.0.0
Config:          ~/.config/itlc/config.yaml
Current Realm:   production
Keycloak:        ✓ Reachable (https://keycloak.example.com)
Kubernetes:      ✓ Configured (prod-us-east)
Token Cache:     3 tokens cached (1 expired)
Last Login:      2 hours ago
```

---

#### Help
```bash
itlc --help
itlc <command> --help

# Detailed help
itlc --help --verbose
```

---

## Environment Variables

```bash
# Keycloak configuration
export ITLAUTH_KEYCLOAK_URL=https://keycloak.example.com
export ITLAUTH_REALM=production
export ITLAUTH_CLIENT_ID=kubectl

# Token cache
export ITLAUTH_TOKEN_CACHE_DIR=~/.itlc/cache
export ITLAUTH_TOKEN_REFRESH_THRESHOLD=5m

# Logging
export ITLAUTH_DEBUG=true
export ITLAUTH_LOG_LEVEL=debug

# Kubernetes
export ITLAUTH_KUBECONFIG=~/.kube/config
export ITLAUTH_CLUSTER_NAME=prod-us-east
```

---

## Common Workflows

### Workflow 1: Local Development
```bash
# Initial setup
itlc auth login
itlc realm switch production

# Use kubectl normally
kubectl get pods
kubectl logs my-pod
kubectl port-forward svc/my-app 8080:80

# When token expires, just run again
itlc token refresh
```

### Workflow 2: CI/CD Pipeline
```bash
# In your CI/CD environment
SA_TOKEN=$(itlc service-account token --name github-actions)
export KUBECONFIG=kubeconfig.yaml

# Use in deployment
kubectl apply -f manifests/
kubectl rollout status deployment/my-app
```

### Workflow 3: Temporary Admin Access
```bash
# Request elevation
itlc pim request admin --duration 1h --reason "Cluster maintenance"

# Perform admin tasks
kubectl drain node-1
kubectl patch nodes node-1 --type merge -p '{"spec":{"unschedulable":false}}'

# Token automatically revokes after 1 hour
```

### Workflow 4: Multi-Cluster Management
```bash
# Switch between clusters
itlc realm list
itlc realm switch production
kubectl get nodes

itlc realm switch staging
kubectl get nodes

itlc realm switch dev
kubectl get pods
```

---

## Exit Codes

| Code | Meaning | Example |
|------|---------|---------|
| 0 | Success | Command completed successfully |
| 1 | General error | Invalid arguments, command failed |
| 2 | Network error | Cannot reach Keycloak or API server |
| 3 | Authentication failed | Login failed, invalid credentials |
| 4 | Token expired | Token expired and refresh failed |
| 5 | Permission denied | Insufficient permissions for operation |
| 127 | Command not found | Command does not exist |

---

## Tips & Tricks

### Alias frequently used commands
```bash
alias itl-prod='itlc realm switch production'
alias itl-stag='itlc realm switch staging'
alias itl-token='itlc get-token'
alias itl-info='itlc token-info'
```

### Export token for external use
```bash
# Save token to environment variable
export OIDC_TOKEN=$(itlc get-token)

# Use in curl
curl -H "Authorization: Bearer $OIDC_TOKEN" https://api.example.com/users
```

### Automate in scripts
```bash
#!/bin/bash
token=$(itlc get-token --json | jq -r '.access_token')
kubeconfig=$(itlc setup kubeconfig --cluster-name prod)
kubectl --kubeconfig=$kubeconfig get pods
```

### Debug token issues
```bash
# Enable debug logging
itlc --debug token-info

# Check cache
itlc token cache list --verbose

# Clear cache if needed
itlc token cache clear --force
itlc auth login
```

---

## Troubleshooting

### "Command not found: itlc"
**Fix:** Reinstall package: `pip install --upgrade itl-kubectl-oidc-setup`

### "Network error: Cannot reach Keycloak"
**Fix:** Check Keycloak URL: `itlc config get keycloak-url`

### "Token expired"
**Fix:** Refresh token: `itlc token refresh`

### "Permission denied"
**Fix:** Check roles: `itlc token-info --verbose`

See [docs/kubernetes/TROUBLESHOOTING.md](docs/kubernetes/TROUBLESHOOTING.md) for more.

---

## See Also

- [QUICKSTART.md](QUICKSTART.md) - Quick getting started
- [QUICKREF_TOKEN_CLI.md](QUICKREF_TOKEN_CLI.md) - Command reference  
- [docs/authentication/TOKEN_CLI_INTEGRATION.md](docs/authentication/TOKEN_CLI_INTEGRATION.md) - Deep dive
- [docs/kubernetes/SERVICE-ACCOUNTS.md](docs/kubernetes/SERVICE-ACCOUNTS.md) - Service accounts
- [docs/pim/PRIVILEGE_ELEVATION_COMPLETE.md](docs/pim/PRIVILEGE_ELEVATION_COMPLETE.md) - PIM guide
