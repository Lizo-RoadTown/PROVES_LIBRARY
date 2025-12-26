# PROVES Library

**A provably-correct knowledge graph construction pipeline for integrating fragmented systems**

[![GitHub Pages](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://lizo-roadtown.github.io/PROVES_LIBRARY/)
[![LangSmith](https://img.shields.io/badge/tracing-LangSmith-orange)](https://smith.langchain.com)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## The Meta-Problem

Modern systems are built from fragmented knowledge across incompatible sources:
- **Documentation lives everywhere** - wikis, PDFs, READMEs, Slack, tribal knowledge
- **Systems don't compose** - different assumptions, units, naming conventions, versions
- **Dependencies are hidden** - changes cascade unpredictably, failures emerge from interactions
- **Risk is invisible** - you can't assess what you can't model

This isn't just a CubeSat problem. It's a **knowledge integration problem** that affects:
- **Enterprise systems** - Siloed documentation, undocumented APIs, orphaned code
- **Supply chains** - Fragmented vendor data, hidden dependencies, cascading failures
- **Medical knowledge** - Multiple databases, incompatible ontologies, missing links
- **Scientific research** - Literature across disciplines, incompatible methodologies
- **Software ecosystems** - Transitive dependencies, version conflicts, breaking changes

**The challenge:** How do you take unstructured, fragmented knowledge and build a composable, provably-correct knowledge graph that reveals hidden relationships and enables risk assessment?

---

## Theoretical Foundation: Nearly Decomposable Systems

Our approach is grounded in **Herbert Simon's theory of nearly decomposable systems** - complex systems that can be analyzed as subsystems with specific interaction patterns.

### Three-Layer Dependency Model

We track dependencies across three layers simultaneously:

1. **Digital Layer** - Code, APIs, protocols, data flows
   - Example: "I2C driver function calls power management API"

2. **Organizational Layer** - Teams, processes, documentation, knowledge transfer
   - Example: "Team A's code changes require Team B's review due to shared I2C bus"

3. **Physical Layer** - Hardware, sensors, actuators, physical constraints
   - Example: "MSP430 GPIO pin physically connected to RP2350 wake signal"

### Rich Dependency Types

Rather than simple "A depends on B", we capture:

- **Interfaces** - How subsystems communicate (API calls, message passing, shared state)
- **Couplings** - Strength and type of interaction (tight/loose, synchronous/asynchronous)
- **Bonds** - Dependencies that hold the system together (power, timing, data flow)

Each dependency is characterized by:
- **Type** - depends_on, enables, conflicts_with, mitigates, causes
- **Layer** - digital, organizational, physical
- **Strength** - tight coupling (failure cascades) vs loose coupling (isolated failures)
- **Direction** - unidirectional, bidirectional, cyclic

### Why This Matters

**Nearly decomposable systems theory** explains why hidden dependencies cause failures:
- Systems appear independent (subsystems are "nearly" decomposable)
- But they interact through subtle cross-layer dependencies
- Changes in one subsystem cascade unpredictably to others
- Traditional documentation captures only obvious dependencies within one layer

**Our solution:** Build a multi-layer dependency graph that reveals the hidden coupling structure, enabling:
- **Risk assessment** - Predict failure cascades from proposed changes
- **Impact analysis** - Identify all affected subsystems across layers
- **Optimization** - Reduce tight coupling, strengthen critical bonds
- **GNN training** - Learn patterns in how dependencies cause failures

This transforms the dependency graph from a static knowledge base into a **predictive model** of system behavior.

---

## Our Solution: Truth Layer Architecture

We've built a **knowledge graph construction pipeline** with three innovations:

### 1. Cryptographic Lineage Tracking
Every extracted entity is provably traceable to its source with:
- **UUID chains** - snapshot_id → extraction_id → entity_id
- **SHA256 checksums** - Evidence integrity verification
- **Byte offset tracking** - Exact source location in original document
- **Lineage confidence scoring** - 0.0 to 1.0 confidence that extraction is traceable

**Result:** Mathematical certainty that knowledge came from documented sources, not hallucination.

### 2. Forward-Looking Relationship Extraction
We capture relationships **before** all entities exist:
- **Staging relationships** - "Component A depends on Component B" stored even if B isn't extracted yet
- **Auto-resolution** - When B is later extracted, relationship automatically links
- **Text-to-ID matching** - Fuzzy matching between text references and entity keys
- **Prepares for GNN** - Graph neural network for risk modeling

**Result:** Build a complete dependency graph even from incomplete knowledge.

### 3. Human-in-the-Loop Truth Layer
Progressive refinement with human verification:
```
Raw Sources → AI Extraction → Validation → Human Review → Truth Graph
```

- **Capture ALL** - LLM agents extract entities, interfaces, flows, mechanisms (FRAMES methodology)
- **Validate lineage** - Verify every extraction traces to source
- **Human gate** - Nothing enters truth graph without human approval
- **Continuous improvement** - Curator observes patterns, suggests optimizations

**Result:** AI speed with human correctness - agents learn from every decision.

---

## Architecture Overview

```mermaid
flowchart TB
  subgraph Sources["Fragmented Sources"]
    A1[Documentation]
    A2[Code Repos]
    A3[Issue Trackers]
    A4[Datasheets]
  end

  subgraph Pipeline["Knowledge Integration Pipeline"]
    B[Extractor Agent<br/>LLM-powered entity extraction]
    C[Validator Agent<br/>Lineage verification]
    D[Storage Agent<br/>Relationship resolution]
    E[Curator<br/>Oversight & optimization]
  end

  subgraph Review["Human Verification (Notion)"]
    F[Extraction Review<br/>Approve/reject entities]
    G[Error Log<br/>Pattern analysis]
    H[Curator Observations<br/>Optimization suggestions]
  end

  subgraph Truth["Truth Layer"]
    I[Core Entities<br/>Verified knowledge]
    J[Relationships<br/>Dependency graph]
    K[Lineage Metadata<br/>Provenance tracking]
  end

  subgraph Future["Future Capabilities"]
    L[Graph Neural Network<br/>Risk prediction]
    M[Multi-domain Composition<br/>Cross-system analysis]
  end

  Sources --> B
  B --> C
  C --> D
  D --> F
  E --> G
  E --> H
  F -->|Approved| I
  I --> J
  J --> K
  K --> L
  J --> M

  style Sources fill:#ffebee
  style Pipeline fill:#e3f2fd
  style Review fill:#fff3e0
  style Truth fill:#e8f5e9
  style Future fill:#f3e5f5
```

---

## What We've Built

### Phase 1: Lineage Tracking System ✅
**Problem:** LLMs hallucinate. How do you trust extracted knowledge?

**Solution:** Cryptographic verification chain
- SHA256 checksums for evidence integrity
- Byte offset tracking for exact source location
- 5-level verification (extraction exists → snapshot linked → evidence found → checksums match → lineage verified)
- Confidence scoring (0.0-1.0) - honest assessment of traceability

**Implementation:**
- Database migration adding 14 lineage columns ([migrations/001_add_lineage_and_relationships.sql](curator-agent/migrations/001_add_lineage_and_relationships.sql))
- Retroactive verification of existing data ([retroactive_verify_lineage.py](curator-agent/retroactive_verify_lineage.py))
- Complete design document ([ID_LINEAGE_SYSTEM.md](curator-agent/ID_LINEAGE_SYSTEM.md))

### Phase 2: Rich Dependency Extraction ✅
**Problem:** Dependencies exist before all entities are extracted. How do you capture them with full context?

**Solution:** Forward-looking relationship staging with multi-layer dependency characterization
- `staging_relationships` table stores relationships with text references
- Captures **interfaces, couplings, and bonds** (nearly decomposable systems framework)
- Tracks **layer** (digital, organizational, physical) and **strength** (tight/loose coupling)
- Auto-resolution trigger matches text to entities when extracted
- Tracks resolution status (unresolved → partially_resolved → resolved)
- Handles ambiguity (multiple possible matches flagged for human review)

**Enables:**
- **Rich dependency graph** - Not just "A depends on B" but type, layer, strength, direction
- **Cross-layer analysis** - Reveal hidden dependencies that span digital/org/physical boundaries
- **GNN preparation** - Training data for predictive models (risk, impact, optimization)
- **Nearly decomposable systems analysis** - Identify tight coupling that causes failure cascades

### Phase 3: Notion Human-in-the-Loop ✅
**Problem:** How do you give humans oversight without slowing down the pipeline?

**Solution:** Three-database Notion integration
1. **Extraction Review** - Human verification of every entity before truth graph
2. **Error Log** - Agent error tracking for pattern analysis (20 properties)
3. **Curator Observations** - Oversight reports on efficiency, cost optimization, limitations

**Curator Workflow:**
- **Daily (5 min):** Check errors, generate metrics summary
- **Weekly (15 min):** Trend analysis, identify optimization opportunities
- **As-needed:** Custom observations (tool gaps, restrictions, optimization opportunities)

---

## Current Application: CubeSat Failure Prevention

We're applying this to prevent CubeSat mission failures (88% failure rate):

**The Problem:**
- University CubeSat programs have fragmented knowledge across teams
- Hidden dependencies cause cascading failures
- Example: Power management change breaks I2C sensors 2 weeks before launch → 6-month delay

**Our Approach:**
1. Extract entities from documentation (components, interfaces, flows, mechanisms)
2. Build dependency graph with lineage tracking
3. Human verification before truth graph
4. Future: GNN predicts failure cascades from proposed changes

**Trial Results:**
- Analyzed F' I2C Driver (411 lines) + PROVES Kit Power Management (154 lines)
- Found **45+ dependencies** with exact line citations
- Discovered **4 critical cross-system dependencies** undocumented in either system
- Identified **5 major knowledge gaps** (timing specs, voltage requirements, error recovery)

**This proves the methodology works.** The next step is scaling it to 60 pages of documentation, then generalizing to other domains.

---

## Why This Matters

### The Generalization Path

**Phase 1 (Current):** CubeSat documentation → Knowledge graph
- Proves: Extraction works, lineage is verifiable, human oversight scales

**Phase 2 (Next):** Multi-ecosystem composition
- Example: Integrate PROVES Kit + F' Prime + custom hardware
- Challenge: Different naming conventions, units, assumptions
- Solution: Entity aliasing + semantic matching + human disambiguation

**Phase 3 (Future):** Cross-domain knowledge integration
- Apply to: Medical databases, supply chains, software ecosystems
- Requirement: Domain-specific extraction prompts, but same pipeline
- Output: Composable knowledge graphs with provable lineage

**Phase 4 (Vision):** Automated risk assessment
- GNN trained on verified relationships
- Predicts: "Changing X will break Y with Z% confidence"
- Human validation: Correct predictions improve model, errors get flagged

---

## Installation

### Requirements

**Python 3.11+**

**Core Dependencies:**
- **LangGraph & LangChain** - Agentic pipeline orchestration
- **Anthropic Claude** - LLM extraction and validation
- **PostgreSQL (Neon)** - Knowledge graph storage
- **pgvector** - Vector embeddings for semantic search
- **Notion API** (optional) - Human review interface

**Key Libraries:**
```bash
# Install all dependencies
pip install -r requirements.txt
```

Main packages installed:
- `langgraph` - Agentic workflow orchestration
- `langchain-anthropic` - Claude integration
- `psycopg[binary,pool]` - PostgreSQL connectivity
- `pgvector` - Vector similarity search
- `sentence-transformers` - Embeddings
- `fastapi` - MCP server
- `tree-sitter` - AST parsing for code analysis
- `langsmith` - Observability and tracing

For detailed setup instructions, see [COMPLETE_NOTION_INTEGRATION.md](curator-agent/COMPLETE_NOTION_INTEGRATION.md).

---

## Technical Highlights

### 1. Deep Agents Pattern (LangGraph)
Sub-agents wrapped as tools for context isolation:

```python
@tool("extractor_agent")
def call_extractor(page_url: str) -> dict:
    """Extract entities from documentation page."""
    # Extractor runs in isolated thread
    # Returns: entities with evidence and confidence
    return extractor.invoke({"url": page_url})
```

**Benefits:**
- Specialized agents (extractor, validator, storage)
- Cost optimization (cheap models for simple tasks)
- Parallel execution where possible

### 2. Lineage Verification Algorithm

```python
def verify_lineage(extraction_id):
    checks_passed = []

    # Check 1: Extraction exists in database
    # Check 2: Snapshot exists and is linked (foreign key)
    # Check 3: Evidence quote exists in snapshot payload (byte-level)
    # Check 4: Evidence checksum matches
    # Check 5: Snapshot checksum valid

    lineage_confidence = len(checks_passed) / total_checks
    return lineage_confidence  # 0.0 to 1.0
```

**Honest assessment:**
- 1.0 = Perfect lineage (all checks pass)
- 0.67 = Partial verification (e.g., retroactive extractions with summaries instead of exact quotes)
- <0.5 = Failed verification (requires re-extraction or mandatory review)

### 3. Forward-Looking Relationships

```sql
CREATE TABLE staging_relationships (
  src_extraction_id UUID,  -- Nullable (might not exist yet)
  src_text_ref TEXT,       -- "MSP430FR Microcontroller"
  dst_extraction_id UUID,  -- Nullable
  dst_text_ref TEXT,       -- "RP2350 Processor"
  rel_type TEXT,           -- "controls", "depends_on", etc.
  resolution_status TEXT   -- 'unresolved', 'partially_resolved', 'resolved'
);

-- Auto-resolution trigger
CREATE TRIGGER auto_resolve
  AFTER INSERT ON staging_extractions
  FOR EACH ROW
  EXECUTE FUNCTION match_text_refs_to_new_entity();
```

**Enables:**
- Capture relationships before all entities extracted
- Build complete dependency graph incrementally
- Handle ambiguity (multiple possible matches → human review)

---

## Metrics & Results

### Current Status (As of December 2025)

| Metric | Value | Notes |
|--------|-------|-------|
| **Pages Processed** | 1 (PROVES Prime) | 60 planned |
| **Extractions Created** | 6 | Components, interfaces, parameters |
| **Lineage Confidence** | 0.67 avg | Retroactive verification (honest assessment) |
| **Database Tables** | 30+ | Including lineage, relationships, aliases |
| **Notion Databases** | 3 | Extraction Review, Error Log, Curator Observations |

### Trial Results (Manual Analysis)

| System | Lines Analyzed | Dependencies Found | Critical Cross-System Deps | Knowledge Gaps |
|--------|----------------|---------------------|---------------------------|----------------|
| F' I2C Driver | 411 | 25+ | 4 | 3 |
| PROVES Power Mgmt | 154 | 20+ | 4 | 2 |
| **Combined** | **565** | **45+** | **4** | **5** |

**Critical Finding:** 4 dependencies existed **only when both systems were considered together** - undocumented in either system individually.

**This is exactly the hidden dependency problem we're solving.**

---

## For Researchers & Builders

### Research Questions We're Exploring

1. **Knowledge Integration:** Can LLMs reliably extract structured knowledge from unstructured technical documentation?
   - **Answer so far:** Yes, with lineage verification and human oversight

2. **Provenance:** Can we achieve cryptographic-level certainty of knowledge origin?
   - **Answer so far:** Yes, SHA256 checksums + byte offsets + UUID chains

3. **Composition:** Can we build relationships before all entities exist?
   - **Answer so far:** Yes, forward-looking relationship staging with auto-resolution

4. **Generalization:** Can this methodology apply to other domains?
   - **Answer so far:** TBD - CubeSat is proving ground, next: multi-ecosystem, then cross-domain

### Why This Is Publishable Research

**Novel Contributions:**
1. **Cryptographic lineage tracking** for LLM-extracted knowledge (SHA256 + byte offsets)
2. **Forward-looking relationship extraction** (capture before entities exist)
3. **Multi-layer dependency modeling** (digital, organizational, physical layers with rich characterization)
4. **Human-in-the-loop at scale** (Notion integration with curator oversight)
5. **Truth layer architecture** (progressive refinement with provable correctness)

**Potential Publications:**
- IEEE Aerospace Conference (CubeSat application)
- ACM Knowledge Management (methodology)
- NeurIPS Workshop (GNN for risk prediction)
- arXiv (complete system description)

---

## Contributing

This is open research. Contributions welcome!

**Ways to contribute:**
1. **Domain expertise:** Help map dependencies in your domain (space, software, medical, etc.)
2. **AI/LLM:** Improve extraction quality, lineage verification, relationship resolution
3. **Graph theory:** Optimize GNN architecture for risk prediction
4. **Documentation:** Improve guides, add tutorials, clarify concepts
5. **Testing:** Run pipeline on your documentation, report issues

**Start here:**
- Report bugs: [GitHub Issues](https://github.com/Lizo-RoadTown/PROVES_LIBRARY/issues)
- Agent development: [curator-agent/README.md](curator-agent/README.md)
- Architecture discussion: [docs/AGENTIC_ARCHITECTURE.md](docs/AGENTIC_ARCHITECTURE.md)

---

## Roadmap

### Complete CubeSat Extraction
- [ ] Process all 60 documentation pages
- [ ] Build complete dependency graph
- [ ] Publish extraction results
- [ ] Validate with CubeSat teams

### Multi-Ecosystem Integration
- [ ] Integrate PROVES Kit + F' Prime + custom hardware
- [ ] Entity aliasing across naming conventions
- [ ] Semantic relationship matching
- [ ] Cross-system dependency analysis

### Graph Neural Network for Predictive Modeling

The rich multi-layer dependency graph becomes training data for multiple types of predictive models.

**Why Rich Dependencies Enable Better Models:**

Traditional dependency graphs store "A depends on B" as a binary edge. Our graph captures:

- **Type** (depends_on, enables, conflicts_with, mitigates, causes)
- **Layer** (digital, organizational, physical)
- **Strength** (tight coupling → failure cascades, loose coupling → isolated failures)
- **Direction** (unidirectional, bidirectional, cyclic)

These become **feature vectors** for the GNN, enabling it to learn:

- *"Tight digital coupling + organizational dependency → 85% cascade probability"*
- *"Physical bond + loose digital coupling → safe to modify"*
- *"Bidirectional dependency + high strength → critical bond, must maintain"*

**Model Types We'll Train:**

1. **Risk Prediction Model**
   - Input: Proposed change to entity X
   - Output: Probability distribution of failure cascades to entities Y, Z, W...
   - Training: Historical failures with known cascades
   - Validation: Predict known incidents, measure precision/recall

2. **Impact Analysis Model**
   - Input: Modified entity + modification type
   - Output: All affected subsystems ranked by impact severity, grouped by layer
   - Training: Change logs + downstream effects
   - Validation: Against documented integration issues

3. **Coupling Optimization Model**
   - Input: Current dependency graph
   - Output: Recommended decoupling actions ranked by risk reduction
   - Training: Successful refactorings that reduced failures
   - Validation: Simulate changes, measure coupling metrics

4. **Cross-Layer Dependency Discovery**
   - Input: Known dependencies in 1-2 layers
   - Output: Predicted hidden dependencies in other layers
   - Training: Complete multi-layer graphs
   - Validation: Against expert-identified dependencies

**GNN Architecture Guided by Nearly Decomposable Systems:**

Herbert Simon's theory suggests:

- Subsystems have **strong internal coupling** (within subsystems)
- Subsystems have **weak cross-coupling** (between subsystems)
- But these weak couplings cause **unexpected cascades**

Our GNN architecture reflects this:

- **Node features:** Entity type, layer memberships, centrality
- **Edge features:** Type, layer, strength, direction (the rich dependency data)
- **Graph attention:** Learn which weak couplings matter most
- **Multi-layer message passing:** Propagate information across digital/org/physical layers
- **Cascade prediction:** Model failure propagation paths through weak cross-couplings

**Architecture Diagram:**

```mermaid
flowchart TB
  subgraph PROVES_LIBRARY["PROVES_LIBRARY (This Repo)"]
    A[Documentation Sources]
    B[Extractor Agent<br/>LLM extraction]
    C[staging_extractions<br/>Entities with lineage]
    D[staging_relationships<br/>Type, Layer, Strength, Direction]
    E[Truth Graph<br/>Verified knowledge]
  end

  subgraph PROVES_AI["PROVES_AI (GNN Stack)"]
    F[Graph Construction<br/>From Neon PostgreSQL]
    G[Feature Engineering<br/>Node: type, layer, centrality<br/>Edge: type, layer, strength, direction]
    H[GraphSAGE GNN<br/>PyTorch Geometric<br/>Multi-layer message passing]
    I[XGBoost Baseline<br/>Mission success probability]
    J[Cross-Encoder Reranker<br/>Semantic risk ranking]
    K[pgvector Retrieval<br/>Similar failure patterns]
  end

  subgraph Output["Risk Assessment Output"]
    L["Risk Prediction<br/>📊 Change Component A:<br/>├─ 85% cascade to B (tight digital)<br/>├─ 60% cascade to C (org dependency)<br/>└─ 15% cascade to D (loose physical)"]
    M["Impact Analysis<br/>🎯 Affected Subsystems:<br/>Digital: 5 components (high severity)<br/>Organizational: 2 teams (medium)<br/>Physical: 1 connection (low)"]
    N["Optimization Recommendations<br/>💡 Decouple A↔B (risk reduction: 40%)<br/>💡 Add redundancy for C (risk reduction: 25%)"]
  end

  A --> B --> C
  B --> D
  C --> E
  D --> E

  E --> F
  F --> G
  G --> H
  G --> I
  K --> J

  H --> L
  H --> M
  I --> L
  J --> M
  H --> N

  style PROVES_LIBRARY fill:#e8f5e9
  style PROVES_AI fill:#e3f2fd
  style Output fill:#fff3e0
  style L fill:#ffebee
  style M fill:#ffebee
  style N fill:#ffebee
```

> **Live Implementation:** The GNN stack is under active development at [Proves_AI](https://github.com/Lizo-RoadTown/Proves_AI)

**Implementation Roadmap:**

- [ ] Build training dataset from verified dependency graph
- [ ] Train GNN on rich dependency features (type, layer, strength, direction)
- [ ] Implement risk prediction model (failure cascade forecasting)
- [ ] Validate predictions against CubeSat historical failures
- [ ] Expand to impact analysis and optimization models
- [ ] Measure precision/recall/F1 for each model type
- [ ] Publish results comparing binary edges vs rich dependencies

**Why This Matters:**

A dependency graph with only "A depends on B" can tell you *what* is connected.

A rich multi-layer dependency graph with type/layer/strength/direction can tell you:

- **Why** they're connected (enables, depends_on, conflicts_with)
- **How tightly** they're coupled (predicts cascade probability)
- **At what level** the coupling exists (digital code? organizational process? physical wire?)
- **What happens if you break it** (tight coupling → cascades, loose → safe)

This transforms the graph from a **static knowledge base** into a **predictive model** of system behavior - exactly what's needed for risk assessment and failure prevention.

### Generalization
- [ ] Apply to second domain (software ecosystem? medical knowledge?)
- [ ] Refine methodology for cross-domain use
- [ ] Publish results
- [ ] Open-source complete pipeline

---

## Links

| Resource | URL |
|----------|-----|
| **Live Documentation** | https://lizo-roadtown.github.io/PROVES_LIBRARY/ |
| **PROVES_AI (GNN Stack)** | https://github.com/Lizo-RoadTown/Proves_AI |
| **Complete Integration Guide** | [curator-agent/COMPLETE_NOTION_INTEGRATION.md](curator-agent/COMPLETE_NOTION_INTEGRATION.md) |
| **Lineage System Design** | [curator-agent/ID_LINEAGE_SYSTEM.md](curator-agent/ID_LINEAGE_SYSTEM.md) |
| **Trial Results** | [trial_docs/COMPREHENSIVE_DEPENDENCY_MAP.md](trial_docs/COMPREHENSIVE_DEPENDENCY_MAP.md) |
| **Architecture Deep Dive** | [docs/AGENTIC_ARCHITECTURE.md](docs/AGENTIC_ARCHITECTURE.md) |

---

## License

MIT License - see [LICENSE](LICENSE)

---

## Contact

**Elizabeth Osborn**
Bronco Space Lab
California State Polytechnic University, Pomona
eosborn@cpp.edu
[Portfolio](https://lizo-roadtown.github.io/proveskit-agent/)

This work is part of a multi-university collaboration involving 9 institutions working to advance CubeSat mission success and knowledge integration methodologies.

---

## Acknowledgments

This project demonstrates a methodology for knowledge integration across fragmented systems:

- **Agentic pipeline built with LangGraph** - Deep agents pattern for specialized extraction, validation, and storage
- **LLM extraction** with cryptographic lineage verification (Anthropic Claude)
- **Multi-layer dependency modeling** grounded in nearly decomposable systems theory
- **Human-in-the-loop truth validation** at scale via Notion integration
- **Forward-looking relationship extraction** enabling composition before complete knowledge

### Inspirations and Related Work

This work draws inspiration from graph neural network research in Earth observation systems:

> Armin Mehrabian. (2025). *nasa-eosdis-heterogeneous-gnn* (Revision 7e71e62). Hugging Face. [https://huggingface.co/arminmehrabian/nasa-eosdis-heterogeneous-gnn](https://huggingface.co/arminmehrabian/nasa-eosdis-heterogeneous-gnn). DOI: [10.57967/hf/6789](https://doi.org/10.57967/hf/6789)

### Contribution

The knowledge graph is the foundation. The real contribution is demonstrating that we can integrate fragmented knowledge at scale with provable correctness, revealing hidden dependencies that cause system failures.

This methodology is generalizable beyond CubeSats to any domain facing knowledge fragmentation: enterprise systems, supply chains, medical knowledge, or scientific research.
