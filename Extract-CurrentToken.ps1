# PowerShell script to extract current OIDC token from your logged-in session
# This extracts the token from your current kubectl context

Write-Host "🔑 Extracting Current OIDC Token" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check current context
$CurrentContext = kubectl config current-context
Write-Host "📋 Current context: $CurrentContext" -ForegroundColor Yellow

# Check current user
Write-Host "👤 Current user authentication:" -ForegroundColor Yellow
kubectl auth whoami

Write-Host ""
Write-Host "🔍 Extracting token information..." -ForegroundColor Yellow

# Method 1: Try to get token from kubeconfig
try {
    $KubeconfigRaw = kubectl config view --raw --minify | ConvertFrom-Yaml
    $CurrentUser = $KubeconfigRaw.users | Where-Object { $_.name -eq $KubeconfigRaw.'current-context' }
    
    if ($CurrentUser.user.exec) {
        Write-Host "✅ Using exec-based authentication (kubelogin)" -ForegroundColor Green
        
        # Run kubelogin to get fresh token
        Write-Host "🔄 Getting fresh token with kubelogin..." -ForegroundColor Yellow
        $TokenOutput = & kubelogin get-token --login devicecode --server-id kubernetes-oidc --client-id kubernetes-oidc --tenant-id itlusions 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Token obtained successfully!" -ForegroundColor Green
            $TokenData = $TokenOutput | ConvertFrom-Json
            
            Write-Host ""
            Write-Host "🔐 Token Information:" -ForegroundColor Cyan
            Write-Host "Access Token (first 50 chars): $($TokenData.status.token.Substring(0,50))..." -ForegroundColor Gray
            Write-Host "Expiration: $($TokenData.status.expirationTimestamp)" -ForegroundColor Gray
            
            # Save token to file
            $TokenFile = "$env:TEMP\k8s-current-token.txt"
            $TokenData.status.token | Out-File -FilePath $TokenFile -Encoding UTF8 -NoNewline
            Write-Host "💾 Token saved to: $TokenFile" -ForegroundColor Green
            
            # Create a simple kubeconfig with this token
            $SimpleConfigPath = "$env:USERPROFILE\.kube\config-token-only"
            $ClusterUrl = kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}'
            $ClusterCA = kubectl config view --raw --minify --flatten -o jsonpath='{.clusters[0].cluster.certificate-authority-data}'
            
            $SimpleConfig = @"
apiVersion: v1
kind: Config
clusters:
- name: kubernetes-cluster
  cluster:
    server: $ClusterUrl
    certificate-authority-data: $ClusterCA
users:
- name: token-user
  user:
    token: $($TokenData.status.token)
contexts:
- name: token-context
  context:
    cluster: kubernetes-cluster
    user: token-user
current-context: token-context
"@
            
            $SimpleConfig | Out-File -FilePath $SimpleConfigPath -Encoding UTF8
            Write-Host "📁 Simple token kubeconfig created: $SimpleConfigPath" -ForegroundColor Green
            
        } else {
            Write-Host "❌ Failed to get token with kubelogin" -ForegroundColor Red
        }
    }
    elseif ($CurrentUser.user.'auth-provider') {
        Write-Host "✅ Using auth-provider (legacy)" -ForegroundColor Green
        $AuthConfig = $CurrentUser.user.'auth-provider'.config
        
        if ($AuthConfig.'id-token') {
            Write-Host "🔐 ID Token found: $($AuthConfig.'id-token'.Substring(0,50))..." -ForegroundColor Gray
        }
        if ($AuthConfig.'refresh-token') {
            Write-Host "🔄 Refresh Token found: $($AuthConfig.'refresh-token'.Substring(0,50))..." -ForegroundColor Gray
        }
    }
    else {
        Write-Host "⚠️ No OIDC token configuration found in current user" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ Error extracting token: $($_.Exception.Message)" -ForegroundColor Red
}

# Method 2: Check if there's a cached token
Write-Host ""
Write-Host "🔍 Checking for cached tokens..." -ForegroundColor Yellow

$TokenCacheLocations = @(
    "$env:USERPROFILE\.kube\cache\oidc-login",
    "$env:USERPROFILE\.kube\cache",
    "$env:APPDATA\kubelogin"
)

foreach ($Location in $TokenCacheLocations) {
    if (Test-Path $Location) {
        Write-Host "📁 Found cache directory: $Location" -ForegroundColor Gray
        Get-ChildItem $Location -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*token*" } | ForEach-Object {
            Write-Host "   🗂️ $($_.FullName)" -ForegroundColor Gray
        }
    }
}

Write-Host ""
Write-Host "💡 Additional Options:" -ForegroundColor Cyan
Write-Host "1. Use kubectl proxy for temporary access" -ForegroundColor Gray
Write-Host "2. Create a service account for long-term automation" -ForegroundColor Gray
Write-Host "3. Use the extracted token directly in API calls" -ForegroundColor Gray

Write-Host ""
Write-Host "🧪 Test the extracted token:" -ForegroundColor Cyan
Write-Host "curl -H `"Authorization: Bearer <token>`" https://your-k8s-api/api/v1/nodes" -ForegroundColor Gray