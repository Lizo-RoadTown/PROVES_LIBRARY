"""
Extractor Sub-Agent
Specialized agent for extracting dependencies from documentation

Supports:
- Local file reading
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
def extract_dependencies_using_claude(text: str, document_name: str) -> str:
    """
    Extract dependencies from text using Claude Sonnet 4.5.

    Identifies:
    - Component names
    - Dependency relationships (ERV types)
    - Criticality levels (HIGH/MEDIUM/LOW)
    - Context and reasoning
    """
    from langchain_anthropic import ChatAnthropic

    try:
        model = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            temperature=0,
        )

        extraction_prompt = f"""Analyze this technical documentation and extract ALL software/hardware dependencies.

Document: {document_name}

Text to analyze:
{text}

For each dependency, identify:
1. Component name (what depends on something else)
2. Depends on (what it needs/requires)
3. Relationship type: depends_on, requires, enables, conflicts_with, mitigates, causes
4. Criticality: HIGH (critical for operation), MEDIUM (important but has workarounds), LOW (nice-to-have)
5. Context (line numbers, specific details)

Format each dependency as:
- Component: <name>
- Depends on: <target>
- Type: <relationship>
- Criticality: <level>
- Context: <details>

Extract ALL dependencies, including:
- Runtime dependencies (code depends on libraries)
- Build dependencies (requires specific tools)
- Hardware dependencies (software needs specific hardware)
- Configuration dependencies
- Cross-system dependencies
"""

        response = model.invoke(extraction_prompt)
        return f"Extraction Results:\n\n{response.content}"

    except Exception as e:
        return f"Error during extraction: {str(e)}"


@traceable(name="extractor_subagent")
def create_extractor_agent():
    """
    Create the extractor sub-agent

    This agent specializes in:
    - Reading local documentation files
    - Fetching web documentation (nasa.github.io/fprime, docs.proveskit.space)
    - Fetching GitHub source files directly (without cloning)
    - Listing GitHub directories to explore structure
    - Extracting dependencies using LLM
    - Identifying ERV relationship types
    - Assessing criticality levels
    
    All extractions include source URLs/paths for citation.
    """
    model = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=0.1,
    )

    tools = [
        read_document,
        fetch_webpage,
        fetch_github_file,
        list_github_directory,
        extract_dependencies_using_claude,
    ]

    agent = create_react_agent(model, tools)
    return agent
