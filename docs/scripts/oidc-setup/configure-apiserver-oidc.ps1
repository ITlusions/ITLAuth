# PowerShell script to add OIDC configuration to kube-apiserver
# Run this script on the control plane node with administrative privileges

Write-Host "🔧 Adding OIDC configuration to kube-apiserver..." -ForegroundColor Green

$manifestPath = "/etc/kubernetes/manifests/kube-apiserver.yaml"
$backupPath = "/etc/kubernetes/manifests/kube-apiserver.yaml.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"

# Check if running on Windows (this script should be run on the Linux control plane)
if ($IsWindows) {
    Write-Host "❌ This script should be run on the Linux control plane node, not Windows" -ForegroundColor Red
    Write-Host "Please SSH to the control plane node (10.99.100.4) and run the bash version instead" -ForegroundColor Yellow
    exit 1
}

# Backup the original file
try {
    Copy-Item $manifestPath $backupPath
    Write-Host "✅ Backup created: $backupPath" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create backup: $_" -ForegroundColor Red
    exit 1
}

# Check if OIDC is already configured
if (Get-Content $manifestPath | Select-String "oidc-issuer-url") {
    Write-Host "⚠️ OIDC configuration already exists in kube-apiserver.yaml" -ForegroundColor Yellow
    exit 1
}

# Read the file content
$content = Get-Content $manifestPath

# Find the line with --tls-private-key-file and add OIDC config after it
$newContent = @()
foreach ($line in $content) {
    $newContent += $line
    if ($line -match "--tls-private-key-file=/etc/kubernetes/pki/apiserver.key") {
        $newContent += "    - --oidc-issuer-url=https://sts.itlusions.com/realms/itlusions"
        $newContent += "    - --oidc-client-id=kubernetes-oidc"
        $newContent += "    - --oidc-username-claim=preferred_username"
        $newContent += "    - --oidc-groups-claim=groups"
        $newContent += "    - --oidc-username-prefix=-"
        $newContent += "    - --oidc-groups-prefix=-"
    }
}

# Write the modified content back
try {
    $newContent | Out-File -FilePath $manifestPath -Encoding UTF8
    Write-Host "✅ OIDC configuration added to kube-apiserver.yaml" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to write configuration: $_" -ForegroundColor Red
    # Restore backup
    Copy-Item $backupPath $manifestPath
    exit 1
}

Write-Host "🔄 The API server pod will restart automatically (this may take 1-2 minutes)" -ForegroundColor Cyan
Write-Host "📋 You can monitor the restart with: kubectl get pods -n kube-system -l component=kube-apiserver" -ForegroundColor Cyan

Write-Host ""
Write-Host "📄 Added OIDC configuration:" -ForegroundColor Green
Write-Host "    - --oidc-issuer-url=https://sts.itlusions.com/realms/itlusions"
Write-Host "    - --oidc-client-id=kubernetes-oidc"
Write-Host "    - --oidc-username-claim=preferred_username"
Write-Host "    - --oidc-groups-claim=groups"
Write-Host "    - --oidc-username-prefix=-"
Write-Host "    - --oidc-groups-prefix=-"