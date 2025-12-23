"""
PROVES Library Curator Agent
Main agent that coordinates sub-agents for dependency curation
"""
import os
from typing import Annotated, Any, Literal, NotRequired, TypedDict
import time
from functools import wraps
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.graph import StateGraph, MessagesState
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt
from langgraph.checkpoint.postgres import PostgresSaver
from langsmith import traceable
from dotenv import load_dotenv

# Load environment variables from project root .env
# The .env file is in PROVES_LIBRARY/, this file is in PROVES_LIBRARY/curator-agent/src/curator/
_this_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_this_dir, '..', '..', '..'))
load_dotenv(os.path.join(_project_root, '.env'))

# Verify critical env vars are loaded
if os.getenv('LANGCHAIN_TRACING_V2') == 'true':
    print(f"[LangSmith] Tracing enabled, project: {os.getenv('LANGCHAIN_PROJECT')}")
else:
    print("[LangSmith] Tracing DISABLED - set LANGCHAIN_TRACING_V2=true in .env")

# Training data logger
from .training_logger import get_training_logger

# Timing utilities
_timing_log = []

def log_timing(func):
    """Decorator to track execution time of functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start
            _timing_log.append({
                'function': func.__name__,
                'duration': duration,
                'status': 'success'
            })
            print(f"[TIMING] {func.__name__}: {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start
            _timing_log.append({
                'function': func.__name__,
                'duration': duration,
                'status': 'error'
            })
            print(f"[TIMING] {func.__name__}: {duration:.2f}s (ERROR)")
            raise
    return wrapper

def get_timing_summary():
    """Get a summary of all timing data"""
    if not _timing_log:
        return "No timing data collected"

    summary = "\n=== TIMING SUMMARY ===\n"
    total = 0
    for entry in _timing_log:
        summary += f"{entry['function']}: {entry['duration']:.2f}s ({entry['status']})\n"
        total += entry['duration']
    summary += f"\nTOTAL TIME: {total:.2f}s\n"
    summary += "=" * 50
    return summary

# Import sub-agents
from .subagents import create_extractor_agent, create_validator_agent, create_storage_agent


class CuratorState(TypedDict):
    messages: Annotated[list, add_messages]
    deferred_storage: NotRequired[list[dict[str, Any]]]  # Legacy - kept for backward compatibility
    storage_approval: NotRequired[str | None]
    human_correction: NotRequired[dict[str, Any] | None]  # For corrected extractions
    current_interaction_id: NotRequired[str | None]  # Track for training data
    current_extraction_id: NotRequired[str | None]  # Track current extraction being reviewed
    extractor_failures: NotRequired[int]  # Track consecutive extractor failures
    last_error: NotRequired[str | None]  # Track what error occurred


# ============================================
# WRAP SUB-AGENTS AS TOOLS (DEEP AGENTS PATTERN!)
# ============================================

@tool("extractor_agent")
@traceable(name="call_extractor_subagent")
@log_timing
def call_extractor_agent(task: str) -> str:
    """
    Call the extractor sub-agent to map system architecture using FRAMES methodology.

    FRAMES = Framework for Resilience Assessment in Modular Engineering Systems

    The extractor maps STRUCTURAL ELEMENTS:
    - COMPONENTS: Semi-autonomous units (modules) with boundaries
    - INTERFACES: Where components connect (ports, buses, protocols)
    - FLOWS: What moves through interfaces (data, commands, power, signals)
    - MECHANISMS: What maintains interfaces (documentation, schemas, drivers)

    Available tools:
    - read_document: Read local documentation files
    - fetch_webpage: Fetch web pages from docs sites
    - fetch_github_file: Fetch files directly from GitHub repos
    - list_github_directory: List GitHub directories
    - extract_architecture_using_claude: Map architecture from text (loads ONTOLOGY.md)

    IMPORTANT: For GitHub repos:
    - list_github_directory("nasa", "fprime", "Svc", branch="devel")
    - fetch_github_file("nasa", "fprime", "Svc/TlmChan/TlmChan.fpp", branch="devel")

    All fetched content is stored in raw_snapshots for audit.

    CRITICAL: Agents note CONFIDENCE (documentation clarity).
              Humans assign CRITICALITY (mission impact) after verification.

    Args:
        task: What architecture to map. Be specific about sources:
              "Read C:\\path\\to\\doc.md and extract all components, interfaces, flows"

    Returns:
        Architecture extraction results with components, interfaces, flows, mechanisms
    """
    print(f"[EXTRACTOR TASK] {task}")

    try:
        extractor = create_extractor_agent()
        result = extractor.invoke({"messages": [{"role": "user", "content": task}]})
        content = result['messages'][-1].content

        # Check for error indicators in the response
        error_indicators = [
            "404", "not found", "error fetching", "failed to", "unable to",
            "timeout", "connection error", "does not exist", "cannot access"
        ]

        content_lower = content.lower()
        if any(indicator in content_lower for indicator in error_indicators):
            print(f"[EXTRACTOR] ⚠️ Warning: Possible error detected in response")

        # Debug: show first 500 chars of extractor result
        print(f"[EXTRACTOR RESULT] {content[:500]}..." if len(content) > 500 else f"[EXTRACTOR RESULT] {content}")
        return content

    except Exception as e:
        error_msg = f"EXTRACTOR ERROR: {str(e)}"
        print(f"[EXTRACTOR] ❌ {error_msg}")
        return error_msg


@tool("validator_agent")
@traceable(name="call_validator_subagent")
@log_timing
def call_validator_agent(task: str) -> str:
    """
    Call the validator sub-agent to validate dependencies.

    Use this when you need to:
    - Check if a dependency already exists
    - Verify ERV schema compliance
    - Detect conflicts or duplicates
    - Search for similar dependencies

    Args:
        task: Description of what to validate (e.g., "Check if ImuManager depends_on LinuxI2cDriver already exists")

    Returns:
        Validation results (OK, DUPLICATE, CONFLICT, etc.)
    """
    validator = create_validator_agent()
    result = validator.invoke({"messages": [{"role": "user", "content": task}]})
    return result['messages'][-1].content


@tool("storage_agent")
@traceable(name="call_storage_subagent")
@log_timing
def call_storage_agent(task: str) -> str:
    """
    Call the storage sub-agent to store validated dependencies.

    Use this when you need to:
    - Store extractions in staging_extractions (store_extraction)
    - Promote validated entities to core_entities (promote_to_core)
    - Link cross-ecosystem equivalences (store_equivalence)
    - Get domain table statistics (get_staging_statistics)
    - Legacy: Store findings, manage knowledge graph

    WORKFLOW:
    1. Extractor stores raw content → raw_snapshots (automatic)
    2. Storage stores extractions → staging_extractions (pending status)
    3. Validator reviews → validation_decisions (accept/reject)
    4. Storage promotes accepted → core_entities

    Args:
        task: Description of what to store, e.g.:
              "Store extraction: component 'CmdDispatcher' from snapshot abc123"
              "Promote extraction xyz789 to core entities"

    Returns:
        Storage confirmation with IDs
    """
    storage = create_storage_agent()
    result = storage.invoke({"messages": [{"role": "user", "content": task}]})
    return result['messages'][-1].content


# ============================================
# MAIN CURATOR AGENT
# ============================================

@traceable(name="curator_agent")
def create_curator():
    """
    Create the main curator agent that coordinates sub-agents.

    This is a DEEP AGENT that:
    - Spawns specialized sub-agents (extractor, validator, storage)
    - Coordinates their work through tool calls
    - Maintains conversation state
    - Enables human-in-the-loop via interrupt() and PostgreSQL checkpointer (Neon)
    - Collects training data for local LLM fine-tuning

    Cost Optimization:
    - Main curator: Sonnet 4.5 (complex decisions)
    - Extractor: Sonnet 4.5 (complex dependency analysis)
    - Validator: Haiku 3.5 (simple schema checks - 90% cheaper!)
    - Storage: Haiku 3.5 (simple DB operations - 90% cheaper!)
    """
    print("Initializing Curator Agent...")
    print("  Main Agent: Claude Sonnet 4.5")
    print("  Sub-Agents: Extractor (Sonnet), Validator (Haiku), Storage (Haiku)")
    print()

    # Initialize the model
    model = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=0.1,
    )

    # Bind sub-agent tools to the model
    tools = [
        call_extractor_agent,
        call_validator_agent,
        call_storage_agent,
    ]

    model_with_tools = model.bind_tools(tools)

    # Define the system message
    system_message = """You are the Curator Agent for the PROVES Library knowledge graph.

## YOUR MISSION: Prepare Data for Human Verification

You coordinate agents that extract architecture data, but HUMANS make the final decisions.

**Why This Exists:**
88% of CubeSat missions fail due to hidden dependencies. Students inherit undocumented systems.
Your job: Capture ALL architecture so humans can verify and build institutional memory.

**The Truth Layer Architecture:**
1. Agents extract → Stage with context
2. Humans verify → ONLY verified data becomes "truth"
3. Future students have complete dependency map

**Your Job: REDUCE AMBIGUITY for the Human Verifier**

Humans can't verify ambiguous data. For EVERY extraction, ensure:
✓ Source is cited (exact URL, section, line numbers)
✓ Evidence is quoted (exact text from source)
✓ Reasoning is documented ("I compared to verified entities X, Y, Z...")
✓ Confidence logic is clear ("HIGH because explicit statement + example")
✓ Uncertainties are noted ("Inferred from context, not stated directly")

## Fail-Fast Safeguards

CRITICAL: Track consecutive extractor failures. After 5 failures:
- **STOP IMMEDIATELY** - No more extractor calls
- **REPORT THE PROBLEM** - What's failing and why
- **SUGGEST SOLUTIONS** - Check docs map, switch sources, fix URLs

## Your Sub-Agents (All Prepare Data for Human Review)

1. **Extractor Agent** (`extractor_agent` tool)
   - Fetches documentation, compares to verified examples
   - Documents reasoning: "Compared to entities X, Y, Z with similar structure"
   - Provides evidence quotes for human to verify
   - Has query tools: Can check verified data to calibrate confidence
   - **Purpose:** Give human ALL context to make informed decision

2. **Validator Agent** (`validator_agent` tool)
   - Checks for duplicates, pattern breaks, missing evidence
   - Queries verified data to compare patterns
   - Flags concerns for human: "Similar to entity X but different ecosystem"
   - **Purpose:** Highlight issues human needs to resolve

3. **Storage Agent** (`storage_agent` tool)
   - Stages data with full metadata (source, evidence, reasoning)
   - Clean data → staging, Flagged data → flagged table
   - **Purpose:** Organize data for human review queue

## Workflow: Every Step Reduces Ambiguity

1. **Extract**: "Get documentation + compare to verified examples + document reasoning"
2. **Validate**: "Check duplicates + flag concerns + query past decisions"
3. **Stage**: "Store with full context (source, evidence, confidence logic)"
4. **Report**: "Tell human: What was found, what was compared, what needs review"

## Critical Reminders

**For the Human Verifier:**
- They need to verify your quotes → Cite exact sources
- They need to understand your logic → Document reasoning trail
- They decide mission impact → Don't assign criticality
- They align across sources → Provide comparison context

**Capture EVERYTHING:**
- Don't filter "unimportant" data → Humans decide importance
- Note ALL uncertainties → Helps humans reduce ambiguity
- Document ALL comparisons → Shows your reasoning

**If Stuck:** STOP and ask human instead of looping on failures.

## ERV Relationship Types

- `depends_on`: Runtime dependency (A needs B to function)
- `requires`: Build/config requirement (A needs B to build)
- `enables`: Makes something possible (A enables B)
- `conflicts_with`: Incompatible (A conflicts with B)
- `mitigates`: Reduces risk (A mitigates risk of B)
- `causes`: Leads to effect (A causes B)

## Criticality Levels

- **HIGH**: Mission-critical, failure causes mission loss
- **MEDIUM**: Important, affects functionality
- **LOW**: Nice-to-have, minor impact

Work autonomously but explain your reasoning. When you're done, provide a summary WITHOUT making more tool calls."""

    system_message += """

## Human-in-the-Loop (HITL)

ALL staged data goes to human review. The agents' job is to:
- Capture everything with context
- Flag concerns with reasoning
- Help humans eliminate ambiguity

Humans verify EACH piece and align across sources. Only human-verified data becomes truth in the graph.
"""

    # NOTE ON HITL + TOOL CALLING (IMPORTANT):
    # Anthropic requires that every assistant tool_use is immediately followed by a tool_result message
    # before the next model turn. Therefore, we must NEVER call interrupt() in-between an AIMessage
    # with tool_calls and the corresponding ToolMessage(s). We implement HITL by:
    # 1) Always emitting ToolMessage(s) for *every* tool call (storage HIGH may be deferred)
    # 2) Only calling interrupt() in a later node, after tool results exist in state.

    # Agent logic
    @log_timing
    def call_model(state: CuratorState):
        print("[CURATOR] Thinking...")
        messages = [{"role": "system", "content": system_message}] + state["messages"]
        response = model_with_tools.invoke(messages)

        # Show what tools the curator wants to call
        if hasattr(response, 'tool_calls') and response.tool_calls:
            print(f"[CURATOR] Planning to call {len(response.tool_calls)} sub-agent(s):")
            for tc in response.tool_calls:
                print(f"  -> {tc['name']}")

        return {"messages": [response]}

    tool_map = {t.name: t for t in tools}

    # Tools node: Execute all sub-agent tools without gates.
    # Storage captures ALL raw data. Validation happens AFTER storage.
    def run_tools_with_gate(state: CuratorState):
        last_message = state["messages"][-1]
        if not (isinstance(last_message, AIMessage) and last_message.tool_calls):
            return {}

        print("[TOOLS] Executing sub-agent tool calls...")
        tool_messages: list[ToolMessage] = []
        deferred_storage: list[dict[str, Any]] = []

        # Track failures
        extractor_failures = state.get("extractor_failures", 0)
        last_error = state.get("last_error")
        had_extractor_failure = False

        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get("name")
            tool_call_id = tool_call.get("id")
            args = tool_call.get("args") or {}

            if not tool_name or not tool_call_id:
                continue

            if tool_name not in tool_map:
                tool_messages.append(
                    ToolMessage(
                        content=f"ERROR: Unknown tool '{tool_name}'.",
                        tool_call_id=tool_call_id,
                    )
                )
                continue

            # Execute tool immediately (no gates on storage - capture all raw data)
            try:
                result = tool_map[tool_name].invoke(args)
                result_str = str(result)
                tool_messages.append(ToolMessage(content=result_str, tool_call_id=tool_call_id))

                # Check if extractor returned an error
                if tool_name == "extractor_agent":
                    error_indicators = [
                        "EXTRACTOR ERROR", "404", "not found", "error fetching",
                        "failed to", "unable to", "timeout", "connection error"
                    ]
                    if any(indicator.lower() in result_str.lower() for indicator in error_indicators):
                        had_extractor_failure = True
                        last_error = result_str[:200]  # Store first 200 chars of error
                        print(f"[FAILURE TRACKER] Extractor failure detected. Count: {extractor_failures + 1}")

            except Exception as e:
                tool_messages.append(
                    ToolMessage(
                        content=f"ERROR executing tool '{tool_name}': {e}",
                        tool_call_id=tool_call_id,
                    )
                )
                if tool_name == "extractor_agent":
                    had_extractor_failure = True
                    last_error = str(e)[:200]
                    print(f"[FAILURE TRACKER] Extractor exception. Count: {extractor_failures + 1}")

        # Update failure counter
        if had_extractor_failure:
            extractor_failures += 1
        else:
            # Reset counter on success
            extractor_failures = 0
            last_error = None

        # Check if we've exceeded threshold
        if extractor_failures >= 5:
            print(f"[FAILURE TRACKER] ⚠️ ABORT THRESHOLD REACHED: {extractor_failures} consecutive failures")
            print(f"[FAILURE TRACKER] Last error: {last_error}")

        updates: dict[str, Any] = {}
        if tool_messages:
            updates["messages"] = tool_messages
        if deferred_storage:
            updates["deferred_storage"] = deferred_storage

        # Always update failure tracking
        updates["extractor_failures"] = extractor_failures
        updates["last_error"] = last_error

        return updates

    def request_human_approval(state: CuratorState):
        """
        Query database for pending extractions and request human approval.
        Passes FULL metadata to help human make informed decision.
        """
        import psycopg
        import json
        from dotenv import load_dotenv

        # Get database connection
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        load_dotenv(os.path.join(project_root, '.env'))
        db_url = os.environ.get('NEON_DATABASE_URL')

        try:
            conn = psycopg.connect(db_url)
            with conn.cursor() as cur:
                # Get one pending extraction (FIFO)
                cur.execute("""
                    SELECT
                        extraction_id,
                        candidate_type::text,
                        candidate_key,
                        candidate_payload,
                        ecosystem::text,
                        confidence_score,
                        confidence_reason,
                        evidence,
                        evidence_type::text,
                        snapshot_id,
                        created_at
                    FROM staging_extractions
                    WHERE status = 'pending'::candidate_status
                    ORDER BY created_at ASC
                    LIMIT 1
                """)
                row = cur.fetchone()
            conn.close()

            if not row:
                # No pending extractions
                return {"storage_approval": None, "current_interaction_id": None, "current_extraction_id": None}

            # Unpack extraction data
            (extraction_id, candidate_type, candidate_key, candidate_payload,
             ecosystem, confidence_score, confidence_reason, evidence,
             evidence_type, snapshot_id, created_at) = row

            # Parse JSONB fields
            evidence_data = evidence if isinstance(evidence, dict) else {}
            properties = candidate_payload if isinstance(candidate_payload, dict) else {}

            # Extract metadata from evidence JSONB
            raw_evidence = evidence_data.get("raw_text", "")
            reasoning_trail = evidence_data.get("reasoning_trail", {})
            duplicate_check = evidence_data.get("duplicate_check", {})
            source_metadata = evidence_data.get("source_metadata", {})

            # Get source URL from raw_snapshots
            source_url = source_metadata.get("source_url", "Unknown")
            try:
                conn = psycopg.connect(db_url)
                with conn.cursor() as cur:
                    cur.execute("SELECT source_url FROM raw_snapshots WHERE id = %s::uuid", (str(snapshot_id),))
                    snapshot_row = cur.fetchone()
                    if snapshot_row:
                        source_url = snapshot_row[0]
                conn.close()
            except:
                pass

            # Build task string for legacy training logger
            task = f"Extract {candidate_type}: {candidate_key} from {ecosystem}"

            # Log the interaction BEFORE interrupt for training data collection
            logger = get_training_logger()
            interaction_id = None
            if logger:
                try:
                    interaction_id = logger.log_interaction(
                        thread_id=state.get("current_interaction_id", "unknown"),
                        session_type="dependency_storage",
                        doc_chunk=raw_evidence[:5000] if raw_evidence else None,
                        ai_extraction={
                            "extraction_id": str(extraction_id),
                            "candidate_type": candidate_type,
                            "candidate_key": candidate_key,
                            "ecosystem": ecosystem,
                            "confidence_score": float(confidence_score),
                            "confidence_reason": confidence_reason
                        },
                        model_used="claude-sonnet-4-5"
                    )
                    print(f"[Training] Logged interaction {interaction_id}")
                except Exception as e:
                    print(f"[Training] Could not log interaction: {e}")

            print("[HITL] Requesting human verification for staged extraction...")

            # Pass FULL metadata to human (reduces ambiguity!)
            approval = interrupt({
                "type": "dependency_approval",

                # Legacy fields (for backward compatibility)
                "task": task,
                "criticality": "STAGED",
                "message": "Review extraction before promoting to truth graph.",
                "instructions": "Reply with 'approved', 'rejected', or provide corrections as JSON.",

                # NEW METADATA - What human needs to verify
                # Source Information
                "source_url": source_url,
                "source_type": source_metadata.get("source_type", "unknown"),
                "snapshot_id": str(snapshot_id),
                "fetch_timestamp": source_metadata.get("fetch_timestamp", ""),

                # Extraction Details
                "extraction_id": str(extraction_id),
                "entity_type": candidate_type,
                "entity_key": candidate_key,
                "ecosystem": ecosystem,
                "properties": properties,

                # Evidence (exact quote from source)
                "evidence_quote": raw_evidence,
                "evidence_type": evidence_type,

                # Confidence & Reasoning
                "confidence_score": float(confidence_score),
                "confidence_reason": confidence_reason,
                "reasoning_trail": reasoning_trail,

                # Duplicate Check Results
                "duplicate_check": duplicate_check,
            })

            return {
                "storage_approval": approval,
                "current_interaction_id": interaction_id,
                "current_extraction_id": str(extraction_id)
            }

        except Exception as e:
            print(f"[HITL] Error retrieving pending extraction: {e}")
            return {"storage_approval": None, "current_interaction_id": None, "current_extraction_id": None}

    def commit_deferred_storage(state: CuratorState):
        """
        Commit human's decision on staged extraction.
        - approved: Promote to core_entities
        - rejected: Mark as rejected
        - corrected: Update and promote
        """
        import psycopg
        from dotenv import load_dotenv

        extraction_id = state.get("current_extraction_id")
        if not extraction_id:
            # No extraction to commit
            return {}

        approval = state.get("storage_approval")
        human_correction = state.get("human_correction")
        interaction_id = state.get("current_interaction_id")

        # Get database connection
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        load_dotenv(os.path.join(project_root, '.env'))
        db_url = os.environ.get('NEON_DATABASE_URL')

        # Get training logger for feedback recording
        logger = get_training_logger()

        # Check if approval is a correction (dict/JSON) rather than simple string
        is_correction = isinstance(approval, dict) or (
            isinstance(approval, str) and approval not in ("approved", "rejected")
        )

        if approval == "approved":
            print(f"[HITL] Approved - promoting extraction {extraction_id} to core_entities...")

            # Record approval in training data
            if logger and interaction_id:
                try:
                    logger.record_feedback(
                        interaction_id=interaction_id,
                        feedback_type="approved",
                        corrected_output=None
                    )
                    print(f"[Training] Recorded approval for {interaction_id}")
                except Exception as e:
                    print(f"[Training] Could not record feedback: {e}")

            try:
                # Promote to core_entities using storage agent's promote_to_core tool
                from .subagents.storage import promote_to_core
                promote_result = promote_to_core.invoke({"extraction_id": extraction_id})

                return {
                    "messages": [
                        AIMessage(
                            content=(
                                f"[HITL] Human verified extraction {extraction_id}. "
                                "Promoted to truth graph.\n\n"
                                f"{promote_result}"
                            )
                        )
                    ],
                    "deferred_storage": [],
                    "storage_approval": None,
                    "current_interaction_id": None,
                    "current_extraction_id": None,
                }
            except Exception as e:
                return {
                    "messages": [AIMessage(content=f"[HITL] ERROR promoting extraction: {e}")],
                    "deferred_storage": [],
                    "storage_approval": None,
                    "current_interaction_id": None,
                    "current_extraction_id": None,
                }

        elif is_correction:
            print(f"[HITL] Correction received - updating extraction {extraction_id}...")

            # Parse correction if it's a string (could be JSON)
            corrected_data = approval
            if isinstance(approval, str):
                try:
                    import json
                    corrected_data = json.loads(approval)
                except json.JSONDecodeError:
                    # Not JSON, treat as note
                    corrected_data = {"note": approval}

            # Record correction in training data - THIS IS GOLD for fine-tuning!
            if logger and interaction_id:
                try:
                    logger.record_feedback(
                        interaction_id=interaction_id,
                        feedback_type="corrected",
                        corrected_output=corrected_data,
                        notes="Human provided corrections to AI output"
                    )
                    print(f"[Training] Recorded correction for {interaction_id} - GOLD DATA!")
                except Exception as e:
                    print(f"[Training] Could not record correction: {e}")

            try:
                # Update extraction with corrections
                conn = psycopg.connect(db_url)
                with conn.cursor() as cur:
                    # Apply corrections to candidate_payload if provided
                    if isinstance(corrected_data, dict):
                        import json
                        # Update fields that were corrected
                        if "candidate_key" in corrected_data:
                            cur.execute("""
                                UPDATE staging_extractions
                                SET candidate_key = %s
                                WHERE extraction_id = %s::uuid
                            """, (corrected_data["candidate_key"], extraction_id))

                        if "properties" in corrected_data:
                            cur.execute("""
                                UPDATE staging_extractions
                                SET candidate_payload = %s::jsonb
                                WHERE extraction_id = %s::uuid
                            """, (json.dumps(corrected_data["properties"]), extraction_id))

                        if "confidence_score" in corrected_data:
                            cur.execute("""
                                UPDATE staging_extractions
                                SET confidence_score = %s
                                WHERE extraction_id = %s::uuid
                            """, (corrected_data["confidence_score"], extraction_id))

                conn.commit()
                conn.close()

                # Now promote the corrected extraction
                from .subagents.storage import promote_to_core
                promote_result = promote_to_core.invoke({"extraction_id": extraction_id})

                return {
                    "messages": [
                        AIMessage(
                            content=(
                                f"[HITL] Human provided corrections to extraction {extraction_id}. "
                                "Applied edits and promoted to truth graph.\n\n"
                                f"{promote_result}"
                            )
                        )
                    ],
                    "deferred_storage": [],
                    "storage_approval": None,
                    "current_interaction_id": None,
                    "current_extraction_id": None,
                    "human_correction": None,
                }
            except Exception as e:
                return {
                    "messages": [AIMessage(content=f"[HITL] ERROR applying corrections: {e}")],
                    "deferred_storage": [],
                    "storage_approval": None,
                    "current_interaction_id": None,
                    "current_extraction_id": None,
                }

        else:
            print(f"[HITL] Rejected - marking extraction {extraction_id} as rejected")

            # Record rejection in training data
            if logger and interaction_id:
                try:
                    logger.record_feedback(
                        interaction_id=interaction_id,
                        feedback_type="rejected",
                        corrected_output=None,
                        notes="Human rejected AI output"
                    )
                    print(f"[Training] Recorded rejection for {interaction_id}")
                except Exception as e:
                    print(f"[Training] Could not record rejection: {e}")

            try:
                # Mark extraction as rejected in database
                conn = psycopg.connect(db_url)
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE staging_extractions
                        SET status = 'rejected'::candidate_status
                        WHERE extraction_id = %s::uuid
                    """, (extraction_id,))
                conn.commit()
                conn.close()

                return {
                    "messages": [AIMessage(content=f"[HITL] Human rejected extraction {extraction_id}. Not promoted to truth graph.")],
                    "deferred_storage": [],
                    "storage_approval": None,
                    "current_interaction_id": None,
                    "current_extraction_id": None,
                }
            except Exception as e:
                return {
                    "messages": [AIMessage(content=f"[HITL] ERROR marking extraction as rejected: {e}")],
                    "deferred_storage": [],
                    "storage_approval": None,
                    "current_interaction_id": None,
                    "current_extraction_id": None,
                }

    # Build the graph
    workflow = StateGraph(CuratorState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", run_tools_with_gate)
    workflow.add_node("approval", request_human_approval)
    workflow.add_node("commit", commit_deferred_storage)
    workflow.set_entry_point("agent")

    # Routing: agent -> tools (if tool calls) -> approval -> commit -> agent -> END (if no tool calls)
    def route_from_agent(state: MessagesState):
        """Route from agent: review if has tool calls, end otherwise."""
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"
        return "__end__"

    workflow.add_conditional_edges(
        "agent",
        route_from_agent,
        {"tools": "tools", "__end__": "__end__"}
    )
    workflow.add_edge("tools", "approval")
    workflow.add_edge("approval", "commit")
    workflow.add_edge("commit", "agent")

    # Initialize PostgreSQL checkpointer for HITL persistence (Neon)
    db_url = os.getenv('NEON_DATABASE_URL')
    if not db_url:
        raise ValueError("NEON_DATABASE_URL not set in environment")
    
    print("Setting up PostgreSQL checkpointer (Neon) for HITL...")
    
    # Use connection pool approach for persistent connections
    from psycopg_pool import ConnectionPool
    pool = ConnectionPool(conninfo=db_url, min_size=1, max_size=5)
    checkpointer = PostgresSaver(pool)
    
    # Setup tables on first use
    try:
        checkpointer.setup()
        print("  Checkpointer tables ready")
    except Exception as e:
        # Tables may already exist
        print(f"  Checkpointer setup: {e}")
    
    print("  Checkpointer connected to Neon")

    print("Curator Agent ready!")
    print()

    return workflow.compile(checkpointer=checkpointer)


# Export the graph for LangGraph
graph = create_curator()
