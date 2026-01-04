# Fix common markdownlint issues in a Markdown file (PowerShell)
# - Adds blank lines around headings
# - Removes multiple consecutive blank lines
# - Fixes headings not starting at the beginning of the line
# - Fixes ordered list numbering
# - Removes spaces inside code spans

param(
    [string]$FilePath = "../docs/diagrams/MERMAID_RULES.md"
)

if (!(Test-Path $FilePath)) {
    Write-Error "File not found: $FilePath"
    exit 1
}

$content = Get-Content $FilePath -Raw -Encoding UTF8

# 1. Ensure headings start at the beginning of the line
$content = $content -replace "(?m)^\s+(#+)", '$1'

# 2. Add blank lines before and after headings
$content = $content -replace "(?m)([^\n])\n(#+ )", '$1\n\n$2'  # Before
$content = $content -replace "(?m)(#+ .+)(?!\n\n)(\n[^#\n])", '$1\n\n$2'  # After

# 3. Remove multiple consecutive blank lines (keep max 1)
$content = $content -replace "\n{3,}", "\n\n"

# 4. Fix ordered list numbering (1. 2. 3. ...)
$lines = $content -split "\n"
for ($i = 0; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -match "^\d+\. ") {
        $num = 1
        $j = $i
        while ($j -lt $lines.Length -and $lines[$j] -match "^\d+\. ") {
            $lines[$j] = $lines[$j] -replace "^\d+\. ", "$num. "
            $num++
            $j++
        }
        $i = $j - 1
    }
}
$content = $lines -join "`n"

# 5. Remove spaces inside code spans (inline code)
$content = $content -replace '`([^`]+ ) `', '`$1`'

# 6. Save the fixed content
Set-Content -Path $FilePath -Value $content -Encoding UTF8
Write-Host "Markdownlint fixes applied to $FilePath"
