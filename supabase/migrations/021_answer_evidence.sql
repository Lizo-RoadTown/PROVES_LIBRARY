-- Migration 021: Answer Evidence Tracking
--
-- Tracks what sources were used to generate each answer in the Ask surface.
-- Enables auditability and the "evidence strip" UI pattern.
--
-- Key design:
-- - Links answers to sources (collective library or user attachments)
-- - Stores snapshot of content at answer time (for citation stability)
-- - Tracks confidence and freshness metrics

BEGIN;

-- =============================================================================
-- PART 1: ENUMS
-- =============================================================================

-- Source type enum: where the evidence came from
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'evidence_source_type') THEN
        CREATE TYPE evidence_source_type AS ENUM (
            'collective',   -- From collective library (core_entities)
            'notebook'      -- From user's attached files
        );
    END IF;
END $$;

-- Confidence level enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'confidence_level') THEN
        CREATE TYPE confidence_level AS ENUM (
            'high',
            'medium',
            'low'
        );
    END IF;
END $$;

-- =============================================================================
-- PART 2: CONVERSATIONS TABLE (for tracking chat sessions)
-- =============================================================================

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    team_id UUID,  -- Optional team scope

    -- Metadata
    title TEXT,  -- Auto-generated or user-provided title

    -- Scope settings at conversation creation
    scope_collective BOOLEAN DEFAULT true NOT NULL,
    scope_notebook BOOLEAN DEFAULT true NOT NULL,
    mission_filter TEXT,
    domain_filter TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- State
    is_active BOOLEAN DEFAULT true NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_conversations_user_id
    ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_recent
    ON conversations(user_id, updated_at DESC)
    WHERE is_active = true;

-- RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY conversations_select_own ON conversations
    FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY conversations_insert_own ON conversations
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY conversations_update_own ON conversations
    FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

CREATE POLICY conversations_delete_own ON conversations
    FOR DELETE
    USING (user_id = auth.uid());

-- =============================================================================
-- PART 3: MESSAGES TABLE (for chat history)
-- =============================================================================

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Message content
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
    ON messages(conversation_id, created_at);

-- RLS (inherit from conversation ownership)
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY messages_select_own ON messages
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = messages.conversation_id
            AND c.user_id = auth.uid()
        )
    );

CREATE POLICY messages_insert_own ON messages
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = messages.conversation_id
            AND c.user_id = auth.uid()
        )
    );

-- =============================================================================
-- PART 4: ANSWER EVIDENCE TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS answer_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to conversation and message
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,

    -- Source identification
    source_type evidence_source_type NOT NULL,
    source_id UUID,  -- core_entities.id or user_attachments.id

    -- Snapshot at answer time (for citation stability)
    source_title TEXT NOT NULL,
    source_excerpt TEXT,  -- Relevant snippet used
    source_url TEXT,      -- Link to original if available
    source_metadata JSONB,  -- Additional context (captured_at, etc.)

    -- Relevance metrics
    relevance_score FLOAT,  -- How relevant this source was (0-1)

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_answer_evidence_message_id
    ON answer_evidence(message_id);
CREATE INDEX IF NOT EXISTS idx_answer_evidence_conversation_id
    ON answer_evidence(conversation_id);
CREATE INDEX IF NOT EXISTS idx_answer_evidence_source
    ON answer_evidence(source_type, source_id);

-- RLS (inherit from conversation ownership)
ALTER TABLE answer_evidence ENABLE ROW LEVEL SECURITY;

CREATE POLICY answer_evidence_select_own ON answer_evidence
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = answer_evidence.conversation_id
            AND c.user_id = auth.uid()
        )
    );

CREATE POLICY answer_evidence_insert_own ON answer_evidence
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM conversations c
            WHERE c.id = answer_evidence.conversation_id
            AND c.user_id = auth.uid()
        )
    );

-- =============================================================================
-- PART 5: ANSWER METADATA TABLE (confidence, freshness per answer)
-- =============================================================================

CREATE TABLE IF NOT EXISTS answer_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE UNIQUE,

    -- Counts
    collective_source_count INT DEFAULT 0 NOT NULL,
    notebook_source_count INT DEFAULT 0 NOT NULL,

    -- Quality metrics
    confidence confidence_level DEFAULT 'medium' NOT NULL,
    freshness_days INT,  -- How old the freshest source is

    -- Model info (since user brings their own model)
    model_provider TEXT,  -- 'openai', 'anthropic', etc.
    model_name TEXT,      -- 'gpt-4', 'claude-3', etc.

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Index
CREATE INDEX IF NOT EXISTS idx_answer_metadata_message_id
    ON answer_metadata(message_id);

-- RLS (inherit from message ownership)
ALTER TABLE answer_metadata ENABLE ROW LEVEL SECURITY;

CREATE POLICY answer_metadata_select_own ON answer_metadata
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            WHERE m.id = answer_metadata.message_id
            AND c.user_id = auth.uid()
        )
    );

CREATE POLICY answer_metadata_insert_own ON answer_metadata
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM messages m
            JOIN conversations c ON c.id = m.conversation_id
            WHERE m.id = answer_metadata.message_id
            AND c.user_id = auth.uid()
        )
    );

-- =============================================================================
-- PART 6: HELPER FUNCTIONS
-- =============================================================================

-- Function to record evidence for an answer
CREATE OR REPLACE FUNCTION record_answer_evidence(
    p_conversation_id UUID,
    p_message_id UUID,
    p_sources JSONB  -- Array of {type, source_id, title, excerpt, url, metadata, relevance_score}
) RETURNS INT AS $$
DECLARE
    v_source JSONB;
    v_count INT := 0;
BEGIN
    FOR v_source IN SELECT * FROM jsonb_array_elements(p_sources)
    LOOP
        INSERT INTO answer_evidence (
            conversation_id,
            message_id,
            source_type,
            source_id,
            source_title,
            source_excerpt,
            source_url,
            source_metadata,
            relevance_score
        ) VALUES (
            p_conversation_id,
            p_message_id,
            (v_source->>'type')::evidence_source_type,
            (v_source->>'source_id')::UUID,
            v_source->>'title',
            v_source->>'excerpt',
            v_source->>'url',
            v_source->'metadata',
            (v_source->>'relevance_score')::FLOAT
        );
        v_count := v_count + 1;
    END LOOP;

    RETURN v_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get evidence for a message
CREATE OR REPLACE FUNCTION get_answer_evidence(
    p_message_id UUID
) RETURNS TABLE (
    id UUID,
    source_type evidence_source_type,
    source_id UUID,
    source_title TEXT,
    source_excerpt TEXT,
    source_url TEXT,
    source_metadata JSONB,
    relevance_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ae.id,
        ae.source_type,
        ae.source_id,
        ae.source_title,
        ae.source_excerpt,
        ae.source_url,
        ae.source_metadata,
        ae.relevance_score
    FROM answer_evidence ae
    WHERE ae.message_id = p_message_id
    ORDER BY ae.relevance_score DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to create or get a conversation
CREATE OR REPLACE FUNCTION get_or_create_conversation(
    p_user_id UUID,
    p_conversation_id UUID DEFAULT NULL,
    p_title TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_conversation_id UUID;
BEGIN
    -- If ID provided and exists, return it
    IF p_conversation_id IS NOT NULL THEN
        SELECT id INTO v_conversation_id
        FROM conversations
        WHERE id = p_conversation_id AND user_id = p_user_id;

        IF v_conversation_id IS NOT NULL THEN
            RETURN v_conversation_id;
        END IF;
    END IF;

    -- Create new conversation
    INSERT INTO conversations (user_id, title)
    VALUES (p_user_id, COALESCE(p_title, 'New Conversation'))
    RETURNING id INTO v_conversation_id;

    RETURN v_conversation_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to add a message to a conversation
CREATE OR REPLACE FUNCTION add_message(
    p_conversation_id UUID,
    p_role TEXT,
    p_content TEXT
) RETURNS UUID AS $$
DECLARE
    v_message_id UUID;
BEGIN
    INSERT INTO messages (conversation_id, role, content)
    VALUES (p_conversation_id, p_role, p_content)
    RETURNING id INTO v_message_id;

    -- Update conversation timestamp
    UPDATE conversations
    SET updated_at = NOW()
    WHERE id = p_conversation_id;

    RETURN v_message_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- PART 7: COMMENTS
-- =============================================================================

COMMENT ON TABLE conversations IS
'Chat sessions for the Ask surface. Scoped to user.';

COMMENT ON TABLE messages IS
'Individual messages within a conversation.';

COMMENT ON TABLE answer_evidence IS
'Sources used to generate each answer. Enables the evidence strip UI.';

COMMENT ON TABLE answer_metadata IS
'Aggregated metadata for each answer (confidence, source counts, model info).';

COMMENT ON COLUMN answer_evidence.source_excerpt IS
'Snapshot of the relevant text at answer time. Ensures citation stability.';

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Migration 021: Answer Evidence Tracking';
    RAISE NOTICE '===========================================';
    RAISE NOTICE '  - conversations table created';
    RAISE NOTICE '  - messages table created';
    RAISE NOTICE '  - answer_evidence table created';
    RAISE NOTICE '  - answer_metadata table created';
    RAISE NOTICE '  - RLS policies applied';
    RAISE NOTICE '  - Helper functions created';
END $$;

COMMIT;
