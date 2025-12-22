-- PROVES Library - Findings Table Migration
-- Created: 2024-12-22
-- Purpose: Store ALL raw observations before deciding if they become dependencies
--
-- Philosophy: Record everything, decide later
--   1. Extractor finds things → stores in findings (raw)
--   2. Validator reviews → marks 'validated' or 'rejected'  
--   3. Storage promotes validated findings → kg_nodes/kg_relationships
--   4. HITL approves HIGH criticality promotions
--
-- Nothing is lost. Even rejected findings become training data.

-- ============================================
-- FINDINGS TABLE (Raw Observations)
-- ============================================

-- Finding types
CREATE TYPE finding_type AS ENUM (
    'fact',                -- Simple statement: "I2CDriver uses address 0x50"
    'constraint',          -- Limitation: "Max 100mA at startup"
    'config',              -- Configuration: "Default timeout is 1000ms"
    'warning',             -- Caution: "Don't exceed 3.3V"
    'procedure',           -- Steps: "To reset: 1. Power off, 2. Wait 5s, 3. Power on"
    'equivalence',         -- Cross-ecosystem match: "F' TlmChan = PK Telemetry"
    'dependency_candidate' -- Potential relationship: "A requires B"
);

-- Source ecosystems
CREATE TYPE source_ecosystem AS ENUM (
    'fprime',              -- NASA F Prime framework
    'proveskit',           -- ProvesKit/Bronco Space Lab
    'pysquared',           -- PySquared (predecessor to ProvesKit)
    'cubesat_general',     -- General CubeSat knowledge
    'unknown'              -- Source ecosystem not yet classified
);

-- Finding status workflow
CREATE TYPE finding_status AS ENUM (
    'raw',                 -- Just extracted, not reviewed
    'validated',           -- Confirmed accurate by agent or human
    'promoted',            -- Converted to kg_node or kg_relationship
    'rejected',            -- Marked as incorrect or irrelevant
    'duplicate'            -- Duplicate of another finding
);

-- Main findings table
CREATE TABLE findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- ============================================
    -- WHAT WAS FOUND (the observation itself)
    -- ============================================
    finding_type finding_type NOT NULL,
    
    -- Subject-Predicate-Object structure (flexible)
    subject TEXT NOT NULL,               -- What it's about: "I2CDriver", "PowerManager"
    predicate TEXT,                      -- Relationship verb (optional): "uses", "requires", "equals"
    object TEXT,                         -- Target (optional): "address 0x50", "3.3V max"
    
    -- Raw text exactly as found
    raw_text TEXT NOT NULL,              -- Exact quote from source (for verification)
    
    -- Structured interpretation
    interpreted_meaning TEXT,            -- Agent's interpretation of what this means
    
    -- ============================================
    -- WHERE IT CAME FROM (mandatory citation)
    -- ============================================
    source_url TEXT NOT NULL,            -- Full URL to exact location
    source_type TEXT NOT NULL,           -- 'github_file', 'github_readme', 'docs_site', 'local_file'
    source_ecosystem source_ecosystem NOT NULL DEFAULT 'unknown',
    source_file_path TEXT,               -- Path within repo if applicable
    source_line_start INTEGER,           -- Line number range if known
    source_line_end INTEGER,
    
    -- ============================================
    -- EXTRACTION METADATA
    -- ============================================
    extracted_by TEXT NOT NULL,          -- Agent name: 'extractor_v1', 'curator_main'
    extraction_model TEXT,               -- Model used: 'claude-sonnet-4-5-20250929'
    extraction_confidence DECIMAL(3,2),  -- 0.00 to 1.00
    extraction_reasoning TEXT,           -- Why agent thinks this is important
    extracted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- ============================================
    -- VALIDATION WORKFLOW
    -- ============================================
    status finding_status NOT NULL DEFAULT 'raw',
    validated_by TEXT,                   -- 'validator_agent', 'human:username'
    validated_at TIMESTAMP,
    validation_notes TEXT,               -- Reason for validation/rejection
    
    -- ============================================
    -- PROMOTION (when finding becomes a kg entity)
    -- ============================================
    promoted_to_node_id UUID REFERENCES kg_nodes(id),
    promoted_to_relationship_id UUID REFERENCES kg_relationships(id),
    promoted_at TIMESTAMP,
    promoted_by TEXT,
    
    -- ============================================
    -- DEDUPLICATION
    -- ============================================
    content_hash TEXT,                   -- Hash of subject+predicate+object for dedup
    duplicate_of_id UUID REFERENCES findings(id),
    
    -- ============================================
    -- TRAINING DATA FLAGS
    -- ============================================
    is_gold_standard BOOLEAN DEFAULT FALSE,  -- Human-verified, use for training
    human_correction TEXT,                   -- If human corrected the extraction
    
    -- ============================================
    -- AUDIT
    -- ============================================
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================

-- Find by subject (component name)
CREATE INDEX idx_findings_subject ON findings(subject);

-- Find by source ecosystem
CREATE INDEX idx_findings_ecosystem ON findings(source_ecosystem);

-- Find by status (for workflow)
CREATE INDEX idx_findings_status ON findings(status);

-- Find raw findings needing validation
CREATE INDEX idx_findings_raw ON findings(status) WHERE status = 'raw';

-- Find validated findings ready for promotion
CREATE INDEX idx_findings_validated ON findings(status) WHERE status = 'validated';

-- Deduplication lookup
CREATE INDEX idx_findings_hash ON findings(content_hash);

-- Full-text search on raw_text
CREATE INDEX idx_findings_text_search ON findings USING gin(to_tsvector('english', raw_text));

-- ============================================
-- FUNCTIONS
-- ============================================

-- Auto-generate content hash for deduplication
CREATE OR REPLACE FUNCTION generate_finding_hash()
RETURNS TRIGGER AS $$
BEGIN
    NEW.content_hash := md5(
        COALESCE(NEW.subject, '') || '::' || 
        COALESCE(NEW.predicate, '') || '::' || 
        COALESCE(NEW.object, '') || '::' ||
        COALESCE(NEW.source_ecosystem::TEXT, '')
    );
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_finding_hash
BEFORE INSERT OR UPDATE ON findings
FOR EACH ROW EXECUTE FUNCTION generate_finding_hash();

-- ============================================
-- EQUIVALENCES TABLE (Cross-Ecosystem Matching)
-- ============================================
-- Special table for tracking when things in different ecosystems
-- are the same concept with different names

CREATE TABLE equivalences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- The two things that are equivalent
    ecosystem_a source_ecosystem NOT NULL,
    name_a TEXT NOT NULL,                -- e.g., "TlmChan" in fprime
    
    ecosystem_b source_ecosystem NOT NULL,
    name_b TEXT NOT NULL,                -- e.g., "Telemetry" in proveskit
    
    -- Confidence and evidence
    confidence DECIMAL(3,2) NOT NULL,    -- How sure are we these are the same?
    evidence_finding_id UUID REFERENCES findings(id),  -- Finding that suggested this
    
    -- Validation
    status finding_status NOT NULL DEFAULT 'raw',
    validated_by TEXT,
    validated_at TIMESTAMP,
    
    -- Canonical name (what we call it in our unified graph)
    canonical_name TEXT,                 -- e.g., "TelemetryChannel"
    canonical_node_id UUID REFERENCES kg_nodes(id),
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Prevent duplicates
    UNIQUE(ecosystem_a, name_a, ecosystem_b, name_b)
);

CREATE INDEX idx_equivalences_lookup_a ON equivalences(ecosystem_a, name_a);
CREATE INDEX idx_equivalences_lookup_b ON equivalences(ecosystem_b, name_b);
CREATE INDEX idx_equivalences_status ON equivalences(status);

-- ============================================
-- SOURCES TABLE (Track What We've Crawled)
-- ============================================
-- Record every URL/file we've processed to avoid re-crawling

CREATE TABLE crawled_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Source identification
    source_url TEXT UNIQUE NOT NULL,
    source_type TEXT NOT NULL,           -- 'github_file', 'github_directory', 'docs_page'
    source_ecosystem source_ecosystem,
    
    -- Content tracking
    content_hash TEXT,                   -- Hash of content (to detect changes)
    content_size INTEGER,
    
    -- Crawl metadata
    first_crawled_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_crawled_at TIMESTAMP NOT NULL DEFAULT NOW(),
    crawl_count INTEGER DEFAULT 1,
    
    -- Extraction results
    findings_extracted INTEGER DEFAULT 0,
    last_extraction_status TEXT,         -- 'success', 'partial', 'failed'
    last_extraction_error TEXT,
    
    -- Scheduling
    next_crawl_after TIMESTAMP,          -- When to re-check for updates
    crawl_priority INTEGER DEFAULT 0     -- Higher = crawl sooner
);

CREATE INDEX idx_sources_ecosystem ON crawled_sources(source_ecosystem);
CREATE INDEX idx_sources_needs_crawl ON crawled_sources(next_crawl_after) WHERE next_crawl_after IS NOT NULL;

-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON TABLE findings IS 'Raw observations extracted from documentation. Everything found is stored here first, then promoted to kg_nodes/kg_relationships after validation.';
COMMENT ON TABLE equivalences IS 'Cross-ecosystem concept mappings. When F Prime calls something one name and ProvesKit calls it another, we track that here.';
COMMENT ON TABLE crawled_sources IS 'Registry of all URLs and files we have processed. Prevents re-crawling and tracks changes.';

COMMENT ON COLUMN findings.raw_text IS 'Exact quote from source document. This is the evidence.';
COMMENT ON COLUMN findings.source_url IS 'Full URL including line numbers if possible. No URL = cannot store.';
COMMENT ON COLUMN findings.status IS 'Workflow: raw → validated → promoted. Rejected findings kept for training.';
