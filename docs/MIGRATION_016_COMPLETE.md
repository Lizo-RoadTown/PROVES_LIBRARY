# Migration 016 Complete ✓

**Date:** 2026-01-15
**Status:** Successfully Applied to Supabase

---

## What Was Created

### Tables (4)

1. **teams** - University/lab team accounts
   - Tracks team settings (max claims, timeout)
   - Stores aggregate stats (approved, rejected counts)
   - Row-level security enabled

2. **team_members** - Individual engineers within teams
   - Links to Supabase auth.users via user_id
   - Roles: admin, member, viewer
   - Individual performance stats

3. **batch_claims** - Batch claim tracking system
   - Arrays of extraction_ids
   - Auto-expiration with timeout
   - Status workflow: active → completed/expired/released

4. **team_notifications** - In-app notification system
   - Notification types: batch_expiring, batch_expired, new_extractions, etc.
   - Optional targeted delivery (recipient_id)
   - Read/unread tracking

### Functions (3)

1. **expire_batch_claims()** - Auto-expire old claims and create notifications
2. **notify_batch_expiring()** - Alert 15 minutes before expiration
3. **update_updated_at()** - Trigger function for timestamp updates

### Views (2)

1. **active_batch_claims** - Active claims with team/member details
2. **team_stats** - Summary statistics per team

### Security

- Row-level security (RLS) enabled on all tables
- Team members can only access their team's data
- Admins can manage team members
- Members can create/update their own batch claims

---

## Verify in Supabase Dashboard

1. **Table Editor:** https://supabase.com/dashboard/project/guigtpwxlqwueylbbcpx/editor
   - Should see: teams, team_members, batch_claims, team_notifications

2. **SQL Editor:** https://supabase.com/dashboard/project/guigtpwxlqwueylbbcpx/sql
   - Test queries on the new tables

3. **Authentication > Policies:**
   - Should see RLS policies for each table

---

## Example Data

The migration created one example team for testing:

```sql
-- Example team (can be deleted)
name: 'Example University Team'
institution: 'Example University'
contact_email: 'admin@example.edu'
max_concurrent_claims: 10
claim_timeout_hours: 24
```

---

## Next Steps

### 1. Set Up Authentication

Enable email authentication in Supabase:
- Dashboard → Authentication → Providers
- Enable Email provider
- Configure email templates (optional)

### 2. Create Your First Real Team

```sql
INSERT INTO teams (name, institution, contact_email, max_concurrent_claims, claim_timeout_hours)
VALUES (
  'Your University Name',
  'Your Institution',
  'your-email@university.edu',
  10,
  24
);
```

### 3. Add Team Members

After users sign up via Supabase Auth, add them to teams:

```sql
INSERT INTO team_members (team_id, user_id, email, full_name, role)
VALUES (
  '<team-uuid>',
  '<auth-user-uuid>',
  'engineer@university.edu',
  'Engineer Name',
  'admin'  -- or 'member' or 'viewer'
);
```

### 4. Build the Dashboard

Convert the Figma design to Next.js:
- Use components from `curation_dashboard/src/app/components/`
- Connect to Supabase using `@supabase/supabase-js`
- Implement batch claiming workflow
- Add extraction review interface

See: `docs/CURATION_DASHBOARD_REQUIREMENTS.md`

### 5. Set Up Scheduled Functions

For auto-expiring claims, set up Supabase Edge Functions or cron jobs:

```sql
-- Run every minute to expire old claims
SELECT expire_batch_claims();

-- Run every minute to send expiring-soon alerts
SELECT notify_batch_expiring();
```

---

## Database Schema Diagram

```
┌─────────────┐
│   teams     │
│             │
│ - id (PK)   │
│ - name      │
│ - settings  │
└──────┬──────┘
       │
       │ 1:N
       │
┌──────▼──────────┐         ┌─────────────────┐
│ team_members    │         │  batch_claims   │
│                 │         │                 │
│ - id (PK)       │◄────────│ - id (PK)       │
│ - team_id (FK)  │   N:1   │ - team_id (FK)  │
│ - user_id       │         │ - claimed_by    │
│ - role          │         │ - status        │
└─────────────────┘         └─────────────────┘
       │
       │ 1:N
       │
┌──────▼──────────────────┐
│ team_notifications      │
│                         │
│ - id (PK)               │
│ - team_id (FK)          │
│ - recipient_id (FK)     │
│ - type                  │
└─────────────────────────┘
```

---

## Migration File Location

Local: `supabase/migrations/20260115191105_teams_and_batch_claims.sql`

Remote: Applied to Supabase project `guigtpwxlqwueylbbcpx`

---

## Testing Queries

### Get all teams
```sql
SELECT * FROM teams;
```

### Get team members with their team name
```sql
SELECT
  tm.full_name,
  tm.email,
  tm.role,
  t.name AS team_name
FROM team_members tm
JOIN teams t ON tm.team_id = t.id;
```

### Get active batch claims
```sql
SELECT * FROM active_batch_claims;
```

### Get team statistics
```sql
SELECT * FROM team_stats;
```

### Test RLS (as authenticated user)
```sql
-- This will only show teams the current user belongs to
SELECT * FROM teams;
```

---

**Status:** Migration complete, database ready for dashboard development
