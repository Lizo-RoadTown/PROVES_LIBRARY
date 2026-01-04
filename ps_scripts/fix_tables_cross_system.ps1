$file = "docs/diagrams/cross-system.md"
$content = Get-Content $file -Raw -Encoding UTF8

# Regex to remove the trailing empty column "|  |" from table rows
# Matches a pipe, optional whitespace, pipe, optional whitespace, at end of line
# Replaces it with a single pipe
$newContent = $content -replace '\|\s*\|\s*(\r?\n)', '|$1'

Set-Content $file $newContent -Encoding UTF8
Write-Host "Fixed tables in $file"
