"""Run database migration using psycopg"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg

# Load environment
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

# Get migration file
migration_file = sys.argv[1] if len(sys.argv) > 1 else '002_create_urls_to_process.sql'
migration_path = Path(__file__).parent / migration_file

if not migration_path.exists():
    print(f"Migration file not found: {migration_path}")
    sys.exit(1)

# Read migration SQL
with open(migration_path, 'r') as f:
    sql = f.read()

# Connect and execute
db_url = os.environ.get('NEON_DATABASE_URL')
if not db_url:
    print("NEON_DATABASE_URL not set")
    sys.exit(1)

print(f"Running migration: {migration_file}")
print(f"Database: {db_url.split('@')[1] if '@' in db_url else 'unknown'}")

conn = psycopg.connect(db_url)
with conn.cursor() as cur:
    cur.execute(sql)
    conn.commit()

print("Migration complete")
conn.close()
