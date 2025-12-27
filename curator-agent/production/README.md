# Production Scripts - Validated & Ready for Use

**Last Updated:** 2025-12-26

This directory contains **production-ready, validated scripts** that have been tested and proven to work reliably.

---

## 🏆 Gold Standard Scripts

### [YES] process_extractions.py
**Status:** Production-Ready | Validated 2025-12-27

**What it does:**
- Orchestrates extraction pipeline: Extract → Validate → Store
- Processes URLs from `urls_to_process` database queue
- Deterministic lineage computation with explicit UTF-8 encoding
- Automatic evidence verification (byte-level matching)

**Performance:**
- **Cost:** 10-12 cents per extraction (optimized from 40-60 cents)
- **Recursion limit:** 1 tool call (extractor), 5 each (validator/storage)
- **Models:** Sonnet 4.5 (extractor), Haiku (validator/storage for 90% cost reduction)

**Validation:**
- Tested with F' Prime and PROVES Kit documentation
- Lineage confidence: 1.0 (perfect byte-for-byte matches)
- All 3 pipeline steps completing successfully
- Evidence verification working with UTF-8 encoding

**Usage:**
```bash
# Process 10 URLs from queue
python production/process_extractions.py --limit 10

# Continuous processing until queue empty
python production/process_extractions.py --continuous
```

**Architecture:**
- **Deterministic lineage:** Pure Python code (not agent behavior)
- **3-step matching:** exact (1.0), normalized (0.85), not found (0.0)
- **Stores:** evidence_checksum, byte_offset, byte_length, verification_details

See `CHANGELOG.md` and `DEPLOYMENT_NOTES.md` for details.

---

### [YES] find_good_urls.py
**Status:** Production-Ready | Validated 2025-12-26

**What it does:**
- Crawls documentation sites (F' Prime, PROVES Kit, custom URLs)
- Assesses page quality (0.0-1.0 scoring, threshold: 0.65)
- Extracts context hints (components, interfaces, keywords)
- Stores qualified URLs in `urls_to_process` database table

**Validation:**
- Tested on 10 pages from F' Prime and PROVES Kit
- Quality scoring verified to capture both technical AND educational content
- Successfully filters noise (TOC pages, indexes, short pages)
- Correctly identifies institutional knowledge (how-to guides, patterns, organizational docs)

**Usage:**
```bash
# Crawl F' Prime docs
python production/find_good_urls.py --fprime --max-pages 50

# Crawl PROVES Kit docs
python production/find_good_urls.py --proveskit --max-pages 50

# Crawl both
python production/find_good_urls.py --fprime --proveskit --max-pages 100

# Custom URL
python production/find_good_urls.py --url https://docs.example.com --max-pages 30
```

**Philosophy:**
Educational content is institutional knowledge. The script values:
- How-to guides and tutorials
- Architectural patterns and design philosophy
- Organizational structures and best practices
- Mental models and decision frameworks

These are the "nodes and edges" that prevent knowledge loss when students graduate.

---

## 📋 Criteria for Production Status

Scripts in this directory must:
1. [YES] Be tested with real data
2. [YES] Have validated outputs (manually reviewed)
3. [YES] Handle errors gracefully
4. [YES] Include clear usage documentation
5. [YES] Support the core mission (institutional knowledge preservation)

---

## 🔄 Process for Adding Scripts

1. Develop in `curator-agent/` (root or experimental/)
2. Test with real data (10+ examples)
3. Manually validate outputs
4. Add validation header and documentation
5. Move to `production/` directory
6. Update this README

---

## 🎯 Mission Alignment

All production scripts support the PROVES Library mission:
- Build institutional memory for university space programs
- Prevent knowledge loss when students graduate
- Capture dependencies before system failures occur
- Map mental models, not just API references
