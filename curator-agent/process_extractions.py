"""
Process Extraction Queue - Curator Agent

Reads URLs from urls_to_process table and processes them with the curator agent.
Uses context hints from WebFetch to focus extraction.

Usage:
    python process_extractions.py --limit 10
    python process_extractions.py --continuous  # Keep processing until queue empty
"""

import os
import sys
import uuid
from pathlib import Path
from dotenv import load_dotenv
import psycopg

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv(os.path.join(Path(__file__).parent.parent, '.env'))

from src.curator.agent_v2 import graph


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
    Process a single URL with the curator agent.

    Uses context hints from WebFetch to focus extraction.
    """
    url = url_info['url']
    components = url_info['components']
    interfaces = url_info['interfaces']
    keywords = url_info['keywords']
    summary = url_info['summary']

    print(f"\n{'='*80}")
    print(f"Processing [{index}/{total}]: {url}")
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
You are the curator agent for the PROVES Library.

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

Then store ALL extractions in staging_extractions. Work autonomously - no approval needed.
"""

    # Run curator agent
    try:
        thread_id = f"batch-{uuid.uuid4().hex[:8]}"
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 20  # Extractor(5) + Validator(5) + Storage(5) + overhead(5)
        }

        result = graph.invoke(
            {"messages": [{"role": "user", "content": task}]},
            config
        )

        # Handle both message object and dict formats
        last_message = result['messages'][-1]
        final_message = last_message.content if hasattr(last_message, 'content') else last_message.get('content', str(last_message))

        # Update status to completed
        update_url_status(url, 'completed')

        print(f"\nCurator Result:")
        print(f"{'-'*80}")
        safe_message = safe_print(final_message[:500] + "..." if len(final_message) > 500 else final_message)
        print(safe_message)
        print(f"{'-'*80}\n")

        return {'url': url, 'status': 'success', 'message': final_message}

    except Exception as e:
        # Update status to failed with error
        update_url_status(url, 'failed', str(e))

        print(f"\nError processing {url}: {e}\n")
        return {'url': url, 'status': 'error', 'message': str(e)}


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Process extraction queue with curator agent"
    )
    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=30,
        help="Number of URLs to process (default: 30)"
    )
    parser.add_argument(
        "-c", "--continuous",
        action="store_true",
        help="Keep processing until queue is empty"
    )

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print("CURATOR AGENT - BATCH PROCESSING FROM QUEUE")
    print(f"{'='*80}")

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
            print("  python find_good_urls.py --fprime --proveskit --max-pages 50")
            return

        print(f"\nProcessing {len(urls)} URLs from queue")
        print(f"\n{'='*80}\n")

        results = []
        for i, url_info in enumerate(urls, 1):
            result = process_url(url_info, i, len(urls))
            results.append(result)

        # Summary
        print(f"\n{'='*80}")
        print("BATCH PROCESSING COMPLETE")
        print(f"{'='*80}\n")

        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'error']

        print(f"Processed: {len(urls)} URLs")
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
    print("  - raw_snapshots table for source snapshots")
    print("  - urls_to_process table for queue status")
    print()
    print("LangSmith traces: https://smith.langchain.com/")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
