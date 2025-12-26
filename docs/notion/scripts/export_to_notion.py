"""
Prepare Reports for Notion Sync

Formats reports for easy syncing to Notion via Claude Desktop (which has MCP access).
Creates JSON summaries that Claude can read and sync.

Usage:
    python export_to_notion.py                    # Prepare today's report
    python export_to_notion.py --summary          # Prepare weekly summary
    python export_to_notion.py --errors           # Prepare error log
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path


def load_progress():
    """Load progress tracker"""
    progress_file = Path(__file__).parent / 'extraction_progress.json'
    if not progress_file.exists():
        return None
    with open(progress_file, 'r') as f:
        return json.load(f)


def prepare_daily_report_for_notion():
    """Prepare today's daily report for Notion sync"""
    date_str = datetime.now().strftime('%Y-%m-%d')
    report_file = Path(__file__).parent / 'reports' / f'daily_report_{date_str}.md'

    if not report_file.exists():
        print(f"❌ No report found for {date_str}")
        print(f"   Run daily_extraction.py first")
        return None

    with open(report_file, 'r') as f:
        report_content = f.read()

    # Create summary JSON for Claude Desktop
    summary = {
        "type": "daily_report",
        "date": date_str,
        "report_file": str(report_file),
        "content": report_content,
        "instruction": "Append this to Notion page 'PROVES Extraction - Daily Reports'"
    }

    output_file = Path(__file__).parent / 'reports' / f'notion_sync_{date_str}.json'
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print()
    print("=" * 80)
    print("NOTION SYNC PREPARED")
    print("=" * 80)
    print()
    print(f"Report: {report_file}")
    print(f"Sync file: {output_file}")
    print()
    print("To sync to Notion:")
    print("1. Open Claude Desktop (which has Notion MCP access)")
    print("2. Say:")
    print()
    print(f'   "Read {output_file} and sync the daily report to my Notion page"')
    print()
    print("=" * 80)
    print()

    return output_file


def prepare_error_log_for_notion():
    """Prepare error log for Notion sync"""
    progress = load_progress()
    if not progress:
        return None

    failed = progress.get('failed', [])
    if not failed:
        print("✅ No failed pages to log")
        return None

    # Format errors for Notion
    errors = []
    for item in failed:
        errors.append({
            "title": item.get('title'),
            "url": item.get('url'),
            "error": item.get('error'),
            "retry_count": item.get('retry_count', 0),
            "date": item.get('failed_date', 'Unknown')
        })

    summary = {
        "type": "error_log",
        "date": datetime.now().isoformat(),
        "error_count": len(errors),
        "errors": errors,
        "instruction": "Append these errors to Notion page 'PROVES Extraction - Error Log'"
    }

    output_file = Path(__file__).parent / 'reports' / 'notion_errors.json'
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print()
    print("=" * 80)
    print("ERROR LOG PREPARED")
    print("=" * 80)
    print()
    print(f"Errors: {len(errors)}")
    print(f"Sync file: {output_file}")
    print()
    print("To sync to Notion:")
    print("1. Open Claude Desktop")
    print("2. Say:")
    print()
    print(f'   "Read {output_file} and log the errors to my Notion error page"')
    print()
    print("=" * 80)
    print()

    return output_file


def main():
    """Main function"""
    if '--summary' in sys.argv:
        print("Weekly summary not implemented yet")
        return 1
    elif '--errors' in sys.argv:
        prepare_error_log_for_notion()
    else:
        # Default: prepare daily report
        prepare_daily_report_for_notion()

    return 0


if __name__ == "__main__":
    sys.exit(main())
