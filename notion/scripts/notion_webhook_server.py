"""
Notion Webhook Server - FastAPI with PostgreSQL Polling

Bidirectional Notion sync following Neon and Notion documentation:
1. Database polling → Check for unsynced items → Push to Notion
2. Notion updates → Webhook → This server → Update PostgreSQL

Based on:
- Neon: https://neon.com/guides/fastapi-webhooks (polling pattern)
- Notion: https://developers.notion.com/docs/webhooks (HTTP webhooks)

Usage:
    # Development (with ngrok):
    python notion_webhook_server.py

    # In another terminal:
    ngrok http 8000

    # Copy ngrok URL and configure in Notion webhook settings
"""

import os
import hmac
import hashlib
import json
import asyncio
from datetime import datetime
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from http import HTTPStatus
from dotenv import load_dotenv
import psycopg

# Load environment
load_dotenv()

# Import our Notion sync modules
from src.curator.notion_sync import NotionSync
from src.curator.suggestion_sync import SuggestionSync

# Initialize Notion sync
notion_sync = NotionSync()
suggestion_sync = SuggestionSync()

# Database URL
DATABASE_URL = os.getenv('NEON_DATABASE_URL')

# Webhook secret (from Notion webhook configuration)
WEBHOOK_SECRET = os.getenv('NOTION_WEBHOOK_SECRET', '')

# Background task for database polling
polling_task = None


# ============================================================================
# POSTGRESQL POLLING (Following Neon's documented pattern)
# ============================================================================

async def poll_for_unsynced_items():
    """
    Background task that polls database for unsynced items.

    Following Neon's recommended polling pattern from:
    https://neon.com/guides/fastapi-webhooks

    Checks every 10 seconds for:
    - Unsynced extractions
    - Unsynced errors
    - Unsynced reports
    - Unsynced suggestions
    """
    print("\n" + "="*80)
    print("Starting database polling for unsynced items...")
    print("Poll interval: 10 seconds")
    print("="*80 + "\n")

    try:
        while True:
            # Poll for unsynced extractions
            conn = psycopg.connect(DATABASE_URL)
            with conn.cursor() as cur:
                # Get unsynced extractions
                cur.execute("""
                    SELECT extraction_id
                    FROM staging_extractions
                    WHERE notion_page_id IS NULL
                    LIMIT 10
                """)
                extraction_ids = [row[0] for row in cur.fetchall()]

                # Get unsynced errors
                cur.execute("""
                    SELECT id
                    FROM curator_errors
                    WHERE notion_page_id IS NULL
                    LIMIT 10
                """)
                error_ids = [row[0] for row in cur.fetchall()]

                # Get unsynced reports
                cur.execute("""
                    SELECT id
                    FROM curator_reports
                    WHERE notion_page_id IS NULL
                    LIMIT 10
                """)
                report_ids = [row[0] for row in cur.fetchall()]

                # Get unsynced suggestions
                cur.execute("""
                    SELECT suggestion_id
                    FROM improvement_suggestions
                    WHERE notion_page_id IS NULL
                    LIMIT 10
                """)
                suggestion_ids = [row[0] for row in cur.fetchall()]

            conn.close()

            # Sync unsynced items
            for extraction_id in extraction_ids:
                await sync_extraction_to_notion(extraction_id)

            for error_id in error_ids:
                await sync_error_to_notion(error_id)

            for report_id in report_ids:
                await sync_report_to_notion(report_id)

            for suggestion_id in suggestion_ids:
                await sync_suggestion_to_notion(suggestion_id)

            # Wait 10 seconds before next poll
            await asyncio.sleep(10)

    except Exception as e:
        print(f"❌ Error in polling loop: {e}")


async def sync_extraction_to_notion(extraction_id: str):
    """Fetch extraction from DB and push to Notion"""
    try:
        conn = psycopg.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    extraction_id, candidate_type, candidate_key, status,
                    confidence_score, confidence_reason, ecosystem, evidence,
                    created_at, lineage_verified, lineage_confidence,
                    candidate_payload, snapshot_id, evidence_type
                FROM staging_extractions
                WHERE extraction_id = %s::uuid
            """, (extraction_id,))

            row = cur.fetchone()

        conn.close()

        if not row:
            print(f"⚠ Extraction {extraction_id} not found")
            return

        # Build extraction data
        extraction_data = {
            'extraction_id': row[0],
            'candidate_type': row[1],
            'candidate_key': row[2],
            'status': row[3],
            'confidence_score': row[4],
            'confidence_reason': row[5],
            'ecosystem': row[6],
            'evidence': row[7],
            'created_at': row[8],
            'lineage_verified': row[9],
            'lineage_confidence': row[10],
            'candidate_payload': row[11],
            'snapshot_id': row[12],
            'evidence_type': row[13]
        }

        # Push to Notion
        notion_page_id = notion_sync.sync_extraction(extraction_data)

        # Mark as synced in database
        conn = psycopg.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT mark_extraction_synced(%s::uuid, %s)",
                (extraction_id, notion_page_id)
            )
            conn.commit()
        conn.close()

        print(f"✓ Extraction {extraction_id} synced to Notion: {notion_page_id}")

    except Exception as e:
        print(f"❌ Failed to sync extraction {extraction_id}: {e}")

        # Mark sync failure
        conn = psycopg.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT mark_sync_failed('staging_extractions', %s, %s)",
                (extraction_id, str(e))
            )
            conn.commit()
        conn.close()


async def sync_error_to_notion(error_id: int):
    """Fetch error from DB and push to Notion"""
    try:
        conn = psycopg.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, url, error_message, stack_trace, created_at
                FROM curator_errors
                WHERE id = %s
            """, (error_id,))

            row = cur.fetchone()

        conn.close()

        if not row:
            print(f"⚠ Error {error_id} not found")
            return

        # Push to Notion
        notion_page_id = notion_sync.log_error(row[1], row[2], row[3])

        # Mark as synced
        conn = psycopg.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT mark_error_synced(%s, %s)",
                (error_id, notion_page_id)
            )
            conn.commit()
        conn.close()

        print(f"✓ Error {error_id} synced to Notion: {notion_page_id}")

    except Exception as e:
        print(f"❌ Failed to sync error {error_id}: {e}")

        conn = psycopg.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT mark_sync_failed('curator_errors', %s, %s)",
                (str(error_id), str(e))
            )
            conn.commit()
        conn.close()


async def sync_report_to_notion(report_id: int):
    """Fetch report from DB and push to Notion"""
    try:
        conn = psycopg.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id, run_date, urls_processed, urls_successful, urls_failed,
                    total_extractions, summary, langsmith_trace_url
                FROM curator_reports
                WHERE id = %s
            """, (report_id,))

            row = cur.fetchone()

        conn.close()

        if not row:
            print(f"⚠ Report {report_id} not found")
            return

        # Build report data
        report_data = {
            'run_date': row[1].strftime('%Y-%m-%d %H:%M:%S'),
            'urls_processed': row[2],
            'successful': row[3],
            'failed': row[4],
            'total_extractions': row[5],
            'summary': row[6],
            'langsmith_trace': row[7]
        }

        # Push to Notion
        notion_page_id = notion_sync.create_run_report(report_data)

        # Mark as synced
        conn = psycopg.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT mark_report_synced(%s, %s)",
                (report_id, notion_page_id)
            )
            conn.commit()
        conn.close()

        print(f"✓ Report {report_id} synced to Notion: {notion_page_id}")

    except Exception as e:
        print(f"❌ Failed to sync report {report_id}: {e}")

        conn = psycopg.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT mark_sync_failed('curator_reports', %s, %s)",
                (str(report_id), str(e))
            )
            conn.commit()
        conn.close()


async def sync_suggestion_to_notion(suggestion_id: str):
    """Fetch suggestion from DB and push to Notion"""
    try:
        conn = psycopg.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    suggestion_id, category, title, evidence,
                    current_state, proposed_change, impact_count,
                    confidence, extraction_ids, status, created_at
                FROM improvement_suggestions
                WHERE suggestion_id = %s::uuid
            """, (suggestion_id,))

            row = cur.fetchone()

        conn.close()

        if not row:
            print(f"⚠ Suggestion {suggestion_id} not found")
            return

        # Build suggestion data
        suggestion_data = {
            'suggestion_id': row[0],
            'category': row[1],
            'title': row[2],
            'evidence': row[3],
            'current_state': row[4],
            'proposed_change': row[5],
            'impact_count': row[6],
            'confidence': row[7],
            'extraction_ids': row[8],
            'status': row[9],
            'created_at': row[10]
        }

        # Push to Notion
        notion_page_id = suggestion_sync.sync_suggestion(suggestion_data)

        print(f"✓ Suggestion {suggestion_id} synced to Notion: {notion_page_id}")

    except Exception as e:
        print(f"❌ Failed to sync suggestion {suggestion_id}: {e}")
        import traceback
        traceback.print_exc()


async def notify_queue_empty(data: Dict[str, Any]):
    """Send notification to Notion that URL queue is empty"""
    try:
        # Create a special notification page or use a dedicated database
        # For now, create an error-like notification
        message = data.get('message', 'URL queue is empty')
        timestamp = data.get('timestamp', datetime.now().isoformat())

        notion_page_id = notion_sync.log_error(
            url="SYSTEM_NOTIFICATION",
            error_message=f"⚠️ Queue Empty: {message}",
            stack_trace=f"Timestamp: {timestamp}\n\nAction required: Run find_good_urls.py to refill the queue"
        )

        print(f"✓ Queue empty notification sent to Notion: {notion_page_id}")

    except Exception as e:
        print(f"❌ Failed to send queue empty notification: {e}")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global polling_task

    # Startup: Start database polling
    polling_task = asyncio.create_task(poll_for_unsynced_items())

    yield

    # Shutdown: Cancel polling
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Curator Notion Webhook Server",
    description="Bidirectional sync between Neon database and Notion",
    version="2.0.0",
    lifespan=lifespan
)


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify Notion webhook signature using HMAC-SHA256"""
    print(f"DEBUG: WEBHOOK_SECRET = '{WEBHOOK_SECRET}'")
    print(f"DEBUG: WEBHOOK_SECRET is empty: {not WEBHOOK_SECRET}")

    if not WEBHOOK_SECRET:
        print("WARNING: NOTION_WEBHOOK_SECRET not set - skipping signature verification")
        return True

    expected_signature = f"sha256={hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()}"
    result = hmac.compare_digest(expected_signature, signature)
    print(f"DEBUG: Signature verification result: {result}")
    print(f"DEBUG: Expected: {expected_signature}")
    print(f"DEBUG: Received: {signature}")
    return result


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Curator Notion Webhook Server",
        "version": "2.0.0",
        "features": [
            "PostgreSQL LISTEN (DB → Notion)",
            "Notion Webhooks (Notion → DB)",
            "Bidirectional sync with tracking"
        ],
        "timestamp": datetime.now().isoformat()
    }


@app.post("/webhook/notion")
async def notion_webhook(request: Request):
    """
    Webhook endpoint for Notion events.

    Receives status updates from Notion and syncs back to database.
    """
    body = await request.body()
    signature = request.headers.get('X-Notion-Signature', '')

    if not verify_signature(body, signature):
        return JSONResponse(
            status_code=HTTPStatus.UNAUTHORIZED,
            content={"error": "Invalid signature"}
        )

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content={"error": "Invalid JSON"}
        )

    # Handle verification challenge
    if 'verification_token' in payload:
        print(f"Verification token: {payload['verification_token']}")
        return JSONResponse(content={"status": "verification_token_received"})

    # Handle page updates
    event_type = payload.get('type')
    print(f"DEBUG: Received webhook with event_type: {event_type}")
    print(f"DEBUG: Full payload keys: {list(payload.keys())}")

    if event_type in ['page.content_updated', 'page.properties_updated']:
        return await handle_notion_page_updated(payload)

    print(f"DEBUG: Event type '{event_type}' not handled, returning acknowledged")
    return JSONResponse(content={"status": "event_acknowledged"})


async def handle_notion_page_updated(payload: Dict[str, Any]) -> JSONResponse:
    """Handle page updates from Notion (status changes)"""
    print(f"\n{'='*80}")
    print("HANDLER CALLED: handle_notion_page_updated")
    print(f"DEBUG: payload['data'] = {payload.get('data', {})}")
    print(f"DEBUG: payload['entity'] = {payload.get('entity', {})}")
    page_id = payload.get('data', {}).get('id') or payload.get('entity', {}).get('id')
    print(f"DEBUG: page_id = {page_id}")

    if not page_id:
        print("ERROR: No page_id found, returning early")
        return JSONResponse(content={"status": "no_page_id"})

    try:
        # Fetch page from Notion
        page = notion_sync.client.pages.retrieve(page_id)
        props = page['properties']

        # Determine if this is an extraction or a suggestion page
        extraction_id_prop = props.get('Extraction ID', {})
        suggestion_id_prop = props.get('Suggestion ID', {})

        if extraction_id_prop.get('rich_text'):
            # Handle extraction page
            return await handle_extraction_page_updated(page_id, props)
        elif suggestion_id_prop.get('rich_text'):
            # Handle suggestion page
            return await handle_suggestion_page_updated(page_id, props)
        else:
            return JSONResponse(content={"status": "unknown_page_type"})

    except Exception as e:
        print(f"❌ Error handling Notion update: {e}")
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )


async def handle_extraction_page_updated(page_id: str, props: Dict[str, Any]) -> JSONResponse:
    """Handle extraction page updates from Notion"""
    try:
        # Extract extraction ID
        extraction_id_prop = props.get('Extraction ID', {})
        if not extraction_id_prop.get('rich_text'):
            return JSONResponse(content={"status": "no_extraction_id"})

        extraction_id = extraction_id_prop['rich_text'][0]['plain_text']

        # Track review decision for database update
        db_review_decision = None

        # Check for Accept/Reject changes (takes priority)
        review_decision_prop = props.get('Accept/Reject', {})
        if review_decision_prop.get('select'):
            review_decision = review_decision_prop['select']['name']

            if review_decision == 'Approved':
                db_status = 'accepted'
                db_review_decision = 'approve'
                print(f"✓ Accept/Reject: Approved → setting status to 'accepted'")

                # Auto-update Notion Status field to match
                notion_sync.client.pages.update(
                    page_id=page_id,
                    properties={"Status": {"select": {"name": "Approved"}}}
                )
            elif review_decision == 'Rejected':
                db_status = 'rejected'
                db_review_decision = 'reject'
                print(f"✓ Accept/Reject: Rejected → setting status to 'rejected'")

                # Auto-update Notion Status field to match
                notion_sync.client.pages.update(
                    page_id=page_id,
                    properties={"Status": {"select": {"name": "Rejected"}}}
                )
            elif review_decision == 'Modified':
                db_status = 'flagged'
                db_review_decision = 'modified'
                print(f"✓ Accept/Reject: Modified → setting status to 'flagged' for review")

                # Auto-update Notion Status field to match
                notion_sync.client.pages.update(
                    page_id=page_id,
                    properties={"Status": {"select": {"name": "Needs Review"}}}
                )
            else:
                # Fall back to Status field
                status_prop = props.get('Status', {})
                if not status_prop.get('select'):
                    return JSONResponse(content={"status": "no_status"})
                notion_status = status_prop['select']['name']
                status_map = {
                    'Pending': 'pending',
                    'Approved': 'accepted',
                    'Rejected': 'rejected',
                    'Needs Review': 'flagged'
                }
                db_status = status_map.get(notion_status, 'pending')
        else:
            # No Review Decision, use Status field
            status_prop = props.get('Status', {})
            if not status_prop.get('select'):
                return JSONResponse(content={"status": "no_status"})

            notion_status = status_prop['select']['name']

            # Map to database status
            status_map = {
                'Pending': 'pending',
                'Approved': 'accepted',
                'Rejected': 'rejected',
                'Needs Review': 'flagged'
            }

            db_status = status_map.get(notion_status, 'pending')

        # Update database with review tracking
        success = notion_sync.update_database_status(extraction_id, db_status, db_review_decision)

        if success:
            print(f"✓ Extraction {extraction_id} status updated to {db_status}")
            return JSONResponse(content={
                "status": "success",
                "extraction_id": extraction_id,
                "new_status": db_status
            })
        else:
            return JSONResponse(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                content={"error": "Database update failed"}
            )

    except Exception as e:
        print(f"❌ Error handling extraction update: {e}")
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )


async def handle_suggestion_page_updated(page_id: str, props: Dict[str, Any]) -> JSONResponse:
    """Handle suggestion page updates from Notion"""
    try:
        # Extract suggestion ID
        suggestion_id_prop = props.get('Suggestion ID', {})
        if not suggestion_id_prop.get('rich_text'):
            return JSONResponse(content={"status": "no_suggestion_id"})

        suggestion_id = suggestion_id_prop['rich_text'][0]['plain_text']

        # Track review decision for database update
        db_review_decision = None

        # Check for Accept/Reject changes (takes priority)
        review_decision_prop = props.get('Accept/Reject', {})
        if review_decision_prop.get('select'):
            review_decision = review_decision_prop['select']['name']

            if review_decision == 'Approved':
                db_status = 'approved'
                db_review_decision = 'approve'
                print(f"✓ Accept/Reject: Approved → setting status to 'approved'")

                # Auto-update Notion Status field to match
                suggestion_sync.client.pages.update(
                    page_id=page_id,
                    properties={"Status": {"select": {"name": "Approved"}}}
                )
            elif review_decision == 'Rejected':
                db_status = 'rejected'
                db_review_decision = 'reject'
                print(f"✓ Accept/Reject: Rejected → setting status to 'rejected'")

                # Auto-update Notion Status field to match
                suggestion_sync.client.pages.update(
                    page_id=page_id,
                    properties={"Status": {"select": {"name": "Rejected"}}}
                )
            elif review_decision == 'Modified':
                db_status = 'needs_review'
                db_review_decision = 'modified'
                print(f"✓ Accept/Reject: Modified → setting status to 'needs_review'")

                # Auto-update Notion Status field to match
                suggestion_sync.client.pages.update(
                    page_id=page_id,
                    properties={"Status": {"select": {"name": "Needs Review"}}}
                )
            else:
                # Fall back to Status field
                status_prop = props.get('Status', {})
                if not status_prop.get('select'):
                    return JSONResponse(content={"status": "no_status"})
                notion_status = status_prop['select']['name']
                status_map = {
                    'Pending': 'pending',
                    'Approved': 'approved',
                    'Rejected': 'rejected',
                    'Needs Review': 'needs_review',
                    'Implemented': 'implemented'
                }
                db_status = status_map.get(notion_status, 'pending')
        else:
            # No Review Decision, use Status field
            status_prop = props.get('Status', {})
            if not status_prop.get('select'):
                return JSONResponse(content={"status": "no_status"})

            notion_status = status_prop['select']['name']

            # Map to database status
            status_map = {
                'Pending': 'pending',
                'Approved': 'approved',
                'Rejected': 'rejected',
                'Needs Review': 'needs_review',
                'Implemented': 'implemented'
            }

            db_status = status_map.get(notion_status, 'pending')

        # Update database with review tracking
        success = suggestion_sync.update_suggestion_status(suggestion_id, db_status, db_review_decision)

        if success:
            print(f"✓ Suggestion {suggestion_id} status updated to {db_status}")
            return JSONResponse(content={
                "status": "success",
                "suggestion_id": suggestion_id,
                "new_status": db_status
            })
        else:
            return JSONResponse(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                content={"error": "Database update failed"}
            )

    except Exception as e:
        print(f"❌ Error handling suggestion update: {e}")
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )


@app.get("/status")
async def status():
    """Get sync status from database"""
    try:
        conn = psycopg.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    item_type,
                    COUNT(*) as count,
                    MIN(created_at) as oldest_unsynced
                FROM notion_sync_status
                GROUP BY item_type
            """)
            rows = cur.fetchall()

        conn.close()

        status_data = {
            row[0]: {
                "unsynced_count": row[1],
                "oldest_unsynced": row[2].isoformat() if row[2] else None
            }
            for row in rows
        }

        return JSONResponse(content=status_data)

    except Exception as e:
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )


if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*80)
    print("CURATOR NOTION WEBHOOK SERVER v2.0")
    print("="*80)
    print("\nFeatures:")
    print("  ✓ Database polling for unsynced items (every 10s)")
    print("  ✓ Notion webhook receiver for status updates")
    print("  ✓ Automatic bidirectional sync")
    print("\nPattern:")
    print("  Following Neon + Notion documentation:")
    print("  - Database → Notion: Poll for notion_page_id IS NULL")
    print("  - Notion → Database: HTTP webhook on /webhook/notion")
    print("\nStarting server on http://localhost:8000")
    print("\nEndpoints:")
    print("  GET  /              - Health check")
    print("  GET  /status        - View sync status")
    print("  POST /webhook/notion - Notion webhook (configure in Notion)")
    print("\nTo expose publicly with ngrok:")
    print("  ngrok http 8000")
    print("\nThen configure the ngrok URL in Notion integration settings")
    print("="*80 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
