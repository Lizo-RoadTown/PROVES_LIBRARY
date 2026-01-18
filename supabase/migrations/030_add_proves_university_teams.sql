-- Migration 030: Add PROVES University Teams
--
-- Updates PROVES Lab to Cal Poly Pomona and adds actual partner universities:
-- - Cal Poly Pomona (PROVES Lab - primary)
-- - Columbia University
-- - Northeastern University
-- - UC Santa Cruz
-- - Texas State University (Austin)

BEGIN;

-- =============================================================================
-- UPDATE PROVES LAB TO CAL POLY POMONA
-- =============================================================================

UPDATE organizations
SET
    name = 'Cal Poly Pomona',
    slug = 'cal-poly-pomona',
    description = 'California State Polytechnic University, Pomona - PROVES Lab',
    org_type = 'university',
    primary_color = '#1E4D2B',  -- CPP Green
    website_url = 'https://www.cpp.edu'
WHERE slug = 'proves-lab';

-- =============================================================================
-- ADD PARTNER UNIVERSITIES
-- =============================================================================

INSERT INTO organizations (name, slug, description, org_type, primary_color, website_url, verified_at)
VALUES
    (
        'Columbia University',
        'columbia',
        'Columbia University - Space Initiative',
        'university',
        '#B9D9EB',  -- Columbia Blue
        'https://www.columbia.edu',
        NOW()
    ),
    (
        'Northeastern University',
        'northeastern',
        'Northeastern University - Space Systems Lab',
        'university',
        '#C8102E',  -- Northeastern Red
        'https://www.northeastern.edu',
        NOW()
    ),
    (
        'UC Santa Cruz',
        'ucsc',
        'University of California, Santa Cruz - Space Systems',
        'university',
        '#003C6C',  -- UCSC Blue
        'https://www.ucsc.edu',
        NOW()
    ),
    (
        'Texas State University',
        'texas-state',
        'Texas State University - San Marcos, Aerospace Engineering',
        'university',
        '#501214',  -- Texas State Maroon
        'https://www.txstate.edu',
        NOW()
    )
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    primary_color = EXCLUDED.primary_color,
    website_url = EXCLUDED.website_url;

-- =============================================================================
-- REASSIGN ENTITIES FROM OLD TEST ORGS TO CAL POLY POMONA
-- Then remove the old test organizations
-- =============================================================================

-- Get the Cal Poly Pomona org ID (updated from proves-lab)
DO $$
DECLARE
    v_cpp_id UUID;
BEGIN
    SELECT id INTO v_cpp_id FROM organizations WHERE slug = 'cal-poly-pomona';

    -- Reassign all entities from old test orgs to Cal Poly Pomona
    UPDATE core_entities
    SET contributed_by_org_id = v_cpp_id
    WHERE contributed_by_org_id IN (
        SELECT id FROM organizations WHERE slug IN (
            'mit-space',
            'stanford-ssdl',
            'gatech-ssdl',
            'cu-asen',
            'calpoly-polysat'
        )
    );

    -- Now safe to delete the old test organizations
    DELETE FROM organizations WHERE slug IN (
        'mit-space',
        'stanford-ssdl',
        'gatech-ssdl',
        'cu-asen',
        'calpoly-polysat'
    );
END $$;

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
DECLARE
    v_org_count INT;
    v_org_names TEXT;
BEGIN
    SELECT COUNT(*), string_agg(name, ', ' ORDER BY name)
    INTO v_org_count, v_org_names
    FROM organizations WHERE is_active = true;

    RAISE NOTICE '=========================================';
    RAISE NOTICE 'Migration 030: PROVES University Teams';
    RAISE NOTICE '=========================================';
    RAISE NOTICE '  - Updated PROVES Lab to Cal Poly Pomona';
    RAISE NOTICE '  - Added Columbia University';
    RAISE NOTICE '  - Added Northeastern University';
    RAISE NOTICE '  - Added UC Santa Cruz';
    RAISE NOTICE '  - Added Texas State University';
    RAISE NOTICE '  - Removed placeholder test universities';
    RAISE NOTICE '  - Total organizations: %', v_org_count;
    RAISE NOTICE '  - Teams: %', v_org_names;
END $$;

COMMIT;
