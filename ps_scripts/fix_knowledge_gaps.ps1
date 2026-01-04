
$file = "docs/diagrams/knowledge-gaps.md"
$content = Get-Content $file -Raw

# Fix tables: remove trailing empty columns |  |
$content = $content -replace '\|\s*\|\s*(\r?\n)', '$1'

# Fix cmake block: remove blank line before closing backticks
# The block ends with:
# # - Microservice architecture?
#
#    ```
# We want to remove the blank line.
$content = $content -replace '(# - Microservice architecture\?)\s+(\s*```)', '$1$2'

# Also check for other cmake blocks with blank lines at the end
# Pattern: content, newline, blank line, closing backticks
# $content = $content -replace '(\r?\n)\s+(\s*```)', '$1$2' # This might be too aggressive

Set-Content -Path $file -Value $content -Encoding UTF8
Write-Host "Fixed tables and cmake block in $file"
