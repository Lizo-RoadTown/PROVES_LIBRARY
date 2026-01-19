-- Migration 037: Add epistemic metadata to review_queue_view
-- The 7 Knowledge Capture questions are stored in knowledge_epistemics sidecar
-- but were not included in the review view. This migration adds them.

BEGIN;

-- =============================================================================
-- RECREATE review_queue_view WITH EPISTEMIC DATA
-- =============================================================================

DROP VIEW IF EXISTS review_queue_view CASCADE;

CREATE OR REPLACE VIEW review_queue_view AS
SELECT
    -- Identity
    e.extraction_id,
    e.candidate_type,
    e.candidate_key,
    e.ecosystem,
    e.status,
    e.created_at,

    -- Organization (for tenant filtering)
    e.source_organization_id,

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

    -- =============================================================================
    -- NEW: Epistemic metadata from knowledge_epistemics sidecar (7 Questions)
    -- =============================================================================
    jsonb_build_object(
        -- Q1: Who knew this, and how close were they?
        'observer', jsonb_build_object(
            'id', ke.observer_id,
            'type', ke.observer_type,
            'contact_mode', ke.contact_mode,
            'contact_strength', ke.contact_strength
        ),
        -- Q2: Where does the experience live?
        'pattern', jsonb_build_object(
            'storage', ke.pattern_storage,
            'representation_media', ke.representation_media,
            'signal_type', ke.signal_type
        ),
        -- Q3: What must stay connected?
        'dependencies', jsonb_build_object(
            'entities', ke.dependencies,
            'sequence_role', ke.sequence_role
        ),
        -- Q4: Under what conditions was this true?
        'conditions', jsonb_build_object(
            'validity_conditions', ke.validity_conditions,
            'assumptions', ke.assumptions,
            'scope', ke.scope
        ),
        -- Q5: When does this expire?
        'temporal', jsonb_build_object(
            'observed_at', ke.observed_at,
            'valid_from', ke.valid_from,
            'valid_to', ke.valid_to,
            'refresh_trigger', ke.refresh_trigger,
            'staleness_risk', ke.staleness_risk
        ),
        -- Q6: Who wrote this, and why?
        'authorship', jsonb_build_object(
            'author_id', ke.author_id,
            'intent', ke.intent,
            'uncertainty_notes', ke.uncertainty_notes
        ),
        -- Q7: Does this only work if someone keeps doing it?
        'transferability', jsonb_build_object(
            'reenactment_required', ke.reenactment_required,
            'practice_interval', ke.practice_interval,
            'skill_transferability', ke.skill_transferability
        ),
        -- Domain context
        'domain', ke.domain
    ) as epistemics,

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
LEFT JOIN validation_decisions d ON e.latest_decision_id = d.decision_id
LEFT JOIN knowledge_epistemics ke ON e.extraction_id = ke.extraction_id;

COMMENT ON VIEW review_queue_view IS
'Review queue with full epistemic metadata from 7 Knowledge Capture questions.';

-- =============================================================================
-- GRANTS (must re-grant after recreating view)
-- =============================================================================

GRANT SELECT ON review_queue_view TO authenticated;
GRANT SELECT ON review_queue_view TO service_role;
GRANT SELECT ON review_queue_view TO anon;

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
DECLARE
    v_count INTEGER;
BEGIN
    -- Verify view was created
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.views
        WHERE table_name = 'review_queue_view'
    ) THEN
        RAISE EXCEPTION 'review_queue_view was not created';
    END IF;

    -- Verify epistemics column exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'review_queue_view' AND column_name = 'epistemics'
    ) THEN
        RAISE EXCEPTION 'epistemics column missing from view';
    END IF;

    -- Count extractions with epistemic data
    SELECT COUNT(*) INTO v_count
    FROM review_queue_view
    WHERE epistemics->'observer'->>'id' IS NOT NULL;

    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration 037: Epistemics in Review View';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Added to review_queue_view:';
    RAISE NOTICE '  - epistemics.observer (Q1: Who knew this?)';
    RAISE NOTICE '  - epistemics.pattern (Q2: Where does experience live?)';
    RAISE NOTICE '  - epistemics.dependencies (Q3: What must stay connected?)';
    RAISE NOTICE '  - epistemics.conditions (Q4: Under what conditions?)';
    RAISE NOTICE '  - epistemics.temporal (Q5: When does this expire?)';
    RAISE NOTICE '  - epistemics.authorship (Q6: Who wrote this?)';
    RAISE NOTICE '  - epistemics.transferability (Q7: Reenactment required?)';
    RAISE NOTICE '';
    RAISE NOTICE 'Extractions with epistemic data: %', v_count;
END $$;

COMMIT;
