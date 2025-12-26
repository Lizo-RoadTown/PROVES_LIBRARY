# ID-Based Lineage Tracking System

**Purpose:** Ensure every extraction can be traced back to raw source data with cryptographic-level confidence in data integrity.

**Principle:** Trust but verify - every agent assigns IDs, every subsequent agent verifies the chain.

---

## ID Chain Architecture

### Complete Lineage Flow

```
┌──────────────────────────────────────────────────────────────┐
│ 1. RAW FETCH                                                 │
│    ┌─────────────────────────────────────────────────────┐   │
│    │ Extractor fetches documentation                     │   │
│    │ → Generates: raw_snapshot_id = uuid4()              │   │
│    │ → Stores to: raw_snapshots table                    │   │
│    │   - id: raw_snapshot_id                             │   │
│    │   - source_url: "https://..."                       │   │
│    │   - payload: {raw_html: "...", text: "..."}         │   │
│    │   - captured_at: timestamp                          │   │
│    │   - checksum: sha256(payload)  ← Integrity check    │   │
│    └─────────────────────────────────────────────────────┘   │
│                                                              │
│    Output: raw_snapshot_id = "979e18be-bb9e-40fa..."       │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. EXTRACTION                                                │
│    ┌─────────────────────────────────────────────────────┐   │
│    │ Extractor analyzes snapshot                         │   │
│    │ → Input: raw_snapshot_id                            │   │
│    │ → Reads: raw_snapshots WHERE id = raw_snapshot_id   │   │
│    │ → Extracts: FRAMES entities                         │   │
│    │                                                      │   │
│    │ For each entity:                                    │   │
│    │   - Generates: extraction_id = uuid4()              │   │
│    │   - Links: source_snapshot_id = raw_snapshot_id     │   │
│    │   - Captures: evidence_quote from payload           │   │
│    │   - Stores: byte_offset (where quote was found)     │   │
│    │   - Generates: evidence_checksum = sha256(quote)    │   │
│    └─────────────────────────────────────────────────────┘   │
│                                                              │
│    Output: [extraction_id_1, extraction_id_2, ...]         │
│            All linked to raw_snapshot_id                    │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. VALIDATION (ID VERIFICATION)                              │
│    ┌─────────────────────────────────────────────────────┐   │
│    │ Validator verifies lineage integrity                │   │
│    │                                                      │   │
│    │ For each extraction_id:                             │   │
│    │   ✓ Check: extraction exists in staging_extractions │   │
│    │   ✓ Check: source_snapshot_id exists in raw_snapshots│  │
│    │   ✓ Verify: evidence quote exists in snapshot payload│  │
│    │   ✓ Verify: evidence_checksum matches                │   │
│    │   ✓ Check: no orphaned IDs                          │   │
│    │                                                      │   │
│    │   If ALL checks pass:                               │   │
│    │     lineage_confidence = 1.0                        │   │
│    │   If ANY fail:                                      │   │
│    │     lineage_confidence = 0.0                        │   │
│    │     status = "lineage_broken"                       │   │
│    │     error = "Specific failure reason"               │   │
│    └─────────────────────────────────────────────────────┘   │
│                                                              │
│    Output: {extraction_id: lineage_confidence, ...}         │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. STORAGE (DOUBLE VERIFICATION)                             │
│    ┌─────────────────────────────────────────────────────┐   │
│    │ Storage agent performs final verification           │   │
│    │                                                      │   │
│    │ Before storing to staging_extractions:              │   │
│    │   ✓ Re-verify: lineage_confidence = 1.0             │   │
│    │   ✓ Re-check: all foreign keys exist                │   │
│    │   ✓ Validate: evidence matches snapshot             │   │
│    │   ✓ Ensure: no duplicate extraction_ids             │   │
│    │                                                      │   │
│    │ Store with full lineage metadata:                   │   │
│    │   - extraction_id (PRIMARY KEY)                     │   │
│    │   - snapshot_id (FOREIGN KEY → raw_snapshots.id)    │   │
│    │   - lineage_verified (BOOLEAN)                      │   │
│    │   - lineage_verified_at (TIMESTAMP)                 │   │
│    │   - lineage_confidence (NUMERIC)                    │   │
│    └─────────────────────────────────────────────────────┘   │
│                                                              │
│    Output: Stored to staging_extractions with lineage ✓    │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│ 5. HUMAN REVIEW (NOTION)                                     │
│    ┌─────────────────────────────────────────────────────┐   │
│    │ Human sees full traceability chain                  │   │
│    │                                                      │   │
│    │ Notion Entry:                                       │   │
│    │   Extraction ID: ext-456                            │   │
│    │   Entity: "MSP430FR Microcontroller"                │   │
│    │                                                      │   │
│    │   📊 TRACEABILITY:                                   │   │
│    │     ✓ Source Snapshot: abc-123 (VERIFIED)           │   │
│    │     ✓ Evidence Checksum: MATCH                      │   │
│    │     ✓ Lineage Confidence: 1.0 (INTACT)              │   │
│    │                                                      │   │
│    │   🔗 LINEAGE CHAIN:                                  │   │
│    │     Raw Fetch → Extraction → Validation → Storage   │   │
│    │     abc-123  →  ext-456   →  val-789    →  STAGED   │   │
│    │                                                      │   │
│    │   📄 EVIDENCE (Clickable to view source):           │   │
│    │     "Ultra-low power supervisor with FRAM"          │   │
│    │     Source: https://docs.proveskit.space/...#L45    │   │
│    │                                                      │   │
│    │   [Approve] [Reject] [Request More Evidence]        │   │
│    └─────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## Database Schema Updates

### 1. raw_snapshots (Enhanced)

```sql
CREATE TABLE raw_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_url TEXT NOT NULL,
    source_type snapshot_type NOT NULL,
    payload JSONB NOT NULL,
    captured_at TIMESTAMPTZ DEFAULT NOW(),

    -- NEW: Integrity verification
    payload_checksum TEXT NOT NULL,  -- sha256(payload::text)
    byte_size INTEGER NOT NULL,      -- SIZE(payload::text)

    -- NEW: Lineage metadata
    fetched_by_thread_id TEXT,       -- LangGraph thread that fetched this
    fetched_by_agent_id TEXT,        -- Agent instance ID

    -- Index for fast lookups
    CONSTRAINT unique_url_timestamp UNIQUE(source_url, captured_at)
);

CREATE INDEX idx_snapshots_checksum ON raw_snapshots(payload_checksum);
CREATE INDEX idx_snapshots_thread ON raw_snapshots(fetched_by_thread_id);
```

### 2. staging_extractions (Enhanced)

```sql
CREATE TABLE staging_extractions (
    extraction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Existing fields
    pipeline_run_id UUID REFERENCES pipeline_runs(id),
    snapshot_id UUID REFERENCES raw_snapshots(id) NOT NULL,
    agent_id TEXT,
    agent_version TEXT,
    candidate_type candidate_type NOT NULL,
    candidate_key TEXT NOT NULL,
    candidate_payload JSONB,
    ecosystem ecosystem_type NOT NULL,
    confidence_score NUMERIC(3,2),
    confidence_reason TEXT,
    evidence JSONB NOT NULL,
    evidence_type evidence_type NOT NULL,
    status candidate_status DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- NEW: Lineage verification
    lineage_verified BOOLEAN DEFAULT FALSE,
    lineage_verified_at TIMESTAMPTZ,
    lineage_confidence NUMERIC(3,2),  -- 0.0 to 1.0
    lineage_verification_details JSONB,  -- What was checked

    -- NEW: Evidence traceability
    evidence_checksum TEXT,           -- sha256(evidence->>'raw_text')
    evidence_byte_offset INTEGER,     -- Where in snapshot payload
    evidence_byte_length INTEGER,     -- Length of evidence quote

    -- NEW: Extraction metadata
    extracted_by_thread_id TEXT,      -- LangGraph thread
    extracted_by_agent_id TEXT,       -- Agent instance

    -- Constraints
    CONSTRAINT valid_lineage_confidence
        CHECK (lineage_confidence IS NULL OR lineage_confidence BETWEEN 0 AND 1),
    CONSTRAINT lineage_verified_requires_confidence
        CHECK (NOT lineage_verified OR lineage_confidence IS NOT NULL)
);

CREATE INDEX idx_extractions_lineage ON staging_extractions(lineage_verified, lineage_confidence);
CREATE INDEX idx_extractions_snapshot ON staging_extractions(snapshot_id);
CREATE INDEX idx_extractions_checksum ON staging_extractions(evidence_checksum);
```

### 3. validation_decisions (Enhanced)

```sql
CREATE TABLE validation_decisions (
    decision_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    extraction_id UUID REFERENCES staging_extractions(extraction_id) NOT NULL,
    decision validation_decision NOT NULL,
    decision_reason TEXT,

    -- NEW: Lineage verification record
    lineage_check_passed BOOLEAN NOT NULL,
    lineage_check_details JSONB,      -- What was verified

    confidence_at_decision NUMERIC(3,2),
    evidence_at_decision JSONB,
    decided_by TEXT,
    decider_type TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT one_decision_per_extraction UNIQUE(extraction_id)
);

CREATE INDEX idx_decisions_lineage_check ON validation_decisions(lineage_check_passed);
```

---

## Agent Implementation

### 1. Extractor Agent (ID Assignment)

```python
@tool
def fetch_and_store_snapshot(source_url: str) -> dict:
    """
    Fetch documentation and store with full lineage metadata.

    Returns:
        {
            "snapshot_id": "uuid",
            "checksum": "sha256",
            "byte_size": int
        }
    """
    import hashlib
    import uuid
    from datetime import datetime, timezone

    # Fetch content
    content = fetch_documentation(source_url)

    # Generate IDs and checksums
    snapshot_id = str(uuid.uuid4())
    payload = {
        "raw_html": content.html,
        "text": content.text,
        "metadata": content.metadata
    }
    payload_str = json.dumps(payload, sort_keys=True)
    checksum = hashlib.sha256(payload_str.encode()).hexdigest()
    byte_size = len(payload_str.encode())

    # Get thread context
    thread_id = get_current_thread_id()  # From LangGraph context
    agent_id = get_current_agent_id()

    # Store to database
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO raw_snapshots (
                id, source_url, source_type, payload,
                payload_checksum, byte_size,
                fetched_by_thread_id, fetched_by_agent_id,
                captured_at
            ) VALUES (
                %s::uuid, %s, %s, %s::jsonb,
                %s, %s,
                %s, %s,
                %s
            )
        """, (
            snapshot_id, source_url, 'webpage', payload_str,
            checksum, byte_size,
            thread_id, agent_id,
            datetime.now(timezone.utc)
        ))
    conn.commit()
    conn.close()

    return {
        "snapshot_id": snapshot_id,
        "checksum": checksum,
        "byte_size": byte_size,
        "source_url": source_url
    }


@tool
def extract_with_lineage(
    snapshot_id: str,
    candidate_type: str,
    candidate_key: str,
    raw_evidence: str,
    **kwargs
) -> dict:
    """
    Extract entity with full lineage tracking.

    Returns:
        {
            "extraction_id": "uuid",
            "evidence_checksum": "sha256",
            "evidence_location": {"offset": int, "length": int}
        }
    """
    import hashlib
    import uuid

    # Generate extraction ID
    extraction_id = str(uuid.uuid4())

    # Verify snapshot exists
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT payload, payload_checksum
            FROM raw_snapshots
            WHERE id = %s::uuid
        """, (snapshot_id,))
        row = cur.fetchone()

        if not row:
            raise ValueError(f"Snapshot {snapshot_id} not found - broken lineage!")

        snapshot_payload, snapshot_checksum = row

    # Find evidence in snapshot
    payload_str = json.dumps(snapshot_payload, sort_keys=True)
    evidence_offset = payload_str.find(raw_evidence)

    if evidence_offset == -1:
        # Evidence not found in snapshot - lineage problem!
        return {
            "extraction_id": extraction_id,
            "lineage_error": "Evidence quote not found in source snapshot",
            "lineage_confidence": 0.0
        }

    # Calculate evidence checksum
    evidence_checksum = hashlib.sha256(raw_evidence.encode()).hexdigest()
    evidence_length = len(raw_evidence.encode())

    # Get thread context
    thread_id = get_current_thread_id()
    agent_id = get_current_agent_id()

    # Store extraction with lineage metadata
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO staging_extractions (
                extraction_id, snapshot_id,
                candidate_type, candidate_key,
                evidence, evidence_checksum,
                evidence_byte_offset, evidence_byte_length,
                extracted_by_thread_id, extracted_by_agent_id,
                lineage_verified, lineage_confidence,
                status
            ) VALUES (
                %s::uuid, %s::uuid,
                %s::candidate_type, %s,
                %s::jsonb, %s,
                %s, %s,
                %s, %s,
                FALSE, NULL,  -- Validator will verify
                'pending'::candidate_status
            )
            RETURNING extraction_id
        """, (
            extraction_id, snapshot_id,
            candidate_type, candidate_key,
            json.dumps({"raw_text": raw_evidence}), evidence_checksum,
            evidence_offset, evidence_length,
            thread_id, agent_id
        ))

    conn.commit()
    conn.close()

    return {
        "extraction_id": extraction_id,
        "evidence_checksum": evidence_checksum,
        "evidence_location": {
            "offset": evidence_offset,
            "length": evidence_length
        },
        "lineage_status": "pending_validation"
    }
```

---

### 2. Validator Agent (Lineage Verification)

```python
@tool
def verify_extraction_lineage(extraction_id: str) -> dict:
    """
    Verify complete lineage chain for an extraction.

    Checks:
    1. Extraction exists
    2. Snapshot exists and is linked
    3. Evidence exists in snapshot payload
    4. Evidence checksum matches
    5. No orphaned IDs

    Returns:
        {
            "lineage_confidence": float (0.0 to 1.0),
            "checks_passed": int,
            "checks_failed": int,
            "failures": [list of what failed],
            "verified": bool
        }
    """
    conn = get_db_connection()
    checks = []
    failures = []

    try:
        with conn.cursor() as cur:
            # Check 1: Extraction exists
            cur.execute("""
                SELECT
                    e.extraction_id,
                    e.snapshot_id,
                    e.evidence,
                    e.evidence_checksum,
                    e.evidence_byte_offset,
                    e.evidence_byte_length
                FROM staging_extractions e
                WHERE e.extraction_id = %s::uuid
            """, (extraction_id,))

            extraction = cur.fetchone()
            if not extraction:
                return {
                    "lineage_confidence": 0.0,
                    "checks_passed": 0,
                    "checks_failed": 1,
                    "failures": ["Extraction not found in database"],
                    "verified": False
                }

            checks.append("✓ Extraction exists")

            ext_id, snapshot_id, evidence, evidence_checksum, byte_offset, byte_length = extraction

            # Check 2: Snapshot exists
            cur.execute("""
                SELECT
                    payload,
                    payload_checksum,
                    source_url
                FROM raw_snapshots
                WHERE id = %s::uuid
            """, (snapshot_id,))

            snapshot = cur.fetchone()
            if not snapshot:
                failures.append("Snapshot not found - broken foreign key")
                return build_lineage_result(checks, failures)

            checks.append("✓ Snapshot exists and is linked")

            snapshot_payload, snapshot_checksum, source_url = snapshot

            # Check 3: Evidence exists in snapshot
            evidence_text = evidence.get('raw_text', '') if isinstance(evidence, dict) else ''
            payload_str = json.dumps(snapshot_payload, sort_keys=True)

            if byte_offset is not None:
                # Use byte offset if available
                payload_bytes = payload_str.encode()
                extracted_evidence = payload_bytes[byte_offset:byte_offset + byte_length].decode()

                if extracted_evidence != evidence_text:
                    failures.append(f"Evidence mismatch at byte offset {byte_offset}")
                else:
                    checks.append("✓ Evidence found at recorded byte offset")
            else:
                # Fallback: search for evidence in payload
                if evidence_text in payload_str:
                    checks.append("✓ Evidence found in snapshot payload")
                else:
                    failures.append("Evidence quote not found in snapshot payload")

            # Check 4: Evidence checksum matches
            import hashlib
            calculated_checksum = hashlib.sha256(evidence_text.encode()).hexdigest()

            if evidence_checksum == calculated_checksum:
                checks.append("✓ Evidence checksum matches")
            else:
                failures.append(f"Evidence checksum mismatch: {evidence_checksum[:8]} != {calculated_checksum[:8]}")

            # Check 5: Snapshot checksum valid
            calculated_snapshot_checksum = hashlib.sha256(
                json.dumps(snapshot_payload, sort_keys=True).encode()
            ).hexdigest()

            if snapshot_checksum == calculated_snapshot_checksum:
                checks.append("✓ Snapshot checksum valid (no tampering)")
            else:
                failures.append("Snapshot checksum invalid - possible data corruption")

        conn.close()

        # Calculate lineage confidence
        total_checks = len(checks) + len(failures)
        lineage_confidence = len(checks) / total_checks if total_checks > 0 else 0.0

        # Update extraction with verification results
        update_lineage_verification(
            extraction_id=extraction_id,
            verified=(len(failures) == 0),
            confidence=lineage_confidence,
            details={
                "checks_passed": checks,
                "checks_failed": failures,
                "verified_at": datetime.now(timezone.utc).isoformat()
            }
        )

        return {
            "lineage_confidence": lineage_confidence,
            "checks_passed": len(checks),
            "checks_failed": len(failures),
            "failures": failures,
            "verified": (len(failures) == 0),
            "details": {
                "checks": checks,
                "snapshot_id": str(snapshot_id),
                "source_url": source_url
            }
        }

    except Exception as e:
        return {
            "lineage_confidence": 0.0,
            "checks_passed": 0,
            "checks_failed": 1,
            "failures": [f"Verification error: {str(e)}"],
            "verified": False
        }


def update_lineage_verification(extraction_id: str, verified: bool, confidence: float, details: dict):
    """Update extraction with lineage verification results."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE staging_extractions
            SET
                lineage_verified = %s,
                lineage_verified_at = NOW(),
                lineage_confidence = %s,
                lineage_verification_details = %s::jsonb
            WHERE extraction_id = %s::uuid
        """, (verified, confidence, json.dumps(details), extraction_id))
    conn.commit()
    conn.close()
```

---

### 3. Storage Agent (Double Verification)

```python
@tool
def store_extraction_with_verification(extraction_id: str) -> str:
    """
    Store extraction to staging ONLY if lineage is verified.

    Performs double-check before allowing human review.
    """
    # Re-verify lineage (trust but verify)
    lineage_result = verify_extraction_lineage(extraction_id)

    if not lineage_result['verified']:
        # Lineage broken - reject
        return f"""
        [REJECTED] Extraction {extraction_id} failed lineage verification.

        Failures:
        {chr(10).join('  - ' + f for f in lineage_result['failures'])}

        This extraction will NOT be presented to humans for review.
        Fix data integrity issues first.
        """

    if lineage_result['lineage_confidence'] < 1.0:
        # Partial verification - warn
        return f"""
        [WARNING] Extraction {extraction_id} has partial lineage confidence: {lineage_result['lineage_confidence']}

        Passed: {lineage_result['checks_passed']} checks
        Failed: {lineage_result['checks_failed']} checks

        Flagging for manual review with caution.
        """

    # Lineage fully verified ✓
    return f"""
    [VERIFIED] Extraction {extraction_id} lineage confidence: {lineage_result['lineage_confidence']}

    ✓ All integrity checks passed
    ✓ Evidence traced to source
    ✓ No data corruption detected

    Ready for human review.
    """
```

---

## Notion Integration (Traceability Display)

### Extraction Review Database Properties

Add these fields to show lineage:

```json
{
  "Extraction ID": "ext-456",
  "Entity Key": "MSP430FR Microcontroller",

  // NEW: Traceability fields
  "Source Snapshot ID": "abc-123",
  "Lineage Verified": true (checkbox),
  "Lineage Confidence": 1.0 (number),
  "Evidence Checksum": "a3f2b1..." (text),
  "Verification Details": {
    "checks_passed": [
      "✓ Extraction exists",
      "✓ Snapshot exists and is linked",
      "✓ Evidence found at recorded byte offset",
      "✓ Evidence checksum matches",
      "✓ Snapshot checksum valid"
    ],
    "source_url": "https://docs.proveskit.space/..."
  },

  // Visual indicator
  "Traceability Status": "✅ VERIFIED" (formula based on Lineage Confidence)
}
```

### Notion Page Template

```markdown
# Extraction: MSP430FR Microcontroller

## 🔐 LINEAGE VERIFICATION

**Status:** ✅ FULLY VERIFIED
**Confidence:** 1.0 (100%)
**Verified At:** 2025-12-24 14:35:22 UTC

### Traceability Chain
```
Raw Fetch (abc-123)
    ↓
Extraction (ext-456)
    ↓
Validation (PASSED)
    ↓
Ready for Human Review
```

### Verification Details
✓ Extraction exists in database
✓ Snapshot exists and is linked
✓ Evidence found at byte offset 12,456
✓ Evidence checksum matches
✓ Snapshot checksum valid (no tampering)

### Source Information
**URL:** [https://docs.proveskit.space/...](https://docs.proveskit.space/...)
**Snapshot ID:** abc-123
**Fetched:** 2025-12-24 10:15:33 UTC
**Snapshot Size:** 67,234 bytes

---

## 📄 EVIDENCE

> "Ultra-low power supervisor with FRAM"

**Checksum:** a3f2b1...
**Location:** Byte 12,456-12,492 in snapshot
**Length:** 36 bytes

[View Full Snapshot →](link to Neon query or file viewer)

---

## ✏️ HUMAN REVIEW

**Confidence:** 0.90
**Type:** Component
**Ecosystem:** PROVES Kit

[✅ Approve] [❌ Reject] [✏️ Correct]
```

---

## Error Scenarios & Handling

### Scenario 1: Evidence Not Found in Snapshot

```python
# Validator detects:
lineage_result = {
    "lineage_confidence": 0.2,  # Only 1 of 5 checks passed
    "failures": ["Evidence quote not found in snapshot payload"],
    "verified": False
}

# Storage agent rejects:
"[REJECTED] Extraction cannot be traced to source.
 Evidence may have been fabricated or snapshot corrupted."

# Human sees in Notion:
"⚠️ LINEAGE BROKEN - Evidence cannot be verified against source"
```

### Scenario 2: Checksum Mismatch

```python
# Validator detects:
"Evidence checksum mismatch: a3f2b1 != b4e3c2"

# Possible causes:
# - Evidence was modified after extraction
# - Database corruption
# - Agent hallucination

# Action:
# - Flag for immediate review
# - Do not allow approval
# - Trigger re-extraction
```

### Scenario 3: Orphaned Extraction

```python
# Validator checks:
cur.execute("SELECT * FROM raw_snapshots WHERE id = %s", (snapshot_id,))
# Returns: None

# Result:
"Snapshot not found - extraction is orphaned"

# Action:
# - Delete orphaned extraction
# - Log error to Notion Error Log
# - Alert human to data integrity issue
```

---

## Cost Impact

### Additional Costs for Lineage Verification:

**Per Extraction:**
- Checksum calculation: ~0.001s CPU (negligible)
- Database queries (5 checks): ~0.01s
- No LLM calls needed for verification ✅

**Total Cost Impact:** ~$0 (pure database operations)

**Value:** Cryptographic-level confidence in data integrity

---

## Implementation Checklist

- [ ] Update raw_snapshots schema with checksums
- [ ] Update staging_extractions schema with lineage fields
- [ ] Implement fetch_and_store_snapshot with checksums
- [ ] Implement extract_with_lineage with byte offsets
- [ ] Implement verify_extraction_lineage in validator
- [ ] Add double-verification in storage agent
- [ ] Update Notion database properties
- [ ] Create Notion page template with traceability
- [ ] Add lineage confidence to daily reports
- [ ] Test with actual extraction (PROVES Prime)
- [ ] Document lineage verification in audit trail

---

## Benefits

1. **Trust:** Every extraction traceable to raw source
2. **Integrity:** Checksums detect data corruption
3. **Auditability:** Full chain visible to humans
4. **Confidence:** Mathematical certainty (not LLM confidence)
5. **Debugging:** Easy to trace errors back to source
6. **Compliance:** Meets research data provenance standards

**Bottom line:** Humans can approve extractions with 100% confidence they came from the documented source.
