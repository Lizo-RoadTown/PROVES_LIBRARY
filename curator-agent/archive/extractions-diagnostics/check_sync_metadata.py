"""Check sync_metadata table for Notion integration setup"""
import os
from dotenv import load_dotenv
import psycopg

load_dotenv('../.env')
conn = psycopg.connect(os.environ['NEON_DATABASE_URL'])
cur = conn.cursor()

# Get schema
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'sync_metadata'
    ORDER BY ordinal_position
""")
cols = cur.fetchall()

print('sync_metadata schema:')
for col in cols:
    print(f'  {col[0]}: {col[1]}')

print()

# Get sample data
cur.execute('SELECT * FROM sync_metadata LIMIT 10')
rows = cur.fetchall()

if rows:
    print('Sample data:')
    for row in rows:
        print(f'  {row}')
else:
    print('No data in sync_metadata table')

cur.close()
conn.close()
