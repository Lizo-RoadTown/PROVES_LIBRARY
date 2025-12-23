"""
Validator Sub-Agent
Specialized agent for validating extractions and recording decisions

DOMAIN TABLE WORKFLOW (2024-12-22):
1. Review staging_extractions awaiting validation
2. Record decisions in validation_decisions table
3. Approved extractions → promoted to core_entities by storage agent
"""
import sys
import os
import uuid
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
            result += "⚠️ EXACT MATCHES:\n"
            for eid, key, name, etype, eco in exact:
                result += f"  - {name} (key: {key}, {etype}, {eco}) ID: {eid}\n"
        else:
            result += "✓ No exact matches\n"
        
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
def verify_schema_compliance(component: str, depends_on: str, relationship_type: str, criticality: str) -> str:
    """Verify that a dependency follows ERV schema and naming conventions."""
    # Valid ERV types
    valid_types = ['depends_on', 'requires', 'enables', 'conflicts_with', 'mitigates', 'causes']
    valid_criticalities = ['HIGH', 'MEDIUM', 'LOW']

    issues = []

    if relationship_type not in valid_types:
        issues.append(f"Invalid relationship type '{relationship_type}'. Must be one of: {', '.join(valid_types)}")

    if criticality not in valid_criticalities:
        issues.append(f"Invalid criticality '{criticality}'. Must be one of: {', '.join(valid_criticalities)}")

    if not component or not depends_on:
        issues.append("Component and depends_on cannot be empty")

    if component == depends_on:
        issues.append("Component cannot depend on itself")

    if issues:
        return f"[INVALID] Schema issues:\n" + "\n".join(f"  - {issue}" for issue in issues)

    return f"[VALID] Schema compliant: {component} --[{relationship_type}]--> {depends_on} ({criticality})"


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


@traceable(name="validator_subagent")
def create_validator_agent():
    """
    Create the validator sub-agent

    This agent specializes in:
    - get_pending_extractions() → review staging_extractions
    - record_validation_decision() → approve/reject with audit trail
    - check_for_duplicates() → detect entities already in core

    Legacy tools (for backward compatibility):
    - check_if_dependency_exists() → kg_nodes lookup
    - verify_schema_compliance() → ERV schema validation
    - search_similar_dependencies() → kg_nodes search

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
        # Legacy kg_nodes tools
        check_if_dependency_exists,
        verify_schema_compliance,
        search_similar_dependencies,
    ]

    agent = create_react_agent(model, tools)
    return agent
