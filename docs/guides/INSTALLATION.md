# Installation and Usage Guide

## Quick Installation

### Option 1: Direct pip install (Recommended)

```bash
pip install itl-kubectl-oidc-setup
```

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
🚀 ITlusions Kubernetes OIDC Setup Tool v1.0.0

✅ Checking operating system... Windows detected
✅ Checking kubectl installation... Found at C:\Users\user\.local\bin\kubectl.exe
✅ Checking kubelogin plugin... Found at C:\Users\user\.krew\bin\kubectl-oidc_login.exe
⚙️  Configuring OIDC authentication...
✅ Cluster configuration updated
✅ User configuration updated  
✅ Context set to: itlusions-cluster
🔐 Testing authentication...
✅ Authentication successful!

🎉 Setup complete! You can now use kubectl with OIDC authentication.

Next steps:
1. Try: kubectl get pods
2. Your browser will open for authentication
3. Login with your ITlusions credentials
4. Return to terminal - you're authenticated!

For help: itl-kubectl-oidc-setup --help
```

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

## Troubleshooting

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