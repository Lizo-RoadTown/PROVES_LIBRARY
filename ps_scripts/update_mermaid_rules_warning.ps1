
$file = 'docs/diagrams/MERMAID_RULES.md'
$content = Get-Content $file -Raw -Encoding UTF8

$warning = @"
## State Diagram-Specific Rules

> **⚠️ WARNING:** `stateDiagram-v2` does NOT support straight lines (`curve: 'linear'`). If straight lines are required, convert the diagram to a `flowchart`.

### Transitions
"@

$content = $content -replace '## State Diagram-Specific Rules\s+### Transitions', $warning

Set-Content -Path $file -Value $content -Encoding UTF8
Write-Output 'Added warning to State Diagram section in MERMAID_RULES.md'
