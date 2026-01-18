# ============================================================================
# PROVES Library - Database Migration Script
# ============================================================================
#
# USAGE:
#   .\migrate.ps1 031        # Run migration 031 directly against database
#   .\migrate.ps1 -List      # List all migrations
#   .\migrate.ps1 -DryRun 031  # Show what would run without executing
#
# REQUIRES: DATABASE_URL in .env
# ============================================================================

param(
    [Parameter(Position=0)]
    [string]$Migration,
    [switch]$List,
    [switch]$DryRun,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot
$MigrationsDir = Join-Path $PSScriptRoot "migrations"
$PythonExe = Join-Path $RootDir ".venv\Scripts\python.exe"
$EnvFile = Join-Path $RootDir ".env"

# ----------------------------------------------------------------------------
# Help
# ----------------------------------------------------------------------------
if ($Help -or (-not $Migration -and -not $List)) {
    Write-Host @"

PROVES Library - Migration Script
=================================

USAGE:
  .\migrate.ps1 031         Run migration 031 against the database
  .\migrate.ps1 -List       List all available migrations
  .\migrate.ps1 -DryRun 031 Show SQL without executing

EXAMPLES:
  .\migrate.ps1 031         # Run user profiles migration
  .\migrate.ps1 032         # Run security fixes migration

REQUIREMENTS:
  - DATABASE_URL in .env file
  - Python with psycopg2 (in .venv)

"@
    exit 0
}

# ----------------------------------------------------------------------------
# List Mode
# ----------------------------------------------------------------------------
if ($List) {
    Write-Host "`nAvailable migrations:" -ForegroundColor Cyan
    Get-ChildItem -Path $MigrationsDir -Filter "*.sql" | Sort-Object Name | ForEach-Object {
        Write-Host "  $($_.Name)" -ForegroundColor Gray
    }
    Write-Host "`nTo apply: .\migrate.ps1 <number>" -ForegroundColor Yellow
    exit 0
}

# ----------------------------------------------------------------------------
# Find Migration File
# ----------------------------------------------------------------------------
$pattern = "*$Migration*"
$found = Get-ChildItem -Path $MigrationsDir -Filter $pattern -ErrorAction SilentlyContinue | Select-Object -First 1

if (-not $found) {
    Write-Host "`n[ERR] Migration not found: $Migration" -ForegroundColor Red
    Write-Host "`nAvailable:" -ForegroundColor Yellow
    Get-ChildItem -Path $MigrationsDir -Filter "*.sql" | Sort-Object Name | ForEach-Object {
        Write-Host "  $($_.Name)" -ForegroundColor Gray
    }
    exit 1
}

Write-Host "`n>> Migration: $($found.Name)" -ForegroundColor Cyan

# ----------------------------------------------------------------------------
# Dry Run Mode
# ----------------------------------------------------------------------------
if ($DryRun) {
    Write-Host "`n[DRY RUN] Would execute:" -ForegroundColor Yellow
    Get-Content $found.FullName | Select-Object -First 30
    Write-Host "`n... (truncated)" -ForegroundColor Gray
    exit 0
}

# ----------------------------------------------------------------------------
# Load DATABASE_URL from .env
# ----------------------------------------------------------------------------
$dbUrl = $env:DATABASE_URL
if (-not $dbUrl -and (Test-Path $EnvFile)) {
    $envContent = Get-Content $EnvFile
    foreach ($line in $envContent) {
        if ($line -match "^DATABASE_URL=(.+)$") {
            $dbUrl = $Matches[1]
            break
        }
    }
}

if (-not $dbUrl) {
    Write-Host "`n[ERR] DATABASE_URL not found in environment or .env file" -ForegroundColor Red
    exit 1
}

Write-Host "   Database: Connected" -ForegroundColor Gray

# ----------------------------------------------------------------------------
# Execute Migration via Python
# ----------------------------------------------------------------------------
$pythonScript = @"
import sys
import psycopg2
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

db_url = sys.argv[1]
sql_file = sys.argv[2]

# Strip pgbouncer parameter that psycopg2 doesn't understand
parsed = urlparse(db_url)
query_params = parse_qs(parsed.query)
query_params.pop('pgbouncer', None)  # Remove if present
clean_query = urlencode(query_params, doseq=True)
clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, clean_query, parsed.fragment))

with open(sql_file, 'r', encoding='utf-8') as f:
    sql = f.read()

try:
    conn = psycopg2.connect(clean_url)
    conn.autocommit = False
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    print('[OK] Migration completed successfully')
    cur.close()
    conn.close()
except psycopg2.Error as e:
    print(f'[ERR] {e}')
    sys.exit(1)
"@

# Write temp python script
$tempScript = [System.IO.Path]::GetTempFileName() + ".py"
$pythonScript | Out-File -FilePath $tempScript -Encoding utf8

try {
    Write-Host "   Executing..." -ForegroundColor Gray
    & $PythonExe $tempScript $dbUrl $found.FullName
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n[OK] $($found.Name) applied successfully" -ForegroundColor Green
    } else {
        Write-Host "`n[ERR] Migration failed" -ForegroundColor Red
        exit 1
    }
} finally {
    Remove-Item $tempScript -ErrorAction SilentlyContinue
}
