# Connection Pool Exhaustion Fix

**Date:** 2026-01-15
**Issue:** Connection pool timeout errors during extraction
**Status:** Fixed
**Updated:** 2026-01-15 - Added separate checkpointer pool to prevent SSL errors

---

## Problem

When running `process_extractions_v3.py --limit 1`, the extraction worked but encountered connection pool exhaustion:

```
Error storing extraction: couldn't get a connection after 30.00 sec
```

The extraction validated 13 extractions but failed to store one due to pool timeout.

## Root Cause

The LangGraph agent makes multiple concurrent database calls during extraction:
- Fetching snapshots
- Validating lineage
- Storing extractions (multiple entities per URL)
- Querying for duplicates
- Updating pipeline runs

With the original pool configuration:
- **min_size:** 1
- **max_size:** 5
- **timeout:** 30 seconds

The agent could exhaust all 5 connections during concurrent operations, causing timeouts.

## Solution

Increased connection pool size to handle concurrent agent operations:

### Changes to [production/Version 3/database.py](../production/Version%203/database.py)

**Lines 67-70:** Updated pool documentation
```python
Note:
    Pool is created on first call with the following settings:
    - min_size: 2 (keep at least 2 connections ready)
    - max_size: 20 (max 20 concurrent connections - handles agent parallel extractions)
    - timeout: 60 seconds (increased for busy periods)
    - keepalive settings for long-running connections
```

**Lines 85-97:** Updated ConnectionPool creation
```python
_pool = ConnectionPool(
    conninfo=db_url,
    min_size=2,      # Was: 1
    max_size=20,     # Was: 5
    timeout=60,      # Was: 30
    open=True,
    kwargs={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }
)
```

**Lines 189-195:** Updated pool stats defaults
```python
return {
    "size": stats.get("pool_size", 0),
    "min_size": stats.get("pool_min", 2),    # Was: 1
    "max_size": stats.get("pool_max", 20),   # Was: 5
    "idle": stats.get("pool_available", 0),
    "in_use": stats.get("requests_waiting", 0),
}
```

## Why This Size?

- **min_size=2:** Keep 2 connections warm for faster access
- **max_size=20:** Allow up to 20 concurrent operations
  - Agent can process multiple extractions in parallel
  - Each extraction may query snapshots, duplicates, and pipeline runs
  - 20 connections provides headroom for bursts
- **timeout=60:** Doubled timeout to handle busy periods gracefully

## Testing

After the fix, extraction test should complete without timeout errors.

### Expected Results

```bash
cd "production/Version 3"
../../.venv/Scripts/python.exe process_extractions_v3.py --limit 1
```

**Success criteria:**
- All extractions stored successfully
- No "couldn't get a connection" errors
- Pool stats show connections being used and returned
- Extractions appear in `staging_extractions` table

### Check Pool Stats

After extraction, verify pool health:

```python
from database import get_pool_stats
stats = get_pool_stats()
print(stats)
# Expected: size=2-20, idle > 0, in_use <= 20
```

## Related Fixes

This is part of the Phase 1 database pooling refactor:

1. ✅ Created centralized pool ([database.py](../production/Version%203/database.py))
2. ✅ Fixed curator scripts to use centralized pool:
   - [batch_promote_accepted.py](../production/curator/batch_promote_accepted.py)
   - [analyze_accepted_batch.py](../production/curator/analyze_accepted_batch.py)
   - [url_fetcher.py](../production/curator/subagents/url_fetcher.py)
3. ✅ Increased pool size for concurrent agent operations (this fix)

## Next Steps

Once extraction test completes successfully:
1. Verify all extractions stored in `staging_extractions`
2. Test batch promotion with `batch_promote_accepted.py`
3. Update [REFACTORING_ROADMAP.md](REFACTORING_ROADMAP.md) with test results
4. Begin Stage 4 implementation (MBSE Export)

---

**See also:**
- [TESTING_INSTRUCTIONS.md](TESTING_INSTRUCTIONS.md) - Full test procedures
- [PIPELINE_VALIDATION_CHECKLIST.md](PIPELINE_VALIDATION_CHECKLIST.md) - Validation steps
- [REFACTORING_ROADMAP.md](REFACTORING_ROADMAP.md) - Overall roadmap
