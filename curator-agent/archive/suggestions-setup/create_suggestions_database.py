#!/usr/bin/env python3
"""
Create Notion database for Improvement Suggestions
Meta-learning system that analyzes extraction patterns to suggest improvements
"""
import os
from notion_client import Client
from dotenv import load_dotenv
from pathlib import Path

# Load .env from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

notion = Client(auth=os.getenv("NOTION_API_KEY"))

# We'll use the same parent as the extractions database
# The extractions database data source can tell us the parent
EXTRACTIONS_DB_ID = os.getenv("NOTION_EXTRACTIONS_DB_ID")

print("=" * 80)
print("CREATING IMPROVEMENT SUGGESTIONS DATABASE")
print("=" * 80)
print()

# Get the parent page from the existing extractions database
print(f"Getting parent page from extractions database: {EXTRACTIONS_DB_ID}")
extractions_db = notion.databases.retrieve(database_id=EXTRACTIONS_DB_ID)
parent_page_id = extractions_db['parent']['page_id']
print(f"✓ Found parent page: {parent_page_id}")
print()

# Create the database
try:
    new_database = notion.databases.create(
        parent={
            "type": "page_id",
            "page_id": parent_page_id
        },
        title=[
            {
                "type": "text",
                "text": {"content": "🧠 Improvement Suggestions"}
            }
        ],
        is_inline=True,
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

    database_id = new_database['id']
    print(f"✓ Created database: {database_id}")
    print()
    print("Add this to your .env file:")
    print(f"NOTION_SUGGESTIONS_DATABASE_ID={database_id}")
    print()
    print("=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. Add the database ID to .env")
    print("2. Create webhook subscription for this database")
    print("3. Run the analysis agent to generate suggestions")
    print()

except Exception as e:
    print(f"Error creating database: {e}")
    import traceback
    traceback.print_exc()
