---
layout: article
title: PROVES Library
key: page-home
---

# PROVES Library

**The central knowledge library for PROVES Kit CubeSat development.**

---

## What It Is

PROVES Library is the knowledge base for [PROVES Kit](https://docs.proveskit.space/)—the open-source CubeSat development framework built on NASA JPL's [F´ (F Prime)](https://nasa.github.io/fprime/).

Components, dependencies, interfaces, and design decisions—all in one place.

---

## FRAMES AI by Bronco Space Lab

FRAMES AI is the agentic intelligence system that powers this library.

<div class="card-grid card-grid-3">
  <div class="card">
    <h3>Agentic Extraction</h3>
    <p>AI agents crawl documentation and extract knowledge automatically.</p>
    <span class="badge">✅ Production</span>
  </div>
  <div class="card">
    <h3>Curation Dashboard</h3>
    <p>Web UI for teams to review, claim, and approve extractions.</p>
    <span class="badge">✅ Production</span>
  </div>
  <div class="card">
    <h3>MCP Server</h3>
    <p>Query the library in natural language.</p>
    <span class="badge">⚠️ Testing</span>
  </div>
  <div class="card">
    <h3>Graph Neural Network</h3>
    <p>Predict cascade failures and detect hidden dependencies.</p>
    <span class="badge">🚧 In Progress</span>
  </div>
  <div class="card">
    <h3>MBSE Export</h3>
    <p>Export to SysML, XTCE, PyTorch Geometric.</p>
    <span class="badge">🚧 In Progress</span>
  </div>
  <div class="card">
    <h3>Multi-Team Support</h3>
    <p>Row-level security for university collaboration.</p>
    <span class="badge">✅ Production</span>
  </div>
</div>

---

## How It Works

```mermaid
flowchart LR
    DOCS[Docs] --> AGENTS[FRAMES AI Agents]
    AGENTS --> REVIEW[Human Review]
    REVIEW --> LIB[PROVES Library]
    LIB --> QUERY[Queries]

    style DOCS fill:#bbdefb
    style AGENTS fill:#ffe0b2
    style REVIEW fill:#ffb74d
    style LIB fill:#a5d6a7
    style QUERY fill:#f8bbd9
```

1. **Agents extract** components and dependencies from PROVES Kit and F´ docs
2. **Engineers verify** in the curation dashboard
3. **Knowledge enters** the PROVES Library
4. **Teams query** via MCP or export to engineering tools

[View Full Architecture Diagram](diagrams/frames-ai-overview.html)

---

## Current Stats

| Metric | Value |
|--------|-------|
| Extractions | 74 |
| Components | 29 |
| Dependencies | 30 |
| Pipeline Reliability | 100% |
| Domain Model Tests | 111 passing |

---

## Get Started

- [**Setup Guide**](../SETUP_GUIDE.html) - Install and configure
- [**Curation Dashboard**](../curation_dashboard/) - Review extractions
- [**MCP Integration**](../mcp-server/docs/MCP_INTEGRATION.html) - Query interface

---

## Documentation

- [Architecture](architecture/AGENTIC_ARCHITECTURE.html) - How FRAMES AI is built
- [Knowledge Framework](../canon/KNOWLEDGE_FRAMEWORK.html) - The theory behind FRAMES
- [Knowledge Graph Schema](architecture/KNOWLEDGE_GRAPH_SCHEMA.html) - Data model

---

## Related Projects

- [PROVES Kit](https://docs.proveskit.space/) - Open-source CubeSat framework
- [F´ (F Prime)](https://nasa.github.io/fprime/) - NASA JPL flight software
- [Proves_AI](https://github.com/Lizo-RoadTown/Proves_AI) - Graph neural network training
