# ITL Token CLI - Quick Reference

## Installation

```bash
pip install itl-kubectl-oidc-setup
```

## Environment Setup

```bash
export KEYCLOAK_CLIENT_ID=your-service-account
export KEYCLOAK_CLIENT_SECRET=your-secret
export KEYCLOAK_URL=https://sts.itlusions.com  # Optional
export KEYCLOAK_REALM=itlusions                # Optional
```

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `itlc get-token` | Get access token | `itlc get-token --output=token` |
| `itlc config` | Show configuration | `itlc config` |
| `itlc cache-list` | List cached tokens | `itlc cache-list` |
| `itlc clear-cache --all` | Clear cache | `itlc clear-cache --all` |
| `itlc inspect <token>` | Inspect JWT | `itlc inspect $TOKEN --decode` |
| `itlc introspect <token>` | Validate token | `itlc introspect $TOKEN` |

## Output Formats

```bash
# Token only (for scripts)
itlc get-token --output=token

# JSON format (for parsing)
itlc get-token --output=json

# Table format (human-readable)
itlc get-token --output=table
```

## Common Use Cases

### 1. Shell Script

```bash
#!/bin/bash
TOKEN=$(itlc get-token --output=token)
curl -H "Authorization: Bearer $TOKEN" https://api.example.com/data
```

### 2. PowerShell Script

```powershell
$TOKEN = itlc get-token --output=token
Invoke-RestMethod -Uri "https://api.example.com/data" `
  -Headers @{Authorization = "Bearer $TOKEN"}
```

### 3. CI/CD Pipeline

```yaml
# GitHub Actions
- run: |
    TOKEN=$(itlc get-token --output=token)
    echo "::add-mask::$TOKEN"
    echo "API_TOKEN=$TOKEN" >> $GITHUB_ENV
```

### 4. Docker Container

```dockerfile
FROM python:3.11
RUN pip install itl-kubectl-oidc-setup
ENV KEYCLOAK_CLIENT_ID=my-app
ENV KEYCLOAK_CLIENT_SECRET=secret
CMD ["sh", "-c", "TOKEN=$(itlc get-token --output=token) && echo $TOKEN"]
```

### 5. Kubernetes Job

```yaml
containers:
- name: job
  image: python:3.11
  command: [sh, -c]
  args:
    - pip install itl-kubectl-oidc-setup && 
      TOKEN=$(itlc get-token --output=token) &&
      curl -H "Authorization: Bearer $TOKEN" https://api.example.com
  envFrom:
  - secretRef:
      name: keycloak-credentials
```

## Cache Location

- **Windows**: `C:\Users\<user>\.itl\token-cache\`
- **Linux/Mac**: `~/.itl/token-cache/`

## Troubleshooting

```bash
# Check installation
itlc --version

# Verify configuration
itlc config

# Clear cache and retry
itlc clear-cache --all
itlc get-token

# Debug mode (verbose output)
itlc get-token --output=json
```

## Quick Test

```bash
# 1. Set credentials
export KEYCLOAK_CLIENT_ID=test-app
export KEYCLOAK_CLIENT_SECRET=test-secret

# 2. Get token
TOKEN=$(itlc get-token --output=token)

# 3. Inspect token
itlc inspect $TOKEN --decode

# 4. Validate token
itlc introspect $TOKEN
```

## Integration with ITL Services

| Service | Command |
|---------|---------|
| Generate service account | Web UI: https://www.itlusions.nl/api-tokens |
| Get access token | `itlc get-token` |
| Use token | `curl -H "Authorization: Bearer $TOKEN" <URL>` |

## Links

- [Full Documentation](docs/TOKEN_CLI_INTEGRATION.md)
- [CLI README](src/itl_token_cli/README.md)
- [ITLAuth Main](README.md)
