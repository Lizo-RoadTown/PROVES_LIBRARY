#!/usr/bin/env python3
"""Check the extractions database schema to see how it works"""
import os
from notion_client import Client
from dotenv import load_dotenv
from pathlib import Path
import json

# Load .env from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

notion = Client(auth=os.getenv("NOTION_API_KEY"), notion_version="2025-09-03")

EXTRACTIONS_DB_ID = os.getenv("NOTION_EXTRACTIONS_DB_ID")
EXTRACTIONS_DATA_SOURCE_ID = os.getenv("NOTION_EXTRACTIONS_DATA_SOURCE_ID")

print("=" * 80)
print("EXTRACTIONS DATABASE SCHEMA")
print("=" * 80)
print()

# Try retrieving the database
db = notion.databases.retrieve(database_id=EXTRACTIONS_DB_ID)

print(f"Database ID: {EXTRACTIONS_DB_ID}")
print(f"Data Source ID: {EXTRACTIONS_DATA_SOURCE_ID}")
print()

# Check data sources
if 'data_sources' in db:
    print("Data Sources:")
    for ds in db['data_sources']:
        print(f"  - ID: {ds['id']}")
        print(f"    Name: {ds['name']}")
    print()

# Try to retrieve the data source
print("Attempting to retrieve data source properties...")
try:
    data_source = notion.databases.retrieve(database_id=EXTRACTIONS_DATA_SOURCE_ID)
    print("Data source retrieved!")
    print(json.dumps(data_source, indent=2, default=str)[:2000])
except Exception as e:
    print(f"Error: {e}")

# Check the database properties
print()
print("Database object keys:", list(db.keys()))
