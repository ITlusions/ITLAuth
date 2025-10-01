# ITLAuth - ITlusions Authentication Suite

🚀 **Complete## 📚 Documentation

### 📖 Complete Documentation Hub
- **[📋 Documentation Index](docs/index.md)** - Complete navigation and overview of all documentation

### 📖 User Guides
- **[Installation Guide](docs/guides/INSTALLATION.md)** - Complete installation and setup instructions
- **[API Server Setup](docs/guides/APISERVER-OIDC-SETUP.md)** - Configure Kubernetes API server for OIDC
- **[Troubleshooting Guide](docs/guides/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Service Account Management](docs/guides/SERVICE-ACCOUNTS.md)** - Keycloak service account setuputhentication solution for ITlusions Kubernetes clusters**

ITLAuth provides automated tools and comprehensive guides for setting up OIDC authentication with ITlusions Kubernetes clusters using Keycloak. This suite includes automated setup tools, API server configuration scripts, and service account management utilities.

## ✨ Components

### 🔧 kubectl OIDC Setup Tool
- **Automatic kubectl installation** (if not already installed)
- **kubelogin plugin installation** via krew or direct download
- **OIDC configuration** for ITlusions Keycloak authentication
- **Cross-platform support** (Windows, macOS, Linux)
- **Interactive setup** with colored terminal output
- **Authentication testing** to verify configuration

### � Keycloak Service Account Manager
- **Centralized service account management** in Keycloak
- **Client credentials flow** for automation
- **Group-based permissions** integration
- **Token management** and refresh capabilities

### ⚙️ API Server Configuration Tools
- **Automated OIDC configuration** for Kubernetes API server
- **Backup and restore** functionality
- **Configuration validation** and testing
- **Troubleshooting scripts** and diagnostics

## 🚀 Quick Start

### Option 1: Python Package Installation

```bash
pip install itl-kubectl-oidc-setup
itl-kubectl-oidc-setup
```

### Option 2: Manual Script Execution

```bash
# Clone this repository
git clone https://github.com/ITlusions/ITLAuth.git
cd ITLAuth

# Run the setup script
python docs/scripts/setup_kubectl_oidc.py
```

### Option 3: PowerShell (Windows)

```powershell
# Clone this repository
git clone https://github.com/ITlusions/ITLAuth.git
cd ITLAuth

# Run PowerShell setup
.\docs\scripts\Setup-KubectlOIDC.ps1
```

## � Documentation

### 📖 User Guides
- **[Installation Guide](docs/guides/INSTALLATION.md)** - Complete installation and setup instructions
- **[API Server Setup](docs/guides/APISERVER-OIDC-SETUP.md)** - Configure Kubernetes API server for OIDC
- **[Troubleshooting Guide](docs/guides/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Service Account Management](docs/guides/SERVICE-ACCOUNTS.md)** - Keycloak service account setup

### �️ Scripts and Tools
- **[Setup Scripts](docs/scripts/)** - Automated setup and configuration scripts
- **[PowerShell Modules](docs/scripts/)** - Windows-specific PowerShell tools
- **[Python Utilities](docs/scripts/)** - Cross-platform Python tools
- **[Bash Scripts](docs/scripts/)** - Linux/macOS shell scripts

### 🔧 Configuration Examples
- **[kubeconfig Examples](docs/examples/)** - Sample kubeconfig files
- **[RBAC Configurations](docs/examples/)** - Role-based access control examples
- **[Keycloak Client Setup](docs/examples/)** - Keycloak client configuration

## 🏗️ Architecture

```
ITLAuth Architecture
├── Client Tools (kubectl + kubelogin)
├── OIDC Authentication (Keycloak)
├── Kubernetes API Server (OIDC enabled)
└── RBAC (Group-based permissions)
```

### Authentication Flow
1. **Client Request** → kubectl command executed
2. **Token Check** → kubelogin checks for valid token
3. **Browser Auth** → Opens browser for Keycloak login (if needed)
4. **Token Exchange** → Receives JWT token from Keycloak
5. **API Request** → kubectl sends request with Bearer token
6. **RBAC Check** → Kubernetes validates token and checks permissions
7. **Response** → Command executed with proper authorization

## 🛠️ Development

### Repository Structure

```
ITLAuth/
├── README.md                    # This file - main documentation
├── docs/
│   ├── guides/                  # User guides and tutorials
│   │   ├── INSTALLATION.md      # Installation instructions
│   │   ├── APISERVER-OIDC-SETUP.md  # API server configuration
│   │   ├── TROUBLESHOOTING.md   # Common issues and solutions
│   │   └── SERVICE-ACCOUNTS.md  # Service account management
│   ├── scripts/                 # Automation scripts
│   │   ├── setup_kubectl_oidc.py    # Main Python setup script
│   │   ├── Setup-KubectlOIDC.ps1    # PowerShell setup script
│   │   ├── configure-apiserver-oidc.sh  # API server config script
│   │   ├── keycloak_sa_manager.py   # Service account manager
│   │   └── persistent_token_manager.py  # Token management
│   └── examples/                # Configuration examples
│       ├── kubeconfig-examples/
│       ├── rbac-examples/
│       └── keycloak-examples/
├── src/                        # Source code (if package)
└── tests/                      # Test files
```

### Local Development

```bash
# Clone the repository
git clone https://github.com/ITlusions/ITLAuth.git
cd ITLAuth

# Install in development mode (if Python package)
pip install -e .

# Run the tools directly
python docs/scripts/setup_kubectl_oidc.py
```

## 🔧 Troubleshooting

### Quick Fixes

**kubectl not found after installation**
- Restart your terminal/shell
- Check your PATH environment variable
- See [Installation Guide](docs/guides/INSTALLATION.md) for detailed steps

**Authentication browser doesn't open**
- Manually copy the URL from terminal output
- Check your default browser settings
- See [Troubleshooting Guide](docs/guides/TROUBLESHOOTING.md)

**Permission denied errors**
- On Windows: Run as Administrator if needed
- On macOS/Linux: Check file permissions
- Review security settings

### Getting Help

1. Check the [Documentation](docs/) for detailed guides
2. Review the [Troubleshooting Guide](docs/guides/TROUBLESHOOTING.md)
3. Run scripts with `--verbose` flag for detailed logging
4. Open an issue on [GitHub](https://github.com/ITlusions/ITLAuth/issues)

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Submit a pull request

### Development Guidelines
- Follow existing code style
- Add tests for new features
- Update documentation
- Test on multiple platforms when possible

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🏢 About ITlusions

ITLAuth is developed and maintained by ITlusions. This suite provides enterprise-grade OIDC authentication for Kubernetes environments.

For more information about our services and infrastructure, visit [www.itlusions.com](https://www.itlusions.com).

## 🔗 Related Projects

- **[ITL.K8s](https://github.com/ITlusions/ITL.K8s)** - Kubernetes cluster configuration and management
- **[ITL.Keycloak.Tenants](https://github.com/ITlusions/ITL.Keycloack.Tenants)** - Multi-tenant Keycloak management
- **[ITL.ArgoCD](https://github.com/ITlusions/ITL.ArgoCD)** - GitOps continuous deployment
- **[ITL.Istio](https://github.com/ITlusions/ITL.Istio)** - Service mesh configuration
- **[ITL.Prometheus](https://github.com/ITlusions/ITL.Prometheus)** - Monitoring and observability

## 🚀 Quick Links

- **[Get Started](docs/guides/INSTALLATION.md)** - Installation and setup
- **[API Server Setup](docs/guides/APISERVER-OIDC-SETUP.md)** - Configure your cluster
- **[Scripts](docs/scripts/)** - Automation tools
- **[Examples](docs/examples/)** - Configuration examples
- **[Troubleshooting](docs/guides/TROUBLESHOOTING.md)** - Common issues

---

Made with ❤️ by [ITlusions](https://www.itlusions.com) for the Kubernetes community