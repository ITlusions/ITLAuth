# Quick Start Guide - ITLAuth

Get ITLAuth up and running in under 2 minutes!

## 🚀 One-Command Installation

### Linux / macOS

Open your terminal and run:

```bash
curl -fsSL https://raw.githubusercontent.com/ITlusions/ITLAuth/main/install.sh | bash
```

### Windows

Open PowerShell and run:

```powershell
iwr -useb https://raw.githubusercontent.com/ITlusions/ITLAuth/main/install.ps1 | iex
```

## ✓ What Happens Next

The installer will:

1. ✅ Check your Python installation (3.8+ required)
2. ✅ Install pip if needed
3. ✅ Install the `itl-kubectl-oidc-setup` package
4. ✅ Verify everything is working

## 🎯 First Run

After installation completes, run:

```bash
itl-kubectl-oidc-setup
```

This will:
- Install `kubectl` (if not present)
- Install `kubelogin` plugin
- Configure OIDC authentication
- Test your connection

## 🔐 Authentication

When you run kubectl commands, you'll be prompted to authenticate via your browser with one of:

- **EntraID - ITlusions** (Azure AD SSO)
- **Github - ITlusions** (GitHub SSO)
- Username/password

## 📚 Next Steps

Once set up, you can use kubectl normally:

```bash
kubectl get pods
kubectl get nodes
kubectl describe deployment myapp
```

## ❓ Troubleshooting

### Command not found

**Linux/macOS:**
```bash
export PATH="$HOME/.local/bin:$PATH"
# Add to ~/.bashrc or ~/.zshrc for permanent
```

**Windows:**
Restart PowerShell to refresh PATH

### Python not found

Install Python 3.8 or higher:
- **Linux:** `sudo apt install python3 python3-pip`
- **macOS:** `brew install python3`
- **Windows:** Download from [python.org](https://www.python.org/downloads/)

### Need more help?

- 📖 [Full Installation Guide](docs/guides/INSTALLATION.md)
- 🐛 [Troubleshooting Guide](docs/guides/TROUBLESHOOTING.md)
- 💬 [GitHub Issues](https://github.com/ITlusions/ITLAuth/issues)

## 📋 Manual Installation

If you prefer manual installation:

```bash
pip install itl-kubectl-oidc-setup
itl-kubectl-oidc-setup
```

---

**Made with ❤️ by [ITlusions](https://www.itlusions.com)**
