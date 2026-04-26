# ITL Control Plane CLI Documentation

Welcome to ITL.ControlPlane.Cli - Complete OIDC authentication and resource management CLI for ITlusions with Just-In-Time privilege management.

## 📖 Documentation Categories

### 🚀 [Getting Started](getting-started/)
Start here for installation and basic configuration
- [Installation Guide](getting-started/INSTALLATION.md) - Setup ITLC on your system
- Quick start examples and first login

### 🔐 [Authentication](authentication/)
Token management and login methods
- [Interactive Login](authentication/INTERACTIVE_LOGIN.md) - Browser-based authentication (Azure CLI-style)
- [Token CLI Integration](authentication/TOKEN_CLI_INTEGRATION.md) - Service accounts & CI/CD
- [Realm Discovery](authentication/REALM_DISCOVERY.md) - Multi-tenant realm management
- [Realm Isolation](authentication/REALM_ISOLATION.md) - Security boundaries

### ☸️ [Kubernetes Integration](kubernetes/)
Configure Kubernetes API server for OIDC
- [**OIDC Setup with ITLC**](OIDC_SETUP.md) - **Complete OIDC authentication guide**
- [API Server OIDC Setup](kubernetes/APISERVER-OIDC-SETUP.md) - Complete K8s configuration guide
- [Service Accounts](kubernetes/SERVICE-ACCOUNTS.md) - Automation & CI/CD
- [Custom STS Setup](kubernetes/CUSTOM_STS_SETUP.md) - Deploy your own Keycloak
- [Troubleshooting](kubernetes/TROUBLESHOOTING.md) - Common issues & solutions

### 🎯 [Privileged Identity Management (PIM)](pim/)
Just-In-Time privilege elevation for Kubernetes and endpoints
- [**Complete PIM Guide**](pim/PRIVILEGE_ELEVATION_COMPLETE.md) - **START HERE** for PIM overview
- [Keycloak PIM Implementation](pim/KEYCLOAK_PIM_IMPLEMENTATIE.md) - Step-by-step deployment (Nederlands)
- [Privilege Agent](pim/PRIVILEGE_AGENT.md) - Local admin rights & software installation
- 4 elevation types: Kubernetes groups, Local groups, Azure AD groups, API scopes

### 🏗️ [Architecture](architecture/)
Design principles and security model
- [Self-Hosted Security](architecture/SELF_HOSTED_SECURITY.md) - Why self-host vs SaaS

### 📋 [Examples](examples/)
Configuration templates and YAML examples
- [Kubernetes Examples](examples/kubernetes/) - API server, kubeconfig, RBAC, service accounts

### 🛠️ [Scripts](scripts/)
Automation scripts for deployment and management
- [OIDC Setup Scripts](scripts/oidc-setup/) - API server automation
- [Service Account Scripts](scripts/service-accounts/) - Account management
- [Token Management Scripts](scripts/token-management/) - Token utilities

### 🐳 [Testing & Development](DOCKER_TESTING.md)
Test ITLC in isolated environments
- [Docker Testing Guide](DOCKER_TESTING.md) - Test without affecting your system
- Isolated container testing
- Development workflows

---

## 🎯 Quick Navigation

### I want to...

**Authenticate users to Kubernetes**
1. [Install ITLC](getting-started/INSTALLATION.md)
2. [Setup OIDC Authentication](OIDC_SETUP.md)
3. [Configure API server](kubernetes/APISERVER-OIDC-SETUP.md)
4. [Login](authentication/INTERACTIVE_LOGIN.md): `itlc login`

**Give temporary admin access (PIM)**
1. [PIM Overview](pim/PRIVILEGE_ELEVATION_COMPLETE.md)
2. [Deploy PIM Controller](pim/KEYCLOAK_PIM_IMPLEMENTATIE.md)
3. [Request elevation](pim/PRIVILEGE_ELEVATION_COMPLETE.md#itlc-cli-commands): `itlc elevate --role=cluster-admin`

**Install software without admin rights**
1. [Privilege Agent Setup](pim/PRIVILEGE_AGENT.md)
2. [Request installation](pim/PRIVILEGE_AGENT.md#software-installatie-aanvragen): `itlc install --app=docker-desktop`

**Automate with service accounts**
1. [Create service account](kubernetes/SERVICE-ACCOUNTS.md)
2. [CI/CD integration](authentication/TOKEN_CLI_INTEGRATION.md#cicd-examples)

**Deploy custom Keycloak**
1. [Custom STS Setup](kubernetes/CUSTOM_STS_SETUP.md)
2. [Configure ITLC](kubernetes/CUSTOM_STS_SETUP.md#configure-itlc)

---

## 🚀 Getting Started Paths

### For End Users
1. [Install ITLC](getting-started/INSTALLATION.md) → `pip install itl-kubectl-oidc-setup`
2. [Login](authentication/INTERACTIVE_LOGIN.md) → `itlc login`
3. [Use kubectl](kubernetes/APISERVER-OIDC-SETUP.md#user-authentication) → Automatic token injection

### For Kubernetes Administrators
1. [API Server OIDC Setup](kubernetes/APISERVER-OIDC-SETUP.md) - Configure K8s
2. [RBAC Configuration](examples/kubernetes/rbac-oidc.yaml) - Map groups to roles
3. [Service Accounts](kubernetes/SERVICE-ACCOUNTS.md) - Automation setup
4. [Troubleshooting](kubernetes/TROUBLESHOOTING.md) - Validation & debugging

### For Security Teams (PIM)
1. [PIM Overview](pim/PRIVILEGE_ELEVATION_COMPLETE.md) - Understand Just-In-Time access
2. [Deploy PIM Controller](pim/KEYCLOAK_PIM_IMPLEMENTATIE.md) - Backend setup
3. [Deploy Agents](pim/PRIVILEGE_AGENT.md) - Endpoint management
4. [Configure Roles](pim/PRIVILEGE_ELEVATION_COMPLETE.md#configuratie) - Define eligible roles

### For Developers
1. [Service Accounts](kubernetes/SERVICE-ACCOUNTS.md) - Non-interactive authentication
2. [Token Management](scripts/token-management/) - CI/CD token handling
3. [Configuration Examples](examples/kubernetes/) - Code templates
4. [Troubleshooting](kubernetes/TROUBLESHOOTING.md) - Debug authentication

### For CI/CD Integration
1. [Service Accounts](kubernetes/SERVICE-ACCOUNTS.md) - Create automation accounts
2. [Token CLI](authentication/TOKEN_CLI_INTEGRATION.md) - Pipeline integration
3. [RBAC Permissions](examples/kubernetes/rbac-oidc.yaml) - Least privilege setup
4. [Automation Scripts](scripts/) - Deployment helpers

## 📖 Documentation by Topic

### Authentication & OIDC
| Document | Description | Audience |
|----------|-------------|----------|
| [Installation Guide](getting-started/INSTALLATION.md) | Complete setup instructions | All users |
| [**OIDC Setup**](OIDC_SETUP.md) | **Kubernetes OIDC authentication** | **All users** |
| [API Server OIDC Setup](kubernetes/APISERVER-OIDC-SETUP.md) | Configure Kubernetes OIDC | Administrators |
| [Interactive Login](authentication/INTERACTIVE_LOGIN.md) | Browser-based auth | End users |
| [Token CLI](authentication/TOKEN_CLI_INTEGRATION.md) | Service account auth | Developers |

### Privilege Management
| Document | Description | Audience |
|----------|-------------|----------|
| [PIM Complete Guide](pim/PRIVILEGE_ELEVATION_COMPLETE.md) | All elevation types | Security teams |
| [Privilege Agent](pim/PRIVILEGE_AGENT.md) | Endpoint management | Admins |
| [Keycloak PIM Setup](pim/KEYCLOAK_PIM_IMPLEMENTATIE.md) | Backend deployment | DevOps |

### Service Accounts
| Document | Description | Audience |
|----------|-------------|----------|
| [Service Accounts Guide](kubernetes/SERVICE-ACCOUNTS.md) | Complete SA management | Administrators |
| [Service Account Scripts](scripts/service-accounts/) | Automation tools | Developers |
| [Service Account Examples](examples/kubernetes/service-accounts.yaml) | Configuration templates | All users |

### Access Control
| Document | Description | Audience |
|----------|-------------|----------|
| [RBAC Examples](examples/kubernetes/rbac-oidc.yaml) | Role-based access control | Administrators |
| [API Server Configuration](examples/kubernetes/apiserver-oidc.yaml) | Complete API server setup | Administrators |
| [Realm Isolation](authentication/REALM_ISOLATION.md) | Multi-tenant security | Security teams |

### Troubleshooting
| Document | Description | Audience |
|----------|-------------|----------|
| [Troubleshooting Guide](kubernetes/TROUBLESHOOTING.md) | Common issues & solutions | All users |
| [Scripts Documentation](scripts/README.md) | Script-specific troubleshooting | Developers |

## 🔍 Quick Reference

### Essential Commands
```bash
# Install ITLAuth tool
pip install itl-kubectl-oidc-setup

# Configure OIDC
itl-kubectl-oidc-setup

# Test authentication
kubectl oidc-login get-token --oidc-issuer-url=https://sts.itlusions.com/realms/itlusions --oidc-client-id=kubernetes-oidc

# Check current user
kubectl auth whoami
```

### Key URLs
- **Keycloak Server:** https://sts.itlusions.com
- **OIDC Issuer:** https://sts.itlusions.com/realms/itlusions
- **Client ID:** kubernetes-oidc
- **GitHub Repository:** https://github.com/ITlusions/ITLAuth

### Important Files
- **Kubeconfig:** `~/.kube/config`
- **API Server Manifest:** `/etc/kubernetes/manifests/kube-apiserver.yaml`
- **Token Cache:** `~/.kube/cache/oidc-login/`

## 🔄 Documentation Updates

This documentation is actively maintained. For the latest updates:

1. **Check GitHub:** [ITLAuth Repository](https://github.com/ITlusions/ITLAuth)
2. **Version Info:** See [README.md](../README.md) for current version
3. **Changelog:** Track changes in Git history
4. **Issues:** Report documentation issues on GitHub

## 🤝 Contributing

Help improve this documentation:

1. **Report Issues:** Found something unclear? [Create an issue](https://github.com/ITlusions/ITLAuth/issues)
2. **Suggest Improvements:** Submit pull requests for documentation enhancements
3. **Add Examples:** Share your configuration examples
4. **Update Scripts:** Contribute automation improvements

## 📞 Support

Need help? Here are your options:

### Self-Service
1. Check the [Troubleshooting Guide](guides/TROUBLESHOOTING.md)
2. Review [Configuration Examples](examples/)
3. Test with [Scripts](scripts/) in debug mode

### Community Support
1. [GitHub Discussions](https://github.com/ITlusions/ITLAuth/discussions)
2. [GitHub Issues](https://github.com/ITlusions/ITLAuth/issues)

### Professional Support
1. ITlusions Support: [www.itlusions.com](https://www.itlusions.com)
2. Enterprise Support: Contact via website
3. Custom Integration: Professional services available

---

**💡 Tip:** Bookmark this page as your starting point for all ITLAuth documentation!

Last updated: $(date +"%Y-%m-%d")  
Version: See [README.md](../README.md)