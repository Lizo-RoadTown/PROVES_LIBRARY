# Safe Domain Model Refactoring Plan
## Avoiding Drift While Building Stage 4 Integration

**Core Principle**: Build domain models on the **verified read/export side** (Stage 4), not by refactoring the extraction write path.

---

## Why This Approach (Response to Architecture Review)

### Risk Analysis
**High Risk** (Original Plan):
- Refactor extractor/validator/storage tools first
- Touch the write path that just achieved 100% reliability
- Increase complexity in Stages 1-3 that were just stabilized

**Low Risk** (This Plan):
- Build domain models for reading `core_entities`
- Export verified knowledge to MBSE tools
- Leave extraction pipeline untouched
- Immediate integration wins

### Architectural Alignment
✅ Preserves the funnel: loose capture → human truth-making → standards export
✅ Human review remains the truth gate
✅ Stage 4 exports generated from verified `core_entities` only
✅ Agent contracts remain stable

---

## Two Domain Models (Not One)

**Do NOT collapse these into a single "Entity"** - they have different semantics:

### 1. CandidateExtraction (maps to `staging_extractions`)
**Purpose**: Unverified extractions awaiting human review

```python
@dataclass
class CandidateExtraction:
    """Unverified extraction from documentation (staging layer)"""

    extraction_id: UUID
    candidate_key: str
    candidate_type: str  # entity_type enum
    candidate_payload: Dict[str, Any]

    # Status tracking
    status: str  # 'pending', 'validated', 'accepted', 'rejected'

    # Machine confidence (not human-verified)
    confidence_score: float
    lineage_verified: bool
    lineage_confidence: Optional[float]

    # Evidence provenance
    snapshot_id: UUID
    evidence: Dict[str, Any]
    evidence_checksum: Optional[str]
    evidence_byte_offset: Optional[int]

    # Notion sync
    notion_page_id: Optional[str]
    notion_synced_at: Optional[datetime]
```

### 2. CoreEntity (maps to `core_entities`)
**Purpose**: Human-verified knowledge (truth layer)

```python
@dataclass
class CoreEntity:
    """Human-verified entity in the knowledge base"""

    id: UUID
    entity_type: str
    canonical_key: str
    name: str
    display_name: Optional[str]
    ecosystem: str

    # Attributes
    attributes: Dict[str, Any]

    # FRAMES dimensions (human-verified)
    dimensions: FramesDimensions  # Separate value object

    # Verification metadata
    verification_status: str  # 'human_verified', 'auto_approved'
    verified_by: str
    verified_at: datetime
    approval_source: str

    # Provenance (links back to evidence)
    source_snapshot_id: UUID

    # Versioning
    version: int
    is_current: bool
    superseded_by_id: Optional[UUID]

    # Notion integration
    notion_page_id: Optional[str]
```

**Rule**: Stage 4 exporters default to `CoreEntity`. Only allow staging export with explicit flag (debug/prototype mode).

---

## Domain Model Components

### Value Objects

#### FramesDimensions
```python
@dataclass
class FramesDimensions:
    """FRAMES 7-question epistemic model (human-verified)"""

    knowledge_form: Optional[str]  # 'embodied', 'inferred', 'unknown'
    knowledge_form_confidence: Optional[float]
    knowledge_form_reasoning: Optional[str]

    contact_level: Optional[str]  # 'direct', 'mediated', 'indirect', 'derived'
    contact_confidence: Optional[float]
    contact_reasoning: Optional[str]

    directionality: Optional[str]  # 'forward', 'backward', 'bidirectional'
    directionality_confidence: Optional[float]
    directionality_reasoning: Optional[str]

    temporality: Optional[str]  # 'snapshot', 'sequence', 'history', 'lifecycle'
    temporality_confidence: Optional[float]
    temporality_reasoning: Optional[str]

    formalizability: Optional[str]  # 'portable', 'conditional', 'local', 'tacit'
    formalizability_confidence: Optional[float]
    formalizability_reasoning: Optional[str]

    carrier: Optional[str]  # 'body', 'instrument', 'artifact', 'community', 'machine'
    carrier_confidence: Optional[float]
    carrier_reasoning: Optional[str]

    def validate(self) -> List[str]:
        """Validate dimensional constraints"""
        errors = []

        # Validate confidences are 0-1
        for field in ['knowledge_form_confidence', 'contact_confidence',
                      'directionality_confidence', 'temporality_confidence',
                      'formalizability_confidence', 'carrier_confidence']:
            val = getattr(self, field)
            if val is not None and not (0.0 <= val <= 1.0):
                errors.append(f"{field} must be between 0.0 and 1.0")

        return errors
```

#### ProvenanceRef
```python
@dataclass
class ProvenanceRef:
    """Evidence provenance pointer"""

    source_snapshot_id: UUID
    source_url: str
    snapshot_checksum: str
    fetched_at: datetime

    # Evidence locators (if available)
    evidence_checksum: Optional[str]
    evidence_byte_offset: Optional[int]
    evidence_byte_length: Optional[int]
```

### Identifiers (Immediate Implementation)

```python
# production/core/identifiers.py

from typing import Optional
import re

class ProvesIdentifier:
    """Standard PROVES identifier with URI/URN support"""

    NAMESPACE = "http://proves.space"

    def __init__(self, entity_type: str, key: str, ecosystem: Optional[str] = None):
        self.entity_type = entity_type
        self.key = self._normalize_key(key)
        self.ecosystem = ecosystem

    @staticmethod
    def _normalize_key(key: str) -> str:
        """Normalize key to URL-safe format"""
        key = key.lower()
        key = re.sub(r'[\s_]+', '-', key)  # spaces/underscores → hyphens
        key = re.sub(r'[^a-z0-9-]', '', key)  # remove special chars
        key = re.sub(r'-+', '-', key)  # collapse consecutive hyphens
        return key.strip('-')

    @property
    def uri(self) -> str:
        """HTTP URI for linked data / web"""
        if self.ecosystem:
            return f"{self.NAMESPACE}/{self.ecosystem}/{self.entity_type}/{self.key}"
        return f"{self.NAMESPACE}/{self.entity_type}/{self.key}"

    @property
    def urn(self) -> str:
        """URN for internal identifiers"""
        if self.ecosystem:
            return f"urn:proves:{self.ecosystem}:{self.entity_type}:{self.key}"
        return f"urn:proves:{self.entity_type}:{self.key}"

    @classmethod
    def from_uri(cls, uri: str) -> Optional["ProvesIdentifier"]:
        """Parse URI back to identifier"""
        if not uri.startswith(cls.NAMESPACE):
            return None

        parts = uri[len(cls.NAMESPACE)+1:].split('/')
        if len(parts) == 2:
            return cls(parts[0], parts[1])
        elif len(parts) == 3:
            return cls(parts[1], parts[2], ecosystem=parts[0])

        return None

    def __str__(self) -> str:
        return self.uri

    def __repr__(self) -> str:
        if self.ecosystem:
            return f"ProvesIdentifier({self.ecosystem}, {self.entity_type}, {self.key})"
        return f"ProvesIdentifier({self.entity_type}, {self.key})"
```

---

## Repositories (Read-First Implementation Order)

### Phase 1: Read-Only on Verified Layer (Immediate)

#### 1.1 CoreEntityRepository (read-only)
```python
# production/core/repositories/core_entity_repository.py

from abc import ABC, abstractmethod
from typing import List, Optional
from production.core.domain.core_entity import CoreEntity

class CoreEntityRepository(ABC):
    """Repository for human-verified entities"""

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[CoreEntity]:
        """Get entity by UUID"""
        pass

    @abstractmethod
    def get_by_key(self, ecosystem: str, canonical_key: str) -> Optional[CoreEntity]:
        """Get entity by ecosystem + canonical key"""
        pass

    @abstractmethod
    def get_by_type(self, entity_type: str, limit: int = 100) -> List[CoreEntity]:
        """Get all entities of a specific type"""
        pass

    @abstractmethod
    def list_recent_verified(self, limit: int = 100) -> List[CoreEntity]:
        """Get recently verified entities"""
        pass

    @abstractmethod
    def get_with_provenance(self, entity_id: str) -> tuple[CoreEntity, ProvenanceRef]:
        """Get entity with full provenance links"""
        pass
```

#### 1.2 RawSnapshotRepository (read-only)
```python
class RawSnapshotRepository(ABC):
    """Repository for source documentation snapshots"""

    @abstractmethod
    def get_by_id(self, snapshot_id: str) -> Optional[RawSnapshot]:
        pass

    @abstractmethod
    def get_by_url(self, source_url: str) -> List[RawSnapshot]:
        """Get all snapshots for a URL (may be multiple over time)"""
        pass
```

#### 1.3 VerifiedRelationshipRepository (read-only)
```python
class VerifiedRelationshipRepository(ABC):
    """Repository for verified relationships (knowledge_component_relationships, etc)"""

    @abstractmethod
    def get_for_entity(self, entity_id: str) -> List[VerifiedRelationship]:
        """Get all verified relationships for an entity"""
        pass

    @abstractmethod
    def get_component_knowledge_map(self, component_id: str) -> List[ComponentKnowledge]:
        """Get knowledge describing a component"""
        pass
```

### Phase 2: Write Support on Staging Layer (Later)

Only implement these AFTER Stage 4 exporters are working:

- `CandidateExtractionRepository` (write + read)
- `CandidateRelationshipRepository` (write + resolution helpers)

---

## KnowledgeNode Projection (Safe Unified Export Model)

**Problem**: Exporters want to work with both staging and core, but shouldn't blur semantics.

**Solution**: Explicit projection type that forces semantic declaration.

```python
# production/core/domain/knowledge_node.py

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
from production.core.identifiers import ProvesIdentifier

class VerificationLevel(Enum):
    """Explicit verification semantics"""
    CANDIDATE = "candidate"  # From staging_extractions
    VERIFIED = "verified"    # From core_entities

@dataclass
class KnowledgeNode:
    """
    Unified projection for export serializers.

    CRITICAL: Must explicitly declare verification level.
    Stage 4 exporters should default to VERIFIED only.
    """

    # Identity
    identifier: ProvesIdentifier
    key: str
    entity_type: str
    label: str

    # Ecosystem
    ecosystem: str
    namespace: Optional[str]

    # Attributes (flexible)
    attributes: Dict[str, Any]

    # FRAMES dimensions
    dimensions: Optional[FramesDimensions]

    # Provenance
    provenance: ProvenanceRef

    # Verification status (REQUIRED)
    verification: VerificationLevel

    # Machine confidence (only for CANDIDATE)
    confidence: Optional[float] = None

    @classmethod
    def from_core_entity(cls, entity: CoreEntity, snapshot: RawSnapshot) -> "KnowledgeNode":
        """Create from verified entity"""
        return cls(
            identifier=ProvesIdentifier(entity.entity_type, entity.canonical_key, entity.ecosystem),
            key=entity.canonical_key,
            entity_type=entity.entity_type,
            label=entity.display_name or entity.name,
            ecosystem=entity.ecosystem,
            namespace=entity.namespace,
            attributes=entity.attributes,
            dimensions=entity.dimensions,
            provenance=ProvenanceRef(
                source_snapshot_id=entity.source_snapshot_id,
                source_url=snapshot.source_url,
                snapshot_checksum=snapshot.checksum,
                fetched_at=snapshot.fetched_at,
            ),
            verification=VerificationLevel.VERIFIED,
            confidence=None,  # Verified entities don't have "confidence"
        )

    @classmethod
    def from_candidate_extraction(cls, candidate: CandidateExtraction, snapshot: RawSnapshot) -> "KnowledgeNode":
        """Create from unverified candidate"""
        return cls(
            identifier=ProvesIdentifier(candidate.candidate_type, candidate.candidate_key, candidate.ecosystem),
            key=candidate.candidate_key,
            entity_type=candidate.candidate_type,
            label=candidate.candidate_key,
            ecosystem=candidate.ecosystem,
            namespace=None,
            attributes=candidate.candidate_payload,
            dimensions=None,  # Candidates don't have verified dimensions
            provenance=ProvenanceRef(
                source_snapshot_id=candidate.snapshot_id,
                source_url=snapshot.source_url,
                snapshot_checksum=snapshot.checksum,
                fetched_at=snapshot.fetched_at,
                evidence_checksum=candidate.evidence_checksum,
                evidence_byte_offset=candidate.evidence_byte_offset,
            ),
            verification=VerificationLevel.CANDIDATE,
            confidence=candidate.confidence_score,
        )
```

---

## Exporters (Stage 4 Deliverables)

### Base Exporter Interface

```python
# production/core/exporters/base_exporter.py

from abc import ABC, abstractmethod
from typing import List, IO
from production.core.domain.knowledge_node import KnowledgeNode, VerificationLevel

class BaseExporter(ABC):
    """Base class for all format exporters"""

    def __init__(self, require_verified: bool = True):
        """
        Args:
            require_verified: If True, only export VERIFIED nodes (default).
                            Set False for debug/prototype exports.
        """
        self.require_verified = require_verified

    def export(self, nodes: List[KnowledgeNode], output: IO):
        """Export knowledge nodes to output stream"""

        # Filter by verification level
        if self.require_verified:
            nodes = [n for n in nodes if n.verification == VerificationLevel.VERIFIED]

        # Delegate to format-specific implementation
        self._export_impl(nodes, output)

    @abstractmethod
    def _export_impl(self, nodes: List[KnowledgeNode], output: IO):
        """Format-specific export implementation"""
        pass
```

### Concrete Exporters

#### GraphML (for Gephi visualization)
```python
class GraphMLExporter(BaseExporter):
    """Export to GraphML format for Gephi"""

    def _export_impl(self, nodes: List[KnowledgeNode], output: IO):
        # Write GraphML XML
        # Include FRAMES dimensions as node attributes
        pass
```

#### XTCE (for command/telemetry)
```python
class XTCEExporter(BaseExporter):
    """Export to XTCE format for spacecraft command/telemetry"""

    def _export_impl(self, nodes: List[KnowledgeNode], output: IO):
        # Write XTCE XML
        # Map entity types to XTCE constructs
        pass
```

#### SysML v2 (for MBSE)
```python
class SysMLExporter(BaseExporter):
    """Export to SysML v2 for model-based systems engineering"""

    def _export_impl(self, nodes: List[KnowledgeNode], output: IO):
        # Write SysML JSON/KerML
        pass
```

#### FPrime (ecosystem-specific)
```python
class FPrimeExporter(BaseExporter):
    """Export FPrime components to FPrime XML format"""

    def _export_impl(self, nodes: List[KnowledgeNode], output: IO):
        # Filter to fprime ecosystem
        # Write FPrime component XML
        pass
```

---

## Implementation Sequence (No-Drift Plan)

### Week 1: Foundation (Low Risk)

**Day 1-2: Identifiers**
- ✅ Create `production/core/identifiers.py`
- ✅ Add tests for URI/URN generation + normalization
- ✅ No pipeline changes

**Day 3-4: Domain Models**
- ✅ Create `production/core/domain/core_entity.py`
- ✅ Create `production/core/domain/frames_dimensions.py`
- ✅ Create `production/core/domain/provenance_ref.py`
- ✅ Create `production/core/domain/knowledge_node.py`
- ✅ Add validation tests
- ✅ No pipeline changes

**Day 5: Repository Interfaces**
- ✅ Create abstract `CoreEntityRepository`
- ✅ Create abstract `RawSnapshotRepository`
- ✅ No implementations yet - just interfaces

### Week 2: Read-Only Repositories (Low Risk)

**Day 1-3: PostgreSQL Implementations**
- ✅ Implement `PostgresCoreEntityRepository` (read-only)
- ✅ Implement `PostgresRawSnapshotRepository` (read-only)
- ✅ Use existing centralized connection pool (`database.py`)
- ✅ Add tests against real Neon data
- ✅ No pipeline changes

**Day 4-5: KnowledgeNode Projections**
- ✅ Implement `from_core_entity()` mapper
- ✅ Add tests for projection semantics
- ✅ Verify verification flags work correctly

### Week 3: Exporters (Immediate Value)

**Day 1-2: GraphML Exporter**
- ✅ Implement `GraphMLExporter`
- ✅ Golden-file tests (deterministic output for known inputs)
- ✅ Validate in Gephi

**Day 3: XTCE Exporter**
- ✅ Implement `XTCEExporter`
- ✅ Golden-file tests
- ✅ Validate with XTCE tools

**Day 4: SysML v2 Exporter**
- ✅ Implement `SysMLExporter`
- ✅ Golden-file tests

**Day 5: Export Scripts**
- ✅ Create `production/scripts/export/export_to_gephi.py`
- ✅ Create `production/scripts/export/export_to_xtce.py`
- ✅ Create `production/scripts/export/export_to_sysml.py`

**Milestone**: Stage 4 complete, extraction pipeline untouched.

---

## Invariants (Must Not Break)

These are hard constraints to prevent drift:

### 1. Stage 1 Stays Loose
❌ Do NOT harden `candidate_type` early
❌ Do NOT add validation that rejects "weird" extractions
✅ Keep capture permissive, let humans decide

### 2. Human Review is Truth Gate
❌ Do NOT auto-promote staging → core without human approval
❌ Do NOT export staging extractions as "official" (except debug mode)
✅ Only `core_entities` with `verification_status='human_verified'` are truth

### 3. Stage 4 Exports from Verified Layer
❌ Do NOT default to exporting `staging_extractions`
✅ Exporters default to `VerificationLevel.VERIFIED`
✅ Require explicit flag to export candidates

### 4. Agent Contracts Remain Valid
❌ Do NOT change tool signatures without version bumps
❌ Do NOT change database writes without testing against existing agents
✅ Keep current agent contracts stable
✅ Add version tags to new serialization (`schema_version: "1.0.0"`)

### 5. Connection Pooling Stays Centralized
❌ Do NOT create new connection patterns in repositories
✅ Repositories use existing `database.py` pool
✅ Reuse connection pool patterns from recent fixes

---

## Test Strategy

### Golden-File Tests (Highest Value Right Now)

```python
# tests/exporters/test_graphml_exporter.py

def test_graphml_export_deterministic():
    """Given known core_entities, output should be deterministic"""

    # Load fixture entities
    entities = load_fixture("sample_core_entities.json")

    # Export to GraphML
    exporter = GraphMLExporter(require_verified=True)
    output = StringIO()
    exporter.export(entities, output)

    # Compare to golden file
    expected = load_golden_file("expected_graphml_output.xml")
    assert output.getvalue() == expected
```

### Semantic Flag Tests

```python
def test_knowledge_node_verification_semantics():
    """Verification flag must match source"""

    # From core_entities → VERIFIED
    core_entity = CoreEntity(...)
    node = KnowledgeNode.from_core_entity(core_entity, snapshot)
    assert node.verification == VerificationLevel.VERIFIED
    assert node.confidence is None  # Verified has no "confidence"

    # From staging_extractions → CANDIDATE
    candidate = CandidateExtraction(...)
    node = KnowledgeNode.from_candidate_extraction(candidate, snapshot)
    assert node.verification == VerificationLevel.CANDIDATE
    assert node.confidence is not None  # Candidates have confidence
```

### Repository Tests

```python
def test_core_entity_repository_read():
    """Repository correctly maps database to domain model"""

    repo = PostgresCoreEntityRepository(db_url)

    # Test get_by_key
    entity = repo.get_by_key("fprime", "TestDriver")
    assert entity.canonical_key == "TestDriver"
    assert entity.entity_type == "component"
    assert entity.is_current == True
```

---

## Schema Fixes / Notes

### A) entity_alias FK Issue
**Current**: `canonical_entity_id → staging_extractions`
**Problem**: Aliases orphaned on promotion

**Fix Options**:
1. Point at `core_entities.id` (preferred)
2. Allow nullable FKs to both staging + core
3. Store aliases by `canonical_key` only (resolve at read time)

**Recommendation**: Wait until alias resolution is actually used, then fix.

### B) episodic_entities Table
**Issue**: `knowledge_episode_relationships` references it, but schema not shown

**Action**: Document `episodic_entities` schema when implementing episode relationships.

### C) core_entities.is_current Constraint
**Missing**: Unique constraint on `(ecosystem, canonical_key) WHERE is_current`

**Action**: Add migration to prevent multiple current versions:
```sql
CREATE UNIQUE INDEX idx_core_entities_current_key
ON core_entities(ecosystem, canonical_key)
WHERE is_current = TRUE;
```

### D) Provenance Evidence Pointers
**Current**: `core_entities.source_snapshot_id` only
**Enhancement**: Consider storing evidence locators from staging:
- `evidence_checksum`
- `evidence_byte_offset`
- `evidence_byte_length`

**Action**: Add to `ProvenanceRef` domain object, populate from staging during promotion.

---

## Deliverables Checklist

### Week 1 (Foundation)
- [ ] `production/core/identifiers.py`
- [ ] `production/core/domain/core_entity.py`
- [ ] `production/core/domain/frames_dimensions.py`
- [ ] `production/core/domain/provenance_ref.py`
- [ ] `production/core/domain/knowledge_node.py`
- [ ] `production/core/repositories/core_entity_repository.py` (abstract)
- [ ] Tests for identifiers
- [ ] Tests for domain models

### Week 2 (Read-Only Repos)
- [ ] `production/core/repositories/postgres_core_entity_repository.py`
- [ ] `production/core/repositories/postgres_raw_snapshot_repository.py`
- [ ] Repository tests against real Neon data
- [ ] KnowledgeNode projection tests

### Week 3 (Exporters)
- [ ] `production/core/exporters/base_exporter.py`
- [ ] `production/core/exporters/graphml_exporter.py`
- [ ] `production/core/exporters/xtce_exporter.py`
- [ ] `production/core/exporters/sysml_exporter.py`
- [ ] `production/scripts/export/export_to_gephi.py`
- [ ] `production/scripts/export/export_to_xtce.py`
- [ ] Golden-file export tests
- [ ] Documentation: `docs/EXPORT_GUIDE.md`

---

## Success Metrics

### Immediate (Week 3)
✅ Can export all 96 core_entities to GraphML and open in Gephi
✅ Can export FPrime components to XTCE format
✅ Extraction pipeline still at 100% reliability (15/15)
✅ Notion sync still operational

### Medium-Term (Month 2)
✅ External tools can consume PROVES exports without custom integration
✅ Domain models support 3+ export formats
✅ Golden-file tests catch serialization regressions

### Long-Term (Month 3+)
✅ Can add new export formats without touching pipeline
✅ Write support added to repositories without breaking reads
✅ Candidate extraction repository integrated (if needed)

---

## Bottom Line

**YES** to identifiers + domain models + repositories.

**BUT** start them on the verified read/export side (Stage 4), not by refactoring the extraction/storage write path first.

That gives you:
- ✅ Integration wins immediately
- ✅ Minimal risk to stabilized pipeline
- ✅ Clear semantics (VERIFIED vs CANDIDATE)
- ✅ Architectural alignment with FRAMES methodology

**Next Action**: Implement identifiers module (low risk, high value).
