# Kubernetes Integration

Configure Kubernetes API server for OIDC authentication with Keycloak.

## 📚 Documentation

### Setup Guides

1. **[Server & Cluster Onboarding](SERVER_ONBOARDING.md)** ← **START HERE**
   - Interactive web wizard for cluster registration
   - Step-by-step guided setup (4 steps)
   - Token generation and validation
   - Kubernetes onboarding automation
   - OIDC authentication setup

2. **[API Server OIDC Setup](APISERVER-OIDC-SETUP.md)**
   - Complete guide for configuring Kubernetes API server
   - Supported distributions (kubeadm, AKS, EKS, GKE, RKE2)
   - OIDC flags configuration
   - Testing & validation

3. **[Service Accounts](SERVICE-ACCOUNTS.md)**
   - Create Keycloak service accounts for automation
   - Generate kubeconfig files
   - CI/CD integration
   - Token management

4. **[Custom STS Setup](CUSTOM_STS_SETUP.md)**
   - Deploy custom Keycloak instance as STS
   - Realm configuration
   - OIDC client setup
   - Production hardening

### Support

5. **[Troubleshooting](TROUBLESHOOTING.md)**
   - Common issues & solutions
   - OIDC configuration validation
   - Token validation errors
   - RBAC debugging

## 🚀 Quick Start

### Step 1: Configure API Server
```bash
# Add OIDC flags to kube-apiserver
--oidc-issuer-url=https://sts.company.com/realms/production
--oidc-client-id=kubernetes
--oidc-username-claim=preferred_username
--oidc-groups-claim=groups
```

### Step 2: Configure RBAC
```yaml
# Map OIDC groups to Kubernetes roles
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: developers-view
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: view
subjects:
- kind: Group
  name: developers  # From Keycloak
  apiGroup: rbac.authorization.k8s.io
```

### Step 3: User Authentication
```bash
# Login via ITLC
itlc login

# Configure kubectl
kubectl config set-credentials user@company.com \
  --exec-api-version=client.authentication.k8s.io/v1beta1 \
  --exec-command=itlc \
  --exec-arg=get-token \
  --exec-arg=--output=token

# Use kubectl
kubectl get pods
```

## 📊 Architecture

```
┌─────────────┐
│   kubectl   │
└──────┬──────┘
       │ 1. exec: itlc get-token
       ▼
┌─────────────┐
│    ITLC     │
└──────┬──────┘
       │ 2. Get token
       ▼
┌─────────────┐
│  Keycloak   │
└──────┬──────┘
       │ 3. JWT token
       ▼
┌─────────────┐
│ K8s API     │
│ Server      │
└─────────────┘
  4. Validate token
  5. Extract groups
  6. RBAC evaluation
```

## 🔧 Configuration Examples

See [../examples/kubernetes/](../examples/kubernetes/) for:
- `apiserver-oidc.yaml` - API server configuration
- `kubeconfig-oidc.yaml` - User kubeconfig
- `rbac-oidc.yaml` - RBAC group mappings
- `service-accounts.yaml` - Service account setup

## 📖 Related Documentation

- [Authentication](../authentication/) - Token management
- [PIM](../pim/) - Temporary privilege elevation
- [Installation](../getting-started/INSTALLATION.md) - ITLC installation

## Common Workflows

### Developer Workflow
```bash
# Daily login
itlc login

# All day kubectl usage
kubectl get pods
kubectl logs my-pod
kubectl exec -it my-pod -- bash

# Auto-refresh (no re-login needed)
```

### CI/CD Workflow
```bash
# Service account authentication
export KEYCLOAK_CLIENT_ID=github-actions
export KEYCLOAK_CLIENT_SECRET=${{ secrets.KEYCLOAK_SECRET }}

# Get token
TOKEN=$(itlc get-token --output=token)

# Configure kubectl
kubectl config set-credentials sa \
  --token=$TOKEN

# Deploy
kubectl apply -f deployment.yaml
```

### Admin Workflow (with PIM)
```bash
# Request temporary cluster-admin
itlc elevate --role=cluster-admin --duration=2h --reason="Deploy critical patch"

# Wait for approval (if required)

# Use elevated access
kubectl get nodes
kubectl apply -f critical-patch.yaml

# Access auto-revokes after 2h
```
