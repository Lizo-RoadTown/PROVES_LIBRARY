# MBSE Standards Integration for PROVES Library

Discussion document for integrating Model-Based Systems Engineering (MBSE) standards with the PROVES ontology and extraction pipeline.

## Current State: PROVES Ontology

### FRAMES Methodology (Osborn, 2025)
Your existing framework defines:

**Structural Elements:**
- **Components**: Discrete modules (what exists)
- **Interfaces**: Connection points (where they connect)
- **Flows**: What moves through interfaces (data, power, heat)
- **Mechanisms**: What maintains connections (protocols, docs, procedures)

**Dimensional Metadata** (From [canon/KNOWLEDGE_FRAMEWORK.md](../canon/KNOWLEDGE_FRAMEWORK.md)):
1. **Contact** - Signal strength between phenomenon and observer
2. **Directionality** - Epistemic operation (forward, backward, bidirectional)
3. **Temporality** - Dependence on history (snapshot, sequence, lifecycle)
4. **Formalizability** - Capacity for symbolic transformation

**Five-Attribute Edge Model:**
1. Directionality (flow direction)
2. Strength (always, sometimes, never)
3. Mechanism (electrical, thermal, timing, protocol)
4. Knownness (verified, assumed, unknown, disproved)
5. Scope (version, hardware revision, mode)

## MBSE Standards Landscape

### 1. SysML (Systems Modeling Language)

**What it is:**
- UML profile for systems engineering
- Industry standard for MBSE
- Supported by tools like Cameo, Enterprise Architect, MagicDraw

**Core Diagram Types:**
- **Block Definition Diagram (BDD)** - System structure (similar to your Components)
- **Internal Block Diagram (IBD)** - Internal structure and connections (similar to your Interfaces + Flows)
- **Activity Diagram** - Behavior and processes
- **Sequence Diagram** - Interactions over time
- **Requirement Diagram** - Requirements traceability
- **Parametric Diagram** - Constraints and equations

**Mapping to PROVES:**
```
SysML Block → PROVES Component
SysML Port → PROVES Interface
SysML Flow Property → PROVES Flow
SysML Dependency → PROVES Dependency (with 5 attributes)
```

### 2. SysML v2 (Next Generation)

**New in SysML v2:**
- Textual syntax (machine-readable!)
- Better API support
- Formal semantics
- Improved analysis capabilities

**Why it matters for PROVES:**
- **Textual format** → Easier for LLMs to extract
- **API-first** → Can programmatically create SysML models from extractions
- **Formal semantics** → Better verification of extracted knowledge

### 3. ISO 81346 (System Structuring)

**What it is:**
- International standard for industrial systems and reference designation
- Defines hierarchical structure and naming conventions

**Key Concepts:**
- **Aspect** (function, product, location)
- **Reference designation** (hierarchical identifiers)
- **Cross-referencing** between aspects

**Relevance to PROVES:**
- Standardized naming for Components
- Hierarchical organization
- Multi-aspect views (functional vs. physical vs. locational)

### 4. ReqIF (Requirements Interchange Format)

**What it is:**
- XML format for requirements exchange
- OMG standard
- Tool-agnostic requirements representation

**Use for PROVES:**
- Extract requirements from documentation
- Link requirements to components/interfaces
- Traceability matrix

### 5. OSLC (Open Services for Lifecycle Collaboration)

**What it is:**
- Standards for tool integration
- RESTful APIs for lifecycle data
- Supports SysML, requirements, test management

**Potential Use:**
- Integrate PROVES with existing MBSE tools
- Export knowledge graph to SysML tools
- Bi-directional sync

## Standardization Opportunities

### Option 1: SysML Alignment (Recommended)

**Approach:**
Map PROVES ontology to SysML v2 constructs while preserving dimensional metadata.

**Pros:**
- Industry-standard vocabulary
- Tool interoperability
- Existing validation rules
- Widely understood by systems engineers

**Cons:**
- SysML doesn't natively support dimensional metadata
- May require custom stereotypes/profiles
- Could lose some PROVES-specific semantics

**Implementation:**
```python
# Extraction produces both PROVES format and SysML v2
extraction = {
    # PROVES format (primary)
    "proves": {
        "candidate_type": "component",
        "dimensional_metadata": {...},
        "five_attributes": {...}
    },
    # SysML v2 mapping (for interop)
    "sysml": {
        "element_type": "Block",
        "stereotype": "<<Hardware>>",
        "tagged_values": {
            "contact": "0.85",
            "knownness": "verified",
            # ... map other metadata
        }
    }
}
```

### Option 2: Hybrid Ontology

**Approach:**
Use SysML for structure, PROVES extensions for epistemics.

**Structure:**
- SysML Block Definition for system architecture
- PROVES dimensional metadata as custom properties
- Five-attribute edge model as SysML relationship stereotypes

**Tools needed:**
- SysML v2 API client
- Custom SysML profile for PROVES extensions
- Bidirectional mapping layer

### Option 3: PROVES-First with SysML Export

**Approach:**
Keep PROVES ontology as primary, generate SysML views for interoperability.

**Workflow:**
```
Documentation → Deep Agent Extraction → PROVES Graph
                                            ↓
                                    Generate Views:
                                    - SysML v2 model
                                    - ReqIF requirements
                                    - GraphML structure
```

**Pros:**
- Preserves full PROVES semantics
- Flexible - can export to multiple formats
- No compromises on dimensional metadata

**Cons:**
- PROVES remains non-standard
- Requires maintenance of multiple exporters
- Users must understand PROVES ontology

## Tool Integration Options

### For Extraction

**Current: Deep Agents**
- ✅ Already integrated
- ✅ Planning and file system for complex docs
- ✅ Subagents for parallel extraction

**Add: SysML Parser**
- Parse existing SysML v2 textual models
- Extract knowledge from formal models
- Tool: `pysysml` or SysML v2 API

**Add: ReqIF Parser**
- Extract requirements from tool exports
- Link to components/interfaces
- Tool: `reqif` Python library

### For Validation

**Option: SysML Model Checker**
- Validate extracted knowledge against SysML constraints
- Check for structural inconsistencies
- Tool: Eclipse SysML v2 validator

**Option: Custom Ontology Validator**
- Verify PROVES-specific rules
- Check dimensional metadata completeness
- Validate five-attribute edges

### For Visualization

**Option: SysML Tool Export**
- Generate SysML v2 files from graph
- Import into Cameo, MagicDraw, etc.
- Visual modeling with standard tools

**Option: Custom Graph Visualizer**
- D3.js for interactive exploration
- Color-code by dimensional metadata
- Filter by contact, knownness, etc.

**Option: Hybrid**
- Standard SysML views for architecture
- Custom views for epistemic properties
- Both exported from same graph

## Recommended Approach

### Phase 1: SysML v2 Mapping Layer (3-4 weeks)

1. **Define mapping rules**:
   ```python
   # proves_to_sysml.py
   def map_component_to_block(component: Dict) -> SysMLBlock:
       """Map PROVES component to SysML v2 Block"""
       block = SysMLBlock(
           name=component["candidate_key"],
           stereotype=infer_stereotype(component),
       )
       # Add dimensional metadata as tagged values
       block.add_tagged_value("contact", component["contact"])
       # ...
       return block
   ```

2. **Create bidirectional converter**:
   - PROVES → SysML v2 (for export)
   - SysML v2 → PROVES (for import from existing models)

3. **Test with F Prime model**:
   - Export PROVES extractions to SysML
   - Validate in SysML tool
   - Import back and verify preservation

### Phase 2: Extraction Enhancement (2-3 weeks)

1. **Add SysML awareness to extraction agent**:
   ```python
   EXTRACTION_SYSTEM_PROMPT += """
   When extracting, also identify SysML element types:
   - Blocks (components)
   - Ports (interfaces)
   - Flow Properties (flows)
   - Dependencies (relationships)

   Provide both PROVES and SysML classifications.
   """
   ```

2. **Create SysML parser tool**:
   ```python
   @tool
   def parse_sysml_model(file_path: str) -> Dict:
       """Parse SysML v2 textual model and extract knowledge"""
       # Use SysML v2 API
       model = parse_sysml_v2(file_path)
       # Convert to PROVES format
       return convert_to_proves(model)
   ```

3. **Add to deep agent tools**:
   ```python
   agent = create_deep_agent(
       tools=[
           fetch_documentation,
           parse_sysml_model,  # NEW
           query_staging,
           insert_staging,
       ]
   )
   ```

### Phase 3: Tool Integration (4-5 weeks)

1. **SysML v2 export pipeline**:
   - Generate `.sysml` files from PROVES graph
   - Maintain directory structure matching system hierarchy
   - Include custom profile for PROVES metadata

2. **Validation workflow**:
   - Export to SysML
   - Validate with SysML tools
   - Import validation results
   - Flag inconsistencies in PROVES

3. **Visualization**:
   - SysML BDD/IBD for standard views
   - Custom D3.js for epistemic views
   - Integrated dashboard

## Discussion Points

### 1. How much SysML conformance?

**Option A: Full Conformance**
- All PROVES knowledge expressible in SysML v2
- Dimensional metadata as custom stereotypes
- Standard tooling compatibility

**Option B: Partial Conformance**
- SysML for structure only
- PROVES extensions for epistemics
- Custom tooling required

**Option C: SysML Export Only**
- PROVES remains primary
- Generate SysML views on demand
- Best of both worlds?

**Question:** Which aligns with your research goals and user needs?

### 2. Tool Investment

**Lightweight:**
- SysML v2 API (free, open source)
- Custom Python converters
- D3.js visualization

**Enterprise:**
- Cameo Systems Modeler license
- Enterprise Architect integration
- Professional visualization tools

**Question:** What's the budget and timeline?

### 3. Standardization Scope

**Narrow:**
- Just structure (components, interfaces)
- Keep epistemics PROVES-specific

**Broad:**
- Full ontology alignment
- SysML + custom profile
- Submit profile to OMG?

**Question:** Is this for internal use or broader adoption?

### 4. Validation Strategy

**Self-Validation:**
- PROVES-specific rules only
- No external dependencies

**Standards-Based:**
- Validate against SysML metamodel
- Leverage existing checkers
- Industry best practices

**Hybrid:**
- Structure validated by SysML
- Epistemics validated by PROVES
- Best error detection?

**Question:** What level of formal validation is needed?

## Next Steps

1. **Review this document** and identify priorities
2. **Decide on conformance level** (A, B, or C above)
3. **Prototype SysML mapping** for one component type
4. **Test with existing extraction** to see what breaks
5. **Iterate on mapping rules** until stable
6. **Implement in deep agent** extraction workflow

## Resources

- **[SysML v2 Release](https://github.com/Systems-Modeling/SysML-v2-Release)** - Official spec and API
- **[ISO 81346](https://www.iso.org/standard/81346.html)** - System structuring
- **[ReqIF](https://www.omg.org/spec/ReqIF/)** - Requirements format
- **[OSLC](https://open-services.net/)** - Tool integration
- **[PROVES FRAMES](../canon/KNOWLEDGE_FRAMEWORK.md)** - Current ontology
- **[Deep Agent Integration](INTEGRATION.md)** - Extraction workflow

## Questions for Discussion

1. **Primary use case**: Internal research? Industry tool? Both?
2. **Existing models**: Do you have SysML models to integrate with?
3. **Tool preference**: Command-line? GUI? Both?
4. **Timeline**: When do you need SysML compatibility?
5. **Audience**: Systems engineers familiar with SysML? Or teaching FRAMES?

---

**Let's discuss and I can help implement the chosen approach!**
