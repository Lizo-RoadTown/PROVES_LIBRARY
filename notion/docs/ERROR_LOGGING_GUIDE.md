# Error Logging Guide for Curator Agents

Each agent logs errors to its own table without disrupting the workflow. Errors are stored in JSONB format and synced to Notion periodically.

## Architecture

```
┌─────────────────┐
│  Agent Code     │
│  (extractor,    │
│   validator,    │──┐
│   analyzer)     │  │
└─────────────────┘  │
                     │ Logs errors to own table
                     ▼
┌─────────────────────────────────┐
│  Database Tables                │
│  • staging_extractions          │
│  • improvement_suggestions      │
│  (error_log JSONB column)       │
└─────────────────────────────────┘
                     │
                     │ Periodic sync (manual or scheduled)
                     ▼
┌─────────────────────────────────┐
│  Notion Errors Database         │
│  (Human review & resolution)    │
└─────────────────────────────────┘
```

## Quick Start

### 1. Import the ErrorLogger

```python
from src.curator.error_logger import ErrorLogger

logger = ErrorLogger()
```

### 2. Log errors in your agent code

**For Extractor/Validator (staging_extractions table):**

```python
try:
    # Your extraction/validation logic
    result = extract_from_url(url)
except Exception as e:
    # Capture the exception
    error_msg, stack_trace = ErrorLogger.capture_exception(e)

    # Log to database
    logger.log_to_extraction(
        extraction_id=extraction_id,
        error_type='extraction_failed',
        error_message=error_msg,
        stack_trace=stack_trace,
        context={
            'url': url,
            'ecosystem': 'fprime',
            'attempt': 1
        }
    )
    # Continue processing other items...
```

**For Analyzer (improvement_suggestions table):**

```python
try:
    # Your analysis logic
    suggestions = analyze_patterns()
except Exception as e:
    error_msg, stack_trace = ErrorLogger.capture_exception(e)

    logger.log_to_suggestion(
        suggestion_id=suggestion_id,
        error_type='analysis_failed',
        error_message=error_msg,
        stack_trace=stack_trace,
        context={'pattern_count': len(patterns)}
    )
```

## Error Types

Use descriptive error types for categorization:

**Extraction Errors:**
- `extraction_failed` - General extraction failure
- `api_timeout` - API request timeout
- `invalid_response` - Malformed API response
- `parsing_error` - Failed to parse document
- `validation_failed` - Validation checks failed

**Analysis Errors:**
- `analysis_failed` - General analysis failure
- `insufficient_data` - Not enough data to analyze
- `pattern_detection_error` - Pattern matching failed
- `confidence_calculation_error` - Confidence scoring failed

**Sync Errors:**
- `notion_sync_failed` - Failed to sync to Notion
- `database_error` - Database operation failed

## Error Log Structure

Errors are stored as JSONB in the `error_log` column:

```json
[
  {
    "error_type": "extraction_failed",
    "message": "Connection timeout after 30s",
    "logged_at": "2025-12-28T10:30:00Z",
    "stack_trace": "Traceback (most recent call last):\n  File...",
    "context": {
      "url": "https://github.com/nasa/fprime",
      "ecosystem": "fprime",
      "attempt": 1
    }
  }
]
```

## Viewing Errors

### In Database

Query all recent errors:
```sql
SELECT * FROM all_errors
ORDER BY last_error_at DESC
LIMIT 10;
```

Query errors for a specific extraction:
```sql
SELECT error_log, error_count, last_error_at
FROM staging_extractions
WHERE extraction_id = 'your-uuid-here';
```

### In Python

```python
from src.curator.error_logger import ErrorLogger

logger = ErrorLogger()

# Get recent errors from all tables
errors = logger.get_recent_errors(table='all', limit=10)

# Get errors from specific table
extraction_errors = logger.get_recent_errors(table='staging_extractions', limit=5)
```

## Notion Database Properties

The Errors database in Notion has the following properties:

- **Title** (title) - Error summary
- **Error Severity** (select) - Type of error (extraction_failed, api_timeout, etc.)
- **Source** (select) - Source table (staging_extraction, improvement_suggestion)
- **Number** (number) - Total error count
- **Date Reported** (date) - When the error was logged
- **Status** (status) - Error resolution status (New, Investigating, Resolved, Ignored)
- **Error Description** (select) - Not used by sync script

## Syncing to Notion

### Manual Sync

Run the sync script to push recent errors to Notion:

```bash
# Sync errors from last 24 hours (default)
python -X utf8 sync_errors_to_notion.py

# Sync errors from last 7 days
python -X utf8 sync_errors_to_notion.py 168
```

The sync script will:
1. Query the `all_errors` view for recent errors
2. Create a Notion page for each error with full details
3. Include error message, stack trace, context, and source info in page content

### Scheduled Sync (Optional)

Add to cron or Windows Task Scheduler:
```bash
# Every hour
0 * * * * cd /path/to/curator-agent && python -X utf8 sync_errors_to_notion.py
```

## Best Practices

1. **Always log context** - Include relevant information (URL, ecosystem, attempt number, etc.)
2. **Use descriptive error types** - Makes filtering and analysis easier
3. **Don't let errors stop workflow** - Log and continue processing other items
4. **Review errors periodically** - Check Notion database for patterns
5. **Clean old errors** - Archive or delete resolved errors to keep the log manageable

## Example: Full Agent Integration

```python
from src.curator.error_logger import ErrorLogger
import psycopg

logger = ErrorLogger()
db_url = os.getenv('NEON_DATABASE_URL')

def process_extractions():
    """Process pending extractions with error logging"""
    conn = psycopg.connect(db_url)

    with conn.cursor() as cur:
        cur.execute("SELECT extraction_id, candidate_key FROM staging_extractions WHERE status = 'pending'")
        pending = cur.fetchall()

    conn.close()

    for extraction_id, candidate_key in pending:
        try:
            # Your processing logic here
            result = process_extraction(extraction_id)

            # Update success status
            update_status(extraction_id, 'completed')

        except Exception as e:
            # Log the error
            error_msg, stack_trace = ErrorLogger.capture_exception(e)

            logger.log_to_extraction(
                extraction_id=extraction_id,
                error_type='processing_failed',
                error_message=error_msg,
                stack_trace=stack_trace,
                context={'candidate_key': candidate_key}
            )

            # Update failed status
            update_status(extraction_id, 'failed')

            # Continue with next extraction
            continue
```

## Database Schema

### Error Columns (added by migration 007)

```sql
-- In staging_extractions and improvement_suggestions
error_log JSONB DEFAULT '[]'::jsonb,  -- Array of error entries
error_count INTEGER DEFAULT 0,         -- Total errors logged
last_error_at TIMESTAMP WITH TIME ZONE -- Last error timestamp
```

### Indexes

```sql
-- For efficient error queries
CREATE INDEX idx_staging_extractions_errors
ON staging_extractions(last_error_at)
WHERE error_count > 0;

CREATE INDEX idx_suggestions_errors
ON improvement_suggestions(last_error_at)
WHERE error_count > 0;
```

### View: all_errors

Aggregates errors from all tables:
```sql
SELECT * FROM all_errors;
```

Returns: `source_table, record_id, record_name, error_log, error_count, last_error_at`
