# UNDERSTANDING HITL: Action-Level vs Data-Level Approval

## The Key Insight

**Criticality is metadata, not a gate.**

ALL dependencies should be extracted and stored in the knowledge graph. The criticality level (HIGH/MEDIUM/LOW) is simply metadata that describes each dependency's importance for later querying and analysis.

## Two Approaches to Human-in-the-Loop

### Current Implementation: Data-Level Approval (Optional)

- Agent can be configured to request approval for HIGH criticality storage
- This is useful during initial testing to verify extraction quality
- But criticality should NOT determine what gets stored - only what gets flagged for review

### Recommended: Action-Level Approval

- Agent autonomously decides HOW to accomplish goals
- Agent requests approval before EXECUTING actions (calling tools)
- You approve the agent's chosen approach
- This tests true autonomous intelligence

The difference:

- **Data-level**: "Should I store this HIGH criticality item?"
- **Action-level**: "Should I execute extractor_agent to analyze this file?"

## Configuration Options

### Option 1: Disable Data-Level Approval (Store All Dependencies)

To remove criticality-based approval and store all dependencies automatically:

Edit `src/curator/agent.py` around line 238-251:

```python
def _is_high_criticality_storage_call(tool_call: dict[str, Any]) -> bool:
    # DISABLED: Criticality is metadata only, not a storage gate
    return False  # <-- Return False to disable data-level approval
```

Now ALL dependencies are stored immediately with criticality as metadata.

### Option 2: Make Data-Level Approval Configurable

Add a configuration parameter:

```python
def create_curator(require_approval_for_high: bool = False):
    """
    Create the main curator agent.

    Args:
        require_approval_for_high: If True, request approval for HIGH criticality storage.
                                   If False, all dependencies auto-store (recommended).
                                   Note: Criticality is always stored as metadata.
    """
    # ... existing code ...

    def _is_high_criticality_storage_call(tool_call: dict[str, Any]) -> bool:
        if not require_approval_for_high:
            return False
        if tool_call.get("name") != "storage_agent":
            return False
        task = (tool_call.get("args") or {}).get("task", "")
        return "HIGH" in str(task).upper()
```

Then at the bottom:
```python
# Export the graph
graph = create_curator(require_approval_for_high=False)  # Recommended: False
```

### Option 3: Implement Action-Level Approval

For true autonomous intelligence testing, implement action-level approval where the agent asks before executing tools:

See [DESIGN_ACTION_LEVEL_HITL.md](DESIGN_ACTION_LEVEL_HITL.md) for detailed implementation strategies.

Key concept:

- Agent plans autonomously
- Agent shows you WHAT it wants to do and WHY
- You approve EXECUTION, not data storage decisions
- This demonstrates genuine intelligence vs automation

## Recommendation

**For production use**: Option 1 or 2 (disable/configure data-level approval)

Why:

1. ALL dependencies should be extracted and stored
2. Criticality is metadata for querying and analysis
3. You can filter and review by criticality after extraction
4. No interruption to the autonomous workflow

**For testing intelligence**: Implement Option 3 (action-level approval)

Why:

1. Tests if agent can learn from examples
2. Shows autonomous decision-making
3. Demonstrates ability to discover insights
4. Maintains human control over execution

## Using Criticality as Metadata

After storing all dependencies, query by criticality in Neo4j:

```cypher
// Get all HIGH criticality dependencies
MATCH (a)-[r:DEPENDS_ON {criticality: 'HIGH'}]->(b)
RETURN a.name, b.name, r.description

// Get dependency counts by criticality
MATCH ()-[r:DEPENDS_ON]->()
RETURN r.criticality, count(r) as count
ORDER BY count DESC

// Find critical failure paths
MATCH path = (start)-[:DEPENDS_ON*]->(end)
WHERE ALL(r IN relationships(path) WHERE r.criticality = 'HIGH')
RETURN path
```
