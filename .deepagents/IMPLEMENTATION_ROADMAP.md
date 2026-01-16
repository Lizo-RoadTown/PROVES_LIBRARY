# PROVES Integration-Ready Implementation Roadmap

Making PROVES easily integratable through best practices, not format exports.

**Current Phase:** Naming and Standards Alignment (Week 3)

---

## Week 1-2: Domain Models Foundation ✅ COMPLETE

**Goal:** Separate domain logic from storage implementation.

### Completed Tasks ✅

1. **✅ Domain models created** (`production/core/domain/`)
   - `core_entity.py` - Human-verified entities
   - `frames_dimensions.py` - FRAMES epistemic metadata value object
   - `raw_snapshot.py` - Source documentation snapshots
   - Entity type discipline defined

2. **✅ Standard identifiers implemented** (`production/core/identifiers.py`)
   - URI format: `http://proves.space/{ecosystem}/{entity_type}/{key}`
   - URN format: `urn:proves:{ecosystem}:{entity_type}:{key}`
   - 41 passing tests

3. **✅ Repository pattern established** (`production/core/repositories/`)
   - Abstract `CoreEntityRepository` interface
   - Concrete `PostgresCoreEntityRepository` (read-only)
   - Abstract `RawSnapshotRepository` interface
   - Concrete `PostgresRawSnapshotRepository` (read-only)
   - 98 repository tests passing

4. **✅ Standards mapping infrastructure** (Migration 015)
   - `knowledge_enrichment` table with `standard_mapping` type
   - Fields for recording vocabulary mappings (not implementing exports)
   - Helper function `add_standard_mapping()`

**Deliverable:** ✅ 111 passing tests, zero pipeline changes, foundation for alignment work

**Status:** Domain models ready for standards alignment study

---

## Week 3: Naming and Standards Alignment ⏳ IN PROGRESS

**Goal:** Establish a canonical PROVES naming and typing system that is:
- Stable
- Internally coherent
- Evidence-backed
- Explicitly mappable to industry standards

**NOT building:** Code-heavy deliverables, exporters, serializers
**ACTUALLY doing:** Naming rules, alignment tables, mapping strategy

### Phase Outputs (Conceptual, Not Code)

1. **Naming & Typing Rules**
   - What counts as Parameter vs Telemetry
   - When something is a Component vs Port
   - Where ambiguity is allowed vs forbidden
   - `candidate_type` discipline

2. **Standards Alignment Tables**
   - PROVES term → XTCE/YAMCS term (if aligned)
   - PROVES term → MBSE/SysML concept (if aligned)
   - PROVES term → PyG/ML concept (if aligned)
   - PROVES term → **no match** (explicitly novel)

3. **Mapping Strategy**
   - **Aligned**: PROVES term maps 1:1 to standard
   - **Adjacent**: PROVES term is similar but not exact
   - **Novel**: PROVES concept has no standard equivalent
   - What gets mapped vs what stays PROVES-native

4. **Constraints on Future Exporters**
   - "Exporters may not rename"
   - "Exporters may only read canonical identity + mappings"
   - "Exporters must fail loudly if mappings are missing"

### Current Tasks

1. **XTCE/YAMCS Vocabulary Study**
   - Parameter vs MetaCommand distinctions
   - Namespace and container organization
   - Alignment table: PROVES → XTCE

2. **PyTorch Geometric Vocabulary Study**
   - Node types and feature expectations
   - Edge types and relationship modeling
   - Alignment table: PROVES → PyG

3. **SysML v2 Vocabulary Study**
   - Block vs Part vs Port constructs
   - Dependency and relationship types
   - Alignment table: PROVES → SysML

4. **PROVES Canonical Naming**
   - Review current `entity_type` enum values
   - Identify collisions with standards
   - Define stable PROVES-native names

**Deliverable:** Naming rules, alignment tables (not code), mapping strategy

**Status:** Ready to begin XTCE/YAMCS vocabulary study

---

## Future: Stabilization & Usage (Later)

**Goal:** Use canonical identities and mappings (NOT build exporters yet)

### What Happens After Alignment Stabilizes

1. **Naming becomes normative**
   - Extraction agents use canonical `entity_type` values
   - No more ambiguous or ad-hoc type names
   - Type boundaries enforced

2. **Mappings become queryable**
   - `knowledge_enrichment` table populated with alignment data
   - Views (`xtce_mappings`, `standard_mappings`) provide lookup
   - Alignment tables (aligned/adjacent/novel) documented

3. **Serializers can be built (MUCH LATER)**
   - Only AFTER mappings are stable
   - Read from alignment tables, not invented on-the-fly
   - Must fail loudly if mappings missing
   - No renaming allowed

**Current Phase Output:** Canonical language, not translators

---

## Key Principles

### Normalization ≠ Export

- **Normalization:** Stabilizes identity, fixes type, preserves meaning (CURRENT PHASE)
- **Export:** Is a view, happens later, should require zero renaming (FUTURE)

### Mental Model

This phase is "learning the languages so we don't invent an untranslatable dialect."

NOT: "Implementing adapters."

### Standards as Reference Vocabularies

We're studying:
