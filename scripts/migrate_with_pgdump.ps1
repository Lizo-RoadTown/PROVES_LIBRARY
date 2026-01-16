# Neon to Supabase Migration using pg_dump/pg_restore
# This is the CORRECT way to migrate PostgreSQL databases

param(
    [string]$NeonUrl = "postgresql://neondb_owner:npg_GvP5x0yVrCLm@ep-empty-morning-af4l9ocx-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require",
    [string]$SupabaseUrl = "postgresql://postgres.guigtpwxlqwueylbbcpx:g%2QHd3qRT%8GK@@aws-0-us-west-2.pooler.supabase.com:5432/postgres"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Neon -> Supabase Migration (pg_dump/pg_restore)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Check if pg_dump is available
$pgDumpPath = $null
$pgRestorePath = $null

# Check common PostgreSQL installation paths on Windows
$possiblePaths = @(
    "C:\Program Files\PostgreSQL\16\bin",
    "C:\Program Files\PostgreSQL\15\bin",
    "C:\Program Files\PostgreSQL\14\bin",
    "$env:ProgramFiles\PostgreSQL\16\bin",
    "$env:ProgramFiles\PostgreSQL\15\bin"
)

foreach ($path in $possiblePaths) {
    if (Test-Path "$path\pg_dump.exe") {
        $pgDumpPath = "$path\pg_dump.exe"
        $pgRestorePath = "$path\pg_restore.exe"
        Write-Host "Found PostgreSQL tools at: $path" -ForegroundColor Green
        break
    }
}

if (-not $pgDumpPath) {
    Write-Host ""
    Write-Host "PostgreSQL client tools not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install PostgreSQL (client tools only is fine):" -ForegroundColor Yellow
    Write-Host "  1. Download from: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
    Write-Host "  2. Or use winget: winget install PostgreSQL.PostgreSQL" -ForegroundColor Yellow
    Write-Host "  3. Or use chocolatey: choco install postgresql" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "After installation, run this script again." -ForegroundColor Yellow
    exit 1
}

$dumpFile = Join-Path $PSScriptRoot "..\neon_full.dump"

Write-Host ""
Write-Host "Step 1: Dumping from Neon..." -ForegroundColor Yellow

# pg_dump with custom format
& $pgDumpPath `
    --dbname=$NeonUrl `
    --format=custom `
    --no-owner `
    --no-privileges `
    --verbose `
    --file=$dumpFile

if ($LASTEXITCODE -ne 0) {
    Write-Host "pg_dump failed!" -ForegroundColor Red
    exit 1
}

$dumpSize = (Get-Item $dumpFile).Length / 1MB
Write-Host "Dump complete: $([math]::Round($dumpSize, 2)) MB" -ForegroundColor Green

Write-Host ""
Write-Host "Step 2: Restoring to Supabase..." -ForegroundColor Yellow

# pg_restore to Supabase
& $pgRestorePath `
    --dbname=$SupabaseUrl `
    --no-owner `
    --no-privileges `
    --clean `
    --if-exists `
    --verbose `
    $dumpFile

if ($LASTEXITCODE -ne 0) {
    Write-Host "pg_restore had some errors (this may be normal for clean/if-exists)" -ForegroundColor Yellow
} else {
    Write-Host "Restore complete!" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Migration Complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Dump file saved at: $dumpFile" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Verify data in Supabase dashboard" -ForegroundColor Yellow
Write-Host "  2. Test your application" -ForegroundColor Yellow
Write-Host "  3. Delete the dump file when satisfied" -ForegroundColor Yellow
