---
layout: article
title: FRAMES AI Overview
---

# FRAMES AI Overview

How FRAMES AI powers the PROVES Library.

[← Back to Home](../index.html)

---

## System Architecture

**What you're looking at:** The complete FRAMES AI system showing how documentation becomes queryable knowledge.

```mermaid
---
config:
  theme: base
  fontSize: 24
  themeVariables:
    primaryColor: '#FFF3E0'
    secondaryColor: '#F3E5F5'
    tertiaryColor: '#FFF8E1'
    primaryTextColor: '#5D4037'
    secondaryTextColor: '#4A148C'
    tertiaryTextColor: '#F57F17'
    primaryBorderColor: '#FF6F00'
    secondaryBorderColor: '#9C27B0'
    tertiaryBorderColor: '#FBC02D'
    background: '#FFF8E1'
    textColor: '#5D4037'
    lineColor: '#FF9800'
    fontFamily: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif'
    fontSize: '24px'
    nodeBorder: '#FF6F00'
    mainBkg: '#FFF3E0'
    clusterBkg: '#F3E5F5'
    clusterBorder: '#9C27B0'
  flowchart:
    curve: 'linear'
    htmlLabels: false
    useMaxWidth: true
    padding: 40
    nodeSpacing: 100
    rankSpacing: 150
---
flowchart TB
    subgraph SOURCES["Documentation Sources"]
        PK[PROVES Kit Docs]
        FP[F Prime Docs]
        GH[GitHub Repos]
    end

    subgraph FRAMES["FRAMES AI"]
        CR[Smart Crawler]
        AG[Extraction Agents]
        DB[(Staging Database)]
        DASH[Curation Dashboard]
        ENG[Engineers]
    end

    subgraph LIBRARY["PROVES Library"]
        KG[(Knowledge Graph)]
        ENT[Verified Entities]
        REL[Dependencies]
    end

    subgraph ACCESS["Query and Export"]
        MCP[MCP Server]
        GNN[Graph Neural Network]
        EXP[MBSE Export]
    end

    PK --> CR
    FP --> CR
    GH --> CR
    CR -->|"finds quality docs"| AG
    AG -->|"extracts knowledge"| DB
    DB -->|"pending review"| DASH
    ENG -->|"verify in dashboard"| DASH
    DASH -->|"approved only"| KG
    KG --> ENT
    KG --> REL
    KG --> MCP
    KG --> GNN
    KG --> EXP

    style SOURCES fill:#e3f2fd
    style FRAMES fill:#fff3e0
    style LIBRARY fill:#e8f5e9
    style ACCESS fill:#fce4ec

    style PK fill:#bbdefb
    style FP fill:#bbdefb
    style GH fill:#bbdefb
    style CR fill:#ffe0b2
    style AG fill:#ffe0b2
    style DB fill:#ffcc80
    style DASH fill:#ffb74d
    style ENG fill:#ff8a65
    style KG fill:#a5d6a7
    style ENT fill:#c8e6c9
    style REL fill:#c8e6c9
    style MCP fill:#f8bbd9
    style GNN fill:#f8bbd9
    style EXP fill:#f8bbd9

    classDef default font-size:20px,font-family:Segoe UI;
```

---

## The Flow

### 1. Sources
Documentation from PROVES Kit, F Prime, and GitHub repositories.

### 2. FRAMES AI
- **Smart Crawler** finds high-quality documentation pages
- **Extraction Agents** identify components, dependencies, and interfaces
- **Staging Database** holds unverified extractions
- **Curation Dashboard** where engineers review and approve

### 3. PROVES Library
- **Knowledge Graph** stores verified entities and relationships
- Only human-approved knowledge enters the library

### 4. Query and Export
- **MCP Server** for natural language queries
- **Graph Neural Network** for cascade prediction
- **MBSE Export** to SysML, XTCE, PyTorch Geometric

---

## Feature Status

```mermaid
---
config:
  theme: base
  themeVariables:
    primaryColor: '#FFF3E0'
    pie1: '#4caf50'
    pie2: '#ff9800'
    pie3: '#2196f3'
  pie:
    textPosition: 0.75
---
pie showData title FRAMES AI Feature Status
    "Production" : 3
    "Testing" : 1
    "In Progress" : 2
```

| Feature | Status |
|---------|--------|
| Agentic Extraction | Production |
| Curation Dashboard | Production |
| Multi-Team Support | Production |
| MCP Server | Testing |
| Graph Neural Network | In Progress |
| MBSE Export | In Progress |

---

## Simple View

For a quick mental model:

```mermaid
---
config:
  theme: base
  themeVariables:
    primaryColor: '#FFF3E0'
    lineColor: '#FF9800'
  flowchart:
    curve: 'linear'
---
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

**Agents extract. Engineers verify. Knowledge stays.**

---

## More Diagrams

- [Agent Self-Improvement](agent-self-improvement.html) — How agents learn and earn autonomy through trust calibration
