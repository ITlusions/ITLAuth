# ITL CLI Gateway Test - Simple Version
$env:CONTROLPLANE_API_URL = "http://localhost:8081"

Write-Host "Testing API Gateway..." -ForegroundColor Cyan

# Check health
Write-Host "`n[1] Checking Gateway health..."
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8081/health" -Method GET
    Write-Host "Gateway Status: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "Gateway error: $_" -ForegroundColor Red
    exit 1
}

# Create tenant
Write-Host "`n[2] Creating tenant..."
python -m itlc tenant create prod-tenant --display-name "Production Tenant" --output json

# Create subscriptions
Write-Host "`n[3] Creating subscriptions..."
python -m itlc subscription create prod-sub-001 --display-name "Production Sub 001" --tenant-id prod-tenant --location westeurope --output json
python -m itlc subscription create prod-sub-002 --display-name "Production Sub 002" --tenant-id prod-tenant --location westeurope --output json
python -m itlc subscription create dev-sub-001 --display-name "Development Sub" --tenant-id prod-tenant --location westeurope --output json

# List subscriptions
Write-Host "`n[4] Listing subscriptions..."
python -m itlc subscription list --output table

# Create resource groups
Write-Host "`n[5] Creating resource groups..."
python -m itlc resourcegroup create app-services-rg prod-sub-001 --location westeurope --tag environment=production --tag team=platform --output json
python -m itlc resourcegroup create data-services-rg prod-sub-001 --location westeurope --tag environment=production --tag team=data --output json
python -m itlc resourcegroup create networking-rg prod-sub-002 --location westeurope --tag environment=production --tag team=infrastructure --output json
python -m itlc resourcegroup create dev-app-rg dev-sub-001 --location westeurope --tag environment=development --tag team=dev --output json

# List resource groups
Write-Host "`n[6] Listing resource groups..."
python -m itlc resourcegroup list --subscription-id prod-sub-001 --output table
python -m itlc resourcegroup list --subscription-id prod-sub-002 --output table
python -m itlc resourcegroup list --subscription-id dev-sub-001 --output table

Write-Host "`nTest Complete!" -ForegroundColor Green
