# ITLAuth: OIDC & Keycloak Integration Guide

**Complete guide to OIDC authentication and Keycloak integration in ITLAuth**

---

## What is OIDC?

**OpenID Connect (OIDC)** is an authentication layer on top of OAuth 2.0. It enables secure, standardized authentication for applications and APIs.

**In plain English:** Instead of sharing passwords, OIDC lets you authenticate to Kubernetes using a central identity provider (Keycloak) via a secure browser-based flow.

---

## Why OIDC for Kubernetes?

### The Problem: Password-Based Authentication
```
Traditional kubectl auth:
├── Users know API token
├── API tokens stored in kubeconfig file
├── Long-lived (never expires)
├── Difficult to rotate
└── Hard to audit who did what

Risks:
❌ Compromised tokens grant permanent access
❌ No audit trail of user identity
❌ Token rotation requires manual steps
❌ No multi-factor authentication
```

### The Solution: OIDC with Keycloak
```
OIDC-based auth:
├── Users authenticate via browser (Keycloak)
├── Short-lived tokens (1 hour default)
├── Tokens automatically refresh
├── Full audit trail of who accessed what
├── Support for MFA, SSO, attribute-based access

Benefits:
✅ Centralized identity management
✅ Token auto-refresh (no repeated logins)
✅ Audit trail of all access
✅ MFA support
✅ SSO with other services
✅ Group-based access control (RBAC)
✅ Temporary elevation (PIM)
```

---

## OIDC Flow in ITLAuth

### Step 1: User Initiates Login
```bash
$ itlc auth login
Opening browser to Keycloak login page...
Waiting for authentication response on http://localhost:18000
```

### Step 2: Keycloak Authentication
User is redirected to Keycloak login page:
```
Keycloak Login
──────────────
Username: john.doe
Password: ••••••••
[Login]
```

### Step 3: PKCE OAuth2 Exchange
```
Client (itlc)          Keycloak
    │
    │─(1) Auth request + code challenge──→
    │                                      (User logs in)
    │←─(2) Authorization code + code────────
    │
    │─(3) Exchange code for token──→
    │                                (Verify code challenge)
    │←─(4) Access Token + ID Token────
```

**PKCE (Proof Key for Code Exchange):** Enhanced security for desktop apps.

### Step 4: Token Cached Locally
```
Access Token: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
ID Token:     eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Refresh Token: eyJhbGciOiJIUzI1NiJ9...

Cached in: ~/.cache/itlc/tokens/production.json
Encrypted: Yes ✓
Expiry:    2026-01-31T11:00:00Z (1 hour from now)
```

### Step 5: kubeconfig Updated
```yaml
# ~/.kube/config
apiVersion: v1
clusters:
- cluster:
    server: https://kubernetes.example.com:6443
    certificate-authority-data: LS0tLS...
  name: production

users:
- name: production
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: itlc
      args: ["get-token", "--realm", "production"]
      interactiveMode: Never

contexts:
- context:
    cluster: production
    user: production
  name: production
```

### Step 6: kubectl Uses Token
```bash
$ kubectl get pods
  (itlc get-token is called automatically)
  (Token from cache is used)
  (If expired, automatically refreshed)
  (Then kubectl command executes with token)
  
NAME                              READY   STATUS
my-app-deployment-abc123def       1/1     Running
...
```

---

## Keycloak Configuration

### What Keycloak Does

**Keycloak** is an open-source identity provider that manages:
- User authentication (login)
- Group/role management
- Token issuance
- Token validation
- MFA/2FA
- SSO (single sign-on)
- User federation

### Keycloak Setup Flow

```
1. Create Realm (per environment)
   ├── Production Realm
   ├── Staging Realm
   └── Dev Realm

2. Create Clients (per app/service)
   ├── kubectl client
   ├── CI/CD bot
   └── API client

3. Create Users & Groups
   ├── Developers
   ├── DevOps
   ├── Admins
   └── CI/CD Bots

4. Assign Roles to Groups
   ├── Developer role → Developers group
   ├── Admin role → Admins group
   └── Viewer role → Everyone

5. Configure OIDC
   ├── Client credentials
   ├── Redirect URIs
   ├── Token lifetime
   └── Access type
```

---

## OIDC Configuration in ITLAuth

### Basic Configuration

```bash
# Set Keycloak URL
itlc config set keycloak-url https://keycloak.example.com

# Add realm
itlc realm add production \
  --keycloak-url https://keycloak.example.com \
  --realm-name production

# Login
itlc auth login --realm production
```

### Advanced Configuration

```yaml
# ~/.config/itlc/config.yaml
keycloak:
  url: https://keycloak.example.com
  realms:
    production:
      name: production
      client_id: kubectl-prod
      client_secret: secret123  # If service account
      scopes:
        - openid
        - profile
        - email
      token_lifetime: 3600      # 1 hour
      refresh_threshold: 300    # 5 minutes

    staging:
      name: staging
      client_id: kubectl-stag
      ...

auth:
  flow: pkce                    # PKCE OAuth2 flow
  callback_port: 18000
  callback_timeout: 60s
  browser_command: "open"       # macOS: 'open', Linux: 'xdg-open', Windows: 'start'

cache:
  location: ~/.cache/itlc/tokens
  encryption: true
  ttl: 2592000                  # 30 days

logging:
  level: info
  file: ~/.local/share/itlc/logs/itlc.log
```

---

## Token Lifecycle

### Token Types

**Access Token**
- Used by kubectl to authenticate to Kubernetes API
- Short-lived (1 hour default)
- Contains user info and scopes
- Cannot be used after expiry

**Refresh Token**
- Used to get a new access token
- Longer-lived (7 days default)
- Never sent to Kubernetes API
- Used internally by itlc only

**ID Token**
- Contains user identity information
- Not used by Kubernetes API
- Used for client verification

### Token Flow

```
User logs in
    ↓
Access Token (1 hour) + Refresh Token (7 days) issued
    ↓
Tokens cached locally (encrypted)
    ↓
kubectl calls itlc get-token
    ↓
    Is token expired? ──NO──→ Return cached token
    │
    YES
    ↓
    Is refresh token valid? ──NO──→ Need re-login
    │
    YES
    ↓
    Use refresh token to get new access token
    │
    ↓
    Cache new token
    │
    ↓
    Return token to kubectl
    │
    ↓
kubectl authenticates with token
```

### Auto-Refresh

```bash
# Token auto-refreshes 5 minutes before expiry
# No user action needed

$ kubectl get pods
✓ Token refreshed automatically (4 mins before expiry)
NAME    READY   STATUS
my-pod  1/1     Running
```

---

## Token Validation

### How Kubernetes Validates Tokens

```
1. kubectl sends token to API server in Authorization header
   Authorization: Bearer eyJhbGciOiJSUzI1NiI...

2. API server receives request
   ├─ Extract token from header
   ├─ Check signature (using Keycloak public key)
   ├─ Verify issuer matches Keycloak
   ├─ Check token not expired
   ├─ Extract user identity from claims
   └─ Allow/deny based on RBAC

3. RBAC maps Keycloak groups → Kubernetes roles
   Example:
   User in group "developers" →
   Bound to Kubernetes role "developer" →
   Can: read pods, view logs
   Cannot: delete pods, modify RBAC

4. Request allowed/denied
```

### Token Claims

```json
{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "key-1"
}
{
  "iss": "https://keycloak.example.com/realms/production",
  "sub": "user-123",
  "aud": "kubernetes",
  "exp": 1643643600,
  "iat": 1643640000,
  "auth_time": 1643640000,
  "email": "john.doe@example.com",
  "email_verified": true,
  "name": "John Doe",
  "preferred_username": "john.doe",
  "groups": ["developers", "kubernetes-users"],
  "realm_access": {
    "roles": ["user", "developer", "admin"]
  },
  "resource_access": {
    "kubernetes": {
      "roles": ["read-pods", "write-deployments"]
    }
  }
}
```

---

## OIDC Security Features

### 1. PKCE (Proof Key for Code Exchange)
```
Traditional OAuth2:
Client ──code──> Keycloak ──token──> Client
(Vulnerable to interception)

PKCE Enhanced:
Client generates: code_challenge = SHA256(code_verifier)
Client ──code + code_challenge──> Keycloak
Client ──code + code_verifier──> Keycloak (validates: SHA256(verifier) == challenge)
Keycloak ──token──> Client
(Prevents token interception)
```

### 2. Token Encryption (at rest)
```bash
# Tokens stored encrypted in cache
~/.cache/itlc/tokens/production.json

Before:  eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
After:   AES256(eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...)
```

### 3. Token Expiry
```
Short-lived tokens (default 1 hour)
├─ Leaked token has limited lifetime
├─ No manual rotation needed
├─ Automatic refresh before expiry
└─ User sees seamless authentication
```

### 4. Scope Limitation
```
Token scope determines what it can do:
Token with scope: openid profile email
├─ Can be used for Kubernetes auth
├─ Cannot: Access other services (unless explicitly granted)
├─ Cannot: Perform actions beyond Kubernetes API
└─ Principle of least privilege
```

### 5. HTTPS Only
```bash
# All communication with Keycloak must use HTTPS
itlc config set keycloak-url https://keycloak.example.com  # ✓ Secure
itlc config set keycloak-url http://keycloak.example.com   # ✗ Blocked
```

### 6. Audience Validation
```
Token includes "aud" (audience) claim:
"aud": "kubernetes"

Kubernetes API server validates:
├─ Is this token meant for me?
├─ Token.aud == "kubernetes" → Yes, accept
└─ Token.aud == "other-service" → No, reject
```

---

## Keycloak Realm Isolation

### Multi-Tenant Setup

```
Single Keycloak Instance
│
├─ Realm: production
│  ├─ Users: [prod-users]
│  ├─ Groups: [prod-admins, prod-devs]
│  ├─ Roles: [admin, developer, viewer]
│  └─ Kubernetes Cluster: prod-us-east
│
├─ Realm: staging
│  ├─ Users: [all-developers]
│  ├─ Groups: [staging-admins, staging-devs]
│  ├─ Roles: [admin, developer, viewer]
│  └─ Kubernetes Cluster: staging-us-east
│
└─ Realm: dev
   ├─ Users: [all-developers]
   ├─ Groups: [dev-admins, dev-devs]
   ├─ Roles: [admin, developer, viewer]
   └─ Kubernetes Cluster: dev-local
```

### Access Control per Realm

```
User: john.doe
├─ production realm
│  ├─ In groups: developers
│  ├─ Kubernetes roles: developer
│  └─ Can: read pods, view logs
│
├─ staging realm
│  ├─ In groups: staging-admins, developers
│  ├─ Kubernetes roles: admin, developer
│  └─ Can: everything in staging (full admin)
│
└─ dev realm
   ├─ In groups: developers
   ├─ Kubernetes roles: developer
   └─ Can: read/write pods (full dev access)
```

---

## OIDC with Kubernetes API Server

### API Server Configuration

```bash
# Configure API server to trust Keycloak OIDC tokens
kube-apiserver \
  --oidc-issuer-url=https://keycloak.example.com/realms/production \
  --oidc-client-id=kubernetes \
  --oidc-username-claim=preferred_username \
  --oidc-groups-claim=groups \
  --oidc-ca-file=/etc/kubernetes/pki/ca.crt
```

### What Each Flag Does

| Flag | Purpose |
|------|---------|
| `--oidc-issuer-url` | URL of Keycloak realm (Kubernetes trusts tokens from this issuer) |
| `--oidc-client-id` | Kubernetes client ID in Keycloak |
| `--oidc-username-claim` | JWT claim that contains username |
| `--oidc-groups-claim` | JWT claim that contains group memberships |
| `--oidc-ca-file` | CA cert to verify Keycloak SSL |

### Example: Complete Setup

```bash
# 1. Create Keycloak client
itlc setup keycloak-client \
  --realm production \
  --client-name kubernetes

# 2. Get client ID and secret
CLIENT_ID=$(itlc keycloak client list --realm production | grep kubernetes | awk '{print $2}')

# 3. Configure API server
cat > /etc/kubernetes/manifests/kube-apiserver.yaml << EOF
apiVersion: v1
kind: Pod
metadata:
  name: kube-apiserver
spec:
  containers:
  - name: kube-apiserver
    image: k8s.gcr.io/kube-apiserver:v1.25.0
    command:
    - kube-apiserver
    - --advertise-address=10.0.0.1
    - --etcd-servers=https://127.0.0.1:2379
    - --oidc-issuer-url=https://keycloak.example.com/realms/production
    - --oidc-client-id=$CLIENT_ID
    - --oidc-username-claim=preferred_username
    - --oidc-groups-claim=groups
    - --oidc-ca-file=/etc/kubernetes/pki/ca.crt
    volumeMounts:
    - name: ca-certs
      mountPath: /etc/kubernetes/pki
  volumes:
  - name: ca-certs
    hostPath:
      path: /etc/kubernetes/pki
EOF
```

---

## Service Account OIDC

### Service Account Token Generation

```bash
# Create service account in Keycloak
itlc service-account create \
  --name github-actions \
  --realm production

# Get token (no browser login needed)
TOKEN=$(itlc service-account token --name github-actions)

# Use in CI/CD
export KUBECONFIG=kubeconfig.yaml
kubectl apply -f manifests/
```

### How Service Accounts Work

```
Service Account Auth:
1. Service account has client_id and client_secret
2. Service account calls Keycloak token endpoint directly
3. Keycloak issues token without browser interaction
4. Service account uses token to authenticate to Kubernetes
5. Perfect for automation, CI/CD, bots
```

### Example: GitHub Actions

```yaml
name: Deploy
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup ITLAuth
      run: pip install itl-kubectl-oidc-setup
    
    - name: Get service account token
      env:
        SA_NAME: github-actions
        KEYCLOAK_URL: https://keycloak.example.com
        REALM: production
      run: |
        TOKEN=$(itlc service-account token --name $SA_NAME)
        echo "KUBECONFIG_TOKEN=$TOKEN" >> $GITHUB_ENV
    
    - name: Deploy to Kubernetes
      env:
        KUBECONFIG: ${{ secrets.KUBECONFIG }}
      run: |
        kubectl apply -f manifests/
        kubectl rollout status deployment/my-app
```

---

## MFA (Multi-Factor Authentication)

### Enable MFA in Keycloak

```
Keycloak Console
  → Realm Settings
    → Realm: production
      → Authentication
        → Flows
          → Browser
            → Add Execution
              → Add Authenticator: TOTP (Time-based OTP)
              → Set to REQUIRED
        → Save
```

### User MFA Setup

```bash
$ itlc auth login --realm production
Opening browser to Keycloak...

# User sees login → MFA challenge
Keycloak MFA
─────────────
Username: john.doe
Password: ••••••••
[Next]

# User enters phone or authenticator app
Enter MFA code: 123456
[Verify]

# Authentication successful
✓ Authenticated and token cached
```

---

## Custom OIDC Provider (Not Keycloak)

ITLAuth can work with any OIDC provider:

```bash
# Use Auth0
itlc realm add auth0-prod \
  --issuer-url https://your-tenant.auth0.com \
  --client-id YOUR_CLIENT_ID

# Use Okta
itlc realm add okta-prod \
  --issuer-url https://your-okta-domain.okta.com \
  --client-id YOUR_CLIENT_ID

# Use Azure AD
itlc realm add azure-prod \
  --issuer-url https://login.microsoftonline.com/YOUR_TENANT_ID/v2.0 \
  --client-id YOUR_CLIENT_ID
```

---

## Troubleshooting OIDC

### Issue: "OIDC provider unreachable"

```bash
# Check Keycloak URL
itlc config get keycloak-url

# Test connectivity
curl https://keycloak.example.com/.well-known/openid-configuration

# Fix: Update URL if needed
itlc config set keycloak-url https://keycloak.example.com
```

### Issue: "Invalid token"

```bash
# Check token details
itlc token-info

# Refresh token
itlc token refresh

# Clear cache and re-login
itlc token cache clear --force
itlc auth login
```

### Issue: "Groups not in token"

```bash
# Check Keycloak client configuration
# Ensure "groups" claim is included in token
# Verify mapper exists: Audience Protocol Mapper

# In ITLAuth, verify realm config
itlc realm info --realm production --verbose
```

---

## Summary

ITLAuth provides:

✅ **OIDC Authentication** - Secure OAuth2 PKCE flow  
✅ **Keycloak Integration** - Full realm management  
✅ **Token Management** - Auto-refresh, caching, expiry  
✅ **Service Accounts** - CI/CD automation  
✅ **Multi-Tenant** - Realm isolation  
✅ **MFA Support** - Enhanced security  
✅ **PIM** - Just-in-time privilege elevation  
✅ **RBAC Integration** - Kubernetes group-based access control  

See Also:
- [README-ENHANCED.md](README-ENHANCED.md) - Full project overview
- [ITLAUTH_CLI_TOOLS_COMPLETE.md](ITLAUTH_CLI_TOOLS_COMPLETE.md) - CLI reference
- [docs/kubernetes/APISERVER-OIDC-SETUP.md](docs/kubernetes/APISERVER-OIDC-SETUP.md) - Kubernetes setup
- [docs/pim/PRIVILEGE_ELEVATION_COMPLETE.md](docs/pim/PRIVILEGE_ELEVATION_COMPLETE.md) - PIM guide
