"""
Storage Sub-Agent
Specialized agent for storing findings and dependencies in the knowledge graph

DOMAIN TABLE WORKFLOW (2024-12-22):
1. store_extraction() - Store extracted entities in staging_extractions
2. promote_to_core() - Move validated entities to core_entities
3. store_equivalence() - Link entities across ecosystems

Tables used:
- staging_extractions: Raw extracted entities awaiting validation
- core_entities: Validated, promoted entities (source of truth)
- core_equivalences: Cross-ecosystem entity mappings
"""
import sys
import os
import hashlib
import uuid
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../scripts'))

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langsmith import traceable
from graph_manager import GraphManager


def get_db_connection():
    """Get a database connection from environment."""
    import psycopg
    from dotenv import load_dotenv
    
    # Load from project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    load_dotenv(os.path.join(project_root, '.env'))
    
    db_url = os.environ.get('NEON_DATABASE_URL')
    if not db_url:
        raise ValueError("NEON_DATABASE_URL not set")
    return psycopg.connect(db_url)


def get_or_create_pipeline_run(conn, run_name: str = "curator_extraction") -> str:
    """Get or create a pipeline run for tracking. Returns run_id."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id FROM pipeline_runs 
            WHERE run_name = %s AND score_status = 'pending'
            ORDER BY created_at DESC LIMIT 1
        """, (run_name,))
        existing = cur.fetchone()
        if existing:
            return str(existing[0])
        
        cur.execute("""
            INSERT INTO pipeline_runs (run_name, run_type, triggered_by)
            VALUES (%s, 'extraction', 'storage_agent')
            RETURNING id
        """, (run_name,))
        return str(cur.fetchone()[0])


@tool
def store_extraction(
    candidate_type: str,
    candidate_key: str,
    raw_evidence: str,
    source_snapshot_id: str,
    ecosystem: str = "external",
    properties: dict = None,
    confidence_score: float = 0.8,
    confidence_reason: str = "LLM extraction",
    evidence_type: str = "definition_spec",
    reasoning_trail: dict = None,
    duplicate_check: dict = None,
    source_metadata: dict = None
) -> str:
    """
    Store an extracted entity in staging_extractions.

    STORE EVERYTHING - validator decides what's promoted to core.

    Args:
        candidate_type: 'component', 'port', 'command', 'telemetry', 'event', 'parameter',
                        'data_type', 'dependency', 'connection', 'inheritance'
        candidate_key: Entity name/key (e.g., "I2CDriver", "PowerManager")
        raw_evidence: Exact quote from source (REQUIRED - this is the evidence)
        source_snapshot_id: ID from raw_snapshots (REQUIRED - links to source document)
        ecosystem: 'fprime', 'proveskit', 'pysquared', 'cubesat_general', 'external'
        properties: JSON dict of entity-specific properties (ports, commands, etc.)
        confidence_score: How confident the extractor is (0.0 to 1.0)
        confidence_reason: Why this confidence level
        evidence_type: 'definition_spec', 'interface_contract', 'example', 'narrative',
                       'table_diagram', 'comment', 'inferred'
        reasoning_trail: Agent's reasoning process (NEW - helps human understand logic):
            {
                "verified_entities_consulted": ["entity_123", "entity_456"],
                "staging_examples_reviewed": 8,
                "validation_patterns_checked": ["i2c_address_required"],
                "comparison_logic": "Matched structure of 3 verified I2C components",
                "uncertainty_factors": ["No driver implementation found"]
            }
        duplicate_check: Results of duplicate checking (NEW - helps human decide merge vs create):
            {
                "exact_matches": [],
                "similar_entities": [{"id": "entity_abc", "similarity": 0.73}],
                "recommendation": "create_new" | "merge_with" | "needs_review"
            }
        source_metadata: Source document metadata (NEW - helps human verify):
            {
                "source_url": "https://...",
                "source_type": "webpage",
                "fetch_timestamp": "2025-12-23T10:45:32Z"
            }

    Returns:
        Confirmation with extraction ID, or error message
    """
    try:
        import json
        conn = get_db_connection()

        # Get or create pipeline run
        run_id = get_or_create_pipeline_run(conn)

        with conn.cursor() as cur:
            payload = json.dumps(properties) if properties else '{}'

            # Build evidence JSONB with metadata for human verification
            evidence_data = {
                "raw_text": raw_evidence
            }

            # Add agent reasoning trail (helps human understand logic)
            if reasoning_trail:
                evidence_data["reasoning_trail"] = reasoning_trail

            # Add duplicate check results (helps human decide merge vs create)
            if duplicate_check:
                evidence_data["duplicate_check"] = duplicate_check

            # Add source metadata (helps human verify source)
            if source_metadata:
                evidence_data["source_metadata"] = source_metadata

            evidence = json.dumps(evidence_data)

            cur.execute("""
                INSERT INTO staging_extractions (
                    pipeline_run_id, snapshot_id, agent_id, agent_version,
                    candidate_type, candidate_key, candidate_payload,
                    ecosystem, confidence_score, confidence_reason,
                    evidence, evidence_type, status
                ) VALUES (
                    %s::uuid, %s::uuid, %s, %s,
                    %s::candidate_type, %s, %s::jsonb,
                    %s::ecosystem_type, %s, %s,
                    %s::jsonb, %s::evidence_type, 'pending'::candidate_status
                ) RETURNING extraction_id
            """, (
                run_id, source_snapshot_id, 'storage_agent', '1.0',
                candidate_type, candidate_key, payload,
                ecosystem, confidence_score, confidence_reason,
                evidence, evidence_type
            ))
            extraction_id = cur.fetchone()[0]
        conn.commit()
        conn.close()

        return f"[STAGED] Extraction recorded (ID: {extraction_id})\n  Type: {candidate_type}\n  Key: {candidate_key}\n  Confidence: {confidence_score}"

    except Exception as e:
        return f"Error storing extraction: {str(e)}"


@tool
def promote_to_core(
    extraction_id: str,
    canonical_name: str = None,
    merge_with_entity_id: str = None
) -> str:
    """
    Promote a validated extraction to core_entities.
    
    Call this after validator approves the extraction.
    
    Args:
        extraction_id: ID from staging_extractions
        canonical_name: Optional unified name (if different from extracted name)
        merge_with_entity_id: If this is a duplicate, merge with existing entity
    """
    try:
        import json
        conn = get_db_connection()
        
        # Get or create pipeline run
        run_id = get_or_create_pipeline_run(conn, "curator_promotion")
        
        with conn.cursor() as cur:
            # Get the staging extraction
            cur.execute("""
                SELECT candidate_type::text, candidate_key, candidate_payload, ecosystem::text,
                       confidence_score, snapshot_id
                FROM staging_extractions WHERE extraction_id = %s::uuid
            """, (extraction_id,))
            row = cur.fetchone()
            
            if not row:
                return f"Extraction {extraction_id} not found"
            
            candidate_type, candidate_key, payload, ecosystem, confidence, snapshot_id = row
            final_name = canonical_name or candidate_key
            
            if merge_with_entity_id:
                # Update existing entity's attributes
                cur.execute("""
                    UPDATE core_entities 
                    SET attributes = attributes || %s::jsonb,
                        updated_at = NOW()
                    WHERE id = %s::uuid
                    RETURNING id
                """, (json.dumps(payload) if payload else '{}', merge_with_entity_id))
                entity_id = merge_with_entity_id
            else:
                # Create new core entity
                cur.execute("""
                    INSERT INTO core_entities (
                        entity_type, canonical_key, name, display_name,
                        ecosystem, attributes,
                        source_snapshot_id, created_by_run_id
                    ) VALUES (
                        %s::entity_type, %s, %s, %s,
                        %s::ecosystem_type, %s::jsonb,
                        %s::uuid, %s::uuid
                    ) RETURNING id
                """, (
                    candidate_type, candidate_key, final_name, final_name,
                    ecosystem, json.dumps(payload) if payload else '{}',
                    snapshot_id, run_id
                ))
                entity_id = cur.fetchone()[0]
            
            # Mark staging extraction as accepted
            cur.execute("""
                UPDATE staging_extractions 
                SET status = 'accepted'::candidate_status
                WHERE extraction_id = %s::uuid
            """, (extraction_id,))
            
        conn.commit()
        conn.close()
        
        return f"[PROMOTED] {final_name} → core_entities (ID: {entity_id})"
        
    except Exception as e:
        return f"Error promoting extraction: {str(e)}"


@tool
def store_finding(
    finding_type: str,
    subject: str,
    raw_text: str,
    source_url: str,
    source_type: str,
    source_ecosystem: str = "unknown",
    predicate: str = None,
    object_value: str = None,
    interpreted_meaning: str = None,
    confidence: float = 0.8,
    reasoning: str = None
) -> str:
    """
    LEGACY: Store a raw finding in the findings table.
    
    NOTE: Prefer store_extraction() for new extractions.
    This is kept for backward compatibility.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO findings (
                    finding_type, subject, predicate, object, raw_text,
                    interpreted_meaning, source_url, source_type, source_ecosystem,
                    extracted_by, extraction_model, extraction_confidence, 
                    extraction_reasoning, status
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, 'raw'
                ) RETURNING id
            """, (
                finding_type, subject, predicate, object_value, raw_text,
                interpreted_meaning, source_url, source_type, source_ecosystem,
                'storage_agent', 'claude-3-5-haiku-20241022', confidence,
                reasoning
            ))
            finding_id = cur.fetchone()[0]
        conn.commit()
        conn.close()
        
        return f"[STORED] Finding recorded (ID: {finding_id})\n  Type: {finding_type}\n  Subject: {subject}\n  Source: {source_url}"
        
    except Exception as e:
        return f"Error storing finding: {str(e)}"


@tool
def store_equivalence(
    entity_a_id: str,
    entity_b_id: str,
    equivalence_type: str,
    confidence: float,
    evidence_snapshot_id: str = None,
    reasoning: str = None
) -> str:
    """
    Store a cross-ecosystem equivalence in core_equivalences.
    
    Use this when two entities from different ecosystems represent the same concept.
    Example: F' "TlmChan" ≡ ProvesKit "Telemetry"
    
    Args:
        entity_a_id: ID of first core_entity
        entity_b_id: ID of second core_entity
        equivalence_type: 'same_concept', 'similar_function', 'wrapper', 'alias'
        confidence: How confident we are (0.0 to 1.0)
        evidence_snapshot_id: Optional snapshot that supports this equivalence
        reasoning: Why these are equivalent
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO core_equivalences (
                    entity_a_id, entity_b_id, 
                    equivalence_type, confidence_score,
                    evidence_snapshot_id, reasoning
                ) VALUES (
                    %s::uuid, %s::uuid,
                    %s, %s,
                    %s::uuid, %s
                )
                ON CONFLICT (entity_a_id, entity_b_id) DO UPDATE
                SET confidence_score = GREATEST(core_equivalences.confidence_score, EXCLUDED.confidence_score),
                    reasoning = COALESCE(EXCLUDED.reasoning, core_equivalences.reasoning)
                RETURNING id
            """, (
                entity_a_id, entity_b_id,
                equivalence_type, confidence,
                evidence_snapshot_id, reasoning
            ))
            equiv_id = cur.fetchone()[0]
            
        conn.commit()
        conn.close()
        
        return f"[EQUIVALENCE] Entities linked (ID: {equiv_id})\n  Type: {equivalence_type}\n  Confidence: {confidence}"
        
    except Exception as e:
        return f"Error storing equivalence: {str(e)}"


@tool
def legacy_store_equivalence(
    ecosystem_a: str,
    name_a: str,
    ecosystem_b: str,
    name_b: str,
    confidence: float,
    source_url: str,
    canonical_name: str = None
) -> str:
    """
    LEGACY: Store equivalence using ecosystem/name pairs.
    
    NOTE: Prefer store_equivalence() with entity IDs for new code.
    This is kept for backward compatibility.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # First store as a finding
            cur.execute("""
                INSERT INTO findings (
                    finding_type, subject, predicate, object, raw_text,
                    source_url, source_type, source_ecosystem,
                    extracted_by, extraction_confidence, status
                ) VALUES (
                    'equivalence', %s, 'equivalent_to', %s,
                    %s, %s, 'inference', %s,
                    'storage_agent', %s, 'raw'
                ) RETURNING id
            """, (
                f"{ecosystem_a}:{name_a}",
                f"{ecosystem_b}:{name_b}",
                f"{name_a} ({ecosystem_a}) is equivalent to {name_b} ({ecosystem_b})",
                source_url, ecosystem_a, confidence
            ))
            finding_id = cur.fetchone()[0]
            
            # Then store in equivalences table
            cur.execute("""
                INSERT INTO equivalences (
                    ecosystem_a, name_a, ecosystem_b, name_b,
                    confidence, evidence_finding_id, canonical_name, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'raw')
                ON CONFLICT (ecosystem_a, name_a, ecosystem_b, name_b) DO UPDATE
                SET confidence = GREATEST(equivalences.confidence, EXCLUDED.confidence)
                RETURNING id
            """, (
                ecosystem_a, name_a, ecosystem_b, name_b,
                confidence, finding_id, canonical_name
            ))
            equiv_id = cur.fetchone()[0]
            
        conn.commit()
        conn.close()
        
        return f"[EQUIVALENCE] {name_a} ({ecosystem_a}) ≡ {name_b} ({ecosystem_b})\n  Confidence: {confidence}\n  ID: {equiv_id}"
        
    except Exception as e:
        return f"Error storing equivalence: {str(e)}"


@tool
def get_staging_statistics() -> str:
    """Get statistics about staging_extractions, core_entities, and domain tables."""
    try:
        conn = get_db_connection()
        stats = []
        
        with conn.cursor() as cur:
            # Count staging extractions by status
            cur.execute("""
                SELECT status::text, COUNT(*) FROM staging_extractions GROUP BY status ORDER BY status
            """)
            status_counts = cur.fetchall()
            if status_counts:
                stats.append("Staging extractions by status:")
                for status, count in status_counts:
                    stats.append(f"  {status}: {count}")
            
            # Count staging by entity type
            cur.execute("""
                SELECT entity_type::text, COUNT(*) FROM staging_extractions GROUP BY entity_type ORDER BY COUNT(*) DESC
            """)
            type_counts = cur.fetchall()
            if type_counts:
                stats.append("\nStaging extractions by type:")
                for etype, count in type_counts:
                    stats.append(f"  {etype}: {count}")
            
            # Count core entities
            cur.execute("SELECT COUNT(*) FROM core_entities")
            core_count = cur.fetchone()[0]
            stats.append(f"\nCore entities: {core_count}")
            
            # Count raw snapshots
            cur.execute("SELECT COUNT(*) FROM raw_snapshots")
            snapshot_count = cur.fetchone()[0]
            stats.append(f"Raw snapshots: {snapshot_count}")
            
            # Count equivalences
            cur.execute("SELECT COUNT(*) FROM core_equivalences")
            equiv_count = cur.fetchone()[0]
            stats.append(f"Core equivalences: {equiv_count}")
        
        conn.close()
        return "\n".join(stats) if stats else "No domain table data yet."
        
    except Exception as e:
        return f"Error getting statistics: {str(e)}"


@tool
def record_crawled_source(
    source_url: str,
    source_type: str,
    source_ecosystem: str = "unknown",
    findings_count: int = 0,
    status: str = "success"
) -> str:
    """
    LEGACY: Record that we've crawled a URL.
    
    NOTE: Raw content is now stored in raw_snapshots by extractor tools.
    This is kept for backward compatibility.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO crawled_sources (
                    source_url, source_type, source_ecosystem,
                    findings_extracted, last_extraction_status
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (source_url) DO UPDATE
                SET last_crawled_at = NOW(),
                    crawl_count = crawled_sources.crawl_count + 1,
                    findings_extracted = crawled_sources.findings_extracted + EXCLUDED.findings_extracted,
                    last_extraction_status = EXCLUDED.last_extraction_status
                RETURNING id, crawl_count
            """, (source_url, source_type, source_ecosystem, findings_count, status))
            row = cur.fetchone()
            source_id, crawl_count = row
        conn.commit()
        conn.close()
        
        if crawl_count > 1:
            return f"[RECRAWLED] {source_url} (crawl #{crawl_count}, +{findings_count} findings)"
        return f"[CRAWLED] {source_url} ({findings_count} findings)"
        
    except Exception as e:
        return f"Error recording source: {str(e)}"


@tool
def get_findings_statistics() -> str:
    """LEGACY: Get statistics about findings table."""
    try:
        conn = get_db_connection()
        stats = []
        
        with conn.cursor() as cur:
            # Count findings by status
            cur.execute("""
                SELECT status, COUNT(*) FROM findings GROUP BY status ORDER BY status
            """)
            status_counts = cur.fetchall()
            if status_counts:
                stats.append("Findings by status:")
                for status, count in status_counts:
                    stats.append(f"  {status}: {count}")
            
            # Count findings by type
            cur.execute("""
                SELECT finding_type, COUNT(*) FROM findings GROUP BY finding_type ORDER BY COUNT(*) DESC
            """)
            type_counts = cur.fetchall()
            if type_counts:
                stats.append("\nFindings by type:")
                for ftype, count in type_counts:
                    stats.append(f"  {ftype}: {count}")
            
            # Count findings by ecosystem
            cur.execute("""
                SELECT source_ecosystem, COUNT(*) FROM findings GROUP BY source_ecosystem ORDER BY COUNT(*) DESC
            """)
            eco_counts = cur.fetchall()
            if eco_counts:
                stats.append("\nFindings by ecosystem:")
                for eco, count in eco_counts:
                    stats.append(f"  {eco}: {count}")
            
            # Count equivalences
            cur.execute("SELECT COUNT(*) FROM equivalences")
            equiv_count = cur.fetchone()[0]
            stats.append(f"\nLegacy equivalences: {equiv_count}")
            
            # Count crawled sources
            cur.execute("SELECT COUNT(*) FROM crawled_sources")
            source_count = cur.fetchone()[0]
            stats.append(f"Sources crawled: {source_count}")
        
        conn.close()
        return "\n".join(stats) if stats else "No findings data yet."
        
    except Exception as e:
        return f"Error getting statistics: {str(e)}"


@tool
def get_graph_statistics() -> str:
    """Get current knowledge graph statistics (kg_nodes and kg_relationships)."""
    try:
        gm = GraphManager()
        stats = gm.get_statistics()

        result = "Knowledge Graph Statistics:\n"
        result += f"  Total nodes: {stats['total_nodes']}\n"
        result += f"  Total relationships: {stats['total_relationships']}\n"

        if stats.get('nodes_by_type'):
            result += "\n  Nodes by type:\n"
            for node_type, count in stats['nodes_by_type'].items():
                result += f"    {node_type}: {count}\n"

        if stats.get('relationships_by_type'):
            result += "\n  Relationships by type:\n"
            for rel_type, count in stats['relationships_by_type'].items():
                result += f"    {rel_type}: {count}\n"

        return result

    except Exception as e:
        return f"Error getting statistics: {str(e)}"


@traceable(name="storage_subagent")
def create_storage_agent():
    """
    Create the storage sub-agent

    This agent specializes in:
    - store_extraction() → staging_extractions (new primary workflow)
    - promote_to_core() → core_entities (after validation)
    - store_equivalence() → core_equivalences (cross-ecosystem links)
    - get_staging_statistics() → domain table stats

    Legacy tools (backward compatible):
    - store_finding() → findings table
    - legacy_store_equivalence() → equivalences table
    - record_crawled_source() → crawled_sources

    Uses Claude Haiku 3.5 for cost optimization (storage is simple database operations)
    """
    model = ChatAnthropic(
        model="claude-3-5-haiku-20241022",
        temperature=0.1,
    )

    tools = [
        # NEW domain table workflow
        store_extraction,
        promote_to_core,
        store_equivalence,
        get_staging_statistics,
        # Legacy tools for backward compatibility
        store_finding,
        legacy_store_equivalence,
        record_crawled_source,
        get_findings_statistics,
        # Legacy kg operations
        get_graph_statistics,
    ]

    agent = create_react_agent(model, tools)
    return agent
