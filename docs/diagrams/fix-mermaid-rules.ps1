# Update MERMAID_RULES.md with fixed flowchart config
$ErrorActionPreference = 'Stop'

$file = 'MERMAID_RULES.md'
$content = Get-Content $file -Raw -Encoding UTF8

Write-Host "Updating MERMAID_RULES.md..." -ForegroundColor Cyan

# Fix 1: Change curve: linear to curve: 'linear' (with quotes) - all occurrences
$content = $content -replace "curve: linear`r?`n", "curve: 'linear'`r`n"

# Fix 2: Add htmlLabels and useMaxWidth after curve - all occurrences
$content = $content -replace "(curve: 'linear')`r?`n(    padding:)", "`$1`r`n    htmlLabels: true`r`n    useMaxWidth: true`r`n`$2"

# Fix 3: Add z-index fix for subgraph labels in themeCSS - all occurrences
$oldCSS = "themeCSS: \|`r?`n    \.node:hover rect, \.node:hover circle, \.node:hover polygon \{ stroke-width: 3px !important; filter: drop-shadow\(0 0 8px rgba\(0,0,0,0\.3\)\); cursor: pointer; \}`r?`n    \.edgePath:hover path \{ stroke-width: 3px !important; opacity: 1; \}"

$newCSS = @"
themeCSS: |
    .node:hover rect, .node:hover circle, .node:hover polygon { stroke-width: 3px !important; filter: drop-shadow(0 0 8px rgba(0,0,0,0.3)); cursor: pointer; }
    .edgePath:hover path { stroke-width: 3px !important; opacity: 1; }
    .cluster-label { z-index: 10 !important; pointer-events: none; }
    .cluster rect { z-index: -1 !important; }
"@

$content = $content -replace $oldCSS, $newCSS

# Save
Set-Content -Path $file -Value $content -Encoding UTF8 -NoNewline
Write-Host "✓ Updated all 4 seasonal themes" -ForegroundColor Green
Write-Host "  - curve: 'linear' (quoted)" -ForegroundColor Yellow
Write-Host "  - htmlLabels: true" -ForegroundColor Yellow
Write-Host "  - useMaxWidth: true" -ForegroundColor Yellow
Write-Host "  - z-index fix for subgraph labels" -ForegroundColor Yellow
