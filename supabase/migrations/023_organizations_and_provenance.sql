-- Migration 023: Organizations and Provenance Tracking
--
-- Implements multi-tenant support for universities/teams:
-- 1. Organizations table - universities, research groups, teams
-- 2. Organization membership - who belongs to which org
-- 3. Provenance tracking on extractions - which org contributed what
-- 4. Sharing workflow - private → pending_review → shared
--
-- Flow: Org's sources → Org's review queue → Verified → Shared library

BEGIN;

-- =============================================================================
-- PART 1: ORGANIZATIONS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    name TEXT NOT NULL,                      -- "PROVES Lab", "University of Colorado"
    slug TEXT NOT NULL UNIQUE,               -- "proves-lab", "univ-colorado"
    description TEXT,

    -- Branding
    logo_url TEXT,
    primary_color TEXT DEFAULT '#3b82f6',    -- For graph visualization

    -- Contact
    contact_email TEXT,
    website_url TEXT,

    -- Type
    org_type TEXT DEFAULT 'university' CHECK (org_type IN (
        'university',
        'research_lab',
        'company',
        'open_source',
        'consortium'
    )),

    -- Settings
    settings JSONB DEFAULT '{}',             -- Org-specific settings

    -- Status
    is_active BOOLEAN DEFAULT true NOT NULL,
    verified_at TIMESTAMPTZ,                 -- When org was verified by admin

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations(slug);
CREATE INDEX IF NOT EXISTS idx_organizations_active ON organizations(is_active) WHERE is_active = true;

-- =============================================================================
-- PART 2: ORGANIZATION MEMBERSHIP
-- =============================================================================

CREATE TABLE IF NOT EXISTS organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- References
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Role within the organization
    role TEXT NOT NULL DEFAULT 'member' CHECK (role IN (
        'admin',       -- Can manage org settings, sources, members
        'lead',        -- Can approve extractions, manage sources
        'engineer',    -- Can review extractions from org's sources
        'researcher',  -- Can view and query, limited review
        'member'       -- Read-only access
    )),

    -- Display info
    display_name TEXT,                       -- Name to show in attribution
    title TEXT,                              -- "Graduate Student", "PI", etc.

    -- Status
    is_primary_org BOOLEAN DEFAULT false,    -- User's primary affiliation
    joined_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT unique_org_member UNIQUE (organization_id, user_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_org_members_org ON organization_members(organization_id);
CREATE INDEX IF NOT EXISTS idx_org_members_user ON organization_members(user_id);
CREATE INDEX IF NOT EXISTS idx_org_members_role ON organization_members(organization_id, role);

-- =============================================================================
-- PART 3: SHARING STATUS ENUM
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sharing_status') THEN
        CREATE TYPE sharing_status AS ENUM (
            'private',          -- Only visible to source org
            'pending_review',   -- Awaiting org review
            'shared'            -- Visible to all (in collective library)
        );
    END IF;
END $$;

-- =============================================================================
-- PART 4: ADD PROVENANCE TO STAGING_EXTRACTIONS
-- =============================================================================

-- Add organization columns to staging_extractions table
DO $$
BEGIN
    -- Source organization (who owns the source this came from)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'staging_extractions' AND column_name = 'source_organization_id'
    ) THEN
        ALTER TABLE staging_extractions ADD COLUMN source_organization_id UUID REFERENCES organizations(id);
    END IF;

    -- Submitted by (who triggered the extraction)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'staging_extractions' AND column_name = 'submitted_by_user_id'
    ) THEN
        ALTER TABLE staging_extractions ADD COLUMN submitted_by_user_id UUID REFERENCES auth.users(id);
    END IF;

    -- Verified by (who approved for sharing)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'staging_extractions' AND column_name = 'verified_by_user_id'
    ) THEN
        ALTER TABLE staging_extractions ADD COLUMN verified_by_user_id UUID REFERENCES auth.users(id);
    END IF;

    -- Verification timestamp
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'staging_extractions' AND column_name = 'verified_at'
    ) THEN
        ALTER TABLE staging_extractions ADD COLUMN verified_at TIMESTAMPTZ;
    END IF;

    -- Sharing status
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'staging_extractions' AND column_name = 'sharing_status'
    ) THEN
        ALTER TABLE staging_extractions ADD COLUMN sharing_status sharing_status DEFAULT 'pending_review';
    END IF;
END $$;

-- Index for filtering by organization
CREATE INDEX IF NOT EXISTS idx_staging_extractions_org ON staging_extractions(source_organization_id);
CREATE INDEX IF NOT EXISTS idx_staging_extractions_sharing ON staging_extractions(sharing_status);
CREATE INDEX IF NOT EXISTS idx_staging_extractions_org_pending ON staging_extractions(source_organization_id, sharing_status)
    WHERE sharing_status = 'pending_review';

-- =============================================================================
-- PART 5: ADD ORGANIZATION TO TEAM_SOURCES
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'team_sources' AND column_name = 'organization_id'
    ) THEN
        ALTER TABLE team_sources ADD COLUMN organization_id UUID REFERENCES organizations(id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_team_sources_org ON team_sources(organization_id);

-- =============================================================================
-- PART 6: ADD ORGANIZATION TO CORE_ENTITIES (promoted entities)
-- =============================================================================

DO $$
BEGIN
    -- Track which org contributed this entity
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'core_entities' AND column_name = 'contributed_by_org_id'
    ) THEN
        ALTER TABLE core_entities ADD COLUMN contributed_by_org_id UUID REFERENCES organizations(id);
    END IF;

    -- Track who verified it
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'core_entities' AND column_name = 'verified_by_user_id'
    ) THEN
        ALTER TABLE core_entities ADD COLUMN verified_by_user_id UUID REFERENCES auth.users(id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_core_entities_org ON core_entities(contributed_by_org_id);

-- =============================================================================
-- PART 7: ROW LEVEL SECURITY
-- =============================================================================

ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;

-- Everyone can see active organizations
CREATE POLICY organizations_select ON organizations
    FOR SELECT TO authenticated
    USING (is_active = true);

-- Only admins can insert/update organizations
CREATE POLICY organizations_admin_insert ON organizations
    FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM organization_members om
            WHERE om.user_id = auth.uid()
            AND om.role = 'admin'
        )
        OR NOT EXISTS (SELECT 1 FROM organizations) -- Allow first org creation
    );

CREATE POLICY organizations_admin_update ON organizations
    FOR UPDATE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM organization_members om
            WHERE om.organization_id = organizations.id
            AND om.user_id = auth.uid()
            AND om.role = 'admin'
        )
    );

-- Users can see memberships for orgs they belong to
CREATE POLICY org_members_select ON organization_members
    FOR SELECT TO authenticated
    USING (
        user_id = auth.uid()
        OR organization_id IN (
            SELECT organization_id FROM organization_members WHERE user_id = auth.uid()
        )
    );

-- Admins/leads can manage members
CREATE POLICY org_members_manage ON organization_members
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM organization_members om
            WHERE om.organization_id = organization_members.organization_id
            AND om.user_id = auth.uid()
            AND om.role IN ('admin', 'lead')
        )
    );

-- =============================================================================
-- PART 8: HELPER FUNCTIONS
-- =============================================================================

-- Get user's organizations
CREATE OR REPLACE FUNCTION get_user_organizations(p_user_id UUID DEFAULT NULL)
RETURNS TABLE (
    org_id UUID,
    org_name TEXT,
    org_slug TEXT,
    org_color TEXT,
    user_role TEXT,
    is_primary BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        o.id,
        o.name,
        o.slug,
        o.primary_color,
        om.role,
        om.is_primary_org
    FROM organizations o
    JOIN organization_members om ON om.organization_id = o.id
    WHERE om.user_id = COALESCE(p_user_id, auth.uid())
    AND o.is_active = true
    ORDER BY om.is_primary_org DESC, o.name;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get organization's review queue (extractions from their sources)
CREATE OR REPLACE FUNCTION get_org_review_queue(
    p_organization_id UUID,
    p_status TEXT DEFAULT 'pending_review',
    p_limit INT DEFAULT 50
)
RETURNS TABLE (
    extraction_id UUID,
    candidate_type TEXT,
    candidate_key TEXT,
    confidence_score FLOAT,
    source_name TEXT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    -- Verify user has access to this org
    IF NOT EXISTS (
        SELECT 1 FROM organization_members
        WHERE organization_id = p_organization_id
        AND user_id = auth.uid()
        AND role IN ('admin', 'lead', 'engineer')
    ) THEN
        RAISE EXCEPTION 'Access denied to organization review queue';
    END IF;

    RETURN QUERY
    SELECT
        se.extraction_id,
        se.candidate_type::TEXT,
        se.candidate_key,
        se.confidence_score,
        ts.name,
        se.created_at
    FROM staging_extractions se
    LEFT JOIN team_sources ts ON ts.id = se.source_id
    WHERE se.source_organization_id = p_organization_id
    AND se.sharing_status = p_status::sharing_status
    ORDER BY se.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Approve extraction for sharing (promotes to shared library)
CREATE OR REPLACE FUNCTION approve_for_sharing(
    p_extraction_id UUID,
    p_notes TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_org_id UUID;
BEGIN
    -- Get the extraction's org
    SELECT source_organization_id INTO v_org_id
    FROM staging_extractions WHERE extraction_id = p_extraction_id;

    -- Verify user can approve for this org
    IF NOT EXISTS (
        SELECT 1 FROM organization_members
        WHERE organization_id = v_org_id
        AND user_id = auth.uid()
        AND role IN ('admin', 'lead', 'engineer')
    ) THEN
        RAISE EXCEPTION 'Not authorized to approve extractions for this organization';
    END IF;

    -- Update the extraction
    UPDATE staging_extractions
    SET sharing_status = 'shared',
        verified_by_user_id = auth.uid(),
        verified_at = NOW()
    WHERE extraction_id = p_extraction_id
    AND source_organization_id = v_org_id;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get organization stats for dashboard
CREATE OR REPLACE FUNCTION get_org_stats(p_organization_id UUID)
RETURNS TABLE (
    our_sources INT,
    our_pending_reviews INT,
    our_verified_entities INT,
    our_contributors INT,
    shared_total INT,
    shared_from_us INT,
    shared_from_others INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        -- Our sources
        (SELECT COUNT(*)::INT FROM team_sources WHERE organization_id = p_organization_id AND is_active = true),

        -- Our pending reviews
        (SELECT COUNT(*)::INT FROM staging_extractions WHERE source_organization_id = p_organization_id AND sharing_status = 'pending_review'),

        -- Our verified entities (in core_entities)
        (SELECT COUNT(*)::INT FROM core_entities WHERE contributed_by_org_id = p_organization_id),

        -- Our contributors
        (SELECT COUNT(*)::INT FROM organization_members WHERE organization_id = p_organization_id),

        -- Total shared entities
        (SELECT COUNT(*)::INT FROM core_entities),

        -- Shared from us
        (SELECT COUNT(*)::INT FROM core_entities WHERE contributed_by_org_id = p_organization_id),

        -- Shared from others
        (SELECT COUNT(*)::INT FROM core_entities WHERE contributed_by_org_id IS NULL OR contributed_by_org_id != p_organization_id);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get all organizations with their colors (for graph visualization)
CREATE OR REPLACE FUNCTION get_all_organizations_for_graph()
RETURNS TABLE (
    org_id UUID,
    org_name TEXT,
    org_slug TEXT,
    org_color TEXT,
    entity_count INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        o.id,
        o.name,
        o.slug,
        o.primary_color,
        COALESCE((SELECT COUNT(*)::INT FROM core_entities WHERE contributed_by_org_id = o.id), 0)
    FROM organizations o
    WHERE o.is_active = true
    ORDER BY o.name;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- PART 9: TRIGGERS
-- =============================================================================

-- Auto-update timestamps
CREATE OR REPLACE FUNCTION update_organizations_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS organizations_updated_at ON organizations;
CREATE TRIGGER organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_organizations_timestamp();

-- Auto-assign org from source when extraction is created
CREATE OR REPLACE FUNCTION auto_assign_extraction_org()
RETURNS TRIGGER AS $$
BEGIN
    -- If extraction has a source_id but no organization, get it from the source
    IF NEW.source_id IS NOT NULL AND NEW.source_organization_id IS NULL THEN
        SELECT organization_id INTO NEW.source_organization_id
        FROM team_sources WHERE id = NEW.source_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS staging_extractions_auto_org ON staging_extractions;
CREATE TRIGGER staging_extractions_auto_org
    BEFORE INSERT ON staging_extractions
    FOR EACH ROW
    EXECUTE FUNCTION auto_assign_extraction_org();

-- =============================================================================
-- PART 10: SEED DEFAULT ORGANIZATION (for existing data)
-- =============================================================================

-- Create a default organization for existing data
INSERT INTO organizations (name, slug, description, org_type, primary_color, verified_at)
VALUES (
    'PROVES Lab',
    'proves-lab',
    'Primary research lab - existing data migrated here',
    'research_lab',
    '#3b82f6',
    NOW()
)
ON CONFLICT (slug) DO NOTHING;

-- =============================================================================
-- PART 11: COMMENTS
-- =============================================================================

COMMENT ON TABLE organizations IS
'Universities, research labs, and teams that contribute to the collective knowledge base';

COMMENT ON TABLE organization_members IS
'User membership in organizations with role-based access';

COMMENT ON COLUMN staging_extractions.source_organization_id IS
'Which organization owns the source this extraction came from';

COMMENT ON COLUMN staging_extractions.sharing_status IS
'Workflow state: private (org only) → pending_review → shared (in collective)';

COMMENT ON COLUMN core_entities.contributed_by_org_id IS
'Attribution: which organization contributed this verified entity';

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
DECLARE
    v_org_count INT;
BEGIN
    SELECT COUNT(*) INTO v_org_count FROM organizations;

    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Migration 023: Organizations and Provenance';
    RAISE NOTICE '===========================================';
    RAISE NOTICE '  - organizations table created';
    RAISE NOTICE '  - organization_members table created';
    RAISE NOTICE '  - sharing_status enum created';
    RAISE NOTICE '  - Provenance columns added to staging_extractions';
    RAISE NOTICE '  - Organization column added to team_sources';
    RAISE NOTICE '  - Attribution columns added to core_entities';
    RAISE NOTICE '  - get_user_organizations function created';
    RAISE NOTICE '  - get_org_review_queue function created';
    RAISE NOTICE '  - approve_for_sharing function created';
    RAISE NOTICE '  - get_org_stats function created';
    RAISE NOTICE '  - get_all_organizations_for_graph function created';
    RAISE NOTICE '  - Default PROVES Lab organization created';
    RAISE NOTICE '  - Total organizations: %', v_org_count;
END $$;

COMMIT;
