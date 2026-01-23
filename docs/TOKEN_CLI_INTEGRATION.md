# ITL Token CLI Integration Guide

The **ITL Token CLI** (`itlc`) has been successfully integrated into the ITLAuth project!

## Installation

The CLI is automatically installed when you install ITLAuth:

```bash
# Install ITLAuth with token CLI
cd d:\repos\ITLAuth
pip install -e .

# Verify installation
itlc --version
itlc --help
```

## What Was Added

### New Package: `src/itlc/`

```
src/itlc/
├── __init__.py           # Package exports
├── __main__.py           # CLI entry point (342 lines)
├── keycloak_client.py    # Keycloak client (120 lines)
├── token_cache.py        # Token caching (127 lines)
└── README.md             # Usage documentation
```

### Updated Files

1. **setup.py**
   - Added `click>=8.0.0` dependency
   - Added `itlc` console script entry point

2. **pyproject.toml**
   - Added `click>=8.0.0` to dependencies
   - Added `itlc` to project.scripts
   - Updated package discovery

3. **requirements.txt**
   - Added `click>=8.0.0`

4. **README.md**
   - Added token CLI to features list
   - Added new section documenting CLI usage

5. **New Files**
   - `test_token_cli.py` - Installation verification script

## Available Commands

```bash
# Get access token
itlc get-token --client-id=<id> --client-secret=<secret>

# Show configuration
itlc config

# List cached tokens
itlc cache-list

# Clear cache
itlc clear-cache --all

# Inspect JWT token
itlc inspect <token> --decode

# Introspect token (validate with Keycloak)
itlc introspect <token>
```

## Environment Variables

Set these for automatic credential discovery:

```powershell
# Keycloak configuration
$env:KEYCLOAK_URL = "https://sts.itlusions.com"
$env:KEYCLOAK_REALM = "itlusions"

# Service account credentials
$env:KEYCLOAK_CLIENT_ID = "your-service-account"
$env:KEYCLOAK_CLIENT_SECRET = "your-secret"

# Alternative names also supported
$env:ITL_CLIENT_ID = "your-service-account"
$env:ITL_CLIENT_SECRET = "your-secret"
```

## Token Cache

Tokens are cached at:
- **Windows**: `C:\Users\<username>\.itl\token-cache\`
- **Linux/Mac**: `~/.itl/token-cache/`

Cache files use MD5-hashed filenames for security.

## Integration with ITL Website

The CLI tool complements the ITL website token generation:

1. **Web UI** (https://www.itlusions.nl/api-tokens):
   - Generate service accounts via web interface
   - Visual token management
   - Revoke tokens via dashboard

2. **CLI** (`itlc`):
   - Get access tokens using service account credentials
   - Inspect and introspect tokens
   - Manage token cache
   - CI/CD automation

## Usage Examples

### Basic Token Acquisition

```bash
# Set credentials
export KEYCLOAK_CLIENT_ID=my-service-account
export KEYCLOAK_CLIENT_SECRET=my-secret

# Get token (cached for future use)
TOKEN=$(itlc get-token --output=token)

# Use token
curl -H "Authorization: Bearer $TOKEN" https://api.example.com/data
```

### CI/CD Pipeline

```yaml
# GitHub Actions example
- name: Get API Token
  run: |
    TOKEN=$(itlc get-token \
      --client-id=${{ secrets.KEYCLOAK_CLIENT_ID }} \
      --client-secret=${{ secrets.KEYCLOAK_CLIENT_SECRET }} \
      --output=token)
    echo "::add-mask::$TOKEN"
    echo "API_TOKEN=$TOKEN" >> $GITHUB_ENV

- name: Call API
  run: |
    curl -H "Authorization: Bearer $API_TOKEN" \
      https://api.example.com/deploy
```

### Kubernetes Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: api-job
spec:
  template:
    spec:
      containers:
      - name: job
        image: python:3.11
        command:
          - sh
          - -c
          - |
            pip install itl-kubectl-oidc-setup
            TOKEN=$(itlc get-token --output=token)
            curl -H "Authorization: Bearer $TOKEN" https://api.example.com/data
        env:
        - name: KEYCLOAK_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: keycloak-credentials
              key: client-id
        - name: KEYCLOAK_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: keycloak-credentials
              key: client-secret
```

## Testing

Run the test script to verify installation:

```bash
cd d:\repos\ITLAuth
python test_token_cli.py
```

Expected output:
```
============================================================
ITL Token Manager CLI - Installation Test
============================================================
[✓] CLI installed: itlc, version 1.0.0
[✓] Help command works
[✓] Config command works
[✓] Cache-list command works
[✓] Python imports work
============================================================
Results: 5 passed, 0 failed
============================================================
```

## Comparison with Azure kubelogin

| Feature | Azure kubelogin | ITL Token CLI |
|---------|----------------|---------------|
| Get token | ✅ | ✅ |
| Token cache | ✅ | ✅ |
| Env variables | ✅ | ✅ |
| JWT inspection | ❌ | ✅ |
| Token introspection | ❌ | ✅ |
| Cache management | ❌ | ✅ |
| Device code flow | ✅ | ⏳ Planned |
| Workload identity | ✅ | ⏳ Planned |

## Future Enhancements

1. **Device Code Flow**: Headless authentication for interactive use
2. **Workload Identity**: Kubernetes ServiceAccount → Keycloak mapping
3. **Token Rotation**: Automatic refresh before expiry
4. **Batch Operations**: Manage multiple service accounts
5. **Multi-Tenant Support**: Switch between Keycloak realms

## Architecture

```
itlc CLI
│
├─ keycloak_client.py
│  └─ KeycloakClient
│     ├─ get_access_token()
│     ├─ introspect_token()
│     └─ get_credentials_from_env()
│
├─ token_cache.py
│  └─ TokenCache
│     ├─ save_token()
│     ├─ get_token()
│     ├─ delete_token()
│     └─ list_cached()
│
└─ __main__.py (CLI)
   ├─ get-token: Acquire tokens
   ├─ inspect: Decode JWT
   ├─ introspect: Validate with Keycloak
   ├─ cache-list: Show cached tokens
   ├─ clear-cache: Remove cache
   └─ config: Show configuration
```

## Troubleshooting

### Command Not Found

```bash
# Reinstall package
cd d:\repos\ITLAuth
pip install --force-reinstall -e .

# Verify PATH
which itlc  # Linux/Mac
where itlc  # Windows
```

### Import Errors

```bash
# Verify installation
pip list | grep itl-kubectl-oidc-setup

# Reinstall dependencies
pip install -r requirements.txt
```

### Token Acquisition Fails

```bash
# Check configuration
itlc config

# Test manually
itlc get-token \
  --client-id=test \
  --client-secret=test \
  --keycloak-url=https://sts.itlusions.com \
  --realm=itlusions \
  --output=json
```

### Cache Issues

```bash
# Clear all cache
itlc clear-cache --all

# Check cache location
ls ~/.itl/token-cache/  # Linux/Mac
dir %USERPROFILE%\.itl\token-cache\  # Windows
```

## Contributing

To add new commands:

1. Add command function to `__main__.py`
2. Use `@cli.command()` decorator
3. Add Click options/arguments
4. Update README.md with usage examples
5. Test installation: `pip install -e .`

## Links

- [Token CLI README](src/itl_token_cli/README.md)
- [ITLAuth Main README](README.md)
- [Keycloak API Tokens Documentation](../itl.website/docs/KEYCLOAK_API_TOKENS.md)

---

Made by [ITlusions](https://www.itlusions.com)
