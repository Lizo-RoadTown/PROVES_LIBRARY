#!/usr/bin/env python3
"""Recreate Notion database for Error Logging WITHOUT API version parameter"""
import os
from notion_client import Client
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Don't specify notion_version - use default like suggestions database
notion = Client(auth=os.getenv("NOTION_API_KEY"))

# Get parent page from extractions database
EXTRACTIONS_DB_ID = os.getenv("NOTION_EXTRACTIONS_DB_ID")

print("=" * 80)
print("RECREATING ERRORS DATABASE (without API version)")
print("=" * 80)
print()

# Get parent page
print(f"Getting parent page from extractions database: {EXTRACTIONS_DB_ID}")
extractions_db = notion.databases.retrieve(database_id=EXTRACTIONS_DB_ID)
parent_page_id = extractions_db['parent']['page_id']
print(f"✓ Found parent page: {parent_page_id}")
print()

# Create database
try:
    new_database = notion.databases.create(
        parent={
            "type": "page_id",
            "page_id": parent_page_id
        },
        title=[
            {
                "type": "text",
                "text": {"content": "🚨 Curator Errors (v2)"}
            }
        ],
        is_inline=True,
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
                "select": {
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

    database_id = new_database['id']
    print(f"✓ Created database: {database_id}")

    # Check if data_sources exist
    data_source_id = None
    if new_database.get('data_sources'):
        data_source_id = new_database['data_sources'][0]['id']
        print(f"✓ Data source ID: {data_source_id}")
    else:
        print("⚠ No data sources in response - will use database_id for syncing")

    print()
    print("Update these in your .env file:")
    print(f"NOTION_ERRORS_DB_ID={database_id}")
    if data_source_id:
        print(f"NOTION_ERRORS_DATA_SOURCE_ID={data_source_id}")
    print()

    # Verify properties were created
    print("Verifying properties...")
    db = notion.databases.retrieve(database_id=database_id)
    if 'properties' in db and db['properties']:
        print("✓ Properties created successfully:")
        for prop_name in db['properties'].keys():
            print(f"  - {prop_name}")
    else:
        print("✗ No properties found in database")

except Exception as e:
    print(f"Error creating database: {e}")
    import traceback
    traceback.print_exc()
