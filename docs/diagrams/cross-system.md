---
layout: article
title: Cross-System Dependencies
---



# Cross-System Dependencies

The 4 critical dependencies between F-Prime and PROVES Kit that are **NOT documented** in either system.

This is the exact failure mode from the Team A/Team B scenario.

[← Back to Home](../index.html)

---

## Quick Terminology

**Cross-System Dependency** - When two separate systems (managed by different teams) depend on each other but neither documents the connection

**F-Prime (F Prime)** - NASA's flight software framework (Team A)

**PROVES Kit** - University power management system (Team B)

**I2C** - Communication bus that sensors use to talk to the computer

**Load Switch** - Electronic power switch controlled by software

**Why This Is Dangerous:** If Team B changes power settings without telling Team A, the sensors fail. Neither team knows to coordinate because the dependency isn't documented anywhere.

---



## Critical Finding: Hidden Dependencies

Neither F-Prime documentation nor PROVES Kit documentation mentions the other system. Yet they have critical runtime dependencies that can cause mission failures if misconfigured.

**Translation for Students:** Imagine two groups working on the same car - one builds the engine (F-Prime/Team A), one controls the fuel pump (PROVES/Team B). The engine obviously needs fuel, but if neither group's manual mentions the other, Team B might change the fuel pump timing and break the engine without realizing it.

### Team A / Team B Knowledge Gap

**Real Scenario:**
- **Team B (PROVES Kit):** Changed power management configuration
- **Team B Testing:** Tested locally, everything worked
- **Launch -2 weeks:** Catastrophic failure when integrated
- **Team A (F-Prime):** Knew the answer from "several generations before"
- **Problem:** Knowledge didn't flow across team boundaries

**Our Analysis Found This Exact Pattern:**

---

## Dependency 1: I2C Device -> Power Stability

### The Hidden Dependency

```mermaid
---
config:
  theme: base
  fontSize: 24
  themeCSS: |
    .node rect, .cluster rect, .edgePath path { transition: filter 0.2s ease, stroke-width: 0.2s ease; }
    .node:hover rect, .cluster:hover rect, .edgePath:hover path { filter: drop-shadow(0 0 8px rgba(0,0,0,0.35)); stroke-width: 3px; }
    .edgeLabel rect { rx: 6px; ry: 6px; stroke-width: 1px; }
    .cluster-label { font-weight: 600; }
    .node .label, .nodeLabel, .node foreignObject div, .edgeLabel { font-size: 20px !important; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif !important; }
    .node.decision .label, .node polygon + .label { font-size: 18px !important; }
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
    gridLineStartPadding: 35
    numberSectionStyles: 4
  flowchart:
    curve: 'linear'
    htmlLabels: false
    useMaxWidth: true
    padding: 25
    nodeSpacing: 60
    rankSpacing: 80
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
    diagrampadding: 25
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
    c4Shapepadding: 25
    width: 216
    height: 60
    boxMargin: 10
---
flowchart LR
    subgraph "F-Prime System (NASA/JPL)"
        spacer16[ ]:::spacer
        IM[ImuManager I2C Device Manager]
        I2C[I2C Bus Driver LinuxI2cDriver]
        STATUS[I2cStatus Error Codes]
    end

    subgraph "PROVES Kit (University Teams)"
        spacer17[ ]:::spacer
        LSM[LoadSwitchManager Power Control]
        IMU_PIN[board.IMU_ENABLE GPIO Pin]
        LOGIC[enable_logic Active High/Low]
    end

    subgraph "Hardware"
        spacer18[ ]:::spacer
        IMU_HW[MPU6050 IMU I2C Address 0x68]
        PWR[Power Supply 3.3V]
    end

    IM -->|reads sensor via| I2C
    I2C -->|I2C protocol| IMU_HW
    IMU_HW -->|requires stable| PWR
    PWR -.->|controlled by| LSM
    LSM -->|enables via| IMU_PIN
    LSM -->|configured with| LOGIC

    IM -->|on error returns| STATUS
    STATUS -.->|should trigger?| LSM

    style IM fill:#e1f5ff
    style LSM fill:#fff4e1
    style IMU_HW fill:#ffebee
    style PWR fill:#ffebee

    linkStyle 3 stroke:#f44336,stroke-width:4px,stroke-dasharray: 5 5
    linkStyle 7 stroke:#ff9800,stroke-width:2px,stroke-dasharray: 5 5
    %% Font sizing classes for consistency
    classDef default font-size:24px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef diamond font-size:22px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef spacer fill:none,stroke:none,color:transparent,width:1px,height:1px;
```

**Legend:**
- Solid lines: Documented dependencies
- <span style="color:red">Red dashed line</span>: **UNDOCUMENTED critical dependency**
- <span style="color:orange">Orange dashed line</span>: **MISSING integration**

### Evidence Chain

| System | Line | Evidence |
|--------|------|----------|
| F-Prime | 28 | "ImuManager uses the bus driver layer to implement data read/writes for MPU6050 sensor" |
| F-Prime | 126 | `Drv::I2cStatus status = this->busWriteRead_out(...)` - I2C operations can fail |
| F-Prime | 188-194 | Errors logged but NOT automatically recovered |
| PROVES | 28 | `"imu": DigitalInOut(board.IMU_ENABLE)` - IMU powered by load switch |
| PROVES | 34 | LoadSwitchManager initialization |
| PROVES | 108 | Enable logic configuration (active high/low) |

### The Gap

**What's NOT Documented:**
- Power-on timing requirements before I2C communication
- Voltage stability requirements for I2C bus
- Recovery strategy on I2C error (should power cycle?)
- Effect of enable logic change on I2C operations

**Risk Level:** 🔴 **CRITICAL**

**Failure Scenario:**
```
Team B changes enable_logic from True to False
  ↓
LoadSwitchManager inverts pin logic
  ↓
IMU loses power during F-Prime initialization
  ↓
I2C bus driver fails to open("/dev/i2c-1")
  ↓
F-Prime logs error but doesn't know to check power
  ↓
Mission continues without IMU (silent failure)
```

---



## Dependency 2: Bus Operations -> Power Control Sequence

### Temporal Ordering Requirement

```mermaid
---
config:
  theme: base
  fontSize: 24
  themeCSS: |
    .node rect, .cluster rect, .edgePath path { transition: filter 0.2s ease, stroke-width: 0.2s ease; }
    .node:hover rect, .cluster:hover rect, .edgePath:hover path { filter: drop-shadow(0 0 8px rgba(0,0,0,0.35)); stroke-width: 3px; }
    .edgeLabel rect { rx: 6px; ry: 6px; stroke-width: 1px; }
    .cluster-label { font-weight: 600; }
    .node .label, .nodeLabel, .node foreignObject div, .edgeLabel { font-size: 20px !important; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif !important; }
    .node.decision .label, .node polygon + .label { font-size: 18px !important; }
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
    gridLineStartPadding: 35
    numberSectionStyles: 4
  flowchart:
    curve: 'linear'
    htmlLabels: false
    useMaxWidth: true
    padding: 25
    nodeSpacing: 60
    rankSpacing: 80
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
    diagrampadding: 25
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
    c4Shapepadding: 25
    width: 216
    height: 60
    boxMargin: 10
---
sequenceDiagram
    autonumber
    participant Topology as Topology.cpp configureTopology
    participant LSM as LoadSwitchManager PROVES Kit
    participant Power as Hardware Power Supply
    participant BusDrv as LinuxI2cDriver F Prime
    participant I2C as "I2C Bus /dev/i2c-1"

    Note over Topology: UNDOCUMENTED ORDER

    rect rgb(255, 200, 200)
        Topology->>LSM: turn_on imu
        LSM->>Power: Enable IMU power
        Note over Power: ⏱️ UNDOCUMENTED DELAY
        Power-->>Power: Voltage stabilizes - how long?
    end

    rect rgb(200, 255, 200)
        Topology->>BusDrv: open /dev/i2c-1
        BusDrv->>I2C: Initialize I2C device
        I2C-->>BusDrv: Device ready
        BusDrv-->>Topology: Return I2C_OK
    end

    Note over Topology,I2C: If order reversed initialization fails silently
```

### Evidence Chain

| System | Line | Evidence |
|--------|------|----------|
| PROVES | 34 | `load_switch_manager = LoadSwitchManager(...)` - initialization required |
| F-Prime | 248 | `busDriver.open("/dev/i2c-1")` - happens in configureTopology() |
| F-Prime | 245-254 | configureTopology() example shown |

### The Gap

**What's NOT Documented:**
- Required power-on delay before I2C initialization
- Order of operations in configureTopology()
- Error handling if bus opens before power stabilizes

**Risk Level:** 🔴 **HIGH**

**Failure Scenario:**
```
configureTopology() calls busDriver.open() first
  ↓
I2C device doesn't exist yet (no power)
  ↓
open() fails with I2C_OPEN_ERR
  ↓
F-Prime logs error, continues without IMU
  ↓
No alert that power sequencing is wrong
```

---



## Dependency 3: I2C Address Configuration -> Pin Enable Logic

### Bus Sharing Conflicts

```mermaid
---
config:
  theme: base
  fontSize: 24
  themeCSS: |
    .node rect, .cluster rect, .edgePath path { transition: filter 0.2s ease, stroke-width: 0.2s ease; }
    .node:hover rect, .cluster:hover rect, .edgePath:hover path { filter: drop-shadow(0 0 8px rgba(0,0,0,0.35)); stroke-width: 3px; }
    .edgeLabel rect { rx: 6px; ry: 6px; stroke-width: 1px; }
    .cluster-label { font-weight: 600; }
    .node .label, .nodeLabel, .node foreignObject div, .edgeLabel { font-size: 20px !important; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif !important; }
    .node.decision .label, .node polygon + .label { font-size: 18px !important; }
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
    gridLineStartPadding: 35
    numberSectionStyles: 4
  flowchart:
    curve: 'linear'
    htmlLabels: false
    useMaxWidth: true
    padding: 25
    nodeSpacing: 60
    rankSpacing: 80
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
    diagrampadding: 25
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
    c4Shapepadding: 25
    width: 216
    height: 60
    boxMargin: 10
---
flowchart TB
    subgraph "F-Prime Configuration"
        spacer19[ ]:::spacer
        IM_ADDR[ImuManager Address 0x68]
        BUS["I2C Bus /dev/i2c-1 Shared Resource"]
    end

    subgraph "PROVES Kit Power"
        spacer20[ ]:::spacer
        IMU_SW[IMU Switch board.IMU_ENABLE]
        MAG_SW[Magnetometer Switch board.MAG_ENABLE]
        CAM_SW[Camera Switch board.CAMERA_ENABLE]
    end

    subgraph "Potential Conflicts"
        spacer21[ ]:::spacer
        MAG_HW[Magnetometer I2C Address ???]
        CAM_HW[Camera I2C Address ???]
        IMU_HW[IMU MPU6050 I2C Address 0x68]
    end

    IM_ADDR -.->|unknown if shared| BUS
    BUS -->|communicates with| IMU_HW
    BUS -.->|might communicate with| MAG_HW
    BUS -.->|might communicate with| CAM_HW

    IMU_SW -->|powers| IMU_HW
    MAG_SW -->|powers| MAG_HW
    CAM_SW -->|powers| CAM_HW

    style BUS fill:#ffebee
    style IMU_HW fill:#e8f5e9
    style MAG_HW fill:#fff9c4
    style CAM_HW fill:#fff9c4

    linkStyle 0 stroke:#f44336,stroke-width:3px,stroke-dasharray: 5 5
    linkStyle 2 stroke:#ff9800,stroke-width:2px,stroke-dasharray: 5 5
    linkStyle 3 stroke:#ff9800,stroke-width:2px,stroke-dasharray: 5 5
    %% Font sizing classes for consistency
    classDef default font-size:24px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef diamond font-size:22px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef spacer fill:none,stroke:none,color:transparent,width:1px,height:1px;
```

### Evidence Chain

| System | Line | Evidence |
|--------|------|----------|
| F-Prime | 253 | `imuManager.configure(0x68)` - Fixed I2C address |
| PROVES | 27-30 | Multiple devices: radio, imu, magnetometer, camera |

### The Gap

**What's NOT Documented:**
- Which devices share the I2C bus?
- I2C addresses of other devices (conflict detection)
- Power sequencing to avoid address collisions
- Bus arbitration strategy if multiple devices active

**Risk Level:** 🟡 **MEDIUM**

**Failure Scenario:**
```
Magnetometer and IMU share I2C bus
  ↓
Both powered on simultaneously
  ↓
Address conflict or bus contention
  ↓
I2C read operations corrupt data
  ↓
Attitude determination fails
```

---



## Dependency 4: Error Handling -> Power State Recovery

### Missing Integration

```mermaid
---
config:
  theme: base
  fontSize: 24
  themeCSS: |
    .node rect, .cluster rect, .edgePath path { transition: filter 0.2s ease, stroke-width: 0.2s ease; }
    .node:hover rect, .cluster:hover rect, .edgePath:hover path { filter: drop-shadow(0 0 8px rgba(0,0,0,0.35)); stroke-width: 3px; }
    .edgeLabel rect { rx: 6px; ry: 6px; stroke-width: 1px; }
    .cluster-label { font-weight: 600; }
    .node .label, .nodeLabel, .node foreignObject div, .edgeLabel { font-size: 20px !important; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif !important; }
    .node.decision .label, .node polygon + .label { font-size: 18px !important; }
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
    gridLineStartPadding: 35
    numberSectionStyles: 4
  flowchart:
    curve: 'linear'
    htmlLabels: false
    useMaxWidth: true
    padding: 25
    nodeSpacing: 60
    rankSpacing: 80
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
    diagrampadding: 25
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
    c4Shapepadding: 25
    width: 216
    height: 60
    boxMargin: 10
---
flowchart TB
    START[F-Prime I2C Read Operation]
    READ{I2C Status}:::diamond
    ERROR[I2cStatus I2C_READ_ERR]
    LOG[log_WARNING_HI_ImuReadError]
    CONTINUE[Continue without IMU data]

    MISSING["✗ MISSING Power Cycle Recovery"]
    POWER_OFF[LoadSwitchManager.turn_off]
    DELAY[Wait for power drain]
    POWER_ON[LoadSwitchManager.turn_on]
    RETRY[Retry I2C operation]

    START --> READ
    READ -->|Error| ERROR
    READ -->|OK| CONTINUE
    ERROR --> LOG
    LOG --> CONTINUE

    ERROR -.->|should trigger| MISSING
    MISSING -.-> POWER_OFF
    POWER_OFF -.-> DELAY
    DELAY -.-> POWER_ON
    POWER_ON -.-> RETRY

    style ERROR fill:#ffebee
    style MISSING fill:#f44336,color:#fff
    style CONTINUE fill:#fff9c4

    linkStyle 5,6,7,8,9 stroke:#f44336,stroke-width:3px,stroke-dasharray: 5 5
    %% Font sizing classes for consistency
    classDef default font-size:24px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef diamond font-size:22px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef spacer fill:none,stroke:none,color:transparent,width:1px,height:1px;
```

### Evidence Chain

| System | Line | Evidence |
|--------|------|----------|
| F-Prime | 188-194 | `if (status == Drv::I2cStatus::I2C_OK) { ... } else { log_WARNING_HI_ImuReadError(status); }` |
| F-Prime | No line | NO recovery strategy implemented |
| PROVES | 119-125 | Load switch operations return boolean success |
| PROVES | 131-142 | Methods: turn_on(), turn_off(), get_switch_state() |

### The Gap

**What's NOT Documented:**
- Should I2C errors trigger power cycling?
- What's the recovery sequence?
- How many retries before giving up?
- Does F-Prime have mechanism to request power cycle?

**Risk Level:** 🟡 **MEDIUM**

**Mitigation Opportunity:**
```python
# Potential integration (NOT IMPLEMENTED)
def imu_read_with_recovery(imu_manager, load_switch_manager):
    max_retries = 3
    for attempt in range(max_retries):
        status = imu_manager.read(data)
        if status == I2cStatus.I2C_OK:
            return data

        # Power cycle recovery (MISSING)
        load_switch_manager.turn_off("imu")
        time.sleep(0.5)  # Power drain delay
        load_switch_manager.turn_on("imu")
        time.sleep(0.1)  # Power stabilization delay

    raise ImuReadFailure("Failed after power cycle attempts")
```

> **Why This Matters:** Without documented error recovery, every team will either (1) give up on first error, or (2) invent their own recovery strategy. This leads to inconsistent behavior and missed opportunities for automatic recovery.

---



## Organizational Analysis

### Team Interface Strength

```mermaid
---
config:
  theme: base
  fontSize: 24
  themeCSS: |
    .node rect, .cluster rect, .edgePath path { transition: filter 0.2s ease, stroke-width: 0.2s ease; }
    .node:hover rect, .cluster:hover rect, .edgePath:hover path { filter: drop-shadow(0 0 8px rgba(0,0,0,0.35)); stroke-width: 3px; }
    .edgeLabel rect { rx: 6px; ry: 6px; stroke-width: 1px; }
    .cluster-label { font-weight: 600; }
    .node .label, .nodeLabel, .node foreignObject div, .edgeLabel { font-size: 20px !important; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif !important; }
    .node.decision .label, .node polygon + .label { font-size: 18px !important; }
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
    gridLineStartPadding: 35
    numberSectionStyles: 4
  flowchart:
    curve: 'linear'
    htmlLabels: false
    useMaxWidth: true
    padding: 25
    nodeSpacing: 60
    rankSpacing: 80
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
    diagrampadding: 25
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
    c4Shapepadding: 25
    width: 216
    height: 60
    boxMargin: 10
---
flowchart LR
    subgraph "NASA/JPL Team"
        spacer22[ ]:::spacer
        F_TEAM[F-Prime Core Team]
        F_DOC[Official Docs]
        F_VER[Versioned Releases]
    end

    subgraph "University Teams"
        spacer23[ ]:::spacer
        PROVES_MAINT[PROVES Kit Maintainers]
        UNI_A[University A 2020 Mission]
        UNI_B[University B 2022 Mission]
    end

    F_TEAM -->|maintains| F_DOC
    F_TEAM -->|publishes| F_VER

    PROVES_MAINT -->|develops| PROVES_KIT[PROVES Kit Docs]
    UNI_A -.->|contributed to| PROVES_KIT
    UNI_B -.->|contributed to| PROVES_KIT

    F_TEAM -.->|WEAK interface| PROVES_MAINT
    UNI_A -.->|graduated/left| UNI_B

    style F_TEAM fill:#e1f5ff
    style PROVES_MAINT fill:#fff4e1
    style UNI_A fill:#ffebee
    style UNI_B fill:#e8f5e9

    linkStyle 4 stroke:#f44336,stroke-width:4px,stroke-dasharray: 5 5
    linkStyle 5 stroke:#ff9800,stroke-width:3px,stroke-dasharray: 5 5
    %% Font sizing classes for consistency
    classDef default font-size:24px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef diamond font-size:22px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef spacer fill:none,stroke:none,color:transparent,width:1px,height:1px;
```

**Interface Strength:**
- F-Prime ↔ PROVES Kit: **WEAK** (no documentation cross-references)
- University A ↔ University B: **WEAK** (student turnover, knowledge loss)

**Knowledge at Risk:**
- Integration knowledge lives in individual team members' heads
- Not captured in either documentation system
- Vulnerable to team turnover
- No mechanism for cross-team knowledge transfer

> **Key Insight:** The weakest link in the system isn't technical—it's organizational. Two excellent documentation systems (F-Prime and PROVES Kit) fail when they don't talk to each other.

---

## Impact Analysis

### What Happens When These Dependencies Break?

| Dependency | Misconfiguration | Result | Detection Time |
|------------|------------------|--------|----------------|
| Power Stability | Enable logic inverted | Silent IMU failure | Launch +hours |
| Power Sequence | Bus opens before power | I2C init fails | Boot time |
| Bus Sharing | Multiple devices conflict | Corrupted data | Mission +days |
| Error Recovery | No power cycle on error | Permanent sensor loss | First error |

### Estimated Risk

```mermaid
---
config:
  theme: base
  fontSize: 24
  themeCSS: |
    .node rect, .cluster rect, .edgePath path { transition: filter 0.2s ease, stroke-width: 0.2s ease; }
    .node:hover rect, .cluster:hover rect, .edgePath:hover path { filter: drop-shadow(0 0 8px rgba(0,0,0,0.35)); stroke-width: 3px; }
    .edgeLabel rect { rx: 6px; ry: 6px; stroke-width: 1px; }
    .cluster-label { font-weight: 600; }
    .node .label, .nodeLabel, .node foreignObject div, .edgeLabel { font-size: 20px !important; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif !important; }
    .node.decision .label, .node polygon + .label { font-size: 18px !important; }
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
    gridLineStartPadding: 35
    numberSectionStyles: 4
  flowchart:
    curve: 'linear'
    htmlLabels: false
    useMaxWidth: true
    padding: 25
    nodeSpacing: 60
    rankSpacing: 80
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
    diagrampadding: 25
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
    c4Shapepadding: 25
    width: 216
    height: 60
    boxMargin: 10
---
quadrantChart
    title Risk Matrix: Cross-System Dependencies
    x-axis Low Impact --> High Impact
    y-axis Low Probability --> High Probability
    quadrant-1 Monitor
    quadrant-2 Critical
    quadrant-3 Accept
    quadrant-4 Mitigate
    "Power Stability": [0.9, 0.8]
    "Power Sequence": [0.8, 0.7]
    "Bus Sharing": [0.6, 0.4]
    "Error Recovery": [0.7, 0.5]
```

**Criticality Assessment:**
- **Power Stability:** Quadrant 2 (Critical) - High impact, high probability
- **Power Sequence:** Quadrant 2 (Critical) - High impact, moderate probability
- **Bus Sharing:** Quadrant 4 (Mitigate) - Moderate impact/probability
- **Error Recovery:** Quadrant 4 (Mitigate) - Moderate impact/probability

---



## Recommendations

### Immediate Actions

1. **Document the Integration**
   - Create "F-Prime + PROVES Kit Integration Guide"
   - Specify power-on timing requirements
   - Define configureTopology() ordering

2. **Add Cross-References**
   - F-Prime docs should mention PROVES Kit power requirements
   - PROVES docs should mention F-Prime I2C dependencies

3. **Implement Health Checks**
   - Verify power state before I2C operations
   - Add power cycle recovery on persistent errors

4. **Create Test Suite**
   - Test power sequencing variations
   - Verify enable logic configurations
   - Validate error recovery mechanisms

### Long-Term Solutions

1. **Automated Dependency Tracking**
   - This PROVES Library system!
   - Continuous scanning for cross-system dependencies
   - Alerting on team boundary crossings

2. **Knowledge Capture Process**
   - Empirical captures from university teams
   - Post-mission reports
   - Failure analysis documentation

3. **Interface Strengthening**
   - Regular F-Prime + PROVES Kit integration meetings
   - Shared documentation repository
   - Cross-team code reviews

---

## Navigation

- [← Back to Home](../index.html)
- [← Previous: Dependency Overview](overview.html)
- [Next: Transitive Dependency Chains ->](transitive-chains.html)

---



**Analysis Method:** Cross-document analysis, manual annotation
**Confidence Level:** High (human-verified, evidence-based)
**Impact:** Demonstrates exact Team A/Team B failure mode
**Date:** December 20, 2024











