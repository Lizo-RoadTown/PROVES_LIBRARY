#!/usr/bin/env python3
"""
Curator Agent for PROVES Library
Uses LangChain agents to autonomously extract, validate, and store dependencies
"""
import os
import sys
from typing import Annotated
from dotenv import load_dotenv

# LangChain imports
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langsmith import traceable

# Local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from graph_manager import GraphManager
from dependency_extractor import DependencyExtractor, process_document_pipeline

# Load environment
load_dotenv()


# ============================================
# TOOLS FOR THE CURATOR AGENT
# ============================================

@tool
def search_dependencies(component_name: str) -> str:
    """
    Search for existing dependencies of a component in the knowledge graph.

    Args:
        component_name: Name of the component to search for

    Returns:
        String describing found dependencies or error message
    """
    gm = GraphManager()

    # Find the node
    node = gm.get_node_by_name(component_name, node_type='component')
    if not node:
        # Try without type filter
        node = gm.get_node_by_name(component_name)

    if not node:
        return f"No component found named '{component_name}'. Try searching for similar names."

    # Get relationships
    deps = gm.get_node_relationships(node['id'], direction='outgoing')

    if not deps:
        return f"Component '{component_name}' exists but has no documented dependencies yet."

    # Format results
    result = f"Found {len(deps)} dependencies for '{component_name}':\n"
    for dep in deps:
        result += f"  - {dep['relationship_type']} → {dep['target_name']}"
        if dep.get('description'):
            result += f": {dep['description']}"
        result += "\n"

    return result


@tool
def extract_from_document(doc_path: str) -> str:
    """
    Extract dependencies from a documentation file using LLM.

    Args:
        doc_path: Path to the documentation file (relative or absolute)

    Returns:
        String summary of extraction results
    """
    if not os.path.exists(doc_path):
        return f"Error: File not found at '{doc_path}'"

    # Run the extraction pipeline
    doc_name = os.path.basename(doc_path)
    try:
        result = process_document_pipeline(doc_path, doc_name)

        stats = result['statistics']
        summary = f"Extracted {stats['total_dependencies']} dependencies from '{doc_name}':\n"
        summary += f"  Criticality: HIGH={stats['by_criticality']['HIGH']}, "
        summary += f"MEDIUM={stats['by_criticality']['MEDIUM']}, "
        summary += f"LOW={stats['by_criticality']['LOW']}\n"
        summary += f"  Types: {', '.join([f'{k}={v}' for k, v in stats['by_type'].items()])}\n"
        summary += f"\nUse store_dependency tool to save these to the knowledge graph."

        # Store the result for later retrieval
        global _last_extraction_result
        _last_extraction_result = result

        return summary
    except Exception as e:
        return f"Error extracting from '{doc_path}': {str(e)}"


@tool
def store_dependency(
    source_component: str,
    target_component: str,
    relationship_type: str,
    description: str = "",
    criticality: str = "MEDIUM"
) -> str:
    """
    Store a new dependency relationship in the knowledge graph.

    Args:
        source_component: Name of the source component
        target_component: Name of the target component (what source depends on)
        relationship_type: ERV type (depends_on, requires, enables, conflicts_with, mitigates, causes)
        description: Optional description of the dependency
        criticality: HIGH, MEDIUM, or LOW (default: MEDIUM)

    Returns:
        String confirming storage or error message
    """
    gm = GraphManager()

    # Validate relationship type
    valid_types = ['depends_on', 'requires', 'enables', 'conflicts_with', 'mitigates', 'causes']
    if relationship_type not in valid_types:
        return f"Error: Invalid relationship_type '{relationship_type}'. Must be one of: {', '.join(valid_types)}"

    # Validate criticality
    valid_criticalities = ['HIGH', 'MEDIUM', 'LOW']
    if criticality not in valid_criticalities:
        return f"Error: Invalid criticality '{criticality}'. Must be one of: {', '.join(valid_criticalities)}"

    try:
        # Get or create source node
        source_node = gm.get_node_by_name(source_component, node_type='component')
        if not source_node:
            source_id = gm.create_node(
                name=source_component,
                node_type='component',
                description=f"Auto-created by curator agent"
            )
            source_node = gm.get_node(source_id)

        # Get or create target node
        target_node = gm.get_node_by_name(target_component, node_type='component')
        if not target_node:
            target_id = gm.create_node(
                name=target_component,
                node_type='component',
                description=f"Auto-created by curator agent"
            )
            target_node = gm.get_node(target_id)

        # Create relationship
        strength = {'HIGH': 1.0, 'MEDIUM': 0.5, 'LOW': 0.25}[criticality]
        rel_id = gm.create_relationship(
            source_node_id=source_node['id'],
            target_node_id=target_node['id'],
            relationship_type=relationship_type,
            strength=strength,
            description=description,
            is_critical=(criticality == 'HIGH')
        )

        return f"[OK] Stored: {source_component} --[{relationship_type}]--> {target_component} (criticality: {criticality})"

    except Exception as e:
        return f"Error storing dependency: {str(e)}"


@tool
def list_recent_entries(limit: int = 10) -> str:
    """
    List recently added components and relationships in the knowledge graph.

    Args:
        limit: Maximum number of entries to return (default: 10)

    Returns:
        String listing recent entries
    """
    gm = GraphManager()

    try:
        # Get recent nodes
        recent_nodes = gm.search_nodes(limit=limit)

        if not recent_nodes:
            return "No entries in knowledge graph yet."

        result = f"Recently added components (last {len(recent_nodes)}):\n"
        for node in recent_nodes:
            result += f"  - {node['name']} ({node['node_type']})"
            if node.get('description'):
                result += f": {node['description'][:50]}..."
            result += "\n"

        # Get statistics
        stats = gm.get_statistics()
        result += f"\nGraph Statistics:\n"
        result += f"  Total nodes: {stats['total_nodes']}\n"
        result += f"  Total relationships: {stats['total_relationships']}\n"

        return result

    except Exception as e:
        return f"Error listing entries: {str(e)}"


@tool
def validate_dependency(
    source_component: str,
    target_component: str,
    relationship_type: str
) -> str:
    """
    Validate if a dependency already exists or conflicts with existing knowledge.

    Args:
        source_component: Source component name
        target_component: Target component name
        relationship_type: ERV relationship type

    Returns:
        Validation result (exists, conflicts, or OK to add)
    """
    gm = GraphManager()

    # Find source node
    source_node = gm.get_node_by_name(source_component)
    if not source_node:
        return f"OK to add - '{source_component}' is new to the knowledge graph"

    # Check existing relationships
    existing = gm.get_node_relationships(source_node['id'], direction='outgoing')

    # Check for exact match
    for rel in existing:
        if rel['target_name'] == target_component and rel['relationship_type'] == relationship_type:
            return f"[WARNING] Already exists: {source_component} --[{relationship_type}]--> {target_component}"

    # Check for conflicts
    conflicts = ['conflicts_with']
    for rel in existing:
        if rel['target_name'] == target_component and rel['relationship_type'] in conflicts:
            return f"[WARNING] Conflict detected: {source_component} already has '{rel['relationship_type']}' relationship with {target_component}"

    return f"[OK] OK to add: {source_component} --[{relationship_type}]--> {target_component}"


# ============================================
# CURATOR AGENT
# ============================================

# Global to store last extraction result
_last_extraction_result = None


@traceable(name="curator_agent_session")
def create_curator_agent():
    """
    Create the curator agent with all tools

    Returns:
        LangGraph agent
    """
    # Initialize LLM - Using Claude (Anthropic)!
    model = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=0.1,  # Low temperature for consistent curation
    )

    # Define tools
    tools = [
        search_dependencies,
        extract_from_document,
        store_dependency,
        list_recent_entries,
        validate_dependency
    ]

    # Create the agent (we'll add system prompt in the user messages)
    agent = create_react_agent(model, tools)

    return agent


# ============================================
# TESTING AND CLI
# ============================================

def test_curator():
    """Test the curator agent with a simple task"""
    print("Initializing Curator Agent...")

    agent = create_curator_agent()

    # Test task: List current state
    print("\nTesting: List recent entries...")
    result = agent.invoke({"messages": [HumanMessage(content="List the current state of the knowledge graph")]})

    print("\nAgent Response:")
    # LangGraph returns messages in the result
    print(result['messages'][-1].content)

    print("\nCurator agent is working! Check LangSmith for full trace.")


def curate_document(doc_path: str):
    """Run curator agent on a specific document"""
    print(f"Curator Agent: Processing {doc_path}...")

    agent = create_curator_agent()

    result = agent.invoke({
        "messages": [HumanMessage(content=f"""Please extract and store all dependencies from the document at: {doc_path}

Work through these steps:
1. Extract dependencies from the document
2. For each HIGH criticality dependency:
   - Validate it doesn't already exist
   - Store it in the knowledge graph
3. Report summary of what was stored

Focus on HIGH criticality dependencies first.""")]
    })

    print("\nAgent Response:")
    print(result['messages'][-1].content)

    print("\nFull trace available in LangSmith UI")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='PROVES Library Curator Agent')
    parser.add_argument('--test', action='store_true', help='Run test mode')
    parser.add_argument('--doc', type=str, help='Process a specific document')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')

    args = parser.parse_args()

    if args.test:
        test_curator()
    elif args.doc:
        curate_document(args.doc)
    elif args.interactive:
        print("Curator Agent - Interactive Mode")
        print("Type your requests, or 'quit' to exit\n")

        agent = create_curator_agent()

        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ['quit', 'exit', 'q']:
                break

            result = agent.invoke({"messages": [HumanMessage(content=user_input)]})

            print(f"\nCurator: {result['messages'][-1].content}")
    else:
        print("Usage:")
        print("  python curator_agent.py --test                  # Test the agent")
        print("  python curator_agent.py --doc <path>            # Process a document")
        print("  python curator_agent.py --interactive           # Interactive mode")
        print("\nExamples:")
        print("  python curator_agent.py --test")
        print("  python curator_agent.py --doc trial_docs/fprime_i2c_driver_full.md")
        print("  python curator_agent.py --interactive")
