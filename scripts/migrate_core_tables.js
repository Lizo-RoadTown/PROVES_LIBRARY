/**
 * Migrate CORE tables from Neon to Supabase
 *
 * Focuses on the tables needed for the curation dashboard.
 * Skips checkpoint tables (LangGraph internal) and other non-essential tables.
 */

const { Client } = require('pg');
require('dotenv').config();

const NEON_URL = "postgresql://neondb_owner:npg_GvP5x0yVrCLm@ep-empty-morning-af4l9ocx-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require";
const SUPABASE_URL = process.env.DIRECT_URL?.replace('?pgbouncer=true', '') || '';

// Tables to migrate in dependency order
// Skip: checkpoint_*, builder_jobs, training_*, derived_*, and other non-essential tables
const CORE_TABLES = [
  'pipeline_runs',
  'raw_snapshots',
  'staging_extractions',
  'validation_decisions',
  'core_entities',
  'curator_errors',
  'curator_reports',
  'improvement_suggestions',
];

async function getCreateTableSQL(client, tableName) {
  // Get column definitions
  const result = await client.query(`
    SELECT column_name, data_type, udt_name, is_nullable, column_default,
           character_maximum_length, numeric_precision, numeric_scale
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = $1
    ORDER BY ordinal_position
  `, [tableName]);

  if (result.rows.length === 0) return null;

  const columns = result.rows.map(col => {
    let type = col.data_type;

    // Handle specific types
    if (col.data_type === 'ARRAY') {
      type = col.udt_name.replace(/^_/, '') + '[]';
    } else if (col.data_type === 'USER-DEFINED') {
      // Use TEXT for enums since we're not recreating them
      type = 'TEXT';
    } else if (col.data_type === 'character varying') {
      type = col.character_maximum_length ? `VARCHAR(${col.character_maximum_length})` : 'TEXT';
    } else if (col.data_type === 'numeric' && col.numeric_precision) {
      type = `NUMERIC(${col.numeric_precision},${col.numeric_scale || 0})`;
    }

    let def = `"${col.column_name}" ${type}`;
    if (col.is_nullable === 'NO') def += ' NOT NULL';
    if (col.column_default) {
      // Skip nextval defaults, add others
      if (!col.column_default.includes('nextval')) {
        def += ` DEFAULT ${col.column_default}`;
      }
    }
    return def;
  });

  return `CREATE TABLE "${tableName}" (\n  ${columns.join(',\n  ')}\n)`;
}

async function getPrimaryKey(client, tableName) {
  const result = await client.query(`
    SELECT a.attname
    FROM pg_index i
    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
    JOIN pg_class c ON c.oid = i.indrelid
    WHERE i.indisprimary AND c.relname = $1
  `, [tableName]);
  return result.rows.map(r => r.attname);
}

async function getTableData(client, tableName) {
  const result = await client.query(`SELECT * FROM "${tableName}"`);
  return result.rows;
}

function escapeValue(val) {
  if (val === null || val === undefined) return 'NULL';
  if (typeof val === 'boolean') return val ? 'TRUE' : 'FALSE';
  if (typeof val === 'number') return String(val);
  if (val instanceof Date) return `'${val.toISOString()}'`;
  if (Buffer.isBuffer(val)) return `'\\x${val.toString('hex')}'`;
  if (typeof val === 'object') {
    return `'${JSON.stringify(val).replace(/'/g, "''")}'::jsonb`;
  }
  return `'${String(val).replace(/'/g, "''")}'`;
}

async function migrateTable(neon, supabase, tableName) {
  console.log(`\n📦 ${tableName}`);

  // Check if table exists in Neon
  const existsResult = await neon.query(`
    SELECT EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'public' AND table_name = $1
    )
  `, [tableName]);

  if (!existsResult.rows[0].exists) {
    console.log(`   ⚠️ Table does not exist in Neon, skipping`);
    return { created: false, rows: 0 };
  }

  // Drop existing table in Supabase
  await supabase.query(`DROP TABLE IF EXISTS "${tableName}" CASCADE`);

  // Get CREATE TABLE statement
  const createSQL = await getCreateTableSQL(neon, tableName);
  if (!createSQL) {
    console.log(`   ⚠️ Could not generate CREATE TABLE, skipping`);
    return { created: false, rows: 0 };
  }

  // Create table
  try {
    await supabase.query(createSQL);
    console.log(`   ✓ Created table`);
  } catch (err) {
    console.log(`   ❌ Error creating table: ${err.message}`);
    return { created: false, rows: 0 };
  }

  // Add primary key
  const pkCols = await getPrimaryKey(neon, tableName);
  if (pkCols.length > 0) {
    try {
      await supabase.query(`ALTER TABLE "${tableName}" ADD PRIMARY KEY (${pkCols.map(c => `"${c}"`).join(', ')})`);
    } catch (err) {
      // PK might already exist
    }
  }

  // Get and insert data
  const data = await getTableData(neon, tableName);
  console.log(`   Found ${data.length} rows in Neon`);

  if (data.length === 0) {
    return { created: true, rows: 0 };
  }

  let inserted = 0;
  let errors = 0;
  const columns = Object.keys(data[0]);
  const colList = columns.map(c => `"${c}"`).join(', ');

  for (const row of data) {
    const values = columns.map(c => escapeValue(row[c])).join(', ');
    try {
      await supabase.query(`INSERT INTO "${tableName}" (${colList}) VALUES (${values})`);
      inserted++;
    } catch (err) {
      errors++;
      if (errors <= 3) {
        console.log(`   ⚠️ Insert error: ${err.message.substring(0, 100)}`);
      }
    }
  }

  console.log(`   ✓ Inserted ${inserted}/${data.length} rows${errors > 0 ? ` (${errors} errors)` : ''}`);
  return { created: true, rows: inserted };
}

async function main() {
  console.log('='.repeat(60));
  console.log('  Neon → Supabase: Core Tables Migration');
  console.log('='.repeat(60));

  if (!SUPABASE_URL) {
    console.error('❌ DIRECT_URL not set');
    process.exit(1);
  }

  const neon = new Client({ connectionString: NEON_URL });
  const supabase = new Client({ connectionString: SUPABASE_URL });

  try {
    await neon.connect();
    console.log('✓ Connected to Neon');

    await supabase.connect();
    console.log('✓ Connected to Supabase');

    // Enable UUID extension
    await supabase.query('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"');

    // Disable FK checks
    await supabase.query('SET session_replication_role = replica');

    let totalRows = 0;
    let tablesCreated = 0;

    for (const table of CORE_TABLES) {
      const result = await migrateTable(neon, supabase, table);
      if (result.created) tablesCreated++;
      totalRows += result.rows;
    }

    // Re-enable FK checks
    await supabase.query('SET session_replication_role = DEFAULT');

    console.log('\n' + '='.repeat(60));
    console.log(`  ✓ Migration Complete!`);
    console.log(`    Tables created: ${tablesCreated}`);
    console.log(`    Total rows: ${totalRows}`);
    console.log('='.repeat(60));

  } catch (err) {
    console.error('❌ Error:', err.message);
  } finally {
    await neon.end();
    await supabase.end();
  }
}

main();
