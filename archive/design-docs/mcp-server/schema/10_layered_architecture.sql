-- ============================================================================
-- PROVES Library - Layered Database Architecture
-- ============================================================================
-- Version: 1.0.0
-- Created: 2024-12-22
-- 
-- ARCHITECTURE:
--   raw_*     → Immutable append-only captures (JSONB payloads)
--   core_*    → Canonical normalized entities (the "truth")
--   derived_* → Regenerable artifacts (chunks, embeddings, graph, scores)
--
-- HARD RULES:
--   1. raw_* tables are IMMUTABLE (append-only, no UPDATE/DELETE)
--   2. Embeddings only from doc_chunks, never raw text
--   3. Every derived record references source_snapshot_id + pipeline_run_id
--   4. Derived tables are disposable (can regenerate from raw+core)
--   5. Explicit status fields for pipeline stage tracking
--
-- NAMING CONVENTIONS:
--   - snake_case for all identifiers
--   - *_id for foreign keys and identifiers
--   - *_type for enum/classification fields
--   - *_at for timestamps
--   - *_hash for content hashes (SHA-256)
--   - NULL = unknown/not-applicable (never "not processed yet")
--   - "not processed yet" = explicit status field value
-- ============================================================================

-- ============================================================================
-- EXTENSIONS
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;          -- pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS pg_trgm;         -- trigram for fuzzy text search

-- ============================================================================
-- ENUMS
-- ============================================================================

-- Source ecosystem identifiers
CREATE TYPE ecosystem_type AS ENUM (
    'fprime',           -- NASA F Prime framework
    'proveskit',        -- ProvesKit/Bronco Space Lab
    'pysquared',        -- PySquared (predecessor)
    'cubesat_general',  -- Generic CubeSat knowledge
    'external'          -- External references (datasheets, papers)
);

-- Source types for raw captures
CREATE TYPE source_type AS ENUM (
    'github_file',      -- File from GitHub repo
    'github_directory', -- Directory listing
    'docs_webpage',     -- Documentation site page
    'local_file',       -- Local filesystem
    'api_response',     -- API call result
    'manual_entry'      -- Human-entered data
);

-- Pipeline stage statuses
CREATE TYPE stage_status AS ENUM (
    'pending',          -- Queued but not started
    'in_progress',      -- Currently processing
    'completed',        -- Successfully finished
    'failed',           -- Failed with error
    'skipped'           -- Intentionally skipped
);

-- Snapshot processing status (aggregate of all stages)
CREATE TYPE snapshot_status AS ENUM (
    'captured',         -- Raw data captured
    'parsed',           -- Parsed into core entities
    'chunked',          -- Text chunked for embedding
    'embedded',         -- Embeddings generated
    'graphed',          -- Graph nodes/edges created
    'scored'            -- Model scores computed
);

-- Core entity types
CREATE TYPE entity_type AS ENUM (
    'repository',       -- GitHub repo
    'artifact',         -- File, document, or other artifact
    'component',        -- Software/hardware component
    'interface',        -- Port, API, protocol
    'constraint',       -- Requirement, limitation, rule
    'metric',           -- Telemetry, measurement
    'procedure',        -- Step-by-step process
    'failure_mode'      -- Known failure pattern
);

-- Relationship types for graph edges
CREATE TYPE edge_type AS ENUM (
    'depends_on',       -- A requires B to function
    'provides',         -- A provides capability to B
    'conflicts_with',   -- A and B cannot coexist
    'implements',       -- A implements interface B
    'contains',         -- A contains B (hierarchy)
    'references',       -- A mentions/links to B
    'equivalent_to',    -- A and B are same concept (cross-ecosystem)
    'mitigates',        -- A reduces risk of B
    'causes',           -- A can cause B
    'measured_by'       -- A is measured by metric B
);

-- ============================================================================
-- PIPELINE TRACKING
-- ============================================================================

-- Pipeline run tracking (the spine of provenance)
CREATE TABLE pipeline_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Run identification
    run_name TEXT NOT NULL,                      -- Human-readable: "fprime_crawl_2024_12_22"
    run_type TEXT NOT NULL,                      -- 'full_crawl', 'incremental', 'reprocess'
    
    -- Scope
    target_ecosystem ecosystem_type,             -- NULL = all ecosystems
    target_source_url TEXT,                      -- NULL = all sources
    
    -- Timing
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    -- Status per stage
    capture_status stage_status DEFAULT 'pending',
    parse_status stage_status DEFAULT 'pending',
    chunk_status stage_status DEFAULT 'pending',
    embed_status stage_status DEFAULT 'pending',
    graph_status stage_status DEFAULT 'pending',
    score_status stage_status DEFAULT 'pending',
    
    -- Metrics
    snapshots_captured INTEGER DEFAULT 0,
    entities_created INTEGER DEFAULT 0,
    chunks_created INTEGER DEFAULT 0,
    embeddings_created INTEGER DEFAULT 0,
    edges_created INTEGER DEFAULT 0,
    
    -- Errors
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    
    -- Operator context
    triggered_by TEXT,                           -- 'manual', 'schedule', 'webhook'
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_pipeline_runs_started ON pipeline_runs(started_at DESC);
CREATE INDEX idx_pipeline_runs_type ON pipeline_runs(run_type);

-- ============================================================================
-- RAW LAYER (Immutable, append-only)
-- ============================================================================

-- Raw source snapshots (the canonical "what we saw")
CREATE TABLE raw_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Source identification (stable key)
    source_url TEXT NOT NULL,                    -- Full URL or path
    source_type source_type NOT NULL,
    ecosystem ecosystem_type NOT NULL,
    
    -- Content (immutable once written)
    content_hash TEXT NOT NULL,                  -- SHA-256 of payload
    payload JSONB NOT NULL,                      -- Full content as captured
    payload_size_bytes INTEGER NOT NULL,
    
    -- Capture metadata
    captured_at TIMESTAMP NOT NULL DEFAULT NOW(),
    captured_by_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
    
    -- Source versioning (for change detection)
    source_commit_sha TEXT,                      -- Git SHA if applicable
    source_etag TEXT,                            -- HTTP ETag if applicable
    source_last_modified TIMESTAMP,              -- HTTP Last-Modified if applicable
    
    -- Processing status
    status snapshot_status NOT NULL DEFAULT 'captured',
    
    -- No updated_at - raw is immutable
    created_at TIMESTAMP DEFAULT NOW()
);

-- Unique on URL + hash = same content at same URL is one record
CREATE UNIQUE INDEX idx_raw_snapshots_identity ON raw_snapshots(source_url, content_hash);
CREATE INDEX idx_raw_snapshots_url ON raw_snapshots(source_url);
CREATE INDEX idx_raw_snapshots_ecosystem ON raw_snapshots(ecosystem);
CREATE INDEX idx_raw_snapshots_status ON raw_snapshots(status);
CREATE INDEX idx_raw_snapshots_captured ON raw_snapshots(captured_at DESC);
CREATE INDEX idx_raw_snapshots_run ON raw_snapshots(captured_by_run_id);

-- Raw telemetry/metrics (for later: live satellite data)
CREATE TABLE raw_telemetry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Source identification
    source_system TEXT NOT NULL,                 -- 'groundstation', 'simulation', etc.
    satellite_id TEXT,                           -- If applicable
    
    -- Content
    content_hash TEXT NOT NULL,
    payload JSONB NOT NULL,
    
    -- Timing
    telemetry_timestamp TIMESTAMP NOT NULL,      -- When data was generated
    captured_at TIMESTAMP NOT NULL DEFAULT NOW(),
    captured_by_run_id UUID REFERENCES pipeline_runs(id),
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_raw_telemetry_source ON raw_telemetry(source_system, satellite_id);
CREATE INDEX idx_raw_telemetry_timestamp ON raw_telemetry(telemetry_timestamp DESC);

-- ============================================================================
-- CORE LAYER (Canonical normalized entities)
-- ============================================================================

-- Core entities (the normalized "things" in our knowledge graph)
CREATE TABLE core_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identity (stable across runs)
    entity_type entity_type NOT NULL,
    canonical_key TEXT NOT NULL,                 -- Stable identifier within type
    
    -- Human-readable
    name TEXT NOT NULL,
    display_name TEXT,                           -- Optional pretty name
    description TEXT,
    
    -- Classification
    ecosystem ecosystem_type,                    -- NULL = cross-ecosystem
    namespace TEXT,                              -- e.g., 'Svc', 'Drv', 'Fw' for F'
    
    -- Flexible attributes
    attributes JSONB DEFAULT '{}',               -- Type-specific properties
    
    -- Provenance (which snapshot + run created this version)
    source_snapshot_id UUID REFERENCES raw_snapshots(id),
    created_by_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
    
    -- Versioning
    version INTEGER NOT NULL DEFAULT 1,
    superseded_by_id UUID REFERENCES core_entities(id),
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Unique current entity per type+key
CREATE UNIQUE INDEX idx_core_entities_identity 
    ON core_entities(entity_type, canonical_key) 
    WHERE is_current = TRUE;
CREATE INDEX idx_core_entities_type ON core_entities(entity_type);
CREATE INDEX idx_core_entities_ecosystem ON core_entities(ecosystem);
CREATE INDEX idx_core_entities_name ON core_entities(name);
CREATE INDEX idx_core_entities_snapshot ON core_entities(source_snapshot_id);
CREATE INDEX idx_core_entities_run ON core_entities(created_by_run_id);

-- Core equivalences (cross-ecosystem identity mapping)
CREATE TABLE core_equivalences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- The two entities that are equivalent
    entity_a_id UUID NOT NULL REFERENCES core_entities(id),
    entity_b_id UUID NOT NULL REFERENCES core_entities(id),
    
    -- Confidence and evidence
    confidence DECIMAL(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    evidence_text TEXT,                          -- Why we think they're equivalent
    
    -- Provenance
    source_snapshot_id UUID REFERENCES raw_snapshots(id),
    created_by_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
    
    -- Validation
    is_validated BOOLEAN DEFAULT FALSE,
    validated_by TEXT,                           -- 'agent' or 'human:username'
    validated_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Prevent duplicates (order-independent)
    CONSTRAINT unique_equivalence UNIQUE (
        LEAST(entity_a_id, entity_b_id),
        GREATEST(entity_a_id, entity_b_id)
    ),
    -- Can't be equivalent to self
    CONSTRAINT no_self_equivalence CHECK (entity_a_id != entity_b_id)
);

CREATE INDEX idx_core_equivalences_entity_a ON core_equivalences(entity_a_id);
CREATE INDEX idx_core_equivalences_entity_b ON core_equivalences(entity_b_id);

-- ============================================================================
-- DERIVED LAYER (Regenerable from raw + core)
-- ============================================================================

-- Document chunks (for embedding)
CREATE TABLE derived_doc_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Source linkage (REQUIRED)
    source_snapshot_id UUID NOT NULL REFERENCES raw_snapshots(id),
    pipeline_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
    
    -- Parent entity (if parsed)
    entity_id UUID REFERENCES core_entities(id),
    
    -- Chunk content
    chunk_index INTEGER NOT NULL,                -- Position within document
    chunk_text TEXT NOT NULL,
    chunk_hash TEXT NOT NULL,                    -- For change detection
    
    -- Chunking metadata
    chunk_strategy TEXT NOT NULL,                -- 'fixed_size', 'semantic', 'section'
    chunk_size_tokens INTEGER,
    overlap_tokens INTEGER,
    
    -- Versioning
    chunk_version INTEGER NOT NULL DEFAULT 1,
    
    -- Status
    embedding_status stage_status DEFAULT 'pending',
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chunks_snapshot ON derived_doc_chunks(source_snapshot_id);
CREATE INDEX idx_chunks_entity ON derived_doc_chunks(entity_id);
CREATE INDEX idx_chunks_run ON derived_doc_chunks(pipeline_run_id);
CREATE INDEX idx_chunks_hash ON derived_doc_chunks(chunk_hash);
CREATE INDEX idx_chunks_embedding_status ON derived_doc_chunks(embedding_status) 
    WHERE embedding_status != 'completed';

-- Document embeddings (vector representations)
CREATE TABLE derived_doc_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Source linkage (REQUIRED)
    chunk_id UUID NOT NULL REFERENCES derived_doc_chunks(id),
    source_snapshot_id UUID NOT NULL REFERENCES raw_snapshots(id),
    pipeline_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
    
    -- Version tracking (must match chunk version)
    chunk_version INTEGER NOT NULL,
    
    -- Embedding
    embedding vector(1536) NOT NULL,             -- OpenAI ada-002 or equivalent
    embedding_model TEXT NOT NULL,               -- 'text-embedding-ada-002', etc.
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_embeddings_chunk ON derived_doc_embeddings(chunk_id);
CREATE INDEX idx_embeddings_snapshot ON derived_doc_embeddings(source_snapshot_id);
CREATE INDEX idx_embeddings_run ON derived_doc_embeddings(pipeline_run_id);

-- Vector similarity index (IVFFlat for large scale, HNSW for better recall)
CREATE INDEX idx_embeddings_vector ON derived_doc_embeddings 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Graph nodes (derived from core entities + relationships)
CREATE TABLE derived_graph_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Source linkage (REQUIRED)
    entity_id UUID NOT NULL REFERENCES core_entities(id),
    source_snapshot_id UUID REFERENCES raw_snapshots(id),
    pipeline_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
    
    -- Node properties for graph algorithms
    node_type TEXT NOT NULL,
    label TEXT NOT NULL,
    properties JSONB DEFAULT '{}',
    
    -- Graph metrics (computed)
    in_degree INTEGER,
    out_degree INTEGER,
    pagerank DECIMAL(10,8),
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_graph_nodes_entity ON derived_graph_nodes(entity_id);
CREATE INDEX idx_graph_nodes_type ON derived_graph_nodes(node_type);
CREATE INDEX idx_graph_nodes_run ON derived_graph_nodes(pipeline_run_id);

-- Graph edges (relationships between entities)
CREATE TABLE derived_graph_edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Source linkage (REQUIRED)
    source_snapshot_id UUID REFERENCES raw_snapshots(id),
    pipeline_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
    
    -- Edge endpoints
    source_node_id UUID NOT NULL REFERENCES derived_graph_nodes(id),
    target_node_id UUID NOT NULL REFERENCES derived_graph_nodes(id),
    
    -- Edge properties
    edge_type edge_type NOT NULL,
    weight DECIMAL(5,4) DEFAULT 1.0,             -- For weighted graph algorithms
    properties JSONB DEFAULT '{}',
    
    -- Cascade analysis
    cascade_domain TEXT,                         -- 'power', 'data', 'thermal', 'timing'
    is_critical BOOLEAN DEFAULT FALSE,           -- On critical path?
    
    -- Evidence
    evidence_text TEXT,
    confidence DECIMAL(3,2),
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Prevent duplicate edges of same type
    CONSTRAINT unique_edge UNIQUE (source_node_id, target_node_id, edge_type)
);

CREATE INDEX idx_graph_edges_source ON derived_graph_edges(source_node_id);
CREATE INDEX idx_graph_edges_target ON derived_graph_edges(target_node_id);
CREATE INDEX idx_graph_edges_type ON derived_graph_edges(edge_type);
CREATE INDEX idx_graph_edges_run ON derived_graph_edges(pipeline_run_id);
CREATE INDEX idx_graph_edges_critical ON derived_graph_edges(is_critical) WHERE is_critical = TRUE;

-- Model scores (risk scores, quality scores, etc.)
CREATE TABLE derived_model_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Source linkage (REQUIRED)
    entity_id UUID NOT NULL REFERENCES core_entities(id),
    source_snapshot_id UUID REFERENCES raw_snapshots(id),
    pipeline_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
    
    -- Score
    score_type TEXT NOT NULL,                    -- 'risk', 'quality', 'completeness'
    score_value DECIMAL(5,4) NOT NULL,           -- 0.0000 to 1.0000
    score_model TEXT NOT NULL,                   -- Model that produced this
    score_version TEXT,                          -- Model version
    
    -- Explanation
    reasoning TEXT,
    contributing_factors JSONB,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_scores_entity ON derived_model_scores(entity_id);
CREATE INDEX idx_scores_type ON derived_model_scores(score_type);
CREATE INDEX idx_scores_run ON derived_model_scores(pipeline_run_id);

-- ============================================================================
-- DB GUARDRAILS
-- ============================================================================

-- Trigger: Prevent UPDATE on raw_snapshots
CREATE OR REPLACE FUNCTION prevent_raw_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'UPDATE not allowed on raw_* tables. Raw data is immutable.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_raw_snapshots_no_update
    BEFORE UPDATE ON raw_snapshots
    FOR EACH ROW
    EXECUTE FUNCTION prevent_raw_update();

CREATE TRIGGER trg_raw_telemetry_no_update
    BEFORE UPDATE ON raw_telemetry
    FOR EACH ROW
    EXECUTE FUNCTION prevent_raw_update();

-- Trigger: Prevent DELETE on raw_snapshots (unless purge mode)
CREATE OR REPLACE FUNCTION prevent_raw_delete()
RETURNS TRIGGER AS $$
BEGIN
    -- Allow delete only if special session variable is set (for admin purge)
    IF current_setting('proves.allow_raw_delete', TRUE) = 'true' THEN
        RETURN OLD;
    END IF;
    RAISE EXCEPTION 'DELETE not allowed on raw_* tables. Use SET proves.allow_raw_delete = true for admin purge.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_raw_snapshots_no_delete
    BEFORE DELETE ON raw_snapshots
    FOR EACH ROW
    EXECUTE FUNCTION prevent_raw_delete();

CREATE TRIGGER trg_raw_telemetry_no_delete
    BEFORE DELETE ON raw_telemetry
    FOR EACH ROW
    EXECUTE FUNCTION prevent_raw_delete();

-- Trigger: Validate embedding has matching chunk version
CREATE OR REPLACE FUNCTION validate_embedding_chunk_version()
RETURNS TRIGGER AS $$
DECLARE
    actual_chunk_version INTEGER;
BEGIN
    SELECT chunk_version INTO actual_chunk_version
    FROM derived_doc_chunks
    WHERE id = NEW.chunk_id;
    
    IF actual_chunk_version IS NULL THEN
        RAISE EXCEPTION 'Chunk % does not exist', NEW.chunk_id;
    END IF;
    
    IF actual_chunk_version != NEW.chunk_version THEN
        RAISE EXCEPTION 'Chunk version mismatch: embedding claims %, chunk is %',
            NEW.chunk_version, actual_chunk_version;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_embedding_chunk_version
    BEFORE INSERT ON derived_doc_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION validate_embedding_chunk_version();

-- Trigger: Only allow embedding if chunk is ready
CREATE OR REPLACE FUNCTION validate_chunk_ready_for_embedding()
RETURNS TRIGGER AS $$
DECLARE
    chunk_status stage_status;
BEGIN
    SELECT embedding_status INTO chunk_status
    FROM derived_doc_chunks
    WHERE id = NEW.chunk_id;
    
    -- Allow if pending or in_progress (embedding is what completes it)
    IF chunk_status = 'completed' THEN
        RAISE EXCEPTION 'Chunk % already has embedding (status: completed)', NEW.chunk_id;
    END IF;
    
    -- Mark chunk as completed when embedding is inserted
    UPDATE derived_doc_chunks
    SET embedding_status = 'completed'
    WHERE id = NEW.chunk_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_chunk_embedding_status
    AFTER INSERT ON derived_doc_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION validate_chunk_ready_for_embedding();

-- Trigger: Update pipeline run metrics on snapshot capture
CREATE OR REPLACE FUNCTION update_pipeline_snapshot_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE pipeline_runs
    SET snapshots_captured = snapshots_captured + 1
    WHERE id = NEW.captured_by_run_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_pipeline_snapshot_count
    AFTER INSERT ON raw_snapshots
    FOR EACH ROW
    EXECUTE FUNCTION update_pipeline_snapshot_count();

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE pipeline_runs IS 'Tracks each pipeline execution with per-stage status. The spine of provenance.';
COMMENT ON TABLE raw_snapshots IS 'Immutable captures of source content. Append-only, no updates allowed.';
COMMENT ON TABLE raw_telemetry IS 'Immutable captures of telemetry/metrics data. For future satellite integration.';
COMMENT ON TABLE core_entities IS 'Canonical normalized entities. The "truth" derived from raw captures.';
COMMENT ON TABLE core_equivalences IS 'Cross-ecosystem identity mappings. Links same concepts with different names.';
COMMENT ON TABLE derived_doc_chunks IS 'Text chunks for embedding. Regenerable from raw snapshots.';
COMMENT ON TABLE derived_doc_embeddings IS 'Vector embeddings of chunks. Regenerable, used for semantic search.';
COMMENT ON TABLE derived_graph_nodes IS 'Graph representation of entities. Regenerable, used for cascade analysis.';
COMMENT ON TABLE derived_graph_edges IS 'Relationships between graph nodes. Regenerable, used for cascade analysis.';
COMMENT ON TABLE derived_model_scores IS 'Computed scores (risk, quality, etc). Regenerable as models improve.';

COMMENT ON COLUMN raw_snapshots.content_hash IS 'SHA-256 hash of payload. Used for deduplication and change detection.';
COMMENT ON COLUMN raw_snapshots.status IS 'Aggregate processing status. Shows how far through pipeline this snapshot has progressed.';
COMMENT ON COLUMN core_entities.canonical_key IS 'Stable identifier within entity_type. e.g., "fprime:Svc:CmdDispatcher"';
COMMENT ON COLUMN core_entities.is_current IS 'TRUE for latest version. Old versions have is_current=FALSE and superseded_by_id set.';
COMMENT ON COLUMN derived_doc_chunks.chunk_version IS 'Incremented when rechunking. Embeddings must match this version.';
COMMENT ON COLUMN derived_doc_embeddings.chunk_version IS 'Must match chunk.chunk_version. Enforced by trigger.';

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
