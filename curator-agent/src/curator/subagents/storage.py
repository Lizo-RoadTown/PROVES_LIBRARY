"""
Storage Sub-Agent
Specialized agent for storing validated dependencies in the knowledge graph
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../scripts'))

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langsmith import traceable
from graph_manager import GraphManager


@tool
def create_or_get_node(name: str, node_type: str, description: str = "") -> str:
    """Create a new node or get existing one."""
    try:
        gm = GraphManager()

        # Check if exists
        existing = gm.get_node_by_name(name, node_type)
        if existing:
            return f"[EXISTS] Node '{name}' already exists (ID: {existing['id']})"

        # Create new
        node_id = gm.create_node(name, node_type, description)
        return f"[CREATED] Node '{name}' created (ID: {node_id})"

    except Exception as e:
        return f"Error creating node: {str(e)}"


@tool
def store_dependency_relationship(
    source: str,
    target: str,
    relationship_type: str,
    criticality: str,
    description: str = ""
) -> str:
    """Store a dependency relationship between two components."""
    try:
        gm = GraphManager()

        # Get or create source node
        source_node = gm.get_node_by_name(source, node_type='component')
        if not source_node:
            source_id = gm.create_node(source, 'component', f'Auto-created by storage agent')
            source_node = gm.get_node(source_id)

        # Get or create target node
        target_node = gm.get_node_by_name(target, node_type='component')
        if not target_node:
            target_id = gm.create_node(target, 'component', f'Auto-created by storage agent')
            target_node = gm.get_node(target_id)

        # Create relationship
        strength_map = {'HIGH': 1.0, 'MEDIUM': 0.5, 'LOW': 0.25}
        strength = strength_map.get(criticality, 0.5)

        rel_id = gm.create_relationship(
            source_node_id=source_node['id'],
            target_node_id=target_node['id'],
            relationship_type=relationship_type,
            strength=strength,
            description=description,
            is_critical=(criticality == 'HIGH')
        )

        return f"[STORED] {source} --[{relationship_type}]--> {target} (criticality: {criticality}, ID: {rel_id})"

    except Exception as e:
        return f"Error storing relationship: {str(e)}"


@tool
def get_graph_statistics() -> str:
    """Get current knowledge graph statistics."""
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
def create_storage_agent():
    """
    Create the storage sub-agent

    This agent specializes in:
    - Creating nodes in the knowledge graph
    - Storing dependency relationships
    - Managing database transactions
    - Tracking graph statistics
    - Ensuring data integrity
    """
    model = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=0.1,
    )

    tools = [
        create_or_get_node,
        store_dependency_relationship,
        get_graph_statistics,
    ]

    agent = create_react_agent(model, tools)
    return agent
