# Fix flowchart fonts - increase size to 20px for better readability
# The previous 16px was too small

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
    
    # Update CSS font-size from 16px to 20px
    $content = $content -replace 'font-size: 16px !important', 'font-size: 20px !important'
    
    # Update classDef default font-size from 16px to 20px
    $content = $content -replace 'classDef default font-size:16px', 'classDef default font-size:20px'
    
    # Update diamond from 14px to 18px (proportionally larger)
    $content = $content -replace 'font-size: 14px !important', 'font-size: 18px !important'
    $content = $content -replace 'classDef diamond font-size:14px', 'classDef diamond font-size:18px'
    
    # Update root fontSize from 16 to 20
    $content = $content -replace '(\s+)fontSize: 16(\s)', '$1fontSize: 20$2'
    $content = $content -replace "fontSize: '16px'", "fontSize: '20px'"
    
    Set-Content $filePath $content -Encoding UTF8 -NoNewline
    Write-Host "  Updated $file - fonts increased to 20px"
}

Write-Host "`nDone! Flowchart fonts increased to 20px."
