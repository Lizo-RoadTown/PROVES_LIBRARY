-- Migration 025: Backfill Organization Data
--
-- Assigns all existing data to PROVES Lab (Bronco Space Lab)
-- This ensures the graph visualization has proper organization attribution

BEGIN;

-- Get the PROVES Lab organization ID
DO $$
DECLARE
    v_proves_lab_id UUID;
    v_entities_updated INT;
    v_extractions_updated INT;
BEGIN
    -- Get PROVES Lab ID
    SELECT id INTO v_proves_lab_id
    FROM organizations
    WHERE slug = 'proves-lab';

    IF v_proves_lab_id IS NULL THEN
        RAISE EXCEPTION 'PROVES Lab organization not found. Run migration 023 first.';
    END IF;

    -- Backfill core_entities
    UPDATE core_entities
    SET contributed_by_org_id = v_proves_lab_id
    WHERE contributed_by_org_id IS NULL;

    GET DIAGNOSTICS v_entities_updated = ROW_COUNT;

    -- Backfill staging_extractions
    UPDATE staging_extractions
    SET source_organization_id = v_proves_lab_id
    WHERE source_organization_id IS NULL;

    GET DIAGNOSTICS v_extractions_updated = ROW_COUNT;

    -- Backfill team_sources (if any exist without org)
    UPDATE team_sources
    SET organization_id = v_proves_lab_id
    WHERE organization_id IS NULL;

    RAISE NOTICE '=========================================';
    RAISE NOTICE 'Migration 025: Backfill Organization Data';
    RAISE NOTICE '=========================================';
    RAISE NOTICE '  - PROVES Lab ID: %', v_proves_lab_id;
    RAISE NOTICE '  - core_entities updated: %', v_entities_updated;
    RAISE NOTICE '  - staging_extractions updated: %', v_extractions_updated;
END $$;

COMMIT;
