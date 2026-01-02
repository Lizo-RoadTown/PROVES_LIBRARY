"""
Curator Orchestration (v2) - Using Deep Agents SubAgentMiddleware

This module orchestrates the extraction pipeline using explicit control flow:
1. Extractor: Fetch page, extract architecture, verify lineage
2. Validator: Check duplicates, verify quality
3. Storage: Save to staging_extractions

No curator agent - just Python orchestration of subagents.
"""
import os
import re
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '../../..', '.env'))

from .subagent_specs import (
    get_extractor_spec,
    get_validator_spec,
    get_storage_spec,
)


def create_curator():
    """
    Create the extraction orchestration system.

    Returns:
        dict with three subagent runnables and checkpointer
    """

    # Initialize PostgreSQL checkpointer (Neon) with SSL config
    db_url = os.getenv('NEON_DATABASE_URL')
    pool = ConnectionPool(
        conninfo=db_url,
        min_size=1,
        max_size=5,
        timeout=30,  # Connection timeout in seconds
        kwargs={
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        }
    )
    checkpointer = PostgresSaver(pool)
    checkpointer.setup()

    # Get subagent specifications
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
        checkpointer=checkpointer,
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
    print(f"\n[STEP 1/3] Extracting from: {url}")
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

    # STEP 2: VALIDATE
    print(f"\n[STEP 2/3] Validating extractions...")
    validator_task = f"""Validate the following extraction results:

{final_message}

Your task:
1. Check for duplicates in core_entities and staging_extractions
2. Verify lineage integrity (checksums, byte offsets)
3. Check quality and completeness
4. Return APPROVED or REJECTED with reasoning

If ANY duplicates found, REJECT immediately.
If lineage_confidence < 0.5, REJECT.
Otherwise, APPROVE.
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
    print(f"[OK] Validation completed")

    # STEP 3: STORE
    print(f"\n[STEP 3/3] Storing validated extractions...")
    storage_task = f"""Store the following VALIDATED extraction results:

{final_message}

Your task:
1. Parse the extraction data
2. Store each coupling in staging_extractions
3. Include snapshot_id, lineage data, and all evidence
4. Return confirmation with extraction_ids

Use the store_extraction() tool for each coupling.
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
    """Wrapper to make orchestration look like a LangGraph graph"""

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
            response = f"""[SUCCESS] Extraction pipeline completed

Extractor: {result['extractor_output'][:200]}...

Validator: {result['validator_output'][:200]}...

Storage: {result['storage_output']}
"""
        else:
            response = f"""[{result['status'].upper()}] Pipeline stopped at {result['stage']}

{result.get('error', result.get('reason', 'Unknown error'))}
"""

        return {
            "messages": [{
                "role": "assistant",
                "content": response
            }]
        }


# Export the graph for process_extractions.py
graph = OrchestrationGraph()
