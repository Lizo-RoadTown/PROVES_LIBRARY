# PROVES Library: Peer Reflection Architecture Analysis

**Date:** 2026-01-16
**Purpose:** Comprehensive analysis of the PROVES agentic system, comparing against industry best practices, with a focus on peer reflection for drift detection and trust calibration.
**Audience:** Technical reviewers, potential collaborators, graduate program evaluators

---

## Executive Summary

PROVES Library is a knowledge extraction system for CubeSat development that uses AI agents with human-in-the-loop verification. This analysis evaluates the system against LangChain's deep-agents-from-scratch best practices and proposes a **peer reflection architecture** where agents monitor each other rather than themselves.

**Key Insight:** Drift detection and trust calibration are fundamentally **traceability problems**. PROVES already has the database schema for traceability. The missing piece is an **analyzer agent** that queries peer performance metrics and proposes evidence-based improvements.

**Recommendation:** Implement peer reflection. It transforms the trust calibration system from "interesting logging" into a defensible, novel contribution to agentic AI.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Comparison with Best Practices](#2-comparison-with-best-practices)
3. [The Drift Problem](#3-the-drift-problem)
4. [Peer Reflection Architecture](#4-peer-reflection-architecture)
5. [Trust Calibration Reassessment](#5-trust-calibration-reassessment)
6. [Implementation Status](#6-implementation-status)
7. [Risk Analysis](#7-risk-analysis)
8. [Recommendations](#8-recommendations)
9. [Technical Appendix](#9-technical-appendix)

---

## 1. System Overview

### 1.1 What PROVES Library Does

PROVES Library addresses a specific problem: **88% of university CubeSat programs fail**, largely due to knowledge loss during team transitions. When students graduate, critical understanding of design decisions disappears.

The system:
1. **Extracts** technical knowledge from documentation using AI agents
2. **Verifies** extractions through human review (lineage verification)
3. **Stores** verified knowledge in a queryable graph
4. **Enables** natural language queries via MCP server

### 1.2 Current Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    EXTRACTOR    │────>│    VALIDATOR    │────>│     STORAGE     │
│                 │     │                 │     │                 │
│ Fetch docs      │     │ Verify lineage  │     │ Persist to DB   │
│ Extract entities│     │ Check duplicates│     │                 │
│ Assign confidence│    │ Validate epistemic│   │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
  raw_snapshots          validation_decisions    staging_extractions
                                                        │
                                                        ▼
                                              ┌─────────────────┐
                                              │  HUMAN REVIEW   │
                                              │  (Dashboard)    │
                                              └─────────────────┘
                                                        │
                                                        ▼
                                                 core_entities
```

### 1.3 Technology Stack

| Layer | Technology |
|-------|------------|
| LLM | Claude Sonnet 4.5 (Anthropic) |
| Agent Orchestration | LangGraph, LangChain |
| Database | Supabase (PostgreSQL + pgvector) |
| Frontend | React, Vite, Tailwind CSS |
| Query Interface | Model Context Protocol (MCP) |

### 1.4 Unique Contributions

| Feature | Description | Industry Status |
|---------|-------------|-----------------|
| **FRAMES Epistemic Metadata** | 7-question checklist tracking how knowledge was acquired | Novel |
| **Lineage Verification** | Verify AI-extracted evidence exists in source document | Novel |
| **Human-in-Loop Staging** | Separate unverified extractions from verified knowledge | Uncommon |
| **Trust Calibration** | Per-capability trust scores with graduated autonomy | Novel |

---

## 2. Comparison with Best Practices

### 2.1 Reference: deep-agents-from-scratch

LangChain's official tutorial identifies three core patterns for production agents:

| Pattern | Purpose | PROVES Status |
|---------|---------|---------------|
| **Task Planning (TODOs)** | Track multi-step workflows | ❌ Not implemented |
| **Context Offloading (Files)** | Reduce token usage via virtual filesystem | ❌ Not implemented |
| **Context Isolation (Subagents)** | Prevent confusion with isolated contexts | ⚠️ Partial (sequential only) |

### 2.2 What PROVES Has That Best Practices Don't

| PROVES Feature | deep-agents-from-scratch | Assessment |
|----------------|--------------------------|------------|
| Epistemic metadata | ❌ None | **PROVES ahead** |
| Lineage verification | ❌ None | **PROVES ahead** |
| Persistent storage | ❌ In-memory only | **PROVES ahead** |
| Human review workflow | ❌ None | **PROVES ahead** |
| Domain models (URIs/URNs) | ❌ Generic state | **PROVES ahead** |
| Industry standards alignment | ❌ None | **PROVES ahead** |

### 2.3 What PROVES Should Adopt

| Pattern | Benefit | Priority |
|---------|---------|----------|
| TODO-based task tracking | Batch extraction progress visible in dashboard | P1 |
| Virtual filesystem | Handle large documents without token overflow | P1 |
| Parallel sub-agents | Faster batch processing | P2 |
| Think tool | Explicit reflection before proposing changes | P2 |

---

## 3. The Drift Problem

### 3.1 How Current Agents Handle Drift

| Approach | Method | Problem |
|----------|--------|---------|
| **Periodic retraining** | Collect data, fine-tune | Expensive, loses old knowledge |
| **Prompt versioning** | Manual updates in git | Not data-driven |
| **Eval suites** | Run benchmarks | Measures symptoms, not cause |
| **RLHF** | Feedback on outputs | No granularity, reward hacking |

### 3.2 Drift Is a Traceability Problem

Every type of "drift" is actually a missing join in the database:

| What We Call It | What It Actually Is |
|-----------------|---------------------|
| Model drift | Can't trace which model version produced which output |
| Prompt decay | Can't trace which prompt version was active |
| Distribution shift | Can't trace document characteristics at extraction time |
| Reviewer drift | Can't trace who approved under which standards |
| Concept drift | Can't trace how definitions evolved |

**If you can trace it, you can diff it. If you can diff it, you can debug it.**

### 3.3 PROVES Traceability Status

| What's Traced | Where | Status |
|---------------|-------|--------|
| Source document | `raw_snapshots.id` | ✅ |
| Evidence quote | `staging_extractions.raw_evidence` | ✅ |
| Who extracted | `observer_id`, `observer_type` | ✅ |
| When extracted | `created_at`, `valid_from` | ✅ |
| Confidence reasoning | `confidence_reason` | ✅ |
| Who approved | `validation_decisions.actor_id` | ✅ |
| Document hash | `raw_snapshots.content_hash` | ✅ |
| Trust changes | `agent_trust_history` | ✅ |
| Model version | — | ❌ Missing |
| Prompt version | — | ❌ Missing |

### 3.4 Drift Detection Query (Once Traceability Complete)

```sql
-- "Why did extraction quality drop in January?"
SELECT
    e.created_at,
    e.observer_id,           -- Which model?
    e.confidence_score,
    rs.content_hash,         -- Same doc or different?
    vd.actor_id,             -- Who reviewed?
    vd.action_type,          -- Approved or rejected?
    ath.change_reason        -- Trust impact?
FROM staging_extractions e
JOIN raw_snapshots rs ON e.source_snapshot_id = rs.id
LEFT JOIN validation_decisions vd ON e.id = vd.extraction_id
LEFT JOIN agent_trust_history ath ON ...
WHERE e.created_at BETWEEN '2026-01-01' AND '2026-01-31'
ORDER BY e.created_at;
```

**Diagnosis by pattern:**
- Same document, different model → model drift
- Same model, different document type → distribution shift
- Same everything, different reviewer → reviewer drift
- Same reviewer, higher rejection rate → quality drop or concept drift

---

## 4. Peer Reflection Architecture

### 4.1 Self-Reflection vs Peer Reflection

| Aspect | Self-Reflection | Peer Reflection |
|--------|-----------------|-----------------|
| Question | "Did I do a good job?" | "Did the extractor do a good job?" |
| Bias | Same biases, same blind spots | Different perspective |
| Drift visibility | Can't see own drift | Can see drift in others |
| Motivation | Motivated to approve own work | No stake in other's output |
| Gaming risk | High — farm safe proposals | Low — no benefit to gaming |

### 4.2 Current Pipeline Already Uses Peer Review

The validator already reflects on the extractor's work for **individual extractions**:

```python
verify_evidence_lineage()      # Does this quote exist in the source?
validate_epistemic_structure() # Are metadata fields coherent?
check_for_duplicates()         # Already extracted?
```

### 4.3 Proposed Extension: Peer Reflection on Patterns

Add an **Improvement Analyzer** agent that reflects on **aggregate patterns**, not individual extractions:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  EXTRACTOR  │────>│  VALIDATOR  │────>│   STORAGE   │
└─────────────┘     └─────────────┘     └─────────────┘
       ▲                   ▲
       │                   │
       └───────┬───────────┘
               │ watches
               ▼
      ┌─────────────────┐
      │    ANALYZER     │
      │                 │
      │ Query metrics   │
      │ Detect patterns │
      │ Propose changes │
      └─────────────────┘
               │
               ▼
      ┌─────────────────┐
      │  HUMAN REVIEW   │
      │                 │
      │ Approve/reject  │
      │ proposal        │
      └─────────────────┘
```

### 4.4 Analyzer Responsibilities

| Function | Query | Output |
|----------|-------|--------|
| **Confidence calibration** | Compare claimed confidence vs actual acceptance rate | "Extractor overconfident on F´ docs by 25%" |
| **Rejection trends** | Track rejection rate over time | "Validator rejection rate up 15% this month" |
| **Ecosystem bias** | Compare metrics across ecosystems | "PROVES Kit extractions 2x more likely to be accepted" |
| **Lineage failure patterns** | Track which evidence types fail verification | "Code snippets fail lineage 40% more than prose" |

### 4.5 Example Peer Analysis Queries

**Confidence Calibration:**
```sql
SELECT
    ecosystem,
    AVG(confidence_score) as claimed_confidence,
    AVG(CASE WHEN status = 'accepted' THEN 1.0 ELSE 0.0 END) as actual_acceptance
FROM staging_extractions
GROUP BY ecosystem;

-- If claimed >> actual: extractor overconfident
-- If claimed << actual: extractor underconfident
```

**Validator Drift:**
```sql
SELECT
    DATE_TRUNC('week', created_at) as week,
    AVG(CASE WHEN action_type = 'reject' THEN 1.0 ELSE 0.0 END) as rejection_rate
FROM validation_decisions
GROUP BY week
ORDER BY week;

-- Rising rejection rate = validator or extractor drift
```

### 4.6 Analyzer Tool Specification

```python
@tool
def analyze_peer_performance(
    target_agent: str,      # 'extractor' or 'validator'
    metric: str,            # 'confidence_calibration', 'rejection_trend',
                            # 'lineage_failure_rate', 'ecosystem_bias'
    time_window: str,       # '7d', '30d', '90d'
    ecosystem: str = None   # Optional filter
) -> dict:
    """
    Analyze another agent's performance patterns.

    Returns:
        - metric_value: The calculated metric
        - baseline: Historical baseline for comparison
        - drift_detected: Boolean
        - proposed_action: Optional change proposal if drift significant
        - evidence: Supporting data for the proposal
    """
```

### 4.7 Separation of Concerns

| Agent | Responsibility | Proposes Changes To |
|-------|----------------|---------------------|
| Extractor | Extract entities from documents | — |
| Validator | Verify individual extractions | — |
| Storage | Persist verified data | — |
| **Analyzer** | Detect patterns, propose improvements | Extractor, Validator |

**Critical constraint:** No agent ever approves its own improvement. Analyzer proposes → Human approves → Target agent changes.

---

## 5. Trust Calibration Reassessment

### 5.1 Original Design (Self-Reflection)

The existing Migration 017 schema assumes agents propose their own improvements:

| Event | Trust Change |
|-------|--------------|
| Proposal Approved | +5% |
| Implementation Succeeds | +8% |
| Proposal Rejected | -10% |
| Implementation Fails | -15% |

**Problems with self-reflection:**
- Gaming: Agent proposes safe changes to farm trust
- Blind spots: Same model can't see own biases
- Circular measurement: Agent judges if own change worked

### 5.2 Revised Design (Peer Reflection)

| Event | Trust Change | Who Proposes | Who's Affected |
|-------|--------------|--------------|----------------|
| Proposal Approved | +5% | Analyzer | Analyzer's trust |
| Implementation Succeeds | +8% | Analyzer | Analyzer's trust |
| Proposal Rejected | -10% | Analyzer | Analyzer's trust |
| Target Metrics Improve | — | — | Target agent's metrics (observed) |

**Key change:** Trust score reflects "Are your diagnoses correct?" not "Do you approve yourself?"

### 5.3 What's Good About Trust Calibration (Peer Model)

| Benefit | Mechanism |
|---------|-----------|
| **Graduated autonomy** | Analyzer earns trust for threshold changes, stays supervised for ontology |
| **Reduced reviewer fatigue** | Routine proposals auto-approve once trust established |
| **Audit trail** | Every change traced to proposal, evidence, and reviewer |
| **Data-driven proposals** | Analyzer queries metrics, doesn't guess |
| **Independent measurement** | Analyzer measures extractor; no circular evaluation |

### 5.4 What's Still Hard

| Challenge | Mitigation |
|-----------|------------|
| Analyzer could be wrong | Human review remains required; analyzer earns trust slowly |
| Humans might rubber-stamp | Require evidence in proposals; reviewers see supporting data |
| Feedback loops | Rate-limit proposals; require cooldown after changes |
| Who watches the analyzer? | Humans permanently; never auto-approve for `ontology_expansion` |

### 5.5 The "Who Watches the Watchman" Problem

```
Extractor ←── Analyzer watches
Validator ←── Analyzer watches
Analyzer  ←── ???
```

**Recommendation:** Humans permanently supervise the analyzer. The analyzer can earn trust for low-risk capabilities (`threshold_change`) but never for high-risk ones (`ontology_expansion`, `method_improvement`).

```sql
-- Seed analyzer capabilities with permanent review requirement
INSERT INTO agent_capabilities (agent_name, capability_type, requires_review) VALUES
    ('improvement_analyzer', 'threshold_change', FALSE),      -- Can earn auto-approve
    ('improvement_analyzer', 'prompt_update', FALSE),         -- Can earn auto-approve
    ('improvement_analyzer', 'ontology_expansion', TRUE),     -- Always requires review
    ('improvement_analyzer', 'method_improvement', TRUE);     -- Always requires review
```

---

## 6. Implementation Status

### 6.1 What's Built

| Component | Status | Location |
|-----------|--------|----------|
| Extraction pipeline | ✅ Production | `production/Version 3/` |
| Lineage verification | ✅ Production | `validator_v3.py` |
| Epistemic metadata | ✅ Production | `storage_v3.py` |
| Curation dashboard | ✅ Production | `curation_dashboard/` |
| Trust calibration schema | ✅ Ready to deploy | `supabase/migrations/017_add_agent_oversight.sql` |
| Trust calculation triggers | ✅ Implemented | Migration 017 |
| RLS policies | ✅ Configured | Migration 017 |
| Domain models | ✅ Production | `production/core/domain/` |
| Standard identifiers | ✅ Production | `production/core/identifiers.py` |

### 6.2 What's Not Built

| Component | Priority | Effort |
|-----------|----------|--------|
| `analyze_peer_performance()` tool | **P0** | Medium |
| Peer drift SQL views | **P0** | Low |
| Dashboard proposal review UI | P1 | Medium |
| `submit_proposal()` tool | P1 | Low |
| Model version tracking | P1 | Low |
| Prompt version tracking | P1 | Low |
| Proposal notification system | P2 | Medium |
| TODO-based task tracking | P2 | Medium |
| Virtual filesystem | P2 | Medium |

### 6.3 Database Tables

**Existing (Production):**
- `raw_snapshots` — Source document storage
- `staging_extractions` — Unverified extractions
- `core_entities` — Verified knowledge
- `validation_decisions` — Review audit trail
- `knowledge_epistemics` — FRAMES metadata

**Ready to Deploy (Migration 017):**
- `agent_capabilities` — Per-agent per-capability trust scores
- `agent_proposals` — Improvement proposals
- `agent_trust_history` — Trust change audit trail

### 6.4 Test Coverage

- 111 tests passing
- Domain models fully tested
- Repository pattern tested
- Identifier generation tested

---

## 7. Risk Analysis

### 7.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Analyzer proposes bad changes | Medium | Medium | Human review required; trust earned slowly |
| Trust gaming | Low (with peer model) | Medium | Analyzer has no stake in target's trust |
| Feedback loops | Medium | Low | Rate limiting; cooldown periods |
| Complexity overhead | Medium | Medium | Phased implementation; start with metrics only |

### 7.2 Adoption Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Reviewer fatigue | Medium | High | Auto-approve for proven capabilities |
| Cold start (0% trust) | High | Low | Seed at 30% for safe capabilities |
| Proposal backlog | Medium | Medium | Priority queue; batch similar proposals |

### 7.3 Research Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Approach doesn't work | Low | High | Incremental deployment; measure before/after |
| Can't publish | Low | Medium | Novel contribution even if results mixed |
| Scooped | Low | Low | Unique domain (CubeSat); specific implementation |

---

## 8. Recommendations

### 8.1 Immediate Actions (Next 2 Weeks)

1. **Deploy Migration 017** — Trust calibration schema ready
2. **Add model version tracking** — Single column addition
3. **Create peer drift SQL views** — Queries analyzer will use
4. **Implement `analyze_peer_performance()` tool** — Core new capability

### 8.2 Short-Term (Next Month)

1. **Dashboard proposal UI** — Engineers review proposals
2. **`submit_proposal()` tool** — Analyzer can propose changes
3. **Seed capabilities with appropriate `requires_review` flags**
4. **Implement confidence calibration metric first** — Easiest to measure

### 8.3 Medium-Term (Next Quarter)

1. **TODO-based batch tracking** — From deep-agents-from-scratch
2. **Virtual filesystem** — For large document handling
3. **Parallel extraction** — Multi-university scale
4. **MCP server scaling** — Query load handling

### 8.4 Research Outputs

| Output | Venue | Timeline |
|--------|-------|----------|
| Peer reflection pattern | Blog post / technical report | 1 month |
| Trust calibration results | Workshop paper | 3 months |
| Full system paper | Conference submission | 6 months |

---

## 9. Technical Appendix

### 9.1 Key Files

| File | Purpose |
|------|---------|
| `production/Version 3/agent_v3.py` | Orchestrator |
| `production/Version 3/extractor_v3.py` | Extraction agent |
| `production/Version 3/validator_v3.py` | Validation agent |
| `production/Version 3/storage_v3.py` | Storage agent |
| `supabase/migrations/017_add_agent_oversight.sql` | Trust calibration schema |
| `docs/diagrams/agent-self-improvement.md` | Trust workflow diagrams |
| `.deepagents/AGENT_CONTRACTS.md` | Agent communication contracts |
| `.deepagents/INTEGRATION_ARCHITECTURE.md` | FRAMES + MBSE integration |

### 9.2 Proposed Analyzer Tool Implementation

```python
from langchain.tools import tool
from typing import Literal
import psycopg2

@tool
def analyze_peer_performance(
    target_agent: Literal["extractor", "validator"],
    metric: Literal[
        "confidence_calibration",
        "rejection_trend",
        "lineage_failure_rate",
        "ecosystem_bias"
    ],
    time_window: Literal["7d", "30d", "90d"],
    ecosystem: str = None
) -> dict:
    """
    Analyze another agent's performance patterns to detect drift.

    Args:
        target_agent: Which agent to analyze
        metric: Which metric to compute
        time_window: How far back to look
        ecosystem: Optional filter by ecosystem

    Returns:
        dict with:
        - metric_value: The calculated metric
        - baseline: Historical baseline (prior period)
        - drift_detected: True if significant change
        - drift_direction: 'improving', 'degrading', or 'stable'
        - proposed_action: Suggested change if drift detected
        - evidence: Supporting query results
    """

    # Query implementation based on metric type
    if metric == "confidence_calibration":
        return _analyze_confidence_calibration(target_agent, time_window, ecosystem)
    elif metric == "rejection_trend":
        return _analyze_rejection_trend(target_agent, time_window, ecosystem)
    # ... etc
```

### 9.3 Proposed SQL Views for Analyzer

```sql
-- View: Confidence calibration by ecosystem
CREATE VIEW v_confidence_calibration AS
SELECT
    ecosystem,
    DATE_TRUNC('week', created_at) as week,
    COUNT(*) as extraction_count,
    AVG(confidence_score) as avg_claimed_confidence,
    AVG(CASE WHEN status = 'accepted' THEN 1.0 ELSE 0.0 END) as actual_acceptance_rate,
    AVG(confidence_score) - AVG(CASE WHEN status = 'accepted' THEN 1.0 ELSE 0.0 END) as calibration_error
FROM staging_extractions
WHERE status IN ('accepted', 'rejected')
GROUP BY ecosystem, DATE_TRUNC('week', created_at);

-- View: Rejection trend over time
CREATE VIEW v_rejection_trend AS
SELECT
    DATE_TRUNC('week', created_at) as week,
    COUNT(*) as total_decisions,
    SUM(CASE WHEN action_type = 'reject' THEN 1 ELSE 0 END) as rejections,
    AVG(CASE WHEN action_type = 'reject' THEN 1.0 ELSE 0.0 END) as rejection_rate
FROM validation_decisions
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY week;

-- View: Lineage failure rate by evidence type
CREATE VIEW v_lineage_failures AS
SELECT
    candidate_type,
    COUNT(*) as total_extractions,
    SUM(CASE WHEN lineage_verified = FALSE THEN 1 ELSE 0 END) as lineage_failures,
    AVG(CASE WHEN lineage_verified = FALSE THEN 1.0 ELSE 0.0 END) as failure_rate
FROM staging_extractions
WHERE lineage_verified IS NOT NULL
GROUP BY candidate_type;
```

### 9.4 Migration 017 Summary

**Tables:**
- `agent_capabilities` — 12 columns, tracks trust per capability
- `agent_proposals` — 20 columns, tracks individual proposals
- `agent_trust_history` — 7 columns, audit trail

**Triggers:**
- `update_agent_trust_on_review()` — Adjusts trust when proposal reviewed
- `update_agent_trust_on_measurement()` — Adjusts trust when impact measured
- `check_auto_approve()` — Auto-approves if trust above threshold

**Seeded Capabilities:**
- extractor: prompt_update, threshold_change, method_improvement
- validator: prompt_update, validation_rule
- improvement_analyzer: prompt_update, ontology_expansion

---

## References

### Internal Documentation
- `.deepagents/DEEP_AGENTS_ANALYSIS.md` — Initial comparison analysis
- `.deepagents/IMPLEMENTATION_ROADMAP.md` — Current development roadmap
- `.deepagents/AGENT_CONTRACTS.md` — Agent communication contracts
- `.deepagents/INTEGRATION_ARCHITECTURE.md` — FRAMES + MBSE integration
- `docs/diagrams/agent-self-improvement.md` — Trust calibration diagrams
- `docs/architecture/AGENTIC_ARCHITECTURE.md` — System architecture

### External References
- `.deepagents_fromscratch/` — LangChain deep agents tutorial (cloned)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [PROVES Kit](https://docs.proveskit.space/)
- [F´ (F Prime)](https://nasa.github.io/fprime/)

---

## Document History

| Date | Change |
|------|--------|
| 2026-01-16 | Initial analysis created |
| 2026-01-16 | Added peer reflection architecture |
| 2026-01-16 | Revised trust calibration assessment |
| 2026-01-16 | Added implementation recommendations |
