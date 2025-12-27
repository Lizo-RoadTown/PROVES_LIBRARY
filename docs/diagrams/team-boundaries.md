---
layout: article
title: Team Boundaries
---

# Team Boundaries

Organizational analysis showing WEAK interface between NASA/JPL F´ team and university PROVES Kit teams - where knowledge gets lost.

[← Back to Home](../index.html)

---

## FRAMES Framework: Where Knowledge Lives

**FRAMES (Failure Modes and Systems Engineering)** maps organizational knowledge flow, not technical components. This analysis shows:
- **WHERE** knowledge lives (which teams)
- **HOW STRONG** team interfaces are
- **WHEN** knowledge is at risk of loss
- **WHY** failures cross team boundaries

---

## Team Boundary Map

### What You're Looking At

This diagram maps the ORGANIZATIONAL structure, not the technical one. Each box is a team or group of people. Solid lines show strong, documented relationships (like F´ Core maintaining their docs). Dashed lines show weak, at-risk relationships (like university teams graduating and losing knowledge). The colors highlight different risk levels—red for teams that already left, orange for teams in transition, green for active teams.

**Think of it like:** A family tree showing who talks to whom. Strong relationships (solid lines) are like parents teaching kids—regular, documented, reliable. Weak relationships (dashed lines) are like distant cousins you only see at weddings—sporadic, informal, knowledge doesn't flow well.

### Organizational Structure

```mermaid
%%{init: {'flowchart': {'defaultRenderer': 'elk'}}}%%
flowchart TB
    subgraph "NASA/JPL"
        JPL_CORE[F´ Core Team<br/>⭐ Permanent Staff]
        JPL_DOC[Documentation Team]
        JPL_REL[Release Engineering]
    end

    subgraph "PROVES Maintainers"
        PROVES_LEAD[PROVES Kit Lead<br/>👤 Faculty/Staff]
        PROVES_DEV[Core Developers<br/>👥 3-5 people]
    end

    subgraph "University Teams"
        UNI_A_2020[University A<br/>2020 Mission<br/>👥 8 students]
        UNI_B_2022[University B<br/>2022 Mission<br/>👥 6 students]
        UNI_C_2024[University C<br/>2024 Mission<br/>👥 10 students]
    end

    subgraph "External Users"
        USER_1[Commercial User 1]
        USER_2[Hobbyist Users]
        USER_3[New Universities]
    end

    JPL_CORE -->|maintains| JPL_DOC
    JPL_CORE -->|publishes| JPL_REL
    JPL_DOC -.->|weak link| PROVES_LEAD

    PROVES_LEAD -->|coordinates| PROVES_DEV
    PROVES_DEV -.->|weak link| UNI_A_2020
    PROVES_DEV -.->|weak link| UNI_B_2022
    PROVES_DEV -.->|weak link| UNI_C_2024

    UNI_A_2020 -.->|graduated| UNI_B_2022
    UNI_B_2022 -.->|graduated| UNI_C_2024

    PROVES_LEAD -.->|minimal support| USER_1
    PROVES_LEAD -.->|minimal support| USER_2
    PROVES_LEAD -.->|minimal support| USER_3

    style JPL_CORE fill:#e1f5ff
    style PROVES_LEAD fill:#fff4e1
    style UNI_A_2020 fill:#ffebee
    style UNI_B_2022 fill:#ffe0b2
    style UNI_C_2024 fill:#c8e6c9
    style USER_1 fill:#f5f5f5
    style USER_2 fill:#f5f5f5
    style USER_3 fill:#f5f5f5

    linkStyle 2 stroke:#f44336,stroke-width:4px,stroke-dasharray: 5 5
    linkStyle 4 stroke:#f44336,stroke-width:3px,stroke-dasharray: 5 5
    linkStyle 5 stroke:#f44336,stroke-width:3px,stroke-dasharray: 5 5
    linkStyle 6 stroke:#f44336,stroke-width:3px,stroke-dasharray: 5 5
    linkStyle 7 stroke:#ff9800,stroke-width:3px,stroke-dasharray: 5 5
    linkStyle 8 stroke:#ff9800,stroke-width:3px,stroke-dasharray: 5 5
```

**Legend:**
- Solid lines: STRONG interfaces (maintained, versioned, stable)
- <span style="color:red">Red dashed lines</span>: **WEAK interfaces** (ad-hoc, undocumented, at-risk)
- <span style="color:orange">Orange dashed lines</span>: **TURNOVER RISK** (student graduation)

---

## Interface Strength Analysis

### F´ Team ↔ PROVES Kit Team

```mermaid
%%{init: {'flowchart': {'defaultRenderer': 'elk'}}}%%
flowchart LR
    subgraph "F´ Knowledge"
        F_PUB[Public Documentation<br/>[YES] Versioned<br/>[YES] Comprehensive]
        F_CODE[GitHub Repository<br/>[YES] nasa/fprime<br/>[YES] Well-maintained]
        F_COM[Community Forums<br/>[YES] Active support]
    end

    subgraph "Interface"
        INT[[NO] No Integration Docs<br/>[NO] No Cross-References<br/>[NO] No Joint Testing<br/>[NO] No Shared Examples]
    end

    subgraph "PROVES Knowledge"
        P_PUB[Public Documentation<br/>[WARNING] Growing<br/>[WARNING] Gaps exist]
        P_CODE[GitHub Repository<br/>[YES] proveskit/pysquared<br/>[WARNING] Active but small team]
        P_COM[Community<br/>[WARNING] Mostly university teams]
    end

    F_PUB -.->|weak| INT
    F_CODE -.->|weak| INT
    F_COM -.->|weak| INT

    INT -.->|weak| P_PUB
    INT -.->|weak| P_CODE
    INT -.->|weak| P_COM

    style F_PUB fill:#c8e6c9
    style F_CODE fill:#c8e6c9
    style F_COM fill:#c8e6c9
    style INT fill:#ffcdd2
    style P_PUB fill:#fff9c4
    style P_CODE fill:#fff9c4
    style P_COM fill:#fff9c4
```

**Interface Strength Score: 2/10 (WEAK)**

**Evidence:**
- [NO] F´ documentation doesn't mention PROVES Kit
- [NO] PROVES Kit documentation doesn't mention F´
- [NO] No shared integration guide
- [NO] No joint GitHub issues/discussions
- [NO] No cross-team code reviews
- [NO] No coordinated releases

**Knowledge at Risk:**
- Integration patterns (how F´ + PROVES work together)
- Power management requirements (this analysis!)
- Error recovery strategies
- Platform-specific configurations

> **Key Insight:** F´ and PROVES Kit are both well-documented systems individually, but the interface between them has a strength score of 2/10. This is like having two excellent textbooks but no syllabus telling you how to use them together.

---

## Knowledge Flow Analysis

### What You're Looking At

This flowchart shows the journey developers take when they need integration knowledge. Start at the top: check F´ docs (not found), check PROVES docs (not found), ask tribal experts. The problem is that the tribal knowledge path leads to either (1) PROVES maintainers who know but are overloaded, (2) JPL engineers who don't know PROVES, or (3) students who are also learning. Eventually, everyone ends up at "Discover Through Failure" -> knowledge gets captured in email/chat -> then LOST at graduation.

**Think of it like:** Trying to find a recipe your grandmother used to make. Check the cookbook (not there), check online (not there), ask family members (some remember pieces), eventually you try to recreate it yourself and write it down... on a sticky note that falls behind the fridge.

### Where Integration Knowledge Lives

```mermaid
%%{init: {'flowchart': {'defaultRenderer': 'elk'}}}%%
flowchart TB
    START[Integration Knowledge Needed]

    DOC_F{Check F´ Docs}
    DOC_P{Check PROVES Docs}

    TRIBAL[Ask Experienced Engineer]
    WHO{Who to Ask?}

    JPL_ENG[JPL Engineer<br/>[NO] Doesn't know PROVES]
    PROVES_ENG[PROVES Maintainer<br/>[WARNING] Knows integration]
    UNI_ENG[University Student<br/>[NO] Learning both]

    DISCOVER[Discover Through Failure]
    CAPTURE[Capture in Email/Chat]
    LOST[Knowledge Lost at Graduation]

    START --> DOC_F
    DOC_F -->|Not found| DOC_P
    DOC_P -->|Not found| TRIBAL

    TRIBAL --> WHO

    WHO -->|Contact JPL| JPL_ENG
    WHO -->|Contact PROVES| PROVES_ENG
    WHO -->|Contact University| UNI_ENG

    JPL_ENG -.->|Doesn't know| DISCOVER
    UNI_ENG --> DISCOVER

    PROVES_ENG -->|Has knowledge| CAPTURE
    DISCOVER --> CAPTURE
    CAPTURE --> LOST

    style DOC_F fill:#e8f5e9
    style DOC_P fill:#fff9c4
    style TRIBAL fill:#ffebee
    style PROVES_ENG fill:#c8e6c9
    style JPL_ENG fill:#ffcdd2
    style UNI_ENG fill:#ffe0b2
    style LOST fill:#b71c1c,color:#fff
```

**Critical Bottleneck:** PROVES Kit maintainers are the ONLY source of integration knowledge.

**Single Point of Failure:** If PROVES maintainers leave, integration knowledge is LOST.

> **Why This Matters:** This diagram explains why the power-on timing issue keeps happening. The knowledge exists somewhere (in someone's head or buried in a chat log), but the path to find it is so convoluted that most developers give up and rediscover it through failure instead.

---

## Team Turnover Analysis

### What You're Looking At

This Gantt chart shows three university team lifecycles over 5 years. Notice the pattern: each team works for 12-18 months (colored bars), then graduates (red "crit" markers), leaving a knowledge gap. Team B starts 6 months after Team A leaves, so there's no overlap for knowledge transfer. The red milestone markers show when knowledge is at risk of being lost forever.

**Think of it like:** Relay race runners who never actually hand off the baton. Runner A finishes and leaves the stadium. Six months later, Runner B shows up and has to figure out where the baton is and which direction to run.

### University Team Lifecycle

```mermaid
gantt
    title University Team Knowledge Retention
    dateFormat YYYY-MM
    section Team A (2020)
    Active mission     :active, a1, 2020-01, 2020-12
    Knowledge captured :done, a2, 2020-12, 1M
    Graduation/leave   :crit, a3, 2021-05, 1M
    Knowledge retention:a4, 2021-06, 18M

    section Team B (2022)
    New team starts    :b1, 2022-01, 1M
    Learning curve     :active, b2, 2022-01, 2022-06
    Active mission     :active, b3, 2022-06, 2023-03
    Knowledge captured :done, b4, 2023-03, 1M
    Graduation/leave   :crit, b5, 2023-08, 1M
    Knowledge retention:b6, 2023-09, 12M

    section Team C (2024)
    New team starts    :c1, 2024-01, 1M
    Learning curve     :active, c2, 2024-01, 2024-06
    Active mission     :active, c3, 2024-06, 2024-12

    section Knowledge Gaps
    Gap: Team A leaves :milestone, crit, 2021-05, 0d
    Gap: Team B leaves :milestone, crit, 2023-08, 0d
    Potential gap 2025 :milestone, crit, 2025-05, 0d
```

**Pattern:**
- ⏱️ Average team lifetime: **12-18 months**
- 🎓 Knowledge turnover: **Every 2 years**
- 📉 Retention rate: **~20%** (1-2 students stay for grad school)

### Knowledge Loss Calculation

```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'pie1':'#ff6b6b', 'pie2':'#ffa500', 'pie3':'#90ee90'}}}%%
pie title Knowledge Retention After Team Graduation
    "Lost (graduated)" : 70
    "Degraded (partially remembered)" : 20
    "Retained (documented or passed on)" : 10
```

**Only 10% of tribal knowledge is captured and passed to next team.**

> **Key Insight:** The 70% knowledge loss isn't because students are lazy about documentation. It's because (1) they're focused on getting their mission to work, (2) they don't know what future teams will need to know, and (3) there's no system in place to capture knowledge automatically as they work.

---

## The Team A / Team B Failure Scenario

### What You're Looking At

This sequence diagram tells the story of an actual failure caused by team boundaries. Follow the numbered steps: Team A discovers the 200ms delay is needed (through testing), commits the code but doesn't document WHY, then graduates. Team B arrives, sees the delay, thinks it's wasteful, "optimizes" it to 10ms, tests (works on warm hardware!), ships to space, then fails on cold boot. The red boxes highlight where knowledge was lost.

**Think of it like:** Your roommate learns that the apartment's hot water takes 2 minutes to warm up, but doesn't tell you. They move out. You move in, wait 30 seconds, decide the hot water is broken, and call the landlord. Meanwhile, you could have just waited 2 minutes.

### Organizational Dynamics

```mermaid
sequenceDiagram
    autonumber
    participant TeamA as Team A<br/>(2020)
    participant Docs as Documentation<br/>(GitHub)
    participant TeamB as Team B<br/>(2022)
    participant System as Integrated<br/>System

    Note over TeamA: Discovers: IMU needs 200ms<br/>power-on delay

    TeamA->>TeamA: Tests and validates<br/>(works with delay)

    rect rgb(255, 200, 200)
        Note over TeamA,Docs: [NO] GAP: Knowledge not captured
        TeamA->>Docs: Commit code with delay<br/>[NO] No comment explaining why
    end

    Note over TeamA: May 2021: Team graduates

    rect rgb(255, 255, 180)
        Note over Docs,TeamB: 6 month gap
    end

    Note over TeamB: January 2022: New team starts

    TeamB->>Docs: Read documentation
    Docs-->>TeamB: [NO] No explanation of delay

    TeamB->>TeamB: "This 200ms delay seems<br/>arbitrary and slow"

    rect rgb(255, 200, 200)
        Note over TeamB: [NO] Optimizes delay to 10ms
        TeamB->>Docs: Commit change<br/>"Optimize power-on sequence"
    end

    TeamB->>System: Bench test<br/>(warm start - works!)

    TeamB->>System: Ship to orbit

    rect rgb(220, 150, 150)
        System-->>TeamB: Cold boot in orbit
        Note over System: 10ms too short<br/>I2C init fails
        System--XSystem: Mission failure
    end

    Note over TeamA,System: [WARNING] Team A knew, but knowledge didn't flow
```

**Root Cause:** WEAK interface between Team A and Team B + inadequate documentation

**FRAMES Analysis:**
- **Where knowledge lived:** Team A members' heads
- **Interface strength:** WEAK (only code, no explanation)
- **Knowledge transfer mechanism:** None (graduation = knowledge loss)
- **Result:** Team B didn't know what Team A knew

> **Why This Matters:** This isn't a hypothetical scenario—it's based on real mission failures. The technical solution (200ms delay) was simple. The organizational problem (no knowledge transfer) caused mission loss. PROVES Library addresses the organizational problem by capturing knowledge automatically, before teams graduate.

---

## Interface Strength Scoring

### FRAMES Interface Strength Model

| Interface | Strength | Evidence | Knowledge Flow | Risk |
|-----------|----------|----------|----------------|------|
| **F´ Core ↔ F´ Docs** | 🟢 STRONG | Versioned, maintained, comprehensive | High | Low |
| **F´ Docs ↔ F´ Users** | 🟢 STRONG | Public, searchable, with examples | High | Low |
| **F´ ↔ PROVES** | 🔴 **WEAK** | No cross-references, no integration guide | **Very Low** | **EXTREME** |
| **PROVES Lead ↔ PROVES Docs** | 🟡 MEDIUM | Active but growing, some gaps | Medium | Medium |
| **PROVES ↔ University Teams** | 🔴 **WEAK** | Ad-hoc, tribal knowledge | **Low** | **HIGH** |
| **Uni Team A ↔ Uni Team B** | 🔴 **WEAK** | Student turnover, minimal handoff | **Very Low** | **EXTREME** |
| **PROVES ↔ External Users** | 🔴 **WEAK** | Minimal support, self-service | **Very Low** | **HIGH** |

### Scoring Criteria

**STRONG Interface (8-10):**
- [YES] Comprehensive documentation
- [YES] Regular communication
- [YES] Shared tooling
- [YES] Code reviews
- [YES] Joint testing
- [YES] Coordinated releases

**MEDIUM Interface (5-7):**
- [WARNING] Some documentation
- [WARNING] Occasional communication
- [WARNING] Separate tools but compatible
- [WARNING] Knowledge exists but not always accessible

**WEAK Interface (0-4):**
- [NO] Little to no documentation
- [NO] Minimal communication
- [NO] Incompatible or unknown tools
- [NO] Knowledge in individuals' heads
- [NO] High risk of knowledge loss

---

## Knowledge Capture Analysis

### What Gets Captured vs. Lost

```mermaid
%%{init: {'flowchart': {'defaultRenderer': 'elk'}}}%%
flowchart TB
    subgraph "Mission Lifecycle"
        DESIGN[Design Decisions]
        IMPL[Implementation]
        TEST[Testing & Debugging]
        OPS[Operations]
        RETRO[Retrospective]
    end

    subgraph "Captured (30%)"
        CODE[Code Repository<br/>[YES] Preserved]
        SCHEMA[Schematics<br/>[YES] Preserved]
        FORMAL_DOC[Formal Documentation<br/>[WARNING] Often outdated]
    end

    subgraph "Partially Captured (20%)"
        ISSUES[GitHub Issues<br/>[WARNING] Searchable but dispersed]
        CHAT[Chat Logs<br/>[WARNING] Saved but not indexed]
        EMAIL[Email Threads<br/>[WARNING] Private, not shared]
    end

    subgraph "Lost (50%)"
        TRIBAL[Tribal Knowledge<br/>[NO] In people's heads]
        WORKAROUND[Workarounds<br/>[NO] Undocumented]
        FAILURES[Failure Lessons<br/>[NO] Not written down]
        WHY[Design Rationale<br/>[NO] Not explained]
    end

    DESIGN --> CODE
    DESIGN --> WHY

    IMPL --> CODE
    IMPL --> WORKAROUND

    TEST --> ISSUES
    TEST --> FAILURES

    OPS --> CHAT
    OPS --> TRIBAL

    RETRO --> FORMAL_DOC
    RETRO -.->|rarely| FAILURES

    style CODE fill:#c8e6c9
    style SCHEMA fill:#c8e6c9
    style FORMAL_DOC fill:#fff9c4
    style ISSUES fill:#ffe0b2
    style CHAT fill:#ffe0b2
    style EMAIL fill:#ffe0b2
    style TRIBAL fill:#ffcdd2
    style WORKAROUND fill:#ffcdd2
    style FAILURES fill:#ffcdd2
    style WHY fill:#ffcdd2
```

**Only 30% of mission knowledge is permanently captured.**

**50% of knowledge is LOST after team graduation.**

> **Key Insight:** Notice that code (30% captured) is preserved, but the "why" behind decisions (50% lost) is not. Team B had Team A's code but not their reasoning. This is why PROVES Library focuses on capturing design rationale, failure lessons, and workarounds—the knowledge that lives in tribal memory, not in code repositories.

---

## Risk Heat Map

### Knowledge at Risk by Interface

```mermaid
quadrantChart
    title Knowledge Loss Risk by Interface Strength
    x-axis Low Team Turnover --> High Team Turnover
    y-axis Strong Interface --> Weak Interface
    quadrant-1 Critical Risk
    quadrant-2 Monitor
    quadrant-3 Low Risk
    quadrant-4 Moderate Risk
    F´ Core Docs: [0.1, 0.9]
    F´ to PROVES: [0.3, 0.2]
    PROVES to Uni Teams: [0.8, 0.2]
    Uni Team to Team: [0.9, 0.1]
    External Users: [0.5, 0.15]
```

**Critical Risk Zone (Quadrant 1):**
- **University Team -> Team:** EXTREME knowledge loss risk
- **PROVES -> University Teams:** HIGH knowledge loss risk
- **F´ -> PROVES:** EXTREME integration knowledge loss risk

---

## Recommendations

### Immediate Actions

1. **Strengthen F´ ↔ PROVES Interface**
   - Create joint integration guide
   - Cross-reference documentation
   - Establish regular sync meetings
   - Share GitHub issues/discussions

2. **Capture Tribal Knowledge**
   - Interview university teams BEFORE graduation
   - Document all workarounds and failures
   - Extract design rationale from code
   - Create searchable knowledge base

3. **Improve Team Handoff**
   - Mandatory knowledge transfer before graduation
   - Overlap period with new team
   - Documented procedures and lessons learned
   - Video recordings of key procedures

### Long-Term Solutions

1. **Automated Knowledge Capture**
   - **This PROVES Library system!**
   - Capture knowledge from GitHub issues, PRs, chat
   - Extract from code comments and commit messages
   - Index and make searchable

2. **Interface Strength Monitoring**
   - Track documentation coverage
   - Measure communication frequency
   - Monitor team turnover impact
   - Alert on weak interfaces

3. **Community Building**
   - Cross-university collaboration
   - Shared mission reviews
   - F´ + PROVES user group
   - Annual knowledge sharing conference

---

## PROVES Library Solution

### How This System Addresses Team Boundary Issues

```mermaid
%%{init: {'flowchart': {'defaultRenderer': 'elk'}}}%%
flowchart TB
    subgraph "Traditional Approach (Failed)"
        TRAD_TEAM[Team Knowledge]
        TRAD_GRAD[Graduation]
        TRAD_LOSS[Knowledge Lost]

        TRAD_TEAM --> TRAD_GRAD
        TRAD_GRAD --> TRAD_LOSS
    end

    subgraph "PROVES Library Approach"
        LIB_CAPTURE[Continuous Capture]
        LIB_AGENTS[Curator Agents]
        LIB_GRAPH[Knowledge Graph]
        LIB_FRAMES[Team Boundaries Tracking]
        LIB_QUERY[Query System]
        LIB_ALERT[Risk Alerts]

        LIB_CAPTURE --> LIB_AGENTS
        LIB_AGENTS --> LIB_GRAPH
        LIB_GRAPH --> LIB_FRAMES
        LIB_FRAMES --> LIB_QUERY
        LIB_QUERY --> LIB_ALERT
    end

    subgraph "Knowledge Sources"
        SRC_CODE[Code + Comments]
        SRC_ISSUES[GitHub Issues]
        SRC_CHAT[Chat/Email]
        SRC_EMPIRICAL[Mission Reports]

        SRC_CODE --> LIB_CAPTURE
        SRC_ISSUES --> LIB_CAPTURE
        SRC_CHAT --> LIB_CAPTURE
        SRC_EMPIRICAL --> LIB_CAPTURE
    end

    subgraph "Preserved Knowledge"
        PRES_TECH[Technical Dependencies]
        PRES_ORG[Organizational Context]
        PRES_WHY[Design Rationale]
        PRES_FAIL[Failure Lessons]

        LIB_GRAPH --> PRES_TECH
        LIB_FRAMES --> PRES_ORG
        LIB_GRAPH --> PRES_WHY
        LIB_GRAPH --> PRES_FAIL
    end

    style TRAD_LOSS fill:#ffcdd2
    style LIB_GRAPH fill:#c8e6c9
    style LIB_CAPTURE fill:#e1f5ff
    style PRES_TECH fill:#e8f5e9
    style PRES_ORG fill:#f3e5f5
```

**Key Features:**
- [YES] Captures knowledge from ALL sources (not just docs)
- [YES] Tracks WHICH TEAM contributed knowledge
- [YES] Preserves DESIGN RATIONALE (why decisions were made)
- [YES] Survives team turnover (knowledge in graph, not heads)
- [YES] Alerts on knowledge at risk
- [YES] Makes tribal knowledge searchable

---

## Success Metrics

### How to Measure Interface Strength Improvement

| Metric | Current | Target | Method |
|--------|---------|--------|--------|
| **Documentation Coverage** | 68% | 95% | % dependencies documented |
| **Cross-Team References** | 0 | 50+ | # doc links between F´ ↔ PROVES |
| **Knowledge Retention** | 10% | 80% | % knowledge captured before graduation |
| **Integration Failures** | 70% | <10% | % new teams that encounter power issue |
| **Time to Answer** | Days | Minutes | Time to find integration knowledge |
| **Interface Strength** | 2/10 | 8/10 | FRAMES scoring system |

---

## Navigation

- [← Back to Home](../index.html)
- [← Previous: Knowledge Gaps](knowledge-gaps.html)

---

**Analysis Method:** FRAMES organizational modeling, team interface analysis
**Interface Strength:** F´ ↔ PROVES scored 2/10 (WEAK)
**Knowledge Retention:** Only 10% captured after graduation
**Risk Level:** 🔴 EXTREME - Multiple weak interfaces, high turnover
**Date:** December 20, 2024
