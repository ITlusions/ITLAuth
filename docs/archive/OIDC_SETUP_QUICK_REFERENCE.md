# Quick Reference: itlc oidc-setup Commands

## Installation & Usage

After installing `itl-auth`:
```bash
pip install itl-auth
```

All OIDC setup commands are accessed via:
```bash
itlc oidc-setup <command> [options]
```

## Available Commands

### 1. **full** - Complete OIDC Setup (Recommended)
Sets up kubectl, kubelogin, and OIDC authentication in one command.

```bash
itlc oidc-setup full

# With options
itlc oidc-setup full --cluster my-cluster --no-test --python-only
```

**When to use:** First time setup or full environment reset

---

### 2. **check** - Verify Setup Status
Checks if kubectl and kubelogin are properly installed.

```bash
itlc oidc-setup check
```

**Output:**
```
✓ kubectl is installed and accessible
✓ kubelogin plugin is installed
✓ OIDC setup is complete and ready to use
```

---

### 3. **configure** - Setup OIDC for a Cluster
Configures OIDC authentication for a specific Kubernetes cluster context.

```bash
itlc oidc-setup configure --cluster my-cluster
```

**When to use:** After kubectl and kubelogin are installed, or to reconfigure

---

### 4. **test** - Test Authentication
Verifies that OIDC authentication is working with Keycloak.

```bash
itlc oidc-setup test
```

**When to use:** Verify authentication after setup, troubleshooting

---

### 5. **token** - Get Fresh OIDC Token
Requests a new OIDC token from Keycloak for kubectl authentication.

```bash
itlc oidc-setup token
```

**When to use:** Manual token refresh, testing OIDC flow

---

### 6. **install-kubectl** - Install kubectl Binary
Downloads and installs kubectl for your operating system.

```bash
itlc oidc-setup install-kubectl
```

**Supports:**
- Windows (winget or manual download)
- macOS (homebrew or manual)
- Linux (apt, snap, or manual)

---

### 7. **install-kubelogin** - Install kubelogin Plugin
Downloads and installs the kubelogin OIDC authentication plugin.

```bash
itlc oidc-setup install-kubelogin
```

**Installation methods (in order):**
1. `kubectl krew` plugin manager
2. Manual binary download from GitHub releases

---

## Integration with Server Onboarding

Complete cluster onboarding in two steps:

```bash
# Step 1: Register cluster
itlc onboard cluster --name my-cluster

# Step 2: Setup OIDC
itlc oidc-setup full
```

Or all-in-one:
```bash
itlc onboard complete --cluster-name my-cluster
```

---

## Common Workflows

### First-Time Setup
```bash
itlc oidc-setup full
itlc oidc-setup test
```

### Check Installation
```bash
itlc oidc-setup check
```

### Refresh Token
```bash
itlc oidc-setup token
```

### Reconfigure Cluster
```bash
itlc oidc-setup configure --cluster my-cluster
```

### Troubleshoot Authentication
```bash
itlc oidc-setup check        # Check status
itlc oidc-setup test         # Test flow
itlc oidc-setup token        # Get token
```

---

## Migration from Old Command

### Before
```bash
python3 -m itl_kubectl_oidc_setup
```

### After
```bash
itlc oidc-setup full
```

### Before (with options)
```bash
python3 -m itl_kubectl_oidc_setup --cluster my-cluster --no-test
```

### After (with options)
```bash
itlc oidc-setup full --cluster my-cluster --no-test
```

---

## Options Reference

### `full` Command Options
```
--cluster TEXT              Kubernetes cluster context
--download-config           Download cluster config from API
--config-url TEXT           Custom cluster config URL
--no-test                   Skip authentication test
--python-only               Use Python auth only (no kubelogin)
```

### `configure` Command Options
```
--cluster TEXT              Cluster context (will prompt if not provided)
```

---

## Help & Support

Get help for any command:

```bash
# General help
itlc oidc-setup --help

# Specific command help
itlc oidc-setup full --help
itlc oidc-setup check --help
itlc oidc-setup token --help
```

---

## File Locations

- **Configuration:** `~/.kube/config`
- **Cached Tokens:** `~/.kube/cache/oidc/itlusions_token.json`
- **Plugins:** `~/.kubectl/plugins/kubectl-oidc_login`
- **Setup Tokens:** `~/.itl/onboarding/`

---

## Platform Support

- ✅ Windows 10/11
- ✅ macOS (Intel & Apple Silicon)
- ✅ Linux (Ubuntu, Debian, Fedora, etc.)

---

## Troubleshooting

### kubectl not found
```bash
itlc oidc-setup install-kubectl
```

### kubelogin not installed
```bash
itlc oidc-setup install-kubelogin
```

### Check current status
```bash
itlc oidc-setup check
```

### Authentication failing
```bash
itlc oidc-setup token         # Test token generation
itlc oidc-setup test          # Test full auth flow
```

---

**Last Updated:** February 1, 2026  
**Version:** itlc 1.0.0+
