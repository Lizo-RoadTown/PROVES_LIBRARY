# Setup Supabase for PROVES Curation Dashboard
# This script initializes Supabase CLI and creates the necessary migrations

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  PROVES Supabase Setup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Step 1: Install Supabase CLI as dev dependency
Write-Host "`n1. Installing Supabase CLI..." -ForegroundColor Yellow
npm install supabase --save-dev

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install Supabase CLI" -ForegroundColor Red
    Write-Host "   Make sure Node.js is installed: https://nodejs.org" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Supabase CLI installed" -ForegroundColor Green

# Step 2: Initialize Supabase (if not already done)
Write-Host "`n2. Initializing Supabase..." -ForegroundColor Yellow

if (Test-Path "supabase/config.toml") {
    Write-Host "✓ Supabase already initialized (supabase folder exists)" -ForegroundColor Green
} else {
    npx supabase init
    Write-Host "✓ Supabase initialized" -ForegroundColor Green
}

# Step 3: Login to Supabase
Write-Host "`n3. Login to Supabase..." -ForegroundColor Yellow
Write-Host "   (This will open a browser window)" -ForegroundColor Gray
npx supabase login

# Step 4: Link to your project
Write-Host "`n4. Linking to your Supabase project..." -ForegroundColor Yellow
Write-Host "   Your project ID is: guigtpwxlqwueylbbcpx" -ForegroundColor Gray
npx supabase link --project-ref guigtpwxlqwueylbbcpx

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Linked to Supabase project" -ForegroundColor Green
} else {
    Write-Host "⚠️  Link failed - you may need to enter your database password" -ForegroundColor Yellow
}

# Step 5: Pull existing schema (if any)
Write-Host "`n5. Checking for existing remote schema..." -ForegroundColor Yellow
$pullResult = npx supabase db pull 2>&1

if ($pullResult -match "migration") {
    Write-Host "✓ Pulled remote schema" -ForegroundColor Green
} else {
    Write-Host "ℹ️  No remote schema to pull (new project)" -ForegroundColor Gray
}

Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "  ✓ Supabase Setup Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Run: npx supabase start" -ForegroundColor White
Write-Host "     (Starts local Supabase stack)" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Access Studio: http://localhost:54323" -ForegroundColor White
Write-Host "     (Local database UI)" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Create Migration 016 for teams/batch_claims" -ForegroundColor White
Write-Host "     Run: .\create_migration_016.ps1" -ForegroundColor Gray
