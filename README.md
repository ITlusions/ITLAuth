# itl-kubectl-oidc-setup

🚀 **Automated kubectl OIDC setup tool for ITlusions Kubernetes clusters**

A command-line tool that automatically installs and configures kubectl with OIDC authentication for ITlusions Kubernetes clusters using Keycloak. No more manual configuration steps!

## ✨ Features

- 🔧 **Automatic kubectl installation** (if not already installed)
- 🔌 **kubelogin plugin installation** via krew or direct download
- 🔐 **OIDC configuration** for ITlusions Keycloak authentication
- 🌍 **Cross-platform support** (Windows, macOS, Linux)
- 🎯 **Interactive setup** with colored terminal output
- ✅ **Authentication testing** to verify configuration
- 📋 **Smart detection** of existing installations

## 🚀 Quick Start

### Installation

```bash
pip install itl-kubectl-oidc-setup
```

### Usage

Simply run the tool and follow the interactive prompts:

```bash
itl-kubectl-oidc-setup
```

### Advanced Usage

```bash
# Specify a custom cluster name
itl-kubectl-oidc-setup --cluster my-cluster

# Skip authentication testing
itl-kubectl-oidc-setup --no-test

# Use custom Keycloak URL
itl-kubectl-oidc-setup --keycloak-url https://auth.example.com

# Help
itl-kubectl-oidc-setup --help
```

## 📋 Prerequisites

- Python 3.8 or higher
- Internet connection for downloading kubectl/kubelogin (if needed)
- Access to ITlusions Kubernetes cluster

## 🔧 What It Does

1. **Detects your operating system** and architecture
2. **Checks for kubectl** and installs it if missing:
   - Windows: Uses `winget`
   - macOS: Uses `homebrew`
   - Linux: Downloads from official Kubernetes releases
3. **Installs kubelogin plugin**:
   - First tries `krew` (if available)
   - Falls back to direct download
4. **Configures OIDC authentication** with ITlusions Keycloak:
   - Sets up cluster configuration
   - Configures user authentication
   - Sets context and namespace
5. **Tests authentication** to ensure everything works
6. **Provides next steps** and usage instructions

## 🏗️ Configuration

The tool configures kubectl with the following OIDC settings:

- **Issuer URL**: `https://sts.itlusions.com/realms/itlusions`
- **Client ID**: `kubernetes-oidc`
- **Username Claim**: `preferred_username`
- **Groups Claim**: `groups`

## 🔐 Authentication Flow

1. Run `kubectl get pods` (or any kubectl command)
2. Browser opens automatically for authentication
3. Login with your ITlusions credentials
4. Return to terminal - you're authenticated!

## 🛠️ Development

### Local Development

```bash
# Clone the repository
git clone https://github.com/ITlusions/itl-kubectl-oidc-setup.git
cd itl-kubectl-oidc-setup

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e .[dev]

# Run the tool
itl-kubectl-oidc-setup
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black kubectl_oidc_setup/
flake8 kubectl_oidc_setup/
```

## 📁 Project Structure

```
itl-kubectl-oidc-setup/
├── itl_kubectl_oidc_setup/
│   ├── __init__.py          # Package metadata and exports
│   └── __main__.py          # Main application logic
├── setup.py                 # Package installation configuration
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── LICENSE                 # MIT License
```

## 🔧 Troubleshooting

### Common Issues

**kubectl not found after installation**
- Restart your terminal/shell
- Check your PATH environment variable

**kubelogin plugin fails to install**
- The tool will try multiple installation methods
- Check if you have proper permissions

**Authentication browser doesn't open**
- Manually copy the URL from terminal output
- Check your default browser settings

**Permission denied errors**
- On Windows: Run as Administrator if needed
- On macOS/Linux: Check file permissions

### Getting Help

1. Check the terminal output for detailed error messages
2. Run with `--verbose` flag for more detailed logging
3. Open an issue on [GitHub](https://github.com/ITlusions/itl-kubectl-oidc-setup/issues)

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🏢 About ITlusions

This tool is developed and maintained by ITlusions. For more information about our services and infrastructure, visit [www.itlusions.com](https://www.itlusions.com).

## 🔗 Related Projects

- [ITL.K8s](https://github.com/ITlusions/ITL.K8s) - Kubernetes cluster configuration
- [ITL.Keycloack.Tenants](https://github.com/ITlusions/ITL.Keycloack.Tenants) - Keycloak tenant management
- [ITL.ArgoCD](https://github.com/ITlusions/ITL.ArgoCD) - ArgoCD configuration and applications

---

Made with ❤️ by [ITlusions](https://www.itlusions.com)