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
from typing import Literal

# Add neon-database to path for database utilities
neon_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../neon-database/scripts'))
sys.path.insert(0, neon_db_path)

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
    source_snapshot_id: str = None,
    ecosystem: str = "external",
    properties: dict = None,
    confidence_score: float = 0.8,
    confidence_reason: str = "LLM extraction",
    evidence_type: Literal[
        'explicit_requirement',
        'safety_constraint',
        'performance_constraint',
        'feature_description',
        'interface_specification',
        'behavioral_contract',
        'example_usage',
        'design_rationale',
        'dependency_declaration',
        'configuration_parameter',
        'inferred'
    ] = "explicit_requirement",
    reasoning_trail: dict = None,
    duplicate_check: dict = None,
    source_metadata: dict = None,
    # Knowledge Capture Checklist (7 questions) - stored in knowledge_epistemics sidecar
    domain: str = "external",  # 'fprime', 'proveskit', 'external', etc.
    # EPISTEMIC ATTRIBUTION: You are the RECORDER, not the OBSERVER
    # observer_id = WHO claimed to know this (designers, authors, system, unknown)
    # observer_type = THEIR role (human, system, instrument, unknown) - NEVER 'ai'
    # The AI (you) is the artifact_recorder, not the attributed_observer
    observer_id: str = "unknown",  # Default: attributed observer unknown
    observer_type: str = "unknown",  # human | system | instrument | unknown (NOT ai)
    contact_mode: str = "derived",  # How the ATTRIBUTED observer knew this
    contact_strength: float = 0.20,  # How close the ATTRIBUTED observer was (default low for derived)
    signal_type: str = "text",
    pattern_storage: str = "externalized",
    representation_media: list = None,  # Will default to [signal_type] if None
    dependencies: list = None,  # List of entity keys or extraction_ids (JSONB array)
    sequence_role: str = "none",
    validity_conditions: dict = None,
    assumptions: list = None,
    scope: str = None,
    observed_at: str = None,
    valid_from: str = None,
    valid_to: str = None,
    refresh_trigger: str = None,
    staleness_risk: float = 0.20,
    author_id: str = None,
    intent: str = "unknown",
    uncertainty_notes: str = None,
    reenactment_required: bool = False,
    practice_interval: str = None,
    skill_transferability: str = "portable"
) -> str:
    """
    Deliver an extracted entity to the human review inbox (staging_extractions table).

    Your job: Deliver clear, unambiguous information to humans.
    Include relationships that help identify what this entity is.
    Humans will review and decide - you just deliver the information.

    CRITICAL: You MUST provide source_metadata with 'source_url' key.
    The system will auto-find the snapshot from the URL.

    Example: source_metadata={'source_url': 'https://docs.proveskit.space/...'}

    Args:
        candidate_type: 'component', 'port', 'command', 'telemetry', 'event', 'parameter',
                        'data_type', 'dependency', 'connection', 'inheritance'
        candidate_key: Entity name/key (e.g., "I2CDriver", "PowerManager")
        raw_evidence: Exact quote from source (REQUIRED - this is the evidence)
        source_snapshot_id: ID from raw_snapshots (auto-found from source_url if not provided)
        ecosystem: 'fprime', 'proveskit', 'pysquared', 'cubesat_general', 'external'
        properties: JSON dict of entity-specific properties

                   For dependencies/relationships, properties MUST include:
                   {
                       "source": "ComponentA",
                       "target": "ComponentB",
                       "relationship_type": "depends_on|requires|enables|conflicts_with|mitigates|causes"
                   }

                   DO NOT include "criticality" field - humans assign that post-verification.
                   DO NOT use "dependency" as relationship_type - use one of the enum values above.

        confidence_score: How confident the extractor is (0.0 to 1.0)
        confidence_reason: Why this confidence level
        evidence_type: 'explicit_requirement', 'safety_constraint', 'performance_constraint',
                       'feature_description', 'interface_specification', 'behavioral_contract',
                       'example_usage', 'design_rationale', 'dependency_declaration',
                       'configuration_parameter', 'inferred'
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
        source_metadata: Source document metadata (REQUIRED - helps human verify):
            {
                "source_url": "https://..." (REQUIRED - used to find snapshot),
                "source_type": "webpage",
                "fetch_timestamp": "2025-12-23T10:45:32Z"
            }
        observer_id: WHO claimed to know this (NOT you the AI!)
            - "designers" | "authors" | "maintainers" | "system" | "unknown"
            - You are the RECORDER (artifact_recorder_id = ai:extractor_v3)
            - observer_id is the ATTRIBUTED observer (who actually documented/observed this)
        observer_type: 'human' | 'system' | 'instrument' | 'unknown' (NEVER 'ai')
            - Question 1: Who knew this, and how close were they?
            - If you can't tell who documented it, use 'unknown'
        contact_mode: How the ATTRIBUTED observer knew this
            - 'direct' | 'mediated' | 'effect_only' | 'derived'
        contact_strength: How close the ATTRIBUTED observer was (0.00-1.00)
            - 1.0 = direct physical contact, 0.2 = derived from docs (default)
        signal_type: 'text' | 'code' | 'spec' | 'comment' | 'log' | 'telemetry' | etc.
        pattern_storage: 'internalized' | 'externalized' | 'mixed' | 'unknown'
            Question 2: Where does the experience live? (embodied in body vs in docs)
        representation_media: List of media types (e.g., ["text"], ["code", "diagram"])
        dependencies: List of entity keys or extraction_ids (Question 3: What must stay connected?)
        sequence_role: 'precondition' | 'step' | 'outcome' | 'postcondition' | 'none'
        validity_conditions: JSON dict (Question 4: Under what conditions was this true?)
        assumptions: List of assumptions this knowledge depends on
        scope: 'local' | 'subsystem' | 'system' | 'general'
        observed_at: When this was observed (ISO timestamp)
        valid_from: When this becomes valid
        valid_to: When this stops being valid (Question 5: When does this expire?)
        refresh_trigger: What triggers need to refresh ("new_rev", "recalibration", etc.)
        staleness_risk: 0.00-1.00 risk of knowledge becoming stale
        author_id: Who wrote/taught this (Question 6: Who wrote this, and why?)
        intent: 'explain' | 'instruct' | 'justify' | 'explore' | 'comply' | 'persuade' | etc.
        uncertainty_notes: Explicit uncertainties or provisional nature
        reenactment_required: Question 7: Does this only work if someone keeps doing it?
        practice_interval: How often practice is needed ("per-run", "weekly", etc.)
        skill_transferability: 'portable' | 'conditional' | 'local' | 'tacit_like'

    Lineage Computation (AUTOMATIC):
        This function automatically computes lineage verification data:
        - evidence_checksum: SHA256 hash with explicit UTF-8 encoding
        - evidence_byte_offset: Byte position in snapshot (exact or normalized match)
        - evidence_byte_length: Length in bytes
        - lineage_verified: TRUE if exact/normalized match found
        - lineage_confidence: 1.0 (exact), 0.85 (normalized), 0.7 (ambiguous), 0.0 (not found)
        - lineage_verification_details: JSONB with method, hashes, match locations

    Returns:
        Confirmation with extraction ID, or error message
    """
    try:
        import json
        conn = get_db_connection()

        # If snapshot_id not provided, try to find it from source_url
        if not source_snapshot_id and source_metadata and 'source_url' in source_metadata:
            source_url = source_metadata['source_url']
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id FROM raw_snapshots
                    WHERE source_url = %s
                    ORDER BY captured_at DESC
                    LIMIT 1
                """, (source_url,))
                row = cur.fetchone()
                if row:
                    source_snapshot_id = str(row[0])
                else:
                    return f"Error: No snapshot found for URL {source_url}. Cannot store extraction without source snapshot."

        if not source_snapshot_id:
            return "Error: source_snapshot_id required (or provide source_url in source_metadata)"

        # ========================================================================
        # DETERMINISTIC LINEAGE COMPUTATION (pure code, not agent behavior)
        # ========================================================================
        import re
        lineage_verification_details = {}

        if not raw_evidence or not raw_evidence.strip():
            # No evidence provided - cannot compute lineage
            evidence_checksum = None
            evidence_byte_offset = None
            evidence_byte_length = 0
            lineage_verified = False
            lineage_confidence = 0.0
            lineage_verification_details = {
                "method": "not_found",
                "notes": "No evidence text provided"
            }
        else:
            # Fetch snapshot content for lineage computation
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT payload, content_hash
                    FROM raw_snapshots
                    WHERE id = %s::uuid
                """, (source_snapshot_id,))
                snapshot_row = cur.fetchone()

                if not snapshot_row:
                    # Snapshot not found - cannot verify lineage
                    evidence_checksum = None
                    evidence_byte_offset = None
                    evidence_byte_length = len(raw_evidence.encode('utf-8'))
                    lineage_verified = False
                    lineage_confidence = 0.0
                    lineage_verification_details = {
                        "method": "not_found",
                        "notes": f"Snapshot {source_snapshot_id} not found in database"
                    }
                else:
                    payload_jsonb, snapshot_content_hash = snapshot_row

                    # Extract content from JSONB payload
                    if isinstance(payload_jsonb, dict):
                        snapshot_text = payload_jsonb.get('content', '')
                    else:
                        snapshot_text = str(payload_jsonb)

                    # CRITICAL: Always use explicit UTF-8 encoding
                    snapshot_bytes = snapshot_text.encode('utf-8')
                    evidence_bytes = raw_evidence.encode('utf-8')

                    # Calculate evidence checksum and length
                    evidence_checksum = f"sha256:{hashlib.sha256(evidence_bytes).hexdigest()}"
                    evidence_byte_length = len(evidence_bytes)

                    # STEP 1: Exact match (byte-for-byte)
                    exact_matches = []
                    search_start = 0
                    while True:
                        found_offset = snapshot_bytes.find(evidence_bytes, search_start)
                        if found_offset == -1:
                            break
                        exact_matches.append(found_offset)
                        search_start = found_offset + 1

                    if len(exact_matches) == 1:
                        # Found exactly once - perfect lineage
                        evidence_byte_offset = exact_matches[0]
                        lineage_verified = True
                        lineage_confidence = 1.0
                        lineage_verification_details = {
                            "method": "exact",
                            "snapshot_content_hash": f"sha256:{snapshot_content_hash}" if snapshot_content_hash else None,
                            "evidence_checksum": evidence_checksum,
                            "matches_found": 1,
                            "match_locations": exact_matches,
                            "normalizations_applied": [],
                            "fuzzy_score": None,
                            "notes": "Exact byte-for-byte match found once."
                        }
                    elif len(exact_matches) > 1:
                        # Found multiple times - ambiguous but verified
                        evidence_byte_offset = exact_matches[0]  # Use first match
                        lineage_verified = True
                        lineage_confidence = 0.7
                        lineage_verification_details = {
                            "method": "exact",
                            "snapshot_content_hash": f"sha256:{snapshot_content_hash}" if snapshot_content_hash else None,
                            "evidence_checksum": evidence_checksum,
                            "matches_found": len(exact_matches),
                            "match_locations": exact_matches,
                            "normalizations_applied": [],
                            "fuzzy_score": None,
                            "notes": f"Evidence found {len(exact_matches)} times in snapshot (ambiguous). Using first occurrence."
                        }
                    else:
                        # STEP 2: Normalized match (formatting-only normalization)
                        def normalize_text(text: str) -> str:
                            """STRICT formatting-only normalization."""
                            # Normalize line endings
                            text = text.replace('\r\n', '\n').replace('\r', '\n')
                            # Collapse repeated whitespace to single spaces
                            text = re.sub(r'\s+', ' ', text)
                            # Strip leading/trailing whitespace
                            text = text.strip()
                            return text

                        snapshot_normalized = normalize_text(snapshot_text)
                        evidence_normalized = normalize_text(raw_evidence)

                        normalized_offset = snapshot_normalized.find(evidence_normalized)
                        if normalized_offset != -1:
                            # Found after normalization
                            evidence_byte_offset = None  # Cannot reliably map to raw bytes
                            lineage_verified = True
                            lineage_confidence = 0.85
                            lineage_verification_details = {
                                "method": "normalized",
                                "snapshot_content_hash": f"sha256:{snapshot_content_hash}" if snapshot_content_hash else None,
                                "evidence_checksum": evidence_checksum,
                                "matches_found": 1,
                                "match_locations": [],  # Not available for normalized
                                "normalizations_applied": ["newline", "whitespace_collapse", "strip"],
                                "fuzzy_score": None,
                                "notes": "Match found after strict formatting normalization. Byte offset not available."
                            }
                        else:
                            # STEP 3: Not found
                            evidence_byte_offset = None
                            lineage_verified = False
                            lineage_confidence = 0.0
                            lineage_verification_details = {
                                "method": "not_found",
                                "snapshot_content_hash": f"sha256:{snapshot_content_hash}" if snapshot_content_hash else None,
                                "evidence_checksum": evidence_checksum,
                                "matches_found": 0,
                                "match_locations": [],
                                "normalizations_applied": [],
                                "fuzzy_score": None,
                                "notes": "Evidence quote not found in snapshot. Possible issues: wrong snapshot, quote modified, encoding mismatch."
                            }

        # Set lineage_verified_at if verified
        lineage_verified_at = datetime.now() if lineage_verified else None

        # Get or create pipeline run
        run_id = get_or_create_pipeline_run(conn)

        with conn.cursor() as cur:
            payload_dict = properties if properties else {}
            if isinstance(payload_dict, dict):
                payload_dict = dict(payload_dict)
                payload_dict.pop("criticality", None)
            payload = json.dumps(payload_dict)

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

            # Insert into staging_extractions (core extraction data)
            cur.execute("""
                INSERT INTO staging_extractions (
                    pipeline_run_id, snapshot_id, agent_id, agent_version,
                    candidate_type, candidate_key, candidate_payload,
                    ecosystem, confidence_score, confidence_reason,
                    evidence, evidence_type, status,
                    evidence_checksum, evidence_byte_offset, evidence_byte_length,
                    lineage_verified, lineage_confidence, lineage_verified_at,
                    lineage_verification_details
                ) VALUES (
                    %s::uuid, %s::uuid, %s, %s,
                    %s::candidate_type, %s, %s::jsonb,
                    %s::ecosystem_type, %s, %s,
                    %s::jsonb, %s::evidence_type, 'pending'::candidate_status,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s::jsonb
                ) RETURNING extraction_id
            """, (
                run_id, source_snapshot_id, 'storage_agent', '1.0',
                candidate_type, candidate_key, payload,
                ecosystem, confidence_score, confidence_reason,
                evidence, evidence_type,
                evidence_checksum, evidence_byte_offset, evidence_byte_length,
                lineage_verified, lineage_confidence, lineage_verified_at,
                json.dumps(lineage_verification_details)
            ))
            extraction_id = cur.fetchone()[0]

            # Insert into knowledge_epistemics sidecar (epistemic metadata)
            # Prepare representation_media as array
            if representation_media is None:
                representation_media = ['text']

            # Convert timestamps to proper format if provided as strings
            observed_at_ts = observed_at if observed_at else None
            valid_from_ts = valid_from if valid_from else None
            valid_to_ts = valid_to if valid_to else None

            cur.execute("""
                INSERT INTO knowledge_epistemics (
                    extraction_id,
                    domain,
                    observer_id, observer_type, contact_mode, contact_strength, signal_type,
                    pattern_storage, representation_media,
                    dependencies, sequence_role,
                    validity_conditions, assumptions, scope,
                    observed_at, valid_from, valid_to, refresh_trigger, staleness_risk,
                    author_id, intent, uncertainty_notes,
                    reenactment_required, practice_interval, skill_transferability
                ) VALUES (
                    %s::uuid,
                    %s,
                    %s, %s, %s::contact_mode, %s, %s::signal_type,
                    %s::pattern_storage, %s,
                    %s::jsonb, %s::sequence_role,
                    %s::jsonb, %s, %s,
                    %s::timestamptz, %s::timestamptz, %s::timestamptz, %s, %s,
                    %s, %s::author_intent, %s,
                    %s, %s, %s::transferability
                )
            """, (
                extraction_id,
                domain,
                observer_id, observer_type, contact_mode, contact_strength, signal_type,
                pattern_storage, representation_media,
                json.dumps(dependencies) if dependencies else None, sequence_role,
                json.dumps(validity_conditions) if validity_conditions else None, assumptions, scope,
                observed_at_ts, valid_from_ts, valid_to_ts, refresh_trigger, staleness_risk,
                author_id, intent, uncertainty_notes,
                reenactment_required, practice_interval, skill_transferability
            ))
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
        
        return f"[PROMOTED] {final_name} -> core_entities (ID: {entity_id})"
        
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
            
            # Count staging by candidate type
            cur.execute("""
                SELECT candidate_type::text, COUNT(*) FROM staging_extractions GROUP BY candidate_type ORDER BY COUNT(*) DESC
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
def create_storage_agent(checkpointer=None):
    """
    Create the storage sub-agent with epistemic field mapping training.

    Args:
        checkpointer: Optional LangGraph checkpointer (e.g., PostgresSaver) for state persistence
    """
    from langchain.agents import create_agent
    from ..subagent_specs import get_storage_spec

    spec = get_storage_spec()

    # Create agent with system prompt and optional checkpointer
    agent = create_agent(
        model=ChatAnthropic(model=spec["model"], temperature=0.1),
        system_prompt=spec["system_prompt"],
        tools=spec["tools"],
        checkpointer=checkpointer,
    )

    return agent
