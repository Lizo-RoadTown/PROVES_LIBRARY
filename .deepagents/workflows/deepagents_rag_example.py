"""
Deep Agents RAG Workflow for PROVES Library
Advanced approach using deepagents middleware

This workflow implements a deep agent that can:
1. Plan multi-step retrieval tasks using TodoList
2. Manage large context using filesystem tools
3. Spawn subagents for specialized retrieval tasks
4. Persist memory across conversations

Compare with:
- agentic_rag_example.py (reactive/conditional routing)
- sequential_rag_example.py (linear pipeline)
"""

from typing import Annotated
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent
from deepagents.middleware import TodoListMiddleware, FilesystemMiddleware, SubAgentMiddleware


# ============================================================================
# Configuration
# ============================================================================

model = init_chat_model("claude-sonnet-4.5", temperature=0)


# ============================================================================
# System Prompts
# ============================================================================

DEEP_AGENT_SYSTEM_PROMPT = """You are a research assistant for the PROVES Library documentation system.

Your capabilities:
1. **Planning**: Use write_todos to break down complex research tasks
2. **File Management**: Use read_file/write_file to manage large contexts
3. **Delegation**: Use task tool to spawn subagents for specialized work
4. **Memory**: Access information from previous conversations

Workflow for complex queries:
1. Create a todo list with write_todos to plan the research
2. For each step, decide whether to:
   - Retrieve directly from vectorstore
   - Write intermediate results to file system
   - Spawn a subagent for deep investigation
3. Synthesize findings into a comprehensive answer
4. Save important findings to file system for future reference

Guidelines:
- Break complex questions into logical subtasks
- Use file system to avoid context overflow
- Spawn subagents to isolate complex subtasks
- Update todos as you make progress
- Be thorough but concise in final answers
"""

SUBAGENT_SYSTEM_PROMPT = """You are a specialized research subagent.

Your parent agent has delegated a specific research task to you.
Focus solely on this task and return detailed findings.

You have access to:
- Retrieval tools for documentation
- File system for managing context

Return comprehensive results so the parent agent can integrate them.
"""


# ============================================================================
# Tools
# ============================================================================

def retrieve_proves_docs(query: str, k: int = 4) -> str:
    """Search and return information from PROVES Library documentation.

    Args:
        query: Search query
        k: Number of documents to retrieve

    Returns:
        Retrieved documentation chunks
    """
    # TODO: Implement actual vectorstore retrieval
    # from production.core.db import get_vectorstore
    # vectorstore = get_vectorstore()
    # docs = vectorstore.similarity_search(query, k=k)
    # return "\n\n".join([f"[Doc {i+1}]\n{doc.page_content}" for i, doc in enumerate(docs)])

    return f"Placeholder: Would retrieve {k} docs for '{query}'"


# ============================================================================
# Deep Agent Creation
# ============================================================================

def create_proves_deep_agent():
    """Create a deep agent with all middleware enabled.

    Middleware layers:
    1. TodoListMiddleware - Planning and task tracking
    2. FilesystemMiddleware - Context management
    3. SubAgentMiddleware - Spawning specialized agents
    """

    # Create the main deep agent with all middleware
    agent = create_deep_agent(
        model=model,
        tools=[retrieve_proves_docs],
        system_prompt=DEEP_AGENT_SYSTEM_PROMPT,
        middleware=[
            TodoListMiddleware(),      # write_todos, update_todos tools
            FilesystemMiddleware(),    # ls, read_file, write_file, edit_file tools
            SubAgentMiddleware(        # task tool to spawn subagents
                subagent_model=model,
                subagent_tools=[retrieve_proves_docs],
                subagent_system_prompt=SUBAGENT_SYSTEM_PROMPT,
            ),
        ],
        enable_memory=True,  # Persist across conversations
    )

    return agent


# ============================================================================
# Example Usage Scenarios
# ============================================================================

def example_simple_query():
    """Example 1: Simple query - agent retrieves and answers directly."""
    agent = create_proves_deep_agent()

    print("=" * 70)
    print("EXAMPLE 1: Simple Query")
    print("=" * 70)

    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": "What is PROVES Library?"
        }]
    })

    print(f"\nAnswer: {result['messages'][-1].content}\n")


def example_complex_research():
    """Example 2: Complex query - agent plans, retrieves, and uses files."""
    agent = create_proves_deep_agent()

    print("=" * 70)
    print("EXAMPLE 2: Complex Research Task")
    print("=" * 70)

    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": """
            Research the PROVES Library extraction pipeline and provide:
            1. An overview of the extraction process
            2. Key components and their roles
            3. Integration points with Notion and LangGraph
            4. Best practices for adding new entity types

            Please save your findings to 'extraction_pipeline_research.md' for future reference.
            """
        }]
    })

    print(f"\nAgent Response:\n{result['messages'][-1].content}\n")
    print(f"Todos Created: {result.get('todos', [])}")
    print(f"Files Created: {result.get('files', [])}")


def example_with_subagents():
    """Example 3: Using subagents for parallel investigation."""
    agent = create_proves_deep_agent()

    print("=" * 70)
    print("EXAMPLE 3: Multi-Aspect Research with Subagents")
    print("=" * 70)

    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": """
            Compare three different approaches to entity canonicalization in PROVES:
            1. Rule-based matching
            2. Embedding-based similarity
            3. LLM-based resolution

            For each approach, investigate:
            - Performance characteristics
            - Accuracy metrics
            - When to use each

            Use subagents to research each approach in parallel, then synthesize findings.
            """
        }]
    })

    print(f"\nSynthesized Answer:\n{result['messages'][-1].content}\n")
    print(f"Subagents Spawned: {result.get('subagent_count', 0)}")


# ============================================================================
# Comparison with Other Approaches
# ============================================================================

"""
ARCHITECTURE COMPARISON:

1. Sequential RAG (sequential_rag_example.py):
   - Fixed linear pipeline
   - No planning or decomposition
   - Direct function calls
   - Good for: Simple, predictable queries

2. Agentic RAG (agentic_rag_example.py):
   - Conditional routing
   - Self-correction via grading
   - Dynamic decision-making
   - Good for: Adaptive retrieval needs

3. Deep Agents RAG (this file):
   - Multi-step planning with todos
   - File system for context management
   - Subagent delegation for complex tasks
   - Persistent memory across sessions
   - Good for: Complex research, multi-step analysis

WHEN TO USE DEEP AGENTS:

✅ Complex, multi-step research tasks
✅ Need to manage large amounts of context
✅ Tasks benefit from parallel investigation
✅ Want to persist findings across sessions
✅ Need to break down ambiguous requests

❌ Simple question-answering
❌ Low-latency requirements
❌ Fully predictable workflows
❌ Small context sizes

MIDDLEWARE BREAKDOWN:

TodoListMiddleware:
- write_todos(tasks: List[str]) - Create task list
- update_todos(updates: Dict) - Mark tasks complete
- Enables planning and progress tracking

FilesystemMiddleware:
- ls(path) - List files
- read_file(path) - Read file content
- write_file(path, content) - Write file
- edit_file(path, old, new) - Edit file
- Prevents context overflow

SubAgentMiddleware:
- task(description, tools) - Spawn subagent
- Isolates context per subtask
- Enables parallel investigation
"""


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    print("\nDeep Agents RAG Examples\n")

    # Run examples
    try:
        example_simple_query()
        print("\n")
        example_complex_research()
        print("\n")
        example_with_subagents()
    except Exception as e:
        print(f"Error running examples: {e}")
        print("\nNote: Examples use placeholder retrieval.")
        print("Connect to actual vectorstore to run fully.")
