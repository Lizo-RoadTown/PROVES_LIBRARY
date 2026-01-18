"""
Crawl Orchestrator - Team Sources Crawler

Orchestrates extraction from team sources defined in the database.
Works with Migration 022 (team_sources, crawl_jobs, crawl_items).

Flow:
1. Claims a pending crawl_job from the queue
2. Crawls the source based on its type (GitHub, Notion, GDrive, Discord)
3. Discovers items and stores them in crawl_items
4. For each item, runs the extractor agent
5. Extractions are stored in staging_extractions (tagged with organization_id)
6. Updates job status on completion

Usage:
    python production/Version 3/crawl_orchestrator.py --once       # Process one job
    python production/Version 3/crawl_orchestrator.py --daemon     # Run continuously
    python production/Version 3/crawl_orchestrator.py --job <id>   # Process specific job
"""

import os
import sys
import time
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
import psycopg

# Setup paths
version3_folder = Path(__file__).parent
project_root = version3_folder.parent.parent
production_root = project_root / 'production'

sys.path.insert(0, str(production_root))
sys.path.insert(0, str(version3_folder))

# Load environment
load_dotenv(project_root / '.env')

# Import extraction agent
try:
    from agent_v3 import graph
except ImportError:
    print("Warning: agent_v3 not available, running in discovery-only mode")
    graph = None


# =============================================================================
# DATABASE HELPERS
# =============================================================================

def get_db_connection():
    """Get database connection."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg.connect(db_url)


def claim_next_job() -> Optional[Dict[str, Any]]:
    """
    Claim the next pending crawl job using the claim_next_crawl_job() function.
    Returns job info or None if no jobs available.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM claim_next_crawl_job()")
            row = cur.fetchone()
            if not row:
                return None

            # Map column names
            return {
                'job_id': str(row[0]),
                'source_id': str(row[1]),
                'source_type': row[2],
                'source_config': row[3],
                'include_patterns': row[4] or [],
                'exclude_patterns': row[5] or [],
            }
        conn.commit()
    finally:
        conn.close()
    return None


def update_job_progress(job_id: str, current_item: str, items_found: int, items_processed: int):
    """Update job progress in the database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE crawl_jobs
                SET current_item = %s,
                    items_found = %s,
                    items_processed = %s
                WHERE id = %s::uuid
            """, (current_item, items_found, items_processed, job_id))
        conn.commit()
    finally:
        conn.close()


def complete_job(job_id: str, status: str, items_found: int, items_processed: int,
                 items_failed: int = 0, error_message: str = None):
    """Mark job as completed using complete_crawl_job() function."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT complete_crawl_job(%s::uuid, %s::crawl_status, %s, %s, %s, %s)
            """, (job_id, status, items_found, items_processed, items_failed, error_message))
        conn.commit()
    finally:
        conn.close()


def get_source_organization(source_id: str) -> Optional[str]:
    """Get the organization_id for a source."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT organization_id FROM team_sources WHERE id = %s::uuid
            """, (source_id,))
            row = cur.fetchone()
            return str(row[0]) if row and row[0] else None
    finally:
        conn.close()


def upsert_crawl_item(source_id: str, job_id: str, external_id: str, item_info: Dict[str, Any]) -> str:
    """Insert or update a crawl item. Returns the item ID."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO crawl_items (
                    source_id, job_id, external_id, external_url, item_path,
                    item_type, title, content_hash, content_size_bytes,
                    last_modified_at, provider_metadata, last_seen_at
                ) VALUES (
                    %s::uuid, %s::uuid, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s::timestamptz, %s::jsonb, NOW()
                )
                ON CONFLICT (source_id, external_id)
                DO UPDATE SET
                    external_url = EXCLUDED.external_url,
                    item_path = EXCLUDED.item_path,
                    title = EXCLUDED.title,
                    content_hash = EXCLUDED.content_hash,
                    content_size_bytes = EXCLUDED.content_size_bytes,
                    last_modified_at = EXCLUDED.last_modified_at,
                    provider_metadata = EXCLUDED.provider_metadata,
                    last_seen_at = NOW(),
                    is_deleted = false
                RETURNING id
            """, (
                source_id, job_id, external_id,
                item_info.get('url'),
                item_info.get('path'),
                item_info.get('type', 'file'),
                item_info.get('title'),
                item_info.get('content_hash'),
                item_info.get('size_bytes'),
                item_info.get('modified_at'),
                json.dumps(item_info.get('metadata', {}))
            ))
            item_id = str(cur.fetchone()[0])
        conn.commit()
        return item_id
    finally:
        conn.close()


def mark_item_processed(item_id: str, extraction_id: str = None):
    """Mark a crawl item as processed."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE crawl_items
                SET processed_at = NOW(),
                    extraction_id = %s::uuid
                WHERE id = %s::uuid
            """, (extraction_id, item_id))
        conn.commit()
    finally:
        conn.close()


# =============================================================================
# SOURCE CRAWLERS
# =============================================================================

def crawl_github_org(config: Dict[str, Any], patterns: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """
    Crawl a GitHub organization's repositories.

    Config: { org: "PROVES", include_repos: ["*"], exclude_repos: [] }
    Returns: List of items to process
    """
    import requests

    org = config.get('org')
    if not org:
        raise ValueError("GitHub org not specified in config")

    include_repos = config.get('include_repos', ['*'])
    exclude_repos = config.get('exclude_repos', [])

    items = []

    # Get repos from GitHub API
    github_token = os.environ.get('GITHUB_TOKEN')
    headers = {'Authorization': f'token {github_token}'} if github_token else {}

    response = requests.get(
        f'https://api.github.com/orgs/{org}/repos',
        headers=headers,
        params={'per_page': 100, 'type': 'public'}
    )

    if response.status_code != 200:
        raise Exception(f"GitHub API error: {response.status_code} - {response.text}")

    repos = response.json()

    for repo in repos:
        repo_name = repo['name']

        # Check include/exclude patterns
        if '*' not in include_repos and repo_name not in include_repos:
            continue
        if repo_name in exclude_repos:
            continue

        # Get README and docs
        readme_url = f"https://raw.githubusercontent.com/{org}/{repo_name}/main/README.md"
        items.append({
            'external_id': f"{org}/{repo_name}/README.md",
            'url': readme_url,
            'path': f"{repo_name}/README.md",
            'type': 'file',
            'title': f"{repo_name} README",
            'modified_at': repo.get('updated_at'),
            'metadata': {
                'repo': repo_name,
                'stars': repo.get('stargazers_count', 0),
                'language': repo.get('language'),
            }
        })

        # Also add docs folder if it exists
        docs_url = f"https://api.github.com/repos/{org}/{repo_name}/contents/docs"
        docs_response = requests.get(docs_url, headers=headers)
        if docs_response.status_code == 200:
            for doc in docs_response.json():
                if doc['type'] == 'file' and doc['name'].endswith('.md'):
                    items.append({
                        'external_id': f"{org}/{repo_name}/{doc['path']}",
                        'url': doc['download_url'],
                        'path': f"{repo_name}/{doc['path']}",
                        'type': 'file',
                        'title': doc['name'],
                        'size_bytes': doc.get('size'),
                        'metadata': {'repo': repo_name}
                    })

    return items


def crawl_github_repo(config: Dict[str, Any], patterns: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """
    Crawl a single GitHub repository.

    Config: { repo: "PROVES/PROVESKit" }
    """
    import requests

    repo = config.get('repo', '')
    if '/' in repo:
        org, repo_name = repo.split('/', 1)
    else:
        raise ValueError("Repo must be in format 'org/repo'")

    items = []
    github_token = os.environ.get('GITHUB_TOKEN')
    headers = {'Authorization': f'token {github_token}'} if github_token else {}

    # Get all markdown files recursively
    def get_files(path=''):
        url = f"https://api.github.com/repos/{org}/{repo_name}/contents/{path}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return

        for item in response.json():
            if item['type'] == 'dir':
                # Skip excluded patterns
                skip = False
                for pattern in patterns.get('exclude', []):
                    if pattern.replace('**/', '').replace('/**', '') in item['path']:
                        skip = True
                        break
                if not skip:
                    get_files(item['path'])
            elif item['type'] == 'file':
                # Only process markdown, python, and config files
                if any(item['name'].endswith(ext) for ext in ['.md', '.py', '.yaml', '.yml', '.json', '.rst']):
                    items.append({
                        'external_id': f"{org}/{repo_name}/{item['path']}",
                        'url': item['download_url'],
                        'path': item['path'],
                        'type': 'file',
                        'title': item['name'],
                        'size_bytes': item.get('size'),
                        'content_hash': item.get('sha'),
                        'metadata': {'repo': repo}
                    })

    get_files()
    return items


def crawl_notion_workspace(config: Dict[str, Any], patterns: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """
    Crawl a Notion workspace.

    Config: { workspace_id: "...", root_page_id: "..." }
    """
    # Placeholder - would use Notion API
    print(f"  [NOTION] Would crawl workspace: {config.get('workspace_id')}")
    return []


def crawl_gdrive_folder(config: Dict[str, Any], patterns: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """
    Crawl a Google Drive folder.

    Config: { folder_id: "..." }
    """
    # Placeholder - would use Google Drive API
    print(f"  [GDRIVE] Would crawl folder: {config.get('folder_id')}")
    return []


def crawl_discord_server(config: Dict[str, Any], patterns: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """
    Crawl Discord server channels.

    Config: { server_id: "...", channel_ids: [...] }
    """
    # Placeholder - would use Discord API
    print(f"  [DISCORD] Would crawl server: {config.get('server_id')}")
    return []


# Source type to crawler mapping
CRAWLERS = {
    'github_org': crawl_github_org,
    'github_repo': crawl_github_repo,
    'notion_workspace': crawl_notion_workspace,
    'notion_database': crawl_notion_workspace,
    'gdrive_folder': crawl_gdrive_folder,
    'gdrive_shared_drive': crawl_gdrive_folder,
    'discord_server': crawl_discord_server,
    'discord_channel': crawl_discord_server,
}


# =============================================================================
# EXTRACTION PROCESSOR
# =============================================================================

def process_item(item: Dict[str, Any], source_org_id: Optional[str]) -> Optional[str]:
    """
    Process a single crawl item through the extraction agent.
    Returns extraction_id if successful, None otherwise.
    """
    if not graph:
        print(f"  [SKIP] No extraction agent available")
        return None

    url = item.get('url')
    if not url:
        print(f"  [SKIP] No URL for item: {item.get('external_id')}")
        return None

    # Build extraction task
    task = f"""
You are the curator agent for the PROVES Library.

YOUR MISSION: Extract architecture knowledge from this document.

URL: {url}
Title: {item.get('title', 'Unknown')}
Type: {item.get('type', 'file')}

EXTRACTION FOCUS (FRAMES methodology):
- COMPONENTS: What modules/units exist?
- INTERFACES: Where do they connect?
- FLOWS: What moves through connections?
- DEPENDENCIES: Component relationships
- SAFETY CONSTRAINTS: Critical requirements

For EACH extraction:
- Provide exact evidence quotes
- Document confidence reasoning
- CITE THE SOURCE URL

IMPORTANT: Tag extractions with source_organization_id = "{source_org_id or 'null'}"

Store ALL extractions in staging_extractions.
"""

    try:
        import uuid
        thread_id = f"crawl-{uuid.uuid4().hex[:8]}"
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 50
        }

        result = graph.invoke(
            {"messages": [{"role": "user", "content": task}]},
            config
        )

        # Extract any extraction IDs from the result
        # This is a simplified version - in practice you'd parse the agent's response
        return None  # Would return actual extraction_id

    except Exception as e:
        print(f"  [ERROR] Extraction failed: {e}")
        return None


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================

def process_job(job: Dict[str, Any], extract: bool = True) -> Dict[str, Any]:
    """
    Process a single crawl job.

    Args:
        job: Job info from claim_next_job()
        extract: Whether to run extraction (False = discovery only)

    Returns:
        Result summary
    """
    job_id = job['job_id']
    source_id = job['source_id']
    source_type = job['source_type']
    source_config = job['source_config']

    print(f"\n{'='*60}")
    print(f"Processing Job: {job_id}")
    print(f"Source Type: {source_type}")
    print(f"{'='*60}")

    # Get organization for this source
    org_id = get_source_organization(source_id)
    print(f"Organization ID: {org_id or 'None'}")

    items_found = 0
    items_processed = 0
    items_failed = 0

    try:
        # Get the appropriate crawler
        crawler = CRAWLERS.get(source_type)
        if not crawler:
            raise ValueError(f"No crawler for source type: {source_type}")

        # Discover items
        print(f"\n[DISCOVER] Crawling {source_type}...")
        patterns = {
            'include': job['include_patterns'],
            'exclude': job['exclude_patterns'],
        }
        items = crawler(source_config, patterns)
        items_found = len(items)
        print(f"[DISCOVER] Found {items_found} items")

        # Store discovered items
        for i, item in enumerate(items):
            print(f"\n[{i+1}/{items_found}] {item.get('path', item.get('external_id'))}")

            # Update progress
            update_job_progress(job_id, item.get('path', ''), items_found, items_processed)

            # Store in crawl_items
            item_id = upsert_crawl_item(source_id, job_id, item['external_id'], item)

            if extract:
                # Process through extraction agent
                extraction_id = process_item(item, org_id)
                if extraction_id:
                    mark_item_processed(item_id, extraction_id)
                    items_processed += 1
                else:
                    items_failed += 1
            else:
                # Discovery only - mark as processed
                mark_item_processed(item_id)
                items_processed += 1

        # Complete job
        complete_job(job_id, 'completed', items_found, items_processed, items_failed)
        print(f"\n[COMPLETE] Job finished: {items_processed}/{items_found} processed, {items_failed} failed")

        return {
            'job_id': job_id,
            'status': 'completed',
            'items_found': items_found,
            'items_processed': items_processed,
            'items_failed': items_failed,
        }

    except Exception as e:
        print(f"\n[ERROR] Job failed: {e}")
        complete_job(job_id, 'failed', items_found, items_processed, items_failed, str(e))
        return {
            'job_id': job_id,
            'status': 'failed',
            'error': str(e),
            'items_found': items_found,
            'items_processed': items_processed,
        }


def run_once(extract: bool = True) -> Optional[Dict[str, Any]]:
    """Process one job from the queue."""
    job = claim_next_job()
    if not job:
        print("No pending jobs in queue")
        return None
    return process_job(job, extract=extract)


def run_daemon(poll_interval: int = 30, extract: bool = True):
    """Run continuously, processing jobs as they become available."""
    print(f"Starting crawl daemon (poll interval: {poll_interval}s)")
    print("Press Ctrl+C to stop\n")

    while True:
        try:
            job = claim_next_job()
            if job:
                result = process_job(job, extract=extract)
                print(f"\nResult: {result}")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No jobs, waiting...")

            time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("\nShutting down...")
            break
        except Exception as e:
            print(f"\n[ERROR] Daemon error: {e}")
            time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(description='Crawl Orchestrator for Team Sources')
    parser.add_argument('--once', action='store_true', help='Process one job and exit')
    parser.add_argument('--daemon', action='store_true', help='Run continuously')
    parser.add_argument('--job', type=str, help='Process a specific job ID')
    parser.add_argument('--discover-only', action='store_true', help='Only discover items, no extraction')
    parser.add_argument('--poll-interval', type=int, default=30, help='Seconds between queue polls (daemon mode)')

    args = parser.parse_args()
    extract = not args.discover_only

    if args.job:
        # Process specific job
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT cj.id, cj.source_id, ts.source_type, ts.source_config,
                           ts.include_patterns, ts.exclude_patterns
                    FROM crawl_jobs cj
                    JOIN team_sources ts ON ts.id = cj.source_id
                    WHERE cj.id = %s::uuid
                """, (args.job,))
                row = cur.fetchone()
                if not row:
                    print(f"Job not found: {args.job}")
                    return

                job = {
                    'job_id': str(row[0]),
                    'source_id': str(row[1]),
                    'source_type': row[2],
                    'source_config': row[3],
                    'include_patterns': row[4] or [],
                    'exclude_patterns': row[5] or [],
                }
        finally:
            conn.close()

        result = process_job(job, extract=extract)
        print(f"\nResult: {result}")

    elif args.daemon:
        run_daemon(poll_interval=args.poll_interval, extract=extract)

    elif args.once:
        result = run_once(extract=extract)
        if result:
            print(f"\nResult: {result}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
