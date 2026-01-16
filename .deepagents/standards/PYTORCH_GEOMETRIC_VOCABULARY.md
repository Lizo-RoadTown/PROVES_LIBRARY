# PyTorch Geometric (PyG) Vocabulary Study

**Purpose:** Understand PyTorch Geometric naming conventions and graph data structures to ensure PROVES canonical naming aligns naturally with graph machine learning standards.

**Library:** PyTorch Geometric (PyG)
**Use Case:** Graph Neural Networks (GNNs), node embeddings, link prediction, graph classification
**Repository:** https://github.com/pyg-team/pytorch_geometric

---

## 1. PyG Core Concepts

### 1.1 Data (Homogeneous Graph)

**Definition:** The fundamental data structure (`torch_geometric.data.Data`) representing a homogeneous graph where all nodes and edges are of the same type.

**Key Characteristics:**
- Holds node-level, edge-level, and graph-level attributes
- Dictionary-like interface with dynamic attribute access
- Not all attributes are required - flexible schema

**Standard Attributes:**

| Attribute | Shape | Type | Description |
|-----------|-------|------|-------------|
| `x` | `[num_nodes, num_node_features]` | `torch.Tensor` | Node feature matrix |
| `edge_index` | `[2, num_edges]` | `torch.long` | Graph connectivity in COO format |
| `edge_attr` | `[num_edges, num_edge_features]` | `torch.Tensor` | Edge feature matrix |
| `y` | `[num_nodes, *]` or `[1, *]` | `torch.Tensor` | Target labels (node-level or graph-level) |
| `pos` | `[num_nodes, num_dimensions]` | `torch.Tensor` | Node position matrix (e.g., 3D coordinates) |

**Example:**
```python
data = Data(
    x=torch.randn(10, 16),          # 10 nodes, 16 features each
    edge_index=torch.tensor([[0, 1, 2], [1, 2, 3]]),  # 3 edges
    edge_attr=torch.randn(3, 8),    # 3 edges, 8 features each
    y=torch.tensor([0, 1, 0, 1])    # Node labels
)
```

**Flexibility:**
- Can extend with custom attributes: `data.face` (for 3D meshes), `data.batch` (for batching), etc.
- No schema enforcement - attributes added dynamically

---

### 1.2 HeteroData (Heterogeneous Graph)

**Definition:** A data object representing a heterogeneous graph with multiple node types and/or edge types, holding them in disjunct storage objects.

**Key Characteristics:**
- **Node types** identified by single string keys
- **Edge types** identified by three-tuple: `(source_node_type, relation_type, destination_node_type)`
- Different feature dimensionalities per type
- Lazy initialization with `-1` for `in_channels` to handle varying dimensions

**Node Type Organization:**
```python
data = HeteroData()
data['paper'].x = torch.randn(num_papers, num_paper_features)
data['author'].x = torch.randn(num_authors, num_author_features)
```

**Edge Type Three-Tuple Format:**
```python
data['author', 'writes', 'paper'].edge_index = ...
data['paper', 'cites', 'paper'].edge_index = ...
```

**Accessing Grouped Data:**
- `data.x_dict` - Dictionary of node features by type
- `data.edge_index_dict` - Dictionary of edge indices by edge type
- `data.edge_attr_dict` - Dictionary of edge attributes by edge type

**Metadata:**
```python
node_types, edge_types = data.metadata()
# node_types: ['paper', 'author']
# edge_types: [('author', 'writes', 'paper'), ('paper', 'cites', 'paper')]
```

**Shorthand Access:**
If edge type can be uniquely identified by source/destination types:
```python
data['paper', 'paper']  # Instead of ('paper', 'cites', 'paper')
data['writes']          # Instead of ('author', 'writes', 'paper')
```

---

### 1.3 Edge Index Format (COO)

**COO Format:** Coordinate List format for sparse graph representation.

**Structure:**
- 2×E tensor where E = number of edges
- Row 0: Source node indices
- Row 1: Destination node indices

**Example:**
```python
edge_index = torch.tensor([
    [0, 1, 1, 2],  # Source nodes
    [1, 0, 2, 1]   # Destination nodes
])
# Edges: 0→1, 1→0, 1→2, 2→1
```

**Important Constraints:**
- Indices must be in range `{0, ..., num_nodes - 1}` (compact representation)
- For undirected graphs, both directions must be included:
  - Edge (0, 1) requires both `(0→1)` and `(1→0)` in `edge_index`

**Conversion from Tuple List:**
If you have `[(0, 1), (1, 2)]`, transpose and call `contiguous()`:
```python
edge_index = torch.tensor(edge_list).t().contiguous()
```

---

### 1.4 Node and Edge Stores

**NodeStorage / EdgeStorage:** Internal storage objects for node and edge attributes in `HeteroData`.

**Access Patterns:**
```python
for node_store in data.node_stores:
    print(node_store._key)  # Node type name
    print(node_store.x)     # Node features for this type

for edge_store in data.edge_stores:
    print(edge_store._key)  # Edge type (three-tuple)
    print(edge_store.edge_index)
```

**Metadata Method:**
```python
metadata = data.metadata()
# Returns: (node_types, edge_types)
```

---

## 2. PyG Naming Conventions

### 2.1 Standard Attribute Names

**Node-Level:**
- `x` - Node features (most common)
- `y` - Node labels (target)
- `pos` - Node positions (spatial graphs)
- `batch` - Batch assignment vector (for mini-batching)
- `train_mask`, `val_mask`, `test_mask` - Boolean masks for dataset splits

**Edge-Level:**
- `edge_index` - Graph connectivity (required)
- `edge_attr` - Edge features
- `edge_weight` - Scalar edge weights (1D)
- `edge_type` - Edge type indices (for typed edges in homogeneous graphs)

**Graph-Level:**
- `y` - Graph label (when doing graph classification)
- `num_nodes` - Number of nodes (optional, inferred from `edge_index` if missing)

### 2.2 Node Type Naming

**Convention:** Lowercase strings with underscores for multi-word types

**Examples:**
- `'paper'`
- `'author'`
- `'user'`
- `'software_component'` (multi-word)
- `'radio_driver'` (multi-word)

**Best Practice:** Singular nouns (e.g., `'author'` not `'authors'`)

### 2.3 Edge Type Naming

**Three-Tuple Format:** `(source_type, relation, dest_type)`

**Relation Naming Convention:**
- Verb phrase or relationship name
- Lowercase with underscores
- Describes the relationship from source to destination

**Examples:**
```python
('author', 'writes', 'paper')
('paper', 'cites', 'paper')
('user', 'rated', 'movie')
('component', 'depends_on', 'component')
('port', 'connected_to', 'port')
```

**Directional Clarity:**
- `'writes'` implies author → paper
- `'cited_by'` implies paper ← paper (reverse)
- Choose relation name that reads naturally: "author writes paper"

### 2.4 Feature Naming in Code

**Variable Names:**
- `h` - Hidden node embeddings (standard in GNN literature)
- `h_src`, `h_dst` - Source and destination node embeddings
- `x` - Input node features
- `out` - Output embeddings or predictions

**Example Forward Pass:**
```python
h = self.conv1(x, edge_index)
h = h.relu()
h = self.conv2(h, edge_index)
out = h
```

---

## 3. Graph Neural Network Vocabulary

### 3.1 Common GNN Operations

**Message Passing:** Core GNN paradigm where nodes exchange information with neighbors

**Aggregation Functions:**
- `'mean'` - Average neighbor features
- `'max'` - Max-pooling over neighbors
- `'sum'` - Sum neighbor features
- `'add'` - Alias for sum

**Order Invariance:** Aggregators must be permutation-invariant (mean, max, sum are valid; concat is not)

### 3.2 Model Naming Patterns

**Convolutional Layers:**
- `GCNConv` - Graph Convolutional Network
- `SAGEConv` - GraphSAGE layer
- `GATConv` - Graph Attention Network
- `GINConv` - Graph Isomorphism Network

**Full Models:**
- `GraphSAGE` - Full GraphSAGE model
- `GAT` - Full Graph Attention Network
- `GCN` - Full Graph Convolutional Network

**Parameters:**
- `in_channels` - Input feature dimension
- `hidden_channels` - Hidden layer dimension
- `out_channels` - Output dimension
- `num_layers` - Number of message passing layers

---

## 4. PROVES → PyG Alignment Table

### 4.1 Entity Type Mappings

| PROVES `entity_type` | PyG Equivalent | Alignment Status | Notes |
|----------------------|----------------|------------------|-------|
| `component` | Node type | **Aligned** | PROVES Component = PyG node with type `'component'` |
| `port` | Node type | **Aligned** | PROVES Port = PyG node with type `'port'` |
| `dependency` | Edge type (relation) | **Aligned** | PROVES Dependency = PyG edge `(source, 'depends_on', target)` |
| `connection` | Edge type (relation) | **Aligned** | PROVES Connection = PyG edge `(port, 'connected_to', port)` |
| `parameter` | Node type or node attribute | **Adjacent** | Could be node type or feature in `x` |
| `command` | Node type or node attribute | **Adjacent** | Could be node type or feature in `x` |
| `telemetry` | Node type or node attribute | **Adjacent** | Could be node type or feature in `x` |
| `event` | Node type or node attribute | **Adjacent** | Could be event node or temporal attribute |
| `data_type` | Node attribute (feature) | **Adjacent** | Type info could be node feature or metadata |

---

### 4.2 Detailed Alignment Analysis

#### 4.2.1 Component → Node Type

**Alignment:** Aligned (1:1)

**PROVES Concept:**
- Software or hardware component (e.g., `RadioDriver`, `PowerDriver`)
- Has attributes, ports, dependencies

**PyG Concept:**
- Node in heterogeneous graph with type `'component'`
- Node features in `x` contain component attributes
- Edges represent dependencies/connections

**Mapping Strategy:**
```python
# PROVES Component → PyG HeteroData node
data['component'].x = torch.tensor([
    # Each row = one component's features
    [feature_1, feature_2, ..., feature_n]
])

# Component attributes → node features
# ecosystem, namespace, verification_status → encoded in feature vector
```

**Example:**
```
PROVES: Component "RadioDriver" (ecosystem=fprime, namespace=Radio)
PyG:    Node in data['component'] with features encoding ecosystem, namespace, etc.
        Node index maps to canonical_key via external lookup
```

**Constraints:**
- Need to encode categorical attributes (ecosystem, entity_type) as features
- Use integer IDs or embeddings for categorical values

---

#### 4.2.2 Port → Node Type

**Alignment:** Aligned (1:1)

**PROVES Concept:**
- Interface point on a component
- Has direction (input/output), type (command/telemetry/data)

**PyG Concept:**
- Node in heterogeneous graph with type `'port'`
- Direction and port_type encoded in node features

**Mapping Strategy:**
```python
data['port'].x = torch.tensor([
    # Features: direction (0=input, 1=output), port_type (encoded), ...
])

# Connections between ports:
data['port', 'connected_to', 'port'].edge_index = ...
```

**Example:**
```
PROVES: Port "RadioStatus" (direction=output, type=telemetry)
PyG:    Node in data['port'] with features [direction=1, type=telemetry_id, ...]
```

**Constraints:**
- Port direction must be encoded in node features
- Port-to-component relationships need edges: `('port', 'belongs_to', 'component')`

---

#### 4.2.3 Dependency → Edge Type

**Alignment:** Aligned (1:1)

**PROVES Concept:**
- Component A depends on Component B
- Relationship with strength, mechanism, knownness (ERV model)

**PyG Concept:**
- Edge in heterogeneous graph: `('component', 'depends_on', 'component')`
- ERV attributes → edge features in `edge_attr`

**Mapping Strategy:**
```python
# Dependency relationship
data['component', 'depends_on', 'component'].edge_index = torch.tensor([
    [source_indices],
    [target_indices]
])

# ERV attributes → edge features
data['component', 'depends_on', 'component'].edge_attr = torch.tensor([
    # [directionality, strength, mechanism_id, knownness_id, ...]
])
```

**Example:**
```
PROVES: Dependency "RadioDriver REQUIRES PowerDriver"
        ERV: (strength=always, mechanism=electrical, knownness=known)

PyG:    Edge (radio_idx, power_idx) in ('component', 'depends_on', 'component')
        edge_attr = [forward, always_id, electrical_id, known_id]
```

**Constraints:**
- ERV categorical attributes (strength, mechanism) must be encoded as integers
- Could use one-hot encoding or embedding layers

---

#### 4.2.4 Connection → Edge Type

**Alignment:** Aligned (1:1)

**PROVES Concept:**
- Port-to-port connection
- Data flow path

**PyG Concept:**
- Edge: `('port', 'connected_to', 'port')`
- Connection metadata → edge attributes

**Mapping Strategy:**
```python
data['port', 'connected_to', 'port'].edge_index = ...
data['port', 'connected_to', 'port'].edge_attr = ...  # Connection metadata
```

**Example:**
```
PROVES: Connection between Port A and Port B
PyG:    Edge (port_a_idx, port_b_idx) in ('port', 'connected_to', 'port')
```

**Constraints:**
- Directionality must be captured in edge_index order or edge_attr

---

#### 4.2.5 Parameter/Command/Telemetry → Node Type or Attribute

**Alignment:** Adjacent (context-dependent)

**PROVES Concept:**
- Parameters, commands, telemetry are data values or signals

**PyG Options:**

**Option 1: Node Types**
```python
data['parameter'].x = ...
data['command'].x = ...
data['telemetry'].x = ...
```

**Option 2: Node Attributes**
Encode as features on component/port nodes:
```python
data['component'].x = torch.tensor([
    # [..., num_parameters, num_commands, num_telemetry_channels, ...]
])
```

**Option 3: Hybrid**
- Telemetry/Parameters that are graph entities → Node types
- Telemetry/Parameters that are component properties → Attributes

**Mapping Strategy:**
Depends on use case:
- **Node classification task**: Parameters/Commands as node types
- **Component relationship task**: Parameters as node features

**Decision:** TBD during canonical naming phase based on ML use case

---

#### 4.2.6 Event → Node Type or Temporal Attribute

**Alignment:** Adjacent

**PROVES Concept:**
- Event log entry or notification

**PyG Options:**

**Option 1: Event as Node Type**
```python
data['event'].x = torch.tensor([
    # [timestamp, severity, event_type, ...]
])
data['component', 'emits', 'event'].edge_index = ...
```

**Option 2: Temporal Graph**
Use dynamic graph representation with time-based features

**Mapping Strategy:**
- If events are entities: Node type `'event'`
- If events are temporal properties: Encode as node/edge features with timestamps

---

#### 4.2.7 Data Type → Node Feature Schema

**Alignment:** Adjacent

**PROVES Concept:**
- Type definition (int32, float64, enum)

**PyG Concept:**
- Not a graph entity - more of a schema/metadata
- Could be encoded as node feature describing type

**Mapping Strategy:**
- **Do NOT create nodes for data_type**
- Use data_type info to determine feature encoding:
  - `int32` → integer features
  - `float64` → float features
  - `enum` → categorical encoding

**Example:**
```
PROVES: DataType "VoltageType" (base_type=float, unit=volts)
PyG:    Not a node - informs feature engineering for voltage parameters
```

**Constraints:**
- Type information is metadata, not graph structure

---

## 5. Graph Structure Patterns

### 5.1 Bipartite Graphs

**Use Case:** Component-to-Port relationships

**Pattern:**
```python
# Components and Ports as separate node types
data['component'].x = ...
data['port'].x = ...

# Bipartite edges: component owns port
data['component', 'has_port', 'port'].edge_index = ...
data['port', 'belongs_to', 'component'].edge_index = ...  # Reverse
```

### 5.2 Multi-Relational Graphs

**Use Case:** Multiple relationship types between same node types

**Pattern:**
```python
# Same node types, multiple edge types
data['component', 'depends_on', 'component'].edge_index = ...
data['component', 'communicates_with', 'component'].edge_index = ...
data['component', 'inherits_from', 'component'].edge_index = ...
```

### 5.3 Knowledge Graph Pattern

**Use Case:** Entities with typed relationships (similar to RDF)

**Pattern:**
```python
# Entity types
data['component'].x = ...
data['port'].x = ...
data['parameter'].x = ...

# Relationships
data['component', 'has_port', 'port'].edge_index = ...
data['port', 'has_parameter', 'parameter'].edge_index = ...
data['component', 'depends_on', 'component'].edge_index = ...
```

**This is the PROVES pattern** - heterogeneous knowledge graph

---

## 6. Feature Engineering for PROVES Entities

### 6.1 Categorical Encoding

**PROVES Attributes:**
- `ecosystem`: 'fprime', 'ros2', 'cubesat'
- `entity_type`: 'component', 'port', etc.
- `verification_status`: 'pending', 'human_verified', 'auto_approved'

**PyG Encoding Options:**

**Option 1: Integer IDs**
```python
ecosystem_map = {'fprime': 0, 'ros2': 1, 'cubesat': 2}
x[:, 0] = torch.tensor([ecosystem_map[e] for e in ecosystems])
```

**Option 2: One-Hot Encoding**
```python
# ecosystem one-hot: [is_fprime, is_ros2, is_cubesat]
x[:, 0:3] = one_hot_encode(ecosystems)
```

**Option 3: Learned Embeddings**
```python
self.ecosystem_embedding = nn.Embedding(num_ecosystems, embed_dim)
h_ecosystem = self.ecosystem_embedding(ecosystem_ids)
```

### 6.2 Text Features

**PROVES Attributes:**
- `name`: 'RadioDriver'
- `canonical_key`: 'RadioDriver'
- `namespace`: 'Radio'

**PyG Encoding:**
- Use pre-trained text embeddings (e.g., Sentence-BERT)
- Encode names as fixed-size vectors

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

name_embeddings = model.encode(names)  # [num_nodes, 384]
x[:, :384] = torch.tensor(name_embeddings)
```

### 6.3 FRAMES Dimensions

**PROVES Concept:** 7-dimensional epistemic metadata

**PyG Encoding:**
Encode each FRAMES dimension + confidence:
```python
# Features: [knowledge_form_id, kf_confidence, contact_level_id, cl_confidence, ...]
# Total: 7 dimensions × 2 (value + confidence) = 14 features
```

**Alternative:** Learned embeddings per dimension

---

## 7. Graph ID and Versioning

### 7.1 Graph Identification

**Convention:** Use metadata attributes for graph identity

```python
data.graph_id = 'fprime_v3.4.3'
data.ecosystem = 'fprime'
data.version = '3.4.3'
data.extraction_date = '2026-01-15'
```

**Use in `standard_constraints`:**
```json
{
  "graph_id": "fprime_v3.4.3",
  "node_type": "component",
  "num_node_features": 128
}
```

### 7.2 Node/Edge ID Mapping

**Challenge:** PyG uses integer indices, PROVES uses UUIDs

**Solution:** External mapping table

```python
# Store UUID → PyG index mapping
node_id_map = {
    'uuid-123-456': 0,  # Component RadioDriver
    'uuid-789-abc': 1,  # Component PowerDriver
    ...
}

# Reverse map for export
index_to_uuid = {v: k for k, v in node_id_map.items()}
```

**In `standard_constraints`:**
```json
{
  "node_id_mapping": "stored_externally",
  "mapping_file": "node_uuid_to_index.json"
}
```

---

## 8. Constraints on Future PyG Exporters

### 8.1 Must-Follow Rules

1. **No Renaming**
   - PROVES `canonical_key` maps to external node ID (not PyG index)
   - PyG uses integer indices internally - maintain UUID mapping separately

2. **Node Type Naming**
   - Use PROVES `entity_type` directly as PyG node type name
   - Example: `entity_type='component'` → `data['component']`

3. **Edge Type Naming**
   - Use PROVES relationship type as middle element of three-tuple
   - Example: PROVES Dependency → `('component', 'depends_on', 'component')`

4. **Feature Consistency**
   - Document feature encoding in `standard_constraints`
   - Example:
     ```json
     {
       "node_features": {
         "0-3": "ecosystem_one_hot",
         "4-7": "verification_status_one_hot",
         "8-391": "name_embedding_384d"
       }
     }
     ```

5. **Fail Loudly**
   - If node/edge type not in PROVES schema, raise error
   - If feature encoding not defined, raise error
   - Do not guess or invent encodings

### 8.2 Example Mapping Record

```sql
INSERT INTO knowledge_enrichment (
  primary_entity_id,
  enrichment_type,
  standard,
  standard_version,
  standard_key,
  standard_name,
  standard_constraints
) VALUES (
  '123e4567-e89b-12d3-a456-426614174000',  -- PROVES entity UUID
  'standard_mapping',
  'pytorch_geometric',
  '2.5.0',
  'Node',  -- PyG concept
  'component',  -- Node type name
  '{
    "node_type": "component",
    "graph_id": "fprime_v3.4.3",
    "num_node_features": 128,
    "feature_encoding": {
      "0-2": "ecosystem_one_hot",
      "3-5": "verification_status_one_hot",
      "6-389": "name_embedding_384d",
      "390-403": "frames_dimensions_14d"
    },
    "node_id_mapping_file": "fprime_v3.4.3_node_mapping.json"
  }'::jsonb
);
```

### 8.3 Exporter Logic Pattern

```python
# Query for PyG mappings
mappings = db.execute("""
  SELECT * FROM standard_mappings
  WHERE standard = 'pytorch_geometric'
    AND entity_id = %s
""", [entity_id])

if not mappings:
    raise ValueError(f"No PyG mapping for entity {entity_id}")

# Use mapping data
node_type = mapping['standard_name']  # e.g., 'component'
constraints = mapping['standard_constraints']
graph_id = constraints['graph_id']
feature_schema = constraints['feature_encoding']

# Build PyG graph
data = HeteroData()
data[node_type].x = encode_features(entity, feature_schema)
```

---

## 9. Open Questions for Canonical Naming Phase

### 9.1 Node Type Granularity

**Question:** Should Parameter/Command/Telemetry be node types or node attributes?

**Options:**
1. **Node types**: Allows learning on parameters themselves
2. **Attributes**: Simpler graph, focuses on components/ports
3. **Hybrid**: Entity-level parameters = nodes, component properties = attributes

**Decision:** TBD based on ML use case (node classification vs link prediction vs graph classification)

### 9.2 Edge Type Vocabulary

**Question:** What relationship names should PROVES use for PyG edges?

**Current ERV relationships:**
- IDENTICAL, ALIAS_OF, EQUIVALENT_TO, DERIVED_FROM
- REQUIRES, CONFIGURES, CONTROLS, CONSTRAINS, COUPLES_TO, VERIFIED_BY

**PyG Convention:** Verb phrases (`writes`, `cites`, `depends_on`)

**Alignment Check:**
- `REQUIRES` → `'requires'` or `'depends_on'`?
- `COUPLES_TO` → `'couples_to'` or `'connected_to'`?

**Decision:** TBD - establish canonical PROVES relation names that read naturally in PyG three-tuples

### 9.3 Feature Standardization

**Question:** Should PROVES define a standard feature encoding schema?

**Trade-offs:**
- **Standard schema**: Consistent, easier to export, comparable across graphs
- **Custom schema**: Flexible, task-specific

**Proposal:** Define baseline feature schema in canonical naming phase:
- Positions 0-N: Standard categorical encodings (ecosystem, entity_type, etc.)
- Positions N+1 onwards: Task-specific features

**Decision:** TBD

### 9.4 Temporal Graphs

**Question:** How should PROVES handle temporal/versioned graphs?

**PyG Support:**
- Temporal graphs via `torch_geometric_temporal`
- Snapshot-based or continuous-time

**PROVES Versioning:**
- Entities have `version` and `is_current`
- Knowledge evolves over time

**Options:**
1. Export snapshots (one graph per version)
2. Use temporal graph format with time attributes
3. Encode version as node feature

**Decision:** TBD

---

## 10. Use Cases and Task Patterns

### 10.1 Node Classification

**Task:** Predict entity properties (e.g., verification_status)

**Graph Structure:**
- Nodes: Components, Ports
- Edges: Dependencies, Connections
- Target: `y` = verification status label

**Model:** GCN, GraphSAGE, GAT

### 10.2 Link Prediction

**Task:** Predict missing dependencies or connections

**Graph Structure:**
- Nodes: Components
- Edges: Known dependencies
- Target: Predict missing edges

**Model:** GraphSAGE with link prediction head

### 10.3 Graph Classification

**Task:** Classify entire system architecture (e.g., mission type, complexity level)

**Graph Structure:**
- One graph per system/ecosystem
- Graph-level label: Mission profile, risk level

**Model:** Graph pooling + classification

### 10.4 Knowledge Graph Embedding

**Task:** Learn embeddings for similarity search, recommendation

**Graph Structure:**
- Heterogeneous knowledge graph (all entity types)
- Multi-relational edges

**Model:** R-GCN, CompGCN

**Use Case:** "Find components similar to RadioDriver"

---

## 11. Next Steps

### 11.1 For Canonical Naming Phase

1. **Review PROVES Relationship Vocabulary**
   - ERV relationship types vs PyG edge naming conventions
   - Decide on canonical relation names (verb phrases)

2. **Define Node Type Boundaries**
   - When is something a node vs an attribute?
   - Parameter/Command/Telemetry granularity decision

3. **Standard Feature Schema**
   - Define baseline encoding for ecosystem, entity_type, verification_status
   - Document feature positions and encoding methods

4. **Edge Type Vocabulary**
   - Canonicalize ERV relationships for PyG compatibility
   - Ensure three-tuple format reads naturally

### 11.2 For Mapping Strategy Documentation

- Consolidate PyG + XTCE alignment tables
- Identify where entities map to multiple standards
- Document multi-standard export strategy

### 11.3 For Future Export Phase (Later)

- Implement UUID → PyG index mapping
- Build feature encoders (categorical, text embeddings)
- Create HeteroData builder from PROVES entities

---

## 12. References

**Official Documentation:**
- [PyTorch Geometric Documentation](https://pytorch-geometric.readthedocs.io/)
- [Introduction by Example](https://pytorch-geometric.readthedocs.io/en/2.6.1/get_started/introduction.html)
- [Heterogeneous Graph Learning](https://pytorch-geometric.readthedocs.io/en/latest/notes/heterogeneous.html)
- [Data Class API](https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.data.Data.html)
- [HeteroData Class API](https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.data.HeteroData.html)

**Repository:**
- [PyTorch Geometric GitHub](https://github.com/pyg-team/pytorch_geometric)
- [GNN Cheatsheet](https://pytorch-geometric.readthedocs.io/en/latest/cheatsheet/gnn_cheatsheet.html)

**Tutorials:**
- [Link Prediction on Heterogeneous Graphs](https://medium.com/@pytorch_geometric/link-prediction-on-heterogeneous-graphs-with-pyg-6d5c29677c70)
- [GraphSAGE Case Study](https://towardsdatascience.com/a-comprehensive-case-study-of-graphsage-algorithm-with-hands-on-experience-using-pytorchgeometric-6fc631ab1067/)

**PROVES Documentation:**
- `.deepagents/IMPLEMENTATION_ROADMAP.md` - Current phase goals
- `docs/architecture/KNOWLEDGE_GRAPH_SCHEMA.md` - PROVES relationship vocabulary (ERV)
- `neon-database/migrations/015_add_standard_mapping_enrichment.sql` - Mapping infrastructure

---

**Status:** PyTorch Geometric vocabulary study complete. Ready for SysML v2 vocabulary study.
