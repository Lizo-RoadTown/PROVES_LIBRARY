"""
Validator Sub-Agent
Specialized agent for validating dependencies against the knowledge graph
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
def check_if_dependency_exists(source: str, target: str, relationship_type: str) -> str:
    """Check if a dependency already exists in the knowledge graph."""
    try:
        gm = GraphManager()
        source_node = gm.get_node_by_name(source)

        if not source_node:
            return f"[NEW] Component '{source}' doesn't exist yet. Safe to add."

        # Check existing relationships
        existing = gm.get_node_relationships(source_node['id'], direction='outgoing')

        # Check for exact match
        for rel in existing:
            if rel['target_name'] == target and rel['relationship_type'] == relationship_type:
                return f"[DUPLICATE] Already exists: {source} --[{relationship_type}]--> {target}"

        # Check for conflicts
        if relationship_type == 'conflicts_with':
            return f"[CONFLICT] Need careful review: {source} conflicts with {target}"

        return f"[OK] Safe to add: {source} --[{relationship_type}]--> {target}"

    except Exception as e:
        return f"Error checking dependency: {str(e)}"


@tool
def verify_schema_compliance(component: str, depends_on: str, relationship_type: str, criticality: str) -> str:
    """Verify that a dependency follows ERV schema and naming conventions."""
    # Valid ERV types
    valid_types = ['depends_on', 'requires', 'enables', 'conflicts_with', 'mitigates', 'causes']
    valid_criticalities = ['HIGH', 'MEDIUM', 'LOW']

    issues = []

    if relationship_type not in valid_types:
        issues.append(f"Invalid relationship type '{relationship_type}'. Must be one of: {', '.join(valid_types)}")

    if criticality not in valid_criticalities:
        issues.append(f"Invalid criticality '{criticality}'. Must be one of: {', '.join(valid_criticalities)}")

    if not component or not depends_on:
        issues.append("Component and depends_on cannot be empty")

    if component == depends_on:
        issues.append("Component cannot depend on itself")

    if issues:
        return f"[INVALID] Schema issues:\n" + "\n".join(f"  - {issue}" for issue in issues)

    return f"[VALID] Schema compliant: {component} --[{relationship_type}]--> {depends_on} ({criticality})"


@tool
def search_similar_dependencies(component_name: str) -> str:
    """Search for similar or related dependencies for a component."""
    try:
        gm = GraphManager()
        # Search for components with similar names
        similar = gm.search_nodes(name_pattern=component_name, limit=5)

        if not similar:
            return f"No similar components found for '{component_name}'"

        result = f"Found {len(similar)} similar components:\n"
        for node in similar:
            result += f"  - {node['name']} ({node['node_type']})\n"
            # Get their dependencies
            deps = gm.get_node_relationships(node['id'], direction='outgoing')
            if deps:
                result += f"    Has {len(deps)} dependencies\n"

        return result

    except Exception as e:
        return f"Error searching: {str(e)}"


@traceable(name="validator_subagent")
def create_validator_agent():
    """
    Create the validator sub-agent

    This agent specializes in:
    - Checking for duplicate dependencies
    - Verifying ERV schema compliance
    - Detecting conflicts
    - Searching for similar dependencies
    - Ensuring data quality
    """
    model = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=0.1,
    )

    tools = [
        check_if_dependency_exists,
        verify_schema_compliance,
        search_similar_dependencies,
    ]

    agent = create_react_agent(model, tools)
    return agent
