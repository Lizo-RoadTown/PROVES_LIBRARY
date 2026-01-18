"""
PROVES Library MCP Server

Exposes the knowledge graph through MCP tools for:
- Fast queries (database-backed)
- External documentation search (F', PROVES Kit, manufacturers)
- Source registry lookups
"""

import argparse
import asyncio
import logging
from typing import Optional, List
import httpx

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
# KNOWLEDGE SEARCH TOOLS
# ============================================

@mcp.tool()
async def search_knowledge(
    query: str,
    ecosystem: Optional[str] = None,
    entity_type: Optional[str] = None,
    include_pending: bool = False,
    limit: int = 10
) -> dict:
    """
    Search the PROVES Library knowledge base.

    Searches both verified entities and pending extractions
    for relevant knowledge about components, interfaces, and patterns.

    Args:
        query: Search query (e.g., "I2C address", "rate group", "power management")
        ecosystem: Filter by ecosystem: fprime, proveskit, generic
        entity_type: Filter by type: component, interface, subsystem
        include_pending: Include pending extractions (default False, verified only)
        limit: Maximum results to return (default 10)

    Returns:
        Dict with 'entities' (verified) and optionally 'extractions' (pending)
    """
    try:
        results = {
            "query": query,
            "entities": [],
            "extractions": []
        }

        # Search verified entities
        entities = await db.search_core_entities(
            query=query,
            entity_type=entity_type,
            ecosystem=ecosystem,
            limit=limit
        )
        results["entities"] = entities

        # Optionally include pending extractions
        if include_pending:
            extractions = await db.search_extractions(
                query=query,
                candidate_type=entity_type,
                ecosystem=ecosystem,
                status="pending",
                limit=limit
            )
            results["extractions"] = extractions

        results["total"] = len(results["entities"]) + len(results["extractions"])
        return results

    except Exception as e:
        logger.error(f"search_knowledge failed: {e}")
        return {"results": [], "total": 0, "error": str(e)}


@mcp.tool()
async def get_entity(entity_id: str) -> dict:
    """
    Get a verified entity by ID.

    Args:
        entity_id: UUID of the entity

    Returns:
        Full entity with attributes and metadata
    """
    try:
        entity = await db.get_entity(entity_id)
        if entity:
            return {"entity": entity}
        return {"error": f"Entity not found: {entity_id}"}
    except Exception as e:
        logger.error(f"get_entity failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_entities(
    ecosystem: Optional[str] = None,
    entity_type: Optional[str] = None,
    limit: int = 50
) -> dict:
    """
    List verified entities in the knowledge library.

    Args:
        ecosystem: Filter by ecosystem: fprime, proveskit, generic
        entity_type: Filter by type: component, interface, subsystem
        limit: Maximum results (default 50)

    Returns:
        List of entities with basic metadata
    """
    try:
        entities = await db.list_entities(
            entity_type=entity_type,
            ecosystem=ecosystem,
            limit=limit
        )
        return {
            "entities": entities,
            "count": len(entities),
            "filters": {"ecosystem": ecosystem, "entity_type": entity_type}
        }
    except Exception as e:
        logger.error(f"list_entities failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_library_stats() -> dict:
    """
    Get statistics about the knowledge library.

    Returns counts of verified entities and pending extractions
    broken down by type and status.
    """
    try:
        stats = await db.get_extraction_stats()
        return {"stats": stats}
    except Exception as e:
        logger.error(f"get_library_stats failed: {e}")
        return {"error": str(e)}


# ============================================
# SOURCE REGISTRY TOOLS
# ============================================

@mcp.tool()
async def get_source_locations(topic: str) -> dict:
    """
    Get source code and documentation locations for a topic.

    Uses the pre-mapped source registry to find where to look
    for information in F' and PROVES Kit repositories.

    Args:
        topic: Topic to search for (e.g., "i2c", "scheduling", "commands", "telemetry")

    Returns:
        Dict with paths to search in F' and PROVES Kit repos, plus external links
    """
    try:
        paths = registry.get_search_paths(topic)
        matching_topics = registry.find_matching_topics(topic)

        return {
            "topic": topic,
            "matching_topics": matching_topics,
            "paths": paths,
            "fprime": {
                "repo": "https://github.com/nasa/fprime",
                "docs": "https://nasa.github.io/fprime/",
                "tutorials": "https://nasa.github.io/fprime/latest/tutorials/"
            },
            "proveskit": {
                "repos": list(registry.get_proveskit_repos().keys()),
                "docs": "https://proveskit.github.io/"
            }
        }
    except Exception as e:
        logger.error(f"get_source_locations failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_hardware_info(hardware_name: str) -> dict:
    """
    Get hardware component information including datasheets and conflicts.

    Returns I2C addresses, driver mappings, known conflicts, and datasheet links.

    Args:
        hardware_name: Hardware component (e.g., "rv3032", "ms5611", "bno085", "sx1262")

    Returns:
        Hardware info including interface, address, driver, conflicts, datasheet URL
    """
    try:
        info = registry.get_hardware_info(hardware_name)
        if info:
            # Add manufacturer datasheet suggestions
            datasheets = {
                "rv3032": "https://www.microcrystal.com/fileadmin/Media/Products/RTC/App.Manual/RV-3032-C7_App-Manual.pdf",
                "bno085": "https://www.ceva-ip.com/wp-content/uploads/2019/10/BNO080_085-Datasheet.pdf",
                "ms5611": "https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Data+Sheet%7FMS5611-01BA03%7FB3%7Fpdf%7FEnglish%7FENG_DS_MS5611-01BA03_B3.pdf",
                "sx1262": "https://www.semtech.com/products/wireless-rf/lora-connect/sx1262",
                "max_m10s": "https://www.u-blox.com/en/product/max-m10-series",
                "w25q": "https://www.winbond.com/resource-files/w25q128jv%20revf%2003272018%20plus.pdf"
            }

            normalized_name = hardware_name.lower().replace("-", "_").replace(" ", "_")
            for key, url in datasheets.items():
                if key in normalized_name:
                    info["datasheet_url"] = url
                    break

            return {
                "hardware": hardware_name,
                "info": info
            }
        return {
            "hardware": hardware_name,
            "error": "Hardware not found in registry",
            "available_hardware": ["rv3032", "bno085", "ms5611", "gps_max_m10s", "radio_sx1262", "flash_w25q"],
            "hint": "Try one of the available hardware names listed above"
        }
    except Exception as e:
        logger.error(f"get_hardware_info failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def find_conflicts(component: str) -> dict:
    """
    Find known conflicts for a component.

    Checks source registry for I2C address collisions, timing conflicts,
    resource contention, and other known incompatibilities.

    Args:
        component: Component name (e.g., "MS5611", "BNO085", "RV3032")

    Returns:
        List of known conflicts with descriptions and mitigation hints
    """
    try:
        hardware_info = registry.get_hardware_info(component)

        conflicts = []
        if hardware_info:
            known = hardware_info.get('known_conflicts', [])
            conflicts = [
                {
                    "source": component,
                    "target": c.get('component', 'unknown'),
                    "reason": c.get('reason', 'Unknown conflict'),
                    "mitigation": c.get('mitigation', 'Check datasheets for alternative configurations')
                }
                for c in known
            ]

            # Check for I2C address conflicts with other registered hardware
            if 'i2c_address' in hardware_info:
                addr = hardware_info['i2c_address']
                all_hardware = registry.get_all_hardware()
                for hw_name, hw_info in all_hardware.items():
                    if hw_name.lower() != component.lower():
                        if hw_info.get('i2c_address') == addr:
                            conflicts.append({
                                "source": component,
                                "target": hw_name,
                                "reason": f"Same I2C address: {addr}",
                                "mitigation": "Use alternate address pin or I2C multiplexer"
                            })

        return {
            "component": component,
            "conflicts": conflicts,
            "count": len(conflicts),
            "hardware_info": hardware_info
        }
    except Exception as e:
        logger.error(f"find_conflicts failed: {e}")
        return {"error": str(e)}


# ============================================
# EXTERNAL REACH TOOLS
# ============================================

# Import external search functions
from proves_mcp.external import (
    search_cubesat_manufacturers,
    search_component_distributors,
    search_nasa_technical_reports,
    search_arxiv_papers,
    lookup_space_standards,
    web_search_suggestions,
    find_alternative_components,
)


@mcp.tool()
async def search_manufacturers(
    component_type: str,
    keywords: list[str] = []
) -> dict:
    """
    Search for CubeSat/SmallSat component manufacturers.

    Find vendors that supply specific component types (EPS, radios, ADCS, etc.)
    Returns manufacturer info, websites, and product categories.

    Args:
        component_type: Type of component (eps, radio, adcs, obc, sensor, gps, thermal)
        keywords: Additional search terms (e.g., ["low power", "rad-tolerant"])

    Returns:
        List of manufacturers with relevant products and contact info
    """
    return await search_cubesat_manufacturers(component_type, keywords or None)


@mcp.tool()
async def find_distributors(
    part_number: str,
    manufacturer: str = None
) -> dict:
    """
    Get distributor search links for a component.

    Provides direct search URLs for DigiKey, Mouser, LCSC, Octopart, etc.
    Use Octopart to compare prices across multiple distributors.

    Args:
        part_number: Component part number (e.g., "MS5611-01BA03", "BNO085")
        manufacturer: Optional manufacturer name for filtering

    Returns:
        Search URLs for major electronics distributors
    """
    return await search_component_distributors(part_number, manufacturer)


@mcp.tool()
async def search_nasa_reports(query: str) -> dict:
    """
    Search NASA Technical Reports Server (NTRS).

    Find NASA mission reports, design documents, and lessons learned.
    Great for CubeSat design references and proven approaches.

    Args:
        query: Search query (e.g., "CubeSat power system design")

    Returns:
        Search URLs and related topics for NASA technical reports
    """
    return await search_nasa_technical_reports(query)


@mcp.tool()
async def search_papers(
    query: str,
    category: str = "astro-ph.IM"
) -> dict:
    """
    Search arXiv for academic papers on space systems.

    Find research papers on satellite design, instrumentation, and methods.

    Args:
        query: Search query
        category: arXiv category (astro-ph.IM=instruments, cs.SY=control systems)

    Returns:
        Search URLs for arXiv and relevant categories
    """
    return await search_arxiv_papers(query, category)


@mcp.tool()
async def lookup_standards(topic: str) -> dict:
    """
    Find relevant space industry standards.

    Returns standards from CCSDS, ECSS, and CubeSat Design Specification
    for topics like telemetry, testing, mechanical requirements, etc.

    Args:
        topic: Topic to search (telemetry, command, testing, mechanical, radiation)

    Returns:
        Relevant standards documents with URLs
    """
    return await lookup_space_standards(topic)


@mcp.tool()
async def find_alternatives(
    component: str,
    specs: dict = None
) -> dict:
    """
    Find alternative/equivalent components.

    Suggests pin-compatible or functionally equivalent parts.
    Useful when a component is out of stock or you need options.

    Args:
        component: Component name or part number (e.g., "MS5611", "BNO085")
        specs: Optional specs to match (interface, voltage, etc.)

    Returns:
        Known alternatives with notes on compatibility
    """
    return await find_alternative_components(component, specs)


@mcp.tool()
async def web_search(
    query: str,
    context: str = "cubesat"
) -> dict:
    """
    Generate optimized web search queries.

    Creates targeted search queries for finding component info,
    datasheets, application notes, and community discussions.

    Args:
        query: What to search for
        context: Context hint (cubesat, fprime, aerospace)

    Returns:
        Optimized search queries for different purposes (datasheets, forums, etc.)
    """
    return await web_search_suggestions(query, context)


# ============================================
# EXTERNAL DOCUMENTATION SEARCH (F' / PROVES)
# ============================================

@mcp.tool()
async def search_fprime_docs(query: str) -> dict:
    """
    Get F' documentation links and search suggestions.

    Provides direct links to relevant F' documentation sections
    based on the query topic.

    Args:
        query: What to search for (e.g., "rate groups", "commands", "telemetry")

    Returns:
        Links to relevant F' documentation pages
    """
    # Map common topics to F' documentation pages
    doc_mappings = {
        "rate": {
            "title": "Rate Groups and Scheduling",
            "url": "https://nasa.github.io/fprime/latest/documentation/user-guide/rate-groups.html",
            "description": "How rate groups schedule component execution"
        },
        "command": {
            "title": "Commands",
            "url": "https://nasa.github.io/fprime/latest/documentation/user-guide/commands.html",
            "description": "Defining and dispatching commands"
        },
        "telemetry": {
            "title": "Telemetry",
            "url": "https://nasa.github.io/fprime/latest/documentation/user-guide/telemetry.html",
            "description": "Telemetry channels and downlink"
        },
        "event": {
            "title": "Events",
            "url": "https://nasa.github.io/fprime/latest/documentation/user-guide/events.html",
            "description": "Event logging and severity levels"
        },
        "parameter": {
            "title": "Parameters",
            "url": "https://nasa.github.io/fprime/latest/documentation/user-guide/parameters.html",
            "description": "Runtime-configurable parameters"
        },
        "port": {
            "title": "Ports",
            "url": "https://nasa.github.io/fprime/latest/documentation/user-guide/ports.html",
            "description": "Component interconnection ports"
        },
        "component": {
            "title": "Components",
            "url": "https://nasa.github.io/fprime/latest/documentation/user-guide/components.html",
            "description": "Building F' components"
        },
        "topology": {
            "title": "Topologies",
            "url": "https://nasa.github.io/fprime/latest/documentation/user-guide/topologies.html",
            "description": "System topology and integration"
        },
        "fpp": {
            "title": "FPP Language Guide",
            "url": "https://nasa.github.io/fpp/fpp-users-guide.html",
            "description": "F Prime Prime modeling language"
        },
        "driver": {
            "title": "Drivers",
            "url": "https://nasa.github.io/fprime/latest/documentation/user-guide/drivers.html",
            "description": "Hardware drivers and interfaces"
        },
        "tutorial": {
            "title": "Tutorials",
            "url": "https://nasa.github.io/fprime/latest/tutorials/",
            "description": "Step-by-step F' tutorials"
        }
    }

    query_lower = query.lower()
    relevant_docs = []

    for key, doc in doc_mappings.items():
        if key in query_lower:
            relevant_docs.append(doc)

    # Always include general references
    general_refs = [
        {
            "title": "F' User Guide",
            "url": "https://nasa.github.io/fprime/latest/documentation/user-guide/",
            "description": "Complete F' user documentation"
        },
        {
            "title": "F' GitHub Repository",
            "url": "https://github.com/nasa/fprime",
            "description": "Source code and examples"
        }
    ]

    return {
        "query": query,
        "relevant_docs": relevant_docs if relevant_docs else general_refs,
        "all_topics": list(doc_mappings.keys()),
        "hint": "Use these links to find detailed documentation on your topic"
    }


@mcp.tool()
async def search_proveskit_docs(query: str) -> dict:
    """
    Get PROVES Kit documentation and repository links.

    Provides links to relevant PROVES Kit repos and documentation
    based on the query topic.

    Args:
        query: What to search for (e.g., "power", "radio", "gps")

    Returns:
        Links to relevant PROVES Kit resources
    """
    # PROVES Kit repository links
    repos = {
        "flight_software": {
            "title": "Flight Software",
            "url": "https://github.com/proveskit/flight-software",
            "description": "F'-based flight software for PROVES missions"
        },
        "pysquared": {
            "title": "PySquared",
            "url": "https://github.com/proveskit/pysquared",
            "description": "CircuitPython-based flight software"
        },
        "avionics": {
            "title": "Avionics Board",
            "url": "https://github.com/proveskit/avionics-board",
            "description": "Hardware design files"
        },
        "documentation": {
            "title": "Documentation",
            "url": "https://proveskit.github.io/",
            "description": "Official PROVES Kit documentation"
        }
    }

    # Topic to repo mapping
    topic_mappings = {
        "power": ["flight_software", "avionics"],
        "radio": ["flight_software", "pysquared"],
        "gps": ["flight_software", "pysquared"],
        "sensor": ["flight_software", "pysquared", "avionics"],
        "i2c": ["flight_software", "pysquared"],
        "spi": ["flight_software", "pysquared"],
        "hardware": ["avionics"],
        "board": ["avionics"],
        "python": ["pysquared"],
        "circuitpython": ["pysquared"]
    }

    query_lower = query.lower()
    relevant_repos = set()

    for topic, repo_list in topic_mappings.items():
        if topic in query_lower:
            relevant_repos.update(repo_list)

    # If no specific matches, return all
    if not relevant_repos:
        relevant_repos = set(repos.keys())

    return {
        "query": query,
        "relevant_repos": [repos[r] for r in relevant_repos if r in repos],
        "all_repos": list(repos.values()),
        "hint": "Check these repositories for PROVES Kit-specific implementations"
    }


@mcp.tool()
async def get_datasheet_links(component: str) -> dict:
    """
    Get manufacturer datasheet and reference links for a component.

    Args:
        component: Component name (e.g., "MS5611", "BNO085", "SX1262")

    Returns:
        Links to manufacturer datasheets and application notes
    """
    # Manufacturer documentation links
    datasheets = {
        "ms5611": {
            "manufacturer": "TE Connectivity",
            "datasheet": "https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Data+Sheet%7FMS5611-01BA03%7FB3%7Fpdf%7FEnglish%7FENG_DS_MS5611-01BA03_B3.pdf",
            "product_page": "https://www.te.com/en/product-CAT-BLPS0036.html",
            "notes": "Barometric pressure sensor, I2C/SPI, address 0x76 or 0x77"
        },
        "bno085": {
            "manufacturer": "CEVA/Bosch",
            "datasheet": "https://www.ceva-ip.com/wp-content/uploads/2019/10/BNO080_085-Datasheet.pdf",
            "product_page": "https://www.ceva-ip.com/product/bno085/",
            "notes": "9-DOF IMU with sensor fusion, I2C address 0x4A or 0x4B"
        },
        "rv3032": {
            "manufacturer": "Micro Crystal",
            "datasheet": "https://www.microcrystal.com/fileadmin/Media/Products/RTC/App.Manual/RV-3032-C7_App-Manual.pdf",
            "product_page": "https://www.microcrystal.com/en/products/real-time-clock-rtc-modules/rv-3032-c7/",
            "notes": "Real-time clock with temperature compensation, I2C address 0x51"
        },
        "sx1262": {
            "manufacturer": "Semtech",
            "datasheet": "https://www.semtech.com/products/wireless-rf/lora-connect/sx1262#documentation",
            "product_page": "https://www.semtech.com/products/wireless-rf/lora-connect/sx1262",
            "notes": "LoRa transceiver, SPI interface"
        },
        "max-m10s": {
            "manufacturer": "u-blox",
            "datasheet": "https://www.u-blox.com/en/docs/UBX-20035208",
            "product_page": "https://www.u-blox.com/en/product/max-m10-series",
            "notes": "GPS/GNSS module, UART interface"
        },
        "w25q128": {
            "manufacturer": "Winbond",
            "datasheet": "https://www.winbond.com/resource-files/w25q128jv%20revf%2003272018%20plus.pdf",
            "product_page": "https://www.winbond.com/hq/product/code-storage-flash-memory/serial-nor-flash/",
            "notes": "128Mbit NOR flash, SPI interface"
        }
    }

    component_lower = component.lower().replace("-", "").replace("_", "").replace(" ", "")

    for key, info in datasheets.items():
        key_normalized = key.replace("-", "").replace("_", "")
        if key_normalized in component_lower or component_lower in key_normalized:
            return {
                "component": component,
                "found": True,
                **info
            }

    return {
        "component": component,
        "found": False,
        "available_components": list(datasheets.keys()),
        "hint": "Component not in registry. Check manufacturer website directly."
    }


# ============================================
# HEALTH CHECK TOOL
# ============================================

@mcp.tool()
async def health_check() -> dict:
    """
    Check server health and database connectivity.

    Returns:
        Health status including database connection state
    """
    status = {
        "status": "healthy",
        "server": "PROVES Library MCP",
        "version": "1.0.0",
        "database": "unknown"
    }

    try:
        # Test database connection
        stats = await db.get_extraction_stats()
        status["database"] = "connected"
        status["entities_count"] = stats.get("verified_entities", 0)
    except Exception as e:
        status["status"] = "degraded"
        status["database"] = f"error: {str(e)}"

    return status


# ============================================
# Entry Point
# ============================================

def main():
    """Main entry point for the MCP server."""
    import os

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
        default=int(os.environ.get("PORT", 8000)),
        help="Port for HTTP transport (default: 8000)"
    )
    args = parser.parse_args()

    logger.info(f"Starting PROVES Library MCP Server (transport: {args.transport})")
    logger.info(f"Database URL configured: {'yes' if settings.database_url else 'no'}")

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        logger.info(f"Listening on port {args.port}")
        mcp.run(transport="streamable-http", port=args.port)


if __name__ == "__main__":
    main()
