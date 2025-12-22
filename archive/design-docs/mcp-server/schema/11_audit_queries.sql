-- ============================================================================
-- PROVES Library - Pipeline Audit Queries
-- ============================================================================
-- These queries help operators verify pipeline correctness and identify gaps
-- ============================================================================

-- ============================================================================
-- 1. SNAPSHOTS MISSING CHUNKING
-- ============================================================================
-- Shows raw snapshots that have been captured but not yet chunked
-- Useful for identifying pipeline stalls or backlog

-- All snapshots that need chunking
SELECT 
    rs.id AS snapshot_id,
    rs.source_url,
    rs.ecosystem,
    rs.status,
    rs.captured_at,
    pr.run_name AS captured_by_run,
    rs.payload_size_bytes,
    EXTRACT(EPOCH FROM (NOW() - rs.captured_at))/3600 AS hours_since_capture
FROM raw_snapshots rs
JOIN pipeline_runs pr ON rs.captured_by_run_id = pr.id
WHERE rs.status = 'captured'  -- Only captured, not yet parsed
   OR rs.status = 'parsed'    -- Parsed but not chunked
ORDER BY rs.captured_at ASC;

-- Count by status for dashboard
SELECT 
    status,
    ecosystem,
    COUNT(*) AS snapshot_count,
    SUM(payload_size_bytes) / 1024 / 1024 AS total_mb
FROM raw_snapshots
GROUP BY status, ecosystem
ORDER BY status, ecosystem;

-- ============================================================================
-- 2. CHUNKS MISSING EMBEDDINGS  
-- ============================================================================
-- Shows chunks that have been created but not yet embedded
-- Critical for ensuring semantic search coverage

-- All chunks awaiting embedding
SELECT 
    dc.id AS chunk_id,
    dc.source_snapshot_id,
    rs.source_url,
    dc.chunk_index,
    dc.chunk_version,
    dc.embedding_status,
    dc.created_at,
    LENGTH(dc.chunk_text) AS chunk_chars,
    pr.run_name AS chunked_by_run
FROM derived_doc_chunks dc
JOIN raw_snapshots rs ON dc.source_snapshot_id = rs.id
JOIN pipeline_runs pr ON dc.pipeline_run_id = pr.id
WHERE dc.embedding_status != 'completed'
ORDER BY dc.created_at ASC;

-- Summary by status
SELECT 
    dc.embedding_status,
    rs.ecosystem,
    COUNT(*) AS chunk_count,
    AVG(LENGTH(dc.chunk_text)) AS avg_chunk_chars
FROM derived_doc_chunks dc
JOIN raw_snapshots rs ON dc.source_snapshot_id = rs.id
GROUP BY dc.embedding_status, rs.ecosystem
ORDER BY dc.embedding_status, rs.ecosystem;

-- ============================================================================
-- 3. STALE EMBEDDINGS (chunk_version mismatch)
-- ============================================================================
-- Shows embeddings that were created from an older chunk version
-- These need to be regenerated when chunk content changes

-- Find embeddings with version mismatch
SELECT 
    de.id AS embedding_id,
    de.chunk_id,
    dc.chunk_text AS current_chunk_text,
    de.chunk_version AS embedding_chunk_version,
    dc.chunk_version AS current_chunk_version,
    de.embedding_model,
    de.created_at AS embedding_created,
    dc.created_at AS chunk_created
FROM derived_doc_embeddings de
JOIN derived_doc_chunks dc ON de.chunk_id = dc.id
WHERE de.chunk_version < dc.chunk_version
ORDER BY de.created_at ASC;

-- Count stale embeddings by model
SELECT 
    de.embedding_model,
    COUNT(*) AS stale_embedding_count,
    MIN(de.chunk_version) AS oldest_version,
    MAX(dc.chunk_version) AS current_version
FROM derived_doc_embeddings de
JOIN derived_doc_chunks dc ON de.chunk_id = dc.id
WHERE de.chunk_version < dc.chunk_version
GROUP BY de.embedding_model;

-- ============================================================================
-- 4. DERIVED RECORDS MISSING PROVENANCE
-- ============================================================================
-- Shows derived records that don't have proper source_snapshot_id or pipeline_run_id
-- This should NEVER happen if constraints are working, but audit anyway

-- Chunks missing provenance
SELECT 
    'derived_doc_chunks' AS table_name,
    id,
    'source_snapshot_id' AS missing_field
FROM derived_doc_chunks
WHERE source_snapshot_id IS NULL

UNION ALL

SELECT 
    'derived_doc_chunks' AS table_name,
    id,
    'pipeline_run_id' AS missing_field
FROM derived_doc_chunks
WHERE pipeline_run_id IS NULL

UNION ALL

-- Embeddings missing provenance
SELECT 
    'derived_doc_embeddings' AS table_name,
    id,
    'source_snapshot_id' AS missing_field
FROM derived_doc_embeddings
WHERE source_snapshot_id IS NULL

UNION ALL

SELECT 
    'derived_doc_embeddings' AS table_name,
    id,
    'pipeline_run_id' AS missing_field
FROM derived_doc_embeddings
WHERE pipeline_run_id IS NULL

UNION ALL

-- Graph nodes missing provenance
SELECT 
    'derived_graph_nodes' AS table_name,
    id,
    'pipeline_run_id' AS missing_field
FROM derived_graph_nodes
WHERE pipeline_run_id IS NULL

UNION ALL

-- Graph edges missing provenance
SELECT 
    'derived_graph_edges' AS table_name,
    id,
    'pipeline_run_id' AS missing_field
FROM derived_graph_edges
WHERE pipeline_run_id IS NULL

UNION ALL

-- Core entities missing provenance
SELECT 
    'core_entities' AS table_name,
    id,
    'created_by_run_id' AS missing_field
FROM core_entities
WHERE created_by_run_id IS NULL;

-- ============================================================================
-- 5. PIPELINE RUN HEALTH CHECK
-- ============================================================================
-- Shows pipeline runs with inconsistent stage statuses

-- Runs where later stages completed but earlier stages didn't
SELECT 
    id AS run_id,
    run_name,
    capture_status,
    parse_status,
    chunk_status,
    embed_status,
    graph_status,
    score_status,
    CASE 
        WHEN embed_status = 'completed' AND chunk_status != 'completed' THEN 'ERROR: embedded before chunked'
        WHEN chunk_status = 'completed' AND parse_status != 'completed' THEN 'ERROR: chunked before parsed'
        WHEN graph_status = 'completed' AND parse_status != 'completed' THEN 'ERROR: graphed before parsed'
        WHEN score_status = 'completed' AND graph_status != 'completed' THEN 'ERROR: scored before graphed'
        ELSE 'OK'
    END AS health_check
FROM pipeline_runs
WHERE 
    (embed_status = 'completed' AND chunk_status != 'completed')
    OR (chunk_status = 'completed' AND parse_status != 'completed')
    OR (graph_status = 'completed' AND parse_status != 'completed')
    OR (score_status = 'completed' AND graph_status != 'completed');

-- ============================================================================
-- 6. COVERAGE REPORT
-- ============================================================================
-- Shows processing coverage across ecosystems

SELECT 
    rs.ecosystem,
    COUNT(DISTINCT rs.id) AS total_snapshots,
    COUNT(DISTINCT rs.id) FILTER (WHERE rs.status >= 'parsed') AS parsed_snapshots,
    COUNT(DISTINCT rs.id) FILTER (WHERE rs.status >= 'chunked') AS chunked_snapshots,
    COUNT(DISTINCT rs.id) FILTER (WHERE rs.status >= 'embedded') AS embedded_snapshots,
    COUNT(DISTINCT rs.id) FILTER (WHERE rs.status >= 'graphed') AS graphed_snapshots,
    COUNT(DISTINCT dc.id) AS total_chunks,
    COUNT(DISTINCT de.id) AS total_embeddings,
    COUNT(DISTINCT ce.id) AS total_entities,
    COUNT(DISTINCT ge.id) AS total_edges
FROM raw_snapshots rs
LEFT JOIN derived_doc_chunks dc ON dc.source_snapshot_id = rs.id
LEFT JOIN derived_doc_embeddings de ON de.source_snapshot_id = rs.id
LEFT JOIN core_entities ce ON ce.source_snapshot_id = rs.id
LEFT JOIN derived_graph_edges ge ON ge.source_snapshot_id = rs.id
GROUP BY rs.ecosystem
ORDER BY rs.ecosystem;

-- ============================================================================
-- 7. RECENT ACTIVITY
-- ============================================================================
-- Shows what happened in recent pipeline runs

SELECT 
    pr.run_name,
    pr.run_type,
    pr.started_at,
    pr.completed_at,
    EXTRACT(EPOCH FROM (COALESCE(pr.completed_at, NOW()) - pr.started_at))/60 AS duration_minutes,
    pr.snapshots_captured,
    pr.entities_created,
    pr.chunks_created,
    pr.embeddings_created,
    pr.edges_created,
    pr.error_count,
    pr.capture_status,
    pr.embed_status,
    pr.graph_status
FROM pipeline_runs pr
ORDER BY pr.started_at DESC
LIMIT 20;

-- ============================================================================
-- 8. ENTITY CROSS-REFERENCE
-- ============================================================================
-- Shows entities and their equivalences across ecosystems

SELECT 
    ce1.ecosystem AS ecosystem_a,
    ce1.name AS name_a,
    ce2.ecosystem AS ecosystem_b,
    ce2.name AS name_b,
    eq.confidence,
    eq.is_validated,
    eq.evidence_text
FROM core_equivalences eq
JOIN core_entities ce1 ON eq.entity_a_id = ce1.id
JOIN core_entities ce2 ON eq.entity_b_id = ce2.id
WHERE ce1.is_current = TRUE AND ce2.is_current = TRUE
ORDER BY eq.confidence DESC, ce1.ecosystem, ce1.name;

-- ============================================================================
-- 9. ORPHANED DERIVED RECORDS
-- ============================================================================
-- Shows derived records whose source snapshots were somehow lost
-- This should never happen, but detect data integrity issues

SELECT 
    'derived_doc_chunks' AS table_name,
    dc.id,
    dc.source_snapshot_id
FROM derived_doc_chunks dc
LEFT JOIN raw_snapshots rs ON dc.source_snapshot_id = rs.id
WHERE rs.id IS NULL

UNION ALL

SELECT 
    'derived_doc_embeddings' AS table_name,
    de.id,
    de.source_snapshot_id
FROM derived_doc_embeddings de
LEFT JOIN raw_snapshots rs ON de.source_snapshot_id = rs.id
WHERE rs.id IS NULL

UNION ALL

SELECT 
    'derived_graph_edges' AS table_name,
    ge.id,
    ge.source_snapshot_id
FROM derived_graph_edges ge
LEFT JOIN raw_snapshots rs ON ge.source_snapshot_id = rs.id
WHERE rs.id IS NULL AND ge.source_snapshot_id IS NOT NULL;

-- ============================================================================
-- 10. SEMANTIC SEARCH READINESS
-- ============================================================================
-- Shows whether the system is ready for semantic search queries

SELECT 
    'Embedding Coverage' AS metric,
    COUNT(*) AS value,
    'chunks with embeddings' AS unit
FROM derived_doc_chunks dc
WHERE EXISTS (
    SELECT 1 FROM derived_doc_embeddings de 
    WHERE de.chunk_id = dc.id 
    AND de.chunk_version = dc.chunk_version
)

UNION ALL

SELECT 
    'Chunks Pending Embedding' AS metric,
    COUNT(*) AS value,
    'chunks waiting' AS unit
FROM derived_doc_chunks
WHERE embedding_status = 'pending'

UNION ALL

SELECT 
    'Stale Embeddings' AS metric,
    COUNT(*) AS value,
    'need regeneration' AS unit
FROM derived_doc_embeddings de
JOIN derived_doc_chunks dc ON de.chunk_id = dc.id
WHERE de.chunk_version < dc.chunk_version

UNION ALL

SELECT 
    'Distinct Embedding Models' AS metric,
    COUNT(DISTINCT embedding_model) AS value,
    'models in use' AS unit
FROM derived_doc_embeddings;
