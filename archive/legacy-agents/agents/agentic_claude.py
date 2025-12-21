#!/usr/bin/env python3
"""
Agentic Claude - Autonomous agent framework for PROVES Library
This makes Claude (via MCP) autonomous for:
- Database initialization
- Library indexing
- Knowledge graph management
- Code generation
- Curation workflows
"""
import os
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
import operator

# Initialize Claude
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
if not anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY not set - needed for autonomous operation")

llm = ChatAnthropic(
    model="claude-sonnet-4-5-20250929",
    api_key=anthropic_api_key,
    temperature=0
)


class AgentState(TypedDict):
    """
    State for the autonomous agent

    This maintains context across operations:
    - messages: Conversation history
    - task: Current task being executed
    - knowledge_graph_status: State of the knowledge graph
    - library_index_status: State of indexed entries
    - next_action: What to do next
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    task: str
    knowledge_graph_status: dict
    library_index_status: dict
    next_action: str


def should_continue(state: AgentState) -> str:
    """
    Decide whether to continue processing or end

    Returns:
        'continue' if more work to do, 'end' if complete
    """
    messages = state.get("messages", [])
    if not messages:
        return "end"

    last_message = messages[-1]

    # If the last message has tool calls, continue
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "continue"

    # If there's a next action specified, continue
    if state.get("next_action") and state["next_action"] != "complete":
        return "continue"

    return "end"


def autonomous_agent(state: AgentState):
    """
    Main agent loop - processes tasks autonomously

    This agent:
    1. Receives a task
    2. Plans the steps needed
    3. Executes using available tools (MCP + local)
    4. Updates its knowledge graph
    5. Reports results
    """
    messages = state.get("messages", [])
    task = state.get("task", "")

    # Build system prompt for autonomous operation
    system_prompt = """You are an autonomous AI agent managing the PROVES Library knowledge base.

Your capabilities:
- Initialize and manage a PostgreSQL knowledge graph via Neon MCP
- Index markdown library entries automatically
- Extract patterns and relationships from documentation
- Generate F´ components from patterns
- Curate raw captures into normalized entries
- Manage risk patterns and scanning

Your tools:
- Neon MCP: Direct database access (23 tools available)
- File system: Read/write library entries
- Python scripts: graph_manager.py, library_indexer.py

Philosophy:
- Autonomous: Execute tasks without human intervention
- Proactive: Build knowledge structures before being asked
- Persistent: Maintain state in the knowledge graph
- Self-improving: Learn from each operation

Current task: {task}

Execute this task autonomously, using all available tools."""

    # Add system message if this is the first call
    if not messages:
        messages = [HumanMessage(content=system_prompt.format(task=task))]

    # Call Claude with access to tools
    response = llm.invoke(messages)

    return {"messages": messages + [response]}


def create_autonomous_agent():
    """
    Create the LangGraph workflow for autonomous operation

    Returns:
        Compiled LangGraph agent
    """
    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", autonomous_agent)

    # Add edges
    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "agent",
            "end": END
        }
    )

    # Compile
    agent = workflow.compile()

    return agent


class AutonomousClaude:
    """
    Autonomous Claude instance for PROVES Library

    Usage:
        claude = AutonomousClaude()
        claude.initialize_knowledge_base()
        claude.index_library()
        claude.curate_capture(raw_text)
    """

    def __init__(self):
        self.agent = create_autonomous_agent()
        self.state = {
            "messages": [],
            "task": "",
            "knowledge_graph_status": {},
            "library_index_status": {},
            "next_action": ""
        }

    def execute_task(self, task: str) -> dict:
        """
        Execute a task autonomously

        Args:
            task: Natural language task description

        Returns:
            Result dict with status and outputs
        """
        self.state["task"] = task
        self.state["messages"] = [HumanMessage(content=task)]
        self.state["next_action"] = "start"

        # Run the agent
        final_state = self.agent.invoke(self.state)

        return {
            "status": "completed",
            "messages": final_state["messages"],
            "knowledge_graph_status": final_state.get("knowledge_graph_status", {}),
            "library_index_status": final_state.get("library_index_status", {})
        }

    def initialize_knowledge_base(self):
        """Initialize the knowledge graph database schema"""
        return self.execute_task("""
Initialize the PROVES Library knowledge base:
1. Check if the database schema exists
2. If not, apply the schema from mcp-server/schema/00_initial_schema.sql
3. Apply seed data from mcp-server/schema/01_seed_data.sql
4. Verify all tables are created correctly
5. Report statistics

Use the Neon MCP tools to execute SQL directly.
""")

    def index_library(self):
        """Index all markdown files from library/ into the knowledge graph"""
        return self.execute_task("""
Index all library entries:
1. Scan library/ directory for .md files
2. Parse each file (frontmatter + content)
3. Extract metadata, tags, citations
4. Insert into library_entries table
5. Create corresponding knowledge graph nodes
6. Report indexing statistics

Use library_indexer.py and graph_manager.py scripts.
""")

    def curate_capture(self, raw_capture: str, source_url: str = None):
        """
        Curate a raw capture into a normalized library entry

        Args:
            raw_capture: Unstructured text (from GitHub issue, PR, etc.)
            source_url: URL of the source

        Returns:
            Curated entry result
        """
        return self.execute_task(f"""
Curate this raw capture into a normalized library entry:

Raw capture:
{raw_capture}

Source: {source_url or 'unknown'}

Steps:
1. Extract citations and references
2. Identify hardware/software components mentioned
3. Classify the entry type (pattern, failure, component, etc.)
4. Generate tags
5. Check for duplicates in the knowledge graph
6. Score quality (0-1 scale)
7. If quality >= 0.5, create library entry
8. If quality < 0.5 or possible duplicate, flag for review
9. Update curator_jobs table

Report the curated entry and quality assessment.
""")

    def generate_component(self, description: str):
        """
        Generate an F´ component from a description

        Args:
            description: Natural language component description

        Returns:
            Generated code and tests
        """
        return self.execute_task(f"""
Generate an F´ component from this description:

{description}

Steps:
1. Search knowledge graph for similar patterns
2. Identify the component type (active, passive, queued)
3. Generate .fpp file
4. Generate C++ implementation
5. Generate unit tests
6. Validate syntax
7. Create integration example
8. Store in builder_jobs table

Return the generated code files.
""")


if __name__ == '__main__':
    print("🤖 Autonomous Claude - PROVES Library Agent")
    print("=" * 50)

    # Create autonomous instance
    claude = AutonomousClaude()

    # Example: Initialize knowledge base
    print("\n📊 Task: Initialize Knowledge Base")
    result = claude.initialize_knowledge_base()

    print(f"\nStatus: {result['status']}")
    print(f"Messages: {len(result['messages'])} exchanges")
