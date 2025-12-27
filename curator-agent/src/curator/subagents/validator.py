"""
Validator Sub-Agent
Specialized agent for validating extractions and recording decisions

DOMAIN TABLE WORKFLOW (2024-12-22):
1. Review staging_extractions awaiting validation
2. Record decisions in validation_decisions table
3. Approved extractions -> promoted to core_entities by storage agent
"""
import sys
import os
import uuid
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../scripts'))

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langsmith import traceable
from scripts.core.graph_manager import GraphManager


def get_db_connection():
    """Get a database connection from environment."""
    import psycopg
    from dotenv import load_dotenv
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    load_dotenv(os.path.join(project_root, '.env'))
    
    db_url = os.environ.get('NEON_DATABASE_URL')
    if not db_url:
        raise ValueError("NEON_DATABASE_URL not set")
    return psycopg.connect(db_url)


@tool
def get_pending_extractions(limit: int = 10) -> str:
    """
    Get staging_extractions awaiting validation.
    
    Returns extractions with status='pending' for review.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT extraction_id, candidate_type::text, candidate_key, 
                       evidence, ecosystem::text, confidence_score,
                       confidence_reason, created_at
                FROM staging_extractions 
                WHERE status = 'pending'::candidate_status
                ORDER BY created_at ASC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
        conn.close()
        
        if not rows:
            return "No pending extractions to validate."
        
        result = f"Found {len(rows)} pending extractions:\n\n"
        for row in rows:
            ext_id, ctype, ckey, evidence, ecosystem, conf, reason, created = row
            evidence_str = str(evidence) if evidence else ""
            result += f"ID: {ext_id}\n"
            result += f"  Type: {ctype} | Key: {ckey}\n"
            result += f"  Ecosystem: {ecosystem} | Confidence: {conf}\n"
            result += f"  Evidence: {evidence_str[:200]}...\n" if len(evidence_str) > 200 else f"  Evidence: {evidence_str}\n"
            result += f"  Reason: {reason}\n\n"
        
        return result
        
    except Exception as e:
        return f"Error getting pending extractions: {str(e)}"


@tool
def record_validation_decision(
    extraction_id: str,
    decision: str,
    reasoning: str,
    confidence_override: float = None,
    suggested_canonical_name: str = None
) -> str:
    """
    Record a validation decision for a staging extraction.
    
    Args:
        extraction_id: UUID of the staging_extraction
        decision: 'accept', 'reject', 'merge', 'needs_more_evidence', 'defer'
        reasoning: Why this decision was made
        confidence_override: Optional new confidence score (if validator disagrees)
        suggested_canonical_name: For accept - suggested unified name
    
    The decision is recorded in validation_decisions.
    If accepted, storage agent should call promote_to_core().
    """
    try:
        import json
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Build evidence JSON
            evidence_json = json.dumps({
                "reasoning": reasoning,
                "suggested_name": suggested_canonical_name
            }) if suggested_canonical_name else None
            
            # Record the decision
            cur.execute("""
                INSERT INTO validation_decisions (
                    extraction_id, decided_by, decider_type,
                    decision, decision_reason, 
                    confidence_at_decision, evidence_at_decision
                ) VALUES (
                    %s::uuid, %s, 'validator_agent'::decider_type,
                    %s::validation_decision_type, %s,
                    %s, %s::jsonb
                ) RETURNING decision_id
            """, (
                extraction_id, 'curator_validator_agent',
                decision, reasoning,
                confidence_override, evidence_json
            ))
            decision_id = cur.fetchone()[0]
            
            # Update extraction status based on decision
            # Uses candidate_status enum: 'pending', 'accepted', 'rejected', 'merged', 'needs_context'
            new_status = {
                'accept': 'accepted',
                'reject': 'rejected',
                'needs_more_evidence': 'needs_context',
                'defer': 'pending',
                'merge': 'merged'
            }.get(decision, 'pending')
            
            cur.execute("""
                UPDATE staging_extractions 
                SET status = %s::candidate_status
                WHERE extraction_id = %s::uuid
            """, (new_status, extraction_id))
            
        conn.commit()
        conn.close()
        
        return f"[DECISION] {decision.upper()} recorded (ID: {decision_id})\n  Extraction: {extraction_id}\n  Reasoning: {reasoning}"
        
    except Exception as e:
        return f"Error recording decision: {str(e)}"


@tool
def check_for_duplicates(entity_name: str, entity_type: str) -> str:
    """
    Check if an entity already exists in core_entities.
    
    Use this before approving to detect duplicates that should be merged.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Exact match on canonical_key
            cur.execute("""
                SELECT id, canonical_key, name, entity_type::text, ecosystem::text
                FROM core_entities 
                WHERE LOWER(canonical_key) = LOWER(%s) AND is_current = TRUE
            """, (entity_name,))
            exact = cur.fetchall()
            
            # Similar names (trigram similarity if pg_trgm is installed)
            try:
                cur.execute("""
                    SELECT id, canonical_key, name, entity_type::text, ecosystem::text,
                           similarity(canonical_key, %s) as sim
                    FROM core_entities 
                    WHERE similarity(canonical_key, %s) > 0.3 AND is_current = TRUE
                    ORDER BY sim DESC
                    LIMIT 5
                """, (entity_name, entity_name))
                similar = cur.fetchall()
            except Exception:
                # pg_trgm not installed - fall back to LIKE
                cur.execute("""
                    SELECT id, canonical_key, name, entity_type::text, ecosystem::text
                    FROM core_entities 
                    WHERE LOWER(canonical_key) LIKE LOWER(%s) AND is_current = TRUE
                    LIMIT 5
                """, (f'%{entity_name}%',))
                similar = [(r[0], r[1], r[2], r[3], r[4], 0.5) for r in cur.fetchall()]
            
        conn.close()
        
        result = f"Duplicate check for '{entity_name}' ({entity_type}):\n\n"
        
        if exact:
            result += "[WARNING] EXACT MATCHES:\n"
            for eid, key, name, etype, eco in exact:
                result += f"  - {name} (key: {key}, {etype}, {eco}) ID: {eid}\n"
        else:
            result += "[OK] No exact matches\n"
        
        if similar:
            result += "\n📊 Similar entities:\n"
            for row in similar:
                eid, key, name, etype, eco = row[:5]
                sim = row[5] if len(row) > 5 else 0.5
                result += f"  - {name} (key: {key}, {etype}, {eco}) similarity: {sim:.2f}\n"
        
        return result
        
    except Exception as e:
        return f"Error checking duplicates: {str(e)}"


@tool
def check_if_dependency_exists(source: str, target: str, relationship_type: str) -> str:
    """LEGACY: Check if a dependency already exists in the knowledge graph (kg_nodes)."""
    try:
        gm = GraphManager()
        source_node = gm.get_node_by_name(source)

        if not source_node:
            return f"[NEW] Component '{source}' doesn't exist yet. Safe to add."

        # Check existing relationships
        existing = gm.get_node_relationships(source_node['id'], direction='outgoing')

        # Check for exact match
        for rel in existing:
            if rel['target_name'] == target and rel['relationship_type'] == relationship_type:
                return f"[DUPLICATE] Already exists: {source} --[{relationship_type}]--> {target}"

        # Check for conflicts
        if relationship_type == 'conflicts_with':
            return f"[CONFLICT] Need careful review: {source} conflicts with {target}"

        return f"[OK] Safe to add: {source} --[{relationship_type}]--> {target}"

    except Exception as e:
        return f"Error checking dependency: {str(e)}"


@tool
def verify_schema_compliance(component: str, depends_on: str, relationship_type: str, criticality: str = None) -> str:
    """Verify that a dependency follows ERV schema and naming conventions."""
    # Valid ERV types
    valid_types = ['depends_on', 'requires', 'enables', 'conflicts_with', 'mitigates', 'causes']

    issues = []

    if relationship_type not in valid_types:
        issues.append(f"Invalid relationship type '{relationship_type}'. Must be one of: {', '.join(valid_types)}")

    if not component or not depends_on:
        issues.append("Component and depends_on cannot be empty")

    if component == depends_on:
        issues.append("Component cannot depend on itself")

    if issues:
        return f"[INVALID] Schema issues:\n" + "\n".join(f"  - {issue}" for issue in issues)

    return f"[VALID] Schema compliant: {component} --[{relationship_type}]--> {depends_on}"


@tool
def search_similar_dependencies(component_name: str) -> str:
    """LEGACY: Search for similar dependencies in kg_nodes."""
    try:
        gm = GraphManager()
        # Search for components with similar names
        similar = gm.search_nodes(name_pattern=component_name, limit=5)

        if not similar:
            return f"No similar components found for '{component_name}'"

        result = f"Found {len(similar)} similar components:\n"
        for node in similar:
            result += f"  - {node['name']} ({node['node_type']})\n"
            # Get their dependencies
            deps = gm.get_node_relationships(node['id'], direction='outgoing')
            if deps:
                result += f"    Has {len(deps)} dependencies\n"

        return result

    except Exception as e:
        return f"Error searching: {str(e)}"


@tool
def query_verified_entities(
    entity_type: str = None,
    ecosystem: str = None,
    name_pattern: str = None,
    limit: int = 20
) -> str:
    """
    Query core_entities (verified truth) - AGENT DECIDES WHAT HELPS.

    Use this to see what verified data exists and calibrate your confidence.

    Examples:
    - query_verified_entities(entity_type='component', ecosystem='proveskit')
      -> See all verified PROVES Kit components

    - query_verified_entities(name_pattern='%I2C%')
      -> Find entities related to I2C

    - query_verified_entities(entity_type='component', limit=10)
      -> Get 10 examples of verified components

    Returns: Entity details including canonical_key, ecosystem, attributes
    """
    try:
        conn = get_db_connection()

        # Build query dynamically based on filters
        query = """
            SELECT id, canonical_key, name, entity_type::text, ecosystem::text,
                   attributes, created_at
            FROM core_entities
            WHERE is_current = TRUE
        """
        params = []

        if entity_type:
            query += " AND entity_type = %s::entity_type"
            params.append(entity_type)

        if ecosystem:
            query += " AND ecosystem = %s::ecosystem_type"
            params.append(ecosystem)

        if name_pattern:
            query += " AND (canonical_key ILIKE %s OR name ILIKE %s)"
            params.extend([name_pattern, name_pattern])

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        conn.close()

        if not rows:
            return "No verified entities found matching criteria."

        result = f"Found {len(rows)} verified entities:\n\n"
        for row in rows:
            entity_id, canonical_key, name, etype, eco, attrs, created = row
            result += f"ID: {entity_id}\n"
            result += f"  Key: {canonical_key} | Name: {name}\n"
            result += f"  Type: {etype} | Ecosystem: {eco}\n"
            if attrs:
                import json
                attrs_dict = attrs if isinstance(attrs, dict) else json.loads(attrs)
                result += f"  Attributes: {json.dumps(attrs_dict)[:200]}...\n"
            result += f"  Created: {created}\n\n"

        return result

    except Exception as e:
        return f"Error querying verified entities: {str(e)}"


@tool
def query_staging_history(
    status: str = None,
    candidate_type: str = None,
    ecosystem: str = None,
    min_confidence: float = None,
    max_confidence: float = None,
    limit: int = 20
) -> str:
    """
    Query staging_extractions history - SEE WHAT WAS ACCEPTED/REJECTED.

    Use this to understand what confidence levels humans accepted,
    what patterns led to rejections, and learn from past decisions.

    Examples:
    - query_staging_history(status='accepted', candidate_type='component')
      -> See what components were accepted

    - query_staging_history(status='rejected')
      -> Learn from rejections

    - query_staging_history(min_confidence=0.8, status='accepted')
      -> See high-confidence items that were accepted

    Returns: Extraction details with confidence scores and reasons
    """
    try:
        conn = get_db_connection()

        query = """
            SELECT extraction_id, candidate_type::text, candidate_key,
                   ecosystem::text, confidence_score, confidence_reason,
                   status::text, evidence, created_at
            FROM staging_extractions
            WHERE 1=1
        """
        params = []

        if status:
            query += " AND status = %s::candidate_status"
            params.append(status)

        if candidate_type:
            query += " AND candidate_type = %s::candidate_type"
            params.append(candidate_type)

        if ecosystem:
            query += " AND ecosystem = %s::ecosystem_type"
            params.append(ecosystem)

        if min_confidence is not None:
            query += " AND confidence_score >= %s"
            params.append(min_confidence)

        if max_confidence is not None:
            query += " AND confidence_score <= %s"
            params.append(max_confidence)

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        conn.close()

        if not rows:
            return "No staging history found matching criteria."

        result = f"Found {len(rows)} staging extractions:\n\n"
        for row in rows:
            ext_id, ctype, ckey, eco, conf, reason, stat, evidence, created = row
            result += f"ID: {ext_id}\n"
            result += f"  Type: {ctype} | Key: {ckey}\n"
            result += f"  Ecosystem: {eco} | Status: {stat}\n"
            result += f"  Confidence: {conf} - {reason}\n"
            if evidence:
                evidence_str = str(evidence)[:150]
                result += f"  Evidence: {evidence_str}...\n"
            result += f"  Created: {created}\n\n"

        return result

    except Exception as e:
        return f"Error querying staging history: {str(e)}"


@tool
def query_validation_decisions(
    decision_type: str = None,
    reasoning_contains: str = None,
    limit: int = 20
) -> str:
    """
    Query validation_decisions - SEE HOW VALIDATOR REASONED.

    Use this to learn what reasoning led to accepts/rejects/merges.

    Examples:
    - query_validation_decisions(decision_type='reject')
      -> Learn why things were rejected

    - query_validation_decisions(reasoning_contains='duplicate')
      -> See duplicate-related decisions

    Returns: Validation reasoning and decisions
    """
    try:
        conn = get_db_connection()

        query = """
            SELECT decision_id, extraction_id, decision::text, decision_reason,
                   confidence_at_decision, evidence_at_decision, created_at
            FROM validation_decisions
            WHERE 1=1
        """
        params = []

        if decision_type:
            query += " AND decision = %s"
            params.append(decision_type)

        if reasoning_contains:
            query += " AND reasoning ILIKE %s"
            params.append(f'%{reasoning_contains}%')

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        conn.close()

        if not rows:
            return "No validation decisions found matching criteria."

        result = f"Found {len(rows)} validation decisions:\n\n"
        for row in rows:
            dec_id, ext_id, decision, reason, conf, evidence, created = row
            result += f"Decision: {decision}\n"
            result += f"  Extraction ID: {ext_id}\n"
            result += f"  Reasoning: {reason}\n"
            if conf:
                result += f"  Confidence: {conf}\n"
            if evidence:
                import json
                evidence_dict = evidence if isinstance(evidence, dict) else json.loads(evidence)
                if 'suggested_name' in evidence_dict:
                    result += f"  Suggested Name: {evidence_dict['suggested_name']}\n"
            result += f"  Created: {created}\n\n"

        return result

    except Exception as e:
        return f"Error querying validation decisions: {str(e)}"


@tool
def query_raw_snapshots(
    source_url_pattern: str = None,
    source_type: str = None,
    limit: int = 10
) -> str:
    """
    Query raw_snapshots - SEE WHAT SOURCES WERE PROCESSED.

    Use this to avoid re-processing same sources.

    Examples:
    - query_raw_snapshots(source_url_pattern='%proveskit.space%')
      -> See what PROVES Kit pages were fetched

    - query_raw_snapshots(source_type='webpage')
      -> See all webpage snapshots

    Returns: Source URLs and fetch timestamps
    """
    try:
        conn = get_db_connection()

        query = """
            SELECT id, source_url, source_type::text, captured_at,
                   LEFT(payload::text, 200) as content_preview
            FROM raw_snapshots
            WHERE 1=1
        """
        params = []

        if source_url_pattern:
            query += " AND source_url ILIKE %s"
            params.append(source_url_pattern)

        if source_type:
            query += " AND source_type = %s"
            params.append(source_type)

        query += " ORDER BY captured_at DESC LIMIT %s"
        params.append(limit)

        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        conn.close()

        if not rows:
            return "No raw snapshots found matching criteria."

        result = f"Found {len(rows)} raw snapshots:\n\n"
        for row in rows:
            snap_id, url, stype, timestamp, preview = row
            result += f"Snapshot ID: {snap_id}\n"
            result += f"  URL: {url}\n"
            result += f"  Type: {stype}\n"
            result += f"  Fetched: {timestamp}\n"
            if preview:
                result += f"  Preview: {preview[:100]}...\n"
            result += "\n"

        return result

    except Exception as e:
        return f"Error querying raw snapshots: {str(e)}"


@traceable(name="validator_subagent")
def create_validator_agent():
    """
    Create the validator sub-agent

    This agent specializes in:
    - get_pending_extractions() -> review staging_extractions
    - record_validation_decision() -> approve/reject with audit trail
    - check_for_duplicates() -> detect entities already in core

    Legacy tools (for backward compatibility):
    - check_if_dependency_exists() -> kg_nodes lookup
    - verify_schema_compliance() -> ERV schema validation
    - search_similar_dependencies() -> kg_nodes search

    Uses Claude Haiku 3.5 for cost optimization (validation is pattern matching)
    """
    model = ChatAnthropic(
        model="claude-3-5-haiku-20241022",
        temperature=0.1,
    )

    tools = [
        # NEW domain table workflow
        get_pending_extractions,
        record_validation_decision,
        check_for_duplicates,
        # Database query tools for confidence calibration
        query_verified_entities,
        query_staging_history,
        query_validation_decisions,
        query_raw_snapshots,
        # Legacy kg_nodes tools
        check_if_dependency_exists,
        verify_schema_compliance,
        search_similar_dependencies,
    ]

    agent = create_react_agent(model, tools)
    return agent
