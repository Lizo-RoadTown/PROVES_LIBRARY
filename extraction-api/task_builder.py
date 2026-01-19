"""
Task Builder - Builds FRAMES-aware extraction prompts.

This module extracts the prompt-building logic from process_extractions_v3.py
so it can be reused by the API, worker, and different processors.

The key insight from V3: Context hints from find_good_urls.py make extractions
significantly better by priming the extractor with component/interface names.

Usage:
    from task_builder import build_extraction_task

    task = build_extraction_task(
        url="https://docs.example.com/page",
        context={
            "components": ["I2CDriver", "PowerMonitor"],
            "interfaces": ["TlmChan", "CmdDisp"],
            "keywords": ["telemetry", "command"],
            "summary": "Driver documentation for I2C bus"
        },
        source_type="web"
    )
"""

from typing import Dict, List, Optional


# =============================================================================
# FRAMES METHODOLOGY - Core extraction focus areas
# =============================================================================

FRAMES_EXTRACTION_FOCUS = """
EXTRACTION FOCUS (use FRAMES methodology):
- COMPONENTS: What modules/units exist? (hardware, software, subsystems)
- INTERFACES: Where do they connect? (ports, buses, protocols, picolocks)
- FLOWS: What moves through connections? (data, commands, power, signals)
- MECHANISMS: What maintains interfaces? (documentation, schemas, drivers)
- DEPENDENCIES: Component-to-component relationships
- CONFIGURATION: Parameters, settings, modes
- SAFETY CONSTRAINTS: Critical requirements, inhibit schemes, failure modes

For EACH extraction, answer 4 FRAMES questions:
1. What flows through? (data, power, decisions)
2. What happens if it stops? (failure mode)
3. What maintains it? (driver, process, documentation)
4. Coupling strength? (0.0-1.0 based on constraints)

Extraction threshold: Must answer at least 2 of 4 questions with evidence.

Coupling strength rubric:
- 0.9-1.0: Hard constraints (must, within Xms, safety-critical)
- 0.6-0.8: Explicit dependency (degraded mode possible)
- 0.3-0.5: Optional (may, can, if available)
- 0.0-0.2: Weak (only coexistence mentioned)
"""

# =============================================================================
# EPISTEMIC DEFAULTS/OVERRIDES PATTERN
# =============================================================================

KNOWLEDGE_CAPTURE_CHECKLIST = """
7-QUESTION KNOWLEDGE CAPTURE CHECKLIST (REQUIRED for ALL extractions):

Question 1: Who knew this, and how close were they? (Observer coupling)
   CRITICAL: You (the AI) are the RECORDER, not the attributed OBSERVER.
   - observer_id: WHO claimed to know this (NOT "agent:extractor"!)
     Options: "designers" | "authors" | "maintainers" | "system" | "unknown"
   - observer_type: "human" | "system" | "instrument" | "unknown" (NEVER "ai")
   - contact_mode: How the ATTRIBUTED observer knew this
     "direct" (physical) | "mediated" (instrumented) | "effect_only" (indirect) | "derived" (docs-only)
   - contact_strength: How close the attributed observer was (0.00-1.00)
     1.0 = direct physical, 0.2 = derived from docs (default for unknown)
   - signal_type: "text" | "code" | "spec" | "comment" | "example" | "log" | "telemetry" | "diagram" | "model" | "table" | "test"

Question 2: Where does the experience live now? (Pattern storage)
   - pattern_storage: "internalized" (in body/nervous system) | "externalized" (in symbols/docs) | "mixed" | "unknown"
   - representation_media: ["text"] | ["code"] | ["text", "diagram"] etc.

Question 3: What has to stay connected for this to work? (Relational integrity)
   - dependencies: JSON array of entity keys that must remain connected
     e.g., ["component:I2C_Driver", "component:PowerMonitor"]
   - sequence_role: "precondition" | "step" | "outcome" | "postcondition" | "none"

Question 4: Under what conditions was this true? (Context preservation)
   - validity_conditions: JSON object e.g., {"fprime_version": "v3.4.0", "hardware_rev": "2.1"}
   - assumptions: Array of strings e.g., ["Normal temperature", "Standard config"]
   - scope: "local" | "subsystem" | "system" | "general"

Question 5: When does this stop being reliable? (Temporal validity)
   - observed_at: Timestamp when source was created
   - valid_from, valid_to: Validity range if known
   - refresh_trigger: "new_rev" | "recalibration" | "periodic" | "after_incident" | null
   - staleness_risk: 0.00-1.00 (0.0 = timeless, 1.0 = highly time-sensitive)

Question 6: Who wrote or taught this, and why? (Authorship & intent)
   - author_id: "doc:fprime_team" | "human:engineer_x" | "agent:parser_v1"
   - intent: "explain" | "instruct" | "justify" | "explore" | "comply" | "persuade" | "remember" | "unknown"
   - uncertainty_notes: What uncertainty was present but not recorded?

Question 7: Does this only work if someone keeps doing it? (Reenactment dependency)
   - reenactment_required: TRUE/FALSE
   - practice_interval: "per-run" | "weekly" | "per-release" | null
   - skill_transferability: "portable" | "conditional" | "local" | "tacit_like" | "unknown"
"""

EPISTEMIC_PATTERN = """
EPISTEMIC DEFAULTS/OVERRIDES PATTERN (anti-boilerplate):

1. Output ONE epistemic_defaults object at the start (for the entire page):
   {
     "observer_id": "unknown",
     "observer_type": "unknown",
     "contact_mode": "derived",
     "contact_strength": 0.20,
     "signal_type": "text",
     "pattern_storage": "externalized",
     "representation_media": ["text"],
     "scope": "subsystem",
     "staleness_risk": 0.20,
     "intent": "instruct",
     "reenactment_required": false,
     "skill_transferability": "portable"
   }

2. For each candidate, output epistemic_overrides (empty {} if all defaults apply):
   - Only include fields that DIFFER from the defaults
   - Example: {"signal_type": "code", "contact_strength": 0.85}

Valid epistemic keys (7-question checklist):
   Q1 (Observer): observer_id, observer_type, contact_mode, contact_strength, signal_type
   Q2 (Storage): pattern_storage, representation_media
   Q3 (Dependencies): dependencies, sequence_role
   Q4 (Context): validity_conditions, assumptions, scope
   Q5 (Temporality): observed_at, valid_from, valid_to, refresh_trigger, staleness_risk
   Q6 (Authorship): author_id, intent, uncertainty_notes
   Q7 (Reenactment): reenactment_required, practice_interval, skill_transferability
"""

# =============================================================================
# CANDIDATE TYPE ENUMS
# =============================================================================

CANDIDATE_TYPE_GUIDANCE = """
STRICT ENUMS - candidate_type (ONLY use these):
- 'dependency' - for ANY coupling between components (digital, physical, organizational)
- 'connection' - for interface/port-level links
- 'component' - for modules/units
- 'port' - for interface points
- 'command', 'telemetry', 'event', 'parameter', 'data_type', 'inheritance'

FORBIDDEN: Do NOT invent types like "coupling", "organizational_coupling", etc.
ALL FRAMES couplings (digital/physical/organizational) → use 'dependency'

STRICT ENUMS - evidence_type (ONLY use these):
- 'explicit_requirement' - "System shall/must..." statements
- 'safety_constraint' - Safety-critical requirements, failure modes
- 'performance_constraint' - Timing (within Xms), resource limits
- 'feature_description' - Functional capabilities
- 'interface_specification' - Port/API contracts, protocols
- 'behavioral_contract' - State machines, event sequences
- 'example_usage' - Code examples, usage patterns
- 'design_rationale' - Why decisions made
- 'dependency_declaration' - Explicit "depends on", "requires"
- 'configuration_parameter' - Settings, modes, parameters
- 'inferred' - Derived from context
"""

# =============================================================================
# SOURCE-SPECIFIC PREAMBLES
# =============================================================================

SOURCE_PREAMBLES = {
    "web": "Extract architecture from this documentation page.",
    "discord": "Extract architecture knowledge from this Discord conversation. Focus on decisions, rationales, and lessons learned that are often lost in chat history.",
    "notion": "Extract architecture from this Notion document. Pay attention to linked databases and nested pages.",
    "github": "Extract architecture from this GitHub content. Focus on code comments, README files, and design documents.",
    "google_doc": "Extract architecture from this Google Doc. Focus on design decisions and specifications.",
    "google_sheet": "Extract architecture from this spreadsheet. Look for configuration tables and dependency matrices.",
}

# =============================================================================
# TASK BUILDER FUNCTIONS
# =============================================================================

def build_context_section(context: Dict) -> str:
    """
    Build context hints section from find_good_urls.py data.

    This is the KEY VALUE of the smart crawler - it primes the extractor
    with component and interface names so it knows what to look for.
    """
    context_hints = []

    components = context.get("components", [])
    interfaces = context.get("interfaces", [])
    keywords = context.get("keywords", [])
    summary = context.get("summary", "")

    if components:
        context_hints.append(f"- Look for these components: {', '.join(components[:10])}")

    if interfaces:
        context_hints.append(f"- Look for these interfaces/ports: {', '.join(interfaces[:10])}")

    if keywords:
        context_hints.append(f"- Key topics: {', '.join(keywords)}")

    if summary:
        context_hints.append(f"- Page summary: {summary[:200]}")

    if context_hints:
        return "\n".join(context_hints)
    else:
        return "- Scan entire page for architecture elements"


def build_extraction_task(
    url: str,
    context: Optional[Dict] = None,
    source_type: str = "web",
    team_id: Optional[str] = None,
    source_id: Optional[str] = None,
) -> str:
    """
    Build a FRAMES-aware extraction task prompt.

    This is the core function that replaces the dumbed-down 15-line prompt
    in extraction-api/app.py with the full V3 methodology.

    Args:
        url: The URL or resource identifier to extract from
        context: Optional dict with components, interfaces, keywords, summary
                 (from find_good_urls.py or similar pre-scan)
        source_type: One of "web", "discord", "notion", "github", "google_doc", "google_sheet"
        team_id: Optional team ID for multi-tenant tracking
        source_id: Optional source ID linking to team_sources table

    Returns:
        Full task prompt string for the curator agent
    """
    # Get source-specific preamble
    preamble = SOURCE_PREAMBLES.get(source_type, SOURCE_PREAMBLES["web"])

    # Build context section
    context_section = build_context_section(context or {})

    # Build team context if provided
    team_context = ""
    if team_id:
        team_context = f"\nTeam ID: {team_id}"
    if source_id:
        team_context += f"\nSource ID: {source_id}"

    task = f"""You are the curator agent for the PROVES Library.

YOUR MISSION: {preamble}

URL: {url}{team_context}

CONTEXT HINTS (from pre-scan):
{context_section}

{FRAMES_EXTRACTION_FOCUS}

{CANDIDATE_TYPE_GUIDANCE}

For EACH extraction:
- Provide exact evidence quotes from source
- Document confidence reasoning
- Identify relationships to other components
- CITE THE SOURCE URL
- Answer ALL 7 Knowledge Capture Checklist questions

{KNOWLEDGE_CAPTURE_CHECKLIST}

{EPISTEMIC_PATTERN}

Then store ALL extractions in staging_extractions. Work autonomously - no approval needed.
"""

    return task


def build_discord_task(
    channel_id: str,
    thread_id: Optional[str] = None,
    context: Optional[Dict] = None,
    team_id: Optional[str] = None,
    source_id: Optional[str] = None,
) -> str:
    """
    Build extraction task for Discord content.

    Discord conversations often contain valuable decision rationales,
    lessons learned, and informal knowledge that never makes it to docs.
    """
    resource_id = f"discord://{channel_id}"
    if thread_id:
        resource_id += f"/thread/{thread_id}"

    # Discord-specific context additions
    discord_context = context or {}
    if "keywords" not in discord_context:
        discord_context["keywords"] = ["decision", "why", "because", "learned", "mistake", "worked", "failed"]

    return build_extraction_task(
        url=resource_id,
        context=discord_context,
        source_type="discord",
        team_id=team_id,
        source_id=source_id,
    )


def build_notion_task(
    page_id: str,
    context: Optional[Dict] = None,
    team_id: Optional[str] = None,
    source_id: Optional[str] = None,
) -> str:
    """
    Build extraction task for Notion pages.
    """
    return build_extraction_task(
        url=f"notion://{page_id}",
        context=context,
        source_type="notion",
        team_id=team_id,
        source_id=source_id,
    )


def build_github_task(
    owner: str,
    repo: str,
    path: str,
    branch: str = "main",
    context: Optional[Dict] = None,
    team_id: Optional[str] = None,
    source_id: Optional[str] = None,
) -> str:
    """
    Build extraction task for GitHub files.
    """
    return build_extraction_task(
        url=f"github://{owner}/{repo}/{branch}/{path}",
        context=context,
        source_type="github",
        team_id=team_id,
        source_id=source_id,
    )


# =============================================================================
# BATCH TASK BUILDER
# =============================================================================

def build_batch_tasks(
    urls: List[str],
    contexts: Optional[List[Dict]] = None,
    source_type: str = "web",
    team_id: Optional[str] = None,
    source_id: Optional[str] = None,
) -> List[Dict]:
    """
    Build tasks for a batch of URLs.

    Returns list of dicts with {url, task} for each URL.
    """
    if contexts is None:
        contexts = [{}] * len(urls)

    if len(contexts) != len(urls):
        raise ValueError(f"contexts length ({len(contexts)}) must match urls length ({len(urls)})")

    return [
        {
            "url": url,
            "task": build_extraction_task(
                url=url,
                context=ctx,
                source_type=source_type,
                team_id=team_id,
                source_id=source_id,
            )
        }
        for url, ctx in zip(urls, contexts)
    ]
