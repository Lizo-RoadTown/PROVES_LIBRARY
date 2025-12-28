#!/usr/bin/env python3
"""Test creating a page in the original Errors database"""
import os
from notion_client import Client
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

notion = Client(auth=os.getenv("NOTION_API_KEY"), notion_version="2025-09-03")
DB_ID = os.getenv("NOTION_ERRORS_DB_ID")
DATA_SOURCE_ID = os.getenv("NOTION_ERRORS_DATA_SOURCE_ID")

print("=" * 80)
print("TESTING PAGE CREATION IN ORIGINAL ERRORS DATABASE")
print("=" * 80)
print(f"Database ID: {DB_ID}")
print(f"Data Source ID: {DATA_SOURCE_ID}")
print()

try:
    print("Creating test page...")
    page = notion.pages.create(
        parent={"type": "data_source_id", "data_source_id": DATA_SOURCE_ID},
        properties={
            "Title": {"title": [{"text": {"content": "Test Error - Manual Properties"}}]},
            "Error Type": {"select": {"name": "extraction_failed"}},
            "Source Table": {"select": {"name": "staging_extraction"}},
            "Error Count": {"number": 1},
            "Timestamp": {"date": {"start": "2025-12-28T10:00:00"}},
            "Status": {"status": {"name": "New"}}
        }
    )

    page_id = page["id"]
    print(f"✓ Created page: {page_id}")
    print()
    print("SUCCESS! Properties are working now.")
    print()

    # Archive the test page
    print("Archiving test page...")
    notion.pages.update(page_id=page_id, archived=True)
    print("✓ Test page archived")

except Exception as e:
    print(f"✗ Error: {e}")
