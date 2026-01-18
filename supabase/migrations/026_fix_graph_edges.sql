-- Migration 026: Fix Graph Edges Function
--
-- Corrects get_graph_edges() to use actual core_equivalences column names:
--   - entity_a_id / entity_b_id (not source_entity_id / target_entity_id)
--   - confidence (not confidence_score)
--   - No equivalence_type column exists, use 'equivalent' as default
--   - No discovered_by_org_id, join through entities

BEGIN;

-- Drop and recreate with correct column names
CREATE OR REPLACE FUNCTION get_graph_edges(
    p_organization_id UUID DEFAULT NULL,
    p_verified_only BOOLEAN DEFAULT true,
    p_limit INT DEFAULT 1000
)
RETURNS TABLE (
    id UUID,
    source UUID,
    target UUID,
    relation TEXT,
    organization_id UUID,
    organization_name TEXT,
    status TEXT,
    confidence FLOAT
) AS $$
BEGIN
    IF p_verified_only THEN
        -- Edges from core_equivalences (verified relationships)
        RETURN QUERY
        SELECT
            eq.id,
            eq.entity_a_id AS source,
            eq.entity_b_id AS target,
            'equivalent'::TEXT AS relation,  -- No type column, default to 'equivalent'
            ce_a.contributed_by_org_id AS organization_id,
            COALESCE(o.name, 'Community') AS organization_name,
            'verified'::TEXT AS status,
            eq.confidence::FLOAT AS confidence
        FROM core_equivalences eq
        JOIN core_entities ce_a ON ce_a.id = eq.entity_a_id
        LEFT JOIN organizations o ON o.id = ce_a.contributed_by_org_id
        WHERE (p_organization_id IS NULL OR ce_a.contributed_by_org_id = p_organization_id)
        ORDER BY eq.created_at DESC
        LIMIT p_limit;
    ELSE
        -- Include edges inferred from extractions (connection/dependency types)
        RETURN QUERY
        (
            -- Verified equivalences
            SELECT
                eq.id,
                eq.entity_a_id AS source,
                eq.entity_b_id AS target,
                'equivalent'::TEXT AS relation,
                ce_a.contributed_by_org_id AS organization_id,
                COALESCE(o.name, 'Community') AS organization_name,
                'verified'::TEXT AS status,
                eq.confidence::FLOAT AS confidence
            FROM core_equivalences eq
            JOIN core_entities ce_a ON ce_a.id = eq.entity_a_id
            LEFT JOIN organizations o ON o.id = ce_a.contributed_by_org_id
            WHERE (p_organization_id IS NULL OR ce_a.contributed_by_org_id = p_organization_id)
        )
        UNION ALL
        (
            -- Pending coupling extractions from staging
            SELECT
                se.extraction_id AS id,
                -- Try to resolve source/target from candidate_payload
                COALESCE(
                    (se.candidate_payload->>'source_entity_id')::UUID,
                    (SELECT ce.id FROM core_entities ce
                     WHERE ce.canonical_key = (se.candidate_payload->>'source_key')
                     LIMIT 1)
                ) AS source,
                COALESCE(
                    (se.candidate_payload->>'target_entity_id')::UUID,
                    (SELECT ce.id FROM core_entities ce
                     WHERE ce.canonical_key = (se.candidate_payload->>'target_key')
                     LIMIT 1)
                ) AS target,
                COALESCE((se.candidate_payload->>'relationship')::TEXT, se.candidate_type::TEXT) AS relation,
                se.source_organization_id AS organization_id,
                COALESCE(o.name, 'Unknown') AS organization_name,
                'pending'::TEXT AS status,
                se.confidence_score AS confidence
            FROM staging_extractions se
            LEFT JOIN organizations o ON o.id = se.source_organization_id
            WHERE se.status = 'pending'
            AND se.candidate_type::TEXT IN ('connection', 'dependency', 'inheritance', 'coupling')
            AND (p_organization_id IS NULL OR se.source_organization_id = p_organization_id)
        )
        ORDER BY confidence DESC
        LIMIT p_limit;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '=========================================';
    RAISE NOTICE 'Migration 026: Fix Graph Edges Function';
    RAISE NOTICE '=========================================';
    RAISE NOTICE '  - get_graph_edges() updated with correct column names';
    RAISE NOTICE '  - Uses entity_a_id/entity_b_id from core_equivalences';
    RAISE NOTICE '  - Joins through core_entities for organization';
END $$;

COMMIT;
