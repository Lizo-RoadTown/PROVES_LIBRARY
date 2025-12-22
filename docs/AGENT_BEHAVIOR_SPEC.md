# PROVES Library - Agent Behavior Specification

## Overview

This document defines how AI agents interact with the layered database architecture. Agents must follow these rules to ensure data integrity, provenance tracking, and pipeline correctness.

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PIPELINE TRACKING                                  │
│  pipeline_runs: Every operation is part of a tracked run                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│   RAW LAYER   │          │  CORE LAYER   │          │ DERIVED LAYER │
│  (immutable)  │    ──►   │ (normalized)  │    ──►   │ (regenerable) │
│               │          │               │          │               │
│ raw_snapshots │          │ core_entities │          │ doc_chunks    │
│ raw_telemetry │          │ core_equiv    │          │ doc_embeddings│
│               │          │               │          │ graph_nodes   │
│               │          │               │          │ graph_edges   │
│               │          │               │          │ model_scores  │
└───────────────┘          └───────────────┘          └───────────────┘
```

## Agent Roles

### 1. Capture Agent (Extractor)
**Purpose**: Fetch and store raw content from sources

**Allowed Operations**:
- INSERT into `raw_snapshots`
- INSERT into `pipeline_runs` (to create a run)
- UPDATE `pipeline_runs` (to update status/metrics)

**Forbidden Operations**:
- UPDATE `raw_snapshots` (immutable)
- DELETE `raw_snapshots` (immutable)
- Any writes to core_* or derived_* tables

**Behavior**:
```python
# 1. Create or get pipeline run
run_id = get_or_create_pipeline_run(
    run_name="fprime_crawl_2024_12_22",
    run_type="incremental"
)

# 2. For each source URL
for url in sources_to_crawl:
    # Fetch content
    content = fetch_url(url)
    
    # Compute hash
    content_hash = sha256(content)
    
    # Check if we already have this exact content
    existing = SELECT id FROM raw_snapshots 
               WHERE source_url = url AND content_hash = content_hash
    
    if existing:
        continue  # Skip, already captured
    
    # Insert new snapshot
    INSERT INTO raw_snapshots (
        source_url, source_type, ecosystem,
        content_hash, payload, payload_size_bytes,
        captured_by_run_id, status
    ) VALUES (
        url, 'github_file', 'fprime',
        content_hash, content_as_json, len(content),
        run_id, 'captured'
    )
```

### 2. Parser Agent
**Purpose**: Extract normalized entities from raw snapshots

**Allowed Operations**:
- INSERT into `core_entities`
- INSERT into `core_equivalences`
- UPDATE `raw_snapshots.status` (captured → parsed)
- UPDATE `pipeline_runs` (status/metrics)

**Forbidden Operations**:
- UPDATE/DELETE on `raw_snapshots` content fields
- Any writes to derived_* tables

**Behavior**:
```python
# Process snapshots that are captured but not parsed
snapshots = SELECT * FROM raw_snapshots WHERE status = 'captured'

for snapshot in snapshots:
    # Parse the payload
    entities = parse_entities(snapshot.payload)
    
    for entity in entities:
        # Create canonical key: ecosystem:namespace:name
        canonical_key = f"{snapshot.ecosystem}:{entity.namespace}:{entity.name}"
        
        # Check if entity already exists (may need versioning)
        existing = SELECT * FROM core_entities 
                   WHERE entity_type = entity.type 
                   AND canonical_key = canonical_key 
                   AND is_current = TRUE
        
        if existing:
            # Create new version if content changed
            if entity.attributes != existing.attributes:
                UPDATE core_entities SET is_current = FALSE, 
                       superseded_by_id = new_id WHERE id = existing.id
                # Insert new version
        else:
            INSERT INTO core_entities (...)
    
    # Update snapshot status
    UPDATE raw_snapshots SET status = 'parsed' WHERE id = snapshot.id
```

### 3. Chunking Agent
**Purpose**: Split documents into chunks for embedding

**Allowed Operations**:
- INSERT into `derived_doc_chunks`
- UPDATE `raw_snapshots.status` (parsed → chunked)
- UPDATE `pipeline_runs` (status/metrics)

**Forbidden Operations**:
- Any writes to raw_* tables
- Any writes to core_* tables (except status)

**Behavior**:
```python
# IMPORTANT: Only chunk documents that have been parsed
snapshots = SELECT * FROM raw_snapshots WHERE status = 'parsed'

for snapshot in snapshots:
    # Get the text content from payload
    text = extract_text(snapshot.payload)
    
    # Chunk using configured strategy
    chunks = chunk_text(text, strategy='semantic', max_tokens=512)
    
    for i, chunk_text in enumerate(chunks):
        INSERT INTO derived_doc_chunks (
            source_snapshot_id,
            pipeline_run_id,
            entity_id,  -- Link to parsed entity if available
            chunk_index,
            chunk_text,
            chunk_hash,
            chunk_strategy,
            chunk_version,
            embedding_status
        ) VALUES (
            snapshot.id,
            current_run_id,
            related_entity_id,
            i,
            chunk_text,
            sha256(chunk_text),
            'semantic',
            1,
            'pending'  -- Ready for embedding
        )
    
    UPDATE raw_snapshots SET status = 'chunked' WHERE id = snapshot.id
```

### 4. Embedding Agent
**Purpose**: Generate vector embeddings for chunks

**Allowed Operations**:
- INSERT into `derived_doc_embeddings`
- UPDATE `derived_doc_chunks.embedding_status` (via trigger)
- UPDATE `raw_snapshots.status` (chunked → embedded)
- UPDATE `pipeline_runs` (status/metrics)

**Forbidden Operations**:
- Any writes to raw_* content
- UPDATE chunk content (would require re-embedding)

**Critical Rules**:
- MUST include `chunk_version` that matches the chunk's current version
- Trigger will validate version match
- Trigger will set chunk's `embedding_status = 'completed'`

**Behavior**:
```python
# Get chunks pending embedding
chunks = SELECT * FROM derived_doc_chunks WHERE embedding_status = 'pending'

for chunk in chunks:
    # Generate embedding
    embedding = embed(chunk.chunk_text, model='text-embedding-ada-002')
    
    # Insert embedding (trigger validates version)
    INSERT INTO derived_doc_embeddings (
        chunk_id,
        source_snapshot_id,
        pipeline_run_id,
        chunk_version,  -- MUST match current chunk version
        embedding,
        embedding_model
    ) VALUES (
        chunk.id,
        chunk.source_snapshot_id,
        current_run_id,
        chunk.chunk_version,
        embedding,
        'text-embedding-ada-002'
    )

# Update snapshot status when all chunks embedded
UPDATE raw_snapshots rs SET status = 'embedded'
WHERE rs.id IN (
    SELECT source_snapshot_id FROM derived_doc_chunks dc
    GROUP BY source_snapshot_id
    HAVING COUNT(*) = COUNT(*) FILTER (WHERE embedding_status = 'completed')
)
AND rs.status = 'chunked'
```

### 5. Graph Agent
**Purpose**: Build graph nodes and edges for cascade analysis

**Allowed Operations**:
- INSERT into `derived_graph_nodes`
- INSERT into `derived_graph_edges`
- UPDATE `raw_snapshots.status` (embedded → graphed)
- UPDATE `pipeline_runs` (status/metrics)

**Behavior**:
```python
# Create nodes from entities
entities = SELECT * FROM core_entities WHERE is_current = TRUE

for entity in entities:
    INSERT INTO derived_graph_nodes (
        entity_id,
        source_snapshot_id,
        pipeline_run_id,
        node_type,
        label,
        properties
    ) VALUES (
        entity.id,
        entity.source_snapshot_id,
        current_run_id,
        entity.entity_type,
        entity.name,
        entity.attributes
    )

# Create edges from relationships found during parsing
# (stored in entity attributes or separate relationship extraction)
for relationship in extracted_relationships:
    INSERT INTO derived_graph_edges (
        source_snapshot_id,
        pipeline_run_id,
        source_node_id,
        target_node_id,
        edge_type,
        weight,
        evidence_text,
        confidence
    ) VALUES (...)
```

### 6. Scoring Agent
**Purpose**: Compute risk/quality scores using models

**Allowed Operations**:
- INSERT into `derived_model_scores`
- UPDATE `raw_snapshots.status` (graphed → scored)
- UPDATE `pipeline_runs` (status/metrics)

**Behavior**:
```python
# Score entities based on graph structure and content
entities = SELECT ce.*, 
                  gn.in_degree, gn.out_degree,
                  array_agg(ge.edge_type) as edge_types
           FROM core_entities ce
           JOIN derived_graph_nodes gn ON gn.entity_id = ce.id
           LEFT JOIN derived_graph_edges ge ON ge.source_node_id = gn.id
           WHERE ce.is_current = TRUE
           GROUP BY ce.id, gn.id

for entity in entities:
    # Compute risk score
    risk_score = compute_risk(entity)
    
    INSERT INTO derived_model_scores (
        entity_id,
        source_snapshot_id,
        pipeline_run_id,
        score_type,
        score_value,
        score_model,
        reasoning
    ) VALUES (
        entity.id,
        entity.source_snapshot_id,
        current_run_id,
        'risk',
        risk_score,
        'proves_risk_v1',
        explain_risk(entity)
    )
```

## Status Flow

```
Snapshot Status:   captured → parsed → chunked → embedded → graphed → scored
                      │          │         │          │          │         │
Pipeline Stage:    CAPTURE   PARSE     CHUNK     EMBED      GRAPH    SCORE
                      │          │         │          │          │         │
Tables Written:    raw_*    core_*    chunks  embeddings  nodes    scores
                                                          edges
```

## HITL (Human-in-the-Loop) Integration

**When to require HITL approval**:
1. Cross-ecosystem equivalences (confidence < 0.9)
2. Critical path graph edges (is_critical = TRUE)
3. Risk scores above threshold (score_value > 0.8)

**Workflow**:
```python
# During graph agent
if edge.is_critical:
    # Store with pending validation
    INSERT INTO derived_graph_edges (..., 
        properties = jsonb_set(properties, '{validation_status}', '"pending"')
    )
    
    # Interrupt for HITL
    await hitl_approval(
        type='critical_edge',
        data=edge,
        message='Detected critical dependency path'
    )
    
    # On approval, update
    UPDATE derived_graph_edges 
    SET properties = jsonb_set(properties, '{validation_status}', '"approved"')
    WHERE id = edge.id
```

## Regeneration

Derived tables can be regenerated:

```sql
-- Delete all derived data for a snapshot
DELETE FROM derived_model_scores WHERE source_snapshot_id = $1;
DELETE FROM derived_graph_edges WHERE source_snapshot_id = $1;
DELETE FROM derived_graph_nodes WHERE source_snapshot_id = $1;
DELETE FROM derived_doc_embeddings WHERE source_snapshot_id = $1;
DELETE FROM derived_doc_chunks WHERE source_snapshot_id = $1;

-- Reset snapshot status
UPDATE raw_snapshots SET status = 'parsed' WHERE id = $1;

-- Re-run pipeline from chunk stage
```

## Provenance Queries

Every derived record can answer:
1. **Where did this come from?** → `source_snapshot_id` → `raw_snapshots.source_url`
2. **When was it created?** → `created_at`
3. **What pipeline created it?** → `pipeline_run_id` → `pipeline_runs.run_name`
4. **Is it stale?** → Compare `chunk_version` or check latest `pipeline_run_id`
