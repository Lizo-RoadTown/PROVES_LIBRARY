# Knowledge Canonicalization Theory
## A Practical Framework for Preserving Knowledge in Technical Systems

---

## Dimensional metadata

Before knowledge enters a system where it will be stored, shared, or reasoned over, we capture four properties:

**1. Contact** — How close was the observer to direct interaction with the phenomenon?
**2. Directionality** — Was this an observation made in prediction (forward) or an assessment (backward) or present?
**3. Temporality** — Does this depend on history, sequence, or just a snapshot?
**4. Formalizability** — Can this be understood with abstraction such as a symbol?

These are structural properties that determine:
- If it is reliable
- What it depends on
- How it should be interpreted
- Whether it can transfer

---

## Two fundamental forms of knowledge

### Embodied knowledge
Learned through direct interaction with reality over time. Built from doing, failing, adjusting, repeating.

**Examples:**
- Recognizing abnormal hardware behavior by sound
- Knowing when a connector is properly seated
- Reading telemetry patterns that don't match any single threshold

**Characteristics:**
- Usually carried by people or practices
- Sensitive to context and history
- Often exists before it can be explained
- Fragile when people rotate out

### Inferred knowledge
Exists in symbolic form—language, math, code, specifications.

**Examples:**
- Software specifications
- Mathematical models
- Documented procedures
- Statistical patterns

**Characteristics:**
- Can be written down and transmitted
- Operable by machines and AI
- Varies widely in how grounded it is
- May be several steps removed from physical reality

**The key insight:** Both forms are essential. The problem is that once knowledge becomes symbolic (written down, entered into a database, used by software), these differences disappear. Everything looks equally valid.


---

## The four dimensions explained

### 1. Contact (How knowledge touches reality)

**Direct:** Physical or experiential interaction
*Technician feels, hears, observes the thing itself*

**Mediated:** Instrumented observation
*Sensors translate reality into data*

**Indirect:** Effect-only
*Outcome visible, cause inferred*

**Derived:** Model-only
*Pure symbolic manipulation, no physical observation*

**Why it matters:** A technician who hears a bearing irregularity has different epistemic grounding than telemetry showing torque increase, which has different grounding than a thermal model prediction. Without tracking this, all three collapse into "bearing degradation" with no reliability differentiation.

---

### 2. Directionality (Prediction vs. assessment)

**Forward:** Action → observed outcome
*"If we command this, torque will increase by X"*

**Backward:** Observed outcome → inferred cause
*"Torque increased, therefore friction likely increased"*

**Bidirectional:** Hypothesis → test → revision loop
*"We think it's friction, let's check thermal data, adjust hypothesis"*

**Why it matters:** Forward and backward are different operations. AI excels at inference and can help humans predict better by finding patterns humans miss. But if AI learns from a backward assessment without knowing the dimensional grounding, its forward predictions inherit hidden uncertainty.

**The distinction:** Humans can do both forward and backward inference. AI can only infer—but it's very good at it. The value is in helping humans see forward by leveraging AI's pattern recognition across high-dimensional data.

---

### 3. Temporality (Dependence on history)

**Snapshot:** Truth evaluable at a point in time
*"Current voltage: 28.5V"*

**Sequence:** Ordering matters
*"Event A must precede Event B"*

**History:** Accumulated past affects present
*"200 thermal cycles induced cumulative stress"*

**Lifecycle:** Long-term evolution
*"Material fatigue over 5 years"*

**Why episodes must be entities:**
Bearing degradation isn't caused by "time in orbit." It's caused by specific thermal cycling patterns. If "thermal cycling episode" is just metadata on a timestamp, your system can't reason about whether two missions with same duration but different thermal profiles have similar risk.

Episodes need to be first-class entities with relationships to components, states, and other episodes. Otherwise temporal causality collapses into timelines and history-dependent knowledge becomes snapshot reasoning.

---

### 4. Formalizability (Can it be symbolized?)

**Portable:** Moves intact into symbolic form
*Interface specifications, mathematical models*

**Conditional:** Can formalize if context preserved
*Calibration procedures requiring specific tooling*

**Local:** Resists formalization outside specific settings
*Team-specific workflows*

**Tacit:** Remains embodied, can't be fully symbolized
*Pattern recognition from decades of hands-on experience*

**Why it matters:** This is the prerequisite for putting knowledge into computational systems. You can't embed what you can't formalize.

But formalization isn't enough—you also need human judgment about what the knowledge means and how it should enter the system.

**Organizational fragility:** When a technician rotates off, their embodied pattern recognition doesn't transfer because there's no structure to preserve the grounding. The observation makes it into docs, but the contact basis, the inference structure, and the conditional transferability are all lost. The next engineer treats "anomalous sound" as a vague note instead of high-contact, conditionally-transferable knowledge requiring conservative margins.

This is structural failure, not personal failure.

---

## Contact and Directionality are independent

These are orthogonal dimensions. Knowledge can have any combination:

**High Contact + Backward Inference:**
Technician hears bearing irregularity (direct interaction), but infers cause from effect (sound → bearing condition).

**Low Contact + Forward Inference:**
Thermal model predicts bearing temperature (no physical interaction), reasoning forward from inputs to outputs.

**Mediated Contact + Bidirectional Inference:**
Telemetry shows torque increase (sensor-mediated), engineer hypothesizes cause, tests against thermal data, revises.

**Why this matters:** These three scenarios look identical once flattened into "RW-3 bearing degradation (suspected)" in documentation. But their reliability, recoverability, and failure modes are completely different. Without dimensional tracking, systems treat them as equivalent.

---

## What this enables

**Better predictions:** Systems can weight confidence based on epistemic grounding, not just statistical correlation.

**Resilient organizations:** Knowledge survives personnel turnover because the structure of how it was known is preserved, not just the content.

**Traceable reasoning:** When predictions fail, you can trace back to see where dimensional grounding was lost.

**Honest uncertainty:** Systems don't claim to know more than they do. If knowledge is backward-inferred from indirect contact with low formalizability, that's explicit.

**AI as amplifier, not replacement:** AI helps humans predict better by finding patterns in high-dimensional data, but dimensional tracking ensures AI-generated insights remain grounded in their epistemic origins.

---
