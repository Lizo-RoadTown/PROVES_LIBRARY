-- Migration 028: Fix Graph Nodes Timestamp Type
--
-- Fixes type mismatch in get_graph_nodes() function
-- The updated_at column needs explicit cast to TIMESTAMPTZ

BEGIN;

-- Recreate with explicit timestamp cast
CREATE OR REPLACE FUNCTION get_graph_nodes(
    p_organization_id UUID DEFAULT NULL,
    p_domain TEXT DEFAULT NULL,
    p_category TEXT DEFAULT NULL,
    p_verified_only BOOLEAN DEFAULT true,
    p_limit INT DEFAULT 500
)
RETURNS TABLE (
    id UUID,
    type TEXT,
    label TEXT,
    domain TEXT,
    category TEXT,
    tags TEXT[],
    organization_id UUID,
    organization_name TEXT,
    organization_color TEXT,
    status TEXT,
    confidence FLOAT,
    updated_at TIMESTAMPTZ
) AS $$
BEGIN
    IF p_verified_only THEN
        -- Return from core_entities (verified)
        RETURN QUERY
        SELECT
            ce.id,
            ce.entity_type::TEXT,
            COALESCE(ce.display_name, ce.name) AS label,
            COALESCE((ce.attributes->>'domain')::TEXT, 'external') AS domain,
            map_to_knowledge_category(ce.entity_type::TEXT) AS category,
            ARRAY(SELECT jsonb_array_elements_text(ce.attributes->'tags')) AS tags,
            ce.contributed_by_org_id AS organization_id,
            COALESCE(o.name, 'Community') AS organization_name,
            COALESCE(o.primary_color, '#6b7280') AS organization_color,
            'verified'::TEXT AS status,
            1.0::FLOAT AS confidence,
            ce.updated_at::TIMESTAMPTZ  -- Explicit cast
        FROM core_entities ce
        LEFT JOIN organizations o ON o.id = ce.contributed_by_org_id
        WHERE (p_organization_id IS NULL OR ce.contributed_by_org_id = p_organization_id)
        AND (p_domain IS NULL OR (ce.attributes->>'domain')::TEXT = p_domain)
        AND (p_category IS NULL OR map_to_knowledge_category(ce.entity_type::TEXT) = p_category)
        ORDER BY ce.updated_at DESC
        LIMIT p_limit;
    ELSE
        -- Include pending extractions too
        RETURN QUERY
        (
            -- Verified entities
            SELECT
                ce.id,
                ce.entity_type::TEXT,
                COALESCE(ce.display_name, ce.name) AS label,
                COALESCE((ce.attributes->>'domain')::TEXT, 'external') AS domain,
                map_to_knowledge_category(ce.entity_type::TEXT) AS category,
                ARRAY(SELECT jsonb_array_elements_text(ce.attributes->'tags')) AS tags,
                ce.contributed_by_org_id AS organization_id,
                COALESCE(o.name, 'Community') AS organization_name,
                COALESCE(o.primary_color, '#6b7280') AS organization_color,
                'verified'::TEXT AS status,
                1.0::FLOAT AS confidence,
                ce.updated_at::TIMESTAMPTZ  -- Explicit cast
            FROM core_entities ce
            LEFT JOIN organizations o ON o.id = ce.contributed_by_org_id
            WHERE (p_organization_id IS NULL OR ce.contributed_by_org_id = p_organization_id)
            AND (p_domain IS NULL OR (ce.attributes->>'domain')::TEXT = p_domain)
            AND (p_category IS NULL OR map_to_knowledge_category(ce.entity_type::TEXT) = p_category)
        )
        UNION ALL
        (
            -- Pending extractions
            SELECT
                se.extraction_id AS id,
                se.candidate_type::TEXT AS type,
                se.candidate_key AS label,
                COALESCE(se.ecosystem::TEXT, 'external') AS domain,
                map_to_knowledge_category(se.candidate_type::TEXT) AS category,
                ARRAY[]::TEXT[] AS tags,
                se.source_organization_id AS organization_id,
                COALESCE(o.name, 'Unknown') AS organization_name,
                COALESCE(o.primary_color, '#9ca3af') AS organization_color,
                'pending'::TEXT AS status,
                se.confidence_score AS confidence,
                se.created_at::TIMESTAMPTZ AS updated_at  -- Explicit cast
            FROM staging_extractions se
            LEFT JOIN organizations o ON o.id = se.source_organization_id
            WHERE se.status = 'pending'
            AND (p_organization_id IS NULL OR se.source_organization_id = p_organization_id)
            AND (p_domain IS NULL OR se.ecosystem::TEXT = p_domain)
            AND (p_category IS NULL OR map_to_knowledge_category(se.candidate_type::TEXT) = p_category)
        )
        ORDER BY updated_at DESC
        LIMIT p_limit;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '==========================================';
    RAISE NOTICE 'Migration 028: Fix Graph Nodes Timestamp';
    RAISE NOTICE '==========================================';
    RAISE NOTICE '  - get_graph_nodes() updated with explicit TIMESTAMPTZ casts';
END $$;

COMMIT;
