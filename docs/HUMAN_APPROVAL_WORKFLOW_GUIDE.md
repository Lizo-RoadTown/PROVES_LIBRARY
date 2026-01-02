# Human Approval Workflow - Implementation Guide

## Overview

The PROVES Library now has a complete human approval workflow with:
- ✅ Full audit trail of all human decisions
- ✅ Idempotency (prevents duplicate webhook processing)
- ✅ Actor tracking (who made what decision)
- ✅ Reason tracking (why they made the decision)
- ✅ Analytics views for review patterns

## Migration

### Run Migration 012

```bash
cd neon-database
python scripts/run_migration.py
```

This migration adds:
1. **Enhanced `validation_decisions` table** - Full audit log
2. **Expanded `candidate_status` enum** - New statuses: `needs_context`, `merged`
3. **Versioning columns** to `staging_extractions`
4. **Helper functions** for decision recording
5. **Analytics views** for review stats

## Database Schema

### validation_decisions (Audit Trail)

**Purpose:** Append-only log of all human actions on extractions

```sql
CREATE TABLE validation_decisions (
    id UUID PRIMARY KEY,
    extraction_id UUID REFERENCES staging_extractions(extraction_id),

    -- What action was taken?
    action_type TEXT CHECK (action_type IN (
        'accept', 'reject', 'edit', 'merge',
        'request_more_evidence', 'flag_for_review'
    )),

    -- Who did it?
    actor_id TEXT,  -- Notion user ID

    -- Why?
    reason TEXT,

    -- What changed? (for edits)
    before_payload JSONB,
    after_payload JSONB,
    patch JSONB,  -- Alternative: JSON Patch format

    -- When?
    timestamp TIMESTAMPTZ DEFAULT NOW(),

    -- Idempotency
    source TEXT UNIQUE,  -- Notion webhook ID

    -- Existing columns
    lineage_check_passed BOOLEAN,
    lineage_check_details JSONB
);
```

### staging_extractions (Enhanced)

**New columns:**
```sql
-- Versioning
current_revision INTEGER DEFAULT 1,
latest_decision_id UUID REFERENCES validation_decisions(id),

-- Assignment
assigned_to TEXT,

-- Existing status enum now includes:
status candidate_status  -- pending | accepted | rejected | flagged | needs_context | merged
```

## Workflow

### 1. Agent Creates Extraction

When an agent creates an extraction, it goes into `staging_extractions`:

```sql
INSERT INTO staging_extractions (...)
VALUES (...);
-- status = 'pending'
-- current_revision = 1
```

### 2. Sync to Notion

The Notion webhook server polls for unsynced extractions and pushes them to Notion:

```python
# Database → Notion (automatic polling)
notion_sync.sync_extraction_to_notion(extraction_id)
```

### 3. Human Reviews in Notion

The human can:
- Set **Accept/Reject** field to:
  - `Approved` → Accept extraction
  - `Rejected` → Reject extraction
  - `Modified` → Flag for re-review after edits

- Or set **Status** field to:
  - `Approved` → Accept
  - `Rejected` → Reject
  - `Needs Review` → Flag for review
  - `Needs Context` → Request more evidence

- Add **Review Notes** to explain decision

### 4. Notion Webhook Fires

When the human updates the page, Notion sends a webhook to:
```
POST /webhook/notion
```

### 5. Webhook Handler Processes Update

The handler:

**A. Checks Idempotency**
```python
if webhook_already_processed(webhook_id):
    return "already_processed"
```

**B. Extracts Decision Details**
```python
extraction_id = props['Extraction ID']
actor_id = webhook_payload['user']['id']  # Notion user
reason = props['Review Notes']['rich_text'][0]['plain_text']
action_type = map_notion_status_to_action(props['Accept/Reject'])
```

**C. Records Decision (Audit Trail)**
```sql
SELECT record_human_decision(
    extraction_id := '123e4567-e89b-12d3-a456-426614174000',
    action_type := 'accept',
    actor_id := 'notion_user_abc123',
    reason := 'Verified against source documentation',
    webhook_source := 'webhook_xyz789'  -- For idempotency
);
```

This creates an immutable record in `validation_decisions` and updates `staging_extractions.latest_decision_id`.

**D. Updates Extraction Status**
```sql
UPDATE staging_extractions
SET status = 'accepted',
    reviewed_at = NOW(),
    review_decision = 'accept'
WHERE extraction_id = '123e4567-e89b-12d3-a456-426614174000';
```

### 6. Promotion to Truth (Future)

When status = 'accepted', the extraction can be promoted to core truth tables:

```sql
-- Future implementation
INSERT INTO core_entities (...)
SELECT ... FROM staging_extractions
WHERE status = 'accepted';

-- Or mark as current:
UPDATE core_entities
SET is_current = true
WHERE extraction_id = '...';
```

## Action Type Mapping

| Notion Field | Value | Action Type | DB Status |
|--------------|-------|-------------|-----------|
| Accept/Reject | Approved | `accept` | `accepted` |
| Accept/Reject | Rejected | `reject` | `rejected` |
| Accept/Reject | Modified | `edit` | `flagged` |
| Status | Approved | `accept` | `accepted` |
| Status | Rejected | `reject` | `rejected` |
| Status | Needs Review | `flag_for_review` | `flagged` |
| Status | Needs Context | `request_more_evidence` | `needs_context` |

## Analytics Views

### View: human_review_stats

**Purpose:** Track who is reviewing what and how fast

```sql
SELECT * FROM human_review_stats
WHERE actor_id = 'notion_user_abc123';
```

**Output:**
```
actor_id         | action_type | action_count | avg_response_time_seconds | first_action | last_action
-----------------|-------------|--------------|--------------------------|--------------|-------------
notion_user_abc  | accept      | 42           | 3600                     | 2025-01-01   | 2025-01-02
notion_user_abc  | reject      | 8            | 1800                     | 2025-01-01   | 2025-01-02
```

### View: extractions_awaiting_review

**Purpose:** See what needs review, prioritized by mandatory review and age

```sql
SELECT * FROM extractions_awaiting_review
LIMIT 10;
```

**Output:**
```
extraction_id | candidate_key | confidence_score | hours_waiting | requires_mandatory_review | assigned_to
--------------|---------------|------------------|---------------|--------------------------|-------------
uuid-1        | Component_X   | 0.85             | 48.5          | true                     | user_123
uuid-2        | Dependency_Y  | 0.92             | 24.2          | false                    | NULL
```

### View: extraction_edit_history

**Purpose:** See the full decision history for an extraction

```sql
SELECT * FROM extraction_edit_history
WHERE extraction_id = '123e4567-e89b-12d3-a456-426614174000'
ORDER BY timestamp;
```

**Output:**
```
decision_id | action_type | actor_id      | timestamp           | reason
------------|-------------|---------------|---------------------|-------------------------
uuid-a      | accept      | user_123      | 2025-01-01 10:00:00 | Looks good
uuid-b      | edit        | user_456      | 2025-01-01 11:00:00 | Fixed component name
uuid-c      | accept      | user_123      | 2025-01-01 12:00:00 | Approved after edit
```

## Benefits

### 1. Complete Audit Trail
Every human action is logged with:
- Who did it (`actor_id`)
- What they did (`action_type`)
- Why they did it (`reason`)
- When they did it (`timestamp`)
- What changed (`before_payload`, `after_payload`)

### 2. Idempotency
Webhooks can be safely retried:
```sql
-- This will only process once, even if webhook fires multiple times
SELECT webhook_already_processed('webhook_xyz789');
-- Returns: true (already processed)
```

### 3. Analytics & Insights
- Track review patterns
- Identify extractions that need frequent edits (signal for agent improvement)
- Measure human-AI collaboration efficiency
- See who reviews what and how fast

### 4. Training Signal
The audit trail provides training data for improving agents:
- Which extractions get rejected? Why?
- What patterns do humans fix most often?
- Which confidence scores are most reliable?

### 5. Compliance & Trust
- Immutable record of all decisions
- Can replay history: "Why was this accepted?"
- Supports regulatory requirements for knowledge bases

## Helper Functions

### record_human_decision()

**Purpose:** Consistently record a human decision with audit trail

```sql
SELECT record_human_decision(
    p_extraction_id := '123e4567-e89b-12d3-a456-426614174000'::uuid,
    p_action_type := 'accept',
    p_actor_id := 'notion_user_abc123',
    p_reason := 'Verified against documentation',
    p_before_payload := NULL,
    p_after_payload := NULL,
    p_webhook_source := 'webhook_xyz789'
);
-- Returns: decision_id (uuid)
```

### webhook_already_processed()

**Purpose:** Check if a webhook has already been processed (idempotency)

```sql
SELECT webhook_already_processed('webhook_xyz789');
-- Returns: true or false
```

## Future Enhancements

### 1. Edit Tracking (Before/After Payloads)

Currently, edits are flagged but we don't capture what changed. To implement:

**Option A: Immutable Original + Revisions**
```sql
-- When human edits:
-- 1. Keep original row immutable
-- 2. Create new row with incremented revision_number
-- 3. Set parent_extraction_id

INSERT INTO staging_extractions (...)
VALUES (
    ...,
    parent_extraction_id = original_uuid,
    current_revision = 2
);
```

**Option B: Mutate + Log Diff**
```sql
-- Before update, capture current payload
before_payload := (SELECT candidate_payload FROM staging_extractions WHERE ...);

-- Update extraction
UPDATE staging_extractions SET candidate_payload = new_payload WHERE ...;

-- Log the diff
INSERT INTO validation_decisions (before_payload, after_payload, ...)
VALUES (before_payload, new_payload, ...);
```

### 2. Truth Tables (core_entities, core_edges)

Create separate tables for accepted-only content:
```sql
CREATE TABLE core_entities (
    entity_id UUID PRIMARY KEY,
    extraction_id UUID REFERENCES staging_extractions(extraction_id),
    -- ... entity data ...
    accepted_at TIMESTAMPTZ,
    accepted_by TEXT,
    is_current BOOLEAN DEFAULT TRUE
);

CREATE TABLE core_edges (
    edge_id UUID PRIMARY KEY,
    extraction_id UUID REFERENCES staging_extractions(extraction_id),
    source_entity_id UUID REFERENCES core_entities(entity_id),
    target_entity_id UUID REFERENCES core_entities(entity_id),
    -- ... FRAMES metadata ...
    accepted_at TIMESTAMPTZ,
    accepted_by TEXT,
    is_current BOOLEAN DEFAULT TRUE
);
```

### 3. Assignment & Workflow

```sql
-- Assign extractions to specific reviewers
UPDATE staging_extractions
SET assigned_to = 'notion_user_abc123'
WHERE requires_mandatory_review = true
AND assigned_to IS NULL;

-- Create assignment notifications
-- Track SLA (time to review)
-- Auto-escalate overdue reviews
```

## Testing

### Test Idempotency

```bash
# Process same webhook twice
curl -X POST http://localhost:8000/webhook/notion \
  -H "Content-Type: application/json" \
  -d '{"id": "webhook_test_123", "type": "page.properties_updated", ...}'

# First call: Processes successfully
# Second call: Returns "already_processed"
```

### Test Audit Trail

```sql
-- Check that all decisions are logged
SELECT COUNT(*) FROM validation_decisions;

-- Verify latest_decision_id is updated
SELECT e.extraction_id, e.latest_decision_id, d.action_type, d.actor_id
FROM staging_extractions e
JOIN validation_decisions d ON e.latest_decision_id = d.id
LIMIT 10;
```

### Test Analytics Views

```sql
-- Review stats
SELECT * FROM human_review_stats;

-- Awaiting review
SELECT * FROM extractions_awaiting_review;

-- Edit history
SELECT * FROM extraction_edit_history
WHERE extraction_id = '...';
```

## Files Modified

1. **Migration:**
   - [neon-database/migrations/012_enhance_human_approval_workflow.sql](../neon-database/migrations/012_enhance_human_approval_workflow.sql)

2. **Webhook Handler:**
   - [notion/scripts/notion_webhook_server.py](../notion/scripts/notion_webhook_server.py)
     - Enhanced `handle_extraction_page_updated()` with idempotency and audit trail
     - Added `map_status_to_action()` helper

3. **Documentation:**
   - [docs/HUMAN_APPROVAL_SCHEMA_ANALYSIS.md](HUMAN_APPROVAL_SCHEMA_ANALYSIS.md)
   - This guide

## Next Steps

1. **Run migration 012** to apply schema changes
2. **Test webhook handler** with Notion integration
3. **Monitor analytics views** to track review patterns
4. **Implement edit tracking** (before/after payloads) when needed
5. **Create truth tables** (`core_entities`, `core_edges`) for production deployment
