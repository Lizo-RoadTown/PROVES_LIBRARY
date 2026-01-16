# Create Migration 016: Teams and Batch Claims for Curation Dashboard
# This migration sets up the multi-team curation system in Supabase

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Create Migration 016" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Check if Supabase is initialized
if (-not (Test-Path "supabase\config.toml")) {
    Write-Host "`n❌ Supabase not initialized" -ForegroundColor Red
    Write-Host "   Run: npx supabase init" -ForegroundColor Yellow
    exit 1
}

# Create migration file
Write-Host "`nCreating migration file..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$migrationName = "${timestamp}_teams_and_batch_claims"
$migrationPath = "supabase\migrations\${migrationName}.sql"

# Migration SQL content
$migrationSQL = @"
-- Migration 016: Teams and Batch Claims for Curation Dashboard
-- Purpose: Multi-team curation system with batch claiming and notifications
-- Date: 2026-01-15

-- ============================================
-- TEAMS TABLE
-- ============================================
-- Each university/lab has a team account

CREATE TABLE IF NOT EXISTS teams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  institution TEXT NOT NULL,
  contact_email TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- Settings
  max_concurrent_claims INTEGER NOT NULL DEFAULT 10,
  claim_timeout_hours INTEGER NOT NULL DEFAULT 24,

  -- Stats (updated via triggers)
  total_extractions_assigned INTEGER NOT NULL DEFAULT 0,
  total_approved INTEGER NOT NULL DEFAULT 0,
  total_rejected INTEGER NOT NULL DEFAULT 0,

  CONSTRAINT valid_email CHECK (contact_email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
  CONSTRAINT positive_max_claims CHECK (max_concurrent_claims > 0),
  CONSTRAINT positive_timeout CHECK (claim_timeout_hours > 0)
);

CREATE INDEX idx_teams_institution ON teams(institution);
CREATE INDEX idx_teams_name ON teams(name);

COMMENT ON TABLE teams IS 'University/lab teams that curate their portion of the PROVES library';
COMMENT ON COLUMN teams.max_concurrent_claims IS 'Maximum number of batches a team can claim at once';
COMMENT ON COLUMN teams.claim_timeout_hours IS 'Hours before unclaimed batches auto-release';

-- ============================================
-- TEAM MEMBERS TABLE
-- ============================================
-- Individual engineers within each team

CREATE TABLE IF NOT EXISTS team_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  user_id UUID NOT NULL, -- References Supabase auth.users
  email TEXT NOT NULL,
  full_name TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'member',

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_active_at TIMESTAMPTZ,

  -- Stats
  total_claimed INTEGER NOT NULL DEFAULT 0,
  total_approved INTEGER NOT NULL DEFAULT 0,
  total_rejected INTEGER NOT NULL DEFAULT 0,

  UNIQUE(team_id, user_id),
  UNIQUE(team_id, email),

  CONSTRAINT valid_role CHECK (role IN ('admin', 'member', 'viewer')),
  CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_team_members_team_id ON team_members(team_id);
CREATE INDEX idx_team_members_user_id ON team_members(user_id);
CREATE INDEX idx_team_members_email ON team_members(email);

COMMENT ON TABLE team_members IS 'Individual engineers who curate extractions';
COMMENT ON COLUMN team_members.role IS 'admin = manage team, member = curate, viewer = read-only';

-- ============================================
-- BATCH CLAIMS TABLE
-- ============================================
-- Tracks which team has claimed which batch of extractions

CREATE TABLE IF NOT EXISTS batch_claims (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  claimed_by UUID NOT NULL REFERENCES team_members(id) ON DELETE CASCADE,

  -- Batch metadata
  batch_size INTEGER NOT NULL,
  extraction_ids UUID[] NOT NULL, -- Array of staging_extraction IDs

  -- Timestamps
  claimed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL,
  completed_at TIMESTAMPTZ,

  -- Progress tracking
  reviewed_count INTEGER NOT NULL DEFAULT 0,
  approved_count INTEGER NOT NULL DEFAULT 0,
  rejected_count INTEGER NOT NULL DEFAULT 0,

  -- Status
  status TEXT NOT NULL DEFAULT 'active',

  CONSTRAINT valid_batch_size CHECK (batch_size > 0),
  CONSTRAINT valid_reviewed_count CHECK (reviewed_count >= 0 AND reviewed_count <= batch_size),
  CONSTRAINT valid_status CHECK (status IN ('active', 'completed', 'expired', 'released'))
);

CREATE INDEX idx_batch_claims_team_id ON batch_claims(team_id);
CREATE INDEX idx_batch_claims_claimed_by ON batch_claims(claimed_by);
CREATE INDEX idx_batch_claims_status ON batch_claims(status);
CREATE INDEX idx_batch_claims_expires_at ON batch_claims(expires_at) WHERE status = 'active';

COMMENT ON TABLE batch_claims IS 'Tracks batch claims with timeout and auto-release';
COMMENT ON COLUMN batch_claims.extraction_ids IS 'Array of staging_extraction IDs in this batch';
COMMENT ON COLUMN batch_claims.expires_at IS 'Auto-release if not completed by this time';

-- ============================================
-- TEAM NOTIFICATIONS TABLE
-- ============================================
-- In-app notifications for teams

CREATE TABLE IF NOT EXISTS team_notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  recipient_id UUID REFERENCES team_members(id) ON DELETE CASCADE, -- NULL = all team members

  -- Notification content
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  link TEXT, -- Optional link to relevant page

  -- Metadata
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  read_at TIMESTAMPTZ,

  CONSTRAINT valid_type CHECK (type IN (
    'batch_expiring',
    'batch_expired',
    'new_extractions',
    'extraction_approved',
    'extraction_rejected',
    'team_invite',
    'system_announcement'
  ))
);

CREATE INDEX idx_team_notifications_team_id ON team_notifications(team_id);
CREATE INDEX idx_team_notifications_recipient_id ON team_notifications(recipient_id);
CREATE INDEX idx_team_notifications_unread ON team_notifications(team_id, read_at) WHERE read_at IS NULL;
CREATE INDEX idx_team_notifications_created_at ON team_notifications(created_at DESC);

COMMENT ON TABLE team_notifications IS 'In-app notifications for team members';

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS on all tables
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE batch_claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_notifications ENABLE ROW LEVEL SECURITY;

-- Teams: Members can read their own team
CREATE POLICY teams_select_policy ON teams
  FOR SELECT
  USING (
    id IN (
      SELECT team_id FROM team_members WHERE user_id = auth.uid()
    )
  );

-- Teams: Only admins can update team settings
CREATE POLICY teams_update_policy ON teams
  FOR UPDATE
  USING (
    id IN (
      SELECT team_id FROM team_members WHERE user_id = auth.uid() AND role = 'admin'
    )
  );

-- Team Members: Members can read their team's members
CREATE POLICY team_members_select_policy ON team_members
  FOR SELECT
  USING (
    team_id IN (
      SELECT team_id FROM team_members WHERE user_id = auth.uid()
    )
  );

-- Team Members: Admins can insert/update/delete members
CREATE POLICY team_members_admin_policy ON team_members
  FOR ALL
  USING (
    team_id IN (
      SELECT team_id FROM team_members WHERE user_id = auth.uid() AND role = 'admin'
    )
  );

-- Batch Claims: Members can read their team's claims
CREATE POLICY batch_claims_select_policy ON batch_claims
  FOR SELECT
  USING (
    team_id IN (
      SELECT team_id FROM team_members WHERE user_id = auth.uid()
    )
  );

-- Batch Claims: Members can create claims for their team
CREATE POLICY batch_claims_insert_policy ON batch_claims
  FOR INSERT
  WITH CHECK (
    team_id IN (
      SELECT team_id FROM team_members WHERE user_id = auth.uid()
    )
  );

-- Batch Claims: Members can update their own claims
CREATE POLICY batch_claims_update_policy ON batch_claims
  FOR UPDATE
  USING (
    claimed_by IN (
      SELECT id FROM team_members WHERE user_id = auth.uid()
    )
  );

-- Team Notifications: Members can read their team's notifications
CREATE POLICY team_notifications_select_policy ON team_notifications
  FOR SELECT
  USING (
    team_id IN (
      SELECT team_id FROM team_members WHERE user_id = auth.uid()
    )
    AND (recipient_id IS NULL OR recipient_id IN (
      SELECT id FROM team_members WHERE user_id = auth.uid()
    ))
  );

-- Team Notifications: Members can mark their notifications as read
CREATE POLICY team_notifications_update_policy ON team_notifications
  FOR UPDATE
  USING (
    recipient_id IN (
      SELECT id FROM team_members WHERE user_id = auth.uid()
    )
  )
  WITH CHECK (
    -- Only allow updating read_at
    recipient_id IN (
      SELECT id FROM team_members WHERE user_id = auth.uid()
    )
  );

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Function to auto-expire batch claims
CREATE OR REPLACE FUNCTION expire_batch_claims()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $
BEGIN
  -- Expire active claims past their expiration time
  UPDATE batch_claims
  SET status = 'expired'
  WHERE status = 'active'
    AND expires_at < now();

  -- Create notifications for expired claims
  INSERT INTO team_notifications (team_id, recipient_id, type, title, message, link)
  SELECT
    bc.team_id,
    bc.claimed_by,
    'batch_expired',
    'Batch Claim Expired',
    'Your batch of ' || bc.batch_size || ' extractions has expired and been released.',
    '/pending'
  FROM batch_claims bc
  WHERE bc.status = 'expired'
    AND bc.expires_at >= now() - INTERVAL '1 minute' -- Only notify recently expired
    AND NOT EXISTS (
      SELECT 1 FROM team_notifications tn
      WHERE tn.recipient_id = bc.claimed_by
        AND tn.type = 'batch_expired'
        AND tn.created_at >= bc.expires_at
    );
END;
$;

COMMENT ON FUNCTION expire_batch_claims IS 'Auto-expire batch claims past their timeout';

-- Function to check batch expiring soon (15 minutes before expiration)
CREATE OR REPLACE FUNCTION notify_batch_expiring()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $
BEGIN
  INSERT INTO team_notifications (team_id, recipient_id, type, title, message, link)
  SELECT
    bc.team_id,
    bc.claimed_by,
    'batch_expiring',
    'Batch Expiring Soon',
    'Your batch of ' || bc.batch_size || ' extractions expires in 15 minutes.',
    '/pending'
  FROM batch_claims bc
  WHERE bc.status = 'active'
    AND bc.expires_at BETWEEN now() AND now() + INTERVAL '15 minutes'
    AND NOT EXISTS (
      SELECT 1 FROM team_notifications tn
      WHERE tn.recipient_id = bc.claimed_by
        AND tn.type = 'batch_expiring'
        AND tn.created_at >= bc.claimed_at
    );
END;
$;

COMMENT ON FUNCTION notify_batch_expiring IS 'Notify teams when batch claims are about to expire';

-- ============================================
-- TRIGGERS
-- ============================================

-- Update teams.updated_at on any change
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$;

CREATE TRIGGER teams_updated_at
  BEFORE UPDATE ON teams
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- ============================================
-- INITIAL DATA (Optional - for testing)
-- ============================================

-- Example team (you can delete this after testing)
INSERT INTO teams (name, institution, contact_email, max_concurrent_claims, claim_timeout_hours)
VALUES (
  'Example University Team',
  'Example University',
  'admin@example.edu',
  10,
  24
)
ON CONFLICT (name) DO NOTHING;

-- ============================================
-- VIEWS (Optional - for convenience)
-- ============================================

-- View: Active batch claims with member info
CREATE OR REPLACE VIEW active_batch_claims AS
SELECT
  bc.id,
  bc.team_id,
  t.name AS team_name,
  bc.claimed_by,
  tm.full_name AS claimed_by_name,
  bc.batch_size,
  bc.reviewed_count,
  bc.approved_count,
  bc.rejected_count,
  bc.claimed_at,
  bc.expires_at,
  EXTRACT(EPOCH FROM (bc.expires_at - now())) / 3600 AS hours_remaining
FROM batch_claims bc
JOIN teams t ON bc.team_id = t.id
JOIN team_members tm ON bc.claimed_by = tm.id
WHERE bc.status = 'active'
ORDER BY bc.expires_at ASC;

COMMENT ON VIEW active_batch_claims IS 'Active batch claims with team and member details';

-- View: Team stats summary
CREATE OR REPLACE VIEW team_stats AS
SELECT
  t.id,
  t.name,
  t.institution,
  t.total_extractions_assigned,
  t.total_approved,
  t.total_rejected,
  COALESCE(active_claims.count, 0) AS active_claims_count,
  COALESCE(active_claims.total_size, 0) AS active_extractions_count,
  COUNT(tm.id) AS member_count
FROM teams t
LEFT JOIN team_members tm ON t.id = tm.team_id
LEFT JOIN (
  SELECT
    team_id,
    COUNT(*) AS count,
    SUM(batch_size) AS total_size
  FROM batch_claims
  WHERE status = 'active'
  GROUP BY team_id
) active_claims ON t.id = active_claims.team_id
GROUP BY t.id, t.name, t.institution, t.total_extractions_assigned,
         t.total_approved, t.total_rejected,
         active_claims.count, active_claims.total_size;

COMMENT ON VIEW team_stats IS 'Summary statistics for each team';

-- ============================================
-- GRANTS (for service role and authenticated users)
-- ============================================

-- Grant access to authenticated users (via RLS policies)
GRANT SELECT, INSERT, UPDATE, DELETE ON teams TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON team_members TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON batch_claims TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON team_notifications TO authenticated;

-- Grant read access to views
GRANT SELECT ON active_batch_claims TO authenticated;
GRANT SELECT ON team_stats TO authenticated;

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION expire_batch_claims TO service_role;
GRANT EXECUTE ON FUNCTION notify_batch_expiring TO service_role;
"@

# Write migration file
$migrationSQL | Out-File -FilePath $migrationPath -Encoding utf8

Write-Host "✓ Created migration: $migrationPath" -ForegroundColor Green

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "  Next Steps" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

Write-Host "`n1. Review the migration file:" -ForegroundColor Yellow
Write-Host "   $migrationPath" -ForegroundColor White

Write-Host "`n2. Apply locally (after supabase start):" -ForegroundColor Yellow
Write-Host "   npx supabase db reset" -ForegroundColor White
Write-Host "   (This applies all migrations to local database)" -ForegroundColor Gray

Write-Host "`n3. Verify in Studio:" -ForegroundColor Yellow
Write-Host "   http://localhost:54323" -ForegroundColor White
Write-Host "   (Check Table Editor for new tables)" -ForegroundColor Gray

Write-Host "`n4. Push to remote Supabase:" -ForegroundColor Yellow
Write-Host "   npx supabase db push" -ForegroundColor White
Write-Host "   (Apply migration to production database)" -ForegroundColor Gray

Write-Host ""
