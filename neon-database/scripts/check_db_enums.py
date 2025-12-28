#!/usr/bin/env python3
"""Query Neon database to check actual enum definitions"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
db_url = os.getenv('NEON_DATABASE_URL')

conn = psycopg2.connect(db_url)
cur = conn.cursor()

# Get all enum types and their values
cur.execute("""
    SELECT t.typname as enum_name,
           array_agg(e.enumlabel ORDER BY e.enumsortorder) as enum_values
    FROM pg_type t
    JOIN pg_enum e ON t.oid = e.enumtypid
    JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'public'
    GROUP BY t.typname
    ORDER BY t.typname;
""")

results = cur.fetchall()

print("=" * 80)
print("ACTUAL ENUMS IN NEON DATABASE")
print("=" * 80)

for enum_name, enum_values in results:
    print(f"\n{enum_name}:")
    for val in enum_values:
        print(f"  - {val}")

print("\n" + "=" * 80)
print(f"Total enums found: {len(results)}")
print("=" * 80)

cur.close()
conn.close()
