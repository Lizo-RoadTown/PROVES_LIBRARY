# Apply All PROVES Migrations to Supabase

**Purpose:** Consolidate all database tables into Supabase (single database)

**Date:** 2026-01-15

---

## What This Does

Migrates all production tables from Neon to Supabase:

### Production Pipeline Tables (Migrations 001-015)
- `core_entities` - Verified library entities
- `staging_extractions` - Pending extractions
- `raw_snapshots` - Original extracted data
- `validation_decisions` - Review history
- `knowledge_enrichment` - Dimensional + standard mappings
- `improvement_suggestions` - Agent suggestions
- `error_logs` - Pipeline errors
- `urls_to_process` - Source URLs
- And 10+ more tables...

### Dashboard Tables (Migration 016)
- `teams` - University/lab accounts
- `team_members` - Engineers
- `batch_claims` - Claim tracking
- `team_notifications` - Alerts

**Total:** ~25 tables, all in one Supabase database

---

## Instructions

### Step 1: Go to Supabase SQL Editor

https://supabase.com/dashboard/project/guigtpwxlqwueylbbcpx/sql/new

### Step 2: Run Migrations in Order

**Option A: Run Consolidated Migration (Recommended)**

Open a new SQL Editor tab and paste the entire contents of:
- `supabase/consolidated_migrations_001_to_015.sql`

This single file contains all migrations 001-015 in the correct order, already fixed for fresh database setup.

**Option B: Run Individual Migrations**

If you prefer to run them separately, copy and paste each migration file into the SQL Editor and run them **in order**:

1. `001_add_lineage_and_relationships.sql`
2. `002_create_urls_to_process.sql`
3. `003_add_notion_integration.sql`
4. `003b_add_missing_triggers.sql`
5. `004_update_evidence_types.sql` ⚠️ (Modified for fresh DB)
6. `005_add_review_tracking.sql`
7. `005b_fix_review_decision_constraint.sql`
8. `006_add_improvement_suggestions.sql`
9. `007_add_error_logging.sql`
10. `008_add_dimensional_canonicalization.sql`
11. `009_add_verified_knowledge_layer.sql`
12. `010_add_knowledge_epistemics_sidecar.sql`
13. `011_rollback_migration_008.sql`
14. `012_enhance_human_approval_workflow.sql`
15. `013_add_promotion_tracking.sql`
16. `014_add_missing_entity_types.sql`
17. `015_add_standard_mapping_enrichment.sql`

**Note:** Migration 016 (teams_and_batch_claims) was already applied!
**Note:** Migration 004 has been fixed to work with fresh databases (no data migration needed)

### Step 3: Verify Tables

After running all migrations, check Table Editor:

https://supabase.com/dashboard/project/guigtpwxlqwueylbbcpx/editor

You should see ~25 tables including:
- core_entities
- staging_extractions
- raw_snapshots
- validation_decisions
- knowledge_enrichment
- teams
- team_members
- batch_claims
- And more...

---

## Alternative: Automated Apply (Requires Supabase CLI)

If you have Supabase CLI set up with Docker, you can apply all at once:

```powershell
npx supabase db reset
```

This will apply all migrations in `supabase/migrations/` folder in order.

---

## After Migration Complete

### Update Environment Variables

Change your `.env` to use Supabase instead of Neon:

```bash
# OLD (Neon)
# NEON_DATABASE_URL=postgresql://neondb_owner:...@ep-empty-morning-af4l9ocx-pooler.c-2.us-west-2.aws.neon.tech/neondb

# NEW (Supabase)
DATABASE_URL=postgresql://postgres.guigtpwxlqwueylbbcpx:[YOUR-PASSWORD]@aws-0-us-west-2.pooler.supabase.com:6543/postgres?pgbouncer=true
DIRECT_URL=postgresql://postgres.guigtpwxlqwueylbbcpx:[YOUR-PASSWORD]@aws-0-us-west-2.pooler.supabase.com:5432/postgres
```

Replace `[YOUR-PASSWORD]` with your actual Supabase database password.

### Update Production Code

Find and replace in your codebase:

```python
# OLD
conn = psycopg2.connect(os.getenv('NEON_DATABASE_URL'))

# NEW
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
```

Or better yet, use a single variable name:

```python
# Add to .env
PROVES_DATABASE_URL=<your-supabase-url>

# In code
conn = psycopg2.connect(os.getenv('PROVES_DATABASE_URL'))
```

---

## Benefits of Single Database

✓ **Simpler architecture** - One database to manage
✓ **No data transfer** - Dashboard and agents use same tables
✓ **Real-time features** - Supabase real-time for live updates
✓ **Row-level security** - Team isolation built-in
✓ **Better backups** - Supabase automated backups
✓ **Unified access control** - One set of credentials

---

## Next Steps

1. Apply migrations 001-015 to Supabase (see Step 2 above)
2. Update `.env` to use Supabase URLs
3. Test extraction agents with new database
4. Build Next.js dashboard
5. Deploy to Vercel

---

**Status:** Ready to apply migrations - all migration files copied to `supabase/migrations/`
