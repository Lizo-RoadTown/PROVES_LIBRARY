#!/usr/bin/env python3
"""
Error Sync - Push errors from database tables to Notion

Reads error_log entries from all tables and syncs to Notion Errors database.
Can be run periodically or on-demand.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any
import psycopg
from dotenv import load_dotenv
from pathlib import Path
from notion_client import Client

# Load environment
env_path = Path(__file__).parent.parent / '.env' if (Path(__file__).parent.parent / '.env').exists() else Path(__file__).parent / '.env'
load_dotenv(env_path)

# Import error logger
from src.curator.error_logger import ErrorLogger


class ErrorSyncToNotion:
    """Syncs errors from database to Notion"""

    def __init__(self):
        self.notion = Client(auth=os.getenv('NOTION_API_KEY'), notion_version='2025-09-03')
        self.db_url = os.getenv('NEON_DATABASE_URL')
        self.errors_db_id = os.getenv('NOTION_ERRORS_DB_ID')
        self.errors_data_source_id = os.getenv('NOTION_ERRORS_DATA_SOURCE_ID')

        if not self.errors_db_id:
            raise ValueError("NOTION_ERRORS_DB_ID not set in environment")
        if not self.errors_data_source_id:
            raise ValueError("NOTION_ERRORS_DATA_SOURCE_ID not set in environment")

        self.logger = ErrorLogger()

    def sync_recent_errors(self, since_hours: int = 24, limit: int = 50):
        """
        Sync recent errors to Notion

        Args:
            since_hours: Only sync errors from the last N hours
            limit: Maximum number of errors to sync
        """
        print("=" * 80)
        print("SYNCING ERRORS TO NOTION")
        print("=" * 80)
        print(f"Looking for errors from the last {since_hours} hours...")
        print()

        # Query all recent errors
        try:
            conn = psycopg.connect(self.db_url)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        source_table,
                        record_id,
                        record_name,
                        error_log,
                        error_count,
                        last_error_at
                    FROM all_errors
                    WHERE last_error_at >= NOW() - INTERVAL '%s hours'
                    ORDER BY last_error_at DESC
                    LIMIT %s
                """, (since_hours, limit))

                errors = cur.fetchall()
            conn.close()

            print(f"Found {len(errors)} error records")
            print()

            synced_count = 0
            for error_record in errors:
                source_table, record_id, record_name, error_log, error_count, last_error_at = error_record

                # Get the most recent error from the log
                if error_log and len(error_log) > 0:
                    latest_error = error_log[-1]  # Last error in the array

                    # Create Notion page for this error
                    try:
                        self._create_error_page(
                            source_table=source_table,
                            record_id=record_id,
                            record_name=record_name,
                            error_data=latest_error,
                            error_count=error_count,
                            last_error_at=last_error_at
                        )
                        synced_count += 1
                        print(f"✓ Synced error from {source_table}: {record_name[:50]}")
                    except Exception as e:
                        print(f"✗ Failed to sync error: {e}")

            print()
            print(f"Synced {synced_count}/{len(errors)} errors to Notion")

        except Exception as e:
            print(f"❌ Error querying database: {e}")
            import traceback
            traceback.print_exc()

    def _create_error_page(
        self,
        source_table: str,
        record_id: str,
        record_name: str,
        error_data: Dict[str, Any],
        error_count: int,
        last_error_at: datetime
    ):
        """Create a Notion page for an error"""

        # Extract error details
        error_type = error_data.get('error_type', 'unknown')
        error_message = error_data.get('message', 'No message')
        stack_trace = error_data.get('stack_trace', '')
        context = error_data.get('context', {})
        logged_at = error_data.get('logged_at', last_error_at.isoformat())

        # Build title
        title = f"{error_type}: {record_name[:100]}"

        # Build content blocks
        blocks = []

        # Error summary
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "🚨 ERROR DETAILS"}}]}
        })

        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": error_message}}]}
        })

        # Source information
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "📍 SOURCE"}}]}
        })

        source_text = f"Table: {source_table}\nRecord ID: {record_id}\nRecord: {record_name}"
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": source_text}}]}
        })

        # Context
        if context:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "📋 CONTEXT"}}]}
            })

            context_text = json.dumps(context, indent=2)
            blocks.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"text": {"content": context_text[:2000]}}],
                    "language": "json"
                }
            })

        # Stack trace
        if stack_trace:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "🔍 STACK TRACE"}}]}
            })

            blocks.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"text": {"content": stack_trace[:2000]}}],
                    "language": "python"
                }
            })

        # Create the page using data_source_id (API v2025-09-03)
        # Property mapping to match Notion database:
        # - Error Severity: select (error type)
        # - Source: select (source table)
        # - Number: number (error count)
        # - Date Reported: date (timestamp)
        # - Status: status
        # - Title: title
        page = self.notion.pages.create(
            parent={"type": "data_source_id", "data_source_id": self.errors_data_source_id},
            properties={
                "Title": {"title": [{"text": {"content": title[:2000]}}]},
                "Error Severity": {"select": {"name": error_type}},
                "Source": {"select": {"name": source_table}},
                "Number": {"number": error_count},
                "Date Reported": {"date": {"start": logged_at}},
                "Status": {"status": {"name": "New"}}
            },
            children=blocks
        )

        return page["id"]


if __name__ == "__main__":
    import sys

    # Default: sync errors from last 24 hours
    since_hours = 24
    if len(sys.argv) > 1:
        try:
            since_hours = int(sys.argv[1])
        except ValueError:
            print(f"Invalid hours: {sys.argv[1]}, using default: 24")

    syncer = ErrorSyncToNotion()
    syncer.sync_recent_errors(since_hours=since_hours, limit=50)
