-- Migration 020: User Attachments (Student Notebook)
--
-- Implements "attachments are pointers, not copies" model.
-- Scoped to: user + team + conversation. Private by default.
--
-- Supports the "student notebook open while asking the teacher" model.

BEGIN;

-- =============================================================================
-- PART 1: ENUMS
-- =============================================================================

-- Provider enum: where the attachment comes from
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'attachment_provider') THEN
        CREATE TYPE attachment_provider AS ENUM (
            'github',
            'google_drive',
            'discord',
            'notion',
            'url',
            'local_file'
        );
    END IF;
END $$;

-- Resource type enum: what kind of resource it is
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'attachment_resource_type') THEN
        CREATE TYPE attachment_resource_type AS ENUM (
            'repo',
            'folder',
            'file',
            'channel',
            'thread',
            'issue',
            'doc',
            'page',
            'url'
        );
    END IF;
END $$;

-- =============================================================================
-- PART 2: USER ATTACHMENTS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS user_attachments (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Ownership & Scoping (private by default)
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    team_id UUID,  -- Optional team scope (no FK for now - teams table may not exist)
    conversation_id UUID NOT NULL,  -- Scoped to specific conversation

    -- Provider info
    provider attachment_provider NOT NULL,
    resource_type attachment_resource_type NOT NULL,

    -- Resource identification (pointers, not copies)
    resource_id TEXT NOT NULL,              -- Provider-native ID (repo full_name, drive file id, etc.)
    resource_path TEXT,                     -- Human-readable path or name
    display_name TEXT NOT NULL,             -- What user sees

    -- Optional versioning
    ref TEXT,                               -- Branch, commit SHA, version, etc.

    -- Metadata (for future use)
    permissions_snapshot JSONB,             -- Cache of permissions at attach time
    provider_metadata JSONB,                -- Provider-specific data (stars, last_push, etc.)

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_used_at TIMESTAMPTZ DEFAULT NOW(),

    -- State
    is_active BOOLEAN DEFAULT true NOT NULL,  -- Is it currently attached to conversation?

    -- Constraints
    CONSTRAINT unique_attachment_per_conversation
        UNIQUE (user_id, conversation_id, provider, resource_id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_user_attachments_user_id
    ON user_attachments(user_id);
CREATE INDEX IF NOT EXISTS idx_user_attachments_conversation
    ON user_attachments(user_id, conversation_id)
    WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_user_attachments_recent
    ON user_attachments(user_id, last_used_at DESC);

-- =============================================================================
-- PART 3: ROW LEVEL SECURITY
-- =============================================================================

ALTER TABLE user_attachments ENABLE ROW LEVEL SECURITY;

-- Users can only see their own attachments (private by default)
CREATE POLICY user_attachments_select_own ON user_attachments
    FOR SELECT
    USING (user_id = auth.uid());

-- Users can only insert their own attachments
CREATE POLICY user_attachments_insert_own ON user_attachments
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Users can only update their own attachments
CREATE POLICY user_attachments_update_own ON user_attachments
    FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Users can only delete their own attachments
CREATE POLICY user_attachments_delete_own ON user_attachments
    FOR DELETE
    USING (user_id = auth.uid());

-- =============================================================================
-- PART 4: USER OAUTH TOKENS (for provider connections)
-- =============================================================================

CREATE TABLE IF NOT EXISTS user_oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Provider info
    provider attachment_provider NOT NULL,

    -- Tokens (encrypted at rest by Supabase)
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,

    -- Scope info
    scopes TEXT[],

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- One token per provider per user
    CONSTRAINT unique_user_provider UNIQUE (user_id, provider)
);

-- RLS for oauth tokens (very strict - only user can see their own)
ALTER TABLE user_oauth_tokens ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_oauth_tokens_select_own ON user_oauth_tokens
    FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY user_oauth_tokens_insert_own ON user_oauth_tokens
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY user_oauth_tokens_update_own ON user_oauth_tokens
    FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

CREATE POLICY user_oauth_tokens_delete_own ON user_oauth_tokens
    FOR DELETE
    USING (user_id = auth.uid());

-- =============================================================================
-- PART 5: HELPER FUNCTIONS
-- =============================================================================

-- Function to attach a resource to a conversation
CREATE OR REPLACE FUNCTION attach_resource(
    p_user_id UUID,
    p_team_id UUID,
    p_conversation_id UUID,
    p_provider attachment_provider,
    p_resource_type attachment_resource_type,
    p_resource_id TEXT,
    p_resource_path TEXT,
    p_display_name TEXT,
    p_ref TEXT DEFAULT NULL,
    p_provider_metadata JSONB DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_attachment_id UUID;
BEGIN
    INSERT INTO user_attachments (
        user_id,
        team_id,
        conversation_id,
        provider,
        resource_type,
        resource_id,
        resource_path,
        display_name,
        ref,
        provider_metadata,
        is_active
    ) VALUES (
        p_user_id,
        p_team_id,
        p_conversation_id,
        p_provider,
        p_resource_type,
        p_resource_id,
        p_resource_path,
        p_display_name,
        p_ref,
        p_provider_metadata,
        true
    )
    ON CONFLICT (user_id, conversation_id, provider, resource_id)
    DO UPDATE SET
        is_active = true,
        last_used_at = NOW(),
        ref = COALESCE(EXCLUDED.ref, user_attachments.ref),
        provider_metadata = COALESCE(EXCLUDED.provider_metadata, user_attachments.provider_metadata)
    RETURNING id INTO v_attachment_id;

    RETURN v_attachment_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to detach (soft-delete) a resource from a conversation
CREATE OR REPLACE FUNCTION detach_resource(
    p_user_id UUID,
    p_attachment_id UUID
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE user_attachments
    SET is_active = false
    WHERE id = p_attachment_id
      AND user_id = p_user_id;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user's recent attachments (across conversations)
CREATE OR REPLACE FUNCTION get_recent_attachments(
    p_user_id UUID,
    p_limit INT DEFAULT 10
) RETURNS TABLE (
    id UUID,
    provider attachment_provider,
    resource_type attachment_resource_type,
    resource_id TEXT,
    resource_path TEXT,
    display_name TEXT,
    ref TEXT,
    last_used_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT ON (ua.provider, ua.resource_id)
        ua.id,
        ua.provider,
        ua.resource_type,
        ua.resource_id,
        ua.resource_path,
        ua.display_name,
        ua.ref,
        ua.last_used_at
    FROM user_attachments ua
    WHERE ua.user_id = p_user_id
    ORDER BY ua.provider, ua.resource_id, ua.last_used_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user has connected a provider
CREATE OR REPLACE FUNCTION has_provider_connection(
    p_user_id UUID,
    p_provider attachment_provider
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM user_oauth_tokens
        WHERE user_id = p_user_id
          AND provider = p_provider
          AND (token_expires_at IS NULL OR token_expires_at > NOW())
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- PART 6: COMMENTS
-- =============================================================================

COMMENT ON TABLE user_attachments IS
'User-scoped pointers to external resources (repos, files, docs). Private by default.';

COMMENT ON COLUMN user_attachments.resource_id IS
'Provider-native identifier. For GitHub: "owner/repo". For Drive: file ID.';

COMMENT ON COLUMN user_attachments.ref IS
'Optional version reference: branch name, commit SHA, or document version.';

COMMENT ON COLUMN user_attachments.is_active IS
'Whether attachment is currently active in the conversation. False = soft-deleted.';

COMMENT ON TABLE user_oauth_tokens IS
'OAuth tokens for external provider connections. One per provider per user.';

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Migration 020: User Attachments';
    RAISE NOTICE '===========================================';
    RAISE NOTICE '  - user_attachments table created';
    RAISE NOTICE '  - user_oauth_tokens table created';
    RAISE NOTICE '  - RLS policies applied (private by default)';
    RAISE NOTICE '  - attach_resource function created';
    RAISE NOTICE '  - detach_resource function created';
    RAISE NOTICE '  - get_recent_attachments function created';
    RAISE NOTICE '  - has_provider_connection function created';
END $$;

COMMIT;
