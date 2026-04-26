# OIDC Kubernetes Authentication with ITLC

This guide explains how to setup and use OIDC authentication for Kubernetes clusters with the ITLC CLI.

## Overview

ITLC provides built-in OIDC (OpenID Connect) authentication for Kubernetes clusters using Keycloak. This allows you to authenticate to Kubernetes using your Keycloak credentials without needing separate kubeconfig credentials.

## Features

- **Two Authentication Methods**:
  - **Python-based**: No external dependencies, pure Python OIDC flow
  - **Binary-based**: Using `kubectl-oidc_login` plugin (kubelogin)

- **Two Access Modes**:
  - **Direct**: Connect directly to the cluster API
  - **SSH Tunnel**: Connect through SSH tunnel (for remote/restricted networks)

## Pre-configured OIDC Contexts

ITLC automatically provides 4 OIDC authentication contexts:

| Context Name | Auth Method | Access Mode | Best For |
|--------------|-------------|-------------|----------|
| `itl-python` | Python (built-in) | Direct | Development, minimal dependencies |
| `itl` | Binary (kubelogin) | Direct | Standard kubectl access |
| `itl-ssh-tunnel-python` | Python + SSH | SSH tunnel | Remote access, minimal dependencies |
| `itl-ssh-tunnel` | Binary + SSH | SSH tunnel | Remote access with kubelogin |

## Quick Start

### 1. Setup OIDC Contexts (Easiest)

Use the built-in configuration command:

```bash
# Setup all OIDC contexts automatically
itlc configure oidc

# Or Python-only (no external dependencies)
itlc configure oidc --python-only

# Use with kubectl
kubectl --context=itl-python get nodes
```

### 2. Using Python OIDC Authentication (Manual)

The Python method requires no external binaries:

```bash
# Set your cluster API server in kubeconfig
kubectl config set-cluster my-cluster --server=https://your-cluster-api:6443

# Use the Python OIDC context
kubectl --context=itl-python get nodes
```

On first use, your browser will open for Keycloak authentication. After login, the token is cached automatically.

## CLI Configuration Command

The `itlc configure oidc` command automatically sets up OIDC authentication contexts in your kubeconfig.

### Basic Usage

```bash
# Setup all OIDC contexts
itlc configure oidc

# See all options
itlc configure oidc --help
```

### Options

```bash
# Python-only (no kubelogin binary)
itlc configure oidc --python-only

# Specify cluster server
itlc configure oidc --server https://10.99.100.4:6443

# Skip authentication test
itlc configure oidc --no-test

# Specify cluster name
itlc configure oidc --cluster-name my-cluster
```

### What It Does

1. Creates/updates `~/.kube/config` with OIDC contexts
2. Configures 4 authentication contexts (2 with `--python-only`)
3. Sets up Python and/or Binary OIDC authentication
4. Configures both direct and SSH tunnel access modes

### Created Contexts

| Context | Auth Method | Access Mode | Use Case |
|---------|-------------|-------------|----------|
| `itl-python` | Python | Direct | Development, minimal dependencies |
| `itl` | Binary | Direct | Standard kubectl with kubelogin |
| `itl-ssh-tunnel-python` | Python | SSH tunnel | Remote access, minimal deps |
| `itl-ssh-tunnel` | Binary | SSH tunnel | Remote access with kubelogin |

### 3. Using Binary OIDC Authentication

Requires `kubectl-oidc_login` plugin:

```bash
# Install kubelogin (if not already installed)
# See: https://github.com/int128/kubelogin

# Use the binary OIDC context
kubectl --context=itl get nodes
```

## Setup Kubeconfig Manually

If you need to create a custom kubeconfig with OIDC authentication:

### Python-based OIDC User

```yaml
users:
  - name: oidc-user-python
    user:
      exec:
        apiVersion: client.authentication.k8s.io/v1beta1
        command: python
        args:
          - -m
          - itlc.oidc_auth
        env: null
        interactiveMode: IfAvailable
        provideClusterInfo: false
```

### Binary-based OIDC User (kubelogin)

```yaml
users:
  - name: oidc-user
    user:
      exec:
        apiVersion: client.authentication.k8s.io/v1beta1
        command: kubectl-oidc_login
        args:
          - get-token
          - '--oidc-issuer-url=https://sts.itlusions.com/realms/itlusions'
          - '--oidc-client-id=kubernetes-oidc'
        env: null
        interactiveMode: IfAvailable
        provideClusterInfo: false
```

### Complete Kubeconfig Example

```yaml
apiVersion: v1
kind: Config
preferences: {}
current-context: itl-python

clusters:
  - cluster:
      server: https://10.99.100.4:6443
      insecure-skip-tls-verify: true  # For development only!
    name: my-cluster

contexts:
  - context:
      cluster: my-cluster
      user: oidc-user-python
    name: itl-python
  - context:
      cluster: my-cluster
      user: oidc-user
    name: itl

users:
  - name: oidc-user-python
    user:
      exec:
        apiVersion: client.authentication.k8s.io/v1beta1
        command: python
        args:
          - -m
          - itlc.oidc_auth
  - name: oidc-user
    user:
      exec:
        apiVersion: client.authentication.k8s.io/v1beta1
        command: kubectl-oidc_login
        args:
          - get-token
          - '--oidc-issuer-url=https://sts.itlusions.com/realms/itlusions'
          - '--oidc-client-id=kubernetes-oidc'
```

## Using with ITLC Cluster Management

Register your cluster with ITLC:

```bash
# Register a cluster
itlc cluster add --name prod-cluster --server https://10.99.100.4:6443 --environment production

# List registered clusters
itlc cluster list

# Use with kubectl (automatically uses OIDC authentication)
kubectl --context=prod-cluster get nodes
```

## SSH Tunnel Setup

For remote clusters or when behind a firewall:

```bash
# Setup SSH tunnel (in separate terminal)
ssh -L 16643:10.99.100.4:6443 user@jump-host

# Use SSH tunnel context
kubectl --context=itl-ssh-tunnel-python get nodes
```

The SSH tunnel contexts expect the tunnel on `127.0.0.1:16643`.

## Environment Variables

Configure OIDC settings via environment variables:

```bash
export KEYCLOAK_URL=https://sts.itlusions.com
export KEYCLOAK_REALM=itlusions
```

## Token Caching

OIDC tokens are automatically cached in `~/.kube/cache/oidc/` and refreshed as needed. You won't need to re-authenticate for each kubectl command.

### Clear Token Cache

```bash
# Clear kubectl OIDC cache
rm -rf ~/.kube/cache/oidc/

# Or clear ITLC token cache
itlc clear-cache --all
```

## Troubleshooting

### Browser Doesn't Open

```bash
# Check if port 8000 is available
netstat -an | grep 8000

# Try binary method instead
kubectl --context=itl get nodes
```

### "exec: executable python failed"

```bash
# Ensure Python is in PATH
python --version

# Or use full Python path in kubeconfig
command: /usr/bin/python3
```

### "connection refused" to Keycloak

```bash
# Check Keycloak URL
curl https://sts.itlusions.com/realms/itlusions/.well-known/openid-configuration

# Verify environment variables
itlc config
```

### Token Expired

Tokens are auto-refreshed. If you get auth errors:

```bash
# Clear cache and re-authenticate
rm -rf ~/.kube/cache/oidc/
kubectl --context=itl-python get nodes
```

### RBAC Permission Denied

Your Keycloak user needs proper Kubernetes RBAC roles:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: oidc-cluster-admin
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: User
  name: your-email@domain.com  # From Keycloak token
  apiGroup: rbac.authorization.k8s.io
```

## Programmatic Use

Use OIDC authentication in Python scripts:

```python
from itlc.oidc_auth import get_oidc_token, output_credential

# Get OIDC token
token_data = get_oidc_token()

# Output in kubectl exec credential format
output_credential(token_data['token'], token_data.get('expiry'))
```

## Advanced Configuration

### Custom Keycloak Server

```bash
# Set custom Keycloak URL
export KEYCLOAK_URL=https://your-keycloak.com
export KEYCLOAK_REALM=your-realm

# Verify configuration
itlc config
```

### Multiple Clusters

```bash
# Register multiple clusters
itlc cluster add --name dev-cluster --server https://dev.example.com:6443 --environment development
itlc cluster add --name prod-cluster --server https://prod.example.com:6443 --environment production

# Switch between them
kubectl --context=dev-cluster get nodes
kubectl --context=prod-cluster get nodes
```

### Available OIDC Contexts

List all pre-configured OIDC contexts:

```bash
# View in kubeconfig
kubectl config get-contexts | grep itl

# Expected contexts:
# itl                    - Binary auth, direct access
# itl-python             - Python auth, direct access
# itl-ssh-tunnel         - Binary auth, via SSH tunnel
# itl-ssh-tunnel-python  - Python auth, via SSH tunnel
```

## Testing OIDC Authentication

```bash
# Test with simple command
kubectl --context=itl-python cluster-info

# Check current user
kubectl --context=itl-python auth whoami

# Test permissions
kubectl --context=itl-python auth can-i list pods
kubectl --context=itl-python auth can-i create deployments
```

## Docker Testing

Test OIDC setup in an isolated container:

```bash
# Build test container
docker build -t itlc-test .

# Test OIDC module directly
docker run --rm itlc-test python -m itlc.oidc_auth

# Note: Interactive browser login won't work in containers
# Use service account tokens for containerized environments
```

## Integration with CI/CD

For CI/CD pipelines, use service account tokens instead of interactive OIDC:

```bash
# Get service account token
TOKEN=$(itlc get-token --client-id=${CLIENT_ID} --client-secret=${CLIENT_SECRET} --output=token)

# Use with kubectl
kubectl --token=$TOKEN get nodes
```

See [docs/kubernetes/SERVICE-ACCOUNTS.md](../kubernetes/SERVICE-ACCOUNTS.md) for more details.

## References

- [Kubernetes Authentication](https://kubernetes.io/docs/reference/access-authn-authz/authentication/)
- [OIDC Authentication](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#openid-connect-tokens)
- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [kubelogin (int128)](https://github.com/int128/kubelogin)
- [ITLC Documentation](../index.md)
