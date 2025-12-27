# PROVES Library

Provably-correct knowledge graph pipeline for space systems and other complex, fragmented domains.

[![GitHub Pages](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://lizo-roadtown.github.io/PROVES_LIBRARY/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## What we are making

A truth-layer pipeline that turns scattered technical knowledge into a verified dependency graph.
That graph becomes high-quality training data for a Graph Neural Network (GNN) that can predict risk, impact, and hidden coupling before a mission breaks.

---

## Why a Graph Neural Network

Space systems are graphs already: components, interfaces, timing, power, teams. A GNN learns from both the structure and the features of each node and relationship, so it can:

- Predict cascade risk when a subsystem changes.
- Surface weak cross-team and cross-layer dependencies.
- Generalize patterns across different missions and hardware stacks.

---

## Why data quality matters

A GNN is only as good as the graph it learns from.

- Bad edges teach the model the wrong physics.
- Missing lineage makes results impossible to trust.
- Inconsistent labels destroy signal in training.
- Verified sources turn the graph into evidence, not guesses.

This repo is the data engine that makes the GNN possible.

---

## Who this is for

- CubeSat and LEO builders who live inside interfaces and failure modes.
- Astrophysics and systems folks who know the real story is in the details.
- Students in space labs who only ever see slices of the stack.
- AI/ML/CS students who want to apply models to real, messy data.
- NASA lovers who want to see how truth-checked data changes outcomes.

---

## How it works

```
Sources -> Extract -> Validate -> Human Review -> Truth Graph
```

---

## Cool diagrams

- `docs/diagrams/overview.md` - dependency overview
- `docs/diagrams/cross-system.md` - cross-system dependencies
- `docs/diagrams/knowledge-gaps.md` - hidden gaps
- `docs/diagrams/gnn-molecule.md` - GNN as molecular model
- `docs/diagrams/team-boundaries.md` - team boundary map
- `docs/diagrams/transitive-chains.md` - transitive chains

---

## Repository map

- `curator-agent/production/` - production pipeline and deployment notes
- `curator-agent/src/` - agent implementations and subagents
- `docs/` - architecture and guides
- `trial_docs/` - trial outputs and results

---

## Quickstart

```bash
pip install -r requirements.txt
```

See:
- `curator-agent/production/README.md`
- `docs/guides/MCP_SETUP_GUIDE.md`

---

## Status

- Active research.
- Initial CubeSat trial found 45+ dependencies and 4 critical cross-system gaps.
- Current focus: scale extraction across documentation sets.

---

## Links

- Docs: https://lizo-roadtown.github.io/PROVES_LIBRARY/
- GNN stack: https://github.com/Lizo-RoadTown/Proves_AI
- Architecture: `docs/architecture/AGENTIC_ARCHITECTURE.md`
- Trial results: `trial_docs/COMPREHENSIVE_DEPENDENCY_MAP.md`
- Issues: https://github.com/Lizo-RoadTown/PROVES_LIBRARY/issues

---

## License

MIT License - see `LICENSE`.

---

## Contact

Elizabeth Osborn - eosborn@cpp.edu
