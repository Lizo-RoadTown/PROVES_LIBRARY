# Deployment Notes

## Prerequisites

- Python 3.14
- NEON_DATABASE_URL environment variable set
- Database schema with lineage fields (see migrations/001_add_lineage_and_relationships.sql)

## Running Production Pipeline

### Process URLs from Queue

```bash
cd curator-agent/production
python process_extractions.py --limit 10
```

### Continuous Processing

```bash
python process_extractions.py --continuous
```

## Key Configuration

- **Recursion limit**: 20 (generous for subagent overhead)
- **Extractor model**: claude-sonnet-4-5-20250929
- **Validator model**: claude-3-5-haiku-20241022 (cost optimization)
- **Storage model**: claude-3-5-haiku-20241022 (cost optimization)

## Monitoring

- Check LangSmith for traces: <https://smith.langchain.com/>
- Database tables:
  - `staging_extractions` - extracted entities with lineage data
  - `raw_snapshots` - source snapshots
  - `urls_to_process` - processing queue

## Cost Expectations

- **Target**: 10-12 cents per extraction
- **Previous**: 40-60 cents (before optimization)

## Troubleshooting

### "Invalid candidate_type" errors

- Extractor must use STRICT enum values only
- ALL FRAMES couplings → 'dependency'
- See subagent_specs.py lines 66-74 for valid types

### Recursion limit errors

- Should not occur with current configuration (extractor uses 1 tool call)
- If it happens, check for agent loops in LangSmith traces

### Lineage verification failures

- Check lineage_confidence in staging_extractions
- confidence < 0.5 = failed verification
- Check lineage_verification_details JSONB for diagnostics
