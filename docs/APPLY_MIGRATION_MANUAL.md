# Apply Migration 016 Manually (No Docker Required)

**Purpose:** Apply the teams/batch_claims migration directly via Supabase Dashboard SQL Editor

**Use this if:** You don't want to install Docker or use the Supabase CLI

---

## Steps

### 1. Generate the Migration SQL

Run this PowerShell command to create the migration file:

```powershell
.\create_migration_016.ps1
```

This creates: `supabase\migrations\<timestamp>_teams_and_batch_claims.sql`

### 2. Copy the SQL

Open the migration file and copy all the SQL content.

### 3. Open Supabase SQL Editor

1. Go to https://supabase.com/dashboard/project/guigtpwxlqwueylbbcpx
2. Click **"SQL Editor"** in the left sidebar
3. Click **"New query"**

### 4. Paste and Run

1. Paste the entire migration SQL into the editor
2. Click **"Run"** (or press Cmd/Ctrl + Enter)
3. Wait for completion (should take 1-2 seconds)

### 5. Verify Tables Created

1. Click **"Table Editor"** in left sidebar
2. You should see 4 new tables:
   - `teams`
   - `team_members`
   - `batch_claims`
   - `team_notifications`

3. Click on each table to verify columns and structure

### 6. Test Row-Level Security

The migration includes RLS policies for team isolation. To test:

1. Click **"Authentication"** > **"Policies"** in sidebar
2. You should see policies for each table (teams_select_policy, etc.)

---

## What This Migration Creates

### Tables

1. **teams** - University/lab accounts
   - Tracks max concurrent claims, timeouts
   - Stores team stats (approved, rejected counts)

2. **team_members** - Engineers within teams
   - Links to Supabase auth users
   - Roles: admin, member, viewer
   - Individual stats per member

3. **batch_claims** - Claim tracking
   - Arrays of extraction IDs
   - Auto-expiration based on timeout
   - Status: active, completed, expired, released

4. **team_notifications** - In-app notifications
   - Batch expiring/expired alerts
   - New extraction notifications
   - Team invites

### Functions

- `expire_batch_claims()` - Auto-expire old claims
- `notify_batch_expiring()` - Alert 15 min before expiration
- `update_updated_at()` - Timestamp trigger

### Views

- `active_batch_claims` - Active claims with team/member details
- `team_stats` - Summary statistics per team

### Security

- Row-level security enabled on all tables
- Team members can only see their team's data
- Admins can manage team members
- Members can create/update their own claims

---

## Troubleshooting

### Error: "permission denied for schema public"

**Fix:** You're not logged in as the project owner. Make sure you're signed into the correct Supabase account.

### Error: "relation already exists"

**Fix:** The migration was already applied. Check Table Editor to see if tables exist.

### Error: "syntax error at or near..."

**Fix:** The migration SQL might have been corrupted. Regenerate it with `.\create_migration_016.ps1`

---

## Next Steps

After migration is applied:

1. **Create a test team** - Add a team in Table Editor or via SQL
2. **Set up Supabase Auth** - Configure email authentication
3. **Build the dashboard** - Convert Figma design to Next.js
4. **Connect to Supabase** - Use Supabase client in dashboard

See: `docs/CURATION_DASHBOARD_REQUIREMENTS.md` for full feature list
