#!/usr/bin/env python3
"""Test error logging workflow"""
import os
import psycopg
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from src.curator.error_logger import ErrorLogger

# Create a test extraction record if needed
db_url = os.getenv('NEON_DATABASE_URL')

print("=" * 80)
print("TEST: Error Logging Workflow")
print("=" * 80)
print()

# Get or create a test extraction
conn = psycopg.connect(db_url)
with conn.cursor() as cur:
    # Find an existing extraction or create a dummy one
    cur.execute("""
        SELECT extraction_id, candidate_key
        FROM staging_extractions
        LIMIT 1
    """)
    result = cur.fetchone()

if result:
    test_extraction_id, candidate_key = result
    print(f"Using existing extraction: {test_extraction_id}")
    print(f"Candidate: {candidate_key}")
else:
    print("No extractions found. Please run the extractor first.")
    exit(1)

conn.close()

# Test error logging
print()
print("Step 1: Logging a test error...")
logger = ErrorLogger()

try:
    # Simulate an error
    raise ValueError("This is a test error for demonstration purposes")
except Exception as e:
    error_msg, stack_trace = ErrorLogger.capture_exception(e)

    success = logger.log_to_extraction(
        extraction_id=test_extraction_id,
        error_type='api_timeout',
        error_message=error_msg,
        stack_trace=stack_trace,
        context={
            'test': True,
            'url': 'https://github.com/test/repo',
            'ecosystem': 'fprime'
        }
    )

    if success:
        print("✓ Error logged successfully")
    else:
        print("✗ Failed to log error")

# Check the error was logged
print()
print("Step 2: Verifying error in database...")
conn = psycopg.connect(db_url)
with conn.cursor() as cur:
    cur.execute("""
        SELECT error_count, last_error_at, error_log
        FROM staging_extractions
        WHERE extraction_id = %s::uuid
    """, (test_extraction_id,))

    error_count, last_error_at, error_log = cur.fetchone()
    print(f"  Error count: {error_count}")
    print(f"  Last error at: {last_error_at}")
    print(f"  Errors in log: {len(error_log) if error_log else 0}")

conn.close()

print()
print("Step 3: Sync error to Notion...")
print("Run: python -X utf8 sync_errors_to_notion.py 1")
print()
print("✓ Test complete!")
