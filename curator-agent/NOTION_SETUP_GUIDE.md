# Notion Integration Setup Guide

**Date:** 2025-12-24
**Purpose:** Set up human review workflow for PROVES Library extractions

---

## Overview

This guide walks through creating the Notion Extraction Review database and syncing the 6 pending extractions for human review.

**Current Status:**
- ✅ 6 extractions in staging_extractions with status='pending'
- ✅ All have lineage_confidence = 0.67 (retroactive verification)
- ✅ Sync script ready ([sync_to_notion.py](sync_to_notion.py))
- ⏳ Notion database needs to be created
- ⏳ Extractions need to be synced

---

## Step 1: Create Notion Database

### 1.1 Create Database in Notion

1. Open your Notion workspace
2. Create a new page called "PROVES Library - Extraction Review"
3. Add a database (full-page database)
4. Name it: **"Extraction Review"**

### 1.2 Add Properties

Add these properties to the database (click "+ Add a property"):

| Property Name | Type | Options (if applicable) |
|--------------|------|-------------------------|
| **Name** | Title | (default) |
| **Type** | Select | component, interface, flow, mechanism, error_mode, parameter, dependency, telemetry, port |
| **Ecosystem** | Select | cubesat, embedded, power, communication, attitude_control, thermal, proveskit |
| **Confidence** | Number | Format: Number, Show as: Progress bar |
| **Lineage** | Number | Format: Number, Show as: Progress bar |
| **Status** | Select | Pending Review, Approved, Rejected, Needs Investigation, Re-extraction (Review Required) |
| **Extraction ID** | Text | - |
| **Source URL** | URL | - |
| **Evidence** | Text | (long text) |
| **Attributes** | Text | (long text) |
| **Created** | Date | - |
| **Reviewed By** | Person | - |
| **Reviewed At** | Date | - |
| **Notes** | Text | (long text) |
| **Lineage Verified** | Checkbox | - |
| **Extraction Attempt** | Number | Format: Number |
| **Requires Investigation** | Checkbox | - |

### 1.3 Create Views

**Default View (All Extractions):**
- No filters
- Sort by: Created (descending)

**Pending Review:**
- Filter: Status = "Pending Review"
- Sort by: Lineage (ascending) - shows lowest lineage first

**Low Lineage:**
- Filter: Lineage < 0.8
- Sort by: Lineage (ascending)

**Needs Investigation:**
- Filter: Requires Investigation = checked
- Sort by: Created (descending)

### 1.4 Get Database ID

1. Open the database in Notion
2. Click "Share" → "Copy link"
3. The URL looks like: `https://www.notion.so/workspace/{DATABASE_ID}?v=...`
4. Copy the `{DATABASE_ID}` part (the 32-character hex string)
5. Save it - you'll need it in Step 2

---

## Step 2: Sync Extractions to Notion

### Option A: Use Notion API (Recommended)

**2.1 Get Notion API Key:**

1. Go to https://www.notion.so/my-integrations
2. Click "+ New integration"
3. Name: "PROVES Library Curator"
4. Select your workspace
5. Capabilities: Read content, Update content, Insert content
6. Click "Submit"
7. Copy the "Internal Integration Token" (starts with `secret_`)

**2.2 Connect Integration to Database:**

1. Open your Extraction Review database in Notion
2. Click "..." (top right) → "Add connections"
3. Select "PROVES Library Curator"
4. Click "Confirm"

**2.3 Add API Key to .env:**

```bash
# Add to .env file
NOTION_API_KEY=secret_your_api_key_here
NOTION_EXTRACTION_REVIEW_DB=your_database_id_here
```

**2.4 Run Sync:**

```bash
cd curator-agent
python sync_to_notion.py --database-id YOUR_DATABASE_ID --use-api
```

### Option B: Manual Sync via Claude Desktop

If you prefer to use the Notion MCP in Claude Desktop:

1. Open Claude Desktop
2. Paste this prompt:

```
I need you to create 6 pages in my Notion "Extraction Review" database.
Database ID: YOUR_DATABASE_ID

Here's the data for each extraction:
[Copy the preview output from the dry-run]

For each extraction, create a page with:
- Name: candidate_key
- Type: candidate_type
- Ecosystem: ecosystem
- Confidence: confidence_score
- Lineage: lineage_confidence
- Status: "Pending Review"
- Extraction ID: extraction_id
- Source URL: source_url
- Evidence: (from evidence.raw_text)
- Attributes: (from candidate_payload as JSON)
- Created: created_at
- Lineage Verified: false
- Extraction Attempt: 1
- Requires Investigation: false
```

### Option C: Manual Entry

If API and MCP don't work, manually create 6 pages in Notion with the data from the preview:

1. **UART Protocol Specification**
   - Type: parameter, Ecosystem: proveskit
   - Confidence: 0.70, Lineage: 0.67
   - Source: https://docs.proveskit.space/en/latest/core_documentation/hardware/proves_prime/

2. **PROVES Prime Development Documentation**
   - Type: dependency, Ecosystem: proveskit
   - Confidence: 0.90, Lineage: 0.67
   - Source: https://docs.proveskit.space/en/latest/core_documentation/hardware/proves_prime/

3. **Satellite Beacon Data**
   - Type: telemetry, Ecosystem: proveskit
   - Confidence: 0.80, Lineage: 0.67
   - Source: https://docs.proveskit.space/en/latest/core_documentation/hardware/proves_prime/

4. **MSP430FR-RP2350 UART Connection**
   - Type: port, Ecosystem: proveskit
   - Confidence: 0.90, Lineage: 0.67
   - Source: https://docs.proveskit.space/en/latest/core_documentation/hardware/proves_prime/

5. **MSP430FR Microcontroller**
   - Type: component, Ecosystem: proveskit
   - Confidence: 0.90, Lineage: 0.67
   - Source: https://docs.proveskit.space/en/latest/core_documentation/hardware/proves_prime/

6. **PROVES Prime Mainboard**
   - Type: component, Ecosystem: proveskit
   - Confidence: 0.90, Lineage: 0.67
   - Source: https://docs.proveskit.space/en/latest/core_documentation/hardware/proves_prime/

---

## Step 3: Review and Approve Extractions

### Human Review Process

For each extraction in Notion:

1. **Click to open** the page
2. **Review the evidence**: Does it support the extraction?
3. **Check the source**: Click Source URL to verify
4. **Assess lineage confidence**: 0.67 means partial verification (expected for these retroactive verifications)
5. **Make a decision**:
   - ✅ **Approve**: Change Status to "Approved", add your name to "Reviewed By", set "Reviewed At" to today
   - ❌ **Reject**: Change Status to "Rejected", add Notes explaining why
   - 🔍 **Needs Investigation**: Check "Requires Investigation", add Notes

### What to Look For

**Good Extractions:**
- Evidence clearly supports the extraction
- Attributes/payload are well-structured
- Type and ecosystem are correct
- Confidence score seems reasonable

**Problematic Extractions:**
- Evidence doesn't match the extraction
- Missing or incomplete attributes
- Wrong type or ecosystem classification
- Very low confidence score (<0.6)

---

## Step 4: Approval Workflow

### Option A: Manual Approval (Simple - Use This First)

After reviewing in Notion, manually promote approved extractions:

```bash
cd curator-agent
python -c "
import psycopg
import os
from dotenv import load_dotenv

load_dotenv('../.env')
conn = psycopg.connect(os.environ['NEON_DATABASE_URL'])

# Get extraction_id from Notion, then run:
extraction_id = 'YOUR_EXTRACTION_ID_HERE'

with conn.cursor() as cur:
    # Promote to core_entities
    cur.execute('''
        INSERT INTO core_entities (
            entity_type, entity_key, ecosystem,
            attributes, confidence_score, evidence,
            source_snapshot_id, created_by_run_id,
            is_current, version
        )
        SELECT
            candidate_type, candidate_key, ecosystem,
            candidate_payload, confidence_score, evidence,
            snapshot_id, pipeline_run_id,
            TRUE, 1
        FROM staging_extractions
        WHERE extraction_id = %s::uuid
        RETURNING id
    ''', (extraction_id,))

    entity_id = cur.fetchone()[0]

    # Update staging_extractions
    cur.execute('''
        UPDATE staging_extractions
        SET status = 'approved',
            promoted_to_id = %s,
            promoted_at = NOW()
        WHERE extraction_id = %s::uuid
    ''', (entity_id, extraction_id))

conn.commit()
conn.close()

print(f'Promoted {extraction_id} to core_entities as {entity_id}')
"
```

### Option B: Webhook Automation (Future)

In a future session, we can set up a Notion webhook that automatically:
1. Detects when Status changes to "Approved"
2. Calls a webhook endpoint
3. Automatically promotes to core_entities
4. Updates Notion with the result

For now, manual approval is simpler and safer.

---

## Step 5: Verification

After syncing and approving, verify the data flow:

**Check Notion:**
```
- All 6 extractions appear in Notion
- Properties are populated correctly
- Source URLs are clickable
- Evidence text is readable
```

**Check Database:**
```bash
# After approval, check core_entities
cd curator-agent
python -c "
import psycopg
import os
from dotenv import load_dotenv

load_dotenv('../.env')
conn = psycopg.connect(os.environ['NEON_DATABASE_URL'])

with conn.cursor() as cur:
    cur.execute('SELECT COUNT(*) FROM core_entities WHERE is_current = TRUE')
    count = cur.fetchone()[0]
    print(f'Approved entities in core_entities: {count}')

    cur.execute('SELECT COUNT(*) FROM staging_extractions WHERE status = \\'approved\\'')
    count = cur.fetchone()[0]
    print(f'Approved in staging_extractions: {count}')

conn.close()
"
```

---

## Understanding Lineage Confidence

**Why are these extractions at 0.67 lineage confidence?**

These 6 extractions were created BEFORE the lineage tracking system was implemented. The retroactive verification found:

✅ **What passed:**
- Extraction exists in database
- Snapshot exists and is linked
- Evidence found in snapshot
- Evidence checksum calculated
- Snapshot checksum exists

❌ **What failed:**
- Evidence is an agent-generated summary, not an exact quote from source
- Can't verify byte-level provenance

**For future extractions:**
- Extractor will capture exact quotes
- Lineage confidence will be 1.0 (perfect lineage)
- Every word will be traceable to source byte offset

**These extractions are still valid!** They're just being honest about lineage verification limits.

---

## Next Steps

After completing Notion setup:

1. ✅ Sync all 6 extractions to Notion
2. ✅ Review and approve valid extractions
3. ✅ Verify data appears in core_entities
4. 📋 Run next extraction (FC Board page) with full lineage tracking
5. 📋 Compare new extraction lineage confidence (should be 1.0)
6. 📋 Set up automated approval workflow (webhook)
7. 📋 Add error logging to Notion
8. 📋 Add daily reports to Notion

---

## Troubleshooting

**Problem: Can't find Database ID**
- Solution: Share the database, copy link, extract the 32-char hex string

**Problem: Integration not appearing in "Add connections"**
- Solution: Refresh the page, or recreate the integration

**Problem: API returns 401 Unauthorized**
- Solution: Check NOTION_API_KEY is correct, integration is connected to database

**Problem: Sync script fails with encoding error**
- Solution: Already fixed in latest version - uses ASCII output

**Problem: Evidence text is truncated**
- Solution: This is expected (Notion has 2000 char limit per property). Full evidence is in database.

---

## Budget Impact

**Notion API Costs:**
- Free tier: 1,000 blocks/month
- Each extraction: ~10 blocks
- 6 extractions: ~60 blocks
- Remaining for next 54 pages: 940 blocks (sufficient for ~94 more extractions)

**Total System Budget:**
- Extraction pipeline: ~$12/month (Claude API)
- Notion integration: ~$5/month (processing approvals)
- Notion plan: $0 (free tier) or $10/month (paid)
- **Total: $17-27/month**

**Within $20 budget if using Notion free tier!**

---

## Summary

You've now set up:
- ✅ Notion database schemas designed
- ✅ Sync script created and tested (dry-run)
- ✅ 6 pending extractions ready to sync
- ✅ Lineage tracking fully implemented
- ✅ Manual approval workflow documented
- 📋 Ready for human review!

Next: Create the Notion database and run the sync!

---

## APPENDIX: Additional Databases for Complete Oversight

### Error Log Database (Optional but Recommended)

**Purpose:** Track all agent errors for pattern analysis and system health monitoring

**Setup Instructions:**

1. Create new database called **"Error Log"**
2. Add properties from [notion_error_log_schema.md](notion_error_log_schema.md):
   - Error ID (Title)
   - Timestamp (Date with time)
   - Agent (Select: extractor, validator, storage, curator, etc.)
   - Error Type (Select: recursive_error, null_values, timeout, etc.)
   - Severity (Select: Critical, High, Medium, Low)
   - Error Message (Text - long)
   - Stack Trace (Text - long)
   - Context (Text - long)
   - Thread ID (Text)
   - Extraction ID (Text)
   - Source URL (URL)
   - Status (Select: Open, Investigating, Resolved, Ignored, Recurring)
   - Resolution (Text - long)
   - Resolved By (Person)
   - Resolved At (Date)
   - Occurrence Count (Number)
   - First Seen (Date)
   - Last Seen (Date)
   - Cost Impact (Number - $)
   - Pattern Notes (Text)

3. Create views:
   - **Open Errors** (Filter: Status = Open, Sort: Severity, Group by: Agent)
   - **Critical Errors** (Filter: Severity = Critical)
   - **Recurring Errors** (Filter: Occurrence Count > 1)
   - **By Agent** (Group by: Agent)
   - **High Cost Impact** (Filter: Cost Impact > 0.10, Sort: Cost Impact desc)

4. Get database ID and add to .env:
```bash
echo "NOTION_ERROR_LOG_DB=your_error_log_database_id" >> .env
```

5. Test error logging:
```bash
cd curator-agent
python log_error_to_notion.py  # Runs test error
```

**Integration with Agents:**

Add error logging to all agent exception handlers:

```python
from log_error_to_notion import log_error

try:
    # Agent work
    result = process_page(url)
except Exception as e:
    log_error(
        agent="extractor",
        error_type="http_error",
        severity="high",
        message=str(e),
        context=f"Processing {url}",
        source_url=url
    )
    raise  # Re-raise to let LangGraph handle
```

---

### Curator Observations Database (Recommended)

**Purpose:** Curator's oversight reports on efficiency, cost optimization, limitations, and system improvements

**Setup Instructions:**

1. Create new database called **"Curator Observations"**
2. Add properties from [notion_curator_reports_schema.md](notion_curator_reports_schema.md):
   - Report Title (Title)
   - Report Date (Date)
   - Report Type (Select: Daily Summary, Weekly Analysis, Cost Review, Efficiency Audit, etc.)
   - Observation Category (Multi-select: Cost Optimization, Efficiency Improvement, Tool Gap, etc.)
   - Severity/Priority (Select: Critical, High, Medium, Low, Informational)
   - Status (Select: New, Under Review, Addressed, Deferred, Monitoring)
   - Summary (Text - long)
   - Detailed Findings (Text - long)
   - Metrics (Text)
   - Cost Impact (Number - $)
   - Efficiency Gain (Number - hours or %)
   - Affected Agents (Multi-select: extractor, validator, storage, curator)
   - Suggested Actions (Text - long)
   - Tools Needed (Text)
   - Restrictions Identified (Text - long)
   - Implementation Complexity (Select: Simple, Moderate, Complex, Requires Architecture Change)
   - Implemented (Checkbox)
   - Implementation Date (Date)
   - Actual Impact (Text)
   - Related Errors (Text)
   - Related Extractions (Text)
   - Supporting Data (Text - long)

3. Create views:
   - **Pending Review** (Filter: Status = New OR Under Review, Sort: Severity)
   - **High Impact Opportunities** (Filter: Cost Impact > 5 OR Efficiency Gain > 10)
   - **By Category** (Group by: Observation Category)
   - **Tool Requests** (Filter: Observation Category contains "Tool Gap")
   - **Implemented Improvements** (Filter: Implemented = TRUE)
   - **Cost Savings Tracker** (Filter: Cost Impact > 0 AND Implemented = TRUE)
   - **Weekly Summaries** (Filter: Report Type = Daily Summary OR Weekly Analysis)

4. Get database ID and add to .env:
```bash
echo "NOTION_CURATOR_REPORTS_DB=your_curator_reports_database_id" >> .env
```

5. Test report generation:
```bash
cd curator-agent

# Daily summary
python generate_curator_report.py --type daily --dry-run

# Weekly analysis
python generate_curator_report.py --type weekly --dry-run
```

**Curator Workflow:**

**Daily (5 minutes):**
```bash
# Generate and sync daily summary
python generate_curator_report.py --type daily
```

**Weekly (15 minutes):**
```bash
# Generate weekly analysis
python generate_curator_report.py --type weekly

# Review Error Log for patterns
# Create custom observations for any issues found
```

**As Needed:**
```bash
# Custom observation (e.g., discovered a cost optimization)
python generate_curator_report.py --type custom \
  --title "Extractor re-requesting same snapshots" \
  --category "Cost Optimization" \
  --severity "High"
```

---

### Complete Notion Integration Summary

**Three Databases:**

1. **Extraction Review** (Required) - Human verification of extractions
   - Where: All extractions before core_entities
   - Who: Human reviewers
   - Frequency: Per extraction batch
   - Purpose: Quality gate

2. **Error Log** (Recommended) - Agent error tracking
   - Where: All agent exceptions
   - Who: Curator + human oversight
   - Frequency: Real-time on errors
   - Purpose: System health, pattern detection

3. **Curator Observations** (Recommended) - System oversight reports
   - Where: Curator's analysis and suggestions
   - Who: Curator → human review
   - Frequency: Daily summaries, weekly analysis, as-needed observations
   - Purpose: Continuous improvement, cost optimization

**Environment Variables:**
```bash
# .env file
NOTION_API_KEY=secret_your_integration_key
NOTION_EXTRACTION_REVIEW_DB=abc123...  # Required
NOTION_ERROR_LOG_DB=def456...           # Optional
NOTION_CURATOR_REPORTS_DB=ghi789...     # Optional
```

**Budget Impact:**

| Database | Blocks/Month | Cost Impact |
|----------|--------------|-------------|
| Extraction Review | ~350 (342 extractions × ~1 block) | Free tier |
| Error Log | ~50-100 (assuming 1-2 errors/day) | Free tier |
| Curator Observations | ~100 (daily + weekly reports) | Free tier |
| **Total** | ~500-550 blocks | **Free tier (1,000 limit)** |

**All three databases fit within Notion's free tier!**

---

### Quick Start Checklist

**Minimum Viable Setup (Human Review Only):**
- [ ] Create Extraction Review database
- [ ] Add all 17 properties
- [ ] Get database ID
- [ ] Add NOTION_API_KEY and NOTION_EXTRACTION_REVIEW_DB to .env
- [ ] Run sync: `python sync_to_notion.py --database-id YOUR_DB_ID --use-api`
- [ ] Review and approve extractions in Notion
- [ ] Promote approved: `python promote_extraction.py EXTRACTION_ID`

**Full Oversight Setup (Recommended):**
- [ ] Create all three databases (Extraction Review, Error Log, Curator Observations)
- [ ] Add all properties to each
- [ ] Get all three database IDs
- [ ] Add all three to .env
- [ ] Test sync: `python sync_to_notion.py --dry-run`
- [ ] Test error logging: `python log_error_to_notion.py`
- [ ] Test reporting: `python generate_curator_report.py --type daily --dry-run`
- [ ] Review and approve extractions
- [ ] Set up daily curator workflow (cron job or manual)

---

**With all three databases, you have:**
- ✅ Complete human-in-the-loop verification
- ✅ Comprehensive error tracking and pattern analysis
- ✅ Curator oversight for continuous improvement
- ✅ Cost optimization opportunities identified
- ✅ System health monitoring
- ✅ Data-driven decision making
- ✅ All within Notion's free tier!
