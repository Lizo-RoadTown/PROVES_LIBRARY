-- PROVES Library - Initial Database Schema
-- This creates the foundational tables for the knowledge graph and library system
-- PostgreSQL + pgvector for semantic search

-- ============================================
-- EXTENSIONS
-- ============================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable vector similarity search (for embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================
-- ENUMS
-- ============================================

-- Knowledge entry types (from ROADMAP.md)
CREATE TYPE entry_type AS ENUM (
    'pattern',           -- Design pattern or best practice
    'failure',           -- Failure case study
    'component',         -- Hardware/software component description
    'config',            -- Configuration guidance
    'test',              -- Testing methodology
    'integration',       -- Integration pattern
    'ops'                -- Operational procedure
);

-- Knowledge domains (from library/ structure)
CREATE TYPE domain_type AS ENUM (
    'software',          -- F´ patterns, code architecture
    'build',             -- Assembly, hardware, fabrication
    'ops',               -- Operations, deployment, monitoring
    'systems',           -- Systems engineering, requirements
    'testing'            -- Testing, validation, verification
);

-- ERV relationship types (from KNOWLEDGE_GRAPH_SCHEMA.md)
CREATE TYPE relationship_type AS ENUM (
    'depends_on',        -- Component A depends on Component B
    'conflicts_with',    -- Component A conflicts with Component B (e.g., I2C address collision)
    'enables',           -- Component A enables capability B
    'requires',          -- Component A requires condition/config B
    'mitigates',         -- Solution A mitigates risk B
    'causes'             -- Action A causes consequence B
);

-- Quality score tiers (for curator agent)
CREATE TYPE quality_tier AS ENUM (
    'high',              -- Score >= 0.8: Complete, well-cited, verified
    'medium',            -- Score >= 0.5: Usable but needs improvement
    'low',               -- Score < 0.5: Incomplete or poorly documented
    'draft'              -- Not yet scored
);

-- ============================================
-- CORE TABLES
-- ============================================

-- Library entries (markdown files indexed)
CREATE TABLE library_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Metadata
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,           -- Filename without .md
    file_path TEXT UNIQUE NOT NULL,      -- Relative path from library/
    entry_type entry_type NOT NULL,
    domain domain_type NOT NULL,

    -- Content
    content TEXT NOT NULL,               -- Full markdown content
    summary TEXT,                        -- AI-generated summary

    -- Frontmatter fields
    tags TEXT[] DEFAULT '{}',
    sources TEXT[] DEFAULT '{}',         -- URLs, repos, issues
    authors TEXT[] DEFAULT '{}',
    date_captured TIMESTAMP,

    -- Quality scoring (curator agent)
    quality_score DECIMAL(3,2),          -- 0.00 to 1.00
    quality_tier quality_tier DEFAULT 'draft',
    completeness_score DECIMAL(3,2),
    citation_count INTEGER DEFAULT 0,
    has_verification BOOLEAN DEFAULT FALSE,

    -- Embeddings for semantic search
    embedding vector(1536),              -- OpenAI ada-002 or sentence-transformers

    -- Artifacts (links to external resources)
    artifact_repos TEXT[] DEFAULT '{}',
    artifact_components TEXT[] DEFAULT '{}',
    artifact_tests TEXT[] DEFAULT '{}',
    artifact_docs TEXT[] DEFAULT '{}',

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    indexed_at TIMESTAMP DEFAULT NOW(),

    -- Search optimization
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('english', title || ' ' || COALESCE(content, ''))
    ) STORED
);

-- Knowledge graph nodes (components, resources, hardware)
CREATE TABLE kg_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Node identity
    name TEXT NOT NULL,
    node_type TEXT NOT NULL,             -- 'component', 'resource', 'hardware', 'pattern', 'risk'
    description TEXT,

    -- Attributes (flexible JSONB for different node types)
    properties JSONB DEFAULT '{}',

    -- Links to library entries
    related_entries UUID[] DEFAULT '{}', -- Array of library_entry IDs

    -- Embeddings for similarity search
    embedding vector(1536),

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Knowledge graph edges (ERV relationships)
CREATE TABLE kg_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relationship
    source_node_id UUID NOT NULL REFERENCES kg_nodes(id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES kg_nodes(id) ON DELETE CASCADE,
    relationship_type relationship_type NOT NULL,

    -- Metadata
    strength DECIMAL(3,2),               -- 0.00 to 1.00 (confidence/importance)
    description TEXT,
    evidence_entry_id UUID REFERENCES library_entries(id), -- Which library entry documents this relationship

    -- Cascade analysis attributes
    cascade_domain TEXT,                 -- 'power', 'data', 'thermal', 'timing'
    is_critical BOOLEAN DEFAULT FALSE,   -- Critical path for cascade detection

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Prevent duplicate relationships
    UNIQUE(source_node_id, target_node_id, relationship_type)
);

-- Risk patterns (for risk scanner)
CREATE TABLE risk_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Pattern identity
    name TEXT NOT NULL UNIQUE,
    pattern_type TEXT NOT NULL,          -- 'i2c_conflict', 'memory_leak', 'power_budget', etc.
    severity TEXT NOT NULL,              -- 'critical', 'high', 'medium', 'low'

    -- Detection
    detection_method TEXT NOT NULL,      -- 'ast', 'regex', 'graph_query', 'heuristic'
    pattern_definition JSONB NOT NULL,   -- AST pattern, regex, or query definition

    -- Resolution
    fix_entry_id UUID REFERENCES library_entries(id), -- Link to fix pattern in library
    fix_summary TEXT,

    -- Related graph structures
    related_cascade_domain TEXT,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Repository scans (tracking risk scanner runs)
CREATE TABLE repository_scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Repository info
    repo_url TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    branch TEXT DEFAULT 'main',
    commit_sha TEXT,

    -- Scan metadata
    scan_type TEXT NOT NULL,             -- 'full', 'incremental', 'pr'
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status TEXT NOT NULL,                -- 'running', 'completed', 'failed'

    -- Results summary
    risks_found INTEGER DEFAULT 0,
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    medium_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW()
);

-- Detected risks (individual findings from scans)
CREATE TABLE detected_risks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Scan reference
    scan_id UUID NOT NULL REFERENCES repository_scans(id) ON DELETE CASCADE,
    pattern_id UUID NOT NULL REFERENCES risk_patterns(id),

    -- Location
    file_path TEXT NOT NULL,
    line_number INTEGER,
    code_snippet TEXT,

    -- Risk details
    severity TEXT NOT NULL,
    description TEXT NOT NULL,
    suggested_fix TEXT,

    -- Graph enhancement (if available)
    cascade_risk BOOLEAN DEFAULT FALSE,  -- Detected via graph cascade analysis
    affected_nodes UUID[] DEFAULT '{}',  -- KG nodes affected

    -- Resolution tracking
    resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,
    resolved_at TIMESTAMP,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- AGENT TABLES
-- ============================================

-- Curator agent workflow state
CREATE TABLE curator_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Input
    raw_capture_text TEXT NOT NULL,      -- The captured context from PULL phase
    source_url TEXT,                     -- Origin (issue, PR, commit, etc.)

    -- Processing state
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed', 'needs_review'
    stage TEXT,                          -- 'citation_extraction', 'normalization', 'quality_scoring', 'duplicate_check'

    -- Output
    generated_entry_id UUID REFERENCES library_entries(id),
    quality_issues JSONB DEFAULT '{}',   -- List of quality concerns
    duplicate_of UUID REFERENCES library_entries(id),

    -- Human review
    needs_human_review BOOLEAN DEFAULT FALSE,
    review_notes TEXT,
    approved BOOLEAN,
    reviewed_at TIMESTAMP,
    reviewed_by TEXT,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Builder agent workflow state
CREATE TABLE builder_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Input
    user_prompt TEXT NOT NULL,           -- Natural language description
    component_type TEXT NOT NULL,        -- 'active', 'passive', 'queued'

    -- Pattern matching
    matched_patterns UUID[] DEFAULT '{}', -- Library entries used as templates

    -- Processing state
    status TEXT NOT NULL DEFAULT 'pending',
    stage TEXT,                          -- 'pattern_search', 'code_generation', 'test_generation', 'validation'

    -- Generated artifacts
    generated_code TEXT,
    generated_tests TEXT,
    generated_integration TEXT,

    -- Validation results
    syntax_valid BOOLEAN,
    tests_pass BOOLEAN,
    validation_errors JSONB DEFAULT '{}',

    -- Human review
    needs_human_review BOOLEAN DEFAULT TRUE, -- Always true (safety-first)
    review_notes TEXT,
    approved BOOLEAN,
    reviewed_at TIMESTAMP,
    reviewed_by TEXT,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================

-- Library entries
CREATE INDEX idx_library_entries_type ON library_entries(entry_type);
CREATE INDEX idx_library_entries_domain ON library_entries(domain);
CREATE INDEX idx_library_entries_quality ON library_entries(quality_tier);
CREATE INDEX idx_library_entries_tags ON library_entries USING GIN(tags);
CREATE INDEX idx_library_entries_search ON library_entries USING GIN(search_vector);
CREATE INDEX idx_library_entries_embedding ON library_entries USING ivfflat(embedding vector_cosine_ops);

-- Knowledge graph
CREATE INDEX idx_kg_nodes_type ON kg_nodes(node_type);
CREATE INDEX idx_kg_nodes_embedding ON kg_nodes USING ivfflat(embedding vector_cosine_ops);
CREATE INDEX idx_kg_relationships_source ON kg_relationships(source_node_id);
CREATE INDEX idx_kg_relationships_target ON kg_relationships(target_node_id);
CREATE INDEX idx_kg_relationships_type ON kg_relationships(relationship_type);
CREATE INDEX idx_kg_relationships_critical ON kg_relationships(is_critical) WHERE is_critical = TRUE;

-- Risk scanner
CREATE INDEX idx_risk_patterns_type ON risk_patterns(pattern_type);
CREATE INDEX idx_detected_risks_scan ON detected_risks(scan_id);
CREATE INDEX idx_detected_risks_pattern ON detected_risks(pattern_id);
CREATE INDEX idx_detected_risks_resolved ON detected_risks(resolved);

-- Agent jobs
CREATE INDEX idx_curator_jobs_status ON curator_jobs(status);
CREATE INDEX idx_builder_jobs_status ON builder_jobs(status);

-- ============================================
-- TRIGGERS
-- ============================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_library_entries_updated_at
    BEFORE UPDATE ON library_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_kg_nodes_updated_at
    BEFORE UPDATE ON kg_nodes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_kg_relationships_updated_at
    BEFORE UPDATE ON kg_relationships
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VIEWS
-- ============================================

-- High-quality entries suitable for agent use
CREATE VIEW high_quality_entries AS
SELECT * FROM library_entries
WHERE quality_tier IN ('high', 'medium')
  AND quality_score >= 0.5
ORDER BY quality_score DESC;

-- Critical cascade paths (for risk scanner)
CREATE VIEW critical_cascade_paths AS
SELECT
    r.id,
    r.source_node_id,
    r.target_node_id,
    r.relationship_type,
    r.cascade_domain,
    n1.name AS source_name,
    n2.name AS target_name
FROM kg_relationships r
JOIN kg_nodes n1 ON r.source_node_id = n1.id
JOIN kg_nodes n2 ON r.target_node_id = n2.id
WHERE r.is_critical = TRUE;

-- Recent unresolved risks
CREATE VIEW unresolved_risks AS
SELECT
    dr.*,
    rp.name AS pattern_name,
    rp.severity AS pattern_severity,
    rs.repo_name,
    rs.repo_url
FROM detected_risks dr
JOIN risk_patterns rp ON dr.pattern_id = rp.id
JOIN repository_scans rs ON dr.scan_id = rs.id
WHERE dr.resolved = FALSE
ORDER BY
    CASE rp.severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
    END,
    dr.created_at DESC;

-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON TABLE library_entries IS 'Indexed markdown knowledge entries from library/';
COMMENT ON TABLE kg_nodes IS 'Knowledge graph nodes representing components, resources, patterns, etc.';
COMMENT ON TABLE kg_relationships IS 'ERV relationships between knowledge graph nodes';
COMMENT ON TABLE risk_patterns IS 'Reusable risk detection patterns for the scanner';
COMMENT ON TABLE repository_scans IS 'Tracking table for repository scan runs';
COMMENT ON TABLE detected_risks IS 'Individual risk findings from scans';
COMMENT ON TABLE curator_jobs IS 'Curator agent workflow state and outputs';
COMMENT ON TABLE builder_jobs IS 'Builder agent workflow state and generated artifacts';

COMMENT ON COLUMN library_entries.embedding IS 'Vector embedding for semantic search (1536 dims for ada-002)';
COMMENT ON COLUMN library_entries.quality_score IS 'Curator agent quality score (0.0-1.0)';
COMMENT ON COLUMN kg_relationships.strength IS 'Relationship confidence/importance (0.0-1.0)';
COMMENT ON COLUMN kg_relationships.is_critical IS 'Part of critical cascade path for risk analysis';
