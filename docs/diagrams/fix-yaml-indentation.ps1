# Fix YAML indentation error caused by improper line removal
# Following MERMAID_RULES.md validation requirements

$files = Get-ChildItem -Path "*.md" -Exclude "MERMAID_RULES.md","VALIDATION_REPORT.md"

foreach ($file in $files) {
    Write-Host "Processing: $($file.Name)"
    
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    
    # Fix: sequence: is incorrectly indented under flowchart
    # Should be at same level as flowchart, not nested inside it
    $content = $content -replace '(?m)^    diagramPadding: 8\r?\n      sequence:\r?\n', "    diagramPadding: 8`r`n  sequence:`r`n"
    
    # Write back
    $content | Set-Content $file.FullName -NoNewline -Encoding UTF8
    
    Write-Host "  ✓ Fixed YAML indentation"
}

Write-Host "`n✓ All files processed"
Write-Host "`nValidation commands:"
Write-Host "1. Check indentation: Select-String -Path *.md -Pattern '      sequence:' -Exclude MERMAID_RULES.md"
Write-Host "2. Should return NO matches if fixed correctly"
