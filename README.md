# PROVES Library

Agentic knowledge base for CubeSat mission safety. This repo preserves the
trial dependency mapping between F Prime and PROVES Kit documentation and
hosts the tooling to curate that knowledge into a structured graph.

[![GitHub Pages](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://lizo-roadtown.github.io/PROVES_LIBRARY/)

## Project snapshot

- Trial mapping complete: FA' I2C driver + PROVES Kit power management docs.
- 45+ dependencies with citations, 4 cross-system dependencies, 5 knowledge gaps.
- Documentation site with interactive Mermaid diagrams in `docs/`.
- Curator agent and graph utilities under active development.

## Current focus

- Automate extraction and validation of dependencies.
- Load curated entries into the knowledge graph.
- Improve monitoring and human review workflows.

## Docs site

- Live site: https://lizo-roadtown.github.io/PROVES_LIBRARY/
- Source: `docs/` (Jekyll, TeXt theme)
- Diagrams: `docs/diagrams/*.md`

## How to use

- Read the docs site or open `docs/index.md` locally.
- For the curator agent, see `curator-agent/README.md`.
- For database and graph utilities, see `scripts/`.

## Repository layout

```
PROVES_LIBRARY/
  curator-agent/           LangGraph-based curator agent
  docs/                    GitHub Pages site and diagrams
  library/                 Example knowledge entries
  scripts/                 Database and graph utilities
  trial_docs/              Manual trial analysis sources and results
  archive/                 Superseded code and docs
  requirements.txt         Python dependencies
  FOLDER_STRUCTURE.md      Repository organization
```

## Contributing

Open research project. Issues and improvements welcome. For agent-specific
changes, start with `curator-agent/README.md`.

## License

MIT License - see `LICENSE`.

## Contact

Elizabeth Osborn
Cal Poly Pomona
eosborn@cpp.edu

Portfolio site: https://lizo-roadtown.github.io/proveskit-agent/
