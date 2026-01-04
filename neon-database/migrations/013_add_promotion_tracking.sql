-- Migration 013: Add Promotion Tracking to staging_extractions
-- Date: 2026-01-03
-- Purpose: Track when extractions are promoted to core_entities to enable idempotent batch processing

BEGIN;

-- ============================================================================
-- PART 1: ADD PROMOTION TRACKING COLUMNS
-- ============================================================================

-- Track when extraction was promoted to core
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
    promoted_at TIMESTAMPTZ;

-- Link to the created/merged core entity
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
    promoted_to_entity_id UUID REFERENCES core_entities(id) ON DELETE SET NULL;

-- Track promotion action type for analytics
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
    promotion_action TEXT CHECK (promotion_action IN ('created', 'merged', 'skipped', 'error'));

-- Optional: Store error details if promotion failed
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
    promotion_error TEXT;

-- ============================================================================
-- PART 2: ADD INDEXES FOR QUERIES
-- ============================================================================

-- Index for finding unpromoted accepted extractions
-- Note: Using enum value directly instead of casting to text for IMMUTABLE requirement
CREATE INDEX IF NOT EXISTS idx_staging_promoted_status
    ON staging_extractions(status, promoted_at)
    WHERE promoted_at IS NULL;

-- Index for promoted extractions
CREATE INDEX IF NOT EXISTS idx_staging_promoted_at
    ON staging_extractions(promoted_at DESC)
    WHERE promoted_at IS NOT NULL;

-- Index for linking back to core entity
CREATE INDEX IF NOT EXISTS idx_staging_promoted_to_entity
    ON staging_extractions(promoted_to_entity_id)
    WHERE promoted_to_entity_id IS NOT NULL;

-- ============================================================================
-- PART 3: ADD COMMENTS
-- ============================================================================

COMMENT ON COLUMN staging_extractions.promoted_at IS
    'Timestamp when this extraction was promoted to core_entities. NULL = not yet promoted.';

COMMENT ON COLUMN staging_extractions.promoted_to_entity_id IS
    'Foreign key to the core_entities entry created or merged during promotion. NULL if not promoted.';

COMMENT ON COLUMN staging_extractions.promotion_action IS
    'Action taken during promotion: created (new entity), merged (with existing), skipped (already promoted), error (promotion failed)';

COMMENT ON COLUMN staging_extractions.promotion_error IS
    'Error message if promotion failed. NULL if successful or not attempted.';

-- ============================================================================
-- PART 4: HELPER VIEW FOR UNPROMOTED EXTRACTIONS
-- ============================================================================

-- View: Accepted extractions awaiting promotion
CREATE OR REPLACE VIEW extractions_awaiting_promotion AS
SELECT
    e.extraction_id,
    e.candidate_key,
    e.candidate_type,
    e.ecosystem,
    e.confidence_score,
    e.status,
    e.created_at,
    EXTRACT(EPOCH FROM (NOW() - e.created_at)) / 3600 as hours_since_extraction,
    d.decided_at as approved_at,
    EXTRACT(EPOCH FROM (NOW() - d.decided_at)) / 3600 as hours_since_approval,
    d.decided_by as approved_by
FROM staging_extractions e
LEFT JOIN validation_decisions d ON e.latest_decision_id = d.decision_id
WHERE e.promoted_at IS NULL
  AND e.promotion_action IS NULL
ORDER BY e.created_at ASC;

COMMENT ON VIEW extractions_awaiting_promotion IS
    'Accepted extractions that have not yet been promoted to core_entities';

-- View: Promotion statistics
CREATE OR REPLACE VIEW promotion_statistics AS
SELECT
    COUNT(*) FILTER (WHERE promoted_at IS NOT NULL) as total_promoted,
    COUNT(*) FILTER (WHERE promotion_action = 'created') as entities_created,
    COUNT(*) FILTER (WHERE promotion_action = 'merged') as entities_merged,
    COUNT(*) FILTER (WHERE promotion_action = 'error') as promotion_errors,
    COUNT(*) FILTER (WHERE promoted_at IS NULL) as awaiting_promotion,
    MIN(promoted_at) as first_promotion,
    MAX(promoted_at) as latest_promotion,
    AVG(EXTRACT(EPOCH FROM (promoted_at - created_at))) / 3600 as avg_hours_to_promotion
FROM staging_extractions;

COMMENT ON VIEW promotion_statistics IS
    'Overall statistics on extraction promotion status';

-- ============================================================================
-- PART 5: VALIDATION
-- ============================================================================

DO $$
BEGIN
    -- Verify columns exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'staging_extractions' AND column_name = 'promoted_at'
    ) THEN
        RAISE EXCEPTION 'Column promoted_at was not added to staging_extractions';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'staging_extractions' AND column_name = 'promoted_to_entity_id'
    ) THEN
        RAISE EXCEPTION 'Column promoted_to_entity_id was not added to staging_extractions';
    END IF;

    -- Verify views exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_views WHERE viewname = 'extractions_awaiting_promotion'
    ) THEN
        RAISE EXCEPTION 'View extractions_awaiting_promotion was not created';
    END IF;

    RAISE NOTICE 'Migration 013 completed successfully ✓';
    RAISE NOTICE '  - Added promotion tracking columns to staging_extractions';
    RAISE NOTICE '  - Created indexes for promotion queries';
    RAISE NOTICE '  - Created helper views for monitoring promotion status';
END $$;

COMMIT;
