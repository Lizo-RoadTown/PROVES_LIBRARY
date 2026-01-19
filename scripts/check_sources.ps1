$apikey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd1aWd0cHd4bHF3dWV5bGJiY3B4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODUyNzE2NiwiZXhwIjoyMDg0MTAzMTY2fQ.NR2qUIIBSppOOzh_ArLTpQuSaKt9BmFv0KtAQ-ILcFw"

$headers = @{
    "apikey" = $apikey
    "Authorization" = "Bearer $apikey"
}

Write-Host "=== All Team Sources ===" -ForegroundColor Cyan
$sources = Invoke-RestMethod -Uri "https://guigtpwxlqwueylbbcpx.supabase.co/rest/v1/team_sources?select=id,name,source_type,source_config,is_active&order=created_at.desc" -Headers $headers
foreach ($s in $sources) {
    Write-Host "`n$($s.name) [$($s.source_type)]" -ForegroundColor Yellow
    Write-Host "  ID: $($s.id.Substring(0,8))..."
    Write-Host "  Active: $($s.is_active)"
    Write-Host "  Config: $($s.source_config | ConvertTo-Json -Compress)"
}
