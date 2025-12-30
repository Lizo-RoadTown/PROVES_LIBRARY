# Fix subgraph heading overlap by adding spacer nodes
# Also standardize font sizes across all config levels

$diagramFiles = @(
    "team-boundaries.md",
    "cross-system.md",
    "gnn-molecule.md",
    "knowledge-gaps.md",
    "overview.md",
    "transitive-chains.md"
)

$spacerCounter = 0

foreach ($file in $diagramFiles) {
    $filePath = "c:\Users\User\PROVES_LIBRARY\docs\diagrams\$file"
    if (-not (Test-Path $filePath)) {
        Write-Host "Skipping $file - not found"
        continue
    }
    
    Write-Host "Processing $file..."
    $content = Get-Content $filePath -Raw -Encoding UTF8
    
    # Fix 1: Standardize fontSize in YAML config - change root fontSize: 20 to fontSize: 16
    # and themeVariables fontSize: '24px' to fontSize: '16px'
    $content = $content -replace "(\s+)fontSize: 20(\s)", '$1fontSize: 16$2'
    $content = $content -replace "(\s+)fontSize: '24px'", '$1fontSize: ''16px'''
    
    # Fix 2: Add spacer nodes after each subgraph declaration
    # Pattern: subgraph "Title" or subgraph id ["Title"]
    # Need to add a spacer node on the next line
    
    # Match subgraph lines and add spacer after them
    $subgraphPattern = '(?m)(^\s*subgraph\s+(?:"[^"]+"|[a-zA-Z_][a-zA-Z0-9_]*\s*\["[^"]+"\]|[a-zA-Z_][a-zA-Z0-9_]*))\s*$'
    
    $content = [regex]::Replace($content, $subgraphPattern, {
        param($match)
        $subgraphLine = $match.Groups[1].Value
        $script:spacerCounter++
        $spacerId = "spacer$($script:spacerCounter)"
        # Add spacer node - using a single space in brackets creates a minimal invisible node
        return "$subgraphLine`n        $spacerId[ ]:::spacer"
    })
    
    # Fix 3: Add spacer classDef if not present (after the existing classDef lines, before closing ```)
    # Look for the classDef diamond line and add spacer class after it
    if ($content -notmatch 'classDef spacer') {
        $content = $content -replace '(classDef diamond[^;]+;)', '$1
    classDef spacer fill:none,stroke:none,color:transparent,width:1px,height:1px;'
    }
    
    Set-Content $filePath $content -Encoding UTF8 -NoNewline
    Write-Host "  Updated $file (added $spacerCounter spacers so far)"
}

Write-Host "`nDone! Subgraph spacer fixes applied."
Write-Host "Changes made:"
Write-Host "  1. Standardized fontSize to 16/16px across root and themeVariables"
Write-Host "  2. Added invisible spacer nodes at top of each subgraph"
Write-Host "  3. Added classDef spacer to hide spacer nodes"
Write-Host "  Total spacers added: $spacerCounter"
