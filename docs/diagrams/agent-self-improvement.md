---
layout: article
title: Agent Self-Improvement
---

# Agent Self-Improvement

How FRAMES AI agents learn and earn autonomy through trust calibration.

[← Back to Home](../index.html)

---

## Trust Calibration Loop

**What you're looking at:** The complete feedback loop where agents propose improvements, humans review them, and trust adjusts based on outcomes.

```mermaid
---
config:
  theme: base
  fontSize: 20
  themeCSS: |
    .node:hover rect, .node:hover circle, .node:hover polygon { stroke-width: 3px !important; filter: drop-shadow(0 0 8px rgba(0,0,0,0.3)); cursor: pointer; }
    .edgePath:hover path { stroke-width: 3px !important; opacity: 1; }
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
    curve: linear
    padding: 15
    nodeSpacing: 50
    rankSpacing: 50
---
flowchart TB
    subgraph DETECT["Pattern Detection"]
        OBS[Agent observes patterns]
        IDEA[Forms improvement hypothesis]
    end

    subgraph PROPOSE["Proposal Submission"]
        PROP[Submit formal proposal]
        QUEUE[(Proposal Queue)]
    end

    subgraph REVIEW["Human Review"]
        DASH[Oversight Dashboard]
        HUMAN{Engineer Decision}
    end

    subgraph OUTCOME["Trust Adjustment"]
        APPROVE[Approved]
        REJECT[Rejected]
        IMPL[Implemented]
        MEASURE{Measure Impact}
    end

    subgraph AUTONOMY["Earned Autonomy"]
        CHECK{Trust > 90%?}
        AUTO[Auto-approve enabled]
        MANUAL[Requires review]
    end

    OBS --> IDEA
    IDEA --> PROP
    PROP --> QUEUE
    QUEUE --> DASH
    DASH --> HUMAN
    HUMAN -->|approve| APPROVE
    HUMAN -->|reject| REJECT
    APPROVE --> IMPL
    IMPL --> MEASURE
    MEASURE -->|success| CHECK
    MEASURE -->|failure| CHECK
    REJECT --> CHECK
    CHECK -->|yes| AUTO
    CHECK -->|no| MANUAL
    AUTO -.->|future proposals| QUEUE
    MANUAL -.->|future proposals| DASH

    style DETECT fill:#e3f2fd,stroke:#1976d2
    style PROPOSE fill:#fff3e0,stroke:#ff6f00
    style REVIEW fill:#ffb74d,stroke:#e65100
    style OUTCOME fill:#e8f5e9,stroke:#388e3c
    style AUTONOMY fill:#f3e5f5,stroke:#7b1fa2

    style OBS fill:#bbdefb,stroke:#1976d2
    style IDEA fill:#bbdefb,stroke:#1976d2
    style PROP fill:#ffe0b2,stroke:#ff6f00
    style QUEUE fill:#ffcc80,stroke:#ff6f00
    style DASH fill:#ff8a65,stroke:#e64a19
    style HUMAN fill:#ff7043,stroke:#d84315
    style APPROVE fill:#a5d6a7,stroke:#388e3c
    style REJECT fill:#ef9a9a,stroke:#c62828
    style IMPL fill:#81c784,stroke:#2e7d32
    style MEASURE fill:#c8e6c9,stroke:#388e3c
    style CHECK fill:#ce93d8,stroke:#7b1fa2
    style AUTO fill:#b39ddb,stroke:#512da8
    style MANUAL fill:#ce93d8,stroke:#7b1fa2
```

---

## The Process

### 1. Pattern Detection
Agent notices something that could be improved during normal operation—a prompt phrase that causes confusion, a threshold that's too strict, a missing validation check.

### 2. Proposal Submission
Agent submits a formal proposal including:
- **Title** — What change is proposed
- **Rationale** — Why this would help
- **Predicted Impact** — Expected improvement
- **Supporting Evidence** — Extraction IDs or patterns that led to this

### 3. Human Review
Engineer sees the proposal in the Oversight Dashboard and decides to approve or reject, with optional notes.

### 4. Trust Adjustment
Based on the decision and implementation outcome, the agent's trust score for that capability adjusts.

### 5. Earned Autonomy
When trust exceeds the threshold (default 90%), that specific capability auto-approves without human review.

---

## Trust Score Changes

```mermaid
---
config:
  theme: base
  fontSize: 20
  themeVariables:
    primaryColor: '#FFF3E0'
    lineColor: '#FF9800'
    fontFamily: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif'
  flowchart:
    curve: linear
---
flowchart LR
    subgraph POSITIVE["Trust Increases"]
        A1["+5% Proposal Approved"]
        A2["+8% Implementation Succeeds"]
    end

    subgraph NEGATIVE["Trust Decreases"]
        R1["-10% Proposal Rejected"]
        R2["-15% Implementation Fails"]
    end

    style POSITIVE fill:#c8e6c9,stroke:#388e3c
    style NEGATIVE fill:#ffcdd2,stroke:#c62828
    style A1 fill:#a5d6a7,stroke:#388e3c
    style A2 fill:#81c784,stroke:#2e7d32
    style R1 fill:#ef9a9a,stroke:#c62828
    style R2 fill:#e57373,stroke:#b71c1c
```

| Event | Trust Change | Rationale |
|-------|--------------|-----------|
| Proposal Approved | +5% | Agent's judgment was correct |
| Implementation Succeeds | +8% | Change actually improved the system |
| Proposal Rejected | -10% | Agent misjudged what was needed |
| Implementation Fails | -15% | Approved change caused problems |

The asymmetry (larger penalties for failures) ensures agents are conservative and only propose changes they're confident about.

---

## Per-Capability Trust

Each agent tracks trust **separately** for each capability type. An agent might be trusted for threshold changes but not yet for prompt updates.

```mermaid
---
config:
  theme: base
  fontSize: 20
  themeVariables:
    primaryColor: '#FFF3E0'
    lineColor: '#FF9800'
    fontFamily: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif'
  flowchart:
    curve: linear
---
flowchart TB
    subgraph EXTRACTOR["Extractor Agent"]
        E1["prompt_update: 45%"]
        E2["threshold_change: 72%"]
        E3["method_improvement: 23%"]
    end

    subgraph VALIDATOR["Validator Agent"]
        V1["prompt_update: 91% ✓ AUTO"]
        V2["validation_rule: 56%"]
    end

    subgraph ANALYZER["Improvement Analyzer"]
        A1["ontology_expansion: 12%"]
        A2["prompt_update: 34%"]
    end

    style EXTRACTOR fill:#fff3e0,stroke:#ff6f00
    style VALIDATOR fill:#e8f5e9,stroke:#388e3c
    style ANALYZER fill:#e3f2fd,stroke:#1976d2

    style E1 fill:#ffe0b2,stroke:#ff6f00
    style E2 fill:#ffcc80,stroke:#ff6f00
    style E3 fill:#ffe0b2,stroke:#ff6f00
    style V1 fill:#a5d6a7,stroke:#388e3c
    style V2 fill:#c8e6c9,stroke:#388e3c
    style A1 fill:#bbdefb,stroke:#1976d2
    style A2 fill:#bbdefb,stroke:#1976d2
```

The **✓ AUTO** indicates this capability has reached auto-approve threshold (90%) and no longer requires human review.

---

## Capability Types

| Capability | Description | Example Proposal |
|------------|-------------|------------------|
| `prompt_update` | Changes to extraction/validation prompts | "Add check for F´ port naming conventions" |
| `threshold_change` | Adjust confidence thresholds | "Lower threshold for well-documented components" |
| `method_improvement` | Change extraction methodology | "Extract interfaces before components" |
| `validation_rule` | Add new validation checks | "Verify telemetry channel IDs are unique" |
| `ontology_expansion` | Define new entity types | "Add 'Health Check' as component category" |
| `tool_configuration` | Change tool usage patterns | "Use vector search before graph traversal" |

---

## Why This Matters

```mermaid
---
config:
  theme: base
  fontSize: 20
  themeVariables:
    primaryColor: '#FFF3E0'
    lineColor: '#FF9800'
    fontFamily: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif'
  flowchart:
    curve: linear
---
flowchart LR
    subgraph TRADITIONAL["Traditional ML"]
        T1[Train model]
        T2[Deploy]
        T3[Collect feedback]
        T4[Retrain]
        T1 --> T2 --> T3 --> T4
        T4 --> T1
    end

    subgraph FRAMES["FRAMES AI"]
        F1[Agent proposes]
        F2[Human reviews]
        F3[Trust adjusts]
        F4[Autonomy earned]
        F1 --> F2 --> F3 --> F4
        F4 -.->|"routine tasks"| F1
        F3 -.->|"critical tasks"| F2
    end

    style TRADITIONAL fill:#ffcdd2,stroke:#c62828
    style FRAMES fill:#c8e6c9,stroke:#388e3c
```

| Traditional ML | FRAMES AI Self-Improvement |
|----------------|---------------------------|
| Requires retraining | Learns continuously |
| All-or-nothing deployment | Granular per-capability trust |
| Humans label data | Humans approve proposals |
| Fixed after deployment | Improves during operation |
| No audit trail | Full proposal history |

---

**Agents that prove themselves earn autonomy. Those that don't stay supervised.**
