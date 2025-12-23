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
    deferred_storage: NotRequired[list[dict[str, Any]]]
    storage_approval: NotRequired[str | None]
    human_correction: NotRequired[dict[str, Any] | None]  # For corrected extractions
    current_interaction_id: NotRequired[str | None]  # Track for training data
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

Your mission: Extract dependencies from CubeSat system documentation and build a comprehensive knowledge graph that prevents catastrophic mission failures due to hidden cross-system dependencies.

## Fail-Fast Safeguards

CRITICAL: You have a failure counter that tracks consecutive extractor failures. If the extractor fails 5 times in a row:
- **STOP IMMEDIATELY** - Do not make more extractor calls
- **REPORT THE PROBLEM** - Tell the human what's failing and why
- **SUGGEST SOLUTIONS** - Recommend fixing the URL, checking documentation map, or switching sources

Check your failure counter before each extractor call. If you see repeated failures with the same approach, CHANGE STRATEGY instead of retrying the same thing.

## Your Sub-Agents

You coordinate THREE specialized sub-agents that prepare data for HUMAN verification:

1. **Extractor Agent** (`extractor_agent` tool)
   - Grabs ALL raw data from sources
   - Makes smart categorization attempts ("this component belongs to this hardware")
   - Provides context based on source/origin
   - Use when: You need to capture documentation, code, or specs
   - **FAILS when**: URLs don't exist (404), timeouts, connection errors

2. **Validator Agent** (`validator_agent` tool)
   - Checks everything is in place
   - Verifies confidence levels are high
   - Flags anything out of ordinary or breaking patterns
   - Notes uncited data or confidence dips
   - Can loop back to Extractor for more context
   - Use when: You need to validate and flag data for human review

3. **Storage Agent** (`storage_agent` tool)
   - Routes data to appropriate staging table
   - Clean data → normal staging
   - Suspect data → flagged table with reasoning
   - Prepares data for human review queue
   - Use when: You're ready to stage data for human verification

## Workflow

For each request, follow this SEQUENTIAL pattern:

1. **Extract**: Call extractor_agent to capture ALL raw data with context and categorization attempts.
2. **Validate**: Call validator_agent to check confidence, flag anomalies, note pattern breaks.
3. **Stage**: Call storage_agent to route data to appropriate staging tables for human review.
4. **Report**: Provide summary of what was captured, flagged, and staged.

**Remember:** You are preparing data for HUMAN verification. Provide context to help humans eliminate ambiguity. The human will align data across sources to establish TRUTH. Only human-verified data enters the knowledge graph.

CRITICAL: Capture EVERYTHING. Flag concerns. Let humans decide truth. BUT if extraction keeps failing, STOP and report the issue.

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
        deferred = state.get("deferred_storage") or []
        if not deferred:
            return {"storage_approval": None, "current_interaction_id": None}

        # Only approve one at a time for now (simple + predictable).
        pending = deferred[0]
        task = pending.get("task", "")

        # Log the interaction BEFORE interrupt for training data collection
        logger = get_training_logger()
        interaction_id = None
        if logger:
            try:
                interaction_id = logger.log_interaction(
                    thread_id=state.get("current_interaction_id", "unknown"),
                    session_type="dependency_storage",
                    doc_chunk=task[:5000] if task else None,  # Truncate to 5K chars
                    ai_extraction=pending,  # The deferred storage data
                    model_used="claude-sonnet-4-5"
                )
                print(f"[Training] Logged interaction {interaction_id}")
            except Exception as e:
                print(f"[Training] Could not log interaction: {e}")

        print("[HITL] Requesting human verification for staged data...")
        approval = interrupt({
            "type": "dependency_approval",
            "task": task,
            "criticality": "STAGED",
            "message": "This data is staged for human verification. Review before promoting to truth graph.",
            "instructions": "Reply with 'approved', 'rejected', or provide corrections as JSON."
        })

        return {"storage_approval": approval, "current_interaction_id": interaction_id}

    def commit_deferred_storage(state: CuratorState):
        deferred = state.get("deferred_storage") or []
        if not deferred:
            return {}

        approval = state.get("storage_approval")
        human_correction = state.get("human_correction")
        interaction_id = state.get("current_interaction_id")
        task = (deferred[0] or {}).get("task", "")
        
        # Get training logger for feedback recording
        logger = get_training_logger()

        # Check if approval is a correction (dict/JSON) rather than simple string
        is_correction = isinstance(approval, dict) or (
            isinstance(approval, str) and approval not in ("approved", "rejected")
        )

        if approval == "approved":
            print("[HITL] Approved - executing deferred storage_agent now...")
            
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
                storage_result = call_storage_agent(task)
                return {
                    "messages": [
                        AIMessage(
                            content=(
                                "[HITL] Human verified staged data. "
                                "Promoted to truth graph.\n\n"
                                f"{storage_result}"
                            )
                        )
                    ],
                    "deferred_storage": [],
                    "storage_approval": None,
                    "current_interaction_id": None,
                }
            except Exception as e:
                return {
                    "messages": [AIMessage(content=f"[HITL] ERROR executing deferred storage_agent: {e}")],
                    "deferred_storage": [],
                    "storage_approval": None,
                    "current_interaction_id": None,
                }
        
        elif is_correction:
            print("[HITL] Correction received - applying human edits...")
            
            # Parse correction if it's a string (could be JSON)
            corrected_data = approval
            if isinstance(approval, str):
                try:
                    import json
                    corrected_data = json.loads(approval)
                except json.JSONDecodeError:
                    # Not JSON, treat as corrected task string
                    corrected_data = {"task": approval}
            
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
            
            # Use corrected data for storage
            corrected_task = corrected_data.get("task", task) if isinstance(corrected_data, dict) else task
            
            try:
                storage_result = call_storage_agent(corrected_task)
                return {
                    "messages": [
                        AIMessage(
                            content=(
                                "[HITL] Human provided corrections. Applied edits and executed storage_agent.\n\n"
                                f"Original: {task[:200]}...\n"
                                f"Corrected: {corrected_task[:200]}...\n\n"
                                f"{storage_result}"
                            )
                        )
                    ],
                    "deferred_storage": [],
                    "storage_approval": None,
                    "current_interaction_id": None,
                    "human_correction": None,
                }
            except Exception as e:
                return {
                    "messages": [AIMessage(content=f"[HITL] ERROR executing corrected storage_agent: {e}")],
                    "deferred_storage": [],
                    "storage_approval": None,
                    "current_interaction_id": None,
                }

        else:
            print("[HITL] Rejected - skipping deferred storage_agent")
            
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
            
            return {
                "messages": [AIMessage(content="[HITL] Human rejected staged data. Not promoted to truth graph.")],
                "deferred_storage": [],
                "storage_approval": None,
                "current_interaction_id": None,
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
