# ITLAuth Scripts

This directory contains automation scripts for the ITLAuth authentication suite. Scripts are organized into functional categories.

## Directory Structure

### `/oidc-setup/`
Scripts for configuring OIDC authentication on Kubernetes API servers.

- `configure-apiserver-oidc.sh` - Main OIDC setup script for Linux
- `configure-apiserver-oidc.ps1` - PowerShell version for Windows/cross-platform
- `configure-apiserver-oidc-enhanced.sh` - Enhanced version with additional features
- `check-oidc-config.sh` - Verification script to check OIDC configuration

**Usage:**
```bash
# Linux/macOS
./oidc-setup/configure-apiserver-oidc.sh

# Windows PowerShell
.\oidc-setup\configure-apiserver-oidc.ps1

# Verify configuration
./oidc-setup/check-oidc-config.sh
```

### `/service-accounts/`
Scripts for managing Keycloak service accounts and Kubernetes service account integration.

- `keycloak_sa_manager.py` - Python utility for managing Keycloak service accounts
- `Create-KeycloakServiceAccount.ps1` - PowerShell script for service account creation
- `create-keycloak-service-account.sh` - Bash script for service account creation
- `create-sa-kubeconfig.sh` - Generate kubeconfig for service accounts

**Usage:**
```bash
# Create service account with Python
python service-accounts/keycloak_sa_manager.py create --name my-service-account

# Create with PowerShell
.\service-accounts\Create-KeycloakServiceAccount.ps1 -ServiceAccountName "my-sa" -Description "My Service Account"

# Create kubeconfig for service account
./service-accounts/create-sa-kubeconfig.sh my-service-account
```

### `/token-management/`
Scripts for managing authentication tokens, token refresh, and persistent authentication.

- `persistent_token_manager.py` - Python tool for managing persistent tokens
- `generate_current_token.py` - Extract current user's authentication token
- `create-persistent-token.sh` - Create long-lived authentication tokens
- `manage-oidc-tokens.sh` - General token management utilities

**Usage:**
```bash
# Generate current user token
python token-management/generate_current_token.py

# Create persistent token
./token-management/create-persistent-token.sh

# Manage tokens
./token-management/manage-oidc-tokens.sh refresh
```

## Prerequisites

### Common Requirements
- kubectl installed and configured
- Access to Kubernetes cluster (for OIDC setup scripts)
- Access to Keycloak admin console (for service account scripts)

### Script-Specific Requirements

**OIDC Setup Scripts:**
- SSH access to Kubernetes control plane nodes
- Kubernetes admin privileges
- Backup of existing API server configuration

**Service Account Scripts:**
- Keycloak admin credentials
- Python 3.6+ (for Python scripts)
- PowerShell 5.1+ (for PowerShell scripts)
- curl and jq (for bash scripts)

**Token Management Scripts:**
- Existing OIDC authentication setup
- kubelogin plugin installed
- Valid Keycloak user account

## Environment Variables

Many scripts support configuration via environment variables:

```bash
# Keycloak Configuration
export KEYCLOAK_SERVER="https://sts.itlusions.com"
export KEYCLOAK_REALM="itlusions"
export KEYCLOAK_ADMIN_USER="admin"
export KEYCLOAK_ADMIN_PASSWORD="your-admin-password"

# Kubernetes Configuration
export KUBECONFIG="$HOME/.kube/config"
export K8S_API_SERVER="https://your-k8s-api:6443"

# OIDC Configuration
export OIDC_ISSUER_URL="https://sts.itlusions.com/realms/itlusions"
export OIDC_CLIENT_ID="kubernetes-oidc"
```

## Quick Start Examples

### 1. Complete OIDC Setup
```bash
# Configure API server with OIDC
./oidc-setup/configure-apiserver-oidc.sh

# Verify configuration
./oidc-setup/check-oidc-config.sh

# Test authentication
kubectl oidc-login get-token --oidc-issuer-url=https://sts.itlusions.com/realms/itlusions --oidc-client-id=kubernetes-oidc
```

### 2. Service Account Workflow
```bash
# Create Keycloak service account
python service-accounts/keycloak_sa_manager.py create --name monitoring-sa --description "Monitoring Service Account"

# Create kubeconfig for the service account
./service-accounts/create-sa-kubeconfig.sh monitoring-sa

# Test service account access
KUBECONFIG=./monitoring-sa-kubeconfig.yaml kubectl get pods
```

### 3. Token Management
```bash
# Extract current user token
python token-management/generate_current_token.py > my-token.txt

# Create persistent token for automation
./token-management/create-persistent-token.sh automation-user

# Set up token refresh
./token-management/manage-oidc-tokens.sh setup-refresh
```

## Script Execution Policies

### PowerShell Scripts
If you encounter execution policy errors on Windows:
```powershell
# Allow local scripts (run as administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine

# Or bypass for current session
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

### Shell Scripts
Ensure scripts have execute permissions:
```bash
# Make scripts executable
chmod +x oidc-setup/*.sh
chmod +x service-accounts/*.sh
chmod +x token-management/*.sh
```

## Safety and Backup

**Always backup before running scripts:**

```bash
# Backup kubeconfig
cp ~/.kube/config ~/.kube/config.backup.$(date +%Y%m%d-%H%M%S)

# Backup API server config (on control plane)
sudo cp /etc/kubernetes/manifests/kube-apiserver.yaml /etc/kubernetes/manifests/kube-apiserver.yaml.backup.$(date +%Y%m%d-%H%M%S)

# Backup Keycloak realm (if possible)
# Export realm configuration before making changes
```

## Troubleshooting

### Common Issues

1. **Permission Denied:**
   - Check script execute permissions
   - Verify you have necessary Kubernetes/Keycloak access
   - Run with appropriate privileges (sudo for system changes)

2. **Network Connectivity:**
   - Verify access to Keycloak server
   - Check firewall/proxy settings
   - Test with curl before running scripts

3. **Authentication Failures:**
   - Verify Keycloak credentials
   - Check OIDC client configuration
   - Validate certificate trust

### Debug Mode

Most scripts support debug/verbose mode:
```bash
# Enable debug output
export DEBUG=1
./script-name.sh

# Or use bash debug mode
bash -x ./script-name.sh
```

### Getting Help

Each script typically supports help options:
```bash
./script-name.sh --help
python script-name.py --help
Get-Help .\script-name.ps1
```

For additional support, see the [Troubleshooting Guide](../guides/TROUBLESHOOTING.md).

## Development

### Adding New Scripts

When adding new scripts to this collection:

1. **Choose appropriate directory** based on functionality
2. **Follow naming conventions:**
   - Use kebab-case for shell scripts: `my-new-script.sh`
   - Use PascalCase for PowerShell: `My-NewScript.ps1`
   - Use snake_case for Python: `my_new_script.py`
3. **Include help text** and usage examples
4. **Add error handling** and validation
5. **Update this README** with script description
6. **Test on target platforms**

### Testing

Test scripts in safe environments before production use:
- Use test Kubernetes clusters
- Test with non-production Keycloak realms
- Validate with limited-privilege accounts

## Related Documentation

- [Installation Guide](../guides/INSTALLATION.md)
- [API Server OIDC Setup](../guides/APISERVER-OIDC-SETUP.md)
- [Service Accounts Guide](../guides/SERVICE-ACCOUNTS.md)
- [Troubleshooting Guide](../guides/TROUBLESHOOTING.md)
- [Configuration Examples](../examples/)