# Archiving & Documentation Sweep Guidelines

**Purpose:** Ensure institutional knowledge is preserved when reorganizing, refactoring, or consolidating documentation.

---

## The Golden Rule

> **Before you delete, extract the canon.**

Every document contains lessons. Some are obvious (design decisions), some are subtle (why something was tried and rejected). Before archiving or deleting, ask: "What would a future developer need to know?"

---

## When to Archive vs Delete

| Situation | Action | Reason |
|-----------|--------|--------|
| Superseded by newer implementation | **Archive** | Historical context matters |
| Design doc never implemented | **Archive** | May revisit in future |
| Duplicate table/code | **Delete after extraction** | Keep one source of truth |
| Contains unique lessons | **Extract to CANON.md first** | Preserve knowledge |
| Typo fix / minor edit | **Just edit** | No historical value |
| Complete rewrite | **Archive old, create new** | Preserve context |

---

## The Sweep Process

### Step 1: Identify What's Changing

Before any major reorganization:

```markdown
## Changes Planned
- [ ] Consolidating X and Y into Z
- [ ] Rewriting agent spec from N agents to M agents
- [ ] Removing duplicate table definitions
```

### Step 2: Extract Canon from Each File

For each file being modified/deleted:

1. **Read the entire file** (don't skim)
2. **Ask:** What design decisions are documented here?
3. **Ask:** What was tried and rejected?
4. **Ask:** What would break if someone didn't know this?
5. **Extract** key lessons to CANON.md with section references

### Step 3: Update CANON.md

Add new sections or update existing ones:

```markdown
## N. [New Concept Name]

### N.1 [Specific Principle]

> "Quote the key insight."

**Why This Matters:**
- Reason 1
- Reason 2

**Example:**
```code or pseudocode```
```

### Step 4: Update Tracking Documents

1. **archive/README.md** - Add row to extraction table
2. **FOLDER_STRUCTURE.md** - Add entry to Decision Log
3. **ROADMAP.md** - Update status if architecture changed

### Step 5: Commit with Detailed Message

```bash
git commit -m "Consolidate X: [brief description]

SCHEMA CHANGES:
- What changed in database/schema

CANON EXTRACTIONS:
- What lessons were preserved

ARCHIVE UPDATES:
- What was archived
- Why it was superseded

BREAKING CHANGES:
- What developers need to update"
```

---

## Document Update Checklist

When doing a documentation sweep, update these files:

### Always Update

| File | What to Add |
|------|------------|
| `CANON.md` | New principles, lessons, patterns |
| `archive/README.md` | Extraction table, recent changes |
| `FOLDER_STRUCTURE.md` | Decision log entry |

### Update If Changed

| File | Condition |
|------|-----------|
| `README.md` | Architecture diagram changed |
| `ROADMAP.md` | Phase status changed |
| `GETTING_STARTED.md` | Setup steps changed |
| `docs/AGENT_BEHAVIOR_SPEC.md` | Agent architecture changed |
| `docs/ARCHITECTURE.md` | System architecture changed |

---

## Canon Extraction Template

When extracting lessons from a file, use this template:

```markdown
### Extracted from: [filename]
**Date:** [YYYY-MM-DD]
**Archived to:** [archive path]
**Replaced by:** [new file path]

**Key Lessons:**
1. [Lesson 1]
2. [Lesson 2]

**Design Decisions:**
- [Decision]: [Rationale]

**What NOT to do:**
- [Anti-pattern]: [Why it failed]
```

---

## Section Numbering in CANON.md

When adding new sections to CANON.md:

1. **Check existing sections** - Does this fit in an existing section?
2. **If new section needed:**
   - Add after the most related existing section
   - Renumber subsequent sections
   - Update all internal references (§N.M)
3. **Update archive/README.md** extraction table with new section numbers

### Current CANON.md Structure

```
§1. Core Design Principles
§2. Human-in-the-Loop (HITL) Patterns
§3. Transfer Learning Methodology
§4. Transparency Stack
§5. Three-Agent Architecture (v2)    ← NEW
§6. LangGraph Loop Control           ← NEW
§7. Sub-Agent Pattern (Historical)
§8. ERV Ontology
§9. Operational Patterns
§10. Key Takeaways
§11. Version History
§12. Related Documents
```

---

## What Makes Good Canon

### Do Extract

- **Design principles** ("We do X because Y")
- **Trade-offs** ("We chose X over Y because...")
- **Anti-patterns** ("Don't do X, it causes Y")
- **Vocabulary** (Domain-specific terms and meanings)
- **Workflow patterns** (How things connect)

### Don't Extract

- Implementation details (that's what code is for)
- Step-by-step tutorials (put in GETTING_STARTED.md)
- API documentation (put in docs/)
- Status updates (put in ROADMAP.md)

---

## Example: Today's Sweep

### What Changed
- Agent spec: 9 agents -> 3 agents
- Schema: Consolidated duplicate tables
- Loop control: Framework built-ins, not custom schema

### Canon Extracted

| From | Lesson | To |
|------|--------|-----|
| Agent spec v1 | "Only LLM reasoning steps are agents" | CANON §5.2 |
| LangChain docs | `recursion_limit`, `ToolCallLimitMiddleware` | CANON §6 |
| 12_extraction_confidence.sql | ENUMs for confidence/evidence types | Kept in 12_extraction_enums.sql |

### Files Updated
1. [YES] `CANON.md` - Added §5, §6, renumbered subsequent sections
2. [YES] `FOLDER_STRUCTURE.md` - Added decision log entry
3. [YES] `archive/README.md` - Added extraction table rows
4. [YES] `docs/AGENT_BEHAVIOR_SPEC.md` - Complete rewrite for v2
5. ⏳ `ROADMAP.md` - May need architecture update

---

## Automation Opportunities

Future improvements:
- [ ] Script to check CANON.md section references match archive/README.md
- [ ] Pre-commit hook to remind about doc updates
- [ ] Template for commit messages during sweeps

---

**Maintained by:** Claude Code + Human Oversight
**Created:** December 22, 2025
