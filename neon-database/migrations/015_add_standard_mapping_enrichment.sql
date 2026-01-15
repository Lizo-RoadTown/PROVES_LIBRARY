-- ============================================================================
-- Migration 015: Add Standard Mapping Enrichment Type
-- ============================================================================
-- Date: 2026-01-15
-- Purpose: Enable storage of mappings between PROVES entities and external
--          standards like XTCE, SysML, OWL, GraphML for export/integration
-- ============================================================================

BEGIN;

-- ============================================================================
-- PART 1: UPDATE ENRICHMENT TYPE CHECK CONSTRAINT
-- ============================================================================

-- Drop old constraint and add new one with 'standard_mapping' included
DO $$
BEGIN
  -- Drop existing constraint if it exists
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'knowledge_enrichment_enrichment_type_check'
      AND conrelid = 'knowledge_enrichment'::regclass
  ) THEN
    ALTER TABLE knowledge_enrichment DROP CONSTRAINT knowledge_enrichment_enrichment_type_check;
  END IF;

  -- Add new constraint with standard_mapping
  ALTER TABLE knowledge_enrichment ADD CONSTRAINT knowledge_enrichment_enrichment_type_check
    CHECK (
      enrichment_type IN (
        'alias',
        'duplicate_merge',
        'cross_source',
        'temporal_update',
        'epistemic_refinement',
        'standard_mapping'
      )
    );
END $$;


-- ============================================================================
-- PART 2: ADD STANDARD MAPPING COLUMNS
-- ============================================================================

-- Standard identification
ALTER TABLE knowledge_enrichment ADD COLUMN IF NOT EXISTS
  standard TEXT;

ALTER TABLE knowledge_enrichment ADD COLUMN IF NOT EXISTS
  standard_version TEXT;

-- Standard-specific entity reference
ALTER TABLE knowledge_enrichment ADD COLUMN IF NOT EXISTS
  standard_key TEXT;  -- Entity type in standard (e.g., 'Parameter', 'MetaCommand', 'Block', 'Class')

ALTER TABLE knowledge_enrichment ADD COLUMN IF NOT EXISTS
  standard_name TEXT;  -- Name in standard namespace (e.g., 'EPS_BattV', 'RadioDriver')

-- Optional constraints for scoping
ALTER TABLE knowledge_enrichment ADD COLUMN IF NOT EXISTS
  standard_constraints JSONB;  -- Flexible storage for namespace, container, subsystem, etc.


-- ============================================================================
-- PART 3: ADD COMMENTS
-- ============================================================================

COMMENT ON COLUMN knowledge_enrichment.standard IS
  'Standard name for standard_mapping enrichments (e.g., "xtce", "sysml_v2", "owl", "graphml")';

COMMENT ON COLUMN knowledge_enrichment.standard_version IS
  'Version of the standard (e.g., "1.2", "v2.0")';

COMMENT ON COLUMN knowledge_enrichment.standard_key IS
  'Entity type or class in the standard (e.g., XTCE: "Parameter", "MetaCommand"; SysML: "Block", "Port")';

COMMENT ON COLUMN knowledge_enrichment.standard_name IS
  'Name of entity in standard namespace (e.g., "EPS_BattV", "RadioDriver")';

COMMENT ON COLUMN knowledge_enrichment.standard_constraints IS
  'JSONB containing standard-specific constraints like:
   - namespace: XTCE namespace path
   - container: XTCE container name
   - subsystem: SysML subsystem
   - stereotype: SysML stereotype
   - ontology_uri: OWL ontology URI
   Examples:
   {"namespace": "/PROVES/EPS", "container": "TelemetryContainer"}
   {"subsystem": "PowerSubsystem", "stereotype": "<<Hardware>>"}';


-- ============================================================================
-- PART 4: ADD CHECK CONSTRAINT
-- ============================================================================

-- Ensure standard mapping fields are populated when enrichment_type = 'standard_mapping'
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'check_standard_mapping_fields'
      AND conrelid = 'knowledge_enrichment'::regclass
  ) THEN
    ALTER TABLE knowledge_enrichment ADD CONSTRAINT
      check_standard_mapping_fields
      CHECK (
        enrichment_type != 'standard_mapping' OR (
          standard IS NOT NULL AND
          standard_key IS NOT NULL AND
          standard_name IS NOT NULL
        )
      );
  END IF;
END $$;

COMMENT ON CONSTRAINT check_standard_mapping_fields ON knowledge_enrichment IS
  'Ensures standard, standard_key, and standard_name are populated for standard_mapping enrichments';


-- ============================================================================
-- PART 5: ADD INDEXES
-- ============================================================================

-- Index for finding entities by standard
CREATE INDEX IF NOT EXISTS idx_knowledge_enrichment_standard
  ON knowledge_enrichment(standard, standard_key)
  WHERE enrichment_type = 'standard_mapping';

-- Index for reverse lookup (standard name -> PROVES entity)
CREATE INDEX IF NOT EXISTS idx_knowledge_enrichment_standard_name
  ON knowledge_enrichment(standard, standard_name)
  WHERE enrichment_type = 'standard_mapping';

-- GIN index for JSONB constraint queries
CREATE INDEX IF NOT EXISTS idx_knowledge_enrichment_standard_constraints
  ON knowledge_enrichment USING GIN (standard_constraints)
  WHERE enrichment_type = 'standard_mapping';


-- ============================================================================
-- PART 6: HELPER VIEWS
-- ============================================================================

-- View: XTCE mappings for YAMCS export
CREATE OR REPLACE VIEW xtce_mappings AS
SELECT
  ce.id AS entity_id,
  ce.canonical_key AS proves_key,
  ce.name AS proves_name,
  ce.entity_type,
  ce.ecosystem,
  ke.standard_key AS xtce_type,
  ke.standard_name AS xtce_name,
  ke.standard_version AS xtce_version,
  ke.standard_constraints->>'namespace' AS xtce_namespace,
  ke.standard_constraints->>'container' AS xtce_container,
  ke.standard_constraints->>'subsystem' AS subsystem,
  ke.enriched_at,
  ke.enriched_by
FROM knowledge_enrichment ke
JOIN core_entities ce ON ke.primary_entity_id = ce.id
WHERE ke.enrichment_type = 'standard_mapping'
  AND ke.standard = 'xtce'
  AND ce.is_current = TRUE
ORDER BY ke.standard_constraints->>'namespace', ke.standard_name;

COMMENT ON VIEW xtce_mappings IS
  'PROVES entities mapped to XTCE format for YAMCS mission control integration';


-- View: All standard mappings (generic)
CREATE OR REPLACE VIEW standard_mappings AS
SELECT
  ce.id AS entity_id,
  ce.canonical_key AS proves_key,
  ce.name AS proves_name,
  ce.entity_type,
  ce.ecosystem,
  ke.standard,
  ke.standard_version,
  ke.standard_key,
  ke.standard_name,
  ke.standard_constraints,
  ke.enriched_at,
  ke.enriched_by
FROM knowledge_enrichment ke
JOIN core_entities ce ON ke.primary_entity_id = ce.id
WHERE ke.enrichment_type = 'standard_mapping'
  AND ce.is_current = TRUE
ORDER BY ke.standard, ke.standard_key, ke.standard_name;

COMMENT ON VIEW standard_mappings IS
  'All PROVES entities with standard format mappings (XTCE, SysML, OWL, etc.)';


-- ============================================================================
-- PART 7: EXAMPLE USAGE DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE knowledge_enrichment IS
  'Enrichment data for core entities including aliases, duplicates, and standard mappings.

  Example standard_mapping records:

  1. XTCE/YAMCS Parameter mapping:
     enrichment_type = ''standard_mapping''
     standard = ''xtce''
     standard_version = ''1.2''
     standard_key = ''Parameter''
     standard_name = ''EPS_BattV''
     standard_constraints = {
       "namespace": "/PROVES/EPS",
       "container": "EPSTelemetryContainer",
       "subsystem": "PowerSubsystem"
     }

  2. SysML v2 Block mapping:
     enrichment_type = ''standard_mapping''
     standard = ''sysml_v2''
     standard_version = ''2.0''
     standard_key = ''Block''
     standard_name = ''RadioDriver''
     standard_constraints = {
       "subsystem": "CommunicationsSubsystem",
       "stereotype": "<<Software>>"
     }

  3. OWL Class mapping:
     enrichment_type = ''standard_mapping''
     standard = ''owl''
     standard_version = ''2.0''
     standard_key = ''Class''
     standard_name = ''RadioDriver''
     standard_constraints = {
       "ontology_uri": "http://proves.space/ontology",
       "namespace": "proves"
     }

  4. PyTorch Geometric node mapping:
     enrichment_type = ''standard_mapping''
     standard = ''pytorch_geometric''
     standard_version = ''2.5.0''
     standard_key = ''Node''
     standard_name = ''fprime_component_radiodriver''
     standard_constraints = {
       "node_type": "software_component",
       "graph_id": "fprime_v3.4.3"
     }';


-- ============================================================================
-- PART 8: HELPER FUNCTION
-- ============================================================================

-- Function to add standard mapping
CREATE OR REPLACE FUNCTION add_standard_mapping(
  p_entity_id UUID,
  p_standard TEXT,
  p_standard_version TEXT,
  p_standard_key TEXT,
  p_standard_name TEXT,
  p_standard_constraints JSONB DEFAULT NULL,
  p_enriched_by TEXT DEFAULT 'auto_mapper',
  p_enrichment_notes TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
  v_enrichment_id UUID;
BEGIN
  -- Validate entity exists and is current
  IF NOT EXISTS (
    SELECT 1 FROM core_entities
    WHERE id = p_entity_id AND is_current = TRUE
  ) THEN
    RAISE EXCEPTION 'Entity % not found or not current', p_entity_id;
  END IF;

  -- Check for duplicate mapping
  IF EXISTS (
    SELECT 1 FROM knowledge_enrichment
    WHERE primary_entity_id = p_entity_id
      AND enrichment_type = 'standard_mapping'
      AND standard = p_standard
      AND standard_key = p_standard_key
      AND standard_name = p_standard_name
  ) THEN
    RAISE EXCEPTION 'Standard mapping already exists for entity % to %.% (%)',
      p_entity_id, p_standard, p_standard_key, p_standard_name;
  END IF;

  -- Insert mapping
  INSERT INTO knowledge_enrichment (
    primary_entity_id,
    enrichment_type,
    standard,
    standard_version,
    standard_key,
    standard_name,
    standard_constraints,
    enriched_by,
    enrichment_notes
  ) VALUES (
    p_entity_id,
    'standard_mapping',
    p_standard,
    p_standard_version,
    p_standard_key,
    p_standard_name,
    p_standard_constraints,
    p_enriched_by,
    p_enrichment_notes
  ) RETURNING enrichment_id INTO v_enrichment_id;

  RETURN v_enrichment_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION add_standard_mapping IS
  'Add a standard mapping enrichment for a PROVES entity.

  Example usage:

  -- Map to XTCE Parameter
  SELECT add_standard_mapping(
    p_entity_id := ''123e4567-e89b-12d3-a456-426614174000'',
    p_standard := ''xtce'',
    p_standard_version := ''1.2'',
    p_standard_key := ''Parameter'',
    p_standard_name := ''EPS_BattV'',
    p_standard_constraints := ''{"namespace": "/PROVES/EPS", "container": "EPSTelemetryContainer"}'',
    p_enriched_by := ''xtce_exporter'',
    p_enrichment_notes := ''Mapped for YAMCS integration''
  );';


-- ============================================================================
-- PART 9: VALIDATION
-- ============================================================================

DO $$
BEGIN
  -- Verify columns exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'knowledge_enrichment' AND column_name = 'standard'
  ) THEN
    RAISE EXCEPTION 'Column standard was not added to knowledge_enrichment';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'knowledge_enrichment' AND column_name = 'standard_constraints'
  ) THEN
    RAISE EXCEPTION 'Column standard_constraints was not added to knowledge_enrichment';
  END IF;

  -- Verify views exist
  IF NOT EXISTS (
    SELECT 1 FROM pg_views WHERE viewname = 'xtce_mappings'
  ) THEN
    RAISE EXCEPTION 'View xtce_mappings was not created';
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_views WHERE viewname = 'standard_mappings'
  ) THEN
    RAISE EXCEPTION 'View standard_mappings was not created';
  END IF;

  -- Verify function exists
  IF NOT EXISTS (
    SELECT 1 FROM pg_proc WHERE proname = 'add_standard_mapping'
  ) THEN
    RAISE EXCEPTION 'Function add_standard_mapping was not created';
  END IF;

  RAISE NOTICE 'Migration 015 completed successfully ✓';
  RAISE NOTICE '  - Added standard_mapping enrichment type';
  RAISE NOTICE '  - Added standard, standard_version, standard_key, standard_name columns';
  RAISE NOTICE '  - Added standard_constraints JSONB column';
  RAISE NOTICE '  - Created xtce_mappings and standard_mappings views';
  RAISE NOTICE '  - Created add_standard_mapping() helper function';
  RAISE NOTICE '';
  RAISE NOTICE 'Supported standards: XTCE, SysML v2, OWL, GraphML, PyTorch Geometric';
END $$;

COMMIT;

-- ============================================================================
-- End of Migration 015
-- ============================================================================
