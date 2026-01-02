"""
Extractor Sub-Agent (BACKUP VERSION for Testing Refactors)

This is a COPY of production/curator/subagents/extractor.py
Used for testing refactors in isolation from production.

Specialized agent for mapping system architecture using FRAMES methodology.

FRAMES = Framework for Resilience Assessment in Modular Engineering Systems

This agent extracts:
- COMPONENTS (modules): Semi-autonomous units with boundaries
- INTERFACES: Connection points where components touch
- FLOWS: What moves through interfaces (data, commands, power, signals)
- MECHANISMS: What maintains the interfaces (docs, schemas, drivers)

Does NOT assign criticality - that's human judgment after verification.

Supports:
- Web page fetching (docs sites)
- GitHub file fetching (source repos)

All fetched content is stored in raw_snapshots for auditability.
"""
import os
import re
import hashlib
import uuid
from datetime import datetime
import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langsmith import traceable


@tool
def get_ontology() -> str:
    """
    Get the full FRAMES ontology reference document.

    Use this tool if you need to check:
    - Complete 4-question methodology details
    - Coupling strength calibration examples
    - Layer-specific if-stops examples
    - Extraction output format specifications

    Most extractions won't need this - the core principles in your system prompt
    are usually sufficient. Only call this if you need the full reference.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    ontology_path = os.path.join(project_root, 'ONTOLOGY.md')

    try:
        with open(ontology_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        # Fallback if ontology not found
        return """## FRAMES Core Vocabulary
- COMPONENTS: What units exist (modules)
- INTERFACES: Where they connect (ports, buses)
- FLOWS: What moves through (data, commands, power)
- MECHANISMS: What maintains connections (docs, schemas)

Do NOT assign criticality - humans do that after verification."""


def get_db_connection():
    """Get a database connection from environment."""
    import psycopg
    from dotenv import load_dotenv

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    load_dotenv(os.path.join(project_root, '.env'))

    db_url = os.environ.get('NEON_DATABASE_URL')
    if not db_url:
        raise ValueError("NEON_DATABASE_URL not set")
    return psycopg.connect(db_url)


def get_or_create_pipeline_run(conn, run_name: str = "curator_extraction") -> str:
    """Get or create a pipeline run for tracking. Returns run_id."""
    import json
    with conn.cursor() as cur:
        # Check for existing active run
        cur.execute("""
            SELECT id FROM pipeline_runs
            WHERE run_name = %s AND score_status = 'pending'
            ORDER BY created_at DESC LIMIT 1
        """, (run_name,))
        existing = cur.fetchone()
        if existing:
            return str(existing[0])

        # Create new run
        cur.execute("""
            INSERT INTO pipeline_runs (run_name, run_type, triggered_by)
            VALUES (%s, 'extraction', 'extractor_agent')
            RETURNING id
        """, (run_name,))
        return str(cur.fetchone()[0])


# create_lineage_data() REMOVED - lineage is computed deterministically by storage.py
# This ensures single-source-of-truth for lineage computation with:
# - Exact UTF-8 byte matching
# - Normalization fallback
# - Confidence tiers
# - Persisted verification metadata


def store_raw_snapshot(source_url: str, source_type: str, ecosystem: str, content: str, content_hash: str) -> str:
    """Store raw content in raw_snapshots table. Returns snapshot_id."""
    import json
    try:
        conn = get_db_connection()

        with conn.cursor() as cur:
            # Check if we already have this exact content
            cur.execute("""
                SELECT id FROM raw_snapshots
                WHERE content_hash = %s AND status = 'captured'::snapshot_status
            """, (content_hash,))
            existing = cur.fetchone()

            if existing:
                conn.close()
                return str(existing[0])  # Return existing snapshot ID

            # Get or create pipeline run
            run_id = get_or_create_pipeline_run(conn)

            # Store content as JSONB payload
            payload = json.dumps({"content": content, "format": "text"})

            # Insert new snapshot
            cur.execute("""
                INSERT INTO raw_snapshots (
                    source_url, source_type, ecosystem,
                    content_hash, payload, payload_size_bytes,
                    captured_by_run_id, status
                ) VALUES (
                    %s, %s::source_type, %s::ecosystem_type,
                    %s, %s::jsonb, %s,
                    %s::uuid, 'captured'::snapshot_status
                )
                RETURNING id
            """, (
                source_url, source_type, ecosystem,
                content_hash, payload, len(content.encode('utf-8')),
                run_id
            ))
            snapshot_id = cur.fetchone()[0]
        conn.commit()
        conn.close()
        return str(snapshot_id)
    except Exception as e:
        return f"ERROR: {str(e)}"


@tool
def read_document(doc_path: str) -> str:
    """Read and return the contents of a local documentation file.

    Content is stored in raw_snapshots for auditability.
    """
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        chars = len(content)

        # Store in raw_snapshots
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        snapshot_id = store_raw_snapshot(
            source_url=f"file://{doc_path}",
            source_type="local_file",
            ecosystem="unknown",  # Will be classified during extraction
            content=content,
            content_hash=content_hash
        )

        # Return full content up to 50K chars (enough for most docs)
        max_chars = 50000
        if chars > max_chars:
            content = content[:max_chars] + f"\n\n... (truncated, showing first {max_chars} of {chars} characters)"

        return f"Document: {doc_path}\nSnapshot ID: {snapshot_id}\nSize: {chars} characters, {len(lines)} lines\n\nFull Content:\n{content}"
    except Exception as e:
        return f"Error reading document: {str(e)}"


@tool
def fetch_webpage(url: str) -> str:
    """
    Fetch content from a documentation webpage.

    Use this to read F' or ProvesKit documentation:
    - https://nasa.github.io/fprime/...
    - https://docs.proveskit.space/...
    - https://fprime.jpl.nasa.gov/...

    Content is stored in raw_snapshots for auditability.
    Returns the page content with the source URL for citation.
    """
    try:
        headers = {
            "User-Agent": "PROVES-Library-Curator/1.0 (knowledge extraction for CubeSat safety)"
        }

        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()

        content = response.text
        chars = len(content)

        # Detect ecosystem from URL
        ecosystem = "unknown"
        if "fprime" in url.lower() or "nasa.github.io" in url.lower():
            ecosystem = "fprime"
        elif "proveskit" in url.lower():
            ecosystem = "proveskit"
        elif "pysquared" in url.lower():
            ecosystem = "pysquared"

        # Store raw HTML in raw_snapshots
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        snapshot_id = store_raw_snapshot(
            source_url=url,
            source_type="docs_webpage",
            ecosystem=ecosystem,
            content=content,
            content_hash=content_hash
        )

        # Strip HTML tags for cleaner extraction (basic approach)
        text_content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
        text_content = re.sub(r'<style[^>]*>.*?</style>', '', text_content, flags=re.DOTALL)
        text_content = re.sub(r'<[^>]+>', ' ', text_content)
        text_content = re.sub(r'\s+', ' ', text_content).strip()

        max_chars = 50000
        if len(text_content) > max_chars:
            text_content = text_content[:max_chars] + f"\n\n... (truncated, showing first {max_chars} of {len(text_content)} characters)"

        return f"Source URL: {url}\nSnapshot ID: {snapshot_id}\nSize: {chars} characters\n\nContent:\n{text_content}"
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"


@tool
def fetch_github_file(owner: str, repo: str, path: str, branch: str = "main") -> str:
    """
    Fetch a file directly from a GitHub repository without cloning.

    Content is stored in raw_snapshots for auditability.

    Examples:
    - fetch_github_file("nasa", "fprime", "Svc/CmdDispatcher/CmdDispatcher.fpp")
    - fetch_github_file("proveskit", "flight-software", "Components/I2CManager/I2CManager.fpp")

    Args:
        owner: GitHub organization or user (e.g., "nasa", "proveskit")
        repo: Repository name (e.g., "fprime", "flight-software")
        path: Path to file within repo (e.g., "Svc/CmdDispatcher/CmdDispatcher.fpp")
        branch: Branch name (default: "main", use "devel" for fprime)

    Returns the file content with full GitHub URL for citation.
    """
    try:
        # Use raw.githubusercontent.com for direct file access
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
        github_url = f"https://github.com/{owner}/{repo}/blob/{branch}/{path}"

        headers = {
            "User-Agent": "PROVES-Library-Curator/1.0"
        }

        # Add GitHub token if available for higher rate limits
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"token {github_token}"

        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(raw_url, headers=headers)
            response.raise_for_status()

        content = response.text
        chars = len(content)
        lines = content.count('\n') + 1

        # Detect ecosystem from repo
        ecosystem = "unknown"
        if owner.lower() == "nasa" and repo.lower() == "fprime":
            ecosystem = "fprime"
        elif "proveskit" in owner.lower() or "proveskit" in repo.lower():
            ecosystem = "proveskit"
        elif "pysquared" in repo.lower():
            ecosystem = "pysquared"

        # Store in raw_snapshots
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        snapshot_id = store_raw_snapshot(
            source_url=github_url,
            source_type="github_file",
            ecosystem=ecosystem,
            content=content,
            content_hash=content_hash
        )

        max_chars = 50000
        if chars > max_chars:
            content = content[:max_chars] + f"\n\n... (truncated, showing first {max_chars} of {chars} characters)"

        return f"Source: {github_url}\nSnapshot ID: {snapshot_id}\nRepository: {owner}/{repo}\nPath: {path}\nBranch: {branch}\nSize: {chars} characters, {lines} lines\n\nContent:\n{content}"
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"File not found: {owner}/{repo}/{path} on branch {branch}. Check the path and branch name."
        return f"HTTP error fetching {owner}/{repo}/{path}: {e.response.status_code}"
    except Exception as e:
        return f"Error fetching {owner}/{repo}/{path}: {str(e)}"


@tool
def list_github_directory(owner: str, repo: str, path: str = "", branch: str = "main") -> str:
    """
    List files and directories in a GitHub repository path.

    Use this to explore repository structure before fetching specific files.

    Examples:
    - list_github_directory("nasa", "fprime", "Svc") - List all service components
    - list_github_directory("nasa", "fprime", "Drv") - List all driver components
    - list_github_directory("proveskit", "flight-software", "Components")

    Args:
        owner: GitHub organization or user
        repo: Repository name
        path: Directory path (empty for root)
        branch: Branch name

    Returns list of files and directories with their types.
    """
    try:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        if branch != "main":
            api_url += f"?ref={branch}"

        headers = {
            "User-Agent": "PROVES-Library-Curator/1.0",
            "Accept": "application/vnd.github.v3+json"
        }

        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"token {github_token}"

        with httpx.Client(timeout=30.0) as client:
            response = client.get(api_url, headers=headers)
            response.raise_for_status()

        items = response.json()

        if not isinstance(items, list):
            return f"Path is a file, not a directory: {path}"

        dirs = []
        files = []

        for item in items:
            name = item.get("name", "")
            item_type = item.get("type", "")
            if item_type == "dir":
                dirs.append(f"📁 {name}/")
            else:
                size = item.get("size", 0)
                files.append(f"📄 {name} ({size} bytes)")

        result = f"Directory: {owner}/{repo}/{path}\nBranch: {branch}\n\n"

        if dirs:
            result += "Directories:\n" + "\n".join(sorted(dirs)) + "\n\n"
        if files:
            result += "Files:\n" + "\n".join(sorted(files))

        if not dirs and not files:
            result += "(empty directory)"

        return result
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"Path not found: {owner}/{repo}/{path}"
        if e.response.status_code == 403:
            return f"Rate limited. Set GITHUB_TOKEN environment variable for higher limits."
        return f"HTTP error: {e.response.status_code}"
    except Exception as e:
        return f"Error listing {owner}/{repo}/{path}: {str(e)}"


@tool
def extract_architecture_using_claude(text: str, document_name: str) -> str:
    """
    Extract system architecture from text using FRAMES methodology.

    Maps the structural elements:
    - COMPONENTS: Semi-autonomous units (modules) with boundaries
    - INTERFACES: Where components connect (ports, buses, protocols)
    - FLOWS: What moves through interfaces (data, commands, power, signals)
    - MECHANISMS: What maintains interfaces (documentation, schemas, drivers)

    NOTE: Do NOT assess criticality - that's metadata assigned by HUMANS after verification.
    Criticality is about MISSION IMPACT which requires human judgment.
    """
    from langchain_anthropic import ChatAnthropic

    try:
        # Extract snapshot_id from the text if present (from fetch_webpage output)
        import re
        snapshot_id_match = re.search(r'Snapshot ID: ([a-f0-9\-]+)', text)
        snapshot_id = snapshot_id_match.group(1) if snapshot_id_match else None

        model = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            temperature=0,
        )

        extraction_prompt = f"""## YOUR MISSION: Reduce Ambiguity for Human Verifier

You are preparing architecture data for HUMAN VERIFICATION using FRAMES methodology.

**FRAMES = Framework for Resilience Assessment in Modular Engineering Systems**

Extract COUPLINGS (not just components). For EVERY coupling, answer 4 questions:
1. What flows through? (data, power, decisions)
2. What happens if it stops? (failure mode)
3. What maintains it? (driver, process, documentation)
4. Coupling strength? (0.0-1.0 based on constraints)

**Extraction threshold:** Must answer at least 2 of 4 questions with evidence.

**Coupling strength rubric:**
- 0.9-1.0: Hard constraints (must, within Xms, safety-critical)
- 0.6-0.8: Explicit dependency (degraded mode possible)
- 0.3-0.5: Optional (may, can, if available)
- 0.0-0.2: Weak (only coexistence mentioned)

**Layers:** digital (software), physical (hardware), organizational (people/teams)

**Reduce Ambiguity:**
- Cite exact sources (they need to verify your quotes)
- Compare against verified examples (they need to see your logic)
- Document what you're confident about and WHY
- Explain any uncertainties

---

## DOCUMENT TO ANALYZE

Document: {document_name}

Text:
{text}

---

## YOUR TASK: Extract with Context for Human Review

Extract ALL structural elements you find. For EACH extraction, help the human verify by providing:

### COMPONENTS FOUND
For each component (module, unit, subsystem):
```
Component: <name>
Type: software | hardware | subsystem | driver | library
Boundary: <what's inside this component>
Confidence: HIGH | MEDIUM | LOW (how clearly documented)
Source: <line numbers or section>
```

### INTERFACES FOUND
For each connection point between components:
```
Interface: <name or description>
Connects: <Component A> ↔ <Component B>
Type: I2C | SPI | UART | USB | power | command | telemetry | API | function_call
Direction: bidirectional | A->B | B->A
Confidence: HIGH | MEDIUM | LOW
Source: <line numbers or section>
```

### FLOWS FOUND
For each thing that moves through an interface:
```
Flow: <what moves>
Through: <interface name>
Type: data | command | power | signal | configuration
If-Stops: <what breaks if this flow ceases>
Confidence: HIGH | MEDIUM | LOW
Source: <line numbers or section>
```

### MECHANISMS FOUND
For each thing that maintains an interface:
```
Mechanism: <name>
Maintains: <interface name>
Type: documentation | schema | driver | protocol | handler
Location: <where to find it>
Confidence: HIGH | MEDIUM | LOW
```

---

## REMEMBER

- Capture EVERYTHING, not just what seems important
- Note Confidence (documentation clarity), NOT Criticality (mission impact)
- Humans will decide what's critical AFTER reviewing your extraction
- Include source references (line numbers, sections) for traceability
"""

        response = model.invoke(extraction_prompt)

        # Include snapshot_id in the output for storage agent
        result = f"Architecture Extraction Results:\n\n{response.content}"
        if snapshot_id:
            result += f"\n\n---\nSnapshot ID: {snapshot_id}\nSource: {document_name}"

        return result

    except Exception as e:
        return f"Error during extraction: {str(e)}"


# ============================================================================
# LONG-TERM MEMORY TOOLS - Agents learn from feedback
# ============================================================================

@tool
def observe_staging_feedback(days_back: int = 7, limit: int = 50) -> str:
    """
    Observe recent human verification decisions to learn extraction patterns.

    Returns accepted and rejected extractions from the last N days.
    Use this to identify what humans value vs what they reject.

    Update /memories/extraction_patterns.txt with learned patterns.

    Args:
        days_back: How many days of feedback to observe (default: 7)
        limit: Maximum number of extractions to review (default: 50)

    Returns:
        Summary of accepted/rejected patterns with examples
    """
    try:
        import psycopg
        from dotenv import load_dotenv
        import os

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
        load_dotenv(os.path.join(project_root, '.env'))

        db_url = os.environ.get('NEON_DATABASE_URL')
        conn = psycopg.connect(db_url)

        query = """
            SELECT
                candidate_type::text,
                candidate_key,
                candidate_payload,
                evidence,
                confidence_score,
                status::text,
                created_at
            FROM staging_extractions
            WHERE status IN ('accepted', 'rejected')
              AND created_at > NOW() - INTERVAL '%s days'
            ORDER BY created_at DESC
            LIMIT %s
        """

        with conn.cursor() as cur:
            cur.execute(query, (days_back, limit))
            rows = cur.fetchall()

        conn.close()

        if not rows:
            return f"No feedback found in the last {days_back} days. Humans haven't verified any extractions yet."

        # Analyze patterns
        accepted = [r for r in rows if r[5] == 'accepted']
        rejected = [r for r in rows if r[5] == 'rejected']

        result = f"=== STAGING FEEDBACK ({len(rows)} extractions reviewed) ===\n\n"
        result += f"Accepted: {len(accepted)} | Rejected: {len(rejected)}\n\n"

        # Summarize accepted patterns
        if accepted:
            result += "ACCEPTED PATTERNS:\n"
            for ctype, ckey, payload, evidence, conf, status, created in accepted[:10]:
                result += f"\n[OK] {ctype}: {ckey}\n"
                result += f"  Confidence: {conf}\n"
                if payload:
                    import json
                    p = payload if isinstance(payload, dict) else json.loads(payload)
                    # Show key fields
                    for k, v in list(p.items())[:3]:
                        result += f"  {k}: {str(v)[:60]}\n"

        # Summarize rejected patterns
        if rejected:
            result += "\n\nREJECTED PATTERNS:\n"
            for ctype, ckey, payload, evidence, conf, status, created in rejected[:10]:
                result += f"\n✗ {ctype}: {ckey}\n"
                result += f"  Confidence: {conf}\n"
                if payload:
                    import json
                    p = payload if isinstance(payload, dict) else json.loads(payload)
                    for k, v in list(p.items())[:3]:
                        result += f"  {k}: {str(v)[:60]}\n"

        result += f"\n\nUse this feedback to update your extraction patterns in memory."
        return result

    except Exception as e:
        return f"Error observing staging feedback: {str(e)}"


@tool
def read_memory_patterns() -> str:
    """
    Read learned extraction patterns from long-term memory.

    Returns patterns that humans have accepted/rejected over time.
    Use this at the START of extractions to follow learned patterns.

    Returns:
        Learned patterns, or empty string if no patterns learned yet
    """
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
        memory_file = os.path.join(project_root, 'memories', 'extraction_patterns.txt')

        if os.path.exists(memory_file):
            with open(memory_file, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return "No learned patterns yet. Use observe_staging_feedback() to learn from human verification."
    except Exception as e:
        return f"Error reading memory patterns: {str(e)}"


@tool
def update_memory_patterns(patterns: str) -> str:
    """
    Update learned extraction patterns in long-term memory.

    After observing staging feedback, update your learned patterns.
    These patterns will persist across all future extractions.

    Args:
        patterns: Updated pattern text to save

    Returns:
        Confirmation message
    """
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
        memory_dir = os.path.join(project_root, 'memories')
        memory_file = os.path.join(memory_dir, 'extraction_patterns.txt')

        # Create memories directory if it doesn't exist
        os.makedirs(memory_dir, exist_ok=True)

        with open(memory_file, 'w', encoding='utf-8') as f:
            f.write(patterns)

        return f"Memory patterns updated successfully. {len(patterns)} characters saved."
    except Exception as e:
        return f"Error updating memory patterns: {str(e)}"


# Database query tools for confidence calibration
@tool
def query_verified_entities(
    entity_type: str = None,
    ecosystem: str = None,
    name_pattern: str = None,
    limit: int = 20
) -> str:
    """
    Query core_entities (verified truth) - USE THIS TO CALIBRATE CONFIDENCE.

    Before staging your extraction, check what verified data exists.
    Compare your extraction against approved examples to set appropriate confidence.

    Examples:
    - query_verified_entities(entity_type='component', ecosystem='proveskit')
      -> See verified PROVES Kit components to match your pattern

    - query_verified_entities(name_pattern='%I2C%')
      -> Find I2C-related entities to see how they were structured

    Returns: Entity details with properties you can compare against
    """
    try:
        import psycopg
        from dotenv import load_dotenv
        import os

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
        load_dotenv(os.path.join(project_root, '.env'))

        db_url = os.environ.get('NEON_DATABASE_URL')
        conn = psycopg.connect(db_url)

        query = """
            SELECT id, canonical_key, name, entity_type::text, ecosystem::text,
                   attributes, created_at
            FROM core_entities
            WHERE is_current = TRUE
        """
        params = []

        if entity_type:
            query += " AND entity_type = %s::entity_type"
            params.append(entity_type)

        if ecosystem:
            query += " AND ecosystem = %s::ecosystem_type"
            params.append(ecosystem)

        if name_pattern:
            query += " AND (canonical_key ILIKE %s OR name ILIKE %s)"
            params.extend([name_pattern, name_pattern])

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        conn.close()

        if not rows:
            return "No verified entities found. You're pioneering this extraction!"

        result = f"Found {len(rows)} verified entities for comparison:\n\n"
        for row in rows:
            entity_id, canonical_key, name, etype, eco, attrs, created = row
            result += f"ID: {entity_id}\n"
            result += f"  Key: {canonical_key} | Name: {name}\n"
            result += f"  Type: {etype} | Ecosystem: {eco}\n"
            if attrs:
                import json
                attrs_dict = attrs if isinstance(attrs, dict) else json.loads(attrs)
                result += f"  Attributes: {json.dumps(attrs_dict)[:200]}...\n"
            result += "\n"

        return result

    except Exception as e:
        return f"Error querying verified entities: {str(e)}"


@tool
def query_staging_history(
    candidate_type: str = None,
    min_confidence: float = None,
    limit: int = 20
) -> str:
    """
    Query staging history - SEE WHAT CONFIDENCE LEVELS WERE ACCEPTED.

    Learn from past extractions to calibrate your confidence scores.

    Examples:
    - query_staging_history(candidate_type='component', min_confidence=0.8)
      -> See high-confidence component extractions that were accepted

    Returns: Confidence scores and reasons from past extractions
    """
    try:
        import psycopg
        from dotenv import load_dotenv
        import os

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
        load_dotenv(os.path.join(project_root, '.env'))

        db_url = os.environ.get('NEON_DATABASE_URL')
        conn = psycopg.connect(db_url)

        query = """
            SELECT candidate_type::text, candidate_key,
                   confidence_score, confidence_reason, status::text
            FROM staging_extractions
            WHERE status = 'accepted'::candidate_status
        """
        params = []

        if candidate_type:
            query += " AND candidate_type = %s::candidate_type"
            params.append(candidate_type)

        if min_confidence is not None:
            query += " AND confidence_score >= %s"
            params.append(min_confidence)

        query += " ORDER BY confidence_score DESC LIMIT %s"
        params.append(limit)

        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

        conn.close()

        if not rows:
            return "No staging history found. Set your best confidence estimate!"

        result = f"Found {len(rows)} accepted extractions for calibration:\n\n"
        for row in rows:
            ctype, ckey, conf, reason, status = row
            result += f"{ctype}: {ckey}\n"
            result += f"  Confidence: {conf} - {reason}\n"
            result += f"  Status: {status}\n\n"

        return result

    except Exception as e:
        return f"Error querying staging history: {str(e)}"


@traceable(name="extractor_subagent")
def create_extractor_agent(checkpointer=None):
    """
    Create the extractor sub-agent with full Knowledge Capture Checklist training.

    Args:
        checkpointer: Optional LangGraph checkpointer (e.g., PostgresSaver) for state persistence
    """
    from langchain.agents import create_agent
    from ..subagent_specs import get_extractor_spec

    spec = get_extractor_spec()

    # Create agent with system prompt and optional checkpointer
    agent = create_agent(
        model=ChatAnthropic(model=spec["model"], temperature=0.1),
        system_prompt=spec["system_prompt"],
        tools=spec["tools"],
        checkpointer=checkpointer,
    )

    return agent
