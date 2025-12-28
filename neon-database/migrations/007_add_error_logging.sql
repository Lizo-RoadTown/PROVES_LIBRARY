-- Migration 007: Add error logging columns to tables
-- Each agent logs its own errors to the table it uses

BEGIN;

-- Add error logging to staging_extractions
-- Used by: extractor, validator, suggestion analyzer
ALTER TABLE staging_extractions
ADD COLUMN IF NOT EXISTS error_log JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS error_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_error_at TIMESTAMP WITH TIME ZONE;

-- Add error logging to improvement_suggestions
-- Used by: improvement analyzer
ALTER TABLE improvement_suggestions
ADD COLUMN IF NOT EXISTS error_log JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS error_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_error_at TIMESTAMP WITH TIME ZONE;

-- Create index for querying errors
CREATE INDEX IF NOT EXISTS idx_staging_extractions_errors
ON staging_extractions(last_error_at)
WHERE error_count > 0;

CREATE INDEX IF NOT EXISTS idx_suggestions_errors
ON improvement_suggestions(last_error_at)
WHERE error_count > 0;

-- Create a view to aggregate all errors across tables
CREATE OR REPLACE VIEW all_errors AS
SELECT
    'staging_extraction' AS source_table,
    extraction_id::text AS record_id,
    candidate_key AS record_name,
    error_log,
    error_count,
    last_error_at,
    created_at,
    updated_at
FROM staging_extractions
WHERE error_count > 0

UNION ALL

SELECT
    'improvement_suggestion' AS source_table,
    suggestion_id::text AS record_id,
    title AS record_name,
    error_log,
    error_count,
    last_error_at,
    created_at,
    updated_at
FROM improvement_suggestions
WHERE error_count > 0;

COMMENT ON VIEW all_errors IS 'Aggregated view of all errors across agent tables';

-- Helper function to append an error to error_log
CREATE OR REPLACE FUNCTION log_error(
    error_data JSONB
) RETURNS JSONB AS $$
DECLARE
    new_error JSONB;
BEGIN
    -- Add timestamp if not present
    new_error := error_data || jsonb_build_object(
        'logged_at', COALESCE(
            (error_data->>'logged_at')::timestamp with time zone,
            NOW()
        )
    );

    RETURN new_error;
END;
$$ LANGUAGE plpgsql;

COMMIT;
