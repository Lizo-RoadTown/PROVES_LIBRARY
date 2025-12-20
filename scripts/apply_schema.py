#!/usr/bin/env python3
"""
Apply database schema to Neon PostgreSQL
"""
import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_schema():
    """Apply all schema files in order"""

    # Get database URL from environment
    db_url = os.getenv('NEON_DATABASE_URL')
    if not db_url:
        print("Error: NEON_DATABASE_URL not found in .env file")
        print("Please add your Neon connection string to .env")
        sys.exit(1)

    # Schema files in order
    schema_dir = Path(__file__).parent.parent / 'mcp-server' / 'schema'
    schema_files = [
        '00_initial_schema.sql',
        '01_seed_data.sql'
    ]

    print(f"Connecting to Neon database...")
    print(f"Database: {db_url.split('@')[1].split('/')[0]}")  # Show host without credentials

    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cur = conn.cursor()

        print(f"\nApplying schema files...")

        for schema_file in schema_files:
            file_path = schema_dir / schema_file

            if not file_path.exists():
                print(f"Warning: {schema_file} not found, skipping")
                continue

            print(f"\n[*] Applying {schema_file}...")

            with open(file_path, 'r') as f:
                sql = f.read()

            try:
                cur.execute(sql)
                conn.commit()
                print(f"[OK] {schema_file} applied successfully")
            except Exception as e:
                print(f"[ERROR] Error applying {schema_file}: {e}")
                conn.rollback()
                raise

        # Verify schema by checking statistics
        print(f"\n[*] Database Statistics:")
        cur.execute("SELECT * FROM database_statistics ORDER BY table_name")
        stats = cur.fetchall()

        for table_name, row_count in stats:
            print(f"  {table_name}: {row_count} rows")

        cur.close()
        conn.close()

        print(f"\n[OK] Schema applied successfully!")
        print(f"\nNext steps:")
        print(f"  1. Run: python scripts/index_library.py")
        print(f"  2. Test queries with graph_manager.py")

    except psycopg2.Error as e:
        print(f"\n[ERROR] Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    apply_schema()
