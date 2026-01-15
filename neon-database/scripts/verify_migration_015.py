#!/usr/bin/env python3
"""Verify migration 015 was applied successfully."""

import os
import sys
from pathlib import Path
import psycopg
from dotenv import load_dotenv

# Load environment
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / '.env')

DATABASE_URL = os.getenv('NEON_DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: NEON_DATABASE_URL not found in .env")
    sys.exit(1)

try:
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            print("Verifying Migration 015: Standard Mapping Enrichment")
            print("=" * 60)

            # Check columns
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'knowledge_enrichment'
                  AND column_name IN ('standard', 'standard_version', 'standard_key', 'standard_name', 'standard_constraints')
                ORDER BY column_name
            """)
            columns = cur.fetchall()

            print("\nColumns added to knowledge_enrichment:")
            if columns:
                for col in columns:
                    print(f"  - {col[0]} ({col[1]})")
            else:
                print("  [ERROR] No columns found!")

            # Check views
            cur.execute("""
                SELECT viewname
                FROM pg_views
                WHERE viewname IN ('xtce_mappings', 'standard_mappings')
                ORDER BY viewname
            """)
            views = cur.fetchall()

            print("\nViews created:")
            if views:
                for view in views:
                    print(f"  - {view[0]}")
            else:
                print("  [ERROR] No views found!")

            # Check function
            cur.execute("""
                SELECT proname
                FROM pg_proc
                WHERE proname = 'add_standard_mapping'
            """)
            funcs = cur.fetchall()

            print("\nFunctions created:")
            if funcs:
                for func in funcs:
                    print(f"  - {func[0]}()")
            else:
                print("  [ERROR] Function not found!")

            # Check constraint
            cur.execute("""
                SELECT conname
                FROM pg_constraint
                WHERE conname IN ('knowledge_enrichment_enrichment_type_check', 'check_standard_mapping_fields')
                  AND conrelid = 'knowledge_enrichment'::regclass
            """)
            constraints = cur.fetchall()

            print("\nConstraints:")
            if constraints:
                for cons in constraints:
                    print(f"  - {cons[0]}")
            else:
                print("  [ERROR] Constraints not found!")

            print("\n" + "=" * 60)
            if len(columns) == 5 and len(views) == 2 and len(funcs) == 1:
                print("SUCCESS: Migration 015 applied successfully!")
            else:
                print("WARNING: Migration may be incomplete")

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
