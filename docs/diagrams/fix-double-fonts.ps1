# Double font sizes since 200% zoom looks correct
# This effectively makes 40px the new default (equivalent to 20px at 200%)

$files = Get-ChildItem -Path "." -Filter "*.md" | Where-Object { $_.Name -ne "MERMAID_RULES.md" -and $_.Name -ne "cross-system.md" }

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    
    # Update fontSize in config from 20 to 40
    $content = $content -replace 'fontSize: 20', 'fontSize: 40'
    
    # Update CSS font-size from 20px to 40px
    $content = $content -replace 'font-size: 20px !important', 'font-size: 40px !important'
    
    # Update CSS font-size from 18px to 36px (diamonds)
    $content = $content -replace 'font-size: 18px !important', 'font-size: 36px !important'
    
    # Update fontSize in themeVariables from '20px' to '40px'
    $content = $content -replace "fontSize: '20px'", "fontSize: '40px'"
    
    # Update classDef default from 20px to 40px
    $content = $content -replace 'classDef default font-size:20px', 'classDef default font-size:40px'
    
    # Update classDef diamond from 18px to 36px
    $content = $content -replace 'classDef diamond font-size:18px', 'classDef diamond font-size:36px'
    
    Set-Content $file.FullName $content -Encoding UTF8 -NoNewline
    Write-Host "Updated $($file.Name) - fonts doubled to 40px"
}

Write-Host "`nAll flowchart fonts doubled. 40px at 100% = 20px at 200%"
