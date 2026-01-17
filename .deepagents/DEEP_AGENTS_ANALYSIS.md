# Deep Agents Analysis: PROVES Library vs Best Practices

**Date:** 2026-01-16
**Purpose:** Compare PROVES Library implementation against LangChain's deep-agents-from-scratch patterns, identify gaps, and assess future needs for multi-university scale.

---

## Executive Summary

The PROVES Library has built a **domain-specific agentic system** for CubeSat knowledge extraction with human-in-the-loop verification. The deep-agents-from-scratch repository provides **general-purpose patterns** for building production agents. This analysis compares what we have, what best practices suggest, and what's needed for scale.

**Key Finding:** PROVES has strong domain-specific features (FRAMES, lineage verification, epistemic metadata) but could benefit from adopting three core patterns from deep-agents-from-scratch: **TODO-based task planning**, **virtual file systems for context offloading**, and **sub-agent context isolation**.

---

## 1. Best Practices from deep-agents-from-scratch

### The Three Core Patterns

| Pattern | Purpose | Implementation |
|---------|---------|----------------|
| **Task Planning (TODOs)** | Track multi-step workflows, maintain focus | `write_todos()` / `read_todos()` tools with state persistence |
| **Context Offloading (Files)** | Reduce token usage, enable large documents | Virtual file system (`ls`, `read_file`, `write_file`) in agent state |
| **Context Isolation (Subagents)** | Prevent confusion, enable parallelism | Sub-agent delegation with fresh context per task |

### Key Technical Patterns

**1. State-Aware Tools:**
```python
@tool
def my_tool(
    user_arg: str,
    state: Annotated[DeepAgentState, InjectedState],  # Injected
    tool_call_id: Annotated[str, InjectedToolCallId], # Injected
) -> Command:
    # Return state updates via Command
    return Command(update={"files": files, "messages": [ToolMessage(...)]})
```

**2. State Structure:**
```python
class DeepAgentState(AgentState):
    todos: NotRequired[list[Todo]]              # Task tracking
    files: Annotated[dict[str, str], file_reducer]  # Virtual filesystem
```

**3. Sub-agent Isolation:**
```python
# Fresh context - no parent history pollution
state["messages"] = [{"role": "user", "content": description}]
result = sub_agent.invoke(state)
```

---

## 2. What PROVES Library Has Built

### Current Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    EXTRACTOR    │ ──> │    VALIDATOR    │ ──> │     STORAGE     │
│                 │     │                 │     │                 │
│ Fetch + Extract │     │ Verify + Check  │     │ Persist Data    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        ↓                       ↓                       ↓
   raw_snapshots         core_entities          staging_extractions
```

### PROVES Strengths (Beyond Best Practices)

| Feature | PROVES Has | deep-agents-from-scratch Has | Analysis |
|---------|-----------|------------------------------|----------|
| **FRAMES Epistemic Metadata** | ✅ 7-question checklist, contact/temporality/formalizability | ❌ No epistemic tracking | **PROVES unique contribution** |
| **Lineage Verification** | ✅ verify_evidence_lineage() checks evidence exists in source | ❌ No evidence verification | **Critical for knowledge systems** |
| **Duplicate Detection** | ✅ Orchestrator-level dedup before storage | ❌ Not addressed | **Essential for scale** |
| **Human Review Workflow** | ✅ Curation dashboard, staging → core promotion | ❌ Not addressed | **PROVES core value prop** |
| **Persistent Storage** | ✅ Supabase with RLS, pgvector | ❌ In-memory only | **Required for production** |
| **Domain Models** | ✅ CoreEntity, RawSnapshot, FRAMESDimensions | ❌ Generic state only | **Type safety** |
| **Standards Alignment** | ✅ XTCE/SysML/PyG vocabulary mapping | ❌ Not addressed | **Industry interoperability** |

### PROVES Gaps (Where deep-agents-from-scratch Patterns Could Help)

| Gap | Current State | Best Practice | Impact |
|-----|---------------|---------------|--------|
| **No TODO tracking** | Implicit in orchestrator | `write_todos()` / `read_todos()` | Agents lose track of multi-extraction batches |
| **No virtual filesystem** | Each tool fetches its own data | Files stored in state, read on demand | Token waste, context overflow on large docs |
| **Limited context isolation** | Validator sees full extractor output | Sub-agents with isolated context | Confusion when validating many extractions |
| **No think_tool** | No explicit reflection steps | `think_tool()` for strategic pauses | Agents don't assess "do I have enough?" |
| **Sequential only** | One extraction at a time | Parallel sub-agent delegation | Slow for batch processing |

---

## 3. Gap Analysis: PROVES vs Best Practices

### Pattern Adoption Readiness

| Pattern | Adoption Effort | Benefit | Priority |
|---------|-----------------|---------|----------|
| **TODO Tools** | Low - add 2 tools | Track extraction batches, show progress in dashboard | **P1** |
| **Virtual Filesystem** | Medium - refactor state | Reduce token usage, handle large docs | **P1** |
| **Sub-agent Isolation** | Medium - wrap validators | Cleaner parallel validation | **P2** |
| **Think Tool** | Low - add 1 tool | Better extraction quality decisions | **P2** |

### What PROVES Adds to Best Practices

The PROVES system should **export** these patterns back to the agentic community:

1. **Epistemic Metadata Pattern** - Track how knowledge was acquired, not just what
2. **Lineage Verification Pattern** - Verify AI claims against source documents
3. **Human-in-Loop Staging Pattern** - Separate unverified extractions from verified knowledge
4. **Domain Model Pattern** - Type-safe entities with standard identifiers (URIs/URNs)

---

## 4. Multi-University Scale Requirements

### Current Capacity
- Single-team extraction
- 74 extractions completed
- Sequential processing

### Target Capacity (8+ Universities)
| Requirement | Current | Target | Gap |
|-------------|---------|--------|-----|
| Concurrent extractions | 1 | 10+ per team | Need parallelism |
| Team isolation | Basic RLS | Full multi-tenant | Supabase RLS ready |
| Real-time dashboard | Basic updates | Live collaboration | WebSocket needed |
| Query load | Single user | 50+ concurrent | MCP server scaling |

### Patterns Needed for Scale

**1. Parallel Extraction with Sub-agents:**
```python
# From deep-agents-from-scratch: parallel task delegation
tasks = [
    {"description": f"Extract from {url}", "subagent_type": "extractor"}
    for url in batch_urls
]
# All run in parallel with isolated contexts
```

**2. Context Offloading for Large Document Sets:**
```python
# Store fetched docs in virtual filesystem
files[f"doc_{i}.md"] = fetched_content
# Agents read on demand, not all at once
```

**3. TODO-based Batch Tracking:**
```python
todos = [
    {"content": f"Extract {url}", "status": "pending"}
    for url in batch
]
# Dashboard shows progress: 3/10 complete
```

---

## 5. Future Architecture: Hybrid Approach

### Proposed Evolution

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROVES DEEP AGENT STATE                       │
├─────────────────────────────────────────────────────────────────┤
│  messages: List[BaseMessage]      # Standard LangGraph          │
│  todos: List[ExtractionTask]      # NEW: Task tracking          │
│  files: Dict[str, str]            # NEW: Virtual filesystem     │
│  current_team_id: UUID            # PROVES: Team isolation      │
│  epistemic_defaults: Dict         # PROVES: FRAMES defaults     │
│  extraction_batch: BatchMetadata  # PROVES: Batch tracking      │
└─────────────────────────────────────────────────────────────────┘
```

### Recommended Tool Additions

| Tool | Purpose | Source |
|------|---------|--------|
| `write_extraction_todos()` | Track batch extraction progress | Adapted from deep-agents |
| `read_extraction_todos()` | Recall pending work | Adapted from deep-agents |
| `store_document()` | Offload fetched docs to virtual fs | Adapted from deep-agents |
| `read_document()` | Read stored doc on demand | Adapted from deep-agents |
| `think_about_extraction()` | Reflect on extraction quality | Adapted from deep-agents |
| `delegate_validation()` | Parallel validation with isolation | Adapted from deep-agents |

### What Stays PROVES-Specific

| Component | Reason |
|-----------|--------|
| `verify_evidence_lineage()` | Core to preventing hallucinated evidence |
| `validate_epistemic_structure()` | FRAMES methodology |
| `store_extraction()` | 50+ field signature for rich metadata |
| `check_for_duplicates()` | Required for knowledge graph integrity |
| `promote_to_core()` | Human-in-loop workflow |

---

## 6. Bronco Space Lab Context

### University Satellite Program Needs

| Need | How PROVES Addresses | Future Enhancement |
|------|---------------------|-------------------|
| **Team transitions** | Epistemic metadata captures "who knew this" | Add team handoff workflows |
| **Multi-team collaboration** | Supabase RLS, team_id scoping | Cross-team query federation |
| **MBSE integration** | XTCE/SysML vocabulary alignment | Export serializers |
| **Cascade analysis** | ERV relationship model | GNN for failure prediction |
| **Real-time ops** | MCP server | Live telemetry integration |

### Value Proposition for Employers/Grad Programs

**Technical Skills Demonstrated:**
1. LangGraph agent orchestration with production patterns
2. PostgreSQL with RLS, pgvector, real-time subscriptions
3. Domain-driven design with repository pattern
4. Human-in-loop AI systems
5. Industry standards integration (XTCE, SysML)

**Research Contributions:**
1. FRAMES epistemic methodology
2. Lineage verification for AI knowledge extraction
3. Trust calibration for agent autonomy

---

## 7. Implementation Roadmap

### Phase 1: Adopt Core Patterns (2 weeks)
- [ ] Add `DeepAgentState` extension with todos and files
- [ ] Implement `write_extraction_todos()` / `read_extraction_todos()`
- [ ] Add virtual filesystem tools (`store_document`, `read_document`)
- [ ] Integrate with existing `agent_v3.py` orchestrator

### Phase 2: Enable Parallelism (2 weeks)
- [ ] Create sub-agent registry for validators
- [ ] Implement `delegate_validation()` with context isolation
- [ ] Add batch extraction mode with parallel sub-agents
- [ ] Update dashboard for batch progress tracking

### Phase 3: Scale for Multi-University (4 weeks)
- [ ] Load testing with 8 concurrent team simulations
- [ ] MCP server horizontal scaling
- [ ] Query caching (Redis)
- [ ] Real-time dashboard collaboration features

### Phase 4: Export & Integration (4 weeks)
- [ ] XTCE serializer (from core_entities)
- [ ] SysML v2 serializer
- [ ] PyTorch Geometric export for GNN training
- [ ] Round-trip import capabilities

---

## 8. Conclusion

### What We Have
A production-ready knowledge extraction system with:
- Unique epistemic methodology (FRAMES)
- Lineage verification preventing hallucinated evidence
- Human-in-loop curation workflow
- Industry standards alignment

### What We Should Adopt
Three patterns from deep-agents-from-scratch:
1. **TODO-based task planning** for batch tracking
2. **Virtual filesystem** for context management
3. **Sub-agent isolation** for clean parallel processing

### What We Contribute Back
Patterns the broader agentic AI community could learn from:
1. **Epistemic metadata** for knowledge provenance
2. **Lineage verification** for AI claim validation
3. **Human-in-loop staging** for verified knowledge
4. **Domain models** for type-safe agent state

---

## 9. Agent Self-Improvement System (Already Designed)

PROVES has a **complete trust calibration system** already designed but not yet fully implemented.

### Existing Documentation
- [docs/diagrams/agent-self-improvement.md](../docs/diagrams/agent-self-improvement.md) — Full workflow diagrams
- [supabase/migrations/017_add_agent_oversight.sql](../supabase/migrations/017_add_agent_oversight.sql) — Database schema

### Database Schema (Migration 017)

| Table | Purpose |
|-------|---------|
| `agent_capabilities` | Trust scores per agent per capability type |
| `agent_proposals` | Individual improvement proposals from agents |
| `agent_trust_history` | Audit trail of all trust changes |

### Trust Calibration Rules

| Event | Trust Change | Rationale |
|-------|--------------|-----------|
| Proposal Approved | +5% | Agent's judgment was correct |
| Implementation Succeeds | +8% | Change actually improved system |
| Proposal Rejected | -10% | Agent misjudged what was needed |
| Implementation Fails | -15% | Approved change caused problems |

### Auto-Approve Logic

```sql
-- Trigger: check_auto_approve()
IF NOT v_requires_review AND v_trust_score >= v_threshold THEN
    NEW.status := 'auto_approved';
    NEW.auto_applied := TRUE;
END IF;
```

Default threshold: **90%** trust required for auto-approve.

### Capability Types

| Capability | Description |
|------------|-------------|
| `prompt_update` | Changes to extraction/validation prompts |
| `threshold_change` | Confidence thresholds |
| `method_improvement` | Extraction methodology |
| `validation_rule` | New validation checks |
| `ontology_expansion` | New entity types |
| `tool_configuration` | Tool usage patterns |

### Implementation Status

| Component | Status |
|-----------|--------|
| Database schema (Migration 017) | ✅ Ready to deploy |
| Trust calculation triggers | ✅ Implemented in SQL |
| RLS policies | ✅ Configured |
| Dashboard proposal review UI | ❌ Not built |
| Agent `submit_proposal()` tool | ❌ Not built |
| Impact measurement system | ❌ Not built |
| Proposal notification system | ❌ Not built |

### Why This Matters for Multi-University Scale

The trust calibration system enables:

1. **Per-team trust levels** — Each university can have different thresholds
2. **Graduated autonomy** — Routine extractions auto-approve, novel ones require review
3. **Audit trail** — Full history of why agents changed
4. **Safety** — High-risk capabilities (ontology_expansion) can require review forever

### Integration with deep-agents-from-scratch Patterns

The trust system could benefit from:

| Pattern | Application |
|---------|-------------|
| **TODO tracking** | Track proposal implementation as tasks |
| **Virtual filesystem** | Store proposed prompt changes for diff review |
| **Think tool** | Agent reflection before proposing: "Is this worth proposing?" |

---

## References

- `.deepagents_fromscratch/` - LangChain deep agents tutorial
- `.deepagents/IMPLEMENTATION_ROADMAP.md` - Current PROVES roadmap
- `.deepagents/AGENT_CONTRACTS.md` - Agent communication contracts
- `docs/architecture/AGENTIC_ARCHITECTURE.md` - System design
- `.deepagents/INTEGRATION_ARCHITECTURE.md` - FRAMES + MBSE integration
- `docs/diagrams/agent-self-improvement.md` - Trust calibration workflow
- `supabase/migrations/017_add_agent_oversight.sql` - Agent oversight database schema
