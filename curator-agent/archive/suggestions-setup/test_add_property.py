from notion_client import Client
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = Client(auth=os.getenv('NOTION_API_KEY'), notion_version='2022-06-28')
db_id = os.getenv('NOTION_EXTRACTIONS_DB_ID')

print(f"Updating database: {db_id}")

try:
    result = client.databases.update(
        database_id=db_id,
        properties={
            'Review Decision': {
                'select': {
                    'options': [
                        {'name': 'Approve', 'color': 'green'},
                        {'name': 'Reject', 'color': 'red'}
                    ]
                }
            }
        }
    )
    print('\n✓ Update successful!')
    print('\nProperties in result:')
    for prop_name in sorted(result.get('properties', {}).keys()):
        print(f'  - {prop_name}')

except Exception as e:
    print(f'\n❌ Error: {e}')
    import traceback
    traceback.print_exc()
