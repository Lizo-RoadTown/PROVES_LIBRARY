-- Migration: Add Dimensional Canonicalization Fields
-- Date: 2025-12-28
-- Purpose: Capture epistemic metadata (Contact, Directionality, Temporality, Formalizability, Carrier)
--          to preserve knowledge grounding as defined in Knowledge Canonicalization Theory

BEGIN;

-- ============================================================================
-- PART 1: KNOWLEDGE FORM AND DIMENSIONAL ATTRIBUTES
-- ============================================================================

-- 1.1: Add knowledge form (Embodied vs Inferred)
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  knowledge_form TEXT CHECK (knowledge_form IN ('embodied', 'inferred', 'unknown'));

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  knowledge_form_confidence NUMERIC(3,2) CHECK (
    knowledge_form_confidence IS NULL OR
    (knowledge_form_confidence >= 0 AND knowledge_form_confidence <= 1)
  );

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  knowledge_form_reasoning TEXT;

COMMENT ON COLUMN staging_extractions.knowledge_form IS
  'Whether knowledge originates through direct interaction (embodied) or symbolic reasoning (inferred)';

-- 1.2: Dimension 1 - Contact (Epistemic Anchoring)
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  contact_level TEXT CHECK (contact_level IN ('direct', 'mediated', 'indirect', 'derived', 'unknown'));

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  contact_confidence NUMERIC(3,2) CHECK (
    contact_confidence IS NULL OR
    (contact_confidence >= 0 AND contact_confidence <= 1)
  );

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  contact_reasoning TEXT;

COMMENT ON COLUMN staging_extractions.contact_level IS
  'How close knowledge is to direct interaction with reality: direct (physical), mediated (instrumented), indirect (effect-only), derived (model-only)';

-- 1.3: Dimension 2 - Directionality (Epistemic Operation)
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  directionality TEXT CHECK (directionality IN ('forward', 'backward', 'bidirectional', 'unknown'));

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  directionality_confidence NUMERIC(3,2) CHECK (
    directionality_confidence IS NULL OR
    (directionality_confidence >= 0 AND directionality_confidence <= 1)
  );

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  directionality_reasoning TEXT;

COMMENT ON COLUMN staging_extractions.directionality IS
  'Whether knowledge formed through forward inference (prediction) or backward inference (assessment from effects)';

-- 1.4: Dimension 3 - Temporality (Epistemic Dependence on History)
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  temporality TEXT CHECK (temporality IN ('snapshot', 'sequence', 'history', 'lifecycle', 'unknown'));

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  temporality_confidence NUMERIC(3,2) CHECK (
    temporality_confidence IS NULL OR
    (temporality_confidence >= 0 AND temporality_confidence <= 1)
  );

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  temporality_reasoning TEXT;

COMMENT ON COLUMN staging_extractions.temporality IS
  'Whether truth depends on time: snapshot (instant), sequence (order matters), history (accumulated past), lifecycle (long-term evolution)';

-- 1.5: Dimension 4 - Formalizability (Capacity for Symbolic Transformation)
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  formalizability TEXT CHECK (formalizability IN ('portable', 'conditional', 'local', 'tacit', 'unknown'));

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  formalizability_confidence NUMERIC(3,2) CHECK (
    formalizability_confidence IS NULL OR
    (formalizability_confidence >= 0 AND formalizability_confidence <= 1)
  );

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  formalizability_reasoning TEXT;

COMMENT ON COLUMN staging_extractions.formalizability IS
  'Degree to which knowledge can be symbolized: portable (full transfer), conditional (context-dependent), local (setting-specific), tacit (embodied only)';

-- 1.6: Carrier (What Holds the Knowledge)
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  carrier TEXT CHECK (carrier IN ('body', 'instrument', 'artifact', 'community', 'machine', 'unknown'));

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  carrier_confidence NUMERIC(3,2) CHECK (
    carrier_confidence IS NULL OR
    (carrier_confidence >= 0 AND carrier_confidence <= 1)
  );

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  carrier_reasoning TEXT;

COMMENT ON COLUMN staging_extractions.carrier IS
  'What carries the knowledge: body (person), instrument (sensor), artifact (document), community (organization), machine (AI/system)';

-- ============================================================================
-- PART 2: EXTRACTION QUALITY FLAGS
-- ============================================================================

-- 2.1: Human review flags (dimensional confidence thresholds)
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  needs_dimensional_review BOOLEAN DEFAULT FALSE;

ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  dimensional_review_reason TEXT;

COMMENT ON COLUMN staging_extractions.needs_dimensional_review IS
  'TRUE if any dimensional confidence score below threshold (e.g., < 0.7) or dimensional conflict detected';

-- 2.2: Dimensional completeness check
ALTER TABLE staging_extractions ADD COLUMN IF NOT EXISTS
  dimensional_completeness NUMERIC(3,2) CHECK (
    dimensional_completeness IS NULL OR
    (dimensional_completeness >= 0 AND dimensional_completeness <= 1)
  );

COMMENT ON COLUMN staging_extractions.dimensional_completeness IS
  'Fraction of dimensions successfully extracted (0.0 = none, 1.0 = all 5 dimensions with high confidence)';

-- ============================================================================
-- PART 3: EPISODIC ENTITY TRACKING (for Temporality dimension)
-- ============================================================================

-- 3.1: New table for episodes-as-entities (temporal events that cause degradation)
CREATE TABLE IF NOT EXISTS episodic_entities (
  episode_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Episode identification
  episode_type TEXT NOT NULL,  -- 'thermal_cycle', 'integration_phase', 'launch_sequence', 'deployment_event', etc.
  episode_name TEXT,           -- Human-readable name
  episode_key TEXT UNIQUE,     -- Canonical identifier

  -- Temporal properties
  start_time TIMESTAMPTZ,
  end_time TIMESTAMPTZ,
  duration_estimate TEXT,      -- "3 hours", "1 semester", "500 cycles"

  -- Relationships to components (JSONB for flexibility)
  affected_components JSONB,   -- Array of component IDs affected by this episode

  -- Evidence and source
  snapshot_id UUID REFERENCES raw_snapshots(id),
  evidence JSONB,
  confidence NUMERIC(3,2) CHECK (confidence >= 0 AND confidence <= 1),

  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  created_by_agent TEXT,
  ecosystem ecosystem_type,

  CONSTRAINT valid_time_range CHECK (start_time IS NULL OR end_time IS NULL OR start_time <= end_time)
);

CREATE INDEX idx_episodes_type ON episodic_entities(episode_type);
CREATE INDEX idx_episodes_key ON episodic_entities(episode_key);
CREATE INDEX idx_episodes_snapshot ON episodic_entities(snapshot_id);
CREATE INDEX idx_episodes_components ON episodic_entities USING GIN(affected_components);

COMMENT ON TABLE episodic_entities IS
  'Temporal events as first-class entities (e.g., thermal cycling episodes, integration phases) that enable causal reasoning about history-dependent degradation';

COMMENT ON COLUMN episodic_entities.episode_type IS
  'Type of temporal event: thermal_cycle, vibration_test, student_rotation, design_review, etc.';

COMMENT ON COLUMN episodic_entities.affected_components IS
  'JSONB array of component extraction IDs affected by this episode, enabling GNN to reason about cumulative effects';

-- 3.2: Linking table for episodes → extractions
CREATE TABLE IF NOT EXISTS episode_extraction_links (
  link_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  episode_id UUID REFERENCES episodic_entities(episode_id) ON DELETE CASCADE,
  extraction_id UUID REFERENCES staging_extractions(extraction_id) ON DELETE CASCADE,

  link_type TEXT,  -- 'caused_by', 'observed_during', 'affects', 'describes'
  confidence NUMERIC(3,2) CHECK (confidence >= 0 AND confidence <= 1),

  created_at TIMESTAMPTZ DEFAULT NOW(),

  CONSTRAINT unique_episode_extraction UNIQUE(episode_id, extraction_id, link_type)
);

CREATE INDEX idx_episode_links_episode ON episode_extraction_links(episode_id);
CREATE INDEX idx_episode_links_extraction ON episode_extraction_links(extraction_id);

COMMENT ON TABLE episode_extraction_links IS
  'Links episodic entities to knowledge extractions, enabling temporal causality tracking';

-- ============================================================================
-- PART 4: INDEXES FOR DIMENSIONAL QUERIES
-- ============================================================================

-- Composite indexes for dimensional analysis
CREATE INDEX IF NOT EXISTS idx_extractions_dimensional_profile
  ON staging_extractions(knowledge_form, contact_level, directionality, temporality, formalizability);

CREATE INDEX IF NOT EXISTS idx_extractions_needs_dimensional_review
  ON staging_extractions(needs_dimensional_review)
  WHERE needs_dimensional_review = TRUE;

CREATE INDEX IF NOT EXISTS idx_extractions_embodied_knowledge
  ON staging_extractions(knowledge_form, carrier)
  WHERE knowledge_form = 'embodied';

CREATE INDEX IF NOT EXISTS idx_extractions_low_formalizability
  ON staging_extractions(formalizability, formalizability_confidence)
  WHERE formalizability IN ('tacit', 'local');

-- ============================================================================
-- PART 5: FUNCTIONS FOR DIMENSIONAL QUALITY CHECKS
-- ============================================================================

-- Function: Calculate dimensional completeness score
CREATE OR REPLACE FUNCTION calculate_dimensional_completeness(
  p_knowledge_form_conf NUMERIC,
  p_contact_conf NUMERIC,
  p_directionality_conf NUMERIC,
  p_temporality_conf NUMERIC,
  p_formalizability_conf NUMERIC,
  p_carrier_conf NUMERIC
) RETURNS NUMERIC AS $$
DECLARE
  total_dimensions INTEGER := 6;
  completed_dimensions INTEGER := 0;
  confidence_threshold NUMERIC := 0.7;
BEGIN
  -- Count dimensions with confidence >= threshold
  IF p_knowledge_form_conf >= confidence_threshold THEN completed_dimensions := completed_dimensions + 1; END IF;
  IF p_contact_conf >= confidence_threshold THEN completed_dimensions := completed_dimensions + 1; END IF;
  IF p_directionality_conf >= confidence_threshold THEN completed_dimensions := completed_dimensions + 1; END IF;
  IF p_temporality_conf >= confidence_threshold THEN completed_dimensions := completed_dimensions + 1; END IF;
  IF p_formalizability_conf >= confidence_threshold THEN completed_dimensions := completed_dimensions + 1; END IF;
  IF p_carrier_conf >= confidence_threshold THEN completed_dimensions := completed_dimensions + 1; END IF;

  RETURN ROUND(completed_dimensions::NUMERIC / total_dimensions, 2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_dimensional_completeness IS
  'Calculates fraction of dimensions extracted with confidence >= 0.7';

-- Function: Auto-flag extractions needing dimensional review
CREATE OR REPLACE FUNCTION check_dimensional_review_needed()
RETURNS TRIGGER AS $$
DECLARE
  confidence_threshold NUMERIC := 0.7;
  reasons TEXT[] := ARRAY[]::TEXT[];
BEGIN
  -- Check for low-confidence dimensions
  IF NEW.knowledge_form_confidence < confidence_threshold THEN
    reasons := array_append(reasons, format('Low knowledge_form confidence (%.2f)', NEW.knowledge_form_confidence));
  END IF;

  IF NEW.contact_confidence < confidence_threshold THEN
    reasons := array_append(reasons, format('Low contact confidence (%.2f)', NEW.contact_confidence));
  END IF;

  IF NEW.directionality_confidence < confidence_threshold THEN
    reasons := array_append(reasons, format('Low directionality confidence (%.2f)', NEW.directionality_confidence));
  END IF;

  IF NEW.temporality_confidence < confidence_threshold THEN
    reasons := array_append(reasons, format('Low temporality confidence (%.2f)', NEW.temporality_confidence));
  END IF;

  IF NEW.formalizability_confidence < confidence_threshold THEN
    reasons := array_append(reasons, format('Low formalizability confidence (%.2f)', NEW.formalizability_confidence));
  END IF;

  IF NEW.carrier_confidence < confidence_threshold THEN
    reasons := array_append(reasons, format('Low carrier confidence (%.2f)', NEW.carrier_confidence));
  END IF;

  -- Check for dimensional conflicts (e.g., derived contact but embodied knowledge)
  IF NEW.knowledge_form = 'embodied' AND NEW.contact_level = 'derived' THEN
    reasons := array_append(reasons, 'Conflict: embodied knowledge cannot have derived contact');
  END IF;

  IF NEW.formalizability = 'tacit' AND NEW.knowledge_form = 'inferred' THEN
    reasons := array_append(reasons, 'Conflict: inferred knowledge should not be tacit');
  END IF;

  -- Calculate completeness
  NEW.dimensional_completeness := calculate_dimensional_completeness(
    COALESCE(NEW.knowledge_form_confidence, 0),
    COALESCE(NEW.contact_confidence, 0),
    COALESCE(NEW.directionality_confidence, 0),
    COALESCE(NEW.temporality_confidence, 0),
    COALESCE(NEW.formalizability_confidence, 0),
    COALESCE(NEW.carrier_confidence, 0)
  );

  -- Set review flag if issues found
  IF array_length(reasons, 1) > 0 THEN
    NEW.needs_dimensional_review := TRUE;
    NEW.dimensional_review_reason := array_to_string(reasons, '; ');
  ELSE
    NEW.needs_dimensional_review := FALSE;
    NEW.dimensional_review_reason := NULL;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-check dimensional quality on insert/update
DROP TRIGGER IF EXISTS trigger_check_dimensional_review ON staging_extractions;
CREATE TRIGGER trigger_check_dimensional_review
  BEFORE INSERT OR UPDATE ON staging_extractions
  FOR EACH ROW
  EXECUTE FUNCTION check_dimensional_review_needed();

COMMENT ON FUNCTION check_dimensional_review_needed IS
  'Auto-flags extractions with low dimensional confidence or logical conflicts for human review';

-- ============================================================================
-- PART 6: VIEWS FOR DIMENSIONAL ANALYSIS
-- ============================================================================

-- View: Dimensional quality dashboard
CREATE OR REPLACE VIEW dimensional_quality_dashboard AS
SELECT
  COUNT(*) as total_extractions,

  -- Overall dimensional completeness
  AVG(dimensional_completeness) as avg_completeness,

  -- Extractions needing review
  SUM(CASE WHEN needs_dimensional_review THEN 1 ELSE 0 END) as needs_review_count,

  -- Knowledge form distribution
  SUM(CASE WHEN knowledge_form = 'embodied' THEN 1 ELSE 0 END) as embodied_count,
  SUM(CASE WHEN knowledge_form = 'inferred' THEN 1 ELSE 0 END) as inferred_count,
  SUM(CASE WHEN knowledge_form = 'unknown' THEN 1 ELSE 0 END) as unknown_form_count,

  -- Contact level distribution
  SUM(CASE WHEN contact_level = 'direct' THEN 1 ELSE 0 END) as direct_contact_count,
  SUM(CASE WHEN contact_level = 'mediated' THEN 1 ELSE 0 END) as mediated_contact_count,
  SUM(CASE WHEN contact_level = 'indirect' THEN 1 ELSE 0 END) as indirect_contact_count,
  SUM(CASE WHEN contact_level = 'derived' THEN 1 ELSE 0 END) as derived_contact_count,

  -- Average confidence scores
  AVG(knowledge_form_confidence) as avg_knowledge_form_conf,
  AVG(contact_confidence) as avg_contact_conf,
  AVG(directionality_confidence) as avg_directionality_conf,
  AVG(temporality_confidence) as avg_temporality_conf,
  AVG(formalizability_confidence) as avg_formalizability_conf,
  AVG(carrier_confidence) as avg_carrier_conf

FROM staging_extractions;

COMMENT ON VIEW dimensional_quality_dashboard IS
  'Overview of dimensional extraction quality across all extractions';

-- View: High-value embodied knowledge at risk
CREATE OR REPLACE VIEW embodied_knowledge_at_risk AS
SELECT
  extraction_id,
  candidate_key,
  candidate_type,
  knowledge_form,
  contact_level,
  formalizability,
  carrier,
  formalizability_confidence,
  dimensional_completeness,
  created_at,
  snapshot_id
FROM staging_extractions
WHERE knowledge_form = 'embodied'
  AND formalizability IN ('tacit', 'local')
  AND contact_level IN ('direct', 'mediated')
ORDER BY formalizability_confidence DESC, created_at DESC;

COMMENT ON VIEW embodied_knowledge_at_risk IS
  'Embodied knowledge with low formalizability (tacit/local) at risk of loss during organizational transitions';

-- View: Episodic temporal knowledge
CREATE OR REPLACE VIEW episodic_temporal_knowledge AS
SELECT
  se.extraction_id,
  se.candidate_key,
  se.temporality,
  se.temporality_confidence,
  ee.episode_id,
  ee.episode_type,
  ee.episode_name,
  ee.duration_estimate,
  eel.link_type,
  se.created_at
FROM staging_extractions se
LEFT JOIN episode_extraction_links eel ON se.extraction_id = eel.extraction_id
LEFT JOIN episodic_entities ee ON eel.episode_id = ee.episode_id
WHERE se.temporality IN ('history', 'lifecycle')
ORDER BY se.temporality_confidence DESC;

COMMENT ON VIEW episodic_temporal_knowledge IS
  'Knowledge with history/lifecycle temporality and associated episodic entities for causal reasoning';

-- ============================================================================
-- PART 7: DATA VALIDATION
-- ============================================================================

DO $$
DECLARE
  missing_columns TEXT[];
BEGIN
  -- Check dimensional columns exist
  SELECT ARRAY_AGG(col)
  INTO missing_columns
  FROM (VALUES
    ('knowledge_form'),
    ('contact_level'),
    ('contact_confidence'),
    ('directionality'),
    ('temporality'),
    ('formalizability'),
    ('carrier'),
    ('dimensional_completeness')
  ) AS expected(col)
  WHERE NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'staging_extractions'
      AND column_name = expected.col
  );

  IF array_length(missing_columns, 1) > 0 THEN
    RAISE EXCEPTION 'Missing dimensional columns: %', array_to_string(missing_columns, ', ');
  END IF;

  -- Check episodic entities table exists
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'episodic_entities') THEN
    RAISE EXCEPTION 'Table episodic_entities was not created';
  END IF;

  RAISE NOTICE 'Dimensional canonicalization migration completed successfully ✓';
END $$;

COMMIT;

-- ============================================================================
-- POST-MIGRATION VERIFICATION QUERIES
-- ============================================================================

-- 1. Check dimensional columns
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'staging_extractions'
--   AND column_name LIKE '%contact%' OR column_name LIKE '%directionality%'
--   OR column_name LIKE '%temporality%' OR column_name LIKE '%formalizability%';

-- 2. Check dimensional quality dashboard
-- SELECT * FROM dimensional_quality_dashboard;

-- 3. Test dimensional review trigger
-- INSERT INTO staging_extractions (candidate_key, contact_level, contact_confidence)
-- VALUES ('TestEntity', 'direct', 0.5);  -- Should trigger review flag (low confidence)

-- 4. Check episodic entities table
-- SELECT table_name, (SELECT COUNT(*) FROM episodic_entities) as episode_count
-- FROM information_schema.tables
-- WHERE table_name = 'episodic_entities';
