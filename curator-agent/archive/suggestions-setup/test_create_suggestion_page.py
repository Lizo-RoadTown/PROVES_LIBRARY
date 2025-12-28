#!/usr/bin/env python3
"""Test creating a page in the suggestions database"""
import os
from notion_client import Client
from dotenv import load_dotenv
from pathlib import Path
import json

# Load .env from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

notion = Client(auth=os.getenv("NOTION_API_KEY"), notion_version="2025-09-03")

DATA_SOURCE_ID = os.getenv("NOTION_SUGGESTIONS_DATA_SOURCE_ID")
DB_ID = os.getenv("NOTION_SUGGESTIONS_DB_ID")

print("=" * 80)
print("TEST: Creating a page in Improvement Suggestions database")
print("=" * 80)
print()

# Try creating with minimal properties
try:
    print("Attempting to create page...")
    page = notion.pages.create(
        parent={"type": "data_source_id", "data_source_id": DATA_SOURCE_ID},
        properties={
            "Title": {"title": [{"text": {"content": "Test Suggestion"}}]}
        }
    )

    print("✓ Page created successfully!")
    print(f"Page ID: {page['id']}")
    print()
    print("Full response:")
    print(json.dumps(page, indent=2, default=str))

except Exception as e:
    print(f"✗ Error: {e}")
    print()
    import traceback
    traceback.print_exc()
