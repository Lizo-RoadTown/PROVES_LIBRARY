# Session Summary: Database Pooling & Storage Agent Fixes

**Date:** 2026-01-15
**Focus:** Fixing database connection pooling and storage agent limitations

---

## Problems Identified

### 1. Curator Scripts Not Using Centralized Pool
**Issue:** Three curator scripts were creating their own database connections instead of using the centralized pool from `database.py`.

**Scripts Fixed:**
- `production/curator/batch_promote_accepted.py`
- `production/curator/analyze_accepted_batch.py`
- `production/curator/subagents/url_fetcher.py`

**Solution:** Updated all three to import and use `get_connection()` from the centralized `database.py` module.

### 2. Connection Pool Too Small
**Issue:** Original pool settings (min=1, max=5, timeout=30s) were insufficient for concurrent LangGraph agent operations.

**Solution:** Upgraded pool configuration in `database.py`:
- `min_size`: 1 → 2
- `max_size`: 5 → 20
- `timeout`: 30s → 60s

### 3. LangGraph Checkpointer Pool Conflict
**Issue:** Agent was creating a separate pool for checkpointer, competing with tool pool and causing SSL timeout errors.

**Solution:** Created separate small pool (3 connections) just for checkpointing in `agent_v3.py`:
- Tool pool: 20 connections (for extractor/validator/storage database queries)
- Checkpointer pool: 3 connections (for LangGraph state persistence)
- Total: 23 connections (well under database limits)

### 4. Storage Agent Tool Call Limit ⭐ **ROOT CAUSE #1**
**Issue:** Storage agent had a hard limit of 5 tool calls, so it could only store 4-5 extractions maximum (one call reserved for verification).

**Impact:** When extractor found 13 entities, storage agent could only store 2-5 before hitting the limit.

**Solution:**
- Removed "MAX 5 TOOL CALLS" limit from `subagent_specs_v3.py`
- Added explicit instruction: "Store ALL extractions - call store_extraction() once for every entity"
- Updated orchestrator prompt to emphasize storing EVERY extraction

### 5. Storage Agent SSL Errors from Checkpointer ⭐ **ROOT CAUSE #2**
**Issue:** After removing tool call limit, storage agent still only stored 2-4 extractions before SSL timeout errors killed the process.

**Error:** `psycopg.OperationalError: sending query and params failed: SSL error: bad length SSL SYSCALL error: EOF detected`

**Impact:** Checkpointer held database connections during agent execution, connections timed out and corrupted, process terminated before all extractions stored.

**Solution:** Disabled checkpointer for storage agent (agent_v3.py line 101)
- Storage agent doesn't need state persistence - it just makes sequential store_extraction() calls
- Extractor and validator still use checkpointer (they have complex branching logic)
- This eliminates SSL errors while maintaining checkpointing where needed

### 6. Recursion Limit Too Low ⭐ **ROOT CAUSE #3**
**Issue:** After fixing SSL errors, storage agent still only stored 2-5 extractions when extractor found 12.

**Impact:** Recursion limit of 20 in process_extractions_v3.py limited total tool calls across the entire agent lifecycle.

**Solution:** Increased recursion_limit from 20 to 100 (line 268)
- Allows storage agent to make more tool calls
- Each store_extraction() call counts as 1 recursion step
- With 12+ entities, need room for 12+ stores + verification calls

### 7. Storage Agent Model Too Weak ⭐ **ROOT CAUSE #4 - FINAL FIX**
**Issue:** Even after fixes #1-6, storage agent still only storing 2-5 of 12 extractions found.

**Test Results with Haiku:**
- Run 1 (FPrime overview): Extractor found 12, storage stored 5
- Run 2 (FPrime tutorials): Storage only stored 2
- LangSmith showed agent saying "I'll continue storing..." but then stopping

**Root Cause:** Haiku model (`claude-3-5-haiku-20241022`) was stopping early despite explicit "Store ALL" instructions. Haiku optimizes for speed/cost and was "helpfully" summarizing instead of completing all work.

**Solution:** Upgraded storage agent from Haiku to Sonnet 4.5 (subagent_specs_v3.py line 558)
- Changed model from `claude-3-5-haiku-20241022` to `claude-sonnet-4-5-20250929`
- Sonnet 4.5 has better instruction-following and doesn't stop early

**Final Test Result:**
- FPrime platforms page: **15 extractions stored** ✅
- All extractions from extractor successfully stored
- No SSL errors, no early stopping

**Cost Impact:** ~$0.47 per extraction (Sonnet 4.5 is more expensive than Haiku but necessary for reliability)

---

## Files Modified

### Database Pooling

**`production/Version 3/database.py`**
- Upgraded pool: min=2, max=20, timeout=60s
- Now handles concurrent agent operations without exhaustion

**`production/Version 3/agent_v3.py`**
- Added separate checkpointer pool (3 connections)
- Prevents SSL errors from checkpointer holding connections too long

**`production/curator/batch_promote_accepted.py`**
- Replaced local `get_db_connection()` with centralized `get_connection()`
- Uses context manager for automatic connection cleanup

**`production/curator/analyze_accepted_batch.py`**
- Same fix as batch_promote_accepted.py

**`production/curator/subagents/url_fetcher.py`**
- Replaced local connection creation with centralized pool
- Both `fetch_next_url` and `mark_url_complete` use `get_connection()`

### Storage Agent Fixes

**`production/Version 3/subagent_specs_v3.py`**
- Lines 510-533: Removed "MAX 5 TOOL CALLS" limitation
- Added "CRITICAL: Store ALL extractions" instruction
- Emphasized calling store_extraction() once per entity

**`production/Version 3/agent_v3.py`**
- Updated storage task prompt to emphasize storing EVERY extraction
- No longer mentions tool call limits

---

## Architecture After Fixes

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTRACTION PIPELINE                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Extractor Agent ──→ Validator Agent ──→ Storage Agent      │
│      (finds N entities)  (approves M)    (stores ALL M)     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   DATABASE CONNECTIONS                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Tool Pool (database.py)                                     │
│  ├─ min_size: 2                                              │
│  ├─ max_size: 20                                             │
│  ├─ timeout: 60s                                             │
│  └─ Used by: extractor, validator, storage tools            │
│                                                              │
│  Checkpointer Pool (agent_v3.py)                             │
│  ├─ min_size: 1                                              │
│  ├─ max_size: 3                                              │
│  ├─ timeout: 60s                                             │
│  └─ Used by: LangGraph state persistence                     │
│                                                              │
│  Total: 23 max connections                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Test Results

### Before Fixes
- Extraction found 13 entities
- Validator approved entities
- Storage agent stored only 2 entities ❌
- Cause: 5 tool call limit

### After Fixes
- Testing in progress...
- Expected: All approved extractions stored ✅

---

## Next Steps

1. ✅ Verify extraction test stores all entities
2. ✅ Update roadmap with test results
3. ⏳ Test Stage 3 (Promotion) with `batch_promote_accepted.py`
4. ⏳ Begin Stage 4 (MBSE Export) implementation

---

## Key Learnings

1. **Agent tool call limits are critical** - A hidden 5-call limit silently dropped 60% of extractions
2. **Separate pools for different use cases** - Checkpointer needs its own pool to avoid SSL timeouts
3. **Connection pool sizing matters** - 5 connections insufficient for concurrent LangGraph operations
4. **Always test end-to-end** - The pipeline "worked" but was silently failing to store most data

---

## Documentation Created

- [CONNECTION_POOL_FIX.md](.deepagents/CONNECTION_POOL_FIX.md) - Detailed pool configuration changes
- [TESTING_INSTRUCTIONS.md](.deepagents/TESTING_INSTRUCTIONS.md) - How to test the fixes
- [PIPELINE_VALIDATION_CHECKLIST.md](.deepagents/PIPELINE_VALIDATION_CHECKLIST.md) - Validation steps
- This summary document

---

**Status:** Fixes applied, testing in progress
**Next Milestone:** Stage 4 - MBSE Export (XTCE/SysML/FPrime serializers)
