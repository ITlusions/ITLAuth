# ITLAuth - ITlusions Authentication Suite

**Complete authentication solution for ITlusions Kubernetes clusters**

ITLAuth provides automated tools and comprehensive guides for setting up OIDC authentication with ITlusions Kubernetes clusters using Keycloak. This suite includes automated setup tools, API server configuration scripts, service account management utilities, and a native Python authentication module.

[![PyPI version](https://badge.fury.io/py/itl-kubectl-oidc-setup.svg)](https://badge.fury.io/py/itl-kubectl-oidc-setup)
[![Python Support](https://img.shields.io/pypi/pyversions/itl-kubectl-oidc-setup.svg)](https://pypi.org/project/itl-kubectl-oidc-setup/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Zero-click installation** - One command to get started
- **Dual authentication** - Binary (kubelogin) or Python (native) modes
- **PKCE OAuth2 flow** - Enhanced security with local callback server
- **Token caching** - Automatic refresh, no repeated logins
- **Offline capable** - Embedded fallback configuration
- **Cross-platform** - Windows, macOS, Linux
- **Four contexts** - Direct and SSH tunnel for each auth mode

## Zero-Click Installation

Get started instantly with our zero-click installers:

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/ITlusions/ITLAuth/main/install.sh | bash
```

Or using wget:
```bash
wget -qO- https://raw.githubusercontent.com/ITlusions/ITLAuth/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
iwr -useb https://raw.githubusercontent.com/ITlusions/ITLAuth/main/install.ps1 | iex
```

Or the long form:
```powershell
Invoke-WebRequest -Uri https://raw.githubusercontent.com/ITlusions/ITLAuth/main/install.ps1 -UseBasicParsing | Invoke-Expression
```

## Alternative Installation Methods

### Option 1: Python Package (pip)

```bash
pip install itl-kubectl-oidc-setup
itl-kubectl-oidc-setup

# Python auth only (skip kubelogin binary)
itl-kubectl-oidc-setup --python-only
```

### Option 2: From Source

```bash
git clone https://github.com/ITlusions/ITLAuth.git
cd ITLAuth
pip install .
itl-kubectl-oidc-setup
```

## Documentation

### Getting Started
- **[Quick Start Guide](QUICKSTART.md)** - Get up and running in 2 minutes
- **[Installation Guide](docs/guides/INSTALLATION.md)** - Complete installation and setup instructions
- **[Cluster Config Solution](CLUSTER-CONFIG-SOLUTION.md)** - Configuration distribution architecture
- **[PyPI Checklist](PYPI_CHECKLIST.md)** - Package publication readiness guide

### User Guides
- **[API Server Setup](docs/guides/APISERVER-OIDC-SETUP.md)** - Configure Kubernetes API server for OIDC
- **[Troubleshooting Guide](docs/guides/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Service Account Management](docs/guides/SERVICE-ACCOUNTS.md)** - Keycloak service account setup

### Scripts and Tools
- **[Setup Scripts](docs/scripts/)** - Automated setup and configuration scripts
- **[PowerShell Modules](docs/scripts/)** - Windows-specific PowerShell tools
- **[Python Utilities](docs/scripts/)** - Cross-platform Python tools
- **[Bash Scripts](docs/scripts/)** - Linux/macOS shell scripts

### Configuration Examples
- **[kubeconfig Examples](docs/examples/)** - Sample kubeconfig files
- **[RBAC Configurations](docs/examples/)** - Role-based access control examples
- **[Keycloak Client Setup](docs/examples/)** - Keycloak client configuration

## How It Works

kubectl → Python/Binary Auth Plugin → Token Cache Check → Browser Login (if needed) → Keycloak OIDC → Token → Kubernetes API

**Authentication Modes**:
- **Python** (`itl-python`, `itl-ssh-tunnel-python`) - Pure Python, PKCE flow, port 8000 callback
- **Binary** (`itl`, `itl-ssh-tunnel`) - kubelogin executable, traditional flow

**Setup Flow**: Run tool → Try API download → Fallback to embedded config → Configure 4 contexts → Test authentication

## Development

```bash
git clone https://github.com/ITlusions/ITLAuth.git
cd ITLAuth
pip install -e .
itl-kubectl-oidc-setup

# Test Python auth module
python -m itl_kubectl_oidc_setup.auth
```

See [CLUSTER-CONFIG-SOLUTION.md](CLUSTER-CONFIG-SOLUTION.md) for API deployment.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| kubectl not found | Restart terminal or check PATH |
| Port 8000 in use | Use binary auth: `kubectl --context=itl` |
| Python import error | `pip install --force-reinstall itl-kubectl-oidc-setup` |
| Browser doesn't open | Copy URL from terminal manually |
| API unavailable | Tool auto-uses embedded fallback |

See [Full Troubleshooting Guide](docs/guides/TROUBLESHOOTING.md) or [open an issue](https://github.com/ITlusions/ITLAuth/issues).

## Authentication Methods

**Python** (Recommended): `kubectl --context=itl-python get pods`
- Pure Python, no binaries
- PKCE flow on port 8000
- Requires Python 3.6+

**Binary**: `kubectl --context=itl get pods`
- Mature kubelogin implementation
- Platform-specific executable
- Widely used in community

Both authenticate via Keycloak (EntraID/GitHub/password). Use SSH tunnel contexts for remote access.

## Contributing

Fork → Create branch → Make changes → Update docs → Submit PR

Guidelines: Follow existing style, add tests, test cross-platform, no emojis in docs.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Links

[Installation](docs/guides/INSTALLATION.md) • [API Server Setup](docs/guides/APISERVER-OIDC-SETUP.md) • [Troubleshooting](docs/guides/TROUBLESHOOTING.md) • [Python Auth](itl_kubectl_oidc_setup/auth.py) • [Scripts](docs/scripts/) • [Examples](docs/examples/)

---

Made by [ITlusions](https://www.itlusions.com)
