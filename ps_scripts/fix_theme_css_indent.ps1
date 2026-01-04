$file = "docs/diagrams/cross-system.md"
$content = Get-Content $file -Raw -Encoding UTF8
# Replace start-of-line themeCSS with indented themeCSS
$newContent = $content -replace '(?m)^themeCSS: \|', '  themeCSS: |'
Set-Content $file $newContent -Encoding UTF8
Write-Host "Fixed indentation in $file"
