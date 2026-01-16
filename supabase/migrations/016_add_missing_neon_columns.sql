-- ============================================================================
-- Migration 016: Add Missing Columns from Neon Database
-- ============================================================================
-- Purpose: Add columns that exist in Neon but are missing in Supabase
-- Date: 2026-01-15
-- Note: Required for data migration from Neon to Supabase
-- ============================================================================

BEGIN;

-- ============================================================================
-- RAW_SNAPSHOTS: Add missing columns
-- ============================================================================

ALTER TABLE raw_snapshots
  ADD COLUMN IF NOT EXISTS source_type TEXT,
  ADD COLUMN IF NOT EXISTS ecosystem TEXT,
  ADD COLUMN IF NOT EXISTS content_hash TEXT,
  ADD COLUMN IF NOT EXISTS payload_size_bytes INTEGER,
  ADD COLUMN IF NOT EXISTS captured_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS captured_by_run_id UUID,
  ADD COLUMN IF NOT EXISTS source_commit_sha TEXT,
  ADD COLUMN IF NOT EXISTS source_etag TEXT,
  ADD COLUMN IF NOT EXISTS source_last_modified TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'captured',
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

-- Add index for content deduplication
CREATE INDEX IF NOT EXISTS idx_snapshots_content_hash ON raw_snapshots(content_hash);

-- ============================================================================
-- STAGING_EXTRACTIONS: Check for any missing columns
-- ============================================================================
-- (The staging_extractions table should already match, but let's ensure)

-- Add any missing columns that might be in Neon
ALTER TABLE staging_extractions
  ADD COLUMN IF NOT EXISTS source_url TEXT,
  ADD COLUMN IF NOT EXISTS source_type TEXT;

COMMIT;

-- ============================================================================
-- VALIDATION
-- ============================================================================

DO $$
BEGIN
  -- Verify columns were added
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'raw_snapshots' AND column_name = 'content_hash'
  ) THEN
    RAISE EXCEPTION 'Column content_hash was not added to raw_snapshots';
  END IF;

  RAISE NOTICE 'Migration 016 completed successfully ✓';
  RAISE NOTICE '  - Added missing columns to raw_snapshots for Neon compatibility';
END $$;
