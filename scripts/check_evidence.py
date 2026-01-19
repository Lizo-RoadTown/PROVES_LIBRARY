"""Quick script to check evidence in snapshot."""
import os
import psycopg
import json
import re
from dotenv import load_dotenv
from pathlib import Path

project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

db_url = os.environ.get('DIRECT_URL') or os.environ.get('DATABASE_URL')
conn = psycopg.connect(db_url)

# Get the snapshot content
with conn.cursor() as cur:
    cur.execute('''
        SELECT payload
        FROM raw_snapshots
        WHERE id = 'd7b48c36-1816-4d47-8964-7db6ce0477bb'::uuid
    ''')
    row = cur.fetchone()

payload_content = row[0].get('content', '')

# Strip HTML (same as validator does)
payload_stripped = re.sub(r'<script[^>]*>.*?</script>', '', payload_content, flags=re.DOTALL)
payload_stripped = re.sub(r'<style[^>]*>.*?</style>', '', payload_stripped, flags=re.DOTALL)
payload_stripped = re.sub(r'<[^>]+>', ' ', payload_stripped)
payload_stripped = re.sub(r'\s+', ' ', payload_stripped).strip()

# Search for key phrases
search_phrases = [
    'configureTopology',
    'RateGroup',
    'The subtopology function should accept',
    'namespace collision',
    'intentionally-empty',
    'empty file tells CMake',
]

print('Searching for key phrases in stripped content:\n')
for phrase in search_phrases:
    if phrase in payload_stripped:
        idx = payload_stripped.find(phrase)
        print(f'[OK] Found: "{phrase}"')
        context = payload_stripped[max(0,idx-30):idx+len(phrase)+70]
        safe_context = context.encode('ascii', 'replace').decode('ascii')
        print(f'    Context: ...{safe_context}...\n')
    else:
        print(f'[X] NOT found: "{phrase}"\n')

# Now check what the full stripped content contains about CMake
print('\n' + '='*60)
print('Searching for CMake references:')
cmake_idx = payload_stripped.lower().find('cmake')
if cmake_idx >= 0:
    # Use ascii encoding to avoid Windows console issues
    context = payload_stripped[cmake_idx-50:cmake_idx+300]
    safe_context = context.encode('ascii', 'replace').decode('ascii')
    print(f'Found CMake at index {cmake_idx}:')
    print(safe_context)

# Also search for "empty file"
print('\n' + '='*60)
print('Searching for "empty file" phrase:')
empty_idx = payload_stripped.lower().find('empty file')
if empty_idx >= 0:
    context = payload_stripped[empty_idx-50:empty_idx+300]
    safe_context = context.encode('ascii', 'replace').decode('ascii')
    print(f'Found at index {empty_idx}:')
    print(safe_context)

conn.close()
