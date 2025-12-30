# Fix text wrapping and remove fixed heights from Mermaid diagrams
# Following MERMAID_RULES.md script guidelines

$files = Get-ChildItem -Path "*.md" -Exclude "MERMAID_RULES.md","VALIDATION_REPORT.md"

foreach ($file in $files) {
    Write-Host "Processing: $($file.Name)"
    
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    
    # 1. Remove wrappingWidth (doesn't actually enable wrapping)
    $content = $content -replace 'wrappingWidth: 300\r?\n', ''
    $content = $content -replace 'wrappingWidth: 200\r?\n', ''
    
    # 2. Remove fixed width/height from sequence diagrams
    $content = $content -replace '    width: 150\r?\n', ''
    $content = $content -replace '    height: 65\r?\n', ''
    
    # 3. Remove fixed width/height from journey diagrams  
    $content = $content -replace '  journey:\r?\n    diagramMarginX: 50\r?\n    diagramMarginY: 10\r?\n    actorMargin: 50\r?\n    width: 150\r?\n    height: 65\r?\n    boxMargin: 10\r?\n    boxTextMargin: 5',
                                  '  journey:\r\n    diagramMarginX: 50\r\n    diagramMarginY: 10\r\n    actorMargin: 50\r\n    boxMargin: 10\r\n    boxTextMargin: 5'
    
    # 4. Replace themeCSS with proper wrapping styles
    $oldCSS = '    .node:hover rect, .node:hover circle, .node:hover polygon \{ stroke-width: 3px !important; filter: drop-shadow\(0 0 8px rgba\(0,0,0,0\.3\)\); cursor: pointer; \}\r?\n    .edgePath:hover path \{ stroke-width: 3px !important; opacity: 1; \}\r?\n    .cluster rect \{ padding-top: 25px !important; \}\r?\n    .cluster-label \{ font-weight: 600 !important; display: block !important; padding-bottom: 8px !important; \}'
    
    $newCSS = @'
    .node:hover rect, .node:hover circle, .node:hover polygon { stroke-width: 3px !important; filter: drop-shadow(0 0 8px rgba(0,0,0,0.3)); cursor: pointer; }
    .edgePath:hover path { stroke-width: 3px !important; opacity: 1; }
    .cluster-label { font-weight: 600 !important; margin-bottom: 12px !important; }
    .nodeLabel { white-space: normal !important; word-wrap: break-word !important; max-width: 250px !important; }
    .edgeLabel { white-space: normal !important; word-wrap: break-word !important; max-width: 200px !important; }
'@
    
    $content = $content -replace $oldCSS, $newCSS
    
    # Write back
    $content | Set-Content $file.FullName -NoNewline -Encoding UTF8
    
    Write-Host "  ✓ Updated: $($file.Name)"
}

Write-Host "`n✓ All diagram files processed"
Write-Host "Run validation: grep -n 'wrappingWidth\|width: 150\|height: 65' *.md"
