"""Check the auth flow setup - sandbox mode, users, org memberships."""
import os
import psycopg
from dotenv import load_dotenv
from pathlib import Path

project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

db_url = os.environ.get('DIRECT_URL') or os.environ.get('DATABASE_URL')
if db_url and 'pgbouncer' in db_url:
    db_url = db_url.split('?')[0]

conn = psycopg.connect(db_url)

print("=" * 60)
print("AUTH FLOW CHECK")
print("=" * 60)

# Check sandbox mode
with conn.cursor() as cur:
    cur.execute("SELECT value FROM app_settings WHERE key = 'sandbox_mode'")
    row = cur.fetchone()
    sandbox_mode = row[0] if row else 'NOT SET'
    print(f"\nSandbox mode: {sandbox_mode}")

# Check users
with conn.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM auth.users")
    user_count = cur.fetchone()[0]
    print(f"Total users in auth.users: {user_count}")

# Check user profiles
with conn.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM user_profiles")
    profile_count = cur.fetchone()[0]
    print(f"Total user_profiles: {profile_count}")

# Check users with active_org_id set
with conn.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM user_profiles WHERE active_org_id IS NOT NULL")
    active_org_count = cur.fetchone()[0]
    print(f"Users with active_org_id set: {active_org_count}")

# Check organizations
with conn.cursor() as cur:
    cur.execute("SELECT id, name, slug FROM organizations WHERE is_active = true ORDER BY name")
    orgs = cur.fetchall()
    print(f"\nActive organizations ({len(orgs)}):")
    for org in orgs:
        print(f"  - {org[1]} (slug: {org[2]})")

# Check organization memberships
with conn.cursor() as cur:
    cur.execute("""
        SELECT o.name, COUNT(om.user_id) as member_count
        FROM organizations o
        LEFT JOIN organization_members om ON o.id = om.organization_id
        WHERE o.is_active = true
        GROUP BY o.id, o.name
        ORDER BY o.name
    """)
    memberships = cur.fetchall()
    print(f"\nOrganization membership counts:")
    for m in memberships:
        print(f"  - {m[0]}: {m[1]} members")

# Check trigger exists
with conn.cursor() as cur:
    cur.execute("""
        SELECT tgname, tgtype, proname
        FROM pg_trigger t
        JOIN pg_proc p ON t.tgfoid = p.oid
        WHERE t.tgrelid = 'auth.users'::regclass
    """)
    triggers = cur.fetchall()
    print(f"\nTriggers on auth.users:")
    for t in triggers:
        print(f"  - {t[0]} -> {t[2]}()")

print("\n" + "=" * 60)
print("RLS STATUS CHECK")
print("=" * 60)

# Check RLS enabled tables
with conn.cursor() as cur:
    cur.execute("""
        SELECT relname, relrowsecurity, relforcerowsecurity
        FROM pg_class
        WHERE relnamespace = 'public'::regnamespace
        AND relkind = 'r'
        AND relrowsecurity = true
        ORDER BY relname
    """)
    rls_tables = cur.fetchall()
    print(f"\nTables with RLS enabled ({len(rls_tables)}):")
    for t in rls_tables:
        force_str = " (force)" if t[2] else ""
        print(f"  - {t[0]}{force_str}")

conn.close()
