#!/usr/bin/env python3
"""Check the actual property names in the Notion Suggestions database"""
import os
from notion_client import Client
from dotenv import load_dotenv
from pathlib import Path
import json

# Load .env from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

notion = Client(auth=os.getenv("NOTION_API_KEY"))
SUGGESTIONS_DB_ID = os.getenv("NOTION_SUGGESTIONS_DB_ID")

print("=" * 80)
print("NOTION SUGGESTIONS DATABASE SCHEMA")
print("=" * 80)
print()

db = notion.databases.retrieve(database_id=SUGGESTIONS_DB_ID)

print(f"Database ID: {SUGGESTIONS_DB_ID}")
print()
print("Full database object:")
print(json.dumps(db, indent=2, default=str))
