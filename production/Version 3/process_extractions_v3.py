"""
Process Extraction Queue - Curator Agent v3

This is version 3 of process_extractions that uses refactored agent files:
- agent_v3.py (orchestration with refactored tools)
- validator_v3.py (lineage verification + epistemic validation)
- storage_v3.py (receives verification results + epistemic defaults/overrides)

Reads URLs from urls_to_process table and processes them with the curator agent.
Uses context hints from WebFetch to focus extraction.

Usage:
    python testing/scripts/refactor_pre_lineage_folder/process_extractions_v3.py --limit 1
"""

import os
import sys
import uuid
from pathlib import Path
from dotenv import load_dotenv
import psycopg

# Setup paths
# Now in production/Version 3/, so go up 2 levels to reach project root
version3_folder = Path(__file__).parent
project_root = version3_folder.parent.parent
production_root = project_root / 'production'

# Add paths
sys.path.insert(0, str(production_root))
sys.path.insert(0, str(version3_folder))

# Load environment
load_dotenv(project_root / '.env')

# Import from v3 agent
from agent_v3 import graph


def ensure_webhook_server_running():
    """
    Ensure the Notion webhook server is running.
    If not, start it as a background process.
    """
    import subprocess
    import requests
    import time

    # Check if webhook server is already running by trying to connect
    try:
        response = requests.get('http://localhost:8000/health', timeout=2)
        if response.status_code == 200:
            print("[OK] Notion webhook server is already running")
            return True
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        pass

    # Server not running, start it
    print("Starting Notion webhook server...")
    webhook_script = project_root / 'notion' / 'scripts' / 'notion_webhook_server.py'

    if not webhook_script.exists():
        print(f"Warning: Webhook server script not found at {webhook_script}")
        return False

    # Start webhook server as background process
    try:
        # Create log file for webhook server output
        webhook_log = project_root / 'webhook_server.log'
        log_file = open(webhook_log, 'w')

        if sys.platform == 'win32':
            # Windows: use CREATE_NEW_PROCESS_GROUP to detach
            subprocess.Popen(
                [sys.executable, str(webhook_script)],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=str(webhook_script.parent)
            )
        else:
            # Unix: use start_new_session to detach
            subprocess.Popen(
                [sys.executable, str(webhook_script)],
                start_new_session=True,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=str(webhook_script.parent)
            )

        print(f"Webhook server output: {webhook_log}")

        # Wait a moment for server to start
        print("Waiting for webhook server to start...")
        for _ in range(10):
            time.sleep(1)
            try:
                response = requests.get('http://localhost:8000/health', timeout=2)
                if response.status_code == 200:
                    print("[OK] Notion webhook server started successfully")
                    return True
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                continue

        print("Warning: Webhook server may not have started properly")
        return False

    except Exception as e:
        print(f"Error starting webhook server: {e}")
        return False


def safe_print(text):
    """Print text, replacing characters Windows console can't display."""
    # Replace problematic Unicode characters with ASCII equivalents
    replacements = {
        '\u2032': "'",  # prime symbol
        '\u2192': "->",  # right arrow
        '\u2713': "[OK]",  # checkmark
        '\u2717': "x",  # cross mark
    }
    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)
    # Remove any remaining non-ASCII characters
    return text.encode('ascii', 'replace').decode('ascii')


def get_pending_urls(limit: int = None):
    """Get pending URLs from queue with their context."""
    db_url = os.environ.get('NEON_DATABASE_URL')
    conn = psycopg.connect(db_url)

    with conn.cursor() as cur:
        query = """
            SELECT url, quality_score, preview_components, preview_interfaces,
                   preview_keywords, preview_summary
            FROM urls_to_process
            WHERE status = 'pending'
            ORDER BY quality_score DESC, discovered_at ASC
        """
        if limit:
            query += f" LIMIT {limit}"

        cur.execute(query)
        results = cur.fetchall()

    conn.close()

    return [
        {
            'url': row[0],
            'quality_score': row[1],
            'components': row[2] or [],
            'interfaces': row[3] or [],
            'keywords': row[4] or [],
            'summary': row[5] or ''
        }
        for row in results
    ]


def update_url_status(url: str, status: str, error_msg: str = None):
    """Update URL status in database."""
    db_url = os.environ.get('NEON_DATABASE_URL')
    conn = psycopg.connect(db_url)

    with conn.cursor() as cur:
        if status == 'completed':
            cur.execute("""
                UPDATE urls_to_process
                SET status = %s, processed_at = NOW(), error_message = NULL
                WHERE url = %s
            """, (status, url))
        else:
            cur.execute("""
                UPDATE urls_to_process
                SET status = %s, error_message = %s
                WHERE url = %s
            """, (status, error_msg, url))

        conn.commit()

    conn.close()


def process_url(url_info: dict, index: int, total: int):
    """
    Process a single URL with the curator agent (BACKUP VERSION).

    Uses context hints from WebFetch to focus extraction.
    """
    url = url_info['url']
    components = url_info['components']
    interfaces = url_info['interfaces']
    keywords = url_info['keywords']
    summary = url_info['summary']

    print(f"\n{'='*80}")
    print(f"[TEST] Processing [{index}/{total}]: {url}")
    print(f"{'='*80}")
    print(f"Quality Score: {url_info['quality_score']:.2f}")

    if summary:
        print(f"Preview: {safe_print(summary[:100])}...")

    if components:
        print(f"Likely Components: {', '.join(components[:5])}")

    if interfaces:
        print(f"Likely Interfaces: {', '.join(interfaces[:5])}")

    if keywords:
        print(f"Keywords: {', '.join(keywords[:8])}")

    print(f"\n{'-'*80}\n")

    # Update status to processing
    update_url_status(url, 'processing')

    # Build context-aware task for curator
    context_hints = []
    if components:
        context_hints.append(f"- Look for these components: {', '.join(components[:10])}")
    if interfaces:
        context_hints.append(f"- Look for these interfaces/ports: {', '.join(interfaces[:10])}")
    if keywords:
        context_hints.append(f"- Key topics: {', '.join(keywords)}")

    context_section = "\n".join(context_hints) if context_hints else "- Scan entire page for architecture elements"

    task = f"""
You are the curator agent for the PROVES Library (TESTING WITH BACKUP REFACTORS).

YOUR MISSION: Extract architecture from this documentation page.

URL: {url}

CONTEXT HINTS (from WebFetch pre-scan):
{context_section}

EXTRACTION FOCUS (use FRAMES methodology):
- COMPONENTS: What modules/units exist? (hardware, software, subsystems)
- INTERFACES: Where do they connect? (ports, buses, protocols, picolocks)
- FLOWS: What moves through connections? (data, commands, power, signals)
- MECHANISMS: What maintains interfaces? (documentation, schemas, drivers)
- DEPENDENCIES: Component-to-component relationships
- CONFIGURATION: Parameters, settings, modes
- SAFETY CONSTRAINTS: Critical requirements, inhibit schemes, failure modes

For EACH extraction:
- Provide exact evidence quotes from source
- Document confidence reasoning
- Identify relationships to other components
- CITE THE SOURCE URL

CRITICAL - NEW EPISTEMIC PATTERN:
1. Output ONE epistemic_defaults object at the start (for the entire page)
2. For each candidate, output epistemic_overrides (empty {{}} if all defaults apply)

Then store ALL extractions in staging_extractions. Work autonomously - no approval needed.
"""

    # Run curator agent (BACKUP VERSION)
    try:
        thread_id = f"test-backup-{uuid.uuid4().hex[:8]}"
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 20  # Limit API calls to prevent expensive loops
        }

        print("[TEST] Invoking BACKUP orchestration pipeline...")
        print("[TEST] This will call: extractor -> validator (BACKUP) -> storage (BACKUP)")
        print()

        result = graph.invoke(
            {"messages": [{"role": "user", "content": task}]},
            config
        )

        # Handle both message object and dict formats
        last_message = result['messages'][-1]
        final_message = last_message.content if hasattr(last_message, 'content') else last_message.get('content', str(last_message))

        # Update status to completed
        update_url_status(url, 'completed')

        print(f"\n[TEST] Curator Result:")
        print(f"{'-'*80}")
        safe_message = safe_print(final_message[:500] + "..." if len(final_message) > 500 else final_message)
        print(safe_message)
        print(f"{'-'*80}\n")

        return {'url': url, 'status': 'success', 'message': final_message}

    except Exception as e:
        # Update status to failed with error
        update_url_status(url, 'failed', str(e))

        print(f"\n[TEST ERROR] Error processing {url}: {e}\n")
        import traceback
        traceback.print_exc()
        return {'url': url, 'status': 'error', 'message': str(e)}


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="TEST process extraction queue with BACKUP refactors"
    )
    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=1,
        help="Number of URLs to process (default: 1 for testing)"
    )
    parser.add_argument(
        "-c", "--continuous",
        action="store_true",
        help="Keep processing until queue is empty"
    )

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print("TEST CURATOR AGENT - BACKUP REFACTORS")
    print(f"{'='*80}")
    print()
    print("Using backup agent files:")
    print("  - agent_v2_BACKUP.py")
    print("  - validator_BACKUP_pre_lineage_split.py")
    print("  - storage_BACKUP_pre_lineage_split.py")
    print("  - subagent_specs_BACKUP_pre_lineage_split.py")
    print()
    print("Refactors being tested:")
    print("  1. Lineage refactor (validator verifies, storage computes)")
    print("  2. Epistemic defaults + overrides pattern")
    print()
    print(f"Testing with {args.limit} URL(s)")
    print(f"\n{'='*80}")

    # Ensure Notion webhook server is running for automatic sync
    ensure_webhook_server_running()
    print()

    if args.continuous:
        print("\nMode: Continuous (process until queue empty)")
        total_processed = 0

        while True:
            # Get next batch
            urls = get_pending_urls(limit=10)

            if not urls:
                print(f"\nQueue empty! Processed {total_processed} total URLs")
                break

            print(f"\nProcessing batch of {len(urls)} URLs...")

            for i, url_info in enumerate(urls, 1):
                result = process_url(url_info, total_processed + i, total_processed + len(urls))

            total_processed += len(urls)
            print(f"\nBatch complete. Total processed: {total_processed}")

    else:
        # Single batch
        urls = get_pending_urls(limit=args.limit)

        if not urls:
            print("\nNo pending URLs in queue.")
            print("\nRun find_good_urls.py first:")
            print("  python production/scripts/find_good_urls.py --fprime --max-pages 10")
            return

        print(f"\nProcessing {len(urls)} URL(s) from queue")
        print(f"\n{'='*80}\n")

        results = []
        for i, url_info in enumerate(urls, 1):
            result = process_url(url_info, i, len(urls))
            results.append(result)

        # Summary
        print(f"\n{'='*80}")
        print("TEST BATCH PROCESSING COMPLETE")
        print(f"{'='*80}\n")

        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'error']

        print(f"Processed: {len(urls)} URL(s)")
        print(f"  Success: {len(successful)}")
        print(f"  Failed: {len(failed)}")
        print()

        if failed:
            print("Failed URLs:")
            for r in failed:
                print(f"  - {r['url']}: {r['message'][:100]}")
            print()

    print("Check database:")
    print("  - staging_extractions table for new extractions")
    print("  - Look for lineage_verified, lineage_confidence from validator")
    print("  - Look for epistemic metadata merged from defaults+overrides")
    print()
    print("LangSmith traces: https://smith.langchain.com/")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\n\n[TEST ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()
