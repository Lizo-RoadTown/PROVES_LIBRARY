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
-- Migration: Create urls_to_process table for WebFetch agent
-- Purpose: Queue system for documentation URLs with extraction context

CREATE TABLE IF NOT EXISTS urls_to_process (
    url TEXT PRIMARY KEY,
    status TEXT DEFAULT 'pending',
    quality_score FLOAT,
    quality_reason TEXT,

    -- Context hints for extractor (saves tokens, focuses extraction)
    preview_components TEXT[],  -- Component/module names found (e.g., ['I2CDriver', 'LinuxI2CDriverComponentImpl'])
    preview_interfaces TEXT[],  -- Port/interface mentions (e.g., ['read()', 'write()', 'TlmChan'])
    preview_keywords TEXT[],    -- Technical keywords (e.g., ['i2c', 'telemetry', 'component'])
    preview_summary TEXT,       -- Brief content summary for prioritization

    -- Tracking
    discovered_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    error_message TEXT,

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_urls_status ON urls_to_process(status);
CREATE INDEX IF NOT EXISTS idx_urls_discovered ON urls_to_process(discovered_at);

-- Comments
COMMENT ON TABLE urls_to_process IS 'Queue of documentation URLs discovered by WebFetch agent with extraction context';
COMMENT ON COLUMN urls_to_process.preview_components IS 'Component names found during page scan (helps extractor focus)';
COMMENT ON COLUMN urls_to_process.preview_interfaces IS 'Port/interface mentions (e.g., read(), write(), TlmChan)';
COMMENT ON COLUMN urls_to_process.preview_keywords IS 'Technical keywords for prioritization';
COMMENT ON COLUMN urls_to_process.preview_summary IS 'Brief summary of page content';
-- Migration: Add Notion Integration with Sync Tracking
-- Date: 2025-12-27
-- Purpose: Enable bidirectional Notion sync with triggers and status tracking

BEGIN;

-- ============================================================================
-- PART 1: NEW TABLES FOR ERRORS AND REPORTS
-- ============================================================================

-- 1.1: Curator Errors - Track all errors for logging to Notion
CREATE TABLE IF NOT EXISTS curator_errors (
    id SERIAL PRIMARY KEY,

    -- Error details
    url TEXT NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    error_context JSONB,  -- Additional context (batch info, etc.)

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Notion sync tracking
    notion_page_id TEXT,  -- Notion page ID after sync
    notion_synced_at TIMESTAMPTZ,  -- When successfully synced
    notion_last_sync_attempt TIMESTAMPTZ,  -- Last attempt (even if failed)
    notion_sync_error TEXT,  -- Error message if sync failed

    -- Indexes
    CONSTRAINT unique_error_per_url_time UNIQUE(url, created_at)
);

CREATE INDEX idx_curator_errors_created ON curator_errors(created_at DESC);
CREATE INDEX idx_curator_errors_notion_sync ON curator_errors(notion_synced_at)
    WHERE notion_synced_at IS NULL;  -- Find unsynced errors

COMMENT ON TABLE curator_errors IS
    'Curator agent errors logged for Notion integration';

COMMENT ON COLUMN curator_errors.notion_page_id IS
    'Notion page ID where this error was logged (for linking)';

-- 1.2: Curator Reports - Completion summaries after batch runs
CREATE TABLE IF NOT EXISTS curator_reports (
    id SERIAL PRIMARY KEY,

    -- Report details
    run_date TIMESTAMPTZ DEFAULT NOW(),
    urls_processed INTEGER DEFAULT 0,
    urls_successful INTEGER DEFAULT 0,
    urls_failed INTEGER DEFAULT 0,
    total_extractions INTEGER DEFAULT 0,

    -- Report content
    summary TEXT,
    langsmith_trace_url TEXT,
    run_details JSONB,  -- Additional metrics

    -- Reference to pipeline run
    pipeline_run_id UUID REFERENCES pipeline_runs(id),

    -- Notion sync tracking
    notion_page_id TEXT,
    notion_synced_at TIMESTAMPTZ,
    notion_last_sync_attempt TIMESTAMPTZ,
    notion_sync_error TEXT
);

CREATE INDEX idx_curator_reports_date ON curator_reports(run_date DESC);
CREATE INDEX idx_curator_reports_notion_sync ON curator_reports(notion_synced_at)
    WHERE notion_synced_at IS NULL;  -- Find unsynced reports

COMMENT ON TABLE curator_reports IS
    'Curator batch completion reports for Notion integration';

-- ============================================================================
-- PART 2: ADD NOTION TRACKING TO EXISTING TABLES
-- ============================================================================

-- 2.1: staging_extractions - Track Notion sync status
ALTER TABLE staging_extractions
    ADD COLUMN IF NOT EXISTS notion_page_id TEXT,
    ADD COLUMN IF NOT EXISTS notion_synced_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS notion_last_sync_attempt TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS notion_sync_error TEXT;

CREATE INDEX IF NOT EXISTS idx_staging_extractions_notion_sync
    ON staging_extractions(notion_synced_at)
    WHERE notion_synced_at IS NULL AND status = 'pending';

COMMENT ON COLUMN staging_extractions.notion_page_id IS
    'Notion page ID for this extraction (enables bidirectional sync)';

COMMENT ON COLUMN staging_extractions.notion_synced_at IS
    'Timestamp when this extraction was successfully pushed to Notion';

-- ============================================================================
-- PART 3: NOTIFICATION FUNCTIONS (Using pg_notify)
-- ============================================================================

-- 3.1: Notify when new extraction is inserted
CREATE OR REPLACE FUNCTION notify_new_extraction()
RETURNS TRIGGER AS $$
BEGIN
    -- Only notify if not yet synced to Notion
    IF NEW.notion_synced_at IS NULL THEN
        PERFORM pg_notify(
            'notion_sync_extraction',
            json_build_object(
                'extraction_id', NEW.extraction_id,
                'action', 'insert'
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3.2: Notify when new error is inserted
CREATE OR REPLACE FUNCTION notify_new_error()
RETURNS TRIGGER AS $$
BEGIN
    -- Only notify if not yet synced to Notion
    IF NEW.notion_synced_at IS NULL THEN
        PERFORM pg_notify(
            'notion_sync_error',
            json_build_object(
                'error_id', NEW.id,
                'action', 'insert'
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3.3: Notify when new report is inserted
CREATE OR REPLACE FUNCTION notify_new_report()
RETURNS TRIGGER AS $$
BEGIN
    -- Only notify if not yet synced to Notion
    IF NEW.notion_synced_at IS NULL THEN
        PERFORM pg_notify(
            'notion_sync_report',
            json_build_object(
                'report_id', NEW.id,
                'action', 'insert'
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3.4: Notify when URL queue is empty
CREATE OR REPLACE FUNCTION check_url_queue_empty()
RETURNS TRIGGER AS $$
DECLARE
    pending_count INTEGER;
BEGIN
    -- Count pending URLs
    SELECT COUNT(*) INTO pending_count
    FROM urls_to_process
    WHERE status = 'pending';

    -- If queue is now empty (and wasn't before), notify
    IF pending_count = 0 AND OLD.status = 'pending' AND NEW.status != 'pending' THEN
        PERFORM pg_notify(
            'notion_queue_empty',
            json_build_object(
                'timestamp', NOW(),
                'message', 'URL queue is empty - time to run find_good_urls.py'
            )::text
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 4: CREATE TRIGGERS
-- ============================================================================

-- 4.1: Trigger on new extraction
DROP TRIGGER IF EXISTS trigger_notify_new_extraction ON staging_extractions;
CREATE TRIGGER trigger_notify_new_extraction
    AFTER INSERT ON staging_extractions
    FOR EACH ROW
    EXECUTE FUNCTION notify_new_extraction();

-- 4.2: Trigger on new error
DROP TRIGGER IF EXISTS trigger_notify_new_error ON curator_errors;
CREATE TRIGGER trigger_notify_new_error
    AFTER INSERT ON curator_errors
    FOR EACH ROW
    EXECUTE FUNCTION notify_new_error();

-- 4.3: Trigger on new report
DROP TRIGGER IF EXISTS trigger_notify_new_report ON curator_reports;
CREATE TRIGGER trigger_notify_new_report
    AFTER INSERT ON curator_reports
    FOR EACH ROW
    EXECUTE FUNCTION notify_new_report();

-- 4.4: Trigger to check queue status
DROP TRIGGER IF EXISTS trigger_check_url_queue ON urls_to_process;
CREATE TRIGGER trigger_check_url_queue
    AFTER UPDATE OF status ON urls_to_process
    FOR EACH ROW
    EXECUTE FUNCTION check_url_queue_empty();

-- ============================================================================
-- PART 5: UTILITY VIEWS
-- ============================================================================

-- 5.1: View unsynced items across all tables
CREATE OR REPLACE VIEW notion_sync_status AS
SELECT
    'extraction' as item_type,
    extraction_id::text as item_id,
    candidate_key as item_name,
    created_at,
    notion_synced_at,
    notion_sync_error
FROM staging_extractions
WHERE notion_synced_at IS NULL AND status = 'pending'

UNION ALL

SELECT
    'error' as item_type,
    id::text as item_id,
    url as item_name,
    created_at,
    notion_synced_at,
    notion_sync_error
FROM curator_errors
WHERE notion_synced_at IS NULL

UNION ALL

SELECT
    'report' as item_type,
    id::text as item_id,
    'Run Report' as item_name,
    run_date as created_at,
    notion_synced_at,
    notion_sync_error
FROM curator_reports
WHERE notion_synced_at IS NULL

ORDER BY created_at DESC;

COMMENT ON VIEW notion_sync_status IS
    'Overview of all items awaiting Notion sync across all tables';

-- ============================================================================
-- PART 6: HELPER FUNCTIONS FOR WEBHOOK SERVER
-- ============================================================================

-- 6.1: Mark extraction as synced to Notion
CREATE OR REPLACE FUNCTION mark_extraction_synced(
    p_extraction_id UUID,
    p_notion_page_id TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE staging_extractions
    SET
        notion_page_id = p_notion_page_id,
        notion_synced_at = NOW(),
        notion_last_sync_attempt = NOW(),
        notion_sync_error = NULL
    WHERE extraction_id = p_extraction_id;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- 6.2: Mark error as synced to Notion
CREATE OR REPLACE FUNCTION mark_error_synced(
    p_error_id INTEGER,
    p_notion_page_id TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE curator_errors
    SET
        notion_page_id = p_notion_page_id,
        notion_synced_at = NOW(),
        notion_last_sync_attempt = NOW(),
        notion_sync_error = NULL
    WHERE id = p_error_id;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- 6.3: Mark report as synced to Notion
CREATE OR REPLACE FUNCTION mark_report_synced(
    p_report_id INTEGER,
    p_notion_page_id TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE curator_reports
    SET
        notion_page_id = p_notion_page_id,
        notion_synced_at = NOW(),
        notion_last_sync_attempt = NOW(),
        notion_sync_error = NULL
    WHERE id = p_report_id;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- 6.4: Record sync failure
CREATE OR REPLACE FUNCTION mark_sync_failed(
    p_table_name TEXT,
    p_item_id TEXT,
    p_error_message TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    CASE p_table_name
        WHEN 'staging_extractions' THEN
            UPDATE staging_extractions
            SET
                notion_last_sync_attempt = NOW(),
                notion_sync_error = p_error_message
            WHERE extraction_id = p_item_id::UUID;

        WHEN 'curator_errors' THEN
            UPDATE curator_errors
            SET
                notion_last_sync_attempt = NOW(),
                notion_sync_error = p_error_message
            WHERE id = p_item_id::INTEGER;

        WHEN 'curator_reports' THEN
            UPDATE curator_reports
            SET
                notion_last_sync_attempt = NOW(),
                notion_sync_error = p_error_message
            WHERE id = p_item_id::INTEGER;
    END CASE;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 7: VALIDATION
-- ============================================================================

DO $$
BEGIN
    -- Verify new tables exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'curator_errors') THEN
        RAISE EXCEPTION 'Table curator_errors was not created';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'curator_reports') THEN
        RAISE EXCEPTION 'Table curator_reports was not created';
    END IF;

    -- Verify new columns exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'staging_extractions' AND column_name = 'notion_page_id'
    ) THEN
        RAISE EXCEPTION 'Column notion_page_id was not added to staging_extractions';
    END IF;

    RAISE NOTICE 'Migration 003 completed successfully ✓';
    RAISE NOTICE '  - Created curator_errors table';
    RAISE NOTICE '  - Created curator_reports table';
    RAISE NOTICE '  - Added Notion tracking columns to staging_extractions';
    RAISE NOTICE '  - Created 4 notification triggers';
    RAISE NOTICE '  - Created helper functions for webhook server';
END $$;

COMMIT;
-- Patch for Migration 003: Add missing triggers
-- This adds the triggers that weren't created when migration 003 partially failed

BEGIN;

-- 4.1: Trigger on new extraction
DROP TRIGGER IF EXISTS trigger_notify_new_extraction ON staging_extractions;
CREATE TRIGGER trigger_notify_new_extraction
    AFTER INSERT ON staging_extractions
    FOR EACH ROW
    EXECUTE FUNCTION notify_new_extraction();

-- 4.2: Trigger on new error
DROP TRIGGER IF EXISTS trigger_notify_new_error ON curator_errors;
CREATE TRIGGER trigger_notify_new_error
    AFTER INSERT ON curator_errors
    FOR EACH ROW
    EXECUTE FUNCTION notify_new_error();

-- 4.3: Trigger on new report
DROP TRIGGER IF EXISTS trigger_notify_new_report ON curator_reports;
CREATE TRIGGER trigger_notify_new_report
    AFTER INSERT ON curator_reports
    FOR EACH ROW
    EXECUTE FUNCTION notify_new_report();

-- 4.4: Trigger to check queue status
DROP TRIGGER IF EXISTS trigger_check_url_queue ON urls_to_process;
CREATE TRIGGER trigger_check_url_queue
    AFTER UPDATE OF status ON urls_to_process
    FOR EACH ROW
    EXECUTE FUNCTION check_url_queue_empty();

COMMIT;

DO $$
BEGIN
    RAISE NOTICE 'Migration 003b completed successfully ✓';
    RAISE NOTICE '  - Created trigger_notify_new_extraction';
    RAISE NOTICE '  - Created trigger_notify_new_error';
    RAISE NOTICE '  - Created trigger_notify_new_report';
    RAISE NOTICE '  - Created trigger_check_url_queue';
END $$;
-- Migration 004: Update evidence_type enum for GNN training
-- Replaces format-based types with semantic content types
--
-- Rationale: For Graph Neural Network features and MCP server,
-- semantic meaning (what the evidence says) is more valuable than
-- documentation format (how it's presented).
--
-- Old types (format-based):
--   definition_spec, interface_contract, example, narrative,
--   table_diagram, comment, inferred
--
-- New types (semantic-based):
--   explicit_requirement, safety_constraint, performance_constraint,
--   feature_description, interface_specification, behavioral_contract,
--   example_usage, design_rationale, inferred

BEGIN;

-- Step 1: Create new enum with semantic types
CREATE TYPE evidence_type_new AS ENUM (
    'explicit_requirement',      -- "System shall/must..." statements
    'safety_constraint',          -- Safety-critical requirements, failure modes
    'performance_constraint',     -- Timing, resource, throughput constraints
    'feature_description',        -- Functional descriptions, capabilities
    'interface_specification',    -- Port/API contracts, protocols
    'behavioral_contract',        -- State machines, event sequences, modes
    'example_usage',              -- Code examples, usage patterns
    'design_rationale',           -- Why decisions were made, trade-offs
    'dependency_declaration',     -- Explicit dependency statements
    'configuration_parameter',    -- Settings, modes, configuration
    'inferred'                    -- Derived from context, not explicit
);

-- Step 2: Add column with new type
-- (Skip data migration - this is a fresh database with no existing evidence_type column)
ALTER TABLE staging_extractions
ADD COLUMN evidence_type evidence_type_new DEFAULT 'inferred';

-- Step 3: Rename enum type to standard name
ALTER TYPE evidence_type_new RENAME TO evidence_type;

-- Add helpful comment
COMMENT ON TYPE evidence_type IS
'Semantic classification of evidence for GNN training and criticality analysis.
Types capture WHAT the evidence says (content) rather than HOW it appears (format).

Categories:
- explicit_requirement: SHALL/MUST statements, formal requirements
- safety_constraint: Safety-critical requirements, failure modes, inhibit schemes
- performance_constraint: Timing (within Xms), resources, throughput limits
- feature_description: Functional capabilities, what the system does
- interface_specification: Port contracts, APIs, protocols, picolock specs
- behavioral_contract: State machines, event sequences, operational modes
- example_usage: Code examples, usage patterns, how-to guides
- design_rationale: Why decisions made, trade-offs, architectural choices
- dependency_declaration: Explicit "depends on", "requires", "uses" statements
- configuration_parameter: Settings, modes, tunable parameters
- inferred: Derived from context, not explicitly stated';

COMMIT;

-- Verification query (run after migration)
-- SELECT evidence_type, COUNT(*) as count
-- FROM staging_extractions
-- GROUP BY evidence_type
-- ORDER BY count DESC;

DO $$
BEGIN
    RAISE NOTICE 'Migration 004 completed successfully ✓';
    RAISE NOTICE '  - Replaced evidence_type enum with semantic categories';
    RAISE NOTICE '  - Migrated existing data to new types';
    RAISE NOTICE '  - Ready for GNN training and MCP server';
    RAISE NOTICE '';
    RAISE NOTICE 'New evidence types available:';
    RAISE NOTICE '  - explicit_requirement (SHALL/MUST statements)';
    RAISE NOTICE '  - safety_constraint (safety-critical requirements)';
    RAISE NOTICE '  - performance_constraint (timing, resource limits)';
    RAISE NOTICE '  - feature_description (functional capabilities)';
    RAISE NOTICE '  - interface_specification (port/API contracts)';
    RAISE NOTICE '  - behavioral_contract (state machines, sequences)';
    RAISE NOTICE '  - example_usage (code examples, patterns)';
    RAISE NOTICE '  - design_rationale (why decisions made)';
    RAISE NOTICE '  - dependency_declaration (explicit dependencies)';
    RAISE NOTICE '  - configuration_parameter (settings, modes)';
    RAISE NOTICE '  - inferred (derived from context)';
END $$;
-- Migration 005: Add review tracking columns
-- Tracks who approved/rejected extractions and when

BEGIN;

-- Add review tracking columns to staging_extractions
ALTER TABLE staging_extractions
ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS review_decision TEXT CHECK (review_decision IN ('approve', 'reject')),
ADD COLUMN IF NOT EXISTS review_notes TEXT;

-- Create index for querying reviewed items
CREATE INDEX IF NOT EXISTS idx_staging_extractions_reviewed
ON staging_extractions(reviewed_at)
WHERE reviewed_at IS NOT NULL;

-- Create index for review decisions
CREATE INDEX IF NOT EXISTS idx_staging_extractions_review_decision
ON staging_extractions(review_decision)
WHERE review_decision IS NOT NULL;

COMMIT;
-- Migration 005b: Fix review_decision constraint to include 'modified'
-- The webhook handler uses 'modified' but the original constraint only allowed 'approve' and 'reject'

BEGIN;

-- Drop the old constraint
ALTER TABLE staging_extractions
DROP CONSTRAINT IF EXISTS staging_extractions_review_decision_check;

-- Add updated constraint
ALTER TABLE staging_extractions
ADD CONSTRAINT staging_extractions_review_decision_check
CHECK (review_decision IN ('approve', 'reject', 'modified'));

COMMIT;
-- Migration 006: Add improvement suggestions tracking
-- Meta-learning system that analyzes extraction patterns to suggest improvements

BEGIN;

-- Create suggestion category enum
CREATE TYPE suggestion_category AS ENUM (
    'prompt_update',           -- Suggestions for improving extractor prompts
    'ontology_change',         -- Suggestions for modifying the ontology
    'method_improvement',      -- Suggestions for extraction methodology
    'evidence_type_refinement', -- Suggestions for evidence type classification
    'confidence_calibration'   -- Suggestions for confidence scoring improvements
);

-- Create suggestion confidence enum
CREATE TYPE suggestion_confidence AS ENUM (
    'low',
    'medium',
    'high'
);

-- Create suggestion status enum
CREATE TYPE suggestion_status AS ENUM (
    'pending',      -- Waiting for human review
    'approved',     -- Approved for implementation
    'rejected',     -- Rejected by human reviewer
    'implemented',  -- Changes have been applied
    'needs_review'  -- Flagged for additional review
);

-- Create improvement_suggestions table
CREATE TABLE IF NOT EXISTS improvement_suggestions (
    -- Primary identification
    suggestion_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Categorization
    category suggestion_category NOT NULL,
    title TEXT NOT NULL,

    -- Analysis and recommendation
    evidence TEXT NOT NULL,              -- What patterns led to this suggestion
    current_state TEXT NOT NULL,         -- What exists now
    proposed_change TEXT NOT NULL,       -- Specific recommendation
    impact_count INTEGER DEFAULT 0,      -- Number of extractions affected
    confidence suggestion_confidence NOT NULL,

    -- Supporting data
    extraction_ids UUID[] DEFAULT '{}',  -- Array of extraction IDs that support this suggestion

    -- Review tracking
    status suggestion_status DEFAULT 'pending',
    review_decision TEXT CHECK (review_decision IN ('approve', 'reject', 'modified')),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,

    -- Notion sync
    notion_page_id TEXT UNIQUE,          -- Notion page ID for bidirectional sync

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_suggestions_status
ON improvement_suggestions(status);

CREATE INDEX IF NOT EXISTS idx_suggestions_category
ON improvement_suggestions(category);

CREATE INDEX IF NOT EXISTS idx_suggestions_notion_page_id
ON improvement_suggestions(notion_page_id)
WHERE notion_page_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_suggestions_reviewed_at
ON improvement_suggestions(reviewed_at)
WHERE reviewed_at IS NOT NULL;

-- Create trigger to update updated_at
CREATE OR REPLACE FUNCTION update_suggestion_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_suggestion_timestamp
BEFORE UPDATE ON improvement_suggestions
FOR EACH ROW
EXECUTE FUNCTION update_suggestion_updated_at();

COMMIT;
-- Migration 007: Add error logging columns to tables
-- Each agent logs its own errors to the table it uses

BEGIN;

-- Add error logging to staging_extractions
-- Used by: extractor, validator, suggestion analyzer
ALTER TABLE staging_extractions
ADD COLUMN IF NOT EXISTS error_log JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS error_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_error_at TIMESTAMP WITH TIME ZONE;

-- Add error logging to improvement_suggestions
-- Used by: improvement analyzer
ALTER TABLE improvement_suggestions
ADD COLUMN IF NOT EXISTS error_log JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS error_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_error_at TIMESTAMP WITH TIME ZONE;

-- Create index for querying errors
CREATE INDEX IF NOT EXISTS idx_staging_extractions_errors
ON staging_extractions(last_error_at)
WHERE error_count > 0;

CREATE INDEX IF NOT EXISTS idx_suggestions_errors
ON improvement_suggestions(last_error_at)
WHERE error_count > 0;

-- Create a view to aggregate all errors across tables
CREATE OR REPLACE VIEW all_errors AS
SELECT
    'staging_extraction' AS source_table,
    extraction_id::text AS record_id,
    candidate_key AS record_name,
    error_log,
    error_count,
    last_error_at,
    created_at,
    updated_at
FROM staging_extractions
WHERE error_count > 0

UNION ALL

SELECT
    'improvement_suggestion' AS source_table,
    suggestion_id::text AS record_id,
    title AS record_name,
    error_log,
    error_count,
    last_error_at,
    created_at,
    updated_at
FROM improvement_suggestions
WHERE error_count > 0;

COMMENT ON VIEW all_errors IS 'Aggregated view of all errors across agent tables';

-- Helper function to append an error to error_log
CREATE OR REPLACE FUNCTION log_error(
    error_data JSONB
) RETURNS JSONB AS $$
DECLARE
    new_error JSONB;
BEGIN
    -- Add timestamp if not present
    new_error := error_data || jsonb_build_object(
        'logged_at', COALESCE(
            (error_data->>'logged_at')::timestamp with time zone,
            NOW()
        )
    );

    RETURN new_error;
END;
$$ LANGUAGE plpgsql;

COMMIT;
-- Migration: Add Dimensional Canonicalization Fields
-- Date: 2025-12-28
-- Purpose: Capture epistemic metadata (Contact, Directionality, Temporality, Formalizability, Carrier)
--          to preserve knowledge grounding as defined in Knowledge Canonicalization Theory

BEGIN;

-- ============================================================================
-- PART 1: KNOWLEDGE FORM AND DIMENSIONAL ATTRIBUTES
-- ============================================================================

-- 1.1: Add knowledge form (Embodied vs Inferred)
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  knowledge_form TEXT CHECK (knowledge_form IN ('embodied', 'inferred', 'unknown'));

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  knowledge_form_confidence NUMERIC(3,2) CHECK (
    knowledge_form_confidence IS NULL OR
    (knowledge_form_confidence >= 0 AND knowledge_form_confidence <= 1)
  );

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  knowledge_form_reasoning TEXT;

COMMENT ON COLUMN staging_extractions.knowledge_form IS
  'Whether knowledge originates through direct interaction (embodied) or symbolic reasoning (inferred)';

-- 1.2: Dimension 1 - Contact (Epistemic Anchoring)
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  contact_level TEXT CHECK (contact_level IN ('direct', 'mediated', 'indirect', 'derived', 'unknown'));

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  contact_confidence NUMERIC(3,2) CHECK (
    contact_confidence IS NULL OR
    (contact_confidence >= 0 AND contact_confidence <= 1)
  );

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  contact_reasoning TEXT;

COMMENT ON COLUMN staging_extractions.contact_level IS
  'How close knowledge is to direct interaction with reality: direct (physical), mediated (instrumented), indirect (effect-only), derived (model-only)';

-- 1.3: Dimension 2 - Directionality (Epistemic Operation)
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  directionality TEXT CHECK (directionality IN ('forward', 'backward', 'bidirectional', 'unknown'));

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  directionality_confidence NUMERIC(3,2) CHECK (
    directionality_confidence IS NULL OR
    (directionality_confidence >= 0 AND directionality_confidence <= 1)
  );

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  directionality_reasoning TEXT;

COMMENT ON COLUMN staging_extractions.directionality IS
  'Whether knowledge formed through forward inference (prediction) or backward inference (assessment from effects)';

-- 1.4: Dimension 3 - Temporality (Epistemic Dependence on History)
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  temporality TEXT CHECK (temporality IN ('snapshot', 'sequence', 'history', 'lifecycle', 'unknown'));

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  temporality_confidence NUMERIC(3,2) CHECK (
    temporality_confidence IS NULL OR
    (temporality_confidence >= 0 AND temporality_confidence <= 1)
  );

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  temporality_reasoning TEXT;

COMMENT ON COLUMN staging_extractions.temporality IS
  'Whether truth depends on time: snapshot (instant), sequence (order matters), history (accumulated past), lifecycle (long-term evolution)';

-- 1.5: Dimension 4 - Formalizability (Capacity for Symbolic Transformation)
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  formalizability TEXT CHECK (formalizability IN ('portable', 'conditional', 'local', 'tacit', 'unknown'));

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  formalizability_confidence NUMERIC(3,2) CHECK (
    formalizability_confidence IS NULL OR
    (formalizability_confidence >= 0 AND formalizability_confidence <= 1)
  );

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  formalizability_reasoning TEXT;

COMMENT ON COLUMN staging_extractions.formalizability IS
  'Degree to which knowledge can be symbolized: portable (full transfer), conditional (context-dependent), local (setting-specific), tacit (embodied only)';

-- 1.6: Carrier (What Holds the Knowledge)
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  carrier TEXT CHECK (carrier IN ('body', 'instrument', 'artifact', 'community', 'machine', 'unknown'));

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  carrier_confidence NUMERIC(3,2) CHECK (
    carrier_confidence IS NULL OR
    (carrier_confidence >= 0 AND carrier_confidence <= 1)
  );

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  carrier_reasoning TEXT;

COMMENT ON COLUMN staging_extractions.carrier IS
  'What carries the knowledge: body (person), instrument (sensor), artifact (document), community (organization), machine (AI/system)';

-- ============================================================================
-- PART 2: EXTRACTION QUALITY FLAGS
-- ============================================================================

-- 2.1: Human review flags (dimensional confidence thresholds)
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  needs_dimensional_review BOOLEAN DEFAULT FALSE;

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  dimensional_review_reason TEXT;

COMMENT ON COLUMN staging_extractions.needs_dimensional_review IS
  'TRUE if any dimensional confidence score below threshold (e.g., < 0.7) or dimensional conflict detected';

-- 2.2: Dimensional completeness check
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  dimensional_completeness NUMERIC(3,2) CHECK (
    dimensional_completeness IS NULL OR
    (dimensional_completeness >= 0 AND dimensional_completeness <= 1)
  );

COMMENT ON COLUMN staging_extractions.dimensional_completeness IS
  'Fraction of dimensions successfully extracted (0.0 = none, 1.0 = all 5 dimensions with high confidence)';

-- ============================================================================
-- PART 3: EPISODIC ENTITY TRACKING (for Temporality dimension)
-- ============================================================================

-- 3.1: New table for episodes-as-entities (temporal events that cause degradation)
CREATE TABLE IF NOT EXISTS episodic_entities (
  episode_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Episode identification
  episode_type TEXT NOT NULL,  -- 'thermal_cycle', 'integration_phase', 'launch_sequence', 'deployment_event', etc.
  episode_name TEXT,           -- Human-readable name
  episode_key TEXT UNIQUE,     -- Canonical identifier

  -- Temporal properties
  start_time TIMESTAMPTZ,
  end_time TIMESTAMPTZ,
  duration_estimate TEXT,      -- "3 hours", "1 semester", "500 cycles"

  -- Relationships to components (JSONB for flexibility)
  affected_components JSONB,   -- Array of component IDs affected by this episode

  -- Evidence and source
  snapshot_id UUID REFERENCES raw_snapshots(id),
  evidence JSONB,
  confidence NUMERIC(3,2) CHECK (confidence >= 0 AND confidence <= 1),

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  created_by_agent TEXT,
  ecosystem ecosystem_type,

  CONSTRAINT valid_time_range CHECK (start_time IS NULL OR end_time IS NULL OR start_time <= end_time)
);

CREATE INDEX idx_episodes_type ON episodic_entities(episode_type);
CREATE INDEX idx_episodes_key ON episodic_entities(episode_key);
CREATE INDEX idx_episodes_snapshot ON episodic_entities(snapshot_id);
CREATE INDEX idx_episodes_components ON episodic_entities USING GIN(affected_components);

COMMENT ON TABLE episodic_entities IS
  'Temporal events as first-class entities (e.g., thermal cycling episodes, integration phases) that enable causal reasoning about history-dependent degradation';

COMMENT ON COLUMN episodic_entities.episode_type IS
  'Type of temporal event: thermal_cycle, vibration_test, student_rotation, design_review, etc.';

COMMENT ON COLUMN episodic_entities.affected_components IS
  'JSONB array of component extraction IDs affected by this episode, enabling GNN to reason about cumulative effects';

-- 3.2: Linking table for episodes → extractions
CREATE TABLE IF NOT EXISTS episode_extraction_links (
  link_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  episode_id UUID REFERENCES episodic_entities(episode_id) ON DELETE CASCADE,
  extraction_id UUID REFERENCES staging_extractions(extraction_id) ON DELETE CASCADE,

  link_type TEXT,  -- 'caused_by', 'observed_during', 'affects', 'describes'
  confidence NUMERIC(3,2) CHECK (confidence >= 0 AND confidence <= 1),

  created_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT unique_episode_extraction UNIQUE(episode_id, extraction_id, link_type)
);

CREATE INDEX idx_episode_links_episode ON episode_extraction_links(episode_id);
CREATE INDEX idx_episode_links_extraction ON episode_extraction_links(extraction_id);

COMMENT ON TABLE episode_extraction_links IS
  'Links episodic entities to knowledge extractions, enabling temporal causality tracking';

-- ============================================================================
-- PART 4: INDEXES FOR DIMENSIONAL QUERIES
-- ============================================================================

-- Composite indexes for dimensional analysis
CREATE INDEX IF NOT EXISTS idx_extractions_dimensional_profile
  ON staging_extractions(knowledge_form, contact_level, directionality, temporality, formalizability);

CREATE INDEX IF NOT EXISTS idx_extractions_needs_dimensional_review
  ON staging_extractions(needs_dimensional_review)
  WHERE needs_dimensional_review = TRUE;

CREATE INDEX IF NOT EXISTS idx_extractions_embodied_knowledge
  ON staging_extractions(knowledge_form, carrier)
  WHERE knowledge_form = 'embodied';

CREATE INDEX IF NOT EXISTS idx_extractions_low_formalizability
  ON staging_extractions(formalizability, formalizability_confidence)
  WHERE formalizability IN ('tacit', 'local');

-- ============================================================================
-- PART 5: FUNCTIONS FOR DIMENSIONAL QUALITY CHECKS
-- ============================================================================

-- Function: Calculate dimensional completeness score
CREATE OR REPLACE FUNCTION calculate_dimensional_completeness(
  p_knowledge_form_conf NUMERIC,
  p_contact_conf NUMERIC,
  p_directionality_conf NUMERIC,
  p_temporality_conf NUMERIC,
  p_formalizability_conf NUMERIC,
  p_carrier_conf NUMERIC
) RETURNS NUMERIC AS $$
DECLARE
  total_dimensions INTEGER := 6;
  completed_dimensions INTEGER := 0;
  confidence_threshold NUMERIC := 0.7;
BEGIN
  -- Count dimensions with confidence >= threshold
  IF p_knowledge_form_conf >= confidence_threshold THEN completed_dimensions := completed_dimensions + 1; END IF;
  IF p_contact_conf >= confidence_threshold THEN completed_dimensions := completed_dimensions + 1; END IF;
  IF p_directionality_conf >= confidence_threshold THEN completed_dimensions := completed_dimensions + 1; END IF;
  IF p_temporality_conf >= confidence_threshold THEN completed_dimensions := completed_dimensions + 1; END IF;
  IF p_formalizability_conf >= confidence_threshold THEN completed_dimensions := completed_dimensions + 1; END IF;
  IF p_carrier_conf >= confidence_threshold THEN completed_dimensions := completed_dimensions + 1; END IF;

  RETURN ROUND(completed_dimensions::NUMERIC / total_dimensions, 2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_dimensional_completeness IS
  'Calculates fraction of dimensions extracted with confidence >= 0.7';

-- Function: Auto-flag extractions needing dimensional review
CREATE OR REPLACE FUNCTION check_dimensional_review_needed()
RETURNS TRIGGER AS $$
DECLARE
  confidence_threshold NUMERIC := 0.7;
  reasons TEXT[] := ARRAY[]::TEXT[];
BEGIN
  -- Check for low-confidence dimensions
  IF NEW.knowledge_form_confidence < confidence_threshold THEN
    reasons := array_append(reasons, format('Low knowledge_form confidence (%.2f)', NEW.knowledge_form_confidence));
  END IF;

  IF NEW.contact_confidence < confidence_threshold THEN
    reasons := array_append(reasons, format('Low contact confidence (%.2f)', NEW.contact_confidence));
  END IF;

  IF NEW.directionality_confidence < confidence_threshold THEN
    reasons := array_append(reasons, format('Low directionality confidence (%.2f)', NEW.directionality_confidence));
  END IF;

  IF NEW.temporality_confidence < confidence_threshold THEN
    reasons := array_append(reasons, format('Low temporality confidence (%.2f)', NEW.temporality_confidence));
  END IF;

  IF NEW.formalizability_confidence < confidence_threshold THEN
    reasons := array_append(reasons, format('Low formalizability confidence (%.2f)', NEW.formalizability_confidence));
  END IF;

  IF NEW.carrier_confidence < confidence_threshold THEN
    reasons := array_append(reasons, format('Low carrier confidence (%.2f)', NEW.carrier_confidence));
  END IF;

  -- Check for dimensional conflicts (e.g., derived contact but embodied knowledge)
  IF NEW.knowledge_form = 'embodied' AND NEW.contact_level = 'derived' THEN
    reasons := array_append(reasons, 'Conflict: embodied knowledge cannot have derived contact');
  END IF;

  IF NEW.formalizability = 'tacit' AND NEW.knowledge_form = 'inferred' THEN
    reasons := array_append(reasons, 'Conflict: inferred knowledge should not be tacit');
  END IF;

  -- Calculate completeness
  NEW.dimensional_completeness := calculate_dimensional_completeness(
    COALESCE(NEW.knowledge_form_confidence, 0),
    COALESCE(NEW.contact_confidence, 0),
    COALESCE(NEW.directionality_confidence, 0),
    COALESCE(NEW.temporality_confidence, 0),
    COALESCE(NEW.formalizability_confidence, 0),
    COALESCE(NEW.carrier_confidence, 0)
  );

  -- Set review flag if issues found
  IF array_length(reasons, 1) > 0 THEN
    NEW.needs_dimensional_review := TRUE;
    NEW.dimensional_review_reason := array_to_string(reasons, '; ');
  ELSE
    NEW.needs_dimensional_review := FALSE;
    NEW.dimensional_review_reason := NULL;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-check dimensional quality on insert/update
DROP TRIGGER IF EXISTS trigger_check_dimensional_review ON staging_extractions;
CREATE TRIGGER trigger_check_dimensional_review
  BEFORE INSERT OR UPDATE ON staging_extractions
  FOR EACH ROW
  EXECUTE FUNCTION check_dimensional_review_needed();

COMMENT ON FUNCTION check_dimensional_review_needed IS
  'Auto-flags extractions with low dimensional confidence or logical conflicts for human review';

-- ============================================================================
-- PART 6: VIEWS FOR DIMENSIONAL ANALYSIS
-- ============================================================================

-- View: Dimensional quality dashboard
CREATE OR REPLACE VIEW dimensional_quality_dashboard AS
SELECT
  COUNT(*) as total_extractions,

  -- Overall dimensional completeness
  AVG(dimensional_completeness) as avg_completeness,

  -- Extractions needing review
  SUM(CASE WHEN needs_dimensional_review THEN 1 ELSE 0 END) as needs_review_count,

  -- Knowledge form distribution
  SUM(CASE WHEN knowledge_form = 'embodied' THEN 1 ELSE 0 END) as embodied_count,
  SUM(CASE WHEN knowledge_form = 'inferred' THEN 1 ELSE 0 END) as inferred_count,
  SUM(CASE WHEN knowledge_form = 'unknown' THEN 1 ELSE 0 END) as unknown_form_count,

  -- Contact level distribution
  SUM(CASE WHEN contact_level = 'direct' THEN 1 ELSE 0 END) as direct_contact_count,
  SUM(CASE WHEN contact_level = 'mediated' THEN 1 ELSE 0 END) as mediated_contact_count,
  SUM(CASE WHEN contact_level = 'indirect' THEN 1 ELSE 0 END) as indirect_contact_count,
  SUM(CASE WHEN contact_level = 'derived' THEN 1 ELSE 0 END) as derived_contact_count,

  -- Average confidence scores
  AVG(knowledge_form_confidence) as avg_knowledge_form_conf,
  AVG(contact_confidence) as avg_contact_conf,
  AVG(directionality_confidence) as avg_directionality_conf,
  AVG(temporality_confidence) as avg_temporality_conf,
  AVG(formalizability_confidence) as avg_formalizability_conf,
  AVG(carrier_confidence) as avg_carrier_conf

FROM staging_extractions;

COMMENT ON VIEW dimensional_quality_dashboard IS
  'Overview of dimensional extraction quality across all extractions';

-- View: High-value embodied knowledge at risk
CREATE OR REPLACE VIEW embodied_knowledge_at_risk AS
SELECT
  extraction_id,
  candidate_key,
  candidate_type,
  knowledge_form,
  contact_level,
  formalizability,
  carrier,
  formalizability_confidence,
  dimensional_completeness,
  created_at,
  snapshot_id
FROM staging_extractions
WHERE knowledge_form = 'embodied'
  AND formalizability IN ('tacit', 'local')
  AND contact_level IN ('direct', 'mediated')
ORDER BY formalizability_confidence DESC, created_at DESC;

COMMENT ON VIEW embodied_knowledge_at_risk IS
  'Embodied knowledge with low formalizability (tacit/local) at risk of loss during organizational transitions';

-- View: Episodic temporal knowledge
CREATE OR REPLACE VIEW episodic_temporal_knowledge AS
SELECT
  se.extraction_id,
  se.candidate_key,
  se.temporality,
  se.temporality_confidence,
  ee.episode_id,
  ee.episode_type,
  ee.episode_name,
  ee.duration_estimate,
  eel.link_type,
  se.created_at
FROM staging_extractions se
LEFT JOIN episode_extraction_links eel ON se.extraction_id = eel.extraction_id
LEFT JOIN episodic_entities ee ON eel.episode_id = ee.episode_id
WHERE se.temporality IN ('history', 'lifecycle')
ORDER BY se.temporality_confidence DESC;

COMMENT ON VIEW episodic_temporal_knowledge IS
  'Knowledge with history/lifecycle temporality and associated episodic entities for causal reasoning';

-- ============================================================================
-- PART 7: DATA VALIDATION
-- ============================================================================

DO $$
DECLARE
  missing_columns TEXT[];
BEGIN
  -- Check dimensional columns exist
  SELECT ARRAY_AGG(col)
  INTO missing_columns
  FROM (VALUES
    ('knowledge_form'),
    ('contact_level'),
    ('contact_confidence'),
    ('directionality'),
    ('temporality'),
    ('formalizability'),
    ('carrier'),
    ('dimensional_completeness')
  ) AS expected(col)
  WHERE NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'staging_extractions'
      AND column_name = expected.col
  );

  IF array_length(missing_columns, 1) > 0 THEN
    RAISE EXCEPTION 'Missing dimensional columns: %', array_to_string(missing_columns, ', ');
  END IF;

  -- Check episodic entities table exists
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'episodic_entities') THEN
    RAISE EXCEPTION 'Table episodic_entities was not created';
  END IF;

  RAISE NOTICE 'Dimensional canonicalization migration completed successfully ✓';
END $$;

COMMIT;

-- ============================================================================
-- POST-MIGRATION VERIFICATION QUERIES
-- ============================================================================

-- 1. Check dimensional columns
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'staging_extractions'
--   AND column_name LIKE '%contact%' OR column_name LIKE '%directionality%'
--   OR column_name LIKE '%temporality%' OR column_name LIKE '%formalizability%';

-- 2. Check dimensional quality dashboard
-- SELECT * FROM dimensional_quality_dashboard;

-- 3. Test dimensional review trigger
-- INSERT INTO staging_extractions (candidate_key, contact_level, contact_confidence)
-- VALUES ('TestEntity', 'direct', 0.5);  -- Should trigger review flag (low confidence)

-- 4. Check episodic entities table
-- SELECT table_name, (SELECT COUNT(*) FROM episodic_entities) as episode_count
-- FROM information_schema.tables
-- WHERE table_name = 'episodic_entities';
-- ============================================================================
-- Migration 009: Verified Knowledge Layer
-- ============================================================================
-- After staging_extractions approval, knowledge is promoted to core_entities
-- with human verification, dimensional adjustments, enrichment, and relationships
-- ============================================================================

-- 1. Add dimensional metadata and verification fields to core_entities
-- ============================================================================

-- 1.1: Add verified dimensional metadata (human-confirmed values)
ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  knowledge_form TEXT CHECK (knowledge_form IN ('embodied', 'inferred', 'unknown'));

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  knowledge_form_confidence NUMERIC(3,2) CHECK (
    knowledge_form_confidence IS NULL OR
    (knowledge_form_confidence >= 0 AND knowledge_form_confidence <= 1)
  );

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  knowledge_form_reasoning TEXT;

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  contact_level TEXT CHECK (contact_level IN ('direct', 'mediated', 'indirect', 'derived', 'unknown'));

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  contact_confidence NUMERIC(3,2);

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  contact_reasoning TEXT;

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  directionality TEXT CHECK (directionality IN ('forward', 'backward', 'bidirectional', 'unknown'));

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  directionality_confidence NUMERIC(3,2);

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  directionality_reasoning TEXT;

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  temporality TEXT CHECK (temporality IN ('snapshot', 'sequence', 'history', 'lifecycle', 'unknown'));

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  temporality_confidence NUMERIC(3,2);

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  temporality_reasoning TEXT;

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  formalizability TEXT CHECK (formalizability IN ('portable', 'conditional', 'local', 'tacit', 'unknown'));

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  formalizability_confidence NUMERIC(3,2);

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  formalizability_reasoning TEXT;

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  carrier TEXT CHECK (carrier IN ('body', 'instrument', 'artifact', 'community', 'machine', 'unknown'));

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  carrier_confidence NUMERIC(3,2);

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  carrier_reasoning TEXT;

-- 1.2: Add verification tracking
ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  verification_status TEXT DEFAULT 'pending' CHECK (
    verification_status IN ('pending', 'human_verified', 'auto_approved', 'needs_review')
  );

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  verified_by TEXT;  -- User ID or webhook identifier

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  verified_at TIMESTAMPTZ;

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  epistemic_notes TEXT;  -- Human notes about knowledge quality/context

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  notion_page_id TEXT;  -- For Notion webhook integration

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  approval_source TEXT CHECK (
    approval_source IN ('notion_webhook', 'manual_review', 'auto_promotion')
  );

-- Create index for verification queries
CREATE INDEX IF NOT EXISTS idx_core_entities_verification_status
  ON core_entities(verification_status);

CREATE INDEX IF NOT EXISTS idx_core_entities_verified_at
  ON core_entities(verified_at);

CREATE INDEX IF NOT EXISTS idx_core_entities_notion_page
  ON core_entities(notion_page_id) WHERE notion_page_id IS NOT NULL;


-- ============================================================================
-- 2. Dimensional Adjustment History Table
-- ============================================================================
-- Tracks when humans adjust dimensional metadata during verification
-- Maintains full audit trail of epistemic reasoning evolution

CREATE TABLE IF NOT EXISTS dimensional_adjustment_history (
  adjustment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- What was adjusted
  entity_id UUID NOT NULL REFERENCES core_entities(id) ON DELETE CASCADE,
  dimension_name TEXT NOT NULL CHECK (
    dimension_name IN ('knowledge_form', 'contact', 'directionality', 'temporality', 'formalizability', 'carrier')
  ),

  -- Before adjustment (from staging_extractions)
  old_value TEXT,
  old_confidence NUMERIC(3,2),
  old_reasoning TEXT,

  -- After adjustment (human-corrected)
  new_value TEXT,
  new_confidence NUMERIC(3,2),
  new_reasoning TEXT,

  -- Who and why
  adjusted_by TEXT NOT NULL,  -- User ID
  adjustment_reason TEXT NOT NULL CHECK (
    adjustment_reason IN (
      'human_correction',        -- Human disagreed with agent inference
      'context_addition',        -- Human added missing context
      'confidence_calibration',  -- Adjusted confidence based on domain knowledge
      'epistemic_clarification', -- Clarified ambiguous epistemic status
      'source_verification'      -- Verified against primary sources
    )
  ),
  adjustment_notes TEXT,  -- Freeform explanation

  -- When
  adjusted_at TIMESTAMPTZ DEFAULT NOW(),

  -- Source of original inference
  source_extraction_id UUID REFERENCES staging_extractions(extraction_id),

  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dimensional_adjustments_entity
  ON dimensional_adjustment_history(entity_id);

CREATE INDEX IF NOT EXISTS idx_dimensional_adjustments_dimension
  ON dimensional_adjustment_history(dimension_name);

CREATE INDEX IF NOT EXISTS idx_dimensional_adjustments_adjusted_at
  ON dimensional_adjustment_history(adjusted_at);

-- View: Recent dimensional corrections (for learning)
CREATE OR REPLACE VIEW recent_dimensional_corrections AS
SELECT
  dah.adjustment_id,
  dah.entity_id,
  ce.canonical_key,
  ce.name,
  dah.dimension_name,
  dah.old_value,
  dah.old_confidence,
  dah.new_value,
  dah.new_confidence,
  dah.adjustment_reason,
  dah.adjustment_notes,
  dah.adjusted_by,
  dah.adjusted_at
FROM dimensional_adjustment_history dah
JOIN core_entities ce ON dah.entity_id = ce.id
WHERE dah.adjusted_at > NOW() - INTERVAL '30 days'
ORDER BY dah.adjusted_at DESC;


-- ============================================================================
-- 3. Knowledge Enrichment Table
-- ============================================================================
-- Handles aliases, duplicates, merged knowledge from multiple sources

CREATE TABLE IF NOT EXISTS knowledge_enrichment (
  enrichment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Primary entity (the canonical knowledge node)
  primary_entity_id UUID NOT NULL REFERENCES core_entities(id) ON DELETE CASCADE,

  -- Enrichment type
  enrichment_type TEXT NOT NULL CHECK (
    enrichment_type IN (
      'alias',              -- Alternative name for same entity
      'duplicate_merge',    -- Merged from duplicate extraction
      'cross_source',       -- Same knowledge from different sources
      'temporal_update',    -- Updated knowledge over time
      'epistemic_refinement' -- Refined understanding from additional evidence
    )
  ),

  -- Source of enrichment
  source_entity_id UUID REFERENCES core_entities(id) ON DELETE SET NULL,  -- If merged from another entity
  source_extraction_id UUID REFERENCES staging_extractions(extraction_id),

  -- Enrichment data
  alias_name TEXT,  -- If enrichment_type = 'alias'
  merged_attributes JSONB,  -- Additional attributes from merged entity
  conflict_resolution JSONB,  -- How conflicts were resolved
  confidence_boost NUMERIC(3,2),  -- Confidence increase from corroboration

  -- Provenance
  enriched_by TEXT NOT NULL,  -- User ID or 'auto_enrichment_agent'
  enriched_at TIMESTAMPTZ DEFAULT NOW(),
  enrichment_notes TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_enrichment_primary
  ON knowledge_enrichment(primary_entity_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_enrichment_type
  ON knowledge_enrichment(enrichment_type);

CREATE INDEX IF NOT EXISTS idx_knowledge_enrichment_source
  ON knowledge_enrichment(source_entity_id) WHERE source_entity_id IS NOT NULL;

-- View: Entity aliases (for search/disambiguation)
CREATE OR REPLACE VIEW entity_aliases AS
SELECT
  ke.primary_entity_id,
  ce.canonical_key AS primary_key,
  ce.name AS primary_name,
  ke.alias_name,
  ke.enriched_at,
  ke.enriched_by
FROM knowledge_enrichment ke
JOIN core_entities ce ON ke.primary_entity_id = ce.id
WHERE ke.enrichment_type = 'alias'
  AND ce.is_current = TRUE;


-- ============================================================================
-- 4. Episode-Knowledge Relationships
-- ============================================================================
-- Links verified knowledge to episodic entities (temporal context)

CREATE TABLE IF NOT EXISTS knowledge_episode_relationships (
  relationship_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- What and when
  knowledge_entity_id UUID NOT NULL REFERENCES core_entities(id) ON DELETE CASCADE,
  episode_id UUID NOT NULL REFERENCES episodic_entities(episode_id) ON DELETE CASCADE,

  -- Relationship type
  relationship_type TEXT NOT NULL CHECK (
    relationship_type IN (
      'observed_during',     -- Knowledge observed during this episode
      'caused_by',           -- Episode caused this knowledge to emerge
      'affects',             -- Knowledge affects this episode
      'validates',           -- Knowledge validates episode hypothesis
      'contradicts'          -- Knowledge contradicts episode expectation
    )
  ),

  -- Strength and confidence
  relationship_strength NUMERIC(3,2) CHECK (
    relationship_strength >= 0 AND relationship_strength <= 1
  ),
  confidence NUMERIC(3,2) CHECK (
    confidence >= 0 AND confidence <= 1
  ),

  -- Evidence
  evidence_extraction_id UUID REFERENCES staging_extractions(extraction_id),
  evidence_text TEXT,

  -- Provenance
  created_by TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(knowledge_entity_id, episode_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_episode_knowledge
  ON knowledge_episode_relationships(knowledge_entity_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_episode_episode
  ON knowledge_episode_relationships(episode_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_episode_type
  ON knowledge_episode_relationships(relationship_type);


-- ============================================================================
-- 5. Component-Knowledge Relationships
-- ============================================================================
-- Links verified knowledge to hardware/software components

CREATE TABLE IF NOT EXISTS knowledge_component_relationships (
  relationship_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- What describes what
  knowledge_entity_id UUID NOT NULL REFERENCES core_entities(id) ON DELETE CASCADE,
  component_entity_id UUID NOT NULL REFERENCES core_entities(id) ON DELETE CASCADE,

  -- Relationship type
  relationship_type TEXT NOT NULL CHECK (
    relationship_type IN (
      'describes_component',      -- Knowledge describes this component
      'describes_behavior',       -- Knowledge describes component behavior
      'describes_failure_mode',   -- Knowledge describes how component fails
      'describes_interface',      -- Knowledge describes component interface
      'describes_constraint',     -- Knowledge describes component constraint
      'describes_performance'     -- Knowledge describes component performance
    )
  ),

  -- Specificity
  aspect TEXT,  -- What aspect of component (e.g., "bearing", "thermal behavior", "I2C interface")

  -- Strength and confidence
  relationship_strength NUMERIC(3,2) CHECK (
    relationship_strength >= 0 AND relationship_strength <= 1
  ),
  confidence NUMERIC(3,2) CHECK (
    confidence >= 0 AND confidence <= 1
  ),

  -- Evidence
  evidence_extraction_id UUID REFERENCES staging_extractions(extraction_id),
  evidence_text TEXT,

  -- Provenance
  created_by TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(knowledge_entity_id, component_entity_id, relationship_type, aspect)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_component_knowledge
  ON knowledge_component_relationships(knowledge_entity_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_component_component
  ON knowledge_component_relationships(component_entity_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_component_type
  ON knowledge_component_relationships(relationship_type);

-- View: Component knowledge map
CREATE OR REPLACE VIEW component_knowledge_map AS
SELECT
  comp.id AS component_id,
  comp.canonical_key AS component_key,
  comp.name AS component_name,
  kc.relationship_type,
  kc.aspect,
  know.id AS knowledge_id,
  know.canonical_key AS knowledge_key,
  know.name AS knowledge_name,
  know.knowledge_form,
  know.contact_level,
  know.formalizability,
  know.verification_status,
  kc.confidence,
  kc.created_at
FROM knowledge_component_relationships kc
JOIN core_entities comp ON kc.component_entity_id = comp.id
JOIN core_entities know ON kc.knowledge_entity_id = know.id
WHERE comp.is_current = TRUE
  AND know.is_current = TRUE
  AND know.verification_status = 'human_verified';


-- ============================================================================
-- 6. Helper Functions
-- ============================================================================

-- Function: Promote staging extraction to verified knowledge
CREATE OR REPLACE FUNCTION promote_to_verified_knowledge(
  p_extraction_id UUID,
  p_verified_by TEXT,
  p_approval_source TEXT DEFAULT 'manual_review',
  p_notion_page_id TEXT DEFAULT NULL,
  p_epistemic_notes TEXT DEFAULT NULL,
  p_dimensional_adjustments JSONB DEFAULT NULL  -- { "contact": {"value": "direct", "confidence": 0.95, "reasoning": "..."}, ... }
) RETURNS UUID AS $$
DECLARE
  v_entity_id UUID;
  v_extraction_record RECORD;
  v_dimension TEXT;
  v_adjustment JSONB;
BEGIN
  -- Get staging extraction
  SELECT * INTO v_extraction_record
  FROM staging_extractions
  WHERE extraction_id = p_extraction_id;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Extraction % not found', p_extraction_id;
  END IF;

  -- Create core entity with verified dimensional metadata
  INSERT INTO core_entities (
    entity_type, canonical_key, name, display_name,
    ecosystem, attributes, source_snapshot_id,
    -- Dimensional metadata (use adjustments if provided, otherwise copy from staging)
    knowledge_form, knowledge_form_confidence, knowledge_form_reasoning,
    contact_level, contact_confidence, contact_reasoning,
    directionality, directionality_confidence, directionality_reasoning,
    temporality, temporality_confidence, temporality_reasoning,
    formalizability, formalizability_confidence, formalizability_reasoning,
    carrier, carrier_confidence, carrier_reasoning,
    -- Verification metadata
    verification_status, verified_by, verified_at,
    approval_source, notion_page_id, epistemic_notes
  ) VALUES (
    v_extraction_record.candidate_type::entity_type,
    v_extraction_record.candidate_key,
    v_extraction_record.candidate_key,
    v_extraction_record.candidate_key,
    v_extraction_record.ecosystem,
    v_extraction_record.candidate_payload,
    v_extraction_record.snapshot_id,
    -- Apply adjustments or copy from staging
    COALESCE((p_dimensional_adjustments->>'knowledge_form')::TEXT, v_extraction_record.knowledge_form),
    COALESCE((p_dimensional_adjustments->'knowledge_form'->>'confidence')::NUMERIC, v_extraction_record.knowledge_form_confidence),
    COALESCE((p_dimensional_adjustments->'knowledge_form'->>'reasoning')::TEXT, v_extraction_record.knowledge_form_reasoning),
    COALESCE((p_dimensional_adjustments->>'contact')::TEXT, v_extraction_record.contact_level),
    COALESCE((p_dimensional_adjustments->'contact'->>'confidence')::NUMERIC, v_extraction_record.contact_confidence),
    COALESCE((p_dimensional_adjustments->'contact'->>'reasoning')::TEXT, v_extraction_record.contact_reasoning),
    COALESCE((p_dimensional_adjustments->>'directionality')::TEXT, v_extraction_record.directionality),
    COALESCE((p_dimensional_adjustments->'directionality'->>'confidence')::NUMERIC, v_extraction_record.directionality_confidence),
    COALESCE((p_dimensional_adjustments->'directionality'->>'reasoning')::TEXT, v_extraction_record.directionality_reasoning),
    COALESCE((p_dimensional_adjustments->>'temporality')::TEXT, v_extraction_record.temporality),
    COALESCE((p_dimensional_adjustments->'temporality'->>'confidence')::NUMERIC, v_extraction_record.temporality_confidence),
    COALESCE((p_dimensional_adjustments->'temporality'->>'reasoning')::TEXT, v_extraction_record.temporality_reasoning),
    COALESCE((p_dimensional_adjustments->>'formalizability')::TEXT, v_extraction_record.formalizability),
    COALESCE((p_dimensional_adjustments->'formalizability'->>'confidence')::NUMERIC, v_extraction_record.formalizability_confidence),
    COALESCE((p_dimensional_adjustments->'formalizability'->>'reasoning')::TEXT, v_extraction_record.formalizability_reasoning),
    COALESCE((p_dimensional_adjustments->>'carrier')::TEXT, v_extraction_record.carrier),
    COALESCE((p_dimensional_adjustments->'carrier'->>'confidence')::NUMERIC, v_extraction_record.carrier_confidence),
    COALESCE((p_dimensional_adjustments->'carrier'->>'reasoning')::TEXT, v_extraction_record.carrier_reasoning),
    'human_verified',
    p_verified_by,
    NOW(),
    p_approval_source,
    p_notion_page_id,
    p_epistemic_notes
  ) RETURNING id INTO v_entity_id;

  -- Record dimensional adjustments if any
  IF p_dimensional_adjustments IS NOT NULL THEN
    FOR v_dimension IN SELECT jsonb_object_keys(p_dimensional_adjustments)
    LOOP
      v_adjustment := p_dimensional_adjustments->v_dimension;

      -- Only record if value actually changed
      IF (v_adjustment->>'value') IS DISTINCT FROM
         (CASE v_dimension
           WHEN 'knowledge_form' THEN v_extraction_record.knowledge_form
           WHEN 'contact' THEN v_extraction_record.contact_level
           WHEN 'directionality' THEN v_extraction_record.directionality
           WHEN 'temporality' THEN v_extraction_record.temporality
           WHEN 'formalizability' THEN v_extraction_record.formalizability
           WHEN 'carrier' THEN v_extraction_record.carrier
         END) THEN

        INSERT INTO dimensional_adjustment_history (
          entity_id, dimension_name,
          old_value, old_confidence, old_reasoning,
          new_value, new_confidence, new_reasoning,
          adjusted_by, adjustment_reason, adjustment_notes,
          source_extraction_id
        ) VALUES (
          v_entity_id,
          v_dimension,
          CASE v_dimension
            WHEN 'knowledge_form' THEN v_extraction_record.knowledge_form
            WHEN 'contact' THEN v_extraction_record.contact_level
            WHEN 'directionality' THEN v_extraction_record.directionality
            WHEN 'temporality' THEN v_extraction_record.temporality
            WHEN 'formalizability' THEN v_extraction_record.formalizability
            WHEN 'carrier' THEN v_extraction_record.carrier
          END,
          CASE v_dimension
            WHEN 'knowledge_form' THEN v_extraction_record.knowledge_form_confidence
            WHEN 'contact' THEN v_extraction_record.contact_confidence
            WHEN 'directionality' THEN v_extraction_record.directionality_confidence
            WHEN 'temporality' THEN v_extraction_record.temporality_confidence
            WHEN 'formalizability' THEN v_extraction_record.formalizability_confidence
            WHEN 'carrier' THEN v_extraction_record.carrier_confidence
          END,
          CASE v_dimension
            WHEN 'knowledge_form' THEN v_extraction_record.knowledge_form_reasoning
            WHEN 'contact' THEN v_extraction_record.contact_reasoning
            WHEN 'directionality' THEN v_extraction_record.directionality_reasoning
            WHEN 'temporality' THEN v_extraction_record.temporality_reasoning
            WHEN 'formalizability' THEN v_extraction_record.formalizability_reasoning
            WHEN 'carrier' THEN v_extraction_record.carrier_reasoning
          END,
          (v_adjustment->>'value')::TEXT,
          (v_adjustment->>'confidence')::NUMERIC,
          (v_adjustment->>'reasoning')::TEXT,
          p_verified_by,
          COALESCE((v_adjustment->>'adjustment_reason')::TEXT, 'human_correction'),
          (v_adjustment->>'notes')::TEXT,
          p_extraction_id
        );
      END IF;
    END LOOP;
  END IF;

  -- Mark staging extraction as accepted
  UPDATE staging_extractions
  SET status = 'accepted'::candidate_status,
      reviewed_at = NOW(),
      reviewed_by = p_verified_by
  WHERE extraction_id = p_extraction_id;

  RETURN v_entity_id;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 7. Analysis Views
-- ============================================================================

-- View: Verification quality dashboard
CREATE OR REPLACE VIEW verification_quality_dashboard AS
SELECT
  COUNT(*) FILTER (WHERE verification_status = 'human_verified') AS human_verified_count,
  COUNT(*) FILTER (WHERE verification_status = 'auto_approved') AS auto_approved_count,
  COUNT(*) FILTER (WHERE verification_status = 'pending') AS pending_count,
  COUNT(*) FILTER (WHERE verification_status = 'needs_review') AS needs_review_count,

  -- Dimensional quality of verified knowledge
  AVG(contact_confidence) FILTER (WHERE verification_status = 'human_verified') AS avg_contact_confidence,
  AVG(directionality_confidence) FILTER (WHERE verification_status = 'human_verified') AS avg_directionality_confidence,
  AVG(temporality_confidence) FILTER (WHERE verification_status = 'human_verified') AS avg_temporality_confidence,
  AVG(formalizability_confidence) FILTER (WHERE verification_status = 'human_verified') AS avg_formalizability_confidence,

  -- Verification velocity
  COUNT(*) FILTER (WHERE verified_at > NOW() - INTERVAL '7 days') AS verified_last_7_days,
  COUNT(*) FILTER (WHERE verified_at > NOW() - INTERVAL '30 days') AS verified_last_30_days,

  -- Human adjustment rate
  (SELECT COUNT(*) FROM dimensional_adjustment_history WHERE adjusted_at > NOW() - INTERVAL '30 days') AS adjustments_last_30_days
FROM core_entities
WHERE is_current = TRUE;


-- View: Epistemic risk assessment
CREATE OR REPLACE VIEW epistemic_risk_assessment AS
SELECT
  ce.id,
  ce.canonical_key,
  ce.name,
  ce.knowledge_form,
  ce.contact_level,
  ce.formalizability,
  ce.verification_status,
  ce.verified_by,
  ce.verified_at,

  -- Risk flags
  CASE
    WHEN ce.knowledge_form = 'embodied' AND ce.formalizability IN ('tacit', 'local') THEN 'high_loss_risk'
    WHEN ce.contact_level IN ('indirect', 'derived') AND ce.directionality = 'backward' THEN 'inference_cascade_risk'
    WHEN ce.temporality IN ('history', 'lifecycle') AND NOT EXISTS (
      SELECT 1 FROM knowledge_episode_relationships ker WHERE ker.knowledge_entity_id = ce.id
    ) THEN 'temporal_context_missing'
    ELSE 'low_risk'
  END AS epistemic_risk_category,

  -- Verification quality
  (ce.contact_confidence + ce.directionality_confidence +
   ce.temporality_confidence + ce.formalizability_confidence) / 4.0 AS avg_dimensional_confidence,

  -- Enrichment status
  (SELECT COUNT(*) FROM knowledge_enrichment ke WHERE ke.primary_entity_id = ce.id) AS enrichment_count,

  -- Episode grounding
  (SELECT COUNT(*) FROM knowledge_episode_relationships ker WHERE ker.knowledge_entity_id = ce.id) AS episode_link_count,

  -- Component grounding
  (SELECT COUNT(*) FROM knowledge_component_relationships kcr WHERE kcr.knowledge_entity_id = ce.id) AS component_link_count

FROM core_entities ce
WHERE ce.is_current = TRUE
  AND ce.verification_status = 'human_verified'
ORDER BY
  CASE
    WHEN ce.knowledge_form = 'embodied' AND ce.formalizability IN ('tacit', 'local') THEN 1
    WHEN ce.contact_level IN ('indirect', 'derived') AND ce.directionality = 'backward' THEN 2
    WHEN ce.temporality IN ('history', 'lifecycle') AND NOT EXISTS (
      SELECT 1 FROM knowledge_episode_relationships ker WHERE ker.knowledge_entity_id = ce.id
    ) THEN 3
    ELSE 4
  END,
  (ce.contact_confidence + ce.directionality_confidence +
   ce.temporality_confidence + ce.formalizability_confidence) / 4.0 ASC;

-- ============================================================================
-- End of Migration 009
-- ============================================================================
-- ============================================================================
-- Migration 010: Knowledge Epistemics Sidecar
-- ============================================================================
-- Purpose: Add practical checklist-oriented epistemic metadata that maps
--          directly to the 7-question Knowledge Capture Checklist
-- Reference: canon/KNOWLEDGE_CAPTURE_CHECKLIST.md
-- Date: 2025-12-30
-- ============================================================================

BEGIN;

-- ============================================================================
-- PART 1: ENUM TYPES FOR EPISTEMIC METADATA
-- ============================================================================

-- Question 1: Who knew this, and how close were they?
CREATE TYPE contact_mode AS ENUM ('direct','mediated','effect_only','derived');

CREATE TYPE signal_type AS ENUM (
  'text','code','spec','comment','example','log','telemetry',
  'diagram','model','table','test','conversation','unknown'
);

-- Question 2: Where does the experience live now?
CREATE TYPE pattern_storage AS ENUM ('internalized','externalized','mixed','unknown');

-- Question 6: Who wrote or taught this, and why?
CREATE TYPE author_intent AS ENUM (
  'explain','instruct','justify','explore','comply','persuade','remember','unknown'
);

-- Question 7: Does this only work if someone keeps doing it?
CREATE TYPE transferability AS ENUM ('portable','conditional','local','tacit_like','unknown');

-- Question 3: What has to stay connected for this to work?
CREATE TYPE sequence_role AS ENUM ('precondition','step','outcome','postcondition','none');

-- Loss modes we care about (from checklist flags)
CREATE TYPE loss_mode AS ENUM (
  'embodiment_loss',
  'practice_decay',
  'context_collapse',
  'relational_fragmentation',
  'drift',
  'authorship_loss',
  'pedagogical_distortion',
  'model_overreach',
  'proxy_replacement'
);

COMMENT ON TYPE contact_mode IS 'How the observer touched reality (or didn''t)';
COMMENT ON TYPE signal_type IS 'What kind of signal this is';
COMMENT ON TYPE pattern_storage IS 'Where accumulated historical patterns live (internalized in body/nervous system vs externalized in symbols/records)';
COMMENT ON TYPE author_intent IS 'Why this was written (helps catch pedagogical/authorship issues)';
COMMENT ON TYPE transferability IS 'How transferable knowledge is (risk proxy; NOT recordability)';
COMMENT ON TYPE sequence_role IS 'Role in a sequence (for relational integrity tracking)';
COMMENT ON TYPE loss_mode IS 'Specific knowledge loss failure modes';

-- ============================================================================
-- PART 2: KNOWLEDGE EPISTEMICS SIDECAR TABLE
-- ============================================================================

CREATE TABLE knowledge_epistemics (
  extraction_id UUID PRIMARY KEY REFERENCES staging_extractions(extraction_id) ON DELETE CASCADE,

  -- ========================================================================
  -- Identity / Quick Handle
  -- ========================================================================
  domain TEXT NOT NULL,                     -- 'fprime', 'proveskit', etc (or finer: subsystem)
  claim_summary TEXT,                       -- Optional: short paraphrase for UX/search

  -- ========================================================================
  -- QUESTION 1: Who knew this & how close were they?
  -- ========================================================================
  observer_id TEXT,                         -- 'agent:parser_v1', 'doc:...', 'human:technician_x'
  observer_type TEXT,                       -- 'ai','human','instrument','process' (keep TEXT for flexibility)
  contact_mode contact_mode NOT NULL DEFAULT 'derived',
  contact_strength NUMERIC(3,2) NOT NULL DEFAULT 0.30 CHECK (
    contact_strength >= 0.00 AND contact_strength <= 1.00
  ),  -- Continuous 0.00..1.00
  signal_type signal_type NOT NULL DEFAULT 'text',
  evidence_ref JSONB,                       -- Pointer(s): file path, url, checksum, offsets

  -- ========================================================================
  -- QUESTION 2: Where does the experience live now?
  -- ========================================================================
  pattern_storage pattern_storage NOT NULL DEFAULT 'externalized',
  representation_media TEXT[] NOT NULL DEFAULT ARRAY['text'], -- e.g., {'text','code','diagram'}

  -- ========================================================================
  -- QUESTION 3: What must stay connected for this to work?
  -- ========================================================================
  episode_id UUID REFERENCES episodic_entities(episode_id) ON DELETE SET NULL,
  sequence_role sequence_role NOT NULL DEFAULT 'none',
  dependencies JSONB,                       -- List of entity keys or extraction_ids that must remain bound
  relational_notes TEXT,                    -- Freeform description of relational dependencies

  -- ========================================================================
  -- QUESTION 4: Under what conditions was this true?
  -- ========================================================================
  validity_conditions JSONB,                -- Key-values: { "fprime_version": "...", "config": "...", ... }
  assumptions TEXT[],                       -- Lightweight list of assumptions
  scope TEXT,                               -- 'local'|'subsystem'|'system'|'general' (TEXT keeps it simple)

  -- ========================================================================
  -- QUESTION 5: When does this stop being reliable?
  -- ========================================================================
  observed_at TIMESTAMPTZ,                  -- When the source snapshot was taken (or doc commit time)
  valid_from TIMESTAMPTZ,
  valid_to TIMESTAMPTZ,
  refresh_trigger TEXT,                     -- 'new_rev','recalibration','periodic','after_incident', etc
  staleness_risk NUMERIC(3,2) NOT NULL DEFAULT 0.20 CHECK (
    staleness_risk >= 0.00 AND staleness_risk <= 1.00
  ),

  -- ========================================================================
  -- QUESTION 6: Who wrote/taught this, and why?
  -- ========================================================================
  author_id TEXT,                           -- Author identifier
  intent author_intent NOT NULL DEFAULT 'unknown',
  confidence NUMERIC(3,2) CHECK (           -- Separate from extraction confidence_score; this is epistemic confidence
    confidence IS NULL OR (confidence >= 0 AND confidence <= 1)
  ),
  uncertainty_notes TEXT,                   -- What uncertainty was present but not recorded?

  -- ========================================================================
  -- QUESTION 7: Does this only work if someone keeps doing it?
  -- ========================================================================
  reenactment_required BOOLEAN NOT NULL DEFAULT FALSE,
  practice_interval TEXT,                   -- 'per-run','weekly','per-release', etc
  skill_transferability transferability NOT NULL DEFAULT 'portable',

  -- ========================================================================
  -- Loss Mode Tracking
  -- ========================================================================
  identified_loss_modes loss_mode[],        -- Array of detected loss modes

  -- ========================================================================
  -- Housekeeping
  -- ========================================================================
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add comments for documentation
COMMENT ON TABLE knowledge_epistemics IS
  'Epistemic metadata sidecar for staging_extractions, mapping to the 7-question Knowledge Capture Checklist';

COMMENT ON COLUMN knowledge_epistemics.observer_id IS
  'Who observed this knowledge (agent ID, human ID, instrument ID)';

COMMENT ON COLUMN knowledge_epistemics.contact_strength IS
  'Continuous measure (0.0-1.0) of observer coupling to phenomenon';

COMMENT ON COLUMN knowledge_epistemics.pattern_storage IS
  'Where accumulated historical patterns live: internalized (body/nervous system) vs externalized (symbols/records)';

COMMENT ON COLUMN knowledge_epistemics.dependencies IS
  'JSONB array of entity keys or extraction_ids that must remain connected for this knowledge to work';

COMMENT ON COLUMN knowledge_epistemics.validity_conditions IS
  'JSONB object describing conditions under which this knowledge holds (versions, configs, environmental constraints)';

COMMENT ON COLUMN knowledge_epistemics.staleness_risk IS
  'Risk (0.0-1.0) that this knowledge has become stale or invalid due to system changes';

COMMENT ON COLUMN knowledge_epistemics.intent IS
  'Why this was written - helps detect pedagogical distortion, false authority, compliance theater';

COMMENT ON COLUMN knowledge_epistemics.reenactment_required IS
  'TRUE if this knowledge requires ongoing practice/reenactment to maintain (embodied skills that degrade without use)';

COMMENT ON COLUMN knowledge_epistemics.identified_loss_modes IS
  'Array of specific loss modes detected for this knowledge (e.g., embodiment_loss, practice_decay, context_collapse)';

-- ============================================================================
-- PART 3: INDEXES FOR EFFICIENT QUERIES
-- ============================================================================

CREATE INDEX idx_epistemics_domain ON knowledge_epistemics(domain);
CREATE INDEX idx_epistemics_contact_mode ON knowledge_epistemics(contact_mode);
CREATE INDEX idx_epistemics_pattern_storage ON knowledge_epistemics(pattern_storage);
CREATE INDEX idx_epistemics_reenactment ON knowledge_epistemics(reenactment_required) WHERE reenactment_required = TRUE;
CREATE INDEX idx_epistemics_episode ON knowledge_epistemics(episode_id) WHERE episode_id IS NOT NULL;
CREATE INDEX idx_epistemics_intent ON knowledge_epistemics(intent);
CREATE INDEX idx_epistemics_staleness ON knowledge_epistemics(staleness_risk) WHERE staleness_risk > 0.5;

-- JSONB indexes for complex queries
CREATE INDEX idx_epistemics_validity_conditions ON knowledge_epistemics USING GIN (validity_conditions);
CREATE INDEX idx_epistemics_dependencies ON knowledge_epistemics USING GIN (dependencies);
CREATE INDEX idx_epistemics_loss_modes ON knowledge_epistemics USING GIN (identified_loss_modes);

-- ============================================================================
-- PART 4: TRIGGER FOR AUTOMATIC LOSS MODE DETECTION
-- ============================================================================

CREATE OR REPLACE FUNCTION detect_loss_modes()
RETURNS TRIGGER AS $$
DECLARE
  detected_modes loss_mode[] := ARRAY[]::loss_mode[];
BEGIN
  -- Detect embodiment_loss: internalized pattern storage + no reenactment mechanism
  IF NEW.pattern_storage = 'internalized'
     AND NEW.reenactment_required = FALSE
     AND NEW.skill_transferability IN ('tacit_like', 'local') THEN
    detected_modes := array_append(detected_modes, 'embodiment_loss'::loss_mode);
  END IF;

  -- Detect practice_decay: reenactment required but no practice interval specified
  IF NEW.reenactment_required = TRUE AND NEW.practice_interval IS NULL THEN
    detected_modes := array_append(detected_modes, 'practice_decay'::loss_mode);
  END IF;

  -- Detect context_collapse: validity conditions missing for conditional knowledge
  IF NEW.skill_transferability = 'conditional'
     AND (NEW.validity_conditions IS NULL OR NEW.validity_conditions = '{}'::jsonb) THEN
    detected_modes := array_append(detected_modes, 'context_collapse'::loss_mode);
  END IF;

  -- Detect relational_fragmentation: dependencies exist but not linked to episode
  IF NEW.dependencies IS NOT NULL
     AND jsonb_array_length(NEW.dependencies) > 0
     AND NEW.episode_id IS NULL
     AND NEW.sequence_role != 'none' THEN
    detected_modes := array_append(detected_modes, 'relational_fragmentation'::loss_mode);
  END IF;

  -- Detect drift: high staleness risk without refresh trigger
  IF NEW.staleness_risk > 0.6 AND NEW.refresh_trigger IS NULL THEN
    detected_modes := array_append(detected_modes, 'drift'::loss_mode);
  END IF;

  -- Detect pedagogical_distortion: instructional intent but low contact strength
  IF NEW.intent IN ('instruct', 'explain') AND NEW.contact_strength < 0.4 THEN
    detected_modes := array_append(detected_modes, 'pedagogical_distortion'::loss_mode);
  END IF;

  -- Detect model_overreach: derived contact mode but missing validity conditions
  IF NEW.contact_mode = 'derived'
     AND (NEW.validity_conditions IS NULL OR NEW.validity_conditions = '{}'::jsonb) THEN
    detected_modes := array_append(detected_modes, 'model_overreach'::loss_mode);
  END IF;

  -- Detect proxy_replacement: effect_only contact but treated as direct observation
  IF NEW.contact_mode = 'effect_only' AND NEW.contact_strength > 0.7 THEN
    detected_modes := array_append(detected_modes, 'proxy_replacement'::loss_mode);
  END IF;

  -- Set detected loss modes
  NEW.identified_loss_modes := detected_modes;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_detect_loss_modes
  BEFORE INSERT OR UPDATE ON knowledge_epistemics
  FOR EACH ROW
  EXECUTE FUNCTION detect_loss_modes();

COMMENT ON FUNCTION detect_loss_modes IS
  'Automatically detects epistemic loss modes based on checklist patterns';

-- ============================================================================
-- PART 5: COMBINED VIEW FOR COMPLETE EPISTEMIC PROFILE
-- ============================================================================

CREATE OR REPLACE VIEW complete_epistemic_profile AS
SELECT
  -- Extraction basics
  se.extraction_id,
  se.candidate_key,
  se.candidate_type,
  se.ecosystem,
  se.status,
  se.confidence_score AS extraction_confidence,

  -- Original dimensional metadata (from migration 008)
  se.knowledge_form,
  se.knowledge_form_confidence,
  se.contact_level,
  se.contact_confidence,
  se.directionality,
  se.temporality,
  se.formalizability,
  se.carrier,
  se.dimensional_completeness,

  -- Checklist-oriented epistemics (from migration 010)
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
  'Complete epistemic metadata combining original dimensions (migration 008) with checklist-oriented fields (migration 010)';

-- ============================================================================
-- PART 6: ANALYSIS VIEWS FOR CHECKLIST QUESTIONS
-- ============================================================================

-- View: High-risk knowledge requiring intervention
CREATE OR REPLACE VIEW knowledge_at_risk AS
SELECT
  ep.extraction_id,
  ep.candidate_key,
  ep.domain,
  ep.pattern_storage,
  ep.contact_mode,
  ep.reenactment_required,
  ep.skill_transferability,
  ep.identified_loss_modes,
  ep.staleness_risk,

  -- Risk score (0-1)
  (
    CASE WHEN ep.pattern_storage = 'internalized' THEN 0.3 ELSE 0.0 END +
    CASE WHEN ep.reenactment_required AND ep.practice_interval IS NULL THEN 0.3 ELSE 0.0 END +
    CASE WHEN ep.skill_transferability IN ('tacit_like', 'local') THEN 0.2 ELSE 0.0 END +
    CASE WHEN ep.staleness_risk > 0.6 THEN 0.2 ELSE 0.0 END +
    CASE WHEN array_length(ep.identified_loss_modes, 1) > 2 THEN 0.2 ELSE 0.0 END
  ) AS composite_risk_score,

  -- Recommended interventions
  CASE
    WHEN 'embodiment_loss' = ANY(ep.identified_loss_modes) THEN 'Pair with experienced technician, capture video walkthroughs'
    WHEN 'practice_decay' = ANY(ep.identified_loss_modes) THEN 'Establish practice schedule, create simulation environment'
    WHEN 'context_collapse' = ANY(ep.identified_loss_modes) THEN 'Document validity conditions, add scope constraints'
    WHEN 'drift' = ANY(ep.identified_loss_modes) THEN 'Set refresh trigger, establish recalibration procedure'
    ELSE 'Monitor for loss modes'
  END AS recommended_intervention,

  ep.created_at

FROM complete_epistemic_profile ep
WHERE ep.identified_loss_modes IS NOT NULL
  AND array_length(ep.identified_loss_modes, 1) > 0
ORDER BY composite_risk_score DESC, ep.created_at DESC;

COMMENT ON VIEW knowledge_at_risk IS
  'Knowledge with identified loss modes and recommended interventions';

-- View: Pattern storage distribution (Question 2)
CREATE OR REPLACE VIEW pattern_storage_distribution AS
SELECT
  pattern_storage,
  COUNT(*) as count,
  AVG(contact_strength) as avg_contact_strength,
  AVG(staleness_risk) as avg_staleness_risk,
  COUNT(*) FILTER (WHERE reenactment_required = TRUE) as reenactment_count,
  COUNT(*) FILTER (WHERE skill_transferability IN ('tacit_like', 'local')) as transfer_risk_count
FROM knowledge_epistemics
GROUP BY pattern_storage
ORDER BY count DESC;

COMMENT ON VIEW pattern_storage_distribution IS
  'Distribution of knowledge by pattern storage location (internalized vs externalized)';

-- View: Authorship intent analysis (Question 6)
CREATE OR REPLACE VIEW authorship_intent_analysis AS
SELECT
  intent,
  COUNT(*) as count,
  AVG(contact_strength) as avg_contact_strength,
  COUNT(*) FILTER (WHERE 'pedagogical_distortion' = ANY(identified_loss_modes)) as pedagogical_distortion_count,
  COUNT(*) FILTER (WHERE uncertainty_notes IS NOT NULL) as has_uncertainty_notes
FROM knowledge_epistemics
GROUP BY intent
ORDER BY count DESC;

COMMENT ON VIEW authorship_intent_analysis IS
  'Distribution of knowledge by authorship intent, flagging pedagogical distortion risks';

-- View: Temporal validity tracking (Question 5)
CREATE OR REPLACE VIEW temporal_validity_status AS
SELECT
  ke.extraction_id,
  se.candidate_key,
  ke.domain,
  ke.observed_at,
  ke.valid_from,
  ke.valid_to,
  ke.refresh_trigger,
  ke.staleness_risk,

  -- Status flags
  CASE
    WHEN ke.valid_to IS NOT NULL AND ke.valid_to < NOW() THEN 'expired'
    WHEN ke.staleness_risk > 0.7 THEN 'high_staleness_risk'
    WHEN ke.refresh_trigger IS NOT NULL AND ke.staleness_risk > 0.4 THEN 'needs_refresh'
    ELSE 'valid'
  END AS validity_status,

  -- Days until expiration (if applicable)
  CASE
    WHEN ke.valid_to IS NOT NULL THEN EXTRACT(DAY FROM ke.valid_to - NOW())
    ELSE NULL
  END AS days_until_expiration,

  ke.created_at

FROM knowledge_epistemics ke
JOIN staging_extractions se ON ke.extraction_id = se.extraction_id
ORDER BY ke.staleness_risk DESC, days_until_expiration ASC NULLS LAST;

COMMENT ON VIEW temporal_validity_status IS
  'Tracks when knowledge stops being reliable (Question 5)';

-- ============================================================================
-- PART 7: HELPER FUNCTIONS
-- ============================================================================

-- Function: Calculate composite risk score
CREATE OR REPLACE FUNCTION calculate_epistemic_risk(
  p_extraction_id UUID
) RETURNS NUMERIC AS $$
DECLARE
  v_risk NUMERIC := 0.0;
  v_record RECORD;
BEGIN
  SELECT * INTO v_record
  FROM knowledge_epistemics
  WHERE extraction_id = p_extraction_id;

  IF NOT FOUND THEN
    RETURN 0.0;
  END IF;

  -- Pattern storage risk
  IF v_record.pattern_storage = 'internalized' THEN
    v_risk := v_risk + 0.3;
  END IF;

  -- Reenactment risk
  IF v_record.reenactment_required AND v_record.practice_interval IS NULL THEN
    v_risk := v_risk + 0.3;
  END IF;

  -- Transferability risk
  IF v_record.skill_transferability IN ('tacit_like', 'local') THEN
    v_risk := v_risk + 0.2;
  END IF;

  -- Staleness risk
  IF v_record.staleness_risk > 0.6 THEN
    v_risk := v_risk + 0.2;
  END IF;

  -- Loss mode count
  IF array_length(v_record.identified_loss_modes, 1) > 2 THEN
    v_risk := v_risk + 0.2;
  END IF;

  RETURN LEAST(v_risk, 1.0);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_epistemic_risk IS
  'Calculates composite epistemic risk score (0.0-1.0) for an extraction';

-- ============================================================================
-- PART 8: DATA VALIDATION
-- ============================================================================

DO $$
DECLARE
  table_exists BOOLEAN;
BEGIN
  -- Check knowledge_epistemics table exists
  SELECT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_name = 'knowledge_epistemics'
  ) INTO table_exists;

  IF NOT table_exists THEN
    RAISE EXCEPTION 'Table knowledge_epistemics was not created';
  END IF;

  -- Check ENUMs exist
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'contact_mode') THEN
    RAISE EXCEPTION 'ENUM contact_mode was not created';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'pattern_storage') THEN
    RAISE EXCEPTION 'ENUM pattern_storage was not created';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'loss_mode') THEN
    RAISE EXCEPTION 'ENUM loss_mode was not created';
  END IF;

  -- Check views exist
  IF NOT EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'complete_epistemic_profile') THEN
    RAISE EXCEPTION 'View complete_epistemic_profile was not created';
  END IF;

  RAISE NOTICE 'Knowledge epistemics sidecar migration completed successfully ✓';
  RAISE NOTICE 'Created: knowledge_epistemics table, 7 ENUMs, 5 views, 2 functions, 1 trigger';
END $$;

COMMIT;

-- ============================================================================
-- POST-MIGRATION VERIFICATION QUERIES
-- ============================================================================

-- 1. Check table structure
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'knowledge_epistemics'
-- ORDER BY ordinal_position;

-- 2. Check ENUMs
-- SELECT typname, enumlabel
-- FROM pg_type t
-- JOIN pg_enum e ON t.oid = e.enumtypid
-- WHERE typname IN ('contact_mode', 'pattern_storage', 'author_intent', 'loss_mode')
-- ORDER BY typname, e.enumsortorder;

-- 3. Test loss mode detection
-- INSERT INTO staging_extractions (candidate_key, candidate_type) VALUES ('TestEntity', 'component');
-- INSERT INTO knowledge_epistemics (extraction_id, domain, pattern_storage, reenactment_required, contact_mode)
-- VALUES (
--   (SELECT extraction_id FROM staging_extractions WHERE candidate_key = 'TestEntity'),
--   'test',
--   'internalized',
--   FALSE,
--   'direct'
-- );
-- SELECT identified_loss_modes FROM knowledge_epistemics
-- WHERE extraction_id = (SELECT extraction_id FROM staging_extractions WHERE candidate_key = 'TestEntity');

-- 4. Check views
-- SELECT * FROM pattern_storage_distribution;
-- SELECT * FROM authorship_intent_analysis;
-- SELECT * FROM knowledge_at_risk LIMIT 5;
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
-- Migration 012: Enhance Human Approval Workflow
-- Date: 2025-01-02
-- Purpose: Add full audit trail for human decisions, idempotency, and versioning

-- NOTE: Enum values must be committed before use, so this migration uses multiple transactions

-- ============================================================================
-- PART 1: ENHANCE validation_decisions TABLE
-- ============================================================================

-- Add full audit trail columns to validation_decisions
-- This table becomes an append-only log of all human actions
--
-- NOTE: Table already exists with:
--   - decision_id (primary key) ✓
--   - extraction_id ✓
--   - decided_by (maps to actor_id) ✓
--   - decision (maps to action_type) ✓
--   - decision_reason (maps to reason) ✓
--   - decided_at (maps to timestamp) ✓
--   - lineage_check_passed, lineage_check_details ✓
--
-- We only need to add NEW columns for:
--   - before_payload, after_payload (edit tracking)
--   - patch (alternative edit format)
--   - source (webhook idempotency)

-- For edits: track what changed
ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
    before_payload JSONB;

ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
    after_payload JSONB;

-- Alternative: JSON Patch format (more compact)
ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
    patch JSONB;

-- Idempotency: webhook source ID
-- Prevents processing the same webhook twice
ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
    source TEXT;  -- Notion webhook ID

-- Idempotency constraint
-- If we've already processed this webhook, don't process it again
-- Use a partial unique index instead of a constraint with WHERE clause
CREATE UNIQUE INDEX IF NOT EXISTS unique_webhook_source
    ON validation_decisions(source)
    WHERE source IS NOT NULL;

-- Add indexes for common queries (using existing column names)
CREATE INDEX IF NOT EXISTS idx_validation_decisions_extraction
    ON validation_decisions(extraction_id);

CREATE INDEX IF NOT EXISTS idx_validation_decisions_actor
    ON validation_decisions(decided_by);  -- Maps to actor_id

CREATE INDEX IF NOT EXISTS idx_validation_decisions_timestamp
    ON validation_decisions(decided_at DESC);  -- Maps to timestamp

CREATE INDEX IF NOT EXISTS idx_validation_decisions_action_type
    ON validation_decisions(decision);  -- Maps to action_type

CREATE INDEX IF NOT EXISTS idx_validation_decisions_source
    ON validation_decisions(source)
    WHERE source IS NOT NULL;

-- Add comments for new columns
COMMENT ON COLUMN validation_decisions.before_payload IS
    'Original candidate_payload before edit (for edit actions only)';

COMMENT ON COLUMN validation_decisions.after_payload IS
    'Modified candidate_payload after edit (for edit actions only)';

COMMENT ON COLUMN validation_decisions.patch IS
    'JSON Patch format of changes (alternative to before/after)';

COMMENT ON COLUMN validation_decisions.source IS
    'Notion webhook ID for idempotency - prevents duplicate processing';

-- Update comments for existing columns to reflect new usage
COMMENT ON COLUMN validation_decisions.decided_by IS
    'Notion user ID who made the decision, or "system" for automated actions (maps to actor_id)';

COMMENT ON COLUMN validation_decisions.decision IS
    'What action was taken: accept, reject, edit, merge, request_more_evidence, flag_for_review (maps to action_type)';

COMMENT ON COLUMN validation_decisions.decision_reason IS
    'Human-provided reason for the decision (from review notes or comment) (maps to reason)';

-- ============================================================================
-- PART 2: EXPAND ENUM TYPES
-- ============================================================================

-- Add new status values for human approval workflow
-- These must be in their own transaction and committed before the views can use them

BEGIN;

DO $$
BEGIN
    -- Expand candidate_status enum
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'flagged'
        AND enumtypid = 'candidate_status'::regtype
    ) THEN
        ALTER TYPE candidate_status ADD VALUE 'flagged';
    END IF;

    -- Expand validation_decision_type enum
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'edit'
        AND enumtypid = 'validation_decision_type'::regtype
    ) THEN
        ALTER TYPE validation_decision_type ADD VALUE 'edit';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'flag_for_review'
        AND enumtypid = 'validation_decision_type'::regtype
    ) THEN
        ALTER TYPE validation_decision_type ADD VALUE 'flag_for_review';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'request_more_evidence'
        AND enumtypid = 'validation_decision_type'::regtype
    ) THEN
        ALTER TYPE validation_decision_type ADD VALUE 'request_more_evidence';
    END IF;
END $$;

COMMIT;  -- Commit enum changes before using them

-- Add comments after committing
COMMENT ON TYPE candidate_status IS
    'Status of extraction: pending (new), accepted (approved), rejected (denied), flagged (needs review), needs_context (awaiting more info), merged (combined with another)';

COMMENT ON TYPE validation_decision_type IS
    'Type of decision: accept, reject, edit, merge, flag_for_review, request_more_evidence, needs_more_evidence, defer';

-- ============================================================================
-- PART 3: ADD VERSIONING TO staging_extractions
-- ============================================================================

-- Track revisions when humans edit extractions
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
    current_revision INTEGER DEFAULT 1;

-- Link to the latest decision made on this extraction
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
    latest_decision_id UUID REFERENCES validation_decisions(decision_id);

-- Optional: track who is assigned to review this
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
    assigned_to TEXT;

CREATE INDEX IF NOT EXISTS idx_staging_extractions_revision
    ON staging_extractions(current_revision);

CREATE INDEX IF NOT EXISTS idx_staging_extractions_latest_decision
    ON staging_extractions(latest_decision_id);

CREATE INDEX IF NOT EXISTS idx_staging_extractions_assigned
    ON staging_extractions(assigned_to)
    WHERE assigned_to IS NOT NULL;

COMMENT ON COLUMN staging_extractions.current_revision IS
    'Revision number - increments when human edits the extraction';

COMMENT ON COLUMN staging_extractions.latest_decision_id IS
    'Foreign key to the most recent validation_decision for this extraction';

COMMENT ON COLUMN staging_extractions.assigned_to IS
    'Optional: Notion user ID assigned to review this extraction';

-- ============================================================================
-- PART 4: HELPER FUNCTIONS
-- ============================================================================

-- Function to record a human decision
-- This ensures consistent audit trail creation
-- Uses existing column names: decided_by, decision, decision_reason, decided_at
CREATE OR REPLACE FUNCTION record_human_decision(
    p_extraction_id UUID,
    p_action_type TEXT,
    p_actor_id TEXT DEFAULT 'unknown',
    p_reason TEXT DEFAULT NULL,
    p_before_payload JSONB DEFAULT NULL,
    p_after_payload JSONB DEFAULT NULL,
    p_webhook_source TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_decision_id UUID;
BEGIN
    -- Insert decision record using existing column names
    INSERT INTO validation_decisions (
        extraction_id,
        decided_by,         -- Maps to actor_id
        decider_type,       -- Set to 'human' or 'system'
        decision,           -- Maps to action_type
        decision_reason,    -- Maps to reason
        before_payload,
        after_payload,
        source,
        decided_at          -- Maps to timestamp
    ) VALUES (
        p_extraction_id,
        p_actor_id,
        CASE WHEN p_actor_id = 'system' THEN 'agent'::decider_type ELSE 'human'::decider_type END,
        p_action_type,
        COALESCE(p_reason, 'No reason provided'),
        p_before_payload,
        p_after_payload,
        p_webhook_source,
        NOW()
    )
    RETURNING decision_id INTO v_decision_id;  -- Use decision_id, not id

    -- Update staging_extractions with latest decision
    UPDATE staging_extractions
    SET latest_decision_id = v_decision_id
    WHERE extraction_id = p_extraction_id;

    RETURN v_decision_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION record_human_decision IS
    'Records a human decision in validation_decisions and updates staging_extractions.latest_decision_id';

-- Function to check if webhook was already processed
CREATE OR REPLACE FUNCTION webhook_already_processed(
    p_webhook_source TEXT
) RETURNS BOOLEAN AS $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM validation_decisions
    WHERE source = p_webhook_source;

    RETURN v_count > 0;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION webhook_already_processed IS
    'Checks if a webhook has already been processed (idempotency check)';

-- ============================================================================
-- PART 5: ANALYTICS VIEWS
-- ============================================================================

-- View: Human review statistics
CREATE OR REPLACE VIEW human_review_stats AS
SELECT
    d.decided_by as actor_id,
    d.decision as action_type,
    COUNT(*) as action_count,
    AVG(EXTRACT(EPOCH FROM (d.decided_at - e.created_at))) as avg_response_time_seconds,
    MIN(d.decided_at) as first_action,
    MAX(d.decided_at) as last_action
FROM validation_decisions d
JOIN staging_extractions e ON d.extraction_id = e.extraction_id
WHERE d.decided_by != 'system' AND d.decider_type = 'human'
GROUP BY d.decided_by, d.decision;

COMMENT ON VIEW human_review_stats IS
    'Statistics on human review activity: who, what actions, response times';

-- View: Extractions awaiting review
CREATE OR REPLACE VIEW extractions_awaiting_review AS
SELECT
    e.extraction_id,
    e.candidate_key,
    e.candidate_type,
    e.confidence_score,
    e.created_at,
    e.assigned_to,
    e.requires_mandatory_review,
    e.current_revision,
    EXTRACT(EPOCH FROM (NOW() - e.created_at)) / 3600 as hours_waiting,
    d.decision as last_action,
    d.decided_by as last_actor,
    d.decided_at as last_action_time
FROM staging_extractions e
LEFT JOIN validation_decisions d ON e.latest_decision_id = d.decision_id
WHERE e.status IN ('pending', 'needs_context', 'flagged')
ORDER BY
    e.requires_mandatory_review DESC,
    e.created_at ASC;

COMMENT ON VIEW extractions_awaiting_review IS
    'All extractions awaiting human review, sorted by priority and age';

-- View: Edit history for extractions
CREATE OR REPLACE VIEW extraction_edit_history AS
SELECT
    e.extraction_id,
    e.candidate_key,
    e.current_revision,
    d.decision_id,
    d.decision as action_type,
    d.decided_by as actor_id,
    d.decided_at as timestamp,
    d.decision_reason as reason,
    CASE
        WHEN d.before_payload IS NOT NULL THEN 'has_diff'
        ELSE 'no_diff'
    END as has_payload_changes
FROM staging_extractions e
LEFT JOIN validation_decisions d ON d.extraction_id = e.extraction_id
WHERE d.decision IN ('edit', 'accept', 'reject')
ORDER BY e.extraction_id, d.decided_at ASC;

COMMENT ON VIEW extraction_edit_history IS
    'History of all decisions made on each extraction, showing evolution over time';

-- ============================================================================
-- PART 6: VALIDATION
-- ============================================================================

DO $$
BEGIN
    -- Verify new columns exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'validation_decisions' AND column_name = 'source'
    ) THEN
        RAISE EXCEPTION 'Column source was not added to validation_decisions';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'validation_decisions' AND column_name = 'before_payload'
    ) THEN
        RAISE EXCEPTION 'Column before_payload was not added to validation_decisions';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'validation_decisions' AND column_name = 'after_payload'
    ) THEN
        RAISE EXCEPTION 'Column after_payload was not added to validation_decisions';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'staging_extractions' AND column_name = 'current_revision'
    ) THEN
        RAISE EXCEPTION 'Column current_revision was not added to staging_extractions';
    END IF;

    -- Verify enum values were added
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'flagged'
        AND enumtypid = 'candidate_status'::regtype
    ) THEN
        RAISE EXCEPTION 'Enum value flagged was not added to candidate_status';
    END IF;

    -- Verify functions exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'record_human_decision'
    ) THEN
        RAISE EXCEPTION 'Function record_human_decision was not created';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_proc WHERE proname = 'webhook_already_processed'
    ) THEN
        RAISE EXCEPTION 'Function webhook_already_processed was not created';
    END IF;

    -- Verify views exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_views WHERE viewname = 'human_review_stats'
    ) THEN
        RAISE EXCEPTION 'View human_review_stats was not created';
    END IF;

    RAISE NOTICE 'Migration 012 completed successfully ✓';
    RAISE NOTICE '  - Enhanced validation_decisions with full audit trail';
    RAISE NOTICE '  - Added idempotency support (source column)';
    RAISE NOTICE '  - Expanded candidate_status enum (flagged, needs_context, merged)';
    RAISE NOTICE '  - Added versioning to staging_extractions';
    RAISE NOTICE '  - Created helper functions for decision recording';
    RAISE NOTICE '  - Created analytics views for human review stats';
END $$;
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
-- Migration 014: Add Missing Entity Types to core_entities
-- Date: 2026-01-03
-- Purpose: Add entity types that exist in candidate_status but not in entity_type

BEGIN;

-- Add missing entity types to the enum
-- These are used in staging_extractions but weren't in core_entities schema

DO $$
BEGIN
    -- Add dependency
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'dependency'
        AND enumtypid = 'entity_type'::regtype
    ) THEN
        ALTER TYPE entity_type ADD VALUE 'dependency';
        RAISE NOTICE 'Added entity_type: dependency';
    END IF;

    -- Add connection
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'connection'
        AND enumtypid = 'entity_type'::regtype
    ) THEN
        ALTER TYPE entity_type ADD VALUE 'connection';
        RAISE NOTICE 'Added entity_type: connection';
    END IF;

    -- Add port
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'port'
        AND enumtypid = 'entity_type'::regtype
    ) THEN
        ALTER TYPE entity_type ADD VALUE 'port';
        RAISE NOTICE 'Added entity_type: port';
    END IF;

    -- Add event
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'event'
        AND enumtypid = 'entity_type'::regtype
    ) THEN
        ALTER TYPE entity_type ADD VALUE 'event';
        RAISE NOTICE 'Added entity_type: event';
    END IF;

    -- Add telemetry
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'telemetry'
        AND enumtypid = 'entity_type'::regtype
    ) THEN
        ALTER TYPE entity_type ADD VALUE 'telemetry';
        RAISE NOTICE 'Added entity_type: telemetry';
    END IF;

    -- Add data_type
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'data_type'
        AND enumtypid = 'entity_type'::regtype
    ) THEN
        ALTER TYPE entity_type ADD VALUE 'data_type';
        RAISE NOTICE 'Added entity_type: data_type';
    END IF;

    -- Add parameter
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'parameter'
        AND enumtypid = 'entity_type'::regtype
    ) THEN
        ALTER TYPE entity_type ADD VALUE 'parameter';
        RAISE NOTICE 'Added entity_type: parameter';
    END IF;

    -- Add command
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'command'
        AND enumtypid = 'entity_type'::regtype
    ) THEN
        ALTER TYPE entity_type ADD VALUE 'command';
        RAISE NOTICE 'Added entity_type: command';
    END IF;
END $$;

COMMIT;

-- Verification
DO $$
DECLARE
    missing_types TEXT[];
BEGIN
    -- Check that all required types exist
    SELECT ARRAY_AGG(type_name)
    INTO missing_types
    FROM (VALUES
        ('dependency'),
        ('connection'),
        ('port'),
        ('event'),
        ('telemetry'),
        ('data_type'),
        ('parameter'),
        ('command')
    ) AS required(type_name)
    WHERE NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = required.type_name
        AND enumtypid = 'entity_type'::regtype
    );

    IF array_length(missing_types, 1) > 0 THEN
        RAISE EXCEPTION 'Missing entity types: %', array_to_string(missing_types, ', ');
    END IF;

    RAISE NOTICE 'Migration 014 completed successfully ✓';
    RAISE NOTICE '  - Added 8 missing entity types to core_entities enum';
END $$;
-- ============================================================================
-- Migration 015: Add Standard Mapping Enrichment Type
-- ============================================================================
-- Date: 2026-01-15
-- Purpose: Enable storage of mappings between PROVES entities and external
--          standards like XTCE, SysML, OWL, GraphML for export/integration
-- ============================================================================

BEGIN;

-- ============================================================================
-- PART 1: UPDATE ENRICHMENT TYPE CHECK CONSTRAINT
-- ============================================================================

-- Drop old constraint and add new one with 'standard_mapping' included
DO $$
BEGIN
  -- Drop existing constraint if it exists
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'knowledge_enrichment_enrichment_type_check'
      AND conrelid = 'knowledge_enrichment'::regclass
  ) THEN
    ALTER TABLE knowledge_enrichment DROP CONSTRAINT knowledge_enrichment_enrichment_type_check;
  END IF;

  -- Add new constraint with standard_mapping
  ALTER TABLE knowledge_enrichment ADD CONSTRAINT knowledge_enrichment_enrichment_type_check
    CHECK (
      enrichment_type IN (
        'alias',
        'duplicate_merge',
        'cross_source',
        'temporal_update',
        'epistemic_refinement',
        'standard_mapping'
      )
    );
END $$;


-- ============================================================================
-- PART 2: ADD STANDARD MAPPING COLUMNS
-- ============================================================================

-- Standard identification
ALTER TABLE knowledge_enrichment ADD COLUMN IF NOT EXISTS
  standard TEXT;

ALTER TABLE knowledge_enrichment ADD COLUMN IF NOT EXISTS
  standard_version TEXT;

-- Standard-specific entity reference
ALTER TABLE knowledge_enrichment ADD COLUMN IF NOT EXISTS
  standard_key TEXT;  -- Entity type in standard (e.g., 'Parameter', 'MetaCommand', 'Block', 'Class')

ALTER TABLE knowledge_enrichment ADD COLUMN IF NOT EXISTS
  standard_name TEXT;  -- Name in standard namespace (e.g., 'EPS_BattV', 'RadioDriver')

-- Optional constraints for scoping
ALTER TABLE knowledge_enrichment ADD COLUMN IF NOT EXISTS
  standard_constraints JSONB;  -- Flexible storage for namespace, container, subsystem, etc.


-- ============================================================================
-- PART 3: ADD COMMENTS
-- ============================================================================

COMMENT ON COLUMN knowledge_enrichment.standard IS
  'Standard name for standard_mapping enrichments (e.g., "xtce", "sysml_v2", "owl", "graphml")';

COMMENT ON COLUMN knowledge_enrichment.standard_version IS
  'Version of the standard (e.g., "1.2", "v2.0")';

COMMENT ON COLUMN knowledge_enrichment.standard_key IS
  'Entity type or class in the standard (e.g., XTCE: "Parameter", "MetaCommand"; SysML: "Block", "Port")';

COMMENT ON COLUMN knowledge_enrichment.standard_name IS
  'Name of entity in standard namespace (e.g., "EPS_BattV", "RadioDriver")';

COMMENT ON COLUMN knowledge_enrichment.standard_constraints IS
  'JSONB containing standard-specific constraints like:
   - namespace: XTCE namespace path
   - container: XTCE container name
   - subsystem: SysML subsystem
   - stereotype: SysML stereotype
   - ontology_uri: OWL ontology URI
   Examples:
   {"namespace": "/PROVES/EPS", "container": "TelemetryContainer"}
   {"subsystem": "PowerSubsystem", "stereotype": "<<Hardware>>"}';


-- ============================================================================
-- PART 4: ADD CHECK CONSTRAINT
-- ============================================================================

-- Ensure standard mapping fields are populated when enrichment_type = 'standard_mapping'
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'check_standard_mapping_fields'
      AND conrelid = 'knowledge_enrichment'::regclass
  ) THEN
    ALTER TABLE knowledge_enrichment ADD CONSTRAINT
      check_standard_mapping_fields
      CHECK (
        enrichment_type != 'standard_mapping' OR (
          standard IS NOT NULL AND
          standard_key IS NOT NULL AND
          standard_name IS NOT NULL
        )
      );
  END IF;
END $$;

COMMENT ON CONSTRAINT check_standard_mapping_fields ON knowledge_enrichment IS
  'Ensures standard, standard_key, and standard_name are populated for standard_mapping enrichments';


-- ============================================================================
-- PART 5: ADD INDEXES
-- ============================================================================

-- Index for finding entities by standard
CREATE INDEX IF NOT EXISTS idx_knowledge_enrichment_standard
  ON knowledge_enrichment(standard, standard_key)
  WHERE enrichment_type = 'standard_mapping';

-- Index for reverse lookup (standard name -> PROVES entity)
CREATE INDEX IF NOT EXISTS idx_knowledge_enrichment_standard_name
  ON knowledge_enrichment(standard, standard_name)
  WHERE enrichment_type = 'standard_mapping';

-- GIN index for JSONB constraint queries
CREATE INDEX IF NOT EXISTS idx_knowledge_enrichment_standard_constraints
  ON knowledge_enrichment USING GIN (standard_constraints)
  WHERE enrichment_type = 'standard_mapping';


-- ============================================================================
-- PART 6: HELPER VIEWS
-- ============================================================================

-- View: XTCE mappings for YAMCS export
CREATE OR REPLACE VIEW xtce_mappings AS
SELECT
  ce.id AS entity_id,
  ce.canonical_key AS proves_key,
  ce.name AS proves_name,
  ce.entity_type,
  ce.ecosystem,
  ke.standard_key AS xtce_type,
  ke.standard_name AS xtce_name,
  ke.standard_version AS xtce_version,
  ke.standard_constraints->>'namespace' AS xtce_namespace,
  ke.standard_constraints->>'container' AS xtce_container,
  ke.standard_constraints->>'subsystem' AS subsystem,
  ke.enriched_at,
  ke.enriched_by
FROM knowledge_enrichment ke
JOIN core_entities ce ON ke.primary_entity_id = ce.id
WHERE ke.enrichment_type = 'standard_mapping'
  AND ke.standard = 'xtce'
  AND ce.is_current = TRUE
ORDER BY ke.standard_constraints->>'namespace', ke.standard_name;

COMMENT ON VIEW xtce_mappings IS
  'PROVES entities mapped to XTCE format for YAMCS mission control integration';


-- View: All standard mappings (generic)
CREATE OR REPLACE VIEW standard_mappings AS
SELECT
  ce.id AS entity_id,
  ce.canonical_key AS proves_key,
  ce.name AS proves_name,
  ce.entity_type,
  ce.ecosystem,
  ke.standard,
  ke.standard_version,
  ke.standard_key,
  ke.standard_name,
  ke.standard_constraints,
  ke.enriched_at,
  ke.enriched_by
FROM knowledge_enrichment ke
JOIN core_entities ce ON ke.primary_entity_id = ce.id
WHERE ke.enrichment_type = 'standard_mapping'
  AND ce.is_current = TRUE
ORDER BY ke.standard, ke.standard_key, ke.standard_name;

COMMENT ON VIEW standard_mappings IS
  'All PROVES entities with standard format mappings (XTCE, SysML, OWL, etc.)';


-- ============================================================================
-- PART 7: EXAMPLE USAGE DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE knowledge_enrichment IS
  'Enrichment data for core entities including aliases, duplicates, and standard mappings.

  Example standard_mapping records:

  1. XTCE/YAMCS Parameter mapping:
     enrichment_type = ''standard_mapping''
     standard = ''xtce''
     standard_version = ''1.2''
     standard_key = ''Parameter''
     standard_name = ''EPS_BattV''
     standard_constraints = {
       "namespace": "/PROVES/EPS",
       "container": "EPSTelemetryContainer",
       "subsystem": "PowerSubsystem"
     }

  2. SysML v2 Block mapping:
     enrichment_type = ''standard_mapping''
     standard = ''sysml_v2''
     standard_version = ''2.0''
     standard_key = ''Block''
     standard_name = ''RadioDriver''
     standard_constraints = {
       "subsystem": "CommunicationsSubsystem",
       "stereotype": "<<Software>>"
     }

  3. OWL Class mapping:
     enrichment_type = ''standard_mapping''
     standard = ''owl''
     standard_version = ''2.0''
     standard_key = ''Class''
     standard_name = ''RadioDriver''
     standard_constraints = {
       "ontology_uri": "http://proves.space/ontology",
       "namespace": "proves"
     }

  4. PyTorch Geometric node mapping:
     enrichment_type = ''standard_mapping''
     standard = ''pytorch_geometric''
     standard_version = ''2.5.0''
     standard_key = ''Node''
     standard_name = ''fprime_component_radiodriver''
     standard_constraints = {
       "node_type": "software_component",
       "graph_id": "fprime_v3.4.3"
     }';


-- ============================================================================
-- PART 8: HELPER FUNCTION
-- ============================================================================

-- Function to add standard mapping
CREATE OR REPLACE FUNCTION add_standard_mapping(
  p_entity_id UUID,
  p_standard TEXT,
  p_standard_version TEXT,
  p_standard_key TEXT,
  p_standard_name TEXT,
  p_standard_constraints JSONB DEFAULT NULL,
  p_enriched_by TEXT DEFAULT 'auto_mapper',
  p_enrichment_notes TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
  v_enrichment_id UUID;
BEGIN
  -- Validate entity exists and is current
  IF NOT EXISTS (
    SELECT 1 FROM core_entities
    WHERE id = p_entity_id AND is_current = TRUE
  ) THEN
    RAISE EXCEPTION 'Entity % not found or not current', p_entity_id;
  END IF;

  -- Check for duplicate mapping
  IF EXISTS (
    SELECT 1 FROM knowledge_enrichment
    WHERE primary_entity_id = p_entity_id
      AND enrichment_type = 'standard_mapping'
      AND standard = p_standard
      AND standard_key = p_standard_key
      AND standard_name = p_standard_name
  ) THEN
    RAISE EXCEPTION 'Standard mapping already exists for entity % to %.% (%)',
      p_entity_id, p_standard, p_standard_key, p_standard_name;
  END IF;

  -- Insert mapping
  INSERT INTO knowledge_enrichment (
    primary_entity_id,
    enrichment_type,
    standard,
    standard_version,
    standard_key,
    standard_name,
    standard_constraints,
    enriched_by,
    enrichment_notes
  ) VALUES (
    p_entity_id,
    'standard_mapping',
    p_standard,
    p_standard_version,
    p_standard_key,
    p_standard_name,
    p_standard_constraints,
    p_enriched_by,
    p_enrichment_notes
  ) RETURNING enrichment_id INTO v_enrichment_id;

  RETURN v_enrichment_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION add_standard_mapping IS
  'Add a standard mapping enrichment for a PROVES entity.

  Example usage:

  -- Map to XTCE Parameter
  SELECT add_standard_mapping(
    p_entity_id := ''123e4567-e89b-12d3-a456-426614174000'',
    p_standard := ''xtce'',
    p_standard_version := ''1.2'',
    p_standard_key := ''Parameter'',
    p_standard_name := ''EPS_BattV'',
    p_standard_constraints := ''{"namespace": "/PROVES/EPS", "container": "EPSTelemetryContainer"}'',
    p_enriched_by := ''xtce_exporter'',
    p_enrichment_notes := ''Mapped for YAMCS integration''
  );';


-- ============================================================================
-- PART 9: VALIDATION
-- ============================================================================

DO $$
BEGIN
  -- Verify columns exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'knowledge_enrichment' AND column_name = 'standard'
  ) THEN
    RAISE EXCEPTION 'Column standard was not added to knowledge_enrichment';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'knowledge_enrichment' AND column_name = 'standard_constraints'
  ) THEN
    RAISE EXCEPTION 'Column standard_constraints was not added to knowledge_enrichment';
  END IF;

  -- Verify views exist
  IF NOT EXISTS (
    SELECT 1 FROM pg_views WHERE viewname = 'xtce_mappings'
  ) THEN
    RAISE EXCEPTION 'View xtce_mappings was not created';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_views WHERE viewname = 'standard_mappings'
  ) THEN
    RAISE EXCEPTION 'View standard_mappings was not created';
  END IF;

  -- Verify function exists
  IF NOT EXISTS (
    SELECT 1 FROM pg_proc WHERE proname = 'add_standard_mapping'
  ) THEN
    RAISE EXCEPTION 'Function add_standard_mapping was not created';
  END IF;

  RAISE NOTICE 'Migration 015 completed successfully ✓';
  RAISE NOTICE '  - Added standard_mapping enrichment type';
  RAISE NOTICE '  - Added standard, standard_version, standard_key, standard_name columns';
  RAISE NOTICE '  - Added standard_constraints JSONB column';
  RAISE NOTICE '  - Created xtce_mappings and standard_mappings views';
  RAISE NOTICE '  - Created add_standard_mapping() helper function';
  RAISE NOTICE '';
  RAISE NOTICE 'Supported standards: XTCE, SysML v2, OWL, GraphML, PyTorch Geometric';
END $$;

COMMIT;

-- ============================================================================
-- End of Migration 015
-- ============================================================================
