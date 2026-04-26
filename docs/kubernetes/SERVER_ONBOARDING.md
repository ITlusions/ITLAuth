# 🖥️ Server & Cluster Onboarding Guide

## Overview

The **Server Onboarding** feature provides a guided web-based wizard for registering Kubernetes clusters with the ITL STS (Security Token Service) platform. This guide covers both the interactive web interface and the underlying CLI integration.

---

## 🎯 What is Server Onboarding?

Server Onboarding is a 4-step wizard that helps users:

1. **Register their Kubernetes cluster** with ITL's STS platform
2. **Configure OIDC authentication** for centralized identity management
3. **Generate secure setup tokens** with time-limited expiry
4. **Verify the cluster setup** before completing registration

**Access:** `/server-onboarding` (requires OIDC login)

---

## ✨ Key Features

### Protected by OIDC Authentication
- Login required via Keycloak
- Redirects unauthorized users to login page
- User email/name displayed in header
- Session-based token generation

### 4-Step Interactive Wizard

#### Step 1: Cluster Information
```
- Cluster Name (required)
- API Server URL (required)
- Region/Location (optional)
- Environment (dev/staging/prod)
- Description (optional)
```

#### Step 2: Generate Token
```
- One-click token generation
- 24-hour expiry
- Secure copy-to-clipboard
- Download as file
- Security warnings included
```

#### Step 3: Installation Instructions
```
- Pre-filled kubectl apply command
- Token automatically included
- Prerequisites checklist
- Estimated execution time
```

#### Step 4: Verification
```
- Kubectl status commands
- ServiceAccount verification
- OIDC configuration checks
- Next steps guidance
```

### Professional UI/UX
- Responsive Bootstrap 5 layout
- Dark theme code blocks
- Copy-to-clipboard buttons with feedback
- Toast notifications
- Form validation
- Mobile-optimized design (320px - 1920px)

### Quick Reference Section
- **Troubleshooting** - Common issues & solutions
- **Terraform** - Infrastructure-as-code examples
- **Helm** - Chart-based installation
- **Compliance** - Audit & SOC2 information

---

## 🚀 Using the Server Onboarding Page

### Access the Page

After logging in to the ITL website:

1. Navigate to: **Tools → Server Onboarding**
2. Or visit directly: `https://your-domain/server-onboarding`

### Complete the Wizard

**Step 1: Enter Cluster Details**
```
Cluster Name:      prod-eu-west-1
API Server URL:    https://api.cluster.local:6443
Region:            eu-west-1
Environment:       production
Description:       Main production cluster
```

**Step 2: Generate Token**
- Click "Generate Setup Token"
- Token appears with `k8s_` prefix
- Copy token (shows "Copied!" feedback)
- Or download as file for secure storage

**Step 3: Run Installation**
```bash
kubectl apply -f https://auth.itlusions.com/setup \
  --token=k8s_abc123xyz...xyz789
```

This command will:
- Create ServiceAccount for authentication
- Configure RBAC roles and bindings
- Setup OIDC authentication webhook
- Register cluster in STS platform
- Enable audit logging

**Step 4: Verify Setup**
```bash
# Check ServiceAccount
kubectl get serviceaccounts -n kube-system

# Verify OIDC configuration
kubectl get configmap -n kube-system

# Check cluster registration
kubectl auth whoami
```

---

## 🔐 Security Considerations

### Token Management
- ✅ Tokens generated server-side (never in browser)
- ✅ 24-hour expiry (configurable)
- ✅ One-time use by design
- ✅ Display-only (not stored in browser)
- ✅ Optional download for secure storage

### Authentication
- ✅ OIDC-protected page (login required)
- ✅ User identity logged on token generation
- ✅ API endpoints require authentication
- ✅ 401 Unauthorized for unauthenticated requests
- ✅ HTTPS recommended for production

### Data Protection
- ✅ No credentials hardcoded
- ✅ Sensitive info clearly marked
- ✅ Security warnings displayed
- ✅ User acknowledgment required

---

## 📋 API Endpoints

### Generate Token
```
POST /api/server-setup/generate-token

Request:
{
  "cluster_name": "prod-eu-west-1"
}

Response:
{
  "success": true,
  "token": "k8s_abc123xyz...xyz789",
  "expires_in_hours": 24,
  "message": "Token generated successfully"
}
```

### Validate Token
```
POST /api/server-setup/validate-token

Request:
{
  "token": "k8s_abc123xyz...xyz789"
}

Response:
{
  "valid": true,
  "message": "Token is valid",
  "expires_in": "23 hours 45 minutes"
}
```

---

## 💻 Implementation Details

### Backend (Python Flask)

**File:** `src/base/views/server_onboarding.py`

```python
def server_onboarding():
    """Render server/cluster onboarding page"""
    # OIDC-protected view
    # Extracts user email from session
    # Renders server_onboarding.html template

def api_generate_setup_token():
    """Generate setup token API endpoint"""
    # POST /api/server-setup/generate-token
    # Requires OIDC authentication
    # Returns token + expiry info

def api_validate_setup_token():
    """Validate setup token API endpoint"""
    # POST /api/server-setup/validate-token
    # Checks token validity and expiry
    # Returns validation result
```

**Files Modified:** `src/base/routers/auth.py`, `src/templates/_navigation.html`

### Frontend (HTML/CSS/JavaScript)

**File:** `src/templates/server_onboarding.html` (650+ lines)

```html
<!-- 4-step wizard with navigation -->
<!-- Bootstrap 5 responsive grid -->
<!-- Copy-to-clipboard functionality -->
<!-- Form validation -->
<!-- Toast notifications -->
<!-- Accordion help sections -->
```

---

## 🧪 Testing

### Quick Test Checklist
- [ ] Access without login → Redirects to `/login`
- [ ] Login successfully → Page loads
- [ ] Step 1: Enter valid cluster info → Continue enabled
- [ ] Step 2: Generate token → Token appears
- [ ] Copy token → Shows "Copied!" feedback
- [ ] Download token → File downloaded
- [ ] Step 3: Copy command → Full command copied
- [ ] Step 4: Verify steps visible
- [ ] Complete setup → Redirects to dashboard

### Browser Compatibility
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

### Mobile Responsiveness
- ✅ 320px (iPhone SE) - Single column, readable
- ✅ 768px (iPad) - 2-column layout
- ✅ 1920px (Desktop) - Full width

---

## 🚀 Deployment

### Docker
```bash
docker build -t itl.website:latest .
docker run -d \
  --name itl-website \
  -p 5000:5000 \
  -e KEYCLOAK_URL=https://keycloak.itlusions.com \
  -e KEYCLOAK_REALM=itlusions \
  itl.website:latest
```

### Kubernetes (Helm)
```bash
helm upgrade itl-website ./charts/itl.website/ \
  --values values-production.yaml \
  --namespace production
```

### Verification
```bash
# Test authentication redirect
curl -I https://your-domain/server-onboarding
# Expected: 302 (redirect to login)

# Test after login
curl -H "Cookie: session=..." https://your-domain/server-onboarding
# Expected: 200 (page loads)

# Test API endpoint
curl -X POST https://your-domain/api/server-setup/generate-token \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"cluster_name":"test"}'
# Expected: 200 with token response
```

---

## 📊 User Flow

```
User visits /server-onboarding
    ↓
[OIDC Check]
    ↓
Not logged in? → Redirect to /login
    ↓
Logged in? → Load wizard page
    ↓
Complete 4-step wizard
    ↓
Generate token → Run setup → Verify
    ↓
Redirect to /dashboard
```

---

## 🔧 Configuration

### Colors
- **Primary (Cluster):** `#007bff` (Blue)
- **Success (OIDC):** `#28a745` (Green)
- **Code blocks:** `#1e1e1e` (Dark)
- **Text:** `#212529` (Dark gray)

### Token Settings
- **Format:** `k8s_` prefix + random string
- **Expiry:** 24 hours (configurable)
- **One-time use:** By design
- **Storage:** Server-side only

### UI Components
- **Framework:** Bootstrap 5
- **Icons:** Bootstrap Icons
- **Animation:** CSS transitions
- **Notifications:** Toast messages

---

## 📚 Related Documentation

- [APISERVER-OIDC-SETUP.md](APISERVER-OIDC-SETUP.md) - API server OIDC configuration
- [CUSTOM_STS_SETUP.md](CUSTOM_STS_SETUP.md) - Custom STS setup
- [SERVICE-ACCOUNTS.md](SERVICE-ACCOUNTS.md) - Service account management
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues & solutions

---

## 🎓 Examples

### Register a Production Cluster
```bash
# Step 1: Visit page and fill in cluster info
# Cluster Name: prod-us-east-1
# API Server: https://api.prod.internal:6443
# Environment: production

# Step 2: Generate token
# Token: k8s_xyz789abc...

# Step 3: Run setup command
kubectl apply -f https://auth.itlusions.com/setup \
  --token=k8s_xyz789abc...

# Step 4: Verify
kubectl get serviceaccounts -n kube-system
```

### Terraform Integration
```hcl
resource "kubernetes_service_account" "itl_sts" {
  metadata {
    name      = "itl-sts-setup"
    namespace = "kube-system"
  }
}

resource "kubernetes_cluster_role_binding" "itl_sts" {
  metadata {
    name = "itl-sts-setup"
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = "cluster-admin"
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.itl_sts.metadata[0].name
    namespace = kubernetes_service_account.itl_sts.metadata[0].namespace
  }
}
```

### Helm Integration
```bash
helm repo add itl https://helm.itlusions.com
helm repo update

helm install itl-sts-setup itl/sts-setup \
  --namespace kube-system \
  --set token=k8s_xyz789abc...
```

---

## 💡 Tips & Best Practices

### Before Onboarding
- ✅ Verify cluster connectivity
- ✅ Check API server accessibility
- ✅ Ensure RBAC admin permissions
- ✅ Document cluster details

### During Onboarding
- ✅ Keep token secure (don't share)
- ✅ Run commands on appropriate cluster
- ✅ Verify each step completes
- ✅ Check logs for errors

### After Onboarding
- ✅ Run verification commands
- ✅ Test user OIDC login
- ✅ Verify audit logging
- ✅ Document setup details

---

## ❓ Troubleshooting

### Token Not Generating
- Check OIDC session is active
- Verify network connectivity
- Check API endpoint `/api/server-setup/generate-token`
- Review server logs

### Kubectl Apply Fails
- Verify token is correct (not expired)
- Check API server URL is reachable
- Ensure kubectl has admin permissions
- Review error messages

### Cluster Not Registered
- Verify setup command completed
- Check ServiceAccount was created
- Run verification commands
- Check cluster logs

### OIDC Not Working
- Verify Keycloak is reachable
- Check OIDC client configuration
- Verify cluster registration
- Review authentication logs

See: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more solutions.

---

## 📞 Support

For help with server onboarding:

1. **Check troubleshooting guide** - [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. **Review setup examples** - See Examples section above
3. **Contact support** - Email: support@itlusions.com
4. **Check logs** - Review application and cluster logs

---

## 📈 Monitoring

### Key Metrics to Track
- Token generation rate
- Setup success rate
- Cluster registration rate
- OIDC authentication success rate
- Average setup completion time

### Logging
- User actions logged (with consent)
- Token generation logged (with timestamp)
- Setup completion logged
- Errors logged for debugging

---

**Version:** 1.0.0  
**Status:** ✅ Production Ready  
**Last Updated:** February 1, 2026  
