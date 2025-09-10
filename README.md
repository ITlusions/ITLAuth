# itl-k8s-oidc

**One-command setup: Kubernetes OIDC via Keycloak + kubelogin (auto-installs krew + oidc-login)**

## What it does

The `itl-k8s-oidc` package provides a CLI tool `itl-oidc-setup` that automates the entire setup process for Kubernetes authentication via Keycloak OIDC. It handles:

1. **Dependency checking**: Verifies kubectl is available
2. **Automatic installation**: Downloads and installs krew (kubectl plugin manager) if needed
3. **Plugin installation**: Installs the `oidc-login` plugin via krew
4. **OIDC configuration**: Runs `kubectl oidc-login setup` with proper parameters
5. **Optional verification**: Tests authentication with `kubectl auth whoami`

## How it works

The tool uses a **public OIDC client with PKCE** for secure authentication. It supports both interactive browser-based auth and **device code flow** for headless environments.

Configuration follows a clear precedence order:
1. **CLI arguments** (highest priority)
2. **Environment variables** (`ITL_OIDC_ISSUER_URL`, etc.)
3. **Configuration file** (`~/.config/itl-k8s-oidc/config.json`)
4. **Baked defaults** (lowest priority)

## Installation

```bash
pip install itl-k8s-oidc
```

## Usage Examples

### Minimal setup
Uses the baked-in default issuer for ITlusions realm:

```bash
itl-oidc-setup --verify
```

### Custom issuer
Override the default issuer:

```bash
itl-oidc-setup --issuer-url https://your-keycloak.example.com/realms/yourrealm
```

### Device code flow
For headless environments or when browser auth isn't available:

```bash
itl-oidc-setup --device-code
```

### Enterprise setup
With custom CA certificate and kubeconfig:

```bash
itl-oidc-setup --ca-file /path/to/ca.crt --kubeconfig ~/.kube/prod-config --verify
```

### Save as defaults
Persist your configuration for future use:

```bash
itl-oidc-setup --issuer-url https://sso.itlusions.com/realms/itlusions --save-default
```

## Configuration

### Environment Variables

```bash
export ITL_OIDC_ISSUER_URL="https://your-keycloak.example.com/realms/yourrealm"
export ITL_OIDC_CLIENT_ID="custom-client"
export ITL_OIDC_SCOPES="openid,profile,email,groups"
itl-oidc-setup
```

### Configuration File

The tool reads configuration from `~/.config/itl-k8s-oidc/config.json` (Linux/macOS) or `%APPDATA%\itl-k8s-oidc\config.json` (Windows):

```json
{
  "issuer_url": "https://sso.example.com/realms/itlusions",
  "client_id": "kubelogin",
  "scopes": "openid,profile,email"
}
```

### All CLI Options

```bash
itl-oidc-setup --help
```

**Main options:**
- `--issuer-url`: OIDC issuer URL
- `--client-id`: OIDC client ID (default: kubelogin)
- `--scopes`: OIDC scopes (default: openid,profile,email)
- `--device-code`: Use device code flow
- `--ca-file`: Custom CA certificate file
- `--kubeconfig`: Custom kubeconfig path
- `--verify`: Verify auth after setup
- `--save-default`: Save config as defaults
- `--dry-run`: Show what would be done
- `--no-install-krew`: Don't auto-install krew
- `--no-install-plugin`: Don't auto-install oidc-login plugin
- `--extra-arg`: Pass additional args to oidc-login (repeatable)
- `--verbose`: Verbose output

## Default Configuration

- **Default issuer**: `https://sso.example.com/realms/itlusions`
- **Default client ID**: `kubelogin`
- **Default scopes**: `openid,profile,email`

## Notes

- Uses **public OIDC client with PKCE** for security
- Supports **device code flow** for headless environments
- Works on **Linux, macOS, and Windows**
- Automatically handles **krew and plugin installation**
- Clean error messages and non-zero exit codes on failure

## License

MIT License - see [LICENSE](LICENSE) file for details.
