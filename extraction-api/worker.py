#!/usr/bin/env python3
"""
PROVES Extraction Worker - Polls queues and routes to processors.

This worker is the correct way to run extractions:
1. Polls urls_to_process table for pending URLs
2. Polls crawl_jobs table for pending jobs
3. Routes to appropriate processor based on source type
4. Uses agent_v3.graph for the actual extraction pipeline

The key insight: This replaces the broken run_extraction_task() in app.py
which bypassed the V3 pipeline with a dumbed-down prompt.

Usage:
    python worker.py --daemon              # Run continuously
    python worker.py --once --limit 5      # Process 5 items and exit
    python worker.py --job <job_id>        # Process a specific job

Environment:
    DATABASE_URL or DIRECT_URL - PostgreSQL connection string
    SUPABASE_URL - Supabase project URL
    SUPABASE_SERVICE_ROLE_KEY - Service role key for Supabase
"""

import os
import sys
import time
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Setup paths
API_DIR = Path(__file__).parent
PROJECT_ROOT = API_DIR.parent
PRODUCTION_DIR = PROJECT_ROOT / "production"
VERSION3_DIR = PRODUCTION_DIR / "Version 3"

sys.path.insert(0, str(VERSION3_DIR))
sys.path.insert(0, str(PRODUCTION_DIR))
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(API_DIR))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

import psycopg

from processors import WebProcessor
from processors.base import ProcessResult


# =============================================================================
# DATABASE HELPERS
# =============================================================================

def get_db_url() -> str:
    """Get direct database URL (without pgbouncer parameter)."""
    return (
        os.environ.get("DIRECT_URL") or
        os.environ.get("PROVES_DATABASE_URL") or
        os.environ.get("DATABASE_URL")
    )


def get_db_connection():
    """Get a database connection using psycopg."""
    db_url = get_db_url()
    # Strip pgbouncer param if present (psycopg doesn't support it)
    if db_url and 'pgbouncer' in db_url:
        db_url = db_url.split('?')[0]
    if not db_url:
        raise ValueError("DATABASE_URL not set in environment")
    return psycopg.connect(db_url)


# =============================================================================
# URL QUEUE FUNCTIONS (urls_to_process table)
# =============================================================================

def get_pending_urls(limit: int = 10) -> List[Dict[str, Any]]:
    """Get pending URLs from urls_to_process table."""
    conn = get_db_connection()

    with conn.cursor() as cur:
        cur.execute("""
            SELECT url, quality_score, preview_components, preview_interfaces,
                   preview_keywords, preview_summary
            FROM urls_to_process
            WHERE status = 'pending'
            ORDER BY quality_score DESC, discovered_at ASC
            LIMIT %s
        """, (limit,))
        results = cur.fetchall()

    conn.close()

    return [
        {
            "url": row[0],
            "quality_score": row[1],
            "context": {
                "components": row[2] or [],
                "interfaces": row[3] or [],
                "keywords": row[4] or [],
                "summary": row[5] or "",
            },
        }
        for row in results
    ]


def update_url_status(
    url: str,
    status: str,
    error_msg: Optional[str] = None
):
    """Update URL status in urls_to_process table."""
    conn = get_db_connection()

    with conn.cursor() as cur:
        if status == "completed":
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


# =============================================================================
# CRAWL JOB FUNCTIONS (crawl_jobs + team_sources tables)
# =============================================================================

def get_pending_jobs(limit: int = 5) -> List[Dict[str, Any]]:
    """Get pending crawl jobs from database."""
    try:
        conn = get_db_connection()

        with conn.cursor() as cur:
            cur.execute("""
                SELECT cj.id, cj.source_id, cj.status,
                       ts.id, ts.name, ts.source_type, ts.source_config
                FROM crawl_jobs cj
                LEFT JOIN team_sources ts ON cj.source_id = ts.id
                WHERE cj.status = 'pending'
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()

        conn.close()

        jobs = []
        for row in rows:
            jobs.append({
                "job_id": str(row[0]),
                "source_id": str(row[1]) if row[1] else None,
                "source_type": row[5] or "unknown",
                "source_config": row[6] or {},
                "source_name": row[4] or "Unknown",
            })

        return jobs

    except Exception as e:
        print(f"Error getting pending jobs: {e}")
        return []


def update_job_status(
    job_id: str,
    status: str,
    items_found: int = 0,
    items_processed: int = 0,
    items_failed: int = 0,
    error_message: Optional[str] = None
):
    """Update crawl job status in database."""
    try:
        conn = get_db_connection()

        with conn.cursor() as cur:
            if status == "crawling":
                cur.execute("""
                    UPDATE crawl_jobs
                    SET status = %s, items_found = %s, items_processed = %s,
                        items_failed = %s, error_message = %s, started_at = NOW()
                    WHERE id = %s
                """, (status, items_found, items_processed, items_failed,
                      error_message, job_id))
            elif status in ("completed", "failed"):
                cur.execute("""
                    UPDATE crawl_jobs
                    SET status = %s, items_found = %s, items_processed = %s,
                        items_failed = %s, error_message = %s, completed_at = NOW()
                    WHERE id = %s
                """, (status, items_found, items_processed, items_failed,
                      error_message, job_id))
            else:
                cur.execute("""
                    UPDATE crawl_jobs
                    SET status = %s, items_found = %s, items_processed = %s,
                        items_failed = %s, error_message = %s
                    WHERE id = %s
                """, (status, items_found, items_processed, items_failed,
                      error_message, job_id))
            conn.commit()

        conn.close()

    except Exception as e:
        print(f"Error updating job status: {e}")


# =============================================================================
# PROCESSORS
# =============================================================================

# Registry of processors by source type
PROCESSORS = {
    "web": WebProcessor,
    "url_list": WebProcessor,  # url_list sources use web processor
    # "discord": DiscordProcessor,  # TODO
    # "notion": NotionProcessor,    # TODO
}


def get_processor(source_type: str):
    """Get the appropriate processor for a source type."""
    processor_class = PROCESSORS.get(source_type)
    if processor_class is None:
        raise ValueError(f"Unknown source type: {source_type}")
    return processor_class()


# =============================================================================
# PROCESSING FUNCTIONS
# =============================================================================

def process_url(url_info: Dict[str, Any], index: int, total: int) -> ProcessResult:
    """
    Process a single URL from urls_to_process table.

    Uses the WebProcessor which properly invokes agent_v3.graph
    with FRAMES-aware prompts from task_builder.
    """
    url = url_info["url"]
    context = url_info["context"]
    source_id = url_info.get("source_id")

    print(f"\n{'='*70}")
    print(f"Processing [{index}/{total}]: {url}")
    print(f"{'='*70}")
    print(f"Quality Score: {url_info.get('quality_score', 'N/A')}")

    if context.get("components"):
        print(f"Components: {', '.join(context['components'][:5])}")
    if context.get("keywords"):
        print(f"Keywords: {', '.join(context['keywords'][:8])}")

    # Update status to processing
    update_url_status(url, "processing")

    # Process with WebProcessor
    processor = WebProcessor()
    result = processor.process(
        job_id=f"url-{index}",
        source_config={"url": url, "context": context},
        source_id=source_id,
    )

    # Update status based on result
    if result.status == "success":
        update_url_status(url, "completed")
        print(f"[OK] Success - {result.extractions_count} extractions")
    else:
        update_url_status(url, "failed", result.error_message or result.message)
        print(f"[FAIL] {result.stage}: {result.message[:100]}")

    return result


def process_job(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a crawl job from crawl_jobs table.

    Routes to appropriate processor based on source_type.
    """
    job_id = job["job_id"]
    source_type = job["source_type"]
    source_config = job["source_config"]
    source_name = job["source_name"]

    print(f"\n{'='*70}")
    print(f"Processing Job: {job_id}")
    print(f"Source: {source_name} ({source_type})")
    print(f"{'='*70}")

    # Update status to crawling
    update_job_status(job_id, "crawling")

    try:
        processor = get_processor(source_type)
    except ValueError as e:
        update_job_status(job_id, "failed", error_message=str(e))
        return {"status": "failed", "error": str(e)}

    # For url_list sources, process each URL
    if source_type == "url_list":
        urls = source_config.get("urls", [])
        if not urls:
            update_job_status(job_id, "failed", error_message="No URLs in source")
            return {"status": "failed", "error": "No URLs"}

        processed = 0
        failed = 0

        for i, url in enumerate(urls, 1):
            result = processor.process(
                job_id=f"{job_id}-{i}",
                source_config={"url": url},
                source_id=job["source_id"],
            )

            if result.status == "success":
                processed += 1
            else:
                failed += 1

            # Update progress
            update_job_status(
                job_id, "crawling",
                items_found=len(urls),
                items_processed=processed,
                items_failed=failed,
            )

        # Mark complete
        final_status = "completed" if failed == 0 else "completed"
        update_job_status(
            job_id, final_status,
            items_found=len(urls),
            items_processed=processed,
            items_failed=failed,
        )

        return {
            "status": final_status,
            "items_found": len(urls),
            "items_processed": processed,
            "items_failed": failed,
        }

    # For other source types (website crawl, etc.)
    else:
        result = processor.process(
            job_id=job_id,
            source_config=source_config,
            source_id=job["source_id"],
        )

        status = "completed" if result.status == "success" else "failed"
        update_job_status(
            job_id, status,
            items_found=1,
            items_processed=1 if result.status == "success" else 0,
            items_failed=0 if result.status == "success" else 1,
            error_message=result.error_message,
        )

        return {"status": status, "result": result}


# =============================================================================
# MAIN WORKER LOOP
# =============================================================================

def run_once(limit: int = 10, job_id: Optional[str] = None):
    """Run worker once and exit."""
    print(f"\n{'='*70}")
    print("PROVES Extraction Worker - Single Run")
    print(f"{'='*70}\n")

    # If specific job requested
    if job_id:
        try:
            conn = get_db_connection()

            with conn.cursor() as cur:
                cur.execute("""
                    SELECT cj.id, cj.source_id, cj.status,
                           ts.id, ts.name, ts.source_type, ts.source_config
                    FROM crawl_jobs cj
                    LEFT JOIN team_sources ts ON cj.source_id = ts.id
                    WHERE cj.id = %s
                """, (job_id,))
                row = cur.fetchone()

            conn.close()

            if not row:
                print(f"Job not found: {job_id}")
                return

            job = {
                "job_id": str(row[0]),
                "source_id": str(row[1]) if row[1] else None,
                "source_type": row[5] or "unknown",
                "source_config": row[6] or {},
                "source_name": row[4] or "Unknown",
            }

            process_job(job)
            return

        except Exception as e:
            print(f"Error fetching job: {e}")
            return

    # Process pending URLs first
    urls = get_pending_urls(limit=limit)
    if urls:
        print(f"Found {len(urls)} pending URLs\n")
        for i, url_info in enumerate(urls, 1):
            process_url(url_info, i, len(urls))
    else:
        print("No pending URLs in queue")

    # Then process pending jobs
    jobs = get_pending_jobs(limit=limit)
    if jobs:
        print(f"\nFound {len(jobs)} pending jobs\n")
        for job in jobs:
            process_job(job)
    else:
        print("No pending jobs")

    print(f"\n{'='*70}")
    print("Worker run complete")
    print(f"{'='*70}\n")


def run_daemon(poll_interval: int = 30):
    """Run worker as daemon, polling continuously."""
    print(f"\n{'='*70}")
    print("PROVES Extraction Worker - Daemon Mode")
    print(f"Poll interval: {poll_interval} seconds")
    print(f"{'='*70}\n")

    while True:
        try:
            # Check for pending URLs
            urls = get_pending_urls(limit=10)
            if urls:
                print(f"\n[{datetime.now().isoformat()}] "
                      f"Processing {len(urls)} URLs...")
                for i, url_info in enumerate(urls, 1):
                    process_url(url_info, i, len(urls))

            # Check for pending jobs
            jobs = get_pending_jobs(limit=5)
            if jobs:
                print(f"\n[{datetime.now().isoformat()}] "
                      f"Processing {len(jobs)} jobs...")
                for job in jobs:
                    process_job(job)

            # Sleep if nothing to do
            if not urls and not jobs:
                print(f"[{datetime.now().isoformat()}] "
                      f"No work. Sleeping {poll_interval}s...")

            time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("\n\nShutting down worker...")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            time.sleep(poll_interval)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="PROVES Extraction Worker - Process extraction queue"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously as daemon"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process once and exit"
    )
    parser.add_argument(
        "--job",
        type=str,
        help="Process a specific job ID"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Max items to process per run (default: 10)"
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=30,
        help="Seconds between polls in daemon mode (default: 30)"
    )

    args = parser.parse_args()

    if args.daemon:
        run_daemon(poll_interval=args.poll_interval)
    elif args.once or args.job:
        run_once(limit=args.limit, job_id=args.job)
    else:
        # Default to single run
        run_once(limit=args.limit)


if __name__ == "__main__":
    main()
