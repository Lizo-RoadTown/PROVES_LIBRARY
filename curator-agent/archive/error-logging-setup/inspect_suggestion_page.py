#!/usr/bin/env python3
"""Inspect a synced suggestion page"""
import os
from notion_client import Client
from dotenv import load_dotenv
from pathlib import Path
import json

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

notion = Client(auth=os.getenv("NOTION_API_KEY"), notion_version="2025-09-03")
PAGE_ID = "2d76b8ea-578a-8117-9582-ce92aa6ef88b"

print("=" * 80)
print("INSPECTING SYNCED SUGGESTION PAGE")
print("=" * 80)
print(f"Page ID: {PAGE_ID}")
print()

try:
    page = notion.pages.retrieve(page_id=PAGE_ID)

    print("Page properties:")
    for prop_name, prop_value in page['properties'].items():
        prop_type = prop_value.get('type', 'unknown')
        print(f"  - {prop_name}: {prop_type}")
    print()

    print("Parent info:")
    print(f"  Type: {page['parent']['type']}")
    if 'database_id' in page['parent']:
        print(f"  Database ID: {page['parent']['database_id']}")
    if 'data_source_id' in page['parent']:
        print(f"  Data Source ID: {page['parent']['data_source_id']}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
