# Testing Instructions: Database Pooling Fix

**Created:** 2026-01-15
**Status:** Ready to test

---

## What Was Fixed

Fixed database connection pooling in 3 curator scripts:
1. ✅ [production/curator/batch_promote_accepted.py](../production/curator/batch_promote_accepted.py)
2. ✅ [production/curator/analyze_accepted_batch.py](../production/curator/analyze_accepted_batch.py)
3. ✅ [production/curator/subagents/url_fetcher.py](../production/curator/subagents/url_fetcher.py)

All now use the centralized pool from `production/Version 3/database.py`.

---

## Quick Test: Run an Extraction

The simplest way to test is to run an actual extraction:

```bash
cd "production/Version 3"
python process_extractions_v3.py --limit 1
```

**Expected behavior:**
- Script starts without import errors
- Fetches 1 URL from `urls_to_process` table
- Extracts FRAMES couplings
- Stores in `staging_extractions` table
- No database connection errors
- Connection pool statistics show usage

**If it fails:**
- Check error message for import issues
- Verify `.env` has `DATABASE_URL`
- Check Python dependencies are installed

---

## Test Each Fixed Script

### Test 1: batch_promote_accepted.py

```bash
cd production/curator
python batch_promote_accepted.py
```

**Expected:**
```
Found N accepted extractions awaiting promotion
Starting batch promotion...
[1/N] Processing: COMPONENT_NAME (ecosystem)... CREATED/MERGED/SKIPPED
...
BATCH PROMOTION SUMMARY REPORT
```

**If it fails with import error:**
- The pooling fix didn't work correctly
- Check the file has `from database import get_connection`

### Test 2: analyze_accepted_batch.py

```bash
cd production/curator
python analyze_accepted_batch.py
```

**Expected:**
```
[ANALYSIS] Analyzing accepted extractions batch...
Found N accepted extractions awaiting promotion
...
```

### Test 3: url_fetcher as tool

The url_fetcher is used by the agent, so it's tested when you run `process_extractions_v3.py`.

---

## Verify Connection Pool is Being Used

After running any of the above, check pool stats:

```python
from database import get_pool_stats
stats = get_pool_stats()
print(stats)
```

**Expected output:**
```python
{
    'size': 1-5,          # Number of connections in pool
    'min_size': 1,
    'max_size': 5,
    'idle': 0-5,          # Available connections
    'in_use': 0-1         # Active connections
}
```

---

## Common Issues

### Issue: ModuleNotFoundError: No module named 'database'

**Cause:** Path setup is wrong

**Fix:** The scripts add Version 3 to sys.path - verify this section exists:
```python
version3_path = project_root / 'production' / 'Version 3'
sys.path.insert(0, str(version3_path))

from database import get_connection
```

### Issue: Connection errors

**Cause:** Environment variable not set

**Fix:**
```bash
# Check .env file exists
cat .env | grep DATABASE_URL

# Or set manually
export DATABASE_URL="your_connection_string"
```

### Issue: "psycopg" module not found

**Cause:** Dependencies not installed

**Fix:**
```bash
pip install psycopg[binary] psycopg-pool
```

---

## Full Integration Test

To test the complete Stages 1-3 pipeline:

```bash
# 1. Run extraction (Stage 1)
cd "production/Version 3"
python process_extractions_v3.py --limit 1

# 2. Manually accept an extraction (Stage 2 - normally done via Notion)
# In psql or SQL client:
# UPDATE staging_extractions
# SET status = 'accepted'
# WHERE extraction_id = '<id_from_step1>';

# 3. Run promotion (Stage 3)
cd ../curator
python batch_promote_accepted.py

# 4. Verify in database
# SELECT * FROM core_entities ORDER BY created_at DESC LIMIT 5;
```

**Success criteria:**
- Stage 1 completes without errors
- Stage 2 status update works
- Stage 3 promotes to `core_entities`
- All FRAMES dimensions are present in `core_entities`
- No connection pool errors

---

## What if Python isn't in PATH?

### Option 1: Use full path

```bash
# Find Python
where python3
# Or: which python3

# Use full path
/full/path/to/python3 process_extractions_v3.py --limit 1
```

### Option 2: Activate virtual environment

```bash
# If you have a venv
source .venv/bin/activate  # Unix
.venv\Scripts\activate     # Windows

# Then run normally
python process_extractions_v3.py --limit 1
```

### Option 3: Use conda

```bash
conda activate proves_env
python process_extractions_v3.py --limit 1
```

---

## Success Checklist

- [ ] `process_extractions_v3.py --limit 1` runs successfully
- [ ] No "ModuleNotFoundError: database" errors
- [ ] Extraction stored in `staging_extractions`
- [ ] `batch_promote_accepted.py` runs (even if no accepted extractions)
- [ ] `analyze_accepted_batch.py` runs without errors
- [ ] Connection pool stats show connections being used
- [ ] No connection leaks (pool returns to idle state)

---

## Next Steps After Testing

Once all tests pass:
1. ✅ Mark Phase 1 as fully complete
2. ✅ Update roadmap with test results
3. ⏳ Begin Phase 3: MBSE Export (Stage 4)

If tests fail:
1. Document the specific error
2. Check which file has the issue
3. Verify the pooling fix was applied correctly
4. Test imports in isolation

---

## Quick Import Test (No Database Required)

If you just want to verify imports work:

```bash
cd "production/Version 3"
python3 -c "
from database import get_connection
from storage_v3 import promote_to_core
print('✅ Version 3 imports OK')
"

cd ../curator
python3 -c "
import sys
from pathlib import Path
project_root = Path.cwd().parent.parent
sys.path.insert(0, str(project_root / 'production' / 'Version 3'))

from database import get_connection
import batch_promote_accepted
import analyze_accepted_batch
print('✅ Curator imports OK')
"
```

**Expected:** Both print success messages, no errors.

---

## Test Results Log

Record test results here:

**Date:** ___________
**Tester:** ___________

| Test | Result | Notes |
|------|--------|-------|
| Import database module | ⬜ Pass / ⬜ Fail | |
| Run process_extractions_v3.py | ⬜ Pass / ⬜ Fail | |
| Run batch_promote_accepted.py | ⬜ Pass / ⬜ Fail | |
| Run analyze_accepted_batch.py | ⬜ Pass / ⬜ Fail | |
| Check pool stats | ⬜ Pass / ⬜ Fail | |
| Full integration test | ⬜ Pass / ⬜ Fail | |

**Overall Status:** ⬜ All Pass / ⬜ Some Fail / ⬜ Not Tested

---

**Once testing is complete, update [REFACTORING_ROADMAP.md](.deepagents/REFACTORING_ROADMAP.md) with test results.**
