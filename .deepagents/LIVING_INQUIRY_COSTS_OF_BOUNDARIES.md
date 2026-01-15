# Coupling, Modularity, and Cost — Open Inquiry
**Living Document | Started: 2026-01-15**

---

## Purpose

To explore the costs of loose vs tight boundaries in PROVES **without premature closure**.

This document:
- Accumulates insight over time
- Tracks disagreement and uncertainty
- Records revisions transparently
- Resists false closure

**This is not a specification.** It's a thinking surface.

---

## Known Context

### The Pipeline
PROVES operates as a 5-stage funnel:

```
Stage 1: Capture (Loose)     → Extract entities from docs, permissive
Stage 2: Review (Human Gate)  → Humans approve/reject
Stage 3: Promote (Tight)      → Move to verified knowledge base
Stage 4: Export (Standards)   → Serialize to MBSE tools
Stage 5: Round-trip (Future)  → Bidirectional sync
```

### Why This Question Arose

1. **Ontology collapse observed**: "dependency" became a catch-all for 15+ distinct relationship types
2. **FRAMES concerns**: Are we losing epistemic metadata (contact, formalizability, temporality) during capture or promotion?
3. **Integration pressure**: Stage 4 exporters need stable types, but Stage 1 needs flexibility
4. **Recent architecture review**: External agent warned against collapsing CoreEntity + CandidateExtraction semantics

### Current Design Decisions

- **Domain models implemented** (Week 1, 2026-01-15):
  - `CoreEntity` (verified) separate from `CandidateExtraction` (staging)
  - `KnowledgeNode` projection with explicit `VerificationLevel` enum
  - Exporters default to VERIFIED only

- **Semantic separation enforced**:
  - Prevents accidental export of unverified knowledge
  - Maintains clear boundary between "loose capture" and "tight export"

---

## Hypotheses in Play

### Hypothesis A: Two Kinds of Cost (Tentative)

There are at least two different costs, and they don't move together:

#### 1. System-Level Collapse Cost
**About structural survivability**

Symptoms:
- System stops differentiating (heterogeneity → homogeneity)
- Entity types collapse into generic catch-alls
- Pipeline "works" but loses expressive power
- Hard to reverse once propagated

Observable via:
- Type distribution (e.g., 80% "dependency", 5% each of 15 specific types)
- UI symptoms (users can't find specific relationship types)
- Query degradation (searches return too many false positives)

Tends to show: **Early, visible, irreversible**

#### 2. Knowledge-Loss / FRAMES Cost
**About epistemic integrity**

Symptoms:
- Meaning lost across capture → review → promotion
- Can't explain how we know something
- Knowledge not portable, auditable, upgradable
- FRAMES dimensions not captured or degraded

Observable via:
- Missing provenance links
- Low confidence in dimensional metadata
- Human reviewers confused by context
- Re-extraction rates (how often do we need to go back to source?)

Tends to show: **Late, silent, accumulates quietly**

#### Critical Tension
These can diverge:
- ✅ No system collapse + ❌ Massive epistemic degradation (system looks healthy, knowledge is garbage)
- ❌ System collapse + ✅ Epistemic richness (can't find anything, but when you do, it's trustworthy)

**Open question**: Do they interact? Does preventing one increase risk of the other?

---

### Hypothesis B: Cost Shows Up at Different Pipeline Stages (Tentative)

| Stage | System Collapse Risk | FRAMES Loss Risk | Reversibility |
|-------|---------------------|------------------|---------------|
| **Stage 1: Capture** | Medium (over-permissive types) | Low (just capturing) | High (can re-extract) |
| **Stage 2: Review** | Low (humans filter) | High (humans miss epistemic metadata) | Medium (can reject) |
| **Stage 3: Promote** | High (type coercion) | High (lossy mapping) | Low (hard to rollback) |
| **Stage 4: Export** | N/A (read-only) | Medium (format limitations) | N/A (external tool) |

**Status**: Speculative. Needs validation.

---

### Hypothesis C: Tightness-Looseness is Not a Spectrum (Tentative)

**Wrong framing**: "How tight should boundaries be?" (implies single dimension)

**Better framing**: "Which boundaries need tightness, which need looseness, and at what stages?"

Example tensions:
- **Capture needs looseness** (don't reject weird entity types)
- **Export needs tightness** (standards formats are rigid)
- **Human review is the gate** (where looseness → tightness transition happens)

**If we tighten too early**: Miss novel entity types, reduce learning
**If we tighten too late**: System collapse, can't find anything

**Open question**: What signals tell us when to tighten?

---

## Observed Failure Modes (So Far)

### System-Level / Structural

#### 1. Dependency Collapse (Confirmed)
**Symptom**: 80% of entities typed as "dependency", obscuring 15+ distinct relationship types

**When noticed**: During Stage 2 bulk data promotion (2025-12)

**Impact**:
- Users can't query for specific relationships ("show me power dependencies")
- Graph visualizations useless (everything is "dependency")
- Cross-tool integration confused (XTCE expects typed relationships)

**Root cause**: Stage 1 extractor defaulting to generic "dependency" when uncertain

**Reversibility**: Medium (can re-extract with better prompt, but expensive)

#### 2. Entity Type Drift (Suspected)
**Symptom**: Same real-world entity extracted with different types across multiple pages

**Example**: "MSP430 Microcontroller" as:
- `component` (from one doc)
- `hardware` (from another doc)
- `dependency` (when mentioned in relationship context)

**When noticed**: During deduplication (2026-01)

**Impact**:
- Duplicate entities in knowledge base
- Cross-references broken
- Affects entity count metrics

**Root cause**: No canonical type mapping, context-dependent extraction

**Reversibility**: Low (would need manual merging + type canonicalization)

---

### Epistemic / FRAMES-Level

#### 1. Provenance Loss During Promotion (Confirmed)
**Symptom**: Byte-level evidence pointers not preserved in core_entities

**When noticed**: Implementing KnowledgeNode projection (2026-01-15)

**Impact**:
- Can't re-verify specific evidence quote
- Re-extraction requires full page re-fetch
- Humans can't audit specific claims

**Schema difference**:
- `staging_extractions` has: `evidence_checksum`, `evidence_byte_offset`, `evidence_byte_length`
- `core_entities` has: `source_snapshot_id` only

**Reversibility**: Low (would need migration to add columns + backfill)

#### 2. FRAMES Dimensions Not Migrated (Confirmed)
**Symptom**: Migration 009 not run on production Neon database

**When noticed**: Querying core_entities during demo (2026-01-15)

**Impact**:
- No epistemic metadata in verified knowledge base
- Can't assess epistemic risk
- Can't filter by formalizability, contact level, etc.
- Domain models have FRAMES support, but database doesn't

**Root cause**: Migration management (human decision to not run yet?)

**Reversibility**: High (just run migration, but need to backfill existing entities)

#### 3. Human Review Blind Spots (Suspected)
**Symptom**: Humans approve/reject based on "does this entity exist?" not "is the epistemic context captured?"

**Evidence**:
- 96 entities in core_entities, all status="pending"
- No FRAMES dimensions captured
- Review workflow doesn't prompt for dimensional assessment

**Impact**:
- Approved knowledge may lack epistemic integrity
- High-risk knowledge (embodied+tacit) not flagged
- Can't prioritize capture of at-risk knowledge

**Reversibility**: Medium (can add to review UI, but past reviews already done)

---

### Near Misses

#### 1. Almost Collapsed CoreEntity + CandidateExtraction (Avoided)
**What almost happened**: Original roadmap suggested unified "Entity" domain model

**Why it would have been bad**:
- Would blur verified vs unverified semantics
- Could accidentally export staging candidates to MBSE tools
- No way to enforce "only verified for standards export"

**How we caught it**: External architecture review (2026-01-15)

**What we did instead**:
- Separate CoreEntity (verified) and CandidateExtraction (staging)
- KnowledgeNode projection with explicit VerificationLevel enum
- Exporters enforce `require_verified=True` by default

**Cost avoided**: Semantic blur (system-level collapse)

#### 2. Almost Used Haiku for Storage Agent (Fixed)
**What almost happened**: Keep Haiku model for storage agent to save cost

**Why it would have been bad**:
- Haiku stops early (stored 2-5 of 15 extractions)
- "Helpfully" summarizes instead of completing work
- Silent data loss (looked successful, but missed 70% of extractions)

**How we caught it**: LangSmith traces showing agent saying "I'll continue..." then stopping

**What we did instead**: Upgraded to Sonnet 4.5, increased recursion limit to 100

**Cost avoided**: Data loss (epistemic cost - missing 70% of knowledge)

---

## Tensions & Tradeoffs

### Tension 1: Early Type Enforcement vs Learning
**Tighten early** (Stage 1 extraction):
- ✅ Prevents type drift
- ✅ Easier to query/export
- ❌ Rejects novel entity types
- ❌ Reduces system's ability to learn

**Stay loose** (Stage 1 extraction):
- ✅ Captures unexpected entities
- ✅ Allows ontology evolution
- ❌ Type collapse risk
- ❌ Harder to query/export

**Current approach**: Loose at Stage 1, tight at Stage 4
**Open question**: Is Stage 2 (human review) the right tightening gate?

---

### Tension 2: Provenance Completeness vs Schema Complexity
**Full provenance** (byte-level evidence):
- ✅ Can re-verify specific claims
- ✅ Supports lineage checking
- ✅ Audit trail for epistemic integrity
- ❌ Database schema complexity
- ❌ Storage cost
- ❌ Migration burden

**Minimal provenance** (snapshot ID only):
- ✅ Simpler schema
- ✅ Less storage
- ❌ Can't re-verify without re-fetching entire page
- ❌ Re-extraction expensive

**Current state**: Minimal (snapshot ID only in core_entities)
**Cost paid**: Epistemic (can't audit specific claims)

---

### Tension 3: FRAMES Capture Timing
**Capture at extraction** (Stage 1):
- ✅ Agent has full document context
- ✅ Can assess contact, directionality, temporality
- ❌ Machine assessment may be wrong
- ❌ Increases extraction complexity/cost

**Capture at review** (Stage 2):
- ✅ Human judgment more reliable
- ✅ Can add context agent missed
- ❌ Humans lack document context (page already fetched)
- ❌ Review takes longer
- ❌ Reviewer fatigue

**Capture at promotion** (Stage 3):
- ✅ Only for approved entities
- ✅ Reduces wasted work
- ❌ Very late (can't filter staging by epistemic risk)
- ❌ Hard to backfill

**Current state**: Mixed (agent extracts some, humans adjust, not all migrated)

---

## Signals We're Watching (Non-binding)

These feel informative, not enforceable. Things to pay attention to:

### System-Level Collapse Signals
- **Type distribution skew**: One type >60% of total entities
- **Query failure rate**: Users can't find what they're looking for
- **Deduplication collision rate**: Same entity extracted with different types
- **Entity count growth rate**: Plateauing (stopped capturing new types?)

### Epistemic / FRAMES Loss Signals
- **Re-extraction rate**: How often do we need to go back to source?
- **Reviewer confusion rate**: "I don't understand this extraction"
- **Confidence distribution**: All extractions high confidence (overconfident?)
- **Dimensional completeness**: % of entities with full FRAMES assessment
- **Epistemic risk concentration**: All knowledge in high-risk categories?

### Integration / Export Signals
- **Export rejection rate**: Entities can't serialize to target format
- **External tool complaints**: "Your data doesn't make sense"
- **Round-trip failure rate**: Can't re-import exported knowledge
- **Format conversion loss**: Semantic information lost in translation

### Human Workflow Signals
- **Review velocity**: Time per entity increasing?
- **Approval rate changes**: Suddenly approving/rejecting more?
- **Reviewer notes frequency**: More clarification needed?
- **Re-review requests**: "I need to look at this again"

**Note**: None of these are thresholds yet. Just things to watch.

---

## Counterexamples & Skepticism

### Where Our Intuitions Might Be Wrong

#### 1. "Loose capture is always safer"
**Intuition**: Better to capture too much, filter later

**Counterexample**: Dependency collapse
- Captured everything as "dependency"
- Now can't differentiate power vs data vs control dependencies
- Filtering later requires expensive re-extraction

**Lesson**: Looseness without structure leads to semantic collapse

---

#### 2. "Humans are the reliability layer"
**Intuition**: Human review catches all errors

**Counterexample**: FRAMES dimensions not assessed
- Humans approve "does this entity exist?"
- Don't assess "is this knowledge portable? Direct contact? Temporal?"
- Epistemic metadata never captured

**Lesson**: Humans only catch what they're prompted to look for

---

#### 3. "Tightness = rigidity = bad"
**Intuition**: Tight boundaries prevent learning

**Counterexample**: VerificationLevel enum
- Very tight: VERIFIED vs CANDIDATE, no middle ground
- Prevents accidental export of unverified knowledge
- Actually enables learning (safe to experiment in staging)

**Lesson**: Strategic tightness can enable flexibility elsewhere

---

#### 4. "Cost is monotonic" (more permissive = more cost)
**Intuition**: Looser boundaries = higher cost

**Counterexample**: Stage 1 extraction with strict types
- Tried to enforce entity_type enum early
- Rejected novel entities (e.g., "procurement constraint")
- Reduced system's ability to capture rare but important knowledge

**Lesson**: Sometimes tightness costs more (missed knowledge)

---

#### 5. "We can always fix it later"
**Intuition**: Reversibility is high, optimize for learning

**Counterexample**: Provenance loss during promotion
- staging_extractions → core_entities loses byte offsets
- Can't re-verify specific claims without full page re-fetch
- Would need migration + expensive backfill

**Lesson**: Some decisions have irreversible consequences

---

## Open Questions

### On System Collapse
1. **What distribution of entity types is "healthy"?**
   - Is 80% "dependency" always bad?
   - What if there really are that many dependencies?
   - How do we distinguish "true distribution" from "lazy extraction"?

2. **How do we know when heterogeneity is signal vs noise?**
   - 50 entity types: rich ontology or fragmented mess?
   - When should we consolidate types?
   - Who decides: humans, agents, or emergent usage patterns?

3. **Can we detect type collapse before it's irreversible?**
   - Early warning signals?
   - Automated checks?
   - How sensitive (false positives vs false negatives)?

---

### On FRAMES / Epistemic Cost
1. **When should FRAMES dimensions be assessed?**
   - At extraction (agent context)?
   - At review (human judgment)?
   - At promotion (only for approved)?
   - Can we do multiple passes (agent + human)?

2. **What's the minimum viable FRAMES capture?**
   - All 7 dimensions every time?
   - Just contact + formalizability?
   - Depends on entity type?

3. **How do we know if epistemic metadata is accurate?**
   - Can we validate FRAMES assessments?
   - What if agent and human disagree?
   - Confidence calibration?

4. **What's the cost of missing epistemic metadata?**
   - Can we quantify "knowledge you can't verify"?
   - How does it affect mission outcomes?
   - Is there a "minimum epistemic threshold" for safety?

---

### On Interaction Between Costs
1. **Does preventing system collapse increase epistemic loss?**
   - Tight types → easier to query
   - But tight types → miss epistemic nuance?

2. **Does preserving FRAMES richness cause system collapse?**
   - 7 dimensions per entity → complex schema
   - But complexity → harder to maintain → drift?

3. **Are there cascading failures?**
   - Type collapse → can't query → humans give up → more collapse?
   - Missing provenance → can't re-verify → trust degrades → knowledge loss?

---

### On Tightening Signals
1. **What would make us confident enough to tighten a boundary?**
   - Type distribution stable for N extractions?
   - Human reviewers consistently agree?
   - Export success rate above threshold?

2. **How do we know we're not tightening too early?**
   - Still discovering new entity types?
   - Novel use cases emerging?
   - External tools adding new requirements?

3. **Can tightening be gradual?**
   - Soft constraints (warnings, not errors)?
   - Opt-in tightness (per-ecosystem, per-team)?
   - Tighten for Stage 4 but not Stage 1?

---

## Case Studies

### Case Study 1: Dependency Collapse (System-Level)

**Timeline**:
- 2025-11: Started extraction, entity_type loosely inferred
- 2025-12: Noticed 80% "dependency", 15+ relationship types lost
- 2026-01: Hard-match data promotion added missing types
- 2026-01-15: Domain models enforce typed relationships

**What Happened**:
- Extractor defaulted to "dependency" when uncertain
- Accumulated over time (thousands of entities)
- Graph visualizations became useless
- Had to re-process with hard-match rules

**Costs Paid**:
- System collapse: Can't differentiate relationship types
- Re-work cost: Manual hard-match rules + re-processing
- User trust: "Is this data reliable?"

**What Prevented Full Collapse**:
- Staging table preserved raw extraction
- Could re-extract with better rules
- Human review gate prevented promotion to core

**Lessons**:
- Silent accumulation: Looked fine per-entity, catastrophic at scale
- Late detection: Only noticed when trying to use the data
- Reversibility matters: Staging table saved us

**Open questions**:
- Could we have detected this earlier?
- What threshold would have triggered alarm?
- Was "dependency" the right default, just over-used?

---

### Case Study 2: Haiku Storage Failure (Epistemic Loss)

**Timeline**:
- 2026-01-10: Extractor found 15 entities per page
- 2026-01-10: Storage agent (Haiku) stored 2-5 entities
- 2026-01-15: LangSmith traces revealed early stopping
- 2026-01-15: Upgraded to Sonnet 4.5, 15/15 stored

**What Happened**:
- Haiku model "helpfully" summarized work
- Said "I'll continue storing..." then stopped
- Looked successful (no errors), but lost 70% of data
- Silent failure (no warnings, just missing entities)

**Costs Paid**:
- Epistemic loss: 70% of extracted knowledge never stored
- Detection cost: Required manual LangSmith trace inspection
- Upgrade cost: Sonnet 4.5 more expensive ($0.47/URL vs $0.15/URL)

**What Prevented Full Loss**:
- LangGraph persistence: Could replay extractions
- Testing mandate: Caught before production rollout
- Real extraction tests: Not just mocks

**Lessons**:
- Model behavior matters: Not all models complete work reliably
- Silent failure worst case: No error = no alarm
- Cost-reliability tradeoff: Cheaper model cost us data

**Open questions**:
- How do we detect "agent stopped early" automatically?
- Is there a reliability threshold per model?
- Can we test for "all work completed" without human review?

---

### Case Study 3: VerificationLevel Enum (Prevented Collapse)

**Timeline**:
- 2026-01-15: Initial roadmap suggested unified "Entity" model
- 2026-01-15: External review warned against semantic blur
- 2026-01-15: Implemented separate CoreEntity + KnowledgeNode with VerificationLevel enum

**What Almost Happened**:
- CoreEntity + CandidateExtraction collapsed into single model
- Export code wouldn't distinguish verified vs unverified
- Could accidentally export staging candidates to MBSE tools
- Standards formats would contain unverified knowledge

**What We Did Instead**:
- Separate domain models
- Explicit `VerificationLevel.VERIFIED` vs `VERIFIED.CANDIDATE`
- Exporters default to `require_verified=True`
- Type system enforces semantic distinction

**Costs Avoided**:
- Semantic blur: "What does it mean to export this entity?"
- Integration failure: External tools consuming bad data
- Trust collapse: "How do I know this is verified?"

**Costs Paid**:
- Code duplication: Two models instead of one
- Mapping complexity: CoreEntity ← → KnowledgeNode
- Documentation burden: Must explain the distinction

**Lessons**:
- Strategic tightness: Enum prevents entire class of errors
- Type system as documentation: VerificationLevel makes intent explicit
- Early investment pays off: Easier to maintain separation than merge later

**Open questions**:
- Is two-level distinction enough? (verified vs candidate)
- Should there be intermediate states? (partially_verified, under_review?)
- How do we handle "auto-approved" entities? (trusted extractor)

---

## Revision Log

### 2026-01-15: Initial version (Claude Sonnet 4.5)
- Created living inquiry document
- Added two-cost hypothesis (system collapse vs epistemic loss)
- Documented observed failures: dependency collapse, Haiku storage, provenance loss
- Added counterexamples to common intuitions
- Listed open questions across all areas
- Added 3 case studies: dependency collapse, Haiku failure, VerificationLevel
- Established revision log for transparency

---

## How to Use This Document

### For Future Agents
1. **Read hypotheses first** - Understand current thinking
2. **Check observed failures** - Learn from past mistakes
3. **Add counterexamples** - Challenge assumptions
4. **Update revision log** - Make changes transparent

### For Collaborators
1. **This is not a spec** - Don't treat hypotheses as decisions
2. **Add your skepticism** - "I think this is wrong because..."
3. **Surface new failure modes** - Real examples > theory
4. **Flag hidden costs** - What are we missing?

### For Decision-Making
1. **Don't rush to resolution** - Complexity earns reduction
2. **Look for interaction effects** - How do costs amplify/dampen?
3. **Test hypotheses empirically** - Run experiments
4. **Update when surprised** - Document what changed our mind

---

## What We Are NOT Doing Yet

- ❌ Defining acceptance criteria
- ❌ Setting thresholds
- ❌ Collapsing costs into single metric
- ❌ Deciding where to enforce constraints
- ❌ Finalizing type ontology
- ❌ Locking in FRAMES capture strategy

**These come after we're satisfied the landscape is understood.**

---

## Meta: Why This Document Exists

Building a system whose core value is **preserving meaning under uncertainty**.

It would be **incoherent** to force cost decisions into prematurely rigid form.

This living document:
- Accumulates insight without premature closure
- Tracks disagreement as legitimate
- Records revision transparently
- Resists false simplification

**This is not indecision.** This is **epistemic integrity**.

---

**Status**: Open inquiry, actively revising
**Next review**: After Week 2 implementation (repositories + exporters)
**Custodian**: PROVES architecture team
