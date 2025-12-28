#!/usr/bin/env python3
"""Create a minimal test page to see what properties work"""
import os
from notion_client import Client
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

client = Client(auth=os.getenv('NOTION_API_KEY'), notion_version='2025-09-03')
data_source_id = os.getenv('NOTION_SUGGESTIONS_DATA_SOURCE_ID')

print("Creating minimal test page...")
try:
    page = client.pages.create(
        parent={'type': 'data_source_id', 'data_source_id': data_source_id},
        properties={
            'Title': {'title': [{'text': {'content': 'Minimal Test Page'}}]},
            'Category': {'select': {'name': 'Prompt Update'}},
            'Impact': {'number': 5}
        }
    )
    print('✓ Created test page successfully!')
    print(f'Page ID: {page["id"]}')
    print()
    print('Properties that worked:')
    for prop_name, prop_value in page['properties'].items():
        print(f'  - {prop_name}: {prop_value.get("type", "unknown")}')

except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()
