"""
Migrate database from Neon to Supabase

This script:
1. Connects to Neon database
2. Exports schema and data
3. Imports to Supabase database

Usage:
    python scripts/migrate_neon_to_supabase.py
"""

import os
import sys
from pathlib import Path
import subprocess
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

def check_pg_dump():
    """Check if pg_dump is installed"""
    try:
        result = subprocess.run(['pg_dump', '--version'], capture_output=True, text=True)
        print(f"✓ PostgreSQL tools found: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("\n❌ PostgreSQL client tools not found!")
        print("\nPlease install PostgreSQL:")
        print("  Windows: https://www.postgresql.org/download/windows/")
        print("  Or use Chocolatey: choco install postgresql")
        print("\nAfter installation, restart your terminal and try again.")
        return False

def export_from_neon():
    """Export database from Neon"""
    neon_url = os.getenv('NEON_DATABASE_URL')
    if not neon_url:
        print("❌ NEON_DATABASE_URL not found in .env")
        return None

    backup_file = project_root / 'proves_neon_backup.sql'

    print(f"\n📦 Exporting from Neon...")
    print(f"   Connection: {neon_url.split('@')[1].split('/')[0]}...")

    try:
        # Export schema and data
        result = subprocess.run(
            ['pg_dump', neon_url, '--file', str(backup_file), '--verbose'],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            print(f"✓ Export complete: {backup_file} ({size_mb:.2f} MB)")
            return backup_file
        else:
            print(f"❌ Export failed: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        print("❌ Export timeout (>5 minutes)")
        return None
    except Exception as e:
        print(f"❌ Export error: {e}")
        return None

def import_to_supabase(backup_file):
    """Import database to Supabase"""
    # Get Supabase connection from .env
    supabase_url = None

    # Try DATABASE_URL first (pooled connection)
    database_url = os.getenv('DATABASE_URL')
    if database_url and '[YOUR-PASSWORD]' not in database_url:
        supabase_url = database_url.replace('?pgbouncer=true', '')

    # Try DIRECT_URL
    if not supabase_url:
        direct_url = os.getenv('DIRECT_URL')
        if direct_url and '[YOUR-PASSWORD]' not in direct_url:
            supabase_url = direct_url

    if not supabase_url:
        print("\n❌ Supabase database URL not configured!")
        print("   Please update DATABASE_URL or DIRECT_URL in .env")
        print("   Replace [YOUR-PASSWORD] with your actual Supabase database password")
        return False

    print(f"\n📥 Importing to Supabase...")
    print(f"   Connection: {supabase_url.split('@')[1].split('/')[0]}...")

    try:
        # Import to Supabase
        result = subprocess.run(
            ['psql', supabase_url, '--file', str(backup_file)],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            print("✓ Import complete!")
            return True
        else:
            print(f"❌ Import failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Import timeout (>5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def verify_migration():
    """Verify migration by counting tables"""
    print("\n🔍 Verifying migration...")

    neon_url = os.getenv('NEON_DATABASE_URL')
    supabase_url = os.getenv('DIRECT_URL', os.getenv('DATABASE_URL', '').replace('?pgbouncer=true', ''))

    if '[YOUR-PASSWORD]' in supabase_url:
        print("⚠️  Cannot verify - Supabase password not configured")
        return

    try:
        # Count tables in Neon
        result_neon = subprocess.run(
            ['psql', neon_url, '-t', '-c',
             "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Count tables in Supabase
        result_supabase = subprocess.run(
            ['psql', supabase_url, '-t', '-c',
             "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"],
            capture_output=True,
            text=True,
            timeout=30
        )

        neon_tables = int(result_neon.stdout.strip())
        supabase_tables = int(result_supabase.stdout.strip())

        print(f"   Neon tables: {neon_tables}")
        print(f"   Supabase tables: {supabase_tables}")

        if neon_tables == supabase_tables:
            print("✓ Migration verified - table counts match!")
        else:
            print("⚠️  Warning: Table counts don't match")

    except Exception as e:
        print(f"⚠️  Could not verify: {e}")

def main():
    print("=" * 60)
    print("  PROVES Database Migration: Neon → Supabase")
    print("=" * 60)

    # Check prerequisites
    if not check_pg_dump():
        return 1

    # Export from Neon
    backup_file = export_from_neon()
    if not backup_file:
        return 1

    # Import to Supabase
    if not import_to_supabase(backup_file):
        return 1

    # Verify
    verify_migration()

    print("\n" + "=" * 60)
    print("  ✓ Migration Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Update NEON_DATABASE_URL in .env to point to Supabase")
    print("     (use DATABASE_URL or DIRECT_URL value)")
    print("  2. Test your application with the new database")
    print("  3. Once verified, you can delete the Neon project")
    print(f"\nBackup saved at: {backup_file}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
