# FRAMES Ontology Canon

## Purpose
This canon captures **lessons learned** about how to shape ontology for future builds—specifically around the *logic of shaping data* so it remains useful for humans **and** trainable, interpretable, and evolvable for agents. This is not a fixed schema. It is a set of **constraints, principles, and warnings** meant to prevent category errors and brittle agent behavior.

This canon exists because we learned—repeatedly—that *what feels natural to collect is often wrong*, and *what feels wrong is often closer to truth*.

---

## Canonical Data-Shaping Logic (Integrated)

### Framing Before Extraction: Identifying Dimensions

Before any extraction occurs, we orient around **dimensions**, not entities.

**Core Insight**  
Failure is rarely the right unit of analysis.

In practice, it was not *mission failure* that mattered, but **knowledge loss**. Treating the mission as the outcome obscured what was actually fragile, missing, or decaying. Only by reframing the outcome did the real structure become visible.

**Canon Rule**  
> Always ask: *what is being lost when this fails?*

This reframing shifts focus from events to **capabilities, continuity, and absence**.

#### 1) Two Kinds of “Why” (Must Not Be Conflated)

When diagnosing loss, we separate:

- **Epistemic why** — *Why did we fail to know?* (missing observation, missing measurement, missing access, missing interpretation)
- **Structural why** — *Why could the system not retain, transfer, or regenerate knowledge?* (brittle workflows, unmodeled handoffs, undocumented decisions, single points of expertise)

**Canon Rule**  
> If you treat a structural failure as an epistemic failure, you will ask for “more data” instead of protecting persistence.

Both can be true at once, but they demand different captures and different interventions.

#### 2) Two Kinds of Dimensions (Domain-Specific vs Universal)

Dimensions can be exposed within a specialty (domain-specific), but some dimensions are **universal** and must remain explicit across domains.

- **Domain-specific dimensions**: the local axes experts use (e.g., thermal, orbital, firmware, assay parameters)
- **Universal dimensions**: layers that shape *all* work and cannot be cleanly separated if they are touched

**Universal Layer Set (Default Explicit Layers)**
- **Socio-technical** (people ↔ tools ↔ practices)
- **Socio-organizational** (roles, incentives, authority, handoffs)
- **Physical** (materials, environment, constraints of reality)
- **Digital** (data structures, software systems, interfaces)

**Canon Rule**  
> If an item touches any universal layer, it must carry that layer attribution; do not force separation into a single-dimensional graph.

Reason: once work spans layers, dimensionality becomes coupled. A graph that pretends separability will hide the real mechanism of loss.

#### Anti-Pattern: The Single-Layer Graph

**What It Looks Like**  
Work is modeled as if it belongs to one layer (e.g., purely technical or purely organizational).

**Why It Fails**  
- Masks cross-layer handoffs where loss actually occurs
- Attributes failure to missing data instead of missing support
- Encourages "add more data" responses

**Typical Symptom**  
High confidence, low resilience. The system looks complete until pressure is applied.

#### Preferred Pattern: The Coupled-Layer Trace

**What It Is**  
A trace that explicitly follows an item as it crosses **socio-technical, socio-organizational, physical, and digital** layers.

**Why It Works**  
- Reveals where knowledge degrades, not just where it exists
- Preserves context through transitions and handoffs
- Makes structural fragility legible before failure

**Canon Rule**  
> Use coupled-layer traces when diagnosing loss, persistence, or regeneration. Graphs are views; traces show pressure paths.

---

#### Temporal Decay and Rediscovery (Non-Negotiable Reality)

**Core Claim**  
Knowledge decays with time—even when encoded digitally or embedded in physical systems.

Social systems are not neutral carriers of knowledge. Time, turnover, and shifting incentives introduce entropy. This is why well-known physical truths have been lost and rediscovered repeatedly throughout history.

**Common Misconception**  
Digital storage or physical embodiment guarantees persistence.

**Reality**  
- Knowledge exposed to time inside social networks is prone to decay
- Digital artifacts without living interpretive context become opaque
- Physical systems retain function while losing explainability

**Illustrative Failure Modes**  
- “Only Fred knew how to wire that part”
- “Only Dana understood how to read this test output”
- “The system works, but no one knows why”

These are not anecdotes—they are predictable outcomes of untracked socio-organizational dependence.

**Canon Rule**  
> Any knowledge that depends on specific people, roles, or tacit practice must be treated as *time-fragile*, regardless of whether it is stored digitally or physically.

**Implication for Modeling**  
- Track *who* can interpret, not just *what* is stored
- Treat expertise concentration as a decay accelerator
- Model rediscovery cost as a real future burden

Rediscovery is not proof of resilience. It is evidence of prior loss.

#### Primary Framing Dimensions
- **Domain** – where this knowledge is valid and where it is not
- **Outcome** – what must remain intact for success to be possible

**Why This Matters**  
Graphs do not show what is missing unless the surrounding shape is modeled. By identifying what is fragile—or could disappear—we can:
- Detect silent failure modes
- Identify dimensions that must be captured
- See which parts affect the absence, not just the presence, of information

Inference is created by forming a shape **around** what cannot be directly observed.

Only after these dimensions are named does extraction begin.

---

### A. Extraction as Observation (Pre-Ontological)

**Aligned Principles:** I, VII

We begin with extraction as *observation*, not data. No ontology, no classes, no edges.

- Signals are sensory input
- Ambiguity is preserved
- Structure is explicitly deferred

This protects against premature semantic collapse.

---

### B. Ontological Domain Filtering (Negative Selection)

**Aligned Principles:** II, III

Before meaning is assigned, we decide **where this observation is allowed to live**.

- Domains are exclusionary, not additive
- Cross-domain leakage is treated as an error condition

This enforces the distinction between components, relationships, constraints, and narratives.

---

### C. Human Truth-Grounding

**Aligned Principles:** VI, VII

Humans verify *what kind of truth* an observation represents.

- Observed
- Measured
- Inferred
- Reported
- Assumed

Correctness is secondary to epistemic type.

---

### D. Normalization Without Semantic Loss

**Aligned Principles:** V, VI

Normalization standardizes form, not meaning.

- Original representation is retained
- Units, scale, and context remain explicit

This prevents agents from mistaking consistency for certainty.

---

### E. Soft Matching to Ontology

**Aligned Principles:** I, III, IX

Alignment to existing ontology is probabilistic.

- Multiple candidate matches allowed
- Confidence is explicit
- Overwrites require human review

This keeps ontology refactorable.

---

### F. Chunking as Units of Reasoning

**Aligned Principles:** IV, VIII

Chunks are shaped by how agents reason.

- One claim per chunk
- Provenance contained
- Order-independent

Chunking defines thought boundaries.

---

### G. Delayed Ontological Commitment

**Aligned Principles:** I, IX, X

Only after uncertainty, provenance, domain limits, and decay are attached do we commit to ontology.

- Every commitment must be reversible
- Removal tests precede acceptance

Ontology remains a tool for sensemaking, not control.

---

## I. First Principle: Ontology Is a Commitment, Not a Description

**Observation**  
The moment you name something, agents treat it as real.

**Canon Rule**  
> Never add a node, field, or class unless you are willing to defend its long‑term semantic cost.

**Implication**  
Ontology is not a mirror of reality. It is a **contract about how reasoning will occur later**.

**Anti‑Pattern**  
- Adding categories because they are socially legible
- Adding fields because “we might need them”

**Practice**  
If a concept cannot survive *removal*, it is not ready to exist.

---

## II. Distinguish: Components, Relationships, Constraints, and Narratives

**Key Lesson**  
Not everything that connects things is an edge.

### 1. Components
- Things that persist
- Can exist independently
- Have internal state

Examples: Sensor, Person, Model, Dataset, Experiment

### 2. Relationships (Edges)
- Mechanisms of interaction
- Directional when possible
- Costly to over‑define

Examples: feeds_into, validates, depends_on

### 3. Constraints (Not Edges)
- Rules that govern behavior
- Often mistaken for dependencies
- Should *not* be traversable

Examples: regulatory limits, ethical bounds, physical laws

> **Canon Rule:** Constraints live outside the graph traversal logic.

### 4. Narratives (Never Nodes)
- Stories humans tell to explain coherence
- Useful for onboarding
- Toxic for agent reasoning if encoded structurally

Examples: “career path,” “success,” “intent,” “motivation”

---

## III. Dependencies Are Not Always Causal

**Hard‑Won Lesson**  
We over‑encoded causality where only correlation or sequencing existed.

**Canon Rule**  
> If removing A does not break B, A is not a dependency.

**Three Dependency Types (Must Be Explicitly Labeled)**
1. **Causal** – A produces B
2. **Enabling** – A allows B to occur but does not produce it
3. **Contextual** – A alters interpretation of B

Agents fail when these are collapsed.

---

## IV. Time Is a First‑Class Entity

**Observation**  
Static graphs hallucinate certainty.

**Canon Rule**  
> If something changes, time must be modeled explicitly.

**Practices**
- Prefer events over states
- Store decay functions separately from entities
- Allow truth to expire

**Agent Training Insight**  
Agents reason better with *process histories* than with snapshots.

---

## V. Data Should Be Shaped for Decay, Not Permanence

**Lesson Learned**  
Most data rots silently.

**Canon Rule**  
> Every datum must answer: *how does it become less true?*

**Decay Dimensions**
- Temporal relevance
- Context drift
- Observer bias
- Environmental change

**Anti‑Pattern**  
Immutable “facts” without provenance.

---

## VI. Provenance Is More Important Than Accuracy

**Counter‑Intuitive Finding**  
Agents recover from wrong data faster than from untraceable data.

**Canon Rule**  
> No datum without lineage.

**Minimum Provenance Fields**
- Source
- Method of acquisition
- Confidence or uncertainty
- Observer or instrument

---

## VII. Human Intuition ≠ Agent Intuition

**Repeated Failure Mode**  
Encoding what *makes sense to us*.

**Canon Rule**  
> If it relies on shared human context, it does not belong in ontology.

**Examples to Exclude**
- “Obvious” ordering
- Implied importance
- Cultural norms

Agents require **explicit scaffolding**, not implication.

---

## VIII. Agents Learn From Gaps, Not Just Signals

**Unexpected Insight**  
Empty space teaches.

**Canon Rule**  
> Absence must be distinguishable from zero.

**Practices**
- Use nulls intentionally
- Encode unknown vs unknowable
- Preserve missingness

---

## IX. Ontology Must Be Refactorable

**Lesson**  
Early certainty is the enemy.

**Canon Rule**  
> If you cannot version, fork, and deprecate ontology elements, stop building.

**Practices**
- Semantic versioning for schemas
- Soft deletion over hard deletion
- Migration paths as first‑class artifacts

---

## X. Final Canon: Ontology Serves Sensemaking, Not Control

**Foundational Belief**  
We are not encoding truth. We are encoding *room to reason*.

**Closing Rule**  
> A good ontology makes it easier to change your mind.

---



### Step 1: Extraction as Observation (Pre-Ontological)

**What We Do**  
We extract signals *without committing them to ontology yet*.

**Why**  
Premature structure creates false certainty. Early labeling collapses ambiguity that agents later need.

**Rules**  
- Treat extraction as *sensory input*, not facts
- Preserve raw phrasing, units, and context
- Do not assign classes or edges yet

**Failure Mode Prevented**  
Agents inheriting early misclassifications as ground truth.

---

### Step 2: Ontological Domain Filtering (Negative Selection)

**What We Do**  
We explicitly decide **which domains this observation is allowed to live in**.

**Why**  
Most data is valid only in *some* domains. Cross-domain leakage causes reasoning errors.

**Rules**  
- Filter *before* normalization
- Allow multiple domains only with justification
- Exclude domains rather than include by default

**Failure Mode Prevented**  
Agents over-generalizing domain-specific truths.

---

### Step 3: Human Verification for Truth Grounding

**What We Do**  
A human verifies *what kind of truth this is*.

**Why**  
Truth is not binary. Agents need to know what they are allowed to trust.

**Verification Types**  
- Observed
- Measured
- Inferred
- Reported
- Assumed

**Rules**  
- Humans classify truth type, not just correctness
- Unverified data is explicitly marked, not discarded

**Failure Mode Prevented**  
Agents treating inference as observation.

---

### Step 4: Normalization (Without Semantic Loss)

**What We Do**  
We normalize format *without collapsing meaning*.

**Why**  
Normalization is lossy by default. Loss must be intentional.

**Rules**  
- Preserve original representation alongside normalized form
- Normalize structure, not interpretation
- Units and scales remain explicit

**Failure Mode Prevented**  
Agents confusing representational consistency with factual certainty.

---

### Step 5: Soft Matching (Probabilistic Alignment)

**What We Do**  
We align data to existing ontology *probabilistically*, not deterministically.

**Why**  
Hard matching bakes errors into structure. Soft matching preserves uncertainty.

**Rules**  
- Multiple candidate matches allowed
- Confidence scores required
- No overwrite of existing nodes without human review

**Failure Mode Prevented**  
Ontology drift via silent overwrites.

---

### Step 6: Chunking for Reasoning, Not Storage

**What We Do**  
We chunk data based on **how agents reason**, not how humans read.

**Why**  
Chunking defines the unit of thought. Bad chunking creates hallucinations.

**Rules**  
- One claim per chunk
- Provenance must stay within chunk
- Chunks must survive reordering

**Failure Mode Prevented**  
Agents stitching unrelated facts into false narratives.

---

### Step 7: Ontological Commitment (Delayed)

**What We Do**  
Only now do we instantiate nodes, edges, and constraints.

**Why**  
By this point, uncertainty, provenance, and domain limits are already attached.

**Rules**  
- Commit only what survives refactoring tests
- Every commitment must be reversible

**Failure Mode Prevented**  
Rigid ontology that cannot evolve with evidence.

---

## Meta-Rule: Humans Decide Meaning, Agents Explore Consequences

Humans are responsible for *semantic intent*. Agents are responsible for *logical exploration*.

Crossing this boundary produces systems that feel confident and are wrong.

---

### Status
Living canon. Amend only with justification and concrete failure examples.

