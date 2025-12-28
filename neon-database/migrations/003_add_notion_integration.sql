-- Migration: Add Notion Integration with Sync Tracking
-- Date: 2025-12-27
-- Purpose: Enable bidirectional Notion sync with triggers and status tracking

BEGIN;

-- ============================================================================
-- PART 1: NEW TABLES FOR ERRORS AND REPORTS
-- ============================================================================

-- 1.1: Curator Errors - Track all errors for logging to Notion
CREATE TABLE IF NOT EXISTS curator_errors (
    id SERIAL PRIMARY KEY,

    -- Error details
    url TEXT NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    error_context JSONB,  -- Additional context (batch info, etc.)

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Notion sync tracking
    notion_page_id TEXT,  -- Notion page ID after sync
    notion_synced_at TIMESTAMPTZ,  -- When successfully synced
    notion_last_sync_attempt TIMESTAMPTZ,  -- Last attempt (even if failed)
    notion_sync_error TEXT,  -- Error message if sync failed

    -- Indexes
    CONSTRAINT unique_error_per_url_time UNIQUE(url, created_at)
);

CREATE INDEX idx_curator_errors_created ON curator_errors(created_at DESC);
CREATE INDEX idx_curator_errors_notion_sync ON curator_errors(notion_synced_at)
    WHERE notion_synced_at IS NULL;  -- Find unsynced errors

COMMENT ON TABLE curator_errors IS
    'Curator agent errors logged for Notion integration';

COMMENT ON COLUMN curator_errors.notion_page_id IS
    'Notion page ID where this error was logged (for linking)';

-- 1.2: Curator Reports - Completion summaries after batch runs
CREATE TABLE IF NOT EXISTS curator_reports (
    id SERIAL PRIMARY KEY,

    -- Report details
    run_date TIMESTAMPTZ DEFAULT NOW(),
    urls_processed INTEGER DEFAULT 0,
    urls_successful INTEGER DEFAULT 0,
    urls_failed INTEGER DEFAULT 0,
    total_extractions INTEGER DEFAULT 0,

    -- Report content
    summary TEXT,
    langsmith_trace_url TEXT,
    run_details JSONB,  -- Additional metrics

    -- Reference to pipeline run
    pipeline_run_id UUID REFERENCES pipeline_runs(id),

    -- Notion sync tracking
    notion_page_id TEXT,
    notion_synced_at TIMESTAMPTZ,
    notion_last_sync_attempt TIMESTAMPTZ,
    notion_sync_error TEXT
);

CREATE INDEX idx_curator_reports_date ON curator_reports(run_date DESC);
CREATE INDEX idx_curator_reports_notion_sync ON curator_reports(notion_synced_at)
    WHERE notion_synced_at IS NULL;  -- Find unsynced reports

COMMENT ON TABLE curator_reports IS
    'Curator batch completion reports for Notion integration';

-- ============================================================================
-- PART 2: ADD NOTION TRACKING TO EXISTING TABLES
-- ============================================================================

-- 2.1: staging_extractions - Track Notion sync status
ALTER TABLE staging_extractions
    ADD COLUMN IF NOT EXISTS notion_page_id TEXT,
    ADD COLUMN IF NOT EXISTS notion_synced_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS notion_last_sync_attempt TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS notion_sync_error TEXT;

CREATE INDEX IF NOT EXISTS idx_staging_extractions_notion_sync
    ON staging_extractions(notion_synced_at)
    WHERE notion_synced_at IS NULL AND status = 'pending';

COMMENT ON COLUMN staging_extractions.notion_page_id IS
    'Notion page ID for this extraction (enables bidirectional sync)';

COMMENT ON COLUMN staging_extractions.notion_synced_at IS
    'Timestamp when this extraction was successfully pushed to Notion';

-- ============================================================================
-- PART 3: NOTIFICATION FUNCTIONS (Using pg_notify)
-- ============================================================================

-- 3.1: Notify when new extraction is inserted
CREATE OR REPLACE FUNCTION notify_new_extraction()
RETURNS TRIGGER AS $$
BEGIN
    -- Only notify if not yet synced to Notion
    IF NEW.notion_synced_at IS NULL THEN
        PERFORM pg_notify(
            'notion_sync_extraction',
            json_build_object(
                'extraction_id', NEW.extraction_id,
                'action', 'insert'
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3.2: Notify when new error is inserted
CREATE OR REPLACE FUNCTION notify_new_error()
RETURNS TRIGGER AS $$
BEGIN
    -- Only notify if not yet synced to Notion
    IF NEW.notion_synced_at IS NULL THEN
        PERFORM pg_notify(
            'notion_sync_error',
            json_build_object(
                'error_id', NEW.id,
                'action', 'insert'
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3.3: Notify when new report is inserted
CREATE OR REPLACE FUNCTION notify_new_report()
RETURNS TRIGGER AS $$
BEGIN
    -- Only notify if not yet synced to Notion
    IF NEW.notion_synced_at IS NULL THEN
        PERFORM pg_notify(
            'notion_sync_report',
            json_build_object(
                'report_id', NEW.id,
                'action', 'insert'
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3.4: Notify when URL queue is empty
CREATE OR REPLACE FUNCTION check_url_queue_empty()
RETURNS TRIGGER AS $$
DECLARE
    pending_count INTEGER;
BEGIN
    -- Count pending URLs
    SELECT COUNT(*) INTO pending_count
    FROM urls_to_process
    WHERE status = 'pending';

    -- If queue is now empty (and wasn't before), notify
    IF pending_count = 0 AND OLD.status = 'pending' AND NEW.status != 'pending' THEN
        PERFORM pg_notify(
            'notion_queue_empty',
            json_build_object(
                'timestamp', NOW(),
                'message', 'URL queue is empty - time to run find_good_urls.py'
            )::text
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 4: CREATE TRIGGERS
-- ============================================================================

-- 4.1: Trigger on new extraction
DROP TRIGGER IF EXISTS trigger_notify_new_extraction ON staging_extractions;
CREATE TRIGGER trigger_notify_new_extraction
    AFTER INSERT ON staging_extractions
    FOR EACH ROW
    EXECUTE FUNCTION notify_new_extraction();

-- 4.2: Trigger on new error
DROP TRIGGER IF EXISTS trigger_notify_new_error ON curator_errors;
CREATE TRIGGER trigger_notify_new_error
    AFTER INSERT ON curator_errors
    FOR EACH ROW
    EXECUTE FUNCTION notify_new_error();

-- 4.3: Trigger on new report
DROP TRIGGER IF EXISTS trigger_notify_new_report ON curator_reports;
CREATE TRIGGER trigger_notify_new_report
    AFTER INSERT ON curator_reports
    FOR EACH ROW
    EXECUTE FUNCTION notify_new_report();

-- 4.4: Trigger to check queue status
DROP TRIGGER IF EXISTS trigger_check_url_queue ON urls_to_process;
CREATE TRIGGER trigger_check_url_queue
    AFTER UPDATE OF status ON urls_to_process
    FOR EACH ROW
    EXECUTE FUNCTION check_url_queue_empty();

-- ============================================================================
-- PART 5: UTILITY VIEWS
-- ============================================================================

-- 5.1: View unsynced items across all tables
CREATE OR REPLACE VIEW notion_sync_status AS
SELECT
    'extraction' as item_type,
    extraction_id::text as item_id,
    candidate_key as item_name,
    created_at,
    notion_synced_at,
    notion_sync_error
FROM staging_extractions
WHERE notion_synced_at IS NULL AND status = 'pending'

UNION ALL

SELECT
    'error' as item_type,
    id::text as item_id,
    url as item_name,
    created_at,
    notion_synced_at,
    notion_sync_error
FROM curator_errors
WHERE notion_synced_at IS NULL

UNION ALL

SELECT
    'report' as item_type,
    id::text as item_id,
    'Run Report' as item_name,
    run_date as created_at,
    notion_synced_at,
    notion_sync_error
FROM curator_reports
WHERE notion_synced_at IS NULL

ORDER BY created_at DESC;

COMMENT ON VIEW notion_sync_status IS
    'Overview of all items awaiting Notion sync across all tables';

-- ============================================================================
-- PART 6: HELPER FUNCTIONS FOR WEBHOOK SERVER
-- ============================================================================

-- 6.1: Mark extraction as synced to Notion
CREATE OR REPLACE FUNCTION mark_extraction_synced(
    p_extraction_id UUID,
    p_notion_page_id TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE staging_extractions
    SET
        notion_page_id = p_notion_page_id,
        notion_synced_at = NOW(),
        notion_last_sync_attempt = NOW(),
        notion_sync_error = NULL
    WHERE extraction_id = p_extraction_id;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- 6.2: Mark error as synced to Notion
CREATE OR REPLACE FUNCTION mark_error_synced(
    p_error_id INTEGER,
    p_notion_page_id TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE curator_errors
    SET
        notion_page_id = p_notion_page_id,
        notion_synced_at = NOW(),
        notion_last_sync_attempt = NOW(),
        notion_sync_error = NULL
    WHERE id = p_error_id;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- 6.3: Mark report as synced to Notion
CREATE OR REPLACE FUNCTION mark_report_synced(
    p_report_id INTEGER,
    p_notion_page_id TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE curator_reports
    SET
        notion_page_id = p_notion_page_id,
        notion_synced_at = NOW(),
        notion_last_sync_attempt = NOW(),
        notion_sync_error = NULL
    WHERE id = p_report_id;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- 6.4: Record sync failure
CREATE OR REPLACE FUNCTION mark_sync_failed(
    p_table_name TEXT,
    p_item_id TEXT,
    p_error_message TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    CASE p_table_name
        WHEN 'staging_extractions' THEN
            UPDATE staging_extractions
            SET
                notion_last_sync_attempt = NOW(),
                notion_sync_error = p_error_message
            WHERE extraction_id = p_item_id::UUID;

        WHEN 'curator_errors' THEN
            UPDATE curator_errors
            SET
                notion_last_sync_attempt = NOW(),
                notion_sync_error = p_error_message
            WHERE id = p_item_id::INTEGER;

        WHEN 'curator_reports' THEN
            UPDATE curator_reports
            SET
                notion_last_sync_attempt = NOW(),
                notion_sync_error = p_error_message
            WHERE id = p_item_id::INTEGER;
    END CASE;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 7: VALIDATION
-- ============================================================================

DO $$
BEGIN
    -- Verify new tables exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'curator_errors') THEN
        RAISE EXCEPTION 'Table curator_errors was not created';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'curator_reports') THEN
        RAISE EXCEPTION 'Table curator_reports was not created';
    END IF;

    -- Verify new columns exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'staging_extractions' AND column_name = 'notion_page_id'
    ) THEN
        RAISE EXCEPTION 'Column notion_page_id was not added to staging_extractions';
    END IF;

    RAISE NOTICE 'Migration 003 completed successfully ✓';
    RAISE NOTICE '  - Created curator_errors table';
    RAISE NOTICE '  - Created curator_reports table';
    RAISE NOTICE '  - Added Notion tracking columns to staging_extractions';
    RAISE NOTICE '  - Created 4 notification triggers';
    RAISE NOTICE '  - Created helper functions for webhook server';
END $$;

COMMIT;
