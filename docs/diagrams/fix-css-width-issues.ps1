# Remove max-width constraints that are causing box width issues
# Remove margin-bottom that's not working for subgraph spacing
# Return to simple, minimal CSS

$files = Get-ChildItem -Path "*.md" -Exclude "MERMAID_RULES.md","VALIDATION_REPORT.md"

foreach ($file in $files) {
    Write-Host "Processing: $($file.Name)"
    
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    
    # Replace complex CSS with simple hover effects only
    $oldCSS = '    \.node:hover rect, \.node:hover circle, \.node:hover polygon \{ stroke-width: 3px !important; filter: drop-shadow\(0 0 8px rgba\(0,0,0,0\.3\)\); cursor: pointer; \}\r?\n    \.edgePath:hover path \{ stroke-width: 3px !important; opacity: 1; \}\r?\n    \.cluster-label \{ font-weight: 600 !important; margin-bottom: 12px !important; \}\r?\n    \.nodeLabel \{ white-space: normal !important; word-wrap: break-word !important; max-width: 250px !important; \}\r?\n    \.edgeLabel \{ white-space: normal !important; word-wrap: break-word !important; max-width: 200px !important; \}'
    
    $newCSS = @'
    .node:hover rect, .node:hover circle, .node:hover polygon { stroke-width: 3px !important; filter: drop-shadow(0 0 8px rgba(0,0,0,0.3)); cursor: pointer; }
    .edgePath:hover path { stroke-width: 3px !important; opacity: 1; }
'@
    
    $content = $content -replace $oldCSS, $newCSS
    
    # Write back
    $content | Set-Content $file.FullName -NoNewline -Encoding UTF8
    
    Write-Host "  ✓ Simplified CSS"
}

Write-Host "`n✓ All files processed"
Write-Host "Removed: max-width constraints, margin-bottom, white-space overrides"
Write-Host "Kept: Hover effects only"
