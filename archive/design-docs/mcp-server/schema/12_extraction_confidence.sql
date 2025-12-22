-- ============================================================================
-- PROVES Library - Extraction Confidence & Evidence Tracking
-- ============================================================================
-- Version: 1.0.0
-- Created: 2024-12-22
-- 
-- PURPOSE:
--   Capture extraction quality metadata BEFORE promoting to canonical entities.
--   Every extracted candidate gets a confidence score + evidence trail.
--
-- FLOW:
--   raw_snapshots → raw_extractions (with confidence) → core_entities (canonical)
--                          ↑
--                   HITL review here
--
-- CONFIDENCE RUBRIC (agent must use consistently):
--   High (0.80–1.00):
--     - Doc explicitly defines it ("is/shall/must") or shows formal signature/table
--     - Term matches known F´ vocabulary (component/port/command/telemetry/event)
--     - Multiple sources agree
--   Medium (0.50–0.79):
--     - Strong cues but not a formal definition
--     - Extracted from an example that looks representative
--     - Missing 1–2 key properties
--   Low (0.00–0.49):
--     - Inferred from narrative text
--     - Only appears once, unclear context
--     - Conflicts with another statement or lacks supporting structure
-- ============================================================================

-- ============================================================================
-- ENUMS FOR CONFIDENCE TRACKING
-- ============================================================================

-- Confidence level (derived from numeric score)
CREATE TYPE confidence_level AS ENUM (
    'low',          -- 0.00–0.49: Uncertain, needs verification
    'medium',       -- 0.50–0.79: Likely correct, some gaps
    'high'          -- 0.80–1.00: High certainty, formal definition
);

-- What type of evidence supports this extraction?
CREATE TYPE evidence_type AS ENUM (
    'definition_spec',      -- Formal definition, specification, interface contract
    'interface_contract',   -- Port signature, API contract, protocol spec
    'example',              -- Code example, usage sample
    'narrative',            -- Descriptive text, documentation prose
    'table_diagram',        -- Structured table, diagram, schematic
    'comment',              -- Code comment, inline documentation
    'inferred'              -- No direct evidence, inferred from context
);

-- What extraction method was used?
CREATE TYPE extraction_method AS ENUM (
    'pattern',          -- Regex/pattern matching
    'llm',              -- LLM extraction (GPT, Claude, etc.)
    'hybrid',           -- Pattern + LLM combination
    'manual'            -- Human-entered
);

-- Candidate status (never auto-promote!)
CREATE TYPE candidate_status AS ENUM (
    'pending',          -- Awaiting review (default, NEVER skip)
    'accepted',         -- Human/agent verified, ready for core_entities
    'rejected',         -- Human/agent rejected as incorrect
    'merged',           -- Merged with another candidate (duplicate)
    'needs_context'     -- Need more information to decide
);

-- What kind of candidate is this?
CREATE TYPE candidate_type AS ENUM (
    -- Nodes (entities)
    'component',        -- Software/hardware component
    'port',             -- F´ port or interface
    'command',          -- F´ command definition
    'telemetry',        -- Telemetry channel
    'event',            -- F´ event
    'parameter',        -- Configuration parameter
    'data_type',        -- Type definition
    
    -- Edges (relationships)
    'dependency',       -- A depends on B
    'connection',       -- A connects to B (port wiring)
    'inheritance',      -- A inherits from B
    'composition',      -- A contains B
    
    -- Specs/properties
    'constraint',       -- Requirement, limitation
    'rate_spec',        -- Timing specification
    'memory_spec',      -- Memory/resource specification
    'protocol_spec'     -- Protocol/format specification
);

-- Specific confidence dimensions
CREATE TYPE confidence_dimension AS ENUM (
    'type_confidence',      -- "Is this really a port vs a parameter?"
    'field_confidence',     -- "Are extracted properties correct (units, rate, type)?"
    'relationship_confidence', -- "Does this dependency actually exist?"
    'completeness_confidence'  -- "Did we extract all the fields?"
);

-- ============================================================================
-- RAW EXTRACTIONS (Staging layer with confidence metadata)
-- ============================================================================

-- Every extracted candidate before promotion to canonical
CREATE TABLE raw_extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Source provenance (immutable references)
    source_snapshot_id UUID NOT NULL REFERENCES raw_snapshots(id),
    pipeline_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
    
    -- What we extracted
    candidate_type candidate_type NOT NULL,
    canonical_key TEXT NOT NULL,                 -- Proposed canonical name
    extracted_name TEXT NOT NULL,                -- Exact name as found in source
    extracted_properties JSONB NOT NULL,         -- All extracted fields as JSONB
    
    -- Ecosystem context
    ecosystem ecosystem_type NOT NULL,
    
    -- =========================================================================
    -- CONFIDENCE SCORING (the heart of this table)
    -- =========================================================================
    
    -- Overall confidence
    confidence_score NUMERIC(3,2) NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    confidence_level confidence_level NOT NULL,  -- Derived from score
    confidence_reason TEXT NOT NULL,             -- Short explanation of score
    
    -- Dimensional confidence (optional breakdown)
    type_confidence NUMERIC(3,2) CHECK (type_confidence >= 0.0 AND type_confidence <= 1.0),
    type_confidence_reason TEXT,                 -- "Is this really a port vs a parameter?"
    
    field_confidence NUMERIC(3,2) CHECK (field_confidence >= 0.0 AND field_confidence <= 1.0),
    field_confidence_reason TEXT,                -- "Are these extracted properties correct?"
    
    -- =========================================================================
    -- EVIDENCE TRACKING
    -- =========================================================================
    
    -- Primary evidence
    evidence_type evidence_type NOT NULL,
    evidence_text TEXT NOT NULL,                 -- Exact text span that supports extraction
    evidence_location JSONB NOT NULL,            -- {"doc": "...", "page": 1, "section": "...", "lines": [10, 15]}
    
    -- Additional evidence (if multiple sources)
    supporting_evidence JSONB,                   -- Array of additional evidence objects
    
    -- =========================================================================
    -- EXTRACTION METADATA
    -- =========================================================================
    
    extraction_method extraction_method NOT NULL,
    extraction_method_version TEXT NOT NULL,     -- e.g., "llm:claude-3.5-sonnet-20241022"
    extraction_prompt_hash TEXT,                 -- Hash of prompt used (for reproducibility)
    
    -- What we couldn't extract
    missing_fields TEXT[],                       -- List of expected but missing fields
    extraction_warnings TEXT[],                  -- Warnings during extraction
    
    -- =========================================================================
    -- STATUS & WORKFLOW
    -- =========================================================================
    
    status candidate_status NOT NULL DEFAULT 'pending',
    
    -- Review tracking
    reviewed_by TEXT,                            -- Agent or human who reviewed
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    
    -- If merged with another candidate
    merged_into_id UUID REFERENCES raw_extractions(id),
    
    -- If promoted to canonical
    promoted_to_entity_id UUID,                  -- References core_entities.id (added after FK setup)
    promoted_at TIMESTAMP,
    
    -- Timestamps
    extracted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_raw_extractions_snapshot ON raw_extractions(source_snapshot_id);
CREATE INDEX idx_raw_extractions_run ON raw_extractions(pipeline_run_id);
CREATE INDEX idx_raw_extractions_status ON raw_extractions(status);
CREATE INDEX idx_raw_extractions_confidence ON raw_extractions(confidence_score);
CREATE INDEX idx_raw_extractions_type ON raw_extractions(candidate_type);
CREATE INDEX idx_raw_extractions_ecosystem ON raw_extractions(ecosystem);
CREATE INDEX idx_raw_extractions_canonical ON raw_extractions(canonical_key);
CREATE INDEX idx_raw_extractions_pending ON raw_extractions(status) WHERE status = 'pending';

-- ============================================================================
-- CONFIDENCE DIMENSION DETAILS (for complex extractions)
-- ============================================================================

-- Per-dimension confidence breakdown (optional, for detailed analysis)
CREATE TABLE extraction_confidence_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    extraction_id UUID NOT NULL REFERENCES raw_extractions(id) ON DELETE CASCADE,
    
    dimension confidence_dimension NOT NULL,
    score NUMERIC(3,2) NOT NULL CHECK (score >= 0.0 AND score <= 1.0),
    level confidence_level NOT NULL,
    reason TEXT NOT NULL,
    
    -- Evidence for this specific dimension
    evidence_text TEXT,
    evidence_location JSONB,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_confidence_details_extraction ON extraction_confidence_details(extraction_id);
CREATE INDEX idx_confidence_details_dimension ON extraction_confidence_details(dimension);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Derive confidence_level from numeric score
CREATE OR REPLACE FUNCTION derive_confidence_level(score NUMERIC)
RETURNS confidence_level AS $$
BEGIN
    IF score >= 0.80 THEN
        RETURN 'high';
    ELSIF score >= 0.50 THEN
        RETURN 'medium';
    ELSE
        RETURN 'low';
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Auto-set confidence_level on insert/update
CREATE OR REPLACE FUNCTION trg_set_confidence_level()
RETURNS TRIGGER AS $$
BEGIN
    NEW.confidence_level := derive_confidence_level(NEW.confidence_score);
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_raw_extractions_confidence
    BEFORE INSERT OR UPDATE ON raw_extractions
    FOR EACH ROW
    EXECUTE FUNCTION trg_set_confidence_level();

-- ============================================================================
-- AUDIT QUERIES FOR EXTRACTION QUALITY
-- ============================================================================

COMMENT ON TABLE raw_extractions IS 
'Staging table for extracted candidates with full confidence metadata.
NEVER auto-promote to core_entities. All candidates start as pending.

Example query - Find low confidence extractions needing review:
SELECT 
    canonical_key,
    candidate_type,
    confidence_score,
    confidence_reason,
    evidence_type,
    missing_fields
FROM raw_extractions
WHERE status = ''pending''
  AND confidence_level = ''low''
ORDER BY extracted_at DESC;

Example query - Find high confidence ready for promotion:
SELECT 
    canonical_key,
    candidate_type,
    confidence_score,
    confidence_reason,
    evidence_text
FROM raw_extractions
WHERE status = ''pending''
  AND confidence_level = ''high''
  AND array_length(missing_fields, 1) IS NULL
ORDER BY confidence_score DESC;';

-- ============================================================================
-- EXAMPLE EVIDENCE_LOCATION JSONB STRUCTURES
-- ============================================================================

COMMENT ON COLUMN raw_extractions.evidence_location IS
'Location of evidence in source document. Examples:

For GitHub file:
{
    "doc": "Svc/TlmChan/TlmChan.fpp",
    "repo": "nasa/fprime",
    "commit": "abc123",
    "lines": [45, 52],
    "url": "https://github.com/nasa/fprime/blob/main/Svc/TlmChan/TlmChan.fpp#L45-L52"
}

For documentation page:
{
    "doc": "F Prime User Guide",
    "page": "Ports",
    "section": "Port Types",
    "url": "https://nasa.github.io/fprime/UsersGuide/user/ports.html",
    "anchor": "#port-types"
}

For local file:
{
    "doc": "proves_power_management.md",
    "path": "/trial_docs/proves_power_management.md",
    "lines": [10, 25]
}';

-- ============================================================================
-- EXAMPLE EXTRACTED_PROPERTIES JSONB STRUCTURES
-- ============================================================================

COMMENT ON COLUMN raw_extractions.extracted_properties IS
'Extracted properties as JSONB. Structure varies by candidate_type.

For port:
{
    "port_type": "sync_input",
    "data_type": "Fw::Buffer",
    "role": "GuardedInput",
    "component": "TlmChan",
    "description": "Receives buffer for telemetry storage"
}

For telemetry:
{
    "channel_name": "CPU_TEMP",
    "data_type": "F32",
    "units": "Celsius",
    "rate": "1Hz",
    "component": "SystemResources"
}

For dependency:
{
    "from_component": "proves_power_manager",
    "to_component": "i2c_driver",
    "dependency_type": "runtime",
    "criticality": "HIGH",
    "reason": "Power management requires I2C bus for sensor communication"
}';

-- ============================================================================
-- VALIDATION CONSTRAINTS
-- ============================================================================

-- Ensure pending candidates are never auto-promoted
ALTER TABLE raw_extractions ADD CONSTRAINT chk_no_auto_promote
    CHECK (
        (status = 'pending' AND promoted_to_entity_id IS NULL AND promoted_at IS NULL)
        OR
        (status = 'accepted' AND (promoted_to_entity_id IS NOT NULL OR promoted_at IS NULL))
        OR
        (status IN ('rejected', 'merged', 'needs_context'))
    );

-- Ensure merged candidates reference another extraction
ALTER TABLE raw_extractions ADD CONSTRAINT chk_merged_has_target
    CHECK (
        (status = 'merged' AND merged_into_id IS NOT NULL)
        OR
        (status != 'merged')
    );

-- ============================================================================
-- RUBRIC REFERENCE (for agent prompts)
-- ============================================================================

COMMENT ON TYPE confidence_level IS
'Confidence Level Rubric for Extraction Agents:

HIGH (0.80–1.00):
  ✓ Doc explicitly defines it ("is/shall/must") or shows formal signature/table
  ✓ Term matches known F´ vocabulary (component/port/command/telemetry/event)
  ✓ Multiple sources agree

MEDIUM (0.50–0.79):
  ~ Strong cues but not a formal definition
  ~ Extracted from an example that looks representative
  ~ Missing 1–2 key properties

LOW (0.00–0.49):
  ✗ Inferred from narrative text
  ✗ Only appears once, unclear context
  ✗ Conflicts with another statement or lacks supporting structure

Agents MUST assign confidence_reason explaining which criteria apply.';
