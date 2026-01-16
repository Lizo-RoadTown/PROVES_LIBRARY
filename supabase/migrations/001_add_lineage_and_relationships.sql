-- Migration: Add Lineage Tracking, Aliases, and Relationship Staging
-- Date: 2025-12-24
-- Purpose: Enable ID-based lineage, synonym tracking, and forward-looking relationship extraction

BEGIN;

-- ============================================================================
-- PART 1: LINEAGE TRACKING - Existing Tables
-- ============================================================================

-- 1.1: raw_snapshots - Add thread tracking
ALTER TABLE raw_snapshots ADD COLUMN IF NOT EXISTS
  fetched_by_thread_id TEXT;

CREATE INDEX IF NOT EXISTS idx_snapshots_thread
  ON raw_snapshots(fetched_by_thread_id);

COMMENT ON COLUMN raw_snapshots.fetched_by_thread_id IS
  'LangGraph thread ID that fetched this snapshot';

-- 1.2: staging_extractions - Add lineage verification fields
-- Evidence integrity
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS evidence_checksum TEXT;
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS evidence_byte_offset INTEGER;
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS evidence_byte_length INTEGER;

-- Lineage verification
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS lineage_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS lineage_verified_at TIMESTAMPTZ;
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS lineage_confidence NUMERIC(3,2);
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS lineage_verification_details JSONB;

-- Re-extraction tracking
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS extraction_attempt INTEGER DEFAULT 1;
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS is_reextraction BOOLEAN DEFAULT FALSE;
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS reextraction_reason TEXT;
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS original_extraction_id UUID REFERENCES staging_extractions(extraction_id);

-- Mandatory review
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS requires_mandatory_review BOOLEAN DEFAULT FALSE;
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS mandatory_review_reason TEXT;

-- Thread tracking
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS extracted_by_thread_id TEXT;

-- Add constraints
ALTER TABLE staging_extractions DROP CONSTRAINT IF EXISTS valid_lineage_confidence;
ALTER TABLE staging_extractions ADD CONSTRAINT valid_lineage_confidence
  CHECK (lineage_confidence IS NULL OR (lineage_confidence >= 0 AND lineage_confidence <= 1));

ALTER TABLE staging_extractions DROP CONSTRAINT IF EXISTS lineage_verified_requires_confidence;
ALTER TABLE staging_extractions ADD CONSTRAINT lineage_verified_requires_confidence
  CHECK (NOT lineage_verified OR lineage_confidence IS NOT NULL);

ALTER TABLE staging_extractions DROP CONSTRAINT IF EXISTS reextraction_must_reference_original;
ALTER TABLE staging_extractions ADD CONSTRAINT reextraction_must_reference_original
  CHECK (NOT is_reextraction OR original_extraction_id IS NOT NULL);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_extractions_lineage
  ON staging_extractions(lineage_verified, lineage_confidence);

CREATE INDEX IF NOT EXISTS idx_extractions_checksum
  ON staging_extractions(evidence_checksum);

CREATE INDEX IF NOT EXISTS idx_extractions_mandatory_review
  ON staging_extractions(requires_mandatory_review)
  WHERE requires_mandatory_review = TRUE;

CREATE INDEX IF NOT EXISTS idx_extractions_reextraction
  ON staging_extractions(is_reextraction, extraction_attempt);

CREATE INDEX IF NOT EXISTS idx_extractions_thread
  ON staging_extractions(extracted_by_thread_id);

-- Add comments
COMMENT ON COLUMN staging_extractions.evidence_checksum IS
  'SHA256 checksum of evidence raw_text for integrity verification';

COMMENT ON COLUMN staging_extractions.evidence_byte_offset IS
  'Byte offset where evidence quote appears in source snapshot payload';

COMMENT ON COLUMN staging_extractions.lineage_confidence IS
  '0.0 to 1.0 confidence that extraction can be traced to source (1.0 = perfect lineage)';

COMMENT ON COLUMN staging_extractions.extraction_attempt IS
  '1 = first attempt, 2 = re-extraction after low confidence';

-- 1.3: validation_decisions - Add lineage check results
ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS lineage_check_passed BOOLEAN DEFAULT TRUE;
ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS lineage_check_details JSONB;

CREATE INDEX IF NOT EXISTS idx_decisions_lineage_check
  ON validation_decisions(lineage_check_passed);

COMMENT ON COLUMN validation_decisions.lineage_check_passed IS
  'Whether lineage verification passed during validation';

-- ============================================================================
-- PART 2: NEW TABLES - Aliases and Relationships
-- ============================================================================

-- 2.1: entity_alias - Track synonyms and alternative names
CREATE TABLE IF NOT EXISTS entity_alias (
  alias_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- The alternative name/synonym
  alias_text TEXT NOT NULL,

  -- Canonical entity (once resolved)
  canonical_key TEXT,  -- Can be NULL if not yet resolved
  canonical_entity_id UUID REFERENCES staging_extractions(extraction_id),

  -- Source tracking
  source_snapshot_id UUID REFERENCES raw_snapshots(id) NOT NULL,
  evidence JSONB,  -- Supporting evidence for this alias

  -- Confidence
  confidence NUMERIC(3,2) CHECK (confidence >= 0 AND confidence <= 1),

  -- Context
  alias_type TEXT,  -- 'abbreviation', 'full_name', 'variant', 'typo', etc.
  ecosystem ecosystem_type,

  -- Resolution status
  resolution_status TEXT DEFAULT 'unresolved',  -- 'unresolved', 'resolved', 'rejected'

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  resolved_at TIMESTAMPTZ,
  resolved_by TEXT,  -- Agent or human who resolved

  CONSTRAINT unique_alias_per_snapshot UNIQUE(alias_text, source_snapshot_id)
);

CREATE INDEX idx_alias_text ON entity_alias(alias_text);
CREATE INDEX idx_alias_canonical ON entity_alias(canonical_key);
CREATE INDEX idx_alias_entity ON entity_alias(canonical_entity_id);
CREATE INDEX idx_alias_resolution ON entity_alias(resolution_status);
CREATE INDEX idx_alias_snapshot ON entity_alias(source_snapshot_id);

COMMENT ON TABLE entity_alias IS
  'Tracks synonyms and alternative names for entities (e.g., "MSP430" = "MSP430FR Microcontroller")';

COMMENT ON COLUMN entity_alias.alias_text IS
  'The alternative name/synonym found in documentation';

COMMENT ON COLUMN entity_alias.canonical_key IS
  'The canonical/official name once resolved';

COMMENT ON COLUMN entity_alias.resolution_status IS
  'unresolved = not matched to entity yet, resolved = matched, rejected = invalid alias';

-- 2.2: staging_relationships - Forward-looking relationship extraction
CREATE TABLE IF NOT EXISTS staging_relationships (
  rel_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Source tracking
  snapshot_id UUID REFERENCES raw_snapshots(id) NOT NULL,
  pipeline_run_id UUID REFERENCES pipeline_runs(id),

  -- Source entity (nullable - might not be extracted yet)
  src_extraction_id UUID REFERENCES staging_extractions(extraction_id),
  src_text_ref TEXT NOT NULL,  -- Text description of source
  src_type_hint TEXT,          -- Type hint if known ("component", "interface", etc.)

  -- Destination entity (nullable - might not be extracted yet)
  dst_extraction_id UUID REFERENCES staging_extractions(extraction_id),
  dst_text_ref TEXT NOT NULL,  -- Text description of destination
  dst_type_hint TEXT,          -- Type hint if known

  -- Relationship details
  rel_type TEXT NOT NULL,      -- "depends_on", "controls", "enables", etc.
  rel_direction TEXT DEFAULT 'directed',  -- 'directed', 'bidirectional', 'undirected'

  -- Confidence and evidence
  confidence NUMERIC(3,2) CHECK (confidence >= 0 AND confidence <= 1),
  evidence JSONB NOT NULL,     -- {"quote": "...", "context": "...", "diagram_ref": "..."}

  -- Resolution tracking
  resolution_status TEXT DEFAULT 'unresolved',
    -- 'unresolved' = Neither extraction ID resolved
    -- 'partially_resolved' = One side resolved
    -- 'resolved' = Both sides matched to extractions
    -- 'ambiguous' = Multiple possible matches
    -- 'rejected' = Invalid relationship

  resolution_attempts INTEGER DEFAULT 0,
  last_resolution_attempt TIMESTAMPTZ,
  resolution_details JSONB,    -- Details about resolution attempts

  -- Workflow status
  status candidate_status DEFAULT 'pending',
    -- 'pending' = Needs validation
    -- 'validated' = Validator approved
    -- 'approved' = Human approved
    -- 'rejected' = Invalid relationship

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_by_agent TEXT,

  CONSTRAINT src_or_dst_must_be_resolved
    CHECK (resolution_status != 'resolved' OR (src_extraction_id IS NOT NULL AND dst_extraction_id IS NOT NULL)),

  CONSTRAINT unresolved_must_have_text_refs
    CHECK (resolution_status = 'resolved' OR (src_text_ref IS NOT NULL AND dst_text_ref IS NOT NULL))
);

-- Indexes for performance
CREATE INDEX idx_relationships_snapshot ON staging_relationships(snapshot_id);
CREATE INDEX idx_relationships_src_extraction ON staging_relationships(src_extraction_id);
CREATE INDEX idx_relationships_dst_extraction ON staging_relationships(dst_extraction_id);
CREATE INDEX idx_relationships_src_text ON staging_relationships(src_text_ref);
CREATE INDEX idx_relationships_dst_text ON staging_relationships(dst_text_ref);
CREATE INDEX idx_relationships_resolution ON staging_relationships(resolution_status);
CREATE INDEX idx_relationships_status ON staging_relationships(status);
CREATE INDEX idx_relationships_type ON staging_relationships(rel_type);

-- GIN index for evidence JSONB
CREATE INDEX idx_relationships_evidence ON staging_relationships USING GIN(evidence);

COMMENT ON TABLE staging_relationships IS
  'Forward-looking relationship extraction: captures relationships even if target entities not extracted yet';

COMMENT ON COLUMN staging_relationships.src_text_ref IS
  'Text description of source entity (e.g., "MSP430FR") for later resolution';

COMMENT ON COLUMN staging_relationships.dst_text_ref IS
  'Text description of destination entity (e.g., "RP2350") for later resolution';

COMMENT ON COLUMN staging_relationships.resolution_status IS
  'Tracks whether text references have been matched to actual extraction IDs';

-- ============================================================================
-- PART 3: UTILITY FUNCTIONS
-- ============================================================================

-- Function to auto-resolve relationships when new extraction is added
CREATE OR REPLACE FUNCTION auto_resolve_relationships()
RETURNS TRIGGER AS $$
BEGIN
  -- Try to resolve relationships that mention this entity's key
  UPDATE staging_relationships
  SET
    src_extraction_id = NEW.extraction_id,
    resolution_status = CASE
      WHEN dst_extraction_id IS NOT NULL THEN 'resolved'
      ELSE 'partially_resolved'
    END,
    resolution_attempts = resolution_attempts + 1,
    last_resolution_attempt = NOW(),
    updated_at = NOW()
  WHERE
    src_extraction_id IS NULL
    AND (
      src_text_ref ILIKE '%' || NEW.candidate_key || '%'
      OR NEW.candidate_key ILIKE '%' || src_text_ref || '%'
    );

  UPDATE staging_relationships
  SET
    dst_extraction_id = NEW.extraction_id,
    resolution_status = CASE
      WHEN src_extraction_id IS NOT NULL THEN 'resolved'
      ELSE 'partially_resolved'
    END,
    resolution_attempts = resolution_attempts + 1,
    last_resolution_attempt = NOW(),
    updated_at = NOW()
  WHERE
    dst_extraction_id IS NULL
    AND (
      dst_text_ref ILIKE '%' || NEW.candidate_key || '%'
      OR NEW.candidate_key ILIKE '%' || dst_text_ref || '%'
    );

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-resolve on new extraction
DROP TRIGGER IF EXISTS trigger_auto_resolve_relationships ON staging_extractions;
CREATE TRIGGER trigger_auto_resolve_relationships
  AFTER INSERT ON staging_extractions
  FOR EACH ROW
  EXECUTE FUNCTION auto_resolve_relationships();

COMMENT ON FUNCTION auto_resolve_relationships IS
  'Automatically attempts to resolve staging_relationships when new extractions are added';

-- ============================================================================
-- PART 4: VIEWS FOR ANALYSIS
-- ============================================================================

-- View: Unresolved relationships needing attention
CREATE OR REPLACE VIEW unresolved_relationships AS
SELECT
  sr.rel_id,
  sr.src_text_ref,
  sr.dst_text_ref,
  sr.rel_type,
  sr.confidence,
  sr.resolution_attempts,
  sr.snapshot_id,
  rs.source_url,
  sr.created_at
FROM staging_relationships sr
JOIN raw_snapshots rs ON sr.snapshot_id = rs.id
WHERE sr.resolution_status IN ('unresolved', 'partially_resolved', 'ambiguous')
ORDER BY sr.confidence DESC, sr.created_at DESC;

COMMENT ON VIEW unresolved_relationships IS
  'Relationships that need entity matching (text_refs not yet resolved to extraction IDs)';

-- View: Lineage verification status
CREATE OR REPLACE VIEW lineage_verification_status AS
SELECT
  extraction_id,
  candidate_key,
  candidate_type,
  lineage_verified,
  lineage_confidence,
  extraction_attempt,
  is_reextraction,
  requires_mandatory_review,
  created_at
FROM staging_extractions
ORDER BY
  CASE WHEN requires_mandatory_review THEN 1 ELSE 2 END,
  lineage_confidence ASC NULLS FIRST,
  created_at DESC;

COMMENT ON VIEW lineage_verification_status IS
  'Overview of extraction lineage verification status, prioritizing issues';

-- ============================================================================
-- PART 5: DATA VALIDATION
-- ============================================================================

-- Verify schema changes applied correctly
DO $$
DECLARE
  missing_columns TEXT[];
BEGIN
  -- Check staging_extractions columns
  SELECT ARRAY_AGG(col)
  INTO missing_columns
  FROM (VALUES
    ('evidence_checksum'),
    ('lineage_verified'),
    ('lineage_confidence'),
    ('extraction_attempt'),
    ('is_reextraction')
  ) AS expected(col)
  WHERE NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'staging_extractions'
      AND column_name = expected.col
  );

  IF array_length(missing_columns, 1) > 0 THEN
    RAISE EXCEPTION 'Missing columns in staging_extractions: %', array_to_string(missing_columns, ', ');
  END IF;

  -- Check new tables exist
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'entity_alias') THEN
    RAISE EXCEPTION 'Table entity_alias was not created';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'staging_relationships') THEN
    RAISE EXCEPTION 'Table staging_relationships was not created';
  END IF;

  RAISE NOTICE 'Schema migration completed successfully ✓';
END $$;

COMMIT;

-- ============================================================================
-- POST-MIGRATION VERIFICATION QUERIES
-- ============================================================================

-- Run these to verify migration:

-- 1. Check new columns
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'staging_extractions'
--   AND column_name LIKE '%lineage%' OR column_name LIKE '%extraction_attempt%';

-- 2. Check new tables
-- SELECT table_name, (SELECT COUNT(*) FROM entity_alias) as alias_count,
--        (SELECT COUNT(*) FROM staging_relationships) as rel_count
-- FROM information_schema.tables
-- WHERE table_name IN ('entity_alias', 'staging_relationships');

-- 3. Test auto-resolution trigger
-- INSERT INTO staging_extractions (candidate_key, ...) VALUES ('TestEntity', ...);
-- SELECT * FROM staging_relationships WHERE src_text_ref LIKE '%TestEntity%';
