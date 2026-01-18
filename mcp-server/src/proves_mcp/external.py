"""
External Search Tools for PROVES MCP Server

Provides "reach" beyond the internal database:
- Web search for manufacturers, vendors, alternatives
- Academic paper search (arXiv, IEEE, NASA TRS)
- Standards lookup (CCSDS, ECSS, CubeSat specs)
- Component distributor search (DigiKey, Mouser, LCSC)
"""

import logging
from typing import Optional, List
import httpx

logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION
# ============================================

# API endpoints (some require keys, others are free)
SEARCH_ENDPOINTS = {
    "digikey": "https://api.digikey.com/v1/products/search",
    "octopart": "https://octopart.com/api/v4/rest/search",
    "nasa_trs": "https://ntrs.nasa.gov/api/citations/search",
    "arxiv": "http://export.arxiv.org/api/query",
}

# CubeSat and space component manufacturers
CUBESAT_MANUFACTURERS = {
    "pumpkin": {
        "name": "Pumpkin Space Systems",
        "url": "https://www.pumpkinspace.com/",
        "products": ["CubeSat kits", "structures", "avionics"],
        "contact": "sales@pumpkinspace.com"
    },
    "gomspace": {
        "name": "GomSpace",
        "url": "https://gomspace.com/",
        "products": ["NanoPower", "NanoMind", "radios", "ADCS"],
        "contact": "sales@gomspace.com"
    },
    "clyde_space": {
        "name": "AAC Clyde Space",
        "url": "https://www.aac-clyde.space/",
        "products": ["EPS", "batteries", "solar panels"],
        "contact": "sales@aac-clyde.space"
    },
    "isis": {
        "name": "ISISpace",
        "url": "https://www.isispace.nl/",
        "products": ["CubeSat structures", "deployers", "antennas"],
        "contact": "info@isispace.nl"
    },
    "nanoavionics": {
        "name": "NanoAvionics",
        "url": "https://nanoavionics.com/",
        "products": ["ADCS", "propulsion", "full satellites"],
        "contact": "info@nanoavionics.com"
    },
    "endurosat": {
        "name": "EnduroSat",
        "url": "https://www.endurosat.com/",
        "products": ["UHF/VHF radios", "OBC", "solar panels"],
        "contact": "info@endurosat.com"
    },
    "blue_canyon": {
        "name": "Blue Canyon Technologies",
        "url": "https://bluecanyontech.com/",
        "products": ["ADCS", "reaction wheels", "star trackers"],
        "contact": "info@bluecanyontech.com"
    },
    "astrodev": {
        "name": "AstroDev",
        "url": "https://www.astrodev.com/",
        "products": ["Radios", "Lithium series"],
        "contact": "sales@astrodev.com"
    }
}

# Component categories for search
COMPONENT_CATEGORIES = {
    "eps": ["power", "battery", "solar", "voltage regulator", "power distribution"],
    "radio": ["uhf", "vhf", "s-band", "x-band", "transceiver", "antenna", "lora"],
    "obc": ["computer", "processor", "flight computer", "microcontroller"],
    "adcs": ["attitude", "magnetorquer", "reaction wheel", "star tracker", "sun sensor", "imu"],
    "sensor": ["temperature", "pressure", "radiation", "magnetometer", "gyroscope", "accelerometer"],
    "gps": ["gnss", "navigation", "positioning", "ublox", "max-m10"],
    "memory": ["flash", "storage", "eeprom", "sdcard", "nand", "nor"],
    "thermal": ["heater", "thermal control", "insulation", "radiator"]
}

# Space standards references
STANDARDS = {
    "ccsds": {
        "name": "Consultative Committee for Space Data Systems",
        "url": "https://public.ccsds.org/Pubs/Forms/AllItems.aspx",
        "key_docs": [
            {"id": "133.0-B-2", "title": "Space Packet Protocol", "topic": "telemetry"},
            {"id": "232.0-B-4", "title": "TC Space Data Link Protocol", "topic": "commands"},
            {"id": "131.0-B-5", "title": "TM Space Data Link Protocol", "topic": "telemetry"},
            {"id": "727.0-B-5", "title": "CCSDS File Delivery Protocol", "topic": "file transfer"}
        ]
    },
    "ecss": {
        "name": "European Cooperation for Space Standardization",
        "url": "https://ecss.nl/standards/",
        "key_docs": [
            {"id": "ECSS-E-ST-70-41C", "title": "Packet Utilization Standard", "topic": "telemetry"},
            {"id": "ECSS-E-ST-50-12C", "title": "SpaceWire", "topic": "data bus"},
            {"id": "ECSS-Q-ST-60C", "title": "EEE Components", "topic": "components"}
        ]
    },
    "cubesat": {
        "name": "CubeSat Design Specification",
        "url": "https://www.cubesat.org/cubesatinfo",
        "key_docs": [
            {"id": "CDS Rev 14.1", "title": "CubeSat Design Specification", "topic": "mechanical"},
            {"id": "CDS Rev 14.1 App A", "title": "Test Requirements", "topic": "testing"}
        ]
    }
}


# ============================================
# MANUFACTURER SEARCH TOOLS
# ============================================

async def search_cubesat_manufacturers(
    component_type: str,
    keywords: Optional[List[str]] = None
) -> dict:
    """
    Search CubeSat component manufacturers.

    Args:
        component_type: Type of component (eps, radio, adcs, obc, etc.)
        keywords: Additional search terms

    Returns:
        List of manufacturers with products matching the criteria
    """
    component_lower = component_type.lower()
    matching_manufacturers = []

    # Find category keywords
    category_keywords = []
    for cat, kws in COMPONENT_CATEGORIES.items():
        if cat in component_lower or any(kw in component_lower for kw in kws):
            category_keywords.extend(kws)

    if keywords:
        category_keywords.extend([k.lower() for k in keywords])

    # Search manufacturers
    for mfr_id, mfr_info in CUBESAT_MANUFACTURERS.items():
        products_lower = [p.lower() for p in mfr_info["products"]]

        # Check if manufacturer has relevant products
        relevance = 0
        matched_products = []

        for product in products_lower:
            if component_lower in product:
                relevance += 2
                matched_products.append(product)
            elif any(kw in product for kw in category_keywords):
                relevance += 1
                matched_products.append(product)

        if relevance > 0:
            matching_manufacturers.append({
                "id": mfr_id,
                **mfr_info,
                "relevance": relevance,
                "matched_products": matched_products
            })

    # Sort by relevance
    matching_manufacturers.sort(key=lambda x: x["relevance"], reverse=True)

    return {
        "query": component_type,
        "keywords": category_keywords[:5],  # Top 5 keywords used
        "manufacturers": matching_manufacturers,
        "count": len(matching_manufacturers),
        "hint": "Contact manufacturers directly for quotes and datasheets"
    }


async def search_component_distributors(
    part_number: str,
    manufacturer: Optional[str] = None
) -> dict:
    """
    Get distributor links for a component.

    Note: This doesn't hit live APIs (would need API keys).
    Instead, it provides direct search URLs for major distributors.

    Args:
        part_number: Component part number (e.g., "MS5611-01BA03")
        manufacturer: Optional manufacturer name

    Returns:
        Search URLs for major distributors
    """
    part_encoded = part_number.replace(" ", "+")

    distributors = {
        "digikey": {
            "name": "DigiKey",
            "search_url": f"https://www.digikey.com/en/products/result?keywords={part_encoded}",
            "notes": "Large selection, good documentation, US-based"
        },
        "mouser": {
            "name": "Mouser",
            "search_url": f"https://www.mouser.com/c/?q={part_encoded}",
            "notes": "Wide selection, good for prototyping"
        },
        "lcsc": {
            "name": "LCSC",
            "search_url": f"https://www.lcsc.com/search?q={part_encoded}",
            "notes": "Lower cost, good for production, China-based"
        },
        "arrow": {
            "name": "Arrow Electronics",
            "search_url": f"https://www.arrow.com/en/products/search?q={part_encoded}",
            "notes": "Good for volume orders"
        },
        "newark": {
            "name": "Newark",
            "search_url": f"https://www.newark.com/search?st={part_encoded}",
            "notes": "UK/EU focused, Farnell network"
        },
        "octopart": {
            "name": "Octopart (Aggregator)",
            "search_url": f"https://octopart.com/search?q={part_encoded}",
            "notes": "Searches multiple distributors, shows pricing comparison"
        }
    }

    return {
        "part_number": part_number,
        "manufacturer": manufacturer,
        "distributors": distributors,
        "recommendation": "Use Octopart to compare prices across distributors",
        "hint": "For space-grade components, check manufacturer directly for radiation specs"
    }


# ============================================
# ACADEMIC / TECHNICAL SEARCH
# ============================================

async def search_nasa_technical_reports(
    query: str,
    limit: int = 10
) -> dict:
    """
    Search NASA Technical Reports Server (NTRS).

    Provides search URL for NASA's public technical reports database.

    Args:
        query: Search query (e.g., "CubeSat power system")
        limit: Maximum results

    Returns:
        Search URL and common related topics
    """
    query_encoded = query.replace(" ", "+")

    # Related topics for CubeSat searches
    related_topics = []
    query_lower = query.lower()

    if "cubesat" in query_lower or "smallsat" in query_lower:
        related_topics = [
            "small satellite missions",
            "university satellite programs",
            "low-cost space systems"
        ]
    if "power" in query_lower:
        related_topics.extend(["solar array", "battery management", "EPS"])
    if "radio" in query_lower or "communication" in query_lower:
        related_topics.extend(["UHF communication", "amateur radio", "S-band"])
    if "attitude" in query_lower or "adcs" in query_lower:
        related_topics.extend(["magnetorquer", "reaction wheel", "star tracker"])

    return {
        "query": query,
        "search_url": f"https://ntrs.nasa.gov/search?q={query_encoded}",
        "api_url": f"https://ntrs.nasa.gov/api/citations/search?q={query_encoded}",
        "related_topics": list(set(related_topics))[:5],
        "notes": "NASA Technical Reports Server contains mission reports, design documents, and lessons learned",
        "hint": "Try adding 'lessons learned' or 'design' to find practical implementation guides"
    }


async def search_arxiv_papers(
    query: str,
    category: str = "astro-ph.IM",  # Instrumentation and Methods
    limit: int = 10
) -> dict:
    """
    Search arXiv for academic papers.

    Provides search URL for arXiv's physics and engineering papers.

    Args:
        query: Search query
        category: arXiv category (astro-ph.IM, astro-ph.EP, physics.ins-det, cs.SY)
        limit: Maximum results

    Returns:
        Search URL and relevant categories
    """
    query_encoded = query.replace(" ", "+")

    # Relevant arXiv categories for space systems
    relevant_categories = {
        "astro-ph.IM": "Instrumentation and Methods for Astrophysics",
        "astro-ph.EP": "Earth and Planetary Astrophysics",
        "physics.ins-det": "Instrumentation and Detectors",
        "physics.space-ph": "Space Physics",
        "cs.SY": "Systems and Control",
        "cs.RO": "Robotics (for autonomous systems)",
        "eess.SP": "Signal Processing"
    }

    return {
        "query": query,
        "search_url": f"https://arxiv.org/search/?query={query_encoded}&searchtype=all",
        "category_search": f"https://arxiv.org/search/?query={query_encoded}&searchtype=all&source=header&cat={category}",
        "relevant_categories": relevant_categories,
        "api_url": f"http://export.arxiv.org/api/query?search_query=all:{query_encoded}&max_results={limit}",
        "hint": "Use category 'astro-ph.IM' for instrument design, 'cs.SY' for control systems"
    }


# ============================================
# STANDARDS LOOKUP
# ============================================

async def lookup_space_standards(
    topic: str
) -> dict:
    """
    Find relevant space industry standards for a topic.

    Args:
        topic: Topic to search (e.g., "telemetry", "testing", "components")

    Returns:
        Relevant standards from CCSDS, ECSS, and CubeSat spec
    """
    topic_lower = topic.lower()
    relevant_standards = []

    for std_org, std_info in STANDARDS.items():
        org_standards = []
        for doc in std_info["key_docs"]:
            if topic_lower in doc["topic"] or topic_lower in doc["title"].lower():
                org_standards.append(doc)

        if org_standards:
            relevant_standards.append({
                "organization": std_info["name"],
                "url": std_info["url"],
                "documents": org_standards
            })

    # Add general search hints
    search_hints = {
        "telemetry": "CCSDS 133.0-B (Space Packet) and ECSS-E-ST-70-41C (PUS) are key references",
        "command": "CCSDS 232.0-B for telecommand protocol",
        "testing": "CubeSat Design Specification Appendix A for environmental test requirements",
        "mechanical": "CubeSat Design Specification Rev 14 for form factor requirements",
        "radiation": "ECSS-Q-ST-60C for EEE component requirements"
    }

    hint = search_hints.get(topic_lower, "Check CCSDS for data protocols, ECSS for European standards, CDS for CubeSat mechanical specs")

    return {
        "topic": topic,
        "standards": relevant_standards,
        "all_organizations": {k: v["url"] for k, v in STANDARDS.items()},
        "hint": hint
    }


# ============================================
# WEB SEARCH (Generic)
# ============================================

async def web_search_suggestions(
    query: str,
    context: str = "cubesat"
) -> dict:
    """
    Generate optimized web search queries for finding space component info.

    Instead of hitting an API, this provides optimized search queries
    that the user (or an AI with web access) can use.

    Args:
        query: What to search for
        context: Context hint (cubesat, fprime, aerospace)

    Returns:
        Optimized search queries for different purposes
    """
    base_query = query.strip()

    search_queries = {
        "general": f"{base_query} site:*.edu OR site:*.gov OR site:*.org",
        "datasheets": f"{base_query} datasheet filetype:pdf",
        "application_notes": f"{base_query} application note OR app note filetype:pdf",
        "github": f"{base_query} site:github.com",
        "cubesat_forums": f"{base_query} site:reddit.com/r/cubesat OR site:reddit.com/r/space OR site:forum.nasaspaceflight.com",
        "manufacturers": f"{base_query} CubeSat supplier OR vendor OR manufacturer",
        "alternatives": f"{base_query} alternative OR equivalent OR replacement component",
        "space_qualified": f"{base_query} space qualified OR rad-hard OR radiation tolerant"
    }

    # Add context-specific searches
    if "fprime" in context.lower():
        search_queries["fprime"] = f"{base_query} site:github.com/nasa/fprime OR site:nasa.github.io/fprime"

    if "cubesat" in context.lower():
        search_queries["cubesat_missions"] = f"{base_query} CubeSat mission OR university satellite"

    return {
        "query": query,
        "context": context,
        "optimized_searches": search_queries,
        "google_search": f"https://www.google.com/search?q={query.replace(' ', '+')}",
        "hint": "Use 'datasheets' query for component docs, 'alternatives' to find equivalent parts"
    }


# ============================================
# ALTERNATIVE COMPONENT FINDER
# ============================================

async def find_alternative_components(
    component: str,
    specs: Optional[dict] = None
) -> dict:
    """
    Suggest alternative/equivalent components.

    Based on known component equivalents in the aerospace industry.

    Args:
        component: Component name or part number
        specs: Optional specs to match (interface, voltage, etc.)

    Returns:
        Known alternatives and search suggestions
    """
    # Known equivalents database
    equivalents = {
        "ms5611": {
            "description": "Barometric pressure sensor",
            "interface": "I2C/SPI",
            "alternatives": [
                {"part": "BMP390", "manufacturer": "Bosch", "notes": "Lower noise, I2C/SPI"},
                {"part": "LPS22HB", "manufacturer": "ST", "notes": "Lower power, I2C/SPI"},
                {"part": "DPS310", "manufacturer": "Infineon", "notes": "High precision"}
            ]
        },
        "bno085": {
            "description": "9-DOF IMU with sensor fusion",
            "interface": "I2C/SPI/UART",
            "alternatives": [
                {"part": "BNO055", "manufacturer": "Bosch", "notes": "Older, widely available"},
                {"part": "ICM-42688-P", "manufacturer": "TDK/InvenSense", "notes": "No fusion, raw data"},
                {"part": "LSM6DSO32", "manufacturer": "ST", "notes": "6-DOF only, add magnetometer"}
            ]
        },
        "sx1262": {
            "description": "LoRa transceiver",
            "interface": "SPI",
            "alternatives": [
                {"part": "SX1276/77/78", "manufacturer": "Semtech", "notes": "Older generation"},
                {"part": "LLCC68", "manufacturer": "Semtech", "notes": "Lower cost variant"},
                {"part": "RFM95W", "manufacturer": "HopeRF", "notes": "Module with SX1276"}
            ]
        },
        "max-m10s": {
            "description": "GPS/GNSS module",
            "interface": "UART/I2C",
            "alternatives": [
                {"part": "SAM-M10Q", "manufacturer": "u-blox", "notes": "Integrated antenna"},
                {"part": "NEO-M9N", "manufacturer": "u-blox", "notes": "Multi-constellation"},
                {"part": "L86", "manufacturer": "Quectel", "notes": "Lower cost option"}
            ]
        }
    }

    component_lower = component.lower().replace("-", "").replace("_", "").replace(" ", "")

    for key, info in equivalents.items():
        key_normalized = key.replace("-", "").replace("_", "")
        if key_normalized in component_lower or component_lower in key_normalized:
            return {
                "component": component,
                "found": True,
                **info,
                "search_suggestion": f"Search '{component} alternative equivalent' for more options"
            }

    # Not found - provide search suggestions
    return {
        "component": component,
        "found": False,
        "suggestion": "Component not in equivalents database",
        "search_queries": {
            "alternatives": f"{component} alternative equivalent replacement",
            "parametric": f"{component} specifications datasheet",
            "forums": f"{component} vs site:reddit.com OR site:eevblog.com"
        },
        "hint": "Try searching for the component's key specs (voltage, interface, package) to find alternatives"
    }
