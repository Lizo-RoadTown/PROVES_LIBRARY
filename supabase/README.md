# PROVES Library - Database Migrations

## Quick Start

```powershell
cd supabase
.\migrate.ps1           # Apply pending migrations
.\migrate.ps1 -Status   # Check what's applied
.\migrate.ps1 -File 031 # Apply specific migration
```

That's it. One script, three use cases.

---

## How It Works

1. **Migrations live in:** `supabase/migrations/*.sql`
2. **Naming:** `NNN_description.sql` (e.g., `031_add_executive_access.sql`)
3. **The script:**
   - Links to Supabase project (auto)
   - Runs `npx supabase db push`
   - Supabase tracks what's applied

---

## Creating a New Migration

1. Create file: `supabase/migrations/NNN_your_description.sql`
2. Write your SQL with `BEGIN;` and `COMMIT;`
3. Run: `.\migrate.ps1`

Example template:
```sql
-- Migration NNN: Description
-- Purpose: What this migration does

BEGIN;

-- Your SQL here
CREATE TABLE IF NOT EXISTS ...

-- Verification
DO $$
BEGIN
    RAISE NOTICE 'Migration NNN complete';
END $$;

COMMIT;
```

---

## Fallback: Manual Apply

If the script fails, you can always paste SQL directly:

1. Open: https://supabase.com/dashboard/project/guigtpwxlqwueylbbcpx/sql/new
2. Paste migration SQL
3. Click Run

---

## Current Migrations

| # | Name | Description |
|---|------|-------------|
| 000 | initial_base_schema | Core tables |
| 001-015 | (various) | Original pipeline tables |
| 016-022 | (various) | Dashboard + review features |
| 023 | organizations_and_provenance | Multi-org support |
| 024-030 | (various) | Graph API, seeds |
| **031** | **add_executive_access** | User profiles + stackable capabilities |
| **032** | **fix_security_warnings** | RLS, search_path, security fixes |

---

## Requirements

- Node.js (for npx)
- Supabase account with project access
- First time: `npx supabase login`

---

## Troubleshooting

**"Not logged in"**
```powershell
npx supabase login
```

**"Migration already applied"**
- Supabase tracks applied migrations, so running twice is safe

**"Syntax error"**
- Check your SQL file
- Try: `.\migrate.ps1 -File NNN` to apply just that one

**"Permission denied"**
- Make sure you're logged into the right Supabase account
