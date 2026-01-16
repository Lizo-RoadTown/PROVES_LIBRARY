# XTCE/YAMCS Vocabulary Study

**Purpose:** Understand XTCE naming conventions and category boundaries to ensure PROVES canonical naming aligns naturally.

**Standards Versions:**
- XTCE 1.2 (CCSDS Recommendation)
- XTCE 1.3 (OMG Specification)
- YAMCS (Mission Control System - XTCE implementation)

---

## 1. XTCE Core Concepts

### 1.1 SpaceSystem

**Definition:** The root organizational unit in XTCE, representing the complete metadata necessary to monitor and command a space device (spacecraft, payload, ground segment).

**Key Characteristics:**
- Defines a namespace
- Can contain nested sub-SpaceSystems (hierarchical organization)
- Analogous to a "system of systems" - reflects spacecraft design hierarchy
- Contains TelemetryMetaData and CommandMetaData

**Example Hierarchy:**
```
SpaceSystem: BogusSAT
  └─ SpaceSystem: PowerSubsystem (EPS)
  └─ SpaceSystem: CommunicationsSubsystem
  └─ SpaceSystem: AttitudeControlSubsystem
```

**Naming Convention:**
- Namespaces use paths: `/PROVES/EPS`, `/PROVES/COMMS`
- Sub-systems group related Parameters and Commands

---

### 1.2 TelemetryMetaData

**Definition:** Container for all telemetry-related definitions within a SpaceSystem.

**Contains:**
- `ParameterTypeSet` - Data type definitions
- `ParameterSet` - Individual Parameter definitions
- `ContainerSet` - Telemetry packaging/framing definitions
- `MessageSet` - Message format definitions
- `StreamSet` - Data stream definitions
- `AlgorithmSet` - Derived parameter calculations

**Purpose:** Groups all metadata about telemetry (downlink from spacecraft to ground).

---

### 1.3 CommandMetaData

**Definition:** Container for all command-related definitions within a SpaceSystem.

**Contains:**
- `ParameterTypeSet` - Data type definitions
- `ParameterSet` - Parameter definitions (shared with telemetry)
- `ArgumentTypeSet` - Command argument type definitions
- `MetaCommandSet` - Command definitions
- `CommandContainerSet` - Command packaging definitions
- `StreamSet` - Command stream definitions
- `AlgorithmSet` - Command verification algorithms

**Purpose:** Groups all metadata about commanding (uplink from ground to spacecraft).

---

### 1.4 Parameter

**XTCE Definition:** A data element representing a telemetry value extracted from a telemetry stream.

**Key Characteristics:**
- Has a `ParameterType` (data type: Integer, Float, String, Boolean, etc.)
- Extracted from `SequenceContainer` (telemetry packet)
- Can have alarm definitions (red/yellow limits)
- Can have calibrations (raw → engineering units)
- Can be referenced across SpaceSystems using qualified names

**Example:**
```xml
<Parameter name="EPS_BattV" parameterTypeRef="VoltageType">
  <ShortDescription>Battery Voltage</ShortDescription>
</Parameter>
```

**Typical Use Cases:**
- Sensor readings (voltage, temperature, current)
- Status flags (radio_enabled, payload_active)
- Counters (packet_count, error_count)

**XTCE Scope:** Telemetry only (downlink data)

---

### 1.5 MetaCommand

**XTCE Definition:** The base type for a telecommand sent from ground to spacecraft.

**Key Characteristics:**
- Supports inheritance (can extend `BaseMetaCommand`)
- Has `ArgumentList` (command parameters)
- Has `CommandContainer` (describes packaging/encoding)
- Can have `TransmissionConstraintList` (when command can be sent)
- Can have verifiers (check if command executed successfully)
- Arguments are local to the command but can reference Parameters

**Example:**
```xml
<MetaCommand name="SET_RADIO_POWER">
  <ArgumentList>
    <Argument name="power_level" argumentTypeRef="PowerLevelType"/>
  </ArgumentList>
  <CommandContainer>
    <!-- Encoding details -->
  </CommandContainer>
</MetaCommand>
```

**Typical Use Cases:**
- Configuration commands (SET_RADIO_FREQ, SET_PAYLOAD_MODE)
- Action commands (START_TELEMETRY, STOP_RECORDING)
- Calibration commands (CALIBRATE_SENSOR, RESET_COUNTER)

**XTCE Scope:** Commands only (uplink instructions)

---

### 1.6 Container (SequenceContainer)

**XTCE Definition:** A structured packaging format describing how Parameters are arranged in telemetry packets or how Arguments are arranged in commands.

**Key Characteristics:**
- Contains ordered list of `Entry` elements (Parameters or nested Containers)
- Can inherit from `BaseContainer` (supports packet versioning)
- Defines binary layout (byte order, bit positions)
- YAMCS uses Containers to determine archive partitions

**Example Use:**
```xml
<SequenceContainer name="EPSTelemetryContainer">
  <EntryList>
    <ParameterRefEntry parameterRef="EPS_BattV"/>
    <ParameterRefEntry parameterRef="EPS_Current"/>
    <ParameterRefEntry parameterRef="EPS_Temperature"/>
  </EntryList>
</SequenceContainer>
```

**Purpose:** Describes binary framing and packet structure for telemetry/commands.

---

### 1.7 Argument vs Parameter

**Distinction in XTCE:**

| Concept | Scope | Direction | Definition |
|---------|-------|-----------|------------|
| **Parameter** | Telemetry | Downlink | Data extracted FROM spacecraft |
| **Argument** | Command | Uplink | Data sent TO spacecraft |

**Key Difference:**
- `Parameter` = "What we measure/observe" (telemetry)
- `Argument` = "What we configure/control" (command input)

**ArgumentType:**
- Very similar to `ParameterType`
- Defines data type, valid range, units, calibrations
- Used exclusively in `MetaCommand` definitions

**Example:**
```
Parameter: EPS_BattV (telemetry value we READ)
Argument: power_level (command value we SEND in SET_RADIO_POWER)
```

---

## 2. XTCE Naming Patterns (from YAMCS examples)

### 2.1 Parameter Naming

**Observed Patterns:**
- Subsystem prefix + underscore + function: `EPS_BattV`, `RADIO_Status`, `ACS_RollAngle`
- CamelCase or UPPER_SNAKE_CASE
- Descriptive but concise
- Namespace scoping: `/PROVES/EPS/EPS_BattV`

### 2.2 MetaCommand Naming

**Observed Patterns:**
- Action verb + target: `SET_RADIO_POWER`, `START_TELEMETRY`, `RESET_COUNTER`
- UPPER_SNAKE_CASE common
- Clear indication of what the command does

### 2.3 Container Naming

**Observed Patterns:**
- Subsystem + purpose + "Container": `EPSTelemetryContainer`, `RadioCommandContainer`
- Describes packet type or message format

### 2.4 SpaceSystem Naming

**Observed Patterns:**
- Satellite name or subsystem name: `BogusSAT`, `PowerSubsystem`, `RadioDriver`
- PascalCase or descriptive names
- Hierarchical paths: `/BogusSAT/PowerSubsystem`

---

## 3. PROVES → XTCE Alignment Table

### 3.1 Entity Type Mappings

| PROVES `entity_type` | XTCE Equivalent | Alignment Status | Notes |
|----------------------|-----------------|------------------|-------|
| `component` | `SpaceSystem` (subsystem) | **Adjacent** | PROVES Component = XTCE SpaceSystem at subsystem level |
| `port` | `Parameter` or `Argument` | **Adjacent** | Context-dependent: input Port → Argument, output Port → Parameter |
| `dependency` | Not directly modeled | **Novel (PROVES)** | XTCE has relationships but no explicit "Dependency" type |
| `connection` | Not directly modeled | **Novel (PROVES)** | XTCE models data flow implicitly through Containers |
| `parameter` | `Parameter` | **Aligned** | Direct 1:1 mapping for telemetry data |
| `command` | `MetaCommand` | **Aligned** | Direct 1:1 mapping for telecommands |
| `telemetry` | `Parameter` | **Aligned** | PROVES Telemetry = XTCE Parameter (if downlink data) |
| `event` | `Parameter` (event channel) | **Adjacent** | XTCE models events as special Parameters with event severity |
| `data_type` | `ParameterType` or `ArgumentType` | **Aligned** | Direct mapping to XTCE type system |

---

### 3.2 Detailed Alignment Analysis

#### 3.2.1 Component → SpaceSystem

**Alignment:** Adjacent

**PROVES Concept:**
- Software or hardware module (e.g., `RadioDriver`, `TestComponent`)
- Can have ports, dependencies, attributes
- F' component = active or passive module

**XTCE Concept:**
- `SpaceSystem` = organizational namespace
- Contains Parameters (telemetry) and MetaCommands
- Represents subsystem or entire spacecraft

**Mapping Strategy:**
- PROVES `component` with `entity_type='component'` → XTCE SpaceSystem
- Use PROVES `namespace` field → XTCE SpaceSystem hierarchy
- PROVES Component name → XTCE SpaceSystem name

**Example:**
```
PROVES: Component "RadioDriver" (ecosystem=fprime)
XTCE:  <SpaceSystem name="RadioDriver">
         <TelemetryMetaData>...</TelemetryMetaData>
         <CommandMetaData>...</CommandMetaData>
       </SpaceSystem>
```

**Constraints:**
- PROVES Components that are purely software (no telemetry/commands) may not map cleanly
- XTCE SpaceSystem expects Parameters or Commands; passive components may need annotation

---

#### 3.2.2 Port → Parameter/Argument

**Alignment:** Adjacent (context-dependent)

**PROVES Concept:**
- Interface point on a component
- Can be input or output
- Types: command, telemetry, data, async

**XTCE Concept:**
- Input Port → `Argument` (data sent TO component via command)
- Output Port → `Parameter` (data read FROM component via telemetry)
- No explicit "Port" construct in XTCE

**Mapping Strategy:**
- PROVES Port (direction=output, type=telemetry) → XTCE Parameter
- PROVES Port (direction=input, type=command) → XTCE Argument in MetaCommand
- Use `standard_constraints` JSONB to record direction:
  ```json
  {
    "port_direction": "output",
    "port_type": "telemetry"
  }
  ```

**Example:**
```
PROVES: Port "RadioStatus" (direction=output, type=telemetry)
XTCE:  <Parameter name="RadioStatus" parameterTypeRef="BooleanType"/>

PROVES: Port "SetFrequency" (direction=input, type=command)
XTCE:  <MetaCommand name="SetFrequency">
         <ArgumentList>
           <Argument name="frequency" argumentTypeRef="FrequencyType"/>
         </ArgumentList>
       </MetaCommand>
```

**Constraints:**
- Bidirectional ports may need multiple XTCE representations
- Data ports (async) may not have direct XTCE equivalent

---

#### 3.2.3 Parameter → Parameter

**Alignment:** Aligned (1:1)

**PROVES Concept:**
- Telemetry value or configurable parameter
- Extracted from documentation

**XTCE Concept:**
- Parameter in TelemetryMetaData
- Represents downlink data

**Mapping Strategy:**
- Direct 1:1 mapping
- PROVES `canonical_key` → XTCE Parameter `name`
- PROVES `namespace` → XTCE SpaceSystem path
- PROVES `attributes` → XTCE ParameterType properties

**Example:**
```
PROVES: Parameter "BatteryVoltage" (ecosystem=cubesat)
XTCE:  <Parameter name="BatteryVoltage" parameterTypeRef="VoltageType"/>
```

**Constraints:**
- None - clean mapping

---

#### 3.2.4 Command → MetaCommand

**Alignment:** Aligned (1:1)

**PROVES Concept:**
- Telecommand or software command
- Can have arguments/parameters

**XTCE Concept:**
- MetaCommand in CommandMetaData
- Represents uplink command

**Mapping Strategy:**
- Direct 1:1 mapping
- PROVES `canonical_key` → XTCE MetaCommand `name`
- PROVES `attributes` (if contains arguments) → XTCE ArgumentList

**Example:**
```
PROVES: Command "SetRadioPower" (ecosystem=fprime)
XTCE:  <MetaCommand name="SetRadioPower">
         <ArgumentList>
           <Argument name="power_level" argumentTypeRef="PowerLevelType"/>
         </ArgumentList>
       </MetaCommand>
```

**Constraints:**
- None - clean mapping

---

#### 3.2.5 Dependency → (Novel)

**Alignment:** Novel (PROVES-specific)

**PROVES Concept:**
- Component A depends on Component B
- Software linkage or hardware requirement
- Recorded in Engineering Relationship Vocabulary (ERV)

**XTCE Concept:**
- No explicit Dependency construct
- Relationships implied through data flow (Parameters, Commands)

**Mapping Strategy:**
- **Do NOT map to XTCE**
- Dependency is a PROVES-native concept for engineering knowledge
- Future graph exports (PyTorch Geometric, GraphML) will use this

**Example:**
```
PROVES: Dependency "RadioDriver REQUIRES PowerDriver"
XTCE:  (Not represented - stays in PROVES knowledge graph)
```

**Constraints:**
- XTCE is data-centric, not dependency-centric
- Mark as explicitly **no mapping** in `standard_mapping` records

---

#### 3.2.6 Connection → (Novel)

**Alignment:** Novel (PROVES-specific)

**PROVES Concept:**
- Port-to-port connection between components
- Data flow path

**XTCE Concept:**
- Implicit in Container structure (data flows through packets)
- No explicit Connection type

**Mapping Strategy:**
- **Do NOT map to XTCE**
- Connection is PROVES-specific architectural knowledge

**Constraints:**
- XTCE Containers describe packet structure, not component wiring

---

#### 3.2.7 Event → Parameter (Event)

**Alignment:** Adjacent

**PROVES Concept:**
- Event log entry or notification
- Often severity-based (INFO, WARNING, ERROR)

**XTCE Concept:**
- Parameter with event severity attributes
- Often in dedicated event telemetry stream

**Mapping Strategy:**
- PROVES Event → XTCE Parameter with event metadata
- Use `standard_constraints` to record event severity:
  ```json
  {
    "xtce_type": "Parameter",
    "event_severity": "WARNING"
  }
  ```

**Example:**
```
PROVES: Event "RadioConnectionLost" (severity=ERROR)
XTCE:  <Parameter name="RadioConnectionLost" parameterTypeRef="EventType"/>
```

**Constraints:**
- Event severity mapping may require additional metadata

---

#### 3.2.8 Data Type → ParameterType/ArgumentType

**Alignment:** Aligned (1:1)

**PROVES Concept:**
- Type definition (int32, float64, enum, string)
- May include units, ranges, constraints

**XTCE Concept:**
- `ParameterType` (for telemetry)
- `ArgumentType` (for commands)

**Mapping Strategy:**
- PROVES `data_type` → XTCE ParameterType or ArgumentType (context-dependent)
- Record context in `standard_constraints`:
  ```json
  {
    "xtce_type": "ParameterType",
    "data_encoding": "IntegerDataEncoding"
  }
  ```

**Example:**
```
PROVES: DataType "VoltageType" (base_type=float, unit=volts, range=0-50)
XTCE:  <ParameterType name="VoltageType">
         <FloatParameterType>
           <UnitSet>
             <Unit>Volts</Unit>
           </UnitSet>
           <ValidRangeSet>
             <ValidRange minInclusive="0" maxInclusive="50"/>
           </ValidRangeSet>
         </FloatParameterType>
       </ParameterType>
```

**Constraints:**
- Must distinguish ParameterType vs ArgumentType based on usage context

---

## 4. Mapping Strategy Summary

### 4.1 Alignment Categories

**Aligned (1:1):**
- `parameter` → `Parameter`
- `command` → `MetaCommand`
- `data_type` → `ParameterType` / `ArgumentType`

**Adjacent (Similar but not exact):**
- `component` → `SpaceSystem` (subsystem level)
- `port` → `Parameter` or `Argument` (direction-dependent)
- `event` → `Parameter` (event channel)
- `telemetry` → `Parameter` (if downlink data)

**Novel (PROVES-specific, no XTCE equivalent):**
- `dependency` - No mapping
- `connection` - No mapping

### 4.2 Namespace Mapping

**PROVES:**
- `ecosystem`: 'fprime', 'ros2', 'cubesat'
- `namespace`: Optional hierarchical path
- `canonical_key`: Unique identifier within ecosystem

**XTCE:**
- SpaceSystem hierarchy defines namespaces
- Qualified names: `/PROVES/EPS/BatteryVoltage`

**Mapping Strategy:**
- PROVES `ecosystem` + `namespace` → XTCE SpaceSystem path
- PROVES `canonical_key` → XTCE Parameter/MetaCommand name

**Example:**
```
PROVES:
  ecosystem: 'fprime'
  namespace: 'RadioDriver'
  canonical_key: 'RadioStatus'
  entity_type: 'parameter'

XTCE:
  <SpaceSystem name="fprime">
    <SpaceSystem name="RadioDriver">
      <TelemetryMetaData>
        <ParameterSet>
          <Parameter name="RadioStatus" .../>
        </ParameterSet>
      </TelemetryMetaData>
    </SpaceSystem>
  </SpaceSystem>
```

---

## 5. Constraints on Future XTCE Exporters

### 5.1 Must-Follow Rules

1. **No Renaming**
   - Exporter MUST use `canonical_key` as-is for XTCE `name` attribute
   - Exporter MUST NOT invent new names or "clean up" naming

2. **Read from Mappings Table**
   - Exporter MUST query `knowledge_enrichment` table for `standard_mapping` records
   - If mapping missing for required entity, exporter MUST fail loudly (not guess)

3. **Respect Alignment Categories**
   - **Aligned** entities: Direct export
   - **Adjacent** entities: Use `standard_constraints` JSONB for context
   - **Novel** entities: Skip (do not export to XTCE)

4. **Namespace Preservation**
   - Use PROVES `namespace` → XTCE SpaceSystem hierarchy
   - Do not flatten or restructure

5. **Type Safety**
   - Only export entities with `standard_key` matching expected XTCE type
   - Verify `standard='xtce'` and `standard_version='1.2'` (or compatible)

### 5.2 Example Mapping Record

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
  'xtce',
  '1.2',
  'Parameter',
  'EPS_BattV',
  '{
    "namespace": "/PROVES/EPS",
    "container": "EPSTelemetryContainer",
    "subsystem": "PowerSubsystem"
  }'::jsonb
);
```

**Exporter Logic:**
```python
# Query for XTCE mappings
mappings = db.execute("""
  SELECT * FROM xtce_mappings
  WHERE entity_id = %s
""", [entity_id])

if not mappings:
    raise ValueError(f"No XTCE mapping for entity {entity_id}")

# Use mapping data (no renaming!)
xtce_name = mapping['standard_name']  # Use as-is
xtce_type = mapping['standard_key']    # 'Parameter', 'MetaCommand', etc.
namespace = mapping['standard_constraints']['namespace']
```

---

## 6. Open Questions for Canonical Naming Phase

### 6.1 Terminology Collisions

**Question:** Does PROVES use "Parameter" to mean something different than XTCE?

**Investigation Needed:**
- Review PROVES `entity_type='parameter'` usage in extractions
- Check if PROVES Parameter = telemetry value (matches XTCE) or something else
- If mismatch, consider renaming PROVES type to avoid confusion

### 6.2 Port Directionality

**Question:** How should bidirectional ports map to XTCE?

**Options:**
1. Create both Parameter (output) and Argument (input) for same port
2. Use JSONB constraints to record bidirectional nature
3. Define PROVES-specific rule: "Ports are always unidirectional for XTCE export"

**Decision:** TBD during canonical naming phase

### 6.3 Component Without Telemetry/Commands

**Question:** Can PROVES Component with no ports/parameters map to XTCE?

**Issue:** XTCE SpaceSystem expects TelemetryMetaData or CommandMetaData

**Options:**
1. Skip Components with no exportable Parameters/Commands
2. Create empty SpaceSystem (valid but not useful)
3. Mark as "not exportable to XTCE" in mapping constraints

**Decision:** TBD during canonical naming phase

### 6.4 Ecosystem → SpaceSystem Root

**Question:** Should PROVES `ecosystem` map to top-level SpaceSystem?

**Current Assumption:** Yes (`ecosystem='fprime'` → `<SpaceSystem name="fprime">`)

**Needs Confirmation:** Align with YAMCS namespace conventions

---

## 7. Next Steps

### 7.1 For Canonical Naming Phase

1. **Review PROVES `entity_type` enum values**
   - Confirm current values: `component`, `port`, `dependency`, `connection`, `parameter`, `command`, `telemetry`, `event`, `data_type`
   - Check for collisions with XTCE vocabulary
   - Identify any ambiguous or overlapping types

2. **Define Type Boundaries**
   - When is something a `parameter` vs `telemetry`?
   - When is a `port` represented as Parameter vs Argument?
   - Document decision rules for extraction agents

3. **Document `candidate_type` Discipline**
   - Ensure extraction agents use canonical type names
   - No ad-hoc or ambiguous types allowed

### 7.2 For PyTorch Geometric Study (Next)

- Similar vocabulary study for graph ML
- Alignment table: PROVES → PyG node/edge types

### 7.3 For Mapping Strategy Documentation

- Consolidate alignment tables from all standards
- Define constraints for multi-standard mappings
- Document when an entity maps to multiple standards

---

## 8. References

**Standards:**
- [XTCE 1.2 Specification (CCSDS)](https://ccsds.org/Pubs/660x0b2.pdf)
- [XTCE 1.3 Specification (OMG)](https://www.omg.org/spec/XTCE)
- [XTCE Tutorial (NASA)](https://ntrs.nasa.gov/api/citations/20090017706/downloads/20090017706.pdf)

**Implementation:**
- [YAMCS Documentation](https://docs.yamcs.org/yamcs-server-manual/mdb/loaders/xtce/)
- [YAMCS XTCE Loader](https://docs.yamcs.org/yamcs-server-manual/mdb/loaders/xtce/)
- [YAMCS GitHub - XTCE Examples](https://github.com/yamcs/yamcs/tree/master/yamcs-core/src/test/resources/xtce)

**PROVES Documentation:**
- `.deepagents/IMPLEMENTATION_ROADMAP.md` - Current phase goals
- `docs/architecture/KNOWLEDGE_GRAPH_SCHEMA.md` - PROVES entity types and relationships
- `neon-database/migrations/015_add_standard_mapping_enrichment.sql` - Mapping infrastructure

---

**Status:** XTCE vocabulary study complete. Ready for PROVES canonical naming review.
