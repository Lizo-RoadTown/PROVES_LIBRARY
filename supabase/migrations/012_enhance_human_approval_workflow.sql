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
