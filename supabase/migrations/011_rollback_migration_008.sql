-- ============================================================================
-- Migration 011: Rollback Migration 008 (Dimensional Canonicalization)
-- ============================================================================
-- Purpose: Remove old dimensional metadata framework to avoid confusion
--          with new epistemic framework (migration 010)
-- Date: 2025-12-30
-- ============================================================================

BEGIN;

-- ============================================================================
-- PART 1: DROP VIEWS CREATED BY MIGRATION 008
-- ============================================================================

DROP VIEW IF EXISTS episodic_temporal_knowledge CASCADE;
DROP VIEW IF EXISTS embodied_knowledge_at_risk CASCADE;
DROP VIEW IF EXISTS dimensional_quality_dashboard CASCADE;

-- ============================================================================
-- PART 2: DROP FUNCTIONS AND TRIGGERS FROM MIGRATION 008
-- ============================================================================

DROP TRIGGER IF EXISTS trigger_check_dimensional_review ON staging_extractions;
DROP FUNCTION IF EXISTS check_dimensional_review_needed() CASCADE;
DROP FUNCTION IF EXISTS calculate_dimensional_completeness(NUMERIC, NUMERIC, NUMERIC, NUMERIC, NUMERIC, NUMERIC) CASCADE;

-- ============================================================================
-- PART 3: DROP INDEXES CREATED BY MIGRATION 008
-- ============================================================================

DROP INDEX IF EXISTS idx_extractions_low_formalizability;
DROP INDEX IF EXISTS idx_extractions_embodied_knowledge;
DROP INDEX IF EXISTS idx_extractions_needs_dimensional_review;
DROP INDEX IF EXISTS idx_extractions_dimensional_profile;

DROP INDEX IF EXISTS idx_episodes_components;
DROP INDEX IF EXISTS idx_episodes_snapshot;
DROP INDEX IF EXISTS idx_episodes_key;
DROP INDEX IF EXISTS idx_episodes_type;

DROP INDEX IF EXISTS idx_episode_links_extraction;
DROP INDEX IF EXISTS idx_episode_links_episode;

-- ============================================================================
-- PART 4: DROP LINKING TABLE (episode_extraction_links)
-- ============================================================================

DROP TABLE IF EXISTS episode_extraction_links CASCADE;

-- Note: We're keeping episodic_entities table because it's still useful
-- for migration 010's episode_id foreign key in knowledge_epistemics

-- ============================================================================
-- PART 5: DROP COLUMNS FROM staging_extractions
-- ============================================================================

-- Drop dimensional metadata columns
ALTER TABLE staging_extractions DROP COLUMN IF EXISTS knowledge_form CASCADE;
ALTER TABLE staging_extractions DROP COLUMN IF EXISTS knowledge_form_confidence CASCADE;
ALTER TABLE staging_extractions DROP COLUMN IF EXISTS knowledge_form_reasoning CASCADE;

ALTER TABLE staging_extractions DROP COLUMN IF EXISTS contact_level CASCADE;
ALTER TABLE staging_extractions DROP COLUMN IF EXISTS contact_confidence CASCADE;
ALTER TABLE staging_extractions DROP COLUMN IF EXISTS contact_reasoning CASCADE;

ALTER TABLE staging_extractions DROP COLUMN IF EXISTS directionality CASCADE;
ALTER TABLE staging_extractions DROP COLUMN IF EXISTS directionality_confidence CASCADE;
ALTER TABLE staging_extractions DROP COLUMN IF EXISTS directionality_reasoning CASCADE;

ALTER TABLE staging_extractions DROP COLUMN IF EXISTS temporality CASCADE;
ALTER TABLE staging_extractions DROP COLUMN IF EXISTS temporality_confidence CASCADE;
ALTER TABLE staging_extractions DROP COLUMN IF EXISTS temporality_reasoning CASCADE;

ALTER TABLE staging_extractions DROP COLUMN IF EXISTS formalizability CASCADE;
ALTER TABLE staging_extractions DROP COLUMN IF EXISTS formalizability_confidence CASCADE;
ALTER TABLE staging_extractions DROP COLUMN IF EXISTS formalizability_reasoning CASCADE;

ALTER TABLE staging_extractions DROP COLUMN IF EXISTS carrier CASCADE;
ALTER TABLE staging_extractions DROP COLUMN IF EXISTS carrier_confidence CASCADE;
ALTER TABLE staging_extractions DROP COLUMN IF EXISTS carrier_reasoning CASCADE;

-- Drop review flags
ALTER TABLE staging_extractions DROP COLUMN IF EXISTS needs_dimensional_review CASCADE;
ALTER TABLE staging_extractions DROP COLUMN IF EXISTS dimensional_review_reason CASCADE;
ALTER TABLE staging_extractions DROP COLUMN IF EXISTS dimensional_completeness CASCADE;

-- ============================================================================
-- PART 6: DROP COLUMNS FROM core_entities (from migration 009)
-- ============================================================================

-- Drop dimensional metadata columns from verified layer
ALTER TABLE core_entities DROP COLUMN IF EXISTS knowledge_form CASCADE;
ALTER TABLE core_entities DROP COLUMN IF EXISTS knowledge_form_confidence CASCADE;
ALTER TABLE core_entities DROP COLUMN IF EXISTS knowledge_form_reasoning CASCADE;

ALTER TABLE core_entities DROP COLUMN IF EXISTS contact_level CASCADE;
ALTER TABLE core_entities DROP COLUMN IF EXISTS contact_confidence CASCADE;
ALTER TABLE core_entities DROP COLUMN IF EXISTS contact_reasoning CASCADE;

ALTER TABLE core_entities DROP COLUMN IF EXISTS directionality CASCADE;
ALTER TABLE core_entities DROP COLUMN IF EXISTS directionality_confidence CASCADE;
ALTER TABLE core_entities DROP COLUMN IF EXISTS directionality_reasoning CASCADE;

ALTER TABLE core_entities DROP COLUMN IF EXISTS temporality CASCADE;
ALTER TABLE core_entities DROP COLUMN IF EXISTS temporality_confidence CASCADE;
ALTER TABLE core_entities DROP COLUMN IF EXISTS temporality_reasoning CASCADE;

ALTER TABLE core_entities DROP COLUMN IF EXISTS formalizability CASCADE;
ALTER TABLE core_entities DROP COLUMN IF EXISTS formalizability_confidence CASCADE;
ALTER TABLE core_entities DROP COLUMN IF EXISTS formalizability_reasoning CASCADE;

ALTER TABLE core_entities DROP COLUMN IF EXISTS carrier CASCADE;
ALTER TABLE core_entities DROP COLUMN IF EXISTS carrier_confidence CASCADE;
ALTER TABLE core_entities DROP COLUMN IF EXISTS carrier_reasoning CASCADE;

-- ============================================================================
-- PART 7: DROP TABLES FROM MIGRATION 009 (dimensional adjustments)
-- ============================================================================

DROP VIEW IF EXISTS recent_dimensional_corrections CASCADE;
DROP TABLE IF EXISTS dimensional_adjustment_history CASCADE;

-- ============================================================================
-- PART 8: UPDATE VIEWS THAT REFERENCED OLD FIELDS
-- ============================================================================

-- Recreate complete_epistemic_profile without migration 008 fields
DROP VIEW IF EXISTS complete_epistemic_profile CASCADE;

CREATE OR REPLACE VIEW complete_epistemic_profile AS
SELECT
  -- Extraction basics
  se.extraction_id,
  se.candidate_key,
  se.candidate_type,
  se.ecosystem,
  se.status,
  se.confidence_score AS extraction_confidence,

  -- Epistemic metadata (migration 010 only)
  ke.domain,
  ke.claim_summary,
  ke.observer_id,
  ke.observer_type,
  ke.contact_mode,
  ke.contact_strength,
  ke.signal_type,
  ke.pattern_storage,
  ke.representation_media,
  ke.episode_id,
  ke.sequence_role,
  ke.dependencies,
  ke.validity_conditions,
  ke.assumptions,
  ke.scope,
  ke.observed_at,
  ke.valid_from,
  ke.valid_to,
  ke.refresh_trigger,
  ke.staleness_risk,
  ke.author_id,
  ke.intent AS author_intent,
  ke.confidence AS epistemic_confidence,
  ke.uncertainty_notes,
  ke.reenactment_required,
  ke.practice_interval,
  ke.skill_transferability,
  ke.identified_loss_modes,

  -- Lineage
  se.snapshot_id,
  se.created_at,
  se.updated_at

FROM staging_extractions se
LEFT JOIN knowledge_epistemics ke ON se.extraction_id = ke.extraction_id;

COMMENT ON VIEW complete_epistemic_profile IS
  'Complete epistemic metadata from migration 010 checklist-oriented framework';

-- ============================================================================
-- PART 9: VALIDATION
-- ============================================================================

DO $$
DECLARE
  remaining_008_columns TEXT[];
BEGIN
  -- Check that migration 008 columns are gone
  SELECT ARRAY_AGG(column_name)
  INTO remaining_008_columns
  FROM information_schema.columns
  WHERE table_name = 'staging_extractions'
    AND column_name IN (
      'knowledge_form', 'contact_level', 'directionality',
      'temporality', 'formalizability', 'carrier',
      'needs_dimensional_review', 'dimensional_completeness'
    );

  IF array_length(remaining_008_columns, 1) > 0 THEN
    RAISE EXCEPTION 'Migration 008 columns still exist: %', array_to_string(remaining_008_columns, ', ');
  END IF;

  -- Check that migration 010 table still exists
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'knowledge_epistemics') THEN
    RAISE EXCEPTION 'Migration 010 table knowledge_epistemics is missing';
  END IF;

  -- Check that episodic_entities still exists (needed by migration 010)
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'episodic_entities') THEN
    RAISE EXCEPTION 'Table episodic_entities is missing (needed by migration 010)';
  END IF;

  RAISE NOTICE 'Migration 008 rollback completed successfully';
  RAISE NOTICE 'Removed: 23 columns, 3 views, 2 functions, 1 trigger, 1 table';
  RAISE NOTICE 'Kept: episodic_entities table (used by migration 010)';
  RAISE NOTICE 'Migration 010 (knowledge_epistemics) remains intact';
END $$;

COMMIT;

-- ============================================================================
-- POST-MIGRATION VERIFICATION QUERIES
-- ============================================================================

-- 1. Verify migration 008 columns are gone
-- SELECT column_name FROM information_schema.columns
-- WHERE table_name = 'staging_extractions'
--   AND column_name LIKE '%knowledge_form%'
--   OR column_name LIKE '%contact_level%'
--   OR column_name LIKE '%directionality%';

-- 2. Verify migration 010 table still exists
-- SELECT COUNT(*) FROM knowledge_epistemics;

-- 3. Verify complete_epistemic_profile view works
-- SELECT * FROM complete_epistemic_profile LIMIT 5;

-- 4. Check episodic_entities still exists
-- SELECT COUNT(*) FROM episodic_entities;
