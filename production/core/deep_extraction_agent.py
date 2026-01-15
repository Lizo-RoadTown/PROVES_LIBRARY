"""
PROVES Deep Extraction Agent
Built with deepagents for multi-step knowledge extraction

This agent uses:
- Planning (TodoList) to break down complex extraction tasks
- File system to manage large documentation contexts
- Subagents for specialized extraction subtasks
- Persistent memory across extraction sessions
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool

# Load environment
load_dotenv()


# ============================================================================
# System Prompts
# ============================================================================

EXTRACTION_SYSTEM_PROMPT = """You are a knowledge extraction specialist for the PROVES Library.

Your task is to extract structured knowledge from technical documentation about satellite systems,
specifically F Prime and PROVES Kit components.

EXTRACTION WORKFLOW:

1. **Planning Phase**:
   - Use write_todos to break down the extraction task
   - Create todos for: reading documentation, extracting entities, extracting relationships, quality checks

2. **Extraction Phase**:
   For each document section:
   - Extract Components (discrete modules: sensors, drivers, boards)
   - Extract Interfaces (connection points: I2C, SPI, power rails)
   - Extract Flows (what moves through interfaces: data, power, commands)
   - Extract Dependencies (what relies on what, under which conditions)

3. **Quality Assurance**:
   - Verify all extractions have source references
   - Ensure confidence scores are realistic
   - Check that relationships are directional and attributed
   - Save intermediate results to file system

4. **Output Format**:
   Every extraction must include:
   - candidate_type: "component", "interface", "flow", or "dependency"
   - candidate_key: Unique identifier
   - description: What it is and why it matters
   - source_reference: URL + line number
   - context: Conditions and dependencies
   - confidence_score: 0.0-1.0 (be conservative)

KNOWLEDGE STRUCTURE (FRAMES):
- Components: Discrete modules (what exists)
- Interfaces: Connection points (where they connect)
- Flows: What moves through interfaces (data, power, heat)
- Dependencies: What relies on what (relationships)

RELATIONSHIP ATTRIBUTES:
1. Directionality: One-way or bidirectional?
2. Strength: Always, sometimes, never?
3. Mechanism: Electrical, thermal, timing, protocol?
4. Knownness: Verified, assumed, unknown?
5. Scope: Under which conditions? (version, hardware, mode)

GUIDELINES:
- Break complex documentation into manageable chunks using file system
- Use subagents for parallel extraction of different sections
- Be conservative with confidence scores (< 0.5 for assumptions)
- Always trace back to source documentation
- Update todos as you progress
- Save findings to files before inserting to database
"""


# ============================================================================
# Custom Tools for PROVES Extraction
# ============================================================================

@tool
def query_staging_extractions(query: str) -> str:
    """Query existing staging extractions to avoid duplicates.

    Args:
        query: Search query for candidate_key or description

    Returns:
        List of matching extractions
    """
    # TODO: Implement actual database query
    # from production.core.db import get_staging_extractions
    # results = get_staging_extractions(query)
    # return format_results(results)

    return f"Placeholder: Would search staging for '{query}'"


@tool
def insert_staging_extraction(extraction: Dict[str, Any]) -> str:
    """Insert an extraction into the staging table for human verification.

    Args:
        extraction: Dict with keys:
            - candidate_type: str
            - candidate_key: str
            - description: str
            - source_url: str
            - source_line_start: int
            - context: str
            - confidence_score: float
            - dimensional_metadata: Dict

    Returns:
        Confirmation with staging ID
    """
    # TODO: Implement actual database insertion
    # from production.core.db import insert_to_staging
    # staging_id = insert_to_staging(extraction)
    # return f"Inserted to staging: ID {staging_id}"

    required_fields = ["candidate_type", "candidate_key", "description",
                      "source_url", "confidence_score"]
    missing = [f for f in required_fields if f not in extraction]

    if missing:
        return f"Error: Missing required fields: {missing}"

    return f"Placeholder: Would insert {extraction['candidate_type']}: {extraction['candidate_key']}"


@tool
def fetch_documentation(url: str) -> str:
    """Fetch documentation content from a URL.

    Args:
        url: Documentation URL to fetch

    Returns:
        Documentation content as markdown
    """
    # TODO: Implement actual web fetching
    # from langchain_community.document_loaders import WebBaseLoader
    # loader = WebBaseLoader(url)
    # docs = loader.load()
    # return docs[0].page_content

    return f"Placeholder: Would fetch content from {url}"


# ============================================================================
# Agent Creation
# ============================================================================

def create_proves_extraction_agent(
    model_name: str = "claude-sonnet-4-5-20250929",
    enable_subagents: bool = True,
    enable_memory: bool = True,
):
    """Create a deep agent for PROVES knowledge extraction.

    Args:
        model_name: LLM model to use
        enable_subagents: Whether to enable subagent delegation
        enable_memory: Whether to enable cross-session memory

    Returns:
        Compiled LangGraph agent
    """

    # Initialize model
    model = init_chat_model(model_name, temperature=0)

    # Custom tools specific to PROVES
    custom_tools = [
        query_staging_extractions,
        insert_staging_extraction,
        fetch_documentation,
    ]

    # Create deep agent with all middleware
    agent = create_deep_agent(
        model=model,
        tools=custom_tools,
        system_prompt=EXTRACTION_SYSTEM_PROMPT,
        # Built-in tools from deepagents:
        # - write_todos, update_todos (planning)
        # - read_file, write_file, edit_file, ls (file system)
        # - task (subagent delegation, if enabled)
    )

    return agent


# ============================================================================
# Helper Functions
# ============================================================================

def extract_from_url(url: str, agent=None) -> Dict[str, Any]:
    """Extract knowledge from a single documentation URL.

    Args:
        url: Documentation URL to process
        agent: Pre-created agent (optional, will create new if None)

    Returns:
        Dict with extraction results and metadata
    """
    if agent is None:
        agent = create_proves_extraction_agent()

    prompt = f"""Extract all knowledge from this documentation URL: {url}

Please:
1. Create a todo list for the extraction
2. Fetch and analyze the documentation
3. Extract all components, interfaces, flows, and dependencies
4. Save intermediate results to files
5. Insert verified extractions to staging table
6. Provide a summary of what was extracted

Focus on technical details, connection requirements, and system dependencies."""

    result = agent.invoke({
        "messages": [{"role": "user", "content": prompt}]
    })

    return {
        "url": url,
        "response": result["messages"][-1].content,
        "metadata": {
            "todos": result.get("todos", []),
            "files_created": result.get("files", []),
        }
    }


def batch_extract_from_queue(limit: int = 10, agent=None) -> List[Dict[str, Any]]:
    """Process multiple URLs from the extraction queue.

    Args:
        limit: Maximum number of URLs to process
        agent: Pre-created agent (optional, will create new if None)

    Returns:
        List of extraction results
    """
    # TODO: Get URLs from database queue
    # from production.core.db import get_pending_urls
    # urls = get_pending_urls(limit)

    urls = []  # Placeholder

    if agent is None:
        agent = create_proves_extraction_agent()

    results = []
    for url in urls:
        print(f"Processing: {url}")
        result = extract_from_url(url, agent=agent)
        results.append(result)

    return results


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("PROVES Deep Extraction Agent - Test Run")
    print("=" * 70)

    # Create agent
    agent = create_proves_extraction_agent()

    # Test extraction
    test_url = "https://nasa.github.io/fprime/UsersGuide/best/app-man-drv.html"

    print(f"\nExtracting from: {test_url}\n")

    result = extract_from_url(test_url, agent=agent)

    print("\nExtraction Results:")
    print("-" * 70)
    print(result["response"])

    print("\n\nMetadata:")
    print(f"Todos created: {len(result['metadata']['todos'])}")
    print(f"Files created: {len(result['metadata']['files_created'])}")

    print("\n" + "=" * 70)
    print("Test Complete")
    print("=" * 70)
