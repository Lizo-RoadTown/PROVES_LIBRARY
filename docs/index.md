---
layout: article
title: PROVES Library
key: page-home
---

# PROVES Library: Agentic Knowledge for CubeSat Mission Safety

**Automated dependency capture + knowledge graph + human review** to prevent
cross-team failures when critical knowledge disappears.

---

## dY>y At a Glance

<div class="card-grid card-grid-3">
  <div class="card">
    <h3>Capture</h3>
    <p>Extract dependencies with citations from docs, code, and issues.</p>
  </div>
  <div class="card">
    <h3>Validate</h3>
    <p>Normalize into ERV relationships and check duplicates.</p>
  </div>
  <div class="card">
    <h3>Review</h3>
    <p>Gate mission-critical items for human approval.</p>
  </div>
  <div class="card">
    <h3>Store</h3>
    <p>Write entries to a structured knowledge graph.</p>
  </div>
  <div class="card">
    <h3>Visualize</h3>
    <p>Render diagrams and trace transitive chains.</p>
  </div>
  <div class="card">
    <h3>Learn</h3>
    <p>Use feedback to improve prompts and patterns.</p>
  </div>
</div>

---

## dY?-‹,? Agentic AI Structure

```mermaid
%%{init: {'flowchart': {'defaultRenderer': 'elk'}}}%%
flowchart TB
  subgraph Sources
    A1[F Prime docs]
    A2[PROVES Kit docs]
    A3[Issues and PRs]
  end

  subgraph Ingestion
    B1[Doc sync]
    B2[Normalization]
  end

  subgraph Agents
    C1[Curator agent]
    C2[Extractor]
    C3[Validator]
    C4[Storage]
    C5[Human review]
  end

  subgraph Knowledge Base
    D1[Library entries]
    D2[Knowledge graph]
    D3[ERV relationships]
  end

  subgraph Outputs
    E1[GitHub Pages diagrams]
    E2[Queries and analysis]
    E3[Risk scanner]
  end

  A1 --> B1
  A2 --> B1
  A3 --> B1
  B1 --> B2
  B2 --> C1
  C1 --> C2
  C2 --> C3
  C3 -->|low/medium| C4
  C3 -->|high/conflict| C5
  C5 -->|approve| C4
  C5 -->|reject| C1
  C4 --> D1
  C4 --> D2
  D2 --> D3
  D1 --> E1
  D2 --> E2
  D2 --> E3
```

---

## dY` Lifecycle: Curation Run

```mermaid
sequenceDiagram
  participant Doc as Documentation
  participant Curator
  participant Extractor
  participant Validator
  participant Review as Human Review
  participant Storage
  participant Graph as Knowledge Graph

  Doc->>Curator: Ingest source
  Curator->>Extractor: Capture ALL dependencies + citations
  Extractor-->>Curator: Raw data with context
  Curator->>Validator: Flag anomalies, check patterns
  Validator-->>Curator: Staged with flags/notes
  Curator->>Staging: Store ALL to staging tables
  Staging-->>Review: Human verifies EVERY piece
  Review-->>Graph: Only verified data enters truth
  Graph->>Graph: Align sources, establish truth
  Graph-->>Storage: Ack
  Storage-->>Curator: Stored summary
```

---

## dY"S Trial Results (What We Found)

- **45+ dependencies** with citations across FA' + PROVES Kit docs
- **4 cross-system dependencies** not documented in either system
- **2 transitive dependency chains** traced end-to-end
- **5 knowledge gaps** that explain mission failures

---

## dY"S Interactive Diagrams

- [Dependency Overview](diagrams/overview.html)
- [Cross-System Dependencies](diagrams/cross-system.html)
- [Transitive Dependency Chains](diagrams/transitive-chains.html)
- [Knowledge Gaps](diagrams/knowledge-gaps.html)
- [Team Boundaries](diagrams/team-boundaries.html)

---

## dY"- What This Enables

- Detect risky changes before they cascade across subsystems.
- Preserve the "why" behind technical decisions.
- Enable cross-team learning without tribal knowledge loss.

---

## Documentation

- [Trial Mapping Design Document](TRIAL_MAPPING_DESIGN.html)
- [Comprehensive Dependency Map](../trial_docs/COMPREHENSIVE_DEPENDENCY_MAP.html)
- [Original FA' Documentation](../trial_docs/fprime_i2c_driver_full.html)
- [Original PROVES Kit Documentation](../trial_docs/proves_power_full.html)
