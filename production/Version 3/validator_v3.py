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
from pathlib import Path

# Add production/core to path for database utilities
version3_folder = Path(__file__).parent  # production/Version 3/
project_root = version3_folder.parent.parent  # PROVES_LIBRARY/
core_path = project_root / 'production' / 'core'
sys.path.insert(0, str(core_path))

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


@tool
def validate_epistemic_structure(epistemic_defaults: dict, epistemic_overrides: dict = None) -> str:
    """
    Validate that epistemic_defaults and epistemic_overrides follow the correct structure.

    This enforces the epistemic anti-boilerplate pattern:
    - epistemic_defaults must exist (for page-level defaults)
    - epistemic_overrides (if provided) must only contain valid epistemic keys

    Args:
        epistemic_defaults: The defaults object (required)
        epistemic_overrides: The overrides for this specific candidate (optional)

    Returns:
        JSON string with validation result:
        {
            "valid": bool,
            "issues": list of validation errors
        }
    """
    import json

    issues = []

    # Valid epistemic keys
    valid_keys = {
        'observer_id', 'observer_type', 'contact_mode', 'contact_strength',
        'signal_type', 'pattern_storage', 'representation_media',
        'dependencies', 'sequence_role', 'validity_conditions', 'assumptions',
        'scope', 'observed_at', 'valid_from', 'valid_to', 'refresh_trigger',
        'staleness_risk', 'author_id', 'intent', 'uncertainty_notes',
        'reenactment_required', 'practice_interval', 'skill_transferability'
    }

    # Check 1: epistemic_defaults must exist
    if not epistemic_defaults:
        issues.append("epistemic_defaults is missing - REQUIRED for anti-boilerplate pattern")
    else:
        # Check 2: epistemic_defaults must be a dict
        if not isinstance(epistemic_defaults, dict):
            issues.append(f"epistemic_defaults must be a dict, got {type(epistemic_defaults).__name__}")
        else:
            # Check 3: All keys in epistemic_defaults must be valid
            invalid_default_keys = set(epistemic_defaults.keys()) - valid_keys
            if invalid_default_keys:
                issues.append(f"Invalid keys in epistemic_defaults: {sorted(invalid_default_keys)}")

    # Check 4: epistemic_overrides (if provided) must be a dict
    if epistemic_overrides is not None:
        if not isinstance(epistemic_overrides, dict):
            issues.append(f"epistemic_overrides must be a dict, got {type(epistemic_overrides).__name__}")
        else:
            # Check 5: All keys in epistemic_overrides must be valid
            invalid_override_keys = set(epistemic_overrides.keys()) - valid_keys
            if invalid_override_keys:
                issues.append(f"Invalid keys in epistemic_overrides: {sorted(invalid_override_keys)}")

    valid = len(issues) == 0

    return json.dumps({
        "valid": valid,
        "issues": issues
    }, indent=2)


@tool
def verify_evidence_lineage(snapshot_id: str, evidence_text: str) -> str:
    """
    Verify that evidence exists in snapshot and passes quality checks.

    This is VALIDATION - checking if evidence is legitimate before storage.
    Returns verification result with lineage_verified and lineage_confidence.

    The storage agent will use these results and compute deterministic metadata
    (checksums, byte offsets) separately.

    Args:
        snapshot_id: UUID of raw_snapshot to verify against
        evidence_text: The evidence quote to verify

    Returns:
        JSON string with verification results:
        {
            "lineage_verified": bool,
            "lineage_confidence": float (0.0-1.0),
            "checks_passed": list of check names,
            "checks_failed": list of check names,
            "snapshot_id": str,
            "issues": list of error messages (if any)
        }
    """
    import json
    import re

    try:
        conn = get_db_connection()

        # Query snapshot
        with conn.cursor() as cur:
            cur.execute("""
                SELECT payload, content_hash
                FROM raw_snapshots
                WHERE id = %s::uuid
            """, (snapshot_id,))
            row = cur.fetchone()

            if not row:
                conn.close()
                return json.dumps({
                    "lineage_verified": False,
                    "lineage_confidence": 0.0,
                    "checks_passed": [],
                    "checks_failed": ["snapshot_not_found"],
                    "snapshot_id": snapshot_id,
                    "issues": [f"Snapshot {snapshot_id} not found in database"]
                }, indent=2)

            payload_jsonb, snapshot_checksum = row

        conn.close()

        # Extract content from JSONB payload
        if isinstance(payload_jsonb, dict):
            payload_content = payload_jsonb.get('content', '')
        else:
            payload_content = str(payload_jsonb)

        # Strip HTML tags (same as extractor does) for fair comparison
        # Evidence quotes are from stripped text, so snapshot must be stripped too
        payload_stripped = re.sub(r'<script[^>]*>.*?</script>', '', payload_content, flags=re.DOTALL)
        payload_stripped = re.sub(r'<style[^>]*>.*?</style>', '', payload_stripped, flags=re.DOTALL)
        payload_stripped = re.sub(r'<[^>]+>', ' ', payload_stripped)
        payload_stripped = re.sub(r'\s+', ' ', payload_stripped).strip()

        # UTF-8 encoding for verification (use stripped content)
        payload_bytes = payload_stripped.encode('utf-8')
        evidence_bytes = evidence_text.encode('utf-8')

        # Verification checks
        checks_passed = []
        checks_failed = []

        # Check 1: Evidence not empty
        if evidence_text.strip():
            checks_passed.append("evidence_not_empty")
        else:
            checks_failed.append("evidence_empty")

        # Check 2: Evidence found in snapshot (exact match)
        exact_match_offset = payload_bytes.find(evidence_bytes)
        if exact_match_offset != -1:
            checks_passed.append("evidence_found_exact")
        else:
            # Try normalized match (formatting-only normalization)
            def normalize_text(text: str) -> str:
                """STRICT formatting-only normalization."""
                text = text.replace('\r\n', '\n').replace('\r', '\n')
                text = re.sub(r'\s+', ' ', text)
                text = text.strip()
                return text

            payload_normalized = normalize_text(payload_stripped)  # Use stripped content
            evidence_normalized = normalize_text(evidence_text)

            if evidence_normalized in payload_normalized:
                checks_passed.append("evidence_found_normalized")
            else:
                checks_failed.append("evidence_not_found_in_snapshot")

        # Check 3: Evidence length reasonable
        evidence_length = len(evidence_bytes)
        if 10 <= evidence_length <= 10000:
            checks_passed.append("evidence_length_reasonable")
        else:
            checks_failed.append("evidence_length_unreasonable")

        # Check 4: Evidence not suspiciously repetitive
        if len(set(evidence_text.split())) / max(len(evidence_text.split()), 1) > 0.3:
            checks_passed.append("evidence_not_repetitive")
        else:
            checks_failed.append("evidence_too_repetitive")

        # Calculate confidence
        total_checks = len(checks_passed) + len(checks_failed)
        lineage_confidence = len(checks_passed) / total_checks if total_checks > 0 else 0.0

        # Verified if evidence found (exact or normalized) and confidence >= 0.5
        evidence_found = "evidence_found_exact" in checks_passed or "evidence_found_normalized" in checks_passed
        lineage_verified = evidence_found and (lineage_confidence >= 0.5)

        return json.dumps({
            "lineage_verified": lineage_verified,
            "lineage_confidence": round(lineage_confidence, 2),
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "snapshot_id": snapshot_id
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "lineage_verified": False,
            "lineage_confidence": 0.0,
            "checks_passed": [],
            "checks_failed": ["verification_error"],
            "snapshot_id": snapshot_id,
            "issues": [str(e)]
        }, indent=2)


@traceable(name="validator_subagent")
def create_validator_agent(checkpointer=None):
    """
    Create the validator sub-agent with validation training.

    Args:
        checkpointer: Optional LangGraph checkpointer (e.g., PostgresSaver) for state persistence
    """
    from langchain.agents import create_agent
    from ..subagent_specs import get_validator_spec

    spec = get_validator_spec()

    # Create agent with system prompt and optional checkpointer
    agent = create_agent(
        model=ChatAnthropic(model=spec["model"], temperature=0.1),
        system_prompt=spec["system_prompt"],
        tools=spec["tools"],
        checkpointer=checkpointer,
    )

    return agent
