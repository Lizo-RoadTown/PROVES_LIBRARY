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
    schema_dir = Path(__file__).parent.parent / 'archive' / 'design-docs' / 'mcp-server' / 'schema'
    schema_files = [
        '00_initial_schema.sql',
        '01_seed_data.sql',
        '02_training_data.sql'  # Training data collection for local LLM fine-tuning
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
                error_str = str(e).lower()
                # Skip "already exists" errors - these are fine for incremental migrations
                if 'already exists' in error_str:
                    print(f"[SKIP] {schema_file} - objects already exist (this is OK)")
                    conn.rollback()
                    continue
                else:
                    print(f"[ERROR] Error applying {schema_file}: {e}")
                    conn.rollback()
                    raise

        # Verify schema by checking statistics
        print(f"\n[*] Database Statistics:")
        try:
            cur.execute("SELECT * FROM database_statistics ORDER BY table_name")
            stats = cur.fetchall()
            for table_name, row_count in stats:
                print(f"  {table_name}: {row_count} rows")
        except Exception as e:
            print(f"  (Could not fetch stats: {e})")

        # Check training data tables
        print(f"\n[*] Training Data Tables:")
        try:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'training_%'
                ORDER BY table_name
            """)
            training_tables = cur.fetchall()
            if training_tables:
                for (table_name,) in training_tables:
                    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cur.fetchone()[0]
                    print(f"  {table_name}: {count} rows")
            else:
                print("  (No training tables found)")
        except Exception as e:
            print(f"  (Could not check training tables: {e})")

        cur.close()
        conn.close()

        print(f"\n[OK] Schema migration complete!")
        print(f"\nNext steps:")
        print(f"  1. Run: python scripts/index_library.py")
        print(f"  2. Test queries with graph_manager.py")
        print(f"  3. Run curator agent to collect training data")

    except psycopg2.Error as e:
        print(f"\n[ERROR] Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    apply_schema()
