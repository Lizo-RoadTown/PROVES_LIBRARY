# Fix flowchart configuration and subgraph label overlap issues
$ErrorActionPreference = 'Stop'

$diagrams = @(
    'team-boundaries.md',
    'overview.md',
    'gnn-molecule.md',
    'knowledge-gaps.md',
    'cross-system.md',
    'transitive-chains.md'
)

foreach ($file in $diagrams) {
    Write-Host "`nProcessing: $file" -ForegroundColor Cyan
    
    $content = Get-Content $file -Raw -Encoding UTF8
    
    # Fix 1: Change curve: linear to curve: 'linear' (with quotes)
    $content = $content -replace "curve: linear`r?`n", "curve: 'linear'`r`n"
    
    # Fix 2: Add htmlLabels and useMaxWidth after curve
    $content = $content -replace "(curve: 'linear')`r?`n", "`$1`r`n    htmlLabels: true`r`n    useMaxWidth: true`r`n"
    
    # Fix 3: Add z-index fix for subgraph labels in themeCSS
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
    Write-Host "  ✓ Fixed curve parameter and subgraph labels" -ForegroundColor Green
}

Write-Host "`n=== All diagrams fixed ===" -ForegroundColor Green
Write-Host "- Curve parameter now quoted: 'linear'" -ForegroundColor Yellow
Write-Host "- Added htmlLabels: true and useMaxWidth: true" -ForegroundColor Yellow
Write-Host "- Added z-index fix for subgraph labels" -ForegroundColor Yellow
