# Quick Start - Daily Extraction

**For Claude Code or new sessions:** This is the main entry point.

---

## First Time Setup

```bash
# 1. Check everything is ready
python check_environment.py

# Expected: All checks pass ✅
```

If any checks fail, fix them before proceeding.

---

## Daily Extraction Workflow

```bash
# Run the daily extraction
python daily_extraction.py
```

This will:
1. ✅ Run health checks
2. ✅ Show you the next page to extract
3. ✅ Launch the curator agent
4. ✅ **You verify each extraction** (this is the human-in-the-loop part)
5. ✅ Auto-generate daily report
6. ✅ Update progress tracker

---

## What Happens During Extraction

The curator agent will:
1. Fetch the PROVES Kit documentation page
2. Extract architecture using FRAMES methodology (see ONTOLOGY.md)
3. **Present each extraction to you for verification**

**For each extraction, you'll see:**
- Source URL
- Evidence quote (from the documentation)
- Extracted entity (type, key, properties)
- Confidence score and reasoning
- Agent's reasoning trail (what they compared against)
- Duplicate check results

**You decide:**
- `[y]es` - Approve (becomes verified truth)
- `[n]o` - Reject (inaccurate)
- `[e]dit` - Correct (becomes GOLD training data)

---

## After Each Page

The script automatically:
- Saves progress to `extraction_progress.json`
- Generates report to `reports/daily_report_YYYY-MM-DD.md`
- Determines next page in queue

---

## View Progress

```bash
# Summary view
python view_progress.py

# Detailed view
python view_progress.py --detailed
```

---

## Common Commands

```bash
# Skip current page
python skip_page.py "Reason for skipping"

# Reset progress (with backup)
python reset_progress.py

# Generate final summary (after 10+ pages)
python generate_final_report.py
```

---

## Files You Care About

- `extraction_progress.json` - Current progress tracker
- `reports/daily_report_*.md` - Daily summaries
- `WORKFLOW_README.md` - Complete documentation
- `ONTOLOGY.md` - Extraction methodology (loaded by agents)
- `PROVESKIT_DOCS_MAP.md` - Page priority order

---

## Troubleshooting

**Q: Environment check fails?**
A: Follow error messages - usually missing .env variables

**Q: Extraction fails?**
A: Auto-retries 3 times. Check `extraction_progress.json` for error

**Q: How do I resume from specific page?**
A: Edit `extraction_progress.json` → `next_page` → set desired URL

---

## The Goal

Extract **10 pages** with heavy human verification to build initial verified corpus.

This enables the **bootstrapping strategy**:
- Pages 1-10: Blind extraction, humans verify everything
- Page 11+: Agents query 10+ verified examples for confidence
- Page 20+: High confidence calibrated against 100+ examples

**You're building institutional memory that prevents knowledge loss.**

---

*For complete docs: See WORKFLOW_README.md*
