# Fix flowchart font sizing by adding CSS to themeCSS
# This adds explicit font-size rules that should work better than classDef

$diagramFiles = @(
    "team-boundaries.md",
    "cross-system.md",
    "gnn-molecule.md",
    "knowledge-gaps.md",
    "overview.md",
    "transitive-chains.md"
)

foreach ($file in $diagramFiles) {
    $filePath = "c:\Users\User\PROVES_LIBRARY\docs\diagrams\$file"
    if (-not (Test-Path $filePath)) {
        Write-Host "Skipping $file - not found"
        continue
    }
    
    Write-Host "Processing $file..."
    $content = Get-Content $filePath -Raw -Encoding UTF8
    
    # Add font-size CSS rules to themeCSS section
    # Find the cluster-label line in themeCSS and add after it
    $oldCSS = '.cluster-label { font-weight: 600; }'
    $newCSS = @'
.cluster-label { font-weight: 600; }
    .node .label, .nodeLabel, .node foreignObject div, .edgeLabel { font-size: 16px !important; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif !important; }
    .node.decision .label, .node polygon + .label { font-size: 14px !important; }
'@
    
    # Only replace if not already updated
    if ($content -notmatch '\.node \.label.*font-size: 16px') {
        $content = $content -replace [regex]::Escape($oldCSS), $newCSS
        Set-Content $filePath $content -Encoding UTF8 -NoNewline
        Write-Host "  Updated $file with font-size CSS"
    } else {
        Write-Host "  $file already has font-size CSS, skipping"
    }
}

Write-Host "`nDone! ThemeCSS font-size rules added."
Write-Host "Added CSS rules:"
Write-Host "  .node .label, .nodeLabel, etc. { font-size: 16px !important; }"
Write-Host "  .node.decision .label { font-size: 14px !important; }"
