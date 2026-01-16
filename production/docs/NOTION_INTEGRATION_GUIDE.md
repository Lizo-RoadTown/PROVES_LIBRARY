# Curator-Agent Notion Integration Guide

## Overview

Event-driven bidirectional sync between Neon PostgreSQL and Notion using database triggers and webhooks.

**Zero changes to `process_extractions.py`** - the curator agent just writes to the database as normal!

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ CURATOR WORKFLOW (Unchanged)                                 │
├─────────────────────────────────────────────────────────────┤
│  process_extractions.py runs normally                        │
│    ↓                                                          │
│  Writes to database tables (staging_extractions, etc.)       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ DATABASE LAYER (Event-Driven Triggers)                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  INSERT into staging_extractions                             │
│    → Trigger → pg_notify('notion_sync_extraction')           │
│                                                               │
│  INSERT into curator_errors                                  │
│    → Trigger → pg_notify('notion_sync_error')                │
│                                                               │
│  INSERT into curator_reports                                 │
│    → Trigger → pg_notify('notion_sync_report')               │
│                                                               │
│  urls_to_process queue empty                                 │
│    → Trigger → pg_notify('notion_queue_empty')               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ WEBHOOK SERVER (notion_webhook_server.py)                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  PostgreSQL LISTEN                                           │
│    ↓                                                          │
│  Receives pg_notify events                                   │
│    ↓                                                          │
│  Fetches data from database                                  │
│    ↓                                                          │
│  Pushes to Notion via API                                    │
│    ↓                                                          │
│  Updates database with notion_page_id & notion_synced_at     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ NOTION (Human Review)                                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Human reviews extractions in Notion                         │
│  Changes status: Pending → Approved/Rejected                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ NOTION WEBHOOK (Bidirectional)                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Notion fires webhook on page update                         │
│    ↓                                                          │
│  POST to /webhook/notion                                     │
│    ↓                                                          │
│  Server updates staging_extractions.status in database       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## What We Built

### 1. Database Migration (`migrations/003_add_notion_integration.sql`)

**New Tables:**
- `curator_errors` - Error logging with Notion tracking
- `curator_reports` - Batch completion reports with Notion tracking

**New Columns** (added to `staging_extractions`):
- `notion_page_id` - Links to Notion page
- `notion_synced_at` - Sync timestamp
- `notion_last_sync_attempt` - Last attempt (for debugging)
- `notion_sync_error` - Error message if sync failed

**Triggers:**
- `trigger_notify_new_extraction` - Fires on INSERT to `staging_extractions`
- `trigger_notify_new_error` - Fires on INSERT to `curator_errors`
- `trigger_notify_new_report` - Fires on INSERT to `curator_reports`
- `trigger_check_url_queue` - Fires when URL queue becomes empty

**Helper Functions:**
- `mark_extraction_synced()` - Mark item as synced to Notion
- `mark_error_synced()` - Mark error as synced
- `mark_report_synced()` - Mark report as synced
- `mark_sync_failed()` - Record sync failure

### 2. Webhook Server (`notion_webhook_server.py`)

**Features:**
- PostgreSQL LISTEN on 4 notification channels
- Automatic push to Notion when database events occur
- Webhook receiver for Notion status updates
- Sync status tracking in database
- Error handling and retry logic

**Endpoints:**
- `GET /` - Health check
- `GET /status` - View sync status (unsynced items)
- `POST /webhook/notion` - Notion webhook receiver

### 3. Notion Integration Module (`src/curator/notion_sync.py`)

**Functions:**
- `create_errors_database()` - Create Notion Errors Log database
- `create_extractions_database()` - Create Notion Extractions Review database
- `create_reports_database()` - Create Notion Run Reports database
- `log_error()` - Push error to Notion
- `sync_extraction()` - Push extraction to Notion
- `create_run_report()` - Push completion report to Notion
- `update_database_status()` - Update extraction status from Notion

### 4. Setup Script (`setup_notion.py`)

One-time setup to create the three Notion databases and update `.env`.

## Setup Instructions

### Step 1: Run Database Migration

```bash
cd curator-agent

# Run migration 003
python migrations/run_migration.py 003_add_notion_integration.sql
```

**Expected output:**
```
Running migration: 003_add_notion_integration.sql
Database: ep-empty-morning-af4l9ocx-pooler.c-2.us-west-2.aws.neon.tech/neondb
Migration complete

NOTICE:  Migration 003 completed successfully ✓
NOTICE:    - Created curator_errors table
NOTICE:    - Created curator_reports table
NOTICE:    - Added Notion tracking columns to staging_extractions
NOTICE:    - Created 4 notification triggers
NOTICE:    - Created helper functions for webhook server
```

### Step 2: Create Notion Databases

```bash
python setup_notion.py
```

Follow the prompts to:
1. Provide your Notion parent page ID
2. Script creates three databases
3. `.env` file updated with database IDs

**Expected output:**
```
Creating Notion databases...
✓ Errors DB created: 1234567890abcdef
✓ Extractions DB created: abcdef1234567890
✓ Reports DB created: fedcba0987654321
✓ .env file updated
```

### Step 3: Start Webhook Server

```bash
python notion_webhook_server.py
```

**Expected output:**
```
================================================================================
CURATOR NOTION WEBHOOK SERVER v2.0
================================================================================

Features:
  ✓ PostgreSQL LISTEN for database triggers
  ✓ Notion webhook receiver for status updates
  ✓ Automatic sync with tracking

Starting server on http://localhost:8000
...
================================================================================
Starting PostgreSQL notification listener...
Listening on channels:
  - notion_sync_extraction
  - notion_sync_error
  - notion_sync_report
  - notion_queue_empty
================================================================================

✓ Listening for database notifications...
```

### Step 4: Expose with Ngrok (Development)

In a **new terminal**:

```bash
ngrok http 8000
```

**Copy the HTTPS URL** (looks like: `https://abc123.ngrok.io`)

### Step 5: Configure Notion Webhook

1. Visit https://www.notion.so/profile/integrations
2. Select your integration
3. Go to **Webhooks** tab
4. Click **Create a subscription**
5. Enter webhook URL: `https://YOUR_NGROK_URL.ngrok.io/webhook/notion`
6. Select event type: `page.content_updated`
7. Click **Create subscription**
8. Copy the `verification_token` from webhook server logs
9. Click **Verify** and paste the token
10. Subscription is now active! ✓

## Testing

### Test 1: Extraction Sync (DB → Notion)

Run the curator agent:

```bash
cd curator-agent
python production/process_extractions.py --limit 5
```

**What happens:**
1. Curator extracts data → writes to `staging_extractions`
2. Trigger fires → `pg_notify('notion_sync_extraction')`
3. Webhook server receives notification
4. Server fetches extraction from DB
5. Server pushes to Notion Extractions Database
6. Server marks extraction as synced in DB

**Check webhook server logs:**
```
📬 Notification received: notion_sync_extraction
   Data: {'extraction_id': 'uuid-here', 'action': 'insert'}
✓ Extraction uuid-here synced to Notion: notion-page-id
```

**Check Notion:** New row appears in Extractions Review database!

### Test 2: Status Update (Notion → DB)

1. Open Notion Extractions Review database
2. Find an extraction with status "Pending"
3. Change status to "Approved"
4. Wait ~1 minute for aggregated webhook

**What happens:**
1. Notion fires webhook → `page.content_updated`
2. Webhook hits `/webhook/notion` endpoint
3. Server fetches page from Notion
4. Server extracts new status
5. Server updates `staging_extractions.status` in database

**Check webhook server logs:**
```
✓ Extraction uuid-here status updated to accepted
```

**Check database:**
```sql
SELECT candidate_key, status, updated_at
FROM staging_extractions
WHERE extraction_id = 'uuid-here';

-- Should show status = 'accepted'
```

### Test 3: Error Logging

Manually insert an error:

```sql
INSERT INTO curator_errors (url, error_message, stack_trace)
VALUES (
    'https://test.com',
    'Test error message',
    'Traceback (most recent call last):\n  File...'
);
```

**Check webhook server logs:**
```
📬 Notification received: notion_sync_error
✓ Error 123 synced to Notion: notion-page-id
```

**Check Notion:** New row in Errors Log!

### Test 4: Completion Report

Insert a report:

```sql
INSERT INTO curator_reports (
    urls_processed, urls_successful, urls_failed,
    total_extractions, summary
) VALUES (
    10, 8, 2, 45,
    'Test run completed successfully'
);
```

**Check Notion:** New row in Run Reports!

### Test 5: Queue Empty Notification

Mark all URLs as completed:

```sql
UPDATE urls_to_process SET status = 'completed' WHERE status = 'pending';
```

**Check Notion:** Notification in Errors Log about empty queue!

## Monitoring

### Check Sync Status

```bash
curl http://localhost:8000/status
```

**Response:**
```json
{
  "extraction": {
    "unsynced_count": 5,
    "oldest_unsynced": "2025-12-27T10:30:00Z"
  },
  "error": {
    "unsynced_count": 0,
    "oldest_unsynced": null
  }
}
```

### Database View

```sql
-- View all unsynced items
SELECT * FROM notion_sync_status;

-- Check specific extraction sync status
SELECT
    candidate_key,
    notion_page_id,
    notion_synced_at,
    notion_sync_error
FROM staging_extractions
WHERE extraction_id = 'uuid-here';
```

## Production Deployment

For production (not ngrok):

1. **Deploy webhook server** to a cloud platform:
   - Railway: `railway up`
   - Vercel: `vercel deploy`
   - AWS Lambda: Use Mangum adapter
   - Fly.io: `fly deploy`

2. **Update Notion webhook URL** to permanent URL

3. **Set environment variables** on hosting platform

4. **Enable logging and monitoring**

## Troubleshooting

### Webhook server not receiving notifications

**Check:**
1. Is server running? `curl http://localhost:8000/`
2. Are triggers installed? `SELECT * FROM pg_trigger WHERE tgname LIKE '%notion%';`
3. Database connection? Check `DATABASE_URL` in `.env`

### Notion sync failing

**Check:**
1. Notion API key valid? Test with `setup_notion.py`
2. Database IDs set? Check `.env` for `NOTION_*_DB_ID`
3. Sync errors? `SELECT * FROM notion_sync_status WHERE notion_sync_error IS NOT NULL;`

### Notion webhook not working

**Check:**
1. Webhook subscription active? Check Notion integration settings
2. Ngrok running? Test with `curl https://YOUR_URL.ngrok.io/`
3. Signature verification? Check `NOTION_WEBHOOK_SECRET` in `.env`

## Files Created

```
curator-agent/
├── migrations/
│   └── 003_add_notion_integration.sql  ✓ Database schema
├── src/curator/
│   └── notion_sync.py                  ✓ Notion API integration
├── notion_webhook_server.py            ✓ FastAPI webhook server
├── setup_notion.py                     ✓ One-time database setup
└── NOTION_INTEGRATION_GUIDE.md         ✓ This file
```

## Summary

✅ **Event-driven architecture** - No polling, no manual triggers
✅ **Zero code changes** to production curator agent
✅ **Full tracking** - Know what's in Notion, when it synced, any errors
✅ **Bidirectional** - Push to Notion, pull status updates back
✅ **Scalable** - Handles thousands of extractions efficiently
✅ **Observable** - Logs, status endpoint, database views

**Next:** Run `process_extractions.py` and watch the magic happen! 🚀
