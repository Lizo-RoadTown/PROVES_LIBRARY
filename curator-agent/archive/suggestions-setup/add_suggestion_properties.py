#!/usr/bin/env python3
"""
Add properties to the Improvement Suggestions database
Notion API 2025-09-03 requires properties to be added via update
"""
import os
from notion_client import Client
from dotenv import load_dotenv
from pathlib import Path

# Load .env from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

notion = Client(auth=os.getenv("NOTION_API_KEY"), notion_version="2025-09-03")

DATA_SOURCE_ID = os.getenv("NOTION_SUGGESTIONS_DATA_SOURCE_ID")
DB_ID = os.getenv("NOTION_SUGGESTIONS_DB_ID")

print("=" * 80)
print("ADDING PROPERTIES TO IMPROVEMENT SUGGESTIONS DATABASE")
print("=" * 80)
print(f"Database ID: {DB_ID}")
print(f"Data Source ID: {DATA_SOURCE_ID}")
print()

# Add properties using database update
try:
    result = notion.databases.update(
        database_id=DB_ID,
        properties={
            "Title": {
                "title": {}
            },
            "Category": {
                "select": {
                    "options": [
                        {"name": "Prompt Update", "color": "blue"},
                        {"name": "Ontology Change", "color": "purple"},
                        {"name": "Method Improvement", "color": "green"},
                        {"name": "Evidence Type Refinement", "color": "orange"},
                        {"name": "Confidence Calibration", "color": "yellow"}
                    ]
                }
            },
            "Evidence": {
                "rich_text": {}
            },
            "Current State": {
                "rich_text": {}
            },
            "Proposed Change": {
                "rich_text": {}
            },
            "Impact": {
                "number": {
                    "format": "number"
                }
            },
            "Confidence": {
                "select": {
                    "options": [
                        {"name": "Low", "color": "gray"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "High", "color": "green"}
                    ]
                }
            },
            "Accept/Reject": {
                "select": {
                    "options": [
                        {"name": "Approved", "color": "green"},
                        {"name": "Rejected", "color": "red"},
                        {"name": "Modified", "color": "yellow"}
                    ]
                }
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Pending", "color": "gray"},
                        {"name": "Approved", "color": "green"},
                        {"name": "Rejected", "color": "red"},
                        {"name": "Implemented", "color": "blue"},
                        {"name": "Needs Review", "color": "orange"}
                    ]
                }
            },
            "Created Date": {
                "date": {}
            },
            "Extraction IDs": {
                "rich_text": {}
            },
            "Suggestion ID": {
                "rich_text": {}
            }
        }
    )

    print("✓ Properties added successfully!")
    print()
    print("Properties:")
    for prop_name in result.get('properties', {}).keys():
        print(f"  - {prop_name}")

except Exception as e:
    print(f"✗ Error adding properties: {e}")
    import traceback
    traceback.print_exc()
