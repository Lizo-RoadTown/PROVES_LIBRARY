"""
Curator Orchestration (v3) - Testing Refactors

This is version 3 of the curator agent that uses refactored agent files:
- validator_v3.py (lineage verification + epistemic validation)
- storage_v3.py (receives verification results + epistemic defaults/overrides)
- subagent_specs_v3.py

This module orchestrates the extraction pipeline using explicit control flow:
1. Extractor: Fetch page, extract architecture
2. Validator: Verify lineage + epistemic structure, check duplicates
3. Storage: Save to staging_extractions with verification results

No curator agent - just Python orchestration of subagents.
"""
import os
import re
from pathlib import Path
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

# Setup paths
# Now in production/Version 3/, so go up 2 levels to reach project root
version3_folder = Path(__file__).parent
project_root = version3_folder.parent.parent
production_root = project_root / 'production'

# Add paths
import sys
sys.path.insert(0, str(production_root))
sys.path.insert(0, str(version3_folder))

# Load environment
load_dotenv(project_root / '.env')

# Import from v3 subagent specs
from subagent_specs_v3 import (
    get_extractor_spec,
    get_validator_spec,
    get_storage_spec,
)

# Import storage tools for direct orchestrator use
from storage_v3 import store_extraction

# Import validator tools for direct orchestrator use (duplicate checking)
from validator_v3 import check_for_duplicates


def create_curator():
    """
    Create the extraction orchestration system using BACKUP specs.

    Returns:
        dict with three subagent runnables and checkpointer
    """

    # Initialize PostgreSQL checkpointer with SEPARATE small pool
    # Checkpointer needs its own pool because it holds connections during agent execution
    # Using the shared pool causes SSL errors when connections timeout
    # NOTE: Use DIRECT_URL (port 5432) instead of DATABASE_URL (port 6543 with pgbouncer)
    # because psycopg doesn't understand the ?pgbouncer=true query parameter
    db_url = os.getenv('DIRECT_URL') or os.getenv('PROVES_DATABASE_URL') or os.getenv('DATABASE_URL')
    checkpointer_pool = ConnectionPool(
        conninfo=db_url,
        min_size=1,
        max_size=3,  # Small pool just for checkpointing
        timeout=60,
        kwargs={
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        }
    )
    checkpointer = PostgresSaver(checkpointer_pool)
    checkpointer.setup()

    # Get subagent specifications (from BACKUP files)
    extractor_spec = get_extractor_spec()
    validator_spec = get_validator_spec()
    storage_spec = get_storage_spec()

    # Create subagents as standalone runnables
    extractor = create_agent(
        model=ChatAnthropic(model=extractor_spec["model"], temperature=0.1),
        system_prompt=extractor_spec["system_prompt"],
        tools=extractor_spec["tools"],
        checkpointer=checkpointer,
    )

    validator = create_agent(
        model=ChatAnthropic(model=validator_spec["model"], temperature=0.1),
        system_prompt=validator_spec["system_prompt"],
        tools=validator_spec["tools"],
        checkpointer=checkpointer,
    )

    storage = create_agent(
        model=ChatAnthropic(model=storage_spec["model"], temperature=0.1),
        system_prompt=storage_spec["system_prompt"],
        tools=storage_spec["tools"],
        checkpointer=None,  # No checkpointing needed - storage agent just makes sequential tool calls
    )

    return {
        "extractor": extractor,
        "validator": validator,
        "storage": storage,
        "checkpointer": checkpointer,
    }


def orchestrate_extraction(url: str, agents: dict, config: dict) -> dict:
    """
    Orchestrate the extraction pipeline with explicit control flow.

    Args:
        url: URL to extract from
        agents: Dict with extractor, validator, storage runnables
        config: LangGraph config with thread_id and recursion_limit

    Returns:
        dict with status, results, and any errors
    """

    # STEP 1: EXTRACT (with lineage verification)
    print(f"\n[TEST STEP 1/3] Extracting from: {url}")
    extractor_task = f"""Extract architecture from this URL: {url}

Your task:
1. Fetch the page
2. Extract couplings using FRAMES methodology
3. Verify lineage (checksums, byte offsets)
4. Return results with snapshot_id and verified lineage data

Return format:
- snapshot_id: <uuid>
- source_url: {url}
- extractions: [list of extracted couplings with evidence]
- lineage_verified: true/false
- lineage_confidence: 0.0-1.0
"""

    extractor_result = agents["extractor"].invoke(
        {"messages": [{"role": "user", "content": extractor_task}]},
        config
    )

    # Extract the final message
    final_message = extractor_result["messages"][-1].content

    # Check if extraction succeeded
    if "snapshot_id" not in final_message.lower() or "no couplings" in final_message.lower():
        return {
            "status": "failed",
            "stage": "extraction",
            "error": "Extractor did not return valid data",
            "extractor_output": final_message
        }

    print(f"[OK] Extraction completed")
    print(f"\n   DEBUG - Extractor output preview (first 2000 chars):\n{'='*60}")
    print(final_message[:2000] if len(final_message) > 2000 else final_message)
    print(f"{'='*60}\n")

    # STEP 1.5: DUPLICATE CHECK - Orchestrator calls check_for_duplicates for EACH entity
    # This is done in Python loop to ensure ALL entities are checked (not limited by tool calls)
    print(f"\n[TEST STEP 1.5/3] Checking for duplicates (orchestrator loop)...")

    # Parse candidate_key values from extractor output
    # The extractor uses markdown format like: **candidate_key:** RadioModule_to_FlightControllerBoard
    import re

    # Pattern: match "candidate_key" preceded by any chars (including **), then : and the value
    # Value can contain letters, numbers, underscores, colons, hyphens, dots
    key_pattern = r'candidate_key[*]*:\s*`?([A-Za-z0-9_:\-\.]+)`?'
    candidate_keys = re.findall(key_pattern, final_message, re.IGNORECASE)

    # Pattern for candidate_type
    type_pattern = r'candidate_type[*]*:\s*`?([a-z_]+)`?'
    candidate_types = re.findall(type_pattern, final_message, re.IGNORECASE)

    # Debug: print what we found
    print(f"   DEBUG: Found keys: {candidate_keys[:5]}..." if len(candidate_keys) > 5 else f"   DEBUG: Found keys: {candidate_keys}")
    print(f"   DEBUG: Found types: {candidate_types[:5]}..." if len(candidate_types) > 5 else f"   DEBUG: Found types: {candidate_types}")

    if candidate_keys:
        print(f"   Found {len(candidate_keys)} candidate(s) to check for duplicates")
        duplicates_found = []

        for i, key in enumerate(candidate_keys):
            # Get corresponding type if available, default to 'dependency'
            entity_type = candidate_types[i] if i < len(candidate_types) else 'dependency'

            # Call check_for_duplicates directly (not via LLM)
            dup_result = check_for_duplicates.invoke({"entity_name": key, "entity_type": entity_type})

            # Check if exact match found (in core_entities OR staging_extractions)
            if "[WARNING] EXACT MATCHES" in dup_result:
                duplicates_found.append(f"{key} ({entity_type})")
                if "staging_extractions" in dup_result:
                    print(f"   [DUPLICATE] {key} already pending in staging!")
                else:
                    print(f"   [DUPLICATE] {key} already exists in core_entities!")
            else:
                print(f"   [OK] {key} - no duplicates")

        if duplicates_found:
            return {
                "status": "rejected",
                "stage": "duplicate_check",
                "reason": f"Duplicates found: {', '.join(duplicates_found)}. Stopping to prevent re-extraction loop.",
                "extractor_output": final_message
            }

        print(f"   [OK] All {len(candidate_keys)} candidates passed duplicate check")
    else:
        print(f"   [WARN] Could not parse candidate keys from extractor output")

    # STEP 2: VALIDATE (using BACKUP validator with new tools)
    print(f"\n[TEST STEP 2/3] Validating extractions with BACKUP validator...")
    validator_task = f"""Validate the following extraction results:

{final_message}

Your task (USING NEW REFACTOR TOOLS):
1. Use validate_epistemic_structure() to check epistemic defaults + overrides
2. Use verify_evidence_lineage() to check lineage for EACH extraction
   - You MUST call verify_evidence_lineage() once per extraction
   - Pass snapshot_id and the raw_evidence text

NOTE: Duplicate checking is ALREADY DONE by the orchestrator. Do NOT call check_for_duplicates().

Return APPROVED or REJECTED with reasoning.

CRITICAL - TOOLS TO USE:
- validate_epistemic_structure(epistemic_defaults, epistemic_overrides)
- verify_evidence_lineage(snapshot_id, evidence_text) - CALL ONCE PER EXTRACTION

If epistemic structure invalid, REJECT.
If ANY lineage_confidence < 0.5 or lineage_verified=FALSE, REJECT.
Otherwise, APPROVE and include verification results for all extractions.
"""

    validator_result = agents["validator"].invoke(
        {"messages": [{"role": "user", "content": validator_task}]},
        config
    )

    validator_message = validator_result["messages"][-1].content

    # Check if validation rejected
    if "REJECTED" in validator_message.upper():
        return {
            "status": "rejected",
            "stage": "validation",
            "reason": validator_message,
            "extractor_output": final_message
        }

    # If not explicitly rejected, proceed to storage
    print(f"[OK] Validation completed with BACKUP validator")

    # STEP 3: STORE - Orchestrator calls store_extraction directly for each extraction
    print(f"\n[TEST STEP 3/3] Storing validated extractions...")

    # Parse the extractor output to get extraction details
    # The extractor returns structured data that we need to parse
    # For now, use an LLM to parse and call store_extraction for each item
    # This removes the 5 tool call limit

    storage_task = f"""Parse the extraction data and call store_extraction() for EVERY extraction.

EXTRACTION DATA:
{final_message}

VALIDATOR RESULTS:
{validator_message}

CRITICAL: Call store_extraction() once for EACH extracted entity. Do not skip any.
Extract the lineage_verified and lineage_confidence from validator results.
Include all required epistemic metadata from the 7-question checklist.
"""

    storage_result = agents["storage"].invoke(
        {"messages": [{"role": "user", "content": storage_task}]},
        config
    )

    # Handle both message object and dict formats
    last_message = storage_result["messages"][-1]
    storage_message = last_message.content if hasattr(last_message, 'content') else last_message.get('content', str(last_message))

    print(f"[OK] Storage completed")

    return {
        "status": "success",
        "extractor_output": final_message,
        "validator_output": validator_message,
        "storage_output": storage_message
    }


# For backward compatibility with process_extractions.py
# Create a graph-like interface that uses orchestration under the hood
class OrchestrationGraph:
    """Wrapper to make orchestration look like a LangGraph graph (BACKUP VERSION)"""

    def __init__(self):
        self.agents = create_curator()

    def invoke(self, input_dict: dict, config: dict) -> dict:
        """
        Invoke the orchestration pipeline.

        Args:
            input_dict: {"messages": [{"role": "user", "content": "Extract from <URL>"}]}
            config: LangGraph config

        Returns:
            {"messages": [{"role": "assistant", "content": "result summary"}]}
        """
        # Extract URL from user message
        user_message = input_dict["messages"][0]["content"]

        # Parse URL from message (format: "Extract from <URL>")
        url_match = re.search(r'https?://[^\s]+', user_message)
        if not url_match:
            return {
                "messages": [{
                    "role": "assistant",
                    "content": "ERROR: No URL found in task"
                }]
            }

        url = url_match.group(0)

        # Run orchestration
        result = orchestrate_extraction(url, self.agents, config)

        # Format response
        if result["status"] == "success":
            response = f"""[TEST SUCCESS] Extraction pipeline completed with BACKUP refactors

Extractor: {result['extractor_output'][:200]}...

Validator (BACKUP with verify_evidence_lineage): {result['validator_output'][:200]}...

Storage (BACKUP with lineage fields): {result['storage_output']}
"""
        else:
            response = f"""[TEST {result['status'].upper()}] Pipeline stopped at {result['stage']}

{result.get('error', result.get('reason', 'Unknown error'))}
"""

        return {
            "messages": [{
                "role": "assistant",
                "content": response
            }]
        }


# Export the graph for process_extractions_BACKUP.py
graph = OrchestrationGraph()
