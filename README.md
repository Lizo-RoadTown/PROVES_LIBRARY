# PROVES Library

Provably-correct knowledge graph pipeline for space systems and other complex, fragmented domains.

[![GitHub Pages](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://lizo-roadtown.github.io/PROVES_LIBRARY/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Why this exists

Space systems knowledge lives in scattered docs, tribal memory, and half-written notes.
PROVES turns those fragments into a verified dependency graph so teams can see hidden couplings before they break a mission.

---

## Who this is for

- CubeSat and LEO builders who live inside interfaces and failure modes.
- Astrophysics and systems folks who know the real story is in the details.
- Students in space labs who only ever see slices of the stack.
- AI/ML/CS students who want to apply models to real, messy data.
- NASA lovers who want to see how truth-checked data changes outcomes.

---

## What it does

- Extracts entities and relationships from messy technical documentation.
- Tracks cryptographic lineage back to original sources.
- Keeps humans in the loop before facts enter the truth graph.

---

## How it works

```
Sources -> Extract -> Validate -> Human Review -> Truth Graph
```

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
