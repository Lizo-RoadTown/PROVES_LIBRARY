# PROVES Library

**Knowledge graph extraction pipeline for training Graph Neural Networks on CubeSat system dependencies.**

[![GitHub Pages](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://lizo-roadtown.github.io/PROVES_LIBRARY/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Overview

This repository builds a knowledge graph from technical documentation (F´, PROVES Kit, CubeSat hardware) to train a GraphSAGE neural network for predicting cascade failures in space systems.

**The problem**: Graph Neural Networks need high-quality training data. Missing edges, inconsistent labels, and unverified relationships teach the model wrong patterns.

**Our approach**: Multi-agent extraction pipeline with full lineage tracking, human verification, and a five-attribute edge model that captures conditional dependencies.

### Why GraphSAGE?

GraphSAGE (Graph Sample and Aggregate) learns from both node features and graph structure, making it suitable for predicting how changes propagate through coupled systems (power → thermal → timing → software).

We're using NASA's heterogeneous GNN implementation as a foundation, initially focused on CubeSat systems with potential application to other technical domains with verifiable dependency graphs.

---

## What We've Built

A multi-agent extraction pipeline that:

1. **Crawls documentation** - Identifies high-quality technical pages (find_good_urls.py)
2. **Extracts structure** - LLM agents identify components, interfaces, flows using FRAMES ontology (process_extractions.py)
3. **Validates lineage** - Tracks every extraction back to source with evidence checksums
4. **Routes for review** - Staged extractions go to human verification via project management integration
5. **Analyzes patterns** - Meta-learning loop identifies extraction quality issues (improvement_analyzer.py)

**What makes this different from standard knowledge graphs**: Five-attribute edges (directionality, strength, mechanism, knownness, scope) that let the GNN learn conditional relationships, not just binary connections.

### Current Phase: Graph Embedding Pipeline

We're currently in the **chunking and embedding phase** - preparing the knowledge graph for neural network training:

```mermaid
graph LR
    A[Documentation Sources] --> B[Smart Crawler]
    B --> C[LLM Extraction Agent]
    C --> D[Validation & Staging]
    D --> E[Human Verification]
    E --> F[Knowledge Graph]
    F --> G[Graph Chunking]
    G --> H[Vector Embeddings]
    H --> I[GNN Training Data]
    I --> J[GraphSAGE Model]

    style F fill:#4D96FF
    style J fill:#FFD93D
```

---

### 🎯 Current Work: Representation Before Interpretation

**Inference is intentionally deferred until after knowledge has been represented without interpretation.** This separation enables an embodiment-aware chunking strategy, where chunks are formed based on observed structural boundaries and relationships rather than inferred meaning or semantic similarity.

This design ensures that chunking reflects **how the system is described**, not how it is prematurely understood. Inference and meaning-making are introduced only after stable representation is established.

#### The Inference-Embodiment Boundary

**Inference** refers to knowledge that is already expressible symbolically (text, equations, specifications) and can be directly operated on by an AI system. All AI reasoning occurs in this space.

**Embodiment** refers to knowledge that exists through physical interaction, practice, intuition, or lived experience, and is not natively symbolic. For humans, many domains are primarily embodied rather than inferential.

**Domains differ in where the inference–embodiment boundary lies:**

- Domains that are already largely inferential (software APIs, protocol specs) are straightforward to extract and chunk
- Domains that are highly embodied (brownout behavior under load, thermal coupling in vacuum) make **extraction the primary challenge**, not chunking

**This pipeline treats chunking as a boundary operation**: domain knowledge remains purely inferential up to chunk formation. A central open problem we're addressing is whether embodied knowledge can be extracted in a way that preserves meaning while remaining universally translatable—what we call **embodied inference**.

---

The agents autonomously:
- Find documentation pages (production/scripts/find_good_urls.py)
- Extract dependency candidates (production/scripts/process_extractions.py)
- Flag quality issues and suggest improvements (production/scripts/improvement_analyzer.py)
- Sync to Notion for human truth establishment
- Build verified graph nodes and edges with full lineage

---

## How It Works: Agent → Graph → Neural Network

### 1. Intelligent Source Discovery

```bash
python production/scripts/find_good_urls.py --fprime --proveskit --max-pages 50
```

Smart crawler analyzes documentation quality, finds high-signal pages, queues for extraction.

### 2. Autonomous Extraction

```bash
python production/scripts/process_extractions.py --limit 10
```

Multi-agent system (Extractor → Validator → Storage) extracts:
- **Components**: Discrete modules (drivers, sensors, boards)
- **Interfaces**: Connection points (I2C bus, SPI, power rails)
- **Flows**: What moves through interfaces (data, power, commands, heat)
- **Mechanisms**: What maintains connections (protocols, documentation, tests)

**NOT** "Component A depends on Component B" (too vague)
**YES** "RadioTX CONSUMES PowerRail_3V3 via electrical mechanism, sometimes (during TX), knownness: verified"

### 3. Human Truth Layer

Extracted candidates appear in Notion for human review:
- Agents provide rich context and confidence scores
- Humans verify evidence and align across conflicting sources
- Only human-verified data enters the truth graph

**Why this matters**: The GNN learns from verified physics, not agent guesses.

### 4. Meta-Learning Improvement

```bash
python production/scripts/improvement_analyzer.py
```

System analyzes extraction patterns:
- Which sources yield high-quality data?
- What extraction patterns lead to validation failures?
- How can ontology adapt to graph structure?
- What methodology improvements would increase accuracy?

**The agent is training itself** to become better at preparing GNN training data.

### 5. Graph Embedding (Current Phase)

The verified knowledge graph gets:
- **Chunked**: Into trainable subgraphs
- **Embedded**: Node and edge features vectorized
- **Indexed**: In pgvector database for efficient retrieval
- **Fed**: To GraphSAGE model for training

---

## Why Data Quality Defines GNN Success

| Bad Data In | Bad Predictions Out |
|-------------|---------------------|
| Missing edges | Model can't learn cascade paths |
| Inconsistent labels | Signal drowns in noise |
| No lineage | Impossible to debug failures |
| Unverified "facts" | Model learns hallucinations |

| Verified Data In | Reliable Predictions Out |
|------------------|--------------------------|
| Complete subgraphs | Model learns full cascade chains |
| Consistent ontology | Clear training signal |
| Full provenance | Debuggable, improvable |
| Human-verified truth | Model learns real physics |

**Our obsession**: Lineage, verification, provenance. Every graph edge traces to source code, documentation, or test results.



## Quickstart

### Prerequisites

```bash
# Python 3.11+
python --version

# PostgreSQL (Neon cloud database)
# Anthropic API key (Claude Sonnet for extraction)
# Notion API key (human verification interface)
```

### Setup

```bash
# Clone repository
git clone https://github.com/Lizo-RoadTown/PROVES_LIBRARY.git
cd PROVES_LIBRARY

# Install dependencies
pip install -r production/pyproject.toml

# Configure environment (copy .env.template to .env)
cp .env.template .env
# Add: NEON_DATABASE_URL, ANTHROPIC_API_KEY, NOTION_API_KEY, LANGCHAIN_API_KEY
```

### Run the Pipeline

```bash
# 1. Find high-quality documentation pages
python production/scripts/find_good_urls.py 

# 2. Extract dependency candidates (runs autonomous agent)
python production/scripts/process_extractions.py 

# 3. Review extractions in Notion (human verification step)
# Visit your Notion workspace → PROVES Library databases

# 4. Analyze extraction quality and improve
python production/scripts/improvement_analyzer.py
```

---

## Current Status & Results

### Phase 1: Foundation ✅ Complete

- Multi-agent curator system operational
- Smart web crawler finding quality sources
- Lineage tracking and evidence verification
- Human-in-the-loop via Project Management integration
- Meta-learning improvement analyzer
- Error logging and quality monitoring

**Results**:
- 45+ verified dependencies extracted from CubeSat documentation
- 4 critical cross-system gaps discovered
- 23 high-quality pages queued for extraction
- Agent methodology improving through meta-learning

### Phase 2: Graph Embedding 🚧 In Progress

- Chunking verified graph into training subgraphs
- Embedding node/edge features with vector models
- pgvector integration for efficient retrieval
- Preparing training data for GraphSAGE model

### Phase 3: GNN Training 📋 Planned

- GraphSAGE model implementation (see [Proves_AI repo](https://github.com/Lizo-RoadTown/Proves_AI))
- Cascade risk prediction
- Hidden coupling detection
- Multi-domain generalization

---

## Design Principles

From [canon/CANON.md](canon/CANON.md):

### 1. Human Verification Layer

Agents extract and categorize, but humans establish truth. This separation ensures the knowledge graph reflects verified physics, not LLM hallucinations.

### 2. Truth Layer Architecture

> "Agents provide context. Humans establish truth."

```
Raw Sources → Agent Capture → Agent Staging → Human Verification → Truth Graph
     ↑              ↑               ↑                ↑
  (all data)   (categorize)    (flag/context)   (align/verify)
```

### 3. FRAMES Ontology (Foundational)

Based on "FRAMES: A Structural Diagnostic for Resilience in Modular University Space Programs" (Osborn, 2025):

- **Components**: Discrete modules (what exists)
- **Interfaces**: Connection points (where they touch)
- **Flows**: What moves through interfaces (data, power, heat, signals)
- **Mechanisms**: What maintains connections (protocols, docs, processes)
- **Coupling**: Strength of bonds (measured via graph edge attributes)

**The fundamental question**: "What MOVES through this system, and through which interfaces?"

NOT: "What depends on what?" (human judgment assigns criticality AFTER understanding structure)

### 4. Five-Attribute Edge Model

Every relationship has:
1. **Directionality**: Does it flow both ways?
2. **Strength**: Always, sometimes, never?
3. **Mechanism**: Electrical, thermal, timing, protocol, software state?
4. **Knownness**: Known (verified), assumed, unknown, disproved?
5. **Scope**: Version tuple, hardware revision, mission profile?

This granularity lets the GNN learn **conditional dependencies** and **mode-specific behavior**.

---

## Who This Is For

- CubeSat teams working with F´, PROVES Kit, or similar modular systems
- Systems engineers analyzing cascade failures and cross-layer dependencies
- ML researchers who need graph datasets with provenance and ground truth
- Students in space systems programs learning how components interact

**Potential applications beyond CubeSat**: The extraction pipeline and five-attribute edge model could work for other domains with technical documentation and verifiable dependencies (manufacturing, infrastructure, software systems). Currently focused on space systems.

---

## Documentation

- [Architecture](docs/architecture/AGENTIC_ARCHITECTURE.md) - Full system design
- [Knowledge Graph Schema](docs/architecture/KNOWLEDGE_GRAPH_SCHEMA.md) - ERV relationship model
- [CANON](canon/CANON.md) - Permanent design principles
- [Production README](production/README.md) - How to run the curator
- [Notion Integration](production/docs/NOTION_INTEGRATION_GUIDE.md) - Human verification setup

### Visualizations

- [Dependency Overview](docs/diagrams/overview.md)
- [Cross-System Dependencies](docs/diagrams/cross-system.md)
- [Knowledge Gaps](docs/diagrams/knowledge-gaps.md)
- [Team Boundaries](docs/diagrams/team-boundaries.md)
- [Transitive Chains](docs/diagrams/transitive-chains.md)

---

## Related Projects

- **[Proves_AI](https://github.com/Lizo-RoadTown/Proves_AI)**: GraphSAGE GNN implementation for mission outcome prediction
- **[PROVES Kit](https://docs.proveskit.space/)**: Open-source CubeSat development framework (primary data source)
- **[F´ (F Prime)](https://nasa.github.io/fprime/)**: NASA's flight software framework (secondary data source)

---

## Contributing

This is active research. Contributions welcome in:

- **New data sources**: Identify high-quality technical documentation for extraction
- **Ontology refinement**: Improve FRAMES categorization for your domain
- **GNN architecture**: Enhance GraphSAGE model for cascade prediction
- **Validation tools**: Better lineage verification and quality checks

See [Issues](https://github.com/Lizo-RoadTown/PROVES_LIBRARY/issues) for current work.

---

## Research Foundation

**FRAMES Methodology**:
Osborn, E. (2025). "FRAMES: A Structural Diagnostic for Resilience in Modular University Space Programs."

**GraphSAGE Foundation**:
Hamilton, W., Ying, Z., & Leskovec, J. (2017). "Inductive Representation Learning on Large Graphs." NeurIPS.

**NASA GNN Implementation**:
Mehrabian, A. (2025). nasa-eosdis-heterogeneous-gnn (Revision 7e71e62). Hugging Face. [Model Repository](https://huggingface.co/arminmehrabian/nasa-eosdis-heterogeneous-gnn) DOI: 10.57967/hf/6789

**PROVES Kit Framework**:
Pham, M. & Bronco Space Lab. (2025). PROVES Kit - Open-Source CubeSat Development Framework. California State Polytechnic University, Pomona. [Documentation](https://docs.proveskit.space/en/latest/)

**Application Domain**:
CubeSat systems, F´ framework, PROVES Kit hardware stack.

**Key Contributions**:

- Five-attribute edge model for conditional dependencies
- Inference-embodiment boundary framework for chunking strategy
- Full lineage tracking from graph edges to source documentation

---

## License

MIT License - see [LICENSE](LICENSE)

---

## Contact

**Elizabeth Osborn**
eosborn@cpp.edu
California State Polytechnic University, Pomona

---
