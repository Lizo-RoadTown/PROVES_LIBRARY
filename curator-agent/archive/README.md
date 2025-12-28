# Archived Scripts

This directory contains one-time setup scripts, diagnostic tools, and test files that are no longer needed for day-to-day operations but may be useful for reference.

## error-logging-setup/

Scripts used to set up the error logging system:
- Database creation scripts
- Property addition attempts
- Test and diagnostic scripts

These files were used during initial setup and troubleshooting. The final working system uses:
- `sync_errors_to_notion.py` (in parent directory)
- `src/curator/error_logger.py` (in parent directory)

## suggestions-setup/

Scripts used to set up the Improvement Suggestions database:
- Database creation scripts
- Property configuration
- Test sync scripts

The final working system uses:
- `src/curator/suggestion_sync.py` (in parent directory)
- `manual_sync_suggestions.py` (in parent directory)

## extractions-diagnostics/

Diagnostic scripts used during troubleshooting:
- Schema inspection tools
- Sync status checkers
- Page content validators

The final working system uses:
- `src/curator/curator_sync.py` (in parent directory)
- `daily_extraction.py` (in parent directory)
