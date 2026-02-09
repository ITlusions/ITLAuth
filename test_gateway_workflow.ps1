#!/usr/bin/env pwsh
# Test ITL CLI against API Gateway with complete workflow

$ErrorActionPreference = "Continue"
$env:CONTROLPLANE_API_URL = "http://localhost:8081"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "ITL CLI Gateway Integration Test" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Check Gateway Health
Write-Host "[1/7] Checking API Gateway health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8081/health" -Method GET
    Write-Host "✓ Gateway Status: $($health.status)" -ForegroundColor Green
    Write-Host "  Registered Providers: $($health.registered_providers.Count)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Gateway not responding: $_" -ForegroundColor Red
    exit 1
}

# Step 2: List available locations
Write-Host "`n[2/7] Listing available locations..." -ForegroundColor Yellow
python -m itlc location list --output table | Select-Object -First 15

# Step 3: Create Production Tenant
Write-Host "`n[3/7] Creating production tenant..." -ForegroundColor Yellow
python -m itlc tenant create prod-tenant --display-name "Production Tenant" --output json

# Step 4: Create subscriptions
Write-Host "`n[4/7] Creating subscriptions..." -ForegroundColor Yellow

Write-Host "  → Creating 'prod-sub-001'..." -ForegroundColor Gray
python -m itlc subscription create prod-sub-001 `
    --display-name "Production Subscription 001" `
    --tenant-id prod-tenant `
    --location westeurope `
    --output json

Write-Host "  → Creating 'prod-sub-002'..." -ForegroundColor Gray
python -m itlc subscription create prod-sub-002 `
    --display-name "Production Subscription 002" `
    --tenant-id prod-tenant `
    --location westeurope `
    --output json

Write-Host "  → Creating 'dev-sub-001'..." -ForegroundColor Gray
python -m itlc subscription create dev-sub-001 `
    --display-name "Development Subscription" `
    --tenant-id prod-tenant `
    --location westeurope `
    --output json

# Step 5: List subscriptions
Write-Host "`n[5/7] Listing all subscriptions..." -ForegroundColor Yellow
python -m itlc subscription list --output table

# Step 6: Create resource groups in West Europe
Write-Host "`n[6/7] Creating resource groups in West Europe..." -ForegroundColor Yellow

Write-Host "  → Creating 'app-services-rg' in prod-sub-001..." -ForegroundColor Gray
python -m itlc resourcegroup create app-services-rg `
    --subscription prod-sub-001 `
    --location westeurope `
    --tags "environment=production" "team=platform" `
    --output json

Write-Host "  → Creating 'data-services-rg' in prod-sub-001..." -ForegroundColor Gray
python -m itlc resourcegroup create data-services-rg `
    --subscription prod-sub-001 `
    --location westeurope `
    --tags "environment=production" "team=data" `
    --output json

Write-Host "  → Creating 'networking-rg' in prod-sub-002..." -ForegroundColor Gray
python -m itlc resourcegroup create networking-rg `
    --subscription prod-sub-002 `
    --location westeurope `
    --tags "environment=production" "team=infrastructure" `
    --output json

Write-Host "  → Creating 'dev-app-rg' in dev-sub-001..." -ForegroundColor Gray
python -m itlc resourcegroup create dev-app-rg `
    --subscription dev-sub-001 `
    --location westeurope `
    --tags "environment=development" "team=dev" `
    --output json

# Step 7: List resource groups by subscription
Write-Host "`n[7/7] Listing resource groups..." -ForegroundColor Yellow

Write-Host "  → Resource groups in prod-sub-001:" -ForegroundColor Gray
python -m itlc resourcegroup list --subscription prod-sub-001 --output table

Write-Host "`n  → Resource groups in prod-sub-002:" -ForegroundColor Gray
python -m itlc resourcegroup list --subscription prod-sub-002 --output table

Write-Host "`n  → Resource groups in dev-sub-001:" -ForegroundColor Gray
python -m itlc resourcegroup list --subscription dev-sub-001 --output table

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Created Resources:" -ForegroundColor White
Write-Host "  * 1 Tenant (prod-tenant)" -ForegroundColor Gray
Write-Host "  * 3 Subscriptions (prod-sub-001, prod-sub-002, dev-sub-001)" -ForegroundColor Gray
Write-Host "  * 4 Resource Groups in West Europe" -ForegroundColor Gray
Write-Host "    - app-services-rg (prod-sub-001)" -ForegroundColor Gray
Write-Host "    - data-services-rg (prod-sub-001)" -ForegroundColor Gray
Write-Host "    - networking-rg (prod-sub-002)" -ForegroundColor Gray
Write-Host "    - dev-app-rg (dev-sub-001)" -ForegroundColor Gray
Write-Host ""
