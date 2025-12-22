-- ============================================================================
-- PROVES Library - Migration: Add extraction provenance to core_entities
-- ============================================================================
-- Run this AFTER 10_layered_architecture.sql and 13_validation_staging.sql
-- 
-- Adds a column to track which extraction an entity was promoted from.
-- This creates the link: staging_extractions → core_entities
-- ============================================================================

-- Add column to track extraction origin
ALTER TABLE core_entities 
ADD COLUMN IF NOT EXISTS created_from_extraction_id UUID;

-- Add foreign key (can only add after staging_extractions exists)
-- Note: This is a loose reference since the FK table is created in a later migration
-- If running all migrations together, this will work. If not, you may need to defer the FK.
COMMENT ON COLUMN core_entities.created_from_extraction_id IS
'References staging_extractions.extraction_id if this entity was promoted from an extraction.
NULL if created directly (e.g., seed data or manual entry).
Enables tracing back to the original extraction with its confidence/evidence.';

-- Index for looking up which extractions became entities
CREATE INDEX IF NOT EXISTS idx_core_entities_extraction 
    ON core_entities(created_from_extraction_id) 
    WHERE created_from_extraction_id IS NOT NULL;

-- ============================================================================
-- VIEW: Entity with extraction provenance
-- ============================================================================

CREATE OR REPLACE VIEW entity_provenance AS
SELECT 
    ce.id as entity_id,
    ce.entity_type,
    ce.canonical_key,
    ce.name,
    ce.ecosystem,
    ce.created_at as entity_created_at,
    
    -- Extraction provenance (if applicable)
    se.extraction_id,
    se.candidate_key,
    se.confidence_score as extraction_confidence,
    se.confidence_reason,
    se.evidence_type,
    se.evidence,
    se.agent_id as extracted_by_agent,
    se.created_at as extraction_created_at,
    
    -- Decision provenance
    vd.decision_id,
    vd.decided_by,
    vd.decider_type,
    vd.decision_reason as acceptance_reason,
    vd.decided_at
    
FROM core_entities ce
LEFT JOIN staging_extractions se ON se.extraction_id = ce.created_from_extraction_id
LEFT JOIN validation_decisions vd ON vd.extraction_id = se.extraction_id 
    AND vd.decision = 'accept';

COMMENT ON VIEW entity_provenance IS
'Full provenance chain for entities: extraction → decision → entity.
Shows confidence, evidence, and decision reasoning for each entity.
NULL extraction columns mean entity was created without staging (seed data).';
