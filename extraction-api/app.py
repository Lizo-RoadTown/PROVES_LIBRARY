#!/usr/bin/env python3
"""
PROVES Extraction API - FastAPI service for queueing extractions.

IMPORTANT: This API is a THIN QUEUEING LAYER only.
It does NOT run extractions directly - that would bypass the V3 pipeline.

Flow:
    1. API receives URLs via POST /extract or POST /extract/job
    2. API inserts URLs into urls_to_process table with status='pending'
    3. Worker (worker.py) polls the queue and runs extractions
    4. Worker uses task_builder.py for FRAMES-aware prompts
    5. Worker invokes agent_v3.graph (Extractor → Validator → Storage)

Endpoints:
    POST /extract      - Queue URLs for extraction
    POST /extract/job  - Acknowledge a crawl job
    GET /jobs/{job_id} - Get job status
    GET /tasks/{task_id} - Get task status
    POST /discover     - Discover URLs from a website
    GET /discover/pending - Get pending discovered URLs
    GET /health        - Health check

Run locally:
    uvicorn app:app --reload --port 8080

Run with Docker:
    docker build -t proves-extraction-api .
    docker run -p 8080:8080 --env-file .env proves-extraction-api

Run worker (required for actual extraction):
    python worker.py --daemon
"""

import os
import sys
import uuid
import asyncio
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg

# =============================================================================
# CONFIGURATION
# =============================================================================

API_DIR = Path(__file__).parent
PROJECT_ROOT = API_DIR.parent if (API_DIR.parent / "production").exists() else API_DIR
PRODUCTION_DIR = PROJECT_ROOT / "production"

sys.path.insert(0, str(PRODUCTION_DIR))
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(API_DIR))

from dotenv import load_dotenv
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path)


# =============================================================================
# DATABASE / SUPABASE
# =============================================================================

def _get_db_url() -> str:
    """Get direct database URL (without pgbouncer parameter)."""
    db_url = (
        os.environ.get("DIRECT_URL") or
        os.environ.get("PROVES_DATABASE_URL") or
        os.environ.get("DATABASE_URL")
    )
    # Strip pgbouncer param if present (psycopg doesn't support it)
    if db_url and 'pgbouncer' in db_url:
        db_url = db_url.split('?')[0]
    return db_url


def get_db_connection():
    """Get a database connection using psycopg."""
    db_url = _get_db_url()
    if not db_url:
        raise ValueError("DATABASE_URL not set in environment")
    return psycopg.connect(db_url)


# =============================================================================
# MODELS
# =============================================================================

class ExtractRequest(BaseModel):
    """Request to queue URLs for extraction."""
    urls: List[str]
    source_id: Optional[str] = None
    quality_score: Optional[float] = 0.8  # Default quality for manually added URLs


class ExtractJobRequest(BaseModel):
    """Request to process a crawl job."""
    job_id: str


class CrawlDiscoveryRequest(BaseModel):
    """Request to discover URLs from a website."""
    starting_url: str
    max_pages: int = 50
    instructions: Optional[str] = None


class ExtractResponse(BaseModel):
    """Response from extraction request."""
    task_id: str
    status: str
    message: str
    urls_queued: int


class JobStatusResponse(BaseModel):
    """Job status response."""
    job_id: str
    status: str
    items_found: int
    items_processed: int
    items_failed: int
    error_message: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str
    worker_hint: str


class CrawlDiscoveryResponse(BaseModel):
    """Response from crawl discovery."""
    task_id: str
    status: str
    starting_url: str
    max_pages: int


# =============================================================================
# TASK TRACKING (for discovery tasks only)
# =============================================================================

running_tasks = {}


async def run_discovery_task(
    task_id: str,
    starting_url: str,
    max_pages: int,
    instructions: Optional[str] = None
):
    """
    Background task to discover good URLs from a website.
    Uses SmartWebFetchAgent from find_good_urls.py.

    This is OK to run in-process because it only DISCOVERS URLs
    and adds them to urls_to_process. The actual extraction
    is done by the worker.
    """
    running_tasks[task_id] = {
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
        "starting_url": starting_url,
        "max_pages": max_pages,
        "discovered": 0,
        "urls": [],
    }

    try:
        from production.scripts.find_good_urls import SmartWebFetchAgent

        agent = SmartWebFetchAgent()

        pages_added = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: agent.crawl([starting_url], max_pages=max_pages)
        )

        running_tasks[task_id]["discovered"] = pages_added
        running_tasks[task_id]["status"] = "completed"
        running_tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()

    except Exception as e:
        running_tasks[task_id]["status"] = "failed"
        running_tasks[task_id]["error"] = str(e)
        running_tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()
        print(f"Discovery task failed: {e}")


# =============================================================================
# FASTAPI APP
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print("PROVES Extraction API starting...")
    print("NOTE: This API only queues URLs. Run worker.py for extraction.")
    yield
    print("PROVES Extraction API shutting down...")


app = FastAPI(
    title="PROVES Extraction API",
    description=(
        "API for queueing extraction jobs. "
        "Actual extraction runs via worker.py using the V3 pipeline."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://proves-curation-dashboard.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="2.0.0",
        worker_hint="Run 'python worker.py --daemon' to process queued URLs",
    )


@app.post("/extract", response_model=ExtractResponse)
async def queue_extraction(request: ExtractRequest):
    """
    Queue URLs for extraction.

    This endpoint ONLY inserts URLs into the urls_to_process table.
    The actual extraction is done by worker.py which:
    1. Polls urls_to_process for pending URLs
    2. Uses task_builder.py for FRAMES-aware prompts
    3. Invokes agent_v3.graph (Extractor → Validator → Storage)

    This ensures all extractions use the correct V3 pipeline with
    FRAMES methodology, 7-question checklist, and epistemic defaults.
    """
    if not request.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    if len(request.urls) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 URLs per request"
        )

    task_id = str(uuid.uuid4())
    urls_queued = 0

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            for url in request.urls:
                try:
                    cur.execute("""
                        INSERT INTO urls_to_process (url, status, quality_score, quality_reason)
                        VALUES (%s, 'pending', %s, %s)
                        ON CONFLICT (url) DO UPDATE SET
                            status = 'pending',
                            quality_score = EXCLUDED.quality_score,
                            quality_reason = EXCLUDED.quality_reason
                    """, (url, request.quality_score, f"Queued via API (task: {task_id})"))
                    urls_queued += 1
                except Exception as e:
                    print(f"[/extract] Failed to insert URL {url}: {e}")
            conn.commit()
        conn.close()

        return ExtractResponse(
            task_id=task_id,
            status="queued",
            message=(
                f"Queued {urls_queued} URL(s) for extraction. "
                f"Run 'python worker.py' to process."
            ),
            urls_queued=urls_queued,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract/job", response_model=ExtractResponse)
async def acknowledge_job(request: ExtractJobRequest):
    """
    Acknowledge a crawl job from the dashboard.

    The job stays in 'pending' status for worker.py to pick up.
    For url_list sources, we insert URLs into urls_to_process.

    The actual extraction is done by worker.py using the V3 pipeline.
    """
    try:
        conn = get_db_connection()

        # Get job details
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, source_id, status
                FROM crawl_jobs
                WHERE id = %s
            """, (request.job_id,))
            job_row = cur.fetchone()

        if not job_row:
            conn.close()
            raise HTTPException(status_code=404, detail="Job not found")

        job = {"id": job_row[0], "source_id": job_row[1], "status": job_row[2]}

        if job["status"] not in ("pending", "crawling"):
            conn.close()
            raise HTTPException(
                status_code=400,
                detail=f"Job already {job['status']}"
            )

        # Get source config
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, source_type, source_config
                FROM team_sources
                WHERE id = %s
            """, (job["source_id"],))
            source_row = cur.fetchone()

        if not source_row:
            conn.close()
            raise HTTPException(status_code=404, detail="Source not found")

        source = {
            "id": source_row[0],
            "name": source_row[1],
            "source_type": source_row[2],
            "source_config": source_row[3] or {}
        }
        source_type = source.get("source_type")
        source_config = source.get("source_config", {})

        # For url_list sources, insert URLs into urls_to_process
        urls_queued = 0
        if source_type == "url_list":
            urls = source_config.get("urls", [])
            with conn.cursor() as cur:
                for url in urls:
                    try:
                        cur.execute("""
                            INSERT INTO urls_to_process (url, status, quality_score, quality_reason)
                            VALUES (%s, 'pending', 0.8, %s)
                            ON CONFLICT (url) DO UPDATE SET
                                status = 'pending',
                                quality_score = EXCLUDED.quality_score,
                                quality_reason = EXCLUDED.quality_reason
                        """, (url, f"From source: {source['name']}"))
                        urls_queued += 1
                    except Exception as e:
                        print(f"[/extract/job] Failed to insert URL {url}: {e}")
                conn.commit()

        conn.close()

        print(
            f"[/extract/job] Job {request.job_id} acknowledged. "
            f"Source type: {source_type}, URLs queued: {urls_queued}"
        )

        return ExtractResponse(
            task_id=request.job_id,
            status="pending",
            message=(
                f"Job queued for {source_type} processor. "
                f"Run 'python worker.py' to process."
            ),
            urls_queued=urls_queued,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a discovery task."""
    if task_id not in running_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = running_tasks[task_id]
    return {
        "task_id": task_id,
        "status": task["status"],
        "started_at": task.get("started_at"),
        "completed_at": task.get("completed_at"),
        "discovered": task.get("discovered", 0),
        "error": task.get("error"),
    }


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get status of a crawl job from database."""
    try:
        conn = get_db_connection()

        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, status, items_found, items_processed, items_failed,
                       error_message, started_at, completed_at
                FROM crawl_jobs
                WHERE id = %s
            """, (job_id,))
            row = cur.fetchone()

        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Job not found")

        return JobStatusResponse(
            job_id=str(row[0]),
            status=row[1],
            items_found=row[2] or 0,
            items_processed=row[3] or 0,
            items_failed=row[4] or 0,
            error_message=row[5],
            started_at=str(row[6]) if row[6] else None,
            completed_at=str(row[7]) if row[7] else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/discover", response_model=CrawlDiscoveryResponse)
async def discover_urls(
    request: CrawlDiscoveryRequest,
    background_tasks: BackgroundTasks
):
    """
    Discover good documentation URLs from a website.

    Uses SmartWebFetchAgent to find quality pages (score >= 0.65)
    and extract context hints (components, interfaces, keywords).

    URLs are added to urls_to_process. Run worker.py to extract.
    """
    if not request.starting_url:
        raise HTTPException(status_code=400, detail="Starting URL required")

    if request.max_pages < 1 or request.max_pages > 200:
        raise HTTPException(
            status_code=400,
            detail="max_pages must be between 1 and 200"
        )

    task_id = str(uuid.uuid4())

    background_tasks.add_task(
        run_discovery_task,
        task_id,
        request.starting_url,
        request.max_pages,
        request.instructions,
    )

    return CrawlDiscoveryResponse(
        task_id=task_id,
        status="queued",
        starting_url=request.starting_url,
        max_pages=request.max_pages,
    )


@app.get("/discover/pending")
async def get_pending_urls():
    """
    Get URLs that have been discovered and are pending extraction.

    Returns URLs from urls_to_process with status='pending'.
    """
    try:
        conn = get_db_connection()

        with conn.cursor() as cur:
            cur.execute("""
                SELECT url, quality_score, quality_reason,
                       preview_components, preview_interfaces,
                       preview_keywords, preview_summary
                FROM urls_to_process
                WHERE status = 'pending'
                ORDER BY quality_score DESC
                LIMIT 100
            """)
            rows = cur.fetchall()

        conn.close()

        return {
            "count": len(rows),
            "urls": [
                {
                    "url": row[0],
                    "quality_score": row[1],
                    "quality_reason": row[2],
                    "components": row[3] or [],
                    "interfaces": row[4] or [],
                    "keywords": row[5] or [],
                    "summary": row[6] or "",
                }
                for row in rows
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/queue/stats")
async def get_queue_stats():
    """Get statistics about the extraction queue."""
    try:
        conn = get_db_connection()

        with conn.cursor() as cur:
            # Get URL stats
            cur.execute("""
                SELECT status, COUNT(*) as count
                FROM urls_to_process
                GROUP BY status
            """)
            url_stats = {row[0]: row[1] for row in cur.fetchall()}

            # Get job stats
            cur.execute("""
                SELECT status, COUNT(*) as count
                FROM crawl_jobs
                GROUP BY status
            """)
            job_stats = {row[0]: row[1] for row in cur.fetchall()}

        conn.close()

        return {
            "urls": url_stats,
            "jobs": job_stats,
            "total_pending": url_stats.get("pending", 0),
            "hint": "Run 'python worker.py --daemon' to process queue",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
