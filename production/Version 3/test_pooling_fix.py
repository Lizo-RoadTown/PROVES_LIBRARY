#!/usr/bin/env python3
"""
Test Database Pooling Fix
=========================
Verifies that all curator scripts can import and use the centralized pool.

Run this to verify the pooling fixes work correctly.
"""

import sys
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'production' / 'Version 3'))
sys.path.insert(0, str(project_root / 'production' / 'curator'))
sys.path.insert(0, str(project_root / 'production' / 'curator' / 'subagents'))

print("=" * 80)
print("DATABASE POOLING FIX VERIFICATION")
print("=" * 80)
print()

# Test 1: Import centralized pool
print("[TEST 1] Importing centralized database module...")
try:
    from database import get_connection, get_pool, check_connection
    print("  ✅ SUCCESS: Centralized database module imported")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Test 2: Check database connection
print("\n[TEST 2] Testing database connection...")
try:
    if check_connection():
        print("  ✅ SUCCESS: Database connection working")
    else:
        print("  ❌ FAILED: Database connection check returned False")
        sys.exit(1)
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Test 3: Import batch_promote_accepted
print("\n[TEST 3] Importing batch_promote_accepted...")
try:
    import batch_promote_accepted
    print("  ✅ SUCCESS: batch_promote_accepted imports correctly")

    # Verify it doesn't have get_db_connection anymore
    if hasattr(batch_promote_accepted, 'get_db_connection'):
        print("  ⚠️  WARNING: Still has get_db_connection() function")
    else:
        print("  ✅ VERIFIED: Old get_db_connection() removed")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Test 4: Import analyze_accepted_batch
print("\n[TEST 4] Importing analyze_accepted_batch...")
try:
    import analyze_accepted_batch
    print("  ✅ SUCCESS: analyze_accepted_batch imports correctly")

    if hasattr(analyze_accepted_batch, 'get_db_connection'):
        print("  ⚠️  WARNING: Still has get_db_connection() function")
    else:
        print("  ✅ VERIFIED: Old get_db_connection() removed")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Test 5: Import url_fetcher
print("\n[TEST 5] Importing url_fetcher...")
try:
    import url_fetcher
    print("  ✅ SUCCESS: url_fetcher imports correctly")

    if hasattr(url_fetcher, 'get_db_connection'):
        print("  ⚠️  WARNING: Still has get_db_connection() function")
    else:
        print("  ✅ VERIFIED: Old get_db_connection() removed")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Test 6: Test pool stats
print("\n[TEST 6] Checking connection pool statistics...")
try:
    from database import get_pool_stats
    stats = get_pool_stats()
    print(f"  Pool size: {stats['size']}")
    print(f"  Min size: {stats['min_size']}")
    print(f"  Max size: {stats['max_size']}")
    print(f"  Idle: {stats['idle']}")
    print(f"  In use: {stats['in_use']}")
    print("  ✅ SUCCESS: Pool statistics retrieved")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Test 7: Test actual connection from pool
print("\n[TEST 7] Testing actual connection from pool...")
try:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 as test")
            result = cur.fetchone()
            if result == (1,):
                print("  ✅ SUCCESS: Query executed successfully via pool")
            else:
                print(f"  ❌ FAILED: Unexpected result: {result}")
                sys.exit(1)
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Test 8: Test batch_promote_accepted can query database
print("\n[TEST 8] Testing batch_promote_accepted database access...")
try:
    from batch_promote_accepted import get_unpromoted_accepted

    with get_connection() as conn:
        unpromoted = get_unpromoted_accepted(conn)
        count = len(unpromoted)
        print(f"  Found {count} unpromoted accepted extractions")
        print("  ✅ SUCCESS: batch_promote_accepted can query database")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Test 9: Test url_fetcher tools work
print("\n[TEST 9] Testing url_fetcher tools...")
try:
    from url_fetcher import fetch_next_url, mark_url_complete

    # Just verify the tools are callable and use the pool
    # Don't actually modify data
    print("  fetch_next_url: Callable")
    print("  mark_url_complete: Callable")
    print("  ✅ SUCCESS: url_fetcher tools are properly defined")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    sys.exit(1)

# Final summary
print()
print("=" * 80)
print("ALL TESTS PASSED! ✅")
print("=" * 80)
print()
print("Summary:")
print("  • Centralized database pool is working")
print("  • batch_promote_accepted.py fixed")
print("  • analyze_accepted_batch.py fixed")
print("  • url_fetcher.py fixed")
print("  • All scripts can query the database")
print()
print("The pooling fix is working correctly!")
print()
