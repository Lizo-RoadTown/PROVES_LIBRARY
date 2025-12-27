# Trial Mapping Design: F´ + PROVES Kit Knowledge Graph

## Purpose

This is a small-scale trial to test our mapping approach before scaling to the full documentation corpus. We'll use documents related to power management and I2C communication - the exact failure domain from the Team A/Team B catastrophic failure story.

## Selected Documents for Trial

### From F´ (nasa/fprime, branch: devel)
1. **Power management documentation** - Component configuration requirements
2. **I2C driver documentation** - Bus configuration and timing requirements

### From PROVES Kit (proveskit/pysquared, branch: main)
1. **Power system documentation** - PySquared power architecture
2. **Sensor integration documentation** - I2C sensor configuration

**Rationale:** These documents represent the exact scenario where Team B changed power code without knowing Team A's historical knowledge about component-specific requirements.

## Dual-Layer Metadata Structure

### Layer 1: Technical Relationships (ERV)

Each document gets mapped to technical nodes and relationships:

```json
{
  "library_entry_id": "uuid-here",
  "title": "F´ I2C Driver Configuration",
  "source": "fprime/docs/i2c-driver.md",
  "technical_nodes": [
    {
      "node_type": "component",
      "name": "I2C Bus Driver",
      "domain": "communication"
    },
    {
      "node_type": "component",
      "name": "Power Regulator",
      "domain": "power"
    }
  ],
  "technical_relationships": [
    {
      "relationship_type": "requires",
      "from": "I2C Bus Driver",
      "to": "Power Regulator",
      "context": "I2C driver requires specific power regulator voltage stability",
      "criticality": "high"
    }
  ]
}
```

### Layer 2: Organizational Provenance (FRAMES-Inspired)

Each document also gets organizational context:

```json
{
  "organizational_metadata": {
    "source_team": "NASA/JPL Flight Software Team",
    "capture_generation": "baseline",
    "mission_context": null,
    "knowledge_type": "vendor_documentation",
    "team_boundary_crossing": false,
    "interface_strength": null,
    "last_validated": "2024-01-15",
    "validation_context": "official_release"
  }
}
```

For PROVES Kit captures from university teams:

```json
{
  "organizational_metadata": {
    "source_team": "University Team A",
    "capture_generation": "2020-mission",
    "mission_context": "PROVE-ALPHA",
    "knowledge_type": "empirical_capture",
    "team_boundary_crossing": true,
    "interface_strength": "weak",
    "last_validated": "2020-09-15",
    "validation_context": "flight_tested"
  }
}
```

## Key Queries the System Must Answer

### Query 1: Technical Dependency Check
**User asks:** "I'm modifying the power regulator component. What else might break?"

**System response:**
```
ALERT: Power Regulator has 3 critical dependencies:
1. I2C Bus Driver (requires stable voltage)
   - Source: F´ docs/i2c-driver.md
2. Camera Interface (requires specific init sequence)
   - Source: PROVES Kit docs/camera-setup.md (Team A, 2020)

CROSS-TEAM KNOWLEDGE ALERT:
Team A (2020 mission) has empirical knowledge about Camera Interface dependency.
Interface strength: WEAK - knowledge may not flow naturally.
Recommendation: Check with Team A captures before modifying.
```

### Query 2: Historical Knowledge Discovery
**User asks:** "Has anyone dealt with I2C bus failures related to power?"

**System response:**
```
Found 2 relevant captures:

1. F´ I2C Driver Documentation (baseline knowledge)
   - Type: Vendor documentation
   - Validation: Official release

2. PROVE-ALPHA Mission Report (Team A, 2020)
   - Type: Empirical capture (flight-tested)
   - Context: "Voltage drop during high power draw caused I2C timing violation"
   - Mitigation: Added capacitor bank to power regulator
   - Validation: Flight-tested successfully

KNOWLEDGE FLOW WARNING:
Team A knowledge is 4+ years old and crosses team boundary.
Verify Team A members are still reachable or knowledge may be lost.
```

### Query 3: Change Impact Analysis
**User asks:** "What's the impact if PROVES Kit updates their power system docs?"

**System response:**
```
BREAKING CHANGE DETECTED:
PROVES Kit docs/power-system.md updated.

Affected mappings:
1. 3 technical relationships reference this document
2. 2 university team captures depend on this configuration
3. 1 risk pattern uses this as mitigation

Action needed:
- Review technical relationships for validity
- Alert teams with dependent captures (Team B, Team C)
- Verify risk mitigation patterns still applicable
```

## Database Schema Changes Needed

### Extended library_entries
```sql
ALTER TABLE library_entries ADD COLUMN organizational_metadata JSONB;

-- Index for fast organizational queries
CREATE INDEX idx_org_metadata_team ON library_entries
  USING gin ((organizational_metadata -> 'source_team'));
CREATE INDEX idx_org_metadata_generation ON library_entries
  USING gin ((organizational_metadata -> 'capture_generation'));
```

### New table: team_boundaries
```sql
CREATE TABLE team_boundaries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_a VARCHAR(255) NOT NULL,
  team_b VARCHAR(255) NOT NULL,
  interface_strength VARCHAR(50), -- 'strong', 'medium', 'weak'
  last_interaction TIMESTAMP,
  mission_context VARCHAR(255),
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### New table: knowledge_validation
```sql
CREATE TABLE knowledge_validation (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  library_entry_id UUID REFERENCES library_entries(id),
  validation_type VARCHAR(50), -- 'empirical', 'vendor', 'theoretical', 'simulation'
  validated_by VARCHAR(255), -- team or person
  validated_date TIMESTAMP,
  mission_context VARCHAR(255),
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Trial Success Criteria

[YES] **Success means:**
1. We can fetch 4 documents from GitHub
2. We can identify at least 2 technical relationships between them
3. We can add organizational metadata to each
4. We can query: "Show me all Team A knowledge that Team B might not know"
5. We can query: "What breaks if I change Component X?"

[NO] **Failure means:**
1. Can't map relationships between F´ and PROVES Kit docs
2. FRAMES metadata doesn't help identify knowledge flow gaps
3. Queries don't provide actionable insights

## Next Steps

1. **Fetch trial documents** - Use GitHub MCP tools to get actual content
2. **Manual annotation** - You and I identify relationships together
3. **Schema update** - Add organizational_metadata column
4. **Insert trial data** - Add 4 documents with full metadata
5. **Test queries** - Verify all 3 query types work
6. **Evaluate** - Does this approach scale? What's missing?

## Comprehensive Dependency Tracking Strategy

### Requirement: Map EVERY Possible Dependency

The system must discover and track ALL dependencies across:
- F´ framework components (hundreds of components)
- PROVES Kit implementations
- University team custom builds
- Third-party libraries and hardware
- Organizational knowledge (who knows what)

### Multi-Source Dependency Discovery

#### 1. Documentation Analysis (Primary)
- Scan ALL markdown files for dependency keywords
- Extract: "requires", "depends on", "conflicts with", "needs", "must have"
- Parse component diagrams, architecture docs
- Track cross-references between documents

#### 2. Code Analysis (Secondary)
- Parse `#include` statements in C++ files
- Analyze import statements in Python
- Track function calls across modules
- Identify hardware register dependencies

#### 3. Configuration Files (Critical)
- F´ topology files (`.fpp`, `.xml`)
- Component assembly definitions
- Build system dependencies (`CMakeLists.txt`)
- Hardware pin mappings

#### 4. Empirical Captures (University Teams)
- Mission reports documenting failures
- Test logs showing unexpected interactions
- Email threads discussing component issues
- Slack/Discord discussions about bugs

#### 5. Runtime Telemetry (Future)
- Actual component interactions during operation
- Power draw correlations
- Timing dependencies discovered in flight

### Continuous Dependency Mapping Process

```
┌─────────────────────────────────────────────────────────┐
│  CONTINUOUS DEPENDENCY DISCOVERY ENGINE                 │
└─────────────────────────────────────────────────────────┘

1. INGESTION LAYER (Always Running)
   ├─ GitHub Webhooks -> Detect new commits
   ├─ Daily Doc Sync -> Fetch changed files
   ├─ Manual Captures -> Team uploads mission reports
   └─ Telemetry Stream -> Runtime data (future)

2. EXTRACTION LAYER (Automated)
   ├─ NLP Parser -> Extract dependency mentions
   ├─ Code Parser -> Static analysis of includes/imports
   ├─ Config Parser -> Parse .fpp, .xml, CMake files
   └─ Pattern Matcher -> Detect known dependency patterns

3. GRAPH UPDATE LAYER (Automated + Human Review)
   ├─ Auto-add: High confidence dependencies (code imports)
   ├─ Human review: Medium confidence (NLP extracted)
   ├─ Alert: Conflicts with existing graph
   └─ Version: Track dependency changes over time

4. VALIDATION LAYER (Mixed)
   ├─ Empirical: Flight-tested (highest confidence)
   ├─ Simulation: Tested in lab
   ├─ Theoretical: Documented but not verified
   └─ Inferred: AI-extracted (needs validation)

5. QUERY LAYER (Always Available)
   ├─ "What does Component X depend on?"
   ├─ "Where is knowledge about X documented?"
   ├─ "Who last worked on X?"
   └─ "What breaks if I change X?"
```

### Dependency Location Tracking

Every dependency must track WHERE it was found:

```json
{
  "dependency": {
    "from_component": "I2C Bus Driver",
    "to_component": "Power Regulator 3.3V",
    "relationship_type": "requires",
    "sources": [
      {
        "source_type": "documentation",
        "location": "fprime/docs/I2CDriver.md:Lines 45-52",
        "confidence": "high",
        "found_date": "2024-01-15",
        "extraction_method": "manual_annotation"
      },
      {
        "source_type": "code",
        "location": "fprime/Drv/I2C/I2CDriver.cpp:Line 127",
        "confidence": "very_high",
        "found_date": "2024-01-15",
        "extraction_method": "static_analysis"
      },
      {
        "source_type": "empirical_capture",
        "location": "proves_library/captures/team_a_2020_mission_report.md",
        "confidence": "very_high",
        "found_date": "2020-09-15",
        "extraction_method": "team_capture",
        "context": "Voltage instability caused I2C timeouts",
        "validated_by": "flight_test"
      }
    ],
    "criticality": "high",
    "context_conditions": [
      "Only critical when using camera module (high power draw)"
    ]
  }
}
```

### Scalability: From 4 Documents to Thousands

**Trial Phase (4 documents):**
- Manual relationship identification
- Human verification of all dependencies
- Establish metadata patterns

**Phase 2 (100 documents):**
- Semi-automated extraction with human review
- Build confidence scoring system
- Train on validated relationships

**Phase 3 (Full corpus):**
- Automated extraction with selective human review
- High-confidence auto-add, medium-confidence flagged
- Continuous background scanning

**Phase 4 (Living system):**
- Real-time updates from GitHub webhooks
- Telemetry integration
- Community validation (teams mark dependencies as verified)

### Example: Complete Dependency Chain

```
Query: "What EVERY dependency for Camera Module X?"

System traces:
┌─────────────────────────────────────────────────────────┐
│ Camera Module X                                          │
├─────────────────────────────────────────────────────────┤
│ DIRECT DEPENDENCIES (found in 12 locations):            │
│                                                          │
│ ├─ I2C Bus Driver [REQUIRED]                           │
│ │  └─ Sources:                                          │
│ │     • fprime/docs/Camera.md (Lines 23-25)            │
│ │     • camera_module_x/datasheet.pdf (Page 4)         │
│ │     • team_a_2020/integration_notes.md               │
│ │                                                       │
│ ├─ Power Regulator 3.3V [REQUIRED]                     │
│ │  └─ Sources:                                          │
│ │     • camera_module_x/schematic.pdf (Section 2.1)    │
│ │     • proves_kit/docs/power_design.md                │
│ │     • team_b_2022/power_failure_report.md (!)        │
│ │       Context: "Voltage drop caused init failure"    │
│ │                                                       │
│ └─ GPIO Pin 12 [REQUIRED - Enable signal]              │
│    └─ Sources:                                          │
│       • fprime/topology.fpp (Line 445)                  │
│       • hardware_spec.xlsx                              │
└─────────────────────────────────────────────────────────┘

TRANSITIVE DEPENDENCIES (dependencies of dependencies):

├─ I2C Bus Driver depends on:
│  ├─ Clock Generator (crystal oscillator stability)
│  ├─ Pull-up Resistors (4.7kΩ on SDA/SCL)
│  └─ Power Regulator (voltage stability during comms)
│
└─ Power Regulator depends on:
   ├─ Main Battery Bus
   ├─ Load Switch
   └─ Capacitor Bank (100µF for spike suppression)
      └─ CRITICAL: Team A 2020 added this after failure!
         Source: team_a_2020/mitigation_log.md

ORGANIZATIONAL KNOWLEDGE:
├─ Power Regulator -> Capacitor Bank relationship
│  └─ Known by: Team A (2020, no longer active)
│  └─ Interface to Team B: WEAK
│  └─ Risk: Knowledge loss due to team turnover
│
└─ Camera Module init sequence timing
   └─ Known by: Team C (2021)
   └─ Documented in: Slack thread (not captured!)
   └─ Risk: HIGH - undocumented tribal knowledge
```

## Trial Success Criteria (Updated)

[YES] **Success means:**
1. We can fetch 4 documents and find ALL dependencies mentioned in them
2. We track WHERE each dependency was found (doc location, line numbers)
3. We can trace transitive dependencies (dependencies of dependencies)
4. We can identify MISSING knowledge (gaps in documentation)
5. System can answer: "Where is every mention of Component X?"
6. System alerts on knowledge at risk (weak team interfaces, old captures)

[NO] **Failure means:**
1. We find only some dependencies (missing others)
2. Can't trace WHERE knowledge came from
3. Can't identify knowledge gaps or at-risk knowledge
4. Manual work doesn't scale to hundreds of documents

## Open Questions

1. **Relationship verification:** How do we verify a relationship is real?
   - Options: Human review, AI inference, empirical testing, all three?

2. **Context dependencies:** Some relationships only matter in specific contexts
   - Example: "Power spike only matters if using Camera Module v2"
   - How do we model conditional relationships?

3. **Change tracking:** How do we know if a documentation change is breaking?
   - Cosmetic changes shouldn't invalidate mappings
   - Technical changes might invalidate relationships
   - Need change classification system?

4. **Team tracking:** How do we identify source teams?
   - Manual entry? GitHub contributors? Commit metadata?

5. **Knowledge aging:** When does Team A's 2020 knowledge become obsolete?
   - Component replaced? New standard adopted? Mission context changed?

6. **Negative space tracking:** How do we track what's NOT documented?
   - Example: "Camera Module timing dependency exists in code but not in docs"
   - System needs to flag undocumented dependencies

---

**Next:** If this comprehensive approach looks right, I'll implement the trial with enhanced dependency tracking that can scale to the full corpus.
