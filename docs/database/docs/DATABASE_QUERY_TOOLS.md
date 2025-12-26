# Database Query Tools for Agent Confidence Calibration

## Problem
Agents currently work BLIND - they can't see verified data to:
- Learn extraction patterns
- Calibrate confidence scores
- Compare against approved examples
- Understand what humans accept vs reject

## Solution: General-Purpose Query Tools

### 1. query_verified_entities
```python
@tool
def query_verified_entities(
    entity_type: str = None,
    ecosystem: str = None,
    name_pattern: str = None,
    has_property: str = None,
    limit: int = 20
) -> str:
    """
    Query core_entities (verified truth) - LET THE AGENT DECIDE WHAT HELPS.

    Examples:
    - "Show me verified I2C components"
      query_verified_entities(entity_type='component', has_property='i2c')

    - "What hardware sensors have been verified?"
      query_verified_entities(entity_type='component', ecosystem='hardware')

    - "Show me all RTC-related entities"
      query_verified_entities(name_pattern='%RTC%')

    Returns: Full entity data including properties, sources, confidence scores
    """
```

### 2. query_staging_history
```python
@tool
def query_staging_history(
    status: str = None,  # 'accepted', 'rejected', 'pending'
    entity_type: str = None,
    ecosystem: str = None,
    min_confidence: float = None,
    limit: int = 20
) -> str:
    """
    Query staging_extractions history - SEE WHAT WAS ACCEPTED/REJECTED.

    Examples:
    - "What I2C extractions did humans accept?"
      query_staging_history(status='accepted', name_pattern='%I2C%')

    - "What low-confidence items were still approved?"
      query_staging_history(status='accepted', min_confidence=0.0, max_confidence=0.6)

    - "Why were similar extractions rejected?"
      query_staging_history(status='rejected', entity_type='component')

    Returns: Confidence scores, confidence reasons, human decisions, evidence
    """
```

### 3. query_validation_decisions
```python
@tool
def query_validation_decisions(
    decision_type: str = None,  # 'accept', 'reject', 'needs_more_evidence'
    entity_type: str = None,
    reasoning_contains: str = None,
    limit: int = 20
) -> str:
    """
    Query validation_decisions - SEE HOW VALIDATOR REASONED.

    Examples:
    - "What evidence issues caused rejections?"
      query_validation_decisions(decision_type='reject', reasoning_contains='evidence')

    - "When did we defer for more evidence?"
      query_validation_decisions(decision_type='needs_more_evidence')

    Returns: Validator reasoning, confidence overrides, merge suggestions
    """
```

### 4. query_raw_snapshots
```python
@tool
def query_raw_snapshots(
    source_url_pattern: str = None,
    source_type: str = None,  # 'webpage', 'github_file', 'local_doc'
    created_after: str = None,
    limit: int = 10
) -> str:
    """
    Query raw_snapshots - SEE WHAT SOURCES WERE PROCESSED.

    Examples:
    - "What PROVES Kit pages have we processed?"
      query_raw_snapshots(source_url_pattern='%proveskit.space%')

    - "Show me F' Prime component sources"
      query_raw_snapshots(source_url_pattern='%nasa/fprime%', source_type='github_file')

    Returns: Source URLs, fetch timestamps, content previews
    """
```

## Why General-Purpose?

**DON'T prescribe** - Let agents decide what helps them:

❌ Bad: "Use this tool to check for I2C duplicates"
✅ Good: "Query anything in core_entities that helps you validate"

Agent might discover:
- "I should check if similar I2C addresses exist"
- "I should see what confidence scores were accepted for hardware components"
- "I should compare against F' Prime examples before extracting PROVES Kit"

## Agent Self-Improvement

With these tools, agents can:

1. **Extractor before staging:**
   - "Let me check verified I2C components to see the pattern"
   - "What confidence score do similar extractions use?"
   - "How granular should I be? Let me see examples"

2. **Validator before deciding:**
   - "Are there existing components with this I2C address?"
   - "What evidence quality led to past rejections?"
   - "Should I merge this or create new entity?"

3. **Both can explain reasoning:**
   - "My confidence is 0.85 because I compared against 3 verified I2C components (IDs: xxx, yyy, zzz) with similar structure"
   - "I recommend merge because entity_id abc123 has same canonical_key"

## Implementation Priority

1. **query_verified_entities** - Critical for confidence calibration
2. **query_staging_history** - Learn from human decisions
3. **query_validation_decisions** - See validator patterns
4. **query_raw_snapshots** - Avoid re-processing sources
