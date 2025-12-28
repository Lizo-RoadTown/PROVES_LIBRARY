#!/usr/bin/env python3
"""Test with just Title and Status"""
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
print("TESTING WITH PARTIAL PROPERTIES")
print("=" * 80)

# Test 1: Just Title
print("Test 1: Creating page with just Title...")
try:
    page = notion.pages.create(
        parent={"type": "data_source_id", "data_source_id": DATA_SOURCE_ID},
        properties={
            "Title": {"title": [{"text": {"content": "Test - Title Only"}}]}
        }
    )
    print(f"✓ Success! Page ID: {page['id']}")
    notion.pages.update(page_id=page['id'], archived=True)
except Exception as e:
    print(f"✗ Failed: {e}")

print()

# Test 2: Title + Status
print("Test 2: Creating page with Title + Status...")
try:
    page = notion.pages.create(
        parent={"type": "data_source_id", "data_source_id": DATA_SOURCE_ID},
        properties={
            "Title": {"title": [{"text": {"content": "Test - Title + Status"}}]},
            "Status": {"status": {"name": "New"}}
        }
    )
    print(f"✓ Success! Page ID: {page['id']}")

    # Check what properties the page has
    page_props = page['properties'].keys()
    print(f"  Properties: {', '.join(page_props)}")

    notion.pages.update(page_id=page['id'], archived=True)
except Exception as e:
    print(f"✗ Failed: {e}")
