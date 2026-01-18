-- Migration 033: Grant anon access to review_queue_view
-- The dashboard uses anon key for unauthenticated access during development
-- This allows the extraction review UI to work without authentication
--
-- NOTE: In production, this should be replaced with proper authentication
-- and these anon policies should be removed or restricted

BEGIN;

-- =============================================================================
-- PART 1: GRANT OBJECT ACCESS TO ANON ROLE
-- =============================================================================

-- Grant SELECT on review_queue_view to anon
GRANT SELECT ON review_queue_view TO anon;

-- Also grant SELECT on the underlying tables that the view references
-- (views need access to the underlying tables they query)
GRANT SELECT ON staging_extractions TO anon;
GRANT SELECT ON raw_snapshots TO anon;
GRANT SELECT ON validation_decisions TO anon;
GRANT SELECT ON validation_edits TO anon;

-- Grant execute on RPC functions to anon (for demo/development)
-- In production, these should require authenticated users
GRANT EXECUTE ON FUNCTION record_review_decision TO anon;
GRANT EXECUTE ON FUNCTION record_review_edit TO anon;

-- =============================================================================
-- PART 2: ADD RLS POLICIES FOR ANON ROLE
-- =============================================================================
-- Since RLS is enabled on these tables (from migration 032), we need
-- explicit policies for anon to read data

-- staging_extractions: anon can read all extractions
DROP POLICY IF EXISTS staging_extractions_anon_select ON staging_extractions;
CREATE POLICY staging_extractions_anon_select ON staging_extractions
    FOR SELECT TO anon
    USING (true);

-- raw_snapshots: anon can read all snapshots
DROP POLICY IF EXISTS raw_snapshots_anon_select ON raw_snapshots;
CREATE POLICY raw_snapshots_anon_select ON raw_snapshots
    FOR SELECT TO anon
    USING (true);

-- validation_decisions: anon can read all decisions
DROP POLICY IF EXISTS validation_decisions_anon_select ON validation_decisions;
CREATE POLICY validation_decisions_anon_select ON validation_decisions
    FOR SELECT TO anon
    USING (true);

-- validation_edits: anon can read all edits
DROP POLICY IF EXISTS validation_edits_anon_select ON validation_edits;
CREATE POLICY validation_edits_anon_select ON validation_edits
    FOR SELECT TO anon
    USING (true);

-- Allow anon to insert validation decisions and edits (for demo)
DROP POLICY IF EXISTS staging_extractions_anon_update ON staging_extractions;
CREATE POLICY staging_extractions_anon_update ON staging_extractions
    FOR UPDATE TO anon
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS validation_decisions_anon_insert ON validation_decisions;
CREATE POLICY validation_decisions_anon_insert ON validation_decisions
    FOR INSERT TO anon
    WITH CHECK (true);

DROP POLICY IF EXISTS validation_edits_anon_insert ON validation_edits;
CREATE POLICY validation_edits_anon_insert ON validation_edits
    FOR INSERT TO anon
    WITH CHECK (true);

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '=========================================';
    RAISE NOTICE 'Migration 033: Anon Access for Review UI';
    RAISE NOTICE '=========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Granted to anon role:';
    RAISE NOTICE '  - SELECT on review_queue_view';
    RAISE NOTICE '  - SELECT on staging_extractions, raw_snapshots, validation_decisions, validation_edits';
    RAISE NOTICE '  - EXECUTE on record_review_decision, record_review_edit';
    RAISE NOTICE '';
    RAISE NOTICE 'Added RLS policies for anon:';
    RAISE NOTICE '  - staging_extractions_anon_select (read all)';
    RAISE NOTICE '  - staging_extractions_anon_update (update all)';
    RAISE NOTICE '  - raw_snapshots_anon_select (read all)';
    RAISE NOTICE '  - validation_decisions_anon_select (read all)';
    RAISE NOTICE '  - validation_decisions_anon_insert (insert all)';
    RAISE NOTICE '  - validation_edits_anon_select (read all)';
    RAISE NOTICE '  - validation_edits_anon_insert (insert all)';
    RAISE NOTICE '';
    RAISE NOTICE 'WARNING: These policies are for development only.';
    RAISE NOTICE 'In production, restrict anon access and require authentication.';
END $$;

COMMIT;
