# Fix flowchart font sizing and subgraph label spacing
# This script adds classDef statements for consistent fonts and spacer nodes for subgraph labels

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
    
    # Pattern to find flowchart blocks (from "flowchart TB" or "flowchart LR" to the closing ```)
    # We need to add classDef statements at the end of each flowchart, before the closing ```
    
    # Find all flowchart blocks and add classDef statements
    $flowchartPattern = '(?ms)(flowchart\s+(?:TB|TD|LR|RL|BT)\s+)(.*?)(```)'
    
    $content = [regex]::Replace($content, $flowchartPattern, {
        param($match)
        $flowchartDecl = $match.Groups[1].Value
        $flowchartBody = $match.Groups[2].Value
        $closingTicks = $match.Groups[3].Value
        
        # Check if classDef default already exists
        if ($flowchartBody -match 'classDef\s+default\s+') {
            return $match.Value  # Already has default classDef, skip
        }
        
        # Add classDef statements for font consistency
        $classDefStatements = @"

    %% Font sizing classes for consistency
    classDef default font-size:16px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef diamond font-size:14px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
"@
        
        return $flowchartDecl + $flowchartBody.TrimEnd() + $classDefStatements + "`n" + $closingTicks
    })
    
    # Now apply diamond class to all diamond nodes (nodes with {text})
    # Pattern: NODE_ID{text} -> NODE_ID{text}:::diamond
    $diamondPattern = '(\s+)([A-Z_][A-Z0-9_]*)\{([^}]+)\}(\s*$|\s+--)'
    
    $content = [regex]::Replace($content, $diamondPattern, {
        param($match)
        $leadingSpace = $match.Groups[1].Value
        $nodeId = $match.Groups[2].Value
        $nodeText = $match.Groups[3].Value
        $trailing = $match.Groups[4].Value
        
        # Check if already has :::diamond
        if ($match.Value -match ':::diamond') {
            return $match.Value
        }
        
        return "${leadingSpace}${nodeId}{${nodeText}}:::diamond${trailing}"
    }, [System.Text.RegularExpressions.RegexOptions]::Multiline)
    
    Set-Content $filePath $content -Encoding UTF8 -NoNewline
    Write-Host "  Updated $file"
}

Write-Host "`nDone! Flowchart font fixes applied."
Write-Host "Changes made:"
Write-Host "  1. Added classDef default with font-size:16px for all nodes"
Write-Host "  2. Added classDef diamond with font-size:14px for decision shapes"
Write-Host "  3. Applied :::diamond class to all diamond/decision nodes"
