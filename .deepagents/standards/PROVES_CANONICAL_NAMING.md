# PROVES Canonical Naming and Type System

**Purpose:** Define the canonical PROVES naming and typing system that is stable, internally coherent, evidence-backed, and explicitly mappable to industry standards (XTCE, PyG, SysML v2).

**Status:** Proposed canonical vocabulary based on standards alignment study

**Date:** 2026-01-15

---

## 1. Current PROVES Entity Types

### 1.1 Inventory

Based on Migration 014 and Knowledge Graph Schema, PROVES currently recognizes these `entity_type` values:

| `entity_type` | Added | Source | Status |
|---------------|-------|--------|--------|
| `component` | Base schema | Original design | ✅ In use |
| `port` | Migration 014 | F' modeling | ✅ In use |
| `dependency` | Migration 014 | ERV relationships | ✅ In use |
| `connection` | Migration 014 | Port wiring | ✅ In use |
| `parameter` | Migration 014 | Telemetry/config values | ✅ In use |
| `command` | Migration 014 | Telecommands | ✅ In use |
| `telemetry` | Migration 014 | Downlink data | ✅ In use |
| `event` | Migration 014 | Event messages | ✅ In use |
| `data_type` | Migration 014 | Type definitions | ✅ In use |

**Total:** 9 entity types

### 1.2 Usage Context

**From Knowledge Graph Schema:**
- `SoftwareComponent` - Active/passive/queued components
- `PortType` - Input/output/bidirectional interfaces
- `HardwareElement` - Boards, sensors, MCUs
- `Resource` - Power, thermal, bandwidth, compute
- `Procedure` - Build, integration, test, ops
- `FailureMode` - Critical/high/medium/low severity

**Note:** Knowledge Graph Schema uses different terminology than `entity_type` enum - this needs reconciliation.

---

## 2. Standards Collision Analysis

### 2.1 XTCE/YAMCS Alignment

| PROVES Type | XTCE Equivalent | Collision Risk | Notes |
|-------------|-----------------|----------------|-------|
| `component` | SpaceSystem (subsystem) | ⚠️ **Adjacent** | XTCE uses "SpaceSystem", not "Component" |
| `port` | Parameter or Argument | ⚠️ **Context-dependent** | XTCE distinguishes by direction |
| `parameter` | Parameter | ✅ **Aligned** | Exact match if used for telemetry |
| `command` | MetaCommand | ⚠️ **Name mismatch** | XTCE calls it "MetaCommand", not "Command" |
| `telemetry` | Parameter | ⚠️ **Overlaps** | XTCE uses "Parameter" for telemetry |
| `event` | Parameter (event) | ⚠️ **Adjacent** | XTCE models events as special Parameters |
| `data_type` | ParameterType/ArgumentType | ✅ **Aligned** | Conceptually aligned |
| `dependency` | (none) | ✅ **Novel** | XTCE doesn't model dependencies |
| `connection` | (none) | ✅ **Novel** | XTCE doesn't model component wiring |

**Findings:**
- ⚠️ **"parameter" vs "telemetry"**: XTCE uses "Parameter" for both - PROVES distinguishes them
- ⚠️ **"command"**: XTCE calls it "MetaCommand"
- ✅ **"dependency", "connection"**: PROVES-native concepts (good!)

### 2.2 PyTorch Geometric Alignment

| PROVES Type | PyG Equivalent | Collision Risk | Notes |
|-------------|----------------|----------------|-------|
| `component` | Node type `'component'` | ✅ **Aligned** | Direct mapping |
| `port` | Node type `'port'` | ✅ **Aligned** | Direct mapping |
| `dependency` | Edge type `'depends_on'` | ⚠️ **Name difference** | PyG uses verb phrases for edges |
| `connection` | Edge type `'connected_to'` | ⚠️ **Name difference** | PyG uses verb phrases for edges |
| `parameter` | Node type or attribute | ⚠️ **Context-dependent** | Could be node or feature |
| `command` | Node type or attribute | ⚠️ **Context-dependent** | Could be node or feature |
| `telemetry` | Node type or attribute | ⚠️ **Context-dependent** | Could be node or feature |
| `event` | Node type or attribute | ⚠️ **Context-dependent** | Could be node or feature |
| `data_type` | Feature encoding metadata | ✅ **Not a node** | Correctly not a graph entity |

**Findings:**
- ✅ **Node types**: `component`, `port` work well
- ⚠️ **Edge types**: PROVES uses nouns (`dependency`, `connection`), PyG prefers verbs (`depends_on`, `connected_to`)
- ⚠️ **Parameter/Command/Telemetry**: Ambiguous whether these are nodes or attributes

### 2.3 SysML v2 Alignment

| PROVES Type | SysML v2 Equivalent | Collision Risk | Notes |
|-------------|---------------------|----------------|-------|
| `component` | PartDefinition | ⚠️ **Name difference** | SysML v2 uses "Part", not "Component" |
| `port` | PortDefinition/PortUsage | ✅ **Aligned** | Exact terminology match |
| `dependency` | Dependency relationship | ✅ **Aligned** | SysML has Dependency construct |
| `connection` | ConnectionUsage | ⚠️ **Name difference** | SysML uses "Connection", not "Connection" (OK) |
| `parameter` | AttributeUsage | ⚠️ **Name difference** | SysML uses "Attribute" for properties |
| `command` | ActionUsage or PortUsage | ⚠️ **Context-dependent** | Could be action or input port |
| `telemetry` | PortUsage (output) | ⚠️ **Context-dependent** | Likely output port or item flow |
| `event` | EventOccurrence | ⚠️ **Adjacent** | SysML has events in state machines |
| `data_type` | AttributeDefinition/ItemDefinition | ✅ **Aligned** | Conceptually aligned |

**Findings:**
- ⚠️ **"component" vs "part"**: SysML v2 systematically uses "Part", not "Component"
- ✅ **"port"**: Perfect alignment
- ⚠️ **"parameter" vs "attribute"**: SysML uses "Attribute" for properties

---

## 3. Naming Collision Summary

### 3.1 Critical Issues

**Issue 1: "parameter" Overloading**

**Problem:**
- PROVES: `parameter` = telemetry value OR configuration parameter
- XTCE: `Parameter` = telemetry value ONLY (commands use `Argument`)
- SysML: `AttributeUsage` = property/characteristic

**Ambiguity:** Is a PROVES `parameter`:
- A telemetry value (aligns with XTCE `Parameter`)?
- A configuration property (aligns with SysML `AttributeUsage`)?
- Both?

**Decision needed:** Define clear boundary

---

**Issue 2: "telemetry" vs "parameter" Overlap**

**Problem:**
- PROVES has BOTH `parameter` and `telemetry`
- XTCE uses ONLY `Parameter` for telemetry values
- PyG/SysML don't distinguish these

**Ambiguity:** What's the difference between:
- `entity_type='parameter'`
- `entity_type='telemetry'`

**Decision needed:** Are these synonyms, or do they mean different things?

---

**Issue 3: "component" vs Standards Terminology**

**Problem:**
- PROVES: `component`
- XTCE: `SpaceSystem` (at subsystem level)
- PyG: Node type (any name works)
- SysML v2: `PartDefinition` (systematic terminology)

**Trade-off:**
- Keep "component" (familiar to F' users)
- Change to "part" (aligns with SysML v2)

**Decision needed:** Stability vs alignment

---

**Issue 4: "dependency" and "connection" as Entities**

**Problem:**
- PROVES models dependencies and connections as entities (nodes in database)
- PyG models them as edges (not nodes)
- SysML models them as relationships (not parts)
- XTCE doesn't model them at all

**Current PROVES Design:**
- `entity_type='dependency'` → Entity in `core_entities` table
- `entity_type='connection'` → Entity in `core_entities` table

**Standards Expectation:**
- Relationships should be in relationship table, not entity table

**Decision needed:** Are dependencies/connections entities or relationships?

---

### 3.2 Minor Issues

**Issue 5: "command" vs "MetaCommand"**

**Impact:** Low - name difference is minor, concept aligns

**Issue 6: "event" Context-Dependency**

**Impact:** Low - most standards have some event concept

**Issue 7: "data_type" as Entity**

**Impact:** Low - correctly identified as metadata, not structural

---

## 4. PROVES Canonical Naming Proposals

### 4.1 Proposal A: Minimal Change (Conservative)

**Philosophy:** Keep current names, clarify boundaries through documentation

**Changes:**
- None to `entity_type` enum values
- Add documentation defining clear boundaries

**"parameter" vs "telemetry" Boundary:**
- `parameter` = **Configuration parameter** (writable, persists across reboots)
- `telemetry` = **Telemetry value** (read-only sensor data, status)

**"dependency" as Entity:**
- Keep as entity type
- Note in `standard_constraints`: "Not exportable to XTCE; maps to PyG edge"

**Pros:**
- No breaking changes
- Minimal migration effort
- Backward compatible

**Cons:**
- Doesn't align terminology with SysML v2
- `parameter` name still ambiguous with XTCE
- Dependency/connection as entities is non-standard

---

### 4.2 Proposal B: Align with SysML v2 (Aggressive)

**Philosophy:** Rename types to match SysML v2 terminology for long-term alignment

**Changes:**

| Current | Proposed | Reason |
|---------|----------|--------|
| `component` | `part` | Aligns with SysML v2 `PartDefinition` |
| `port` | `port` | ✅ Already aligned |
| `parameter` | `attribute` | Aligns with SysML v2 `AttributeUsage` |
| `telemetry` | `telemetry` | Keep (PROVES-specific distinction) |
| `command` | `command` | Keep (close enough to `MetaCommand`) |
| `event` | `event` | Keep |
| `data_type` | `data_type` | Keep |
| `dependency` | **Remove** (move to relationships) | Align with all standards |
| `connection` | **Remove** (move to relationships) | Align with all standards |

**Dependency/Connection Handling:**
- Remove from `entity_type` enum
- Store in `staging_relationships` table (already exists!)
- Promote to `core_relationships` table (new)

**Pros:**
- Strong SysML v2 alignment
- Cleaner separation of entities vs relationships
- More standard-conformant architecture

**Cons:**
- ⚠️ **Breaking change** - requires migration
- Renames familiar terms
- Disrupts existing extractions

---

### 4.3 Proposal C: Hybrid Approach (Recommended)

**Philosophy:** Clarify boundaries, minimize breaking changes, add new types selectively

**Phase 1 Changes (Immediate):**

1. **Clarify "parameter" vs "telemetry"**
   - `parameter` = **Configuration parameter or command argument**
     - Writeable values
     - Command inputs
     - Configuration properties
   - `telemetry` = **Telemetry channel or sensor reading**
     - Read-only downlink data
     - Status indicators
     - Event messages

2. **Keep "component" name**
   - Familiar to F' ecosystem
   - Works fine with PyG
   - Document mapping to SysML v2 `PartDefinition` in `standard_constraints`

3. **Keep "dependency" and "connection" as entities**
   - They ARE entities in PROVES knowledge graph (first-class citizens)
   - Document in `standard_constraints`: `"export_as": "edge"` for PyG/SysML
   - Note: "Not exportable to XTCE"

**Phase 2 Changes (Later, if needed):**

4. **Add optional alias system**
   - Allow multiple names for same concept
   - Example: `component` internally, but can query as `part`
   - Implemented via `knowledge_enrichment` table `alias` records

**Pros:**
- ✅ Minimal breaking changes
- ✅ Clear semantic boundaries
- ✅ Standards-mappable via `standard_constraints`
- ✅ Preserves PROVES-native concepts

**Cons:**
- Doesn't rename to match SysML v2 exactly
- Requires good documentation discipline

---

## 5. Recommended Canonical Vocabulary

### 5.1 Final Entity Types (Proposal C)

| `entity_type` | Definition | XTCE Mapping | PyG Mapping | SysML v2 Mapping |
|---------------|------------|--------------|-------------|------------------|
| `component` | Software or hardware module with defined interface | SpaceSystem | Node `'component'` | PartDefinition |
| `port` | Interface point on component (input/output/bidirectional) | Parameter (out) or Argument (in) | Node `'port'` | PortDefinition |
| `parameter` | Configuration parameter or command argument value | Argument (in command) | Node attribute or Node type | AttributeUsage |
| `telemetry` | Telemetry channel or downlink data value | Parameter | Node attribute or Node type | PortUsage (output) |
| `command` | Telecommand or action | MetaCommand | Node type or edge label | ActionUsage or PortUsage (input) |
| `event` | Event message or notification | Parameter (event severity) | Node type | EventOccurrence |
| `data_type` | Type definition (int32, float, enum, struct) | ParameterType or ArgumentType | Feature encoding metadata | AttributeDefinition or ItemDefinition |
| `dependency` | Component A depends on Component B (relationship as entity) | Not exported | Edge `('component', 'depends_on', 'component')` | Dependency relationship |
| `connection` | Port-to-port connection (relationship as entity) | Not exported | Edge `('port', 'connected_to', 'port')` | ConnectionUsage |

### 5.2 Type Boundaries and Decision Rules

**When to use `component`:**
- Software components (F' active/passive/queued)
- Hardware elements (boards, sensors, MCUs)
- Subsystems
- External systems
- **NOT:** Ports, parameters, data types

**When to use `port`:**
- Interface points on components
- Command ports, telemetry ports, data ports
- Has direction (input/output/bidirectional)
- **NOT:** The data flowing through the port (that's parameter/telemetry/command)

**When to use `parameter`:**
- Configuration parameters (writable, persistent)
- Command arguments (inputs to commands)
- Properties of components
- **NOT:** Telemetry values (use `telemetry`)
- **NOT:** Commands themselves (use `command`)

**When to use `telemetry`:**
- Sensor readings
- Status indicators
- Downlink data channels
- Telemetry packet contents
- **NOT:** Configuration parameters (use `parameter`)

**When to use `command`:**
- Telecommands (uplink)
- Actions/behaviors
- Operations that change state
- **NOT:** Command arguments (use `parameter`)

**When to use `event`:**
- Event log messages
- Notifications
- State change announcements
- Severity-based alerts (INFO, WARNING, ERROR)
- **NOT:** Regular telemetry (use `telemetry`)

**When to use `data_type`:**
- Type definitions (schemas)
- Enumerations
- Struct definitions
- Units and constraints
- **NOT:** Instances of the type (use appropriate entity type)

**When to use `dependency`:**
- "Component A requires Component B"
- "Module X depends on Library Y"
- Hard dependencies (cannot function without)
- **Stored as:** Entity in `core_entities` with `entity_type='dependency'`
- **Exported as:** Edge/relationship in graph standards

**When to use `connection`:**
- "Port A connects to Port B"
- Data flow path between ports
- Wiring between interfaces
- **Stored as:** Entity in `core_entities` with `entity_type='connection'`
- **Exported as:** Edge/relationship in graph standards

---

## 6. Naming Conventions

### 6.1 Entity Type Names

**Convention:** Lowercase, singular nouns, underscores for multi-word

**Examples:**
- ✅ `component`, `port`, `parameter`
- ✅ `data_type` (multi-word with underscore)
- ❌ `components` (plural)
- ❌ `Component` (capitalized)

**Rationale:** Matches database enum style, PyG node type conventions

### 6.2 Canonical Key Naming

**Convention:** PascalCase for component names, descriptive identifiers

**Examples:**
- `RadioDriver`
- `PowerMonitor`
- `I2cBus`
- `BatteryVoltage`

**For parameters/telemetry:**
- `batteryVoltage` (camelCase) or
- `battery_voltage` (snake_case) or
- `BatteryVoltage` (PascalCase)

**Decision:** Allow flexibility - extraction agents may use different conventions based on source ecosystem (F' uses PascalCase, ROS2 uses snake_case)

### 6.3 Namespace Conventions

**Format:** Hierarchical path with forward slashes or dots

**Examples:**
- `CommunicationsSubsystem/RadioDriver`
- `PowerSubsystem.BatteryMonitor`
- `Sensors/Temperature/TMP117`

**Mapping to Standards:**
- XTCE: `/PROVES/CommunicationsSubsystem/RadioDriver`
- PyG: Graph metadata `graph_id="fprime_v3.4.3"`
- SysML v2: `package CommunicationsSubsystem { part def RadioDriver }`

---

## 7. Candidate Type Discipline

### 7.1 Extraction Agent Rules

**Rule 1: No Ambiguous Types**
- Extraction agents MUST use canonical `entity_type` values
- No ad-hoc or invented types allowed
- If unsure, flag for human review (don't guess)

**Rule 2: Type Evidence Required**
- `candidate_type` assignment must have supporting evidence in `evidence_text`
- Include rationale in extraction reasoning

**Rule 3: Consistent Naming**
- Same entity extracted from different sources must get same `candidate_type`
- Use `entity_alias` table for alternate names

**Rule 4: Boundary Enforcement**
- If entity could be multiple types (e.g., parameter vs telemetry), choose based on:
  - Direction: Input → parameter, Output → telemetry
  - Mutability: Writable → parameter, Read-only → telemetry
  - Context: Command argument → parameter, Sensor value → telemetry

### 7.2 Human Review Triggers

**Mandatory review when:**
- `candidate_type` = (ambiguous/unknown)
- Multiple extractions assign different types to same `canonical_key`
- Type doesn't match expected pattern (e.g., parameter with no value type)

### 7.3 Type Promotion Rules

**From `staging_extractions` to `core_entities`:**
- `candidate_type` → `entity_type` (cast to enum)
- If `candidate_type` not in enum, promotion fails (human must fix)
- Verification status must be `human_verified` or `auto_approved`

---

## 8. Standards Mapping Strategy

### 8.1 Mapping Categories

**Aligned (1:1):**
- Direct export with no transformation
- Examples: `port` → XTCE Parameter/Argument, `data_type` → SysML AttributeDefinition

**Adjacent (Context-Dependent):**
- Requires context from `standard_constraints` to map correctly
- Examples: `parameter` (config vs command arg), `command` (action vs port)

**Novel (PROVES-Specific):**
- No direct equivalent in standard
- Examples: `dependency`, `connection` (as entities, not relationships)
- Export strategy: Skip for XTCE, export as edges for PyG/SysML

### 8.2 Multi-Standard Export Priority

**Priority 1: XTCE (Mission Control)**
- Export: `component`, `port`, `parameter`, `command`, `telemetry`, `event`, `data_type`
- Skip: `dependency`, `connection`

**Priority 2: PyTorch Geometric (ML)**
- Export all entity types as nodes or edges
- `dependency` → edge `('component', 'depends_on', 'component')`
- `connection` → edge `('port', 'connected_to', 'port')`

**Priority 3: SysML v2 (MBSE)**
- Export: `component` → PartDefinition, `port` → PortDefinition
- `dependency` → Dependency relationship
- `connection` → ConnectionUsage

### 8.3 Exporter Constraints

**Rule 1: No Renaming**
- Use PROVES `canonical_key` as-is
- Map to standard type via `standard_key` in `knowledge_enrichment`

**Rule 2: Fail Loudly**
- If entity lacks required mapping, exporter MUST error (not guess)
- Example: Exporting to XTCE without knowing if parameter is input/output

**Rule 3: Read Mappings from Database**
- Query `standard_mappings` view for each entity
- Use `standard_constraints` JSONB for context-dependent decisions

---

## 9. Open Questions and Future Decisions

### 9.1 Remaining Ambiguities

**Q1: Should "parameter" and "telemetry" be merged?**

**Current:** Separate types
**Alternative:** Single `signal` or `value` type with attribute distinguishing direction
**Decision:** TBD - keep separate for now, revisit after extraction usage patterns observed

---

**Q2: Should "dependency" and "connection" move to relationships table?**

**Current:** Entities in `core_entities`
**Alternative:** Relationships in `staging_relationships` / new `core_relationships`
**Trade-off:**
- Entities: Easier to query, can have attributes (ERV metadata)
- Relationships: More standard-conformant, cleaner separation
**Decision:** TBD - keep as entities for now (they ARE first-class knowledge)

---

**Q3: Should we add "interface" or "contract" type?**

**Use case:** Representing F' port definitions or API contracts
**Current:** Could be modeled as `data_type` or `port`
**Decision:** TBD - observe extraction patterns

---

**Q4: How to handle "resource" from Knowledge Graph Schema?**

**Knowledge Graph Schema defines:** Power, thermal, bandwidth, compute resources
**Current `entity_type` enum:** No `resource` type
**Options:**
1. Add `resource` type
2. Model as `component` with special attributes
3. Keep in knowledge graph docs only (not extracted)
**Decision:** TBD

---

**Q5: How to handle "procedure" from Knowledge Graph Schema?**

**Knowledge Graph Schema defines:** Build, integration, test, ops procedures
**Current `entity_type` enum:** No `procedure` type
**Options:**
1. Add `procedure` type
2. Model as `command` or `action`
3. Keep in knowledge graph docs only
**Decision:** TBD

---

### 9.2 Standards Evolution Risks

**Risk 1: XTCE v2.0**
If XTCE releases v2.0 with new terminology, re-evaluate alignment

**Risk 2: SysML v3.0**
SysML v2 is still stabilizing - monitor for vocabulary changes

**Risk 3: PyG Evolution**
PyTorch Geometric may add new conventions - stay updated

**Mitigation:** Version all `standard_version` fields in `knowledge_enrichment`

---

## 10. Implementation Checklist

### 10.1 Immediate Actions (Week 3)

- [x] ✅ Document current `entity_type` values
- [x] ✅ Identify collisions with XTCE, PyG, SysML v2
- [x] ✅ Define canonical naming rules
- [ ] 🔲 Update extraction agent prompts with type boundaries
- [ ] 🔲 Add validation in promotion logic to enforce type enum
- [ ] 🔲 Document `standard_constraints` JSONB schema for each standard

### 10.2 Documentation Updates Needed

- [ ] 🔲 Update `docs/architecture/KNOWLEDGE_GRAPH_SCHEMA.md` to align with `entity_type` enum
- [ ] 🔲 Create extraction agent guide: "How to Choose the Right Type"
- [ ] 🔲 Document ERV attributes for `dependency` entities
- [ ] 🔲 Document connection metadata for `connection` entities

### 10.3 Future Work (Week 4+)

- [ ] 🔲 Observe extraction patterns to validate type boundaries
- [ ] 🔲 Collect ambiguous cases for human review
- [ ] 🔲 Refine `parameter` vs `telemetry` boundary based on real usage
- [ ] 🔲 Decide on `resource` and `procedure` types
- [ ] 🔲 Consider alias system for multi-vocabulary support

---

## 11. Summary and Recommendations

### 11.1 Canonical Vocabulary

**PROVES defines 9 entity types:**

1. `component` - Software/hardware modules
2. `port` - Interface points (input/output)
3. `parameter` - Configuration parameters, command arguments
4. `telemetry` - Telemetry channels, sensor readings
5. `command` - Telecommands, actions
6. `event` - Event messages, notifications
7. `data_type` - Type definitions, schemas
8. `dependency` - Dependency relationships (stored as entities)
9. `connection` - Port connections (stored as entities)

### 11.2 Key Decisions

**Decision 1: Keep Current Names**
- Minimal breaking changes
- Align to standards via `standard_mapping` in database
- Document clear type boundaries

**Decision 2: Clarify Parameter vs Telemetry**
- `parameter` = writable configuration or command input
- `telemetry` = read-only downlink data

**Decision 3: Dependencies/Connections as Entities**
- Keep as entities (first-class knowledge with attributes)
- Export as edges/relationships for graph standards
- Use `standard_constraints` to record export strategy

**Decision 4: No Renames to Match SysML v2**
- "component" stays "component" (not renamed to "part")
- Mapping handled in `knowledge_enrichment` table
- Preserves F' ecosystem familiarity

### 11.3 Success Criteria

✅ **Stable:** Names won't change in future migrations
✅ **Coherent:** Clear boundaries between types
✅ **Evidence-backed:** Based on standards alignment study
✅ **Mappable:** Explicit mappings to XTCE, PyG, SysML v2

---

## 12. References

**PROVES Documentation:**
- `.deepagents/standards/XTCE_VOCABULARY.md` - XTCE alignment study
- `.deepagents/standards/PYTORCH_GEOMETRIC_VOCABULARY.md` - PyG alignment study
- `.deepagents/standards/SYSML_V2_VOCABULARY.md` - SysML v2 alignment study
- `docs/architecture/KNOWLEDGE_GRAPH_SCHEMA.md` - Original ERV design
- `neon-database/migrations/014_add_missing_entity_types.sql` - Current entity types

**Standards:**
- XTCE 1.2 (CCSDS): https://ccsds.org/Pubs/660x0b2.pdf
- PyTorch Geometric: https://pytorch-geometric.readthedocs.io/
- SysML v2 (OMG): https://www.omg.org/sysml/sysmlv2/

---

**Status:** Canonical naming defined. Ready for extraction agent updates and mapping strategy consolidation.
