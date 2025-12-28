#!/usr/bin/env python3
"""Add properties to the Errors database"""
import os
from notion_client import Client
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

notion = Client(auth=os.getenv("NOTION_API_KEY"), notion_version="2025-09-03")
DB_ID = os.getenv("NOTION_ERRORS_DB_ID")

print("=" * 80)
print("ADDING PROPERTIES TO ERRORS DATABASE")
print("=" * 80)
print(f"Database ID: {DB_ID}")
print()

try:
    result = notion.databases.update(
        database_id=DB_ID,
        properties={
            "Title": {
                "title": {}
            },
            "Error Type": {
                "select": {
                    "options": [
                        {"name": "extraction_failed", "color": "red"},
                        {"name": "validation_failed", "color": "orange"},
                        {"name": "api_timeout", "color": "yellow"},
                        {"name": "parsing_error", "color": "pink"},
                        {"name": "analysis_failed", "color": "purple"},
                        {"name": "notion_sync_failed", "color": "gray"},
                        {"name": "database_error", "color": "brown"}
                    ]
                }
            },
            "Source Table": {
                "select": {
                    "options": [
                        {"name": "staging_extraction", "color": "blue"},
                        {"name": "improvement_suggestion", "color": "green"}
                    ]
                }
            },
            "Error Count": {
                "number": {
                    "format": "number"
                }
            },
            "Timestamp": {
                "date": {}
            },
            "Status": {
                "status": {
                    "options": [
                        {"name": "New", "color": "red"},
                        {"name": "Investigating", "color": "yellow"},
                        {"name": "Resolved", "color": "green"},
                        {"name": "Ignored", "color": "gray"}
                    ]
                }
            }
        }
    )

    print("✓ Properties added successfully!")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
