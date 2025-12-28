from notion_client import Client
import os
from dotenv import load_dotenv

load_dotenv()

# Use API version 2025-09-03 since that's what we're using for page creation
client = Client(auth=os.getenv('NOTION_API_KEY'), notion_version='2025-09-03')
data_source_id = os.getenv('NOTION_EXTRACTIONS_DATA_SOURCE_ID')

print(f"Creating test page in data source: {data_source_id}")

try:
    page = client.pages.create(
        parent={"type": "data_source_id", "data_source_id": data_source_id},
        properties={
            "Candidate Key": {"title": [{"text": {"content": "TEST - Review Decision Test"}}]},
            "Type": {"select": {"name": "component"}},
            "Status": {"select": {"name": "Pending"}},
            "Review Decision": {"select": {"name": "Approve"}},  # Test the new property
            "Confidence Score": {"number": 0.95},
            "Extraction ID": {"rich_text": [{"text": {"content": "test-123"}}]},
        }
    )
    print('\n✓ Test page created successfully!')
    print(f'Page ID: {page["id"]}')
    print('\nThis means the Review Decision property CAN be set on pages.')

except Exception as e:
    print(f'\n❌ Error creating page: {e}')
    if 'Review Decision is not a property' in str(e):
        print('\nThe property does not exist in the database schema.')
    import traceback
    traceback.print_exc()
