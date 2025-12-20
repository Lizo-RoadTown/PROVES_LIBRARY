# Documentation Synchronization Strategy

## Problem Statement

How to keep PROVES Library knowledge base fresh with F´ and PROVES Kit documentation that lives in GitHub repositories?

**Key Requirements:**
- Stay up-to-date with source documentation
- Avoid unnecessary reprocessing
- Detect and handle changes efficiently
- Maintain relationship integrity in knowledge graph
- Support versioning and history

---

## Recommended Strategy: Hybrid Incremental

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Repositories                      │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │   F´ (NASA)      │         │  PROVES Kit      │         │
│  │  nasa/fprime     │         │  (Cal Poly)      │         │
│  └──────────────────┘         └──────────────────┘         │
└────────────┬───────────────────────────┬────────────────────┘
             │                           │
             │ Git pull (daily)          │
             ↓                           ↓
┌─────────────────────────────────────────────────────────────┐
│            Local Cache (.cache/repos/)                       │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  fprime/         │         │  proves_kit/     │         │
│  │  (Git clone)     │         │  (Git clone)     │         │
│  └──────────────────┘         └──────────────────┘         │
└────────────┬───────────────────────────┬────────────────────┘
             │                           │
             │ Git diff detection        │
             ↓                           ↓
┌─────────────────────────────────────────────────────────────┐
│          Doc Sync Manager (doc_sync_manager.py)             │
│  • Detect changes (commit SHA comparison)                   │
│  • Process only modified files                              │
│  • Update knowledge graph incrementally                     │
│  • Track sync metadata                                      │
└────────────┬───────────────────────────┬────────────────────┘
             │                           │
             ↓                           ↓
┌─────────────────────────────────────────────────────────────┐
│             PROVES Library Knowledge Base                    │
│  ┌──────────────────────────────────────────────┐          │
│  │  Neon PostgreSQL                              │          │
│  │  • library_entries (processed docs)           │          │
│  │  • kg_nodes (extracted entities)              │          │
│  │  • kg_relationships (connections)             │          │
│  │  • sync_metadata (change tracking)            │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Initial Build (One-Time)

### What Happens
1. Clone F´ and PROVES Kit repos to `.cache/repos/`
2. Extract all markdown documentation
3. Process into library entries
4. Build knowledge graph (nodes + relationships)
5. Store commit SHA for change detection

### Commands
```bash
# Clone and index F´ docs
python scripts/doc_sync_manager.py init fprime

# Clone and index PROVES Kit docs (after adding URL)
python scripts/doc_sync_manager.py init proves_kit
```

### Expected Results
- ~50-100 library entries from F´ docs
- ~20-50 entries from PROVES Kit
- Knowledge graph with component relationships
- Baseline commit SHAs stored

---

## Phase 2: Daily Incremental Updates

### What Happens
1. **6:00 AM daily (scheduled):**
   - Git fetch from remotes
   - Compare HEAD SHA with stored SHA
   - If changed:
     - Git pull latest changes
     - Run `git diff --name-only <old> <new>`
     - Reprocess only changed `.md` files
     - Update affected graph nodes
     - Update commit SHA

2. **If no changes:**
   - Skip processing
   - Log "up-to-date"
   - Continue next day

### Commands
```bash
# Manual trigger
python scripts/doc_sync_manager.py daily

# Check for updates without processing
python scripts/doc_sync_manager.py check fprime
```

### Scheduling (Windows)
```powershell
# Task Scheduler - runs daily at 6 AM
schtasks /create /tn "PROVES_DocSync" /tr "C:\Users\LizO5\PROVES_LIBRARY\.venv\Scripts\python.exe C:\Users\LizO5\PROVES_LIBRARY\scripts\doc_sync_manager.py daily" /sc daily /st 06:00
```

### Scheduling (Linux/Mac)
```bash
# Crontab - runs daily at 6 AM
0 6 * * * cd /path/to/PROVES_LIBRARY && .venv/bin/python scripts/doc_sync_manager.py daily >> logs/sync.log 2>&1
```

---

## Change Detection Strategy

### Git Diff-Based
```bash
# Get changed files between commits
git diff --name-only <old_sha> <new_sha>

# Filter to markdown in docs/
grep -E '^docs/.*\.md$'
```

### Example Output
```
docs/UsersGuide/api/python/fprime-gds/html/sources/api/fprime_gds/common/models/serialize/bool_type.rst.txt
docs/Tutorials/GettingStarted.md
docs/Architecture/ComponentModel.md
```

### Processing
```python
changed_files = ['docs/Architecture/ComponentModel.md']

for file in changed_files:
    # 1. Re-extract metadata
    metadata = extract_metadata(file)

    # 2. Update library entry
    update_library_entry(metadata)

    # 3. Find affected graph nodes
    nodes = find_nodes_by_source(file)

    # 4. Update nodes
    for node in nodes:
        update_node(node, metadata)

    # 5. Rebuild relationships for this node
    rebuild_relationships(node)
```

---

## Refresh Frequency Decision Matrix

| Frequency | Pros | Cons | Recommendation |
|-----------|------|------|----------------|
| **Hourly** | Very fresh | Wastes resources, rate limits | ❌ Too aggressive |
| **Daily** | Fresh enough, efficient | Up to 24hr lag | ✅ **Recommended** |
| **Weekly** | Very efficient | Stale data | ⚠️ Too slow for active development |
| **On-Demand** | Full control | May miss updates | ⚠️ Useful as supplement |
| **Webhook (Event)** | Instant, efficient | Complex setup | ✅ **Future upgrade** |

### Recommended: Daily + On-Demand

**Daily (Scheduled):**
- Runs at 6 AM automatically
- Catches all changes from previous day
- Low overhead (usually no changes)

**On-Demand:**
- User/agent can trigger immediate refresh
- Useful before major operations
- Command: `python scripts/doc_sync_manager.py update fprime`

---

## Data Storage Strategy

### Metadata Tracking Table

```sql
CREATE TABLE sync_metadata (
    repo_key TEXT PRIMARY KEY,           -- 'fprime', 'proves_kit'
    last_commit_sha TEXT NOT NULL,       -- For change detection
    last_sync_at TIMESTAMP DEFAULT NOW(),
    files_indexed INTEGER DEFAULT 0,
    nodes_created INTEGER DEFAULT 0,
    sync_stats JSONB                     -- Detailed stats
);
```

### Library Entry Links

```sql
-- Add to library_entries table
ALTER TABLE library_entries
ADD COLUMN source_repo TEXT,          -- 'fprime', 'proves_kit'
ADD COLUMN source_file_path TEXT,     -- 'docs/Architecture/ComponentModel.md'
ADD COLUMN source_commit_sha TEXT;    -- Git commit when indexed
```

**Benefits:**
- Track which repo each entry came from
- Find all entries from a specific file
- Version control (know which commit was used)
- Orphan detection (file deleted in repo)

---

## Handling Edge Cases

### 1. File Deleted in Repo
```python
# Detect deletions
deleted_files = get_deleted_files(old_sha, new_sha)

for file in deleted_files:
    # Find library entries from this file
    entries = get_entries_by_source(file)

    # Option A: Soft delete (mark as archived)
    mark_as_archived(entries)

    # Option B: Hard delete (remove from graph)
    delete_entries_and_nodes(entries)
```

**Recommendation:** Soft delete (preserve history)

### 2. File Renamed/Moved
```python
# Git tracks renames
git diff --name-status <old> <new>
# Output: R docs/old.md -> docs/new.md

# Update source_file_path in library_entries
update_source_path(old_path, new_path)
```

### 3. Relationship Conflicts
```python
# Example: Doc says ComponentA depends on ComponentB
# But ComponentB is later removed

# Detection
orphaned = find_orphaned_relationships()

# Resolution
for rel in orphaned:
    if target_node_archived:
        archive_relationship(rel)
        log_warning(f"Orphaned: {rel}")
```

### 4. Duplicate Content
```python
# Two files describe same component
# Use deduplication logic in curator agent

if similar_entry_exists(new_entry):
    # Merge or flag for review
    flag_for_human_review(new_entry, similar_entry)
```

---

## Performance Optimization

### 1. Shallow Clone
```bash
# Only clone latest commit (faster)
git clone --depth 1 <url>

# Fetch updates (pulls minimal data)
git fetch origin --depth 1
```

### 2. Parallel Processing
```python
# Process multiple files concurrently
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    executor.map(process_file, changed_files)
```

### 3. Caching
```python
# Cache parsed markdown for 24 hours
@lru_cache(maxsize=1000)
def parse_markdown(file_path, commit_sha):
    # Only reparse if commit changed
    return extract_metadata(file_path)
```

---

## Monitoring and Logging

### Sync Log Format
```json
{
  "timestamp": "2025-12-20T06:00:00Z",
  "repo": "fprime",
  "old_sha": "abc123",
  "new_sha": "def456",
  "files_changed": 3,
  "files_processed": 3,
  "entries_updated": 3,
  "nodes_updated": 5,
  "relationships_updated": 2,
  "errors": 0,
  "duration_seconds": 12.5
}
```

### Metrics to Track
- Sync success rate
- Average processing time
- Files changed per day
- Error frequency
- Graph size growth

---

## Future Enhancements

### Phase 3: GitHub Webhooks (Production)
```python
# FastAPI endpoint receives webhook
@app.post("/webhook/github")
async def github_webhook(payload: dict):
    if payload['ref'] == 'refs/heads/main':
        # Trigger incremental sync immediately
        sync_manager.incremental_update('fprime')
```

### Phase 4: Semantic Versioning
```python
# Track documentation versions
# Enable "as of date" queries

def get_entry_at_date(slug, date):
    return db.fetch_one("""
        SELECT * FROM library_entries
        WHERE slug = %s
        AND indexed_at <= %s
        ORDER BY indexed_at DESC
        LIMIT 1
    """, (slug, date))
```

---

## Best Practices Summary

✅ **DO:**
- Use Git diff for incremental updates
- Track commit SHAs for change detection
- Soft delete archived entries
- Run daily scheduled syncs
- Log all sync operations
- Cache parsed content
- Handle renames/deletes gracefully

❌ **DON'T:**
- Full rebuild every time
- Poll GitHub hourly (rate limits!)
- Hard delete historical data
- Ignore orphaned relationships
- Skip error handling
- Process unchanged files

---

## Implementation Checklist

- [x] Create `DocSyncManager` class
- [x] Implement initial clone/index
- [x] Implement Git diff detection
- [x] Implement incremental update
- [ ] Add sync_metadata table
- [ ] Add source tracking to library_entries
- [ ] Implement orphan detection
- [ ] Add scheduling (cron/task scheduler)
- [ ] Add monitoring/logging
- [ ] Test with real F´ repo
- [ ] Add PROVES Kit repo URL
- [ ] Document troubleshooting

---

## Configuration

### Add PROVES Kit Repository
Edit `scripts/doc_sync_manager.py`:
```python
self.repos = {
    'fprime': {
        'url': 'https://github.com/nasa/fprime.git',
        # ...
    },
    'proves_kit': {
        'url': 'https://github.com/your-org/proves-kit.git',  # ← Add this
        'name': 'PROVES Kit',
        'doc_paths': ['docs/', 'README.md'],
        # ...
    }
}
```

---

## Questions for User

1. **PROVES Kit URL:** What's the GitHub URL for PROVES Kit documentation?
2. **Refresh frequency:** Daily at 6 AM okay? Or different time?
3. **Deletion strategy:** Soft delete (archive) or hard delete old docs?
4. **Notification:** Email/Slack when sync fails?
5. **Manual triggers:** Should agents be able to trigger on-demand refreshes?

---

## Next Steps

1. Provide PROVES Kit GitHub URL
2. Run initial sync: `python scripts/doc_sync_manager.py init fprime`
3. Set up daily scheduling
4. Monitor first few syncs
5. Refine based on actual update patterns
