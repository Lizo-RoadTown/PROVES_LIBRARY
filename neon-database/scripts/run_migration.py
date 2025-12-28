#!/usr/bin/env python3
"""
Run a database migration file
"""
import os
import sys
import psycopg
from dotenv import load_dotenv
from pathlib import Path

# Load .env from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

DATABASE_URL = os.getenv('NEON_DATABASE_URL')

if len(sys.argv) < 2:
    print("Usage: python run_migration.py <migration_file>")
    sys.exit(1)

migration_file = sys.argv[1]

if not os.path.exists(migration_file):
    print(f"Error: Migration file not found: {migration_file}")
    sys.exit(1)

print(f"Running migration: {migration_file}")
print("=" * 80)

with open(migration_file, 'r', encoding='utf-8') as f:
    migration_sql = f.read()

try:
    conn = psycopg.connect(DATABASE_URL)
    with conn.cursor() as cur:
        cur.execute(migration_sql)
    conn.commit()
    conn.close()
    print("✓ Migration completed successfully")
except Exception as e:
    print(f"✗ Migration failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
