# PROVES Library Integration Architecture

> **Purpose:** Define how FRAMES (socio-organizational provenance) wraps industry-standard MBSE models for CubeSat knowledge management.

**Created:** January 2026
**Status:** Living Document

---

## 1. The Complete Pipeline: Loose Capture → Verified Export

The PROVES Library uses a **funnel architecture**: capture loosely, verify with humans, then export to industry standards.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FULL PIPELINE FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  STAGE 1: LOOSE CAPTURE (Extractor)                                 │    │
│  │                                                                     │    │
│  │  • Cast wide net - don't force rigid classification                │    │
│  │  • Preserve ambiguity in gray areas                                │    │
│  │  • Capture subtle knowledge loss patterns                          │    │
│  │  • candidate_type is approximate, not definitive                   │    │
│  │                                                                     │    │
│  │  Output: staging_extractions (loose, all candidates)               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  STAGE 2: HUMAN REVIEW (Notion)                                     │    │
│  │                                                                     │    │
│  │  • Establish truth - agents assist, humans decide                  │    │
│  │  • Adjust dimensional metadata (contact, temporality, etc.)        │    │
│  │  • Train the system on what "good" looks like                      │    │
│  │  • Accept, reject, or flag for refinement                          │    │
│  │                                                                     │    │
│  │  Output: accepted extractions with verified dimensions             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  STAGE 3: PROMOTION & MATCHING (batch_promote_accepted.py)         │    │
│  │                                                                     │    │
│  │  • Hard matching: exact key + ecosystem deduplication              │    │
│  │  • Merge with existing entities or create new                      │    │
│  │  • Track: created | merged | skipped | error                       │    │
│  │  • Record dimensional adjustments in history                       │    │
│  │                                                                     │    │
│  │  Tables:                                                            │    │
│  │  ├── core_entities (verified knowledge with FRAMES dimensions)     │    │
│  │  ├── knowledge_enrichment (aliases, merges, cross-source)          │    │
│  │  └── dimensional_adjustment_history (human corrections)            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  STAGE 4: STANDARDIZATION & EXPORT (Future)                         │    │
│  │                                                                     │    │
│  │  • Normalize verified entities to industry standards               │    │
│  │  • XTCE for command/telemetry                                      │    │
│  │  • SysML v2 for architecture                                       │    │
│  │  • FPrime XML/FPP for flight software                              │    │
│  │  • Preserve FRAMES provenance in exports                           │    │
│  │                                                                     │    │
│  │  Output: Standard-compliant files + FRAMES annotations             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Loose Capture Matters

From the canon:

> "Premature structure creates false certainty. Early labeling collapses ambiguity that agents later need."

The extraction layer intentionally stays loose because:

1. **Gray areas contain the knowledge loss** - The subtle couplings that cause 88% failure aren't always clearly "component" or "telemetry"
2. **Humans train the system** - Over time, patterns emerge from human corrections
3. **Standards compliance is an export concern** - Not an extraction constraint
4. **Flexibility enables evolution** - The ontology can grow without breaking existing data

### Existing Infrastructure

| Stage | Component | Status |
|-------|-----------|--------|
| Capture | `extractor_v3.py` | ✓ Implemented |
| Capture | `staging_extractions` table | ✓ Implemented |
| Review | Notion integration | ✓ Implemented |
| Promotion | `batch_promote_accepted.py` | ✓ Implemented |
| Promotion | `core_entities` with FRAMES dimensions | ✓ Implemented (Migration 009) |
| Promotion | `knowledge_enrichment` table | ✓ Implemented (Migration 009) |
| Promotion | `dimensional_adjustment_history` | ✓ Implemented (Migration 009) |
| Export | XTCE serializer | ⏳ Not yet implemented |
| Export | SysML v2 serializer | ⏳ Not yet implemented |
| Export | FPrime serializer | ⏳ Not yet implemented |

---

## 2. The Two-Layer Model

The PROVES Library maintains two distinct but interconnected layers:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       PROVES KNOWLEDGE LIBRARY                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                 FRAMES LAYER (Provenance)                          │ │
│  │                                                                    │ │
│  │  "How do we know this? Who learned it? Can it transfer?"          │ │
│  │                                                                    │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐               │ │
│  │  │   Contact    │ │ Directionality│ │  Temporality │               │ │
│  │  │ (signal str) │ │ (fwd/back)   │ │ (time dep)   │               │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘               │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐               │ │
│  │  │Formalizability│ │   Coupling   │ │  Interface   │               │ │
│  │  │ (symbolic?)  │ │  Strength    │ │  Mechanisms  │               │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘               │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    │ wraps                               │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │              TECHNICAL LAYER (Industry Standard MBSE)              │ │
│  │                                                                    │ │
│  │  "What is the system? How is it structured?"                      │ │
│  │                                                                    │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐               │ │
│  │  │    XTCE      │ │  SysML v2    │ │   FPrime     │               │ │
│  │  │ Cmd/Tlm Def  │ │  Arch Model  │ │  Topology    │               │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘               │ │
│  │  ┌──────────────┐ ┌──────────────┐                                │ │
│  │  │    CCSDS     │ │    ReqIF     │                                │ │
│  │  │ Packet Fmt   │ │ Requirements │                                │ │
│  │  └──────────────┘ └──────────────┘                                │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### What Each Layer Does

| Layer | Question Answered | Standards | Your Contribution |
|-------|-------------------|-----------|-------------------|
| **FRAMES** | "How do we know this? Who learned it? Will it survive turnover?" | W3C PROV (provenance) | The 7-question checklist, epistemic dimensions, coupling strength |
| **Technical** | "What is the system? How does it work?" | XTCE, SysML v2, FPrime, CCSDS | Integration with existing standards |

---

## 2. FRAMES: The Provenance Layer

FRAMES captures the **socio-organizational dimension** - why 88% of university CubeSat programs fail.

### 2.1 The Seven Questions (Knowledge Capture Checklist)

Every piece of knowledge entering the system must answer:

| # | Question | Dimension | Risk If Missing |
|---|----------|-----------|-----------------|
| 1 | Who knew this, and how close were they? | Contact | Embodiment loss, proxy replacement |
| 2 | Where does the experience live now? | Pattern Storage | Observer loss, practice decay |
| 3 | What has to stay connected for this to work? | Relational Integrity | Fragmentation, hidden dependencies |
| 4 | Under what conditions was this true? | Context | Model overreach, context collapse |
| 5 | When does this stop being reliable? | Temporality | Drift, lifecycle mismatch |
| 6 | Who wrote or taught this, and why? | Authorship | Bad authorship, false authority |
| 7 | Does this only work if someone keeps doing it? | Reenactment | Embodied decay, skill erosion |

### 2.2 The Four Epistemic Dimensions

```
┌─────────────────────────────────────────────────────────────────┐
│                    EPISTEMIC SPACE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CONTACT (Signal Strength)                                       │
│  ├── Direct: Physical/experiential interaction                  │
│  ├── Mediated: Instrumented observation                         │
│  ├── Indirect: Effect-only inference                            │
│  └── Derived: Model-only, no physical observation               │
│                                                                  │
│  DIRECTIONALITY (Epistemic Operation)                           │
│  ├── Forward: Prediction (cause → effect)                       │
│  ├── Backward: Assessment (effect → cause)                      │
│  └── Bidirectional: Hypothesis → test → revision                │
│                                                                  │
│  TEMPORALITY (History Dependence)                               │
│  ├── Snapshot: Instantaneous state                              │
│  ├── Sequence: Ordering matters                                 │
│  ├── History: Accumulated past affects present                  │
│  └── Lifecycle: Long-term evolution                             │
│                                                                  │
│  FORMALIZABILITY (Symbolic Transformation Capacity)             │
│  ├── Portable: Moves intact to symbolic form                    │
│  ├── Conditional: Can formalize if context preserved            │
│  ├── Local: Resists formalization outside setting               │
│  └── Tacit: Remains embodied, cannot fully symbolize            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Coupling Strength

FRAMES measures the **bond strength** between modules:

| Strength | Range | Indicators |
|----------|-------|------------|
| Strong | 0.9-1.0 | Hard timing, safety-critical, explicit failure modes |
| Medium | 0.6-0.8 | Explicit dependency, degraded operation possible |
| Weak | 0.3-0.5 | Optional, "may", "can", fallbacks available |
| Very Weak | 0.0-0.2 | Only coexistence mentioned |

### 2.4 Interface Mechanisms

What maintains connections at boundaries:

- **Roles:** Integration lead, documentation owner
- **Processes:** Monthly reviews, design reviews, handoff checklists
- **Tools:** Shared repos, ICDs, tracking systems
- **Documentation:** Specs, procedures, lessons learned

---

## 3. Technical Layer: Industry Standard MBSE

The technical layer uses **existing industry standards** for system modeling.

### 3.1 Standard Mapping

| Standard | Purpose | File Format | PROVES Use Case |
|----------|---------|-------------|-----------------|
| **XTCE** | Command/Telemetry definitions | XML | Define spacecraft parameters, packets |
| **SysML v2** | System architecture | API-based | Model components, ports, connections |
| **FPrime** | Flight software topology | XML/FPP | F' component definitions |
| **CCSDS** | Packet formats | Binary + XML | Telemetry/command encoding |
| **ReqIF** | Requirements interchange | XML | Traceability |

### 3.2 Candidate Type Mapping to Standards

Your current `candidate_type` enum maps to standard elements:

| candidate_type | XTCE | SysML v2 | FPrime | Notes |
|----------------|------|----------|--------|-------|
| `component` | SpaceSystem | Part/Block | Component | Module/subsystem |
| `port` | - | Port | Port | Interface point |
| `command` | MetaCommand | Action | CommandPort | Operation |
| `telemetry` | SequenceContainer | - | TelemetryPort | Measurement |
| `parameter` | Parameter | Attribute | - | Configuration value |
| `data_type` | ParameterType | DataType | Type | Type definition |
| `event` | - | - | EventPort | State change |
| `connection` | - | Connector | Connection | Link between ports |
| `dependency` | - | Dependency | - | Requires relationship |
| `inheritance` | - | Generalization | - | Extends relationship |

---

## 4. How They Integrate

### 4.1 The Wrapping Pattern

FRAMES provenance **wraps** technical model elements:

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRAMES ENVELOPE                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Provenance Metadata                                        │ │
│  │ ├── observer_id: "claude-sonnet-4-5"                      │ │
│  │ ├── observer_type: "llm"                                   │ │
│  │ ├── contact_mode: "inferred"                               │ │
│  │ ├── contact_strength: 0.85                                 │ │
│  │ ├── temporality: "snapshot"                                │ │
│  │ ├── formalizability: "portable"                            │ │
│  │ ├── valid_from: "2026-01-14"                               │ │
│  │ ├── staleness_risk: "low"                                  │ │
│  │ └── source_snapshot_id: "abc123..."                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              │ wraps                             │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ XTCE Parameter (Industry Standard)                         │ │
│  │ ├── name: "BATT_VOLTAGE"                                   │ │
│  │ ├── parameterTypeRef: "VoltageType"                        │ │
│  │ ├── shortDescription: "Main battery voltage"               │ │
│  │ └── unitSet: { unit: "V", ... }                            │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Storage Model

```sql
-- Technical layer: Standard-compliant model elements
CREATE TABLE xtce_parameters (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    parameter_type_ref TEXT,
    short_description TEXT,
    unit TEXT,
    -- ... other XTCE fields
);

-- FRAMES layer: Provenance envelope
CREATE TABLE frames_provenance (
    id UUID PRIMARY KEY,
    technical_element_id UUID REFERENCES xtce_parameters(id),
    technical_element_type TEXT, -- 'xtce_parameter', 'sysml_block', etc.

    -- 7-question checklist
    observer_id TEXT,
    observer_type observer_type_enum,
    contact_mode contact_mode_enum,
    contact_strength NUMERIC(3,2),
    pattern_storage pattern_storage_enum,

    -- Epistemic dimensions
    directionality TEXT, -- 'forward', 'backward', 'bidirectional'
    temporality TEXT,    -- 'snapshot', 'sequence', 'history', 'lifecycle'
    formalizability TEXT, -- 'portable', 'conditional', 'local', 'tacit'

    -- Temporal validity
    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ,
    staleness_risk TEXT,
    refresh_trigger TEXT,

    -- Authorship
    author_id TEXT,
    intent TEXT,
    uncertainty_notes TEXT,

    -- Source tracking
    source_snapshot_id UUID,
    raw_evidence TEXT NOT NULL,
    confidence_score NUMERIC(3,2)
);
```

### 4.3 Export Patterns

#### Export to XTCE (Technical Only)
```xml
<SpaceSystem name="PROVES_Kit">
  <TelemetryMetaData>
    <ParameterSet>
      <Parameter name="BATT_VOLTAGE" parameterTypeRef="VoltageType">
        <ShortDescription>Main battery voltage</ShortDescription>
      </Parameter>
    </ParameterSet>
  </TelemetryMetaData>
</SpaceSystem>
```

#### Export to XTCE + FRAMES (With Provenance Annotations)
```xml
<SpaceSystem name="PROVES_Kit">
  <TelemetryMetaData>
    <ParameterSet>
      <Parameter name="BATT_VOLTAGE" parameterTypeRef="VoltageType">
        <ShortDescription>Main battery voltage</ShortDescription>
        <!-- FRAMES Provenance Extension -->
        <AncillaryDataSet>
          <AncillaryData name="frames:observer_id">claude-sonnet-4-5</AncillaryData>
          <AncillaryData name="frames:contact_mode">inferred</AncillaryData>
          <AncillaryData name="frames:contact_strength">0.85</AncillaryData>
          <AncillaryData name="frames:source_snapshot">abc123...</AncillaryData>
          <AncillaryData name="frames:raw_evidence">Battery voltage measured via ADC on pin PA0</AncillaryData>
        </AncillaryDataSet>
      </Parameter>
    </ParameterSet>
  </TelemetryMetaData>
</SpaceSystem>
```

---

## 5. The Three Relationship Layers

FRAMES captures couplings across three layers:

### 5.1 Digital Layer (Software ↔ Software/Hardware)

**Standards:** XTCE, FPrime, CCSDS

**Flows:** Data, commands, signals, messages, telemetry

**Example Coupling:**
```json
{
  "from": "xtce:TEMP_SENSOR",
  "to": "xtce:THERMAL_MANAGER",
  "via": "fprime:I2C_Bus",
  "flow": {
    "what": "Temperature readings in Celsius",
    "frequency": "every 100ms"
  },
  "if_stops": {
    "impact": "Thermal protection fails, safe mode entry"
  },
  "coupling_strength": 0.95,
  "frames_provenance": {
    "contact_mode": "mediated",
    "temporality": "sequence",
    "formalizability": "portable"
  }
}
```

### 5.2 Physical Layer (Hardware ↔ Hardware)

**Standards:** CCSDS packet encoding, hardware specs

**Flows:** Power, heat, mechanical force, electromagnetic signals

**Example Coupling:**
```json
{
  "from": "sysml:Battery",
  "to": "sysml:PowerRegulator",
  "via": "sysml:5V_Rail",
  "flow": {
    "what": "5V DC @ 200mA max",
    "frequency": "continuous"
  },
  "if_stops": {
    "impact": "Immediate brown-out reset"
  },
  "coupling_strength": 1.0,
  "frames_provenance": {
    "contact_mode": "direct",
    "temporality": "snapshot",
    "formalizability": "portable"
  }
}
```

### 5.3 Organizational Layer (People ↔ People/Teams)

**Standards:** W3C PROV for provenance

**Flows:** Information, decisions, authority, knowledge transfer

**Example Coupling:**
```json
{
  "from": "org:Electrical_Team",
  "to": "org:Software_Team",
  "via": "doc:ICD_v2.3",
  "flow": {
    "what": "Pin definitions, voltage levels, timing requirements",
    "frequency": "Updated at monthly design reviews"
  },
  "if_stops": {
    "impact": "Integration failures discovered late, 3-week delays"
  },
  "coupling_strength": 0.75,
  "frames_provenance": {
    "contact_mode": "cited",
    "temporality": "lifecycle",
    "formalizability": "conditional"
  }
}
```

**This is where FRAMES shines** - capturing the organizational fragility that causes the 88% failure rate.

---

## 6. Implementation Phases

### Stage 1-3: Current State (Implemented)

**Capture Layer (Stage 1):**
- `extractor_v3.py` - Loose extraction with FRAMES metadata
- `staging_extractions` table - All candidates with epistemic fields
- Schema validation via `schema_validator.py`

**Review Layer (Stage 2):**
- Notion integration for human review
- Accept/reject/flag workflow
- Dimensional adjustment during review

**Promotion Layer (Stage 3):**
- `batch_promote_accepted.py` - Batch promotion with hard matching
- `core_entities` table - Verified knowledge with full FRAMES dimensions:
  - `knowledge_form` (embodied/inferred)
  - `contact_level` (direct/mediated/indirect/derived)
  - `directionality` (forward/backward/bidirectional)
  - `temporality` (snapshot/sequence/history/lifecycle)
  - `formalizability` (portable/conditional/local/tacit)
  - `carrier` (body/instrument/artifact/community/machine)
- `knowledge_enrichment` table - Aliases, duplicate merges, cross-source correlation
- `dimensional_adjustment_history` - Audit trail of human corrections
- Promotion tracking (`promoted_at`, `promotion_action`)

### Stage 4: Standardization & Export (Next)

This is where industry-standard MBSE integration happens - **after human verification**.

**4.1 Normalization Layer:**
- Map verified `core_entities` to standard types
- Soft matching for semantic deduplication (not just exact key match)
- Canonical naming conventions per standard

**4.2 XTCE Export (Priority for cmd/tlm):**
- Export `telemetry` entities → XTCE `Parameter` elements
- Export `command` entities → XTCE `MetaCommand` elements
- Export `parameter` entities → XTCE `ParameterType` definitions
- Export `data_type` entities → XTCE type system
- Include FRAMES provenance as `AncillaryData`

**4.3 FPrime Export (For F' ecosystem):**
- Export `component` entities → FPrime Component XML
- Export `port` entities → FPrime Port definitions
- Export `connection` entities → FPrime topology connections
- Generate FPP files as alternative to XML

**4.4 SysML v2 Export (For architecture):**
- Export `component` entities → SysML Part/Block
- Export `port` entities → SysML Port
- Export `dependency` entities → SysML Dependency
- Export `inheritance` entities → SysML Generalization
- Use API-based approach (not XMI - SysML v2 doesn't use XMI)

**4.5 Organizational Layer (FRAMES-native):**
- No industry standard exists for organizational couplings
- Export to W3C PROV format for provenance
- Keep organizational layer in FRAMES format
- This is your unique contribution

### Stage 5: Round-Trip Sync (Future)

- Import from standard tools (Cameo, Capella, FPrime ground tools)
- Match imported elements to existing `core_entities`
- Merge with existing FRAMES provenance
- Detect conflicts and flag for human review

---

## 7. Key Principles

### 7.1 FRAMES Wraps, Doesn't Replace

Technical standards define **what the system is**. FRAMES defines **how we know it**.

```
WRONG: Replace XTCE Parameter with FRAMES Component
RIGHT: Wrap XTCE Parameter with FRAMES Provenance
```

### 7.2 Provenance Never Discarded

Even when exporting to pure XTCE (for tool compatibility), provenance is:
- Stored separately in the library
- Optionally included as XTCE AncillaryData
- Always retrievable via source_snapshot_id

### 7.3 Standards First, Extensions Second

When a standard element exists (XTCE Parameter, SysML Block), use it. Only use custom FRAMES elements for:
- Organizational layer (no standard exists)
- Epistemic metadata (FRAMES contribution)
- Coupling strength (FRAMES contribution)

### 7.4 Export Clean, Store Rich

```
EXPORT: Clean XTCE/SysML that standard tools can read
STORE:  Rich FRAMES-wrapped data with full provenance
```

---

## 8. File Structure (Proposed)

```
production/
├── schemas/
│   ├── extraction_schema.json      # Current: FRAMES extraction
│   ├── xtce/
│   │   └── xtce_1.2.xsd            # XTCE schema
│   ├── sysml/
│   │   └── kerml_types.json        # SysML v2 type definitions
│   └── frames/
│       ├── provenance_schema.json  # FRAMES provenance envelope
│       └── coupling_schema.json    # FRAMES coupling definition
│
├── serializers/
│   ├── xtce_serializer.py          # Export to XTCE XML
│   ├── sysml_serializer.py         # Export to SysML v2
│   ├── fprime_serializer.py        # Export to FPrime topology
│   └── frames_serializer.py        # Export FRAMES provenance
│
├── domain/
│   ├── technical/
│   │   ├── xtce_models.py          # XTCE dataclasses
│   │   ├── sysml_models.py         # SysML v2 dataclasses
│   │   └── fprime_models.py        # FPrime dataclasses
│   └── frames/
│       ├── provenance.py           # FRAMES provenance model
│       ├── coupling.py             # FRAMES coupling model
│       └── epistemic.py            # Epistemic dimension model
│
└── Version 3/
    ├── extractor_v3.py             # Extracts with FRAMES metadata
    ├── validator_v3.py             # Validates with schema
    └── storage_v3.py               # Stores with provenance
```

---

## 9. Summary

| Question | FRAMES Answer | Technical Answer |
|----------|---------------|------------------|
| What is the system? | - | XTCE, SysML, FPrime |
| How do we know this? | 7-question checklist | - |
| Who learned it? | Observer tracking | - |
| Will it transfer? | Formalizability dimension | - |
| Is it still valid? | Temporality, staleness | - |
| How strong is the bond? | Coupling strength | - |
| Can tools read it? | - | Standard formats |

**FRAMES is the provenance layer. MBSE standards are the technical layer. Together, they form a knowledge library that survives organizational turnover while remaining interoperable with industry tools.**

---

## 10. Related Documents

- [CANON.md](../canon/CANON.md) - Core principles and lessons learned
- [ONTOLOGY.md](../canon/ONTOLOGY.md) - FRAMES ontology for agent prompts
- [KNOWLEDGE_CAPTURE_CHECKLIST.md](../canon/KNOWLEDGE_CAPTURE_CHECKLIST.md) - 7-question checklist
- [KNOWLEDGE_FRAMEWORK.md](../canon/KNOWLEDGE_FRAMEWORK.md) - Epistemic dimension theory
- [REFACTORING_ROADMAP.md](REFACTORING_ROADMAP.md) - Implementation phases
