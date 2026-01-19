#!/usr/bin/env python3
"""
Extraction Worker - Polls for pending crawl jobs and runs extraction pipeline.

This worker:
1. Polls Supabase for pending crawl jobs via claim_next_crawl_job()
2. Runs the extraction pipeline for each URL
3. Reports completion via complete_crawl_job()

Run locally for development:
    python production/worker/extraction_worker.py

Deploy to Railway/Render/Fly.io for production.

Environment variables required:
    - DIRECT_URL or PROVES_DATABASE_URL or DATABASE_URL
    - SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (for Supabase client)
    - ANTHROPIC_API_KEY
"""

import os
import sys
import time
import signal
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Setup paths
worker_folder = Path(__file__).parent
production_root = worker_folder.parent
project_root = production_root.parent
version3_folder = production_root / 'Version 3'

sys.path.insert(0, str(production_root))
sys.path.insert(0, str(version3_folder))
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env')

import psycopg
from supabase import create_client, Client

# Import extraction components
from agent_v3 import graph

# =============================================================================
# CONFIGURATION
# =============================================================================

POLL_INTERVAL_SECONDS = 5  # How often to check for new jobs
MAX_RETRIES = 3
SHUTDOWN_REQUESTED = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# =============================================================================
# DATABASE HELPERS
# =============================================================================

def _get_db_url() -> str:
    """Get direct database URL (without pgbouncer parameter)."""
    return (
        os.environ.get('DIRECT_URL') or
        os.environ.get('PROVES_DATABASE_URL') or
        os.environ.get('DATABASE_URL')
    )


def get_supabase_client() -> Client:
    """Create Supabase client with service role key for RPC calls."""
    url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL') or os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")

    return create_client(url, key)


# =============================================================================
# JOB PROCESSING
# =============================================================================

def claim_next_job(supabase: Client) -> Optional[Dict[str, Any]]:
    """
    Claim the next pending crawl job.

    Returns job info or None if no jobs available.
    """
    try:
        result = supabase.rpc('claim_next_crawl_job').execute()

        if result.data and len(result.data) > 0:
            job = result.data[0]
            logger.info(f"Claimed job {job['job_id']} for source {job['source_id']}")
            return job

        return None
    except Exception as e:
        logger.error(f"Error claiming job: {e}")
        return None


def complete_job(
    supabase: Client,
    job_id: str,
    status: str,
    items_found: int = 0,
    items_processed: int = 0,
    items_failed: int = 0,
    error_message: Optional[str] = None
) -> bool:
    """Mark a crawl job as completed."""
    try:
        result = supabase.rpc('complete_crawl_job', {
            'p_job_id': job_id,
            'p_status': status,
            'p_items_found': items_found,
            'p_items_processed': items_processed,
            'p_items_failed': items_failed,
            'p_error_message': error_message
        }).execute()

        logger.info(f"Completed job {job_id} with status {status}")
        return True
    except Exception as e:
        logger.error(f"Error completing job {job_id}: {e}")
        return False


def get_urls_for_source(source_id: str, source_type: str, source_config: Dict) -> list[str]:
    """
    Get URLs to process based on source type and config.

    For 'url_list' type: returns URLs from config
    For other types: would fetch from provider API (GitHub, Notion, etc.)
    """
    urls = []

    if source_type == 'url_list':
        # Direct URL list from config
        urls = source_config.get('urls', [])
        logger.info(f"Source has {len(urls)} URLs to process")

    elif source_type in ('github_repo', 'github_org'):
        # TODO: Fetch from GitHub API
        # For now, check if there's a docs URL in config
        docs_url = source_config.get('docs_url')
        if docs_url:
            urls = [docs_url]
        logger.info(f"GitHub source - found {len(urls)} docs URLs")

    elif source_type in ('notion_workspace', 'notion_database'):
        # TODO: Fetch from Notion API
        logger.warning("Notion source type not yet implemented")

    else:
        logger.warning(f"Unknown source type: {source_type}")

    return urls


def process_url(url: str, job_id: str, thread_prefix: str = "worker") -> Dict[str, Any]:
    """
    Process a single URL through the extraction pipeline.

    Returns dict with status and details.
    """
    import uuid

    logger.info(f"Processing URL: {url}")

    task = f"""
You are the curator agent for the PROVES Library.

YOUR MISSION: Extract architecture from this documentation page.

URL: {url}

EXTRACTION FOCUS (use FRAMES methodology):
- COMPONENTS: What modules/units exist? (hardware, software, subsystems)
- INTERFACES: Where do they connect? (ports, buses, protocols)
- FLOWS: What moves through connections? (data, commands, power, signals)
- MECHANISMS: What maintains interfaces? (documentation, schemas, drivers)
- DEPENDENCIES: Component-to-component relationships
- CONFIGURATION: Parameters, settings, modes
- SAFETY CONSTRAINTS: Critical requirements, failure modes

For EACH extraction:
- Provide exact evidence quotes from source
- Document confidence reasoning
- Identify relationships to other components
- CITE THE SOURCE URL

Store ALL extractions in staging_extractions. Work autonomously.
"""

    try:
        thread_id = f"{thread_prefix}-{job_id}-{uuid.uuid4().hex[:8]}"
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 100
        }

        result = graph.invoke(
            {"messages": [{"role": "user", "content": task}]},
            config
        )

        last_message = result['messages'][-1]
        final_message = last_message.content if hasattr(last_message, 'content') else str(last_message)

        # Check for success indicators
        if "success" in final_message.lower() or "stored" in final_message.lower():
            return {
                'url': url,
                'status': 'success',
                'message': final_message[:500]
            }
        else:
            return {
                'url': url,
                'status': 'completed',
                'message': final_message[:500]
            }

    except Exception as e:
        logger.error(f"Error processing {url}: {e}")
        return {
            'url': url,
            'status': 'error',
            'error': str(e)
        }


def process_job(supabase: Client, job: Dict[str, Any]) -> None:
    """
    Process a single crawl job.

    1. Get URLs for the source
    2. Process each URL through extraction pipeline
    3. Report completion
    """
    job_id = job['job_id']
    source_id = job['source_id']
    source_type = job['source_type']
    source_config = job.get('source_config', {})

    logger.info(f"Processing job {job_id}")
    logger.info(f"  Source type: {source_type}")
    logger.info(f"  Source config: {source_config}")

    try:
        # Get URLs to process
        urls = get_urls_for_source(source_id, source_type, source_config)

        if not urls:
            logger.warning(f"No URLs found for source {source_id}")
            complete_job(
                supabase, job_id, 'completed',
                items_found=0, items_processed=0, items_failed=0,
                error_message="No URLs found in source configuration"
            )
            return

        # Process each URL
        items_found = len(urls)
        items_processed = 0
        items_failed = 0
        errors = []

        for i, url in enumerate(urls):
            if SHUTDOWN_REQUESTED:
                logger.info("Shutdown requested, stopping job processing")
                break

            logger.info(f"Processing URL {i+1}/{len(urls)}: {url}")

            result = process_url(url, job_id)

            if result['status'] == 'error':
                items_failed += 1
                errors.append(f"{url}: {result.get('error', 'Unknown error')}")
            else:
                items_processed += 1

        # Complete the job
        final_status = 'completed' if items_failed == 0 else 'completed'  # Still completed even with some failures
        error_message = "; ".join(errors[:5]) if errors else None  # Limit error message length

        complete_job(
            supabase, job_id, final_status,
            items_found=items_found,
            items_processed=items_processed,
            items_failed=items_failed,
            error_message=error_message
        )

        logger.info(f"Job {job_id} completed: {items_processed}/{items_found} processed, {items_failed} failed")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        complete_job(
            supabase, job_id, 'failed',
            error_message=str(e)[:500]
        )


# =============================================================================
# MAIN WORKER LOOP
# =============================================================================

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global SHUTDOWN_REQUESTED
    logger.info("Shutdown signal received, finishing current job...")
    SHUTDOWN_REQUESTED = True


def main():
    """Main worker loop."""
    global SHUTDOWN_REQUESTED

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("=" * 60)
    logger.info("PROVES Extraction Worker Starting")
    logger.info("=" * 60)
    logger.info(f"Poll interval: {POLL_INTERVAL_SECONDS}s")
    logger.info(f"Press Ctrl+C to stop")
    logger.info("")

    # Initialize Supabase client
    try:
        supabase = get_supabase_client()
        logger.info("Supabase client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase: {e}")
        sys.exit(1)

    # Main loop
    idle_count = 0
    while not SHUTDOWN_REQUESTED:
        try:
            # Try to claim a job
            job = claim_next_job(supabase)

            if job:
                idle_count = 0
                process_job(supabase, job)
            else:
                idle_count += 1
                if idle_count % 12 == 1:  # Log every ~60 seconds when idle
                    logger.info("No pending jobs, waiting...")

            # Wait before next poll
            time.sleep(POLL_INTERVAL_SECONDS)

        except Exception as e:
            logger.error(f"Worker error: {e}")
            time.sleep(POLL_INTERVAL_SECONDS * 2)  # Back off on errors

    logger.info("Worker shutdown complete")


if __name__ == "__main__":
    main()
