# Notion Database Schemas for PROVES Library

**Date:** 2025-12-24
**Purpose:** Human review interface for curator agent workflow

---

## 1. Extraction Review Database

**Primary Purpose:** Human verification of extractions before promoting to truth graph

### Properties

| Property | Type | Description |
|----------|------|-------------|
| **Name** | Title | candidate_key (e.g., "MSP430FR5969 Microcontroller") |
| **Type** | Select | component, interface, flow, mechanism, error_mode |
| **Ecosystem** | Select | cubesat, embedded, power, communication, attitude_control, thermal |
| **Confidence** | Number | confidence_score (0.0-1.0) |
| **Lineage** | Number | lineage_confidence (0.0-1.0) |
| **Status** | Select | Pending Review, Approved, Rejected, Needs Re-extraction |
| **Extraction ID** | Text | UUID for database linkage |
| **Source URL** | URL | Link to original documentation |
| **Evidence** | Text (long) | Supporting quote/evidence |
| **Attributes** | Text (long) | JSON of extracted attributes |
| **Created** | Date | When extracted |
| **Reviewed By** | Person | Who reviewed |
| **Reviewed At** | Date | When reviewed |
| **Notes** | Text | Human review notes |
| **Lineage Verified** | Checkbox | Whether lineage passed all checks |
| **Extraction Attempt** | Number | 1 = first attempt, 2 = re-extraction |
| **Requires Investigation** | Checkbox | Flagged for mandatory review |

### Views

1. **Pending Review** - Filter: Status = "Pending Review", Sort: Lineage (ascending)
2. **Low Lineage** - Filter: Lineage < 0.8, Sort: Lineage (ascending)
3. **Needs Investigation** - Filter: Requires Investigation = true
4. **Recently Approved** - Filter: Status = "Approved", Sort: Reviewed At (descending)

---

## 2. Error Log Database

**Primary Purpose:** Track all agent errors for investigation

### Properties

| Property | Type | Description |
|----------|------|-------------|
| **Error ID** | Title | Unique error identifier |
| **Agent** | Select | extractor, validator, storage, curator, website-validator |
| **Error Type** | Select | recursive_error, null_values, timeout, http_error, validation_failure |
| **Severity** | Select | Critical, High, Medium, Low |
| **Message** | Text (long) | Error message |
| **Stack Trace** | Text (long) | Full traceback |
| **Context** | Text (long) | What was being processed |
| **Thread ID** | Text | LangGraph thread ID |
| **Timestamp** | Date | When occurred |
| **Status** | Select | Open, Investigating, Resolved, Ignored |
| **Resolution** | Text | How fixed |

### Views

1. **Open Errors** - Filter: Status = "Open", Sort: Severity, Timestamp (desc)
2. **By Agent** - Group by: Agent
3. **Critical** - Filter: Severity = "Critical"

---

## 3. Daily Reports Database

**Primary Purpose:** Curator's daily activity summaries

### Properties

| Property | Type | Description |
|----------|------|-------------|
| **Report Date** | Title | YYYY-MM-DD |
| **Pages Processed** | Number | How many pages extracted |
| **Extractions Created** | Number | Total new extractions |
| **Extractions Verified** | Number | How many passed lineage check |
| **Errors Encountered** | Number | Total errors logged |
| **Warnings** | Text (long) | Issues needing attention |
| **Suggestions** | Text (long) | Curator recommendations |
| **Status Summary** | Text (long) | Overall system health |
| **Cost Estimate** | Number | Estimated API cost for day |

### Views

1. **Recent Reports** - Sort: Report Date (descending)
2. **High Error Days** - Filter: Errors Encountered > 5

---

## Integration Architecture

### Flow 1: Extraction to Notion (Push)

```
staging_extractions (status='pending')
  ↓
sync_to_notion.py
  ↓
Notion MCP → Create page in Extraction Review
  ↓
Human reviews in Notion
```

### Flow 2: Approval from Notion (Webhook)

**Option A: Webhook (Preferred)**
```
Human clicks "Approve" in Notion
  ↓
Notion webhook → curator-agent/webhooks/notion_approval.py
  ↓
Resume LangGraph thread
  ↓
storage_agent.promote_to_core()
  ↓
Update staging_extractions.status = 'approved'
  ↓
Insert into core_entities
```

**Option B: Polling (Fallback if webhook complex)**
```
Curator runs check_notion_approvals() every 6 hours
  ↓
Query Notion for Status = "Approved" AND Reviewed At > last_check
  ↓
Process approvals
```

### Flow 3: Error Logging (Push)

```
Agent catches exception
  ↓
log_error_to_notion(error_details)
  ↓
Notion MCP → Create page in Error Log
  ↓
Optional: Notify curator to investigate
```

---

## Webhook Setup (Notion → Curator)

**Notion Webhook URL:**
```
https://your-domain.com/webhooks/notion/approval
```

**Payload Example:**
```json
{
  "event": "page_updated",
  "page_id": "abc-123",
  "properties": {
    "Status": "Approved",
    "Extraction ID": "ext-456-uuid",
    "Reviewed By": "User Name"
  }
}
```

**Handler Logic:**
```python
# curator-agent/webhooks/notion_approval.py
def handle_approval(payload):
    extraction_id = payload['properties']['Extraction ID']

    # Resume LangGraph thread
    thread_id = get_thread_for_extraction(extraction_id)
    resume_thread(thread_id, action='approve')

    # Storage agent promotes to core_entities
    # Updates staging_extractions.status = 'approved'
```

---

## Budget Considerations

**Notion API Limits:**
- Free tier: 1,000 blocks per month (should be sufficient)
- Each extraction = ~10 blocks (title, properties, evidence text)
- 60 pages × 5.7 extractions = 342 extractions × 10 blocks = 3,420 blocks/month
- **Recommendation:** Paid Notion plan ($10/month) if exceeding limits

**API Costs:**
- Sync to Notion: Negligible (just reading from database)
- Webhook processing: ~$0.01 per approval (one LLM call to validate)
- Total: <$5/month for Notion integration

**Total System Budget:**
- Extraction pipeline: ~$12/month
- Notion integration: ~$5/month
- **Total: ~$17/month (under $20 budget!)**

---

## Implementation Phases

### Phase 1: Manual Sync (This Session)
1. Create Notion databases manually in workspace
2. Run sync_to_notion.py to populate 6 existing extractions
3. Test human review workflow manually
4. Manual promotion via script

### Phase 2: Webhook Integration (Next Session)
1. Set up webhook endpoint (Flask/FastAPI)
2. Configure Notion webhook
3. Test automated approval flow
4. Monitor for 24 hours

### Phase 3: Error Logging (Future)
1. Add error logging to all agents
2. Test error capture
3. Add curator monitoring

### Phase 4: Daily Reports (Future)
1. Curator generates reports
2. Scheduled sync to Notion
3. Email notifications for critical issues

---

## Simplified Starter Schema

**For this session, we'll create just ONE database:**

**Extraction Review Database** (simplified)

Properties:
- Name (Title) - candidate_key
- Type (Select) - candidate_type
- Confidence (Number) - confidence_score
- Lineage (Number) - lineage_confidence
- Status (Select) - Pending Review, Approved, Rejected
- Extraction ID (Text) - extraction_id
- Source URL (URL) - source_url
- Evidence (Text) - evidence quote
- Created (Date) - created_at

This is enough to start human review. We can add more databases later.
