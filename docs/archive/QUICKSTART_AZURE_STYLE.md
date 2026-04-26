# ITL Token CLI - Azure-Style Quick Start

Get started with Azure CLI-style authentication in 60 seconds!

## Prerequisites

```bash
pip install itl-kubectl-oidc-setup
```

## Method 1: Interactive Login (Recommended)

Perfect for developers and interactive use.

```bash
# 1. Login with browser (like 'az login')
itlc login

# 2. Check who you are
itlc whoami

# 3. Get token
TOKEN=$(itlc get-token --output=token)

# 4. Use it!
curl -H "Authorization: Bearer $TOKEN" https://api.example.com
```

**That's it!** Token is cached, auto-refreshes, works all day.

### Multi-Realm Setup

```bash
# List available realms
itlc realm list

# Switch realm (like 'az account set')
itlc realm set production

# Show current realm
itlc realm show

# Logout when done
itlc logout
```

## Method 2: Service Account (CI/CD)

Perfect for automation and pipelines.

```bash
# 1. Set credentials
export KEYCLOAK_CLIENT_ID=my-service-account
export KEYCLOAK_CLIENT_SECRET=secret

# 2. Get token
TOKEN=$(itlc get-token --output=token)

# 3. Use it!
curl -H "Authorization: Bearer $TOKEN" https://api.example.com
```

## Command Cheat Sheet

| Task | Command |
|------|---------|
| Login | `itlc login` |
| Who am I? | `itlc whoami` |
| Get token | `itlc get-token --output=token` |
| List realms | `itlc realm list` |
| Switch realm | `itlc realm set <name>` |
| Show realm | `itlc realm show` |
| Logout | `itlc logout` |
| Help | `itlc --help` |

## Azure CLI Comparison

| Azure CLI | ITL Token CLI |
|-----------|---------------|
| `az login` | `itlc login` |
| `az account list` | `itlc realm list` |
| `az account set` | `itlc realm set` |
| `az account show` | `itlc whoami` |
| `az logout` | `itlc logout` |

## Common Workflows

### Developer Daily Workflow

```bash
# Morning
itlc login           # Opens browser once

# All day
itlc get-token       # Works without re-login
itlc get-token       # Still works
itlc get-token       # Auto-refreshes if needed

# Evening
itlc logout          # Optional cleanup
```

### CI/CD Workflow

```yaml
# GitHub Actions
- name: Authenticate
  run: |
    TOKEN=$(itlc get-token \
      --client-id=${{ secrets.CLIENT_ID }} \
      --client-secret=${{ secrets.CLIENT_SECRET }} \
      --output=token)
    echo "::add-mask::$TOKEN"
    echo "API_TOKEN=$TOKEN" >> $GITHUB_ENV

- name: Deploy
  run: |
    curl -H "Authorization: Bearer $API_TOKEN" \
      https://api.example.com/deploy
```

### Multi-Environment Workflow

```bash
# Development
itlc login --realm=development
itlc get-token --output=token

# Production (switch context)
itlc realm set production
itlc get-token --output=token
```

## Troubleshooting

**Browser doesn't open?**
```bash
# Copy URL from terminal and open manually
```

**Port 8765 in use?**
```bash
# Windows: netstat -ano | findstr :8765
# Linux: lsof -i :8765
# Kill the process and retry
```

**Not logged in?**
```bash
itlc login
```

**Token expired?**
```bash
# Auto-refreshes, but if issues:
itlc logout
itlc login
```

## Next Steps

- 📖 [Full Interactive Login Guide](docs/INTERACTIVE_LOGIN.md)
- 📖 [Token CLI Documentation](src/itlc/README.md)
- 📖 [Integration Examples](docs/TOKEN_CLI_INTEGRATION.md)

## Links

- [Main README](README.md)
- [Quick Reference](QUICKREF_TOKEN_CLI.md)

---

**Get Started Now**: `itlc login` 🚀
