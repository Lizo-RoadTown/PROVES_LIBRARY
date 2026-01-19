$apikey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd1aWd0cHd4bHF3dWV5bGJiY3B4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODUyNzE2NiwiZXhwIjoyMDg0MTAzMTY2fQ.NR2qUIIBSppOOzh_ArLTpQuSaKt9BmFv0KtAQ-ILcFw"

$headers = @{
    "apikey" = $apikey
    "Authorization" = "Bearer $apikey"
}

Write-Host "=== Recent Crawl Jobs ===" -ForegroundColor Cyan
$jobs = Invoke-RestMethod -Uri "https://guigtpwxlqwueylbbcpx.supabase.co/rest/v1/crawl_jobs?select=id,source_id,status,error_message,created_at&order=created_at.desc&limit=5" -Headers $headers
$jobs | Format-Table -Property @{L='ID';E={$_.id.Substring(0,8)}}, status, error_message, created_at

if ($jobs.Count -gt 0) {
    $sourceId = $jobs[0].source_id
    Write-Host "`n=== Source Config for Latest Job ===" -ForegroundColor Cyan
    $source = Invoke-RestMethod -Uri "https://guigtpwxlqwueylbbcpx.supabase.co/rest/v1/team_sources?select=name,source_type,source_config&id=eq.$sourceId" -Headers $headers
    Write-Host "Name: $($source.name)"
    Write-Host "Type: $($source.source_type)"
    Write-Host "Config: $($source.source_config | ConvertTo-Json -Compress)"
}
