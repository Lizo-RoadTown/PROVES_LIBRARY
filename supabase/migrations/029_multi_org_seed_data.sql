-- Migration 029: Multi-Organization Seed Data
--
-- Adds additional university organizations with distinct colors
-- and assigns some entities to different orgs to demonstrate multi-tenant graph

BEGIN;

-- =============================================================================
-- ADD MORE ORGANIZATIONS (Universities with distinct colors)
-- =============================================================================

INSERT INTO organizations (name, slug, description, org_type, primary_color, verified_at)
VALUES
    ('MIT Space Lab', 'mit-space', 'Massachusetts Institute of Technology Space Systems', 'university', '#a31f34', NOW()),
    ('Stanford SSDL', 'stanford-ssdl', 'Stanford Space Systems Development Lab', 'university', '#8c1515', NOW()),
    ('Georgia Tech SSDL', 'gatech-ssdl', 'Georgia Tech Space Systems Design Lab', 'university', '#b3a369', NOW()),
    ('CU Boulder ASEN', 'cu-asen', 'University of Colorado Boulder Aerospace', 'university', '#cfb87c', NOW()),
    ('Cal Poly PolySat', 'calpoly-polysat', 'Cal Poly San Luis Obispo CubeSat Lab', 'university', '#154734', NOW())
ON CONFLICT (slug) DO NOTHING;

-- =============================================================================
-- ADD CROSS-ORG ENTITIES
-- Each org contributes different types of knowledge
-- =============================================================================

DO $$
DECLARE
    v_mit_id UUID;
    v_stanford_id UUID;
    v_gatech_id UUID;
    v_cu_id UUID;
    v_calpoly_id UUID;
    v_run_id UUID;
BEGIN
    -- Get org IDs
    SELECT id INTO v_mit_id FROM organizations WHERE slug = 'mit-space';
    SELECT id INTO v_stanford_id FROM organizations WHERE slug = 'stanford-ssdl';
    SELECT id INTO v_gatech_id FROM organizations WHERE slug = 'gatech-ssdl';
    SELECT id INTO v_cu_id FROM organizations WHERE slug = 'cu-asen';
    SELECT id INTO v_calpoly_id FROM organizations WHERE slug = 'calpoly-polysat';

    -- Create a pipeline run for cross-org data
    INSERT INTO pipeline_runs (run_name, run_type, started_at, completed_at)
    VALUES ('seed_multi_org_demo', 'manual', NOW(), NOW())
    RETURNING id INTO v_run_id;

    -- ==========================================================================
    -- MIT: Contributes propulsion and guidance knowledge
    -- ==========================================================================

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('cold_gas_thruster', 'Cold Gas Thruster', 'cold_gas_thruster', 'component',
            '{"domain": "hardware", "description": "Nitrogen-based cold gas propulsion system", "tags": ["propulsion", "attitude", "maneuver"]}'::jsonb,
            v_mit_id, v_run_id);

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('star_tracker', 'Star Tracker', 'star_tracker', 'component',
            '{"domain": "hardware", "description": "Optical attitude determination sensor", "tags": ["sensors", "navigation", "attitude"]}'::jsonb,
            v_mit_id, v_run_id);

    -- ==========================================================================
    -- Stanford: Contributes software and testing procedures
    -- ==========================================================================

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('flight_software_fsw', 'Flight Software Framework', 'flight_software_fsw', 'component',
            '{"domain": "software", "description": "Modular flight software architecture using F Prime", "tags": ["software", "fprime", "framework"]}'::jsonb,
            v_stanford_id, v_run_id);

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('flatsat_testing', 'FlatSat Testing Procedure', 'flatsat_testing', 'procedure',
            '{"domain": "ops", "description": "Hardware-in-the-loop testing on development flat satellite", "tags": ["testing", "integration", "verification"]}'::jsonb,
            v_stanford_id, v_run_id);

    -- ==========================================================================
    -- Georgia Tech: Contributes power system and thermal knowledge
    -- ==========================================================================

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('mppt_controller', 'MPPT Solar Controller', 'mppt_controller', 'component',
            '{"domain": "hardware", "description": "Maximum Power Point Tracking for solar panels", "tags": ["power", "solar", "efficiency"]}'::jsonb,
            v_gatech_id, v_run_id);

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('lesson_deployables', 'Lesson: Deployable Mechanism Testing', 'lesson_deployables', 'failure_mode',
            '{"domain": "hardware", "description": "Deployables failed during thermal vacuum - insufficient margin", "tags": ["thermal", "deployables", "testing"], "category": "lesson"}'::jsonb,
            v_gatech_id, v_run_id);

    -- ==========================================================================
    -- CU Boulder: Contributes communications and ground ops
    -- ==========================================================================

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('sband_radio', 'S-Band Radio', 'sband_radio', 'component',
            '{"domain": "hardware", "description": "High-bandwidth S-band communication system", "tags": ["radio", "sband", "highrate"]}'::jsonb,
            v_cu_id, v_run_id);

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('ground_station_ops', 'Ground Station Operations', 'ground_station_ops', 'procedure',
            '{"domain": "ops", "description": "Automated pass scheduling and execution", "tags": ["ground", "operations", "scheduling"]}'::jsonb,
            v_cu_id, v_run_id);

    -- ==========================================================================
    -- Cal Poly: Contributes CubeSat standards and deployment knowledge
    -- ==========================================================================

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('ppod_interface', 'P-POD Interface Spec', 'ppod_interface', 'interface',
            '{"domain": "hardware", "description": "Poly-PicoSatellite Orbital Deployer interface requirements", "tags": ["deployer", "interface", "standard"]}'::jsonb,
            v_calpoly_id, v_run_id);

    INSERT INTO core_entities (name, display_name, canonical_key, entity_type, attributes, contributed_by_org_id, created_by_run_id)
    VALUES ('cubesat_standard', 'CubeSat Design Standard', 'cubesat_standard', 'constraint',
            '{"domain": "hardware", "description": "1U/2U/3U form factor specifications and requirements", "tags": ["standard", "cubesat", "specification"], "category": "decision"}'::jsonb,
            v_calpoly_id, v_run_id);

    -- ==========================================================================
    -- CREATE CROSS-ORG EDGES
    -- ==========================================================================

    -- MIT star tracker connects to ADCS (PROVES)
    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'star_tracker' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'adcs' ORDER BY created_at DESC LIMIT 1),
        0.88, 'Star tracker provides high-accuracy attitude data to ADCS', true, NOW(), v_run_id;

    -- Stanford FSW runs on PROVES flight computer
    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'flight_software_fsw' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'flight_computer' ORDER BY created_at DESC LIMIT 1),
        0.92, 'F Prime flight software deployed on flight computer', true, NOW(), v_run_id;

    -- GT MPPT connects to PROVES EPS
    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'mppt_controller' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'eps' ORDER BY created_at DESC LIMIT 1),
        0.90, 'MPPT controller integrated with EPS', true, NOW(), v_run_id;

    -- CU S-band extends PROVES comm system
    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'sband_radio' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'comm_system' ORDER BY created_at DESC LIMIT 1),
        0.85, 'S-band provides high-rate downlink alongside UHF', true, NOW(), v_run_id;

    -- Cal Poly standard constrains all CubeSats
    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'cubesat_standard' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'ppod_interface' ORDER BY created_at DESC LIMIT 1),
        0.95, 'CubeSat standard defines P-POD compatibility', true, NOW(), v_run_id;

    -- Cross-org lesson connection
    INSERT INTO core_equivalences (entity_a_id, entity_b_id, confidence, evidence_text, is_validated, validated_at, created_by_run_id)
    SELECT
        (SELECT id FROM core_entities WHERE canonical_key = 'lesson_deployables' ORDER BY created_at DESC LIMIT 1),
        (SELECT id FROM core_entities WHERE canonical_key = 'lesson_thermal' ORDER BY created_at DESC LIMIT 1),
        0.75, 'Both thermal-related lessons - shared learning', true, NOW(), v_run_id;

    RAISE NOTICE '=========================================';
    RAISE NOTICE 'Migration 029: Multi-Org Seed Data';
    RAISE NOTICE '=========================================';
    RAISE NOTICE '  - Added 5 university organizations';
    RAISE NOTICE '  - MIT (red): propulsion, guidance';
    RAISE NOTICE '  - Stanford (cardinal): software, testing';
    RAISE NOTICE '  - Georgia Tech (gold): power, thermal';
    RAISE NOTICE '  - CU Boulder (gold): comms, ground ops';
    RAISE NOTICE '  - Cal Poly (green): standards, deployers';
    RAISE NOTICE '  - Created 10 new entities across orgs';
    RAISE NOTICE '  - Created 6 cross-org equivalences';
END $$;

COMMIT;
