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
%%{init: {'flowchart': {'defaultRenderer': 'elk'}, 'theme':'base', 'themeVariables': { 'fontFamily': 'Space Mono, monospace', 'lineColor': '#6b8fb3'}}}%%
flowchart TB
    subgraph Molecule["Truth Graph as Molecular Structure"]
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
