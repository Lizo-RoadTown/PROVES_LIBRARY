# PROVES Library Documentation Index

This document provides a standardized map of all documentation in the repository.

## 📋 Documentation Structure

### Getting Started (Start Here)

1. **[SETUP_GUIDE.md](../SETUP_GUIDE.md)** - Complete setup instructions
   - Prerequisites and installation
   - Environment configuration
   - First extraction walkthrough
   - Troubleshooting guide

2. **[README.md](../README.md)** - Project overview and quick links

### Core Concepts

3. **[FRAMES_METHODOLOGY.md](frames/FRAMES_METHODOLOGY.md)** - Understanding FRAMES
   - 7-question epistemic model
   - Socio-organizational provenance
   - Why FRAMES matters for CubeSat missions

4. **[ARCHITECTURE.md](architecture/SYSTEM_ARCHITECTURE.md)** - System design
   - 5-stage pipeline overview
   - Agent architecture
   - Database schema

### Implementation Documentation

#### Pipeline (`.deepagents/`)

- **[SESSION_SUMMARY_2026-01-15.md](../.deepagents/SESSION_SUMMARY_2026-01-15.md)** - Latest fixes and improvements
- **[CONNECTION_POOL_FIX.md](../.deepagents/CONNECTION_POOL_FIX.md)** - Database connection pooling
- **[IMPLEMENTATION_ROADMAP.md](../.deepagents/IMPLEMENTATION_ROADMAP.md)** - Development roadmap

#### Production (`production/docs/`)

- **[NOTION_INTEGRATION_GUIDE.md](../production/docs/NOTION_INTEGRATION_GUIDE.md)** - Human review workflow
- **[HUMAN_APPROVAL_WORKFLOW_GUIDE.md](../docs/HUMAN_APPROVAL_WORKFLOW_GUIDE.md)** - Approval process details

### API & Technical References

- **[production/Version 3/](../production/Version%203/)** - Current implementation
  - `agent_v3.py` - Agent orchestration
  - `extractor_v3.py` - Entity extraction
  - `validator_v3.py` - Validation logic
  - `storage_v3.py` - Database storage
  - `database.py` - Connection pooling

### Database

- **[neon-database/migrations/](../neon-database/migrations/)** - Schema migrations
  - `001_initial_schema.sql` - Core tables
  - `002_add_epistemic_fields.sql` - FRAMES metadata
  - `003_add_notion_integration.sql` - Bidirectional sync

---

## 🎯 Quick Navigation by Task

### "I want to set up PROVES Library"
→ Start with [SETUP_GUIDE.md](../SETUP_GUIDE.md)

### "I want to understand what this system does"
→ Read [README.md](../README.md) then [FRAMES_METHODOLOGY.md](frames/FRAMES_METHODOLOGY.md)

### "I want to know how the agents work"
→ Check [ARCHITECTURE.md](architecture/SYSTEM_ARCHITECTURE.md)

### "I'm getting errors during extraction"
→ See troubleshooting in [SETUP_GUIDE.md](../SETUP_GUIDE.md#troubleshooting)

### "I want to review extractions in Notion"
→ Read [NOTION_INTEGRATION_GUIDE.md](../production/docs/NOTION_INTEGRATION_GUIDE.md)

### "I want to understand recent changes"
→ Check [SESSION_SUMMARY_2026-01-15.md](../.deepagents/SESSION_SUMMARY_2026-01-15.md)

### "I want to contribute or extend the system"
→ Read [IMPLEMENTATION_ROADMAP.md](../.deepagents/IMPLEMENTATION_ROADMAP.md)

---

## 📝 Documentation Standards (For Contributors)

When adding new documentation:

### File Naming

- Use `SCREAMING_SNAKE_CASE.md` for guides: `SETUP_GUIDE.md`
- Use `Title_Case.md` for concepts: `FRAMES_Methodology.md`
- Use descriptive names: `connection_pool_fix.md` not `fix.md`

### File Location

```
PROVES_LIBRARY/
├── SETUP_GUIDE.md           # Main setup (root level)
├── README.md                 # Project overview (root level)
├── docs/
│   ├── README.md            # This index
│   ├── frames/              # Conceptual documentation
│   ├── architecture/        # System design docs
│   └── tutorials/           # How-to guides
├── .deepagents/             # Implementation notes
│   ├── SESSION_*.md         # Development sessions
│   └── *_FIX.md            # Specific fixes/improvements
└── production/docs/         # Production-specific docs
    └── NOTION_*.md          # Notion integration
```

### Document Structure

Every guide should have:

1. **Title and Purpose** - What is this document about?
2. **Prerequisites** - What do you need to know first?
3. **Step-by-Step Instructions** - Clear, numbered steps
4. **Examples** - Show don't tell
5. **Troubleshooting** - Common issues and fixes
6. **Next Steps** - Where to go from here

### Code Examples

Always include:
- **Language identifier**: \`\`\`python or \`\`\`bash
- **Comments**: Explain what code does
- **Full context**: Don't assume imports
- **Expected output**: What should happen

### Cross-References

Use relative links:
```markdown
See [SETUP_GUIDE.md](../SETUP_GUIDE.md) for installation.
```

Not:
```markdown
See the setup guide.  # ❌ No link
```

---

## 🔄 Documentation Maintenance

### When Code Changes

1. **Update related docs** - Don't let docs get stale
2. **Add to SESSION_SUMMARY** - Record what changed and why
3. **Update this index** - If adding new docs

### Review Checklist

Before committing documentation:

- [ ] Is the title clear and descriptive?
- [ ] Are prerequisites stated?
- [ ] Are instructions step-by-step?
- [ ] Are code examples tested?
- [ ] Are file paths correct?
- [ ] Are cross-references working?
- [ ] Is troubleshooting included?
- [ ] Is this doc added to the index?

---

## 📚 External Resources

- **Neon PostgreSQL**: https://neon.tech/docs
- **Notion API**: https://developers.notion.com/docs
- **LangChain**: https://python.langchain.com/docs
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **Anthropic Claude**: https://docs.anthropic.com/

---

## 🚀 Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Code style guidelines
- Testing requirements
- Pull request process
- Documentation standards

---

**Last Updated**: 2026-01-15
**Maintained By**: PROVES Library Team
**Questions?**: File an issue at https://github.com/Lizo-RoadTown/PROVES_LIBRARY/issues
