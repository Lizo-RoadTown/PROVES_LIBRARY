/**
 * Full Neon to Supabase Migration
 *
 * Exports EVERYTHING from Neon and imports to Supabase exactly as-is.
 * Handles schema (tables, indexes, constraints) and all data.
 */

const { Client } = require('pg');
require('dotenv').config();

// Connection strings
const NEON_URL = "postgresql://neondb_owner:npg_GvP5x0yVrCLm@ep-empty-morning-af4l9ocx-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require";
const SUPABASE_URL = process.env.DIRECT_URL?.replace('?pgbouncer=true', '') || '';

async function getTableDependencyOrder(client) {
  // Get tables ordered by foreign key dependencies
  const result = await client.query(`
    WITH RECURSIVE table_deps AS (
      -- Base: tables with no foreign keys
      SELECT
        c.relname as table_name,
        0 as depth
      FROM pg_class c
      JOIN pg_namespace n ON n.oid = c.relnamespace
      WHERE c.relkind = 'r'
        AND n.nspname = 'public'
        AND NOT EXISTS (
          SELECT 1 FROM pg_constraint con
          WHERE con.conrelid = c.oid AND con.contype = 'f'
        )

      UNION ALL

      -- Recursive: tables that depend on already-included tables
      SELECT
        c.relname,
        td.depth + 1
      FROM pg_class c
      JOIN pg_namespace n ON n.oid = c.relnamespace
      JOIN pg_constraint con ON con.conrelid = c.oid
      JOIN pg_class ref ON ref.oid = con.confrelid
      JOIN table_deps td ON td.table_name = ref.relname
      WHERE c.relkind = 'r'
        AND n.nspname = 'public'
        AND con.contype = 'f'
    )
    SELECT DISTINCT table_name, MAX(depth) as depth
    FROM table_deps
    GROUP BY table_name
    ORDER BY depth, table_name;
  `);

  return result.rows.map(r => r.table_name);
}

async function getAllTables(client) {
  const result = await client.query(`
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_type = 'BASE TABLE'
    ORDER BY table_name
  `);
  return result.rows.map(r => r.table_name);
}

async function getTableSchema(client, tableName) {
  // Get column definitions
  const columns = await client.query(`
    SELECT
      column_name,
      data_type,
      udt_name,
      character_maximum_length,
      numeric_precision,
      numeric_scale,
      is_nullable,
      column_default
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = $1
    ORDER BY ordinal_position
  `, [tableName]);

  return columns.rows;
}

async function getEnums(client) {
  const result = await client.query(`
    SELECT
      t.typname as enum_name,
      array_agg(e.enumlabel ORDER BY e.enumsortorder) as enum_values
    FROM pg_type t
    JOIN pg_enum e ON t.oid = e.enumtypid
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'public'
    GROUP BY t.typname
  `);
  return result.rows;
}

async function getIndexes(client, tableName) {
  const result = await client.query(`
    SELECT indexdef
    FROM pg_indexes
    WHERE schemaname = 'public'
      AND tablename = $1
      AND indexname NOT LIKE '%_pkey'
  `, [tableName]);
  return result.rows.map(r => r.indexdef);
}

async function getForeignKeys(client, tableName) {
  const result = await client.query(`
    SELECT
      con.conname as constraint_name,
      a.attname as column_name,
      ref_cl.relname as ref_table,
      ref_a.attname as ref_column
    FROM pg_constraint con
    JOIN pg_class cl ON cl.oid = con.conrelid
    JOIN pg_namespace n ON n.oid = cl.relnamespace
    JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = ANY(con.conkey)
    JOIN pg_class ref_cl ON ref_cl.oid = con.confrelid
    JOIN pg_attribute ref_a ON ref_a.attrelid = con.confrelid AND ref_a.attnum = ANY(con.confkey)
    WHERE con.contype = 'f'
      AND n.nspname = 'public'
      AND cl.relname = $1
  `, [tableName]);
  return result.rows;
}

async function getTableData(client, tableName) {
  const result = await client.query(`SELECT * FROM "${tableName}"`);
  return result.rows;
}

function formatValue(val, dataType) {
  if (val === null) return 'NULL';
  if (typeof val === 'boolean') return val ? 'TRUE' : 'FALSE';
  if (typeof val === 'number') return String(val);
  if (val instanceof Date) return `'${val.toISOString()}'`;
  if (typeof val === 'object') return `'${JSON.stringify(val).replace(/'/g, "''")}'::jsonb`;
  // String - escape single quotes
  return `'${String(val).replace(/'/g, "''")}'`;
}

async function main() {
  console.log('='.repeat(60));
  console.log('  FULL Neon → Supabase Migration');
  console.log('='.repeat(60));

  if (!SUPABASE_URL) {
    console.error('❌ DIRECT_URL not set in .env');
    process.exit(1);
  }

  const neon = new Client({ connectionString: NEON_URL });
  const supabase = new Client({ connectionString: SUPABASE_URL });

  try {
    await neon.connect();
    console.log('✓ Connected to Neon');

    await supabase.connect();
    console.log('✓ Connected to Supabase');

    // Step 1: Drop all existing tables in Supabase (reverse order)
    console.log('\n📦 Dropping existing Supabase tables...');
    const existingTables = await getAllTables(supabase);

    // Disable FK checks temporarily
    await supabase.query('SET session_replication_role = replica;');

    for (const table of existingTables.reverse()) {
      try {
        await supabase.query(`DROP TABLE IF EXISTS "${table}" CASCADE`);
        console.log(`   Dropped: ${table}`);
      } catch (e) {
        console.log(`   Warning dropping ${table}: ${e.message}`);
      }
    }

    // Step 2: Drop and recreate enums
    console.log('\n📦 Migrating enums...');
    const enums = await getEnums(neon);

    for (const enumDef of enums) {
      try {
        await supabase.query(`DROP TYPE IF EXISTS "${enumDef.enum_name}" CASCADE`);
        const values = enumDef.enum_values.map(v => `'${v}'`).join(', ');
        await supabase.query(`CREATE TYPE "${enumDef.enum_name}" AS ENUM (${values})`);
        console.log(`   Created enum: ${enumDef.enum_name}`);
      } catch (e) {
        console.log(`   Warning with enum ${enumDef.enum_name}: ${e.message}`);
      }
    }

    // Step 3: Get table creation order (respecting FKs)
    console.log('\n📦 Getting table dependency order...');
    const allNeonTables = await getAllTables(neon);
    let orderedTables;
    try {
      orderedTables = await getTableDependencyOrder(neon);
      // Add any tables not in the dependency order
      for (const t of allNeonTables) {
        if (!orderedTables.includes(t)) {
          orderedTables.push(t);
        }
      }
    } catch (e) {
      orderedTables = allNeonTables;
    }
    console.log(`   Tables to migrate: ${orderedTables.join(', ')}`);

    // Step 4: Create tables and insert data
    console.log('\n📦 Creating tables and copying data...');

    // Enable UUID extension
    await supabase.query('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"');

    for (const tableName of orderedTables) {
      console.log(`\n   Table: ${tableName}`);

      // Get full CREATE TABLE statement from Neon
      const createResult = await neon.query(`
        SELECT
          'CREATE TABLE "' || table_name || '" (' ||
          string_agg(
            '"' || column_name || '" ' ||
            CASE
              WHEN data_type = 'ARRAY' THEN udt_name || '[]'
              WHEN data_type = 'USER-DEFINED' THEN udt_name
              WHEN data_type = 'character varying' THEN 'VARCHAR(' || COALESCE(character_maximum_length::text, '255') || ')'
              WHEN data_type = 'numeric' AND numeric_precision IS NOT NULL THEN 'NUMERIC(' || numeric_precision || ',' || COALESCE(numeric_scale, 0) || ')'
              ELSE data_type
            END ||
            CASE WHEN is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END ||
            CASE WHEN column_default IS NOT NULL THEN ' DEFAULT ' || column_default ELSE '' END,
            ', ' ORDER BY ordinal_position
          ) ||
          ')' as create_stmt
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = $1
        GROUP BY table_name
      `, [tableName]);

      if (createResult.rows.length > 0) {
        const createStmt = createResult.rows[0].create_stmt;

        try {
          await supabase.query(createStmt);
          console.log(`      ✓ Created table`);
        } catch (e) {
          console.log(`      ❌ Error creating: ${e.message}`);
          continue;
        }

        // Get and add primary key
        const pkResult = await neon.query(`
          SELECT a.attname as column_name
          FROM pg_index i
          JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
          JOIN pg_class c ON c.oid = i.indrelid
          JOIN pg_namespace n ON n.oid = c.relnamespace
          WHERE i.indisprimary AND n.nspname = 'public' AND c.relname = $1
        `, [tableName]);

        if (pkResult.rows.length > 0) {
          const pkCols = pkResult.rows.map(r => `"${r.column_name}"`).join(', ');
          try {
            await supabase.query(`ALTER TABLE "${tableName}" ADD PRIMARY KEY (${pkCols})`);
          } catch (e) {
            // PK might already exist from column default
          }
        }

        // Copy data
        const data = await getTableData(neon, tableName);
        if (data.length > 0) {
          const columns = Object.keys(data[0]);
          const colList = columns.map(c => `"${c}"`).join(', ');

          let inserted = 0;
          for (const row of data) {
            const values = columns.map(c => formatValue(row[c])).join(', ');
            try {
              await supabase.query(`INSERT INTO "${tableName}" (${colList}) VALUES (${values})`);
              inserted++;
            } catch (e) {
              console.log(`      ⚠ Insert error: ${e.message.substring(0, 80)}`);
            }
          }
          console.log(`      ✓ Inserted ${inserted}/${data.length} rows`);
        } else {
          console.log(`      (empty table)`);
        }
      }
    }

    // Step 5: Add foreign keys
    console.log('\n📦 Adding foreign keys...');
    for (const tableName of orderedTables) {
      const fks = await getForeignKeys(neon, tableName);
      for (const fk of fks) {
        try {
          await supabase.query(`
            ALTER TABLE "${tableName}"
            ADD CONSTRAINT "${fk.constraint_name}"
            FOREIGN KEY ("${fk.column_name}")
            REFERENCES "${fk.ref_table}"("${fk.ref_column}")
          `);
          console.log(`   ✓ ${tableName}.${fk.column_name} → ${fk.ref_table}.${fk.ref_column}`);
        } catch (e) {
          console.log(`   ⚠ FK ${fk.constraint_name}: ${e.message.substring(0, 60)}`);
        }
      }
    }

    // Step 6: Add indexes
    console.log('\n📦 Creating indexes...');
    for (const tableName of orderedTables) {
      const indexes = await getIndexes(neon, tableName);
      for (const indexDef of indexes) {
        try {
          await supabase.query(indexDef);
          console.log(`   ✓ ${indexDef.substring(0, 60)}...`);
        } catch (e) {
          // Index might already exist
        }
      }
    }

    // Re-enable FK checks
    await supabase.query('SET session_replication_role = DEFAULT;');

    console.log('\n' + '='.repeat(60));
    console.log('  ✓ Migration Complete!');
    console.log('='.repeat(60));

  } catch (error) {
    console.error('❌ Error:', error.message);
    console.error(error.stack);
  } finally {
    await neon.end();
    await supabase.end();
  }
}

main();
