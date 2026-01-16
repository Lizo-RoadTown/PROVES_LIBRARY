# Production Scripts

Production-ready scripts for running the PROVES Library curator system.

## Structure

### scripts/

Production scripts that orchestrate the curator workflow:

- **find_good_urls.py** - Smart web crawler that finds high-quality documentation pages
  ```bash
  python production/scripts/find_good_urls.py --fprime --proveskit --max-pages 50
  ```

- **process_extractions.py** - Process queued URLs with curator agent
  ```bash
  python production/scripts/process_extractions.py --limit 10
  python production/scripts/process_extractions.py --continuous  # Until queue empty
  ```

- **improvement_analyzer.py** - Meta-learning system that analyzes extraction patterns
  ```bash
  python production/scripts/improvement_analyzer.py
  ```

- **check_pending_extractions.py** - Diagnostic tool to check queue status
  ```bash
  python production/scripts/check_pending_extractions.py
  ```

### docs/

Production documentation:

- **README.md** - Production script documentation (see scripts/ subdirectory)
- **DEPLOYMENT_NOTES.md** - Deployment and operational notes
- **CHANGELOG.md** - Production system change history

## Workflow

### 1. Find URLs
```bash
python production/scripts/find_good_urls.py --fprime --proveskit --max-pages 50
```
Crawls documentation sites and adds high-quality pages to the queue.

### 2. Process Extractions
```bash
python production/scripts/process_extractions.py --limit 10
```
Runs curator agent on queued URLs to extract evidence candidates.

### 3. Review in Notion
Extracted candidates appear in Notion for human review and approval.

### 4. Analyze Patterns
```bash
python production/scripts/improvement_analyzer.py
```
Analyzes extraction patterns and generates improvement suggestions.

## Environment Setup

All scripts use environment variables from `.env` in the project root:
- `DATABASE_URL` - Database connection
- `ANTHROPIC_API_KEY` - Claude API for curator agent
- `LANGCHAIN_API_KEY` - LangSmith tracing
- `NOTION_API_KEY` - Notion integration

## Related Directories

- **curator-agent/** - Agent implementation (used by production scripts)
- **neon-database/** - Database schema and utilities
- **notion/** - Notion sync and webhook server
- **langchain/** - LangGraph deployment configuration
