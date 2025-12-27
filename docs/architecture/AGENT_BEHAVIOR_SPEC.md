# PROVES Library - Agent Behavior Specification v2

## Overview

This document defines the **3-agent architecture** for the PROVES Library curation pipeline. Each agent has a specific role, and loop control is handled by **LangGraph's built-in middleware**—not custom schema fields.

## Architecture: 3 Agents

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER REQUEST                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         1. EXTRACTOR AGENT                                  │
│  Fetch source -> Parse content -> Extract candidates -> Assign confidence     │
│                                                                             │
│  OUTPUT: staging_extractions (candidates with evidence + confidence)        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │      REFINEMENT LOOP          │
                    │   (recursion_limit = 5)       │
                    ▼                               │
┌─────────────────────────────────────────────────────────────────────────────┐
│                         2. VALIDATOR AGENT                                  │
│  Check confidence -> Validate evidence -> Request more info OR approve       │
│                                                                             │
│  IF needs_more_evidence -> LOOP BACK to Extractor (up to recursion_limit)   │
│  IF acceptable -> PASS to Decision Maker                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      3. DECISION MAKER AGENT                                │
│  Final gate: Promote to core_entities OR package for human review          │
│                                                                             │
│  IF high confidence + complete -> AUTO-PROMOTE (with audit log)             │
│  IF medium/low OR incomplete -> QUEUE for human review                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
          ┌─────────────────┐             ┌─────────────────┐
          │  core_entities  │             │  HITL Queue     │
          │  (canonical)    │             │  (human review) │
          └─────────────────┘             └─────────────────┘
```

## What's NOT an Agent

These are **deterministic pipeline functions**, not LLM agents:

| Function | Why Not an Agent |
|----------|------------------|
| **Chunking** | Deterministic text splitting (no LLM needed) |
| **Embedding** | API call to embedding model (no reasoning) |
| **Graph Building** | Deterministic node/edge creation from entities |
| **Scoring** | Rule-based or ML model inference (no agent loop) |

These run **after** entities are promoted to `core_entities`, as batch jobs.

---

## Loop Control: LangGraph Built-Ins

### 1. Graph-Level: `recursion_limit`

Limits the number of super-steps in a graph execution. Default is 25.

```python
from langgraph.graph import StateGraph

graph = create_curator_graph()

# Invoke with recursion limit
result = graph.invoke(
    {"document_url": "https://..."},
    config={"recursion_limit": 10}  # Max 10 round-trips
)
```

When limit is reached, raises `GraphRecursionError`. Handle gracefully:

```python
from langgraph.errors import GraphRecursionError

try:
    result = graph.invoke(inputs, config={"recursion_limit": 5})
except GraphRecursionError:
    # Escalate to human after max refinement attempts
    queue_for_human_review(inputs)
```

### 2. Agent-Level: `ToolCallLimitMiddleware`

Limits tool calls per agent to prevent runaway loops.

```python
from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware

# Global limit across all tools
global_limiter = ToolCallLimitMiddleware(
    thread_limit=50,   # Max across entire conversation
    run_limit=15,      # Max per single invocation
    exit_behavior="continue"  # or "error" or "end"
)

# Per-tool limits (expensive operations)
fetch_limiter = ToolCallLimitMiddleware(
    tool_name="fetch_document",
    run_limit=3,       # Max 3 fetches per run
    exit_behavior="error"
)

extractor_agent = create_agent(
    model="claude-sonnet-4-20250514",
    tools=[fetch_tool, parse_tool, extract_tool],
    middleware=[global_limiter, fetch_limiter]
)
```

### 3. Model Call Limit (JS)

```javascript
import { createAgent, modelCallLimitMiddleware } from "langchain";

const agent = createAgent({
  model: "gpt-4o",
  tools: [...],
  middleware: [
    modelCallLimitMiddleware({
      threadLimit: 20,
      runLimit: 10,
      exitBehavior: "end"
    })
  ]
});
```

---

## Agent 1: Extractor

**Purpose**: Fetch source documents, parse content, extract structured candidates with confidence scores.

### Responsibilities

1. **Fetch** source documents (URLs, files, GitHub repos)
2. **Parse** content into structured format
3. **Extract** candidate entities/relationships
4. **Score** each candidate using the confidence rubric
5. **Store** in `staging_extractions` with status = `pending`

### Allowed Operations

| Table | Operation | Notes |
|-------|-----------|-------|
| `raw_snapshots` | INSERT | Store fetched content |
| `staging_extractions` | INSERT | Store extracted candidates |
| `pipeline_runs` | INSERT, UPDATE | Track run progress |

### Forbidden Operations

- [NO] UPDATE `raw_snapshots` content (immutable)
- [NO] Any writes to `core_entities` (Decision Maker's job)
- [NO] Setting `status = 'accepted'` (requires Validator)

### Output Schema

Every extraction MUST include:

```python
{
    # Identity
    "candidate_type": "component|port|dependency|...",
    "candidate_key": "fprime:Svc:TlmChan",
    "candidate_payload": {...},  # Extracted fields as JSONB
    
    # Confidence (REQUIRED)
    "confidence_score": 0.85,    # Numeric 0.0-1.0
    "confidence_reason": "Formal port definition with complete signature",
    
    # Evidence (REQUIRED)
    "evidence": {
        "text": "port BufferGet: Fw.Buffer",
        "source": {"doc": "TlmChan.fpp", "lines": [45, 52]}
    },
    "evidence_type": "interface_contract",
    
    # Status (ALWAYS pending)
    "status": "pending"
}
```

### Confidence Rubric

| Level | Score Range | Criteria |
|-------|-------------|----------|
| **HIGH** | 0.80–1.00 | Formal definition (`is/shall/must`), F´ vocabulary match, multiple sources agree |
| **MEDIUM** | 0.50–0.79 | Strong cues but not formal, example-based, missing 1–2 properties |
| **LOW** | 0.00–0.49 | Narrative inference, single mention, conflicts with other sources |

---

## Agent 2: Validator

**Purpose**: Check the Extractor's work. Request refinement or approve for promotion.

### Responsibilities

1. **Review** pending extractions from `staging_extractions`
2. **Validate** confidence score matches evidence quality
3. **Check** for missing fields, conflicts, duplicates
4. **Decide**: 
   - `needs_more_evidence` -> Loop back to Extractor
   - `acceptable` -> Pass to Decision Maker

### Allowed Operations

| Table | Operation | Notes |
|-------|-----------|-------|
| `staging_extractions` | UPDATE status | Only status field |
| `validation_decisions` | INSERT | Record decision + reasoning |

### Forbidden Operations

- [NO] Modifying extraction content (only status)
- [NO] Promoting to `core_entities` (Decision Maker's job)
- [NO] Auto-accepting without evidence review

### Refinement Loop

```python
def validate_extraction(extraction):
    """Validator's decision logic."""
    
    # Check evidence quality
    if not extraction.evidence or extraction.evidence.get("text") == "":
        return {
            "decision": "needs_more_evidence",
            "reason": "No evidence text provided",
            "request": "Extract the exact source quote supporting this candidate"
        }
    
    # Check confidence matches evidence
    if extraction.evidence_type == "narrative" and extraction.confidence_score > 0.6:
        return {
            "decision": "needs_more_evidence", 
            "reason": "Confidence too high for narrative-only evidence",
            "request": "Find formal definition or additional sources"
        }
    
    # Check for missing fields
    if extraction.candidate_type == "telemetry":
        required = ["channel_name", "data_type", "units"]
        missing = [f for f in required if f not in extraction.candidate_payload]
        if missing:
            return {
                "decision": "needs_more_evidence",
                "reason": f"Missing required fields: {missing}",
                "request": f"Extract {missing} from source document"
            }
    
    # Passed validation
    return {"decision": "acceptable", "reason": "Evidence supports confidence level"}
```

### Loop Limit Handling

The Validator does NOT track retry counts. LangGraph's `recursion_limit` handles this:

```python
# In the graph definition
workflow = StateGraph(State)
workflow.add_node("extractor", extractor_node)
workflow.add_node("validator", validator_node)
workflow.add_node("decision_maker", decision_maker_node)

# Conditional edge: validator may loop back to extractor
workflow.add_conditional_edges(
    "validator",
    lambda state: "extractor" if state["needs_refinement"] else "decision_maker"
)

# Runtime: limit loops
graph.invoke(input, config={"recursion_limit": 5})  # Max 5 Extractor↔Validator loops
```

When `GraphRecursionError` is raised, escalate to human:

```python
except GraphRecursionError:
    # Max refinement attempts reached
    store_for_human_review(
        extraction_id=current_extraction.id,
        reason="Exceeded refinement limit after 5 attempts"
    )
```

---

## Agent 3: Decision Maker

**Purpose**: Final gate. Promote to canonical OR queue for human review.

### Responsibilities

1. **Receive** validated extractions from Validator
2. **Apply** promotion rules based on confidence + completeness
3. **Promote** high-confidence candidates to `core_entities`
4. **Queue** uncertain candidates for human review

### Decision Rules

```python
def make_decision(extraction):
    """Decision Maker's promotion logic."""
    
    score = extraction.confidence_score
    has_all_fields = not extraction.missing_fields
    
    # Auto-promote: High confidence + complete
    if score >= 0.80 and has_all_fields:
        return {
            "decision": "accept",
            "action": "promote_to_core",
            "reason": f"High confidence ({score}) with complete fields"
        }
    
    # Queue for human: Medium confidence or incomplete
    if 0.50 <= score < 0.80:
        return {
            "decision": "defer",
            "action": "queue_for_human",
            "priority": "normal",
            "reason": f"Medium confidence ({score}) requires human verification"
        }
    
    # Queue for human with high priority: Low confidence
    if score < 0.50:
        return {
            "decision": "defer",
            "action": "queue_for_human",
            "priority": "high",
            "reason": f"Low confidence ({score}) needs expert review"
        }
    
    # Edge case: High confidence but missing fields
    return {
        "decision": "defer",
        "action": "queue_for_human",
        "priority": "normal",
        "reason": f"High confidence but missing: {extraction.missing_fields}"
    }
```

### Allowed Operations

| Table | Operation | Notes |
|-------|-----------|-------|
| `core_entities` | INSERT | Promote accepted candidates |
| `staging_extractions` | UPDATE status | Mark accepted/rejected |
| `validation_decisions` | INSERT | Record final decision |

### Promotion Flow

```python
def promote_extraction(extraction, decision):
    """Promote to core_entities with full provenance."""
    
    # 1. Insert into core_entities
    entity_id = insert_core_entity(
        entity_type=extraction.candidate_type,
        canonical_key=extraction.candidate_key,
        name=extraction.candidate_payload.get("name"),
        attributes=extraction.candidate_payload,
        ecosystem=extraction.ecosystem,
        source_snapshot_id=extraction.snapshot_id,
        created_from_extraction_id=extraction.extraction_id  # Provenance link
    )
    
    # 2. Update staging extraction status
    update_staging_extraction(
        extraction_id=extraction.extraction_id,
        status="accepted",
        promoted_to_id=entity_id,
        promoted_at=now()
    )
    
    # 3. Record decision
    insert_validation_decision(
        extraction_id=extraction.extraction_id,
        decided_by="decision_maker_agent",
        decider_type="validator_agent",
        decision="accept",
        decision_reason=decision["reason"],
        canonical_id=entity_id,
        confidence_at_decision=extraction.confidence_score
    )
    
    return entity_id
```

---

## Database Tables Summary

| Table | Layer | Purpose | Written By |
|-------|-------|---------|------------|
| `raw_snapshots` | Raw | Immutable source content | Extractor |
| `staging_extractions` | Raw | Candidates with confidence | Extractor |
| `validation_decisions` | Raw | Decision audit log | Validator, Decision Maker |
| `core_entities` | Core | Canonical entities | Decision Maker only |
| `core_equivalences` | Core | Cross-system mappings | Decision Maker only |

---

## Pipeline Functions (Not Agents)

These run **after** promotion to `core_entities`:

### Chunking (Batch Job)

```python
def chunk_documents(snapshot_ids: list[UUID]):
    """Deterministic chunking - no LLM needed."""
    for snapshot_id in snapshot_ids:
        content = get_snapshot_content(snapshot_id)
        chunks = semantic_chunker(content, max_tokens=512)
        for i, chunk in enumerate(chunks):
            insert_doc_chunk(snapshot_id, i, chunk)
```

### Embedding (Batch Job)

```python
def embed_chunks(chunk_ids: list[UUID]):
    """API call to embedding model - no agent loop."""
    for chunk_id in chunk_ids:
        chunk_text = get_chunk_text(chunk_id)
        embedding = openai.embed(chunk_text, model="text-embedding-3-small")
        insert_embedding(chunk_id, embedding)
```

### Graph Building (Batch Job)

```python
def build_graph(entity_ids: list[UUID]):
    """Deterministic graph construction from entities."""
    for entity_id in entity_ids:
        entity = get_entity(entity_id)
        insert_graph_node(entity)
        
        # Build edges from relationships in entity attributes
        for dep in entity.attributes.get("dependencies", []):
            target = find_entity_by_key(dep["target"])
            if target:
                insert_graph_edge(entity_id, target.id, dep["type"])
```

---

## Complete Graph Definition

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

# State schema
class CuratorState(TypedDict):
    document_url: str
    raw_content: Optional[str]
    extractions: list[dict]
    current_extraction: Optional[dict]
    validation_result: Optional[dict]
    promoted_entities: list[UUID]
    needs_refinement: bool

# Build graph
workflow = StateGraph(CuratorState)

# Add nodes
workflow.add_node("extractor", extractor_agent)
workflow.add_node("validator", validator_agent)
workflow.add_node("decision_maker", decision_maker_agent)

# Entry point
workflow.set_entry_point("extractor")

# Edges
workflow.add_edge("extractor", "validator")

# Conditional: Validator -> Extractor (refinement) or -> Decision Maker
workflow.add_conditional_edges(
    "validator",
    lambda state: "extractor" if state["needs_refinement"] else "decision_maker"
)

# Decision Maker -> END
workflow.add_edge("decision_maker", END)

# Compile with checkpointer
checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)
graph = workflow.compile(checkpointer=checkpointer)

# Invoke with loop limit
result = graph.invoke(
    {"document_url": "https://github.com/nasa/fprime/..."},
    config={
        "recursion_limit": 10,  # Max Extractor↔Validator loops
        "configurable": {"thread_id": "extraction_run_001"}
    }
)
```

---

## Middleware Configuration

```python
from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware

# Create agents with appropriate limits

extractor_agent = create_agent(
    model="claude-sonnet-4-20250514",
    tools=[fetch_document, parse_content, extract_candidates],
    middleware=[
        ToolCallLimitMiddleware(run_limit=20, exit_behavior="continue"),
        ToolCallLimitMiddleware(tool_name="fetch_document", run_limit=5)
    ]
)

validator_agent = create_agent(
    model="claude-sonnet-4-20250514", 
    tools=[check_evidence, find_duplicates, request_refinement],
    middleware=[
        ToolCallLimitMiddleware(run_limit=10, exit_behavior="continue")
    ]
)

decision_maker_agent = create_agent(
    model="claude-sonnet-4-20250514",
    tools=[promote_entity, queue_for_review, record_decision],
    middleware=[
        ToolCallLimitMiddleware(run_limit=5, exit_behavior="end")
    ]
)
```

---

## Summary

| Aspect | Old Approach (9 agents) | New Approach (3 agents) |
|--------|-------------------------|-------------------------|
| Agent Count | 9 (bloat) | 3 (focused) |
| Loop Control | Custom `refinement_count` column | LangGraph `recursion_limit` |
| Tool Limits | None | `ToolCallLimitMiddleware` |
| Chunking | Agent | Batch function |
| Embedding | Agent | Batch function |
| Graph Building | Agent | Batch function |
| Scoring | Agent | Batch function |

**The key insight**: Only steps requiring LLM reasoning are agents. Everything else is a deterministic pipeline function.
