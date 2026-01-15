# PROVES Library Refactoring Roadmap

A systematic plan for introducing integration practices without breaking existing functionality.

**Guiding Principle:** Small, reversible changes with validation at each step.

---

## Part 1: Current State Assessment

### 1.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATION LAYER                          │
│                         (agent_v3.py)                               │
│                                                                     │
│   orchestrate_extraction(url, agents, config)                       │
│        │                                                            │
│        ├─→ Step 1: Extractor Agent                                  │
│        │      - Fetch webpage → raw_snapshots                       │
│        │      - Extract FRAMES couplings                            │
│        │      - Return snapshot_id + candidates                     │
│        │                                                            │
│        ├─→ Step 2: Validator Agent                                  │
│        │      - Verify lineage (evidence ↔ snapshot)                │
│        │      - Check duplicates (core_entities, staging)           │
│        │      - Validate epistemic structure                        │
│        │      - APPROVE or REJECT                                   │
│        │                                                            │
│        └─→ Step 3: Storage Agent                                    │
│               - Parse extraction data                               │
│               - Merge epistemic defaults + overrides                │
│               - Insert into staging_extractions                     │
│               - Return extraction_ids                               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        POSTGRESQL (Neon)                            │
│                                                                     │
│   raw_snapshots          - Source content with checksums            │
│   staging_extractions    - Awaiting human verification              │
│   core_entities          - Verified knowledge (truth layer)         │
│   pipeline_runs          - Execution tracking                       │
│   checkpoint_*           - LangGraph state persistence              │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 File Structure

```
production/
├── Version 3/                    # Current working version
│   ├── agent_v3.py              # Orchestration (Python control flow)
│   ├── extractor_v3.py          # Fetch + extract tools
│   ├── validator_v3.py          # Lineage + duplicate checking tools
│   ├── storage_v3.py            # Persistence tools
│   ├── subagent_specs_v3.py     # System prompts + tool bindings
│   └── process_extractions_v3.py # Entry point script
│
├── Version 2/                    # Previous iteration
│   └── ...
│
├── core/
│   ├── db_connector.py          # Database utilities
│   ├── graph_manager.py         # Graph operations
│   └── deep_extraction_agent.py # New deepagents integration (WIP)
│
├── curator/
│   ├── notion_sync.py           # Notion integration
│   ├── error_logger.py          # Error tracking
│   └── subagents/               # Original subagent implementations
│
└── scripts/
    ├── find_good_urls.py        # URL discovery
    ├── improvement_analyzer.py  # Self-analysis
    └── check_pending_extractions.py
```

### 1.3 What Works Well

| Component | Status | Notes |
|-----------|--------|-------|
| **Epistemic Framework** | ✅ Excellent | 7-question checklist, defaults+overrides pattern |
| **Lineage Verification** | ✅ Solid | SHA256 checksums, byte offsets, confidence tiers |
| **FRAMES Methodology** | ✅ Strong | Clear coupling extraction with 4 questions |
| **Duplicate Prevention** | ✅ Works | Checks both core_entities and staging |
| **Human-in-the-Loop** | ✅ Designed | Staging → Verification → Core flow |
| **Strict Enums** | ✅ Good | candidate_type, evidence_type constrained |
| **PostgreSQL Schema** | ✅ Mature | 14 migrations, comprehensive |

### 1.4 Current Issues

#### Issue 1: Path Dependencies (Fragility)

**Location:** All v3 files

**Problem:**
```python
# Every file has this pattern
version3_folder = Path(__file__).parent
project_root = version3_folder.parent.parent
production_root = project_root / 'production'
sys.path.insert(0, str(production_root))
sys.path.insert(0, str(version3_folder))
```

**Impact:**
- Moving files breaks imports
- IDE can't resolve imports properly
- Tests require specific working directory
- Refactoring is risky

**Severity:** 🔴 HIGH - Prevents safe refactoring

---

#### Issue 2: Database Coupling (Scattered Connections)

**Location:** `extractor_v3.py`, `validator_v3.py`, `storage_v3.py`

**Problem:**
```python
# Every tool opens its own connection
def get_db_connection():
    import psycopg
    from dotenv import load_dotenv
    project_root = os.path.abspath(...)
    load_dotenv(os.path.join(project_root, '.env'))
    db_url = os.environ.get('NEON_DATABASE_URL')
    return psycopg.connect(db_url)

# Then in every tool:
@tool
def some_tool():
    conn = get_db_connection()  # Opens new connection
    # ... do work
    conn.close()  # Manual cleanup
```

**Impact:**
- Connection pool not shared
- Environment loaded multiple times
- No transaction management across tools
- Hard to mock for testing
- Can't swap database backend

**Severity:** 🔴 HIGH - Prevents testing and integration

---

#### Issue 3: No Domain Layer (Business Logic + Persistence Mixed)

**Location:** Tool functions in extractor/validator/storage

**Problem:**
```python
@tool
def store_extraction(...):
    # Business logic (validation, transformation)
    # AND database operations (INSERT)
    # AND error handling
    # All in one function
```

**Impact:**
- Can't test business logic without database
- Can't serialize domain objects to other formats
- Can't reuse logic in different contexts
- Changes require understanding SQL + domain

**Severity:** 🟡 MEDIUM - Limits integration options

---

#### Issue 4: Implicit Contracts (Agent Communication)

**Location:** Between agents in orchestration

**Problem:**
```python
# Extractor outputs free-form text
extractor_result = agents["extractor"].invoke(...)
final_message = extractor_result["messages"][-1].content

# Validator parses that text
validator_task = f"""Validate the following extraction results:
{final_message}
"""

# Storage parses both outputs
storage_task = f"""Store the following VALIDATED extraction results:
{final_message}
VALIDATOR RESULTS:
{validator_message}
"""
```

**Impact:**
- No schema validation between agents
- Prompts must parse free-form text
- Format changes break downstream agents
- Hard to debug communication failures

**Severity:** 🟡 MEDIUM - Causes intermittent failures

---

#### Issue 5: No Standard Identifiers

**Location:** Throughout codebase

**Problem:**
```python
# Database IDs only
cur.execute("... RETURNING id")
staging_id = cur.fetchone()[0]  # Just an integer

# No URI/URN for external reference
# Can't link to external systems
# Can't merge with other knowledge graphs
```

**Impact:**
- Can't reference entities from external tools
- No Linked Data compatibility
- Graph exports lose identity
- Merging graphs is impossible

**Severity:** 🟡 MEDIUM - Blocks integration

---

#### Issue 6: No Schema Validation Layer

**Location:** Missing entirely

**Problem:**
```python
# Validation is in prompts, not code
# System prompt says "candidate_type must be..."
# But no runtime validation

# If agent produces wrong type, it goes to database
# Errors caught late (or not at all)
```

**Impact:**
- Invalid data can enter staging
- Debugging requires reading prompts
- No API documentation
- Can't auto-generate interfaces

**Severity:** 🟡 MEDIUM - Data quality risk

---

#### Issue 7: No Event System

**Location:** Missing entirely

**Problem:**
```python
# Operations happen silently
store_extraction(...)  # No notification

# Other systems can't react
# No audit trail of operations
# Can't build integrations
```

**Impact:**
- Can't notify external systems
- No real-time monitoring
- Integrations require polling
- Audit trail incomplete

**Severity:** 🟢 LOW - Nice to have

---

#### Issue 8: Version Folder Structure

**Location:** `production/Version 2/`, `production/Version 3/`

**Problem:**
```
production/
├── Version 2/   # Old code still present
├── Version 3/   # Current code
└── curator/     # Also has code?
```

**Impact:**
- Unclear which code is active
- Duplicated functionality
- Import confusion
- Maintenance burden

**Severity:** 🟢 LOW - Organizational issue

---

## Part 2: Refactoring Options

### Option A: Minimal Changes (Low Risk)

**Philosophy:** Fix the most painful issues without restructuring.

**Changes:**
1. ✅ Centralize database connection (single pool)
2. ✅ Add JSON schema validation at storage boundary
3. ✅ Add URI generation for exported entities
4. ⏸️ Keep existing file structure
5. ⏸️ Keep prompt-based contracts

**Effort:** 1-2 weeks
**Risk:** Low
**Integration Benefit:** Moderate

**Implementation:**
```python
# Step 1: Create shared db module
# production/core/database.py
from psycopg_pool import ConnectionPool

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = ConnectionPool(os.getenv('NEON_DATABASE_URL'), ...)
    return _pool

def get_connection():
    return get_pool().getconn()

# Step 2: Update all tools to use shared pool
# (Search/replace get_db_connection → get_connection)
```

---

### Option B: Domain Layer Introduction (Medium Risk)

**Philosophy:** Add abstraction layer without removing existing code.

**Changes:**
1. ✅ Everything from Option A
2. ✅ Create domain models (Component, Relationship, etc.)
3. ✅ Create repository interfaces
4. ✅ Wrap existing tools with domain layer
5. ⏸️ Keep existing orchestration
6. ⏸️ Keep existing prompts

**Effort:** 3-4 weeks
**Risk:** Medium
**Integration Benefit:** High

**Implementation:**
```python
# Step 1: Define domain models
# production/core/domain/extraction.py
@dataclass
class Extraction:
    candidate_type: str
    candidate_key: str
    raw_evidence: str
    epistemic_defaults: Dict
    epistemic_overrides: Dict
    # ...

    def to_uri(self) -> str:
        return f"http://proves.space/extraction/{self.candidate_key}"

    def validate(self) -> List[str]:
        """Return list of validation errors"""
        errors = []
        if self.candidate_type not in VALID_TYPES:
            errors.append(f"Invalid type: {self.candidate_type}")
        # ...
        return errors

# Step 2: Create repository interface
# production/core/repositories/extraction_repository.py
class ExtractionRepository(ABC):
    @abstractmethod
    def save(self, extraction: Extraction) -> str: pass

    @abstractmethod
    def find_by_key(self, key: str) -> Optional[Extraction]: pass

# Step 3: Implement for PostgreSQL
# production/core/repositories/postgres_extraction_repository.py
class PostgresExtractionRepository(ExtractionRepository):
    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    def save(self, extraction: Extraction) -> str:
        # Existing SQL logic
        pass

# Step 4: Update storage tool to use repository
@tool
def store_extraction(...):
    extraction = Extraction(...)
    errors = extraction.validate()
    if errors:
        return f"Validation failed: {errors}"
    repo = get_repository()  # Injected
    return repo.save(extraction)
```

---

### Option C: Full Architecture Refactor (High Risk)

**Philosophy:** Rebuild with integration-first design.

**Changes:**
1. ✅ Everything from Options A and B
2. ✅ Structured inter-agent communication (JSON schemas)
3. ✅ Event bus for all operations
4. ✅ Plugin system for storage backends
5. ✅ Proper Python package structure
6. ⚠️ Rewrite orchestration
7. ⚠️ Update all prompts

**Effort:** 6-8 weeks
**Risk:** High
**Integration Benefit:** Maximum

**Implementation:**
```
proves_library/
├── pyproject.toml
├── src/
│   └── proves/
│       ├── __init__.py
│       ├── domain/
│       │   ├── extraction.py
│       │   ├── component.py
│       │   └── relationship.py
│       ├── repositories/
│       │   ├── base.py
│       │   └── postgres.py
│       ├── agents/
│       │   ├── extractor.py
│       │   ├── validator.py
│       │   └── storage.py
│       ├── orchestration/
│       │   └── pipeline.py
│       ├── events/
│       │   └── bus.py
│       └── serializers/
│           ├── graphml.py
│           └── owl.py
└── tests/
    ├── unit/
    └── integration/
```

---

## Part 3: Recommended Approach

### Phase 1: Stabilize (Weeks 1-2)

**Goal:** Fix critical issues without changing behavior.

| Task | Risk | Benefit | Status |
|------|------|---------|--------|
| 1.1 Centralize database pool | Low | Eliminates connection leaks | **DONE** |
| 1.2 Add JSON schema for staging_extractions | Low | Catches invalid data | **DONE** |
| 1.3 Document current agent contracts | None | Enables future changes | **DONE** |
| 1.4 Add integration tests for current pipeline | Low | Prevents regressions | **DONE** |

**Completed:**
- `production/Version 3/database.py` - Centralized connection pool (singleton, thread-safe)
- `production/schemas/extraction_schema.json` - JSON schema with actual database enums
- `production/Version 3/schema_validator.py` - Schema validation module
- `.deepagents/AGENT_CONTRACTS.md` - Full agent contract documentation
- `production/Version 3/tests/test_contracts.py` - 25 integration tests (all passing)
- `production/Version 3/tests/test_database.py` - 8 database pool tests (all passing)
- `production/Version 3/tests/test_schema_validator.py` - 16 schema tests (all passing)

**Integrated into agent code:**
- `storage_v3.py` - Uses centralized pool + schema validation before INSERT
- `validator_v3.py` - Uses centralized pool
- `extractor_v3.py` - Uses centralized pool

**Curator scripts fixed (2026-01-15):**
- `production/curator/batch_promote_accepted.py` - Now uses centralized pool
- `production/curator/analyze_accepted_batch.py` - Now uses centralized pool
- `production/curator/subagents/url_fetcher.py` - Now uses centralized pool

**Connection pool configuration upgraded (2026-01-15):**
- `min_size`: 1 → 2 (keep warm connections)
- `max_size`: 5 → 20 (handle concurrent agent operations)
- `timeout`: 30s → 60s (handle busy periods)
- **Fix documented in:** `.deepagents/CONNECTION_POOL_FIX.md`

**Total tests: 49 passing**

**Live Validation (2026-01-15):**
- ✅ Ran `process_extractions_v3.py --limit 1` successfully
- ✅ Extracted and stored 2 entities from https://proveskit.github.io/pysquared/frozen-modules/
- ✅ No connection pool timeout errors (previously: "couldn't get a connection after 30 sec")
- ✅ Pool stats healthy: size=3, max=20, idle=2, in_use=0
- ✅ Lineage verification working
- ✅ Schema validation working
- **Result:** Stage 1 (Extraction) fully operational

---

### Phase 2: Promotion Layer (Already Implemented)

**Status:** ✅ COMPLETE (discovered during architecture review)

The promotion layer was already built before this roadmap was created:

| Component | Status | Location |
|-----------|--------|----------|
| `batch_promote_accepted.py` | ✅ Done | `production/curator/` |
| Hard matching (exact key + ecosystem) | ✅ Done | `promote_to_core()` in storage_v3.py |
| `core_entities` table with FRAMES dimensions | ✅ Done | Migration 009 |
| `knowledge_enrichment` table | ✅ Done | Migration 009 |
| `dimensional_adjustment_history` table | ✅ Done | Migration 009 |
| Promotion tracking columns | ✅ Done | Migration 013 |
| `promote_to_verified_knowledge()` function | ✅ Done | Migration 009 |

**FRAMES Dimensions in core_entities:**
- `knowledge_form` (embodied/inferred)
- `contact_level` (direct/mediated/indirect/derived)
- `directionality` (forward/backward/bidirectional)
- `temporality` (snapshot/sequence/history/lifecycle)
- `formalizability` (portable/conditional/local/tacit)
- `carrier` (body/instrument/artifact/community/machine)

---

### Phase 3: Standardization & Export (In Progress)

**Goal:** Export verified `core_entities` to industry-standard MBSE formats.

> **Key Insight:** Standards compliance happens AFTER human verification, not at extraction time.
> The extraction layer intentionally stays loose to capture gray areas.

#### Week 1-2: Domain Models Foundation ✅ COMPLETE (2026-01-15)

**Status:** 85 passing tests, zero pipeline changes

| Task | Status | Files Created |
|------|--------|---------------|
| 3.0a Stable identifiers (URI/URN) | ✅ Done | `production/core/identifiers.py` (41 tests) |
| 3.0b FRAMES dimensions model | ✅ Done | `production/core/domain/frames_dimensions.py` (16 tests) |
| 3.0c Provenance reference model | ✅ Done | `production/core/domain/provenance_ref.py` |
| 3.0d CoreEntity domain model | ✅ Done | `production/core/domain/core_entity.py` (16 tests) |
| 3.0e KnowledgeNode projection | ✅ Done | `production/core/domain/knowledge_node.py` (12 tests) |
| 3.0f Repository interfaces | ✅ Done | `production/core/repositories/*.py` |
| 3.0g PostgreSQL implementations | ✅ Done | `production/core/repositories/postgres_*.py` |
| 3.0h CoreEntity repository tests | ✅ Done | `test_postgres_core_entity_repository.py` (291 lines) |
| 3.0i RawSnapshot repository tests | ⏳ **IN PROGRESS** | `test_postgres_raw_snapshot_repository.py` (MISSING) |

**Deliverables:**
- URI/URN format: `http://proves.space/{ecosystem}/{type}/{key}`
- 7-question FRAMES model embedded in domain
- Verification-level semantics (VERIFIED vs CANDIDATE)
- Read-only repositories (no write-path changes)

**Documentation:**
- `.deepagents/DOMAIN_MODELS_COMPLETE.md` - Full summary
- `.deepagents/SESSION_SUMMARY_2026-01-15_DOMAIN_MODELS.md` - Conversation transcript
- `.deepagents/SAFE_REFACTORING_PLAN.md` - Safe refactoring approach

#### Week 3+: Export Serializers ⏳ NEXT

| Task | Risk | Benefit | Status |
|------|------|---------|--------|
| 3.1 Soft matching (semantic deduplication) | Medium | Catches near-duplicates | ⏳ Pending |
| 3.2 XTCE serializer for cmd/tlm | Low | Space industry standard | ⏳ Pending |
| 3.3 FPrime serializer for F' ecosystem | Low | F' tool compatibility | ⏳ Pending |
| 3.4 SysML v2 serializer for architecture | Medium | MBSE tool compatibility | ⏳ Pending |
| 3.5 W3C PROV export for organizational layer | Low | Provenance standard | ⏳ Pending |

**Mapping: core_entities → Standards**

| candidate_type | XTCE | FPrime | SysML v2 |
|----------------|------|--------|----------|
| `telemetry` | Parameter | TelemetryPort | - |
| `command` | MetaCommand | CommandPort | Action |
| `parameter` | ParameterType | - | Attribute |
| `data_type` | ParameterType | Type | DataType |
| `component` | SpaceSystem | Component | Part/Block |
| `port` | - | Port | Port |
| `connection` | - | Connection | Connector |
| `dependency` | - | - | Dependency |
| `inheritance` | - | - | Generalization |

**FRAMES provenance preserved via:**
- XTCE `AncillaryData` elements
- Separate provenance export (JSON-LD/W3C PROV)
- Database link via `source_snapshot_id`

**Validation:** Export verified entities, import into standard tools, verify structure.

---

### Phase 4: Round-Trip Sync (Future)

**Goal:** Import from standard tools and merge with FRAMES provenance.

| Task | Risk | Benefit |
|------|------|---------|
| 4.1 Import XTCE files | Medium | Ground system integration |
| 4.2 Import FPrime topology | Medium | F' project import |
| 4.3 Match imported elements to core_entities | High | Avoid duplicates |
| 4.4 Merge FRAMES provenance with imports | Medium | Preserve knowledge context |
| 4.5 Conflict detection and human review | Medium | Data quality |

**Validation:** Round-trip test - export, import, verify no data loss.

---

### Phase 5: Modernize (Optional)

**Goal:** Clean up technical debt.

| Task | Risk | Benefit |
|------|------|---------|
| 5.1 Consolidate Version folders | Medium | Cleaner structure |
| 5.2 Create proper Python package | Medium | Standard tooling |
| 5.3 Add structured inter-agent messages | High | Reliable communication |
| 5.4 Implement plugin system | Medium | Extensibility |

**Validation:** Full test suite passes, pipeline unchanged.

---

## Part 4: Decision Points

### Decision 1: Which Option?

| Factor | Option A | Option B | Option C |
|--------|----------|----------|----------|
| **Risk** | Low | Medium | High |
| **Effort** | 1-2 weeks | 3-4 weeks | 6-8 weeks |
| **Integration Benefit** | Moderate | High | Maximum |
| **Breaking Changes** | None | Few | Many |
| **Testability** | Slight improvement | Major improvement | Full coverage |
| **Recommendation** | ✅ Start here | ✅ Goal | ⚠️ Future |

**Recommendation:** Start with Option A, progress to Option B.

---

### Decision 2: When to Validate?

**After every change:**
1. Run `process_extractions_v3.py` with test URL
2. Check `staging_extractions` for correct output
3. Compare with previous run (no regressions)

**Validation script:**
```bash
# scripts/validate_pipeline.py
# 1. Run extraction on known URL
# 2. Compare output with expected schema
# 3. Check database state
# 4. Report pass/fail
```

---

### Decision 3: What to Preserve?

**Must preserve (core value):**
- ✅ Epistemic framework (7-question checklist)
- ✅ Lineage verification (evidence ↔ snapshot)
- ✅ FRAMES methodology (4-question coupling)
- ✅ Human-in-the-loop workflow
- ✅ Strict enums for types

**Can change (implementation detail):**
- ⚙️ Database connection handling
- ⚙️ File structure
- ⚙️ Inter-agent message format
- ⚙️ Serialization approach

---

## Part 5: First Steps

### Immediate Actions (This Session)

1. **Create database pool module** (`production/core/database.py`)
   - Single connection pool
   - Environment loading once
   - Connection context manager

2. **Create JSON schema** (`production/schemas/extraction_schema.json`)
   - Validate candidate_type enum
   - Validate evidence_type enum
   - Validate epistemic structure

3. **Create validation script** (`scripts/validate_pipeline.py`)
   - Test extraction on known URL
   - Verify output matches schema
   - Baseline for regression testing

4. **Document current contracts** (`.deepagents/AGENT_CONTRACTS.md`)
   - Extractor output format
   - Validator input/output
   - Storage input format

### Before Next Session

- [ ] Run current pipeline to establish baseline
- [ ] Review JSON schemas for accuracy
- [ ] Identify test URLs for validation
- [ ] Decide on Phase 1 scope

---

---

## Part 6: The Complete 5-Stage Architecture

> **Updated based on full understanding of existing infrastructure**

The conversation with the previous agent revealed the actual pipeline architecture:

```
STAGE 1: Loose Capture (Extractor v3) ✅ DONE
    ↓ Cast wide net, don't force rigid classification
    ↓ Capture gray areas where knowledge loss happens
    ↓ Extract FRAMES couplings with epistemic metadata
    ↓ Output: raw_snapshots + staging_extractions

STAGE 2: Human Review (Notion Integration) ✅ DONE
    ↓ Humans establish truth, verify EACH extraction
    ↓ Apply 7-question checklist for epistemic dimensions
    ↓ Approve/reject individual extractions
    ↓ Output: Notion approval status

STAGE 3: Promotion & Matching ✅ DONE
    ↓ Hard matching (exact key + ecosystem)
    ↓ Merge with existing core_entities
    ↓ Store with full FRAMES dimensions
    ↓ Output: core_entities (verified truth layer)

STAGE 4: Standardization & Export ⏳ NEXT TO BUILD
    ↓ Soft matching (semantic deduplication)
    ↓ Export to XTCE/SysML/FPrime/W3C PROV
    ↓ Preserve FRAMES provenance in AncillaryData
    ↓ Output: Clean MBSE format + provenance sidecar

STAGE 5: Round-trip Sync 🔮 FUTURE
    ↓ Import from standard tools (Cameo, Capella, FPrime)
    ↓ Merge with existing FRAMES provenance
    ↓ Bidirectional sync with Notion views
```

### Key Architectural Principles (from CANON + ONTOLOGY)

**1. FRAMES Wraps Standards, Doesn't Replace Them**
- **Technical Layer (XTCE, SysML, FPrime):** Defines *what the system is*
- **FRAMES Layer (provenance + epistemic):** Defines *how we know it*
- Export clean standard formats, store rich FRAMES-wrapped data

**2. Loose Capture → Narrow Truth (Funnel Architecture)**
- **At Extraction:** Keep it loose, capture gray areas, don't force classification
- **At Human Review:** Establish truth, align to standards
- **At Export:** Standard-compliant output for tool interoperability

**3. Per-Type Defaults, NOT Global Defaults**
- Global defaults collapse the ontology (learned in V3 development)
- Type-specific templates after `candidate_type` is determined
- Three-layer merge: type defaults → page defaults → candidate overrides

**4. Evidence + Lineage Are Not Optional**
- Every extraction: `snapshot_id`, `source_url`, `raw_evidence`, confidence
- Epistemic metadata from 7-question checklist
- Makes graph auditable and supports cross-source reconciliation

**5. Bifurcated Workflow (Agents vs Humans)**
```
Agents ──────────────────────► Staging Tables (ALL data)
                                      │
                                      ▼
                               Human Review
                                      │
                                      ▼
Human ───────────────────────► Core Tables (Verified ONLY)
```

**6. The Three Relationship Layers**
- **Digital Layer:** Software ↔ Software/Hardware (XTCE, FPrime, CCSDS)
- **Physical Layer:** Hardware ↔ Hardware (power, heat, mechanical)
- **Organizational Layer:** People ↔ People/Teams (where 88% failure happens)

**7. Extraction Focus: COUPLINGS, Not Components**

Every coupling must answer 4 questions:
1. **What flows through?** (data, power, information, decisions)
2. **What happens if it stops?** (failure mode/impact)
3. **What maintains it?** (interface mechanisms)
4. **Coupling strength** (0.0-1.0, based on failure severity)

Plus epistemic dimensions:
- **Knowledge form** (Embodied/Inferred)
- **Contact** (Direct/Mediated/Indirect/Derived)
- **Directionality** (Forward/Backward/Bidirectional)
- **Temporality** (Snapshot/Sequence/History/Lifecycle)
- **Formalizability** (Portable/Conditional/Local/Tacit)

---

## Part 7: Risk Mitigation

### If Something Breaks

1. **Git branches:** All changes on feature branches
2. **Validation after each change:** Run test pipeline
3. **Rollback plan:** Revert to last working commit
4. **Parallel implementation:** New code alongside old, switch when ready

### Testing Strategy

```
Level 1: Unit tests (domain models, validators)
Level 2: Integration tests (repository + database)
Level 3: Pipeline tests (full extraction cycle)
Level 4: Regression tests (compare outputs)
```

### Communication

- Document all changes in this roadmap
- Update after each phase
- Flag risks early

---

## Part 8: File-by-File Impact Analysis

| File | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|------|---------|---------|---------|---------|---------|
| `extractor_v3.py` | ✅ Done | N/A | Minor | Add events | Restructure |
| `validator_v3.py` | ✅ Done | N/A | Minor | Add events | Restructure |
| `storage_v3.py` | ✅ Done | ✅ Has promote | Minor | Add events | Restructure |
| `agent_v3.py` | No changes | No changes | No changes | Add events | Restructure |
| `batch_promote_accepted.py` | N/A | ✅ Exists | Extend | Add events | Integrate |
| **NEW: Serializers** | N/A | N/A | **Create** | Extend | Plugin system |
| **NEW: Soft matching** | N/A | N/A | **Create** | Extend | ML-based |

---

## Part 9: Next Implementation Steps

### For Phase 3 (Standardization & Export):

**3.1 Soft Matching Module** (`production/core/soft_matching.py`)
- Semantic similarity for near-duplicates
- Fuzzy key matching (edit distance, embeddings)
- Propose merges for human review (don't auto-merge)

**3.2 XTCE Serializer** (`production/serializers/xtce_serializer.py`)
- Map core_entities → XTCE Parameter/MetaCommand
- Preserve FRAMES provenance in AncillaryData
- Export clean XML for standard tools

**3.3 FPrime Serializer** (`production/serializers/fprime_serializer.py`)
- Map core_entities → FPrime topology
- Component/Port/Connection export
- FPP format support

**3.4 SysML v2 Serializer** (`production/serializers/sysml_serializer.py`)
- Map core_entities → SysML v2 elements
- KerML type definitions
- API integration

**3.5 W3C PROV Export** (`production/serializers/frames_provenance.py`)
- Organizational layer couplings
- Full epistemic metadata
- JSON-LD format

### Validation Strategy:
1. Export verified entities from `core_entities`
2. Import into standard tools (XTCE viewer, FPrime, SysML tool)
3. Verify structure matches expectations
4. Preserve FRAMES provenance link via `source_snapshot_id`

---

## Summary: Where We Are

**✅ Phase 1 (Stabilize):** Complete - 49 passing tests, centralized DB pool, schema validation
**✅ Phase 2 (Promotion):** Already existed - `batch_promote_accepted.py` + Migration 009
**⏳ Phase 3 (Standardization):** Ready to implement - soft matching + MBSE serializers
**🔮 Phase 4 (Round-trip):** Future - import from standard tools
**🔮 Phase 5 (Modernize):** Optional - clean up technical debt

**The previous conversation established:**
- FRAMES wraps MBSE standards (doesn't replace them)
- Standards compliance happens POST-verification (not at extraction)
- Stage 4 is the actual next phase to implement
- All infrastructure for Stages 1-3 already exists
