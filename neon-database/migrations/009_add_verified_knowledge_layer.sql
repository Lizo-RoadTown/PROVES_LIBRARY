-- ============================================================================
-- Migration 009: Verified Knowledge Layer
-- ============================================================================
-- After staging_extractions approval, knowledge is promoted to core_entities
-- with human verification, dimensional adjustments, enrichment, and relationships
-- ============================================================================

-- 1. Add dimensional metadata and verification fields to core_entities
-- ============================================================================

-- 1.1: Add verified dimensional metadata (human-confirmed values)
ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  knowledge_form TEXT CHECK (knowledge_form IN ('embodied', 'inferred', 'unknown'));

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  knowledge_form_confidence NUMERIC(3,2) CHECK (
    knowledge_form_confidence IS NULL OR
    (knowledge_form_confidence >= 0 AND knowledge_form_confidence <= 1)
  );

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  knowledge_form_reasoning TEXT;

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  contact_level TEXT CHECK (contact_level IN ('direct', 'mediated', 'indirect', 'derived', 'unknown'));

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  contact_confidence NUMERIC(3,2);

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  contact_reasoning TEXT;

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  directionality TEXT CHECK (directionality IN ('forward', 'backward', 'bidirectional', 'unknown'));

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  directionality_confidence NUMERIC(3,2);

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  directionality_reasoning TEXT;

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  temporality TEXT CHECK (temporality IN ('snapshot', 'sequence', 'history', 'lifecycle', 'unknown'));

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  temporality_confidence NUMERIC(3,2);

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  temporality_reasoning TEXT;

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  formalizability TEXT CHECK (formalizability IN ('portable', 'conditional', 'local', 'tacit', 'unknown'));

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  formalizability_confidence NUMERIC(3,2);

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  formalizability_reasoning TEXT;

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  carrier TEXT CHECK (carrier IN ('body', 'instrument', 'artifact', 'community', 'machine', 'unknown'));

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  carrier_confidence NUMERIC(3,2);

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  carrier_reasoning TEXT;

-- 1.2: Add verification tracking
ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  verification_status TEXT DEFAULT 'pending' CHECK (
    verification_status IN ('pending', 'human_verified', 'auto_approved', 'needs_review')
  );

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  verified_by TEXT;  -- User ID or webhook identifier

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  verified_at TIMESTAMPTZ;

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  epistemic_notes TEXT;  -- Human notes about knowledge quality/context

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  notion_page_id TEXT;  -- For Notion webhook integration

ALTER TABLE core_entities ADD COLUMN IF NOT EXISTS
  approval_source TEXT CHECK (
    approval_source IN ('notion_webhook', 'manual_review', 'auto_promotion')
  );

-- Create index for verification queries
CREATE INDEX IF NOT EXISTS idx_core_entities_verification_status
  ON core_entities(verification_status);

CREATE INDEX IF NOT EXISTS idx_core_entities_verified_at
  ON core_entities(verified_at);

CREATE INDEX IF NOT EXISTS idx_core_entities_notion_page
  ON core_entities(notion_page_id) WHERE notion_page_id IS NOT NULL;


-- ============================================================================
-- 2. Dimensional Adjustment History Table
-- ============================================================================
-- Tracks when humans adjust dimensional metadata during verification
-- Maintains full audit trail of epistemic reasoning evolution

CREATE TABLE IF NOT EXISTS dimensional_adjustment_history (
  adjustment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- What was adjusted
  entity_id UUID NOT NULL REFERENCES core_entities(id) ON DELETE CASCADE,
  dimension_name TEXT NOT NULL CHECK (
    dimension_name IN ('knowledge_form', 'contact', 'directionality', 'temporality', 'formalizability', 'carrier')
  ),

  -- Before adjustment (from staging_extractions)
  old_value TEXT,
  old_confidence NUMERIC(3,2),
  old_reasoning TEXT,

  -- After adjustment (human-corrected)
  new_value TEXT,
  new_confidence NUMERIC(3,2),
  new_reasoning TEXT,

  -- Who and why
  adjusted_by TEXT NOT NULL,  -- User ID
  adjustment_reason TEXT NOT NULL CHECK (
    adjustment_reason IN (
      'human_correction',        -- Human disagreed with agent inference
      'context_addition',        -- Human added missing context
      'confidence_calibration',  -- Adjusted confidence based on domain knowledge
      'epistemic_clarification', -- Clarified ambiguous epistemic status
      'source_verification'      -- Verified against primary sources
    )
  ),
  adjustment_notes TEXT,  -- Freeform explanation

  -- When
  adjusted_at TIMESTAMPTZ DEFAULT NOW(),

  -- Source of original inference
  source_extraction_id UUID REFERENCES staging_extractions(extraction_id),

  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dimensional_adjustments_entity
  ON dimensional_adjustment_history(entity_id);

CREATE INDEX IF NOT EXISTS idx_dimensional_adjustments_dimension
  ON dimensional_adjustment_history(dimension_name);

CREATE INDEX IF NOT EXISTS idx_dimensional_adjustments_adjusted_at
  ON dimensional_adjustment_history(adjusted_at);

-- View: Recent dimensional corrections (for learning)
CREATE OR REPLACE VIEW recent_dimensional_corrections AS
SELECT
  dah.adjustment_id,
  dah.entity_id,
  ce.canonical_key,
  ce.name,
  dah.dimension_name,
  dah.old_value,
  dah.old_confidence,
  dah.new_value,
  dah.new_confidence,
  dah.adjustment_reason,
  dah.adjustment_notes,
  dah.adjusted_by,
  dah.adjusted_at
FROM dimensional_adjustment_history dah
JOIN core_entities ce ON dah.entity_id = ce.id
WHERE dah.adjusted_at > NOW() - INTERVAL '30 days'
ORDER BY dah.adjusted_at DESC;


-- ============================================================================
-- 3. Knowledge Enrichment Table
-- ============================================================================
-- Handles aliases, duplicates, merged knowledge from multiple sources

CREATE TABLE IF NOT EXISTS knowledge_enrichment (
  enrichment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Primary entity (the canonical knowledge node)
  primary_entity_id UUID NOT NULL REFERENCES core_entities(id) ON DELETE CASCADE,

  -- Enrichment type
  enrichment_type TEXT NOT NULL CHECK (
    enrichment_type IN (
      'alias',              -- Alternative name for same entity
      'duplicate_merge',    -- Merged from duplicate extraction
      'cross_source',       -- Same knowledge from different sources
      'temporal_update',    -- Updated knowledge over time
      'epistemic_refinement' -- Refined understanding from additional evidence
    )
  ),

  -- Source of enrichment
  source_entity_id UUID REFERENCES core_entities(id) ON DELETE SET NULL,  -- If merged from another entity
  source_extraction_id UUID REFERENCES staging_extractions(extraction_id),

  -- Enrichment data
  alias_name TEXT,  -- If enrichment_type = 'alias'
  merged_attributes JSONB,  -- Additional attributes from merged entity
  conflict_resolution JSONB,  -- How conflicts were resolved
  confidence_boost NUMERIC(3,2),  -- Confidence increase from corroboration

  -- Provenance
  enriched_by TEXT NOT NULL,  -- User ID or 'auto_enrichment_agent'
  enriched_at TIMESTAMPTZ DEFAULT NOW(),
  enrichment_notes TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_enrichment_primary
  ON knowledge_enrichment(primary_entity_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_enrichment_type
  ON knowledge_enrichment(enrichment_type);

CREATE INDEX IF NOT EXISTS idx_knowledge_enrichment_source
  ON knowledge_enrichment(source_entity_id) WHERE source_entity_id IS NOT NULL;

-- View: Entity aliases (for search/disambiguation)
CREATE OR REPLACE VIEW entity_aliases AS
SELECT
  ke.primary_entity_id,
  ce.canonical_key AS primary_key,
  ce.name AS primary_name,
  ke.alias_name,
  ke.enriched_at,
  ke.enriched_by
FROM knowledge_enrichment ke
JOIN core_entities ce ON ke.primary_entity_id = ce.id
WHERE ke.enrichment_type = 'alias'
  AND ce.is_current = TRUE;


-- ============================================================================
-- 4. Episode-Knowledge Relationships
-- ============================================================================
-- Links verified knowledge to episodic entities (temporal context)

CREATE TABLE IF NOT EXISTS knowledge_episode_relationships (
  relationship_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- What and when
  knowledge_entity_id UUID NOT NULL REFERENCES core_entities(id) ON DELETE CASCADE,
  episode_id UUID NOT NULL REFERENCES episodic_entities(episode_id) ON DELETE CASCADE,

  -- Relationship type
  relationship_type TEXT NOT NULL CHECK (
    relationship_type IN (
      'observed_during',     -- Knowledge observed during this episode
      'caused_by',           -- Episode caused this knowledge to emerge
      'affects',             -- Knowledge affects this episode
      'validates',           -- Knowledge validates episode hypothesis
      'contradicts'          -- Knowledge contradicts episode expectation
    )
  ),

  -- Strength and confidence
  relationship_strength NUMERIC(3,2) CHECK (
    relationship_strength >= 0 AND relationship_strength <= 1
  ),
  confidence NUMERIC(3,2) CHECK (
    confidence >= 0 AND confidence <= 1
  ),

  -- Evidence
  evidence_extraction_id UUID REFERENCES staging_extractions(extraction_id),
  evidence_text TEXT,

  -- Provenance
  created_by TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(knowledge_entity_id, episode_id, relationship_type)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_episode_knowledge
  ON knowledge_episode_relationships(knowledge_entity_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_episode_episode
  ON knowledge_episode_relationships(episode_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_episode_type
  ON knowledge_episode_relationships(relationship_type);


-- ============================================================================
-- 5. Component-Knowledge Relationships
-- ============================================================================
-- Links verified knowledge to hardware/software components

CREATE TABLE IF NOT EXISTS knowledge_component_relationships (
  relationship_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- What describes what
  knowledge_entity_id UUID NOT NULL REFERENCES core_entities(id) ON DELETE CASCADE,
  component_entity_id UUID NOT NULL REFERENCES core_entities(id) ON DELETE CASCADE,

  -- Relationship type
  relationship_type TEXT NOT NULL CHECK (
    relationship_type IN (
      'describes_component',      -- Knowledge describes this component
      'describes_behavior',       -- Knowledge describes component behavior
      'describes_failure_mode',   -- Knowledge describes how component fails
      'describes_interface',      -- Knowledge describes component interface
      'describes_constraint',     -- Knowledge describes component constraint
      'describes_performance'     -- Knowledge describes component performance
    )
  ),

  -- Specificity
  aspect TEXT,  -- What aspect of component (e.g., "bearing", "thermal behavior", "I2C interface")

  -- Strength and confidence
  relationship_strength NUMERIC(3,2) CHECK (
    relationship_strength >= 0 AND relationship_strength <= 1
  ),
  confidence NUMERIC(3,2) CHECK (
    confidence >= 0 AND confidence <= 1
  ),

  -- Evidence
  evidence_extraction_id UUID REFERENCES staging_extractions(extraction_id),
  evidence_text TEXT,

  -- Provenance
  created_by TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(knowledge_entity_id, component_entity_id, relationship_type, aspect)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_component_knowledge
  ON knowledge_component_relationships(knowledge_entity_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_component_component
  ON knowledge_component_relationships(component_entity_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_component_type
  ON knowledge_component_relationships(relationship_type);

-- View: Component knowledge map
CREATE OR REPLACE VIEW component_knowledge_map AS
SELECT
  comp.id AS component_id,
  comp.canonical_key AS component_key,
  comp.name AS component_name,
  kc.relationship_type,
  kc.aspect,
  know.id AS knowledge_id,
  know.canonical_key AS knowledge_key,
  know.name AS knowledge_name,
  know.knowledge_form,
  know.contact_level,
  know.formalizability,
  know.verification_status,
  kc.confidence,
  kc.created_at
FROM knowledge_component_relationships kc
JOIN core_entities comp ON kc.component_entity_id = comp.id
JOIN core_entities know ON kc.knowledge_entity_id = know.id
WHERE comp.is_current = TRUE
  AND know.is_current = TRUE
  AND know.verification_status = 'human_verified';


-- ============================================================================
-- 6. Helper Functions
-- ============================================================================

-- Function: Promote staging extraction to verified knowledge
CREATE OR REPLACE FUNCTION promote_to_verified_knowledge(
  p_extraction_id UUID,
  p_verified_by TEXT,
  p_approval_source TEXT DEFAULT 'manual_review',
  p_notion_page_id TEXT DEFAULT NULL,
  p_epistemic_notes TEXT DEFAULT NULL,
  p_dimensional_adjustments JSONB DEFAULT NULL  -- { "contact": {"value": "direct", "confidence": 0.95, "reasoning": "..."}, ... }
) RETURNS UUID AS $$
DECLARE
  v_entity_id UUID;
  v_extraction_record RECORD;
  v_dimension TEXT;
  v_adjustment JSONB;
BEGIN
  -- Get staging extraction
  SELECT * INTO v_extraction_record
  FROM staging_extractions
  WHERE extraction_id = p_extraction_id;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Extraction % not found', p_extraction_id;
  END IF;

  -- Create core entity with verified dimensional metadata
  INSERT INTO core_entities (
    entity_type, canonical_key, name, display_name,
    ecosystem, attributes, source_snapshot_id,
    -- Dimensional metadata (use adjustments if provided, otherwise copy from staging)
    knowledge_form, knowledge_form_confidence, knowledge_form_reasoning,
    contact_level, contact_confidence, contact_reasoning,
    directionality, directionality_confidence, directionality_reasoning,
    temporality, temporality_confidence, temporality_reasoning,
    formalizability, formalizability_confidence, formalizability_reasoning,
    carrier, carrier_confidence, carrier_reasoning,
    -- Verification metadata
    verification_status, verified_by, verified_at,
    approval_source, notion_page_id, epistemic_notes
  ) VALUES (
    v_extraction_record.candidate_type::entity_type,
    v_extraction_record.candidate_key,
    v_extraction_record.candidate_key,
    v_extraction_record.candidate_key,
    v_extraction_record.ecosystem,
    v_extraction_record.candidate_payload,
    v_extraction_record.snapshot_id,
    -- Apply adjustments or copy from staging
    COALESCE((p_dimensional_adjustments->>'knowledge_form')::TEXT, v_extraction_record.knowledge_form),
    COALESCE((p_dimensional_adjustments->'knowledge_form'->>'confidence')::NUMERIC, v_extraction_record.knowledge_form_confidence),
    COALESCE((p_dimensional_adjustments->'knowledge_form'->>'reasoning')::TEXT, v_extraction_record.knowledge_form_reasoning),
    COALESCE((p_dimensional_adjustments->>'contact')::TEXT, v_extraction_record.contact_level),
    COALESCE((p_dimensional_adjustments->'contact'->>'confidence')::NUMERIC, v_extraction_record.contact_confidence),
    COALESCE((p_dimensional_adjustments->'contact'->>'reasoning')::TEXT, v_extraction_record.contact_reasoning),
    COALESCE((p_dimensional_adjustments->>'directionality')::TEXT, v_extraction_record.directionality),
    COALESCE((p_dimensional_adjustments->'directionality'->>'confidence')::NUMERIC, v_extraction_record.directionality_confidence),
    COALESCE((p_dimensional_adjustments->'directionality'->>'reasoning')::TEXT, v_extraction_record.directionality_reasoning),
    COALESCE((p_dimensional_adjustments->>'temporality')::TEXT, v_extraction_record.temporality),
    COALESCE((p_dimensional_adjustments->'temporality'->>'confidence')::NUMERIC, v_extraction_record.temporality_confidence),
    COALESCE((p_dimensional_adjustments->'temporality'->>'reasoning')::TEXT, v_extraction_record.temporality_reasoning),
    COALESCE((p_dimensional_adjustments->>'formalizability')::TEXT, v_extraction_record.formalizability),
    COALESCE((p_dimensional_adjustments->'formalizability'->>'confidence')::NUMERIC, v_extraction_record.formalizability_confidence),
    COALESCE((p_dimensional_adjustments->'formalizability'->>'reasoning')::TEXT, v_extraction_record.formalizability_reasoning),
    COALESCE((p_dimensional_adjustments->>'carrier')::TEXT, v_extraction_record.carrier),
    COALESCE((p_dimensional_adjustments->'carrier'->>'confidence')::NUMERIC, v_extraction_record.carrier_confidence),
    COALESCE((p_dimensional_adjustments->'carrier'->>'reasoning')::TEXT, v_extraction_record.carrier_reasoning),
    'human_verified',
    p_verified_by,
    NOW(),
    p_approval_source,
    p_notion_page_id,
    p_epistemic_notes
  ) RETURNING id INTO v_entity_id;

  -- Record dimensional adjustments if any
  IF p_dimensional_adjustments IS NOT NULL THEN
    FOR v_dimension IN SELECT jsonb_object_keys(p_dimensional_adjustments)
    LOOP
      v_adjustment := p_dimensional_adjustments->v_dimension;

      -- Only record if value actually changed
      IF (v_adjustment->>'value') IS DISTINCT FROM
         (CASE v_dimension
           WHEN 'knowledge_form' THEN v_extraction_record.knowledge_form
           WHEN 'contact' THEN v_extraction_record.contact_level
           WHEN 'directionality' THEN v_extraction_record.directionality
           WHEN 'temporality' THEN v_extraction_record.temporality
           WHEN 'formalizability' THEN v_extraction_record.formalizability
           WHEN 'carrier' THEN v_extraction_record.carrier
         END) THEN

        INSERT INTO dimensional_adjustment_history (
          entity_id, dimension_name,
          old_value, old_confidence, old_reasoning,
          new_value, new_confidence, new_reasoning,
          adjusted_by, adjustment_reason, adjustment_notes,
          source_extraction_id
        ) VALUES (
          v_entity_id,
          v_dimension,
          CASE v_dimension
            WHEN 'knowledge_form' THEN v_extraction_record.knowledge_form
            WHEN 'contact' THEN v_extraction_record.contact_level
            WHEN 'directionality' THEN v_extraction_record.directionality
            WHEN 'temporality' THEN v_extraction_record.temporality
            WHEN 'formalizability' THEN v_extraction_record.formalizability
            WHEN 'carrier' THEN v_extraction_record.carrier
          END,
          CASE v_dimension
            WHEN 'knowledge_form' THEN v_extraction_record.knowledge_form_confidence
            WHEN 'contact' THEN v_extraction_record.contact_confidence
            WHEN 'directionality' THEN v_extraction_record.directionality_confidence
            WHEN 'temporality' THEN v_extraction_record.temporality_confidence
            WHEN 'formalizability' THEN v_extraction_record.formalizability_confidence
            WHEN 'carrier' THEN v_extraction_record.carrier_confidence
          END,
          CASE v_dimension
            WHEN 'knowledge_form' THEN v_extraction_record.knowledge_form_reasoning
            WHEN 'contact' THEN v_extraction_record.contact_reasoning
            WHEN 'directionality' THEN v_extraction_record.directionality_reasoning
            WHEN 'temporality' THEN v_extraction_record.temporality_reasoning
            WHEN 'formalizability' THEN v_extraction_record.formalizability_reasoning
            WHEN 'carrier' THEN v_extraction_record.carrier_reasoning
          END,
          (v_adjustment->>'value')::TEXT,
          (v_adjustment->>'confidence')::NUMERIC,
          (v_adjustment->>'reasoning')::TEXT,
          p_verified_by,
          COALESCE((v_adjustment->>'adjustment_reason')::TEXT, 'human_correction'),
          (v_adjustment->>'notes')::TEXT,
          p_extraction_id
        );
      END IF;
    END LOOP;
  END IF;

  -- Mark staging extraction as accepted
  UPDATE staging_extractions
  SET status = 'accepted'::candidate_status,
      reviewed_at = NOW(),
      reviewed_by = p_verified_by
  WHERE extraction_id = p_extraction_id;

  RETURN v_entity_id;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 7. Analysis Views
-- ============================================================================

-- View: Verification quality dashboard
CREATE OR REPLACE VIEW verification_quality_dashboard AS
SELECT
  COUNT(*) FILTER (WHERE verification_status = 'human_verified') AS human_verified_count,
  COUNT(*) FILTER (WHERE verification_status = 'auto_approved') AS auto_approved_count,
  COUNT(*) FILTER (WHERE verification_status = 'pending') AS pending_count,
  COUNT(*) FILTER (WHERE verification_status = 'needs_review') AS needs_review_count,

  -- Dimensional quality of verified knowledge
  AVG(contact_confidence) FILTER (WHERE verification_status = 'human_verified') AS avg_contact_confidence,
  AVG(directionality_confidence) FILTER (WHERE verification_status = 'human_verified') AS avg_directionality_confidence,
  AVG(temporality_confidence) FILTER (WHERE verification_status = 'human_verified') AS avg_temporality_confidence,
  AVG(formalizability_confidence) FILTER (WHERE verification_status = 'human_verified') AS avg_formalizability_confidence,

  -- Verification velocity
  COUNT(*) FILTER (WHERE verified_at > NOW() - INTERVAL '7 days') AS verified_last_7_days,
  COUNT(*) FILTER (WHERE verified_at > NOW() - INTERVAL '30 days') AS verified_last_30_days,

  -- Human adjustment rate
  (SELECT COUNT(*) FROM dimensional_adjustment_history WHERE adjusted_at > NOW() - INTERVAL '30 days') AS adjustments_last_30_days
FROM core_entities
WHERE is_current = TRUE;


-- View: Epistemic risk assessment
CREATE OR REPLACE VIEW epistemic_risk_assessment AS
SELECT
  ce.id,
  ce.canonical_key,
  ce.name,
  ce.knowledge_form,
  ce.contact_level,
  ce.formalizability,
  ce.verification_status,
  ce.verified_by,
  ce.verified_at,

  -- Risk flags
  CASE
    WHEN ce.knowledge_form = 'embodied' AND ce.formalizability IN ('tacit', 'local') THEN 'high_loss_risk'
    WHEN ce.contact_level IN ('indirect', 'derived') AND ce.directionality = 'backward' THEN 'inference_cascade_risk'
    WHEN ce.temporality IN ('history', 'lifecycle') AND NOT EXISTS (
      SELECT 1 FROM knowledge_episode_relationships ker WHERE ker.knowledge_entity_id = ce.id
    ) THEN 'temporal_context_missing'
    ELSE 'low_risk'
  END AS epistemic_risk_category,

  -- Verification quality
  (ce.contact_confidence + ce.directionality_confidence +
   ce.temporality_confidence + ce.formalizability_confidence) / 4.0 AS avg_dimensional_confidence,

  -- Enrichment status
  (SELECT COUNT(*) FROM knowledge_enrichment ke WHERE ke.primary_entity_id = ce.id) AS enrichment_count,

  -- Episode grounding
  (SELECT COUNT(*) FROM knowledge_episode_relationships ker WHERE ker.knowledge_entity_id = ce.id) AS episode_link_count,

  -- Component grounding
  (SELECT COUNT(*) FROM knowledge_component_relationships kcr WHERE kcr.knowledge_entity_id = ce.id) AS component_link_count

FROM core_entities ce
WHERE ce.is_current = TRUE
  AND ce.verification_status = 'human_verified'
ORDER BY
  CASE
    WHEN ce.knowledge_form = 'embodied' AND ce.formalizability IN ('tacit', 'local') THEN 1
    WHEN ce.contact_level IN ('indirect', 'derived') AND ce.directionality = 'backward' THEN 2
    WHEN ce.temporality IN ('history', 'lifecycle') AND NOT EXISTS (
      SELECT 1 FROM knowledge_episode_relationships ker WHERE ker.knowledge_entity_id = ce.id
    ) THEN 3
    ELSE 4
  END,
  (ce.contact_confidence + ce.directionality_confidence +
   ce.temporality_confidence + ce.formalizability_confidence) / 4.0 ASC;

-- ============================================================================
-- End of Migration 009
-- ============================================================================
