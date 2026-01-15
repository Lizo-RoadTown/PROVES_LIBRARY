# PROVES Integration-Ready Implementation Roadmap

Making PROVES easily integratable through best practices, not format exports.

---

## Week 1: Domain Model Refactoring

**Goal:** Separate domain logic from storage implementation.

### Tasks

1. **Create clean domain models** (`production/core/domain/`)
   ```python
   # component.py - Pure domain object
   # interface.py
   # relationship.py
   # flow.py
   ```

2. **Implement standard identifiers** (`production/core/identifiers.py`)
   - URI format: `http://proves.space/{entity_type}/{key}`
   - URN format: `urn:proves:{entity_type}:{key}`

3. **Define JSON schemas** (`production/schemas/`)
   - `component_schema.json`
   - `relationship_schema.json`
   - Schema versioning: `v1.0.0`

4. **Repository pattern** (`production/core/repositories/`)
   - Abstract `ComponentRepository` interface
   - Concrete `PostgresComponentRepository`
   - Clean separation from domain

**Deliverable:** Domain models that can serialize to ANY format.

---

## Week 2: API Layer

**Goal:** Consistent interface for all data access.

### Tasks

1. **Service layer** (`production/core/services/`)
   ```python
   # component_service.py
   # relationship_service.py
   # extraction_service.py
   ```

2. **Dependency injection** (`production/core/container.py`)
   - Plugin registry
   - Service locator
   - Configuration-driven

3. **Event bus** (`production/core/events/`)
   - Pub/sub for extraction events
   - Audit trail
   - Integration hooks

4. **Versioning system** (`production/core/versioning/`)
   - Schema version tracking
   - Migration support
   - Compatibility checking

**Deliverable:** API that external tools can rely on.

---

## Week 3: Integration Layer

**Goal:** Serialize to standard formats.

### Tasks

1. **Serializers** (`production/core/serializers/`)
   - `GraphMLSerializer` (for Gephi)
   - `OWLSerializer` (for Protégé)
   - `JSONLDSerializer` (for web)
   - `SysMLSerializer` (for MBSE tools)

2. **Export scripts** (`production/scripts/export/`)
   - `export_to_gephi.py`
   - `export_to_protege.py`
   - `export_to_sysml.py`

3. **Documentation metadata** (`production/schemas/proves_metadata.yaml`)
   - Machine-readable ontology description
   - Auto-generate API docs
   - Version tracking

**Deliverable:** One-command exports to any tool.

---

## What to Build First

Based on your current codebase, let's start with the foundation:

### Step 1: Domain Models (Do this NOW)

Current state:
```python
# Extraction code is tightly coupled to database
# Mixes domain logic with SQL queries
```

Target state:
```python
# production/core/domain/component.py

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class DimensionalMetadata:
    """PROVES-specific dimensional metadata"""
    contact: float  # 0.0-1.0
    directionality: str  # forward, backward, bidirectional
    temporality: str  # snapshot, sequence, history, lifecycle
    formalizability: str  # portable, conditional, local, tacit

    def validate(self):
        """Validate metadata constraints"""
        assert 0.0 <= self.contact <= 1.0, "Contact must be 0-1"
        # ... other validations

@dataclass
class Component:
    """Pure domain model for PROVES component"""

    # Core identity
    key: str
    entity_type: str

    # Required fields
    description: str
    source_url: str

    # PROVES-specific
    dimensional_metadata: DimensionalMetadata
    confidence_score: float  # 0.0-1.0

    # Optional
    source_line_start: Optional[int] = None
    context: Optional[str] = None

    # Metadata (not business logic)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_uri(self) -> str:
        """Get URI for this component"""
        from production.core.identifiers import ProveIdentifier
        return ProveIdentifier("component", self.key).uri

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary (format-agnostic)"""
        return {
            "id": self.to_uri(),
            "key": self.key,
            "entity_type": self.entity_type,
            "description": self.description,
            "source_url": self.source_url,
            "dimensional_metadata": {
                "contact": self.dimensional_metadata.contact,
                "directionality": self.dimensional_metadata.directionality,
                "temporality": self.dimensional_metadata.temporality,
                "formalizability": self.dimensional_metadata.formalizability,
            },
            "confidence_score": self.confidence_score,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Component":
        """Deserialize from dictionary"""
        dim_meta = DimensionalMetadata(**data["dimensional_metadata"])
        return cls(
            key=data["key"],
            entity_type=data["entity_type"],
            description=data["description"],
            source_url=data["source_url"],
            dimensional_metadata=dim_meta,
            confidence_score=data["confidence_score"],
            context=data.get("context"),
        )
```

### Step 2: Identifiers

```python
# production/core/identifiers.py

from typing import Optional
import re

class ProveIdentifier:
    """Standard PROVES identifier with URI/URN support"""

    NAMESPACE = "http://proves.space"

    def __init__(self, entity_type: str, key: str):
        self.entity_type = entity_type
        self.key = self._normalize_key(key)

    @staticmethod
    def _normalize_key(key: str) -> str:
        """Normalize key to URL-safe format"""
        # Lowercase
        key = key.lower()
        # Replace spaces and underscores with hyphens
        key = re.sub(r'[\s_]+', '-', key)
        # Remove special characters
        key = re.sub(r'[^a-z0-9-]', '', key)
        # Remove consecutive hyphens
        key = re.sub(r'-+', '-', key)
        # Strip hyphens from ends
        return key.strip('-')

    @property
    def uri(self) -> str:
        """HTTP URI for linked data / web"""
        return f"{self.NAMESPACE}/{self.entity_type}/{self.key}"

    @property
    def urn(self) -> str:
        """URN for internal identifiers"""
        return f"urn:proves:{self.entity_type}:{self.key}"

    @classmethod
    def from_uri(cls, uri: str) -> Optional["ProveIdentifier"]:
        """Parse URI back to identifier"""
        if not uri.startswith(cls.NAMESPACE):
            return None

        parts = uri[len(cls.NAMESPACE)+1:].split('/')
        if len(parts) != 2:
            return None

        return cls(parts[0], parts[1])

    def __str__(self) -> str:
        return self.uri

    def __repr__(self) -> str:
        return f"ProveIdentifier({self.entity_type}, {self.key})"
```

### Step 3: Repository Pattern

```python
# production/core/repositories/component_repository.py

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from production.core.domain.component import Component

class ComponentRepository(ABC):
    """Abstract repository for component persistence"""

    @abstractmethod
    def save(self, component: Component) -> str:
        """Save component, return ID"""
        pass

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[Component]:
        """Get component by ID"""
        pass

    @abstractmethod
    def get_by_key(self, key: str) -> Optional[Component]:
        """Get component by key"""
        pass

    @abstractmethod
    def find_by_criteria(self, **criteria) -> List[Component]:
        """Find components matching criteria"""
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete component"""
        pass


# production/core/repositories/postgres_component_repository.py

import psycopg
from typing import List, Optional
from production.core.domain.component import Component, DimensionalMetadata
from production.core.repositories.component_repository import ComponentRepository

class PostgresComponentRepository(ComponentRepository):
    """PostgreSQL implementation of component repository"""

    def __init__(self, connection_string: str):
        self.conn_string = connection_string

    def save(self, component: Component) -> str:
        """Save component to staging_extractions table"""
        with psycopg.connect(self.conn_string) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO staging_extractions (
                        candidate_key,
                        candidate_type,
                        description,
                        source_url,
                        source_line_start,
                        context,
                        confidence_score,
                        dimensional_metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    component.key,
                    component.entity_type,
                    component.description,
                    component.source_url,
                    component.source_line_start,
                    component.context,
                    component.confidence_score,
                    component.dimensional_metadata.__dict__,  # JSONB
                ))
                return cur.fetchone()[0]

    def get_by_key(self, key: str) -> Optional[Component]:
        """Get component by key"""
        with psycopg.connect(self.conn_string) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        candidate_key, candidate_type, description,
                        source_url, source_line_start, context,
                        confidence_score, dimensional_metadata
                    FROM staging_extractions
                    WHERE candidate_key = %s
                    LIMIT 1
                """, (key,))

                row = cur.fetchone()
                if not row:
                    return None

                return self._row_to_component(row)

    def find_by_criteria(
        self,
        contact_min: Optional[float] = None,
        confidence_min: Optional[float] = None,
        entity_type: Optional[str] = None,
    ) -> List[Component]:
        """Find components matching criteria"""
        # Build dynamic query
        conditions = []
        params = []

        if contact_min is not None:
            conditions.append("(dimensional_metadata->>'contact')::float >= %s")
            params.append(contact_min)

        if confidence_min is not None:
            conditions.append("confidence_score >= %s")
            params.append(confidence_min)

        if entity_type is not None:
            conditions.append("candidate_type = %s")
            params.append(entity_type)

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        with psycopg.connect(self.conn_string) as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT
                        candidate_key, candidate_type, description,
                        source_url, source_line_start, context,
                        confidence_score, dimensional_metadata
                    FROM staging_extractions
                    WHERE {where_clause}
                """, params)

                return [self._row_to_component(row) for row in cur.fetchall()]

    def _row_to_component(self, row) -> Component:
        """Convert database row to Component domain object"""
        dim_meta = DimensionalMetadata(**row[7])  # dimensional_metadata JSONB

        return Component(
            key=row[0],
            entity_type=row[1],
            description=row[2],
            source_url=row[3],
            source_line_start=row[4],
            context=row[5],
            confidence_score=row[6],
            dimensional_metadata=dim_meta,
        )
```

---

## Integration with Deep Agents

Update the extraction agent to use the new architecture:

```python
# production/core/deep_extraction_agent.py (updated)

from deepagents import create_deep_agent
from production.core.repositories.postgres_component_repository import PostgresComponentRepository
from production.core.domain.component import Component, DimensionalMetadata
from langchain.tools import tool

# Inject repository (don't hardcode database)
def create_proves_extraction_agent(repository: ComponentRepository):
    """Create extraction agent with injected dependencies"""

    @tool
    def save_component_extraction(extraction_data: Dict) -> str:
        """Save extracted component to staging"""
        # Create domain object
        dim_meta = DimensionalMetadata(**extraction_data["dimensional_metadata"])
        component = Component(
            key=extraction_data["key"],
            entity_type=extraction_data["entity_type"],
            description=extraction_data["description"],
            source_url=extraction_data["source_url"],
            dimensional_metadata=dim_meta,
            confidence_score=extraction_data["confidence_score"],
        )

        # Validate
        component.dimensional_metadata.validate()

        # Save via repository (abstracted from storage)
        component_id = repository.save(component)

        return f"Saved component: {component.to_uri()} (ID: {component_id})"

    agent = create_deep_agent(
        tools=[save_component_extraction],
        system_prompt=EXTRACTION_SYSTEM_PROMPT,
    )

    return agent

# Usage
from production.core.repositories import get_repository

repository = get_repository("component")  # Configured via DI
agent = create_proves_extraction_agent(repository)
```

---

## Benefits of This Approach

1. **Integration-ready:**
   - Domain models can serialize to ANY format
   - Standard URIs for linking to external systems
   - Repository pattern allows swapping storage

2. **Testable:**
   - Mock repositories for testing
   - Domain logic separate from infrastructure
   - Clear boundaries

3. **Maintainable:**
   - Changes to database don't affect domain
   - Can add new serializers without touching core
   - Versioning prevents breaking changes

4. **Extensible:**
   - Plug in new storage backends
   - Add new export formats easily
   - Event bus for integration hooks

---

## Next Actions

**Should I start implementing this refactoring?**

I can:
1. Create the domain model files
2. Implement the identifier system
3. Set up repository pattern
4. Update deep extraction agent to use new architecture

This will make PROVES naturally compatible with any tool, not just through exports but through clean architecture.

**Want me to proceed?**
