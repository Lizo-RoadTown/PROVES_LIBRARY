-- PROVES Library - Training Data Schema
-- Tables for collecting human-in-the-loop feedback for fine-tuning local models
-- PostgreSQL

-- ============================================
-- TRAINING DATA TABLES
-- ============================================

-- Raw interaction logs from curator agent sessions
-- Captures everything: input, AI output, human feedback
CREATE TABLE training_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Session context
    thread_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    session_type TEXT,  -- 'extraction', 'validation', 'storage'
    
    -- Input context
    doc_chunk TEXT,                      -- The text chunk being analyzed
    doc_source TEXT,                     -- Source file path
    doc_chunk_start_line INT,            -- Line number context
    doc_chunk_end_line INT,
    
    -- AI output (what Claude produced)
    ai_extraction JSONB,                 -- Structured extraction result
    ai_raw_response TEXT,                -- Full text response
    model_used TEXT,                     -- 'claude-sonnet-4-5', 'claude-haiku-3-5', etc.
    
    -- Human feedback
    human_decision TEXT,                 -- 'approved', 'rejected', 'corrected'
    human_correction JSONB,              -- If corrected, the fixed version
    correction_reason TEXT,              -- Why human corrected
    correction_categories TEXT[],        -- Tags: 'wrong_relationship', 'wrong_criticality', 'missing_dep', etc.
    
    -- Performance metrics
    latency_ms INT,                      -- How long the AI took
    token_count_input INT,
    token_count_output INT,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    curator_version TEXT DEFAULT '1.0'
);

-- Processed training examples ready for fine-tuning
-- Instruction-following format compatible with Llama, Mistral, etc.
CREATE TABLE training_examples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interaction_id UUID REFERENCES training_interactions(id) ON DELETE SET NULL,
    
    -- Instruction format (Alpaca-style)
    instruction TEXT NOT NULL,           -- The task description
    input TEXT NOT NULL,                 -- The document chunk
    output TEXT NOT NULL,                -- The gold answer (approved or corrected)
    
    -- Metadata
    task_type TEXT NOT NULL,             -- 'dependency_extraction', 'criticality_assessment', etc.
    is_correction BOOLEAN DEFAULT FALSE, -- Was this a human fix? (higher weight)
    difficulty TEXT,                     -- 'easy', 'medium', 'hard'
    
    -- Quality signals
    confidence_score DECIMAL(3,2),       -- Human confidence in this example
    include_in_training BOOLEAN DEFAULT TRUE,  -- Filter flag
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    exported_at TIMESTAMPTZ              -- When exported to JSONL
);

-- Learning log: track what patterns the system learns
CREATE TABLE learning_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- What was learned
    lesson_type TEXT NOT NULL,           -- 'pattern', 'mistake', 'edge_case'
    lesson_summary TEXT NOT NULL,        -- Brief description
    lesson_details JSONB,                -- Structured details
    
    -- Source
    interaction_ids UUID[],              -- Which interactions taught this
    example_count INT DEFAULT 1,         -- How many examples support this
    
    -- Application
    applied_to_prompt BOOLEAN DEFAULT FALSE,  -- Was this incorporated into prompts?
    prompt_version TEXT,                 -- Which prompt version includes this
    
    -- Audit
    discovered_at TIMESTAMPTZ DEFAULT NOW(),
    last_reinforced_at TIMESTAMPTZ
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX idx_training_interactions_thread ON training_interactions(thread_id);
CREATE INDEX idx_training_interactions_decision ON training_interactions(human_decision);
CREATE INDEX idx_training_interactions_timestamp ON training_interactions(timestamp);
CREATE INDEX idx_training_interactions_model ON training_interactions(model_used);

CREATE INDEX idx_training_examples_task ON training_examples(task_type);
CREATE INDEX idx_training_examples_correction ON training_examples(is_correction);
CREATE INDEX idx_training_examples_include ON training_examples(include_in_training);

CREATE INDEX idx_learning_log_type ON learning_log(lesson_type);

-- ============================================
-- VIEWS
-- ============================================

-- Summary of training data collection progress
CREATE OR REPLACE VIEW training_data_summary AS
SELECT 
    COUNT(*) as total_interactions,
    COUNT(*) FILTER (WHERE human_decision = 'approved') as approved_count,
    COUNT(*) FILTER (WHERE human_decision = 'rejected') as rejected_count,
    COUNT(*) FILTER (WHERE human_decision = 'corrected') as corrected_count,
    COUNT(*) FILTER (WHERE human_decision IS NULL) as pending_count,
    (SELECT COUNT(*) FROM training_examples WHERE include_in_training = TRUE) as training_examples_ready,
    (SELECT COUNT(*) FROM training_examples WHERE is_correction = TRUE) as corrections_count,
    (SELECT COUNT(*) FROM learning_log) as lessons_learned
FROM training_interactions;

-- Correction patterns (what types of mistakes does the AI make?)
CREATE OR REPLACE VIEW correction_patterns AS
SELECT 
    unnest(correction_categories) as category,
    COUNT(*) as occurrence_count,
    array_agg(DISTINCT model_used) as models_affected
FROM training_interactions
WHERE human_decision = 'corrected'
GROUP BY unnest(correction_categories)
ORDER BY occurrence_count DESC;

-- ============================================
-- FUNCTIONS
-- ============================================

-- Convert an interaction to a training example
CREATE OR REPLACE FUNCTION create_training_example(
    p_interaction_id UUID,
    p_task_type TEXT DEFAULT 'dependency_extraction'
) RETURNS UUID AS $$
DECLARE
    v_example_id UUID;
    v_interaction training_interactions%ROWTYPE;
    v_instruction TEXT;
    v_input TEXT;
    v_output TEXT;
    v_is_correction BOOLEAN;
BEGIN
    -- Get the interaction
    SELECT * INTO v_interaction FROM training_interactions WHERE id = p_interaction_id;
    
    IF v_interaction.id IS NULL THEN
        RAISE EXCEPTION 'Interaction not found: %', p_interaction_id;
    END IF;
    
    -- Skip if no human decision
    IF v_interaction.human_decision IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Skip rejected (no gold answer)
    IF v_interaction.human_decision = 'rejected' THEN
        RETURN NULL;
    END IF;
    
    -- Build instruction
    v_instruction := 'Analyze this technical documentation and extract all dependencies. ' ||
                     'For each dependency, identify: component name, what it depends on, ' ||
                     'relationship type (depends_on, requires, enables, conflicts_with, mitigates, causes), ' ||
                     'and criticality level (HIGH, MEDIUM, LOW).';
    
    -- Input is the doc chunk
    v_input := v_interaction.doc_chunk;
    
    -- Output is either original (if approved) or corrected
    IF v_interaction.human_decision = 'corrected' AND v_interaction.human_correction IS NOT NULL THEN
        v_output := v_interaction.human_correction::TEXT;
        v_is_correction := TRUE;
    ELSE
        v_output := v_interaction.ai_raw_response;
        v_is_correction := FALSE;
    END IF;
    
    -- Insert the example
    INSERT INTO training_examples (
        interaction_id,
        instruction,
        input,
        output,
        task_type,
        is_correction
    ) VALUES (
        p_interaction_id,
        v_instruction,
        v_input,
        v_output,
        p_task_type,
        v_is_correction
    ) RETURNING id INTO v_example_id;
    
    RETURN v_example_id;
END;
$$ LANGUAGE plpgsql;

-- Export training examples to JSONL format (returns as TEXT)
CREATE OR REPLACE FUNCTION export_training_jsonl(
    p_task_type TEXT DEFAULT NULL,
    p_only_corrections BOOLEAN DEFAULT FALSE
) RETURNS TABLE(jsonl_line TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT json_build_object(
        'instruction', te.instruction,
        'input', te.input,
        'output', te.output,
        'task_type', te.task_type,
        'is_correction', te.is_correction
    )::TEXT
    FROM training_examples te
    WHERE te.include_in_training = TRUE
      AND (p_task_type IS NULL OR te.task_type = p_task_type)
      AND (NOT p_only_corrections OR te.is_correction = TRUE);
    
    -- Mark as exported
    UPDATE training_examples 
    SET exported_at = NOW()
    WHERE include_in_training = TRUE
      AND (p_task_type IS NULL OR task_type = p_task_type)
      AND (NOT p_only_corrections OR is_correction = TRUE);
END;
$$ LANGUAGE plpgsql;

-- Update database statistics view to include training tables
CREATE OR REPLACE VIEW database_statistics AS
SELECT 'library_entries' as table_name, COUNT(*) as row_count FROM library_entries
UNION ALL
SELECT 'kg_nodes', COUNT(*) FROM kg_nodes
UNION ALL
SELECT 'kg_relationships', COUNT(*) FROM kg_relationships
UNION ALL
SELECT 'training_interactions', COUNT(*) FROM training_interactions
UNION ALL
SELECT 'training_examples', COUNT(*) FROM training_examples
UNION ALL
SELECT 'learning_log', COUNT(*) FROM learning_log
ORDER BY table_name;
