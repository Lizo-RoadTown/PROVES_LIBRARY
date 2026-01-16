/**
 * Migrate EVERYTHING from Neon to Supabase
 *
 * 1. Create all enums
 * 2. Create all tables
 * 3. Copy all data
 * 4. Add foreign keys and indexes
 */

const { Client } = require('pg');
require('dotenv').config();

const NEON_URL = "postgresql://neondb_owner:npg_GvP5x0yVrCLm@ep-empty-morning-af4l9ocx-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require";
const SUPABASE_URL = process.env.DIRECT_URL?.replace('?pgbouncer=true', '') || '';

// Tables to skip (internal LangGraph checkpoint tables that have bytea issues)
const SKIP_TABLES = ['checkpoint_blobs'];

async function getAllEnums(client) {
  // Get enum names first
  const enumNames = await client.query(`
    SELECT DISTINCT t.typname as name
    FROM pg_type t
    JOIN pg_enum e ON t.oid = e.enumtypid
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'public'
  `);

  const enums = [];
  for (const row of enumNames.rows) {
    const valuesResult = await client.query(`
      SELECT e.enumlabel as value
      FROM pg_type t
      JOIN pg_enum e ON t.oid = e.enumtypid
      WHERE t.typname = $1
      ORDER BY e.enumsortorder
    `, [row.name]);
    enums.push({
      name: row.name,
      values: valuesResult.rows.map(r => r.value)
    });
  }
  return enums;
}

async function getAllTables(client) {
  const result = await client.query(`
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    ORDER BY table_name
  `);
  return result.rows.map(r => r.table_name);
}

async function getCreateTableSQL(client, tableName) {
  const result = await client.query(`
    SELECT column_name, data_type, udt_name, is_nullable, column_default,
           character_maximum_length, numeric_precision, numeric_scale
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = $1
    ORDER BY ordinal_position
  `, [tableName]);

  if (result.rows.length === 0) return null;

  const columns = result.rows.map(col => {
    let type;

    if (col.data_type === 'ARRAY') {
      const baseType = col.udt_name.replace(/^_/, '');
      type = baseType + '[]';
    } else if (col.data_type === 'USER-DEFINED') {
      type = col.udt_name;  // Use the enum name directly
    } else if (col.data_type === 'character varying') {
      type = col.character_maximum_length ? `VARCHAR(${col.character_maximum_length})` : 'TEXT';
    } else if (col.data_type === 'numeric' && col.numeric_precision) {
      type = `NUMERIC(${col.numeric_precision},${col.numeric_scale || 0})`;
    } else {
      type = col.data_type;
    }

    let def = `"${col.column_name}" ${type}`;
    if (col.is_nullable === 'NO') def += ' NOT NULL';
    if (col.column_default && !col.column_default.includes('nextval')) {
      def += ` DEFAULT ${col.column_default}`;
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

async function getForeignKeys(client, tableName) {
  const result = await client.query(`
    SELECT
      con.conname,
      a.attname as column_name,
      ref.relname as ref_table,
      ref_a.attname as ref_column
    FROM pg_constraint con
    JOIN pg_class cl ON cl.oid = con.conrelid
    JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = ANY(con.conkey)
    JOIN pg_class ref ON ref.oid = con.confrelid
    JOIN pg_attribute ref_a ON ref_a.attrelid = con.confrelid AND ref_a.attnum = ANY(con.confkey)
    WHERE con.contype = 'f' AND cl.relname = $1
  `, [tableName]);
  return result.rows;
}

async function getIndexes(client, tableName) {
  const result = await client.query(`
    SELECT indexdef FROM pg_indexes
    WHERE schemaname = 'public' AND tablename = $1 AND indexname NOT LIKE '%_pkey'
  `, [tableName]);
  return result.rows.map(r => r.indexdef);
}

async function getTableData(client, tableName) {
  const result = await client.query(`SELECT * FROM "${tableName}"`);
  return result.rows;
}

function escapeValue(val, colName) {
  if (val === null || val === undefined) return 'NULL';
  if (typeof val === 'boolean') return val ? 'TRUE' : 'FALSE';
  if (typeof val === 'number') return String(val);
  if (val instanceof Date) return `'${val.toISOString()}'`;

  // Handle bytea/Buffer
  if (Buffer.isBuffer(val)) {
    return `'\\x${val.toString('hex')}'::bytea`;
  }

  // Handle objects (JSONB)
  if (typeof val === 'object') {
    return `'${JSON.stringify(val).replace(/'/g, "''")}'::jsonb`;
  }

  // String
  return `'${String(val).replace(/'/g, "''")}'`;
}

async function main() {
  console.log('='.repeat(60));
  console.log('  FULL Neon → Supabase Migration');
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

    // Step 1: Drop all existing tables
    console.log('\n📦 Step 1: Dropping existing Supabase tables...');
    const existingTables = await getAllTables(supabase);
    await supabase.query('SET session_replication_role = replica');
    for (const t of existingTables) {
      await supabase.query(`DROP TABLE IF EXISTS "${t}" CASCADE`);
    }
    console.log(`   Dropped ${existingTables.length} tables`);

    // Step 2: Drop and recreate enums
    console.log('\n📦 Step 2: Creating enums...');
    const enums = await getAllEnums(neon);

    // Drop existing enums
    for (const e of enums) {
      try {
        await supabase.query(`DROP TYPE IF EXISTS "${e.name}" CASCADE`);
      } catch (err) {}
    }

    // Create enums
    let enumsCreated = 0;
    for (const e of enums) {
      const values = e.values.map(v => `'${v}'`).join(', ');
      try {
        await supabase.query(`CREATE TYPE "${e.name}" AS ENUM (${values})`);
        enumsCreated++;
      } catch (err) {
        console.log(`   ⚠️ Enum ${e.name}: ${err.message.substring(0, 50)}`);
      }
    }
    console.log(`   Created ${enumsCreated} enums`);

    // Enable UUID extension
    await supabase.query('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"');

    // Step 3: Create all tables (without FKs)
    console.log('\n📦 Step 3: Creating tables...');
    const allTables = await getAllTables(neon);
    const tablesToMigrate = allTables.filter(t => !SKIP_TABLES.includes(t));
    console.log(`   Found ${tablesToMigrate.length} tables to migrate`);

    let tablesCreated = 0;
    let tableErrors = [];

    for (const tableName of tablesToMigrate) {
      const createSQL = await getCreateTableSQL(neon, tableName);
      if (!createSQL) continue;

      try {
        await supabase.query(createSQL);

        // Add primary key
        const pkCols = await getPrimaryKey(neon, tableName);
        if (pkCols.length > 0) {
          try {
            await supabase.query(`ALTER TABLE "${tableName}" ADD PRIMARY KEY (${pkCols.map(c => `"${c}"`).join(', ')})`);
          } catch (err) {}
        }

        tablesCreated++;
      } catch (err) {
        tableErrors.push({ table: tableName, error: err.message.substring(0, 80) });
      }
    }
    console.log(`   Created ${tablesCreated}/${tablesToMigrate.length} tables`);
    if (tableErrors.length > 0) {
      console.log(`   Errors:`);
      for (const e of tableErrors.slice(0, 5)) {
        console.log(`     - ${e.table}: ${e.error}`);
      }
      if (tableErrors.length > 5) console.log(`     ... and ${tableErrors.length - 5} more`);
    }

    // Step 4: Copy data
    console.log('\n📦 Step 4: Copying data...');
    let totalRows = 0;
    let dataErrors = [];

    for (const tableName of tablesToMigrate) {
      // Check if table was created
      try {
        await supabase.query(`SELECT 1 FROM "${tableName}" LIMIT 0`);
      } catch (err) {
        continue; // Table wasn't created, skip
      }

      const data = await getTableData(neon, tableName);
      if (data.length === 0) continue;

      const columns = Object.keys(data[0]);
      const colList = columns.map(c => `"${c}"`).join(', ');

      let inserted = 0;
      let errors = 0;

      for (const row of data) {
        const values = columns.map(c => escapeValue(row[c], c)).join(', ');
        try {
          await supabase.query(`INSERT INTO "${tableName}" (${colList}) VALUES (${values})`);
          inserted++;
        } catch (err) {
          errors++;
          if (errors === 1) {
            dataErrors.push({ table: tableName, error: err.message.substring(0, 80) });
          }
        }
      }

      if (inserted > 0) {
        console.log(`   ${tableName}: ${inserted}/${data.length} rows`);
        totalRows += inserted;
      }
    }

    if (dataErrors.length > 0) {
      console.log(`\n   Data copy errors:`);
      for (const e of dataErrors.slice(0, 10)) {
        console.log(`     - ${e.table}: ${e.error}`);
      }
    }

    // Step 5: Add foreign keys
    console.log('\n📦 Step 5: Adding foreign keys...');
    let fksAdded = 0;

    for (const tableName of tablesToMigrate) {
      const fks = await getForeignKeys(neon, tableName);
      for (const fk of fks) {
        try {
          await supabase.query(`
            ALTER TABLE "${tableName}"
            ADD CONSTRAINT "${fk.conname}"
            FOREIGN KEY ("${fk.column_name}")
            REFERENCES "${fk.ref_table}"("${fk.ref_column}")
          `);
          fksAdded++;
        } catch (err) {}
      }
    }
    console.log(`   Added ${fksAdded} foreign keys`);

    // Step 6: Create indexes
    console.log('\n📦 Step 6: Creating indexes...');
    let indexesCreated = 0;

    for (const tableName of tablesToMigrate) {
      const indexes = await getIndexes(neon, tableName);
      for (const indexDef of indexes) {
        try {
          await supabase.query(indexDef);
          indexesCreated++;
        } catch (err) {}
      }
    }
    console.log(`   Created ${indexesCreated} indexes`);

    // Re-enable FK checks
    await supabase.query('SET session_replication_role = DEFAULT');

    console.log('\n' + '='.repeat(60));
    console.log('  ✓ Migration Complete!');
    console.log(`    Enums: ${enumsCreated}`);
    console.log(`    Tables: ${tablesCreated}`);
    console.log(`    Rows: ${totalRows}`);
    console.log(`    Foreign keys: ${fksAdded}`);
    console.log(`    Indexes: ${indexesCreated}`);
    console.log('='.repeat(60));

  } catch (err) {
    console.error('❌ Error:', err.message);
    console.error(err.stack);
  } finally {
    await neon.end();
    await supabase.end();
  }
}

main();
