# Apply Migration 016 Directly to Remote Supabase
# This bypasses local development and applies migration directly to your Supabase project

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Apply Migration to Remote Supabase" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Step 1: Create migration file
Write-Host "`n1. Creating migration file..." -ForegroundColor Yellow
.\create_migration_016.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create migration" -ForegroundColor Red
    exit 1
}

# Step 2: Login to Supabase (if not already logged in)
Write-Host "`n2. Checking Supabase login..." -ForegroundColor Yellow
npx supabase login

# Step 3: Link to project (if not already linked)
Write-Host "`n3. Linking to Supabase project..." -ForegroundColor Yellow
npx supabase link --project-ref guigtpwxlqwueylbbcpx

# Step 4: Push migration to remote
Write-Host "`n4. Pushing migration to remote Supabase..." -ForegroundColor Yellow
Write-Host "   This applies the migration directly to your production database" -ForegroundColor Gray

npx supabase db push

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Migration applied successfully!" -ForegroundColor Green
    Write-Host "`nVerify in Supabase Dashboard:" -ForegroundColor Yellow
    Write-Host "  https://supabase.com/dashboard/project/guigtpwxlqwueylbbcpx/editor" -ForegroundColor White
    Write-Host "`nYou should see these new tables:" -ForegroundColor Gray
    Write-Host "  - teams" -ForegroundColor White
    Write-Host "  - team_members" -ForegroundColor White
    Write-Host "  - batch_claims" -ForegroundColor White
    Write-Host "  - team_notifications" -ForegroundColor White
} else {
    Write-Host "`n❌ Migration failed" -ForegroundColor Red
    Write-Host "   Check error messages above" -ForegroundColor Yellow
}
