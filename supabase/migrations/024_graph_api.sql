-- Migration 024: Graph API Functions
--
-- Provides clean graph data for the Cytoscape.js renderer:
-- 1. get_graph_nodes() - Returns nodes with tenant filtering
-- 2. get_graph_edges() - Returns edges (couplings) with tenant filtering
-- 3. get_graph_data() - Combined nodes + edges in one call
--
-- Data contract:
--   nodes[]: { id, type, label, domain, tags, organization_id, status, confidence, updated_at }
--   edges[]: { id, source, target, relation, organization_id, status, confidence }

BEGIN;

-- =============================================================================
-- PART 1: NODE TYPES FOR KNOWLEDGE MAP
-- =============================================================================

-- Map entity types to Knowledge Map categories
-- Procedures / Architecture / Interfaces / Decisions / Lessons
CREATE OR REPLACE FUNCTION map_to_knowledge_category(p_entity_type TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN CASE p_entity_type
        -- Procedures
        WHEN 'procedure' THEN 'procedures'
        WHEN 'checklist' THEN 'procedures'
        WHEN 'runbook' THEN 'procedures'
        WHEN 'workflow' THEN 'procedures'

        -- Architecture
        WHEN 'component' THEN 'architecture'
        WHEN 'system' THEN 'architecture'
        WHEN 'subsystem' THEN 'architecture'
        WHEN 'module' THEN 'architecture'

        -- Interfaces
        WHEN 'interface' THEN 'interfaces'
        WHEN 'port' THEN 'interfaces'
        WHEN 'connection' THEN 'interfaces'
        WHEN 'command' THEN 'interfaces'
        WHEN 'telemetry' THEN 'interfaces'
        WHEN 'event' THEN 'interfaces'

        -- Decisions
        WHEN 'decision' THEN 'decisions'
        WHEN 'adr' THEN 'decisions'
        WHEN 'trade_study' THEN 'decisions'
        WHEN 'rationale' THEN 'decisions'

        -- Lessons Learned
        WHEN 'lesson' THEN 'lessons'
        WHEN 'postmortem' THEN 'lessons'
        WHEN 'gotcha' THEN 'lessons'
        WHEN 'risk' THEN 'lessons'

        ELSE 'architecture'  -- Default
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================================================
-- PART 2: GET GRAPH NODES
-- =============================================================================

CREATE OR REPLACE FUNCTION get_graph_nodes(
    p_organization_id UUID DEFAULT NULL,  -- Filter by org (NULL = all visible)
    p_domain TEXT DEFAULT NULL,           -- Filter by domain (ops/software/hardware/process)
    p_category TEXT DEFAULT NULL,         -- Filter by knowledge category
    p_verified_only BOOLEAN DEFAULT true, -- Only show verified (core_entities)
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
            1.0::FLOAT AS confidence,  -- Verified = full confidence
            ce.updated_at
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
                ce.updated_at
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
                se.created_at AS updated_at
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
-- PART 3: GET GRAPH EDGES
-- =============================================================================

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
            eq.source_entity_id AS source,
            eq.target_entity_id AS target,
            eq.equivalence_type::TEXT AS relation,
            eq.discovered_by_org_id AS organization_id,
            COALESCE(o.name, 'Community') AS organization_name,
            'verified'::TEXT AS status,
            eq.confidence_score AS confidence
        FROM core_equivalences eq
        LEFT JOIN organizations o ON o.id = eq.discovered_by_org_id
        WHERE (p_organization_id IS NULL OR eq.discovered_by_org_id = p_organization_id)
        ORDER BY eq.created_at DESC
        LIMIT p_limit;
    ELSE
        -- Include edges inferred from extractions (connection/dependency types)
        RETURN QUERY
        (
            -- Verified equivalences
            SELECT
                eq.id,
                eq.source_entity_id AS source,
                eq.target_entity_id AS target,
                eq.equivalence_type::TEXT AS relation,
                eq.discovered_by_org_id AS organization_id,
                COALESCE(o.name, 'Community') AS organization_name,
                'verified'::TEXT AS status,
                eq.confidence_score AS confidence
            FROM core_equivalences eq
            LEFT JOIN organizations o ON o.id = eq.discovered_by_org_id
            WHERE (p_organization_id IS NULL OR eq.discovered_by_org_id = p_organization_id)
        )
        UNION ALL
        (
            -- Pending coupling extractions
            SELECT
                se.extraction_id AS id,
                -- Parse source/target from candidate_key (format: "Source→Target" or "Source_to_Target")
                (SELECT ce.id FROM core_entities ce
                 WHERE ce.canonical_key = split_part(
                     replace(replace(se.candidate_key, '→', '_to_'), '->', '_to_'),
                     '_to_', 1
                 ) LIMIT 1) AS source,
                (SELECT ce.id FROM core_entities ce
                 WHERE ce.canonical_key = split_part(
                     replace(replace(se.candidate_key, '→', '_to_'), '->', '_to_'),
                     '_to_', 2
                 ) LIMIT 1) AS target,
                COALESCE((se.candidate_payload->>'relationship')::TEXT, 'depends_on') AS relation,
                se.source_organization_id AS organization_id,
                COALESCE(o.name, 'Unknown') AS organization_name,
                'pending'::TEXT AS status,
                se.confidence_score AS confidence
            FROM staging_extractions se
            LEFT JOIN organizations o ON o.id = se.source_organization_id
            WHERE se.status = 'pending'
            AND se.candidate_type IN ('connection', 'dependency', 'inheritance')
            AND (p_organization_id IS NULL OR se.source_organization_id = p_organization_id)
        )
        ORDER BY confidence DESC
        LIMIT p_limit;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- PART 4: COMBINED GRAPH DATA (single call)
-- =============================================================================

CREATE OR REPLACE FUNCTION get_graph_data(
    p_organization_id UUID DEFAULT NULL,
    p_domain TEXT DEFAULT NULL,
    p_category TEXT DEFAULT NULL,
    p_verified_only BOOLEAN DEFAULT true,
    p_node_limit INT DEFAULT 500,
    p_edge_limit INT DEFAULT 1000
)
RETURNS TABLE (
    data_type TEXT,
    payload JSONB
) AS $$
BEGIN
    -- Return nodes
    RETURN QUERY
    SELECT
        'nodes'::TEXT AS data_type,
        jsonb_agg(jsonb_build_object(
            'id', n.id,
            'type', n.type,
            'label', n.label,
            'domain', n.domain,
            'category', n.category,
            'tags', n.tags,
            'organization_id', n.organization_id,
            'organization_name', n.organization_name,
            'organization_color', n.organization_color,
            'status', n.status,
            'confidence', n.confidence,
            'updated_at', n.updated_at
        )) AS payload
    FROM get_graph_nodes(p_organization_id, p_domain, p_category, p_verified_only, p_node_limit) n;

    -- Return edges
    RETURN QUERY
    SELECT
        'edges'::TEXT AS data_type,
        jsonb_agg(jsonb_build_object(
            'id', e.id,
            'source', e.source,
            'target', e.target,
            'relation', e.relation,
            'organization_id', e.organization_id,
            'organization_name', e.organization_name,
            'status', e.status,
            'confidence', e.confidence
        )) AS payload
    FROM get_graph_edges(p_organization_id, p_verified_only, p_edge_limit) e
    WHERE e.source IS NOT NULL AND e.target IS NOT NULL;  -- Only include edges with resolved endpoints
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- PART 5: CATEGORY COUNTS (for Knowledge Map tiles)
-- =============================================================================

CREATE OR REPLACE FUNCTION get_graph_category_counts(
    p_organization_id UUID DEFAULT NULL,
    p_verified_only BOOLEAN DEFAULT true
)
RETURNS TABLE (
    category TEXT,
    count BIGINT,
    verified_count BIGINT,
    pending_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH all_nodes AS (
        SELECT
            n.category,
            n.status
        FROM get_graph_nodes(p_organization_id, NULL, NULL, false, 10000) n
    )
    SELECT
        an.category,
        COUNT(*)::BIGINT AS count,
        COUNT(*) FILTER (WHERE an.status = 'verified')::BIGINT AS verified_count,
        COUNT(*) FILTER (WHERE an.status = 'pending')::BIGINT AS pending_count
    FROM all_nodes an
    GROUP BY an.category
    ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '=========================================';
    RAISE NOTICE 'Migration 024: Graph API Functions';
    RAISE NOTICE '=========================================';
    RAISE NOTICE '  - map_to_knowledge_category() created';
    RAISE NOTICE '  - get_graph_nodes() created';
    RAISE NOTICE '  - get_graph_edges() created';
    RAISE NOTICE '  - get_graph_data() created';
    RAISE NOTICE '  - get_graph_category_counts() created';
END $$;

COMMIT;
