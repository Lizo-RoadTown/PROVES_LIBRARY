# Production Release - 2025-12-27

## Major Changes

### Deterministic Lineage Computation
- **Moved lineage creation from agent behavior to pure Python code**
- Prevents "agent tore it apart" problem
- 3-step matching algorithm with explicit UTF-8 encoding:
  - Exact match: confidence 1.0
  - Exact match (ambiguous): confidence 0.7
  - Normalized match: confidence 0.85
  - Not found: confidence 0.0
- Stores complete verification details in lineage_verification_details JSONB

### Performance Improvements
- **Cost reduced from 40-60 cents → 10-12 cents per extraction**
- Extractor recursion limit: MAX 1 tool call (fetch_webpage only)
- Removed redundant tool calls and agent loops
- Validator and Storage using Haiku model (90% cheaper)

### Architecture Changes
- **Orchestration pattern**: Explicit Python control flow instead of curator agent
- Extract → Validate → Store pipeline with forced sequential execution
- Storage automatically computes lineage (no agent involvement)

## Files Updated

### Core Pipeline
- `process_extractions.py` - Main extraction orchestration
- `src/curator/agent_v2.py` - Orchestration graph
- `src/curator/subagent_specs.py` - Agent specifications with strict enum validation

### Subagents
- `src/curator/subagents/storage.py` - Deterministic lineage computation (lines 171-374)
- `src/curator/subagents/extractor.py` - Simplified to 1 tool call
- `src/curator/subagents/validator.py` - Validation logic

## Database Schema
- All lineage fields populated: evidence_checksum, evidence_byte_offset, evidence_byte_length
- lineage_verified, lineage_confidence, lineage_verified_at
- lineage_verification_details (JSONB with method, hashes, match locations)

## Testing
- ✅ End-to-end pipeline working
- ✅ Lineage confidence: 1.0 (perfect match)
- ✅ Cost: 10-12 cents per extraction
- ✅ Recursion limit respected (1 tool call)
