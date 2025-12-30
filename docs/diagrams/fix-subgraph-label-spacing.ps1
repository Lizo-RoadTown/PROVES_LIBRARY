# Add proper subgraph label spacing using cluster padding
# This adds internal padding to push content away from labels

$files = Get-ChildItem -Path "*.md" -Exclude "MERMAID_RULES.md","VALIDATION_REPORT.md"

foreach ($file in $files) {
    Write-Host "Processing: $($file.Name)"
    
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    
    # Add cluster padding to themeCSS
    $oldCSS = '    \.node:hover rect, \.node:hover circle, \.node:hover polygon \{ stroke-width: 3px !important; filter: drop-shadow\(0 0 8px rgba\(0,0,0,0\.3\)\); cursor: pointer; \}\r?\n    \.edgePath:hover path \{ stroke-width: 3px !important; opacity: 1; \}'
    
    $newCSS = @'
    .node:hover rect, .node:hover circle, .node:hover polygon { stroke-width: 3px !important; filter: drop-shadow(0 0 8px rgba(0,0,0,0.3)); cursor: pointer; }
    .edgePath:hover path { stroke-width: 3px !important; opacity: 1; }
    .cluster > rect { padding: 20px !important; }
    .cluster-label { margin-bottom: 15px !important; }
'@
    
    $content = $content -replace $oldCSS, $newCSS
    
    # Write back
    $content | Set-Content $file.FullName -NoNewline -Encoding UTF8
    
    Write-Host "  ✓ Added cluster padding"
}

Write-Host "`n✓ All files processed"
Write-Host "Added: .cluster > rect { padding: 20px } and .cluster-label { margin-bottom: 15px }"
