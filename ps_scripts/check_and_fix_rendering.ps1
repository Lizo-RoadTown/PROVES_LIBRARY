<#
.SYNOPSIS
    Orchestrates the validation and fixing of Markdown files, including Mermaid rendering verification via GitHub.

.DESCRIPTION
    This script runs the standard linting and fixing scripts (v3 and mermaid rules), 
    then pushes the changes to a temporary branch ('verification-auto') and uses 
    Playwright to verify that the diagrams render correctly on GitHub.
    It can also attempt to fix rendering errors automatically.

.PARAMETER CheckOnly
    If set, skips the local linting/fixing scripts and only runs the GitHub rendering verification.

.PARAMETER FilePath
    Optional. Path to a specific file or directory to process. Defaults to 'docs/diagrams'.

.EXAMPLE
    .\check_and_fix_rendering.ps1
    Runs full process on docs/diagrams.

.EXAMPLE
    .\check_and_fix_rendering.ps1 -CheckOnly
    Only verifies rendering on GitHub (requires existing 'verification-auto' branch or pushes current state).
#>
#>

param(
    [switch]$CheckOnly,
    [switch]$ScanOnly,
    [string]$FilePath = "docs/diagrams"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path "$PSScriptRoot\.."
$ScriptsDir = "$RepoRoot\ps_scripts"
$PythonScript = "$RepoRoot\scripts\verify_rendering.py"
$BranchName = "verification-auto"

# 1. Run Local Fixes (unless CheckOnly or ScanOnly)
if (-not ($CheckOnly -or $ScanOnly)) {
    Write-Host "=== Phase 1: Running Local Fix Scripts ===" -ForegroundColor Cyan
    
    # Run the combined Mermaid and Lint fixer
    $combinedScript = "$ScriptsDir\fix_mermaid_and_lint.ps1"
    if (Test-Path $combinedScript) {
        Write-Host "Running fix_mermaid_and_lint.ps1..."
        # Pass the FilePath as RootPath if it's a directory, or handle file logic
        if (Test-Path $FilePath -PathType Container) {
            & pwsh $combinedScript -RootPath $FilePath
        } else {
            # If it's a file, we might need to run it differently or just run on parent dir
            # fix_mermaid_and_lint.ps1 defaults to recursive scan.
            # Let's just run it on the parent dir of the file if a file is passed
            $parent = Split-Path $FilePath -Parent
            & pwsh $combinedScript -RootPath $parent
        }
    } else {
        Write-Warning "Script not found: $combinedScript"
        
        # Fallback to v3 script if combined not found
        $v3Script = "$ScriptsDir\fix_markdownlint_robust_v3.ps1"
        if (Test-Path $v3Script) {
             Write-Host "Running fix_markdownlint_robust_v3.ps1..."
             $files = Get-ChildItem -Path $FilePath -Filter "*.md" -Recurse
             foreach ($file in $files) {
                 Write-Host "  Processing $($file.Name)..."
                 & pwsh $v3Script -FilePath $file.FullName
             }
        }
    }
}

# 2. Push to Verification Branch
Write-Host "=== Phase 2: Pushing to Verification Branch ($BranchName) ===" -ForegroundColor Cyan

# Check if we have changes
$hasChanges = $(git status --porcelain)
if ($hasChanges) {
    Write-Host "Staging and committing local changes..."
    git add .
    git commit -m "Auto-commit for verification $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
}

# Push to the verification branch (force update)
Write-Host "Pushing to origin/$BranchName..."
git push origin HEAD:refs/heads/$BranchName --force

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to push to verification branch. Cannot proceed with GitHub verification."
}

# 3. Run Playwright Verification
Write-Host "=== Phase 3: Verifying Rendering on GitHub ===" -ForegroundColor Cyan

# Get list of files to check
$filesToCheck = Get-ChildItem -Path $FilePath -Filter "*.md" -Recurse | Select-Object -ExpandProperty FullName

# Run Python script
Write-Host "Launching Playwright verification..."
if ($ScanOnly) {
    # Scan only: No --fix flag
    python $PythonScript --files $filesToCheck --branch $BranchName --owner "phantom-man" --repo "PROVES_LIBRARY"
} else {
    # Default/CheckOnly: Include --fix flag
    python $PythonScript --files $filesToCheck --branch $BranchName --owner "phantom-man" --repo "PROVES_LIBRARY" --fix
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "=== Verification Passed! ===" -ForegroundColor Green
} else {
    Write-Host "=== Verification Failed! ===" -ForegroundColor Red
    Write-Host "Check the output above for details."
    
    # If fixes were applied by Python, we might want to commit them?
    # The user can decide.
    $newChanges = $(git status --porcelain)
    if ($newChanges) {
        Write-Host "Note: The verification script applied fixes to local files." -ForegroundColor Yellow
        Write-Host "You should review and commit these changes."
    }
}
