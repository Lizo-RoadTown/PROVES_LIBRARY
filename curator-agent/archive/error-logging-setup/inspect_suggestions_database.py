#!/usr/bin/env python3
"""Inspect the Suggestions database schema"""
import os
from notion_client import Client
from dotenv import load_dotenv
from pathlib import Path
import json

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

notion = Client(auth=os.getenv("NOTION_API_KEY"))
DB_ID = os.getenv("NOTION_SUGGESTIONS_DB_ID")

print("=" * 80)
print("INSPECTING SUGGESTIONS DATABASE SCHEMA")
print("=" * 80)
print(f"Database ID: {DB_ID}")
print()

try:
    db = notion.databases.retrieve(database_id=DB_ID)

    print(f"Title: {db['title'][0]['plain_text'] if db.get('title') else 'Untitled'}")
    print()

    print("Properties:")
    if 'properties' in db and db['properties']:
        for prop_name, prop_config in db['properties'].items():
            prop_type = prop_config.get('type', 'unknown')
            print(f"  - {prop_name}: {prop_type}")
    else:
        print("  NO PROPERTIES FOUND")
    print()

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
