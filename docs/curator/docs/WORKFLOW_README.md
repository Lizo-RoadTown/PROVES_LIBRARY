# Daily Extraction Workflow - User Guide

Complete infrastructure for managing incremental PROVES Kit documentation extraction.

---

## Quick Start

### Daily Routine

```bash
cd curator-agent
python daily_extraction.py
```

This will:
1. ✅ Check environment health
2. ✅ Load progress tracker
3. ✅ Determine next page
4. ✅ Launch extraction with human verification
5. ✅ Update progress after completion

---

## Available Scripts

### 1. `check_environment.py` - Health Check

Verifies all systems are ready for extraction.

```bash
python check_environment.py
```

**Checks:**
- Python version (3.9+)
- Environment file (.env)
- API keys (Anthropic, LangSmith)
- Database connectivity (Neon)
- Required packages (LangChain, LangGraph, psycopg)
- Disk space
- Required files (ONTOLOGY.md, PROVESKIT_DOCS_MAP.md)

**Output:**
```
✅ Python Version: Python 3.11.5
✅ Environment File: Found at /path/to/.env
✅ API Key (Anthropic): Set (sk-ant-a...)
✅ Database (Neon): Connected (staging_extractions: 15 rows)
...
✅ ALL CHECKS PASSED - Ready for extraction
```

---

### 2. `daily_extraction.py` - Main Workflow

Orchestrates the daily extraction process.

```bash
# Interactive mode (asks for confirmation)
python daily_extraction.py

# Auto mode (skips confirmation)
python daily_extraction.py --auto
```

**Workflow:**
1. Runs health check
2. Loads progress tracker
3. Shows next page to extract
4. Asks for confirmation (unless --auto)
5. Launches curator agent
6. Updates progress tracker
7. Shows summary

**Output:**
```
=================================
DAILY EXTRACTION WORKFLOW
=================================

Step 1: Running environment health check...
✅ ALL CHECKS PASSED

Step 2: Loading progress tracker...
✅ Progress: 5/60 pages complete

Step 3: Determining next page...
✅ Next: Flight Control Board
   URL: https://docs.proveskit.space/.../FC_board/
   Reason: F' Prime integration likely documented here

Step 4: Launching extraction...
[Human verifies each extraction...]

Step 5: Updating progress tracker...

=================================
DAILY EXTRACTION COMPLETE
=================================
Status: COMPLETED
Extractions: 12
Progress: 6/60 pages
```

---

### 3. `view_progress.py` - View Status

Shows current extraction progress.

```bash
# Summary view
python view_progress.py

# Detailed view (shows history)
python view_progress.py --detailed
```

**Output:**
```
=================================
PROVES KIT EXTRACTION PROGRESS
=================================

Phase: Phase 1: Hardware Foundation
Total Pages: 60
Completed: 5 ✅
Skipped: 1 ⏭️
Failed: 0 ❌
Remaining: 54

Progress: [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 8.3%

Next Page:
  Title: Flight Control Board
  URL: https://docs.proveskit.space/.../FC_board/
  Reason: F' Prime integration likely here

Last Updated: 2025-12-23T15:30:00Z
```

---

### 4. `skip_page.py` - Skip Current Page

Marks current page as skipped and moves to next.

```bash
python skip_page.py "Reason for skipping"
```

**Example:**
```bash
python skip_page.py "Page is tutorial, not architecture"
```

**Use when:**
- Page is not relevant (tutorials, guides, etc.)
- Page is broken/unavailable
- Page has no extractable architecture data

---

### 5. `reset_progress.py` - Reset Progress

Resets extraction progress to start over.

```bash
# Interactive mode (asks for confirmation)
python reset_progress.py

# Auto mode (skips confirmation)
python reset_progress.py --confirm
```

**Creates backup before resetting:**
- Backup saved to: `extraction_progress_backup_YYYYMMDD_HHMMSS.json`

---

## Progress Tracker Format

The `extraction_progress.json` file tracks all extraction progress:

```json
{
  "metadata": {
    "created": "2025-12-23T00:00:00Z",
    "last_updated": "2025-12-23T15:30:00Z",
    "total_pages": 60,
    "completed_pages": 5,
    "skipped_pages": 1,
    "failed_pages": 0,
    "current_phase": "Phase 1: Hardware Foundation"
  },
  "completed": [
    {
      "title": "Hardware Overview",
      "url": "https://docs.proveskit.space/.../hardware/index.md",
      "phase": "Phase 1: Hardware Foundation",
      "extractions_count": 8,
      "snapshot_ids": ["uuid-1", "uuid-2"],
      "completed_date": "2025-12-23T10:00:00Z"
    }
  ],
  "skipped": [
    {
      "title": "Getting Started Tutorial",
      "reason": "Not architecture documentation",
      "skipped_date": "2025-12-23T11:00:00Z"
    }
  ],
  "failed": [],
  "next_page": {
    "url": "https://docs.proveskit.space/.../FC_board/",
    "title": "Flight Control Board",
    "phase": "Phase 1: Hardware Foundation",
    "priority": 3,
    "reason": "F' Prime integration likely here"
  },
  "extraction_history": [...]
}
```

---

## Extraction Phases

Based on `PROVESKIT_DOCS_MAP.md`, extraction follows this priority order:

### Phase 1: Hardware Foundation (Pages 1-4)
1. Hardware Overview → Get component list
2. PROVES Prime → Main board
3. Flight Control Board → F' Prime integration
4. Battery Board → Power management

### Phase 2: F' Prime Integration (Page 5)
5. fprime-proves Tutorial → Understand F' Prime usage

### Phase 3: Software Architecture (Pages 6-8)
6. Software Overview
7. pysquared.py → Main flight software
8. cdh.py → Command & data handling

### Phase 4: Specific Components (Pages 9+)
9. Remaining hardware (solar panels, structure, etc.)
10. Remaining software modules (payload, detumble, etc.)

---

## Troubleshooting

### Environment Check Fails

**Problem:** `❌ Database (Neon): Connection failed`

**Solution:**
1. Check `.env` file has `NEON_DATABASE_URL`
2. Test connection: `python -c "import psycopg; psycopg.connect(os.environ['NEON_DATABASE_URL'])"`
3. Verify network connectivity

---

**Problem:** `❌ API Key (Anthropic): Missing`

**Solution:**
1. Check `.env` file has `ANTHROPIC_API_KEY`
2. Get key from: https://console.anthropic.com/
3. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

---

### Extraction Fails

**Problem:** Extraction fails with error

**Solution:**
1. Check error message in terminal
2. If network issue: Retry with `python daily_extraction.py`
3. If persistent: Skip page with `python skip_page.py "Error: [description]"`
4. Review failed pages: `python view_progress.py --detailed`

---

### Progress Tracker Corrupted

**Problem:** `extraction_progress.json` is corrupted

**Solution:**
```bash
# Reset progress (creates backup first)
python reset_progress.py
```

---

## Advanced Usage

### Resume from Specific Page

Edit `extraction_progress.json` manually:

```json
{
  "next_page": {
    "url": "https://docs.proveskit.space/.../specific_page/",
    "title": "Specific Page Title",
    "phase": "Phase X",
    "priority": 10,
    "reason": "Manually set to resume here"
  }
}
```

Then run:
```bash
python daily_extraction.py
```

---

### Bulk Skip Pages

Create a script to skip multiple pages:

```python
import subprocess

pages_to_skip = [
    "Tutorial page 1",
    "Tutorial page 2",
    "Guide page 1"
]

for page in pages_to_skip:
    subprocess.run([
        "python", "skip_page.py",
        f"Bulk skip: {page} (not architecture)"
    ])
```

---

## What's Next?

After implementing the basic workflow, consider:

### ✅ Recommended Additions

1. **Error Retry Logic**
   - Auto-retry failed pages with exponential backoff
   - Track retry count, max 3 attempts
   - After 3 failures, mark as "needs_manual_review"

2. **Weekly Summary Report**
   - Generate summary every Sunday
   - Show: pages completed this week, total progress, estimated completion
   - Save to: `reports/weekly_summary_YYYY_WW.md`

3. **Extraction Statistics**
   - Track: extractions per page, confidence scores, human decisions
   - Generate charts/graphs of progress
   - Identify patterns (which pages have most extractions, highest confidence, etc.)

### 🤔 Optional Additions

4. **Email Notifications**
   - Send email when extraction completes (useful for long sessions)
   - Requires: SMTP configuration in `.env`

5. **Cloud Backup**
   - Auto-backup progress to cloud (S3, GCS, etc.)
   - Or just use: `git add extraction_progress.json && git commit -m "Update progress"`

6. **MCP Server Health Check**
   - Check MCP servers are running (if using)
   - Auto-restart if needed

---

## Daily Workflow Best Practices

### Morning Routine

```bash
# 1. Check environment
python check_environment.py

# 2. View progress
python view_progress.py

# 3. Run daily extraction
python daily_extraction.py
```

### After Each Session

```bash
# Commit progress to git
git add extraction_progress.json
git commit -m "Daily extraction: completed [Page Title]"
git push
```

### Weekly Review

```bash
# View detailed progress
python view_progress.py --detailed

# Review failed/skipped pages
# Decide: retry or permanently skip?
```

---

## Support

Questions or issues?
- Check: `HITL_CONTEXT_REQUIREMENTS.md` for human verification details
- Check: `DATABASE_QUERY_TOOLS.md` for agent confidence calibration
- Review: Commit history for recent changes
