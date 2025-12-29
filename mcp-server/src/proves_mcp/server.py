"""
PROVES Library MCP Server

Exposes the knowledge graph through MCP tools for:
- Fast queries (database-backed)
- Deep queries (agent-backed with source registry)
"""

import argparse
import asyncio
import logging
from typing import Optional, List

from fastmcp import FastMCP

from proves_mcp.config import settings
from proves_mcp.db import db
from proves_mcp.registry import registry

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# MCP Server Definition
# ============================================

mcp = FastMCP("PROVES Library")


# ============================================
# FAST TOOLS (Database-backed, ~50ms)
# ============================================

@mcp.tool()
async def search_library(
    query: str,
    domain: Optional[str] = None,
    entry_type: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 10
) -> dict:
    """
    Search the PROVES Library for relevant knowledge entries.
    
    Performs semantic and keyword search across indexed patterns,
    lessons, and component documentation.
    
    Args:
        query: Search query (e.g., "I2C address conflicts")
        domain: Filter by domain: software, build, ops, systems, testing
        entry_type: Filter by type: pattern, failure, component, config, test
        tags: Filter by tags (e.g., ["power", "i2c"])
        limit: Maximum results to return (default 10)
        
    Returns:
        Dict with 'results' list and 'total' count
    """
    try:
        results = await db.search_entries(
            query=query,
            domain=domain,
            entry_type=entry_type,
            tags=tags,
            limit=limit
        )
        return {
            "results": results,
            "total": len(results),
            "query": query
        }
    except Exception as e:
        logger.error(f"search_library failed: {e}")
        return {
            "results": [],
            "total": 0,
            "error": str(e)
        }


@mcp.tool()
async def get_entry(entry_id: str) -> dict:
    """
    Get the full content of a specific library entry.
    
    Args:
        entry_id: UUID of the entry to retrieve
        
    Returns:
        Full entry with content, metadata, and relationships
    """
    try:
        entry = await db.get_entry(entry_id)
        if entry:
            return {"entry": entry}
        return {"error": f"Entry not found: {entry_id}"}
    except Exception as e:
        logger.error(f"get_entry failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_relationships(
    component: str,
    relationship_type: Optional[str] = None
) -> dict:
    """
    Get relationships for a component.
    
    Find what a component depends on, conflicts with, enables, or requires.
    
    Args:
        component: Component name (e.g., "RV3032", "I2C Driver")
        relationship_type: Filter by type:
            - depends_on: Component A depends on B
            - conflicts_with: A conflicts with B (e.g., I2C address collision)
            - enables: A enables capability B
            - requires: A requires condition/config B
            - mitigates: Solution A mitigates risk B
            - causes: Action A causes consequence B
            
    Returns:
        List of relationships with source and target components
    """
    try:
        relationships = await db.get_relationships(component, relationship_type)
        return {
            "component": component,
            "relationships": relationships,
            "count": len(relationships)
        }
    except Exception as e:
        logger.error(f"get_relationships failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def find_conflicts(component: str) -> dict:
    """
    Find known conflicts for a component.
    
    Checks for I2C address collisions, timing conflicts, resource
    contention, and other incompatibilities.
    
    Args:
        component: Component name (e.g., "MS5611", "BNO085")
        
    Returns:
        List of known conflicts with descriptions
    """
    try:
        # First check the source registry for known hardware conflicts
        hardware_info = registry.get_hardware_info(component)
        
        registry_conflicts = []
        if hardware_info:
            known = hardware_info.get('known_conflicts', [])
            registry_conflicts = [
                {
                    "source": component,
                    "target": c.get('component', 'unknown'),
                    "reason": c.get('reason', 'Unknown conflict')
                }
                for c in known
            ]
        
        # Then check the database
        db_conflicts = await db.find_conflicts(component)
        
        all_conflicts = registry_conflicts + db_conflicts
        
        return {
            "component": component,
            "conflicts": all_conflicts,
            "count": len(all_conflicts),
            "hardware_info": hardware_info
        }
    except Exception as e:
        logger.error(f"find_conflicts failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_components(
    domain: Optional[str] = None,
    limit: int = 50
) -> dict:
    """
    List components in the knowledge library.
    
    Args:
        domain: Filter by domain: software, build, ops
        limit: Maximum results (default 50)
        
    Returns:
        List of components with basic metadata
    """
    try:
        components = await db.list_components(domain, limit)
        return {
            "components": components,
            "count": len(components),
            "domain": domain
        }
    except Exception as e:
        logger.error(f"list_components failed: {e}")
        return {"error": str(e)}


# ============================================
# REGISTRY TOOLS (Source location lookup)
# ============================================

@mcp.tool()
async def get_source_locations(topic: str) -> dict:
    """
    Get source code locations for a topic.
    
    Uses the pre-mapped source registry to find where to look
    for information about a topic in F' and ProvesKit.
    
    Args:
        topic: Topic to search for (e.g., "i2c", "scheduling", "commands")
        
    Returns:
        Dict with paths to search in F' and ProvesKit repos
    """
    try:
        paths = registry.get_search_paths(topic)
        matching_topics = registry.find_matching_topics(topic)
        
        return {
            "topic": topic,
            "matching_topics": matching_topics,
            "paths": paths,
            "fprime_repo": registry.get_fprime_repo_url(),
            "proveskit_repos": list(registry.get_proveskit_repos().keys())
        }
    except Exception as e:
        logger.error(f"get_source_locations failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_hardware_info(hardware_name: str) -> dict:
    """
    Get hardware component information from the source registry.
    
    Returns I2C addresses, driver mappings, known conflicts, etc.
    
    Args:
        hardware_name: Hardware component (e.g., "rv3032", "ms5611", "bno085")
        
    Returns:
        Hardware info including interface, address, driver, conflicts
    """
    try:
        info = registry.get_hardware_info(hardware_name)
        if info:
            return {
                "hardware": hardware_name,
                "info": info
            }
        return {
            "hardware": hardware_name,
            "error": "Hardware not found in registry",
            "hint": "Try: rv3032, bno085, ms5611, gps_max_m10s, radio_sx1262"
        }
    except Exception as e:
        logger.error(f"get_hardware_info failed: {e}")
        return {"error": str(e)}


# ============================================
# DEEP TOOLS (Agent-backed, 2-10s)
# Coming soon - will invoke curator agent
# ============================================

@mcp.tool()
async def deep_search(
    query: str,
    include_fprime: bool = True,
    include_proveskit: bool = True
) -> dict:
    """
    Deep search across F' and ProvesKit documentation.
    
    [PLACEHOLDER] This tool will invoke the curator agent to search
    documentation sources not yet indexed in the database.
    
    Args:
        query: What to search for
        include_fprime: Search F' documentation
        include_proveskit: Search ProvesKit documentation
        
    Returns:
        Synthesized answer from documentation search
    """
    # TODO: Implement agent-backed deep search
    # For now, return guidance on what this will do
    
    # Find relevant paths from registry
    matching_topics = registry.find_matching_topics(query)
    paths = {}
    for topic in matching_topics:
        topic_paths = registry.get_search_paths(topic)
        for key, value in topic_paths.items():
            if key not in paths:
                paths[key] = []
            paths[key].extend(value)
    
    return {
        "status": "placeholder",
        "message": "Deep search not yet implemented. Will invoke curator agent.",
        "query": query,
        "would_search": {
            "fprime": include_fprime,
            "proveskit": include_proveskit,
            "matching_topics": matching_topics,
            "suggested_paths": paths
        },
        "hint": "Use search_library() for indexed content, or get_source_locations() to find where to look manually."
    }


# ============================================
# Entry Point
# ============================================

def main():
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="PROVES Library MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Transport type (default: stdio)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP transport (default: 8000)"
    )
    args = parser.parse_args()
    
    logger.info(f"Starting PROVES Library MCP Server (transport: {args.transport})")
    
    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", port=args.port)


if __name__ == "__main__":
    main()
