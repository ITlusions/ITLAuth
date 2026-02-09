# ITL.ControlPlane.Cli Scripts

This directory contains automation scripts for ITL Control Plane CLI authentication suite, focused on server-side configuration and administrative operations.

## ITLC CLI

For client-side authentication and user workflows, use the `itlc` command-line tool:

```bash
pip install itlc
itlc --help
```

**Common ITLC commands:**
- `itlc configure oidc` - Setup OIDC kubeconfig contexts
- `itlc login` - Interactive authentication
- `itlc get-token` - Retrieve authentication tokens
- `itlc cluster add` - Register new clusters

See [OIDC_SETUP.md](../OIDC_SETUP.md) for complete ITLC usage guide.

---

## Scripts Overview

Scripts in this directory handle server-side configuration and administrative tasks that are outside the scope of the ITLC CLI.

## Directory Structure

### `/oidc-setup/`
Scripts for configuring OIDC authentication on Kubernetes API servers (server-side configuration).

- `configure-apiserver-oidc.sh` - Configure API server OIDC flags (Linux)
- `configure-apiserver-oidc.ps1` - Configure API server OIDC flags (Windows)
- `configure-apiserver-oidc-enhanced.sh` - Enhanced configuration with validation
- `check-oidc-config.sh` - Verify API server OIDC settings

**Usage:**
```bash
# Configure API server (requires control plane access)
./oidc-setup/configure-apiserver-oidc.sh

# Verify configuration
./oidc-setup/check-oidc-config.sh
```

**Note:** These scripts configure the Kubernetes API server. For client-side kubeconfig setup, use `itlc configure oidc` instead.

### `/service-accounts/`
Scripts for managing Keycloak service accounts and Kubernetes service account integration (administrative operations).

- `keycloak_sa_manager.py` - Manage Keycloak service account clients
- `Create-KeycloakServiceAccount.ps1` - Create service accounts (PowerShell)
- `create-keycloak-service-account.sh` - Create service accounts (Bash)
- `create-sa-kubeconfig.sh` - Generate kubeconfig for service accounts

**Usage:**
```bash
# Create Keycloak service account (requires admin credentials)
python service-accounts/keycloak_sa_manager.py create --name my-service-account

# PowerShell version
.\service-accounts\Create-KeycloakServiceAccount.ps1 -ServiceAccountName "my-sa"

# Generate kubeconfig for CI/CD
./service-accounts/create-sa-kubeconfig.sh my-service-account
```

**Note:** These scripts are for administrative service account management. For user authentication, use `itlc login` instead.

## Prerequisites

### OIDC Setup Scripts
- SSH access to Kubernetes control plane nodes
- Kubernetes admin privileges
- Backup of existing API server configuration

### Service Account Scripts
- Keycloak admin credentials
- Python 3.8+ (for Python scripts)
- PowerShell 5.1+ (for PowerShell scripts)
- curl and jq (for bash scripts)

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

### 1. OIDC API Server Setup
```bash
# Configure API server with OIDC (control plane)
./oidc-setup/configure-apiserver-oidc.sh

# Verify configuration
./oidc-setup/check-oidc-config.sh

# Setup client-side kubeconfig
itlc configure oidc
```

### 2. Service Account Creation
```bash
# Create Keycloak service account (admin operation)
python service-accounts/keycloak_sa_manager.py create \
    --name monitoring-sa \
    --description "Monitoring Service Account"

# Generate kubeconfig for service account
./service-accounts/create-sa-kubeconfig.sh monitoring-sa

# Test service account access
KUBECONFIG=./monitoring-sa-kubeconfig.yaml kubectl get pods
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