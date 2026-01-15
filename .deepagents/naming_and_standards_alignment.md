# Naming & Standards Alignment (Living Document)

> **Purpose**  
This document defines how PROVES names, types, and stabilizes knowledge **without locking itself to any single industry standard**, while remaining cleanly integratable with systems like **YAMCS / XTCE**, MBSE tooling, and ML frameworks.

This is a *living inquiry*, not a frozen spec. Decisions are recorded with rationale so future contributors understand *why* boundaries exist.

---

## 1. Core Principle (Non‑Negotiable)

**Canonical identity is PROVES‑native and stable.**  
External standards are *mappings*, not identities.

> We do **not** rename entities to match standards.  
> We **map** stable PROVES identities to external vocabularies.

This prevents:
- Rename cascades
- Broken references
- Knowledge drift across runs
- Re‑normalization churn

---

## 2. Two‑Layer Naming Model

### Layer 1: Canonical Identity (Internal)
Used everywhere inside PROVES.

**Fields**:
- `entity_type` (enum, required)
- `canonical_key` (stable, human‑legible)
- `ecosystem` (fprime, cubesat, ros2, etc.)
- Generated URI / URN

**Rules**:
- Never changes once promoted
- Not tied to any external standard’s naming quirks
- Designed for long‑term graph stability

Example:
```
entity_type: telemetry
canonical_key: battery_voltage
ecosystem: cubesat
URI: http://proves.space/cubesat/telemetry/battery_voltage
```

---

### Layer 2: Standards & Industry Mappings (External)
Used only when integrating or exporting.

**Stored as data**, not code logic.

Mappings answer questions like:
- “What does YAMCS / XTCE call this?”
- “What category does PyTorch Geometric expect?”
- “Is this aligned, adjacent, or novel relative to MBSE?”

Mappings may change over time **without breaking identity**.

---

## 3. Candidate Types as the Primary Boundary

Classification is **irreversible** and must happen at extraction.

**Why**:
- Standards mapping depends on type
- Storage defaults cannot recover lost class boundaries
- Later normalization cannot infer intent

### Required Canonical Types (non‑exhaustive)
- `component`
- `port`
- `parameter`
- `telemetry`
- `command`
- `event`
- `data_type`
- `connection`
- `dependency`

> If types collapse here, **standards alignment becomes impossible later**.

---

## 4. Relationship Between PROVES and MBSE

MBSE is treated as a **shared language**, not an authority.

PROVES asks:
- What does MBSE already name well?
- Where does PROVES need finer or different distinctions?
- What knowledge exists *before* it becomes formal MBSE?

### Mapping Posture
- **Aligned**: Same concept, different name → map
- **Adjacent**: Overlapping but not identical → annotate
- **Novel**: No standard equivalent → preserve PROVES term

No forced conformity.

---

## 5. YAMCS / XTCE Alignment (Conceptual)

YAMCS relies on XTCE for telemetry & command definitions.

Typical mappings (illustrative, not binding):

| PROVES Type | XTCE Concept |
|------------|--------------|
| telemetry  | Parameter (telemetry container) |
| parameter  | Parameter (config/calibration) |
| command    | MetaCommand |
| data_type  | ParameterType |

Structural concepts (`component`, `port`, `connection`) remain PROVES‑native and provide **context**, provenance, and lifecycle.

---

## 6. Machine Learning / GNN Alignment

ML frameworks do not care about names — they care about **structure and consistency**.

PROVES responsibilities:
- Stable node identity
- Stable type labels
- Consistent feature schema (e.g., FRAMES)

Standards knowledge here informs:
- Feature encoding
- Category grouping
- Interpretation — *not identity*

---

## 7. Where Standards Mappings Live

### Current Option
Reuse `knowledge_enrichment` with a new enrichment type:

- `standard_mapping`

Suggested fields:
- `standard` (xtce, yamcs, sysml, pyg, etc.)
- `standard_version`
- `standard_kind` (Parameter, MetaCommand, NodeType, etc.)
- `standard_name`
- `confidence`
- `notes`

### Future Option
Dedicated table:
```
entity_standard_mappings(
  entity_id,
  standard,
  standard_kind,
  standard_name,
  version,
  confidence,
  notes
)
```

---

## 8. Design Rule of Thumb

> **Normalize for truth. Map for interoperability.**

If you feel tempted to rename:
- Stop
- Ask whether this is identity or representation

If it’s representation → mapping
If it’s identity → it should have been caught at extraction

---

## 9. Open Questions (Living)

- Which XTCE distinctions matter operationally vs. semantically?
- When does a PROVES‑novel concept deserve its own mapping vs. remaining standalone?
- How should conflicting standards mappings be represented?
- What minimum mapping set is required before export is considered “valid”?

---

## 10. Status

- **State**: Draft / Active
- **Stability**: Medium
- **Change posture**: Amend via decision logs, not silent edits

---

*This document exists so future agents don’t “helpfully” collapse meaning.*

