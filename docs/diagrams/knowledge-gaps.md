---
layout: article
title: Knowledge Gaps
---



# Knowledge Gaps

What's NOT documented: power-on timing, voltage stability, error recovery, bus sharing conflicts, and platform integration.

[← Back to Home](../index.html)

---

## What Are Knowledge Gaps?

**Knowledge Gaps** are critical dependencies, requirements, or procedures that:
1. **Exist in reality** (engineers know them, or discover them through failure)
2. **Are NOT documented** in any system
3. **Can cause mission failures** if unknown
4. **Are at risk of loss** during team turnover

This analysis found **5 major knowledge gaps** in the F-Prime + PROVES Kit integration.

---



## Gap 1: Power-On Timing Requirements

### What You're Looking At

This sequence diagram shows the power-on process for an I2C device, with all the timing steps highlighted in red because they're NOT documented anywhere. When you turn on power, the voltage takes time to rise, the device takes time to reset itself, and it takes more time to be ready for communication. Without knowing these delays, you'll try to talk to the device before it's ready.

**Think of it like:** Calling someone right after they wake up. You need time for them to (1) open their eyes (voltage rise), (2) remember who they are (power-on reset), and (3) get their brain working (ready for conversation). Call too early and you'll just get confused mumbling.

### The Missing Specification

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
sequenceDiagram
    participant LSM as LoadSwitchManager
    participant Power as Power Supply
    participant Device as I2C Device
    participant Driver as I2C Bus Driver

    LSM->>Power: turn_on imu
    Power->>Power: GPIO goes HIGH
    Power->>Device: Voltage ramps up

    Note over Power,Device: GAP: How long does this take?
    rect rgb(255, 200, 200)
        Power-->>Device: t_rise = ??? ms
        Device-->>Device: Internal power-on reset
        Note over Device: GAP: How long for POR?
        Device-->>Device: t_por = ??? ms
        Device-->>Device: Initialize registers
        Note over Device: GAP: Ready delay?
        Device-->>Device: t_ready = ??? ms
    end

    Note over Device,Driver: GAP: Total delay unknown
    Driver->>Device: I2C address probe
    alt Device Ready
        Device-->>Driver: ACK
    else Device Not Ready
        Device-->>Driver: No response - bus timeout
    end
```

### What's NOT Documented

| Parameter | F-Prime Docs | PROVES Docs | Typical Value | Impact if Unknown |
|-----------|---------|-------------|---------------|-------------------|
| **t_rise** - Voltage rise time | [NO] | [NO] | 1-10ms | Race condition |
| **t_por** - Power-on reset duration | [NO] | [NO] | 10-100ms | Device not initialized |
| **t_ready** - Ready after POR | [NO] | [NO] | 1-50ms | I2C communication fails |
| **t_total** - Safe delay before I2C | [NO] | [NO] | 50-200ms | **Intermittent failures** |

### Where This Knowledge Lives

**Currently:**
- 🧠 In experienced engineers' heads
- 📄 Maybe in MPU6050 datasheet (not referenced in either doc)
- 🐛 Discovered through debugging after failures
- 📧 Discussed in email threads (not captured)

**Risk:** When Team A graduates, this knowledge is **LOST**.

### Real-World Impact

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
    START[New developer integrates IMU]

    CASE1{Does developer add delay?}:::diamond
    CASE2{What delay value?}:::diamond
    CASE3{Test coverage?}:::diamond

    TOO_SHORT[Delay too short 50ms]
    WORKS_BENCH["✓ Works on bench<br/>warm start"]
    FAILS_FLIGHT["✗ Fails in flight<br/>cold start slower"]

    NO_DELAY[No delay added]
    WORKS_LINUX["✓ Works on Linux<br/>scheduler slow enough"]
    FAILS_RTOS["✗ Fails on RTOS<br/>too fast"]

    CORRECT[Delay adequate<br/>200ms]
    SUCCESS["✓ Always works"]

    START --> CASE1
    CASE1 -->|Yes| CASE2
    CASE1 -->|No| NO_DELAY

    CASE2 -->|Guesses 50ms| TOO_SHORT
    CASE2 -->|Finds spec: 200ms| CORRECT

    TOO_SHORT --> CASE3
    CASE3 -->|Only bench test| WORKS_BENCH
    WORKS_BENCH -.->|Ships to orbit| FAILS_FLIGHT

    NO_DELAY --> WORKS_LINUX
    WORKS_LINUX -.->|Ports to embedded| FAILS_RTOS

    CORRECT --> SUCCESS

    style FAILS_FLIGHT fill:#ffcdd2
    style FAILS_RTOS fill:#ffcdd2
    style SUCCESS fill:#c8e6c9
    %% Font sizing classes for consistency
    classDef default font-size:24px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef diamond font-size:22px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef spacer fill:none,stroke:none,color:transparent,width:1px,height:1px;
```

**Probability:** 70% of developers will get this wrong without documentation.

> **Why This Matters:** This is the EXACT failure mode from the Team A/Team B scenario. Team A knew the 200ms delay was needed (through trial and error). Team B saw it, thought "that's too slow," changed it to 10ms, tested on a warm system (worked), then failed in orbit on a cold boot. All because the timing requirement wasn't documented.

---



## Gap 2: Voltage Stability Requirements

### What You're Looking At

This diagram shows electrical characteristics that software developers never think about but absolutely matter for I2C communication. Every component has voltage requirements (how clean the power needs to be, how much it can drop, etc.). The diagram shows all the parameters with "???" because they're not in the software documentation.

**Think of it like:** Trying to have a phone conversation with a bad connection. If the signal drops too low (voltage dropout), gets too noisy (ripple), or cuts out briefly (current spike), you'll miss words or get static. Your phone app doesn't tell you "you need -85dBm signal strength" but that knowledge matters.

### The Missing Specification

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
    subgraph "Power Supply Characteristics"
        spacer25[ ]:::spacer
        V_NOM[Nominal Voltage 3.3V]
        V_RIPPLE[Ripple ??? mV]
        V_DROPOUT[Dropout ??? mV]
        I_SPIKE[Current spike ??? mA]
    end

    subgraph "I2C Bus Requirements"
        spacer26[ ]:::spacer
        V_IH[V_IH Input High ??? V minimum]
        V_IL[V_IL Input Low ??? V maximum]
        V_MARGIN[Noise Margin ???]
    end

    subgraph "Load Switch Characteristics"
        spacer27[ ]:::spacer
        R_ON[R_ON ??? mΩ]
        I_MAX[I_MAX ??? mA]
        T_SWITCH[Switch time ??? μs]
    end

    V_NOM -.->|minus dropout| V_DROPOUT
    V_DROPOUT -.->|must exceed| V_IH
    I_SPIKE -.->|causes drop: I × R_ON| R_ON
    V_RIPPLE -.->|must be less than| V_MARGIN

    style V_RIPPLE fill:#ffebee
    style V_DROPOUT fill:#ffebee
    style I_SPIKE fill:#ffebee
    style V_IH fill:#fff9c4
    style V_MARGIN fill:#fff9c4
    style R_ON fill:#e1f5ff
    %% Font sizing classes for consistency
    classDef default font-size:24px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef diamond font-size:22px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef spacer fill:none,stroke:none,color:transparent,width:1px,height:1px;
```

### What's NOT Documented

| Parameter | Required For | F-Prime Docs | PROVES Docs | Impact |
|-----------|--------------|---------|-------------|--------|
| **V_ripple** | Clean I2C signals | [NO] | [NO] | Bit errors |
| **V_dropout** | Load regulation | [NO] | [NO] | Brownout |
| **I_spike** | Inrush current | [NO] | [NO] | Voltage sag |
| **R_ON** | Switch resistance | [NO] | [NO] | Power loss |
| **V_IH, V_IL** | I2C thresholds | [NO] | [NO] | Communication errors |

### Where This Knowledge Lives

**Currently:**
- 📊 Hardware schematics (not linked to software docs)
- 🔬 Oscilloscope measurements during debugging
- 🏭 Component datasheets (MPU6050, load switch IC, regulators)
- 👥 Hardware engineer tribal knowledge

**Risk:** Software developers don't know to check these parameters.

### Failure Mode

```
Scenario: High power draw during camera operation
  ↓
3.3V rail sags to 3.1V (within regulator spec)
  ↓
I2C V_IH threshold is 0.7 × Vdd = 0.7 × 3.1V = 2.17V
  ↓
Signal integrity marginal
  ↓
I2C bus has intermittent bit errors
  ↓
IMU read returns corrupted data
  ↓
Attitude determination fails
  ↓
Mission loss
```

**Time to debug:** Days to weeks (requires oscilloscope, experienced hardware engineer)

> **Key Insight:** This gap exists because hardware knowledge and software knowledge live in different teams and different documents. The hardware team knows the voltage requirements (they designed the circuit), but the software team doesn't have access to that information. This is an organizational problem, not a technical one.

---



## Gap 3: Error Recovery Strategies

### What You're Looking At

This state diagram shows a decision tree for error recovery that SHOULD exist but doesn't. When an I2C error happens, the system needs to decide: Is this recoverable? Should we retry? Should we power cycle? How many times? The diagram shows that currently, systems just log the error and give up (red path at bottom), when they should follow the recovery decision tree (red-boxed section).

**Think of it like:** When you drop your phone and the screen freezes, you could either (1) declare it broken and buy a new one, or (2) try turning it off and on again first. Most software does option 1 because nobody documented that option 2 exists and works 90% of the time.

### The Missing Integration

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
stateDiagram-v2
    [*] --> Normal: System boot

    Normal --> I2C_Error: I2C read fails
    I2C_Error --> Log_Warning: F-Prime logs event

    state "KNOWLEDGE GAP" as GAP {
        Log_Warning --> Should_Power_Cycle: Decision point
        Should_Power_Cycle --> Power_Off: Yes
        Should_Power_Cycle --> Give_Up: No

        Power_Off --> Wait_Discharge
        Wait_Discharge --> Power_On
        Power_On --> Wait_Stabilize
        Wait_Stabilize --> Retry_I2C

        Retry_I2C --> Normal: Success
        Retry_I2C --> Try_Again: Fail (retry < max)
        Try_Again --> Power_Off
        Retry_I2C --> Give_Up: Fail (retry >= max)
    }

    Give_Up --> Degraded_Mode: Continue without IMU

    Log_Warning --> [*]: Currently No recovery implemented

    style GAP fill:#ffebee
    style Log_Warning fill:#fff9c4
    style Give_Up fill:#ffcdd2
    style Normal fill:#c8e6c9
```

### What's NOT Documented

| Decision Point | Question | F-Prime Docs | PROVES Docs | Current Reality |
|----------------|----------|---------|-------------|-----------------|
| **Error Detection** | Which errors are recoverable? | Logs error | N/A | Unknown |
| **Recovery Strategy** | Should power cycle on I2C error? | [NO] | [NO] | No recovery |
| **Retry Count** | How many retries before giving up? | [NO] | [NO] | Give up immediately |
| **Timing** | How long to wait after power cycle? | [NO] | [NO] | N/A |
| **Escalation** | When to alert operator? | Logs event | N/A | Every error (noisy) |

### Missing Decision Tree

**No documentation exists for:**

```
IF I2cStatus == I2C_READ_ERR:
    IF consecutive_errors < 3:
        # Try simple retry
        WAIT 10ms
        RETRY read()
    ELSE IF consecutive_errors < 10:
        # Power cycle recovery
        LoadSwitchManager.turn_off("imu")
        WAIT 500ms  # Capacitor discharge
        LoadSwitchManager.turn_on("imu")
        WAIT 200ms  # Power stabilization
        RETRY read()
    ELSE:
        # Permanent failure
        LOG CRITICAL "IMU unrecoverable"
        ENTER degraded_mode
        ALERT operator
```

**This entire decision tree is UNDOCUMENTED.**

### Where This Knowledge Lives

**Currently:**
- 🔬 Discovered through mission operations
- 📝 Procedures written after first failure
- 🧠 Operator tribal knowledge
- ✉️ Communicated verbally between shifts

**Risk:** Each new mission team rediscovers this through failures.

> **Why This Matters:** Without documented recovery strategies, every team invents their own (or doesn't bother). This means inconsistent behavior across missions and lost opportunities for automatic recovery. One team might have a sensor permanently fail while another team's system auto-recovers—just because of undocumented tribal knowledge.

---



## Gap 4: Bus Sharing and Conflicts

### What You're Looking At

This diagram shows an I2C bus topology where multiple devices share the same communication bus, but nobody documented which devices are where or what addresses they use. The dashed lines represent "unknown" connections. Without knowing the full picture, you might accidentally put two devices at the same address or try to power them all on simultaneously (overloading the power supply).

**Think of it like:** A party line telephone (old tech, look it up!). Multiple people share one phone line, so you need to know (1) who else is on the line, (2) their "ring codes" (addresses), and (3) not to call everyone at once. Without documentation, you'll accidentally call the wrong person or interrupt someone else's call.

### The Missing Architecture

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
    subgraph "I2C Bus Topology (UNDOCUMENTED)"
        spacer28[ ]:::spacer
        BUS["I2C Bus /dev/i2c-1 SDA/SCL"]

        DEV1[Device 1 IMU Addr 0x68]
        DEV2[Device 2 Magnetometer Addr ???]
        DEV3[Device 3 Camera Addr ???]
        DEV4[Device 4 ??? Addr ???]
    end

    subgraph "Power Control"
        spacer29[ ]:::spacer
        LSM1[IMU_ENABLE]
        LSM2[MAG_ENABLE]
        LSM3[CAM_ENABLE]
    end

    subgraph "Questions"
        spacer30[ ]:::spacer
        Q1[Are devices on<br/>same bus?]
        Q2[Can addresses<br/>conflict?]
        Q3[Power-on<br/>sequence?]
        Q4[Bus arbitra-<br/>tion?]
    end

    BUS -.->|unknown| DEV1
    BUS -.->|unknown| DEV2
    BUS -.->|unknown| DEV3
    BUS -.->|unknown| DEV4

    LSM1 --> DEV1
    LSM2 --> DEV2
    LSM3 --> DEV3

    DEV1 -.-> Q1
    DEV2 -.-> Q2
    LSM1 -.-> Q3
    BUS -.-> Q4

    style BUS fill:#ffebee
    style Q1 fill:#fff9c4
    style Q2 fill:#fff9c4
    style Q3 fill:#fff9c4
    style Q4 fill:#fff9c4
    %% Font sizing classes for consistency
    classDef default font-size:24px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef diamond font-size:22px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef spacer fill:none,stroke:none,color:transparent,width:1px,height:1px;
```

### What's NOT Documented

| Aspect | Information Needed | F-Prime Docs | PROVES Docs | Impact if Unknown |
|--------|-------------------|---------|-------------|-------------------|
| **Bus Topology** | Which devices on which bus? | [NO] | [NO] | Wrong bus configured |
| **Address Map** | All I2C addresses | Partial (0x68) | [NO] | Address conflicts |
| **Power Sequence** | Order to enable devices | [NO] | [NO] | Bus contention |
| **Simultaneity** | Can devices operate together? | [NO] | [NO] | Data corruption |
| **Priority** | Which device has priority? | [NO] | [NO] | Starvation |

### Conflict Scenarios

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
sequenceDiagram
    participant App as Application
    participant IMU as IMU Manager
    participant Mag as Magnetometer Manager
    participant Bus as I2C Bus
    participant HW_IMU as IMU Hardware
    participant HW_MAG as MAG Hardware

    Note over App,HW_MAG: Scenario 1: Address Conflict (UNDOCUMENTED)

    App->>IMU: Read IMU data
    App->>Mag: Read MAG data

    par Simultaneous I2C Transactions
        IMU->>Bus: Start transaction to 0x68
    and
        Mag->>Bus: Start transaction to 0x68 conflict
    end

    Bus-->>IMU: Data corrupted
    Bus-->>Mag: Data corrupted

    Note over App,HW_MAG: Both reads fail no indication why

    Note over App,HW_MAG: Scenario 2 Power-On Glitch UNDOCUMENTED

    App->>IMU: turn_on IMU
    App->>Mag: turn_on MAG

    par Simultaneous Power-On
        HW_IMU->>HW_IMU: Inrush current spike
    and
        HW_MAG->>HW_MAG: Inrush current spike
    end

    Note over HW_IMU,HW_MAG: Combined current exceeds load switch rating

    HW_IMU--XHW_IMU: Brownout / latchup
    HW_MAG--XHW_MAG: Brownout / latchup

    Note over App,HW_MAG: [NO] Devices damaged, mission loss
```

### Where This Knowledge Lives

**Currently:**
- 📐 Hardware schematics (separate from software docs)
- 🔍 Reverse-engineered from board layout
- 🧪 Discovered during integration testing
- 🚨 Learned from failures

**Risk:** Software developers don't have access to hardware documentation.

> **Key Insight:** This is another hardware/software knowledge gap. The hardware team drew schematics showing the bus topology, but the software team is writing I2C drivers without seeing those schematics. Both teams have half the picture, neither has the complete view.

---



## Gap 5: Platform-Specific Integration

### What You're Looking At

This diagram shows how F-Prime supports multiple platforms (Linux, Zephyr, bare metal) and PROVES Kit supports multiple languages (CircuitPython, C), but there's no documentation on how to combine them. Each box is a valid configuration, but the arrows with "how to combine?" show that the integration patterns are undocumented.

**Think of it like:** You have IKEA furniture (F-Prime) and tools from Home Depot (PROVES Kit). Both are good products with instructions, but there's no guide for "how to use Home Depot tools to assemble IKEA furniture." Every team figures it out themselves, often differently.

### The Missing Cross-Platform Guide

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
flowchart LR
    subgraph "F-Prime Framework"
        spacer31[ ]:::spacer
        F_LINUX[LinuxI2cDriver<br/>Linux]
        F_ZEPHYR[ZephyrI2cDriver<br/>Zephyr RTOS]
        F_BAREMETAL[Custom Driver<br/>Bare Metal]
    end

    subgraph "PROVES Kit"
        spacer32[ ]:::spacer
        P_CIRCUITPY[CircuitPython<br/>board.IMU_ENABLE]
        P_MICROPYTHON[MicroPython<br/>???]
        P_C[C/C++<br/>???]
    end

    subgraph "Integration Patterns"
        spacer33[ ]:::spacer
        INT1[F-Prime Linux +<br/>PROVES CircuitPython]
        INT2[F-Prime Zephyr +<br/>PROVES C]
        INT3[F-Prime Bare Metal +<br/>???]
    end

    F_LINUX -.->|how to combine?| P_CIRCUITPY
    F_ZEPHYR -.->|how to combine?| P_C
    F_BAREMETAL -.->|how to combine?| P_C

    F_LINUX -.-> INT1
    P_CIRCUITPY -.-> INT1

    F_ZEPHYR -.-> INT2
    P_C -.-> INT2

    style INT1 fill:#ffebee
    style INT2 fill:#ffebee
    style INT3 fill:#ffebee
    %% Font sizing classes for consistency
    classDef default font-size:24px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef diamond font-size:22px,font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;
    classDef spacer fill:none,stroke:none,color:transparent,width:1px,height:1px;
```

### What's NOT Documented

| Integration | F-Prime Platform | PROVES Platform | Documented? | Challenge |
|-------------|-------------|-----------------|-------------|-----------|
| **Desktop Sim** | Linux + Python | CircuitPython sim | [NO] | How to mock hardware? |
| **Flight Target** | Zephyr RTOS + C++ | C + registers | [NO] | How to share GPIO? |
| **Lab Test** | Linux + Python | Hardware board | [NO] | How to communicate? |

### Missing Integration Examples

**No documentation exists for:**

1. **How F-Prime C++ calls PROVES CircuitPython:**
   ```cpp
   // [NO] NOT DOCUMENTED
   // In F-Prime configureTopology():
   void configureTopology() {
       // How to call Python LoadSwitchManager from C++?
       // - Embed Python interpreter?
       // - Use IPC (sockets, shared memory)?
       // - Compile PROVES to C extension?
       // - Use external process + protocol?
   }
   ```

2. **How to share GPIO control:**
   ```
   [NO] NOT DOCUMENTED
   - Does F-Prime control GPIO directly?
   - Does PROVES control GPIO and F-Prime requests power?
   - Is there a hardware abstraction layer?
   - Who owns the GPIO driver?
   ```

3. **Build system integration:**
   ```cmake
   # [NO] NOT DOCUMENTED
   # How to build F-Prime + PROVES together?
   # - Separate processes?
   # - Linked libraries?
   # - Microservice architecture?
   ```

### Where This Knowledge Lives

**Currently:**
- 🔨 Each mission team invents their own integration
- 🎭 Architecture decisions not documented
- 📞 Communicated through private channels
- 🔄 Reinvented for each new mission

**Risk:** No standard integration pattern, constant rework.

> **Why This Matters:** Every mission team is reinventing the wheel. One team builds F-Prime+PROVES as separate processes communicating over sockets. Another compiles PROVES to C and links it with F-Prime. A third uses Python embedding. Without a documented pattern, teams waste months on integration instead of working on their actual mission.

---



## Summary: Knowledge Gap Impact

### Gap Distribution

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
pie title Knowledge Gaps by Category
    "Timing Specifications" : 3
    "Hardware Parameters" : 5
    "Software Integration" : 4
    "Error Handling" : 2
    "Platform Specifics" : 3
```

### Risk Matrix

| Gap | Probability of Occurrence | Severity if Unknown | Overall Risk |
|-----|--------------------------|---------------------|--------------|
| **Power-On Timing** | 70% | Critical | 🔴 **EXTREME** |
| **Voltage Stability** | 40% | Critical | 🔴 **HIGH** |
| **Error Recovery** | 90% | Medium | 🟡 **HIGH** |
| **Bus Conflicts** | 30% | High | 🟡 **MEDIUM** |
| **Platform Integration** | 60% | Medium | 🟡 **MEDIUM** |

### Time to Discover

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
gantt
    title Typical Discovery Timeline for Knowledge Gaps
    dateFormat YYYY-MM-DD
    section Design Phase
    Integration planning     :2024-01-01, 7d
    section Development
    Code implementation     :2024-01-08, 14d
    section Testing
    Bench testing          :2024-01-22, 7d
    Discovery Timing gap  :milestone, 2024-01-26, 0d
    section Integration
    System integration     :2024-01-29, 14d
    Discovery Bus conflict:milestone, 2024-02-05, 0d
    section Flight Prep
    Environmental testing  :2024-02-12, 21d
    Discovery Voltage gap :milestone, 2024-02-28, 0d
    section Operations
    Launch and operations  :2024-03-05, 7d
    Discovery Error handling gap :crit, 2024-03-08, 0d
```

**Average Discovery Time:** 45-60 days after project start

**Cost of Late Discovery:** Exponential
- Design phase: 1× cost to fix
- Development: 10× cost to fix
- Testing: 100× cost to fix
- **Flight: Mission loss**

---



## Recommendations

### Immediate Actions

1. **Create Integration Guide**
   - Document all 5 knowledge gaps
   - Provide specifications for timing, voltage, errors
   - Include decision trees for error recovery
   - Specify platform integration patterns

2. **Extract from Tribal Knowledge**
   - Interview experienced engineers
   - Document undocumented procedures
   - Capture failure lessons learned
   - Create searchable knowledge base

3. **Link Hardware to Software Docs**
   - Cross-reference schematics
   - Include component datasheets
   - Document pin mappings
   - Specify electrical characteristics

### Long-Term Solutions

1. **Automated Gap Detection**
   - Scan documentation for missing specifications
   - Flag undefined timing requirements
   - Detect undocumented integrations
   - Alert on platform-specific gaps

2. **Empirical Capture System**
   - Log all mission failures
   - Extract knowledge from debugging sessions
   - Capture workarounds and fixes
   - Build searchable failure database

3. **Continuous Knowledge Review**
   - Regular documentation audits
   - Cross-team knowledge sharing sessions
   - Mandatory post-mission reports
   - Knowledge preservation before team turnover

---

## Navigation

- [← Back to Home](../index.html)
- [← Previous: Transitive Dependency Chains](transitive-chains.html)
- [Next: Team Boundaries ->](team-boundaries.html)

---



**Analysis Method:** Negative space analysis, gap identification
**Gaps Found:** 5 major categories, 17 specific missing items
**Estimated Risk:** 🔴 EXTREME (multiple critical gaps)
**Date:** December 20, 2024











