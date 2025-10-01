# Troubleshooting Guide

## Common Issues and Solutions

### kubectl Installation Issues

#### kubectl not found after installation

**Windows:**
```powershell
# Refresh PATH environment variable
$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")

# Or restart PowerShell/Command Prompt
```

**macOS/Linux:**
```bash
# Restart terminal or reload shell configuration
source ~/.bashrc  # or ~/.zshrc for zsh users

# Check if kubectl is in PATH
which kubectl
```

**Solution:** If kubectl still isn't found, manually add it to your PATH or reinstall using the appropriate method for your OS.

#### Permission denied when installing kubectl

**Windows:**
- Run PowerShell as Administrator
- Disable Windows Defender real-time protection temporarily
- Check corporate antivirus settings

**macOS/Linux:**
```bash
# Use sudo for system-wide installation
sudo curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

### kubelogin Plugin Issues

#### kubelogin plugin not working

The setup tool tries multiple installation methods:
1. krew (if available)
2. Direct download from GitHub releases
3. Manual installation instructions

**Manual Installation:**

**Windows:**
```powershell
# Download latest release
$url = "https://github.com/Azure/kubelogin/releases/latest/download/kubelogin-win-amd64.zip"
Invoke-WebRequest -Uri $url -OutFile "kubelogin.zip"
Expand-Archive kubelogin.zip -DestinationPath "$env:USERPROFILE\.krew\bin\"
```

**macOS:**
```bash
# Using Homebrew
brew install Azure/kubelogin/kubelogin

# Or manual download
curl -LO https://github.com/Azure/kubelogin/releases/latest/download/kubelogin-darwin-amd64.zip
unzip kubelogin-darwin-amd64.zip
sudo mv bin/darwin_amd64/kubelogin /usr/local/bin/
```

**Linux:**
```bash
curl -LO https://github.com/Azure/kubelogin/releases/latest/download/kubelogin-linux-amd64.zip
unzip kubelogin-linux-amd64.zip
sudo mv bin/linux_amd64/kubelogin /usr/local/bin/
```

### OIDC Authentication Issues

#### Browser doesn't open for authentication

**Symptoms:**
- kubectl commands hang
- No browser window opens
- Terminal shows authentication URL

**Solutions:**
1. **Manual browser authentication:**
   - Copy the URL from terminal output
   - Paste into your preferred browser
   - Complete authentication
   - Return to terminal

2. **Check default browser:**
   ```bash
   # Linux - set default browser
   export BROWSER=firefox
   
   # macOS - check default browser
   defaults read com.apple.LaunchServices/com.apple.launchservices.secure | grep -A 1 -B 1 http
   ```

3. **Corporate network issues:**
   - Check proxy settings
   - Verify firewall allows browser redirects
   - Contact IT support for authentication URL whitelist

#### Invalid or expired tokens

**Symptoms:**
- Authentication works but kubectl commands fail with 401 Unauthorized
- Error: "token has expired"

**Solutions:**
1. **Clear token cache:**
   ```bash
   # Remove cached tokens
   rm -rf ~/.kube/cache/oidc-login/
   
   # Windows
   Remove-Item -Recurse -Force "$env:USERPROFILE\.kube\cache\oidc-login\"
   ```

2. **Force re-authentication:**
   ```bash
   kubectl oidc-login get-token --oidc-issuer-url=https://sts.itlusions.com/realms/itlusions --oidc-client-id=kubernetes-oidc
   ```

3. **Check system clock:**
   - Ensure system time is synchronized
   - JWT tokens are time-sensitive

#### Groups not mapping correctly

**Symptoms:**
- Authentication succeeds but access denied
- User authenticated but wrong permissions

**Solutions:**
1. **Verify group membership in Keycloak:**
   - Login to Keycloak admin console
   - Check user's group assignments
   - Ensure `itl-cluster-admin` group exists and user is member

2. **Check Kubernetes RBAC:**
   ```bash
   # Verify ClusterRoleBinding exists
   kubectl get clusterrolebinding itl-cluster-admin-oidc-binding
   
   # Check what groups you're authenticated with
   kubectl auth whoami
   ```

3. **API Server OIDC configuration:**
   ```bash
   # Verify API server has correct group claim configuration
   kubectl get pod -n kube-system -l component=kube-apiserver -o yaml | grep oidc-groups-claim
   ```

### Network and Connectivity Issues

#### Cannot reach Keycloak server

**Symptoms:**
- Connection timeouts
- SSL/TLS errors
- DNS resolution failures

**Solutions:**
1. **Test connectivity:**
   ```bash
   # Test basic connectivity
   curl -I https://sts.itlusions.com
   
   # Test OIDC endpoint
   curl https://sts.itlusions.com/realms/itlusions/.well-known/openid_configuration
   ```

2. **Corporate proxy/firewall:**
   ```bash
   # Set proxy environment variables
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080
   export NO_PROXY=localhost,127.0.0.1,.local
   ```

3. **SSL/TLS issues:**
   ```bash
   # Check certificate validity
   openssl s_client -connect sts.itlusions.com:443 -servername sts.itlusions.com
   
   # For testing only - disable SSL verification (NOT for production)
   export KUBECONFIG=~/.kube/config-insecure
   ```

#### VPN or private network issues

**Solutions:**
- Ensure VPN is connected
- Check DNS settings point to correct servers
- Verify routing to ITlusions infrastructure

### API Server Configuration Issues

#### API server won't start after OIDC configuration

**Symptoms:**
- API server pod in CrashLoopBackOff
- Control plane unreachable

**Emergency Recovery:**
1. **Access control plane node directly:**
   ```bash
   ssh root@control-plane-ip
   
   # Restore backup
   cd /etc/kubernetes/manifests
   cp kube-apiserver.yaml.backup.* kube-apiserver.yaml
   ```

2. **Check kubelet logs:**
   ```bash
   journalctl -u kubelet -f
   ```

3. **Validate YAML syntax:**
   ```bash
   # Check YAML is valid
   python3 -c "import yaml; yaml.safe_load(open('/etc/kubernetes/manifests/kube-apiserver.yaml'))"
   ```

#### OIDC configuration not loading

**Symptoms:**
- API server starts but OIDC authentication doesn't work
- API server pod doesn't have OIDC flags

**Solutions:**
1. **Force pod restart:**
   ```bash
   # Touch manifest to trigger restart
   touch /etc/kubernetes/manifests/kube-apiserver.yaml
   
   # Or move and restore
   mv /etc/kubernetes/manifests/kube-apiserver.yaml /tmp/
   sleep 10
   mv /tmp/kube-apiserver.yaml /etc/kubernetes/manifests/
   ```

2. **Verify configuration:**
   ```bash
   # Check OIDC flags in running pod
   kubectl get pod -n kube-system -l component=kube-apiserver -o yaml | grep oidc
   ```

### Permission and RBAC Issues

#### Access denied after successful authentication

**Symptoms:**
- User authenticates successfully
- kubectl commands return 403 Forbidden

**Solutions:**
1. **Check user's groups:**
   ```bash
   kubectl auth whoami
   ```

2. **Verify RBAC bindings:**
   ```bash
   # List all ClusterRoleBindings
   kubectl get clusterrolebinding | grep oidc
   
   # Check specific binding
   kubectl describe clusterrolebinding itl-cluster-admin-oidc-binding
   ```

3. **Create missing RBAC:**
   ```bash
   # Create ClusterRoleBinding for your group
   kubectl create clusterrolebinding my-oidc-binding \
     --clusterrole=cluster-admin \
     --group=itl-cluster-admin
   ```

## Advanced Debugging

### Enable verbose logging

```bash
# Run kubectl with verbose output
kubectl --v=9 get pods

# Enable kubelogin debug logging
export KUBELOGIN_LOG_LEVEL=trace
```

### Capture network traffic

```bash
# Use tcpdump to capture OIDC traffic
sudo tcpdump -i any -w oidc-debug.pcap host sts.itlusions.com

# Analyze with Wireshark
wireshark oidc-debug.pcap
```

### Check JWT token contents

```bash
# Decode JWT token (don't log sensitive data in production)
echo "your-jwt-token" | cut -d. -f2 | base64 -d | jq .
```

## Getting Additional Help

### Information to collect

When reporting issues, please provide:

1. **Environment information:**
   ```bash
   kubectl version --client
   kubelogin --version
   echo $OSTYPE
   ```

2. **Configuration files:**
   ```bash
   kubectl config view --minify --raw
   ```

3. **Error messages:**
   - Full error output
   - Relevant log entries
   - Screenshots if helpful

4. **Network information:**
   - Proxy settings
   - VPN status
   - Corporate firewall rules

### Support channels

1. **GitHub Issues:** [ITlusions/ITLAuth/issues](https://github.com/ITlusions/ITLAuth/issues)
2. **ITlusions Support:** Contact via [www.itlusions.com](https://www.itlusions.com)
3. **Internal Matrix:** #k8s-support channel

## Prevention Tips

### Regular maintenance

1. **Keep tools updated:**
   ```bash
   # Update kubectl
   kubectl version --client
   
   # Update kubelogin
   kubelogin --version
   ```

2. **Monitor token expiration:**
   - Set up alerts for token expiry
   - Implement automated token refresh

3. **Backup configurations:**
   ```bash
   # Backup kubeconfig
   cp ~/.kube/config ~/.kube/config.backup.$(date +%Y%m%d)
   
   # Backup API server config
   cp /etc/kubernetes/manifests/kube-apiserver.yaml /etc/kubernetes/manifests/kube-apiserver.yaml.backup.$(date +%Y%m%d)
   ```

### Security best practices

1. **Principle of least privilege:**
   - Don't grant cluster-admin unless necessary
   - Use namespace-specific roles when possible

2. **Token security:**
   - Never share JWT tokens
   - Use service accounts for automation
   - Rotate secrets regularly

3. **Network security:**
   - Use TLS everywhere
   - Implement proper firewall rules
   - Monitor authentication logs