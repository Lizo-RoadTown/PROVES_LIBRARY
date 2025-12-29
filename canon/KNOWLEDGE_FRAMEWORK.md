# Knowledge Canonicalization Theory
## The Methodological Foundation of the FRAMES Ontology

---

## Why this theory exists

Complex systems do not fail because information is missing.
They fail because knowledge cannot move.

In large sociotechnical systems—space missions, embedded platforms, software stacks, and the organizations that operate them—critical knowledge exists, but it is unevenly grounded, inconsistently transferred, and silently degraded as it moves between people, tools, and time.

Once knowledge enters a digital system, it is treated as if it has a uniform shape. A telemetry-derived inference, a specification written after years of hands-on failures, and a rule copied from documentation all appear equally valid to downstream systems. This flattening of epistemic origin produces false confidence and masks risk.

**The FRAMES ontology is designed to prevent this failure mode.**

It does so by introducing a knowledge canonicalization layer—a theory-backed structure that makes the form of knowledge explicit before it enters universal systems.

This document defines that theory.

---

## The core claim

**Knowledge is not transferable until it is canonicalized.**

Before canonicalization:
- knowledge is context-bound,
- person-bound,
- time-bound,
- and often only meaningful within the situation where it was learned.

After canonicalization:
- knowledge has a stable shape,
- can pass through software systems,
- can be reasoned over by AI,
- and can survive organizational turnover.

**Dimensions are the mechanism of canonicalization.**

They do not describe what knowledge says.
They describe how knowledge exists.

---

## The ontology we are building (made explicit)

The FRAMES ontology is not merely a knowledge graph of facts, components, or interfaces. It is an **ontology of knowledge form**.

Each knowledge unit entering the system is accompanied by a canonical description of:
- how it was obtained,
- how close it is to direct interaction with reality,
- whether time and history are intrinsic to its truth,
- and whether it can be formalized into symbolic representation.

This canonical description is what allows:
- human reasoning,
- automated reasoning,
- and organizational decision-making

to operate on the same knowledge without assuming it is equally grounded.

Without this theory, the ontology collapses into a flat graph of symbols.

---

## Knowledge Forms Under Canonicalization

### Why we distinguish two knowledge forms

The canonicalization framework operates across two fundamental knowledge forms that coexist in all real systems but behave very differently once digitized.

These forms are not domains. They are **epistemic positions**.

Failing to distinguish them guarantees loss.

The two forms are:
- **Embodied Knowledge**
- **Inferred Knowledge**

The dimensions defined in this theory exist specifically to make movement between these forms visible, bounded, and survivable.

---

### Embodied Knowledge

**Definition**

Embodied knowledge originates through direct interaction with reality over time. It is learned through action, perception, failure, repetition, and calibration. It exists before formal explanation and often before conscious articulation.

**Characteristics**
- Grounded in physical, temporal, or experiential contact
- Learned through doing, not reading
- Sensitive to sequence, context, and accumulation
- Commonly carried by people, practices, and communities

**Examples**
- Recognizing abnormal hardware behavior by sound or timing
- Knowing when a connector is properly seated
- Interpreting telemetry by pattern rather than threshold
- Musical timing and phrasing
- Organizational "how things actually work" knowledge

**Why it matters**

Embodied knowledge is where systems actually succeed or fail. It is also the most fragile.

When embodied knowledge is converted into inferred form without preserving its grounding, downstream systems treat the representation as fully authoritative. The original conditions under which the knowledge was valid disappear.

Canonicalization does not eliminate embodiment.
It marks its origin and constraints so that inference does not overreach.

---

### Inferred Knowledge

**Definition**

Inferred knowledge exists in symbolic form. It is produced through reasoning, abstraction, modeling, or interpretation of effects. It can be manipulated, transmitted, and automated without direct interaction with the underlying phenomenon.

**Characteristics**
- Expressible in language, mathematics, code, or artifacts
- Portable across systems and people
- Often atemporal unless explicitly modeled
- Fully operable by digital and AI systems

**Examples**
- Software specifications and interface contracts
- Mathematical models and simulations
- Scientific theories derived from indirect observation
- Telemetry-based diagnoses
- AI-learned representations

**Why it matters**

Inferred knowledge is indispensable. It is the only form digital systems can operate on.

But inferred knowledge varies widely in distance from reality. Some inferred knowledge is deeply grounded; some is several steps removed. Without canonicalization, these differences vanish.

Some knowledge may never become embodied:
- nanoscale phenomena,
- abstract mathematics,
- latent statistical structures.

This is not a weakness. It is an epistemic condition that must be preserved, not hidden.

---

### The critical transition: embodiment → inference → automation

Knowledge does not switch categories cleanly. It moves along a path:

1. **Embodied knowledge** becomes **inferred by humans**
2. **Human inference** becomes **instrument-mediated**
3. **Instrumented inference** becomes **machine-operable**
4. **Machine inference** becomes **organizational truth**

At each step, loss can occur:
- contact becomes proxy,
- time collapses into snapshot,
- causality is reconstructed backward,
- memory decays across turnover.

**The FRAMES ontology exists to prevent these losses from becoming invisible.**

---

## A Concrete Example: Reaction Wheel Bearing Degradation

To make these abstractions concrete, consider how knowledge degrades through a real satellite anomaly:

### Stage 1: Embodied Origin

During integration, a technician hears a slight irregularity in reaction wheel RW-3 spin-down. Not outside specification limits, but "sounds wrong" based on 15 years of hands-on experience with bearing behavior. The technician documents it as an anomaly, but the wheel passes acceptance testing.

**Knowledge form:** Embodied
**Contact:** Direct (physical hearing, tactile feedback)
**Directionality:** Backward inference (sound → suspected bearing condition)
**Temporality:** History-bound (pattern matching across accumulated cases)
**Formalizability:** Low (tacit pattern recognition)

### Stage 2: First Inference Transition

Six months on-orbit, telemetry shows nominal performance initially. Then momentum desaturation maneuvers begin requiring 3% more torque than predicted. Flight dynamics engineer infers bearing friction increase from the *effect* (torque demand) without direct access to the *cause* (bearing state).

**Knowledge form:** Inferred (human)
**Contact:** Mediated (telemetry sensors)
**Directionality:** Backward inference (torque increase → bearing friction hypothesis)
**Temporality:** Sequence-bound (trend over multiple maneuvers)
**Formalizability:** Conditional (can be documented if context preserved)

### Stage 3: Second Inference Transition

The anomaly gets encoded in the fault tree as "RW-3 bearing degradation (suspected)". Now it's a node in a graph. Contact with the original technician observation is severed. The inference direction (backward from torque) is not preserved. The temporal pattern (specific thermal cycling profile) is reduced to metadata.

**Knowledge form:** Inferred (symbolic)
**Contact:** Indirect (effect-only, no access to bearing state)
**Directionality:** Backward (but direction not preserved in representation)
**Temporality:** Snapshot (temporal context lost)
**Formalizability:** Portable (but with epistemic loss)

### Stage 4: Third Inference Transition

The GNN learns correlation between "torque increase + thermal cycling history + time-in-orbit" and labels it "bearing wear pattern." The model has no idea this started with embodied knowledge. It treats it as statistically inferred from telemetry alone.

**Knowledge form:** Inferred (machine)
**Contact:** Derived (pattern extracted from data)
**Directionality:** Forward (statistical prediction)
**Temporality:** History-bound (in aggregate statistics only)
**Formalizability:** Fully embedded (but dimensionally flattened)

### Stage 5: Failure Mode

New mission uses same reaction wheel model. GNN predicts nominal performance because:
- The **embodied origin** (technician's tacit pattern recognition) is not structurally visible
- The **temporal accumulation** (specific thermal cycling profile of original mission) is not represented as episodic entities
- The **contact basis** (direct interaction vs. mediated telemetry) is not dimensionalized
- The **formalizability limits** (loss of tacit knowledge) are not flagged

The wheel fails earlier than predicted.

**This is why dimensions matter operationally.**

Without dimensional canonicalization, the GNN treats all these knowledge transitions as equivalent. High-contact embodied knowledge and low-contact derived inference appear the same in the graph. The system cannot weight its confidence appropriately.

---

## Knowledge Canonicalization via Dimensions

### Why dimensions are required

Dimensions are the operation that transforms knowledge into a universal, pipe-compatible form.

**Before dimensions:**
- knowledge exists, but cannot move reliably
- systems substitute confidence for grounding
- organizations repeat failures they "already knew"

**After dimensions:**
- knowledge retains its epistemic constraints
- inference systems can reason with restraint
- risk becomes visible instead of implicit

This is not categorization.
**This is canonicalization.**

---

### Dimension Set Overview

Each knowledge unit is canonicalized along four orthogonal dimensions. Together, they define the minimum structure required for safe transfer and reasoning.

These dimensions apply uniformly across:
- hardware,
- embedded systems (e.g., F´),
- software,
- human organizations,
- and indirectly observable science.

**The four dimensions:**

1. **Contact** — epistemic anchoring (how knowledge touches reality)
2. **Directionality** — epistemic operation (prediction vs. assessment)
3. **Temporality** — epistemic dependence on history
4. **Formalizability** — capacity for symbolic transformation

---

### Dimension 1: Contact (Epistemic Anchoring)

**What it is:**

Contact describes where knowledge touched the phenomenon itself—how close the knower is to direct interaction with reality.

**Levels:**
- **Direct contact**: Physical/experiential interaction (technician feels, hears, observes directly)
- **Mediated contact**: Instrumented observation (sensors translate reality)
- **Indirect contact**: Effect-only observation (outcome visible, cause inferred)
- **Derived**: Model-only (symbolic manipulation, no physical observation)

**Why it matters:**

If the GNN treats "RW-3 bearing degradation (suspected)" as uniformly grounded regardless of whether it came from a technician's hands-on pattern recognition or a telemetry-derived inference, it cannot distinguish **direct evidence** from **backward reconstruction**.

**Failure mode:**
Overconfidence in model-derived claims when embodied knowledge contradicts them.

**Example from reaction wheel case:**

The technician's observation (direct contact: hearing + tactile feedback) carries different epistemic weight than the telemetry inference (mediated contact: torque sensor data) or the thermal model prediction (derived: no physical observation).

Without Contact as a dimensional attribute, these collapse into "bearing degradation" with no differentiation in reliability.

---

### Dimension 2: Directionality (Epistemic Operation)

**What it is:**

Directionality describes whether knowledge was formed through **forward inference (prediction)** or **backward inference (assessment)**.

- **Forward inference**: "If we command this maneuver, torque demand will increase by X"
- **Backward inference**: "Torque demand increased by X, therefore bearing friction likely increased"

**Why it matters:**

Forward and backward inference are **different epistemic operations**, not different quality levels.

**Humans can do both:**
- Predict based on embodied experience ("this bearing will fail soon based on how it sounds")
- Assess based on pattern matching ("this sound means bearing degradation")

**AI can only infer**, but excels at inference across high-dimensional spaces. This makes AI extremely valuable for **helping humans see forward into prediction** by identifying patterns humans would miss.

**The critical distinction:**

AI infers from inferred representations. It cannot know whether its input came from high-contact embodied knowledge or fully derived models.

If the GNN learns from a backward assessment ("bearing degradation suspected") without knowing the **dimensional grounding** of that assessment, its forward predictions inherit hidden uncertainty.

**Directionality must be preserved** so that:
- Humans know whether they're looking at prediction vs. assessment
- AI-generated forward inferences can be traced back to their assessment origins
- The system doesn't confuse "what we think caused this" with "what will happen next"

**Example from reaction wheel case:**

The technician's knowledge is backward-inferred (sound → bearing condition hypothesis) from high-contact observation.

The GNN's prediction is forward-inferred (bearing wear pattern → future torque demand) from statistically derived patterns.

Without directionality preserved, the system cannot trace the prediction back to an assessment that originated in embodied, tacit pattern recognition.

---

### Dimension 3: Temporality (Epistemic Dependence on History)

**What it is:**

Temporality describes whether the truth of knowledge depends on:
- **Snapshot** (instantaneous state)
- **Sequence** (ordering of events matters)
- **History** (accumulated past affects current behavior)
- **Lifecycle** (long-term degradation or evolution)

**Why it matters:**

Digital systems default to present-time reasoning. Physical systems do not.

Heat, wear, drift, saturation, and skill acquisition are all forms of **history embedded in the present**. If time is not made structurally real, these effects become conceptually invisible.

**The critical insight: Episodes as entities**

Bearing degradation isn't caused by *time in orbit*—it's caused by *thermal cycling episodes*. If "thermal cycling" is metadata on a timestamp rather than a **first-class entity with relationships to components and states**, the GNN cannot reason about:

- Whether two missions with same orbit duration but different thermal profiles have similar risk
- Whether rapid cycling early in life compounds later vulnerability
- Whether a desaturation maneuver during peak thermal stress accelerates damage

**Failure mode:**

Without episodes as entities, temporal causality disappears into timelines. History-dependent knowledge degrades into snapshot reasoning, and the GNN misses cumulative effects.

**Example from reaction wheel case:**

The bearing degradation depends on:
- **Sequence:** Eclipse transitions (heating/cooling cycles) in specific order
- **History:** Accumulated thermal stress over hundreds of cycles
- **Lifecycle:** Long-term material fatigue

If these are not represented as episodic entities (with relationships to the bearing component, thermal environment, and maneuver schedule), the knowledge becomes: "bearing failed after 6 months"—a snapshot with no causal structure.

---

### Dimension 4: Formalizability (Capacity for Symbolic Transformation)

**What it is:**

Formalizability describes the degree to which embodied or inferred knowledge can be transformed into explicit, portable symbolic form.

**Levels:**
- **Portable**: Moves intact into symbolic representation (interface specifications, mathematical models)
- **Conditional**: Can be formalized if context/conditions are preserved (calibration procedures requiring specific tooling)
- **Local**: Resists formalization outside specific settings (team-specific workflows)
- **Tacit**: Remains embodied, cannot be fully symbolized (pattern recognition built from decades of hands-on experience)

**Why it matters:**

Formalizability is the **prerequisite for embeddability**. You cannot embed what you cannot formalize.

But formalization alone doesn't determine embeddability—that requires meaning formation (human judgment about what the knowledge means and how it enters the graph).

**The organizational fragility problem:**

When the integration technician rotates off, their embodied pattern recognition ("hearing bearing irregularities") doesn't transfer *because the system has no structure to preserve the epistemic grounding*.

The observation ("anomalous sound during spin-down") makes it into documentation, but:
- The **contact basis** (years of hands-on experience) is lost
- The **directionality** (backward inference from accumulated pattern matching) is lost
- The **conditional formalizability** (requires similar experiential grounding to interpret) is not flagged

**Failure mode:**

Without formalizability metadata, the next engineer treats "anomalous sound" as a vague historical note rather than **high-contact, conditionally-formalizable knowledge** requiring heightened monitoring and conservative margins.

This is organizational fragility without individual blame. The failure is structural, not personal.

**Example from reaction wheel case:**

- Technician's tacit pattern recognition: **Low formalizability** (tacit, embodied)
- Flight dynamics torque analysis: **Conditional formalizability** (can be documented if thermal cycling context preserved)
- Fault tree entry: **High formalizability** (portable symbolic form, but with epistemic loss)
- GNN statistical pattern: **Fully formalized** (embedded, but dimensionally flattened)

Each formalization step loses information. Without tracking formalizability, the system cannot see where meaning degraded.

---

## Contact and Directionality Are Orthogonal

**Contact** describes *what carries the interaction with reality*.
**Directionality** describes *the reasoning process that produced the knowledge*.

These are independent dimensions. Knowledge can have:

### High Contact + Backward Inference
Integration technician hears irregularity during spin-down. Direct physical interaction (high contact), but the *cause* (bearing defect) is inferred backward from the *effect* (sound pattern). The technician cannot see inside the bearing—only interpret accumulated pattern-matching from 15 years of hands-on experience.

### Low Contact + Forward Inference
Thermal model predicts bearing temperature during eclipse transitions. No physical interaction (low contact—purely symbolic), but reasoning is forward: known inputs → predicted outputs via mathematical model.

### Mediated Contact + Bidirectional Inference
Six months on-orbit, telemetry shows 3% torque increase during desaturation. Contact is mediated by sensors. Directionality is bidirectional: flight dynamics engineer hypothesizes bearing friction increase, tests it against thermal cycling data, revises hypothesis based on mismatch.

**Why this matters for the ontology:**

These three knowledge units *look identical* once flattened into "RW-3 bearing degradation (suspected)" in a fault tree.

But their **reliability, recoverability, and failure modes** are completely different.

Without dimensional canonicalization, a GNN trained on this graph treats them as equivalent. The system has no way to weight confidence appropriately or trace predictions back to their epistemic origins.

---

## Closing: Why this theory makes the system work

The FRAMES ontology is viable because it does not assume that knowledge is uniform once digitized.

This theory ensures that:
- **Embodied origins are not erased**
- **Inferred abstractions do not masquerade as ground truth**
- **Automated reasoning remains bounded by epistemic reality**

**Dimensions turn experience into infrastructure.**
**Canonicalization makes knowledge move without lying.**

That is the theory that makes the system work.

When the reaction wheel bearing fails earlier than predicted, it is not because the GNN made a mathematical error. It is because the knowledge entering the graph had already lost its dimensional grounding—and no amount of sophisticated inference can recover what was never preserved.

The FRAMES ontology prevents this by making epistemic form a first-class structural concern from the moment knowledge is admitted into the system.
