"""
Export Neon database schema and data using Python (no pg_dump needed)
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def export_database():
    """Export schema and data from Neon"""

    neon_url = os.getenv('NEON_DATABASE_URL')
    output_file = 'proves_export.sql'

    print(f"Connecting to Neon database...")

    try:
        # Connect to Neon
        conn = psycopg2.connect(neon_url)
        cur = conn.cursor()

        with open(output_file, 'w', encoding='utf-8') as f:
            # Export schema
            print("Exporting schema...")
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)

            tables = [row[0] for row in cur.fetchall()]
            print(f"Found {len(tables)} tables")

            # Get CREATE statements for each table
            for table in tables:
                print(f"  Exporting table: {table}")

                # Get table definition
                cur.execute(f"""
                    SELECT
                        'CREATE TABLE ' || quote_ident(table_name) || ' (' ||
                        string_agg(
                            quote_ident(column_name) || ' ' || data_type ||
                            CASE WHEN character_maximum_length IS NOT NULL
                                THEN '(' || character_maximum_length || ')'
                                ELSE ''
                            END ||
                            CASE WHEN is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END,
                            ', '
                        ) || ');'
                    FROM information_schema.columns
                    WHERE table_name = %s
                    GROUP BY table_name
                """, (table,))

                create_stmt = cur.fetchone()
                if create_stmt:
                    f.write(f"\n-- Table: {table}\n")
                    f.write(create_stmt[0] + "\n\n")

                # Export data
                cur.execute(f"SELECT * FROM {table}")
                rows = cur.fetchall()

                if rows:
                    cur.execute(f"""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = %s
                        ORDER BY ordinal_position
                    """, (table,))
                    columns = [row[0] for row in cur.fetchall()]

                    f.write(f"-- Data for {table} ({len(rows)} rows)\n")
                    for row in rows:
                        values = []
                        for val in row:
                            if val is None:
                                values.append('NULL')
                            elif isinstance(val, str):
                                values.append(f"'{val.replace(\"'\", \"''\")}'")
                            else:
                                values.append(str(val))

                        f.write(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)});\n")
                    f.write("\n")

        print(f"\n✓ Export complete: {output_file}")
        print(f"  Size: {os.path.getsize(output_file) / 1024:.2f} KB")

    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    return True

if __name__ == "__main__":
    export_database()
