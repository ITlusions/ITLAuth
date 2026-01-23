# Quick Start - ITLAuth

## Install (One Command)

**Linux/macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/ITlusions/ITLAuth/main/install.sh | bash
```

**Windows:**
```powershell
iwr -useb https://raw.githubusercontent.com/ITlusions/ITLAuth/main/install.ps1 | iex
```

## Setup

```bash
itl-kubectl-oidc-setup

# Or Python-only (skip binary installation)
itl-kubectl-oidc-setup --python-only
```

Installs kubectl, configures OIDC. Default: 4 contexts. Python-only: 2 contexts.

## Use

**Python auth** (recommended):
```bash
kubectl --context=itl-python get pods
```

**Binary auth** (alternative):
```bash
kubectl --context=itl get pods
```

Browser opens → Login via EntraID/GitHub/password → Token cached → Done!

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Command not found | Restart terminal |
| Port 8000 in use | Use `--context=itl` (binary) |
| Python not found | Install Python 3.6+ |
| Need help | [Full Guide](docs/guides/INSTALLATION.md) |

---

Made by [ITlusions](https://www.itlusions.com)
