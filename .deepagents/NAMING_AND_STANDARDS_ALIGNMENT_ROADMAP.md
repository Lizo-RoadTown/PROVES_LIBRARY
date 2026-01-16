# PROVES Naming and Standards Alignment Roadmap

**Current Phase:** Vocabulary alignment and mapping strategy documentation
**NOT implementing:** Exporters, serializers, or format converters

---

## Core Principle

**Normalization ≠ Export**

- **Normalization:** Stabilizes identity, fixes type, preserves meaning
- **Export:** Is a view, happens later, should require zero renaming

This phase is **preventive architecture** to avoid future normalization hell.

---

## Mental Model

"Learning the languages so we don't invent an untranslatable dialect."

NOT: "Implementing adapters."

---

## What We're Actually Doing

### ✅ Domain Model Files
**Purpose:** Define entity types, invariants, and canonical fields

**Status:** COMPLETE (Week 1-2)
- `production/core/domain/core_entity.py` - Verified entities
- `production/core/domain/frames_dimensions.py` - FRAMES epistemic metadata
- `production/core/domain/raw_snapshot.py` - Source snapshots
- Especially `candidate_type` discipline and entity type enums

**Deliverable:** Clear boundaries between Component, Port, Dependency, etc.

### ✅ Identifier System
**Purpose:** Stable URI/URN from (ecosystem, type, canonical_key)

**Status:** COMPLETE (Week 1-2)
- `production/core/identifiers.py`
- URI format: `http://proves.space/{ecosystem}/{entity_type}/{key}`
- URN format: `urn:proves:{ecosystem}:{entity_type}:{key}`

**Deliverable:** Permanent, dereferenceable identifiers that won't change

### ✅ Repository Pattern
**Purpose:** Isolate storage schema, enable testable normalization/mapping logic

**Status:** COMPLETE (Week 1-2)
- `production/core/repositories/postgres_core_entity_repository.py`
- `production/core/repositories/postgres_raw_snapshot_repository.py`
- Abstract interfaces for future implementations
- 111 passing tests, zero pipeline changes

**Deliverable:** Clean separation between domain logic and database

### ✅ Standards Mapping Infrastructure
**Purpose:** Store mappings to YAMCS/XTCE and ML vocabularies as data

**Status:** COMPLETE (Migration 015)
- `knowledge_enrichment` table with `standard_mapping` enrichment type
- Fields: `standard`, `standard_version`, `standard_key`, `standard_name`, `standard_constraints`
- Views: `xtce_mappings`, `standard_mappings`
- Helper function: `add_standard_mapping()`

**Deliverable:** Database support for recording vocabulary mappings

---

## Current Work: Vocabulary Alignment (Week 3)

### Phase 1: Standards Vocabulary Study

**Goal:** Understand how target standards name and categorize concepts

#### XTCE/YAMCS (Mission Control)
**Task:** Document XTCE vocabulary and category boundaries

**Deliverable:** `.deepagents/standards/XTCE_VOCABULARY.md`
- What XTCE calls a "Parameter" vs "MetaCommand"
- How XTCE organizes namespaces and containers
- XTCE subsystem boundaries
- Mapping strategy: PROVES types → XTCE types

#### PyTorch Geometric / GraphSAGE (Machine Learning)
**Task:** Document PyG vocabulary and graph structure expectations

**Deliverable:** `.deepagents/standards/PYTORCH_GEOMETRIC_VOCABULARY.md`
- Node types and feature expectations
- Edge types and relationship modeling
- Graph ID and versioning conventions
- Mapping strategy: PROVES entities → PyG nodes

#### SysML v2 (MBSE)
**Task:** Document SysML v2 vocabulary and modeling constructs

**Deliverable:** `.deepagents/standards/SYSML_V2_VOCABULARY.md`
- Block vs Part vs Port in SysML
- Dependency and relationship types
- Stereotype conventions
- Mapping strategy: PROVES types → SysML constructs

#### OWL/RDF (Semantic Web)
**Task:** Document OWL vocabulary and ontology patterns

**Deliverable:** `.deepagents/standards/OWL_VOCABULARY.md`
- Class vs Individual vs Property
- Ontology URI conventions
- Mapping strategy: PROVES types → OWL constructs

---

### Phase 2: PROVES Canonical Naming Design

**Goal:** Design PROVES-native names that align cleanly with standards

**Tasks:**

1. **Entity Type Review**
   - Review current `entity_type` enum values
   - Identify potential conflicts with standard vocabularies
   - Propose canonical PROVES names that don't collide

2. **Candidate Type Discipline**
   - Document when to use `component` vs `port` vs `dependency`
   - Define clear boundaries (aligned with standards where possible)
   - Create decision tree for extraction agents

3. **Naming Conventions**
   - Canonical key format standards
   - Ecosystem naming conventions
   - Namespace organization

**Deliverable:** `.deepagents/standards/PROVES_CANONICAL_NAMING.md`

---

### Phase 3: Mapping Strategy Documentation

**Goal:** Record how PROVES concepts map to each standard (as data, not code)

**Tasks:**

1. **Create Mapping Tables**
   - PROVES entity_type → XTCE type
   - PROVES entity_type → SysML construct
   - PROVES entity_type → PyG node type
   - PROVES entity_type → OWL class

2. **Document Edge Cases**
   - PROVES concepts with no standard equivalent (novel to PROVES)
   - Standard concepts with no PROVES equivalent (gaps to fill)
   - Many-to-many mappings (context-dependent)

3. **Constraint Documentation**
   - When namespace matters
   - When subsystem grouping applies
   - When version/revision affects mapping

**Deliverable:** `.deepagents/standards/MAPPING_STRATEGY.md`

---

### Phase 4: Populate Mapping Records (Data, Not Code)

**Goal:** Store mapping strategies in `knowledge_enrichment` table

**Tasks:**

1. **Define Standard Mapping Records**
   - Create example records for each standard
   - Document `standard_constraints` JSONB schema for each
   - Test `add_standard_mapping()` function

2. **Validation Rules**
   - What makes a valid XTCE mapping?
   - What makes a valid PyG mapping?
   - Constraint checking logic

**Deliverable:** Example mapping records in database, documented patterns

---

### Phase 5 (Optional): Extraction Agent Migration

**Goal:** Update extraction agents to use canonical naming

**Timing:** ONLY after alignment is stable

**Tasks:**
- Update deep extraction agent to use new domain models
- Ensure `candidate_type` follows canonical naming
- Test that extractions produce alignment-ready data

**Note:** This is NOT required for alignment phase. Can be deferred.

---

## Non-Goals (What We're NOT Doing)

❌ **Not building exporters** - No file generation for XTCE, SysML, PyG, OWL
❌ **Not building serializers** - No format conversion code
❌ **Not building pipelines** - No data movement automation
❌ **Not building adapters** - No runtime translation layers

**Only:** Vocabulary study, naming design, mapping strategy documentation

---

## Success Criteria

### For Vocabulary Alignment Phase:

✅ We understand how each standard names similar concepts
✅ We've identified where PROVES aligns naturally
✅ We've identified where PROVES has novel concepts
✅ We've designed canonical PROVES names that won't need renaming
✅ We've documented mapping strategies (not implemented them)
✅ We've stored example mapping records in database

### For Future Export Phase (Later):

When we eventually build exporters, they should:
- Require zero renaming of PROVES entities
- Work purely by querying `knowledge_enrichment` mappings
- Not need a "second normalization pipeline"
- Just transform structure, not semantics

---

## Timeline

**Week 3 (Current):**
- Day 1-2: XTCE/YAMCS vocabulary study
- Day 3: PyTorch Geometric vocabulary study
- Day 4: SysML v2 vocabulary study
- Day 5: OWL vocabulary study

**Week 4:**
- Day 1-2: PROVES canonical naming design
- Day 3-4: Mapping strategy documentation
- Day 5: Example mapping records in database

**Week 5+ (Optional):**
- Extraction agent migration to use canonical naming

---

## Current Status

| Component | Status | Deliverable |
|-----------|--------|-------------|
| Domain Models | ✅ Complete | `production/core/domain/` |
| Identifiers | ✅ Complete | `production/core/identifiers.py` |
| Repositories | ✅ Complete | `production/core/repositories/` |
| Mapping Infrastructure | ✅ Complete | Migration 015, `knowledge_enrichment` table |
| XTCE Vocabulary Study | ⏳ Next | `.deepagents/standards/XTCE_VOCABULARY.md` |
| PyG Vocabulary Study | 🔲 Pending | `.deepagents/standards/PYTORCH_GEOMETRIC_VOCABULARY.md` |
| SysML Vocabulary Study | 🔲 Pending | `.deepagents/standards/SYSML_V2_VOCABULARY.md` |
| OWL Vocabulary Study | 🔲 Pending | `.deepagents/standards/OWL_VOCABULARY.md` |
| Canonical Naming | 🔲 Pending | `.deepagents/standards/PROVES_CANONICAL_NAMING.md` |
| Mapping Strategy | 🔲 Pending | `.deepagents/standards/MAPPING_STRATEGY.md` |

---

## Key Architectural Rules

1. **No premature export** - Study vocabularies, don't implement converters
2. **Mappings as data** - Store in `knowledge_enrichment`, not in code
3. **Normalization first** - Get names right before building views
4. **Zero pipeline changes** - Don't touch extraction (Stages 1-3)
5. **Standards as reference** - Learn their language, don't invent our own

---

## Questions to Answer During Alignment

1. **Identity Conflicts:**
   - Do any PROVES `entity_type` values collide with standard names?
   - Which PROVES types are novel (no standard equivalent)?
   - Which standard types are missing from PROVES?

2. **Boundary Alignment:**
   - Does PROVES "Component" mean the same as XTCE "Subsystem"?
   - Does PROVES "Port" map cleanly to SysML "Port"?
   - Are PROVES "Dependencies" the same as PyG "Edges"?

3. **Naming Stability:**
   - Can we commit to current PROVES names long-term?
   - Will future standards force renaming?
   - Are we inventing names unnecessarily?

4. **Mapping Complexity:**
   - Are mappings always 1:1 or sometimes context-dependent?
   - When does namespace/subsystem/version matter?
   - What metadata must travel with mappings?

---

**Next Step:** Begin XTCE/YAMCS vocabulary study to understand mission control naming conventions.
