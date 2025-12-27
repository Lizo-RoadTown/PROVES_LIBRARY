#!/usr/bin/env python3
"""
Setup PROVES Library domain tables in Neon PostgreSQL.

This script creates all the domain-specific tables for auditable extraction:
- pipeline_runs: Track each extraction run
- raw_snapshots: Immutable source documents  
- staging_extractions: Candidates with confidence scores
- validation_decisions: Decision audit trail
- core_entities: Promoted canonical entities
- core_equivalences: Cross-ecosystem mappings
- derived_* tables: Chunks, embeddings, graph nodes/edges, scores

Run this AFTER setup_checkpointer.py which creates LangGraph's internal tables.
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
db_url = os.getenv('NEON_DATABASE_URL')

if not db_url:
    print("Error: NEON_DATABASE_URL not set")
    exit(1)

conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

print("=" * 60)
print("PROVES Library Domain Tables Setup")
print("=" * 60)

# ============================================================================
# EXTENSIONS
# ============================================================================
print("\n[1/8] Extensions...")
extensions = [
    ("uuid-ossp", "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""),
    ("vector", "CREATE EXTENSION IF NOT EXISTS vector"),
    ("pg_trgm", "CREATE EXTENSION IF NOT EXISTS pg_trgm"),
]
for name, sql in extensions:
    try:
        cur.execute(sql)
        print(f"  [OK] {name}")
    except Exception as e:
        print(f"  ✗ {name}: {e}")

# ============================================================================
# ENUMS
# ============================================================================
print("\n[2/8] ENUMs...")

enums = [
    # From 10_layered_architecture.sql
    ("ecosystem_type", """
        CREATE TYPE ecosystem_type AS ENUM (
            'fprime', 'proveskit', 'pysquared', 'cubesat_general', 'external'
        )
    """),
    ("source_type", """
        CREATE TYPE source_type AS ENUM (
            'github_file', 'github_directory', 'docs_webpage', 
            'local_file', 'api_response', 'manual_entry'
        )
    """),
    ("stage_status", """
        CREATE TYPE stage_status AS ENUM (
            'pending', 'in_progress', 'completed', 'failed', 'skipped'
        )
    """),
    ("snapshot_status", """
        CREATE TYPE snapshot_status AS ENUM (
            'captured', 'parsed', 'chunked', 'embedded', 'graphed', 'scored'
        )
    """),
    ("entity_type", """
        CREATE TYPE entity_type AS ENUM (
            'repository', 'artifact', 'component', 'interface',
            'constraint', 'metric', 'procedure', 'failure_mode'
        )
    """),
    ("edge_type", """
        CREATE TYPE edge_type AS ENUM (
            'depends_on', 'provides', 'conflicts_with', 'implements',
            'contains', 'references', 'equivalent_to', 'mitigates', 'causes', 'measured_by'
        )
    """),
    
    # From 12_extraction_enums.sql
    ("confidence_level", """
        CREATE TYPE confidence_level AS ENUM ('low', 'medium', 'high')
    """),
    ("evidence_type", """
        CREATE TYPE evidence_type AS ENUM (
            'definition_spec', 'interface_contract', 'example',
            'narrative', 'table_diagram', 'comment', 'inferred'
        )
    """),
    ("extraction_method", """
        CREATE TYPE extraction_method AS ENUM ('pattern', 'llm', 'hybrid', 'manual')
    """),
    ("candidate_status", """
        CREATE TYPE candidate_status AS ENUM (
            'pending', 'accepted', 'rejected', 'merged', 'needs_context'
        )
    """),
    ("candidate_type", """
        CREATE TYPE candidate_type AS ENUM (
            'component', 'port', 'command', 'telemetry', 'event',
            'parameter', 'data_type', 'dependency', 'connection', 'inheritance'
        )
    """),
    
    # From 13_validation_staging.sql
    ("validation_decision_type", """
        CREATE TYPE validation_decision_type AS ENUM (
            'accept', 'reject', 'merge', 'needs_more_evidence', 'defer'
        )
    """),
    ("decider_type", """
        CREATE TYPE decider_type AS ENUM (
            'human', 'validator_agent', 'consensus', 'rule_based'
        )
    """),
]

for name, sql in enums:
    try:
        cur.execute(sql)
        print(f"  [OK] {name}")
    except psycopg2.errors.DuplicateObject:
        print(f"  - {name} (already exists)")
        conn.rollback()
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        conn.rollback()

# ============================================================================
# PIPELINE TRACKING
# ============================================================================
print("\n[3/8] Pipeline tracking tables...")

cur.execute("""
    CREATE TABLE IF NOT EXISTS pipeline_runs (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        run_name TEXT NOT NULL,
        run_type TEXT NOT NULL,
        target_ecosystem ecosystem_type,
        target_source_url TEXT,
        started_at TIMESTAMP NOT NULL DEFAULT NOW(),
        completed_at TIMESTAMP,
        capture_status stage_status DEFAULT 'pending',
        parse_status stage_status DEFAULT 'pending',
        chunk_status stage_status DEFAULT 'pending',
        embed_status stage_status DEFAULT 'pending',
        graph_status stage_status DEFAULT 'pending',
        score_status stage_status DEFAULT 'pending',
        snapshots_captured INTEGER DEFAULT 0,
        entities_created INTEGER DEFAULT 0,
        chunks_created INTEGER DEFAULT 0,
        embeddings_created INTEGER DEFAULT 0,
        edges_created INTEGER DEFAULT 0,
        error_count INTEGER DEFAULT 0,
        last_error TEXT,
        triggered_by TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
""")
print("  [OK] pipeline_runs")

# ============================================================================
# RAW LAYER (Immutable)
# ============================================================================
print("\n[4/8] Raw layer tables...")

cur.execute("""
    CREATE TABLE IF NOT EXISTS raw_snapshots (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        source_url TEXT NOT NULL,
        source_type source_type NOT NULL,
        ecosystem ecosystem_type NOT NULL,
        content_hash TEXT NOT NULL,
        payload JSONB NOT NULL,
        payload_size_bytes INTEGER NOT NULL,
        captured_at TIMESTAMP NOT NULL DEFAULT NOW(),
        captured_by_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
        source_commit_sha TEXT,
        source_etag TEXT,
        source_last_modified TIMESTAMP,
        status snapshot_status NOT NULL DEFAULT 'captured',
        created_at TIMESTAMP DEFAULT NOW()
    )
""")
print("  [OK] raw_snapshots")

# Indexes
indexes = [
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_snapshots_identity ON raw_snapshots(source_url, content_hash)",
    "CREATE INDEX IF NOT EXISTS idx_raw_snapshots_url ON raw_snapshots(source_url)",
    "CREATE INDEX IF NOT EXISTS idx_raw_snapshots_ecosystem ON raw_snapshots(ecosystem)",
    "CREATE INDEX IF NOT EXISTS idx_raw_snapshots_status ON raw_snapshots(status)",
]
for sql in indexes:
    try:
        cur.execute(sql)
    except:
        pass
print("  [OK] raw_snapshots indexes")

# ============================================================================
# STAGING & VALIDATION
# ============================================================================
print("\n[5/8] Staging & validation tables...")

cur.execute("""
    CREATE TABLE IF NOT EXISTS staging_extractions (
        extraction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        pipeline_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
        snapshot_id UUID NOT NULL REFERENCES raw_snapshots(id),
        agent_id TEXT NOT NULL,
        agent_version TEXT,
        candidate_type candidate_type NOT NULL,
        candidate_key TEXT NOT NULL,
        candidate_payload JSONB NOT NULL,
        ecosystem ecosystem_type NOT NULL,
        confidence_score NUMERIC(3,2) NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
        confidence_reason TEXT NOT NULL,
        evidence JSONB NOT NULL,
        evidence_type evidence_type NOT NULL,
        status candidate_status NOT NULL DEFAULT 'pending',
        promoted_to_id UUID,
        promoted_at TIMESTAMP,
        merged_into_id UUID,
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    )
""")
print("  [OK] staging_extractions")

cur.execute("""
    CREATE TABLE IF NOT EXISTS validation_decisions (
        decision_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        extraction_id UUID NOT NULL REFERENCES staging_extractions(extraction_id),
        decided_by TEXT NOT NULL,
        decider_type decider_type NOT NULL,
        decision validation_decision_type NOT NULL,
        decision_reason TEXT NOT NULL,
        canonical_id UUID,
        merged_into_extraction_id UUID,
        confidence_at_decision NUMERIC(3,2),
        evidence_at_decision JSONB,
        feedback JSONB,
        decided_at TIMESTAMP NOT NULL DEFAULT NOW(),
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
""")
print("  [OK] validation_decisions")

# Indexes
for sql in [
    "CREATE INDEX IF NOT EXISTS idx_staging_status ON staging_extractions(status)",
    "CREATE INDEX IF NOT EXISTS idx_staging_pipeline ON staging_extractions(pipeline_run_id)",
    "CREATE INDEX IF NOT EXISTS idx_staging_confidence ON staging_extractions(confidence_score DESC)",
    "CREATE INDEX IF NOT EXISTS idx_decisions_extraction ON validation_decisions(extraction_id)",
    "CREATE INDEX IF NOT EXISTS idx_decisions_decision ON validation_decisions(decision)",
]:
    try:
        cur.execute(sql)
    except:
        pass
print("  [OK] staging/validation indexes")

# ============================================================================
# CORE LAYER
# ============================================================================
print("\n[6/8] Core layer tables...")

cur.execute("""
    CREATE TABLE IF NOT EXISTS core_entities (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        entity_type entity_type NOT NULL,
        canonical_key TEXT NOT NULL,
        name TEXT NOT NULL,
        display_name TEXT,
        description TEXT,
        ecosystem ecosystem_type,
        namespace TEXT,
        attributes JSONB DEFAULT '{}',
        source_snapshot_id UUID REFERENCES raw_snapshots(id),
        created_by_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
        version INTEGER NOT NULL DEFAULT 1,
        superseded_by_id UUID,
        is_current BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    )
""")
print("  [OK] core_entities")

cur.execute("""
    CREATE TABLE IF NOT EXISTS core_equivalences (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        entity_a_id UUID NOT NULL REFERENCES core_entities(id),
        entity_b_id UUID NOT NULL REFERENCES core_entities(id),
        confidence DECIMAL(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
        evidence_text TEXT,
        source_snapshot_id UUID REFERENCES raw_snapshots(id),
        created_by_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
        is_validated BOOLEAN DEFAULT FALSE,
        validated_by TEXT,
        validated_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW()
    )
""")
print("  [OK] core_equivalences")

# Indexes
for sql in [
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_core_entities_identity ON core_entities(entity_type, canonical_key) WHERE is_current = TRUE",
    "CREATE INDEX IF NOT EXISTS idx_core_entities_type ON core_entities(entity_type)",
    "CREATE INDEX IF NOT EXISTS idx_core_entities_ecosystem ON core_entities(ecosystem)",
]:
    try:
        cur.execute(sql)
    except:
        pass
print("  [OK] core indexes")

# ============================================================================
# DERIVED LAYER
# ============================================================================
print("\n[7/8] Derived layer tables...")

cur.execute("""
    CREATE TABLE IF NOT EXISTS derived_doc_chunks (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        source_snapshot_id UUID NOT NULL REFERENCES raw_snapshots(id),
        pipeline_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
        entity_id UUID REFERENCES core_entities(id),
        chunk_index INTEGER NOT NULL,
        chunk_text TEXT NOT NULL,
        chunk_hash TEXT NOT NULL,
        chunk_strategy TEXT NOT NULL,
        chunk_size_tokens INTEGER,
        overlap_tokens INTEGER,
        chunk_version INTEGER NOT NULL DEFAULT 1,
        embedding_status stage_status DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT NOW()
    )
""")
print("  [OK] derived_doc_chunks")

cur.execute("""
    CREATE TABLE IF NOT EXISTS derived_doc_embeddings (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        chunk_id UUID NOT NULL REFERENCES derived_doc_chunks(id),
        source_snapshot_id UUID NOT NULL REFERENCES raw_snapshots(id),
        pipeline_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
        chunk_version INTEGER NOT NULL,
        embedding vector(1536) NOT NULL,
        embedding_model TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    )
""")
print("  [OK] derived_doc_embeddings")

cur.execute("""
    CREATE TABLE IF NOT EXISTS derived_graph_nodes (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        entity_id UUID NOT NULL REFERENCES core_entities(id),
        source_snapshot_id UUID REFERENCES raw_snapshots(id),
        pipeline_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
        node_type TEXT NOT NULL,
        label TEXT NOT NULL,
        properties JSONB DEFAULT '{}',
        in_degree INTEGER,
        out_degree INTEGER,
        pagerank DECIMAL(10,8),
        created_at TIMESTAMP DEFAULT NOW()
    )
""")
print("  [OK] derived_graph_nodes")

cur.execute("""
    CREATE TABLE IF NOT EXISTS derived_graph_edges (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        source_snapshot_id UUID REFERENCES raw_snapshots(id),
        pipeline_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
        source_node_id UUID NOT NULL REFERENCES derived_graph_nodes(id),
        target_node_id UUID NOT NULL REFERENCES derived_graph_nodes(id),
        edge_type edge_type NOT NULL,
        weight DECIMAL(5,4) DEFAULT 1.0,
        properties JSONB DEFAULT '{}',
        cascade_domain TEXT,
        is_critical BOOLEAN DEFAULT FALSE,
        evidence_text TEXT,
        confidence DECIMAL(3,2),
        created_at TIMESTAMP DEFAULT NOW()
    )
""")
print("  [OK] derived_graph_edges")

cur.execute("""
    CREATE TABLE IF NOT EXISTS derived_model_scores (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        entity_id UUID NOT NULL REFERENCES core_entities(id),
        source_snapshot_id UUID REFERENCES raw_snapshots(id),
        pipeline_run_id UUID NOT NULL REFERENCES pipeline_runs(id),
        score_type TEXT NOT NULL,
        score_value DECIMAL(5,4) NOT NULL,
        score_model TEXT NOT NULL,
        score_version TEXT,
        reasoning TEXT,
        contributing_factors JSONB,
        created_at TIMESTAMP DEFAULT NOW()
    )
""")
print("  [OK] derived_model_scores")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
print("\n[8/8] Helper functions...")

cur.execute("""
    CREATE OR REPLACE FUNCTION derive_confidence_level(score NUMERIC)
    RETURNS confidence_level AS $$
    BEGIN
        IF score >= 0.8 THEN RETURN 'high';
        ELSIF score >= 0.5 THEN RETURN 'medium';
        ELSE RETURN 'low';
        END IF;
    END;
    $$ LANGUAGE plpgsql IMMUTABLE
""")
print("  [OK] derive_confidence_level()")

# ============================================================================
# VERIFICATION
# ============================================================================
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name
""")
tables = [t[0] for t in cur.fetchall()]
print(f"\nTables in database ({len(tables)}):")
for t in tables:
    marker = "[OK]" if t in [
        'pipeline_runs', 'raw_snapshots', 'staging_extractions', 
        'validation_decisions', 'core_entities', 'core_equivalences',
        'derived_doc_chunks', 'derived_doc_embeddings', 
        'derived_graph_nodes', 'derived_graph_edges', 'derived_model_scores'
    ] else "•"
    print(f"  {marker} {t}")

cur.execute("""
    SELECT typname FROM pg_type 
    WHERE typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
    AND typtype = 'e'
    ORDER BY typname
""")
enums = [t[0] for t in cur.fetchall()]
print(f"\nENUMs in database ({len(enums)}):")
for e in enums:
    print(f"  [OK] {e}")

cur.close()
conn.close()

print("\n" + "=" * 60)
print("[OK] Domain tables setup complete!")
print("=" * 60)
print("\nNext steps:")
print("  1. Update agent code to INSERT into these tables")
print("  2. Run the curator agent to populate data")
print("  3. Query staging_extractions for audit trail")
