-- ============================================================================
-- PROVES Library - Validation Staging & Decision Tables
-- ============================================================================
-- Version: 1.0.0
-- Created: 2024-12-22
-- 
-- PURPOSE:
--   Persistent memory for extraction validation workflow.
--   These tables work alongside LangGraph's checkpointer (short-term thread memory)
--   to provide cross-session decision tracking (long-term institutional memory).
--
-- LANGGRAPH INTEGRATION:
--   - PostgresSaver: Handles thread-level state (conversation checkpoints)
--   - These tables: Handle cross-thread persistent decisions (institutional memory)
--   - Store interface: Can read/write to these tables via custom namespace
--
-- FLOW:
--   raw_snapshots 
--     → staging_extractions (candidates with confidence)
--       → validation_decisions (accept/reject/merge)
--         → core_entities (promoted canonical entities)
--
-- NAMESPACE PATTERN (for LangGraph Store):
--   ("extractions", pipeline_run_id) → staging_extractions
--   ("decisions", extraction_id) → validation_decisions
--   ("entities", ecosystem, entity_type) → core_entities
-- ============================================================================

-- ============================================================================
-- ENUMS
-- ============================================================================

-- Decision types for validation
CREATE TYPE validation_decision_type AS ENUM (
    'accept',               -- Promote to core_entities
    'reject',               -- Mark as incorrect, do not promote
    'merge',                -- Merge with another extraction
    'needs_more_evidence',  -- Request additional evidence before deciding
    'defer'                 -- Defer decision to human
);

-- Who made the decision
CREATE TYPE decider_type AS ENUM (
    'human',                -- Human reviewer
    'validator_agent',      -- Automated validator agent
    'consensus',            -- Multiple agents agreed
    'rule_based'            -- Automatic rule (e.g., high confidence auto-accept)
);

-- ============================================================================
-- STAGING EXTRACTIONS (Consolidated staging table)
-- ============================================================================
-- Note: This is the canonical staging table for all extraction candidates.
-- ENUMs are defined in 12_extraction_enums.sql.

CREATE TABLE staging_extractions (
    -- Primary key
    extraction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Provenance (immutable references)
    pipeline_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
    snapshot_id UUID NOT NULL REFERENCES raw_snapshots(id),
    
    -- Agent identification
    agent_id TEXT NOT NULL,                      -- Agent name/version: "extractor_v1.2.0"
    agent_version TEXT,                          -- Detailed version info
    
    -- What was extracted
    candidate_type candidate_type NOT NULL,      -- component/port/constraint/etc.
    candidate_key TEXT NOT NULL,                 -- Provisional stable key
    candidate_payload JSONB NOT NULL,            -- The structured guess (all extracted fields)
    
    -- Ecosystem context
    ecosystem ecosystem_type NOT NULL,
    
    -- =========================================================================
    -- CONFIDENCE SCORING
    -- =========================================================================
    confidence_score NUMERIC(3,2) NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    confidence_reason TEXT NOT NULL,             -- Short explanation
    
    -- =========================================================================
    -- EVIDENCE
    -- =========================================================================
    evidence JSONB NOT NULL,                     -- Source pointers + snippet
    -- Example: {
    --   "text": "port BufferGet: Fw.Buffer",
    --   "source": {"doc": "TlmChan.fpp", "lines": [45, 52], "url": "..."},
    --   "supporting": [...]  -- Additional evidence
    -- }
    evidence_type evidence_type NOT NULL,        -- spec/definition/example/narrative
    
    -- =========================================================================
    -- STATUS TRACKING
    -- =========================================================================
    status candidate_status NOT NULL DEFAULT 'pending',
    
    -- If promoted
    promoted_to_id UUID,                         -- FK to core_entities.id (nullable)
    promoted_at TIMESTAMP,
    
    -- If merged
    merged_into_id UUID REFERENCES staging_extractions(extraction_id),
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_staging_status ON staging_extractions(status);
CREATE INDEX idx_staging_pipeline ON staging_extractions(pipeline_run_id);
CREATE INDEX idx_staging_snapshot ON staging_extractions(snapshot_id);
CREATE INDEX idx_staging_confidence ON staging_extractions(confidence_score DESC);
CREATE INDEX idx_staging_pending ON staging_extractions(status) WHERE status = 'pending';
CREATE INDEX idx_staging_candidate_key ON staging_extractions(candidate_key);
CREATE INDEX idx_staging_type ON staging_extractions(candidate_type);

-- ============================================================================
-- VALIDATION DECISIONS (Persistent decision memory)
-- ============================================================================
-- This is the "institutional memory" - tracks every decision ever made.
-- Enables learning from past decisions and audit trail.

CREATE TABLE validation_decisions (
    -- Primary key
    decision_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- What we're deciding on
    extraction_id UUID NOT NULL REFERENCES staging_extractions(extraction_id),
    
    -- Who decided
    decided_by TEXT NOT NULL,                    -- Human username or agent name
    decider_type decider_type NOT NULL,
    
    -- The decision
    decision validation_decision_type NOT NULL,
    decision_reason TEXT NOT NULL,               -- Why this decision was made
    
    -- If accepted, what it became
    canonical_id UUID,                           -- FK to core_entities.id (nullable until promoted)
    
    -- If merged, what it merged into
    merged_into_extraction_id UUID REFERENCES staging_extractions(extraction_id),
    
    -- Additional context for learning
    confidence_at_decision NUMERIC(3,2),         -- What was the confidence when decided
    evidence_at_decision JSONB,                  -- Snapshot of evidence at decision time
    
    -- Feedback for improving extraction
    feedback JSONB,                              -- {"missing_fields": [...], "incorrect_fields": [...]}
    
    -- Timestamps
    decided_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_decisions_extraction ON validation_decisions(extraction_id);
CREATE INDEX idx_decisions_decided_by ON validation_decisions(decided_by);
CREATE INDEX idx_decisions_decision ON validation_decisions(decision);
CREATE INDEX idx_decisions_canonical ON validation_decisions(canonical_id);
CREATE INDEX idx_decisions_at ON validation_decisions(decided_at DESC);

-- ============================================================================
-- DECISION HISTORY VIEW (For learning from past decisions)
-- ============================================================================

CREATE VIEW decision_history AS
SELECT 
    vd.decision_id,
    vd.extraction_id,
    se.candidate_type,
    se.candidate_key,
    se.confidence_score,
    se.confidence_reason,
    se.evidence_type,
    vd.decision,
    vd.decision_reason,
    vd.decided_by,
    vd.decider_type,
    vd.decided_at,
    vd.canonical_id,
    CASE 
        WHEN vd.decision = 'accept' THEN TRUE
        WHEN vd.decision = 'reject' THEN FALSE
        ELSE NULL
    END as was_correct
FROM validation_decisions vd
JOIN staging_extractions se ON se.extraction_id = vd.extraction_id
ORDER BY vd.decided_at DESC;

COMMENT ON VIEW decision_history IS
'View of all validation decisions with extraction context.
Use for:
- Learning from past accept/reject patterns
- Auditing decision quality
- Training extraction models on verified data';

-- ============================================================================
-- PENDING REVIEW QUEUE VIEW
-- ============================================================================

CREATE VIEW pending_review_queue AS
SELECT 
    se.extraction_id,
    se.candidate_type,
    se.candidate_key,
    se.candidate_payload,
    se.confidence_score,
    se.confidence_reason,
    se.evidence,
    se.evidence_type,
    se.ecosystem,
    se.agent_id,
    se.created_at,
    -- Priority: lower confidence needs more review
    CASE 
        WHEN se.confidence_score >= 0.80 THEN 1  -- High: quick review
        WHEN se.confidence_score >= 0.50 THEN 2  -- Medium: needs attention
        ELSE 3                                    -- Low: deep review needed
    END as review_priority
FROM staging_extractions se
WHERE se.status = 'pending'
ORDER BY review_priority, se.created_at;

COMMENT ON VIEW pending_review_queue IS
'Queue of extractions needing review, prioritized by confidence.
High confidence = quick review, low confidence = deep review needed.';

-- ============================================================================
-- FUNCTIONS FOR DECISION WORKFLOW
-- ============================================================================

-- Accept an extraction and promote to core_entities
CREATE OR REPLACE FUNCTION accept_extraction(
    p_extraction_id UUID,
    p_decided_by TEXT,
    p_decider_type decider_type,
    p_decision_reason TEXT
) RETURNS UUID AS $$
DECLARE
    v_extraction staging_extractions%ROWTYPE;
    v_entity_id UUID;
    v_decision_id UUID;
BEGIN
    -- Get the extraction
    SELECT * INTO v_extraction 
    FROM staging_extractions 
    WHERE extraction_id = p_extraction_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Extraction not found: %', p_extraction_id;
    END IF;
    
    IF v_extraction.status != 'pending' THEN
        RAISE EXCEPTION 'Extraction is not pending: %', v_extraction.status;
    END IF;
    
    -- Create the canonical entity
    INSERT INTO core_entities (
        entity_type,
        canonical_key,
        ecosystem,
        display_name,
        attributes,
        source_snapshot_id,
        created_from_extraction_id
    ) VALUES (
        v_extraction.candidate_type::text::entity_type,  -- May need mapping
        v_extraction.candidate_key,
        v_extraction.ecosystem,
        v_extraction.candidate_key,  -- Use key as display name initially
        v_extraction.candidate_payload,
        v_extraction.snapshot_id,
        v_extraction.extraction_id
    ) RETURNING id INTO v_entity_id;
    
    -- Record the decision
    INSERT INTO validation_decisions (
        extraction_id,
        decided_by,
        decider_type,
        decision,
        decision_reason,
        canonical_id,
        confidence_at_decision,
        evidence_at_decision
    ) VALUES (
        p_extraction_id,
        p_decided_by,
        p_decider_type,
        'accept',
        p_decision_reason,
        v_entity_id,
        v_extraction.confidence_score,
        v_extraction.evidence
    ) RETURNING decision_id INTO v_decision_id;
    
    -- Update the extraction status
    UPDATE staging_extractions 
    SET status = 'accepted',
        promoted_to_id = v_entity_id,
        promoted_at = NOW(),
        updated_at = NOW()
    WHERE extraction_id = p_extraction_id;
    
    RETURN v_entity_id;
END;
$$ LANGUAGE plpgsql;

-- Reject an extraction
CREATE OR REPLACE FUNCTION reject_extraction(
    p_extraction_id UUID,
    p_decided_by TEXT,
    p_decider_type decider_type,
    p_decision_reason TEXT,
    p_feedback JSONB DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_extraction staging_extractions%ROWTYPE;
    v_decision_id UUID;
BEGIN
    -- Get the extraction
    SELECT * INTO v_extraction 
    FROM staging_extractions 
    WHERE extraction_id = p_extraction_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Extraction not found: %', p_extraction_id;
    END IF;
    
    -- Record the decision
    INSERT INTO validation_decisions (
        extraction_id,
        decided_by,
        decider_type,
        decision,
        decision_reason,
        confidence_at_decision,
        evidence_at_decision,
        feedback
    ) VALUES (
        p_extraction_id,
        p_decided_by,
        p_decider_type,
        'reject',
        p_decision_reason,
        v_extraction.confidence_score,
        v_extraction.evidence,
        p_feedback
    ) RETURNING decision_id INTO v_decision_id;
    
    -- Update the extraction status
    UPDATE staging_extractions 
    SET status = 'rejected',
        updated_at = NOW()
    WHERE extraction_id = p_extraction_id;
    
    RETURN v_decision_id;
END;
$$ LANGUAGE plpgsql;

-- Request more evidence
CREATE OR REPLACE FUNCTION request_more_evidence(
    p_extraction_id UUID,
    p_decided_by TEXT,
    p_what_is_needed TEXT
) RETURNS UUID AS $$
DECLARE
    v_decision_id UUID;
BEGIN
    INSERT INTO validation_decisions (
        extraction_id,
        decided_by,
        decider_type,
        decision,
        decision_reason
    ) VALUES (
        p_extraction_id,
        p_decided_by,
        'human',
        'needs_more_evidence',
        p_what_is_needed
    ) RETURNING decision_id INTO v_decision_id;
    
    UPDATE staging_extractions 
    SET status = 'needs_context',
        updated_at = NOW()
    WHERE extraction_id = p_extraction_id;
    
    RETURN v_decision_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- AUTO-ACCEPT RULES (Optional: for high confidence extractions)
-- ============================================================================

-- Function to auto-accept high-confidence extractions (call with caution!)
CREATE OR REPLACE FUNCTION auto_accept_high_confidence(
    p_threshold NUMERIC DEFAULT 0.90,
    p_agent_id TEXT DEFAULT 'auto_validator'
) RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER := 0;
    v_extraction RECORD;
BEGIN
    FOR v_extraction IN 
        SELECT extraction_id
        FROM staging_extractions
        WHERE status = 'pending'
          AND confidence_score >= p_threshold
          AND evidence_type IN ('definition_spec', 'interface_contract')  -- Only formal sources
    LOOP
        PERFORM accept_extraction(
            v_extraction.extraction_id,
            p_agent_id,
            'rule_based',
            format('Auto-accepted: confidence %.2f >= threshold %.2f with formal evidence', 
                   (SELECT confidence_score FROM staging_extractions WHERE extraction_id = v_extraction.extraction_id),
                   p_threshold)
        );
        v_count := v_count + 1;
    END LOOP;
    
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION auto_accept_high_confidence IS
'Auto-accept extractions with confidence >= threshold AND formal evidence.
Use with caution! Default threshold is 0.90 (very high).
Only accepts from definition_spec or interface_contract evidence types.';

-- ============================================================================
-- LEARNING QUERIES (For improving extraction quality)
-- ============================================================================

COMMENT ON TABLE validation_decisions IS
'Persistent decision memory. Every decision is recorded for:

1. AUDIT: Who decided what, when, and why?
   SELECT * FROM validation_decisions 
   WHERE extraction_id = ''...''
   ORDER BY decided_at;

2. LEARNING: What patterns get accepted vs rejected?
   SELECT 
       se.candidate_type,
       se.evidence_type,
       vd.decision,
       AVG(se.confidence_score) as avg_confidence,
       COUNT(*) as count
   FROM validation_decisions vd
   JOIN staging_extractions se ON se.extraction_id = vd.extraction_id
   GROUP BY se.candidate_type, se.evidence_type, vd.decision
   ORDER BY count DESC;

3. FEEDBACK: What errors are agents making?
   SELECT 
       se.agent_id,
       vd.feedback->>''incorrect_fields'' as errors,
       COUNT(*) as error_count
   FROM validation_decisions vd
   JOIN staging_extractions se ON se.extraction_id = vd.extraction_id
   WHERE vd.decision = ''reject''
     AND vd.feedback IS NOT NULL
   GROUP BY se.agent_id, vd.feedback->>''incorrect_fields''
   ORDER BY error_count DESC;

4. CALIBRATION: Are confidence scores accurate?
   SELECT 
       CASE 
           WHEN se.confidence_score >= 0.80 THEN ''high''
           WHEN se.confidence_score >= 0.50 THEN ''medium''
           ELSE ''low''
       END as confidence_band,
       COUNT(*) FILTER (WHERE vd.decision = ''accept'') as accepted,
       COUNT(*) FILTER (WHERE vd.decision = ''reject'') as rejected,
       ROUND(COUNT(*) FILTER (WHERE vd.decision = ''accept'')::numeric / NULLIF(COUNT(*), 0), 2) as accept_rate
   FROM validation_decisions vd
   JOIN staging_extractions se ON se.extraction_id = vd.extraction_id
   GROUP BY confidence_band
   ORDER BY confidence_band;
';

-- ============================================================================
-- LANGGRAPH STORE INTEGRATION PATTERN
-- ============================================================================

COMMENT ON TABLE staging_extractions IS
'Staging table for extracted candidates.

LANGGRAPH STORE INTEGRATION:
Use the LangGraph Store interface to read/write to this table.

# In your LangGraph node:
from langgraph.store.memory import InMemoryStore  # or PostgresStore

# Namespace pattern:
namespace = ("extractions", pipeline_run_id)

# Write (after extraction):
store.put(
    namespace,
    str(extraction_id),
    {
        "candidate_type": "port",
        "candidate_key": "fprime:Svc:BufferGet",
        "confidence_score": 0.85,
        "evidence": {...}
    }
)

# Read (in validator):
pending = store.search(namespace, filter={"status": "pending"})

This table persists decisions across all threads/sessions.
The checkpointer handles thread-level state; this table handles
institutional memory that spans all sessions.';
