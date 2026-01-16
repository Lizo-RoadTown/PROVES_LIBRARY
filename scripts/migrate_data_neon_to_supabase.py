"""
Migrate DATA from Neon to Supabase (respecting foreign key constraints)

This script migrates data in the correct order to avoid FK violations:
1. raw_snapshots (no dependencies)
2. staging_extractions (depends on raw_snapshots)
3. human_decisions (depends on staging_extractions)

Usage:
    python scripts/migrate_data_neon_to_supabase.py
"""

import os
import sys
from pathlib import Path

# Ensure we can import psycopg2
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("Installing psycopg2-binary...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2
    from psycopg2.extras import RealDictCursor

from dotenv import load_dotenv

# Load environment
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

# Connection strings
NEON_URL = "postgresql://neondb_owner:npg_GvP5x0yVrCLm@ep-empty-morning-af4l9ocx-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require"
SUPABASE_URL = os.getenv('DIRECT_URL', '').replace('?pgbouncer=true', '')

def get_neon_connection():
    """Connect to Neon database"""
    return psycopg2.connect(NEON_URL)

def get_supabase_connection():
    """Connect to Supabase database"""
    return psycopg2.connect(SUPABASE_URL)

def count_rows(conn, table):
    """Count rows in a table"""
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        return cur.fetchone()[0]

def get_table_columns(conn, table):
    """Get column names for a table"""
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table,))
        return [row[0] for row in cur.fetchall()]

def migrate_table(neon_conn, supabase_conn, table_name, batch_size=100):
    """Migrate a single table from Neon to Supabase"""
    print(f"\n📦 Migrating {table_name}...")

    # Get row counts
    neon_count = count_rows(neon_conn, table_name)
    supabase_count_before = count_rows(supabase_conn, table_name)

    print(f"   Neon rows: {neon_count}")
    print(f"   Supabase rows (before): {supabase_count_before}")

    if neon_count == 0:
        print(f"   ⚠️  No data to migrate")
        return 0

    if supabase_count_before >= neon_count:
        print(f"   ✓ Already migrated (Supabase has {supabase_count_before} rows)")
        return 0

    # Get columns
    columns = get_table_columns(neon_conn, table_name)
    columns_str = ', '.join(f'"{c}"' for c in columns)
    placeholders = ', '.join(['%s'] * len(columns))

    # Read all data from Neon
    with neon_conn.cursor(cursor_factory=RealDictCursor) as neon_cur:
        neon_cur.execute(f'SELECT {columns_str} FROM {table_name}')
        rows = neon_cur.fetchall()

    # Insert into Supabase
    inserted = 0
    errors = 0

    with supabase_conn.cursor() as supabase_cur:
        for row in rows:
            try:
                values = [row[col] for col in columns]
                supabase_cur.execute(
                    f'INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING',
                    values
                )
                inserted += 1
            except Exception as e:
                errors += 1
                if errors <= 3:  # Only show first 3 errors
                    print(f"   ❌ Error: {e}")

        supabase_conn.commit()

    supabase_count_after = count_rows(supabase_conn, table_name)
    print(f"   Supabase rows (after): {supabase_count_after}")
    print(f"   Inserted: {inserted}, Errors: {errors}")

    return inserted

def main():
    print("=" * 60)
    print("  PROVES Data Migration: Neon → Supabase")
    print("=" * 60)

    if not SUPABASE_URL or '[YOUR-PASSWORD]' in SUPABASE_URL:
        print("❌ DIRECT_URL not properly configured in .env")
        return 1

    print(f"\nNeon: {NEON_URL.split('@')[1].split('/')[0]}")
    print(f"Supabase: {SUPABASE_URL.split('@')[1].split('/')[0]}")

    try:
        neon_conn = get_neon_connection()
        print("✓ Connected to Neon")
    except Exception as e:
        print(f"❌ Failed to connect to Neon: {e}")
        return 1

    try:
        supabase_conn = get_supabase_connection()
        print("✓ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return 1

    # Migration order (respecting foreign keys)
    tables_to_migrate = [
        'raw_snapshots',           # No FK dependencies
        'staging_extractions',     # Depends on raw_snapshots
        'human_decisions',         # Depends on staging_extractions
        'pipeline_runs',           # Independent
    ]

    total_inserted = 0

    for table in tables_to_migrate:
        try:
            # Check if table exists
            with neon_conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = %s
                    )
                """, (table,))
                exists = cur.fetchone()[0]

            if exists:
                inserted = migrate_table(neon_conn, supabase_conn, table)
                total_inserted += inserted
            else:
                print(f"\n⚠️  Table {table} does not exist in Neon")

        except Exception as e:
            print(f"\n❌ Error migrating {table}: {e}")

    # Close connections
    neon_conn.close()
    supabase_conn.close()

    print("\n" + "=" * 60)
    print(f"  ✓ Migration Complete! Total rows inserted: {total_inserted}")
    print("=" * 60)

    return 0

if __name__ == "__main__":
    sys.exit(main())
