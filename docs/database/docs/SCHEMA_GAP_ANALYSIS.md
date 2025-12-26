# Database Schema Gap Analysis - Lineage System

**Date:** 2025-12-24
**Purpose:** Identify what's needed vs. what exists for ID-based lineage tracking

---

## Current State Summary

### ✅ What You Already Have

**1. raw_snapshots** ✓ Excellent foundation
```
✓ id (uuid)                    - Snapshot ID tracking
✓ source_url (text)            - Source traceability
✓ content_hash (text)          - ALREADY HAS CHECKSUM! 🎉
✓ payload (jsonb)              - Raw data storage
✓ payload_size_bytes (int)     - Size tracking
✓ captured_at (timestamp)      - Temporal tracking
✓ captured_by_run_id (uuid)    - Run lineage
```

**2. staging_extractions** ✓ Good structure
```
✓ extraction_id (uuid)         - Extraction ID tracking
✓ snapshot_id (uuid)           - Links to raw_snapshots
✓ pipeline_run_id (uuid)       - Run lineage
✓ evidence (jsonb)             - Evidence storage
✓ confidence_score (numeric)   - Confidence tracking
✓ status (enum)                - Workflow state
```

**3. validation_decisions** ✓ Decision tracking
```
✓ decision_id (uuid)           - Decision ID
✓ extraction_id (uuid)         - Links to extraction
✓ decided_by (text)            - Who decided
✓ decision (enum)              - Accept/reject/etc
✓ confidence_at_decision       - Confidence snapshot
✓ evidence_at_decision         - Evidence snapshot
```

**4. core_entities** ✅ TRUTH TABLE EXISTS!
```
✓ id (uuid)                    - Entity ID
✓ source_snapshot_id (uuid)    - Lineage to snapshot!
✓ created_by_run_id (uuid)     - Run lineage
✓ is_current (boolean)         - Version tracking
✓ version (integer)            - Versioning
```

**5. pipeline_runs** ✓ Job tracking
```
✓ id (uuid)                    - Run ID
✓ run_name (text)              - Identifiable runs
✓ triggered_by (text)          - Who/what triggered
✓ error_count (integer)        - Error tracking
✓ last_error (text)            - Error details
```

---

## 🔍 What's Missing for Complete Lineage

### 1. raw_snapshots - Minor Additions Needed

**Current:**
```sql
content_hash          text  -- ✓ Already checksums!
```

**Need to Add:**
```sql
-- Just rename/clarify existing field
ALTER TABLE raw_snapshots
  RENAME COLUMN content_hash TO payload_checksum;  -- More explicit naming

-- Optional: Add thread tracking
ALTER TABLE raw_snapshots
  ADD COLUMN fetched_by_thread_id TEXT;  -- LangGraph thread ID
```

**Status:** 95% ready! Just need to add thread tracking.

---

### 2. staging_extractions - Add Lineage Verification Fields

**Missing Fields:**
```sql
ALTER TABLE staging_extractions ADD COLUMN
  -- Evidence checksums (verify evidence hasn't changed)
  evidence_checksum TEXT,
  evidence_byte_offset INTEGER,      -- Where in snapshot
  evidence_byte_length INTEGER,      -- Length of quote

  -- Lineage verification (validator populates)
  lineage_verified BOOLEAN DEFAULT FALSE,
  lineage_verified_at TIMESTAMPTZ,
  lineage_confidence NUMERIC(3,2),  -- 0.0 to 1.0
  lineage_verification_details JSONB,

  -- Re-extraction tracking (auto-retry logic)
  extraction_attempt INTEGER DEFAULT 1,
  is_reextraction BOOLEAN DEFAULT FALSE,
  reextraction_reason TEXT,
  original_extraction_id UUID REFERENCES staging_extractions(extraction_id),

  -- Mandatory review flags
  requires_mandatory_review BOOLEAN DEFAULT FALSE,
  mandatory_review_reason TEXT,

  -- Thread tracking
  extracted_by_thread_id TEXT;
```

**Constraints to Add:**
```sql
ALTER TABLE staging_extractions ADD CONSTRAINT
  valid_lineage_confidence
    CHECK (lineage_confidence IS NULL OR lineage_confidence BETWEEN 0 AND 1);

ALTER TABLE staging_extractions ADD CONSTRAINT
  lineage_verified_requires_confidence
    CHECK (NOT lineage_verified OR lineage_confidence IS NOT NULL);

ALTER TABLE staging_extractions ADD CONSTRAINT
  reextraction_must_reference_original
    CHECK (NOT is_reextraction OR original_extraction_id IS NOT NULL);
```

---

### 3. validation_decisions - Add Lineage Check Results

**Missing Fields:**
```sql
ALTER TABLE validation_decisions ADD COLUMN
  -- Lineage verification record
  lineage_check_passed BOOLEAN NOT NULL DEFAULT TRUE,
  lineage_check_details JSONB;  -- What was verified
```

---

### 4. core_entities - Already Perfect! ✅

**No changes needed!** Already has:
- `source_snapshot_id` - Traces back to raw data ✓
- `created_by_run_id` - Audit trail ✓
- `is_current` - Version control ✓

Only thing we might add later (not now):
```sql
-- Future: Add human approval metadata
ALTER TABLE core_entities ADD COLUMN
  approved_by TEXT,           -- Who approved
  approved_at TIMESTAMPTZ,    -- When approved
  approval_method TEXT;       -- 'notion_webhook', 'manual', etc.
```

But this can wait until we implement Notion integration.

---

## 📋 Migration Script

### Step 1: Rename Existing Field (Clarity)

```sql
-- raw_snapshots: Just rename for clarity
ALTER TABLE raw_snapshots
  RENAME COLUMN content_hash TO payload_checksum;

COMMENT ON COLUMN raw_snapshots.payload_checksum IS
  'SHA256 checksum of payload JSONB for integrity verification';
```

### Step 2: Add Lineage Fields to staging_extractions

```sql
ALTER TABLE staging_extractions ADD COLUMN
  -- Evidence integrity
  evidence_checksum TEXT,
  evidence_byte_offset INTEGER,
  evidence_byte_length INTEGER,

  -- Lineage verification
  lineage_verified BOOLEAN DEFAULT FALSE,
  lineage_verified_at TIMESTAMPTZ,
  lineage_confidence NUMERIC(3,2),
  lineage_verification_details JSONB,

  -- Re-extraction tracking
  extraction_attempt INTEGER DEFAULT 1,
  is_reextraction BOOLEAN DEFAULT FALSE,
  reextraction_reason TEXT,
  original_extraction_id UUID REFERENCES staging_extractions(extraction_id),

  -- Mandatory review
  requires_mandatory_review BOOLEAN DEFAULT FALSE,
  mandatory_review_reason TEXT,

  -- Thread tracking
  extracted_by_thread_id TEXT;

-- Add constraints
ALTER TABLE staging_extractions ADD CONSTRAINT
  valid_lineage_confidence
    CHECK (lineage_confidence IS NULL OR lineage_confidence BETWEEN 0 AND 1);

ALTER TABLE staging_extractions ADD CONSTRAINT
  lineage_verified_requires_confidence
    CHECK (NOT lineage_verified OR lineage_confidence IS NOT NULL);

ALTER TABLE staging_extractions ADD CONSTRAINT
  reextraction_must_reference_original
    CHECK (NOT is_reextraction OR original_extraction_id IS NOT NULL);

-- Add indexes for performance
CREATE INDEX idx_extractions_lineage
  ON staging_extractions(lineage_verified, lineage_confidence);

CREATE INDEX idx_extractions_checksum
  ON staging_extractions(evidence_checksum);

CREATE INDEX idx_extractions_mandatory_review
  ON staging_extractions(requires_mandatory_review)
  WHERE requires_mandatory_review = TRUE;

CREATE INDEX idx_extractions_reextraction
  ON staging_extractions(is_reextraction, extraction_attempt);
```

### Step 3: Add Lineage Fields to validation_decisions

```sql
ALTER TABLE validation_decisions ADD COLUMN
  lineage_check_passed BOOLEAN NOT NULL DEFAULT TRUE,
  lineage_check_details JSONB;

CREATE INDEX idx_decisions_lineage_check
  ON validation_decisions(lineage_check_passed);
```

### Step 4: Add Thread Tracking to raw_snapshots

```sql
ALTER TABLE raw_snapshots ADD COLUMN
  fetched_by_thread_id TEXT;

CREATE INDEX idx_snapshots_thread
  ON raw_snapshots(fetched_by_thread_id);
```

---

## 🎯 Impact Analysis

### Existing Data

**Your 6 PROVES Prime extractions:**
- Already in staging_extractions ✓
- Already have snapshot_id linking to raw_snapshots ✓
- Already have evidence field ✓

**After migration:**
- All new columns will be NULL (expected)
- Can retroactively verify lineage:

```sql
-- Retroactive lineage verification
UPDATE staging_extractions
SET
  lineage_verified = TRUE,
  lineage_confidence = 1.0,
  extraction_attempt = 1,
  is_reextraction = FALSE,
  evidence_checksum = encode(sha256(evidence->>'raw_text'::bytea), 'hex')
WHERE extraction_id IN (
  SELECT extraction_id FROM staging_extractions WHERE created_at >= '2025-12-24'
);
```

### New Extractions

**From next extraction forward:**
- Extractor will populate: evidence_checksum, byte_offset, thread_id
- Validator will populate: lineage_verified, lineage_confidence, details
- Storage will check: lineage_confidence >= threshold before allowing review

---

## 📊 Storage Impact

### Estimated Storage Increase

**Per raw_snapshot:**
- fetched_by_thread_id: ~50 bytes
- Total: 50 bytes/snapshot

**Per staging_extraction:**
- evidence_checksum: 64 bytes (sha256 hex)
- evidence_byte_offset: 4 bytes (int)
- evidence_byte_length: 4 bytes (int)
- lineage_verified: 1 byte (bool)
- lineage_confidence: 8 bytes (numeric)
- lineage_verification_details: ~500 bytes avg (jsonb)
- extraction_attempt: 4 bytes (int)
- is_reextraction: 1 byte (bool)
- reextraction_reason: ~100 bytes avg
- requires_mandatory_review: 1 byte (bool)
- mandatory_review_reason: ~100 bytes avg
- extracted_by_thread_id: ~50 bytes
- Total: ~837 bytes/extraction

**For 60 pages × 5.7 extractions/page = 342 extractions:**
- 342 × 837 bytes = 286 KB

**Negligible!** Less than one small image.

---

## 🔒 Data Integrity Benefits

### Before Lineage System

```
Extraction says: "Component is MSP430FR"
Evidence says: "Ultra-low power supervisor"
Question: Can we trust this came from the documentation?
Answer: We assume yes, but can't prove it
```

### After Lineage System

```
Extraction ID: ext-456
  ↓ evidence_checksum: a3f2b1c4...
  ↓ snapshot_id: abc-123
  ↓ payload_checksum: d5e6f7g8...

Verification:
  ✓ Evidence "Ultra-low power supervisor" found at byte 12,456
  ✓ Evidence checksum matches
  ✓ Snapshot checksum valid
  ✓ No tampering detected

Lineage Confidence: 1.0 (VERIFIED)
```

**Result:** Mathematical certainty that extraction came from documented source.

---

## 🚀 Implementation Recommendation

### Phase 1: Schema Migration (30 minutes)
1. Run Step 1: Rename content_hash → payload_checksum
2. Run Step 2: Add fields to staging_extractions
3. Run Step 3: Add fields to validation_decisions
4. Run Step 4: Add thread tracking to raw_snapshots
5. Verify with `\d+ staging_extractions` in psql

### Phase 2: Retroactive Verification (15 minutes)
1. Calculate checksums for existing 6 extractions
2. Verify lineage for existing data
3. Set lineage_confidence = 1.0 for verified items

### Phase 3: Code Updates (2-3 hours)
1. Update extractor to populate checksums
2. Update validator to perform lineage checks
3. Update storage to verify before allowing review
4. Add re-extraction logic

### Phase 4: Testing (1 hour)
1. Run one new extraction (FC Board)
2. Verify checksums are calculated
3. Verify lineage check passes
4. Check Neon database for populated fields

**Total Time: ~4 hours of work**

---

## ✅ Summary: You're 95% There!

**What you already have:**
- ✅ core_entities table exists (truth database)
- ✅ Snapshot checksums (content_hash)
- ✅ Extraction IDs
- ✅ Foreign key relationships
- ✅ Evidence storage
- ✅ Validation decisions

**What you need to add:**
- 🔧 11 new columns to staging_extractions
- 🔧 2 new columns to validation_decisions
- 🔧 1 new column to raw_snapshots
- 🔧 5 indexes for performance
- 🔧 3 constraints for data integrity

**Total changes:** ~20 lines of SQL

**Your schema is already well-designed!** We just need to add lineage tracking metadata.
