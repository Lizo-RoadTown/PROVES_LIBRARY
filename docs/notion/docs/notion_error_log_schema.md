# Notion Error Log Database Schema

**Purpose:** Track all agent errors for investigation and pattern analysis

---

## Properties

| Property | Type | Options/Format |
|----------|------|----------------|
| **Error ID** | Title | Auto-generated unique ID (e.g., "ERR-2025-12-24-001") |
| **Timestamp** | Date | Include time |
| **Agent** | Select | extractor, validator, storage, curator, website-validator, error-tracker |
| **Error Type** | Select | recursive_error, null_values, timeout, http_error, validation_failure, database_error, llm_error, schema_mismatch, missing_data, auth_error |
| **Severity** | Select | Critical, High, Medium, Low |
| **Error Message** | Text (long) | Short error description |
| **Stack Trace** | Text (long) | Full Python traceback |
| **Context** | Text (long) | What was being processed (page URL, extraction ID, etc.) |
| **Thread ID** | Text | LangGraph thread ID |
| **Extraction ID** | Text | Related extraction_id if applicable |
| **Source URL** | URL | Page being processed when error occurred |
| **Status** | Select | Open, Investigating, Resolved, Ignored, Recurring |
| **Resolution** | Text (long) | How it was fixed |
| **Resolved By** | Person | Who fixed it |
| **Resolved At** | Date | When fixed |
| **Occurrence Count** | Number | How many times this error has occurred |
| **First Seen** | Date | When first encountered |
| **Last Seen** | Date | When most recently encountered |
| **Cost Impact** | Number | Estimated wasted API cost ($) |
| **Pattern Notes** | Text | Notes about when/why this occurs |

---

## Views

### 1. Open Errors (Default)
- **Filter:** Status = "Open"
- **Sort:** Severity (Critical first), then Timestamp (newest first)
- **Group by:** Agent

### 2. Critical Errors
- **Filter:** Severity = "Critical"
- **Sort:** Timestamp (newest first)

### 3. Recurring Errors
- **Filter:** Occurrence Count > 1 OR Status = "Recurring"
- **Sort:** Occurrence Count (descending)
- **Useful for:** Identifying systemic issues

### 4. By Agent
- **Group by:** Agent
- **Sort:** Timestamp (newest first)
- **Useful for:** Seeing which agents have the most issues

### 5. Recently Resolved
- **Filter:** Status = "Resolved"
- **Sort:** Resolved At (newest first)
- **Useful for:** Tracking fixes

### 6. High Cost Impact
- **Filter:** Cost Impact > 0.10
- **Sort:** Cost Impact (descending)
- **Useful for:** Budget monitoring

---

## Error Categories

### Recursive Errors
- **Severity:** Critical
- **Pattern:** Agent calls itself or creates infinite loop
- **Action:** Immediate investigation required

### Null Values / Missing Data
- **Severity:** High
- **Pattern:** Database returned NULL when value expected
- **Action:** Check schema, verify data integrity

### Timeout Errors
- **Severity:** Medium
- **Pattern:** HTTP request or LLM call exceeded timeout
- **Action:** Check if URL is down, increase timeout if needed

### Validation Failures
- **Severity:** High
- **Pattern:** Lineage check failed, confidence too low
- **Action:** Review extraction quality, may need re-extraction

### Schema Mismatches
- **Severity:** High
- **Pattern:** Code expects field that doesn't exist
- **Action:** Update schema or fix code

### LLM Errors
- **Severity:** Medium
- **Pattern:** Claude API error, rate limit, context length
- **Action:** Check API status, implement retry logic

---

## Integration

### Automatic Logging

All agents should catch exceptions and log to Notion:

```python
try:
    # Agent work here
    result = do_extraction(page_url)
except Exception as e:
    # Log to Notion
    log_error_to_notion(
        agent="extractor",
        error_type="http_error" if isinstance(e, HTTPError) else "unknown",
        severity="high",
        message=str(e),
        stack_trace=traceback.format_exc(),
        context=f"Processing {page_url}",
        thread_id=thread_id,
        source_url=page_url
    )
    raise  # Re-raise to let LangGraph handle
```

### Pattern Detection

Curator should periodically analyze errors:
- Group by Error Type and Context to find patterns
- Count occurrences of same error message
- Flag recurring errors for investigation
- Calculate total cost impact

---

## Sample Entries

### Example 1: Recurring Timeout
- **Error ID:** ERR-2025-12-24-003
- **Agent:** extractor
- **Error Type:** timeout
- **Severity:** Medium
- **Message:** "Request to https://docs.proveskit.space/fc_board/ timed out after 30s"
- **Occurrence Count:** 5
- **Pattern Notes:** "Always happens with FC Board page - page is very large, needs longer timeout"
- **Resolution:** "Increased timeout to 60s for pages > 500KB"

### Example 2: Null Value Error
- **Error ID:** ERR-2025-12-24-007
- **Agent:** validator
- **Error Type:** null_values
- **Severity:** High
- **Message:** "Column 'evidence_checksum' returned NULL for extraction ext-abc-123"
- **Context:** "Validating extraction from PROVES Prime page"
- **Resolution:** "Retroactive extractions missing checksums - ran retroactive_verify_lineage.py to populate"

### Example 3: Recursive Error
- **Error ID:** ERR-2025-12-24-001
- **Agent:** storage
- **Error Type:** recursive_error
- **Severity:** Critical
- **Message:** "Agent called promote_to_core() within promote_to_core() - infinite loop detected"
- **Resolution:** "Fixed logic to check if already promoted before calling function"
