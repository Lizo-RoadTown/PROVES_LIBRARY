# Neon & Notion Cleanup Roadmap

## Purpose
Systematically remove Neon and Notion references to prevent agent confusion after migrating to Supabase and the new Curation Dashboard.

## Current State
- **Database**: Migrated from Neon to Supabase (2026-01-15)
- **Review UI**: Moving from Notion to Curation Dashboard
- **Problem**: 44+ files still reference Neon/Notion, confusing agents

---

## Phase 1: Security - Remove Hardcoded Credentials (URGENT)

### 1.1 Delete files with embedded credentials
| File | Issue | Action |
|------|-------|--------|
| `scripts/migrate_data_neon_to_supabase.py` | Hardcoded Neon URL with password | DELETE |
| `scripts/migrate_neon_to_supabase.py` | May have credentials | REVIEW & DELETE |

### 1.2 Archive old Neon export scripts
Move to `.archive/neon-migration/`:
- `scripts/export_neon_schema.py`
- `scripts/export_neon_to_csv.js`
- `scripts/full_neon_to_supabase.js`
- `scripts/migrate_all_neon.js`
- `scripts/migrate_core_tables.js`
- `scripts/migrate_with_pgdump.ps1`
- `neon-database/` (entire folder)
- `neon_exports/` (entire folder - already gitignored)

---

## Phase 2: Standardize Database Connection

### 2.1 Rename environment variable
**Goal**: Replace `NEON_DATABASE_URL` with `DATABASE_URL` everywhere

**Already done in .env**:
```
# ALIAS: Many scripts still reference NEON_DATABASE_URL
NEON_DATABASE_URL=<points to Supabase>
```

**Files to update** (search: `NEON_DATABASE_URL`):

#### Core Database Layer
| File | Line | Change |
|------|------|--------|
| `production/core/db_connector.py` | 26-30 | Use `DATABASE_URL`, add comment about Supabase |

#### Version 3 (Production)
| File | Lines | Change |
|------|-------|--------|
| `production/Version 3/database.py` | - | Use `DATABASE_URL` |
| `production/Version 3/agent_v3.py` | 64 | Use `DATABASE_URL` |
| `production/Version 3/extractor_v3.py` | - | Use `DATABASE_URL` |
| `production/Version 3/process_extractions_v3.py` | - | Use `DATABASE_URL` |
| `production/Version 3/validator_v3.py` | - | Use `DATABASE_URL` |
| `production/Version 3/storage_v3.py` | - | Use `DATABASE_URL` |

#### Version 2 (Legacy - Mark for deprecation)
| File | Change |
|------|--------|
| `production/Version 2/agent_v2.py` | Use `DATABASE_URL` |
| `production/Version 2/extractor.py` | Use `DATABASE_URL` |
| `production/Version 2/storage.py` | Use `DATABASE_URL` |
| `production/Version 2/validator.py` | Use `DATABASE_URL` |
| `production/Version 2/process_extractions_v2.py` | Use `DATABASE_URL` |

#### Other Scripts
| File | Change |
|------|--------|
| `production/curator/error_logger.py` | Use `DATABASE_URL` |
| `production/scripts/check_pending_extractions.py` | Use `DATABASE_URL` |
| `production/scripts/find_good_urls.py` | Use `DATABASE_URL` |
| `production/scripts/improvement_analyzer.py` | Use `DATABASE_URL` |
| `mcp-server/examples/test_mcp_setup.py` | Use `DATABASE_URL` |
| `langchain/scripts/setup_checkpointer.py` | Use `DATABASE_URL` |

### 2.2 Update db_connector.py
```python
# Before
db_url = os.getenv('NEON_DATABASE_URL')

# After
db_url = os.getenv('DATABASE_URL') or os.getenv('PROVES_DATABASE_URL')
```

---

## Phase 3: Remove Notion Integration

### 3.1 Archive Notion sync code
Move to `.archive/notion-integration/`:

| Source | Destination |
|--------|-------------|
| `notion/` | `.archive/notion-integration/notion/` |
| `production/curator/notion_sync.py` | `.archive/notion-integration/` |
| `production/curator/suggestion_sync.py` | `.archive/notion-integration/` |

### 3.2 Remove Notion webhook server auto-start
**File**: `production/Version 2/process_extractions_v2.py`

Remove or comment out:
```python
# Lines 29-99: ensure_webhook_server_running() and related code
```

### 3.3 Remove Notion environment variables from .env.example
Remove:
```
NOTION_API_KEY=
NOTION_EXTRACTIONS_DB_ID=
NOTION_REPORTS_DB_ID=
NOTION_ERRORS_DB_ID=
NOTION_SUGGESTIONS_DB_ID=
NOTION_EXTRACTIONS_DATA_SOURCE_ID=
NOTION_SUGGESTIONS_DATA_SOURCE_ID=
NOTION_ERRORS_DATA_SOURCE_ID=
NOTION_WEBHOOK_SECRET=
```

### 3.4 Update requirements.txt
Remove:
```
notion-client
```

---

## Phase 4: Update setup.py

### 4.1 Remove Neon setup prompts
**File**: `setup.py` (lines 115-130)

Replace Neon setup with Supabase setup:
- Remove references to neon.tech
- Update example connection strings
- Point to Supabase setup docs

---

## Phase 5: Update Documentation

### 5.1 Archive outdated docs
Move to `.archive/docs/`:
| File | Reason |
|------|--------|
| `docs/architecture/AGENT_HANDOFF.md` | Heavy Neon references |
| `production/docs/NOTION_INTEGRATION_GUIDE.md` | Notion-specific |
| `notion/README.md` | Notion-specific |
| `notion/docs/ERROR_LOGGING_GUIDE.md` | Notion-specific |

### 5.2 Update remaining docs
| File | Change |
|------|--------|
| `README.md` | Replace Neon mentions with Supabase |
| `docs/DASHBOARD_PLATFORM_SETUP.md` | Update to reflect Supabase choice |
| `.deepagents/*.md` | Update Neon/Notion references |

---

## Phase 6: Test & Verify

### 6.1 Test database connections
```bash
# Run extraction pipeline
python production/Version 3/process_extractions_v3.py --test

# Verify database connection
python -c "from production.core.db_connector import get_db_connection; print(get_db_connection())"
```

### 6.2 Verify no Neon/Notion references remain
```bash
# Search for remaining references
grep -r "NEON" --include="*.py" production/ scripts/
grep -r "notion" --include="*.py" production/
grep -r "neon.tech" .
```

---

## Checklist

### Phase 1: Security
- [ ] Delete `scripts/migrate_data_neon_to_supabase.py`
- [ ] Review/delete other migration scripts with credentials
- [ ] Create `.archive/neon-migration/` folder
- [ ] Move old migration scripts to archive

### Phase 2: Database Connection
- [ ] Update `production/core/db_connector.py` to use `DATABASE_URL`
- [ ] Update all Version 3 files
- [ ] Update all Version 2 files (or mark deprecated)
- [ ] Update other scripts
- [ ] Test all database connections

### Phase 3: Notion Removal
- [ ] Create `.archive/notion-integration/` folder
- [ ] Archive `notion/` folder
- [ ] Archive `notion_sync.py` and `suggestion_sync.py`
- [ ] Remove webhook server auto-start from process_extractions_v2.py
- [ ] Update `.env.example` to remove Notion vars
- [ ] Remove `notion-client` from requirements.txt

### Phase 4: Setup Script
- [ ] Update `setup.py` to reference Supabase instead of Neon

### Phase 5: Documentation
- [ ] Archive outdated docs
- [ ] Update README.md
- [ ] Update remaining .deepagents docs

### Phase 6: Verification
- [ ] Run extraction pipeline test
- [ ] Grep for remaining references
- [ ] Commit all changes

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking database connections | Keep NEON_DATABASE_URL alias in .env during transition |
| Losing migration history | Archive to .archive/ instead of deleting |
| Breaking Version 2 code | Version 2 is legacy; prioritize Version 3 |
| Missing Notion functionality | Dashboard replaces Notion for review workflow |

---

## Timeline Estimate

| Phase | Effort |
|-------|--------|
| Phase 1 (Security) | 15 min |
| Phase 2 (DB Connection) | 30 min |
| Phase 3 (Notion Removal) | 20 min |
| Phase 4 (Setup Script) | 10 min |
| Phase 5 (Documentation) | 20 min |
| Phase 6 (Testing) | 15 min |
| **Total** | ~2 hours |

---

## Notes

- The `.env` file already aliases `NEON_DATABASE_URL` to Supabase, providing backward compatibility
- Version 2 code can be fully deprecated once Version 3 is stable
- Notion webhook server was for bidirectional sync with Notion databases - no longer needed with Dashboard
- Keep archive folders for reference in case rollback is needed
