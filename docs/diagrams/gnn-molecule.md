---
layout: article
title: GNN Molecular Model
---



# GNN Molecular Model

Think of the truth graph as a molecular structure:
- **Nodes** are atoms (components, teams, documents).
- **Edges** are bonds (dependencies).
- **Bond strength** shows coupling (tight vs loose).
- **Message passing** is like an electron pull that carries influence across bonds.

[Back to Home](../index.html)

---

## Molecular View of the Graph

```mermaid
---
config:
  theme: base
  fontSize: 18
  themeCSS: |
    .nodeLabel { font-size: 18px !important; }
    .edgeLabel { font-size: 16px !important; }
    .edgeLabel rect { stroke: black !important; stroke-width: 1px !important; }
    .node:hover rect, .node:hover circle, .node:hover polygon { stroke-width: 3px !important; filter: drop-shadow(0 0 8px rgba(0,0,0,0.3)); cursor: pointer; }
    .edgePath:hover path { stroke-width: 3px !important; opacity: 1; }
    .edgeLabel:hover rect { stroke-width: 2px !important; filter: brightness(1.1); }
  themeVariables:
    primaryColor: '#E8F5E9'
    secondaryColor: '#FCE4EC'
    tertiaryColor: '#FFF9C4'
    primaryTextColor: '#2E7D32'
    secondaryTextColor: '#C2185B'
    tertiaryTextColor: '#F57F17'
    primaryBorderColor: '#66BB6A'
    secondaryBorderColor: '#F06292'
    tertiaryBorderColor: '#FDD835'
    lineColor: '#4CAF50'
    edgeLabelBackground: '#F1F8E9'
    nodeBorder: '#66BB6A'
    clusterBkg: '#FFF9C4'
    clusterBorder: '#FDD835'
    defaultLinkColor: '#4CAF50'
    titleColor: '#2E7D32'
    actorBkg: '#E8F5E9'
    actorBorder: '#66BB6A'
    actorTextColor: '#2E7D32'
    signalColor: '#4CAF50'
    labelBoxBkgColor: '#FCE4EC'
    stateBkg: '#E8F5E9'
    sectionBkgColor: '#FFF9C4'
    taskBorderColor: '#66BB6A'
    taskBkgColor: '#E8F5E9'
    activeTaskBkgColor: '#C8E6C9'
    gridColor: '#A5D6A7'
    doneTaskBkgColor: '#81C784'
    critBkgColor: '#F06292'
    todayLineColor: '#2E7D32'
    pie1: '#4CAF50'
    pie2: '#F06292'
    pie3: '#FDD835'
    pie4: '#66BB6A'
    pie5: '#E91E63'
    pie6: '#FFEB3B'
    pie7: '#81C784'
    pie8: '#F48FB1'
    pie9: '#FFF176'
    pie10: '#A5D6A7'
    pie11: '#FCE4EC'
    pie12: '#FFF9C4'
  flowchart:
    curve: linear
---
flowchart TB
    subgraph Molecule ["Truth Graph as Molecular Structure"]
        A[Power Manager]
        B[I2C Bus]
        C[IMU Sensor]
        D[Load Switch]
        E[Topology Config]
        F[Team A Docs]
        G[Team B Docs]
    end

    P[Change Pulse]

    A --- B
    B --- C
    A --- D
    D --- C
    E --- A
    F --- E
    G --- E
    B --- G
    P --> A

    classDef atom fill:#f5f9ff,stroke:#4a7fb3,stroke-width:1px,color:#0b1b2b;
    classDef core fill:#ffe7b3,stroke:#c9882a,stroke-width:2px,color:#3a2603;
    classDef doc fill:#e8f7ef,stroke:#3a9d6d,stroke-width:1px,color:#0f2b1f;
    classDef pulse fill:#ffd6d6,stroke:#c44,stroke-width:2px,color:#3a0d0d;

    class A,B,C,D atom;
    class E core;
    class F,G doc;
    class P pulse;

    linkStyle 0 stroke:#4a7fb3,stroke-width:3px;
    linkStyle 1 stroke:#4a7fb3,stroke-width:3px;
    linkStyle 2 stroke:#4a7fb3,stroke-width:3px;
    linkStyle 3 stroke:#4a7fb3,stroke-width:3px;
    linkStyle 4 stroke:#9ab7d6,stroke-width:1px,stroke-dasharray:3 3;
    linkStyle 5 stroke:#9ab7d6,stroke-width:1px,stroke-dasharray:3 3;
    linkStyle 6 stroke:#9ab7d6,stroke-width:1px,stroke-dasharray:3 3;
    linkStyle 7 stroke:#9ab7d6,stroke-width:1px,stroke-dasharray:3 3;
    linkStyle 8 stroke:#c44,stroke-width:2px;
```

**Legend**
- **Thick bonds** = tight coupling (strong pull)
- **Dashed bonds** = loose coupling (weak pull)
- **Change pulse** = a modification that propagates across bonds

---



## Why this helps

A GNN learns which bonds carry the strongest influence. With verified edges and consistent labels, the model learns real system behavior instead of noise.

---

[Back to Home](../index.html)




