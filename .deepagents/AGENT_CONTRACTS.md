# PROVES Agent Contracts Documentation

**Version:** 1.0.0
**Last Updated:** 2026-01-14
**Purpose:** Document the implicit contracts between agents in the extraction pipeline.

---

## Pipeline Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    EXTRACTOR    │ ──> │    VALIDATOR    │ ──> │     STORAGE     │
│                 │     │                 │     │                 │
│ Fetch + Extract │     │ Verify + Check  │     │ Persist Data    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Orchestrator:** `agent_v3.py` - Python control flow (not LangGraph routing)

---

## 1. Extractor Agent Contract

### Identity
- **Model:** `claude-sonnet-4-5-20250929`
- **Temperature:** 0.1
- **Max Tool Calls:** 1

### Input Contract

The extractor receives a task message from the orchestrator:

```
Extract architecture from this URL: {url}

Your task:
1. Fetch the page
2. Extract couplings using FRAMES methodology
3. Verify lineage (checksums, byte offsets)
4. Return results with snapshot_id and verified lineage data

Return format:
- snapshot_id: <uuid>
- source_url: {url}
- extractions: [list of extracted couplings with evidence]
- lineage_verified: true/false
- lineage_confidence: 0.0-1.0
```

### Tools Available

| Tool | Purpose | Returns |
|------|---------|---------|
| `fetch_webpage(url)` | Fetch documentation webpage | Content + snapshot_id |
| `fetch_github_file(owner, repo, path, branch)` | Fetch GitHub file | Content + snapshot_id |
| `list_github_directory(owner, repo, path, branch)` | List directory contents | File/folder listing |
| `read_document(doc_path)` | Read local file | Content + snapshot_id |
| `extract_architecture_using_claude(text, doc_name)` | FRAMES extraction | Structured extraction |
| `get_ontology()` | Get FRAMES reference | Ontology markdown |
| `query_verified_entities(...)` | Query core_entities | Verified entities list |
| `query_staging_history(...)` | Query past extractions | Historical extractions |
| `observe_staging_feedback(...)` | Learn from feedback | Accepted/rejected patterns |
| `read_memory_patterns()` | Read learned patterns | Pattern text |
| `update_memory_patterns(patterns)` | Update learned patterns | Confirmation |

### Output Contract

The extractor MUST return a message containing:

```yaml
Required Fields:
  snapshot_id: string (UUID)  # From fetch_webpage/fetch_github_file
  source_url: string          # The URL that was processed
  extractions: array          # List of candidates found

Each Extraction MUST Include:
  candidate_type: enum
    - component
    - interface
    - flow
    - mechanism
    - dependency
  candidate_key: string       # Unique identifier
  description: string         # What this entity is
  raw_evidence: string        # Exact quote from source
  confidence_score: float     # 0.0-1.0
  confidence_reason: string   # Why this confidence level

Optional (Recommended):
  epistemic_defaults: object  # Page-level defaults (anti-boilerplate)
  epistemic_overrides: object # Per-candidate overrides
  lineage_verified: boolean   # If lineage was verified
  lineage_confidence: float   # 0.0-1.0
```

### Success Criteria

The orchestrator checks for success:
```python
if "snapshot_id" not in final_message.lower() or "no couplings" in final_message.lower():
    return {"status": "failed", "stage": "extraction", ...}
```

---

## 2. Validator Agent Contract

### Identity
- **Model:** `claude-3-5-haiku-20241022`
- **Temperature:** 0.1
- **Max Tool Calls:** 5

### Input Contract

The validator receives the extractor's output as a task:

```
Validate the following extraction results:

{extractor_output}

Your task (USING NEW REFACTOR TOOLS):
1. Use validate_epistemic_structure() to check epistemic defaults + overrides
2. Use verify_evidence_lineage() to check lineage for each extraction
3. Check for duplicates in core_entities and staging_extractions
4. Return APPROVED or REJECTED with reasoning

CRITICAL - NEW TOOLS:
- validate_epistemic_structure(epistemic_defaults, epistemic_overrides)
- verify_evidence_lineage(snapshot_id, evidence_text)

If ANY duplicates found, REJECT immediately.
If epistemic structure invalid, REJECT.
If lineage_confidence < 0.5, REJECT.
Otherwise, APPROVE and include verification results.
```

### Tools Available

| Tool | Purpose | Returns |
|------|---------|---------|
| `validate_epistemic_structure(defaults, overrides)` | Check epistemic validity | `{valid: bool, issues: []}` |
| `verify_evidence_lineage(snapshot_id, evidence)` | Verify evidence exists | `{lineage_verified: bool, lineage_confidence: float, ...}` |
| `check_for_duplicates(entity_name, entity_type)` | Check core_entities | Duplicate report |
| `get_pending_extractions(limit)` | Get awaiting extractions | Extraction list |
| `record_validation_decision(...)` | Record decision | Decision confirmation |
| `query_verified_entities(...)` | Query verified data | Entity list |
| `query_staging_history(...)` | Query past extractions | Historical data |
| `query_validation_decisions(...)` | Query past decisions | Decision history |
| `query_raw_snapshots(...)` | Query source snapshots | Snapshot list |
| `check_if_dependency_exists(...)` | Legacy: Check kg_nodes | Duplicate status |
| `verify_schema_compliance(...)` | Check ERV schema | Compliance status |
| `search_similar_dependencies(...)` | Legacy: Search kg_nodes | Similar entities |

### Output Contract

The validator MUST return a message containing ONE of:

```yaml
APPROVED Response:
  Status: "APPROVED"
  Reasoning: string           # Why approved

  Per-Extraction Verification:
    - extraction_id/key: string
      lineage_verified: boolean
      lineage_confidence: float
      epistemic_valid: boolean
      duplicate_check: "passed" | "warning"

REJECTED Response:
  Status: "REJECTED"
  Reasoning: string           # Why rejected

  Issues Found:
    - issue_type: string      # duplicate | epistemic_invalid | lineage_failed
      details: string
      extraction_key: string (optional)
```

### Decision Logic (from system prompt)

```
If ANY duplicates found → REJECT immediately
If epistemic structure invalid → REJECT
If lineage_confidence < 0.5 → REJECT
Otherwise → APPROVE with verification results
```

### Success Criteria

The orchestrator checks for rejection:
```python
if "REJECTED" in validator_message.upper():
    return {"status": "rejected", "stage": "validation", ...}
```

---

## 3. Storage Agent Contract

### Identity
- **Model:** `claude-3-5-haiku-20241022`
- **Temperature:** 0.1
- **Max Tool Calls:** 5

### Input Contract

The storage agent receives both extractor and validator output:

```
Store the following VALIDATED extraction results:

{extractor_output}

VALIDATOR RESULTS:
{validator_output}

Your task (USING NEW REFACTOR PARAMETERS):
1. Parse the extraction data
2. Extract lineage verification results from validator output
3. Extract epistemic defaults + overrides from validator output
4. Store each coupling in staging_extractions with:
   - lineage_verified, lineage_confidence (from validator)
   - epistemic_defaults, epistemic_overrides (will be merged deterministically)
5. Return confirmation with extraction_ids

Use the store_extraction() tool for each coupling.
```

### Tools Available

| Tool | Purpose | Returns |
|------|---------|---------|
| `store_extraction(...)` | Store to staging_extractions | Extraction ID |
| `promote_to_core(...)` | Promote to core_entities | Entity ID |
| `query_verified_entities(...)` | Query verified data | Entity list |
| `query_staging_history(...)` | Query past extractions | Historical data |

### store_extraction() Full Signature

This is the critical function with 50+ parameters:

```python
@tool
def store_extraction(
    # REQUIRED - Core Identity
    candidate_type: str,        # component | port | command | telemetry | event | parameter | data_type | dependency | connection | inheritance
    candidate_key: str,         # Unique identifier for this candidate
    raw_evidence: str,          # Exact quote from source

    # OPTIONAL - Source Tracking
    source_snapshot_id: str = None,  # UUID of raw_snapshot
    ecosystem: str = "external",     # fprime | proveskit | pysquared | cubesat_general | external

    # OPTIONAL - Candidate Details
    description: str = None,
    confidence_score: float = None,
    confidence_reason: str = None,

    # OPTIONAL - Lineage (from validator)
    lineage_verified: bool = None,
    lineage_confidence: float = None,

    # OPTIONAL - Epistemic Anti-Boilerplate
    epistemic_defaults: dict = None,    # Page-level defaults
    epistemic_overrides: dict = None,   # Per-candidate overrides

    # OPTIONAL - 7-Question Knowledge Capture Checklist
    # Q1: Who/what observed this coupling? (Observer)
    observer_id: str = None,
    observer_type: str = None,          # human | sensor | algorithm | llm
    contact_mode: str = None,           # direct | inferred | cited | simulated
    contact_strength: float = None,     # 0.0-1.0
    signal_type: str = None,

    # Q2: Where is the pattern stored? (Storage)
    pattern_storage: str = None,        # url | file | memory | db
    representation_media: str = None,

    # Q3: What else must be true? (Dependencies)
    dependencies: str = None,           # JSON array of dependency keys
    sequence_role: str = None,          # predecessor | successor | parallel

    # Q4: What context was assumed? (Context)
    validity_conditions: str = None,
    assumptions: str = None,
    scope: str = None,

    # Q5: When is this valid? (Temporality)
    observed_at: str = None,
    valid_from: str = None,
    valid_to: str = None,
    refresh_trigger: str = None,
    staleness_risk: str = None,

    # Q6: Who authored this? (Authorship)
    author_id: str = None,
    intent: str = None,
    uncertainty_notes: str = None,

    # Q7: Does this require practice? (Reenactment)
    reenactment_required: bool = None,
    practice_interval: str = None,
    skill_transferability: str = None,
) -> str:
```

### Output Contract

The storage agent MUST return a message containing:

```yaml
Success Response:
  Status: "STORED" or "SUCCESS"
  extraction_ids: array       # UUIDs of stored extractions

  Per-Extraction Confirmation:
    - candidate_key: string
      extraction_id: string (UUID)
      lineage_verified: boolean
      epistemic_merged: boolean   # Defaults + overrides merged

Error Response:
  Status: "ERROR" or "FAILED"
  error_message: string
  failed_extractions: array (optional)
```

---

## 4. Data Flow Between Agents

### Extractor → Validator

```
snapshot_id         → verify_evidence_lineage(snapshot_id, ...)
raw_evidence        → verify_evidence_lineage(..., evidence_text)
epistemic_defaults  → validate_epistemic_structure(defaults, ...)
epistemic_overrides → validate_epistemic_structure(..., overrides)
candidate_key       → check_for_duplicates(entity_name, ...)
candidate_type      → check_for_duplicates(..., entity_type)
```

### Validator → Storage

```
lineage_verified    → store_extraction(..., lineage_verified=...)
lineage_confidence  → store_extraction(..., lineage_confidence=...)
epistemic_valid     → Determines if epistemic_defaults/overrides are passed
APPROVED/REJECTED   → Determines if storage is called at all
```

### Storage → Database

```
staging_extractions Table:
  - extraction_id (auto-generated UUID)
  - candidate_type, candidate_key
  - raw_evidence (as 'evidence' column)
  - source_snapshot_id
  - ecosystem
  - confidence_score, confidence_reason
  - lineage_verified, lineage_confidence (NEW)
  - candidate_payload (JSONB with all other fields)
  - status = 'pending'

knowledge_epistemics Table (if epistemic data provided):
  - extraction_id (FK to staging_extractions)
  - observer_id, observer_type, contact_mode, etc.
  - All 7-question checklist fields merged from defaults + overrides
```

---

## 5. Epistemic Anti-Boilerplate Pattern

### Purpose
Avoid repeating the same epistemic metadata for every extraction from the same page.

### How It Works

1. **Extractor** sets `epistemic_defaults` for the page:
   ```json
   {
     "observer_type": "llm",
     "observer_id": "claude-sonnet-4-5",
     "contact_mode": "inferred",
     "pattern_storage": "url"
   }
   ```

2. **Extractor** sets `epistemic_overrides` for specific candidates:
   ```json
   {
     "contact_strength": 0.9,
     "uncertainty_notes": "Explicit in documentation"
   }
   ```

3. **Validator** verifies structure is valid

4. **Storage** merges deterministically:
   ```python
   merged = {**epistemic_defaults}
   merged.update(epistemic_overrides or {})
   ```

### Valid Epistemic Keys

```python
valid_keys = {
    # Q1: Observer
    'observer_id', 'observer_type', 'contact_mode', 'contact_strength', 'signal_type',

    # Q2: Storage
    'pattern_storage', 'representation_media',

    # Q3: Dependencies
    'dependencies', 'sequence_role',

    # Q4: Context
    'validity_conditions', 'assumptions', 'scope',

    # Q5: Temporality
    'observed_at', 'valid_from', 'valid_to', 'refresh_trigger', 'staleness_risk',

    # Q6: Authorship
    'author_id', 'intent', 'uncertainty_notes',

    # Q7: Reenactment
    'reenactment_required', 'practice_interval', 'skill_transferability'
}
```

---

## 6. Lineage Verification Contract

### How Lineage Works

1. **Extractor** fetches content → stored in `raw_snapshots` → returns `snapshot_id`

2. **Validator** calls `verify_evidence_lineage(snapshot_id, evidence_text)`:
   - Fetches snapshot content from database
   - Strips HTML tags (same as extractor)
   - Checks if evidence exists in content
   - Returns verification result

3. **Storage** receives verification results:
   - `lineage_verified: bool`
   - `lineage_confidence: float`

4. **Storage** computes deterministic metadata:
   - SHA256 checksum of evidence
   - Byte offset in snapshot (if exact match)
   - Stores in `candidate_payload`

### Confidence Tiers

| Tier | Confidence | Meaning |
|------|------------|---------|
| Exact | 1.0 | UTF-8 byte-exact match found |
| Normalized | 0.75 | Match after whitespace normalization |
| Partial | 0.5 | Some checks passed |
| Failed | 0.0 | Evidence not found or errors |

---

## 7. Error Handling Contract

### Extractor Errors
- No URL found → Return error message
- Fetch failed → Return error with HTTP status
- No couplings found → Return message (orchestrator treats as failure)

### Validator Errors
- Snapshot not found → Return `lineage_verified: false`
- Invalid epistemic structure → Return validation errors
- Database error → Return error message

### Storage Errors
- Missing required fields → Return error (candidate_type, candidate_key, raw_evidence)
- Database constraint violation → Return error with details
- Connection error → Return error message

---

## 8. Database Tables Touched

| Agent | Tables Written | Tables Read |
|-------|---------------|-------------|
| Extractor | `raw_snapshots`, `pipeline_runs` | `raw_snapshots` (for dedup) |
| Validator | `validation_decisions`, `staging_extractions` (status update) | `raw_snapshots`, `core_entities`, `staging_extractions` |
| Storage | `staging_extractions`, `knowledge_epistemics` | `staging_extractions` (for dedup) |

---

## 9. Known Issues with Current Contracts

1. **Implicit Contracts**: Contracts are embedded in prompts, not enforced programmatically
2. **No Schema Validation**: JSON payloads not validated against schemas
3. **Text Parsing**: Orchestrator parses agent output as text, fragile
4. **Duplicate DB Connections**: Each tool creates its own connection
5. **No Retry Logic**: Failures are final, no automatic retry
6. **No Timeouts**: Long-running tools can block indefinitely

---

## 10. Recommended Contract Improvements (Option A)

1. **Add JSON Schema validation** for:
   - Extractor output
   - Validator output
   - store_extraction parameters

2. **Centralize database pool** to reduce connection overhead

3. **Add structured output parsing** instead of text search

4. **Add integration tests** to verify contracts are honored

---

*This document is the source of truth for agent communication contracts.*
