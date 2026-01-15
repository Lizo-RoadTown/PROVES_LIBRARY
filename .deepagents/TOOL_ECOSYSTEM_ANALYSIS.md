# Tool Ecosystem Analysis for PROVES Library

**Goal:** Choose an integration lane that maximizes open-source tool compatibility and systems engineering adoption.

**Priority:** Open source + systems engineering tools > proprietary MBSE suites

---

## The Lanes: Core Format Choices

### Lane 1: Graph Database Native (Recommended)

**Core Format:** GraphML / Cypher / Property Graph
**Philosophy:** Graph-first, export to other formats as needed

**Pros:**
- ✅ **Native to your architecture** - PROVES is already a knowledge graph
- ✅ **Tool-agnostic** - Can export to SysML, OWL, JSON-LD, etc.
- ✅ **Open source ecosystem** - Neo4j, ArangoDB, JanusGraph
- ✅ **Flexible schema** - Easy to evolve as ontology develops
- ✅ **Queryable** - Cypher, Gremlin for complex graph queries
- ✅ **Visualization ready** - Gephi, Cytoscape, GraphXR (all open source)

**Systems Engineering Integration:**
- Export to SysML v2 for standard tools
- Export to OWL for ontology tools (Protégé)
- Export to OSLC for lifecycle tool integration
- Import from various formats via parsers

**Open Source Tools:**
```
Primary Storage:
- PostgreSQL + pgvector (current - keep!)
- Neo4j (optional graph view)

Visualization:
- Gephi (desktop, open source)
- Cytoscape (biomedical focus but adaptable)
- yEd (free, Java-based)
- D3.js / Sigma.js (web-based)

Query/Analysis:
- Apache TinkerPop (graph traversal)
- NetworkX (Python graph analysis)
- igraph (R/Python network analysis)

Export Formats:
- GraphML (standard)
- GEXF (Gephi format)
- Cypher (Neo4j)
- RDF/Turtle (semantic web)
```

**Integration Path:**
```
PROVES Graph (PostgreSQL)
    ↓
GraphML Export
    ├─→ SysML v2 (for Cameo/EA users)
    ├─→ OWL/RDF (for semantic web)
    ├─→ OSLC (for tool integration)
    ├─→ JSON-LD (for web APIs)
    └─→ Gephi/Cytoscape (for visualization)
```

---

### Lane 2: Semantic Web / Linked Data

**Core Format:** RDF/OWL + SPARQL
**Philosophy:** Web-native, formal ontologies, reasoning engines

**Pros:**
- ✅ **Formal semantics** - OWL reasoners can infer relationships
- ✅ **Standards-based** - W3C specifications
- ✅ **Interoperable** - Linked Open Data ecosystem
- ✅ **Queryable** - SPARQL (SQL for graphs)
- ✅ **Ontology tools** - Protégé, TopBraid, WebProtégé

**Cons:**
- ❌ **Steeper learning curve** - RDF/OWL more complex than property graphs
- ❌ **Verbose** - Turtle/RDF-XML can be hard to read
- ❌ **Overkill?** - Full reasoning may be more than you need

**Open Source Tools:**
```
Triple Stores:
- Apache Jena (Java-based)
- RDF4J (Eclipse project)
- Virtuoso (open source edition)

Ontology Editors:
- Protégé (Stanford, very popular)
- WebProtégé (web-based version)
- OntoStudio (free edition)

Reasoning:
- HermiT (OWL reasoner)
- Pellet (OWL-DL reasoner)
- ELK (fast OWL EL reasoner)

Visualization:
- WebVOWL (web-based ontology viz)
- OntoGraf (Protégé plugin)
```

**Integration Path:**
```
PROVES Graph
    ↓
OWL Ontology Export
    ├─→ Protégé (editing/validation)
    ├─→ SPARQL endpoint (queries)
    ├─→ Reasoner (infer relationships)
    └─→ RDF dump (data exchange)
```

---

### Lane 3: Modern Data Formats (Developer-Friendly)

**Core Format:** JSON-LD + GraphQL
**Philosophy:** Web APIs, developer experience, modern stack

**Pros:**
- ✅ **Developer-friendly** - JSON is universal
- ✅ **API-first** - GraphQL for flexible queries
- ✅ **Web-native** - Easy to build UIs
- ✅ **Flexible** - Schema evolution is easy
- ✅ **Tooling** - Tons of JavaScript/Python libraries

**Cons:**
- ❌ **Less formal** - No built-in reasoning
- ❌ **Not SE-specific** - General web format
- ❌ **DIY integration** - More custom code needed

**Open Source Tools:**
```
API Layer:
- Hasura (GraphQL on PostgreSQL)
- PostGraphile (PostgreSQL → GraphQL)
- Dgraph (GraphQL-native graph DB)

Visualization:
- React Flow (interactive graphs)
- Mermaid (text-to-diagram)
- ELK.js (graph layout)

Query:
- GraphQL (typed queries)
- JSONPath (JSON traversal)
- jq (command-line JSON processing)
```

---

## Recommended: Hybrid Graph-First Approach

**Primary Lane:** Graph Database Native (Lane 1)
**Secondary:** Export to Semantic Web (Lane 2) + Developer APIs (Lane 3)

### Core Architecture

```
┌─────────────────────────────────────────────────────────┐
│  PROVES Knowledge Graph (PostgreSQL + pgvector)         │
│  - Native graph structure                               │
│  - Dimensional metadata (Contact, Knownness, etc.)      │
│  - Five-attribute edges                                 │
└───────────────────┬─────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────┐      ┌────────────────┐
│  Export APIs  │      │  Query APIs    │
│               │      │                │
│ - GraphML     │      │ - SQL          │
│ - OWL/RDF     │      │ - GraphQL      │
│ - SysML v2    │      │ - REST         │
│ - JSON-LD     │      │ - Cypher       │
│ - OSLC        │      │ - SPARQL       │
└───────┬───────┘      └────────┬───────┘
        │                       │
        ▼                       ▼
┌──────────────────────────────────────────┐
│  Tool Integrations                       │
│                                          │
│  Open Source SE Tools:                   │
│  - Gephi (visualization)                 │
│  - Protégé (ontology editing)            │
│  - Jupyter (analysis notebooks)          │
│  - OpenProject (project mgmt)            │
│  - Redmine (issue tracking)              │
│                                          │
│  Commercial SE Tools (via exports):      │
│  - Cameo Systems Modeler (SysML)         │
│  - Enterprise Architect (SysML)          │
│  - Jama Connect (requirements)           │
│  - PTC Windchill (PLM)                   │
└──────────────────────────────────────────┘
```

### Implementation Phases

#### Phase 1: Core Export Layer (Week 1-2)

Create standardized exporters:

```python
# production/core/exporters/

# Base exporter interface
class GraphExporter:
    def export(self, graph_data: Dict) -> str:
        """Export PROVES graph to target format"""
        raise NotImplementedError

# GraphML exporter (universal)
class GraphMLExporter(GraphExporter):
    def export(self, graph_data: Dict) -> str:
        """Export to GraphML for Gephi, yEd, etc."""
        # Nodes with PROVES metadata
        # Edges with five attributes
        return graphml_string

# OWL exporter (semantic web)
class OWLExporter(GraphExporter):
    def export(self, graph_data: Dict) -> str:
        """Export to OWL ontology for Protégé"""
        # Classes = Component types
        # Properties = Relationships
        # Individuals = Specific components
        return owl_string

# SysML v2 exporter (MBSE tools)
class SysMLExporter(GraphExporter):
    def export(self, graph_data: Dict) -> str:
        """Export to SysML v2 textual format"""
        # Blocks = Components
        # Ports = Interfaces
        # Dependencies = Relationships
        return sysml_string

# JSON-LD exporter (web/API)
class JSONLDExporter(GraphExporter):
    def export(self, graph_data: Dict) -> Dict:
        """Export to JSON-LD with context"""
        return jsonld_dict
```

#### Phase 2: Visualization Integration (Week 3-4)

**Gephi Integration:**
```python
# scripts/export_to_gephi.py
from production.core.exporters import GraphMLExporter

def export_for_gephi(filter_params: Dict = None):
    """Export PROVES graph for Gephi visualization"""
    graph = get_proves_graph(filter_params)
    exporter = GraphMLExporter()

    # Add visual attributes
    graph = add_visual_attributes(graph)
    # - Node size by confidence score
    # - Node color by contact level
    # - Edge thickness by strength
    # - Edge color by mechanism type

    graphml = exporter.export(graph)

    # Save with metadata
    write_file("proves_graph.graphml", graphml)
    write_file("gephi_instructions.md", """
    # Open in Gephi
    1. File → Open → proves_graph.graphml
    2. Layout: Force Atlas 2 (for graph structure)
    3. Color nodes by 'contact' attribute
    4. Size nodes by 'confidence' attribute
    5. Filter by 'knownness' = verified
    """)
```

**Protégé Integration:**
```python
# scripts/export_to_protege.py
from production.core.exporters import OWLExporter

def export_for_protege():
    """Export PROVES ontology for Protégé editing"""
    graph = get_proves_graph()
    exporter = OWLExporter()

    owl = exporter.export(graph)
    write_file("proves_ontology.owl", owl)

    print("""
    # Open in Protégé
    1. File → Open → proves_ontology.owl
    2. Navigate to 'Classes' tab to see component hierarchy
    3. Navigate to 'Object Properties' to see relationships
    4. Run reasoner: Reasoner → Pellet → Start reasoner
    5. View inferred relationships
    """)
```

#### Phase 3: Query APIs (Week 5-6)

**GraphQL API:**
```python
# mcp-server/src/proves_mcp/graphql_schema.py
import strawberry

@strawberry.type
class Component:
    id: str
    candidate_key: str
    description: str
    contact: float
    confidence_score: float
    relationships: List["Relationship"]

@strawberry.type
class Relationship:
    id: str
    source: Component
    target: Component
    mechanism: str
    strength: str
    knownness: str

@strawberry.type
class Query:
    @strawberry.field
    def components(self, filter: Optional[str] = None) -> List[Component]:
        """Query components with optional filter"""
        return get_components(filter)

    @strawberry.field
    def component_by_key(self, key: str) -> Optional[Component]:
        """Get specific component"""
        return get_component(key)

    @strawberry.field
    def dependencies(self, component_key: str, depth: int = 1) -> List[Relationship]:
        """Get dependencies for a component"""
        return get_dependencies(component_key, depth)

schema = strawberry.Schema(query=Query)
```

**SPARQL Endpoint:**
```python
# mcp-server/src/proves_mcp/sparql_endpoint.py
from rdflib import Graph, Namespace
from SPARQLWrapper import SPARQLWrapper, JSON

class ProvesRDFGraph:
    def __init__(self):
        self.graph = Graph()
        self.PROVES = Namespace("http://proves.space/ontology#")

    def load_from_db(self):
        """Load PROVES graph into RDF"""
        components = get_all_components()
        for comp in components:
            self.add_component(comp)

    def query(self, sparql: str):
        """Execute SPARQL query"""
        return self.graph.query(sparql)

# Example query:
"""
SELECT ?component ?confidence WHERE {
    ?component proves:hasConfidence ?confidence .
    ?component proves:hasContact ?contact .
    FILTER (?confidence > 0.8 && ?contact > 0.7)
}
"""
```

---

## Open Source Tool Matrix

| Tool | Purpose | Format | License | Integration Priority |
|------|---------|--------|---------|---------------------|
| **Gephi** | Graph visualization | GraphML | GPL | 🔥 HIGH |
| **Protégé** | Ontology editing | OWL | BSD | 🔥 HIGH |
| **Jupyter** | Analysis notebooks | JSON/SQL | BSD | 🔥 HIGH |
| **Neo4j** | Graph database | Cypher | GPL/Commercial | ⭐ MEDIUM |
| **Apache Jena** | RDF/SPARQL | RDF | Apache 2.0 | ⭐ MEDIUM |
| **yEd** | Diagram editor | GraphML | Freeware | ⭐ MEDIUM |
| **Cytoscape** | Network analysis | Various | LGPL | ⭐ MEDIUM |
| **OpenProject** | Project mgmt | OSLC | GPL | ⚡ LOW |
| **Redmine** | Issue tracking | REST API | GPL | ⚡ LOW |

---

## Decision Matrix

### For Your Use Case:

**Start with:** Lane 1 (Graph Database Native)

**Rationale:**
1. ✅ **Already using PostgreSQL** - No migration needed
2. ✅ **Flexible** - Can export to any format later
3. ✅ **Open source native** - GraphML → Gephi, OWL → Protégé
4. ✅ **Research-friendly** - Easy to evolve ontology
5. ✅ **Developer-friendly** - Can add GraphQL/REST APIs

**Implementation:**
```
Week 1-2:  GraphML + OWL exporters
Week 3-4:  Gephi + Protégé workflows
Week 5-6:  GraphQL API + documentation
Week 7-8:  SysML exporter (for industry users)
```

---

## Concrete Next Steps

1. **This Week:**
   - Create `production/core/exporters/` directory
   - Implement `GraphMLExporter` (simplest, highest value)
   - Test export with current graph data
   - Open in Gephi to validate

2. **Next Week:**
   - Implement `OWLExporter`
   - Create PROVES ontology in Protégé
   - Define classes for Component, Interface, Flow, Dependency
   - Add object properties for relationships

3. **Week 3:**
   - Add export scripts to production pipeline
   - Document workflows for each tool
   - Create example Jupyter notebooks

**Should I start implementing the GraphML exporter now?**

---

## Questions

1. **Primary Users:** Researchers? Systems engineers? Both?
2. **Tool Preference:** Desktop (Gephi) vs Web (D3.js) for visualization?
3. **Reasoning Needed:** Do you need OWL reasoners to infer relationships?
4. **API Priority:** GraphQL for developers? Or focus on file exports?
5. **Timeline:** When do you need external tool integration?

Let me know and I can start building the exporter layer!
