#!/usr/bin/env python3
"""
PROVES Extraction API - FastAPI service for triggering extractions.

Endpoints:
    POST /extract - Trigger extraction for URLs
    POST /extract/job - Trigger extraction from a crawl job
    GET /jobs/{job_id} - Get job status
    GET /health - Health check

Run locally:
    uvicorn app:app --reload --port 8080

Run with Docker:
    docker build -t proves-extraction-api .
    docker run -p 8080:8080 --env-file .env proves-extraction-api
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
from supabase import create_client, Client

# =============================================================================
# CONFIGURATION
# =============================================================================

# Get the extraction pipeline path
# In Docker: /app/app.py, /app/production/, /app/production/Version 3/
# Locally: extraction-api/app.py, production/, production/Version 3/
API_DIR = Path(__file__).parent
PROJECT_ROOT = API_DIR.parent if (API_DIR.parent / 'production').exists() else API_DIR
PRODUCTION_DIR = PROJECT_ROOT / 'production'
VERSION3_DIR = PRODUCTION_DIR / 'Version 3'

# Add to path for imports
sys.path.insert(0, str(VERSION3_DIR))
sys.path.insert(0, str(PRODUCTION_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
# Try to load .env from project root (Docker mounts env vars instead)
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Lazy import of extraction graph (heavy dependencies)
_graph = None

def get_graph():
    """Lazy load the extraction graph to speed up startup."""
    global _graph
    if _graph is None:
        from agent_v3 import graph
        _graph = graph
    return _graph


# =============================================================================
# DATABASE / SUPABASE
# =============================================================================

def _get_db_url() -> str:
    """Get direct database URL (without pgbouncer parameter)."""
    return (
        os.environ.get('DIRECT_URL') or
        os.environ.get('PROVES_DATABASE_URL') or
        os.environ.get('DATABASE_URL')
    )


def get_supabase_client() -> Client:
    """Create Supabase client."""
    url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL') or os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")

    return create_client(url, key)


# =============================================================================
# MODELS
# =============================================================================

class ExtractRequest(BaseModel):
    """Request to extract from URLs."""
    urls: List[str]
    source_id: Optional[str] = None  # Optional link to team_sources

class ExtractJobRequest(BaseModel):
    """Request to process a crawl job."""
    job_id: str

class CrawlDiscoveryRequest(BaseModel):
    """Request to discover URLs from a website."""
    starting_url: str
    max_pages: int = 50
    instructions: Optional[str] = None  # Custom instructions for crawl focus

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

class CrawlDiscoveryResponse(BaseModel):
    """Response from crawl discovery."""
    task_id: str
    status: str
    starting_url: str
    max_pages: int

class DiscoveredUrl(BaseModel):
    """A discovered URL with quality info."""
    url: str
    quality_score: float
    quality_reason: str
    components: List[str]
    interfaces: List[str]
    keywords: List[str]
    summary: str


# =============================================================================
# BACKGROUND EXTRACTION TASK
# =============================================================================

# Track running tasks
running_tasks = {}

async def run_extraction_task(task_id: str, urls: List[str], source_id: Optional[str] = None):
    """
    Background task to run extraction on URLs.
    """
    running_tasks[task_id] = {
        'status': 'running',
        'started_at': datetime.utcnow().isoformat(),
        'urls': urls,
        'processed': 0,
        'failed': 0,
        'results': []
    }

    graph = get_graph()
    supabase = get_supabase_client()

    for i, url in enumerate(urls):
        if running_tasks.get(task_id, {}).get('status') == 'cancelled':
            break

        try:
            # Build extraction task
            task_prompt = f"""
You are the curator agent for the PROVES Library.

YOUR MISSION: Extract architecture from this documentation page.

URL: {url}

EXTRACTION FOCUS (use FRAMES methodology):
- COMPONENTS: What modules/units exist? (hardware, software, subsystems)
- INTERFACES: Where do they connect? (ports, buses, protocols)
- FLOWS: What moves through connections? (data, commands, power, signals)
- DEPENDENCIES: Component-to-component relationships

Store ALL extractions in staging_extractions. Work autonomously.
"""

            thread_id = f"api-{task_id}-{uuid.uuid4().hex[:8]}"
            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 100
            }

            # Run extraction (this is synchronous, runs in thread pool)
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: graph.invoke(
                    {"messages": [{"role": "user", "content": task_prompt}]},
                    config
                )
            )

            running_tasks[task_id]['processed'] += 1
            running_tasks[task_id]['results'].append({
                'url': url,
                'status': 'success'
            })

        except Exception as e:
            running_tasks[task_id]['failed'] += 1
            running_tasks[task_id]['results'].append({
                'url': url,
                'status': 'error',
                'error': str(e)
            })

    # Mark complete
    running_tasks[task_id]['status'] = 'completed'
    running_tasks[task_id]['completed_at'] = datetime.utcnow().isoformat()

    # If linked to a source, update the crawl job
    if source_id:
        try:
            supabase.rpc('complete_crawl_job', {
                'p_job_id': source_id,
                'p_status': 'completed',
                'p_items_found': len(urls),
                'p_items_processed': running_tasks[task_id]['processed'],
                'p_items_failed': running_tasks[task_id]['failed']
            }).execute()
        except Exception as e:
            print(f"Warning: Failed to update crawl job: {e}")


async def run_discovery_task(task_id: str, starting_url: str, max_pages: int, instructions: Optional[str] = None):
    """
    Background task to discover good URLs from a website.
    Uses the SmartWebFetchAgent from find_good_urls.py.
    """
    running_tasks[task_id] = {
        'status': 'running',
        'started_at': datetime.utcnow().isoformat(),
        'starting_url': starting_url,
        'max_pages': max_pages,
        'discovered': 0,
        'urls': []
    }

    try:
        # Import the smart crawler
        from scripts.find_good_urls import SmartWebFetchAgent

        agent = SmartWebFetchAgent()

        # Run discovery in thread pool (it's synchronous)
        pages_added = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: agent.crawl([starting_url], max_pages=max_pages)
        )

        running_tasks[task_id]['discovered'] = pages_added
        running_tasks[task_id]['status'] = 'completed'
        running_tasks[task_id]['completed_at'] = datetime.utcnow().isoformat()

    except Exception as e:
        running_tasks[task_id]['status'] = 'failed'
        running_tasks[task_id]['error'] = str(e)
        running_tasks[task_id]['completed_at'] = datetime.utcnow().isoformat()
        print(f"Discovery task failed: {e}")


# =============================================================================
# FASTAPI APP
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("PROVES Extraction API starting...")
    yield
    # Shutdown
    print("PROVES Extraction API shutting down...")


app = FastAPI(
    title="PROVES Extraction API",
    description="API for triggering extraction pipeline jobs",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - allow dashboard to call us
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
        version="1.0.0"
    )


@app.post("/extract", response_model=ExtractResponse)
async def trigger_extraction(
    request: ExtractRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger extraction for a list of URLs.

    The extraction runs in the background. Use the returned task_id
    to check status via GET /tasks/{task_id}.
    """
    if not request.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")

    if len(request.urls) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 URLs per request")

    task_id = str(uuid.uuid4())

    # Start background extraction
    background_tasks.add_task(
        run_extraction_task,
        task_id,
        request.urls,
        request.source_id
    )

    return ExtractResponse(
        task_id=task_id,
        status="queued",
        message=f"Extraction started for {len(request.urls)} URL(s)",
        urls_queued=len(request.urls)
    )


@app.post("/extract/job", response_model=ExtractResponse)
async def trigger_job_extraction(
    request: ExtractJobRequest,
    background_tasks: BackgroundTasks
):
    """
    Process a crawl job from the dashboard.

    Claims the job, gets URLs from source config, and runs extraction.
    """
    try:
        supabase = get_supabase_client()

        # Get job details
        result = supabase.from_('crawl_jobs').select(
            'id, source_id, status'
        ).eq('id', request.job_id).single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Job not found")

        job = result.data

        if job['status'] not in ('pending', 'crawling'):
            raise HTTPException(
                status_code=400,
                detail=f"Job already {job['status']}"
            )

        # Get source config
        source_result = supabase.from_('team_sources').select(
            'source_type, source_config'
        ).eq('id', job['source_id']).single().execute()

        if not source_result.data:
            raise HTTPException(status_code=404, detail="Source not found")

        source = source_result.data
        urls = source.get('source_config', {}).get('urls', [])

        if not urls:
            raise HTTPException(
                status_code=400,
                detail="No URLs in source configuration"
            )

        # Update job status to crawling
        supabase.from_('crawl_jobs').update({
            'status': 'crawling',
            'started_at': datetime.utcnow().isoformat()
        }).eq('id', request.job_id).execute()

        task_id = str(uuid.uuid4())

        # Start background extraction
        background_tasks.add_task(
            run_extraction_task,
            task_id,
            urls,
            request.job_id  # Link to job for completion callback
        )

        return ExtractResponse(
            task_id=task_id,
            status="queued",
            message=f"Processing job {request.job_id} with {len(urls)} URL(s)",
            urls_queued=len(urls)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a running extraction task."""
    if task_id not in running_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = running_tasks[task_id]
    return {
        "task_id": task_id,
        "status": task['status'],
        "started_at": task.get('started_at'),
        "completed_at": task.get('completed_at'),
        "urls_total": len(task.get('urls', [])),
        "processed": task.get('processed', 0),
        "failed": task.get('failed', 0),
        "results": task.get('results', [])[-10:]  # Last 10 results
    }


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get status of a crawl job from Supabase."""
    try:
        supabase = get_supabase_client()

        result = supabase.from_('crawl_jobs').select('*').eq('id', job_id).single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Job not found")

        job = result.data
        return JobStatusResponse(
            job_id=job['id'],
            status=job['status'],
            items_found=job.get('items_found', 0),
            items_processed=job.get('items_processed', 0),
            items_failed=job.get('items_failed', 0),
            error_message=job.get('error_message'),
            started_at=job.get('started_at'),
            completed_at=job.get('completed_at')
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

    Uses the smart crawler to find quality pages (score >= 0.65) and
    extract context hints (components, interfaces, keywords).

    The discovery runs in the background. Use GET /tasks/{task_id} to check status.
    """
    if not request.starting_url:
        raise HTTPException(status_code=400, detail="Starting URL required")

    if request.max_pages < 1 or request.max_pages > 200:
        raise HTTPException(status_code=400, detail="max_pages must be between 1 and 200")

    task_id = str(uuid.uuid4())

    # Start background discovery
    background_tasks.add_task(
        run_discovery_task,
        task_id,
        request.starting_url,
        request.max_pages,
        request.instructions
    )

    return CrawlDiscoveryResponse(
        task_id=task_id,
        status="queued",
        starting_url=request.starting_url,
        max_pages=request.max_pages
    )


@app.get("/discover/pending")
async def get_pending_urls():
    """
    Get URLs that have been discovered and are pending extraction.

    Returns URLs from the urls_to_process table with status='pending'.
    """
    try:
        supabase = get_supabase_client()

        result = supabase.from_('urls_to_process').select(
            'url, quality_score, quality_reason, preview_components, preview_interfaces, preview_keywords, preview_summary'
        ).eq('status', 'pending').order('quality_score', desc=True).limit(100).execute()

        return {
            "count": len(result.data),
            "urls": [
                {
                    "url": row['url'],
                    "quality_score": row['quality_score'],
                    "quality_reason": row['quality_reason'],
                    "components": row.get('preview_components', []),
                    "interfaces": row.get('preview_interfaces', []),
                    "keywords": row.get('preview_keywords', []),
                    "summary": row.get('preview_summary', '')
                }
                for row in result.data
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
