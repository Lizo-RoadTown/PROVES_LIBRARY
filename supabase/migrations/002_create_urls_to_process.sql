-- Migration: Create urls_to_process table for WebFetch agent
-- Purpose: Queue system for documentation URLs with extraction context

CREATE TABLE IF NOT EXISTS urls_to_process (
    url TEXT PRIMARY KEY,
    status TEXT DEFAULT 'pending',
    quality_score FLOAT,
    quality_reason TEXT,

    -- Context hints for extractor (saves tokens, focuses extraction)
    preview_components TEXT[],  -- Component/module names found (e.g., ['I2CDriver', 'LinuxI2CDriverComponentImpl'])
    preview_interfaces TEXT[],  -- Port/interface mentions (e.g., ['read()', 'write()', 'TlmChan'])
    preview_keywords TEXT[],    -- Technical keywords (e.g., ['i2c', 'telemetry', 'component'])
    preview_summary TEXT,       -- Brief content summary for prioritization

    -- Tracking
    discovered_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    error_message TEXT,

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_urls_status ON urls_to_process(status);
CREATE INDEX IF NOT EXISTS idx_urls_discovered ON urls_to_process(discovered_at);

-- Comments
COMMENT ON TABLE urls_to_process IS 'Queue of documentation URLs discovered by WebFetch agent with extraction context';
COMMENT ON COLUMN urls_to_process.preview_components IS 'Component names found during page scan (helps extractor focus)';
COMMENT ON COLUMN urls_to_process.preview_interfaces IS 'Port/interface mentions (e.g., read(), write(), TlmChan)';
COMMENT ON COLUMN urls_to_process.preview_keywords IS 'Technical keywords for prioritization';
COMMENT ON COLUMN urls_to_process.preview_summary IS 'Brief summary of page content';
