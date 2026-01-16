# Verify Supabase Local Development Prerequisites
# Run this script to check if you have everything needed for Supabase local dev

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Supabase Prerequisites Check" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

$allGood = $true

# Check 1: Node.js
Write-Host "`n1. Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "   ✓ Node.js installed: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Node.js not found" -ForegroundColor Red
    Write-Host "      Install from: https://nodejs.org" -ForegroundColor Gray
    $allGood = $false
}

# Check 2: npm
Write-Host "`n2. Checking npm..." -ForegroundColor Yellow
try {
    $npmVersion = npm --version
    Write-Host "   ✓ npm installed: v$npmVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ npm not found" -ForegroundColor Red
    $allGood = $false
}

# Check 3: Docker Desktop
Write-Host "`n3. Checking Docker Desktop..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "   ✓ Docker installed: $dockerVersion" -ForegroundColor Green

    # Check if Docker is running
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Docker is running" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Docker installed but not running" -ForegroundColor Yellow
        Write-Host "      Open Docker Desktop and wait for it to start" -ForegroundColor Gray
        $allGood = $false
    }
} catch {
    Write-Host "   ❌ Docker not found" -ForegroundColor Red
    Write-Host "      Download from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Gray
    Write-Host "      This is REQUIRED for Supabase local development" -ForegroundColor Gray
    $allGood = $false
}

# Check 4: Supabase CLI
Write-Host "`n4. Checking Supabase CLI..." -ForegroundColor Yellow
if (Test-Path "node_modules\.bin\supabase.ps1") {
    try {
        $supabaseVersion = npx supabase --version
        Write-Host "   ✓ Supabase CLI installed: v$supabaseVersion" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠️  Supabase CLI found but not working" -ForegroundColor Yellow
        $allGood = $false
    }
} else {
    Write-Host "   ⚠️  Supabase CLI not installed" -ForegroundColor Yellow
    Write-Host "      Run: npm install supabase --save-dev" -ForegroundColor Gray
    $allGood = $false
}

# Check 5: Supabase config
Write-Host "`n5. Checking Supabase configuration..." -ForegroundColor Yellow
if (Test-Path "supabase\config.toml") {
    Write-Host "   ✓ Supabase config found: supabase\config.toml" -ForegroundColor Green
} else {
    Write-Host "   ❌ Supabase not initialized" -ForegroundColor Red
    Write-Host "      Run: npx supabase init" -ForegroundColor Gray
    $allGood = $false
}

# Check 6: Environment variables
Write-Host "`n6. Checking environment variables..." -ForegroundColor Yellow
if (Test-Path ".env") {
    $envContent = Get-Content .env -Raw

    $checks = @(
        @{Name="NEXT_PUBLIC_SUPABASE_URL"; Required=$true},
        @{Name="NEXT_PUBLIC_SUPABASE_ANON_KEY"; Required=$true},
        @{Name="SUPABASE_SERVICE_ROLE_KEY"; Required=$true},
        @{Name="RESEND_API_KEY"; Required=$true}
    )

    $envGood = $true
    foreach ($check in $checks) {
        if ($envContent -match $check.Name) {
            $value = ($envContent | Select-String -Pattern "$($check.Name)=(.+)" | ForEach-Object { $_.Matches.Groups[1].Value }).Trim()
            if ($value -and $value -ne "your_key_here" -and $value -notmatch "\[YOUR-PASSWORD\]") {
                Write-Host "   ✓ $($check.Name) configured" -ForegroundColor Green
            } else {
                Write-Host "   ⚠️  $($check.Name) needs value" -ForegroundColor Yellow
                $envGood = $false
            }
        } else {
            Write-Host "   ⚠️  $($check.Name) missing" -ForegroundColor Yellow
            $envGood = $false
        }
    }

    if (-not $envGood) {
        Write-Host "      See: docs\DASHBOARD_PLATFORM_SETUP.md" -ForegroundColor Gray
    }
} else {
    Write-Host "   ⚠️  .env file not found" -ForegroundColor Yellow
    Write-Host "      Copy .env.example to .env and configure" -ForegroundColor Gray
}

# Summary
Write-Host "`n======================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "  ✓ All Prerequisites Met!" -ForegroundColor Green
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host "`nYou're ready to start Supabase local development!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "  1. Run: .\setup_supabase.ps1" -ForegroundColor White
    Write-Host "     (Login and link to your Supabase project)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. Run: npx supabase start" -ForegroundColor White
    Write-Host "     (Start local Supabase stack with Docker)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. Open: http://localhost:54323" -ForegroundColor White
    Write-Host "     (Supabase Studio - local database UI)" -ForegroundColor Gray
} else {
    Write-Host "  ⚠️  Prerequisites Missing" -ForegroundColor Yellow
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host "`nPlease install missing prerequisites above." -ForegroundColor Yellow
    Write-Host "See: docs\SUPABASE_LOCAL_SETUP_WINDOWS.md" -ForegroundColor Gray
}

Write-Host ""
