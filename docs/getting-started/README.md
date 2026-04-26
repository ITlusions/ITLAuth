# Getting Started

Quick start guides for ITLAuth setup and configuration.

## 📚 Documentation

1. **[Installation](INSTALLATION.md)**
   - Prerequisites
   - Installation methods (pip, source)
   - Configuration
   - First login

## 🚀 Quick Start (60 seconds)

### Install
```bash
pip install itl-kubectl-oidc-setup
```

### Login
```bash
# Interactive login (browser opens)
itlc login

# Verify
itlc whoami
```

### Get Token
```bash
# For scripts
TOKEN=$(itlc get-token --output=token)

# Use token
curl -H "Authorization: Bearer $TOKEN" https://api.example.com
```

**That's it!** 🎉

## 📖 Next Steps

### For Developers
1. [Interactive Login Guide](../authentication/INTERACTIVE_LOGIN.md)
2. [Token CLI Integration](../authentication/TOKEN_CLI_INTEGRATION.md)
3. [Kubernetes Setup](../kubernetes/APISERVER-OIDC-SETUP.md)

### For Administrators
1. [Keycloak Setup](../kubernetes/CUSTOM_STS_SETUP.md)
2. [PIM Deployment](../pim/KEYCLOAK_PIM_IMPLEMENTATIE.md)
3. [Agent Deployment](../pim/PRIVILEGE_AGENT.md)

### For DevOps
1. [Service Accounts](../kubernetes/SERVICE-ACCOUNTS.md)
2. [CI/CD Integration](../authentication/TOKEN_CLI_INTEGRATION.md#cicd-examples)
3. [Troubleshooting](../kubernetes/TROUBLESHOOTING.md)

## 🎯 Common Use Cases

### Kubernetes Access
```bash
# 1. Login
itlc login

# 2. Configure kubectl
kubectl config set-credentials user@company.com \
  --exec-command=itlc \
  --exec-arg=get-token \
  --exec-arg=--output=token

# 3. Use kubectl
kubectl get pods
```

### API Access (CI/CD)
```bash
# Set credentials
export KEYCLOAK_CLIENT_ID=my-service
export KEYCLOAK_CLIENT_SECRET=secret

# Get token
TOKEN=$(itlc get-token --output=token)

# Call API
curl -H "Authorization: Bearer $TOKEN" \
  https://api.company.com/v1/resources
```

### Temporary Privilege Elevation
```bash
# Request admin access (PIM)
itlc elevate --role=cluster-admin --duration=2h \
  --reason="Deploy critical patch"

# Use elevated access
kubectl apply -f critical-patch.yaml

# Access auto-revokes after 2h
```

## 🔧 Configuration

### Environment Variables
```bash
# Keycloak URL (optional, default: https://sts.itlusions.com)
export KEYCLOAK_URL=https://keycloak.company.com

# Realm (optional, default: itlusions)
export KEYCLOAK_REALM=production

# Service account credentials (for automation)
export KEYCLOAK_CLIENT_ID=my-service
export KEYCLOAK_CLIENT_SECRET=secret
```

### Config File
```bash
# Create config directory
mkdir -p ~/.itl

# Edit config
cat > ~/.itl/config.yaml <<EOF
keycloak_url: https://keycloak.company.com
realm: production
token_cache_dir: ~/.itl/token-cache
EOF
```

## 📊 Architecture Overview

```
┌──────────┐
│   User   │
└────┬─────┘
     │ itlc login
     ▼
┌──────────┐     ┌──────────┐
│ Browser  │────▶│ Keycloak │
└────┬─────┘     └────┬─────┘
     │ Authenticate     │
     │◀─────────────────┘
     │ Token
     ▼
┌──────────┐
│   ITLC   │
│  Cache   │
└────┬─────┘
     │ itlc get-token
     ▼
┌──────────┐
│   API    │
│  Server  │
└──────────┘
```

## 🆘 Troubleshooting

### Installation Issues
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install with verbose
pip install -v itl-kubectl-oidc-setup

# Check version
itlc --version
```

### Login Issues
```bash
# Clear cache
itlc clear-cache --all

# Try device code flow (headless)
itlc login --device-code

# Check logs
itlc login --debug
```

### Token Issues
```bash
# Inspect token
TOKEN=$(itlc get-token --output=token)
itlc inspect $TOKEN --decode

# Validate token
itlc introspect $TOKEN

# Refresh token
itlc logout
itlc login
```

## 📖 Related Documentation

- [Installation Guide](INSTALLATION.md) - Complete installation
- [Authentication](../authentication/) - Login methods
- [Kubernetes](../kubernetes/) - K8s integration
- [PIM](../pim/) - Privilege elevation

## 🔗 External Resources

- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [OIDC Specification](https://openid.net/specs/openid-connect-core-1_0.html)
- [Kubernetes OIDC](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#openid-connect-tokens)
