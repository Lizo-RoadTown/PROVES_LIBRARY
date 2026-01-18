-- Migration 019: Enhanced Human Review System
-- Structured rejection taxonomy, validation edits table, and review constraints
-- Supports the feedback loop: human decisions -> analyzer -> prompt improvements

BEGIN;

-- =============================================================================
-- PART 1: REJECTION CATEGORY ENUM
-- Structured taxonomy for rejection reasons (replaces free-text tokenization)
-- =============================================================================

-- Check if enum already exists before creating
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'rejection_category') THEN
        CREATE TYPE rejection_category AS ENUM (
            -- Evidence issues
            'evidence_insufficient',    -- Not enough supporting evidence
            'evidence_misquoted',       -- Quote doesn't match source
            'evidence_outdated',        -- Source is outdated/superseded
            'evidence_irrelevant',      -- Evidence doesn't support extraction

            -- Extraction accuracy
            'wrong_entity_type',        -- Should be different entity type
            'duplicate_entity',         -- Already exists in library
            'partial_extraction',       -- Missing key information
            'hallucinated',             -- Entity doesn't exist in source

            -- Classification issues
            'wrong_ecosystem',          -- Wrong ecosystem/domain assignment
            'wrong_frames',             -- FRAMES metadata incorrect
            'confidence_too_high',      -- AI confidence doesn't match quality

            -- Source issues
            'source_unreliable',        -- Source not authoritative
            'source_inaccessible',      -- Cannot verify source

            -- Other
            'other'                     -- Other reason (see notes)
        );
    END IF;
END $$;

COMMENT ON TYPE rejection_category IS
'Structured taxonomy for rejection reasons. Families: evidence_*, extraction_*, classification_*, source_*, other';

-- =============================================================================
-- PART 2: ENHANCE validation_decisions TABLE
-- Add rejection category, confidence override, source flagging
-- =============================================================================

-- Add rejection category column
ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
    rejection_category rejection_category;

-- Add human confidence override (when reviewer disagrees with AI confidence)
ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
    human_confidence_override NUMERIC(3,2)
    CHECK (human_confidence_override IS NULL OR (human_confidence_override >= 0 AND human_confidence_override <= 1));

ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
    confidence_override_reason TEXT;

-- Add source flagging (when reviewer questions the source itself)
ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
    source_flagged BOOLEAN DEFAULT FALSE;

ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
    source_flag_reason TEXT;

-- Comments for documentation
COMMENT ON COLUMN validation_decisions.rejection_category IS
'Structured rejection reason from taxonomy. Required when decision = reject.';

COMMENT ON COLUMN validation_decisions.human_confidence_override IS
'Reviewer''s confidence assessment (0.0-1.0) when they disagree with AI. NULL means agreement.';

COMMENT ON COLUMN validation_decisions.confidence_override_reason IS
'Why the reviewer disagreed with AI confidence. Required when override is set.';

COMMENT ON COLUMN validation_decisions.source_flagged IS
'TRUE if reviewer flagged the source as questionable/unreliable.';

COMMENT ON COLUMN validation_decisions.source_flag_reason IS
'Why the source was flagged. Required when source_flagged = TRUE.';

-- =============================================================================
-- PART 3: DATA INTEGRITY CONSTRAINTS
-- Prevent partial writes from the UI
-- =============================================================================

-- BACKFILL existing rejections with 'other' category before adding constraint
-- This ensures existing data doesn't violate the new constraint
UPDATE validation_decisions
SET rejection_category = 'other'
WHERE decision = 'reject' AND rejection_category IS NULL;

-- If rejected, require a category (drop first if exists to allow recreation)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'reject_requires_category'
    ) THEN
        ALTER TABLE validation_decisions DROP CONSTRAINT reject_requires_category;
    END IF;
END $$;

ALTER TABLE validation_decisions
    ADD CONSTRAINT reject_requires_category
    CHECK (decision != 'reject' OR rejection_category IS NOT NULL);

-- If confidence override provided, require reason
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'override_requires_reason'
    ) THEN
        ALTER TABLE validation_decisions DROP CONSTRAINT override_requires_reason;
    END IF;
END $$;

ALTER TABLE validation_decisions
    ADD CONSTRAINT override_requires_reason
    CHECK (human_confidence_override IS NULL OR confidence_override_reason IS NOT NULL);

-- If source flagged, require reason
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'source_flag_requires_reason'
    ) THEN
        ALTER TABLE validation_decisions DROP CONSTRAINT source_flag_requires_reason;
    END IF;
END $$;

ALTER TABLE validation_decisions
    ADD CONSTRAINT source_flag_requires_reason
    CHECK (source_flagged = FALSE OR source_flag_reason IS NOT NULL);

-- =============================================================================
-- PART 4: VALIDATION_EDITS TABLE
-- Separate change log for "Modify" operations (not in validation_decisions)
-- =============================================================================

CREATE TABLE IF NOT EXISTS validation_edits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to extraction
    extraction_id UUID NOT NULL REFERENCES staging_extractions(extraction_id) ON DELETE CASCADE,

    -- Who made the edit
    reviewer_id TEXT NOT NULL,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- The actual change (JSONB for full payload diff)
    before_payload JSONB NOT NULL,
    after_payload JSONB NOT NULL,

    -- Optional context
    edit_reason TEXT,

    -- Quick filtering: which fields were changed
    fields_changed TEXT[] DEFAULT '{}'
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_validation_edits_extraction_id
    ON validation_edits(extraction_id);

CREATE INDEX IF NOT EXISTS idx_validation_edits_reviewer
    ON validation_edits(reviewer_id);

CREATE INDEX IF NOT EXISTS idx_validation_edits_created
    ON validation_edits(created_at DESC);

-- Comments
COMMENT ON TABLE validation_edits IS
'Audit log of payload edits made during human review. Separate from validation_decisions.';

COMMENT ON COLUMN validation_edits.before_payload IS
'Complete candidate_payload before this edit.';

COMMENT ON COLUMN validation_edits.after_payload IS
'Complete candidate_payload after this edit.';

COMMENT ON COLUMN validation_edits.fields_changed IS
'Array of field names that changed, for quick filtering.';

-- =============================================================================
-- PART 5: INDEXES FOR ANALYZER QUERIES
-- Support efficient pattern analysis by rejection category
-- =============================================================================

-- Index for rejection category analysis
CREATE INDEX IF NOT EXISTS idx_validation_decisions_rejection_category
    ON validation_decisions(rejection_category)
    WHERE decision = 'reject';

-- Index for confidence override analysis (approved-but-overridden)
CREATE INDEX IF NOT EXISTS idx_validation_decisions_confidence_override
    ON validation_decisions(human_confidence_override)
    WHERE human_confidence_override IS NOT NULL;

-- Index for source flag analysis
CREATE INDEX IF NOT EXISTS idx_validation_decisions_source_flagged
    ON validation_decisions(source_flagged)
    WHERE source_flagged = TRUE;

-- =============================================================================
-- PART 6: RPC FUNCTION - record_review_decision
-- Clean function for recording decisions (separate from edits)
-- =============================================================================

CREATE OR REPLACE FUNCTION record_review_decision(
    p_extraction_id UUID,
    p_decision TEXT,                                    -- 'accept', 'reject', 'merge', 'defer', 'needs_more_evidence'
    p_reviewer_id TEXT,
    p_rejection_category rejection_category DEFAULT NULL,
    p_decision_reason TEXT DEFAULT NULL,
    p_human_confidence_override NUMERIC DEFAULT NULL,
    p_confidence_override_reason TEXT DEFAULT NULL,
    p_source_flagged BOOLEAN DEFAULT FALSE,
    p_source_flag_reason TEXT DEFAULT NULL
) RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_decision_id UUID;
BEGIN
    -- Validate: reject requires category
    IF p_decision = 'reject' AND p_rejection_category IS NULL THEN
        RAISE EXCEPTION 'Rejection requires a category';
    END IF;

    -- Validate: confidence override requires reason
    IF p_human_confidence_override IS NOT NULL AND p_confidence_override_reason IS NULL THEN
        RAISE EXCEPTION 'Confidence override requires a reason';
    END IF;

    -- Validate: source flag requires reason
    IF p_source_flagged = TRUE AND p_source_flag_reason IS NULL THEN
        RAISE EXCEPTION 'Source flag requires a reason';
    END IF;

    -- Insert the decision
    INSERT INTO validation_decisions (
        extraction_id,
        decision,
        decided_by,
        decider_type,
        decision_reason,
        rejection_category,
        human_confidence_override,
        confidence_override_reason,
        source_flagged,
        source_flag_reason,
        decided_at
    ) VALUES (
        p_extraction_id,
        p_decision::validation_decision_type,
        p_reviewer_id,
        'human',
        p_decision_reason,
        p_rejection_category,
        p_human_confidence_override,
        p_confidence_override_reason,
        p_source_flagged,
        p_source_flag_reason,
        NOW()
    )
    RETURNING decision_id INTO v_decision_id;

    -- Update staging_extractions with latest decision
    UPDATE staging_extractions
    SET
        latest_decision_id = v_decision_id,
        status = CASE
            WHEN p_decision = 'accept' THEN 'accepted'
            WHEN p_decision = 'reject' THEN 'rejected'
            WHEN p_decision = 'merge' THEN 'merged'
            WHEN p_decision = 'needs_more_evidence' THEN 'needs_context'
            ELSE status
        END::candidate_status,
        review_decision = p_decision,
        reviewed_by = p_reviewer_id,
        reviewed_at = NOW(),
        updated_at = NOW()
    WHERE extraction_id = p_extraction_id;

    RETURN v_decision_id;
END;
$$;

COMMENT ON FUNCTION record_review_decision IS
'Record a human review decision with structured rejection category and optional overrides.';

-- =============================================================================
-- PART 7: RPC FUNCTION - record_review_edit
-- Separate function for payload modifications
-- =============================================================================

CREATE OR REPLACE FUNCTION record_review_edit(
    p_extraction_id UUID,
    p_reviewer_id TEXT,
    p_before_payload JSONB,
    p_after_payload JSONB,
    p_edit_reason TEXT DEFAULT NULL,
    p_apply_to_extraction BOOLEAN DEFAULT TRUE
) RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_edit_id UUID;
    v_fields_changed TEXT[];
    v_key TEXT;
BEGIN
    -- Compute which fields changed
    v_fields_changed := ARRAY[]::TEXT[];

    FOR v_key IN SELECT jsonb_object_keys(p_after_payload)
    LOOP
        IF p_before_payload->v_key IS DISTINCT FROM p_after_payload->v_key THEN
            v_fields_changed := array_append(v_fields_changed, v_key);
        END IF;
    END LOOP;

    -- Also check for removed keys
    FOR v_key IN SELECT jsonb_object_keys(p_before_payload)
    LOOP
        IF NOT p_after_payload ? v_key THEN
            v_fields_changed := array_append(v_fields_changed, v_key);
        END IF;
    END LOOP;

    -- Insert the edit record
    INSERT INTO validation_edits (
        extraction_id,
        reviewer_id,
        before_payload,
        after_payload,
        edit_reason,
        fields_changed,
        created_at
    ) VALUES (
        p_extraction_id,
        p_reviewer_id,
        p_before_payload,
        p_after_payload,
        p_edit_reason,
        v_fields_changed,
        NOW()
    )
    RETURNING id INTO v_edit_id;

    -- Optionally apply the edit to the extraction
    IF p_apply_to_extraction THEN
        UPDATE staging_extractions
        SET
            candidate_payload = p_after_payload,
            updated_at = NOW()
        WHERE extraction_id = p_extraction_id;
    END IF;

    RETURN v_edit_id;
END;
$$;

COMMENT ON FUNCTION record_review_edit IS
'Record a payload edit during review. Separate from decision. Can optionally apply to extraction.';

-- =============================================================================
-- PART 8: REVIEW QUEUE VIEW
-- Single query returning ReviewExtractionDTO shape for frontend
-- =============================================================================

CREATE OR REPLACE VIEW review_queue_view AS
SELECT
    -- Identity
    e.extraction_id,
    e.candidate_type,
    e.candidate_key,
    e.ecosystem,
    e.status,
    e.created_at,

    -- Payload (editable)
    e.candidate_payload,

    -- Evidence (structured for reviewer)
    jsonb_build_object(
        'raw_text', COALESCE(e.evidence->>'raw_text', e.evidence->>'raw_evidence', ''),
        'byte_offset', e.evidence_byte_offset,
        'byte_length', e.evidence_byte_length,
        'checksum', e.evidence_checksum,
        'rationale_summary', jsonb_build_object(
            'signals_observed', COALESCE(e.evidence->'reasoning_trail'->'validation_patterns_checked', '[]'::jsonb),
            'comparisons_made', COALESCE(e.evidence->'reasoning_trail'->'verified_entities_consulted', '[]'::jsonb),
            'uncertainty_factors', COALESCE(e.evidence->'reasoning_trail'->'uncertainty_factors', '[]'::jsonb)
        ),
        'duplicate_check', COALESCE(e.evidence->'duplicate_check', jsonb_build_object(
            'exact_matches', '[]'::jsonb,
            'similar_entities', '[]'::jsonb,
            'recommendation', 'create_new'
        ))
    ) as evidence,

    -- Lineage verification
    jsonb_build_object(
        'verified', COALESCE(e.lineage_verified, FALSE),
        'confidence', COALESCE(e.lineage_confidence, 0),
        'verified_at', e.lineage_verified_at
    ) as lineage,

    -- Snapshot context
    jsonb_build_object(
        'snapshot_id', s.id,
        'source_url', s.source_url,
        'source_type', s.source_type,
        'context_excerpt', CASE
            WHEN s.payload->>'content' IS NOT NULL
            THEN substring(s.payload->>'content' from 1 for 2000)
            ELSE NULL
        END,
        'captured_at', s.captured_at
    ) as snapshot,

    -- Confidence
    jsonb_build_object(
        'score', COALESCE(e.confidence_score, 0),
        'reason', COALESCE(e.confidence_reason, '')
    ) as confidence,

    -- Latest decision (if any)
    CASE WHEN d.decision_id IS NOT NULL THEN
        jsonb_build_object(
            'decision_id', d.decision_id,
            'decision', d.decision,
            'decided_by', d.decided_by,
            'decided_at', d.decided_at,
            'rejection_category', d.rejection_category,
            'decision_reason', d.decision_reason,
            'human_confidence_override', d.human_confidence_override,
            'confidence_override_reason', d.confidence_override_reason,
            'source_flagged', d.source_flagged,
            'source_flag_reason', d.source_flag_reason
        )
    ELSE NULL END as latest_decision,

    -- Edit history count (for UI indication)
    (SELECT COUNT(*) FROM validation_edits ve WHERE ve.extraction_id = e.extraction_id) as edit_count

FROM staging_extractions e
LEFT JOIN raw_snapshots s ON e.snapshot_id = s.id
LEFT JOIN validation_decisions d ON e.latest_decision_id = d.decision_id;

COMMENT ON VIEW review_queue_view IS
'Single query view for human review UI. Returns ReviewExtractionDTO shape.';

-- =============================================================================
-- PART 9: GRANTS AND RLS
-- =============================================================================

-- Grant access to validation_edits
ALTER TABLE validation_edits ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view validation edits"
ON validation_edits FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Users can insert validation edits"
ON validation_edits FOR INSERT
TO authenticated
WITH CHECK (true);

CREATE POLICY "Service role full access to validation edits"
ON validation_edits FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Grant access to the view
GRANT SELECT ON review_queue_view TO authenticated;
GRANT SELECT ON review_queue_view TO service_role;

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION record_review_decision TO authenticated;
GRANT EXECUTE ON FUNCTION record_review_decision TO service_role;
GRANT EXECUTE ON FUNCTION record_review_edit TO authenticated;
GRANT EXECUTE ON FUNCTION record_review_edit TO service_role;

-- =============================================================================
-- PART 10: UPDATE ANALYZER VIEW (if exists)
-- Add rejection_category to rejection trend view
-- =============================================================================

-- Drop and recreate v_rejection_trend to include category
DROP VIEW IF EXISTS v_rejection_trend CASCADE;

CREATE OR REPLACE VIEW v_rejection_trend AS
SELECT
    se.ecosystem,
    se.candidate_type,
    DATE_TRUNC('week', se.created_at)::DATE as week,
    COUNT(*) FILTER (WHERE se.status = 'rejected') as rejection_count,
    COUNT(*) as total_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE se.status = 'rejected') / NULLIF(COUNT(*), 0),
        1
    ) as rejection_rate,
    -- Use structured rejection category instead of free text
    MODE() WITHIN GROUP (ORDER BY vd.rejection_category) FILTER (WHERE se.status = 'rejected') as top_rejection_category,
    -- Keep decision_reason for additional context
    MODE() WITHIN GROUP (ORDER BY vd.decision_reason) FILTER (WHERE se.status = 'rejected') as top_rejection_reason
FROM staging_extractions se
LEFT JOIN validation_decisions vd ON se.extraction_id = vd.extraction_id
    AND vd.decision = 'reject'
WHERE se.status IN ('accepted', 'rejected')
GROUP BY se.ecosystem, se.candidate_type, DATE_TRUNC('week', se.created_at)
HAVING COUNT(*) >= 3
ORDER BY week DESC, rejection_count DESC;

COMMENT ON VIEW v_rejection_trend IS
'Weekly rejection rates by ecosystem and entity type with structured rejection categories.';

GRANT SELECT ON v_rejection_trend TO authenticated;
GRANT SELECT ON v_rejection_trend TO service_role;

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
BEGIN
    -- Verify rejection_category type exists
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'rejection_category') THEN
        RAISE EXCEPTION 'rejection_category type was not created';
    END IF;

    -- Verify validation_edits table exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'validation_edits') THEN
        RAISE EXCEPTION 'validation_edits table was not created';
    END IF;

    -- Verify constraints exist
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'reject_requires_category') THEN
        RAISE EXCEPTION 'reject_requires_category constraint was not created';
    END IF;

    -- Verify functions exist
    IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'record_review_decision') THEN
        RAISE EXCEPTION 'record_review_decision function was not created';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'record_review_edit') THEN
        RAISE EXCEPTION 'record_review_edit function was not created';
    END IF;

    RAISE NOTICE 'Migration 019 verification passed:';
    RAISE NOTICE '  - rejection_category enum created';
    RAISE NOTICE '  - validation_edits table created';
    RAISE NOTICE '  - Data integrity constraints added';
    RAISE NOTICE '  - record_review_decision function created';
    RAISE NOTICE '  - record_review_edit function created';
    RAISE NOTICE '  - review_queue_view created';
    RAISE NOTICE '  - v_rejection_trend updated with categories';
END $$;

COMMIT;
