#!/usr/bin/env python3
"""Test creating a page in the Errors database to see if properties auto-create"""
import os
from notion_client import Client
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Use the same API version as suggestion_sync.py
notion = Client(auth=os.getenv("NOTION_API_KEY"), notion_version="2025-09-03")

# Use the NEW database we just created
DB_ID = "798b41bd-d87f-4f9f-a56b-e3b65f10e8e4"
DATA_SOURCE_ID = "e90a364b-61c1-404b-a955-c2542c78f6c9"

print("=" * 80)
print("TESTING PAGE CREATION IN ERRORS DATABASE")
print("=" * 80)
print(f"Database ID: {DB_ID}")
print(f"Data Source ID: {DATA_SOURCE_ID}")
print()

try:
    print("Creating test page...")
    page = notion.pages.create(
        parent={"type": "data_source_id", "data_source_id": DATA_SOURCE_ID},
        properties={
            "Title": {"title": [{"text": {"content": "Test Error Page"}}]},
            "Error Type": {"select": {"name": "extraction_failed"}},
            "Source Table": {"select": {"name": "staging_extraction"}},
            "Error Count": {"number": 1},
            "Timestamp": {"date": {"start": "2025-12-28T10:00:00"}},
            "Status": {"select": {"name": "New"}}
        }
    )

    page_id = page["id"]
    print(f"✓ Created page: {page_id}")
    print()

    # Now check if properties were created in the database
    print("Checking if properties were created in database...")
    db = notion.databases.retrieve(database_id=DB_ID)

    if 'properties' in db and db['properties']:
        print("✓ Properties found:")
        for prop_name in db['properties'].keys():
            print(f"  - {prop_name}")
    else:
        print("✗ Still no properties in database")

    # Archive the test page
    print()
    print("Archiving test page...")
    notion.pages.update(page_id=page_id, archived=True)
    print("✓ Test page archived")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
