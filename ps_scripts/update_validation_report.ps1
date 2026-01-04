
$file = 'docs/diagrams/VALIDATION_REPORT.md'
$content = Get-Content $file -Raw -Encoding UTF8

# Update Diagram 4 type
$content = $content -replace 'Type: stateDiagram-v2', 'Type: flowchart TB'

Set-Content -Path $file -Value $content -Encoding UTF8
Write-Output 'Updated VALIDATION_REPORT.md'
