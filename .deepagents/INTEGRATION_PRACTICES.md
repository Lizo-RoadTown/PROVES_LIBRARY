# Integration Practices for PROVES Library

**Core Principle:** Build integration-ready from the ground up, not as an afterthought.

"Integration" isn't about choosing SysML vs OWL vs GraphML. It's about **practices that make your system naturally compatible** with whatever tools your users already have.

---

## The Integration-First Mindset

### What We Mean by "Integration Practices"

**Not this:** "Let's build PROVES, then figure out how to export to SysML"
**But this:** "Let's build PROVES so that any reasonable tool can consume it"

**The difference:**
- Integration practices = How you design your data structures
- Integration tools = What formats you export to (downstream decision)

---

## Core Integration Practices

### 1. Separation of Concerns

**Practice:** Keep domain model independent from storage format.

**What this means:**
```python
# BAD: Storage format leaks into domain model
class Component:
    def __init__(self):
        self.db_id = None  # ❌ Tied to PostgreSQL
        self.sql_created_at = None  # ❌ Storage detail

# GOOD: Domain model is storage-agnostic
class Component:
    def __init__(self):
        self.key: str
        self.description: str
        self.contact: float
        self.knownness: str
    # Storage handled separately by repository pattern
```

**Why it enables integration:**
- Domain model can be serialized to ANY format
- No PostgreSQL-specific assumptions
- Easy to swap storage backends
- Tools can work with clean domain objects

**Implementation:**
```python
# production/core/domain/
#   - component.py (pure domain model)
#   - interface.py
#   - relationship.py
#
# production/core/repositories/
#   - postgres_repository.py (storage adapter)
#   - neo4j_repository.py (optional)
#
# production/core/serializers/
#   - graphml_serializer.py
#   - owl_serializer.py
#   - sysml_serializer.py
```

---

### 2. Standard Identifiers

**Practice:** Use URIs/IRIs for all entities, not just database IDs.

**What this means:**
```python
# BAD: Only internal IDs
component_id = 42  # ❌ Meaningless outside your database

# GOOD: Globally unique, meaningful identifiers
component_uri = "http://proves.space/component/MS5611_Barometer"
# or
component_urn = "urn:proves:component:ms5611-barometer"
```

**Why it enables integration:**
- Other systems can reference your entities
- Linked Data compatibility
- Merging graphs from multiple sources
- No ID collision when importing/exporting

**Implementation:**
```python
# production/core/domain/identifiers.py

class ProveIdentifier:
    """Standard PROVES identifier"""

    def __init__(self, entity_type: str, key: str):
        self.namespace = "http://proves.space"
        self.entity_type = entity_type
        self.key = self._normalize(key)

    @property
    def uri(self) -> str:
        """HTTP URI for web/linked data"""
        return f"{self.namespace}/{self.entity_type}/{self.key}"

    @property
    def urn(self) -> str:
        """URN for internal use"""
        return f"urn:proves:{self.entity_type}:{self.key}"

    def _normalize(self, key: str) -> str:
        """Normalize to URL-safe format"""
        return key.lower().replace(" ", "-").replace("_", "-")

# Usage
comp_id = ProveIdentifier("component", "MS5611 Barometer")
print(comp_id.uri)  # http://proves.space/component/ms5611-barometer
print(comp_id.urn)  # urn:proves:component:ms5611-barometer
```

---

### 3. Schema-First Design

**Practice:** Define your schema formally, independently of implementation.

**What this means:**
```
# BAD: Schema is implicit in code
# (Developer has to read Python code to understand structure)

# GOOD: Schema is explicit and documented
proves_schema.json     # JSON Schema
proves_ontology.ttl    # OWL/RDF ontology
proves_graphml.xsd     # GraphML schema
```

**Why it enables integration:**
- Other developers know exactly what to expect
- Validation is automatic
- Documentation is machine-readable
- Tools can auto-generate interfaces

**Implementation:**
```json
// production/schemas/proves_schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PROVES Component",
  "type": "object",
  "required": ["id", "candidate_key", "candidate_type"],
  "properties": {
    "id": {
      "type": "string",
      "format": "uri",
      "description": "Globally unique identifier"
    },
    "candidate_key": {
      "type": "string",
      "description": "Human-readable key"
    },
    "dimensional_metadata": {
      "type": "object",
      "properties": {
        "contact": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0
        },
        "knownness": {
          "enum": ["verified", "assumed", "unknown", "disproved"]
        }
      }
    }
  }
}
```

**Validation:**
```python
import jsonschema

def validate_component(component_data: Dict) -> bool:
    """Validate component against schema"""
    with open("production/schemas/proves_schema.json") as f:
        schema = json.load(f)
    jsonschema.validate(component_data, schema)
    return True
```

---

### 4. API-First Thinking

**Practice:** Design APIs before implementing storage.

**What this means:**
```python
# BAD: Direct database access everywhere
results = db.execute("SELECT * FROM components WHERE ...")

# GOOD: Well-defined API layer
components = component_api.find_by_criteria(contact_min=0.8)
```

**Why it enables integration:**
- Consistent interface for all consumers
- Easy to add new storage backends
- Can wrap with REST/GraphQL/gRPC
- Clear contract for external tools

**Implementation:**
```python
# production/core/api/component_api.py

from abc import ABC, abstractmethod
from typing import List, Optional

class ComponentAPI(ABC):
    """Abstract interface for component operations"""

    @abstractmethod
    def get_by_id(self, id: str) -> Optional[Component]:
        """Get component by identifier"""
        pass

    @abstractmethod
    def find_by_criteria(
        self,
        contact_min: Optional[float] = None,
        knownness: Optional[str] = None,
        **kwargs
    ) -> List[Component]:
        """Find components matching criteria"""
        pass

    @abstractmethod
    def get_dependencies(
        self,
        component_id: str,
        depth: int = 1
    ) -> List[Relationship]:
        """Get component dependencies"""
        pass

# Concrete implementation
class PostgresComponentAPI(ComponentAPI):
    def get_by_id(self, id: str) -> Optional[Component]:
        # PostgreSQL-specific implementation
        pass

# Future implementations
class Neo4jComponentAPI(ComponentAPI):
    pass

class RESTComponentAPI(ComponentAPI):
    """Wraps remote REST API"""
    pass
```

---

### 5. Documentation as Data

**Practice:** Make documentation machine-readable, not just human-readable.

**What this means:**
```yaml
# BAD: Only prose documentation
# README.md with paragraphs of text

# GOOD: Structured documentation
# proves_metadata.yaml
ontology:
  name: "PROVES Knowledge Graph"
  version: "1.0.0"
  namespace: "http://proves.space/"

entities:
  component:
    description: "Discrete module in a system"
    properties:
      - name: candidate_key
        type: string
        required: true
      - name: contact
        type: float
        range: [0.0, 1.0]

  relationship:
    description: "Connection between entities"
    properties:
      - name: mechanism
        type: enum
        values: [electrical, thermal, protocol, software]
```

**Why it enables integration:**
- Tools can parse your documentation
- Auto-generate API docs
- Validate data against spec
- Generate SDKs in other languages

**Implementation:**
```python
# production/core/metadata/loader.py

import yaml

class ProveMetadata:
    """Load and provide access to PROVES metadata"""

    def __init__(self, metadata_file: str):
        with open(metadata_file) as f:
            self.metadata = yaml.safe_load(f)

    def get_entity_schema(self, entity_type: str) -> Dict:
        """Get schema for entity type"""
        return self.metadata["entities"][entity_type]

    def validate_entity(self, entity_type: str, data: Dict) -> bool:
        """Validate data against entity schema"""
        schema = self.get_entity_schema(entity_type)
        # Validation logic
        return True

# Auto-generate documentation
def generate_api_docs():
    """Generate API docs from metadata"""
    metadata = ProveMetadata("production/schemas/proves_metadata.yaml")
    # Generate OpenAPI spec
    # Generate GraphQL schema
    # Generate human-readable docs
```

---

### 6. Versioning Everything

**Practice:** Version your ontology, schemas, and APIs.

**What this means:**
```python
# BAD: Breaking changes without notice
# Component format changes, tools break

# GOOD: Semantic versioning + compatibility
{
  "schema_version": "1.2.0",
  "component": {...},
  "compatible_with": ["1.0.0", "1.1.0", "1.2.0"]
}
```

**Why it enables integration:**
- Tools know what version they're working with
- Can support multiple versions simultaneously
- Clear upgrade paths
- Backwards compatibility tracking

**Implementation:**
```python
# production/core/versioning/schema_version.py

from dataclasses import dataclass
from typing import List

@dataclass
class SchemaVersion:
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def is_compatible_with(self, other: "SchemaVersion") -> bool:
        """Check if versions are compatible (same major version)"""
        return self.major == other.major

class VersionedData:
    """Wrapper for versioned data"""

    def __init__(self, data: Dict, version: SchemaVersion):
        self.data = data
        self.version = version
        self.data["_schema_version"] = str(version)

    def migrate_to(self, target_version: SchemaVersion):
        """Migrate data to target version"""
        if self.version == target_version:
            return self

        # Apply migrations
        migrator = get_migrator(self.version, target_version)
        migrated_data = migrator.migrate(self.data)

        return VersionedData(migrated_data, target_version)
```

---

### 7. Pluggable Architecture

**Practice:** Use dependency injection and interfaces everywhere.

**What this means:**
```python
# BAD: Hard-coded dependencies
class ExtractionAgent:
    def __init__(self):
        self.db = PostgresDB()  # ❌ Can't swap

# GOOD: Injected dependencies
class ExtractionAgent:
    def __init__(self, repository: ComponentRepository):
        self.repository = repository  # ✅ Any implementation
```

**Why it enables integration:**
- Easy to add new storage backends
- Testing with mocks
- Users can provide custom implementations
- Extensible without modifying core

**Implementation:**
```python
# production/core/plugins/

from abc import ABC, abstractmethod

# Define interfaces
class StoragePlugin(ABC):
    @abstractmethod
    def save(self, entity: Any) -> str:
        pass

    @abstractmethod
    def load(self, id: str) -> Any:
        pass

# Concrete implementations
class PostgresStorage(StoragePlugin):
    def save(self, entity):
        # PostgreSQL implementation
        pass

class FileSystemStorage(StoragePlugin):
    def save(self, entity):
        # File system implementation
        pass

# Plugin registry
class PluginRegistry:
    def __init__(self):
        self.plugins: Dict[str, StoragePlugin] = {}

    def register(self, name: str, plugin: StoragePlugin):
        self.plugins[name] = plugin

    def get(self, name: str) -> StoragePlugin:
        return self.plugins[name]

# Usage
registry = PluginRegistry()
registry.register("postgres", PostgresStorage())
registry.register("filesystem", FileSystemStorage())

# Agent uses whatever storage is configured
storage = registry.get(config["storage_backend"])
agent = ExtractionAgent(storage)
```

---

### 8. Event-Driven Architecture

**Practice:** Emit events for all important actions.

**What this means:**
```python
# BAD: Direct coupling
def extract_component(url):
    component = extract(url)
    db.save(component)  # ❌ Tightly coupled

# GOOD: Event-driven
def extract_component(url):
    component = extract(url)
    event_bus.emit("component_extracted", component)
    # Other systems can listen and react
```

**Why it enables integration:**
- Other tools can subscribe to events
- Loose coupling between systems
- Easy to add new consumers
- Audit trail built-in

**Implementation:**
```python
# production/core/events/event_bus.py

from typing import Callable, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Event:
    type: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str

class EventBus:
    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to event type"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(handler)

    def emit(self, event_type: str, data: Dict[str, Any], source: str = "unknown"):
        """Emit event"""
        event = Event(
            type=event_type,
            data=data,
            timestamp=datetime.now(),
            source=source
        )

        # Call all listeners
        for handler in self.listeners.get(event_type, []):
            handler(event)

# Usage
event_bus = EventBus()

# Subscribe to events
def on_component_extracted(event: Event):
    print(f"New component: {event.data['candidate_key']}")

event_bus.subscribe("component.extracted", on_component_extracted)

# Emit events
def extract_component(url):
    component = extract(url)
    event_bus.emit("component.extracted", component.to_dict(), source="extraction_agent")
```

---

## Putting It All Together

### The Integration-Ready Stack

```
┌─────────────────────────────────────────────────────────────┐
│  External Tools (Gephi, Protégé, SysML tools, etc.)        │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│  Export/Import Layer (Serializers)                          │
│  - GraphML, OWL, SysML v2, JSON-LD, etc.                   │
│  - Uses standard identifiers (URIs)                         │
│  - Schema validation                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│  API Layer (GraphQL, REST, SPARQL)                          │
│  - Versioned endpoints                                      │
│  - Clear contracts                                          │
│  - Documentation as data                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│  Service Layer (Component API, Relationship API, etc.)      │
│  - Abstract interfaces                                      │
│  - Dependency injection                                     │
│  - Event emission                                           │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│  Domain Layer (Pure domain objects)                         │
│  - Component, Interface, Relationship                       │
│  - No storage dependencies                                  │
│  - Validated by schemas                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│  Repository Layer (Storage adapters)                        │
│  - Pluggable (Postgres, Neo4j, File, etc.)                 │
│  - Implements abstract interfaces                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Checklist

### Phase 1: Foundation (This Week)
- [ ] Define domain models (separate from storage)
- [ ] Create standard identifiers (URI/URN for entities)
- [ ] Write JSON Schema for core entities
- [ ] Set up versioning system

### Phase 2: Architecture (Next Week)
- [ ] Abstract interfaces for repositories
- [ ] Dependency injection container
- [ ] Event bus implementation
- [ ] Plugin registry

### Phase 3: Integration (Week 3)
- [ ] Serializers (GraphML, OWL, JSON-LD)
- [ ] API layer (GraphQL)
- [ ] Documentation metadata
- [ ] Example integrations (Gephi, Protégé)

---

## The Answer to Your Question

**You asked:** "We want the practices that cause integration"

**The practices are:**
1. ✅ Separation of concerns (domain ≠ storage)
2. ✅ Standard identifiers (URIs, not just IDs)
3. ✅ Schema-first design (formal specs)
4. ✅ API-first thinking (interfaces everywhere)
5. ✅ Documentation as data (machine-readable)
6. ✅ Versioning everything (compatibility tracking)
7. ✅ Pluggable architecture (dependency injection)
8. ✅ Event-driven design (loose coupling)

**These practices make PROVES naturally compatible with:**
- Any storage backend
- Any serialization format
- Any query language
- Any visualization tool
- Any integration pattern

**Should I start implementing these patterns in the PROVES codebase?**

We can start with #1-3 this week (domain models, identifiers, schemas) and build out from there.
