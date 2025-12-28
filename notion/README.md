# Notion Integration

This directory contains all Notion-related scripts and documentation for the PROVES Library curator system.

## Structure

### scripts/

Production scripts for Notion integration:

- **sync_errors_to_notion.py** - Sync error logs from database to Notion Errors database
- **manual_sync_suggestions.py** - Manually sync improvement suggestions to Notion
- **notion_webhook_server.py** - Webhook server for bidirectional sync (extractions, suggestions, errors)
- **setup_notion.py** - Initial Notion workspace setup

### docs/

Documentation for Notion integration:

- **ERROR_LOGGING_GUIDE.md** - Complete guide for error logging system
  - How agents log errors to database tables
  - Error sync workflow to Notion
  - Notion database schema and properties
  - Best practices

## Usage

### Error Sync

```bash
# Sync errors from last 24 hours
python -X utf8 notion/scripts/sync_errors_to_notion.py

# Sync errors from last 7 days
python -X utf8 notion/scripts/sync_errors_to_notion.py 168
```

### Suggestion Sync

```bash
# Manually sync unsynced suggestions
python -X utf8 notion/scripts/manual_sync_suggestions.py
```

### Webhook Server

```bash
# Start webhook server for bidirectional sync
python -X utf8 notion/scripts/notion_webhook_server.py
```

## Notion Databases

The curator system uses three Notion databases:

1. **Extractions** - Candidate evidence extracted from documentation
2. **Improvement Suggestions** - Meta-learning suggestions for system improvements
3. **Errors** - Error logs from all curator agents
