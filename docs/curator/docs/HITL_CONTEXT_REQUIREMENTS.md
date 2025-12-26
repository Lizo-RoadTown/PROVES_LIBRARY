# HITL Context Requirements - What Humans Need to See

## Problem Statement

Humans cannot effectively verify extractions without seeing:
1. **Source** - Where did this come from?
2. **Evidence** - What exact quote supports this?
3. **Reasoning** - Why does the agent think this is correct?
4. **Confidence Logic** - What did they compare against?
5. **Lineage** - What verified data influenced this?

**Current State:** Human sees only a task string
**Required State:** Human sees ALL metadata to reduce ambiguity

---

## Required Context for EVERY Extraction

### 1. Source Information
```
Source URL: https://docs.proveskit.space/en/latest/.../proves_prime/
Source Type: webpage | github_file | local_doc
Fetched: 2025-12-23 10:45:32 UTC
Snapshot ID: abc123-def456-...
```

### 2. Extraction Details
```
Entity Type: component | interface | flow | mechanism
Entity Key: RTC_RV3032
Ecosystem: hardware | fprime | proveskit | pysquared
Candidate ID: extraction_12345
```

### 3. Evidence (Critical!)
```
Evidence Quote:
────────────────────────────────────────
"The RV3032 Real-Time Clock is a low-power
device that communicates over I2C at address
0x51. It provides timekeeping functionality
for the satellite..."
────────────────────────────────────────
Evidence Type: definition_spec | example | narrative | table_diagram
```

### 4. Properties/Payload
```
Properties:
  - i2c_address: "0x51"
  - interface_type: "I2C"
  - power_consumption: "low"
  - function: "timekeeping"
```

### 5. Confidence Score & Reasoning
```
Confidence: 0.85 / 1.0

Reasoning:
  ✓ Compared against 3 verified I2C components:
    - entity_123: RTC_DS3231 (fprime, confidence=0.90, VERIFIED)
    - entity_456: IMU_BNO085 (hardware, confidence=0.88, VERIFIED)
    - entity_789: TEMP_TMP117 (hardware, confidence=0.92, VERIFIED)

  ✓ Pattern match:
    - All verified I2C components have i2c_address property
    - Evidence includes explicit address declaration
    - Similar evidence quality (definition_spec type)

  ✓ Source credibility:
    - Official PROVES Kit documentation
    - Matches mkdocs.yml structure

  ⚠ Uncertainty factors:
    - No driver implementation found yet
    - Integration with F' Prime not confirmed
```

### 6. Duplicate Check Results
```
Duplicate Check:
  - Exact matches: 0
  - Similar entities: 2
    • RTC_DS3231 (entity_abc, 0.73 similarity, fprime ecosystem)
    • RTC_PCF8523 (entity_def, 0.68 similarity, hardware ecosystem)
  - Recommendation: CREATE NEW (ecosystems different)
```

### 7. Validator Assessment (if available)
```
Validator Notes:
  - Schema compliance: PASS
  - Evidence quality: HIGH
  - Confidence appropriate: YES
  - Recommendation: ACCEPT
```

### 8. Lineage/Comparison Trail
```
Agent Consulted:
  ✓ Queried verified entities: 15 results (I2C components)
  ✓ Checked staging history: 8 accepted, 2 rejected
  ✓ Reviewed validation decisions: No rejections for similar pattern
  ✓ Compared evidence format: Matches 85% of verified examples
```

---

## Implementation Requirements

### Phase 1: Capture in Storage
`store_extraction()` must capture:
```python
store_extraction(
    # Existing
    candidate_type, candidate_key, raw_evidence, source_snapshot_id,
    ecosystem, properties, confidence_score, confidence_reason,

    # NEW - Agent reasoning
    reasoning_trail: dict = {
        "verified_entities_consulted": ["entity_123", "entity_456"],
        "staging_examples_reviewed": 8,
        "validation_patterns_checked": ["i2c_address_required"],
        "comparison_logic": "Matched structure of 3 verified I2C components",
        "uncertainty_factors": ["No driver implementation found"],
    },

    # NEW - Duplicate check results
    duplicate_check: dict = {
        "exact_matches": [],
        "similar_entities": [{"id": "entity_abc", "similarity": 0.73}],
        "recommendation": "create_new" | "merge_with" | "needs_review"
    },

    # NEW - Source metadata
    source_metadata: dict = {
        "source_url": "https://...",
        "source_type": "webpage",
        "fetch_timestamp": "2025-12-23T10:45:32Z"
    }
)
```

### Phase 2: Pass to Interrupt
Update `request_human_approval()` interrupt data:
```python
interrupt({
    "type": "dependency_approval",

    # Source
    "source_url": extraction["source_url"],
    "source_type": extraction["source_type"],
    "snapshot_id": extraction["snapshot_id"],

    # Extraction
    "entity_type": extraction["candidate_type"],
    "entity_key": extraction["candidate_key"],
    "ecosystem": extraction["ecosystem"],
    "properties": extraction["properties"],

    # Evidence
    "evidence_quote": extraction["raw_evidence"],
    "evidence_type": extraction["evidence_type"],

    # Confidence
    "confidence_score": extraction["confidence_score"],
    "confidence_reason": extraction["confidence_reason"],
    "reasoning_trail": extraction.get("reasoning_trail", {}),

    # Validation context
    "duplicate_check": extraction.get("duplicate_check", {}),
    "validator_assessment": extraction.get("validator_notes", None),
})
```

### Phase 3: Display to Human
Update run scripts to show structured data:
```python
print("=" * 80)
print("EXTRACTION FOR VERIFICATION")
print("=" * 80)
print()
print(f"Source: {interrupt_data['source_url']}")
print(f"Type: {interrupt_data['entity_type']} | Key: {interrupt_data['entity_key']}")
print(f"Ecosystem: {interrupt_data['ecosystem']}")
print()
print("Evidence (from source):")
print("─" * 40)
print(interrupt_data['evidence_quote'][:500])
print("─" * 40)
print()
print(f"Confidence: {interrupt_data['confidence_score']} / 1.0")
print(f"Reasoning: {interrupt_data['confidence_reason']}")
print()
if 'reasoning_trail' in interrupt_data:
    trail = interrupt_data['reasoning_trail']
    print("Agent Consulted:")
    print(f"  • Verified entities: {len(trail.get('verified_entities_consulted', []))}")
    print(f"  • Staging examples: {trail.get('staging_examples_reviewed', 0)}")
    print(f"  • Comparison: {trail.get('comparison_logic', 'None')}")
print()
if 'duplicate_check' in interrupt_data:
    dup = interrupt_data['duplicate_check']
    print(f"Duplicate Check: {dup.get('recommendation', 'not_checked')}")
    if dup.get('similar_entities'):
        print(f"  Similar: {len(dup['similar_entities'])} entities found")
print()
print("=" * 80)
```

---

## Success Criteria

Human can answer these WITHOUT leaving the CLI:

✅ Where did this come from? (source URL visible)
✅ What's the exact quote? (evidence quote visible)
✅ Why is agent confident? (confidence reasoning visible)
✅ What did they compare against? (reasoning trail visible)
✅ Are there duplicates? (duplicate check results visible)
✅ What verified data influenced this? (lineage visible)

**If human needs to look up external context → WE FAILED**
