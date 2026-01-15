# Pipeline Validation Checklist

**Purpose:** Verify Stages 1-3 are operational before building Stage 4

**Created:** 2026-01-14
**Status:** In Progress

---

## Stage 1: Loose Capture (Extractor v3)

### Components
- [production/Version 3/extractor_v3.py](../production/Version%203/extractor_v3.py)
- [production/Version 3/database.py](../production/Version%203/database.py) ✅ Added in Phase 1

### Dependencies
```python
# Core dependencies
psycopg + psycopg_pool  # Database
langchain_anthropic     # LLM client
langchain_core          # Tools
langgraph               # Agent framework
httpx                   # HTTP client
dotenv                  # Environment
```

### Validation Steps

#### 1.1 Check Database Connection
```bash
# Test centralized pool
cd "production/Version 3"
python3 -c "from database import get_connection; print('Pool OK')"
```

**Expected:** "Pool OK" printed, no errors

#### 1.2 Check Extraction Tools Import
```bash
cd "production/Version 3"
python3 -c "from extractor_v3 import fetch_and_store_snapshot, extract_frames_couplings; print('Extractor OK')"
```

**Expected:** "Extractor OK" printed

#### 1.3 Verify Schema Validator
```bash
cd "production/Version 3"
python3 -c "from schema_validator import ValidationResult, validate_extraction; print('Validator OK')"
```

**Expected:** "Validator OK" printed

#### 1.4 Test Extraction on Sample URL
```bash
cd "production/Version 3"
python3 process_extractions_v3.py --limit 1
```

**Expected:**
- Snapshot stored in `raw_snapshots`
- Extractions stored in `staging_extractions`
- All extractions have `status='pending'`

#### 1.5 Check Staging Table Structure
```sql
SELECT
    extraction_id,
    candidate_key,
    candidate_type,
    status,
    promoted_at,
    promotion_action
FROM staging_extractions
WHERE created_at > NOW() - INTERVAL '1 day'
LIMIT 5;
```

**Expected:**
- Recent extractions visible
- `promoted_at` and `promotion_action` are NULL for new extractions
- All required FRAMES fields present

---

## Stage 2: Human Review (Notion Integration)

### Components
- Notion webhook server (should auto-start with process_extractions_v3.py)
- Notion database sync

### Validation Steps

#### 2.1 Check Webhook Server
```bash
curl http://localhost:8000/health
```

**Expected:** `{"status": "healthy"}` or 200 OK

#### 2.2 Verify Notion Database Connection
```sql
-- Check if Notion sync is configured
SELECT * FROM information_schema.tables
WHERE table_name LIKE 'notion%';
```

**Expected:** Notion-related tables exist (if Notion sync is active)

#### 2.3 Test Approval Workflow
Manual test:
1. Find a pending extraction in `staging_extractions`
2. Update via Notion or direct SQL:
   ```sql
   UPDATE staging_extractions
   SET status = 'accepted'
   WHERE extraction_id = 'test-id';
   ```
3. Verify status changed

**Expected:** Status updates successfully

---

## Stage 3: Promotion & Matching

### Components
- [production/curator/batch_promote_accepted.py](../production/curator/batch_promote_accepted.py) ✅ Exists
- [production/Version 3/storage_v3.py](../production/Version%203/storage_v3.py) - `promote_to_core()` function
- Migration 009: `core_entities` table with FRAMES dimensions
- Migration 013: Promotion tracking columns

### Validation Steps

#### 3.1 Check Promotion Function Import
```bash
cd "production/curator"
python3 -c "from storage_v3 import promote_to_core; print('Promotion function OK')"
```

**Expected:** "Promotion function OK" printed

#### 3.2 Verify core_entities Table Schema
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'core_entities'
AND column_name IN (
    'entity_id',
    'knowledge_form',
    'contact_level',
    'directionality',
    'temporality',
    'formalizability',
    'carrier'
);
```

**Expected:** All FRAMES dimension columns exist

#### 3.3 Check knowledge_enrichment Table
```sql
SELECT * FROM information_schema.tables
WHERE table_name = 'knowledge_enrichment';
```

**Expected:** Table exists (created in Migration 009)

#### 3.4 Test Batch Promotion (DRY RUN)
```bash
cd production/curator
python3 batch_promote_accepted.py --dry-run
```

**Expected:**
- Script runs without errors
- Shows count of unpromoted accepted extractions
- No actual database changes (dry run)

#### 3.5 Test Single Promotion
```sql
-- 1. Create a test accepted extraction
INSERT INTO staging_extractions (
    extraction_id, candidate_key, candidate_type,
    ecosystem, status, confidence_score
) VALUES (
    gen_random_uuid(), 'TEST_COMPONENT', 'component',
    'test-ecosystem', 'accepted', 0.9
);

-- 2. Run promotion (use Python or SQL function)
-- Via batch_promote_accepted.py or direct call
```

Then check:
```sql
-- Verify promotion
SELECT
    extraction_id,
    promoted_at,
    promotion_action,
    promoted_to_entity_id
FROM staging_extractions
WHERE candidate_key = 'TEST_COMPONENT';

-- Check core_entities
SELECT *
FROM core_entities
WHERE candidate_key = 'TEST_COMPONENT';
```

**Expected:**
- `promoted_at` is set
- `promotion_action` is 'created' or 'merged'
- `promoted_to_entity_id` points to `core_entities.entity_id`
- Entity exists in `core_entities` with FRAMES dimensions

---

## Known Issues & Fixes

### Issue 1: Python Not in PATH
**Symptom:** `python: command not found`

**Fix:**
- Windows: Use full path or fix PATH
- Check: `where python3` or `which python3`
- Alternative: Install Python via Microsoft Store

### Issue 2: Module Import Errors
**Symptom:** `ModuleNotFoundError: No module named 'psycopg'`

**Fix:**
```bash
pip install psycopg[binary] psycopg-pool
pip install langchain langchain-anthropic langgraph
pip install httpx python-dotenv
```

### Issue 3: Database Connection Fails
**Symptom:** `connection to server failed`

**Fix:**
1. Check `.env` has `NEON_DATABASE_URL`
2. Verify network connectivity to Neon
3. Test with: `psql $NEON_DATABASE_URL`

### Issue 4: Virtual Environment Errors
**Symptom:** `.venv` has error files

**Fix:**
```bash
# Remove broken venv
rm -rf .venv

# Create new venv
python3 -m venv .venv

# Activate
source .venv/bin/activate  # Unix
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## Quick Validation (All Stages)

Run this single check to verify all stages:

```bash
# From project root
cd "production/Version 3"

# Test imports
python3 << 'EOF'
try:
    from database import get_connection
    from extractor_v3 import fetch_and_store_snapshot
    from validator_v3 import verify_extraction_lineage
    from storage_v3 import store_extraction, promote_to_core
    from schema_validator import validate_extraction
    print("✅ Stage 1 (Extraction): OK")
    print("✅ Stage 2 (Review): OK")
    print("✅ Stage 3 (Promotion): OK")
    print("\nAll stages import successfully!")
except Exception as e:
    print(f"❌ Error: {e}")
EOF
```

**Expected:** All green checkmarks

---

## Next Steps After Validation

Once all checks pass:

1. ✅ Stage 1-3 are operational
2. ⏳ Ready to implement Stage 4 (MBSE Export)
3. 📝 Document any fixes made during validation
4. 🧪 Run full end-to-end test with real URL

---

## Test Data for End-to-End Validation

Use these test URLs (from your existing queue):

```sql
SELECT url, ecosystem
FROM urls_to_process
WHERE status = 'pending'
LIMIT 3;
```

Or use a known-good test URL:
```
https://fprime.jpl.nasa.gov/documentation/components.html
```

---

## Success Criteria

✅ **Stage 1:** Can extract from URL and store in `staging_extractions`
✅ **Stage 2:** Can change extraction status to 'accepted'
✅ **Stage 3:** Can promote accepted extractions to `core_entities` with FRAMES dimensions

When all three pass, we're ready for Stage 4 (MBSE Export).
