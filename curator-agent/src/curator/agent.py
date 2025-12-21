"""
PROVES Library Curator Agent
Main agent that coordinates sub-agents for dependency curation
"""
from typing import Annotated
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState
from langsmith import traceable

# Import sub-agents
from .subagents import create_extractor_agent, create_validator_agent, create_storage_agent


# ============================================
# WRAP SUB-AGENTS AS TOOLS (DEEP AGENTS PATTERN!)
# ============================================

@tool("extractor_agent")
@traceable(name="call_extractor_subagent")
def call_extractor_agent(task: str) -> str:
    """
    Call the extractor sub-agent to extract dependencies from documentation.

    Use this when you need to:
    - Read and process documentation files
    - Extract dependencies from text
    - Identify ERV relationship types
    - Assess dependency criticality

    Args:
        task: Description of what to extract (e.g., "Extract dependencies from trial_docs/fprime_i2c_driver.md")

    Returns:
        Extraction results with found dependencies
    """
    extractor = create_extractor_agent()
    result = extractor.invoke({"messages": [{"role": "user", "content": task}]})
    return result['messages'][-1].content


@tool("validator_agent")
@traceable(name="call_validator_subagent")
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
def call_storage_agent(task: str) -> str:
    """
    Call the storage sub-agent to store validated dependencies.

    Use this when you need to:
    - Create nodes in the knowledge graph
    - Store dependency relationships
    - Get graph statistics
    - Manage database operations

    Args:
        task: Description of what to store (e.g., "Store dependency: ImuManager depends_on LinuxI2cDriver (HIGH criticality)")

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
    - Enables human-in-the-loop via LangSmith Studio
    """
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

## Your Sub-Agents

You coordinate THREE specialized sub-agents:

1. **Extractor Agent** (`extractor_agent` tool)
   - Extracts dependencies from documentation
   - Identifies ERV relationship types
   - Assesses criticality levels
   - Use when: You need to process documentation files

2. **Validator Agent** (`validator_agent` tool)
   - Checks for duplicates
   - Verifies schema compliance
   - Detects conflicts
   - Use when: You need to validate dependencies before storage

3. **Storage Agent** (`storage_agent` tool)
   - Creates nodes
   - Stores relationships
   - Manages database
   - Use when: You're ready to save validated dependencies

## Workflow

For each request, follow this pattern:

1. **Extract**: Use extractor_agent to process documentation
2. **Validate**: Use validator_agent to check each HIGH criticality dependency
3. **Store**: Use storage_agent to save validated dependencies
4. **Report**: Summarize what was stored and any issues

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

Work autonomously but explain your reasoning. The human can watch and intervene via LangSmith Studio."""

    # Agent logic
    def call_model(state: MessagesState):
        messages = [{"role": "system", "content": system_message}] + state["messages"]
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}

    # Build the graph
    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", call_model)
    workflow.set_entry_point("agent")

    # Add tool node for sub-agent calls
    from langgraph.prebuilt import ToolNode
    tool_node = ToolNode(tools)
    workflow.add_node("tools", tool_node)

    # Add conditional edges
    from langgraph.prebuilt import tools_condition
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile()


# Export the graph for LangGraph
graph = create_curator()
