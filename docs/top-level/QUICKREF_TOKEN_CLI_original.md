````markdown
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

---

Made by ITlusions

````
