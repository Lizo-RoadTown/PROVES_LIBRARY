
$file = "docs/diagrams/MERMAID_RULES.md"
$content = Get-Content $file -Raw -Encoding UTF8

# Add rule about stateDiagram-v2
$newRule = @"

### ⚠️ State Diagrams vs Flowcharts

**AVOID `stateDiagram-v2` if straight lines are required.**

- `stateDiagram-v2` uses the `dagre` renderer which defaults to curved splines and **ignores** `curve: 'linear'` configuration.
- If you need straight lines (orthogonal or linear), use `flowchart` instead.
- **Rule:** Convert existing `stateDiagram-v2` to `flowchart` if curved lines are undesirable.
- **Data Processing:** When processing data for use in mermaid diagrams, process it in a way that produces `flowchart` syntax instead of `stateDiagram-v2` to ensure control over line curvature.

"@

# Insert this new rule after "Common Validation Errors Found" section
$pattern = "(### Common Validation Errors Found)"
$content = $content -replace $pattern, "$newRule`r`n`r`n$1"

Set-Content -Path $file -Value $content -Encoding UTF8
Write-Host "Updated MERMAID_RULES.md"
