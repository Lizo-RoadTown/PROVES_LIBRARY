# Human Approval Workflow Schema Analysis

## Current Schema (What We Have)

### staging_extractions
**Purpose:** Inbox for all extractions pending review

**Columns (from migrations + storage code):**
```sql
-- Core extraction data
extraction_id UUID PRIMARY KEY
pipeline_run_id UUID
snapshot_id UUID
agent_id TEXT
agent_version TEXT
candidate_type candidate_type  -- enum
candidate_key TEXT
candidate_payload JSONB
ecosystem ecosystem_type
confidence_score NUMERIC
confidence_reason TEXT
evidence JSONB
evidence_type evidence_type
created_at TIMESTAMPTZ

-- Status tracking
status candidate_status  -- enum (at least 'pending', possibly others)

-- Lineage verification (from migration 001)
evidence_checksum TEXT
evidence_byte_offset INTEGER
evidence_byte_length INTEGER
lineage_verified BOOLEAN DEFAULT FALSE
lineage_verified_at TIMESTAMPTZ
lineage_confidence NUMERIC(3,2)
lineage_verification_details JSONB

-- Re-extraction tracking (from migration 001)
extraction_attempt INTEGER DEFAULT 1
is_reextraction BOOLEAN DEFAULT FALSE
reextraction_reason TEXT
original_extraction_id UUID REFERENCES staging_extractions(extraction_id)

-- Mandatory review (from migration 001)
requires_mandatory_review BOOLEAN DEFAULT FALSE
mandatory_review_reason TEXT

-- Thread tracking (from migration 001)
extracted_by_thread_id TEXT

-- Review tracking (from migration 005)
reviewed_at TIMESTAMPTZ
review_decision TEXT CHECK (review_decision IN ('approve', 'reject'))
review_notes TEXT

-- Notion integration (from migration 003)
notion_page_id TEXT
notion_synced_at TIMESTAMPTZ
notion_last_sync_attempt TIMESTAMPTZ
notion_sync_error TEXT
```

### knowledge_epistemics
**Purpose:** Sidecar table for epistemic metadata (7-Question Knowledge Capture Checklist)

Stores all epistemic fields from the 7-Question framework.

### validation_decisions
**Purpose:** Referenced in migrations, appears to log validation actions

**Columns (from migration 001):**
```sql
-- (Base columns unknown - need to check actual table)
lineage_check_passed BOOLEAN DEFAULT TRUE
lineage_check_details JSONB
```

---

## Suggested Schema (From AI Recommendations)

### 1. Keep staging_extractions as inbox (one table)

**Suggested additions:**
```sql
status ENUM: pending | accepted | rejected | needs_context | merged
current_revision INTEGER  -- or version
latest_decision_id UUID REFERENCES validation_decisions(id)
assigned_to TEXT  -- optional
reviewed_at TIMESTAMPTZ  -- ✅ Already have this
```

### 2. Add/enhance validation_decisions (append-only log)

**Purpose:** Audit trail for all human actions

**Suggested columns:**
```sql
id UUID PRIMARY KEY
extraction_id UUID REFERENCES staging_extractions(extraction_id)
action_type TEXT  -- accept | reject | edit | merge | request_more_evidence
actor_id TEXT  -- Notion user ID
reason TEXT
patch JSONB  -- JSON Patch format for edits
timestamp TIMESTAMPTZ
source TEXT  -- notion webhook id for idempotency
```

**Usage:**
- Each webhook-triggered action writes a new row
- Enables idempotency: "Have I already processed this webhook id?"
- Provides complete audit trail

### 3. Promotion to "truth" tables

**When human accepts:**
- Option A: Promote into `core_entities` / `core_edges` (new tables)
- Option B: Mark `core_entities.is_current = true` and version old ones

**Key principle:** Truth tables should only contain validated, canonical content

### 4. Handle edits/modifications

**Option A (Best for audit) - Immutable original + revisions:**
```sql
-- In staging_extractions:
parent_extraction_id UUID  -- or supersedes_extraction_id
revision_number INTEGER

-- When human edits:
1. Keep original row immutable (what agent proposed)
2. Create new staging revision row with incremented revision_number
3. Set parent_extraction_id to original
4. Status resets to 'pending' or 'accepted' if "accept with edits"
5. Log edit in validation_decisions with patch
```

**Option B (Simpler) - Mutate staging row with diff logging:**
```sql
-- Update candidate_payload in place
-- Log in validation_decisions with:
before_payload JSONB
after_payload JSONB
-- or JSON Patch format
```

**Warning:** If you mutate without logging diffs, you'll regret it later.

---

## Gap Analysis

### ✅ What We Already Have
1. `status` column (though enum values may need expansion)
2. `reviewed_at` timestamp
3. `review_decision` (approve/reject)
4. `review_notes` (can be used for reason)
5. `notion_page_id` for bidirectional sync
6. Lineage verification system
7. Re-extraction tracking with `original_extraction_id`

### ⚠️ What Needs Enhancement

#### staging_extractions
1. **Expand status enum** to include:
   - ✅ `pending` (have)
   - ❓ `accepted` (may exist, need to check)
   - ❓ `rejected` (may exist, need to check)
   - ➕ `needs_context` (add)
   - ➕ `merged` (add)

2. **Add versioning columns:**
   ```sql
   current_revision INTEGER DEFAULT 1
   latest_decision_id UUID REFERENCES validation_decisions(id)
   ```

3. **Add assignment tracking (optional):**
   ```sql
   assigned_to TEXT
   ```

4. **Add edit tracking (if using Option A):**
   ```sql
   parent_extraction_id UUID REFERENCES staging_extractions(extraction_id)
   revision_number INTEGER DEFAULT 1
   ```
   - Note: We already have `original_extraction_id` for re-extractions; could reuse or keep separate

#### validation_decisions
1. **Enhance to be full audit log:**
   ```sql
   ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
   id UUID PRIMARY KEY DEFAULT uuid_generate_v4();

   ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
   extraction_id UUID REFERENCES staging_extractions(extraction_id);

   ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
   action_type TEXT CHECK (action_type IN (
       'accept', 'reject', 'edit', 'merge', 'request_more_evidence'
   ));

   ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
   actor_id TEXT;  -- Notion user ID

   ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
   reason TEXT;

   ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
   before_payload JSONB;  -- For edits

   ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
   after_payload JSONB;  -- For edits

   ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
   patch JSONB;  -- JSON Patch format (alternative to before/after)

   ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
   timestamp TIMESTAMPTZ DEFAULT NOW();

   ALTER TABLE validation_decisions ADD COLUMN IF NOT EXISTS
   source TEXT;  -- Notion webhook ID for idempotency

   -- Idempotency constraint
   ALTER TABLE validation_decisions ADD CONSTRAINT
   unique_webhook_source UNIQUE(source)
   WHERE source IS NOT NULL;
   ```

#### New "Truth" Tables (Optional but Recommended)
```sql
-- Option A: Separate truth tables
CREATE TABLE core_entities (
    entity_id UUID PRIMARY KEY,
    extraction_id UUID REFERENCES staging_extractions(extraction_id),
    -- ... entity fields ...
    accepted_at TIMESTAMPTZ,
    accepted_by TEXT,
    is_current BOOLEAN DEFAULT TRUE,
    superseded_by UUID REFERENCES core_entities(entity_id)
);

CREATE TABLE core_edges (
    edge_id UUID PRIMARY KEY,
    extraction_id UUID REFERENCES staging_extractions(extraction_id),
    source_entity_id UUID REFERENCES core_entities(entity_id),
    target_entity_id UUID REFERENCES core_entities(entity_id),
    -- ... edge fields (FRAMES metadata) ...
    accepted_at TIMESTAMPTZ,
    accepted_by TEXT,
    is_current BOOLEAN DEFAULT TRUE,
    superseded_by UUID REFERENCES core_edges(edge_id)
);
```

---

## Recommendations

### Immediate Actions (High Priority)

1. **Check current status enum values:**
   ```sql
   SELECT enumlabel FROM pg_enum
   WHERE enumtypid = 'candidate_status'::regtype
   ORDER BY enumsortorder;
   ```

2. **Enhance validation_decisions table:**
   - Add full audit trail columns
   - Add source column for webhook idempotency
   - Add before/after payload tracking for edits

3. **Update Notion webhook handler to:**
   - Check `source` (webhook ID) for idempotency
   - Write to validation_decisions for every action
   - Update staging_extractions status accordingly

### Medium Priority

4. **Add versioning to staging_extractions:**
   - `current_revision` / `revision_number`
   - `latest_decision_id` foreign key

5. **Decide on edit strategy:**
   - **Option A:** Immutable original + revision rows (better audit trail)
   - **Option B:** Mutate in place + log diff (simpler)

### Lower Priority (But Important for Scale)

6. **Create truth tables:**
   - `core_entities` for accepted components/facts
   - `core_edges` for accepted dependencies/relationships
   - Clear separation: staging (all proposals) vs. core (validated truth)

7. **Add analytics views:**
   ```sql
   CREATE VIEW human_review_stats AS
   SELECT
       actor_id,
       action_type,
       COUNT(*) as action_count,
       AVG(EXTRACT(EPOCH FROM (timestamp - e.created_at))) as avg_response_time_seconds
   FROM validation_decisions d
   JOIN staging_extractions e ON d.extraction_id = e.extraction_id
   GROUP BY actor_id, action_type;
   ```

---

## Benefits of Suggested Approach

### 1. Audit Trail
- Every human action is logged immutably in `validation_decisions`
- Can replay history and understand "why did this change?"
- Training signal for future AI improvements

### 2. Idempotency
- Webhook deduplication via `source` column
- Safe to process same webhook multiple times
- No accidental double-processing

### 3. Analytics
- Track review patterns (who approves what, when)
- Identify extractions that need frequent editing (signal for agent improvement)
- Measure human-AI collaboration efficiency

### 4. Clean Truth
- Truth tables contain only validated content
- Staging remains as permanent record of "what was proposed"
- Clear separation enables different access patterns

### 5. Edit History
- Know exactly what changed and why
- Revert edits if needed
- Understand human correction patterns for agent training

---

## Migration Strategy

### Phase 1: Enhance Audit Trail
1. Update `validation_decisions` schema
2. Update Notion webhook handler to write decisions
3. Test idempotency

### Phase 2: Add Versioning
1. Add revision tracking to `staging_extractions`
2. Implement edit flow (Option A or B)
3. Update UI to show revision history

### Phase 3: Create Truth Layer
1. Create `core_entities` and `core_edges` tables
2. Add promotion logic when status → 'accepted'
3. Create views for querying current truth

---

## Questions to Answer

1. **What are the current values in the `candidate_status` enum?**
   - Need to check actual enum definition in database

2. **What columns currently exist in `validation_decisions`?**
   - Need to query information_schema or check base schema

3. **Edit strategy preference:**
   - Option A (immutable + revisions) or Option B (mutate + diff)?
   - Recommendation: Option A for better audit trail

4. **Truth table timing:**
   - Implement now or later?
   - Recommendation: Later, after audit trail is solid

5. **Notion webhook current behavior:**
   - Does it already write to `validation_decisions`?
   - Does it handle idempotency?
   - Need to review webhook handler code
