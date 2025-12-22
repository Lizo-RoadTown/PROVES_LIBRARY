"""
Apply the findings table migration to Neon database.
"""
import os
from dotenv import load_dotenv
import psycopg

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
db_url = os.environ.get('NEON_DATABASE_URL')

if not db_url:
    print("ERROR: NEON_DATABASE_URL not set in .env")
    exit(1)

# Read the migration
migration_path = os.path.join(
    os.path.dirname(__file__), 
    '..', 
    'archive', 
    'design-docs', 
    'mcp-server', 
    'schema', 
    '03_findings_table.sql'
)

with open(migration_path, 'r') as f:
    sql = f.read()

print("Applying findings migration to Neon...")
print(f"Database: {db_url.split('@')[1].split('/')[0] if '@' in db_url else 'unknown'}")

# Apply to Neon
try:
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        print("Migration applied successfully!")
        
        # Verify tables created
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('findings', 'equivalences', 'crawled_sources')
                ORDER BY table_name
            """)
            tables = [r[0] for r in cur.fetchall()]
            print(f"New tables created: {tables}")
            
            # Count columns in findings table
            cur.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'findings'
            """)
            columns = [r[0] for r in cur.fetchall()]
            print(f"Findings table has {len(columns)} columns")
            
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
