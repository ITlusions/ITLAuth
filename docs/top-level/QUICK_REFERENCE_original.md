````markdown
# ITL CLI - Quick Reference

## Installation

```bash
cd ITLAuth
pip install -e .
```

## Authentication

```bash
# Login with Keycloak
itlc login

# Check current user
itlc whoami

# Logout
itlc logout
```

## Subscriptions

```bash
# Create (server auto-generates subscription_id)
itlc resource subscription create --name my-sub --display-name "My Sub"

# List all
itlc resource subscription list

# Get details
itlc resource subscription get my-sub

# Delete
itlc resource subscription delete my-sub --force
```

---

Made by ITlusions

````
