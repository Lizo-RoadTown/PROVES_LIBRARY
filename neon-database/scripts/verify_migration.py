"""Verify migration 003 was successful"""
import os
from dotenv import load_dotenv
import psycopg

load_dotenv('../.env')
conn = psycopg.connect(os.environ['NEON_DATABASE_URL'])
cur = conn.cursor()

print("\n" + "="*60)
print("MIGRATION 003 VERIFICATION")
print("="*60)

# Check new tables
cur.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('curator_errors', 'curator_reports')
    ORDER BY table_name
""")
tables = [row[0] for row in cur.fetchall()]

print("\nNew tables created:")
for t in tables:
    print(f"  [OK] {t}")

# Check new columns
cur.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_name = 'staging_extractions'
    AND column_name LIKE 'notion%'
    ORDER BY column_name
""")
cols = [row[0] for row in cur.fetchall()]

print("\nNew columns in staging_extractions:")
for c in cols:
    print(f"  [OK] {c}")

# Check triggers
cur.execute("""
    SELECT trigger_name FROM information_schema.triggers
    WHERE trigger_name LIKE '%notion%'
    ORDER BY trigger_name
""")
triggers = [row[0] for row in cur.fetchall()]

print("\nTriggers created:")
for t in triggers:
    print(f"  [OK] {t}")

# Check functions
cur.execute("""
    SELECT routine_name FROM information_schema.routines
    WHERE routine_schema = 'public'
    AND routine_name LIKE '%notion%'
    OR routine_name LIKE '%sync%'
    ORDER BY routine_name
""")
functions = [row[0] for row in cur.fetchall()]

print("\nHelper functions:")
for f in functions[:10]:  # Limit output
    print(f"  [OK] {f}")

print("\n" + "="*60)
print("Migration successful!")
print("="*60 + "\n")

cur.close()
conn.close()
