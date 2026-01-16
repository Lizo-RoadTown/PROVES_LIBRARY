-- Migration 017: Add agent oversight and trust calibration
-- Human-in-the-loop system for agent self-improvement proposals
-- Agents propose changes, humans approve, trust grows over time

BEGIN;

-- =============================================================================
-- ENUMS
-- =============================================================================

-- Capability types that agents can improve
CREATE TYPE agent_capability_type AS ENUM (
    'prompt_update',           -- Changes to extraction/validation prompts
    'threshold_change',        -- Confidence thresholds, limits
    'method_improvement',      -- Extraction methodology changes
    'tool_configuration',      -- Tool usage patterns
    'ontology_expansion',      -- New entity types or relationships
    'validation_rule'          -- New validation rules
);

-- Proposal status tracking
CREATE TYPE proposal_status AS ENUM (
    'pending',                 -- Awaiting human review
    'approved',                -- Approved by human
    'rejected',                -- Rejected by human
    'auto_approved',           -- Auto-approved (high trust)
    'implemented',             -- Applied to system
    'reverted'                 -- Rolled back after issues
);

-- =============================================================================
-- AGENT CAPABILITIES TABLE
-- Tracks trust levels per agent per capability type
-- =============================================================================

CREATE TABLE IF NOT EXISTS agent_capabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    agent_name TEXT NOT NULL,              -- 'extractor', 'validator', 'improvement_analyzer'
    capability_type agent_capability_type NOT NULL,

    -- Trust metrics
    trust_score NUMERIC(4,3) DEFAULT 0.000 CHECK (trust_score >= 0 AND trust_score <= 1),
    total_proposals INTEGER DEFAULT 0,
    approved_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    auto_approved_count INTEGER DEFAULT 0,
    successful_implementations INTEGER DEFAULT 0,  -- Measured improvement
    failed_implementations INTEGER DEFAULT 0,       -- Caused problems

    -- Autonomy thresholds (configurable per capability)
    auto_approve_threshold NUMERIC(4,3) DEFAULT 0.900,  -- Trust needed for auto-approve
    requires_review BOOLEAN DEFAULT TRUE,               -- Override: always require review

    -- Metadata
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Each agent can only have one entry per capability type
    UNIQUE(agent_name, capability_type)
);

-- =============================================================================
-- AGENT PROPOSALS TABLE
-- Individual proposals from agents for system changes
-- =============================================================================

CREATE TABLE IF NOT EXISTS agent_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to capability (for trust tracking)
    capability_id UUID REFERENCES agent_capabilities(id) ON DELETE CASCADE,

    -- Proposal details
    title TEXT NOT NULL,
    proposed_change JSONB NOT NULL,        -- The actual change (prompt text, config, etc.)
    rationale TEXT NOT NULL,               -- Why the agent thinks this helps
    predicted_impact TEXT,                 -- What should improve

    -- Evidence supporting the proposal
    supporting_evidence JSONB,             -- Extraction IDs, patterns found, etc.
    affected_extraction_ids UUID[],        -- Extractions that led to this proposal

    -- Status tracking
    status proposal_status DEFAULT 'pending',
    auto_applied BOOLEAN DEFAULT FALSE,

    -- Review details
    reviewed_by TEXT,                      -- User ID from auth
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT,

    -- Implementation tracking
    implemented_at TIMESTAMPTZ,
    implementation_details JSONB,          -- What was actually changed

    -- Impact measurement (filled in after implementation)
    actual_impact TEXT,
    success_measured BOOLEAN DEFAULT FALSE,
    success_score NUMERIC(4,3),            -- 0-1, did it actually help?
    measurement_details JSONB,
    measured_at TIMESTAMPTZ,

    -- Rollback tracking
    reverted_at TIMESTAMPTZ,
    revert_reason TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- TRUST HISTORY TABLE
-- Audit trail of trust score changes
-- =============================================================================

CREATE TABLE IF NOT EXISTS agent_trust_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    capability_id UUID REFERENCES agent_capabilities(id) ON DELETE CASCADE,

    -- Change details
    previous_score NUMERIC(4,3),
    new_score NUMERIC(4,3),
    change_reason TEXT NOT NULL,           -- 'proposal_approved', 'proposal_rejected', 'implementation_success', etc.

    -- Context
    proposal_id UUID REFERENCES agent_proposals(id) ON DELETE SET NULL,
    changed_by TEXT,                        -- 'system' or user ID

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Agent capabilities
CREATE INDEX idx_agent_capabilities_agent ON agent_capabilities(agent_name);
CREATE INDEX idx_agent_capabilities_type ON agent_capabilities(capability_type);
CREATE INDEX idx_agent_capabilities_trust ON agent_capabilities(trust_score);

-- Agent proposals
CREATE INDEX idx_agent_proposals_status ON agent_proposals(status);
CREATE INDEX idx_agent_proposals_capability ON agent_proposals(capability_id);
CREATE INDEX idx_agent_proposals_created ON agent_proposals(created_at DESC);
CREATE INDEX idx_agent_proposals_pending ON agent_proposals(status)
    WHERE status = 'pending';

-- Trust history
CREATE INDEX idx_trust_history_capability ON agent_trust_history(capability_id);
CREATE INDEX idx_trust_history_created ON agent_trust_history(created_at DESC);

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Update trust score when a proposal is reviewed
CREATE OR REPLACE FUNCTION update_agent_trust_on_review()
RETURNS TRIGGER AS $$
DECLARE
    v_capability_id UUID;
    v_old_score NUMERIC(4,3);
    v_new_score NUMERIC(4,3);
    v_change_reason TEXT;
BEGIN
    -- Only process status changes
    IF OLD.status = NEW.status THEN
        RETURN NEW;
    END IF;

    v_capability_id := NEW.capability_id;

    -- Get current trust score
    SELECT trust_score INTO v_old_score
    FROM agent_capabilities
    WHERE id = v_capability_id;

    -- Calculate new trust score based on decision
    IF NEW.status = 'approved' OR NEW.status = 'auto_approved' THEN
        -- Approval increases trust
        v_new_score := LEAST(1.0, v_old_score + 0.05);
        v_change_reason := 'proposal_approved';

        UPDATE agent_capabilities
        SET approved_count = approved_count + 1,
            total_proposals = total_proposals + 1,
            trust_score = v_new_score,
            updated_at = NOW()
        WHERE id = v_capability_id;

        IF NEW.status = 'auto_approved' THEN
            UPDATE agent_capabilities
            SET auto_approved_count = auto_approved_count + 1
            WHERE id = v_capability_id;
        END IF;

    ELSIF NEW.status = 'rejected' THEN
        -- Rejection decreases trust
        v_new_score := GREATEST(0.0, v_old_score - 0.10);
        v_change_reason := 'proposal_rejected';

        UPDATE agent_capabilities
        SET rejected_count = rejected_count + 1,
            total_proposals = total_proposals + 1,
            trust_score = v_new_score,
            updated_at = NOW()
        WHERE id = v_capability_id;
    END IF;

    -- Record trust history
    IF v_new_score IS NOT NULL AND v_new_score != v_old_score THEN
        INSERT INTO agent_trust_history (
            capability_id, previous_score, new_score,
            change_reason, proposal_id, changed_by
        ) VALUES (
            v_capability_id, v_old_score, v_new_score,
            v_change_reason, NEW.id, NEW.reviewed_by
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Update trust when implementation success is measured
CREATE OR REPLACE FUNCTION update_agent_trust_on_measurement()
RETURNS TRIGGER AS $$
DECLARE
    v_capability_id UUID;
    v_old_score NUMERIC(4,3);
    v_new_score NUMERIC(4,3);
    v_change_reason TEXT;
BEGIN
    -- Only process when success is measured
    IF OLD.success_measured = NEW.success_measured THEN
        RETURN NEW;
    END IF;

    IF NOT NEW.success_measured THEN
        RETURN NEW;
    END IF;

    v_capability_id := NEW.capability_id;

    -- Get current trust score
    SELECT trust_score INTO v_old_score
    FROM agent_capabilities
    WHERE id = v_capability_id;

    -- Adjust trust based on actual success
    IF NEW.success_score >= 0.7 THEN
        -- Implementation was successful
        v_new_score := LEAST(1.0, v_old_score + 0.08);
        v_change_reason := 'implementation_success';

        UPDATE agent_capabilities
        SET successful_implementations = successful_implementations + 1,
            trust_score = v_new_score,
            updated_at = NOW()
        WHERE id = v_capability_id;

    ELSIF NEW.success_score < 0.3 THEN
        -- Implementation failed or made things worse
        v_new_score := GREATEST(0.0, v_old_score - 0.15);
        v_change_reason := 'implementation_failure';

        UPDATE agent_capabilities
        SET failed_implementations = failed_implementations + 1,
            trust_score = v_new_score,
            updated_at = NOW()
        WHERE id = v_capability_id;
    END IF;

    -- Record trust history
    IF v_new_score IS NOT NULL AND v_new_score != v_old_score THEN
        INSERT INTO agent_trust_history (
            capability_id, previous_score, new_score,
            change_reason, proposal_id, changed_by
        ) VALUES (
            v_capability_id, v_old_score, v_new_score,
            v_change_reason, NEW.id, 'system'
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Check if a proposal should be auto-approved
CREATE OR REPLACE FUNCTION check_auto_approve()
RETURNS TRIGGER AS $$
DECLARE
    v_trust_score NUMERIC(4,3);
    v_threshold NUMERIC(4,3);
    v_requires_review BOOLEAN;
BEGIN
    -- Only check new pending proposals
    IF NEW.status != 'pending' THEN
        RETURN NEW;
    END IF;

    -- Get capability settings
    SELECT trust_score, auto_approve_threshold, requires_review
    INTO v_trust_score, v_threshold, v_requires_review
    FROM agent_capabilities
    WHERE id = NEW.capability_id;

    -- Check if auto-approve conditions are met
    IF NOT v_requires_review AND v_trust_score >= v_threshold THEN
        NEW.status := 'auto_approved';
        NEW.auto_applied := TRUE;
        NEW.reviewed_at := NOW();
        NEW.review_notes := 'Auto-approved due to high trust score';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_agent_oversight_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_agent_capabilities_updated
BEFORE UPDATE ON agent_capabilities
FOR EACH ROW
EXECUTE FUNCTION update_agent_oversight_timestamp();

CREATE TRIGGER trigger_agent_proposals_updated
BEFORE UPDATE ON agent_proposals
FOR EACH ROW
EXECUTE FUNCTION update_agent_oversight_timestamp();

-- Trust updates on review
CREATE TRIGGER trigger_update_trust_on_review
AFTER UPDATE ON agent_proposals
FOR EACH ROW
EXECUTE FUNCTION update_agent_trust_on_review();

-- Trust updates on measurement
CREATE TRIGGER trigger_update_trust_on_measurement
AFTER UPDATE ON agent_proposals
FOR EACH ROW
EXECUTE FUNCTION update_agent_trust_on_measurement();

-- Auto-approve check
CREATE TRIGGER trigger_check_auto_approve
BEFORE INSERT ON agent_proposals
FOR EACH ROW
EXECUTE FUNCTION check_auto_approve();

-- =============================================================================
-- SEED DEFAULT CAPABILITIES
-- =============================================================================

INSERT INTO agent_capabilities (agent_name, capability_type, description, trust_score) VALUES
    ('extractor', 'prompt_update', 'Updates to extraction prompts and instructions', 0.0),
    ('extractor', 'threshold_change', 'Confidence score thresholds for extraction', 0.0),
    ('extractor', 'method_improvement', 'Extraction methodology and patterns', 0.0),
    ('validator', 'prompt_update', 'Updates to validation prompts and checks', 0.0),
    ('validator', 'validation_rule', 'New validation rules and constraints', 0.0),
    ('improvement_analyzer', 'prompt_update', 'Meta-learning analysis prompts', 0.0),
    ('improvement_analyzer', 'ontology_expansion', 'New entity types and relationships', 0.0)
ON CONFLICT (agent_name, capability_type) DO NOTHING;

-- =============================================================================
-- ROW LEVEL SECURITY
-- =============================================================================

ALTER TABLE agent_capabilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_trust_history ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read all oversight data
CREATE POLICY "Users can view agent capabilities"
ON agent_capabilities FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Users can view agent proposals"
ON agent_proposals FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "Users can view trust history"
ON agent_trust_history FOR SELECT
TO authenticated
USING (true);

-- Allow authenticated users to update proposals (for review)
CREATE POLICY "Users can review proposals"
ON agent_proposals FOR UPDATE
TO authenticated
USING (true)
WITH CHECK (true);

-- Service role can do everything
CREATE POLICY "Service role full access to capabilities"
ON agent_capabilities FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service role full access to proposals"
ON agent_proposals FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

CREATE POLICY "Service role full access to trust history"
ON agent_trust_history FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

COMMIT;
