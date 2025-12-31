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
    edgeLabelBackground: '#FFF8E1'
    actorBkg: '#FFF3E0'
    actorBorder: '#FF6F00'
    actorTextColor: '#5D4037'
    signalColor: '#FF9800'
    signalTextColor: '#5D4037'
    labelBoxBkgColor: '#F3E5F5'
    noteBkgColor: '#FFF8E1'
    noteTextColor: '#F57F17'
    noteBorderColor: '#FBC02D'
    pie1: '#FF6F00'
    pie2: '#9C27B0'
    pie3: '#FBC02D'
    pie4: '#FF9800'
    pie5: '#BA68C8'
    pie6: '#FFD54F'
    pie7: '#FFB74D'
    pie8: '#CE93D8'
    pie9: '#FFF176'
    pie10: '#FF8A65'
    pie11: '#F3E5F5'
    pie12: '#FFF8E1'
    sectionBkgColor: '#FFF8E1'
    altSectionBkgColor: '#FFF3E0'
    sectionBkgColor2: '#F3E5F5'
    taskBkgColor: '#FFB74D'
    taskBorderColor: '#FF6F00'
    activeTaskBkgColor: '#FF9800'
    activeTaskBorderColor: '#E65100'
    doneTaskBkgColor: '#FFCC80'
    doneTaskBorderColor: '#FF6F00'
    critBkgColor: '#CE93D8'
    critBorderColor: '#7B1FA2'
    taskTextColor: '#5D4037'
    taskTextOutsideColor: '#5D4037'
    taskTextLightColor: '#5D4037'
    taskTextDarkColor: '#FFFFFF'
    gridColor: '#FFCC80'
    todayLineColor: '#7B1FA2'
    classText: '#5D4037'
    fillType0: '#FFF3E0'
    fillType1: '#F3E5F5'
    fillType2: '#FFF8E1'
    fillType3: '#FFB74D'
    fillType4: '#CE93D8'
    fillType5: '#FFD54F'
    fillType6: '#FF8A65'
    fillType7: '#BA68C8'
    attributeBackgroundColorOdd: '#FFF8E1'
    attributeBackgroundColorEven: '#FFF3E0'
  gantt:
    fontSize: 24
    barHeight: 24
    barGap: 6
    topPadding: 50
    leftPadding: 75
    gridLineStartpadding: 40
    numberSectionStyles: 4
  flowchart:
    curve: 'linear'
    htmlLabels: false
    useMaxWidth: true
    padding: 40
    nodeSpacing: 100
    rankSpacing: 150
    diagramPadding: 8
  sequence:
    diagramMarginX: 50
    diagramMarginY: 10
    actorMargin: 50
    boxMargin: 10
    boxTextMargin: 5
    noteMargin: 10
    messageMargin: 35
    mirrorActors: false
    bottomMarginAdj: 1
    useMaxWidth: true
    rightAngles: false
    showSequenceNumbers: false
  state:
    dividerMargin: 10
    sizeUnit: 5
    padding: 8
    textHeight: 10
    titleShift: -15
    noteMargin: 10
    forkWidth: 70
    forkHeight: 7
    miniPadding: 2
    fontSizeFactor: 5.02
    fontSize: 24
    labelHeight: 16
    edgeLengthFactor: 20
    compositeTitleSize: 35
    radius: 5
  class:
    arrowMarkerAbsolute: false
    hideEmptyMembersBox: false
  er:
    diagrampadding: 40
    layoutDirection: 'TB'
    minEntityWidth: 100
    minEntityHeight: 75
    entityPadding: 15
    stroke: 'gray'
    fill: 'honeydew'
    fontSize: 12
  journey:
    diagramMarginX: 50
    diagramMarginY: 10
    actorMargin: 50
    boxMargin: 10
    boxTextMargin: 5
  pie:
    textPosition: 0.75
  quadrant:
    chartWidth: 500
    chartHeight: 500
    titlePadding: 10
    titlefontSize: 24
    quadrantPadding: 5
    quadrantTextTopPadding: 5
    quadrantLabelFontSize: 16
    quadrantInternalBorderStrokeWidth: 1
    quadrantExternalBorderStrokeWidth: 2
    pointTextPadding: 5
    pointLabelFontSize: 12
    pointRadius: 6
    xAxisLabelPadding: 5
    xAxisLabelFontSize: 16
    yAxisLabelPadding: 5
    yAxisLabelFontSize: 16
  requirement:
    rect_fill: '#FFF3E0'
    text_color: '#5D4037'
    rect_border_size: 2
    rect_border_color: '#FF6F00'
    rect_min_width: 200
    rect_min_height: 200
    fontSize: 14
    rect_padding: 10
    line_height: 20
  gitGraph:
    showBranches: true
    showCommitLabel: true
    mainBranchName: 'main'
    rotateCommitLabel: true
  c4:
    diagramMarginX: 50
    diagramMarginY: 10
    c4ShapeMargin: 50
    c4Shapepadding: 40
    width: 216
    height: 60
    boxMargin: 10
---
flowchart TB
    subgraph Molecule ["Truth Graph as Molecular Structure"]
        spacer24[ ]:::spacer
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
    %% Font sizing classes for consistency
    classDef default font-size:24px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef diamond font-size:22px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef spacer fill:none,stroke:none,color:transparent,width:1px,height:1px;
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











