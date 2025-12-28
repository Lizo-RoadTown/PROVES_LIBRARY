#!/usr/bin/env python3
"""Check if Notion Errors database exists and what properties it has"""
import os
from notion_client import Client
from dotenv import load_dotenv
from pathlib import Path
import json

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

notion = Client(auth=os.getenv("NOTION_API_KEY"), notion_version="2025-09-03")
ERRORS_DB_ID = os.getenv("NOTION_ERRORS_DB_ID")

print("=" * 80)
print("CHECKING NOTION ERRORS DATABASE")
print("=" * 80)
print(f"Database ID from .env: {ERRORS_DB_ID}")
print()

if not ERRORS_DB_ID:
    print("❌ NOTION_ERRORS_DB_ID not set in .env")
    print()
    print("You need to either:")
    print("1. Create the database manually in Notion")
    print("2. Or run a script to create it via the API")
else:
    try:
        db = notion.databases.retrieve(database_id=ERRORS_DB_ID)

        print(f"✓ Database exists: {db['title'][0]['plain_text'] if db.get('title') else 'Untitled'}")
        print()

        # Check for data sources
        if 'data_sources' in db:
            print("Data Sources:")
            for ds in db['data_sources']:
                print(f"  - ID: {ds['id']}")
                print(f"    Name: {ds['name']}")
            print()

        # Try creating a test page to see what properties are available
        print("Testing page creation to discover properties...")
        try:
            test_page = notion.pages.create(
                parent={"database_id": ERRORS_DB_ID},
                properties={
                    "Title": {"title": [{"text": {"content": "Test Error Page"}}]}
                }
            )

            print("✓ Test page created successfully!")
            print()
            print("Available properties:")
            for prop_name, prop_value in test_page['properties'].items():
                prop_type = prop_value.get('type', 'unknown')
                print(f"  - {prop_name}: {prop_type}")

            # Delete the test page
            notion.pages.update(page_id=test_page['id'], archived=True)
            print()
            print("(Test page archived)")

        except Exception as e:
            print(f"✗ Could not create test page: {e}")
            print()
            print("The database might not have any properties set up yet.")
            print("You'll need to add properties manually in Notion:")
            print("  - Title (title)")
            print("  - Error Type (select)")
            print("  - Source Table (select)")
            print("  - Error Count (number)")
            print("  - Timestamp (date)")
            print("  - Status (status)")

    except Exception as e:
        print(f"✗ Could not retrieve database: {e}")
        print()
        print("The database ID might be invalid or not shared with the integration.")
        print("You need to create a new Errors database in Notion.")
