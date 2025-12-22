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
│ raw_extracts  │          │               │          │ graph_nodes   │
│               │          │               │          │ graph_edges   │
│               │          │               │          │ model_scores  │
└───────────────┘          └───────────────┘          └───────────────┘

## Confidence Rubric (Agents MUST Use)

All extraction agents must assign confidence scores using this rubric:

### HIGH (0.80–1.00)
- ✓ Doc explicitly defines it ("is/shall/must") or shows formal signature/table
- ✓ Term matches known F´ vocabulary (component/port/command/telemetry/event)
- ✓ Multiple sources agree

### MEDIUM (0.50–0.79)
- ~ Strong cues but not a formal definition
- ~ Extracted from an example that looks representative
- ~ Missing 1–2 key properties

### LOW (0.00–0.49)
- ✗ Inferred from narrative text
- ✗ Only appears once, unclear context
- ✗ Conflicts with another statement or lacks supporting structure

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

### 2. Extraction Agent
**Purpose**: Extract candidates from raw snapshots WITH confidence metadata

**Allowed Operations**:
- INSERT into `raw_extractions` (with full confidence scoring)
- INSERT into `extraction_confidence_details` (for per-dimension breakdown)
- UPDATE `pipeline_runs` (status/metrics)

**Forbidden Operations**:
- Any writes to `core_entities` (that's the Validator's job after HITL)
- UPDATE/DELETE on `raw_snapshots` (immutable)
- Setting `status = 'accepted'` (requires HITL or Validator Agent)

**Critical Rules**:
1. NEVER auto-promote extractions to `core_entities`
2. ALL extractions start as `status = 'pending'`
3. MUST assign `confidence_score` using the rubric above
4. MUST provide `evidence_text` with exact source quote
5. MUST provide `evidence_location` with doc/page/line info

**Required Fields Per Extraction**:
```python
# For EVERY extracted candidate:
{
    "confidence_score": 0.0-1.0,      # Numeric score
    "confidence_level": "low|medium|high",  # Auto-derived from score
    "confidence_reason": "...",        # Short text explaining score
    
    # Evidence trail
    "evidence_type": "definition_spec|interface_contract|example|narrative|...",
    "evidence_text": "...",           # Exact quote from source
    "evidence_location": {            # Pointer to source
        "doc": "...",
        "lines": [10, 15],
        "url": "..."
    },
    
    # What we couldn't get
    "missing_fields": ["units", "rate"],  # List of gaps
    
    # How we extracted
    "extraction_method": "pattern|llm|hybrid",
    "extraction_method_version": "llm:claude-3.5-sonnet-20241022",
    
    # NEVER skip this
    "status": "pending"
}
```

**Confidence Dimensions** (for complex extractions):
- `type_confidence`: "Is this really a port vs a parameter?"
- `field_confidence`: "Are these extracted properties correct (units, rate, type)?"
- `relationship_confidence`: "Does this dependency actually exist?"
- `completeness_confidence`: "Did we extract all the fields?"

**Behavior**:
```python
# Process raw snapshots
snapshots = SELECT * FROM raw_snapshots WHERE status = 'captured'

for snapshot in snapshots:
    # Extract candidates using LLM
    candidates = extract_candidates(
        snapshot.payload,
        model="claude-3.5-sonnet"
    )
    
    for candidate in candidates:
        # Compute confidence using rubric
        confidence_score = assess_confidence(candidate, snapshot.payload)
        
        INSERT INTO raw_extractions (
            source_snapshot_id,
            pipeline_run_id,
            candidate_type,
            canonical_key,
            extracted_name,
            extracted_properties,
            ecosystem,
            
            # CONFIDENCE (required)
            confidence_score,        # e.g., 0.85
            confidence_level,        # auto: 'high'
            confidence_reason,       # "Formal port definition with signature"
            
            # DIMENSIONAL CONFIDENCE (optional but helpful)
            type_confidence,         # 0.90 - definitely a port
            type_confidence_reason,  # "Matches F´ port syntax"
            field_confidence,        # 0.75 - missing units
            field_confidence_reason, # "Rate extracted, units not specified"
            
            # EVIDENCE (required)
            evidence_type,           # 'definition_spec'
            evidence_text,           # "port BufferGet: Fw.Buffer"
            evidence_location,       # {"doc": "...", "lines": [45, 52]}
            
            # METADATA
            extraction_method,       # 'llm'
            extraction_method_version, # 'claude-3.5-sonnet-20241022'
            missing_fields,          # ['description']
            
            # STATUS - always pending!
            status                   # 'pending'
        )
    
    # Update metrics
    UPDATE pipeline_runs 
    SET entities_created = entities_created + len(candidates)
    WHERE id = current_run_id
```

**Scoring Examples**:

| Extraction | Score | Level | Reason |
|------------|-------|-------|--------|
| Port with formal `.fpp` definition | 0.95 | high | Formal F´ syntax, interface contract |
| Component mentioned in prose | 0.35 | low | Narrative only, no formal definition |
| Telemetry from example code | 0.65 | medium | Strong cues, missing units |
| Dependency stated "A uses B" | 0.80 | high | Explicit statement, verb "uses" |
| Inferred relationship | 0.30 | low | Single mention, unclear context |

### 3. Validator Agent (HITL Gateway)
**Purpose**: Review pending extractions and promote to canonical

**Allowed Operations**:
- UPDATE `raw_extractions.status` (pending → accepted|rejected|merged|needs_context)
- INSERT into `core_entities` (ONLY for accepted extractions)
- UPDATE `raw_extractions.promoted_to_entity_id` (after promotion)
- UPDATE `raw_snapshots.status` (captured → parsed, when extractions promoted)

**Forbidden Operations**:
- Accepting extractions without review
- Modifying `raw_extractions` content fields (only status/review fields)

**Behavior**:
```python
# Get pending extractions, prioritize high confidence
extractions = SELECT * FROM raw_extractions 
              WHERE status = 'pending'
              ORDER BY confidence_score DESC

for extraction in extractions:
    # Present to human or auto-validate high confidence
    if extraction.confidence_level == 'high' and extraction.missing_fields is None:
        # Auto-accept if confidence is high and complete
        decision = 'accepted'
    else:
        # Require human review
        decision = await human_review(extraction)
    
    if decision == 'accepted':
        # Promote to core_entities
        entity_id = INSERT INTO core_entities (...)
        
        UPDATE raw_extractions 
        SET status = 'accepted',
            promoted_to_entity_id = entity_id,
            promoted_at = NOW(),
            reviewed_by = 'validator_agent'
        WHERE id = extraction.id
    
    elif decision == 'rejected':
        UPDATE raw_extractions
        SET status = 'rejected',
            reviewed_by = 'human:alice',
            review_notes = 'Not a valid component'
        WHERE id = extraction.id
```

### 5. Parser Agent
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

### 6. Chunking Agent
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

### 7. Embedding Agent
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

### 8. Graph Agent
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

### 9. Scoring Agent
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
