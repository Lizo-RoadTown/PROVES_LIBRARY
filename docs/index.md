---
layout: article
title: PROVES Library
key: page-home
---

# PROVES Library: Capturing Mission Knowledge Before It's Lost

## Preventing CubeSat Failures Through Automated Knowledge Capture

**What We're Building:** A system that automatically finds and tracks technical dependencies in spacecraft software - before student teams graduate and the knowledge disappears.

**Why It Matters:** University CubeSat missions fail when teams don't know what previous teams learned. This system captures that knowledge automatically.

---

## The Problem: Knowledge Loss at Team Boundaries

**Real Scenario from a CubeSat Mission:**

A new student team took over a satellite project. They found a 200ms delay in the power management code. It seemed pointless - "why wait 200 milliseconds?" They removed it to make the code faster.

On the bench in the lab, everything worked fine.

Two weeks before launch, during integration testing, the satellite failed completely. The IMU (navigation sensor) wouldn't respond. After days of debugging, they discovered: the sensor needs 200ms after power-on before it's ready to talk. The original team (who graduated 2 years ago) had figured this out the hard way and added the delay - but never documented WHY.

**The Real Problem:**
- Critical knowledge lived only in people's heads
- When students graduated, the knowledge vanished
- Code comments didn't explain the "why" behind decisions
- No one knew there was a dependency between power timing and sensor communication

**Our Solution:**
Automatically find and capture these dependencies BEFORE the knowledge is lost. Track exactly which team discovered each piece of knowledge. Alert teams when they're about to change something that might break other systems.

---

## Trial Analysis Summary

### Documents Analyzed

1. **[F´ I2C Driver Documentation](https://github.com/nasa/fprime/blob/devel/docs/how-to/develop-device-driver.md)** (411 lines)
   - NASA/JPL flight software framework
   - I2C communication and device driver patterns

2. **[PROVES Kit Power Management](https://github.com/proveskit/pysquared/blob/main/docs/load_switch.md)** (154 lines)
   - University CubeSat platform
   - Load switch control for subsystem power

### Key Findings

- **45+ Dependencies Identified** across 6 categories
- **4 Critical Cross-System Dependencies** found (not documented in either system)
- **2 Complete Transitive Dependency Chains** traced
- **5 Major Knowledge Gaps** detected
- **Team Interface Weakness** identified between F´ and PROVES Kit teams

---

## Interactive Diagrams

Explore the dependency relationships through interactive visualizations:

### 📊 [Dependency Overview](diagrams/overview.html)
Complete inventory of all 45+ dependencies found in both documents, categorized by type (software, hardware, configuration).

### 🔗 [Cross-System Dependencies](diagrams/cross-system.html)
The 4 critical dependencies between F´ and PROVES Kit that are **NOT documented** in either system - the exact failure mode from the Team A/Team B scenario.

### ⛓️ [Transitive Dependency Chains](diagrams/transitive-chains.html)
Multi-hop dependency paths showing how Application Layer depends on I2C, which depends on Power, which depends on Load Switch configuration.

### ⚠️ [Knowledge Gaps](diagrams/knowledge-gaps.html)
What's NOT documented: power-on timing, voltage stability, error recovery, bus sharing conflicts, and platform integration.

### 👥 [Team Boundaries](diagrams/team-boundaries.html)
Organizational analysis showing WEAK interface between NASA/JPL F´ team and university PROVES Kit teams - where knowledge gets lost.

---

## System Capabilities Demonstrated

### ✅ Comprehensive Dependency Discovery
- Found EVERY dependency mentioned in source documents
- Tracked 6 dependency types: software, hardware, configuration, build, data, state

### ✅ Location Tracking
- Every dependency has source file and line number citations
- Can answer: "Where is Component X mentioned?"

### ✅ Cross-Document Analysis
- Identified relationships between separate documentation sources
- Found hidden dependencies across system boundaries

### ✅ Knowledge Gap Detection
- Flagged 5 major undocumented dependencies
- Detected negative space (what's missing from docs)

### ✅ Transitive Chain Tracing
- Followed dependencies through multiple hops
- Identified complete dependency paths

### ✅ Organizational Insight
- Mapped knowledge to source teams
- Identified weak team interfaces
- Flagged knowledge at risk of loss

---

## Technical Implementation

This analysis demonstrates the foundation for the PROVES Library automated knowledge graph system:

**Database Schema:**
- `library_entries` - Indexed documentation
- `kg_nodes` - Components and concepts
- `kg_relationships` - Dependency edges with metadata
- `team_boundaries` - Organizational interfaces
- `knowledge_validation` - Validation tracking

**Query Capabilities:**
```sql
-- "What depends on Component X?"
SELECT * FROM kg_relationships WHERE to_node_id = X;

-- "Where is knowledge about X documented?"
SELECT * FROM library_entries WHERE content LIKE '%X%';

-- "What breaks if I change X?"
SELECT transitive_dependencies(X);
```

---

## What's Working Now vs. What's Coming

### ✅ Phase 1: Manual Analysis (COMPLETE)
We manually analyzed two real NASA/university CubeSat documents and found:
- 45+ dependencies that teams need to know about
- 4 critical dependencies that aren't documented ANYWHERE
- 5 major knowledge gaps that cause failures

[See the interactive diagrams below](#interactive-diagrams) to explore what we found.

### ✅ Phase 2: Automated Extraction (WORKING NOW)
The system can now automatically:
- Read documentation and extract dependencies using AI (Claude)
- Validate dependencies against our schema
- Store them in a PostgreSQL knowledge graph
- Ask humans to approve critical findings
- Track which team/person contributed each piece of knowledge

**Status:** Proof of concept working. You can run it yourself!

### 🔨 Phase 3: Smart Analysis (IN PROGRESS)
Building AI agents that can:
- Find hidden dependencies across multiple documents
- Detect when changes might break other systems
- Identify what knowledge is missing from documentation
- Trace why failures happen by following dependency chains

**Status:** Core framework built, connecting the pieces now.

### 🎯 Phase 4: Full Automation (FUTURE VISION)
The big goal:
- Automatically scan all your code and docs
- Find risks before they cause failures
- Generate code that follows best practices
- Continuous knowledge capture as teams work
- Alert when someone's about to make a dangerous change

**Status:** Designed but not yet implemented.

---

## Documentation

- [Trial Mapping Design Document](TRIAL_MAPPING_DESIGN.html)
- [Comprehensive Dependency Map](../trial_docs/COMPREHENSIVE_DEPENDENCY_MAP.html)
- [Original F´ Documentation](../trial_docs/fprime_i2c_driver_full.html)
- [Original PROVES Kit Documentation](../trial_docs/proves_power_full.html)

---

## About PROVES Library

**What It Does:**
The PROVES Library automatically captures and preserves technical knowledge from CubeSat missions before student teams graduate and that knowledge is lost.

**How It Works:**
1. **Reads** documentation and code using AI (Claude language models)
2. **Finds** dependencies between components (like "IMU needs power to be stable for 200ms")
3. **Stores** them in a database with evidence (which document, which line number)
4. **Tracks** which team discovered each piece of knowledge
5. **Alerts** when someone might break something by changing code

**Who It's For:**
- University CubeSat teams (students, faculty)
- Anyone building complex systems with team turnover
- Organizations that need to preserve "tribal knowledge"

**Technology We're Using:**
- **AI Models:** Claude (by Anthropic) for reading and understanding docs
- **Database:** PostgreSQL with pgvector for storing knowledge graphs
- **Agents:** LangGraph framework for orchestrating AI tasks
- **APIs:** GitHub integration for scanning repositories
- **Human Oversight:** System asks for approval before storing critical findings

**Current Status (December 2024):**
- ✅ Trial analysis complete (45+ dependencies found manually)
- ✅ Automated extraction working (AI can find dependencies)
- 🔨 Smart analysis in progress (connecting multiple AI agents)
- 🎯 Full automation planned (scan whole repos, detect risks)

---

**For Students:** This is a research project showing how AI can help preserve knowledge in spacecraft missions. The trial analysis (diagrams below) is complete and shows what we're trying to achieve at scale.

**For Developers:** The automated extraction system is working. Check out the [GitHub repository](https://github.com/Lizo-RoadTown/PROVES_LIBRARY) to see the code.
