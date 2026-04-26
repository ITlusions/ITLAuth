# Installation and Usage Guide

## Zero-Click Installation (Recommended)

The fastest way to get started with ITLAuth is using our zero-click installers:

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

**What the installer does:**
- Checks Python 3.6+ installation
- Installs pip if needed
- Installs itl-kubectl-oidc-setup package with Python auth module
- Verifies installation
- Uses embedded fallback configuration if API unavailable
- Provides next steps

## Standard Installation Methods

### Option 1: Direct pip install

```bash
pip install itl-kubectl-oidc-setup
# Standard: Both binary and Python auth
itl-kubectl-oidc-setup

# Python-only: Skip binary installation
itl-kubectl-oidc-setup --python-only```

### Option 2: Install from source

```bash
# Clone the repository
git clone https://github.com/ITlusions/itl-kubectl-oidc-setup.git
cd itl-kubectl-oidc-setup

# Install the package
pip install .

# Or install in development mode
pip install -e .
```

### Option 3: Install from GitHub

```bash
pip install git+https://github.com/ITlusions/itl-kubectl-oidc-setup.git
```

## Usage

### Basic Usage

After installation, simply run:

```bash
itl-kubectl-oidc-setup
```

The tool will:
1. Check if kubectl is installed (install if missing)
2. Check if kubelogin plugin is available (install if missing)
3. Configure OIDC authentication for ITlusions Keycloak
4. Test the authentication
5. Provide next steps

### Command Line Options

```bash
# Show help
itl-kubectl-oidc-setup --help

# Use custom cluster name
itl-kubectl-oidc-setup --cluster my-cluster

# Use custom Keycloak URL
itl-kubectl-oidc-setup --keycloak-url https://auth.example.com

# Skip authentication testing
itl-kubectl-oidc-setup --no-test

# Verbose output
itl-kubectl-oidc-setup --verbose

# Force reinstall kubectl/kubelogin
itl-kubectl-oidc-setup --force-install
```

### Example Output

```
ITlusions Kubernetes OIDC Setup Tool v1.0.0

Checking operating system... Windows detected
Checking kubectl installation... Found at C:\Users\user\.local\bin\kubectl.exe
Checking kubelogin plugin... Found at C:\Users\user\.krew\bin\kubectl-oidc_login.exe
Configuring OIDC authentication...
Cluster configuration updated
User configuration updated  
Context set to: itlusions-cluster
Testing authentication...
Authentication successful!

Setup complete! You can now use kubectl with OIDC authentication.

Next steps:
1. Try: kubectl get pods
2. Your browser will open for authentication
3. Login with your ITlusions credentials
4. Return to terminal - you're authenticated!

For help: itl-kubectl-oidc-setup --help
```

## Authentication Methods

ITLAuth provides two authentication methods. Both are configured automatically during setup.

### Python Authentication Module (Recommended)

**Contexts**: `itl-python`, `itl-ssh-tunnel-python`

The native Python authentication module (`itl_kubectl_oidc_setup.auth`) provides:

**Features**:
- No binary dependencies required
- Pure Python using only stdlib
- PKCE-based OAuth2 flow (enhanced security)
- Automatic token caching in `~/.kube/cache/oidc/`
- Token refresh with 5-minute expiry buffer
- Local callback server on port 8000
- Seamless browser authentication

**Configuration added to ~/.kube/config**:
```yaml
users:
- name: oidc-user-python
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: python
      args:
      - -m
      - itl_kubectl_oidc_setup.auth
      env: null
      interactiveMode: IfAvailable
      provideClusterInfo: false
```

**How it works**:
1. kubectl executes `python -m itl_kubectl_oidc_setup.auth`
2. Module checks for valid cached token in `~/.kube/cache/oidc/itlusions_token.json`
3. If token valid (>5min remaining), returns it immediately
4. Otherwise:
   - Generates PKCE code verifier and challenge
   - Starts local HTTP server on `localhost:8000`
   - Opens browser to Keycloak login page with PKCE parameters
   - User authenticates via Keycloak (EntraID/GitHub/password)
   - Keycloak redirects to `localhost:8000/callback` with auth code
   - Module exchanges auth code for ID token using PKCE
   - Saves token to cache with expiry timestamp
   - Returns token to kubectl in ExecCredential format

**Requirements**:
- Python 3.6+ (no external packages needed)
- Port 8000 available for callback server
- ~/.kube/cache/oidc/ directory writable (created automatically)

**Usage**:
```bash
# Use Python auth context
kubectl --context=itl-python get pods

# Or via SSH tunnel
kubectl --context=itl-ssh-tunnel-python get pods
```

### Binary Authentication (kubelogin)

**Contexts**: `itl`, `itl-ssh-tunnel`

The traditional kubelogin binary plugin provides:

**Features**:
- Well-tested, mature implementation
- Widely used in Kubernetes community
- Minimal setup required

**Configuration added to ~/.kube/config**:
```yaml
users:
- name: oidc-user
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: ..\\.kubectl\\plugins\\kubectl-oidc_login.exe
      args:
      - get-token
      - --oidc-issuer-url=https://sts.itlusions.com/realms/itlusions
      - --oidc-client-id=kubernetes
      - --oidc-extra-scope=groups
```

**Requirements**:
- kubectl-oidc_login.exe binary (auto-installed by setup tool)
- Platform-specific binary for your OS

**Usage**:
```bash
# Use binary auth context
kubectl --context=itl get pods

# Or via SSH tunnel
kubectl --context=itl-ssh-tunnel get pods
```

### Choosing Your Method

**Use Python authentication if**:
- You want minimal dependencies
- Python is already installed on your system
- You prefer pure Python implementation
- Binary installation is restricted by policy
- You want easier debugging and extension

**Use binary authentication if**:
- You need maximum compatibility
- Python is not available
- You prefer the mature, widely-used tool
- You're already familiar with kubelogin

Both methods provide identical authentication capabilities and can be used interchangeably.

## Authentication Flow

1. **First time setup**: Run `itl-kubectl-oidc-setup`
2. **Daily usage**: Just use kubectl normally
   ```bash
   kubectl get pods
   kubectl get nodes
   kubectl describe deployment myapp
   ```
3. **Authentication**: When tokens expire, kubectl will automatically:
   - Open your browser
   - Redirect to ITlusions Keycloak
   - After login, return you to terminal
   - Continue with your kubectl command

## What Gets Configured

The tool modifies your `~/.kube/config` file to add:

### Cluster Configuration
```yaml
clusters:
- cluster:
    server: https://kubernetes.itlusions.com:6443
    certificate-authority-data: <base64-cert>
  name: itlusions-cluster
```

### User Configuration  
```yaml
users:
- name: itlusions-oidc-user
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: kubectl
      args:
      - oidc-login
      - get-token
      - --oidc-issuer-url=https://auth.itlusions.com/realms/ITL
      - --oidc-client-id=kubernetes-oidc
      - --oidc-extra-scope=email
      - --oidc-extra-scope=profile
      - --oidc-extra-scope=groups
```

### Context Configuration
```yaml
contexts:
- context:
    cluster: itlusions-cluster
    user: itlusions-oidc-user
    namespace: default
  name: itlusions-cluster
current-context: itlusions-cluster
```

## Verify Installation

After installation, verify everything is working:

### Quick Verification

```bash
# Check if command is available
itl-kubectl-oidc-setup --version

# Run verification script
python -c "$(curl -fsSL https://raw.githubusercontent.com/ITlusions/ITLAuth/main/verify-install.py)"
```

Or download and run the verification script:
```bash
curl -fsSL https://raw.githubusercontent.com/ITlusions/ITLAuth/main/verify-install.py -o verify-install.py
python verify-install.py
```

The verification script checks:
- Python version (3.6+)
- pip availability
- Package installation
- Command availability
- kubectl presence (optional)
- kubeconfig existence (optional)

### Verify Python Auth Module

```bash
# Test Python auth module directly
python -m itl_kubectl_oidc_setup.auth

# Should output ExecCredential JSON or open browser for authentication
```

### Verify Contexts

```bash
# List all configured contexts
kubectl config get-contexts

# Should show:
#   itl                      (binary auth, direct)
#   itl-ssh-tunnel          (binary auth, SSH tunnel)
#   itl-python              (Python auth, direct)
#   itl-ssh-tunnel-python   (Python auth, SSH tunnel)

# Test Python authentication
kubectl --context=itl-python get nodes
```

## Troubleshooting

### Python Authentication Issues

**Port 8000 already in use**
```bash
# Find what's using port 8000
# Windows:
netstat -ano | findstr :8000

# Linux/macOS:
lsof -i :8000

# Solutions:
# 1. Stop the conflicting application
# 2. Use binary authentication instead: kubectl --context=itl get pods
```

**ImportError: No module named itl_kubectl_oidc_setup**
```bash
# Reinstall the package
pip install --force-reinstall itl-kubectl-oidc-setup

# Verify installation
pip show itl-kubectl-oidc-setup
python -c "import itl_kubectl_oidc_setup.auth; print('OK')"
```

**Token cache permission errors**
```bash
# Check cache directory
ls -la ~/.kube/cache/oidc/

# Fix permissions (Linux/macOS)
chmod 700 ~/.kube/cache/oidc
chmod 600 ~/.kube/cache/oidc/*.json

# Windows - ensure only your user has access
# Right-click folder → Properties → Security → Advanced
```

**Browser doesn't open automatically**
```bash
# Copy the URL from terminal output manually
# Look for: "Open this URL in your browser: http://localhost:8000/..."

# Paste into browser and complete authentication
```

**"exec plugin: invalid apiVersion" error**
```yaml
# Ensure ~/.kube/config has correct apiVersion
# Should be: client.authentication.k8s.io/v1beta1
# NOT: client.authentication.k8s.io/v1alpha1
```

### kubectl not found after installation

**Windows:**
```powershell
# Refresh PATH
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")

# Or restart PowerShell/Command Prompt
```

**macOS/Linux:**
```bash
# Restart terminal or run:
source ~/.bashrc  # or ~/.zshrc
```

### kubelogin plugin not working

The tool tries multiple installation methods:
1. krew (if available)
2. Direct download from GitHub releases
3. Manual instructions

If all fail, you can manually install:

**Windows:**
```powershell
# Download and extract kubelogin
curl -LO https://github.com/Azure/kubelogin/releases/latest/download/kubelogin-win-amd64.zip
# Extract to a directory in your PATH
```

**macOS:**
```bash
brew install Azure/kubelogin/kubelogin
```

**Linux:**
```bash
# Download and extract
curl -LO https://github.com/Azure/kubelogin/releases/latest/download/kubelogin-linux-amd64.zip
sudo unzip kubelogin-linux-amd64.zip -d /usr/local/bin/
```

### Authentication browser doesn't open

1. Copy the URL from terminal output
2. Paste into your browser manually
3. Complete authentication
4. Return to terminal

### Permission errors

**Windows:**
- Run PowerShell as Administrator if needed
- Check Windows Defender/antivirus settings

**macOS/Linux:**
- Ensure proper file permissions: `chmod +x ~/.kube/itl-kubectl-oidc-setup`
- Use `sudo` if installing system-wide packages

### Network/Proxy Issues

If you're behind a corporate firewall:

```bash
# Set proxy environment variables
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Then run the tool
itl-kubectl-oidc-setup
```

## Development

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/ITlusions/itl-kubectl-oidc-setup.git
cd itl-kubectl-oidc-setup

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Run the tool
python -m itl_kubectl_oidc_setup
```

### Making Changes

```bash
# Format code
black kubectl_oidc_setup/ tests/

# Run linting
flake8 kubectl_oidc_setup/

# Run tests
pytest tests/

# Build package
python -m build
```

## Getting Help

1. **Command help**: `itl-kubectl-oidc-setup --help`
2. **GitHub Issues**: [Report issues](https://github.com/ITlusions/itl-kubectl-oidc-setup/issues)
3. **ITlusions Support**: Contact via [www.itlusions.com](https://www.itlusions.com)

## Security Notes

- The tool only configures local kubectl configuration
- No credentials are stored by the tool itself
- Authentication tokens are managed by kubectl/kubelogin
- All communication uses HTTPS
- Tool source code is open and auditable