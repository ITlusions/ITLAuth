# PowerShell script to create Keycloak service account
# Creates OIDC service accounts for centralized management

param(
    [string]$KeycloakUrl = "https://sts.itlusions.com",
    [string]$Realm = "itlusions",
    [string]$ClientId = "k8s-automation-sa"
)

Write-Host "🔑 Keycloak Service Account Creator" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Get admin credentials
$AdminUser = Read-Host "Enter Keycloak admin username"
$AdminPassword = Read-Host "Enter Keycloak admin password" -AsSecureString
$AdminPasswordText = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($AdminPassword))

# Get admin token
Write-Host "🔑 Getting admin access token..." -ForegroundColor Yellow
$TokenBody = @{
    username = $AdminUser
    password = $AdminPasswordText
    grant_type = "password"
    client_id = "admin-cli"
}

try {
    $TokenResponse = Invoke-RestMethod -Uri "$KeycloakUrl/realms/master/protocol/openid-connect/token" -Method Post -Body $TokenBody -ContentType "application/x-www-form-urlencoded"
    $AdminToken = $TokenResponse.access_token
    Write-Host "✅ Admin token obtained" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to get admin token: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Create service account client
Write-Host "🔧 Creating service account client: $ClientId" -ForegroundColor Yellow

$ClientData = @{
    clientId = $ClientId
    name = "$ClientId Service Account"
    description = "Kubernetes automation service account"
    enabled = $true
    clientAuthenticatorType = "client-secret"
    serviceAccountsEnabled = $true
    standardFlowEnabled = $false
    implicitFlowEnabled = $false
    directAccessGrantsEnabled = $false
    publicClient = $false
    protocol = "openid-connect"
    attributes = @{
        "access.token.lifespan" = "3600"
        "client.session.idle.timeout" = "1800"
        "client.session.max.lifespan" = "36000"
    }
} | ConvertTo-Json -Depth 3

$Headers = @{
    "Authorization" = "Bearer $AdminToken"
    "Content-Type" = "application/json"
}

try {
    Invoke-RestMethod -Uri "$KeycloakUrl/admin/realms/$Realm/clients" -Method Post -Body $ClientData -Headers $Headers
    Write-Host "✅ Service account client created" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create client: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Get client UUID and secret
try {
    $ClientInfo = Invoke-RestMethod -Uri "$KeycloakUrl/admin/realms/$Realm/clients?clientId=$ClientId" -Headers $Headers
    $ClientUuid = $ClientInfo[0].id
    
    $ClientSecret = Invoke-RestMethod -Uri "$KeycloakUrl/admin/realms/$Realm/clients/$ClientUuid/client-secret" -Headers $Headers
    $Secret = $ClientSecret.value
    
    Write-Host "✅ Client secret generated" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to get client secret: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test service account authentication
Write-Host "🧪 Testing service account authentication..." -ForegroundColor Yellow

$TestBody = @{
    grant_type = "client_credentials"
    client_id = $ClientId
    client_secret = $Secret
}

try {
    $TestResponse = Invoke-RestMethod -Uri "$KeycloakUrl/realms/$Realm/protocol/openid-connect/token" -Method Post -Body $TestBody -ContentType "application/x-www-form-urlencoded"
    Write-Host "✅ Service account authentication successful!" -ForegroundColor Green
    Write-Host "   Token expires in: $($TestResponse.expires_in) seconds" -ForegroundColor Gray
} catch {
    Write-Host "❌ Service account authentication failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Create kubeconfig
Write-Host ""
$CreateConfig = Read-Host "Create kubeconfig file? (Y/n)"
if ($CreateConfig -ne 'n') {
    Write-Host "🔧 Creating kubeconfig..." -ForegroundColor Yellow
    
    # Get cluster info
    try {
        $ClusterUrl = kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}'
        $ClusterCA = kubectl config view --raw --minify --flatten -o jsonpath='{.clusters[0].cluster.certificate-authority-data}'
        
        $KubeconfigPath = "$env:USERPROFILE\.kube\config-sa-$ClientId"
        
        $KubeconfigContent = @"
apiVersion: v1
kind: Config
clusters:
- name: kubernetes-cluster
  cluster:
    server: $ClusterUrl
    certificate-authority-data: $ClusterCA
users:
- name: keycloak-sa-$ClientId
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: kubelogin
      args:
      - get-token
      - --oidc-issuer-url=$KeycloakUrl/realms/$Realm
      - --oidc-client-id=$ClientId
      - --oidc-client-secret=$Secret
      - --grant-type=client_credentials
      env: null
      provideClusterInfo: false
contexts:
- name: keycloak-sa-context
  context:
    cluster: kubernetes-cluster
    user: keycloak-sa-$ClientId
current-context: keycloak-sa-context
"@
        
        $KubeconfigContent | Out-File -FilePath $KubeconfigPath -Encoding UTF8
        Write-Host "✅ Kubeconfig created: $KubeconfigPath" -ForegroundColor Green
        
    } catch {
        Write-Host "❌ Failed to create kubeconfig: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🎉 Keycloak Service Account Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Client ID: $ClientId" -ForegroundColor White
Write-Host "Client Secret: $Secret" -ForegroundColor Yellow
Write-Host "Realm: $Realm" -ForegroundColor White
Write-Host "Issuer URL: $KeycloakUrl/realms/$Realm" -ForegroundColor White
Write-Host ""
Write-Host "💾 Save these credentials securely!" -ForegroundColor Red
Write-Host ""
Write-Host "🔧 To use the kubeconfig:" -ForegroundColor Cyan
Write-Host "`$env:KUBECONFIG = '$KubeconfigPath'" -ForegroundColor Gray
Write-Host "kubectl auth whoami" -ForegroundColor Gray