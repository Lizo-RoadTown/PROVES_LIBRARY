-- Migration 006: Add improvement suggestions tracking
-- Meta-learning system that analyzes extraction patterns to suggest improvements

BEGIN;

-- Create suggestion category enum
CREATE TYPE suggestion_category AS ENUM (
    'prompt_update',           -- Suggestions for improving extractor prompts
    'ontology_change',         -- Suggestions for modifying the ontology
    'method_improvement',      -- Suggestions for extraction methodology
    'evidence_type_refinement', -- Suggestions for evidence type classification
    'confidence_calibration'   -- Suggestions for confidence scoring improvements
);

-- Create suggestion confidence enum
CREATE TYPE suggestion_confidence AS ENUM (
    'low',
    'medium',
    'high'
);

-- Create suggestion status enum
CREATE TYPE suggestion_status AS ENUM (
    'pending',      -- Waiting for human review
    'approved',     -- Approved for implementation
    'rejected',     -- Rejected by human reviewer
    'implemented',  -- Changes have been applied
    'needs_review'  -- Flagged for additional review
);

-- Create improvement_suggestions table
CREATE TABLE IF NOT EXISTS improvement_suggestions (
    -- Primary identification
    suggestion_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Categorization
    category suggestion_category NOT NULL,
    title TEXT NOT NULL,

    -- Analysis and recommendation
    evidence TEXT NOT NULL,              -- What patterns led to this suggestion
    current_state TEXT NOT NULL,         -- What exists now
    proposed_change TEXT NOT NULL,       -- Specific recommendation
    impact_count INTEGER DEFAULT 0,      -- Number of extractions affected
    confidence suggestion_confidence NOT NULL,

    -- Supporting data
    extraction_ids UUID[] DEFAULT '{}',  -- Array of extraction IDs that support this suggestion

    -- Review tracking
    status suggestion_status DEFAULT 'pending',
    review_decision TEXT CHECK (review_decision IN ('approve', 'reject', 'modified')),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,

    -- Notion sync
    notion_page_id TEXT UNIQUE,          -- Notion page ID for bidirectional sync

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_suggestions_status
ON improvement_suggestions(status);

CREATE INDEX IF NOT EXISTS idx_suggestions_category
ON improvement_suggestions(category);

CREATE INDEX IF NOT EXISTS idx_suggestions_notion_page_id
ON improvement_suggestions(notion_page_id)
WHERE notion_page_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_suggestions_reviewed_at
ON improvement_suggestions(reviewed_at)
WHERE reviewed_at IS NOT NULL;

-- Create trigger to update updated_at
CREATE OR REPLACE FUNCTION update_suggestion_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_suggestion_timestamp
BEFORE UPDATE ON improvement_suggestions
FOR EACH ROW
EXECUTE FUNCTION update_suggestion_updated_at();

COMMIT;
