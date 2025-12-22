"""
Storage Sub-Agent
Specialized agent for storing findings and dependencies in the knowledge graph

NEW WORKFLOW (2024-12-22):
1. store_finding() - Store raw observations first (everything gets recorded)
2. Later: promote validated findings to kg_nodes/kg_relationships
"""
import sys
import os
import hashlib
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
    Store a raw finding (observation) from documentation.
    
    STORE EVERYTHING - we decide what's important later.
    
    Args:
        finding_type: 'fact', 'constraint', 'config', 'warning', 'procedure', 'equivalence', 'dependency_candidate'
        subject: What it's about (e.g., "I2CDriver", "PowerManager")
        raw_text: Exact quote from source (REQUIRED - this is the evidence)
        source_url: Full URL to the source (REQUIRED - no citation = no storage)
        source_type: 'github_file', 'github_readme', 'docs_site', 'local_file'
        source_ecosystem: 'fprime', 'proveskit', 'pysquared', 'cubesat_general', 'unknown'
        predicate: Optional relationship verb ("uses", "requires", "equals")
        object_value: Optional target ("address 0x50", "3.3V max")
        interpreted_meaning: What the agent thinks this means
        confidence: How confident the agent is (0.0 to 1.0)
        reasoning: Why this finding is important
    
    Returns:
        Confirmation with finding ID, or error message
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
    ecosystem_a: str,
    name_a: str,
    ecosystem_b: str,
    name_b: str,
    confidence: float,
    source_url: str,
    canonical_name: str = None
) -> str:
    """
    Store a cross-ecosystem equivalence (when two ecosystems use different names for the same thing).
    
    Example: F' calls it "TlmChan", ProvesKit calls it "Telemetry" -> they're equivalent
    
    Args:
        ecosystem_a: First ecosystem ('fprime', 'proveskit', etc.)
        name_a: Name in first ecosystem
        ecosystem_b: Second ecosystem
        name_b: Name in second ecosystem
        confidence: How confident we are these are equivalent (0.0 to 1.0)
        source_url: URL that suggests this equivalence
        canonical_name: Our unified name for this concept (optional)
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
def record_crawled_source(
    source_url: str,
    source_type: str,
    source_ecosystem: str = "unknown",
    findings_count: int = 0,
    status: str = "success"
) -> str:
    """
    Record that we've crawled a URL (prevents re-crawling, tracks coverage).
    
    Call this AFTER extracting findings from a source.
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
    """Get statistics about findings, equivalences, and crawled sources."""
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
            stats.append(f"\nEquivalences recorded: {equiv_count}")
            
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
    - Storing RAW FINDINGS first (everything gets recorded)
    - Recording equivalences between ecosystems
    - Tracking what sources have been crawled
    - Later: promoting validated findings to kg_nodes/kg_relationships

    Uses Claude Haiku 3.5 for cost optimization (storage is simple database operations)
    """
    model = ChatAnthropic(
        model="claude-3-5-haiku-20241022",
        temperature=0.1,
    )

    tools = [
        # New findings-first workflow
        store_finding,
        store_equivalence,
        record_crawled_source,
        get_findings_statistics,
        # Legacy kg operations (for promotion later)
        get_graph_statistics,
    ]

    agent = create_react_agent(model, tools)
    return agent
