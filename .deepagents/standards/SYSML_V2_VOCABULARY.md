# SysML v2 Vocabulary Study

**Purpose:** Understand SysML v2 (Systems Modeling Language version 2) naming conventions and modeling constructs to ensure PROVES canonical naming aligns naturally with Model-Based Systems Engineering (MBSE) standards.

**Standard:** SysML v2 (OMG Systems Modeling Language)
**Use Case:** Model-Based Systems Engineering (MBSE), system architecture, requirements modeling
**Version:** 2.0

---

## 1. SysML v2 Overview

### 1.1 What is SysML v2?

**Definition:** SysML v2 is the next-generation systems modeling language, providing significant enhancements over SysML version 1 in terms of:
- **Precision**: Grounded in formal semantics (KerML metamodel)
- **Expressiveness**: Richer modeling constructs
- **Usability**: Both textual and graphical syntax
- **Interoperability**: Standard API support
- **Extensibility**: Definition/Usage pattern for reuse

**Purpose:** Facilitate Model-Based Systems Engineering (MBSE) approach for complex system design, requirements management, and architecture documentation.

### 1.2 Key Innovation: Definition vs Usage Pattern

**Core Concept:** SysML v2 systematically distinguishes between:
- **Definition**: Type description (like a blueprint or datasheet) - valid for a class of similar entities
- **Usage**: Specific instance of a definition in a particular context - how a definition is used

**Visual Convention:**
- **Definitions**: Rectangular symbols with **sharp corners**
- **Usages**: Rectangular symbols with **rounded corners**

**Reuse Pattern:** Model elements can be defined once with their features, then reused in different contexts.

**Applies to all major concepts:**
- Part (PartDefinition / PartUsage)
- Port (PortDefinition / PortUsage)
- Connection (ConnectionDefinition / ConnectionUsage)
- Requirement (RequirementDefinition / RequirementUsage)
- Action (ActionDefinition / ActionUsage)
- State (StateDefinition / StateUsage)
- Attribute (AttributeDefinition / AttributeUsage)

---

## 2. SysML v2 Core Vocabulary

### 2.1 PartDefinition and PartUsage

**PartDefinition** (replaces SysML v1 "Block")

**Definition:** An OccurrenceDefinition representing the structure of things that may be systems or parts of systems - modular units of structure such as system components or external entities.

**Textual Notation:**
```sysml
part def Vehicle {
    attribute mass: Real;
    attribute length: Real;
    port fuelPort: FuelPort;
    part engine: Engine;
    part transmission: Transmission;
}
```

**Typical Features:**
- Attributes (properties/characteristics)
- Ports (interaction points)
- Nested parts (composition)
- Constraints
- Requirements

**PartUsage** (replaces SysML v1 "part property")

**Definition:** A specific instance/usage of a PartDefinition in a particular context.

**Textual Notation:**
```sysml
part myCar: Vehicle {
    attribute :>> mass = 1500;  // Overriding/refining attribute
    part :>> engine: V8Engine;  // Specific engine type
}
```

**Metamodel:** `PartUsage | PartDefinition`

---

### 2.2 PortDefinition and PortUsage

**PortDefinition**

**Definition:** Defines an interaction point on a part - a connection point for communication, material flow, or energy transfer.

**Textual Notation:**
```sysml
port def FuelPort {
    in fuel: Fuel;      // Incoming item
    out fuelStatus: Status;  // Outgoing item
}

port def DataPort {
    in commandData: CommandMessage;
    out telemetryData: TelemetryMessage;
}
```

**Typical Features:**
- Input items (incoming data/materials)
- Output items (outgoing data/materials)
- Bidirectional flows

**PortUsage**

**Definition:** A specific port instance on a part.

**Example:**
```sysml
part def RadioComponent {
    port commandPort: CommandPort;
    port telemetryPort: TelemetryPort;
}
```

**Purpose:** Ports enable parts to interact with one another - defining communication points for parts, while connections model the flow of information, materials, or energy between them.

---

### 2.3 ConnectionDefinition and ConnectionUsage

**ConnectionDefinition**

**Definition:** Represents a relationship between parts through their ports - describes how parts are connected.

**Textual Notation:**
```sysml
connection def DataConnection {
    end sourceEnd: DataPort;
    end targetEnd: DataPort;
}
```

**Key Characteristics:**
- Defined by connection endpoints
- Can specify flow direction
- May include interface specifications

**ConnectionUsage**

**Definition:** A specific connection instance in a system context.

**Example:**
```sysml
part def System {
    part componentA: ComponentA {
        port output: DataPort;
    }
    part componentB: ComponentB {
        port input: DataPort;
    }

    // Connection usage
    interface connect componentA.output to componentB.input {
        flow from componentA.output to componentB.input;
    }
}
```

**SysML v1 → v2 Mapping:**
- SysML v1 connector → SysML v2 connection
- SysML v1 proxy port and interface block → SysML v2 port and port definition

---

### 2.4 ItemDefinition and ItemUsage

**ItemDefinition**

**Definition:** An OccurrenceDefinition representing the structure of things that may themselves be systems or parts of systems - primarily spatial occurrences that can be passed between components or acted on by systems.

**Purpose:** Represents entities that flow through the system (data, materials, energy).

**Example:**
```sysml
item def Fuel {
    attribute octaneRating: Integer;
    attribute volume: Real;
}

item def TelemetryPacket {
    attribute timestamp: Time;
    attribute sensorData: SensorReading[*];
}
```

**Distinction from Part:**
- **Part**: Structural component of the system (persists)
- **Item**: Entity that flows or is acted upon (transient)

---

### 2.5 AttributeDefinition and AttributeUsage

**AttributeDefinition**

**Definition:** Defines a data type for representing values, properties, or characteristics.

**Textual Notation:**
```sysml
attribute def Mass {
    attribute value: Real;
    attribute unit: MassUnit;
}
```

**AttributeUsage**

**Definition:** A usage whose type is a DataType - represents the value of some system quality or characteristic.

**Key Constraint:** AttributeUsage and all nested features must be referential (non-composite).

**Example:**
```sysml
part def Component {
    attribute mass: Mass;
    attribute serialNumber: String;
    attribute isActive: Boolean;
}
```

**Purpose:** Represents properties, parameters, configuration values.

---

### 2.6 InterfaceDefinition and InterfaceUsage

**InterfaceDefinition**

**Definition:** Defines a specification for how parts interact through ports.

**InterfaceUsage**

**Definition:** A usage of an InterfaceDefinition to represent an interface connecting parts of a system through specific connection points.

**Key Concept:** SysML v2 Interface is a kind of connection whose connection ends are ports.

**Example:**
```sysml
interface def SerialInterface {
    port end transmitter: SerialPort;
    port end receiver: SerialPort;
}
```

---

### 2.7 RequirementDefinition and RequirementUsage

**RequirementDefinition**

**Definition:** Defines a requirement type or template.

**RequirementUsage**

**Definition:** A specific requirement instance in a system context.

**Special Relationships:**
- **Satisfy**: Relationship between a requirement and a model element that satisfies it
- **Refine**: Specifies that model elements refine other model elements
- **Conform**: Models that elements conform to other elements
- **Allocate**: Allocation relationship (similar to SysML v1)

**Direction:** Most requirement relationships are based on UML dependency - arrow points from dependent (client) to independent (supplier).

---

## 3. SysML v2 Relationship Types

### 3.1 Four Specialization Relationships

SysML v2 defines four distinct specialization relationships:

**1. Subclassification**
- Inheritance relationship between definitions
- A SubDef is a specialization of a more general definition
- Inherits properties from parent

**2. Subsetting**
- A usage represents a restricted subset of another usage
- Applied to ports, attributes, roles
- Usage-level relationship

**3. Redefinition**
- Refines inherited features in specialized context
- Allows overriding/specializing inherited properties

**4. Definition**
- Links a usage to its definition
- Answers: "What type is this specific element?"

---

### 3.2 Dependency Relationships

SysML v2 provides multiple dependency relationship types:

| Relationship | Description | Example |
|--------------|-------------|---------|
| **Dependency** | Generic dependency between model elements | Component A depends on Component B |
| **Satisfy** | Requirement satisfied by model element | Design satisfies requirement |
| **Refine** | Model element refines another | Detailed design refines high-level architecture |
| **Conform** | Element conforms to specification | Implementation conforms to interface |
| **Allocate** | Allocation relationship | Function allocated to component |

**Direction:** Arrow points from dependent (client) to independent (supplier).

---

## 4. SysML v2 Naming Conventions

### 4.1 Keyword Patterns

**Definition Keywords:**
- `part def` - Part definition
- `port def` - Port definition
- `connection def` - Connection definition
- `item def` - Item definition
- `attribute def` - Attribute definition
- `requirement def` - Requirement definition
- `action def` - Action definition
- `state def` - State definition

**Usage Keywords:**
- `part` - Part usage
- `port` - Port usage
- `connection` - Connection usage
- `item` - Item usage
- `attribute` - Attribute usage
- `requirement` - Requirement usage

### 4.2 Naming Style

**Convention:** PascalCase for definition names (like class names)

**Examples:**
- `part def Vehicle`
- `port def CommandPort`
- `connection def DataConnection`
- `item def TelemetryPacket`

**Instance Names:** camelCase for usage instances

**Examples:**
- `part myCar: Vehicle`
- `port commandPort: CommandPort`
- `attribute serialNumber: String`

### 4.3 Graphical Notation Conventions

**Definitions:**
- Rectangular symbols with **sharp corners**
- Represent type/blueprint

**Usages:**
- Rectangular symbols with **rounded corners**
- Represent instances

**Stereotypes:**
- Used to indicate specific kinds of elements
- Examples: `<<Hardware>>`, `<<Software>>`, `<<External>>`

---

## 5. SysML v1 to SysML v2 Mapping

### 5.1 Terminology Changes

| SysML v1 | SysML v2 | Notes |
|----------|----------|-------|
| Block | PartDefinition | Renamed to emphasize Definition/Usage pattern |
| Part property | PartUsage | Explicitly separated usage from definition |
| Proxy port | PortDefinition | Clearer separation of interface definition |
| Interface block | PortDefinition | Integrated into port concept |
| Connector | Connection (ConnectionUsage) | More precise terminology |
| Value property | AttributeUsage | Clearer semantic distinction |

### 5.2 Diagram Mapping

| SysML v1 | SysML v2 | Level |
|----------|----------|-------|
| Block Definition Diagram (bdd) | Part Definition diagram | Definition level |
| Internal Block Diagram (ibd) | Part Usage diagram | Usage level |

### 5.3 Conceptual Evolution

**SysML v1 Limitation:** Mixed definition and usage concepts
**SysML v2 Solution:** Systematic Definition/Usage pattern across all elements

**Benefits:**
- Clearer reuse semantics
- More precise modeling
- Better tool interoperability
- Domain-specific model libraries

---

## 6. PROVES → SysML v2 Alignment Table

### 6.1 Entity Type Mappings

| PROVES `entity_type` | SysML v2 Equivalent | Alignment Status | Notes |
|----------------------|---------------------|------------------|-------|
| `component` | PartDefinition | **Aligned** | PROVES Component = SysML Part |
| `port` | PortDefinition | **Aligned** | Direct 1:1 mapping |
| `dependency` | Dependency relationship | **Aligned** | SysML has explicit dependency construct |
| `connection` | ConnectionUsage | **Aligned** | PROVES Connection = SysML Connection |
| `parameter` | AttributeUsage | **Adjacent** | Parameter as attribute/property of part |
| `command` | PortUsage (input) or ActionUsage | **Adjacent** | Commands could be input ports or actions |
| `telemetry` | PortUsage (output) or ItemFlow | **Adjacent** | Telemetry as output port or flowing item |
| `event` | EventOccurrence or StateChange | **Adjacent** | Events as state transitions or occurrences |
| `data_type` | AttributeDefinition or ItemDefinition | **Aligned** | Type definitions map cleanly |

---

### 6.2 Detailed Alignment Analysis

#### 6.2.1 Component → PartDefinition

**Alignment:** Aligned (1:1)

**PROVES Concept:**
- Software or hardware component (e.g., `RadioDriver`, `PowerDriver`)
- Has attributes, ports, dependencies
- Modular unit in system architecture

**SysML v2 Concept:**
- PartDefinition = modular unit of structure (system component)
- Has attributes, ports, nested parts
- Can represent hardware or software

**Mapping Strategy:**
```sysml
// PROVES Component: RadioDriver
part def RadioDriver {
    // Attributes from PROVES
    attribute ecosystem: String = "fprime";
    attribute namespace: String = "Radio";
    attribute verificationStatus: VerificationStatus;

    // Ports (from PROVES port entities)
    port commandPort: CommandPort;
    port telemetryPort: TelemetryPort;
    port statusPort: StatusPort;
}
```

**Constraints:**
- PROVES `canonical_key` → SysML part name
- PROVES `namespace` → SysML package/subsystem hierarchy
- PROVES `attributes` → SysML attribute usages

**Example Mapping Record:**
```json
{
  "standard": "sysml_v2",
  "standard_key": "PartDefinition",
  "standard_name": "RadioDriver",
  "standard_constraints": {
    "package": "CommunicationsSubsystem",
    "stereotype": "<<Software>>"
  }
}
```

---

#### 6.2.2 Port → PortDefinition/PortUsage

**Alignment:** Aligned (1:1)

**PROVES Concept:**
- Interface point on component
- Direction: input/output
- Type: command, telemetry, data, async

**SysML v2 Concept:**
- PortDefinition = interaction point specification
- PortUsage = specific port on part
- Can specify input/output items

**Mapping Strategy:**
```sysml
// PROVES Port: CommandPort (direction=input, type=command)
port def CommandPort {
    in command: CommandMessage;
    out acknowledgment: AckMessage;
}

// Usage in component
part def RadioDriver {
    port commandPort: CommandPort;  // PortUsage
}
```

**Direction Mapping:**
- PROVES `direction=input` → SysML `in` item
- PROVES `direction=output` → SysML `out` item
- PROVES `direction=bidirectional` → Both `in` and `out` items

**Constraints:**
```json
{
  "standard": "sysml_v2",
  "standard_key": "PortDefinition",
  "standard_name": "CommandPort",
  "standard_constraints": {
    "direction": "input",
    "port_type": "command",
    "item_type": "CommandMessage"
  }
}
```

---

#### 6.2.3 Dependency → Dependency Relationship

**Alignment:** Aligned (1:1)

**PROVES Concept:**
- Component A depends on Component B
- Engineering Relationship Vocabulary (ERV): strength, mechanism, knownness, scope

**SysML v2 Concept:**
- Dependency relationship between model elements
- Arrow from dependent (client) to independent (supplier)
- Can be refined with stereotypes

**Mapping Strategy:**
```sysml
part def RadioDriver {
    // Dependency on PowerDriver
}

part def PowerDriver {
    // Provides power
}

// Dependency relationship (graphical or textual)
dependency RadioDriver -> PowerDriver {
    // ERV attributes as metadata
    attribute strength: DependencyStrength = always;
    attribute mechanism: DependencyMechanism = electrical;
    attribute knownness: Knownness = known;
}
```

**ERV Mapping:**
- PROVES ERV attributes → SysML dependency metadata or stereotypes
- Could use custom stereotypes: `<<ElectricalDependency>>`, `<<SoftwareDependency>>`

**Alternative:** Use SysML Allocate relationship
```sysml
allocate RadioDriver to PowerDriver;
```

**Constraints:**
```json
{
  "standard": "sysml_v2",
  "standard_key": "Dependency",
  "standard_name": "RadioDriver_DependsOn_PowerDriver",
  "standard_constraints": {
    "client": "RadioDriver",
    "supplier": "PowerDriver",
    "erv_strength": "always",
    "erv_mechanism": "electrical"
  }
}
```

---

#### 6.2.4 Connection → ConnectionUsage

**Alignment:** Aligned (1:1)

**PROVES Concept:**
- Port-to-port connection
- Data flow path between components

**SysML v2 Concept:**
- ConnectionUsage = specific connection between ports
- Can specify flow direction
- Interface defines connection protocol

**Mapping Strategy:**
```sysml
part def System {
    part radioDriver: RadioDriver {
        port telemetryPort: TelemetryPort;
    }
    part dataLogger: DataLogger {
        port inputPort: DataInputPort;
    }

    // Connection (PROVES Connection entity)
    interface connect radioDriver.telemetryPort to dataLogger.inputPort {
        flow from radioDriver.telemetryPort to dataLogger.inputPort;
    }
}
```

**Constraints:**
```json
{
  "standard": "sysml_v2",
  "standard_key": "ConnectionUsage",
  "standard_name": "RadioToLogger_DataConnection",
  "standard_constraints": {
    "source_part": "radioDriver",
    "source_port": "telemetryPort",
    "target_part": "dataLogger",
    "target_port": "inputPort"
  }
}
```

---

#### 6.2.5 Parameter → AttributeUsage

**Alignment:** Adjacent (context-dependent)

**PROVES Concept:**
- Configurable parameter or telemetry value
- May be property of component or standalone entity

**SysML v2 Concept:**
- AttributeUsage = property/characteristic of a part
- Represents values, not structural elements

**Mapping Strategy:**

**Option 1: Parameter as Part Attribute**
```sysml
part def RadioDriver {
    attribute frequency: Real;  // Parameter
    attribute powerLevel: Integer;  // Parameter
    attribute batteryVoltage: Real;  // Telemetry value
}
```

**Option 2: Parameter as ItemFlow**
If parameter is a data entity that flows:
```sysml
item def FrequencyParameter {
    attribute value: Real;
    attribute unit: FrequencyUnit;
}

port def ConfigPort {
    in frequencyParam: FrequencyParameter;
}
```

**Decision:** Depends on whether parameter is:
- **Configuration property** → AttributeUsage
- **Flowing data** → ItemDefinition + port

**Constraints:**
```json
{
  "standard": "sysml_v2",
  "standard_key": "AttributeUsage",
  "standard_name": "frequency",
  "standard_constraints": {
    "owner_part": "RadioDriver",
    "data_type": "Real",
    "unit": "MHz"
  }
}
```

---

#### 6.2.6 Command → ActionUsage or PortUsage

**Alignment:** Adjacent (context-dependent)

**PROVES Concept:**
- Telecommand or software command
- Action that can be invoked

**SysML v2 Options:**

**Option 1: Command as ActionUsage**
```sysml
action def SetRadioPower {
    in powerLevel: Integer;
    out success: Boolean;
}

part def RadioDriver {
    action setRadioPower: SetRadioPower;
}
```

**Option 2: Command as Input Port**
```sysml
port def CommandPort {
    in setPowerCommand: SetPowerCommand;
    out commandAck: Acknowledgment;
}

part def RadioDriver {
    port commandPort: CommandPort;
}
```

**Recommendation:** Use PortUsage for interface-based commands (like XTCE MetaCommand), ActionUsage for internal behaviors.

**Constraints:**
```json
{
  "standard": "sysml_v2",
  "standard_key": "ActionUsage",
  "standard_name": "SetRadioPower",
  "standard_constraints": {
    "owner_part": "RadioDriver",
    "inputs": ["powerLevel:Integer"],
    "outputs": ["success:Boolean"]
  }
}
```

---

#### 6.2.7 Telemetry → PortUsage or ItemFlow

**Alignment:** Adjacent (context-dependent)

**PROVES Concept:**
- Telemetry data value (sensor reading, status)
- Typically output from component

**SysML v2 Options:**

**Option 1: Telemetry as Output Port**
```sysml
port def TelemetryPort {
    out batteryVoltage: VoltageReading;
    out temperature: TemperatureReading;
    out status: StatusMessage;
}

part def PowerDriver {
    port telemetryPort: TelemetryPort;
}
```

**Option 2: Telemetry as ItemFlow**
```sysml
item def TelemetryPacket {
    attribute timestamp: Time;
    attribute sensorId: String;
    attribute value: Real;
}

interface connect powerDriver.telemetryPort to groundStation.receivePort {
    flow of TelemetryPacket from powerDriver.telemetryPort to groundStation.receivePort;
}
```

**Recommendation:** Use PortUsage with output items for telemetry channels.

**Constraints:**
```json
{
  "standard": "sysml_v2",
  "standard_key": "PortUsage",
  "standard_name": "telemetryPort",
  "standard_constraints": {
    "owner_part": "PowerDriver",
    "direction": "output",
    "item_types": ["VoltageReading", "TemperatureReading", "StatusMessage"]
  }
}
```

---

#### 6.2.8 Event → EventOccurrence or StateChange

**Alignment:** Adjacent

**PROVES Concept:**
- Event log entry or notification
- Severity-based (INFO, WARNING, ERROR)

**SysML v2 Options:**

**Option 1: Event as State Change**
```sysml
state def RadioState {
    entry / sendEvent("Radio State Entered");
    exit / sendEvent("Radio State Exited");
}
```

**Option 2: Event as ItemFlow**
```sysml
item def EventMessage {
    attribute severity: EventSeverity;
    attribute message: String;
    attribute timestamp: Time;
}

port def EventPort {
    out event: EventMessage;
}
```

**Recommendation:** Use ItemFlow for event messages, State machines for state-based events.

---

#### 6.2.9 Data Type → AttributeDefinition or ItemDefinition

**Alignment:** Aligned (1:1)

**PROVES Concept:**
- Type definition (int32, float64, enum, struct)
- Specifies data format, units, constraints

**SysML v2 Concept:**
- AttributeDefinition = data type for attributes
- ItemDefinition = data type for flowing items

**Mapping Strategy:**
```sysml
attribute def VoltageType {
    attribute value: Real;
    attribute unit: VoltageUnit;
    attribute range: RealRange {
        attribute min: Real = 0.0;
        attribute max: Real = 50.0;
    }
}

item def CommandMessage {
    attribute commandId: Integer;
    attribute payload: String;
    attribute checksum: Integer;
}
```

**Decision:**
- **Attribute data type** → AttributeDefinition
- **Flowing data type** → ItemDefinition

**Constraints:**
```json
{
  "standard": "sysml_v2",
  "standard_key": "AttributeDefinition",
  "standard_name": "VoltageType",
  "standard_constraints": {
    "base_type": "Real",
    "unit": "Volts",
    "min": 0.0,
    "max": 50.0
  }
}
```

---

## 7. Namespace and Package Organization

### 7.1 SysML v2 Package Structure

**Concept:** Packages organize model elements into namespaces/hierarchies.

**Example:**
```sysml
package CommunicationsSubsystem {
    part def RadioDriver { ... }
    part def AntennaController { ... }
    port def RadioCommandPort { ... }
}

package PowerSubsystem {
    part def PowerDriver { ... }
    part def BatteryMonitor { ... }
}
```

### 7.2 PROVES Namespace Mapping

**PROVES Fields:**
- `ecosystem`: 'fprime', 'ros2', 'cubesat'
- `namespace`: Optional hierarchical path

**SysML v2 Mapping:**
```
ecosystem='fprime', namespace='Radio'
  → package fprime::Radio { ... }

ecosystem='cubesat', namespace='PowerSubsystem'
  → package cubesat::PowerSubsystem { ... }
```

**Constraints:**
```json
{
  "package": "fprime::CommunicationsSubsystem",
  "stereotype": "<<Software>>"
}
```

---

## 8. Constraints on Future SysML v2 Exporters

### 8.1 Must-Follow Rules

1. **No Renaming**
   - PROVES `canonical_key` → SysML element name (part def, port def, etc.)
   - Exporter MUST NOT invent new names or modify existing ones

2. **Read from Mappings Table**
   - Query `knowledge_enrichment` for `standard='sysml_v2'` mappings
   - If mapping missing, fail loudly (do not guess)

3. **Respect Alignment Categories**
   - **Aligned** entities: Direct export (Component → PartDefinition)
   - **Adjacent** entities: Use `standard_constraints` to determine context
   - **Novel** entities: Mark as not exportable to SysML v2

4. **Namespace Preservation**
   - PROVES `ecosystem` + `namespace` → SysML package hierarchy
   - Do not flatten structure

5. **Definition vs Usage**
   - Export both PartDefinition (type) and PartUsage (instance) if needed
   - For type libraries: Export definitions only
   - For system models: Export both definitions and usages

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
  '123e4567-e89b-12d3-a456-426614174000',
  'standard_mapping',
  'sysml_v2',
  '2.0',
  'PartDefinition',
  'RadioDriver',
  '{
    "package": "fprime::CommunicationsSubsystem",
    "stereotype": "<<Software>>",
    "attributes": {
      "ecosystem": "fprime",
      "namespace": "Radio",
      "verificationStatus": "human_verified"
    },
    "ports": ["commandPort", "telemetryPort", "statusPort"]
  }'::jsonb
);
```

### 8.3 Exporter Logic Pattern

```python
# Query for SysML v2 mappings
mappings = db.execute("""
  SELECT * FROM standard_mappings
  WHERE standard = 'sysml_v2'
    AND entity_id = %s
""", [entity_id])

if not mappings:
    raise ValueError(f"No SysML v2 mapping for entity {entity_id}")

# Use mapping data
sysml_type = mapping['standard_key']  # e.g., 'PartDefinition'
sysml_name = mapping['standard_name']  # e.g., 'RadioDriver'
constraints = mapping['standard_constraints']
package = constraints['package']
stereotype = constraints.get('stereotype', '')

# Generate SysML v2 textual notation
output = f"""
package {package} {{
    {stereotype}
    part def {sysml_name} {{
        // Attributes, ports, etc.
    }}
}}
"""
```

---

## 9. Open Questions for Canonical Naming Phase

### 9.1 Component Stereotypes

**Question:** Should PROVES `entity_type` values map to SysML stereotypes?

**Options:**
- `entity_type='component'` → `<<Software>>` or `<<Hardware>>`?
- Use PROVES `attributes` to determine stereotype
- Define PROVES-specific stereotypes: `<<FPrimeComponent>>`, `<<ROS2Node>>`

**Decision:** TBD

### 9.2 Parameter vs Attribute Boundary

**Question:** When is a PROVES Parameter an AttributeUsage vs ItemDefinition?

**Current Ambiguity:**
- Is Parameter a configuration property (static attribute)?
- Is Parameter a flowing value (item)?

**Decision:** TBD - establish clear boundary in canonical naming

### 9.3 Command Representation

**Question:** Should PROVES Commands be ActionUsage or PortUsage?

**Trade-offs:**
- **ActionUsage**: Emphasizes behavior, matches software design
- **PortUsage**: Emphasizes interface, matches XTCE MetaCommand

**Proposal:** Use PortUsage for consistency with XTCE alignment

**Decision:** TBD

### 9.4 ERV Metadata Encoding

**Question:** How should PROVES Engineering Relationship Vocabulary (ERV) map to SysML?

**Options:**
1. Custom dependency stereotypes: `<<ElectricalDependency>>`
2. Dependency metadata attributes
3. Custom profile extension

**Decision:** TBD - may require SysML profile definition

---

## 10. Next Steps

### 10.1 For Canonical Naming Phase

1. **Review Entity Type Stereotypes**
   - Define mapping from PROVES entity types to SysML stereotypes
   - Establish when to use `<<Software>>`, `<<Hardware>>`, `<<External>>`

2. **Parameter/Command/Telemetry Boundaries**
   - Decide: AttributeUsage vs ItemDefinition vs PortUsage
   - Document decision rules for extraction agents

3. **Package Naming Convention**
   - Establish canonical package hierarchy from ecosystem + namespace
   - Example: `fprime::CommunicationsSubsystem::RadioDriver`

4. **ERV Mapping Strategy**
   - Define how ERV attributes (strength, mechanism, knownness) map to SysML
   - Consider custom profile or stereotype approach

### 10.2 For Mapping Strategy Documentation

- Consolidate XTCE + PyG + SysML v2 alignment tables
- Identify multi-standard mappings
- Document export priority (which standard for which use case)

### 10.3 For Future Export Phase (Later)

- Implement SysML v2 textual notation generator
- Build PartDefinition/PartUsage exporter
- Create package hierarchy from PROVES namespace

---

## 11. References

**Official Specifications:**
- [OMG SysML v2 Specification](https://www.omg.org/sysml/sysmlv2/)
- [SysML v2 Textual Notation (DeepWiki)](https://deepwiki.com/Systems-Modeling/SysML-v2-Release/2.2-sysml-v2-textual-notation)
- [OSLC SysML v2 Vocabulary](https://docs.oasis-open-projects.org/oslc-op/sysml/v2.0/sysml-vocab.pdf)
- [SysML v2 Release (GitHub)](https://github.com/Systems-Modeling/SysML-v2-Release)

**Tutorials and Guides:**
- [SysML v2 Basics (Sanford Friedenthal, INCOSE)](https://www.omgwiki.org/MBSE/lib/exe/fetch.php?media=mbse:sysml_v2_transition:sysml_v2_basics-incose_iw-sfriedenthal-2024-01-28.pdf)
- [SysML v2 Definition vs. Usage (Stephan Roth)](https://roth-soft.de/blog/2025-08-23-sysml-2-definition-usage.html)
- [Which SysML v2 Element to Choose?](https://mbse4u.com/2024/12/02/which-sysml-v2-element-to-choose/)
- [SysML v2 Specialization Kinds](https://mbse4u.com/2022/11/29/the-sysml-v2-specialization-kinds/)

**Transition Guides:**
- [SysML v1 to SysML v2 Model Conversion](https://www.cto.mil/wp-content/uploads/2025/02/SysML-v2-TransitionApproach-1.3.pdf)
- [Key Differences Between SysML v1 and v2](https://dinesh-kumar-rajamani.medium.com/key-differences-between-sysml-v1-and-sysml-v2-b035d4e3faad)
- [SysML v2 Release: What's Inside?](https://mbse4u.com/2020/12/21/sysml-v2-release-whats-inside/)

**PROVES Documentation:**
- `.deepagents/IMPLEMENTATION_ROADMAP.md` - Current phase goals
- `docs/architecture/KNOWLEDGE_GRAPH_SCHEMA.md` - PROVES ERV
- `neon-database/migrations/015_add_standard_mapping_enrichment.sql` - Mapping infrastructure

---

**Status:** SysML v2 vocabulary study complete. Ready for PROVES canonical naming review.
