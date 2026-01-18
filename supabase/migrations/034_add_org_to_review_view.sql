-- Migration 034: Add Organization ID to Review Queue View
--
-- Fixes tenant isolation by adding source_organization_id to review_queue_view
-- so that Admin UI can filter extractions by the user's organization.
--
-- Key changes:
-- 1. Recreate review_queue_view with source_organization_id column
-- 2. Add organization name and color for display
-- 3. Create org-scoped version of the view for RLS enforcement

BEGIN;

-- =============================================================================
-- PART 1: RECREATE REVIEW_QUEUE_VIEW WITH ORGANIZATION DATA
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

    -- ORGANIZATION CONTEXT (NEW)
    e.source_organization_id,
    o.name as organization_name,
    o.slug as organization_slug,
    o.primary_color as organization_color,

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
LEFT JOIN validation_decisions d ON e.latest_decision_id = d.decision_id
LEFT JOIN organizations o ON e.source_organization_id = o.id;

COMMENT ON VIEW review_queue_view IS
'Review queue with organization context. Filter by source_organization_id for tenant isolation.';

-- =============================================================================
-- PART 2: GRANTS
-- =============================================================================

-- Restore grants after recreating view
GRANT SELECT ON review_queue_view TO authenticated;
GRANT SELECT ON review_queue_view TO service_role;
GRANT SELECT ON review_queue_view TO anon;

-- =============================================================================
-- PART 3: CREATE ORG-SCOPED HELPER FUNCTION
-- =============================================================================

-- Function to get review queue for a specific organization
-- This enforces tenant isolation by checking membership
CREATE OR REPLACE FUNCTION get_org_review_queue_v2(
    p_organization_id UUID,
    p_status TEXT DEFAULT 'pending',
    p_limit INT DEFAULT 100,
    p_offset INT DEFAULT 0
)
RETURNS SETOF review_queue_view
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Verify user has access to this organization
    IF NOT EXISTS (
        SELECT 1 FROM organization_members
        WHERE organization_id = p_organization_id
        AND user_id = auth.uid()
        AND role IN ('admin', 'lead', 'engineer', 'researcher')
    ) THEN
        RAISE EXCEPTION 'Access denied: not a member of this organization';
    END IF;

    RETURN QUERY
    SELECT *
    FROM review_queue_view
    WHERE source_organization_id = p_organization_id
    AND status = p_status::candidate_status
    ORDER BY created_at DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;

GRANT EXECUTE ON FUNCTION get_org_review_queue_v2 TO authenticated;

COMMENT ON FUNCTION get_org_review_queue_v2 IS
'Get review queue filtered by organization with membership check. Use this in Admin UI.';

-- =============================================================================
-- PART 4: AGGREGATED STATS FOR MISSION CONTROL (ALL ORGS)
-- =============================================================================

-- Function to get aggregated stats across all organizations for Mission Control
-- This is the SHARED view - no org filtering, shows global activity
CREATE OR REPLACE FUNCTION get_all_orgs_activity()
RETURNS TABLE (
    org_id UUID,
    org_name TEXT,
    org_slug TEXT,
    org_color TEXT,
    pending_reviews BIGINT,
    approvals_today BIGINT,
    rejections_today BIGINT,
    last_promotion TIMESTAMPTZ,
    total_contributed BIGINT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT
        o.id,
        o.name,
        o.slug,
        o.primary_color,
        -- Pending reviews for this org
        COUNT(*) FILTER (WHERE se.status = 'pending') as pending_reviews,
        -- Approvals today
        COUNT(*) FILTER (
            WHERE se.status = 'accepted'
            AND se.reviewed_at >= CURRENT_DATE
        ) as approvals_today,
        -- Rejections today
        COUNT(*) FILTER (
            WHERE se.status = 'rejected'
            AND se.reviewed_at >= CURRENT_DATE
        ) as rejections_today,
        -- Last promotion time
        MAX(se.reviewed_at) FILTER (WHERE se.status = 'accepted') as last_promotion,
        -- Total entities contributed to shared library
        (SELECT COUNT(*) FROM core_entities ce WHERE ce.contributed_by_org_id = o.id) as total_contributed
    FROM organizations o
    LEFT JOIN staging_extractions se ON se.source_organization_id = o.id
    WHERE o.is_active = true
    GROUP BY o.id, o.name, o.slug, o.primary_color
    ORDER BY pending_reviews DESC, o.name;
END;
$$;

GRANT EXECUTE ON FUNCTION get_all_orgs_activity TO authenticated;
GRANT EXECUTE ON FUNCTION get_all_orgs_activity TO anon;

COMMENT ON FUNCTION get_all_orgs_activity IS
'Get activity stats for all organizations. Used by Mission Control Heat Map.';

-- =============================================================================
-- PART 5: PIPELINE STATS FOR MISSION CONTROL
-- =============================================================================

-- Function to get pipeline flow stats (sources → extract → validate → promote)
CREATE OR REPLACE FUNCTION get_pipeline_stats()
RETURNS TABLE (
    stage TEXT,
    count BIGINT,
    items_today BIGINT,
    items_this_hour BIGINT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY

    -- Sources (active team_sources)
    SELECT
        'sources'::TEXT,
        COUNT(*)::BIGINT,
        0::BIGINT,
        0::BIGINT
    FROM team_sources WHERE is_active = true

    UNION ALL

    -- Extraction (pending extractions)
    SELECT
        'extraction'::TEXT,
        COUNT(*) FILTER (WHERE status = 'pending')::BIGINT,
        COUNT(*) FILTER (WHERE status = 'pending' AND created_at >= CURRENT_DATE)::BIGINT,
        COUNT(*) FILTER (WHERE status = 'pending' AND created_at >= NOW() - INTERVAL '1 hour')::BIGINT
    FROM staging_extractions

    UNION ALL

    -- Validation (needs_context status)
    SELECT
        'validation'::TEXT,
        COUNT(*) FILTER (WHERE status = 'needs_context')::BIGINT,
        COUNT(*) FILTER (WHERE status = 'needs_context' AND created_at >= CURRENT_DATE)::BIGINT,
        COUNT(*) FILTER (WHERE status = 'needs_context' AND created_at >= NOW() - INTERVAL '1 hour')::BIGINT
    FROM staging_extractions

    UNION ALL

    -- Promotion (accepted, ready to promote)
    SELECT
        'promotion'::TEXT,
        COUNT(*) FILTER (WHERE status = 'accepted' AND sharing_status = 'pending_review')::BIGINT,
        COUNT(*) FILTER (WHERE status = 'accepted' AND reviewed_at >= CURRENT_DATE)::BIGINT,
        COUNT(*) FILTER (WHERE status = 'accepted' AND reviewed_at >= NOW() - INTERVAL '1 hour')::BIGINT
    FROM staging_extractions

    UNION ALL

    -- Library (core_entities - verified knowledge)
    SELECT
        'library'::TEXT,
        COUNT(*)::BIGINT,
        COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE)::BIGINT,
        COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 hour')::BIGINT
    FROM core_entities;
END;
$$;

GRANT EXECUTE ON FUNCTION get_pipeline_stats TO authenticated;
GRANT EXECUTE ON FUNCTION get_pipeline_stats TO anon;

COMMENT ON FUNCTION get_pipeline_stats IS
'Get pipeline flow statistics for Mission Control visualization.';

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
BEGIN
    -- Verify view has org columns
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'review_queue_view'
        AND column_name = 'source_organization_id'
    ) THEN
        RAISE EXCEPTION 'source_organization_id column not in review_queue_view';
    END IF;

    -- Verify functions exist
    IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'get_org_review_queue_v2') THEN
        RAISE EXCEPTION 'get_org_review_queue_v2 function not created';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'get_all_orgs_activity') THEN
        RAISE EXCEPTION 'get_all_orgs_activity function not created';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'get_pipeline_stats') THEN
        RAISE EXCEPTION 'get_pipeline_stats function not created';
    END IF;

    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration 034: Org Context in Review Queue';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Changes:';
    RAISE NOTICE '  - review_queue_view now includes source_organization_id';
    RAISE NOTICE '  - Added organization_name, organization_slug, organization_color';
    RAISE NOTICE '  - Created get_org_review_queue_v2() with membership check';
    RAISE NOTICE '  - Created get_all_orgs_activity() for Mission Control Heat Map';
    RAISE NOTICE '  - Created get_pipeline_stats() for Pipeline Flow visualization';
    RAISE NOTICE '';
    RAISE NOTICE 'Usage in Admin UI:';
    RAISE NOTICE '  - Filter review_queue_view by source_organization_id';
    RAISE NOTICE '  - OR use get_org_review_queue_v2(org_id) RPC';
    RAISE NOTICE '';
    RAISE NOTICE 'Usage in Mission Control:';
    RAISE NOTICE '  - Call get_all_orgs_activity() for Heat Map';
    RAISE NOTICE '  - Call get_pipeline_stats() for Pipeline Flow';
END $$;

COMMIT;
