# Fix subgraph heading spacing - add margin/padding
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
    
    # Replace the CSS to add proper spacing for cluster labels
    $oldCSS = "themeCSS: \|`r?`n    \.node:hover rect, \.node:hover circle, \.node:hover polygon \{ stroke-width: 3px !important; filter: drop-shadow\(0 0 8px rgba\(0,0,0,0\.3\)\); cursor: pointer; \}`r?`n    \.edgePath:hover path \{ stroke-width: 3px !important; opacity: 1; \}`r?`n    \.cluster-label \{ z-index: 10 !important; pointer-events: none; \}`r?`n    \.cluster rect \{ z-index: -1 !important; \}"
    
    $newCSS = @"
themeCSS: |
    .node:hover rect, .node:hover circle, .node:hover polygon { stroke-width: 3px !important; filter: drop-shadow(0 0 8px rgba(0,0,0,0.3)); cursor: pointer; }
    .edgePath:hover path { stroke-width: 3px !important; opacity: 1; }
    .cluster-label { transform: translateY(-15px) !important; font-weight: 600 !important; }
"@
    
    $content = $content -replace $oldCSS, $newCSS
    
    # Save
    Set-Content -Path $file -Value $content -Encoding UTF8 -NoNewline
    Write-Host "  ✓ Added translateY(-15px) to move labels up" -ForegroundColor Green
}

Write-Host "`n=== All diagrams updated ===" -ForegroundColor Green
Write-Host "Subgraph labels now offset 15px upward from content boxes" -ForegroundColor Yellow
