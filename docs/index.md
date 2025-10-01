# ITLAuth Documentation Index

Welcome to the ITLAuth documentation. This comprehensive guide covers all aspects of the ITlusions Authentication Suite.

## 📖 Documentation Structure

### 🚀 Quick Start
- [**README.md**](../README.md) - Main overview and quick start guide
- [**Installation Guide**](guides/INSTALLATION.md) - Complete installation instructions
- [**API Server OIDC Setup**](guides/APISERVER-OIDC-SETUP.md) - Configure Kubernetes API server

### 📚 User Guides
- [**Service Accounts Management**](guides/SERVICE-ACCOUNTS.md) - Keycloak and Kubernetes service accounts
- [**Troubleshooting Guide**](guides/TROUBLESHOOTING.md) - Common issues and solutions

### 🛠️ Scripts & Automation
- [**Scripts Overview**](scripts/README.md) - All automation scripts
- [**OIDC Setup Scripts**](scripts/oidc-setup/) - API server configuration automation
- [**Service Account Scripts**](scripts/service-accounts/) - Service account management tools
- [**Token Management Scripts**](scripts/token-management/) - Authentication token utilities

### 📋 Configuration Examples
- [**Kubeconfig Examples**](examples/kubeconfig-oidc.yaml) - OIDC kubeconfig templates
- [**API Server Configuration**](examples/apiserver-oidc.yaml) - Complete API server manifest
- [**RBAC Configuration**](examples/rbac-oidc.yaml) - Role-based access control examples
- [**Service Account Configuration**](examples/service-accounts.yaml) - Service account templates

## 🎯 Getting Started Paths

### For New Users
1. Read the [README.md](../README.md) overview
2. Follow the [Installation Guide](guides/INSTALLATION.md)
3. Review [Configuration Examples](examples/)
4. Test with [Troubleshooting Guide](guides/TROUBLESHOOTING.md) if needed

### For Administrators
1. Start with [API Server OIDC Setup](guides/APISERVER-OIDC-SETUP.md)
2. Use [OIDC Setup Scripts](scripts/oidc-setup/) for automation
3. Configure [RBAC](examples/rbac-oidc.yaml) for your teams
4. Implement [Service Accounts](guides/SERVICE-ACCOUNTS.md) for automation

### For Developers
1. Review [Service Account Scripts](scripts/service-accounts/) 
2. Examine [Token Management](scripts/token-management/) utilities
3. Use [Configuration Examples](examples/) as templates
4. Refer to [Troubleshooting Guide](guides/TROUBLESHOOTING.md) for debugging

### For CI/CD Integration
1. Set up [Service Accounts](guides/SERVICE-ACCOUNTS.md)
2. Use [Token Management Scripts](scripts/token-management/)
3. Implement [Automation Scripts](scripts/) in your pipelines
4. Configure appropriate [RBAC permissions](examples/rbac-oidc.yaml)

## 📖 Documentation by Topic

### Authentication & OIDC
| Document | Description | Audience |
|----------|-------------|----------|
| [Installation Guide](guides/INSTALLATION.md) | Complete setup instructions | All users |
| [API Server OIDC Setup](guides/APISERVER-OIDC-SETUP.md) | Configure Kubernetes OIDC | Administrators |
| [OIDC Setup Scripts](scripts/oidc-setup/) | Automation tools | Administrators |
| [Kubeconfig Examples](examples/kubeconfig-oidc.yaml) | Configuration templates | All users |

### Service Accounts
| Document | Description | Audience |
|----------|-------------|----------|
| [Service Accounts Guide](guides/SERVICE-ACCOUNTS.md) | Complete SA management | Administrators |
| [Service Account Scripts](scripts/service-accounts/) | Automation tools | Developers |
| [Service Account Examples](examples/service-accounts.yaml) | Configuration templates | All users |

### Access Control
| Document | Description | Audience |
|----------|-------------|----------|
| [RBAC Examples](examples/rbac-oidc.yaml) | Role-based access control | Administrators |
| [API Server Configuration](examples/apiserver-oidc.yaml) | Complete API server setup | Administrators |

### Token Management
| Document | Description | Audience |
|----------|-------------|----------|
| [Token Management Scripts](scripts/token-management/) | Token utilities | Developers |
| [Service Accounts Guide](guides/SERVICE-ACCOUNTS.md) | Token-based authentication | All users |

### Troubleshooting
| Document | Description | Audience |
|----------|-------------|----------|
| [Troubleshooting Guide](guides/TROUBLESHOOTING.md) | Common issues & solutions | All users |
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