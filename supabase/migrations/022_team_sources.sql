-- Migration 022: Team Sources (Collective Ingestion)
--
-- Implements extraction pipelines for Admin surface.
-- These are team/org-level sources that feed the collective knowledge base.
--
-- Supports: Discord, Notion, Google Drive, GitHub organizations

BEGIN;

-- =============================================================================
-- PART 1: ENUMS
-- =============================================================================

-- Source type enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'team_source_type') THEN
        CREATE TYPE team_source_type AS ENUM (
            'github_org',
            'github_repo',
            'notion_workspace',
            'notion_database',
            'gdrive_folder',
            'gdrive_shared_drive',
            'discord_server',
            'discord_channel',
            'url_list'
        );
    END IF;
END $$;

-- Crawl status enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'crawl_status') THEN
        CREATE TYPE crawl_status AS ENUM (
            'pending',
            'crawling',
            'completed',
            'failed',
            'paused'
        );
    END IF;
END $$;

-- =============================================================================
-- PART 2: TEAM SOURCES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS team_sources (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Ownership
    team_id UUID,  -- Optional team scope (null = org-wide)
    created_by UUID REFERENCES auth.users(id),

    -- Source identification
    source_type team_source_type NOT NULL,
    name TEXT NOT NULL,                     -- Human-readable name
    description TEXT,                       -- What this source contains

    -- Provider-specific configuration
    -- For GitHub: { org: "PROVES", include_repos: ["*"], exclude_repos: [] }
    -- For Notion: { workspace_id: "...", root_page_id: "..." }
    -- For Google Drive: { folder_id: "...", shared_drive_id: "..." }
    -- For Discord: { server_id: "...", channel_ids: [...] }
    source_config JSONB NOT NULL DEFAULT '{}',

    -- Authentication
    -- References the team's oauth token or API key
    auth_token_id UUID,  -- Reference to a shared team token
    auth_method TEXT DEFAULT 'oauth',  -- 'oauth', 'api_key', 'service_account'

    -- Crawl configuration
    crawl_schedule TEXT,            -- Cron expression (e.g., '0 */6 * * *' for every 6 hours)
    crawl_depth INT DEFAULT 3,      -- How deep to crawl (for hierarchical sources)
    include_patterns TEXT[],        -- Glob patterns to include
    exclude_patterns TEXT[],        -- Glob patterns to exclude

    -- Content filtering
    file_types TEXT[],              -- File extensions to process (null = all)
    max_file_size_mb INT DEFAULT 10,

    -- State
    is_active BOOLEAN DEFAULT true NOT NULL,

    -- Last crawl info
    last_crawl_at TIMESTAMPTZ,
    last_crawl_status crawl_status,
    last_crawl_error TEXT,
    last_crawl_stats JSONB,         -- { items_found: N, items_processed: N, errors: [] }

    -- Metadata
    item_count INT DEFAULT 0,       -- Total items discovered
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_team_sources_team ON team_sources(team_id);
CREATE INDEX IF NOT EXISTS idx_team_sources_type ON team_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_team_sources_active ON team_sources(is_active) WHERE is_active = true;

-- =============================================================================
-- PART 3: CRAWL JOBS TABLE (Ingestion Queue)
-- =============================================================================

CREATE TABLE IF NOT EXISTS crawl_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Reference to source
    source_id UUID NOT NULL REFERENCES team_sources(id) ON DELETE CASCADE,

    -- Job state
    status crawl_status NOT NULL DEFAULT 'pending',
    priority INT DEFAULT 0,         -- Higher = run first

    -- Execution tracking
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Progress
    items_found INT DEFAULT 0,
    items_processed INT DEFAULT 0,
    items_failed INT DEFAULT 0,
    current_item TEXT,              -- What's being processed now

    -- Error handling
    error_message TEXT,
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,

    -- Metadata
    triggered_by TEXT,              -- 'schedule', 'manual', 'webhook'
    job_metadata JSONB,             -- Additional context

    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_source ON crawl_jobs(source_id);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_status ON crawl_jobs(status) WHERE status IN ('pending', 'crawling');
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_pending ON crawl_jobs(priority DESC, created_at ASC) WHERE status = 'pending';

-- =============================================================================
-- PART 4: CRAWL ITEMS TABLE (What was discovered)
-- =============================================================================

CREATE TABLE IF NOT EXISTS crawl_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- References
    source_id UUID NOT NULL REFERENCES team_sources(id) ON DELETE CASCADE,
    job_id UUID REFERENCES crawl_jobs(id) ON DELETE SET NULL,

    -- Item identification
    external_id TEXT NOT NULL,      -- Provider's ID for this item
    external_url TEXT,              -- URL to view in provider
    item_path TEXT,                 -- Path within source (e.g., "docs/getting-started.md")
    item_type TEXT,                 -- 'file', 'page', 'message', 'issue', etc.

    -- Content info
    title TEXT,
    content_hash TEXT,              -- Hash to detect changes
    content_size_bytes INT,

    -- Processing state
    processed_at TIMESTAMPTZ,
    extraction_id UUID,             -- Link to extractions table if processed

    -- Change tracking
    first_seen_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_modified_at TIMESTAMPTZ,   -- From provider
    is_deleted BOOLEAN DEFAULT false,

    -- Metadata from provider
    provider_metadata JSONB,

    CONSTRAINT unique_item_per_source UNIQUE (source_id, external_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_crawl_items_source ON crawl_items(source_id);
CREATE INDEX IF NOT EXISTS idx_crawl_items_unprocessed ON crawl_items(source_id, processed_at)
    WHERE processed_at IS NULL AND is_deleted = false;
CREATE INDEX IF NOT EXISTS idx_crawl_items_external_id ON crawl_items(external_id);

-- =============================================================================
-- PART 5: ROW LEVEL SECURITY
-- =============================================================================

ALTER TABLE team_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE crawl_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE crawl_items ENABLE ROW LEVEL SECURITY;

-- For now, allow authenticated users to view sources (admin-only in production)
-- TODO: Add proper team membership checks
CREATE POLICY team_sources_select ON team_sources
    FOR SELECT TO authenticated
    USING (true);

CREATE POLICY team_sources_insert ON team_sources
    FOR INSERT TO authenticated
    WITH CHECK (true);

CREATE POLICY team_sources_update ON team_sources
    FOR UPDATE TO authenticated
    USING (true);

CREATE POLICY crawl_jobs_select ON crawl_jobs
    FOR SELECT TO authenticated
    USING (true);

CREATE POLICY crawl_items_select ON crawl_items
    FOR SELECT TO authenticated
    USING (true);

-- =============================================================================
-- PART 6: HELPER FUNCTIONS
-- =============================================================================

-- Create a new team source
CREATE OR REPLACE FUNCTION create_team_source(
    p_name TEXT,
    p_source_type team_source_type,
    p_source_config JSONB,
    p_team_id UUID DEFAULT NULL,
    p_description TEXT DEFAULT NULL,
    p_crawl_schedule TEXT DEFAULT NULL,
    p_include_patterns TEXT[] DEFAULT NULL,
    p_exclude_patterns TEXT[] DEFAULT ARRAY['**/node_modules/**', '**/.git/**', '**/build/**']
) RETURNS UUID AS $$
DECLARE
    v_source_id UUID;
BEGIN
    INSERT INTO team_sources (
        team_id,
        created_by,
        source_type,
        name,
        description,
        source_config,
        crawl_schedule,
        include_patterns,
        exclude_patterns
    ) VALUES (
        p_team_id,
        auth.uid(),
        p_source_type,
        p_name,
        p_description,
        p_source_config,
        p_crawl_schedule,
        p_include_patterns,
        p_exclude_patterns
    )
    RETURNING id INTO v_source_id;

    RETURN v_source_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger a crawl job for a source
CREATE OR REPLACE FUNCTION trigger_crawl(
    p_source_id UUID,
    p_triggered_by TEXT DEFAULT 'manual',
    p_priority INT DEFAULT 0
) RETURNS UUID AS $$
DECLARE
    v_job_id UUID;
BEGIN
    -- Check if source exists and is active
    IF NOT EXISTS (SELECT 1 FROM team_sources WHERE id = p_source_id AND is_active = true) THEN
        RAISE EXCEPTION 'Source not found or inactive';
    END IF;

    -- Create the job
    INSERT INTO crawl_jobs (
        source_id,
        status,
        priority,
        triggered_by
    ) VALUES (
        p_source_id,
        'pending',
        p_priority,
        p_triggered_by
    )
    RETURNING id INTO v_job_id;

    RETURN v_job_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get next pending crawl job (for workers)
CREATE OR REPLACE FUNCTION claim_next_crawl_job()
RETURNS TABLE (
    job_id UUID,
    source_id UUID,
    source_type team_source_type,
    source_config JSONB,
    include_patterns TEXT[],
    exclude_patterns TEXT[]
) AS $$
DECLARE
    v_job_id UUID;
BEGIN
    -- Find and claim the highest priority pending job
    UPDATE crawl_jobs cj
    SET status = 'crawling',
        started_at = NOW()
    WHERE cj.id = (
        SELECT id FROM crawl_jobs
        WHERE status = 'pending'
        ORDER BY priority DESC, created_at ASC
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    )
    RETURNING cj.id INTO v_job_id;

    IF v_job_id IS NULL THEN
        RETURN;
    END IF;

    -- Return job with source config
    RETURN QUERY
    SELECT
        cj.id,
        cj.source_id,
        ts.source_type,
        ts.source_config,
        ts.include_patterns,
        ts.exclude_patterns
    FROM crawl_jobs cj
    JOIN team_sources ts ON ts.id = cj.source_id
    WHERE cj.id = v_job_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Complete a crawl job
CREATE OR REPLACE FUNCTION complete_crawl_job(
    p_job_id UUID,
    p_status crawl_status,
    p_items_found INT DEFAULT 0,
    p_items_processed INT DEFAULT 0,
    p_items_failed INT DEFAULT 0,
    p_error_message TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE crawl_jobs
    SET status = p_status,
        completed_at = NOW(),
        items_found = p_items_found,
        items_processed = p_items_processed,
        items_failed = p_items_failed,
        error_message = p_error_message
    WHERE id = p_job_id;

    -- Update source stats
    UPDATE team_sources
    SET last_crawl_at = NOW(),
        last_crawl_status = p_status,
        last_crawl_error = p_error_message,
        last_crawl_stats = jsonb_build_object(
            'items_found', p_items_found,
            'items_processed', p_items_processed,
            'items_failed', p_items_failed
        ),
        item_count = (
            SELECT COUNT(*) FROM crawl_items
            WHERE source_id = team_sources.id AND is_deleted = false
        ),
        updated_at = NOW()
    WHERE id = (SELECT source_id FROM crawl_jobs WHERE id = p_job_id);

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get ingestion stats for dashboard
CREATE OR REPLACE FUNCTION get_ingestion_stats()
RETURNS TABLE (
    pending_jobs INT,
    running_jobs INT,
    completed_today INT,
    failed_today INT,
    total_sources INT,
    active_sources INT,
    total_items INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*)::INT FROM crawl_jobs WHERE status = 'pending'),
        (SELECT COUNT(*)::INT FROM crawl_jobs WHERE status = 'crawling'),
        (SELECT COUNT(*)::INT FROM crawl_jobs WHERE status = 'completed' AND completed_at > CURRENT_DATE),
        (SELECT COUNT(*)::INT FROM crawl_jobs WHERE status = 'failed' AND completed_at > CURRENT_DATE),
        (SELECT COUNT(*)::INT FROM team_sources),
        (SELECT COUNT(*)::INT FROM team_sources WHERE is_active = true),
        (SELECT COUNT(*)::INT FROM crawl_items WHERE is_deleted = false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- PART 7: TRIGGERS
-- =============================================================================

-- Auto-update updated_at on team_sources
CREATE OR REPLACE FUNCTION update_team_sources_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS team_sources_updated_at ON team_sources;
CREATE TRIGGER team_sources_updated_at
    BEFORE UPDATE ON team_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_team_sources_timestamp();

-- =============================================================================
-- PART 8: COMMENTS
-- =============================================================================

COMMENT ON TABLE team_sources IS
'Team/org-level sources for collective knowledge ingestion. Managed by admins.';

COMMENT ON TABLE crawl_jobs IS
'Queue of crawl jobs to be processed. Workers claim jobs via claim_next_crawl_job().';

COMMENT ON TABLE crawl_items IS
'Items discovered during crawls. Links to extractions when processed.';

COMMENT ON COLUMN team_sources.source_config IS
'Provider-specific configuration as JSONB. Schema varies by source_type.';

COMMENT ON COLUMN team_sources.crawl_schedule IS
'Cron expression for scheduled crawls. NULL means manual-only.';

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Migration 022: Team Sources';
    RAISE NOTICE '===========================================';
    RAISE NOTICE '  - team_sources table created';
    RAISE NOTICE '  - crawl_jobs table created';
    RAISE NOTICE '  - crawl_items table created';
    RAISE NOTICE '  - create_team_source function created';
    RAISE NOTICE '  - trigger_crawl function created';
    RAISE NOTICE '  - claim_next_crawl_job function created';
    RAISE NOTICE '  - complete_crawl_job function created';
    RAISE NOTICE '  - get_ingestion_stats function created';
END $$;

COMMIT;
