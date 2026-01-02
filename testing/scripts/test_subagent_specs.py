"""
Test Subagent Specifications - Uses BACKUP files directly

This is a test-only version that imports from backup validator and storage
to avoid import conflicts during testing.
"""
import os
import sys
from pathlib import Path

# Add paths
production_root = Path(__file__).parent.parent.parent / 'production'
sys.path.insert(0, str(production_root))

# Import from backup files directly (bypass production imports)
from curator.subagents.extractor import (
    fetch_webpage,
    extract_architecture_using_claude,
    query_verified_entities,
    query_staging_history,
    get_ontology,
)

# Import from BACKUP validator
from curator.subagents.validator_BACKUP_pre_lineage_split import (
    get_pending_extractions,
    check_for_duplicates,
    validate_epistemic_structure,
    verify_evidence_lineage,
    query_verified_entities as validator_query_verified,
    query_staging_history as validator_query_staging,
    query_validation_decisions,
    query_raw_snapshots,
    check_if_dependency_exists,
    verify_schema_compliance,
    search_similar_dependencies,
)

# Import from BACKUP storage
from curator.subagents.storage_BACKUP_pre_lineage_split import (
    store_extraction,
    get_staging_statistics,
)


def get_extractor_spec() -> dict:
    """Get the extractor subagent specification (using production extractor)."""

    # Load the full spec from backup file
    import importlib.util
    spec_path = production_root / 'curator' / 'subagent_specs_BACKUP_pre_lineage_split.py'
    spec = importlib.util.spec_from_file_location("backup_specs", spec_path)
    backup_specs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backup_specs)

    return backup_specs.get_extractor_spec()


def get_validator_spec() -> dict:
    """Get the validator subagent specification (using BACKUP validator)."""

    return {
        "name": "validator",
        "description": "Validates extractions for duplicates, pattern breaks, and missing evidence. Uses backup refactors.",
        "system_prompt": """You are the Validator Agent for the PROVES Library (TESTING WITH BACKUPS).

## Your Mission

Validate extraction data BEFORE storage to prevent duplicates and ensure lineage integrity.

## CRITICAL VALIDATION CHECKS (MUST DO ALL)

### 1. Lineage Verification (MANDATORY)
For each extraction, use verify_evidence_lineage(snapshot_id, evidence_text):
- [REQ] Call verify_evidence_lineage() with snapshot_id and evidence_text
- [REQ] Returns JSON with lineage_verified, lineage_confidence, checks_passed, checks_failed
- [REQ] Pass results to storage agent for deterministic metadata computation

**Lineage confidence scoring:**
- 1.0 = Perfect (all checks pass)
- 0.75-0.99 = Good (minor issues, can proceed)
- 0.5-0.74 = Questionable (flag for human review)
- <0.5 = REJECT (broken lineage, do NOT approve)

### 2. Epistemic Structure Validation (NEW - MANDATORY)
For each extraction, use validate_epistemic_structure(epistemic_defaults, epistemic_overrides):
- [REQ] Call validate_epistemic_structure() with defaults and overrides
- [REQ] Returns JSON with valid (bool) and issues (list)
- [REQ] REJECT if validation fails

### 3. Duplicate Detection (PREVENTS LOOPS)
- Use check_for_duplicates() to search core_entities
- If duplicate found: REJECT with clear reason

## Workflow (MAX 5 TOOL CALLS)

1. **Epistemic Validation** (1 tool call):
   - Call validate_epistemic_structure()
   - REJECT if invalid

2. **Lineage Verification** (1 tool call):
   - Call verify_evidence_lineage()
   - REJECT if lineage_confidence < 0.5 or lineage_verified = FALSE

3. **Duplicate Check** (1 tool call):
   - Use check_for_duplicates()
   - REJECT if duplicate found

4. **Decision** (return immediately):
   - APPROVE if: epistemic valid AND lineage verified AND no duplicates
   - Pass verification results to storage

After 5 tool calls, you MUST return a decision. No exceptions.""",
        "tools": [
            get_pending_extractions,
            check_for_duplicates,
            validate_epistemic_structure,  # NEW: Validate epistemic defaults + overrides
            verify_evidence_lineage,  # NEW: Lineage verification before storage
            validator_query_verified,
            validator_query_staging,
            query_validation_decisions,
            query_raw_snapshots,
            check_if_dependency_exists,
            verify_schema_compliance,
            search_similar_dependencies,
        ],
        "model": "claude-3-5-haiku-20241022",
    }


def get_storage_spec() -> dict:
    """Get the storage subagent specification (using BACKUP storage)."""

    return {
        "name": "storage",
        "description": "Stores extracted entities in staging_extractions table. Uses backup refactors.",
        "system_prompt": """You are the Storage Agent for the PROVES Library (TESTING WITH BACKUPS).

## Your Mission

Store extracted entities in staging_extractions for human review.

## Your Tools

- store_extraction() - Stage extractions with:
  * Lineage verification results from validator (lineage_verified, lineage_confidence)
  * Epistemic defaults + overrides (will be merged deterministically)
  * All extraction metadata
- get_staging_statistics() - Query database stats

## Workflow (MAX 5 TOOL CALLS)

1. Receive extraction data from validator (with verification results)
2. Store using store_extraction():
   - Pass lineage_verified, lineage_confidence from validator
   - Pass epistemic_defaults, epistemic_overrides (storage will merge)
   - Storage computes deterministic metadata (checksums, byte offsets)
3. Verify storage with get_staging_statistics()

**CRITICAL:** You receive verification results from validator. Storage computes ONLY:
- Deterministic checksums (SHA256)
- Byte offsets (UTF-8)
- Byte lengths
- Epistemic merge (defaults + overrides)

After 5 tool calls, you MUST return confirmation. No exceptions.""",
        "tools": [
            store_extraction,
            get_staging_statistics,
        ],
        "model": "claude-3-5-haiku-20241022",
    }
