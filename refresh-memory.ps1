# ============================================================================
# PROVES Library - Refresh Claude Code Memory
# ============================================================================
#
# Run this before starting a session to give Claude current context.
#
# USAGE:
#   .\refresh-memory.ps1           # Update CLAUDE.md with current state
#   .\refresh-memory.ps1 -Verbose  # Show what's being gathered
#
# ============================================================================

param(
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Step($msg) { Write-Host "`n>> $msg" -ForegroundColor Cyan }
function Write-Info($msg) { if ($Verbose) { Write-Host "   $msg" -ForegroundColor Gray } }
function Write-Success($msg) { Write-Host "   $msg" -ForegroundColor Green }

# ----------------------------------------------------------------------------
# Gather Current State
# ----------------------------------------------------------------------------

Write-Step "Gathering current project state..."

# 1. Git status
Write-Info "Getting git status..."
$gitBranch = git -C $RootDir branch --show-current 2>$null
$gitStatus = git -C $RootDir status --porcelain 2>$null | Measure-Object | Select-Object -ExpandProperty Count
$recentCommits = git -C $RootDir log --oneline -3 2>$null

# 2. Implementation roadmap phase
Write-Info "Reading roadmap..."
$roadmapFile = Join-Path $RootDir ".deepagents\IMPLEMENTATION_ROADMAP.md"
$currentPhase = "Unknown"
if (Test-Path $roadmapFile) {
    $roadmapContent = Get-Content $roadmapFile -Raw
    if ($roadmapContent -match "Current Phase:\*\*\s*(.+)") {
        $currentPhase = $Matches[1].Trim()
    }
}

# 3. Recent session summaries
Write-Info "Finding recent session summaries..."
$sessionSummaries = Get-ChildItem -Path (Join-Path $RootDir ".deepagents") -Filter "SESSION_SUMMARY*.md" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 3

# 4. Migration status
Write-Info "Checking migrations..."
$migrationsDir = Join-Path $RootDir "supabase\migrations"
$latestMigration = "None found"
if (Test-Path $migrationsDir) {
    $latestMigrationFile = Get-ChildItem -Path $migrationsDir -Filter "*.sql" |
        Sort-Object Name -Descending |
        Select-Object -First 1
    if ($latestMigrationFile) {
        $latestMigration = $latestMigrationFile.Name
    }
}

# 5. Key folders status
Write-Info "Checking folder structure..."
$keyFolders = @{
    "canon" = Test-Path (Join-Path $RootDir "canon")
    ".deepagents" = Test-Path (Join-Path $RootDir ".deepagents")
    "production/core" = Test-Path (Join-Path $RootDir "production\core")
    "curation_dashboard" = Test-Path (Join-Path $RootDir "curation_dashboard")
    "supabase" = Test-Path (Join-Path $RootDir "supabase")
}

# ----------------------------------------------------------------------------
# Generate Current State Section
# ----------------------------------------------------------------------------

Write-Step "Generating current state..."

$currentState = @"

---

## Current State (Auto-Generated)

> Last refreshed: $(Get-Date -Format "yyyy-MM-dd HH:mm")

### Git Status
- **Branch:** $gitBranch
- **Uncommitted changes:** $gitStatus files
- **Recent commits:**
$(($recentCommits | ForEach-Object { "  - $_" }) -join "`n")

### Implementation Phase
- **Current:** $currentPhase
- **Roadmap:** `.deepagents/IMPLEMENTATION_ROADMAP.md`

### Database
- **Latest migration:** $latestMigration
- **Run migrations:** `cd supabase && .\migrate.ps1`

### Recent Session Work
$( if ($sessionSummaries.Count -gt 0) {
    ($sessionSummaries | ForEach-Object { "- $($_.Name)" }) -join "`n"
} else {
    "- No recent session summaries found"
})

### Active Folders
| Folder | Status |
|--------|--------|
$( ($keyFolders.GetEnumerator() | ForEach-Object { "| ``$($_.Key)`` | $(if ($_.Value) { 'Present' } else { 'Missing' }) |" }) -join "`n")
"@

# ----------------------------------------------------------------------------
# Update CLAUDE.md
# ----------------------------------------------------------------------------

Write-Step "Updating CLAUDE.md..."

$claudeFile = Join-Path $RootDir "CLAUDE.md"

if (-not (Test-Path $claudeFile)) {
    Write-Host "   CLAUDE.md not found at root. Creating..." -ForegroundColor Yellow
    # Create minimal version if missing
    $minimalContent = @"
# PROVES Library - Claude Code Context

> **This file is auto-loaded at session start.**

See canon/CANON.md for design principles.
See .deepagents/AGENT_CONTRACTS.md for agent patterns.
"@
    Set-Content -Path $claudeFile -Value $minimalContent
}

# Read current content
$content = Get-Content $claudeFile -Raw

# Remove old "Current State" section if exists
$pattern = "(?s)---\s*\r?\n\r?\n## Current State \(Auto-Generated\).*$"
$content = $content -replace $pattern, ""

# Append new current state
$content = $content.TrimEnd() + "`n" + $currentState

# Write back
Set-Content -Path $claudeFile -Value $content -NoNewline

Write-Success "CLAUDE.md updated with current state"

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------

Write-Host "`n" -NoNewline
Write-Host "============================================" -ForegroundColor Green
Write-Host " Memory refreshed! Ready for Claude session." -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Key context files:" -ForegroundColor White
Write-Host "  CLAUDE.md                           - Auto-loaded session context"
Write-Host "  canon/CANON.md                      - Design principles"
Write-Host "  .deepagents/AGENT_CONTRACTS.md      - Agent patterns"
Write-Host "  .deepagents/IMPLEMENTATION_ROADMAP.md - Current work phase"
Write-Host ""
